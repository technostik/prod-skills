# Catalogue des primitives (démo)

Chaque primitive ou situation est montrée **une seule fois**, avec du lorem ipsum, et son nom s'affiche en haut à droite (calque `assets/demo-label.css`, propre à la démo). Le repère `I2.1#0` en bas à gauche est l'identifiant de l'étape (`.slideno`), repris dans `storyboard.md`.

Pour corriger une primitive : repère son nom à l'écran, retrouve l'étape dans le tableau, modifie le balisage dans la composition et le style dans `assets/style-joriel.css`.

## Lancer

```bash
bash scripts/make-placeholders.sh   # médias factices (FFmpeg) pour les fichiers que tu n'as pas fournis (images, caméra, musiques)
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
| `assets/cam-clean.mkv` | toi face caméra | 16:9, au moins 22 s (30 s conseillé), le son n'est pas utilisé |

`assets/style-joriel-ext.css` n'est **pas** ignoré : il porte les styles des primitives rendues par `build.py` qui ne sont pas dans `style-joriel.css` (dont les schémas animés, `.sch-*`). C'est le même fichier que `scripts/build.py` écrit dans un projet.

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
| `I9.1#0` | webcam · pip avant Cast | `compositions/i09.html` | dépôt d'origine |
| `I9.1#1` | webcam · cast (plein écran, crop du filet OBS) | `compositions/i09.html` | mode Cast de `scripts/build.py` |
| `I10.1#0` | schéma · 1/2 (Budget, Postes) | `compositions/i10.html` | `scripts/build.py` + `schema_anim.py` |
| `I10.1#1` | schéma · 1/2 (Heures de cours, zoom) | `compositions/i10.html` | `scripts/build.py` + `schema_anim.py` |
| `I11.1#0` | schéma · 2/2 (reprise de l'état, Niveau) | `compositions/i11.html` | `scripts/build.py` + `schema_anim.py` |
| `I11.1#1` | schéma · 2/2 (focus « all », glow) | `compositions/i11.html` | `scripts/build.py` + `schema_anim.py` |
| `I12.1#0` | schéma **Excalidraw** · le rond « Écosystème » (+ musique M01, la montée) | `compositions/i12.html` | `scripts/build.py` + `excalidraw_anim.py` |
| `I12.1#1` | schéma Excalidraw · rectangle et cercle **imbriqués**, zoom `@Équipe` | `compositions/i12.html` | `scripts/build.py` + `excalidraw_anim.py` |
| `I12.1#2` | schéma Excalidraw · **losange** « Décision », le lien traverse l'imbrication, glow | `compositions/i12.html` | `scripts/build.py` + `excalidraw_anim.py` |
| `I12.1#3` | schéma Excalidraw · rectangle « Résultat » et flèche « oui » | `compositions/i12.html` | `scripts/build.py` + `excalidraw_anim.py` |
| `I12.1#4` | schéma Excalidraw · **flèche pointillée** montrée à la main, `focus` | `compositions/i12.html` | `scripts/build.py` + `excalidraw_anim.py` |
| `I12.1#5` | schéma Excalidraw · `focus` « all », glow `@Équipe` (+ musique M02, la conclusion) | `compositions/i12.html` | `scripts/build.py` + `excalidraw_anim.py` |

Le même schéma `D01` (registre §1c de `storyboard.md`) **se déploie sur deux compositions** : `i10` construit sa première moitié, `i11` retrouve les nœuds déjà affichés et termine le schéma. C'est le cas à regarder pour vérifier la persistance de l'état d'une scène à l'autre.

## Schéma Excalidraw, musique et shorts (`I12`)

**Le schéma** `D02` est un **asset à part** : `assets/schemas/D02.excalidraw`, référencé dans le registre §1c du storyboard par `- fichier: assets/schemas/D02.excalidraw`. Un **rond** (« Écosystème ») contient un **rectangle** (« Équipe ») qui contient un **cercle** (« Idée ») ; un **losange** (« Décision »), un rectangle (« Résultat ») et trois **flèches** : « Idée → Décision » traverse deux bords sans être gênée, « Décision → Résultat » (« oui ») et la boucle « Décision → Équipe » (« non »), **pointillée**, donc montrée à la main (`show: ["Décision>Équipe"]`). Les étapes construisent le schéma un élément à la fois (`show`), mettent en relief (`glow`), isolent (`focus`) et cadrent (`zoom: ["@Équipe"]`).

Le workflow d'un schéma (`references/schemas-excalidraw.md`), avec les fichiers de `assets/schemas/` :

| Fichier | Rôle |
|---|---|
| `D02.src.json` | la description compacte (nœuds, formes, liens) |
| `D02.excalidraw` | le schéma : généré par `scripts/schema-to-excalidraw.py`, **ouvrable et retouchable dans Excalidraw** ; c'est lui qui fait foi |
| `D02.preview.png` | le schéma **habillé aux couleurs de la vidéo** (`scripts/excalidraw-preview.py`) : à regarder avant de valider |
| `D02.handles.md` | les éléments à citer dans `show`, `glow`, `focus`, `zoom` (lu par le LLM qui écrit le storyboard) |
| `D02.validated` | le tampon de validation (`scripts/prepare.py validate-schema D02`) : retouché ensuite, le schéma redevient « à valider » |

```bash
python3 scripts/schema-to-excalidraw.py --json assets/schemas/D02.src.json --id D02 --force   # régénère (jamais sans --force)
python3 scripts/excalidraw-preview.py assets/schemas/D02.excalidraw                             # aperçu + liste des éléments
python3 scripts/prepare.py validate-schema D02
```

**La musique** : le registre §1d du storyboard déclare deux musiques et `I12.1#0` / `I12.1#5` les posent (`music: M01` jusqu'à `I12.1#4`, `music: M02` jusqu'à la fin de la scène). Elles soulignent la montée puis la conclusion ; ce n'est pas un fond continu (17 % de la démo). `build.py` écrit `data/music.json` (committé ici pour l'exemple). Les fichiers audio ne sont pas dans le dépôt : `scripts/make-placeholders.sh` crée des **musiques factices** (une nappe synthétique, pour que le mixage tourne) ; les vraies se génèrent avec `python3 scripts/make-music.py` (CLI `sound` de fast-market), puis `python3 scripts/mix-music.py` les mixe sous la voix du master rendu (`references/music.md`).

**Les shorts** : le §6 du storyboard propose trois séquences de 20 à 26 s ; `build.py` les écrit dans `data/shorts_segments.json`, au format de `video short-extractor` : `video short-extractor renders/final.mp4 --segments data/shorts_segments.json --layout fit-blur --output-dir shorts/` (`references/shorts.md`).

Régénérer `compositions/i12.html` : `build.py` sur `storyboard.md` (copier `i12.html`, puis y ajouter le calque `demo-label`, comme pour `i10` et `i11`).

## Primitives décrites mais absentes de la démo

Leur balisage n'existe pas dans le dépôt, je ne l'ai pas inventé : `bar` / `bars`, `seuil`, `compare3`, `define` (morph vers `versus`), `brand` (SVG `thesvg`), `doc-crop`, `ref-iframe`, `nl`. Pour les ajouter, il suffit de fournir le HTML et le CSS que tu utilises dans ton projet.

Le `kind: schema` n'est pas dans cette liste : il est rendu par `scripts/schema_anim.py` (schéma JSON, démonstration sur deux compositions en `i10` / `i11`) et `scripts/excalidraw_anim.py` (schéma Excalidraw, en `i12`) (styles dans `assets/style-joriel-ext.css`).

Les lignes marquées « déduit de la spec » (`cols2`, `stamp`, `chip`, `icon`, `check / cross`) ont un balisage documenté dans `references/primitives-joriel.md`, mais leur CSS n'existait pas : il est déduit de `references/visual-language-joriel.md` §3, signalé « à valider » à l'écran.
