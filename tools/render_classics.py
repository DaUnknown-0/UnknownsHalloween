# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# render_classics.py - vier gemeinfreie Gruselklassiker, SELBST aus den Noten gerendert (Idee D5, 2026-10-20).
#
# Gemeinfrei sind die Kompositionen, nicht jede Aufnahme: hier wird nichts heruntergeladen und keine Aufnahme
# benutzt. Die Noten stehen unten in einer kleinen Notenschrift, gespielt von dem Software-Synthesizer, mit dem auch
# die UTS-Draft-Musik entstand (Assets/MusicGen/synth.py und instruments.py, nur importiert, nicht veraendert),
# plus ein paar eigenen Klaengen (Pfeifenorgel, Harfe, Xylophon, Becken, Oboe).
#
#   danse_macabre.ogg   Saint-Saens, Danse macabre op. 40 (1874), g-Moll 3/8: Mitternacht (12 Harfenschlaege auf D),
#                       der Tod stimmt die Geige (Tritonus A/Es), Walzer, Xylophon-Knochen, Dies irae, Hahnenschrei
#   bald_mountain.ogg   Mussorgsky, Eine Nacht auf dem kahlen Berge (1867), d-Moll: wirbelnde Streicher, Blechchoral,
#                       Hexensabbat-Ostinato, Glocke und Floete im Morgengrauen
#   toccata.ogg         Bach, Toccata und Fuge d-Moll BWV 565: die drei Eroeffnungsrufe, verminderter Septakkord ueber
#                       dem Orgelpunkt, Laufwerk, Fugenthema, Schlusskadenz (Orgel)
#   mountain_king.ogg   Grieg, In der Halle des Bergkoenigs (Peer Gynt op. 23/46), h-Moll: das Thema viermal, jedes
#                       Mal dichter besetzt (Pizzicato/Fagott bis Tutti). Gleichmaessiges Tempo: das Schneller-Werden
#                       besorgt UTS ueber AudioSource.pitch nach der Restzeit der Sabotage (Flag "tempo").
#
# Notenschrift: "A5:1/8 G5 A5:2 r:1/2 C#5+E5:1" - Ton:Dauer in Vierteln (Bruch erlaubt), die Dauer gilt weiter bis zur
# naechsten Angabe, "r" = Pause, "+" = Akkord, "|" ist nur Lesehilfe.
#
# Alle Stuecke schleifen nahtlos (Song.render faltet den Nachhall an den Anfang).
#   python render_classics.py [ausgabe_ordner] [stueck ...]      Standard: ../Resources/hw2026/music

import math
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "Assets" / "MusicGen"))
import instruments as I                                                       # noqa: E402
from synth import (SR, Song, adsr, bp, compress, decay, hp, limit, lp, mtof, noise, pulse, reverb, saturate,   # noqa: E402
                   sine, tri)

PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "E#": 5, "F": 5, "F#": 6, "Gb": 6, "G": 7,
      "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": -1}


def note(name):
    i = 2 if len(name) > 2 and name[1] in "#b" else 1
    return 12 * (int(name[i:]) + 1) + PC[name[:i]]


def seq(text):
    """Notenschrift -> [(Schlag, Dauer, [midi])], Schlag ab 0."""
    out, beat, last = [], 0.0, 1.0
    for tok in text.replace("|", " ").split():
        name, _, d = tok.partition(":")
        if d:
            last = float(Fraction(d))
        if name != "r":
            out.append((beat, last, [note(x) for x in name.split("+")]))
        beat += last
    return out, beat


class Score:
    """Ein Stueck auf einer durchgehenden Zeitachse in Vierteln (keine Takte noetig)."""

    def __init__(self, bpm, beats, seed=1):
        self.song = Song(bpm, int(math.ceil(beats / 4.0)), seed=seed)
        self.spb = self.song.spb
        self.rng = np.random.default_rng(seed + 7)

    def track(self, name, gain, fx=None, human=0.0):
        self.song.track(name, gain, fx, human)

    def play(self, track, inst, start, text, vel=0.7, pan=0.0, tr=0, legato=0.95, **kw):
        """Spielt eine Stimme ab Schlag start; liefert den Schlag hinter der letzten Note."""
        notes, end = seq(text)
        for beat, dur, ms in notes:
            for m in ms:
                w = inst(mtof(m + tr), dur * self.spb * legato, v=vel, **kw)
                self.song.add(track, 0, start + beat, w, pan=pan)
        return start + end

    def hit(self, track, beat, wave, pan=0.0, gain=1.0):
        self.song.add(track, 0, beat, wave, pan=pan, gain=gain)

    def render(self, master):
        return self.song.render(master)


def bus(wet=0.25, seconds=2.2, damp=6000):
    return lambda y: reverb(y, seconds, wet, damp=damp) if wet else y


def master_chain(warm=1.1):
    def m(y):
        y = hp(y, 30)
        y = compress(y, -18, 2.2, 0.01, 0.2)
        return limit(saturate(y, warm), -1.0)
    return m


def finish(y, target_db=-17.0, ceil_db=-1.0):
    rms = math.sqrt(float(np.mean(y.astype(np.float64) ** 2))) + 1e-9
    y = y * (10 ** (target_db / 20) / rms)
    c = 10 ** (ceil_db / 20)
    knee = 0.7 * c
    a = np.abs(y)
    over = a > knee
    y[over] = np.sign(y[over]) * (knee + (c - knee) * np.tanh((a[over] - knee) / (c - knee)))
    return y.astype(np.float32)


# ====================================================================== eigene Klaenge

def _n(dur, rel):
    return int((dur + rel) * SR)


def pipe_organ(f, dur, v=0.6, r=0.35, stops=(1.0, 0.75, 0.32, 0.5, 0.22, 0.16), sub=0.0):
    """Pfeifenorgel: 8' 4' 2 2/3' 2' 1 3/5' 1' (additiv), Anblasgeraeusch, kein Leslie; sub = 16'."""
    n = _n(dur, r)
    ratios = (1, 2, 3, 4, 5, 8)
    y = np.zeros(n)
    for g, k in zip(stops, ratios):
        if f * k < 12000:
            y += g * sine(f * k, n, ph0=0.13 * k)
    if sub:
        y += sub * sine(f * 0.5, n)
    y /= (sum(stops) + sub)
    rng = np.random.default_rng(int(f * 7) % 991)
    chiff = bp(noise(n, rng), min(8000.0, f * 3), 1.5) * decay(n, 0.05) * 0.35
    return (y + chiff) * adsr(n, 0.025, 0.05, 0.95, r, gate=dur) * v


def harp(f, dur=0.5, v=0.6):
    n = int(2.6 * SR)
    y = 0.75 * tri(f, n) + 0.35 * sine(f * 2, n) * decay(n, 0.6) + 0.12 * sine(f * 3, n) * decay(n, 0.25)
    y = lp(y, min(5000.0, f * 8))
    return y * decay(n, 2.2) * adsr(n, 0.002, 0.0, 1.0, 0.01, gate=2.59) * v * 0.7


def xylophone(f, dur=0.2, v=0.6):
    """Xylophon: harter Holzanschlag, kurzer Ton, der 3,9-fache Teilton klingt sofort ab."""
    n = int(0.6 * SR)
    y = sine(f, n) * decay(n, 0.35) + 0.5 * sine(f * 3.93, n) * decay(n, 0.06) + 0.25 * sine(f * 9.2, n) * decay(n, 0.02)
    rng = np.random.default_rng(int(f) % 211)
    y[:int(0.006 * SR)] += 0.4 * lp(noise(int(0.006 * SR), rng), 6000)
    return y * v * 0.6


def oboe(f, dur, v=0.6, r=0.1):
    """Oboe: schmale Pulswelle, naeselnde Formanten, schnelles Vibrato."""
    from synth import peak
    n = _n(dur, r)
    t = np.arange(n) / SR
    freq = f * 2 ** (8 / 1200 * np.clip((t - 0.2) / 0.3, 0, 1) * np.sin(2 * math.pi * 5.8 * t))
    y = pulse(freq, n, 0.22)
    y = peak(lp(hp(y, 400), 4200), 1400, 8.0, 1.6)
    return y * adsr(n, 0.03, 0.1, 0.85, r, gate=dur) * v * 0.32


def violin(f, dur, v=0.6, a=0.06, r=0.25):
    """Solo-Geige: eine Stimme (statt vier im Satz), staerkeres Vibrato, Bogengeraeusch."""
    from synth import peak, saw
    n = _n(dur, r)
    t = np.arange(n) / SR
    freq = f * 2 ** (14 / 1200 * np.clip((t - 0.12) / 0.25, 0, 1) * np.sin(2 * math.pi * 5.6 * t))
    y = saw(freq, n)
    y = peak(peak(lp(hp(y, 250), 5200), 2600, 5.0, 1.2), 600, 3.0, 1.0)
    rng = np.random.default_rng(int(f) % 131)
    y += 0.04 * bp(noise(n, rng), 3500, 1.0)
    return y * adsr(n, a, 0.2, 0.85, r, gate=dur) * v * 0.45


def tremolo(inst, rate=13.0):
    def w(f, dur, v=0.5, **kw):
        y = inst(f, dur, v=v, **kw)
        t = np.arange(len(y)) / SR
        return y * (0.65 + 0.35 * np.sin(2 * math.pi * rate * t))
    return w


def cymbal(v=0.6, length=3.0, rng=None):
    rng = rng or np.random.default_rng(5)
    n = int(length * SR)
    y = hp(noise(n, rng), 4500) + 0.4 * bp(noise(n, rng), 7000, 0.8)
    return y * decay(n, length) * adsr(n, 0.003, 0.0, 1.0, 0.01, gate=length - 0.01) * v * 0.5


def bass_drum(v=0.8):
    return I.kick(v, 0.9, 90, 38, 0.1)


def tubular_bell(f, dur=2.0, v=0.6):
    return I.bell(f, dur, v, r=3.5, ratio=2.76)


# ====================================================================== 1 Danse macabre (Saint-Saens)
# 3/8, eine Achtel = ein Schlag der Zeitachse (bpm 176 -> Takt ~1 s). g-Moll.
def danse_macabre():
    E = 1.0                      # eine Achtel
    BAR = 3 * E
    bars_total = 84
    sc = Score(176, bars_total * BAR, seed=31)
    sc.track("harp", 0.55, bus(0.35, 2.8))
    sc.track("pad", 0.22, bus(0.4, 3.0))
    sc.track("fiddle", 0.55, bus(0.3, 2.4))
    sc.track("pizz", 0.55, bus(0.25, 1.8))
    sc.track("flute", 0.6, bus(0.32, 2.6))
    sc.track("xylo", 0.55, bus(0.22, 1.6))
    sc.track("winds", 0.5, bus(0.3, 2.4))
    sc.track("strings", 0.32, bus(0.32, 2.6))
    sc.track("brass", 0.32, bus(0.3, 2.4))
    sc.track("perc", 0.5, bus(0.3, 2.0))

    b = 0.0
    # --- Mitternacht: zwoelf Harfenschlaege auf D, darunter leise Streicher (12 Takte)
    for k in range(12):
        sc.play("harp", harp, b + k * BAR, "D4+D3:3", vel=0.75)
    sc.play("pad", I.strings, b, "D3+A3:18 | Eb3+A3:18", vel=0.35, a=1.2, r=1.5)
    b += 12 * BAR

    # --- der Tod stimmt die Geige: Tritonus A/Es, dann D/A, ueber leisem Pizzicato (8 Takte)
    fid = "A4+Eb5:2 A4+Eb5:1 | A4+Eb5:3 | D4+A4:2 D4+A4:1 | D4+A4:3 | " * 2
    sc.play("fiddle", violin, b, fid, vel=0.8, legato=0.9)
    for k in range(8):
        sc.play("pizz", I.pizz, b + k * BAR, "G2:1", vel=0.7)
    b += 8 * BAR

    # --- der Walzer: Begleitung (Bass auf 1, Akkord auf 2 und 3), Thema in der Floete (16 Takte)
    prog = ["G2", "G2", "D2", "D2", "G2", "G2", "C3", "D2"] * 2
    chords = {"G2": "Bb3+D4", "D2": "A3+C4+F#4", "C3": "C4+Eb4+G4"}

    def waltz_acc(start, bars, vel=0.6):
        for k in range(bars):
            root = prog[k % len(prog)]
            sc.play("pizz", I.pizz, start + k * BAR, f"{root}:1 {chords[root]}:1 {chords[root]}:1", vel=vel)

    theme = ("D5:2 D5:1 | D5:2 D5:1 | Eb5:1 D5:1 C5:1 | Bb4:2 A4:1 | G4:2 A4:1 | Bb4:2 C5:1 | D5:3 | A4:3 | "
             "D5:2 D5:1 | D5:2 D5:1 | Eb5:1 D5:1 C5:1 | Bb4:2 A4:1 | G4:2 F#4:1 | G4:1 A4:1 Bb4:1 | G4:3 | r:3")
    waltz_acc(b, 16)
    sc.play("flute", I.flute, b, theme, vel=0.75, legato=0.9)
    b += 16 * BAR

    # --- die Knochen: dasselbe Thema im Xylophon, die Geige darunter (16 Takte)
    waltz_acc(b, 16, 0.65)
    sc.play("xylo", xylophone, b, theme, vel=0.85, tr=12, legato=0.5)
    sc.play("fiddle", violin, b, "G4:6 | A4:6 | Bb4:6 | A4:6 | G4:6 | A4:6 | D4:6 | G4:6", vel=0.5)
    b += 16 * BAR

    # --- Dies irae in den Holzblaesern (8 Takte, je ein Ton pro Takt)
    waltz_acc(b, 8, 0.5)
    sc.play("winds", I.bassoon, b, "Bb3:3 A3:3 Bb3:3 G3:3 A3:3 F3:3 G3:3 G3:3", vel=0.8, legato=0.92)
    sc.play("winds", I.clarinet, b, "Bb4:3 A4:3 Bb4:3 G4:3 A4:3 F4:3 G4:3 G4:3", vel=0.55, legato=0.92)
    b += 8 * BAR

    # --- Tutti: Thema in den Streichern und im Blech, Becken (16 Takte)
    waltz_acc(b, 16, 0.85)
    sc.play("strings", I.strings, b, theme, vel=0.75, legato=0.85, a=0.03, r=0.25)
    sc.play("strings", I.strings, b, theme, vel=0.55, tr=-12, legato=0.85, a=0.03, r=0.25)
    sc.play("brass", I.brass, b, "G3+D4:3 | G3+D4:3 | A3+D4:3 | G3+D4:3 | G3+Bb3:3 | G3+C4:3 | F#3+A3:3 | F#3+A3:3 | "
                                 "G3+D4:3 | G3+D4:3 | A3+D4:3 | G3+D4:3 | Eb3+G3:3 | D3+F#3:3 | G3+Bb3:3 | r:3", vel=0.6)
    for k in (0, 8):
        sc.hit("perc", b + k * BAR, cymbal(0.7))
    for k in range(16):
        sc.hit("perc", b + k * BAR, I.timpani(mtof(note(prog[k % len(prog)])), 0.6, 1.0))
    sc.play("xylo", xylophone, b, theme, vel=0.6, tr=12, legato=0.5)
    b += 16 * BAR

    # --- Morgengrauen: der Hahn (Oboe), die Geige verklingt, dann wieder Mitternacht (8 Takte)
    sc.play("winds", oboe, b, "r:1 A5:1/2 E6:5/2 | r:3", vel=0.75)
    sc.play("fiddle", violin, b + 2 * BAR, "D5:3 | Bb4:3 | A4:3 | G4:6 | r:3", vel=0.35)
    sc.play("pad", I.strings, b + 2 * BAR, "G3+D4:15", vel=0.3, a=0.8, r=2.0)
    sc.play("harp", harp, b + 6 * BAR, "G2+D3+G3:3", vel=0.5)
    return sc.render(master_chain())


# ====================================================================== 2 Night on Bald Mountain (Mussorgsky)
def bald_mountain():
    bars = 36
    sc = Score(144, bars * 4, seed=41)
    sc.track("whirl", 0.38, bus(0.28, 2.0))
    sc.track("trem", 0.32, bus(0.25, 2.0))
    sc.track("brass", 0.45, bus(0.3, 2.6))
    sc.track("low", 0.5, bus(0.2, 1.8))
    sc.track("winds", 0.4, bus(0.3, 2.2))
    sc.track("perc", 0.55, bus(0.28, 2.2))
    sc.track("dawn", 0.36, bus(0.45, 3.5))

    whirl = "A5:1/4 Bb5 A5 G#5 " * 4
    rush = "D5:1/4 E5 F5 G5 A5 Bb5 C#6 D6 E6 F6 E6 D6 C#6 Bb5 A5 G5 "

    b = 0.0
    # --- A: wirbelnde Streicher ueber dem Tremolo, Schreie der Holzblaeser, ab Takt 5 der Blechchoral (16 Takte)
    for k in range(16):
        txt = rush if k % 4 == 3 else whirl
        sc.play("whirl", I.strings, b + 4 * k, txt, vel=0.5, a=0.01, r=0.08, legato=0.9, tr=0 if k < 8 else 5)
    sc.play("trem", tremolo(I.strings), b, "D2+A2:16 | D2+A2:16 | G2+D3:16 | A2+E3:16", vel=0.6, a=0.05)
    for k in (2, 6, 10, 14):
        sc.play("winds", I.flute, b + 4 * k + 2, "D7:1/8 C#7 Bb6 A6 G6 F6 E6 D6", vel=0.45, legato=0.8)
    choral = ("D3:2 D3:1 Eb3:1 | D3:2 C#3:2 | D3:1 F3:1 E3:1 D3:1 | C#3:2 A2:2 | "
              "Bb2:2 A2:1 G#2:1 | A2:4 | D3:1 C3:1 Bb2:1 A2:1 | D3:4 | "
              "D3:2 D3:1 Eb3:1 | D3:2 C#3:2 | F3:1 G3:1 A3:1 Bb3:1 | A3:4")
    sc.play("brass", I.brass, b + 16, choral, vel=0.8, legato=0.9)
    sc.play("brass", I.tuba, b + 16, choral, vel=0.8, tr=-12, legato=0.9)
    for k in (4, 8, 12):
        sc.hit("perc", b + 4 * k, I.timpani(mtof(38), 0.8, 1.6))
    b += 16 * 4

    # --- B: Hexensabbat, Ostinato der tiefen Streicher, Hoerner auf den Gegenschlaegen (8 Takte)
    ost = "D3:1/2 D3 A2 A2 Bb2 Bb2 A2 A2 "
    for k in range(8):
        sc.play("low", I.bassoon, b + 4 * k, ost, vel=0.85, legato=0.6)
        sc.play("low", I.pizz, b + 4 * k, ost, vel=0.6, tr=-12)
        sc.play("brass", I.brass, b + 4 * k, "r:1/2 D4+F4:1/2 r:1/2 D4+F4:1/2 r:1/2 D4+G4:1/2 r:1/2 C#4+E4:1/2", vel=0.5, legato=0.7)
        sc.hit("perc", b + 4 * k, I.timpani(mtof(38), 0.7, 0.9))
        sc.hit("perc", b + 4 * k + 2, I.timpani(mtof(33), 0.6, 0.9))
        txt = whirl if k % 2 == 0 else "D6:1/4 Eb6 D6 C#6 " * 4
        sc.play("whirl", I.strings, b + 4 * k, txt, vel=0.42, a=0.01, r=0.08, legato=0.9)
    b += 8 * 4

    # --- C: Hoehepunkt, Choral im Tutti, Becken (8 Takte)
    climax = "D3:2 D3:1 Eb3:1 | D3:2 C#3:2 | F3:1 G3:1 A3:1 Bb3:1 | A3:4 | Bb3:2 A3:1 G#3:1 | A3:2 E3:2 | D3:4 | D3:4"
    sc.play("brass", I.brass, b, climax, vel=0.95, legato=0.92)
    sc.play("brass", I.brass, b, climax, vel=0.7, tr=12, legato=0.92)
    sc.play("brass", I.tuba, b, climax, vel=0.9, tr=-12, legato=0.92)
    for k in range(8):
        sc.play("whirl", I.strings, b + 4 * k, rush if k % 2 else whirl.replace("5", "6"), vel=0.5, a=0.01, r=0.08)
        sc.hit("perc", b + 4 * k, I.timpani(mtof(38), 0.9, 1.2))
    sc.play("trem", tremolo(I.strings), b, "D2+A2+D3:32", vel=0.7, a=0.05)
    for k in (0, 4, 7):
        sc.hit("perc", b + 4 * k, cymbal(0.75))
    sc.hit("perc", b + 30, bass_drum(0.9))
    b += 8 * 4

    # --- Morgengrauen: Kirchenglocke, Floete, Harfe (4 Takte), dann beginnt die Nacht von vorn
    for k in range(4):
        sc.hit("dawn", b + 4 * k, tubular_bell(mtof(62), 2.5, 0.55))
    sc.play("dawn", I.flute, b + 1, "F#5:2 A5:1 G5:1 | F#5:2 E5:2 | D5:4", vel=0.55)
    sc.play("dawn", harp, b, "D3:1 A3 D4 F#4 A4 D5 F#4 A3 D3:1 A3 D4 F#4 A4 D5 F#4 A3", vel=0.4)
    sc.play("trem", I.strings, b, "D3+F#3+A3:14", vel=0.2, a=1.0, r=1.5)
    return sc.render(master_chain())


# ====================================================================== 3 Toccata d-Moll BWV 565 (Bach)
def toccata():
    sc = Score(72, 88, seed=51)
    sc.track("man", 0.5, bus(0.45, 4.8, 5000))
    sc.track("ped", 0.55, bus(0.45, 4.8, 3500))

    def call(start, tr):
        txt = "A5:1/8 G5 A5:2 r:1/2 G5:1/8 F5 E5 D5 C#5:3/2 D5:3 r:1"
        sc.play("man", pipe_organ, start, txt, vel=0.75, tr=tr, legato=0.98)
        return sc.play("man", pipe_organ, start, txt, vel=0.6, tr=tr - 12, legato=0.98)

    b = 0.0
    b = call(b, 0)
    b = call(b, -12)
    end3 = call(b, -24)
    sc.play("ped", pipe_organ, b + 5.0, "D2:4", vel=0.8, sub=0.6)          # das Pedal kommt unter dem dritten D
    b = end3

    # verminderter Septakkord, Ton fuer Ton aufgebaut ueber dem Orgelpunkt D, dann d-Moll
    sc.play("ped", pipe_organ, b, "D2:8", vel=0.85, sub=0.8)
    arp = ["C#3", "E3", "G3", "Bb3", "C#4", "E4", "G4", "Bb4"]
    for k, nm in enumerate(arp):
        sc.play("man", pipe_organ, b + k * 0.25, f"{nm}:{4 - k * 0.25}", vel=0.55)
    sc.play("man", pipe_organ, b + 4, "D3+F3+A3+D4+F4+A4:3", vel=0.7)
    b += 8

    # Laufwerk: Kaskaden in d-Moll ueber dem Orgelpunkt
    casc = "A5:1/6 G5 A5 F5 G5 E5 F5 D5 E5 C#5 D5 A4 "
    sc.play("ped", pipe_organ, b, "D2:12", vel=0.75, sub=0.7)
    x = b
    for tr in (0, -12):
        x = sc.play("man", pipe_organ, x, casc * 2, vel=0.55, tr=tr, legato=1.0)
    x = sc.play("man", pipe_organ, x, "D4:1/6 E4 F4 G4 A4 Bb4 C#5 D5 E5 F5 G5 A5 Bb5 A5 G5 F5 E5 D5 C#5 D5 E5 C#5 A4 D5:1", vel=0.58, legato=1.0)
    b = max(b + 12, x) + 1

    # Fuge: Thema (mit dem wiederholten A), Antwort eine Quarte hoeher, dann im Pedal
    subj = ("A4:1/4 G4 A4 E4 A4 F4 A4 D4 A4 E4 A4 C#4 A4 D4 A4 E4 "
            "A4 F4 A4 G4 A4 E4 A4 F4 A4 D4 A4 E4 A4 C#4 A4 D4")
    sc.play("man", pipe_organ, b, subj, vel=0.55, legato=0.9, stops=(1.0, 0.6, 0.25, 0.35, 0.1, 0.08))
    b2 = sc.play("man", pipe_organ, b + 8, subj, vel=0.55, tr=5, legato=0.9, stops=(1.0, 0.6, 0.25, 0.35, 0.1, 0.08))
    sc.play("man", pipe_organ, b + 8, "D4:2 C4:2 Bb3:2 A3:2 G3:2 A3:2 Bb3:2 A3:2", vel=0.4)
    sc.play("ped", pipe_organ, b + 16, subj, vel=0.75, tr=-24, legato=0.9, sub=0.6)
    sc.play("man", pipe_organ, b + 16, "F4+A4:2 E4+G4:2 D4+F4:2 C#4+E4:2 D4+F4:2 E4+G4:2 F4+A4:2 E4+A4:2", vel=0.45)
    b = b2 + 8

    # Schluss: der Ruf noch einmal im vollen Werk, Kadenz g-Moll / A-Dur / d-Moll
    sc.play("man", pipe_organ, b, "A5:1/8 G5 A5:3/2 r:1/4 G5:1/8 F5 E5 D5 C#5:1 D5:3/2", vel=0.8)
    sc.play("man", pipe_organ, b, "A4:1/8 G4 A4:3/2 r:1/4 G4:1/8 F4 E4 D4 C#4:1 D4:3/2", vel=0.65)
    sc.play("ped", pipe_organ, b, "D2:4", vel=0.8, sub=0.8)
    b += 4.5
    sc.play("man", pipe_organ, b, "G3+Bb3+D4+G4:2 A3+C#4+E4+A4:2 D3+F3+A3+D4+F4:5", vel=0.75)
    sc.play("ped", pipe_organ, b, "G1:2 A1:2 D1:5", vel=0.85, sub=0.9)
    return sc.render(master_chain(1.05))


# ====================================================================== 4 In the Hall of the Mountain King (Grieg)
def mountain_king():
    sc = Score(152, 4 * 32 + 4, seed=61)
    sc.track("pizz", 0.6, bus(0.22, 1.6))
    sc.track("bsn", 0.55, bus(0.25, 1.8))
    sc.track("horn", 0.3, bus(0.35, 2.4))
    sc.track("str", 0.42, bus(0.25, 2.0))
    sc.track("wind", 0.4, bus(0.25, 2.0))
    sc.track("brass", 0.45, bus(0.28, 2.2))
    sc.track("perc", 0.55, bus(0.25, 2.0))

    theme = ("B3:1/2 C#4 D4 E4 F#4 D4 F#4:1 | F4:1/2 C#4 F4:1 E4:1/2 C4 E4:1 | B3:1/2 C#4 D4 E4 F#4 D4 F#4 B4 | A4 F#4 D4 F#4 A4:2 | "
             "F#4:1/2 G#4 A4 B4 C#5 A4 C#5:1 | C5:1/2 G#4 C5:1 B4:1/2 G4 B4:1 | F#4:1/2 G#4 A4 B4 C#5 A4 C#5 F#5 | E5 C#5 A4 C#5 E5:2")
    pulse_txt = ("B1:1 " * 16) + ("F#1:1 " * 16)

    b = 2.0
    sc.play("horn", I.brass, 0, "F#3:2", vel=0.3)                                 # zwei Schlaege Horn-Vorhang
    dyn = (0.42, 0.6, 0.8, 1.0)                                                   # p, mf, f, ff
    for k in range(4):
        s = b + 32 * k
        d = dyn[k]
        # Thema: 1 Pizzicato + Fagott tief, 2 Klarinette/Pizzicato hoch, 3 Streicher, 4 Tutti
        sc.play("pizz", I.pizz, s, theme, vel=0.9 * d, tr=-24)
        sc.play("bsn", I.bassoon, s, theme, vel=0.8 * d, tr=-12, legato=0.55)
        sc.play("pizz", I.pizz, s, pulse_txt, vel=0.6 * d, tr=12, legato=0.5)
        sc.play("horn", I.brass, s, "B2+F#3:16 F#2+C#3:16", vel=0.55 * d, legato=0.98)
        if k >= 1:
            sc.play("wind", I.clarinet, s, theme, vel=0.75 * d, legato=0.55)
            sc.play("pizz", I.pizz, s, theme, vel=0.8 * d)
        if k >= 2:
            sc.play("str", I.strings, s, theme, vel=0.6, legato=0.5, a=0.01, r=0.1)
            sc.play("str", I.strings, s, theme, vel=0.45, tr=12, legato=0.5, a=0.01, r=0.1)
            for q in range(0, 32, 2):
                sc.hit("perc", s + q, I.timpani(mtof(35 if q < 16 else 30), 0.55 + 0.1 * (k - 2), 0.6))
        if k >= 3:
            sc.play("brass", I.brass, s, theme, vel=0.8, tr=-12, legato=0.6)
            sc.play("brass", I.brass, s, "B3+D4+F#4:1/2 r:1/2 " * 16 + "F#3+A3+C#4:1/2 r:1/2 " * 16, vel=0.5, legato=0.6)
            sc.play("wind", I.flute, s, theme, vel=0.5, tr=12, legato=0.55)
            for q in range(32):
                sc.hit("perc", s + q, bass_drum(0.55))
            for q in (0, 16, 28, 30):
                sc.hit("perc", s + q, cymbal(0.65, 2.0))
    return sc.render(master_chain(1.15))


PIECES = {
    "danse_macabre": ("Danse Macabre", danse_macabre),
    "bald_mountain": ("Night on Bald Mountain", bald_mountain),
    "toccata": ("Toccata in D Minor", toccata),
    "mountain_king": ("In the Hall of the Mountain King", mountain_king),
}


def main(argv):
    out = Path(argv[0]) if argv else HERE.parent / "Resources" / "hw2026" / "music"
    out.mkdir(parents=True, exist_ok=True)
    want = argv[1:] or list(PIECES)
    for key in want:
        title, fn = PIECES[key]
        t0 = time.time()
        raw = fn()
        y = finish(raw)
        p = out / f"{key}.ogg"
        frames = np.ascontiguousarray(y.T)
        with sf.SoundFile(p, "w", SR, 2, format="OGG", subtype="VORBIS") as f:
            for i in range(0, len(frames), 16384):                         # libsndfile-Vorbis: grosse Bloecke = Stackueberlauf
                f.write(frames[i:i + 16384])

        def db(x):
            return 20 * math.log10(math.sqrt(float(np.mean(x.astype(np.float64) ** 2))) + 1e-9)
        seam = db(y[:, -2 * SR:]) - db(y[:, :2 * SR])
        print(f"{key:14s} {title:34s} {y.shape[1] / SR:5.1f} s  {p.stat().st_size / 1e6:4.2f} MB  "
              f"Naht {seam:+5.1f} dB  ({time.time() - t0:4.1f} s)")


if __name__ == "__main__":
    main(sys.argv[1:])
