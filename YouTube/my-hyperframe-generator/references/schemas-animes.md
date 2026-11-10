# Schémas animés (`kind: schema`)

Un schéma qui **se construit au fil de la voix** : on déclare le schéma une fois, puis chaque étape
fait apparaître, éclaire, isole ou cadre une partie. Contrairement aux autres primitives, dont
chaque étape repart de zéro, **l'état du schéma persiste d'une étape à la suivante**.

Le LLM conçoit le schéma à partir du scénario ; un script le met en page et l'anime. Aucun
langage à apprendre : un bloc JSON dans le registre §1c, et quatre clés dans les étapes.

Code : `scripts/schema_anim.py` (modèle, géométrie, état), `scripts/render_primitive.py`
(`schema_group`), `scripts/build.py` (registre, regroupement des étapes). Tests :
`scripts/test-schema.py`.

## Quand l'utiliser

- Une explication qui a une **structure** : étapes d'un processus, causes et effets, boucle de
  rétroaction, composants et leurs relations, parties d'un tout.
- Quand l'idée se comprend **en voyant les éléments s'ajouter dans l'ordre où on les dit**.
- Pas pour une liste (`enumerate`), une comparaison à deux (`versus`), un chiffre (`count`).
- Plein cadre seulement : **refusé en mode `incrustation`** (illisible dans un quart d'écran).

## Déclarer le schéma : registre §1c

````markdown
## 1c. Registre des schémas

### D01 — Le Grand Filtre

```json
{
  "nodes": [
    {"id": "vie", "label": "Apparition\nde la vie", "x": 1.9, "y": 3, "cls": "bleu", "size": "s", "group": "passe"},
    {"id": "intel", "label": "Intelligence", "x": 5.5, "y": 3, "cls": "vert", "size": "s", "group": "passe"},
    {"id": "filtre", "label": "Le Grand Filtre", "sub": "devant nous ?", "x": 10.1, "y": 6.6, "cls": "rouge", "size": "l"}
  ],
  "edges": [
    {"from": "vie", "to": "intel"},
    {"from": "intel", "to": "filtre", "label": "durée L", "cls": "rouge", "manual": true}
  ]
}
```
````

Un en-tête `### Dxx — Titre`, puis un bloc JSON. Le JSON peut tenir sur
plusieurs lignes : la règle « une seule ligne » ne vaut que pour les paramètres des étapes.

### Nœuds (`nodes`)

| Clé | Sens |
|---|---|
| `id` | identifiant court, **unique**, utilisé dans les étapes (insensible à la casse) |
| `label` | texte du nœud ; `\n` pour couper la ligne (sinon coupé automatiquement au-delà de 720 px) |
| `sub` | sous-titre en texte romain, plus petit (optionnel) |
| `x`, `y` | **centre** du nœud sur une grille 16 × 9 (1 unité = 120 px). `x` de 0 à 16, `y` de 0 à 9 |
| `cls` | `plain` (défaut), `bleu`, `vert`, `or`, `rouge`, `dim` : couleurs du langage visuel |
| `size` | `s` (40 px), `m` (52 px, défaut), `l` (68 px) |
| `group` | nom de groupe, pour désigner plusieurs nœuds d'un coup (`@nom`) |

### Liens (`edges`)

| Clé | Sens |
|---|---|
| `from`, `to` | ids de nœuds |
| `label` | étiquette, posée **au-dessus** du lien |
| `cls` | couleur (défaut : `plain`, gris clair) |
| `dir` | `->` (défaut), `<->`, `--` (sans pointe) |
| `curve` | courbure, de -1 à 1 (0 = droit) : utile pour une boucle de rétroaction |
| `manual` | `true` : le lien n'apparaît pas tout seul, il faut le nommer dans `show` |
| `id` | identifiant explicite (défaut : `from>to`) |

Par défaut un lien apparaît **dès que ses deux nœuds sont visibles**, juste après eux. Mettre
`manual: true` pour le faire arriver plus tard, ou ne jamais l'afficher automatiquement.

### Placer les nœuds sur la grille

Un nœud est large : à `size: m`, comptez **≈ 0,25 unité par caractère de la ligne la plus longue,
plus 0,75** ; `s` ≈ 0,19 par caractère + 0,75 ; `l` ≈ 0,32 par caractère + 0,8. Hauteur ≈ 1 unité
par ligne.

- « Intelligence » à `m` ≈ 3,7 unités. **Quatre nœuds sur une ligne ne tiennent qu'en `s`** ;
  au-delà, passer sur deux rangées.
- Laisser **≥ 1,2 unité** entre deux nœuds reliés (flèche visible), davantage si le lien a une
  étiquette (≈ 0,0 + 0,17 × caractères d'étiquette).
- Rester dans `x` ∈ [0,8 ; 15,2] et `y` ∈ [0,7 ; 8,3].
- **Max ≈ 8 nœuds** par schéma. Au-delà : un second schéma, ou `zoom` pour détailler une zone.
- `build.py` **avertit** d'un nœud hors scène, de deux nœuds qui se chevauchent, d'une étiquette
  plus large que son lien. Ces avertissements sont des erreurs de mise en page : les corriger.

## Piloter le schéma : les étapes

Les étapes d'un schéma sont des étapes `kind: schema` **consécutives** ; la première nomme le
schéma, les suivantes le reprennent.

```
- `S02.1#0` · cue « apparition » → **la vie apparaît**
  - kind: schema
  - schema: D01
  - show: ["vie", "intel"]
- `S02.1#1` · cue « durée » → **la technologie, puis la durée L**
  - kind: schema
  - show: ["tech"]
  - glow: ["tech"]
- `S02.1#2` · cue « devant nous » → **le filtre, isolé**
  - kind: schema
  - show: ["filtre", "intel>filtre"]
  - zoom: ["filtre", "tech"]
  - focus: ["filtre", "tech"]
- `S02.1#3` · cue « au total » → **retour à l'ensemble**
  - kind: schema
  - zoom: "all"
  - focus: "all"
```

| Clé | Effet |
|---|---|
| `schema` | `Dxx`. Obligatoire sur la 1re étape ; les suivantes de la scène le reprennent si absent |
| `show` | éléments qui **apparaissent** : nœud (pop), lien (tracé). Les liens dont les deux nœuds sont visibles suivent seuls (sauf `manual`) |
| `glow` | coup de projecteur sur des éléments **déjà visibles** |
| `focus` | ces éléments restent pleins, **tout le reste visible passe en retrait** (25 %), jusqu'au prochain `focus`. `"all"` rétablit tout |
| `zoom` | la caméra cadre ces éléments (zoom jusqu'à 2,4×). `"all"` revient à la vue d'ensemble. Absent : la caméra ne bouge pas |

**Références** : `vie` (un nœud) · `vie>intel` (un lien, par ses nœuds, ou son `id`) · `@passe` (un
groupe : ses nœuds et les liens entre eux) · `"all"` (tout). Une liste JSON, ou `"vie, intel"`.

### Règles de mise en scène

1. **Construire dans l'ordre de la parole.** Ce qui est dit en premier apparaît en premier ; un
   élément ne se montre jamais avant d'être évoqué.
2. **Une idée par étape.** Une étape qui fait apparaître cinq nœuds fait apparaître cinq mots d'un
   coup : le spectateur ne suit plus. Deux ou trois éléments par étape au maximum.
3. **`zoom` pour la lisibilité, pas pour le spectacle.** Un schéma complet est petit : quand on
   parle d'une zone, la cadrer. Revenir à `"all"` quand on revient à l'ensemble.
4. **`focus` pour opposer ou isoler.** Il ne dure que jusqu'à un nouveau `focus` ; ne pas oublier
   `"all"` pour sortir du retrait.
5. **`glow` pour accentuer** ce qui vient d'être dit, pas pour décorer.
6. **Camera `off` ou `pip`** pendant un schéma. `full` (webcam au centre) recouvre le schéma : le
   build avertit.
7. **Un schéma peut revenir.** Une étape `kind: schema` plus tard (même scène après une autre
   primitive, ou une autre scène) qui nomme le même `Dxx` retrouve **ce qui était déjà affiché**,
   sans le redessiner. Le zoom et le focus, eux, repartent de zéro.
8. Un schéma illustre ce qui est dit : **aucun texte éditorial n'est écrit par le script**. Les
   libellés viennent du registre ; le texte dit reste dans `notes`.

## Exemple : un schéma sur deux compositions

Un schéma peut traverser une frontière de scène. Chaque scène reste une composition séparée
(`compositions/iNN.html`), mais `build.py` reporte les éléments déjà montrés : la seconde scène
réaffiche le schéma avec **ce qui était là**, sans le redessiner. Le zoom et le focus, eux,
repartent de zéro (leurs valeurs ne sont pas reportées).

```markdown
### I10 — La chaîne (1/2)

- `I10.1#0` · cue « budget » → **le budget, puis les postes**
  - kind: schema
  - schema: D01
  - show: ["budget", "postes"]

- `I10.1#1` · cue « classe » → **l'argent arrive-t-il en classe ?**
  - kind: schema
  - show: ["classe", "postes>classe"]
  - zoom: ["postes", "classe"]

### I11 — La chaîne (2/2)

- `I11.1#0` · cue « résultat » → **le niveau, isolé**
  - kind: schema
  - schema: D01
  - show: ["niveau", "classe>niveau"]
  - zoom: "all"
  - focus: ["classe", "niveau"]

- `I11.1#1` · cue « au total » → **tout reprend sa place**
  - kind: schema
  - focus: "all"
  - glow: ["postes>classe"]
```

Points à retenir :

- La première étape schéma de chaque scène **nomme** le schéma (`schema: D01`) ; le `last` qui
  permet de l'omettre ne vaut que dans une scène.
- `I11.1#0` ne montre que `niveau` et `classe>niveau` : `budget`, `postes`, `classe` et les liens
  déjà tracés sont visibles d'emblée.
- Le rendu coupe d'une composition à l'autre : si la scène précédente finissait zoomée, la
  suivante rouvre en vue d'ensemble. Écrire `zoom: "all"` quand on veut être sûr de la reprise.
- Exemple vivant : `examples/demo/` scènes `I10` et `I11` (`compositions/i10.html`, `i11.html`).

## Ce que `build.py` fait

- Les étapes schéma consécutives d'une même scène et d'un même schéma deviennent **un seul clip**
  (sinon rien ne persisterait) ; chaque étape garde son identifiant, son numéro en bas à gauche et
  son label GSAP, donc `check-steps.py` et le recalage sur le transcript fonctionnent comme avant.
- Le schéma est écrit dans `data/schemas.json` (boîtes calculées, pour contrôle).
- Un schéma absent du registre, ou un JSON invalide, **arrête le build** avec un message qui nomme
  l'étape ou le schéma.
- Mode webcam : la caméra de chaque étape (`off`/`pip`/`full`) est appliquée à chaque étape du
  groupe, comme pour les autres primitives.
