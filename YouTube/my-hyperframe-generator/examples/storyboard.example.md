# STORYBOARD — Exemple minimal (toutes les primitives)

**Source** : SCENARIO.md
**Langage visuel** : references/visual-language-joriel.md
**Mode** : auto
**Durée estimée** : ≈ 1 min 30
**Format** : 1920×1080 @ 30 fps

## 0. Fiche

- **Thèse** : la dépense éducative a augmenté, les résultats ont baissé.
- **Fil rouge** : du chiffre officiel au paradoxe.
- **Parties** : bilan, analyse

## 1. Registre des chiffres

| ID | Valeur | Label | Source | Statut | Note |
|---|---|---|---|---|---|
| F01 | +57 | % de non-enseignants | MEN-DEPP, 2026 | ok | |
| F02 | −250 000 | élèves en dix ans | MEN-DEPP, 2026 | ok | |
| F03 | +2 | % d'enseignants stables | MEN-DEPP, 2026 | verify | source à confirmer |
| F04 | 24 | lycées incendiés | Le Monde, 2026-10-10 | ok | |

### ⚠️ À vérifier

F03 reste `verify` tant que la source n'est pas confirmée.

### ❌ Écartés

| ID | Valeur | Raison |
|---|---|---|
| F99 | 12 | chiffre non sourçable, exclu du film |

## 1b. Registre des références

| ID | Type | Source | Fichier local | Statut |
|---|---|---|---|---|
| R01 | tweet | https://x.com/exemple/status/1 | assets/references/R01-tweet.png | ok |
| R02 | page | https://www.lemonde.fr/exemple | assets/references/R02-page.png | ok |

## 1c. Registre des schémas

### D01 — La chaîne de la dépense

```json
{
  "nodes": [
    {"id": "budget", "label": "Budget", "x": 2.4, "y": 3, "cls": "bleu", "size": "s"},
    {"id": "postes", "label": "Postes", "x": 6.4, "y": 3, "cls": "or", "size": "s"},
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

## 2. Vigilance

Ne pas transformer la corrélation dépense/résultats en causalité unique.

## 3. Correspondance des identifiants

| Notion | Forme | Exemple |
|---|---|---|
| Scène | `I0`…`S99` | `S01` |
| Slide | `SCÈNE.N` | `S01.1` |
| Étape | `SLIDE#k` | `S01.1#2` |

## 4. Scènes

### I0 — Ouverture

- section: bilan · type: title · fond: BG-00 · durée: 10

#### Étapes

- `I0.1#0` · cue « commencer » → **titre du film**
  - kind: title
  - title: "L'école à contre-courant"
  - blocks: [{"sub": "Ce que les chiffres disent vraiment"}]
  - notes: poser le sujet sans dramatiser.

### I1 — Le chiffre choc

- section: bilan · type: numbers · fond: BG-01 · durée: 22 · figures: F01

#### Étapes

- `I1.1#0` · cue « cinquante-sept » → **compteur +57 %**
  - kind: count
  - figure: F01
  - prefix: "+ "
  - suffix: " %"
  - notes: marquer le chiffre, ton calme.

- `I1.1#1` · cue « élèves » → **compteur −250 000 élèves**
  - kind: count
  - figure: F02
  - notes: le contraste avec le chiffre précédent.

- `I1.1#2` · cue « seuil » → **seuil : +57 % contre un repère de 2 %**
  - kind: seuil
  - figure: F01
  - repere: "+2 % · enseignants stables"
  - repere_val: 2
  - sens: bad
  - verdict: "DÉPASSEMENT"
  - sub: "non-enseignants"
  - notes: le repère rend le chiffre lisible.

### S01 — Deux camps

- section: analyse · type: versus · fond: BG-02 · durée: 18 · figures: F03, F04

#### Étapes

- `S01.1#0` · cue « oppresseurs » → **deux camps face à face**
  - kind: versus
  - left: [{"kw": "l'école oppresse", "cls": "dim"}]
  - right: [{"kw": "l'école protège", "cls": "vert"}, {"sub": "un lieu, pas un guichet"}, {"check": true}]
  - recall: left
  - notes: laisser la gauche grisée, insister sur la droite.

- `S01.1#1` · cue « lycées » → **barré : la thèse adverse**
  - kind: strike
  - strike: "les classes sont surchargées"
  - kw: "24 lycées incendiés"
  - cls: "rouge"
  - notes: démolir l'argument sans agressivité.

### S02 — La chaîne

- section: analyse · type: chain · fond: BG-03 · durée: 16

#### Étapes

- `S02.1#0` · cue « donc » → **chaîne causale**
  - kind: chain
  - blocks: [{"kw": "moins d'élèves"}, {"arrow": true}, {"kw": "plus de moyens par élève", "cls": "bleu"}, {"arrow": true}, {"kw": "résultats en baisse", "cls": "rouge"}]
  - notes: une causalité revendiquée, pas une corrélation.

- `S02.1#1` · cue « sinon » → **branche : deux trajectoires**
  - kind: diverge
  - trunk: "Face à l'IA"
  - up: {"kw": "lire, prompter, vérifier", "cls": "vert", "sub": "la compétence reste humaine"}
  - down: {"kw": "copier-coller", "cls": "rouge", "sub": "la compétence disparaît"}
  - notes: montrer les deux issues.

### S03 — Les données

- section: analyse · type: bars · fond: BG-04 · durée: 18 · figures: F02, F03

#### Étapes

- `S03.1#0` · cue « barres » → **barres comparatives**
  - kind: bars
  - items: [{"label": "élèves", "display": "−250 000", "value": 250, "cls": "bleu"}, {"label": "enseignants", "display": "+2 %", "value": 2, "cls": "vert"}, {"label": "non-enseignants", "display": "+57 %", "value": 57, "cls": "rouge"}]
  - max: 250
  - label: "Évolution sur dix ans"
  - notes: échelle commune, unités hétérogènes signalées.

- `S03.1#1` · cue « tableau » → **trois séries hétérogènes**
  - kind: compare3
  - rows: [{"icon": "trend-down", "kw": "−250 000 élèves", "cls": "bleu", "sub": "effectifs en baisse"}, {"icon": "arrow-r", "kw": "≈ stables", "cls": "bleu", "sub": "+2 % · enseignants"}, {"icon": "trend-up", "kw": "+57 %", "cls": "rouge", "sub": "non-enseignants"}]
  - verdict: "DÉPASSEMENT"
  - notes: le tableau qui tue l'argument.

### S04 — La source et la sortie

- section: analyse · type: cards · fond: BG-00 · durée: 20 · refs: R02

#### Étapes

- `S04.1#0` · cue « article » → **carte de source**
  - kind: ref-card
  - ref: R02
  - source: "Le Monde · 8 octobre 2026"
  - author: "Prénom Nom"
  - title: "L'école à contre-courant"
  - quote: "Les moyens augmentent, les résultats reculent."
  - hl: "les résultats reculent"
  - url: "lemonde.fr/exemple"
  - notes: la source prime sur le commentaire.

- `S04.1#1` · cue « conclusion » → **punchline**
  - kind: punch
  - text: "Moins d'idéologie. Plus de résultats."
  - camera: off
  - notes: laisser le silence après.

### S05 — Où va l'argent

- section: analyse · type: cards · fond: BG-00 · durée: 28

#### Étapes

- `S05.1#0` · cue « budget » → **le budget, puis les postes**
  - kind: schema
  - schema: D01
  - show: ["budget", "postes"]
  - notes: poser le point de départ.

- `S05.1#1` · cue « classe » → **l'argent arrive-t-il en classe ?**
  - kind: schema
  - show: ["classe", "postes>classe"]
  - zoom: ["postes", "classe"]
  - notes: le « ? » est la question de la vidéo.

- `S05.1#2` · cue « résultat » → **le niveau, isolé**
  - kind: schema
  - show: ["niveau", "classe>niveau"]
  - zoom: "all"
  - focus: ["classe", "niveau"]
  - notes: on revient à la vue d'ensemble, on isole la fin de chaîne.

- `S05.1#3` · cue « au total » → **tout reprend sa place**
  - kind: schema
  - focus: "all"
  - glow: ["postes>classe"]
  - notes: rétablir, puis souligner le maillon douteux.

## 5. Fonds

| ID | Description | Scènes |
|---|---|---|
| BG-00 | noir + voile (défaut, punchlines) | I0, S04, S05 |
| BG-01 | salle de classe vide | I1 |
| BG-02 | cour d'école | S01 |
| BG-03 | couloir | S02 |
| BG-04 | tableau noir | S03 |
