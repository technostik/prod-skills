# Changelog

## 1.16.0

- **Schémas animés (`kind: schema`).** Un schéma se déclare une fois dans un nouveau registre §1c du storyboard (un bloc JSON : nœuds posés sur une grille 16 × 9, liens), puis les étapes le pilotent : `show` (apparition), `glow` (relief), `focus` (le reste passe en retrait), `zoom` (cadrage caméra). Contrairement aux autres primitives, **l'état persiste d'une étape à la suivante** : le schéma se construit au fil de la voix, et un schéma qui revient dans une autre scène retrouve ce qui était déjà affiché.
- Les étapes schéma consécutives d'une scène sont rendues dans **un seul clip** ; chaque étape garde son identifiant, son numéro d'étape et son label GSAP (`check-steps.py` inchangé). Sans schéma dans le storyboard, la sortie de `build.py` est identique à l'octet près.
- Nouveau module `scripts/schema_anim.py` (pur, sans E/S) : boîtes dimensionnées d'après le texte (estimation déterministe), flèches clippées aux boîtes, liens courbes, avertissements de mise en page (hors scène, chevauchement, étiquette plus large que le lien), état suivi en Python : le JS ne reçoit que des opérations avec valeurs de départ et d'arrivée, donc la timeline se rejoue à l'identique quel que soit l'ordre des seeks.
- Refusé en mode `incrustation` (illisible dans un quart d'écran). `Primitives(root, figures, refs, schemas=None)` : 4ᵉ argument optionnel, le studio pas à pas ne change pas. `data/schemas.json` est écrit quand le storyboard contient des schémas.
- Documentation : `references/schemas-animes.md` (format, grille, règles de mise en scène), règle 13 du prompt scénario → storyboard. Tests : `scripts/test-schema.py` (logique, build de bout en bout, rendu Chromium avec seeks avant / arrière / au hasard).

## 1.15.0

- **Mode `incrustation` (4ᵉ mode).** La vidéo (webcam plein écran ou screencast OBS) reste plein écran **sous** les visuels, qui sont posés par-dessus dans l'une de 9 zones (`place:` : coin = centre d'un quart d'écran, haut/bas/gauche/droite = centre d'une moitié, centre). Position automatique par défaut : un des deux quarts supérieurs, reproductible (dépend de l'id de l'étape), jamais deux fois de suite la même, avec zones à éviter (`--avoid`, `**Zones à éviter**`). Le storyboard n'y choisit pas la caméra ; les intervalles Cast détectés ajoutent le crop du filet comme en mode webcam. Seules les primitives lisibles dans un quart d'écran sont acceptées (le build refuse les autres avec un message clair). `build.py` lit `**Mode**` (ou `--mode`) ; forme courte `[kind]` dans le format minuté ; `data/steps.json` porte `place` / `place_source`. Les trois autres modes sont inchangés (compositions et index identiques à l'octet près). Tests : `scripts/test-incrustation.py`.
- **Skill découpée en un routeur et 4 sous-skills.** `SKILL.md` garde le routeur et le socle commun ; `modes/auto.md`, `slides.md`, `webcam.md`, `incrustation.md` portent chacun les étapes, les règles et le contexte LLM propres à leur mode, et ne se lisent qu'une fois le mode choisi. `prepare-webcam-context.sh --mode` copie le sous-skill voulu.
- Le mot « incrustation » désignait la webcam en coin : il devient « webcam incrustée » (`pip`) ; « incrustation » est réservé au nouveau mode.
- `video transcribe` remplace `sound transcribe` dans les commandes restantes ; `lint-repo.py` vérifie aussi les chemins `modes/…` ; README aligné sur `SKILL_DIR`.

## 1.14.0

- **Mode Cast (webcam).** Quatrième valeur de `camera` : `cast`, une séquence de screencast OBS affichée en vrai plein écran. OBS pose un filet vert `#00FF00` de 10 px en haut de l'image pendant les screencasts ; **`scripts/detect-cast.py`** le repère dans `cam-clean.mkv` (lecture FFmpeg de la seule bande supérieure, tolérance de couleur, de largeur, d'épaisseur et de durée) et écrit `assets/cast-segments.json` (schéma versionné, intervalles semi-ouverts, métadonnées du média). Il ne découpe ni ne réencode rien. À relancer après chaque nettoyage.
- **Crop au rendu HyperFrames, sans réencodage** : DOM `cam-frame > cam-content > video`. Le wrapper `.cam-content` porte un `scale` + `yPercent` (12 px rognés par défaut, `CAST_CROP_TOP_PX`) ; le cadre `.cam-frame` découpe la vidéo native en preview et l'image injectée par le moteur au rendu. Cadre en 1920 × 1080 sans bordure, coins ni ombre pendant Cast.
- `build.py` fusionne états de base et intervalles Cast en une timeline effective, déterministe, convertie en temps locaux par scène (`--cast-segments`, `--cast-crop-top-px`, `data/camera.json`). `camera: cast` n'est qu'une annotation : elle ne change jamais l'état de base. Sans `cast-segments.json`, la sortie est identique à l'octet près à celle de la 1.13.0.
- Corrections : `clean-posthoc.py` écrit un `voix-posthoc-vN.wav` et un `clean-map-vN.json` par passe (prochain N libre, jamais d'écrasement) ; `build.py` retient le plus grand N numériquement ; `concat-mkv.sh` écrit `start`/`end` cumulés dans `chapters.json` ; `prepare-webcam-context.sh` copie `data-schemas.md` et `webcam.md` (et, avec `--project`, `cast-segments.json` et `transcript.json`) ; `references/webcam.md` décrit le vrai mécanisme du moteur (balise native masquée, image sœur injectée) au lieu d'un canvas.
- HyperFrames : `hyperframes@0.9.15` partout (démo, `SKILL.md`). Démo : scène `i09` (webcam avec Cast).

## 1.13.0

- **`scripts/render_primitive.py`**, module commun de rendu des primitives, importé par `build.py` et `build_studio_anim.py`. Une primitive n'est plus écrite deux fois : le studio affiche le même balisage que la composition finale, et charge `style-joriel.css` + `style-joriel-ext.css`.
- `scenes.json` transporte désormais les paramètres complets de chaque étape (`beats[].params`), donc `versus`, `strike`, `diverge`, `seuil`, `compare3`, `ref-card`… se rendent dans le studio sans second modèle.
- Studio : plus aucun texte codé en dur. Le bloc sources vient des figures ou d'un paramètre `items` ; le libellé du waffle vient du storyboard ; les overlays ne pointent plus vers un dossier personnel par défaut. Un `versus` reste **une** étape (ses deux camps sont dans le même bloc), le nombre de pas du studio ne diverge plus du storyboard.

## 1.12.0

- **Scénario ≠ storyboard ≠ primitives.** `SCENARIO.md` est un texte libre (entrée) ; `assets/storyboard.md` est la mise en scène structurée produite par le LLM ; les primitives sont le vocabulaire visuel figé. Le LLM décide quel passage devient quelle primitive, le code ne décide plus rien.
- **`scripts/build.py`**, builder unique et générique des trois modes : lit le storyboard, écrit `data/figures.json`, `refs.json`, `steps.json`, `design.json`, `scenes.json`, `index.html` et `compositions/iNN.html`. Sans transcript, il utilise les durées estimées ; avec `--transcript`, il recale chaque `cue` sur les mots de la voix. Audio (`assets/voix.wav`) et caméra (`assets/cam-clean.mkv`) détectés automatiquement.
- **`references/storyboard-format.md`** : format canonique lisible par le parser (registres, scènes, étapes, catalogue des `kind`, caméra, format minuté, sorties du build). **`references/scenario-to-storyboard-prompt.md`** : prompt de transformation. **`examples/storyboard.example.md`** : exemple complet et parsable, toutes primitives.
- Renommage : `assets/scenario-hyperframes.md` → `assets/storyboard.md` dans `post-render.py`, `inserts.md`, `test-post-render.sh`, `glossaire.md`, `data-schemas.md`, `README.md`.
- `check-steps.py` réécrit : `--storyboard` (alias `--scenario`), slides et studio optionnels, étapes lues dans `data-step` et les labels GSAP, composition en un ou plusieurs fichiers.
- `build_studio_anim.py` : le kicker tolère un nom de section libre (`KICK.get(...)` avec repli sur la casse de phrase).
- Les builders du studio slides (`build_studio_anim.py`, `build_studio_slides.py`) sont conservés : ils produisent la vue d'enregistrement pas à pas et lisent `data/scenes.json` / `data/figures.json` écrits par `build.py`.

## 1.11.0

- Primitives plus lisibles et mieux animées, vérifiées sur des captures réelles (`hyperframes snapshot`) et `hyperframes check` complet : halos de la couleur du sens, vignette, filet sous le titre, tailles de `count` (28 vh), de `stitle` et de `diverge` alignées sur la spec, `dkw.dim` plus grand dans `versus`, `punch` équilibré et centré, `chip` en pastille, `stamp` à double cadre, `icon` en pastille avec trait dessiné, `strike` plus fin, `cols2` avec filet, `ref-card` avec surlignage par balayage.
- Mouvements : lignes décalées, `enumerate` avec focus-shift, `stamp` qui claque, compteur qui ralentit, `diverge` en séquence, `punch` avec avancée lente, transitions webcam en tween (0,55 s).
- Correctif : le cadre webcam en `off` restait visible (rectangle noir) ; `off` passe l'opacité du cadre à 0. `references/webcam.md` mis à jour.
- Documentation : les blocs CSS et JS recopiés dans `primitives-joriel.md` sont remplacés par un tableau `Mouvements` ; `style-joriel.css` et les compositions de la démo sont la source de vérité.

## 1.10.0

- Inserts : extraits vidéo qui remplacent l'image et le son du master, posés après le rendu. `scripts/post-render.py` télécharge (yt-dlp), découpe, transforme (hauteur du son +5 % à durée constante, rotation de 1° avec zoom) et assemble en un seul graphe ffmpeg. Les coupes sont ancrées sur les étapes du storyboard, pas sur des temps ; `--plan` affiche le texte autour de chaque coupe, `--preview` produit un clip de 11 s par coupe.
- `references/inserts.md` (procédure pour l'agent, manifeste), `examples/inserts.example.json`, `scripts/test-post-render.sh`.
- `SKILL.md` : l'agent propose l'emplacement des inserts au storyboard minuté ; étape 7 « Post-rendu ».

## 1.9.2

- `examples/demo` refait en catalogue : 24 étapes, une primitive ou situation par étape, lorem ipsum, nom affiché à l'écran (`assets/demo-label.css`), 3 étapes au plus par fichier ; plus de voix ni de contenu du projet de maths.
- Corrections issues de `npm run check` : contraste de `.slideno` et `.dkw.dim`, animation de la `ref-card` (`overlapping_gsap_tweens`, `gsap_repeated_fromto_without_baseline`), occlusion voulue de la webcam `full`.
- `references/hyperframes-check.md` (avertissements connus) ; `.step-punch` sur noir pur ; `strike` documenté avec `sline1` / `sline2` comme le CSS ; sections `ref-card` et `ref-shot` ; CSS de `chip`, `stamp`, `dico`, `cols2` déduit de la spec (à valider).

## 1.9.1

Correctifs du refactoring 1.9.0 :
- restauration du contenu du mode slides perdu au déplacement (commandes, previews du deck et de la composition) dans `references/studio-slides.md`, qui reçoit aussi le format des slides ;
- les commandes du mode webcam vont dans `references/webcam.md` ; `SKILL.md` repasse à 257 lignes ;
- les « Règles absolues » retrouvent leur en-tête (elles se retrouvaient sous « Webcam ») ;
- registre des références `Rxx` dans le format du storyboard ; `references/data-schemas.md` complété (champs vérifiés dans le code) ;
- `examples/gabarits/` : exemples JSON de `design.json` à la place d'une page HTML sans objet ;
- `make-placeholders.sh` couvre `assets/references/`, tient en 2 secondes ; `scenario.md` n'a plus de mot-clé `?` ;
- `lint-repo.py` détecte aussi les termes obsolètes (`lyceen`, `Mode A/B`, chemins `~/Code`).

## 1.9.0

Étapes 0 à 5 du refactoring : ordre canonique, chemins paramétrés, autonomie de la démo, allègement de SKILL.md, vocabulaire unique, trous du format, fichiers de dépôt.
