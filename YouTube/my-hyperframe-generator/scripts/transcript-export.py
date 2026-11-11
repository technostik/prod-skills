#!/usr/bin/env python3
"""Sous-titres à deux formats : JSON avec timecodes, TXT sans timecode.

  transcript.json   {language, text, words:[{word,start,end}], segments:[{start,end,text}]}
                    (le format de `video extract-transcript -f json`, lu par build.py --transcript)
  transcript.txt    le texte seul, une ligne par segment, aucun timecode, aucune balise
                    (le même texte que `_ass_to_plain_text` de long_publish)

Trois usages :

  1. Projet (défaut). Lit assets/transcript.json, écrit assets/transcript.txt à côté.
       python3 scripts/transcript-export.py
  2. Génération. Lance d'abord la transcription (CLI `video` de fast-market), puis écrit les deux fichiers.
       python3 scripts/transcript-export.py --from-video assets/voix.wav [--language fr] [--model medium]
  3. Publication avec long_publish. Écrit <stem>_transcript.json et <stem>_transcript.txt AU NOM de la
     vidéo publiée, c'est-à-dire ce que long_publish cherche à côté du fichier : renders/final_transcript.*
       python3 scripts/transcript-export.py --publish final [--publish-dir renders] [--inserts assets/inserts.json]
     Avec --inserts, les temps sont décalés sur la timeline de renders/final.mp4 (les inserts s'ajoutent
     au master : tout ce qui suit une coupe est repoussé de la durée de l'insert).

Le JSON est normalisé : mots et segments toujours présents (reconstitués si l'un manque), temps arrondis
à la milliseconde. Rien d'autre n'est modifié : les mots restent ceux du transcript mesuré.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SENTENCE_END = re.compile(r"[.!?…]+[»\")\]]*$")
MAX_WORDS = 14        # segment reconstitué : au plus ce nombre de mots, sinon coupe à la fin d'une phrase


def die(msg):
    print("erreur : " + msg, file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------- #

def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def normalize(data):
    """Dict ou liste de segments -> {language, text, words, segments}, temps arrondis (ms)."""
    if isinstance(data, list):
        data = {"segments": data}
    if not isinstance(data, dict):
        raise ValueError("transcript illisible : objet ou liste de segments attendu")
    words = []
    for w in data.get("words") or []:
        txt = str(w.get("word") if w.get("word") is not None else w.get("text") or "").strip()
        if txt:
            a = _f(w.get("start"))
            words.append({"word": txt, "start": round(a, 3), "end": round(_f(w.get("end"), a), 3)})
    segments = []
    for s in data.get("segments") or []:
        txt = " ".join(str(s.get("text") or "").split())
        if txt:
            a = _f(s.get("start"))
            segments.append({"start": round(a, 3), "end": round(_f(s.get("end"), a), 3), "text": txt})
    if not words and segments:                       # mots reconstitués, répartis dans le segment
        for s in segments:
            toks = s["text"].split()
            step = max(0.05, (s["end"] - s["start"]) / len(toks))
            for i, tok in enumerate(toks):
                a = s["start"] + i * step
                words.append({"word": tok, "start": round(a, 3), "end": round(a + step, 3)})
    if not segments and words:                       # segments reconstitués : fin de phrase, ou 14 mots
        cur = []
        for w in words:
            cur.append(w)
            if SENTENCE_END.search(w["word"]) or len(cur) >= MAX_WORDS:
                segments.append({"start": cur[0]["start"], "end": cur[-1]["end"],
                                 "text": " ".join(x["word"] for x in cur)})
                cur = []
        if cur:
            segments.append({"start": cur[0]["start"], "end": cur[-1]["end"],
                             "text": " ".join(x["word"] for x in cur)})
    if not words and not segments:
        raise ValueError("transcript vide : ni mots ni segments")
    return {"language": data.get("language") or "fr",
            "text": " ".join(s["text"] for s in segments),
            "words": words, "segments": segments}


def plain_text(data):
    """Une ligne par segment, sans timecode ni balise : le texte que long_publish lit dans <stem>_transcript.txt."""
    lines = []
    for s in data["segments"]:
        t = re.sub(r"\{[^}]*\}", "", s["text"]).strip()
        if t:
            lines.append(t)
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Décalage (inserts de post-render.py)
# --------------------------------------------------------------------------- #

def shift_times(data, cuts):
    """`cuts` : [(t_coupe_sur_le_master, durée_insert)]. Un instant après la coupe est repoussé de la
    durée de l'insert. Un segment à cheval sur une coupe est étiré (l'insert remplace sa voix)."""
    cuts = sorted(cuts)

    def f(t, closed):
        return t + sum(d for c, d in cuts if (c <= t if closed else c < t))

    out = {"language": data["language"], "words": [], "segments": []}
    for w in data["words"]:
        out["words"].append({"word": w["word"], "start": round(f(w["start"], True), 3),
                             "end": round(f(w["end"], False), 3)})
    for s in data["segments"]:
        out["segments"].append({"start": round(f(s["start"], True), 3), "end": round(f(s["end"], False), 3),
                                "text": s["text"]})
    out["text"] = data["text"]
    return {k: out[k] for k in ("language", "text", "words", "segments")}


def load_post_render():
    spec = importlib.util.spec_from_file_location("post_render", HERE / "post-render.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def insert_cuts(manifest_path):
    """Coupes du manifeste d'inserts, sur la timeline du master : [(t, durée)]."""
    pr = load_post_render()
    man = pr.load_manifest(manifest_path)
    steps = pr.load_steps(man["scenario"])
    cuts = []
    for ins in man["inserts"]:
        t, _ = pr.resolve(ins, steps)
        a, b = pr.tc(ins.get("start")), pr.tc(ins.get("end"))
        if a is None or b is None:
            die("insert %s : `start` et `end` sont nécessaires pour décaler les temps" % ins["id"])
        cuts.append((t, b - a))
    return cuts


# --------------------------------------------------------------------------- #
# Écriture
# --------------------------------------------------------------------------- #

def write_pair(data, json_path, txt_path):
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    txt_path.write_text(plain_text(data) + "\n", encoding="utf-8")
    print("écrit : %s (%d mots, %d segments)" % (json_path, len(data["words"]), len(data["segments"])))
    print("écrit : %s (%d lignes, sans timecode)" % (txt_path, len(data["segments"])))


def run_video_cli(src, out_json, language, model):
    video = os.environ.get("VIDEO_CMD") or shutil.which("video")
    if not video:
        die("commande `video` introuvable (CLI fast-market) : l'ajouter au PATH ou définir VIDEO_CMD")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    cmd = [video, "extract-transcript", str(src), "-o", str(out_json), "-l", language, "-m", model,
           "--format", "json"]
    print("$ " + " ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0 or not out_json.exists():
        die("la transcription a échoué (code %s)" % r.returncode)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sous-titres : JSON avec timecodes + TXT sans timecode.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--transcript", default="assets/transcript.json", help="JSON d'entrée (défaut assets/transcript.json)")
    ap.add_argument("--from-video", default=None, metavar="FICHIER", help="transcrire d'abord ce fichier audio ou vidéo (CLI `video`)")
    ap.add_argument("--language", default="fr")
    ap.add_argument("--model", default="medium")
    ap.add_argument("--normalize", action="store_true", help="réécrire aussi le JSON d'entrée, normalisé")
    ap.add_argument("--publish", default=None, metavar="STEM", help="écrire <STEM>_transcript.json/.txt (nom lu par long_publish)")
    ap.add_argument("--publish-dir", default="renders")
    ap.add_argument("--inserts", default=None, metavar="MANIFESTE", help="décaler les temps sur la timeline de final.mp4")
    a = ap.parse_args(argv)

    root = Path(a.root).resolve()
    os.chdir(root)
    src = Path(a.transcript)
    if a.from_video:
        run_video_cli(a.from_video, src, a.language, a.model)
    if not src.exists():
        die("transcript absent : %s (le produire avec --from-video, ou `video extract-transcript … -f json`)" % src)
    try:
        data = normalize(json.loads(src.read_text(encoding="utf-8")))
    except (ValueError, json.JSONDecodeError) as exc:
        die("%s : %s" % (src, exc))

    # projet : le texte seul à côté du JSON
    txt = src.with_suffix(".txt")
    if a.normalize:
        src.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("écrit : %s (normalisé)" % src)
    txt.write_text(plain_text(data) + "\n", encoding="utf-8")
    print("écrit : %s (%d lignes, sans timecode)" % (txt, len(data["segments"])))

    if a.publish:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", a.publish):
            die("--publish : nom de fichier simple attendu (reçu %r)" % a.publish)
        pub = shift_times(data, insert_cuts(a.inserts)) if a.inserts else data
        d = Path(a.publish_dir)
        write_pair(pub, d / (a.publish + "_transcript.json"), d / (a.publish + "_transcript.txt"))
        if a.inserts:
            print("temps décalés sur la timeline de la vidéo finale (inserts : %s)" % a.inserts)


if __name__ == "__main__":
    main()
