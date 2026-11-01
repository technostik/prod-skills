#!/usr/bin/env python3
"""Post-rendu des inserts : extraits vidéo qui REMPLACENT l'image et le son du master.

Entrée  : renders/full.mp4 (master), assets/inserts.json (manifeste), le storyboard minuté.
Sortie  : renders/final.mp4 (un seul graphe ffmpeg, master encodé une fois).

Les coupes sont exprimées sur la timeline D'ORIGINE du master. Un insert s'ajoute à
l'endroit de la coupe (le master n'est pas raccourci) : rien ne se décale entre deux passes.
Chaque insert est téléchargé (yt-dlp) ou lu en local, découpé, puis légèrement transformé
(hauteur du son +5 % à durée constante, rotation de 1°, avec zoom pour masquer les coins).

Usage (depuis le dossier du projet) :
  python3 $SKILL_DIR/scripts/post-render.py --plan       # coupes résolues, sans rien télécharger
  python3 $SKILL_DIR/scripts/post-render.py --preview    # un clip court autour de chaque coupe
  python3 $SKILL_DIR/scripts/post-render.py              # téléchargement + rendu final
  options : --manifest FILE  --root DIR  --force  --dry-run  --fetch-only

Format du manifeste : references/inserts.md.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

STEP_RE = re.compile(r"^\s*-\s*`?(I\d+\.\d+#\d+)`?\s+t=([\d.]+)\s*\(([\d.]+)s\)\s*(?:\[[^\]]*\])?\s*(.*)$")
VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
FPS = 30
DEFAULTS = {"pitch": 1.05, "rotate_deg": 1.0}


def die(msg):
    print("erreur : " + msg, file=sys.stderr)
    sys.exit(1)


def tc(v):
    """'1:23', '01:02:03', '83.5' ou nombre -> secondes (None reste None)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    parts = s.split(":")
    if not 2 <= len(parts) <= 3 or not all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
        die("timecode illisible : %r (attendu 83, 1:23 ou 0:01:23)" % (v,))
    x = 0.0
    for p in parts:
        x = x * 60 + float(p)
    return x


def fmt(t):
    t = max(t, 0.0)
    return "%d:%05.2f" % (int(t // 60), t % 60)


def q(cmd):
    return " ".join(shlex.quote(str(c)) for c in cmd)


class Ctx:
    def __init__(self, dry):
        self.dry = dry

    def run(self, cmd, what):
        print("$ " + q(cmd), file=sys.stderr)
        if self.dry:
            return
        if subprocess.run(cmd).returncode != 0:
            die("%s a échoué (commande ci-dessus)" % what)


def probe(path):
    """(durée, a_audio, largeur, hauteur) via ffprobe."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
         "-of", "json", str(path)], capture_output=True, text=True)
    if out.returncode != 0:
        die("ffprobe ne lit pas %s" % path)
    j = json.loads(out.stdout)
    dur = float(j.get("format", {}).get("duration") or 0)
    st = j.get("streams", [])
    has_a = any(s.get("codec_type") == "audio" for s in st)
    v = next((s for s in st if s.get("codec_type") == "video"), {})
    return dur, has_a, int(v.get("width") or 0), int(v.get("height") or 0)


# ---------------------------------------------------------------- manifeste et ancrages
def load_manifest(path):
    p = Path(path)
    if not p.exists():
        die("manifeste absent : %s (voir references/inserts.md)" % p)
    m = json.loads(p.read_text(encoding="utf-8"))
    m.setdefault("master", "renders/full.mp4")
    m.setdefault("output", "renders/final.mp4")
    m.setdefault("scenario", "assets/scenario-hyperframes.md")
    m["transform"] = {**DEFAULTS, **m.get("transform", {})}
    ids = [i.get("id") for i in m.get("inserts", [])]
    if not ids:
        die("aucun insert dans %s" % p)
    if len(set(ids)) != len(ids) or not all(ids):
        die("chaque insert a besoin d'un `id` unique")
    for i in m["inserts"]:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", i["id"]):
            die("id d'insert invalide : %r (lettres, chiffres, . _ -)" % i["id"])
        if not i.get("source"):
            die("insert %s : `source` manquante (URL ou chemin local)" % i["id"])
        if sum(k in i for k in ("after", "before", "at")) != 1:
            die("insert %s : exactement un ancrage parmi after / before / at" % i["id"])
    return m


def load_steps(path):
    p = Path(path)
    if not p.exists():
        return {}
    steps = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        m = STEP_RE.match(line)
        if m:
            steps[m.group(1)] = (float(m.group(2)), float(m.group(3)), m.group(4).strip())
    return steps


def resolve(ins, steps):
    """Retourne (T sur la timeline du master, note)."""
    if "at" in ins:
        t = tc(ins["at"])
        for sid, (st, d, _) in steps.items():
            if st + 0.05 < t < st + d - 0.05:
                return t, "au milieu de l'étape %s : préférer after/before" % sid
        return t, ""
    key = "after" if "after" in ins else "before"
    a = ins[key]
    if re.fullmatch(r"I\d+", a):                     # une scène entière
        sc = [(s, v) for s, v in steps.items() if s.startswith(a + ".")]
        if not sc:
            die("insert %s : scène %s introuvable dans le storyboard" % (ins["id"], a))
        sc.sort(key=lambda x: x[1][0])
        s, (st, d, _) = sc[-1] if key == "after" else sc[0]
        return (st + d if key == "after" else st), ""
    if a not in steps:
        near = [s for s in steps if s.split("#")[0] == a.split("#")[0]][:6] or list(steps)[:6]
        die("insert %s : étape %s introuvable dans le storyboard (proches : %s)" % (ins["id"], a, ", ".join(near) or "aucune"))
    st, d, _ = steps[a]
    return (st + d if key == "after" else st), ""


def around(t, steps):
    """Texte des étapes qui finissent et commencent à la coupe (pour valider sans réécouter)."""
    prev = [tx for st, d, tx in steps.values() if abs(st + d - t) < 0.06 and tx]
    nxt = [tx for st, d, tx in steps.values() if abs(st - t) < 0.06 and tx]
    if not prev and not nxt:
        return ""
    return "       …%s  ⟂  %s…" % (prev[0] if prev else "(début)", nxt[0] if nxt else "(fin)")


# ---------------------------------------------------------------- téléchargement
def is_url(s):
    return re.match(r"https?://", s) is not None


def fetch(ins, ctx, force):
    """Retourne (fichier brut, déjà découpé ?)."""
    raw_dir = Path("assets/inserts/raw")
    src, a, b = ins["source"], tc(ins.get("start")), tc(ins.get("end"))
    if not is_url(src):
        p = Path(src)
        if not p.exists():
            die("insert %s : fichier local absent : %s" % (ins["id"], p))
        return p, False
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta_p = raw_dir / (ins["id"] + ".meta.json")
    want = {"source": src, "start": a, "end": b}
    if meta_p.exists() and not force:
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        f = raw_dir / meta.get("file", "")
        if meta.get("want") == want and f.exists():
            print("déjà téléchargé : %s" % f, file=sys.stderr)
            return f, meta["trimmed"]
    if shutil.which("yt-dlp") is None and not ctx.dry:
        die("yt-dlp introuvable (pip install -U yt-dlp)")
    base = ["yt-dlp", "--no-playlist", "--no-progress", "-f", "bv*[height<=1080]+ba/b[height<=1080]/b",
            "--merge-output-format", "mp4", "-o", str(raw_dir / (ins["id"] + ".%(ext)s"))]
    for old in raw_dir.glob(ins["id"] + ".*"):
        if old.name != meta_p.name and not ctx.dry:
            old.unlink()
    trimmed = False
    if a is not None and b is not None:
        cmd = base + ["--download-sections", "*%s-%s" % (a, b), "--force-keyframes-at-cuts", src]
        print("$ " + q(cmd), file=sys.stderr)
        ok = ctx.dry or subprocess.run(cmd).returncode == 0
        trimmed = ok
        if not ok:
            print("découpe à la source impossible, repli : téléchargement entier puis découpe locale", file=sys.stderr)
    if not trimmed:
        ctx.run(base + [src], "le téléchargement de %s" % ins["id"])
    if ctx.dry:
        return raw_dir / (ins["id"] + ".mp4"), trimmed
    found = sorted((f for f in raw_dir.glob(ins["id"] + ".*") if f.suffix.lower() in VIDEO_EXT),
                   key=lambda f: f.stat().st_mtime)
    if not found:
        die("insert %s : yt-dlp n'a produit aucun fichier vidéo" % ins["id"])
    meta_p.write_text(json.dumps({"want": want, "file": found[-1].name, "trimmed": trimmed}), encoding="utf-8")
    return found[-1], trimmed


# ---------------------------------------------------------------- transformation
def vf_fit(w, h):
    return ("scale=%d:%d:force_original_aspect_ratio=decrease,"
            "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1" % (w, h, w, h))


def vf_insert(w, h, deg):
    vf = vf_fit(w, h)
    if abs(deg) > 1e-6:
        r = math.radians(abs(deg))
        z = math.cos(r) + (max(w / h, h / w)) * math.sin(r) + 0.01     # zoom qui masque les coins
        zw, zh = int(math.ceil(w * z / 2) * 2), int(math.ceil(h * z / 2) * 2)
        vf += ",scale=%d:%d,rotate=a=%.6f:ow=iw:oh=ih:c=black,crop=%d:%d" % (zw, zh, math.radians(deg), w, h)
    return vf + ",setsar=1,fps=%d,format=yuv420p" % FPS


def af_insert(pitch):
    af = "aresample=48000"
    if abs(pitch - 1) > 1e-6:
        af += ",asetrate=%d,aresample=48000,atempo=%.6f" % (round(48000 * pitch), 1 / pitch)
    return af + ",aformat=sample_fmts=fltp:channel_layouts=stereo"


def prepare(ins, raw, trimmed, tr, size, ctx, force):
    """Écrit assets/inserts/<id>.mp4 : découpé, 1920x1080 30 i/s AAC 48 kHz, pitch et rotation."""
    pitch = float(ins.get("pitch", tr["pitch"]))
    deg = float(ins.get("rotate_deg", tr["rotate_deg"]))
    a, b = tc(ins.get("start")), tc(ins.get("end"))
    out = Path("assets/inserts") / (ins["id"] + ".mp4")
    key = hashlib.sha1(json.dumps([str(raw), a, b, trimmed, pitch, deg, size], sort_keys=True).encode()).hexdigest()
    key_p = out.with_suffix(".json")
    if out.exists() and key_p.exists() and key_p.read_text() == key and not force and not ctx.dry:
        print("déjà préparé : %s" % out, file=sys.stderr)
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    has_a = True if ctx.dry else probe(raw)[1]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if not trimmed and a is not None:
        cmd += ["-ss", "%.3f" % a]
        if b is not None:
            cmd += ["-t", "%.3f" % (b - a)]
    cmd += ["-i", str(raw)]
    if not has_a:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    cmd += ["-map", "0:v:0", "-map", "0:a:0" if has_a else "1:a:0"]
    cmd += ["-vf", vf_insert(size[0], size[1], deg), "-af", af_insert(pitch)]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    if not has_a:
        cmd += ["-shortest"]
    cmd += [str(out)]
    ctx.run(cmd, "la préparation de %s" % ins["id"])
    if not ctx.dry:
        key_p.write_text(key)
    return out


# ---------------------------------------------------------------- assemblage
AF_NORM = "aresample=48000:async=1:first_pts=0,aformat=sample_fmts=fltp:channel_layouts=stereo"


def graph(cuts, size, outro, mdur):
    """cuts : [(T, indice d'entrée de l'insert)], triés. Entrée 0 = master. outro : indice d'entrée ou None."""
    w, h = size
    vmain = "fps=%d,setsar=1,format=yuv420p" % FPS
    segs, prev = [], 0.0
    for t, _ in cuts:
        segs.append((prev, t))
        prev = t
    segs.append((prev, None))
    # segments non vides du master ; une coupe à 0 s ou deux inserts au même point n'en créent pas
    keep = [i for i, (a, b) in enumerate(segs) if (b if b is not None else mdur) - a >= 0.04]
    n = len(keep)
    parts = ["[0:v]split=%d%s;[0:a]asplit=%d%s;" % (
        n, "".join("[s%d]" % i for i in keep), n, "".join("[b%d]" % i for i in keep))]
    for i in keep:
        a, b = segs[i]
        rng = "start=%.3f" % a + (":end=%.3f" % b if b is not None else "")
        parts.append("[s%d]trim=%s,setpts=PTS-STARTPTS,%s[v%d];" % (i, rng, vmain, i))
        parts.append("[b%d]atrim=%s,asetpts=PTS-STARTPTS,%s[a%d];" % (i, rng, AF_NORM, i))
    order = []
    for i in range(len(segs)):
        if i in keep:
            order.append(("m", i))
        if i < len(cuts):
            order.append(("i", cuts[i][1]))
    if outro is not None:
        order.append(("o", outro))
    labels = []
    for kind, idx in order:
        if kind == "m":
            labels += ["[v%d]" % idx, "[a%d]" % idx]
            continue
        if kind == "o":     # signature : ajustée en 1920x1080, sans transformation
            vf = "setpts=PTS-STARTPTS,%s,fps=%d,format=yuv420p" % (vf_fit(w, h), FPS)
        else:               # insert déjà préparé (taille, fps, transformation)
            vf = "setpts=PTS-STARTPTS,setsar=1,fps=%d,format=yuv420p" % FPS
        parts.append("[%d:v]%s[vx%d];" % (idx, vf, idx))
        parts.append("[%d:a]asetpts=PTS-STARTPTS,%s[ax%d];" % (idx, AF_NORM, idx))
        labels += ["[vx%d]" % idx, "[ax%d]" % idx]
    parts.append("%sconcat=n=%d:v=1:a=1[v][a]" % ("".join(labels), len(order)))
    return "".join(parts)


def render(master, mdur, cuts_sorted, prepared, outro, size, out, ctx):
    inputs = ["-i", str(master)]
    cuts = []
    for k, (t, ins) in enumerate(cuts_sorted):
        inputs += ["-i", str(prepared[ins["id"]])]
        cuts.append((t, k + 1))
    outro_idx = None
    if outro:
        inputs += ["-i", str(outro)]
        outro_idx = len(cuts) + 1
    tmp = Path(str(out) + ".part.mp4")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + inputs + [
        "-filter_complex", graph(cuts, size, outro_idx, mdur if mdur is not None else 1e9), "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(tmp)]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    ctx.run(cmd, "le rendu final")
    if not ctx.dry:
        os.replace(tmp, out)


def preview(master, t, ins_file, k, size, ctx, before=4.0, after=4.0, ins_len=3.0):
    """Clip court : 4 s de master, 3 s de l'insert, 4 s de master."""
    out = Path("renders") / ("preview-%s.mp4" % k)
    out.parent.mkdir(parents=True, exist_ok=True)
    a = max(t - before, 0.0)
    w, h = size[0] // 2, size[1] // 2
    norm = "scale=%d:%d,setsar=1,fps=%d,format=yuv420p" % (w, h, FPS)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", "%.3f" % a, "-t", "%.3f" % (t - a), "-i", str(master),
           "-t", "%.3f" % ins_len, "-i", str(ins_file),
           "-ss", "%.3f" % t, "-t", "%.3f" % after, "-i", str(master),
           "-filter_complex",
           "[0:v]%s[v0];[0:a]%s[a0];[1:v]%s[v1];[1:a]%s[a1];[2:v]%s[v2];[2:a]%s[a2];"
           "[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]" % (norm, AF_NORM, norm, AF_NORM, norm, AF_NORM),
           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
           "-c:a", "aac", "-b:a", "128k", str(out)]
    ctx.run(cmd, "l'aperçu de %s" % k)
    return out


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description="Post-rendu : inserts qui remplacent image et son du master.")
    ap.add_argument("--manifest", default="assets/inserts.json")
    ap.add_argument("--root", default=".")
    ap.add_argument("--plan", action="store_true", help="affiche les coupes résolues et s'arrête")
    ap.add_argument("--preview", action="store_true", help="un clip court autour de chaque coupe, pas de rendu final")
    ap.add_argument("--fetch-only", action="store_true", help="télécharge et prépare les inserts, sans rendu")
    ap.add_argument("--force", action="store_true", help="refait téléchargements et préparations")
    ap.add_argument("--dry-run", action="store_true", help="affiche les commandes sans les exécuter")
    args = ap.parse_args()

    os.chdir(args.root)
    man = load_manifest(args.manifest)
    steps = load_steps(man["scenario"])
    needs_steps = any(("after" in i or "before" in i) for i in man["inserts"])
    if needs_steps and not steps:
        die("storyboard minuté absent ou sans étapes : %s" % man["scenario"])

    master = Path(man["master"])
    mdur, size = None, (1920, 1080)
    if master.exists():
        mdur, _, mw, mh = probe(master)
        size = (mw or 1920, mh or 1080)
    elif not (args.plan or args.dry_run):
        die("master absent : %s (rendre la composition d'abord)" % master)

    cuts = []
    for ins in man["inserts"]:
        t, note = resolve(ins, steps)
        if mdur is not None and not 0 < t <= mdur:
            die("insert %s : coupe à %.2f s hors du master (0 à %.2f s)" % (ins["id"], t, mdur))
        cuts.append((t, ins, note))
    cuts.sort(key=lambda c: c[0])          # tri stable : même point = ordre du manifeste

    ctx = Ctx(args.dry_run)
    ilen = {}
    for t, ins, _ in cuts:
        a, b = tc(ins.get("start")), tc(ins.get("end"))
        ilen[ins["id"]] = (b - a) if (a is not None and b is not None) else None

    # --- plan
    print("\nCoupes sur la timeline du master%s :" % (" (%.1f s)" % mdur if mdur else ""))
    shift = 0.0
    for t, ins, note in cuts:
        d = ilen[ins["id"]]
        print("  %-18s coupe à %8s (final %8s)  insert %s  %s%s" % (
            ins["id"], fmt(t), fmt(t + shift), ("%.1f s" % d) if d else "durée ?",
            ins.get("why", ""), ("  ⚠ " + note) if note else ""))
        ctxt = around(t, steps)
        if ctxt:
            print(ctxt)
        shift += d or 0.0
    if mdur:
        print("Durée finale estimée (hors signature) : %s" % fmt(mdur + shift))
    if args.plan:
        return

    # --- téléchargement et préparation
    tr = man["transform"]
    prepared, lens = {}, {}
    for t, ins, _ in cuts:
        raw, trimmed = fetch(ins, ctx, args.force)
        prepared[ins["id"]] = prepare(ins, raw, trimmed, tr, size, ctx, args.force)
        lens[ins["id"]] = None if ctx.dry else probe(prepared[ins["id"]])[0]
    if args.fetch_only:
        return

    # --- aperçus
    if args.preview:
        for t, ins, _ in cuts:
            f = preview(master, t, prepared[ins["id"]], ins["id"], size, ctx)
            print("aperçu : %s" % f)
        return

    # --- rendu final
    outro = man.get("outro")
    if outro and not Path(outro).exists() and not ctx.dry:
        die("outro absent : %s" % outro)
    out = Path(man["output"])
    render(master, mdur, [(t, ins) for t, ins, _ in cuts], prepared, outro, size, out, ctx)

    if not ctx.dry:
        cred = ["# Extraits utilisés", ""]
        for t, ins, _ in cuts:
            cred.append("- %s : %s (%s → %s)" % (ins["id"], ins["source"], ins.get("start", "début"), ins.get("end", "fin")))
        Path("renders").mkdir(exist_ok=True)
        Path("renders/inserts-credits.md").write_text("\n".join(cred) + "\n", encoding="utf-8")
        fdur = probe(out)[0]
        exp = mdur + sum(lens.values()) + (probe(outro)[0] if outro else 0)
        print("écrit : %s (%.2f s ; attendu %.2f s)" % (out, fdur, exp))
        if abs(fdur - exp) > 0.5:
            print("⚠ écart de durée supérieur à 0,5 s : vérifier l'aperçu", file=sys.stderr)


if __name__ == "__main__":
    main()
