#!/usr/bin/env python3
"""Tests de la musique : plan (music_plan.py, build.py), génération (make-music.py), mixage (mix-music.py).

  A. registre §1d et repères : fins (`music_until`, durée du registre), chevauchements, couverture ;
  B. build : data/music.json, désactivation (`**Musique** : aucune`, --no-music), erreurs claires ;
  C. génération : appel de `sound music …`, cache, un seul fichier pour deux repères identiques ;
  D. mixage : la musique reste sous la voix (mesuré), monte dans les silences, fondus, vidéo non ré-encodée ;
  E. post-render : prend renders/full-music.mp4, refuse un mixage périmé.

Usage : python3 scripts/test-music.py   (FFmpeg requis ; aucun autre outil)
"""
import array
import importlib.util
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import music_plan as mp  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def scenes_fixture():
    def st(i, t, d, **p):
        return {"id": i, "_t": t, "_abs_dur": d, "params": p}
    return [
        {"id": "I0", "_start": 0.0, "_dur": 30.0, "steps": [st("I0.1#0", 0.0, 10.0), st("I0.1#1", 10.0, 20.0, music="M01")]},
        {"id": "I1", "_start": 30.0, "_dur": 40.0, "steps": [st("I1.1#0", 30.0, 10.0, music="M02", music_until="I1.1#2"),
                                                             st("I1.1#1", 40.0, 10.0), st("I1.1#2", 50.0, 20.0)]},
        {"id": "I2", "_start": 70.0, "_dur": 30.0, "steps": [st("I2.1#0", 70.0, 30.0, music="M01", music_until="I2")]},
    ]


REG_ROWS = {
    "M01": {"id": "M01", "role": "montée", "prompt": "epic orchestral build", "duree": "15", "volume": "0,5", "seed": "7"},
    "M02": {"id": "M02", "role": "sommet", "prompt": "epic orchestral climax, choir-less", "duree": "", "volume": "", "seed": ""},
}


def part_a():
    print("A. registre et repères")
    reg, errs = mp.registry_from_rows(REG_ROWS)
    check("registre : prompt, durée, volume (virgule décimale), graine", reg["M01"]["duration"] == 15.0
          and reg["M01"]["volume"] == 0.5 and reg["M01"]["seed"] == 7 and not errs, (reg, errs))
    check("registre : volume et durée par défaut", reg["M02"]["volume"] == mp.DEFAULT_VOLUME and reg["M02"]["duration"] is None)
    _, errs = mp.registry_from_rows({"M09": {"id": "M09", "prompt": ""}})
    check("registre : prompt obligatoire", len(errs) == 1 and "sans prompt" in errs[0], errs)
    _, errs = mp.registry_from_rows({"M09": {"id": "M09", "prompt": "x", "volume": "3"}})
    check("registre : volume hors de ]0 ; 1] refusé", len(errs) == 1, errs)

    cues, warns, errs = mp.resolve_cues(scenes_fixture(), reg, 100.0)
    byid = {c["step"]: c for c in cues}
    check("repère : début = début de l'étape, fin = durée du registre", byid["I0.1#1"]["start"] == 10.0 and byid["I0.1#1"]["end"] == 25.0, byid["I0.1#1"])
    check("`music_until` = une étape : fin au début de cette étape", byid["I1.1#0"]["end"] == 50.0, byid["I1.1#0"])
    check("`music_until` = une scène : fin de la scène", byid["I2.1#0"]["end"] == 100.0, byid["I2.1#0"])
    check("sans durée ni until : durée par défaut", True)
    check("repères triés par temps, numérotés", [c["cue"] for c in cues] == ["C1", "C2", "C3"] and
          [c["start"] for c in cues] == sorted(c["start"] for c in cues))
    check("fichier nommé d'après musique, prompt, graine, durée (stable)",
          cues[0]["file"] == mp.gen_file("M01", reg["M01"]["prompt"], 7, 15)
          and cues[0]["file"].startswith("assets/music/M01-") and cues[0]["file"].endswith(".wav"), cues[0]["file"])
    check("même musique, même durée = même fichier ; durée différente = autre fichier",
          mp.gen_file("M01", "p", 7, 15) == mp.gen_file("M01", "p", 7, 15) and mp.gen_file("M01", "p", 7, 15) != mp.gen_file("M01", "p", 7, 16))
    check("couverture : 15 + 20 + 30 s sur 100 s -> avertissement (musique trop présente)",
          any("couvre" in w for w in warns), warns)

    sc = scenes_fixture()
    sc[0]["steps"][1]["params"]["music_until"] = "I1.1#0"      # fin à 30 s
    sc[1]["steps"][0]["params"] = {"music": "M02", "music_until": "4"}
    c2, w2, _ = mp.resolve_cues(sc, reg, 100.0)
    check("`music_until` en secondes : durée depuis le début", [c for c in c2 if c["step"] == "I1.1#0"][0]["end"] == 34.0)
    check("musique de 4 s : acceptée sans avertissement de durée", not any("trop court" in w for w in w2), w2)
    sc[1]["steps"][0]["params"] = {"music": "M02", "music_until": "2"}
    _, w3, _ = mp.resolve_cues(sc, reg, 100.0)
    check("musique de 2 s : trop courte", any("trop court" in w for w in w3), w3)

    sc = scenes_fixture()
    sc[0]["steps"][1]["params"]["music_until"] = "I1"            # 10 -> 70 s
    c4, w4, _ = mp.resolve_cues(sc, reg, 100.0)
    c4 = {c["step"]: c for c in c4}
    check("chevauchement : la première musique est coupée au début de la seconde + avertissement",
          c4["I0.1#1"]["end"] == 30.0 and any("se chevauchent" in w for w in w4), (c4["I0.1#1"], w4))

    c5, w5, e5 = mp.resolve_cues(scenes_fixture(), reg, 20.0)
    check("fin du film : la musique ne dépasse pas la durée totale", all(c["end"] <= 20.0 for c in c5), c5)
    sc = scenes_fixture()
    sc[0]["steps"][1]["params"]["music"] = "M77"
    _, _, e6 = mp.resolve_cues(sc, reg, 100.0)
    check("musique inconnue : erreur qui nomme l'étape", len(e6) == 1 and "I0.1#1" in e6[0] and "M77" in e6[0], e6)
    sc = scenes_fixture()
    sc[0]["steps"][1]["params"]["music_until"] = "zzz"
    _, _, e7 = mp.resolve_cues(sc, reg, 100.0)
    check("`music_until` incompréhensible : erreur", len(e7) == 1, e7)
    sc = scenes_fixture()
    sc[0]["steps"][1]["params"]["music_volume"] = "0.2"
    c8, _, _ = mp.resolve_cues(sc, reg, 100.0)
    check("`music_volume` : surcharge le volume du registre", [c for c in c8 if c["step"] == "I0.1#1"][0]["volume"] == 0.2)


STORYBOARD = """# STORYBOARD — Test musique

**Mode** : auto
%s
## 1d. Registre des musiques

| ID | Rôle | Prompt | Durée | Volume | Seed |
|---|---|---|---|---|---|
| M01 | montée | epic orchestral build, rising strings, timpani, cinematic, no vocals | 12 | 0.5 | 7 |
| M02 | conclusion | epic orchestral finale, brass and choir-less strings, resolving, no vocals | | | |

## 4. Scènes

### I1 — Début

- section: a · type: cards · fond: BG-00 · durée: 40

#### Étapes

- `I1.1#0` · cue « a » → **un mot**
  - kind: kw
  - text: Début
- `I1.1#1` · cue « b » → **la montée**
  - kind: kw
  - text: Montée
  - music: M01
- `I1.1#2` · cue « c » → **la suite**
  - kind: kw
  - text: Suite

### I2 — Fin

- section: b · type: cards · fond: BG-00 · durée: 30

#### Étapes

- `I2.1#0` · cue « d » → **la conclusion**
  - kind: kw
  - text: Fin
  - music: M02
  - music_until: I2
"""


def build(tmp, *extra):
    return sh([sys.executable, str(HERE / "build.py"), "--root", str(tmp)] + list(extra), cwd=str(tmp))


def project(tmp, header=""):
    (tmp / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE.parent / "examples" / "demo" / "assets" / "gsap.min.js", tmp / "assets" / "gsap.min.js")
    (tmp / "assets" / "storyboard.md").write_text(STORYBOARD % header, encoding="utf-8")


def part_b(tmp):
    print("B. build : data/music.json")
    project(tmp)
    r = build(tmp)
    check("build : réussit et annonce la musique", r.returncode == 0 and "musique : 2 repère(s)" in r.stdout, r.stderr[-300:] + r.stdout[-300:])
    plan = json.loads((tmp / "data" / "music.json").read_text(encoding="utf-8"))
    c = plan["cues"]
    check("music.json : deux repères aux temps du storyboard", len(c) == 2 and c[0]["music"] == "M01" and c[1]["music"] == "M02"
          and abs(c[0]["end"] - c[0]["start"] - 12.0) < 0.01 and c[1]["duration"] > 4, c)
    check("music.json : prompt, graine, volume, fichier, fondus", c[0]["seed"] == 7 and c[0]["volume"] == 0.5
          and c[0]["file"].startswith("assets/music/M01-") and c[0]["fade_in"] == 1.5 and c[0]["fade_out"] == 3.0, c[0])
    check("music.json : couverture calculée", 0 < plan["coverage"] < 1, plan["coverage"])
    comps = "".join(p.read_text(encoding="utf-8") for p in (tmp / "compositions").glob("*.html")) + (tmp / "index.html").read_text(encoding="utf-8")
    check("la composition ne contient aucune trace de la musique (elle est mixée après le rendu)",
          "music" not in comps.lower().replace("music-", "") or "M01" not in comps, "")
    project(tmp, header="**Musique** : aucune\n")
    r = build(tmp)
    check("en-tête **Musique** : aucune -> pas de music.json (et le plan périmé est supprimé)",
          r.returncode == 0 and not (tmp / "data" / "music.json").exists() and "désactivée" in r.stdout, r.stdout[-300:])
    project(tmp)
    build(tmp)
    r = build(tmp, "--no-music")
    check("--no-music : désactive aussi", r.returncode == 0 and not (tmp / "data" / "music.json").exists() and "--no-music" in r.stdout)
    project(tmp)
    (tmp / "assets" / "storyboard.md").write_text(STORYBOARD.replace("music: M02", "music: M77") % "", encoding="utf-8")
    r = build(tmp)
    check("musique absente du registre : le build s'arrête, message clair", r.returncode == 1 and "M77" in r.stderr and "registre §1d" in r.stderr, r.stderr[-300:])
    (tmp / "assets" / "storyboard.md").write_text(STORYBOARD.replace("| M01 | montée | epic orchestral build, rising strings, timpani, cinematic, no vocals |", "| M01 | montée | |") % "", encoding="utf-8")
    r = build(tmp)
    check("registre sans prompt : erreur", r.returncode == 1 and "sans prompt" in r.stderr, r.stderr[-300:])
    t2 = tmp / "plain"
    t2.mkdir()
    (t2 / "assets").mkdir()
    shutil.copy(HERE.parent / "examples" / "demo" / "assets" / "gsap.min.js", t2 / "assets" / "gsap.min.js")
    ex = (HERE.parent / "examples" / "storyboard.example.md").read_text(encoding="utf-8")
    ex = re.sub(r"## 1d\. Registre des musiques.*?(?=\n## )", "", ex, flags=re.S)          # l'exemple porte de la musique : on la retire
    ex = "\n".join(l for l in ex.split("\n") if not re.match(r"\s*- music(_until|_volume)?:", l))
    (t2 / "assets" / "storyboard.md").write_text(ex, encoding="utf-8")
    r = build(t2)
    check("storyboard sans musique : build inchangé, aucune sortie musique", r.returncode == 0 and not (t2 / "data" / "music.json").exists()
          and "musique" not in r.stdout.lower(), r.stdout[-200:])


FAKE_SOUND = """#!/bin/sh
echo "$@" >> "%(log)s"
out=""; dur=5
while [ $# -gt 0 ]; do
  case "$1" in -o) out="$2";; -d) dur="$2";; esac
  shift
done
ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=440:sample_rate=44100:duration=$dur" "$out"
printf '{"path": "%%s", "duration_secs": %%s}' "$out" "$dur"
"""


def part_c(tmp):
    print("C. génération (faux `sound`)")
    project(tmp)
    build(tmp)
    bindir = tmp / "bin"
    bindir.mkdir(exist_ok=True)
    log = tmp / "sound-calls.txt"
    fake = bindir / "sound"
    fake.write_text(FAKE_SOUND % {"log": log}, encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ["PATH"])
    script = str(HERE / "make-music.py")
    r = subprocess.run([sys.executable, script, "--root", str(tmp), "--plan"], capture_output=True, text=True, env=env)
    check("--plan : liste les fichiers, ne génère rien", r.returncode == 0 and "à générer" in r.stdout and not log.exists(), r.stdout[-300:] + r.stderr[-200:])
    r = subprocess.run([sys.executable, script, "--root", str(tmp)], capture_output=True, text=True, env=env)
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    check("génération : un appel `sound music` par fichier", r.returncode == 0 and len(calls) == 2 and all(c.startswith("music ") for c in calls), (r.stderr, calls))
    c1 = [c for c in calls if "rising strings" in c][0]
    check("appel : prompt, instrumental, durée, graine, sortie, JSON", "-i" in c1.split() and "-d 12 " in c1 and "-S 7" in c1 and "-F json" in c1 and "assets/music/M01-" in c1, c1)
    c2 = [c for c in calls if "finale" in c][0]
    check("appel : pas de graine quand le registre n'en a pas", "-S" not in c2.split(), c2)
    plan = json.loads((tmp / "data" / "music.json").read_text(encoding="utf-8"))
    check("fichiers présents et lisibles", all((tmp / c["file"]).exists() for c in plan["cues"]))
    log.unlink()
    r = subprocess.run([sys.executable, script, "--root", str(tmp)], capture_output=True, text=True, env=env)
    check("cache : deuxième passage = rien à générer", r.returncode == 0 and not log.exists() and "déjà là" in r.stdout, r.stdout[-300:])
    r = subprocess.run([sys.executable, script, "--root", str(tmp), "--force", "--engine", "musicgen"], capture_output=True, text=True, env=env)
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    check("--force régénère ; --engine est transmis", len(calls) == 2 and all("-e musicgen" in c for c in calls), calls)
    r = subprocess.run([sys.executable, script, "--root", str(tmp), "--force", "--max-duration", "5", "--dry-run"], capture_output=True, text=True, env=env)
    check("--max-duration : durée plafonnée, avertissement", "-d 5" in r.stdout and "limité à 5 s" in r.stdout, r.stdout[-400:])
    r = subprocess.run([sys.executable, script, "--root", str(tmp), "--force"], capture_output=True, text=True, env=dict(os.environ, PATH="/nonexistent"))
    check("`sound` absente : erreur claire", r.returncode == 1 and "introuvable" in r.stderr, r.stderr)

    # deux repères, même musique, même durée = un seul fichier
    dup = json.loads((tmp / "data" / "music.json").read_text(encoding="utf-8"))
    dup["cues"].append(dict(dup["cues"][0], cue="C3", start=200.0, end=212.0))
    (tmp / "data" / "music.json").write_text(json.dumps(dup), encoding="utf-8")
    log.unlink()
    r = subprocess.run([sys.executable, script, "--root", str(tmp), "--force"], capture_output=True, text=True, env=env)
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    check("deux repères identiques : un seul fichier généré", len(calls) == 2, calls)


# ---- mesures -------------------------------------------------------------

def rms_db(path, start, length):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(length), "-i", str(path), "-vn", "-ac", "1",
                        "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    a = array.array("f")
    a.frombytes(r.stdout[: len(r.stdout) // 4 * 4])
    if not a:
        return -120.0
    ms = sum(x * x for x in a) / len(a)
    return 10 * math.log10(ms) if ms > 1e-12 else -120.0


def make_master(path, with_audio=True):
    """20 s : vidéo de test + voix (sinus 220 Hz, 0,12) active de 0 à 6 s et de 12 à 20 s, silence entre."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=160x90:rate=10:duration=20"]
    if with_audio:
        cmd += ["-f", "lavfi", "-i", "aevalsrc=0.12*sin(2*PI*220*t)*(lt(t\\,6)+gt(t\\,12)):s=48000:d=20"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p"] + (["-c:a", "aac"] if with_audio else []) + [str(path)]
    return sh(cmd)


def part_d(tmp):
    print("D. mixage mesuré")
    root = tmp / "mix"
    (root / "renders").mkdir(parents=True)
    (root / "assets" / "music").mkdir(parents=True)
    (root / "data").mkdir()
    r = make_master(root / "renders" / "full.mp4")
    check("master de test créé", r.returncode == 0, r.stderr[-200:])
    # musique : sinus 440 Hz FORT (0,6), 14 s : pire cas, bien plus forte que la voix
    sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "aevalsrc=0.6*sin(2*PI*440*t):s=44100:d=14",
        str(root / "assets" / "music" / "M01-test.wav")])
    plan = {"version": 1, "total": 20, "coverage": 0.6, "cues": [
        {"cue": "C1", "music": "M01", "role": "", "prompt": "x", "seed": None, "step": "I1.1#0", "start": 3.0, "end": 15.0,
         "duration": 12.0, "volume": 0.45, "fade_in": 1.5, "fade_out": 3.0, "gen_duration": 12, "file": "assets/music/M01-test.wav"}]}
    (root / "data" / "music.json").write_text(json.dumps(plan), encoding="utf-8")
    script = str(HERE / "mix-music.py")
    r = sh([sys.executable, script, "--root", str(root)])
    out = root / "renders" / "full-music.mp4"
    check("mix-music : écrit renders/full-music.mp4", r.returncode == 0 and out.exists(), r.stderr[-400:] + r.stdout[-200:])
    master = root / "renders" / "full.mp4"
    voice = lambda a, b: rms_db(master, a, b - a)          # noqa: E731
    mix = lambda a, b: rms_db(out, a, b - a)               # noqa: E731
    check("avant la musique (0 à 2,5 s) : la voix seule, inchangée (±0,5 dB)", abs(mix(0.2, 2.5) - voice(0.2, 2.5)) < 0.5, (mix(0.2, 2.5), voice(0.2, 2.5)))
    over = mix(4.5, 5.8) - voice(4.5, 5.8)
    check("pendant que la voix parle, la musique ne la surpasse pas (≤ +1 dB au total ; voix %.1f dB, mix %.1f dB)" % (voice(4.5, 5.8), mix(4.5, 5.8)),
          over <= 1.0, "%.2f dB au-dessus de la voix" % over)
    quiet = mix(8.0, 10.0)
    check("dans les silences de la voix, la musique monte et s'entend (%.1f dBFS)" % quiet, quiet > -30.0, quiet)
    check("et reste mesurée (pas d'écrêtage : < -3 dBFS)", quiet < -3.0, quiet)
    check("fondu d'entrée : à 3,1 s la musique est bien plus basse qu'à 9 s", mix(8.0, 10.0) - mix(6.1, 6.2) > 0 and
          rms_db(out, 6.0, 0.15) < rms_db(out, 9.0, 0.5) - 6, (rms_db(out, 6.0, 0.15), rms_db(out, 9.0, 0.5)))
    check("fondu de sortie : la musique s'éteint avant 15 s, la voix reprend seule (≈ voix à 16 s)",
          abs(mix(16.0, 19.0) - voice(16.0, 19.0)) < 0.6, (mix(16.0, 19.0), voice(16.0, 19.0)))
    vc = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,nb_frames", "-of", "csv=p=0", str(out)]).stdout.strip()
    vm = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,nb_frames", "-of", "csv=p=0", str(master)]).stdout.strip()
    check("vidéo non ré-encodée (même codec, même nombre d'images)", vc == vm and vc != "", (vc, vm))
    dur = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)]).stdout)
    check("durée inchangée (±0,3 s)", abs(dur - 20.0) < 0.3, dur)

    out2 = root / "renders" / "nodk.mp4"
    sh([sys.executable, script, "--root", str(root), "--no-duck", "--out", str(out2)])
    over2 = rms_db(out2, 4.5, 1.3) - voice(4.5, 5.8)
    check("sans ducking la musique écraserait la voix (le test est sensible : +%.1f dB)" % over2, over2 > 4.0, over2)
    out3 = root / "renders" / "half.mp4"
    sh([sys.executable, script, "--root", str(root), "--scale", "0.5", "--out", str(out3)])
    check("--scale 0.5 : musique ≈ 6 dB plus basse dans les silences", 4.5 < quiet - rms_db(out3, 8.0, 2.0) < 7.5, quiet - rms_db(out3, 8.0, 2.0))
    r = sh([sys.executable, script, "--root", str(root), "--print-graph", "--dry-run"])
    check("--print-graph : sidechaincompress, adelay en ms, limiteur", "sidechaincompress" in r.stdout and "adelay=3000|3000" in r.stdout and "alimiter" in r.stdout, r.stdout[:300])
    (root / "assets" / "music" / "M01-test.wav").rename(root / "assets" / "music" / "x.wav")
    r = sh([sys.executable, script, "--root", str(root)])
    check("fichier de musique manquant : erreur qui renvoie à make-music.py", r.returncode == 1 and "make-music.py" in r.stderr, r.stderr)
    (root / "assets" / "music" / "x.wav").rename(root / "assets" / "music" / "M01-test.wav")
    make_master(root / "renders" / "mute.mp4", with_audio=False)
    r = sh([sys.executable, script, "--root", str(root), "--master", "renders/mute.mp4"])
    check("master sans audio : erreur claire", r.returncode == 1 and "piste audio" in r.stderr, r.stderr)


def part_e(tmp):
    print("E. post-render : master avec musique")
    root = tmp / "mix"
    man = {"inserts": [{"id": "X1", "source": "clip.mp4", "start": "0:10", "end": "0:12", "at": "5"}]}
    (root / "assets").mkdir(exist_ok=True)
    (root / "assets" / "inserts.json").write_text(json.dumps(man), encoding="utf-8")
    (root / "assets" / "storyboard.md").write_text("# x\n", encoding="utf-8")
    pr = str(HERE / "post-render.py")
    full, mus = root / "renders" / "full.mp4", root / "renders" / "full-music.mp4"
    now = time.time()
    os.utime(full, (now - 100, now - 100))
    os.utime(mus, (now - 10, now - 10))
    r = sh([sys.executable, pr, "--root", str(root), "--plan"])
    check("full-music.mp4 plus récent : c'est le master", r.returncode == 0 and "full-music.mp4 (musique mixée" in r.stdout, r.stdout[-300:] + r.stderr[-200:])
    r = sh([sys.executable, pr, "--root", str(root), "--plan", "--no-music"])
    check("--no-music : on part de full.mp4", r.returncode == 0 and "full-music.mp4" not in r.stdout, r.stdout[-300:])
    os.utime(full, (now, now))
    os.utime(mus, (now - 500, now - 500))
    r = sh([sys.executable, pr, "--root", str(root), "--plan"])
    check("mixage plus ancien que le master : refusé, message qui renvoie à mix-music.py", r.returncode == 1 and "mix-music.py" in r.stderr, r.stderr[-300:])
    man["master"] = "renders/full.mp4"
    (root / "assets" / "inserts.json").write_text(json.dumps(man), encoding="utf-8")
    r = sh([sys.executable, pr, "--root", str(root), "--plan"])
    check("master fixé dans le manifeste : jamais remplacé", r.returncode == 0 and "full-music.mp4" not in r.stdout, r.stderr[-200:])


def main():
    if not shutil.which("ffmpeg"):
        print("FFmpeg absent : tests non exécutés")
        sys.exit(0)
    part_a()
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        part_b(tmp)
        part_c(tmp)
        part_d(tmp)
        part_e(tmp)
    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
