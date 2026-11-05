#!/usr/bin/env python3
"""Nettoyage post-hoc conjoint A/V : cappe les silences à ~0.35s sans désync.
Usage: python3 scripts/clean-posthoc.py assets/cam-original.mkv [--version N]
       [--out-mkv assets/cam-clean.mkv] [--out-wav F] [--map F]
Sorties (N = prochain numéro libre, jamais d'écrasement d'une passe précédente) :
  assets/cam-clean.mkv        master A/V nettoyé (nom stable, réécrit à chaque passe)
  assets/voix-posthoc-vN.wav  audio nettoyé de cette passe
  assets/clean-map-vN.json    carte des coupes de cette passe (même N que le wav)
Le nettoyage décale les timecodes : toute détection Cast antérieure est périmée
(relancer scripts/detect-cast.py après chaque passe).
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("src", nargs="?", default="assets/cam-original.mkv")
ap.add_argument("--out-mkv", default="assets/cam-clean.mkv", help="master nettoyé (nom stable)")
ap.add_argument("--out-wav", default=None, help="défaut : <dossier du master>/voix-posthoc-vN.wav")
ap.add_argument("--map", default=None, help="défaut : <dossier du master>/clean-map-vN.json")
ap.add_argument("--version", type=int, default=None, help="forcer N (refuse d'écraser un fichier existant)")
args = ap.parse_args()


def next_version(folder: Path) -> int:
    """Plus grand N déjà présent (voix-posthoc-vN.wav ou clean-map-vN.json) + 1 ; comparaison numérique."""
    n = 0
    for pat in ("voix-posthoc-v*.wav", "clean-map-v*.json"):
        for f in folder.glob(pat):
            m = re.search(r"-v(\d+)\.(?:wav|json)$", f.name)
            if m:
                n = max(n, int(m.group(1)))
    return n + 1


SRC = Path(args.src)
DST_MKV = Path(args.out_mkv)
DST_MKV.parent.mkdir(parents=True, exist_ok=True)
VER = args.version or next_version(DST_MKV.parent)
DST_WAV = Path(args.out_wav) if args.out_wav else DST_MKV.parent / ("voix-posthoc-v%d.wav" % VER)
MAP = Path(args.map) if args.map else DST_MKV.parent / ("clean-map-v%d.json" % VER)
for _f in (DST_WAV, MAP):
    if _f.exists():
        sys.exit("ERREUR : %s existe déjà (jamais d'écrasement d'une passe précédente) ; "
                 "choisir --version / --out-wav / --map" % _f)
NOISE, MIN_D, KEEP = "-35dB", 0.6, 0.35
p = subprocess.run(["ffmpeg","-hide_banner","-i",str(SRC),
    "-af",f"silencedetect=noise={NOISE}:d={MIN_D}","-f","null","-"],
    capture_output=True, text=True)
sils = re.findall(r"silence_start: ([\d.]+).*?silence_end: ([\d.]+)", p.stderr, re.S)
dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
    "-of","csv=p=0",str(SRC)],capture_output=True,text=True).stdout.strip())
cuts, keeps, cur = [], [], 0.0
for s_,e_ in sils:
    s,e = float(s_),float(e_)
    if e-s <= KEEP+0.05: continue
    cs,ce = s+(KEEP/2), e-(KEEP/2)
    if cs>cur: keeps.append((cur,min(cs,dur)))
    cuts.append((cs,ce)); cur = ce
if cur<dur: keeps.append((cur,dur))
sel = "+".join(f"between(t\\,{a:.3f}\\,{b:.3f})" for a,b in keeps)
print(f"dur={dur:.1f}s silences={len(sils)} coupes={len(cuts)} segments={len(keeps)} "
      f"estim_net={sum(b-a for a,b in keeps):.1f}s")
MAP.write_text(json.dumps({"version":VER,"src":str(SRC),"clean":str(DST_MKV),"wav":str(DST_WAV),
    "noise":NOISE,"min_d":MIN_D,"keep":KEEP,"keeps":keeps,"cuts":cuts},indent=1))
n = len(keeps)
# Vidéo : select (éprouvé OK) ; audio : atrim+concat (aselect ne coupe pas).
vtrim = "".join(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}];" for i,(a,b) in enumerate(keeps))
atrim = "".join(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}];" for i,(a,b) in enumerate(keeps))
vcat = "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
acat = "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,aresample=48000,loudnorm[a]"
fc = vtrim + atrim + vcat + ";" + acat
# Écriture dans un fichier temporaire puis remplacement : un échec ne laisse pas un master tronqué.
TMP_MKV = DST_MKV.with_name(DST_MKV.stem + ".tmp" + DST_MKV.suffix)
subprocess.run(["ffmpeg","-y","-i",str(SRC),"-filter_complex",fc,
    "-map","[v]","-map","[a]",
    "-c:v","libx264","-preset","veryfast","-crf","20","-c:a","aac","-ar","48000","-ac","2",
    str(TMP_MKV)],check=True)
os.replace(TMP_MKV, DST_MKV)
subprocess.run(["ffmpeg","-y","-i",str(DST_MKV),"-ar","48000","-ac","2",str(DST_WAV)],check=True)
print(f"OK (passe v{VER}) -> {DST_MKV} + {DST_WAV} + {MAP}")
print("Si la prise contient des screencasts OBS : relancer "
      f"python3 scripts/detect-cast.py {DST_MKV} --output {DST_MKV.parent / 'cast-segments.json'} "
      "(les timecodes ont changé).")
