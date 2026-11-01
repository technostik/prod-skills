# Studio slides (mode slides)

Entrée : le script. Écrire le scénario au format estimé, puis les slides aux mêmes identifiants. La composition suit le scénario, avant la prise. Après la prise, le transcript peut s'écarter du script : les temps suivent le transcript. Une étape dont l'écran ne correspond plus à ce qui a été dit se reprend. Si le deck est déjà fourni, le copier vers `assets/slides.md` et ne pas le réécrire (`references/advanced-slides-subset.md`). Résoudre les assets avant la preview.

```bash
cp $SKILL_DIR/scripts/build_studio_slides.py scripts/
cp $SKILL_DIR/scripts/build_studio_anim.py scripts/
cp $SKILL_DIR/scripts/studio_server.py scripts/
cp $SKILL_DIR/scripts/check-steps.py scripts/
cp $SKILL_DIR/scripts/make-sfx.py scripts/
```

Deux previews. Par défaut, la slide et les notes restent au prompteur ; l'enregistrement capture les clips. La preview du deck ne sert que si la prise doit montrer le deck lui-même.

### Preview du deck

```bash
python3 scripts/build_studio_slides.py assets/slides.md -o studio-slides.html
```

- `?view=present` : le deck, 1920×1080. Fond photo si `<!-- img: ... -->` ou `![...](...)`, sinon fond uni.
- `?view=prompteur` : aperçu + `note:` en grand. `(pas de notes)` si absent. Jamais projeté.
- Chaque `fragment` est une étape. Avance (Espace/→/clic) révèle le fragment puis la slide suivante. Recule (←) inverse. Compteur `fragment k/n` des deux côtés.
- Compléter les slides sans `note:` avant la prise.

### Preview de la composition

Le prompteur montre les notes : ancre (étape, fragment, durée, cue) + `note:` en grand. Jamais le transcript en entier, jamais la ligne déjà dans le clip. Les clips sont la prise. `studio.html` sert à la prise, `index.html` au rendu, mêmes labels que le scénario.

Animation pas à pas, le deck en mémo seulement :

```bash
python3 scripts/build_studio_anim.py -o studio-anim.html
```

Présentation : `data/scenes.json` + `data/figures.json`. Prompteur : `assets/slides.md`, relié par `I1`, `S01`, etc. 1 pas = 1 beat, dernier pas = punch. Synchro `studio-anim`.

Présentation et prompteur avancent ensemble (BroadcastChannel + localStorage). Avance et Recule des deux côtés.

### Servir et enregistrer

Caméra, capture et POST `/prise` exigent Chrome ou Edge en `http://localhost`. Pas de `file://`.

```bash
python3 scripts/studio_server.py 8321
```

Fenêtre capturée : `http://localhost:8321/<preview>?view=present`. Fenêtre du locuteur : `?view=prompteur`. Le bouton **Ouvrir présentation** ouvre la première. `<preview>` est `studio-slides.html`, `studio-anim.html` ou `studio.html`.

Essai : Avance/Recule sur un fragment, caméra en coin, un overlay, 5 s d'enregistrement → `$HF_VIDEOS_DIR/prise-studio-*.webm`.

Prise : improviser depuis les notes, dans l'ordre du scénario. Raté : Pause, Recule, Reprendre. Une seule prise continue. Stop envoie le fichier dans `$HF_VIDEOS_DIR`.

Overlays lus depuis `$HF_OVERLAYS_DIR` vers `assets/overlays/`. Caméra : Off, coin, mi-écran, miroir.

### Après la prise

1. Transcrire, retirer les silences, re-transcrire l'audio final.
2. Caler les clips sur la voix (ancres = débits du transcript, cues = fragments). `index.html` porte les timings. `npm run check`, preview, mp4 sur feu vert uniquement.
3. Échec inexpliqué : skill `report`.

## Format des slides

`assets/03-slides-advanced-slides.md`, seulement si quelqu'un parle en pas à pas.

```markdown
---
theme: black
transition: fade
controls: false
progress: true
slideNumber: false
margin: 0.05
---

<!-- id: I1.1 -->
### Depuis la mi-septembre 2026
# +5 000 interpellations <!-- element class="fragment" -->
*Source : …*
note:
- Idée en plus. Pas la ligne affichée.

---
```

Le `id:` est celui du scénario. Chaque `fragment` est l'étape `#k` suivante. La ligne à l'écran est celle du scénario (`→`), pas le transcript. `note:` est pour le locuteur. Un chiffre ⚠️ du registre porte la pastille, et se dit comme non confirmé.
