# Catalogue des primitives (démo)

Chaque primitive ou situation est montrée **une seule fois**, avec du lorem ipsum, et son nom s'affiche en haut à droite (calque `assets/demo-label.css`, propre à la démo). Le repère `I2.1#0` en bas à gauche est l'identifiant de l'étape (`.slideno`), repris dans `scenario.md`.

Pour corriger une primitive : repère son nom à l'écran, retrouve l'étape dans le tableau, modifie le balisage dans la composition et le style dans `assets/style-joriel.css`.

## Lancer

```bash
bash scripts/make-placeholders.sh   # médias factices (FFmpeg) pour les fichiers que tu n'as pas fournis
npm run lint                        # rapide, sans navigateur : doit afficher 0 erreur, 0 avertissement
npm run check                       # Node ≥ 22, Chrome, accès réseau
npm run dev                         # aperçu
```

## Assets

Tous sont ignorés par git. `make-placeholders.sh` crée un aplat à la place de chaque fichier manquant (et ne touche pas à ceux que tu as déjà).

| Fichier | À fournir | Spécifications |
|---|---|---|
| `assets/bg/BG-00.jpg` | fond par défaut (réseau neuronal blanc sur noir) | 1920×1080, sombre |
| `assets/bg/BG-01.jpg` | un second fond de scène, différent | 1920×1080, sombre, sans texte, logo ni personne identifiable |
| `assets/images/image-plein-ecran.jpg` | image plein écran | 1920×1080, sans texte |
| `assets/references/ref-capture.png` | capture d'une page web | 1920×1080, n'importe laquelle |
| `assets/cam-clean.mkv` | toi face caméra | 16:9, au moins 16 s (30 s conseillé), le son n'est pas utilisé |

Si tu as encore les fichiers du projet de maths, depuis `examples/demo/` :

```bash
mkdir -p assets/bg assets/images assets/references
cp <ancien>/assets/bg/BG-00.jpg assets/bg/BG-00.jpg
cp <ancien>/assets/images/image-02-formules-mathematiques-tableau-noir-1920x1080.jpg assets/bg/BG-01.jpg
cp <ancien>/assets/images/copernican-1920x1080.jpg assets/images/image-plein-ecran.jpg
cp <ancien>/assets/references/R09-silicon-reckoner.png assets/references/ref-capture.png
cp <ancien>/assets/cam-clean.mkv assets/cam-clean.mkv     # les 30 premières secondes suffisent
```

## Primitives et situations montrées

| Étape | Primitive / situation | Fichier | Balisage |
|---|---|---|---|
| `I0.1#0` | step | `compositions/i00.html` | dépôt d'origine |
| `I0.1#1` | kw | `compositions/i00.html` | dépôt d'origine |
| `I0.1#2` | sub | `compositions/i00.html` | dépôt d'origine |
| `I1.1#0` | enumerate | `compositions/i01.html` | dépôt d'origine |
| `I1.1#1` | enumerate | `compositions/i01.html` | dépôt d'origine |
| `I1.1#2` | enumerate | `compositions/i01.html` | dépôt d'origine |
| `I2.1#0` | strike | `compositions/i02.html` | dépôt d'origine |
| `I2.1#1` | stamp | `compositions/i02.html` | déduit de la spec (à valider) |
| `I2.1#2` | chip | `compositions/i02.html` | déduit de la spec (à valider) |
| `I3.1#0` | count (bignum) | `compositions/i03.html` | dépôt d'origine |
| `I3.1#1` | cols2 | `compositions/i03.html` | déduit de la spec (à valider) |
| `I4.1#0` | icon | `compositions/i04.html` | déduit de la spec (à valider) |
| `I4.1#1` | check / cross | `compositions/i04.html` | déduit de la spec (à valider) |
| `I4.1#2` | arrow (darr) | `compositions/i04.html` | dépôt d'origine |
| `I5.1#0` | versus | `compositions/i05.html` | dépôt d'origine |
| `I5.1#1` | diverge | `compositions/i05.html` | dépôt d'origine |
| `I5.2#0` | punch | `compositions/i05.html` | dépôt d'origine |
| `I6.1#0` | fond de scène (BG-01) | `compositions/i06.html` | dépôt d'origine |
| `I6.1#1` | image plein écran | `compositions/i06.html` | dépôt d'origine |
| `I7.1#0` | ref-card | `compositions/i07.html` | dépôt d'origine |
| `I7.1#1` | ref-shot | `compositions/i07.html` | dépôt d'origine |
| `I8.1#0` | webcam · off | `compositions/i08.html` | dépôt d'origine |
| `I8.1#1` | webcam · pip | `compositions/i08.html` | dépôt d'origine |
| `I8.1#2` | webcam · full | `compositions/i08.html` | dépôt d'origine |

## Primitives décrites mais absentes de la démo

Leur balisage n'existe pas dans le dépôt, je ne l'ai pas inventé : `bar` / `bars`, `seuil`, `compare3`, `define` (morph vers `versus`), `brand` (SVG `thesvg`), `doc-crop`, `ref-iframe`, `nl`. Pour les ajouter, il suffit de fournir le HTML et le CSS que tu utilises dans ton projet.

Les lignes marquées « déduit de la spec » (`cols2`, `stamp`, `chip`, `icon`, `check / cross`) ont un balisage documenté dans `references/primitives-joriel.md`, mais leur CSS n'existait pas : il est déduit de `references/visual-language-joriel.md` §3, signalé « à valider » à l'écran.
