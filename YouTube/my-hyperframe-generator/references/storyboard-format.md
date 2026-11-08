# Format STORYBOARD.md (standardisé, unique)

`STORYBOARD.md` est la **mise en scène structurée** d'un scénario. Il est produit par le LLM à partir de `SCENARIO.md` (texte libre) et du langage visuel figé (`references/visual-language-joriel.md`). C'est la seule source d'entrée de `scripts/build.py`.

| Terme | Nature | Auteur |
|---|---|---|
| **Scénario** (`SCENARIO.md`) | texte libre, l'histoire et l'argumentaire | humain / amont |
| **Storyboard** (`assets/storyboard.md`) | mise en scène structurée, écran par écran | LLM |
| **Primitives** | vocabulaire visuel figé, identique d'une vidéo à l'autre | `references/visual-language-joriel.md` |
| **Composition** (`index.html`, `compositions/`) | HTML/GSAP rendu par HyperFrames | `scripts/build.py` |

Le LLM rend le markdown `STORYBOARD.md` ; l'agent l'enregistre dans le projet sous `assets/storyboard.md`.

Le LLM décide **quel passage devient quelle primitive** (éditorial). Le code ne décide jamais à sa place : il applique le `kind` écrit dans le storyboard.

---

## Structure complète

```markdown
# STORYBOARD — <titre de la vidéo>

**Source** : SCENARIO.md
**Langage visuel** : references/visual-language-joriel.md
**Mode** : auto | slides | webcam | incrustation
**Durée estimée** : ≈ N min
**Format** : 1920×1080 @ 30 fps

## 0. Fiche

- **Thèse** : une phrase, le fil rouge.
- **Fil rouge** : ce qui relie le début à la fin.
- **Parties** : bilan, analyse, conclusion

## 1. Registre des chiffres

| ID | Valeur | Label | Source | Statut | Note |
|---|---|---|---|---|---|
| F01 | +5 000 | interpellations | Le Monde, 2026-10-10 | ok | |
| F02 | 24 | lycées incendiés | à confirmer | verify | dite à l'oral |

### ⚠️ À vérifier

Les figures `verify` restent dans le registre (elles sont dites), mais ne passent `ok` qu'avec une source confirmée.

### ❌ Écartés

| ID | Valeur | Raison |
|---|---|---|
| F99 | 12 | chiffre non sourçable, exclu du film |

## 1b. Registre des références

| ID | Type | Source | Fichier local | Statut |
|---|---|---|---|---|
| R01 | tweet | https://x.com/…/status/… | assets/references/R01-tweet.png | ok |
| R02 | page | https://… | assets/references/R02-page.png | à capturer |

## 2. Vigilance

Ce que la thèse ne doit pas faire dire aux chiffres ou aux sources.

## 3. Correspondance des identifiants

| Notion | Forme | Exemple |
|---|---|---|
| Scène | `I0`…`I9`, `S01`…`S99` | `S04` |
| Slide | `SCÈNE.N` | `S04.3` |
| Étape | `SLIDE#k` | `S04.3#2` |

`#0` = la scène apparaît. `#1`, `#2`… = les fragments, dans l'ordre. Une étape = une apparition = un label GSAP = un affichage au prompteur. Une punchline est une scène à part, `#0` seul. L'ordre du storyboard est l'ordre de la timeline.

## 4. Scènes

### I1 — Titre court de la scène

- section: bilan
- type: numbers
- fond: BG-01
- durée estimée: 40
- figures: F01, F02

#### Étapes

- `I1.1#0` · cue « interpellations » → **« +5 000 » : compteur**
  - kind: count
  - figure: F01
  - prefix: "+ "
  - notes: marquer le chiffre, ton calme

- `I1.1#1` · cue « lycées » → **versus : 24 incendiés vs 3 700 total**
  - kind: versus
  - left: [{"kw": "24 incendiés", "cls": "rouge"}]
  - right: [{"kw": "3 700 total", "cls": "bleu"}]
  - recall: left
  - notes: poser le contraste

## 5. Fonds

| ID | Description | Scènes |
|---|---|---|
| BG-00 | noir + voile (punchlines, défaut) | I0, S09 |
| BG-01 | photo d'ambiance | I1, I2 |
```

---

## Règles de syntaxe (lues par `build.py`)

### Scène

- En-tête : `### <ID> — <Titre court>`. ID `I0`…`I9` puis `S01`…`S99`.
- Métadonnées : un ou plusieurs bullets avant les étapes. Deux formes acceptées :
  - un bullet par clé : `- section: bilan` ;
  - une ligne groupée : `- section: bilan · type: numbers · fond: BG-01 · durée: 40`.
- Clés : `section`, `type`, `fond`, `durée` / `durée estimée`, `figures`, `refs`, `cols2`, `punchline`.
- `section` est un nom libre (`bilan`, `analyse`, `conclusion`, ou autre) ; il sert au kicker et au studio.
- `duration` en secondes. Absente : la scène estime 20 s (ou la somme des durées d'étapes).

### Étape

- Ligne : ``- `ID` · cue « mot probable » → **libellé affiché**``.
- Sous-bullets indentés (2 espaces ou plus) : `- clé: valeur`.
- Clés communes :

| Clé | Sens |
|---|---|
| `kind` | primitive visuelle (voir catalogue) |
| `notes` / `note` | indication pour le locuteur, jamais affichée |
| `camera` | `off` (défaut), `pip`, `full`, `cast` (mode webcam) |
| `durée` / `duration` | durée de l'étape en secondes |
| `t` | temps absolu explicite (storyboard minuté) |
| `figure` / `figures` | IDs `Fxx` du registre §1 |
| `ref` | ID `Rxx` du registre §1b |
| `cols2` | force deux colonnes pour cette étape |

- Les valeurs JSON s'écrivent **sur une seule ligne**, en JSON valide. Le parseur tolère aussi les guillemets simples et les valeurs nues.
- Une étape peut aussi être écrite au **format minuté** (mode webcam) :
  ``- `I1.1#0` t=39.18 (3.6s) [off/count] 24 lycées``.
  `build.py` utilise alors `t`, la durée et l'état caméra ; sans transcript, ces temps sont conservés.
  Une étape qui n'est qu'un état caméra, sans primitive, s'écrit `[cast]` (forme courte, `kind:` en sous-bullet).

#### Valeurs de `camera`

| Valeur | Sens |
|---|---|
| `off` | aucune webcam |
| `pip` | webcam incrustée |
| `full` | webcam pseudo-plein écran (50 %) |
| `cast` | intention de présenter une séquence OBS en plein écran |

```markdown
- `I2.1#0` t=42.35 (8.2s) [cast] Démonstration
  - kind: kw
  - camera: cast
```

`cast` est une **annotation éditoriale**. Les bornes de Cast viennent **uniquement** de `assets/cast-segments.json` (produit par `scripts/detect-cast.py` sur `cam-clean.mkv`, après nettoyage). Conséquences :

- un intervalle détecté s'affiche en Cast même si l'étape correspondante n'est pas annotée ;
- une étape annotée `cast` sans intervalle détecté pendant sa durée donne un avertissement de `build.py` (et l'annotation est ignorée) ;
- `camera: cast` n'écrase jamais l'état de base (`off`, `pip`, `full`) : à la fin d'un Cast, c'est l'état de base de cet instant qui revient. L'état caméra des étapes qui tombent pendant un Cast reste donc à renseigner normalement.

L'agent qui rédige le storyboard lit `cast-segments.json` et `transcript.json` pour repérer quelles étapes tombent dans un intervalle ; il annote ces étapes `camera: cast` et leur donne un état de base (`off`, `pip` ou `full`) pour l'après-Cast.

#### Mode `incrustation`

`**Mode** : incrustation` (et, facultatif, `**Zones à éviter** : bas-droite`). La vidéo reste plein écran ; le storyboard n'écrit **aucun** `camera` (ignoré). Une étape s'écrit avec sa primitive seule, en format minuté, et un `place:` facultatif :

```markdown
- `I1.1#0` t=39.18 (3.6s) [count] 24 lycées
- `I1.1#1` t=42.76 (2.5s) [kw] manque de profs
  - place: coin inférieur gauche
```

| `place:` | Zone (centre d'un sous-rectangle de l'écran) |
|---|---|
| `haut-gauche` `haut-droite` `bas-gauche` `bas-droite` | centre des quatre quarts |
| `haut` `bas` `gauche` `droite` | centre des quatre moitiés |
| `centre` | centre de l'écran |
| `auto` ou absent | automatique : un des deux quarts supérieurs, reproductible, jamais deux fois de suite la même |

Seules les primitives lisibles en surimpression sont acceptées (`kw`, `count`, `strike`, `enumerate`, `stamp`, `define`, `brand`, `chain`, `image`, `ref-shot`, `ref-card`) ; le build refuse les autres. Détails : `modes/incrustation.md`.

### Registres

- Tableaux Markdown. Colonnes reconnues par leur nom, pas par leur position.
- `§1` : `ID`, `Valeur` (ou `Chiffre`), `Label`, `Source`, `Statut`, `Note`.
- `§1b` : `ID`, `Type`, `Source`, `Fichier local`, `Statut`.
- Statut chiffre : `ok` · `verify`. Statut référence : `ok` · `à capturer` · `bloquée`.
- Les lignes d'une sous-section « Écartés » ne sont **jamais** importées.
- Un `Rxx` ne s'affiche jamais à l'écran : seule l'attribution lisible apparaît.

---

## Catalogue des `kind` (primitives)

Le `kind` d'une étape est **une primitive du langage visuel**, pas un type de scène. Chaque ligne renvoie au balisage de `references/primitives-joriel.md` et au rendu de `scripts/build.py`.

| `kind` | Ce que ça produit | Paramètres |
|---|---|---|
| `kw` | mot-clé visuel, une ou plusieurs lignes | `blocks` (liste) |
| `title` | kicker + titre de section + corps | `title`, `blocks` |
| `count` / `bignum` | compteur géant or | `figure`, `prefix`, `suffix`, `label` |
| `strike` / `negate` | proposition barrée en rouge | `strike`, `kw`, `cls` |
| `chain` / `causal-chain` | maillons et flèches | `blocks` |
| `enumerate` / `list` | items successifs, focus-shift | `items`, `index` |
| `spotlight` | liste entière, même couleur, relief tour à tour (zoom temporaire) | `items`, `cls` |
| `versus` | deux camps face à face | `left`, `right` ; `recall` / `pair` = repères éditoriaux (non rendus) |
| `diverge` | tronc + branches ↗ / ↘ | `trunk`, `up`, `down` ; `recall` éditorial |
| `seuil` | valeur contre repère | `figure`, `repere`, `repere_val`, `sens`, `verdict`, `sub` |
| `bars` | barres comparatives, échelle commune | `items` (`label`, `display`, `value`, `cls`), `max`, `label` |
| `compare3` | trois séries hétérogènes | `rows` (`icon`, `kw`, `cls`, `sub`), `verdict` |
| `stamp` | tampon verdict | `stamp`, `cls` (vert / rouge / or) |
| `define` | terme puis définition | `kw`, `sub` |
| `ref-card` | carte de source stylisée | `ref`, `source`, `author`, `title`, `quote`, `hl`, `url` |
| `ref-shot` | capture pleine page | `ref` |
| `image` | image pleine scène | `src` |
| `punch` | punchline mot à mot, noir pur | `text` |
| `brand` | logo local | `brand` (nom de `assets/brands/<nom>.svg`) |
| `cols2` | mise en deux colonnes | `blocks` |

**Blocs** (dans `blocks`, `left`, `right`, `items`, `rows`) : `kw`, `sub`, `arrow`, `strike`, `icon`, `brand`, `chip`, `stamp`, `check`, `cross`, `nl`, `darr`, `darr-big`. Les clés `cls` acceptent `plain`, `bleu`, `vert`, `or`, `rouge`, `dim`.

> **Règle** : on n'invente pas de `kind`. Si un besoin n'est pas couvert, on l'ajoute d'abord au catalogue (`visual-language-joriel.md` + `primitives-joriel.md` + `examples/demo/` + `build.py`), puis on l'utilise.

---

## Fonds

- Un fond = `assets/bg/BG-XX.jpg`, 1920×1080, local, jamais de CDN.
- Voile 55–70 % et zoom lent 3–6 % appliqués par `build.py`.
- `BG-00` = noir + voile, fond par défaut ; noir pur réservé aux punchlines.

---

## Ce que `build.py` produit

| Sortie | Contenu |
|---|---|
| `data/figures.json` | registre §1 (lu aussi par `build_studio_anim.py`) |
| `data/refs.json` | registre §1b |
| `data/steps.json` | une entrée par étape, temps absolus, caméra (`off`, `pip`, `full` ou l'annotation `cast`) |
| `data/camera.json` | timeline caméra effective (base ∪ Cast) en temps absolu ; **écrit seulement si `cast-segments.json` contient des intervalles, ou en mode incrustation** |
| `data/design.json` | le `kind` et ses paramètres, par étape |
| `data/scenes.json` | scènes + beats (schéma attendu par `build_studio_anim.py`) |
| `index.html` | composition racine : scènes, audio, durée totale |
| `compositions/iNN.html` | une sous-composition par scène |
| `assets/style-joriel.css` | écrit **seulement s'il est absent** |
| `assets/style-joriel-ext.css` | styles des primitives non présentes dans la démo (bars, seuil, compare3, caméra) |

Les temps viennent de `transcript.json` s'il est fourni (recalage des `cue`), sinon des durées estimées du storyboard. Voir `SKILL.md` § Composition.
