#!/usr/bin/env bash
# Concatène des tronçons .mkv ordonnés -> assets/cam-original.mkv + chapters.json + voix-brut.wav
# Usage: scripts/concat-mkv.sh <sortie-mkv> <troncon1.mkv> [troncon2.mkv ...]
# Ex: scripts/concat-mkv.sh assets/cam-original.mkv prise1.mkv prise2.mkv
set -euo pipefail
if [ $# -lt 2 ]; then echo "usage: $0 <sortie.mkv> <troncon1.mkv> [...]" >&2; exit 1; fi
OUT="$1"; shift
LIST=$(mktemp /tmp/opencode/concat-XXXXXX.txt 2>/dev/null || mktemp /tmp/concat-XXXXXX.txt)
trap 'rm -f "$LIST"' EXIT
DUR=0
JSON_ENTRIES=""
for f in "$@"; do
  [ -f "$f" ] || { echo "manquant: $f" >&2; exit 1; }
  printf "file '%s'\n" "$(realpath "$f")" >> "$LIST"
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  JSON_ENTRIES="$JSON_ENTRIES{\"file\":\"$f\",\"duration\":$D},"
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
echo "{\"concat\":\"$OUT\",\"troncons\":[${JSON_ENTRIES%,}]}" > assets/chapters.json
echo "OK -> $OUT + assets/chapters.json"
