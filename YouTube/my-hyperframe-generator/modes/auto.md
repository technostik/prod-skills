# Mode auto

Sous-skill de `hyperframe-joriel`. Lire d'abord `SKILL.md` (socle commun : vocabulaire, principes, étapes communes, règles de rendu, assets, commande de build). Ce fichier ne contient que ce qui est propre au mode auto.

## Quand

Rien n'est enregistré. Le TTS lira le script (le scénario oralisé). Le script est le transcript. La voix existe **avant** le storyboard : elle est produite dans la préparation, et le storyboard se pose sur son transcript mesuré.

## Étapes

1. **Préparation** (`references/preparation.md`) : `python3 scripts/prepare.py init --mode auto`, puis dans l'ordre :
   - `SCENARIO.md` (un titre `##` par chapitre) ;
   - vocaliser le script avec le TTS fast-market (`npx hyperframes tts`, Kokoro, skill `media-use`) → `assets/voix.wav` ;
   - transcrire : `python3 scripts/transcript-export.py --from-video assets/voix.wav` → `assets/transcript.json` (avec timecodes) **et** `assets/transcript.txt` (sans) ;
   - les fonds, références, chiffres, schémas (`assets/assets.md`, `refs.md`, `figures.md`, `assets/schemas/`) ;
   - `python3 scripts/prepare.py chapters`, puis `python3 scripts/prepare.py check` jusqu'à `ready`.
2. **Storyboard** sur le transcript mesuré (`assets/storyboard.md`, en-tête `**Mode** : auto`, format minuté).
3. `python3 scripts/build.py --transcript assets/transcript.json --audio assets/voix.wav` : les `cue` sont recalés sur la voix, les lignes du storyboard ne changent pas.
4. `python3 scripts/check-steps.py`, `npm run check` vert, preview, mp4 sur feu vert uniquement. Puis, s'il y en a, la musique (`references/music.md`) et les inserts (`references/inserts.md`).

## Ce qui est propre à ce mode

- Pas de caméra : aucune étape ne porte `camera`, et `build.py` n'émet ni `cam-frame` ni vidéo. Le fond est l'image `BG-xx` de la scène.
- Un storyboard écrit sans voix (durées estimées) reste lisible par `build.py` : c'est une première preview, pas l'ordre normal.
- Écart script / voix : nul (le script *est* la voix). Un `cue` est le mot probable de la voix.

## Contexte LLM (scénario → storyboard)

Les fichiers communs listés dans `SKILL.md` § Contexte LLM suffisent. Rien de plus pour ce mode.
