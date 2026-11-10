#!/usr/bin/env python3
"""Schémas animés : la primitive `schema` (skill hyperframe-joriel).

Un schéma est déclaré UNE fois dans le registre §1c du storyboard (un bloc JSON par
schéma : des nœuds posés sur une grille 16×9 et des liens). Les étapes `kind: schema`
ne font ensuite que le piloter : afficher, mettre en relief (`glow`), isoler (`focus`),
cadrer (`zoom`). Le schéma se construit au fil de la voix et garde son état d'une étape
à la suivante, au lieu de repartir de zéro à chaque étape comme les autres primitives.

Ce module est pur : il ne lit ni ne n'écrit aucun fichier. Il fournit

    schemas_from_lines(lines)   -> registre §1c : {Dxx: Schema}, avertissements, erreurs
    Schema                      -> nœuds, liens, géométrie (boîtes, flèches, cadrage)
    render_group(...)           -> HTML du schéma + JS GSAP pour un groupe d'étapes consécutives
    render_static(...)          -> HTML du schéma sans animation (studio pas à pas)

`render_primitive.py` l'appelle ; `build.py` regroupe les étapes consécutives qui portent
le même schéma en UN seul clip (sinon chaque étape serait un clip indépendant, et rien ne
persisterait d'une étape à l'autre).

Aucun texte éditorial n'est écrit ici : tout vient du registre et des étapes du storyboard.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #

W, H = 1920, 1080            # scène, en px
GRID = 120                   # une unité de grille = 120 px (16 × 9 unités)
MARGIN = 24                  # marge de sécurité autour de la scène
DIM = 0.25                   # opacité d'un élément mis en retrait par `focus`
CAM_MARGIN = 110             # marge autour d'une zone cadrée par `zoom`
CAM_MAX = 2.4                # zoom maximal
SIZES = {"s": (40, 28), "m": (52, 32), "l": (68, 38)}   # (px du libellé, px du sous-titre)
PAD_X, PAD_Y, BORDER = 40, 24, 4
WRAP_AT = 720                # largeur au-delà de laquelle un libellé est coupé en lignes
HEAD_LEN, HEAD_HALF = 26, 13  # pointe de flèche
LABEL_PX, LABEL_H = 32, 52   # étiquette d'un lien : corps du texte, hauteur de la pastille
EDGE_GAP = 8                 # écart entre la flèche et la boîte
CLASSES = ("plain", "bleu", "vert", "or", "rouge", "dim")
COLORS = {"plain": "#F4F6F9", "bleu": "#5B9CF6", "vert": "#6FDC8C", "or": "#F0B429",
          "rouge": "#E5484D", "dim": "#9AA4B2"}
EDGE_COLORS = dict(COLORS, plain="#C9D1DC")
HALOS = {"plain": "rgba(244,246,249,.45)", "bleu": "rgba(91,156,246,.75)",
         "vert": "rgba(111,220,140,.70)", "or": "rgba(240,180,41,.75)",
         "rouge": "rgba(229,72,77,.75)", "dim": "rgba(154,164,178,.45)"}
ALL_REFS = {"*", "all", "tout", "tous"}
IDENT = (0.0, 0.0, 1.0)      # caméra au repos : (x, y, échelle)


class SchemaError(ValueError):
    """Schéma inutilisable (JSON invalide, aucun nœud…)."""


# --------------------------------------------------------------------------- #
# Texte : largeur estimée (déterministe, sans police ni navigateur)
# --------------------------------------------------------------------------- #
# La police de la skill est Verdana en gras. On estime la largeur par classes de
# caractères, avec une marge prudente : le résultat ne dépend pas de la machine, donc
# le build reste reproductible. Un texte qui déborde de sa boîte est signalé par le test
# de rendu (Chromium), pas ici.

_NARROW = set("il.,;:'!|`’")
_SMALL = set("frt()[]-–—/\\")


def _char_w(ch):
    base = unicodedata.normalize("NFD", ch)[:1] or ch
    if base in " \u00a0" or base in _NARROW:
        return 0.36
    if base in _SMALL:
        return 0.46
    if base == "m":
        return 0.97
    if base == "w":
        return 0.90
    if base in "MW":
        return 0.98
    if base == "I":
        return 0.52
    if base.isdigit():
        return 0.72
    if base.isupper():
        return 0.78
    if base.isalpha():
        return 0.68
    return 1.0


def text_width(text, px, bold=True):
    """Largeur estimée (px) d'une ligne de texte."""
    total = sum(_char_w(c) for c in str(text)) * px
    return total * (1.0 if bold else 0.9)


def wrap(text, px, max_w=WRAP_AT):
    """Coupe un libellé trop long en lignes (aux espaces). Un `\\n` explicite est conservé."""
    lines = []
    for raw in str(text).split("\n"):
        cur = ""
        for word in raw.split(" "):
            cand = (cur + " " + word).strip() if cur else word
            if cur and text_width(cand, px) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = cand
        lines.append(cur)
    return lines


def _esc(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _key(value):
    """Clé de recherche d'un identifiant : sans espaces autour, sans casse."""
    return str(value if value is not None else "").strip().lower()


def _is_all(spec):
    """`all`, `*`… (texte seul, ou liste d'un seul élément) : tout le schéma."""
    if isinstance(spec, (list, tuple)) and len(spec) == 1:
        spec = spec[0]
    return isinstance(spec, str) and _key(spec) in ALL_REFS


def _num(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------- #
# Géométrie
# --------------------------------------------------------------------------- #

def clip_to_rect(cx, cy, w, h, tx, ty, pad=EDGE_GAP):
    """Point où le rayon centre -> (tx, ty) sort du rectangle (centré en cx, cy), plus `pad`."""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw, hh = w / 2 + pad, h / 2 + pad
    sx = hw / abs(dx) if dx else math.inf
    sy = hh / abs(dy) if dy else math.inf
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def cam_for(bbox, margin=CAM_MARGIN, smax=CAM_MAX):
    """Caméra (x, y, échelle) qui cadre `bbox` = (x0, y0, x1, y1). Identité si le zoom est négligeable."""
    x0, y0, x1, y1 = bbox
    bw, bh = (x1 - x0) + 2 * margin, (y1 - y0) + 2 * margin
    s = min(W / bw, H / bh)
    if s <= 1.05:
        return IDENT
    s = min(s, smax)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (round(W / 2 - s * cx, 1), round(H / 2 - s * cy, 1), round(s, 3))


def _same_cam(a, b):
    return all(abs(x - y) < 0.5 for x, y in zip(a[:2], b[:2])) and abs(a[2] - b[2]) < 0.01


# --------------------------------------------------------------------------- #
# Schéma
# --------------------------------------------------------------------------- #

class Schema:
    """Nœuds et liens normalisés, avec leur géométrie en px sur 1920×1080."""

    def __init__(self, sid, title, raw):
        self.id = sid
        self.title = title or ""
        self.warnings = []
        self.nodes, self.edges = [], []
        self._nk, self._ek = {}, {}
        if not isinstance(raw, dict):
            raise SchemaError("le bloc JSON d'un schéma doit être un objet {\"nodes\": […], \"edges\": […]}")
        self.auto_edges = raw.get("auto_edges", True) is not False
        self._load_nodes(raw.get("nodes") or [])
        if not self.nodes:
            raise SchemaError("aucun nœud (clé `nodes`)")
        self._load_edges(raw.get("edges") or [])
        self._check_layout()

    def warn(self, msg):
        self.warnings.append("schéma %s : %s" % (self.id, msg))

    # -- chargement --------------------------------------------------------
    def _load_nodes(self, items):
        for i, it in enumerate(items):
            if isinstance(it, str):
                it = {"id": it, "label": it}
            if not isinstance(it, dict) or not str(it.get("id", "")).strip():
                self.warn("nœud #%d ignoré (objet avec `id` attendu)" % i)
                continue
            nid = str(it["id"]).strip()
            if _key(nid) in self._nk:
                self.warn("nœud en double ignoré : %s" % nid)
                continue
            cls = str(it.get("cls") or "plain").strip().lower()
            if cls not in CLASSES:
                self.warn("nœud %s : cls `%s` inconnue (attendu : %s), `plain` utilisée"
                          % (nid, cls, ", ".join(CLASSES)))
                cls = "plain"
            size = str(it.get("size") or "m").strip().lower()
            if size not in SIZES:
                self.warn("nœud %s : size `%s` inconnue (s, m, l), `m` utilisée" % (nid, size))
                size = "m"
            if "x" not in it or "y" not in it:
                self.warn("nœud %s : `x` et `y` manquants (grille 16×9), placé au centre" % nid)
            fs, sub_px = SIZES[size]
            label = str(it.get("label") if it.get("label") is not None else nid)
            lines = wrap(label, fs) if "\n" not in label else label.split("\n")
            sub = str(it.get("sub") or "")
            sub_lines = wrap(sub, sub_px, WRAP_AT) if sub else []
            lw = max([text_width(l, fs) for l in lines] + [0])
            sw = max([text_width(l, sub_px, bold=False) for l in sub_lines] + [0])
            w = _num(it.get("w"), 0) or max(160.0, math.ceil(max(lw, sw)) + 2 * (PAD_X + BORDER))
            h = _num(it.get("h"), 0) or math.ceil(
                len(lines) * fs * 1.22 + (len(sub_lines) * sub_px * 1.25 + 8 if sub_lines else 0)
                + 2 * (PAD_Y + BORDER))
            node = {"id": nid, "i": len(self.nodes), "label": label, "lines": lines,
                    "sub": sub, "sub_lines": sub_lines, "cls": cls, "size": size,
                    "fs": fs, "sub_px": sub_px, "group": str(it.get("group") or "").strip(),
                    "cx": _num(it.get("x"), 8.0) * GRID, "cy": _num(it.get("y"), 4.5) * GRID,
                    "w": float(w), "h": float(h)}
            self.nodes.append(node)
            self._nk[_key(nid)] = node

    def _load_edges(self, items):
        for i, it in enumerate(items):
            if isinstance(it, str) and ">" in it:
                a, _, b = it.partition(">")
                it = {"from": a, "to": b}
            if not isinstance(it, dict):
                self.warn("lien #%d ignoré (objet avec `from` et `to` attendu)" % i)
                continue
            a, b = self._nk.get(_key(it.get("from"))), self._nk.get(_key(it.get("to")))
            if a is None or b is None:
                self.warn("lien #%d ignoré : nœud inconnu (%s → %s)" % (i, it.get("from"), it.get("to")))
                continue
            eid = str(it.get("id") or "%s>%s" % (a["id"], b["id"])).strip()
            if _key(eid) in self._ek:
                self.warn("lien en double ignoré : %s" % eid)
                continue
            cls = str(it.get("cls") or "plain").strip().lower()
            if cls not in CLASSES:
                self.warn("lien %s : cls `%s` inconnue, `plain` utilisée" % (eid, cls))
                cls = "plain"
            direction = str(it.get("dir") or "->").strip()
            if direction not in ("->", "<->", "--"):
                self.warn("lien %s : dir `%s` inconnue (->, <->, --), `->` utilisée" % (eid, direction))
                direction = "->"
            edge = {"id": eid, "i": len(self.edges), "a": a, "b": b, "cls": cls, "dir": direction,
                    "label": str(it.get("label") or ""), "curve": _num(it.get("curve"), 0.0),
                    "manual": bool(it.get("manual")), "dash": bool(it.get("dash"))}
            edge["geo"] = self._edge_geometry(edge)
            self.edges.append(edge)
            self._ek[_key(eid)] = edge
            self._ek.setdefault(_key("%s>%s" % (a["id"], b["id"])), edge)

    def _edge_geometry(self, e):
        a, b = e["a"], e["b"]
        ax, ay, bx, by = a["cx"], a["cy"], b["cx"], b["cy"]
        length = math.hypot(bx - ax, by - ay) or 1.0
        ctrl = None
        if e["curve"]:
            nx, ny = -(by - ay) / length, (bx - ax) / length
            ctrl = ((ax + bx) / 2 + nx * e["curve"] * length * 0.5,
                    (ay + by) / 2 + ny * e["curve"] * length * 0.5)
        tgt_a = ctrl or (bx, by)
        tgt_b = ctrl or (ax, ay)
        p1 = clip_to_rect(ax, ay, a["w"], a["h"], *tgt_a)
        p2 = clip_to_rect(bx, by, b["w"], b["h"], *tgt_b)
        # tangentes aux deux extrémités (de la courbe vers l'extérieur)
        t_end = (p2[0] - (ctrl or p1)[0], p2[1] - (ctrl or p1)[1])
        t_start = (p1[0] - (ctrl or p2)[0], p1[1] - (ctrl or p2)[1])
        heads = []
        if e["dir"] in ("->", "<->"):
            heads.append(self._head(p2, t_end))
        if e["dir"] == "<->":
            heads.append(self._head(p1, t_start))
        s, f = p1, p2
        if e["dir"] in ("->", "<->"):
            f = self._back(p2, t_end, HEAD_LEN * 0.8)
        if e["dir"] == "<->":
            s = self._back(p1, t_start, HEAD_LEN * 0.8)
        if ctrl:
            d = "M%.1f %.1f Q%.1f %.1f %.1f %.1f" % (s[0], s[1], ctrl[0], ctrl[1], f[0], f[1])
            mid = (0.25 * p1[0] + 0.5 * ctrl[0] + 0.25 * p2[0], 0.25 * p1[1] + 0.5 * ctrl[1] + 0.25 * p2[1])
        else:
            d = "M%.1f %.1f L%.1f %.1f" % (s[0], s[1], f[0], f[1])
            mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        # étiquette : posée AU-DESSUS du lien (la normale qui monte), jamais sur la flèche
        lab_w = math.ceil(text_width(e["label"], LABEL_PX, bold=False)) + 28 if e["label"] else 0
        tx, ty = (p2[0] - p1[0], p2[1] - p1[1])
        tn = math.hypot(tx, ty) or 1.0
        nx, ny = ty / tn, -tx / tn
        if ny > 0 or (ny == 0 and nx < 0):
            nx, ny = -nx, -ny
        off = LABEL_H / 2 + 16
        label_at = (mid[0] + nx * off, mid[1] + ny * off)
        if e["label"] and lab_w > tn - 2 * EDGE_GAP and abs(tx) >= abs(ty):
            self.warn("lien %s : l'étiquette « %s » (%d px) est plus large que le lien (%d px), "
                      "écarter les nœuds sur la grille" % (e["id"], e["label"], lab_w, tn))
        pts = [p1, p2, mid] + ([ctrl] if ctrl else [])
        if e["label"]:
            pts += [(label_at[0] - lab_w / 2, label_at[1] - LABEL_H / 2),
                    (label_at[0] + lab_w / 2, label_at[1] + LABEL_H / 2)]
        return {"d": d, "heads": heads, "mid": mid, "pts": pts, "label_at": label_at, "label_w": lab_w}

    @staticmethod
    def _back(p, tangent, dist):
        n = math.hypot(*tangent) or 1.0
        return (p[0] - tangent[0] / n * dist, p[1] - tangent[1] / n * dist)

    @staticmethod
    def _head(tip, tangent):
        n = math.hypot(*tangent) or 1.0
        ux, uy = tangent[0] / n, tangent[1] / n
        bx, by = tip[0] - ux * HEAD_LEN, tip[1] - uy * HEAD_LEN
        px, py = -uy * HEAD_HALF, ux * HEAD_HALF
        return "%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (tip[0], tip[1], bx + px, by + py, bx - px, by - py)

    def _check_layout(self):
        for n in self.nodes:
            x0, y0, x1, y1 = self.rect(n)
            if x0 < MARGIN or y0 < MARGIN or x1 > W - MARGIN or y1 > H - MARGIN:
                self.warn("nœud %s dépasse de la scène (%d,%d)-(%d,%d) : le rapprocher du centre ou "
                          "raccourcir son libellé" % (n["id"], x0, y0, x1, y1))
        for i, a in enumerate(self.nodes):
            for b in self.nodes[i + 1:]:
                ax0, ay0, ax1, ay1 = self.rect(a)
                bx0, by0, bx1, by1 = self.rect(b)
                if ax0 < bx1 + 20 and bx0 < ax1 + 20 and ay0 < by1 + 20 and by0 < ay1 + 20:
                    self.warn("nœuds %s et %s se chevauchent : les écarter sur la grille" % (a["id"], b["id"]))

    # -- accès -------------------------------------------------------------
    @staticmethod
    def rect(n):
        return (n["cx"] - n["w"] / 2, n["cy"] - n["h"] / 2, n["cx"] + n["w"] / 2, n["cy"] + n["h"] / 2)

    def node(self, nid):
        return self._nk.get(_key(nid))

    def resolve(self, spec):
        """Références d'une étape -> (nœuds, liens, inconnues).

        `a` : un nœud ; `a>b` ou l'`id` d'un lien ; `@groupe` : les nœuds du groupe et les liens
        entre eux ; `all` / `*` : tout le schéma. `spec` : liste, ou texte séparé par des virgules.
        """
        if spec in (None, "", False):
            return [], [], []
        if isinstance(spec, str):
            spec = [s for s in re.split(r"[,;]", spec)]
        nodes, edges, unknown = [], [], []
        for raw in spec:
            ref = str(raw).strip()
            if not ref:
                continue
            k = _key(ref)
            if k in ALL_REFS:
                nodes += [n for n in self.nodes if n not in nodes]
                edges += [e for e in self.edges if e not in edges]
            elif k.startswith("@"):
                grp = [n for n in self.nodes if _key(n["group"]) == k[1:]]
                if not grp:
                    unknown.append(ref)
                    continue
                nodes += [n for n in grp if n not in nodes]
                edges += [e for e in self.edges if e["a"] in grp and e["b"] in grp and e not in edges]
            elif k in self._nk:
                n = self._nk[k]
                if n not in nodes:
                    nodes.append(n)
            elif k in self._ek:
                e = self._ek[k]
                if e not in edges:
                    edges.append(e)
            elif ">" in k:
                a, _, b = k.partition(">")
                hit = next((e for e in self.edges if _key(e["a"]["id"]) == _key(a)
                            and _key(e["b"]["id"]) == _key(b)), None)
                if hit and hit not in edges:
                    edges.append(hit)
                elif not hit:
                    unknown.append(ref)
            else:
                unknown.append(ref)
        return nodes, edges, unknown

    def bbox(self, nodes, edges):
        pts = []
        for n in nodes:
            x0, y0, x1, y1 = self.rect(n)
            pts += [(x0, y0), (x1, y1)]
        for e in edges:
            pts += e["geo"]["pts"]
        if not pts:
            return None
        return (min(p[0] for p in pts), min(p[1] for p in pts),
                max(p[0] for p in pts), max(p[1] for p in pts))

    def as_dict(self):
        """Description complète, écrite dans data/schemas.json (contrôle et débogage)."""
        return {
            "id": self.id, "title": self.title, "auto_edges": self.auto_edges,
            "nodes": [{"id": n["id"], "label": n["label"], "sub": n["sub"], "cls": n["cls"],
                       "group": n["group"], "x": n["cx"] / GRID, "y": n["cy"] / GRID,
                       "w": n["w"], "h": n["h"]} for n in self.nodes],
            "edges": [{"id": e["id"], "from": e["a"]["id"], "to": e["b"]["id"], "cls": e["cls"],
                       "dir": e["dir"], "label": e["label"], "manual": e["manual"]} for e in self.edges],
            "warnings": list(self.warnings),
        }


# --------------------------------------------------------------------------- #
# Registre §1c
# --------------------------------------------------------------------------- #

_HEAD = re.compile(r"^#{2,4}\s+(D\d+)\s*(?:[—–:-]\s*)?(.*)$")


def schemas_from_lines(lines):
    """Lit les lignes du registre §1c.

    Chaque schéma : un en-tête `### D01 — Titre`, puis un bloc JSON entre ``` ``` ```.
    Retourne ({id: Schema}, avertissements, erreurs).
    """
    blocks, cur, in_code, buf = {}, None, False, []
    for ln in lines:
        if not in_code:
            m = _HEAD.match(ln)
            if m:
                cur = m.group(1)
                blocks[cur] = {"title": m.group(2).strip(), "text": None}
                continue
            if cur and ln.strip().startswith("```"):
                in_code, buf = True, []
            continue
        if ln.strip().startswith("```"):
            in_code = False
            if cur and blocks[cur]["text"] is None:
                blocks[cur]["text"] = "\n".join(buf)
            continue
        buf.append(ln)
    out, warns, errors = {}, [], []
    for sid, b in blocks.items():
        if b["text"] is None:
            errors.append("registre §1c : %s sans bloc JSON (entre ```)" % sid)
            continue
        try:
            sch = Schema(sid, b["title"], json.loads(b["text"]))
        except json.JSONDecodeError as exc:
            errors.append("registre §1c : JSON invalide pour %s : %s" % (sid, exc))
            continue
        except SchemaError as exc:
            errors.append("registre §1c : %s : %s" % (sid, exc))
            continue
        out[sid] = sch
        warns += sch.warnings
    return out, warns, errors


# --------------------------------------------------------------------------- #
# Étapes -> « beats » (opérations explicites, état suivi en Python)
# --------------------------------------------------------------------------- #

def _pid(uid, kind, idx):
    return "%s-%s%d" % (uid, kind, idx)


def compile_beats(schema, uid, items, carry=None):
    """Transforme les étapes d'un groupe en opérations explicites.

    `items` : [{"id": "I3.1#0", "rel": 12.3, "params": {...}, "camera": "off"}] dans l'ordre.
    `carry` : éléments déjà montrés par un groupe précédent du même schéma (visibles d'emblée).

    L'état (qui est visible, qui est en retrait, où est la caméra) est suivi ici : le JS ne reçoit
    que des opérations avec valeurs de départ et d'arrivée, donc la timeline se rejoue à
    l'identique quel que soit l'ordre des seeks.
    Retourne (beats, éléments montrés à la fin, avertissements).
    """
    shown = set(carry or ())            # clés ("n", i) / ("e", i)
    opac = {k: 1.0 for k in shown}
    cam = IDENT
    beats, warns = [], []
    prev_cam = None
    for idx, it in enumerate(items):
        p = it.get("params") or {}
        sid = it["id"]
        ops = []
        nodes, edges, unk = schema.resolve(p.get("show"))
        gnodes, gedges, unk2 = schema.resolve(p.get("glow"))
        focus_raw = p.get("focus")
        zoom_raw = p.get("zoom")
        for u in unk + unk2:
            warns.append("étape %s : référence inconnue `%s` (schéma %s)" % (sid, u, schema.id))

        # 1) caméra
        dt = 0.0
        if zoom_raw not in (None, "", False):
            if _is_all(zoom_raw):
                target = IDENT
            else:
                zn, ze, zu = schema.resolve(zoom_raw)
                for u in zu:
                    warns.append("étape %s : `zoom` référence inconnue `%s` (schéma %s)" % (sid, u, schema.id))
                box = schema.bbox(zn, ze)
                target = cam_for(box) if box else cam
                if not box:
                    warns.append("étape %s : `zoom` sans cible (schéma %s)" % (sid, schema.id))
            if not _same_cam(cam, target):
                ops.append({"op": "cam", "dt": 0.0, "from": list(cam), "to": list(target)})
                cam = target
                dt = 0.25

        # 2) apparitions : nœuds, puis liens (explicites + automatiques)
        new_nodes = [n for n in nodes if ("n", n["i"]) not in shown]
        for k, n in enumerate(new_nodes):
            ops.append({"op": "node", "dt": round(dt + k * 0.16, 3), "el": _pid(uid, "n", n["i"])})
            shown.add(("n", n["i"]))
            opac[("n", n["i"])] = 1.0
        t_edges = dt + len(new_nodes) * 0.16 + (0.15 if new_nodes else 0.0)
        new_edges = [e for e in edges if ("e", e["i"]) not in shown]
        if schema.auto_edges:
            for e in schema.edges:
                if (("e", e["i"]) not in shown and e not in new_edges and not e["manual"]
                        and ("n", e["a"]["i"]) in shown and ("n", e["b"]["i"]) in shown
                        and (e["a"] in new_nodes or e["b"] in new_nodes)):
                    new_edges.append(e)
        for k, e in enumerate(new_edges):
            if ("n", e["a"]["i"]) not in shown or ("n", e["b"]["i"]) not in shown:
                warns.append("étape %s : le lien %s est montré avant l'un de ses nœuds (schéma %s)"
                             % (sid, e["id"], schema.id))
            heads = [_pid(uid, "e", e["i"]) + "-h%d" % h for h in range(len(e["geo"]["heads"]))]
            ops.append({"op": "edge", "dt": round(t_edges + k * 0.3, 3), "el": _pid(uid, "e", e["i"]),
                        "path": _pid(uid, "e", e["i"]) + "-p", "heads": heads,
                        "label": (_pid(uid, "l", e["i"]) if e["label"] else None)})
            shown.add(("e", e["i"]))
            opac[("e", e["i"])] = 1.0
        t_after = t_edges + len(new_edges) * 0.3 + (0.45 if new_edges else 0.0)
        fresh = {("n", n["i"]) for n in new_nodes} | {("e", e["i"]) for e in new_edges}

        # 3) focus : tout ce qui est visible hors de la sélection passe en retrait, jusqu'au prochain focus
        if focus_raw not in (None, "", False):
            if _is_all(focus_raw):
                target = {k: 1.0 for k in sorted(shown)}
            else:
                fn, fe, fu = schema.resolve(focus_raw)
                for u in fu:
                    warns.append("étape %s : `focus` référence inconnue `%s` (schéma %s)" % (sid, u, schema.id))
                keep = {("n", n["i"]) for n in fn} | {("e", e["i"]) for e in fe}
                for e in schema.edges:     # un lien entre deux nœuds retenus est retenu
                    if ("n", e["a"]["i"]) in keep and ("n", e["b"]["i"]) in keep:
                        keep.add(("e", e["i"]))
                target = {k: (1.0 if (k in keep or k in fresh) else DIM) for k in sorted(shown)}
            groups = {}
            for k, v in target.items():
                if k in fresh or abs(opac.get(k, 1.0) - v) < 0.01:
                    continue
                groups.setdefault((opac.get(k, 1.0), v), []).append(k)
            for (frm, to), keys in groups.items():
                els = []
                for kind, i in keys:
                    if kind == "n":
                        els.append(_pid(uid, "n", i))
                    else:
                        els.append(_pid(uid, "e", i))
                        if schema.edges[i]["label"]:
                            els.append(_pid(uid, "l", i))
                ops.append({"op": "fade", "dt": round(t_after, 3), "els": els, "from": frm, "to": to})
            for k, v in target.items():
                opac[k] = v

        # 4) glow : un coup de projecteur sur la sélection
        gdt = t_after + (0.35 if focus_raw not in (None, "", False) else 0.0)
        for k, n in enumerate(gnodes):
            if ("n", n["i"]) not in shown:
                warns.append("étape %s : `glow` sur %s, pas encore affiché (schéma %s)" % (sid, n["id"], schema.id))
            ops.append({"op": "glow", "kind": "node", "dt": round(gdt + k * 0.1, 3),
                        "el": _pid(uid, "n", n["i"]), "halo": HALOS[n["cls"]]})
        for k, e in enumerate(gedges):
            if ("e", e["i"]) not in shown:
                warns.append("étape %s : `glow` sur le lien %s, pas encore affiché (schéma %s)"
                             % (sid, e["id"], schema.id))
            ops.append({"op": "glow", "kind": "edge", "dt": round(gdt + (len(gnodes) + k) * 0.1, 3),
                        "el": _pid(uid, "e", e["i"]) + "-p"})

        if not ops:
            warns.append("étape %s sans effet : aucun `show`, `glow`, `focus` ni `zoom` utile (schéma %s)"
                         % (sid, schema.id))
        beat = {"id": sid, "t": round(float(it["rel"]), 3), "ops": ops}
        mode = it.get("camera")
        # webcam sans Cast : la 1re étape est traitée par la boucle générale de build.py ;
        # les suivantes ne posent la caméra que si son état change.
        if it.get("legacy_cam") and mode is not None:
            if idx > 0 and mode != prev_cam:
                beat["cam"] = mode
            prev_cam = mode
        if it.get("camera") == "full":
            warns.append("étape %s : `camera: full` recouvre le centre du schéma ; préférer `off` ou `pip`" % sid)
        beats.append(beat)
    return beats, shown, warns


# --------------------------------------------------------------------------- #
# Balisage
# --------------------------------------------------------------------------- #

def stage_html(schema, uid, shown, hidden_until_shown=True):
    """Le schéma (`.sch-stage`). Un élément pas encore montré est caché en ligne ; un élément
    déjà montré (`shown`) est visible d'emblée."""
    def vis(key):
        return key in shown or not hidden_until_shown

    out = ['<div class="sch-stage" id="%s-stage">' % uid,
           '<svg class="sch-svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H)]
    for e in schema.edges:
        v = vis(("e", e["i"]))
        gid = _pid(uid, "e", e["i"])
        out.append('<g class="sch-edge %s" id="%s">' % (e["cls"], gid))
        out.append('<path id="%s-p" d="%s" pathLength="1" style="stroke-dashoffset:%d"/>'
                   % (gid, e["geo"]["d"], 0 if v else 1))
        for h, pts in enumerate(e["geo"]["heads"]):
            out.append('<polygon class="sch-head" id="%s-h%d" points="%s"%s/>'
                       % (gid, h, pts, "" if v else ' style="opacity:0"'))
        out.append("</g>")
    out.append("</svg>")
    for n in schema.nodes:
        x0, y0, _, _ = schema.rect(n)
        sub = ('<div class="sch-s" style="font-size:%dpx">%s</div>'
               % (n["sub_px"], "<br>".join(_esc(l) for l in n["sub_lines"]))) if n["sub_lines"] else ""
        out.append('<div class="sch-node %s" id="%s" style="left:%.1fpx;top:%.1fpx;width:%.0fpx;height:%.0fpx;'
                   'font-size:%dpx%s"><div class="sch-l">%s</div>%s</div>'
                   % (n["cls"], _pid(uid, "n", n["i"]), x0, y0, n["w"], n["h"], n["fs"],
                      "" if vis(("n", n["i"])) else ";opacity:0",
                      "<br>".join(_esc(l) for l in n["lines"]), sub))
    for e in schema.edges:
        if not e["label"]:
            continue
        lw, lh = e["geo"]["label_w"], LABEL_H
        mx, my = e["geo"]["label_at"]
        out.append('<div class="sch-elab" id="%s" style="left:%.1fpx;top:%.1fpx;width:%dpx;height:%dpx%s">%s</div>'
                   % (_pid(uid, "l", e["i"]), mx - lw / 2, my - lh / 2, lw, lh,
                      "" if vis(("e", e["i"])) else ";opacity:0", _esc(e["label"])))
    out.append("</div>")
    return "".join(out)


# Exécution des opérations. Écrit une fois par groupe, dans la sous-composition.
RUNTIME = r"""
(function (G) {
  tl.set(G.stage, { transformOrigin: "0 0" }, 0);
  G.beats.forEach(function (b, i) {
    tl.addLabel(b.id, b.t);
    if (i > 0) {   // la 1re étape est visible d'emblée ; les suivantes prennent la place de la précédente
      tl.set("#" + G.beats[i - 1].no, { opacity: 0 }, b.t);
      tl.set("#" + b.no, { opacity: 1 }, b.t);
    }
    if (b.cam && G.camFrame && document.querySelector(G.camFrame)) applyCam(tl, G.camFrame, b.cam, b.t, G.sel);
    b.ops.forEach(function (o) {
      var t = b.t + (o.dt || 0);
      if (o.op === "cam") {
        tl.fromTo(G.stage, { x: o.from[0], y: o.from[1], scale: o.from[2] },
          { x: o.to[0], y: o.to[1], scale: o.to[2], duration: 0.9, ease: "power3.inOut", transformOrigin: "0 0", immediateRender: false }, t);
      } else if (o.op === "node") {
        tl.fromTo("#" + o.el, { opacity: 0, scale: 0.55 }, { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.8)", immediateRender: false }, t);
      } else if (o.op === "edge") {
        tl.fromTo("#" + o.path, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut", immediateRender: false }, t);
        o.heads.forEach(function (h) { tl.fromTo("#" + h, { opacity: 0 }, { opacity: 1, duration: 0.2, immediateRender: false }, t + 0.55); });
        if (o.label) tl.fromTo("#" + o.label, { opacity: 0 }, { opacity: 1, duration: 0.4, immediateRender: false }, t + 0.35);
      } else if (o.op === "fade") {
        tl.fromTo(o.els.map(function (e) { return "#" + e; }).join(","), { opacity: o.from }, { opacity: o.to, duration: 0.5, ease: "power2.out", immediateRender: false }, t);
      } else if (o.op === "glow" && o.kind === "node") {
        tl.to("#" + o.el, { scale: 1.14, boxShadow: "0 0 64px 8px " + o.halo, duration: 0.28, yoyo: true, repeat: 1, ease: "power2.inOut" }, t);
      } else if (o.op === "glow") {
        tl.fromTo("#" + o.el, { strokeWidth: 5 }, { strokeWidth: 12, duration: 0.3, yoyo: true, repeat: 1, ease: "power2.inOut", immediateRender: false }, t);
      }
    });
  });
})(__G__);
"""


def render_group(schema, uid, items, carry=None, cam_frame=None, sel=None):
    """Un groupe d'étapes consécutives portant le même schéma -> un seul clip.

    Retourne {"inner": HTML (numéros d'étape + schéma), "js": JS à ajouter à la composition,
              "shown": éléments montrés (à reporter sur le groupe suivant), "warnings": [...]}.
    """
    beats, shown, warns = compile_beats(schema, uid, items, carry)
    numbers = []
    for k, b in enumerate(beats):
        b["no"] = "%s-no%d" % (uid, k)
        numbers.append('<div class="slideno" id="%s" data-step="%s"%s>%s</div>'
                       % (b["no"], _esc(b["id"]), "" if k == 0 else ' style="opacity:0"', _esc(b["id"])))
    inner = "".join(numbers) + stage_html(schema, uid, set(carry or ()))
    payload = {"stage": "#%s-stage" % uid, "sel": sel or "", "camFrame": cam_frame or "",
               "beats": beats}
    js = "\n" + RUNTIME.replace("__G__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return {"inner": inner, "js": js, "shown": shown, "warnings": warns}


def render_static(schema, uid, step):
    """Schéma sans animation (studio pas à pas) : ce que `show` montre est visible, rien ne bouge."""
    p = step.get("params") or {}
    nodes, edges, _ = schema.resolve(p.get("show"))
    shown = {("n", n["i"]) for n in nodes} | {("e", e["i"]) for e in edges}
    if schema.auto_edges:
        for e in schema.edges:
            if not e["manual"] and ("n", e["a"]["i"]) in shown and ("n", e["b"]["i"]) in shown:
                shown.add(("e", e["i"]))
    return stage_html(schema, uid, shown)
