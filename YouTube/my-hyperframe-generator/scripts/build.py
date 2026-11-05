#!/usr/bin/env python3
"""Construit la composition HyperFrames depuis assets/storyboard.md.

Le storyboard est la source unique : scènes, étapes, registres de chiffres et de
références. Ce script ne décide rien d'éditorial ; il applique le `kind` écrit
par le LLM et produit :

    data/figures.json  data/refs.json  data/steps.json
    data/design.json   data/scenes.json
    index.html         compositions/iNN.html

Usage :
    python3 scripts/build.py [--root .] [--storyboard assets/storyboard.md]
        [--transcript transcript.json] [--audio assets/voix.wav]
        [--camera assets/cam-clean.mkv] [--slug mon-film]

Sans transcript, les durées sont celles du storyboard (estimées). Avec un
transcript, chaque `cue` est recalé sur les mots de la voix : la durée des
étapes vient de l'audio, jamais l'inverse.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import unicodedata
import wave
from pathlib import Path

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #

STEP_ID_RE = re.compile(r"^[A-Za-z0-9]+\.[0-9]+#[0-9]+$")
SCENE_HEAD_RE = re.compile(r"^###\s+([A-Z][A-Za-z0-9]*)\s*[—–-]\s*(.+?)\s*$")
BULLET_RE = re.compile(r"^(\s*)-\s*(.*)$")
KV_RE = re.compile(r"^([A-Za-zÀ-ÿ0-9_][A-Za-zÀ-ÿ0-9 _\-]*?)\s*:\s*(.*)$")
NUM_RE = re.compile(r"([+\-−]?)\s*(\d[\d\s\u00a0\u202f]*(?:[.,]\d+)?)\s*(.*)$")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")

KICK = {"bilan": "Le bilan", "analyse": "L'analyse", "conclusion": "Conclusion"}

from render_primitive import (ALIASES, CSS_EXT, ICONS, Primitives,
                              as_blocks, esc, num_parts, to_float)

JS_TEMPLATE = r"""
// Mouvements des primitives. Délais relatifs au début de l'étape.
var CAM = {
  pip:  { left: 1460, top: 821, width: 422, height: 238, opacity: 1 },
  full: { left: 480, top: 270, width: 960, height: 540, opacity: 1 },
  off:  { left: 1460, top: 821, width: 422, height: 238, opacity: 0 }
};
function applyCam(tl, frame, mode, t, stepSel) {
  var g = CAM[mode] || CAM.off;
  if (t === 0) tl.set(frame, g, 0);
  else tl.to(frame, Object.assign({ duration: 0.55, ease: "power3.inOut" }, g), t);
  var blur = mode === "full" ? "blur(8px)" : "blur(0px)";
  tl.to("#fond", { filter: blur, duration: 0.4, ease: "power2.inOut" }, t);
  tl.to(stepSel, { filter: blur, duration: 0.4, ease: "power2.inOut" }, t);
}
const tl = gsap.timeline({ paused: true });
if (document.querySelector("#fond-img")) tl.fromTo("#fond-img", { scale: 1 }, { scale: 1.05, duration: __DUR__, ease: "none" }, 0);
function _fmt(n, dec) {
  var s = dec ? Number(n).toFixed(dec) : Math.round(n).toString();
  var p = s.split(".");
  p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return p.join(",");
}
document.querySelectorAll(".step,.step-punch").forEach(function (step) {
  const t = parseFloat(step.getAttribute("data-start"));
  const dur = parseFloat(step.getAttribute("data-duration"));
  const sel = "#" + step.id;
  const has = function (q) { return step.querySelector(q) !== null; };
  if (document.querySelector("#__CAM__")) applyCam(tl, "#__CAM__", step.getAttribute("data-cam") || "off", t, sel);
  tl.addLabel(step.getAttribute("data-step"), t);

  // entrée de l'étape : le bloc glisse et apparaît
  const inEl = step.querySelector(".in");
  if (inEl) tl.fromTo("#" + inEl.id, { opacity: 0, y: 34 }, { opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }, t);
  var _num = step.querySelector(".dbig") || step.querySelector(".dkw");
  if (_num && inEl) tl.fromTo("#" + inEl.id, { scale: 0.92 }, { scale: 1, duration: 0.7, ease: "back.out(1.5)" }, t + 0.05);
  if (inEl && step.querySelectorAll(".in > .dline").length > 1) tl.fromTo(sel + " .in > .dline", { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out", stagger: 0.12 }, t + 0.1);
  if (has(".kicker")) tl.fromTo(sel + " .kicker", { opacity: 0, x: -26 }, { opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }, t);
  if (has(".stitle")) tl.fromTo(sel + " .stitle", { opacity: 0, y: -20 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, t + 0.1);

  // versus
  if (has(".versus")) {
    tl.fromTo(sel + " .vsep", { scaleY: 0 }, { scaleY: 1, duration: 0.5, ease: "power2.out" }, t + 0.15);
    tl.fromTo(sel + " .vcol.left", { scale: 1, x: 0 }, { scale: 0.82, x: -24, duration: 0.7, ease: "power2.out" }, t + 0.3);
    tl.fromTo(sel + " .vcol.right", { scale: 1 }, { scale: 1.16, duration: 0.8, ease: "back.out(1.4)" }, t + 0.3);
  }
  // diverge
  if (has(".diverge")) {
    tl.fromTo(sel + " .branch.up .darr-big", { opacity: 0, x: -36, y: 36 }, { opacity: 1, x: 0, y: 0, duration: 0.45, ease: "power3.out" }, t + 0.35);
    tl.fromTo(sel + " .branch.down .darr-big", { opacity: 0, x: -36, y: -36 }, { opacity: 1, x: 0, y: 0, duration: 0.45, ease: "power3.out" }, t + 0.85);
    tl.fromTo(sel + " .branch.up .dsub", { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }, t + 0.6);
    tl.fromTo(sel + " .branch.down .dsub", { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }, t + 1.1);
    tl.fromTo(sel + " .branch.up .darr-big", { scale: 1 }, { scale: 1.35, duration: 0.25, yoyo: true, repeat: 1, ease: "power2.inOut" }, t + 0.85);
    tl.fromTo(sel + " .branch.down .darr-big", { scale: 1 }, { scale: 1.35, duration: 0.25, yoyo: true, repeat: 1, ease: "power2.inOut" }, t + 1.35);
  }
  // strike
  if (has(".sline1")) {
    tl.fromTo(sel + " .sline1", { scaleX: 0 }, { scaleX: 1, duration: 0.4, ease: "power2.inOut", transformOrigin: "left center" }, t + 0.35);
    tl.fromTo(sel + " .sline2", { scaleX: 0 }, { scaleX: 1, duration: 0.4, ease: "power2.inOut", transformOrigin: "right center" }, t + 0.7);
  }
  // count
  step.querySelectorAll(".ctr").forEach(function (el) {
    var obj = { val: 0 }, target = parseFloat(el.getAttribute("data-target"));
    var dec = parseInt(el.getAttribute("data-dec") || "0", 10);
    if (!isFinite(target)) return;
    tl.to(obj, { val: target, duration: 1.1, ease: "power3.out", onUpdate: function () { el.textContent = _fmt(obj.val, dec); } }, t + 0.15);
  });
  if (has(".dbig") && has(".dsub")) tl.fromTo(sel + " .dsub", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }, t + 0.9);
  // enumerate : le nouvel item entre, les précédents s'estompent
  if (has(".it.new")) {
    tl.fromTo(sel + " .it.new", { opacity: 0, y: 28 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, t + 0.1);
    if (has(".it:not(.new)")) tl.fromTo(sel + " .it:not(.new)", { opacity: 1 }, { opacity: 0.55, duration: 0.5, ease: "power2.out" }, t + 0.1);
  }
  // cols2
  if (has(".cols2")) tl.fromTo(sel + " .cols2 .dline", { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.45, ease: "power3.out", stagger: 0.1 }, t + 0.15);
  // stamp
  if (has(".stamp")) {
    tl.fromTo(sel + " .stamp", { scale: 2.4, opacity: 0, rotation: -14 }, { scale: 0.94, opacity: 1, rotation: -3, duration: 0.24, ease: "power4.in", stagger: 0.24 }, t + 0.35);
    tl.to(sel + " .stamp", { scale: 1, duration: 0.2, ease: "back.out(3)", stagger: 0.24 }, t + 0.59);
  }
  // chip
  if (has(".chip")) tl.fromTo(sel + " .chip", { scale: 0, y: 10 }, { scale: 1, y: 0, duration: 0.45, ease: "back.out(2.4)", stagger: 0.14 }, t + 0.25);
  // icon / check / cross
  if (has(".dico")) {
    tl.fromTo(sel + " .dico", { scale: 0 }, { scale: 1, duration: 0.45, ease: "back.out(2.2)", stagger: 0.14 }, t + 0.2);
    tl.fromTo(sel + " .dico path", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.5, ease: "power2.out", stagger: 0.07 }, t + 0.45);
  }
  // arrow
  if (has(".darr")) tl.fromTo(sel + " .darr", { opacity: 0, x: -34, scale: 0.7 }, { opacity: 1, x: 0, scale: 1, duration: 0.5, ease: "back.out(2)", stagger: 0.28 }, t + 0.3);
  // punch
  if (step.classList.contains("step-punch")) {
    tl.fromTo(sel + " .w", { opacity: 0, y: 46, scale: 0.92 }, { opacity: 1, y: 0, scale: 1, duration: 0.45, ease: "back.out(1.7)", stagger: 0.2 }, t + 0.1);
    tl.fromTo(sel + " .punch-text", { scale: 1 }, { scale: 1.035, duration: dur, ease: "none" }, t);
  }
  // ref-card
  var _ref = step.querySelector(".ref-card");
  if (_ref) {
    var rs = "#" + _ref.id;
    tl.fromTo(rs, { opacity: 0, y: 34 }, { opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }, t);
    tl.fromTo(rs + " > div", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.45, ease: "power3.out", stagger: 0.12 }, t + 0.2);
    tl.to(rs + " .hl", { color: "#F0B429", backgroundSize: "100% 100%", duration: 0.7, ease: "power2.inOut" }, t + 1.0);
    tl.fromTo(rs, { scale: 1 }, { scale: 1.03, duration: dur, ease: "none", immediateRender: false }, t);
  }
  // barres : poussent à leur largeur relative
  if (has(".bfill")) tl.fromTo(sel + " .bfill", { scaleX: 0 }, { scaleX: function (i, el) { return parseFloat(el.getAttribute("data-w")) / 100; }, transformOrigin: "left center", duration: 0.8, ease: "power3.out", stagger: 0.14 }, t + 0.3);
  // seuil : le remplissage rejoint la valeur, le repère se pose
  if (has(".sfill")) {
    tl.fromTo(sel + " .sfill", { scaleX: 0 }, { scaleX: function (i, el) { return parseFloat(el.getAttribute("data-w")) / 100; }, transformOrigin: "left center", duration: 0.9, ease: "power3.out" }, t + 0.3);
    tl.fromTo(sel + " .stick", { opacity: 0, scaleY: 0 }, { opacity: .9, scaleY: 1, duration: 0.45, ease: "back.out(1.8)" }, t + 0.55);
  }
  // compare3 : lignes successives
  if (has(".crow")) tl.fromTo(sel + " .crow", { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out", stagger: 0.16 }, t + 0.15);
  // image plein écran, capture : zoom lent
  var _img = step.querySelector("img.fond, img.ref-shot");
  if (_img) tl.fromTo("#" + _img.id, { scale: 1 }, { scale: _img.classList.contains("fond") ? 1.07 : 1.04, duration: dur, ease: "none" }, t);
});
window.__timelines = window.__timelines || {};
window.__timelines["__ID__"] = tl;
"""


# --------------------------------------------------------------------------- #
# Petits utilitaires
# --------------------------------------------------------------------------- #

def die(msg):
    print("ERREUR : " + msg, file=sys.stderr)
    sys.exit(1)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("’", "'")
    return re.sub(r"[^a-z0-9%+\-']+", " ", s).strip()


def parse_value(raw):
    """Valeur tolérante : JSON, littéral Python, ou texte nu."""
    s = (raw or "").strip()
    if not s:
        return ""
    if len(s) >= 2 and s[0] == "`" and s[-1] == "`":
        s = s[1:-1].strip()
    for fn in (json.loads, ast.literal_eval):
        try:
            return fn(s)
        except Exception:
            pass
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'«“”":
        return s[1:-1].strip()
    if s.lower() in ("true", "oui"):
        return True
    if s.lower() in ("false", "non"):
        return False
    return s


def split_meta(line):
    """Coupe une ligne `a: 1 · b: 2` sans couper dans les JSON/guillemets."""
    parts, cur, depth, quote = [], [], 0, None
    for ch in line:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch in "[{(":
            depth += 1
            cur.append(ch)
        elif ch in "]})":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch == "·" and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    out = {}
    for p in parts:
        m = KV_RE.match(p.strip())
        if m:
            out[m.group(1).strip().lower()] = parse_value(m.group(2))
        elif p.strip():
            out.setdefault("_", p.strip())
    return out


def split_cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def clean_cell(s):
    s = MD_LINK_RE.sub(r"\1", s or "")
    return s.replace("**", "").replace("`", "").strip()


def truthy(v):
    return v is True or (isinstance(v, str) and v.strip().lower() in ("true", "oui", "1", "yes"))


def as_list(v):
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, (int, float)):
        return [v]
    return [x.strip() for x in str(v).split(",") if x.strip()]


def section_label(section):
    s = (section or "").strip()
    return KICK.get(norm(s), KICK.get(s.lower(), s[:1].upper() + s[1:] if s else "Scène"))


# --------------------------------------------------------------------------- #
# Lecture du storyboard
# --------------------------------------------------------------------------- #

def parse_registry(lines, prefix):
    """Tableau Markdown -> dict ordonné. Saute les sous-sections « Écartés »."""
    rows, header, skip = {}, None, False
    for ln in lines:
        h = re.match(r"^#{2,4}\s+(.*)$", ln)
        if h:
            skip = "ecart" in norm(h.group(1))
            header = None
            continue
        if skip or not ln.strip().startswith("|"):
            if not ln.strip().startswith("|"):
                header = None
            continue
        cells = split_cells(ln)
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if header is None:
            header = [norm(clean_cell(c)) for c in cells]
            continue
        row = {}
        for k, c in zip(header, cells):
            row[k] = clean_cell(c)
        rid = row.get("id", "")
        if not re.fullmatch(prefix + r"\d+", rid):
            continue
        rows[rid] = row
    return rows


def figures_from(rows):
    out = {}
    for rid, r in rows.items():
        status = norm(r.get("statut", r.get("status", "ok")))
        out[rid] = {
            "value": r.get("valeur", r.get("chiffre", "")),
            "label": r.get("label", ""),
            "source": r.get("source", ""),
            "status": "verify" if "verif" in status or status == "verify" else "ok",
            "note": r.get("note", ""),
        }
    return out


def refs_from(rows):
    out = {}
    for rid, r in rows.items():
        out[rid] = {
            "type": r.get("type", ""),
            "source": r.get("source", ""),
            "file": r.get("fichier local", r.get("fichier", "")),
            "status": r.get("statut", r.get("status", "")),
        }
    return out


def parse_storyboard(path):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    meta = {}
    for ln in lines[:20]:
        m = re.match(r"^\*\*(.+?)\*\*\s*:\s*(.+)$", ln.strip())
        if m:
            meta[m.group(1).strip().lower()] = m.group(2).strip()
    title = ""
    for ln in lines:
        if ln.startswith("# "):
            title = re.sub(r"^#\s*(STORYBOARD\s*[—–-]\s*)?", "", ln).strip()
            break

    # découpage par sections de niveau 2
    sections, cur, name = {}, [], "__head__"
    for ln in lines:
        if re.match(r"^##\s+", ln):
            sections[name] = cur
            name = ln
            cur = []
        else:
            cur.append(ln)
    sections[name] = cur

    fig_lines, ref_lines, scene_lines = [], [], []
    for h, body in sections.items():
        hh = norm(h)
        if re.match(r"^##\s*1b", h) or "references" in hh and "registre" in hh:
            ref_lines = body
        elif re.match(r"^##\s*1\b", h) or ("registre" in hh and "chiffre" in hh):
            fig_lines = body
        elif re.match(r"^##\s*4\b", h) or "scene" in hh:
            scene_lines = body
    if not scene_lines:
        scene_lines = lines

    figs = figures_from(parse_registry(fig_lines, "F"))
    refs = refs_from(parse_registry(ref_lines, "R"))
    scenes = parse_scenes(scene_lines)
    if not scenes:
        die("aucune scène trouvée dans %s (attendu : §4 avec des en-têtes `### I1 — Titre`)" % path)
    return {"title": title or "film", "meta": meta, "figures": figs, "refs": refs, "scenes": scenes}


def parse_scenes(lines):
    scenes, cur = [], None
    in_steps = False
    for ln in lines:
        sm = SCENE_HEAD_RE.match(ln)
        if sm:
            cur = {"id": sm.group(1), "title": sm.group(2).strip(), "section": "", "type": "cards",
                   "fond": "BG-00", "duree": None, "punchline": "", "cols2": False, "steps": []}
            scenes.append(cur)
            in_steps = False
            continue
        if cur is None:
            continue
        if re.match(r"^#{2,4}\s+", ln):
            in_steps = "etape" in norm(ln) or "step" in norm(ln)
            continue

        bm = BULLET_RE.match(ln)
        if bm:
            indent, body = len(bm.group(1)), bm.group(2).strip()
            step_m = re.match(r"^`([^`]+)`\s*(?:·|—|–|-)?\s*(.*)$", body)
            if step_m and STEP_ID_RE.match(step_m.group(1)):
                in_steps = True
                cur["steps"].append(parse_step_head(step_m.group(1), step_m.group(2)))
                continue
            if in_steps and cur["steps"] and indent >= 2:
                kv = KV_RE.match(body)
                if kv:
                    apply_step_kv(cur["steps"][-1], kv.group(1), kv.group(2))
                    continue
            if not in_steps:
                # métadonnées de scène
                for k, v in split_meta(body).items():
                    apply_scene_kv(cur, k, v)
                continue
        # clé: valeur sans puce (tolérance)
        kv = KV_RE.match(ln.strip()) if ln.strip() else None
        if kv and cur["steps"] and in_steps and (len(ln) - len(ln.lstrip())) >= 2:
            apply_step_kv(cur["steps"][-1], kv.group(1), kv.group(2))
        elif kv and not in_steps:
            apply_scene_kv(cur, kv.group(1).strip().lower(), parse_value(kv.group(2)))
    return [s for s in scenes if s["steps"]]


def parse_step_head(sid, rest):
    step = {"id": sid, "cue": "", "label": "", "camera": "off", "params": {}, "blocks": [],
            "figures": [], "t": None, "duree": None}
    cm = re.search(r"cue\s*[«\"“]([^»\"”]+)[»\"”]", rest, re.I)
    if cm:
        step["cue"] = cm.group(1).strip()
    lm = re.search(r"→\s*\*\*(.+?)\*\*", rest)
    if lm:
        step["label"] = lm.group(1).strip()
    tm = re.search(r"\bt=([\d.]+)", rest)
    if tm:
        step["t"] = float(tm.group(1))
    dm = re.search(r"\(([\d.]+)\s*s\)", rest)
    if dm:
        step["duree"] = float(dm.group(1))
    km = re.search(r"\[([A-Za-z]+)/([A-Za-z0-9\-]+)\]", rest)
    if km:
        step["camera"] = km.group(1).lower()
        step["params"]["kind"] = km.group(2)
    if not step["label"]:
        tail = re.sub(r"^.*?\]\s*", "", rest) if km else rest
        tail = re.sub(r"cue\s*[«\"“][^»\"”]+[»\"”]", "", tail, flags=re.I)
        step["label"] = tail.strip(" ·—-")
    return step


def apply_scene_kv(scene, k, v):
    k = norm(k)
    if k in ("section", "partie"):
        scene["section"] = str(v)
    elif k == "type":
        scene["type"] = str(v).strip().lower()
    elif k in ("fond", "background", "bg"):
        scene["fond"] = str(v).strip()
    elif k.startswith("duree") or k == "duration":
        try:
            scene["duree"] = float(re.sub(r"[^\d.]", "", str(v)) or 0) or None
        except ValueError:
            pass
    elif k in ("figures", "figure"):
        scene.setdefault("figures", []).extend(as_list(v))
    elif k in ("refs", "ref"):
        scene.setdefault("refs", []).extend(as_list(v))
    elif k == "cols2":
        scene["cols2"] = truthy(v)
    elif k in ("punchline", "punch"):
        scene["punchline"] = str(v)


def apply_step_kv(step, k, raw):
    key = norm(k).replace(" ", "_")
    v = parse_value(raw)
    if key == "kind":
        step["params"]["kind"] = str(v).strip().lower()
    elif key in ("notes", "note", "guide"):
        step["params"]["notes"] = str(v)
    elif key == "camera" or key == "cam":
        step["camera"] = str(v).strip().lower()
    elif key.startswith("duree") or key == "duration":
        try:
            step["duree"] = float(re.sub(r"[^\d.]", "", str(v)) or 0) or None
        except ValueError:
            pass
    elif key == "t":
        try:
            step["t"] = float(v)
        except (TypeError, ValueError):
            pass
    elif key == "figure":
        step["figures"] = [str(v).strip()]
    elif key == "figures":
        step["figures"] = [str(x).strip() for x in as_list(v)]
    elif key == "ref":
        step["params"]["ref"] = str(v).strip()
    elif key == "blocks":
        step["blocks"] = v if isinstance(v, list) else [v]
    elif key == "cols2":
        step["params"]["cols2"] = truthy(v)
    else:
        step["params"][key] = v


# --------------------------------------------------------------------------- #
# Temps
# --------------------------------------------------------------------------- #

def transcript_words(data):
    words = []
    if isinstance(data, dict) and isinstance(data.get("words"), list):
        for w in data["words"]:
            txt = w.get("word") or w.get("text") or ""
            if txt.strip():
                words.append((float(w.get("start") or 0), txt))
    segs = data.get("segments", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    if not words:
        for s in segs:
            txt = s.get("text") or ""
            tokens = txt.split()
            if not tokens:
                continue
            a = float(s.get("start") or 0)
            b = float(s.get("end") or a + len(tokens) * 0.35)
            step = max(0.05, (b - a) / len(tokens))
            for i, tok in enumerate(tokens):
                words.append((a + i * step, tok))
    return words


def find_cue(words, cue, start):
    tokens = [norm(w) for w in cue.replace("«", "").replace("»", "").split()]
    tokens = [t for t in tokens if t]
    if not tokens:
        return None
    hay = []
    for i, (t, txt) in enumerate(words):
        hay.append((t, norm(txt)))
    q = tokens[0]
    for i in range(start, len(hay)):
        if hay[i][1] == q or hay[i][1].startswith(q):
            ok = True
            for j in range(1, len(tokens)):
                if i + j >= len(hay) or not (hay[i + j][1] == tokens[j] or hay[i + j][1].startswith(tokens[j])):
                    ok = False
                    break
            if ok:
                return i, hay[i][0]
    return None


def resolve_times(scenes, transcript):
    words = transcript_words(transcript) if transcript else []
    end_audio = words[-1][0] + 0.5 if words else 0.0

    # 1) temps explicites + recalage des cues sur la voix
    for scene in scenes:
        for step in scene["steps"]:
            step["_t"] = step.get("t")
    if words:
        cursor = 0
        for scene in scenes:
            for step in scene["steps"]:
                if step["_t"] is not None:
                    continue
                cue = step.get("cue") or ""
                hit = find_cue(words, cue, cursor) if cue else None
                if hit:
                    cursor = hit[0] + 1
                    step["_t"] = hit[1]
                else:
                    print("AVERTISSEMENT : cue introuvable dans le transcript pour %s (%r) ; "
                          "temps estimé" % (step["id"], cue), file=sys.stderr)
    # temps manquants dans une scène minutée : on prolonge le précédent
    for scene in scenes:
        last = None
        for step in scene["steps"]:
            if step["_t"] is not None:
                last = step["_t"]
            elif last is not None:
                step["_t"] = last + (step.get("duree") or 2.0)
                last = step["_t"]

    # 2) durées estimées quand aucun temps explicite n'existe
    for scene in scenes:
        steps = scene["steps"]
        if any(s["_t"] is not None for s in steps):
            continue
        explicit = [s["duree"] for s in steps if s.get("duree")]
        d = scene.get("duree")
        if d and len(explicit) != len(steps):
            rest = max(0.0, d - sum(explicit))
            n = len(steps) - len(explicit)
            for s in steps:
                if not s.get("duree"):
                    s["duree"] = rest / n if n else d / len(steps)
        elif not d:
            base = sum(explicit) / len(explicit) if explicit else 6.0
            for s in steps:
                if not s.get("duree"):
                    s["duree"] = base

    # 3) temps absolus, durée de chaque étape, durée de scène
    out, clock = [], 0.0
    for si, sc in enumerate(scenes):
        steps = sc["steps"]
        if any(s["_t"] is not None for s in steps):
            first = next(s["_t"] for s in steps if s["_t"] is not None)
            start = first
            for s in steps:
                if s["_t"] is None:
                    s["_t"] = start
                s["_t"] = max(s["_t"], start)
        else:
            start = clock
            for s in steps:
                s["_t"] = clock
                clock += s["duree"]

        for i, s in enumerate(steps):
            if i + 1 < len(steps):
                s["_abs_dur"] = max(0.4, steps[i + 1]["_t"] - s["_t"])
            else:
                s["_abs_dur"] = max(0.4, s.get("duree") or 4.0)
        sc["_start"] = start
        # une scène sans temps explicite démarre après la précédente
        clock = max(clock, steps[-1]["_t"] + steps[-1]["_abs_dur"])
        out.append(sc)

    for i, sc in enumerate(out):
        if i + 1 < len(out):
            sc["_dur"] = max(0.1, out[i + 1]["_start"] - sc["_start"])
        elif words:
            sc["_dur"] = max(0.1, end_audio - sc["_start"])
        else:
            sc["_dur"] = max(0.1, sc["steps"][-1]["_t"] + sc["steps"][-1]["_abs_dur"] - sc["_start"])
        # la dernière étape tient jusqu'à la fin de sa scène
        last = sc["steps"][-1]
        last["_abs_dur"] = max(last["_abs_dur"], sc["_dur"] - (last["_t"] - sc["_start"]))
    return out


# --------------------------------------------------------------------------- #
# Rendu des primitives
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #

def comp_id(i):
    return "i%02d" % i


def scene_bg(scene):
    fond = str(scene.get("fond") or "BG-00").strip()
    if fond.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        return fond if fond.startswith("assets/") else "assets/" + fond.lstrip("/")
    return "assets/bg/%s.jpg" % fond


def render_composition(renderer, scene, idx, total_dur, camera_src, camera_media_start):
    cid = comp_id(idx)
    dur = float(scene.get("_dur") or total_dur)
    start = float(scene.get("_start") or 0)
    bg = scene_bg(scene)
    kicker = "%s · %s" % (scene["id"], section_label(scene.get("section", "")))
    slideno = ""

    parts = []
    for step in scene["steps"]:
        html, opts = renderer.render_step(scene, step)
        rel = max(0.0, step["_t"] - start)
        sdur = max(0.4, min(step["_abs_dur"], dur - rel)) if dur > rel else max(0.4, step["_abs_dur"])
        sid = re.sub(r"[^A-Za-z0-9_-]+", "-", step["id"])
        cam = step.get("camera", "off")
        cls = opts.get("class", "step")
        slideno = '<div class="slideno">%s</div>' % esc(step["id"])
        if opts.get("punch"):
            body = '<div class="zone">%s</div>' % html
            parts.append('<section class="clip step-punch" id="step-%s" data-step="%s" data-start="%.2f" '
                         'data-duration="%.2f" data-track-index="1" data-cam="%s">%s%s</section>'
                         % (sid, esc(step["id"]), rel, sdur, esc(cam), slideno, body))
            continue
        if opts.get("full"):
            parts.append('<section class="clip step" id="step-%s" data-step="%s" data-start="%.2f" '
                         'data-duration="%.2f" data-track-index="1" data-cam="%s">%s%s</section>'
                         % (sid, esc(step["id"]), rel, sdur, esc(cam), slideno, html))
            continue
        head = ""
        if step.get("params", {}).get("kind") == "title" or step["id"].endswith("#0") and idx == 0:
            head = ('<div class="kicker">%s</div><div class="stitle">%s</div>'
                    % (esc(kicker), esc(step.get("params", {}).get("title") or scene["title"])))
        zone_cls = "zone"
        if opts.get("cols2") or step["params"].get("cols2") or scene.get("cols2"):
            zone_cls += " cols2"
        parts.append('<section class="clip %s" id="step-%s" data-step="%s" data-start="%.2f" '
                     'data-duration="%.2f" data-track-index="1" data-cam="%s">%s%s'
                     '<div class="%s"><div class="in" id="in-%s">%s</div></div></section>'
                     % (cls, sid, esc(step["id"]), rel, sdur, esc(cam), slideno, head,
                        zone_cls, sid, html))

    cam_html = ""
    if camera_src:
        cam_html = ('<div id="cam-frame-%s" class="cam-frame clip" '
                    'data-track-index="2" data-layout-allow-occlusion="">'
                    '<video id="cam-%s" src="%s" data-start="0" data-duration="%.2f" '
                    'data-media-start="%.2f" data-track-index="2" muted playsinline></video></div>'
                    % (cid, cid, esc(camera_src), dur, max(0.0, camera_media_start)))

    js = (JS_TEMPLATE.replace("__DUR__", "%.2f" % dur)
          .replace("__CAM__", "cam-frame-" + cid if camera_src else "__none__")
          .replace("__ID__", cid))

    return """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"></head><body>
<template>
<link rel="stylesheet" href="assets/style-joriel.css">
<link rel="stylesheet" href="assets/style-joriel-ext.css">
<div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080" data-duration="{dur:.2f}">
<div class="clip bg" id="fond" data-start="0" data-duration="{dur:.2f}" data-track-index="0" data-layout-allow-overflow="">
  <img class="fond" id="fond-img" src="{bg}" alt="">
  <div class="voile"></div>
  <div class="vignette"></div>
</div>
{cam}
{steps}
</div>
<script>{js}</script>
</template>
</body></html>
""".format(cid=cid, dur=dur, bg=esc(bg), cam=cam_html, steps="\n".join(parts), js=js)


def render_index(title, slug, scenes, total_dur, audio_src, audio_dur):
    hosts = []
    for i, sc in enumerate(scenes):
        hosts.append('<div id="%s" class="clip" data-composition-id="%s" data-composition-src="compositions/%s.html" '
                     'data-start="%.2f" data-duration="%.2f" data-track-index="0" data-width="1920" '
                     'data-height="1080" data-track-kind="graphics"></div>'
                     % (comp_id(i), comp_id(i), comp_id(i), sc["_start"], sc["_dur"]))
    audio = ""
    if audio_src:
        audio = ('<audio id="voix" src="%s" data-start="0" data-duration="%.2f"></audio>'
                 % (esc(audio_src), audio_dur or total_dur))
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1920, height=1080">
<title>{title}</title>
<script src="assets/gsap.min.js"></script>
</head>
<body>
<div id="root" data-composition-id="{slug}" data-start="0" data-duration="{dur:.2f}" data-width="1920" data-height="1080">
{hosts}
{audio}
</div>
<script>
window.__timelines = window.__timelines || {{}};
window.__timelines["{slug}"] = gsap.timeline({{ paused: true }});
</script>
</body>
</html>
""".format(title=esc(title), slug=esc(slug), dur=total_dur, hosts="\n".join(hosts), audio=audio)


# --------------------------------------------------------------------------- #
# Registres de sortie
# --------------------------------------------------------------------------- #

def design_for(step):
    p = dict(step["params"])
    p["kind"] = ALIASES.get(str(p.get("kind") or "kw").lower(), str(p.get("kind") or "kw").lower())
    if step.get("figures"):
        p.setdefault("figure", step["figures"][0])
    if step.get("blocks"):
        p.setdefault("blocks", step["blocks"])
    if step.get("camera") and step["camera"] != "off":
        p["camera"] = step["camera"]
    return p


def scenes_json(scenes):
    out = []
    for sc in scenes:
        beats = []
        for st in sc["steps"]:
            p = st["params"]
            beat = {
                "id": st["id"],
                "cue": st.get("cue") or "",
                "text": st.get("label") or "",
                "kind": design_for(st)["kind"],
                "col": p.get("col", "full"),
                # Paramètres complets : le studio pas à pas rend la même
                # primitive que la composition finale (versus, strike, etc.).
                "params": design_for(st),
            }
            if st.get("figures"):
                beat["figure"] = st["figures"][0]
                if len(st["figures"]) > 1:
                    beat["figures"] = st["figures"][1:]
            if p.get("viz"):
                beat["viz"] = p["viz"]
            if p.get("kind") == "bars" and p.get("items"):
                items, peak = [], 0.0
                for it in p["items"]:
                    it = dict(it) if isinstance(it, dict) else {"label": str(it), "value": 0}
                    it["v"] = to_float(it.get("value", it.get("v", 0)))
                    peak = max(peak, it["v"])
                    items.append(it)
                beat["viz"] = {"type": "bars", "items": items,
                               "max": to_float(p.get("max"), peak) or peak or 1.0}
            if p.get("kind") == "count":
                prefix, number, _ = num_parts(st.get("_value") or "")
                beat["viz"] = {"type": "count", "to": int(float(number)) if number else 0,
                               "prefix": p.get("prefix", "")}
            beats.append(beat)
        out.append({
            "id": sc["id"],
            "section": sc.get("section") or "analyse",
            "title": sc["title"],
            "type": sc.get("type") or "cards",
            "illustration": scene_bg(sc),
            "punchline": sc.get("punchline") or next(
                (st["params"].get("text") for st in sc["steps"] if st["params"].get("kind") == "punch"), ""),
            "beats": beats,
        })
    return {"scenes": out}


def posthoc_version(path):
    """Numéro N de `voix-posthoc-vN.wav` (comparaison numérique : v10 > v9), None sinon."""
    m = re.fullmatch(r"voix-posthoc-v(\d+)\.wav", Path(path).name)
    return int(m.group(1)) if m else None


def detect_audio(root):
    """`assets/voix.wav` s'il existe (choix explicite), sinon la dernière passe de nettoyage
    `voix-posthoc-vN.wav` (N le plus grand, numériquement), sinon un autre `voix-*.wav`."""
    assets = root / "assets"
    if (assets / "voix.wav").exists():
        return "assets/voix.wav"
    if not assets.exists():
        return None
    posthoc = [(posthoc_version(f), f) for f in assets.glob("voix-posthoc-v*.wav")]
    posthoc = [(n, f) for n, f in posthoc if n is not None]
    if posthoc:
        return str(max(posthoc, key=lambda nf: nf[0])[1].relative_to(root))
    found = sorted(assets.glob("voix-*.wav"))
    return str(found[-1].relative_to(root)) if found else None


def wav_duration(path):
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--storyboard", default="assets/storyboard.md")
    ap.add_argument("--transcript", default=None)
    ap.add_argument("--audio", default=None)
    ap.add_argument("--camera", default=None)
    ap.add_argument("--slug", default=None)
    a = ap.parse_args()

    root = Path(a.root).resolve()
    sb_path = Path(a.storyboard)
    if not sb_path.is_absolute():
        sb_path = root / sb_path
    if not sb_path.exists():
        die("storyboard absent : %s (voir references/storyboard-format.md)" % sb_path)

    movie = parse_storyboard(sb_path)
    scenes = movie["scenes"]
    figs, refs = movie["figures"], movie["refs"]

    transcript = None
    if a.transcript:
        tp = Path(a.transcript)
        if not tp.is_absolute():
            tp = root / tp
        if not tp.exists():
            die("transcript absent : %s" % tp)
        transcript = json.loads(tp.read_text(encoding="utf-8"))

    # audio : option explicite, sinon détection
    audio = a.audio
    if not audio:
        audio = detect_audio(root)
    if audio:
        apath = Path(audio)
        if not apath.is_absolute():
            apath = root / apath
        if not apath.exists():
            print("AVERTISSEMENT : audio introuvable, ignoré : %s" % apath)
            audio = None

    camera = a.camera
    if not camera:
        for cand in ("assets/cam-clean.mkv", "assets/cam-clean.mp4", "assets/cam-original.mkv"):
            if (root / cand).exists():
                camera = cand
                break

    # timecodes
    scenes = resolve_times(scenes, transcript)
    total = max(sc["_start"] + sc["_dur"] for sc in scenes)
    audio_dur = wav_duration(root / audio) if audio else 0.0
    total = max(total, audio_dur)

    # sorties
    data = root / "data"
    comps = root / "compositions"
    data.mkdir(exist_ok=True)
    comps.mkdir(exist_ok=True)

    (data / "figures.json").write_text(
        json.dumps({"figures": figs}, ensure_ascii=False, indent=2), encoding="utf-8")
    (data / "refs.json").write_text(
        json.dumps({"refs": refs}, ensure_ascii=False, indent=2), encoding="utf-8")

    steps_out = []
    design_out = {}
    for i, sc in enumerate(scenes):
        for st in sc["steps"]:
            rel = max(0.0, st["_t"] - sc["_start"])
            steps_out.append({
                "id": st["id"],
                "scene": sc["id"],
                "scene_title": sc["title"],
                "slide": st["id"].split("#")[0],
                "frag": int(st["id"].split("#")[1]),
                "cue": st.get("cue", ""),
                "appear": rel,
                "t": st["_t"],
                "end": st["_t"] + st["_abs_dur"],
                "type": sc.get("type"),
                "fond": scene_bg(sc),
                "figures": st.get("figures", []),
                "duration": st["_abs_dur"],
                "punch": st["params"].get("kind") == "punch",
                "camera": st.get("camera", "off"),
                "kind": design_for(st)["kind"],
            })
            design_out[st["id"]] = design_for(st)
    (data / "steps.json").write_text(
        json.dumps({"steps": steps_out}, ensure_ascii=False, indent=2), encoding="utf-8")
    (data / "design.json").write_text(
        json.dumps({"steps": design_out}, ensure_ascii=False, indent=2), encoding="utf-8")

    renderer = Primitives(root, figs, refs)
    compositions = []
    for i, sc in enumerate(scenes):
        # valeur des figures pour le studio
        for st in sc["steps"]:
            st["_value"] = renderer.figure((st.get("figures") or [""])[0]).get("value", "")
        compositions.append(render_composition(renderer, sc, i, sc["_dur"], camera,
                                               sc["_start"] if camera else 0))
    (data / "scenes.json").write_text(
        json.dumps(scenes_json(scenes), ensure_ascii=False, indent=2), encoding="utf-8")

    for i, html in enumerate(compositions):
        (comps / (comp_id(i) + ".html")).write_text(html, encoding="utf-8")

    slug = a.slug or re.sub(r"[^a-z0-9]+", "-", norm(movie["title"])).strip("-") or "film"
    (root / "index.html").write_text(
        render_index(movie["title"], slug, scenes, total, audio, audio_dur), encoding="utf-8")

    # styles
    css = root / "assets" / "style-joriel.css"
    if not css.exists():
        demo_css = Path(__file__).resolve().parent.parent / "examples" / "demo" / "assets" / "style-joriel.css"
        if demo_css.exists():
            css.write_text(demo_css.read_text(encoding="utf-8"), encoding="utf-8")
            print("écrit : assets/style-joriel.css (copie de la démo ; les primitives absentes sont dans style-joriel-ext.css)")
        else:
            die("assets/style-joriel.css absent et modèle de démo introuvable")
    (root / "assets" / "style-joriel-ext.css").write_text(CSS_EXT, encoding="utf-8")

    for w in renderer.warnings:
        print("AVERTISSEMENT : " + w)
    missing = []
    for sc in scenes:
        p = root / scene_bg(sc)
        if not p.exists():
            missing.append(str(p.relative_to(root)))
    for m in sorted(set(missing)):
        print("AVERTISSEMENT : fond absent : %s" % m)

    print("écrit : index.html + %d compositions/ + data/ (%.1f s, %d étapes)"
          % (len(compositions), total, len(steps_out)))
    print("scènes : %s" % " · ".join("%s %s" % (sc["id"], comp_id(i)) for i, sc in enumerate(scenes)))
    if not (root / "assets" / "gsap.min.js").exists():
        print("AVERTISSEMENT : assets/gsap.min.js absent (copier depuis examples/demo/assets/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
