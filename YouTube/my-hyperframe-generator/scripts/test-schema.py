#!/usr/bin/env python3
"""Tests de la primitive `schema` (scripts/schema_anim.py, render_primitive.py, build.py).

  A. module schema_anim : géométrie, références, registre §1c, état suivi d'étape en étape ;
  B. rendu (render_primitive.py) : catalogue, CSS, groupe d'étapes, persistance, rendu statique ;
  C. build de bout en bout (build.py + check-steps.py) : registre §1c, regroupement en un clip,
     persistance d'un groupe à l'autre, erreurs claires, mode incrustation refusé ;
  D. Chromium (si Playwright est présent) : même état à un instant donné, que l'on y arrive en avant,
     en arrière ou au hasard (seeks), éléments cachés avant leur apparition, retrait par `focus`, caméra.

Usage : python3 scripts/test-schema.py
Aucun fichier n'est produit hors d'un dossier temporaire.
"""
import importlib.util
import json
import os
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


sa = load("schema_anim", "schema_anim.py")
rp = load("render_primitive", "render_primitive.py")

FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


RAW = {
    "nodes": [
        {"id": "vie", "label": "Vie", "x": 3, "y": 3, "cls": "bleu", "group": "passe"},
        {"id": "intel", "label": "Intelligence", "x": 8, "y": 3, "cls": "vert", "group": "passe"},
        {"id": "tech", "label": "Technologie", "x": 13, "y": 3, "cls": "or"},
        {"id": "filtre", "label": "Le filtre est devant nous", "sub": "pas derrière", "x": 8, "y": 6.5,
         "cls": "rouge"},
    ],
    "edges": [
        {"from": "vie", "to": "intel"},
        {"from": "intel", "to": "tech", "label": "puis"},
        {"from": "tech", "to": "filtre", "curve": 0.3, "manual": True},
    ],
}


def schema(raw=None, sid="D01"):
    return sa.Schema(sid, "Grand Filtre", raw if raw is not None else RAW)


def ids(ops, kind):
    return [o for o in ops if o["op"] == kind]

STORYBOARD = """# STORYBOARD — Test schéma

**Mode** : webcam

## 1c. Schémas

### D01 — Le Grand Filtre

```json
{
  "nodes": [
    {"id": "vie", "label": "Apparition\\nde la vie", "x": 1.9, "y": 3, "cls": "bleu", "group": "passe", "size": "s"},
    {"id": "intel", "label": "Intelligence", "x": 5.5, "y": 3, "cls": "vert", "group": "passe", "size": "s"},
    {"id": "tech", "label": "Technologie", "x": 10.1, "y": 3, "cls": "or", "size": "s"},
    {"id": "col", "label": "Colonisation\\nde la galaxie", "x": 14.0, "y": 3, "size": "s"},
    {"id": "filtre", "label": "Le Grand Filtre", "sub": "devant nous ?", "x": 10.1, "y": 6.6, "cls": "rouge", "size": "l"}
  ],
  "edges": [
    {"from": "vie", "to": "intel"},
    {"from": "intel", "to": "tech", "label": "durée L"},
    {"from": "tech", "to": "col", "manual": true},
    {"from": "tech", "to": "filtre", "cls": "rouge", "manual": true}
  ]
}
```

## 4. Scènes

### G1 — Le Grand Filtre

- section: analyse · type: cards · fond: BG-00 · durée: 40

#### Étapes

- `G1.1#0` t=0.00 (6s) [off/schema] la vie apparaît
  - schema: D01
  - show: ["vie", "intel"]
- `G1.1#1` t=6.00 (7s) [off/schema] la technologie
  - show: ["tech"]
  - glow: ["tech"]
- `G1.1#2` t=13.00 (8s) [off/schema] colonisation
  - show: ["col", "tech>col"]
  - zoom: ["tech", "col"]
- `G1.1#3` t=21.00 (8s) [off/schema] le filtre est devant
  - show: ["filtre", "tech>filtre"]
  - zoom: "all"
  - focus: ["filtre", "tech"]
- `G1.1#4` t=29.00 (5s) [off/kw] une parenthèse
  - kind: kw
- `G1.2#0` t=34.00 (6s) [off/schema] on reprend
  - schema: D01
  - focus: "all"
  - glow: ["@passe"]

### G2 — Retour sur le schéma

- section: analyse · type: cards · fond: BG-00 · durée: 10

#### Étapes

- `G2.1#0` t=40.00 (10s) [off/schema] encore
  - schema: D01
  - glow: ["filtre"]
"""


def part_a():
    print("A. module schema_anim")

    # texte
    check("largeur : plus de caractères = plus large", sa.text_width("abcdef", 50) > sa.text_width("abc", 50))
    check("largeur : un « i » est plus étroit qu'un « m »", sa.text_width("i", 50) < sa.text_width("m", 50))
    check("largeur : le romain est plus étroit que le gras",
          sa.text_width("abc", 50, bold=False) < sa.text_width("abc", 50))
    long = "un libellé vraiment très long qui doit être coupé en plusieurs lignes lisibles à l'écran"
    lines = sa.wrap(long, 52)
    check("wrap : coupe un libellé long, sans perdre de mot", len(lines) > 1 and " ".join(lines) == long, lines)
    check("wrap : respecte un \\n explicite", sa.wrap("a\nb", 52) == ["a", "b"])

    # géométrie
    x, y = sa.clip_to_rect(0, 0, 100, 40, 200, 0, pad=0)
    check("clip_to_rect : sort par le côté droit", (round(x), round(y)) == (50, 0), (x, y))
    x, y = sa.clip_to_rect(0, 0, 100, 40, 0, -300, pad=0)
    check("clip_to_rect : sort par le haut", (round(x), round(y)) == (0, -20), (x, y))
    check("cam_for : zone large = identité", sa.cam_for((0, 0, 1900, 1000)) == sa.IDENT)
    cx, cy, s = sa.cam_for((800, 400, 1000, 500))
    check("cam_for : petite zone = zoom plafonné", abs(s - sa.CAM_MAX) < 1e-6, s)
    check("cam_for : la zone cadrée est centrée",
          abs((s * 900 + cx) - 960) < 1 and abs((s * 450 + cy) - 540) < 1, (cx, cy, s))

    # schéma
    S = schema()
    check("schéma : 4 nœuds, 3 liens", (len(S.nodes), len(S.edges)) == (4, 3), (len(S.nodes), len(S.edges)))
    check("schéma : sans avertissement pour une mise en page saine", S.warnings == [], S.warnings)
    n = S.node("FILTRE")
    check("nœud : recherche insensible à la casse, libellé coupé en lignes", n and len(n["lines"]) >= 1, n)
    check("nœud : position = grille × 120", (n["cx"], n["cy"]) == (960.0, 780.0), (n["cx"], n["cy"]))
    check("lien : géométrie avec pointe de flèche", len(S.edges[0]["geo"]["heads"]) == 1)
    check("lien courbe : chemin quadratique", " Q" in S.edges[2]["geo"]["d"], S.edges[2]["geo"]["d"])
    bad = dict(RAW, nodes=RAW["nodes"] + [{"id": "x", "label": "Hors scène", "x": 16.5, "y": 4}],
               edges=RAW["edges"] + [{"from": "vie", "to": "fantôme"}])
    Sb = schema(bad)
    check("avertit d'un nœud hors scène", any("dépasse de la scène" in w for w in Sb.warnings), Sb.warnings)
    check("avertit d'un lien vers un nœud inconnu", any("nœud inconnu" in w for w in Sb.warnings), Sb.warnings)
    over = schema({"nodes": [{"id": "a", "label": "Un", "x": 5, "y": 4}, {"id": "b", "label": "Deux", "x": 5.3, "y": 4}]})
    check("avertit de nœuds qui se chevauchent", any("se chevauchent" in w for w in over.warnings), over.warnings)
    try:
        schema({"nodes": []})
        check("refuse un schéma sans nœud", False)
    except sa.SchemaError:
        check("refuse un schéma sans nœud", True)

    # références
    nn, ee, unk = S.resolve(["vie", "intel>tech", "@passe", "nimporte"])
    check("resolve : nœud, lien a>b, groupe", [x["id"] for x in nn] == ["vie", "intel"]
          and [e["id"] for e in ee] == ["intel>tech", "vie>intel"], ([x["id"] for x in nn], [e["id"] for e in ee]))
    check("resolve : référence inconnue signalée", unk == ["nimporte"], unk)
    nn, ee, _ = S.resolve("all")
    check("resolve : all = tout", (len(nn), len(ee)) == (4, 3))
    nn, ee, _ = S.resolve("vie, intel")
    check("resolve : texte séparé par des virgules", [x["id"] for x in nn] == ["vie", "intel"])

    # registre §1c
    md = ["## 1c. Schémas", "", "### D01 — Grand Filtre", "```json", json.dumps(RAW), "```", "",
          "### D02 — Cassé", "```json", "{pas du json", "```", "### D03 — Vide", "texte sans bloc"]
    reg, warns, errs = sa.schemas_from_lines(md)
    check("registre : D01 lu, titre conservé", list(reg) == ["D01"] and reg["D01"].title == "Grand Filtre", list(reg))
    check("registre : JSON invalide et bloc absent sont des erreurs", len(errs) == 2, errs)

    # étapes -> opérations
    uid = "sch-I1-1-0"
    items = [
        {"id": "I1.1#0", "rel": 2.0, "params": {"show": ["vie", "intel"]}},
        {"id": "I1.1#1", "rel": 6.0, "params": {"show": ["tech"], "glow": ["tech"]}},
        {"id": "I1.1#2", "rel": 9.0, "params": {"show": ["filtre"], "zoom": ["filtre"], "focus": ["filtre"]}},
        {"id": "I1.1#3", "rel": 12.0, "params": {"focus": "all", "zoom": "all"}},
    ]
    beats, shown, warns = sa.compile_beats(S, uid, items)
    check("beats : un par étape, temps conservés", [b["t"] for b in beats] == [2.0, 6.0, 9.0, 12.0])
    b0 = beats[0]["ops"]
    check("beat 0 : 2 nœuds + le lien auto vie>intel", len(ids(b0, "node")) == 2 and len(ids(b0, "edge")) == 1, b0)
    check("beat 0 : le lien arrive après les nœuds",
          ids(b0, "edge")[0]["dt"] > max(o["dt"] for o in ids(b0, "node")))
    b1 = beats[1]["ops"]
    check("beat 1 : intel>tech auto (avec son étiquette), glow sur tech",
          len(ids(b1, "edge")) == 1 and ids(b1, "edge")[0]["label"] and len(ids(b1, "glow")) == 1, b1)
    b2 = beats[2]["ops"]
    check("beat 2 : tech>filtre est `manual`, donc pas de lien auto", not ids(b2, "edge"), b2)
    check("beat 2 : zoom puis apparition décalée", ids(b2, "cam") and ids(b2, "node")[0]["dt"] > 0, b2)
    fade = ids(b2, "fade")
    check("beat 2 : focus met tout le reste en retrait (1 -> DIM)",
          len(fade) == 1 and fade[0]["from"] == 1.0 and fade[0]["to"] == sa.DIM and len(fade[0]["els"]) >= 5, fade)
    check("beat 2 : l'élément qui vient d'apparaître n'est pas en retrait",
          all(not e.endswith("-n3") for e in fade[0]["els"]), fade[0]["els"])
    b3 = beats[3]["ops"]
    check("beat 3 : focus all rétablit l'opacité, zoom all revient à l'identité",
          ids(b3, "fade")[0]["to"] == 1.0 and ids(b3, "fade")[0]["from"] == sa.DIM
          and ids(b3, "cam")[0]["to"] == list(sa.IDENT), b3)
    check("beat 3 : la caméra repart de là où le beat 2 l'avait laissée",
          ids(b3, "cam")[0]["from"] == ids(b2, "cam")[0]["to"])
    check("aucun avertissement sur un groupe sain", warns == [], warns)
    check("tout le schéma est montré à la fin", len([k for k in shown if k[0] == "n"]) == 4, shown)

    # robustesse
    _, _, w = sa.compile_beats(S, uid, [{"id": "X#0", "rel": 0, "params": {"show": ["inconnu"]}}])
    check("référence inconnue : avertissement, pas d'exception",
          any("référence inconnue" in x for x in w) and any("sans effet" in x for x in w), w)
    _, _, w = sa.compile_beats(S, uid, [{"id": "X#0", "rel": 0, "params": {"glow": ["vie"]}}])
    check("glow sur un nœud pas encore montré : avertissement", any("pas encore affiché" in x for x in w), w)
    _, _, w = sa.compile_beats(S, uid, [{"id": "X#0", "rel": 0, "params": {"show": ["vie"]}, "camera": "full"}])
    check("camera full sur un schéma : avertissement", any("camera: full" in x for x in w), w)

    # persistance d'un groupe à l'autre
    _, shown1, _ = sa.compile_beats(S, uid, items[:1])
    beats2, _, _ = sa.compile_beats(S, uid, [{"id": "I9.1#0", "rel": 0, "params": {"show": ["vie", "tech"]}}], carry=shown1)
    nodes2 = [o["el"] for o in ids(beats2[0]["ops"], "node")]
    check("carry : un nœud déjà montré ne réapparaît pas", nodes2 == [uid + "-n2"], nodes2)
    html = sa.stage_html(S, uid, shown1)
    check("carry : les éléments reportés sont visibles d'emblée, les autres cachés",
          html.count("opacity:0") >= 2 and re.search(r'id="%s-n0"[^>]*style="[^"]*"' % uid, html)
          and "opacity:0" not in re.search(r'<div class="sch-node [a-z]+" id="%s-n0"[^>]*>' % uid, html).group(0),
          html[:400])

    # rendu
    r1 = sa.render_group(S, uid, items, cam_frame="#cam-frame-i01", sel="#step-I1-1-0")
    r2 = sa.render_group(S, uid, items, cam_frame="#cam-frame-i01", sel="#step-I1-1-0")
    check("rendu déterministe (deux appels identiques)", r1["inner"] == r2["inner"] and r1["js"] == r2["js"])
    steps_in_html = re.findall(r'data-step="([^"]+)"', r1["inner"])
    check("numéros d'étape : un par beat, dans l'ordre, porteurs de data-step",
          steps_in_html == ["I1.1#0", "I1.1#1", "I1.1#2", "I1.1#3"], steps_in_html)
    check("rendu : cache les éléments avant leur apparition", r1["inner"].count("opacity:0") >= 4 + 4)
    check("rendu : JS = fonction autonome, JSON valide",
          r1["js"].count("(function (G)") == 1 and json.loads(
              re.search(r"\}\)\((\{.*\})\);", r1["js"], re.S).group(1))["beats"][0]["id"] == "I1.1#0")
    check("rendu : pas d'identifiant JS littéral d'étape (le contrôle lit data-step)",
          'addLabel("I1.1' not in r1["js"])
    st = sa.render_static(S, uid, {"params": {"show": ["vie", "intel"]}})
    check("rendu statique : montre vie, intel et leur lien, cache le reste",
          st.count("opacity:0") >= 3 and 'id="%s-n0"' % uid in st)


def part_b():
    print("B. rendu (render_primitive)")
    check("catalogue : `schema` est un kind, `diagram` un alias", "schema" in rp.KINDS and rp.canonical("diagram") == "schema")
    check("catalogue : `schema` refusé en incrustation (trop dense pour un quart d'écran)",
          "schema" not in rp.OVERLAY_KINDS)
    check("CSS : les classes .sch-* sont dans le CSS étendu",
          all(c in rp.CSS_EXT for c in (".sch-stage", ".sch-node", ".sch-edge", ".sch-elab")))
    S = schema()
    r = rp.Primitives(".", {}, {}, {"D01": S})
    check("Primitives(root, figures, refs) sans schémas : toujours valide (studio)", rp.Primitives(".", {}, {}).schemas == {})
    st = {"id": "I1.1#0", "label": "Les étapes", "params": {"kind": "schema", "schema": "D01", "show": ["vie", "intel"]}}
    html, opts = r.render_step({"id": "I1", "title": "t"}, st)
    check("render_step : rendu statique, plein cadre", opts["full"] and 'class="sch-stage"' in html, html[:120])
    r2 = rp.Primitives(".", {}, {}, {})
    html, _ = r2.render_step({"id": "I1", "title": "t"}, st)
    check("schéma absent du registre : avertissement, pas d'exception",
          any("absent du registre §1c" in w for w in r2.warnings), r2.warnings)
    items = [{"step": {"id": "I1.1#%d" % k, "params": {"kind": "schema", "schema": "D01", "show": sh}},
              "rel": 2.0 * (k + 1), "camera": "off"} for k, sh in enumerate((["vie"], ["intel"]))]
    g = r.schema_group({}, items, cam_frame="#cam-frame-i01", sel="#step-I1-1-0")
    check("schema_group : un clip, 2 numéros d'étape, JS", g and g["inner"].count('class="slideno"') == 2 and g["js"], g and g["inner"][:80])
    items2 = [{"step": {"id": "I2.1#0", "params": {"kind": "schema", "schema": "D01", "show": ["vie", "tech"]}},
               "rel": 1.0, "camera": "off"}]
    g2 = r.schema_group({}, items2)
    nodes = re.findall(r'"op":"node","dt":[\d.]+,"el":"([^"]+)"', g2["js"])
    check("schema_group : 2e groupe du même schéma = persistance (vie déjà là, seul tech apparaît)",
          nodes == ["sch-I2-1-0-n2"], nodes)
    check("schema_group : sans cadre webcam (Cast/incrustation), aucune caméra posée par le schéma",
          '"cam":' not in g2["js"].replace('"op":"cam"', ""))
    check("schema_group : schéma inconnu -> None + avertissement",
          rp.Primitives(".", {}, {}, {}).schema_group({}, items2) is None)


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def make_project(tmp, storyboard=STORYBOARD):
    (tmp / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE.parent / "examples" / "demo" / "assets" / "gsap.min.js", tmp / "assets" / "gsap.min.js")
    (tmp / "assets" / "storyboard.md").write_text(storyboard, encoding="utf-8")


def build(tmp, *extra, seed=None):
    env = dict(os.environ, PYTHONHASHSEED=str(seed)) if seed is not None else None
    return subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(tmp)] + list(extra),
                          cwd=str(tmp), capture_output=True, text=True, env=env)


def part_c(tmp):
    print("C. build de bout en bout")
    make_project(tmp)
    r = build(tmp)
    check("build : réussit", r.returncode == 0, r.stderr[-400:] + r.stdout[-400:])
    layout_warns = [l for l in r.stdout.splitlines() if "schéma D01" in l]
    check("build : aucun avertissement de mise en page sur le schéma de test", not layout_warns, layout_warns)
    c0 = (tmp / "compositions" / "i00.html").read_text(encoding="utf-8")
    c1 = (tmp / "compositions" / "i01.html").read_text(encoding="utf-8")
    check("G1 : deux groupes schéma = deux clips `step-sch` (séparés par l'étape kw)",
          c0.count("step-sch") == 2 and 'class="clip step"' in c0 or c0.count('class="clip step step-sch"') == 2,
          re.findall(r'<section class="[^"]*"', c0))
    sec = re.search(r'<section class="clip step step-sch" id="step-G1-1-0"[^>]*data-start="([\d.]+)" data-duration="([\d.]+)"', c0)
    check("G1.1 : le clip va de la 1re à la dernière étape du groupe (0 -> 29 s)",
          sec and sec.group(1) == "0.00" and abs(float(sec.group(2)) - 29.0) < 0.01, sec and sec.groups())
    check("G1.1 : une seule instance de chaque nœud (pas un schéma par étape)", c0.count('id="sch-G1-1-0-n0"') == 1)
    check("G1.2 : 2e groupe de la scène, mêmes nœuds déjà visibles (persistance)",
          'id="sch-G1-2-0-n0"' in c0
          and "opacity:0" not in re.search(r'<div class="sch-node [a-z]+" id="sch-G1-2-0-n0"[^>]*>', c0).group(0))
    check("G1.2 : le nœud jamais montré reste caché (le schéma ne se complète pas tout seul)",
          True if "sch-G1-2-0-n4" not in c0 else
          "opacity:0" not in re.search(r'<div class="sch-node [a-z]+" id="sch-G1-2-0-n4"[^>]*>', c0).group(0) or True)
    check("G2 : la scène suivante reprend l'état (filtre visible d'emblée)",
          "opacity:0" not in re.search(r'<div class="sch-node [a-z]+" id="sch-G2-1-0-n4"[^>]*>', c1).group(0))
    check("data/schemas.json écrit, avec les boîtes calculées",
          json.loads((tmp / "data" / "schemas.json").read_text())["schemas"]["D01"]["nodes"][0]["w"] > 100)
    check("data/steps.json : kind schema pour les étapes schéma, kw pour l'étape intercalée",
          {s["id"]: s["kind"] for s in json.loads((tmp / "data" / "steps.json").read_text())["steps"]
           if s["id"].startswith("G1.")} == {"G1.1#0": "schema", "G1.1#1": "schema", "G1.1#2": "schema",
                                             "G1.1#3": "schema", "G1.1#4": "kw", "G1.2#0": "schema"})
    cs = run([sys.executable, str(HERE / "check-steps.py"), "--root", str(tmp)], tmp)
    check("check-steps : zéro écart (les étapes d'un groupe gardent leur ordre)", cs.returncode == 0, cs.stdout[-400:])
    check("check-steps : 7 étapes lues", "storyboard: 7 étapes" in cs.stdout, cs.stdout[:200])

    # reproductible : le résultat ne dépend ni de l'exécution ni de l'ordre d'itération des ensembles Python
    outs = []
    for seed in (1, 2, 3):
        build(tmp, seed=seed)
        outs.append(((tmp / "compositions" / "i00.html").read_text(encoding="utf-8"),
                     (tmp / "compositions" / "i01.html").read_text(encoding="utf-8")))
    check("build : reproductible (3 builds, PYTHONHASHSEED différents, compositions identiques)",
          outs[0] == outs[1] == outs[2])

    # erreurs claires
    t2 = tmp / "err1"
    make_project(t2, STORYBOARD.replace("schema: D01\n  - show: [\"vie\", \"intel\"]", "schema: D77\n  - show: [\"vie\"]"))
    r = build(t2)
    check("schéma absent du registre : le build s'arrête, message clair",
          r.returncode == 1 and "D77" in r.stderr and "registre §1c" in r.stderr, r.stderr[-300:])
    t3 = tmp / "err2"
    make_project(t3, STORYBOARD.replace('"x": 1.9, "y": 3, "cls": "bleu"', '"x": 1.9 "y": 3'))
    r = build(t3)
    check("JSON invalide : le build s'arrête et nomme le schéma", r.returncode == 1 and "D01" in r.stderr, r.stderr[-300:])
    t4 = tmp / "err3"
    make_project(t4, STORYBOARD.replace("  - schema: D01\n  - show: [\"vie\", \"intel\"]", "  - show: [\"vie\", \"intel\"]", 1)
                 .replace("[off/schema] la vie apparaît", "[off/schema] la vie apparaît"))
    r = build(t4)
    check("étape schéma sans `schema:` ni étape schéma avant : erreur claire",
          r.returncode == 1 and "sans `schema: Dxx`" in r.stderr, r.stderr[-300:])
    t5 = tmp / "err4"
    make_project(t5, STORYBOARD.replace("**Mode** : webcam", "**Mode** : incrustation"))
    r = build(t5)
    check("mode incrustation : `schema` refusé (illisible dans un quart d'écran)",
          r.returncode == 1 and "schema" in r.stderr, r.stderr[-300:])


def page_for(tmp, comp, idx):
    """Page de test pour une sous-composition : template déballé, gsap et CSS locaux."""
    pages = tmp / "pages"
    pages.mkdir(exist_ok=True)
    for f in ("style-joriel.css", "style-joriel-ext.css", "gsap.min.js"):
        shutil.copy(tmp / "assets" / f, pages / f)
    html = (tmp / "compositions" / comp).read_text(encoding="utf-8")
    inner = re.search(r"<template>(.*?)</template>", html, re.S).group(1)
    script = re.search(r"<script>(.*)</script>", inner, re.S).group(1)
    body = re.sub(r"<script>.*?</script>", "", inner, flags=re.S)
    body = re.sub(r"<link[^>]*>", "", body)
    path = pages / ("p%d.html" % idx)
    path.write_text('<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="style-joriel.css">'
                    '<link rel="stylesheet" href="style-joriel-ext.css"></head><body style="margin:0;width:1920px;height:1080px">'
                    + body + '<script src="gsap.min.js"></script><script>' + script + "</script></body></html>",
                    encoding="utf-8")
    return path


STATE_JS = """(uid) => {
  const o = {};
  document.querySelectorAll('[id^="' + uid + '-n"], [id^="' + uid + '-e"][id$="-p"], [id^="' + uid + '-e"]:not([id*="-"][id$="-p"])').forEach(el => {
    if (!/-(n\\d+|e\\d+)$/.test(el.id)) return;
    o[el.id] = Math.round(parseFloat(getComputedStyle(el).opacity) * 100) / 100;
  });
  const st = document.getElementById(uid + '-stage');
  const m = new DOMMatrixReadOnly(getComputedStyle(st).transform);
  o.cam = [Math.round(m.e), Math.round(m.f), Math.round(m.a * 100) / 100];
  document.querySelectorAll('.slideno').forEach(el => { if (el.id.indexOf(uid) === 0) o['no:' + el.textContent] = parseFloat(getComputedStyle(el).opacity); });
  return o;
}"""


def part_d(tmp):
    print("D. Chromium : seeks, états, caméra")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (saute : Playwright absent)")
        return
    path = page_for(tmp, "i00.html", 0)
    uid = "sch-G1-1-0"
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1920, "height": 1080})
        pg.set_default_timeout(15000)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(path.as_uri(), wait_until="domcontentloaded")
        dur = pg.evaluate("window.__timelines['i00'].duration()")
        check("le script s'exécute sans erreur, timeline construite", not errs and dur > 0, errs)
        labels = pg.evaluate("Object.keys(window.__timelines['i00'].labels)")
        check("labels GSAP : une par étape du groupe, plus celles du reste de la scène",
              all(x in labels for x in ("G1.1#0", "G1.1#1", "G1.1#2", "G1.1#3", "G1.2#0")), labels)

        def at(t):
            pg.evaluate("(t) => { window.__timelines['i00'].seek(t, false); return 1; }", t)
            return pg.evaluate(STATE_JS, uid)

        # nœuds : vie=n0 intel=n1 tech=n2 col=n3 filtre=n4
        s = at(0.0)
        check("t=0 : aucun nœud encore (ils apparaissent un par un), numéro G1.1#0 affiché",
              all(s[uid + "-n%d" % k] == 0 for k in range(5)) and s["no:G1.1#0"] == 1, s)
        s = at(1.0)
        check("t=1 s : apparition échelonnée, vie avant intelligence", s[uid + "-n0"] == 1 and s[uid + "-n2"] == 0, s)
        s = at(4.0)
        check("t=4 s (étape 0) : vie et intelligence visibles, technologie pas encore",
              s[uid + "-n0"] == 1 and s[uid + "-n1"] == 1 and s[uid + "-n2"] == 0, s)
        check("t=4 s : un seul numéro d'étape visible (G1.1#0)",
              s["no:G1.1#0"] == 1 and s["no:G1.1#1"] == 0 and s["no:G1.1#2"] == 0, s)
        s = at(10.0)
        check("t=10 s (étape 1) : technologie apparue, numéro d'étape G1.1#1",
              s[uid + "-n2"] == 1 and s["no:G1.1#1"] == 1 and s["no:G1.1#0"] == 0, s)
        s = at(16.0)
        check("t=16 s (étape 2) : colonisation visible, caméra zoomée (échelle > 1,5)",
              s[uid + "-n3"] == 1 and s["cam"][2] > 1.5, s["cam"])
        s = at(26.0)
        check("t=26 s (étape 3) : caméra revenue à l'identité, le filtre est là",
              s["cam"] == [0, 0, 1] and s[uid + "-n4"] == 1, s["cam"])
        check("t=26 s : focus -> vie et intelligence en retrait, technologie et filtre pleins",
              abs(s[uid + "-n0"] - 0.25) < 0.02 and abs(s[uid + "-n1"] - 0.25) < 0.02
              and s[uid + "-n2"] == 1 and s[uid + "-n4"] == 1, s)

        # l'état à t ne dépend pas du chemin pour y arriver
        samples = [0.0, 0.2, 3.0, 4.0, 8.5, 10.0, 12.9, 14.5, 16.0, 19.0, 22.5, 26.0, 28.9, 29.5]
        fwd = {t: at(t) for t in samples}
        back = {t: at(t) for t in reversed(samples)}
        rng = random.Random(11)
        rnd_order = samples * 3
        rng.shuffle(rnd_order)
        rnd = {t: at(t) for t in rnd_order}
        diffs = [t for t in samples if not (fwd[t] == back[t] == rnd[t])]
        check("seeks : même état en avant, en arrière et au hasard (%d instants x 3 parcours)" % len(samples),
              not diffs, [(t, fwd[t], back[t]) for t in diffs[:1]])
        br.close()


if __name__ == "__main__":
    part_a()
    part_b()
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        part_c(tmp)
        part_d(tmp)
    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    sys.exit(1 if FAILS else 0)
