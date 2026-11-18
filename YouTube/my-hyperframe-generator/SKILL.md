---
name: hyperframe-joriel
description: Build a Joriel-styled HyperFrames video in one of three modes — auto (the script is the transcript, vocalized with TTS), webcam (a take read from the script; the video alternates with the visuals) or incrustation (same take, but the video stays full screen under the visuals, which are overlaid in one of nine screen zones). The order is fixed: the scenario, then a preparation stage (voice and transcript first, then backgrounds, references, chapters, screencasts, schemas), then a structured storyboard written on the measured transcript, then scripts/build.py. Includes animated Excalidraw schemas, punctual orchestral music mixed under the voice, and full-screen backgrounds with full-image references. The worked chapter is examples/demo. Output format 16:9 (default) or 9:16 (a vertical Short from one take, orthogonal to the mode). Use when the user asks for hyperframe-joriel.
argument-hint: "<script.md | video.mkv>"
author: joriel
category: Video Creation
version: 1.18.0
---

# Hyperframe-joriel

Trois modes, un seul langage visuel. **Un seul mode par projet** : ne jamais en mélanger deux.
On part toujours d'un script. Le transcript est ce qui est dit. Le mp4 YouTube sort de quatre étapes : le scénario (texte libre), la **préparation** (voix, transcript, assets : `references/preparation.md`), le storyboard (mise en scène structurée, écrite sur le transcript), puis la composition (`build.py`).

Cette skill est découpée en un **socle commun** (ce fichier) et **trois sous-skills**, une par mode, dans `modes/`. On choisit le mode ci-dessous, puis on lit **uniquement** le fichier de ce mode, en plus de ce socle.

## Routeur

| Situation | Mode | Sous-skill |
|---|---|---|
| Rien n'est enregistré, le TTS lira le script. Script = transcript. | **auto** | `modes/auto.md` |
| 1..n `.mkv` déjà tournés en lisant le script, sans composition. L'écart est faible. La vidéo **alterne** avec les visuels (coin, mi-écran, absente, ou plein écran pour un screencast). | **webcam** | `modes/webcam.md` |
| Les mêmes `.mkv`, mais la vidéo **reste plein écran** (webcam ou screencast OBS) et les visuels sont **posés par-dessus**. | **incrustation** | `modes/incrustation.md` |

**Format de sortie** (orthogonal au mode) : 16:9 par défaut, ou **9:16** pour un Short vertical (§ Format 9:16). Ce n'est pas un quatrième mode : les trois modes s'y appliquent.

Le choix entre **webcam** et **incrustation** est celui de l'utilisateur, pour toute la vidéo ; le LLM ne le déduit pas du contenu. S'il n'est pas dit, le demander. S'il manque l'ordre des tronçons `.mkv`, le demander aussi. Le mode s'écrit dans l'en-tête du storyboard : `**Mode** : auto | webcam | incrustation`. Le mode `slides` (le storyboard avant la prise) n'est plus utilisé : il est archivé dans `archive/slides/README.md`.

S'il manque le script : le demander, ou l'obtenir via `hyperframe-scenario`. Un scénario ou un storyboard déjà fournis ne se réécrivent pas : on vérifie seulement que les identifiants correspondent. Sinon, cette skill les écrit avant la composition.

## Vocabulaire

- **Studio** : montage vidéo HyperFrames.
- **Scénario** (`SCENARIO.md`) : le texte libre de départ, l'histoire et l'argumentaire. Il n'est pas formaté : c'est l'amont de toutes les étapes.
- **Storyboard** (`assets/storyboard.md`) : la mise en scène structurée du scénario, produite par le LLM. Il décrit l'écran, pas ce qui est dit. Chaque passage reçoit une primitive du langage visuel. C'est la seule entrée de `scripts/build.py`.
- **Primitives** : le vocabulaire visuel figé, identique d'une vidéo à l'autre (`references/visual-language-joriel.md`, `references/primitives-joriel.md`). Le LLM choisit la primitive ; le code ne choisit jamais à sa place.
- **Script** : le texte de départ, dans les trois modes.
- **Transcript** : ce qui est dit. Auto : le script, lu par le TTS. Webcam et incrustation : la lecture, écart faible. Après une prise, le transcript mesuré porte les temps.
- **Notes** : le guide pour commenter. Visibles du locuteur seul (`notes:` dans le storyboard).
- **Composition** : le document HTML animé produit par `build.py`. Une scène par unité du storyboard. Le chapitre de référence est `examples/demo/`.
- **Preview** : le HTML affiché avant le mp4.
- **Incrustation** : un visuel posé *sur* la vidéo plein écran, dans une zone de l'écran (mode `incrustation`). À ne pas confondre avec la webcam incrustée en bas à droite, le `pip` du mode webcam.

## Principes

La composition illustre, le transcript explique. L'un renforce l'autre. La composition ne répète pas le transcript. Elle reste simple, claire, directe, et varie assez souvent pour tenir l'attention.

- Les clips illustrent le storyboard. Un concept passe par un SVG (`thesvg`, en local, sans altération), un graphique, ou des mots.
- Les primitives visuelles sont animées dynamiquement : compteurs (défilement rapide), pulse des flèches (gauche puis droite), versus (gauche diminue, droite s'agrandit), barré (trait progressif). Voir `references/primitives-joriel.md` pour les patterns GSAP.
- Dans un clip, et d'un clip à l'autre, relier les concepts. Quand on illustre une phrase ou un paragraphe, garder le concept d'un clip au suivant tant que c'est pertinent.
- Entre deux phrases ou deux paragraphes, changer de perspective : vidéo d'illustration, image zoomée lentement, webcam en mi-écran (fond figé et flouté), ou webcam incrustée (`pip`). Le plein écran est évité (résolution), sauf pour un screencast OBS (`cast`).
- S'il existe une source (tweet, page HTML), elle prime. La découpe locale est dans `references/embed-tweets-video.md` (§8 pour les pages web : screenshot si accessible, card stylisée si paywallée/bloquée).
- Une thématique, une ambiance ou une émotion : image ou vidéo de fond. Rien d'identifiable, pas de logo, pas de texte lisible dans le fond, rien chargé du réseau au rendu.
- S'il existe une vidéo du locuteur (mode webcam) : webcam incrustée en coin, mi-écran, ou rien. En mode incrustation, la vidéo reste plein écran et ce sont les visuels qui se posent dessus.

Visuel, identique d'une vidéo à l'autre : fond noir, typographie la plus grande possible, éléments simples (flèche, liste, tableau, graphique, deux colonnes, symétrie), mouvement simple (translation, rotation, zoom) et changement de couleur (griser pour mettre en retrait).

Les valeurs, les blocs et les gabarits sont dans `references/visual-language-joriel.md`. Les appliquer, sans style improvisé. Le fond par défaut est `BG-00` ; le noir pur est réservé aux punchlines. Écran, caméra, sons, correspondance des étapes : `references/scenario-studio-conventions.md`.

## Prérequis

Variables d'environnement (valeurs par défaut entre parenthèses). Aucun chemin n'est écrit en dur ailleurs dans ce dépôt.

| Variable | Rôle | Défaut |
|---|---|---|
| `SKILL_DIR` | dossier de cette skill | `~/.agents/skills/my-hyperframe-generator` |
| `HF_WORKDIR` | dossier des projets HyperFrames | `~/Code/hyperframes` |
| `FASTMARKET_DIR` | dépôt fast-market (CLI `image`, `video`) | `~/Code/fast-market` |
| `HF_VIDEOS_DIR` | sortie des prises studio | `~/Vidéos` |
| `HF_OVERLAYS_DIR` | overlays lus par le studio | `$HF_VIDEOS_DIR/OBS/assets` |

Dépendances : Node ≥ 22, `hyperframes@0.9.15`, FFmpeg, Python 3, Chrome ou Edge (prise studio), `yt-dlp` (inserts seulement). Skills compagnes : `thesvg`, `media-use`, `hyperframes`, `hyperframe-scenario` (optionnelle), `report` (diagnostic). CLI fast-market : `image`, `video`.

## Format 9:16 (Short)

Un format de sortie, pas un mode : `**Format** : 1080×1920 @ 30 fps` dans l'en-tête du storyboard (ou `build.py --format 9:16`, `prepare.py init --format 9:16`). Les trois modes s'appliquent, avec le même storyboard et les mêmes primitives. Différences :

- **Une seule vidéo, un seul chapitre.** Pas de concaténation de tronçons. La prise par défaut est **la dernière vidéo de `$HF_VIDEOS_DIR`** (`~/Vidéos`, comme en 16:9) : `python3 scripts/short-take.py` (`--which` pour voir laquelle, ou un fichier en argument), puis `clean-posthoc.py`, `detect-cast.py`, `transcript-export.py` comme d'habitude. `prepare.py chapters` écrit alors un chapitre unique.
- **La webcam est déjà en 9:16** (sinon avertissement : rognée au centre). Caméra `pip` / `full` / `cast` et `incrustation` en 1080×1920 (`references/webcam.md`, `modes/incrustation.md`).
- **Pas de shorts de promotion** : la vidéo *est* le short (`## 6. Shorts` ignoré). Au plus 180 s (avertissement au-delà).
- Le CSS est dérivé du CSS 16:9 dans `assets/style-joriel-9x16.css` ; marges de sécurité (zones recouvertes par l'interface de YouTube Shorts) ; `versus` empilé ; les schémas (dessinés en 16:9) sont posés dans une bande centrale ; fonds en 1080×1920.
- **Début animé, rythme dense dans les 30 premières secondes** : un Short dont le début n'est pas animé n'est pas regardé. Première étape à `t=0`, la plus forte ; une étape toutes les 2 à 4 s ; primitives qui bougent et caméra alternée (`references/scenario-to-storyboard-prompt.md` règle 16). `build.py` avertit si rien n'apparaît avant 1 s ou si l'image reste plus de 4 s sans changer dans les 30 premières secondes.
- Pas d'inserts. Sortie : le mp4 vertical de `npx hyperframes render`, directement le short.

## Projet

```bash
cd "$HF_WORKDIR"
npx --yes hyperframes@0.9.15 init <slug>
cd <slug>
```

`assets/gsap.min.js` doit être là (template d'init, ou copie d'un projet existant). Jamais de CDN au rendu.

## Étapes communes (ordre canonique)

Dans les trois modes, on suit le même ordre. **La voix et le transcript passent avant le storyboard** : le storyboard se pose sur ce qui est réellement dit, avec ses temps.

1. **Scénario** — `SCENARIO.md` : le texte libre, l'histoire à raconter (amont, déjà à disposition). Un titre `##` par chapitre.
2. **Préparation** — tout ce qui est nécessaire pour écrire le storyboard (`references/preparation.md`), vérifié par `python3 scripts/prepare.py check` jusqu'à `ready` :
   - **la voix et le transcript** : auto, le scénario est vocalisé (TTS) puis transcrit ; webcam et incrustation, la prise que le locuteur dicte (concat, nettoyage). Le transcript est toujours produit **aux deux formats** : JSON avec timecodes et TXT sans timecode (`scripts/transcript-export.py`) ;
   - **les fonds d'écran** (`assets/assets.md`), plein écran ; **les références** et **les assets de référence** d'un auteur cité (`assets/refs.md`), en entier ; **les chiffres** sourcés (`assets/figures.md`) ;
   - **les chapitres** (`prepare.py chapters`), **les screencasts** repérés (`detect-cast.py`, webcam et incrustation), **les schémas** (`assets/schemas/*.excalidraw`, regardés et validés), les inserts.
3. **Storyboard** — le LLM transforme le scénario, le transcript et les assets préparés en `assets/storyboard.md` : scènes, étapes, primitives, registres de chiffres, de références, de schémas et de musiques, et **trois shorts de promotion** (`## 6. Shorts`, 3 minutes au plus chacun : `references/shorts.md`). C'est lui qui décide « ce passage devient un versus » ; le code n'invente rien. Format : `references/storyboard-format.md` ; prompt : `references/scenario-to-storyboard-prompt.md`.
4. **Build** — `python3 scripts/build.py` lit le storyboard, recale les `cue` sur le transcript, et écrit `data/*.json`, `index.html` et `compositions/`. Le storyboard n'est pas réécrit.
5. **Contrôle et preview** — `python3 scripts/check-steps.py`, `npx hyperframes check`, preview. Le mp4 seulement sur feu vert.
6. **Rendu et post-rendu** — la musique (`make-music.py`, `mix-music.py` : `references/music.md`), puis les inserts (`scripts/post-render.py` : `references/inserts.md`) qui assemblent `renders/final.mp4`, les sous-titres de publication (`transcript-export.py --publish final`), et l'extraction des shorts : `video short-extractor renders/final.mp4 --segments data/shorts_segments.json --layout fit-blur --output-dir shorts/` (`scripts/shorts-export.py` si des inserts ont décalé la timeline).

`build.py` produit aussi `data/scenes.json` et `data/figures.json` (schémas : `references/data-schemas.md`). Le rendu des primitives est dans `scripts/render_primitive.py`, importé par `build.py` : une primitive n'est écrite qu'une fois.

## Storyboard

`assets/storyboard.md` est écrit par le LLM avant toute composition. Format complet et lisible par le code : `references/storyboard-format.md`. Prompt de transformation : `references/scenario-to-storyboard-prompt.md`.

- Le LLM reçoit `SCENARIO.md`, le transcript et les livrables de la préparation (`references/preparation.md` § Ce que reçoit le LLM), ce `SKILL.md`, `references/visual-language-joriel.md`, `references/primitives-joriel.md`, `references/storyboard-format.md` et `examples/demo/`.
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

### Format minuté (modes webcam et incrustation, et après mesure)

Le même fichier peut porter des temps absolus, ligne par ligne. `build.py` les respecte, et recale les lignes sans `t` sur le transcript.

```markdown
### I1 — Titre [BG-02]
- `I1.1#0` t=39.18 (3.6s) [off/count] 24 lycées
- `I1.1#1` t=42.76 (2.5s) [pip/enumerate] manque de profs
```

Mode webcam : `off`, `pip`, `full` (états de base) et `cast` (annotation d'une séquence de screencast OBS), voir `modes/webcam.md`. Mode incrustation : la primitive seule (`[count]`) et `place:` facultatif, voir `modes/incrustation.md`. Après une coupe, on décale les temps et on ne réécrit pas les lignes.

## Règles de rendu de la composition (spectateur final)

> `python3 scripts/check-steps.py` est exécuté à chaque modification des étapes. `npm run check` (lent) est exécuté une fois avant toute demande de rendu mp4, et sur demande de l'utilisateur. Le mp4 n'est jamais rendu sans feu vert.

### Timing des sub-compositions (IMPORTANT)
- Dans un fichier de sub-composition (`compositions/iNN.html`), les `data-start` doivent être **relatifs** au début de cette sub-composition (t=0 = début de la scène). Le `data-start` absolu (depuis le début de l'audio) est celui de l'`index.html` qui monte la sub-composition via `data-composition-src` + `data-start`.
- Ne jamais laisser des timecodes absolus dans une sub-composition : cela crée un vide au début et décale tout le reste.

### Caméra

La caméra dépend du mode : états `off` / `pip` / `full` et `cast` (`modes/webcam.md`, `references/webcam.md`), ou vidéo plein écran sous les visuels (`modes/incrustation.md`). Pas de caméra en `auto`.

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

### Fonds et références

Ces assets se préparent **avant** le storyboard (`references/preparation.md`).

- **Un fond** (image décorative d'un chapitre, `BG-xx`, `kind: image` avec `src`) occupe **tout l'écran**, quitte à être rognée (`object-fit: cover`).
- **Une référence** (portrait, couverture, capture, image d'un auteur cité ; `ref:` ou `ref-shot`) se voit **en entier** (`object-fit: contain`) : s'il y a des bandes sur les côtés ou en haut et en bas, elles sont **transparentes** et laissent voir le fond de la scène. `fit: cover` ou `fit: contain` sur une étape force l'autre choix.
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
- **Musique** : `sound music '<prompt>' -i -d <s> -S <graine> -o assets/music/… -F json` (fast-market), appelée par `scripts/make-music.py` d'après le plan `data/music.json` que `build.py` écrit du storyboard (registre §1d, `music:`). Elle souligne les moments forts, jamais en fond continu, et est mixée **sous la voix** après le rendu (`scripts/mix-music.py`, ducking) sauf instruction contraire (`**Musique** : aucune`). Voir `references/music.md`.
- **Audio (STT)** : transcription Whisper via l'utilitaire fast-market (`video extract-transcript`, alias `video transcribe`) — utilisé en auto, en webcam et en incrustation. **Toujours deux formats** : `scripts/transcript-export.py` produit `assets/transcript.json` (mots et segments **avec timecodes**, lu par `build.py --transcript`) et `assets/transcript.txt` (le texte seul, **sans timecode**, une ligne par segment). Pour `long_publish`, `--publish final` écrit `renders/final_transcript.json` et `.txt` aux noms que long_publish cherche à côté de la vidéo publiée (`--inserts` décale les temps sur la timeline de `final.mp4`).

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
  [--mode auto|webcam|incrustation] [--avoid bas-droite] [--format 16:9|9:16] \
  [--slug mon-film]
```

| Sortie | Contenu |
|---|---|
| `data/figures.json` | registre §1 |
| `data/refs.json` | registre §1b |
| `data/steps.json` | une entrée par étape, temps absolus, caméra, `kind` |
| `data/design.json` | `kind` + paramètres, par étape |
| `data/camera.json` | timeline caméra effective (base ∪ Cast), **seulement si** `cast-segments.json` a des intervalles |
| `data/scenes.json` | scènes + beats (schéma : `references/data-schemas.md`) |
| `index.html` | composition racine : scènes, audio, registre de timeline |
| `compositions/iNN.html` | une sous-composition par scène |
| `assets/style-joriel.css` | écrit **seulement s'il est absent** (copie de la démo) |
| `assets/style-joriel-ext.css` | styles des primitives absentes de la démo (bars, seuil, compare3, caméra) |

Le temps vient de `transcript.json` s'il est fourni : chaque `cue` est recalé sur les mots de la voix. Sinon, les durées estimées du storyboard font foi. L'audio (`assets/voix.wav`, sinon le plus grand `assets/voix-posthoc-vN.wav`, N comparé numériquement), la caméra (`assets/cam-clean.mkv`) et `assets/cast-segments.json` sont détectés automatiquement s'ils existent. Sans `cast-segments.json`, le rendu webcam est exactement celui d'avant (trois états). Le mode vient de `**Mode**` dans l'en-tête du storyboard (`--mode` le force) ; `incrustation` change le rendu (`modes/incrustation.md`), les trois autres sont identiques à l'octet près.

**Nomenclature :** toujours deux chiffres avec zéro initial pour le numéro de scène — `i00.html`, `i01.html`, …, `i09.html`, `i10.html`. Jamais `i3.html`. Les identifiants (`data-composition-id`, `window.__timelines`, cadre caméra) suivent le même nommage (`i03`, etc.).

Le HTML produit reprend le balisage et les classes de `examples/demo/` : le catalogue des primitives (12 scènes, `i00` à `i11` ; `i09` : webcam avec Cast ; `i10` et `i11` : un même schéma déployé sur deux compositions), une primitive par étape. Les ids du storyboard sont les labels GSAP. Contrôle : `python3 scripts/check-steps.py`, puis `npm run check`.

L'exemple se vérifie seul :

```bash
cd $SKILL_DIR/examples/demo && npm run check
```

Avertissements connus de `hyperframes check` et leurs corrections : `references/hyperframes-check.md`.

## Contexte LLM

Fichiers à donner tels quels.

- **Scénario → storyboard**
  - Sources : `SCENARIO.md` (texte libre, l'histoire et l'argumentaire) et **la préparation** : `assets/transcript.json` + `transcript.txt`, `assets/chapters.json`, `assets/assets.md`, `assets/refs.md`, `assets/figures.md`, `assets/cast-segments.json` (webcam, incrustation), `assets/schemas/Dxx.handles.md` (les noms exacts des éléments d'un schéma) ; `assets/prep.json` dit si c'est prêt
  - `SKILL.md`
  - `references/visual-language-joriel.md`
  - `references/primitives-joriel.md`
  - `references/storyboard-format.md` (format lisible par `build.py`, catalogue des `kind`)
  - `references/scenario-to-storyboard-prompt.md` (prompt de transformation)
  - `examples/storyboard.example.md` (exemple complet et parsable)
  - Selon le mode : la section « Contexte LLM » de son sous-skill (`modes/<mode>.md`) ajoute ses propres fichiers.
  - Conventions détaillées : `references/scenario-studio-conventions.md`

- **Storyboard → contrôle**
  - `assets/storyboard.md` (la sortie du LLM)
  - `scripts/build.py` produit la composition ; on ne réécrit pas le storyboard à la main après le build.
  - Selon les besoins :
    - Extraits de tweets ou vidéos externes : `references/embed-tweets-video.md`

## Modes

Chaque mode a son sous-skill, à lire une fois le mode choisi (§ Routeur) : `modes/auto.md`, `modes/webcam.md`, `modes/incrustation.md`. Un sous-skill décrit ses étapes, ses règles propres et le contexte LLM supplémentaire ; tout ce qui est commun reste dans ce fichier.

## Ce que ce dépôt fournit

- `scripts/build.py` : builder générique des trois modes, source unique `assets/storyboard.md`.
- `scripts/render_primitive.py` : module commun de rendu des primitives, importé par `build.py`. Une primitive n'est écrite qu'une fois.
- `scripts/prepare.py` : la préparation (checklist, contrôle, chapitres, validation des schémas) ; `scripts/transcript-export.py`, `scripts/make-music.py`, `scripts/mix-music.py`, `scripts/excalidraw-preview.py`, `scripts/schema-to-excalidraw.py` : les étapes qui l'entourent.
- Les primitives sont dans `references/primitives-joriel.md` et rendues par `render_primitive.py`. Les **schémas animés** (`kind: schema`, registre §1c, état qui persiste d'une étape à l'autre) sont décrits dans `references/schemas-animes.md` et rendus par `scripts/schema_anim.py`. `seuil`, `bars`, `compare3`, `brand`, la caméra et l'incrustation sont couverts ; leurs styles manquants sont écrits dans `assets/style-joriel-ext.css` au build. **Schémas Excalidraw** : un fichier `assets/schemas/Dxx.excalidraw`, asset de la préparation, qu'on regarde (`scripts/excalidraw-preview.py`), valide et retouche avant de l'intégrer ; ronds, losanges, imbrications ; voir `references/schemas-excalidraw.md`.
- Un `kind` absent du catalogue ne s'invente pas : on l'ajoute d'abord à `visual-language-joriel.md`, `primitives-joriel.md`, `examples/demo/` et `render_primitive.py`, puis on l'utilise.

Limites assumées :

- La collecte des assets (Pexels, `thesvg`, captures, embeds) reste manuelle ou via les outils cités en § Assets.
- Le TTS et le STT sont des commandes externes (`npx hyperframes tts`, fast-market `video transcribe`) : le dépôt ne les réimplémente pas.
- `examples/demo/` reste le chapitre de référence ; ses médias factices sont générés par le script de placeholders du dépôt source.
