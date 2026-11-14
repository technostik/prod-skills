# Shorts de promotion

En écrivant le storyboard, le LLM **propose trois séquences** de la vidéo, **3 minutes au plus chacune**, parmi les plus
percutantes, pour en faire la promo. Elles sont déclarées dans la section `## 6. Shorts` du storyboard ; `build.py` en tire
`data/shorts_segments.json`, au format que lit la commande `video short-extractor` de fast-market.

## Déclarer : `## 6. Shorts`

```markdown
## 6. Shorts

| ID | Titre | Début | Fin | Pourquoi |
|---|---|---|---|---|
| SH01 | La métaphore du pistolet chargé : technologie vs maturité | I1.1#0 | I1.1#3 | l'image qui ouvre la vidéo, comprise sans contexte |
| SH02 | Le wokisme comme refus de la maturation | I3.2#0 | I3.2#4 | la thèse la plus clivante, argumentée en 30 s |
| SH03 | La technosophie : prendre en charge notre maturité face aux IA | S05.1#2 | S05.1#5 | la chute et la promesse |
```

| Colonne | Sens |
|---|---|
| `ID` | `SH01`, `SH02`, `SH03` |
| `Titre` | l'**accroche** du short (≤ 100 caractères) : ce qui fait cliquer. Les fichiers de sortie sont nommés d'après lui |
| `Début` | une **étape** (le short démarre au début de cette étape), une **scène** (à son début), ou un **timecode** (`00:09:10,040`, `9:10`, `550`) |
| `Fin` | une **étape** (le short s'arrête à la **fin** de cette étape), une **scène** (à sa fin), ou un **timecode** |
| `Pourquoi` | une phrase : pourquoi cette séquence est percutante (pour le relecteur ; non exporté) |

Citer des **étapes** plutôt que des timecodes : les temps se résolvent sur la timeline mesurée, et suivent si le storyboard bouge.

## Choisir les trois séquences

1. **Les plus percutantes**, pas les plus représentatives : une punchline, une métaphore forte, un chiffre choc, un renversement,
   une thèse tranchée qui s'argumente en une minute. Les étapes `punch`, `count`, `versus` et `diverge` du storyboard sont des
   candidates naturelles.
2. **Autonomes** : comprises sans avoir vu le reste. Pas de « comme on l'a vu », pas de renvoi à une scène précédente.
3. **Une accroche dans les trois premières secondes** : le short démarre sur l'idée, pas sur un « donc » ou une mise en contexte.
4. **Une chute** : il se termine sur une phrase qui conclut ; jamais au milieu d'un raisonnement.
5. **Durée** : 20 à 60 s est l'idéal ; **180 s au plus** (le build refuse au-delà), 10 s au moins.
6. **Trois séquences différentes** : pas de chevauchement, et trois idées différentes (par exemple une métaphore, une thèse, la
   conclusion), pour que chacune amène un public différent vers la vidéo.

## Ce que fait `build.py`

- Résout chaque `Début` / `Fin` en temps sur la timeline du master.
- **Cale** le début sur le début de phrase le plus proche (jusqu'à 4 s en arrière) et la fin sur la fin de phrase la plus proche
  (jusqu'à 4 s en avant), d'après le transcript : un short ne coupe jamais une phrase. Sans phrase proche : avertissement « à vérifier ».
- **Refuse** (le build s'arrête) un short de plus de 3 minutes, ou dont la fin précède le début.
- **Avertit** : moins ou plus de trois shorts, séquences qui se chevauchent, moins de 10 s, titre trop long.
- Écrit `data/shorts_segments.json`, exactement :

```json
[
  {"title": "La métaphore du pistolet chargé : technologie vs maturité", "start": "00:00:00,000", "end": "00:01:04,480"},
  {"title": "Le wokisme comme refus de la maturation", "start": "00:09:10,040", "end": "00:09:37,320"},
  {"title": "La technosophie : prendre en charge notre maturité face aux IA", "start": "00:15:29,400", "end": "00:15:56,000"}
]
```

`**Shorts** : aucun` dans l'en-tête du storyboard, ou `build.py --no-shorts`, désactive (et supprime un plan périmé).

## Extraire les shorts

Les temps de `data/shorts_segments.json` sont ceux du **master**. Sans inserts, la vidéo finale a la même timeline :

```bash
video short-extractor renders/final.mp4 --segments data/shorts_segments.json --layout fit-blur --output-dir shorts/
```

Avec des inserts (`post-render.py`), la vidéo finale est plus longue : `scripts/shorts-export.py --inserts assets/inserts.json` écrit
`renders/shorts_segments.json` décalé sur la timeline de `renders/final.mp4`, et affiche la commande à lancer.

`video short-extractor` nomme les fichiers de sortie d'après le titre, sinon les numérote ; `--layout fit-blur` est le cadrage
vertical sur fond flou.
