#!/usr/bin/env python3
"""Tests de scripts/transcript-export.py : JSON avec timecodes + TXT sans, nommage long_publish.

Usage : python3 scripts/test-transcript-export.py
"""
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "transcript-export.py"
spec = importlib.util.spec_from_file_location("transcript_export", SCRIPT)
te = importlib.util.module_from_spec(spec)
spec.loader.exec_module(te)

FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def ass_to_plain_text(ass):
    """Copie fidèle de `_ass_to_plain_text` (fast-market, webux/long_publish/utils.py)."""
    lines = []
    for line in ass.splitlines():
        if not line.startswith("Dialogue:"):
            continue
        parts = line.split(",", 9)
        if len(parts) < 10:
            continue
        text = re.sub(r"\{[^}]*\}", "", parts[9].strip())
        if text:
            lines.append(text)
    return "\n".join(lines)


WORDS = [("Bonjour", 0.0, 0.4), ("à", 0.5, 0.6), ("tous.", 0.6, 1.0), ("Voici", 2.0, 2.3), ("la", 2.3, 2.4),
         ("suite", 2.4, 2.8), ("du", 3.0, 3.1), ("film", 3.1, 3.5)]
FULL = {"language": "fr", "text": "x",
        "words": [{"word": w, "start": a, "end": b} for w, a, b in WORDS],
        "segments": [{"start": 0.0, "end": 1.0, "text": " Bonjour à tous. "}, {"start": 2.0, "end": 3.5, "text": "Voici la suite du film"}]}


def main():
    print("A. normalisation et texte")
    n = te.normalize(FULL)
    check("JSON : les 4 clés, temps en secondes", list(n) == ["language", "text", "words", "segments"]
          and n["words"][0] == {"word": "Bonjour", "start": 0.0, "end": 0.4}, n["words"][:1])
    check("JSON : segments nettoyés (espaces)", n["segments"][0]["text"] == "Bonjour à tous.")
    check("TXT : une ligne par segment, aucun timecode",
          te.plain_text(n) == "Bonjour à tous.\nVoici la suite du film", te.plain_text(n))
    check("TXT : aucun chiffre de timecode ni balise ASS", not re.search(r"\d+:\d+|\{|\}", te.plain_text(n)))
    only_words = te.normalize({"words": FULL["words"]})
    check("segments reconstitués à partir des mots (fin de phrase)",
          [s["text"] for s in only_words["segments"]] == ["Bonjour à tous.", "Voici la suite du film"], only_words["segments"])
    only_segs = te.normalize({"segments": FULL["segments"]})
    check("mots reconstitués à partir des segments, dans l'intervalle du segment",
          len(only_segs["words"]) == 8 and 2.0 <= only_segs["words"][3]["start"] < 3.5)
    check("liste de segments seule acceptée", te.normalize(FULL["segments"])["words"])
    try:
        te.normalize({"words": [], "segments": []})
        check("transcript vide refusé", False)
    except ValueError:
        check("transcript vide refusé", True)

    print("B. compatibilité long_publish")
    ass = "[Events]\n" + "\n".join(
        "Dialogue: 0,0:00:%05.2f,0:00:%05.2f,Default,,0,0,0,,{\\k20}%s" % (s["start"], s["end"], s["text"]) for s in n["segments"])
    check("TXT identique à ce que long_publish tire d'un ASS (_ass_to_plain_text)",
          te.plain_text(n) == ass_to_plain_text(ass), (te.plain_text(n), ass_to_plain_text(ass)))

    print("C. écriture, publication, décalage")
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "assets").mkdir()
        (tmp / "assets" / "transcript.json").write_text(json.dumps(FULL), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp)], capture_output=True, text=True)
        check("projet : transcript.txt écrit à côté du JSON", r.returncode == 0 and
              (tmp / "assets" / "transcript.txt").read_text(encoding="utf-8") == "Bonjour à tous.\nVoici la suite du film\n", r.stderr)
        check("projet : le JSON d'entrée n'est pas réécrit sans --normalize",
              json.loads((tmp / "assets" / "transcript.json").read_text())["text"] == "x")
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp), "--publish", "final"], capture_output=True, text=True)
        pj, pt = tmp / "renders" / "final_transcript.json", tmp / "renders" / "final_transcript.txt"
        check("publication : <stem>_transcript.json et .txt dans renders/ (noms lus par long_publish)",
              r.returncode == 0 and pj.exists() and pt.exists(), r.stderr)
        pub = json.loads(pj.read_text(encoding="utf-8"))
        check("publication : JSON au format de `video extract-transcript -f json`",
              set(pub) == {"language", "text", "words", "segments"} and set(pub["words"][0]) == {"word", "start", "end"}
              and set(pub["segments"][0]) == {"start", "end", "text"})
        check("publication : TXT identique à celui du projet", pt.read_text(encoding="utf-8") == (tmp / "assets" / "transcript.txt").read_text(encoding="utf-8"))
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp), "--publish", "../x"], capture_output=True, text=True)
        check("nom de publication invalide refusé", r.returncode == 1 and "nom de fichier simple" in r.stderr)

        # décalage par un insert de 10 s, coupe à 2.0 s (fin de l'étape I1.1#0 : t=0 durée 2)
        (tmp / "assets" / "storyboard.md").write_text(
            "# SB\n\n- `I1.1#0` t=0.00 (2.0s) [off/kw] début\n- `I1.1#1` t=2.00 (2.0s) [off/kw] suite\n", encoding="utf-8")
        (tmp / "assets" / "inserts.json").write_text(json.dumps(
            {"inserts": [{"id": "X1", "source": "clip.mp4", "start": "0:10", "end": "0:20", "after": "I1.1#0"}]}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp), "--publish", "final", "--inserts", "assets/inserts.json"],
                           capture_output=True, text=True)
        sh = json.loads(pj.read_text(encoding="utf-8"))
        check("inserts : ce qui précède la coupe ne bouge pas", sh["words"][2]["start"] == 0.6 and sh["segments"][0]["end"] == 1.0, sh["words"][2])
        check("inserts : ce qui suit la coupe est repoussé de la durée de l'insert (+10 s)",
              sh["words"][3]["start"] == 12.0 and sh["segments"][1]["start"] == 12.0 and sh["segments"][1]["end"] == 13.5, sh["segments"][1])
        check("inserts : le texte ne change pas", (tmp / "renders" / "final_transcript.txt").read_text(encoding="utf-8") == "Bonjour à tous.\nVoici la suite du film\n")
        (tmp / "assets" / "inserts.json").write_text(json.dumps(
            {"inserts": [{"id": "X1", "source": "clip.mp4", "after": "I1.1#0"}]}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp), "--publish", "final", "--inserts", "assets/inserts.json"],
                           capture_output=True, text=True)
        check("inserts sans start/end : erreur claire", r.returncode == 1 and "`start` et `end`" in r.stderr, r.stderr)

        print("D. génération (faux `video` sur le PATH)")
        bindir = tmp / "bin"
        bindir.mkdir()
        fake = bindir / "video"
        fake.write_text("#!/bin/sh\necho \"$@\" > \"%s\"\n"
                        "while [ $# -gt 0 ]; do if [ \"$1\" = \"-o\" ]; then out=\"$2\"; fi; shift; done\n"
                        "cat > \"$out\" <<'EOF2'\n%s\nEOF2\n" % (tmp / "video-args.txt", json.dumps(FULL)), encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        (tmp / "assets" / "transcript.json").unlink()
        (tmp / "assets" / "voix.wav").write_bytes(b"RIFF")
        env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ["PATH"])
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp), "--from-video", "assets/voix.wav", "--language", "fr"],
                           capture_output=True, text=True, env=env)
        args = (tmp / "video-args.txt").read_text(encoding="utf-8") if (tmp / "video-args.txt").exists() else ""
        check("la CLI `video extract-transcript … -f json` est appelée avec langue et modèle",
              r.returncode == 0 and "extract-transcript assets/voix.wav" in args and "-l fr" in args and "-m medium" in args and "--format json" in args,
              (r.stderr, args))
        check("génération : JSON et TXT présents", (tmp / "assets" / "transcript.json").exists() and (tmp / "assets" / "transcript.txt").exists())
        r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp), "--from-video", "assets/voix.wav"],
                           capture_output=True, text=True, env=dict(os.environ, PATH="/nonexistent"))
        check("CLI `video` absente : erreur claire", r.returncode == 1 and "introuvable" in r.stderr, r.stderr)

    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
