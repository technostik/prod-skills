# Mode incrustation

Sous-skill de `hyperframe-joriel`. Lire d'abord `SKILL.md` (socle commun). Ce fichier ne contient que ce qui est propre au mode incrustation.

## Principe

Dans les autres modes, un visuel **remplace** la vidéo (la webcam se réduit, se floute ou disparaît). Ici il se **superpose** : la vidéo du locuteur reste plein écran du début à la fin, et chaque visuel du storyboard est posé par-dessus, dans une zone de l'écran. Deux fonds possibles, sans que le storyboard ait à choisir :

- la **webcam plein écran** (vidéo plus personnelle, quelques visuels ici et là) ;
- le **screencast OBS** (démo, visuels qui ajoutent de la dynamique). Les intervalles Cast sont détectés (`detect-cast.py`) et le filet vert est retiré au rendu, comme en mode webcam.

C'est un style de vidéo à part entière, choisi **par l'utilisateur pour toute la vidéo** : il ne se mélange pas avec l'alternance du mode webcam. Le LLM ne choisit jamais la caméra ici.

## Quand

Une ou plusieurs prises `.mkv` déjà tournées (comme en mode webcam), et l'utilisateur veut que la vidéo reste visible sous les visuels. S'il ne l'a pas dit, le lui demander : webcam (alternance) ou incrustation ?

## Étapes

1. Prises : mêmes commandes que le mode webcam (`references/webcam.md` § Commandes) : `concat-mkv.sh`, `clean-posthoc.py`, `detect-cast.py` (si screencasts OBS), `video transcribe`.
2. Storyboard sur le transcript mesuré, en-tête `**Mode** : incrustation` (format minuté, § Storyboard ci-dessous).
3. Build :

```bash
python3 scripts/build.py --transcript transcript.json \
  --camera assets/cam-clean.mkv --audio assets/voix.wav \
  [--avoid bas-droite]
```

`**Mode** : incrustation` dans l'en-tête suffit ; `--mode incrustation` le force.
4. `python3 scripts/check-steps.py`, snapshots des étapes incrustées (voir § Contrôle), `npm run check` vert, preview, mp4 sur feu vert uniquement.

## Storyboard

- `**Mode** : incrustation` ; facultatif : `**Zones à éviter** : bas-droite` (ancres que la position automatique n'utilise jamais, par exemple le coin où OBS place la webcam dans le screencast).
- Format minuté ; la primitive s'écrit seule : ``- `I1.1#0` t=39.18 (3.6s) [count] 24 lycées``. Le champ `camera` n'existe pas dans ce mode : il est ignoré (`plein` pour la webcam, `cast` aux intervalles détectés). Une annotation `camera: cast` reste un simple repère éditorial (même règle qu'en mode webcam).
- `place:` (facultatif) choisit la zone d'une étape. Sans lui, la position est automatique.

Exemple complet et parsable : `examples/storyboard.incrustation.example.md`.

### Les 9 zones

Une zone est le **centre d'un sous-rectangle** de l'écran. L'écran coupé en quatre : les quatre coins. L'écran coupé en deux : haut, bas, gauche, droite. Et le centre.

| `place:` | Centre (px sur 1920×1080) | Échelle |
|---|---|---|
| `haut-gauche`, `haut-droite`, `bas-gauche`, `bas-droite` | (480 ou 1440, 270 ou 810) | 0,5 |
| `haut`, `bas` | (960, 270 ou 810) | 0,5 |
| `gauche`, `droite` | (480 ou 1440, 540) | 0,5 |
| `centre` | (960, 540) | 0,75 |

Écritures acceptées : les noms ci-dessus, `coin supérieur droite`, `coin inférieur gauche`, `plein centre`, `tl` `tr` `bl` `br` `t` `b` `l` `r` `c`, sans tenir compte des accents ni de la casse. `place: auto` force la position automatique. Un nom inconnu donne un avertissement et la position automatique.

### Position automatique

Par défaut : le milieu d'un des deux quarts supérieurs (`haut-gauche`, `haut-droite`). Le tirage est **reproductible** : il ne dépend que de l'identifiant de l'étape, jamais d'un aléa à chaque build, et la même position n'est jamais choisie deux fois de suite (hors `place:` explicite). Les zones à éviter sont exclues. Le résultat est écrit dans `data/steps.json` (`place`, `place_source` : `auto` ou `storyboard`).

### Primitives autorisées

Dans un quart d'écran, un visuel dense réduit de moitié ne se lit plus. Autorisées : `kw`, `count`, `strike`, `enumerate` (court), `stamp`, `define`, `brand`, `chain`, `image`, `ref-shot`, `ref-card` (et leurs alias). **Refusées** (le build s'arrête avec un message qui nomme l'étape et la primitive) : `versus`, `diverge`, `seuil`, `bars`, `compare3`, `waffle`, `sources`, `cols2`, `title`, `punch`, `schema` (un schéma qui se construit demande le plein cadre). Une idée qui demande une de ces primitives passe en mode webcam, ou se découpe en étapes simples.

## Rendu

- **Calques** (de bas en haut) : la vidéo plein écran (cadre `cam-frame cam-under`, `z-index` 2, sans bordure ni arrondi ni ombre), les visuels (`.step`, `z-index` 4), le numéro d'étape `.slideno`. Pas de fond image, pas de flou, pas de `pip`.
- **Visuel** : le balisage de la primitive est rendu comme en plein cadre, puis posé dans une scène de 1920×1080 réduite par l'échelle ci-dessus et centrée dans son sous-rectangle (classes `.ov`, `.ov-tl`…, `.ovstage`, dans `assets/style-joriel-ext.css`). Un panneau sombre translucide (`.ovstage .in`) assure la lisibilité sur la vidéo. Pas de titre ni de kicker.
- **Cast** : même mécanisme qu'en mode webcam (wrapper `.cam-content`, crop instantané aux bornes, `CAST_CROP_TOP_PX`) ; seul le fond change (`plein` ↔ `cast`, cadre immobile). Voir `references/webcam.md` § Cast.
- Rien n'anime la balise `<video>`.

## Contrôle

La position automatique est un pari à l'aveugle : un visuel peut cacher le visage ou l'action d'un screencast. Contrôler avec des snapshots des étapes incrustées (`npx hyperframes snapshot --at <t1>,<t2>,…`), puis corriger l'étape fautive avec `place:` et relancer `build.py` : pas de nouveau rendu complet.

## Contexte LLM (scénario → storyboard)

Fichiers communs (`SKILL.md` § Contexte LLM), plus : `references/posthoc-video-conventions.md`, `references/webcam.md` (Cast), et, s'ils existent, `assets/cast-segments.json` et `transcript.json`. Le LLM choisit la primitive de chaque étape parmi celles qui sont autorisées, et `place:` seulement quand l'utilisateur l'a demandé ou quand le texte l'impose ; il n'écrit pas de `camera`. `prepare-webcam-context.sh --mode incrustation` rassemble ces fichiers.
