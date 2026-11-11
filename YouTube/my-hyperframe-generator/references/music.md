# Musique

De la musique **pour souligner**, jamais pour accompagner. Les moments forts (une montée en puissance, un
point culminant, la conclusion) en ont ; le reste du film n'en a pas. Style : épique, orchestral,
instrumental.

Sauf instruction contraire, la musique est ajoutée au résultat final, **sous la voix, sans jamais la
surpasser**.

## Où elle vit

| Étape | Qui | Quoi |
|---|---|---|
| Déclarer | le LLM, dans le storyboard | registre §1d + `music:` sur des étapes |
| Planifier | `build.py` | `data/music.json` : un repère par `music:`, avec ses temps |
| Générer | `scripts/make-music.py` | `sound music` (fast-market) → `assets/music/Mxx-<hash>.wav` |
| Mixer | `scripts/mix-music.py` | `renders/full.mp4` → `renders/full-music.mp4` (voix + musique) |
| Publier | `scripts/post-render.py` | part de `renders/full-music.mp4` s'il existe |

La composition ne contient **aucune** musique : elle est mixée après le rendu, donc la preview ne
l'entend pas. Les temps sont ceux du master, avant les inserts ; comme les inserts s'ajoutent au master
sans le raccourcir, la musique reste calée.

## Déclarer : registre §1d

```markdown
## 1d. Registre des musiques

| ID | Rôle | Prompt | Durée | Volume | Seed |
|---|---|---|---|---|---|
| M01 | montée | epic cinematic orchestral build, low strings ostinato, rising brass and timpani, tension growing, no vocals | 14 | 0.45 | 11 |
| M02 | conclusion | epic orchestral finale, full strings and brass, slow powerful resolution, hopeful, no vocals | | 0.5 | 12 |
```

| Colonne | Sens |
|---|---|
| `ID` | `M01`, `M02`… |
| `Rôle` | montée, point culminant, conclusion… (pour le lecteur du storyboard) |
| `Prompt` | **obligatoire**, décrit la musique au générateur, **en anglais** : style, instruments, progression, ambiance, `no vocals` |
| `Durée` | secondes, facultative (20 s par défaut) |
| `Volume` | facultatif, de 0 à 1 (0,45 par défaut). Gain **avant** la compression par la voix |
| `Seed` | facultative : même graine, même musique (reproductible) |

Une musique du registre peut servir plusieurs fois (un thème qui revient pour la conclusion) : le fichier est
généré une seule fois par durée.

## Poser une musique : paramètres d'étape

```markdown
- `I1.1#0` · cue « cinquante-sept » → **compteur +57 %**
  - kind: count
  - music: M01
- `S04.1#1` · cue « conclusion » → **punchline**
  - kind: punch
  - music: M02
  - music_until: S04
```

| Clé | Effet |
|---|---|
| `music` | `Mxx` : la musique **démarre au début de cette étape** |
| `music_until` | où elle s'arrête : une **étape** (`I1.1#2` : à son début), une **scène** (`S04` : à sa fin) ou un **nombre de secondes** (`8`). Absent : la `Durée` du registre |
| `music_volume` | surcharge le volume du registre pour ce repère |

Fondus : 1,5 s à l'entrée, 3 s à la sortie.

## Règles de mise en scène

1. **Ponctuer, pas habiller.** Au plus ≈ 35 % du film ; `build.py` avertit au-delà. Pas de musique sous une
   démonstration, un chiffre à lire, une explication fine.
2. **Les trois moments** : la **montée** (elle démarre pendant que l'idée s'installe et culmine sur la phrase
   forte), le **sommet** (une punchline, un renversement : musique courte, 5 à 10 s), la **conclusion**
   (elle démarre avant la dernière phrase, se résout, puis s'éteint).
3. **Elle commence avant le mot fort**, pas sur lui : une montée se prépare 5 à 10 s à l'avance.
4. **Au moins 4 s** : en dessous, elle n'a pas le temps de s'installer (avertissement).
5. **Pas de chevauchement** : deux musiques ne se superposent pas ; la première est coupée au début de
   la seconde (avertissement).
6. **Prompt** : épique et orchestral par défaut ; préciser l'arc (`build`, `climax`, `resolution`), le tempo, les
   instruments, **`no vocals`**. Un prompt par rôle, pas par scène.
7. **Instruction contraire** : `**Musique** : aucune` dans l'en-tête du storyboard, ou `build.py --no-music` :
   le registre et les `music:` sont ignorés, aucun `data/music.json`.

## Commandes

```bash
python3 scripts/build.py ...                 # écrit data/music.json (+ avertissements)
python3 scripts/make-music.py --plan         # ce qui sera généré
python3 scripts/make-music.py                # génère les fichiers absents (`sound music … -i`)
# … rendu du master : renders/full.mp4 …
python3 scripts/mix-music.py                 # renders/full-music.mp4
python3 scripts/post-render.py               # inserts éventuels, à partir de full-music.mp4
```

`make-music.py` : `--engine acestep|musicgen`, `--max-duration 120`, `--force`, `--dry-run`. Commande `sound` du
PATH, ou `SOUND_CMD`. `mix-music.py` : `--scale 0.8` (toutes les musiques plus basses), `--no-duck`,
`--print-graph`.

## Ce que fait le mixage

Chaque repère est coupé à sa durée, avec fondus, posé à son temps, à son volume. Le total est ensuite
**comprimé par la voix** (`sidechaincompress` : dès que la voix parle, la musique baisse de 12 dB et plus ; elle
remonte dans les silences, ce qui fait les montées), mélangé à la voix, puis limité à -0,45 dBFS. La vidéo n'est
pas ré-encodée. Le test (`scripts/test-music.py`) mesure le résultat sur un signal : pendant que la voix parle, la
musique, même très forte, ne dépasse pas la voix de plus de 1 dB au total.

`post-render.py` refuse un `full-music.mp4` plus ancien que `full.mp4` (composition rendue de nouveau depuis le
mixage) : relancer `mix-music.py`, ou `--no-music`.
