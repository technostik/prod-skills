#!/usr/bin/env python3
"""La démo (examples/demo) reste synchrone avec le code : schéma Excalidraw, musique, shorts.

  - `build.py` sur examples/demo/storyboard.md redonne la composition i12 (au calque `demo-label` près),
    data/music.json et data/shorts_segments.json tels qu'ils sont committés ;
  - le schéma D02 contient bien un rond, un rectangle, un losange et des flèches, avec des imbrications ;
  - index.html référence i12 avec les bons temps.

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

    print("C. index.html")
    idx = (DEMO / "index.html").read_text(encoding="utf-8")
    m = re.search(r'id="i12"[^>]*data-composition-src="compositions/i12.html" data-start="([\d.]+)" data-duration="([\d.]+)"', idx)
    check("i12 référencé : début 162,50 s, durée 42 s", m and (m.group(1), m.group(2)) == ("162.50", "42.00"), m and m.groups())
    root = re.search(r'id="root"[^>]*data-duration="([\d.]+)"', idx)
    check("durée du film : 204,50 s", root and root.group(1) == "204.50", root and root.group(1))

    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
