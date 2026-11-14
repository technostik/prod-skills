#!/usr/bin/env python3
"""Génère un fichier `.excalidraw` à partir d'une description compacte (nœuds et liens).

C'est le point de départ d'un schéma que l'on VOIT avant de l'intégrer : le fichier s'ouvre dans Excalidraw
(excalidraw.com, ou l'extension de ton éditeur), se retouche à la main, et sert ensuite de source au build
(`fichier:` dans le registre §1c). Les flèches sont **liées** aux formes : en déplaçant une forme dans Excalidraw,
ses flèches suivent.

Description (JSON) : la même que le registre §1c « à blocs JSON », avec en plus des formes et des conteneurs.

    {"nodes": [{"id": "vie", "label": "Apparition\\nde la vie", "x": 2, "y": 3, "cls": "bleu", "size": "s"},
               {"id": "filtre", "label": "Le filtre", "x": 10, "y": 6.5, "shape": "diamond", "cls": "rouge"},
               {"id": "galaxie", "label": "La galaxie", "x": 8, "y": 4.5, "w": 1500, "h": 800, "valign": "top"}],
     "edges": [{"from": "vie", "to": "filtre", "label": "devant ?", "curve": 0.2}]}

Clés d'un nœud : `id`, `label`, `x`, `y` (centre, grille 16 × 9 de 120 px), `cls` (plain, bleu, vert, or, rouge, dim),
`size` (s, m, l), `shape` (rect, ellipse, diamond), `w`, `h` (px, sinon calculées d'après le texte), `valign`
(`top` pour le titre d'un conteneur). Un nœud qui en contient d'autres (par sa position et sa taille) est dessiné
avant eux. Clés d'un lien : `from`, `to`, `label`, `cls`, `curve` (-1 à 1), `dir` (`->`, `<->`, `--`), `manual`
(`true` : flèche pointillée, qui n'apparaît pas toute seule : il faut la nommer dans `show`).

Les coordonnées du fichier sont celles de l'écran 1920 × 1080 et les polices sont celles de la vidéo : le schéma
est déjà à la bonne échelle quand on l'ouvre.
"""
from __future__ import annotations

import json
import math
import re

import schema_anim as sa
from schema_anim import COLORS, GRID, H, W, SchemaError, text_width, wrap

SHAPE_ALIASES = {"rect": "rectangle", "rectangle": "rectangle", "box": "rectangle", "carre": "rectangle",
                 "carré": "rectangle", "ellipse": "ellipse", "rond": "ellipse", "cercle": "ellipse", "circle": "ellipse",
                 "diamond": "diamond", "losange": "diamond"}
BG = "#05070b"
GAP = 8.0
FONT_FAMILY = 2          # Helvetica : lisible dans Excalidraw, remplacée par la police du thème dans la vidéo
LINE_H = 1.25


def _seed(n):
    return 1000 + 7919 * n


class _Ids:
    def __init__(self):
        self.n = 0

    def next(self, prefix):
        self.n += 1
        return "%s%02d" % (prefix, self.n)


def _node_size(n):
    """Boîte d'un nœud : celle de `w`/`h` si donnés, sinon d'après le texte, agrandie pour les formes rondes."""
    fs, sub_px = sa.SIZES[n["size"]]
    lines = n["lines"]
    lw = max([text_width(l, fs) for l in lines] + [0])
    if n["w"] and n["h"]:
        return float(n["w"]), float(n["h"])
    base_w = max(160.0, math.ceil(lw) + 2 * (sa.PAD_X + sa.BORDER))
    base_h = math.ceil(len(lines) * fs * LINE_H + 2 * (sa.PAD_Y + sa.BORDER))
    k = {"rectangle": (1.0, 1.0), "ellipse": (1.38, 1.55), "diamond": (1.95, 2.1)}[n["shape"]]
    return float(n["w"] or base_w * k[0]), float(n["h"] or base_h * k[1])


def _exit_point(n, tx, ty, gap=GAP):
    """Point où la droite centre -> (tx, ty) sort de la forme (rectangle, ellipse ou losange), plus `gap`."""
    cx, cy, w, h = n["cx"], n["cy"], n["w"], n["h"]
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw, hh = w / 2, h / 2
    if n["shape"] == "ellipse":
        t = 1 / math.sqrt((dx / hw) ** 2 + (dy / hh) ** 2)
    elif n["shape"] == "diamond":
        t = 1 / (abs(dx) / hw + abs(dy) / hh)
    else:
        t = min(hw / abs(dx) if dx else math.inf, hh / abs(dy) if dy else math.inf)
    dist = math.hypot(dx, dy)
    t += gap / dist
    return cx + dx * t, cy + dy * t


def _base(eid, etype, x, y, w, h, color, n):
    return {"id": eid, "type": etype, "x": round(x, 1), "y": round(y, 1), "width": round(w, 1), "height": round(h, 1),
            "angle": 0, "strokeColor": color, "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 2,
            "strokeStyle": "solid", "roughness": 0, "opacity": 100, "groupIds": [], "frameId": None, "roundness": None,
            "seed": _seed(n), "version": 1, "versionNonce": _seed(n) + 1, "isDeleted": False, "boundElements": [],
            "updated": 1700000000000, "link": None, "locked": False}


def _text(eid, text, x, y, w, h, color, fs, container, align, valign, n):
    e = _base(eid, "text", x, y, w, h, color, n)
    e.update({"text": text, "originalText": text, "fontSize": round(fs, 1), "fontFamily": FONT_FAMILY,
              "textAlign": align, "verticalAlign": valign, "containerId": container, "autoResize": True,
              "lineHeight": LINE_H, "baseline": int(fs * 0.8)})
    return e


def build_elements(raw):
    """Description compacte -> (éléments Excalidraw, avertissements). Lève SchemaError."""
    if not isinstance(raw, dict) or not raw.get("nodes"):
        raise SchemaError("description sans `nodes`")
    warns = []
    ids = _Ids()
    nodes, by_key = [], {}
    for k, it in enumerate(raw["nodes"]):
        if isinstance(it, str):
            it = {"id": it, "label": it}
        nid = str(it.get("id") or "").strip()
        if not nid or nid.lower() in by_key:
            warns.append("nœud #%d ignoré (id manquant ou en double)" % k)
            continue
        shape = SHAPE_ALIASES.get(str(it.get("shape") or "rect").strip().lower())
        if shape is None:
            warns.append("nœud %s : forme `%s` inconnue (rect, ellipse, diamond), rectangle utilisé" % (nid, it.get("shape")))
            shape = "rectangle"
        cls = str(it.get("cls") or "plain").strip().lower()
        if cls not in COLORS:
            warns.append("nœud %s : cls `%s` inconnue, `plain` utilisée" % (nid, cls))
            cls = "plain"
        size = str(it.get("size") or "m").strip().lower()
        if size not in sa.SIZES:
            size = "m"
        label = str(it.get("label") if it.get("label") is not None else nid)
        fs = sa.SIZES[size][0]
        lines = label.split("\n") if "\n" in label else wrap(label, fs, sa.WRAP_AT)
        n = {"id": nid, "label": "\n".join(lines), "lines": lines, "shape": shape, "cls": cls, "size": size,
             "cx": float(it.get("x", 8)) * GRID, "cy": float(it.get("y", 4.5)) * GRID,
             "w": it.get("w"), "h": it.get("h"), "valign": "top" if str(it.get("valign") or "").lower() == "top" else "middle",
             "eid": "", "tid": ""}
        n["w"], n["h"] = _node_size(n)
        nodes.append(n)
        by_key[nid.lower()] = n
    if not nodes:
        raise SchemaError("aucun nœud utilisable")

    def inside(a, b):          # b est dans a
        return (a is not b and a["cx"] - a["w"] / 2 <= b["cx"] - b["w"] / 2 + 2 and a["cy"] - a["h"] / 2 <= b["cy"] - b["h"] / 2 + 2
                and a["cx"] + a["w"] / 2 >= b["cx"] + b["w"] / 2 - 2 and a["cy"] + a["h"] / 2 >= b["cy"] + b["h"] / 2 - 2
                and a["w"] * a["h"] > b["w"] * b["h"])

    depth = {id(n): sum(1 for m in nodes if inside(m, n)) for n in nodes}
    order = sorted(nodes, key=lambda n: depth[id(n)])          # les conteneurs d'abord, les enfants par-dessus
    els, count = [], 0
    for n in order:
        count += 1
        n["eid"], n["tid"] = ids.next("n"), ids.next("t")
        x, y = n["cx"] - n["w"] / 2, n["cy"] - n["h"] / 2
        e = _base(n["eid"], n["shape"], x, y, n["w"], n["h"], COLORS[n["cls"]], count)
        e["roundness"] = {"type": 3} if n["shape"] == "rectangle" else None
        e["boundElements"].append({"id": n["tid"], "type": "text"})
        n["el"] = e
        fs = sa.SIZES[n["size"]][0]
        tw = max([text_width(l, fs) for l in n["lines"]] + [0])
        th = len(n["lines"]) * fs * LINE_H
        ty = y + 14 if n["valign"] == "top" else n["cy"] - th / 2
        els.append(e)
        els.append(_text(n["tid"], n["label"], n["cx"] - tw / 2, ty, tw, th, COLORS[n["cls"]], fs, n["eid"], "center", n["valign"], count))
    for k, it in enumerate(raw.get("edges") or []):
        if isinstance(it, str) and ">" in it:
            a, _, b = it.partition(">")
            it = {"from": a, "to": b}
        a = by_key.get(str((it or {}).get("from", "")).strip().lower())
        b = by_key.get(str((it or {}).get("to", "")).strip().lower())
        if a is None or b is None:
            warns.append("lien #%d ignoré : nœud inconnu (%s → %s)" % (k, (it or {}).get("from"), (it or {}).get("to")))
            continue
        cls = str(it.get("cls") or "plain").lower()
        if cls not in COLORS:
            cls = "plain"
        curve = float(it.get("curve") or 0)
        direction = str(it.get("dir") or "->")
        if curve:
            mx, my = (a["cx"] + b["cx"]) / 2, (a["cy"] + b["cy"]) / 2
            ln = math.hypot(b["cx"] - a["cx"], b["cy"] - a["cy"]) or 1.0
            ctrl = (mx - (b["cy"] - a["cy"]) / ln * curve * ln * 0.5, my + (b["cx"] - a["cx"]) / ln * curve * ln * 0.5)
        else:
            ctrl = None
        p1 = _exit_point(a, *(ctrl or (b["cx"], b["cy"])))
        p2 = _exit_point(b, *(ctrl or (a["cx"], a["cy"])))
        count += 1
        eid = ids.next("a")
        e = _base(eid, "arrow", p1[0], p1[1], p2[0] - p1[0], p2[1] - p1[1], COLORS[cls] if cls != "plain" else "#C9D1DC", count)
        pts = [[0, 0]] + ([[round(ctrl[0] - p1[0], 1), round(ctrl[1] - p1[1], 1)]] if ctrl else []) + [[round(p2[0] - p1[0], 1), round(p2[1] - p1[1], 1)]]
        e.update({"points": pts, "lastCommittedPoint": None, "elbowed": False,
                  "startBinding": {"elementId": a["eid"], "focus": 0, "gap": GAP}, "endBinding": {"elementId": b["eid"], "focus": 0, "gap": GAP},
                  "startArrowhead": "arrow" if direction == "<->" else None, "endArrowhead": None if direction == "--" else "arrow"})
        if it.get("manual"):
            e["strokeStyle"] = "dashed"
        if ctrl:
            e["roundness"] = {"type": 2}
        a["el"]["boundElements"].append({"id": eid, "type": "arrow"})
        b["el"]["boundElements"].append({"id": eid, "type": "arrow"})
        els.append(e)
        label = str(it.get("label") or "")
        if label and abs(p2[0] - p1[0]) >= abs(p2[1] - p1[1]) and text_width(label, 32, bold=False) + 28 > math.hypot(p2[0] - p1[0], p2[1] - p1[1]) - 16:
            warns.append("lien %s → %s : l'étiquette « %s » est plus large que le lien, écarter les deux formes" % (a["id"], b["id"], label))
        if label:
            tid = ids.next("l")
            e["boundElements"].append({"id": tid, "type": "text"})
            lw, lh = text_width(label, 32, bold=False) + 10, 32 * LINE_H
            mx, my = (ctrl[0] if ctrl else (p1[0] + p2[0]) / 2), (ctrl[1] if ctrl else (p1[1] + p2[1]) / 2)
            if ctrl:
                mx, my = 0.25 * p1[0] + 0.5 * ctrl[0] + 0.25 * p2[0], 0.25 * p1[1] + 0.5 * ctrl[1] + 0.25 * p2[1]
            els.append(_text(tid, label, mx - lw / 2, my - lh / 2 - 36, lw, lh, "#A9C7F5", 32, eid, "center", "middle", count))
    return els, warns


def to_document(elements):
    """Enveloppe d'un fichier Excalidraw (ouvrable dans excalidraw.com)."""
    return {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": elements,
            "appState": {"gridSize": None, "viewBackgroundColor": BG}, "files": {}}


def dumps(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


_HEAD = re.compile(r"^#{2,4}\s+(D\d+)\b")


def raw_from_storyboard(text, sid):
    """Bloc JSON d'un schéma `Dxx` du registre §1c d'un storyboard (texte). Lève SchemaError."""
    lines, cur, in_code, buf, found = text.split("\n"), None, False, [], None
    for ln in lines:
        if not in_code:
            m = _HEAD.match(ln)
            if m:
                cur = m.group(1)
            elif cur == sid and ln.strip().startswith("```"):
                in_code, buf = True, []
        elif ln.strip().startswith("```"):
            found = "\n".join(buf)
            break
        else:
            buf.append(ln)
    if found is None:
        raise SchemaError("schéma %s absent du registre §1c (ou sans bloc JSON)" % sid)
    try:
        return json.loads(found)
    except json.JSONDecodeError as exc:
        raise SchemaError("JSON invalide pour %s : %s" % (sid, exc))
