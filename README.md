# prod-skills

Skills de production pour agents IA, organisées par domaine.

## Organisation

```
prod-skills/
├── Article/
└── YouTube/
    ├── jo-hyperframe/
    │   └── SKILL.md
    └── jo-youtube-title/
        └── SKILL.md
```

Chaque skill vit dans un sous-répertoire de son domaine. Le répertoire `~/.agents/skills/<nom>` est un lien symbolique vers le skill correspondant dans ce dépôt.

## Historique

`YouTube/jo-hyperframe` a été importé depuis [technostik/hyperframe-gen](https://github.com/technostik/hyperframe-gen) avec son historique complet via `git subtree`. Pour parcourir cet historique :

```bash
git log --graph --oneline          # l'arbre complet, branches fusionnées incluses
git log --oneline HEAD^2           # uniquement l'historique importé
```

Le dépôt d'origine est archivé ; ce dépôt en est la source de vérité.
