#!/usr/bin/env python3
"""Musique du storyboard : registre §1d, repères posés par les étapes, fichiers à générer.

Une musique n'est PAS un fond permanent : elle souligne un moment fort (montée en puissance, point
culminant, conclusion). Elle se déclare une fois dans le registre §1d (identifiant, rôle, prompt pour
le générateur, durée, volume, graine) puis une étape la déclenche avec `music: M01`. Elle s'arrête
à la durée du registre, ou à `music_until:` (une étape : son début ; une scène : sa fin ; un nombre :
des secondes).

Ce module est pur (ni fichier ni réseau). `build.py` l'appelle pour écrire `data/music.json`,
`make-music.py` génère les fichiers, `mix-music.py` les mixe sous la voix.

Les temps sont ceux du master (la composition), avant les inserts de `post-render.py` : les inserts
s'ajoutent au master, donc la musique mixée dans le master reste calée.
"""
from __future__ import annotations

import hashlib
import math
import re

DEFAULT_VOLUME = 0.45        # gain avant ducking (≈ -7 dB) ; sous la voix, le ducking retire encore ~12 dB
DEFAULT_DURATION = 20.0      # secondes, si ni `Durée` ni `music_until`
FADE_IN, FADE_OUT = 1.5, 3.0
MIN_CUE = 4.0                # une musique plus courte qu'ici n'a pas le temps d'exister
MAX_COVERAGE = 0.35          # au-delà, ce n'est plus une ponctuation mais un fond : avertissement
GEN_MARGIN = 0.0             # secondes générées en plus de la durée du repère (la sortie est coupée au mixage)


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", re.sub(r"[àâä]", "a", re.sub(r"[éèêë]", "e", str(s or "").lower())))


def _float(v, default=None):
    try:
        return float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return default


def registry_from_rows(rows):
    """Lignes du tableau §1d (clés déjà en minuscules sans accents, par build.py) -> registre.

    Colonnes : ID | Rôle | Prompt | Durée | Volume | Seed. Seuls ID et Prompt sont obligatoires.
    Retourne (registre, erreurs)."""
    reg, errors = {}, []
    for mid, r in rows.items():
        prompt = (r.get("prompt") or "").strip()
        if not prompt:
            errors.append("registre §1d : %s sans prompt (la colonne Prompt décrit la musique au générateur)" % mid)
            continue
        vol = _float(r.get("volume"), DEFAULT_VOLUME)
        if vol is None or not 0 < vol <= 1:
            errors.append("registre §1d : %s a un volume hors de ]0 ; 1] (%r)" % (mid, r.get("volume")))
            continue
        seed = _float(r.get("seed"))
        reg[mid] = {"role": (r.get("role") or "").strip(), "prompt": prompt,
                    "duration": _float(r.get("duree") or r.get("duration")),
                    "volume": vol, "seed": int(seed) if seed is not None else None}
    return reg, errors


def gen_file(mid, prompt, seed, gen_duration):
    """Nom du fichier : stable pour (musique, prompt, graine, durée), donc réutilisé tant que rien ne change."""
    h = hashlib.sha1(("%s|%s|%s" % (prompt, seed, gen_duration)).encode("utf-8")).hexdigest()[:8]
    return "assets/music/%s-%s.wav" % (mid, h)


def resolve_cues(scenes, registry, total):
    """Étapes portant `music:` -> repères {start, end, ...}. Retourne (repères, avertissements, erreurs).

    `scenes` : liste de scènes de build.py (`id`, `_start`, `_dur`, `steps` avec `id`, `_t`, `_abs_dur`, `params`)."""
    cues, warns, errors = [], [], []
    step_t, scene_end = {}, {}
    for sc in scenes:
        scene_end[sc["id"]] = sc["_start"] + sc["_dur"]
        for st in sc["steps"]:
            step_t[st["id"]] = st["_t"]
    n = 0
    for sc in scenes:
        for st in sc["steps"]:
            p = st.get("params") or {}
            mid = str(p.get("music") or "").strip()
            if not mid:
                continue
            if mid not in registry:
                errors.append("étape %s : musique `%s` absente du registre §1d (déclarées : %s)"
                              % (st["id"], mid, ", ".join(sorted(registry)) or "aucune"))
                continue
            reg = registry[mid]
            start = float(st["_t"])
            until = p.get("music_until")
            if until not in (None, ""):
                u = str(until).strip()
                if u in step_t:
                    end = step_t[u]
                elif u in scene_end:
                    end = scene_end[u]
                elif _float(u) is not None:
                    end = start + _float(u)
                else:
                    errors.append("étape %s : `music_until: %s` n'est ni une étape, ni une scène, ni un nombre de secondes"
                                  % (st["id"], u))
                    continue
                if end <= start:
                    warns.append("étape %s : `music_until` (%.1f s) tombe avant le début de la musique (%.1f s), "
                                 "durée du registre utilisée" % (st["id"], end, start))
                    end = start + (reg["duration"] or DEFAULT_DURATION)
            else:
                end = start + (reg["duration"] or DEFAULT_DURATION)
            end = min(end, total)
            if end - start <= 0.05:
                warns.append("étape %s : la musique %s commence à la fin du film, ignorée" % (st["id"], mid))
                continue
            n += 1
            vol = _float(p.get("music_volume"), reg["volume"])
            gen_dur = int(math.ceil(round(end - start + GEN_MARGIN, 3)))
            cues.append({"cue": "C%d" % n, "music": mid, "role": reg["role"], "prompt": reg["prompt"],
                         "seed": reg["seed"], "step": st["id"], "start": round(start, 3), "end": round(end, 3),
                         "duration": round(end - start, 3), "volume": vol,
                         "fade_in": FADE_IN, "fade_out": FADE_OUT, "gen_duration": gen_dur,
                         "file": gen_file(mid, reg["prompt"], reg["seed"], gen_dur)})
    cues.sort(key=lambda c: c["start"])
    for a, b in zip(cues, cues[1:]):                       # deux musiques ne se superposent pas
        if a["end"] > b["start"]:
            warns.append("musiques %s (%s) et %s (%s) se chevauchent : la première est coupée au début de la seconde"
                         % (a["cue"], a["step"], b["cue"], b["step"]))
            a["end"] = b["start"]
            a["duration"] = round(a["end"] - a["start"], 3)
    for c in cues:
        if c["duration"] < MIN_CUE:
            warns.append("musique %s (%s) : %.1f s seulement, trop court pour s'installer (≥ %.0f s)"
                         % (c["cue"], c["step"], c["duration"], MIN_CUE))
    cov = sum(c["duration"] for c in cues) / total if total else 0.0
    if cov > MAX_COVERAGE:
        warns.append("la musique couvre %.0f %% du film (max conseillé %.0f %%) : elle doit souligner les moments forts, "
                     "pas accompagner la voix en continu" % (cov * 100, MAX_COVERAGE * 100))
    return cues, warns, errors


def plan_dict(cues, total):
    cov = sum(c["duration"] for c in cues) / total if total else 0.0
    return {"version": 1, "total": round(total, 3), "coverage": round(cov, 3), "cues": cues}
