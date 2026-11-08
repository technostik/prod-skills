# Mode auto

Sous-skill de `hyperframe-joriel`. Lire d'abord `SKILL.md` (socle commun : vocabulaire, principes, étapes communes, règles de rendu, assets, commande de build). Ce fichier ne contient que ce qui est propre au mode auto.

## Quand

Rien n'est enregistré. Le TTS lira le script (le scénario oralisé). Le script est le transcript. La composition est finie avant toute voix.

## Étapes

1. Écrire `SCENARIO.md`, puis le transformer en `assets/storyboard.md` (format estimé, durées approximatives). En-tête : `**Mode** : auto`. Résoudre les assets nommés (SKILL.md § Assets).
2. Vocaliser le script avec le TTS fast-market (`npx hyperframes tts`, Kokoro — skill `media-use`), puis transcrire avec Whisper fast-market (`video transcribe … -F json -l fr -o transcript.json`) pour obtenir `transcript.json`.
3. `python3 scripts/build.py --transcript transcript.json` : les `cue` sont recalés sur la voix, les lignes du storyboard ne changent pas.
4. `python3 scripts/check-steps.py`, `npm run check` vert, preview, mp4 sur feu vert uniquement.

## Ce qui est propre à ce mode

- Pas de caméra : aucune étape ne porte `camera`, et `build.py` n'émet ni `cam-frame` ni vidéo. Le fond est l'image `BG-xx` de la scène.
- Sans transcript, `build.py` utilise les durées estimées du storyboard (utile pour une première preview sans voix).
- Écart script / voix : nul (le script *est* la voix). Un `cue` est le mot probable de la voix.

## Contexte LLM (scénario → storyboard)

Les fichiers communs listés dans `SKILL.md` § Contexte LLM suffisent. Rien de plus pour ce mode.
