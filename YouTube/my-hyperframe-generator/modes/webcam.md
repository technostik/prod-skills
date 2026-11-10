# Mode webcam

Sous-skill de `hyperframe-joriel`. Lire d'abord `SKILL.md` (socle commun). Ce fichier ne contient que ce qui est propre au mode webcam. Si la vidéo doit rester plein écran sous les visuels, c'est le mode `incrustation` (`modes/incrustation.md`), pas celui-ci.

## Quand

La prise est déjà faite : le locuteur a lu le script (transcript chapitré), sans composition. Pas de prompteur. Écart script / prise : faible. La vidéo **alterne** avec les visuels : elle passe en coin, en mi-écran, disparaît ou, pour un screencast OBS, occupe tout l'écran. S'il manque l'ordre des tronçons `.mkv`, le demander.

## Étapes

1. Même init que `SKILL.md` § Projet, puis les commandes de `references/webcam.md` § Commandes : concaténer (`concat-mkv.sh`), nettoyer (`clean-posthoc.py`), **détecter les Cast** (`detect-cast.py`, si la prise contient des screencasts OBS), transcrire (`video transcribe`). Détail caméra, nettoyage et cues : `references/posthoc-video-conventions.md`.
2. `transcript.json` (segments + mots) puis le storyboard sur cet audio (`**Mode** : webcam`, format minuté). Pas de slides.
3. Build :

```bash
python3 scripts/build.py --transcript transcript.json \
  --camera assets/cam-clean.mkv --audio assets/voix.wav
```

4. `python3 scripts/check-steps.py`, `npm run check` vert, preview, snapshots, mp4 sur feu vert uniquement.

L'audio nettoyé fait foi : tout timing se remesure après le nettoyage. Pas de cut sec.

## Caméra : quatre valeurs

Trois états de base posés par les étapes (`off`, `pip`, `full`), plus `cast` : une séquence de screencast OBS (capture d'écran + webcam incrustée, filet vert `#00FF00` de 10 px en haut de l'image) affichée en vrai plein écran, filet retiré au rendu. Les intervalles Cast sont **détectés** (`scripts/detect-cast.py` → `assets/cast-segments.json`, après nettoyage) ; `camera: cast` dans le storyboard n'est qu'une annotation et ne change jamais l'état de base. Rythme : un état dure au moins 2,5 s ; revoir le locuteur (`pip` ou `full`) au moins toutes les ~20 s. Détails (CSS, `applyCam`, crop Cast, priorités, règles de cadre) : `references/webcam.md`.

La caméra est intégrée à chaque composition (`cam-frame` + `<video data-media-start>`, avec un wrapper `cam-content` quand il y a des Cast). Le nettoyage décale les timecodes : relancer `detect-cast.py` après chaque nettoyage. Sans `cast-segments.json`, le rendu est celui des trois états.

## Contexte LLM (scénario → storyboard)

Fichiers communs (`SKILL.md` § Contexte LLM), plus : `references/posthoc-video-conventions.md`, `references/webcam.md`, et, s'ils existent, `assets/cast-segments.json` et `transcript.json`. `prepare-webcam-context.sh` les rassemble dans un dossier (option `--project`).

## Schémas animés

`kind: schema` (voir `references/schemas-animes.md`) est un visuel plein cadre comme les autres : choisir `camera: off` ou `pip` pendant le schéma (`full` recouvre son centre, le build avertit). Les étapes consécutives d'un schéma sont un seul clip ; la caméra de chaque étape y est appliquée comme ailleurs.
