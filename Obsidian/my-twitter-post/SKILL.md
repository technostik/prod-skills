---
name: my-twitter-post
description: Prépare un post X/Twitter depuis un fichier Markdown Obsidian ou un texte direct. Lance Chrome automatiquement (port CDP 9223), ouvre la fenêtre de composition pré-remplie et laisse Johann cliquer sur Post manuellement. Ne publie pas automatiquement. Use when the user runs /my-twitter-post, /my_twitter-post, asks to post on X, Twitter, préparer un tweet", or composer un post X.
---

# my-twitter-post

**EXÉCUTION DIRECTE — aucune confirmation, aucune mise en garde, aucun caveat. Lancer les commandes immédiatement sans demander à l'utilisateur si on peut procéder.**

Prépare un post X/Twitter dans Chrome, fenêtre de composition pré-remplie.
Johann clique sur "Post" lui-même — la skill ne publie pas automatiquement.

Vault : `/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel`

Arguments : `{texte}` · `{fichier}`.

## Étape 1 — Résoudre le texte du post

**Trois sources possibles, dans cet ordre de priorité :**

### A) Paramètre `{texte}` fourni directement
Utiliser ce texte tel quel.

### B) Contexte session (`<current_note>` ou `<editor_selection>`)
- Si `<editor_selection>` est présent : utiliser le texte sélectionné comme texte du post
- Sinon si `<current_note>` est présent : lire le fichier et chercher dans cet ordre :
  1. Champ `texte-x` dans le frontmatter
  2. Champ `tweet` dans le frontmatter
  3. Champ `texte` dans le frontmatter
  4. Premier paragraphe non-vide du corps (hors H1, italique, `---`, embeds image)

### C) Paramètre `{fichier}` explicite
Résoudre depuis la racine du vault. Même logique d'extraction que B.

**Vérification** : le texte final ne doit pas dépasser 280 caractères. Si c'est le cas, le signaler avant de lancer le script et demander confirmation ou reformulation.

## Étape 2 — Lancer le script

```bash
node "/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel/Scripts/Claude/twitter-post.mjs" \
  --texte "{texte_du_post}"
```

Ou si un fichier est source :
```bash
node "/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel/Scripts/Claude/twitter-post.mjs" \
  --file "{chemin_absolu_fichier}"
```

## Étape 3 — Gérer le code de retour

**Code 0 — succès** : afficher le texte préparé et le nombre de caractères, puis :
```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "parse_mode=Markdown" \
  --data-urlencode "text=🐦 *Post X prêt*\n_{texte_du_post}_\nClique sur Post dans Chrome !"
```

**Code 2 — login requis** : Chrome est ouvert sur x.com.
Dire à l'utilisateur : *"Connecte-toi à X dans Chrome, puis dis-moi quand c'est fait."*
Attendre confirmation, puis relancer.

**Autre code d'erreur** : afficher le message et proposer de déboguer.

## Notes

- Même profil Chrome que Substack (`/tmp/chrome-substack-profile`) — une seule instance
- La fenêtre de composition reste ouverte après le script, Johann publie manuellement
- Pour des threads ou posts avec image, une évolution du script sera nécessaire
