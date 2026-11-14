#!/usr/bin/env python3
"""Prépare shorts_segments.json pour `video short-extractor`, sur la timeline de la vidéo à découper.

`build.py` écrit data/shorts_segments.json sur la timeline du master. Si des inserts ont été ajoutés (post-render.py), la vidéo
finale est plus longue : les temps sont décalés comme le fait `transcript-export.py --publish`.

  python3 scripts/shorts-export.py                                   # data/shorts_segments.json -> renders/shorts_segments.json
  python3 scripts/shorts-export.py --inserts assets/inserts.json     # temps décalés sur renders/final.mp4

Puis, avec la commande de fast-market :

  video short-extractor renders/final.mp4 --segments renders/shorts_segments.json --layout fit-blur --output-dir shorts/

(les fichiers de sortie sont nommés d'après le titre de chaque séquence, sinon numérotés).
"""
import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shorts_plan as sp  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="shorts_segments.json sur la timeline de la vidéo finale.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--segments", default="data/shorts_segments.json")
    ap.add_argument("--out", default="renders/shorts_segments.json")
    ap.add_argument("--inserts", default=None, help="manifeste d'inserts : décale les temps sur la timeline de final.mp4")
    ap.add_argument("--video", default="renders/final.mp4", help="la vidéo à découper (pour la commande affichée)")
    a = ap.parse_args(argv)
    os.chdir(Path(a.root).resolve())
    src = Path(a.segments)
    if not src.exists():
        print("erreur : %s absent : le storyboard n'a pas de section `## 6. Shorts` (ou build.py n'a pas été relancé)" % src, file=sys.stderr)
        sys.exit(1)
    items = json.loads(src.read_text(encoding="utf-8"))
    segs = [{"title": i["title"], "start": sp.parse_tc(i["start"]), "end": sp.parse_tc(i["end"])} for i in items]
    if a.inserts:
        spec = importlib.util.spec_from_file_location("transcript_export", HERE / "transcript-export.py")
        te = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(te)
        segs = sp.shift(segs, te.insert_cuts(a.inserts))
        print("temps décalés sur la timeline de la vidéo finale (inserts : %s)" % a.inserts)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sp.extractor_list(segs), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("écrit : %s (%d séquences)" % (out, len(segs)))
    for s in segs:
        print("  %s → %s  (%.0f s)  %s" % (sp.fmt_tc(s["start"]), sp.fmt_tc(s["end"]), s["end"] - s["start"], s["title"]))
    print("\nvideo short-extractor %s --segments %s --layout fit-blur --output-dir shorts/" % (a.video, out))


if __name__ == "__main__":
    main()
