# Storyboard minuté — catalogue des primitives (30 étapes, 12 scènes, 162.50 s)

> Format minuté historique, conservé comme trace du catalogue. Le format canonique, lisible par `scripts/build.py`, est `references/storyboard-format.md` ; exemple complet : `examples/storyboard.example.md`.
>
> Les scènes `I10` et `I11` montrent **un même schéma qui se déploie sur deux compositions** : le schéma est déclaré une fois dans le registre §1c, `I10` en construit la première moitié, `I11` reprend l'état déjà affiché et le termine.

Une étape = une primitive ou une situation, démontrée une seule fois. Texte : lorem ipsum. Le nom de la primitive est affiché à l'écran par `assets/demo-label.css`.

## 1c. Registre des schémas

### D01 — La chaîne de la dépense

```json
{
  "nodes": [
    {"id": "budget", "label": "Budget", "x": 2.6, "y": 3, "cls": "bleu", "size": "s"},
    {"id": "postes", "label": "Postes", "x": 6.6, "y": 3, "cls": "or", "size": "s"},
    {"id": "classe", "label": "Heures de cours", "x": 11.2, "y": 3, "cls": "vert", "size": "s"},
    {"id": "niveau", "label": "Niveau des élèves", "x": 11.2, "y": 6.6, "cls": "rouge", "size": "m"}
  ],
  "edges": [
    {"from": "budget", "to": "postes"},
    {"from": "postes", "to": "classe", "label": "?", "manual": true},
    {"from": "classe", "to": "niveau", "cls": "rouge", "manual": true}
  ]
}
```

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
- `I10.1#0` t=136.50 (6.0s) [off/schema] Budget puis Postes
  - schema: D01
  - show: ["budget", "postes"]
- `I10.1#1` t=142.50 (6.0s) [off/schema] Heures de cours, puis le lien « ? »
  - show: ["classe", "postes>classe"]
  - zoom: ["postes", "classe"]

### I11 — Schéma sur deux compositions (2/2) [BG-00]
- `I11.1#0` t=148.50 (7.0s) [off/schema] Niveau des élèves, le schéma continue
  - schema: D01
  - show: ["niveau", "classe>niveau"]
  - zoom: "all"
  - focus: ["classe", "niveau"]
- `I11.1#1` t=155.50 (7.0s) [off/schema] Tout reprend sa place
  - focus: "all"
  - glow: ["postes>classe"]
