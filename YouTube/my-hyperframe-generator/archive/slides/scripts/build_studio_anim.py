#!/usr/bin/env python3
"""Construit studio-anim.html : l'ANIMATION HyperFrames jouée en pas-à-pas.

- vue présentation (capturée) : les scènes de data/scenes.json + figures,
  révélées manuellement (Avance/Recule/Espace/clic), même design que index.html.
- vue prompteur (mémo, jamais projetée) : par scène, les slides Advanced Slides
  correspondantes (aperçu + `note:`) comme aide-mémoire d'impro.
- inchangé : caméra Off/Coin/Full + Miroir, overlays OBS, Record/Pause/Stop
  (écran+micro -> webm -> POST /prise), synchro BroadcastChannel.

Mapping slides->scènes : marqueurs de section dans les commentaires
(<!-- I1 ... -->, <!-- S01 ... -->) ; la slide 1 (titre) va à la 1re scène.

Usage : python3 scripts/build_studio_anim.py [-o studio-anim.html]
Dépendances : stdlib uniquement.
"""
import html
import json
import os
import re
import shutil
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
# Le projet est le répertoire courant (comme build.py --root .), pas le dépôt.
ROOT = os.getcwd()

from render_primitive import Primitives  # noqa: E402  (module voisin, script lancé depuis scripts/)

FRAG_RE = re.compile(r"<!--\s*element\s+class\s*=\s*[\"']fragment[\"']\s*-->", re.I)
COMMENT_RE = re.compile(r"<!--(.*?)-->", re.S)
IMG_MD_RE = re.compile(r"!\[[^\]]*\]\(\s*([^)\s]+)[^)]*\)")
NOTE_RE = re.compile(r"^\s*note\s*:\s*$", re.I)
SEP_RE = re.compile(r"^\s*---\s*$")
MARK_RE = re.compile(r"\b([IS]\d{1,2})\b")


def esc(s):
    return html.escape(s or "", quote=False)


def inline_md(s):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", s)
    return s


def plain_preview(content, n=200):
    t = COMMENT_RE.sub(" ", content)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[#*>`\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return (t[:n] + "…") if len(t) > n else t


def parse_slides(path):
    if not os.path.exists(path):
        return []
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    start = 0
    if lines and lines[0].strip() == "---":
        for k in range(1, 40):
            if lines[k].strip() == "---":
                start = k + 1
                break
    chunks, cur = [], []
    for ln in lines[start:]:
        if SEP_RE.match(ln):
            chunks.append("\n".join(cur))
            cur = []
        else:
            cur.append(ln)
    chunks.append("\n".join(cur))
    slides = []
    for ch in chunks:
        if not ch.strip():
            continue
        parts = re.split(r"(?m)^\s*note\s*:\s*$", ch, maxsplit=1)
        content, notes = (parts[0].rstrip(), parts[1].strip()) if len(parts) == 2 else (ch, "")
        content = IMG_MD_RE.sub("", FRAG_RE.sub("", content)).strip()
        labels = [c.strip() for c in COMMENT_RE.findall(ch) if "fragment" not in c and "img:" not in c]
        slides.append({"content": content, "notes": notes,
                       "preview": plain_preview(content), "labels": labels})
    for i, s in enumerate(slides, 1):
        s["n"] = i
    return slides


def map_slides(slides, scene_ids):
    mapping = {sid: [] for sid in scene_ids}
    cur = None
    for s in slides:
        for lb in s["labels"]:
            m = MARK_RE.search(lb)
            if m and m.group(1).lower() in mapping:
                cur = m.group(1).lower()
                break
        (mapping[cur] if cur else mapping[scene_ids[0]]).append(s)
    return mapping


# Dossier d'overlays : explicite (HF_OVERLAYS_DIR), sinon le dossier du projet.
# Aucun chemin propre à un ancien projet n'est codé en dur.
OVERLAY_SRC = os.environ.get("HF_OVERLAYS_DIR", "")
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def slug(nom):
    base, ext = os.path.splitext(nom)
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base.lower()).strip("-")
    return (base or "image") + ext.lower()


def collect_overlays(dst):
    overs = []
    src_dir = os.path.expanduser(OVERLAY_SRC) if OVERLAY_SRC else dst
    if not os.path.isdir(src_dir):
        return overs
    same = os.path.abspath(src_dir) == os.path.abspath(dst)
    if not same:
        os.makedirs(dst, exist_ok=True)
    for nom in sorted(os.listdir(src_dir)):
        if not nom.lower().endswith(IMG_EXTS):
            continue
        src = os.path.join(src_dir, nom)
        d = os.path.join(dst, slug(nom))
        if (not same) and ((not os.path.exists(d)) or (os.path.getsize(d) != os.path.getsize(src))):
            shutil.copyfile(src, d)
        label = re.sub(r"\s*-\s*kindle\s*$", "", os.path.splitext(nom)[0], flags=re.I)
        overs.append({"label": label, "file": os.path.relpath(d, ROOT)})
    return overs


PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Studio Anim — l'animation en pas-à-pas</title>
<link rel="icon" href="data:,">
<script src="assets/gsap.min.js"></script>
<link rel="stylesheet" href="assets/style-joriel.css">
<link rel="stylesheet" href="assets/style-joriel-ext.css">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { width: 100%; height: 100%; overflow: hidden; background: #000; font-family: sans-serif; }
  #present { position: fixed; inset: 0; background: #0d1117; cursor: none; font-family: Verdana, Geneva, sans-serif; color: var(--blanc); }
  #present .scene { position: absolute; inset: 0; overflow: hidden; opacity: 0; color: #f5f4f0; }
  #present .fond { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
  #present .voile { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,.45), rgba(0,0,0,.78)); }
  #present .kicker { position: absolute; top: 4.4vh; left: 7.3vw; font-size: 2.8vh; letter-spacing: .22em; text-transform: uppercase; color: #fbbf24; }
  #present .title { position: absolute; top: 9.2vh; left: 7.3vw; right: 7.3vw; font-size: 5.4vh; line-height: 1.1; font-weight: 800; }
  #present .zone { position: absolute; top: 21vh; left: 7.3vw; right: 7.3vw; bottom: 13vh;
                   display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
  #present .src { position: absolute; left: 7.3vw; right: 7.3vw; bottom: 5vh; font-size: 2.6vh; color: #b8b2a7; }
  #present .step { width: 100%; margin-bottom: 2.4vh; opacity: 0; }
  #present .punch { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; text-align: center; padding: 0 7.3vw; background: #0d1117; opacity: 0; }
  #present .pt { font-size: 8vh; line-height: 1.15; font-weight: 900; }
  #present .fin { position: absolute; inset: 0; background: #000; display: none; z-index: 5; }
  #present .pastille { position: absolute; top: 2vh; right: 2vw; color: rgba(255,255,255,.55); font-size: 2vh; z-index: 6; }
  body.rec #present .pastille { display: none; }
  #present.flou .scene { filter: blur(16px) brightness(.65); transition: filter .45s ease; }
  #present .scene { transition: filter .45s ease; }
  #overlay { position: absolute; inset: 0; z-index: 4; display: none; pointer-events: auto; }
  #overlay img { width: 100%; height: 100%; object-fit: contain; display: block; filter: drop-shadow(0 24px 80px rgba(0,0,0,.65)); }
  #cam { position: absolute; z-index: 4; display: none; object-fit: cover; background: #000; }
  #cam.coin { display: block; top: 4vh; right: 3vw; width: 24vw; aspect-ratio: 16/9; border-radius: 1vw; border: 3px solid rgba(255,255,255,.85); box-shadow: 0 10px 40px rgba(0,0,0,.6); }
  #cam.full { display: block; left: 0; top: 0; width: 100%; height: 100%; }
  #cam.miroir { transform: scaleX(-1); }
  #prompteur { display: none; height: 100vh; background: #111; color: #eee; overflow-y: auto; }
  #prompteur .bar { position: sticky; top: 0; z-index: 10; background: #111; padding: 12px 18px 10px; border-bottom: 1px solid #333; }
  #prompteur .rowp { display: flex; gap: 8px; margin: 0 0 8px; flex-wrap: wrap; }
  #prompteur .rowp:last-child { margin-bottom: 0; }
  #prompteur .corps { padding: 14px 18px 18px; }
  #defile .bloc { opacity: .42; padding: 14px 4px 22px; border-bottom: 1px solid #2a2a2a; cursor: pointer; }
  #defile .bloc .b-kick { font-size: 14px; color: #fde68a; letter-spacing: .15em; margin-bottom: 4px; }
  #defile .bloc .b-cues { font-size: 15px; color: #888; margin: 6px 0; }
  #defile .bloc .b-slide { font-size: 17px; color: #bbb; margin-top: 8px; }
  #defile .bloc .b-notes { font-size: 18px; line-height: 1.5; color: #777; background: #1a1a1a; border-radius: 8px; padding: 10px 12px; margin-top: 6px; white-space: pre-wrap; }
  #defile .bloc.cur { opacity: 1; }
  #defile .bloc.cur .b-notes { font-size: 28px; line-height: 1.55; color: #fff; background: #000; padding: 16px; }
  #defile .bloc.cur .b-slide { font-size: 19px; color: #eee; }
  #defile .bloc .b-step { font-size: 13px; color: #666; margin-top: 6px; }
  #prompteur button { font-size: 16px; padding: 9px 14px; border: none; border-radius: 8px; background: #2a2a2a; color: #fff; cursor: pointer; }
  #prompteur button:hover { background: #3a3a3a; }
  #prompteur button.go { background: #1d4ed8; }
  #prompteur button.rec { background: #b91c1c; }
  #prompteur button.on { outline: 2px solid #fde68a; }
  #prompteur button:disabled { opacity: .4; cursor: default; }
  #prompteur .meta { color: #999; font-size: 14px; margin-top: 8px; }
  #prompteur .dots { color: #666; font-size: 13px; margin: 8px 0; }
  #prompteur a.dl { display: inline-block; margin-top: 10px; color: #7dd3fc; font-size: 16px; }
  #prompteur .lbl { color: #777; font-size: 13px; align-self: center; }
</style>
</head>
<body>
<div id="present">
__SCENES__
  <div id="overlay"><img id="overImg" alt=""></div>
  <video id="cam" muted playsinline></video>
  <div class="fin" id="pFin"></div>
  <div class="pastille" id="pNum"></div>
</div>
<div id="prompteur">
  <div class="bar">
    <div class="rowp">
      <button id="bDebut" title="Home">&#124;&#9664; Début</button>
      <button id="bPrev" title="Flèche gauche">&#9664; Recule</button>
      <button id="bNext" class="go" title="Espace / flèche droite">Avance &#9654;</button>
      <button id="bFin" title="Fin">Fin &#9654;&#124;</button>
      <span class="lbl" id="stepLbl"></span>
    </div>
    <div class="rowp">
      <button id="bRec" class="rec">&#9679; Record</button>
      <button id="bPause" disabled>&#10074;&#10074; Pause</button>
      <button id="bStop" disabled>&#9632; Stop</button>
      <span class="lbl">Caméra :</span>
      <button id="bCamOff" class="on">Off</button>
      <button id="bCamCoin">Coin</button>
      <button id="bCamFull">Plein écran</button>
      <button id="bMiroir" class="on" title="Inverser gauche/droite">Miroir</button>
      <button id="bOpen">Ouvrir présentation</button>
    </div>
    <div class="rowp">
      <span class="lbl">Overlays :</span>
__OVERS_BTN__
    </div>
  </div>
  <div class="corps">
    <div id="defile"></div>
    <div class="meta" id="rMeta"></div>
    <div class="dots" id="rDots"></div>
    <div id="rDl"></div>
  </div>
</div>
<script>
var SCENES = __DATA__;
var OVERS = __OVERS__;
var N = SCENES.length;
var view = new URLSearchParams(location.search).get("view") || "present";
var idx = 0, step = 0, fini = false, camMode = "off", mirror = true, overlay = null, recOn = false;

// beats + punch final seulement si la scène a un bloc punch hérité (pas une étape punch)
function nsteps() { return SCENES[idx].steps.length + (SCENES[idx].has_punch ? 1 : 0); }
var bc = null;
try { bc = new BroadcastChannel("studio-anim"); } catch (e) { bc = null; }
function emit() {
  var msg = JSON.stringify({ idx: idx, step: step, fini: fini, cam: camMode, mirror: mirror, overlay: overlay, rec: recOn });
  if (bc) { try { bc.postMessage(msg); } catch (e) {} }
  try { localStorage.setItem("studio-anim", msg); } catch (e) {}
}
function emitRaw(o) {
  var msg = JSON.stringify(o);
  if (bc) { try { bc.postMessage(msg); } catch (e) {} }
  try { localStorage.setItem("studio-anim", msg); } catch (e) {}
}
function onMsg(msg) {
  var d = null;
  try { d = JSON.parse(msg); } catch (e) { return; }
  if (d.camErr && view === "prompteur") { tickMeta(d.camErr); return; }
  if (!("idx" in d)) return;
  idx = Math.max(0, Math.min(N - 1, d.idx)); fini = !!d.fini;
  step = Math.max(0, Math.min(nsteps() - 1, ("step" in d) ? d.step : 0));
  if (view === "present" && d.cam && d.cam !== camMode) applyCam(d.cam, true);
  if (view === "present" && ("mirror" in d) && d.mirror !== mirror) { mirror = !!d.mirror; refreshCamClass(); syncMiroir(); }
  if (view === "present" && ("overlay" in d) && d.overlay !== overlay) applyOverlay(d.overlay, false);
  if (view === "present" && ("rec" in d)) { recOn = !!d.rec; document.body.classList.toggle("rec", recOn); }
  render();
}
if (bc) bc.onmessage = function (ev) { onMsg(ev.data); };
window.addEventListener("storage", function (ev) { if (ev.key === "studio-anim" && ev.newValue) onMsg(ev.newValue); });

function go(i) { idx = Math.max(0, Math.min(N - 1, i)); step = 0; fini = false; emit(); render(); }
function avance() {
  if (fini) return;
  if (step < nsteps() - 1) { step++; emit(); render(); }
  else if (idx < N - 1) { idx++; step = 0; emit(); render(); }
}
function recule() {
  if (fini) { fini = false; emit(); render(); return; }
  if (step > 0) { step--; emit(); render(); }
  else if (idx > 0) { idx--; step = nsteps() - 1; emit(); render(); }
}
function debut() { go(0); }
function fin() { fini = true; emit(); render(); }
function setCam(m) {
  camMode = m;
  ["bCamOff", "bCamCoin", "bCamFull"].forEach(function (id) {
    var b = document.getElementById(id);
    if (b) b.classList.toggle("on", (id === "bCamOff" && m === "off") || (id === "bCamCoin" && m === "coin") || (id === "bCamFull" && m === "full"));
  });
  emit();
  if (view === "present") applyCam(m, false);
}
var camStream = null;
function refreshCamClass() {
  var v = document.getElementById("cam");
  if (camMode === "off") { v.className = ""; return; }
  v.className = ((camMode === "full") ? "full" : "coin") + (mirror ? " miroir" : "");
}
function syncMiroir() {
  var b = document.getElementById("bMiroir");
  if (b) b.classList.toggle("on", mirror);
}
function setMirror(m) { mirror = !!m; syncMiroir(); emit(); if (view === "present") refreshCamClass(); }
function applyCam(m, distant) {
  camMode = m;
  refreshCamClass();
  var v = document.getElementById("cam");
  if (m === "off") { try { v.pause(); } catch (e) {} return; }
  var start = function () { try { v.play(); } catch (e) {} };
  if (camStream) { start(); return; }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    emitRaw({ camErr: "Caméra non supportée ici (Chrome/Edge via http://localhost)." }); return;
  }
  navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 } }, audio: false }).then(function (s) {
    camStream = s; v.srcObject = s; start();
  }).catch(function (e) { emitRaw({ camErr: "Caméra refusée/indisponible : " + e.message }); });
}
var popAudio = null;
function pop(local) {
  try {
    if (!popAudio) { popAudio = new Audio("assets/sfx-pop.wav"); popAudio.volume = 0.5; }
    if (local === false) { popAudio.currentTime = 0; popAudio.play().catch(function () {}); return; }
    popAudio.currentTime = 0;
    popAudio.play().catch(function () {});
  } catch (e) {}
}
function toggleOverlay(name) {
  overlay = (overlay === name) ? null : name;
  emit();
  if (view === "present") applyOverlay(overlay, true);
  else render();
}
function applyOverlay(name, sounded) {
  overlay = name;
  var box = document.getElementById("overlay");
  var img = document.getElementById("overImg");
  if (!name) {
    document.getElementById("present").classList.remove("flou");
    if (window.gsap) { gsap.to(box, { opacity: 0, duration: 0.3, onComplete: function () { box.style.display = "none"; } }); }
    else { box.style.display = "none"; }
    return;
  }
  var f = null;
  for (var k = 0; k < OVERS.length; k++) if (OVERS[k].file === name) f = OVERS[k];
  if (!f) return;
  if (img.getAttribute("src") !== f.file) img.src = f.file;
  document.getElementById("present").classList.add("flou");
  box.style.display = "block";
  if (window.gsap) {
    gsap.fromTo(box, { opacity: 0 }, { opacity: 1, duration: 0.35 });
    gsap.fromTo(img, { opacity: 0, scale: 0.94 }, { opacity: 1, scale: 1, duration: 0.55, ease: "back.out(1.3)" });
  }
  if (sounded) pop(true);
}
function grp(n, dec) {
  var s = dec ? Number(n).toFixed(dec) : Math.round(n).toString();
  var p = s.split(".");
  p[0] = p[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, " ");
  return p.join(",");
}
function paintStep(i, k, animate) {
  var sc = document.getElementById("sc-" + i);
  if (!sc) return;
  var steps = sc.querySelectorAll(".step");
  for (var j = 0; j < steps.length; j++) {
    (function (el, sj) {
      var meta = SCENES[i].steps[sj] || {};
      var show = sj < k, cur = sj === k;
      var ctrs = el.querySelectorAll(".ctr");
      var fills = el.querySelectorAll(".bfill, .sfill");
      function final() {
        el.style.opacity = 1;
        for (var c = 0; c < ctrs.length; c++) {
          var t = parseFloat(ctrs[c].getAttribute("data-target"));
          if (isFinite(t)) ctrs[c].textContent = grp(t, parseInt(ctrs[c].getAttribute("data-dec") || "0", 10));
        }
        for (var f = 0; f < fills.length; f++) fills[f].style.transform = "scaleX(" + (fills[f].getAttribute("data-w") / 100) + ")";
      }
      if (show) { if (window.gsap) gsap.set(el, { opacity: 1 }); else el.style.opacity = 1; final(); }
      else if (cur) {
        if (window.gsap && animate) {
          var kind = meta.kind || "fade";
          if (kind === "slide") gsap.fromTo(el, { opacity: 0, x: -160 }, { opacity: 1, x: 0, duration: 0.6, ease: "power3.out" });
          else gsap.fromTo(el, { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" });
          if (kind === "spotlight") {
            var _its = el.querySelectorAll(".spot .it");
            for (var z = 0; z < _its.length; z++) {
              (function (it, zi) {
                gsap.fromTo(it, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.45, ease: "power3.out", delay: zi * 0.12 });
                gsap.fromTo(it, { scale: 1 }, { scale: 1.16, duration: 0.28, yoyo: true, repeat: 1, ease: "power2.inOut", delay: 0.7 + zi * 0.3 });
              })(_its[z], z);
            }
          }
          if (ctrs.length) {
            for (var c = 0; c < ctrs.length; c++) {
              (function (ctr) {
                var target = parseFloat(ctr.getAttribute("data-target"));
                var dec = parseInt(ctr.getAttribute("data-dec") || "0", 10);
                if (!isFinite(target)) return;
                var o = { v: 0 };
                gsap.to(o, { v: target, duration: 1.2, ease: "power2.out", onUpdate: function () { ctr.textContent = grp(o.v, dec); } });
              })(ctrs[c]);
            }
          } else final();
          if (fills.length) {
            for (var g = 0; g < fills.length; g++) {
              (function (fl) { gsap.fromTo(fl, { scaleX: 0 }, { scaleX: fl.getAttribute("data-w") / 100, duration: 1.0, ease: "power2.out", delay: 0.2 }); })(fills[g]);
            }
          }
        } else final();
      }
      else { if (window.gsap) gsap.set(el, { opacity: 0 }); else el.style.opacity = 0; }
    })(steps[j], j);
  }
  var punch = sc.querySelector(".punch");
  var isPunch = k >= steps.length;
  if (punch) {
    if (isPunch) {
      sc.querySelector(".zone").style.display = "none";
      punch.style.opacity = 1;
      if (window.gsap && animate) gsap.fromTo(punch.querySelector(".pt"), { opacity: 0, scale: 1.12 }, { opacity: 1, scale: 1, duration: 0.7, ease: "power2.out" });
      else if (window.gsap) gsap.set(punch.querySelector(".pt"), { opacity: 1 });
    } else {
      sc.querySelector(".zone").style.display = "block";
      punch.style.opacity = 0;
    }
  }
}
var scrolledKey = "";
function escHtml(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function buildDefile() {
  var html = "";
  for (var i = 0; i < N; i++) {
    var s = SCENES[i];
    var slides = "";
    for (var g = 0; g < s.memo.length; g++) {
      var m = s.memo[g];
      slides += '<div class="b-slide">SLIDE ' + m.n + (m.notes ? "" : " (sans notes)") + " — " + escHtml(m.preview) + "</div>"
        + (m.notes ? '<div class="b-notes">' + escHtml(m.notes) + "</div>" : "");
    }
    html += '<div class="bloc" id="bloc-' + i + '" data-i="' + i + '">'
      + '<div class="b-kick">SCÈNE ' + (i + 1) + "/" + N + " — " + escHtml(s.kicker) + " · " + escHtml(s.title) + "</div>"
      + '<div class="b-cues">déroulé : ' + escHtml(s.cues.join(" → ")) + "</div>"
      + slides
      + ((i === idx) ? '<div class="b-step">pas ' + (step + 1) + "/" + nsteps() + (s.has_punch && step >= s.steps.length ? " (punch)" : "") + "</div>" : "")
      + "</div>";
  }
  document.getElementById("defile").innerHTML = html;
  var blocs = document.getElementById("defile").children;
  for (var j = 0; j < blocs.length; j++) {
    (function (el) {
      el.addEventListener("click", function () { go(parseInt(el.getAttribute("data-i"), 10)); });
    })(blocs[j]);
  }
}
function render() {
  if (view === "present") {
    document.getElementById("present").style.display = "block";
    document.getElementById("prompteur").style.display = "none";
    var scenes = document.querySelectorAll("#present .scene");
    for (var q = 0; q < scenes.length; q++) {
      scenes[q].style.opacity = (q === idx) ? 1 : 0;
      scenes[q].style.zIndex = (q === idx) ? 2 : 1;
    }
    paintStep(idx, step, true);
    document.getElementById("pNum").textContent = fini ? "FIN" : (idx + 1) + " / " + N + " · pas " + (step + 1) + "/" + nsteps();
    document.getElementById("pFin").style.display = fini ? "block" : "none";
  } else {
    document.getElementById("present").style.display = "none";
    document.getElementById("prompteur").style.display = "block";
    buildDefile();
    var blocs = document.getElementById("defile").children;
    for (var bi = 0; bi < blocs.length; bi++) blocs[bi].classList.toggle("cur", bi === idx);
    var key = idx + ":" + step + ":" + fini;
    if (key !== scrolledKey) {
      scrolledKey = key;
      var cur = document.getElementById("bloc-" + idx);
      if (cur && cur.scrollIntoView) {
        try { cur.scrollIntoView({ block: "center", behavior: "smooth" }); } catch (e) {}
      }
    }
    var dots = "";
    for (var k = 0; k < N; k++) dots += (k === idx) ? "● " : "○ ";
    document.getElementById("rDots").textContent = dots;
    var fl = document.getElementById("stepLbl");
    if (fl) fl.textContent = "pas " + (step + 1) + "/" + nsteps() + (step >= SCENES[idx].steps.length ? " (punch)" : "");
    for (var q2 = 0; q2 < OVERS.length; q2++) {
      var bb = document.getElementById("over-" + q2);
      if (bb) bb.classList.toggle("on", overlay === OVERS[q2].file);
    }
    tickMeta();
  }
}
document.addEventListener("keydown", function (ev) {
  if (ev.key === "ArrowRight" || ev.key === " ") { ev.preventDefault(); if (!fini) avance(); }
  else if (ev.key === "ArrowLeft") { if (!fini) recule(); }
  else if (ev.key === "Home") debut();
  else if (ev.key === "End") fin();
});
if (view === "present") {
  document.getElementById("present").addEventListener("click", function () { if (!fini) avance(); });
  document.getElementById("overlay").addEventListener("click", function (ev) { ev.stopPropagation(); });
}
for (var oi = 0; oi < OVERS.length; oi++) {
  (function (f) {
    var b = document.getElementById("over-" + OVERS.indexOf(f));
    if (b) b.onclick = function () { toggleOverlay(f.file); };
  })(OVERS[oi]);
}
document.getElementById("bDebut").onclick = debut;
document.getElementById("bPrev").onclick = recule;
document.getElementById("bNext").onclick = avance;
document.getElementById("bFin").onclick = fin;
document.getElementById("bCamOff").onclick = function () { setCam("off"); };
document.getElementById("bCamCoin").onclick = function () { setCam("coin"); };
document.getElementById("bCamFull").onclick = function () { setCam("full"); };
document.getElementById("bMiroir").onclick = function () { setMirror(!mirror); };
document.getElementById("bOpen").onclick = function () {
  window.open(location.pathname.replace("studio-anim.html", "studio-anim.html") + "?view=present", "_blank");
};
var rec = null, chunks = [], t0rec = 0, timerId = null, paused = false;
function mime() {
  var cands = ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"];
  for (var i = 0; i < cands.length; i++) {
    try { if (window.MediaRecorder && MediaRecorder.isTypeSupported(cands[i])) return cands[i]; } catch (e) {}
  }
  return "";
}
function fmt(ms) {
  var s = Math.floor(ms / 1000);
  var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60); s = s % 60;
  return (h < 10 ? "0" + h : h) + ":" + (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
}
function tickMeta(extra) {
  var el = document.getElementById("rMeta");
  if (!el) return;
  var base = rec ? ("● REC " + fmt(performance.now() - t0rec) + (paused ? " (pause)" : "")) : "Prêt. Scène " + (idx + 1) + "/" + N + " · pas " + (step + 1) + "/" + nsteps() + ".";
  el.textContent = extra ? (base + " " + extra) : base;
}
document.getElementById("bRec").onclick = function () {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
    tickMeta("Capture non supportée ici (utiliser Chrome/Edge via http://localhost)."); return;
  }
  navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 30 }, audio: false }).then(function (screen) {
    var mic = (navigator.mediaDevices.getUserMedia) ? navigator.mediaDevices.getUserMedia({ audio: true }) : Promise.reject(new Error("micro indisponible"));
    mic.then(function (audio) {
      var stream = new MediaStream(screen.getVideoTracks().concat(audio.getAudioTracks()));
      screen.getVideoTracks()[0].onended = function () { stopRec("Partage d'écran terminé."); };
      chunks = [];
      try { rec = new MediaRecorder(stream, mime() ? { mimeType: mime(), videoBitsPerSecond: 12000000 } : undefined); }
      catch (e) { tickMeta("MediaRecorder indisponible : " + e.message); return; }
      rec.ondataavailable = function (ev) { if (ev.data && ev.data.size) chunks.push(ev.data); };
      rec.onstop = function () {
        var blob = new Blob(chunks, { type: "video/webm" });
        var url = URL.createObjectURL(blob);
        document.getElementById("rDl").innerHTML = "";
        var a = document.createElement("a");
        a.className = "dl"; a.href = url; a.download = "prise-studio.webm";
        a.textContent = "⬇ Télécharger la prise (" + (blob.size / 1048576).toFixed(1) + " Mo)";
        document.getElementById("rDl").appendChild(a);
        var st = document.createElement("div");
        st.className = "meta"; st.id = "rSave";
        st.textContent = "Envoi vers le dossier des prises…";
        document.getElementById("rDl").appendChild(st);
        (function send() {
          fetch("prise", { method: "POST", body: blob }).then(function (r) { return r.json(); }).then(function (j) {
            st.textContent = "✓ Enregistré : " + j.path + " (" + (j.size / 1048576).toFixed(1) + " Mo)";
          }).catch(function (e) {
            st.textContent = "Envoi auto impossible (" + e.message + ") : utilise le lien de téléchargement.";
          });
        })();
        stream.getTracks().forEach(function (t) { try { t.stop(); } catch (e) {} });
        rec = null; recOn = false; emit(); tickMeta("Prise terminée.");
        document.getElementById("bRec").disabled = false;
        document.getElementById("bPause").disabled = true;
        document.getElementById("bStop").disabled = true;
      };
      rec.start(1000); t0rec = performance.now(); paused = false;
      recOn = true; emit();
      timerId = setInterval(function () { tickMeta(); }, 500);
      document.getElementById("bRec").disabled = true;
      document.getElementById("bPause").disabled = false;
      document.getElementById("bStop").disabled = false;
      document.getElementById("bPause").textContent = "❚❚ Pause";
      tickMeta("Enregistrement… choisis l'écran de présentation dans le sélecteur.");
    }).catch(function (e) { tickMeta("Micro refusé : " + e.message + "."); screen.getTracks().forEach(function (t) { try { t.stop(); } catch (e2) {} }); });
  }).catch(function (e) { tickMeta("Capture annulée : " + e.message); });
};
document.getElementById("bPause").onclick = function () {
  if (!rec) return;
  if (paused) { try { rec.resume(); } catch (e) {} paused = false; document.getElementById("bPause").textContent = "❚❚ Pause"; }
  else { try { rec.pause(); } catch (e) {} paused = true; document.getElementById("bPause").textContent = "▶ Reprendre"; }
  tickMeta();
};
function stopRec(msg) {
  if (rec && rec.state !== "inactive") { try { rec.stop(); } catch (e) {} }
  if (timerId) { clearInterval(timerId); timerId = null; }
  if (msg) tickMeta(msg);
}
document.getElementById("bStop").onclick = function () { stopRec(); };
render();
</script>
</body>
</html>
"""


def legacy_params(beat):
    """Ancien `scenes.json` : reconstruit des paramètres depuis `viz`."""
    kind = beat.get("kind") or "kw"
    viz = beat.get("viz") or {}
    p = {"kind": kind}
    if viz.get("type") == "count":
        p.update(kind="count", value=viz.get("to"), prefix=viz.get("prefix", ""))
    elif viz.get("type") == "bars":
        p.update(kind="bars", items=viz.get("items") or [], max=viz.get("max"))
    elif viz.get("type") == "waffle":
        p.update(kind="waffle", **{k: viz[k] for k in ("marked", "total", "label") if k in viz})
    elif viz.get("type") == "versus":
        p.update(kind="versus", left=viz.get("left") or [], right=viz.get("right") or [])
    return p


def beat_to_step(scene, beat, index):
    """Reconstruit l'étape complète attendue par `Primitives.render_step`."""
    p = beat.get("params")
    if not isinstance(p, dict) or not p:
        p = legacy_params(beat)
    figs = []
    if beat.get("figure"):
        figs.append(beat["figure"])
    figs.extend(beat.get("figures") or [])
    return {
        "id": beat.get("id") or "%s#%d" % (scene["id"], index),
        "params": p,
        "figures": figs,
        "label": beat.get("text") or "",
        "cue": beat.get("cue") or "",
    }


def anim_meta(anim):
    anim = anim or {}
    return {
        "kind": anim.get("kind", "fade"),
        "to": anim.get("to"),
        "prefix": anim.get("prefix", ""),
        "suffix": anim.get("suffix", ""),
        "dec": anim.get("dec", 0),
    }


def build(out_path):
    scenes = json.load(open(os.path.join(ROOT, "data/scenes.json"), encoding="utf-8"))["scenes"]
    figs = json.load(open(os.path.join(ROOT, "data/figures.json"), encoding="utf-8"))["figures"]
    refs_path = os.path.join(ROOT, "data/refs.json")
    refs = (json.load(open(refs_path, encoding="utf-8"))["refs"]
            if os.path.exists(refs_path) else {})
    renderer = Primitives(ROOT, figs, refs)
    slides = parse_slides(os.path.join(ROOT, "assets/slides.md"))
    mapping = map_slides(slides, [s["id"] for s in scenes]) if slides else {s["id"]: [] for s in scenes}
    if slides:
        orphan = [s["n"] for s in slides if not any(s in v for v in mapping.values())]
        assert not orphan, "slides non mappées : %s" % orphan

    KICK = {"bilan": "Le bilan", "analyse": "L'analyse"}

    def kicker(section):
        s = (section or "").strip()
        return KICK.get(s.lower(), s[:1].upper() + s[1:] if s else "Scène")

    data, html_scenes = [], []
    for i, s in enumerate(scenes):
        steps, anims = [], []
        for k, b in enumerate(s["beats"]):
            step = beat_to_step(s, b, k)
            html, opts = renderer.render_step(s, step)
            steps.append({"html": html})
            anims.append(anim_meta(opts.get("anim")))
        # Une primitive = une étape, y compris `versus` : ses deux camps sont
        # dans le même bloc HTML, pas dans deux beats séparés.
        zone = "".join('<div class="step">%s</div>' % st["html"] for st in steps)
        used = sorted({f for b in s["beats"] for f in ([b.get("figure")] + (b.get("figures") or [])) if f})
        sources = []
        for f in used:
            src = figs.get(f, {}).get("source")
            if src and src not in sources:
                sources.append(src)
        src = ("Source : " + " · ".join(sources)) if sources else ""
        fond = (('<img class="fond" src="%s" alt=""><div class="voile"></div>' % s["illustration"])
                if s.get("illustration") else "")
        # Punchline : soit une étape `punch` du storyboard (elle a son temps),
        # soit l'ancien bloc final ajouté après les beats.
        has_punch_beat = any((b.get("kind") == "punch") for b in s["beats"])
        has_punch = bool(s.get("punchline")) and not has_punch_beat
        punch_html = ""
        if has_punch:
            punch_html = '<div class="punch"><div class="pt">%s</div></div>' % esc(s["punchline"])
        html_scenes.append(
            '<div class="scene" id="sc-' + str(i) + '">' + fond
            + '<div class="kicker">' + esc(kicker(s["section"])) + '</div>'
            + '<div class="title">' + esc(s["title"]) + '</div>'
            + '<div class="zone">' + zone + '</div>'
            + (('<div class="src">' + esc(src) + '</div>') if src else '')
            + punch_html
            + '</div>')
        memo = [{"n": m["n"], "preview": m["preview"], "notes": m["notes"]} for m in mapping[s["id"]]]
        cues = [b.get("cue") or ("▪ " + (b.get("text") or "")[:40]) for b in s["beats"]]
        if has_punch:
            cues.append("PUNCH")
        data.append({"id": s["id"], "kicker": kicker(s["section"]), "title": s["title"],
                     "steps": anims,
                     "has_punch": has_punch,
                     "cues": cues, "memo": memo,
                     "slides": [m["n"] for m in mapping[s["id"]]]})

    overs = collect_overlays(os.path.join(ROOT, "assets/overlays"))
    page = PAGE.replace("__SCENES__", "\n".join(html_scenes))
    page = page.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    page = page.replace("__OVERS__", json.dumps(overs, ensure_ascii=False))
    page = page.replace("__OVERS_BTN__", "\n".join(
        '      <button id="over-%d">%s</button>' % (k, esc(o["label"])) for k, o in enumerate(overs)))
    open(out_path, "w", encoding="utf-8").write(page)
    nonotes = [(s["id"], [m["n"] for m in mapping[s["id"]] if not m["notes"]]) for s in scenes]
    print("scènes: %d | overlays: %d -> %s" % (len(scenes), len(overs), out_path))
    for sid, sl in nonotes:
        if sl:
            print("  %s : slides sans notes %s" % (sid, sl))

    overs = collect_overlays(os.path.join(ROOT, "assets/overlays"))
    page = PAGE.replace("__SCENES__", "\n".join(html_scenes))
    page = page.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    page = page.replace("__OVERS__", json.dumps(overs, ensure_ascii=False))
    page = page.replace("__OVERS_BTN__", "\n".join(
        '      <button id="over-%d">%s</button>' % (k, esc(o["label"])) for k, o in enumerate(overs)))
    open(out_path, "w", encoding="utf-8").write(page)
    nonotes = [(s["id"], [m["n"] for m in mapping[s["id"]] if not m["notes"]]) for s in scenes]
    print("scènes: %d | overlays: %d -> %s" % (len(scenes), len(overs), out_path))
    for sid, sl in nonotes:
        if sl:
            print("  %s : slides sans notes %s" % (sid, sl))


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("-o") + 1] if "-o" in sys.argv else os.path.join(ROOT, "studio-anim.html")
    build(out)
