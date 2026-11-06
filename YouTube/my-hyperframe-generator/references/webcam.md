# Webcam

Un seul master vidéo (`assets/cam-clean.mkv`), quatre valeurs de `camera` : trois états de base posés par les étapes du storyboard (`off`, `pip`, `full`) et un quatrième, `cast`, pour les séquences de screencast OBS (§ Cast). La définition de la prise ne tient pas un vrai plein écran : `full` est un pseudo plein écran. Seul `cast` occupe vraiment 1920 × 1080.

| Valeur | Sens | Origine des bornes |
|---|---|---|
| `off` | aucune webcam | étape du storyboard |
| `pip` | webcam incrustée | étape du storyboard |
| `full` | webcam pseudo-plein écran (50 %) | étape du storyboard |
| `cast` | séquence OBS en vrai plein écran, filet vert retiré | **`assets/cast-segments.json`**, jamais le storyboard |

- `off` — rien à l'écran. Le visuel porte l'argument. Obligatoire sur une punchline (noir, texte or) et sur un gabarit dense (`versus`, `diverge`, `seuil`, `compare3`, barres).
- `pip` — incrustation en bas à droite, 22 % de la largeur. Le schéma reste lisible, le locuteur reste là. Chiffre isolé, preuve, explication.
- `full` — fond et étapes floutés, webcam centrée sur la moitié de l'écran (50 % × 50 %). Entrée de scène, question ouverte, conclusion, moment où le visage porte le propos.

Rythme : un état dure au moins 2,5 s. Le changement de mode est un tween du cadre (position, taille, opacité, 0,55 s) avec un flou de 0,4 s sur le fond et l'étape ; le tout premier état se pose en `tl.set` à `t = 0`. Jamais de cut sec. Revoir le locuteur (`pip` ou `full`) au moins toutes les ~20 s.

On ne redimensionne ni ne transforme la balise `<video>`. Comportement réel du moteur, vérifié dans `hyperframes@0.9.15` (`packages/engine/src/services/screenshotService.ts`, `injectVideoFramesBatch`, relu et testé en rendu réel ; les projets restés sur la 0.8.123 n'ont pas été retestés) : au rendu, les images de la vidéo sont extraites par FFmpeg, la **balise native est masquée** (`visibility: hidden !important`) et le moteur insère **à côté d'elle, comme frère suivant, une balise `<img class="__render_frame__">`** dans le même parent. Cette image est en `position: absolute`, calée sur la boîte de mise en page de la vidéo (`offsetLeft/Top/Width/Height`, donc sans les transformations des ancêtres) et reprend son style calculé (`object-fit`, `opacity`, `transform`, `clip-path`…). Il n'y a **ni canvas ni `opacity: 0` sur la vidéo** : une description plus ancienne de cette page parlait d'un dessin sur canvas, elle est fausse. En preview, c'est la vidéo native qui s'affiche.

Conséquence : tout ce qui est posé sur un **ancêtre** de la vidéo (clipping `overflow: hidden`, coins arrondis, `transform`, `opacity`) s'applique à l'image de rendu comme à la vidéo native, dans les deux cas. C'est pourquoi le cadre `<div class="cam-frame">` découpe, et pourquoi le crop Cast est porté par un wrapper et non par `<video>`. Le cadre contient la vidéo ; la vidéo remplit son parent (`inset: 0`). C'est le div qu'on place.

La géométrie est pilotée par `applyCam` en pixels sur 1920×1080 : `pip` 422×238 en bas à droite (22 % de la largeur, le 16:9 de la prise), `full` 960×540 centré (50 % × 50 %). La feuille de style ne fixe que l'habillage du cadre (rayon, bordure, ombre, fond noir) : `.cam-frame` dans `examples/demo/assets/style-joriel.css`.

Le seek passe avec `suppressEvents`. GSAP 3 n'applique pas `className`. Le cadre est piloté par les tweens de la timeline, pas par un callback. `off` met l'`opacity` du **cadre** à 0, jamais celle de la vidéo : un `visibility: hidden` sur le cadre ne masque pas l'image de rendu (le moteur la remet en `visibility: visible`), et on voit un rectangle fantôme. Le flou va sur `#fond` et sur l'étape courante, jamais sur `#root` ni sur le cadre.

```js
// webcam : géométrie en px sur 1920x1080. off = fondu + léger retrait, pip = coin bas droit, full = mi-écran.
var CAM = {
  pip:  { left: 1460, top: 821, width: 422, height: 238, opacity: 1 },
  full: { left: 480, top: 270, width: 960, height: 540, opacity: 1 },
  off:  { left: 1460, top: 821, width: 422, height: 238, opacity: 0 }
};
function applyCam(tl, frame, mode, t, stepSel) {
  var g = CAM[mode] || CAM.off;
  if (t === 0) tl.set(frame, g, 0);
  else tl.to(frame, Object.assign({ duration: 0.55, ease: "power3.inOut" }, g), t);
  var blur = mode === "full" ? "blur(8px)" : "blur(0px)";
  tl.to("#fond", { filter: blur, duration: 0.4, ease: "power2.inOut" }, t);
  tl.to(stepSel, { filter: blur, duration: 0.4, ease: "power2.inOut" }, t);
}
// dans la boucle des étapes : applyCam(tl, "#cam-frame-i00", step.getAttribute("data-cam") || "off", t, "#" + step.id);
```

Le corps est recopié dans chaque composition : le script doit rester dans le HTML (scope HyperFrames), pas de fichier partagé.

Le cadre a `data-start="0"` et la durée de sa scène, pour disparaître avec elle. Pas de `style` inline. L'id du cadre est unique dans le projet (`cam-frame-i00`…), les ids `cam` dupliqués se marchent dessus.

Sans `assets/cast-segments.json`, `build.py` émet exactement ce balisage et ce script (`applyCam`), à l'octet près : les trois états de base sont inchangés.

## Cast : séquences OBS en plein écran

OBS enregistre une scène composée de la capture d'écran et de la webcam incrustée dedans, avec en haut de l'image un **filet horizontal vert pur `#00FF00` de 10 px**, présent seulement pendant les screencasts. La composition repère ces séquences et affiche la prise en vrai plein écran pendant ces intervalles seulement.

### Détection (`scripts/detect-cast.py`)

```bash
python3 scripts/detect-cast.py assets/cam-clean.mkv --output assets/cast-segments.json
```

Le script **repère, il ne découpe pas** : aucune vidéo produite, `cam-clean.mkv` jamais modifié ni réencodé. FFmpeg ne lit que la bande supérieure (20 px de haut, réduite à 96 colonnes) ; une image porte un filet si, depuis le bord supérieur, 6 à 16 lignes consécutives sont « vertes » (G fort **et** dominant sur R et B, jamais d'égalité avec `#00FF00` : H.264 et le sous-échantillonnage chroma décalent les valeurs) sur au moins 92 % de la largeur. Un aplat vert plus épais, un filet partiel ou une bande qui ne touche pas le bord ne sont pas des filets. Les trous de moins de 0,25 s sont comblés, les intervalles de moins de 0,5 s écartés. Précision : l'image. Une vidéo sans filet donne `"segments": []`. Tous les seuils sont des constantes commentées en tête du script.

**À relancer après chaque nettoyage** : `clean-posthoc.py` coupe des silences et décale les timecodes. Les intervalles sont dans le référentiel de `cam-clean.mkv`, jamais dans celui de `chapters.json` (qui décrit `cam-original.mkv`, avant nettoyage).

Schéma de `cast-segments.json` (version 1, intervalles semi-ouverts `[start, end)`, temps en secondes depuis le début de la vidéo nettoyée, `end_frame` exclusif) : `references/data-schemas.md`.

### Crop du filet : dans la composition, pas dans la vidéo

Le filet est retiré **au rendu HyperFrames**, sans réencodage ni fichier intermédiaire, par un wrapper intérieur :

```html
<div id="cam-frame-i00" class="cam-frame clip" data-track-index="2" data-layout-allow-occlusion="">
  <div id="cam-content-i00" class="cam-content" data-layout-allow-overflow="">
    <video id="cam-i00" src="assets/cam-clean.mkv" data-start="0" data-duration="60" data-media-start="0" muted playsinline></video>
  </div>
</div>
```

- `.cam-frame` : viewport extérieur, positionné par GSAP, `overflow: hidden` (il découpe la vidéo native en preview et l'image injectée au rendu).
- `.cam-content` : `position: absolute; inset: 0`. Il contient la vidéo **et** l'image que le moteur insère à côté d'elle ; c'est lui qui reçoit le crop.
- `<video>` : jamais de `width`, `height`, `top`, `left` ni `transform` animés dessus.

Pendant un intervalle Cast, `.cam-frame` passe en 1920 × 1080 sans bordure, sans coins arrondis, sans ombre ni flou de fond, et `.cam-content` reçoit un agrandissement uniforme centré en largeur plus une translation verticale qui repoussent les premières lignes hors du cadre. Pour une source 1920 × 1080 et `CAST_CROP_TOP_PX = 12` (les 10 px du filet + 2 px de marge contre les artefacts de compression) :

```
scale    = 1080 / (1080 − 12) = 1,01124   (origine 50 % 0)
yPercent = −12 / (1080 − 12) × 100 = −1,1236   (% de la hauteur du contenu : reste juste pendant que le cadre change de taille)
```

Aucune déformation. Les dimensions de la source viennent de `cast-segments.json` ; si elle n'est pas en 16:9, `cast_crop()` (dans `build.py`) garde la plus grande fenêtre au ratio du viewport sous les lignes rognées. La constante se règle dans `build.py` (`CAST_CROP_TOP_PX`) ou par `--cast-crop-top-px`. Le crop est **instantané** et collé aux bornes : une transition l'aurait laissé apparaître. La bascule est placée 1/4 d'image avant la borne (`CAST_FRAME_LEAD`), de sorte que l'image échantillonnée à `n / fps` est du bon côté quelle que soit la fréquence de rendu.

### Priorité entre Cast et les états de base

`build.py` construit **une timeline effective** : à un instant `t`, l'état est `cast` si `t` est dans un intervalle de `cast-segments.json`, sinon l'état de base en vigueur. Les changements de base posés par le storyboard pendant un Cast sont retenus mais invisibles ; à la fin du Cast, on retrouve **l'état de base de cet instant**, pas celui d'avant :

| Avant | Pendant Cast (étape) | Après |
|---|---|---|
| `pip` | `off` | `off` |
| `off` | `pip` | `pip` |
| `full` | `pip` | `pip` |

`camera: cast` dans le storyboard est une **annotation éditoriale** : elle ne détermine aucun timecode et ne modifie jamais l'état de base. Un intervalle détecté s'affiche en Cast même sans annotation (note à la construction) ; une annotation sans intervalle détecté pendant l'étape donne un avertissement. Entrée en Cast : instantanée depuis `off` (la capture ne doit pas se fondre), tween de cadre de 0,35 s depuis `pip` / `full` ; sortie : tween de 0,35 s vers l'état de base.

La timeline est calculée en Python puis injectée telle quelle dans chaque composition (`CAMEV`, temps locaux de la scène, intervalles qui commencent avant ou traversent plusieurs scènes compris). Chaque tween porte ses valeurs de départ (`fromTo`, `immediateRender: false`) et il n'y a aucun callback : les seeks avant et arrière sont déterministes. Le résultat complet est écrit dans `data/camera.json`.

## Commandes (mode webcam)

Même init que `SKILL.md` § Projet, puis :

```bash
cp $SKILL_DIR/scripts/concat-mkv.sh scripts/
cp $SKILL_DIR/scripts/clean-posthoc.py scripts/
cp $SKILL_DIR/scripts/detect-cast.py scripts/        # seulement si la prise contient des screencasts OBS
cp $SKILL_DIR/scripts/check-steps.py scripts/
cp $SKILL_DIR/scripts/make-sfx.py scripts/
bash scripts/concat-mkv.sh assets/cam-original.mkv <troncon1.mkv> [<troncon2.mkv> ...]
# → assets/cam-original.mkv + assets/chapters.json (start/end cumulés, avant nettoyage)
python3 scripts/clean-posthoc.py assets/cam-original.mkv
# → assets/cam-clean.mkv (nom stable) + assets/voix-posthoc-vN.wav + assets/clean-map-vN.json (N = prochain numéro libre)
python3 scripts/detect-cast.py assets/cam-clean.mkv --output assets/cast-segments.json   # APRÈS chaque nettoyage
sound transcribe assets/voix-posthoc-vN.wav -F json -l fr -o /tmp/tr.json              # N = dernière passe
```

`build.py` détecte seul le dernier `voix-posthoc-vN.wav` (N comparé numériquement) et `assets/cast-segments.json` ; `--cast-segments` force un autre fichier.
