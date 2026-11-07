---
name: hyperframe-joriel
description: Build a Joriel-styled HyperFrames video in one of three modes — auto (the script is the transcript, vocalized with TTS), slides (composition from the script, then a live take that may diverge), or webcam (a take read from the script, then the composition from the measured transcript). The scenario is written first, then turned into a structured storyboard, then built by scripts/build.py. The worked chapter is examples/demo. Use when the user asks for hyperframe-joriel.
argument-hint: "<script.md | video.mkv>"
author: joriel
category: Video Creation
version: 1.14.0
---

# Hyperframe-joriel

Trois modes, un seul langage visuel. Ne jamais mélanger deux modes dans le même projet.
On part toujours d'un script. Le transcript est ce qui est dit. Le mp4 YouTube sort de trois étapes : le scénario (texte libre), le storyboard (mise en scène structurée), puis la composition (`build.py`).

**Routeur**

- Rien n'est enregistré, le TTS lira le script → **auto**. Script = transcript.
- Le script est monté en présentation, le locuteur s'enregistre en commentant → **slides**. L'écart entre le script et la prise peut être important.
- 1..n `.mkv` déjà tournés en lisant le script, sans composition → **webcam**. L'écart est faible. S'il manque l'ordre des tronçons, le demander.

S'il manque le script : le demander, ou l'obtenir via `hyperframe-scenario`. Un scénario, un storyboard ou des slides déjà fournis ne se réécrivent pas : on vérifie seulement que les identifiants correspondent. Sinon, cette skill les écrit avant la composition.

## Vocabulaire

- **Studio** : montage vidéo HyperFrames. **Slides** (le produit) : pas à pas avec enregistrement. Le mode **auto** et le mode **webcam** finissent en studio. Le mode **slides** enregistre au pas à pas.
- **Scénario** (`SCENARIO.md`) : le texte libre de départ, l'histoire et l'argumentaire. Il n'est pas formaté : c'est l'amont de toutes les étapes.
- **Storyboard** (`assets/storyboard.md`) : la mise en scène structurée du scénario, produite par le LLM. Il décrit l'écran, pas ce qui est dit. Chaque passage reçoit une primitive du langage visuel. C'est la seule entrée de `scripts/build.py`.
- **Primitives** : le vocabulaire visuel figé, identique d'une vidéo à l'autre (`references/visual-language-joriel.md`, `references/primitives-joriel.md`). Le LLM choisit la primitive ; le code ne choisit jamais à sa place.
- **Script** : le texte de départ, dans les trois modes.
- **Transcript** : ce qui est dit. Auto : le script, lu par le TTS. Slides : la prise, qui peut s'écarter beaucoup du script. Webcam : la lecture, écart faible. Après une prise, le transcript mesuré porte les temps.
- **Notes** : le guide pour commenter. Visibles du locuteur seul (`notes:` dans le storyboard).
- **Composition** : le document HTML animé produit par `build.py`. Une scène par unité du storyboard. Le chapitre de référence est `examples/demo/`.
- **Preview** : le HTML affiché avant le mp4.

## Principes

La composition illustre, le transcript explique. L'un renforce l'autre. La composition ne répète pas le transcript. Elle reste simple, claire, directe, et varie assez souvent pour tenir l'attention.

- Les clips illustrent le storyboard. Un concept passe par un SVG (`thesvg`, en local, sans altération), un graphique, ou des mots.
- Les primitives visuelles sont animées dynamiquement : compteurs (défilement rapide), pulse des flèches (gauche puis droite), versus (gauche diminue, droite s'agrandit), barré (trait progressif). Voir `references/primitives-joriel.md` pour les patterns GSAP.
- Dans un clip, et d'un clip à l'autre, relier les concepts. Quand on illustre une phrase ou un paragraphe, garder le concept d'un clip au suivant tant que c'est pertinent.
- Entre deux phrases ou deux paragraphes, changer de perspective : vidéo d'illustration, image zoomée lentement, webcam en mi-écran (fond figé et flouté), ou incrustation. Le plein écran est évité (résolution).
- S'il existe une source (tweet, page HTML), elle prime. La découpe locale est dans `references/embed-tweets-video.md` (§8 pour les pages web : screenshot si accessible, card stylisée si paywallée/bloquée).
- Une thématique, une ambiance ou une émotion : image ou vidéo de fond. Rien d'identifiable, pas de logo, pas de texte lisible dans le fond, rien chargé du réseau au rendu.
- S'il existe une vidéo du locuteur : incrustation en coin, mi-écran, ou rien.

Visuel, identique d'une vidéo à l'autre : fond noir, typographie la plus grande possible, éléments simples (flèche, liste, tableau, graphique, deux colonnes, symétrie), mouvement simple (translation, rotation, zoom) et changement de couleur (griser pour mettre en retrait).

Les valeurs, les blocs et les gabarits sont dans `references/visual-language-joriel.md`. Les appliquer, sans style improvisé. Le fond par défaut est `BG-00` ; le noir pur est réservé aux punchlines. Écran, caméra, sons, correspondance des étapes : `references/scenario-studio-conventions.md`.

## Prérequis

Variables d'environnement (valeurs par défaut entre parenthèses). Aucun chemin n'est écrit en dur ailleurs dans ce dépôt.

| Variable | Rôle | Défaut |
|---|---|---|
| `SKILL_DIR` | dossier de cette skill | `~/.agents/skills/my-hyperframe-generator` |
| `HF_WORKDIR` | dossier des projets HyperFrames | `~/Code/hyperframes` |
| `FASTMARKET_DIR` | dépôt fast-market (CLI `image`, `sound`) | `~/Code/fast-market` |
| `HF_VIDEOS_DIR` | sortie des prises studio | `~/Vidéos` |
| `HF_OVERLAYS_DIR` | overlays lus par le studio | `$HF_VIDEOS_DIR/OBS/assets` |

Dépendances : Node ≥ 22, `hyperframes@0.9.15`, FFmpeg, Python 3, Chrome ou Edge (prise studio), `yt-dlp` (inserts seulement). Skills compagnes : `thesvg`, `media-use`, `hyperframes`, `hyperframe-scenario` (optionnelle), `report` (diagnostic). CLI fast-market : `image`, `sound`.

## Projet

```bash
cd "$HF_WORKDIR"
npx --yes hyperframes@0.9.15 init <slug>
cd <slug>
```

`assets/gsap.min.js` doit être là (template d'init, ou copie d'un projet existant). Jamais de CDN au rendu.

## Étapes communes (ordre canonique)

Dans les trois modes, on suit le même ordre :

1. **Scénario** — `SCENARIO.md` : le texte libre, l'histoire à raconter (amont, déjà à disposition).
2. **Storyboard** — le LLM transforme le scénario en `assets/storyboard.md` : scènes, étapes, primitives, registres de chiffres et de références. C'est lui qui décide « ce passage devient un versus » ; le code n'invente rien. Format : `references/storyboard-format.md` ; prompt : `references/scenario-to-storyboard-prompt.md`.
3. **Collecte des assets** — Pexels (image/vidéo 1920×1080), `thesvg` (SVG local sans altération, logos), recherche web, génération via fast-market `image`, embeds YouTube/tweet (voir section Assets). Résoudre les fonds, images et logos nommés par le storyboard.
4. **Voix et transcript** — selon le mode : TTS+STT (auto), prise (slides), concat+nettoyage+STT (webcam) → `transcript.json`. Facultatif : sans transcript, `build.py` utilise les durées estimées du storyboard.
5. **Build** — `python3 scripts/build.py` lit le storyboard, recale les `cue` sur le transcript s'il existe, et écrit `data/*.json`, `index.html` et `compositions/`. Le storyboard n'est pas réécrit.
6. **Contrôle et preview** — `python3 scripts/check-steps.py`, `npx hyperframes check`, preview. Le mp4 seulement sur feu vert.
7. **Post-rendu** — si `assets/inserts.json` existe, `scripts/post-render.py` assemble `renders/final.mp4`. Voir `references/inserts.md`.

Deux builds distincts :

| Build | Quand | Script | Sortie |
|---|---|---|---|
| **Composition finale** | toujours | `scripts/build.py` | `index.html` + `compositions/` |
| **Studio pas à pas** | mode slides | `scripts/build_studio_anim.py`, `build_studio_slides.py` | `studio.html` (vue d'enregistrement) |

`build.py` produit aussi `data/scenes.json` et `data/figures.json`. Le rendu des primitives est partagé : `scripts/render_primitive.py` est importé par `build.py` et par `build_studio_anim.py`, donc une primitive (versus, strike, count…) a le même balisage dans la composition finale et dans le studio.

## Storyboard

`assets/storyboard.md` est écrit par le LLM avant toute composition. Format complet et lisible par le code : `references/storyboard-format.md`. Prompt de transformation : `references/scenario-to-storyboard-prompt.md`.

- Le LLM reçoit `SCENARIO.md`, ce `SKILL.md`, `references/visual-language-joriel.md`, `references/primitives-joriel.md`, `references/storyboard-format.md` et `examples/demo/`.
- Il rend **uniquement** le markdown du storyboard. Une étape = une primitive (`kind`) = une apparition = un label GSAP.
- Les chiffres viennent du registre §1 (`Fxx`), les sources du registre §1b (`Rxx`). Jamais de chiffre ou d'URL en dur dans une étape.
- Le registre est la seule source : `build.py` en extrait `data/figures.json` et `data/refs.json`.

Format court :

```markdown
## 4. Scènes

### I1 — Le chiffre choc

- section: bilan · type: numbers · fond: BG-01 · durée: 40
- figures: F01

#### Étapes

- `I1.1#0` · cue « interpellations » → **compteur +5 000**
  - kind: count
  - figure: F01
  - prefix: "+ "
  - notes: marquer le chiffre, ton calme

- `I1.1#1` · cue « lycées » → **versus : 24 incendiés vs 3 700 total**
  - kind: versus
  - left: [{"kw": "24 incendiés", "cls": "rouge"}]
  - right: [{"kw": "3 700 total", "cls": "bleu"}]
  - recall: left
```

Identifiants, les mêmes partout :

| Notion | Forme | Exemple |
|---|---|---|
| Scène | `I1`, `S04` | `S04` |
| Slide | `SCÈNE.N` | `S04.3` |
| Étape | `SLIDE#k` | `S04.3#2` |

`#0` = la scène apparaît. `#1`, `#2`… = les fragments, dans l'ordre. Une étape = une apparition = un label GSAP. Une punchline est une scène à part, `#0` seul. L'ordre du storyboard est l'ordre de la timeline. Le `cue` est un mot probable de la voix, pas une réplique à lire.

Références `Rxx` : `Type` ∈ tweet · page · capture · video · image ; `Statut` ∈ ok · à capturer · bloquée (card). Une étape cite sa source avec `ref: Rxx`. Acquisition : `references/embed-tweets-video.md` §8. Un `Rxx` ne s'affiche jamais à l'écran (Règles absolues).

### Format minuté (mode webcam, et après mesure)

Le même fichier peut porter des temps absolus, ligne par ligne. `build.py` les respecte, et recale les lignes sans `t` sur le transcript.

```markdown
### I1 — Titre [BG-02]
- `I1.1#0` t=39.18 (3.6s) [off/count] 24 lycées
- `I1.1#1` t=42.76 (2.5s) [pip/enumerate] manque de profs
```

`off`, `pip`, `full` (états de base) et `cast` (annotation d'une séquence de screencast OBS) : section Webcam. Après une coupe, on décale les temps et on ne réécrit pas les lignes.

### Slides (mode slides seulement)

Format du deck (un `id:` par slide, un `fragment` = une étape `#k`, `note:` pour le locuteur) : `references/studio-slides.md`, § « Format des slides ». Les modes auto et webcam n'ont pas de slides.

## Règles de rendu de la composition (spectateur final)

> `python3 scripts/check-steps.py` est exécuté à chaque modification des étapes. `npm run check` (lent) est exécuté une fois avant toute demande de rendu mp4, et sur demande de l'utilisateur. Le mp4 n'est jamais rendu sans feu vert.

### Timing des sub-compositions (IMPORTANT)
- Dans un fichier de sub-composition (`compositions/iNN.html`), les `data-start` doivent être **relatifs** au début de cette sub-composition (t=0 = début de la scène). Le `data-start` absolu (depuis le début de l'audio) est celui de l'`index.html` qui monte la sub-composition via `data-composition-src` + `data-start`.
- Ne jamais laisser des timecodes absolus dans une sub-composition : cela crée un vide au début et décale tout le reste.

### Webcam

Trois états de base : `off`, `pip`, `full`, plus `cast` : une séquence de screencast OBS (capture d'écran + webcam incrustée, filet vert `#00FF00` de 10 px en haut de l'image) affichée en vrai plein écran, filet retiré au rendu. Les intervalles Cast sont **détectés** (`scripts/detect-cast.py` → `assets/cast-segments.json`, après nettoyage) ; `camera: cast` dans le storyboard n'est qu'une annotation et ne change jamais l'état de base. Rythme : un état dure au moins 2,5 s ; revoir le locuteur (`pip` ou `full`) au moins toutes les ~20 s. Détails (CSS, `applyCam`, crop Cast, priorités, règles de cadre) : `references/webcam.md`.

### Règles absolues (spectateur final)

La composition est vue par le spectateur, pas par l'auteur. Règles absolues :

- **Numérotation discrète obligatoire.** Chaque étape affiche son identifiant (`I0.1#0`) en bas à gauche, gris, classe `.slideno`. C’est le repère de debug. Il reste à l’écran, y compris au rendu.
- **Aucune autre référence interne** dans le contenu : pas de codes `F01`, `R01`, `?draft=1`, ni de pastilles « À VÉRIFIER » sauf décision explicite d'affichage éditorial. Les figures du registre servent à sourcer le contenu. On affiche le **texte du registre** (la valeur et sa définition) ou l'image-source, pas le code de figure.
- **Aucune instruction de mise en page** dans le HTML affiché : pas de « couleur bleu », « fond noir pur », « sub: … », « source prioritaire Rxx », « morph avec pair », « pastille draft ». Tout ce qui est dans le storyboard comme directive doit être **appliqué** dans le style/la mise en page, jamais rendu comme texte.
- **Pas de texte de storyboard brut** dans les compositions : le storyboard est la source de vérité, l'écran montre le résultat visuel final, pas la consigne.
- Les chiffres s'affichent avec leur valeur et leur unité (ex. « 722 manuscrits », « ≈ 3 h de calcul équivalent »), jamais avec leur code.
- Les sources s'affichent comme attribution lisible (ex. « OpenAI, 2026-10-06 »), jamais comme code `R04`.
- Les directives `verify`/`draft` se traduisent par le style (couleur or, pastille visuelle dédiée) ou restent invisibles ; jamais le mot « draft ».

## Assets

### Fonds
- Varier les images de fond entre chapitres au minimum. Le storyboard nomme les fonds et les visuels ; on les résout avant la composition.

### Sources

1. Un fichier déjà là (ce projet, ou un asset du même sujet) se réutilise.
2. Image ou vidéo : Pexels, 1920×1080, téléchargé dans `assets/`. Noter l'URL, l'id, l'auteur et la requête. Rien n'est chargé du réseau au rendu.
3. Un concept ou une idée (pas une photo) : skill `thesvg`, SVG local, sans altération. Les logos aussi.
4. Une ambiance abstraite sans plan Pexels utilisable : Flux.2 Klein 9B (fast-market `image`).
5. Une personnalité ou un sujet identifiable : recherche web, puis capture locale (screenshot si accessible, card stylisée si paywallé/bloqué) — voir `references/embed-tweets-video.md` §8.
6. Un extrait YouTube ou un tweet : embed local (voir `references/embed-tweets-video.md`). La source prime sur une image générique.

### Outils fast-market (`$FASTMARKET_DIR`)

- **Image** : `image generate '<prompt>' -e flux29bcloud -w 1920 -h 1080 --output-format JPEG -o assets/ -F json` (équivalent `-e flux2cloud --cf-model 9b`). Pas de 4B. La CLI écrit toujours `<engine>_0.jpeg` : le renommer tout de suite. Erreur 400 : retirer les termes menaçants et reformuler. Fond par défaut `BG-00`. Noir pur seulement pour une punchline. Voile 55–70 % et zoom lent 3–6 % sur une photo.
- **Audio (TTS)** : `npx hyperframes tts` (Kokoro) — utilisé en mode auto pour vocaliser le script. Voir skill `media-use`.
- **Audio (STT)** : transcription Whisper via l'utilitaire fast-market (`video transcribe … -F json -l fr -o …`) — utilisé en auto et en webcam pour produire `transcript.json`.

### Règles

- Rien n'est chargé du réseau au rendu.

## Composition

**Un seul builder :** `scripts/build.py`. Il lit `assets/storyboard.md` et écrit la composition complète. Aucun builder par projet.

```bash
python3 scripts/build.py \
  --root . \
  --storyboard assets/storyboard.md \
  [--transcript transcript.json] \
  [--audio assets/voix.wav] \
  [--camera assets/cam-clean.mkv] \
  [--cast-segments assets/cast-segments.json] \
  [--slug mon-film]
```

| Sortie | Contenu |
|---|---|
| `data/figures.json` | registre §1 (lu aussi par `build_studio_anim.py`) |
| `data/refs.json` | registre §1b |
| `data/steps.json` | une entrée par étape, temps absolus, caméra, `kind` |
| `data/design.json` | `kind` + paramètres, par étape |
| `data/camera.json` | timeline caméra effective (base ∪ Cast), **seulement si** `cast-segments.json` a des intervalles |
| `data/scenes.json` | scènes + beats, schéma attendu par `build_studio_anim.py` |
| `index.html` | composition racine : scènes, audio, registre de timeline |
| `compositions/iNN.html` | une sous-composition par scène |
| `assets/style-joriel.css` | écrit **seulement s'il est absent** (copie de la démo) |
| `assets/style-joriel-ext.css` | styles des primitives absentes de la démo (bars, seuil, compare3, caméra) |

Le temps vient de `transcript.json` s'il est fourni : chaque `cue` est recalé sur les mots de la voix. Sinon, les durées estimées du storyboard font foi. L'audio (`assets/voix.wav`, sinon le plus grand `assets/voix-posthoc-vN.wav`, N comparé numériquement), la caméra (`assets/cam-clean.mkv`) et `assets/cast-segments.json` sont détectés automatiquement s'ils existent. Sans `cast-segments.json`, le rendu webcam est exactement celui d'avant (trois états).

**Nomenclature :** toujours deux chiffres avec zéro initial pour le numéro de scène — `i00.html`, `i01.html`, …, `i09.html`, `i10.html`. Jamais `i3.html`. Les identifiants (`data-composition-id`, `window.__timelines`, cadre caméra) suivent le même nommage (`i03`, etc.).

Le HTML produit reprend le balisage et les classes de `examples/demo/` : le catalogue des primitives (10 scènes, `i00` à `i09` ; `i09` : webcam avec Cast), une primitive par étape. Les ids du storyboard sont les labels GSAP. Contrôle : `python3 scripts/check-steps.py`, puis `npm run check`.

L'exemple se vérifie seul :

```bash
cd $SKILL_DIR/examples/demo && npm run check
```

Avertissements connus de `hyperframes check` et leurs corrections : `references/hyperframes-check.md`.

## Contexte LLM

Fichiers à donner tels quels.

- **Scénario → storyboard**
  - Source : `SCENARIO.md` (texte libre, l'histoire et l'argumentaire)
  - `SKILL.md`
  - `references/visual-language-joriel.md`
  - `references/primitives-joriel.md`
  - `references/storyboard-format.md` (format lisible par `build.py`, catalogue des `kind`)
  - `references/scenario-to-storyboard-prompt.md` (prompt de transformation)
  - `examples/storyboard.example.md` (exemple complet et parsable)
  - Selon le mode :
    - Webcam : `references/posthoc-video-conventions.md`
    - Conventions détaillées : `references/scenario-studio-conventions.md`

- **Storyboard → contrôle**
  - `assets/storyboard.md` (la sortie du LLM)
  - `scripts/build.py` produit la composition ; on ne réécrit pas le storyboard à la main après le build.
  - Selon les besoins :
    - Extraits de tweets ou vidéos externes : `references/embed-tweets-video.md`

## Mode auto

Pas de prise, pas de slides. Le TTS lit le script (le scénario oralisé). Le script = le transcript.

1. Écrire `SCENARIO.md`, puis le transformer en `assets/storyboard.md` (format estimé, durées approximatives). Résoudre les assets nommés.
2. Vocaliser le script avec le TTS fast-market (`npx hyperframes tts`, Kokoro — skill `media-use`), puis transcrire avec Whisper fast-market pour obtenir `transcript.json`.
3. `python3 scripts/build.py --transcript transcript.json` : les `cue` sont recalés sur la voix, les lignes du storyboard ne changent pas.
4. `python3 scripts/check-steps.py`, `npm run check` vert, preview, mp4 sur feu vert uniquement.

## Mode slides

Entrée : le script. Écrire le storyboard, puis les slides aux mêmes identifiants. La composition suit le storyboard, avant la prise ; après la prise, le transcript peut s'écarter du script et les temps le suivent : `python3 scripts/build.py --transcript transcript.json`.

Le studio pas à pas garde ses deux builders (`build_studio_anim.py`, `build_studio_slides.py`) : ils lisent `data/scenes.json` et `data/figures.json` produits par `build.py`.

Commandes à copier, deux previews (deck, composition), serveur d'enregistrement, suites de prise : `references/studio-slides.md`.

## Mode webcam

La prise est déjà faite : le locuteur a lu le script (transcript chapitré), sans composition. Pas de prompteur. Les vidéos par chapitre sont concaténées, puis transcrites pour obtenir `transcript.json`. Le storyboard et la composition partent du transcript mesuré. Détail caméra, nettoyage et cues : `references/posthoc-video-conventions.md`.

Même init que Projet, puis les commandes de `references/webcam.md` (§ Commandes) : concaténer, nettoyer, **détecter les Cast** (si la prise contient des screencasts OBS), transcrire.

Puis `transcript.json` (segments + mots) et le storyboard sur cet audio. Pas de slides.

```bash
python3 scripts/build.py --transcript transcript.json \
  --camera assets/cam-clean.mkv --audio assets/voix.wav
```

La caméra est intégrée à chaque composition (`cam-frame` + `<video data-media-start>`, avec un wrapper `cam-content` quand il y a des Cast), avec les états `off` / `pip` / `full` et, pendant les intervalles détectés, `cast`. Le nettoyage décale les timecodes : relancer `detect-cast.py` après chaque nettoyage. `npm run check` vert, preview, snapshots, mp4 sur feu vert uniquement.

L'audio nettoyé fait foi : tout timing se remesure après le nettoyage. Pas de cut sec.

## Ce que ce dépôt fournit

- `scripts/build.py` : builder générique des trois modes, source unique `assets/storyboard.md`. Il ne remplace pas les builders du studio (mode slides), qui gardent la vue d'enregistrement pas à pas.
- `scripts/render_primitive.py` : module commun de rendu des primitives, importé par `build.py` et `build_studio_anim.py`. Une primitive n'est écrite qu'une fois.
- Les primitives sont dans `references/primitives-joriel.md` et rendues par `render_primitive.py`. `seuil`, `bars`, `compare3`, `brand` et la caméra sont couverts ; leurs styles manquants sont écrits dans `assets/style-joriel-ext.css` au build.
- Un `kind` absent du catalogue ne s'invente pas : on l'ajoute d'abord à `visual-language-joriel.md`, `primitives-joriel.md`, `examples/demo/` et `render_primitive.py`, puis on l'utilise.

Limites assumées :

- La collecte des assets (Pexels, `thesvg`, captures, embeds) reste manuelle ou via les outils cités en § Assets.
- Le TTS et le STT sont des commandes externes (`npx hyperframes tts`, fast-market `video transcribe`) : le dépôt ne les réimplémente pas.
- `examples/demo/` reste le chapitre de référence ; ses médias factices sont générés par le script de placeholders du dépôt source.
