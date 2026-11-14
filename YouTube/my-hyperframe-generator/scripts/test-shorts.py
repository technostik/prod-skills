#!/usr/bin/env python3
"""Tests des shorts de promotion : section `## 6. Shorts` du storyboard -> data/shorts_segments.json.

  A. shorts_plan.py : temps, résolution (étapes, scènes, timecodes), calage sur les phrases, limites ;
  B. build.py : le fichier au format de `video short-extractor`, désactivation, erreurs claires ;
  C. shorts-export.py : décalage par les inserts.

Usage : python3 scripts/test-shorts.py   (n'appelle pas `video short-extractor`)
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shorts_plan as sp  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def scenes():
    def st(i, t, d):
        return {"id": i, "_t": t, "_abs_dur": d, "params": {}}
    return [{"id": "I1", "_start": 0.0, "_dur": 60.0, "steps": [st("I1.1#0", 0.0, 20.0), st("I1.1#1", 20.0, 20.0), st("I1.1#2", 40.0, 20.0)]},
            {"id": "I2", "_start": 60.0, "_dur": 300.0, "steps": [st("I2.1#0", 60.0, 100.0), st("I2.1#1", 160.0, 100.0), st("I2.1#2", 260.0, 100.0)]}]


SENT = [(0.0, 9.5), (10.0, 19.8), (20.5, 38.0), (38.7, 59.5), (60.0, 120.0), (121.0, 200.0), (201.0, 360.0)]


def part_a():
    print("A. shorts_plan")
    check("timecode : HH:MM:SS,mmm, point, MM:SS, secondes", (sp.parse_tc("00:09:10,040"), sp.parse_tc("00:09:10.040"), sp.parse_tc("9:10"), sp.parse_tc("70"), sp.parse_tc(70.5))
          == (550.04, 550.04, 550.0, 70.0, 70.5))
    check("timecode invalide -> None", sp.parse_tc("pas un temps") is None and sp.parse_tc("") is None)
    check("fmt_tc : le format de video short-extractor", sp.fmt_tc(550.04) == "00:09:10,040" and sp.fmt_tc(3725.5) == "01:02:05,500" and sp.fmt_tc(0) == "00:00:00,000")
    check("fmt_tc ∘ parse_tc : aller-retour", sp.fmt_tc(sp.parse_tc("00:15:29,400")) == "00:15:29,400")

    rows = {"SH01": {"id": "SH01", "titre": "Un titre", "debut": "I1.1#0", "fin": "I1.1#1", "pourquoi": "x"},
            "SH02": {"id": "SH02", "titre": "", "debut": "I1", "fin": "I2"},
            "SH03": {"id": "SH03", "titre": "Sans fin", "debut": "I1", "fin": ""}}
    ents, errs = sp.entries_from_rows(rows)
    check("entrées : titre, début, fin obligatoires", len(ents) == 1 and len(errs) == 2 and "sans titre" in errs[0], (ents, errs))

    e = [{"id": "SH01", "title": "T", "start": "I1.1#1", "end": "I1.1#1", "why": ""}]
    segs, w, er = sp.resolve(scenes(), e, 360.0)
    check("étape : début = son début, fin = sa FIN", segs[0]["start"] == 20.0 and segs[0]["end"] == 40.0 and not er, segs)
    segs, w, er = sp.resolve(scenes(), [dict(e[0], start="I2", end="I2")], 360.0)
    check("scène : de son début à sa fin (300 s : trop long, 3 min au plus)", not segs and len(er) == 1 and "3 minutes au plus" in er[0], er)
    segs, w, er = sp.resolve(scenes(), [dict(e[0], start="00:01:05,000", end="2:00")], 360.0)
    check("timecodes explicites", segs and segs[0]["start"] == 65.0 and segs[0]["end"] == 120.0, (segs, er))
    segs, w, er = sp.resolve(scenes(), [dict(e[0], start="nimporte", end="I1.1#1")], 360.0)
    check("début incompréhensible : erreur claire", not segs and "ne désigne ni une étape" in er[0], er)
    segs, w, er = sp.resolve(scenes(), [dict(e[0], start="I1.1#2", end="I1.1#0")], 360.0)
    check("fin avant le début : erreur", not segs and "avant le début" in er[0], er)

    # calage sur les phrases : le début recule, la fin avance
    segs, w, er = sp.resolve(scenes(), [dict(e[0], start="00:00:21,300", end="00:00:37,200")], 360.0, SENT)
    check("calage : début ramené au début de phrase (20,5 s), fin avancée à la fin de phrase (38,0 s)", segs[0]["start"] == 20.5 and segs[0]["end"] == 38.0 and not any("phrase" in x for x in w), (segs, w))
    segs, w, er = sp.resolve(scenes(), [dict(e[0], start="00:00:10,000", end="00:00:19,800")], 360.0, SENT)
    check("calage : un début et une fin déjà sur une phrase ne bougent pas", segs[0]["start"] == 10.0 and segs[0]["end"] == 19.8 and not any("phrase" in x for x in w), (segs, w))
    segs, w, er = sp.resolve(scenes(), [dict(e[0], start="00:00:14,000", end="00:00:30,000")], 360.0, [(0.0, 5.0), (30.2, 40.0)])
    check("calage impossible dans la fenêtre : avertissement « à vérifier », temps inchangés", segs[0]["start"] == 14.0 and any("début de phrase" in x for x in w), w)
    segs, w, er = sp.resolve(scenes(), [dict(e[0], start="I1.1#0", end="I1.1#0")], 360.0, SENT)
    check("calage : la fin ne dépasse pas ce qui est dit (fin de phrase la plus proche)", segs[0]["end"] == 19.8, segs)

    three = [{"id": "SH0%d" % i, "title": "T%d" % i, "start": s, "end": t, "why": ""} for i, (s, t) in enumerate((("I1.1#0", "I1.1#0"), ("I1.1#1", "I1.1#1"), ("I1.1#2", "I1.1#2")), 1)]
    segs, w, er = sp.resolve(scenes(), three, 360.0)
    check("trois séquences distinctes : aucun avertissement", len(segs) == 3 and not w and not er, w)
    segs, w, er = sp.resolve(scenes(), three[:2], 360.0)
    check("deux seulement : avertissement (trois attendus)", any("3 attendus" in x for x in w), w)
    overl = [dict(three[0], end="I1.1#1"), three[1], three[2]]
    segs, w, er = sp.resolve(scenes(), overl, 360.0)
    check("séquences qui se chevauchent : avertissement", any("se chevauchent" in x for x in w), w)
    short = [dict(three[0], start="00:00:05,000", end="00:00:09,000"), three[1], three[2]]
    segs, w, er = sp.resolve(scenes(), short, 360.0)
    check("4 s : trop court (≥ 10 s) : avertissement", any("trop court" in x for x in w), w)
    longt = [dict(three[0], title="x" * 130), three[1], three[2]]
    segs, w, er = sp.resolve(scenes(), longt, 360.0)
    check("titre de 130 caractères : avertissement", any("caractères" in x for x in w), w)
    segs, w, er = sp.resolve(scenes(), [dict(three[0], start="00:00:00,000", end="00:03:00,500")], 360.0)
    check("exactement 3 minutes acceptées, 3 min 0,5 s refusées", not segs and "3 minutes au plus" in er[0], er)
    segs, w, er = sp.resolve(scenes(), [dict(three[0], start="00:00:00,000", end="00:03:00,000")], 360.0)
    check("180 s pile : accepté", len(segs) == 1 and not er, (segs, er))

    out = sp.extractor_list(sp.resolve(scenes(), three, 360.0)[0])
    check("format de sortie : titre, début, fin et rien d'autre, temps HH:MM:SS,mmm",
          all(set(o) == {"title", "start", "end"} and re.fullmatch(r"\d\d:\d\d:\d\d,\d{3}", o["start"]) and re.fullmatch(r"\d\d:\d\d:\d\d,\d{3}", o["end"]) for o in out), out)
    sh = sp.shift([{"title": "t", "start": 5.0, "end": 15.0}, {"title": "u", "start": 30.0, "end": 40.0}], [(20.0, 10.0)])
    check("décalage par un insert de 10 s à 20 s : avant la coupe inchangé, après +10 s",
          sh[0]["start"] == 5.0 and sh[0]["end"] == 15.0 and sh[1]["start"] == 40.0 and sh[1]["end"] == 50.0, sh)
    sentences = sp.sentences_from_transcript({"words": [{"word": "Un", "start": 0, "end": 0.3}, {"word": "mot.", "start": 0.4, "end": 0.9}, {"word": "Deux", "start": 1.5, "end": 2.0}, {"word": "mots!", "start": 2.1, "end": 2.6}]})
    check("phrases reconstituées depuis les mots quand il n'y a pas de segments", sentences == [(0.0, 0.9), (1.5, 2.6)], sentences)


STORYBOARD = """# STORYBOARD — Test shorts

**Mode** : auto
%s
## 4. Scènes

### I1 — Début

- section: a · type: cards · fond: BG-00 · durée: 60

#### Étapes

- `I1.1#0` · cue « a » → **un mot**
  - kind: kw
  - text: Début
- `I1.1#1` · cue « b » → **la suite**
  - kind: kw
  - text: Suite
- `I1.1#2` · cue « c » → **encore**
  - kind: kw
  - text: Encore

### I2 — Milieu

- section: b · type: cards · fond: BG-00 · durée: 120

#### Étapes

- `I2.1#0` · cue « d » → **le fort**
  - kind: punch
  - text: Le fort
- `I2.1#1` · cue « e » → **le calme**
  - kind: kw
  - text: Calme

### I3 — Fin

- section: c · type: cards · fond: BG-00 · durée: 60

#### Étapes

- `I3.1#0` · cue « f » → **la chute**
  - kind: punch
  - text: La chute

## 6. Shorts

Trois séquences percutantes pour la promo.

| ID | Titre | Début | Fin | Pourquoi |
|---|---|---|---|---|
| SH01 | La métaphore du pistolet chargé | I1.1#0 | I1.1#1 | l'image qui ouvre la vidéo |
| SH02 | Le moment fort | I2.1#0 | I2.1#0 | la punchline du milieu |
| SH03 | La chute | I3.1#0 | I3.1#0 | la conclusion |
"""


def project(tmp, sb=STORYBOARD % ""):
    (tmp / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE.parent / "examples" / "demo" / "assets" / "gsap.min.js", tmp / "assets" / "gsap.min.js")
    (tmp / "assets" / "storyboard.md").write_text(sb, encoding="utf-8")


def build(tmp, *extra):
    return subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp)] + list(extra), cwd=str(tmp), capture_output=True, text=True)


def part_b(tmp):
    print("B. build")
    project(tmp)
    r = build(tmp)
    check("build : réussit et annonce les shorts avec la commande d'extraction", r.returncode == 0 and "shorts : 3 séquence(s)" in r.stdout and "video short-extractor" in r.stdout, r.stderr[-300:] + r.stdout[-300:])
    f = tmp / "data" / "shorts_segments.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    check("data/shorts_segments.json : 3 séquences, clés title/start/end uniquement", len(data) == 3 and all(set(d) == {"title", "start", "end"} for d in data), data)
    check("format des temps : HH:MM:SS,mmm", all(re.fullmatch(r"\d\d:\d\d:\d\d,\d{3}", d[k]) for d in data for k in ("start", "end")), data)
    check("titres repris du storyboard", data[0]["title"] == "La métaphore du pistolet chargé" and data[2]["title"] == "La chute", data)
    check("durées ≤ 3 minutes", all(sp.parse_tc(d["end"]) - sp.parse_tc(d["start"]) <= 180 for d in data), data)
    steps = json.loads((tmp / "data" / "steps.json").read_text(encoding="utf-8"))["steps"]
    first = [s for s in steps if s["id"] == "I1.1#0"][0]
    check("le premier short démarre au début de son étape de départ", abs(sp.parse_tc(data[0]["start"]) - first["t"]) < 0.01, (data[0], first))

    # avec un transcript : calage sur les phrases
    words = [{"word": "Début", "start": 0.0, "end": 0.5}, {"word": "calé.", "start": 0.6, "end": 1.0}]
    (tmp / "assets" / "transcript.json").write_text(json.dumps({"words": words, "segments": [{"start": 0.0, "end": 1.0, "text": "Début calé."}]}), encoding="utf-8")
    r = build(tmp, "--transcript", "assets/transcript.json")
    check("avec un transcript, le build réussit", r.returncode == 0, r.stderr[-300:] + r.stdout[-300:])

    t2 = tmp / "off"
    project(t2, STORYBOARD % "**Shorts** : aucun\n")
    r = build(t2)
    check("en-tête **Shorts** : aucun -> pas de fichier", r.returncode == 0 and not (t2 / "data" / "shorts_segments.json").exists())
    t3 = tmp / "off2"
    project(t3)
    build(t3)
    r = build(t3, "--no-shorts")
    check("--no-shorts : désactive et supprime le plan périmé", r.returncode == 0 and not (t3 / "data" / "shorts_segments.json").exists())
    t4 = tmp / "err1"
    project(t4, STORYBOARD.replace("| SH02 | Le moment fort | I2.1#0 | I2.1#0 |", "| SH02 | Le moment fort | I2 | I2 |").replace("durée: 120", "durée: 400"))
    r = build(t4)
    check("séquence de plus de 3 minutes : le build s'arrête, message qui nomme le short", r.returncode == 1 and "SH02" in r.stderr and "3 minutes au plus" in r.stderr, r.stderr[-300:])
    t5 = tmp / "err2"
    project(t5, STORYBOARD.replace("| SH03 | La chute | I3.1#0 |", "| SH03 | La chute | zzz |"))
    r = build(t5)
    check("début inconnu : erreur claire", r.returncode == 1 and "SH03" in r.stderr and "ne désigne ni une étape" in r.stderr, r.stderr[-300:])
    t6 = tmp / "plain"
    project(t6, re.sub(r"## 6\. Shorts.*", "", STORYBOARD % "", flags=re.S))
    r = build(t6)
    check("storyboard sans section Shorts : rien de nouveau", r.returncode == 0 and not (t6 / "data" / "shorts_segments.json").exists() and "shorts" not in r.stdout.lower(), r.stdout[-200:])


def part_c(tmp):
    print("C. shorts-export")
    root = tmp / "exp"
    project(root)
    build(root)
    exp = [sys.executable, str(HERE / "shorts-export.py"), "--root", str(root)]
    r = subprocess.run(exp, capture_output=True, text=True)
    out = root / "renders" / "shorts_segments.json"
    a = json.loads((root / "data" / "shorts_segments.json").read_text(encoding="utf-8"))
    check("sans inserts : copie identique dans renders/ et la commande à lancer", r.returncode == 0 and json.loads(out.read_text(encoding="utf-8")) == a
          and "video short-extractor renders/final.mp4 --segments renders/shorts_segments.json --layout fit-blur --output-dir shorts/" in r.stdout, r.stdout[-300:] + r.stderr[-200:])
    # post-render lit le storyboard minuté (étapes avec leurs temps) pour placer les coupes
    (root / "assets" / "storyboard.md").write_text("# SB\n\n- `I1.1#0` t=0.00 (20.0s) [off/kw] a\n- `I1.1#1` t=20.00 (20.0s) [off/kw] b\n", encoding="utf-8")
    ins = {"inserts": [{"id": "X1", "source": "c.mp4", "start": "0:10", "end": "0:20", "after": "I1.1#0"}]}
    (root / "assets" / "inserts.json").write_text(json.dumps(ins), encoding="utf-8")
    r = subprocess.run(exp + ["--inserts", "assets/inserts.json"], capture_output=True, text=True)
    b = json.loads(out.read_text(encoding="utf-8"))
    shift = sp.parse_tc(b[1]["start"]) - sp.parse_tc(a[1]["start"])
    check("avec un insert de 10 s après la 1re étape : les shorts qui suivent sont décalés de 10 s", r.returncode == 0 and abs(shift - 10.0) < 0.01, (a, b, r.stderr))
    r = subprocess.run([sys.executable, str(HERE / "shorts-export.py"), "--root", str(tmp / "nope")], capture_output=True, text=True)
    check("sans data/shorts_segments.json : erreur claire", r.returncode != 0)


def main():
    part_a()
    with tempfile.TemporaryDirectory() as d:
        part_b(Path(d))
        part_c(Path(d))
    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
