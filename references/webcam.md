# Webcam

Une seule webcam, trois modes, `data-cam` sur l'étape. La définition de la prise ne tient pas un vrai plein écran : `full` est un pseudo plein écran.

- `off` — rien à l'écran. Le visuel porte l'argument. Obligatoire sur une punchline (noir, texte or) et sur un gabarit dense (`versus`, `diverge`, `seuil`, `compare3`, barres).
- `pip` — incrustation en bas à droite, 22 % de la largeur. Le schéma reste lisible, le locuteur reste là. Chiffre isolé, preuve, explication.
- `full` — fond et étapes floutés, webcam centrée sur la moitié de l'écran (50 % × 50 %). Entrée de scène, question ouverte, conclusion, moment où le visage porte le propos.

Rythme : un état dure au moins 2,5 s. Le changement de mode est un tween du cadre (position, taille, opacité, 0,55 s) avec un flou de 0,4 s sur le fond et l'étape ; le tout premier état se pose en `tl.set` à `t = 0`. Jamais de cut sec. Revoir le locuteur (`pip` ou `full`) au moins toutes les ~20 s.

On ne redimensionne pas la balise `<video>`. Le runtime la passe en `opacity: 0` et peint l'image sur un canvas calé sur la vidéo. Le cadre est un `<div class="cam-frame">` qui contient la vidéo ; la vidéo remplit le cadre (`inset: 0`). C'est le div qu'on place.

La géométrie est pilotée par `applyCam` en pixels sur 1920×1080 : `pip` 422×238 en bas à droite (22 % de la largeur, le 16:9 de la prise), `full` 960×540 centré (50 % × 50 %). La feuille de style ne fixe que l'habillage du cadre (rayon, bordure, ombre, fond noir) : `.cam-frame` dans `examples/demo/assets/style-joriel.css`.

Le seek passe avec `suppressEvents`. GSAP 3 n'applique pas `className`. Le cadre est piloté par les tweens de la timeline, pas par un callback. `off` met l'`opacity` du **cadre** à 0, jamais celle de la vidéo : un `visibility: hidden` sur le cadre laisse le canvas du runtime visible, et on voit un rectangle noir fantôme. Le flou va sur `#fond` et sur l'étape courante, jamais sur `#root` ni sur le cadre.

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

## Commandes (mode webcam)

Même init que `SKILL.md` § Projet, puis :

```bash
cp $SKILL_DIR/scripts/concat-mkv.sh scripts/
cp $SKILL_DIR/scripts/clean-posthoc.py scripts/
cp $SKILL_DIR/scripts/check-steps.py scripts/
cp $SKILL_DIR/scripts/make-sfx.py scripts/
bash scripts/concat-mkv.sh assets/cam-original.mkv <troncon1.mkv> [<troncon2.mkv> ...]
python3 scripts/clean-posthoc.py assets/cam-original.mkv
# → assets/cam-clean.mkv + assets/voix-posthoc-v1.wav (nouveau nom à chaque passe)
sound transcribe assets/voix-posthoc-v1.wav -F json -l fr -o /tmp/tr.json
```
