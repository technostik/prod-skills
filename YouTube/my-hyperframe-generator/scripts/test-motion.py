#!/usr/bin/env python3
"""Tests du mouvement des primitives (scripts/motion.py, scripts/motion_js/).

  A. profils : `sobre` n'ajoute aucun code (aucun jeton `__M_`, aucun `_M`) ; `vivant` et `calme` l'ajoutent ;
  B. déterminisme : deux builds identiques sont identiques octet pour octet ; une autre graine change le rendu ;
  C. aucun hasard au rendu : `Math.random` absent de la bibliothèque et des compositions ;
  D. en-tête `**Mouvement** : sobre` et `motion:` d'une étape ; profil inconnu → avertissement ;
  E. syntaxe JS (node --check, si node est présent) de chaque composition en vivant et en calme, en 16:9 et en 9:16.

Usage : python3 scripts/test-motion.py   (Python 3 ; node facultatif)
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
DEMO = SKILL / "examples" / "demo"
sys.path.insert(0, str(HERE))
import motion  # noqa: E402

FAILS = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def build(tag, *args, storyboard=None):
    work = Path(tempfile.mkdtemp(prefix="motion-" + tag + "-"))
    root = work / "p"
    shutil.copytree(DEMO, root)
    if storyboard is not None:
        (root / "storyboard.md").write_text(storyboard, encoding="utf-8")
    r = subprocess.run([sys.executable, str(HERE / "build.py"), "--root", str(root), "--storyboard", "storyboard.md",
                        *args], capture_output=True, text=True)
    return root, r


def comps(root):
    return {p.name: p.read_text(encoding="utf-8") for p in sorted((root / "compositions").glob("i*.html"))}


def main():
    # A
    root_s, r = build("sobre", "--motion", "sobre")
    sobre = comps(root_s)
    check(r.returncode == 0 and len(sobre) > 0, "build sobre")
    check(all("__M_" not in h and "_M.step" not in h and "_mv" not in h for h in sobre.values()), "sobre : aucun code de mouvement ajouté")
    root_v, r = build("vivant")
    viv = comps(root_v)
    check(r.returncode == 0 and all("_M.step" in h and "__M_" not in h and "__MCFG__" not in h for h in viv.values()),
          "vivant : bibliothèque présente, aucun jeton résiduel")
    root_c, r = build("calme", "--motion", "calme")
    check(r.returncode == 0 and all('"level": "calme"' in h for h in comps(root_c).values()), "calme")
    # B
    root_v2, _ = build("vivant2")
    check(comps(root_v2) == viv, "vivant déterministe")
    root_g, _ = build("graine", "--motion-seed", "5")
    check(comps(root_g) != viv, "une autre graine change les variations")
    # C
    lib = "\n".join(p.read_text(encoding="utf-8") for p in (HERE / "motion_js").glob("*.js"))
    check("Math.random" not in lib and not any("Math.random" in h for h in viv.values()), "aucun Math.random")
    # D
    sb = (DEMO / "storyboard.md").read_text(encoding="utf-8")
    head_sb = sb.replace("\n\n> Format minuté", "\n\n**Mouvement** : sobre\n\n> Format minuté", 1)
    root_h, r = build("entete", storyboard=head_sb)
    check("**Mouvement**" in head_sb and comps(root_h) == sobre, "en-tête `**Mouvement** : sobre` = rendu historique")
    profile, seed, warns = motion.parse_profile("bizarre", None)
    check(profile == "vivant" and warns, "profil inconnu : avertissement, repli sur vivant")
    check(motion.parse_profile(None, "calme · graine 7")[:2] == ("calme", 7), "en-tête « calme · graine 7 »")
    step_sb = re.sub(r"(\n- `I1\.1#0`[^\n]*\n)", r"\1  - motion: gauche\n", sb, count=1)
    root_f, r = build("force", storyboard=step_sb)
    check('"I1.1#0": "gauche"' in "".join(comps(root_f).values()), "`motion: gauche` transmis à la composition")
    # E
    if shutil.which("node"):
        for tag, rt in (("vivant", root_v), ("calme", root_c)):
            bad = 0
            for name, h in comps(rt).items():
                js = re.search(r"<script>(.*?)</script>\s*</template>", h, re.S).group(1)
                f = rt / (name + ".js")
                f.write_text(js, encoding="utf-8")
                bad += subprocess.run(["node", "--check", str(f)], capture_output=True).returncode != 0
            check(bad == 0, "syntaxe JS (%s, 16:9)" % tag)
        root_9, r = build("vertical", "--format", "9:16")
        check(r.returncode == 0 and "_M.step" in "".join(comps(root_9).values()), "build 9:16 en vivant")
    print("\n%d échec(s)" % len(FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
