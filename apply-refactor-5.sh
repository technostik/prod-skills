#!/usr/bin/env bash
# Applique les patchs refactor-5-*.patch un par un (un commit chacun).
# S'arrête au premier échec ; relançable : un patch déjà appliqué est sauté.
# Usage : depuis la racine du dépôt, sur la branche refactor/cleanup :  bash apply-refactor-5.sh [dossier-des-patchs]
set -u
DIR="${1:-.}"
for p in "$DIR"/refactor-5-*.patch; do
  n=$(basename "$p" .patch)
  if git apply --reverse --check "$p" 2>/dev/null; then echo "déjà appliqué : $n"; continue; fi
  if ! git apply --check "$p"; then echo "ÉCHEC sur $n : rien n'a été modifié par ce patch. Corrige ou envoie-moi l'erreur." >&2; exit 1; fi
  git apply "$p" && git add -A && git commit -q -m "1.11.0 : $n" && echo "appliqué    : $n"
done
echo "terminé"
