#!/usr/bin/env bash
# Génère des médias factices légers (ignorés par git) pour que `npm run check` passe sans les vrais assets.
# Remplace-les par tes fichiers : voir README.md, section « Assets ».
set -euo pipefail
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { echo "ffmpeg requis" >&2; exit 1; }
mkdir -p assets
# caméra : 640x360, 2 images/s, noir, 30 s, sans audio (la scène webcam dure 16 s)
[ -e assets/cam-clean.mkv ] || ffmpeg -nostdin -y -v error -f lavfi -i "color=c=black:s=640x360:r=2" -t 30 -c:v libx264 -preset ultrafast -crf 45 -pix_fmt yuv420p assets/cam-clean.mkv
# images : aplats sombres 1920x1080, un ton par fichier, aux noms exacts référencés
N=0
while read -r f; do
  [ -e "$f" ] && continue
  case "$f" in
    *BG-00*) c=0x10151c ;; *BG-01*) c=0x1b1426 ;; *image-plein-ecran*) c=0x1b2b4a ;; *) c=0x222831 ;;
  esac
  mkdir -p "$(dirname "$f")"
  ffmpeg -nostdin -y -v error -f lavfi -i "color=c=$c:s=1920x1080" -frames:v 1 "$f"
  N=$((N+1))
done < <(grep -rhoE 'assets/(images|bg|references)/[^" )]+' index.html compositions/*.html | sort -u)
echo "médias factices créés : $N image(s) ; caméra : $( [ -e assets/cam-clean.mkv ] && echo présente )"
