# Schémas Excalidraw (asset à part)

Un schéma qu'on **voit avant de l'intégrer**, qu'on **valide**, qu'on peut **retoucher à la main**, puis qu'on
anime au fil de la voix. Le schéma est un fichier `assets/schemas/Dxx.excalidraw`, un asset de la phase de
préparation ; le storyboard ne fait que le référencer. Les étapes `kind: schema` le pilotent comme les autres
schémas (`show`, `glow`, `focus`, `zoom`, voir `references/schemas-animes.md`).

Ce que ça apporte par rapport au schéma décrit en JSON dans le storyboard : on ne produit plus un graphe à
l'aveugle. Les formes sont libres (rectangle, **rond**, **losange**), **imbriquées** si on veut, les liens ne sont
jamais gênés par l'imbrication, et le fichier s'ouvre dans Excalidraw.

## Le workflow

1. **Produire le fichier.** Au choix : le dessiner dans Excalidraw ; ou le générer depuis une description compacte
   (`scripts/schema-to-excalidraw.py`, ci-dessous) ; ou l'écrire directement (format Excalidraw standard).
2. **Le regarder.** `python3 scripts/excalidraw-preview.py assets/schemas/D01.excalidraw` écrit
   `D01.preview.png` (le schéma **habillé aux couleurs de la vidéo**, 1920 × 1080) et `D01.handles.md` (la liste des
   éléments à citer). Le LLM regarde l'image (outil de lecture d'images), corrige, relance ; toi, tu l'ouvres.
3. **Le retoucher.** Ouvre `D01.excalidraw` dans Excalidraw (excalidraw.com → Ouvrir, ou l'extension de ton éditeur),
   déplace, renomme, ajoute, enregistre **sur le même fichier**, relance l'aperçu. Le fichier est la source : tout ce
   que tu changes est repris. Les flèches générées sont liées aux formes : elles suivent quand tu déplaces.
4. **Le valider**, puis le référencer dans le registre §1c du storyboard :

   ```markdown
   ### D01 — Le Grand Filtre

   - fichier: assets/schemas/D01.excalidraw
   ```

5. Le LLM écrit les étapes à partir de `D01.handles.md` (les noms exacts des éléments).

Si tu retouches le dessin après coup, relance simplement `build.py` : un élément cité dans une étape qui n'existe
plus dans le fichier est signalé par un avertissement (« référence inconnue »).

## Générer le fichier : `schema-to-excalidraw.py`

```bash
python3 scripts/schema-to-excalidraw.py --json assets/schemas/D01.src.json --id D01
python3 scripts/schema-to-excalidraw.py --storyboard assets/storyboard.md --id D01   # bloc JSON du registre §1c
```

Description (JSON), mêmes clés que le schéma JSON de `schemas-animes.md`, plus des formes et des conteneurs :

```json
{"nodes": [
   {"id": "galaxie", "label": "La galaxie", "x": 8, "y": 4.6, "w": 1500, "h": 800, "shape": "ellipse", "cls": "bleu", "valign": "top"},
   {"id": "vie",   "label": "Apparition\nde la vie", "x": 3.5, "y": 4.2, "cls": "vert", "size": "s"},
   {"id": "intel", "label": "Intelligence", "x": 8, "y": 4.2, "cls": "or", "size": "s", "shape": "ellipse"},
   {"id": "filtre", "label": "Le Grand\nFiltre", "x": 8, "y": 7.3, "cls": "rouge", "shape": "diamond", "size": "s"}],
 "edges": [{"from": "vie", "to": "intel"},
           {"from": "intel", "to": "filtre", "cls": "rouge", "curve": 0.25, "label": "durée L"}]}
```

| Clé de nœud | Sens |
|---|---|
| `shape` | `rect` (défaut), `ellipse` (aussi `rond`, `cercle`), `diamond` (aussi `losange`) |
| `x`, `y` | **centre**, grille 16 × 9 de 120 px |
| `w`, `h` | taille en px ; sinon calculée d'après le texte (plus grande pour un rond ou un losange) |
| `valign` | `top` : le texte en haut, pour le **titre d'un conteneur** |
| `cls`, `size`, `label` | comme dans `schemas-animes.md` |

**Imbrication** : un nœud grand posé autour d'autres en est le conteneur (positions et tailles suffisent). Les
conteneurs sont écrits avant ce qu'ils contiennent. Liens : `from`, `to`, `label`, `cls`, `curve`, `dir`.

Le fichier n'est **jamais** écrasé s'il existe (tu l'as peut-être retouché) : `--force` pour le régénérer.

## Dessiner à la main (ou demander au LLM de le faire)

- **Formes** : rectangle, ellipse, losange. **Texte dans une forme** : double-clic sur la forme, tape. **Titre d'un
  conteneur** : un texte libre posé **en haut** d'une forme vide en est le titre (la forme prend ce nom).
- **Liens** : flèches ou lignes, **accrochées** aux formes (le point d'accroche apparaît quand on approche). Une
  flèche non accrochée mais qui touche deux formes est reliée quand même. Texte d'une flèche : double-clic dessus.
- **Cadres** (`frame`, outil F) : un cadre **nommé** regroupe ce qu'il contient : `@nom`.
- **Taille du texte** : le schéma est mis à l'échelle de l'écran 1920 × 1080 (agrandi jusqu'à 3×), pas la police :
  sous ≈ 30 px à l'écran le texte est illisible dans la vidéo, `build.py` et l'aperçu l'**avertissent**. Écrire gros,
  et peu : un mot ou deux par forme.
- **Un texte trop long pour sa forme** rétrécit (jusqu'à 55 %), puis un avertissement demande d'agrandir la forme.
- **Pas pris en charge** (ignorés, avec avertissement) : images, intégrations. **Rotation** ignorée.

## Habillage au thème de la vidéo

Excalidraw dessine en noir, avec un trait « crayonné », sur fond clair. La vidéo est sombre, nette, en Verdana gras :
le schéma est **habillé** à l'affichage, le fichier n'est pas modifié.

| Excalidraw | Dans la vidéo |
|---|---|
| noir, blanc, gris clair | `plain` (blanc) ; gris moyen : `dim` |
| rouge, rose | `rouge` ; orange, jaune : `or` ; vert : `vert` ; cyan, bleu, violet : `bleu` |
| remplissage | teinte du rôle, 22 % ; **transparent** : fond sombre translucide (plus léger pour un conteneur, pour laisser voir son contenu) |
| épaisseur du trait | 3, 4,5 ou 6,5 px |
| trait pointillé d'une forme | forme pointillée |
| flèche **pointillée** | n'apparaît **pas toute seule** avec ses deux formes : à nommer dans `show` (reste pleine à l'écran : son tracé s'anime) |
| police, rugosité | police de la vidéo, trait net |

Le plus simple : **choisir ses couleurs dans la palette d'Excalidraw** (rouge, vert, bleu, orange) ; elles sont
rapprochées du rôle le plus proche.

## Références dans les étapes

| Référence | Désigne |
|---|---|
| `Vie` | l'élément dont le **texte** est « Vie » (casse libre) ; pour un conteneur, son titre |
| `Vie>Intelligence` | le lien entre ces deux éléments, ou le texte de son étiquette |
| `@La galaxie` | la forme **et tout ce qu'elle contient** (formes, textes, liens entre eux) |
| `@passe` | un **cadre** nommé « passe » : ses éléments |
| `gal` | l'identifiant Excalidraw (pour une forme sans texte) |
| `all` | tout |

Les liens accrochés à deux éléments apparaissent **dès que les deux sont visibles**, sauf une flèche **pointillée** (`"manual": true` dans la description compacte) qui se nomme dans `show`. Une flèche libre (sans forme à
un bout) se cite par son identifiant ou son étiquette dans `show`.

## Pas de rendu Excalidraw intégral

Le schéma n'est pas affiché par le moteur d'Excalidraw : ses éléments sont relus et redessinés (formes, textes,
flèches) pour pouvoir être animés un par un et habillés. Ce que le rendu ignore (images, rotation, rugosité,
polices) ne change pas la structure : l'aperçu montre exactement ce que la vidéo montrera.
