# STORYBOARD — Exemple minimal, mode incrustation

**Source** : SCENARIO.md
**Langage visuel** : references/visual-language-joriel.md
**Mode** : incrustation
**Zones à éviter** : bas-droite
**Format** : 1920×1080 @ 30 fps

## 0. Fiche

- **Thèse** : la dépense éducative a augmenté, les résultats ont baissé.
- **Parties** : bilan

## 1. Registre des chiffres

| ID | Valeur | Label | Source | Statut | Note |
|---|---|---|---|---|---|
| F01 | +57 | % de non-enseignants | MEN-DEPP, 2026 | ok | |

## 4. Scènes

Mode incrustation : la vidéo reste plein écran ; aucune étape n'écrit `camera`. Une étape = une primitive lisible
en surimpression (`kw`, `count`, `strike`, `enumerate`, `stamp`, `define`, `brand`, `chain`, `image`, `ref-shot`,
`ref-card`). Sans `place:`, la position est automatique (un des deux quarts supérieurs, jamais deux fois de suite
la même) ; `place:` choisit l'une des 9 zones.

### I1 — Le chiffre choc [BG-01]

- `I1.1#0` t=0.00 (4.0s) [kw] Le constat
- `I1.1#1` t=4.00 (4.0s) [count] +57 % de non-enseignants
  - figure: F01
  - place: haut-droite
- `I1.1#2` t=8.00 (4.0s) [kw] Au centre de l'écran
  - place: centre
- `I1.1#3` t=12.00 (4.0s) [kw] En bas à gauche
  - place: coin inférieur gauche
