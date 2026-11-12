# Mode slides (archivé)

Le mode `slides` n'est plus utilisé. Il est conservé ici, à part du SKILL principal, au cas où.

## Ce que c'était

Un script monté en **présentation** (slides, une étape = un fragment), puis un locuteur qui s'enregistre en la commentant pas à
pas. La composition HyperFrames suivait le storyboard **avant** la prise ; après la prise, le transcript mesuré recalait les temps.
C'est l'inverse de l'ordre actuel (la voix et le transcript d'abord, le storyboard ensuite : `references/preparation.md`).

## Ce qui est archivé

| Fichier | Rôle |
|---|---|
| `mode-slides.md` | l'ancien sous-skill du mode |
| `studio-slides.md` | le format des slides, les commandes, les deux previews, le serveur d'enregistrement |
| `advanced-slides-subset.md` | le sous-ensemble Advanced Slides supporté par `build_studio_slides.py` |
| `scripts/build_studio_slides.py`, `scripts/build_studio_anim.py` | les deux builders du studio pas à pas |
| `scripts/studio_server.py` | le serveur d'enregistrement |

## Ce qui reste dans le SKILL principal

- `scripts/build.py --mode slides` accepte toujours cette valeur ; `**Mode** : slides` se lit toujours.
- `scripts/check-steps.py` compare toujours un deck (`--slides`) et un `studio.html` (`--studio`) quand ils existent.
- `data/scenes.json` et `data/figures.json` sont toujours écrits par `build.py` (les builders du studio les lisent).
- `scripts/render_primitive.py` est toujours importé par `build_studio_anim.py` : c'est pourquoi les scripts archivés se copient dans le
  `scripts/` du projet, à côté de lui.

## Réutiliser

Copier les trois scripts dans le projet (`cp $SKILL_DIR/archive/slides/scripts/*.py scripts/`) puis suivre `studio-slides.md`. Rien ici
n'est maintenu ni testé : les nouvelles fonctions (préparation, schémas Excalidraw, musique, sous-titres) ne s'y appliquent pas.
