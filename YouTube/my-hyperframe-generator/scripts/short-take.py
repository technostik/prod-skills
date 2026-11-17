#!/usr/bin/env python3
"""Prise d'un Short (format 9:16) : une seule vidéo, un seul chapitre, pas de concaténation.

Par défaut, la source est la DERNIÈRE vidéo de `$HF_VIDEOS_DIR` (défaut `~/Vidéos`, le dossier des prises de la
skill), sans descendre dans les sous-dossiers (`OBS/assets`…). Sorties, au même contrat que `concat-mkv.sh`
(la suite est donc la même : `clean-posthoc.py`, `detect-cast.py`, `transcript-export.py`) :

  assets/cam-original.mkv   la prise, remuxée sans réencodage (réencodée seulement si le remux échoue)
  assets/voix-brut.wav      sa piste audio
  assets/take.json          la source choisie, ses dimensions, sa durée

Le format d'entrée doit déjà être 9:16 si la prise contient une webcam : sinon un avertissement, la vidéo sera
rognée au centre (`object-fit: cover`) dans la composition.

Usage : python3 scripts/short-take.py [vidéo] [--dir DOSSIER] [--out assets/cam-original.mkv] [--which]
  --which : affiche seulement la vidéo retenue.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

EXTS = {".mkv", ".mp4", ".mov", ".webm", ".m4v"}
SETTLE_S = 2.0          # un fichier modifié depuis moins de 2 s est encore en cours d'écriture


def videos_dir(arg=None):
    return Path(arg or os.environ.get("HF_VIDEOS_DIR") or "~/Vidéos").expanduser()


def latest_video(folder, now=None):
    """La vidéo la plus récente (date de modification) du dossier, hors sous-dossiers et fichiers cachés ou en cours d'écriture."""
    now = time.time() if now is None else now
    found = [f for f in Path(folder).iterdir()
             if f.is_file() and f.suffix.lower() in EXTS and not f.name.startswith(".")
             and now - f.stat().st_mtime >= SETTLE_S]
    return max(found, key=lambda f: (f.stat().st_mtime, f.name)) if found else None


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("ERREUR : ffprobe ne lit pas %s : %s" % (path, out.stderr.strip()[-200:]))
    doc = json.loads(out.stdout)
    st = (doc.get("streams") or [{}])[0]
    w, h = int(st.get("width") or 0), int(st.get("height") or 0)
    rot = abs(int(float(((st.get("side_data_list") or [{}])[0]).get("rotation", 0)))) % 180
    if rot == 90:
        w, h = h, w
    return {"width": w, "height": h, "duration": float(doc.get("format", {}).get("duration") or 0)}


def is_vertical(w, h):
    return h > 0 and abs(w / float(h) - 9 / 16.0) < 0.03


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?", default=None, help="défaut : la dernière vidéo de $HF_VIDEOS_DIR")
    ap.add_argument("--dir", default=None, help="dossier des prises (défaut : $HF_VIDEOS_DIR, sinon ~/Vidéos)")
    ap.add_argument("--out", default="assets/cam-original.mkv")
    ap.add_argument("--which", action="store_true", help="affiche la vidéo retenue et s'arrête")
    a = ap.parse_args(argv)

    if a.video:
        src = Path(a.video).expanduser()
        if not src.is_file():
            sys.exit("ERREUR : vidéo absente : %s" % src)
    else:
        folder = videos_dir(a.dir)
        if not folder.is_dir():
            sys.exit("ERREUR : dossier des prises absent : %s (HF_VIDEOS_DIR, ou donner la vidéo)" % folder)
        src = latest_video(folder)
        if src is None:
            sys.exit("ERREUR : aucune vidéo (%s) dans %s" % (", ".join(sorted(EXTS)), folder))
    info = probe(src)
    print("prise : %s (%d×%d, %.1f s)" % (src, info["width"], info["height"], info["duration"]))
    if a.which:
        return 0
    if not is_vertical(info["width"], info["height"]):
        print("AVERTISSEMENT : la prise n'est pas en 9:16 (%d×%d) : elle sera rognée au centre dans la composition. "
              "Pour un Short avec webcam, filmer en vertical." % (info["width"], info["height"]), file=sys.stderr)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0?",
                        "-c", "copy", str(out)], capture_output=True, text=True)
    if r.returncode != 0:
        print("remux impossible (%s) : réencodage 30 i/s, AAC 48 kHz" % r.stderr.strip()[-120:], file=sys.stderr)
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0?",
                            "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac",
                            "-ar", "48000", "-ac", "2", str(out)], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("ERREUR : ffmpeg : " + r.stderr.strip()[-300:])
    wav = out.parent / "voix-brut.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out), "-vn", "-ar", "48000", "-ac", "2", str(wav)],
                   capture_output=True)
    (out.parent / "take.json").write_text(json.dumps(
        {"source": str(src), "format": "9:16", "width": info["width"], "height": info["height"],
         "duration": info["duration"], "vertical": is_vertical(info["width"], info["height"])},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("OK -> %s (+ %s, take.json)" % (out, wav.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
