# Schémas des fichiers `data/`

Ces fichiers sont produits par `scripts/build.py` à partir de `assets/storyboard.md` (voir `SKILL.md` § Composition). Ce sont des sorties : on ne les édite pas à la main, on corrige le storyboard et on relance le build.

| Fichier | Producteur | Lu par | Rôle |
|---|---|---|---|
| `data/figures.json` | `build.py` | `build_studio_anim.py` | registre des chiffres (§1 du storyboard) |
| `data/refs.json` | `build.py` | — | registre des références (§1b du storyboard) |
| `data/scenes.json` | `build.py` | `build_studio_anim.py` | scènes de la vue « animation pas à pas » |
| `data/steps.json` | `build.py` | — | une entrée par étape, temps absolus |
| `data/design.json` | `build.py` | — | primitive (`kind`) et paramètres, par étape |

`scripts/check-steps.py` ne lit aucun de ces fichiers : il compare le storyboard et les labels GSAP de `index.html` / `compositions/` / `studio.html`.

## `data/figures.json`

Objet `{"figures": {"F01": {...}}}`, clé = identifiant de la figure. Champs : `value`, `label`, `source`, `status` (`ok` ou `verify` ; `verify` donne une pastille visible avec `?draft=1` seulement), `note`. Les chiffres écartés du storyboard sont absents du fichier.

```json
{"figures": {"F01": {"value": "+5 000", "label": "interpellations", "source": "Le Monde, 2026-10-10", "status": "ok", "note": ""}}}
```

## `data/scenes.json`

Objet `{"scenes": [...]}`. Champs lus par `build_studio_anim.py` : `id`, `section`, `title`, `type`, `illustration` (fond), `punchline`, `beats`. Un beat : `cue`, `text`, `kind`, `col` (`left` / `right` / `full`), `figure` ou `figures`, et selon le gabarit `viz`.

```json
{"scenes": [{"id": "I1", "section": "bilan", "title": "Titre court", "type": "numbers", "illustration": "assets/bg/BG-01.jpg", "punchline": "…", "beats": [{"cue": "interpellations", "text": "+5 000", "kind": "count", "col": "full", "figure": "F01"}]}]}
```

## `data/steps.json`

Une entrée par étape : `id`, `scene`, `scene_title`, `slide`, `frag`, `cue`, `appear` (temps relatif à la scène), `t` et `end` (temps absolus), `type`, `fond`, `figures`, `duration`, `punch`, `camera` (`off`, `pip`, `full`, ou l'annotation `cast` ; jamais un état d'affichage : voir `data/camera.json`), `kind`.

Sans transcript, les temps viennent des durées estimées du storyboard. Avec `--transcript`, chaque `cue` est recalé sur les mots de la voix.

## `data/design.json`

Objet `{"steps": {"<étape>": {kind, …paramètres}}}`. Une entrée par étape, avec la primitive normalisée (`count`, `versus`, `seuil`, `bars`, `compare3`, `ref-card`, `punch`…) et ses paramètres tels qu'écrits dans le storyboard. Exemples de gabarits : `examples/gabarits/design.json`.

## `data/refs.json`

Même forme que `figures.json`, clé = `Rxx`. Champs : `type` (`tweet`, `page`, `capture`, `video`, `image`), `source` (URL), `file` (chemin local sous `assets/references/`), `status` (`ok`, `à capturer`, `bloquée`). Un `Rxx` ne s'affiche jamais à l'écran : seule l'attribution lisible apparaît.

```json
{"refs": {"R01": {"type": "tweet", "source": "https://x.com/…", "file": "assets/references/R01-nom.png", "status": "ok"}}}
```

## Mode webcam : fichiers de la chaîne de nettoyage et de Cast

### `assets/chapters.json` (écrit par `scripts/concat-mkv.sh`)

Un objet par tronçon d'origine, bornes **cumulées dans la vidéo concaténée originale** (`cam-original.mkv`, **avant nettoyage**). Ne pas les utiliser comme référence après nettoyage ni pour les intervalles Cast.

```json
{"concat": "assets/cam-original.mkv", "timebase": "cam-original (avant nettoyage)",
 "troncons": [{"file": "chapitre-1.mkv", "start": 0.0, "end": 125.4, "duration": 125.4},
              {"file": "chapitre-2.mkv", "start": 125.4, "end": 248.9, "duration": 123.5}]}
```

### `assets/clean-map-vN.json` (écrit par `scripts/clean-posthoc.py`)

Carte des coupes d'**une** passe de nettoyage ; `N` est celui de `voix-posthoc-vN.wav` de la même passe. Champs : `version`, `src`, `clean` (le master, `assets/cam-clean.mkv`), `wav`, `noise`, `min_d`, `keep`, `keeps` (segments conservés, secondes de `cam-original`), `cuts` (silences coupés).

### `assets/cast-segments.json` (écrit par `scripts/detect-cast.py`)

Intervalles Cast, exprimés dans le référentiel de `assets/cam-clean.mkv`. Version 1, intervalles semi-ouverts `[start, end)`, temps en secondes depuis le début de la vidéo nettoyée, `end_frame` exclusif. Liste vide si aucun filet (cas normal).

```json
{"version": 1, "source": "assets/cam-clean.mkv", "source_size": 123456789, "source_mtime": 1767225600.123,
 "duration": 245.6, "width": 1920, "height": 1080, "fps": 30.0, "frames": 7368,
 "segments": [{"start": 42.35, "end": 78.9, "start_frame": 1271, "end_frame": 2367}],
 "detector": {"zone_px": 20, "band_min_px": 6, "band_max_px": 16, "max_gap_s": 0.25, "min_segment_s": 0.5}}
```

| Champ | Sens |
|---|---|
| `version` | schéma ; `build.py` refuse une autre valeur que 1 |
| `source`, `source_size`, `source_mtime` | média analysé ; `build.py` avertit si la taille ou la date de `cam-clean.mkv` ne correspondent plus (nettoyage refait sans nouvelle détection) |
| `duration`, `width`, `height`, `fps`, `frames` | métadonnées du média ; `width`/`height` servent au calcul du crop, `fps` au calage des bornes sur la grille d'images |
| `segments[].start`, `end` | secondes, arrondies à la milliseconde |
| `segments[].start_frame`, `end_frame` | indices d'image (`end_frame` exclusif) ; **ce sont eux que `build.py` utilise** pour caler les bascules |
| `detector` | seuils utilisés (traçabilité) |

L'écriture est atomique (fichier temporaire puis remplacement). Le détecteur ne modifie jamais le média.

### `data/camera.json` (écrit par `scripts/build.py`, si `cast-segments.json` a des intervalles, ou en mode incrustation)

Timeline caméra effective en temps absolu (celui de `cam-clean.mkv`), pour contrôle : `version`, `mode` (`webcam` ou `incrustation`), `cast_segments` (nom du fichier lu, `null` s'il n'y en a pas), `crop_top_px`, `crop` (`scale`, `yPercent` appliqués à `.cam-content`), `timeline` : tuiles contiguës `{start, end, state, base}` où `state` ∈ `off`/`pip`/`full`/`cast` (mode webcam) ou `plein`/`cast` (mode incrustation) est ce qui s'affiche et `base` l'état de base en vigueur (celui qui revient à la fin d'un Cast). Les bornes Cast y sont décalées de 1/4 d'image avant l'image concernée (`CAST_FRAME_LEAD`).

### Mode incrustation : champs ajoutés à `data/steps.json`

En mode `incrustation` seulement, chaque étape porte `place` (zone résolue : `haut-gauche`, `haut-droite`, `bas-gauche`, `bas-droite`, `haut`, `bas`, `gauche`, `droite`, `centre`) et `place_source` (`storyboard` si l'étape avait `place:`, `auto` sinon) ; `camera` vaut toujours `plein`. Les autres modes n'ont pas ces champs.
