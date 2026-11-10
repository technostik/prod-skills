#!/usr/bin/env python3
"""Primitives visuelles, rendues une seule fois pour tous les builders.

`build.py` (composition finale) et `build_studio_anim.py` (studio pas à pas)
importent ce module. Une primitive = un `kind` du storyboard, un balisage HTML
et un descripteur d'animation. Le balisage est identique dans les deux sorties :
le studio réutilise donc le CSS de la composition (`style-joriel.css` +
`style-joriel-ext.css`) au lieu d'entretenir une seconde grammaire visuelle.

Aucun texte éditorial n'est écrit ici : les sources, les libellés et les
chiffres viennent du storyboard et des registres (`figures`, `refs`).

Usage :
    from render_primitive import Primitives
    r = Primitives(root, figures, refs)
    html, opts = r.render_step(scene, step)

`opts` :
    class   classe du conteneur (toujours « step »)
    full    la primitive occupe la scène entière (image, ref-card)
    punch   la primitive est une punchline noire
    cols2   la scène est en deux colonnes
    anim    descripteur pour le studio : {"kind": ..., ...}
"""
from __future__ import annotations

import re
from pathlib import Path

import schema_anim

# --------------------------------------------------------------------------- #
# Catalogue
# --------------------------------------------------------------------------- #

# Alias éditoriaux -> kind canonique. Les deux builders partagent cette table,
# donc un alias accepté par le storyboard est rendu de la même façon partout.
ALIASES = {
    "numbers": "count", "number": "count", "bignum": "count",
    "negate": "strike", "causal-chain": "chain", "causal": "chain",
    "list": "enumerate", "cards": "kw", "text": "kw", "claim": "kw",
    "doc-crop": "ref-card", "ref-iframe": "ref-shot", "capture": "ref-shot",
    "source": "ref-card", "branch": "diverge", "threshold": "seuil",
    "diagram": "schema", "graph": "schema",
}

ICONS = {
    "trend-up": '<path d="M3 17l6-6 4 4 8-8"/><path d="M21 7h-6v6"/>',
    "trend-down": '<path d="M3 7l6 6 4-4 8 8"/><path d="M21 17h-6v-6"/>',
    "arrow-r": '<path d="M4 12h16"/><path d="M14 6l6 6-6 6"/>',
    "arrow-down": '<path d="M12 4v16"/><path d="M6 14l6 6 6-6"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "cross": '<path d="M18 6L6 18"/><path d="M6 6l12 12"/>',
    "alert": '<path d="M12 3l9 17H3z"/><path d="M12 9v5"/><path d="M12 17h.01"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "money": '<rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="3"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-4 3-6 6-6s6 2 6 6"/><path d="M17 5a3 3 0 010 6"/><path d="M18 20c0-3-1-5-3-6"/>',
    "building": '<path d="M4 21V5l8-3v19"/><path d="M12 8h8v13"/><path d="M7 8h2M7 12h2M7 16h2M16 12h1M16 16h1"/>',
    "book": '<path d="M4 5a2 2 0 012-2h13v18H6a2 2 0 01-2-2z"/><path d="M8 3v18"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    "lock": '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 018 0v3"/>',
    "code": '<path d="M8 6l-5 6 5 6"/><path d="M16 6l5 6-5 6"/>',
    "brain": '<path d="M9 4a3 3 0 00-3 3 3 3 0 00-2 5 3 3 0 002 5 3 3 0 003 3h1V4z"/><path d="M15 4a3 3 0 013 3 3 3 0 012 5 3 3 0 01-2 5 3 3 0 01-3 3h-1V4z"/>',
}

# --------------------------------------------------------------------------- #
# Incrustation (mode `incrustation`) : un visuel posé SUR la vidéo plein écran
# --------------------------------------------------------------------------- #
# Une ancre est le centre d'un sous-rectangle de l'écran : un coin = le centre d'un quart,
# haut / bas / gauche / droite = le centre d'une moitié, centre = le centre de l'écran.
# Le visuel est rendu comme en plein cadre (même balisage, mêmes classes) dans une scène de
# 1920×1080 réduite par `scale` et centrée dans son sous-rectangle (voir `.ov*` dans CSS_EXT).
# nom canonique -> (classe CSS, échelle). L'échelle est à ajuster ici.
OVERLAY_ANCHORS = {
    "haut-gauche": ("ov-tl", 0.5), "haut-droite": ("ov-tr", 0.5),
    "bas-gauche": ("ov-bl", 0.5), "bas-droite": ("ov-br", 0.5),
    "haut": ("ov-t", 0.5), "bas": ("ov-b", 0.5),
    "gauche": ("ov-l", 0.5), "droite": ("ov-r", 0.5),
    "centre": ("ov-c", 0.75),
}
OVERLAY_SCALE_CLASS = {0.5: "ov-s50", 0.75: "ov-s75", 1.0: "ov-s100"}
# Positions automatiques par défaut : le milieu des deux quarts supérieurs.
OVERLAY_DEFAULTS = ("haut-gauche", "haut-droite")
# Écritures acceptées dans le storyboard (`place:`), sans accents ni casse.
OVERLAY_ALIASES = {
    "tl": "haut-gauche", "hg": "haut-gauche", "coin-haut-gauche": "haut-gauche",
    "coin-superieur-gauche": "haut-gauche", "haut-gauche": "haut-gauche",
    "tr": "haut-droite", "hd": "haut-droite", "coin-haut-droite": "haut-droite",
    "coin-superieur-droite": "haut-droite", "haut-droite": "haut-droite",
    "bl": "bas-gauche", "bg": "bas-gauche", "coin-bas-gauche": "bas-gauche",
    "coin-inferieur-gauche": "bas-gauche", "bas-gauche": "bas-gauche",
    "br": "bas-droite", "bd": "bas-droite", "coin-bas-droite": "bas-droite",
    "coin-inferieur-droite": "bas-droite", "bas-droite": "bas-droite",
    "t": "haut", "haut": "haut", "b": "bas", "bas": "bas",
    "l": "gauche", "gauche": "gauche", "r": "droite", "droite": "droite",
    "c": "centre", "centre": "centre", "milieu": "centre", "plein-centre": "centre",
}
# `kind` lisibles dans un quart d'écran (grands textes, peu d'éléments). Les autres sont refusés
# par build.py : un visuel dense réduit de moitié ne se lit plus.
OVERLAY_KINDS = {"kw", "count", "strike", "enumerate", "stamp", "define", "brand", "chain",
                 "image", "ref-shot", "ref-card"}


# Tous les `kind` rendus par `render_step` (hors alias) : sert au format minuté `[kind]`.
KINDS = {"kw", "punch", "image", "ref-shot", "title", "count", "strike", "chain", "enumerate", "versus",
         "diverge", "seuil", "bars", "compare3", "stamp", "define", "ref-card", "brand", "cols2", "waffle",
         "sources", "schema"}


def canonical_anchor(value):
    """`place:` du storyboard -> nom canonique, ou None si inconnu."""
    key = re.sub(r"[\s_]+", "-", str(value or "").strip().lower())
    key = key.translate(str.maketrans("éèêëàâùûôîï", "eeeeaauuoii"))
    return OVERLAY_ALIASES.get(key)


def overlay_wrap(html, anchor):
    """Enveloppe le balisage d'une primitive dans le sous-rectangle de l'ancre."""
    cls, scale = OVERLAY_ANCHORS[anchor]
    return ('<div class="ov %s %s"><div class="ovstage">%s</div></div>'
            % (cls, OVERLAY_SCALE_CLASS[scale], html))


# Styles des primitives absentes de la démo. Ce bloc est écrit tel quel dans
# `assets/style-joriel-ext.css` par build.py ; le studio le charge aussi.
CSS_EXT = """
/* ------------------------------------------------------------------ *
 * style-joriel-ext.css — primitives absentes de la démo.
 * Fichier généré par scripts/build.py ; ne pas éditer à la main.
 * ------------------------------------------------------------------ */
/* Barres comparatives (échelle commune, base 100) */
.bars{width:100%;max-width:78vw}
.brow{margin:1.4vh 0;text-align:left}
.blab{font-size:3.4vh;line-height:1.2;color:var(--bleu-clair);margin-bottom:.7vh}
.btrack{height:3.2vh;border-radius:2vh;background:rgba(255,255,255,.09);overflow:hidden}
.bfill{height:100%;width:100%;border-radius:2vh;background:var(--bleu);transform-origin:left center;transform:scaleX(0)}
.bfill.vert{background:var(--vert)}.bfill.rouge{background:var(--rouge)}.bfill.or{background:var(--or)}
.bflab{margin-top:2vh;font-size:3.4vh;color:var(--gris);text-align:center}
/* Seuil : valeur contre repère */
.seuil{width:100%;max-width:78vw}
.srow{display:flex;align-items:baseline;justify-content:center;gap:1.2vw}
.srow .dbig{font-size:23vh}
.seuil .dbig.bad{color:var(--rouge);text-shadow:0 0 6vh var(--halo-rouge),0 .5vh 2.4vh var(--ombre)}
.seuil .dbig.good{color:var(--vert);text-shadow:0 0 6vh var(--halo-vert),0 .5vh 2.4vh var(--ombre)}
.seuil .dbig.neutre{color:var(--or);text-shadow:0 0 6vh var(--halo-or),0 .5vh 2.4vh var(--ombre)}
.spiste{position:relative;height:3.2vh;border-radius:2vh;background:rgba(255,255,255,.09);margin:2.6vh 0 5vh}
.sfill{height:100%;width:100%;border-radius:2vh;background:var(--or);transform-origin:left center;transform:scaleX(0)}
.seuil.bad .sfill{background:var(--rouge)}.seuil.good .sfill{background:var(--vert)}
.stick{position:absolute;top:-1.2vh;bottom:-1.2vh;width:.4vh;background:var(--blanc);opacity:.9}
.stick span{position:absolute;top:100%;left:50%;transform:translateX(-50%);margin-top:1vh;white-space:nowrap;font-size:2.6vh;color:var(--gris)}
/* Compare3 : trois séries hétérogènes */
.compare3{width:100%;max-width:84vw}
.crow{display:flex;align-items:center;gap:2vw;padding:1.5vh 0;border-bottom:.2vh solid rgba(255,255,255,.1);text-align:left}
.crow:last-child{border-bottom:0}
.crow .dico{width:8vh;height:8vh;margin:0}
.c3body{flex:1;min-width:0}
.c3kw{font-size:5.2vh;line-height:1.15;font-weight:800;text-shadow:0 .5vh 2.4vh var(--ombre)}
.c3kw.bleu{color:var(--bleu)}.c3kw.vert{color:var(--vert)}.c3kw.or{color:var(--or)}.c3kw.rouge{color:var(--rouge)}
/* Waffle : proportion sur 100 cases */
.waffle-wrap{width:100%;max-width:78vw;text-align:center}
.waffle{display:grid;grid-template-columns:repeat(20,1fr);gap:.55vh;width:36vw;margin:2vh auto 0}
.waffle span{display:block;aspect-ratio:1;border-radius:.3vh;background:rgba(255,255,255,.1)}
.waffle span.on{background:var(--or)}
/* Sources : bloc neutre, alimenté par les figures ou par `items` */
.sources{text-align:left;max-width:80vw}
.srct{font-size:3.6vh;letter-spacing:.2em;text-transform:uppercase;color:var(--or);margin-bottom:2vh}
.sources .src{font-size:3.4vh;line-height:1.5;color:var(--blanc)}
.sources .snote{font-size:3vh;line-height:1.4;margin-top:2vh;color:var(--bleu-clair)}
/* Marque (logo local, jamais chargé du réseau) */
.brand{height:8vh;width:auto;vertical-align:middle;background:var(--blanc);border-radius:1.2vh;padding:.8vh 1.2vw}
.brand-text{display:inline-block;font-size:4.6vh;font-weight:800;padding:.6vh 1.4vw;border-radius:1vh;background:var(--blanc);color:#111}
/* Schémas animés (kind schema) : un schéma 1920×1080 posé sur la scène, cadré par la caméra GSAP */
.sch-stage{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0}
.sch-svg{position:absolute;left:0;top:0;overflow:visible}
.sch-edge path{fill:none;stroke:var(--c);stroke-width:5;stroke-linecap:round;stroke-dasharray:1}
.sch-edge .sch-head{fill:var(--c);stroke:none}
.sch-edge.plain{--c:#C9D1DC}.sch-edge.bleu{--c:var(--bleu)}.sch-edge.vert{--c:var(--vert)}
.sch-edge.or{--c:var(--or)}.sch-edge.rouge{--c:var(--rouge)}.sch-edge.dim{--c:var(--gris)}
.sch-node{position:absolute;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border:4px solid var(--c);border-radius:26px;background:rgba(6,10,18,.74);color:var(--c);font-weight:800;line-height:1.22;white-space:nowrap;box-shadow:0 0 0 0 rgba(0,0,0,0);text-shadow:0 0 28px var(--halo),0 5px 24px var(--ombre)}
.sch-node.plain{--c:var(--blanc);--halo:rgba(244,246,249,.18)}.sch-node.bleu{--c:var(--bleu);--halo:var(--halo-bleu)}
.sch-node.vert{--c:var(--vert);--halo:var(--halo-vert)}.sch-node.or{--c:var(--or);--halo:var(--halo-or)}
.sch-node.rouge{--c:var(--rouge);--halo:var(--halo-rouge)}.sch-node.dim{--c:var(--gris);--halo:rgba(154,164,178,.2)}
.sch-s{font-weight:400;color:var(--bleu-clair);text-shadow:none;margin-top:8px}
.sch-elab{position:absolute;display:flex;align-items:center;justify-content:center;text-align:center;font-size:32px;color:var(--bleu-clair);background:rgba(0,0,0,.6);border-radius:12px;white-space:nowrap}
/* Caméra (mode webcam) */
.cam-frame{position:absolute;z-index:6;border-radius:1.4vh;overflow:hidden;border:.3vh solid var(--bleu);background:#000;box-shadow:0 1.6vh 5vh rgba(0,0,0,.65)}
.cam-frame video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
/* Cast : wrapper intérieur qui porte le crop (transform GSAP). Positionné : il est le parent de la vidéo ET de l'image que le moteur insère à son côté au rendu. */
.cam-content{position:absolute;inset:0;transform-origin:50% 0}
/* Incrustation : la vidéo est sous les visuels (z-index 2 < .step 4), cadre plein écran, sans habillage. */
.cam-frame.cam-under{z-index:2;left:0;top:0;width:1920px;height:1080px;border:0;border-radius:0;box-shadow:none}
/* Ancres : sous-rectangle de l'écran (px sur 1920×1080) ; la scène réduite y est centrée. */
.ov{position:absolute;overflow:visible}
.ov-tl{left:0;top:0;width:960px;height:540px}.ov-tr{left:960px;top:0;width:960px;height:540px}
.ov-bl{left:0;top:540px;width:960px;height:540px}.ov-br{left:960px;top:540px;width:960px;height:540px}
.ov-t{left:0;top:0;width:1920px;height:540px}.ov-b{left:0;top:540px;width:1920px;height:540px}
.ov-l{left:0;top:0;width:960px;height:1080px}.ov-r{left:960px;top:0;width:960px;height:1080px}
.ov-c{left:0;top:0;width:1920px;height:1080px}
.ovstage{position:absolute;left:50%;top:50%;width:1920px;height:1080px;margin:-540px 0 0 -960px}
.ov-s50 .ovstage{transform:scale(.5)}.ov-s75 .ovstage{transform:scale(.75)}.ov-s100 .ovstage{transform:scale(1)}
/* dans la scène réduite, le contenu est centré sans l'espace réservé au titre, sur un fond sombre translucide */
.ovstage .zone{top:0;bottom:0}
.ovstage .in{background:rgba(6,10,18,.62);border-radius:3vh;padding:3vh 3vw}
/* Statut de source non vérifiée : invisible par défaut, jamais un code à l'écran */
[data-status="verify"]{outline:0}
"""

NUM_RE = re.compile(r"([+\-−]?)\s*(\d[\d\s\u00a0\u202f]*(?:[.,]\d+)?)\s*(.*)$")


# --------------------------------------------------------------------------- #
# Petits utilitaires partagés
# --------------------------------------------------------------------------- #

def esc(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def as_blocks(v):
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return v
    return [v]


def to_float(v, default=0.0):
    try:
        return float(re.sub(r"[^\d.\-]", "", str(v).replace(",", ".")) or default)
    except (TypeError, ValueError):
        return default


def num_parts(value):
    """('≈ +', '3', ' h') depuis '≈ 3 h' ; (None, None, value) si non numérique."""
    m = NUM_RE.search(str(value or ""))
    if not m:
        return None, None, str(value or "")
    before = str(value)[:m.start()]
    sign = m.group(1).replace("−", "-")
    digits = re.sub(r"[\s\u00a0\u202f]", "", m.group(2)).replace(",", ".")
    after = m.group(3)
    prefix = (before + sign).strip()
    return prefix, digits, after.strip()


def canonical(kind):
    k = str(kind or "kw").strip().lower()
    return ALIASES.get(k, k)


def slug_id(value):
    return re.sub(r"[^A-Za-z0-9_-]+", "-", str(value))


# --------------------------------------------------------------------------- #
# Renderer
# --------------------------------------------------------------------------- #

class Primitives:
    """Rend une étape de storyboard en HTML + descripteur d'animation."""

    def __init__(self, root, figures, refs, schemas=None):
        self.root = Path(root)
        self.figures = figures or {}
        self.refs = refs or {}
        self.schemas = schemas or {}      # registre §1c : {Dxx: schema_anim.Schema}
        self._schema_shown = {}           # éléments déjà montrés, par schéma (d'un groupe au suivant)
        self.warnings = []

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    def figure(self, fid):
        fid = str(fid or "").strip()
        if fid and fid not in self.figures:
            self.warn("figure absente du registre §1 : %s" % fid)
        return self.figures.get(fid, {})

    def ref(self, rid):
        rid = str(rid or "").strip()
        if rid and rid not in self.refs:
            self.warn("référence absente du registre §1b : %s" % rid)
        return self.refs.get(rid, {})

    # -- blocs ---------------------------------------------------------------
    def icon(self, name, cls=""):
        path = ICONS.get(str(name or "").strip(), ICONS["target"])
        return ('<span class="dico %s"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">%s</svg></span>'
                % (esc(cls), path))

    def chip(self, val):
        if re.fullmatch(r"F\d+", str(val or "")):
            f = self.figure(val)
            val = f.get("value", val)
        return '<span class="chip">%s</span>' % esc(val)

    def span(self, b):
        """Un bloc inline -> HTML (sans gérer les sauts de ligne)."""
        if not isinstance(b, dict):
            return esc(b)
        cls = esc(b.get("cls", "plain"))
        if "kw" in b:
            return '<span class="dkw %s">%s</span>' % (cls, esc(b["kw"]))
        if "arrow" in b or "darr" in b:
            return '<span class="darr">%s</span>' % esc(b.get("arrow") or b.get("darr") or "→")
        if "strike" in b:
            return self.strike(b["strike"])
        if "icon" in b:
            kind = "good" if b.get("cls") == "vert" else ("bad" if b.get("cls") == "rouge" else "")
            return self.icon(b["icon"], kind)
        if "check" in b:
            return self.icon("check", "good")
        if "cross" in b:
            return self.icon("cross", "bad")
        if "brand" in b:
            return self.brand(b["brand"])
        if "chip" in b:
            return self.chip(b["chip"])
        if "stamp" in b:
            return '<span class="stamp %s">%s</span>' % (esc(b.get("cls", "or")), esc(b["stamp"]))
        if "bignum" in b:
            return '<span class="dbig or">%s</span>' % esc(b["bignum"])
        if "text" in b:
            return esc(b["text"])
        return ""

    def strike(self, text):
        return ('<span class="dstrike" data-layout-allow-occlusion=""><span data-layout-allow-occlusion="">%s</span>'
                '<span class="sline1" data-layout-allow-occlusion=""></span>'
                '<span class="sline2" data-layout-allow-occlusion=""></span></span>' % esc(text))

    def brand(self, name):
        p = self.root / "assets" / "brands" / (str(name) + ".svg")
        if p.exists():
            return '<img class="brand" src="assets/brands/%s.svg" alt="%s">' % (esc(name), esc(name))
        self.warn("logo absent : assets/brands/%s.svg" % name)
        return '<span class="brand-text">%s</span>' % esc(name)

    def blocks(self, blocks):
        out, line = [], []
        for b in blocks or []:
            if isinstance(b, str):
                line.append(esc(b))
                continue
            if not isinstance(b, dict):
                continue
            if "sub" in b:
                if line:
                    out.append('<div class="dline">%s</div>' % "".join(line))
                    line = []
                out.append('<div class="dsub">%s</div>' % esc(b["sub"]))
                continue
            if b.get("nl") or b.get("br"):
                if line:
                    out.append('<div class="dline">%s</div>' % "".join(line))
                    line = []
                continue
            line.append(self.span(b))
        if line:
            out.append('<div class="dline">%s</div>' % "".join(line))
        return "".join(out)

    def col(self, items):
        return self.blocks(items)

    # -- schémas animés ------------------------------------------------------
    def schema_of(self, step):
        """Schéma d'une étape `kind: schema` : `_schema` (hérité de l'étape précédente par build.py)
        ou `schema:` de l'étape. None si absent du registre §1c."""
        sid = str(step.get("_schema") or (step.get("params") or {}).get("schema") or "").strip()
        sch = self.schemas.get(sid)
        if sch is None:
            self.warn("schéma absent du registre §1c : %s (étape %s)" % (sid or "—", step.get("id", "")))
        return sch

    def schema_group(self, scene, items, cam_frame=None, sel=None):
        """Étapes consécutives d'un même schéma -> {"inner", "js", "warnings"} pour UN clip.

        `items` : [{"step": step, "rel": temps relatif à la scène, "camera": état webcam}].
        La persistance (éléments déjà montrés) passe d'un groupe au suivant du même schéma."""
        first = items[0]["step"]
        sch = self.schema_of(first)
        if sch is None:
            return None
        uid = "sch-" + slug_id(first.get("id") or "")
        beats = [{"id": it["step"]["id"], "rel": it["rel"], "params": it["step"].get("params") or {},
                  "camera": it.get("camera"), "legacy_cam": bool(cam_frame)} for it in items]
        out = schema_anim.render_group(sch, uid, beats, carry=self._schema_shown.get(sch.id),
                                       cam_frame=cam_frame, sel=sel)
        self._schema_shown[sch.id] = out["shown"]
        for w in out["warnings"]:
            self.warn(w)
        return out

    # -- primitives ----------------------------------------------------------
    def render_step(self, scene, step):
        """-> (html, opts) ; opts contient aussi le descripteur `anim`."""
        p = dict(step.get("params") or {})
        kind = canonical(p.get("kind") or "kw")
        label = step.get("label") or ""
        figs = list(step.get("figures") or [])
        if p.get("figure"):
            figs = [p["figure"]]
        fig = self.figure(figs[0]) if figs else {}
        pid = slug_id(step.get("id") or "")
        opts = {"class": "step", "full": False, "punch": False,
                "cols2": False, "anim": {"kind": "fade"}}

        def line(html):
            return '<div class="dline">%s</div>' % html

        if kind == "punch":
            opts["punch"] = True
            opts["anim"] = {"kind": "punch"}
            text = str(p.get("text") or label or "")
            words = " ".join('<span class="w">%s</span>' % esc(w) for w in text.split())
            return '<div class="punch-text">%s</div>' % words, opts

        if kind in ("image", "ref-shot"):
            src = p.get("src") or self.ref(p.get("ref", "")).get("file") or ""
            if not src:
                self.warn("image sans source à l'étape %s" % step.get("id", ""))
                src = "assets/bg/BG-00.jpg"
            cls = "ref-shot" if kind == "ref-shot" else "fond"
            opts["full"] = True
            return ('<img class="%s" id="img-%s" src="%s" alt="%s" style="z-index:2">'
                    % (cls, pid, esc(src), esc(label))), opts

        if kind == "schema":
            # Appel isolé (studio pas à pas) : le schéma s'affiche d'un bloc, sans animation.
            # La composition finale passe par `schema_group`, qui garde l'état d'une étape à l'autre.
            opts["full"] = True
            opts["anim"] = {"kind": "schema"}
            sch = self.schema_of(step)
            if sch is None:
                return '<div class="dline"><span class="dkw dim">%s</span></div>' % esc(label), opts
            return schema_anim.render_static(sch, "sch-" + pid, step), opts

        if kind == "title":
            p.setdefault("title", scene.get("title", ""))
            blocks = step.get("blocks") or ([{"kw": label, "cls": p.get("cls", "plain")}] if label else [])
            return self.blocks(blocks), opts

        if kind == "count":
            opts["anim"] = self._count_anim(p, fig)
            return self.render_count(p, fig), opts

        if kind == "strike":
            strike = p.get("strike") or label
            kw = p.get("kw")
            html = self.strike(strike)
            if kw:
                html += ' <span class="dkw %s">%s</span>' % (esc(p.get("cls", "vert")), esc(kw))
            return line(html), opts

        if kind == "chain":
            blocks = as_blocks(step.get("blocks")) or [{"kw": label}]
            return self.blocks(blocks), opts

        if kind == "enumerate":
            opts["anim"] = {"kind": "slide"}
            items = as_blocks(p.get("items") or step.get("blocks") or [{"kw": label}])
            try:
                upto = int(p.get("index") or len(items))
            except (TypeError, ValueError):
                upto = len(items)
            upto = max(1, min(upto, len(items)))
            out = []
            for i, it in enumerate(items[:upto]):
                it = it if isinstance(it, dict) else {"kw": str(it)}
                cls = " new" if i == upto - 1 else ""
                body = self.blocks([{"kw": it.get("kw", ""), "cls": it.get("cls", "plain")}]
                                   + ([{"sub": it["sub"]}] if it.get("sub") else []))
                out.append('<div class="it%s">%s</div>' % (cls, body))
            return "".join(out), opts

        if kind == "spotlight":
            # Liste affichée en entier, tous les items de la même couleur, chacun mis
            # en relief tour à tour (zoom temporaire) au fil de l'étape. À la différence
            # d'`enumerate`, rien n'est grisé et aucun item n'est désigné « nouveau ».
            opts["anim"] = {"kind": "spotlight"}
            items = as_blocks(p.get("items") or step.get("blocks") or [{"kw": label}])
            cls = esc(p.get("cls") or "bleu")
            out = []
            for it in items:
                it = it if isinstance(it, dict) else {"kw": str(it)}
                body = self.blocks([{"kw": it.get("kw", ""), "cls": cls}]
                                   + ([{"sub": it["sub"]}] if it.get("sub") else []))
                out.append('<div class="it">%s</div>' % body)
            return '<div class="spot">%s</div>' % "".join(out), opts

        if kind == "versus":
            opts["anim"] = {"kind": "versus"}
            left = as_blocks(p.get("left")) or [{"kw": label, "cls": "dim"}]
            right = as_blocks(p.get("right"))
            return ('<div class="versus"><div class="vcol left">%s</div><div class="vsep"></div>'
                    '<div class="vcol right">%s</div></div>' % (self.col(left), self.col(right))), opts

        if kind == "diverge":
            up = p.get("up") or {}
            down = p.get("down") or {}
            return ('<div class="diverge"><div class="trunk">%s</div><div class="branches">'
                    '<div class="branch up"><div class="darr-big">↗</div>%s</div>'
                    '<div class="branch down"><div class="darr-big">↘</div>%s</div></div></div>'
                    % (esc(p.get("trunk", "")), self.col(as_blocks(up)), self.col(as_blocks(down)))), opts

        if kind == "seuil":
            opts["anim"] = {"kind": "seuil"}
            return self.render_seuil(p, fig), opts

        if kind == "bars":
            opts["anim"] = {"kind": "bars"}
            return self.render_bars(p), opts

        if kind == "compare3":
            return self.render_compare3(p), opts

        if kind == "stamp":
            return line('<span class="stamp %s">%s</span>' % (esc(p.get("cls", "or")), esc(p.get("stamp") or label))), opts

        if kind == "define":
            body = line('<span class="dkw plain">%s</span>' % esc(p.get("kw") or label))
            if p.get("sub"):
                body += '<div class="dsub">%s</div>' % esc(p["sub"])
            return body, opts

        if kind == "ref-card":
            opts["full"] = True
            opts["anim"] = {"kind": "ref-card"}
            return self.render_ref_card(p, step), opts

        if kind == "brand":
            return line(self.brand(p.get("brand") or label)), opts

        if kind == "cols2":
            opts["cols2"] = True
            return self.blocks(step.get("blocks") or [{"kw": label}]), opts

        if kind == "waffle":
            opts["anim"] = {"kind": "waffle"}
            return self.render_waffle(p, fig), opts

        if kind == "sources":
            return self.render_sources(p, step), opts

        # kw (défaut) : blocks, sinon libellé
        blocks = step.get("blocks") or []
        if not blocks:
            blocks = [{"kw": label or "…", "cls": p.get("cls", "plain")}]
            if p.get("sub"):
                blocks.append({"sub": p["sub"]})
        opts["anim"] = {"kind": "slide" if len(label) >= 120 else "fade"}
        return self.blocks(blocks), opts

    # Alias de compatibilité pour les anciens appels.
    def step(self, scene, step):
        return self.render_step(scene, step)

    def _count_anim(self, p, fig):
        value = str(p.get("value") or fig.get("value") or "")
        prefix, number, suffix = num_parts(value)
        if p.get("prefix") is not None and str(p["prefix"]) != "":
            prefix = str(p["prefix"])
        if p.get("suffix") is not None and str(p["suffix"]) != "":
            suffix = str(p["suffix"])
        dec = len(number.split(".")[1]) if number and "." in number else 0
        try:
            target = float(number) if number is not None else 0.0
        except (TypeError, ValueError):
            target = 0.0
        return {"kind": "count", "to": target, "prefix": prefix or "",
                "suffix": suffix or "", "dec": dec}

    def render_count(self, p, fig):
        value = str(p.get("value") or fig.get("value") or "")
        prefix, number, suffix = num_parts(value)
        if p.get("prefix") is not None and str(p["prefix"]) != "":
            prefix = str(p["prefix"])
        if p.get("suffix") is not None and str(p["suffix"]) != "":
            suffix = str(p["suffix"])
        prefix = prefix or ""
        suffix = suffix or ""
        label = p.get("label") or fig.get("label") or ""
        status = ' data-status="%s"' % fig.get("status") if fig.get("status") else ""
        if number is not None:
            dec = len(number.split(".")[1]) if "." in number else 0
            ctr = ('<span class="ctr" data-target="%s" data-dec="%d">%s</span>'
                   % (esc(number), dec, "0" if dec == 0 else "0," + "0" * dec))
            body = '<span class="dbig or"%s>%s%s%s</span>' % (status, esc(prefix), ctr, esc(suffix))
        else:
            body = '<span class="dbig or"%s>%s</span>' % (status, esc(value))
        html = '<div class="dline">%s</div>' % body
        if label:
            html += '<div class="dsub">%s</div>' % esc(label)
        return html

    def render_seuil(self, p, fig):
        sens = str(p.get("sens", "neutre")).lower()
        sens = sens if sens in ("good", "bad", "neutre") else "neutre"
        prefix, number, suffix = num_parts(str(p.get("value") or fig.get("value") or ""))
        if p.get("prefix") is not None and str(p["prefix"]) != "":
            prefix = str(p["prefix"])
        if p.get("suffix") is not None and str(p["suffix"]) != "":
            suffix = str(p["suffix"]) or suffix
        try:
            val = float(number) if number is not None else 0.0
        except (TypeError, ValueError):
            val = 0.0
        try:
            rep = float(p.get("repere_val") or 0)
        except (TypeError, ValueError):
            rep = 0.0
        scale = max(val, rep) * 1.06 or 1.0
        pct = max(0.0, min(100.0, val / scale * 100))
        rpct = max(0.0, min(100.0, rep / scale * 100))
        label = p.get("label") or fig.get("label") or ""
        dec = len(number.split(".")[1]) if number and "." in number else 0
        ctr = ('<span class="ctr" data-target="%s" data-dec="%d">0</span>'
               % (esc(number or val), dec)) if number is not None else esc(str(val))
        html = ['<div class="seuil %s">' % sens,
                '<div class="srow"><span class="dbig %s">%s%s%s</span></div>' % (
                    sens, esc(prefix or ""), ctr, esc(suffix or "")),
                '<div class="spiste"><div class="sfill" data-w="%.1f"></div>'
                '<div class="stick" style="left:%.1f%%"><span>%s</span></div></div>'
                % (pct, rpct, esc(p.get("repere", "")))]
        if label or p.get("sub"):
            html.append('<div class="dsub">%s</div>' % esc(p.get("sub") or label))
        if p.get("verdict"):
            html.append('<div class="dline"><span class="stamp %s">%s</span></div>'
                        % (esc(p.get("cls", sens if sens != "neutre" else "or")), esc(p["verdict"])))
        html.append('</div>')
        return "".join(html)

    def render_bars(self, p):
        items = p.get("items") or []
        try:
            mx = float(p.get("max") or max([to_float(i.get("value", i.get("v", 0))) for i in items] or [1]))
        except (TypeError, ValueError):
            mx = 1.0
        mx = mx or 1.0
        rows = []
        for it in items:
            if not isinstance(it, dict):
                it = {"label": str(it), "value": 0}
            v = to_float(it.get("value", it.get("v", 0)))
            pct = max(0.0, min(100.0, v / mx * 100))
            disp = it.get("display") or str(it.get("value", it.get("v", "")))
            cls = it.get("cls", "bleu")
            rows.append('<div class="brow"><div class="blab">%s — %s</div>'
                        '<div class="btrack"><div class="bfill %s" data-w="%.1f"></div></div></div>'
                        % (esc(it.get("label", "")), esc(disp), esc(cls), pct))
        if p.get("label"):
            rows.append('<div class="bflab">%s</div>' % esc(p["label"]))
        return '<div class="bars">%s</div>' % "".join(rows)

    def render_compare3(self, p):
        rows = []
        for r in p.get("rows") or []:
            cls = esc(r.get("cls", "plain"))
            ico = self.icon(r.get("icon", "arrow-r"),
                            "good" if cls == "vert" else ("bad" if cls == "rouge" else ""))
            sub = '<div class="dsub">%s</div>' % esc(r["sub"]) if r.get("sub") else ""
            rows.append('<div class="crow">%s<div class="c3body"><div class="c3kw %s">%s</div>%s</div></div>'
                        % (ico, cls, esc(r.get("kw", "")), sub))
        if p.get("verdict"):
            rows.append('<div class="dline"><span class="stamp %s">%s</span></div>'
                        % (esc(p.get("cls", "rouge")), esc(p["verdict"])))
        return '<div class="compare3">%s</div>' % "".join(rows)

    def render_ref_card(self, p, step):
        rid = p.get("ref") or (step.get("figures") or [""])[0]
        ref = self.ref(rid)
        source = p.get("source") or ref.get("source") or ""
        file = ref.get("file") or ""
        quote = str(p.get("quote") or "")
        hl = str(p.get("hl") or "")
        if hl and hl in quote:
            quote_html = esc(quote).replace(esc(hl), '<span class="hl">%s</span>' % esc(hl), 1)
        elif "**" in quote:
            quote_html = esc(quote).replace("**", "\x00")
            parts = quote_html.split("\x00")
            quote_html = "".join(
                ('<span class="hl">%s</span>' % x if i % 2 else x) for i, x in enumerate(parts))
        else:
            quote_html = esc(quote)
        url = p.get("url") or source
        url = re.sub(r"^https?://(www\.)?", "", str(url)).rstrip("/")
        bits = ['<div class="ref-card" id="ref-%s">' % slug_id(step.get("id", ""))]
        if source:
            bits.append('<div class="ref-source">%s</div>' % esc(source.split(" · ")[0]))
        if p.get("author"):
            bits.append('<div class="ref-author">%s</div>' % esc(p["author"]))
        if p.get("title"):
            bits.append('<div class="ref-title">%s</div>' % esc(p["title"]))
        if quote:
            bits.append('<div class="ref-quote">« %s »</div>' % quote_html)
        if url:
            bits.append('<div class="ref-url">%s</div>' % esc(url))
        bits.append("</div>")
        if file and p.get("show_file"):
            bits.append('<img class="ref-shot" id="ref-shot-%s" src="%s" alt="">'
                        % (slug_id(step.get("id", "")), esc(file)))
        return "".join(bits)

    def render_waffle(self, p, fig):
        try:
            total = float(p.get("total") or 100)
        except (TypeError, ValueError):
            total = 100.0
        try:
            marked = float(p.get("marked") or 0)
        except (TypeError, ValueError):
            marked = 0.0
        cells = 100
        filled = round(marked / total * cells) if total else 0
        dots = "".join('<span class="%s"></span>' % ("on" if i < filled else "off")
                       for i in range(cells))
        value = p.get("value") or fig.get("value", "")
        label = p.get("label") or fig.get("label", "")
        note = p.get("note") or p.get("sub") or ""
        bits = ['<div class="waffle-wrap">']
        if value:
            bits.append('<div class="dline"><span class="dbig or">%s</span></div>' % esc(value))
        if label:
            bits.append('<div class="dsub">%s</div>' % esc(label))
        bits.append('<div class="waffle">%s</div>' % dots)
        if note:
            bits.append('<div class="dsub">%s</div>' % esc(note))
        bits.append('</div>')
        return "".join(bits)

    def render_sources(self, p, step):
        raw = p.get("items") or p.get("sources") or []
        if isinstance(raw, (str, dict)):
            raw = [raw]
        items = []
        for it in raw:
            if isinstance(it, dict):
                val = it.get("source") or it.get("label") or it.get("kw") or ""
            else:
                val = str(it)
            val = str(val).strip()
            if val and val not in items:
                items.append(val)
        if not items:
            for fid in step.get("figures") or []:
                src = self.figure(fid).get("source")
                if src and src not in items:
                    items.append(src)
        if not items:
            self.warn("sources sans contenu à l'étape %s" % step.get("id", ""))
        note = p.get("note") or p.get("sub") or ""
        bits = ['<div class="sources"><div class="srct">%s</div>'
                % esc(p.get("title") or "Sources")]
        if items:
            bits.append('<div class="src">%s</div>' % " · ".join(esc(i) for i in items))
        if note:
            bits.append('<div class="snote">%s</div>' % esc(note))
        bits.append('</div>')
        return "".join(bits)
