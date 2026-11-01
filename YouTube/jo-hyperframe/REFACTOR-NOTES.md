# REFACTOR-NOTES

## À décider (propriétaire)
- licence : choix laissé au propriétaire.
- nom du dépôt (`hyperframe-gen`) vs nom du skill (`hyperframe-joriel`).
- règle `npm run check` : tranchée en « une fois avant tout rendu, et sur demande » (l'ancienne règle disait « sur demande uniquement »). À confirmer.
- correspondance avec la skill de scénarisation : voir `references/glossaire.md` (à vérifier).

## État après 1.9.1
- `examples/demo` : tous les médias référencés sont générés par `scripts/make-placeholders.sh` (vérifié : aucun fichier manquant). `npm run check` n'a pas pu être exécuté dans l'environnement de correction (pas d'accès réseau à npm) : à lancer en local.
- `examples/demo/scenario.md` : storyboard minuté du catalogue (réécrit en 1.9.2).
- Occurrences volontairement conservées des anciens termes : `references/glossaire.md` (table de correspondance), `CHANGELOG.md`, et valeurs par défaut des variables d'environnement (`SKILL.md` § Prérequis, `os.environ.get(...)` dans les scripts).
- Gabarits `seuil`, `compare3`, `cols2` : décrits par du JSON (`data/design.json`), rendus par un builder non fourni ; pas de HTML à extraire. Exemples : `examples/gabarits/design.json`.
- Builders `build.py`, `make-steps.py`, `make-scenario.py` : non fournis (propres au projet).

## État après 1.9.2
- `hyperframes lint` sur `examples/demo` : 0 erreur, 0 avertissement (vérifié avec hyperframes@0.8.123). `hyperframes check` (mise en page, contraste) non exécutable sans Chrome dans l'environnement de correction : à lancer en local.
- Décisions de style à valider : `.step-punch` sur noir pur (spec `visual-language` §1) ; `.slideno` et `.dkw.dim` en `--gris` (contraste) à la place de `--gris-rappel` ; CSS déduit de `chip`, `stamp`, `dico`, `cols2`.
- Primitives sans balisage dans le dépôt, absentes de la démo : `bar`/`bars`, `seuil`, `compare3`, `define`, `brand`, `doc-crop`, `ref-iframe`.
