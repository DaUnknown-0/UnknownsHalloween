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
    """Verschleierte Gartenstatue, neu 24.10.: Stufensockel mit Efeu und Moos, Frauenfigur im langen Gewand mit
    Faltenwurf, Haende halten eine Rose vor der Brust, Schleier ueber Kopf und Schultern, Gesicht nur angedeutet
    und leicht zur Seite gedreht, Flechten, Riss."""
    cx = (x0 + x1) / 2
    stone_block(p, x0, y0, x1, y1, 0, 0.3)
    stone_block(p, x0 + 0.1, y0 + 0.1, x1 - 0.1, y1 - 0.1, 0.3, 0.25)
    base = y0 + 0.1 + 0.55 * K
    moss(c, x0 + 0.1, y0 + 0.05, 0.1, seed=idx)
    moss(c, x1 - 0.1, y0 + 0.15, 0.08, seed=idx + 1)
    ivy = VA.HD.wobble([(x1 - 0.05, y0 + 0.02), (x1 - 0.25, y0 + 0.12), (x1 - 0.15, y0 + 0.26), (x1 - 0.35, y0 + 0.36)], amp=0.02, seed=idx, step=0.05)
    c.line(ivy, fill=hexc("#2e4a30"), width=0.014)
    for k, (lx, ly) in enumerate(ivy[::2]):
        c.poly([(lx, ly + 0.03), (lx + 0.03, ly), (lx, ly - 0.03), (lx - 0.03, ly)], fill=LEAF if k % 2 else LEAF_D, outline=alpha(OUTLINE, 200), width=0.006)
    gown = VA.HD.wobble([(cx - 0.3, base), (cx + 0.3, base), (cx + 0.24, base + 0.6), (cx + 0.19, base + 1.1), (cx - 0.19, base + 1.1), (cx - 0.24, base + 0.6)],
                        amp=0.012, seed=idx, step=0.06, closed=True)
    c.poly(gown, fill=STONE_L, outline=OUTLINE, width=0.025)
    for k in range(5):
        c.line(VA.HD.wobble([(cx - 0.16 + k * 0.08, base + 1.05), (cx - 0.22 + k * 0.11, base + 0.04)], amp=0.01, seed=idx + k, step=0.05), fill=alpha(STONE_D, 140), width=0.013)
    c.line([(cx - 0.21, base + 0.1), (cx - 0.15, base + 1.0)], fill=alpha((255, 255, 255, 255), 90), width=0.02)
    for k in range(4):                                                                                   # Saum
        c.ellipse(cx - 0.22 + k * 0.15, base, 0.07, 0.03, fill=STONE_L, outline=OUTLINE, width=0.012)
    c.rect(cx - 0.17, base + 1.05, cx + 0.17, base + 1.1, fill=STONE_D, outline=OUTLINE, width=0.012)        # Guertel
    c.poly([(cx - 0.2, base + 1.1), (cx + 0.2, base + 1.1), (cx + 0.17, base + 1.42), (cx - 0.17, base + 1.42)], fill=STONE_L, outline=OUTLINE, width=0.025)
    for s in (-1, 1):                                                                                    # Arme zur Brust
        c.line([(cx + s * 0.18, base + 1.38), (cx + s * 0.27, base + 1.18), (cx + s * 0.06, base + 1.2)], fill=OUTLINE, width=0.07)
        c.line([(cx + s * 0.18, base + 1.38), (cx + s * 0.27, base + 1.18), (cx + s * 0.06, base + 1.2)], fill=STONE_L, width=0.042)
    c.ellipse(cx, base + 1.21, 0.07, 0.05, fill=shade(STONE_L, 1.08), outline=OUTLINE, width=0.015)        # Haende
    c.line([(cx, base + 1.24), (cx + 0.02, base + 1.4)], fill=hexc("#2e4a30"), width=0.012)                  # Rose
    c.ellipse(cx + 0.02, base + 1.42, 0.035, 0.03, fill=hexc("#9a2a3a"), outline=OUTLINE, width=0.01)
    c.ellipse(cx + 0.01, base + 1.43, 0.015, 0.012, fill=hexc("#c84a5a"))
    hy = base + 1.56
    c.poly([(cx - 0.3, base + 1.4), (cx + 0.3, base + 1.4), (cx + 0.22, hy + 0.12), (cx + 0.1, hy + 0.24), (cx - 0.1, hy + 0.24), (cx - 0.22, hy + 0.12)],
           fill=STONE_L, outline=OUTLINE, width=0.025)                                                   # Schleier
    for k in range(3):
        c.line([(cx - 0.2 + k * 0.2, hy + 0.1), (cx - 0.26 + k * 0.26, base + 1.42)], fill=alpha(STONE_D, 130), width=0.012)
    c.ellipse(cx + 0.02, hy, 0.13, 0.15, fill=STONE, outline=OUTLINE, width=0.022)                           # Gesicht, leicht gedreht
    c.ellipse(cx + 0.075, hy + 0.02, 0.016, 0.018, fill=STONE_D)
    c.ellipse(cx + 0.125, hy + 0.025, 0.014, 0.016, fill=STONE_D)
    c.line([(cx + 0.09, hy - 0.06), (cx + 0.13, hy - 0.06)], fill=alpha(STONE_D, 170), width=0.01)
    c.line([(cx - 0.08, hy + 0.2), (cx + 0.1, hy + 0.2)], fill=alpha((255, 255, 255, 255), 90), width=0.015)
    crack(c, [(cx + 0.1, base + 0.3), (cx + 0.05, base + 0.6), (cx + 0.12, base + 0.8)], seed=idx)
    for k in range(5):
        c.ellipse(cx + rnd.uniform(-0.2, 0.2), base + rnd.uniform(0.1, 1.0), 0.02, 0.012, fill=alpha(hexc("#b8c070"), 150))
    cobweb(c, cx - 0.22, base + 1.4, 0.1, -1, -1, seed=idx)


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
    """Vor dem Brunnen gezeichnet: rotes Wasser im ovalen Becken (Geometrie wie villa_art._brunnen: Beckenmitte
    1,4 m noerdlich der Standlinie dieses Sprites, Wasser rx 0,94 / ry 0,59 auf Beckenhoehe) und die Figur
    noch einmal darueber, damit sie vor dem Wasser steht; Tropfen am Beckenrand."""
    cx = (x0 + x1) / 2
    # Beckenmitte (Brunnenkreis 31/31 Plan, cy - 0,05) liegt 1,4 m noerdlich dieser Standlinie (Plan-y 32,45);
    # Wasserspiegel auf der Wandungsoberkante (+ 0,5 K)
    wy = y0 + 1.4 + 0.5 * K
    c.ellipse(cx, wy, 0.94, 0.59, fill=WATER_RED)
    c.ellipse(cx, wy + 0.02, 0.86, 0.53, fill=alpha(hexc("#8a1a26"), 200))
    c.ellipse(cx - 0.3, wy + 0.1, 0.25, 0.07, fill=alpha(hexc("#b03848"), 120))
    c.ellipse(cx + 0.35, wy - 0.05, 0.16, 0.05, fill=alpha(hexc("#b03848"), 120))
    for k in range(3):
        c.ellipse(cx, wy + 0.06, 0.4 + k * 0.14, 0.14 + k * 0.05, outline=alpha(hexc("#d06070"), 70 - k * 15), width=0.012)
    VA.fountain_statue(c, cx, wy + 0.12, idx)
    blood_drips(c, cx + 0.5, wy - 0.45, 3, 0.15, seed=idx)
    blood_drips(c, cx - 0.7, wy - 0.3, 2, 0.1, seed=idx + 1)


# ------------------------------------------------------------------ Friedhof, Gruft

def _engelsstatue(p, c, x0, y0, x1, y1, idx, rnd):
    """Trauernder Friedhofsengel, neu 24.10.: zweistufiger Sockel mit Inschrift REST, Engel im langen Gewand mit
    Faltenwurf, Kopf gesenkt, Gesicht in den Haenden, grosse gesenkte Fluegel mit drei Federreihen, Moos, Flechten,
    Riss durch das Gewand, verwelkter Kranz am Sockel."""
    cx = (x0 + x1) / 2
    stone_block(p, x0, y0, x1, y1, 0, 0.35)
    stone_block(p, x0 + 0.08, y0 + 0.08, x1 - 0.08, y1 - 0.08, 0.35, 0.3)
    c.rect(x0 + 0.16, y0 + 0.08 + 0.4 * K, x1 - 0.16, y0 + 0.08 + 0.6 * K, outline=alpha(STONE_D, 200), width=0.01)
    c.text(cx, y0 + 0.08 + 0.5 * K, "REST", 0.045, STONE_D)
    base = y0 + 0.08 + 0.65 * K
    moss(c, x0 + 0.15, y0 + 0.05, 0.1, seed=idx)
    moss(c, x1 - 0.2, y0 + 0.1 + 0.3 * K, 0.08, seed=idx + 1)
    # Fluegel (hinter dem Koerper), drei Federreihen
    for s in (-1, 1):
        wing = [(cx + s * 0.1, base + 0.5), (cx + s * 0.3, base + 0.9), (cx + s * 0.55, base + 1.45), (cx + s * 0.64, base + 1.2),
                (cx + s * 0.6, base + 0.75), (cx + s * 0.5, base + 0.4), (cx + s * 0.3, base + 0.2)]
        c.poly(wing, fill=STONE_L, outline=OUTLINE, width=0.025)
        for row in range(3):
            for k in range(4):
                t = 0.15 + k * 0.22
                fx = cx + s * (0.14 + 0.44 * t + row * 0.04)
                fy = base + 0.25 + 1.0 * t - row * 0.16
                c.line([(fx, fy), (fx - s * 0.03, fy - 0.14)], fill=alpha(STONE_D, 150), width=0.01)
                c.ellipse(fx - s * 0.03, fy - 0.15, 0.025, 0.018, outline=alpha(STONE_D, 150), width=0.008)
        c.line([(cx + s * 0.32, base + 0.92), (cx + s * 0.54, base + 1.4)], fill=alpha((255, 255, 255, 255), 90), width=0.015)
    # Gewand mit Falten, Saum, Fuss
    gown = VA.HD.wobble([(cx - 0.3, base), (cx + 0.3, base), (cx + 0.22, base + 0.7), (cx + 0.18, base + 1.15), (cx - 0.18, base + 1.15), (cx - 0.22, base + 0.7)],
                        amp=0.012, seed=idx, step=0.06, closed=True)
    c.poly(gown, fill=STONE_L, outline=OUTLINE, width=0.025)
    for k in range(5):
        c.line(VA.HD.wobble([(cx - 0.14 + k * 0.07, base + 1.1), (cx - 0.22 + k * 0.11, base + 0.04)], amp=0.01, seed=idx + k, step=0.05), fill=alpha(STONE_D, 140), width=0.013)
    c.line([(cx - 0.2, base + 0.1), (cx - 0.14, base + 1.05)], fill=alpha((255, 255, 255, 255), 90), width=0.02)
    for k in range(4):
        c.ellipse(cx - 0.22 + k * 0.15, base, 0.07, 0.03, fill=STONE_L, outline=OUTLINE, width=0.012)
    c.ellipse(cx + 0.08, base + 0.02, 0.07, 0.03, fill=STONE, outline=OUTLINE, width=0.012)                   # Fuss
    # Oberkoerper gebeugt, Arme zum Gesicht, Kopf gesenkt mit Haar
    c.poly([(cx - 0.2, base + 1.15), (cx + 0.2, base + 1.15), (cx + 0.16, base + 1.42), (cx - 0.16, base + 1.42)], fill=STONE_L, outline=OUTLINE, width=0.025)
    hy = base + 1.5
    c.ellipse(cx, hy, 0.13, 0.14, fill=STONE_L, outline=OUTLINE, width=0.025)                                 # Kopf
    c.ellipse(cx - 0.01, hy + 0.08, 0.14, 0.08, fill=STONE, outline=OUTLINE, width=0.015)                      # Haar
    for k in range(4):
        c.line([(cx - 0.1 + k * 0.06, hy + 0.14), (cx - 0.12 + k * 0.07, hy + 0.02)], fill=alpha(STONE_D, 150), width=0.01)
    for s in (-1, 1):
        c.line([(cx + s * 0.18, base + 1.3), (cx + s * 0.2, base + 1.42), (cx + s * 0.06, hy - 0.02)], fill=OUTLINE, width=0.07)
        c.line([(cx + s * 0.18, base + 1.3), (cx + s * 0.2, base + 1.42), (cx + s * 0.06, hy - 0.02)], fill=STONE_L, width=0.042)
    c.poly([(cx - 0.1, hy - 0.1), (cx + 0.1, hy - 0.1), (cx + 0.11, hy + 0.05), (cx - 0.11, hy + 0.05)], fill=shade(STONE_L, 1.1), outline=OUTLINE, width=0.015)   # Haende
    for k in range(5):
        c.line([(cx - 0.08 + k * 0.04, hy - 0.08), (cx - 0.08 + k * 0.04, hy + 0.03)], fill=alpha(STONE_D, 170), width=0.006)
    c.ellipse(cx + 0.045, hy - 0.02, 0.01, 0.014, fill=hexc("#1a1c22"))                                      # ein Auge zwischen den Fingern
    crack(c, [(cx - 0.1, base + 0.2), (cx - 0.05, base + 0.5), (cx - 0.12, base + 0.8)], seed=idx)
    for k in range(6):
        c.ellipse(cx + rnd.uniform(-0.45, 0.45), base + rnd.uniform(0.2, 1.2), 0.02, 0.012, fill=alpha(hexc("#b8c070"), 150))
    # verwelkter Kranz am Sockel
    kx, ky = x1 - 0.2, y0 + 0.06
    for k in range(10):
        a = k / 10 * math.tau
        c.ellipse(kx + 0.1 * math.cos(a), ky + 0.07 * math.sin(a), 0.03, 0.022, fill=hexc("#6a5a3a") if k % 2 else hexc("#7a6a46"), outline=OUTLINE, width=0.006)
    c.poly([(kx - 0.03, ky - 0.08), (kx + 0.03, ky - 0.08), (kx + 0.02, ky - 0.2), (kx - 0.02, ky - 0.2)], fill=hexc("#5a2a3a"), outline=OUTLINE, width=0.006)


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


# ------------------------------------------------------------------ Maske (User 24.10.: Garderobe "wie frueher") und Crew Camp

def _schminkspiegel(p, c, x0, y0, x1, y1, idx, rnd):
    """Schminktisch an der Nordwand (2,6 x 0,45 m): Tisch mit drei Schubladen und Messingknoepfen, grosser Spiegel mit
    Gluehbirnenrahmen an drei Seiten (eine Birne durchgebrannt), auf der Platte Schminkdosen, Puderdose mit Quaste,
    Tiegel, Pinselbecher, Lippenstifte, Parfumflakon mit Zerstaeuber, ein Handtuch."""
    w = x1 - x0
    cx = (x0 + x1) / 2
    p.box(x0, y0, x1, y1, 0, 0.78, WALNUT_L, WALNUT)
    n = 3
    for k in range(n):
        dx0 = x0 + 0.08 + k * (w - 0.16) / n
        dx1 = dx0 + (w - 0.16) / n - 0.06
        c.rect(dx0, y0 + 0.18 * K, dx1, y0 + 0.64 * K, fill=shade(WALNUT, 0.92), outline=WALNUT_D, width=0.015)
        c.ellipse((dx0 + dx1) / 2, y0 + 0.41 * K, 0.022, 0.018, fill=BRASS, outline=OUTLINE, width=0.01)
    c.rect(x0 + 0.02, y0 + 0.02, x1 - 0.02, y0 + 0.07, fill=WALNUT_D)
    ty = y0 + 0.78 * K
    # Spiegel mit Rahmen an der Rueckwand
    mx0, mx1 = x0 + 0.3, x1 - 0.3
    my = y1 + 0.78 * K
    gy0, gy1 = my + 0.12, my + 1.05
    c.rect(mx0 - 0.1, gy0 - 0.1, mx1 + 0.1, gy1 + 0.1, fill=MATTE, outline=OUTLINE, width=0.025)
    c.rect(mx0, gy0, mx1, gy1, fill=hexc("#aebfd0"), outline=OUTLINE, width=0.02)
    c.line([(mx0 + 0.15, gy0 + 0.08), (mx0 + 0.5, gy1 - 0.08)], fill=alpha((255, 255, 255, 255), 110), width=0.06)
    c.line([(mx0 + 0.65, gy0 + 0.08), (mx0 + 0.85, gy1 - 0.15)], fill=alpha((255, 255, 255, 255), 70), width=0.035)
    c.rect(mx1 - 0.45, gy1 - 0.3, mx1 - 0.1, gy1 - 0.08, fill=CREAM, outline=OUTLINE, width=0.01)            # Zettel im Rahmen
    for k in range(3):
        c.line([(mx1 - 0.41, gy1 - 0.26 + k * 0.06), (mx1 - 0.15, gy1 - 0.26 + k * 0.06)], fill=alpha(OUTLINE, 110), width=0.006)
    pts = [(mx0 - 0.05, gy0 + 0.05 + k * (gy1 - gy0 - 0.1) / 4) for k in range(5)]
    pts += [(mx1 + 0.05, gy0 + 0.05 + k * (gy1 - gy0 - 0.1) / 4) for k in range(5)]
    nb = max(4, int((mx1 - mx0) / 0.22))
    pts += [(mx0 + (mx1 - mx0) * (k + 0.5) / nb, gy1 + 0.05) for k in range(nb)]
    c.glow(cx, (gy0 + gy1) / 2, 1.2, WARM, 0.22)
    bulb = hexc("#ffe6a8")
    for k, (bx, by) in enumerate(pts):
        dead = (k * 7 + idx) % 13 == 0
        if not dead:
            c.glow(bx, by, 0.17, bulb, 0.55)
        c.ellipse(bx, by, 0.035, 0.035, fill=(bulb if not dead else hexc("#6a6050")), outline=OUTLINE, width=0.012)
        c.ellipse(bx - 0.01, by + 0.012, 0.01, 0.008, fill=(255, 255, 255, 200 if not dead else 60))
    # Platte: Spitzendeckchen, dann die Dinge (von links nach rechts)
    c.ellipse(x0 + 0.55, ty + 0.2, 0.3, 0.12, fill=alpha(CREAM, 170))
    def tin(x, y, r, col, lid=True, label=None):
        c.ellipse(x, y, r, r * 0.5, fill=shade(col, 0.8), outline=OUTLINE, width=0.012)
        c.rect(x - r, y, x + r, y + r * 0.6, fill=col)
        c.line([(x - r, y), (x - r, y + r * 0.6)], fill=OUTLINE, width=0.012)
        c.line([(x + r, y), (x + r, y + r * 0.6)], fill=OUTLINE, width=0.012)
        c.ellipse(x, y + r * 0.6, r, r * 0.5, fill=shade(col, 1.2) if lid else shade(col, 0.6), outline=OUTLINE, width=0.012)
        if label:
            c.rect(x - r * 0.6, y + r * 0.15, x + r * 0.6, y + r * 0.45, fill=label)
    tin(x0 + 0.3, ty + 0.14, 0.09, hexc("#c8b070"), label=hexc("#a02a34"))                              # Schminkdose
    tin(x0 + 0.52, ty + 0.1, 0.07, hexc("#d8d0c8"), label=hexc("#4a6ab0"))
    tin(x0 + 0.5, ty + 0.3, 0.1, hexc("#e0c8d0"), lid=False)                                               # Puderdose offen
    c.ellipse(x0 + 0.5, ty + 0.3 + 0.06, 0.07, 0.035, fill=hexc("#f0e0d8"))
    c.ellipse(x0 + 0.66, ty + 0.36, 0.06, 0.045, fill=hexc("#f4ece4"), outline=OUTLINE, width=0.012)        # Quaste
    c.line([(x0 + 0.66, ty + 0.4), (x0 + 0.66, ty + 0.46)], fill=hexc("#d8a0b0"), width=0.015)
    for k, col in enumerate((hexc("#c0302a"), hexc("#a02a4a"), hexc("#d06a3a"))):                          # Lippenstifte
        lx = x0 + 0.84 + k * 0.08
        c.rect(lx - 0.02, ty + 0.1, lx + 0.02, ty + 0.2, fill=hexc("#2a2a30"), outline=OUTLINE, width=0.01)
        c.poly([(lx - 0.016, ty + 0.2), (lx + 0.016, ty + 0.2), (lx + 0.016, ty + 0.27), (lx - 0.016, ty + 0.3)], fill=col, outline=OUTLINE, width=0.008)
    tin(x0 + 1.12, ty + 0.3, 0.065, hexc("#4a6a5a"), label=hexc("#e8d8a0"))                                 # Tiegel
    tin(x0 + 1.3, ty + 0.16, 0.055, hexc("#8a3a4a"))
    bx, by = cx + 0.2, ty + 0.14                                                                            # Pinselbecher
    c.rect(bx - 0.07, by, bx + 0.07, by + 0.16, fill=hexc("#6a8aa0"), outline=OUTLINE, width=0.012)
    c.ellipse(bx, by + 0.16, 0.07, 0.03, fill=hexc("#5a7a90"), outline=OUTLINE, width=0.012)
    for k, (dx, h_, col) in enumerate(((-0.04, 0.26, hexc("#8a6a4a")), (0.0, 0.32, hexc("#2a2a30")), (0.04, 0.24, hexc("#c8b070")))):
        c.line([(bx + dx, by + 0.14), (bx + dx * 1.6, by + h_)], fill=OUTLINE, width=0.028)
        c.line([(bx + dx, by + 0.14), (bx + dx * 1.6, by + h_)], fill=WALNUT_L, width=0.014)
        c.ellipse(bx + dx * 1.6, by + h_ + 0.02, 0.02, 0.03, fill=col, outline=OUTLINE, width=0.008)
    fx, fy = x1 - 0.5, ty + 0.3                                                                             # Parfumflakon
    c.poly([(fx - 0.07, fy), (fx + 0.07, fy), (fx + 0.06, fy + 0.16), (fx - 0.06, fy + 0.16)], fill=alpha(hexc("#9fc4e0"), 200), outline=OUTLINE, width=0.012)
    c.rect(fx - 0.05, fy + 0.02, fx + 0.05, fy + 0.1, fill=alpha(hexc("#d8a0b0"), 200))
    c.rect(fx - 0.025, fy + 0.16, fx + 0.025, fy + 0.22, fill=BRASS, outline=OUTLINE, width=0.01)
    c.ellipse(fx + 0.1, fy + 0.2, 0.035, 0.03, fill=hexc("#8a2a3a"), outline=OUTLINE, width=0.01)            # Zerstaeuberball
    c.line([(fx + 0.025, fy + 0.19), (fx + 0.07, fy + 0.2)], fill=OUTLINE, width=0.012)
    c.line([(fx - 0.04, fy + 0.03), (fx - 0.035, fy + 0.13)], fill=(255, 255, 255, 150), width=0.01)
    c.rect(x1 - 0.3, ty + 0.06, x1 - 0.06, ty + 0.16, fill=hexc("#e8e0d0"), outline=OUTLINE, width=0.012)   # Handtuch
    c.line([(x1 - 0.27, ty + 0.11), (x1 - 0.09, ty + 0.11)], fill=hexc("#a02a34"), width=0.012)
    tin(x1 - 0.22, ty + 0.3, 0.06, hexc("#c8b070"), label=hexc("#2a5a8a"))
    c.rect(x1 - 0.55, ty + 0.04, x1 - 0.42, ty + 0.1, fill=hexc("#f0e0d8"), outline=OUTLINE, width=0.008)   # Schwaemmchen


def _dosenregal(p, c, x0, y0, x1, y1, idx, rnd):
    """Hohes Regal an der Suedwand der Maske (1,7 x 0,5 m): vier Boeden mit gestapelten Blechdosen (rund, mit
    Etikett), Fettschminke-Tuben, runden Hutschachteln mit Streifen, einem Perueckenblock, Puderquasten und einer
    Schale, Flasche Haarwasser, Zettel am Regalpfosten."""
    w = x1 - x0
    H = 2.1
    p.box(x0, y0, x1, y1, 0, H, WALNUT_L, WALNUT)
    fb = y0
    boards = [fb + 0.1, fb + 0.4, fb + 0.7, fb + 1.0]
    c.rect(x0 + 0.03, fb + 0.03, x1 - 0.03, H * K + fb - 0.03, fill=shade(WALNUT, 0.72))                      # Rueckwand (dunkel)
    for k in range(5):                                                                                       # Regalpfosten-Fugen
        c.line([(x0 + 0.04 + k * (w - 0.08) / 4, fb + 0.05), (x0 + 0.04 + k * (w - 0.08) / 4, fb + H * K - 0.05)], fill=alpha(WALNUT_D, 120), width=0.008)
    gold, red, blue, green, cream = hexc("#c8b070"), hexc("#a02a34"), hexc("#2a5a8a"), hexc("#4a6a5a"), hexc("#e8e0d0")

    def tin(x, y, r, h, col, label=None):
        c.rect(x - r, y, x + r, y + h, fill=col, outline=OUTLINE, width=0.012)
        c.ellipse(x, y + h, r, r * 0.4, fill=shade(col, 1.25), outline=OUTLINE, width=0.012)
        c.line([(x - r + 0.015, y + 0.02), (x - r + 0.015, y + h - 0.02)], fill=shade(col, 1.3), width=0.01)
        if label:
            c.rect(x - r * 0.65, y + h * 0.3, x + r * 0.65, y + h * 0.65, fill=label)

    def hatbox(x, y, r, h, col, stripe):
        c.rect(x - r, y, x + r, y + h, fill=col, outline=OUTLINE, width=0.014)
        for k in range(int(2 * r / 0.06)):
            if k % 2 == 0:
                c.rect(x - r + k * 0.06 + 0.01, y + 0.01, x - r + (k + 1) * 0.06 - 0.005, y + h - 0.01, fill=stripe)
        c.ellipse(x, y + h, r, r * 0.4, fill=shade(col, 1.2), outline=OUTLINE, width=0.014)
        c.line([(x - r * 0.4, y + h + r * 0.3), (x, y + h + r * 0.55), (x + r * 0.4, y + h + r * 0.3)], fill=OUTLINE, width=0.02)

    for i, by in enumerate(boards):
        c.rect(x0 + 0.03, by, x1 - 0.03, by + 0.04, fill=WALNUT_L, outline=OUTLINE, width=0.012)              # Brett
        c.rect(x0 + 0.03, by - 0.01, x1 - 0.03, by, fill=alpha((0, 0, 0, 255), 90))
    # Boden 0: grosse Dosen, Hutschachtel
    tin(x0 + 0.2, boards[0] + 0.04, 0.12, 0.18, gold, red)
    tin(x0 + 0.46, boards[0] + 0.04, 0.1, 0.14, blue, cream)
    tin(x0 + 0.46, boards[0] + 0.22, 0.08, 0.1, red, cream)
    hatbox(x0 + 0.85, boards[0] + 0.04, 0.17, 0.2, cream, hexc("#8a4a5a"))
    hatbox(x1 - 0.3, boards[0] + 0.04, 0.14, 0.17, hexc("#4a6a8a"), cream)
    # Boden 1: Fettschminke-Tuben, Dosenstapel, Flasche
    for k, col in enumerate((red, hexc("#e0c080"), green, hexc("#d08060"), blue, cream)):
        tx = x0 + 0.12 + k * 0.09
        c.poly([(tx - 0.025, boards[1] + 0.04), (tx + 0.025, boards[1] + 0.04), (tx + 0.03, boards[1] + 0.2), (tx - 0.03, boards[1] + 0.2)], fill=col, outline=OUTLINE, width=0.01)
        c.rect(tx - 0.015, boards[1] + 0.2, tx + 0.015, boards[1] + 0.24, fill=hexc("#2a2a30"), outline=OUTLINE, width=0.008)
        c.rect(tx - 0.02, boards[1] + 0.09, tx + 0.02, boards[1] + 0.15, fill=cream)
    for k in range(3):
        tin(x0 + 0.78, boards[1] + 0.04 + k * 0.07, 0.09, 0.07, (gold, red, blue)[k], cream)
    tin(x0 + 1.0, boards[1] + 0.04, 0.07, 0.1, green, gold)
    bx = x1 - 0.3
    c.rect(bx - 0.045, boards[1] + 0.04, bx + 0.045, boards[1] + 0.2, fill=alpha(hexc("#7ab0c8"), 220), outline=OUTLINE, width=0.01)   # Haarwasser
    c.rect(bx - 0.02, boards[1] + 0.2, bx + 0.02, boards[1] + 0.26, fill=BRASS, outline=OUTLINE, width=0.008)
    c.rect(bx - 0.035, boards[1] + 0.08, bx + 0.035, boards[1] + 0.15, fill=cream)
    tin(x1 - 0.13, boards[1] + 0.04, 0.06, 0.08, cream, red)
    # Boden 2: Perueckenblock, Puderquasten in Schale, Dosen
    hx = x0 + 0.25
    c.rect(hx - 0.03, boards[2] + 0.04, hx + 0.03, boards[2] + 0.1, fill=WALNUT_D, outline=OUTLINE, width=0.01)
    c.ellipse(hx, boards[2] + 0.2, 0.08, 0.1, fill=hexc("#c8b8a0"), outline=OUTLINE, width=0.012)             # Block
    c.ellipse(hx - 0.03, boards[2] + 0.21, 0.01, 0.008, fill=alpha(OUTLINE, 120))
    c.ellipse(hx + 0.03, boards[2] + 0.21, 0.01, 0.008, fill=alpha(OUTLINE, 120))
    for k in range(4):                                                                                       # Haarnadeln im Block
        c.line([(hx - 0.04 + k * 0.025, boards[2] + 0.28), (hx - 0.05 + k * 0.03, boards[2] + 0.34)], fill=hexc("#2a2a30"), width=0.006)
    sx = x0 + 0.62
    c.ellipse(sx, boards[2] + 0.07, 0.14, 0.05, fill=hexc("#6a8aa0"), outline=OUTLINE, width=0.012)             # Schale
    for k in range(3):
        c.ellipse(sx - 0.07 + k * 0.07, boards[2] + 0.1 + (k % 2) * 0.03, 0.05, 0.04, fill=hexc("#f4ece4"), outline=OUTLINE, width=0.01)
    tin(x0 + 1.0, boards[2] + 0.04, 0.1, 0.12, red, gold)
    tin(x0 + 1.22, boards[2] + 0.04, 0.08, 0.09, cream, blue)
    tin(x1 - 0.2, boards[2] + 0.04, 0.11, 0.16, hexc("#2a2a30"), gold)
    # Boden 3 (oben): Hutschachteln, flache Dosen
    hatbox(x0 + 0.25, boards[3] + 0.04, 0.18, 0.22, hexc("#8a4a5a"), cream)
    hatbox(x0 + 0.65, boards[3] + 0.04, 0.14, 0.16, cream, hexc("#4a6a8a"))
    for k in range(3):
        tin(x0 + 1.05, boards[3] + 0.04 + k * 0.06, 0.1, 0.06, (blue, gold, cream)[k])
    tin(x1 - 0.22, boards[3] + 0.04, 0.09, 0.12, gold, red)
    c.rect(x1 - 0.14, fb + 0.5, x1 - 0.04, fb + 0.64, fill=CREAM, outline=OUTLINE, width=0.008)                # Zettel am Pfosten
    for k in range(3):
        c.line([(x1 - 0.12, fb + 0.53 + k * 0.03), (x1 - 0.06, fb + 0.53 + k * 0.03)], fill=alpha(OUTLINE, 110), width=0.005)
    cobweb(c, x0 + 0.03, fb + H * K, 0.14, 1, -1, seed=idx)
    VA.dust(c, x0 + 0.1, boards[3] + 0.3, x1 - 0.1, boards[3] + 0.4, 5, seed=idx)


def _jeep(p, c, x0, y0, x1, y1, idx, rnd):
    """Offener Gelaendewagen im Stil eines Willys-Jeeps (Nachtrag 2, 24.10.), Crew Camp, 3,4 x 1,7 m, Seitenansicht von
    Sueden, Front nach Osten: niedrige wannenfoermige Karosserie mit Ausschnitt statt Tuer, runde Kotfluegel ueber
    grossen Stollenraedern, kurze flache Haube, senkrechter Kuehlergrill mit Schlitzen und runden Scheinwerfern,
    Windschutzscheibe mit Rahmen, offener Innenraum mit Sitzen und Lenkrad, Ueberrollbuegel, Ersatzrad und Kanister am
    Heck, Filmklappen-Aufkleber, Kennzeichen HM 1888, Schlamm. Olivgruen, eine Schattenstufe, kraeftige Umrisse."""
    olive = VA.lift("#4e5a3a", 1.45)
    olive_l = shade(olive, 1.28)
    olive_d = shade(olive, 0.7)
    tyre = hexc("#24262c")
    rim = hexc("#8a8e96")
    chrome = hexc("#c8d0d4")
    glass = alpha(hexc("#c4d8e8"), 150)
    seat = hexc("#5a3a2a")
    mud = hexc("#4a3a2a")
    ow = OUT_W
    W_ = x1 - x0
    # Bodenschatten
    c.ellipse((x0 + x1) / 2, y0 + 0.12, W_ * 0.5, 0.22, fill=alpha((0, 0, 0, 255), 85))
    # Raeder: Mitte auf Hoehe des Radius, Lauf auf der Standlinie
    R = 0.42
    wheels = (x0 + 0.78, x1 - 0.72)
    wy = y0 + R
    hood0 = x1 - 1.3                     # Spritzwand (Ende der Haube)
    tub0, tub1 = x0 + 0.28, x1 - 0.22    # Wanne von hinten bis zur Kuehlerfront
    floor = y0 + 0.5                     # Unterkante der Wanne
    rail = y0 + 0.98                     # Oberkante der Seitenwand
    cut0, cut1 = wheels[0] + 0.55, hood0 - 0.1   # Ausschnitt (keine Tuer)
    cut_y = y0 + 0.74
    # hintere Raeder zuerst (hinter der Wanne sieht man nur den Reifen, die Kotfluegel liegen davor)

    def wheel(wx):
        c.ellipse(wx, wy, R, R, fill=tyre, outline=OUTLINE, width=ow)
        for k in range(14):                                                                    # Stollen
            a = k * math.tau / 14
            c.line([(wx + (R - 0.07) * math.cos(a), wy + (R - 0.07) * math.sin(a)), (wx + (R - 0.01) * math.cos(a), wy + (R - 0.01) * math.sin(a))],
                   fill=hexc("#3a3c44"), width=0.045)
        c.ellipse(wx, wy, R * 0.52, R * 0.52, fill=rim, outline=OUTLINE, width=0.025)
        c.ellipse(wx, wy, R * 0.52, R * 0.52, fill=None, outline=shade(rim, 0.75), width=0.03)
        for k in range(5):
            a = k * math.tau / 5 + 0.4
            c.ellipse(wx + R * 0.33 * math.cos(a), wy + R * 0.33 * math.sin(a), 0.022, 0.022, fill=hexc("#4a4c54"))
        c.ellipse(wx, wy, 0.06, 0.06, fill=hexc("#4a4c54"), outline=OUTLINE, width=0.015)
        c.ellipse(wx - 0.1, wy + 0.1, 0.05, 0.03, fill=(255, 255, 255, 70))
        for k in range(4):                                                                     # Schlamm am Reifen
            a = math.pi * 1.1 + k * 0.28
            c.ellipse(wx + R * 0.95 * math.cos(a), wy + R * 0.95 * math.sin(a), 0.06, 0.035, fill=alpha(mud, 200))

    # Innenraum (hinter der Seitenwand): Rueckwand der Wanne, Sitze, Lenkrad, Ueberrollbuegel
    c.rect(tub0 + 0.05, floor, hood0, rail + 0.22, fill=olive_d, outline=OUTLINE, width=ow)          # ferne Bordwand
    c.line([(tub0 + 0.1, rail + 0.18), (hood0 - 0.05, rail + 0.18)], fill=olive, width=0.02)
    bar_x = cut0 + 0.35
    c.line([(bar_x - 0.05, rail), (bar_x, rail + 0.62), (bar_x + 0.3, rail + 0.62), (bar_x + 0.36, rail)], fill=OUTLINE, width=0.07)
    c.line([(bar_x - 0.05, rail), (bar_x, rail + 0.62), (bar_x + 0.3, rail + 0.62), (bar_x + 0.36, rail)], fill=hexc("#2a2a30"), width=0.04)
    for sx_ in (cut0 - 0.05, cut0 + 0.5):                                                      # Sitze (Lehne und Polster)
        c.rect(sx_, cut_y - 0.08, sx_ + 0.3, rail + 0.3, fill=seat, outline=OUTLINE, width=0.025)
        c.rect(sx_ + 0.03, cut_y, sx_ + 0.27, rail + 0.26, outline=shade(seat, 0.75), width=0.012)
        c.rect(sx_, cut_y - 0.12, sx_ + 0.42, cut_y + 0.02, fill=shade(seat, 0.85), outline=OUTLINE, width=0.025)
    c.line([(hood0 - 0.35, rail + 0.05), (hood0 - 0.22, rail + 0.3)], fill=OUTLINE, width=0.035)     # Lenksaeule
    c.ellipse(hood0 - 0.22, rail + 0.3, 0.14, 0.1, fill=None, outline=OUTLINE, width=0.05)
    c.ellipse(hood0 - 0.22, rail + 0.3, 0.14, 0.1, fill=None, outline=hexc("#2a2a30"), width=0.025)
    wheel(wheels[0])
    wheel(wheels[1])
    # Wanne (Seitenwand) mit Ausschnitt statt Tuer, hinterer Kotfluegel als Hump in der Seitenwand
    hump_r = R + 0.14
    hx = wheels[0]
    side = [(tub0, floor), (tub1, floor), (tub1, rail + 0.02), (hood0 + 0.02, rail + 0.02), (hood0, rail), (cut1, rail), (cut1 - 0.06, cut_y),
            (cut0 + 0.06, cut_y), (cut0, rail), (tub0, rail)]
    c.poly(side, fill=olive, outline=OUTLINE, width=ow)
    c.poly([(tub0 + 0.04, floor + 0.02), (tub1 - 0.04, floor + 0.02), (tub1 - 0.04, floor + 0.1), (tub0 + 0.04, floor + 0.1)], fill=olive_d)   # Schattenband unten
    c.line([(tub0 + 0.05, rail - 0.04), (cut0 - 0.04, rail - 0.04)], fill=olive_l, width=0.02)
    c.line([(cut1 + 0.04, rail - 0.04), (hood0 - 0.02, rail - 0.04)], fill=olive_l, width=0.02)
    c.line([(cut0 + 0.08, cut_y + 0.03), (cut1 - 0.08, cut_y + 0.03)], fill=olive_l, width=0.02)
    # hinterer Kotfluegel: runder Bogen ueber dem Rad (Ring zwischen Radausschnitt und Aussenkante), der Reifen bleibt darunter sichtbar
    outer = [(hx + hump_r * math.cos(a), wy + hump_r * math.sin(a)) for a in [math.pi - k * math.pi / 20 for k in range(21)]]
    inner = [(hx + (R + 0.03) * math.cos(a), wy + (R + 0.03) * math.sin(a)) for a in [k * math.pi / 20 for k in range(21)]]
    c.poly(outer + inner, fill=olive, outline=OUTLINE, width=ow)
    c.line([(hx + (hump_r - 0.05) * math.cos(a), wy + (hump_r - 0.05) * math.sin(a)) for a in [math.pi * 0.85 - k * math.pi * 0.7 / 10 for k in range(11)]], fill=olive_l, width=0.02)
    # Trittstufe unter dem Ausschnitt, Aufkleber (Filmklappe) und Kennzeichen an der Seitenwand
    c.rect(cut0 + 0.15, floor - 0.08, cut1 - 0.15, floor, fill=hexc("#2a2a30"), outline=OUTLINE, width=0.025)
    sx, sy = hx - 0.02, rail - 0.3
    c.rect(sx - 0.15, sy, sx + 0.15, sy + 0.14, fill=hexc("#20222a"), outline=OUTLINE, width=0.012)
    for k in range(4):
        q = sx - 0.13 + k * 0.07
        c.poly([(q, sy + 0.14), (q + 0.035, sy + 0.14), (q + 0.05, sy + 0.2), (q + 0.015, sy + 0.2)], fill=hexc("#f0f0f0"), outline=OUTLINE, width=0.008)
    c.rect(sx - 0.15, sy + 0.14, sx + 0.15, sy + 0.2, outline=OUTLINE, width=0.01)
    for k in range(2):
        c.line([(sx - 0.11, sy + 0.04 + k * 0.045), (sx + 0.09, sy + 0.04 + k * 0.045)], fill=hexc("#d8d8d8"), width=0.008)
    # Haube: Seite (flach, kurz), Deckflaeche heller, Mittelsicke, Haltegurt
    hood_top = rail + 0.02
    c.poly([(hood0, hood_top), (tub1, hood_top), (tub1 - 0.04, hood_top + 0.16), (hood0 + 0.02, hood_top + 0.18)], fill=olive_l, outline=OUTLINE, width=ow)
    c.line([(hood0 + 0.15, hood_top + 0.1), (tub1 - 0.2, hood_top + 0.09)], fill=olive_d, width=0.02)
    for k in range(2):                                                                         # Haubenriegel
        lx = hood0 + 0.35 + k * 0.45
        c.line([(lx, hood_top - 0.1), (lx, hood_top + 0.12)], fill=OUTLINE, width=0.035)
        c.line([(lx, hood_top - 0.1), (lx, hood_top + 0.12)], fill=hexc("#2a2a30"), width=0.018)
    # vorderer Kotfluegel (flach, Willys-typisch) ueber dem Vorderrad bis zur Stossstange
    fx = wheels[1]
    arch = [(fx + (R + 0.03) * math.cos(a), wy + (R + 0.03) * math.sin(a)) for a in [k * math.pi / 20 for k in range(21)]]
    fender = [(fx - R - 0.2, wy), (fx - R - 0.2, wy + 0.3), (fx - R + 0.1, wy + 0.44), (fx + R + 0.05, wy + 0.44), (fx + R + 0.05, wy)] + arch
    c.poly(fender, fill=olive, outline=OUTLINE, width=ow)
    c.line([(fx - R - 0.14, wy + 0.3), (fx + R, wy + 0.38)], fill=olive_l, width=0.02)
    c.ellipse(fx - R - 0.05, wy + 0.46, 0.08, 0.05, fill=hexc("#ffe6a8"), outline=OUTLINE, width=0.02)   # Blinker/Standlicht auf dem Kotfluegel
    # Kuehlerfront: senkrechter Grill mit Schlitzen, Scheinwerfer, Stossstange
    gx0, gx1 = tub1 - 0.02, tub1 + 0.1
    c.rect(gx0, floor + 0.02, gx1, rail + 0.02, fill=olive_d, outline=OUTLINE, width=ow)
    for k in range(6):
        gy = floor + 0.1 + k * 0.065
        c.line([(gx0 + 0.02, gy), (gx1 - 0.02, gy)], fill=OUTLINE, width=0.014)
    c.ellipse(gx1 + 0.01, rail - 0.16, 0.09, 0.09, fill=hexc("#ffe6a8"), outline=OUTLINE, width=0.025)   # Scheinwerfer
    c.ellipse(gx1 - 0.02, rail - 0.13, 0.025, 0.02, fill=(255, 255, 255, 230))
    c.glow(gx1 + 0.1, rail - 0.16, 0.3, hexc("#ffe6a8"), 0.3)
    c.rect(gx0 - 0.05, floor - 0.1, gx1 + 0.16, floor - 0.02, fill=rim, outline=OUTLINE, width=0.025)   # Stossstange vorn
    c.line([(gx0, floor - 0.06), (gx1 + 0.12, floor - 0.06)], fill=(255, 255, 255, 110), width=0.012)
    c.rect(gx0 - 0.1, floor - 0.28, gx0 + 0.3, floor - 0.12, fill=hexc("#e8e0d0"), outline=OUTLINE, width=0.015)   # Kennzeichen haengt an der Stossstange
    c.text(gx0 + 0.1, floor - 0.2, "HM 1888", 0.07, hexc("#2a2422"))
    # Windschutzscheibe (umklappbar, aufgestellt): Rahmen mit Scharnieren, Glas, Wischer
    ws_b, ws_t = hood_top, rail + 0.72
    wsx = hood0
    frame = [(wsx - 0.06, ws_b), (wsx + 0.06, ws_b), (wsx + 0.14, ws_t), (wsx + 0.02, ws_t)]
    c.poly(frame, fill=glass, outline=OUTLINE, width=0.03)
    c.line([(wsx + 0.0, ws_b + 0.06), (wsx + 0.08, ws_t - 0.06)], fill=alpha((255, 255, 255, 255), 120), width=0.02)
    c.rect(wsx - 0.07, ws_t - 0.02, wsx + 0.16, ws_t + 0.05, fill=olive, outline=OUTLINE, width=0.02)          # Rahmen oben
    c.ellipse(wsx, ws_b + 0.02, 0.035, 0.035, fill=hexc("#2a2a30"), outline=OUTLINE, width=0.012)                 # Scharnier
    c.line([(wsx + 0.03, ws_b + 0.08), (wsx + 0.09, ws_b + 0.3)], fill=hexc("#2a2a30"), width=0.015)              # Wischer
    # Heck: Ersatzrad (steht an der Rueckwand), Kanister, Ruecklicht, Stossstange, Griff
    sr = 0.3
    c.ellipse(tub0 - 0.06, floor + 0.36, sr * 0.42, sr, fill=tyre, outline=OUTLINE, width=0.035)
    c.ellipse(tub0 - 0.06, floor + 0.36, sr * 0.2, sr * 0.5, fill=rim, outline=OUTLINE, width=0.02)
    for k in range(5):
        a = k * math.tau / 5
        c.ellipse(tub0 - 0.06 + sr * 0.12 * math.cos(a), floor + 0.36 + sr * 0.3 * math.sin(a), 0.016, 0.016, fill=hexc("#4a4c54"))
    c.rect(tub0 - 0.04, floor + 0.3, tub0 + 0.02, floor + 0.42, fill=rim, outline=OUTLINE, width=0.015)   # Halter
    kx0 = tub0 - 0.02
    c.rect(kx0 - 0.04, rail - 0.3, kx0 + 0.18, rail + 0.06, fill=hexc("#5a7a3a"), outline=OUTLINE, width=0.025)   # Kanister am Heckrand
    c.rect(kx0, rail - 0.22, kx0 + 0.14, rail - 0.1, outline=OUTLINE, width=0.012)
    c.rect(kx0 + 0.02, rail + 0.06, kx0 + 0.12, rail + 0.1, fill=hexc("#2a2a30"), outline=OUTLINE, width=0.012)
    c.ellipse(tub0 + 0.08, floor + 0.14, 0.035, 0.035, fill=hexc("#c0392b"), outline=OUTLINE, width=0.015)      # Ruecklicht
    c.rect(tub0 - 0.12, floor - 0.1, tub0 + 0.12, floor - 0.02, fill=rim, outline=OUTLINE, width=0.025)        # Stossstange hinten
    c.line([(tub0 + 0.1, rail - 0.12), (tub0 + 0.28, rail - 0.12)], fill=OUTLINE, width=0.04)                  # Haltegriff
    c.line([(tub0 + 0.1, rail - 0.12), (tub0 + 0.28, rail - 0.12)], fill=hexc("#2a2a30"), width=0.02)
    # Schlamm an der unteren Seitenwand und am Boden
    for k in range(7):
        c.ellipse(tub0 + 0.2 + k * 0.4 + rnd.uniform(-0.05, 0.05), floor + 0.05 + rnd.uniform(0, 0.06), rnd.uniform(0.04, 0.08), 0.03, fill=alpha(mud, 170))
    for k in range(5):
        c.ellipse(x0 + rnd.uniform(0.3, W_ - 0.3), y0 + rnd.uniform(-0.05, 0.1), 0.08, 0.03, fill=alpha(mud, 150))
    gaffer(c, cut1 + 0.05, rail - 0.1, hood0 - 0.03, rail - 0.1, 0.03)


GARDEN_H = {
    "kamerakran": 2.8, "statue_schleier": 2.6, "gartentisch": 1.0, "kuebelpflanze": 1.5, "vogelschwarm": 0.6, "van": 2.3,
    "lichtstativ": 2.5, "campingtisch": 0.9, "kabeltrommel": 0.7, "dixi": 2.4, "zelt_aufgeschlitzt": 2.6, "schlafsack": 0.3,
    "riesenpflanze": 2.2, "giesskannen": 0.7, "schlauchtrommel": 1.0, "kletterpflanzen": 2.1, "sonnenuhr": 1.2,
    "parkbank": 1.0, "brunnen_blut": 6.0, "engelsstatue": 2.8, "offenes_grab": 1.0, "grabstein_hausherr": 1.4,
    "kraehen": 1.3, "sarkophag": 1.1, "tunneleingang": 0.3, "nischen_urnen": 2.1, "wandfackel": 2.2, "zerbrochene_urne": 0.3,
    "tunnelausgang": 0.3,
    # Maske und Crew Camp (User 24.10.)
    "schminkspiegel": 2.4, "dosenregal": 2.4, "jeep": 2.3,
}
GARDEN_PAD = {"kamerakran": 0.8, "lichtstativ": 0.6, "wandfackel": 0.9, "riesenpflanze": 0.9, "van": 0.5,
              "gartentisch": 0.6, "brunnen_blut": 0.6, "kletterpflanzen": 0.6, "kuebelpflanze": 0.5, "kabeltrommel": 0.7,
              "schlauchtrommel": 0.6, "offenes_grab": 0.5, "grabstein_hausherr": 0.4, "nischen_urnen": 0.5,
              "tunneleingang": 0.4, "zerbrochene_urne": 0.4, "giesskannen": 0.4, "kraehen": 0.4, "vogelschwarm": 0.4,
              "tunnelausgang": 0.4, "schminkspiegel": 0.5, "dosenregal": 0.4, "jeep": 0.6, "brunnen_blut": 0.85}
GARDEN_NO_SHADOW = {"vogelschwarm", "schlafsack", "kletterpflanzen", "brunnen_blut", "kraehen", "nischen_urnen",
                    "wandfackel", "zerbrochene_urne", "tunneleingang", "offenes_grab", "tunnelausgang"}

register(GARDEN_H, GARDEN_PAD, GARDEN_NO_SHADOW, {k: globals()["_" + k] for k in GARDEN_H})
