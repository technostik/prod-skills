# hyperframe-gen

Distribution du skill `hyperframe-joriel` : produire une vidéo HyperFrames au langage visuel Joriel, en trois modes (auto, webcam, incrustation), après une étape de préparation (voix et transcript d'abord, puis assets) qui précède le storyboard.

## Installation

Le skill vit dans [technostik/prod-skills](https://github.com/technostik/prod-skills), sous `YouTube/my-hyperframe-generator/`. Pour l'exposer aux agents, on clone le dépôt une fois et on lie le skill :

```bash
git clone https://github.com/technostik/prod-skills.git "$HOME/Code/prod-skills"
ln -s "$HOME/Code/prod-skills/YouTube/my-hyperframe-generator" "$HOME/.agents/skills/my-hyperframe-generator"
```

Le nom du lien (`my-hyperframe-generator`) est le `SKILL_DIR` par défaut documenté dans `SKILL.md` (la skill s'appelle `hyperframe-joriel` dans son en-tête) ; c'est lui que les agents résolvent, pas une copie. Après un `git pull` dans `prod-skills`, le skill est à jour sans autre manipulation.

Historique : le skill a d'abord vécu sous `YouTube/jo-hyperframe/`, lié sous le nom `jo-hyperframe`. Ces chemins n'existent plus dans le dépôt ; un lien resté sur l'ancien chemin est à refaire avec la commande ci-dessus.

Une copie simple du seul répertoire `YouTube/my-hyperframe-generator/` fonctionne aussi, si le dépôt complet n'est pas souhaité — mais il faut alors refaire la copie à chaque mise à jour.

Prérequis et variables d'environnement : `SKILL.md` § Prérequis.

## Arborescence

| Chemin | Contenu |
|---|---|
| `SKILL.md` | point d'entrée : routeur des 4 modes, puis le socle commun (vocabulaire, étapes, format du storyboard, règles de rendu) |
| `modes/` | un sous-skill par mode, lu seulement une fois le mode choisi : `auto.md`, `webcam.md`, `incrustation.md` |
| `archive/slides/` | le mode `slides` (archivé, plus utilisé) : doc, builders du studio, serveur d'enregistrement ; `archive/slides/README.md` |
| `references/` | **préparation**, langage visuel, primitives (balisage exact), format du storyboard, schémas animés et Excalidraw, musique, conventions studio et webcam, schémas `data/`, glossaire |
| `scripts/` | `build.py` (composition finale), `render_primitive.py` (primitives partagées), `schema_anim.py` (schémas animés), `prepare.py` (préparation), `transcript-export.py` (sous-titres JSON + TXT), `music_plan.py` / `make-music.py` / `mix-music.py` (musique), `shorts_plan.py` / `shorts-export.py` (shorts de promotion), `excalidraw_anim.py` / `excalidraw_gen.py` / `schema-to-excalidraw.py` / `excalidraw-preview.py` (schémas Excalidraw), builders studio, `check-steps.py`, nettoyage webcam (`concat-mkv.sh`, `clean-posthoc.py`), détection des screencasts OBS (`detect-cast.py`), `post-render.py` (inserts), `lint-repo.py` ; tests : `test-detect-cast.py`, `test-cast-build.py`, `test-schema.py`, `test-transcript-export.py`, `test-media-fit.py`, `test-post-render.sh` |
| `examples/demo/` | catalogue des primitives (12 scènes dont la webcam avec Cast et un schéma déployé sur deux compositions, lorem ipsum, nom affiché à l'écran) ; médias factices via `scripts/make-placeholders.sh` |
| `examples/storyboard.example.md` | storyboard complet et parsable, couvre toutes les primitives |
| `examples/gabarits/` | exemples JSON de `data/design.json` pour `diverge`, `seuil`, `compare3`, `cols2` |
| `prepare-webcam-context.sh` | script ad hoc de préparation de contexte (voir ci-dessous) |

## Contexte ad hoc pour une tâche (`prepare-webcam-context.sh`)

Script ad hoc, en marge du flux normal : il ne produit aucun contenu, il **rassemble les fichiers utiles** dans un répertoire dédié, pour les tâches qui en ont besoin — la rédaction du storyboard et la composition. Pratique pour travailler dans un répertoire isolé, ou pour donner à un agent un contexte propre et borné sans le laisser se balader dans l'arborescence du skill.

```bash
./prepare-webcam-context.sh /chemin/vers/contexte [--project /chemin/vers/projet] [--mode webcam|incrustation]
```

`--project` (facultatif) ajoute au dossier `storyboard/` les données du projet dont le LLM a besoin pour annoter les séquences Cast : `assets/cast-segments.json` et `transcript.json`. Sans cette option, rien ne change par rapport à avant.

Il crée trois sous-répertoires :

| Sortie | Contenu |
|---|---|
| `commun/` | `SKILL.md`, `references/visual-language-joriel.md` |
| `storyboard/` | `references/storyboard-format.md`, `references/scenario-to-storyboard-prompt.md`, `references/data-schemas.md`, `references/webcam.md`, `modes/<mode>.md` (copié sous le nom `mode-<mode>.md`, `--mode`, défaut `webcam`), `references/posthoc-video-conventions.md`, `references/scenario-studio-conventions.md` ; avec `--project`, aussi `cast-segments.json` et `transcript.json` du projet |
| `composition/` | `references/primitives-joriel.md`, `examples/storyboard.example.md`, `examples/demo/index.html`, `assets/style-joriel.css`, et `composition-examples.html` — toutes les sections des `examples/demo/compositions/i*.html` extraites et fusionnées en un seul fichier consultable |

Les fichiers sont **copiés**, pas liés : le répertoire produit est autonome et jetable. Le script s'arrête en erreur si un fichier source manque, si aucun exemple `i*.html` n'est trouvé, ou si la fusion ne produit pas de fichier non vide.

## Vérifier

```bash
python3 scripts/build.py --root <projet>                              # storyboard -> index.html + compositions/
python3 scripts/lint-repo.py                                          # chemins cités, termes obsolètes
python3 scripts/test-detect-cast.py                                   # détecteur Cast : vidéos synthétiques, FFmpeg seul
python3 scripts/test-cast-build.py                                    # build Cast : logique, build, seeks (Playwright optionnel)
python3 scripts/test-schema.py                                        # schémas animés : géométrie, build, seeks Chromium (Playwright optionnel)
python3 scripts/test-transcript-export.py                             # sous-titres : JSON + TXT, nommage long_publish, décalage des inserts
python3 scripts/test-shorts.py                                     # shorts : section §6, calage sur les phrases, format de video short-extractor
python3 scripts/test-prepare.py                                    # préparation : gabarits, contrôle par mode, chapitres, validation des schémas
python3 scripts/test-excalidraw.py                                  # schémas Excalidraw : lecture, habillage, génération, build, formes et seeks Chromium
python3 scripts/test-music.py                                      # musique : plan, génération (faux sound), mixage mesuré, post-render
python3 scripts/test-media-fit.py                                     # fonds cover, références contain (pixels dans Chromium)
python3 scripts/test-incrustation.py                                  # mode incrustation : ancres, primitives, calques, crop (Playwright optionnel)
bash scripts/test-post-render.sh                                      # inserts : test de bout en bout, FFmpeg seul
cd examples/demo && bash scripts/make-placeholders.sh && npm run check  # nécessite Node, FFmpeg, accès réseau
```
