# Langage visuel Joriel (skill `hyperframe-joriel`)

Identité verrouillée pour tous les scénarios HyperFrames de cette skill.
**Les objets changent, les opérations restent.** Ne jamais réinventer un style
par vidéo : sélectionner dans ce catalogue, paramétrer, c'est tout.

Source palette : image de référence fournie (balle bleu/vert/noir/blanc) +
consigne : **fonds noir, éléments bleu + vert, mises en valeur or + rouge.**

---

## 1. Tokens (source unique de vérité)

```css
:root{
  --fond:#000000;        /* fond plein écran, toujours */
  --voile:rgba(0,0,0,.62); /* voile sur fond photo, 55–70 % */
  --bleu:#5B9CF6;        /* faits, structures, liens */
  --bleu-clair:#A9C7F5;  /* sous-lignes, filets, repères */
  --vert:#6FDC8C;        /* positif, solution, accumulation */
  --vert-clair:#B9EFC3;  /* variantes vert */
  --blanc:#F4F6F9;       /* texte courant */
  --gris:#9AA4B2;        /* sources, repères, secondaire */
  --or:#F0B429;          /* MISE EN VALEUR : chiffre-clé, punchline, seuil */
  --rouge:#E5484D;       /* MISE EN VALEUR : négation, alerte, dépassement */
  --bleu-sombre:#1B2B4A; /* aplats : fond des chips bleus */
  --vert-sombre:#173A26; /* aplats : fond des chips verts */
  --pastille:#E8EDF3;    /* pastille claire derrière un logo (tracé jamais altéré) */
  --gris-rappel:#6B7484; /* historique : trop sombre sur noir (contraste 2,1:1). `.dkw.dim` et `.slideno` utilisent `--gris` */
}
```

Fonds (règle tranchée v1.2.1 — voir conventions §8) :

- **Défaut : `assets/bg/BG-00.jpg`** (réseau neuronal blanc sur noir, image de
  référence du langage) + voile 62 % + zoom lent 3–6 % + fondu. **Jamais de
  noir nu** : toute scène sans fond dédié utilise BG-00.
- **Par scène : `assets/bg/BG-01..08.jpg`** du scénario (sans personne
  identifiable / logo / texte lisible), mêmes voile/zoom/fondu.
- **Seule exception : les punchlines** plein écran mot à mot restent en
  `--or` sur noir pur (contraste maximal, pas de photo derrière).

Règles impératives :

- **Fonds : voir paragraphe « Fonds » ci-dessus (BG-00 par défaut, BG-01..08
  par scène, noir pur réservé aux punchlines).** Jamais de fond blanc, jamais
  de fond uni clair, jamais de noir nu hors punchline.
- **Base écran = bleu + vert + blanc.** 1 seul sens par couleur :
  bleu = ce qui est (faits, structures), vert = ce qui aide / s'accumule /
  résout. Ne pas inverser d'une vidéo à l'autre.
- **Or + rouge = mises en valeur uniquement**, jamais en texte courant.
  1 seule mise en valeur par étape. Or = « regardez ce chiffre / cette phrase ».
  Rouge = « c'est faux / danger / seuil franchi ».
- Texte courant toujours `--blanc` sur noir (contraste AAA). Sources/repères
  `--gris` ≥ 40 px. Rien depuis le réseau (polices système uniquement,
  2 polices max, icônes et SVG en local).

Tailles à 1080p (rappel conventions, inchangées) : contenu ≥ 64 px,
titres 96–140, chiffres 260–420, punchlines 110–150.

Finitions (1.11.0, aucune teinte nouvelle) : halo de la couleur du sens sous les mots colorés (36 % d'opacité au plus), vignette noire sur les fonds (55 % au plus), filet de 4 px sous le titre de scène, pastilles rondes pour les `chip` et les pictos, tampons à double cadre.

## 2. Typographie et composition

- **Centrage par défaut : contenu centré verticalement et horizontalement**
  (titres, mots-clés, chiffres, punchlines, sources). Alignement à gauche ou
  en colonnes **uniquement quand l'élément l'exige** : `versus`, `diverge`,
  `compare3`, `cols2`, barres comparatives (labels lisibles à gauche dans un
  bloc centré). Jamais de mise en page « PPT en haut à gauche » par défaut.
- Titre scène : 96–120 px, `--blanc`, 1 ligne. Kicker section (`I1`, `S04`…)
  en `--bleu-clair` 40 px espacé au-dessus.
- Grande ligne (`kw`) : 72–84 px `--blanc`. Mot accentué : même ligne en
  `--bleu` ou `--vert` selon sens (classe `cls`).
- Sous-ligne (`sub`) : 48–56 px `--bleu-clair`, sous la grande ligne.
- Filet de séparation : 4 px `--bleu` à 30 % d'opacité entre titre et lignes.
- Listes : lignes simples sans encadré, jamais de « cartes » qui détonnent.
  ≥ 5 items → `cols2` (2 colonnes, ~4,8vh, 3 rangées max) + défilement
  de secours masqué.
- Punchline : plein écran, mot à mot, `--or` sur noir. Chiffre-clé : compteur
  `--or` 260–420 px + label `--blanc`.

## 3. Primitives (blocs — seuls autorisés)

Chaque étape = combinaison de ces blocs. Le balisage HTML est
`examples/demo/` : chaque bloc y figure une fois, avec son nom affiché à l'écran (table dans `examples/demo/README.md`).

| Bloc | Usage | Couleur |
|---|---|---|
| `kw` (+`cls`: `plain`/`bleu`/`vert`/`or`) | mot-clé visuel, grande ligne | blanc/bleu/vert/or |
| `sub` | précision, date, source courte | bleu-clair |
| `arrow` (`→`) | cause → effet, avant → après | bleu |
| `strike` | négation (barré qui se trace) | blanc barré rouge |
| `icon` (picto trait inline) | concept générique | bleu ou vert, 1 style trait |
| `brand` (SVG `thesvg` local) | logo marque, sans altération | pastille claire si besoin |
| `chip` (réf `figures.json`) | valeur courte inline | fond bleu/vert sombre, texte blanc |
| `bignum` / `count` | compteur animé plein écran | **or** |
| `bar` / `bars` | barres comparatives, échelle commune | bleu vs vert ; dépassement en rouge |
| `stamp` | tampon verdict (VRAI / FAUX / SEUIL) | vert (valide) / rouge (invalide) / or (seuil) |
| `check` / `cross` | preuve / réfutation | vert / rouge |
| `enumerate` | liste progressive, 1 item / étape, lignes `kw` + `sub` | blanc / bleu-clair |
| `punch` | accroche plein écran, mot à mot | **or** |
| `cols2` | mise en 2 colonnes (≥ 5 items, 3 rangées max à 1080p) | — (layout, pas de couleur) |
| `define` | concept statué, puis `versus` morph vers sa redéfinition | blanc, puis règles `versus` |
| `darr` | flèche qui glisse vers le bas (résultat qui apparaît) | bleu (rouge si alerte) |
| `darr-big` | flèche géante 7vh, branches `diverge` (↗ / ↘) | couleur de la branche (vert / rouge) |
| `nl` | retour ligne | — |

Interdits : nouvelle primitive ad hoc par vidéo, style « carte »,
emoji, dégradés criards, photo avec texte lisible / logo / personne
identifiable.

## 4. Grammaire de mouvement (GSAP, durées fixes)

- Entrées 0,5–1,2 s : punchlines mot à mot, listes ligne par ligne,
  compteurs (`count`), barres qui poussent (`bar`).
- Micro-animations inline à la même échelle : flèche qui glisse (`arrow`),
  barré qui se trace (`strike`), tampon qui claque (`stamp`), picto qui
  pop (`icon`), mot-clé accent qui pulse (1×, jamais en boucle).
- Le détail des mouvements, primitive par primitive (délais, durées), est dans `primitives-joriel.md`, § Mouvements.
- 1 étape = 1 apparition = 1 affichage = 1 label GSAP `SLIDE#k`.
  `python3 scripts/check-steps.py` vert exigé.
- 1 son max / étape (pops alternés / tic / carillon punchlines),
  titres silencieux, volumes 0.10–0.16 (`make-sfx.py`).

## 5. Catalogue des opérations → blocs (sélection sans improvisation)

Principe : **identifier l'intention rhétorique du fragment `note:`, puis
prendre la ligne correspondante.** Ne pas choisir au faciès.

### A. Relations logiques et argumentatives

- `compare` (comparer selon critères) → 2 `kw` face à face + `bar` ou chips
  sur échelle commune. Ex. pomme vs poire / 2 modèles IA : mêmes blocs,
  seuls les labels changent.
- `contrast` (opposition) → 2 colonnes bleu vs vert + `arrow` central.
  Ne pas utiliser `compare` quand il y a conflit.
- `negate` (nier) → `strike` rouge sur la proposition. 1 proposition / étape.
- `refute` (proposition puis preuve contraire) → étape 1 : `kw` blanc ;
  étape 2 : `strike` + `check` vert (preuve). Ne pas confondre avec `negate`
  seul (sans preuve).
- `connect` (relier sans causalité) → `kw` + `kw` reliés par ligne fine
  bleue, **sans** `arrow`. Ne jamais mettre de flèche orientée.
- `causal-chain` (A → B → C) → `kw` + `arrow` + `kw` + `arrow` + `kw`,
  1 maillon par étape. Flèche = causalité revendiquée par le discours,
  sinon `connect`.
- `decompose` (tout → parties) → `kw` titre puis `enumerate` des parties.
- `compose` (parties → tout) → parties puis `stamp` vert du tout. Inverse
  de `decompose`, ne pas les fusionner.
- `transform` (état A → état B) → `kw` + `arrow` + `kw`, fond qui change.
- `feedback-loop` (boucle) → 3–4 `kw` en cercle + `arrow` en boucle, dernier
  pas = retour au départ.
- `branch` (alternative) → `kw` question puis 2 `kw` bleu / vert côte à côte.
- `hierarchy` (niveaux) → `kw` empilés + indentations, titre en haut.
- `zoom` (ensemble → détail) → `kw` large puis `bignum`/`kw` détail plein
  écran. Ne pas utiliser pour un simple exemple.
- `accumulate` (apparition progressive) → `enumerate` pas à pas, 1 item / étape.
- `evidence` (preuves → conclusion) → `check` × N puis `stamp` vert conclusion.
- `synthesize` (synthèse) → `stamp` or + `kw` modèle commun.

### B. Quantité et mesure (données de `figures.json` uniquement)

- `enumerate` → lignes `kw` + `sub`, 1 / étape, synchro voix.
- `count` → `bignum` compteur or + label. Format `{value, label, source,
  status}` ; `verify` = pastille `?draft=1` uniquement.
- `proportion` → `bar` barre de proportion + dénominateur explicite
  (`sub` : « sur N … »). Jamais de camembert improvisé.
- `scale` → `bars` échelle commune, base 100 si besoin.
- `rank` → `bars` triées + numéros 1..N.
- `threshold` → ligne seuil or + `stamp` rouge si dépassement.
- `distribution` → `bars` histogramme, jamais réduite à la moyenne seule.
- `growth` / `change-over-time` → `bars` ou courbe chronologique, ordre
  temporel conservé, variation annotée (+x %).
- `uncertainty` → fourchette `chip` min–max + `sub` « estimation ».
- `accumulation-to-threshold` → barres qui montent puis `stamp` seuil.

Règles stats : échelle commune pour comparer, zéro explicite si tronqué,
corrélation ≠ causalité (sinon `connect`, pas `causal-chain`), **jamais
de chiffre inventé** — données manquantes = demander la source ou
illustration qualitative signalée.

### C. Attention et révélation

- `highlight` → mot-clé passe en `or` + pulse 1×. 1 seul / étape.
- `reveal` → fragment caché puis révélé (pas-à-pas natif).
- `conceal` → zone masquée (voile) puis dévoilée ; montrer les limites
  si le masquage est le sujet.
- `focus-shift` → ancien `kw` en gris, nouveau en blanc/bleu.
- `reframe` → même `kw`, nouveau `sub` qui change le cadrage.
- `zoom-context` → détail puis plan large (inverse de `zoom`).

### Familles (mêmes blocs, sens distinct — ne pas créer de doublon)

- **Stats** : valeur absolue (`count`), % (`proportion`), ratio (`bars`),
  écart (`bars` 2 valeurs), moyenne/min/max (`sub` annoté), séries multiples
  (`bars` groupées), tableau (`enumerate` tabulaire), matrice (`cols2`).
- **Listes** : simple / numérotée / à puces / progressive synchro (`enumerate`),
  catégorisée (`cols2` + kicker), pour/contre (bleu vs rouge), inventaire
  (`chip` × N).
- **Temporalité** : chronologie (`causal-chain` datée), avant/après
  (`transform`), fréquence (`count` + `sub` /an), simultané (2 `kw` même
  étape, sans flèche).
- **Systèmes** : réseau (`connect` N+N), flux (`arrow` épais), goulot
  (`bars` + `stamp` rouge), équilibre (2 `bars` égales).
- **Argumentation** : question (`kw` + « ? »), hypothèse (`sub` « hypothèse »),
  objection (`strike` + `kw` adverse), **concession** (`check` vert + point
  accordé en `kw` — valider avant de pivoter, ex. S09.1#1/#2),
  **définition/équation** (`define` : concept statué puis `versus` morph vers
  sa redéfinition, ex. S10.1#2 → S10.1#3), dilemme (`branch`), paradoxe
  (`contrast` + `stamp` or), analogie (2 `compare` parallèles).
- **Incertitude** : fait (`check` vert) / hypothèse (`sub`) / spéculation
  (`sub` gris + « ? »), risque (`threshold` rouge), zone inconnue (voile).
- **Rhétorique** : accroche (`punch` or), surprise (`contrast` brusque),
  question ouverte (`kw` + « ? » sans réponse), récap (`synthesize`).

Si aucun mapping ne convient : 1) chercher une composition existante,
2) prouver le besoin nouveau, 3) proposer l'extension **documentée**
(contrat + exemple + test) — jamais de bloc ad hoc silencieux.

## 6. Données et sélection en 5 pas (pipeline §2c)

1. Lire `note:` → nommer l'intention (1 opération du §5).
2. Chercher la ligne du catalogue → blocs + couleurs imposés.
3. Extraire paramètres : `kw` ≤ 5 mots, `sub` ≤ 8 mots, chiffres depuis
   `figures.json` (jamais du texte libre). **Une seule figure par étape**
   (un `count`, ou un `seuil`, ou un `compare3`, jamais deux).
4. Poser ces blocs dans la composition, sur le balisage de
   `examples/demo/` (table des primitives dans son README). `cols2` si ≥ 5 items.
5. Les ids du scénario sont les labels GSAP. `check-steps.py`, puis preview :
   lisible à 3 m, 1 idée / étape, zéro chevauchement écran/prompteur.

## 7. Interdits (erreurs qui disqualifient une étape)

- **Plus d'un élément nouveau par étape.** 1 étape = 1 apparition = 1 seul
  élément visuel nouveau, illustré en gros (taille max utile). Ne jamais poser
  deux éléments nouveaux sur la même étape. Le déjà-affiché peut rester en
  contexte (grisé pour un rappel `versus`, tamisé sinon). Un gabarit
  (`versus` révélation, `diverge`, `seuil`, `compare3`) compte pour un seul
  élément : c'est une figure unique, pas une collection.
- Écran qui répète le prompteur (zéro chevauchement).
- Visualisation choisie pour son look, pas pour sa question.
- Chiffre sans source, moyenne sans distribution, axe tronqué muet.
- 2 mises en valeur concurrentes (or + rouge même étape).
- Nouveau style / primitive / couleur hors tokens.
- Texte > 3 rangées à 1080p sans `cols2` ni défilement de secours.
- Son sur titre, 2 sons / étape, volume > 0.16.

## 8. Extension contrôlée

1 nouvel élément = identifiant stable + version + contrat d'entrée
+ conditions d'utilisation + exemple concret + exemple abstrait
+ test de rendu. Déprécier, ne jamais supprimer silencieusement.
Registre licences pour toute ressource externe (`thesvg`, Flux 9B,
Lucide/Tabler si importés un jour).

---

## 9. Gabarits à signature (V2 — au-delà du mapping)

Le §5 seul ne produit **aucune différence visible** quand deux opérations se
rabattent sur les mêmes blocs (ex. `compare` ≈ `contrast` → kw + bar).
Chaque gabarit ci-dessous a une signature de mise en page propre.
`versus` et `diverge` sont balisés dans `examples/demo/compositions/i05.html`
(étapes `I5.1#0` et `I5.1#1`). `seuil` et `compare3` n'ont pas de balisage
dans le dépôt (voir `SKILL.md`, « Ce que ce dépôt ne fournit pas »). Les utiliser dès que l'intention correspond.

### 9.1. `versus` — contrast / refute à deux camps

```json
{"versus": {"recall": "left",
  "left": [{"kw": "…", "cls": "dim"}, {"stamp": "TABOU"}],
  "right": [{"kw": "…", "cls": "rouge"}, {"sub": "…"}, {"cross": true}]}}
```

- Deux colonnes séparées par un filet vertical, **dans la même étape**.
- `recall: "left"|"right"` : le camp déjà dit à l'étape précédente est
  réaffiché **grisé et réduit** (rappel `--gris-rappel`, `opacity:.6`, kw 3.8vh) — ce rappel
  fait partie de l'apparition, pas une redite prompteur.
- Camp révélé : pleine taille, verdict (`stamp`/`cross`/`check`) inclus.
- **Ne jamais fusionner deux étapes** pour faire un versus : les labels
  `SLIDE#k` restent un par étape (`check-steps.py` vert exigé).
- Exemple validé : `S02.1#2` (ancien monde grisé + TABOU | compétition
  victimaire rouge + ✗).

### 9.1b. `versus` morph — variante sans doublon (prioritaire)

```json
{"versus": {"pair": "S02.1#1",
  "right": [{"kw": "…", "cls": "rouge"}, {"sub": "…"}, {"cross": true}]}}
```

- Quand le camp adverse **est déjà une étape à part entière** (annonce
  lumineuse plein format), ne PAS le recopier en rappel : le build groupe
  l'annonce et l'étape versus (`.mgroup`, labels intacts) et **l'arrivée
  anime l'annonce** — minimisée, grisée (`opacity:.6`, kw 3.8vh), rangée en
  colonne gauche face à la révélation. Reculer restaure l'annonce pleine.
- Le groupe reste en place pour la suite de la scène (`idx >= versus`) :
  le tableau devient le contexte, pas un doublon.
- Règle : **un contenu déjà affiché en grand ne réapparaît jamais en petit
  dans la même vue** — il *devient* petit par animation.
- Exemples validés : `S02.1#2` (pair `S02.1#1`), `S06.1#2` (pair `S06.1#1`,
  avant/après sans verdict).

### 9.2. `diverge` — branch / trajectoires opposées

```json
{"diverge": {"trunk": "Face à l'IA", "recall": "up",
  "up": {"kw": "…", "cls": "vert", "sub": "…"},
  "down": {"kw": "…", "cls": "rouge", "sub": "…"}}}
```

- Tronc commun (`sub`), puis deux branches : `↗` verte / `↘` rouge,
  flèches géantes (7vh) propres au gabarit.
- `recall` grise la branche déjà montrée à l'étape précédente.
- Branches = blocs `kw` + `sub` uniquement (pas de `stamp`, la divergence
  n'est pas un verdict).
- Exemple validé : `S08.3#2` (tronc IA, ↗ lire·prompter·vérifier en rappel,
  ↘ copie-colle en révélation).

### 9.3. `seuil` — threshold / accumulation-to-threshold

```json
{"seuil": {"fig": "F42", "repere": "+2 % · enseignants stables",
  "repere_val": 2, "verdict": "DÉPASSEMENT", "sens": "bad",
  "sub": "non-enseignants"}}
```

- Piste commune à double lecture : tick blanc = repère (valeur + label),
  remplissage animé (`data-w` calculé, même hook GSAP que `bars`) = valeur.
- Le **verdict colore le chiffre** (`dbig.bad/good`, compteur animé
  `data-to` conservé) : `bad` → rouge, `good` → vert, `neutre` → or.
  Règle V1 affinée : un `count` avec verdict prend la couleur du verdict
  (1 seule famille d'accent par étape : chiffre + tampon même couleur).
- Préconditions : **un seul nombre** dans la figure (pas de fourchette) ;
  `repere_val` numérique ; échelle auto `max(valeur, repère) × 1.06`
  (jamais d'axe tronqué muet : le repère est labellisé).
- Exemple validé : `S04.3#2` (+57 % explose le repère +2 %, DÉPASSEMENT).

### Règles communes aux gabarits

- Contenu : `kw` ≤ 5 mots, `sub` ≤ 8 mots, chiffres depuis `figures.json`.
- Micro-animations et sons hérités du générique (pop/tic, `stamp` qui
  claque, `darr-big` qui glisse comme `darr`) — aucun nouveau son.
- Pastille `verify` : portée par le gabarit lui-même (pas de doublon).
- **Unités hétérogènes** (absolus vs %) : jamais de piste commune —
  `compare3` (compteurs directionnels, unités natives labellisées), jamais
  de barres à échelles indépendantes (trompeur, interdit §7).
- **Sources non vérifiées** : exclues de la ligne « Source : » (pastille
  `?draft=1` + badge suffisent) ; à vérifier en draft avant de passer `ok`.

### 9.4. `compare3` — comparaison à 3 séries hétérogènes

```json
{"compare3": {"absorb": "S04.3#1", "verdict": "DÉPASSEMENT",
  "rows": [
    {"icon": "trend-down", "kw": "−250 000 élèves", "cls": "bleu", "sub": "effectifs en baisse"},
    {"icon": "arrow-r", "kw": "≈ stables", "cls": "bleu", "sub": "+2 % · enseignants"},
    {"icon": "trend-up", "kw": "+57 %", "cls": "rouge", "sub": "non-enseignants"}]}}
```

- 3 compteurs directionnels (picto tendance + valeur native + sous-ligne),
  verdict (`stamp`) optionnel en fin de tableau.
- `absorb: <id>` : l'étape annonce est **repliée en animé** quand le tableau
  arrive (et reste repliée pour la suite de la scène) — jamais de doublon
  annonce + tableau. Reculer la restaure.
- Précondition : chaque valeur sourcée (`figures.json`) ; toute figure
  `verify` donne badge + pastille draft (ex. F46 « à vérifier » : le dire
  comme tel au prompteur, ne pas la passer `ok` sans source).
- Exemple validé : `S04.3#2` (élèves ↓ / enseignants → / non-enseignants ↗,
  absorb `S04.3#1`).

---

*V1 : tokens + mapping sur le moteur existant. V1.1 : 3 gabarits à
signature (`versus`, `diverge`, `seuil`). V1.2 : `versus` morph sans doublon
(`pair`), `compare3` hétérogène (`absorb`), règle unités/sources. V1.2.1 :
blocs manquants spécifiés (`enumerate`, `punch`, `cols2`, `define`,
`darr`/`darr-big`), règle fonds tranchée (BG-00 par défaut), tokens
d'aplat (`bleu/vert-sombre`, `pastille`, `gris-rappel`). V1.2.2 : règle
« un élément nouveau par étape » (§7 + §6). Voir §9.
Familles supplémentaires et planches de validation : ajouts contrôlés, sans
remise en cause des tokens ci-dessus.*
