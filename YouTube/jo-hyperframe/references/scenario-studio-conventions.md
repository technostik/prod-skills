# Conventions du studio scénario

Le balisage du rendu est `examples/demo/`. Ce fichier décrit le studio :
correspondance des ids, prompteur, sons, fonds.

Pattern éprouvé (projets de l'auteur, non fournis) : quand le projet contient,
en plus du deck slides, un **fichier scénario** (scènes, étapes, fonds, chiffres),
la présentation joue le scénario avec le moteur HyperFrames et le prompteur
n'affiche que le « en plus ». Les fichiers sources (`01-prompt`, `02-scenario`,
`03-slides`) ne sont **jamais modifiés** : tout le design vit dans `data/` + builders.

## 0. Principes

- **Le scénario ILLUSTRE, le prompteur EXPLIQUE.** Zéro chevauchement : toute
  information déjà affichée à l'écran est interdite au prompteur.
- **Toujours synchronisés** : les deux vues avancent ensemble sur les mêmes
  étapes `SLIDE#k` (BroadcastChannel + localStorage dédiés).
- **Illustrer avec des images** : génération (`image generate`, flux29bcloud)
  pour fonds et visuels + skill `thesvg` pour les logos de marques.
- **Contenu qui dépasse** : 2 colonnes selon la place, défilement auto sinon.

## 1. Correspondance scénario ↔ slides ↔ timeline (point le plus important)

- Scène : `I1`, `S04`… · Slide : `SCÈNE.N` (`id: S04.3` en tête de slide) ·
  Étape : `SLIDE#k` (`#0` = la slide apparaît ; `#1`, `#2`… = ses fragments
  `class="fragment"`, dans l'ordre).
- **UNE ÉTAPE = UNE APPARITION ANIMÉE = UN AFFICHAGE PROMPTEUR**, même ordre des
  deux côtés. Une étape n'introduit qu'**un seul élément visuel nouveau**,
  illustré en gros (voir langage visuel §7). Punchline = slide dédiée, étape `#0` uniquement.
- Chaque étape est un **label GSAP du même nom exact** (`tl.addLabel("S04.3#2", t)`).
- Les `cue` (mots probables de la voix improvisée) servent au prompteur et au
  recalage, jamais au déclenchement automatique.
- Contrôle obligatoire, zéro écart exigé avant d'enregistrer :
  `python3 scripts/check-steps.py` (voir l'aide intégrée pour `--slides`,
  `--scenario`, `--sec-start/--sec-end`). Il compare : étapes déduites des slides,
  étapes déclarées du scénario, labels de `studio.html` + `index.html` +
  `compositions/`, dans le même ordre.

## 2. Données du studio

- `data/figures.json` : registre unique des chiffres `{value, label, source,
  status, note}`. `ok` = affiché normalement ; `verify` = pastille
  « À VÉRIFIER » visible **uniquement avec `?draft=1`**, jamais en version jouée ;
  écartés = absents du fichier, jamais affichés. Chaque scène de données affiche
  sa ligne « Source : … ».
- `data/steps.json` : 1 entrée par étape `{id, scene, slide, frag, cue, appear,
  type, fond, figures, duration, punch}` + métadonnées scènes. **Seul endroit
  pour recaler les durées** (durée scène répartie entre ses étapes), puis rebuild.
- `data/design.json` : différenciation écran (voir §3) + `{"cols2": true}` par scène.

## 3. Écran laconique, prompteur complet (dosage)

- L'écran **ne répète pas** l'énumération des slides : mots-clés visuels
  (`data/design.json`, blocs `kw`/`sub`/`arrow`/`strike`/`icon`/`brand`/`chip`/
  `stamp`/`bignum`), **dans le même langage que le reste** : grandes lignes 6vh
  + filet de séparation, sous-lignes, chips, compteurs, barres — jamais de style
  « cartes » qui détonne. Icônes et animations inline à la même échelle
  (flèche qui glisse, barré qui se trace, tampon qui claque, picto qui pop,
  mot-clé accent qui pulse).
- Le prompteur garde les phrases complètes… **non** : voir §4, il ne garde que
  le « en plus ». Punchlines et chiffres : **mot pour mot**, jamais reformulés.
- Tailles à 1080p : contenu ≥ 64 px, titres 96–140, chiffres 260–420, punchlines
  110–150, sources/repères ≥ 40 px. Une couleur d'accent unique, 2 polices max,
  aucune police réseau. Repère « Le bilan » / « L'analyse » en coin.
- Punchlines plein écran, entrées 0,5–1,2 s (mot par mot pour les punchlines,
  ligne par ligne pour les listes, compteurs, barres qui poussent).

## 4. Prompteur = informations en plus (jamais de redite de l'écran)

Règle : **si l'information est déjà affichée dans le scénario, inutile de la
rajouter au prompteur**. Chaque bloc = ancre minimale + « en plus » :
- ancre (petit) : `ÉTAPE i/N — ID · section · titre scène`, puis
  `slide X.N · fragment k/n` (ou `plein écran`) `· ~Xs · cue : …`
  (+ `⚠ chiffre à vérifier` si figure `verify`) ;
- notes `note:` **en grand** (arguments, transitions, vigilances — jamais la
  répétition du slide) ; si absentes : mention discrète
  « (pas de notes — improviser depuis l'écran) ».
- Ne PAS afficher l'aperçu complet du slide. Les slides sans notes deviennent
  visiblement vides : les faire compléter **avec du « en plus »** (pas de redite)
  avant l'enregistrement.

## 5. Listes longues : 2 colonnes + défilement de secours

- Scènes à ≥ 5 items : `"cols2": true` dans `data/design.json` (titres pleine
  largeur, lignes simples sans encadré, tailles réduites ~4,8vh pour tenir en
  3 rangées à 1080p).
- Toutes les zones : `overflow-y: auto` (ascenseur masqué) + recentrage auto sur
  l'étape courante — secours uniquement, le contenu doit tenir sans scroller.

## 6. Sons : peu, courts, variés, coupables jamais

- Générer avec `scripts/make-sfx.py` (stdlib, WAV 16-bit) : 3 pops alternés
  (0,09 s, jamais 2× le même de suite), 1 tic discret (0,05 s, compteurs/barres/
  grille), 1 carillon 2 notes (0,5 s, **punchlines uniquement**).
- Règle codée : **1 son max par étape**, titres de slides silencieux, rien sur le
  texte courant. Volumes 0.10–0.16, `play()` en `catch` silencieux (autoplay :
  le son ne démarre qu'après un geste). Émis par la seule fenêtre présentation.
- Contrôle : bouton **Son : on/coupé** + touche `M`, `?mute=1` (`?sound=0`).

## 7. Icônes (skill `thesvg` pour les marques)

- Marques : chercher le slug dans le registre (`icons.json` via jsDelivr pour les
  accès agent), télécharger en local `assets/icons/`. Sur fond sombre : variante
  `light`/`mono` si dispo (sinon pastille claire derrière le logo, **sans altérer
  le tracé**). Marques = propriété de leurs détenteurs, usage éditorial.
  Vérifier l'absence au registre avant de renoncer (pas d'icône inventée).
- Concepts génériques : jeu de pictos trait inline (style unique, accent/neutres),
  pas de marques détournées. Pas d'icônes réseau au rendu (tout en local).

## 8. Fonds (BG-00 par défaut, BG-01..08 par scène, punchlines sur noir pur)

- **Défaut : `assets/bg/BG-00.jpg`** (réseau neuronal blanc sur noir — l'image
  de référence du langage). Toute scène sans fond dédié l'utilise. **Jamais
  de noir nu** hors punchlines (voir langage visuel §1, paragraphe « Fonds »).
- `assets/bg/BG-01..08.jpg`, 1920×1080 min, descriptions du scénario, sans personne
  identifiable / logo / texte lisible. Voile sombre 55–70 %, zoom lent 3–6 %,
  fondu entre scènes de fonds différents.
- Génération `image generate '<prompt>' -e flux29bcloud -w 1920 -h 1080
  --output-format JPEG -o assets/bg -F json`, `mv` **immédiatement après chaque
  génération** (la CLI écrase sinon). Modération Cloudflare : reformuler neutre.
- Quota épuisé (erreur 429) → fallback prévu : réutiliser des assets existants
  (redimensionnés) + procédural, **nommés pareil**, signalés à régénérer dans le
  rapport (prompts neutres fournis).

## 9. Livrables par projet

- `studio.html` (manuel à enregistrer) + `index.html` (auto, mêmes labels) +
  `compositions/` (1/scène, indépendantes) + `studio-slides.html` (skill, conformité).
- `scripts/` : `build.py` et `make-steps.py` (propres au projet, non fournis : voir `SKILL.md`),
  `make-sfx.py`, `check-steps.py`, `studio_server.py`, `build_studio_slides.py`.
- `README.md` (lancer, relier, contrôler, `?draft=1`, sons) + `BUILD-REPORT.md`
  (tableau étape ↔ label, BG à refaire, ⚠, écarts skill, vérifications manuelles).
- Ne jamais rendre de mp4 sans feu vert : vérifier lancement, labels, contrôle.
