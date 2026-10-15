# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_doors.py - eigene Tueren und Drehkameras von Hollowmere Manor (seit 15.10., Audit).
#
# SCHNITTSTELLE (gen_villa.render_consoles):
#   door_frames(kind, axis, ppm) -> [(PIL RGBA, anker_x_px, anker_y_px)] mit 6 Bildern, [0] = zu, [5] = offen.
#       kind: "wood" (Zimmertuer, Nussholz mit Messing), "heavy" (Haus-/Hintertuer, Eisenbaender) oder
#             "iron" (schmiedeeisernes Gartentor); axis: "y" = Tuer in einer waagerechten Wand (von vorn
#             zu sehen), "x" = Tuer in einer senkrechten Wand (von oben, Skeld-Konvention: flaches Paneel).
#       Alle Bilder eines Satzes sind gleich gross und haben denselben Anker = Mitte der Oeffnung auf der
#       Wandachse; Atlas spielt sie beim Oeffnen und Schliessen in 50-ms-Schritten ab.
#   camera(ppm, on) -> (PIL RGBA, ax, ay): Drehkamera der Crew auf Stativ, on = rotes Tally-Licht leuchtet.
#
# GESTALTUNG
#   Waagerechte Wand: zwei Fluegel von vorn, jeder halb so breit wie die Oeffnung (2,5 m), 2,1 m hoch
#   (K-verkuerzt). Beim Oeffnen schwingen sie um die Angel an die Wand: die sichtbare Breite folgt cos,
#   ab 90 Grad erscheint die Rueckseite neben der Oeffnung. Ueber der Oeffnung ein Sturz mit Architrav.
#   Senkrechte Wand: Fluegel als flache Paneele (0,42 m breit, so dick wie die Wand), die sich in der
#   Bodenebene um die Angel drehen und offen laengs der Wand liegen. Zargenpfosten an beiden Enden.

import math

import os
import sys

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)

from museum_art import Canvas, K, OUTLINE, OUT_W, alpha, hexc, lift, shade  # noqa: E402

OPENING = 2.5                 # Laenge aller Tueroeffnungen der Villa
LEAF = OPENING / 2
WALL_T = 0.42                 # Wanddicke im Bild (senkrechte Wand)
DOOR_H = 2.1 * K              # Fluegelhoehe im Bild (waagerechte Wand)
FACE_Y0 = -0.2                # Unterkante der Tuerfront: Suedseite der Wand (Wandachse = 0)
N_FRAMES = 6
MARGIN = 0.14

WALNUT = hexc("#6e4a30")
WALNUT_L = hexc("#8e6440")
WALNUT_D = hexc("#4a3020")
BRASS = lift("#9c7c3c", 1.25)
BRASS_D = hexc("#6a5226")
IRON = hexc("#3c3e46")
IRON_L = hexc("#6a6e78")
IRON_D = hexc("#22242a")
FRAME = hexc("#5a3a22")
STONE = hexc("#7c8088")
TALLY = hexc("#ff3a3a")
GEAR = hexc("#2c2e34")
GEAR_L = hexc("#4a4e58")


def _result(c, ppm):
    img = c.finish()
    return img, int(round((0 - c.x0) * ppm)), int(round((0 - c.y0) * ppm))


# ------------------------------------------------------------------ Fluegel-Zeichnung (lokal)

def _wood_face(c, Pm, w, h, kind, hinge_left, mirror):
    """Tuerfront als Bild: Pm(u, v) bildet (0..1 Breite, 0..1 Hoehe) in die Leinwand ab.
    hinge_left: Angel links (Griff rechts). mirror: Rueckseite (Griff auf der anderen Seite)."""
    body = WALNUT if kind == "wood" else WALNUT_D
    q = lambda a, b, cc, d: [Pm(a, b), Pm(cc, b), Pm(cc, d), Pm(a, d)]
    c.poly(q(0, 0, 1, 1), fill=body, outline=OUTLINE, width=OUT_W * 0.7)
    # Lichtkante links, Schattenkante rechts
    c.line([Pm(0.03, 0.02), Pm(0.03, 0.98)], fill=shade(body, 1.25), width=0.02 * w)
    c.line([Pm(0.97, 0.02), Pm(0.97, 0.98)], fill=shade(body, 0.7), width=0.02 * w)
    # zwei Fuellungen
    for v0, v1 in ((0.08, 0.44), (0.54, 0.9)):
        c.poly(q(0.14, v0, 0.86, v1), fill=shade(body, 0.85), outline=shade(body, 0.55), width=0.015)
        c.line([Pm(0.14, v1), Pm(0.86, v1)], fill=shade(body, 1.3), width=0.012)
        c.line([Pm(0.14, v0), Pm(0.14, v1)], fill=shade(body, 1.2), width=0.012)
    if kind == "heavy":
        # Eisenbaender mit Nieten
        for v in (0.22, 0.72):
            c.poly(q(0.0, v - 0.035, 1.0, v + 0.035), fill=IRON, outline=OUTLINE, width=0.015)
            for u in (0.15, 0.4, 0.65, 0.9):
                c.ellipse(*Pm(u, v), 0.012, 0.012, fill=IRON_L, outline=IRON_D, width=0.006)
    # Griff an der freien Kante
    gu = 0.86 if (hinge_left != mirror) else 0.14
    c.ellipse(*Pm(gu, 0.5), 0.035, 0.035, fill=BRASS, outline=BRASS_D, width=0.012)
    c.ellipse(*Pm(gu, 0.5), 0.012, 0.012, fill=BRASS_D)


def _iron_face(c, Pm, w, h):
    """Gittertor: Rahmen, Staebe, Spitzen. Dazwischen durchsichtig."""
    q = lambda a, b, cc, d: [Pm(a, b), Pm(cc, b), Pm(cc, d), Pm(a, d)]
    for v in (0.06, 0.52, 0.9):
        c.poly(q(0.0, v - 0.025, 1.0, v + 0.025), fill=IRON, outline=OUTLINE, width=0.012)
    n = 6
    for i in range(n + 1):
        u = i / n
        c.poly(q(u - 0.02, 0.0, u + 0.02, 0.97), fill=IRON, outline=OUTLINE, width=0.012)
        # Spitze
        c.poly([Pm(u - 0.035, 0.95), Pm(u + 0.035, 0.95), Pm(u, 1.0)], fill=IRON_L, outline=OUTLINE, width=0.01)
        c.line([Pm(u - 0.01, 0.05), Pm(u - 0.01, 0.9)], fill=IRON_L, width=0.006)
    # Schnoerkel in der Mitte
    cx, cy = Pm(0.5, 0.3)
    c.ellipse(cx, cy, 0.09 * w, 0.06 * h, outline=IRON, width=0.02)
    c.ellipse(cx, cy, 0.05 * w, 0.03 * h, outline=IRON_L, width=0.012)


# ------------------------------------------------------------------ waagerechte Wand: von vorn

def _frames_y(kind, ppm):
    out = []
    x0, x1 = -2 * LEAF - MARGIN, 2 * LEAF + MARGIN
    y0, y1 = FACE_Y0 - MARGIN - 0.1, FACE_Y0 + DOOR_H + 0.32 + MARGIN
    for k in range(N_FRAMES):
        th = math.radians(k / (N_FRAMES - 1) * 160.0)         # bis 160 Grad: fast an der Wand
        c = Canvas(x0, y0, x1, y1, ppm)
        # Boden-Schatten der Fluegel und Schwelle
        c.soft_shadow([(-LEAF - 0.05, FACE_Y0 - 0.12), (LEAF + 0.1, FACE_Y0 - 0.12), (LEAF + 0.1, FACE_Y0 + 0.02), (-LEAF - 0.05, FACE_Y0 + 0.02)], 70, 0.05)
        if kind == "iron":
            c.rect(-LEAF - 0.1, FACE_Y0 - 0.06, LEAF + 0.1, FACE_Y0 + 0.03, fill=STONE, outline=OUTLINE, width=0.03)
        else:
            c.rect(-LEAF - 0.08, FACE_Y0 - 0.06, LEAF + 0.08, FACE_Y0 + 0.02, fill=shade(FRAME, 0.8), outline=OUTLINE, width=0.03)
        # Fluegel: links Angel bei -LEAF, rechts bei +LEAF; sichtbare Breite = LEAF * cos(th), ab 90 Grad spiegelverkehrt
        vis = LEAF * abs(math.cos(th))
        back = th > math.pi / 2
        for side in (-1, 1):
            hinge = side * LEAF                          # -1: linker Fluegel, Angel links; +1: rechter, Angel rechts
            if vis < 0.03:
                c.rect(hinge - 0.03, FACE_Y0, hinge + 0.03, FACE_Y0 + DOOR_H, fill=WALNUT_D if kind != "iron" else IRON_D, outline=OUTLINE, width=0.02)
                continue
            direction = -side if not back else side     # zur Mitte hin (zu) oder nach aussen (offen)
            ax0 = hinge
            ax1 = hinge + direction * vis
            lo, hi = min(ax0, ax1), max(ax0, ax1)
            hinge_left = (hinge == lo)
            Pm = lambda u, v, lo=lo, hi=hi, hl=hinge_left: ((lo + u * (hi - lo)) if hl else (hi - u * (hi - lo)), FACE_Y0 + v * DOOR_H)
            if kind == "iron":
                _iron_face(c, Pm, hi - lo, DOOR_H)
            else:
                _wood_face(c, Pm, hi - lo, DOOR_H, kind, hinge_left, back)
            # Angelband
            c.rect(hinge - 0.03, FACE_Y0 + 0.02, hinge + 0.03, FACE_Y0 + DOOR_H - 0.02, fill=IRON if kind != "wood" else BRASS_D, outline=OUTLINE, width=0.015)
        # Zarge: Pfosten und Sturz ueber der Oeffnung
        fr = FRAME if kind != "iron" else STONE
        for px in (-LEAF, LEAF):
            c.rect(px - 0.09, FACE_Y0 - 0.02, px + 0.09, FACE_Y0 + DOOR_H + 0.08, fill=fr, outline=OUTLINE, width=0.03)
            c.line([(px - 0.06, FACE_Y0), (px - 0.06, FACE_Y0 + DOOR_H + 0.05)], fill=shade(fr, 1.3), width=0.015)
        c.rect(-LEAF - 0.14, FACE_Y0 + DOOR_H + 0.02, LEAF + 0.14, FACE_Y0 + DOOR_H + 0.3, fill=fr, outline=OUTLINE, width=0.03)
        c.line([(-LEAF - 0.1, FACE_Y0 + DOOR_H + 0.26), (LEAF + 0.1, FACE_Y0 + DOOR_H + 0.26)], fill=shade(fr, 1.35), width=0.02)
        if kind == "iron":
            for px in (-LEAF, LEAF):                      # Torpfeiler mit Kugel
                c.ellipse(px, FACE_Y0 + DOOR_H + 0.4, 0.11, 0.09, fill=shade(STONE, 1.1), outline=OUTLINE, width=0.025)
        elif kind == "heavy":
            c.text(0, FACE_Y0 + DOOR_H + 0.16, "HOLLOWMERE", 0.12, shade(fr, 1.6))
        out.append(_result(c, ppm))
    return out


# ------------------------------------------------------------------ senkrechte Wand: flache Paneele von oben

def _frames_x(kind, ppm):
    out = []
    x0, x1 = -WALL_T / 2 - MARGIN - 0.1, LEAF + WALL_T + MARGIN
    y0, y1 = -2 * LEAF - MARGIN - 0.1, 2 * LEAF + MARGIN + 0.1
    for k in range(N_FRAMES):
        th = math.radians(k / (N_FRAMES - 1) * 160.0)
        c = Canvas(x0, y0, x1, y1, ppm)
        # Schwelle in der Oeffnung
        c.rect(-WALL_T / 2 + 0.02, -LEAF, WALL_T / 2 - 0.02, LEAF, fill=shade(FRAME if kind != "iron" else STONE, 0.75))
        for side in (-1, 1):
            hinge = (0.0, side * LEAF)
            # Richtung des Fluegels: zu = zur Mitte (0, -side), offen = nach Osten gedreht, dann laengs der Wand nach aussen
            dx, dy = math.sin(th), -side * math.cos(th)
            ux, uy = -dy, dx                              # Querachse (Paneelbreite)
            pts = [(hinge[0] + a * dx + b * ux, hinge[1] + a * dy + b * uy)
                   for a, b in ((0, -WALL_T / 2), (LEAF, -WALL_T / 2), (LEAF, WALL_T / 2), (0, WALL_T / 2))]
            c.soft_shadow([(x + 0.05, y - 0.06) for x, y in pts], 60, 0.04)
            # Bildabbildung: u laengs des Fluegels (0 = Angel), v quer (0..1 = Breite); die Front liegt "von oben"
            Pm = lambda u, v, hx=hinge[0], hy=hinge[1], dx=dx, dy=dy, ux=ux, uy=uy: (hx + u * LEAF * dx + (v - 0.5) * WALL_T * ux, hy + u * LEAF * dy + (v - 0.5) * WALL_T * uy)
            # die Flaechenfunktionen erwarten u = Breite, v = Hoehe: hier Breite = Fluegellaenge, Hoehe = Wanddicke
            if kind == "iron":
                _iron_face(c, Pm, LEAF, WALL_T)
            else:
                _wood_face(c, Pm, LEAF, WALL_T, kind, True, False)
            # Angel
            c.ellipse(hinge[0], hinge[1], 0.05, 0.05, fill=IRON if kind != "wood" else BRASS, outline=OUTLINE, width=0.015)
        # Zargenpfosten an den Enden der Oeffnung (klein, mit Hoehe)
        fr = FRAME if kind != "iron" else STONE
        for py in (-LEAF, LEAF):
            c.rect(-WALL_T / 2 - 0.06, py - 0.1, WALL_T / 2 + 0.06, py + 0.1, fill=fr, outline=OUTLINE, width=0.03)
            c.rect(-WALL_T / 2 - 0.06, py + 0.1, WALL_T / 2 + 0.06, py + 0.1 + 0.9 * K * 0.35, fill=shade(fr, 1.15), outline=OUTLINE, width=0.025)
            if kind == "iron":
                c.ellipse(0, py + 0.1 + 0.9 * K * 0.35, 0.1, 0.08, fill=shade(STONE, 1.1), outline=OUTLINE, width=0.025)
        out.append(_result(c, ppm))
    return out


def door_frames(kind, axis, ppm):
    return _frames_y(kind, ppm) if axis == "y" else _frames_x(kind, ppm)


# ------------------------------------------------------------------ Drehkamera

def camera(ppm, on):
    """Drehkamera der Crew auf Stativ, Blick nach Suedwesten; on = Tally-Licht an. Anker = Stativmitte am Boden."""
    c = Canvas(-0.55, -0.4, 0.55, 1.25, ppm)
    c.soft_shadow([(-0.3, -0.22), (0.38, -0.22), (0.38, 0.02), (-0.3, 0.02)], 80, 0.06)
    # Stativbeine
    for lx, ly in ((-0.3, -0.18), (0.32, -0.16), (0.04, -0.3)):
        c.line([(lx, ly), (0.0, 0.62)], fill=GEAR_L, width=0.05)
        c.line([(lx, ly), (0.0, 0.62)], fill=GEAR, width=0.03)
        c.ellipse(lx, ly, 0.04, 0.025, fill=IRON_D)
    c.rect(-0.05, 0.6, 0.05, 0.74, fill=GEAR, outline=OUTLINE, width=0.02)
    # Kamerakoerper mit Objektiv nach links unten
    c.poly([(-0.2, 0.74), (0.26, 0.74), (0.28, 0.98), (-0.18, 1.0)], fill=GEAR_L, outline=OUTLINE, width=0.025)
    c.rect(-0.16, 0.78, 0.22, 0.94, fill=GEAR)
    c.line([(-0.14, 0.9), (0.18, 0.9)], fill=hexc("#6f7480"), width=0.012)
    c.poly([(-0.38, 0.76), (-0.2, 0.8), (-0.2, 0.92), (-0.4, 0.9)], fill=GEAR, outline=OUTLINE, width=0.025)   # Objektiv
    c.ellipse(-0.4, 0.83, 0.05, 0.07, fill=hexc("#1a1c22"), outline=OUTLINE, width=0.02)
    c.ellipse(-0.41, 0.84, 0.02, 0.03, fill=alpha(hexc("#8fb4d8"), 170))
    # Filmrollen oben
    for rx in (-0.06, 0.16):
        c.ellipse(rx, 1.08, 0.11, 0.1, fill=GEAR_L, outline=OUTLINE, width=0.025)
        c.ellipse(rx, 1.08, 0.04, 0.035, fill=GEAR)
    # Sucher und Tally-Licht
    c.rect(0.2, 0.9, 0.3, 0.98, fill=GEAR, outline=OUTLINE, width=0.02)
    if on:
        c.glow(0.12, 1.0, 0.22, TALLY, 0.55)
    c.ellipse(0.12, 1.0, 0.035, 0.035, fill=TALLY if on else hexc("#5a1a1a"), outline=OUTLINE, width=0.015)
    if on:
        c.ellipse(0.11, 1.01, 0.012, 0.012, fill=hexc("#ffd0d0"))
    # Kabel am Boden
    c.line([(0.1, -0.2), (0.3, -0.3), (0.5, -0.26)], fill=GEAR, width=0.03)
    return _result(c, ppm)


if __name__ == "__main__":
    for kind in ("wood", "heavy", "iron"):
        for axis in ("y", "x"):
            fr = door_frames(kind, axis, 128)
            print(kind, axis, fr[0][0].size, fr[0][1:], len({f[0].size for f in fr}) == 1)
    print("camera", camera(128, True)[0].size)
