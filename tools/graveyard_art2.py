# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_art2.py - Einrichtung von Ravenhollow Cemetery: Kapelle, Sargkammer, Brunnenhaus, Gruft, Leichenhalle.
# Traegt sich ueber graveyard_art.kind() ein (Vertrag und Stil siehe graveyard_art.py).

import math
import random

import graveyard_art as G
from graveyard_art import (BONE, BRASS, BRASS_D, BRASS_L, CREAM, IRON, IRON_D, IRON_L, K, MARBLE, MOSS, OUTLINE, RUST,
                           SANDSTONE, SLATE, GRANITE, VELVET, WOOD, WOOD_D, WOOD_L, OAK, alpha, candle, crack, flame,
                           grass_tufts, hexc, kind, lichen, moss, shade)
import handdraw as HD

OUT_W = G.OUT_W
STONE = shade(GRANITE, 1.05)
STONE_L = shade(STONE, 1.18)
STONE_D = shade(STONE, 0.72)
CLOTH = hexc("#e2dccb")
CLOTH_D = shade(CLOTH, 0.8)
GOLD = hexc("#c8a050")
STEEL = hexc("#9aa2ac")
STEEL_D = shade(STEEL, 0.7)
STEEL_L = hexc("#d0d8e0")
WATER = hexc("#1e2c44")


def planks_front(c, x0, x1, yb, yt, col, n=None, seed=0, vertical=False):
    """Bretterstruktur auf einer Vorderflaeche (nur Fugen und Maserung)."""
    rnd = random.Random(seed)
    if vertical:
        n = n or max(2, int((x1 - x0) / 0.14))
        for k in range(1, n):
            x = x0 + (x1 - x0) * k / n
            c.line([(x, yb + 0.02), (x, yt - 0.02)], fill=alpha(shade(col, 0.6), 220), width=0.012)
    else:
        n = n or max(2, int((yt - yb) / 0.11))
        for k in range(1, n):
            y = yb + (yt - yb) * k / n
            c.line([(x0 + 0.02, y), (x1 - 0.02, y)], fill=alpha(shade(col, 0.6), 220), width=0.012)
    for _ in range(int((x1 - x0) * 3)):
        gx = rnd.uniform(x0 + 0.05, x1 - 0.05)
        gy = rnd.uniform(yb + 0.03, yt - 0.03)
        c.line([(gx, gy), (gx + rnd.uniform(0.06, 0.16), gy + rnd.uniform(-0.01, 0.01))], fill=alpha(shade(col, 0.82), 180), width=0.006)


def book(c, x, y, w=0.18, h=0.12, col=None, open_=False, rnd=None):
    col = col or hexc("#6a2a2a")
    if open_:
        c.poly([(x - w, y), (x, y - 0.015), (x, y + h), (x - w, y + h + 0.01)], fill=hexc("#e8dfc4"), outline=OUTLINE, width=0.012)
        c.poly([(x + w, y), (x, y - 0.015), (x, y + h), (x + w, y + h + 0.01)], fill=hexc("#ded4b8"), outline=OUTLINE, width=0.012)
        for k in range(4):
            yy = y + 0.025 + k * h / 5
            c.line([(x - w + 0.03, yy), (x - 0.03, yy - 0.004)], fill=alpha(hexc("#5a4a3a"), 200), width=0.006)
            c.line([(x + 0.03, yy - 0.004), (x + w - 0.03, yy)], fill=alpha(hexc("#5a4a3a"), 200), width=0.006)
        c.line([(x, y - 0.015), (x, y + h)], fill=shade(col, 0.8), width=0.01)
    else:
        c.rect(x - w / 2, y, x + w / 2, y + h * 0.35, fill=hexc("#e2d8bc"), outline=OUTLINE, width=0.01)
        c.rect(x - w / 2 - 0.01, y + h * 0.35, x + w / 2 + 0.01, y + h * 0.35 + h * 0.6, fill=col, outline=OUTLINE, width=0.012)
        c.line([(x - w / 2 + 0.02, y + h * 0.65), (x + w / 2 - 0.02, y + h * 0.65)], fill=GOLD, width=0.008)


def skull(c, x, y, s=1.0, col=None):
    col = col or BONE
    c.ellipse(x, y + 0.07 * s, 0.075 * s, 0.065 * s, fill=col, outline=OUTLINE, width=0.014 * s)
    c.rect(x - 0.045 * s, y + 0.0, x + 0.045 * s, y + 0.04 * s, fill=col, outline=OUTLINE, width=0.012 * s)
    c.ellipse(x - 0.028 * s, y + 0.065 * s, 0.018 * s, 0.02 * s, fill=hexc("#1c1818"))
    c.ellipse(x + 0.028 * s, y + 0.065 * s, 0.018 * s, 0.02 * s, fill=hexc("#1c1818"))
    c.poly([(x - 0.008 * s, y + 0.04 * s), (x + 0.008 * s, y + 0.04 * s), (x, y + 0.055 * s)], fill=hexc("#2a2424"))
    for k in range(4):
        c.line([(x - 0.03 * s + k * 0.02 * s, y + 0.004), (x - 0.03 * s + k * 0.02 * s, y + 0.03 * s)], fill=alpha(OUTLINE, 200), width=0.006 * s)
    c.ellipse(x - 0.03 * s, y + 0.1 * s, 0.025 * s, 0.015 * s, fill=alpha((255, 255, 255, 255), 90))


def candlestick(c, x, y, h=0.3, lit=True, seed=0):
    c.ellipse(x, y, 0.06, 0.025, fill=BRASS, outline=OUTLINE, width=0.012)
    c.line([(x, y), (x, y + h)], fill=OUTLINE, width=0.035)
    c.line([(x, y), (x, y + h)], fill=BRASS, width=0.02)
    for k in range(2):
        c.ellipse(x, y + h * (0.35 + 0.3 * k), 0.025, 0.012, fill=BRASS_L, outline=OUTLINE, width=0.008)
    c.ellipse(x, y + h, 0.045, 0.018, fill=BRASS, outline=OUTLINE, width=0.01)
    candle(c, x, y + h, 0.14, lit=lit, r=0.022, seed=seed)


# ------------------------------------------------------------------ Kapelle

@kind("altar", 2.3, pad=0.6)
def _altar(p, c, x0, y0, x1, y1, idx, rnd):
    w = x1 - x0
    cx = (x0 + x1) / 2
    H = 1.0
    # Standkreuz hinter dem Altar (dunkles Holz, Korpus nur als Silhouette)
    by = y1 - 0.05
    cy_ = by + 1.0 * K
    for col, wd in ((OUTLINE, 0.14), (OAK, 0.09)):
        c.line([(cx, by), (cx, cy_ + 1.25)], fill=col, width=wd)
        c.line([(cx - 0.42, cy_ + 0.85), (cx + 0.42, cy_ + 0.85)], fill=col, width=wd)
    c.line([(cx - 0.02, by + 0.05), (cx - 0.02, cy_ + 1.2)], fill=shade(OAK, 1.35), width=0.02)
    c.ellipse(cx, cy_ + 0.85, 0.12, 0.12, outline=GOLD, width=0.025)
    # Steinblock mit drei Blendarkaden
    p.box(x0, y0, x1, y1, 0, H, STONE_L, STONE)
    fy = y0 + 0.05
    for k in range(3):
        ax0 = x0 + 0.15 + k * (w - 0.3) / 3 + 0.05
        ax1 = ax0 + (w - 0.3) / 3 - 0.1
        top = fy + 0.42
        acx = (ax0 + ax1) / 2
        arch = [(ax0, fy + 0.06), (ax1, fy + 0.06), (ax1, top - 0.08)] + \
               [(acx + (ax1 - ax0) / 2 * math.cos(t), top - 0.08 + 0.1 * math.sin(t)) for t in [j * math.pi / 8 for j in range(9)]] + [(ax0, top - 0.08)]
        c.poly(arch, fill=STONE_D, outline=OUTLINE, width=0.015)
        c.line([(ax0 + 0.02, fy + 0.08), (ax0 + 0.02, top - 0.1)], fill=alpha(STONE_L, 180), width=0.01)
    # Altartuch: Decke oben, vorne ueberhaengend mit Goldborte und gesticktem Kreuz
    ty = y0 + H * K
    c.poly([(x0 - 0.03, ty + 0.01), (x1 + 0.03, ty + 0.01), (x1 + 0.03, y1 + H * K), (x0 - 0.03, y1 + H * K)], fill=CLOTH, outline=OUTLINE, width=0.03)
    for k in range(9):
        fx = x0 + 0.15 + k * (w - 0.3) / 8
        c.line([(fx, ty + 0.03), (fx + 0.03, y1 + H * K - 0.03)], fill=alpha(CLOTH_D, 150), width=0.008)
    for k in range(int(w / 0.06)):                                                    # Spitzenkante vorn
        lx = x0 + k * 0.06
        c.ellipse(lx + 0.03, ty + 0.0, 0.026, 0.02, fill=CLOTH, outline=alpha(OUTLINE, 200), width=0.006)
    hang = [(x0 + 0.25, ty + 0.02), (x1 - 0.25, ty + 0.02), (x1 - 0.28, ty - 0.3), (cx, ty - 0.34), (x0 + 0.28, ty - 0.3)]
    c.poly(hang, fill=hexc("#7a1e2a"), outline=OUTLINE, width=0.025)
    c.line([(x0 + 0.29, ty - 0.27), (cx, ty - 0.31), (x1 - 0.29, ty - 0.27)], fill=GOLD, width=0.02)
    for k in range(17):                                                               # Fransen
        fx = x0 + 0.3 + k * (w - 0.6) / 16
        c.line([(fx, ty - 0.3 - 0.04 * (1 - abs(fx - cx) / (w / 2))), (fx, ty - 0.36 - 0.04 * (1 - abs(fx - cx) / (w / 2)))], fill=GOLD, width=0.008)
    c.line([(cx, ty - 0.05), (cx, ty - 0.24)], fill=GOLD, width=0.025)
    c.line([(cx - 0.07, ty - 0.11), (cx + 0.07, ty - 0.11)], fill=GOLD, width=0.025)
    # Auf dem Altar: Leuchter, aufgeschlagenes Buch, Kelch, Totenschaedel mit Kerze
    sy = ty + 0.12
    candlestick(c, x0 + 0.3, sy, 0.34, True, seed=1)
    candlestick(c, x1 - 0.3, sy, 0.34, True, seed=2)
    book(c, cx - 0.2, sy - 0.02, 0.17, 0.14, open_=True)
    kx = cx + 0.32                                                                    # Kelch
    c.poly([(kx - 0.05, sy), (kx + 0.05, sy), (kx + 0.015, sy + 0.04), (kx + 0.015, sy + 0.1), (kx + 0.06, sy + 0.14), (kx + 0.06, sy + 0.19),
            (kx - 0.06, sy + 0.19), (kx - 0.06, sy + 0.14), (kx - 0.015, sy + 0.1), (kx - 0.015, sy + 0.04)], fill=GOLD, outline=OUTLINE, width=0.012)
    c.ellipse(kx, sy + 0.19, 0.06, 0.02, fill=hexc("#5a1018"), outline=OUTLINE, width=0.01)
    c.line([(kx - 0.04, sy + 0.15), (kx - 0.04, sy + 0.18)], fill=BRASS_L, width=0.008)
    skull(c, cx + 0.62, sy - 0.01, 1.0)
    candle(c, cx + 0.62, sy + 0.135, 0.08, lit=True, r=0.02, seed=5)
    for k in range(6):                                                                # Wachs am Tuch
        wx = rnd.uniform(x0 + 0.2, x1 - 0.2)
        c.line([(wx, ty + 0.02), (wx, ty - rnd.uniform(0.04, 0.12))], fill=hexc("#efe6cc"), width=0.014)


@kind("kandelaber", 1.8, pad=1.0, variants=("off",))
def _kandelaber(p, c, x0, y0, x1, y1, idx, rnd, variant=None):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for a in (-0.5, 0.5, math.pi / 2 + 0.6):                                          # Dreifuss
        fx, fy = cx + math.sin(a) * 0.2, cy - 0.06 + math.cos(a) * 0.05
        c.line([(cx, cy + 0.12), (fx, fy)], fill=OUTLINE, width=0.05)
        c.line([(cx, cy + 0.12), (fx, fy)], fill=IRON, width=0.028)
        c.ellipse(fx, fy, 0.035, 0.018, fill=IRON, outline=OUTLINE, width=0.01)
    top = cy + 1.45 * K
    c.line([(cx, cy + 0.1), (cx, top)], fill=OUTLINE, width=0.06)
    c.line([(cx, cy + 0.1), (cx, top)], fill=IRON, width=0.035)
    c.line([(cx - 0.01, cy + 0.12), (cx - 0.01, top - 0.02)], fill=IRON_L, width=0.008)
    for k in range(3):                                                                # Knoten
        c.ellipse(cx, cy + 0.2 + k * 0.2, 0.035, 0.022, fill=IRON_L, outline=OUTLINE, width=0.01)
    arms = [(-0.28, 0.1), (-0.15, 0.2), (0.0, 0.3), (0.15, 0.2), (0.28, 0.1)]
    for dx, dy in arms:
        pts = [(cx, top - 0.05), (cx + dx * 0.6, top - 0.05), (cx + dx, top + dy - 0.05)] if dx else [(cx, top), (cx, top + dy)]
        c.line(pts, fill=OUTLINE, width=0.04)
        c.line(pts, fill=IRON, width=0.02)
        c.ellipse(cx + dx, top + dy - 0.05, 0.045, 0.016, fill=IRON_L, outline=OUTLINE, width=0.01)
    off = variant == "off"
    for k, (dx, dy) in enumerate(arms):
        candle(c, cx + dx, top + dy - 0.05, 0.12 + 0.03 * (k % 2), lit=not off and (k + idx) % 4 != 3, r=0.02, seed=idx * 9 + k)
    if not off:
        c.glow(cx, top + 0.25, 0.9, G.WARM, 0.28)


@kind("kirchenbank", 1.05)
def _kirchenbank(p, c, x0, y0, x1, y1, idx, rnd):
    """Kirchenbank (Blick von hinten): Sitz, Ruecklehne an der Suedkante, Wangen mit Knaufen, Gesangbuch."""
    w = x1 - x0
    p.box(x0 + 0.08, y0 + 0.12, x1 - 0.08, y1 - 0.02, 0, 0.45, shade(OAK, 1.15), shade(OAK, 0.85))               # Sitz
    for k in range(3):
        bx = x0 + 0.3 + k * (w - 0.6) / 2
        book(c, bx, y0 + 0.2 + 0.45 * K, 0.14, 0.08, col=hexc("#3a2a48") if k % 2 else hexc("#5a2228"))
    p.box(x0 + 0.05, y0, x1 - 0.05, y0 + 0.12, 0, 0.95, shade(OAK, 1.2), OAK)                                       # Ruecklehne
    fy = y0
    planks_front(c, x0 + 0.05, x1 - 0.05, fy + 0.04, fy + 0.93 * K, OAK, n=4, seed=idx)
    c.rect(x0 + 0.2, fy + 0.18, x1 - 0.2, fy + 0.42, outline=alpha(shade(OAK, 0.6), 230), width=0.012)               # Fuellung
    c.line([(x0 + 0.1, fy + 0.93 * K - 0.03), (x1 - 0.1, fy + 0.93 * K - 0.03)], fill=alpha(shade(OAK, 1.4), 200), width=0.014)
    c.rect(x0 + 0.5, fy + 0.27, x0 + 0.62, fy + 0.33, fill=BRASS, outline=OUTLINE, width=0.008)                       # Namensschild
    for sx in (x0, x1 - 0.1):                                                         # Wangen mit Knauf (Mohnkopf)
        p.box(sx, y0 - 0.02, sx + 0.1, y1, 0, 1.0, shade(OAK, 1.1), shade(OAK, 0.9), w=0.04)
        kx = sx + 0.05
        ky = y0 - 0.02 + 1.0 * K
        c.ellipse(kx, ky + 0.06, 0.06, 0.06, fill=shade(OAK, 1.05), outline=OUTLINE, width=0.025)
        c.ellipse(kx - 0.015, ky + 0.08, 0.02, 0.015, fill=shade(OAK, 1.4))
    if idx % 3 == 0:                                                                  # vergessene Kerze am Boden
        candle(c, x1 - 0.35, y0 - 0.12, 0.08, lit=False, r=0.02, seed=idx)


@kind("taufbecken", 1.2, pad=0.4)
def _taufbecken(p, c, x0, y0, x1, y1, idx, rnd):
    """Taufstein wie ein Kelch: Stufensockel, schlanker Schaft mit Nodus, nach oben weite Schale mit Fries,
    Wasser mit Mondspiegel."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    p.cyl(cx, cy, r * 0.75, 0, 0.08, STONE_L, STONE_D, ry=r * 0.4, w=0.025)
    p.cyl(cx, cy, r * 0.55, 0.08, 0.08, STONE_L, STONE, ry=r * 0.3, w=0.025)
    sb, st = cy + 0.16 * K, cy + 0.62 * K
    c.poly([(cx - r * 0.22, sb), (cx + r * 0.22, sb), (cx + r * 0.16, st), (cx - r * 0.16, st)], fill=STONE, outline=OUTLINE, width=0.025)
    c.line([(cx - r * 0.12, sb + 0.02), (cx - r * 0.09, st - 0.02)], fill=alpha(G.MOON, 120), width=0.014)
    c.ellipse(cx, (sb + st) / 2, r * 0.26, r * 0.08, fill=STONE_L, outline=OUTLINE, width=0.015)                 # Nodus
    bb, bt = cy + 0.6 * K, cy + 0.95 * K                                              # Schale
    ry = r * 0.45
    bowl = [(cx - r * 0.25, bb)] + [(cx - r * (0.25 + 0.75 * t ** 0.7), bb + (bt - bb) * t) for t in (0.25, 0.5, 0.75, 1.0)]
    bowl += [(cx + x_ - cx, y_) for x_, y_ in []]
    right = [(2 * cx - x_, y_) for x_, y_ in reversed(bowl)]
    c.poly(bowl + right + [(cx, bb - r * 0.06)], fill=STONE, outline=OUTLINE, width=0.03)
    for k in range(5):                                                                # Spitzbogenfries
        fx = cx - r * 0.6 + k * r * 0.3
        fy = bb + (bt - bb) * 0.55
        c.line([(fx - 0.035, fy - 0.04), (fx, fy + 0.04), (fx + 0.035, fy - 0.04)], fill=alpha(STONE_D, 230), width=0.012)
    c.line([(cx - r * 0.85, bt - 0.04), (cx - r * 0.5, bb + 0.04)], fill=alpha(G.MOON, 100), width=0.014)
    c.ellipse(cx, bt, r, ry, fill=STONE_L, outline=OUTLINE, width=0.03)
    c.ellipse(cx, bt, r * 0.82, ry * 0.78, fill=WATER, outline=alpha(OUTLINE, 220), width=0.015)
    c.ellipse(cx - r * 0.25, bt + ry * 0.15, r * 0.24, ry * 0.15, fill=alpha(G.MOON, 140))
    c.ellipse(cx + r * 0.3, bt - ry * 0.25, r * 0.07, ry * 0.05, fill=alpha(G.MOON, 100))
    moss(c, cx - r * 0.5, cy - 0.02, 0.06, seed=idx)


@kind("opferkerzen", 1.2, pad=0.7)
def _opferkerzen(p, c, x0, y0, x1, y1, idx, rnd):
    """Eiserner Opferkerzenstaender: drei Stufen mit Sandschalen und vielen Teelichtern."""
    w = x1 - x0
    for k in range(3):
        z = 0.35 + k * 0.22
        yy = y0 + 0.08 + k * 0.14
        p.box(x0 + 0.04 + k * 0.08, yy, x1 - 0.04 - k * 0.08, yy + 0.16, z, 0.05, hexc("#8a7a60"), IRON, w=0.03)
    for sx in (x0 + 0.06, x1 - 0.06):
        c.line([(sx, y0 + 0.05), (sx, y0 + 0.35 * K + 0.1)], fill=OUTLINE, width=0.045)
        c.line([(sx, y0 + 0.05), (sx, y0 + 0.35 * K + 0.1)], fill=IRON, width=0.025)
    for k in range(3):
        z = 0.4 + k * 0.22
        yy = y0 + 0.16 + k * 0.14 + z * K
        n = 7 - k * 2
        for j in range(n):
            lx = x0 + 0.12 + k * 0.08 + j * (w - 0.24 - k * 0.16) / max(1, n - 1)
            lit = rnd.random() < 0.75
            c.ellipse(lx, yy, 0.03, 0.014, fill=hexc("#c8c0b0"), outline=OUTLINE, width=0.008)
            c.rect(lx - 0.022, yy, lx + 0.022, yy + 0.035, fill=CREAM, outline=OUTLINE, width=0.008)
            if lit:
                flame(c, lx, yy + 0.04, 0.6, glow=False)
    c.glow((x0 + x1) / 2, y0 + 0.9 * K + 0.2, 0.9, G.WARM, 0.4)
    c.rect(x0 + 0.3, y0 + 0.1, x0 + 0.5, y0 + 0.22, fill=BRASS, outline=OUTLINE, width=0.01)                       # Opferstock
    c.line([(x0 + 0.36, y0 + 0.2), (x0 + 0.44, y0 + 0.2)], fill=OUTLINE, width=0.01)


# ------------------------------------------------------------------ Sargkammer

def coffin_top(c, x0, x1, yb, d, H, wood, lid=True, seed=0):
    """Sarg in Aufsicht (liegend): sechseckiger Grundriss, Fussende links, Seiten mit Griffen, Deckel."""
    w = x1 - x0
    cy = yb + d / 2
    xs = x0 + w * 0.7
    base = [(x0, cy - d * 0.28), (xs, yb), (x1, cy - d * 0.32), (x1, cy + d * 0.32), (xs, yb + d), (x0, cy + d * 0.28)]
    for a, b in ((base[0], base[1]), (base[1], base[2])):
        c.poly([a, b, (b[0], b[1] + H * K), (a[0], a[1] + H * K)], fill=shade(wood, 0.82), outline=OUTLINE, width=0.04)
        c.line([(a[0] + 0.03, a[1] + H * K - 0.025), (b[0] - 0.03, b[1] + H * K - 0.025)], fill=shade(wood, 1.12), width=0.015)
    for (a, b, t) in ((base[0], base[1], 0.3), (base[0], base[1], 0.75), (base[1], base[2], 0.5)):
        gx, gy = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + H * K * 0.45
        c.rect(gx - 0.06, gy - 0.01, gx + 0.06, gy + 0.012, fill=BRASS_D)
        c.ellipse(gx, gy - 0.012, 0.05, 0.022, outline=BRASS, width=0.012)
    top = [(x, y + H * K) for x, y in base]
    if lid:
        c.poly(top, fill=shade(wood, 1.08), outline=OUTLINE, width=0.04)
        inner = [(x + (sum(q[0] for q in top) / 6 - x) * 0.12, y + (sum(q[1] for q in top) / 6 - y) * 0.2) for x, y in top]
        c.poly(inner, outline=alpha(shade(wood, 0.75), 220), width=0.012)
        mx = top[1][0]
        c.line([(mx - 0.06, cy + H * K), (mx + 0.06, cy + H * K)], fill=BRASS, width=0.02)
        c.line([(mx, cy + H * K - 0.05), (mx, cy + H * K + 0.05)], fill=BRASS, width=0.02)
    return top


@kind("sargstapel", 2.0, pad=0.35)
def _sargstapel(p, c, x0, y0, x1, y1, idx, rnd):
    """Saergestapel an der Westwand: drei liegende Saerge uebereinander, vorn ein Rohling, Seil, Preisschilder."""
    w = x1 - x0
    woods = [lift_wood(k) for k in range(5)]
    layers = 3
    d = (y1 - y0) / 2.2
    for row in range(2):                                                              # zwei Reihen (hinten, vorn)
        yb = y1 - d - row * (d + 0.1)
        for k in range(layers if row == 0 else 2):
            z = k * 0.42
            top = coffin_top(c, x0 + 0.05 + row * 0.08, x1 - 0.05, yb + z * K, d, 0.4, woods[(row * 3 + k + idx) % 5], seed=idx + k)
            if k == (layers - 1 if row == 0 else 1):
                tx, ty = top[1][0] - 0.3, top[1][1] - 0.04
                c.rect(tx, ty - 0.07, tx + 0.12, ty, fill=hexc("#d8ceb0"), outline=OUTLINE, width=0.008)
                c.line([(tx + 0.02, ty - 0.035), (tx + 0.1, ty - 0.035)], fill=hexc("#5a4a3a"), width=0.006)
                c.line([(tx + 0.06, ty), (tx + 0.04, ty + 0.05)], fill=hexc("#a08a60"), width=0.006)
    for k in range(3):                                                                # Seil um den hinteren Stapel
        sx = x0 + 0.4 + k * (w - 0.8) / 2
        c.line([(sx, y1 - d + 0.05), (sx + 0.02, y1 - d + 1.2 * K + 0.05)], fill=hexc("#b0946a"), width=0.022)
        c.line([(sx, y1 - d + 0.05), (sx + 0.02, y1 - d + 1.2 * K + 0.05)], fill=alpha(hexc("#6a5030"), 200), width=0.008)
    G.lichen(c, x0 + 0.1, y0, x1 - 0.1, y0 + 0.2, 0, seed=idx)
    for k in range(2):
        G.crack(c, [(x0 + 0.6 + k, y0 + 0.3), (x0 + 0.7 + k, y0 + 0.5)], seed=idx + k, col=alpha(OUTLINE, 120))
    # Spinnweben in der Ecke
    for k in range(6):
        a = (math.pi / 2) * k / 5
        c.line([(x0 + 0.02, y1 + 1.2 * K), (x0 + 0.02 + 0.35 * math.cos(a), y1 + 1.2 * K - 0.35 * math.sin(a))], fill=alpha((232, 236, 242, 255), 110), width=0.006)


def lift_wood(k):
    return [shade(WOOD, 1.05), shade(OAK, 1.0), hexc("#6a5644"), hexc("#4e4038"), shade(WOOD_L, 0.95)][k % 5]


@kind("hobelbank", 1.0, pad=0.4)
def _hobelbank(p, c, x0, y0, x1, y1, idx, rnd):
    """Hobelbank an der Ostwand (laengs Nord-Sued): Beine, Platte mit Vorderzange, Hobel, Stemmeisen, Spaene,
    halbfertiger Sargdeckel."""
    H = 0.9
    for (lx, ly) in ((x0 + 0.08, y0 + 0.05), (x1 - 0.1, y0 + 0.05), (x0 + 0.08, y1 - 0.15), (x1 - 0.1, y1 - 0.15)):
        p.box(lx, ly, lx + 0.07, ly + 0.07, 0, H - 0.1, shade(OAK, 1.1), shade(OAK, 0.8), w=0.03)
    p.box(x0 + 0.08, y0 + 0.1, x1 - 0.08, y1 - 0.1, 0.25, 0.05, shade(OAK, 0.95), shade(OAK, 0.75), w=0.025)       # Ablage
    p.box(x0, y0, x1, y1, H - 0.1, 0.1, shade(OAK, 1.2), OAK)
    ty = H * K
    c.rect(x0 + 0.05, y0 + ty + 0.15, x1 - 0.05, y0 + ty + 0.95, fill=shade(hexc("#6a5644"), 1.05), outline=OUTLINE, width=0.025)   # Sargdeckel-Rohling
    c.line([(x0 + 0.1, y0 + ty + 0.55), (x1 - 0.1, y0 + ty + 0.55)], fill=alpha(OUTLINE, 120), width=0.008)
    c.rect(x0 + 0.12, y1 + ty - 0.22, x0 + 0.38, y1 + ty - 0.12, fill=hexc("#8a6a44"), outline=OUTLINE, width=0.012)    # Hobel
    c.ellipse(x0 + 0.33, y1 + ty - 0.12, 0.03, 0.03, fill=hexc("#5a3a24"), outline=OUTLINE, width=0.008)
    for k in range(3):                                                                # Stemmeisen
        sx = x1 - 0.2 - k * 0.05
        c.line([(sx, y0 + ty + 0.05), (sx, y0 + ty + 0.13)], fill=hexc("#8a6a44"), width=0.02)
        c.line([(sx, y0 + ty + 0.13), (sx, y0 + ty + 0.2)], fill=STEEL, width=0.012)
    for _ in range(14):                                                               # Spaene
        x, y = rnd.uniform(x0 - 0.2, x1 + 0.1), rnd.uniform(y0 - 0.25, y0 + 0.05)
        a = rnd.uniform(0, 360)
        p.c.d.arc([p.c.p(x - 0.05, y + 0.03), p.c.p(x + 0.05, y - 0.03)], a, a + 220, fill=hexc("#d8b884"), width=p.c.px(0.012))
    c.rect(x0 + 0.02, y0 + 0.02 + ty * 0.3, x0 + 0.14, y0 + 0.02 + ty * 0.8, fill=IRON, outline=OUTLINE, width=0.015)   # Vorderzange


@kind("sarg_stehend", 2.0, pad=0.3)
def _sarg_stehend(p, c, x0, y0, x1, y1, idx, rnd):
    """Zwei Saerge, aufrecht an die Westwand gelehnt (Vorderansicht: Sechseck hochkant)."""
    for k, (fx, wood) in enumerate(((0.0, hexc("#5a4838")), (0.33, shade(OAK, 1.05)))):
        bx0 = x0 + 0.02 + fx * 0.6
        w = 0.42
        yb = y0 + 0.05 + (y1 - y0 - 0.1) * (1 - k) * 0.6
        H = 1.75 * K
        cx = bx0 + w / 2
        pts = [(cx - w * 0.35, yb), (cx + w * 0.35, yb), (cx + w * 0.5, yb + H * 0.72), (cx + w * 0.38, yb + H), (cx - w * 0.38, yb + H), (cx - w * 0.5, yb + H * 0.72)]
        c.poly([(x + 0.05, y + 0.05) for x, y in pts], fill=shade(wood, 0.7), outline=OUTLINE, width=0.035)
        c.poly(pts, fill=wood, outline=OUTLINE, width=0.035)
        inner = [(cx + (x - cx) * 0.82, yb + 0.05 + (y - yb) * 0.94) for x, y in pts]
        c.poly(inner, outline=alpha(shade(wood, 0.65), 220), width=0.012)
        c.line([(cx - w * 0.3, yb + 0.05), (cx - w * 0.42, yb + H * 0.7)], fill=alpha(shade(wood, 1.3), 180), width=0.012)
        c.line([(cx, yb + H * 0.4), (cx, yb + H * 0.85)], fill=BRASS, width=0.02)
        c.line([(cx - 0.07, yb + H * 0.72), (cx + 0.07, yb + H * 0.72)], fill=BRASS, width=0.02)
        if k == 1:                                                                    # Kratzspuren von innen?
            for j in range(3):
                c.line([(cx - 0.06 + j * 0.04, yb + H * 0.3), (cx - 0.04 + j * 0.04, yb + H * 0.18)], fill=alpha(hexc("#2a1a14"), 200), width=0.01)


@kind("bretter", 0.5, pad=0.3)
def _bretter(p, c, x0, y0, x1, y1, idx, rnd):
    """Bretterstapel mit Querhoelzern, Saege obenauf, verstreute Naegel."""
    for k in range(5):
        z = k * 0.07
        off = rnd.uniform(-0.08, 0.08)
        col = shade(lift_wood(k + idx), rnd.uniform(0.95, 1.12))
        p.box(x0 + 0.04 + off, y0 + 0.05, x1 - 0.04 + off, y1 - 0.05, z, 0.06, shade(col, 1.15), col, w=0.025)
        if k in (0, 2):
            for sx in (x0 + 0.25, x1 - 0.3):
                p.box(sx, y0 + 0.02, sx + 0.08, y1 - 0.02, z + 0.06, 0.03, shade(WOOD_D, 1.1), WOOD_D, w=0.02)
    ty = y0 + 0.05 + 0.38 * K
    sx = x0 + 0.5                                                                     # Saege
    c.poly([(sx, ty + 0.1), (sx + 0.55, ty + 0.06), (sx + 0.55, ty + 0.16), (sx, ty + 0.2)], fill=STEEL, outline=OUTLINE, width=0.012)
    for j in range(14):
        tx = sx + j * 0.04
        c.poly([(tx, ty + 0.1 - j * 0.003), (tx + 0.02, ty + 0.08 - j * 0.003), (tx + 0.04, ty + 0.1 - j * 0.003)], fill=STEEL_D)
    c.rect(sx + 0.55, ty + 0.06, sx + 0.7, ty + 0.2, fill=hexc("#8a5a34"), outline=OUTLINE, width=0.012)
    for _ in range(6):
        nx, ny = rnd.uniform(x0, x1), rnd.uniform(y0 - 0.15, y0)
        c.line([(nx, ny), (nx + 0.04, ny + 0.01)], fill=STEEL_D, width=0.008)


@kind("sarg_bock", 1.0, pad=0.45)
def _sarg_bock(p, c, x0, y0, x1, y1, idx, rnd):
    """Offener Sarg auf zwei Boecken, Deckel lehnt daneben, Satinfutter, Kissen, Kratzspuren an der Innenwand."""
    w = x1 - x0
    for bx in (x0 + 0.25, x1 - 0.35):                                                  # Boecke
        for dx in (-0.06, 0.06):
            c.line([(bx + dx, y0 + 0.05), (bx + 0.05 + dx * 0.3, y0 + 0.5 * K)], fill=OUTLINE, width=0.05)
            c.line([(bx + dx, y0 + 0.05), (bx + 0.05 + dx * 0.3, y0 + 0.5 * K)], fill=WOOD, width=0.03)
        c.line([(bx + dx, y1 - 0.1), (bx + 0.05, y1 - 0.1 + 0.5 * K)], fill=OUTLINE, width=0.05)
    wood = hexc("#4e3a2c")
    d = y1 - y0
    cy = y0 + d / 2
    xs = x0 + w * 0.7
    z = 0.5
    H = 0.38
    base = [(x0, cy - d * 0.28), (xs, y0), (x1, cy - d * 0.32), (x1, cy + d * 0.32), (xs, y1), (x0, cy + d * 0.28)]
    base = [(x, y + z * K) for x, y in base]
    top = [(x, y + H * K) for x, y in base]
    c.poly(top, fill=wood, outline=OUTLINE, width=0.04)                                 # Rueckwand-Oberkante
    inner = [(x + (sum(q[0] for q in top) / 6 - x) * 0.1, y + (sum(q[1] for q in top) / 6 - y) * 0.16) for x, y in top]
    c.poly(inner, fill=hexc("#ece4d0"), outline=OUTLINE, width=0.015)                  # Satin
    for k in range(6):
        fx = inner[0][0] + 0.12 + k * (w - 0.3) / 6
        c.line([(fx, inner[1][1] + 0.03), (fx + 0.04, inner[4][1] - 0.03)], fill=alpha(hexc("#c8bca4"), 200), width=0.01)
    c.ellipse(x1 - 0.2, cy + z * K + H * K, 0.12, 0.08, fill=hexc("#f4ecda"), outline=OUTLINE, width=0.012)           # Kissen
    for j in range(4):                                                                # Kratzspuren im Satin
        c.line([(x0 + 0.5 + j * 0.05, cy + z * K + H * K + 0.08), (x0 + 0.56 + j * 0.05, cy + z * K + H * K - 0.02)], fill=hexc("#7a1a22"), width=0.008)
    for a, b in ((base[0], base[1]), (base[1], base[2])):
        c.poly([a, b, (b[0], b[1] + H * K), (a[0], a[1] + H * K)], fill=shade(wood, 0.85), outline=OUTLINE, width=0.04)
    lx = x1 + 0.02                                                                    # Deckel lehnt am Bock
    c.poly([(lx, y0 + 0.02), (lx + 0.22, y0 + 0.05), (lx + 0.18, y0 + 1.1 * K), (lx - 0.04, y0 + 1.05 * K)], fill=shade(wood, 1.1), outline=OUTLINE, width=0.035)
    c.line([(lx + 0.08, y0 + 0.25), (lx + 0.07, y0 + 0.5)], fill=BRASS, width=0.02)


# ------------------------------------------------------------------ Brunnenhaus

@kind("brunnen", 2.6, pad=0.45)
def _brunnen(p, c, x0, y0, x1, y1, idx, rnd):
    """Ziehbrunnen: runde Bruchsteinmauer mit Abdeckrand, schwarzer Schacht mit Wasserspiegel, Dach auf zwei Pfosten,
    Seilwalze mit Kurbel, Eimer, Moos."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    ry = r * 0.55
    H = 0.75
    yb, yt = cy, cy + H * K
    for sx in (-1, 1):                                                                # Pfosten (stehen auf der Mauer, hinten)
        c.rect(cx + sx * (r - 0.06) - 0.05, yt + ry * 0.3, cx + sx * (r - 0.06) + 0.05, cy + 2.05 * K, fill=OAK, outline=OUTLINE, width=0.03)
        c.line([(cx + sx * (r - 0.06) - 0.025, yt + ry * 0.3), (cx + sx * (r - 0.06) - 0.025, cy + 2.0 * K)], fill=alpha(shade(OAK, 1.35), 200), width=0.012)
    c.ellipse(cx, yb, r, ry, fill=STONE, outline=OUTLINE, width=OUT_W)               # Mauerkoerper
    c.rect(cx - r, yb, cx + r, yt, fill=STONE)
    c.line([(cx - r, yb), (cx - r, yt)], fill=OUTLINE, width=OUT_W)
    c.line([(cx + r, yb), (cx + r, yt)], fill=OUTLINE, width=OUT_W)
    rows = 3
    for row in range(rows):                                                           # Bruchsteine, im Verband, der Rundung folgend
        z0 = row / rows
        for k in range(7):
            a0 = math.pi + (k + (0.5 if row % 2 else 0)) * math.pi / 7
            a1 = a0 + math.pi / 7
            if a1 > 2 * math.pi + 1e-6:
                a1 = 2 * math.pi
            pts = []
            for a in (a0, a1):
                pts.append((cx + r * math.cos(a), yb + ry * math.sin(a) + z0 * H * K))
            pts += [(x, y + H * K / rows) for x, y in reversed(pts)]
            col = shade(STONE, rnd.uniform(0.9, 1.1))
            q = [(x + (cx - x) * 0.0, y) for x, y in pts]
            c.poly(q, fill=col, outline=alpha(STONE_D, 255), width=0.014)
    c.ellipse(cx, yt, r * 1.03, ry * 1.03, fill=STONE_L, outline=OUTLINE, width=OUT_W)   # Abdeckrand
    c.ellipse(cx, yt, r * 0.74, ry * 0.7, fill=hexc("#07090e"), outline=OUTLINE, width=0.03)
    c.ellipse(cx + 0.03, yt - ry * 0.25, r * 0.42, ry * 0.2, fill=WATER)
    c.ellipse(cx - 0.06, yt - ry * 0.22, r * 0.14, ry * 0.05, fill=alpha(G.MOON, 120))
    for k in range(10):                                                               # Fugen im Rand
        a = k / 10 * math.tau
        c.line([(cx + r * 0.76 * math.cos(a), yt + ry * 0.72 * math.sin(a)), (cx + r * 1.0 * math.cos(a), yt + ry * 1.0 * math.sin(a))], fill=alpha(STONE_D, 230), width=0.012)
    c.line([(cx - r * 0.9, yt + ry * 0.35), (cx - r * 0.5, yt + ry * 0.75)], fill=alpha(G.MOON, 110), width=0.016)
    moss(c, cx - r * 0.6, yb - ry * 0.4, 0.1, seed=idx)
    moss(c, cx + r * 0.5, yb - ry * 0.2, 0.08, seed=idx + 1)
    moss(c, cx + r * 0.6, yt + ry * 0.3, 0.07, seed=idx + 3)
    wy = cy + 1.6 * K                                                                 # Walze mit Seil und Kurbel
    c.rect(cx - r + 0.08, wy - 0.05, cx + r - 0.08, wy + 0.05, fill=OAK, outline=OUTLINE, width=0.025)
    for k in range(7):
        c.line([(cx - 0.24 + k * 0.07, wy - 0.05), (cx - 0.21 + k * 0.07, wy + 0.05)], fill=hexc("#b0946a"), width=0.022)
    for col_, wd in ((OUTLINE, 0.04), (IRON, 0.02)):
        c.line([(cx + r - 0.08, wy), (cx + r + 0.12, wy), (cx + r + 0.12, wy - 0.16), (cx + r + 0.22, wy - 0.16)], fill=col_, width=wd)
    c.line([(cx, wy - 0.05), (cx, yt + 0.05)], fill=hexc("#b0946a"), width=0.016)
    c.poly([(cx - 0.1, yt + 0.2), (cx + 0.1, yt + 0.2), (cx + 0.08, yt + 0.03), (cx - 0.08, yt + 0.03)], fill=OAK, outline=OUTLINE, width=0.025)
    c.line([(cx - 0.1, yt + 0.16), (cx + 0.1, yt + 0.16)], fill=IRON, width=0.012)
    c.line([(cx - 0.09, yt + 0.07), (cx + 0.09, yt + 0.07)], fill=IRON, width=0.012)
    c.line([(cx - 0.1, yt + 0.2), (cx, yt + 0.28), (cx + 0.1, yt + 0.2)], fill=IRON, width=0.01)
    ry_ = cy + 2.05 * K                                                               # Satteldach mit Schindeln
    roof = [(cx - r - 0.22, ry_), (cx + r + 0.22, ry_), (cx + r * 0.12, ry_ + 0.6), (cx - r * 0.12, ry_ + 0.6)]
    c.poly(roof, fill=hexc("#4a4048"), outline=OUTLINE, width=OUT_W)
    for k in range(5):
        yy = ry_ + 0.06 + k * 0.11
        t = (yy - ry_) / 0.6
        xa = cx - r - 0.22 + (r * 0.88 + 0.22) * t
        xb = cx + r + 0.22 - (r * 0.88 + 0.22) * t
        c.line([(xa + 0.02, yy), (xb - 0.02, yy)], fill=alpha(OUTLINE, 160), width=0.012)
        for j in range(int((xb - xa) / 0.11)):
            sx = xa + 0.05 + j * 0.11 + (k % 2) * 0.055
            c.line([(sx, yy), (sx, yy - 0.09)], fill=alpha(OUTLINE, 110), width=0.008)
    c.line([(cx - r - 0.2, ry_ + 0.02), (cx + r + 0.2, ry_ + 0.02)], fill=alpha(G.MOON, 130), width=0.02)
    c.line([(cx - r * 0.12, ry_ + 0.6), (cx + r * 0.12, ry_ + 0.6)], fill=OUTLINE, width=0.05)
    moss(c, cx - r * 0.5, ry_ + 0.3, 0.09, seed=idx + 2)



@kind("trog", 0.7, pad=0.3)
def _trog(p, c, x0, y0, x1, y1, idx, rnd):
    p.box(x0, y0, x1, y1, 0, 0.55, STONE_L, STONE)
    ty = 0.55 * K
    c.rect(x0 + 0.08, y0 + ty + 0.06, x1 - 0.08, y1 + ty - 0.06, fill=WATER, outline=OUTLINE, width=0.02)
    c.line([(x0 + 0.15, y1 + ty - 0.12), (x0 + 0.45, y1 + ty - 0.12)], fill=alpha(G.MOON, 130), width=0.018)
    for k in range(3):
        c.ellipse(x0 + 0.5 + k * 0.2, y0 + ty + 0.2, 0.04, 0.02, fill=alpha(hexc("#4a7a50"), 200))                 # Algen
    moss(c, x0 + 0.2, y0 + 0.05, 0.1, seed=idx)
    G.crack(c, [(x1 - 0.3, y0 + 0.05), (x1 - 0.26, y0 + 0.2), (x1 - 0.32, y0 + 0.3)], seed=idx)


@kind("fass", 1.0, pad=0.3)
def _fass(p, c, x0, y0, x1, y1, idx, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    H = 0.9
    wood = shade(OAK, 0.95 + 0.1 * (idx % 2))
    c.ellipse(cx, cy, r, r * 0.5, fill=shade(wood, 0.8), outline=OUTLINE, width=OUT_W)
    c.rect(cx - r, cy, cx + r, cy + H * K, fill=wood)
    c.poly([(cx - r, cy), (cx - r * 1.08, cy + H * K * 0.5), (cx - r, cy + H * K)], fill=wood, outline=OUTLINE, width=OUT_W)
    c.poly([(cx + r, cy), (cx + r * 1.08, cy + H * K * 0.5), (cx + r, cy + H * K)], fill=wood, outline=OUTLINE, width=OUT_W)
    for k in range(5):                                                                # Dauben
        a = math.pi + (k + 1) * math.pi / 6
        sx = cx + r * math.cos(a) * 1.02
        c.line([(sx, cy + 0.02), (sx * 1.0 + (sx - cx) * 0.06, cy + H * K * 0.5), (sx, cy + H * K - 0.02)], fill=alpha(shade(wood, 0.6), 220), width=0.01)
    for t in (0.18, 0.82):                                                            # Reifen
        yy = cy + H * K * t
        c.ellipse(cx, yy - r * 0.5 * 0.9 + r * 0.5 * 0.9, r * 1.05, r * 0.15, outline=None)
        c.line([(cx - r * 1.04, yy), (cx + r * 1.04, yy)], fill=OUTLINE, width=0.045)
        c.line([(cx - r * 1.04, yy), (cx + r * 1.04, yy)], fill=IRON, width=0.025)
    c.ellipse(cx, cy + H * K, r, r * 0.5, fill=shade(wood, 1.15), outline=OUTLINE, width=OUT_W)
    for k in range(3):
        c.line([(cx - r * 0.8, cy + H * K - r * 0.25 + k * r * 0.25), (cx + r * 0.8, cy + H * K - r * 0.25 + k * r * 0.25)], fill=alpha(shade(wood, 0.75), 200), width=0.008)
    c.line([(cx - r + 0.04, cy + 0.05), (cx - r + 0.04, cy + H * K - 0.05)], fill=alpha(shade(wood, 1.3), 180), width=0.014)


# ------------------------------------------------------------------ Gruft

@kind("sarkophag", 1.1, pad=0.5)
def _sarkophag(p, c, x0, y0, x1, y1, idx, rnd):
    """Steinsarkophag mit liegender Grabfigur (Ritter oder Dame) im Relief, Arkadenfries, Kerzen an den Ecken."""
    w = x1 - x0
    col = shade(SANDSTONE, 1.12) if idx % 2 else shade(STONE, 1.08)
    p.box(x0 - 0.05, y0 - 0.05, x1 + 0.05, y1 + 0.05, 0, 0.12, shade(col, 1.05), shade(col, 0.8))
    p.box(x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05, 0.12, 0.55, shade(col, 1.1), col)
    fy = y0 + 0.05 + 0.12 * K
    n = 5
    for k in range(n):                                                                # Arkaden mit Nischenfiguren
        ax0 = x0 + 0.12 + k * (w - 0.24) / n + 0.03
        ax1 = ax0 + (w - 0.24) / n - 0.06
        acx = (ax0 + ax1) / 2
        top = fy + 0.25
        pts = [(ax0, fy + 0.03), (ax1, fy + 0.03), (ax1, top - 0.05)] + [(acx + (ax1 - ax0) / 2 * math.cos(t), top - 0.05 + 0.06 * math.sin(t)) for t in [j * math.pi / 6 for j in range(7)]] + [(ax0, top - 0.05)]
        c.poly(pts, fill=shade(col, 0.66), outline=alpha(OUTLINE, 220), width=0.012)
        c.ellipse(acx, fy + 0.17, 0.022, 0.024, fill=shade(col, 0.95))
        c.poly([(acx - 0.03, fy + 0.04), (acx + 0.03, fy + 0.04), (acx + 0.018, fy + 0.15), (acx - 0.018, fy + 0.15)], fill=shade(col, 0.92))
    lz = 0.67
    p.box(x0, y0, x1, y1, lz, 0.1, shade(col, 1.1), shade(col, 0.92))
    top0, top1 = y0 + (lz + 0.1) * K, y1 + (lz + 0.1) * K
    my = (top0 + top1) / 2
    c.rect(x0 + 0.06, top0 + 0.05, x1 - 0.06, top1 - 0.05, outline=alpha(shade(col, 0.75), 220), width=0.012)
    hx = x1 - 0.3                                                                     # Kopfende rechts
    def relief(pts, f=1.0):
        c.poly([(x + 0.02, y - 0.025) for x, y in pts], fill=shade(col, 0.62))
        c.poly(pts, fill=shade(col, f), outline=OUTLINE, width=0.022)
    relief([(hx - 0.08, my - 0.16), (hx + 0.22, my - 0.16), (hx + 0.22, my + 0.16), (hx - 0.08, my + 0.16)], 1.02)       # Kissen
    c.ellipse(hx - 0.05, my - 0.15, 0.03, 0.025, fill=shade(col, 0.9), outline=alpha(OUTLINE, 200), width=0.008)
    c.ellipse(hx - 0.05, my + 0.15, 0.03, 0.025, fill=shade(col, 0.9), outline=alpha(OUTLINE, 200), width=0.008)
    robe = [(x0 + 0.28, my - 0.12), (hx - 0.32, my - 0.2), (hx - 0.12, my - 0.17), (hx - 0.05, my - 0.1), (hx - 0.05, my + 0.1),
            (hx - 0.12, my + 0.17), (hx - 0.32, my + 0.2), (x0 + 0.28, my + 0.12)]
    relief(robe, 1.08)
    for k in range(6):                                                                # Faltenwurf zum Fussende
        fx = x0 + 0.32 + k * 0.13
        c.line([(fx, my - 0.11 - k * 0.012), (fx + 0.1, my - 0.02), (fx, my + 0.11 + k * 0.012)], fill=alpha(shade(col, 0.72), 220), width=0.01)
    relief(G.HD.wobble_ellipse(hx + 0.07, my, 0.1, 0.1, amp=0.004, seed=idx), 1.12)                                   # Kopf
    c.line([(hx + 0.1, my - 0.035), (hx + 0.1, my - 0.005)], fill=alpha(OUTLINE, 200), width=0.008)                    # geschlossene Augen
    c.line([(hx + 0.1, my + 0.005), (hx + 0.1, my + 0.035)], fill=alpha(OUTLINE, 200), width=0.008)
    c.line([(hx + 0.15, my - 0.01), (hx + 0.15, my + 0.01)], fill=alpha(OUTLINE, 160), width=0.008)
    if idx % 2 == 0:                                                                  # Ritter: Kettenhaube, Schwert laengs
        c.line([(hx + 0.0, my - 0.09), (hx + 0.0, my + 0.09)], fill=alpha(OUTLINE, 220), width=0.012)
        for k in range(4):
            c.ellipse(hx - 0.02, my - 0.07 + k * 0.045, 0.012, 0.012, outline=alpha(shade(col, 0.6), 230), width=0.006)
        c.line([(x0 + 0.32, my), (hx - 0.3, my)], fill=OUTLINE, width=0.04)
        c.line([(x0 + 0.32, my), (hx - 0.3, my)], fill=shade(col, 0.9), width=0.022)
        c.line([(hx - 0.32, my - 0.09), (hx - 0.32, my + 0.09)], fill=OUTLINE, width=0.035)
        c.line([(hx - 0.32, my - 0.09), (hx - 0.32, my + 0.09)], fill=shade(col, 0.9), width=0.018)
    else:                                                                             # Dame: Haar, Schleier, Rose
        relief([(hx + 0.13, my - 0.12), (hx + 0.2, my - 0.1), (hx + 0.2, my + 0.1), (hx + 0.13, my + 0.12)], 0.95)
        c.ellipse(hx - 0.28, my + 0.06, 0.035, 0.032, fill=hexc("#8a2a34"), outline=OUTLINE, width=0.008)
        c.line([(hx - 0.28, my + 0.03), (hx - 0.36, my - 0.06)], fill=hexc("#3a5a3a"), width=0.01)
    relief([(hx - 0.24, my - 0.06), (hx - 0.1, my - 0.03), (hx - 0.1, my + 0.03), (hx - 0.24, my + 0.06), (hx - 0.28, my)], 1.18)   # betende Haende
    c.line([(hx - 0.27, my), (hx - 0.11, my)], fill=alpha(OUTLINE, 180), width=0.006)
    relief(G.HD.wobble_ellipse(x0 + 0.2, my, 0.1, 0.12, amp=0.006, seed=idx + 5), 0.98)                                 # Hund zu Fuessen
    c.ellipse(x0 + 0.13, my + 0.07, 0.04, 0.03, fill=shade(col, 1.0), outline=OUTLINE, width=0.01)
    c.ellipse(x0 + 0.14, my + 0.08, 0.008, 0.008, fill=OUTLINE)
    lichen(c, x0 + 0.1, y0, x1 - 0.1, top0 - 0.02, 10, seed=idx)
    G.crack(c, [(x0 + w * 0.65, y0 + 0.02), (x0 + w * 0.6, y0 + 0.2), (x0 + w * 0.66, y0 + 0.35)], seed=idx)
    G.crack(c, [(x0 + 0.4, top1 - 0.05), (x0 + 0.5, my + 0.1)], seed=idx + 3)
    for (kx, ky) in ((x0 + 0.02, y0 - 0.12), (x1 - 0.02, y0 - 0.12)):
        for j in range(3):
            c.ellipse(kx + (j - 1) * 0.04, ky - 0.01, 0.035, 0.012, fill=hexc("#eae0c6"))
        candle(c, kx, ky, 0.18 + 0.05 * (idx % 2), lit=True, r=0.03, seed=idx + int(abs(kx) * 10))



@kind("saeule", 3.0, pad=0.5)
def _saeule(p, c, x0, y0, x1, y1, idx, rnd):
    """Saeule der Gruft, neu 24.10.: Plinthe und Basis mit Wulsten, kannelierter Schaft mit Lichtkante, korinthisches
    Kapitell mit Akanthusblaettern und Voluten, darauf eine Urne mit Tuch, Efeu am Schaft, Risse und Flechten."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    m, m_l, m_d = MARBLE, shade(MARBLE, 1.06), shade(MARBLE, 0.74)
    p.box(cx - r - 0.1, cy - r * 0.6 - 0.06, cx + r + 0.1, cy + r * 0.6 + 0.06, 0, 0.12, m_l, shade(m, 0.84))
    p.cyl(cx, cy, r + 0.02, 0.12, 0.07, m_l, m_d, ry=(r + 0.02) * 0.5)                                 # Basiswulst
    p.cyl(cx, cy, r * 0.9, 0.19, 0.05, m_l, m_d, ry=r * 0.45)
    H = 2.1
    yb = cy + 0.24 * K
    yt = yb + H * K
    c.rect(cx - r * 0.82, yb, cx + r * 0.82, yt, fill=m, outline=OUTLINE, width=OUT_W)
    for k in range(6):                                                                # Kanneluren
        x = cx - r * 0.62 + k * r * 0.25
        c.line([(x, yb + 0.04), (x, yt - 0.04)], fill=alpha(m_d, 200), width=0.012)
        c.line([(x + 0.012, yb + 0.04), (x + 0.012, yt - 0.04)], fill=alpha((255, 255, 255, 255), 90), width=0.006)
    c.line([(cx - r * 0.74, yb + 0.04), (cx - r * 0.74, yt - 0.04)], fill=alpha((255, 255, 255, 255), 140), width=0.022)
    c.rect(cx + r * 0.5, yb + 0.02, cx + r * 0.82, yt - 0.02, fill=alpha(m_d, 90))                   # Schattenseite
    # Kapitell: Hals, zwei Reihen Akanthus, Voluten, Deckplatte
    c.rect(cx - r * 0.86, yt, cx + r * 0.86, yt + 0.05, fill=m_d, outline=OUTLINE, width=0.02)
    for row, (n, hgt) in enumerate(((5, 0.14), (4, 0.16))):
        for k in range(n):
            lx = cx - r * 0.8 + (k + 0.5) * (r * 1.6) / n
            ly = yt + 0.04 + row * 0.1
            c.poly([(lx - 0.055, ly), (lx + 0.055, ly), (lx + 0.045, ly + hgt * 0.7), (lx, ly + hgt), (lx - 0.045, ly + hgt * 0.7)],
                   fill=m_l if (k + row) % 2 else m, outline=OUTLINE, width=0.012)
            c.line([(lx, ly + 0.02), (lx, ly + hgt - 0.03)], fill=alpha(m_d, 160), width=0.008)
    for sx in (-1, 1):                                                                # Voluten
        vx, vy = cx + sx * r * 0.95, yt + 0.3
        c.ellipse(vx, vy, 0.07, 0.065, fill=m_l, outline=OUTLINE, width=0.02)
        c.ellipse(vx - sx * 0.01, vy + 0.005, 0.035, 0.03, outline=m_d, width=0.012)
        c.ellipse(vx - sx * 0.01, vy + 0.005, 0.012, 0.012, fill=m_d)
    c.poly([(cx - r * 1.25, yt + 0.34), (cx + r * 1.25, yt + 0.34), (cx + r * 1.1, yt + 0.46), (cx - r * 1.1, yt + 0.46)], fill=m_l, outline=OUTLINE, width=0.03)
    c.line([(cx - r * 1.0, yt + 0.44), (cx + r * 1.0, yt + 0.44)], fill=alpha((255, 255, 255, 255), 110), width=0.012)
    # Urne mit Tuch auf der Saeule
    uy = yt + 0.46
    c.rect(cx - 0.08, uy, cx + 0.08, uy + 0.05, fill=m_d, outline=OUTLINE, width=0.015)
    c.poly([(cx - 0.07, uy + 0.05), (cx + 0.07, uy + 0.05), (cx + 0.15, uy + 0.2), (cx + 0.13, uy + 0.36), (cx - 0.13, uy + 0.36), (cx - 0.15, uy + 0.2)],
           fill=m, outline=OUTLINE, width=0.02)
    c.ellipse(cx, uy + 0.4, 0.1, 0.04, fill=m_l, outline=OUTLINE, width=0.015)
    c.poly([(cx - 0.12, uy + 0.4), (cx + 0.1, uy + 0.42), (cx + 0.2, uy + 0.2), (cx + 0.14, uy + 0.12), (cx + 0.06, uy + 0.3), (cx - 0.1, uy + 0.3)],
           fill=CLOTH, outline=OUTLINE, width=0.014)                                     # Tuch haengt ueber
    c.line([(cx + 0.1, uy + 0.36), (cx + 0.16, uy + 0.18)], fill=alpha(CLOTH_D, 200), width=0.01)
    c.line([(cx - 0.1, uy + 0.1), (cx - 0.08, uy + 0.3)], fill=alpha((255, 255, 255, 255), 110), width=0.012)
    for sx in (-1, 1):
        c.line([(cx + sx * 0.14, uy + 0.3), (cx + sx * 0.22, uy + 0.24), (cx + sx * 0.15, uy + 0.14)], fill=OUTLINE, width=0.04)
        c.line([(cx + sx * 0.14, uy + 0.3), (cx + sx * 0.22, uy + 0.24), (cx + sx * 0.15, uy + 0.14)], fill=m, width=0.02)
    # Efeu, Risse, Flechten
    vine = HD.wobble([(cx - r * 0.7, yb), (cx + r * 0.5, yb + 0.4), (cx - r * 0.4, yb + 0.85), (cx + r * 0.3, yb + 1.2)], amp=0.03, seed=idx, step=0.05)
    c.line(vine, fill=hexc("#2e4a30"), width=0.016)
    for k, (lx, ly) in enumerate(vine[::2]):
        c.poly([(lx, ly + 0.035), (lx + 0.035, ly), (lx, ly - 0.035), (lx - 0.035, ly)], fill=hexc("#4e7c50") if k % 2 else hexc("#3e6a48"), outline=alpha(OUTLINE, 200), width=0.006)
    G.crack(c, [(cx + r * 0.3, yt - 0.1), (cx + r * 0.1, yt - 0.4), (cx + r * 0.35, yt - 0.7)], seed=idx)
    G.lichen(c, cx - r * 0.6, yb, cx + r * 0.6, yb + 1.0, 8, seed=idx)
    G.moss(c, cx - r * 0.5, cy - r * 0.5, 0.08, seed=idx)


@kind("urne", 1.3, pad=0.35)
def _urne(p, c, x0, y0, x1, y1, idx, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    p.box(cx - r, cy - r * 0.6, cx + r, cy + r * 0.6, 0, 0.7, shade(MARBLE, 1.05), shade(MARBLE, 0.85))
    by = cy - r * 0.6 + 0.7 * K + 0.1
    c.ellipse(cx, by, 0.08, 0.03, fill=BRASS_D, outline=OUTLINE, width=0.012)
    c.poly([(cx - 0.05, by), (cx + 0.05, by), (cx + 0.14, by + 0.15), (cx + 0.1, by + 0.3), (cx - 0.1, by + 0.3), (cx - 0.14, by + 0.15)],
           fill=BRASS, outline=OUTLINE, width=0.02)
    c.line([(cx - 0.11, by + 0.15), (cx + 0.11, by + 0.15)], fill=BRASS_D, width=0.015)
    c.line([(cx - 0.09, by + 0.08), (cx - 0.09, by + 0.26)], fill=alpha(BRASS_L, 200), width=0.012)
    c.rect(cx - 0.08, by + 0.3, cx + 0.08, by + 0.36, fill=BRASS_D, outline=OUTLINE, width=0.012)
    c.ellipse(cx, by + 0.4, 0.03, 0.03, fill=BRASS, outline=OUTLINE, width=0.01)
    G.bouquet(c, cx - r * 0.6, cy - r * 0.6 + 0.7 * K, rnd, dead=True, s=0.8)


# ------------------------------------------------------------------ Leichenhalle

@kind("obduktionstisch", 1.0, pad=0.4)
def _obduktionstisch(p, c, x0, y0, x1, y1, idx, rnd):
    w = x1 - x0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for lx in (x0 + 0.25, x1 - 0.3):                                                   # Fuss
        c.rect(lx, y0 + 0.15, lx + 0.06, y0 + 0.15 + 0.75 * K, fill=STEEL_D, outline=OUTLINE, width=0.02)
    p.box(x0, y0, x1, y1, 0.75, 0.08, STEEL_L, STEEL)
    ty = y0 + 0.83 * K
    c.rect(x0 + 0.05, ty + 0.04, x1 - 0.05, y1 + 0.83 * K - 0.04, fill=shade(STEEL, 1.15), outline=alpha(OUTLINE, 200), width=0.012)
    c.ellipse(x1 - 0.12, cy + 0.83 * K, 0.035, 0.03, fill=hexc("#2a2e34"))           # Ablauf
    if idx % 2 == 0:                                                                  # Koerper unter dem Laken
        sheet = [(x0 + 0.15, ty + 0.08), (x1 - 0.2, ty + 0.06), (x1 - 0.12, ty + 0.2), (x1 - 0.15, ty + 0.45), (x1 - 0.3, ty + 0.5),
                 (x0 + 0.6, ty + 0.48), (x0 + 0.35, ty + 0.5), (x0 + 0.15, ty + 0.42), (x0 + 0.08, ty + 0.25)]
        c.poly([(x, y + 0.04) for x, y in sheet], fill=CLOTH_D, outline=OUTLINE, width=0.025)
        c.poly(sheet, fill=CLOTH, outline=OUTLINE, width=0.025)
        c.ellipse(x1 - 0.32, ty + 0.3, 0.13, 0.12, fill=shade(CLOTH, 1.05), outline=alpha(OUTLINE, 200), width=0.012)   # Kopf
        c.ellipse(x0 + 0.62, ty + 0.3, 0.12, 0.1, fill=shade(CLOTH, 1.03))                                          # Knie
        for k in range(5):
            fx = x0 + 0.5 + k * 0.17
            c.line([(fx, ty + 0.1), (fx + 0.05, ty + 0.45)], fill=alpha(CLOTH_D, 210), width=0.01)
        for j, dy in enumerate((0.16, 0.32)):                                         # Fuesse mit Zehenzettel
            c.ellipse(x0 + 0.07, ty + dy, 0.05, 0.045, fill=hexc("#b8c0b0"), outline=OUTLINE, width=0.012)
        c.line([(x0 + 0.04, ty + 0.16), (x0 - 0.02, ty + 0.08)], fill=hexc("#c8b080"), width=0.006)
        c.rect(x0 - 0.08, ty + 0.0, x0 + 0.02, ty + 0.07, fill=hexc("#e8dcb0"), outline=OUTLINE, width=0.008)
        c.ellipse(x1 - 0.25, ty + 0.12, 0.05, 0.03, fill=alpha(hexc("#7a1a24"), 200))                                # Fleck
    else:                                                                             # leer: Knochensaege, Schalen
        c.line([(x0 + 0.3, ty + 0.2), (x0 + 0.75, ty + 0.25)], fill=STEEL_L, width=0.03)
        c.rect(x0 + 0.75, ty + 0.2, x0 + 0.9, ty + 0.3, fill=hexc("#3a3a40"), outline=OUTLINE, width=0.01)
        for k in range(3):
            c.ellipse(x1 - 0.6 + k * 0.17, ty + 0.3, 0.07, 0.04, fill=STEEL_L, outline=OUTLINE, width=0.01)
        c.ellipse(x1 - 0.43, ty + 0.3, 0.04, 0.02, fill=hexc("#7a1a24"))
    for k in range(4):                                                                # Instrumente auf dem Rand
        c.line([(x0 + 0.1 + k * 0.06, y0 + 0.83 * K + 0.02), (x0 + 0.12 + k * 0.06, y0 + 0.83 * K + 0.1)], fill=STEEL_L, width=0.01)


@kind("instrumentenschrank", 2.0, pad=0.3)
def _instrumentenschrank(p, c, x0, y0, x1, y1, idx, rnd):
    w = x1 - x0
    H = 1.9
    p.box(x0, y0, x1, y1, 0, H, hexc("#d8dcd8"), hexc("#c0c6c2"))
    fy = y0
    gx0, gx1 = x0 + 0.08, x1 - 0.08
    c.rect(gx0, fy + 0.5, gx1, fy + H * K - 0.08, fill=hexc("#2a3238"), outline=OUTLINE, width=0.02)
    for s in range(3):                                                                # Regalboeden mit Glaesern
        sy = fy + 0.5 + s * (H * K - 0.58) / 3
        c.line([(gx0, sy + 0.01), (gx1, sy + 0.01)], fill=hexc("#8a9298"), width=0.012)
        for k in range(int(w / 0.16)):
            jx = gx0 + 0.08 + k * 0.16
            hh = rnd.uniform(0.12, 0.2)
            liquid = rnd.choice([hexc("#9ab060"), hexc("#c8a060"), hexc("#a8c0b8"), hexc("#b07068")])
            c.rect(jx - 0.05, sy + 0.02, jx + 0.05, sy + 0.02 + hh, fill=alpha(hexc("#c8d8e0"), 200), outline=OUTLINE, width=0.008)
            c.rect(jx - 0.045, sy + 0.025, jx + 0.045, sy + 0.02 + hh * 0.7, fill=alpha(liquid, 230))
            if rnd.random() < 0.4:
                c.ellipse(jx, sy + 0.02 + hh * 0.35, 0.025, 0.03, fill=alpha(hexc("#e0d0c0"), 230), outline=alpha(OUTLINE, 160), width=0.005)
            c.rect(jx - 0.05, sy + 0.02 + hh, jx + 0.05, sy + 0.04 + hh, fill=hexc("#5a5a60"))
    c.line([(gx0 + 0.04, fy + 0.55), (gx0 + 0.12, fy + H * K - 0.15)], fill=alpha((255, 255, 255, 255), 70), width=0.025)   # Glasreflex
    c.line([((gx0 + gx1) / 2, fy + 0.5), ((gx0 + gx1) / 2, fy + H * K - 0.08)], fill=hexc("#9aa0a4"), width=0.015)
    ty = y0 + H * K
    c.rect(x0 + 0.12, ty + 0.15, x0 + 0.42, ty + 0.35, fill=hexc("#6a5a48"), outline=OUTLINE, width=0.015)        # Kiste
    c.line([(x0 + 0.12, ty + 0.27), (x0 + 0.42, ty + 0.27)], fill=OUTLINE, width=0.008)
    skull(c, x1 - 0.3, ty + 0.18, 0.9)
    c.rect(x1 - 0.55, ty + 0.12, x1 - 0.45, ty + 0.36, fill=alpha(hexc("#c8d8e0"), 200), outline=OUTLINE, width=0.008)
    c.rect(x1 - 0.545, ty + 0.13, x1 - 0.455, ty + 0.27, fill=alpha(hexc("#9ab060"), 230))
    for k in range(2):                                                                # Schubladen unten
        c.rect(gx0, fy + 0.06 + k * 0.2, gx1, fy + 0.22 + k * 0.2, fill=hexc("#cdd2ce"), outline=OUTLINE, width=0.012)
        c.rect((gx0 + gx1) / 2 - 0.05, fy + 0.12 + k * 0.2, (gx0 + gx1) / 2 + 0.05, fy + 0.15 + k * 0.2, fill=STEEL_D)
