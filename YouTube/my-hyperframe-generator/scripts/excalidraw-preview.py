#!/usr/bin/env python3
"""Aperçu d'un schéma Excalidraw : comment il sera vu dans la vidéo, et comment le nommer dans les étapes.

  python3 scripts/excalidraw-preview.py assets/schemas/D01.excalidraw

écrit à côté du fichier :
  D01.preview.png    le schéma habillé au thème de la vidéo (1920 × 1080, fond sombre) : à REGARDER avant de valider
  D01.handles.md     la liste des éléments à citer dans `show`, `glow`, `focus`, `zoom` (lue par le LLM qui écrit le storyboard)
  D01.preview.html   (avec --html) la même image en page web, si Playwright n'est pas installé

Workflow : générer ou dessiner le schéma → lancer l'aperçu → regarder l'image → corriger dans Excalidraw si besoin
(le fichier .excalidraw est la source : le retoucher, l'enregistrer, relancer l'aperçu) → valider → référencer
`fichier:` dans le registre §1c du storyboard.

Options : --id D01  --title "…"  --html  --no-write (n'écrit rien, affiche seulement la liste)
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import excalidraw_anim as ex  # noqa: E402
import render_primitive as rp  # noqa: E402
import schema_anim as sa  # noqa: E402

ROOT_VARS = ("--blanc:#F4F6F9;--bleu:#5B9CF6;--vert:#6FDC8C;--or:#F0B429;--rouge:#E5484D;--gris:#9AA4B2;"
             "--bleu-clair:#A9C7F5;--ombre:rgba(0,0,0,.6);--halo-bleu:rgba(91,156,246,.75);--halo-vert:rgba(111,220,140,.7);"
             "--halo-or:rgba(240,180,41,.75);--halo-rouge:rgba(229,72,77,.75)")


def page_html(schema, uid="prev"):
    """La page d'aperçu : le schéma entier, tout montré, sur le fond de la vidéo."""
    allk = {("n", n["i"]) for n in schema.nodes} | {("e", e["i"]) for e in schema.edges}
    return ('<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><style>:root{%s}html,body{margin:0;background:#05070b;'
            'width:1920px;height:1080px;overflow:hidden;font-family:Verdana,Geneva,sans-serif}.stage-wrap{position:absolute;'
            'inset:0}%s</style></head><body><div class="stage-wrap">%s</div></body></html>'
            % (ROOT_VARS, rp.CSS_EXT, schema.stage_html(uid, allk, hidden_until_shown=False)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Aperçu thématisé d'un schéma Excalidraw + liste des éléments à citer.")
    ap.add_argument("file")
    ap.add_argument("--id", default=None, help="identifiant du schéma (défaut : nom du fichier)")
    ap.add_argument("--title", default="")
    ap.add_argument("--html", action="store_true", help="écrire aussi la page HTML")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv)

    path = Path(a.file)
    try:
        schema = ex.load_schema(path, a.id or path.stem.split(".")[0], a.title)
    except sa.SchemaError as exc:
        print("erreur : %s" % exc, file=sys.stderr)
        sys.exit(1)
    handles = schema.handles()
    print(handles)
    if a.no_write:
        return schema
    stem = path.with_suffix("")
    hp = stem.parent / (stem.name + ".handles.md")
    hp.write_text(handles, encoding="utf-8")
    print("écrit : %s" % hp)
    html = page_html(schema)
    if a.html:
        hh = stem.parent / (stem.name + ".preview.html")
        hh.write_text(html, encoding="utf-8")
        print("écrit : %s" % hh)
    png = stem.parent / (stem.name + ".preview.png")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        tmp = stem.parent / (stem.name + ".preview.html")
        tmp.write_text(html, encoding="utf-8")
        print("Playwright absent : ouvrir %s dans un navigateur pour voir le schéma (1920 × 1080)" % tmp)
        return schema
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": sa.W, "height": sa.H})
        pg.set_default_timeout(20000)
        pg.set_content(html)
        pg.wait_for_timeout(150)
        pg.screenshot(path=str(png))
        br.close()
    print("écrit : %s  ← à regarder avant de valider" % png)
    return schema


if __name__ == "__main__":
    main()
