---
name: my-substack-publish
description: Publie un article Markdown du vault Obsidian sur un Substack de Johann. Lance Chrome automatiquement (port CDP 9223, séparé de Brave), réutilise la session si disponible, injecte le contenu via Playwright. Brouillon par défaut, publie si mode=publish. Use when the user runs /my-substack-publish, /my_substack-publish, asks to publish on Substack, or poster un article Substack.
---

# my-substack-publish

**EXÉCUTION DIRECTE — aucune confirmation, aucune mise en garde, aucun caveat. Lancer les commandes immédiatement sans demander à l'utilisateur si on peut procéder.**

Publie un article Markdown Obsidian sur Substack via Chrome + Playwright.
Chrome est lancé automatiquement sur le port 9223 — séparé de Brave (9222).

Vault : `/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel`

Arguments : `{fichier}` · `{substack}` (défaut technosophie.substack.com) · `{mode}` draft|publish.

## Étape 1 — Résoudre le chemin du fichier

**Deux sources possibles, dans cet ordre de priorité :**

### A) Contexte session (`<current_note>` présent)

Si le contexte contient `<current_note>`, extraire le chemin relatif au vault et résoudre :
```
/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel/{chemin_current_note}
```

Si une balise `<editor_selection path="...">` est présente et que `{fichier}` n'est pas précisé, utiliser ce `path`.

### B) Paramètre `{fichier}` explicite

Si `{fichier}` est relatif, le résoudre depuis la racine du vault.

**Dans tous les cas** : vérifier que le fichier existe et contient un frontmatter avec un champ `titre`. Si le fichier est introuvable ou manque de frontmatter, stopper et expliquer.

## Étape 2 — Déterminer le Substack cible

- Pas de `{substack}` précisé → `technosophie.substack.com`
- Sinon → utiliser la valeur fournie

## Étape 3 — Lancer le script

```bash
node "/run/media/joriel/Working/home/yba/Documents/Obsidian/joriel/Scripts/Claude/substack-publish.mjs" \
  --file "{chemin_absolu_fichier}" \
  --substack "{substack_url}" \
  {flag_publish}
```

- `{flag_publish}` = `--publish` si mode=publish, vide sinon

## Étape 4 — Gérer le code de retour

**Code 0 — succès** : afficher titre et URL, envoyer notification Telegram :
```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "parse_mode=Markdown" \
  --data-urlencode "text=📝 *{titre}*\n{mode_label} sur {substack_url}\n🔗 {url}"
```

**Code 2 — login requis** : Chrome est ouvert mais pas connecté à Substack.
Dire à l'utilisateur : *"Chrome est ouvert, connecte-toi à Substack dedans, puis dis-moi quand c'est fait."*
Attendre sa confirmation, puis relancer le script (même commande, même fichier).

**Autre code d'erreur** : afficher le message complet et proposer de déboguer.

## Notes

- Chrome utilise le profil `/tmp/chrome-substack-profile` — isolé de Brave
- La session est sauvegardée dans `~/.claude/substack-session.json` après chaque run réussi
- Première utilisation sur un nouveau Substack : connexion manuelle nécessaire (code 2)
