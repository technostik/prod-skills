---
name: jo-narration-serie
description: Transforme un corpus de concepts articulés en une série narrative d'articles (Substack, mini-cours). Pipeline en 4 phases avec validation à chaque cran = Architecture → Trame → Narration → v2 heuristique. Un fichier par article, reprise possible à n'importe quelle étape. Les articles restent dans le cadre philosophique de la souveraineté intégrale. Use when the user runs /jo-narration-serie, /jo_narration-serie, asks for a series of articles, architecture éditoriale, or mini-cours narratif.
---

# jo-narration-serie

Tu transformes un corpus de notes de réflexion en une série narrative d'articles. C'est une **distillation en pipeline** : chaque phase produit des fichiers, validés avant de passer à la suivante. Ne brûle pas les étapes.

Vault : `/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel`

Arguments : `{corpus}` (chemins séparés par virgules, requis) · `{but}` (requis) · `{public}` · `{format}` substack|mini-cours · `{sortie}` · `{phase}` 1|2|3|4|tout (défaut 1).

## Lire avant tout

Lis ces fichiers au démarrage :
1. Les fichiers `{corpus}` — la matière brute
2. `Business/reference-profil.md` — voix, médailles, style
3. `Business/Lead-magnet/Newsletter/Heuristiques narratives.md` — les 10 piliers marketing à appliquer en Phase 3 et Phase 4
4. Si disponible : `Business/reference-cadre-philo.md` (fondation conceptuelle du souverainisme intégral)

Les heuristiques ne se réétablissent pas : on les **applique**. Elles servent à la fois en Phase 3 (rédaction) et en Phase 4 (audit).

---

## Arborescence de sortie

Tout va dans `{sortie}`. Convention numérotée pour pouvoir reprendre là où ça casse :

```
{sortie}/
  _status.md                  ← tableau de bord : phase atteinte, état par article
  01 - Architecture.md        ← Phase 1
  02 - Trame synoptique.md    ← Phase 2
  03 - Narration v1/          ← Phase 3 — UN FICHIER PAR ARTICLE
     Article-1-[slug].md
     Article-2-[slug].md
     ...
  04 - Audit heuristique.md   ← Phase 4 — rapport
  05 - Narration v2/          ← Phase 4 — UN FICHIER PAR ARTICLE (corrigé)
     Article-1-[slug].md
     ...
```

**`_status.md` se met à jour à la fin de chaque phase et de chaque article.** Il contient : la phase courante, une ligne par article avec son état (☐ à faire / ◐ en cours / ☑ validé), et une note « dernier point de reprise ».

---

## Phase 1 — Architecture éditoriale

> Produit : `01 - Architecture.md`

Construis le **cadrage éditorial** de la série. Contenu obligatoire :

**1. Le fil rouge** (à tenir dans chaque article)
- But unique : `{but}` — qui n'a pas ce but passe son chemin. L'exclusion est assumée.
- Le fil rouge est une idée simple qui relie tous les articles. La série l'*applique*, elle ne le revendique pas. Précise où il se pose explicitement (article 1) et comment il se rappelle ensuite.
- Ancrage : les articles restent dans le champ de la **souveraineté intégrale** — santé, autonomie, attention, société, technologie, toujours rapporté à la capacité du lecteur à reprendre la main sur sa propre vie.

**2. La promesse** (une phrase) + **le contrat de lecture** (le plan annoncé dès l'article 1 : "en N articles je t'emmène de X à Y")

**3. L'arc émotionnel** article par article (le mouvement intérieur du lecteur, pas la densité d'idées)

**4. La structure article par article** (tableau)
| # | Titre de travail | Idée maîtresse | Source dans le corpus | Boucle ouverte |
|---|---|---|---|---|

- Chaque article = 1 idée maîtresse, 1 analogie forte, 1 boucle ouverte.
- Nombre d'articles non figé : fusionne ou scinde si le récit le demande.

**5. Principes de narration** à tenir dans tous les articles (issus de la voix de l'auteur et des heuristiques).

**Règle** : aucun trou comblé avec du générique. Si le corpus manque d'un élément, pose la question.

→ À la fin : écris/actualise `_status.md` (Phase 1 ✓).

---

## Phase 2 — Trame synoptique

> Produit : `02 - Trame synoptique.md`
> **Valide d'abord l'Architecture.**

Pour chaque article :
- La **promesse** de l'article (une phrase)
- Le **plan** : les beats dans l'ordre (pas de rédaction — juste l'enchaînement des idées)
- L'**idée de hook** : quelle scène vraie, vérifiable, avec quel personnage nommé
- Le **pont nommé** : la phrase « Ce n'est pas une histoire sur X. C'est une histoire sur… » + l'élément concret de la scène porté dans le monde du lecteur
- **2 à 4 références** placées là où elles servent un beat
- L'**analogie maîtresse**
- La **boucle ouverte** (question que seul l'article suivant résout)
- Un **CTA** (même dans une série d'articles, chaque article invite à quelque chose)

En tête : les invariants transverses. En bas : une liste **À valider**.

→ Actualise `_status.md` (Phase 2 ✓).

---

## Phase 3 — Narration ⭐ — UN FICHIER PAR ARTICLE

> Produit : `03 - Narration v1/Article-N-[slug].md` — **un fichier distinct par article.**
> **Valide d'abord la Trame.**

**Le geste central : c'est un argumentaire, le transformer en histoire.** On entre par le concret, on porte le lecteur, l'image avant le terme savant, références en bloc `› Pour creuser` en fin. Voix "tu / on". Pas de H2/H3 dans le corps.

**Écris les articles un par un.** Après chaque article : actualise `_status.md`.

### Checklist-gate par article — OBLIGATOIRE

Chaque fichier se termine par ce bloc, rempli honnêtement. **Tu ne déclares un article terminé que si les 5 critères critiques sont ☑.**

```
--- CHECKLIST (ne pas publier) ---
☐ HOOK — scène vraie + 1re phrase sensorielle (température/lumière/son) + personnage nommé + ~150 mots avant le pont
☐ PONT NOMMÉ — « Ce n'est pas une histoire sur X. C'est une histoire sur… » + élément concret de la scène porté chez le lecteur
☐ CTA — présent (invitation à agir, question, partage)
☐ BOUCLE — question logique que seul l'article suivant résout (sauf dernier article)
☐ CADRE — l'article touche à la souveraineté intégrale (autonomie, santé, attention, société, technologie) sans plaquer un jargon hors contexte
Secondaires : 1 seul aha · analogie avant concept · dialectique (paire de contraires) · sources intégrées · voix (phrases courtes, pas de moralisme)
```

**Interdiction** : ne réécris pas les arguments, n'en invente pas. Tu changes la **forme** (argumenter → raconter), pas le fond. Si un passage manque de matière, pose la question.

→ Quand les N articles sont écrits : actualise `_status.md` (Phase 3 ✓).

---

## Phase 4 — Audit heuristique → v2

> Produit : `04 - Audit heuristique.md` (rapport) + `05 - Narration v2/Article-N-[slug].md`.
> **Valide d'abord la Narration v1.**

1. **Score** sur les 10 piliers de `Business/Lead-magnet/Newsletter/Heuristiques narratives.md` (/5 chacun) + critères narratifs (hook, pont, arc, dialectique, voix) — par article.
2. **Pistes** : pour chaque critère insuffisant, une correction concrète **ancrée dans le corpus** — exemple réel à écrire, pas une règle abstraite.
3. **v2** : réécris chaque article (un fichier par article) en intégrant les corrections. Comble les manques en piochant dans le corpus — jamais du slop. Si un élément manque, **pose la question**.

→ Actualise `_status.md` (Phase 4 ✓ + scores finaux).

---

## Comportement par défaut

Si `{phase}` vaut `1` (défaut), exécute la **Phase 1** seule, puis arrête pour validation.
Si `{phase}` = `tout`, enchaîne toutes les phases **en demandant validation entre chacune**.
Si l'utilisateur pointe un article ou une phase précise, reprends **uniquement** ce point.

---

## Règle d'or anti-slop

La matière rare (le vécu de l'auteur, ses médailles réelles, ses nuances propres) vient de lui, à la demande. L'IA ne comble jamais les trous avec du plausible. Un document lacunaire avec des questions vaut mieux qu'un document complet avec du générique.
