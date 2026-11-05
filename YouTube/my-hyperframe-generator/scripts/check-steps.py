#!/usr/bin/env python3
"""Contrôle de correspondance storyboard ↔ composition (skill hyperframe-joriel).

1. Lit `assets/storyboard.md` et en déduit les étapes (`I1.1#0`, `S04.3#2`).
2. Si un deck slides existe (mode slides), il doit déclarer les mêmes étapes,
   dans le même ordre. Sinon l'étape est simplement ignorée.
3. Vérifie chaque étape comme label GSAP (`tl.addLabel("X.N#k", ...)`) dans
   `index.html` + `compositions/`, même ordre.
4. Si `studio.html` existe (mode slides), il doit porter les mêmes labels.
5. Affiche tous les écarts. Zéro écart exigé (exit 0) avant d'enregistrer.

Usage :
    python3 scripts/check-steps.py [--root .]
        [--storyboard assets/storyboard.md]
        [--slides assets/slides.md] [--studio studio.html]
        [--sec-start "## 4."] [--sec-end "## 5."]
"""
import argparse
import re
import sys
from pathlib import Path

FRAG = re.compile(r"<!--\s*element\s+class\s*=\s*[\"']fragment[\"']\s*-->", re.I)
IDR = re.compile(r"id\s*:\s*([A-Za-z0-9]+\.[0-9]+)", re.I)
SEP = re.compile(r"^\s*---\s*$")
STEP = re.compile(r"`([A-Za-z0-9]+\.[0-9]+#[0-9]+)`")


def slides_steps(path):
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    start = 0
    if lines and lines[0].strip() == "---":
        for k in range(1, min(40, len(lines))):
            if lines[k].strip() == "---":
                start = k + 1
                break
    chunks, cur = [], []
    for ln in lines[start:]:
        if SEP.match(ln):
            chunks.append("\n".join(cur))
            cur = []
        else:
            cur.append(ln)
    chunks.append("\n".join(cur))
    out = []
    for ch in chunks:
        if not ch.strip():
            continue
        m = IDR.search(ch)
        if not m:
            print(f"AVERTISSEMENT: slide sans id: {ch[:60]!r}")
            continue
        sid = m.group(1)
        nf = len(FRAG.findall(ch))
        out.extend(f"{sid}#{k}" for k in range(nf + 1))
    return out


def storyboard_steps(path, sec_start, sec_end):
    text = Path(path).read_text(encoding="utf-8")
    # section « 4. Scènes » (ou un titre qui contient « scène »), sinon repli explicite
    heads = list(re.finditer(r"^##\s+(.*)$", text, re.M))
    chosen = None
    for i, h in enumerate(heads):
        title = h.group(1)
        if re.match(r"^4\b", title) or "scène" in title.lower() or "scene" in title.lower():
            chosen = i
            break
    if chosen is None:
        m = re.search(re.escape(sec_start) + r"(.*?)" + re.escape(sec_end), text, re.S)
        return list(dict.fromkeys(STEP.findall(m.group(1) if m else text)))
    sub = text[heads[chosen].end():]
    nxt = re.search(r"^##\s+", sub, re.M)
    sec = sub[:nxt.start()] if nxt else sub
    return list(dict.fromkeys(STEP.findall(sec)))


def labels_in(path):
    txt = Path(path).read_text(encoding="utf-8")
    found = re.findall(r'addLabel\("([A-Za-z0-9]+\.[0-9]+#[0-9]+)"', txt)
    found += re.findall(r'data-step="([A-Za-z0-9]+\.[0-9]+#[0-9]+)"', txt)
    return list(dict.fromkeys(found))


def compare(name, expected, got):
    print(f"labels {name}: {len(got)}")
    if got == expected:
        print(f"OK: {name} labels conformes.")
        return 0
    print(f"ÉCART étapes ↔ {name} (10 premiers) :")
    shown = 0
    for i in range(max(len(expected), len(got))):
        x = expected[i] if i < len(expected) else "—"
        y = got[i] if i < len(got) else "—"
        if x != y and shown < 10:
            print(f"  pos {i}: étape={x} label={y}")
            shown += 1
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--storyboard", "--scenario", dest="storyboard",
                    default="assets/storyboard.md")
    ap.add_argument("--slides", default="assets/slides.md")
    ap.add_argument("--studio", default="studio.html")
    ap.add_argument("--sec-start", default="## 4.")
    ap.add_argument("--sec-end", default="## 5.")
    a = ap.parse_args()
    root = Path(a.root)

    sb = root / a.storyboard
    if not sb.exists():
        print(f"MANQUANT: {a.storyboard}")
        if a.storyboard != "assets/storyboard.md":
            print("  (défaut attendu : assets/storyboard.md)")
        return 1
    sc = storyboard_steps(sb, a.sec_start, a.sec_end)
    print(f"storyboard: {len(sc)} étapes")
    if not sc:
        print("ÉCHEC : aucune étape dans le storyboard.")
        return 1

    ecarts = 0
    sl = []
    slide_path = root / a.slides
    if slide_path.exists():
        sl = slides_steps(slide_path)
        print(f"slides: {len(sl)} étapes")
        if sl != sc:
            ecarts += 1
            print("ÉCART slides ↔ storyboard :")
            for i in range(max(len(sl), len(sc))):
                x = sl[i] if i < len(sl) else "—"
                y = sc[i] if i < len(sc) else "—"
                if x != y and i < 20:
                    print(f"  pos {i}: slides={x} storyboard={y}")
        else:
            print("OK: slides == storyboard, même ordre.")
    else:
        print(f"slides ignorées (deck absent : {a.slides})")

    idx = root / "index.html"
    if not idx.exists():
        print("MANQUANT: index.html")
        ecarts += 1

    studio = root / a.studio
    if studio.exists():
        ecarts += compare("studio.html", sc, labels_in(studio))
    else:
        print(f"studio.html ignoré (absent : {a.studio})")

    compdir = root / "compositions"
    if compdir.exists():
        clabs = []
        for f in sorted(compdir.glob("*.html")):
            clabs.extend(labels_in(f))
        ecarts += compare("compositions/", sc, clabs)
    elif idx.exists():
        # composition historique en un seul fichier
        ecarts += compare("index.html", sc, labels_in(idx))

    if ecarts == 0:
        print(f"CONTRÔLE PASSÉ : zéro écart ({len(sc)} étapes).")
        return 0
    print(f"CONTRÔLE ÉCHOUÉ : {ecarts} famille(s) d'écarts.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
