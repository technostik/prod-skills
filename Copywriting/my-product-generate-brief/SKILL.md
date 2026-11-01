---
name: my-product-generate-brief
description: Analyse un produit — un document unique (livre, ebook) ou un répertoire (formation, programme) — et en extrait un brief-produit.md contenant toute la matière nécessaire au copywriting (promesse, douleurs, villain, mécanisme unique, before/after, preuves réelles, banque de hooks, objections, offre, CTA). Tout est sourcé sur le produit, jamais inventé. Use when the user runs /jo-brief-produit, /jo_brief-produit, asks for a brief produit, extraire un brief, or copywriting source material.
---

# jo-brief-produit

Tu analyses **un produit** et tu en extrais un **brief de copywriting complet et sourcé**. Le brief est la matière première qu'ingèrent ensuite les skills de copy (email de vente, narration). Tu n'écris pas de copy ici — tu prépares le terrain.

Vault : `/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel`

Arguments : `{produit}` (chemin fichier ou dossier, requis) · `{sortie}` (optionnel).

> **Règle cardinale : tu extrais, tu n'inventes pas.** Chaque élément du brief renvoie à un endroit précis du produit. Ce qui manque n'est pas comblé : c'est consigné en lacune (Étape 4). Un brief lacunaire avec des questions vaut mieux qu'un brief complet avec du générique.

## Étape 0 — Lire les références avant tout

1. `Business/Copywriting/00 - Synthèse copywriting.md` — **la structure du brief (§4.0) et les techniques que le brief doit nourrir.**
2. `Business/Reference/reference-profil.md` (ou `Business/Profil/profil-resume.md`) — **le réglage profil** : légitimité indirecte (preuves = médailles réelles + sources scientifiques + témoignages réels), villain = système jamais des personnes, lignes rouges, voix dialectique.

Ces deux fichiers définissent *quoi* extraire et *comment* le cadrer. Ne réétablis pas leurs principes — applique-les.

## Étape 1 — Cartographier le produit

Détecte d'abord si `{produit}` est un **fichier** ou un **dossier**.

- **Dossier (formation, programme)** : liste la structure. Repère les fichiers porteurs de matière copy : programme/synoptique, fiches de contenu, slides, **témoignages**, **concurrence**, intro/bienvenue, ebook/lead-magnet associé, notes de copywriting déjà présentes. Lis en priorité ceux-là.
- **Fichier unique (livre, ebook)** : s'il est volumineux, lis d'abord sa **structure** (table des matières, titres), puis lis les sections riches en **histoires, preuves, promesses, douleurs**. Tu n'as pas besoin de tout le texte — tu as besoin de la matière de copywriting.

Note explicitement ce que tu as lu intégralement vs survolé (ça conditionne la confiance du brief).

## Étape 2 — Extraire chaque champ, en sourçant

Remplis chaque section du brief (template plus bas). **Pour chaque affirmation, indique d'où elle vient** (fichier + section/page). Quand un champ n'a pas de matière dans le produit, ne l'invente pas : marque `⚠ à compléter` et reporte-le en Étape 4.

Ce qu'il faut chercher, champ par champ :
- **Promesse / transformation** : la phrase qui dit ce que le client devient.
- **Douleurs** : le langage réel du problème (mots du produit, pas paraphrase lisse). Précises et viscérales.
- **Villain** : le système/mécanisme responsable du problème.
- **Mécanisme unique** : ce que ce produit fait et qu'on ne trouve pas ailleurs (méthode nommée, angle propriétaire).
- **Before / After** : l'état avant vs après, le plus concret possible.
- **Preuves** : médailles de l'auteur, sources/études citées, **témoignages réels** présents dans le produit.
- **Objections** : ce qui retient d'acheter (souvent visible dans les FAQ, critiques, intro).
- **Hooks** : scènes, histoires, anecdotes, expériences déjà présentes dans le produit — sépare vérifiables et vécues.
- **Offre** : format, prix, échéance, garantie, bonus.

## Étape 3 — Appliquer le réglage profil

Avant d'écrire, passe le brief au filtre du profil :
- **Villain = système** (captologie, bureaucrature, mismatch, méthode concurrente inefficace), **jamais** des personnes ou des groupes nommés pour ce qu'ils sont.
- **Preuves = réel uniquement.** Médailles réelles + sources scientifiques + témoignages réels. Si tu croises un chiffre ou un témoignage, vérifie qu'il existe dans le produit. **Aucune invention, aucune exagération.**
- **Hooks : deux piles.** *Vérifiables* (historique/scientifique → audience froide, légitimité indirecte) et *vécus* (anecdotes réelles de l'auteur → audience chaude).
- **Signaler** tout matériel qui frôle une ligne rouge (hype, moralisme, prosélytisme, écologie catastrophiste, attaque de personnes), pour que le copywriter l'évite ou le retraite.

## Étape 4 — Lacunes & questions

Liste ce qui **manque** pour un copy complet et formule-le en **questions à l'auteur**. C'est la partie anti-slop : elle rend le brief honnête et actionnable.

## Étape 5 — Écrire le brief

Écris dans `{sortie}` si précisé. Sinon : `brief-produit.md` à la racine du dossier `{produit}` (ou à côté du fichier si produit unique).

Frontmatter obligatoire :

```yaml
---
type: brief-produit
produit: [chemin du produit analysé]
date: [date du jour]
statut: brief-v1
regime-cible: [nurture | vente | les deux]
confiance: [haute | moyenne | partielle — selon ce qui a été lu vs survolé]
---
```

Puis le corps, dans cet ordre exact :

```markdown
## 0. Identité produit
Nom · type (livre / formation / …) · format · prix · emplacement · statut.

## 1. Promesse centrale
La transformation, en une phrase. → source

## 2. Public cible & niveau de conscience
Qui · froid / problem-aware / solution-aware / product-aware · identité tribale. → source

## 3. Douleurs (précises, langage réel)
| Douleur | Formulation réelle (mots du produit) | Source |
|---|---|---|

## 4. Villain externe (système, jamais des personnes)
Le mécanisme/système responsable. → source

## 5. Mécanisme unique
Ce que le produit fait et qu'on ne trouve pas ailleurs (méthode nommée, angle propriétaire). → source

## 6. Before / After
| Avant | Après |
|---|---|

## 7. Bénéfices
- Rationnels : …
- Émotionnels : …

## 8. Preuves disponibles (RÉEL uniquement — zéro invention)
| Type | Élément | Source |
|---|---|---|
| Médaille auteur | | |
| Source scientifique | | |
| Témoignage réel | | |

## 9. Objections probables → réponses
| Objection | Réponse ancrée dans le produit |
|---|---|

## 10. Banque de hooks
**Vérifiables (audience froide)** — scène historique/scientifique :
- …
**Vécus (audience chaude)** — anecdote réelle de l'auteur :
- …

## 11. Banque narrative
Analogies, métaphores, histoires, citations déjà présentes dans le produit (réutilisables). → sources

## 12. Signature / rattachement
Comment le produit se relie au fil (mismatch → souveraineté) et à la signature *origine évolutive → complexification → mismatch → quoi faire*.

## 13. Offre
Prix · format · échéance réelle · garantie · bonus.

## 14. CTA
- Régime nurture : … (doux, micro-engagement / boucle ouverte)
- Régime vente : … (ferme, unique, daté)

## 15. ⚠ Lacunes & questions à l'auteur
- …
```

## Règle d'or anti-slop

La matière rare (preuves, témoignages, vécu, chiffres) vient du produit ou de l'auteur — jamais d'une supposition plausible. Si un champ est vide dans le produit, il reste vide dans le brief, et la question part en §15.
