#!/usr/bin/env python3
"""Tests de scripts/detect-cast.py sur des vidéos synthétiques (FFmpeg, dossier temporaire).

Usage : python3 scripts/test-detect-cast.py
Sortie 0 si tout passe. Aucun fichier du projet n'est touché.
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("detect_cast", HERE / "detect-cast.py")
dc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dc)

W, H, FPS = 1920, 1080, 30
# Même encodage que clean-posthoc.py (libx264 veryfast crf 20) ; « dur » = compression sévère.
ENC_CLEAN = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
ENC_HARD = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "35", "-pix_fmt", "yuv420p", "-g", "7"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def make(path, dur, band=(), extra="", enc=ENC_CLEAN, size=(W, H)):
    """Image de fond animée + « webcam » incrustée ; `band` = [(t0, t1)] → filet vert 10 px."""
    w, h = size
    k = h / 1080.0
    vf = "testsrc2=size=%dx%d:rate=%d:duration=%s,format=yuv420p" % (w, h, FPS, dur)
    vf += ",drawbox=x=%d:y=%d:w=%d:h=%d:color=black@1:t=fill" % (w * 3 // 4, h * 3 // 4, w // 5, h // 5)
    if extra:
        vf += "," + extra
    if band:
        en = "+".join("between(t,%s,%s)" % b for b in band)
        vf += ",drawbox=x=0:y=0:w=iw:h=%d:color=0x00FF00:t=fill:enable='%s'" % (round(10 * k), en)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", vf, *enc, str(path)], check=True)


def detect(path, tmp):
    out = Path(tmp) / (Path(path).stem + ".json")
    before = sha(path)
    assert dc.main([str(path), "--output", str(out), "--quiet"]) == 0
    assert sha(path) == before, "le média source a été modifié"
    assert not list(Path(tmp).glob("*.tmp")), "fichier temporaire résiduel"
    return json.loads(out.read_text(encoding="utf-8"))


FAILS = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  ECHEC ") + name + ("" if cond else "  -> " + str(detail)))
    if not cond:
        FAILS.append(name)


def near(seg, t0, t1, tol=0.1):
    return abs(seg["start"] - t0) <= tol and abs(seg["end"] - t1) <= tol


def main():
    with tempfile.TemporaryDirectory(prefix="detect-cast-") as tmp:
        tmp = Path(tmp)

        print("1. webcam sans filet")
        make(tmp / "t1.mkv", 8)
        d = detect(tmp / "t1.mkv", tmp)
        check("aucun intervalle, JSON valide", d["segments"] == [] and d["version"] == 1, d["segments"])

        print("2. filet continu")
        make(tmp / "t2.mkv", 10, band=[(2, 7)])
        d = detect(tmp / "t2.mkv", tmp)
        check("un intervalle [2, 7)", len(d["segments"]) == 1 and near(d["segments"][0], 2, 7), d["segments"])
        s = d["segments"][0]
        check("bornes en images cohérentes",
              abs(s["start_frame"] - 2 * FPS) <= 2 and abs(s["end_frame"] - 7 * FPS) <= 2, s)
        check("métadonnées source",
              d["width"] == W and d["height"] == H and d["fps"] == FPS and d["source_size"] == (tmp / "t2.mkv").stat().st_size
              and abs(d["duration"] - 10) < 0.2, d)

        print("3. deux séquences")
        make(tmp / "t3.mkv", 14, band=[(1, 4), (8, 12)])
        d = detect(tmp / "t3.mkv", tmp)
        check("deux intervalles", len(d["segments"]) == 2 and near(d["segments"][0], 1, 4)
              and near(d["segments"][1], 8, 12), d["segments"])

        print("4. filet qui apparaît et disparaît, avec clignotement")
        # trou de 2 images (0,067 s) à l'intérieur de la 1re séquence : doit être comblé
        make(tmp / "t4.mkv", 12, band=[(1, 3), (3.067, 5), (8, 9)])
        d = detect(tmp / "t4.mkv", tmp)
        check("clignotement comblé, 2 intervalles", len(d["segments"]) == 2 and near(d["segments"][0], 1, 5)
              and near(d["segments"][1], 8, 9), d["segments"])
        make(tmp / "t4b.mkv", 8, band=[(3, 3.1)])
        d = detect(tmp / "t4b.mkv", tmp)
        check("micro-détection (0,1 s) ignorée", d["segments"] == [], d["segments"])

        print("5. faux positifs : vert dans la capture")
        extra = ("drawbox=x=200:y=300:w=900:h=500:color=0x00FF00:t=fill,"            # aplat vert au milieu
                 "drawbox=x=0:y=60:w=iw:h=12:color=0x00FF00:t=fill,"                # bande verte non collée au bord
                 "drawbox=x=0:y=0:w=500:h=10:color=0x00FF00:t=fill")                # filet partiel (26 % de la largeur)
        make(tmp / "t5.mkv", 8, extra=extra)
        d = detect(tmp / "t5.mkv", tmp)
        check("aucun faux positif", d["segments"] == [], d["segments"])
        make(tmp / "t5b.mkv", 8, extra="drawbox=x=0:y=0:w=iw:h=200:color=0x00FF00:t=fill")  # écran vert plein haut
        d = detect(tmp / "t5b.mkv", tmp)
        check("grand aplat vert depuis le bord rejeté (trop épais)", d["segments"] == [], d["segments"])
        make(tmp / "t5c.mkv", 10, band=[(2, 6)], extra="drawbox=x=200:y=300:w=900:h=500:color=0x00FF00:t=fill")
        d = detect(tmp / "t5c.mkv", tmp)
        check("filet vrai + contenu vert : un seul intervalle", len(d["segments"]) == 1 and near(d["segments"][0], 2, 6),
              d["segments"])

        print("6. compression sévère autour du filet")
        make(tmp / "t6.mkv", 10, band=[(2, 6)], enc=ENC_HARD)
        d = detect(tmp / "t6.mkv", tmp)
        check("intervalle [2, 6) malgré crf 35", len(d["segments"]) == 1 and near(d["segments"][0], 2, 6, 0.15),
              d["segments"])

        print("7. réencodage H.264 façon clean-posthoc (source encodée, puis réencodée)")
        make(tmp / "t7a.mkv", 10, band=[(2, 6)], enc=["-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p"])
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / "t7a.mkv"),
                        "-filter_complex", "[0:v]trim=start=0.000:end=4.000,setpts=PTS-STARTPTS[v0];"
                                           "[0:v]trim=start=4.500:end=10.000,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0[v]",
                        "-map", "[v]", *ENC_CLEAN, str(tmp / "t7.mkv")], check=True)
        d = detect(tmp / "t7.mkv", tmp)
        # le filet couvrait [2, 6) ; après retrait de [4, 4.5) il couvre [2, 5.5)
        check("intervalle après coupe : [2, 5.5)", len(d["segments"]) == 1 and near(d["segments"][0], 2, 5.5, 0.15),
              d["segments"])

        print("8. autre résolution (1280×720)")
        make(tmp / "t8.mkv", 8, band=[(2, 5)], size=(1280, 720))
        d = detect(tmp / "t8.mkv", tmp)
        check("détecté en 720p", len(d["segments"]) == 1 and near(d["segments"][0], 2, 5) and d["height"] == 720,
              d["segments"])

        print("9. pas de découpage, pas de modification")
        check("seul le JSON est écrit à côté des vidéos",
              sorted(p.suffix for p in tmp.iterdir() if p.suffix not in (".json", ".mkv")) == [], list(tmp.iterdir()))

    print()
    if FAILS:
        print("ÉCHEC : %d test(s) : %s" % (len(FAILS), ", ".join(FAILS)))
        return 1
    print("OK : tous les tests passent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
