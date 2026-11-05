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

Une entrée par étape : `id`, `scene`, `scene_title`, `slide`, `frag`, `cue`, `appear` (temps relatif à la scène), `t` et `end` (temps absolus), `type`, `fond`, `figures`, `duration`, `punch`, `camera` (`off`, `pip`, `full`), `kind`.

Sans transcript, les temps viennent des durées estimées du storyboard. Avec `--transcript`, chaque `cue` est recalé sur les mots de la voix.

## `data/design.json`

Objet `{"steps": {"<étape>": {kind, …paramètres}}}`. Une entrée par étape, avec la primitive normalisée (`count`, `versus`, `seuil`, `bars`, `compare3`, `ref-card`, `punch`…) et ses paramètres tels qu'écrits dans le storyboard. Exemples de gabarits : `examples/gabarits/design.json`.

## `data/refs.json`

Même forme que `figures.json`, clé = `Rxx`. Champs : `type` (`tweet`, `page`, `capture`, `video`, `image`), `source` (URL), `file` (chemin local sous `assets/references/`), `status` (`ok`, `à capturer`, `bloquée`). Un `Rxx` ne s'affiche jamais à l'écran : seule l'attribution lisible apparaît.

```json
{"refs": {"R01": {"type": "tweet", "source": "https://x.com/…", "file": "assets/references/R01-nom.png", "status": "ok"}}}
```
