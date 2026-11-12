#!/usr/bin/env python3
"""Schémas Excalidraw : un fichier `.excalidraw` dessiné, validé et retouché à la main, puis animé.

Le schéma est un **asset à part** (`assets/schemas/Dxx.excalidraw`) : on le dessine (ou on le génère avec
`schema-to-excalidraw.py`), on le regarde (`excalidraw-preview.py`), on le valide ou on le retouche dans Excalidraw,
et seulement ensuite le storyboard le référence (`fichier:` dans le registre §1c). Les étapes `kind: schema`
le pilotent comme les autres schémas : `show` (apparition), `glow` (relief), `focus` (retrait du reste),
`zoom` (cadrage). Ce module charge le fichier et l'**habille** aux couleurs du thème (joriel) ; l'animation
est celle de `schema_anim.py`, dont `ExSchema` reprend l'interface.

Éléments pris en charge : rectangle, ellipse, losange (avec leur texte), texte libre, flèche et ligne (avec
leur étiquette), trait libre, cadre (`frame`, nommé : sert de groupe). Les imbrications ne coûtent rien : tout est
positionné en coordonnées absolues, et les liens sont dessinés au-dessus de toutes les formes, donc une forme
« dans » une autre ne gêne jamais un lien.

Habillage : les couleurs Excalidraw sont rapprochées d'un rôle du thème (`plain`, `bleu`, `vert`, `or`, `rouge`,
`dim`), la police est celle de la vidéo, le trait est net (pas de rendu « crayonné »), le schéma est mis à
l'échelle de l'écran 1920×1080. Les polices Excalidraw et la rugosité sont ignorées.

Références (dans les étapes) : le **texte** d'un élément (insensible à la casse), `a>b` pour un lien entre deux
éléments (par leurs textes), l'identifiant Excalidraw d'un élément, `@nom` pour un cadre nommé ou pour une forme
et tout ce qu'elle contient, `all`.

Ce module est pur : il ne lit que le fichier qu'on lui donne.
"""
from __future__ import annotations

import colorsys
import json
import math
import re
from pathlib import Path

import schema_anim as sa
from schema_anim import (COLORS, EDGE_COLORS, GRID, H, HALOS, HEAD_LEN, LABEL_H, LABEL_PX, W, Schema, SchemaError,
                         _esc, _key, _pid, text_width, wrap)

SHAPES = ("rectangle", "ellipse", "diamond")
EDGES = ("arrow", "line")
PAD = 64                 # marge autour du schéma mis à l'échelle
MAX_SCALE = 3.0          # un petit dessin n'est pas agrandi au-delà
MIN_FONT = 30            # au-dessous, le texte n'est pas lisible à l'écran : avertissement
SHRINK_MIN = 0.55        # un texte trop large pour sa forme rétrécit jusqu'à ce facteur
STROKE = {1: 3.0, 2: 4.5, 4: 6.5}
INSET = {"rectangle": (1.0, 1.0), "ellipse": (0.72, 0.72), "diamond": (0.5, 0.5)}   # zone de texte utile
EDGE_CAP = 8


# --------------------------------------------------------------------------- #
# Couleurs : rapprochement d'une couleur Excalidraw vers un rôle du thème
# --------------------------------------------------------------------------- #

def _rgb(color):
    c = str(color or "").strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{6})([0-9a-f]{2})?", c)
    if m:
        v = m.group(1)
        return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)
    m = re.fullmatch(r"#([0-9a-f]{3})", c)
    if m:
        return tuple(int(ch * 2, 16) for ch in m.group(1))
    return None


def role_of(color, default="plain"):
    """Couleur Excalidraw -> rôle du thème. `transparent` -> None.

    Gris et noirs -> `plain` (blanc sur le fond sombre de la vidéo), gris moyens -> `dim` ; rouges et roses ->
    `rouge` ; oranges et jaunes -> `or` ; verts -> `vert` ; cyans, bleus et violets -> `bleu`."""
    c = str(color or "").strip().lower()
    if c in ("", "transparent"):
        return None
    rgb = _rgb(c)
    if rgb is None:
        return default
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in rgb))
    if s < 0.18:
        return "dim" if 0.35 <= v <= 0.7 else "plain"
    hue = h * 360
    if hue >= 300 or hue < 20:
        return "rouge"
    if hue < 70:
        return "or"
    if hue < 170:
        return "vert"
    return "bleu"


def _rgba(role, alpha):
    r, g, b = _rgb(COLORS[role])
    return "rgba(%d,%d,%d,%.2f)" % (r, g, b, alpha)


# --------------------------------------------------------------------------- #
# Lecture du fichier
# --------------------------------------------------------------------------- #

def read_elements(path):
    """Éléments utiles d'un fichier .excalidraw (objet {"elements": [...]} ou liste). Lève SchemaError."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SchemaError("fichier introuvable : %s" % path)
    except json.JSONDecodeError as exc:
        raise SchemaError("%s n'est pas un JSON valide : %s" % (path, exc))
    els = data.get("elements") if isinstance(data, dict) else data
    if not isinstance(els, list):
        raise SchemaError("%s : pas un fichier Excalidraw (clé `elements` attendue)" % path)
    return [e for e in els if isinstance(e, dict) and not e.get("isDeleted")]


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _label_of(text):
    return " ".join(str(text or "").split())


class ExSchema(Schema):
    """Un schéma Excalidraw habillé, avec l'interface de `schema_anim.Schema` (nœuds, liens, références,
    cadrage) : `compile_beats` et le JS d'animation sont ceux des autres schémas."""

    def __init__(self, sid, title, elements, source=""):       # noqa: super().__init__ volontairement non appelé
        self.id = sid
        self.title = title or ""
        self.source = source
        self.warnings = []
        self.nodes, self.edges = [], []
        self._nk, self._ek = {}, {}
        self.auto_edges = True
        self.frames = {}
        self._load(elements)
        self._check_layout()

    # -- construction -------------------------------------------------------
    def _load(self, elements):
        elements = [e for e in elements if not e.get("isDeleted")]
        by_id = {e.get("id"): e for e in elements}
        frames = {e["id"]: str(e.get("name") or "").strip() for e in elements if e.get("type") in ("frame", "magicframe")}
        bound = {}                                   # id du conteneur -> texte lié
        for e in elements:
            if e.get("type") == "text" and e.get("containerId") in by_id:
                bound.setdefault(e["containerId"], e)
        # Un texte libre posé en haut d'une forme vide en est le TITRE : la forme prend ce nom (`show: ["La galaxie"]`
        # montre la forme, `@La galaxie` la forme et tout son intérieur).
        adopted = set()
        for sh in elements:
            if sh.get("type") not in SHAPES or sh["id"] in bound:
                continue
            sx, sy, sw_, sh_ = _f(sh.get("x")), _f(sh.get("y")), _f(sh.get("width")), _f(sh.get("height"))
            cands = [t for t in elements if t.get("type") == "text" and t.get("containerId") not in by_id and t["id"] not in adopted
                     and sx - 2 <= _f(t.get("x")) and _f(t.get("x")) + _f(t.get("width")) <= sx + sw_ + 2
                     and sy - 2 <= _f(t.get("y")) and _f(t.get("y")) + _f(t.get("height")) <= sy + sh_ + 2
                     and _f(t.get("y")) + _f(t.get("height")) / 2 <= sy + 0.3 * sh_]
            if cands:
                t = min(cands, key=lambda c: _f(c.get("y")))
                bound[sh["id"]] = dict(t, verticalAlign="top", _title=True)
                adopted.add(t["id"])
        items = []                                   # éléments dessinés, dans l'ordre du fichier (= la profondeur)
        for e in elements:
            t = e.get("type")
            if t in SHAPES or t in EDGES or t == "freedraw":
                items.append(e)
            elif t == "text" and e.get("containerId") not in by_id and e["id"] not in adopted:
                items.append(e)
            elif t in ("image", "embeddable", "iframe"):
                self.warn("élément `%s` ignoré (images et intégrations non prises en charge)" % t)
        if not items:
            raise SchemaError("aucun élément dessiné (rectangle, ellipse, losange, texte, flèche)")

        # mise à l'échelle sur l'écran
        pts = []
        for e in items:
            x, y = _f(e.get("x")), _f(e.get("y"))
            if e.get("type") in EDGES or e.get("type") == "freedraw":
                for p in e.get("points") or [[0, 0]]:
                    pts.append((x + _f(p[0]), y + _f(p[1])))
            else:
                pts += [(x, y), (x + _f(e.get("width")), y + _f(e.get("height")))]
        minx, miny = min(p[0] for p in pts), min(p[1] for p in pts)
        bw, bh = max(p[0] for p in pts) - minx, max(p[1] for p in pts) - miny
        s = min((W - 2 * PAD) / bw if bw > 1 else MAX_SCALE, (H - 2 * PAD) / bh if bh > 1 else MAX_SCALE, MAX_SCALE)
        self.scale = s
        ox = (W - bw * s) / 2 - minx * s
        oy = (H - bh * s) / 2 - miny * s

        def X(v):
            return v * s + ox

        def Y(v):
            return v * s + oy

        # nœuds
        eid_node = {}
        for e in items:
            t = e["type"]
            if t in EDGES:
                continue
            node = self._make_node(e, t, bound.get(e["id"]), frames, X, Y, s)
            if node is not None:
                eid_node[e["id"]] = node
        # liens
        for e in items:
            if e["type"] in EDGES:
                self._make_edge(e, bound.get(e["id"]), eid_node, X, Y, s)
        # groupes par cadre et conteneurs
        for n in self.nodes:
            n["group"] = n.get("group") or ""
        self.frames = {name: [n["id"] for n in self.nodes if n["group"] == name] for name in set(frames.values()) if name}

    def _unique(self, base, eid):
        key = _key(base) if base else ""
        if not base or key in self._nk:
            if base:
                self.warn("deux éléments portent le texte « %s » : le second est désigné par son identifiant `%s`" % (base, eid))
            return eid
        return base

    def _make_node(self, e, t, txt, frames, X, Y, s):
        x, y, w, h = X(_f(e.get("x"))), Y(_f(e.get("y"))), _f(e.get("width")) * s, _f(e.get("height")) * s
        if _f(e.get("angle")):
            self.warn("élément %s : la rotation est ignorée" % e.get("id"))
        role = role_of(e.get("strokeColor")) or "plain"
        node = {"i": len(self.nodes), "eid": e["id"], "kind": t, "cls": role, "fx": "filter",
                "group": frames.get(e.get("frameId"), ""), "opacity": max(0.05, min(1.0, _f(e.get("opacity"), 100) / 100)),
                "sw": STROKE.get(int(_f(e.get("strokeWidth"), 2)), 4.5), "dash": e.get("strokeStyle") in ("dashed", "dotted"),
                "bg": role_of(e.get("backgroundColor")) if e.get("backgroundColor") not in (None, "transparent") else None,
                "round": bool(e.get("roundness")), "lines": [], "fs": 0.0, "valign": "center", "talign": "center"}
        if t == "text":
            raw = str(e.get("originalText") or e.get("text") or "")
            fs = max(1.0, _f(e.get("fontSize"), 20)) * s
            lines = raw.split("\n")
            need = max([text_width(l, fs) for l in lines] + [0]) + 8
            ta = e.get("textAlign") or "left"
            if need > w:                                    # la police du thème est plus large : la boîte s'élargit
                x = x if ta == "left" else (x - (need - w) / 2 if ta == "center" else x - (need - w))
                w = need
            node.update(label=_label_of(raw), lines=lines, fs=fs, talign=ta, cx=x + w / 2, cy=y + h / 2, w=w, h=h, x=x, y=y,
                        valign=e.get("verticalAlign") or "top", bg=None)
            if fs < MIN_FONT:
                self.warn("texte « %s » : %.0f px à l'écran, trop petit (≥ %d px) : l'agrandir dans Excalidraw" % (node["label"], fs, MIN_FONT))
        elif t == "freedraw":
            pts = [(X(_f(e.get("x")) + _f(p[0])), Y(_f(e.get("y")) + _f(p[1]))) for p in (e.get("points") or [])]
            if len(pts) < 2:
                return None
            x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
            x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
            node.update(label="", cx=(x0 + x1) / 2, cy=(y0 + y1) / 2, w=max(1.0, x1 - x0), h=max(1.0, y1 - y0), x=x0, y=y0,
                        path=pts)
        else:
            node.update(cx=x + w / 2, cy=y + h / 2, w=w, h=h, x=x, y=y)
            if txt is not None:
                raw = str(txt.get("originalText") or txt.get("text") or "")
                node["label"] = _label_of(raw)
                node["valign"] = txt.get("verticalAlign") or "center"
                node["talign"] = txt.get("textAlign") or "center"
                if txt.get("_title"):                           # titre posé par l'auteur : sa taille et ses retours à la ligne
                    node["lines"], node["fs"] = raw.split("\n"), max(1.0, _f(txt.get("fontSize"), 20)) * s
                    node["title_y"] = Y(_f(txt.get("y"))) - y
                    if node["fs"] < MIN_FONT:
                        self.warn("« %s » : texte de %.0f px à l'écran, trop petit (≥ %d px)" % (node["label"], node["fs"], MIN_FONT))
                else:
                    self._fit_text(node, raw, max(1.0, _f(txt.get("fontSize"), 20)) * s)
            else:
                node["label"] = ""
        label = self._unique(node["label"], e["id"])
        node["id"] = label
        node["id_key"] = _key(label)
        self.nodes.append(node)
        self._nk[_key(label)] = node
        self._nk.setdefault(_key(e["id"]), node)
        return node

    def _fit_text(self, node, raw, fs0):
        """Coupe le texte d'une forme à sa zone utile, et le rétrécit s'il ne tient pas.

        La largeur utile dépend de la hauteur du bloc de texte : dans un losange ou une ellipse, une ligne unique
        peut presque toucher les bords latéraux, trois lignes beaucoup moins."""
        kind, w, h = node["kind"], node["w"], node["h"]
        pad_x, pad_y = max(10.0, min(0.08 * w, 36.0)), max(6.0, min(0.06 * h, 20.0))
        max_h = (h - 2 * pad_y) if kind == "rectangle" else 0.82 * h

        def avail_w(block_h):
            r = min(0.98, block_h / h)
            f = 1.0 if kind == "rectangle" else (1 - r if kind == "diamond" else math.sqrt(1 - r * r))
            return max(20.0, w * f - 2 * pad_x)

        fs = fs0
        while True:
            lines = [x for para in raw.split("\n") for x in wrap(para.strip(), fs, max(20.0, w - 2 * pad_x))]
            block = len(lines) * fs * 1.22
            lw = max([text_width(l, fs) for l in lines] + [0])
            if (lw <= avail_w(block) and block <= max_h) or fs <= fs0 * SHRINK_MIN:
                break
            fs *= 0.93
        node["lines"], node["fs"] = lines, fs
        if lw > avail_w(block) * 1.02 or block > max_h * 1.02:
            self.warn("« %s » ne tient pas dans sa forme même rétréci (%.0f px) : agrandir la forme dans Excalidraw"
                      % (node["label"], fs))
        if fs < MIN_FONT:
            self.warn("« %s » : texte de %.0f px à l'écran, trop petit (≥ %d px) : agrandir le texte dans Excalidraw, ou "
                      "réduire la taille du schéma" % (node["label"], fs, MIN_FONT))

    def _make_edge(self, e, txt, eid_node, X, Y, s):
        raw = e.get("points") or []
        if len(raw) < 2:
            return
        x0, y0 = _f(e.get("x")), _f(e.get("y"))
        pts = [(X(x0 + _f(p[0])), Y(y0 + _f(p[1]))) for p in raw]

        def bound(k):
            b = e.get(k)
            return eid_node.get(b.get("elementId")) if isinstance(b, dict) else None

        a, b = bound("startBinding"), bound("endBinding")
        a = a or self._nearest(pts[0], exclude=None)
        b = b or self._nearest(pts[-1], exclude=None)
        if a is not None and a is b and len(pts) <= 2:
            a = b = None                                        # une flèche qui part et arrive sur la même forme n'en relie pas deux
        role = role_of(e.get("strokeColor")) or "plain"
        smooth = bool(e.get("roundness")) and len(pts) > 2 and not e.get("elbowed")
        d, ends = self._path(pts, smooth)
        heads = []
        want = {"start": e.get("startArrowhead") if e["type"] == "arrow" else None,
                "end": e.get("endArrowhead", "arrow") if e["type"] == "arrow" else None}
        shortened = list(pts)
        if want["end"]:
            heads.append(Schema._head(pts[-1], ends["end"]))
            shortened[-1] = Schema._back(pts[-1], ends["end"], HEAD_LEN * 0.8)
        if want["start"]:
            heads.append(Schema._head(pts[0], ends["start"]))
            shortened[0] = Schema._back(pts[0], ends["start"], HEAD_LEN * 0.8)
        d, _ = self._path(shortened, smooth)
        mid = pts[len(pts) // 2] if len(pts) % 2 else ((pts[len(pts) // 2 - 1][0] + pts[len(pts) // 2][0]) / 2,
                                                       (pts[len(pts) // 2 - 1][1] + pts[len(pts) // 2][1]) / 2)
        label = _label_of((txt or {}).get("originalText") or (txt or {}).get("text")) if txt else ""
        lab_w = int(math.ceil(text_width(label, LABEL_PX, bold=False))) + 28 if label else 0
        label_at = mid
        if txt:
            label_at = (X(_f(txt.get("x")) + _f(txt.get("width")) / 2), Y(_f(txt.get("y")) + _f(txt.get("height")) / 2))
        eid = (a["id"] + ">" + b["id"]) if (a is not None and b is not None) else (label or e["id"])
        if _key(eid) in self._ek:
            eid = e["id"]
        edge = {"id": eid, "i": len(self.edges), "eid": e["id"], "a": a, "b": b, "cls": role, "dir": "->", "label": label,
                "curve": 0.0, "manual": a is None or b is None, "dash": False, "sw": STROKE.get(int(_f(e.get("strokeWidth"), 2)), 4.5),
                "geo": {"d": d, "heads": heads, "mid": mid, "label_at": label_at, "label_w": lab_w,
                        "pts": list(pts) + ([(label_at[0] - lab_w / 2, label_at[1] - LABEL_H / 2),
                                             (label_at[0] + lab_w / 2, label_at[1] + LABEL_H / 2)] if label else [])}}
        self.edges.append(edge)
        self._ek[_key(eid)] = edge
        self._ek.setdefault(_key(e["id"]), edge)
        if label:
            self._ek.setdefault(_key(label), edge)

    @staticmethod
    def _path(pts, smooth):
        """Chemin SVG d'une flèche et tangentes aux deux bouts (de la courbe vers l'extérieur)."""
        n = len(pts)

        def tang(p, q):
            return (p[0] - q[0], p[1] - q[1])

        if not smooth:
            d = "M%.1f %.1f " % pts[0] + " ".join("L%.1f %.1f" % p for p in pts[1:])
            return d, {"start": tang(pts[0], pts[1]), "end": tang(pts[-1], pts[-2])}
        d = "M%.1f %.1f" % pts[0]
        c2_last, c1_first = pts[-2], pts[1]
        for i in range(n - 1):
            p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
            p3 = pts[min(i + 2, n - 1)]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            d += " C%.1f %.1f %.1f %.1f %.1f %.1f" % (c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
            if i == 0:
                c1_first = c1
            if i == n - 2:
                c2_last = c2
        return d, {"start": tang(pts[0], c1_first), "end": tang(pts[-1], c2_last)}

    def _nearest(self, p, exclude):
        """Nœud qui contient (ou frôle) un bout de flèche non lié : relie les flèches dessinées sans accroche."""
        best, best_area = None, None
        for n in self.nodes:
            if n["kind"] == "freedraw" or n["kind"] == "text" and not n["label"]:
                continue
            m = 24.0
            if n["x"] - m <= p[0] <= n["x"] + n["w"] + m and n["y"] - m <= p[1] <= n["y"] + n["h"] + m:
                area = n["w"] * n["h"]
                if best is None or area < best_area:
                    best, best_area = n, area
        return best

    def _check_layout(self):
        for n in self.nodes:
            x0, y0, x1, y1 = self.rect(n)
            if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
                self.warn("« %s » dépasse de l'écran" % (n["label"] or n["id"]))

    # -- références ----------------------------------------------------------
    def resolve(self, spec):
        if spec in (None, "", False):
            return [], [], []
        items = list(re.split(r"[,;]", spec)) if isinstance(spec, str) else list(spec)
        nodes, edges, unknown = [], [], []
        for raw in items:
            ref = str(raw).strip()
            if not ref:
                continue
            n, e, u = Schema.resolve(self, [ref])
            if u and ref.startswith("@"):
                n, e, u = self._contained(ref[1:])
            for x in n:
                if x not in nodes:
                    nodes.append(x)
            for x in e:
                if x not in edges:
                    edges.append(x)
            unknown += u
        return nodes, edges, unknown

    def _container_of(self, node):
        """La plus petite forme qui contient `node` (None s'il n'y en a pas)."""
        x0, y0, x1, y1 = self.rect(node)
        best = None
        for c in self.nodes:
            if c is node or c["kind"] not in SHAPES or c["w"] * c["h"] <= node["w"] * node["h"]:
                continue
            a0, b0, a1, b1 = self.rect(c)
            if a0 <= x0 + 3 and b0 <= y0 + 3 and a1 >= x1 - 3 and b1 >= y1 - 3:
                if best is None or c["w"] * c["h"] < best["w"] * best["h"]:
                    best = c
        return best

    def _contained(self, name):
        """`@Forme` : la forme et tout ce qu'elle contient (formes, textes, liens dont les deux bouts sont dedans)."""
        box = self._nk.get(_key(name))
        if box is not None and box["kind"] == "text":            # un titre libre posé dans une forme désigne cette forme
            box = self._container_of(box)
        if box is None or box["kind"] not in SHAPES:
            return [], [], ["@" + name]
        x0, y0, x1, y1 = self.rect(box)
        tol = 3.0
        inside = [box]
        for n in self.nodes:
            if n is box:
                continue
            a0, b0, a1, b1 = self.rect(n)
            if a0 >= x0 - tol and b0 >= y0 - tol and a1 <= x1 + tol and b1 <= y1 + tol and n["w"] * n["h"] < box["w"] * box["h"]:
                inside.append(n)
        edges = []
        for e in self.edges:
            ends = [e["a"], e["b"]]
            if all(x is not None and x in inside for x in ends):
                edges.append(e)
            elif e["a"] is None and e["b"] is None and all(x0 - tol <= p[0] <= x1 + tol and y0 - tol <= p[1] <= y1 + tol
                                                           for p in e["geo"]["pts"][:2]):
                edges.append(e)
        return inside, edges, []

    # -- balisage -------------------------------------------------------------
    def stage_html(self, uid, shown, hidden_until_shown=True):
        """Le schéma (`.sch-stage`) : formes, puis liens AU-DESSUS (ils ne sont pas gênés par les imbrications), puis
        étiquettes de liens. Un élément pas encore montré est caché en ligne."""
        def vis(key):
            return key in shown or not hidden_until_shown

        out = ['<div class="sch-stage" id="%s-stage">' % uid]
        for n in self.nodes:
            out.append(self._node_html(n, uid, vis(("n", n["i"]))))
        out.append('<svg class="sch-svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H))
        for e in self.edges:
            v = vis(("e", e["i"]))
            gid = _pid(uid, "e", e["i"])
            out.append('<g class="sch-edge %s" id="%s">' % (e["cls"], gid))
            out.append('<path id="%s-p" d="%s" pathLength="1" style="stroke-dashoffset:%d;stroke-width:%.1f"/>'
                       % (gid, e["geo"]["d"], 0 if v else 1, e["sw"]))
            for h, pts in enumerate(e["geo"]["heads"]):
                out.append('<polygon class="sch-head" id="%s-h%d" points="%s"%s/>' % (gid, h, pts, "" if v else ' style="opacity:0"'))
            out.append("</g>")
        out.append("</svg>")
        for e in self.edges:
            if not e["label"]:
                continue
            lw, lh = e["geo"]["label_w"], LABEL_H
            mx, my = e["geo"]["label_at"]
            out.append('<div class="sch-elab" id="%s" style="left:%.1fpx;top:%.1fpx;width:%dpx;height:%dpx%s">%s</div>'
                       % (_pid(uid, "l", e["i"]), mx - lw / 2, my - lh / 2, lw, lh,
                          "" if vis(("e", e["i"])) else ";opacity:0", _esc(e["label"])))
        out.append("</div>")
        return "".join(out)

    def _node_html(self, n, uid, visible):
        w, h = n["w"], n["h"]
        role = n["cls"]
        hide = "" if visible else ";opacity:0"
        base = ('id="%s" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;filter:drop-shadow(0 0 0 rgba(0,0,0,0))%s"'
                % (_pid(uid, "n", n["i"]), n["x"], n["y"], w, h, hide))
        kind = n["kind"]
        if kind == "text":
            body = "<br>".join(_esc(l) for l in n["lines"])
            jc = {"top": "flex-start", "middle": "center", "bottom": "flex-end"}.get(n["valign"], "flex-start")
            al = {"left": "flex-start", "center": "center", "right": "flex-end"}.get(n["talign"], "flex-start")
            return ('<div class="exn exn-text %s" %s><div class="exn-t" style="font-size:%.1fpx;justify-content:%s;align-items:%s;'
                    'text-align:%s">%s</div></div>' % (role, base, n["fs"], jc, al, n["talign"], body))
        sw = n["sw"]
        stroke = COLORS[role]
        if n["bg"]:
            fill = _rgba(n["bg"], 0.22)
        else:
            fill = "rgba(6,10,18,.62)" if not self._is_container(n) else "rgba(255,255,255,.025)"
        dash = ' stroke-dasharray="%.0f %.0f"' % (sw * 2.2, sw * 1.6) if n["dash"] else ""
        common = 'fill="%s" stroke="%s" stroke-width="%.1f"%s stroke-linejoin="round"' % (fill, stroke, sw, dash)
        i = sw / 2
        if kind == "freedraw":
            d = "M" + " L".join("%.1f %.1f" % (p[0] - n["x"], p[1] - n["y"]) for p in n["path"])
            shape = '<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round"/>' % (d, stroke, sw)
        elif kind == "ellipse":
            shape = '<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" %s/>' % (w / 2, h / 2, max(1, w / 2 - i), max(1, h / 2 - i), common)
        elif kind == "diamond":
            shape = '<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f" %s/>' % (w / 2, i, w - i, h / 2, w / 2, h - i, i, h / 2, common)
        else:
            rx = min(26.0, 0.16 * min(w, h)) if n["round"] else 6.0
            shape = '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" %s/>' % (i, i, max(1, w - 2 * i), max(1, h - 2 * i), rx, common)
        text = ""
        if n["lines"]:
            jc = {"top": "flex-start", "middle": "center", "bottom": "flex-end"}.get(n["valign"], "center")
            padt = n["title_y"] if "title_y" in n else max(6.0, 0.06 * h)
            text = ('<div class="exn-t" style="font-size:%.1fpx;justify-content:%s;padding:%.1fpx %.1fpx 0">%s</div>'
                    % (n["fs"], jc, max(0.0, padt), max(10.0, 0.08 * w), "<br>".join(_esc(l) for l in n["lines"])) if "title_y" in n else
                    '<div class="exn-t" style="font-size:%.1fpx;justify-content:%s;padding:%.1fpx %.1fpx">%s</div>'
                    % (n["fs"], jc, padt, max(10.0, 0.08 * w), "<br>".join(_esc(l) for l in n["lines"])))
        return ('<div class="exn %s %s" %s><svg class="exn-s" width="%.1f" height="%.1f" viewBox="0 0 %.1f %.1f" style="opacity:%.2f">%s</svg>%s</div>'
                % (role, kind, base, w, h, w, h, n["opacity"], shape, text))

    def _is_container(self, n):
        if "_cont" not in n:
            x0, y0, x1, y1 = self.rect(n)
            n["_cont"] = any(m is not n and m["kind"] in SHAPES + ("text",) and m["w"] * m["h"] < n["w"] * n["h"]
                             and self.rect(m)[0] >= x0 - 3 and self.rect(m)[1] >= y0 - 3 and self.rect(m)[2] <= x1 + 3
                             and self.rect(m)[3] <= y1 + 3 for m in self.nodes)
        return n["_cont"]

    # -- description -----------------------------------------------------------
    def handles(self):
        """Ce qu'on peut nommer dans `show` / `glow` / `focus` / `zoom` : texte lisible, pour le LLM et pour toi."""
        lines = ["Schéma %s — %s%s" % (self.id, self.title or "sans titre", " (%s)" % self.source if self.source else ""),
                 "", "Éléments (références pour `show`, `glow`, `focus`, `zoom`) :"]
        for n in self.nodes:
            label = n["label"] or "(sans texte)"
            tag = "%s, %s" % (n["kind"], n["cls"]) + (", cadre « %s »" % n["group"] if n["group"] else "")
            lines.append("  - %s  [%s]%s" % (n["id"] if n["label"] else n["eid"], tag, "" if n["label"] else "  ← " + label))
        if self.edges:
            lines += ["", "Liens (références `a>b`, ou le texte du lien) :"]
            for e in self.edges:
                ends = "%s → %s" % (e["a"]["id"] if e["a"] else "?", e["b"]["id"] if e["b"] else "?")
                lines.append("  - %s  [%s%s]%s" % (e["id"], ends, ", étiquette « %s »" % e["label"] if e["label"] else "",
                                                    ", libre (à nommer dans `show`)" if e["manual"] else ", apparaît avec ses deux éléments"))
        conts = [n for n in self.nodes if n["kind"] in SHAPES and self._is_container(n)]
        if conts or self.frames:
            lines += ["", "Groupes (`@nom`) :"]
            for name, members in sorted(self.frames.items()):
                lines.append("  - @%s : cadre, contient %s" % (name, ", ".join(members)))
            for n in conts:
                inside, _, _ = self._contained(n["id"] if n["label"] else n["eid"])
                titles = [m["label"] for m in inside if m["kind"] == "text" and m["label"]][:1]
                name = n["id"] if n["label"] else (titles[0] if titles else n["eid"])
                lines.append("  - @%s : forme et ses %d éléments intérieurs" % (name, len(inside) - 1))
        if self.warnings:
            lines += ["", "Avertissements :"] + ["  - " + w for w in self.warnings]
        return "\n".join(lines) + "\n"

    def as_dict(self):
        return {"id": self.id, "title": self.title, "source": self.source, "kind": "excalidraw", "scale": round(self.scale, 3),
                "nodes": [{"id": n["id"], "eid": n["eid"], "shape": n["kind"], "label": n["label"], "cls": n["cls"],
                           "group": n["group"], "x": round(n["x"], 1), "y": round(n["y"], 1), "w": round(n["w"], 1),
                           "h": round(n["h"], 1)} for n in self.nodes],
                "edges": [{"id": e["id"], "from": e["a"]["id"] if e["a"] else None, "to": e["b"]["id"] if e["b"] else None,
                           "label": e["label"], "manual": e["manual"]} for e in self.edges],
                "warnings": list(self.warnings)}


def load_schema(path, sid, title="", root=None):
    """Charge un fichier .excalidraw. `path` est relatif à `root` (le dossier du projet) s'il est donné."""
    p = Path(path)
    if root is not None and not p.is_absolute():
        p = Path(root) / p
    return ExSchema(sid, title, read_elements(p), source=str(path))
