#!/usr/bin/env bash
# Concatène des tronçons .mkv ordonnés -> assets/cam-original.mkv + chapters.json + voix-brut.wav
# chapters.json : pour chaque tronçon d'origine, `start` / `end` cumulés et `duration` (secondes),
# dans la vidéo concaténée ORIGINALE (cam-original.mkv, avant nettoyage). Ces bornes ne valent pas
# pour cam-clean.mkv : clean-posthoc.py supprime des silences et décale les timecodes. Les
# intervalles Cast (cast-segments.json) ne s'y réfèrent jamais.
# Usage: scripts/concat-mkv.sh <sortie-mkv> <troncon1.mkv> [troncon2.mkv ...]
# Ex: scripts/concat-mkv.sh assets/cam-original.mkv prise1.mkv prise2.mkv
set -euo pipefail
if [ $# -lt 2 ]; then echo "usage: $0 <sortie.mkv> <troncon1.mkv> [...]" >&2; exit 1; fi
OUT="$1"; shift
LIST=$(mktemp /tmp/opencode/concat-XXXXXX.txt 2>/dev/null || mktemp /tmp/concat-XXXXXX.txt)
META=$(mktemp /tmp/chapters-XXXXXX.tsv)
trap 'rm -f "$LIST" "$META"' EXIT
for f in "$@"; do
  [ -f "$f" ] || { echo "manquant: $f" >&2; exit 1; }
  printf "file '%s'\n" "$(realpath "$f")" >> "$LIST"
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  printf '%s\t%s\n' "$f" "$D" >> "$META"
done
mkdir -p "$(dirname "$OUT")"
# Lossless si mêmes codecs, sinon normaliser (re-encode 1080p30 / aac 48kHz stereo).
# Tentative 1 : concat demuxer en copie ; repli : re-encode.
if ffmpeg -y -f concat -safe 0 -i "$LIST" -c copy "$OUT" 2>/tmp/opencode/concat-err.log || ffmpeg -y -f concat -safe 0 -i "$LIST" -vf scale=1920:1080 -r 30 -c:v libx264 -preset medium -crf 20 -c:a aac -ar 48000 -ac 2 "$OUT"; then
  :
else
  cat /tmp/opencode/concat-err.log >&2; exit 1
fi
ffmpeg -y -i "$OUT" -ar 48000 -ac 2 "${OUT%.mkv}-brut.wav" 2>/dev/null || ffmpeg -y -i "$OUT" -ar 48000 -ac 2 assets/voix-brut.wav
python3 - "$OUT" "$META" > assets/chapters.json <<'PY'
import json, sys
out, meta = sys.argv[1], sys.argv[2]
t, items = 0.0, []
for line in open(meta, encoding="utf-8"):
    f, d = line.rstrip("\n").rsplit("\t", 1)
    d = float(d)
    items.append({"file": f, "start": round(t, 3), "end": round(t + d, 3), "duration": round(d, 3)})
    t += d
print(json.dumps({"concat": out, "timebase": "cam-original (avant nettoyage)", "troncons": items},
                 ensure_ascii=False, indent=2))
PY
echo "OK -> $OUT + assets/chapters.json"
