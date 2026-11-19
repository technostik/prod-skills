#!/usr/bin/env python3
"""Mouvement des primitives : profils `vivant` (défaut), `calme` et `sobre`.

`sobre` reproduit exactement le rendu historique (octet pour octet) : aucun code n'est ajouté.
`vivant` ajoute, dans chaque composition, une petite bibliothèque JS (scripts/motion_js/*.js) qui remplace les
mouvements fixes des primitives par des variantes tirées au sort : texte qui arrive d'un bord, qui tombe, qui
tourne, tampon lancé de travers, pastilles dispersées, etc. Les tirages sont déterministes : une graine
(`--motion-seed`, `**Mouvement**` ou, par défaut, un hachage du titre) + l'identifiant de l'étape.
`calme` garde les variantes mais réduit les distances et supprime les effets les plus voyants.

Écritures acceptées dans le storyboard :
    **Mouvement** : vivant | calme | sobre   (optionnel : « vivant · graine 7 »)
    - motion: sobre | calme | vivant | gauche | droite | haut | bas | zoom | inclinaison | rotation | flou | chute | montee
      (sur une étape : change le profil de cette étape, ou force la direction d'entrée)
"""
from __future__ import annotations

import json
import re
import unicodedata
import zlib
from pathlib import Path

PROFILES = ("vivant", "calme", "sobre")
DEFAULT_PROFILE = "vivant"
PROFILE_ALIASES = {
    "vivant": "vivant", "dynamique": "vivant", "lively": "vivant", "on": "vivant", "oui": "vivant",
    "calme": "calme", "doux": "calme", "discret": "calme", "soft": "calme",
    "sobre": "sobre", "off": "sobre", "non": "sobre", "aucun": "sobre", "none": "sobre", "classique": "sobre",
    "fixe": "sobre", "historique": "sobre",
}
STEP_FORCE = {"sobre", "calme", "vivant", "gauche", "droite", "haut", "bas", "zoom", "inclinaison", "rotation",
              "flou", "chute", "montee"}
JS_DIR = Path(__file__).resolve().parent / "motion_js"


def _norm(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode()
    return s.strip().lower()


def parse_profile(cli_value, header_value):
    """-> (profil, graine ou None, avertissements). La ligne de commande l'emporte sur l'en-tête."""
    warns, seed = [], None
    for raw in (cli_value, header_value):
        if raw is None or str(raw).strip() == "":
            continue
        txt = _norm(raw)
        m = re.search(r"(?:graine|seed)\s*[:=]?\s*(\d+)", txt)
        if m and seed is None:
            seed = int(m.group(1))
        word = re.split(r"[\s·,;|]+", re.sub(r"(?:graine|seed)\s*[:=]?\s*\d+", "", txt).strip())[0]
        if word in PROFILE_ALIASES:
            return PROFILE_ALIASES[word], seed, warns
        warns.append("mouvement inconnu %r (vivant, calme ou sobre) : profil par défaut `%s`" % (raw, DEFAULT_PROFILE))
    return DEFAULT_PROFILE, seed, warns


def default_seed(title):
    return zlib.crc32(_norm(title).encode("utf-8")) & 0xFFFFFFFF


def step_overrides(scenes):
    """{id d'étape: valeur normalisée} d'après `motion:` / `mouvement:`, + avertissements."""
    out, warns = {}, []
    for sc in scenes:
        for st in sc["steps"]:
            p = st.get("params") or {}
            raw = p.get("motion", p.get("mouvement"))
            if raw is None or str(raw).strip() == "":
                continue
            v = PROFILE_ALIASES.get(_norm(raw), _norm(raw)) if _norm(raw) in PROFILE_ALIASES else _norm(raw)
            if v in STEP_FORCE:
                out[st["id"]] = v
            else:
                warns.append("`motion: %s` inconnu à l'étape %s (ignoré)" % (raw, st["id"]))
    return out, warns


def _lib():
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(JS_DIR.glob("*.js")))


# jeton du gabarit JS -> nom du drapeau posé par la bibliothèque (` && !_mv.<drapeau>` dans la condition)
FLAGS = {"__M_IN__": "entry", "__M_HEAD__": "head", "__M_IM__": "img"}
SIMPLE_FLAGS = {"__M_CT__": "count", "__M_ST__": "strike", "__M_EN__": "enumerate", "__M_SP__": "spot",
                "__M_C2__": "cols2", "__M_SM__": "stamp", "__M_CH__": "chip", "__M_IC__": "icon",
                "__M_AR__": "arrow", "__M_PU__": "punch", "__M_VS__": "versus", "__M_DV__": "diverge",
                "__M_RF__": "ref", "__M_BA__": "bars", "__M_SE__": "seuil", "__M_C3__": "compare3"}


def apply(js, profile, cfg):
    """Remplace les jetons `__M_*__` du gabarit. `sobre` : tous vides (rendu historique à l'octet près)."""
    lively = profile != "sobre"
    for tok, flag in {**FLAGS, **SIMPLE_FLAGS}.items():
        js = js.replace(tok, (" && !_mv.%s" % flag) if lively else "")
    js = js.replace("__M_PRE__", " var _mv = _M.step(step, sel, t, dur);" if lively else "")
    js = js.replace("__M_CTRRET__", "if (_mv.count) return; " if lively else "")
    js = js.replace("__M_BG__", " && !_M.bg(__DUR__)" if lively else "")
    js = js.replace("__M_LIB__", ("\n" + _lib().replace("__MCFG__", json.dumps(cfg, ensure_ascii=False))) if lively else "")
    return js


def scene_cfg(profile, seed, cid, vw, vh, steps):
    """Configuration d'une composition (`cid` = `i03`) : la graine du film est mêlée à la scène."""
    mine = {k: v for k, v in steps.items()}
    return {"level": profile, "seed": (seed ^ zlib.crc32(cid.encode())) & 0xFFFFFFFF, "vw": vw, "vh": vh,
            "steps": mine}
