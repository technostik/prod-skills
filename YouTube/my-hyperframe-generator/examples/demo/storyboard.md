# Storyboard minuté — catalogue des primitives (36 étapes, 13 scènes, 204.50 s)

> Format minuté historique, conservé comme trace du catalogue. Le format canonique, lisible par `scripts/build.py`, est `references/storyboard-format.md` ; exemple complet : `examples/storyboard.example.md`.
>
> Les scènes `I10` et `I11` montrent **un même schéma Excalidraw qui se déploie sur deux compositions** : le schéma `D01` est **décrit en JSON dans le registre §1c** (comme avant) ; la ligne `- fichier: assets/schemas/D01.excalidraw` à côté du bloc en fait un schéma Excalidraw : le fichier est **généré automatiquement depuis le bloc** au premier build (intermédiaire qu'on peut ensuite retoucher à la main), avec **un conteneur imbriqué** (l'« École » contient « Postes » et « Heures de cours », et le lien « Budget → Postes » en traverse le bord) et **un cercle** (« Niveau des élèves »). `I10` en construit la première moitié, `I11` reprend l'état déjà affiché et le termine.
>
> La scène `I12` montre **un schéma Excalidraw** : un fichier `assets/schemas/D02.excalidraw` (asset à part, regardé et validé avant d'être intégré) avec des **formes imbriquées** (un rond qui contient un rectangle qui contient un cercle), un **losange**, des **flèches** qui traversent l'imbrication et une flèche pointillée montrée à la main, construits un élément à la fois. Elle porte aussi deux **musiques** (registre §1d) : une montée, puis la conclusion. Le §6 propose **trois shorts de promotion**.

Une étape = une primitive ou une situation, démontrée une seule fois. Texte : lorem ipsum. Le nom de la primitive est affiché à l'écran par `assets/demo-label.css`.

## 1c. Registre des schémas

### D01 — La chaîne de la dépense (décrit en JSON ; l'Excalidraw est son intermédiaire)

```json
{
  "nodes": [
    {"id": "Budget", "label": "Budget", "x": 1.417, "y": 5.0, "w": 240, "h": 140, "shape": "rect", "cls": "bleu", "size": "s"},
    {"id": "École", "label": "École", "x": 7.333, "y": 4.5, "w": 960, "h": 520, "shape": "rect", "cls": "plain", "valign": "top"},
    {"id": "Postes", "label": "Postes", "x": 5.0, "y": 5.0, "w": 300, "h": 140, "shape": "rect", "cls": "or", "size": "s"},
    {"id": "Heures de cours", "label": "Heures de cours", "x": 9.083, "y": 5.0, "w": 480, "h": 140, "shape": "rect", "cls": "vert", "size": "s"},
    {"id": "Niveau des élèves", "label": "Niveau\ndes élèves", "x": 14.0, "y": 5.0, "w": 340, "h": 340, "shape": "ellipse", "cls": "rouge", "size": "s"}
  ],
  "edges": [
    {"from": "Budget", "to": "Postes", "cls": "bleu"},
    {"from": "Postes", "to": "Heures de cours", "label": "?", "manual": true},
    {"from": "Heures de cours", "to": "Niveau des élèves", "cls": "rouge", "manual": true}
  ]
}
```

- fichier: assets/schemas/D01.excalidraw

### D02 — Écosystème : formes imbriquées

- fichier: assets/schemas/D02.excalidraw

## 1d. Registre des musiques

| ID | Rôle | Prompt | Durée | Volume | Seed |
|---|---|---|---|---|---|
| M01 | montée | epic cinematic orchestral build, low strings ostinato, rising brass and timpani, tension growing, 110 bpm, no vocals | 14 | 0.45 | 11 |
| M02 | conclusion | epic orchestral finale, full strings and brass, slow powerful resolution, hopeful, big timpani, no vocals | | 0.5 | 12 |

## 4. Scènes

### I0 — Structure et texte [BG-00]
- `I0.1#0` t=0.00 (5.0s) [off/step] Consectetur adipiscing
- `I0.1#1` t=5.00 (6.0s) [off/kw] Lorem Ipsum Dolor Sit Amet Elit
- `I0.1#2` t=11.00 (5.0s) [off/sub] Lorem ipsum

### I1 — Listes [BG-00]
- `I1.1#0` t=16.00 (4.0s) [off/enumerate] Lorem ipsum
- `I1.1#1` t=20.00 (4.0s) [off/enumerate] Consectetur
- `I1.1#2` t=24.00 (4.0s) [off/enumerate] Sed do eiusmod

### I2 — Mises en valeur [BG-00]
- `I2.1#0` t=28.00 (5.0s) [off/strike] Lorem ipsum dolor
- `I2.1#1` t=33.00 (5.0s) [off/stamp] Lorem ipsum
- `I2.1#2` t=38.00 (5.0s) [off/chip] Lorem 00 000 ipsum 00 %

### I3 — Chiffres et colonnes [BG-00]
- `I3.1#0` t=43.00 (5.0s) [off/count] 1 234
- `I3.1#1` t=48.00 (6.0s) [off/cols2] Lorem Ipsum Dolor Sit amet Consectetur Adipiscing

### I4 — Symboles et flèches [BG-00]
- `I4.1#0` t=54.00 (5.0s) [off/icon] lorem ipsum
- `I4.1#1` t=59.00 (5.0s) [off/check/cross] Lorem ipsum / Dolor sit amet
- `I4.1#2` t=64.00 (6.0s) [off/arrow] Lorem → Ipsum → Dolor

### I5 — Gabarits et punchline [BG-00]
- `I5.1#0` t=70.00 (6.0s) [off/versus] Lorem ipsum / Dolor sit amet
- `I5.1#1` t=76.00 (6.0s) [off/diverge] Lorem ipsum
- `I5.2#0` t=82.00 (3.5s) [off/punch] Lorem ipsum dolor sit amet.

### I6 — Fonds et images [BG-01]
- `I6.1#0` t=85.50 (6.0s) [off/fond] Lorem ipsum
- `I6.1#1` t=91.50 (6.0s) [off/image] [image] Lorem ipsum

### I7 — Références [BG-00]
- `I7.1#0` t=97.50 (7.0s) [off/ref-card] Dolor Sit — Lorem ipsum
- `I7.1#1` t=104.50 (5.0s) [off/ref-shot] [capture] ref-capture.png

### I8 — Webcam (situations) [BG-00]
- `I8.1#0` t=109.50 (5.0s) [off/webcam] Lorem ipsum
- `I8.1#1` t=114.50 (5.0s) [pip/webcam] Lorem ipsum
- `I8.1#2` t=119.50 (6.0s) [full/webcam] Lorem ipsum

### I9 — Webcam (Cast) [BG-00]
- `I9.1#0` t=125.50 (5.0s) [pip/webcam] Lorem ipsum
- `I9.1#1` t=130.50 (6.0s) [cast/webcam] Lorem ipsum

### I10 — Schéma sur deux compositions (1/2) [BG-00]
- `I10.1#0` t=136.50 (6.0s) [off/schema] Budget, puis l'école qui contient les postes
  - schema: D01
  - show: ["Budget", "École", "Postes"]
- `I10.1#1` t=142.50 (6.0s) [off/schema] Heures de cours, puis le lien « ? »
  - show: ["Heures de cours", "Postes>Heures de cours"]
  - zoom: ["@École"]

### I11 — Schéma sur deux compositions (2/2) [BG-00]
- `I11.1#0` t=148.50 (7.0s) [off/schema] Niveau des élèves (le cercle), le schéma continue
  - schema: D01
  - show: ["Niveau des élèves", "Heures de cours>Niveau des élèves"]
  - zoom: "all"
  - focus: ["Heures de cours", "Niveau des élèves"]
- `I11.1#1` t=155.50 (7.0s) [off/schema] Tout reprend sa place
  - focus: "all"
  - glow: ["Postes>Heures de cours"]

### I12 — Schéma Excalidraw : formes, imbrication, flèches [BG-00]
- `I12.1#0` t=162.50 (6.0s) [off/schema] L'écosystème : un rond qui contiendra tout le reste
  - schema: D02
  - show: ["Écosystème"]
  - music: M01
  - music_until: I12.1#4
- `I12.1#1` t=168.50 (7.0s) [off/schema] L'équipe (rectangle) et son idée (cercle), imbriqués
  - show: ["Équipe", "Idée"]
  - zoom: ["@Équipe"]
- `I12.1#2` t=175.50 (7.0s) [off/schema] Le losange « Décision » : le lien traverse l'imbrication
  - show: ["Décision"]
  - zoom: "all"
  - glow: ["Idée>Décision"]
- `I12.1#3` t=182.50 (7.0s) [off/schema] Le résultat, au bout de la flèche « oui »
  - show: ["Résultat"]
- `I12.1#4` t=189.50 (7.0s) [off/schema] La boucle « non » : une flèche pointillée, montrée à la main
  - show: ["Décision>Équipe"]
  - focus: ["Décision", "Équipe", "Décision>Équipe"]
- `I12.1#5` t=196.50 (8.0s) [off/schema] Tout reprend sa place, relief sur l'équipe
  - focus: "all"
  - glow: ["@Équipe"]
  - music: M02
  - music_until: I12

## 6. Shorts

Trois séquences percutantes (3 minutes au plus chacune) pour la promo de la vidéo : une accroche dans les trois premières secondes, une chute, des idées différentes.

| ID | Titre | Début | Fin | Pourquoi |
|---|---|---|---|---|
| SH01 | Un schéma qui se construit, une forme après l'autre | I12.1#0 | I12.1#2 | la construction progressive, imbrication comprise |
| SH02 | Une boucle de retour montrée à la main | I12.1#3 | I12.1#5 | le moment fort, la flèche pointillée |
| SH03 | Un schéma qui se déploie sur deux compositions | I10.1#0 | I11.1#1 | la reprise d'état d'une scène à l'autre |
