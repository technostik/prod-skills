# Changelog

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
