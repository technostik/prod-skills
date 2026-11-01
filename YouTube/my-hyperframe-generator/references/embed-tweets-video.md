# Embed tweets & vidéos externes (X, YouTube) — acquis testés 2026-10-15/16

Exemple vivant : un test de l'auteur, non fourni (4 scènes, 87 s :
carte + image, long tweet + scroll, extrait vidéo X, extrait YouTube).

## 0. Règle mère

**Rien depuis le réseau au rendu.** Jamais d'iframe ni de script externe
(X `widgets.js`, embed YouTube) : ils restent noirs dans la vidéo. Toujours
rapatrier les médias en local dans `assets/` et **recréer la carte** (style
Joriel : fond `#0d1117`, bordure `--bleu`, texte `--blanc`, surlignage `--or`).
Texte du post recopié mot à mot + URL source en légende.

## 1. Images jointes (X : `pbs.twimg.com`)

```bash
curl -sL -o assets/<nom>.jpg "https://pbs.twimg.com/media/<id>?format=jpg&name=large"
```

- Affichage **entier** : `object-fit: contain` (+ `max-height` en vh), jamais
  `cover` (croppe : on ne voyait que le haut de l'image).
- Layout : 2 colonnes texte + image (paysage) ; colonne unique centrée étroite
  si portrait. Réduire le corps à ~3.2 vh pour l'équilibre.

## 2. Vidéos (X `amplify`, YouTube) — découpe + audio OBLIGATOIRE

```bash
# secondes ABSOLUES du post d'origine (ex. 22:31 → 1351)
yt-dlp --no-playlist --download-sections "*<start>-<end>" --force-keyframes-at-cuts \
  -f "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b" --merge-output-format mp4 \
  -o "assets/<nom>.mp4" "<url>"
# 1080p suffit largement (downscale si 4K) :
ffmpeg -y -i assets/<nom>.mp4 -map 0:v:0 -map 0:a:0 -vf scale=1920:1080 \
  -c:v libx264 -preset fast -crf 20 -c:a aac assets/<nom>.mp4
```

- ⚠️ `-f mp4` seul prend souvent un flux **vidéo sans audio** (vécu : mp4
  muet, « que l'image »). Le format `bv+ba` ci-dessus + `-map` explicites
  au downscale sont obligatoires.
- Vérifier à chaque fois :
  `ffprobe -show_streams` (streams `h264` + `aac` présents) +
  `ffmpeg -af ebur128` (voix ≈ −29 LUFS = audible, pas de silence).
- Preuve pipeline : un mini-rendu 10 s doit sortir avec piste `aac`
  non silencieuse avant d'intégrer au scénario.

## 3. Câblage HyperFrames

```html
<video id="vid" class="tvid clip" src="assets/<nom>.mp4" playsinline
  data-has-audio="true" data-start="<t>" data-duration="<d>"
  data-track-index="0" data-volume="1"></video>
```

- Son de la vidéo **sur le `<video>`** (`data-has-audio`, pas `muted`).
  `<audio>` séparé uniquement pour musique/voix off.
- Jamais de `play()` / `pause()` / `seek` en code (le framework possède
  la lecture). Timing sur le media, **jamais** sur un wrapper qui porte
  aussi `data-start` (erreur `video_nested_in_timed_element` réelle).
- Ne jamais animer les dimensions du media ; animer un wrapper non timé.

## 4. Preview : le son exige une lecture continue

Politique autoplay des navigateurs : pas de son sans geste (cliquer Play,
vérifier non-muté). Le scrub de timeline est muet par nature — « pas de
son que l'image » en scrub ne prouve rien ; seul un rendu (même draft
partiel) prouve l'audio.

## 5. Tweets longs : extrait + scroll

Le texte intégral est illisible en 3 s → **extrait seul**, légende qui
le dit (« extrait seul : le texte intégral est illisible en 3 s »).
Scroll : `.viewport` hauteur fixe + `overflow:hidden` + tween GSAP `y`
en `vh` + `data-layout-allow-overflow` sur le contenu (overflow intentionnel,
sinon info `container_overflow` au `check`). Surlignage `--or` **après**
la fin du scroll. Offset calibré par snapshots (ex. `-8vh`).

## 6. ⚠️ Bug GSAP avéré : pulse `scale` sur `<span>` inline + ancêtre transformé

`tl.fromTo("span", {scale:1}, {scale:1.06, yoyo…})` avec `immediateRender`
quand un **ancêtre porte lui aussi un transform GSAP** (ex. scroll `y`) →
texte du span **invisible en capture** jusqu'au prochain repaint (prouvé
par snapshots : invisible à t=3.2 s, visible après fin du pulse).
Règle : sur span inline dans sous-arbre transformé → **surlignage couleur
seule, sans pulse**. Pulse réservé aux éléments block ou sans ancêtre
transformé.

## 7. Vérification (inchangée, rappel)

`check` vert (layout + contraste AA) → snapshots aux temps-clés
(carte, mi-scroll, highlight, début/fin vidéo) → `preview --background`
(HTTP 200, reload auto) → `render` draft **sur feu vert utilisateur
uniquement**.

## 8. Références web (pages d'articles, rapports) — acquis 2026-10-27

Pour afficher une source web dans une composition (page d'article, rapport,
documentation), **deux méthodes**, choisies selon l'accessibilité de la
page :

### 8.1 Screenshot local (préféré quand la page est accessible)

```bash
google-chrome --headless=new --disable-gpu --window-size=1920,1080 \
  --virtual-time-budget=8000 --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  --screenshot=assets/references/Rxx-<slug>.png "<url>"
```

- Vérifier que le fichier fait > 50 Ko (sinon page bloquée / paywall /
  anti-bot → basculer sur 8.2).
- Affichage : `<img class="ref-shot" id="ref-…" src="assets/references/Rxx-<slug>.png" alt="…">`
  en plein écran (`position:absolute; inset:0; object-fit:cover`), avec un
  zoom léger GSAP (`scale: 1 → 1.03/1.04` sur la durée du clip).
- Pas de webcam incrustée sur ces steps (`data-cam="off"`, pas de
  `cam-frame`).

### 8.2 Card stylisée (fallback pour pages paywallées ou bloquées)

Reproduire le contenu réel dans une card plein écran (fond `#0d1117`,
bordure `--bleu`, texte `--blanc`, surlignage `--or`), sans réseau :

```html
<div class="ref-card" id="ref-…">
  <div class="ref-source">Source · Date</div>
  <div class="ref-author">Auteur</div>
  <div class="ref-title">Titre de l'article</div>
  <div class="ref-quote">« <span class="hl">citation clé</span> »</div>
  <div class="ref-url">domaine.com/…/slug</div>
</div>
```

- Animation : entrée opacity/y + scale 0.97→1 (0.5 s), surlignage couleur
  seul sur `.hl` (pas de pulse scale sur span inline — cf. §6), puis zoom
  léger `scale: 1 → 1.03` sur la durée du clip.

### 8.3 Règles communes

- `data-cam="off"` sur ces steps, pas de `cam-frame`.
- Pas de réseau au rendu : screenshot téléchargé localement ou card
  stylisée uniquement.
- Le scénario doit indiquer pour chaque référence si elle est accessible
  (screenshot) ou paywallée/bloquée (card).
