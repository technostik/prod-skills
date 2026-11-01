#!/usr/bin/env python3
"""Serveur du studio : fichiers du projet + POST /prise -> $HF_VIDEOS_DIR (défaut ~/Vidéos).

Usage : python3 scripts/studio_server.py [port=8321]
  (lançable depuis N'IMPORTE QUEL répertoire : sert toujours la racine
  du projet = le parent de scripts/, pas le répertoire courant.)

La page studio*.html envoie la prise (webm) en fin d'enregistrement ;
elle est écrite dans $HF_VIDEOS_DIR (défaut ~/Vidéos)/prise-studio-AAAAMMJJ-HHMMSS.webm.
"""
import datetime
import functools
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

SAVE_DIR = os.path.expanduser(os.environ.get("HF_VIDEOS_DIR", "~/Vidéos"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8321
# Racine projet = parent de scripts/ (ce fichier vit dans <projet>/scripts/).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_POST(self):
        if self.path != "/prise":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if length <= 0 or length > 4 * 1024**3:
            self.send_error(400, "taille invalide")
            return
        os.makedirs(SAVE_DIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        nom = "prise-studio-%s.webm" % stamp
        dest = os.path.join(SAVE_DIR, nom)
        restant = length
        with open(dest, "wb") as f:
            while restant > 0:
                morceau = self.rfile.read(min(1024 * 1024, restant))
                if not morceau:
                    break
                f.write(morceau)
                restant -= len(morceau)
        corps = json.dumps({"ok": True, "path": dest,
                            "size": os.path.getsize(dest)}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)
        print("prise -> %s (%d octets)" % (dest, os.path.getsize(dest)), flush=True)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("racine : %s" % ROOT, flush=True)
    for f in sorted(os.listdir(ROOT)):
        if f.startswith("studio") and f.endswith(".html"):
            print("présentation : http://localhost:%d/%s?view=present" % (PORT, f), flush=True)
            print("prompteur     : http://localhost:%d/%s?view=prompteur" % (PORT, f), flush=True)
    print("prises -> %s" % SAVE_DIR, flush=True)
    srv.serve_forever()
