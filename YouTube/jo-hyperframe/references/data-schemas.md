# Schémas des fichiers `data/`

Ces fichiers sont produits par les builders du projet (non fournis, voir `SKILL.md` § « Ce que ce dépôt ne fournit pas »). Les champs ci-dessous viennent de `scenario-studio-conventions.md` §2-3, de `posthoc-video-conventions.md` et du code de `scripts/build_studio_anim.py`.

| Fichier | Lu par un script de ce dépôt | Rôle |
|---|---|---|
| `data/figures.json` | `build_studio_anim.py` | registre des chiffres |
| `data/scenes.json` | `build_studio_anim.py` | scènes de la vue « animation pas à pas » |
| `data/steps.json` | aucun (builders du projet) | une entrée par étape, durées |
| `data/design.json` | aucun (builders du projet) | blocs et gabarits de l'écran |
| `data/refs.json` | aucun (builders du projet) | registre des références `Rxx` |

`scripts/check-steps.py` ne lit aucun de ces fichiers : il compare le deck, la section du storyboard et les labels GSAP.

## `data/figures.json`

Objet `{"figures": {"F01": {...}}}`, clé = identifiant de la figure. Champs : `value`, `label`, `source`, `status` (`ok` ou `verify` ; `verify` donne une pastille visible avec `?draft=1` seulement), `note`. Les chiffres écartés sont absents du fichier.

```json
{"figures": {"F01": {"value": "+5 000", "label": "interpellations", "source": "Le Monde, 2026-10-10", "status": "ok", "note": ""}}}
```

## `data/scenes.json`

Objet `{"scenes": [...]}`. Champs lus par `build_studio_anim.py` : `id`, `section`, `title`, `type`, `illustration` (fond), `punchline`, `beats`. Un beat : `cue`, `text`, `figure` ou `figures`, et selon le gabarit `kind`, `viz`.

```json
{"scenes": [{"id": "I1", "section": "…", "title": "Titre court", "type": "numbers", "illustration": "assets/bg/BG-01.jpg", "punchline": "…", "beats": [{"cue": "interpellations", "text": "+5 000", "figure": "F01"}]}]}
```

## `data/steps.json`

Une entrée par étape : `id`, `scene`, `slide`, `frag`, `cue`, `appear`, `type`, `fond`, `figures`, `duration`, `punch`, plus les métadonnées de scène. C'est le seul endroit où recaler les durées (la durée d'une scène est répartie entre ses étapes), puis on reconstruit. Mode webcam : en plus `t` et `end` en secondes absolues, `camera` (`off`, `pip`, `full`), `cam_src` (`assets/cam-original.mkv`) et `media_start`. Le champ `camera` n'est contrôlé par aucun script.

Champ optionnel `ref` : identifiant `Rxx` de la source citée par l'étape (voir `refs.json`).

## `data/design.json`

Ce qui s'affiche à l'écran, par étape : blocs `kw`, `sub`, `arrow`, `strike`, `icon`, `brand`, `chip`, `stamp`, `bignum`, et gabarits `diverge`, `seuil`, `compare3`, plus `{"cols2": true}` par scène. Exemples exacts des gabarits : `examples/gabarits/design.json`.

## `data/refs.json`

Même forme que `figures.json`, clé = `Rxx`. Champs : `type` (`tweet`, `page`, `capture`, `video`, `image`), `source` (URL), `file` (chemin local sous `assets/references/`), `status` (`ok`, `à capturer`, `bloquée`). Un `Rxx` ne s'affiche jamais à l'écran : seule l'attribution lisible.

```json
{"refs": {"R01": {"type": "tweet", "source": "https://x.com/…", "file": "assets/references/R01-nom.png", "status": "ok"}}}
```
