#!/usr/bin/env python3
"""Shorts de promotion : trois séquences percutantes de la vidéo, proposées dans le storyboard.

Le LLM qui écrit le storyboard choisit TROIS séquences (3 minutes au plus chacune) qui feront la promo de la
vidéo, et les déclare dans la section `## 6. Shorts`. `build.py` les résout en temps, les cale sur des débuts et
des fins de phrases du transcript, et écrit `data/shorts_segments.json` au format de la commande
`video short-extractor` de fast-market :

    [{"title": "…", "start": "00:09:10,040", "end": "00:09:37,320"}, …]

    video short-extractor renders/final.mp4 --segments data/shorts_segments.json --layout fit-blur --output-dir shorts/

Ce module est pur (ni fichier ni réseau).
"""
from __future__ import annotations

import re

MAX_SHORT = 180.0         # 3 minutes : la limite d'un short
MIN_SHORT = 10.0          # en dessous, la séquence n'a pas le temps de dire quelque chose
WANTED = 3                # le nombre de shorts proposés
SNAP_START = 4.0          # s : de combien le début peut reculer pour tomber sur un début de phrase
SNAP_END = 4.0            # s : de combien la fin peut avancer pour tomber sur une fin de phrase
MAX_TITLE = 100
SENTENCE_END = re.compile(r"[.!?…]+[»\")\]]*$")


def parse_tc(v):
    """`00:09:10,040`, `00:09:10.040`, `9:10`, `70`, `70.5` -> secondes ; None si ce n'est pas un temps."""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v or "").strip().replace(",", ".")
    if not s:
        return None
    m = re.fullmatch(r"(?:(\d+):)?(\d{1,2}):(\d{1,2}(?:\.\d+)?)", s)
    if m:
        return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return float(s) if re.fullmatch(r"\d+(?:\.\d+)?", s) else None


def fmt_tc(t):
    """Secondes -> `HH:MM:SS,mmm` (le format de `video short-extractor`)."""
    ms = int(round(max(0.0, t) * 1000))
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def entries_from_rows(rows):
    """Lignes du tableau §6 (clés normalisées par build.py : id, titre, debut, fin, pourquoi) -> (entrées, erreurs)."""
    out, errors = [], []
    for sid, r in rows.items():
        title = " ".join(str(r.get("titre") or r.get("title") or "").split())
        a, b = str(r.get("debut") or r.get("start") or "").strip(), str(r.get("fin") or r.get("end") or "").strip()
        if not title:
            errors.append("§6 Shorts : %s sans titre (l'accroche du short)" % sid)
        elif not a or not b:
            errors.append("§6 Shorts : %s sans début ou sans fin (une étape ou un timecode)" % sid)
        else:
            out.append({"id": sid, "title": title, "start": a, "end": b, "why": str(r.get("pourquoi") or "").strip()})
    return out, errors


def sentences_from_transcript(data):
    """[(début, fin)] des phrases : les segments du transcript s'il y en a, sinon coupés aux fins de phrase."""
    if not isinstance(data, dict):
        return []
    segs = [(float(s.get("start") or 0), float(s.get("end") or 0)) for s in data.get("segments") or [] if s.get("text")]
    if segs:
        return segs
    words = [w for w in data.get("words") or [] if str(w.get("word") or w.get("text") or "").strip()]
    out, cur = [], []
    for w in words:
        cur.append(w)
        if SENTENCE_END.search(str(w.get("word") or w.get("text")).strip()):
            out.append((float(cur[0].get("start") or 0), float(cur[-1].get("end") or cur[-1].get("start") or 0)))
            cur = []
    if cur:
        out.append((float(cur[0].get("start") or 0), float(cur[-1].get("end") or cur[-1].get("start") or 0)))
    return out


def resolve(scenes, entries, total, sentences=None):
    """Entrées -> segments {title, start, end, ...}. Retourne (segments, avertissements, erreurs).

    Début : une étape (son début), une scène (son début) ou un timecode. Fin : une étape (sa FIN), une scène (sa fin)
    ou un timecode. Le début recule jusqu'au début de phrase le plus proche (≤ 4 s) et la fin avance jusqu'à la fin de
    phrase la plus proche (≤ 4 s), pour ne jamais couper un mot ou une phrase."""
    step_start, step_end, scene_start, scene_end = {}, {}, {}, {}
    for sc in scenes:
        scene_start[sc["id"]] = sc["_start"]
        scene_end[sc["id"]] = sc["_start"] + sc["_dur"]
        for st in sc["steps"]:
            step_start[st["id"]] = st["_t"]
            step_end[st["id"]] = st["_t"] + st["_abs_dur"]
    segs, warns, errors = [], [], []
    for e in entries:
        def at(tok, ends):
            t = str(tok).strip()
            if t in step_start:
                return (step_end if ends else step_start)[t]
            if t in scene_start:
                return (scene_end if ends else scene_start)[t]
            return parse_tc(t)
        a, b = at(e["start"], False), at(e["end"], True)
        if a is None or b is None:
            errors.append("§6 Shorts : %s : `%s` → `%s` ne désigne ni une étape, ni une scène, ni un timecode"
                          % (e["id"], e["start"], e["end"]))
            continue
        a, b = max(0.0, a), min(total, b)
        if sentences:
            starts = [s for s, _ in sentences if a - SNAP_START <= s <= a + 0.25]
            if starts:
                a = max(starts)                               # le début de phrase le plus proche, jamais après
            else:
                warns.append("short %s : le début (%.1f s) ne tombe pas sur un début de phrase, à vérifier" % (e["id"], a))
            ends = [t for _, t in sentences if b - 0.25 <= t <= b + SNAP_END]
            if ends:
                b = min(ends)
            else:
                warns.append("short %s : la fin (%.1f s) ne tombe pas sur une fin de phrase, à vérifier" % (e["id"], b))
        dur = b - a
        if dur <= 0:
            errors.append("§6 Shorts : %s : la fin (%.1f s) est avant le début (%.1f s)" % (e["id"], b, a))
            continue
        if dur > MAX_SHORT:
            errors.append("§6 Shorts : %s dure %.0f s, 3 minutes au plus (%.0f s) : raccourcir la séquence" % (e["id"], dur, MAX_SHORT))
            continue
        if dur < MIN_SHORT:
            warns.append("short %s : %.0f s seulement, trop court pour dire quelque chose (≥ %.0f s)" % (e["id"], dur, MIN_SHORT))
        if len(e["title"]) > MAX_TITLE:
            warns.append("short %s : titre de %d caractères (≤ %d) : une accroche, pas une phrase" % (e["id"], len(e["title"]), MAX_TITLE))
        segs.append({"id": e["id"], "title": e["title"], "start": round(a, 3), "end": round(b, 3),
                     "duration": round(dur, 3), "why": e.get("why", "")})
    for i, x in enumerate(segs):
        for y in segs[i + 1:]:
            if x["start"] < y["end"] and y["start"] < x["end"]:
                warns.append("shorts %s et %s se chevauchent : choisir trois séquences différentes" % (x["id"], y["id"]))
    if segs and len(segs) != WANTED:
        warns.append("%d short(s) proposé(s), %d attendus" % (len(segs), WANTED))
    return segs, warns, errors


def extractor_list(segs):
    """Le contenu de data/shorts_segments.json : exactement les trois clés que lit `video short-extractor`."""
    return [{"title": s["title"], "start": fmt_tc(s["start"]), "end": fmt_tc(s["end"])} for s in segs]


def shift(segs, cuts):
    """Segments décalés sur la timeline de la vidéo finale : `cuts` = [(t_coupe_sur_le_master, durée_insert)]."""
    cuts = sorted(cuts)

    def f(t, closed):
        return t + sum(d for c, d in cuts if (c <= t if closed else c < t))

    return [dict(s, start=round(f(s["start"], True), 3), end=round(f(s["end"], False), 3)) for s in segs]
