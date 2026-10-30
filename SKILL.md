---
name: hyperframe-joriel
description: Build a Joriel-styled HyperFrames video in one of three modes — auto (the script is the transcript, vocalized with TTS), slides (composition from the script, then a live take that may diverge), or webcam (a take read from the script, then the composition from the measured transcript). Write the scenario before the composition. The worked chapter is examples/demo. Use when the user asks for hyperframe-joriel.
argument-hint: "<script.md | video.mkv>"
author: joriel
category: Video Creation
version: 1.11.0
---

# Hyperframe-joriel

Trois modes, un seul langage visuel. Ne jamais mélanger deux modes dans le même projet.
On part toujours d'un script. Le transcript est ce qui est dit. Le mp4 YouTube sort de deux étapes : le scénario, puis la composition.

**Routeur**

- Rien n'est enregistré, le TTS lira le script → **auto**. Script = transcript.
- Le script est monté en présentation, le locuteur s'enregistre en commentant → **slides**. L'écart entre le script et la prise peut être important.
- 1..n `.mkv` déjà tournés en lisant le script, sans composition → **webcam**. L'écart est faible. S'il manque l'ordre des tronçons, le demander.

S'il manque le script : le demander, ou l'obtenir via `hyperframe-scenario`. Un scénario ou des slides déjà fournis ne se réécrivent pas : on vérifie seulement que les identifiants correspondent. Sinon, cette skill les écrit avant la composition.

## Vocabulaire

- **Studio** : montage vidéo HyperFrames. **Slides** (le produit) : pas à pas avec enregistrement. Le mode **auto** et le mode **webcam** finissent en studio. Le mode **slides** enregistre au pas à pas.
- **Script** : le texte de départ, dans les trois modes.
- **Transcript** : ce qui est dit. Auto : le script, lu par le TTS. Slides : la prise, qui peut s'écarter beaucoup du script. Webcam : la lecture, écart faible. Après une prise, le transcript mesuré porte les temps.
- **Notes** : le guide pour commenter. Visibles du locuteur seul (`note:`).
- **Scénario** : l'histoire qu'on va raconter, écrite avant tout le reste. C'est l'amont de toutes les étapes. Dans les trois modes, on part toujours d'un scénario à disposition.
- **Storyboard** : la mise en scène écrite avant la composition (`assets/scenario-hyperframes.md`). Il décrit l'écran, pas ce qui est dit. Généré à partir du `transcript.json` (timecodes complets). C'est ce qu'on appelait auparavant « scénario ».
- **Composition** : le document HTML animé. Une scène par unité du scénario. Le chapitre de référence est `examples/demo/`.
- **Preview** : le HTML affiché avant le mp4.

## Principes

La composition illustre, le transcript explique. L'un renforce l'autre. La composition ne répète pas le transcript. Elle reste simple, claire, directe, et varie assez souvent pour tenir l'attention.

- Les clips illustrent le scénario. Un concept passe par un SVG (`thesvg`, en local, sans altération), un graphique, ou des mots.
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
| `SKILL_DIR` | dossier de cette skill | `~/.agents/skills/hyperframe-joriel` |
| `HF_WORKDIR` | dossier des projets HyperFrames | `~/Code/hyperframes` |
| `FASTMARKET_DIR` | dépôt fast-market (CLI `image`, `sound`) | `~/Code/fast-market` |
| `HF_VIDEOS_DIR` | sortie des prises studio | `~/Vidéos` |
| `HF_OVERLAYS_DIR` | overlays lus par le studio | `$HF_VIDEOS_DIR/OBS/assets` |

Dépendances : Node ≥ 22, `hyperframes@0.8.123`, FFmpeg, Python 3, Chrome ou Edge (prise studio), `yt-dlp` (inserts seulement). Skills compagnes : `thesvg`, `media-use`, `hyperframes`, `hyperframe-scenario` (optionnelle), `report` (diagnostic). CLI fast-market : `image`, `sound`.

## Projet

```bash
cd "$HF_WORKDIR"
npx --yes hyperframes@0.8.123 init <slug>
cd <slug>
```

`assets/gsap.min.js` doit être là (template d'init, ou copie d'un projet existant). Jamais de CDN au rendu.

## Étapes communes (ordre canonique)

Dans les trois modes, on suit le même ordre :

1. **Scénario** — l'histoire à raconter (amont, déjà à disposition).
2. **Collecte des assets** — Pexels (image/vidéo 1920×1080), `thesvg` (SVG local sans altération, logos), recherche web (personnalités), génération via fast-market `image`, embeds YouTube/tweet (voir section Assets).
3. **Storyboard estimé** — écrit à partir du script, sans temps (modes auto et slides seulement ; le mode webcam n'en a pas).
4. **Transcript** — obtenu selon le mode (TTS+STT en auto, prise en slides, concat+clean+STT en webcam) → `transcript.json` (segments + mots, timecodes complets).
5. **Storyboard minuté** — temps absolus issus de `transcript.json`, mêmes identifiants et mêmes lignes que l'estimé. En webcam, c'est le seul storyboard. Plan de l'écran, identifiants, cues. Si l'utilisateur fournit des extraits à insérer, proposer ici leur emplacement (`assets/inserts.json`, ancré sur une étape) : `references/inserts.md`.
6. **Composition HyperFrames** — traduction du storyboard minuté en HTML/CSS/JS selon le langage visuel figé (primitives). Voir `references/primitives-joriel.md` et `visual-language-joriel.md`.
7. **Post-rendu** — si `assets/inserts.json` existe, une fois `renders/full.mp4` rendu, lancer `scripts/post-render.py` : téléchargement des extraits, légère transformation, un seul graphe ffmpeg → `renders/final.mp4`. Voir `references/inserts.md`.

## Storyboard

Écrit avant toute composition, dans `assets/scenario-hyperframes.md`. Fichiers à donner à un LLM : voir Contexte LLM. C'est le plan de l'écran. Chaque ligne affichée illustre le transcript : un mot-clé, un chiffre, une flèche, une liste. Elle ne recopie pas la phrase dite. Le `type` de chaque scène est une opération du langage visuel (`references/visual-language-joriel.md`) : `title`, `numbers`, `bars`, `cards`, `list`, `versus`, `punch`, ou un nom du catalogue (`count`, `negate`, `causal-chain`, `enumerate`…). Un élément nouveau par étape. Les chiffres viennent du registre, jamais du texte libre.

### Format estimé (modes slides et auto, avant la voix mesurée)

```markdown
## 0. Fiche
- **Thèse** : …
- **Fil rouge** : …
- **Format** : 1920×1080
- **Durée** : ≈ N min
- **Parties** : …

## 1. Registre des chiffres
| ID | Chiffre | Source | Note |
| F01 | … | … | |
### ⚠️ À vérifier
### ❌ Écartés

## 1b. Registre des références
| ID | Type | Source | Fichier local | Statut |
| R01 | tweet | … | assets/references/R01-….png | ok |

## 2. Vigilance
Ce que la thèse ne doit pas faire dire aux chiffres.

## 3. Correspondance
Mêmes identifiants que les slides et que la timeline.

## 4. Scènes
### I1 — Titre court
- section: … · type: numbers · fond: BG-01 · durée estimée : 40 s · figures: F01, F02 · ref: R01
- étapes :
  - `I1.1#0` · cue « mot » → bandeau laconique
  - `I1.1#1` · cue « interpellations » → « +5 000 » : compteur
- notes: idée à dire, pas la ligne déjà à l'écran

## 5. Fonds
| ID | Description | Scènes |
| BG-01 | … | I0, I1 |
```

Références `Rxx` : `Type` ∈ tweet · page · capture · video · image ; `Statut` ∈ ok · à capturer · bloquée (card). Une étape cite sa source avec `ref: Rxx`. Acquisition : `references/embed-tweets-video.md` §8. Un `Rxx` ne s'affiche jamais à l'écran (Règles absolues).

Identifiants, les mêmes partout :

| Notion | Forme | Exemple |
|---|---|---|
| Scène | `I1`, `S04` | `S04` |
| Slide | `SCÈNE.N` | `S04.3` |
| Étape | `SLIDE#k` | `S04.3#2` |

`#0` = la slide apparaît. `#1`, `#2`… = les fragments, dans l'ordre. Une étape = une apparition = un label GSAP = un affichage au prompteur. Une punchline est une slide à part, `#0` seul. L'ordre du scénario est l'ordre des slides. Le `cue` est un mot probable de la voix, pas une réplique à lire.

### Format minuté (mode webcam, et auto une fois la voix mesurée)

Même identifiants, temps absolus sur l'audio nettoyé. Une ligne = un item, une opération, un état caméra.

```markdown
# Scénario — N étapes, N scènes, D s
Source: transcript.json (audio nettoyé).
Chiffres: N figures, statut verify si la source n'est pas confirmée.

### I1 — Titre [BG-02]
- `I1.1#0` t=39.18 (3.6s) [off/enumerate] manque de profs
- `I1.1#1` t=42.76 (2.5s) [pip/count] 24 lycées
```

`off`, `pip`, `full` : section Webcam. Après une coupe, on décale les temps et on ne réécrit pas les lignes.

### Slides (mode slides seulement)

Format du deck (un `id:` par slide, un `fragment` = une étape `#k`, `note:` pour le locuteur) : `references/studio-slides.md`, § « Format des slides ». Les modes auto et webcam n'ont pas de slides.

## Règles de rendu de la composition (spectateur final)

> `python3 scripts/check-steps.py` est exécuté à chaque modification des étapes. `npm run check` (lent) est exécuté une fois avant toute demande de rendu mp4, et sur demande de l'utilisateur. Le mp4 n'est jamais rendu sans feu vert.

### Timing des sub-compositions (IMPORTANT)
- Dans un fichier de sub-composition (`compositions/iNN.html`), les `data-start` doivent être **relatifs** au début de cette sub-composition (t=0 = début de la scène). Le `data-start` absolu (depuis le début de l'audio) est celui de l'`index.html` qui monte la sub-composition via `data-composition-src` + `data-start`.
- Ne jamais laisser des timecodes absolus dans une sub-composition : cela crée un vide au début et décale tout le reste.

### Webcam

Trois états : `off`, `pip`, `full`. Rythme : un état dure au moins 2,5 s ; revoir le locuteur (`pip` ou `full`) au moins toutes les ~20 s. Détails (CSS, `applyCam`, règles de cadre) : `references/webcam.md`.

### Règles absolues (spectateur final)

La composition est vue par le spectateur, pas par l'auteur. Règles absolues :

- **Numérotation discrète obligatoire.** Chaque étape affiche son identifiant (`I0.1#0`) en bas à gauche, gris, classe `.slideno`. C’est le repère de debug. Il reste à l’écran, y compris au rendu.
- **Aucune autre référence interne** dans le contenu : pas de codes `F01`, `R01`, `?draft=1`, ni de pastilles « À VÉRIFIER » sauf décision explicite d'affichage éditorial. Les figures du registre servent à sourcer le contenu. On affiche le **texte du registre** (la valeur et sa définition) ou l'image-source, pas le code de figure.
- **Aucune instruction de mise en page** dans le HTML affiché : pas de « couleur bleu », « fond noir pur », « sub: … », « source prioritaire Rxx », « morph avec pair », « pastille draft ». Tout ce qui est dans le scénario comme directive doit être **appliqué** dans le style/la mise en page, jamais rendu comme texte.
- **Pas de texte de scénario brut** dans les compositions : le scénario est la source de vérité, l'écran montre le résultat visuel final, pas la consigne.
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
- **Audio (STT)** : transcription Whisper via l'utilitaire fast-market (`sound transcribe … -F json -l fr -o …`) — utilisé en auto et en webcam pour produire `transcript.json`.

### Règles

- Rien n'est chargé du réseau au rendu.

## Composition

**Nomenclature des fichiers de composition :** toujours deux chiffres avec zéro initial pour le numéro de scène — `i00.html`, `i01.html`, …, `i09.html`, `i10.html`. Jamais `i3.html`. Les identifiants (`data-composition-id`, `window.__timelines`, cadre caméra) suivent le même nommage (`i03`, etc.).

Le HTML réalise le storyboard. `index.html` monte une scène par unité (`compositions/iNN.html`). Le balisage, les classes et la timeline sont ceux de `examples/demo/` : le catalogue des primitives (9 scènes, `i00` à `i08`) : une primitive par étape, texte lorem ipsum, nom affiché à l'écran. Les ids du scénario sont les labels GSAP. `python3 scripts/check-steps.py`, puis `npm run check`.

L'exemple se vérifie seul :

```bash
cd $SKILL_DIR/examples/demo && npm run check
```

Avertissements connus de `hyperframes check` et leurs corrections : `references/hyperframes-check.md`.

Deux modèles et deux contextes donnent deux HTML. L'exemple montre chaque primitive une fois ; le film reprend ce balisage et ce montage, une scène par unité du storyboard. Les scripts de preview du mode slides restent dans la section Slides.

## Contexte LLM

Fichiers à donner tels quels.

- **Scénario → storyboard**
  - Source :
    - Auto : script, puis `transcript.json` après vocalisation TTS pour le recalage.
    - Slides avant prise : script.
    - Slides après prise : transcript mesuré.
    - Webcam : `transcript.json` (segments et mots).
  - `SKILL.md`
  - `references/visual-language-joriel.md`
  - Selon le mode :
    - Webcam : `references/posthoc-video-conventions.md`
    - Conventions détaillées : `references/scenario-studio-conventions.md`

- **Storyboard → composition**
  - Source : `assets/scenario-hyperframes.md` (storyboard du film)
  - `SKILL.md`
  - `references/visual-language-joriel.md`
  - `references/primitives-joriel.md`
  - `examples/demo/index.html`
  - `examples/demo/assets/style-joriel.css`
  - `examples/demo/compositions/i00.html`
  - `examples/demo/compositions/i01.html` et les suivantes (`i02.html`, etc.)
  - Selon les besoins :
    - Extraits de tweets ou vidéos externes : `references/embed-tweets-video.md`

## Mode auto

Pas de prise, pas de slides. Le TTS lit le script (le scénario oralisé). Le scénario = le transcript.

1. Écrire le storyboard au format estimé. Résoudre les assets.
2. Vocaliser le script avec le TTS fast-market (`npx hyperframes tts`, Kokoro — skill `media-use`), puis transcrire avec Whisper fast-market pour obtenir `transcript.json`.
3. Recaler le storyboard en temps absolus sur cette voix, sans changer les lignes.
4. Monter la composition (labels = temps). `npm run check` vert, preview, mp4 sur feu vert uniquement.

## Mode slides

Entrée : le script. Écrire le storyboard au format estimé, puis les slides aux mêmes identifiants. La composition suit le storyboard, avant la prise ; après la prise, le transcript peut s'écarter du script et les temps le suivent.

Commandes à copier, deux previews (deck, composition), serveur d'enregistrement, suites de prise : `references/studio-slides.md`.

## Mode webcam

La prise est déjà faite : le locuteur a lu le script (transcript chapitré), sans composition. Pas de prompteur. Les vidéos par chapitre sont concaténées, puis transcrites pour obtenir `transcript.json`. Le storyboard minuté et la composition partent du transcript mesuré. Détail caméra, nettoyage et cues : `references/posthoc-video-conventions.md`.

Même init que Projet, puis les commandes de `references/webcam.md` (§ Commandes) : concaténer, nettoyer, transcrire.

Puis le transcript mesuré (`transcript.json`, segments + mots, skill `hyperframes`) et le scénario minuté sur cet audio. Pas de slides. Résoudre les assets, puis la composition. Chaque étape est un clip de la scène, comme `examples/demo/`. Sélecteurs GSAP scopés à l'étape. `npm run check` vert, preview, snapshots, mp4 sur feu vert uniquement.

L'audio nettoyé fait foi : tout timing se remesure après le nettoyage. La caméra suit la section Webcam, sauf surcharge explicite. Pas de cut sec.

## Ce que ce dépôt ne fournit pas

- Les builders `scripts/build.py`, `scripts/make-steps.py`, `scripts/make-scenario.py` : propres au projet (gabarit non inclus). Schémas des fichiers qu'ils produisent : `references/data-schemas.md`.
- Le HTML des gabarits `seuil` et `compare3` : ils sont décrits par du JSON dans `data/design.json` (exemples : `examples/gabarits/design.json`) et rendus par le builder. Idem `bar`/`bars`, `define`, `brand`, `doc-crop` : aucun balisage dans le dépôt, donc absents de la démo.
