# Préparation

Tout ce qui est nécessaire pour écrire le storyboard, **avant** le storyboard. La skill ne le redemande pas à chaque
projet : c'est une checklist, un script (`scripts/prepare.py`) qui la vérifie, et un fichier d'état (`assets/prep.json`).

```
scénario → PRÉPARATION → storyboard → build → contrôle → rendu → post-rendu (musique, inserts, sous-titres)
```

**La voix et le transcript viennent d'abord.** Le storyboard se pose sur ce qui est réellement dit, avec ses temps :
auto : le scénario est vocalisé (TTS) puis transcrit ; webcam et incrustation : le locuteur dicte la prise. Le storyboard
n'est jamais écrit sur une voix qui n'existe pas encore. (Le mode `slides`, où le storyboard précédait la voix, est archivé :
`archive/slides/README.md`.)

## Les livrables

| Livrable | Fichier | Comment | Modes |
|---|---|---|---|
| **Scénario** | `SCENARIO.md` | texte libre, l'histoire ; un titre `##` par chapitre | tous |
| **Voix** | `assets/voix.wav` (auto) ; `assets/cam-clean.mkv` + `voix-posthoc-vN.wav` (webcam, incrustation) | TTS (`media-use`, Kokoro) ; ou `concat-mkv.sh` + `clean-posthoc.py` | tous |
| **Transcript** | `assets/transcript.json` (avec timecodes) + `transcript.txt` (sans) | `scripts/transcript-export.py --from-video <voix>` | tous |
| **Fonds d'écran** | `assets/assets.md` + `assets/bg/BG-xx.jpg` | image/vidéo 1920 × 1080 : Pexels, génération `image`, `thesvg` pour les logos | tous |
| **Références** | `assets/refs.md` + `assets/references/…` | une source citée (tweet, page, article) : capture ou carte locale | tous |
| **Assets de référence** | `assets/refs.md` (type `portrait`, `couverture`) | l'image d'un **auteur** ou d'une œuvre **cités** : portrait, couverture | si un auteur est cité |
| **Chapitres** | `assets/chapters.json` + `chapters.txt` | `scripts/prepare.py chapters` : les titres `##` du scénario alignés sur le transcript | tous |
| **Screencasts** | `assets/cast-segments.json` | `scripts/detect-cast.py assets/cam-clean.mkv` | webcam, incrustation |
| **Schémas** | `assets/schemas/Dxx.excalidraw` | dessinés ou générés, **regardés et validés** avant d'être intégrés | si besoin |
| **Chiffres** | `assets/figures.md` | un chiffre affiché a **toujours** une source | si besoin |
| **Inserts** | `assets/inserts.json` | extraits vidéo à insérer (`references/inserts.md`) | facultatif |

Ajoutés à ta liste : **chiffres sourcés** (le storyboard n'invente ni chiffre ni URL, il pioche dans le registre) et
**inserts** (extraits, avec leur point de coupe). Ni la musique ni les sons ne sont préparés : ils se décident dans le
storyboard (`references/music.md`) et se génèrent après le build.

## Dans l'ordre, par mode

### auto

1. `SCENARIO.md` (le script *est* la voix).
2. Vocaliser (TTS) → `assets/voix.wav`.
3. `python3 scripts/transcript-export.py --from-video assets/voix.wav` → transcript JSON + TXT.
4. Fonds, références, chiffres, schémas : les tableaux et dossiers ci-dessous.
5. `python3 scripts/prepare.py chapters`, puis `python3 scripts/prepare.py check`.

### webcam et incrustation

1. `SCENARIO.md` ; le locuteur dicte (pas de prompteur, écart faible avec le scénario).
2. La prise : `concat-mkv.sh` puis `clean-posthoc.py` (`references/webcam.md` § Commandes).
3. Screencasts : `detect-cast.py assets/cam-clean.mkv --output assets/cast-segments.json` (**après chaque nettoyage** ; s'il n'y en
   a pas, `"screencasts": "none"` dans `assets/prep.json`).
4. `python3 scripts/transcript-export.py --from-video assets/voix-posthoc-vN.wav` (N = la dernière passe).
5. Fonds, références, chiffres, schémas.
6. `python3 scripts/prepare.py chapters`, puis `python3 scripts/prepare.py check`.

## Commandes

```bash
python3 scripts/prepare.py init --mode auto|webcam|incrustation   # dossiers + gabarits + checklist du mode
python3 scripts/prepare.py check                                    # état de chaque livrable ; code 1 tant que ça bloque
python3 scripts/prepare.py chapters                                 # chapitres
python3 scripts/prepare.py validate-schema D01                      # après avoir regardé le schéma
```

`check` écrit `assets/prep.json` (`mode`, `ready`, l'état de chaque livrable). **Le storyboard s'écrit quand `ready` est vrai.**
Un livrable est `ok`, `n/a` (rien à préparer : par exemple aucune référence), `à faire` ou `BLOQUANT`.

## Formats

### `assets/assets.md` : les fonds

| ID | Description | Fichier | Statut |
|---|---|---|---|
| BG-00 | noir + voile (fond par défaut) | assets/bg/BG-00.jpg | ok |

Un fond par chapitre au moins, varié. **Un fond est toujours affiché plein écran**, rogné au besoin (`cover`) : cadrer l'image
pour que le sujet résiste au rognage. Rien d'identifiable, pas de logo, pas de texte lisible. Statut : `à faire`, `ok`, `écarté`.

### `assets/refs.md` : les références

| ID | Type | Source | Fichier local | Statut |
|---|---|---|---|---|
| R01 | tweet | https://x.com/… | assets/references/R01-tweet.png | ok |
| R02 | portrait | https://fr.wikipedia.org/… | assets/references/R02-auteur.jpg | ok |

Mêmes colonnes que le registre §1b du storyboard : le LLM les y recopie. **Une référence se voit toujours en entier** (`contain`) :
s'il y a des bandes, elles sont transparentes et laissent voir le fond de la scène. Sources : `references/embed-tweets-video.md`.

### `assets/figures.md` : les chiffres

| ID | Valeur | Libellé | Source | Statut |
|---|---|---|---|---|
| F01 | +57 % | budget de l'éducation depuis 2000 | INSEE 2024 | ok |

Statut : `ok`, `verify` (pastille « À VÉRIFIER » en brouillon), `écarté` (jamais affiché). Sans source, `check` bloque.

### `assets/chapters.json` et `chapters.txt`

`chapters.json` : `[{"start": 0.0, "title": "Le constat"}, …]` (un chapitre `"verify": true` a un alignement incertain, à vérifier).
`chapters.txt` : le format de description YouTube, `00:00 Le constat`, premier chapitre à `00:00`, au moins trois chapitres, au moins
10 s chacun (YouTube ignore les plus courts : ils sont fusionnés).

### Schémas

`assets/schemas/Dxx.excalidraw`, regardé (`Dxx.preview.png`), validé (`prepare.py validate-schema Dxx` : un tampon `Dxx.validated`
porte l'empreinte du fichier). Retouché ensuite, il redevient « à valider » : `check` bloque. Voir `references/schemas-excalidraw.md`.

## Ce que reçoit le LLM qui écrit le storyboard

`SCENARIO.md`, `assets/transcript.json` et `transcript.txt`, `assets/chapters.json`, `assets/assets.md`, `assets/refs.md`, `assets/figures.md`,
`assets/cast-segments.json` (webcam, incrustation), pour chaque schéma `assets/schemas/Dxx.handles.md` (les noms exacts des éléments), et les
références de la skill (`SKILL.md`, `references/visual-language-joriel.md`, `references/primitives-joriel.md`, `references/storyboard-format.md`,
`references/scenario-to-storyboard-prompt.md`, `examples/demo/`). `prepare-webcam-context.sh` rassemble ces fichiers dans un dossier.
