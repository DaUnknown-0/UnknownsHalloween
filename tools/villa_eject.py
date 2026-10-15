# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_eject.py - Regie der Rauswurf-Szenen auf Hollowmere Manor -> Resources/villa/villa_eject.json.
#
# Gleiches Format wie UnknownsAtlas/tools/eject_scenes.py (dort steht die Formatbeschreibung): Objekte mit
# Keyframes je Eigenschaft, Partikel-Emitter, Kamera, Ereignisse. Abgespielt von Villa/EjectEngine.cs
# (Spiel) und tools/villa_theater/index.html (Vorschau). Einheiten: 1 = 180 px der Grafik, Ursprung
# Bildmitte, y nach oben, sichtbar 11 x 6,2 bei Zoom 1. Die Grafik erzeugt gen_villa_eject.py.
#
# Stimmung: Horrorfilm-Set in einer Spukvilla, kalt und entsaettigt, Kerzen und Scheinwerfer als warme
# Inseln, Gewitter und Mondlicht. Vier Szenen mit Spieler, zwei Skip-Szenen ohne Spieler.
# Klaenge: nur die Namen, die die Engine synthetisiert (siehe SOUNDS).
#
#     python tools/villa_eject.py

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "Resources" / "villa" / "villa_eject.json"
SOUNDS = {"boom", "chime", "clack", "click", "creak", "fire", "grind", "growl", "organ", "owl", "pop", "rush",
          "sizzle", "slam", "splash", "step", "thud", "thunder", "twig", "whoosh", "zap"}
EASES = {"lin", "in", "out", "io", "back", "inback", "hold"}
PROPS = {"x", "y", "rot", "sx", "sy", "s", "a", "b", "flip", "arc"}


def key(t, ease="io", **p):
    return [t, p, ease]


def em(sprite, z, **kw):
    e = {"sprite": sprite, "z": z}
    e.update(kw)
    return e


def burst(sprite, z, t, n, **kw):
    return em(sprite, z, burst=t, n=n, **kw)


def ev(t, **kw):
    e = {"t": t}
    e.update(kw)
    return e


def steps(t0, t1, n, vol=0.2):
    """Schritte in gleichmaessigem Abstand."""
    return [ev(round(t0 + (t1 - t0) * k / max(1, n - 1), 2), sound="step", vol=vol) for k in range(n)]


GLOW, MOTE, PUFF, STREAK, DROP, RIPPLE, LEAF, FLAME, MIST, PX, CONE, SWIRL, EYES, SHADOW, BOLT, CLOUD = (
    "villa_eject_glow.png", "villa_eject_mote.png", "villa_eject_puff.png", "villa_eject_streak.png",
    "villa_eject_droplet.png", "villa_eject_ripple.png", "villa_eject_leaf.png", "villa_eject_flame.png",
    "villa_eject_mist.png", "villa_eject_px.png", "villa_eject_cone.png", "villa_eject_swirl.png",
    "villa_eject_eyes.png", "villa_eject_shadow.png", "villa_eject_bolt.png", "villa_eject_cloud.png")

FLOOR_Y = -0.75          # Mitte der Spielerfigur, wenn sie auf dem Boden steht (Boden bei -1,25)
SCENES = []


def dark_overlay(id_, t, a, z=30):
    """Schwarze Flaeche ueber der Welt, die ab t auf a einblendet (Licht aus)."""
    return {"id": id_, "sprite": PX, "z": z, "s": 100, "tint": "#000000",
            "keys": [key(0, "hold", a=0), key(t, "hold", a=0), key(t + 0.12, "in", a=a)]}


# ============================================================================ Villa: Aus dem Fenster
# Salon bei Nacht, Gewitter hinter dem hohen Fenster, eine Wandkerze als einziges warmes Licht. Der Spieler
# tritt ans Fenster, ein Blitz erschreckt ihn. Die Fluegel schlagen auf, Regen und Laub fegen herein, die
# Kerze erlischt, und der Sturm reisst den Spieler hinaus in die Nacht. Die Fluegel knallen wieder zu, die
# Vorhaenge kommen zur Ruhe, ein letztes Wetterleuchten.
WIN_X, WIN_Y = 1.8, 1.0           # Mitte der Fensteroeffnung (2,6 x 3,0)
SCENES.append({
    "id": "window", "map": "villa", "title": "Aus dem Fenster", "length": 6.6, "text": [1.3, 2.6],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.06, x=-0.8, y=-0.2), key(2.2, z=1.08, x=-0.2, y=-0.1), key(3.3, "out", z=1.12, x=0.6, y=0.1),
               key(4.2, z=1.16, x=0.9, y=0.2), key(6.6, z=1.1, x=0.5, y=0.0)],
    "objects": [
        {"id": "bg", "sprite": "villa_eject_window_bg.jpg", "z": -100},
        # Wetterleuchten in der Oeffnung: kaltes Leuchten, das mit den Blitzen aufflammt
        {"id": "sky", "sprite": GLOW, "z": -80, "x": WIN_X, "y": WIN_Y, "sx": 3.4, "sy": 3.8, "tint": "#aebfe6",
         "keys": [key(0, "hold", a=0.1), key(2.25, "hold", a=0.1), key(2.3, "out", a=0.9), key(2.55, a=0.15), key(2.7, "out", a=0.6),
                  key(3.1, a=0.1), key(4.25, "hold", a=0.1), key(4.3, "out", a=0.95), key(4.7, a=0.12), key(5.7, "hold", a=0.12),
                  key(5.75, "out", a=0.45), key(6.1, a=0.1)]},
        {"id": "bolt", "sprite": BOLT, "z": -78, "x": WIN_X + 0.4, "y": WIN_Y + 0.5, "s": 0.9,
         "keys": [key(0, "hold", a=0), key(2.28, "hold", a=0), key(2.3, "hold", a=1), key(2.42, "hold", a=0.35), key(2.5, "hold", a=0)]},
        {"id": "bolt2", "sprite": BOLT, "z": -78, "x": WIN_X - 0.5, "y": WIN_Y + 0.6, "s": 0.75, "sx": -1,
         "keys": [key(0, "hold", a=0), key(4.28, "hold", a=0), key(4.3, "hold", a=1), key(4.4, "hold", a=0.4), key(4.5, "hold", a=0)]},
        # Fensterfluegel: Angel aussen, geschlossen sx=1, aufgerissen edge-on (sx klein)
        {"id": "shutL", "sprite": "villa_eject_shutter.png", "z": 6, "x": WIN_X - 1.3, "y": WIN_Y, "pivot": [0, 0.5],
         "keys": [key(0, "hold", sx=1), key(2.9, "hold", sx=1), key(3.02, "back", sx=0.1), key(4.95, "hold", sx=0.1), key(5.05, "in", sx=1.0),
                  key(5.12, "out", sx=0.92), key(5.2, "in", sx=1)],
         "wobble": [{"p": "sx", "amp": 0.05, "f": 6, "t0": 3.0, "t1": 4.9}]},
        {"id": "shutR", "sprite": "villa_eject_shutter.png", "z": 6, "x": WIN_X + 1.3, "y": WIN_Y, "pivot": [0, 0.5],
         "keys": [key(0, "hold", sx=-1), key(2.9, "hold", sx=-1), key(3.05, "back", sx=-0.1), key(4.95, "hold", sx=-0.1), key(5.05, "in", sx=-1.0),
                  key(5.12, "out", sx=-0.92), key(5.2, "in", sx=-1)],
         "wobble": [{"p": "sx", "amp": 0.05, "f": 5.3, "t0": 3.0, "t1": 4.9, "ph": 1}]},
        # Vorhaenge: haengen ruhig, flattern nach dem Aufschlagen
        {"id": "curtL", "sprite": "villa_eject_curtain.png", "z": 8, "x": WIN_X - 1.55, "y": WIN_Y + 1.6, "pivot": [0.5, 1],
         "wobble": [{"p": "rot", "amp": 22, "f": 1.7, "t0": 2.95, "t1": 5.4}, {"p": "sx", "amp": 0.25, "f": 2.9, "t0": 2.95, "t1": 5.4},
                    {"p": "rot", "amp": 3, "f": 0.5, "t0": 5.3, "t1": 6.6}]},
        {"id": "curtR", "sprite": "villa_eject_curtain.png", "z": 8, "x": WIN_X + 1.55, "y": WIN_Y + 1.6, "pivot": [0.5, 1], "sx": -1,
         "wobble": [{"p": "rot", "amp": -24, "f": 1.5, "t0": 2.95, "t1": 5.4, "ph": 0.8}, {"p": "sx", "amp": 0.25, "f": 2.6, "t0": 2.95, "t1": 5.4},
                    {"p": "rot", "amp": -3, "f": 0.5, "t0": 5.3, "t1": 6.6}]},
        # Wandkerze links: warme Insel, erlischt im Sturm
        {"id": "cglow", "sprite": GLOW, "z": -60, "x": -3.3, "y": 0.9, "sx": 3.6, "sy": 3.2, "tint": "#ffc274",
         "keys": [key(0, a=0.5), key(3.0, "hold", a=0.5), key(3.25, "in", a=0)], "flicker": {"amp": 0.3, "f": 6}},
        {"id": "cflame", "sprite": FLAME, "z": -58, "x": -3.3, "y": 0.62, "pivot": [0.5, 0.1], "s": 0.55,
         "keys": [key(0, a=1), key(3.0, "hold", a=1), key(3.08, "hold", sx=1.6, sy=0.5), key(3.15, "hold", a=0)],
         "wobble": [{"p": "sx", "amp": 0.1, "f": 7}, {"p": "sy", "amp": 0.14, "f": 10.3}, {"p": "rot", "amp": 5, "f": 3.3}]},
        {"id": "pshadow", "sprite": GLOW, "parent": "player", "z": -1, "y": -0.5, "sx": 1.1, "sy": 0.22, "tint": "#000000", "a": 0.5},
    ],
    "player": {"hide": 4.05, "keys": [
        key(0, "lin", x=-6.6, y=FLOOR_Y, rot=0, s=1, sx=1, sy=1, flip=1), key(2.0, "out", x=-0.5),
        key(2.3, "hold", sx=1, sy=1), key(2.38, "out", sx=0.88, sy=1.16), key(2.55, sx=1, sy=1),
        key(2.95, "hold", x=-0.5, rot=0), key(3.25, "out", x=-0.1, rot=28, sx=1.1, sy=0.95),
        key(3.45, "in", x=0.2, y=FLOOR_Y, rot=20, s=1, sx=1.25, sy=0.85),
        key(4.0, "in", x=WIN_X + 0.1, y=WIN_Y - 0.2, rot=-520, s=0.2, sx=1, sy=1, arc=0.6)],
        "wobble": [{"p": "y", "amp": 0.05, "f": 2.2, "t0": 0, "t1": 2.0}, {"p": "x", "amp": 0.03, "f": 12, "t0": 3.0, "t1": 3.4}]},
    "emitters": [
        em(STREAK, -70, t0=0, t1=6.6, rate=55, area=[WIN_X - 1.2, WIN_Y + 1.5, WIN_X + 1.2, WIN_Y + 1.6], vel=[-1.4, -9, -0.8, -7.5],
           life=[0.3, 0.42], size=[0.18, 0.3], tint="#9fb4d8", a=0.4, stretch=True, fade=[0.05, 0.1]),
        em(STREAK, 10, t0=3.0, t1=4.95, rate=90, area=[WIN_X - 0.6, WIN_Y + 1.2, WIN_X + 1.2, WIN_Y + 1.6], vel=[-7, -5, -4, -2.5],
           life=[0.35, 0.55], size=[0.2, 0.35], tint="#b8c8e8", a=0.5, stretch=True, fade=[0.05, 0.1]),
        em(LEAF, 12, t0=3.0, t1=4.9, rate=14, area=[WIN_X - 0.4, WIN_Y - 1.2, WIN_X + 0.8, WIN_Y + 1.3], vel=[-7, -1.5, -3.5, 1.2],
           acc=[0, -1.5], drag=0.8, life=[1.0, 1.8], size=[0.12, 0.24], spin=[-500, 500], tint="#7a6a4a", a=0.9),
        em(MOTE, -59, t0=0, t1=3.0, rate=6, area=[-4.0, 0.2, -2.6, 1.6], vel=[-0.05, 0.05, 0.05, 0.2],
           life=[2, 3.5], size=[0.04, 0.09], tint="#ffd9a0", a=0.7),
        burst(PUFF, -57, 3.1, 3, area=[-3.4, 0.6, -3.2, 0.8], vel=[-0.5, 0.3, 0.1, 0.8], life=[0.8, 1.3], size=[0.25, 0.4],
              grow=0.9, tint="#9a9aa6", a=0.4),
        burst(PUFF, 5, 5.05, 10, area=[WIN_X - 1.3, WIN_Y - 1.4, WIN_X + 1.3, WIN_Y + 1.4], vel=[-0.6, -0.3, 0.6, 0.3], drag=2,
              life=[0.5, 0.9], size=[0.3, 0.6], tint="#6a6a78", a=0.35),
    ],
    "events": steps(0.3, 1.9, 5) + [
        ev(2.3, flash=["#dfe8ff", 0.6, 0.35]), ev(2.55, sound="thunder", vol=0.8), ev(2.9, sound="slam", vol=0.9),
        ev(2.9, shake=[0.4, 0.07]), ev(2.95, sound="rush", vol=0.8), ev(3.3, sound="whoosh", vol=0.6), ev(3.6, sound="whoosh", vol=0.8),
        ev(4.3, flash=["#dfe8ff", 0.7, 0.4]), ev(4.5, sound="thunder", vol=0.9), ev(4.5, shake=[0.5, 0.05]),
        ev(5.05, sound="slam", vol=0.9), ev(5.05, shake=[0.3, 0.06]), ev(5.75, flash=["#cfd8ff", 0.25, 0.3]),
        ev(6.1, sound="thunder", vol=0.3)],
})

# ============================================================================ Villa: Der alte Brunnen
# Mondnacht im verwilderten Garten, Nebel kriecht ueber den Boden. Der Spieler kommt zum alten Ziehbrunnen,
# beugt sich neugierig ueber den Rand, das Holz knarrt, er kippt hinein. Die Kurbel surrt, weit unten ein
# Platschen, Nebel quillt aus dem Schacht, eine Eule ruft. Die Kurbel bleibt mit einem Klacken stehen.
WELL_X = 0.0
SCENES.append({
    "id": "well", "map": "villa", "title": "Der alte Brunnen", "length": 6.4, "text": [1.3, 2.6],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.06, x=0.9, y=-0.2), key(2.4, z=1.1, x=0.5, y=-0.3), key(3.6, "out", z=1.2, x=0.2, y=-0.55),
               key(4.8, z=1.22, x=0.1, y=-0.6), key(6.4, z=1.12, x=0.2, y=-0.4)],
    "objects": [
        {"id": "bg", "sprite": "villa_eject_well_bg.jpg", "z": -100},
        {"id": "cloud1", "sprite": CLOUD, "z": -95, "y": 2.3, "s": 1.4, "a": 0.55, "tint": "#8d97b0",
         "keys": [key(0, "lin", x=-4.8), key(6.4, "lin", x=-2.2)]},
        {"id": "cloud2", "sprite": CLOUD, "z": -95, "y": 1.6, "s": 1.1, "a": 0.4, "tint": "#6d7690",
         "keys": [key(0, "lin", x=3.0), key(6.4, "lin", x=4.6)]},
        {"id": "moonglow", "sprite": GLOW, "z": -96, "x": -3.4, "y": 2.0, "s": 3.2, "tint": "#c8d8f0", "a": 0.35,
         "flicker": {"amp": 0.25, "f": 0.35}},
        {"id": "mist1", "sprite": MIST, "z": 20, "x": -2.6, "y": -2.2, "s": 1.3, "a": 0.4, "tint": "#aab4c8",
         "wobble": [{"p": "x", "amp": 0.3, "f": 0.12}]},
        {"id": "mist2", "sprite": MIST, "z": 20, "x": 3.2, "y": -2.5, "s": 1.5, "a": 0.35, "tint": "#aab4c8",
         "wobble": [{"p": "x", "amp": 0.35, "f": 0.1, "ph": 2}]},
        {"id": "wellBack", "sprite": "villa_eject_well_back.png", "z": -10, "x": WELL_X, "y": -1.9, "pivot": [0.5, 0]},
        {"id": "crank", "sprite": "villa_eject_crank.png", "z": -9, "x": WELL_X + 1.02, "y": 0.42, "s": 0.9,
         "keys": [key(0, "hold", rot=20), key(3.7, "hold", rot=20), key(5.0, "lin", rot=-2500), key(5.12, "out", rot=-2530),
                  key(5.25, "in", rot=-2515)]},
        {"id": "shaft", "sprite": GLOW, "z": -8, "x": WELL_X, "y": -0.95, "sx": 1.5, "sy": 0.45, "tint": "#000000", "a": 0.7},
        {"id": "wellFront", "sprite": "villa_eject_well_front.png", "z": 10, "x": WELL_X, "y": -1.95, "pivot": [0.5, 0]},
        {"id": "pshadow", "sprite": GLOW, "parent": "player", "z": -1, "y": -0.5, "sx": 1.1, "sy": 0.22, "tint": "#000000", "a": 0.45},
    ],
    "player": {"hide": 4.05, "keys": [
        key(0, "lin", x=6.6, y=FLOOR_Y, rot=0, s=1, sx=1, sy=1, flip=-1), key(2.0, "out", x=1.35),
        key(2.4, "hold", x=1.35, rot=0, sx=1, sy=1), key(2.8, x=1.15, rot=18, sx=1.04, sy=0.98), key(3.2, "out", x=1.0, rot=40, sx=1.08, sy=0.96),
        key(3.5, "in", x=0.7, y=FLOOR_Y, rot=62, s=1), key(4.0, "in", x=WELL_X + 0.05, y=-1.9, rot=200, s=0.55)],
        "wobble": [{"p": "y", "amp": 0.05, "f": 2.2, "t0": 0, "t1": 2.0}, {"p": "rot", "amp": 3, "f": 9, "t0": 3.15, "t1": 3.5}]},
    "emitters": [
        em(MOTE, -50, t0=0, t1=6.4, rate=5, area=[-5, -1.5, 5, 1.5], vel=[-0.08, -0.04, 0.08, 0.08],
           life=[3, 5], size=[0.03, 0.06], tint="#c8d4ea", a=0.5),
        burst(DROP, 12, 4.75, 7, area=[WELL_X - 0.3, -0.85, WELL_X + 0.3, -0.8], vel=[-0.8, 1.2, 0.8, 2.4], acc=[0, -10],
              life=[0.4, 0.7], size=[0.05, 0.1], tint="#c0d4f0", a=0.8, stretch=True),
        em(PUFF, 11, t0=4.7, t1=6.0, rate=6, area=[WELL_X - 0.5, -1.0, WELL_X + 0.5, -0.85], vel=[-0.2, 0.35, 0.2, 0.7], drag=1.2,
           life=[1.2, 2.0], size=[0.35, 0.6], grow=0.6, tint="#aab4c8", a=0.3),
    ],
    "events": steps(0.3, 1.9, 5, vol=0.18) + [
        ev(2.8, sound="creak", vol=0.4), ev(3.2, sound="creak", vol=0.7), ev(3.45, sound="twig", vol=0.5),
        ev(3.55, sound="whoosh", vol=0.5), ev(3.75, sound="grind", vol=0.5), ev(4.4, sound="grind", vol=0.3),
        ev(4.72, sound="splash", vol=0.4), ev(5.1, sound="clack", vol=0.7), ev(5.5, sound="owl", vol=0.5)],
})

# ============================================================================ Villa: Die Kristallkugel
# Verdunkelter Salon, Seance-Tisch mit Ouija-Brett, drei Kerzen, Kristallkugel. Der Spieler tritt heran,
# die Kugel beginnt kalt zu leuchten, ein Strudel dreht sich, die Kerzen flackern, und die Kugel saugt den
# Spieler spiralfoermig in sich hinein. Lila Blitz. Die Kerzen erloeschen nacheinander, im Portraet an der
# Wand oeffnen sich die Augen.
BALL_X, BALL_Y = 1.05, -0.08
SCENES.append({
    "id": "seance", "map": "villa", "title": "Die Kristallkugel", "length": 6.8, "text": [1.3, 2.6],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.06, x=-0.8, y=-0.3), key(2.4, z=1.1, x=-0.2, y=-0.3), key(3.9, "out", z=1.22, x=0.7, y=-0.25),
               key(4.6, z=1.2, x=0.6, y=-0.2), key(6.8, z=1.1, x=0.3, y=-0.1)],
    "objects": [
        {"id": "bg", "sprite": "villa_eject_seance_bg.jpg", "z": -100},
        {"id": "table", "sprite": "villa_eject_table.png", "z": -6, "x": 0.9, "y": -1.95, "pivot": [0.5, 0]},
        {"id": "ballGlow", "sprite": GLOW, "z": -5, "x": BALL_X, "y": BALL_Y, "s": 2.6, "tint": "#9b7cff",
         "keys": [key(0, a=0.12), key(2.0, "hold", a=0.12), key(2.9, a=0.7), key(3.95, "hold", a=0.8), key(4.0, "out", a=1.0), key(4.6, a=0.4),
                  key(6.8, a=0.45)],
         "flicker": {"amp": 0.4, "f": 5, "t0": 2.4, "t1": 6.8}},
        {"id": "ball", "sprite": "villa_eject_ball.png", "z": -4, "x": BALL_X, "y": BALL_Y - 0.45, "pivot": [0.5, 0]},
        {"id": "swirl", "sprite": SWIRL, "z": -3, "x": BALL_X, "y": BALL_Y, "tint": "#d8c8ff",
         "keys": [key(0, "hold", a=0, s=0.1, rot=0), key(2.5, "hold", a=0, s=0.1, rot=0), key(3.0, "out", a=0.8, s=1.5),
                  key(4.0, "lin", rot=1440, s=1.0), key(4.05, "hold", a=0)]},
        {"id": "core", "sprite": GLOW, "z": -3, "x": BALL_X, "y": BALL_Y, "s": 0.8, "tint": "#ffffff",
         "keys": [key(0, "hold", a=0), key(3.9, "hold", a=0), key(4.0, "out", a=1), key(4.5, a=0.15), key(6.8, a=0.2)],
         "flicker": {"amp": 0.5, "f": 7, "t0": 4.4, "t1": 6.8}},
    ] + [
        {"id": f"cand{i}", "sprite": "villa_eject_candle.png", "z": -4, "x": cx, "y": cy, "pivot": [0.5, 0], "s": 0.9}
        for i, (cx, cy) in enumerate([(-0.25, -0.5), (0.15, -0.38), (2.0, -0.5)])
    ] + [
        {"id": f"flame{i}", "sprite": FLAME, "z": -3, "x": cx, "y": cy + 0.52, "pivot": [0.5, 0.1], "s": 0.5,
         "keys": [key(0, a=1), key(t_out, "hold", a=1), key(t_out + 0.08, "hold", sx=1.5, sy=0.45), key(t_out + 0.15, "hold", a=0)],
         "wobble": [{"p": "sx", "amp": 0.1, "f": 6 + i}, {"p": "sy", "amp": 0.12, "f": 9 + i * 0.7}, {"p": "rot", "amp": 4, "f": 3 + i * 0.4},
                    {"p": "rot", "amp": 18, "f": 11, "t0": 2.6, "t1": 4.0}, {"p": "sy", "amp": 0.3, "f": 13, "t0": 2.6, "t1": 4.0}]}
        for i, (cx, cy, t_out) in enumerate([(-0.25, -0.5, 4.4), (0.15, -0.38, 4.75), (2.0, -0.5, 5.1)])
    ] + [
        {"id": f"cglow{i}", "sprite": GLOW, "z": -7, "x": cx, "y": cy + 0.6, "s": 1.8, "tint": "#ffc274",
         "keys": [key(0, a=0.4), key(t_out, "hold", a=0.4), key(t_out + 0.2, "in", a=0)],
         "flicker": {"amp": 0.3, "f": 6 + i, "t0": 0, "t1": 2.6}, }
        for i, (cx, cy, t_out) in enumerate([(-0.25, -0.5, 4.4), (0.15, -0.38, 4.75), (2.0, -0.5, 5.1)])
    ] + [
        {"id": "eyes", "sprite": EYES, "z": -90, "x": -2.75, "y": 1.3, "s": 0.9, "tint": "#d8f0ff",
         "keys": [key(0, "hold", a=0), key(5.5, "hold", a=0), key(5.75, "out", a=0.95)], "flicker": {"amp": 0.25, "f": 4, "t0": 5.8, "t1": 6.8}},
        {"id": "eyeGlow", "sprite": GLOW, "z": -91, "x": -2.75, "y": 1.3, "sx": 1.4, "sy": 0.7, "tint": "#a8d0ff",
         "keys": [key(0, "hold", a=0), key(5.5, "hold", a=0), key(5.8, "out", a=0.5)]},
        dark_overlay("dark", 5.1, 0.3, z=25),
        {"id": "pshadow", "sprite": GLOW, "parent": "player", "z": -1, "y": -0.5, "sx": 1.1, "sy": 0.22, "tint": "#000000", "a": 0.45},
    ],
    "player": {"hide": 4.0, "keys": [
        key(0, "lin", x=-6.6, y=FLOOR_Y, rot=0, s=1, sx=1, sy=1, flip=1), key(1.9, "out", x=-1.5),
        key(2.9, "hold", x=-1.5, rot=0, sx=1, sy=1), key(3.15, "out", x=-1.3, rot=-12, sx=0.9, sy=1.1),
        key(3.4, "in", x=-0.9, y=FLOOR_Y, rot=-30, s=1, sx=0.7, sy=1.35), key(4.0, "in", x=BALL_X, y=BALL_Y, rot=-1100, s=0.05, sx=0.6, sy=1.5)],
        "wobble": [{"p": "y", "amp": 0.05, "f": 2.2, "t0": 0, "t1": 1.9}, {"p": "x", "amp": 0.03, "f": 11, "t0": 2.8, "t1": 3.3}]},
    "emitters": [
        em(MOTE, -5, t0=2.6, t1=4.0, rate=40, area=[-2.2, -1.4, 2.2, 1.2], vel=[0, 0, 0, 0], drag=0,
           life=[0.5, 0.9], size=[0.04, 0.1], tint="#c8b0ff", a=0.8),
        em(STREAK, -2, t0=2.9, t1=4.0, rate=45, area=[-3.5, -1.6, 3.5, 1.4], vel=[0, 0, 0, 0],
           life=[0.3, 0.5], size=[0.25, 0.45], tint="#c8b0ff", a=0.45, stretch=True),
        burst(MOTE, 2, 4.0, 30, area=[BALL_X - 0.2, BALL_Y - 0.2, BALL_X + 0.2, BALL_Y + 0.2], vel=[-2.5, -2.5, 2.5, 2.5], drag=2.5,
              life=[0.5, 0.9], size=[0.06, 0.14], tint="#e8dcff", a=0.9),
    ] + [
        burst(PUFF, -2, t_out + 0.1, 3, area=[cx - 0.05, cy + 0.55, cx + 0.05, cy + 0.65], vel=[-0.15, 0.3, 0.15, 0.7],
              life=[0.9, 1.4], size=[0.2, 0.35], grow=0.8, tint="#9a9aa6", a=0.4)
        for cx, cy, t_out in [(-0.25, -0.5, 4.4), (0.15, -0.38, 4.75), (2.0, -0.5, 5.1)]
    ],
    "events": steps(0.3, 1.8, 5, vol=0.18) + [
        ev(2.1, sound="growl", vol=0.35), ev(2.7, sound="chime", vol=0.3), ev(2.9, sound="rush", vol=0.6),
        ev(3.3, sound="growl", vol=0.5), ev(3.5, sound="whoosh", vol=0.7), ev(4.0, sound="zap", vol=0.8),
        ev(4.0, flash=["#b48cff", 0.7, 0.35]), ev(4.0, shake=[0.35, 0.07]), ev(4.1, sound="thud", vol=0.4),
        ev(4.45, sound="whoosh", vol=0.15), ev(4.8, sound="whoosh", vol=0.15), ev(5.15, sound="whoosh", vol=0.15),
        ev(5.7, sound="creak", vol=0.45), ev(6.1, sound="chime", vol=0.25)],
})

# ============================================================================ Villa: CUT!
# Das Set in der Halle: Kamera links, Scheinwerfer rechts, Gaffer-Kreuz auf dem Boden. Der Spieler stellt
# sich auf seine Marke und posiert. Die Filmklappe faellt vor ihn und schlaegt zu, hebt sich wieder, und von
# rechts kommt der lange Buehnenhaken, legt sich um den Spieler und reisst ihn aus dem Bild. Der
# Scheinwerfer platzt, die REC-Lampe blinkt noch ein paarmal in der Dunkelheit.
MARK_X = 0.3
LAMP_X, LAMP_Y = 3.6, -1.95
SCENES.append({
    "id": "cut", "map": "villa", "title": "CUT!", "length": 6.4, "text": [1.3, 2.6],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.06, x=0.8, y=-0.3), key(2.0, z=1.1, x=0.2, y=-0.3), key(2.6, "out", z=1.14, x=0.1, y=-0.1),
               key(3.8, z=1.1, x=0.4, y=-0.3), key(5.0, "out", z=1.08, x=1.2, y=-0.3), key(6.4, z=1.08, x=0.6, y=-0.3)],
    "objects": [
        {"id": "bg", "sprite": "villa_eject_set_bg.jpg", "z": -100},
        {"id": "camera", "sprite": "villa_eject_camera.png", "z": -12, "x": -2.9, "y": -2.1, "pivot": [0.5, 0], "s": 0.95},
        {"id": "rec", "sprite": GLOW, "z": -11, "x": -2.46, "y": 0.14, "s": 0.35, "tint": "#ff4040", "a": 0.9,
         "keys": [key(0, a=0.9), key(5.3, "hold", a=0.9), key(5.3, "hold", a=0.9)],
         "flicker": {"amp": 1.0, "f": 2.5, "t0": 5.3, "t1": 6.4}},
        {"id": "lamp", "sprite": "villa_eject_lamp.png", "z": -8, "x": LAMP_X, "y": LAMP_Y, "pivot": [0.5, 0]},
        {"id": "lampGlow", "sprite": GLOW, "z": -7, "x": LAMP_X - 0.42, "y": 1.05, "s": 1.6, "tint": "#ffe0a8",
         "keys": [key(0, a=0.8), key(5.15, "hold", a=0.8), key(5.2, "out", a=1.3), key(5.3, "hold", a=0)],
         "flicker": {"amp": 0.9, "f": 9, "t0": 4.85, "t1": 5.2}},
        {"id": "cone", "sprite": CONE, "z": -9, "x": LAMP_X - 0.42, "y": 1.05, "pivot": [0, 0.5], "rot": 207, "s": 2.4, "tint": "#ffe7bb",
         "keys": [key(0, a=0.42), key(5.15, "hold", a=0.42), key(5.2, "out", a=0.7), key(5.3, "hold", a=0)],
         "flicker": {"amp": 0.9, "f": 9, "t0": 4.85, "t1": 5.2}},
        {"id": "pool", "sprite": GLOW, "z": -40, "x": MARK_X, "y": -1.25, "sx": 2.8, "sy": 0.7, "tint": "#ffe0b0",
         "keys": [key(0, a=0.45), key(5.15, "hold", a=0.45), key(5.3, "hold", a=0)], "flicker": {"amp": 0.9, "f": 9, "t0": 4.85, "t1": 5.2}},
        {"id": "rig", "keys": [key(0, "hold", x=0, y=0), key(4.6, "hold", x=0, y=0), key(5.0, "in", x=13)]},
        {"id": "hook", "sprite": "villa_eject_hook.png", "parent": "rig", "z": 15, "y": FLOOR_Y + 0.05, "pivot": [1, 0.5],
         "keys": [key(0, "hold", x=12, rot=0), key(3.8, "hold", x=12), key(4.3, "out", x=MARK_X + 5.3, rot=0), key(4.45, "in", x=MARK_X + 5.15),
                  key(4.6, "hold", x=MARK_X + 5.15, rot=0), key(4.75, "out", rot=6), key(5.0, "in", rot=2)],
         "wobble": [{"p": "y", "amp": 0.04, "f": 7, "t0": 3.8, "t1": 4.3}]},
        {"id": "clap", "keys": [key(0, "hold", x=-0.3, y=6.0), key(2.2, "hold", x=-0.3, y=6.0), key(2.6, "out", y=-0.3),
                                key(2.9, "hold", y=-0.3), key(2.93, "out", y=-0.38), key(3.05, "in", y=-0.3),
                                key(3.4, "hold", y=-0.3), key(3.8, "in", y=6.0)]},
        {"id": "clapBase", "sprite": "villa_eject_clap_base.png", "parent": "clap", "z": 30},
        {"id": "clapTop", "sprite": "villa_eject_clap_top.png", "parent": "clap", "z": 31, "x": -1.5, "y": 1.1, "pivot": [0, 1],
         "keys": [key(0, "hold", rot=32), key(2.75, "hold", rot=32), key(2.9, "in", rot=0), key(2.95, "out", rot=4), key(3.02, "in", rot=0)]},
        dark_overlay("dark", 5.25, 0.42, z=35),
        {"id": "pshadow", "sprite": GLOW, "parent": "player", "z": -1, "y": -0.5, "sx": 1.1, "sy": 0.22, "tint": "#000000", "a": 0.5},
    ],
    "player": {"parent": "rig", "hide": 5.05, "keys": [
        key(0, "lin", x=6.8, y=FLOOR_Y, rot=0, s=1, sx=1, sy=1, flip=-1), key(1.8, "out", x=MARK_X),
        key(2.0, "hold", sx=1, sy=1), key(2.1, "out", sx=1.08, sy=0.92), key(2.25, "out", sx=0.95, sy=1.08), key(2.4, sx=1, sy=1),
        key(2.9, "hold", sx=1, sy=1), key(2.96, "out", sx=1.1, sy=0.86), key(3.15, sx=1, sy=1),
        key(4.3, "hold", rot=0, sx=1, sy=1), key(4.4, "out", rot=-12, sx=1.1, sy=0.92), key(4.6, "hold", rot=-12),
        key(4.75, "out", rot=-30, sx=1.4, sy=0.78), key(5.0, "in", rot=-45, sx=1.6, sy=0.7)],
        "wobble": [{"p": "y", "amp": 0.05, "f": 2.2, "t0": 0, "t1": 1.8}, {"p": "x", "amp": 0.03, "f": 12, "t0": 4.4, "t1": 4.6}]},
    "emitters": [
        em(MOTE, -9, t0=0, t1=5.2, rate=9, area=[LAMP_X - 3.0, -1.2, LAMP_X - 0.6, 0.9], vel=[-0.05, -0.05, 0.05, 0.08],
           life=[2.5, 4], size=[0.04, 0.09], tint="#ffe7bb", a=0.6),
        burst(PUFF, 32, 2.9, 6, area=[-1.8, -1.2, 1.2, -1.0], vel=[-0.8, -0.1, 0.8, 0.5], drag=2, life=[0.5, 0.9], size=[0.3, 0.5],
              tint="#9a9aa6", a=0.3),
        burst(PUFF, 16, 4.75, 8, area=[MARK_X - 0.5, -1.2, MARK_X + 0.3, -0.9], vel=[-1.5, 0, -0.3, 0.6], drag=2, life=[0.5, 0.9],
              size=[0.3, 0.6], tint="#8a8a96", a=0.35),
        burst(MOTE, -6, 5.2, 18, area=[LAMP_X - 0.5, 0.9, LAMP_X - 0.3, 1.2], vel=[-2, -2, 2, 1.5], acc=[0, -7], drag=0.5,
              life=[0.5, 1.0], size=[0.05, 0.1], tint="#ffe7bb", a=0.9),
    ],
    "events": steps(0.3, 1.7, 5, vol=0.18) + [
        ev(2.25, sound="whoosh", vol=0.7), ev(2.6, sound="thud", vol=0.3), ev(2.9, sound="clack", vol=1.0), ev(2.9, shake=[0.25, 0.05]),
        ev(3.45, sound="whoosh", vol=0.5), ev(3.85, sound="whoosh", vol=0.6), ev(4.3, sound="thud", vol=0.45), ev(4.4, sound="creak", vol=0.3),
        ev(4.65, sound="whoosh", vol=0.9), ev(4.65, shake=[0.3, 0.04]), ev(5.2, sound="pop", vol=0.9), ev(5.2, flash=["#fff2d6", 0.6, 0.2]),
        ev(5.25, sound="sizzle", vol=0.3), ev(5.7, sound="click", vol=0.35), ev(6.05, sound="click", vol=0.3)],
})

# ============================================================================ SKIP: Villa - Mitternacht
# Die leere Halle, die Standuhr in der Mitte, Kandelaber rechts und links, das Set verlassen. Der Minuten-
# zeiger kriecht auf die Zwoelf, das Pendel schwingt. Die Uhr schlaegt, bei jedem Schlag zuckt das Bild,
# die Kerzen gehen aus. Wetterleuchten durchs Fenster, ein Schatten huscht ueber die Wand. Das Pendel
# bleibt stehen.
CLOCK_X = 0.0
CHIMES = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
SCENES.append({
    "id": "skip_midnight", "map": "villa", "skip": True, "title": "Mitternacht", "length": 6.4, "text": [1.0, 2.8],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.04, x=0.2, y=-0.1), key(2.4, z=1.14, x=0, y=0.3), key(5.0, "lin", z=1.2, x=0, y=0.4),
               key(6.4, z=1.22, x=0.1, y=0.4)],
    "objects": [
        {"id": "bg", "sprite": "villa_eject_hall_bg.jpg", "z": -100},
        {"id": "winGlow", "sprite": GLOW, "z": -90, "x": 4.2, "y": 1.3, "sx": 2.6, "sy": 3.2, "tint": "#aebfe6",
         "keys": [key(0, "hold", a=0.12), key(5.15, "hold", a=0.12), key(5.2, "out", a=0.9), key(5.55, a=0.12)]},
    ] + [
        {"id": f"cglow{i}", "sprite": GLOW, "z": -60, "x": cx, "y": 0.75, "sx": 3.4, "sy": 3.0, "tint": "#ffc274",
         "keys": [key(0, a=0.5), key(t_out, "hold", a=0.5), key(t_out + 0.25, "in", a=0)], "flicker": {"amp": 0.3, "f": 5.5 + i}}
        for i, (cx, t_out) in enumerate([(-2.6, 3.55), (2.6, 4.05)])
    ] + [
        {"id": f"flame{i}{k}", "sprite": FLAME, "z": -55, "x": cx + dx, "y": 0.52 + dy, "pivot": [0.5, 0.1], "s": 0.5,
         "keys": [key(0, a=1), key(t_out + k * 0.05, "hold", a=1), key(t_out + k * 0.05 + 0.08, "hold", sx=1.6, sy=0.45),
                  key(t_out + k * 0.05 + 0.15, "hold", a=0)],
         "wobble": [{"p": "sx", "amp": 0.1, "f": 6 + k}, {"p": "sy", "amp": 0.12, "f": 9 + k * 0.7 + i}, {"p": "rot", "amp": 4, "f": 3 + k * 0.4}]}
        for i, (cx, t_out) in enumerate([(-2.6, 3.55), (2.6, 4.05)]) for k, (dx, dy) in enumerate([(-0.22, 0.0), (0.0, 0.08), (0.22, 0.0)])
    ] + [
        {"id": "clock", "sprite": "villa_eject_clock.png", "z": -20, "x": CLOCK_X, "y": -1.6, "pivot": [0.5, 0]},
        {"id": "pend", "sprite": "villa_eject_pendulum.png", "z": -19, "x": CLOCK_X, "y": 0.02, "pivot": [0.5, 0.04],
         "wobble": [{"p": "rot", "amp": 11, "f": 0.55, "t0": 0, "t1": 5.55}]},
        {"id": "handH", "sprite": "villa_eject_hand_h.png", "z": -18, "x": CLOCK_X, "y": 1.12, "pivot": [0.5, 0.86],
         "keys": [key(0, "lin", rot=2.5), key(2.4, "lin", rot=0)]},
        {"id": "handM", "sprite": "villa_eject_hand_m.png", "z": -17, "x": CLOCK_X, "y": 1.12, "pivot": [0.5, 0.86],
         "keys": [key(0, "lin", rot=30), key(2.4, "lin", rot=0)]},
        {"id": "faceGlow", "sprite": GLOW, "z": -21, "x": CLOCK_X, "y": 1.12, "s": 1.4, "tint": "#ffe6b0",
         "keys": [key(0, "hold", a=0.15)] + sum(([key(t, "hold", a=0.15), key(t + 0.03, "out", a=0.7), key(t + 0.4, a=0.15)] for t in CHIMES), [])},
        {"id": "shadow", "sprite": SHADOW, "z": -30, "y": -0.3, "s": 2.4, "a": 0.0,
         "keys": [key(0, "hold", x=-6.5, a=0), key(5.2, "hold", x=-6.5, a=0), key(5.22, "hold", a=0.6), key(5.55, "lin", x=7),
                  key(5.56, "hold", a=0)]},
        dark_overlay("dark", 4.15, 0.35, z=20),
    ],
    "player": {"keys": [key(0, "lin", x=0, y=0, s=1)]},
    "emitters": [
        em(MOTE, -50, t0=0, t1=6.4, rate=8, area=[-4, -1, 4, 2], vel=[-0.05, -0.04, 0.05, 0.08],
           life=[3, 5], size=[0.03, 0.07], tint="#ffe2b8", a=0.5),
    ] + [
        burst(PUFF, -54, t_out + 0.2, 3, area=[cx - 0.25, 0.55, cx + 0.25, 0.7], vel=[-0.15, 0.3, 0.15, 0.7], life=[0.9, 1.5],
              size=[0.2, 0.35], grow=0.8, tint="#9a9aa6", a=0.4) for cx, t_out in [(-2.6, 3.55), (2.6, 4.05)]
    ],
    "events": [ev(0.4, sound="click", vol=0.12), ev(1.2, sound="click", vol=0.12), ev(2.0, sound="click", vol=0.12)]
    + [ev(t, sound="chime", vol=0.55) for t in CHIMES] + [ev(t, shake=[0.15, 0.015]) for t in CHIMES]
    + [ev(3.6, sound="whoosh", vol=0.15), ev(4.1, sound="whoosh", vol=0.15), ev(5.2, flash=["#cfd8ff", 0.5, 0.4]),
       ev(5.25, sound="rush", vol=0.35), ev(5.5, sound="thunder", vol=0.6), ev(5.6, sound="clack", vol=0.4), ev(5.95, sound="creak", vol=0.45)],
})

# ============================================================================ SKIP: Villa - Leerer Stuhl
# Das Set, der Regiestuhl im Scheinwerferlicht, leer. Zwei Crewleute kommen von beiden Seiten und schauen
# ratlos auf den Stuhl: Schulterzucken, Kopfkratzen. Ein Schatten huscht ueber die Wand hinter ihnen, beide
# fahren herum, nichts. Der Scheinwerfer platzt, Dunkelheit, die REC-Lampe blinkt, einer hopst vor Schreck.
CHAIR_X = 0.5
SCENES.append({
    "id": "skip_chair", "map": "villa", "skip": True, "title": "Leerer Stuhl", "length": 6.4, "text": [1.0, 2.8],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.04, x=0.3, y=-0.3), key(2.0, z=1.1, x=0.4, y=-0.3), key(3.4, "lin", z=1.1, x=0.4, y=-0.25),
               key(3.9, "out", z=1.06, x=0.2, y=0.0), key(4.6, z=1.1, x=0.4, y=-0.3), key(6.4, z=1.12, x=0.4, y=-0.3)],
    "objects": [
        {"id": "bg", "sprite": "villa_eject_set_bg.jpg", "z": -100},
        {"id": "camera", "sprite": "villa_eject_camera.png", "z": -12, "x": -2.9, "y": -2.1, "pivot": [0.5, 0], "s": 0.95},
        {"id": "rec", "sprite": GLOW, "z": -11, "x": -2.46, "y": 0.14, "s": 0.35, "tint": "#ff4040", "a": 0.9,
         "flicker": {"amp": 1.0, "f": 2.5, "t0": 5.1, "t1": 6.4}},
        {"id": "lamp", "sprite": "villa_eject_lamp.png", "z": -8, "x": LAMP_X, "y": LAMP_Y, "pivot": [0.5, 0]},
        {"id": "lampGlow", "sprite": GLOW, "z": -7, "x": LAMP_X - 0.42, "y": 1.05, "s": 1.6, "tint": "#ffe0a8",
         "keys": [key(0, a=0.8), key(4.85, "hold", a=0.8), key(4.9, "out", a=1.3), key(5.0, "hold", a=0)],
         "flicker": {"amp": 0.9, "f": 9, "t0": 4.5, "t1": 4.9}},
        {"id": "cone", "sprite": CONE, "z": -9, "x": LAMP_X - 0.42, "y": 1.05, "pivot": [0, 0.5], "rot": 205, "s": 2.4, "tint": "#ffe7bb",
         "keys": [key(0, a=0.42), key(4.85, "hold", a=0.42), key(4.9, "out", a=0.7), key(5.0, "hold", a=0)],
         "flicker": {"amp": 0.9, "f": 9, "t0": 4.5, "t1": 4.9}},
        {"id": "pool", "sprite": GLOW, "z": -40, "x": CHAIR_X, "y": -1.3, "sx": 2.8, "sy": 0.7, "tint": "#ffe0b0",
         "keys": [key(0, a=0.45), key(4.85, "hold", a=0.45), key(5.0, "hold", a=0)], "flicker": {"amp": 0.9, "f": 9, "t0": 4.5, "t1": 4.9}},
        {"id": "chair", "sprite": "villa_eject_chair.png", "z": -5, "x": CHAIR_X, "y": -1.5, "pivot": [0.5, 0]},
        {"id": "shadow", "sprite": SHADOW, "z": -30, "y": -0.2, "s": 2.4,
         "keys": [key(0, "hold", x=-6.5, a=0), key(3.35, "hold", x=-6.5, a=0), key(3.37, "hold", a=0.55), key(3.85, "lin", x=7),
                  key(3.86, "hold", a=0)]},
        {"id": "crewA", "sprite": "villa_eject_crew_a.png", "z": 2, "y": FLOOR_Y - 0.02, "s": 1.05,
         "keys": [key(0, "lin", x=-6.5, sx=1, rot=0), key(1.4, "out", x=-1.3), key(3.5, "hold", sx=1), key(3.55, "hold", sx=-1),
                  key(4.2, "hold", sx=-1), key(4.25, "hold", sx=1), key(5.9, "hold", y=FLOOR_Y - 0.02), key(6.0, "out", y=FLOOR_Y + 0.35),
                  key(6.12, "in", y=FLOOR_Y - 0.02)],
         "wobble": [{"p": "y", "amp": 0.05, "f": 2.4, "t0": 0, "t1": 1.4}, {"p": "y", "amp": 0.06, "f": 3, "t0": 2.0, "t1": 2.5},
                    {"p": "rot", "amp": 5, "f": 3, "t0": 2.0, "t1": 2.5}]},
        {"id": "crewB", "sprite": "villa_eject_crew_b.png", "z": 3, "y": FLOOR_Y - 0.02, "s": 1.05,
         "keys": [key(0, "lin", x=7, sx=-1, rot=0), key(1.4, "out", x=2.5), key(2.6, "hold", rot=0), key(2.9, rot=9), key(3.3, rot=0),
                  key(3.55, "hold", sx=-1), key(3.6, "hold", sx=1), key(4.25, "hold", sx=1), key(4.3, "hold", sx=-1)],
         "wobble": [{"p": "y", "amp": 0.05, "f": 2.4, "t0": 0, "t1": 1.4, "ph": 1.2}]},
        dark_overlay("dark", 4.95, 0.42, z=35),
    ],
    "player": {"keys": [key(0, "lin", x=0, y=0, s=1)]},
    "emitters": [
        em(MOTE, -9, t0=0, t1=4.9, rate=9, area=[LAMP_X - 3.0, -1.2, LAMP_X - 0.6, 0.9], vel=[-0.05, -0.05, 0.05, 0.08],
           life=[2.5, 4], size=[0.04, 0.09], tint="#ffe7bb", a=0.6),
        burst(MOTE, -6, 4.9, 18, area=[LAMP_X - 0.5, 0.9, LAMP_X - 0.3, 1.2], vel=[-2, -2, 2, 1.5], acc=[0, -7], drag=0.5,
              life=[0.5, 1.0], size=[0.05, 0.1], tint="#ffe7bb", a=0.9),
    ],
    "events": steps(0.2, 1.3, 4, vol=0.16) + [ev(t + 0.1, sound="step", vol=0.14) for t in (0.2, 0.57, 0.93, 1.3)] + [
        ev(2.1, sound="click", vol=0.2), ev(2.8, sound="creak", vol=0.2), ev(3.3, sound="rush", vol=0.4), ev(3.55, sound="twig", vol=0.4),
        ev(3.6, sound="step", vol=0.2), ev(4.25, sound="step", vol=0.2), ev(4.9, sound="pop", vol=0.9), ev(4.9, flash=["#fff2d6", 0.6, 0.2]),
        ev(4.95, sound="sizzle", vol=0.3), ev(5.5, sound="click", vol=0.35), ev(5.95, sound="step", vol=0.4), ev(6.1, sound="thud", vol=0.3)],
})


# ============================================================================ Pruefung und Ausgabe

def lint():
    """Prueft Schluessel, Klangnamen, Easings, Eigenschaften, Zeitfenster und Verweise; meldet ausserdem
    Eigenschaften, die ueber mehrere Keys hinweg gleiten (wie eject_scenes.lint). Rueckgabe: Zahl der Fehler."""
    errors = 0

    def err(msg):
        nonlocal errors
        errors += 1
        print("  FEHLER:", msg)

    ids = set()
    for sc in SCENES:
        for k in ("id", "map", "title", "length", "text", "bounds", "camera", "objects", "player", "emitters", "events"):
            if k not in sc:
                err(f"{sc.get('id')}: Schluessel {k} fehlt")
        if sc["id"] in ids:
            err(f"{sc['id']}: doppelte Szenen-Id")
        ids.add(sc["id"])
        if sc["map"] != "villa":
            err(f"{sc['id']}: map muss villa sein")
        if not 5.0 <= sc["length"] <= 7.0:
            err(f"{sc['id']}: Laenge {sc['length']} nicht in 5..7 s")
        at, dur = sc["text"]
        if at + dur > sc["length"] - 1.0:
            err(f"{sc['id']}: Textfenster {at}+{dur} endet zu spaet")
        obj_ids = {o["id"] for o in sc["objects"]}
        if len(obj_ids) != len(sc["objects"]):
            err(f"{sc['id']}: doppelte Objekt-Ids")
        for o in sc["objects"]:
            p = o.get("parent")
            if p and p != "player" and p not in obj_ids:
                err(f"{sc['id']}/{o['id']}: parent {p} unbekannt")
            for w in o.get("wobble", []):
                if w["p"] not in PROPS or "amp" not in w or "f" not in w:
                    err(f"{sc['id']}/{o['id']}: wobble {w}")
            if "flicker" in o and not {"amp", "f"} <= set(o["flicker"]):
                err(f"{sc['id']}/{o['id']}: flicker {o['flicker']}")
        pl = sc["player"]
        if pl.get("parent") and pl["parent"] not in obj_ids:
            err(f"{sc['id']}/player: parent {pl['parent']} unbekannt")
        if sc.get("skip") and "hide" in pl:
            err(f"{sc['id']}: Skip-Szene mit hide")
        if not sc.get("skip") and "hide" not in pl:
            err(f"{sc['id']}: Spieler-Szene ohne hide")
        if "hide" in pl and pl["hide"] > sc["length"] - 1.0:
            err(f"{sc['id']}: hide {pl['hide']} zu spaet")
        for o in sc["objects"] + [dict(pl, id="player")] + [{"id": "camera", "keys": sc["camera"]}]:
            ks = sorted(o.get("keys", []), key=lambda k: k[0])
            last = {}
            for i, (t, props, ease) in enumerate(ks):
                if ease not in EASES:
                    err(f"{sc['id']}/{o['id']}: ease {ease}")
                if t < 0 or t > sc["length"] + 0.01:
                    err(f"{sc['id']}/{o['id']}: Key bei {t}s ausserhalb der Szene")
                for pr, v in props.items():
                    if pr not in PROPS and not (o["id"] == "camera" and pr == "z"):
                        err(f"{sc['id']}/{o['id']}: Eigenschaft {pr}")
                    if pr in ("arc", "flip"):
                        continue
                    if pr in last:
                        j, t0, v0 = last[pr]
                        if i - j > 2 and v != v0 and ease != "hold":
                            print(f"  pruefen: {sc['id']}/{o['id']}.{pr} gleitet {t0}s -> {t}s ({v0} -> {v})")
                    last[pr] = (i, t, v)
        for e in sc["emitters"]:
            if "burst" in e:
                if "n" not in e:
                    err(f"{sc['id']}: burst ohne n ({e['sprite']})")
            elif not {"t0", "t1", "rate"} <= set(e):
                err(f"{sc['id']}: Emitter ohne t0/t1/rate ({e['sprite']})")
            if not e["sprite"].startswith("villa_eject_"):
                err(f"{sc['id']}: Emitter-Sprite {e['sprite']}")
        for e in sc["events"]:
            if "sound" in e and e["sound"] not in SOUNDS:
                err(f"{sc['id']}: Klang {e['sound']} kennt die Engine nicht")
            if e["t"] > sc["length"] + 0.01:
                err(f"{sc['id']}: Ereignis bei {e['t']}s ausserhalb der Szene")
            if "flash" in e and (len(e["flash"]) != 3 or not e["flash"][0].startswith("#")):
                err(f"{sc['id']}: flash {e['flash']}")
            if "shake" in e and len(e["shake"]) != 2:
                err(f"{sc['id']}: shake {e['shake']}")
    for sc in SCENES:
        for o in sc["objects"]:
            sp = o.get("sprite")
            if sp and not sp.startswith("villa_eject_"):
                err(f"{sc['id']}/{o['id']}: Sprite {sp} liegt nicht unter villa_eject_*")
    return errors


def sprites():
    """Alle Sprite-Dateinamen, die die Szenen brauchen (fuer gen_villa_eject.py und das Kino)."""
    names = set()
    for sc in SCENES:
        for o in sc["objects"]:
            if o.get("sprite"):
                names.add(o["sprite"])
        for e in sc["emitters"]:
            names.add(e["sprite"])
    return sorted(names)


# Daempfung aller Effekte: hier nachregeln statt in den Szenen (wie bei Atlas).
FX = {"shake": 0.55, "flash": 0.55, "flicker": 0.65, "glow": 0.9, "rate": 0.75, "burst": 0.8, "palpha": 0.85,
      "vignette": 0.6, "volume": 0.55}
GLOWS = (GLOW, CONE)


def damp(sc):
    for e in sc["events"]:
        if "shake" in e:
            e["shake"] = [e["shake"][0], round(e["shake"][1] * FX["shake"], 4)]
        if "flash" in e:
            e["flash"] = [e["flash"][0], round(e["flash"][1] * FX["flash"], 3), e["flash"][2]]
        if "vol" in e:
            e["vol"] = round(e["vol"] * FX["volume"], 3)
    for o in sc["objects"]:
        if "flicker" in o:
            o["flicker"] = dict(o["flicker"], amp=round(o["flicker"]["amp"] * FX["flicker"], 3))
        if o.get("sprite") in GLOWS:
            if "a" in o:
                o["a"] = round(o["a"] * FX["glow"], 3)
            for k in o.get("keys", []):
                if "a" in k[1]:
                    k[1] = dict(k[1], a=round(k[1]["a"] * FX["glow"], 3))
    for em_ in sc["emitters"]:
        if "rate" in em_:
            em_["rate"] = round(em_["rate"] * FX["rate"], 2)
        if "n" in em_:
            em_["n"] = max(1, round(em_["n"] * FX["burst"]))
        em_["a"] = round(em_.get("a", 1) * FX["palpha"], 3)


def main():
    n = lint()
    if n:
        raise SystemExit(f"{n} Fehler in den Szenen")
    for sc in SCENES:
        damp(sc)
    doc = {"version": 1, "ppu": 180, "cinema": {"top": 0.8, "bottom": 0.55, "in": 0.45, "vignette": FX["vignette"]}, "scenes": SCENES}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(OUT, f"{OUT.stat().st_size / 1024:.1f} KB, {len(SCENES)} scenes")
    for sc in SCENES:
        print(f"  {sc['id']:14s} {sc['length']:.1f} s  {'skip' if sc.get('skip') else 'player'}  {sc['title']}")
    print("  sprites:", ", ".join(sprites()))


if __name__ == "__main__":
    main()
