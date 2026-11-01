#!/usr/bin/env python3
"""Construit studio-slides.html depuis un fichier Markdown format Advanced Slides (Obsidian).

Usage :
    python3 build_studio_slides.py <slides.md> [-o studio-slides.html] [--assets assets]

Principe (skill hyperframe-joriel) : même coquille studio éprouvée que
le studio.html d'un projet existant (présentation manuelle + prompteur +
webcam coin/plein écran + overlays OBS + enregistrement écran+micro -> webm),
mais la source des slides n'est PLUS SCENES + transcript.json : c'est le
fichier Advanced Slides lui-même.
  - vue présentation : le contenu visible de chaque slide (markdown -> HTML).
  - vue prompteur   : les `note:` de chaque slide (jamais projetées).
  - fragments `<!-- element class="fragment" -->` : révélés pas à pas avec
    Avance/Recule (comme Reveal.js), sans changer de slide.

Dépendances : stdlib uniquement.
"""
import html
import json
import os
import re
import shutil
import sys
import unicodedata

# ---------------------------------------------------------------- parse

FRAG_RE = re.compile(r"<!--\s*element\s+class\s*=\s*[\"']fragment[\"']\s*-->", re.I)
COMMENT_RE = re.compile(r"<!--(.*?)-->", re.S)
IMG_MD_RE = re.compile(r"!\[[^\]]*\]\(\s*([^)\s]+)[^)]*\)")
IMG_DIRECTIVE_RE = re.compile(r"img\s*:\s*(\S+)", re.I)
NOTE_RE = re.compile(r"^\s*note\s*:\s*$", re.I)
SEP_RE = re.compile(r"^\s*---\s*$")


def split_slides(text):
    lines = text.split("\n")
    # frontmatter éventuel : bloc --- ... --- en tête avec des ':'
    start = 0
    front = {}
    if lines and lines[0].strip() == "---":
        for k in range(1, min(len(lines), 40)):
            if lines[k].strip() == "---":
                body = "\n".join(lines[1:k])
                if ":" in body:
                    for ln in body.split("\n"):
                        if ":" in ln:
                            a, b = ln.split(":", 1)
                            front[a.strip()] = b.strip()
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
    chunks = [c for c in (c.strip("\n") for c in chunks) if c.strip()]
    return front, chunks


def split_note(chunk):
    lines = chunk.split("\n")
    for i, ln in enumerate(lines):
        if NOTE_RE.match(ln):
            return "\n".join(lines[:i]).rstrip(), "\n".join(lines[i + 1:]).strip()
    return chunk, ""


def esc(s):
    return html.escape(s, quote=False)


def inline_md(s):
    """**gras**, *italique*, `code` -> HTML (sans toucher au HTML déjà présent)."""
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", s)
    return s


def md_blocks_to_html(content):
    """Convertisseur minimal couvrant le sous-ensemble Advanced Slides utilisé.
    Retourne (html, nfrag, fond_img, labels). Granularité fragment = la ligne
    (comme Reveal.js) : chaque ligne portant `<!-- element class="fragment" -->`
    devient une étape `class="frag" data-fi="k"` (k = 1..nfrag, ordre
    d'apparition). Les lignes sans marqueur restent toujours visibles."""
    # 1. extraire directives проводили
    directives = COMMENT_RE.findall(content)
    fond_img = None
    labels = []
    for d in directives:
        if FRAG_RE.search("<!--%s-->" % d):
            continue
        m = IMG_DIRECTIVE_RE.search(d)
        if m:
            fond_img = m.group(1).strip().strip("\"'")
            continue
        t = d.strip()
        if t:
            labels.append(re.sub(r"\s+", " ", t))
    # 2. image markdown ![..](..) -> fond, retirée du contenu
    m = IMG_MD_RE.search(content)
    if m and not fond_img:
        fond_img = m.group(1)
    content = IMG_MD_RE.sub("", content)

    # 3. découper en unités : une ligne avec marqueur fragment = sa propre unité
    #    (granularité Reveal.js). Les autres lignes se regroupent par blocs.
    units = []  # (text, is_frag)
    buf = []
    for ln in content.split("\n"):
        if FRAG_RE.search(ln):
            if [l for l in buf if l.strip()]:
                units.append(("\n".join(buf), False))
            buf = []
            units.append((FRAG_RE.sub("", ln).strip(), True))
        else:
            buf.append(ln)
    if [l for l in buf if l.strip()]:
        units.append(("\n".join(buf), False))

    frag_counter = 0
    html_parts = []
    for text, is_frag in units:
        text = text.strip("\n")
        if not text.strip():
            continue
        # commentaires restants seuls -> ignorés (labels déjà extraits)
        if COMMENT_RE.sub("", text).strip() == "":
            continue
        frag_attr = ""
        if is_frag:
            frag_counter += 1
            frag_attr = ' class="frag" data-fi="%d"' % frag_counter
        html_parts.append(render_block(text, frag_attr))
    return "\n".join(html_parts), frag_counter, fond_img, labels


def render_block(b, frag_attr):
    # PATCH v3 : le deck 03 utilise des commentaires `<!-- id: X.N -->` en tête de
    # slide ; sans nettoyage, ils fusionnent avec les titres suivants en un bloc
    # multi-lignes qui partait en passthrough brut (affichait `## ...` tel quel).
    s = COMMENT_RE.sub("", b).strip()
    if not s:
        return ""
    # HTML brut (split, small, div, img...) -> passthrough, enveloppé si fragment
    if s.startswith("<"):
        if frag_attr:
            return "<div%s>\n%s\n</div>" % (frag_attr, s)
        return s
    lines = [ln.rstrip() for ln in s.split("\n")]
    # unité fragment : une seule ligne par construction (titre, item ou paragraphe)
    if frag_attr:
        ln = " ".join(ln.strip() for ln in lines if ln.strip())
        m = re.match(r"^(#{1,3})\s+(.*)$", ln)
        if m:
            tag = ("h1", "h2", "h3")[len(m.group(1)) - 1]
            return "<%s%s>%s</%s>" % (tag, frag_attr, inline_md(m.group(2).strip()), tag)
        if re.match(r"^\s*[-*]\s+\S", ln):
            return "<ul%s><li>%s</li></ul>" % (frag_attr, inline_md(re.sub(r"^\s*[-*]\s+", "", ln)))
        if re.match(r"^\s*\d+[.)]\s+\S", ln):
            return "<ol%s><li>%s</li></ol>" % (frag_attr, inline_md(re.sub(r"^\s*\d+[.)]\s+", "", ln)))
        return "<p%s>%s</p>" % (frag_attr, inline_md(ln))
    # bloc multi-lignes : convertir ligne par ligne (titres, listes, paragraphes)
    parts, para, in_list = [], [], None

    def flush_para():
        if para:
            parts.append("<p>%s</p>" % "<br>".join(inline_md(ln) for ln in para))
            para.clear()

    def close_list():
        nonlocal in_list
        if in_list:
            parts.append("</%s>" % in_list)
            in_list = None

    for ln in lines:
        t = ln.strip()
        if not t:
            flush_para()
            close_list()
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", t)
        if m:
            flush_para()
            close_list()
            tag = ("h1", "h2", "h3")[len(m.group(1)) - 1]
            parts.append("<%s>%s</%s>" % (tag, inline_md(m.group(2).strip()), tag))
            continue
        if re.match(r"^[-*]\s+\S", t):
            flush_para()
            if in_list != "ul":
                close_list()
                parts.append("<ul>")
                in_list = "ul"
            parts.append("<li>%s</li>" % inline_md(re.sub(r"^[-*]\s+", "", t)))
            continue
        if re.match(r"^\d+[.)]\s+\S", t):
            flush_para()
            if in_list != "ol":
                close_list()
                parts.append("<ol>")
                in_list = "ol"
            parts.append("<li>%s</li>" % inline_md(re.sub(r"^\d+[.)]\s+", "", t)))
            continue
        close_list()
        para.append(t)
    flush_para()
    close_list()
    return "\n".join(parts)


def clean_title(s):
    """Nettoie un titre/kicker extrait du markdown brut (PATCH v3) : retire les
    commentaires résiduels (`<!-- element class="fragment" -->` sur la même ligne)
    et le formatage inline, pour ne jamais afficher `**` ou `<!-- -->` en brut."""
    s = COMMENT_RE.sub("", s or "")
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"\1", s)
    s = s.replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def plain_preview(content, n=220):
    t = COMMENT_RE.sub(" ", content)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[#*>`\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return (t[:n] + "…") if len(t) > n else t


def parse_slides_file(path):
    text = open(path, encoding="utf-8").read()
    front, chunks = split_slides(text)
    slides = []
    for n, ch in enumerate(chunks, 1):
        content, notes = split_note(ch)
        slide_html, nfrag, fond, labels = md_blocks_to_html(content)
        # kicker : le DERNIER label court (le plus spécifique : ex. sous
        # `<!-- PARTIE 1 -->` + `<!-- I1 : ... -->` on garde "I1 : ..."),
        # sinon premier ### du contenu, sinon première ##, sinon "Slide N".
        # PATCH v3 : ignorer les labels `id: X.N` (identifiants techniques du deck 03).
        kicker = ""
        for lb in reversed(labels):
            if len(lb) < 80 and not re.match(r"(?i)^id\s*:", lb):
                kicker = lb
                break
        if not kicker:
            m = re.search(r"^###\s+(.+)$", content, re.M)
            kicker = clean_title(m.group(1)) if m else ""
        if not kicker:
            m = re.search(r"^##\s+(.+)$", content, re.M)
            kicker = clean_title(m.group(1)) if m else ("Slide %d" % n)
        titre = ""
        m1 = re.search(r"^#\s+(.+)$", content, re.M)
        m2 = re.search(r"^##\s+(.+)$", content, re.M)
        titre = (clean_title(m1.group(1)) if m1 else "") or (clean_title(m2.group(1)) if m2 else "")
        slides.append({
            "n": n,
            "kicker": re.sub(r"\s+", " ", kicker)[:120],
            "titre": re.sub(r"\s+", " ", titre)[:200],
            "html": slide_html,
            "preview": plain_preview(content),
            "notes": notes,
            "img": fond or "",
            "nfrag": nfrag,
            "labels": labels[:4],
        })
    return front, slides


# ---------------------------------------------------------------- overlays

OVERLAY_SRC = os.path.expanduser(os.environ.get("HF_OVERLAYS_DIR", "~/Vidéos/OBS/assets"))
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def slug(nom):
    base, ext = os.path.splitext(nom)
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base.lower()).strip("-")
    return (base or "image") + ext.lower()


def collect_overlays(dst="assets/overlays"):
    overs = []
    if os.path.isdir(OVERLAY_SRC):
        os.makedirs(dst, exist_ok=True)
        for nom in sorted(os.listdir(OVERLAY_SRC)):
            if not nom.lower().endswith(IMG_EXTS):
                continue
            src = os.path.join(OVERLAY_SRC, nom)
            d = os.path.join(dst, slug(nom))
            if (not os.path.exists(d)) or (os.path.getsize(d) != os.path.getsize(src)):
                shutil.copyfile(src, d)
            label = re.sub(r"\s*-\s*kindle\s*$", "", os.path.splitext(nom)[0], flags=re.I)
            overs.append({"label": label, "file": d})
    return overs


# ---------------------------------------------------------------- template

PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Studio Slides — présentation manuelle</title>
<link rel="icon" href="data:,">
<script src="assets/gsap.min.js"></script>
<!-- source: __SOURCE__ | __NSLIDES__ slides | front: __FRONT__ -->
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { width: 100%; height: 100%; overflow: hidden; background: #000; font-family: sans-serif; }
  #present { position: fixed; inset: 0; background: #0d1117; cursor: none; }
  #present .slide { position: absolute; inset: 0; overflow: hidden; opacity: 0; display: flex; align-items: center; justify-content: center; }
  #present .photo { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; display: block; }
  #present .voile { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,.45), rgba(0,0,0,.72) 80%); }
  #present .contenu { position: relative; z-index: 2; width: 86%; max-height: 88%; overflow: hidden; color: #fff; text-align: center; }
  #present .contenu h1 { font-size: 7.2vh; line-height: 1.06; font-weight: 900; text-shadow: 0 4px 30px rgba(0,0,0,.8); margin-bottom: 2vh; }
  #present .contenu h2 { font-size: 5.4vh; line-height: 1.1; font-weight: 800; color: #fde68a; text-shadow: 0 4px 26px rgba(0,0,0,.8); margin-bottom: 1.6vh; }
  #present .contenu h3 { font-size: 3.4vh; letter-spacing: .18em; text-transform: uppercase; color: #fde68a; margin-bottom: 1.6vh; }
  #present .contenu p { font-size: 3.6vh; line-height: 1.4; margin: 1vh 0; text-shadow: 0 2px 18px rgba(0,0,0,.8); }
  #present .contenu ul, #present .contenu ol { list-style: none; margin: 1.4vh 0; }
  #present .contenu li { font-size: 4vh; font-weight: 700; padding: .8vh 0; border-bottom: 1px solid rgba(255,255,255,.22); }
  #present .contenu small { font-size: 2.2vh; color: #d6d3d1; }
  #present .contenu strong { color: #fde68a; }
  #present .contenu code { background: rgba(255,255,255,.12); padding: .2vh .8vw; border-radius: .5vw; font-size: 3vh; }
  #present .kicker { display: inline-block; font-size: 2vh; letter-spacing: .22em; text-transform: uppercase; color: #fde68a; background: rgba(0,0,0,.55); padding: 1vh 1.4vw; border-radius: .6vw; margin-bottom: 2vh; }
  #present .frag { opacity: 0; }
  #present .fin { position: absolute; inset: 0; background: #000; display: none; z-index: 5; }
  #present .pastille { position: absolute; top: 2vh; right: 2vw; color: rgba(255,255,255,.55); font-size: 2vh; z-index: 6; }
  body.rec #present .pastille { display: none; }
  #present.flou .slide { filter: blur(16px) brightness(.65); transition: filter .45s ease; }
  #present .slide { transition: filter .45s ease; }
  #overlay { position: absolute; inset: 0; z-index: 4; display: none; pointer-events: auto; }
  #overlay img { width: 100%; height: 100%; object-fit: contain; display: block; filter: drop-shadow(0 24px 80px rgba(0,0,0,.65)); }
  #cam { position: absolute; z-index: 4; display: none; object-fit: cover; background: #000; }
  #cam.coin { display: block; top: 4vh; right: 3vw; width: 24vw; aspect-ratio: 16/9; border-radius: 1vw; border: 3px solid rgba(255,255,255,.85); box-shadow: 0 10px 40px rgba(0,0,0,.6); }
  #cam.full { display: block; left: 0; top: 0; width: 100%; height: 100%; }
  #cam.miroir { transform: scaleX(-1); }
  #prompteur { display: none; height: 100vh; background: #111; color: #eee; overflow-y: auto; }
  #prompteur .bar { position: sticky; top: 0; z-index: 10; background: #111; padding: 12px 18px 10px; border-bottom: 1px solid #333; }
  #prompteur .row { display: flex; gap: 8px; margin: 0 0 8px; flex-wrap: wrap; }
  #prompteur .row:last-child { margin-bottom: 0; }
  #prompteur .corps { padding: 14px 18px 18px; }
  #defile .bloc { opacity: .42; padding: 14px 4px 22px; border-bottom: 1px solid #2a2a2a; cursor: pointer; }
  #defile .bloc .b-kick { font-size: 14px; color: #fde68a; letter-spacing: .15em; margin-bottom: 4px; }
  #defile .bloc .b-prev { font-size: 19px; line-height: 1.5; color: #bbb; }
  #defile .bloc .b-notes { font-size: 19px; line-height: 1.5; color: #777; background: #1a1a1a; border-radius: 8px; padding: 10px 12px; margin-top: 8px; white-space: pre-wrap; }
  #defile .bloc.cur { opacity: 1; }
  #defile .bloc.cur .b-notes { font-size: 30px; line-height: 1.55; color: #fff; background: #000; border-radius: 10px; padding: 18px; }
  #defile .bloc.cur .b-prev { font-size: 20px; color: #eee; }
  #defile .bloc .b-frag { font-size: 13px; color: #666; margin-top: 6px; }
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
__SLIDES__
  <div id="overlay"><img id="overImg" alt=""></div>
  <video id="cam" muted playsinline></video>
  <div class="fin" id="pFin"></div>
  <div class="pastille" id="pNum"></div>
</div>
<div id="prompteur">
  <div class="bar">
    <div class="row">
      <button id="bDebut" title="Home">&#124;&#9664; Début</button>
      <button id="bPrev" title="Flèche gauche">&#9664; Recule</button>
      <button id="bNext" class="go" title="Espace / flèche droite">Avance &#9654;</button>
      <button id="bFin" title="Fin">Fin &#9654;&#124;</button>
      <span class="lbl" id="fragLbl"></span>
    </div>
    <div class="row">
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
    <div class="row">
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
var SLIDES = __DATA__;
var OVERS = __OVERS__;
var N = SLIDES.length;
var view = new URLSearchParams(location.search).get("view") || "present";
var idx = 0, frag = 0, fini = false, camMode = "off", mirror = true, overlay = null, recOn = false;

var bc = null;
try { bc = new BroadcastChannel("studio-prompt"); } catch (e) { bc = null; }
function emit() {
  var msg = JSON.stringify({ idx: idx, frag: frag, fini: fini, cam: camMode, mirror: mirror, overlay: overlay, rec: recOn });
  if (bc) { try { bc.postMessage(msg); } catch (e) {} }
  try { localStorage.setItem("studio-prompt", msg); } catch (e) {}
}
function emitRaw(o) {
  var msg = JSON.stringify(o);
  if (bc) { try { bc.postMessage(msg); } catch (e) {} }
  try { localStorage.setItem("studio-prompt", msg); } catch (e) {}
}
function onMsg(msg) {
  var d = null;
  try { d = JSON.parse(msg); } catch (e) { return; }
  if (d.camErr && view === "prompteur") { tickMeta(d.camErr); return; }
  if (d.needSound && view === "prompteur") { pop(false); return; }
  if (!("idx" in d)) return;
  idx = Math.max(0, Math.min(N - 1, d.idx)); fini = !!d.fini;
  frag = Math.max(0, Math.min(SLIDES[idx].nfrag || 0, ("frag" in d) ? d.frag : 0));
  if (view === "present" && d.cam && d.cam !== camMode) applyCam(d.cam, true);
  if (view === "present" && ("mirror" in d) && d.mirror !== mirror) { mirror = !!d.mirror; refreshCamClass(); syncMiroir(); }
  if (view === "present" && ("overlay" in d) && d.overlay !== overlay) applyOverlay(d.overlay, false);
  if (view === "present" && ("rec" in d)) {
    recOn = !!d.rec;
    document.body.classList.toggle("rec", recOn);
  }
  render();
}
if (bc) bc.onmessage = function (ev) { onMsg(ev.data); };
window.addEventListener("storage", function (ev) { if (ev.key === "studio-prompt" && ev.newValue) onMsg(ev.newValue); });

function nfrag() { return SLIDES[idx].nfrag || 0; }
function go(i) { idx = Math.max(0, Math.min(N - 1, i)); frag = 0; fini = false; emit(); render(); }
function avance() {
  if (fini) return;
  if (frag < nfrag()) { frag++; emit(); render(); }
  else if (idx < N - 1) { idx++; frag = 0; emit(); render(); }
}
function recule() {
  if (fini) { fini = false; emit(); render(); return; }
  if (frag > 0) { frag--; emit(); render(); }
  else if (idx > 0) { idx--; frag = SLIDES[idx].nfrag || 0; emit(); render(); }
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

/* Webcam : flux acquis dans la fenêtre présentation (c'est elle qui est capturée) */
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

/* Overlays : plein écran (contain), toggle depuis le prompteur */
var popAudio = null;
function pop(local) {
  try {
    if (!popAudio) { popAudio = new Audio("assets/sfx-pop.wav"); popAudio.volume = 0.5; }
    if (local === false) { popAudio.currentTime = 0; popAudio.play().catch(function () {}); return; }
    popAudio.currentTime = 0;
    popAudio.play().catch(function () { emitRaw({ needSound: true }); });
  } catch (e) { emitRaw({ needSound: true }); }
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

/* Rendu présentation : fond + contenu, fragments jusqu'à `frag` visibles */
function showSlide(i) {
  var slides = document.querySelectorAll("#present .slide");
  for (var s = 0; s < slides.length; s++) {
    slides[s].style.opacity = (s === i) ? 1 : 0;
    slides[s].style.zIndex = (s === i) ? 2 : 1;
  }
  var cur = document.getElementById("slide-" + (i + 1));
  if (!cur) return;
  var frags = cur.querySelectorAll(".frag");
  for (var f = 0; f < frags.length; f++) {
    var fi = parseInt(frags[f].getAttribute("data-fi"), 10) || 0;
    var vis = fi <= frag;
    if (window.gsap && vis && frags[f].style.opacity !== "1") {
      (function (el) { gsap.fromTo(el, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }); })(frags[f]);
    } else if (!window.gsap) {
      frags[f].style.opacity = vis ? 1 : 0;
    } else if (!vis) {
      gsap.set(frags[f], { opacity: 0 });
    } else {
      gsap.set(frags[f], { opacity: 1 });
    }
  }
  if (window.gsap) {
    var ph = cur.querySelector(".photo");
    if (ph) gsap.fromTo(ph, { opacity: 0, scale: 1 }, { opacity: 1, scale: 1.08, duration: 1.2, ease: "power2.out" });
  }
  document.getElementById("pNum").textContent = fini ? "FIN" : (i + 1) + " / " + N + (nfrag() ? " · " + frag + "/" + nfrag() : "");
  document.getElementById("pFin").style.display = fini ? "block" : "none";
}

var scrolledKey = "";
function escHtml(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function buildDefile() {
  var html = "";
  for (var i = 0; i < N; i++) {
    var s = SLIDES[i];
    html += '<div class="bloc" id="bloc-' + i + '" data-i="' + i + '">'
      + '<div class="b-kick">SLIDE ' + (i + 1) + " / " + N + " — " + escHtml(s.kicker)
      + (s.nfrag ? "  [" + s.nfrag + " fragment" + (s.nfrag > 1 ? "s" : "") + "]" : "") + "</div>"
      + '<div class="b-prev">' + escHtml(s.preview) + "</div>"
      + (s.notes ? '<div class="b-notes">' + escHtml(s.notes) + "</div>" : '<div class="b-notes" style="opacity:.5">(pas de notes)</div>')
      + ((i === idx && s.nfrag) ? '<div class="b-frag">fragment ' + frag + "/" + s.nfrag + "</div>" : "")
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
    showSlide(idx);
  } else {
    document.getElementById("present").style.display = "none";
    document.getElementById("prompteur").style.display = "block";
    buildDefile();
    var blocs = document.getElementById("defile").children;
    for (var bi = 0; bi < blocs.length; bi++) blocs[bi].classList.toggle("cur", bi === idx);
    var key = idx + ":" + frag + ":" + fini;
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
    var fl = document.getElementById("fragLbl");
    if (fl) fl.textContent = nfrag() ? ("fragment " + frag + "/" + nfrag()) : "";
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
  window.open(location.pathname + "?view=present", "_blank");
};

/* Enregistrement : capture écran + micro -> webm */
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
  var base = rec ? ("● REC " + fmt(performance.now() - t0rec) + (paused ? " (pause)" : "")) : "Prêt. Slide " + (idx + 1) + "/" + N + (nfrag() ? " · fragment " + frag + "/" + nfrag() : "") + ".";
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


def build(slides_path, out_path, assets_dir="assets"):
    front, slides = parse_slides_file(slides_path)
    overs = collect_overlays(os.path.join(os.path.dirname(os.path.abspath(out_path)), assets_dir, "overlays")
                             if os.path.isabs(assets_dir) or "/" in assets_dir else assets_dir)
    # HTML des slides présentation
    parts = []
    for i, s in enumerate(slides, 1):
        fond = ""
        if s["img"]:
            fond = '<img class="photo" src="%s" alt="">' % esc(s["img"])
        voile = '<div class="voile"></div>' if s["img"] else ""
        parts.append(
            '<div class="slide" id="slide-%d">%s%s<div class="contenu">'
            '<div class="kicker">%s</div>%s</div></div>'
            % (i, fond, voile, esc(s["kicker"]), s["html"]))
    data = [
        {"kicker": s["kicker"], "titre": s["titre"], "preview": s["preview"],
         "notes": s["notes"], "img": s["img"], "nfrag": s["nfrag"]}
        for s in slides
    ]
    page = PAGE.replace("__SLIDES__", "\n".join(parts))
    page = page.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    page = page.replace("__OVERS__", json.dumps(overs, ensure_ascii=False))
    page = page.replace("__OVERS_BTN__", "\n".join(
        '      <button id="over-%d">%s</button>' % (k, esc(o["label"])) for k, o in enumerate(overs)))
    page = page.replace("__SOURCE__", esc(os.path.basename(slides_path)))
    page = page.replace("__NSLIDES__", str(len(slides)))
    page = page.replace("__FRONT__", esc(json.dumps(front, ensure_ascii=False)))
    open(out_path, "w", encoding="utf-8").write(page)
    nfrag_tot = sum(s["nfrag"] for s in slides)
    nonotes = sum(1 for s in slides if not s["notes"])
    print("slides: %d | fragments: %d | sans notes: %d | overlays: %d -> %s"
          % (len(slides), nfrag_tot, nonotes, len(overs), out_path))
    if nonotes:
        print("AVERTISSEMENT: %d slide(s) sans `note:` — le prompteur affichera '(pas de notes)'. IDs: %s"
              % (nonotes, [s["n"] for s in slides if not s["notes"]][:10]))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) > 1 else 1)
    src = sys.argv[1]
    out = "studio-slides.html"
    assets = "assets"
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "-o" and i + 1 < len(args):
            out = args[i + 1]; i += 2
        elif args[i] == "--assets" and i + 1 < len(args):
            assets = args[i + 1]; i += 2
        else:
            i += 1
    build(src, out, assets)
