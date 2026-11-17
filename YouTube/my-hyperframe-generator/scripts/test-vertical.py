#!/usr/bin/env python3
"""Tests du format 9:16 (Short vertical) : build.py, render_primitive.py, prepare.py, short-take.py, detect-cast.py.

  A. logique : parse_format, conversion `vh` → `calc(N * var(--u))` ;
  B. build 16:9 inchangé (`--format 16:9` = pas d'option), build 9:16 (viewport, CSS, pas de shorts de promotion) ;
  C. webcam + Cast sur une vidéo verticale synthétique : détection du filet, géométrie, crop ;
  D. incrustation : positions automatiques dans les quarts inférieurs ;
  E. prise : dernière vidéo du dossier, chapitre unique ;
  F. Chromium (si Playwright est présent) : cadre pip 252×448, Cast plein écran 1080×1920, schéma dans sa bande.

Usage : python3 scripts/test-vertical.py   (aucun MP4 final ; tout dans un dossier temporaire)
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
FAILS = []


def load(name, fname):
    spec = importlib.util.spec_from_file_location(name, HERE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build = load("build", "build.py")
rp = load("render_primitive", "render_primitive.py")
stk = load("short_take", "short-take.py")


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def run(*cmd, cwd=None, env=None):
    return subprocess.run([sys.executable] + [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True,
                          env=dict(os.environ, **(env or {})))


def project(tmp, storyboard, name):
    root = tmp / name
    (root / "assets").mkdir(parents=True)
    shutil.copy(HERE.parent / "examples" / "demo" / "assets" / "gsap.min.js", root / "assets" / "gsap.min.js")
    (root / "assets" / "storyboard.md").write_text(storyboard, encoding="utf-8")
    return root


def video(path, secs=14, cast=(6, 9)):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=%d" % secs,
                    "-f", "lavfi", "-i", "sine=f=300:d=%d" % secs, "-vf",
                    "drawbox=x=0:y=0:w=iw:h=10:color=0x00FF00:t=fill:enable='between(t,%d,%d)'" % cast,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)], check=True)


EXAMPLE = (HERE.parent / "examples" / "storyboard.example.md").read_text(encoding="utf-8")
CAM_SB = """# STORYBOARD — Short test

**Mode** : webcam
**Format** : 1080×1920 @ 30 fps
**Musique** : aucune

## 4. Scènes

### I1 — Test [BG-00]

- `I1.1#0` t=0.00 (2.5s) [off/kw] Sans caméra
- `I1.1#1` t=2.50 (3.0s) [pip/kw] Caméra en coin
- `I1.1#2` t=5.50 (3.0s) [full/kw] Caméra au centre
- `I1.1#3` t=8.50 (2.5s) [pip/stamp] Preuve
- `I1.1#4` t=11.00 (3.0s) [off/kw] Fin
"""


def part_a():
    print("A. logique")
    pf = build.parse_format
    check("parse_format : défaut, noms, définitions",
          [pf(""), pf("9:16"), pf("Vertical"), pf("short"), pf("1080×1920 @ 30 fps"), pf("1920×1080 @ 30 fps")]
          == ["16:9", "9:16", "9:16", "9:16", "9:16", "16:9"])
    try:
        pf("1080x1080")
        ok = False
    except SystemExit:
        ok = True
    check("parse_format : un carré est refusé", ok)
    css = rp.vertical_css(".a{font-size:7.2vh;margin:-1.2vh 0 .5vh;gap:1vh 1.8vw}")
    check("vertical_css : chaque `vh` devient calc(N * var(--u)), les `vw` restent",
          "vh" not in css and "calc(7.2 * var(--u))" in css and "calc(-1.2 * var(--u))" in css
          and "calc(.5 * var(--u))" in css and "1.8vw" in css, css)
    base = (HERE.parent / "examples" / "demo" / "assets" / "style-joriel.css").read_text(encoding="utf-8")
    full = rp.css_vertical(base)
    check("css_vertical : aucune unité vh restante, --u et ancres 1080×1920 présents",
          not re.search(r"\dvh", full) and ":root{--u:10.8px}" in full and ".ov-br{left:540px;top:960px" in full)
    check("détection Cast : la zone suit le petit côté (10 px en 1080×1920)",
          load("detect_cast", "detect-cast.py").zone_rows(1920, 1080) == 20
          and load("detect_cast2", "detect-cast.py").zone_rows(1080, 1920) == 20)


def part_b(tmp):
    print("B. build 16:9 inchangé, build 9:16")
    r1 = project(tmp, EXAMPLE, "p169a")
    r2 = project(tmp, EXAMPLE, "p169b")
    run(HERE / "build.py", "--root", r1)
    run(HERE / "build.py", "--root", r2, "--format", "16:9")
    same = all((r1 / f).read_bytes() == (r2 / f).read_bytes() for f in ("index.html", "compositions/i00.html", "compositions/i03.html"))
    check("`--format 16:9` = pas d'option (octet pour octet)", same)
    check("16:9 : data-width 1920, deux feuilles de style, pas de feuille 9x16",
          'data-width="1920"' in (r1 / "index.html").read_text(encoding="utf-8")
          and "style-joriel-ext.css" in (r1 / "compositions/i00.html").read_text(encoding="utf-8")
          and not (r1 / "assets/style-joriel-9x16.css").exists())
    sb = EXAMPLE.replace("**Format** : 1920×1080 @ 30 fps", "**Format** : 1080×1920 @ 30 fps")
    r = project(tmp, sb, "p916")
    res = run(HERE / "build.py", "--root", r)
    idx = (r / "index.html").read_text(encoding="utf-8")
    c0 = (r / "compositions/i00.html").read_text(encoding="utf-8")
    check("9:16 : build réussit", res.returncode == 0, res.stderr[-300:])
    check("9:16 : index 1080×1920 (viewport, racine, hôtes), aucun 1920 de largeur",
          'content="width=1080, height=1920"' in idx and 'data-width="1080"' in idx and 'data-height="1920"' in idx
          and 'data-width="1920"' not in idx)
    check("9:16 : composition 1080×1920, feuille style-joriel-9x16.css seule", 'data-width="1080" data-height="1920"' in c0
          and "style-joriel-9x16.css" in c0 and "style-joriel-ext.css" not in c0)
    check("9:16 : feuille écrite, plus de 16:9 ext", (r / "assets/style-joriel-9x16.css").exists()
          and not (r / "assets/style-joriel-ext.css").exists())
    check("9:16 : pas de shorts de promotion (la vidéo est le short)", not (r / "data/shorts_segments.json").exists()
          and "ignorés" in res.stdout)
    sb2 = sb.replace("**Mode** : auto", "**Mode** : auto\n").replace("1080×1920", "1920×1080")
    r3 = project(tmp, sb2, "p169c")
    res3 = run(HERE / "build.py", "--root", r3, "--format", "vertical")
    check("`--format vertical` prime sur l'en-tête", 'data-width="1080"' in (r3 / "index.html").read_text(encoding="utf-8"), res3.stderr[-200:])


def part_c(tmp):
    print("C. webcam + Cast, prise verticale")
    r = project(tmp, CAM_SB, "pcam")
    video(r / "assets" / "cam-clean.mkv")
    d = run(HERE / "detect-cast.py", r / "assets" / "cam-clean.mkv", "--output", r / "assets" / "cast-segments.json", "-q")
    doc = json.loads((r / "assets" / "cast-segments.json").read_text(encoding="utf-8"))
    check("detect-cast : le filet d'une prise 1080×1920 est repéré (≈ 6 à 9 s)",
          d.returncode == 0 and doc["width"] == 1080 and doc["height"] == 1920 and len(doc["segments"]) == 1
          and abs(doc["segments"][0]["start"] - 6) < 0.1, (d.stderr, doc.get("segments")))
    res = run(HERE / "build.py", "--root", r)
    c0 = (r / "compositions/i00.html").read_text(encoding="utf-8")
    check("webcam 9:16 : build réussit", res.returncode == 0, res.stderr[-300:])
    check("webcam 9:16 : géométrie pip / full / cast en 1080×1920",
          "pip:  { left: 40, top: 1052, width: 252, height: 448" in c0 and "full: { left: 162, top: 288, width: 756, height: 1344" in c0
          and "CAM.cast = { left: 0, top: 0, width: 1080, height: 1920" in c0, c0[c0.find("var CAM"):c0.find("var CAM") + 400])
    crop = json.loads((r / "data/camera.json").read_text(encoding="utf-8"))["crop"]
    check("webcam 9:16 : crop du filet sans déformation (échelle ≈ 1920/1908)", abs(crop["scale"] - 1920 / 1908) < 1e-3, crop)
    # incrustation
    ri = project(tmp, CAM_SB.replace("webcam", "incrustation"), "pinc")
    shutil.copy(r / "assets" / "cam-clean.mkv", ri / "assets" / "cam-clean.mkv")
    shutil.copy(r / "assets" / "cast-segments.json", ri / "assets" / "cast-segments.json")
    sb = re.sub(r"\[[a-z]+/", "[", (ri / "assets/storyboard.md").read_text(encoding="utf-8"))
    (ri / "assets/storyboard.md").write_text(sb, encoding="utf-8")
    run(HERE / "build.py", "--root", ri)
    steps = json.loads((ri / "data/steps.json").read_text(encoding="utf-8"))["steps"]
    check("incrustation 9:16 : positions automatiques dans les quarts inférieurs",
          steps and all(s["place"] in ("bas-gauche", "bas-droite") for s in steps), [s["place"] for s in steps])
    return r


def part_e(tmp):
    print("E. prise et chapitre unique")
    d = tmp / "videos"
    (d / "OBS").mkdir(parents=True)
    old = time.time() - 100
    for name, age in (("a.mp4", 50), ("b.mkv", 10), ("c.txt", 1)):
        (d / name).write_bytes(b"x")
        os.utime(d / name, (time.time() - age, time.time() - age))
    (d / "OBS" / "z.mkv").write_bytes(b"x")
    check("dernière vidéo : la plus récente, ni sous-dossier ni autre extension", stk.latest_video(d).name == "b.mkv")
    (d / "d.mkv").write_bytes(b"x")
    check("dernière vidéo : un fichier en cours d'écriture est ignoré", stk.latest_video(d).name == "b.mkv")
    p = tmp / "prise"
    (p).mkdir()
    vd = tmp / "vids"
    vd.mkdir()
    video(vd / "take.mkv", secs=3, cast=(1, 2))
    time.sleep(2.1)
    res = run(HERE / "short-take.py", cwd=p, env={"HF_VIDEOS_DIR": str(vd)})
    take = json.loads((p / "assets/take.json").read_text(encoding="utf-8")) if (p / "assets/take.json").exists() else {}
    check("short-take : prend la dernière vidéo de $HF_VIDEOS_DIR, écrit cam-original.mkv, voix-brut.wav, take.json",
          res.returncode == 0 and (p / "assets/cam-original.mkv").exists() and (p / "assets/voix-brut.wav").exists()
          and take.get("vertical") is True, res.stdout + res.stderr)
    run(HERE / "prepare.py", "--root", p, "init", "--mode", "webcam", "--format", "9:16")
    prep = json.loads((p / "assets/prep.json").read_text(encoding="utf-8"))
    check("prepare init --format 9:16 : prep.json porte le format ; fonds en portrait",
          prep.get("format") == "9:16" and "1080 × 1920" in (p / "assets/assets.md").read_text(encoding="utf-8"))
    (p / "SCENARIO.md").write_text("# Le titre du short\n\nUn texte.\n", encoding="utf-8")
    (p / "assets/transcript.json").write_text(json.dumps({"words": [{"word": "un", "start": 0, "end": 1}], "segments": []}), encoding="utf-8")
    rr = run(HERE / "prepare.py", "--root", p, "chapters")
    ch = json.loads((p / "assets/chapters.json").read_text(encoding="utf-8"))
    check("prepare chapters (9:16) : un seul chapitre, à 0, titre du scénario ; pas de chapters.txt",
          rr.returncode == 0 and ch == [{"start": 0.0, "title": "Le titre du short"}] and not (p / "assets/chapters.txt").exists(), rr.stderr)
    run(HERE / "prepare.py", "--root", tmp / "autre", "init", "--mode", "auto")
    check("prepare init sans --format : pas de clé format (16:9 inchangé)",
          "format" not in json.loads((tmp / "autre/assets/prep.json").read_text(encoding="utf-8")))


def part_f(tmp, rcam):
    print("F. Chromium")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (saute : Playwright absent)")
        return
    pages = tmp / "pages"
    pages.mkdir()
    for f in ("style-joriel-9x16.css", "gsap.min.js"):
        shutil.copy(rcam / "assets" / f, pages / f)
    html = (rcam / "compositions/i00.html").read_text(encoding="utf-8")
    inner = re.search(r"<template>(.*?)</template>", html, re.S).group(1)
    script = re.search(r"<script>(.*)</script>", inner, re.S).group(1)
    body = re.sub(r"<link[^>]*>", "", re.sub(r"<script>.*?</script>", "", inner, flags=re.S))
    body = re.sub(r"<video[^>]*></video>", '<video id="cam-i00" muted playsinline></video>', body)
    (pages / "p.html").write_text('<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="style-joriel-9x16.css">'
                                  '</head><body style="margin:0;width:1080px;height:1920px">' + body
                                  + '<script src="gsap.min.js"></script><script>' + script + "</script></body></html>", encoding="utf-8")
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1080, "height": 1920})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto((pages / "p.html").as_uri())

        def rect(t):
            pg.evaluate("t => { window.__timelines['i00'].seek(t, false); return 1 }", t)
            return pg.evaluate("() => { const r = document.querySelector('.cam-frame').getBoundingClientRect(); "
                               "return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }")

        check("script sans erreur", not errs, errs)
        check("pip : cadre 252×448 en (40, 1052)", all(abs(a - b) <= 4 for a, b in zip(rect(4.5), (40, 1052, 252, 448))), rect(4.5))
        check("Cast : cadre plein écran 1080×1920", all(abs(a - b) <= 2 for a, b in zip(rect(7.5), (0, 0, 1080, 1920))), rect(7.5))
        pg.evaluate("t => { window.__timelines['i00'].seek(t, false); return 1 }", 1.0)
        check("off : cadre invisible (opacité 0)", pg.evaluate("() => getComputedStyle(document.querySelector('.cam-frame')).opacity") == "0")
        br.close()


def main():
    part_a()
    with tempfile.TemporaryDirectory(prefix="vertical-") as t:
        t = Path(t)
        part_b(t)
        rcam = part_c(t)
        part_e(t)
        part_f(t, rcam)
    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
