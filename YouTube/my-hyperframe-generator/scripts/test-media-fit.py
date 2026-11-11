#!/usr/bin/env python3
"""Fonds en plein écran (cover), références en entier (contain).

  A. le balisage : `image` avec `src` = fond (classe `fond`), `image` avec `ref:`, `ref-shot` et le
     fichier d'un `ref-card` = référence (classe `ref-shot`) ; `fit:` force l'autre choix ;
  B. Chromium (si Playwright est présent) : une image très large est rognée sur les côtés quand c'est un
     fond, vue en entier avec des bandes transparentes quand c'est une référence.

Usage : python3 scripts/test-media-fit.py
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


STORYBOARD = """# STORYBOARD — Test fit

**Mode** : auto

## 1b. Registre des références

| ID | Type | Source | Fichier local | Statut |
|---|---|---|---|---|
| R01 | image | https://exemple.org/a | assets/references/R01.png | ok |

## 4. Scènes

### I1 — Images

- section: test · type: cards · fond: BG-00 · durée: 30

#### Étapes

- `I1.1#0` · cue « a » → **un fond**
  - kind: image
  - src: assets/references/wide.png
- `I1.1#1` · cue « b » → **une référence**
  - kind: image
  - ref: R01
- `I1.1#2` · cue « c » → **une capture**
  - kind: ref-shot
  - src: assets/references/wide.png
- `I1.1#3` · cue « d » → **une référence forcée en cover**
  - kind: image
  - ref: R01
  - fit: cover
- `I1.1#4` · cue « e » → **un fond forcé en contain**
  - kind: image
  - src: assets/references/wide.png
  - fit: contain
"""


def make_png(path, w, h, rgb):
    try:
        from PIL import Image
    except ImportError:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (w, h), rgb).save(path)
    return True


def main():
    print("A. balisage")
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "assets").mkdir()
        shutil.copy(HERE.parent / "examples" / "demo" / "assets" / "gsap.min.js", tmp / "assets" / "gsap.min.js")
        (tmp / "assets" / "storyboard.md").write_text(STORYBOARD, encoding="utf-8")
        have_png = make_png(tmp / "assets" / "references" / "wide.png", 2400, 400, (220, 30, 30))
        make_png(tmp / "assets" / "references" / "R01.png", 2400, 400, (220, 30, 30))
        r = subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp)], cwd=str(tmp),
                           capture_output=True, text=True)
        check("build : réussit", r.returncode == 0, r.stderr[-300:])
        html = (tmp / "compositions" / "i00.html").read_text(encoding="utf-8")
        got = {m.group(2): m.group(1) for m in re.finditer(r'<img class="([^"]*)" id="img-([^"]*)"', html)}
        check("image avec src = fond (cover, par la classe `fond`)", got.get("I1-1-0") == "fond", got)
        check("image avec ref = référence (classe `ref-shot`)", got.get("I1-1-1") == "ref-shot", got)
        check("ref-shot = référence", got.get("I1-1-2") == "ref-shot", got)
        check("`fit: cover` force le rognage d'une référence", got.get("I1-1-3") == "ref-shot fit-cover", got)
        check("`fit: contain` montre un fond en entier", got.get("I1-1-4") == "fond fit-contain", got)
        ext = (tmp / "assets" / "style-joriel-ext.css").read_text(encoding="utf-8")
        check("CSS étendu : .fond en cover, .ref-shot en contain (même avec un vieux style-joriel.css)",
              ".fond{object-fit:cover}" in ext and ".ref-shot{object-fit:contain}" in ext)
        demo = (HERE.parent / "examples" / "demo" / "assets" / "style-joriel.css").read_text(encoding="utf-8")
        check("CSS de la démo : .ref-shot en contain", re.search(r"\.ref-shot\{[^}]*object-fit:contain", demo) is not None)

        print("B. Chromium : rognage et bandes")
        try:
            from playwright.sync_api import sync_playwright
            from PIL import Image
        except ImportError:
            print("  (saute : Playwright ou Pillow absent)")
        else:
            if not have_png:
                return
            for f in ("style-joriel.css", "style-joriel-ext.css"):
                shutil.copy(tmp / "assets" / f, tmp / f)
            body = re.search(r"<template>(.*?)</template>", html, re.S).group(1)
            body = re.sub(r"<script>.*?</script>", "", body, flags=re.S)
            body = re.sub(r"<link[^>]*>", "", body)
            body = body.replace('src="assets/', 'src="assets/')
            page = tmp / "p.html"
            page.write_text('<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="style-joriel.css">'
                            '<link rel="stylesheet" href="style-joriel-ext.css"><style>.step{opacity:1!important;'
                            'visibility:visible!important}.clip{display:none}.clip.show{display:block}'
                            'body{margin:0;background:#00ff00}#root{background:transparent!important}</style></head><body style="width:1920px;height:1080px">'
                            + body + "</body></html>", encoding="utf-8")
            with sync_playwright() as p:
                br = p.chromium.launch()
                pg = br.new_page(viewport={"width": 1920, "height": 1080})
                pg.set_default_timeout(15000)
                pg.goto(page.as_uri(), wait_until="domcontentloaded")

                def shot(step):
                    pg.evaluate("""(s) => {
                      document.querySelectorAll('.clip').forEach(c => c.classList.remove('show'));
                      document.querySelectorAll('.bg, .vignette, .voile, .slideno').forEach(e => e.style.display = 'none');
                      const img = document.getElementById('img-' + s); img.closest('.clip').classList.add('show');
                      document.querySelectorAll('img').forEach(i => i.style.transform = 'none');
                      return 1; }""", step)
                    pg.wait_for_timeout(150)
                    out = tmp / ("s-%s.png" % step)
                    pg.screenshot(path=str(out))
                    return Image.open(out).convert("RGB")

                fond = shot("I1-1-0")
                ref = shot("I1-1-1")
                # image 2400x400 (rouge) : en cover elle remplit tout l'écran ; en contain elle fait 1920x320 centrée
                check("fond : plein écran, y compris en haut et en bas (rogné sur les côtés)",
                      fond.getpixel((960, 20)) [0] > 180 and fond.getpixel((960, 1060))[0] > 180, (fond.getpixel((960, 20)), fond.getpixel((960, 1060))))
                check("référence : image visible en entier au centre",
                      ref.getpixel((960, 540))[0] > 180 and ref.getpixel((20, 540))[0] > 180 and ref.getpixel((1900, 540))[0] > 180)
                check("référence : bandes transparentes en haut et en bas (le vert du test apparaît)",
                      ref.getpixel((960, 20)) == (0, 255, 0) and ref.getpixel((960, 1060)) == (0, 255, 0),
                      (ref.getpixel((960, 20)), ref.getpixel((960, 1060))))
                forced = shot("I1-1-3")
                check("`fit: cover` sur une référence : plein écran", forced.getpixel((960, 20))[0] > 180)
                br.close()

    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
