# Inserts : extraits qui remplacent l'image et le son

Un insert est un extrait (vidéo YouTube, vidéo d'un tweet, fichier local) qui s'affiche **à la place** de la webcam et de la voix, pendant sa durée. Il s'ajoute à la coupe : le master n'est pas raccourci, la suite reprend après l'insert.

Il est posé **après le rendu**, par `scripts/post-render.py`, sur la timeline d'origine du master (`renders/full.mp4`). Le storyboard, la composition et le transcript ne changent donc jamais : rien ne se décale. Un tweet sans vidéo n'est pas un insert (voir `ref-card` et `ref-shot` dans `primitives-joriel.md`) : il ne remplace pas la voix.

## Ce qui est fourni, ce qui est décidé

| L'utilisateur fournit | L'agent décide |
|---|---|
| la source : URL de vidéo ou de tweet, ou fichier local | l'`id` de l'insert |
| le début et la fin de l'extrait dans la source (`12:40`, `1:02:03` ou secondes) | l'emplacement dans le film : une étape du storyboard |
| éventuellement le sujet (« quand il parle de… ») | la raison (`why`), une ligne |

« Rajoute ces extraits » suffit : l'agent trouve l'emplacement lui-même.

## Procédure pour l'agent

1. **Au moment du storyboard minuté**, avant la composition : pour chaque extrait, retrouver dans `transcript.json` et dans le storyboard le passage qui en parle (nom de la personne, sujet, affirmation illustrée). Choisir l'étape.
2. **Ancrer sur une étape**, jamais sur un temps : `after` (la coupe tombe à la fin de l'étape), `before` (au début), ou une scène entière (`"after": "I4"`). Les temps se déduisent du storyboard minuté.
3. Écrire `assets/inserts.json` (format ci-dessous) puis lancer `python3 "$SKILL_DIR/scripts/post-render.py" --plan`. Le plan affiche, pour chaque coupe, le temps sur le master, le temps final et le texte des deux étapes qui l'encadrent. L'utilisateur valide en lisant, sans réécouter. Un `⚠` signale une coupe qui tombe au milieu d'une étape.
4. La composition n'est pas modifiée par les inserts. Rendre le master comme d'habitude (feu vert de l'utilisateur pour le mp4).
5. Une fois `renders/full.mp4` rendu, lancer le script sans option : téléchargement, transformation, un seul graphe ffmpeg → `renders/final.mp4`. Vérifier la ligne `écrit : … (durée ; attendu …)`. En cas de doute sur un emplacement, lancer d'abord `--preview` : un clip de 11 secondes par coupe (4 s de master, 3 s d'insert, 4 s de master), en quelques secondes.

Repères de placement, à ajuster : une coupe tombe sur une fin de phrase, juste après la phrase qui annonce l'extrait ; on évite deux inserts à moins de quelques dizaines de secondes l'un de l'autre ; on n'ancre pas un insert au milieu d'une animation (c'est la raison de l'ancrage sur les étapes).

## Manifeste `assets/inserts.json`

Exemple complet : `examples/inserts.example.json`.

| Champ | Rôle | Défaut |
|---|---|---|
| `master`, `output` | entrée et sortie | `renders/full.mp4`, `renders/final.mp4` |
| `scenario` | storyboard minuté (lignes `- \`I1.1#0\` t=… (…s)`) | `assets/scenario-hyperframes.md` |
| `transform.pitch` | hauteur du son (×), durée inchangée | `1.05` |
| `transform.rotate_deg` | rotation de l'image, avec un zoom calculé qui masque les coins | `1.0` |
| `outro` | vidéo ajoutée à la fin (signature), ajustée en 1920×1080 sans transformation | aucune |
| `inserts[].id` | identifiant (lettres, chiffres, `.` `_` `-`) | obligatoire |
| `inserts[].source` | URL (yt-dlp) ou chemin local | obligatoire |
| `inserts[].start`, `end` | bornes dans la source ; sans bornes, la vidéo entière | |
| `inserts[].after` / `before` / `at` | un seul : id d'étape ou de scène, ou secondes du master (`at` sert aux essais) | obligatoire |
| `inserts[].pitch`, `rotate_deg` | réglages propres à cet insert (`1` et `0` désactivent) | `transform` |
| `inserts[].why` | raison du placement, affichée dans le plan | |

## Commandes

Depuis le dossier du projet :

```bash
python3 "$SKILL_DIR/scripts/post-render.py" --plan       # coupes résolues, rien n'est téléchargé
python3 "$SKILL_DIR/scripts/post-render.py" --preview    # clips de 11 s autour de chaque coupe
python3 "$SKILL_DIR/scripts/post-render.py"              # téléchargement + rendu final
```
Options : `--manifest FILE`, `--root DIR`, `--fetch-only`, `--force` (refait téléchargements et préparations), `--dry-run` (affiche les commandes sans les exécuter).

## Ce que fait le script

1. **Téléchargement** (`yt-dlp`, 1080p au plus) dans `assets/inserts/raw/<id>.*`, limité à la section `start`–`end`. Si la découpe à la source échoue, il retélécharge la vidéo entière et découpe en local. Un fichier déjà téléchargé n'est pas retéléchargé.
2. **Transformation** dans `assets/inserts/<id>.mp4` : découpe, ajustement en 1920×1080 (bandes noires si besoin), 30 i/s, son AAC 48 kHz stéréo (un insert sans son reçoit du silence), hauteur du son ×`pitch` à durée constante, rotation de `rotate_deg` degrés avec zoom. Le résultat est mis en cache (un `.json` mémorise les paramètres).
3. **Assemblage** : un seul graphe ffmpeg découpe le master aux points de coupe, intercale les inserts et ajoute la signature. Le master n'est encodé qu'une fois (CRF 18).
4. **Crédits** : `renders/inserts-credits.md` liste les sources et les bornes, à reprendre dans la description de la vidéo. Le recours à des extraits courts, commentés et attribués relève de la citation ; la transformation de l'image et du son ne change pas ce statut.

## Dépendances et limites

`ffmpeg`, `ffprobe`, Python 3, et `yt-dlp` (`pip install -U yt-dlp`, à tenir à jour) seulement pour les URL. Testé avec `scripts/test-post-render.sh` (médias synthétiques) et avec un serveur HTTP local ; non testé contre YouTube ou X depuis l'environnement de développement. La découpe à la source demande un serveur qui accepte les requêtes par plage ; sinon le repli (vidéo entière) s'applique.
