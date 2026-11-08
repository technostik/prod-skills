# Mode slides

Sous-skill de `hyperframe-joriel`. Lire d'abord `SKILL.md` (socle commun). Ce fichier ne contient que ce qui est propre au mode slides.

## Quand

Le script est monté en présentation ; le locuteur s'enregistre en la commentant, pas à pas. L'écart entre le script et la prise peut être important : après la prise, le transcript mesuré fait foi pour les temps.

## Étapes

1. Écrire le storyboard (`**Mode** : slides`), puis les slides aux **mêmes identifiants** (`SCÈNE.N`, étapes `SLIDE#k`). Format du deck (un `id:` par slide, un `fragment` = une étape `#k`, `note:` pour le locuteur) : `references/studio-slides.md`, § « Format des slides ».
2. La composition suit le storyboard, **avant** la prise : `python3 scripts/build.py`.
3. Le studio pas à pas garde ses deux builders (`scripts/build_studio_anim.py`, `scripts/build_studio_slides.py`) : ils lisent `data/scenes.json` et `data/figures.json` produits par `build.py`. Commandes à copier, deux previews (deck, composition), serveur d'enregistrement, suites de prise : `references/studio-slides.md`.
4. Après la prise, transcrire (`video transcribe … -F json -l fr -o transcript.json`), puis `python3 scripts/build.py --transcript transcript.json` : les temps suivent la prise.
5. `python3 scripts/check-steps.py`, `npm run check` vert, preview, mp4 sur feu vert uniquement.

## Ce qui est propre à ce mode

- Deux builds distincts (SKILL.md § Étapes communes) : la composition finale (`build.py`) et le studio pas à pas (`studio.html`).
- Le rendu des primitives est partagé (`scripts/render_primitive.py`) : une primitive a le même balisage dans le studio et dans la composition finale.
- Les `notes:` du storyboard sont visibles du locuteur seul.
- Pas de caméra dans la composition : la prise est la vidéo studio.

## Contexte LLM (scénario → storyboard)

Fichiers communs (`SKILL.md` § Contexte LLM), plus `references/studio-slides.md` et `references/scenario-studio-conventions.md` (écran, sons, correspondance des étapes).
