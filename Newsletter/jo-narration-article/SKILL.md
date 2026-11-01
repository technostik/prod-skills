---
name: jo-narration-article
description: Transforme une note de réflexion ou un argumentaire en article narratif publiable (Substack, fil, LinkedIn). Entrée par le concret, un seul aha, arc situation→tension→pivot→retour concret. Les articles restent dans le cadre philosophique de la souveraineté intégrale. Use when the user runs /jo-narration-article, /jo_narration-article, asks to narrativiser a note, write a Substack article, or transformer une note en article.
---

# jo-narration-article

Tu transformes UNE note de réflexion en UN article narratif publiable. C'est une distillation, pas un résumé.

Vault : `/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel`

Arguments : `{source}` (chemin, défaut = `<current_note>` si présent) · `{format}` substack|fil-x|linkedin (défaut substack) · `{sortie}`.

## Étape 0 — Lire les sources avant tout

Lis dans cet ordre :
1. Le fichier `{source}` — c'est la matière brute à transformer
2. `Business/reference-profil.md` §5 (voix et style)
3. `Business/Lead-magnet/Newsletter/Heuristiques narratives.md` — les 10 piliers marketing. **Ne les réétablis pas, applique-les directement.**

## Étape 1 — Identifier l'unique "aha"

Avant d'écrire, pose-toi cette question : **quelle est la seule idée de cet article ?**
- Un seul insight. Pas une liste.
- Formulé comme un paradoxe ou un retournement ("ce que tu crois est X, en réalité c'est Y").
- L'article doit rester dans le cadre philosophique de la **souveraineté intégrale** — santé, autonomie, attention, société, technologie : tout ce qui touche à reprendre la main sur sa propre vie.

Si la note source ne contient pas clairement cet "aha", **pose la question avant d'écrire**.

## Étape 2 — Construire le hook

Le hook ouvre sur une **scène vraie, vérifiable, cinématographique**. Règles strictes :

- Historique, scientifique, ou anecdote documentée d'une célébrité/personnage public. **Pas une scène de vie générique inventée.**
- Première phrase = image physique (température, lumière, son, texture). Pas un résumé.
- Tension ou mystère dès la 2e ligne.
- Un personnage nommé.
- Longueur : ~150 mots minimum. Ne pas couper court — c'est le temps d'immersion qui crée l'attachement.
- Puis **pont nommé explicitement** : "Ce n'est pas une histoire sur X. C'est une histoire sur…" + un élément concret de la scène porté dans le monde du lecteur.

## Étape 3 — Rédiger l'article

Structure (dans cet ordre, sans titres H2/H3 dans le corps) :

1. **Hook** (scène + pont)
2. **Idée maîtresse** — l'unique "aha", développé. L'analogie *avant* le terme technique.
3. **Dialectique** — montre les deux pôles en tension. Jamais un seul extrême.
4. **Retour concret** au lecteur (son quotidien, son corps, lundi matin).
5. **Clôture** — une question ouverte ou une invitation à agir. Pas de morale.

Contraintes de style :
- Phrases courtes. Une idée par phrase.
- Pas de formules creuses ("il est essentiel de", "n'oubliez pas").
- Pas de listes à puces dans le corps.
- Gras parcimoniaux — mots-clés de survol uniquement.
- Termes propres (mismatch, néguentropie, agent/arène…) introduits avec une image la première fois.
- Zéro témoignage client inventé. Les preuves = les médailles réelles de l'auteur (marathon, 2e dan, 4 livres, maison bâtie, langage de prog, sortie d'insomnie).

## Longueur cible par format

| Format | Longueur | Notes |
|---|---|---|
| `substack` | 600–900 mots | Texte aéré, peut avoir un intertitre |
| `fil-x` | 8–12 tweets | Premier tweet = hook compressé |
| `linkedin` | 300–500 mots | Retour concret en premier, hook condensé |

## Étape 4 — Vérifier les 10 piliers

Relis l'article en cochant les piliers de `Business/Lead-magnet/Newsletter/Heuristiques narratives.md`.
Indique en note de rédaction (2-3 lignes) : les piliers satisfaits, ceux absents et pourquoi.

## Étape 5 — Écrire le fichier

Si `{sortie}` est précisé, écris là. Sinon, crée le fichier à côté de `{source}` avec le suffixe `-article.md`.

Frontmatter obligatoire :
```yaml
---
type: article-narratif
format: [le format cible]
source: [chemin de la note source]
statut: brouillon
date: [date du jour]
---
```

**Interdiction de slop.** Si la note source manque d'un élément (preuve, analogie concrète, chiffre), pose la question — ne comble pas avec du générique.
