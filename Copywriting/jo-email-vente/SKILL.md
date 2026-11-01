---
name: jo-email-vente
description: Rédige un email de vente OU une séquence de vente (régime vente directe) à partir d'un brief-produit. Habille l'argumentaire en narration — hook vérifiable ou vécu, pont nommé, douleur, villain système, mécanisme unique, preuves réelles, offre, urgence fondée, CTA ferme et unique. Zéro faux témoignage, zéro urgence artificielle. Propose 3 accroches avant de rédiger. Use when the user runs /jo-email-vente, /jo_email-vente, asks for an email de vente, séquence de vente, or sales email from a brief.
---

# jo-email-vente

Tu écris du copy de **vente directe** — un email ou une séquence — à partir d'un brief produit. C'est le régime « un cran au-dessus du nurture » : on vient **déclencher une décision**, pas seulement nourrir une relation. La narration reste l'habillage ; l'argument de vente est le patron.

Vault : `/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel`

Arguments : `{produit}` (brief ou dossier, requis) · `{mode}` email|sequence · `{audience}` froid|chaud · `{sortie}`.

> **Principe-mère : la narration est l'habillage de l'argumentation.** Le brief est le patron. Tu lui tailles un vêtement qui fait *agir* — sans jamais inventer la matière.

## Étape 0 — Lire les sources avant tout

1. `{produit}` — si c'est un `brief-produit.md`, c'est ta matière première. **Si c'est un dossier/fichier sans brief, arrête-toi et propose de lancer `jo-brief-produit` d'abord** — ne devine pas le produit.
2. `Business/Copywriting/00 - Synthèse copywriting.md` — §2 (techniques), §4.1 (email de vente), §5 (adopter/adapter/rejeter).
3. `Business/Reference/reference-profil.md` (ou `Business/Profil/profil-resume.md`) — voix, médailles réelles, lignes rouges.

## Étape 1 — Cadrer la vente

Depuis le brief, verrouille : **promesse · douleur n°1 · villain · mécanisme unique · before/after · preuves réelles disponibles · niveau de conscience · offre (prix / contenu / garantie / bonus / échéance) · CTA**.

Détermine l'**audience** : froide → hook **vérifiable** (historique/scientifique) ; chaude → hook **vécu** autorisé (anecdote réelle de l'auteur).

Si un élément essentiel manque (offre non fixée, aucune preuve, pas d'échéance) → **pose la question, ne comble pas.**

## Étape 2 — Proposer 3 accroches (avant de rédiger)

**Ne commence pas l'email.** Propose d'abord **3 accroches** (6-10 lignes chacune), sur des angles différents (historique / scientifique / vécu réel — selon l'audience). Première phrase sensorielle, personnage nommé, tension immédiate. **Attends la validation**, puis passe à l'Étape 3.

## Étape 3 — Rédiger

### Si `mode = email` — anatomie

1. **Objet (3 options)** + **préheader** — curiosité ou paradoxe, jamais clickbait.
2. **Hook** — l'accroche validée.
3. **Pont nommé** vers la douleur du lecteur (élément concret de la scène porté chez lui).
4. **Douleur agitée** — en **langage réel** (brief §3) ; ce que ça coûte de rester là.
5. **Villain externe** — le **système** responsable (déculpabilise le lecteur).
6. **Bascule** — la nouvelle vision / l'insight contre-intuitif (before → after).
7. **Mécanisme unique** — le produit présenté comme la **solution logique**, pas une liste de features.
8. **Preuve** — médailles réelles + sources scientifiques + **témoignages réels** (jamais inventés).
9. **L'offre** — ce que c'est, prix, contenu, garantie, bonus.
10. **Coût de l'inaction + urgence fondée** — ce qui se perd à ne rien faire + **échéance réelle**.
11. **CTA unique et ferme** — une seule action, formulée clairement.
12. **PS** — récap du bénéfice + rappel de l'échéance (le PS est lu).

Longueur : 500-900 mots. Le CTA se répète 1 à 2 fois max — **toujours la même action.**

### Si `mode = sequence` — squelette recommandé (adaptable)

| # | Rôle de l'email | Cœur |
|---|---|---|
| 1 | Ouverture | histoire + problème nommé + « une solution arrive » |
| 2 | Mécanisme | pourquoi les tentatives passées ont échoué (villain) + la nouvelle voie |
| 3 | Preuve | médailles, sources, témoignages réels, cas concrets |
| 4 | Offre | détail de l'offre + bonus + garantie + 1er rappel d'échéance |
| 5 | Objections | lever les freins (brief §9) en FAQ narrative |
| 6 | Close | dernier jour, urgence fondée, CTA final |

**Un fichier par email.** Chaque email respecte l'anatomie (hook → … → CTA) mais ne poursuit qu'**un seul objectif d'étape**. Le nombre d'emails n'est pas figé : fusionne ou scinde selon l'offre.

## Réglage profil — lignes rouges

- Hook froid = **vérifiable uniquement** ; le vécu est réservé à l'audience chaude.
- **Villain = système** (captologie, méthode concurrente inefficace, mismatch) — **jamais** des personnes ou des groupes.
- **Preuves = réel uniquement.** Zéro faux témoignage, zéro chiffre gonflé.
- **Urgence = réelle** (échéance datée, cohorte limitée). **Aucun faux countdown.**
- Voix **dialectique, directe, analytique** — il **analyse, ne prêche pas**. Pas de hype.
- **CTA unique.** Pas d'empilement d'offres.

## Checklist-gate — OBLIGATOIRE (ne pas livrer si un critère critique manque)

```
☐ HOOK conforme — sensoriel, personnage nommé, tension ; vérifiable (froid) ou vécu (chaud)
☐ PONT NOMMÉ vers la douleur du lecteur
☐ DOULEUR en langage réel (issu du brief)
☐ VILLAIN = système, jamais des personnes
☐ MÉCANISME UNIQUE présent (pas une liste de features)
☐ PREUVES réelles uniquement (zéro invention)
☐ OFFRE claire — prix, contenu, garantie, échéance
☐ URGENCE fondée (pas artificielle)
☐ CTA unique et ferme
Secondaires : before/after concret · dialectique · signature mismatch si pertinent · voix (phrases courtes, pas de moralisme)
```

## Sortie fichier (obligatoire)

Défaut : à côté du brief.
- `mode = email` → `Email-vente-[slug].md`
- `mode = sequence` → dossier `Sequence-vente-[slug]/` avec `Email-N-[slug].md`

Frontmatter :

```yaml
---
type: email-vente
mode: [email | sequence]
produit: [chemin du produit]
brief: [chemin du brief-produit]
audience: [froid | chaud]
statut: brouillon
date: [date du jour]
---
```

## Règle d'or anti-slop

Les preuves, chiffres, témoignages et l'offre viennent du brief ou de l'auteur — **jamais inventés**. Si une brique manque, **pose la question avant d'écrire.**
