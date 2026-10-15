# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_art3.py - Einrichtung und Horror-Schicht von Garten, Einfahrt, Crew-Lager, Gewaechshaus, Friedhof und
# Gruft seit dem Audit 15.10. Vertrag wie villa_art.py; wird von villa_art2 importiert und registriert sich selbst.

import math
import random

import villa_art as VA
from museum_art import OUT_W  # noqa: E402
from villa_art import (BLOOD, BLOOD_L, BRASS, BRASS_D, BRASS_L, CREAM, FLAME, GAFFER, IRON, IRON_D, IRON_L, MATTE,
                       MATTE_D, MATTE_L, MOSS, PARCH, STEEL, WALNUT, WALNUT_D, WALNUT_L, WARM, K, OUTLINE,                        alpha, hexc, shade, cable, gaffer, blood_pool, blood_drips, cobweb, smoke, flame, crack, moss,
                       hedge_mass)
from villa_art2 import register, LINEN, LINEN_D, PALE, GLASS_C, WOOD_LIGHT, RED, chair_simple

STONE = hexc("#8c9098")
STONE_D = shade(STONE, 0.7)
STONE_L = shade(STONE, 1.2)
LEAF = hexc("#4f7a3c")
LEAF_D = shade(LEAF, 0.7)
CANVAS = hexc("#6a6e52")
VAN = hexc("#d8d4c8")
EARTH = hexc("#5a4a3a")
WATER_RED = alpha(hexc("#7a1a22"), 230)


def stone_block(p, x0, y0, x1, y1, z0, h):
    p.box(x0, y0, x1, y1, z0, h, STONE_L, STONE)


# ------------------------------------------------------------------ Terrasse

def _kamerakran(p, c, x0, y0, x1, y1, idx, rnd):
    """Kamerakran der Crew: Rollgestell mit Gegengewicht, langer Ausleger mit Kamera, Gaffer-Markierungen."""
    for rx, ry in ((x0 + 0.3, y0 + 0.15), (x1 - 0.3, y0 + 0.15), (x0 + 0.3, y1 - 0.15), (x1 - 0.3, y1 - 0.15)):
        c.ellipse(rx, ry, 0.12, 0.07, fill=MATTE_D, outline=OUTLINE, width=0.015)
    p.box(x0 + 0.2, y0 + 0.2, x1 - 0.2, y1 - 0.2, 0.12, 0.5, MATTE_L, MATTE)
    zt = y0 + 0.2 + 0.62 * K
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for sx in (cx - 0.3, cx + 0.3):
        c.line([(sx, zt), (cx, zt + 1.1)], fill=OUTLINE, width=0.06)
        c.line([(sx, zt), (cx, zt + 1.1)], fill=MATTE_L, width=0.035)
    c.line([(cx - 0.25, zt + 0.5), (cx + 0.25, zt + 0.5)], fill=MATTE_L, width=0.025)
    px, py = cx, zt + 1.1
    c.ellipse(px, py, 0.08, 0.08, fill=STEEL, outline=OUTLINE, width=0.015)
    ax, ay = px + 1.5, py + 0.7
    bx, by = px - 0.9, py - 0.4
    c.line([(bx, by), (ax, ay)], fill=OUTLINE, width=0.09)
    c.line([(bx, by), (ax, ay)], fill=MATTE_L, width=0.06)
    c.line([(bx + 0.1, by + 0.06), (ax - 0.1, ay - 0.04)], fill=STEEL, width=0.012)
    for k in range(6):
        t = k / 5
        c.line([(bx + (ax - bx) * t, by + (ay - by) * t - 0.04), (bx + (ax - bx) * t, by + (ay - by) * t + 0.04)], fill=OUTLINE, width=0.015)
    c.rect(bx - 0.15, by - 0.15, bx + 0.12, by + 0.1, fill=MATTE, outline=OUTLINE, width=0.02)        # Gegengewicht
    gaffer(c, bx - 0.13, by - 0.02, bx + 0.1, by - 0.02, 0.03)
    c.rect(ax - 0.1, ay - 0.12, ax + 0.18, ay + 0.1, fill=MATTE_L, outline=OUTLINE, width=0.02)       # Kamera
    c.rect(ax + 0.18, ay - 0.06, ax + 0.3, ay + 0.04, fill=MATTE, outline=OUTLINE, width=0.015)
    c.ellipse(ax + 0.31, ay - 0.01, 0.03, 0.04, fill=hexc("#1a1c22"), outline=OUTLINE, width=0.012)
    c.ellipse(ax + 0.02, ay + 0.1, 0.02, 0.02, fill=RED)
    c.glow(ax + 0.02, ay + 0.1, 0.05, RED, 0.5)
    cable(c, [(bx, by - 0.1), (bx - 0.2, zt + 0.2), (x0 - 0.1, y0 - 0.1)], seed=idx)
    cobweb(c, px - 0.04, py + 0.05, 0.12, -1, 1, seed=idx)


def _statue_schleier(p, c, x0, y0, x1, y1, idx, rnd):
    """Gartenstatue mit Schleier, der Kopf ist gedreht, Moos am Sockel."""
    cx = (x0 + x1) / 2
    stone_block(p, x0, y0, x1, y1, 0, 0.5)
    base = y0 + 0.5 * K
    moss(c, x0 + 0.1, y0 + 0.05, 0.1, seed=idx)
    moss(c, x1 - 0.1, y0 + 0.15, 0.08, seed=idx + 1)
    c.poly([(cx - 0.26, base), (cx + 0.26, base), (cx + 0.2, base + 1.2), (cx - 0.2, base + 1.2)], fill=STONE_L, outline=OUTLINE, width=0.02)
    for k in range(4):
        c.line([(cx - 0.18 + k * 0.12, base + 0.05), (cx - 0.15 + k * 0.1, base + 1.1)], fill=alpha(STONE_D, 120), width=0.012)
    c.ellipse(cx, base + 1.32, 0.14, 0.17, fill=STONE_L, outline=OUTLINE, width=0.02)
    c.poly([(cx - 0.16, base + 1.3), (cx + 0.16, base + 1.3), (cx + 0.2, base + 1.55), (cx - 0.2, base + 1.55)], fill=STONE_L, outline=OUTLINE, width=0.015)   # Schleier
    c.ellipse(cx + 0.06, base + 1.32, 0.012, 0.016, fill=STONE_D)                                        # Kopf gedreht
    c.ellipse(cx + 0.11, base + 1.33, 0.01, 0.014, fill=STONE_D)
    c.line([(cx - 0.3, base + 0.8), (cx - 0.36, base + 1.1)], fill=OUTLINE, width=0.05)
    c.line([(cx - 0.3, base + 0.8), (cx - 0.36, base + 1.1)], fill=STONE_L, width=0.03)
    crack(c, [(cx + 0.1, base + 0.3), (cx + 0.05, base + 0.6), (cx + 0.12, base + 0.8)], seed=idx)
    cobweb(c, cx - 0.2, base + 1.2, 0.1, -1, -1, seed=idx)


def _gartentisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Schmiedeeiserner Gartentisch mit zwei Stuehlen, ein Stuhl umgekippt, Regenlache nur auf dem Tisch."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    for a in (0.3, 2.4, 4.4):
        c.line([(cx, cy + 0.4 * K), (cx + r * 0.7 * math.cos(a), cy + r * 0.4 * math.sin(a))], fill=OUTLINE, width=0.03)
        c.line([(cx, cy + 0.4 * K), (cx + r * 0.7 * math.cos(a), cy + r * 0.4 * math.sin(a))], fill=IRON, width=0.016)
    c.rect(cx - 0.02, cy + 0.3 * K, cx + 0.02, cy + 0.72 * K, fill=IRON, outline=OUTLINE, width=0.012)
    zt = cy + 0.72 * K
    c.ellipse(cx, zt, r * 0.75, r * 0.4, fill=IRON_L, outline=OUTLINE, width=0.02)
    for k in range(5):
        c.ellipse(cx, zt, r * 0.75 * (k + 1) / 6, r * 0.4 * (k + 1) / 6, outline=alpha(IRON_D, 120), width=0.006)
    c.ellipse(cx + 0.05, zt + 0.02, r * 0.4, r * 0.18, fill=alpha(hexc("#8ab0d8"), 110))
    # Stuehle: links stehend, rechts umgekippt
    chair_simple(p, c, cx - r * 0.95, cy - 0.1, 0.4, 0.4, 0.0, IRON)
    c.poly([(cx + r * 0.6, cy - 0.35), (cx + r * 0.6 + 0.4, cy - 0.3), (cx + r * 0.6 + 0.38, cy - 0.1), (cx + r * 0.6 - 0.02, cy - 0.15)], fill=IRON_L, outline=OUTLINE, width=0.015)
    for k in range(3):
        c.line([(cx + r * 0.6 + 0.05 + k * 0.13, cy - 0.33), (cx + r * 0.6 + 0.1 + k * 0.13, cy - 0.55)], fill=OUTLINE, width=0.03)
        c.line([(cx + r * 0.6 + 0.05 + k * 0.13, cy - 0.33), (cx + r * 0.6 + 0.1 + k * 0.13, cy - 0.55)], fill=IRON, width=0.016)


def _kuebelpflanze(p, c, x0, y0, x1, y1, idx, rnd):
    """Welke Kuebelpflanze: Terrakotta-Kuebel, kahle Zweige, ein paar braune Blaetter."""
    cx = (x0 + x1) / 2
    p.cyl(cx, (y0 + y1) / 2, (x1 - x0) / 2 - 0.02, 0, 0.55, hexc("#b86a4a"), hexc("#9a5a3a"), ry=(y1 - y0) / 2 * 0.5)
    zt = (y0 + y1) / 2 + 0.55 * K
    c.ellipse(cx, zt, (x1 - x0) / 2 - 0.04, (y1 - y0) / 2 * 0.45, fill=EARTH)
    for k in range(5):
        a = -0.6 + k * 0.3
        pts = [(cx, zt), (cx + 0.3 * math.sin(a), zt + 0.4), (cx + 0.55 * math.sin(a) + 0.05 * k, zt + 0.75 + 0.1 * (k % 2))]
        c.line(VA.HD.wobble(pts, amp=0.015, seed=idx + k, step=0.05), fill=hexc("#5a4a3a"), width=0.016)
        c.ellipse(pts[-1][0], pts[-1][1], 0.03, 0.02, fill=hexc("#8a6a3a"), outline=OUTLINE, width=0.006)
    c.ellipse(cx + 0.1, y0 - 0.03, 0.04, 0.02, fill=hexc("#8a6a3a"))
    crack(c, [(cx - 0.1, (y0 + y1) / 2 + 0.05), (cx - 0.05, (y0 + y1) / 2 + 0.25)], seed=idx)


def _vogelschwarm(p, c, x0, y0, x1, y1, idx, rnd):
    """Vogelschwarm auf der Balustrade: Kraehen in einer Reihe, alle schauen in dieselbe Richtung."""
    n = 6
    for k in range(n):
        bx = x0 + (x1 - x0) * (k + 0.5) / n
        by = y0 + 0.05 + (k % 2) * 0.03
        c.ellipse(bx, by + 0.08, 0.07, 0.05, fill=hexc("#141418"), outline=OUTLINE, width=0.01)
        c.ellipse(bx + 0.05, by + 0.14, 0.035, 0.03, fill=hexc("#141418"))
        c.poly([(bx + 0.08, by + 0.14), (bx + 0.13, by + 0.13), (bx + 0.08, by + 0.12)], fill=hexc("#8a8a30"))
        c.ellipse(bx + 0.06, by + 0.15, 0.006, 0.006, fill=RED)
        c.line([(bx - 0.06, by + 0.07), (bx - 0.12, by + 0.05)], fill=hexc("#141418"), width=0.02)
    c.rect(x0 - 0.1, y0, x1 + 0.1, y0 + 0.05, fill=STONE_L, outline=OUTLINE, width=0.012)


# ------------------------------------------------------------------ Einfahrt, Crew-Lager

def _van(p, c, x0, y0, x1, y1, idx, rnd):
    """Crew-Transporter: weisser Kastenwagen, Schiebetuer offen, Seitenscheibe zerschlagen, Aufschrift."""
    for rx in (x0 + 0.5, x1 - 0.5):
        c.ellipse(rx, y0 + 0.02, 0.26, 0.14, fill=MATTE_D, outline=OUTLINE, width=0.02)
        c.ellipse(rx, y0 + 0.02, 0.12, 0.065, fill=STEEL, outline=OUTLINE, width=0.012)
    p.box(x0, y0 + 0.1, x1, y1, 0.25, 1.1, shade(VAN, 1.05), VAN)
    fz = y0 + 0.1 + 0.25 * K
    ft = fz + 1.1 * K
    c.line([(x0 + 0.05, fz + 0.3), (x1 - 0.05, fz + 0.3)], fill=shade(VAN, 0.7), width=0.012)
    c.rect(x0 + 0.08, fz + 0.32, x0 + 0.7, ft - 0.08, fill=hexc("#8ab0d8"), outline=OUTLINE, width=0.015)       # Windschutzscheibe (links Fahrerhaus)
    c.line([(x0 + 0.12, ft - 0.12), (x0 + 0.5, fz + 0.4)], fill=alpha(hexc("#ffffff"), 90), width=0.03)
    c.rect(x0 + 0.85, fz + 0.32, x0 + 1.45, ft - 0.08, fill=hexc("#8ab0d8"), outline=OUTLINE, width=0.015)      # Seitenscheibe, zerschlagen
    crack(c, [(x0 + 1.0, ft - 0.1), (x0 + 1.15, fz + 0.5), (x0 + 1.3, fz + 0.4)], seed=idx)
    crack(c, [(x0 + 1.15, fz + 0.5), (x0 + 1.4, fz + 0.6)], seed=idx + 1)
    c.ellipse(x0 + 1.15, fz + 0.5, 0.05, 0.04, fill=hexc("#1a2234"))
    c.rect(x0 + 1.6, fz + 0.08, x1 - 0.1, ft - 0.08, fill=hexc("#1a1c22"), outline=OUTLINE, width=0.015)        # Schiebetuer offen
    c.rect(x0 + 1.65, fz + 0.12, x0 + 2.2, fz + 0.4, fill=MATTE, outline=OUTLINE, width=0.01)                   # Kisten drin
    gaffer(c, x0 + 1.7, fz + 0.3, x0 + 2.1, fz + 0.3, 0.03)
    c.text(x0 + 0.8, fz + 0.18, "HOLLOWMERE PICTURES", 0.055, hexc("#3a3a60"))
    c.rect(x1 - 0.12, fz + 0.1, x1 - 0.04, fz + 0.2, fill=RED, outline=OUTLINE, width=0.008)                   # Ruecklicht
    blood_drips(c, x0 + 1.62, fz + 0.3, 2, 0.1, seed=idx)


def _lichtstativ(p, c, x0, y0, x1, y1, idx, rnd):
    """Lichtstativ der Crew mit Scheinwerferkopf, Torblenden, eine Klammer mit Filterfolie."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for a in (0.6, 2.6, 4.6):
        c.line([(cx, cy + 0.5 * K), (cx + 0.3 * math.cos(a), cy + 0.18 * math.sin(a))], fill=OUTLINE, width=0.035)
        c.line([(cx, cy + 0.5 * K), (cx + 0.3 * math.cos(a), cy + 0.18 * math.sin(a))], fill=MATTE_L, width=0.02)
    c.rect(cx - 0.02, cy + 0.4 * K, cx + 0.02, cy + 2.0 * K, fill=MATTE, outline=OUTLINE, width=0.012)
    hz = cy + 2.0 * K
    c.rect(cx - 0.2, hz - 0.05, cx + 0.2, hz + 0.3, fill=MATTE_L, outline=OUTLINE, width=0.02)
    c.ellipse(cx, hz + 0.13, 0.15, 0.13, fill=hexc("#f0e8c8"), outline=OUTLINE, width=0.015)
    c.glow(cx, hz + 0.13, 0.35, WARM, 0.4)
    for k in range(4):
        a = math.pi / 2 * k + 0.4
        c.poly([(cx + 0.2 * math.cos(a), hz + 0.13 + 0.2 * math.sin(a)), (cx + 0.34 * math.cos(a + 0.3), hz + 0.13 + 0.34 * math.sin(a + 0.3)), (cx + 0.34 * math.cos(a - 0.3), hz + 0.13 + 0.34 * math.sin(a - 0.3))], fill=MATTE, outline=OUTLINE, width=0.01)
    c.rect(cx + 0.14, hz + 0.3, cx + 0.3, hz + 0.42, fill=alpha(hexc("#c83a30"), 160), outline=OUTLINE, width=0.008)
    cable(c, [(cx, cy + 0.4 * K), (cx + 0.3, cy - 0.05), (cx + 0.6, cy - 0.15)], seed=idx)


def _campingtisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Campingtisch der Crew: Klapptisch mit Thermoskanne, Drehbuch, Funkgeraet, Kaffeebecher."""
    for sx in (x0 + 0.1, x1 - 0.1):
        c.line([(sx - 0.05, y0 + 0.02), (sx + 0.05, y0 + 0.7 * K)], fill=OUTLINE, width=0.03)
        c.line([(sx - 0.05, y0 + 0.02), (sx + 0.05, y0 + 0.7 * K)], fill=STEEL, width=0.016)
        c.line([(sx + 0.05, y0 + 0.02), (sx - 0.05, y0 + 0.7 * K)], fill=OUTLINE, width=0.03)
        c.line([(sx + 0.05, y0 + 0.02), (sx - 0.05, y0 + 0.7 * K)], fill=STEEL, width=0.016)
    p.box(x0, y0, x1, y1, 0.7, 0.04, shade(CANVAS, 1.15), CANVAS)
    zt = y0 + 0.74 * K
    c.rect(x0 + 0.15, zt + 0.02, x0 + 0.27, zt + 0.3, fill=STEEL, outline=OUTLINE, width=0.012)
    c.rect(x0 + 0.17, zt + 0.3, x0 + 0.25, zt + 0.36, fill=MATTE_D)
    c.poly([(x0 + 0.5, zt + 0.04), (x0 + 0.95, zt + 0.02), (x0 + 0.96, zt + 0.3), (x0 + 0.51, zt + 0.32)], fill=CREAM, outline=OUTLINE, width=0.01)
    c.text(x0 + 0.73, zt + 0.2, "SCRIPT", 0.04, OUTLINE)
    c.text(x0 + 0.73, zt + 0.1, "REV. 13", 0.03, RED)
    c.rect(x1 - 0.5, zt + 0.02, x1 - 0.38, zt + 0.2, fill=MATTE_D, outline=OUTLINE, width=0.01)
    c.line([(x1 - 0.44, zt + 0.2), (x1 - 0.44, zt + 0.34)], fill=MATTE_D, width=0.012)
    c.ellipse(x1 - 0.2, zt + 0.08, 0.04, 0.035, fill=CREAM, outline=OUTLINE, width=0.01)
    c.ellipse(x1 - 0.2, zt + 0.08, 0.025, 0.015, fill=hexc("#5a3a1a"))


def _kabeltrommel(p, c, x0, y0, x1, y1, idx, rnd):
    """Kabeltrommel: Holztrommel liegend mit schwarzem Kabel, ein Ende laeuft weg."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    c.ellipse(cx, cy, r, r * 0.55, fill=WOOD_LIGHT, outline=OUTLINE, width=0.02)
    c.rect(cx - r, cy, cx + r, cy + 0.45, fill=MATTE)
    c.line([(cx - r, cy), (cx - r, cy + 0.45)], fill=OUTLINE, width=0.02)
    c.line([(cx + r, cy), (cx + r, cy + 0.45)], fill=OUTLINE, width=0.02)
    for k in range(5):
        c.line([(cx - r + 0.02, cy + 0.06 + k * 0.08), (cx + r - 0.02, cy + 0.06 + k * 0.08)], fill=MATTE_L, width=0.012)
    c.ellipse(cx, cy + 0.45, r, r * 0.55, fill=WOOD_LIGHT, outline=OUTLINE, width=0.02)
    c.ellipse(cx, cy + 0.45, r * 0.3, r * 0.17, fill=shade(WOOD_LIGHT, 0.7), outline=OUTLINE, width=0.012)
    for k in range(4):
        a = math.pi / 2 * k + 0.3
        c.line([(cx, cy + 0.45), (cx + r * 0.9 * math.cos(a), cy + 0.45 + r * 0.5 * math.sin(a))], fill=shade(WOOD_LIGHT, 0.75), width=0.015)
    cable(c, [(cx + r, cy + 0.1), (cx + r + 0.3, cy - 0.1), (cx + r + 0.7, cy - 0.05)], seed=idx)


def _dixi(p, c, x0, y0, x1, y1, idx, rnd):
    """Toilettenhaeuschen der Crew, Tuer angelehnt, Schild BESETZT, von innen klopft es (Kratzer)."""
    col = hexc("#3a7a8a")
    p.box(x0, y0, x1, y1, 0, 2.1, shade(col, 1.15), col)
    fz = y0
    ft = fz + 2.1 * K
    c.rect(x0 + 0.08, fz + 0.12, x1 - 0.08, ft - 0.12, fill=shade(col, 0.9), outline=OUTLINE, width=0.015)
    c.rect(x0 + 0.1, fz + 0.14, x0 + 0.3, ft - 0.14, fill=hexc("#0b0d10"))
    c.rect(x1 - 0.2, fz + 0.5, x1 - 0.14, fz + 0.6, fill=STEEL, outline=OUTLINE, width=0.008)
    c.rect(x0 + 0.35, ft - 0.3, x1 - 0.14, ft - 0.2, fill=RED, outline=OUTLINE, width=0.008)
    c.text((x0 + x1) / 2 + 0.1, ft - 0.25, "OCCUPIED", 0.03, CREAM)
    c.rect(x0 + 0.3, ft - 0.08, x1 - 0.3, ft - 0.02, fill=MATTE_D)
    for k in range(3):
        c.line([(x1 - 0.5 + k * 0.08, fz + 0.9), (x1 - 0.45 + k * 0.08, fz + 0.65)], fill=shade(col, 0.55), width=0.012)
    c.ellipse((x0 + x1) / 2, y1 + 2.1 * K + 0.03, (x1 - x0) / 2, 0.08, fill=shade(col, 1.25), outline=OUTLINE, width=0.015)


def _zelt_aufgeschlitzt(p, c, x0, y0, x1, y1, idx, rnd):
    """Crew-Zelt, aufgeschlitzt: die Zeltwand haengt in Fetzen, drinnen ein umgestuerzter Stuhl."""
    VA._zelt(p, c, x0, y0, x1, y1, idx, rnd)
    cx = (x0 + x1) / 2
    base = y0
    c.poly([(cx - 0.3, base + 0.15), (cx - 0.1, base + 0.2), (cx - 0.05, base + 0.9), (cx - 0.35, base + 0.85)], fill=hexc("#1a1c16"), outline=OUTLINE, width=0.015)
    c.poly([(cx - 0.12, base + 0.25), (cx + 0.02, base + 0.3), (cx - 0.1, base + 0.8), (cx - 0.2, base + 0.6)], fill=shade(CANVAS, 0.85), outline=OUTLINE, width=0.012)
    for k in range(4):
        c.line([(cx - 0.3 + k * 0.1, base + 0.2 + k * 0.15), (cx - 0.33 + k * 0.1, base + 0.05)], fill=shade(CANVAS, 0.7), width=0.01)
    c.line([(cx - 0.25, base + 0.6), (cx - 0.15, base + 0.35)], fill=WOOD_LIGHT, width=0.02)
    blood_pool(c, cx - 0.2, base + 0.05, 0.12, 0.05, seed=idx, a=200)


def _schlafsack(p, c, x0, y0, x1, y1, idx, rnd):
    """Schlafsack am Boden mit dem Umriss von jemandem darin, Reissverschluss zu."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pts = VA.HD.wobble_ellipse(cx, cy, (x1 - x0) / 2, (y1 - y0) / 2, amp=0.02, seed=idx)
    c.poly(pts, fill=hexc("#3a4a6a"), outline=OUTLINE, width=0.02)
    c.ellipse(cx - 0.2, cy + 0.05, 0.25, 0.14, fill=alpha(hexc("#2a3a5a"), 180))
    c.ellipse(cx + 0.45, cy + 0.02, 0.18, 0.14, fill=alpha(hexc("#2a3a5a"), 180))
    c.line([(x0 + 0.1, cy), (x1 - 0.3, cy)], fill=STEEL, width=0.012)
    c.ellipse(x1 - 0.3, cy, 0.015, 0.015, fill=STEEL, outline=OUTLINE, width=0.006)
    c.ellipse(x1 - 0.15, cy + 0.02, 0.12, 0.1, fill=hexc("#3a4a6a"), outline=OUTLINE, width=0.015)
    c.ellipse(x1 - 0.15, cy + 0.02, 0.07, 0.055, fill=hexc("#1a1c22"))


# ------------------------------------------------------------------ Gewaechshaus, Brunnenhof

def _riesenpflanze(p, c, x0, y0, x1, y1, idx, rnd):
    """Fleischfressende Riesenpflanze im Kuebel, Maul offen, ein Stiefel ragt heraus, Ranken am Boden."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    p.cyl(cx, cy, 0.5, 0, 0.5, hexc("#b86a4a"), hexc("#9a5a3a"), ry=0.25)
    zt = cy + 0.5 * K
    for k in range(5):
        a = -1.2 + k * 0.6
        pts = [(cx, zt), (cx + 0.6 * math.sin(a), zt + 0.5), (cx + 0.9 * math.sin(a), zt + 0.3 + 0.2 * (k % 2))]
        c.line(VA.HD.wobble(pts, amp=0.02, seed=idx + k, step=0.05), fill=LEAF_D, width=0.05)
        c.poly([(pts[-1][0] - 0.12, pts[-1][1]), (pts[-1][0] + 0.12, pts[-1][1]), (pts[-1][0], pts[-1][1] + 0.28)], fill=LEAF, outline=OUTLINE, width=0.015)
    c.line(VA.HD.wobble([(cx, zt), (cx + 0.1, zt + 0.6), (cx - 0.05, zt + 1.1)], amp=0.03, seed=idx, step=0.06), fill=LEAF_D, width=0.09)
    c.line(VA.HD.wobble([(cx, zt), (cx + 0.1, zt + 0.6), (cx - 0.05, zt + 1.1)], amp=0.03, seed=idx, step=0.06), fill=LEAF, width=0.05)
    mx, my = cx - 0.05, zt + 1.2
    c.ellipse(mx, my, 0.32, 0.22, fill=hexc("#8a2a4a"), outline=OUTLINE, width=0.025)
    c.ellipse(mx, my - 0.02, 0.24, 0.12, fill=hexc("#3a0a18"))
    for k in range(7):
        tx = mx - 0.22 + k * 0.073
        c.poly([(tx - 0.025, my + 0.1), (tx + 0.025, my + 0.1), (tx, my - 0.02)], fill=CREAM, outline=OUTLINE, width=0.006)
        c.poly([(tx - 0.025, my - 0.12), (tx + 0.025, my - 0.12), (tx, my + 0.0)], fill=CREAM, outline=OUTLINE, width=0.006)
    c.poly([(mx + 0.05, my - 0.02), (mx + 0.22, my - 0.08), (mx + 0.3, my + 0.12), (mx + 0.18, my + 0.2), (mx + 0.08, my + 0.12)], fill=hexc("#5a3a2a"), outline=OUTLINE, width=0.015)   # Stiefel
    c.line([(mx + 0.1, my + 0.05), (mx + 0.2, my + 0.02)], fill=hexc("#8a6a4a"), width=0.012)
    blood_drips(c, mx - 0.1, my - 0.16, 3, 0.12, seed=idx)
    for k in range(3):
        cable(c, [(cx - 0.5 + k * 0.5, cy - 0.2), (cx - 0.7 + k * 0.6, cy - 0.45), (cx - 0.9 + k * 0.8, cy - 0.5)], seed=idx + k, w=0.03, col=LEAF_D)


def _giesskannen(p, c, x0, y0, x1, y1, idx, rnd):
    """Zwei Giesskannen aus Zink, eine umgekippt, Wasser laeuft rot aus."""
    cx = (x0 + x1) / 2
    p.cyl(x0 + 0.22, y0 + 0.25, 0.16, 0, 0.35, shade(STEEL, 1.1), STEEL, ry=0.08)
    c.line([(x0 + 0.36, y0 + 0.25 + 0.2 * K), (x0 + 0.6, y0 + 0.25 + 0.4 * K + 0.1)], fill=OUTLINE, width=0.04)
    c.line([(x0 + 0.36, y0 + 0.25 + 0.2 * K), (x0 + 0.6, y0 + 0.25 + 0.4 * K + 0.1)], fill=STEEL, width=0.022)
    c.ellipse(x0 + 0.6, y0 + 0.25 + 0.4 * K + 0.1, 0.04, 0.03, fill=shade(STEEL, 0.8), outline=OUTLINE, width=0.01)
    c.ellipse(x0 + 0.22, y0 + 0.25 + 0.42 * K, 0.08, 0.04, outline=OUTLINE, width=0.025)
    c.ellipse(x0 + 0.22, y0 + 0.25 + 0.42 * K, 0.08, 0.04, outline=shade(STEEL, 1.2), width=0.012)
    c.poly([(cx + 0.05, y1 - 0.15), (cx + 0.35, y1 - 0.2), (cx + 0.36, y1 + 0.0), (cx + 0.06, y1 + 0.05)], fill=shade(STEEL, 0.9), outline=OUTLINE, width=0.015)
    c.ellipse(cx + 0.36, y1 - 0.1, 0.03, 0.1, fill=shade(STEEL, 0.75), outline=OUTLINE, width=0.012)
    blood_pool(c, cx + 0.5, y1 - 0.14, 0.15, 0.05, seed=idx, a=200)


def _schlauchtrommel(p, c, x0, y0, x1, y1, idx, rnd):
    """Schlauchtrommel aus Gusseisen an der Wand mit gruenem Schlauch, Ende zur Pflanze."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    c.rect(cx - 0.04, cy, cx + 0.04, cy + 0.5, fill=IRON, outline=OUTLINE, width=0.012)
    c.ellipse(cx, cy + 0.5, r, r, fill=hexc("#2f6b3f"), outline=OUTLINE, width=0.025)
    for k in range(4):
        c.ellipse(cx, cy + 0.5, r * (0.85 - k * 0.18), r * (0.85 - k * 0.18), outline=shade(hexc("#2f6b3f"), 0.6), width=0.012)
    c.ellipse(cx, cy + 0.5, 0.06, 0.06, fill=IRON_L, outline=OUTLINE, width=0.012)
    c.line([(cx + 0.08, cy + 0.5), (cx + 0.2, cy + 0.58)], fill=IRON, width=0.018)
    cable(c, [(cx + r, cy + 0.3), (cx + r + 0.3, cy - 0.1), (cx + r + 0.2, cy - 0.4)], seed=idx, w=0.035, col=hexc("#2f6b3f"))


def _kletterpflanzen(p, c, x0, y0, x1, y1, idx, rnd):
    """Efeu und Ranken an der Glaswand des Gewaechshauses, mit Blaettern, eine Ranke greift nach innen."""
    cx = (x0 + x1) / 2
    for k in range(3):
        pts = [(cx + 0.1 * (k - 1), y0 + 0.05), (cx - 0.2 + 0.25 * k, y0 + 0.8), (cx + 0.1 - 0.2 * k, y0 + 1.5), (cx - 0.15 + 0.15 * k, y0 + 2.0)]
        q = VA.HD.wobble(pts, amp=0.03, seed=idx + k, step=0.06)
        c.line(q, fill=LEAF_D, width=0.025)
        for j, (lx, ly) in enumerate(q[::3]):
            c.poly([(lx - 0.06, ly), (lx, ly + 0.09), (lx + 0.06, ly), (lx, ly - 0.04)], fill=LEAF if (j + k) % 2 else shade(LEAF, 0.85), outline=OUTLINE, width=0.008)
    c.line(VA.HD.wobble([(cx, y0 + 1.2), (cx - 0.3, y0 + 1.05), (cx - 0.5, y0 + 0.9)], amp=0.03, seed=idx + 9, step=0.05), fill=LEAF_D, width=0.03)
    c.poly([(cx - 0.5, y0 + 0.9), (cx - 0.56, y0 + 1.0), (cx - 0.6, y0 + 0.86), (cx - 0.55, y0 + 0.8)], fill=LEAF, outline=OUTLINE, width=0.008)


def _sonnenuhr(p, c, x0, y0, x1, y1, idx, rnd):
    """Sonnenuhr auf Steinsaeule ohne Schatten, Ziffernring, Messingzeiger."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    p.cyl(cx, cy, r, 0, 0.15, STONE_L, STONE, ry=r * 0.5)
    p.cyl(cx, cy, r * 0.5, 0.15, 0.8, STONE_L, STONE, ry=r * 0.25)
    zt = cy + 0.95 * K
    c.ellipse(cx, zt, r * 1.05, r * 0.5, fill=STONE_L, outline=OUTLINE, width=0.02)
    for k in range(12):
        a = math.pi * 2 * k / 12
        c.line([(cx + r * 0.8 * math.cos(a), zt + r * 0.38 * math.sin(a)), (cx + r * 0.95 * math.cos(a), zt + r * 0.45 * math.sin(a))], fill=STONE_D, width=0.01)
    c.poly([(cx, zt), (cx + r * 0.5, zt + 0.02), (cx, zt + 0.3)], fill=BRASS, outline=OUTLINE, width=0.012)
    moss(c, cx - r * 0.5, cy + 0.1, 0.08, seed=idx)
    c.text(cx, zt - r * 0.2, "TEMPUS FUGIT", 0.028, STONE_D)


def _parkbank(p, c, x0, y0, x1, y1, idx, rnd):
    """Parkbank, waagerecht an der Suedwand, gusseiserne Fuesse, ein Brett fehlt, Zeitung von heute."""
    for sx in (x0 + 0.15, x1 - 0.15):
        c.rect(sx - 0.04, y0 + 0.02, sx + 0.04, y0 + 0.45 * K, fill=IRON, outline=OUTLINE, width=0.012)
        c.line([(sx - 0.1, y0 + 0.02), (sx + 0.1, y0 + 0.02)], fill=IRON, width=0.03)
    for k in range(3):
        if k == 1:
            continue
        sy = y0 + 0.45 * K + k * 0.09
        c.rect(x0, sy, x1, sy + 0.07, fill=WALNUT_L, outline=OUTLINE, width=0.012)
    for k in range(3):
        by = y1 + 0.45 * K + 0.3 + k * 0.1
        c.rect(x0 + 0.02, by, x1 - 0.02, by + 0.07, fill=WALNUT_L, outline=OUTLINE, width=0.012)
    for sx in (x0 + 0.15, x1 - 0.15):
        c.line([(sx, y0 + 0.45 * K + 0.2), (sx, y1 + 0.45 * K + 0.6)], fill=IRON, width=0.03)
    c.poly([(x0 + 0.5, y0 + 0.45 * K + 0.04), (x0 + 0.85, y0 + 0.45 * K + 0.02), (x0 + 0.86, y0 + 0.45 * K + 0.2), (x0 + 0.51, y0 + 0.45 * K + 0.22)], fill=CREAM, outline=OUTLINE, width=0.008)
    c.text(x0 + 0.68, y0 + 0.45 * K + 0.12, "OCT 31", 0.03, OUTLINE)


def _brunnen_blut(p, c, x0, y0, x1, y1, idx, rnd):
    """Vor dem Brunnen gezeichnet: rotes Wasser im Becken und eine verschleierte Figur in der Mitte."""
    cx = (x0 + x1) / 2
    # Beckenwasser (liegt auf der Zeichnung des Brunnens, Mitte 1,2 m noerdlich der Standlinie)
    wy = y0 + 1.2
    c.ellipse(cx, wy, 0.95, 0.42, fill=WATER_RED)
    c.ellipse(cx - 0.3, wy + 0.1, 0.2, 0.06, fill=alpha(hexc("#a83040"), 120))
    c.ellipse(cx + 0.35, wy - 0.05, 0.15, 0.05, fill=alpha(hexc("#a83040"), 120))
    # Figur mit Schleier auf dem Sockel
    base = wy + 0.25
    pts = VA.HD.wobble([(cx - 0.18, base), (cx + 0.18, base), (cx + 0.14, base + 0.9), (cx, base + 1.05), (cx - 0.14, base + 0.9)], amp=0.012, seed=idx, step=0.05)
    c.poly(pts, fill=STONE_L, outline=OUTLINE, width=0.02)
    c.ellipse(cx - 0.04, base + 0.78, 0.02, 0.018, fill=STONE_D)
    c.ellipse(cx + 0.05, base + 0.78, 0.02, 0.018, fill=STONE_D)
    for k in range(3):
        c.line([(cx - 0.1 + k * 0.1, base + 0.7), (cx - 0.12 + k * 0.1, base + 0.1)], fill=alpha(STONE_D, 110), width=0.012)
    blood_drips(c, cx + 0.3, wy + 0.3, 3, 0.15, seed=idx)


# ------------------------------------------------------------------ Friedhof, Gruft

def _engelsstatue(p, c, x0, y0, x1, y1, idx, rnd):
    """Trauernder Engel auf Sockel, Gesicht in den Haenden, Fluegel; ein Auge blickt zwischen den Fingern."""
    cx = (x0 + x1) / 2
    stone_block(p, x0, y0, x1, y1, 0, 0.6)
    base = y0 + 0.6 * K
    moss(c, x0 + 0.15, y0 + 0.05, 0.1, seed=idx)
    for s in (-1, 1):
        c.poly([(cx + s * 0.1, base + 0.5), (cx + s * 0.55, base + 1.4), (cx + s * 0.45, base + 0.6), (cx + s * 0.2, base + 0.3)], fill=STONE_L, outline=OUTLINE, width=0.02)
        for k in range(3):
            c.line([(cx + s * (0.15 + k * 0.1), base + 0.45 + k * 0.25), (cx + s * (0.5 - k * 0.05), base + 1.1 + k * 0.08)], fill=alpha(STONE_D, 110), width=0.01)
    c.poly([(cx - 0.22, base), (cx + 0.22, base), (cx + 0.18, base + 1.1), (cx - 0.18, base + 1.1)], fill=STONE_L, outline=OUTLINE, width=0.02)
    c.ellipse(cx, base + 1.2, 0.13, 0.15, fill=STONE_L, outline=OUTLINE, width=0.02)
    c.poly([(cx - 0.15, base + 1.05), (cx + 0.15, base + 1.05), (cx + 0.12, base + 1.28), (cx - 0.12, base + 1.28)], fill=STONE, outline=OUTLINE, width=0.015)   # Haende
    for k in range(4):
        c.line([(cx - 0.1 + k * 0.065, base + 1.08), (cx - 0.1 + k * 0.065, base + 1.26)], fill=STONE_D, width=0.008)
    c.ellipse(cx + 0.03, base + 1.17, 0.012, 0.016, fill=hexc("#1a1c22"))
    crack(c, [(cx - 0.1, base + 0.2), (cx - 0.05, base + 0.5), (cx - 0.12, base + 0.8)], seed=idx)
    c.text(cx, y0 + 0.3 * K, "REST", 0.035, STONE_D)


def _offenes_grab(p, c, x0, y0, x1, y1, idx, rnd):
    """Frisch ausgehobenes Grab: Erdhaufen, dunkles Loch, Schaufel steckt, ein Seil haengt hinein."""
    cx = (x0 + x1) / 2
    pts = VA.HD.wobble_rect(x0 + 0.1, y0 + 0.1, x1 - 0.1, y1 - 0.5, amp=0.03, seed=idx)
    c.poly(pts, fill=hexc("#0e0c0a"), outline=OUTLINE, width=0.02)
    c.poly([(x0 + 0.12, y1 - 0.7), (x1 - 0.12, y1 - 0.7), (x1 - 0.14, y1 - 0.52), (x0 + 0.14, y1 - 0.52)], fill=hexc("#2a1e16"))
    mound = VA.HD.wobble([(x0 - 0.05, y1 - 0.5), (cx, y1 - 0.45), (x1 + 0.05, y1 - 0.5), (x1, y1 + 0.1), (cx, y1 + 0.25), (x0, y1 + 0.1)], amp=0.03, seed=idx + 1, step=0.08)
    c.poly(mound, fill=EARTH, outline=OUTLINE, width=0.02)
    for _ in range(10):
        c.ellipse(rnd.uniform(x0 + 0.05, x1 - 0.05), rnd.uniform(y1 - 0.4, y1 + 0.15), 0.02, 0.012, fill=shade(EARTH, 1.3))
    c.line([(x1 - 0.3, y1 - 0.1), (x1 - 0.05, y1 + 0.75)], fill=OUTLINE, width=0.04)
    c.line([(x1 - 0.3, y1 - 0.1), (x1 - 0.05, y1 + 0.75)], fill=WOOD_LIGHT, width=0.022)
    c.poly([(x1 - 0.42, y1 - 0.2), (x1 - 0.18, y1 - 0.25), (x1 - 0.2, y1 + 0.02), (x1 - 0.4, y1 + 0.05)], fill=STEEL, outline=OUTLINE, width=0.015)
    c.line([(x0 + 0.3, y1 - 0.45), (x0 + 0.35, y0 + 0.5)], fill=hexc("#8a7a5a"), width=0.012)
    c.ellipse(cx - 0.15, y0 + 0.35, 0.04, 0.03, fill=PALE)                                            # etwas Helles unten


def _grabstein_hausherr(p, c, x0, y0, x1, y1, idx, rnd):
    """Grabstein des Hausherrn mit heutigem Datum, frisch gemeisselt, Rabe obendrauf."""
    cx = (x0 + x1) / 2
    w = (x1 - x0) / 2
    c.rect(x0 - 0.05, y0, x1 + 0.05, y0 + 0.08, fill=STONE_D, outline=OUTLINE, width=0.015)
    c.rect(x0, y0 + 0.08, x1, y0 + 0.9, fill=STONE_L, outline=OUTLINE, width=0.02)
    c.ellipse(cx, y0 + 0.9, w, 0.22, fill=STONE_L, outline=OUTLINE, width=0.02)
    c.rect(x0 + 0.02, y0 + 0.88, x1 - 0.02, y0 + 0.92, fill=STONE_L)
    c.text(cx, y0 + 0.72, "LORD HOLLOWMERE", 0.045, STONE_D)
    c.text(cx, y0 + 0.55, "1931", 0.045, STONE_D)
    c.text(cx, y0 + 0.4, "OCT 31", 0.05, hexc("#3a2a2a"))
    c.text(cx, y0 + 0.24, "THIS YEAR", 0.035, hexc("#3a2a2a"))
    moss(c, x0 + 0.05, y0 + 0.15, 0.06, seed=idx)
    c.ellipse(cx + 0.1, y0 + 1.14, 0.07, 0.05, fill=hexc("#141418"), outline=OUTLINE, width=0.01)     # Rabe
    c.ellipse(cx + 0.15, y0 + 1.2, 0.035, 0.03, fill=hexc("#141418"))
    c.poly([(cx + 0.18, y0 + 1.2), (cx + 0.24, y0 + 1.19), (cx + 0.18, y0 + 1.18)], fill=hexc("#8a8a30"))
    c.ellipse(cx + 0.16, y0 + 1.21, 0.006, 0.006, fill=RED)


def _kraehen(p, c, x0, y0, x1, y1, idx, rnd):
    """Drei Kraehen auf einem Grabstein, eine mit etwas Glaenzendem im Schnabel."""
    for k in range(3):
        bx = x0 + (x1 - x0) * (k + 0.5) / 3
        by = y0 + 1.0 + (k % 2) * 0.05
        c.ellipse(bx, by, 0.07, 0.05, fill=hexc("#141418"), outline=OUTLINE, width=0.01)
        c.ellipse(bx + (0.05 if k != 1 else -0.05), by + 0.06, 0.035, 0.03, fill=hexc("#141418"))
        bk = 1 if k != 1 else -1
        c.poly([(bx + bk * 0.08, by + 0.06), (bx + bk * 0.13, by + 0.055), (bx + bk * 0.08, by + 0.04)], fill=hexc("#8a8a30"))
        c.ellipse(bx + bk * 0.06, by + 0.07, 0.006, 0.006, fill=RED)
        if k == 2:
            c.ellipse(bx + 0.14, by + 0.05, 0.018, 0.014, fill=BRASS_L, outline=OUTLINE, width=0.006)


def _sarkophag(p, c, x0, y0, x1, y1, idx, rnd):
    """Steinsarkophag in der Gruft, Deckel verschoben, ein Spalt ins Dunkle, Reliefkreuz."""
    stone_block(p, x0, y0, x1, y1, 0, 0.9)
    fz = y0
    c.rect(x0 + 0.1, fz + 0.1, x1 - 0.1, fz + 0.9 * K - 0.1, outline=STONE_D, width=0.015)
    c.line([((x0 + x1) / 2, fz + 0.15), ((x0 + x1) / 2, fz + 0.9 * K - 0.15)], fill=STONE_D, width=0.02)
    c.line([((x0 + x1) / 2 - 0.15, fz + 0.9 * K - 0.3), ((x0 + x1) / 2 + 0.15, fz + 0.9 * K - 0.3)], fill=STONE_D, width=0.02)
    zt = y0 + 0.9 * K
    c.poly([(x0 + 0.05, zt + 0.02), (x1 - 0.25, zt + 0.02), (x1 - 0.25, y1 + 0.9 * K - 0.02), (x0 + 0.05, y1 + 0.9 * K - 0.02)], fill=hexc("#0b0d10"))
    c.poly([(x0 + 0.3, zt + 0.06), (x1 + 0.1, zt + 0.1), (x1 + 0.1, y1 + 1.0 * K), (x0 + 0.3, y1 + 1.0 * K - 0.04)], fill=STONE_L, outline=OUTLINE, width=0.02)
    c.line([(x0 + 0.5, zt + 0.3), (x1 - 0.1, zt + 0.32)], fill=STONE_D, width=0.015)
    crack(c, [(x0 + 0.6, zt + 0.1), (x0 + 0.7, zt + 0.25), (x0 + 0.65, zt + 0.4)], seed=idx)
    c.ellipse(x0 + 0.17, (zt + y1 + 0.9 * K) / 2, 0.025, 0.02, fill=PALE)
    cobweb(c, x1 + 0.1, y1 + 1.0 * K, 0.14, -1, -1, seed=idx)


def _tunnelausgang(p, c, x0, y0, x1, y1, idx, rnd):
    """Das andere Ende des Gruft-Tunnels in der Kapelle: Bodenplatte im Steinboden, Deckel einen Spalt
    verschoben, Eisenring, Erdkruemel und Kratzspuren davor."""
    cx = (x0 + x1) / 2
    c.rect(x0 - 0.06, y0 - 0.06, x1 + 0.06, y1 + 0.06, fill=STONE_D, outline=OUTLINE, width=0.022)
    c.rect(x0, y0, x1, y1, fill=hexc("#0b0d10"), outline=OUTLINE, width=0.015)
    # Deckplatte, nach Nordosten verschoben: der Spalt unten links bleibt dunkel
    c.rect(x0 + 0.1, y0 - 0.1, x1 + 0.08, y1 - 0.12, fill=STONE, outline=OUTLINE, width=0.02)
    c.line([(x0 + 0.16, y0 - 0.04), (x1 - 0.02, y0 - 0.04)], fill=alpha(hexc("#ffffff"), 60), width=0.012)
    for k in range(3):
        c.line([(x0 + 0.2 + k * 0.18, y0 + 0.02), (x0 + 0.26 + k * 0.18, y1 - 0.2)], fill=alpha(STONE_D, 160), width=0.008)
    # Eisenring mit Oese
    rx, ry = cx + 0.06, (y0 + y1) / 2 - 0.1
    c.ellipse(rx, ry, 0.07, 0.045, outline=OUTLINE, width=0.03)
    c.ellipse(rx, ry, 0.07, 0.045, outline=IRON, width=0.016)
    c.ellipse(rx, ry - 0.05, 0.02, 0.015, fill=IRON_D, outline=OUTLINE, width=0.008)
    # Kruemel und Kratzer auf dem Boden davor
    for k in range(7):
        c.ellipse(x0 + rnd.uniform(-0.1, x1 - x0 + 0.1), y1 + rnd.uniform(0.02, 0.16), 0.012, 0.009, fill=hexc("#4a3a2c"))
    for k in range(3):
        c.line([(x0 + 0.15 + k * 0.2, y1 + 0.06), (x0 + 0.3 + k * 0.2, y1 + 0.2)], fill=alpha(OUTLINE, 110), width=0.008)
    c.text(cx, y1 + 0.03, "UP", 0.03, alpha(CREAM, 110))


def _tunneleingang(p, c, x0, y0, x1, y1, idx, rnd):
    """Tunneleingang in der Gruft: Steinrahmen am Boden, Stufen ins Dunkle, Fackelschein von unten."""
    cx = (x0 + x1) / 2
    c.rect(x0 - 0.08, y0 - 0.08, x1 + 0.08, y1 + 0.08, fill=STONE, outline=OUTLINE, width=0.025)
    c.rect(x0, y0, x1, y1, fill=hexc("#0b0d10"), outline=OUTLINE, width=0.02)
    for k in range(4):
        sy = y1 - 0.12 - k * 0.2
        c.rect(x0 + 0.05 + k * 0.05, sy, x1 - 0.05 - k * 0.05, sy + 0.1, fill=shade(STONE_D, 1.0 - k * 0.18), outline=OUTLINE, width=0.01)
    c.glow(cx, y0 + 0.2, 0.3, hexc("#ff8a3c"), 0.3)
    for sx, sy in ((x0 - 0.04, y0 - 0.04), (x1 + 0.04, y0 - 0.04), (x0 - 0.04, y1 + 0.04), (x1 + 0.04, y1 + 0.04)):
        c.ellipse(sx, sy, 0.02, 0.02, fill=IRON, outline=OUTLINE, width=0.008)
    c.text(cx, y1 + 0.03, "DOWN", 0.03, alpha(CREAM, 130))
    moss(c, x1 + 0.05, y1 + 0.02, 0.07, seed=idx)


def _nischen_urnen(p, c, x0, y0, x1, y1, idx, rnd):
    """Steinnischen in der Gruftwand mit Urnen, eine Nische leer, eine mit Schaedel."""
    vertical = (y1 - y0) > (x1 - x0)
    n = 4
    for k in range(n):
        if vertical:
            cx = (x0 + x1) / 2
            ny = y0 + 1.0 * K + (y1 - y0) * (k + 0.5) / n * 0.6
        else:
            cx = x0 + (x1 - x0) * (k + 0.5) / n
            ny = y0 + 1.0 * K
        c.rect(cx - 0.17, ny - 0.1, cx + 0.17, ny + 0.28, fill=hexc("#0b0d10"), outline=OUTLINE, width=0.02)
        c.poly([(cx - 0.17, ny + 0.28), (cx + 0.17, ny + 0.28), (cx + 0.12, ny + 0.36), (cx - 0.12, ny + 0.36)], fill=STONE_D, outline=OUTLINE, width=0.015)
        if k == 1:
            continue
        if k == 3:
            c.ellipse(cx, ny + 0.08, 0.06, 0.07, fill=PALE, outline=OUTLINE, width=0.012)
            c.ellipse(cx - 0.02, ny + 0.09, 0.012, 0.016, fill=OUTLINE)
            c.ellipse(cx + 0.02, ny + 0.09, 0.012, 0.016, fill=OUTLINE)
        else:
            c.poly([(cx - 0.07, ny - 0.06), (cx + 0.07, ny - 0.06), (cx + 0.09, ny + 0.12), (cx + 0.05, ny + 0.2), (cx - 0.05, ny + 0.2), (cx - 0.09, ny + 0.12)], fill=hexc("#7a6a5a"), outline=OUTLINE, width=0.012)
            c.ellipse(cx, ny + 0.2, 0.05, 0.02, fill=hexc("#8a7a6a"), outline=OUTLINE, width=0.01)
            c.line([(cx - 0.05, ny + 0.05), (cx + 0.05, ny + 0.05)], fill=BRASS_D, width=0.01)


def _wandfackel(p, c, x0, y0, x1, y1, idx, rnd):
    """Wandfackel in eiserner Halterung, brennt, Russfahne an der Wand."""
    cx = (x0 + x1) / 2
    hy = y0 + 1.3 * K
    c.poly([(cx - 0.05, hy), (cx + 0.05, hy), (cx + 0.04, hy + 0.12), (cx - 0.04, hy + 0.12)], fill=IRON, outline=OUTLINE, width=0.012)
    c.line([(cx, hy + 0.12), (cx, hy + 0.45)], fill=OUTLINE, width=0.05)
    c.line([(cx, hy + 0.12), (cx, hy + 0.45)], fill=WALNUT_D, width=0.03)
    c.ellipse(cx, hy + 0.47, 0.05, 0.03, fill=hexc("#3a2a1a"), outline=OUTLINE, width=0.012)
    flame(c, cx, hy + 0.48, 1.4)
    c.poly([(cx - 0.06, hy + 0.6), (cx + 0.06, hy + 0.6), (cx + 0.1, hy + 1.0), (cx - 0.1, hy + 1.0)], fill=alpha((20, 18, 18, 255), 110))
    VA.floor_light(c, cx, y0 - 0.05, 0.9, 0.45, WARM, 0.3, seed=idx)


def _zerbrochene_urne(p, c, x0, y0, x1, y1, idx, rnd):
    """Zerbrochene Urne am Boden, Asche verstreut, ein Ring darin."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c.ellipse(cx, cy, 0.25, 0.1, fill=alpha(hexc("#8a8a8a"), 140))
    c.poly([(cx - 0.15, cy - 0.02), (cx - 0.02, cy - 0.04), (cx - 0.01, cy + 0.1), (cx - 0.16, cy + 0.08)], fill=hexc("#7a6a5a"), outline=OUTLINE, width=0.012)
    c.poly([(cx + 0.03, cy + 0.02), (cx + 0.14, cy - 0.01), (cx + 0.16, cy + 0.08), (cx + 0.05, cy + 0.1)], fill=hexc("#7a6a5a"), outline=OUTLINE, width=0.012)
    c.poly([(cx + 0.18, cy - 0.06), (cx + 0.26, cy - 0.08), (cx + 0.24, cy + 0.0)], fill=hexc("#7a6a5a"), outline=OUTLINE, width=0.01)
    c.ellipse(cx - 0.02, cy + 0.0, 0.02, 0.012, outline=BRASS_L, width=0.008)
    for _ in range(8):
        c.ellipse(cx + rnd.uniform(-0.28, 0.28), cy + rnd.uniform(-0.1, 0.1), 0.012, 0.008, fill=alpha(hexc("#b0b0b0"), 150))


GARDEN_H = {
    "kamerakran": 2.8, "statue_schleier": 2.6, "gartentisch": 1.0, "kuebelpflanze": 1.5, "vogelschwarm": 0.6, "van": 2.3,
    "lichtstativ": 2.5, "campingtisch": 0.9, "kabeltrommel": 0.7, "dixi": 2.4, "zelt_aufgeschlitzt": 2.6, "schlafsack": 0.3,
    "riesenpflanze": 2.2, "giesskannen": 0.7, "schlauchtrommel": 1.0, "kletterpflanzen": 2.1, "sonnenuhr": 1.2,
    "parkbank": 1.0, "brunnen_blut": 1.6, "engelsstatue": 2.8, "offenes_grab": 1.0, "grabstein_hausherr": 1.4,
    "kraehen": 1.3, "sarkophag": 1.1, "tunneleingang": 0.3, "nischen_urnen": 2.1, "wandfackel": 2.2, "zerbrochene_urne": 0.3,
    "tunnelausgang": 0.3,
}
GARDEN_PAD = {"kamerakran": 0.8, "lichtstativ": 0.6, "wandfackel": 0.9, "riesenpflanze": 0.9, "van": 0.5,
              "gartentisch": 0.6, "brunnen_blut": 0.6, "kletterpflanzen": 0.6, "kuebelpflanze": 0.5, "kabeltrommel": 0.7,
              "schlauchtrommel": 0.6, "offenes_grab": 0.5, "grabstein_hausherr": 0.4, "nischen_urnen": 0.5,
              "tunneleingang": 0.4, "zerbrochene_urne": 0.4, "giesskannen": 0.4, "kraehen": 0.4, "vogelschwarm": 0.4,
              "tunnelausgang": 0.4}
GARDEN_NO_SHADOW = {"vogelschwarm", "schlafsack", "kletterpflanzen", "brunnen_blut", "kraehen", "nischen_urnen",
                    "wandfackel", "zerbrochene_urne", "tunneleingang", "offenes_grab", "tunnelausgang"}

register(GARDEN_H, GARDEN_PAD, GARDEN_NO_SHADOW, {k: globals()["_" + k] for k in GARDEN_H})
