# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_candy_eject.py - Grafik der Rauswurf-Szene "Die Suessigkeitenschuessel" (Vanilla-Karten mit Halloween-Optik)
# -> Resources/candy_eject/cb_eject_*
#
# Konventionen wie gen_graveyard_eject.py (die Zeichenhelfer der Villa werden mitbenutzt): gezeichnet in 100 px pro
# Szenen-Einheit mit Supersampling, exportiert mit K = 1,8 (180 px pro Einheit), Hintergrund 12 x 6,8 Einheiten als
# JPG, alles andere PNG mit Alpha. Generische Partikel (Glow, Puff, Mote) kommen aus dem Villa-Satz.
#
# Stil: Comic-Halloween in einer Speisekammer bei Nacht, Pflaume und Kuerbisorange, zitternde Umrisse (handdraw).
# Das Monster ist ein eigener Entwurf: lila Zottelfell, orange Glubschaugen, breites Maul mit stumpfen Zaehnen.
# Es besteht aus Einzelteilen (Rumpf mit Augenweiss und Oberkiefer, Unterkiefer, Pranke, Pupille, Lid), damit die
# Regie (candy_eject.py) Blick, Biss und Griff animieren kann.
#
#     python tools/gen_candy_eject.py

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_villa_eject as V                         # noqa: E402  (Zeichenhelfer, Export)
from gen_villa_eject import (C, S, K, BW, BH, INK, a4, ux, uy, hpoly, hrect, hell, hrr, hline, apoly, aline, grad_rect,
                             blur, ell_pts, rr_pts, wob, grad, rect, light)   # noqa: E402
import handdraw as HD                               # noqa: E402

OUT = HERE.parent / "Resources" / "candy_eject"
V.OUT = OUT

# ------------------------------------------------------------------ Palette
WALL_T, WALL_B = (30, 18, 40, 255), (62, 34, 66, 255)
SKY_T, SKY_B = (16, 12, 36, 255), (70, 40, 96, 255)
WOOD, WOOD_L, WOOD_D = (96, 62, 40, 255), (128, 90, 58, 255), (58, 36, 24, 255)
CLOTH, CLOTH_D = (176, 84, 30, 255), (120, 52, 20, 255)
CLOTH_STRIPE = (34, 24, 36, 255)
CERAMIC, CERAMIC_L, CERAMIC_D = (34, 26, 40, 255), (74, 58, 86, 255), (20, 14, 24, 255)
ORANGE, ORANGE_L, ORANGE_D = (238, 128, 32, 255), (255, 186, 90, 255), (170, 74, 18, 255)
PUMPKIN, PUMPKIN_D, PUMPKIN_L = (236, 118, 28, 255), (164, 70, 16, 255), (255, 170, 80, 255)
FUR, FUR_D, FUR_L = (122, 70, 198, 255), (80, 40, 142, 255), (168, 120, 236, 255)
MOUTH, TONGUE, TONGUE_L = (38, 10, 34, 255), (214, 70, 110, 255), (240, 120, 150, 255)
TOOTH, TOOTH_D = (240, 236, 220, 255), (190, 184, 160, 255)
EYE_W, EYE_IRIS, EYE_IRIS_D = (250, 246, 232, 255), (255, 150, 40, 255), (200, 90, 20, 255)
GUMMY = (236, 236, 240, 255)
WARM = (255, 200, 120, 255)
GREEN, GREEN_D = (120, 200, 80, 255), (60, 120, 40, 255)
PURPLE, PURPLE_D = (150, 80, 210, 255), (90, 40, 140, 255)
WHITE = (248, 246, 240, 255)
BH2 = 840                                           # Hintergrund 12 x 8,4 Einheiten (Kamera faehrt nach oben)


def ux(x):                                          # eigene Umrechnung fuer die hohe Buehne
    return BW / 2 + x * 100


def uy(y):
    return BH2 / 2 - y * 100


FLOOR_PX = int(uy(-1.25))                           # Tischkante (Boden der Szene)


# ------------------------------------------------------------------ Helfer

def fur_outline(cx, cy, rx, ry, seed=0, n=96, tuft=0.09, base_wob=0.035, a0=0.0, a1=math.tau):
    """Zottelige Silhouette: Ellipse mit kleinen Buescheln und leichter Unruhe."""
    rnd = random.Random(seed)
    pts = []
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        w = 1 + base_wob * math.sin(a * 5 + rnd.random() * 0.2) + base_wob * 0.6 * math.sin(a * 11 + 1.3)
        if k % 4 == 2:
            w += tuft * rnd.uniform(0.6, 1.0)
        if k % 4 == 3:
            w -= tuft * 0.25
        pts.append((cx + rx * w * math.cos(a), cy + ry * w * math.sin(a)))
    return pts


def fur_fill(c, pts, col, col_d, col_l, seed=0, lw=5, sh=(0.1, 0.3), strands=60, lit=(-0.35, -0.3)):
    """Fellflaeche mit Schattierung, Lichtfleck und Fellstrichen."""
    hpoly(c, pts, col, lw=lw, seed=seed, amp=1.6, sh=sh)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    rx, ry = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
    # Lichtfleck oben links (nur innerhalb der Form)
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse(c.P([(cx + lit[0] * rx - rx * 0.45, cy + lit[1] * ry - ry * 0.4), (cx + lit[0] * rx + rx * 0.45, cy + lit[1] * ry + ry * 0.4)]), fill=a4(col_l, 70))
    g = g.filter(ImageFilter.GaussianBlur(14 * S))
    m, md = c.mask()
    md.polygon(c.P(pts), fill=255)
    g.putalpha(Image.fromarray(np.minimum(np.asarray(g.split()[3]), np.asarray(m))))
    c.img.alpha_composite(g)
    c.d = ImageDraw.Draw(c.img)
    # Fellstriche
    rnd = random.Random(seed + 7)
    for _ in range(strands):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0.35, 0.96)
        x, y = cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)
        ln = rnd.uniform(6, 16)
        ang = a + rnd.uniform(-0.5, 0.5)
        colr = col_d if rnd.random() < 0.65 else col_l
        aline(c, [(x, y), (x + ln * math.cos(ang), y + ln * math.sin(ang))], a4(colr, 150), 2.2)


def tooth(c, x, y, w, h, seed=0, up=True):
    """Stumpfer Zahn, Wurzel bei (x, y); up = Zahn haengt nach unten (Oberkiefer)."""
    d = 1 if up else -1
    pts = [(x - w / 2, y), (x + w / 2, y), (x + w * 0.4, y + d * h), (x - w * 0.4, y + d * h)]
    hpoly(c, rr_pts(min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts), w * 0.3), TOOTH,
          lw=3, seed=seed, sh=(0.05, 0.25))


def candy_shadow(c, x, y, rx, ry):
    c.glow(x, y, rx, ry, (0, 0, 0, 90), 4)


# ------------------------------------------------------------------ Hintergrund: die Speisekammer

def table(c, y0, seed=41):
    """Tischvorderkante ab y0: Holz, Tischtuch mit Streifenborte, verstreute Bonbons. Steht im Hintergrund und
    noch einmal als eigene Ebene (cb_eject_table_front.png), hinter der das Monster aufsteigt."""
    grad(c, WOOD_L, WOOD_D, y0, c.h)
    rect(c, 0, y0 + 40, c.w, c.h, WOOD_D)
    for k in range(0, c.w, 7):
        aline(c, [(k, y0 + 42), (k + 3, c.h)], (0, 0, 0, 20), 2)
    hpoly(c, [(0, y0), (c.w, y0), (c.w, y0 + 40), (0, y0 + 40)], CLOTH, lw=4, seed=8, sh=(0.1, 0.3))
    for xx in range(-20, c.w + 20, 48):
        apoly(c, [(xx, y0 + 2), (xx + 22, y0 + 2), (xx + 18, y0 + 38), (xx - 4, y0 + 38)], a4(CLOTH_STRIPE, 200))
    hline(c, [(0, y0 + 1), (c.w, y0 + 1)], ORANGE_L, 3, seed=9)
    rnd3 = random.Random(seed)
    for _ in range(9):
        x = rnd3.uniform(80, c.w - 80)
        y = rnd3.uniform(y0 + 8, y0 + 34)
        if ux(-2.6) < x < ux(3.2) or ux(-5.2) < x < ux(-3.4):
            continue
        twist_px(c, x, y, 16, seed=rnd3.randint(0, 99), cols=rnd3.choice(((ORANGE, CERAMIC_D), (PURPLE, GREEN))))


def pantry_bg():
    c = C(BW, BH2)
    grad(c, WALL_T, WALL_B, 0, FLOOR_PX)
    # Tapete: schwache Fledermaus-Rauten
    rnd = random.Random(3)
    for yy in range(40, FLOOR_PX - 30, 70):
        for xx in range(20, BW, 86):
            x = xx + (35 if (yy // 70) % 2 else 0)
            col = a4((90, 54, 100), 60)
            c.d.polygon(c.P([(x, yy), (x + 9, yy + 6), (x + 22, yy + 2), (x + 14, yy + 12), (x, yy + 9), (x - 14, yy + 12), (x - 22, yy + 2), (x - 9, yy + 6)]), fill=col)
    # Fenster rechts mit Mond
    wx0, wy0, wx1, wy1 = 790, 130, 1030, 410
    hrect(c, wx0 - 16, wy0 - 16, wx1 + 16, wy1 + 16, WOOD_D, lw=5, seed=1, sh=(0.08, 0.2))
    grad_rect(c, wx0, wy0, wx1, wy1, SKY_T, SKY_B)
    stars = random.Random(9)
    for _ in range(40):
        sx, sy = stars.uniform(wx0 + 6, wx1 - 6), stars.uniform(wy0 + 6, wy1 - 60)
        r = stars.choice((1.0, 1.0, 1.4, 2.0))
        c.d.ellipse(c.P([(sx - r, sy - r), (sx + r, sy + r)]), fill=(230, 226, 255, stars.randint(120, 230)))
    c.glow(900, 220, 70, 70, (255, 230, 170, 60), 18)
    c.ell(900, 220, 34, 34, (246, 238, 210, 255), lw=0)
    for dx, dy, rr in ((0.3, -0.2, 0.2), (-0.35, 0.3, 0.14), (0.1, 0.45, 0.1)):
        c.ell(900 + 34 * dx, 220 + 34 * dy, 34 * rr, 34 * rr, (220, 212, 190, 255), lw=0)
    # Fledermaeuse vor dem Mond
    for bx, by, sc in ((870, 190, 1.0), (935, 255, 0.8), (815, 300, 0.7)):
        pts = [(bx - 20 * sc, by - 6 * sc), (bx - 8 * sc, by + 2 * sc), (bx, by - 4 * sc), (bx + 8 * sc, by + 2 * sc), (bx + 20 * sc, by - 6 * sc),
               (bx + 10 * sc, by + 8 * sc), (bx + 4 * sc, by + 4 * sc), (bx, by + 10 * sc), (bx - 4 * sc, by + 4 * sc), (bx - 10 * sc, by + 8 * sc)]
        c.d.polygon(c.P(pts), fill=(18, 10, 24, 255))
    for xx in (wx0 + 80, wx0 + 160):
        hline(c, [(xx, wy0), (xx, wy1)], WOOD_D, 6, seed=2)
    hline(c, [(wx0, wy0 + 130), (wx1, wy0 + 130)], WOOD_D, 6, seed=3)
    aline(c, [(wx0 + 8, wy0 + 8), (wx0 + 60, wy0 + 8)], (255, 255, 255, 40), 4)
    # Regalbrett links mit Glaesern
    sx0, sy0 = 60, 300
    hrect(c, sx0, sy0, sx0 + 330, sy0 + 16, WOOD, lw=4, seed=4, sh=(0.1, 0.3))
    hline(c, [(sx0 + 10, sy0 + 16), (sx0 + 30, sy0 + 60)], WOOD_D, 5, seed=5)
    hline(c, [(sx0 + 320, sy0 + 16), (sx0 + 300, sy0 + 60)], WOOD_D, 5, seed=6)
    for jx, jw, jh, col, seed in ((sx0 + 50, 44, 70, (120, 170, 90, 200), 11), (sx0 + 120, 54, 84, (200, 110, 50, 200), 12),
                                  (sx0 + 200, 40, 62, (150, 70, 160, 200), 13), (sx0 + 270, 50, 76, (236, 180, 70, 200), 14)):
        hrr(c, jx - jw / 2, sy0 - jh, jx + jw / 2, sy0, 8, col, lw=4, seed=seed, sh=(0.12, 0.25))
        hrect(c, jx - jw / 2 + 4, sy0 - jh - 10, jx + jw / 2 - 4, sy0 - jh + 2, (70, 50, 40, 255), lw=3, seed=seed + 1)
        aline(c, [(jx - jw / 2 + 8, sy0 - jh + 8), (jx - jw / 2 + 8, sy0 - 10)], (255, 255, 255, 70), 4)
    # Wimpelkette oben
    pts = [(0, 30), (150, 70), (300, 40), (450, 78), (600, 36), (750, 72), (900, 44), (1050, 76), (1200, 34)]
    hline(c, pts, (40, 28, 44, 255), 3, seed=7)
    rnd2 = random.Random(21)
    for k in range(len(pts) - 1):
        x0, y0 = pts[k]
        x1, y1 = pts[k + 1]
        for u in (0.25, 0.6):
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            col = ORANGE if (k + int(u * 10)) % 2 else (40, 28, 44, 255)
            hpoly(c, [(x - 16, y), (x + 16, y), (x, y + 34)], col, lw=3, seed=rnd2.randint(0, 99))
    table(c, FLOOR_PX)
    # Kuerbis links auf dem Tisch
    px, py = int(ux(-4.3)), FLOOR_PX
    candy_shadow(c, px, py + 2, 70, 12)
    for k, (dx, rxx) in enumerate(((0, 62), (-34, 44), (34, 44))):
        hell(c, px + dx, py - 52, rxx, 54, PUMPKIN, lw=4, seed=30 + k, sh=(0.12, 0.3))
    hrect(c, px - 7, py - 122, px + 7, py - 98, GREEN_D, lw=3, seed=35)
    for ex, ey in ((px - 24, py - 68), (px + 24, py - 68)):
        c.d.polygon(c.P([(ex - 14, ey + 10), (ex + 14, ey + 10), (ex, ey - 14)]), fill=(255, 236, 150, 255))
    grin = [(px - 36, py - 40), (px - 24, py - 30), (px - 12, py - 42), (px, py - 30), (px + 12, py - 42), (px + 24, py - 30), (px + 36, py - 40), (px + 30, py - 20), (px - 30, py - 20)]
    c.d.polygon(c.P(grin), fill=(255, 236, 150, 255))
    c.glow(px, py - 50, 90, 70, (255, 180, 70, 55), 24)
    V.save_bg(c, "cb_eject_pantry_bg.jpg")
    # dieselbe Tischkante als eigene Ebene (Pivot oben Mitte, liegt bei y = -1,25)
    c = C(BW, BH2 - FLOOR_PX)
    table(c, 0)
    V.save(c, "cb_eject_table_front.png")


# ------------------------------------------------------------------ Suessigkeiten

def twist_px(c, x, y, r, seed=0, cols=(ORANGE, CERAMIC_D)):
    """Bonbon im Papier mit Drehenden, (x, y) = Mitte, r = halbe Koerperhoehe."""
    a, b = cols
    for sgn in (-1, 1):
        hpoly(c, [(x + sgn * r * 1.3, y - r * 0.55), (x + sgn * r * 2.3, y - r * 0.9), (x + sgn * r * 2.1, y), (x + sgn * r * 2.3, y + r * 0.9), (x + sgn * r * 1.3, y + r * 0.55)],
              a, lw=3, seed=seed + sgn, sh=(0.1, 0.3))
    hell(c, x, y, r * 1.45, r, a, lw=3, seed=seed + 3, sh=(0.12, 0.3))
    m, md = c.mask()
    md.ellipse(c.P([(x - r * 1.45, y - r), (x + r * 1.45, y + r)]), fill=255)
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for k in range(-2, 3):
        xx = x + k * r * 0.7
        gd.polygon(c.P([(xx - r * 0.18, y - r * 1.2), (xx + r * 0.18, y - r * 1.2), (xx + r * 0.36, y + r * 1.2), (xx, y + r * 1.2)]), fill=b)
    g.putalpha(Image.fromarray(np.minimum(np.asarray(g.split()[3]), np.asarray(m))))
    c.img.alpha_composite(g)
    c.d = ImageDraw.Draw(c.img)
    aline(c, [(x - r * 0.9, y - r * 0.62), (x + r * 0.2, y - r * 0.72)], (255, 255, 255, 120), max(2, r * 0.18))


def candy_sprites():
    # Bonbon im Papier, zwei Farbstellungen
    for name, cols in (("cb_eject_candy_twist.png", (ORANGE, CERAMIC_D)), ("cb_eject_candy_twist2.png", (PURPLE, GREEN))):
        c = C(110, 56)
        twist_px(c, 55, 28, 18, seed=1, cols=cols)
        V.save(c, name)
    # Crewmate-Gummi (hell, wird per Tint eingefaerbt)
    c = C(60, 70)
    hpoly(c, rr_pts(8, 36, 24, 64, 7), (200, 200, 206, 255), lw=3, seed=2, sh=(0.08, 0.2))
    hpoly(c, rr_pts(36, 36, 52, 64, 7), (200, 200, 206, 255), lw=3, seed=3, sh=(0.08, 0.2))
    hpoly(c, rr_pts(13, 8, 50, 60, (18, 9)), GUMMY, lw=3, seed=4, sh=(0.14, 0.3))
    hpoly(c, rr_pts(27, 16, 56, 34, 8), (255, 255, 255, 255), lw=3, seed=5, sh=(0.1, 0.2))
    c.d.polygon(c.P(rr_pts(31, 19, 44, 25, 3)), fill=(255, 255, 255, 230))
    V.save(c, "cb_eject_candy_bean.png")
    # Augapfel-Kaugummi
    c = C(60, 60)
    hell(c, 30, 30, 26, 26, EYE_W, lw=3, seed=6, sh=(0.1, 0.3))
    rnd = random.Random(5)
    for _ in range(7):
        a = rnd.uniform(0, math.tau)
        aline(c, [(30 + 24 * math.cos(a), 30 + 24 * math.sin(a)), (30 + 13 * math.cos(a + 0.3), 30 + 13 * math.sin(a + 0.3))], (200, 60, 60, 160), 1.6)
    hell(c, 34, 30, 11, 11, GREEN, lw=3, seed=7, sh=(0.1, 0.3))
    c.ell(35, 30, 5, 5, INK, lw=0)
    c.ell(31, 26, 2, 2, WHITE, lw=0)
    V.save(c, "cb_eject_candy_eye.png")
    # Mini-Kuerbis
    c = C(64, 64)
    for k, (dx, rxx) in enumerate(((0, 24), (-14, 17), (14, 17))):
        hell(c, 32 + dx, 38, rxx, 22, PUMPKIN, lw=3, seed=10 + k, sh=(0.12, 0.3))
    hrect(c, 29, 8, 35, 20, GREEN_D, lw=2, seed=14)
    V.save(c, "cb_eject_candy_pump.png")
    # Candy Corn
    c = C(50, 70)
    hpoly(c, [(8, 62), (42, 62), (25, 6)], (255, 224, 90, 255), lw=3, seed=15, sh=(0.1, 0.25))
    m, md = c.mask()
    md.polygon(c.P([(8, 62), (42, 62), (25, 6)]), fill=255)
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.rectangle(c.P([(0, 24), (50, 44)]), fill=ORANGE)
    gd.rectangle(c.P([(0, 0), (50, 24)]), fill=WHITE)
    g.putalpha(Image.fromarray(np.minimum(np.asarray(g.split()[3]), np.asarray(m))))
    c.img.alpha_composite(g)
    c.d = ImageDraw.Draw(c.img)
    V.save(c, "cb_eject_candy_corn.png")
    # Lutscher mit Spirale
    c = C(60, 100)
    hrect(c, 27, 50, 33, 96, (230, 226, 210, 255), lw=2, seed=16)
    hell(c, 30, 30, 26, 26, PURPLE, lw=3, seed=17, sh=(0.12, 0.3))
    pts = []
    for k in range(80):
        t = k / 79
        a = t * math.tau * 2.4
        r = 2 + 22 * t
        pts.append((30 + r * math.cos(a), 30 + r * math.sin(a)))
    aline(c, pts, ORANGE, 5)
    aline(c, [(16, 18), (24, 14)], (255, 255, 255, 120), 3)
    V.save(c, "cb_eject_candy_lolly.png")
    # Kruemel (weiss, Tint) und Papier
    c = C(30, 30)
    hpoly(c, [(4, 10), (14, 3), (26, 8), (24, 22), (10, 27), (3, 20)], WHITE, lw=2, seed=18, sh=(0.1, 0.3))
    V.save(c, "cb_eject_crumb.png")
    c = C(120, 72)
    paper = [(6, 30), (30, 8), (58, 16), (84, 6), (114, 26), (100, 44), (112, 62), (70, 66), (40, 58), (14, 64)]
    hpoly(c, paper, a4(ORANGE, 235), lw=3, seed=19, sh=(0.12, 0.3))
    m, md = c.mask()
    md.polygon(c.P(paper), fill=255)
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for k in range(-1, 6):
        xx = 10 + k * 22
        gd.polygon(c.P([(xx, 0), (xx + 8, 0), (xx + 16, 72), (xx + 8, 72)]), fill=a4(CERAMIC_D, 200))
    g.putalpha(Image.fromarray(np.minimum(np.asarray(g.split()[3]), np.asarray(m))))
    c.img.alpha_composite(g)
    c.d = ImageDraw.Draw(c.img)
    for a_, b_ in (((30, 8), (40, 58)), ((84, 6), (70, 66))):
        aline(c, [a_, b_], (255, 255, 255, 60), 2)
    V.save(c, "cb_eject_wrapper.png")


# ------------------------------------------------------------------ Schuessel und Haufen

BOWL_W, BOWL_H = 520, 180                 # 5,2 x 1,8 Einheiten, Pivot unten Mitte
RIM_Y, RIM_RX, RIM_RY = 45, 250, 38


def bowl_back():
    c = C(BOWL_W, BOWL_H)
    cx = BOWL_W / 2
    # Innenwand (obere Haelfte des Randovals, nach unten eingewoelbt)
    inner = ell_pts(cx, RIM_Y, RIM_RX - 6, RIM_RY - 4, n=60)
    hpoly(c, inner, CERAMIC_D, lw=0, seed=1)
    m, md = c.mask()
    md.polygon(c.P(inner), fill=255)
    c.shade(m, 0.0, 0.35)
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse(c.P([(cx - RIM_RX + 30, RIM_Y - 10), (cx + RIM_RX - 30, RIM_Y + 60)]), fill=(90, 60, 110, 70))
    g = g.filter(ImageFilter.GaussianBlur(10 * S))
    g.putalpha(Image.fromarray(np.minimum(np.asarray(g.split()[3]), np.asarray(m))))
    c.img.alpha_composite(g)
    c.d = ImageDraw.Draw(c.img)
    # hinterer Rand (orange Borte, nur die obere Haelfte)
    rim = ell_pts(cx, RIM_Y, RIM_RX, RIM_RY, n=60, a0=math.pi, a1=math.tau)
    HD.ink(c.d, c.P(wob(rim, 2, 1.2, closed=False)), ORANGE, 9 * S, seed=2, var=0.2)
    HD.ink(c.d, c.P(wob(ell_pts(cx, RIM_Y, RIM_RX + 2, RIM_RY + 2, n=60, a0=math.pi, a1=math.tau), 3, 1.2, closed=False)), INK, 4 * S, seed=3, var=0.2)
    V.save(c, "cb_eject_bowl_back.png")


def bowl_front():
    c = C(BOWL_W, BOWL_H)
    cx = BOWL_W / 2
    bottom = BOWL_H - 8
    body = ell_pts(cx, RIM_Y, RIM_RX, RIM_RY, n=40, a0=0.0, a1=math.pi)       # vordere Randhaelfte
    foot_r = RIM_RX * 0.55
    body += [(cx + RIM_RX * 0.98, RIM_Y + 30), (cx + RIM_RX * 0.86, bottom - 40), (cx + foot_r, bottom), (cx - foot_r, bottom),
             (cx - RIM_RX * 0.86, bottom - 40), (cx - RIM_RX * 0.98, RIM_Y + 30)]
    # Reihenfolge: Rand von rechts nach links (a 0..pi geht ueber unten), dann aussen herum zurueck
    pts = body[:41] + body[41:][::-1]
    hpoly(c, pts, CERAMIC, lw=5, seed=4, amp=1.4, sh=(0.18, 0.32))
    candy_shadow(c, cx, bottom + 2, RIM_RX * 0.8, 10)
    # Glanz links
    apoly(c, [(cx - RIM_RX * 0.78, RIM_Y + 40), (cx - RIM_RX * 0.64, RIM_Y + 34), (cx - RIM_RX * 0.56, bottom - 34), (cx - RIM_RX * 0.7, bottom - 40)], (255, 255, 255, 40))
    # Kuerbisgesicht (ausgeschnitten, gluehend)
    fy = RIM_Y + 62
    for ex in (cx - 70, cx + 70):
        c.glow(ex, fy, 30, 24, (255, 170, 60, 110), 10)
        c.d.polygon(c.P([(ex - 22, fy + 12), (ex + 22, fy + 12), (ex, fy - 20)]), fill=ORANGE_L)
    grin = [(cx - 110, fy + 36), (cx - 78, fy + 56), (cx - 46, fy + 36), (cx - 14, fy + 56), (cx + 18, fy + 36), (cx + 50, fy + 56), (cx + 82, fy + 36), (cx + 110, fy + 36), (cx + 90, fy + 76), (cx - 90, fy + 76)]
    c.glow(cx, fy + 55, 110, 24, (255, 170, 60, 100), 12)
    c.d.polygon(c.P(grin), fill=ORANGE_L)
    # vorderer Rand: orange Borte mit Streifen
    rim = ell_pts(cx, RIM_Y, RIM_RX, RIM_RY, n=60, a0=0.0, a1=math.pi)
    HD.ink(c.d, c.P(wob(rim, 5, 1.2, closed=False)), ORANGE, 11 * S, seed=5, var=0.2)
    for k in range(-9, 10, 2):
        a = math.pi / 2 + k * 0.155
        x0, y0 = cx + (RIM_RX - 6) * math.cos(a), RIM_Y + (RIM_RY - 6) * math.sin(a)
        x1, y1 = cx + (RIM_RX + 6) * math.cos(a), RIM_Y + (RIM_RY + 6) * math.sin(a)
        aline(c, [(x0, y0), (x1, y1)], a4(CERAMIC_D, 220), 4)
    HD.ink(c.d, c.P(wob(ell_pts(cx, RIM_Y, RIM_RX + 2, RIM_RY + 3, n=60, a0=0.0, a1=math.pi), 6, 1.2, closed=False)), INK, 4 * S, seed=6, var=0.2)
    aline(c, [(cx - RIM_RX * 0.5, RIM_Y + RIM_RY - 2), (cx - RIM_RX * 0.1, RIM_Y + RIM_RY + 2)], (255, 255, 255, 90), 3)
    V.save(c, "cb_eject_bowl_front.png")


def heap():
    """Der Suessigkeitenhaufen in der Schuessel (Pivot unten Mitte), Kuppe in der Mitte."""
    w, h = 460, 120
    c = C(w, h)
    cx = w / 2
    mound = [(8, h)] + [(cx + (w / 2 - 8) * math.cos(math.pi - math.pi * k / 40), h - 12 - (h - 20) * math.sin(math.pi * k / 40) ** 0.8) for k in range(41)] + [(w - 8, h)]
    hpoly(c, mound, (70, 40, 70, 255), lw=0, seed=7)
    rnd = random.Random(23)
    pieces = []
    for _ in range(70):
        u = rnd.random()
        x = 20 + (w - 40) * u
        top = h - 12 - (h - 20) * math.sin(math.pi * u) ** 0.8
        y = rnd.uniform(top + 6, h - 2)
        pieces.append((y, x, rnd.randint(0, 999)))
    for y, x, seed in sorted(pieces):
        kind = seed % 6
        s = rnd.uniform(0.75, 1.05)
        if kind == 0:
            twist_px(c, x, y, 9 * s, seed=seed, cols=(ORANGE, CERAMIC_D))
        elif kind == 1:
            twist_px(c, x, y, 9 * s, seed=seed, cols=(PURPLE, GREEN))
        elif kind == 2:
            col = rnd.choice(((197, 17, 17, 255), (19, 46, 209, 255), (17, 127, 45, 255), (245, 245, 87, 255), (239, 125, 13, 255), (107, 47, 187, 255), (56, 254, 220, 255), (237, 84, 186, 255)))
            hpoly(c, rr_pts(x - 10 * s, y - 14 * s, x + 10 * s, y + 10 * s, (9 * s, 5 * s)), col, lw=2, seed=seed, sh=(0.14, 0.3))
            hpoly(c, rr_pts(x - 2 * s, y - 10 * s, x + 12 * s, y - 2 * s, 4 * s), (190, 225, 240, 255), lw=2, seed=seed + 1)
        elif kind == 3:
            hell(c, x, y, 11 * s, 11 * s, EYE_W, lw=2, seed=seed, sh=(0.1, 0.3))
            hell(c, x + 2 * s, y, 5 * s, 5 * s, GREEN, lw=2, seed=seed + 1)
            c.ell(x + 2.5 * s, y, 2.2 * s, 2.2 * s, INK, lw=0)
        elif kind == 4:
            for k, (dx, rxx) in enumerate(((0, 11), (-6, 8), (6, 8))):
                hell(c, x + dx * s, y + 2 * s, rxx * s, 9 * s, PUMPKIN, lw=2, seed=seed + k, sh=(0.12, 0.3))
        else:
            hpoly(c, [(x - 8 * s, y + 10 * s), (x + 8 * s, y + 10 * s), (x, y - 14 * s)], (255, 224, 90, 255), lw=2, seed=seed, sh=(0.1, 0.25))
            c.d.polygon(c.P([(x - 4.4 * s, y - 2 * s), (x + 4.4 * s, y - 2 * s), (x, y - 14 * s)]), fill=WHITE)
    V.save(c, "cb_eject_heap.png")


# ------------------------------------------------------------------ Das Monster

BODY_W, BODY_H = 640, 420                 # 6,4 x 4,2 Einheiten, Pivot unten Mitte
EYE_Y, EYE_DX, EYE_RX, EYE_RY = 70, 88, 60, 48
HOLE_CY, HOLE_RX, HOLE_RY = 195, 175, 60


def monster_body():
    c = C(BODY_W, BODY_H)
    cx = BODY_W / 2
    # Rumpf: Ei mit Zotteln, unten breiter
    pts = []
    for k in range(121):
        a = math.tau * k / 120
        rx = 300 * (1 + 0.1 * max(0.0, math.sin(a)))              # unten (sin > 0 in Bildkoordinaten) breiter
        ry = 205
        pts.append((cx + rx * math.cos(a), 215 + ry * math.sin(a)))
    pts = fur_outline(cx, 215, 300, 205, seed=2, n=140, tuft=0.07)
    pts = [(x, min(y, BODY_H - 4)) for x, y in pts]
    fur_fill(c, pts, FUR, FUR_D, FUR_L, seed=2, lw=6, sh=(0.12, 0.3), strands=160, lit=(-0.3, -0.45))
    # Zottelkrone
    rnd = random.Random(4)
    for k in range(9):
        x = cx - 150 + k * 37
        h = rnd.uniform(30, 55)
        hpoly(c, [(x - 14, 44), (x + 14, 44), (x + rnd.uniform(-10, 10), 44 - h)], FUR, lw=5, seed=10 + k, amp=1.5, sh=(0.05, 0.2))
    # Augen (Weiss mit oranger Iris, Pupille separat)
    for sgn in (-1, 1):
        ex = cx + sgn * EYE_DX
        hell(c, ex, EYE_Y, EYE_RX, EYE_RY, EYE_W, lw=6, seed=20 + sgn, sh=(0.08, 0.22))
        hell(c, ex + sgn * 6, EYE_Y + 4, 30, 30, EYE_IRIS, lw=4, seed=22 + sgn, sh=(0.15, 0.3))
        c.ell(ex + sgn * 6, EYE_Y + 4, 32, 32, EYE_IRIS_D, lw=3, outline=EYE_IRIS_D)
    # Nase: dunkler Knubbel zwischen den Augen
    hell(c, cx, EYE_Y + 60, 26, 18, FUR_D, lw=5, seed=25, sh=(0.1, 0.3))
    # Maulhoehle mit Zunge und oberer Zahnreihe
    hole = ell_pts(cx, HOLE_CY, HOLE_RX, HOLE_RY, n=60)
    hpoly(c, hole, MOUTH, lw=6, seed=26, amp=1.2, sh=(0.0, 0.3))
    m, md = c.mask()
    md.polygon(c.P(hole), fill=255)
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse(c.P([(cx - 120, HOLE_CY + 10), (cx + 120, HOLE_CY + 90)]), fill=TONGUE)
    gd.ellipse(c.P([(cx - 70, HOLE_CY + 22), (cx + 20, HOLE_CY + 56)]), fill=a4(TONGUE_L, 160))
    g.putalpha(Image.fromarray(np.minimum(np.asarray(g.split()[3]), np.asarray(m))))
    c.img.alpha_composite(g)
    c.d = ImageDraw.Draw(c.img)
    aline(c, [(cx, HOLE_CY + 28), (cx, HOLE_CY + 80)], a4((160, 40, 80), 150), 3)
    for k in range(-4, 5):
        x = cx + k * 38
        y = HOLE_CY - HOLE_RY * math.sqrt(max(0.0, 1 - (k * 38 / HOLE_RX) ** 2)) + 2
        tooth(c, x, y, 26, 30 if k % 2 else 36, seed=30 + k, up=True)
    V.save(c, "cb_eject_monster_body.png")


def monster_jaw():
    """Unterkiefer: Unterlippe mit Zahnreihe und Fellkinn, Pivot oben Mitte."""
    w, h = 440, 170
    c = C(w, h)
    cx = w / 2
    pts = [(10, 52), (w - 10, 52)] + fur_outline(cx, 64, 215, 104, seed=5, n=60, tuft=0.1, a0=0.05, a1=math.pi - 0.05)[::-1]
    pts = [(x, min(y, h - 4)) for x, y in pts]
    fur_fill(c, pts, FUR, FUR_D, FUR_L, seed=5, lw=6, sh=(0.05, 0.35), strands=50, lit=(-0.3, -0.2))
    hpoly(c, rr_pts(16, 34, w - 16, 70, 14), (150, 60, 110, 255), lw=5, seed=6, sh=(0.15, 0.3))        # Unterlippe
    for k in range(-4, 5):
        tooth(c, cx + k * 44 + 10, 38, 24, 22 if k % 2 else 28, seed=40 + k, up=False)
    V.save(c, "cb_eject_monster_jaw.png")


def monster_paw():
    """Arm mit Pranke, Pivot an der Schulter (unten Mitte), Pranke oben."""
    w, h = 130, 290
    c = C(w, h)
    cx = w / 2
    arm = fur_outline(cx, 170, 42, 120, seed=8, n=70, tuft=0.1)
    fur_fill(c, arm, FUR, FUR_D, FUR_L, seed=8, lw=5, sh=(0.1, 0.3), strands=40, lit=(-0.3, -0.3))
    paw = fur_outline(cx, 52, 56, 46, seed=9, n=60, tuft=0.08)
    fur_fill(c, paw, FUR, FUR_D, FUR_L, seed=9, lw=5, sh=(0.1, 0.3), strands=20, lit=(-0.3, -0.3))
    for k, (dx, dy, r) in enumerate(((-38, 14, 17), (-14, -4, 18), (12, -6, 18), (36, 10, 16))):
        hell(c, cx + dx, 52 + dy - 26, r, r * 1.15, FUR, lw=4, seed=50 + k, sh=(0.12, 0.3))
        c.ell(cx + dx, 52 + dy - 26 - r * 0.2, r * 0.45, r * 0.4, (60, 30, 90, 255), lw=0)         # Ballen
    hell(c, cx, 62, 22, 16, (60, 30, 90, 255), lw=0)
    V.save(c, "cb_eject_monster_paw.png")


def monster_small():
    c = C(44, 44)
    c.ell(22, 22, 19, 19, INK, lw=0)
    c.ell(16, 15, 6, 6, WHITE, lw=0)
    c.ell(27, 28, 2.5, 2.5, (255, 255, 255, 170), lw=0)
    V.save(c, "cb_eject_pupil.png")
    # Augenlid: Fellhalbscheibe (Pivot unten Mitte), deckt das Auge von oben ab
    c = C(140, 70)
    lid = fur_outline(70, 70, 66, 62, seed=12, n=50, tuft=0.06, a0=math.pi, a1=math.tau)
    lid = [(x, min(y, 68)) for x, y in lid]
    fur_fill(c, lid, FUR, FUR_D, FUR_L, seed=12, lw=5, sh=(0.08, 0.3), strands=16, lit=(-0.3, -0.2))
    V.save(c, "cb_eject_lid.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pantry_bg()
    candy_sprites()
    bowl_back()
    bowl_front()
    heap()
    monster_body()
    monster_jaw()
    monster_paw()
    monster_small()


if __name__ == "__main__":
    main()
