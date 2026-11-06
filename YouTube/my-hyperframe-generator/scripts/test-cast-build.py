#!/usr/bin/env python3
"""Tests de l'intégration Cast dans scripts/build.py.

  A. logique : fusion états de base ∪ intervalles Cast, conversion en temps locaux, crop (sans navigateur) ;
  B. navigateur (optionnel, Playwright + Chromium) : la composition générée est chargée avec GSAP, on
     fait des seeks avant / arrière / aléatoires et on relit l'état réel du DOM.

Usage : python3 scripts/test-cast-build.py        (B est sauté si Playwright est absent)
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
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location("build", HERE / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def approx(a, b, tol=1e-3):
    return abs(a - b) <= tol


def mk_scenes(spec_):
    """spec_ = [(start, dur, [(id, t, camera), ...]), ...] -> structure de resolve_times."""
    scenes = []
    for i, (start, dur, steps) in enumerate(spec_):
        st = []
        for j, (sid, t, cam) in enumerate(steps):
            nxt = steps[j + 1][1] if j + 1 < len(steps) else start + dur
            st.append({"id": sid, "_t": t, "_abs_dur": nxt - t, "camera": cam})
        scenes.append({"id": "I%d" % i, "_start": start, "_dur": dur, "steps": st})
    return scenes


def segs(frames, fps=30.0):
    """[(start_frame, end_frame)] -> segments tels que load_cast_segments les calcule."""
    L = build.CAST_FRAME_LEAD
    return [((a - L) / fps, (b - L) / fps) for a, b in frames]


def evs(plan, scene):
    return [(e["t"], e["p"], e["m"]) for e in plan.scene_events(scene)]


def part_a():
    print("A. logique")
    # --- crop -----------------------------------------------------------------------------------
    c = build.cast_crop(1920, 1080, 12)
    check("crop 1920x1080/12 px : scale 1080/1068", approx(c["scale"], 1080 / 1068, 1e-5), c)
    check("crop 1920x1080/12 px : yPercent -12/1068", approx(c["yPercent"], -12 / 1068 * 100, 1e-4), c)
    c10 = build.cast_crop(1920, 1080, 10)
    check("crop 10 px : scale 1,00935", approx(c10["scale"], 1.00935, 1e-5), c10)
    c720 = build.cast_crop(1280, 720, 8)
    check("crop 1280x720/8 px : même fraction que 1080p/12", approx(c720["scale"], 720 / 712, 1e-5)
          and approx(c720["yPercent"], -8 / 712 * 100, 1e-4), c720)
    # le haut de la fenêtre affichée tombe bien sur la ligne `crop` de la source (1080p) :
    # y_écran = (y_src - top) * k  ->  ligne 12 de la source en y=0, ligne 1080 en y=1080
    s, yp = c["scale"], c["yPercent"]
    y_of = lambda ysrc: ysrc * s + yp / 100 * 1080            # origine 50 % 0, source affichée 1:1
    check("la ligne 12 de la source arrive en y=0", approx(y_of(12), 0, 1e-3), y_of(12))
    check("la ligne 1080 de la source arrive en y=1080", approx(y_of(1080), 1080, 1e-3), y_of(1080))

    # --- cas du builder ---------------------------------------------------------------------------
    # I0 [0,10): pip 0, off 5 ; I1 [10,22): cast annoté 10, pip 16 ; I2 [22,30): full 22, off 26
    base = [(0, 10, [("a", 0, "pip"), ("b", 5, "off")]),
            (10, 12, [("c", 10, "cast"), ("d", 16, "pip")]),
            (22, 8, [("e", 22, "full"), ("f", 26, "off")])]

    def plan_for(frames, spec_=base):
        sc = mk_scenes(spec_)
        return build.CameraPlan(sc, segs(frames)), sc

    p, sc = plan_for([(210, 361)])            # Cast [7 ; 12,033)
    check("2/3. Cast au milieu d'une étape : entrée puis sortie dans la scène",
          [(e[1], e[2]) for e in evs(p, sc[0])] == [(None, "pip"), ("pip", "off"), ("off", "cast")], evs(p, sc[0]))
    check("   l'annotation `cast` ne change pas l'état de base (I1 reste off au départ)",
          p.base_at(10.0) == "off" and p.base_at(16.0) == "pip")
    check("   à t=12,05 on retrouve la base du moment (off), pas celle d'avant le Cast",
          p.state_at(12.05) == "off")
    ev1 = evs(p, sc[1])
    check("4. Cast se terminant au milieu de I1 : initial cast, puis off à la sortie, puis pip à 16",
          [(e[1], e[2]) for e in ev1] == [(None, "cast"), ("cast", "off"), ("off", "pip")], ev1)
    check("   sortie de Cast : 1/4 d'image avant l'image 361, en temps local de I1",
          approx(ev1[1][0], (361 - 0.25) / 30 - 10, 1e-3), ev1[1])

    p, sc = plan_for([(210, 361)] )
    check("5. Cast traversant deux scènes (6,5 → 12,5) : I0 sort en cast, I1 démarre en cast",
          p.state_at(9.99) == "cast" and p.state_at(10.0) == "cast"
          and evs(p, sc[1])[0][1:] == (None, "cast"))
    p, sc = plan_for([(195, 450)])            # [6,5 ; 15] : traverse I0->I1
    check("   début I1 en cast, sortie à ~15 s", evs(p, sc[1])[0][1:] == (None, "cast")
          and any(e[1] == "cast" and e[2] == "off" for e in evs(p, sc[1])))
    p, sc = plan_for([(0, 150)])              # actif dès le début du média
    check("6. Cast actif dès t=0 : premier événement de I0 = cast", evs(p, sc[0])[0][1:] == (None, "cast"), evs(p, sc[0]))
    p, sc = plan_for([(750, 900)])            # jusqu'à la fin (30 s)
    last = evs(p, sc[2])
    check("7. Cast jusqu'à la fin du média : pas de bascule dans la dernière image",
          last[-1][2] == "cast" and not any(e[2] == "off" and e[0] > 7.9 for e in last), last)

    # 8. pip -> off pendant Cast : (pip avant, off pendant, sortie => off)
    b8 = [(0, 20, [("a", 0, "pip"), ("b", 8, "off")])]
    sc = mk_scenes(b8); p = build.CameraPlan(sc, segs([(150, 450)]))      # Cast [5 ; 15)
    check("8. pip -> off pendant Cast : sortie en off", p.state_at(4.9) == "pip" and p.state_at(10) == "cast"
          and p.state_at(15.1) == "off", [p.state_at(t) for t in (4.9, 10, 15.1)])
    # 9. off -> pip pendant Cast
    b9 = [(0, 20, [("a", 0, "off"), ("b", 8, "pip")])]
    sc = mk_scenes(b9); p = build.CameraPlan(sc, segs([(150, 450)]))
    check("9. off -> pip pendant Cast : sortie en pip", p.state_at(4.9) == "off" and p.state_at(15.1) == "pip")
    # 10. full -> pip pendant Cast
    b10 = [(0, 20, [("a", 0, "full"), ("b", 8, "pip")])]
    sc = mk_scenes(b10); p = build.CameraPlan(sc, segs([(150, 450)]))
    check("10. full -> pip pendant Cast : sortie en pip", p.state_at(4.9) == "full" and p.state_at(15.1) == "pip")
    e10 = p.scene_events(sc[0])
    check("    pendant Cast, le changement de base n'émet aucun événement visuel",
          [(e["m"]) for e in e10] == ["full", "cast", "pip"], [e["m"] for e in e10])

    # 12. entrée et sortie exactement à une frontière de scène
    sc = mk_scenes(base); p = build.CameraPlan(sc, segs([(300, 660)]))    # [10 ; 22) = I1 entier
    ev = evs(p, sc[1])
    check("12. Cast = scène entière : I1 démarre en cast ; sortie à la frontière seulement dans I2",
          ev[0][1:] == (None, "cast") and not any(e[2] != "cast" for e in ev[:1]) and p.state_at(21.99) == "cast"
          and p.state_at(22.0) == "full", (ev, p.state_at(22.0)))
    check("    I2 démarre hors Cast (état de base full)", evs(p, sc[2])[0][1:] == (None, "full"))

    # précision à l'image : bascule 1/4 d'image avant la borne
    sc = mk_scenes([(0, 20, [("a", 0, "pip")])]); p = build.CameraPlan(sc, segs([(300, 600)]))
    t_in = p.scene_events(sc[0])[1]["t"]
    check("bascule 1/4 d'image avant l'image 300", approx(t_in, (300 - 0.25) / 30, 1e-3), t_in)
    for fps_render in (30, 60, 25):
        # chaque image de rendu k/fps est du bon côté de la bascule (image 300 = t 10,0 s)
        ok = all((k / fps_render < t_in) == (k / fps_render < 10.0) for k in range(0, fps_render * 20))
        check("   rendu à %d i/s : toute image échantillonnée est du bon côté de la borne" % fps_render, ok)

    # durées de transition
    p, sc = plan_for([(210, 361)])
    e = p.scene_events(sc[0])
    check("transition Cast : 0 s depuis off (instantané), 0,35 s sinon",
          e[2]["m"] == "cast" and e[2]["d"] == 0 and e[1]["d"] == 0.55)
    # annotations / avertissements
    sc = mk_scenes(base)
    for s_ in sc:
        for st in s_["steps"]:
            st["_abs_dur"] = st["_abs_dur"]
    w, n = build.cast_warnings(sc, segs([(600, 660)]), True)
    check("annotation cast sans intervalle détecté sur l'étape -> avertissement", len(w) == 1 and "I" not in w[0][:0] and "c" in w[0], w)
    w, n = build.cast_warnings(sc, segs([(300, 660)]), True)
    check("annotation cast couverte -> pas d'avertissement", w == [], w)
    w, n = build.cast_warnings(sc, [], False)
    check("annotation sans cast-segments.json -> avertissement explicite", len(w) == 1 and "absent" in w[0], w)

    # timeline globale déterministe
    p = build.CameraPlan(mk_scenes(base), segs([(210, 361), (390, 571)]))
    g = p.global_timeline(30.0)
    check("timeline globale : tuiles contiguës couvrant [0, 30)",
          approx(g[0]["start"], 0) and approx(g[-1]["end"], 30)
          and all(approx(g[i]["end"], g[i + 1]["start"]) for i in range(len(g) - 1)), g)
    check("timeline globale : même résultat à chaque appel", g == p.global_timeline(30.0))


# ----------------------------------------------------------------------------------------------- B
def make_project(tmp):
    S = tmp
    (S / "assets" / "bg").mkdir(parents=True)
    sb = """# Test Cast

### I0 — Intro [BG-00]
- `I0.1#0` t=0.00 (5.0s) [pip/kw] Bonjour
- `I0.1#1` t=5.00 (5.0s) [off/kw] Deuxième
### I1 — Démo [BG-00]
- `I1.1#0` t=10.00 (6.0s) [cast] Démonstration
  - kind: kw
  - camera: cast
- `I1.1#1` t=16.00 (6.0s) [pip/kw] Retour
### I2 — Fin [BG-00]
- `I2.1#0` t=22.00 (4.0s) [full/kw] Plein
- `I2.1#1` t=26.00 (4.0s) [off/kw] Fin
"""
    (S / "storyboard.md").write_text(sb, encoding="utf-8")
    vf = ("testsrc2=size=1920x1080:rate=30:duration=30,drawbox=x=1400:y=700:w=420:h=240:color=black:t=fill,"
          "drawbox=x=0:y=0:w=iw:h=10:color=0x00FF00:t=fill:enable='between(t,7,12)+between(t,13,19)+between(t,24,30)'")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", vf, "-c:v", "libx264", "-preset", "ultrafast",
                    "-crf", "23", "-pix_fmt", "yuv420p", str(S / "assets" / "cam-clean.mkv")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x10151c:s=1920x1080", "-frames:v", "1",
                    str(S / "assets" / "bg" / "BG-00.jpg")], check=True)
    shutil.copy(ROOT / "examples" / "demo" / "assets" / "gsap.min.js", S / "assets" / "gsap.min.js")


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def part_b_build(tmp):
    print("B1. build.py de bout en bout (détection réelle -> build)")
    make_project(tmp)
    # sans cast-segments.json : rendu historique
    r = run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "storyboard.md"], tmp)
    legacy = (tmp / "compositions" / "i01.html").read_text(encoding="utf-8")
    check("sans JSON : build OK, JS historique (applyCam), pas de CAMEV, pas de cam-content",
          r.returncode == 0 and "applyCam(tl," in legacy and "CAMEV" not in legacy and "cam-content-" not in legacy
          and not (tmp / "data" / "camera.json").exists(), r.stderr[-300:])
    check("sans JSON : avertissement sur l'annotation cast", "annotée `camera: cast`" in r.stderr, r.stderr[-300:])
    # détection puis build
    d = run([sys.executable, str(HERE / "detect-cast.py"), "assets/cam-clean.mkv", "--output", "assets/cast-segments.json",
             "--quiet"], tmp)
    check("detect-cast.py sur la vidéo synthétique", d.returncode == 0, d.stderr[-300:])
    r = run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "storyboard.md"], tmp)
    c1 = (tmp / "compositions" / "i01.html").read_text(encoding="utf-8")
    check("avec JSON : DOM cam-frame > cam-content > video",
          re.search(r'<div id="cam-frame-i01"[^>]*><div id="cam-content-i01" class="cam-content"[^>]*><video id="cam-i01"', c1)
          is not None, c1[:200])
    check("avec JSON : plus d'appel applyCam par étape, rien n'anime la balise <video>",
          'applyCam(tl, "#' not in c1 and '"#cam-i01"' not in c1)
    check("avec JSON : data/camera.json écrit", (tmp / "data" / "camera.json").exists())
    check("avec JSON : annotation couverte -> pas d'avertissement", "annotée `camera: cast` :" not in r.stderr, r.stderr[-300:])
    # périmé : on réécrit la vidéo
    sz = (tmp / "assets" / "cast-segments.json").read_text()
    doc = json.loads(sz); doc["source_size"] += 1
    (tmp / "assets" / "cast-segments.json").write_text(json.dumps(doc))
    r = run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "storyboard.md"], tmp)
    check("JSON périmé (taille) -> avertissement", "ne correspond plus" in r.stderr, r.stderr[-300:])
    doc["source_size"] -= 1
    (tmp / "assets" / "cast-segments.json").write_text(json.dumps(doc))
    run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "storyboard.md"], tmp)


def part_b_browser(tmp):
    print("B2. navigateur : seeks avant / arrière / aléatoires")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (saute : Playwright absent)")
        return
    plan_doc = json.loads((tmp / "data" / "camera.json").read_text())
    crop = plan_doc["crop"]
    scenes_json = json.loads((tmp / "data" / "scenes.json").read_text())
    starts = []
    for i in range(3):
        html = (tmp / "compositions" / ("i0%d.html" % i)).read_text(encoding="utf-8")
        starts.append(html)
    pages = tmp / "pages"
    pages.mkdir()
    for f in ("style-joriel.css", "style-joriel-ext.css", "gsap.min.js"):
        shutil.copy(tmp / "assets" / f, pages / f)
    cam_geom = {"pip": (1460, 821, 422, 238, 1), "full": (480, 270, 960, 540, 1), "off": (1460, 821, 422, 238, 0),
                "cast": (0, 0, 1920, 1080, 1)}
    # temps de début de chaque scène (secondes vidéo) : 0, 10, 22
    sc_start = [0.0, 10.0, 22.0]
    cast_doc = json.loads((tmp / "assets" / "cast-segments.json").read_text())
    segsec = [((s["start_frame"] - 0.25) / cast_doc["fps"], (s["end_frame"] - 0.25) / cast_doc["fps"])
              for s in cast_doc["segments"]]
    base_ev = [(0, "pip"), (5, "off"), (16, "pip"), (22, "full"), (26, "off")]

    def expected(t):
        if any(a <= t < b for a, b in segsec):
            return "cast"
        m = "off"
        for tt, mm in base_ev:
            if tt <= t:
                m = mm
        return m

    with sync_playwright() as p:
        br = p.chromium.launch()
        for i, html in enumerate(starts):
            m = re.search(r"<template>(.*?)</template>", html, re.S)
            inner = m.group(1)
            script = re.search(r"<script>(.*)</script>", inner, re.S).group(1)
            body = re.sub(r"<script>.*?</script>", "", inner, flags=re.S)
            body = re.sub(r'<link[^>]*>', "", body)
            body = re.sub(r"<video[^>]*></video>", '<video id="cam-i0%d" muted playsinline></video>' % i, body)
            (pages / ("p%d.html" % i)).write_text(
                '<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="style-joriel.css">'
                '<link rel="stylesheet" href="style-joriel-ext.css"></head><body style="margin:0;width:1920px;height:1080px">'
                + body + '<script src="gsap.min.js"></script><script>' + script + '</script></body></html>',
                encoding="utf-8")
            pg = br.new_page(viewport={"width": 1920, "height": 1080})
            pg.set_default_timeout(15000)
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto((pages / ("p%d.html" % i)).as_uri())
            dur = pg.evaluate("window.__timelines['i0%d'].duration()" % i)
            check("scène i0%d : script exécuté sans erreur, timeline construite" % i, not errs and dur > 0, errs)
            has_content = pg.evaluate("!!document.getElementById('cam-content-i0%d')" % i)
            check("scène i0%d : wrapper .cam-content présent" % i, has_content)
            # instants échantillonnés : milieux d'états stables, plus bornes ±1 image
            ev = json.loads(re.search(r"var CAMEV = (.*?);\n", script).group(1))
            samples = []
            for k, e in enumerate(ev):
                t0 = e["t"] + e["d"] + 0.05
                t1 = (ev[k + 1]["t"] if k + 1 < len(ev) else dur) - 0.05
                if t1 > t0:
                    samples.append((t0 + t1) / 2)
            rng = random.Random(7)
            order = samples + samples[::-1] + rng.sample(samples, len(samples)) * 2
            bad = []
            for tl_t in order:
                pg.evaluate("() => { window.__timelines['i0%d'].seek(%f, false); return 1; }" % (i, tl_t))
                st = pg.evaluate("""(id) => { const f = document.getElementById('cam-frame-' + id), c = document.getElementById('cam-content-' + id);
                  const r = f.getBoundingClientRect(); const cs = getComputedStyle(f);
                  const m = new DOMMatrixReadOnly(getComputedStyle(c).transform);
                  return {l: r.left, t: r.top, w: r.width, h: r.height, o: parseFloat(cs.opacity), a: m.a, f: m.f,
                          bw: parseFloat(cs.borderTopWidth), br: parseFloat(cs.borderTopLeftRadius), sh: cs.boxShadow,
                          vt: getComputedStyle(document.getElementById('cam-' + id)).transform}; }""", "i0%d" % i)
                mode = expected(sc_start[i] + tl_t)
                gl, gt, gw, gh, go = cam_geom[mode]
                ok = approx(st["l"], gl, 1) and approx(st["t"], gt, 1) and approx(st["w"], gw, 1) and approx(st["h"], gh, 1) \
                    and approx(st["o"], go, 0.01)
                if mode == "cast":
                    ok = ok and approx(st["a"], crop["scale"], 1e-4) and approx(st["f"], crop["yPercent"] / 100 * 1080, 0.05) \
                        and st["bw"] == 0 and st["br"] == 0 and st["sh"].startswith("rgba(0, 0, 0, 0)")
                else:
                    ok = ok and approx(st["a"], 1, 1e-6) and approx(st["f"], 0, 1e-6) and st["bw"] >= 3 and st["br"] >= 14 and st["sh"].startswith("rgba(0, 0, 0, 0.65)")
                ok = ok and st["vt"] == "none"
                if not ok:
                    bad.append((round(tl_t, 3), mode, st))
            check("scène i0%d : %d seeks (avant, arrière, aléatoires) conformes à l'état attendu" % (i, len(order)),
                  not bad, bad[:2])
            # le crop bascule exactement aux bornes Cast : une image avant = pas de crop, à la borne = crop (et inversement)
            edge_bad = []
            for e in ev:
                if e["p"] is None or (e["m"] == "cast") == (e["p"] == "cast"):
                    continue
                for dt, want_crop in ((-0.002, e["p"] == "cast"), (0.002, e["m"] == "cast")):
                    pg.evaluate("() => { window.__timelines['i0%d'].seek(%f, false); return 1; }" % (i, e["t"] + dt))
                    a = pg.evaluate("(id) => new DOMMatrixReadOnly(getComputedStyle(document.getElementById('cam-content-' + id)).transform).a", "i0%d" % i)
                    if (a > 1.005) != want_crop:
                        edge_bad.append((e["t"], dt, a))
            check("scène i0%d : le crop bascule exactement aux bornes Cast (avant/après, sens aller)" % i, not edge_bad, edge_bad)
            for e in reversed(ev):
                if e["p"] is None or (e["m"] == "cast") == (e["p"] == "cast"):
                    continue
                for dt, want_crop in ((0.002, e["m"] == "cast"), (-0.002, e["p"] == "cast")):
                    pg.evaluate("() => { window.__timelines['i0%d'].seek(%f, false); return 1; }" % (i, e["t"] + dt))
                    a = pg.evaluate("(id) => new DOMMatrixReadOnly(getComputedStyle(document.getElementById('cam-content-' + id)).transform).a", "i0%d" % i)
                    if (a > 1.005) != want_crop:
                        edge_bad.append((e["t"], dt, a))
            check("scène i0%d : idem en lecture arrière" % i, not edge_bad, edge_bad)
            pg.close()
        br.close()


def main():
    part_a()
    with tempfile.TemporaryDirectory(prefix="cast-build-") as t:
        t = Path(t)
        part_b_build(t)
        part_b_browser(t)
    print()
    if FAILS:
        print("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)))
        return 1
    print("OK : tous les tests passent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
