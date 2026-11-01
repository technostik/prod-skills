# `hyperframes check` : avertissements connus et corrections

`npx hyperframes@0.8.123 lint` est rapide et ne demande pas de navigateur. `check` ajoute le runtime, la mise en page et le contraste (Chrome requis). La démo (`examples/demo`) doit sortir de `lint` sans erreur ni avertissement.

| Code | Cause | Correction |
|---|---|---|
| `timeline_track_too_dense` | 4 clips ou plus sur une même piste d'un même fichier | Dans la démo : 3 étapes au plus par fichier. Dans un film, une scène a souvent plus de 3 étapes : avertissement informatif, à accepter ou à traiter en scindant la scène en deux fichiers |
| `overlapping_gsap_tweens`, `gsap_repeated_fromto_without_baseline` | Deux `fromTo` sur le même élément et la même propriété (typiquement `scale` d'une `ref-card`) | Séparer les propriétés (entrée : `opacity` et `y` ; zoom lent : `scale`) et ajouter `immediateRender: false` au `fromTo` suivant |
| `text_occluded` (info) | La webcam en `full` recouvre le texte de l'étape | Voulu : `data-layout-allow-occlusion` sur le cadre caméra (`.cam-frame`) |
| Contraste (WCAG AA) | Texte normal sous 4,5:1, grand texte (24 px, ou 19 px gras) sous 3:1 | `.slideno` et `.dkw.dim` utilisent `--gris`. Ne pas baisser l'opacité d'un texte gris sur noir |

Le contraste est échantillonné en 5 points de la timeline, calculé contre ce qui est réellement derrière le texte : une capture claire (`ref-shot`) peut faire échouer `.slideno`.
