#!/usr/bin/env bash
# Test de bout en bout de post-render.py sur des médias synthétiques (FFmpeg seulement, ~1 min).
# Vérifie : durée finale, hauteur du son de l'insert (+5 %), master et signature intacts.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
cd "$T"; mkdir -p renders assets/src
F="-v error -y"
ffmpeg $F -f lavfi -i testsrc2=s=1920x1080:r=30:d=14 -f lavfi -i sine=f=440:r=48000:d=14 -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest renders/full.mp4
ffmpeg $F -f lavfi -i testsrc2=s=1280x720:r=60:d=6 -f lavfi -i sine=f=880:r=44100:d=6 -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest assets/src/a.mp4
ffmpeg $F -f lavfi -i color=c=blue:s=1280x720:r=30:d=1 -f lavfi -i sine=f=300:r=48000:d=1 -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a aac -shortest assets/src/outro.mp4
cat > assets/scenario-hyperframes.md <<'MD'
### I1 — Test
- `I1.1#0` t=0.00 (6.0s) [off/kw] lorem
- `I1.1#1` t=6.00 (4.0s) [pip/kw] ipsum
- `I1.1#2` t=10.00 (4.0s) [off/kw] dolor
MD
cat > assets/inserts.json <<'JSON'
{"outro": "assets/src/outro.mp4",
 "inserts": [{"id": "a", "source": "assets/src/a.mp4", "start": "0:01", "end": "0:05", "after": "I1.1#1"}]}
JSON
python3 "$HERE/post-render.py" --plan >/dev/null
python3 "$HERE/post-render.py"
python3 - <<'PY'
import json, math, struct, subprocess, wave
def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
def freq(t0, d=0.8):
    subprocess.run(["ffmpeg","-y","-v","error","-ss",str(t0),"-t",str(d),"-i","renders/final.mp4","-vn","-ac","1","-ar","48000","seg.wav"],check=True)
    w = wave.open("seg.wav"); n = w.getnframes(); s = struct.unpack("<%dh" % n, w.readframes(n))
    return sum(1 for i in range(1, n) if (s[i-1] < 0) != (s[i] < 0)) / 2 / (n / 48000)
d = dur("renders/final.mp4"); exp = 14 + 4 + 1
ok = abs(d - exp) < 0.3 and abs(freq(3) - 440) < 8 and abs(freq(11) - 880 * 1.05) < 25 and abs(freq(14.4 + 4 + 0.1, 0.5) - 300) < 12
print("durée %.2f s (attendu %.2f s) ; master %.0f Hz ; insert %.0f Hz ; signature %.0f Hz" % (d, exp, freq(3), freq(11), freq(18.6, 0.5)))
raise SystemExit(0 if ok else "ÉCHEC")
PY
echo "test-post-render : OK"
