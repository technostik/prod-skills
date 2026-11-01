# Changelog

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
