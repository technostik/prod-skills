# Primitives HTML — catalogue Joriel

Source de vérité pour la traduction scénario → HTML.
Chaque primitive est démontrée une fois, avec son nom affiché à l'écran, dans `examples/demo/` (table : `examples/demo/README.md`). Les styles de `chip`, `stamp`, `dico` et `cols2` sont déduits de `visual-language-joriel.md` §3 : à valider.
Chaque primitive ci-dessous est un bloc HTML réutilisable tel quel.

## Mouvements

Le style est dans `examples/demo/assets/style-joriel.css`, les animations dans le script de chaque composition de la démo (`examples/demo/compositions/`) : ce sont les deux sources de vérité, aucun bloc de code n'est recopié ici. Les délais sont relatifs au début de l'étape, les durées en secondes.

| Primitive | Mouvement | Délai | Durée |
|---|---|---|---|
| bloc `.in` | glisse (y 34 → 0) et apparaît ; rebond léger pour `kw` et `count` | 0 | 0,6 (0,7) |
| lignes d'un bloc | décalées de 0,12 s | 0,1 | 0,5 |
| `kicker`, `stitle` | le kicker entre par la gauche, le titre descend | 0 ; 0,1 | 0,5 ; 0,6 |
| `strike` | deux traits tracés, le second en sens inverse | 0,35 ; 0,7 | 0,4 |
| `stamp` | claque (×2,4 → 0,94 → 1), un tampon toutes les 0,24 s | 0,35 | 0,24 + 0,2 |
| `chip` | pop `back.out`, 0,14 s entre deux | 0,25 | 0,45 |
| `icon`, `check`, `cross` | la pastille pop, puis le trait se dessine | 0,2 ; 0,45 | 0,45 ; 0,5 |
| `arrow` | glisse et se pose, 0,28 s entre deux | 0,3 | 0,5 |
| `count` | compteur qui ralentit (`power3.out`), puis le libellé | 0,15 ; 0,9 | 1,1 ; 0,5 |
| `enumerate` | le nouvel item entre, les précédents passent à 55 % | 0,1 | 0,5 |
| `cols2` | ligne par ligne, 0,1 s entre deux | 0,15 | 0,45 |
| `versus` | le filet se trace, la gauche passe à ×0,82, la droite à ×1,16 | 0,15 ; 0,3 | 0,5 ; 0,7 |
| `diverge` | la flèche ↗ entre et pulse (×1,35, 1 fois), puis ↘ ; chaque sous-ligne suit | 0,35 à 1,35 | 0,25 à 0,45 |
| `punch` | mot à mot (0,2 s), puis avancée lente ×1,035 sur l'étape | 0,1 | 0,45 |
| `ref-card` | la carte, ses lignes (0,12 s), l'extrait surligné par balayage, zoom ×1,03 | 0 ; 0,2 ; 1,0 | 0,6 ; 0,45 ; 0,7 |
| image, `ref-shot` | zoom lent (×1,07 ; ×1,04) pendant toute l'étape | 0 | l'étape |
| webcam | tween du cadre et flou (`references/webcam.md`) | 0 | 0,55 |

Les tweens d'un même élément portent sur des propriétés différentes ; quand un `fromTo` en suit un autre sur le même élément (zoom de la `ref-card`), il reçoit `immediateRender: false` (voir `hyperframes-check.md`).

## Structure d'une étape (step)

```html
<section class="clip step" id="step-S05-1-0" data-step="S05.1#0" data-start="0" data-duration="10.68" data-track-index="1">
  <div class="kicker">S05 · L'analyse</div>
  <div class="stitle">Oppression ou autorité ?</div>
  <div class="zone"><div class="in" id="in-S05-1-0">
    <!-- contenu ici -->
  </div></div>
</section>
```

## Mot-clé visuel (kw)

```html
<div class="dline"><span class="dkw plain">L'oppression ?</span></div>
```
Classes : `plain` (blanc), `bleu`, `vert`, `or`, `rouge`, `dim` (grisé, opacity .6, taille réduite).

## Sous-ligne (sub)

```html
<div class="dsub">au détriment des élèves</div>
```

## Icône trait inline (icon)

```html
<span class="dico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">...</svg></span>
<span class="dico bad">   <!-- rouge -->
<span class="dico good">  <!-- vert -->
```

## Barré (strike)

```html
<span class="dstrike"><span>préparation à l'oppression</span><span class="sline1"></span><span class="sline2"></span></span>
```

## Diverge (trunk + branches)

```html
<div class="diverge">
  <div class="trunk">PRODUCTION MACHINE</div>
  <div class="branches">
    <div class="branch up"><div class="darr-big">↗</div><div class="dsub">production qui accélère</div></div>
    <div class="branch down"><div class="darr-big">↘</div><div class="dsub">compréhension humaine en retard</div></div>
  </div>
</div>
```

## Flèche (arrow / darr / darr-big)

```html
<span class="darr">→</span>
<div class="darr-big">↗</div>   <!-- branche diverge, couleur de la branche -->
```

## Chip (référence figures)

```html
<span class="chip">1975</span>
```

## Image plein écran (illustration / photo)

Pour afficher une image en plein écran (illustration, photo, capture d'écran) :

```html
<img class="fond" id="img-xxx" src="assets/images/<nom>.jpg" alt="description" style="z-index:2;">
```

CSS : `.fond` (position absolute, inset 0, object-fit cover). z-index 2 pour être au-dessus du fond BG (z-index 1) mais sous les steps (z-index 4).

Règles :
- L'image doit être en 1920×1080 (ou redimensionnée avec ffmpeg pad).
- Pas de webcam incrustée sur ces steps (`data-cam="off"`, pas de `cam-frame`).
- L'image est un `<img class="fond">`, pas un `<div class="zone">` avec du texte.
- Le `.in` n'est pas nécessaire pour ces steps (pas d'animation opacity sur le .in).

## Chiffre-clé (bignum / count)

```html
<span class="dbig"><span class="ctr" id="ctr-xxx" data-target="24">0</span></span>
```

## Tampon verdict (stamp)

```html
<span class="stamp">PIRES SCORES</span>
```

## Coche / croix (check / cross)

```html
<span class="dico good"><svg>...</svg></span>   <!-- check -->
<span class="dico bad"><svg>...</svg></span>    <!-- cross -->
```

## Versus (deux colonnes)

```html
<div class="versus">
  <div class="vcol left"><div class="dline"><span class="dkw dim">professeur autorité</span></div></div>
  <div class="vsep"></div>
  <div class="vcol right"><div class="dline"><span class="dkw rouge">guichet des savoirs</span></div><div class="dsub">l'élève égal du prof</div></div>
</div>
```

## Diverge (branches)

```html
<div class="diverge">
  <div class="trunk">Face à l'IA</div>
  <div class="branches">
    <div class="branch up"><div class="darr-big">↗</div><div class="dsub">...</div></div>
    <div class="branch down"><div class="darr-big">↘</div><div class="dsub">...</div></div>
  </div>
</div>
```

## Compare3 (3 lignes)

```html
<div class="compare3">
  <div class="c3row">...</div>
  <div class="c3row">...</div>
  <div class="c3row">...</div>
</div>
```

## Punchline (punch)

```html
<div class="clip step-punch" data-step="S09.1#3" data-i="79">
  <div class="punch-text"><span class="w">Tu</span> <span class="w">ne</span> <span class="w">peux</span> <span class="w">pas</span></div>
</div>
```

## Pièce documentaire (crop d'article / source prioritaire)

```html
<img class="doc-crop" src="assets/references/R02-lemonde-duminil-copin.png" alt="">
<div class="dsub">Le Monde, ...</div>
```

## Carte de référence (ref-card)

Page web stylisée, pour une source citée (`Rxx`). Jamais d'iframe ni de chargement réseau.

```html
<div class="ref-card" id="ref-I6-1-0">
  <div class="ref-source">Le Monde · 8 octobre 2026</div>
  <div class="ref-author">Prénom Nom</div>
  <div class="ref-title">Titre de l'article</div>
  <div class="ref-quote">« <span class="hl">extrait mis en valeur</span> suite de la citation »</div>
  <div class="ref-url">lemonde.fr/…/article</div>
</div>
```

## Capture plein écran (ref-shot)

```html
<img class="ref-shot" id="ref-xxx" src="assets/references/Rxx-nom.png" alt="description">
```
Zoom lent : `tl.fromTo("#ref-xxx", { scale: 1 }, { scale: 1.04, duration: dur, ease: "none" }, t);`. Pas de webcam sur ces étapes (`data-cam="off"`).

## Mapping scénario → primitive

| Directive scénario | Primitive HTML |
|---|---|
| `figures: Fxx` | `chip` ou `dbig` selon contexte |
| `source prioritaire Rxx; crop de l'article` | `doc-crop` (img) + `sub` source |
| `type: cards` | `.clip.step` + `.zone` centré, `.dkw` + `.dsub` |
| `type: versus` | `.versus` + `.vcol` + `.vsep` |
| `type: punch` | `.step-punch` + `.punch-text` en `--or` sur noir |
| `type: numbers` | `.dbig` compteur en `--or` + label |
| `type: bars` | `.bar` / `.bars` comparatifs |
| `type: enumerate` | `.dline` + `.dkw` + `.dsub`, 1 item/étape |
| `type: diverge` | `.diverge` + `.trunk` + `.branches` |
| `type: define` | `.dkw` puis morph vers `.versus` |
| `type: cols2` | `.zone.cols2` |
| `negate` | `.dstrike` + `.sline` |
| `count` | `.dbig` avec `data-to` |
| `causal-chain` | `.darr` entre `.dkw` |
| tampon verdict | `.stamp` |

## Webcam

Les trois modes et `applyCam` sont dans `references/webcam.md`. Ne pas recopier un bloc plus ancien (coin haut, `className`, `visibility`).

## Règle d'or

Chaque étape du scénario doit produire **au moins un élément HTML non-textuel** (image, SVG, primitive visuelle) qui illustre le concept. Jamais de sous-titre seul.

---

## Catalogue complet des opérations → primitives HTML

### A. Relations logiques et argumentatives

- `compare` → 2 `kw` face à face + `bar` sur échelle commune
- `contrast` → 2 colonnes bleu vs vert + `arrow` central
- `negate` → `strike` rouge sur la proposition
- `refute` → étape 1 : `kw` blanc ; étape 2 : `strike` + `check` vert
- `connect` → `kw` + `kw` reliés par ligne fine bleue, sans `arrow`
- `causal-chain` → `kw` + `arrow` + `kw` + `arrow` + `kw`
- `decompose` → `kw` titre puis `enumerate` des parties
- `compose` → parties puis `stamp` vert du tout
- `transform` → `kw` + `arrow` + `kw`, fond qui change
- `feedback-loop` → 3–4 `kw` en cercle + `arrow` en boucle
- `branch` → `kw` question puis 2 `kw` bleu/vert côte à côte
- `hierarchy` → `kw` empilés + indentations
- `zoom` → `kw` large puis `bignum`/`kw` détail plein écran
- `accumulate` → `enumerate` pas à pas, 1 item/étape
- `evidence` → `check` × N puis `stamp` vert conclusion
- `synthesize` → `stamp` or + `kw` modèle commun

### B. Quantité et mesure

- `enumerate` → lignes `kw` + `sub`, 1/étape
- `count` → `bignum` compteur or + label
- `proportion` → `bar` + dénominateur explicite (`sub`)
- `scale` → `bars` échelle commune, base 100
- `rank` → `bars` triées + numéros 1..N
- `threshold` → ligne seuil or + `stamp` rouge si dépassement
- `distribution` → `bars` histogramme
- `growth` / `change-over-time` → `bars` ou courbe + variation annotée
- `uncertainty` → fourchette `chip` min–max + `sub` « estimation »
- `accumulation-to-threshold` → barres qui montent puis `stamp` seuil

### C. Attention et révélation

- `highlight` → mot-clé passe en `or` + pulse 1×
- `reveal` → fragment caché puis révélé
- `conceal` → zone masquée (voile) puis dévoilée
- `focus-shift` → ancien `kw` en gris, nouveau en blanc/bleu
- `reframe` → même `kw`, nouveau `sub`
- `zoom-context` → détail puis plan large

### Gabarits à signature

- `versus` → `.versus` + `.vcol` + `.vsep` (voir balisage §versus)
- `versus` morph → `.define` puis morph vers `.versus`
- `diverge` → `.diverge` + `.trunk` + `.branches` (voir balisage §diverge)
- `seuil` → barres qui montent + `.stamp` seuil or/rouge
- `compare3` → `.compare3` + `.c3row` (voir balisage §compare3)

### Familles

- **Stats** : valeur absolue (`count`), % (`proportion`), ratio (`bars`), écart (`bars` 2 valeurs), moyenne/min/max (`sub` annoté), séries multiples (`bars` groupées), tableau (`enumerate` tabulaire), matrice (`cols2`).
- **Listes** : simple/numérotée/à puces/progressive (`enumerate`), catégorisée (`cols2` + kicker), pour/contre (bleu vs rouge), inventaire (`chip` × N).
- **Temporalité** : chronologie (`causal-chain` datée), avant/après (`transform`), fréquence (`count` + `sub` /an), simultané (2 `kw` même étape, sans flèche).
- **Systèmes** : réseau (`connect` N+N), flux (`arrow` épais), goulot (`bars` + `stamp` rouge), équilibre (2 `bars` égales).
- **Argumentation** : question (`kw` + « ? »), hypothèse (`sub` « hypothèse »), objection (`strike` + `kw` adverse), concession (`check` vert + point accordé en `kw`), définition/équation (`define`), dilemme (`branch`), paradoxe (`contrast` + `stamp` or), analogie (2 `compare` parallèles).
- **Incertitude** : fait (`check` vert) / hypothèse (`sub`) / spéculation (`sub` gris + « ? »), risque (`threshold` rouge), zone inconnue (voile).
- **Rhétorique** : accroche (`punch` or), surprise (`contrast` brusque), question ouverte (`kw` + « ? » sans réponse), récap (`synthesize`).

### Règles stats

- Échelle commune pour comparer
- Zéro explicite si tronqué
- Corrélation ≠ causalité (sinon `connect`, pas `causal-chain`)
- Jamais de chiffre inventé — données manquantes = demander la source
- 1 seule figure par étape (un `count`, ou un `seuil`, ou un `compare3`, jamais deux)
