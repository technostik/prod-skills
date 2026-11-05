# REFACTOR-NOTES

## À décider (propriétaire)
- licence : choix laissé au propriétaire.
- nom du dépôt (`hyperframe-gen`) vs nom du skill (`hyperframe-joriel`).
- règle `npm run check` : tranchée en « une fois avant tout rendu, et sur demande » (l'ancienne règle disait « sur demande uniquement »). À confirmer.
- correspondance avec la skill de scénarisation : voir `references/glossaire.md` (à vérifier).

## État après 1.9.1
- `examples/demo` : tous les médias référencés sont générés par `scripts/make-placeholders.sh` (vérifié : aucun fichier manquant). `npm run check` n'a pas pu être exécuté dans l'environnement de correction (pas d'accès réseau à npm) : à lancer en local.
- `examples/demo/storyboard.md` : storyboard minuté du catalogue (réécrit en 1.9.2 ; renommé de `scenario.md` en 1.12.0).
- Occurrences volontairement conservées des anciens termes : `references/glossaire.md` (table de correspondance), `CHANGELOG.md`, et valeurs par défaut des variables d'environnement (`SKILL.md` § Prérequis, `os.environ.get(...)` dans les scripts).
- Gabarits `seuil`, `compare3`, `cols2` : décrits par du JSON (`data/design.json`), rendus par un builder non fourni ; pas de HTML à extraire. Exemples : `examples/gabarits/design.json`.
- Builders `build.py`, `make-steps.py`, `make-scenario.py` : non fournis (propres au projet).

## État après 1.9.2
- `hyperframes lint` sur `examples/demo` : 0 erreur, 0 avertissement (vérifié avec hyperframes@0.8.123). `hyperframes check` (mise en page, contraste) non exécutable sans Chrome dans l'environnement de correction : à lancer en local.
- Décisions de style à valider : `.step-punch` sur noir pur (spec `visual-language` §1) ; `.slideno` et `.dkw.dim` en `--gris` (contraste) à la place de `--gris-rappel` ; CSS déduit de `chip`, `stamp`, `dico`, `cols2`.
- Primitives sans balisage dans le dépôt, absentes de la démo : `bar`/`bars`, `seuil`, `compare3`, `define`, `brand`, `doc-crop`, `ref-iframe`.

## État après 1.12.0

- **Un seul builder de composition finale** : `scripts/build.py`, générique et livré dans le dépôt. La phrase « builders non fournis » de 1.9.1 ne vaut plus pour lui ; `make-steps.py` et `make-scenario.py` n'existent plus dans le flux (le storyboard tient les deux rôles).
- **Deux builds** : composition finale (`build.py`, toujours) et studio pas à pas (`build_studio_anim.py` + `build_studio_slides.py`, mode slides seulement). Les builders studio n'ont pas été fusionnés dans `build.py`.
- **Une seule grammaire visuelle** : `scripts/render_primitive.py` est importé par les deux. `build.py` écrit `beats[].params` dans `scenes.json` pour que le studio rende les mêmes primitives. Le studio n'a plus de texte propre à un projet (sources, libellé de waffle, dossier d'overlays).
- **Le storyboard est la source unique.** Registres `Fxx`/`Rxx`, scènes, étapes et `kind` viennent de `assets/storyboard.md` ; `data/*.json` sont des sorties, jamais éditées à la main.
- `build.py` écrit `assets/style-joriel.css` seulement s'il est absent, et toujours `assets/style-joriel-ext.css` (styles de `bars`, `seuil`, `compare3`, `brand`, `cam-frame` absents de la démo).
- **Primitives couvertes par `build.py`** : `kw`, `title`, `count`, `strike`, `chain`, `enumerate`, `versus`, `diverge`, `seuil`, `bars`, `compare3`, `stamp`, `define`, `ref-card`, `ref-shot`, `image`, `punch`, `brand`, `cols2`. Un besoin absent s'ajoute d'abord au catalogue, pas au cas par cas dans le builder.
- Vérifié dans un projet temporaire (6 scènes, 12 étapes) : `build.py` puis `hyperframes check` → `ok: true` avec audio, caméra et transcript. `check-steps.py` → zéro écart.
- Reste à valider sur une vraie vidéo : calage des `cue`, rendu visuel des primitives `bars`/`seuil`/`compare3`, et fluidité de la caméra en mode webcam.
