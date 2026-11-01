#!/usr/bin/env python3
"""Nettoyage post-hoc conjoint A/V : cappe les silences à ~0.35s sans désync.
Usage: python3 scripts/clean-posthoc.py assets/cam-original.mkv
Sorties: assets/cam-clean.mkv (A/V nettoyés synchrones), assets/voix-posthoc-v1.wav, assets/clean-map.json
"""
import json, re, subprocess, sys
from pathlib import Path
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("assets/cam-original.mkv")
DST_MKV = Path("assets/cam-clean.mkv")
DST_WAV = Path("assets/voix-posthoc-v1.wav")
MAP = Path("assets/clean-map.json")
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
MAP.write_text(json.dumps({"src":str(SRC),"noise":NOISE,"min_d":MIN_D,"keep":KEEP,
    "keeps":keeps,"cuts":cuts},indent=1))
n = len(keeps)
# Vidéo : select (éprouvé OK) ; audio : atrim+concat (aselect ne coupe pas).
vtrim = "".join(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}];" for i,(a,b) in enumerate(keeps))
atrim = "".join(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}];" for i,(a,b) in enumerate(keeps))
vcat = "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
acat = "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,aresample=48000,loudnorm[a]"
fc = vtrim + atrim + vcat + ";" + acat
subprocess.run(["ffmpeg","-y","-i",str(SRC),"-filter_complex",fc,
    "-map","[v]","-map","[a]",
    "-c:v","libx264","-preset","veryfast","-crf","20","-c:a","aac","-ar","48000","-ac","2",
    str(DST_MKV)],check=True)
subprocess.run(["ffmpeg","-y","-i",str(DST_MKV),"-ar","48000","-ac","2",str(DST_WAV)],check=True)
print(f"OK -> {DST_MKV} + {DST_WAV}")
