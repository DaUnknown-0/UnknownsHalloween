# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_eject.py - Regie der Rauswurf-Szenen auf Ravenhollow Cemetery -> Resources/graveyard_eject/graveyard_eject.json.
#
# Gleiches Format wie villa_eject.py (Objekte mit Keyframes je Eigenschaft, Partikel-Emitter, Kamera, Ereignisse),
# abgespielt von Villa/EjectEngine.cs. Einheiten: 1 = 180 px der Grafik, Ursprung Bildmitte, y nach oben,
# sichtbar 11 x 6,2 bei Zoom 1. Die Grafik erzeugt gen_graveyard_eject.py; die allgemeinen Partikel
# (Glimmen, Staub, Tropfen ...) kommen aus der Villa.
#
# Vier Szenen mit Spieler, eine Skip-Szene (Rabenrat) und eine Sonderszene "special_sadako", die nur
# spielt, wenn der Ausgeworfene das Sadako-Kostuem traegt (GraveyardEject.cs waehlt sie gezielt aus;
# Szenen mit "special_" am Anfang fallen aus der Zufallsauswahl).
#
#     python tools/graveyard_eject.py

import json
import math
from pathlib import Path

from gen_graveyard_eject import PERCH

OUT = Path(__file__).resolve().parent.parent / "Resources" / "graveyard_eject" / "graveyard_eject.json"
SOUNDS = {"boom", "chime", "clack", "click", "creak", "fire", "grind", "growl", "organ", "owl", "pop", "rush",
          "sizzle", "slam", "splash", "step", "thud", "thunder", "twig", "whoosh", "zap"}
EASES = {"lin", "in", "out", "io", "back", "inback", "hold"}
PROPS = {"x", "y", "rot", "sx", "sy", "s", "a", "b", "flip", "arc"}
SPRITE_PREFIX = ("gy_eject_", "villa_eject_", "task_eject_")


def key(t, ease="io", **p):
    return [round(t, 3), p, ease]


def em(sprite, z, **kw):
    e = {"sprite": sprite, "z": z}
    e.update(kw)
    return e


def burst(sprite, z, t, n, **kw):
    return em(sprite, z, burst=t, n=n, **kw)


def ev(t, **kw):
    e = {"t": round(t, 3)}
    e.update(kw)
    return e


def steps(t0, t1, n, vol=0.2):
    """Schritte in gleichmaessigem Abstand."""
    return [ev(round(t0 + (t1 - t0) * k / max(1, n - 1), 2), sound="step", vol=vol) for k in range(n)]


def jerk(t0, poses, move=0.07, pause=0.16):
    """Ruckartige Bewegung: je Pose ein schneller Satz, dann Stillstand (Stop-Motion)."""
    ks, t = [], t0
    for i, p in enumerate(poses):
        if i:
            ks.append(key(t, "lin", **poses[i - 1]))
            t += move
            ks.append(key(t, "out", **p))
        else:
            ks.append(key(t, "hold", **p))
        t += pause
    return ks


GLOW, MOTE, PUFF, STREAK, DROP, RIPPLE, LEAF, FLAME, MIST, PX, EYES, CLOUD = (
    "villa_eject_glow.png", "villa_eject_mote.png", "villa_eject_puff.png", "villa_eject_streak.png",
    "villa_eject_droplet.png", "villa_eject_ripple.png", "villa_eject_leaf.png", "villa_eject_flame.png",
    "villa_eject_mist.png", "villa_eject_px.png", "villa_eject_eyes.png", "villa_eject_cloud.png")

FLOOR_Y = -0.75          # Mitte der Spielerfigur, wenn sie auf dem Boden steht (Boden bei -1,25)
SCENES = []


def dark_overlay(id_, t, a, z=30, dur=0.12):
    """Schwarze Flaeche ueber der Welt, die ab t auf a einblendet (Licht aus)."""
    return {"id": id_, "sprite": PX, "z": z, "s": 100, "tint": "#000000",
            "keys": [key(0, "hold", a=0), key(t, "hold", a=0), key(t + dur, "in", a=a)]}


def shadow(a=0.45, y=-0.5):
    return {"id": "pshadow", "sprite": GLOW, "parent": "player", "z": -1, "y": y, "sx": 1.1, "sy": 0.22, "tint": "#000000", "a": a}


# ============================================================================ Friedhof: Das offene Grab
# Mondnacht zwischen Eiben, ein frisch ausgehobenes Grab mit Erdhaufen und Schaufel. Der Spieler tritt an
# die Kante und schaut hinein, da schiesst eine Knochenhand heraus und zieht ihn hinab. Die Schaufel erhebt
# sich von selbst und schaufelt das Grab zu, klopft die Erde fest, ein Grabstein faellt vom Himmel an seinen
# Platz. Zum Schluss winkt die Knochenhand noch einmal aus der frischen Erde.
PIT_X, PIT_Y = 0.6, -1.4
MOUND_X = PIT_X + 2.2
SCOOPS = (3.25, 3.85, 4.45)


def shovel_keys():
    ks = [key(0, "hold", x=MOUND_X + 0.1, y=-0.98, rot=-14), key(2.95, "hold", x=MOUND_X + 0.1, y=-0.98, rot=-14),
          key(3.15, "out", x=MOUND_X + 0.05, y=-0.45, rot=4)]
    for t in SCOOPS:
        ks += [key(t, "in", x=MOUND_X - 0.05, y=-0.95, rot=26),                 # in den Haufen stechen
               key(t + 0.18, "out", x=MOUND_X - 0.2, y=-0.5, rot=-6),           # anheben
               key(t + 0.36, "io", x=PIT_X + 1.15, y=-0.35, rot=58),            # ueber dem Grab auskippen
               key(t + 0.52, "io", x=MOUND_X + 0.05, y=-0.45, rot=10)]
    ks += [key(5.05, "io", x=PIT_X + 0.15, y=-0.9, rot=84), key(5.15, "in", y=-1.08), key(5.25, "out", y=-0.88),
           key(5.35, "in", y=-1.08), key(5.5, "out", x=PIT_X + 1.5, y=-0.7, rot=-10), key(5.75, "in", x=PIT_X + 1.55, y=-1.25, rot=-12)]
    return ks


SCENES.append({
    "id": "grave", "map": "graveyard", "title": "Das offene Grab", "length": 7.4, "text": [1.3, 2.6],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.06, x=-0.8, y=-0.2), key(2.1, z=1.12, x=0.2, y=-0.45), key(2.9, "out", z=1.18, x=0.5, y=-0.6),
               key(4.6, z=1.12, x=1.1, y=-0.45), key(6.0, z=1.16, x=0.8, y=-0.5), key(7.4, z=1.14, x=0.7, y=-0.45)],
    "objects": [
        {"id": "bg", "sprite": "gy_eject_grave_bg.jpg", "z": -100},
        {"id": "moonglow", "sprite": GLOW, "z": -96, "x": 3.7, "y": 2.2, "s": 2.4, "tint": "#c8d8f0", "a": 0.3, "flicker": {"amp": 0.2, "f": 0.3}},
        {"id": "cloud", "sprite": CLOUD, "z": -95, "y": 2.6, "s": 1.2, "a": 0.4, "tint": "#6d7690", "keys": [key(0, "lin", x=1.4), key(7.4, "lin", x=3.2)]},
        {"id": "pit", "sprite": "gy_eject_pit.png", "z": -20, "x": PIT_X, "y": PIT_Y},
        {"id": "headstone", "sprite": "gy_eject_headstone.png", "z": -18, "x": PIT_X, "pivot": [0.5, 0],
         "keys": [key(0, "hold", y=4.8, sx=1, sy=1), key(5.25, "hold", y=4.8), key(5.6, "in", y=PIT_Y + 0.36),
                  key(5.66, "out", sx=1.08, sy=0.9), key(5.8, "io", sx=1, sy=1)]},
        {"id": "mound", "sprite": "gy_eject_mound.png", "z": -15, "x": MOUND_X, "y": PIT_Y + 0.02, "pivot": [0.5, 0],
         "keys": [key(0, "hold", sx=1, sy=1)] + [key(t + 0.2, "out", sx=1 - 0.08 * (i + 1), sy=1 - 0.17 * (i + 1)) for i, t in enumerate(SCOOPS)]},
        {"id": "shovel", "sprite": "gy_eject_shovel.png", "z": -16, "pivot": [0.5, 0], "keys": shovel_keys(),
         "wobble": [{"p": "rot", "amp": 3, "f": 1.3, "t0": 3.1, "t1": 5.0}]},
        {"id": "shovelGlow", "sprite": GLOW, "z": -17, "parent": "shovel", "y": 0.75, "sx": 0.9, "sy": 1.4, "tint": "#9fe8c8",
         "keys": [key(0, "hold", a=0), key(2.95, "hold", a=0), key(3.2, "out", a=0.3), key(5.6, "hold", a=0.3), key(6.0, a=0)]},
        {"id": "grabHand", "sprite": "gy_eject_hand.png", "z": 0, "x": PIT_X - 0.12, "s": 0.75, "pivot": [0.5, 0],
         "keys": [key(0, "hold", y=-2.2, a=0, rot=0), key(2.2, "hold", y=-2.2, a=0), key(2.21, "hold", a=1),
                  key(2.38, "back", y=-1.68, rot=-8), key(2.5, "hold", y=-1.68), key(2.85, "in", y=-2.2, rot=4), key(2.95, "hold", a=0)]},
        {"id": "waveHand", "sprite": "gy_eject_hand.png", "z": 0, "x": PIT_X + 0.5, "s": 0.5, "pivot": [0.5, 0],
         "keys": [key(0, "hold", y=-2.1, a=0, rot=0), key(6.1, "hold", y=-2.1, a=0), key(6.12, "hold", a=1), key(6.45, "out", y=-1.55),
                  key(7.0, "hold", y=-1.55), key(7.35, "in", y=-2.1)],
         "wobble": [{"p": "rot", "amp": 16, "f": 2.6, "t0": 6.45, "t1": 7.0}]},
        {"id": "fill", "sprite": "gy_eject_fill.png", "z": 1, "x": PIT_X, "y": PIT_Y - 0.02,
         "keys": [key(0, "hold", a=0, sx=0.9, sy=0.5), key(SCOOPS[0] + 0.42, "hold", a=0),
                  key(SCOOPS[0] + 0.5, "out", a=0.5, sy=0.6), key(SCOOPS[1] + 0.5, "out", a=0.8, sx=0.95, sy=0.8),
                  key(SCOOPS[2] + 0.5, "out", a=1, sx=1, sy=1), key(5.17, "hold", sy=1), key(5.2, "out", sy=0.92), key(5.37, "hold", sy=0.92),
                  key(5.4, "out", sy=0.86)]},
        {"id": "lip", "sprite": "gy_eject_pit_lip.png", "z": 5, "x": PIT_X, "y": PIT_Y - 0.2, "pivot": [0.5, 1]},
        {"id": "mist1", "sprite": MIST, "z": 20, "x": -2.6, "y": -2.3, "s": 1.4, "a": 0.38, "tint": "#aab4c8",
         "wobble": [{"p": "x", "amp": 0.3, "f": 0.12}]},
        {"id": "mist2", "sprite": MIST, "z": 20, "x": 3.4, "y": -2.6, "s": 1.6, "a": 0.32, "tint": "#aab4c8",
         "wobble": [{"p": "x", "amp": 0.35, "f": 0.1, "ph": 2}]},
        shadow(0.45),
    ],
    "player": {"hide": 2.92, "keys": [
        key(0, "lin", x=-6.6, y=-0.62, rot=0, s=1, sx=1, sy=1, a=1, flip=1), key(2.0, "out", x=PIT_X - 0.2),
        key(2.2, "io", rot=-9), key(2.26, "hold", sx=1, sy=1, y=-0.62), key(2.33, "out", sx=0.88, sy=1.16, y=-0.5, rot=4),
        key(2.48, "in", sx=1, sy=1, y=-0.62, rot=6), key(2.55, "hold", y=-0.62), key(2.86, "in", y=-1.6, rot=-14),
        key(2.72, "hold", a=1), key(2.88, "in", a=0)],
        "wobble": [{"p": "y", "amp": 0.05, "f": 2.2, "t0": 0, "t1": 2.0}, {"p": "x", "amp": 0.04, "f": 14, "t0": 2.45, "t1": 2.85}]},
    "emitters": [
        em(MOTE, -50, t0=0, t1=7.4, rate=4, area=[-5, -1.2, 5, 1.6], vel=[-0.08, -0.04, 0.08, 0.08], life=[3, 5], size=[0.03, 0.06],
           tint="#c8d4ea", a=0.45),
        burst(PX, 6, 2.22, 12, area=[PIT_X - 0.4, -1.6, PIT_X + 0.3, -1.5], vel=[-1.2, 1.2, 1.2, 3.0], acc=[0, -9], life=[0.4, 0.7],
              size=[0.05, 0.11], spin=[-400, 400], tint="#4a3a2c", a=0.95),
        burst(PUFF, 6, 2.88, 4, area=[PIT_X - 0.6, -1.5, PIT_X + 0.6, -1.4], vel=[-0.4, 0.3, 0.4, 0.8], drag=1.5, life=[0.7, 1.1],
              size=[0.35, 0.55], grow=0.7, tint="#5a4c40", a=0.35),
    ] + [e for t in SCOOPS for e in (
        burst(PX, 3, t + 0.36, 16, area=[PIT_X + 0.7, -0.3, PIT_X + 1.0, -0.15], vel=[-2.6, 0.2, -1.0, 1.6], acc=[0, -9], life=[0.35, 0.55],
              size=[0.05, 0.13], spin=[-500, 500], tint="#4a3a2c", a=0.95),
        burst(PUFF, 3, t + 0.55, 3, area=[PIT_X - 0.6, -1.5, PIT_X + 0.6, -1.3], vel=[-0.3, 0.2, 0.3, 0.6], drag=1.5, life=[0.6, 1.0],
              size=[0.3, 0.5], grow=0.6, tint="#5a4c40", a=0.3),
        burst(PX, -14, t + 0.05, 6, area=[MOUND_X - 0.3, -0.75, MOUND_X + 0.2, -0.6], vel=[-0.8, 0.6, 0.8, 1.6], acc=[0, -8], life=[0.3, 0.5],
              size=[0.04, 0.09], tint="#3e3026", a=0.9))] + [
        burst(PUFF, -17, 5.6, 6, area=[PIT_X - 0.6, PIT_Y + 0.3, PIT_X + 0.6, PIT_Y + 0.45], vel=[-0.8, 0.1, 0.8, 0.5], drag=1.6, life=[0.7, 1.2],
              size=[0.3, 0.5], grow=0.7, tint="#6a6070", a=0.35),
        burst(PX, 2, 6.12, 7, area=[PIT_X + 0.35, -1.35, PIT_X + 0.65, -1.25], vel=[-0.7, 0.8, 0.7, 1.8], acc=[0, -8], life=[0.3, 0.5],
              size=[0.04, 0.09], tint="#4a3a2c", a=0.9),
    ],
    "events": steps(0.3, 1.9, 5, vol=0.18) + [
        ev(2.22, sound="twig", vol=0.6), ev(2.25, sound="growl", vol=0.4), ev(2.25, shake=[0.25, 0.04]), ev(2.6, sound="whoosh", vol=0.6),
        ev(2.88, sound="thud", vol=0.7), ev(2.88, shake=[0.3, 0.05]), ev(3.0, sound="creak", vol=0.5)] + [
        e for t in SCOOPS for e in (ev(t + 0.02, sound="step", vol=0.45), ev(t + 0.34, sound="whoosh", vol=0.35), ev(t + 0.55, sound="thud", vol=0.3))] + [
        ev(5.15, sound="thud", vol=0.5), ev(5.35, sound="thud", vol=0.5), ev(5.75, sound="step", vol=0.4),
        ev(5.6, sound="boom", vol=0.5), ev(5.6, sound="thud", vol=0.8), ev(5.6, shake=[0.35, 0.07]),
        ev(6.12, sound="twig", vol=0.4), ev(6.5, sound="owl", vol=0.45)],
})

# ============================================================================ Friedhof: Die Totenglocke
# Glockenstube im Kapellenturm, durch die Bogenoeffnung der Friedhof tief unten und der Mond. Der Spieler
# greift das Glockenseil, die Glocke beginnt zu schwingen und reisst ihn mit jedem Schlag hoeher, Staub
# rieselt vom Gebaelk, die Raben auf der Bruestung fliehen. Beim groessten Ausschlag schleudert ihn das Seil
# durch den Bogen hinaus, er fliegt als kleiner Schatten vor den Mond. Die Glocke klingt aus.
BELL_X, BELL_Y = -0.6, 2.92
YOKE = (0.75, -0.06)                      # rechtes Jochende relativ zum Drehpunkt (dort haengt das Seil)
SWING = [(0, 0), (1.95, 0), (2.35, 20), (2.8, -24), (3.28, 31), (3.75, -36), (4.25, 40), (4.8, -26), (5.35, 17), (5.9, -10), (6.45, 5), (7.0, 0)]
MOON = (3.9, 1.7)


def rope_end(th):
    r = math.radians(th)
    return (BELL_X + YOKE[0] * math.cos(r) - YOKE[1] * math.sin(r), BELL_Y + YOKE[0] * math.sin(r) + YOKE[1] * math.cos(r))


def belfry_player():
    ks = [key(0, "lin", x=-6.6, y=FLOOR_Y, rot=0, s=1, sx=1, sy=1, a=1, flip=1), key(1.75, "out", x=0.45),
          key(1.85, "out", y=FLOOR_Y + 0.12), key(1.95, "in", y=FLOOR_Y)]
    for t, th in SWING[2:6]:                                                  # mitgerissen: hoch, wenn das Seil steigt
        dy = rope_end(th)[1] - rope_end(0)[1]
        ks.append(key(t, "io", x=0.45, y=FLOOR_Y + max(0.0, dy) * 1.1, sy=1.0 if dy > 0 else 0.86, sx=1.0 if dy > 0 else 1.1, rot=-6 if dy > 0 else 4))
    t_fl = SWING[6][0]
    ks += [key(t_fl - 0.05, "in", x=0.45, y=FLOOR_Y + 0.6, sx=0.92, sy=1.12, rot=-10),
           key(t_fl + 0.55, "out", x=2.7, y=1.35, s=0.42, sx=1, sy=1, rot=-420, arc=0.55),
           key(t_fl + 1.15, "in", x=MOON[0], y=MOON[1] + 0.05, s=0.1, rot=-760),
           key(t_fl + 1.2, "hold", a=1), key(t_fl + 1.32, "lin", a=0)]
    return ks


SCENES.append({
    "id": "belfry", "map": "graveyard", "title": "Die Totenglocke", "length": 7.0, "text": [1.3, 2.6],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.06, x=-1.0, y=0.3), key(1.9, z=1.1, x=-0.3, y=0.6), key(4.2, z=1.08, x=0.4, y=0.6),
               key(5.3, "io", z=1.16, x=1.6, y=0.9), key(7.0, z=1.14, x=1.4, y=0.8)],
    "objects": [
        {"id": "bg", "sprite": "gy_eject_belfry_bg.jpg", "z": -100},
        {"id": "moonglow", "sprite": GLOW, "z": -96, "x": MOON[0], "y": MOON[1], "s": 1.8, "tint": "#c8d8f0", "a": 0.35,
         "flicker": {"amp": 0.2, "f": 0.3}},
        {"id": "lantern", "sprite": GLOW, "z": -90, "x": -4.5, "y": 0.68, "sx": 2.6, "sy": 2.4, "tint": "#ffc274", "a": 0.4,
         "flicker": {"amp": 0.3, "f": 5}},
    ] + [o for i, (cx, flip, dx, dy, tt) in enumerate(((2.0, 1, 5.8, 3.2, 2.42), (3.75, -1, 6.5, 2.4, 2.5))) for o in (
        {"id": f"crow{i}", "sprite": "gy_eject_crow.png", "z": -60, "x": cx, "y": -0.88, "pivot": [0.47, 0.07], "sx": flip,
         "keys": [key(0, "hold", a=1), key(tt, "hold", a=1), key(tt + 0.01, "hold", a=0)],
         "wobble": [{"p": "rot", "amp": 3, "f": 0.7 + 0.3 * i}]},
        {"id": f"crowF{i}", "sprite": "gy_eject_crow_fly.png", "z": -60, "s": 0.8,
         "keys": [key(0, "hold", x=cx, y=-0.6, a=0, flip=1), key(tt, "hold", a=0), key(tt + 0.01, "hold", a=1),
                  key(tt + 1.4, "in", x=dx, y=dy, s=0.45, arc=0.4)],
         "wobble": [{"p": "sy", "amp": 0.45, "f": 9 + i}]})] + [
        {"id": "bell", "sprite": "gy_eject_bell.png", "z": -20, "x": BELL_X, "y": BELL_Y, "pivot": [0.5, 0.96],
         "keys": [key(t, "io", rot=th) for t, th in SWING]},
        {"id": "rope", "sprite": "gy_eject_rope.png", "z": 2, "pivot": [0.5, 1], "sy": 1.2,
         "keys": [key(t, "io", x=round(rope_end(th)[0], 3), y=round(rope_end(th)[1], 3), rot=round(-th * 0.25, 1)) for t, th in SWING],
         "wobble": [{"p": "rot", "amp": 2.5, "f": 0.9}]},
        shadow(0.5),
    ],
    "player": {"hide": SWING[6][0] + 1.35, "keys": belfry_player(),
               "wobble": [{"p": "y", "amp": 0.05, "f": 2.2, "t0": 0, "t1": 1.75}, {"p": "rot", "amp": 4, "f": 3, "t0": 2.0, "t1": 4.1}]},
    "emitters": [
        em(MOTE, -50, t0=0, t1=7.0, rate=4, area=[-5, -1.2, 1.2, 2.6], vel=[-0.06, -0.08, 0.06, 0.02], life=[3, 5], size=[0.03, 0.06],
           tint="#e8d8b8", a=0.45),
    ] + [burst(PX, 8, t, 9 if th > 0 else 6, area=[-3.0, 2.9, 1.6, 3.05], vel=[-0.2, -0.6, 0.2, -0.2], acc=[0, -2.2], life=[1.2, 2.0],
               size=[0.02, 0.05], tint="#9a8a74", a=0.8) for t, th in SWING[2:8]] + [
        em(LEAF, 9, t0=2.6, t1=4.6, rate=3, area=[1.6, 0.5, 4.2, 1.6], vel=[-0.3, -0.25, 0.3, -0.05], drag=0.6, life=[2.0, 3.0],
           size=[0.08, 0.13], spin=[-160, 160], tint="#1c1c24", a=0.9),
    ],
    "events": steps(0.3, 1.6, 4, vol=0.2) + [ev(1.9, sound="creak", vol=0.4)] + [
        e for i, (t, th) in enumerate(SWING[2:10]) for e in (
            ev(t, sound="boom", vol=round(0.75 - 0.07 * i, 2)), ev(t + 0.02, sound="chime", vol=round(0.55 - 0.05 * i, 2)),
            ev(t, shake=[0.3, round(0.06 - 0.006 * i, 3)]), ev(t - 0.2, sound="creak", vol=0.3))] + [
        ev(2.45, sound="whoosh", vol=0.5), ev(SWING[6][0] + 0.05, sound="whoosh", vol=0.9), ev(SWING[6][0] + 0.5, sound="rush", vol=0.5),
        ev(SWING[6][0] + 1.25, sound="pop", vol=0.25), ev(6.5, sound="owl", vol=0.4)],
})

# ============================================================================ Friedhof: Das Krematorium
# Backsteinkeller mit Urnenregal, Kohlenhaufen und dem grossen Ofen, Schienen fuehren hinein. Der Spieler
# kommt herein, die Ofentuer fliegt auf, Flammen lecken heraus, ein Sog zieht ihn ueber den Boden und in die
# Glut. Die Tuer knallt zu, das Feuer brausst, das Manometer schlaegt in den roten Bereich. Dann oeffnet sich
# die Tuer knarrend, und eine kleine Urne huepft heraus und bleibt rauchend stehen.
OVEN_X, OVEN_Y = 0.9, -0.2
GAUGE = (2.8, 1.4)


def needle_keys():
    ks = [key(0, "hold", rot=150), key(1.6, "hold", rot=150), key(2.0, "out", rot=95), key(3.15, "hold", rot=95), key(3.6, "out", rot=-15),
          key(4.6, "hold", rot=-15), key(5.4, "io", rot=60), key(7.2, "io", rot=110)]
    return ks


SCENES.append({
    "id": "furnace", "map": "graveyard", "title": "Das Krematorium", "length": 7.2, "text": [1.3, 2.6],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.06, x=-1.2, y=-0.2), key(1.6, z=1.08, x=-0.7, y=-0.2), key(2.9, "io", z=1.16, x=0.4, y=-0.3),
               key(4.3, z=1.12, x=1.2, y=0.15), key(5.4, z=1.18, x=0.8, y=-0.55), key(7.2, z=1.2, x=0.6, y=-0.7)],
    "objects": [
        {"id": "bg", "sprite": "gy_eject_furnace_bg.jpg", "z": -100},
        {"id": "floorGlow", "sprite": GLOW, "z": -90, "x": OVEN_X, "y": -1.7, "sx": 5.0, "sy": 1.1, "tint": "#ff8a3c",
         "keys": [key(0, "hold", a=0.18), key(1.6, "hold", a=0.18), key(1.7, "out", a=0.55), key(3.05, "hold", a=0.55), key(3.15, "in", a=0.22),
                  key(5.3, "hold", a=0.22), key(5.7, a=0.4), key(7.2, a=0.3)], "flicker": {"amp": 0.25, "f": 7}},
        {"id": "ovenGlow", "sprite": GLOW, "z": -14, "x": OVEN_X, "y": OVEN_Y - 0.1, "sx": 2.4, "sy": 2.0, "tint": "#ff8a3c",
         "keys": [key(0, "hold", a=0.4), key(1.6, "hold", a=0.4), key(1.68, "out", a=0.95), key(3.05, "hold", a=0.95), key(3.15, "in", a=0.5),
                  key(5.3, "hold", a=0.5), key(5.7, a=0.75), key(7.2, a=0.6)], "flicker": {"amp": 0.3, "f": 9}},
    ] + [{"id": f"fire{i}", "sprite": FLAME, "z": -12, "x": OVEN_X + dx, "y": -0.92, "pivot": [0.5, 0.05], "s": sc, "a": 0.95,
           "wobble": [{"p": "sx", "amp": 0.12, "f": 6 + i * 1.3, "ph": i}, {"p": "sy", "amp": 0.2, "f": 8.5 + i * 0.9, "ph": i * 2},
                      {"p": "rot", "amp": 7, "f": 2.4 + i * 0.5, "ph": i}]}
         for i, (dx, sc) in enumerate(((-0.62, 0.9), (-0.3, 1.25), (0.02, 1.5), (0.34, 1.2), (0.64, 0.95)))] + [
        {"id": "door", "sprite": "gy_eject_door.png", "z": -10, "x": OVEN_X - 0.93, "y": OVEN_Y + 0.03, "pivot": [0, 0.5],
         "keys": [key(0, "hold", sx=1), key(1.6, "hold", sx=1), key(1.7, "out", sx=-0.2), key(1.8, "out", sx=-0.12), key(1.9, "io", sx=-0.18),
                  key(3.02, "hold", sx=-0.18), key(3.12, "in", sx=1), key(3.18, "out", sx=0.94), key(3.25, "in", sx=1),
                  key(5.3, "hold", sx=1), key(5.75, "io", sx=-0.16)],
         "wobble": [{"p": "x", "amp": 0.012, "f": 21, "t0": 3.3, "t1": 4.6}]},
        {"id": "slitGlow", "sprite": GLOW, "z": -9, "x": OVEN_X + 0.05, "y": OVEN_Y - 0.08, "sx": 1.6, "sy": 0.8, "tint": "#ff9a40",
         "keys": [key(0, "hold", a=0.25), key(1.6, "hold", a=0.25), key(1.62, "hold", a=0), key(3.12, "hold", a=0), key(3.2, "out", a=0.75),
                  key(4.6, "hold", a=0.75), key(5.3, a=0.3), key(5.35, "hold", a=0)], "flicker": {"amp": 0.35, "f": 11}},
        {"id": "needle", "sprite": "gy_eject_needle.png", "z": -8, "x": GAUGE[0], "y": GAUGE[1], "pivot": [0.05, 0.5], "s": 1.0,
         "keys": needle_keys(), "wobble": [{"p": "rot", "amp": 7, "f": 13, "t0": 3.5, "t1": 4.7}]},
        {"id": "urn", "sprite": "gy_eject_urn.png", "z": -6, "pivot": [0.5, 0],
         "keys": [key(0, "hold", x=OVEN_X + 0.1, y=-0.8, s=0.6, sx=1, sy=1, a=0, rot=0), key(5.6, "hold", a=0), key(5.62, "hold", a=1),
                  key(6.0, "in", x=OVEN_X - 0.55, y=-1.5, s=1.25, arc=0.55, rot=-12), key(6.07, "out", sx=1.15, sy=0.82, rot=0),
                  key(6.2, "io", sx=1, sy=1), key(6.35, "io", rot=6), key(6.5, "io", rot=-3), key(6.65, "io", rot=0)]},
        shadow(0.4),
    ],
    "player": {"hide": 3.02, "keys": [
        key(0, "lin", x=-6.6, y=FLOOR_Y, rot=0, s=1, sx=1, sy=1, a=1, flip=1), key(1.5, "out", x=-2.3),
        key(1.66, "hold", sx=1, sy=1), key(1.74, "out", sx=0.88, sy=1.15, rot=8), key(1.9, "io", sx=1, sy=1, rot=-6),
        key(2.62, "in", x=-0.35, y=FLOOR_Y, rot=-22, sx=1.12, sy=0.92),
        key(3.0, "in", x=OVEN_X, y=OVEN_Y - 0.05, s=0.3, sx=1, sy=1, rot=-400, arc=0.3),
        key(2.86, "hold", a=1), key(3.0, "in", a=0)],
        "wobble": [{"p": "y", "amp": 0.05, "f": 2.2, "t0": 0, "t1": 1.5}, {"p": "x", "amp": 0.03, "f": 15, "t0": 1.9, "t1": 2.6}]},
    "emitters": [
        em(FLAME, -12, t0=0, t1=7.2, rate=12, area=[OVEN_X - 0.7, -0.85, OVEN_X + 0.7, -0.6], vel=[-0.1, 0.7, 0.1, 1.3], grow=-0.9,
           life=[0.45, 0.75], size=[0.25, 0.42], rot=[-12, 12], a=0.9, fade=[0.1, 0.4]),
        em(MOTE, -40, t0=0, t1=7.2, rate=4, area=[OVEN_X - 1.0, -1.0, OVEN_X + 1.0, 0.3], vel=[-0.15, 0.15, 0.15, 0.45], life=[2, 3.5],
           size=[0.03, 0.06], tint="#ffae60", a=0.7),
        em(STREAK, 6, t0=1.75, t1=3.0, rate=40, area=[-5.4, -1.2, -0.6, 1.6], vel=[3.5, -0.4, 6.0, 0.3], life=[0.3, 0.5],
           size=[0.18, 0.32], tint="#d8b890", a=0.35, stretch=True, fade=[0.05, 0.1]),
        em(LEAF, 7, t0=1.8, t1=2.9, rate=10, area=[-5.2, -1.2, -1.0, 0.0], vel=[2.5, 0.0, 4.5, 0.8], drag=0.3, life=[0.6, 1.0],
           size=[0.08, 0.14], spin=[-500, 500], tint="#3a3430", a=0.9),
        burst(PX, -11, 1.66, 18, area=[OVEN_X - 0.6, -0.6, OVEN_X + 0.6, 0.3], vel=[-2.4, 0.2, 2.4, 2.8], acc=[0, -3], life=[0.4, 0.9],
              size=[0.03, 0.06], tint="#ffc070", a=1.0),
        em(PX, -7, t0=3.2, t1=4.6, rate=16, area=[OVEN_X - 0.5, -0.4, OVEN_X + 0.6, 0.1], vel=[-0.5, 0.4, 0.5, 1.4], acc=[0, -1.5], life=[0.4, 0.8],
           size=[0.025, 0.05], tint="#ffb050", a=1.0),
        burst(PUFF, -5, 3.12, 6, area=[OVEN_X - 1.0, -1.0, OVEN_X + 1.0, 0.6], vel=[-0.7, -0.2, 0.7, 0.4], drag=1.6, life=[0.6, 1.0],
              size=[0.35, 0.6], grow=0.6, tint="#4a4040", a=0.35),
        burst(PUFF, -5, 6.02, 4, area=[OVEN_X - 0.8, -1.55, OVEN_X - 0.3, -1.45], vel=[-0.4, 0.1, 0.4, 0.4], drag=1.6, life=[0.6, 1.0],
              size=[0.25, 0.4], grow=0.6, tint="#7a7070", a=0.35),
        em(PUFF, -4, t0=6.2, t1=7.2, rate=3, area=[OVEN_X - 0.6, -0.95, OVEN_X - 0.5, -0.9], vel=[-0.05, 0.25, 0.05, 0.45], drag=0.4,
           life=[1.2, 1.8], size=[0.12, 0.18], grow=0.9, tint="#9a9aa0", a=0.3),
    ],
    "events": steps(0.2, 1.4, 4, vol=0.2) + [
        ev(1.6, sound="slam", vol=0.8), ev(1.62, sound="fire", vol=0.8), ev(1.62, flash=["#ffb070", 0.45, 0.35]), ev(1.62, shake=[0.35, 0.06]),
        ev(1.85, sound="rush", vol=0.8), ev(2.4, sound="whoosh", vol=0.6), ev(2.85, sound="whoosh", vol=0.9),
        ev(3.12, sound="slam", vol=1.0), ev(3.12, shake=[0.4, 0.08]), ev(3.2, sound="fire", vol=0.9), ev(3.6, sound="sizzle", vol=0.4),
        ev(4.1, sound="fire", vol=0.6), ev(3.6, sound="click", vol=0.4), ev(4.6, sound="click", vol=0.3),
        ev(5.3, sound="creak", vol=0.7), ev(6.0, sound="clack", vol=0.7), ev(6.1, sound="pop", vol=0.25)],
})

# ============================================================================ Friedhof: Die Gruft
# Gewoelbe mit Grabnischen, Marmorsaeulen, zwei Kerzenstaendern und einem Buntglasfenster, durch das Mond-
# licht auf einen offenen Sarkophag faellt. Der Spieler tritt naeher, ein bandagierter Arm faehrt heraus und
# zieht ihn hinein. Der Deckel loest sich von der Saeule, schwebt herueber und schiebt sich knirschend zu. Die
# Kerzen verloeschen nacheinander, im Dunkeln gluehen die Augen eines Schaedels in seiner Nische auf.
SARC_X, SARC_Y = 0.5, -1.5
SHOULDER = (SARC_X - 0.45, -0.5)

SCENES.append({
    "id": "crypt", "map": "graveyard", "title": "Die Gruft", "length": 7.2, "text": [1.3, 2.6],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.06, x=-1.2, y=-0.1), key(2.0, z=1.1, x=-0.5, y=-0.2), key(3.3, "io", z=1.16, x=0.1, y=-0.35),
               key(5.2, z=1.12, x=0.4, y=-0.2), key(7.2, z=1.16, x=0.5, y=0.1)],
    "objects": [
        {"id": "bg", "sprite": "gy_eject_crypt_bg.jpg", "z": -100},
        {"id": "beamGlow", "sprite": GLOW, "z": -95, "x": SARC_X + 0.1, "y": -0.6, "sx": 2.6, "sy": 2.2, "tint": "#a8bce8", "a": 0.22,
         "flicker": {"amp": 0.15, "f": 0.4}},
    ] + [o for i, (cx, tout) in enumerate(((-3.6, 5.3), (4.4, 5.6))) for o in (
        {"id": f"cglow{i}", "sprite": GLOW, "z": -60, "x": cx, "y": 0.5, "sx": 3.0, "sy": 2.8, "tint": "#ffc274",
         "keys": [key(0, a=0.5), key(tout, "hold", a=0.5), key(tout + 0.2, "in", a=0)], "flicker": {"amp": 0.3, "f": 6 + i}},
        {"id": f"cflame{i}", "sprite": FLAME, "z": -58, "x": cx, "y": 0.34, "pivot": [0.5, 0.1], "s": 0.42,
         "keys": [key(0, a=1, sx=1, sy=1), key(tout - 0.08, "hold", a=1), key(tout, "out", sx=1.7, sy=0.45), key(tout + 0.06, "hold", a=0)],
         "wobble": [{"p": "sx", "amp": 0.1, "f": 7 + i}, {"p": "sy", "amp": 0.14, "f": 10.3}, {"p": "rot", "amp": 6, "f": 3.3},
                    {"p": "rot", "amp": 22, "f": 4, "t0": 4.8, "t1": 5.3}]})] + [
        {"id": "arm", "sprite": "gy_eject_mummy_arm.png", "z": 1, "x": SHOULDER[0], "y": SHOULDER[1], "pivot": [0.0, 0.5],
         "keys": [key(0, "hold", a=0, sx=-0.3, sy=1, rot=-80), key(2.15, "hold", a=0), key(2.16, "hold", a=1),
                  key(2.32, "out", sx=-0.95, rot=-30), key(2.46, "back", sx=-1.0, rot=-6), key(2.6, "hold", rot=-6),
                  key(3.0, "io", sx=-0.75, rot=-70), key(3.3, "in", sx=-0.3, rot=-95), key(3.35, "hold", a=0)],
         "wobble": [{"p": "rot", "amp": 3, "f": 5, "t0": 2.3, "t1": 2.6}]},
        {"id": "sarc", "sprite": "gy_eject_sarc.png", "z": 2, "x": SARC_X, "y": SARC_Y, "pivot": [0.5, 0]},
        {"id": "lid", "sprite": "gy_eject_sarc_lid.png", "z": 4,
         "keys": [key(0, "hold", x=2.88, y=-0.22, rot=80), key(3.7, "hold", x=2.88, y=-0.22, rot=80), key(3.85, "out", x=2.8, y=-0.1, rot=76),
                  key(4.45, "io", x=1.2, y=0.3, rot=4), key(4.8, "in", x=0.9, y=-0.38, rot=0), key(5.15, "out", x=SARC_X, y=-0.38),
                  key(5.2, "hold", x=SARC_X)],
         "wobble": [{"p": "y", "amp": 0.04, "f": 2.5, "t0": 3.85, "t1": 4.45}]},
        dark_overlay("dark", 5.55, 0.55, z=30, dur=0.35),
        {"id": "winGlow", "sprite": GLOW, "z": 31, "x": SARC_X, "y": 2.0, "sx": 2.2, "sy": 2.8, "tint": "#8fa8e0",
         "keys": [key(0, "hold", a=0), key(5.55, "hold", a=0), key(5.9, a=0.25)], "flicker": {"amp": 0.15, "f": 0.5}},
        {"id": "eyeGlow", "sprite": GLOW, "z": 32, "x": 0.58, "y": 0.6, "sx": 0.9, "sy": 0.5, "tint": "#ff3a2a",
         "keys": [key(0, "hold", a=0), key(6.15, "hold", a=0), key(6.3, "out", a=0.55)], "flicker": {"amp": 0.25, "f": 3}},
        {"id": "eyes", "sprite": EYES, "z": 33, "x": 0.58, "y": 0.6, "s": 0.2, "tint": "#ff5040",
         "keys": [key(0, "hold", a=0, sy=0.1), key(6.15, "hold", a=0, sy=0.1), key(6.2, "hold", a=1), key(6.32, "out", sy=1),
                  key(6.9, "hold", sy=1), key(6.95, "in", sy=0.1), key(7.02, "out", sy=1)]},
        shadow(0.4),
    ],
    "player": {"hide": 3.4, "keys": [
        key(0, "lin", x=-6.6, y=FLOOR_Y, rot=0, s=1, sx=1, sy=1, a=1, flip=1), key(1.95, "out", x=-1.45),
        key(2.15, "hold", sx=1, sy=1), key(2.22, "out", sx=0.88, sy=1.15, rot=6), key(2.4, "io", sx=1, sy=1, rot=0),
        key(2.5, "hold", x=-1.45, y=FLOOR_Y), key(2.62, "out", x=-1.3, rot=-12, sx=1.08, sy=0.94),
        key(3.0, "out", x=-0.15, y=0.45, rot=-140, sx=1, sy=1, arc=0.3), key(3.32, "in", x=SARC_X, y=-1.0, rot=-200)],
        "wobble": [{"p": "y", "amp": 0.05, "f": 2.2, "t0": 0, "t1": 1.95}, {"p": "x", "amp": 0.03, "f": 14, "t0": 2.45, "t1": 2.62}]},
    "emitters": [
        em(MOTE, -50, t0=0, t1=7.2, rate=5, area=[SARC_X - 1.0, -1.2, SARC_X + 1.6, 1.4], vel=[-0.05, -0.08, 0.05, 0.05], life=[3, 5],
           size=[0.03, 0.06], tint="#c8d4ea", a=0.55),
        burst(PUFF, 3, 3.35, 5, area=[SARC_X - 1.0, -0.25, SARC_X + 1.0, -0.1], vel=[-0.5, 0.2, 0.5, 0.6], drag=1.5, life=[0.7, 1.1],
              size=[0.3, 0.5], grow=0.6, tint="#8a8a84", a=0.3),
        burst(PUFF, 5, 5.15, 8, area=[SARC_X - 1.3, -0.25, SARC_X + 1.3, -0.05], vel=[-0.9, 0.0, 0.9, 0.4], drag=1.6, life=[0.7, 1.2],
              size=[0.3, 0.55], grow=0.7, tint="#8a8a84", a=0.35),
        burst(PX, 5, 3.85, 8, area=[2.6, -1.4, 3.1, 1.1], vel=[-0.3, -0.6, 0.3, -0.1], acc=[0, -3], life=[0.6, 1.0], size=[0.03, 0.06],
              tint="#9a9a90", a=0.8),
    ] + [burst(PUFF, -57, t, 3, area=[cx - 0.05, 0.4, cx + 0.05, 0.5], vel=[-0.2, 0.3, 0.2, 0.7], life=[0.9, 1.4], size=[0.15, 0.25],
               grow=0.9, tint="#9a9aa6", a=0.45) for cx, t in ((-3.6, 5.32), (4.4, 5.62))],
    "events": steps(0.3, 1.8, 5, vol=0.18) + [
        ev(2.16, sound="growl", vol=0.5), ev(2.2, sound="whoosh", vol=0.5), ev(2.45, sound="clack", vol=0.4), ev(2.7, sound="whoosh", vol=0.7),
        ev(3.32, sound="thud", vol=0.7), ev(3.32, shake=[0.3, 0.05]), ev(3.85, sound="creak", vol=0.5), ev(4.5, sound="whoosh", vol=0.3),
        ev(4.8, sound="grind", vol=0.8), ev(5.15, sound="thud", vol=0.9), ev(5.15, shake=[0.35, 0.07]), ev(5.15, sound="boom", vol=0.35),
        ev(5.3, sound="whoosh", vol=0.3), ev(5.6, sound="whoosh", vol=0.3), ev(6.2, sound="growl", vol=0.45), ev(6.25, sound="organ", vol=0.3)],
})

# ============================================================================ Friedhof (Skip): Der Rabenrat
# Niemand fliegt. Ein toter Baum vor dem Vollmond, darauf sitzen acht Raben und halten Gericht: sie
# drehen die Koepfe, putzen sich, eine Eule ruft. Ein Blitz, und der ganze Schwarm fliegt auf, kreist einmal
# um den Mond und verschwindet. Federn trudeln herab. Ein einzelner Rabe kehrt zurueck und setzt sich wieder
# ganz oben hin.
MOON_R = (0.2, 1.6)
TAKEOFF = 3.25


def crow_objects():
    objs = []
    for i, (px, py) in enumerate(PERCH):
        flip0 = 1 if (i % 2 == 0) else -1
        turns = [key(0, "hold", sx=flip0)]
        for k in range(2):                                                    # Kopf drehen zu versetzten Zeiten
            t = 0.5 + ((i * 0.37 + k * 1.1) % 2.4)
            turns.append(key(round(t, 2), "hold", sx=flip0 * (-1 if k % 2 == 0 else 1)))
        t_off = TAKEOFF + (i * 0.047) % 0.25
        objs.append({"id": f"c{i}", "sprite": "gy_eject_crow.png", "z": -40 + i, "x": px, "y": py - 0.1, "pivot": [0.47, 0.07],
                     "keys": [key(0, "hold", a=1)] + [k_ for k_ in turns[1:]] + [key(t_off, "hold", a=1), key(t_off + 0.01, "hold", a=0)],
                     "wobble": [{"p": "rot", "amp": 2.5, "f": 0.6 + 0.13 * i, "ph": i}, {"p": "sy", "amp": 0.03, "f": 1.4 + 0.1 * i, "ph": i}]})
        # Fluegelschlag ueber sy; Flug als Kreis um den Mond, dann hinaus
        ks = [key(0, "hold", x=px, y=py, a=0, s=0.75, flip=flip0), key(t_off, "hold", a=0), key(t_off + 0.01, "hold", a=1)]
        r = 1.9 + 0.22 * (i % 4)
        a0 = math.atan2(py - MOON_R[1], px - MOON_R[0])
        dirn = 1 if i % 2 == 0 else -1
        t = t_off
        prev = (px, py)
        for k in range(1, 9):
            ang = a0 + dirn * k * 0.62
            x, y = MOON_R[0] + r * math.cos(ang), MOON_R[1] + r * 0.55 * math.sin(ang)
            t += 0.13
            ks.append(key(t, "lin", x=round(x, 3), y=round(y, 3), flip=1 if x > prev[0] else -1, s=round(0.75 - 0.02 * k, 3)))
            prev = (x, y)
        ex = 7.2 if prev[0] > MOON_R[0] else -7.2
        ks.append(key(t + 0.7, "in", x=ex, y=round(3.0 + 0.2 * (i % 3), 2), s=0.4, flip=1 if ex > 0 else -1))
        objs.append({"id": f"f{i}", "sprite": "gy_eject_crow_fly.png", "z": -30 + i, "keys": ks,
                     "wobble": [{"p": "sy", "amp": 0.45, "f": 8.5 + 0.4 * i, "ph": i}]})
    # der eine, der zurueckkommt
    hx, hy = PERCH[2]
    objs.append({"id": "back", "sprite": "gy_eject_crow_fly.png", "z": -20,
                 "keys": [key(0, "hold", x=6.5, y=3.4, a=0, s=0.5, flip=-1), key(5.15, "hold", a=0), key(5.16, "hold", a=1),
                          key(5.85, "out", x=hx + 0.05, y=hy + 0.08, s=0.75), key(5.86, "hold", a=0)],
                 "wobble": [{"p": "sy", "amp": 0.45, "f": 9, "t1": 5.8}]})
    objs.append({"id": "backSit", "sprite": "gy_eject_crow.png", "z": -19, "x": hx, "y": hy - 0.1, "pivot": [0.47, 0.07],
                 "keys": [key(0, "hold", a=0, sx=-1), key(5.85, "hold", a=0), key(5.86, "hold", a=1, sy=0.85), key(5.98, "out", sy=1),
                          key(6.5, "hold", sx=-1), key(6.51, "hold", sx=1)]})
    return objs


SCENES.append({
    "id": "skip_ravens", "map": "graveyard", "skip": True, "title": "Der Rabenrat", "length": 6.6, "text": [1.0, 2.8],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.04, x=0.0, y=0.25), key(3.1, z=1.1, x=0.0, y=0.42), key(3.3, "out", z=1.08, x=0.05, y=0.42),
               key(5.0, z=1.06, x=0.1, y=0.38), key(6.6, z=1.1, x=-0.2, y=0.42)],
    "objects": [
        {"id": "bg", "sprite": "gy_eject_roost_bg.jpg", "z": -100},
        {"id": "moonglow", "sprite": GLOW, "z": -96, "x": MOON_R[0], "y": MOON_R[1], "s": 3.6, "tint": "#c8d8f0",
         "keys": [key(0, a=0.3), key(3.15, "hold", a=0.3), key(3.2, "out", a=0.7), key(3.8, a=0.3)], "flicker": {"amp": 0.15, "f": 0.25}},
        {"id": "mist1", "sprite": MIST, "z": 20, "x": -2.8, "y": -2.3, "s": 1.5, "a": 0.38, "tint": "#aab4c8",
         "wobble": [{"p": "x", "amp": 0.35, "f": 0.11}]},
        {"id": "mist2", "sprite": MIST, "z": 20, "x": 3.2, "y": -2.6, "s": 1.6, "a": 0.32, "tint": "#aab4c8",
         "wobble": [{"p": "x", "amp": 0.3, "f": 0.1, "ph": 2}]},
    ] + crow_objects(),
    "player": {"keys": [key(0, "hold", x=0, y=FLOOR_Y)]},
    "emitters": [
        em(MOTE, -50, t0=0, t1=6.6, rate=4, area=[-5, -1.5, 5, 1.5], vel=[-0.08, -0.04, 0.08, 0.08], life=[3, 5], size=[0.03, 0.06],
           tint="#c8d4ea", a=0.45),
        em(LEAF, 10, t0=2.9, t1=3.7, rate=14, area=[-6.0, -1.8, -4.8, 1.2], vel=[3.0, -0.4, 5.5, 0.8], drag=0.4, life=[1.4, 2.2],
           size=[0.1, 0.18], spin=[-500, 500], tint="#6a5a3e", a=0.9),
        burst(LEAF, -10, TAKEOFF + 0.05, 14, area=[-3.0, 0.4, 2.7, 2.6], vel=[-0.3, -0.3, 0.3, 0.1], drag=0.9, life=[2.0, 3.2],
              size=[0.07, 0.12], spin=[-200, 200], tint="#16161c", a=0.95),
    ],
    "events": [
        ev(0.7, sound="owl", vol=0.45), ev(1.3, sound="twig", vol=0.25), ev(2.1, sound="creak", vol=0.3), ev(2.6, sound="twig", vol=0.2),
        ev(3.1, flash=["#dfe8ff", 0.5, 0.35]), ev(3.15, sound="thunder", vol=0.7), ev(3.1, sound="rush", vol=0.5),
        ev(TAKEOFF, sound="whoosh", vol=0.8), ev(TAKEOFF + 0.15, sound="whoosh", vol=0.6), ev(TAKEOFF + 0.05, shake=[0.3, 0.03]),
        ev(5.86, sound="twig", vol=0.35), ev(6.2, sound="owl", vol=0.3)],
})

# ============================================================================ Sonderszene: Sadako kehrt heim
# Nur wenn der Ausgeworfene das Sadako-Kostuem traegt. Brunnenhaus bei Nacht, ein Mondstrahl faellt auf den
# alten Brunnen. Das Bild flimmert an wie ein Videoband. Der Spieler steigt auf den Rand und laesst sich in den
# Schacht fallen, weit unten platscht es. Die Laterne erlischt. Dann klatscht nasses schwarzes Haar ueber den
# Rand, zwei bleiche Haende krallen sich fest, und die Gestalt kriecht ruckartig heraus und auf die Kamera zu,
# bis das Bildrauschen alles verschluckt.
WELL_X, WELL_Y, WS = 0.6, -1.85, 1.35
RIM_FRONT = WELL_Y + 0.72 * WS                # Vorderkante des Brunnenkranzes
SWAP = 5.95                                    # ab hier steht die Vorderwand hinter der Figur
CRAWL = [dict(x=WELL_X, y=-1.32, rot=0, s=1.0), dict(x=WELL_X, y=-1.0, rot=-6), dict(x=WELL_X + 0.05, y=-0.62, rot=-14),
         dict(x=WELL_X + 0.05, y=-0.28, rot=-30), dict(x=WELL_X, y=0.0, rot=-62), dict(x=WELL_X - 0.05, y=-0.4, rot=-78, s=1.1),
         dict(x=WELL_X - 0.1, y=-1.0, rot=-64, s=1.22), dict(x=WELL_X - 0.15, y=-1.55, rot=-44, s=1.42),
         dict(x=WELL_X - 0.2, y=-1.9, rot=-26, s=1.75), dict(x=WELL_X - 0.25, y=-2.05, rot=-12, s=2.3), dict(x=WELL_X - 0.3, y=-2.0, rot=-4, s=3.2),
         dict(x=WELL_X - 0.35, y=-1.85, rot=0, s=4.4)]
CRAWL_T0 = 5.1


def sadako_player():
    ks = [key(0, "lin", x=-6.6, y=FLOOR_Y, rot=0, s=1, sx=1, sy=1, a=1, flip=1), key(1.8, "out", x=WELL_X - 1.75),
          key(2.0, "hold", x=WELL_X - 1.75, y=FLOOR_Y), key(2.16, "out", y=0.2), key(2.35, "io", x=WELL_X), key(2.35, "in", y=0.02),
          key(2.42, "out", sx=1.08, sy=0.9),
          key(2.55, "io", sx=1, sy=1), key(2.7, "hold", flip=-1), key(2.95, "hold", flip=1),
          key(3.15, "hold", y=0.02), key(3.42, "in", y=-1.32), key(3.3, "hold", a=1), key(3.42, "in", a=0),
          key(CRAWL_T0 - 0.01, "hold", a=0), key(CRAWL_T0, "hold", a=1)]
    ks += jerk(CRAWL_T0, CRAWL, move=0.07, pause=0.12)
    return ks


def crawl_end():
    return CRAWL_T0 + (len(CRAWL) - 1) * 0.19 + 0.12


def static_keys():
    t_end = crawl_end()
    ks = [key(0, "hold", a=0.75), key(0.15, "hold", a=0.45), key(0.22, "hold", a=0.6), key(0.5, "in", a=0),
          key(4.2, "hold", a=0), key(4.22, "hold", a=0.35), key(4.32, "hold", a=0.05), key(4.36, "hold", a=0.28), key(4.45, "hold", a=0)]
    t, a = CRAWL_T0, 0.0
    for i in range(1, len(CRAWL)):                                            # jeder Ruck ein Bildfehler, immer staerker
        t += 0.19
        a = min(0.62, 0.02 + 0.052 * i)
        ks += [key(t - 0.12, "hold", a=round(a * 0.5, 3)), key(t - 0.1, "hold", a=round(a, 3))]
    ks += [key(t_end, "hold", a=0.9), key(t_end + 0.1, "lin", a=1.0), key(t_end + 0.6, "hold", a=1.0), key(t_end + 0.9, "lin", a=0.25)]
    return ks


SCENES.append({
    "id": "special_sadako", "map": "graveyard", "title": "Sadako kehrt heim", "length": 8.5, "text": [1.3, 2.6],
    "bounds": [12, 6.8],
    "camera": [key(0, "lin", z=1.05, x=-0.8, y=-0.2), key(2.3, z=1.1, x=0.1, y=-0.2), key(3.6, "out", z=1.2, x=0.5, y=-0.6),
               key(4.6, z=1.24, x=0.6, y=-0.7), key(CRAWL_T0 + 0.9, z=1.3, x=0.5, y=-0.6), key(crawl_end(), "in", z=1.55, x=0.3, y=-1.25),
               key(8.5, z=1.6, x=0.3, y=-1.25)],
    "objects": [
        {"id": "bg", "sprite": "gy_eject_wellhouse_bg.jpg", "z": -100},
        {"id": "lantern", "sprite": GLOW, "z": -90, "x": -4.4, "y": 1.0, "sx": 2.6, "sy": 2.4, "tint": "#ffc274",
         "keys": [key(0, a=0.45), key(3.9, "hold", a=0.45), key(3.95, "hold", a=0.1), key(4.02, "hold", a=0.4), key(4.08, "hold", a=0.05),
                  key(4.12, "hold", a=0.3), key(4.16, "hold", a=0)], "flicker": {"amp": 0.3, "f": 6}},
        {"id": "lanternDark", "sprite": GLOW, "z": -89, "x": -4.4, "y": 0.95, "s": 0.4, "tint": "#000000",
         "keys": [key(0, "hold", a=0), key(4.16, "hold", a=0), key(4.2, a=0.7)]},
        {"id": "moonbeam", "sprite": GLOW, "z": -88, "x": WELL_X + 0.4, "y": -1.3, "sx": 3.6, "sy": 1.1, "tint": "#b8c8f0", "a": 0.28,
         "flicker": {"amp": 0.12, "f": 0.4}},
        {"id": "wellBack", "sprite": "gy_eject_well_back.png", "z": -12, "x": WELL_X, "y": WELL_Y, "pivot": [0.5, 0], "s": WS},
        {"id": "ripple", "sprite": RIPPLE, "z": -11, "x": WELL_X, "y": WELL_Y + 0.95 * WS, "tint": "#a8c0e8",
         "keys": [key(0, "hold", a=0, sx=0.2, sy=0.12), key(3.62, "hold", a=0), key(3.64, "hold", a=0.8), key(4.4, "out", a=0, sx=0.9, sy=0.3)]},
        {"id": "wellFrontB", "sprite": "gy_eject_well_front.png", "z": -8, "x": WELL_X, "y": WELL_Y, "pivot": [0.5, 0], "s": WS,
         "keys": [key(0, "hold", a=0), key(SWAP, "hold", a=0), key(SWAP + 0.01, "hold", a=1)]},
        {"id": "wellFront", "sprite": "gy_eject_well_front.png", "z": 10, "x": WELL_X, "y": WELL_Y, "pivot": [0.5, 0], "s": WS,
         "keys": [key(0, "hold", a=1), key(SWAP, "hold", a=1), key(SWAP + 0.01, "hold", a=0)]},
        {"id": "hair", "sprite": "gy_eject_hair.png", "z": 11, "x": WELL_X, "y": RIM_FRONT + 0.1, "pivot": [0.5, 1], "sx": 0.95,
         "keys": [key(0, "hold", a=0, sy=0.0), key(4.55, "hold", a=0, sy=0.0), key(4.56, "hold", a=1), key(4.78, "out", sy=0.7),
                  key(4.86, "in", sy=0.64), key(5.6, "hold", sy=0.64, a=1), key(5.75, "in", a=0, sy=0.3)],
         "wobble": [{"p": "sx", "amp": 0.03, "f": 1.1, "t0": 4.8, "t1": 5.7}]},
    ] + [{"id": f"hand{i}", "sprite": "gy_eject_pale_hand.png", "z": 12, "x": WELL_X + dx, "y": RIM_FRONT - 0.32, "pivot": [0.5, 0],
          "sx": -1 if dx > 0 else 1, "rot": -8 if dx < 0 else 8,
          "keys": [key(0, "hold", a=0, s=0.6), key(t, "hold", a=0), key(t + 0.01, "hold", a=1), key(t + 0.1, "back", s=1.0),
                   key(5.7, "hold", a=1), key(5.85, "in", a=0)]}
         for i, (dx, t) in enumerate(((-0.72, 4.88), (0.74, 5.05)))] + [
        {"id": "dark", "sprite": PX, "z": 40, "s": 100, "tint": "#000000", "screen": True,
         "keys": [key(0, "hold", a=0), key(crawl_end() + 0.05, "hold", a=0), key(crawl_end() + 0.12, "lin", a=1)]},
        {"id": "static", "sprite": "gy_eject_static.png", "z": 45, "screen": True, "sx": 3.6, "sy": 3.6, "keys": static_keys(),
         "wobble": [{"p": "x", "amp": 0.18, "f": 23}, {"p": "y", "amp": 0.14, "f": 17, "ph": 1}]},
        {"id": "roll", "sprite": PX, "z": 46, "screen": True, "sx": 80, "sy": 2.2, "tint": "#ffffff",
         "keys": [key(0, "hold", y=3.3, a=0.08)] + [k_ for j in range(6) for k_ in (key(j * 1.4 + 0.01, "hold", y=3.3), key(j * 1.4 + 1.4, "lin", y=-3.3))]},
    ],
    "player": {"hide": round(crawl_end() + 0.12, 2), "keys": sadako_player(),
               "wobble": [{"p": "y", "amp": 0.05, "f": 2.2, "t0": 0, "t1": 1.8}, {"p": "x", "amp": 0.02, "f": 19, "t0": CRAWL_T0, "t1": crawl_end()}]},
    "emitters": [
        em(MOTE, -50, t0=0, t1=8.5, rate=4, area=[WELL_X - 1.5, -1.5, WELL_X + 2.5, 1.5], vel=[-0.05, -0.08, 0.05, 0.05], life=[3, 5],
           size=[0.03, 0.06], tint="#c8d4ea", a=0.5),
        burst(DROP, -9, 3.62, 9, area=[WELL_X - 0.3, -0.6, WELL_X + 0.3, -0.5], vel=[-0.9, 1.6, 0.9, 3.2], acc=[0, -10], life=[0.4, 0.7],
              size=[0.05, 0.1], tint="#c0d4f0", a=0.85, stretch=True),
        em(DROP, 13, t0=4.8, t1=5.8, rate=7, area=[WELL_X - 0.7, RIM_FRONT - 0.85, WELL_X + 0.7, RIM_FRONT - 0.7], vel=[0, -0.4, 0, -0.2],
           acc=[0, -7], life=[0.3, 0.5], size=[0.04, 0.07], tint="#a8c0e0", a=0.8, stretch=True),
        em(DROP, -95, t0=0, t1=8.5, rate=0.8, area=[-5.0, 2.95, 5.0, 3.0], vel=[0, -0.2, 0, 0], acc=[0, -8], life=[0.7, 0.8],
           size=[0.03, 0.05], tint="#8aa0c0", a=0.6, stretch=True),
        burst(PUFF, 12, 4.57, 3, area=[WELL_X - 0.6, RIM_FRONT - 0.1, WELL_X + 0.6, RIM_FRONT + 0.1], vel=[-0.4, -0.1, 0.4, 0.2], drag=1.6,
              life=[0.5, 0.8], size=[0.25, 0.4], grow=0.5, tint="#8090a8", a=0.25),
    ],
    "events": [ev(0.0, sound="zap", vol=0.3)] + steps(0.4, 1.7, 4, vol=0.18) + [
        ev(2.05, sound="step", vol=0.3), ev(2.38, sound="clack", vol=0.4), ev(2.9, sound="creak", vol=0.3),
        ev(3.2, sound="whoosh", vol=0.5), ev(3.64, sound="splash", vol=0.6), ev(4.0, sound="click", vol=0.2),
        ev(3.95, sound="sizzle", vol=0.3), ev(4.22, sound="zap", vol=0.35), ev(4.57, sound="splash", vol=0.35), ev(4.6, sound="growl", vol=0.35),
        ev(4.89, sound="thud", vol=0.5), ev(5.06, sound="thud", vol=0.5)] + [
        ev(round(CRAWL_T0 + 0.19 * i, 2), sound="twig" if i % 2 else "click", vol=round(0.25 + 0.03 * i, 2)) for i in range(1, len(CRAWL))] + [
        ev(5.4, sound="growl", vol=0.55), ev(crawl_end() - 0.3, sound="growl", vol=0.75),
        ev(crawl_end(), sound="zap", vol=0.8), ev(crawl_end(), flash=["#ffffff", 0.6, 0.25]), ev(crawl_end(), shake=[0.3, 0.06])],
})


# ---------------------------------------------------------------------------- Pruefung
def lint():
    errors = 0

    def err(msg):
        nonlocal errors
        errors += 1
        print("  FEHLER:", msg)

    ids = set()
    for sc in SCENES:
        if sc["id"] in ids:
            err(f"doppelte Szene {sc['id']}")
        ids.add(sc["id"])
        if sc.get("map") != "graveyard":
            err(f"{sc['id']}: map {sc.get('map')}")
        obj_ids = set()
        for o in sc["objects"]:
            if o["id"] in obj_ids:
                err(f"{sc['id']}: doppelte Objekt-Id {o['id']}")
            obj_ids.add(o["id"])
        for o in sc["objects"]:
            p = o.get("parent")
            if p and p != "player" and p not in obj_ids:
                err(f"{sc['id']}/{o['id']}: parent {p} unbekannt")
            if p and p != "player" and p in obj_ids and [x["id"] for x in sc["objects"]].index(p) > sc["objects"].index(o):
                err(f"{sc['id']}/{o['id']}: parent {p} steht spaeter in der Liste (Engine kennt ihn dann noch nicht)")
            for w in o.get("wobble", []):
                if w["p"] not in PROPS or "amp" not in w or "f" not in w:
                    err(f"{sc['id']}/{o['id']}: wobble {w}")
            if "flicker" in o and not {"amp", "f"} <= set(o["flicker"]):
                err(f"{sc['id']}/{o['id']}: flicker {o['flicker']}")
            sp = o.get("sprite")
            if sp and not sp.startswith(SPRITE_PREFIX):
                err(f"{sc['id']}/{o['id']}: Sprite {sp}")
        pl = sc["player"]
        if sc.get("skip") and "hide" in pl:
            err(f"{sc['id']}: Skip-Szene mit hide")
        if not sc.get("skip") and "hide" not in pl:
            err(f"{sc['id']}: Spieler-Szene ohne hide")
        if "hide" in pl and pl["hide"] > sc["length"] - 1.0:
            err(f"{sc['id']}: hide {pl['hide']} zu spaet")
        for o in sc["objects"] + [dict(pl, id="player")] + [{"id": "camera", "keys": sc["camera"]}]:
            for t, props, ease in o.get("keys", []):
                if ease not in EASES:
                    err(f"{sc['id']}/{o['id']}: ease {ease}")
                if t < 0 or t > sc["length"] + 0.01:
                    err(f"{sc['id']}/{o['id']}: Key bei {t}s ausserhalb der Szene")
                for pr in props:
                    if pr not in PROPS and not (o["id"] == "camera" and pr == "z"):
                        err(f"{sc['id']}/{o['id']}: Eigenschaft {pr}")
        for e in sc["emitters"]:
            if "burst" in e:
                if "n" not in e:
                    err(f"{sc['id']}: burst ohne n ({e['sprite']})")
                elif e["burst"] > sc["length"]:
                    err(f"{sc['id']}: burst nach Szenenende")
            elif not {"t0", "t1", "rate"} <= set(e):
                err(f"{sc['id']}: Emitter ohne t0/t1/rate ({e['sprite']})")
            if not e["sprite"].startswith(SPRITE_PREFIX):
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
    res = Path(__file__).resolve().parent.parent / "Resources"
    for name in sprites():
        if not ((res / "graveyard_eject" / name).exists() or (res / "villa" / name).exists()):
            err(f"Sprite-Datei fehlt: {name}")
    return errors


def sprites():
    names = set()
    for sc in SCENES:
        for o in sc["objects"]:
            if o.get("sprite"):
                names.add(o["sprite"])
        for e in sc["emitters"]:
            names.add(e["sprite"])
    return sorted(names)


# Daempfung aller Effekte (gleiche Werte wie die Villa)
FX = {"shake": 0.55, "flash": 0.55, "flicker": 0.65, "glow": 0.9, "rate": 0.75, "burst": 0.8, "palpha": 0.85,
      "vignette": 0.6, "volume": 0.55}


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
        if o.get("sprite") == GLOW:
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
        print(f"  {sc['id']:16s} {sc['length']:.1f} s  {'skip' if sc.get('skip') else 'player'}  {sc['title']}")
    print("  sprites:", ", ".join(sprites()))


if __name__ == "__main__":
    main()
