---
name: my-generate-image
description: Génère une image de couverture pour un article Obsidian via Cloudflare Workers AI (flux-2-klein-4b, tier gratuit) et l'intègre en tête de l'article. Style épuré, vectoriel, illustration business. Use when the user runs /my-generate-image, /my_generate_image, asks for a cover image, illustration d'article, image Cloudflare, or "génère une image". Optional style hint after the command; add "local" to force the local flux2 model.
---

# my-generate-image

**EXÉCUTION DIRECTE — aucune confirmation, aucune mise en garde. Lancer les commandes immédiatement.**

Génère une image de couverture depuis un article Obsidian via Cloudflare Workers AI (même pipeline que le skill Claude `my_generate-image`).

Vault : `/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel`

## Étape 0 — Mode de génération

Analyser les arguments (`style_hint` / texte après la commande) :
- Si le mot **local** est présent → passer `--local` au script et le retirer du style_hint avant l'étape 3
- Sinon → mode cloud (fallback automatique si crédits épuisés)

## Étape 1 — Résoudre le chemin de l'article

Dans cet ordre :

**A)** Si le contexte session contient `<current_note>` : extraire le chemin et résoudre depuis la racine du vault.

**B)** Si un chemin de fichier `.md` est fourni : relatif → depuis la racine du vault ; absolu → tel quel.

**C)** Sinon : l'onglet actif Obsidian via le skill `obsidian-cli` si disponible.

Vérifier que le fichier existe. Stopper avec explication si absent.

## Étape 2 — Lire l'article et extraire le moment fort

Lire le Markdown. Identifier :
- Le **concept central**
- Le **moment de tension** ou **pivot narratif**
- Les **mots-clés visuels** (objets, gestes, espaces, contrastes)

Ne pas résumer — chercher la scène ou la métaphore qui *incarne* l'article.

## Étape 3 — Générer le prompt image

Prompt en anglais, 30–60 mots :

```
{scène_ou_métaphore_principale}, {éléments_visuels_clés}, clean minimal vector illustration,
flat corporate style, {palette_couleurs}, white background, no text, no people faces,
sharp geometric shapes, professional editorial illustration
```

Règles :
- Anglais obligatoire
- Un seul sujet central
- Style par défaut : vectoriel plat, corporate, épuré, fond blanc
- Si `style_hint` : l'intégrer dans la palette ou la mise en scène sans casser le style
- Pas de visages détaillés (silhouettes OK)
- Pas de texte dans l'image

Afficher le prompt à l'utilisateur avant de lancer la génération.

## Étape 4 — Chemin de sortie

```
{dossier_de_l_article}/_resources/{nom_article_sans_extension}-cover-{YYYYMMDD}.jpg
```

Exemple : `Blog/Souverain/article.md` → `Blog/Souverain/_resources/article-cover-20260612.jpg`.

## Étape 5 — Script de génération

```bash
node "/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel/Scripts/Claude/generate-image.mjs" \
  --prompt "{prompt_image}" \
  --output "{chemin_absolu_output}" \
  {--local si mode local forcé}
```

Le script affiche `✅ Image sauvegardée : {chemin}` en cas de succès.

**Fallback** : HTTP 402 ou message credit/quota/billing → bascule automatique sur `flux2` local (fast-market). `--local` force le local sans tenter le cloud.

**Erreurs** :
- `CLOUDFLARE_ACCOUNT_ID / API_TOKEN manquants` → les ajouter dans l'env Grok (`env` / settings) — mêmes variables que Claude Code
- `401` → token expiré
- Erreur locale → afficher le message complet

Les credentials viennent de `CLOUDFLARE_ACCOUNT_ID` et `CLOUDFLARE_API_TOKEN`.

## Étape 6 — Intégrer en tête de l'article

```markdown
![[{chemin_relatif_depuis_vault}]]
```

- Frontmatter YAML présent : insérer **immédiatement après** le bloc `---`, avant le premier `#` ou paragraphe
- Sinon : première ligne
- Une ligne vide après l'image

Si une couverture `![[...-cover-....jpg]]` existe déjà en tête, la remplacer.

## Étape 7 — Confirmer

Afficher : prompt, chemin de l'image, confirmation de mise à jour.

Notification Telegram si `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` sont dans l'env :

```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "parse_mode=Markdown" \
  --data-urlencode "text=🎨 *Image générée*\n_{titre_article}_\n\`{prompt_court}\`"
```

## Notes

- Modèle : `@cf/black-forest-labs/flux-2-klein-4b` (tier gratuit Cloudflare Workers AI)
- PNG natif du modèle, écrit en JPEG par le script
- Fichier existant du même nom : écrasé
