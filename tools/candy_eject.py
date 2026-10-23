# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# candy_eject.py - Regie der Rauswurf-Szene "Die Suessigkeitenschuessel" -> Resources/candy_eject/candy_eject.json.
#
# Gleiches Format wie villa_eject.py und graveyard_eject.py (Objekte mit Keyframes je Eigenschaft, Partikel-Emitter,
# Kamera, Ereignisse), abgespielt von Villa/EjectEngine.cs auf den Vanilla-Karten, sobald die Halloween-Optik an ist
# (Villa/CandyBowlEject.cs). Einheiten: 1 = 180 px der Grafik, Ursprung Bildmitte, y nach oben, sichtbar 11 x 6,2
# bei Zoom 1. Die Grafik erzeugt gen_candy_eject.py, die vier eigenen Klaenge gen_candy_sfx.py (sfx_*.wav, von der
# Engine den Synth-Klaengen vorgezogen); Glimmen, Staub und Wolken kommen aus dem Villa-Satz.
#
# Ablauf (7,6 s): der Ausgeworfene faellt von oben in eine riesige Schuessel voll Halloween-Suessigkeiten, taucht
# unter und kommt wieder hoch. Hinter der Schuessel erhebt sich ein lila Zottelmonster, rollt die Augen, packt ihn
# mit der Pranke, hebt ihn ins Maul und kaut dreimal (Kruemel), schluckt, ruelpst, und nur das Bonbonpapier segelt
# auf den Tisch. Das Maul ist eine Hoehle im Rumpf, der Unterkiefer faehrt davor nach unten; der Spieler steht
# beim Biss vor der Hoehle und wird beim Zuschnappen ausgeblendet.
#
#     python tools/candy_eject.py

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "Resources" / "candy_eject" / "candy_eject.json"
SOUNDS = {"boom", "chime", "clack", "click", "creak", "fire", "grind", "growl", "organ", "owl", "pop", "rush",
          "sizzle", "slam", "splash", "step", "thud", "thunder", "twig", "whoosh", "zap", "roar",
          "rustle", "munch", "gulp", "burp"}                     # die letzten vier: sfx_*.wav aus gen_candy_sfx.py
EASES = {"lin", "in", "out", "io", "back", "inback", "hold"}
PROPS = {"x", "y", "rot", "sx", "sy", "s", "a", "b", "flip", "arc"}
SPRITE_PREFIX = ("cb_eject_", "villa_eject_", "task_eject_")


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


GLOW, MOTE, PUFF, CLOUD = "villa_eject_glow.png", "villa_eject_mote.png", "villa_eject_puff.png", "villa_eject_cloud.png"
TWIST, TWIST2, BEAN, EYE, PUMP, CORN, LOLLY, CRUMB, WRAPPER = (
    "cb_eject_candy_twist.png", "cb_eject_candy_twist2.png", "cb_eject_candy_bean.png", "cb_eject_candy_eye.png",
    "cb_eject_candy_pump.png", "cb_eject_candy_corn.png", "cb_eject_candy_lolly.png", "cb_eject_crumb.png", "cb_eject_wrapper.png")

FLOOR = -1.25             # Tischplatte
BOWL_X = 0.3
MON_Y = -0.65             # Fuss des Monsters (hinter Tisch und Schuessel; Maul ueber dem Schuesselrand)
MON_START = -8.5          # Start weit unter dem Bild (Augen und Pranken ausserhalb)
EYE_DX, EYE_Y = 0.88, 3.5    # Augen relativ zum Monsterfuss
JAW_Y = 2.7               # Oberkante des Unterkiefers relativ zum Fuss (geschlossen)
PAW_X, PAW_Y = 2.6, 0.5   # Schultern relativ zum Fuss (breit und tief, damit die Pranke in die Schuessel reicht)
PAW_SHOW = 3.05           # ab hier sind die Schultern ueber der Tischkante: Pranken einblenden
PLAYER = (0.9, 0.75)      # Sitzplatz im Haufen, rechts vor der Wange
MOUTH = (1.0, 1.35)       # wohin die Pranke ihn hebt (rechte Maulhaelfte)

# Spielerfarben als Tint fuer die Gummi-Crewmates
BEAN_TINTS = ("#d02020", "#2a48e0", "#2aa050", "#f0e060", "#f08a28", "#8a48d8", "#50f0d8", "#f070c8")

SCENES = []


def pupil(sgn):
    bx, by = sgn * EYE_DX, EYE_Y
    return {"id": f"pupil{'L' if sgn < 0 else 'R'}", "sprite": "cb_eject_pupil.png", "parent": "monster", "z": -28, "s": 1.0, "keys": [
        key(0, "hold", x=bx - 0.16, y=by - 0.1), key(3.3, "hold", x=bx - 0.16, y=by - 0.1),
        key(3.5, "out", x=bx + 0.2, y=by + 0.05), key(3.75, "io", x=bx - 0.2, y=by + 0.02),
        key(3.95, "io", x=bx + 0.2, y=by - 0.2), key(4.5, "io", x=bx + 0.12, y=by - 0.2),
        key(5.0, "io", x=bx + 0.1, y=by - 0.1), key(5.7, "hold", x=bx + 0.1, y=by - 0.1),
        key(5.9, "out", x=bx, y=by + 0.22), key(6.5, "io", x=bx, y=by - 0.04), key(7.6, "lin", x=bx + 0.05, y=by - 0.06)]}


def lid(sgn):
    bx = sgn * EYE_DX
    return {"id": f"lid{'L' if sgn < 0 else 'R'}", "sprite": "cb_eject_lid.png", "parent": "monster", "z": -27, "pivot": [0.5, 0], "x": bx, "s": 0.92, "keys": [
        key(0, "hold", y=EYE_Y + 0.6, a=0), key(5.7, "hold", y=EYE_Y + 0.6, a=0), key(5.72, "hold", a=1),
        key(5.95, "out", y=EYE_Y - 0.08), key(6.55, "hold", y=EYE_Y - 0.08), key(6.85, "io", y=EYE_Y + 0.6), key(6.87, "hold", a=0)]}


def paw_right():
    return {"id": "pawR", "sprite": "cb_eject_monster_paw.png", "parent": "monster", "z": 15, "pivot": [0.5, 0.02], "x": PAW_X, "y": PAW_Y, "keys": [
        key(0, "hold", rot=-20, a=0), key(PAW_SHOW, "hold", rot=-20, a=0), key(PAW_SHOW + 0.01, "hold", a=1),
        key(3.3, "hold", rot=-20), key(3.5, "out", rot=-38), key(3.9, "io", rot=-18),
        key(4.15, "out", rot=66), key(4.55, "io", rot=56), key(4.75, "in", rot=48), key(4.98, "out", rot=-8),
        key(5.6, "io", rot=-24), key(6.2, "out", rot=-40), key(6.6, "io", rot=-22), key(7.6, "lin", rot=-20)],
        "wobble": [{"p": "rot", "amp": 2.5, "f": 7, "t0": 4.15, "t1": 4.75}]}


def paw_left():
    return {"id": "pawL", "sprite": "cb_eject_monster_paw.png", "parent": "monster", "z": 15, "pivot": [0.5, 0.02], "x": -PAW_X, "y": PAW_Y, "flip": -1, "keys": [
        key(0, "hold", rot=20, a=0), key(PAW_SHOW, "hold", rot=20, a=0), key(PAW_SHOW + 0.01, "hold", a=1), key(3.3, "hold", rot=20), key(3.5, "out", rot=38), key(3.9, "io", rot=22),
        key(4.15, "out", rot=10), key(5.6, "io", rot=26), key(6.2, "out", rot=44), key(6.6, "io", rot=24), key(7.6, "lin", rot=22)]}


def jaw():
    return {"id": "jaw", "sprite": "cb_eject_monster_jaw.png", "parent": "monster", "z": -29, "pivot": [0.5, 1], "x": 0.0, "keys": [
        key(0, "hold", y=JAW_Y), key(3.3, "hold", y=JAW_Y), key(3.45, "out", y=JAW_Y - 0.3), key(3.85, "io", y=JAW_Y),
        key(4.35, "hold", y=JAW_Y), key(4.55, "out", y=JAW_Y - 0.85), key(4.75, "hold", y=JAW_Y - 0.85),
        key(4.82, "in", y=JAW_Y), key(4.98, "out", y=JAW_Y - 0.45), key(5.08, "in", y=JAW_Y),
        key(5.24, "out", y=JAW_Y - 0.45), key(5.34, "in", y=JAW_Y), key(5.9, "hold", y=JAW_Y),
        key(6.2, "out", y=JAW_Y - 0.75), key(6.55, "io", y=JAW_Y)]}


def monster():
    return {"id": "monster", "sprite": "cb_eject_monster_body.png", "z": -30, "pivot": [0.5, 0], "x": BOWL_X, "keys": [
        key(0, "hold", y=MON_START, sx=1, sy=1), key(2.6, "hold", y=MON_START), key(3.3, "out", y=MON_Y), key(3.42, "in", y=MON_Y - 0.15), key(3.6, "out", y=MON_Y),
        key(4.75, "hold", sy=1, sx=1), key(4.82, "out", sy=0.95, sx=1.02), key(4.95, "io", sy=1, sx=1),
        key(5.08, "out", sy=0.95, sx=1.02), key(5.2, "io", sy=1, sx=1), key(5.34, "out", sy=0.95, sx=1.02), key(5.46, "io", sy=1, sx=1),
        key(5.75, "hold", sy=1, sx=1), key(5.9, "out", sy=1.06, sx=0.97), key(6.05, "in", sy=1, sx=1),
        key(6.2, "out", sy=0.94, sx=1.04), key(6.5, "io", sy=1, sx=1)],
        "wobble": [{"p": "sy", "amp": 0.012, "f": 1.1, "t0": 3.6, "t1": 7.6}]}


def player_keys():
    px, py = PLAYER
    mx, my = MOUTH
    return [
        key(0, "hold", x=px, y=4.8, rot=0, s=1, sx=1, sy=1, flip=1), key(0.45, "hold", x=px, y=4.8),
        key(1.45, "in", x=px, y=py + 0.15, rot=-350),
        key(1.6, "out", y=py - 0.3, sx=1.14, sy=0.82, rot=-360), key(1.85, "out", y=py + 0.1, sx=0.95, sy=1.06), key(2.05, "io", y=py, sx=1, sy=1),
        key(2.5, "hold", flip=1), key(2.52, "hold", flip=-1), key(3.1, "hold", flip=-1), key(3.12, "hold", flip=1),
        key(3.4, "hold", x=px, y=py, rot=0),
        key(3.55, "out", y=py + 0.25, sx=0.9, sy=1.12), key(3.7, "in", y=py, sx=1.05, sy=0.95), key(3.85, "out", sx=1, sy=1),
        key(4.15, "hold", x=px, y=py),
        key(4.55, "io", x=mx, y=my + 0.1, s=0.88, rot=-15), key(4.75, "in", x=mx, y=my - 0.05, s=0.8)]


SCENES.append({
    "id": "bowl", "map": "candy", "title": "Die Suessigkeitenschuessel", "length": 7.6, "text": [1.3, 2.6],
    "bounds": [12, 8.4],
    "camera": [key(0, "lin", z=1.02, x=0.2, y=0.0), key(1.4, z=1.06, x=0.3, y=0.05), key(2.7, z=1.06, x=0.3, y=0.05),
               key(3.4, "out", z=1.0, x=0.3, y=0.85), key(4.6, z=1.06, x=0.5, y=0.9), key(5.8, z=1.02, x=0.3, y=0.85), key(7.6, "lin", z=1.0, x=0.3, y=0.7)],
    "objects": [
        {"id": "bg", "sprite": "cb_eject_pantry_bg.jpg", "z": -100},
        {"id": "moonglow", "sprite": GLOW, "z": -96, "x": 3.0, "y": 2.0, "s": 1.6, "tint": "#c8c0f0", "a": 0.25, "flicker": {"amp": 0.15, "f": 0.3}},
        {"id": "lantern", "sprite": GLOW, "z": -95, "x": -4.3, "y": -0.7, "sx": 1.8, "sy": 1.4, "tint": "#ffb060", "a": 0.35, "flicker": {"amp": 0.4, "f": 7}},
        monster(), jaw(), pupil(-1), pupil(1), lid(-1), lid(1),
        {"id": "table", "sprite": "cb_eject_table_front.png", "z": -25, "x": 0.0, "y": FLOOR, "pivot": [0.5, 1]},
        {"id": "bowlBack", "sprite": "cb_eject_bowl_back.png", "z": -20, "x": BOWL_X, "y": FLOOR, "pivot": [0.5, 0]},
        {"id": "heap", "sprite": "cb_eject_heap.png", "z": -15, "x": BOWL_X, "y": -0.1, "pivot": [0.5, 0],
         "wobble": [{"p": "sx", "amp": 0.03, "f": 9, "t0": 1.45, "t1": 1.95}, {"p": "sy", "amp": 0.05, "f": 9, "t0": 1.45, "t1": 1.95}]},
        {"id": "pshadow", "sprite": GLOW, "parent": "player", "z": -1, "y": -0.45, "sx": 1.0, "sy": 0.2, "tint": "#000000", "a": 0.35},
        {"id": "bowlFront", "sprite": "cb_eject_bowl_front.png", "z": 10, "x": BOWL_X, "y": FLOOR, "pivot": [0.5, 0],
         "wobble": [{"p": "rot", "amp": 1.2, "f": 9, "t0": 1.45, "t1": 1.9}]},
        {"id": "faceGlow", "sprite": GLOW, "z": 11, "x": BOWL_X, "y": FLOOR + 0.55, "sx": 1.4, "sy": 0.6, "tint": "#ffb060", "a": 0.25, "flicker": {"amp": 0.5, "f": 6}},
        paw_left(), paw_right(),
        {"id": "wrapper", "sprite": WRAPPER, "z": 14, "s": 0.55, "keys": [
            key(0, "hold", x=MOUTH[0], y=MOUTH[1], a=0, rot=0), key(6.2, "hold", x=MOUTH[0], y=MOUTH[1], a=0, rot=0), key(6.22, "hold", a=1),
            key(6.55, "out", x=1.6, y=2.2, rot=50), key(7.5, "lin", x=2.6, y=-1.07, rot=400), key(7.6, "hold", y=-1.07)],
         "wobble": [{"p": "x", "amp": 0.3, "f": 1.3, "t0": 6.6, "t1": 7.45}, {"p": "rot", "amp": 22, "f": 1.6, "t0": 6.6, "t1": 7.45}]},
    ],
    "player": {"hide": 4.78, "keys": player_keys(),
               "wobble": [{"p": "y", "amp": 0.03, "f": 2.4, "t0": 2.1, "t1": 3.4}, {"p": "rot", "amp": 6, "f": 9, "t0": 4.15, "t1": 4.75}]},
    "emitters": [
        em(MOTE, -50, t0=0, t1=7.6, rate=4, area=[-5, -1.2, 5, 1.8], vel=[-0.06, -0.03, 0.06, 0.06], life=[3, 5], size=[0.03, 0.06], tint="#d8c0ff", a=0.4),
        # Landung: Suessigkeiten spritzen (hinter dem Rand und ein paar davor)
        burst(TWIST, 3, 1.45, 5, area=[0.5, 0.6, 1.3, 0.9], vel=[-3, 2.5, 3, 5.5], acc=[0, -10], life=[0.5, 0.9], size=[0.3, 0.42], spin=[-400, 400], rot=[0, 360], fade=[0.0, 0.3]),
        burst(TWIST2, 3, 1.45, 4, area=[0.5, 0.6, 1.3, 0.9], vel=[-3, 2.5, 3, 5.5], acc=[0, -10], life=[0.5, 0.9], size=[0.3, 0.42], spin=[-400, 400], rot=[0, 360], fade=[0.0, 0.3]),
        burst(EYE, 3, 1.45, 3, area=[0.5, 0.6, 1.3, 0.9], vel=[-2.5, 2.5, 2.5, 5], acc=[0, -10], life=[0.5, 0.9], size=[0.24, 0.32], spin=[-300, 300], fade=[0.0, 0.3]),
        burst(PUMP, 3, 1.45, 3, area=[0.5, 0.6, 1.3, 0.9], vel=[-2.5, 2.5, 2.5, 5], acc=[0, -10], life=[0.5, 0.9], size=[0.26, 0.34], spin=[-300, 300], fade=[0.0, 0.3]),
        burst(CORN, 3, 1.45, 4, area=[0.5, 0.6, 1.3, 0.9], vel=[-3, 2.5, 3, 5.5], acc=[0, -10], life=[0.5, 0.9], size=[0.22, 0.3], spin=[-500, 500], rot=[0, 360], fade=[0.0, 0.3]),
    ] + [burst(BEAN, 3, 1.45, 1, area=[0.5, 0.6, 1.3, 0.9], vel=[-3, 2.5, 3, 5.5], acc=[0, -10], life=[0.5, 0.9], size=[0.3, 0.38], spin=[-400, 400], rot=[0, 360], fade=[0.0, 0.3], tint=t) for t in BEAN_TINTS] + [
        burst(TWIST, 12, 1.47, 2, area=[0.1, 0.7, 1.5, 0.9], vel=[-4, 2, 4, 4.5], acc=[0, -10], life=[0.55, 0.75], size=[0.34, 0.42], spin=[-400, 400], rot=[0, 360], fade=[0.0, 0.3]),
        burst(LOLLY, 12, 1.47, 1, area=[0.7, 0.8, 1.1, 0.9], vel=[1.5, 3, 3, 4.5], acc=[0, -10], life=[0.6, 0.7], size=[0.5, 0.55], spin=[-300, -200], fade=[0.0, 0.3]),
        burst(BEAN, 12, 1.47, 2, area=[0.1, 0.7, 1.5, 0.9], vel=[-4, 2, 4, 4.5], acc=[0, -10], life=[0.55, 0.75], size=[0.34, 0.4], spin=[-400, 400], fade=[0.0, 0.3], tint="#2aa050"),
        # Erschrecken: Krone der Schuessel staubt
        burst(PUFF, 2, 3.32, 4, area=[-1.6, 0.6, 2.2, 0.9], vel=[-0.5, 0.3, 0.5, 0.9], drag=1.5, life=[0.6, 1.0], size=[0.3, 0.5], grow=0.6, tint="#c8a8ff", a=0.3),
        # Kruemel beim Kauen
        burst(CRUMB, 14, 4.84, 8, area=[0.6, 1.2, 1.4, 1.5], vel=[-2.2, 0.5, 2.2, 3.2], acc=[0, -9], life=[0.5, 0.8], size=[0.08, 0.16], spin=[-600, 600], rot=[0, 360], fade=[0.0, 0.3], tint="#f0e0c0"),
        burst(CRUMB, 14, 5.1, 7, area=[0.6, 1.2, 1.4, 1.5], vel=[-2.2, 0.5, 2.2, 3.2], acc=[0, -9], life=[0.5, 0.8], size=[0.08, 0.16], spin=[-600, 600], rot=[0, 360], fade=[0.0, 0.3], tint="#f0e0c0"),
        burst(CRUMB, 14, 5.36, 7, area=[0.6, 1.2, 1.4, 1.5], vel=[-2.2, 0.5, 2.2, 3.2], acc=[0, -9], life=[0.5, 0.8], size=[0.08, 0.16], spin=[-600, 600], rot=[0, 360], fade=[0.0, 0.3], tint="#f0e0c0"),
        burst(CORN, 14, 4.84, 2, area=[0.7, 1.2, 1.3, 1.4], vel=[-2, 1, 2, 3], acc=[0, -9], life=[0.5, 0.7], size=[0.16, 0.22], spin=[-500, 500], fade=[0.0, 0.3]),
        burst(EYE, 14, 5.1, 1, area=[0.7, 1.2, 1.3, 1.4], vel=[-2, 1, 2, 3], acc=[0, -9], life=[0.5, 0.7], size=[0.18, 0.22], spin=[-500, 500], fade=[0.0, 0.3]),
        # Ruelpser: gruene Wolke
        burst(PUFF, 13, 6.22, 7, area=[0.0, 1.3, 0.8, 1.6], vel=[-0.7, 0.8, 0.7, 1.7], drag=1.0, life=[1.0, 1.6], size=[0.4, 0.8], grow=0.5, tint="#b8e8a0", a=0.45),
        em(MOTE, 13, t0=6.25, t1=6.8, rate=14, area=[0.0, 1.3, 0.8, 1.7], vel=[-0.4, 0.6, 0.4, 1.4], life=[0.6, 1.1], size=[0.04, 0.08], tint="#c8ffb0", a=0.6),
    ],
    "events": [
        ev(0.5, sound="whoosh", vol=0.5), ev(1.45, sound="rustle", vol=0.8), ev(1.45, sound="thud", vol=0.35, shake=[0.3, 0.06]), ev(1.78, sound="pop", vol=0.4),
        ev(2.6, sound="growl", vol=0.7), ev(2.7, sound="rush", vol=0.35), ev(3.3, sound="thud", vol=0.6, shake=[0.4, 0.12]), ev(3.45, sound="roar", vol=0.5),
        ev(3.55, sound="pop", vol=0.5), ev(3.95, sound="whoosh", vol=0.5), ev(4.15, sound="rustle", vol=0.5), ev(4.4, sound="growl", vol=0.4),
        ev(4.8, sound="munch", vol=0.9, shake=[0.2, 0.05]), ev(5.06, sound="munch", vol=0.8), ev(5.32, sound="munch", vol=0.85),
        ev(5.8, sound="gulp", vol=0.9), ev(6.2, sound="burp", vol=1.0, shake=[0.5, 0.08]), ev(7.5, sound="click", vol=0.3),
    ],
})


# ============================================================================ Pruefung, Daempfung, Ausgabe

def lint():
    errors = 0

    def err(msg):
        nonlocal errors
        errors += 1
        print("FEHLER:", msg)

    ids = set()
    for sc in SCENES:
        if sc["id"] in ids:
            err(f"Szene {sc['id']} doppelt")
        ids.add(sc["id"])
        pl = sc.get("player", {})
        for o in sc["objects"] + [dict(pl, id="player")] + [{"id": "camera", "keys": sc["camera"]}]:
            for t, props, ease in o.get("keys", []):
                if ease not in EASES:
                    err(f"{sc['id']}/{o['id']}: ease {ease}")
                if t < 0 or t > sc["length"] + 0.01:
                    err(f"{sc['id']}/{o['id']}: Key bei {t}s ausserhalb der Szene")
                for pr in props:
                    if pr not in PROPS and not (o["id"] == "camera" and pr == "z"):
                        err(f"{sc['id']}/{o['id']}: Eigenschaft {pr}")
            if o.get("sprite") and not o["sprite"].startswith(SPRITE_PREFIX):
                err(f"{sc['id']}/{o['id']}: Sprite {o['sprite']}")
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
        if not ((res / "candy_eject" / name).exists() or (res / "villa" / name).exists()):
            err(f"Sprite-Datei fehlt: {name}")
    for snd in ("rustle", "munch", "gulp", "burp"):
        if not (res / "candy_eject" / f"sfx_{snd}.wav").exists():
            err(f"Klangdatei fehlt: sfx_{snd}.wav (python tools/gen_candy_sfx.py)")
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


# Daempfung aller Effekte (gleiche Werte wie Villa und Friedhof)
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
