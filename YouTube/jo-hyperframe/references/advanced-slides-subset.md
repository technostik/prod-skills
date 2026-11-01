# Sous-ensemble Advanced Slides supporté par `build_studio_slides.py`

Basé sur un deck réel de l'auteur (non fourni).
Tout ce qui n'est pas ci-dessous est ignoré sans erreur (jamais de crash de build).

## Structure

- **Frontmatter** YAML entre `---` en tête de fichier (`theme`, `transition`,
  `controls`, …) : lu et rappelé en commentaire HTML, **sans effet** sur le rendu
  (le thème du studio est fixe : sombre, centré).
- **Séparateur de slides** : ligne contenant uniquement `---`.
- **`note:`** : une ligne contenant exactement `note:` (insensible à la casse).
  Tout ce qui suit, jusqu'au prochain `---`, va au **prompteur uniquement**
  (texte brut, jamais projeté). Absent → prompteur affiche `(pas de notes)`
  et le build le signale.

## Contenu projeté (markdown → HTML, au build)

| Syntaxe | Rendu présentation |
|---|---|
| `#`, `##`, `###` | h1 / h2 (accent) / h3 (kicker espacé) |
| `- ` / `* ` / `1. ` | listes (chaque item fragmentable, voir ci-dessous) |
| `**gras**`, `*italique*`, `` `code` `` | inline, `**gras**` en accent |
| `![alt](src)` (1ʳᵉ image) | **fond photo** plein écran (retirée du contenu) |
| `<small>`, `<split …>`, tout bloc commençant par `<` | passthrough HTML tel quel |
| `<!-- texte -->` (commentaire simple) | **non projeté** ; le dernier de < 80 car. devient le **kicker** (ex. `<!-- I1 : … -->` après `<!-- PARTIE 1 … -->` → kicker = `I1 : …`) |
| `<!-- img: fichier.jpg -->` | **fond photo** plein écran (prioritaire sur `![]()`) |

## Fragments (pas-à-pas, granularité Reveal.js)

Suffixer une ligne avec `<!-- element class="fragment" -->` en fait une étape :
Avance la révèle, Recule la masque. Ordre = ordre d'apparition (`data-fi=1..n`).
Les lignes non marquées sont toujours visibles. Cas couverts : titres, paragraphes,
items de liste (un item = une étape), lignes dans `<split>`.

## Volontairement non supporté (v1)

- Fragments imbriqués / index explicites (`data-fragment-index`), animations
  d'arrière-plan, transitions par slide, `grid`/`drag` avancés, footnotes,
  numéros de slide (`slideNumber`), exports PDF : tout est ignoré, le contenu
  texte reste affiché en une fois.
