#!/usr/bin/env python3
"""Repère les séquences « Cast » (screencast OBS) dans la vidéo nettoyée.

OBS pose un filet vert pur (#00FF00, 10 px) en haut de l'image pendant les
screencasts. Ce script lit la seule bande supérieure de `cam-clean.mkv`, repère
les images où le filet est présent et écrit les intervalles dans un JSON.

    Il REPÈRE, il ne découpe pas : aucun fichier vidéo n'est produit, le média
    source n'est jamais modifié ni réencodé. Le filet est retiré plus tard, dans
    la composition HyperFrames (voir references/webcam.md).

Usage :
    python3 scripts/detect-cast.py assets/cam-clean.mkv --output assets/cast-segments.json

À lancer APRÈS clean-posthoc.py : le nettoyage supprime des silences et décale les
timecodes. Les intervalles sont exprimés dans le référentiel de `cam-clean.mkv` ;
un nouveau nettoyage impose une nouvelle détection.

Schéma de sortie (version 1) — intervalles semi-ouverts [start, end) :

    {
      "version": 1,
      "source": "assets/cam-clean.mkv",
      "source_size": 123456789,          # octets, pour vérifier que le JSON colle au média
      "source_mtime": 1767225600.123,    # secondes epoch (UTC), idem
      "duration": 245.6,                 # secondes (ffprobe)
      "width": 1920, "height": 1080,
      "fps": 30.0,
      "frames": 7368,                    # images lues
      "segments": [
        {"start": 42.35, "end": 78.9, "start_frame": 1271, "end_frame": 2367}
      ],                                  # end_frame exclusif ; [] si aucun filet
      "detector": { ...paramètres utilisés... }
    }

Aucune dépendance au-delà de ffmpeg/ffprobe et de la bibliothèque standard.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

SCHEMA_VERSION = 1

# --------------------------------------------------------------------------- #
# Paramètres de détection — tout se règle ici.
# Les valeurs en « px » sont données pour une image de 1080 px de haut et sont
# mises à l'échelle si la vidéo a une autre hauteur.
# --------------------------------------------------------------------------- #

# Zone examinée en haut de l'image (px). Le filet mesure 10 px : 20 laisse voir
# ce qu'il y a juste en dessous, pour distinguer un filet d'un grand aplat vert.
ZONE_PX = 20

# Colonnes d'échantillonnage après réduction horizontale (moyenne par zone).
# Plus bas = plus rapide ; 96 suffit pour mesurer la couverture en largeur.
SAMPLE_COLS = 96

# Un pixel est « vert » si le canal G est fort ET domine nettement R et B.
# Jamais d'égalité stricte avec #00FF00 : H.264 + sous-échantillonnage chroma
# 4:2:0 décalent les valeurs (typiquement R,B de 0 à ~40, G de ~215 à 255).
GREEN_MIN_G = 150          # G minimal
GREEN_DOMINANCE = 80       # G - max(R, B) minimal

# Une ligne est « filet » si cette part des colonnes est verte (très grande
# proportion de la largeur ; un peu de marge pour les coins arrondis d'OBS ou
# un overlay posé sur le bord).
ROW_COVERAGE_MIN = 0.92

# Épaisseur (lignes consécutives vertes depuis le bord supérieur) admise.
# En dessous : bruit / début de fondu ; au-dessus : aplat vert du contenu
# (slide verte, fond d'écran…), pas un filet.
BAND_MIN_PX = 6
BAND_MAX_PX = 16

# Tolérance temporelle.
# - un trou plus court est comblé (compression, image corrompue, flash) ;
# - un intervalle plus court est supprimé (micro-détection).
MAX_GAP_S = 0.25
MIN_SEGMENT_S = 0.50


# --------------------------------------------------------------------------- #
# Sonde ffprobe
# --------------------------------------------------------------------------- #

def die(msg: str) -> "None":
    print("ERREUR : " + msg, file=sys.stderr)
    sys.exit(1)


def probe(path: Path) -> dict:
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate,nb_frames,duration",
           "-show_entries", "format=duration", "-of", "json", str(path)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except FileNotFoundError:
        die("ffprobe introuvable (installer ffmpeg)")
    except subprocess.CalledProcessError as e:
        die("ffprobe a échoué sur %s : %s" % (path, e.stderr.strip()))
    info = json.loads(out)
    if not info.get("streams"):
        die("aucun flux vidéo dans %s" % path)
    st = info["streams"][0]

    def frac(s):
        try:
            f = Fraction(s)
            return f if f > 0 else None
        except (ValueError, ZeroDivisionError, TypeError):
            return None

    fps = frac(st.get("avg_frame_rate", "")) or frac(st.get("r_frame_rate", ""))
    if fps is None:
        die("fréquence d'images illisible pour %s" % path)
    dur = None
    for cand in (info.get("format", {}).get("duration"), st.get("duration")):
        try:
            dur = float(cand)
            break
        except (TypeError, ValueError):
            pass
    return {"width": int(st["width"]), "height": int(st["height"]), "fps": fps, "duration": dur}


# --------------------------------------------------------------------------- #
# Lecture de la bande supérieure
# --------------------------------------------------------------------------- #

def zone_rows(height: int) -> int:
    """Hauteur source (px) de la zone examinée, mise à l'échelle de l'image."""
    return max(4, min(height, round(ZONE_PX * height / 1080)))


def read_band(path: Path, width: int, height: int):
    """Générateur : un `bytes` RGB24 (SAMPLE_COLS × ZONE_PX) par image.

    ffmpeg ne décode que le flux vidéo, recadre la bande du haut, la réduit en
    largeur (moyenne `area`) et la sert brute sur stdout. Rien n'est écrit sur disque.
    """
    zr = zone_rows(height)
    vf = "crop=%d:%d:0:0,scale=%d:%d:flags=area,format=rgb24" % (width, zr, SAMPLE_COLS, ZONE_PX)
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", str(path), "-map", "0:v:0", "-an", "-sn",
           "-vsync", "passthrough", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    size = SAMPLE_COLS * ZONE_PX * 3
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            yield buf
    finally:
        proc.stdout.close()
        err = proc.stderr.read().decode("utf-8", "replace").strip()
        rc = proc.wait()
        if rc != 0:
            die("ffmpeg a échoué (%d) : %s" % (rc, err[-400:]))


def band_thickness(buf: bytes) -> int:
    """Nombre de lignes consécutives « filet vert » à partir du bord supérieur."""
    need = ROW_COVERAGE_MIN * SAMPLE_COLS
    stride = SAMPLE_COLS * 3
    n = 0
    for row in range(ZONE_PX):
        base = row * stride
        r = buf[base:base + stride:3]
        g = buf[base + 1:base + stride:3]
        b = buf[base + 2:base + stride:3]
        ok = 0
        for rr, gg, bb in zip(r, g, b):
            if gg >= GREEN_MIN_G and gg - (rr if rr > bb else bb) >= GREEN_DOMINANCE:
                ok += 1
        if ok < need:
            break
        n += 1
    return n


def classify(buf: bytes) -> bool:
    """Vrai si l'image porte un filet : épaisseur dans [BAND_MIN_PX, BAND_MAX_PX]."""
    t = band_thickness(buf)
    return BAND_MIN_PX <= t <= BAND_MAX_PX


# --------------------------------------------------------------------------- #
# Filtrage temporel
# --------------------------------------------------------------------------- #

def runs(flags):
    """Intervalles [a, b) d'images consécutives vraies."""
    out, start = [], None
    for i, f in enumerate(flags):
        if f and start is None:
            start = i
        elif not f and start is not None:
            out.append([start, i])
            start = None
    if start is not None:
        out.append([start, len(flags)])
    return out


def clean_runs(rs, fps: Fraction, total: int):
    """Comble les trous courts puis écarte les intervalles trop courts."""
    max_gap = int(MAX_GAP_S * fps)
    min_len = max(1, int(round(MIN_SEGMENT_S * fps)))
    merged = []
    for a, b in rs:
        if merged and a - merged[-1][1] <= max_gap:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [(a, min(b, total)) for a, b in merged if b - a >= min_len]


# --------------------------------------------------------------------------- #
# Programme
# --------------------------------------------------------------------------- #

def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?", default="assets/cam-clean.mkv",
                    help="vidéo nettoyée (défaut : assets/cam-clean.mkv)")
    ap.add_argument("--output", "-o", default=None,
                    help="JSON de sortie (défaut : cast-segments.json à côté de la vidéo)")
    ap.add_argument("--quiet", "-q", action="store_true")
    a = ap.parse_args(argv)

    src = Path(a.video)
    if not src.is_file():
        die("vidéo absente : %s" % src)
    out = Path(a.output) if a.output else src.with_name("cast-segments.json")
    if out.resolve() == src.resolve():
        die("la sortie ne peut pas être la vidéo source")

    meta = probe(src)
    fps = meta["fps"]
    st = src.stat()  # relevé avant lecture : détecte un média modifié pendant l'analyse

    flags = [classify(buf) for buf in read_band(src, meta["width"], meta["height"])]
    total = len(flags)
    segs = clean_runs(runs(flags), fps, total)

    def t(frame: int) -> float:
        return round(float(Fraction(frame) / fps), 3)

    duration = meta["duration"] if meta["duration"] is not None else float(Fraction(total) / fps)
    segments = [{"start": t(a), "end": t(b), "start_frame": a, "end_frame": b} for a, b in segs]
    if total and abs(total / float(fps) - duration) > max(0.5, 2 / float(fps)):
        print("AVERTISSEMENT : %d images lues pour %.2f s à %.3f i/s : durée incohérente "
              "(vidéo à fréquence variable ?)" % (total, duration, float(fps)), file=sys.stderr)

    doc = {
        "version": SCHEMA_VERSION,
        "source": src.as_posix(),
        "source_size": st.st_size,
        "source_mtime": round(st.st_mtime, 3),
        "duration": round(duration, 3),
        "width": meta["width"],
        "height": meta["height"],
        "fps": round(float(fps), 6),
        "frames": total,
        "segments": segments,
        "detector": {
            "zone_px": ZONE_PX, "sample_cols": SAMPLE_COLS,
            "green_min_g": GREEN_MIN_G, "green_dominance": GREEN_DOMINANCE,
            "row_coverage_min": ROW_COVERAGE_MIN,
            "band_min_px": BAND_MIN_PX, "band_max_px": BAND_MAX_PX,
            "max_gap_s": MAX_GAP_S, "min_segment_s": MIN_SEGMENT_S,
        },
    }
    if src.stat().st_mtime != st.st_mtime or src.stat().st_size != st.st_size:
        die("le média a changé pendant l'analyse : relancer")
    atomic_write_json(out, doc)
    if not a.quiet:
        print("OK -> %s : %d intervalle(s) Cast sur %d images (%.1f s)" % (out, len(segments), total, duration))
        for s in segments:
            print("  [%.3f, %.3f) · images %d–%d" % (s["start"], s["end"], s["start_frame"], s["end_frame"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
