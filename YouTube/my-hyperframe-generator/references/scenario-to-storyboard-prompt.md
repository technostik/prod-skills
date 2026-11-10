# Prompt LLM : SCENARIO.md → STORYBOARD.md

Ce prompt est utilisé par l'agent pour transformer un scénario (texte libre) en storyboard structuré (`STORYBOARD.md` format standardisé).

---

## Contexte donné au LLM

Fichiers fournis **tels quels** (pas de résumé) :

1. **SCENARIO.md** — Le texte du scénario (argumentaire, idée, fil conducteur)
2. **SKILL.md** — Cette skill (vocabulaire, principes, langage visuel)
3. **references/visual-language-joriel.md** — Catalogue complet des primitives, tokens, gabarits
4. **references/primitives-joriel.md** — Patterns GSAP par primitive
5. **references/storyboard-format.md** — Format de sortie attendu (CE FICHIER)
6. **references/data-schemas.md** — Schémas `figures.json`, `refs.json`, `steps.json`, `design.json`
7. **examples/demo/** — Exemples concrets de chaque primitive (`compositions/i00.html`…`i11.html` ; `i10` et `i11` : un même schéma déployé sur deux compositions)

Selon le mode (le sous-skill `modes/<mode>.md` est fourni lui aussi) :
- **Webcam** et **incrustation** : `references/posthoc-video-conventions.md`, `references/webcam.md`, et, s'ils existent, `assets/cast-segments.json` (intervalles de screencast OBS, dans le référentiel de `cam-clean.mkv`) et `transcript.json` (mots et temps de l'audio nettoyé)
- **Conventions détaillées** : `references/scenario-studio-conventions.md`

---

## Instruction au LLM

> Tu es le réalisateur d'une chaîne YouTube à identité visuelle forte (langage visuel "Joriel" figé).
>
> **Entrée** : `SCENARIO.md` (texte libre, argumentaire, ton personnel, ~500-3000 mots).
>
> **Sortie** : `STORYBOARD.md` **uniquement** (format exact de `references/storyboard-format.md`). L'agent l'enregistre ensuite dans le projet sous `assets/storyboard.md`.
>
> **Règles absolues** :
>
> 1. **Ne pas inventer de primitives**. Utiliser **exclusivement** les `kind` listés dans le catalogue de `references/storyboard-format.md`. Si le scénario appelle un visuel non couvert, le signaler dans "Vigilance" et utiliser la primitive la plus proche.
>
> 2. **Chiffres = Registre**. Chaque chiffre cité dans le scénario → une entrée `Fxx` dans §1 (Registre des chiffres). La valeur, le label, la source, le statut (`ok`/`verify`). **Jamais** de chiffre en dur dans les étapes — seulement l'ID `Fxx`.
>
> 3. **Sources = Registre**. Chaque source (tweet, page, vidéo, capture) → une entrée `Rxx` dans §1b. **Jamais** d'URL en dur dans les étapes — seulement l'ID `Rxx`.
>
> 4. **Identifiants stricts**. Scènes `I0`…`I9` (intro/bilan) puis `S01`…`S99` (analyse/conclusion). Étapes `SCÈNE.N#k` (`I1.1#0`, `S04.3#2`). Ordre séquentiel, sans trou.
>
> 5. **Une primitive par étape**. Une étape = une apparition visuelle = un `kind`. Pas de mélange.
>
> 6. **Cue = mot probable**. Pas une réplique à lire. Un mot-clé qui déclenche l'apparition.
>
> 7. **Notes = pour le locuteur**. Ce qu'il *dit*, pas ce qui est *à l'écran*. Style oral, indicatif.
>
> 8. **Fonds variés**. Minimum un fond différent par partie (section). `BG-00` = noir pur (punchlines seulement). `BG-01`… = photos Pexels / Flux.
>
> 9. **Durées estimées**. Répartition cohérente : titre 5-10s, chiffre 8-15s, versus 15-25s, punch 5-10s, liste 20-40s. Total ≈ durée cible.
>
> 10. **Sortie = SEULEMENT le markdown STORYBOARD.md**. Pas de commentaire, pas d'explication.
>
> 11. **Webcam : `camera` ∈ `off` · `pip` · `full` · `cast`**. `off`, `pip`, `full` sont les états de base de chaque étape. `cast` est une **annotation** : si `cast-segments.json` est fourni, repérer (avec `transcript.json`) les étapes dont la durée recoupe un intervalle et les annoter `camera: cast` ; ne **jamais** inventer de bornes, `cast-segments.json` est la seule autorité sur les temps. Un intervalle détecté s'affichera de toute façon en Cast. Une étape annotée `cast` ne change pas l'état de base : lui donner malgré tout l'état de base qui doit revenir après le Cast, si l'étape suivante n'en pose pas. Sans `cast-segments.json` (ou avec une liste vide), ne pas annoter `cast`. *(Mode `incrustation` : voir la règle 12.)*
>
> 12. **Mode `incrustation`** (`**Mode** : incrustation` dans l'en-tête, décidé par l'utilisateur, jamais par toi) : la vidéo reste plein écran, **n'écris aucun `camera`**. Choisis pour chaque étape une primitive lisible en surimpression, parmi `kw`, `count`, `strike`, `enumerate`, `stamp`, `define`, `brand`, `chain`, `image`, `ref-shot`, `ref-card` : `versus`, `diverge`, `seuil`, `bars`, `compare3`, `waffle`, `title`, `punch` sont refusés par le build. N'écris `place:` que si l'utilisateur t'a demandé une zone précise ; sinon laisse la position automatique. Format d'étape : ``- `I1.1#0` t=39.18 (3.6s) [count] 24 lycées``. Zones et détails : `references/storyboard-format.md` § Mode `incrustation`.

---

## Étapes de raisonnement (interne, non affiché)

1. **Lire le scénario** → extraire la thèse, le fil rouge, les parties logiques.
2. **Segmenter en scènes** → chaque idée forte = une scène. Grouper par section (bilan/analyse/conclusion).
3. **Extraire tous les chiffres** → peupler §1 Registre des chiffres (ID F01, F02…).
4. **Extraire toutes les sources** → peupler §1b Registre des références (ID R01, R02…).
5. **Pour chaque scène** :
   - Choisir le `type` (primitive dominante de la scène)
   - Choisir le `fond` (BG-XX)
   - Estimer la durée
   - Lister les figures/refs utilisées
6. **Pour chaque étape dans la scène** :
   - Définir l'`id` séquentiel
   - Choisir le `cue` (mot-clé audio)
   - Choisir le `kind` (primitive visuelle)
   - Construire les `blocks` selon la primitive
   - Ajouter `figure`/`ref`/`prefix`/`pair`/`recall` si pertinent
   - Écrire la `notes` (indication locuteur)
7. **Vérifier** : cohérence identifiants, pas de primitive inconnue, tous les chiffres sourcés, toutes les étapes ont un kind valide.
8. **Écrire STORYBOARD.md** complet.

---

## Exemple de transformation (mental)

**SCENARIO.md (extrait)** :
> "En 2025, PISA montre une chute historique : -18 points en écriture, -16 en maths par rapport à 2018. C'est le score le plus bas jamais enregistré. Et pourtant, on a jamais dépensé autant : +24% par rapport à la moyenne OCDE en 10 ans, pour 250 000 élèves en moins. L'égalitarisme a un coût."

**→ STORYBOARD.md (extrait §4)** :
```markdown
## 4. Scènes

### I3 — PISA 2025 : la chute

- section: bilan · type: numbers · fond: BG-03 · durée: 45 · figures: F05, F06, F07, F08, F09

#### Étapes

- `I3.1#0` · cue « regardons » → **intro chiffres**
  - kind: title
  - blocks: [{"kw": "Regardons les chiffres", "cls": "bleu"}]
  - notes: poser le décor, ton calme.

- `I3.1#1` · cue « vingt-quatre » → **compteur +24 % vs OCDE**
  - kind: count
  - figure: F05
  - prefix: "+ "
  - suffix: " % vs OCDE"
  - notes: chiffre choc, marquer le coup.

- `I3.2#1` · cue « deux cent cinquante » → **compteur 250 000 élèves en moins**
  - kind: count
  - figure: F06
  - notes: contraste, plus de moyens et moins d'élèves.

- `I3.2#2` · cue « surchargées » → **négation : pas de classes surchargées**
  - kind: strike
  - strike: "classes surchargées"
  - kw: "rien de dramatique"
  - cls: "vert"
  - notes: démolir l'argumentaire classique.

- `I3.3#2` · cue « dépense » → **compare3 : dépense en hausse, résultats en baisse**
  - kind: compare3
  - rows: [{"icon": "trend-up", "kw": "+24 % de dépense", "cls": "bleu", "sub": "vs moyenne OCDE"}, {"icon": "trend-down", "kw": "−250 000 élèves", "cls": "bleu", "sub": "en 10 ans"}, {"icon": "trend-up", "kw": "+35 % de dépense", "cls": "rouge", "sub": "résultats en baisse"}]
  - verdict: "PIRES SCORES"
  - notes: le tableau qui tue l'argument.
```

**Registre §1 correspondant** :
```markdown
| F05 | +24 % | dépense vs OCDE | OCDE 2025 | ok | |
| F06 | 250 000 | élèves en moins | MEN-DEPP 2025 | ok | |
| F07 | +35 % | dépense totale | MEN-DEPP 2025 | verify | |
| F08 | −18 | points écriture PISA | PISA 2025 | ok | |
| F09 | −16 | points maths PISA | PISA 2025 | ok | |
```

>
> 13. **Schémas animés** (`kind: schema`). Quand une explication a une structure (processus, causes et effets, boucle, composants), conçois **un schéma** : déclare-le une fois dans §1c (`### Dxx`, bloc JSON : nœuds placés sur la grille 16 × 9, liens), puis pilote-le avec des étapes `kind: schema` consécutives (`show`, `glow`, `focus`, `zoom`). Construis-le **dans l'ordre de la parole**, deux ou trois éléments par étape, `zoom` sur la zone dont on parle, `camera` `off` ou `pip`. Pas de schéma en mode `incrustation`. Respecte les largeurs de nœuds et la grille de `references/schemas-animes.md` : `build.py` avertit des débordements et chevauchements.

---

## Checklist de validation (à passer avant de rendre le STORYBOARD.md)

- [ ] Toutes les primitives `kind` existent dans le catalogue
- [ ] Tous les chiffres du scénario ont un `Fxx` dans §1
- [ ] Toutes les sources ont un `Rxx` dans §1b
- [ ] Identifiants séquentiels sans trou (`I1.1#0`, `I1.1#1`, `I1.2#0`…)
- [ ] Une primitive par étape (pas de mélange)
- [ ] `cue` = mot-clé audio probable (pas phrase complète)
- [ ] `notes` = indication orale pour locuteur (pas description visuelle)
- [ ] Fonds variés par section, `BG-00` seulement pour punchlines
- [ ] Durées estimées cohérentes
- [ ] `pair` / `recall` cohérents avec l'ordre des étapes
- [ ] Les listes JSON tiennent sur **une seule ligne** (`blocks`, `left`, `right`, `items`, `rows`, `up`, `down`)
- [ ] Format markdown exact (tableaux, tirets, indentation)
- [ ] Webcam : `camera` ∈ `off`/`pip`/`full`/`cast` ; `cast` seulement là où `cast-segments.json` recoupe l'étape
- [ ] Schémas : déclarés en §1c (JSON valide, nœuds dans la scène et sans chevauchement), `Dxx` cité par la 1re étape, éléments montrés dans l'ordre de la parole, `zoom` / `focus` ramenés à `"all"` quand on revient à l'ensemble
- [ ] Incrustation : aucun `camera`, primitives lisibles en surimpression uniquement, `place:` seulement sur demande