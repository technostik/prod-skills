#!/usr/bin/env python3
"""Mixe les musiques de data/music.json sous la voix du master.

  python3 scripts/mix-music.py            # renders/full.mp4 -> renders/full-music.mp4
  options : --root DIR  --master FILE  --out FILE  --plan-file FILE  --scale 1.0
            --no-duck  --duck-ratio 6  --print-graph  --dry-run

La musique ne surpasse jamais la voix : chaque repère est posé à son temps, avec un fondu d'entrée et de
sortie, à son volume, puis **comprimée par la voix** (sidechain : dès que la voix parle, la musique baisse
fortement (≈ 12 dB et plus) ; elle remonte dans les silences, c'est ce qui fait les montées). La vidéo n'est pas ré-encodée
(`-c:v copy`), seule la piste audio l'est. Un limiteur final évite l'écrêtage.

Les temps sont ceux du master, avant les inserts : `post-render.py` ajoute les inserts au master, donc
la musique mixée ici reste calée (`post-render.py` utilise renders/full-music.mp4 s'il existe).
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SR = 48000
DUCK_THRESHOLD = 0.01       # niveau de voix à partir duquel la musique baisse (amplitude linéaire)
DUCK_RATIO = 8.0
DUCK_ATTACK_MS = 10
DUCK_RELEASE_MS = 600
LIMIT = 0.95


def die(msg):
    print("erreur : " + msg, file=sys.stderr)
    sys.exit(1)


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration:stream=codec_type",
                        "-of", "json", str(path)], capture_output=True, text=True)
    try:
        j = json.loads(r.stdout)
        dur = float(j["format"]["duration"])
        kinds = {s.get("codec_type") for s in j.get("streams", [])}
        return dur, kinds
    except (ValueError, KeyError, json.JSONDecodeError):
        return None, set()


def cue_chain(k, cue, file_dur, scale):
    """Chaîne de filtres d'un repère (entrée k+1) : coupe, fondus, volume, retard."""
    length = min(cue["duration"], file_dur)
    fi = max(0.0, min(float(cue.get("fade_in", 1.5)), length / 2))
    fo = max(0.0, min(float(cue.get("fade_out", 3.0)), length / 2))
    delay = int(round(cue["start"] * 1000))
    vol = float(cue["volume"]) * scale
    f = ["aresample=%d" % SR, "aformat=sample_fmts=fltp:channel_layouts=stereo",
         "atrim=0:%.3f" % length, "asetpts=PTS-STARTPTS"]
    if fi > 0:
        f.append("afade=t=in:st=0:d=%.3f" % fi)
    if fo > 0:
        f.append("afade=t=out:st=%.3f:d=%.3f" % (length - fo, fo))
    f += ["volume=%.4f" % vol, "adelay=%d|%d" % (delay, delay)]
    return "[%d:a]%s[m%d]" % (k + 1, ",".join(f), k)


def build_graph(cues, durations, scale=1.0, duck=True, ratio=DUCK_RATIO):
    """Graphe ffmpeg complet. Entrée 0 = master (voix), entrées 1..N = un fichier par repère."""
    parts = [cue_chain(k, c, durations[k], scale) for k, c in enumerate(cues)]
    n = len(cues)
    if n == 1:
        parts.append("[m0]anull[mus]")
    else:
        parts.append("%samix=inputs=%d:normalize=0:duration=longest[mus]" % ("".join("[m%d]" % k for k in range(n)), n))
    if duck:
        parts.append("[0:a]aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo,asplit=2[vo][sc]" % SR)
        parts.append("[mus][sc]sidechaincompress=threshold=%.4f:ratio=%.1f:attack=%d:release=%d:makeup=1[duck]"
                     % (DUCK_THRESHOLD, ratio, DUCK_ATTACK_MS, DUCK_RELEASE_MS))
    else:
        parts.append("[0:a]aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo[vo]" % SR)
        parts.append("[mus]anull[duck]")
    parts.append("[vo][duck]amix=inputs=2:normalize=0:duration=first:dropout_transition=0,alimiter=limit=%.2f[a]" % LIMIT)
    return ";".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mixe la musique sous la voix (ducking), sans ré-encoder la vidéo.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--master", default="renders/full.mp4")
    ap.add_argument("--out", default="renders/full-music.mp4")
    ap.add_argument("--plan-file", default="data/music.json")
    ap.add_argument("--scale", type=float, default=1.0, help="multiplicateur du volume de toutes les musiques")
    ap.add_argument("--no-duck", action="store_true", help="pas de compression par la voix (déconseillé)")
    ap.add_argument("--duck-ratio", type=float, default=DUCK_RATIO, help="taux de compression par la voix (défaut %g)" % DUCK_RATIO)
    ap.add_argument("--print-graph", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    os.chdir(Path(a.root).resolve())
    pf = Path(a.plan_file)
    if not pf.exists():
        die("%s absent : pas de musique dans le storyboard (ou build.py pas relancé)" % pf)
    plan = json.loads(pf.read_text(encoding="utf-8"))
    cues = plan.get("cues") or []
    if not cues:
        die("aucun repère dans %s" % pf)
    master = Path(a.master)
    if not master.exists():
        die("master absent : %s (rendre la composition d'abord)" % master)
    mdur, kinds = probe(master)
    if "audio" not in kinds:
        die("%s n'a pas de piste audio : rien à mixer sous la voix" % master)

    use, durations, missing = [], [], []
    for c in cues:
        f = Path(c["file"])
        if not f.exists():
            missing.append(c["file"])
            continue
        d, _ = probe(f)
        if d is None:
            die("fichier audio illisible : %s" % f)
        if c["start"] >= (mdur or 1e9):
            print("avertissement : %s commence après la fin du master, ignoré" % c["cue"])
            continue
        if d < c["duration"] - 1.0:
            print("avertissement : %s : le fichier dure %.1f s pour %.1f s demandées, la musique s'arrête avant" % (c["cue"], d, c["duration"]))
        use.append(c)
        durations.append(d)
    if missing:
        die("fichiers manquants : %s (lancer scripts/make-music.py)" % ", ".join(sorted(set(missing))))
    if not use:
        die("aucun repère utilisable")

    graph = build_graph(use, durations, a.scale, not a.no_duck, a.duck_ratio)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(master)]
    for c in use:
        cmd += ["-i", c["file"]]
    cmd += ["-filter_complex", graph, "-map", "0:v?", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
            "-movflags", "+faststart", a.out]
    if a.print_graph:
        print(graph)
    if a.dry_run:
        print("$ " + " ".join(cmd))
        return
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die("ffmpeg a échoué : " + r.stderr.strip()[-500:])
    odur, _ = probe(a.out)
    print("écrit : %s (%.2f s ; master %.2f s ; %d musique(s), ducking %s)" % (a.out, odur or 0, mdur or 0, len(use), "non" if a.no_duck else "oui"))
    if odur and mdur and abs(odur - mdur) > 0.3:
        print("avertissement : durée différente du master (%.2f s contre %.2f s)" % (odur, mdur), file=sys.stderr)


if __name__ == "__main__":
    main()
