#!/usr/bin/env python3
"""Tests des schémas Excalidraw (excalidraw_anim.py, excalidraw_gen.py, build.py, outils).

  A. lecture et habillage : couleurs -> thème, texte lié, flèches liées ou non, cadres, imbrications, références ;
  B. génération : description compacte -> fichier .excalidraw (liens, formes, conteneurs, protection) ;
  C. build : `fichier:` dans le registre §1c, erreurs claires, étapes qui pilotent le schéma ;
  D. Chromium : formes réellement rondes / en losange, animation, même état quel que soit le chemin (seeks) ;
  E. aperçu : PNG + liste des éléments à citer.

Usage : python3 scripts/test-excalidraw.py
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
import excalidraw_anim as ex  # noqa: E402
import excalidraw_gen as gen  # noqa: E402
import schema_anim as sa  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def el(id, type, x, y, w, h, **kw):
    e = {"id": id, "type": type, "x": x, "y": y, "width": w, "height": h, "angle": 0, "strokeColor": "#1e1e1e",
         "backgroundColor": "transparent", "strokeWidth": 2, "strokeStyle": "solid", "opacity": 100, "roundness": None,
         "isDeleted": False, "boundElements": [], "groupIds": [], "frameId": None}
    e.update(kw)
    return e


def txt(id, text, x, y, w, h, container=None, fs=28, **kw):
    return el(id, "text", x, y, w, h, text=text, originalText=text, fontSize=fs, textAlign=kw.pop("textAlign", "center"),
              verticalAlign=kw.pop("verticalAlign", "middle"), containerId=container, **kw)


def arrow(id, x, y, pts, a=None, b=None, **kw):
    e = el(id, "arrow", x, y, abs(pts[-1][0]), abs(pts[-1][1]), points=pts, startArrowhead=None, endArrowhead="arrow", **kw)
    if a:
        e["startBinding"] = {"elementId": a, "focus": 0, "gap": 4}
    if b:
        e["endBinding"] = {"elementId": b, "focus": 0, "gap": 4}
    return e


def fixture():
    """Une galaxie (ellipse) qui contient Vie (rectangle vert), Intelligence (losange orange) ; Filtre (rond rouge) dehors."""
    return [
        el("gal", "ellipse", 0, 0, 1000, 560, strokeColor="#1971c2"),
        txt("gal_t", "La galaxie", 380, 20, 240, 36, fs=32, verticalAlign="top"),                    # titre libre dans le conteneur
        el("vie", "rectangle", 100, 220, 260, 120, strokeColor="#2f9e44", backgroundColor="#b2f2bb", roundness={"type": 3}),
        txt("vie_t", "Vie", 120, 250, 220, 40, "vie"),
        el("intel", "diamond", 520, 180, 300, 200, strokeColor="#f08c00"),
        txt("intel_t", "Intelligence", 540, 260, 260, 40, "intel"),
        arrow("a1", 364, 280, [[0, 0], [152, 0]], "vie", "intel"),
        txt("a1_t", "puis", 400, 230, 60, 30, "a1", fs=22),
        el("fil", "ellipse", 520, 680, 300, 140, strokeColor="#e03131"),
        txt("fil_t", "Filtre", 560, 730, 220, 40, "fil"),
        arrow("a2", 670, 384, [[0, 0], [0, 290]], "intel", "fil", strokeColor="#e03131"),
        el("del", "rectangle", 0, 0, 10, 10, isDeleted=True),
    ]


def schema(els=None, sid="D01"):
    return ex.ExSchema(sid, "Test", els if els is not None else fixture())


def part_a():
    print("A. lecture et habillage")
    r = ex.role_of
    check("couleurs : noir et blanc -> plain, gris moyen -> dim", (r("#1e1e1e"), r("#ffffff"), r("#868e96")) == ("plain", "plain", "dim"),
          (r("#1e1e1e"), r("#ffffff"), r("#868e96")))
    check("couleurs : rouge, orange, jaune, vert, bleu, violet, rose",
          (r("#e03131"), r("#f08c00"), r("#fab005"), r("#2f9e44"), r("#1971c2"), r("#6741d9"), r("#e64980"))
          == ("rouge", "or", "or", "vert", "bleu", "bleu", "rouge"), [r(c) for c in ("#e03131", "#f08c00", "#fab005", "#2f9e44", "#1971c2", "#6741d9", "#e64980")])
    check("couleurs : transparent -> aucun rôle ; couleur inconnue -> plain", r("transparent") is None and r("rouge") == "plain")

    S = schema()
    check("éléments supprimés ignorés ; 4 nœuds (le titre « La galaxie » nomme son ellipse), 2 liens", (len(S.nodes), len(S.edges)) == (4, 2), (len(S.nodes), len(S.edges)))
    check("le texte lié nomme la forme ; un texte libre en haut d'une forme vide en est le titre",
          [n["id"] for n in S.nodes] == ["La galaxie", "Vie", "Intelligence", "Filtre"] and S.nodes[0]["kind"] == "ellipse", [n["id"] for n in S.nodes])
    check("formes conservées : rectangle, losange, ellipses", {n["id"]: n["kind"] for n in S.nodes}["Intelligence"] == "diamond"
          and {n["id"]: n["kind"] for n in S.nodes}["Vie"] == "rectangle" and {n["id"]: n["kind"] for n in S.nodes}["Filtre"] == "ellipse")
    check("rôles de couleur : Vie vert, Intelligence or, Filtre rouge", {n["id"]: n["cls"] for n in S.nodes}["Vie"] == "vert"
          and {n["id"]: n["cls"] for n in S.nodes}["Intelligence"] == "or" and {n["id"]: n["cls"] for n in S.nodes}["Filtre"] == "rouge")
    e = {x["id"]: x for x in S.edges}
    check("liens : par les textes des éléments reliés, étiquette lue", "Vie>Intelligence" in e and e["Vie>Intelligence"]["label"] == "puis"
          and "Intelligence>Filtre" in e, list(e))
    check("liens liés aux deux bouts : apparition automatique", not e["Vie>Intelligence"]["manual"])
    check("tête de flèche à l'arrivée seulement", len(e["Vie>Intelligence"]["geo"]["heads"]) == 1)
    check("tout tient dans l'écran 1920 × 1080 (mis à l'échelle)", all(S.rect(n)[0] >= -1 and S.rect(n)[2] <= 1921 and S.rect(n)[1] >= -1 and S.rect(n)[3] <= 1081 for n in S.nodes))
    check("échelle : le dessin est agrandi au plus 3×", S.scale <= 3.0 + 1e-9, S.scale)

    # références
    nn, ee, unk = S.resolve(["vie", "VIE", "Intelligence>Filtre", "intel", "nimporte"])
    check("références : texte (casse libre), a>b, identifiant Excalidraw, inconnue signalée",
          [n["id"] for n in nn] == ["Vie", "Intelligence"] and [x["id"] for x in ee] == ["Intelligence>Filtre"] and unk == ["nimporte"], ([n["id"] for n in nn], unk))
    nn, ee, unk = S.resolve(["@La galaxie"])
    check("@titre : la forme et tout son intérieur (imbrication)",
          {n["id"] for n in nn} == {"La galaxie", "Vie", "Intelligence"} and [x["id"] for x in ee] == ["Vie>Intelligence"] and not unk,
          ({n["id"] for n in nn}, [x["id"] for x in ee], unk))
    check("@titre : le Filtre, hors de la galaxie, n'en fait pas partie", "Filtre" not in {n["id"] for n in S.resolve(["@La galaxie"])[0]})
    check("@forme : par l'identifiant Excalidraw aussi", len(S.resolve(["@gal"])[0]) == 3)
    check("show d'un titre : montre la forme seule, sans son intérieur", [n["id"] for n in S.resolve(["La galaxie"])[0]] == ["La galaxie"])

    # imbrication : les liens ne sont jamais gênés
    html = S.stage_html("u", set(), hidden_until_shown=False)
    check("titre d'un conteneur rendu en haut de la forme, à la taille choisie", "La galaxie" in html)
    check("liens dessinés AU-DESSUS des formes (couche svg après tous les nœuds)",
          html.rindex('class="exn ') < html.index('<svg class="sch-svg"'), "")
    check("formes : ellipse -> <ellipse>, losange -> <polygon>, rectangle -> <rect>",
          html.count("<ellipse") == 2 and html.count("<polygon points=") >= 1 and "<rect " in html)
    hidden = S.stage_html("u", set())
    check("éléments cachés tant qu'ils ne sont pas montrés", hidden.count("opacity:0") >= 4 + 2)

    # flèche sans accroche : rattachée par sa position
    els = fixture()
    els[6] = arrow("a1", 364, 280, [[0, 0], [152, 0]])
    S2 = schema(els)
    check("flèche non accrochée : reliée aux formes qu'elle touche", "Vie>Intelligence" in {x["id"] for x in S2.edges}, [x["id"] for x in S2.edges])
    els = fixture()
    els.append(arrow("free", 900, 700, [[0, 0], [80, 0]]))
    S3 = schema(els)
    free = [x for x in S3.edges if x["a"] is None and x["b"] is None]
    check("flèche libre (aucune forme) : à nommer dans `show`, jamais automatique", len(free) == 1 and free[0]["manual"])

    # avertissements
    els = fixture()
    els.append(el("img", "image", 0, 0, 50, 50))
    S4 = schema(els)
    check("image ignorée avec avertissement", any("images" in w for w in S4.warnings), S4.warnings)
    els = [el("r", "rectangle", 0, 0, 60, 30), txt("r_t", "Un texte beaucoup trop long pour cette petite forme carrée", 0, 0, 50, 20, "r", fs=24)]
    S5 = schema(els)
    check("texte trop long pour sa forme : avertissement (ou rétréci)", any("ne tient pas" in w or "trop petit" in w for w in S5.warnings), S5.warnings)
    els = [el("a", "rectangle", 0, 0, 3000, 2000), txt("a_t", "Petit", 0, 0, 40, 20, "a", fs=12)]
    S6 = schema(els)
    check("texte minuscule à l'écran : avertissement de lisibilité", any("trop petit" in w for w in S6.warnings), S6.warnings)
    els = fixture() + [txt("dup", "Vie", 0, 600, 40, 20, fs=28)]
    S7 = schema(els)
    check("deux éléments au même texte : le second est désigné par son identifiant", any("même" in w or "deux éléments" in w for w in S7.warnings), S7.warnings)
    try:
        ex.ExSchema("D", "", [el("t", "text", 0, 0, 10, 10, text="x", containerId="nope")][:0])
        check("fichier sans élément refusé", False)
    except sa.SchemaError:
        check("fichier sans élément refusé", True)
    check("liste d'éléments nue acceptée (sans enveloppe)", True)

    # cadres : groupes nommés
    els = fixture() + [el("fr", "frame", -20, -20, 500, 400, name="passe")]
    for e_ in els:
        if e_["id"] in ("vie", "vie_t"):
            e_["frameId"] = "fr"
    S8 = schema(els)
    check("cadre nommé = groupe `@passe` (les éléments qui y sont rattachés)", [n["id"] for n in S8.resolve(["@passe"])[0]] == ["Vie"], [n["id"] for n in S8.resolve(["@passe"])[0]])

    # compile : même moteur que les autres schémas
    items = [{"id": "X#0", "rel": 1.0, "params": {"show": ["La galaxie", "Vie", "Intelligence"]}},
             {"id": "X#1", "rel": 5.0, "params": {"show": ["Filtre", "Intelligence>Filtre"], "focus": ["Filtre"], "zoom": ["Filtre"], "glow": ["Filtre"]}}]
    beats, shown, warns = sa.compile_beats(S, "u", items)
    ops0 = [o["op"] for o in beats[0]["ops"]]
    check("compile : formes puis lien automatique Vie>Intelligence", ops0.count("node") == 3 and ops0.count("edge") == 1, ops0)
    glow = [o for o in beats[1]["ops"] if o["op"] == "glow"]
    check("compile : halo par filtre pour les formes (pas de boîte rectangulaire autour d'un rond)", glow and glow[0].get("fx") == "filter", glow)
    check("compile : sans avertissement", warns == [], warns)

    # persistance d'un groupe à l'autre
    r1 = sa.render_group(S, "u1", items[:1])
    r2 = sa.render_group(S, "u2", [dict(items[1], rel=0.0)], carry=r1["shown"])
    nodes2 = re.findall(r'"op":"node","dt":[\d.]+,"el":"([^"]+)"', r2["js"])
    check("persistance : ce que le 1er groupe a montré n'est pas redessiné", nodes2 == ["u2-n%d" % [n["id"] for n in S.nodes].index("Filtre")], nodes2)


def part_b():
    print("B. génération .excalidraw")
    raw = {"nodes": [
        {"id": "gal", "label": "La galaxie", "x": 8, "y": 4.6, "w": 1500, "h": 800, "cls": "bleu", "shape": "ellipse", "valign": "top"},
        {"id": "vie", "label": "Vie", "x": 4, "y": 4.2, "cls": "vert", "size": "s"},
        {"id": "intel", "label": "Intelligence", "x": 8.5, "y": 4.2, "cls": "or", "size": "s", "shape": "diamond"},
        {"id": "fil", "label": "Filtre", "x": 12, "y": 4.2, "cls": "rouge", "shape": "ellipse", "size": "s"}],
        "edges": [{"from": "vie", "to": "intel"}, {"from": "intel", "to": "fil", "label": "fin", "curve": 0.2}, {"from": "vie", "to": "fil", "dir": "<->"}]}
    els, warns = gen.build_elements(raw)
    doc = gen.to_document(els)
    check("enveloppe Excalidraw : type, version, éléments, appState sombre, files", doc["type"] == "excalidraw" and doc["version"] == 2
          and isinstance(doc["elements"], list) and doc["appState"]["viewBackgroundColor"] == gen.BG and doc["files"] == {})
    ids = [e["id"] for e in els]
    check("identifiants uniques", len(ids) == len(set(ids)))
    byid = {e["id"]: e for e in els}
    need = {"id", "type", "x", "y", "width", "height", "angle", "strokeColor", "backgroundColor", "fillStyle", "strokeWidth", "strokeStyle",
            "roughness", "opacity", "groupIds", "frameId", "roundness", "seed", "version", "versionNonce", "isDeleted", "boundElements",
            "updated", "link", "locked"}
    check("chaque élément porte les champs standard d'Excalidraw", all(need <= set(e) for e in els), [e["id"] for e in els if not need <= set(e)])
    texts = [e for e in els if e["type"] == "text"]
    check("textes : fontFamily, originalText, containerId, lineHeight", all({"fontFamily", "originalText", "containerId", "lineHeight", "textAlign", "verticalAlign"} <= set(t) for t in texts))
    check("formes : rectangle / ellipse / losange gardés", {e["type"] for e in els} >= {"ellipse", "diamond", "rectangle", "arrow", "text"})
    first = [e["id"] for e in els if e["type"] in ("ellipse", "rectangle", "diamond")]
    check("le conteneur est dessiné avant ce qu'il contient (profondeur)", first[0] == [e["id"] for e in els if e["type"] == "ellipse"][0]
          and byid[first[0]]["width"] == 1500.0, first)
    arrows = [e for e in els if e["type"] == "arrow"]
    check("flèches liées aux deux formes, et formes qui connaissent leurs flèches",
          all(a["startBinding"] and a["endBinding"] for a in arrows)
          and all({"id": a["id"], "type": "arrow"} in byid[a["startBinding"]["elementId"]]["boundElements"]
                  and {"id": a["id"], "type": "arrow"} in byid[a["endBinding"]["elementId"]]["boundElements"] for a in arrows))
    check("flèche courbe : 3 points + arrondi ; double sens : tête au départ", any(len(a["points"]) == 3 and a["roundness"] for a in arrows)
          and any(a["startArrowhead"] == "arrow" for a in arrows))
    # les bouts de flèche sont sur le bord des formes rondes (pas sur la boîte englobante)
    import math
    d = byid[[a for a in arrows if a["startBinding"]["elementId"] != a["endBinding"]["elementId"]][0]["endBinding"]["elementId"]]
    a0 = [a for a in arrows if a["endBinding"]["elementId"] == d["id"]][0]
    tip = (a0["x"] + a0["points"][-1][0], a0["y"] + a0["points"][-1][1])
    cx, cy = d["x"] + d["width"] / 2, d["y"] + d["height"] / 2
    if d["type"] == "diamond":
        k = abs(tip[0] - cx) / (d["width"] / 2) + abs(tip[1] - cy) / (d["height"] / 2)
    else:
        k = math.hypot((tip[0] - cx) / (d["width"] / 2), (tip[1] - cy) / (d["height"] / 2))
    check("bout de flèche sur le bord du %s (à l'écart près)" % d["type"], 1.0 <= k <= 1.12, k)

    S = ex.ExSchema("D01", "", els)
    check("rechargé par excalidraw_anim : mêmes éléments, mêmes liens", {n["id"] for n in S.nodes} == {"La galaxie", "Vie", "Intelligence", "Filtre"}
          and len(S.edges) == 3, ({n["id"] for n in S.nodes}, len(S.edges)))
    check("rechargé : aucun avertissement de mise en page", S.warnings == [], S.warnings)
    check("rechargé : @La galaxie contient la forme et les trois autres éléments", len(S.resolve(["@La galaxie"])[0]) == 4)

    _, w = gen.build_elements({"nodes": [{"id": "a", "label": "A", "x": 2, "y": 3, "cls": "violet"}, {"id": "b", "label": "B", "x": 8, "y": 3, "shape": "hexagone"}],
                               "edges": [{"from": "a", "to": "zzz"}, {"from": "a", "to": "b", "label": "une étiquette vraiment trop large pour ce lien"}]})
    check("avertit : cls inconnue, forme inconnue, lien vers un nœud inconnu, étiquette trop large",
          sum(any(k in x for x in w) for k in ("cls", "forme", "nœud inconnu", "plus large")) == 4, w)
    try:
        gen.build_elements({"nodes": []})
        check("description vide refusée", False)
    except sa.SchemaError:
        check("description vide refusée", True)
    md = "# SB\n\n## 1c. Registre\n\n### D01 — Un\n\n```json\n%s\n```\n\n### D02 — Deux\n\n```json\n{\"nodes\": [{\"id\": \"z\"}]}\n```\n" % json.dumps(raw)
    check("bloc JSON repris du registre §1c d'un storyboard", gen.raw_from_storyboard(md, "D02")["nodes"][0]["id"] == "z" and
          len(gen.raw_from_storyboard(md, "D01")["nodes"]) == 4)
    try:
        gen.raw_from_storyboard(md, "D09")
        check("schéma absent du storyboard : erreur", False)
    except sa.SchemaError:
        check("schéma absent du storyboard : erreur", True)


def write_doc(path, els):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"type": "excalidraw", "version": 2, "elements": els}), encoding="utf-8")


STORYBOARD = """# STORYBOARD — Test Excalidraw

**Mode** : webcam

## 1c. Registre des schémas

### D01 — Le Grand Filtre

- fichier: assets/schemas/D01.excalidraw

## 4. Scènes

### G1 — Le Grand Filtre

- section: analyse · type: cards · fond: BG-00 · durée: 40

#### Étapes

- `G1.1#0` t=0.00 (6s) [off/schema] la galaxie
  - kind: schema
  - schema: D01
  - show: ["La galaxie"]
- `G1.1#1` t=6.00 (7s) [off/schema] vie et intelligence
  - show: ["Vie", "Intelligence"]
  - glow: ["Intelligence"]
- `G1.1#2` t=13.00 (8s) [off/schema] zoom
  - show: ["Filtre"]
  - zoom: ["Intelligence", "Filtre"]
- `G1.1#3` t=21.00 (8s) [off/schema] focus
  - zoom: "all"
  - focus: ["Filtre", "Intelligence"]
- `G1.1#4` t=29.00 (11s) [off/schema] retour
  - focus: "all"
  - glow: ["@La galaxie"]
"""


def build(tmp, *extra):
    return subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp)] + list(extra), cwd=str(tmp), capture_output=True, text=True)


def project(tmp, storyboard=STORYBOARD, els=None):
    (tmp / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE.parent / "examples" / "demo" / "assets" / "gsap.min.js", tmp / "assets" / "gsap.min.js")
    (tmp / "assets" / "storyboard.md").write_text(storyboard, encoding="utf-8")
    if els is not None:
        write_doc(tmp / "assets" / "schemas" / "D01.excalidraw", els)


def part_c(tmp):
    print("C. build avec `fichier:`")
    project(tmp, els=fixture())
    r = build(tmp)
    check("build : réussit, aucun avertissement de schéma", r.returncode == 0 and "schéma D01" not in r.stdout, r.stderr[-300:] + r.stdout[-300:])
    c0 = (tmp / "compositions" / "i00.html").read_text(encoding="utf-8")
    check("un seul clip pour les 5 étapes, formes habillées", c0.count('class="clip step step-sch"') == 1 and 'class="exn ' in c0 and "<ellipse" in c0 and "<polygon" in c0)
    check("data/schemas.json : schéma Excalidraw décrit (formes, éléments, échelle)",
          json.loads((tmp / "data" / "schemas.json").read_text())["schemas"]["D01"]["kind"] == "excalidraw")
    cs = subprocess.run([sys.executable, str(HERE / "check-steps.py"), "--root", str(tmp)], cwd=str(tmp), capture_output=True, text=True)
    check("check-steps : zéro écart", cs.returncode == 0, cs.stdout[-300:])

    t2 = tmp / "e1"
    project(t2)
    r = build(t2)
    check("fichier absent : le build s'arrête et renvoie vers schema-to-excalidraw.py", r.returncode == 1 and "D01" in r.stderr and "schema-to-excalidraw.py" in r.stderr, r.stderr[-300:])
    t3 = tmp / "e2"
    project(t3)
    (t3 / "assets" / "schemas").mkdir()
    (t3 / "assets" / "schemas" / "D01.excalidraw").write_text("{pas du json", encoding="utf-8")
    r = build(t3)
    check("fichier invalide : message clair", r.returncode == 1 and "pas un JSON valide" in r.stderr, r.stderr[-300:])
    t4 = tmp / "e3"
    project(t4, STORYBOARD.replace('["Vie", "Intelligence"]', '["Viee", "Intelligence"]'), fixture())
    r = build(t4)
    check("référence inconnue dans une étape : avertissement qui nomme l'élément", r.returncode == 0 and "Viee" in r.stdout, r.stdout[-300:])
    t5 = tmp / "e4"
    project(t5, els=[e for e in fixture() if e["id"] not in ("vie", "vie_t", "a1", "a1_t")])
    r = build(t5)
    check("élément cité qui n'existe plus dans le fichier retouché : avertissement", "référence inconnue `Vie`" in r.stdout or "Vie" in r.stdout, r.stdout[-300:])
    t6 = tmp / "inline"
    project(t6, STORYBOARD.replace("- fichier: assets/schemas/D01.excalidraw", '```json\n{"nodes": [{"id": "A", "label": "A", "x": 4, "y": 4}, {"id": "B", "label": "B", "x": 10, "y": 4}], "edges": [{"from": "A", "to": "B"}]}\n```').replace('["La galaxie"]', '["A", "B"]').replace('["Vie", "Intelligence"]', '["A"]').replace('["Filtre"]', '["B"]').replace('["Intelligence", "Filtre"]', '["A", "B"]').replace('["Filtre", "Intelligence"]', '["A"]').replace('["Intelligence"]', '["A"]').replace('"@La galaxie"', '"A"'))
    r = build(t6)
    check("l'ancien format (bloc JSON dans le registre) fonctionne toujours", r.returncode == 0 and "sch-node" in (t6 / "compositions" / "i00.html").read_text(encoding="utf-8"), r.stderr[-300:] + r.stdout[-200:])


def page_for(tmp, comp):
    pages = tmp / "pages"
    pages.mkdir(exist_ok=True)
    for f in ("style-joriel.css", "style-joriel-ext.css", "gsap.min.js"):
        shutil.copy(tmp / "assets" / f, pages / f)
    html = (tmp / "compositions" / comp).read_text(encoding="utf-8")
    inner = re.search(r"<template>(.*?)</template>", html, re.S).group(1)
    script = re.search(r"<script>(.*)</script>", inner, re.S).group(1)
    body = re.sub(r"<link[^>]*>", "", re.sub(r"<script>.*?</script>", "", inner, flags=re.S))
    path = pages / "p.html"
    path.write_text('<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="style-joriel.css">'
                    '<link rel="stylesheet" href="style-joriel-ext.css"></head><body style="margin:0;width:1920px;height:1080px">'
                    + body + '<script src="gsap.min.js"></script><script>' + script + "</script></body></html>", encoding="utf-8")
    return path


STATE_JS = """(uid) => {
  const o = {};
  document.querySelectorAll('[id^="' + uid + '-n"]').forEach(el => { if (/-n\\d+$/.test(el.id)) o[el.id] = Math.round(parseFloat(getComputedStyle(el).opacity) * 100) / 100; });
  const st = document.getElementById(uid + '-stage');
  const m = new DOMMatrixReadOnly(getComputedStyle(st).transform);
  o.cam = [Math.round(m.e), Math.round(m.f), Math.round(m.a * 100) / 100];
  return o;
}"""


def part_d(tmp):
    print("D. Chromium : formes, animation, seeks")
    try:
        from playwright.sync_api import sync_playwright
        from PIL import Image
    except ImportError:
        print("  (saute : Playwright ou Pillow absent)")
        return
    root = tmp / "shapes"
    project(root, els=[
        el("e", "ellipse", 100, 100, 800, 400, strokeColor="#1971c2", strokeWidth=4), txt("e_t", "Rond", 0, 0, 10, 10, "e"),
        el("d", "diamond", 1100, 100, 800, 400, strokeColor="#e03131", strokeWidth=4), txt("d_t", "Losange", 0, 0, 10, 10, "d"),
        el("r", "rectangle", 100, 700, 800, 300, strokeColor="#2f9e44", strokeWidth=4), txt("r_t", "Carré", 0, 0, 10, 10, "r")])
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location("excalidraw_preview", HERE / "excalidraw-preview.py")
    prev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prev)
    S = ex.load_schema(root / "assets" / "schemas" / "D01.excalidraw", "D01")
    html = prev.page_html(S)
    ph = root / "shapes.html"
    ph.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1920, "height": 1080})
        pg.set_default_timeout(20000)
        pg.goto(ph.as_uri(), wait_until="domcontentloaded")
        pg.wait_for_timeout(150)
        shot = root / "shapes.png"
        pg.screenshot(path=str(shot))
        im = Image.open(shot).convert("RGB")
        nd = {n["id"]: n for n in S.nodes}

        def stroke_like(px, role):
            r, g, b = px
            tr, tg, tb = int(sa.COLORS[role][1:3], 16), int(sa.COLORS[role][3:5], 16), int(sa.COLORS[role][5:7], 16)
            return abs(r - tr) < 60 and abs(g - tg) < 60 and abs(b - tb) < 60

        def at(n, dx, dy):                     # pixel à (dx, dy) du coin haut-gauche de la boîte du nœud
            return im.getpixel((int(n["x"] + dx), int(n["y"] + dy)))
        e, d, r = nd["Rond"], nd["Losange"], nd["Carré"]
        check("ellipse : le sommet est tracé, le coin de la boîte est vide (c'est bien un rond)",
              stroke_like(at(e, e["w"] / 2, 2.5), "bleu") and not stroke_like(at(e, 6, 6), "bleu") and sum(at(e, 6, 6)) < 60, (at(e, e["w"] / 2, 2.5), at(e, 6, 6)))
        check("losange : la pointe du haut est tracée, le coin de la boîte est vide",
              stroke_like(at(d, d["w"] / 2, 2.5), "rouge") and sum(at(d, 6, 6)) < 60, (at(d, d["w"] / 2, 2.5), at(d, 6, 6)))
        check("rectangle : le coin est tracé (le test distingue bien les formes)", stroke_like(at(r, 4, r["h"] / 2), "vert"), at(r, 4, r["h"] / 2))
        br.close()

    # animation et seeks sur le build complet
    project(tmp / "anim", els=fixture())
    build(tmp / "anim")
    path = page_for(tmp / "anim", "i00.html")
    uid = "sch-G1-1-0"
    nodes = {n["id"]: "n%d" % n["i"] for n in ex.load_schema(tmp / "anim" / "assets" / "schemas" / "D01.excalidraw", "D01").nodes}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1920, "height": 1080})
        pg.set_default_timeout(20000)
        errs = []
        pg.on("pageerror", lambda x: errs.append(str(x)))
        pg.goto(path.as_uri(), wait_until="domcontentloaded")
        check("le script s'exécute sans erreur", not errs, errs)

        def at(t):
            pg.evaluate("(t) => { window.__timelines['i00'].seek(t, false); return 1; }", t)
            return pg.evaluate(STATE_JS, uid)
        s = at(0.0)
        check("t=0 : rien n'est visible", all(s[uid + "-" + k] == 0 for k in nodes.values()), s)
        s = at(4.0)
        check("t=4 s : la galaxie est là, pas la vie", s[uid + "-" + nodes["La galaxie"]] == 1 and s[uid + "-" + nodes["Vie"]] == 0, s)
        s = at(10.0)
        check("t=10 s : Vie et Intelligence visibles, Filtre pas encore", s[uid + "-" + nodes["Vie"]] == 1 and s[uid + "-" + nodes["Intelligence"]] == 1 and s[uid + "-" + nodes["Filtre"]] == 0, s)
        s = at(16.0)
        check("t=16 s : caméra zoomée sur Intelligence et Filtre", s["cam"][2] > 1.1, s["cam"])
        s = at(25.0)
        check("t=25 s : retour à la vue d'ensemble, Vie en retrait (focus)", s["cam"] == [0, 0, 1] and abs(s[uid + "-" + nodes["Vie"]] - 0.25) < 0.02, s)
        samples = [0.0, 3.0, 8.0, 10.0, 14.0, 16.0, 19.0, 23.0, 25.0, 30.0, 35.0]
        fwd = {t: at(t) for t in samples}
        back = {t: at(t) for t in reversed(samples)}
        rnd = list(samples) * 3
        random.Random(5).shuffle(rnd)
        rr = {t: at(t) for t in rnd}
        diffs = [t for t in samples if not (fwd[t] == back[t] == rr[t])]
        check("seeks : même état en avant, en arrière et au hasard (%d instants)" % len(samples), not diffs, [(t, fwd[t], back[t]) for t in diffs[:1]])
        br.close()


def part_e(tmp):
    print("E. aperçu et génération en ligne de commande")
    root = tmp / "cli"
    (root / "assets" / "schemas").mkdir(parents=True)
    src = root / "assets" / "schemas" / "D01.src.json"
    src.write_text(json.dumps({"nodes": [{"id": "a", "label": "Un", "x": 4, "y": 4.5, "cls": "bleu"}, {"id": "b", "label": "Deux", "x": 12, "y": 4.5, "shape": "ellipse", "cls": "vert"}],
                               "edges": [{"from": "a", "to": "b", "label": "va"}]}), encoding="utf-8")
    cmd = [sys.executable, str(HERE / "schema-to-excalidraw.py"), "--root", str(root), "--json", "assets/schemas/D01.src.json", "--id", "D01"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root))
    f = root / "assets" / "schemas" / "D01.excalidraw"
    check("génération : fichier .excalidraw écrit", r.returncode == 0 and f.exists(), r.stderr[-300:])
    hp = root / "assets" / "schemas" / "D01.handles.md"
    check("aperçu : D01.handles.md liste les éléments à citer", hp.exists() and "Un" in hp.read_text(encoding="utf-8") and "Un>Deux" in hp.read_text(encoding="utf-8"))
    png = root / "assets" / "schemas" / "D01.preview.png"
    try:
        import playwright  # noqa: F401
        check("aperçu : D01.preview.png écrit (1920 × 1080)", png.exists() and png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n")
    except ImportError:
        check("aperçu : page HTML écrite si Playwright absent", (root / "assets" / "schemas" / "D01.preview.html").exists())
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root))
    check("jamais d'écrasement silencieux d'un fichier existant (retouché à la main)", r.returncode == 1 and "--force" in r.stderr, r.stderr[-200:])
    r = subprocess.run(cmd + ["--force", "--no-preview"], capture_output=True, text=True, cwd=str(root))
    check("--force régénère", r.returncode == 0)
    r = subprocess.run([sys.executable, str(HERE / "excalidraw-preview.py"), str(f), "--no-write"], capture_output=True, text=True)
    check("excalidraw-preview --no-write : n'écrit rien, affiche la liste", r.returncode == 0 and "Deux" in r.stdout)
    r = subprocess.run([sys.executable, str(HERE / "excalidraw-preview.py"), str(root / "nope.excalidraw")], capture_output=True, text=True)
    check("aperçu d'un fichier absent : erreur claire", r.returncode == 1 and "introuvable" in r.stderr, r.stderr)


def main():
    part_a()
    part_b()
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        part_c(tmp)
        part_d(tmp)
        part_e(tmp)
    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
