# Conventions post-hoc vidéo (mode webcam, skill `hyperframe-joriel`)

Source = **enregistrement préalable** (1..n `.mkv` qui se succèdent, sans visuels).
But = **plaquer le scénario HyperFrames langage Joriel sur l'audio**,
en alternant hyperframe / caméra du locuteur (décision automatique de la skill).
Le langage visuel (`visual-language-joriel.md`) et les règles scénario
(`scenario-studio-conventions.md`) s'appliquent **sans changement** :
seule la source des timings change (transcription de l'audio final, pas prompteur).

## 0. Principes post-hoc

- **L'audio final est le maître.** Tous les `t` des CUES viennent de
  `transcript.json` mesuré sur l'audio **nettoyé**. On ne recale jamais
  la voix sur les visuels, c'est l'inverse.
- **Nettoyage autorisé** (choix verrouillé) : concat → nettoyage
  (silences, loudnorm) → **re-transcription obligatoire** de l'audio nettoyé.
  Ne jamais réutiliser les timings d'avant nettoyage. Chaque nettoyage écrit
  un **nouveau nom de fichier** (`voix-posthoc-v1.wav`, `-v2`, …) — jamais
  d'écrasement en place (cache rendu).
- **Caméra = décision automatique de la skill** (agent, pendant la scénarisation —
  jamais l'utilisateur) : le scénario déclare par étape `camera: off | pip | full`.
  Géométrie, flou et moment d'usage : references/webcam.md.
  Surcharge utilisateur optionnelle (`camera!:`), jamais exigée.
- **Zéro studio d'enregistrement** en mode webcam : pas de `studio-slides.html`,
  pas de prompteur, pas de POST /prise. Le livrable est direct `index.html` auto.

## 1. Entrée et concaténation

- Entrée : liste ordonnée des `.mkv` (tronçons/chapitres). Vérifier :
  `ffprobe` codec/résolution/fps/audio de chacun. Si hétérogènes → normaliser
  au concat (re-encode 1080p, 48 kHz stéréo), sinon concat lossless.
- Script : `scripts/concat-mkv.sh` (ffmpeg concat demuxer) → `assets/cam-original.mkv`
  (vidéo caméra conservée pour `pip`/`full`) + `assets/chapters.json`
  (bornes de chaque tronçon d'origine, pour la scénarisation).
- Extraire l'audio brut : `ffmpeg -i assets/cam-original.mkv -ar 48000 -ac 2 assets/voix-brut.wav`
  (nouveau nom à chaque passe, jamais d'écrasement).
- Fonds photo : si l'utilisateur fournit ses images, les réutiliser
  (normalisation `scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080`
  → `assets/bg/BG-0N.jpg`, originaux intacts). Écarter gros plans identifiables
  et textes trop lisibles quand possible ; tout écart à la règle (visages,
  pancartes lisibles) est **signalé dans BUILD-REPORT.md** (choix utilisateur
  explicite, voile 62 % + zoom atténuent).

## 2. Nettoyage conjoint A/V (obligatoire, scripté)

1. `scripts/clean-posthoc.py assets/cam-original.mkv` : détecte les silences
   (`silencedetect noise=-35dB:d=0.6`), **cappe chaque silence à ~0,35 s**
   (0,175 s conservés tête + queue, le milieu est excisé — garde le rythme
   respiratoire au lieu de tout retirer) puis coupe **audio + vidéo aux mêmes
   bornes** (`trim`/`atrim` + `concat`, puis `loudnorm`). Sorties synchrones :
   `assets/cam-clean.mkv` + `assets/voix-posthoc-v1.wav` + `assets/clean-map.json`.
2. **Ne jamais couper l'audio seul** (désync labiale en `full`) : éprouvé,
   `aselect` ne coupe pas l'audio alors que `select` coupe la vidéo — d'où le
   `trim`/`atrim` conjoint, seule méthode fiable.
3. **Re-transcrire l'audio NETTOYÉ** (jamais le brut) :
   ```bash
   sound transcribe assets/voix-posthoc-v1.wav -F json -l fr -o /tmp/tr.json
   ```
   Construire `transcript.json` comme skill `hyperframe` §4 (`segments`
   mesurés + `words` interpolés, `source` = nom exact de l'audio nettoyé).
4. Hygiène transcription : **exclure les segments hallucinés** (ex. générique
   « Sous-titrage Société Radio-Canada », segments au-delà de la durée audio).
   Tout nouveau nettoyage (`-v2`, …) ⇒ re-transcription + rebuild CUES.

## 3. Scénarisation contrainte par l'audio

- Découper `transcript.json` en scènes `I1`, `S01`… puis étapes `SLIDE#k`
  (`#0` = entrée de scène, `#k` = apparitions suivantes). Contraintes :
  - 1 étape = 1 apparition = 1 affichage = 1 label GSAP (comme §2c).
  - ~1 visuel / 8–12 s, jamais le même visuel > ~12 s ; 1 seul élément
    nouveau par étape (langage §7) ; punchlines/chiffres mot pour mot en or.
  - Chaque étape a une durée réelle (`end - start` transcript) : si < 1,2 s,
    fusionner avec la suivante ; si > 12 s, subdiviser (même phrase, 2 apparitions).
  - **Listes et chaînes causales : 1 item / 1 maillon par étape** (jamais
    3–5 items affichés d'un coup). Subdiviser le span temporel parent en
    sous-étapes : chaque item s'affiche seul, en grand.
- **Timings en secondes absolues, jamais en indices de segments** : Groq
  re-segmente différemment à chaque passe — toute référence par n° de segment
  casse à la re-transcription. Chaque étape porte `t`/`end` absolus.
- Champs `data/steps.json` : comme conventions §2 (`id, scene, slide, frag,
  cue, appear, type, fond, figures, duration, punch`) **plus**
  `camera: off|pip|full` + `cam_src` (toujours `assets/cam-original.mkv`,
  `media_start` = temps caméra = temps audio si A/V synchrones, sinon décalage
  noté). Le choix du mode et le rythme sont dans references/webcam.md.
- `data/figures.json` : inchangé (registre unique, `ok`/`verify`, sources).
  `data/design.json` : inchangé (blocs §3 + gabarits §9 du langage).
- Contrôle : `python3 scripts/check-steps.py` vert (étapes ↔ labels), comme §2c.
  Le champ `camera` n'est pas contrôlé par ce script : le build doit l'émettre
  en CUES (voir §4).

## 4. Build index.html (natif HyperFrames — règles éprouvées)

- 1 timeline racine pausée `window.__timelines["<slug>"]`, labels `SLIDE#k` = `t`
  mesurés ; visuels = clips `data-start`/`data-duration` ; micro-anims = tweens
  positionnés ; médias possédés par le framework (`<audio>` voix + spans
  `<video>` caméra fusionnés par état + `<audio data-volume>` SFX).
- Transport = timeline (`tl.play()/pause()/time()`), jamais `play()/pause()/
  currentTime` sur les médias (erreur `imperative_media_control`). Mises à jour
  d'affichage via `tl.eventCallback("onUpdate")`, jamais `requestAnimationFrame`.
- Visibilité des steps : **pilotée en JS (classe `.on`, 1 seule affichée)**,
  pas par le runtime (il ne révèle que les clips racine — les steps imbriqués
  resteraient invisibles ou fantômes). **Pas de `data-start` sur les steps**
  imbriqués (conflit runtime ↔ JS). Compositions : wrapper avec
  `data-composition-id` + `data-width`/`data-height` + `data-duration`,
  script gardé (`if(window.gsap)`, chemins relatifs racine — sinon l'export
  échoue « zero duration » : `ReferenceError` gsap → `__timelines` vide).
- **Sélecteurs GSAP : scorer chaque membre** (`A X,B X`, jamais `S X` avec
  `S` = liste). Un sélecteur nu applique le tween (ex. `rotate:-8` du stamp)
  à **tout le step** — tilt global constaté.
- Compteurs : `onUpdate` ré-émet **préfixe + valeur groupée + suffixe**
  (sinon `+24 %` s'affiche `24`). Grands nombres (≥ 5 chiffres) en taille
  réduite. Versus : `min-width:0` + padding sur les colonnes.
- Caméra : spans fusionnés par état, fondus + zoom d'apparition
  (`fromTo` scale .85→1 + opacity 0,5 s ; jamais de cut sec).
  - `pip` et `full` : géométrie dans references/webcam.md.
    Le cadre est un `div.cam-frame`, pas la balise vidéo. `tl.set` sur ce div.
  - Bandes noires cuites dans la source (pillarbox) : rognées côté CSS
    (`object-view-box:inset(0 8% 0 8%)`, cadre round intact, crop assumé),
    pas de re-encode.
  - `data-media-start` = `data-start` (même timeline coupée ensemble).
    Miroir déjà baked dans le mkv — ne pas re-miroir. SFX 0.10–0.16,
  1 max/étape, `M` + `?mute=1`.
- Vérifier : `npm run check` (0 erreur ; recouvre `check-steps.py` mode webcam
  via l'assert du build : labels uniques, ordre, `t` croissants),
  `npx hyperframes preview --background`, snapshots (voir §6),
  `render` sur feu vert uniquement.

## 5. Livrables mode webcam

- `assets/cam-original.mkv`, `assets/voix-posthoc-vN.wav`,
  `transcript.json`, `assets/chapters.json`,
  `data/steps.json` (+`camera`) / `figures.json` / `design.json`,
  `index.html` + `compositions/`, `scripts/concat-mkv.sh` + `build.py` adapté,
  `README.md` + `BUILD-REPORT.md` (chaîne nettoyage, mapping étape ↔ t ↔ camera).
- Interdit : timings pré-nettoyage, chiffres sans source, 2 accents concurrents,
  style hors tokens, mp4 sans feu vert.

## 6. Validation sans rendu (préviews + corrections)

- Servir : `npx hyperframes preview --background` (URL localhost à donner).
  Ne jamais rendre de MP4 pour « vérifier » — snapshots + preview suffisent.
- Snapshots : `npx hyperframes snapshot --at=t1,t2 --no-end` (+ `--zoom`
  sélecteur si besoin), planche `contact-sheet.jpg` = preuve visuelle par
  étape-clé (compteurs, punchlines, gabarits, bascules caméra).
- Pas de variante courte en changeant TOTAL seul : la durée vient des tweens
  positionnés, pas de la constante — un MP4 « test » ainsi bricolé n'affiche
  que l'écran FIN. Pour un test render, tronquer les tweens eux-mêmes.
- **Numérotation discrète obligatoire** (corrections par ID) : `.stepid`
  permanent (`ID · n/N`, ex. `S05.2#1 · 39/67`), `?draft=1` = pastilles
  « À VÉRIFIER », `?debug=1` = + `t`, caméra, opération. Contrôles :
  lecture/pause (Espace), pas-à-pas (←/→), seek au clic.
- Pièges vus : cache navigateur (forcer Ctrl+Maj+R après rebuild) ;
  compteur filmé en pleine animation = valeur intermédiaire (normal).

## 7. Retouches manuelles (2 voies, jamais en alternance aveugle)

- **Studio visuel** (URL preview = éditeur) : clic texte sur canvas, trim
  timeline — sauvegarde dans le projet. **Un rebuild par scripts écrase
  les retouches Studio** : choisir une voie par phase et l'annoncer.
- **Fichiers** : `data/design.json` (contenu écran), `data/steps.json`
  (`t`, `camera`), `data/figures.json` (chiffres). Supprimer une étape =
  la retirer des deux JSON + `python3 fourni par le projet (gabarit non inclus)`. Régénération
  complète : SPEC de `fourni par le projet (gabarit non inclus)` (source de vérité) →
  `make-scenario.py` → `build.py`. Ne pas toucher aux `data-hf-id`
  (ajoutés par le Studio).

## 8. Coupe tardive (doublon/raté découvert après build)

- Pas besoin de tout refaire : couper [a, b] sur audio+vidéo **ensemble**
  (un seul ffmpeg depuis le master nettoyé, backups `*-full.*`), re-transcrire,
  remapper le SPEC (trivial si timings absolus, §3), rebuild. Wording et
  designs conservés.
