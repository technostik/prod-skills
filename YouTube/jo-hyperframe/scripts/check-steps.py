#!/usr/bin/env python3
"""Contrôle de correspondance scénario ↔ slides ↔ timeline (skill hyperframe-joriel).

1. Lit le deck slides et en déduit les étapes : chaque `id: X.N` donne `X.N#0`,
   puis un `#k` par fragment `class="fragment"` de la slide.
2. Lit la section du scénario et en déduit les étapes déclarées (entre accents graves).
3. Vérifie les deux listes identiques, même ordre.
4. Vérifie chaque étape comme label GSAP (`tl.addLabel("X.N#k", ...)`) dans
   `studio.html` + `index.html` + `compositions/`, même ordre.
5. Affiche tous les écarts. Zéro écart exigé (exit 0) avant d'enregistrer.

Usage :
    python3 scripts/check-steps.py [--root .] [--slides assets/03-slides-advanced-slides.md]
        [--scenario assets/02-scenario-hyperframes.md]
        [--sec-start "## 4. Scènes"] [--sec-end "## 5."]
"""
import argparse
import re
import sys
from pathlib import Path

FRAG = re.compile(r"<!--\s*element\s+class\s*=\s*[\"']fragment[\"']\s*-->", re.I)
IDR = re.compile(r"id\s*:\s*([A-Za-z0-9]+\.[0-9]+)", re.I)
SEP = re.compile(r"^\s*---\s*$")


def slides_steps(path):
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    start = 0
    if lines and lines[0].strip() == "---":
        for k in range(1, 40):
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


def scenario_steps(path, sec_start, sec_end):
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(re.escape(sec_start) + r"(.*?)" + re.escape(sec_end), text, re.S)
    sec = m.group(1) if m else text
    return re.findall(r"`([A-Za-z0-9]+\.[0-9]+#[0-9]+)`", sec)


def labels_in(path):
    txt = Path(path).read_text(encoding="utf-8")
    return list(dict.fromkeys(re.findall(r'addLabel\("([A-Za-z0-9]+\.[0-9]+#[0-9]+)"', txt)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--slides", default="assets/03-slides-advanced-slides.md")
    ap.add_argument("--scenario", default="assets/02-scenario-hyperframes.md")
    ap.add_argument("--sec-start", default="## 4. Scènes")
    ap.add_argument("--sec-end", default="## 5.")
    a = ap.parse_args()
    root = Path(a.root)
    sl = slides_steps(root / a.slides)
    sc = scenario_steps(root / a.scenario, a.sec_start, a.sec_end)
    print(f"slides: {len(sl)} étapes | scénario: {len(sc)} étapes")
    ecarts = 0
    if sl != sc:
        ecarts += 1
        print("ÉCART slides ↔ scénario :")
        for i in range(max(len(sl), len(sc))):
            x = sl[i] if i < len(sl) else "—"
            y = sc[i] if i < len(sc) else "—"
            if x != y and i < 20:
                print(f"  pos {i}: slides={x} scénario={y}")
    else:
        print("OK: slides == scénario, même ordre.")
    for name in ["studio.html", "index.html"]:
        f = root / name
        if not f.exists():
            print(f"MANQUANT: {name}")
            ecarts += 1
            continue
        labs = labels_in(f)
        print(f"labels {name}: {len(labs)}")
        if labs != sl:
            ecarts += 1
            print(f"ÉCART étapes ↔ {name} (10 premiers) :")
            shown = 0
            for i in range(max(len(sl), len(labs))):
                x = sl[i] if i < len(sl) else "—"
                y = labs[i] if i < len(labs) else "—"
                if x != y and shown < 10:
                    print(f"  pos {i}: étape={x} label={y}")
                    shown += 1
        else:
            print(f"OK: {name} labels conformes.")
    compdir = root / "compositions"
    if compdir.exists():
        clabs = []
        for f in sorted(compdir.glob("*.html")):
            clabs.extend(labels_in(f))
        print(f"labels compositions/: {len(clabs)}")
        if clabs != sl:
            ecarts += 1
            print("ÉCART étapes ↔ compositions/ (10 premiers) :")
            for i in range(max(len(sl), len(clabs))):
                x = sl[i] if i < len(sl) else "—"
                y = clabs[i] if i < len(clabs) else "—"
                if x != y and i < 10:
                    print(f"  pos {i}: étape={x} label={y}")
        else:
            print("OK: compositions/ labels conformes.")
    if ecarts == 0:
        print(f"CONTRÔLE PASSÉ : zéro écart ({len(sl)} étapes).")
        return 0
    print(f"CONTRÔLE ÉCHOUÉ : {ecarts} famille(s) d'écarts.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
