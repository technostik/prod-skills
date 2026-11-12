#!/usr/bin/env python3
"""Génère le fichier .excalidraw d'un schéma à partir d'une description compacte (nœuds, liens), puis l'aperçoit.

  python3 scripts/schema-to-excalidraw.py --json assets/schemas/D01.src.json --id D01
  python3 scripts/schema-to-excalidraw.py --storyboard assets/storyboard.md --id D01      # bloc JSON du registre §1c

Écrit assets/schemas/D01.excalidraw (sauf --out), puis lance l'aperçu : D01.preview.png (à regarder) et
D01.handles.md (les éléments à citer dans les étapes). Format de la description : en tête de excalidraw_gen.py.

Le fichier n'est JAMAIS écrasé s'il existe (tu as peut-être retouché le dessin) : --force pour le régénérer.
Le schéma est ensuite validé et retouché dans Excalidraw ; le storyboard le référence par `fichier:` (registre §1c).
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import excalidraw_gen as gen  # noqa: E402
import schema_anim as sa  # noqa: E402


def die(msg):
    print("erreur : " + msg, file=sys.stderr)
    sys.exit(1)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Description compacte -> fichier .excalidraw + aperçu.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", default=None, help="fichier JSON de description")
    ap.add_argument("--storyboard", default=None, help="storyboard dont le registre §1c porte le bloc JSON de --id")
    ap.add_argument("--id", required=True, help="identifiant du schéma (D01…)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--force", action="store_true", help="écraser un fichier existant")
    ap.add_argument("--no-preview", action="store_true")
    a = ap.parse_args(argv)
    if bool(a.json) == bool(a.storyboard):
        die("donner --json FICHIER ou --storyboard FICHIER (l'un des deux)")
    root = Path(a.root).resolve()
    try:
        if a.json:
            raw = json.loads((root / a.json).read_text(encoding="utf-8"))
        else:
            raw = gen.raw_from_storyboard((root / a.storyboard).read_text(encoding="utf-8"), a.id)
        elements, warns = gen.build_elements(raw)
    except (sa.SchemaError, json.JSONDecodeError, FileNotFoundError) as exc:
        die(str(exc))
    out = Path(a.out) if a.out else Path("assets/schemas") / (a.id + ".excalidraw")
    out = out if out.is_absolute() else root / out
    if out.exists() and not a.force:
        die("%s existe déjà (peut-être retouché à la main) : --force pour le régénérer" % out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(gen.dumps(gen.to_document(elements)), encoding="utf-8")
    print("écrit : %s (%d éléments)" % (out, len(elements)))
    for w in warns:
        print("avertissement : " + w)
    if not a.no_preview:
        import importlib.util
        spec = importlib.util.spec_from_file_location("excalidraw_preview", HERE / "excalidraw-preview.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main([str(out), "--id", a.id])
    print("suite : regarder %s, retoucher dans Excalidraw si besoin, puis `- fichier: %s` dans le registre §1c"
          % (out.with_name(out.stem + ".preview.png").name, out.relative_to(root) if out.is_relative_to(root) else out))


if __name__ == "__main__":
    main()
