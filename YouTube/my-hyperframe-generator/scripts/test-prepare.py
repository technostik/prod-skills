#!/usr/bin/env python3
"""Tests de scripts/prepare.py : gabarits, contrôle des livrables par mode, chapitres, validation des schémas.

Usage : python3 scripts/test-prepare.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "prepare.py"
FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def run(root, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root)] + list(args), capture_output=True, text=True)


SCENARIO = """# Où va l'argent

Introduction hors chapitre.

## Le constat

Le budget de l'éducation a augmenté de cinquante-sept pour cent depuis deux mille, mais le niveau des élèves a baissé.

## Les causes

Premièrement les dépenses ont servi à créer des postes administratifs plutôt que des heures de cours devant les élèves.

## Les conséquences

Deuxièmement les élèves arrivent au collège sans maîtriser la lecture et le calcul, ce qui coûte cher ensuite.

## La conclusion

Moins d'idéologie, plus de résultats : voilà ce qu'il faut exiger de l'école de la république.
"""

WORDS = ("Bonjour à tous. Aujourd'hui je vous parle du constat. Le budget de l'éducation a augmenté de cinquante-sept pour cent "
         "depuis deux mille mais le niveau des élèves a baissé. Passons aux causes. Premièrement les dépenses ont servi à créer "
         "des postes administratifs plutôt que des heures de cours devant les élèves. Voyons les conséquences. Deuxièmement les "
         "élèves arrivent au collège sans maîtriser la lecture et le calcul ce qui coûte cher ensuite. Pour finir. Moins "
         "d'idéologie plus de résultats voilà ce qu'il faut exiger de l'école de la république.").split()


def make_transcript(root, step=1.0):
    words = [{"word": w, "start": round(i * step, 3), "end": round(i * step + 0.8, 3)} for i, w in enumerate(WORDS)]
    segs = []
    cur = []
    for w in words:
        cur.append(w)
        if w["word"].endswith("."):
            segs.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(x["word"] for x in cur)})
            cur = []
    if cur:
        segs.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": " ".join(x["word"] for x in cur)})
    (root / "assets").mkdir(parents=True, exist_ok=True)
    (root / "assets" / "transcript.json").write_text(json.dumps({"language": "fr", "text": "", "words": words, "segments": segs}), encoding="utf-8")
    return words


def states(r):
    return {m.group(1).strip(): m.group(2) for m in re.finditer(r"^\s{2}(.+?)\s{2,}(ok|n/a|à faire|BLOQUANT)\s", r.stdout, re.M)}


def main():
    print("A. init")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        r = run(root, "init", "--mode", "webcam")
        check("init : dossiers et gabarits", r.returncode == 0 and (root / "assets/bg").is_dir() and (root / "assets/assets.md").exists()
              and (root / "assets/refs.md").exists() and (root / "assets/figures.md").exists() and (root / "assets/schemas").is_dir(), r.stderr)
        check("init : la checklist du mode place la prise et le transcript AVANT les fonds, et le contrôle à la fin",
              r.stdout.index("la prise") < r.stdout.index("transcript") < r.stdout.index("fonds") < r.stdout.index("contrôle"), r.stdout)
        check("init : mode écrit dans assets/prep.json", json.loads((root / "assets/prep.json").read_text())["mode"] == "webcam")
        before = (root / "assets/assets.md").read_text(encoding="utf-8")
        (root / "assets/assets.md").write_text(before + "| BG-09 | x | assets/bg/BG-09.jpg | à faire |\n", encoding="utf-8")
        run(root, "init", "--mode", "webcam")
        check("init : ne réécrit jamais un gabarit déjà rempli", "BG-09" in (root / "assets/assets.md").read_text(encoding="utf-8"))
        r = run(root, "init", "--mode", "auto")
        check("un seul mode par projet", r.returncode == 1 and "un seul mode" in r.stderr, r.stderr)
        r = run(Path(d) / "inconnu", "check")
        check("check sans mode : demande le mode", r.returncode == 1 and "--mode" in r.stderr)

    print("B. check, mode auto")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        run(root, "init", "--mode", "auto")
        r = run(root, "check")
        st = states(r)
        check("projet vide : bloqué, code 1, `pas prêt`", r.returncode == 1 and "pas prêt" in r.stdout, r.stdout)
        check("scénario, voix, transcript : bloquants", st.get("scénario") == "BLOQUANT" and st.get("voix") == "BLOQUANT" and st.get("transcript") == "BLOQUANT", st)
        check("auto : pas de ligne « screencasts »", "screencasts" not in st)
        (root / "SCENARIO.md").write_text(SCENARIO, encoding="utf-8")
        (root / "assets" / "voix.wav").write_bytes(b"RIFF")
        make_transcript(root)
        r = run(root, "check")
        st = states(r)
        check("scénario et voix ok ; transcript : le .txt (sans timecode) manque -> à faire", st["scénario"] == "ok" and st["voix"] == "ok" and st["transcript"] == "à faire", st)
        subprocess.run([sys.executable, str(HERE / "transcript-export.py"), "--root", str(root)], capture_output=True)
        r = run(root, "check")
        st = states(r)
        check("transcript ok avec JSON + TXT", st["transcript"] == "ok", st)
        (root / "assets" / "transcript.txt").write_text("autre chose\n", encoding="utf-8")
        check("transcript.txt qui ne correspond plus au JSON : à faire", states(run(root, "check"))["transcript"] == "à faire")
        subprocess.run([sys.executable, str(HERE / "transcript-export.py"), "--root", str(root)], capture_output=True)

        check("gabarit fonds : la ligne BG-00 « à faire » bloque", states(r)["fonds"] == "à faire", states(r))
        (root / "assets/bg").mkdir(exist_ok=True)
        (root / "assets/assets.md").write_text("| ID | Description | Fichier | Statut |\n|---|---|---|---|\n| BG-00 | noir | assets/bg/BG-00.jpg | ok |\n| BG-01 | ciel | assets/bg/BG-01.jpg | ok |\n| BG-02 | x | assets/bg/BG-02.jpg | écarté |\n", encoding="utf-8")
        check("fonds `ok` mais fichier absent : bloquant, le fichier est nommé", states(run(root, "check"))["fonds"] == "BLOQUANT" and "BG-00" in run(root, "check").stdout)
        (root / "assets/bg/BG-00.jpg").write_bytes(b"x")
        (root / "assets/bg/BG-01.jpg").write_bytes(b"x")
        check("fonds : les lignes écartées sont ignorées", states(run(root, "check"))["fonds"] == "ok")

        (root / "assets/refs.md").write_text("| ID | Type | Source | Fichier local | Statut |\n|---|---|---|---|---|\n| R01 | portrait | https://x | assets/references/R01.png | ok |\n", encoding="utf-8")
        check("référence `ok` sans fichier : bloquant", states(run(root, "check"))["références"] == "BLOQUANT")
        (root / "assets/references").mkdir(exist_ok=True)
        (root / "assets/references/R01.png").write_bytes(b"x")
        check("référence avec fichier : ok", states(run(root, "check"))["références"] == "ok")
        (root / "assets/refs.md").write_text("| ID | Type | Source | Fichier local | Statut |\n|---|---|---|---|---|\n", encoding="utf-8")
        check("aucune référence : n/a, ne bloque pas", states(run(root, "check"))["références"] == "n/a")
        (root / "assets/figures.md").write_text("| ID | Valeur | Libellé | Source | Statut |\n|---|---|---|---|---|\n| F01 | +57 % | budget | | ok |\n", encoding="utf-8")
        check("chiffre sans source : bloquant (un chiffre affiché a toujours une source)", states(run(root, "check"))["chiffres"] == "BLOQUANT")
        (root / "assets/figures.md").write_text("| ID | Valeur | Libellé | Source | Statut |\n|---|---|---|---|---|\n| F01 | +57 % | budget | INSEE 2024 | ok |\n", encoding="utf-8")
        check("chiffre sourcé : ok", states(run(root, "check"))["chiffres"] == "ok")

        print("C. chapitres")
        r = run(root, "chapters")
        ch = json.loads((root / "assets/chapters.json").read_text(encoding="utf-8"))
        check("chapters : un chapitre par titre `##`, le premier à 0", r.returncode == 0 and [c["title"] for c in ch] == ["Le constat", "Les causes", "Les conséquences", "La conclusion"] and ch[0]["start"] == 0.0, r.stdout + r.stderr)
        idx = {w: i for i, w in enumerate(WORDS)}
        want = {"Les causes": idx["Premièrement"], "Les conséquences": idx["Deuxièmement"], "La conclusion": idx["Moins"]}
        got = {c["title"]: c["start"] for c in ch}
        check("chapters : chaque titre est aligné sur le début de sa section dans le transcript (±2 s)",
              all(abs(got[t] - float(i)) <= 2.0 for t, i in want.items()), (got, want))
        check("chapters : aucun chapitre « à vérifier » quand l'alignement est net", not any(c.get("verify") for c in ch), [c for c in ch if c.get("verify")])
        txt = (root / "assets/chapters.txt").read_text(encoding="utf-8").splitlines()
        check("format YouTube : « 00:00 Titre », temps croissants", txt[0] == "00:00 Le constat" and all(re.match(r"^\d\d:\d\d ", l) for l in txt) and len(txt) == 4, txt)
        check("check : chapitres ok", states(run(root, "check"))["chapitres"] == "ok")
        r = run(root, "check")
        check("tout est prêt : code 0 et assets/prep.json « ready »", r.returncode == 0 and json.loads((root / "assets/prep.json").read_text())["ready"] is True, r.stdout[-300:])

        (root / "SCENARIO.md").write_text("# T\n\n## Un\n\nalpha beta gamma delta epsilon zeta eta theta iota\n\n## Deux\n\nkappa lambda mu nu xi omicron pi rho sigma\n\n## Trois\n\ntau upsilon phi chi psi omega\n", encoding="utf-8")
        r = run(root, "chapters")
        ch = json.loads((root / "assets/chapters.json").read_text(encoding="utf-8"))
        check("section introuvable dans le transcript : temps estimé et marquée « à vérifier »", any(c.get("verify") for c in ch) and "à vérifier" in r.stdout, r.stdout)
        (root / "SCENARIO.md").write_text("# T\n\n## Un\n\ntexte\n", encoding="utf-8")
        r = run(root, "chapters")
        check("moins de deux titres : erreur claire", r.returncode == 1 and "deux titres" in r.stderr, r.stderr)

    print("D. check, mode webcam")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        run(root, "init", "--mode", "webcam")
        (root / "SCENARIO.md").write_text(SCENARIO, encoding="utf-8")
        st = states(run(root, "check"))
        check("webcam : la prise (caméra) est bloquante, les screencasts sont à faire", st.get("prise (caméra)") == "BLOQUANT" and st.get("screencasts") == "à faire", st)
        (root / "assets" / "cam-clean.mkv").write_bytes(b"x")
        check("caméra sans voix nettoyée : encore bloquant", states(run(root, "check"))["prise (caméra)"] == "BLOQUANT")
        (root / "assets" / "voix-posthoc-v1.wav").write_bytes(b"x")
        (root / "assets" / "cast-segments.json").write_text(json.dumps({"segments": [{"start": 1.0, "end": 5.0}]}), encoding="utf-8")
        st = states(run(root, "check"))
        check("prise ok, screencasts repérés", st["prise (caméra)"] == "ok" and st["screencasts"] == "ok", st)
        (root / "assets" / "cast-segments.json").unlink()
        prep = json.loads((root / "assets/prep.json").read_text())
        prep["screencasts"] = "none"
        (root / "assets/prep.json").write_text(json.dumps(prep), encoding="utf-8")
        check("« pas de screencast » déclaré dans prep.json : ok", states(run(root, "check"))["screencasts"] == "ok")

    print("E. schémas : voir, valider, retoucher")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        run(root, "init", "--mode", "auto")
        sch = root / "assets" / "schemas" / "D01.excalidraw"
        (root / "assets/schemas/D01.src.json").write_text(json.dumps({"nodes": [{"id": "a", "label": "A", "x": 4, "y": 4.5}, {"id": "b", "label": "B", "x": 12, "y": 4.5}], "edges": [{"from": "a", "to": "b"}]}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(HERE / "schema-to-excalidraw.py"), "--root", str(root), "--json", "assets/schemas/D01.src.json", "--id", "D01", "--no-preview"], capture_output=True, text=True)
        check("fichier généré", r.returncode == 0 and sch.exists(), r.stderr)
        st = states(run(root, "check"))
        check("schéma sans aperçu : bloquant", st["schémas"] == "BLOQUANT" and "pas d'aperçu" in run(root, "check").stdout, st)
        subprocess.run([sys.executable, str(HERE / "excalidraw-preview.py"), str(sch), "--html"], capture_output=True, text=True)
        out = run(root, "check").stdout
        check("aperçu fait mais pas validé : bloquant, avec la commande de validation", "pas encore validé" in out and "validate-schema" in out, out)
        r = run(root, "validate-schema", "D01")
        check("validate-schema D01 : écrit le tampon", r.returncode == 0 and (root / "assets/schemas/D01.validated").exists(), r.stderr)
        check("validé : ok", states(run(root, "check"))["schémas"] == "ok")
        time.sleep(1.1)
        doc = json.loads(sch.read_text(encoding="utf-8"))
        doc["elements"][0]["x"] += 5                       # retouché à la main dans Excalidraw
        sch.write_text(json.dumps(doc), encoding="utf-8")
        out = run(root, "check").stdout
        check("retouché depuis l'aperçu : bloquant (relancer l'aperçu)", "retouché depuis l'aperçu" in out, out)
        subprocess.run([sys.executable, str(HERE / "excalidraw-preview.py"), str(sch), "--html"], capture_output=True, text=True)
        out = run(root, "check").stdout
        check("aperçu refait mais plus validé : bloquant (retouché depuis sa validation)", "retouché depuis sa validation" in out, out)
        run(root, "validate-schema", "D01")
        check("revalidé : ok", states(run(root, "check"))["schémas"] == "ok")
        r = run(root, "validate-schema", "D77")
        check("schéma absent : erreur claire", r.returncode == 1 and "absent" in r.stderr, r.stderr)
        os.remove(root / "assets/schemas/D01.handles.md")
        r = run(root, "validate-schema", "D01")
        check("valider sans aperçu à jour : refusé", r.returncode == 1 and "aperçu" in r.stderr, r.stderr)

    print("\n" + ("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)) if FAILS else "OK : tous les tests passent"))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
