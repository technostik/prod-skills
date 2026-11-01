#!/usr/bin/env python3
"""Génère des sons procéduraux très courts (stdlib uniquement) dans assets/sfx/.
- pop-a/b/c : blips à 3 hauteurs (alternés à chaque item de liste -> jamais le même son 2x de suite)
- tick : micro-clic pour compteurs/barres/grille (discret)
- chime : carillon doux 2 notes pour les punchlines (moments clés uniquement)
Niveaux bas par construction (pics ~0.5) ; le JS joue à volume 0.10-0.16 + bouton Mute.
Usage: python3 scripts/make-sfx.py
"""
import math
import struct
import wave
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"
OUT.mkdir(parents=True, exist_ok=True)
SR = 44100


def tone(freq0, freq1, dur, vol=0.5, attack=0.005):
    n = int(SR * dur)
    frames = []
    for i in range(n):
        t = i / SR
        k = i / max(n - 1, 1)
        f = freq0 + (freq1 - freq0) * k
        env = min(t / attack, 1.0) * math.exp(-4.0 * k)
        frames.append(int(32767 * vol * env * math.sin(2 * math.pi * f * t)))
    return frames


def mix(*layers):
    n = max(len(l) for l in layers)
    out = [0] * n
    for l in layers:
        for i, v in enumerate(l):
            out[i] += v
    peak = max(abs(v) for v in out) or 1
    return [int(v / peak * 16000) for v in out]


def save(name, frames):
    p = OUT / name
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(struct.pack("<%dh" % len(frames), *frames))
    print(f"{name}: {len(frames)/SR:.2f}s")


save("pop-a.wav", tone(560, 470, 0.09))
save("pop-b.wav", tone(680, 570, 0.09))
save("pop-c.wav", tone(810, 690, 0.09))
save("tick.wav", tone(1250, 1100, 0.05, vol=0.35))
save("chime.wav", mix(tone(880, 880, 0.45, vol=0.4), tone(1318.5, 1318.5, 0.5, vol=0.25)))
