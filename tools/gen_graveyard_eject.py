# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_graveyard_eject.py - Grafik der Rauswurf-Szenen auf Ravenhollow Cemetery -> Resources/graveyard_eject/gy_eject_*
#
# Konventionen wie gen_villa_eject.py (dessen Zeichenhelfer hier mitbenutzt werden): gezeichnet in 100 px pro
# Szenen-Einheit mit Supersampling, exportiert mit K = 1,8 (180 px pro Einheit), Hintergruende 12 x 6,8 Einheiten
# als JPG, alles andere PNG mit Alpha. Generische Partikel (Glow, Mote, Puff, Mist, Flamme, Tropfen ...) kommen aus
# dem Villa-Satz (villa_eject_*.png), die Engine laedt beide als UnknownsHalloween.Resources.<datei>.
#
# Stil: Mondnacht des Friedhofs (graveyard_art.py), kaltes Blaugruen, Granit, Bronze, Moos; warme Inseln nur an
# Laternen, Kerzen und Ofenglut. Umrisse zittern leicht (handdraw.wobble/ink).
#
#     python tools/gen_graveyard_eject.py

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_villa_eject as V                         # noqa: E402  (Zeichenhelfer, Export)
from gen_villa_eject import (C, S, K, BW, BH, INK, a4, ux, uy, hpoly, hrect, hell, hrr, hline, apoly, aline, grad_rect,
                             blur, cold_moon, cobweb_px, ell_pts, rr_pts, wob, leaf, grad, rect, light)   # noqa: E402
import handdraw as HD                               # noqa: E402

OUT = HERE.parent / "Resources" / "graveyard_eject"
V.OUT = OUT

SKY_T, SKY_B = (12, 16, 28, 255), (38, 52, 62, 255)
HILL, HILL_D = (20, 28, 32, 255), (14, 20, 24, 255)
GRASS, GRASS_L, GRASS_D = (40, 58, 48, 255), (64, 90, 70, 255), (24, 36, 30, 255)
EARTH, EARTH_L, EARTH_D = (70, 56, 44, 255), (96, 78, 60, 255), (40, 32, 26, 255)
STONE, STONE_L, STONE_D = (104, 108, 118, 255), (140, 146, 158, 255), (66, 70, 80, 255)
MARBLE, MARBLE_D = (184, 186, 180, 255), (138, 142, 138, 255)
BRONZE, BRONZE_L, BRONZE_D = (150, 108, 58, 255), (210, 170, 104, 255), (96, 66, 36, 255)
IRON, IRON_L, IRON_D = (52, 54, 62, 255), (92, 96, 108, 255), (30, 32, 38, 255)
WOOD, WOOD_L, WOOD_D = (98, 78, 58, 255), (128, 104, 80, 255), (62, 48, 36, 255)
BRICK, BRICK_D = (122, 66, 52, 255), (84, 44, 36, 255)
BONE, BONE_D = (222, 214, 192, 255), (168, 158, 134, 255)
MOSS = (72, 104, 66, 255)
WARM = (255, 200, 120, 255)
EMBER = (255, 120, 40, 255)
CROW, CROW_L = (20, 20, 28, 255), (64, 74, 104, 255)
FLOOR_PX = int(uy(-1.25))                               # Bodenlinie der Szenen (Figur steht mit der Mitte bei -0,75)

# Sitzplaetze der Raben im Skip-Bild (Szenen-Einheiten); graveyard_eject.py setzt die Raben genau dorthin
PERCH = [(-2.15, 1.35), (-1.35, 1.72), (-0.55, 2.02), (0.85, 1.88), (1.7, 1.55), (2.55, 0.95), (-2.9, 0.5), (0.2, 1.3)]


# ------------------------------------------------------------------ gemeinsame Teile

def arect(c, x0, y0, x1, y1, fill):
    apoly(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill)


def stars(c, n, y1, seed=4):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y, r = rnd.uniform(0, c.w), rnd.uniform(0, y1), rnd.choice((0.8, 1, 1, 1.4))
        a = rnd.randint(80, 200) / 255
        bg = c.img.getpixel((min(c.img.width - 1, int(x * S)), min(c.img.height - 1, int(y * S))))
        col = tuple(int(bg[i] + (v - bg[i]) * a) for i, v in enumerate((230, 236, 255))) + (255,)
        c.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=col)


def ground(c, y0, seed=5, top=GRASS, bottom=GRASS_D):
    grad(c, top, bottom, y0, c.h)
    rnd = random.Random(seed)
    for _ in range(int(c.w * 0.3)):
        x, y = rnd.uniform(0, c.w), rnd.uniform(y0 + 4, c.h)
        for (a, b) in HD.tuft(x, y, rnd, n=3, h=8 + (y - y0) * 0.04, spread=4):
            c.line([a, b], GRASS_L if rnd.random() < 0.35 else a4(GRASS_D, 255), 1.4)
    for _ in range(int(c.w * 0.08)):
        x, y = rnd.uniform(0, c.w), rnd.uniform(y0 + 10, c.h)
        leaf(c, x, y, rnd.uniform(8, 14), rnd.uniform(3, 6), rnd.uniform(0, 360), rnd.choice(((120, 70, 40, 255), (96, 60, 34, 255), (130, 96, 46, 255))))


def headstone_px(c, x, base, w, h, col=STONE, seed=0, form=0, rim=True):
    """Grabstein in Vorderansicht (Fuss bei base): 0 Rundbogen, 1 Kreuz, 2 Spitzbogen, 3 Obelisk."""
    if form == 1:
        hrect(c, x - w * 0.14, base - h, x + w * 0.14, base, col, lw=3, seed=seed, sh=(0.1, 0.25))
        hrect(c, x - w * 0.5, base - h * 0.78, x + w * 0.5, base - h * 0.6, col, lw=3, seed=seed + 1, sh=(0.1, 0.25))
    elif form == 3:
        hpoly(c, [(x - w * 0.5, base), (x + w * 0.5, base), (x + w * 0.3, base - h * 0.85), (x, base - h), (x - w * 0.3, base - h * 0.85)], col, lw=3, seed=seed,
              sh=(0.1, 0.25))
    else:
        r = (w / 2, 3) if form == 0 else (w * 0.5, 2)
        pts = rr_pts(x - w / 2, base - h, x + w / 2, base, r)
        if form == 2:
            pts = [(x - w / 2, base), (x + w / 2, base), (x + w / 2, base - h * 0.62), (x, base - h), (x - w / 2, base - h * 0.62)]
        hpoly(c, pts, col, lw=3, seed=seed, sh=(0.12, 0.28))
        hline(c, [(x, base - h * 0.78), (x, base - h * 0.5)], a4(light(col, -0.3) if False else (60, 62, 70, 255), 255), 2, seed=seed)
        hline(c, [(x - w * 0.14, base - h * 0.68), (x + w * 0.14, base - h * 0.68)], (60, 62, 70, 255), 2, seed=seed + 1)
    if rim:
        aline(c, [(x - w / 2 + 2, base - 4), (x - w / 2 + 2, base - h * 0.6)], (190, 210, 236, 110), 2)


def yew_px(c, x, base, h, col=(18, 30, 26, 255), rim=(38, 58, 52, 120), seed=0):
    rnd = random.Random(seed)
    blobs = []
    for k in range(int(h / 9)):
        t = k / max(1, int(h / 9) - 1)
        w = (0.34 * math.sin(math.pi * (0.25 + 0.75 * t)) ** 0.7 * (1 - t * 0.5) + 0.04) * h
        blobs.append((x + rnd.uniform(-1, 1) * w * 0.6, base - 10 - t * (h - 20), rnd.uniform(0.16, 0.24) * h * (1 - t * 0.4)))
    for bx, by, r in blobs:
        c.ell(bx, by, r, r * 0.85, col, lw=0)
    for bx, by, r in blobs[::3]:
        c.ell(bx - r * 0.3, by - r * 0.2, r * 0.45, r * 0.3, rim, lw=0)


def dead_tree_px(c, x, base, h, col=(16, 18, 22, 255), seed=0, w=None, perches=()):
    rnd = random.Random(seed)
    w = w or h * 0.05

    def br(px_, py_, a, ln, wd, depth):
        if depth == 0 or ln < 6:
            return
        ex, ey = px_ + math.cos(a) * ln, py_ - math.sin(a) * ln
        hline(c, [(px_, py_), (ex, ey)], col, max(1.2, wd), seed=int(ln * 7 + depth), amp=1.5)
        for s_ in (-1, 1):
            if rnd.random() < 0.85:
                br(ex, ey, a + s_ * rnd.uniform(0.25, 0.6), ln * rnd.uniform(0.6, 0.75), wd * 0.65, depth - 1)
    hpoly(c, [(x - w, base), (x + w, base), (x + w * 0.5, base - h * 0.5), (x - w * 0.5, base - h * 0.5)], col, lw=0, seed=seed)
    for a, f in ((math.pi / 2 + 0.5, 1), (math.pi / 2 - 0.55, 0.95), (math.pi / 2 + 0.05, 0.85), (math.pi / 2 + 1.1, 0.7), (math.pi / 2 - 1.15, 0.7)):
        br(x, base - h * 0.48, a, h * 0.26 * f, w * 1.1, 5)
    for px_, py_ in perches:                                                          # kurze Sitzaeste
        hline(c, [(px_ - 26, py_ + 6), (px_, py_ + 2), (px_ + 24, py_ - 4)], col, 5, seed=int(px_))
        hline(c, [(px_ + 24, py_ - 4), (px_ + 36, py_ - 14)], col, 3, seed=int(px_) + 1)


def fence_px(c, y_top, y_bot, col=(18, 22, 26, 255), step=22, seed=1):
    for x in range(-10, c.w + 20, step):
        hline(c, [(x, y_bot), (x, y_top)], col, 3, seed=x + seed, amp=0.6)
        c.d.polygon(c.P([(x - 4, y_top + 4), (x + 4, y_top + 4), (x, y_top - 8)]), fill=col)
    for yy in (y_top + 12, y_bot - 10):
        hline(c, [(-10, yy), (c.w + 10, yy)], col, 4, seed=yy, amp=0.8)


def tower_silhouette(c, x, base, s=1.0, col=HILL_D):
    w = 34 * s
    hrect(c, x - w / 2, base - 120 * s, x + w / 2, base, col, lw=0)
    hpoly(c, [(x - w / 2 - 6 * s, base - 120 * s), (x + w / 2 + 6 * s, base - 120 * s), (x, base - 170 * s)], col, lw=0)
    c.line([(x, base - 170 * s), (x, base - 186 * s)], col, 3 * s)
    c.line([(x - 6 * s, base - 180 * s), (x + 6 * s, base - 180 * s)], col, 3 * s)
    arect(c, x - 7 * s, base - 108 * s, x + 7 * s, base - 88 * s, (255, 210, 130, 160))


def chapel_silhouette(c, x, base, s=1.0, col=HILL_D):
    hrect(c, x - 60 * s, base - 70 * s, x + 60 * s, base, col, lw=0)
    hpoly(c, [(x - 70 * s, base - 70 * s), (x + 70 * s, base - 70 * s), (x, base - 120 * s)], col, lw=0)
    for k in range(3):
        wx = x - 34 * s + k * 34 * s
        apoly(c, [(wx - 6 * s, base - 20 * s), (wx + 6 * s, base - 20 * s), (wx + 6 * s, base - 46 * s), (wx, base - 54 * s), (wx - 6 * s, base - 46 * s)],
              (150, 120, 200, 110) if k == 1 else (255, 200, 120, 90))


def crow_px(c, x, y, s=1.0, flip=1, flying=False):
    f = flip
    if flying:
        hpoly(c, [(x, y), (x - 40 * s * f, y - 24 * s), (x - 62 * s * f, y - 18 * s), (x - 40 * s * f, y - 6 * s), (x - 16 * s * f, y + 4 * s),
                  (x + 16 * s * f, y + 4 * s), (x + 40 * s * f, y - 6 * s), (x + 62 * s * f, y - 18 * s), (x + 40 * s * f, y - 24 * s)], CROW, lw=2, seed=3)
        hell(c, x + 22 * s * f, y + 2 * s, 10 * s, 7 * s, CROW, lw=2, seed=4)
        hpoly(c, [(x + 30 * s * f, y), (x + 42 * s * f, y + 3 * s), (x + 30 * s * f, y + 5 * s)], (80, 80, 88, 255), lw=1, seed=5)
        hpoly(c, [(x - 20 * s * f, y + 2 * s), (x - 34 * s * f, y + 10 * s), (x - 20 * s * f, y + 8 * s)], CROW, lw=1, seed=6)
        aline(c, [(x - 30 * s * f, y - 14 * s), (x - 6 * s * f, y - 2 * s)], a4(CROW_L, 140), 2 * s)
        return
    hpoly(c, [(x - 10 * s * f, y + 8 * s), (x - 32 * s * f, y + 18 * s), (x - 26 * s * f, y + 10 * s), (x - 8 * s * f, y)], CROW, lw=2, seed=1)   # Schwanz
    hell(c, x, y, 16 * s, 12 * s, CROW, lw=2, seed=2)
    hell(c, x + 14 * s * f, y - 12 * s, 9 * s, 8 * s, CROW, lw=2, seed=3)
    hpoly(c, [(x + 21 * s * f, y - 14 * s), (x + 34 * s * f, y - 11 * s), (x + 21 * s * f, y - 9 * s)], (84, 84, 92, 255), lw=1, seed=4)
    c.ell(x + 16 * s * f, y - 14 * s, 1.8 * s, 1.8 * s, (232, 200, 90, 255), lw=0)
    aline(c, [(x - 8 * s * f, y - 4 * s), (x + 8 * s * f, y - 7 * s)], a4(CROW_L, 150), 2 * s)
    c.line([(x - 2 * s * f, y + 12 * s), (x - 3 * s * f, y + 18 * s)], (50, 50, 56, 255), 1.6 * s)
    c.line([(x + 4 * s * f, y + 12 * s), (x + 4 * s * f, y + 18 * s)], (50, 50, 56, 255), 1.6 * s)


# ================================================================== Szene 1: Das offene Grab

def grave():
    c = C(BW, BH)
    grad(c, SKY_T, SKY_B, 0, 320)
    stars(c, 110, 260)
    cold_moon(c, ux(3.7), uy(2.2), 44)
    for cx_, cy_, rx in ((ux(2.6), uy(2.5), 120), (ux(-3.2), uy(2.7), 160)):          # Wolkenfetzen
        c.glow(cx_, cy_, rx, rx * 0.25, (90, 104, 130, 90), 18)
    hill = [(-20, 330), (-20, 262), (160, 248), (330, 266), (520, 240), (700, 256), (880, 236), (1060, 254), (1220, 244), (1220, 330)]
    hpoly(c, hill, HILL, lw=0, seed=2, amp=2)
    tower_silhouette(c, 250, 262, 0.9)
    chapel_silhouette(c, 900, 246, 0.85)
    rnd = random.Random(9)
    for k in range(26):                                                               # Graeber auf dem Huegel
        x = rnd.uniform(20, 1180)
        if 200 < x < 300 or 820 < x < 980:
            continue
        b = 262 - 12 * math.sin(x / 140)
        headstone_px(c, x, b + 4, rnd.uniform(8, 12), rnd.uniform(12, 18), HILL_D, seed=k, form=rnd.randint(0, 3), rim=False)
    fence_px(c, 284, 336)
    ground(c, 330, seed=5)
    yew_px(c, 70, 470, 330, seed=1)
    yew_px(c, 1150, 450, 290, seed=2)
    for k, (x, base, w, h, form) in enumerate(((ux(-3.3), 410, 52, 74, 0), (ux(-1.9), 392, 40, 58, 1), (ux(2.9), 400, 46, 66, 2),
                                              (ux(4.1), 418, 56, 82, 3), (ux(-4.6), 430, 48, 70, 1))):
        headstone_px(c, x, base, w, h, STONE_D, seed=10 + k, form=form)
        c.ell(x, base + 4, w * 0.7, 6, (0, 0, 0, 90), lw=0)
    c.glow(ux(0.6), uy(-1.4), 300, 90, (120, 150, 200, 40), 40)                       # Mondschein um die Grube
    for x, y, w in ((260, 500, 180), (920, 560, 220), (560, 640, 260), (120, 620, 160)):
        c.glow(x, y, w, 24, (150, 165, 190, 60), 26)
    c.vignette(0.6)
    V.save_bg(c, "gy_eject_grave_bg.jpg")
    bgc = c

    # Grube: Oeffnung mit Erdwand hinten (Pivot Mitte, 2,6 x 1,0)
    c = C(260, 100)
    hpoly(c, [(18, 18), (242, 18), (232, 82), (28, 82)], (10, 8, 8, 255), lw=4, seed=1)
    hpoly(c, [(18, 18), (242, 18), (238, 44), (22, 44)], EARTH, lw=0, seed=2)
    grad_rect(c, 22, 44, 236, 82, (24, 18, 16), (6, 5, 5))
    for k in range(9):                                                                # Wurzeln in der Wand
        x = 30 + k * 24
        hline(c, [(x, 22), (x + 6, 34), (x + 2, 46)], (120, 96, 70, 255), 2, seed=k)
    for k in range(14):
        c.ell(30 + k * 15, 26 + (k % 3) * 5, 3, 2, (110, 96, 80, 255), lw=0)
    hline(c, [(18, 18), (242, 18)], (130, 108, 84, 255), 3, seed=3)
    V.save(c, "gy_eject_pit.png")

    # Vorderer Rand der Grube (Pivot oben Mitte, 2,8 x 0,6, sitzt bei (0,6, -1,6)): Boden aus dem Hintergrund
    # ausgeschnitten, damit der Rand nahtlos in die Wiese uebergeht, darauf Erdkante und Grasbueschel
    c = C(280, 60)
    x0, y0 = ux(0.6) - 140, uy(-1.6)
    cut = bgc.img.crop((int(x0 * S), int(y0 * S), int((x0 + 280) * S), int((y0 + 60) * S)))
    m = Image.new("L", cut.size, 0)
    ImageDraw.Draw(m).polygon(c.P([(0, 12), (280, 12), (280, 60), (0, 60)]), fill=255)
    c.img.paste(cut, (0, 0), m)
    c.d = ImageDraw.Draw(c.img)
    hpoly(c, [(34, 8), (246, 8), (250, 16), (238, 22), (140, 25), (42, 22), (30, 16)], EARTH, lw=3, seed=2)   # Erdkante = Vorderwand der Grube
    rnd = random.Random(3)
    for _ in range(40):
        x = rnd.uniform(30, 250)
        for (a, b) in HD.tuft(x, rnd.uniform(14, 40), rnd, n=3, h=12, spread=4):
            c.line([a, b], GRASS_L if rnd.random() < 0.4 else GRASS, 1.6)
    for _ in range(10):
        c.ell(rnd.uniform(44, 236), rnd.uniform(10, 19), rnd.uniform(3, 6), rnd.uniform(2, 4), EARTH_L, lw=1)
    V.save(c, "gy_eject_pit_lip.png")

    # Erdhaufen (Pivot unten Mitte, 1,7 x 0,9)
    c = C(170, 90)
    hpoly(c, [(4, 88), (30, 50), (64, 24), (100, 14), (140, 34), (166, 88)], EARTH, lw=4, seed=1, sh=(0.18, 0.3))
    rnd = random.Random(4)
    for _ in range(26):
        x, y = rnd.uniform(24, 150), rnd.uniform(28, 82)
        c.ell(x, y, rnd.uniform(4, 9), rnd.uniform(3, 6), rnd.choice((EARTH_L, EARTH_D, (88, 72, 56, 255))), lw=1)
    for _ in range(4):
        c.ell(rnd.uniform(40, 130), rnd.uniform(40, 80), rnd.uniform(5, 8), rnd.uniform(4, 6), STONE_D, lw=2)
    aline(c, [(40, 50), (80, 22)], (200, 210, 230, 70), 3)
    V.save(c, "gy_eject_mound.png")

    # Schaufel (Pivot unten Mitte = Blattspitze, 0,4 x 1,5)
    c = C(40, 150)
    hpoly(c, [(8, 104), (32, 104), (32, 130), (20, 148), (8, 130)], (120, 126, 136, 255), lw=3, seed=1, sh=(0.1, 0.3))
    hrect(c, 16, 10, 24, 106, WOOD, lw=3, seed=2)
    hrr(c, 8, 2, 32, 14, 5, WOOD_D, lw=3, seed=3)
    aline(c, [(18, 14), (18, 100)], a4(WOOD_L, 200), 2)
    V.save(c, "gy_eject_shovel.png")

    # Zugeschuettetes Grab (Pivot Mitte, 2,6 x 0,9)
    c = C(260, 90)
    hpoly(c, [(16, 70), (40, 36), (130, 22), (220, 36), (244, 70), (130, 82)], EARTH, lw=4, seed=1, sh=(0.16, 0.3))
    rnd = random.Random(5)
    for _ in range(40):
        c.ell(rnd.uniform(40, 220), rnd.uniform(34, 74), rnd.uniform(3, 7), rnd.uniform(2, 5), rnd.choice((EARTH_L, EARTH_D)), lw=1)
    V.save(c, "gy_eject_fill.png")

    # Grabstein am Kopfende (Pivot unten Mitte, 1,0 x 1,2)
    c = C(100, 120)
    headstone_px(c, 50, 118, 76, 104, STONE, seed=7, form=0)
    for k in range(3):
        hline(c, [(30, 70 + k * 12), (70, 70 + k * 12)], (70, 72, 82, 255), 2, seed=k)
    c.ell(22, 108, 10, 6, MOSS, lw=0)
    V.save(c, "gy_eject_headstone.png")

    # Knochenarm (Pivot unten Mitte, 0,7 x 1,7)
    c = C(70, 170)
    for dx in (-5, 5):
        hline(c, [(35 + dx, 168), (35 + dx * 0.6, 70)], INK, 9, seed=dx)
        hline(c, [(35 + dx, 168), (35 + dx * 0.6, 70)], BONE, 6, seed=dx)
    hell(c, 35, 64, 12, 9, BONE, lw=3, seed=3, sh=(0.1, 0.3))                         # Handwurzel
    for k, (a, ln) in enumerate(((-2.4, 46), (-1.95, 54), (-1.55, 56), (-1.2, 50), (-0.55, 34))):
        x0, y0 = 35 + 9 * math.cos(a), 60 + 9 * math.sin(a)
        mx, my = x0 + math.cos(a) * ln * 0.5, y0 + math.sin(a) * ln * 0.5
        ex, ey = x0 + math.cos(a - 0.25) * ln, y0 + math.sin(a - 0.25) * ln
        for col, w in ((INK, 7), (BONE, 4)):
            hline(c, [(x0, y0), (mx, my), (ex, ey)], col, w, seed=k)
        c.ell(mx, my, 3, 3, BONE_D, lw=1)
    for y in range(80, 166, 22):
        aline(c, [(29, y), (41, y + 4)], a4(BONE_D, 200), 2)
    V.save(c, "gy_eject_hand.png")

    # Raben (sitzend 0,9 x 0,7 und fliegend 1,3 x 0,7, Blick nach rechts)
    c = C(90, 70)
    crow_px(c, 42, 40, 1.4)
    V.save(c, "gy_eject_crow.png")
    c = C(130, 70)
    crow_px(c, 65, 34, 1.0, flying=True)
    V.save(c, "gy_eject_crow_fly.png")


# ================================================================== Szene 2: Die Totenglocke

def belfry():
    c = C(BW, BH)
    stones = HD.stone_grid(0, 0, BW, BH, 70, 34, seed=3, joint=3, jitter=0.15, tilt=0.0, skip=0.0, split=0.08, merge=0.05, periodic=False, bond=0.5)
    c.d.rectangle([0, 0, BW * S, BH * S], fill=(40, 42, 50, 255))
    rnd = random.Random(2)
    for i, st in enumerate(stones):
        v = rnd.randint(-9, 9)
        col = (66 + v, 70 + v, 80 + v, 255)
        c.d.polygon(c.P(st.pts), fill=col)
        HD.ink(c.d, c.P(st.pts + [st.pts[0]]), (30, 30, 36, 255), 2 * S, seed=i, var=0.2, closed=True)
    ax0, ax1, atop, abot = ux(1.3), ux(4.7), uy(2.4), FLOOR_PX - 36                    # Bogenoeffnung
    arch = [(ax0, abot), (ax0, atop + 170)] + [((ax0 + ax1) / 2 - (ax1 - ax0) / 2 * math.cos(t), atop + 170 - 170 * math.sin(t)) for t in [k * math.pi / 20 for k in range(21)]] + [(ax1, abot)]
    sky = C(BW, BH)
    grad(sky, (14, 20, 34, 255), (44, 60, 72, 255), 0, abot)
    stars(sky, 60, 300, seed=7)
    cold_moon(sky, ax1 - 80, atop + 70, 34)
    # Friedhof weit unten: Huegel, Wege, Grabreihen, Kapellendach, Nebel
    hpoly(sky, [(ax0 - 10, abot), (ax0 - 10, abot - 70), (ax1 + 10, abot - 100), (ax1 + 10, abot)], (24, 34, 34, 255), lw=0)
    for r in range(5):
        y = abot - 80 + r * 16
        for k in range(14):
            x = ax0 + 10 + k * 24 + (r % 2) * 12
            sky.d.rectangle(sky.P([(x, y - 7), (x + 5, y)]), fill=(70, 78, 84, 255))
    hline(sky, [(ax0, abot - 40), (ax1, abot - 64)], (70, 68, 66, 255), 5, seed=1)
    hpoly(sky, [(ax0 + 40, abot - 60), (ax0 + 130, abot - 60), (ax0 + 85, abot - 100)], (30, 30, 38, 255), lw=0)
    for x, y, w in ((ax0 + 120, abot - 50, 130), (ax1 - 90, abot - 70, 110)):
        sky.glow(x, y, w, 16, (150, 165, 190, 90), 14)
    m = Image.new("L", c.img.size, 0)
    ImageDraw.Draw(m).polygon(c.P(arch), fill=255)
    c.img.paste(sky.img, (0, 0), m)
    c.d = ImageDraw.Draw(c.img)
    hpoly(c, [(ax0 - 26, abot)] + arch[1:-1] + [(ax1 + 26, abot)] + [(ax1, abot)] + arch[-2:0:-1] + [(ax0, abot)], None, lw=0)
    HD.ink(c.d, c.P(arch), INK, 6 * S, seed=1, var=0.2)
    for k in range(9):                                                                # Bogensteine
        t = k / 8
        a = math.pi * (1 - t)
        bx, by = (ax0 + ax1) / 2 + (ax1 - ax0) / 2 * math.cos(a), atop + 170 - 170 * math.sin(a)
        hline(c, [(bx, by), (bx + 18 * math.cos(a), by - 18 * math.sin(a))], (36, 36, 44, 255), 3, seed=k)
    hrect(c, ax0 - 30, abot, ax1 + 30, FLOOR_PX, STONE, lw=4, seed=2, sh=(0.15, 0.3))   # Bruestung
    grad(c, WOOD, WOOD_D, FLOOR_PX, BH)                                                  # Bodenbohlen
    for x in range(-40, BW, 110):
        c.line([(x, FLOOR_PX), (x + 80, BH)], a4(WOOD_D, 255), 3)
    hrect(c, -10, 20, BW + 10, 58, WOOD_D, lw=4, seed=4, sh=(0.1, 0.3))                  # Balken oben
    for x0, x1 in ((40, 230), (ux(-0.6) + 120, ax0 - 30)):
        hline(c, [(x0, 58), (x1, 200)], WOOD_D, 14, seed=int(x0))
        hline(c, [(x0, 58), (x1, 200)], WOOD, 9, seed=int(x0))
    hrect(c, ux(-0.6) - 22, 20, ux(-0.6) + 22, 72, IRON, lw=4, seed=6)                   # Glockenlager
    for k in range(3):                                                                # Seilrollen an der Wand
        hell(c, 120 + k * 8, 380 + k * 4, 34 - k * 4, 14, (150, 128, 92, 255), lw=3, seed=k)
    c.glow(150, 300, 140, 120, (255, 200, 120, 45), 30)                               # Laternenschein links
    hline(c, [(150, 58), (150, 250)], (60, 56, 50, 255), 3, seed=8)
    hrr(c, 136, 250, 164, 296, 4, (40, 34, 30, 255), lw=4, seed=9)
    c.d.rectangle(c.P([(141, 256), (159, 290)]), fill=(255, 214, 140, 255))
    cobweb_px(c, 0, 58, 110, 1, 1, seed=3)
    cobweb_px(c, ax0 - 30, 58, 60, -1, 1, seed=4)
    for k in range(18):                                                               # Federn und Dreck am Boden
        x, y = rnd.uniform(40, ax0), rnd.uniform(FLOOR_PX + 10, BH - 20)
        aline(c, [(x, y), (x + rnd.uniform(-8, 8), y - 6)], (220, 220, 214, 160), 2)
    c.vignette(0.55)
    V.save_bg(c, "gy_eject_belfry_bg.jpg")

    # Glocke mit Joch (Pivot oben Mitte bei (0,5, 0,96); 1,9 x 2,3)
    c = C(190, 230)
    hrect(c, 20, 4, 170, 26, WOOD_D, lw=4, seed=1, sh=(0.1, 0.3))                       # Joch
    for x in (70, 120):
        hrect(c, x - 5, 20, x + 5, 56, IRON, lw=3, seed=x)
    bell = [(95 - 26, 44), (95 + 26, 44), (95 + 44, 70), (95 + 50, 150), (95 + 64, 196), (95 + 80, 214), (95 - 80, 214), (95 - 64, 196), (95 - 50, 150), (95 - 44, 70)]
    hpoly(c, bell, BRONZE, lw=5, seed=2, sh=(0.12, 0.3), )
    m, md = c.mask()
    md.polygon(c.P(bell), fill=255)
    c.shade_x(m, 0.25, 0.3)
    hpoly(c, [(95 - 70, 200), (95 + 70, 200), (95 + 80, 214), (95 - 80, 214)], BRONZE_D, lw=3, seed=3)
    for y in (90, 168):                                                               # Zierbaender
        hline(c, [(95 - 48 - (y - 90) * 0.08, y), (95 + 48 + (y - 90) * 0.08, y)], BRONZE_D, 4, seed=y)
    for k in range(7):                                                                # Inschrift
        arect(c, 95 - 42 + k * 12, 106, 95 - 36 + k * 12, 116, a4(BRONZE_D, 220))
    aline(c, [(95 - 34, 60), (95 - 46, 190)], (255, 230, 170, 120), 6)
    hell(c, 95, 224, 13, 8, IRON_D, lw=3, seed=4)                                     # Kloeppel
    hline(c, [(95, 200), (95, 218)], IRON_D, 5, seed=5)
    V.save(c, "gy_eject_bell.png")

    c = C(20, 300)                                                                    # Glockenseil (Pivot oben)
    hline(c, [(10, 0), (11, 150), (9, 300)], (150, 128, 92, 255), 6, seed=1, amp=2)
    for y in range(10, 300, 14):
        c.line([(7, y), (13, y + 5)], (110, 92, 66, 255), 2)
    hell(c, 10, 240, 9, 16, (150, 40, 50, 255), lw=3, seed=2)
    V.save(c, "gy_eject_rope.png")


# ================================================================== Szene 3: Das Krematorium

def furnace():
    c = C(BW, BH)
    c.d.rectangle([0, 0, BW * S, BH * S], fill=(54, 34, 30, 255))
    rnd = random.Random(3)
    for row, y in enumerate(range(0, FLOOR_PX, 26)):                                   # Ziegelwand
        for x in range(-((row % 2) * 30), BW, 60):
            col = (BRICK if rnd.random() < 0.6 else BRICK_D)
            col = tuple(max(0, min(255, int(v * rnd.uniform(0.85, 1.12)))) for v in col[:3]) + (255,)
            c.d.rectangle(c.P([(x + 2, y + 2), (x + 58, y + 24)]), fill=col)
    for k in range(4):                                                                # Russ von oben
        arect(c, 0, 0, BW, 150 - k * 34, (10, 8, 8, 24))
    grad(c, (70, 66, 64, 255), (36, 34, 34, 255), FLOOR_PX, BH)                        # Steinboden
    for x in range(-60, BW + 60, 90):
        c.line([(x, FLOOR_PX), (x + (x - 600) * 0.5, BH)], a4((30, 28, 28, 255), 255), 2)
    for y in (FLOOR_PX + 40, FLOOR_PX + 100, FLOOR_PX + 180):
        c.line([(0, y), (BW, y)], a4((30, 28, 28, 255), 255), 2)
    fx = ux(0.9)                                                                      # Ofenblock
    hrect(c, fx - 250, 120, fx + 250, FLOOR_PX, BRICK_D, lw=6, seed=4, sh=(0.1, 0.3))
    for row, y in enumerate(range(124, FLOOR_PX, 22)):
        for x in range(int(fx - 246) - (row % 2) * 24, int(fx + 246), 48):
            c.d.rectangle(c.P([(max(fx - 246, x + 2), y + 2), (min(fx + 246, x + 46), y + 20)]),
                          fill=(110 + rnd.randint(-14, 10), 56 + rnd.randint(-8, 8), 44 + rnd.randint(-6, 6), 255))
    ox0, ox1, otop = fx - 92, fx + 92, uy(0.55)                                       # Ofenloch (Glut)
    arch = [(ox0, FLOOR_PX - 30), (ox0, otop + 60)] + [(fx - 92 * math.cos(t), otop + 60 - 60 * math.sin(t)) for t in [k * math.pi / 16 for k in range(17)]] + [(ox1, FLOOR_PX - 30)]
    hpoly(c, [(x + (x - fx) * 0.16, y - (8 if y < otop + 70 else 0)) for x, y in arch], (88, 84, 86, 255), lw=5, seed=6)
    hpoly(c, arch, (30, 10, 6, 255), lw=5, seed=7)
    g = C(BW, BH)
    g.glow(fx, FLOOR_PX - 70, 90, 70, (255, 120, 40, 200), 24)
    g.glow(fx, FLOOR_PX - 60, 50, 36, (255, 210, 120, 200), 12)
    m = Image.new("L", c.img.size, 0)
    ImageDraw.Draw(m).polygon(c.P(arch), fill=255)
    c.img.paste(Image.alpha_composite(c.img, g.img), (0, 0), m)
    c.d = ImageDraw.Draw(c.img)
    hrect(c, fx - 130, FLOOR_PX - 30, fx + 130, FLOOR_PX - 8, (70, 66, 64, 255), lw=4, seed=8)   # Schwelle
    hrect(c, fx + 150, 40, fx + 200, 120, IRON_D, lw=5, seed=9, sh=(0.1, 0.3))          # Rohr
    hrect(c, fx + 140, 0, fx + 210, 40, IRON, lw=5, seed=10)
    hell(c, fx + 190, 200, 26, 26, (226, 218, 194, 255), lw=4, seed=11)                 # Manometer
    c.ell(fx + 190, 200, 3, 3, INK, lw=0)
    for k, y in enumerate((150, 250, 350)):                                           # Urnenregal links
        hrect(c, 40, y, 260, y + 12, WOOD_D, lw=3, seed=20 + k)
        for j in range(4):
            ux_ = 70 + j * 52
            col = (BRONZE, (70, 90, 110, 255), (110, 70, 56, 255), (90, 96, 88, 255))[(j + k) % 4]
            hpoly(c, [(ux_ - 12, y), (ux_ + 12, y), (ux_ + 17, y - 22), (ux_ + 12, y - 40), (ux_ - 12, y - 40), (ux_ - 17, y - 22)], col, lw=3, seed=k * 7 + j,
                  sh=(0.1, 0.3))
            hrect(c, ux_ - 9, y - 46, ux_ + 9, y - 40, light(col, -0.2) if False else (60, 50, 40, 255), lw=2, seed=k + j)
    hpoly(c, [(BW - 220, FLOOR_PX + 8), (BW - 160, FLOOR_PX - 50), (BW - 90, FLOOR_PX - 70), (BW - 20, FLOOR_PX - 40), (BW + 10, FLOOR_PX + 8)],
          (26, 26, 32, 255), lw=4, seed=13)                                           # Kohlen
    for _ in range(40):
        c.ell(rnd.uniform(BW - 210, BW - 20), rnd.uniform(FLOOR_PX - 55, FLOOR_PX), rnd.uniform(4, 9), rnd.uniform(3, 7), (40, 40, 48, 255), lw=1)
    for k in range(2):                                                                # Schienen zum Ofen
        hline(c, [(fx - 60 + k * 120, FLOOR_PX), (fx - 200 + k * 400, BH)], (130, 134, 142, 255), 5, seed=30 + k)
    c.glow(fx, FLOOR_PX + 60, 260, 70, (255, 120, 40, 50), 30)
    cobweb_px(c, BW, 0, 90, -1, 1, seed=6)
    c.vignette(0.55)
    V.save_bg(c, "gy_eject_furnace_bg.jpg")

    # Ofentuer (Pivot links Mitte, 1,9 x 1,7)
    c = C(190, 170)
    door = [(4, 166), (4, 60)] + [(94 - 90 * math.cos(t), 60 - 56 * math.sin(t)) for t in [k * math.pi / 16 for k in range(17)]] + [(184, 166)]
    hpoly(c, door, IRON, lw=6, seed=1, sh=(0.12, 0.3))
    for k in range(4):                                                                # Luftschlitze (Glut dahinter)
        y = 92 + k * 16
        hrr(c, 40, y, 150, y + 8, 3, (255, 140, 50, 255), lw=2, seed=k)
    for x, y in ((18, 70), (170, 70), (18, 150), (170, 150), (94, 18)):
        c.rivet(x, y, 5, IRON_L)
    hrect(c, 150, 120, 186, 132, IRON_L, lw=3, seed=5)
    aline(c, [(16, 60), (16, 150)], (180, 190, 210, 80), 3)
    V.save(c, "gy_eject_door.png")

    # Manometer-Nadel (Pivot links Mitte, 0,24 x 0,06; zeigt bei rot=0 nach rechts)
    c = C(24, 6)
    hpoly(c, [(0, 1), (22, 2.6), (24, 3), (22, 3.4), (0, 5)], (180, 30, 30, 255), lw=1.5, seed=1)
    V.save(c, "gy_eject_needle.png")

    # Urne, die der Ofen zurueckgibt (Pivot unten Mitte, 0,44 x 0,6)
    c = C(44, 60)
    body = [(10, 58), (34, 58), (40, 36), (34, 16), (28, 12), (16, 12), (10, 16), (4, 36)]
    hpoly(c, body, BRONZE, lw=3, seed=1, sh=(0.15, 0.3))
    m, md = c.mask()
    md.polygon(c.P(body), fill=255)
    c.shade_x(m, 0.25, 0.3)
    hrr(c, 13, 4, 31, 13, 3, BRONZE_D, lw=3, seed=2)
    hell(c, 22, 4, 5, 3, BRONZE_D, lw=2, seed=3)
    hline(c, [(7, 40), (37, 40)], BRONZE_D, 2.5, seed=4)
    aline(c, [(14, 20), (11, 50)], (255, 230, 170, 120), 3)
    V.save(c, "gy_eject_urn.png")


# ================================================================== Szene 4: Die Gruft

def crypt():
    c = C(BW, BH)
    c.d.rectangle([0, 0, BW * S, BH * S], fill=(70, 74, 72, 255))
    rnd = random.Random(5)
    cols_x = (ux(-2.6), ux(3.4))
    for row in range(3):                                                              # Grabnischen, nicht hinter den Saeulen
        for k in range(12):
            x0, y0 = 14 + k * 100, 46 + row * 92
            if any(abs(x0 + 44 - cx) < 90 for cx in cols_x) or (row < 2 and 470 < x0 + 44 < 730):
                continue
            hrect(c, x0, y0, x0 + 88, y0 + 80, (58, 62, 60, 255), lw=3, seed=row * 20 + k)
            open_ = rnd.random() < 0.14
            hrect(c, x0 + 7, y0 + 7, x0 + 81, y0 + 73, (14, 14, 18, 255) if open_ else (146, 148, 140, 255), lw=3, seed=row * 30 + k, sh=(0.1, 0.25))
            if not open_:
                hrect(c, x0 + 26, y0 + 32, x0 + 62, y0 + 46, BRONZE_D, lw=2, seed=k)
                c.line([(x0 + 30, y0 + 39), (x0 + 58, y0 + 39)], (60, 44, 24, 255), 2)
            else:
                hell(c, x0 + 44, y0 + 58, 12, 10, (196, 188, 168, 255), lw=2, seed=k)
                c.ell(x0 + 39, y0 + 56, 3, 3, (20, 20, 20, 255), lw=0); c.ell(x0 + 49, y0 + 56, 3, 3, (20, 20, 20, 255), lw=0)
    sx = ux(0.5)                                                                      # Buntglasfenster hinten (Mondlicht)
    win = [(sx - 70, 228), (sx - 70, 100), (sx, 36), (sx + 70, 100), (sx + 70, 228)]
    hpoly(c, [(x + (x - sx) * 0.18, y + (6 if y > 200 else -8)) for x, y in win], (92, 96, 94, 255), lw=5, seed=2)
    hpoly(c, win, (22, 30, 54, 255), lw=6, seed=1)
    glass = [(140, 40, 56, 230), (40, 70, 150, 230), (190, 150, 60, 230), (50, 110, 80, 230)]
    for i in range(5):
        for j in range(3):
            x0, y0 = sx - 62 + j * 42, 104 + i * 24
            apoly(c, [(x0 + 21, y0), (x0 + 40, y0 + 12), (x0 + 21, y0 + 24), (x0 + 2, y0 + 12)], glass[(i * 3 + j) % 4])
    c.ell(sx, 78, 20, 20, (200, 160, 60, 230), lw=3)
    c.line([(sx - 6, 72), (sx + 6, 72)], (90, 60, 30, 255), 4)
    c.line([(sx, 64), (sx, 92)], (90, 60, 30, 255), 4)
    beam = C(BW, BH)
    apoly(beam, [(sx - 60, 228), (sx + 60, 228), (sx + 190, FLOOR_PX + 40), (sx - 150, FLOOR_PX + 40)], (170, 190, 230, 34))
    c.img.alpha_composite(beam.img.filter(ImageFilter.GaussianBlur(10 * S)))
    c.d = ImageDraw.Draw(c.img)
    for x in cols_x:                                                                  # Saeulen
        hrect(c, x - 34, 30, x + 34, FLOOR_PX, MARBLE, lw=5, seed=int(x), sh=(0.0, 0.0))
        m, md = c.mask()
        md.rectangle(c.P([(x - 34, 30), (x + 34, FLOOR_PX)]), fill=255)
        c.shade_x(m, 0.2, 0.35)
        for k in range(4):
            aline(c, [(x - 22 + k * 15, 50), (x - 22 + k * 15, FLOOR_PX - 20)], a4(MARBLE_D, 200), 3)
        hrect(c, x - 46, 14, x + 46, 34, MARBLE, lw=4, seed=int(x) + 1)
        hrect(c, x - 46, FLOOR_PX - 22, x + 46, FLOOR_PX, MARBLE_D, lw=4, seed=int(x) + 2)
        vine = wob([(x - 30, FLOOR_PX - 30), (x + 20, FLOOR_PX - 120), (x - 24, FLOOR_PX - 220)], seed=int(x), amp=3, closed=False, step=12)
        hline(c, vine, (40, 60, 44, 255), 3, seed=int(x))
        for k, (lx, ly) in enumerate(vine[::2]):
            c.ell(lx + 6, ly, 7, 5, (60, 92, 64, 255) if k % 2 else (48, 76, 54, 255), lw=1)
    grad(c, (60, 64, 62, 255), (26, 28, 28, 255), FLOOR_PX, BH)                        # Schachbrettboden in Perspektive
    rows = 6
    for r in range(rows):
        y0 = FLOOR_PX + (BH - FLOOR_PX) * (r / rows) ** 1.25
        y1 = FLOOR_PX + (BH - FLOOR_PX) * ((r + 1) / rows) ** 1.25
        s0, s1 = 1 + 0.22 * r, 1 + 0.22 * (r + 1)
        for k in range(-12, 12):
            if (k + r) % 2:
                continue
            q = [(600 + k * 70 * s0, y0), (600 + (k + 1) * 70 * s0, y0), (600 + (k + 1) * 70 * s1, y1), (600 + k * 70 * s1, y1)]
            apoly(c, q, (34, 52, 46, 230))
        aline(c, [(0, y1), (BW, y1)], (22, 24, 24, 160), 2)
    for x in (ux(-3.6), ux(4.4)):                                                     # Kerzenstaender (Flammen sind Sprites)
        c.glow(x, FLOOR_PX - 170, 170, 170, (255, 196, 110, 46), 40)
        hline(c, [(x, FLOOR_PX), (x, FLOOR_PX - 120)], INK, 9, seed=int(x))
        hline(c, [(x, FLOOR_PX), (x, FLOOR_PX - 120)], IRON, 5, seed=int(x))
        hell(c, x, FLOOR_PX - 4, 26, 8, IRON, lw=3, seed=int(x) + 1)
        hell(c, x, FLOOR_PX - 122, 16, 6, IRON, lw=3, seed=int(x) + 2)
        V.candle_px(c, x, FLOOR_PX - 124, 34, r=9, seed=int(x))
    for k in range(10):                                                               # welke Blueten, Staub
        x = rnd.uniform(60, BW - 60)
        c.ell(x, FLOOR_PX + rnd.uniform(10, 60), 6, 4, (120, 60, 70, 255), lw=1)
    cobweb_px(c, 0, 0, 120, 1, 1, seed=8)
    cobweb_px(c, BW, 0, 90, -1, 1, seed=9)
    c.vignette(0.65)
    V.save_bg(c, "gy_eject_crypt_bg.jpg")

    # Sarkophag-Kasten (Pivot unten Mitte, 2,6 x 1,3), Oberseite innen dunkel
    c = C(260, 130)
    hrect(c, 10, 30, 250, 128, STONE, lw=5, seed=1, sh=(0.1, 0.3))
    hrect(c, 16, 22, 244, 40, (14, 18, 14, 255), lw=4, seed=2)                         # Innenraum (sichtbar bei offenem Deckel)
    for k in range(6):                                                                # Arkaden
        x0 = 24 + k * 37
        hpoly(c, [(x0, 118), (x0 + 28, 118), (x0 + 28, 70)] + [(x0 + 14 + 14 * math.cos(t), 70 - 14 * math.sin(t)) for t in [j * math.pi / 8 for j in range(9)]] + [(x0, 70)],
              STONE_D, lw=2, seed=k)
    hrect(c, 4, 116, 256, 130, STONE_D, lw=4, seed=3)
    c.ell(30, 120, 14, 6, MOSS, lw=0)
    V.save(c, "gy_eject_sarc.png")

    c = C(280, 54)                                                                     # Deckel (Pivot Mitte)
    hrect(c, 4, 10, 276, 44, STONE_L, lw=5, seed=1, sh=(0.15, 0.3))
    hrect(c, 30, 14, 250, 22, (150, 156, 166, 255), lw=2, seed=2)
    hell(c, 228, 18, 16, 9, STONE, lw=3, seed=3)                                       # Kopf der Grabfigur
    hpoly(c, [(60, 22), (210, 22), (214, 12), (56, 12)], STONE, lw=2, seed=4)
    V.save(c, "gy_eject_sarc_lid.png")

    c = C(170, 50)                                                                     # Mumienarm (Pivot links Mitte)
    hpoly(c, [(0, 18), (120, 14), (124, 36), (0, 34)], (196, 186, 160, 255), lw=4, seed=1)
    for k in range(7):
        x = 8 + k * 16
        hline(c, [(x, 15), (x + 14, 35)], (150, 140, 116, 255), 3, seed=k)
    hpoly(c, [(120, 10), (150, 6), (166, 14), (160, 22), (168, 30), (156, 36), (140, 34), (120, 40)], (150, 140, 116, 255), lw=4, seed=2)
    for k in range(3):
        hline(c, [(150, 12 + k * 8), (166, 10 + k * 9)], INK, 2, seed=k)
    hline(c, [(40, 34), (46, 46), (40, 50)], (196, 186, 160, 255), 3, seed=9)          # loses Bandende
    V.save(c, "gy_eject_mummy_arm.png")


# ================================================================== Skip: Die Raben

def roost():
    c = C(BW, BH)
    grad(c, (10, 14, 26, 255), (44, 58, 70, 255), 0, 360)
    stars(c, 120, 300, seed=11)
    c.glow(ux(0.2), uy(1.6), 330, 330, (150, 175, 210, 50), 80)
    cold_moon(c, ux(0.2), uy(1.6), 120)
    hpoly(c, [(-20, 380), (-20, 330), (300, 316), (700, 340), (1220, 320), (1220, 380)], HILL, lw=0, seed=3, amp=2)
    tower_silhouette(c, 1020, 330, 0.8)
    fence_px(c, 340, 392, step=26)
    ground(c, 380, seed=12)
    perches = [(ux(x), uy(y) + 10) for x, y in PERCH]
    dead_tree_px(c, ux(0.0), FLOOR_PX + 30, 520, col=(14, 16, 20, 255), seed=3, w=34, perches=perches)
    rnd = random.Random(14)
    for k in range(10):
        x = rnd.choice((rnd.uniform(40, 380), rnd.uniform(820, 1160)))
        base = rnd.uniform(420, 520)
        headstone_px(c, x, base, rnd.uniform(38, 58), rnd.uniform(56, 84), STONE_D, seed=40 + k, form=rnd.randint(0, 3))
    for x, y, w in ((200, 560, 220), (980, 600, 260), (600, 640, 300)):
        c.glow(x, y, w, 26, (150, 165, 190, 60), 26)
    c.vignette(0.6)
    V.save_bg(c, "gy_eject_roost_bg.jpg")


# ================================================================== Sonderszene: Sadako im Brunnenhaus

def wellhouse():
    c = C(BW, BH)
    c.d.rectangle([0, 0, BW * S, BH * S], fill=(46, 50, 58, 255))
    stones = HD.stone_grid(0, 0, BW, FLOOR_PX, 80, 40, seed=6, joint=3, jitter=0.18, tilt=0.0, skip=0.0, split=0.1, merge=0.05, periodic=False, bond=0.5)
    rnd = random.Random(6)
    for i, st in enumerate(stones):
        v = rnd.randint(-9, 9)
        col = (64 + v, 68 + v, 74 + v, 255)
        c.d.polygon(c.P(st.pts), fill=col)
        HD.ink(c.d, c.P(st.pts + [st.pts[0]]), (30, 32, 36, 255), 2 * S, seed=i, var=0.2, closed=True)
    for k in range(4):                                                                # Feuchte von unten
        arect(c, 0, FLOOR_PX - 24 * (k + 1), BW, FLOOR_PX, (10, 20, 30, 14))
    grad(c, (66, 70, 76, 255), (30, 32, 36, 255), FLOOR_PX, BH)                        # Kopfsteinboden
    for r in range(8):
        y = FLOOR_PX + 6 + r * (14 + r * 3)
        x = -rnd.uniform(0, 30)
        while x < BW:
            w = (28 + r * 6) * rnd.uniform(0.75, 1.3)
            v = rnd.randint(-10, 10)
            hell(c, x + w / 2, y + 4 + r, w / 2 - 2, 6 + r, (80 + v, 84 + v, 90 + v, 255), lw=1, seed=int(x) + r)
            x += w
    hrect(c, -10, 10, BW + 10, 44, WOOD_D, lw=4, seed=2, sh=(0.1, 0.3))                 # Balken
    for x in (180, 1020):
        hrect(c, x - 14, 44, x + 14, FLOOR_PX, WOOD_D, lw=4, seed=x, sh=(0.1, 0.3))
    wx0, wy0 = 900, 90                                                                # kleines Fenster mit Mond
    hrect(c, wx0, wy0, wx0 + 120, wy0 + 100, (20, 26, 44, 255), lw=5, seed=3)
    c.ell(wx0 + 84, wy0 + 30, 14, 14, (226, 232, 236, 255), lw=0)
    for x in (wx0 + 40, wx0 + 80):
        c.line([(x, wy0), (x, wy0 + 100)], (40, 40, 46, 255), 5)
    c.line([(wx0, wy0 + 50), (wx0 + 120, wy0 + 50)], (40, 40, 46, 255), 5)
    beam = C(BW, BH)                                                                  # Mondstrahl
    apoly(beam, [(wx0, wy0 + 100), (wx0 + 120, wy0 + 100), (ux(0.8) + 200, FLOOR_PX + 60), (ux(0.8) - 120, FLOOR_PX + 60)], (180, 200, 230, 30))
    c.img.alpha_composite(beam.img.filter(ImageFilter.GaussianBlur(8 * S)))
    c.d = ImageDraw.Draw(c.img)
    hline(c, [(160, 44), (160, 210)], (60, 56, 50, 255), 3, seed=4)                    # Laterne links
    c.glow(160, 236, 110, 100, (255, 200, 120, 38), 30)
    hrr(c, 146, 210, 174, 256, 4, (40, 34, 30, 255), lw=4, seed=5)
    c.d.rectangle(c.P([(151, 216), (169, 250)]), fill=(255, 214, 140, 255))
    hrect(c, 40, FLOOR_PX - 50, 150, FLOOR_PX - 4, STONE_D, lw=4, seed=6, sh=(0.1, 0.3))   # Trog
    hrect(c, 48, FLOOR_PX - 48, 142, FLOOR_PX - 40, (30, 44, 66, 255), lw=2, seed=7)
    hpoly(c, [(1060, FLOOR_PX), (1068, FLOOR_PX - 50), (1112, FLOOR_PX - 50), (1120, FLOOR_PX)], WOOD, lw=4, seed=8)   # Eimer
    c.line([(1064, FLOOR_PX - 30), (1116, FLOOR_PX - 30)], IRON, 4)
    cobweb_px(c, 0, 44, 90, 1, 1, seed=5)
    c.vignette(0.55)
    V.save_bg(c, "gy_eject_wellhouse_bg.jpg")

    # Brunnen hinten: Kranz-Oberseite mit dunklem Schacht, Pfosten, Dach, Welle, Seil (Pivot unten Mitte, 2,6 x 3,0)
    c = C(260, 300)
    cx, g = 130, 300
    hell(c, cx, g - 100, 98, 30, STONE_L, lw=5, seed=1, sh=(0.1, 0.3))
    hell(c, cx, g - 100, 80, 22, (8, 10, 12, 255), lw=4, seed=2)
    hell(c, cx, g - 96, 54, 12, (20, 34, 44, 255), lw=0, seed=3)                       # Wasser tief unten
    for sx in (-1, 1):
        px_ = cx + sx * 92
        hrect(c, px_ - 8, g - 240, px_ + 8, g - 74, WOOD_D, lw=4, seed=3 + sx, sh=(0.1, 0.25))
    hrect(c, cx - 100, g - 214, cx + 100, g - 200, WOOD_D, lw=4, seed=6)
    hell(c, cx, g - 207, 20, 9, WOOD, lw=3, seed=7)
    hline(c, [(cx, g - 200), (cx, g - 116)], (140, 120, 90, 255), 3, seed=8, amp=1.5)
    roof = [(cx - 128, g - 214), (cx, g - 292), (cx + 128, g - 214), (cx + 112, g - 208), (cx, g - 276), (cx - 112, g - 208)]
    hpoly(c, roof, (60, 56, 66, 255), lw=5, seed=10, sh=(0.1, 0.2))
    V.save(c, "gy_eject_well_back.png")

    c = C(210, 140)                                                                    # Brunnen vorn (Pivot unten Mitte)
    cx, g = 105, 138
    hpoly(c, [(cx - 82, g), (cx + 82, g), (cx + 82, g - 100), (cx - 82, g - 100)], STONE, lw=0, seed=1)
    rnd = random.Random(2)
    for row in range(4):
        y = g - 22 - row * 24
        x = cx - 82 - (0 if row % 2 else 24)
        while x < cx + 82:
            w = rnd.uniform(36, 54)
            col = (STONE, STONE_D, (90, 94, 102, 255))[rnd.randint(0, 2)]
            hpoly(c, [(max(cx - 82, x) + 2, y - 10), (min(cx + 82, x + w) - 2, y - 10), (min(cx + 82, x + w) - 2, y + 10), (max(cx - 82, x) + 2, y + 10)],
                  col, lw=2, outline=STONE_D, seed=int(x) + row, amp=1)
            x += w
    hline(c, [(cx - 82, g), (cx - 82, g - 100)], INK, 5, seed=3)
    hline(c, [(cx + 82, g), (cx + 82, g - 100)], INK, 5, seed=4)
    hole = Image.new("L", c.img.size, 0)                                              # Oeffnung freistellen: dort sieht man den Schacht
    ImageDraw.Draw(hole).ellipse(c.P([(cx - 80, g - 122), (cx + 80, g - 78)]), fill=255)
    c.img.putalpha(ImageChops.subtract(c.img.getchannel("A"), hole))
    c.d = ImageDraw.Draw(c.img)
    ring = ell_pts(cx, g - 100, 98, 30, 40, 0, math.pi) + ell_pts(cx, g - 100, 80, 22, 40, math.pi, 0)
    hpoly(c, ring, STONE_L, lw=5, seed=5, sh=(0.15, 0.3))
    for k in range(5):
        c.ell(cx + rnd.uniform(-70, 70), g - rnd.uniform(10, 90), rnd.uniform(6, 12), rnd.uniform(3, 6), (66, 92, 60, 255), lw=0)
    V.save(c, "gy_eject_well_front.png")

    c = C(160, 130)                                                                    # nasses schwarzes Haar ueber dem Rand (Pivot oben Mitte)
    rnd = random.Random(8)
    tips = []
    x = 10
    while x < 150:
        tips.append((x + rnd.uniform(-2, 2), rnd.uniform(78, 126)))
        x += rnd.uniform(9, 14)
    outline = [(14, 0), (146, 0), (152, 30)]
    for i in range(len(tips) - 1, -1, -1):                                            # Unterkante: Spitzen und Kerben
        tx, ty = tips[i]
        outline.append((tx + 4, ty - 26))
        outline.append((tx, ty))
        outline.append((tx - 4, ty - 26))
    outline.append((8, 30))
    hpoly(c, outline, (12, 12, 16, 255), lw=4, seed=1)
    m, md = c.mask()
    md.polygon(c.P(outline), fill=255)
    for k in range(46):                                                               # Straehnen innen
        x0 = rnd.uniform(14, 146)
        tx = min(tips, key=lambda t: abs(t[0] - x0))
        pts = [(x0, 0)]
        for j in range(1, 6):
            u = j / 5
            pts.append((x0 + (tx[0] - x0) * u + rnd.uniform(-2, 2), (tx[1] - 6) * u))
        aline(c, pts, (34, 36, 44, 200) if k % 3 else (4, 4, 6, 220), rnd.uniform(1.2, 2.6))
    for k in range(9):                                                                # nasser Glanz
        x0 = rnd.uniform(24, 136)
        y0 = rnd.uniform(4, 30)
        aline(c, [(x0, y0), (x0 + rnd.uniform(-3, 3), y0 + rnd.uniform(24, 46))], (120, 136, 170, 110), 2)
    for k in range(5):                                                                # Tropfen an den Spitzen
        tx, ty = tips[rnd.randrange(len(tips))]
        c.ell(tx, ty + 3, 2.2, 3, (150, 176, 210, 255), lw=1)
    V.save(c, "gy_eject_hair.png")

    c = C(80, 70)                                                                      # bleiche Hand, die den Rand packt (Pivot unten Mitte)
    pale, pale_d = (204, 212, 210, 255), (150, 160, 162, 255)
    hpoly(c, [(24, 0), (54, 0), (58, 20), (62, 34), (16, 34), (20, 20)], (16, 20, 24, 255), lw=0)   # Unterarm verschwindet im Schacht
    for y in range(0, 20, 2):
        k = y / 20
        col = tuple(int(16 + (v - 16) * k) for v in pale[:3]) + (255,)
        c.d.rectangle(c.P([(24 - k * 4, y), (54 + k * 4, y + 2)]), fill=col)
    hpoly(c, [(14, 40), (18, 22), (60, 22), (66, 40), (64, 46), (16, 46)], pale, lw=4, seed=1, sh=(0.12, 0.3))   # Handruecken
    for k in range(3):                                                                # Sehnen
        aline(c, [(26 + k * 12, 24), (24 + k * 13, 42)], (150, 160, 162, 150), 2)
    for k, (x, ln) in enumerate(((22, 20), (34, 24), (46, 23), (57, 18))):            # Finger, ueber den Rand gekrallt
        hrr(c, x - 5, 38, x + 5, 38 + ln, 5, pale, lw=3, seed=k + 2, sh=(0.1, 0.3))
        c.line([(x - 3, 46), (x + 3, 46)], pale_d, 1.6)
        hpoly(c, [(x - 4, 34 + ln), (x + 4, 34 + ln), (x + 3, 42 + ln), (x, 46 + ln), (x - 3, 42 + ln)], (60, 66, 62, 255), lw=2, seed=k + 9)
    hpoly(c, [(14, 30), (8, 40), (6, 52), (12, 56), (18, 44)], pale, lw=3, seed=20)    # Daumen
    hpoly(c, [(5, 52), (11, 53), (9, 60), (5, 59)], (60, 66, 62, 255), lw=2, seed=21)
    V.save(c, "gy_eject_pale_hand.png")

    # Bildrauschen (Bildschirm-Ebene, 3,4 x 1,9 -> per sx/sy aufgeblasen)
    w, h = 340, 190
    rng = np.random.default_rng(3)
    v = rng.integers(0, 255, (h * 2, w * 2)).astype(np.uint8)
    img = Image.fromarray(v, "L").resize((round(w * K), round(h * K)), Image.NEAREST)
    a = Image.new("L", img.size, 210)
    lines = Image.new("L", img.size, 0)
    ld = ImageDraw.Draw(lines)
    for y in range(0, img.height, 6):
        ld.line([(0, y), (img.width, y)], fill=120, width=2)
    rgb = Image.merge("RGB", (img, img, img))
    rgb = Image.composite(Image.new("RGB", img.size, (20, 20, 24)), rgb, lines)
    out = rgb.convert("RGBA")
    out.putalpha(a)
    out.save(OUT / "gy_eject_static.png", optimize=True)
    print("  gy_eject_static.png", out.size)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    grave()
    belfry()
    furnace()
    crypt()
    roost()
    wellhouse()


if __name__ == "__main__":
    main()
