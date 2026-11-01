---
name: jo-narration-relecture
description: Évalue un email narratif ou une série complète sur des critères précis (hook, arc, dialectique, signature, heuristiques marketing). Donne une note /10 par critère, par email, et un score global de série. Produit un rapport de relecture avec corrections prioritaires. Use when the user runs /jo-narration-relecture, /jo_narration-relecture, asks to review emails, relecture narrative, or scorer une série.
---

# jo-narration-relecture

Tu évalues la qualité narrative d'un ou plusieurs emails sur des critères précis et objectifs. Tu produis un rapport structuré avec notes, diagnostics et corrections prioritaires.

Vault : `/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel`

Arguments : `{cible}` (fichier ou dossier, requis) · `{mode}` email|serie (auto-détecté) · `{sortie}`.

## Étape 0 — Lire les références avant tout

Lis ces fichiers. Ils définissent les critères :
1. `Business/Lead-magnet/Newsletter/Heuristiques narratives.md` — les 10 piliers marketing (grille A)
2. `Business/Lead-magnet/Newsletter/Prompt rédaction email.md` — les 12 règles + 6 principes narratifs (grille B)
3. `Business/Lead-magnet/Newsletter/Architecture de la série.md` — l'arc global, le fil rouge, les boucles (grille C — série uniquement)
4. Le(s) fichier(s) `{cible}`

---

## Grille A — Heuristiques marketing (par email)

Évalue chaque email sur les 10 piliers de `Heuristiques narratives.md` :

| # | Pilier | Note /5 | Diagnostic (1 ligne) |
|---|---|---|---|
| 1 | Lecteur = héros | | |
| 2 | Douleur précise et viscérale | | |
| 3 | Villain externe identifiable | | |
| 4 | Transformation Before/After visible | | |
| 5 | Mécanisme unique nommé | | |
| 6 | Preuve et spécificité | | |
| 7 | Coût de l'inaction | | |
| 8 | CTA progressif | | |
| 9 | Identité tribale | | |
| 10 | Cohérence niveau de conscience | | |

**Score A = moyenne des 10 notes × 2 → /10**

---

## Grille B — Critères narratifs (par email)

Évalue chaque email sur les critères issus du `Prompt rédaction email.md` :

| # | Critère | Note /5 | Diagnostic (1 ligne) |
|---|---|---|---|
| B1 | **Hook** — scène vraie, vérifiable, cinématographique | | |
| B2 | **Sensorialité** — première phrase = image physique | | |
| B3 | **Tension immédiate** — mystère/problème dès la 2e ligne | | |
| B4 | **Personnage nommé** — pas de "des chercheurs ont montré" | | |
| B5 | **Longueur du hook** — ~150 mots, l'immersion ne coupe pas court | | |
| B6 | **Pont nommé** — explicite ("Ce n'est pas une histoire sur X…") + élément concret de la scène porté dans le monde du lecteur | | |
| B7 | **Arc narratif** — situation → tension → pivot → retour concret | | |
| B8 | **Idée unique** — un seul "aha", pas une liste | | |
| B9 | **Analogie avant concept** — l'image précède le terme technique | | |
| B10 | **Boucle ouverte** — question logique que seul l'épisode suivant résout | | |
| B11 | **Rappel au dispositif** — mention du score/questionnaire | | |
| B12 | **Dialectique** — paires de contraires en équilibre, jamais un seul pôle | | |
| B13 | **Voix** — phrases courtes, une idée/phrase, pas de formules creuses, pas de moralisme | | |
| B14 | **Sources citées** — crédibilité indirecte, intégrées dans le flux | | |
| B15 | **CTA adapté** — cohérent avec la position dans la série (micro-engagement ep.1-4, décoder score ep.5-6, formations ep.7) | | |
| B16 | **Signature martelée** — *origine évolutive → complexification → mismatch → quoi faire* quand pertinent | | |

**Score B = moyenne des 16 notes × 2 → /10**

---

## Score email = (Score A × 0,4) + (Score B × 0,6) → /10

*Pondération : les critères narratifs (B) comptent plus que les heuristiques marketing (A) pour un email de série philosophique. Ajustable si demandé.*

---

## Grille C — Cohérence de série (mode `serie` uniquement)

Évalue l'ensemble des emails comme un tout :

| # | Critère série | Note /5 | Diagnostic (1 ligne) |
|---|---|---|---|
| C1 | **Fil rouge** — le but unique et la signature sont posés en ep.1 et rappelés progressivement | | |
| C2 | **Arc émotionnel** — la progression émotionnelle (curiosité → émerveillement → vertige → pouvoir → cohérence) est perceptible à la lecture enchaînée | | |
| C3 | **Modularité** — chaque email est lisible seul sans connaître les précédents | | |
| C4 | **Boucles fermées** — chaque boucle ouverte trouve sa réponse dans l'épisode suivant | | |
| C5 | **Progression narrative** — pas de redite stérile, chaque épisode ajoute un cran | | |
| C6 | **Cohérence de voix** — même registre, même niveau de familiarité tout au long | | |
| C7 | **Dispositif constant** — le rappel au score/questionnaire est présent sans être mécanique | | |
| C8 | **CTA progressif global** — l'escalade micro-engagement → action finale est logique | | |

**Score C = moyenne des 8 notes × 2 → /10**

---

## Score global série = (moyenne des scores email × 0,6) + (Score C × 0,4) → /10

---

## Format du rapport

Produis le rapport dans cet ordre exact :

### 1. Résumé exécutif (5 lignes max)
- Score global : X/10
- Points forts (2 max)
- Points faibles prioritaires (2 max)
- Recommandation d'action immédiate

### 2. Tableau des scores par email

| Email | Score A /10 | Score B /10 | Score email /10 | Point critique |
|---|---|---|---|---|
| Email-1-… | | | | |
| … | | | | |

*(En mode `email` : un seul email, pas de tableau.)*

### 3. Détail par email

Pour chaque email, les deux grilles complètes (A et B) avec notes et diagnostics.

**Ne développe que les critères avec note ≤ 6/10** — les critères satisfaits (> 7) sont listés en une ligne "✓ satisfait".

### 4. Cohérence de série *(mode `serie` uniquement)*

Grille C complète + score C.

### 5. Corrections prioritaires (classées par impact)

Liste **au maximum 5 corrections** classées par impact décroissant. Pour chaque :
- **Critère** concerné (ex : B6 — Pont nommé)
- **Email(s)** concerné(s)
- **Diagnostic** : ce qui cloche en une phrase
- **Correction concrète** : ce qu'il faudrait écrire à la place (exemple réel, pas une règle abstraite)

**Règle** : les corrections s'appuient sur le matériel existant (corpus, Architecture, Narration synoptique). Pas de slop, pas de suggestions génériques.

---

## Écrire le fichier

Crée le rapport à l'emplacement `{sortie}` (ou auto-généré : même dossier que la cible, `Relecture-[date].md`). Frontmatter :

```yaml
---
type: rapport-relecture
cible: [chemin évalué]
mode: [email | serie]
score-global: [X/10]
date: [date du jour]
statut: relecture-v1
---
```
