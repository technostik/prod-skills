#!/usr/bin/env python3
"""La démo (examples/demo) reste synchrone avec le code : schéma Excalidraw, musique, shorts.

  - `build.py` sur examples/demo/storyboard.md redonne la composition i12 (au calque `demo-label` près),
    data/music.json et data/shorts_segments.json tels qu'ils sont committés ;
  - le schéma D02 contient bien un rond, un rectangle, un losange et des flèches, avec des imbrications ;
  - index.html référence i12 avec les bons temps ;
  - le CSS étendu de la démo (assets/style-joriel-ext.css) est celui que `build.py` écrit (sinon les formes Excalidraw
    ne sont pas stylées dans la démo) et, dans Chromium, les formes sont bien posées avec CSS de la démo.

Usage : python3 scripts/test-demo.py
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent / "examples" / "demo"
sys.path.insert(0, str(HERE))
import excalidraw_anim as ex  # noqa: E402
import render_primitive as rp  # noqa: E402
import shorts_plan as sp  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def strip_demo(html):
    """Retire le calque d'étiquettes propre à la démo (lien CSS et clips `demo-label`)."""
    html = html.replace('<link rel="stylesheet" href="assets/demo-label.css">\n', "")
    return re.sub(r'<div class="clip demo-label"[^\n]*\n', "", html)


def main():
    print("0. CSS de la démo")
    ext = (DEMO / "assets" / "style-joriel-ext.css").read_text(encoding="utf-8")
    check("assets/style-joriel-ext.css = celui que build.py écrit (CSS_EXT), formes Excalidraw comprises", ext == rp.CSS_EXT and ".exn{" in ext, "regénérer : voir README de la démo")

    print("A. le schéma D01 (I10, I11) : un conteneur imbriqué, un cercle")
    S1 = ex.load_schema(DEMO / "assets" / "schemas" / "D01.excalidraw", "D01")
    k1 = {n["id"]: n["kind"] for n in S1.nodes}
    sb = (DEMO / "storyboard.md").read_text(encoding="utf-8")
    block = sb[sb.index("### D01"):sb.index("### D02")]
    check("D01 : décrit en JSON dans le registre §1c ET relié à un fichier Excalidraw (intermédiaire généré)", "```json" in block and "- fichier: assets/schemas/D01.excalidraw" in block)
    raw = json.loads(re.search(r"```json\n(.*?)\n```", block, re.S).group(1))
    gen_nodes = {n["id"]: n["kind"] for n in ex.ExSchema("D01", "", __import__("excalidraw_gen").build_elements(raw)[0]).nodes}
    check("D01 : le fichier committé a la structure du bloc JSON (mêmes éléments et formes)", gen_nodes == {n["id"]: n["kind"] for n in S1.nodes}, (gen_nodes, {n["id"]: n["kind"] for n in S1.nodes}))
    check("D01 : le bloc JSON n'a plus de fichier source à côté (pas de D01.src.json)", not (DEMO / "assets/schemas/D01.src.json").exists())
    check("D01 : rectangles, un conteneur « École », un cercle", k1 == {"Budget": "rectangle", "École": "rectangle", "Postes": "rectangle", "Heures de cours": "rectangle", "Niveau des élèves": "ellipse"}, k1)
    circle = [n for n in S1.nodes if n["id"] == "Niveau des élèves"][0]
    check("D01 : le cercle est rond (largeur = hauteur)", abs(circle["w"] - circle["h"]) < 1.0, (circle["w"], circle["h"]))
    inside1 = {n["id"] for n in S1.resolve(["@École"])[0]}
    check("D01 : @École contient Postes et Heures de cours, pas Budget ni le cercle", inside1 == {"École", "Postes", "Heures de cours"}, inside1)
    ed = {e["id"]: e for e in S1.edges}
    check("D01 : le lien Budget → Postes traverse le bord de l'École (automatique) ; les deux autres sont à nommer",
          not ed["Budget>Postes"]["manual"] and ed["Postes>Heures de cours"]["manual"] and ed["Heures de cours>Niveau des élèves"]["manual"], {k: v["manual"] for k, v in ed.items()})
    check("D01 : aucun avertissement, et le tampon de validation est à jour", S1.warnings == []
          and json.loads((DEMO / "assets/schemas/D01.validated").read_text(encoding="utf-8"))["sha256"] == __import__("hashlib").sha256((DEMO / "assets/schemas/D01.excalidraw").read_bytes()).hexdigest(), S1.warnings)

    print("A. le schéma D02")
    S = ex.load_schema(DEMO / "assets" / "schemas" / "D02.excalidraw", "D02")
    kinds = {n["id"]: n["kind"] for n in S.nodes}
    check("formes : rond, rectangle, cercle, losange, rectangle", kinds == {"Écosystème": "ellipse", "Équipe": "rectangle", "Idée": "ellipse", "Décision": "diamond", "Résultat": "rectangle"}, kinds)
    check("trois flèches, dont une pointillée (manuelle)", len(S.edges) == 3 and [e["id"] for e in S.edges if e["manual"]] == ["Décision>Équipe"], [(e["id"], e["manual"]) for e in S.edges])
    inside = lambda ref: {n["id"] for n in S.resolve([ref])[0]}  # noqa: E731
    check("imbrication : @Équipe contient Idée ; @Écosystème contient Équipe, Idée, Décision, pas Résultat",
          inside("@Équipe") == {"Équipe", "Idée"} and inside("@Écosystème") == {"Écosystème", "Équipe", "Idée", "Décision"}, (inside("@Équipe"), inside("@Écosystème")))
    check("aucun avertissement de mise en page", S.warnings == [], S.warnings)
    stamp = json.loads((DEMO / "assets" / "schemas" / "D02.validated").read_text(encoding="utf-8"))
    import hashlib
    check("le schéma est validé (tampon à jour)", stamp["sha256"] == hashlib.sha256((DEMO / "assets" / "schemas" / "D02.excalidraw").read_bytes()).hexdigest())
    check("aperçu et liste des éléments présents", (DEMO / "assets/schemas/D02.preview.png").exists() and "Décision" in (DEMO / "assets/schemas/D02.handles.md").read_text(encoding="utf-8"))
    check("la description compacte régénère le même schéma (mêmes éléments)",
          {n["id"] for n in ex.ExSchema("D", "", __import__("excalidraw_gen").build_elements(json.loads((DEMO / "assets/schemas/D02.src.json").read_text(encoding="utf-8")))[0]).nodes} == set(kinds))

    print("B. build de la démo")
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "demo"
        shutil.copytree(DEMO, tmp, ignore=shutil.ignore_patterns("data", "node_modules"))
        for f in (tmp / "assets" / "voix-posthoc-v1.wav",):
            if f.exists():
                f.unlink()                      # la voix factice allonge le film : le plan de musique est calculé sur le storyboard
        r = subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp), "--storyboard", "storyboard.md"], cwd=str(tmp), capture_output=True, text=True)
        check("build : réussit", r.returncode == 0, r.stderr[-400:] + r.stdout[-400:])
        built = (tmp / "compositions" / "i12.html").read_text(encoding="utf-8")
        committed = (DEMO / "compositions" / "i12.html").read_text(encoding="utf-8")
        check("compositions/i12.html : celle du build, au calque demo-label près", strip_demo(committed) == built, "différences : regénérer i12 avec build.py")
        check("compositions/i12.html : une étiquette par étape (6)", committed.count('class="clip demo-label"') == 6)
        for comp in ("i10", "i11"):
            b = (tmp / "compositions" / (comp + ".html")).read_text(encoding="utf-8")
            c = (DEMO / "compositions" / (comp + ".html")).read_text(encoding="utf-8")
            check("compositions/%s.html : celle du build (schéma D01 Excalidraw), au calque demo-label près" % comp, strip_demo(c) == b and 'class="exn ' in c, "regénérer %s avec build.py" % comp)
        check("data/music.json committé = celui du build", json.loads((DEMO / "data" / "music.json").read_text(encoding="utf-8")) == json.loads((tmp / "data" / "music.json").read_text(encoding="utf-8")))
        check("data/shorts_segments.json committé = celui du build", json.loads((DEMO / "data" / "shorts_segments.json").read_text(encoding="utf-8")) == json.loads((tmp / "data" / "shorts_segments.json").read_text(encoding="utf-8")))
        plan = json.loads((tmp / "data" / "music.json").read_text(encoding="utf-8"))
        check("musique : deux repères (la montée, la conclusion), ≈ 17 % du film, pas un fond continu",
              [c["music"] for c in plan["cues"]] == ["M01", "M02"] and 0.1 < plan["coverage"] < 0.3 and abs(plan["total"] - 204.5) < 0.01, (plan["cues"], plan["coverage"], plan["total"]))
        segs = json.loads((tmp / "data" / "shorts_segments.json").read_text(encoding="utf-8"))
        check("shorts : trois séquences au format de video short-extractor, ≤ 3 min",
              len(segs) == 3 and all(set(s) == {"title", "start", "end"} for s in segs) and all(sp.parse_tc(s["end"]) - sp.parse_tc(s["start"]) <= 180 for s in segs), segs)
        cs = subprocess.run([sys.executable, str(HERE / "check-steps.py"), "--root", str(tmp), "--storyboard", "storyboard.md", "--sec-end", "## 6."],
                            cwd=str(tmp), capture_output=True, text=True)
        check("check-steps : 36 étapes du storyboard, toutes dans les compositions (I12 comprise)", cs.returncode == 0 and "36 étapes" in cs.stdout, cs.stdout[-300:])

    print("C. Chromium : les formes sont posées avec le CSS de la démo")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (saute : Playwright absent)")
    else:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            for f in ("style-joriel.css", "style-joriel-ext.css", "gsap.min.js"):
                shutil.copy(DEMO / "assets" / f, tmp / f)           # le CSS COMMITTÉ de la démo, pas celui que le build réécrit
            for comp, end, want in (("i10", 5.0, ("Postes", "Budget")), ("i11", 13.0, ("Niveau des élèves", "Budget")), ("i12", 39.5, ("Résultat", "Décision"))):
                html = (DEMO / "compositions" / (comp + ".html")).read_text(encoding="utf-8")
                inner = re.search(r"<template>(.*?)</template>", html, re.S).group(1)
                script = re.search(r"<script>(.*)</script>", inner, re.S).group(1)
                body = re.sub(r"<link[^>]*>", "", re.sub(r"<script>.*?</script>", "", inner, flags=re.S))
                page = tmp / (comp + ".html")
                page.write_text('<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="style-joriel.css"><link rel="stylesheet" href="style-joriel-ext.css">'
                                '</head><body style="margin:0;width:1920px;height:1080px">' + body + '<script src="gsap.min.js"></script><script>' + script + "</script></body></html>", encoding="utf-8")
                with sync_playwright() as p:
                    br = p.chromium.launch()
                    pg = br.new_page(viewport={"width": 1920, "height": 1080})
                    pg.set_default_timeout(20000)
                    errs = []
                    pg.on("pageerror", lambda e: errs.append(str(e)))
                    pg.goto(page.as_uri(), wait_until="domcontentloaded")
                    pg.evaluate("([c, t]) => { window.__timelines[c].seek(t, false); return 1; }", [comp, end])
                    info = pg.evaluate("""() => { const o = {};
                      document.querySelectorAll('.exn').forEach(e => { const r = e.getBoundingClientRect(); o[e.textContent.trim().split('\\n')[0] || e.id] = {pos: getComputedStyle(e).position, x: r.x, y: r.y, w: r.width, h: r.height, op: parseFloat(getComputedStyle(e).opacity)}; });
                      return o; }""")
                    br.close()
                nodes = list(info.values())
                check("%s : script sans erreur, formes .exn en position absolue (CSS de la démo à jour)" % comp, not errs and nodes and all(n["pos"] == "absolute" for n in nodes), (errs, nodes[:2]))
                check("%s : toutes les formes sont dans l'écran 1920 × 1080" % comp, all(n["x"] >= -5 and n["y"] >= -5 and n["x"] + n["w"] <= 1925 and n["y"] + n["h"] <= 1085 for n in nodes if n["op"] > 0.01),
                      [(k, v) for k, v in info.items() if v["op"] > 0.01 and (v["x"] < -5 or v["x"] + v["w"] > 1925)][:2])

    print("D. index.html")
    idx = (DEMO / "index.html").read_text(encoding="utf-8")
    m = re.search(r'id="i12"[^>]*data-composition-src="compositions/i12.html" data-start="([\d.]+)" data-duration="([\d.]+)"', idx)
    check("i12 référencé : début 162,50 s, durée 42 s", m and (m.group(1), m.group(2)) == ("162.50", "42.00"), m and m.groups())
    root = re.search(r'id="root"[^>]*data-duration="([\d.]+)"', idx)
    check("durée du film : 204,50 s", root and root.group(1) == "204.50", root and root.group(1))

    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
