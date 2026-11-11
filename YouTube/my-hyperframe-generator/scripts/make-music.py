#!/usr/bin/env python3
"""Génère les musiques de data/music.json avec la commande `sound music` de fast-market.

  python3 scripts/make-music.py --plan     # ce qui sera généré, sans rien lancer
  python3 scripts/make-music.py            # génère les fichiers absents (instrumental, jamais de voix chantée)
  options : --root DIR  --engine acestep|musicgen  --max-duration 120  --force  --dry-run

Un fichier est nommé d'après (musique, prompt, graine, durée) : tant que rien ne change il est réutilisé,
et deux repères qui partagent la même musique et la même durée n'en génèrent qu'un.

Commande : `sound music PROMPT -i -d SECONDES [-S GRAINE] [-e MOTEUR] -o FICHIER -F json`. La commande est
`sound` du PATH, ou celle de la variable d'environnement SOUND_CMD.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def die(msg):
    print("erreur : " + msg, file=sys.stderr)
    sys.exit(1)


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def unique_jobs(cues, max_duration):
    """Un travail par fichier : le même (musique, prompt, graine, durée) n'est généré qu'une fois."""
    jobs, notes = {}, []
    for c in cues:
        job = jobs.setdefault(c["file"], {"file": c["file"], "music": c["music"], "prompt": c["prompt"],
                                          "seed": c["seed"], "duration": c["gen_duration"], "cues": []})
        job["cues"].append(c["cue"])
    for job in jobs.values():
        if job["duration"] > max_duration:
            notes.append("%s : %d s demandées, le moteur est limité à %d s : le mixage coupera le repère à la durée "
                         "du fichier (ou raccourcir la musique avec `music_until`)" % (job["file"], job["duration"], max_duration))
            job["duration"] = int(max_duration)
    return list(jobs.values()), notes


def sound_command(job, engine, out_path):
    sound = os.environ.get("SOUND_CMD") or shutil.which("sound")
    if not sound:
        die("commande `sound` introuvable (CLI fast-market) : l'ajouter au PATH ou définir SOUND_CMD")
    cmd = [sound, "music", job["prompt"], "-i", "-d", str(job["duration"]), "-o", str(out_path), "-F", "json"]
    if job["seed"] is not None:
        cmd += ["-S", str(job["seed"])]
    if engine:
        cmd += ["-e", engine]
    return cmd


def main(argv=None):
    ap = argparse.ArgumentParser(description="Génère les musiques du plan data/music.json.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--plan-file", default="data/music.json")
    ap.add_argument("--engine", choices=("acestep", "musicgen"), default=None)
    ap.add_argument("--max-duration", type=float, default=120.0, help="durée maximale demandée au moteur (défaut 120 s)")
    ap.add_argument("--plan", action="store_true", help="affiche ce qui serait généré, sans rien lancer")
    ap.add_argument("--dry-run", action="store_true", help="affiche les commandes sans les exécuter")
    ap.add_argument("--force", action="store_true", help="régénère même si le fichier existe")
    a = ap.parse_args(argv)

    root = Path(a.root).resolve()
    os.chdir(root)
    pf = Path(a.plan_file)
    if not pf.exists():
        die("%s absent : lancer build.py (storyboard avec un registre §1d et des `music:`)" % pf)
    plan = json.loads(pf.read_text(encoding="utf-8"))
    jobs, notes = unique_jobs(plan["cues"], a.max_duration)
    if not jobs:
        print("aucune musique à générer")
        return

    print("Musiques (%.0f %% du film) :" % (100 * plan.get("coverage", 0)))
    for c in plan["cues"]:
        print("  %-4s %-4s %-13s %7.1f → %7.1f s  vol %.2f  %s" % (c["cue"], c["music"], c["step"], c["start"], c["end"],
                                                                 c["volume"], c.get("role", "")))
    todo = []
    for j in jobs:
        have = Path(j["file"]).exists() and not a.force
        print("  fichier %-34s %3d s  %s" % (j["file"], j["duration"], "déjà là" if have else "à générer"))
        if not have:
            todo.append(j)
    for n in notes:
        print("avertissement : " + n)
    if a.plan:
        return

    for j in todo:
        out = Path(j["file"])
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = sound_command(j, a.engine, out)
        print("$ " + " ".join(repr(x) if " " in x else x for x in cmd))
        if a.dry_run:
            continue
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            die("génération échouée pour %s (code %s) : %s" % (j["file"], r.returncode, (r.stderr or r.stdout).strip()[-300:]))
        d = probe_duration(out)
        short = d is not None and d < j["duration"] - 1.0
        print("écrit : %s (%s s)%s" % (out, "%.1f" % d if d else "?", "  ⚠ plus court que demandé" if short else ""))
    if not a.dry_run:
        print("suite : python3 scripts/mix-music.py (mixe sous la voix dans renders/full-music.mp4)")


if __name__ == "__main__":
    main()
