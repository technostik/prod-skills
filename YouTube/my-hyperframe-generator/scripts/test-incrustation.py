#!/usr/bin/env python3
"""Tests du mode `incrustation` (scripts/build.py + render_primitive.py).

  A. logique : ancres, positions automatiques reproductibles, zones à éviter, primitives refusées ;
  B. build de bout en bout sur une vidéo synthétique avec filet vert, puis, si Playwright est présent,
     géométrie réelle dans Chromium (centre de chaque ancre, calques, crop Cast aux bornes, seeks).

Usage : python3 scripts/test-incrustation.py
Aucun MP4 n'est produit ; tout se passe dans un dossier temporaire.
"""
import importlib.util
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def load(name, fname):
    spec = importlib.util.spec_from_file_location(name, HERE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build = load("build", "build.py")
rp = load("render_primitive", "render_primitive.py")
tcb = load("test_cast_build", "test-cast-build.py")

FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def approx(a, b, tol=1.5):
    return abs(a - b) <= tol


CENTERS = {"haut-gauche": (480, 270), "haut-droite": (1440, 270), "bas-gauche": (480, 810), "bas-droite": (1440, 810),
           "haut": (960, 270), "bas": (960, 810), "gauche": (480, 540), "droite": (1440, 540), "centre": (960, 540)}


def scenes_of(steps):
    """steps = [(id, params)] dans une seule scène."""
    return [{"id": "I0", "steps": [{"id": sid, "params": dict(par)} for sid, par in steps]}]


def part_a():
    print("A. logique")
    ca = rp.canonical_anchor
    check("alias : coin supérieur droite / coin inférieur gauche / plein centre / Haut",
          (ca("coin supérieur droite"), ca("coin inférieur gauche"), ca("plein centre"), ca("Haut"))
          == ("haut-droite", "bas-gauche", "centre", "haut"), [ca("coin supérieur droite"), ca("plein centre")])
    check("9 ancres, chacune avec classe et échelle", len(rp.OVERLAY_ANCHORS) == 9
          and all(a in rp.OVERLAY_ANCHORS for a in CENTERS))
    check("ancre inconnue -> None", ca("n'importe où") is None)

    # positions automatiques
    sc = scenes_of([("I0.1#%d" % i, {}) for i in range(6)])
    w = build.assign_placements(sc, [])
    seq = [s["_place"] for s in sc[0]["steps"]]
    check("auto : uniquement les deux quarts supérieurs", set(seq) <= {"haut-gauche", "haut-droite"} and w == [], seq)
    check("auto : jamais deux fois de suite la même position", all(a != b for a, b in zip(seq, seq[1:])), seq)
    sc2 = scenes_of([("I0.1#%d" % i, {}) for i in range(6)])
    build.assign_placements(sc2, [])
    check("auto : reproductible (même id -> même position à chaque build)",
          seq == [s["_place"] for s in sc2[0]["steps"]])
    sc3 = scenes_of([("I0.1#%d" % i, {}) for i in range(6)])
    build.assign_placements(sc3, ["haut-droite"])
    check("zone à éviter haut-droite : tout en haut-gauche", {s["_place"] for s in sc3[0]["steps"]} == {"haut-gauche"})
    sc4 = scenes_of([("I0.1#0", {})])
    w = build.assign_placements(sc4, ["haut-gauche", "haut-droite"])
    check("deux défauts évités : avertissement, repli sur les deux", len(w) == 1 and sc4[0]["steps"][0]["_place"] in rp.OVERLAY_DEFAULTS, w)

    # place: manuel
    sc5 = scenes_of([("I0.1#0", {"place": "centre"}), ("I0.1#1", {}), ("I0.1#2", {"place": "coin inférieur droite"}),
                     ("I0.1#3", {"place": "n'importe où"}), ("I0.1#4", {"place": "auto"})])
    w = build.assign_placements(sc5, ["bas-droite"])
    st = sc5[0]["steps"]
    check("place: respecté (centre, coin inférieur droite)", st[0]["_place"] == "centre" and st[2]["_place"] == "bas-droite"
          and st[0]["_place_src"] == "storyboard", [s["_place"] for s in st])
    check("place: dans une zone à éviter -> avertissement mais respecté", any("zone à éviter" in x for x in w) and st[2]["_place"] == "bas-droite", w)
    check("place: inconnu -> avertissement + position automatique", any("inconnu" in x for x in w) and st[3]["_place_src"] == "auto"
          and st[3]["_place"] in rp.OVERLAY_DEFAULTS, w)
    check("place: auto -> automatique", st[4]["_place_src"] == "auto")

    # primitives
    ok_scenes = scenes_of([("I0.1#0", {"kind": "kw"}), ("I0.1#1", {"kind": "list"}), ("I0.1#2", {"kind": "numbers"})])
    try:
        build.check_overlay_kinds(ok_scenes)
        ok = True
    except SystemExit:
        ok = False
    check("kw, alias list (enumerate) et alias numbers (count) acceptés", ok)
    for bad in ("versus", "punch", "seuil", "bars", "compare3", "diverge", "title", "waffle"):
        try:
            build.check_overlay_kinds(scenes_of([("I0.1#0", {"kind": bad})]))
            refused = False
        except SystemExit:
            refused = True
        check("primitive dense refusée : %s" % bad, refused)

    # parse
    avoid, warns = build.parse_avoid("bas-droite, coin supérieur gauche; xx")
    check("zones à éviter : liste + alias + inconnu signalé", avoid == ["bas-droite", "haut-gauche"] and len(warns) == 1, (avoid, warns))
    st = build.parse_step_head("I0.1#0", "t=1.00 (2.0s) [kw] Bonjour")
    check("format minuté `[kw]` : primitive seule, caméra inchangée", st["params"].get("kind") == "kw" and st["camera"] == "off", st)
    st = build.parse_step_head("I0.1#0", "t=1.00 (2.0s) [pip/count] 24")
    check("format minuté `[pip/count]` inchangé", st["camera"] == "pip" and st["params"]["kind"] == "count", st)
    plan = build.CameraPlan([{"_start": 0.0, "_dur": 10.0, "steps": [{"id": "a", "_t": 0.0, "camera": "pip"}]}],
                            [(2.0, 4.0)], fixed_base="plein")
    check("plan en incrustation : base plein, jamais pip, Cast aux bornes",
          [plan.state_at(t) for t in (0, 3, 5)] == ["plein", "cast", "plein"])


STORYBOARD = """# Test incrustation

**Mode** : incrustation
**Zones à éviter** : bas-droite

### I0 — Intro [BG-00]
- `I0.1#0` t=0.00 (4.0s) [kw] Premier visuel
- `I0.1#1` t=4.00 (3.0s) [kw] Deuxième visuel
- `I0.1#2` t=7.00 (3.0s) [kw] Troisième visuel
### I1 — Démo [BG-00]
- `I1.1#0` t=10.00 (4.0s) [kw] Au centre
  - place: centre
- `I1.1#1` t=14.00 (4.0s) [kw] En bas à gauche
  - place: coin inférieur gauche
- `I1.1#2` t=18.00 (4.0s) [kw] Bandeau haut
  - place: haut
### I2 — Fin [BG-00]
- `I2.1#0` t=22.00 (4.0s) [stamp] à droite
  - kind: stamp
  - stamp: OK
  - place: droite
- `I2.1#1` t=26.00 (4.0s) [kw] Auto encore
"""
EXPECTED = {"I0.1#1": "haut-droite", "I1.1#0": "centre", "I1.1#1": "bas-gauche", "I1.1#2": "haut", "I2.1#0": "droite"}


def part_b(tmp):
    print("B1. build de bout en bout (vidéo synthétique + détection)")
    tcb.make_project(tmp)
    (tmp / "storyboard.md").write_text(STORYBOARD, encoding="utf-8")
    d = subprocess.run([sys.executable, str(HERE / "detect-cast.py"), "assets/cam-clean.mkv", "--output",
                        "assets/cast-segments.json", "--quiet"], cwd=tmp, capture_output=True, text=True)
    check("detect-cast.py", d.returncode == 0, d.stderr[-200:])
    r = subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "storyboard.md"],
                       cwd=tmp, capture_output=True, text=True)
    check("build.py en mode incrustation", r.returncode == 0, r.stderr[-400:])
    c0 = (tmp / "compositions" / "i00.html").read_text(encoding="utf-8")
    check("pas de fond image ; vidéo en cadre `cam-under` avec wrapper `cam-content`",
          'id="fond"' not in c0 and 'class="cam-frame cam-under clip"' in c0 and 'class="cam-content"' in c0)
    check("chaque étape porte son ancre (data-place) et sa surimpression", c0.count("data-place=") == 3 and c0.count('class="ovstage"') == 3)
    check("pas d'en-tête de titre ni de bloc applyCam par étape", 'class="stitle"' not in c0 and 'applyCam(tl, "#' not in c0)
    steps = {s["id"]: s for s in json.loads((tmp / "data" / "steps.json").read_text())["steps"]}
    check("data/steps.json : place + source", all(steps[k]["place"] == v for k, v in EXPECTED.items())
          and steps["I1.1#0"]["place_source"] == "storyboard" and steps["I0.1#1"]["place_source"] == "auto"
          and steps["I0.1#0"]["place"] == "haut-gauche", {k: steps[k]["place"] for k in steps})
    cam = json.loads((tmp / "data" / "camera.json").read_text())
    check("data/camera.json : mode incrustation, états plein/cast uniquement",
          cam["mode"] == "incrustation" and {t["state"] for t in cam["timeline"]} == {"plein", "cast"}, cam["mode"])
    # refus d'une primitive dense
    (tmp / "bad.md").write_text(STORYBOARD.replace("- `I0.1#1` t=4.00 (3.0s) [kw] Deuxième visuel",
                                                   "- `I0.1#1` t=4.00 (3.0s) [versus] Deuxième visuel"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "bad.md"],
                       cwd=tmp, capture_output=True, text=True)
    check("primitive dense refusée avec un message clair", r.returncode != 0 and "I0.1#1" in r.stderr + r.stdout
          and "versus" in r.stderr + r.stdout, (r.stderr + r.stdout)[-300:])
    # mode absent de l'en-tête : build classique, aucune surimpression
    (tmp / "classic.md").write_text(STORYBOARD.replace("**Mode** : incrustation\n", ""), encoding="utf-8")
    subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "classic.md"],
                   cwd=tmp, capture_output=True, text=True)
    cl = (tmp / "compositions" / "i00.html").read_text(encoding="utf-8")
    check("sans `**Mode** : incrustation` : mode classique (fond image, pas de surimpression)",
          'id="fond"' in cl and "ovstage" not in cl and "data-place" not in cl)
    # l'exemple fourni au LLM se construit sans erreur ni avertissement de placement
    shutil.copy(HERE.parent / "examples" / "storyboard.incrustation.example.md", tmp / "ex.md")
    r = subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "ex.md"],
                       cwd=tmp, capture_output=True, text=True)
    ex = (tmp / "compositions" / "i00.html").read_text(encoding="utf-8")
    check("examples/storyboard.incrustation.example.md : build OK, 4 surimpressions, place: respecté",
          r.returncode == 0 and ex.count('class="ovstage"') == 4 and 'data-place="haut-droite"' in ex
          and 'data-place="centre"' in ex and 'data-place="bas-gauche"' in ex, (r.stderr + r.stdout)[-300:])
    # on reconstruit le mode incrustation pour les tests navigateur
    subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "storyboard.md"],
                   cwd=tmp, capture_output=True, text=True)


def part_b_browser(tmp):
    print("B2. navigateur : géométrie, calques, crop")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (saute : Playwright absent)")
        return
    pages = tmp / "pages"
    pages.mkdir(exist_ok=True)
    for f in ("style-joriel.css", "style-joriel-ext.css", "gsap.min.js"):
        shutil.copy(tmp / "assets" / f, pages / f)
    cast_doc = json.loads((tmp / "assets" / "cast-segments.json").read_text())
    segsec = [((s["start_frame"] - 0.25) / cast_doc["fps"], (s["end_frame"] - 0.25) / cast_doc["fps"]) for s in cast_doc["segments"]]
    crop = json.loads((tmp / "data" / "camera.json").read_text())["crop"]
    steps = json.loads((tmp / "data" / "steps.json").read_text())["steps"]
    starts = [0.0, 10.0, 22.0]
    with sync_playwright() as p:
        br = p.chromium.launch()
        for i in range(3):
            html = (tmp / "compositions" / ("i0%d.html" % i)).read_text(encoding="utf-8")
            inner = re.search(r"<template>(.*?)</template>", html, re.S).group(1)
            script = re.search(r"<script>(.*)</script>", inner, re.S).group(1)
            body = re.sub(r"<script>.*?</script>", "", inner, flags=re.S)
            body = re.sub(r"<link[^>]*>", "", body)
            body = re.sub(r"<video[^>]*></video>", '<video id="cam-i0%d" muted playsinline></video>' % i, body)
            (pages / ("p%d.html" % i)).write_text(
                '<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="style-joriel.css">'
                '<link rel="stylesheet" href="style-joriel-ext.css"></head><body style="margin:0;width:1920px;height:1080px">'
                + body + '<script src="gsap.min.js"></script><script>' + script + "</script></body></html>", encoding="utf-8")
            pg = br.new_page(viewport={"width": 1920, "height": 1080})
            pg.set_default_timeout(15000)
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto((pages / ("p%d.html" % i)).as_uri())
            check("scène i0%d : script sans erreur" % i, not errs, errs)
            mine = [s for s in steps if s["scene"] == "I%d" % i]
            bad = []
            for st in mine:
                t_mid = st["t"] - starts[i] + min(1.2, st["duration"] / 2)
                pg.evaluate("() => { window.__timelines['i0%d'].seek(%f, false); return 1; }" % (i, t_mid))
                sid = re.sub(r"[^A-Za-z0-9_-]+", "-", st["id"])
                geo = pg.evaluate("""(sid) => { const s = document.getElementById('step-' + sid);
                    const o = s.querySelector('.ovstage').getBoundingClientRect(), z = getComputedStyle(s).zIndex;
                    const f = document.querySelector('.cam-frame'), fr = f.getBoundingClientRect();
                    return {cx: o.left + o.width / 2, cy: o.top + o.height / 2, w: o.width, h: o.height,
                            sz: parseInt(z), fz: parseInt(getComputedStyle(f).zIndex),
                            fl: fr.left, ft: fr.top, fw: fr.width, fh: fr.height, fo: parseFloat(getComputedStyle(f).opacity)}; }""", sid)
                cx, cy = CENTERS[st["place"]]
                scale = rp.OVERLAY_ANCHORS[st["place"]][1]
                good = (approx(geo["cx"], cx) and approx(geo["cy"], cy) and approx(geo["w"], 1920 * scale)
                        and geo["fz"] < geo["sz"] and approx(geo["fl"], 0) and approx(geo["ft"], 0)
                        and approx(geo["fw"], 1920) and approx(geo["fh"], 1080) and geo["fo"] == 1)
                if not good:
                    bad.append((st["id"], st["place"], geo))
            check("scène i0%d : chaque visuel centré sur son ancre, échelle, vidéo plein écran SOUS les visuels" % i, not bad, bad[:1])
            # crop : actif en Cast, absent ailleurs, aussi dans tous les ordres de seek
            samples = [round(x * 0.37, 3) for x in range(1, int(10 / 0.37))]
            rng = random.Random(3)
            order = samples + samples[::-1] + rng.sample(samples, len(samples))
            cbad = []
            dur = pg.evaluate("window.__timelines['i0%d'].duration()" % i)
            for t_loc in order:
                if t_loc >= dur - 0.05:
                    continue
                pg.evaluate("() => { window.__timelines['i0%d'].seek(%f, false); return 1; }" % (i, t_loc))
                a = pg.evaluate("(id) => new DOMMatrixReadOnly(getComputedStyle(document.getElementById('cam-content-' + id)).transform).a", "i0%d" % i)
                t_abs = starts[i] + t_loc
                in_cast = any(x <= t_abs < y for x, y in segsec)
                if in_cast and not approx(a, crop["scale"], 2e-4) or (not in_cast and not approx(a, 1, 1e-6)):
                    cbad.append((round(t_abs, 3), in_cast, a))
            check("scène i0%d : crop actif exactement pendant Cast (%d seeks avant/arrière/aléatoires)" % (i, len(order)),
                  not cbad, cbad[:2])
            pg.close()
        br.close()


def main():
    part_a()
    with tempfile.TemporaryDirectory(prefix="incrust-") as t:
        t = Path(t)
        part_b(t)
        part_b_browser(t)
    print()
    if FAILS:
        print("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)))
        return 1
    print("OK : tous les tests passent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
