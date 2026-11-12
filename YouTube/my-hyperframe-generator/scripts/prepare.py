#!/usr/bin/env python3
"""Préparation : tout ce qui est nécessaire pour écrire le storyboard, avant le storyboard.

La voix et le transcript passent AVANT le storyboard (auto : voix de synthèse tirée du scénario ; webcam et
incrustation : la prise, que le locuteur dicte ; la skill n'écrit jamais le storyboard sur une voix qui n'existe pas
encore). Même chose pour les fonds, les références, les chapitres, les screencasts et les schémas.

  python3 scripts/prepare.py init --mode auto|webcam|incrustation   # dossiers, gabarits, checklist du mode
  python3 scripts/prepare.py check                                  # l'état de chaque livrable ; code 1 s'il bloque
  python3 scripts/prepare.py chapters                               # chapitres : titres du scénario alignés sur le transcript
  python3 scripts/prepare.py validate-schema D01                    # marque un schéma Excalidraw comme validé

Livrables (détail : references/preparation.md) :
  assets/transcript.json + transcript.txt   ce qui est dit, avec timecodes / sans timecode  (transcript-export.py)
  assets/assets.md                          les fonds d'écran : ID | Description | Fichier | Statut
  assets/refs.md                            les références (sources) et les assets de référence (auteur cité)
  assets/figures.md                         les chiffres et leur source
  assets/chapters.json + chapters.txt       les chapitres (format YouTube : « 00:00 Titre »)
  assets/cast-segments.json                 les screencasts repérés (webcam, incrustation)
  assets/schemas/Dxx.excalidraw             les schémas, vus et validés avant d'être intégrés
  assets/inserts.json                       les extraits à insérer (facultatif)

`check` écrit assets/prep.json : le mode, l'état de chaque livrable, et `ready`. Le storyboard s'écrit quand `ready` est vrai.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODES = ("auto", "webcam", "incrustation")
STATUS_OK = {"ok", "valide", "validé", "fait", "prêt", "pret"}
STATUS_SKIP = {"écarté", "ecarte", "écartée", "abandonné", "abandonne", "non", "n/a"}
MIN_CHAPTER = 10.0            # secondes : YouTube ignore les chapitres plus courts
MATCH_MIN = 0.55              # en dessous, l'alignement d'un titre sur le transcript est « à vérifier »
HEAD_WORDS = 12


def die(msg):
    print("erreur : " + msg, file=sys.stderr)
    sys.exit(1)


def load_module(name, fname):
    spec = importlib.util.spec_from_file_location(name, HERE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# Tableaux Markdown (assets.md, refs.md, figures.md)
# --------------------------------------------------------------------------- #

def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return re.sub(r"[^a-z0-9 ]+", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def read_table(path):
    """Lignes d'un tableau Markdown -> liste de dicts, clés normalisées (minuscules, sans accent)."""
    rows, head = [], None
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if head is None:
            head = [norm(c).replace(" ", "_") for c in cells]
            continue
        if len(cells) < len(head):
            cells += [""] * (len(head) - len(cells))
        rows.append(dict(zip(head, cells)))
    return rows


def status_of(row):
    return norm(row.get("statut", "")).strip()


def is_skipped(row):
    return status_of(row) in {norm(x) for x in STATUS_SKIP}


def is_ok(row):
    return status_of(row) in {norm(x) for x in STATUS_OK}


# --------------------------------------------------------------------------- #
# Gabarits
# --------------------------------------------------------------------------- #

TEMPLATES = {
    "assets/assets.md": """# Assets : fonds d'écran

Un fond par chapitre au moins (variété : `references/visual-language-joriel.md`). Image 1920 × 1080, **plein écran**
(rognée au besoin), rien d'identifiable, pas de logo, pas de texte lisible. Statut : `à faire`, `ok`, `écarté`.

| ID | Description | Fichier | Statut |
|---|---|---|---|
| BG-00 | noir + voile (fond par défaut) | assets/bg/BG-00.jpg | à faire |
""",
    "assets/refs.md": """# Références et assets de référence

Les **références** : une source citée (tweet, page, article). Les **assets de référence** : l'image d'un auteur ou
d'une œuvre cités (portrait, couverture). Une référence se voit **en entier** (bandes transparentes si besoin).
Type : `tweet`, `page`, `video`, `portrait`, `couverture`, `autre`. Statut : `à faire`, `ok`, `écarté`.

| ID | Type | Source | Fichier local | Statut |
|---|---|---|---|---|
""",
    "assets/figures.md": """# Chiffres et sources

Un chiffre affiché dans la vidéo a une **source**. Statut : `ok`, `verify` (à vérifier : pastille en brouillon),
`écarté` (jamais affiché).

| ID | Valeur | Libellé | Source | Statut |
|---|---|---|---|---|
""",
}

CHECKLIST = {
    "auto": ["scénario (SCENARIO.md)", "voix de synthèse (TTS) lue depuis le scénario → assets/voix.wav",
             "transcript (STT) → scripts/transcript-export.py --from-video assets/voix.wav",
             "fonds → assets/assets.md", "références → assets/refs.md", "chiffres → assets/figures.md",
             "chapitres → prepare.py chapters", "schémas (si besoin) → assets/schemas/", "contrôle → prepare.py check"],
    "webcam": ["scénario (SCENARIO.md)", "la prise : le locuteur dicte (concat-mkv.sh, clean-posthoc.py)",
               "screencasts → detect-cast.py → assets/cast-segments.json",
               "transcript → scripts/transcript-export.py --from-video assets/voix-posthoc-vN.wav",
               "fonds → assets/assets.md", "références → assets/refs.md", "chiffres → assets/figures.md",
               "chapitres → prepare.py chapters", "schémas (si besoin) → assets/schemas/", "contrôle → prepare.py check"],
}
CHECKLIST["incrustation"] = CHECKLIST["webcam"]


def cmd_init(a):
    root = Path(a.root).resolve()
    for d in ("assets/bg", "assets/references", "assets/schemas"):
        (root / d).mkdir(parents=True, exist_ok=True)
    made = []
    for rel, text in TEMPLATES.items():
        p = root / rel
        if not p.exists():
            p.write_text(text, encoding="utf-8")
            made.append(rel)
    pj = root / "assets" / "prep.json"
    prep = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
    if prep.get("mode") and prep["mode"] != a.mode:
        die("le projet est déjà en mode %s (un seul mode par projet) : %s" % (prep["mode"], pj))
    prep.update({"mode": a.mode, "created": prep.get("created") or time.strftime("%Y-%m-%d")})
    pj.write_text(json.dumps(prep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("mode %s : dossiers assets/bg, assets/references, assets/schemas ; gabarits écrits : %s" % (a.mode, ", ".join(made) or "(déjà là)"))
    print("\nPréparation, dans l'ordre (le storyboard vient APRÈS) :")
    for i, step in enumerate(CHECKLIST[a.mode], 1):
        print("  %d. %s" % (i, step))
    print("\nDétail : references/preparation.md")


# --------------------------------------------------------------------------- #
# Contrôle
# --------------------------------------------------------------------------- #

class Report:
    def __init__(self):
        self.items = []         # (livrable, état, détail) ; état : ok | à faire | bloquant | n/a

    def add(self, name, state, detail=""):
        self.items.append({"livrable": name, "etat": state, "detail": detail})

    @property
    def blockers(self):
        return [i for i in self.items if i["etat"] in ("bloquant", "à faire")]


def check_voice(root, mode, rep):
    assets = root / "assets"
    if mode == "auto":
        v = sorted(assets.glob("voix*.wav"))
        rep.add("voix", "ok" if v else "bloquant", v[-1].name if v else "assets/voix.wav absent : vocaliser le scénario (TTS)")
        return
    cam = assets / "cam-clean.mkv"
    voices = sorted(assets.glob("voix-posthoc-v*.wav"))
    if not cam.exists():
        rep.add("prise (caméra)", "bloquant", "assets/cam-clean.mkv absent : concat-mkv.sh puis clean-posthoc.py (references/webcam.md)")
    elif not voices:
        rep.add("prise (caméra)", "bloquant", "assets/voix-posthoc-vN.wav absent : relancer clean-posthoc.py")
    else:
        rep.add("prise (caméra)", "ok", "%s + %s" % (cam.name, voices[-1].name))


def check_transcript(root, rep):
    tj, tt = root / "assets" / "transcript.json", root / "assets" / "transcript.txt"
    if not tj.exists():
        rep.add("transcript", "bloquant", "assets/transcript.json absent : python3 scripts/transcript-export.py --from-video <voix>")
        return None
    te = load_module("transcript_export", "transcript-export.py")
    try:
        data = te.normalize(json.loads(tj.read_text(encoding="utf-8")))
    except (ValueError, json.JSONDecodeError) as exc:
        rep.add("transcript", "bloquant", "assets/transcript.json illisible : %s" % exc)
        return None
    if not tt.exists():
        rep.add("transcript", "à faire", "assets/transcript.txt (sans timecode) absent : relancer scripts/transcript-export.py")
    elif tt.read_text(encoding="utf-8").strip() != te.plain_text(data).strip():
        rep.add("transcript", "à faire", "transcript.txt ne correspond plus à transcript.json : relancer scripts/transcript-export.py")
    else:
        rep.add("transcript", "ok", "%d mots, %d segments, %.0f s (JSON avec timecodes + TXT sans)" %
                (len(data["words"]), len(data["segments"]), data["words"][-1]["end"] if data["words"] else 0))
    return data


def check_table(root, rep, rel, name, file_col, require_file=True):
    p = root / rel
    if not p.exists():
        rep.add(name, "bloquant", "%s absent : python3 scripts/prepare.py init" % rel)
        return
    rows = [r for r in read_table(p) if r.get("id")]
    live = [r for r in rows if not is_skipped(r)]
    todo, missing = [], []
    for r in live:
        if not is_ok(r) and status_of(r) != "verify":
            todo.append(r["id"])
        elif file_col and require_file:
            f = (r.get(file_col) or "").strip()
            if not f or not (root / f).exists():
                missing.append("%s (%s)" % (r["id"], f or "fichier non indiqué"))
    if todo:
        rep.add(name, "à faire", "à faire : %s" % ", ".join(todo))
    elif missing:
        rep.add(name, "bloquant", "fichier absent : %s" % ", ".join(missing))
    elif not live:
        rep.add(name, "n/a", "aucune ligne (rien à préparer)")
    else:
        rep.add(name, "ok", "%d ligne(s)" % len(live))


def check_figures(root, rep):
    p = root / "assets" / "figures.md"
    if not p.exists():
        rep.add("chiffres", "bloquant", "assets/figures.md absent : python3 scripts/prepare.py init")
        return
    live = [r for r in read_table(p) if r.get("id") and not is_skipped(r)]
    nosrc = [r["id"] for r in live if not (r.get("source") or "").strip()]
    if nosrc:
        rep.add("chiffres", "bloquant", "sans source : %s (un chiffre affiché a toujours une source)" % ", ".join(nosrc))
    else:
        rep.add("chiffres", "ok" if live else "n/a", "%d chiffre(s) sourcé(s)" % len(live) if live else "aucun chiffre")


def check_chapters(root, rep, duration):
    cj, ct = root / "assets" / "chapters.json", root / "assets" / "chapters.txt"
    if not cj.exists():
        rep.add("chapitres", "à faire", "assets/chapters.json absent : python3 scripts/prepare.py chapters")
        return
    try:
        ch = json.loads(cj.read_text(encoding="utf-8"))
        starts = [float(c["start"]) for c in ch]
        assert all(c.get("title") for c in ch)
    except (ValueError, KeyError, TypeError, AssertionError, json.JSONDecodeError):
        rep.add("chapitres", "bloquant", "assets/chapters.json illisible (liste de {start, title})")
        return
    if starts != sorted(starts) or (starts and starts[0] != 0):
        rep.add("chapitres", "bloquant", "le premier chapitre doit commencer à 0 et les temps croître")
    elif duration and starts and starts[-1] >= duration:
        rep.add("chapitres", "bloquant", "un chapitre commence après la fin du transcript (%.0f s)" % duration)
    elif not ct.exists():
        rep.add("chapitres", "à faire", "assets/chapters.txt (format YouTube) absent : relancer prepare.py chapters")
    else:
        flagged = [c["title"] for c in ch if c.get("verify")]
        rep.add("chapitres", "ok", "%d chapitre(s)%s" % (len(ch), " ; à vérifier : %s" % ", ".join(flagged) if flagged else ""))


def check_screencasts(root, mode, rep):
    if mode == "auto":
        return
    cs = root / "assets" / "cast-segments.json"
    pj = root / "assets" / "prep.json"
    prep = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
    if cs.exists():
        try:
            d = json.loads(cs.read_text(encoding="utf-8"))
            n = len(d.get("segments", d.get("cast", [])) if isinstance(d, dict) else d)
        except (ValueError, json.JSONDecodeError):
            rep.add("screencasts", "bloquant", "assets/cast-segments.json illisible")
            return
        rep.add("screencasts", "ok", "%d séquence(s) Cast repérée(s)" % n)
    elif prep.get("screencasts") == "none":
        rep.add("screencasts", "ok", "aucun screencast (indiqué dans prep.json)")
    else:
        rep.add("screencasts", "à faire", "python3 scripts/detect-cast.py assets/cam-clean.mkv --output assets/cast-segments.json "
                "(ou \"screencasts\": \"none\" dans assets/prep.json s'il n'y en a pas)")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_schemas(root, rep):
    files = sorted((root / "assets" / "schemas").glob("*.excalidraw"))
    if not files:
        rep.add("schémas", "n/a", "aucun schéma")
        return
    bad, notes = [], []
    for f in files:
        stem = f.with_suffix("")
        png, hd, stamp = Path(str(stem) + ".preview.png"), Path(str(stem) + ".handles.md"), Path(str(stem) + ".validated")
        if not hd.exists() or (not png.exists() and not Path(str(stem) + ".preview.html").exists()):
            bad.append("%s : pas d'aperçu (python3 scripts/excalidraw-preview.py %s)" % (f.name, f.relative_to(root)))
        elif hd.stat().st_mtime + 1 < f.stat().st_mtime:
            bad.append("%s : retouché depuis l'aperçu (relancer excalidraw-preview.py)" % f.name)
        elif not stamp.exists():
            bad.append("%s : pas encore validé (le regarder, puis python3 scripts/prepare.py validate-schema %s)" % (f.name, stem.name))
        else:
            try:
                ok = json.loads(stamp.read_text(encoding="utf-8")).get("sha256") == sha256(f)
            except (ValueError, json.JSONDecodeError):
                ok = False
            if ok:
                notes.append(stem.name)
            else:
                bad.append("%s : retouché depuis sa validation (le regarder de nouveau, puis validate-schema)" % f.name)
    if bad:
        rep.add("schémas", "bloquant", " ; ".join(bad))
    else:
        rep.add("schémas", "ok", "validé(s) : %s" % ", ".join(notes))


def check_optional(root, rep):
    ins = root / "assets" / "inserts.json"
    if ins.exists():
        try:
            n = len(json.loads(ins.read_text(encoding="utf-8")).get("inserts", []))
            rep.add("inserts", "ok", "%d extrait(s)" % n)
        except (ValueError, json.JSONDecodeError):
            rep.add("inserts", "bloquant", "assets/inserts.json illisible")


def cmd_check(a):
    root = Path(a.root).resolve()
    pj = root / "assets" / "prep.json"
    prep = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
    mode = a.mode or prep.get("mode")
    if mode not in MODES:
        die("mode inconnu : donner --mode %s, ou lancer `prepare.py init --mode …` d'abord" % "|".join(MODES))
    rep = Report()
    sc = root / a.scenario
    rep.add("scénario", "ok" if sc.exists() and sc.read_text(encoding="utf-8").strip() else "bloquant",
            a.scenario if sc.exists() else "%s absent" % a.scenario)
    check_voice(root, mode, rep)
    data = check_transcript(root, rep)
    check_table(root, rep, "assets/assets.md", "fonds", "fichier")
    check_table(root, rep, "assets/refs.md", "références", "fichier_local")
    check_figures(root, rep)
    check_chapters(root, rep, data["words"][-1]["end"] if data and data["words"] else None)
    check_screencasts(root, mode, rep)
    check_schemas(root, rep)
    check_optional(root, rep)

    width = max(len(i["livrable"]) for i in rep.items)
    print("Préparation (mode %s)" % mode)
    for i in rep.items:
        mark = {"ok": "ok      ", "n/a": "n/a     ", "à faire": "à faire ", "bloquant": "BLOQUANT"}[i["etat"]]
        print("  %-*s  %s  %s" % (width, i["livrable"], mark, i["detail"]))
    ready = not rep.blockers
    prep.update({"mode": mode, "ready": ready, "checked": time.strftime("%Y-%m-%d %H:%M"),
                 "etat": {i["livrable"]: i["etat"] for i in rep.items}})
    pj.parent.mkdir(parents=True, exist_ok=True)
    pj.write_text(json.dumps(prep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n" + ("prêt : le storyboard peut s'écrire (assets/prep.json : ready)" if ready else
                  "pas prêt : %d livrable(s) à finir avant d'écrire le storyboard" % len(rep.blockers)))
    return 0 if ready else 1


# --------------------------------------------------------------------------- #
# Chapitres : les titres du scénario, alignés sur le transcript
# --------------------------------------------------------------------------- #

def sections(text):
    """[(titre, corps)] : un chapitre par titre `##` du scénario ; sans `##`, par titre `#` après le premier."""
    lines = text.splitlines()
    heads = [(i, re.match(r"^(#{1,3})\s+(.*?)\s*#*\s*$", l)) for i, l in enumerate(lines)]
    heads = [(i, len(m.group(1)), m.group(2)) for i, m in heads if m]
    level = 2 if any(h[1] == 2 for h in heads) else (1 if len([h for h in heads if h[1] == 1]) > 1 else 3)
    cut = [h for h in heads if h[1] == level]
    out = []
    for k, (i, _, title) in enumerate(cut):
        end = cut[k + 1][0] if k + 1 < len(cut) else len(lines)
        body = " ".join(l for l in lines[i + 1:end] if l.strip() and not l.lstrip().startswith("#"))
        out.append((title, body))
    return out


def tokens(text):
    return [t for t in norm(re.sub(r"[`*_\[\]()>#|-]", " ", text)).split() if t]


def align(sections_, words):
    """Pour chaque section : (indice du mot, score). Cherche, après le chapitre précédent, la fenêtre du transcript
    qui ressemble le plus aux premiers mots de la section."""
    tw = [norm(w["word"]).replace(" ", "") for w in words]
    res, pos = [], 0
    for title, body in sections_:
        head = tokens(body)[:HEAD_WORDS] or tokens(title)
        if not head or not tw:
            res.append((None, 0.0))
            continue
        target = " ".join(head)
        best, best_i = 0.0, None
        n = len(head)
        for i in range(pos, max(pos + 1, len(tw) - n + 1)):
            win = " ".join(tw[i:i + n])
            # test rapide : au moins un mot en commun avant de calculer le rapport
            if not set(tw[i:i + n]) & set(head):
                continue
            r = SequenceMatcher(None, target, win).ratio()
            if r > best:
                best, best_i = r, i
        res.append((best_i, best))
        if best_i is not None and best >= MATCH_MIN:
            pos = best_i + 1
    return res


def fmt(t):
    t = int(round(t))
    h, m, s = t // 3600, (t % 3600) // 60, t % 60
    return "%d:%02d:%02d" % (h, m, s) if h else "%02d:%02d" % (m, s)


def cmd_chapters(a):
    root = Path(a.root).resolve()
    sc, tj = root / a.scenario, root / "assets" / "transcript.json"
    if not sc.exists():
        die("%s absent" % a.scenario)
    if not tj.exists():
        die("assets/transcript.json absent : le transcript d'abord (scripts/transcript-export.py)")
    te = load_module("transcript_export", "transcript-export.py")
    data = te.normalize(json.loads(tj.read_text(encoding="utf-8")))
    secs = sections(sc.read_text(encoding="utf-8"))
    if len(secs) < 2:
        die("moins de deux titres dans %s : un chapitre par titre `##` (YouTube en demande au moins trois)" % a.scenario)
    total = data["words"][-1]["end"] if data["words"] else 0.0
    found = align(secs, data["words"])
    chapters, warns = [], []
    for k, ((title, _), (idx, score)) in enumerate(zip(secs, found)):
        if idx is None or score < MATCH_MIN:
            est = total * k / len(secs)
            warns.append("« %s » : alignement incertain (score %.2f), temps estimé %s" % (title, score, fmt(est)))
            chapters.append({"start": round(est, 1), "title": title, "verify": True, "score": round(score, 2)})
        else:
            chapters.append({"start": round(data["words"][idx]["start"], 1), "title": title, "score": round(score, 2)})
    chapters[0]["start"] = 0.0
    chapters.sort(key=lambda c: c["start"])
    kept = [chapters[0]]
    for c in chapters[1:]:
        if c["start"] - kept[-1]["start"] < MIN_CHAPTER:
            warns.append("« %s » (%s) est à moins de %.0f s du chapitre précédent : fusionné (YouTube ignore les chapitres trop courts)"
                         % (c["title"], fmt(c["start"]), MIN_CHAPTER))
            continue
        kept.append(c)
    if len(kept) < 3:
        warns.append("%d chapitre(s) seulement : YouTube en demande au moins trois" % len(kept))
    (root / "assets").mkdir(exist_ok=True)
    (root / "assets" / "chapters.json").write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "assets" / "chapters.txt").write_text("\n".join("%s %s" % (fmt(c["start"]), c["title"]) for c in kept) + "\n", encoding="utf-8")
    print("\n".join("%s  %s%s" % (fmt(c["start"]), c["title"], "   ← à vérifier" if c.get("verify") else "") for c in kept))
    for w in warns:
        print("avertissement : " + w)
    print("écrit : assets/chapters.json, assets/chapters.txt (format YouTube)")


# --------------------------------------------------------------------------- #
# Validation d'un schéma
# --------------------------------------------------------------------------- #

def cmd_validate(a):
    root = Path(a.root).resolve()
    f = Path(a.schema)
    if not f.suffix:
        f = Path("assets/schemas") / (a.schema + ".excalidraw")
    f = f if f.is_absolute() else root / f
    if not f.exists():
        die("schéma absent : %s" % f)
    sys.path.insert(0, str(HERE))
    import excalidraw_anim
    try:
        S = excalidraw_anim.load_schema(f, f.stem)
    except Exception as exc:                       # noqa: BLE001
        die("%s n'est pas un schéma utilisable : %s" % (f.name, exc))
    stem = f.with_suffix("")
    hd = Path(str(stem) + ".handles.md")
    if not hd.exists() or hd.stat().st_mtime + 1 < f.stat().st_mtime:
        die("pas d'aperçu à jour : python3 scripts/excalidraw-preview.py %s, le regarder, puis valider" % f)
    Path(str(stem) + ".validated").write_text(json.dumps({"sha256": sha256(f), "at": time.strftime("%Y-%m-%d %H:%M"),
                                                          "elements": len(S.nodes), "links": len(S.edges)}) + "\n", encoding="utf-8")
    print("validé : %s (%d éléments, %d liens). Retouché ensuite, il devra être validé de nouveau." % (f.name, len(S.nodes), len(S.edges)))
    if S.warnings:
        print("avertissements encore présents :")
        for w in S.warnings:
            print("  - " + w)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Préparation du storyboard : livrables, contrôle, chapitres.")
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("--mode", required=True, choices=MODES)
    p = sub.add_parser("check")
    p.add_argument("--mode", choices=MODES, default=None)
    p.add_argument("--scenario", default="SCENARIO.md")
    p = sub.add_parser("chapters")
    p.add_argument("--scenario", default="SCENARIO.md")
    p = sub.add_parser("validate-schema")
    p.add_argument("schema", help="Dxx ou chemin du fichier .excalidraw")
    a = ap.parse_args(argv)
    if a.cmd == "init":
        cmd_init(a)
    elif a.cmd == "check":
        sys.exit(cmd_check(a))
    elif a.cmd == "chapters":
        cmd_chapters(a)
    else:
        cmd_validate(a)


if __name__ == "__main__":
    main()
