# prod-skills

Skills de production pour agents IA, organisées par domaine.

## Organisation

```
prod-skills/
├── Article/
├── Copywriting/
│   ├── my-product-generate-brief/    # extrait un brief de copywriting sourcé à partir d'un produit
│   │   └── SKILL.md
│   └── my-product-generate-email-vente/      # rédige un email ou une séquence de vente directe à partir d'un brief
│       └── SKILL.md
├── Newsletter/
│   ├── my-joriel-narration-article/    # transforme une note de réflexion en article narratif (Substack, fil, LinkedIn)
│   │   └── SKILL.md
│   ├── my-joriel-narration-relecture/  # audite et score un email ou une série sur critères narratifs et marketing
│   │   └── SKILL.md
│   └── my-joriel-narration-serie/      # transforme un corpus en série narrative d'articles (pipeline 4 phases)
│       └── SKILL.md
└── YouTube/
    ├── my-hyperframe-generator/            # produit une vidéo HyperFrames en mode auto/slides/webcam
    │   └── SKILL.md
    ├── my-youtube-title-proposer/         # génère un titre YouTube
    │   └── SKILL.md
    ├── my-technostik-editorial-check/  # audite une idée/sujet vidéo selon la ligne éditoriale
    │   └── SKILL.md
    └── my-narration-from-scenario/  # produit des scripts YouTube narratifs, oraux et accrocheurs avec chapitres
        └── SKILL.md
```

Chaque skill vit dans un sous-répertoire de son domaine. Le répertoire `~/.agents/skills/<nom>` est un lien symbolique vers le skill correspondant dans ce dépôt.

## Historique

`YouTube/my-hyperframe-generator` a été importé depuis [technostik/hyperframe-gen](https://github.com/technostik/hyperframe-gen) avec son historique complet via `git subtree`. Pour parcourir cet historique :

```bash
git log --graph --oneline          # l'arbre complet, branches fusionnées incluses
git log --oneline HEAD^2           # uniquement l'historique importé
```

Le dépôt d'origine n'est plus maintenu : ce dépôt en est la source de vérité.
