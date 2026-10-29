# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_art2.py - Einrichtung und Horror-Schicht des Hauses seit dem Audit 15.10. (docs/villa/hollowmere.html,
# Abschnitt "Audit"). Gleicher Vertrag und Strich wie villa_art.py; dieses Modul traegt seine Arten beim Import in
# villa_art ein (PROP_H, PROP_PAD, _KIND_FN, KINDS, NO_SHADOW), gen_villa importiert es direkt nach villa_art.
# Die Garten- und Gruftarten stehen in villa_art3.py (wird am Ende importiert).
#
# Konventionen: (p, c, x0, y0, x1, y1, idx, rnd) wie villa_art; Grundflaeche in Weltmetern, y nach Norden.
# Wandobjekte (DECOR, keine Kollision) liegen mit der Grundflaeche an der Wand und steigen mit K nach oben.

import math
import random

import villa_art as VA
from museum_art import OUT_W  # noqa: E402
from villa_art import (BLOOD, BLOOD_L, BORDEAUX, BORDEAUX_D, BRASS, BRASS_D, BRASS_L, CANDLE, CREAM, CREAM_D, FLAME,
                       GAFFER, IRON, IRON_D, IRON_L, MATTE, MATTE_D, MATTE_L, PARCH, STEEL, WALNUT, WALNUT_D, WALNUT_L,
                       WARM, WEB, K, OUTLINE, alpha, hexc, lift, shade, candle, cobweb, cable, gaffer, bottle,
                       book_stack, blood_pool, blood_drips, chalk_text, smoke, dust, flame, crack)

COPPER = hexc("#b0683a")
COPPER_L = shade(COPPER, 1.3)
LINEN = hexc("#d8d2c4")
LINEN_D = shade(LINEN, 0.75)
PALE = hexc("#b9b0a6")
VELVET = hexc("#5a2a3a")
GOLD = BRASS_L
PORCELAIN = hexc("#e6e2d6")
GLASS_C = alpha(hexc("#c4d8e8"), 160)
WOOD_LIGHT = hexc("#a8865a")
RED = hexc("#c83a30")
GREEN_LAMP = hexc("#3f7f5f")
LEATHER = hexc("#5a3a2a")


# ------------------------------------------------------------------ Helfer

def wall_board(p, c, x0, y0, x1, y1, z0, h, col, depth=0.06):
    """Flaches Brett oder Bild an der Wand: Front von z0 bis z0+h, Grundflaeche = Wandlinie."""
    p.box(x0, y0, x1, min(y1, y0 + depth), z0, h, shade(col, 1.1), col)
    return y0 + z0 * K, y0 + (z0 + h) * K


def picture(c, x0, fy0, x1, fy1, frame_col, inner, idx, scratched=False, empty=False, gaze=0):
    """Gerahmtes Bild (Front-Rechteck in Bildkoordinaten). gaze -1/1: Pupillen nach links/rechts (die
    Portraets blicken beim Uhrschlag zur zuletzt gemeldeten Leiche)."""
    c.rect(x0, fy0, x1, fy1, fill=frame_col, outline=OUTLINE, width=0.02)
    c.rect(x0 + 0.03, fy0 + 0.03, x1 - 0.03, fy1 - 0.03, outline=shade(frame_col, 1.35), width=0.01)
    if empty:
        c.rect(x0 + 0.06, fy0 + 0.06, x1 - 0.06, fy1 - 0.06, fill=shade(BORDEAUX, 1.15))
        return
    c.rect(x0 + 0.06, fy0 + 0.06, x1 - 0.06, fy1 - 0.06, fill=inner)
    cx, cy = (x0 + x1) / 2, (fy0 + fy1) / 2
    w = x1 - x0
    # Portraet: Oval mit Kopf und Kragen. Blick (gaze): der Kopf dreht sich mit (verschoben, Gesicht schmaler)
    # und die Pupillen sitzen am Augenrand, damit man es bei Spielzoom erkennt (9 mm Pupillenweg war unsichtbar)
    hx = cx + gaze * w * 0.07
    c.ellipse(cx, cy - 0.02, w * 0.3, (fy1 - fy0) * 0.28, fill=shade(inner, 0.8))
    c.ellipse(hx, cy + 0.04, w * (0.13 if gaze else 0.16), w * 0.2, fill=PALE, outline=OUTLINE, width=0.01)
    c.poly([(cx - w * 0.2, cy - 0.12), (cx + w * 0.2, cy - 0.12), (cx + w * 0.12, cy - 0.02), (cx - w * 0.12, cy - 0.02)], fill=MATTE_D)
    c.ellipse(cx, cy - 0.1, w * 0.03, w * 0.03, fill=CREAM)
    ex = (-0.04, 0.04) if not gaze else (-0.032 + gaze * 0.006, 0.032 + gaze * 0.006)
    if scratched:
        for dx in ex:
            c.line([(hx + dx - 0.03, cy + 0.08), (hx + dx + 0.03, cy + 0.0)], fill=OUTLINE, width=0.012)
            c.line([(hx + dx + 0.03, cy + 0.08), (hx + dx - 0.03, cy + 0.0)], fill=OUTLINE, width=0.012)
    else:
        for dx in ex:
            c.ellipse(hx + dx, cy + 0.05, 0.024, 0.019, fill=CREAM, outline=OUTLINE, width=0.006)   # Augapfel
            c.ellipse(hx + dx + gaze * 0.013, cy + 0.05, 0.012, 0.012, fill=OUTLINE)                # Pupille
            if gaze:
                c.line([(hx + dx - 0.026, cy + 0.075), (hx + dx + 0.026, cy + 0.068 - gaze * 0.006)], fill=OUTLINE, width=0.008)   # Braue


def sheet_ghost(c, x, y, w, h, seed, handprint=False):
    """Haengendes Laken mit Faltenwurf, Saum zittrig; wirkt wie eine Gestalt."""
    rnd = random.Random(seed)
    hem = VA.HD.wobble([(x - w / 2, y), (x - w / 4, y + 0.04), (x, y - 0.02), (x + w / 4, y + 0.03), (x + w / 2, y)], amp=0.02, seed=seed, step=0.05)
    pts = [(x - w / 2, y + h), (x + w / 2, y + h)] + list(reversed(hem))
    c.poly(pts, fill=LINEN, outline=OUTLINE, width=0.025)
    for k in range(3):
        fx = x - w / 2 + w * (0.25 + 0.25 * k)
        c.line(VA.HD.wobble([(fx, y + h - 0.05), (fx + rnd.uniform(-0.04, 0.04), y + 0.08)], amp=0.015, seed=seed + k, step=0.06),
               fill=alpha(LINEN_D, 150), width=0.014)
    # zwei dunkle Schatten wie Augenhoehlen
    c.ellipse(x - w * 0.18, y + h * 0.7, 0.035, 0.03, fill=alpha(LINEN_D, 140))
    c.ellipse(x + w * 0.18, y + h * 0.7, 0.035, 0.03, fill=alpha(LINEN_D, 140))
    if handprint:
        hx, hy = x + w * 0.1, y + h * 0.35
        c.ellipse(hx, hy, 0.05, 0.045, fill=alpha(BLOOD, 200))
        for dx, ln in ((-0.045, 0.06), (-0.015, 0.08), (0.015, 0.085), (0.045, 0.065)):
            c.line([(hx + dx, hy + 0.03), (hx + dx * 1.3, hy + 0.03 + ln)], fill=alpha(BLOOD, 200), width=0.022)


def chair_simple(p, c, x, y, w, d, z, col, back=True):
    """Einfacher Stuhl: Sitz als Kasten, Lehne als Platte, vier Beine."""
    for lx, ly in ((x - w / 2 + 0.04, y - d / 2 + 0.03), (x + w / 2 - 0.04, y - d / 2 + 0.03)):
        c.line([(lx, ly + z * K), (lx, ly + (z + 0.45) * K)], fill=OUTLINE, width=0.035)
        c.line([(lx, ly + z * K), (lx, ly + (z + 0.45) * K)], fill=col, width=0.02)
    p.box(x - w / 2, y - d / 2, x + w / 2, y + d / 2, z + 0.45, 0.08, shade(col, 1.15), col)
    if back:
        p.box(x - w / 2, y + d / 2 - 0.06, x + w / 2, y + d / 2, z + 0.53, 0.5, shade(col, 1.15), shade(col, 0.9))


def masks_on_shelf(c, x, y, idx):
    """Vier Masken nebeneinander (Freddy-Hut, Hockeymaske, Ghostface, Xeno-Kopf) auf einem Brett bei (x, y)."""
    # Freddy: brauner Hut, rote Haut
    c.ellipse(x - 0.27, y + 0.08, 0.055, 0.06, fill=hexc("#9a4a3a"), outline=OUTLINE, width=0.012)
    c.rect(x - 0.34, y + 0.12, x - 0.2, y + 0.145, fill=hexc("#5a3a22"), outline=OUTLINE, width=0.01)
    c.rect(x - 0.31, y + 0.145, x - 0.23, y + 0.2, fill=hexc("#5a3a22"), outline=OUTLINE, width=0.01)
    # Jason: weisse Hockeymaske mit roten Marken
    c.ellipse(x - 0.09, y + 0.09, 0.055, 0.065, fill=PORCELAIN, outline=OUTLINE, width=0.012)
    for dy in (0.06, 0.1):
        c.ellipse(x - 0.11, y + dy, 0.008, 0.008, fill=OUTLINE)
        c.ellipse(x - 0.07, y + dy, 0.008, 0.008, fill=OUTLINE)
    c.line([(x - 0.12, y + 0.13), (x - 0.06, y + 0.13)], fill=RED, width=0.008)
    c.line([(x - 0.09, y + 0.11), (x - 0.09, y + 0.15)], fill=RED, width=0.008)
    # Ghostface: schwarze Kapuze, weisses langes Gesicht
    c.poly([(x + 0.03, y + 0.02), (x + 0.17, y + 0.02), (x + 0.15, y + 0.18), (x + 0.05, y + 0.18)], fill=MATTE_D, outline=OUTLINE, width=0.01)
    c.ellipse(x + 0.1, y + 0.09, 0.04, 0.06, fill=PORCELAIN, outline=OUTLINE, width=0.01)
    c.ellipse(x + 0.085, y + 0.11, 0.01, 0.014, fill=OUTLINE)
    c.ellipse(x + 0.115, y + 0.11, 0.01, 0.014, fill=OUTLINE)
    c.ellipse(x + 0.1, y + 0.06, 0.012, 0.025, fill=OUTLINE)
    # Xenomorph: laenglicher schwarzer Kopf
    c.ellipse(x + 0.3, y + 0.09, 0.09, 0.045, fill=hexc("#1a1c22"), outline=OUTLINE, width=0.012)
    c.line([(x + 0.24, y + 0.075), (x + 0.36, y + 0.075)], fill=hexc("#3a3c44"), width=0.01)
    c.ellipse(x + 0.22, y + 0.085, 0.015, 0.01, fill=hexc("#e8e8e8"))


# ------------------------------------------------------------------ Kueche und Waschkueche

def _kupferkessel(p, c, x0, y0, x1, y1, idx, rnd):
    """Kupferkessel auf Ziegelsockel mit Feuerloch, Dampf ohne Feuer (das Haus kocht von selbst)."""
    p.box(x0, y0, x1, y1, 0, 0.5, shade(hexc("#8a4a3a"), 1.1), hexc("#7a4030"))
    c.rect(x0 + 0.08, y0 + 0.08, x1 - 0.08, y0 + 0.5 * K - 0.05, fill=hexc("#1a0c08"), outline=OUTLINE, width=0.015)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2 - 0.02
    p.cyl(cx, cy, r, 0.5, 0.85, COPPER_L, COPPER, ry=r * 0.5)
    top = cy + 1.35 * K
    c.ellipse(cx, top, r, r * 0.5, fill=shade(COPPER, 0.8), outline=OUTLINE, width=0.02)
    c.ellipse(cx, top, r * 0.75, r * 0.36, fill=hexc("#2a1a14"))
    c.line([(cx - r + 0.03, cy + 0.6 * K), (cx - r + 0.03, top - 0.03)], fill=COPPER_L, width=0.015)
    for k in range(3):
        smoke(c, cx - 0.1 + k * 0.1, top + 0.02, seed=idx + k, h=0.45)
    c.ellipse(cx + r * 0.4, cy + 0.9 * K, 0.03, 0.02, fill=BRASS, outline=OUTLINE, width=0.01)


def _mangel(p, c, x0, y0, x1, y1, idx, rnd):
    """Waeschemangel: Holzgestell, zwei Walzen, Kurbel, ein Laken haengt durch."""
    p.box(x0, y0, x1, y1, 0, 0.75, WALNUT_L, WALNUT)
    zt = y0 + 0.75 * K
    for k in range(2):
        c.rect(x0 + 0.1, zt + 0.06 + k * 0.1, x1 - 0.1, zt + 0.14 + k * 0.1, fill=WOOD_LIGHT, outline=OUTLINE, width=0.015)
        c.line([(x0 + 0.12, zt + 0.08 + k * 0.1), (x1 - 0.12, zt + 0.08 + k * 0.1)], fill=shade(WOOD_LIGHT, 1.3), width=0.008)
    c.rect(x0 + 0.04, zt - 0.02, x0 + 0.1, zt + 0.3, fill=IRON, outline=OUTLINE, width=0.015)
    c.rect(x1 - 0.1, zt - 0.02, x1 - 0.04, zt + 0.3, fill=IRON, outline=OUTLINE, width=0.015)
    c.line([(x1 - 0.06, zt + 0.2), (x1 + 0.12, zt + 0.3)], fill=OUTLINE, width=0.035)
    c.line([(x1 - 0.06, zt + 0.2), (x1 + 0.12, zt + 0.3)], fill=IRON_L, width=0.018)
    c.ellipse(x1 + 0.12, zt + 0.3, 0.025, 0.02, fill=WALNUT_D, outline=OUTLINE, width=0.01)
    c.poly([(x0 + 0.2, zt + 0.1), (x1 - 0.3, zt + 0.1), (x1 - 0.35, y0 + 0.1), (x0 + 0.3, y0 + 0.14)], fill=LINEN, outline=OUTLINE, width=0.015)
    c.line([(x0 + 0.4, zt + 0.05), (x0 + 0.42, y0 + 0.2)], fill=alpha(LINEN_D, 150), width=0.012)


def _seifenkisten(p, c, x0, y0, x1, y1, idx, rnd):
    """Zwei Seifenkisten uebereinander mit Aufdruck, eine Buerste."""
    p.box(x0, y0, x1, y1, 0, 0.4, shade(WOOD_LIGHT, 1.1), WOOD_LIGHT)
    p.box(x0 + 0.04, y0 + 0.02, x1 - 0.06, y1 - 0.04, 0.4, 0.36, shade(WOOD_LIGHT, 1.15), shade(WOOD_LIGHT, 0.95))
    c.text((x0 + x1) / 2, y0 + 0.2 * K, "SOAP", 0.06, shade(WALNUT_D, 0.8))
    c.text((x0 + x1) / 2 - 0.01, y0 + 0.02 + 0.58 * K, "LYE", 0.055, hexc("#5a2a2a"))
    c.ellipse(x1 - 0.1, y1 - 0.02 + 0.76 * K, 0.06, 0.03, fill=WALNUT_L, outline=OUTLINE, width=0.012)


def _hackblock(p, c, x0, y0, x1, y1, idx, rnd):
    """Hackblock mit Beil, Blut und einem Stueck Fleisch, das nicht nach Fleisch aussieht."""
    p.box(x0, y0, x1, y1, 0, 0.85, shade(WOOD_LIGHT, 1.1), WOOD_LIGHT)
    fz = y0
    for k in range(4):
        c.line([(x0 + 0.03, fz + 0.1 + k * 0.1), (x1 - 0.03, fz + 0.1 + k * 0.1)], fill=shade(WOOD_LIGHT, 0.75), width=0.012)
    zt = y0 + 0.85 * K
    cx, cy = (x0 + x1) / 2, zt + (y1 - y0) * 0.45
    blood_pool(c, cx, cy, 0.22, 0.1, seed=idx, a=230)
    blood_drips(c, x0 + 0.15, zt + 0.02, 4, 0.14, seed=idx + 1)
    VA.knife(c, cx - 0.12, cy + 0.1, 0.6, 1.2)
    c.ellipse(cx + 0.14, cy + 0.02, 0.09, 0.05, fill=hexc("#8a3a3a"), outline=OUTLINE, width=0.012)
    c.ellipse(cx + 0.12, cy + 0.03, 0.03, 0.015, fill=hexc("#c86a6a"))
    c.line([(cx + 0.19, cy + 0.03), (cx + 0.3, cy + 0.08)], fill=hexc("#e8e0d0"), width=0.025)         # Knochen


def _craftservice(p, c, x0, y0, x1, y1, idx, rnd):
    """Craft Service der Crew: Kisten, Kaffeeurne, Donutkarton, Becherturm."""
    p.box(x0, y0, x1 - 0.5, y1, 0, 0.75, shade(WOOD_LIGHT, 1.1), WOOD_LIGHT)
    gaffer(c, x0 + 0.1, y0 + 0.5 * K, x1 - 0.6, y0 + 0.5 * K, 0.04)
    c.text((x0 + x1 - 0.5) / 2, y0 + 0.5 * K, "CRAFT", 0.045, OUTLINE)
    zt = y0 + 0.75 * K
    p.cyl(x0 + 0.25, y0 + 0.5, 0.14, 0.75, 0.5, STEEL, shade(STEEL, 0.85), ry=0.07)
    c.ellipse(x0 + 0.25, y0 + 0.5 + 1.25 * K, 0.14, 0.07, fill=shade(STEEL, 1.1), outline=OUTLINE, width=0.015)
    c.rect(x0 + 0.23, y0 + 0.5 + 0.85 * K, x0 + 0.27, y0 + 0.5 + 0.95 * K, fill=MATTE_D)
    c.ellipse(x0 + 0.25, y0 + 0.5 + 0.82 * K, 0.02, 0.015, fill=RED)
    c.rect(x1 - 0.9, zt + 0.02, x1 - 0.55, zt + 0.16, fill=hexc("#e8b8c8"), outline=OUTLINE, width=0.012)   # Donutkarton
    c.ellipse(x1 - 0.72, zt + 0.09, 0.05, 0.03, fill=hexc("#c88a5a"), outline=OUTLINE, width=0.008)
    c.ellipse(x1 - 0.72, zt + 0.09, 0.015, 0.01, fill=hexc("#e8b8c8"))
    for k in range(4):                                                                                 # Becher
        c.rect(x1 - 0.4 + (k % 2) * 0.12, y0 + 0.2 + (k // 2) * 0.1, x1 - 0.32 + (k % 2) * 0.12, y0 + 0.32 + (k // 2) * 0.1, fill=CREAM, outline=OUTLINE, width=0.01)
    c.rect(x1 - 0.45, y0 + 0.02, x1 - 0.05, y0 + 0.18, fill=hexc("#5a3a1a"), outline=OUTLINE, width=0.012)    # Kiste
    blood_drips(c, x1 - 0.58, zt + 0.02, 2, 0.08, seed=idx)


def _topfregal(p, c, x0, y0, x1, y1, idx, rnd):
    """Topfregal an der Nordwand: Eisenstange mit haengenden Kupfertoepfen und Pfannen."""
    z0 = 1.6
    c.rect(x0, y0 + z0 * K, x1, y0 + z0 * K + 0.04, fill=IRON, outline=OUTLINE, width=0.015)
    for k in range(5):
        px = x0 + 0.2 + k * (x1 - x0 - 0.4) / 4
        top = y0 + z0 * K
        c.line([(px, top), (px, top - 0.08)], fill=IRON_L, width=0.012)
        w, h = (0.1, 0.08) if k % 2 == 0 else (0.13, 0.05)
        c.rect(px - w / 2, top - 0.08 - h, px + w / 2, top - 0.08, fill=COPPER if k % 2 == 0 else STEEL, outline=OUTLINE, width=0.015)
        c.line([(px - w / 2 + 0.02, top - 0.1), (px + w / 2 - 0.02, top - 0.1)], fill=COPPER_L if k % 2 == 0 else shade(STEEL, 1.3), width=0.01)
        if k % 2:
            c.line([(px + w / 2, top - 0.1), (px + w / 2 + 0.1, top - 0.06)], fill=MATTE_D, width=0.018)
    cobweb(c, x1, y0 + z0 * K + 0.04, 0.14, -1, -1, seed=idx)


def _speiseaufzug(p, c, x0, y0, x1, y1, idx, rnd):
    """Speiseaufzug-Klappe in der Ostwand: Holzrahmen, Schiebetuer halb offen, dunkler Schacht, Seil."""
    fy0, fy1 = wall_board(p, c, x0, y0, x1, y1, 0.7, 0.9, WALNUT_D, depth=0.25)
    c.rect(x0 - 0.02, fy0 + 0.02, x1 + 0.02, fy1 - 0.02, fill=WALNUT, outline=OUTLINE, width=0.015)
    c.rect(x0 + 0.02, fy0 + 0.06, x1 - 0.02, fy1 - 0.25, fill=hexc("#0b0d10"))
    c.rect(x0 + 0.02, fy1 - 0.25, x1 - 0.02, fy1 - 0.06, fill=WALNUT_L, outline=OUTLINE, width=0.012)
    c.line([((x0 + x1) / 2, fy0 + 0.08), ((x0 + x1) / 2, fy1 - 0.25)], fill=hexc("#8a7a5a"), width=0.008)
    c.ellipse((x0 + x1) / 2, fy1 - 0.15, 0.015, 0.015, fill=BRASS, outline=OUTLINE, width=0.008)
    c.text((x0 + x1) / 2, fy1 - 0.03, "LIFT", 0.028, BRASS_D)


def _drehregal(p, c, x0, y0, x1, y1, idx, rnd):
    """Drehbuecherregal an der Ostwand der Bibliothek (schmal in x, lang in y): Walnusskorpus, von oben die
    Buchoberkanten in Reihen, auf dem Deckel ein Kerzenstummel, in der Wandfuge ein Lichtspalt (Geheimgang)."""
    H = 2.4
    p.box(x0, y0, x1, y1, 0, H, WALNUT_L, WALNUT)
    fb, ft = y0, y0 + H * K
    # Stirnseite (Sueden): zwei Boeden mit Buchruecken
    for z in (0.4, 1.3):
        sy = y0 + z * K
        c.rect(x0 + 0.03, sy, x1 - 0.03, sy + 0.03, fill=WALNUT_D, outline=OUTLINE, width=0.01)
        xa = x0 + 0.05
        cols = [lift("#5a1e22", 1.5), lift("#1e3a2a", 1.6), hexc("#b48a3c"), lift("#1e2a4a", 1.6), CREAM_D]
        k = 0
        while xa < x1 - 0.08:
            bw = 0.035 + (k % 3) * 0.01
            bh = (0.28 + (k % 2) * 0.06) * K
            c.rect(xa, sy + 0.03, xa + bw, sy + 0.03 + bh, fill=cols[(k + idx) % len(cols)], outline=OUTLINE, width=0.008)
            xa += bw + 0.012
            k += 1
    # Deckel: Buchreihen von oben (Oberkanten der stehenden Buecher, drei Reihen entlang y)
    ty0, ty1 = ft, y1 + H * K
    for r in range(3):
        rx = x0 + 0.07 + r * (x1 - x0 - 0.14) / 3
        rw = (x1 - x0 - 0.14) / 3 - 0.02
        yy = ty0 + 0.08
        k = 0
        while yy < ty1 - 0.1:
            bh = 0.035 + (k % 3) * 0.012
            col = [lift("#5a1e22", 1.4), lift("#1e3a2a", 1.5), hexc("#a0783a"), lift("#1e2a4a", 1.5), CREAM_D][(k + r + idx) % 5]
            c.rect(rx, yy, rx + rw, yy + bh, fill=col, outline=OUTLINE, width=0.008)
            c.line([(rx + 0.01, yy + bh / 2), (rx + rw - 0.01, yy + bh / 2)], fill=alpha(CREAM, 60), width=0.006)
            yy += bh + 0.01
            k += 1
    # Kerzenstummel auf dem Deckel, Wachs gelaufen
    candle(c, x1 - 0.1, ty1 - 0.18, 0.09, True, r=0.022, seed=idx)
    # Lichtspalt an der Wandfuge (Ostseite): der Gang dahinter
    c.rect(x1 - 0.012, fb + 0.1 * K, x1 + 0.006, ft - 0.05, fill=alpha(WARM, 150))
    dust(c, x0 + 0.03, ty1 - 0.06, x1 - 0.03, ty1 - 0.02, 4, seed=idx)


def _fleischerhaken(p, c, x0, y0, x1, y1, idx, rnd):
    """Fleischerhaken an Ketten von der Decke, einer mit Schuerze dran."""
    for k in range(3):
        hx = x0 + 0.15 + k * (x1 - x0 - 0.3) / 2
        top = y0 + 2.5 * K
        ly = top - 0.3 - (k % 2) * 0.08
        for j in range(6):
            c.ellipse(hx, top - j * (top - ly) / 6, 0.012, 0.016, outline=IRON_L, width=0.008)
        c.line([(hx, ly), (hx, ly - 0.08), (hx + 0.04, ly - 0.12), (hx + 0.02, ly - 0.06)], fill=OUTLINE, width=0.035)
        c.line([(hx, ly), (hx, ly - 0.08), (hx + 0.04, ly - 0.12), (hx + 0.02, ly - 0.06)], fill=STEEL, width=0.018)
        if k == 1:
            c.poly([(hx - 0.1, ly - 0.1), (hx + 0.1, ly - 0.1), (hx + 0.08, ly - 0.45), (hx - 0.08, ly - 0.45)], fill=LINEN_D, outline=OUTLINE, width=0.015)
            blood_drips(c, hx - 0.03, ly - 0.2, 3, 0.15, seed=idx)


def _waescheleine(p, c, x0, y0, x1, y1, idx, rnd):
    """Waescheleine mit drei Laken, die wie Gestalten haengen; eines mit blutigem Handabdruck."""
    z0 = 1.9
    ly = y0 + z0 * K
    c.line([(x0, ly + 0.04), ((x0 + x1) / 2, ly), (x1, ly + 0.04)], fill=hexc("#8a7a5a"), width=0.012)
    for k in range(3):
        sx = x0 + 0.55 + k * (x1 - x0 - 1.1) / 2
        sheet_ghost(c, sx, ly - 0.95, 0.7, 0.93, seed=idx + k, handprint=(k == 1))
        for dx in (-0.25, 0.25):
            c.rect(sx + dx - 0.015, ly - 0.03, sx + dx + 0.015, ly + 0.05, fill=WOOD_LIGHT, outline=OUTLINE, width=0.008)
    for px in (x0, x1):
        c.line([(px, y0), (px, ly + 0.05)], fill=OUTLINE, width=0.04)
        c.line([(px, y0), (px, ly + 0.05)], fill=WALNUT_L, width=0.022)


# ------------------------------------------------------------------ Seance und Funkraum

def _seance_wand(p, c, x0, y0, x1, y1, idx, rnd):
    """Nordwand des Seance-Salons: schwere Vorhaenge, Ouija-Tableau, Spiritfotos mit verwischten Gesichtern."""
    z1 = 2.4
    top = y0 + z1 * K
    for cx0, cx1 in ((x0, x0 + 0.9), (x1 - 0.9, x1)):
        c.poly([(cx0, y0 + 0.02), (cx1, y0 + 0.02), (cx1, top), (cx0, top)], fill=VELVET, outline=OUTLINE, width=0.02)
        for k in range(4):
            fx = cx0 + 0.12 + k * 0.2
            c.line([(fx, y0 + 0.06), (fx + 0.04, top - 0.04)], fill=alpha(shade(VELVET, 0.6), 180), width=0.02)
        c.rect(cx0 - 0.02, top - 0.03, cx1 + 0.02, top + 0.05, fill=BRASS, outline=OUTLINE, width=0.015)
        c.line([(cx0 + 0.1, y0 + 0.55), (cx1 - 0.1, y0 + 0.45)], fill=GOLD, width=0.02)           # Raffhalter
    # Ouija-Tableau mittig
    tx0, tx1 = (x0 + x1) / 2 - 0.9, (x0 + x1) / 2 + 0.9
    c.rect(tx0, y0 + 0.45, tx1, y0 + 1.25, fill=WALNUT_D, outline=OUTLINE, width=0.02)
    c.rect(tx0 + 0.05, y0 + 0.5, tx1 - 0.05, y0 + 1.2, fill=PARCH, outline=shade(PARCH, 0.6), width=0.01)
    c.text((tx0 + tx1) / 2, y0 + 1.08, "A B C D E F G H I J K L M", 0.06, OUTLINE)
    c.text((tx0 + tx1) / 2, y0 + 0.95, "N O P Q R S T U V W X Y Z", 0.06, OUTLINE)
    c.text((tx0 + tx1) / 2, y0 + 0.82, "1 2 3 4 5 6 7 8 9 0", 0.055, OUTLINE)
    c.text(tx0 + 0.3, y0 + 0.62, "YES", 0.06, OUTLINE)
    c.text(tx1 - 0.3, y0 + 0.62, "NO", 0.06, OUTLINE)
    c.text((tx0 + tx1) / 2, y0 + 0.6, "GOODBYE", 0.05, OUTLINE)
    c.glow((tx0 + tx1) / 2, y0 + 0.85, 0.6, hexc("#a0c8c0"), 0.1)
    # Spiritfotos links und rechts vom Tableau
    for k, px in enumerate((tx0 - 0.5, tx1 + 0.5)):
        for j in range(2):
            fy = y0 + 0.55 + j * 0.42
            c.rect(px - 0.17, fy, px + 0.17, fy + 0.3, fill=WALNUT, outline=OUTLINE, width=0.015)
            c.rect(px - 0.14, fy + 0.03, px + 0.14, fy + 0.27, fill=hexc("#8a8070"))
            c.ellipse(px + (0.04 if (k + j) % 2 else -0.03), fy + 0.14, 0.05, 0.07, fill=alpha(hexc("#d0c8b0"), 170))
            c.ellipse(px + (0.04 if (k + j) % 2 else -0.03), fy + 0.14, 0.03, 0.045, fill=alpha(hexc("#f0ece0"), 120))
    cobweb(c, x0 + 0.9, top, 0.2, 1, -1, seed=idx)


def _wandteppich(p, c, x0, y0, x1, y1, idx, rnd):
    """Wandteppich (verbirgt den Geheimgang): Bordeaux mit goldener Borte und Wappen, unten leicht gelupft."""
    top = y0 + 2.2 * K
    c.rect(x0 - 0.05, top - 0.02, x1 + 0.05, top + 0.05, fill=WALNUT_D, outline=OUTLINE, width=0.015)
    pts = [(x0, top), (x1, top), (x1, y0 + 0.08), (x1 - 0.3, y0 + 0.12), (x1 - 0.5, y0 + 0.26), (x0 + 0.1, y0 + 0.05)]
    c.poly(pts, fill=BORDEAUX_D, outline=OUTLINE, width=0.02)
    c.rect(x0 + 0.1, y0 + 0.2, x1 - 0.1, top - 0.1, outline=GOLD, width=0.025)
    cx, cy = (x0 + x1) / 2, (y0 + top) / 2
    c.poly([(cx - 0.3, cy + 0.3), (cx + 0.3, cy + 0.3), (cx + 0.25, cy - 0.15), (cx, cy - 0.35), (cx - 0.25, cy - 0.15)], fill=GOLD, outline=OUTLINE, width=0.015)
    c.poly([(cx - 0.2, cy + 0.22), (cx + 0.2, cy + 0.22), (cx + 0.16, cy - 0.1), (cx, cy - 0.25), (cx - 0.16, cy - 0.1)], fill=BORDEAUX)
    c.line([(cx, cy + 0.2), (cx, cy - 0.2)], fill=GOLD, width=0.02)
    c.line([(cx - 0.15, cy), (cx + 0.15, cy)], fill=GOLD, width=0.02)
    c.rect(x1 - 0.5, y0 + 0.05, x1 - 0.3, y0 + 0.14, fill=hexc("#0b0d10"))      # Spalt dahinter
    dust(c, x0 + 0.1, top - 0.08, x1 - 0.1, top - 0.02, 6, seed=idx)


def _umgestuerzter_stuhl(p, c, x0, y0, x1, y1, idx, rnd):
    """Umgestuerzter Stuhl, liegt auf der Seite, Beine zur Seite."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c.soft_shadow([(x0 + 0.04, y0 - 0.03), (x1 + 0.06, y0 - 0.03), (x1 + 0.06, y1), (x0 + 0.04, y1)], 70, 0.04)
    c.poly([(x0, cy - 0.1), (x0 + 0.35, cy - 0.14), (x0 + 0.35, cy + 0.16), (x0, cy + 0.12)], fill=WALNUT, outline=OUTLINE, width=0.02)
    c.poly([(x0 + 0.35, cy - 0.12), (x0 + 0.45, cy - 0.12), (x0 + 0.45, cy + 0.14), (x0 + 0.35, cy + 0.14)], fill=VELVET, outline=OUTLINE, width=0.015)
    for k in range(4):
        ly = cy - 0.14 + k * 0.09
        c.line([(x0 + 0.45, ly), (x1, ly + 0.02)], fill=OUTLINE, width=0.035)
        c.line([(x0 + 0.45, ly), (x1, ly + 0.02)], fill=WALNUT_L, width=0.02)
    c.line([(x0 + 0.05, cy - 0.05), (x0 + 0.3, cy - 0.07)], fill=WALNUT_D, width=0.012)


def _kristallkugel_tisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Beistelltisch mit Kristallkugel unter Samttuch, die von innen leuchtet."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    p.cyl(cx, cy, 0.05, 0, 0.65, WALNUT_L, WALNUT, ry=0.03)
    p.cyl(cx, cy, r, 0.65, 0.05, shade(VELVET, 1.2), VELVET, ry=r * 0.55)
    zt = cy + 0.7 * K
    c.glow(cx, zt + 0.12, 0.3, hexc("#9ad0e8"), 0.45)
    c.ellipse(cx, zt + 0.12, 0.12, 0.12, fill=alpha(hexc("#bfe0f0"), 200), outline=OUTLINE, width=0.015)
    c.ellipse(cx - 0.04, zt + 0.16, 0.035, 0.025, fill=alpha(hexc("#ffffff"), 170))
    c.ellipse(cx, zt + 0.02, 0.1, 0.04, fill=BRASS_D, outline=OUTLINE, width=0.012)
    c.ellipse(cx + 0.02, zt + 0.1, 0.02, 0.03, fill=alpha(hexc("#2a3a60"), 120))


def _phonograph(p, c, x0, y0, x1, y1, idx, rnd):
    """Grammophon: Holzkasten, Platte, grosser Messingtrichter; dreht sich von selbst."""
    p.box(x0, y0, x1 - 0.2, y1, 0, 0.4, WALNUT_L, WALNUT)
    zt = y0 + 0.4 * K
    c.ellipse(x0 + 0.3, zt + 0.12, 0.16, 0.08, fill=MATTE_D, outline=OUTLINE, width=0.015)
    c.ellipse(x0 + 0.3, zt + 0.12, 0.05, 0.025, fill=BORDEAUX)
    c.line([(x0 + 0.5, zt + 0.12), (x0 + 0.36, zt + 0.16)], fill=STEEL, width=0.015)
    hx, hy = x1 - 0.2, zt + 0.1
    c.poly([(hx - 0.08, hy), (hx + 0.02, hy + 0.05), (hx + 0.3, hy + 0.55), (hx - 0.12, hy + 0.55), (hx - 0.16, hy + 0.1)], fill=BRASS, outline=OUTLINE, width=0.02)
    c.ellipse(hx + 0.09, hy + 0.55, 0.21, 0.1, fill=shade(BRASS, 0.8), outline=OUTLINE, width=0.02)
    c.ellipse(hx + 0.09, hy + 0.55, 0.14, 0.06, fill=hexc("#3a2a14"))
    c.line([(hx - 0.1, hy + 0.12), (hx - 0.02, hy + 0.5)], fill=BRASS_L, width=0.015)
    for k in range(3):
        c.ellipse(hx + 0.3 + k * 0.06, hy + 0.7 + k * 0.08, 0.02 + k * 0.01, 0.015 + k * 0.01, outline=alpha(CREAM, 120), width=0.008)   # Noten


def _bandregal(p, c, x0, y0, x1, y1, idx, rnd):
    """Bandregal an der Westwand: Faecher mit beschrifteten Tonbandschachteln, eine Spule abgewickelt."""
    p.box(x0, y0, x1, y1, 0, 2.0, WALNUT_L, WALNUT)
    for k in range(4):
        sy = y0 + 0.3 + k * 0.45
        c.rect(x0 + 0.03, sy, x1 - 0.03, sy + 0.03, fill=WALNUT_D)
        for j in range(5):
            bx = x0 + 0.05 + j * 0.07
            col = (hexc("#8a6a3a"), hexc("#6a5a4a"), hexc("#9a7a4a"))[(j + k + idx) % 3]
            c.rect(bx, sy + 0.03, bx + 0.06, sy + 0.34, fill=col, outline=OUTLINE, width=0.008)
            c.line([(bx + 0.01, sy + 0.1), (bx + 0.05, sy + 0.1)], fill=CREAM, width=0.012)
    c.text((x0 + x1) / 2, y0 + 2.0 * K - 0.1, "DAILIES", 0.045, CREAM)
    c.ellipse(x1 + 0.1, y0 + 0.05, 0.08, 0.05, fill=hexc("#5a4224"), outline=OUTLINE, width=0.012)
    c.line(VA.HD.wobble([(x1 + 0.1, y0 + 0.05), (x1 + 0.35, y0 - 0.05), (x1 + 0.5, y0 + 0.08), (x1 + 0.7, y0 - 0.02)], amp=0.02, seed=idx, step=0.04), fill=hexc("#3a2a18"), width=0.01)


def _walkie_station(p, c, x0, y0, x1, y1, idx, rnd):
    """Ladestation mit vier Walkie-Talkies, LEDs, Kabel zur Wand."""
    p.box(x0, y0, x1, y1, 0, 0.75, MATTE_L, MATTE)
    zt = y0 + 0.75 * K
    for k in range(4):
        wx = x0 + 0.06 + k * 0.1
        c.rect(wx, zt + 0.02, wx + 0.07, zt + 0.22, fill=MATTE_D, outline=OUTLINE, width=0.01)
        c.line([(wx + 0.035, zt + 0.22), (wx + 0.035, zt + 0.36)], fill=MATTE_D, width=0.012)
        c.ellipse(wx + 0.035, zt + 0.06, 0.008, 0.008, fill=hexc("#4caf50") if k != 2 else RED)
    gaffer(c, x0 + 0.03, y0 + 0.4 * K, x1 - 0.03, y0 + 0.4 * K, 0.035)
    cable(c, [(x1, zt - 0.05), (x1 + 0.1, zt - 0.2), (x1 + 0.05, y0 - 0.1)], seed=idx, w=0.02)


def _drehstuhl(p, c, x0, y0, x1, y1, idx, rnd):
    """Drehstuhl mit Sternfuss, leicht gedreht."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for k in range(5):
        a = math.pi * 2 * k / 5 + 0.3
        c.line([(cx, cy), (cx + 0.27 * math.cos(a), cy + 0.16 * math.sin(a))], fill=OUTLINE, width=0.04)
        c.line([(cx, cy), (cx + 0.27 * math.cos(a), cy + 0.16 * math.sin(a))], fill=MATTE_L, width=0.022)
    c.rect(cx - 0.025, cy, cx + 0.025, cy + 0.45 * K, fill=STEEL, outline=OUTLINE, width=0.012)
    p.cyl(cx, cy, 0.24, 0.45, 0.1, shade(LEATHER, 1.2), LEATHER, ry=0.14)
    p.box(cx - 0.2, cy + 0.1, cx + 0.2, cy + 0.2, 0.55, 0.5, shade(LEATHER, 1.2), shade(LEATHER, 0.9))


def _tonband_boden(p, c, x0, y0, x1, y1, idx, rnd):
    """Abgewickelte Tonbandspule am Boden."""
    c.ellipse(x0 + 0.2, y0 + 0.2, 0.14, 0.08, fill=hexc("#8a6a3a"), outline=OUTLINE, width=0.012)
    c.ellipse(x0 + 0.2, y0 + 0.2, 0.05, 0.03, fill=STEEL)
    pts = [(x0 + 0.3, y0 + 0.2)]
    for k in range(12):
        pts.append((x0 + 0.3 + (x1 - x0 - 0.4) * k / 11, y0 + 0.1 + 0.25 * abs(math.sin(k * 1.3 + idx))))
    c.line(VA.HD.wobble(pts, amp=0.02, seed=idx, step=0.03), fill=hexc("#3a2a18"), width=0.012)


# ------------------------------------------------------------------ Prop Store, Sternwarte

def _kleiderstange(p, c, x0, y0, x1, y1, idx, rnd):
    """Kleiderstange mit Kostuemen: Umhang, Kittel, Hochzeitskleid mit Blut, Clownsanzug."""
    z = 1.7
    top = y0 + z * K
    for px in (x0 + 0.08, x1 - 0.08):
        c.line([(px, y0 + 0.02), (px, top)], fill=OUTLINE, width=0.04)
        c.line([(px, y0 + 0.02), (px, top)], fill=STEEL, width=0.022)
        c.ellipse(px, y0 + 0.02, 0.06, 0.03, fill=MATTE_D, outline=OUTLINE, width=0.01)
    c.rect(x0 + 0.06, top - 0.02, x1 - 0.06, top + 0.02, fill=STEEL, outline=OUTLINE, width=0.012)
    outfits = [(MATTE_D, 0.9), (LINEN, 1.1), (CREAM, 1.3), (hexc("#d8a830"), 1.0), (VELVET, 1.05)]
    n = len(outfits)
    for k, (col, ln) in enumerate(outfits):
        ox = x0 + 0.3 + k * (x1 - x0 - 0.6) / (n - 1)
        c.line([(ox, top + 0.02), (ox, top - 0.06)], fill=STEEL, width=0.01)
        c.poly([(ox - 0.14, top - 0.08), (ox + 0.14, top - 0.08), (ox + 0.19, top - 0.08 - ln * 0.9), (ox - 0.19, top - 0.08 - ln * 0.9)], fill=col, outline=OUTLINE, width=0.015)
        c.line([(ox, top - 0.1), (ox, top - 0.08 - ln * 0.85)], fill=alpha(shade(col, 0.7), 150), width=0.012)
        if k == 2:
            blood_pool(c, ox + 0.02, top - 0.08 - ln * 0.5, 0.07, 0.05, seed=idx, a=210)
            blood_drips(c, ox + 0.02, top - 0.08 - ln * 0.55, 3, 0.2, seed=idx + 1)
        if k == 3:
            for j in range(4):
                c.ellipse(ox - 0.08 + j * 0.055, top - 0.3 - (j % 2) * 0.2, 0.025, 0.025, fill=RED)


def _maskenregal(p, c, x0, y0, x1, y1, idx, rnd):
    """Maskenregal an der Ostwand: Bretter mit den Kostuemmasken, Schild PROPS - DO NOT TOUCH."""
    p.box(x0, y0, x1, y1, 0, 2.0, WALNUT_L, WALNUT)
    for k in range(3):
        sy = y0 + 0.35 + k * 0.5
        c.rect(x0 - 0.08, sy, x1 + 0.08, sy + 0.04, fill=WALNUT_L, outline=OUTLINE, width=0.012)
    masks_on_shelf(c, (x0 + x1) / 2, y0 + 0.39, idx)
    masks_on_shelf(c, (x0 + x1) / 2 + 0.05, y0 + 0.89, idx + 1)
    c.ellipse((x0 + x1) / 2 - 0.15, y0 + 1.5, 0.06, 0.07, fill=PALE, outline=OUTLINE, width=0.012)           # Totenschaedel
    c.ellipse((x0 + x1) / 2 - 0.17, y0 + 1.5, 0.012, 0.016, fill=OUTLINE)
    c.ellipse((x0 + x1) / 2 - 0.13, y0 + 1.5, 0.012, 0.016, fill=OUTLINE)
    c.ellipse((x0 + x1) / 2 + 0.1, y0 + 1.48, 0.07, 0.05, fill=hexc("#3a5a3a"), outline=OUTLINE, width=0.012)  # Gummimaske
    c.rect(x0 - 0.1, y0 + 2.0 * K - 0.14, x1 + 0.1, y0 + 2.0 * K - 0.04, fill=CREAM, outline=OUTLINE, width=0.012)
    c.text((x0 + x1) / 2, y0 + 2.0 * K - 0.09, "PROPS - DO NOT TOUCH", 0.028, OUTLINE)
    cobweb(c, x1, y0 + 2.0 * K, 0.14, -1, -1, seed=idx)


def _schneiderpuppe(p, c, x0, y0, x1, y1, idx, rnd):
    """Schneiderpuppe ohne Kopf auf Dreifuss, mit halb genaehtem Kostuem."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for k in range(3):
        a = math.pi * 2 * k / 3 + 0.5
        c.line([(cx, cy + 0.35 * K), (cx + 0.22 * math.cos(a), cy + 0.13 * math.sin(a))], fill=OUTLINE, width=0.035)
        c.line([(cx, cy + 0.35 * K), (cx + 0.22 * math.cos(a), cy + 0.13 * math.sin(a))], fill=WALNUT_L, width=0.018)
    c.rect(cx - 0.02, cy + 0.3 * K, cx + 0.02, cy + 0.75 * K, fill=WALNUT, outline=OUTLINE, width=0.012)
    b0 = cy + 0.75 * K
    c.poly([(cx - 0.14, b0), (cx + 0.14, b0), (cx + 0.19, b0 + 0.35), (cx + 0.15, b0 + 0.62), (cx - 0.15, b0 + 0.62), (cx - 0.19, b0 + 0.35)], fill=LINEN, outline=OUTLINE, width=0.018)
    c.line([(cx, b0 + 0.02), (cx, b0 + 0.6)], fill=alpha(LINEN_D, 160), width=0.01)
    c.poly([(cx - 0.19, b0 + 0.35), (cx + 0.02, b0 + 0.4), (cx + 0.0, b0 + 0.62), (cx - 0.15, b0 + 0.62)], fill=VELVET, outline=OUTLINE, width=0.012)
    for k in range(4):
        c.line([(cx + 0.04 + k * 0.03, b0 + 0.42 - k * 0.02), (cx + 0.06 + k * 0.03, b0 + 0.47 - k * 0.02)], fill=STEEL, width=0.008)   # Nadeln
    c.ellipse(cx, b0 + 0.64, 0.05, 0.02, fill=WALNUT_D, outline=OUTLINE, width=0.012)                     # Halsstumpf
    c.ellipse(cx, b0 + 0.64, 0.02, 0.01, fill=OUTLINE)


def _sarg_angelehnt(p, c, x0, y0, x1, y1, idx, rnd):
    """Requisitensarg, hochkant an die Wand gelehnt, Deckel einen Spalt offen."""
    w = x1 - x0
    top = y1 + 1.9 * K
    c.poly([(x0, y0 + 0.02), (x1, y0 + 0.02), (x1 + 0.06, top), (x0 - 0.06, top)], fill=WALNUT_D, outline=OUTLINE, width=0.025)
    c.poly([(x0 + 0.05, y0 + 0.1), (x1 - 0.05, y0 + 0.1), (x1 - 0.02, top - 0.1), (x0 + 0.02, top - 0.1)], fill=WALNUT, outline=OUTLINE, width=0.015)
    c.poly([(x0 + 0.05, y0 + 0.1), (x0 + 0.05 + w * 0.3, y0 + 0.1), (x0 + 0.02 + w * 0.3, top - 0.1), (x0 + 0.02, top - 0.1)], fill=hexc("#0b0d10"))
    c.poly([(x0 + 0.05 + w * 0.22, y0 + 0.12), (x0 + 0.12 + w * 0.3, y0 + 0.1), (x0 + 0.1 + w * 0.3, top - 0.1), (x0 + 0.02 + w * 0.22, top - 0.1)], fill=WALNUT_L, outline=OUTLINE, width=0.012)
    for sy in (top * 0.3 + y0 * 0.7, top * 0.65 + y0 * 0.35):
        c.rect(x0 + 0.02, sy, x1 - 0.02, sy + 0.03, fill=BRASS, outline=OUTLINE, width=0.01)
    c.ellipse(x0 + 0.08 + w * 0.15, (y0 + top) / 2, 0.02, 0.02, fill=PALE)        # etwas Helles im Spalt
    cobweb(c, x1 + 0.06, top, 0.12, -1, -1, seed=idx)


def _nebelmaschine(p, c, x0, y0, x1, y1, idx, rnd):
    """Nebelmaschine der Crew mit Nebelfahne, Griff und Kabel."""
    p.box(x0, y0, x1, y1, 0, 0.35, MATTE_L, MATTE)
    fz = y0
    c.rect(x0 + 0.05, fz + 0.04, x0 + 0.25, fz + 0.14, fill=MATTE_D, outline=OUTLINE, width=0.01)
    c.ellipse(x1 - 0.12, fz + 0.1, 0.02, 0.02, fill=hexc("#4caf50"))
    c.rect(x0 + 0.2, y1 + 0.35 * K, x1 - 0.2, y1 + 0.35 * K + 0.06, fill=STEEL, outline=OUTLINE, width=0.012)
    for k in range(4):
        c.ellipse(x0 - 0.1 - k * 0.14, fz + 0.06 + k * 0.03, 0.1 + k * 0.05, 0.06 + k * 0.03, fill=alpha(hexc("#d8dce8"), 120 - k * 25))
    cable(c, [(x1, fz + 0.06), (x1 + 0.15, fz - 0.02), (x1 + 0.3, fz - 0.15)], seed=idx, w=0.02)


def _orrery(p, c, x0, y0, x1, y1, idx, rnd):
    """Planetenmodell auf Messingsaeule: Sonne in der Mitte, drei Planeten auf Armen."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    c.ellipse(cx, cy, r, r * 0.55, fill=WALNUT, outline=OUTLINE, width=0.02)
    p.cyl(cx, cy, 0.04, 0, 1.0, BRASS_L, BRASS, ry=0.02)
    zt = cy + 1.0 * K
    c.ellipse(cx, zt + 0.02, 0.06, 0.06, fill=hexc("#e8b830"), outline=OUTLINE, width=0.012)
    c.glow(cx, zt + 0.02, 0.1, hexc("#e8b830"), 0.4)
    for k, (ra, pr, col) in enumerate(((0.16, 0.025, hexc("#6a8ac8")), (0.26, 0.035, hexc("#c86a3a")), (0.36, 0.02, hexc("#c8c8c8")))):
        a = 0.6 * k + idx
        px, py = cx + ra * math.cos(a), zt + 0.02 + ra * 0.5 * math.sin(a)
        c.ellipse(cx, zt + 0.02, ra, ra * 0.5, outline=BRASS, width=0.01)
        c.line([(cx, zt + 0.02), (px, py)], fill=BRASS_L, width=0.008)
        c.ellipse(px, py, pr, pr, fill=col, outline=OUTLINE, width=0.01)


def _buecherstapel(p, c, x0, y0, x1, y1, idx, rnd):
    """Buecherstapel am Boden (zwei Stapel), ein Buch aufgeschlagen."""
    cx = (x0 + x1) / 2
    book_stack(c, cx - 0.1, y0 + 0.02, 5, w=min(0.3, x1 - x0 - 0.05), rnd=rnd)
    book_stack(c, cx + 0.12, y0 + 0.1, 3, w=min(0.26, x1 - x0 - 0.1), rnd=rnd)
    c.poly([(x0, y1 - 0.1), (x0 + 0.3, y1 - 0.12), (x0 + 0.3, y1 + 0.06), (x0, y1 + 0.08)], fill=CREAM, outline=OUTLINE, width=0.01)
    c.line([(x0 + 0.15, y1 - 0.11), (x0 + 0.15, y1 + 0.07)], fill=alpha(OUTLINE, 150), width=0.008)


def _sternkarte_datum(p, c, x0, y0, x1, y1, idx, rnd):
    """Sternkarte an der Wand mit einem rot eingekreisten Datum und Zahlen am Rand."""
    fy0, fy1 = wall_board(p, c, x0, y0, x1, y1, 0.9, 1.1, WALNUT_D)
    c.rect(x0 + 0.05, fy0 + 0.05, x1 - 0.05, fy1 - 0.05, fill=hexc("#1a2234"), outline=OUTLINE, width=0.012)
    for _ in range(40):
        c.ellipse(rnd.uniform(x0 + 0.1, x1 - 0.1), rnd.uniform(fy0 + 0.1, fy1 - 0.1), 0.006, 0.006, fill=hexc("#dfe8f0"))
    for k in range(3):
        c.ellipse((x0 + x1) / 2 + 0.1 * k - 0.1, (fy0 + fy1) / 2 + 0.05 * k, 0.08 + 0.1 * k, 0.05 + 0.06 * k, outline=alpha(hexc("#dfe8f0"), 70), width=0.006)
    c.text((x0 + x1) / 2, fy1 - 0.14, "OCT 31", 0.07, RED)
    c.ellipse((x0 + x1) / 2, fy1 - 0.14, 0.25, 0.09, outline=RED, width=0.015)
    c.text(x0 + 0.3, fy0 + 0.12, "HOLLOWMERE SKY", 0.035, hexc("#8ab0d8"))


# ------------------------------------------------------------------ Heizungskeller, Bibliothek, Kapelle

def _rohre(p, c, x0, y0, x1, y1, idx, rnd):
    """Rohrleitungen an der Nordwand: zwei Rohre mit Ventilen, Dampf an einer Muffe, Rost."""
    for k, z in enumerate((1.3, 1.7)):
        py = y0 + z * K
        c.line([(x0, py), (x1, py)], fill=OUTLINE, width=0.09)
        c.line([(x0, py), (x1, py)], fill=IRON, width=0.065)
        c.line([(x0 + 0.02, py + 0.015), (x1 - 0.02, py + 0.015)], fill=IRON_L, width=0.012)
        for j in range(3):
            mx = x0 + 0.5 + j * (x1 - x0 - 1.0) / 2 + k * 0.2
            c.rect(mx - 0.05, py - 0.05, mx + 0.05, py + 0.05, fill=IRON_D, outline=OUTLINE, width=0.012)
    vx = x0 + 1.2
    c.rect(vx - 0.02, y0 + 1.3 * K, vx + 0.02, y0 + 1.6 * K, fill=IRON, outline=OUTLINE, width=0.01)
    c.ellipse(vx, y0 + 1.3 * K + 0.1, 0.08, 0.04, outline=OUTLINE, width=0.035)
    c.ellipse(vx, y0 + 1.3 * K + 0.1, 0.08, 0.04, outline=RED, width=0.016)
    smoke(c, x1 - 0.5, y0 + 1.7 * K + 0.04, seed=idx, h=0.3)
    for k in range(4):
        c.ellipse(x0 + 0.3 + k * 0.7, y0 + 1.3 * K - 0.02, 0.03, 0.015, fill=alpha(hexc("#8a4a2a"), 150))
    for j in range(2):                                                                  # Halterungen zur Wand
        hx = x0 + 0.9 + j * 1.6
        c.rect(hx - 0.03, y0 + 0.02, hx + 0.03, y0 + 1.3 * K, fill=alpha(IRON_D, 120))


def _handabdruck_russ(p, c, x0, y0, x1, y1, idx, rnd):
    """Handabdruck in Russ an der Westwand, mit Schleifspur nach unten."""
    hx, hy = (x0 + x1) / 2 + 0.05, y0 + 1.2 * K
    soot = alpha((20, 18, 18, 255), 170)
    c.ellipse(hx, hy, 0.07, 0.06, fill=soot)
    for dx, ln in ((-0.06, 0.08), (-0.02, 0.11), (0.02, 0.115), (0.06, 0.09)):
        c.line([(hx + dx, hy + 0.04), (hx + dx * 1.3, hy + 0.04 + ln)], fill=soot, width=0.03)
    c.line([(hx - 0.09, hy - 0.01), (hx - 0.14, hy + 0.06)], fill=soot, width=0.03)
    for k in range(4):
        c.line([(hx - 0.05 + k * 0.035, hy - 0.05), (hx - 0.04 + k * 0.035, hy - 0.4 - k * 0.05)], fill=alpha((20, 18, 18, 255), 110), width=0.016)


def _garderobe(p, c, x0, y0, x1, y1, idx, rnd):
    """Garderobe: Holzleiste mit Haken, Maentel, Hut, Schirm; ein Mantel zu viel."""
    p.box(x0, y0, x1, y1, 0, 1.9, WALNUT_L, WALNUT)
    top = y0 + 1.9 * K
    c.rect(x0 - 0.05, top - 0.14, x1 + 0.05, top - 0.08, fill=WALNUT_D, outline=OUTLINE, width=0.012)
    n = max(2, int((y1 - y0) / 0.45))
    for k in range(n):
        hx = x0 + (x1 - x0) / 2 + (k - (n - 1) / 2) * 0.1
        hy = top - 0.11
        c.ellipse(hx, hy, 0.015, 0.015, fill=BRASS, outline=OUTLINE, width=0.008)
        col = (MATTE_D, hexc("#4a4a5a"), LEATHER, hexc("#3a4a3a"))[(k + idx) % 4]
        c.poly([(hx - 0.14, hy - 0.05), (hx + 0.14, hy - 0.05), (hx + 0.18, hy - 0.9), (hx - 0.18, hy - 0.9)], fill=col, outline=OUTLINE, width=0.015)
        c.line([(hx, hy - 0.08), (hx, hy - 0.85)], fill=alpha(shade(col, 0.6), 160), width=0.012)
    c.ellipse(x0 + (x1 - x0) / 2 - 0.1, top - 0.02, 0.09, 0.04, fill=MATTE_D, outline=OUTLINE, width=0.012)   # Hut
    c.rect(x0 + (x1 - x0) / 2 - 0.15, top - 0.08, x0 + (x1 - x0) / 2 - 0.05, top - 0.02, fill=MATTE_D, outline=OUTLINE, width=0.012)
    c.line([(x1 + 0.05, y0 + 0.02), (x1 + 0.1, top - 0.3)], fill=OUTLINE, width=0.03)                         # Schirm
    c.line([(x1 + 0.05, y0 + 0.02), (x1 + 0.1, top - 0.3)], fill=MATTE, width=0.016)
    c.ellipse(x1 + 0.1, top - 0.3, 0.02, 0.02, fill=WALNUT_L, outline=OUTLINE, width=0.008)


def _klingelbrett(p, c, x0, y0, x1, y1, idx, rnd):
    """Dienstbotenklingelbrett: Holztafel mit Glocken und Raumnamen, eine Glocke schief (laeutet)."""
    fy0, fy1 = wall_board(p, c, x0, y0, x1, y1, 1.0, 0.75, WALNUT_D)
    rooms = ["STUDY", "SEANCE", "LIBRARY", "CHAPEL", "NURSERY"]
    n = len(rooms)
    for k, name in enumerate(rooms):
        bx = x0 + (x1 - x0) * (k + 0.5) / n if (x1 - x0) > (y1 - y0) else (x0 + x1) / 2
        by = fy0 + 0.12 + (k * (fy1 - fy0 - 0.3) / (n - 1) if (x1 - x0) <= (y1 - y0) else 0)
        tilt = 0.25 if k == 4 else 0.0
        c.poly([(bx - 0.04 - tilt * 0.1, by), (bx + 0.04 - tilt * 0.1, by), (bx + 0.025, by + 0.07 + tilt * 0.02), (bx - 0.025, by + 0.07 + tilt * 0.02)], fill=BRASS, outline=OUTLINE, width=0.01)
        c.ellipse(bx - tilt * 0.1, by - 0.01, 0.012, 0.01, fill=BRASS_D)
        c.rect(bx + 0.06, by + 0.0, bx + 0.26, by + 0.05, fill=CREAM, outline=OUTLINE, width=0.006)
        c.text(bx + 0.16, by + 0.025, name, 0.02, OUTLINE)
    c.text((x0 + x1) / 2 + 0.1, fy1 - 0.05, "SERVANTS", 0.028, BRASS_L)


def _rauchendes_buch(p, c, x0, y0, x1, y1, idx, rnd):
    """Aufgeschlagenes Buch am Boden, aus dem Rauch steigt; Seiten angesengt."""
    cx = (x0 + x1) / 2
    c.poly([(x0, y0 + 0.02), (cx, y0 + 0.06), (x1, y0 + 0.02), (x1, y1), (cx, y1 + 0.04), (x0, y1)], fill=CREAM, outline=OUTLINE, width=0.012)
    c.line([(cx, y0 + 0.06), (cx, y1 + 0.04)], fill=alpha(OUTLINE, 150), width=0.01)
    for k in range(3):
        c.line([(x0 + 0.05, y0 + 0.08 + k * 0.06), (cx - 0.04, y0 + 0.1 + k * 0.06)], fill=alpha(OUTLINE, 90), width=0.005)
        c.line([(cx + 0.04, y0 + 0.1 + k * 0.06), (x1 - 0.05, y0 + 0.08 + k * 0.06)], fill=alpha(OUTLINE, 90), width=0.005)
    c.ellipse(x1 - 0.05, y1 - 0.02, 0.06, 0.04, fill=alpha((40, 30, 24, 255), 180))
    smoke(c, cx + 0.1, y1 + 0.03, seed=idx, h=0.4)
    c.glow(cx + 0.08, y1 - 0.02, 0.08, hexc("#ff8a3c"), 0.5)


def _leiter(p, c, x0, y0, x1, y1, idx, rnd):
    """Bibliotheksleiter, ans Regal gelehnt."""
    top = y1 + 2.3 * K
    for px in (x0 + 0.05, x1 - 0.05):
        c.line([(px, y0 + 0.02), (px + 0.08, top)], fill=OUTLINE, width=0.045)
        c.line([(px, y0 + 0.02), (px + 0.08, top)], fill=WOOD_LIGHT, width=0.028)
    for k in range(8):
        t = (k + 0.5) / 8
        ly = y0 + 0.02 + (top - y0 - 0.02) * t
        c.line([(x0 + 0.05 + 0.08 * t, ly), (x1 - 0.05 + 0.08 * t, ly)], fill=OUTLINE, width=0.035)
        c.line([(x0 + 0.05 + 0.08 * t, ly), (x1 - 0.05 + 0.08 * t, ly)], fill=shade(WOOD_LIGHT, 1.1), width=0.02)


def _globus(p, c, x0, y0, x1, y1, idx, rnd):
    """Standglobus auf Holzgestell, Messingring, Kontinente in Sepia."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    for a in (0.5, 2.6, 4.7):
        c.line([(cx, cy + 0.3 * K), (cx + r * math.cos(a), cy + r * 0.55 * math.sin(a))], fill=OUTLINE, width=0.035)
        c.line([(cx, cy + 0.3 * K), (cx + r * math.cos(a), cy + r * 0.55 * math.sin(a))], fill=WALNUT, width=0.02)
    gz = cy + 0.85 * K
    c.ellipse(cx, gz, r * 0.95, r * 0.95, fill=hexc("#c8b888"), outline=OUTLINE, width=0.02)
    for (ox, oy, rx, ry) in ((-0.08, 0.06, 0.08, 0.06), (0.09, -0.02, 0.06, 0.08), (-0.02, -0.12, 0.09, 0.04)):
        c.ellipse(cx + ox * r / 0.3, gz + oy * r / 0.3, rx * r / 0.3, ry * r / 0.3, fill=hexc("#8a7a4a"))
    c.ellipse(cx, gz, r * 1.05, r * 0.35, outline=BRASS, width=0.02)
    c.line([(cx - r * 1.1, gz - r * 0.2), (cx - r * 1.05, gz + r * 1.1), (cx + r * 1.05, gz + r * 1.1)], fill=BRASS_D, width=0.02)
    c.ellipse(cx, gz + r * 1.1, 0.02, 0.02, fill=BRASS, outline=OUTLINE, width=0.008)


def _lesesessel(p, c, x0, y0, x1, y1, idx, rnd):
    """Ohrensessel mit Decke, eine Buchseite auf der Armlehne."""
    col = hexc("#3a5a4a")
    p.box(x0, y0, x1, y1 - 0.25, 0, 0.5, shade(col, 1.15), col)
    p.box(x0, y0 + 0.05, x0 + 0.15, y1 - 0.2, 0.5, 0.25, shade(col, 1.2), shade(col, 0.9))
    p.box(x1 - 0.15, y0 + 0.05, x1, y1 - 0.2, 0.5, 0.25, shade(col, 1.2), shade(col, 0.9))
    p.box(x0, y1 - 0.25, x1, y1, 0.5, 0.75, shade(col, 1.15), shade(col, 0.95))
    top = y1 + 1.25 * K
    c.poly([(x0, top - 0.02), (x0 + 0.1, top + 0.12), (x1 - 0.1, top + 0.12), (x1, top - 0.02)], fill=shade(col, 1.1), outline=OUTLINE, width=0.015)
    c.poly([(x0 + 0.1, y0 + 0.5 * K + 0.05), (x0 + 0.55, y0 + 0.5 * K + 0.02), (x0 + 0.5, y0 + 0.5 * K + 0.3), (x0 + 0.08, y0 + 0.5 * K + 0.32)], fill=hexc("#8a6a5a"), outline=OUTLINE, width=0.012)   # Decke
    c.poly([(x1 - 0.14, y0 + 0.75 * K + 0.02), (x1, y0 + 0.75 * K), (x1, y0 + 0.75 * K + 0.1), (x1 - 0.14, y0 + 0.75 * K + 0.12)], fill=CREAM, outline=OUTLINE, width=0.01)


def _laterne(p, c, x0, y0, x1, y1, idx, rnd):
    """Sturmlaterne am Boden, brennt."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c.ellipse(cx, cy, 0.12, 0.06, fill=IRON, outline=OUTLINE, width=0.015)
    c.rect(cx - 0.08, cy, cx + 0.08, cy + 0.3, fill=GLASS_C, outline=OUTLINE, width=0.015)
    c.rect(cx - 0.03, cy + 0.02, cx + 0.03, cy + 0.1, fill=IRON_D)
    flame(c, cx, cy + 0.1, 0.9)
    c.ellipse(cx, cy + 0.3, 0.1, 0.04, fill=IRON, outline=OUTLINE, width=0.015)
    c.ellipse(cx, cy + 0.42, 0.06, 0.05, outline=OUTLINE, width=0.03)
    c.ellipse(cx, cy + 0.42, 0.06, 0.05, outline=IRON_L, width=0.014)
    VA.floor_light(c, cx, cy - 0.05, 0.6, 0.3, WARM, 0.35, seed=idx)


def _engelsstatue_tuch(p, c, x0, y0, x1, y1, idx, rnd):
    """Verhuellte Statue in der Kapelle, neu 24.10.: Steinsockel mit Inschrift, darueber ein staubiges Leinentuch
    ueber einer Engelsform (Kopf, Schultern, ein Fluegel zeichnen sich ab), schwere Falten mit haengendem Saum,
    ein gesprungener Fluegel und eine Steinhand ragen heraus, Spinnweben, Staub."""
    cx = (x0 + x1) / 2
    p.box(x0, y0, x1, y1, 0, 0.3, hexc("#8c9098"), hexc("#7c8088"))
    c.rect(x0 + 0.08, y0 + 0.04, x1 - 0.08, y0 + 0.3 * K - 0.03, outline=alpha(hexc("#5a5e66"), 200), width=0.01)
    c.text(cx, y0 + 0.3 * K / 2, "ANNO 1888", 0.04, hexc("#5a5e66"))
    base = y0 + 0.3 * K
    top = y1 + 2.0 * K
    hw = (x1 - x0) / 2
    pts = VA.HD.wobble([(cx - hw - 0.08, base), (cx + hw + 0.08, base), (cx + hw + 0.02, base + 0.5), (cx + hw * 0.85, top - 0.6),
                        (cx + hw * 0.9, top - 0.35), (cx + 0.2, top - 0.22), (cx + 0.13, top), (cx - 0.13, top), (cx - 0.2, top - 0.22),
                        (cx - hw * 0.8, top - 0.4), (cx - hw * 0.7, top - 0.7), (cx - hw - 0.02, base + 0.5)], amp=0.015, seed=idx, step=0.06, closed=True)
    c.poly(pts, fill=LINEN, outline=OUTLINE, width=0.03)
    # Saum mit Wellen
    for k in range(int((2 * hw + 0.16) / 0.12)):
        sx = cx - hw - 0.08 + 0.06 + k * 0.12
        c.ellipse(sx, base, 0.06, 0.03, fill=LINEN, outline=OUTLINE, width=0.012)
    # Falten (dunkel) und Lichtkanten
    for k in range(5):
        c.line(VA.HD.wobble([(cx - 0.22 + k * 0.11, top - 0.3 - abs(k - 2) * 0.1), (cx - 0.32 + k * 0.16, base + 0.08)], amp=0.015, seed=idx + k, step=0.05),
               fill=alpha(LINEN_D, 160), width=0.016)
    c.line(VA.HD.wobble([(cx - 0.1, top - 0.1), (cx - 0.16, base + 0.3)], amp=0.01, seed=idx + 9, step=0.05), fill=alpha((255, 255, 255, 255), 110), width=0.02)
    # Kopfform und Schulter unter dem Tuch
    c.ellipse(cx, top - 0.14, 0.14, 0.11, outline=alpha(LINEN_D, 120), width=0.014)
    c.line([(cx + 0.14, top - 0.26), (cx + hw * 0.85, top - 0.4)], fill=alpha(LINEN_D, 110), width=0.016)
    c.ellipse(cx - 0.05, top - 0.17, 0.03, 0.025, fill=alpha(LINEN_D, 170))
    c.ellipse(cx + 0.06, top - 0.17, 0.03, 0.025, fill=alpha(LINEN_D, 170))
    # Fluegel ragt rechts heraus (gesprungen), Steinhand links unten
    wing = [(cx + hw * 0.8, top - 0.7), (cx + hw + 0.36, top - 0.42), (cx + hw + 0.4, top - 0.7), (cx + hw + 0.28, top - 0.95), (cx + hw * 0.85, top - 1.0)]
    c.poly(wing, fill=hexc("#9a9ea6"), outline=OUTLINE, width=0.025)
    for k in range(3):
        c.line([(cx + hw * 0.9, top - 0.78 - k * 0.06), (cx + hw + 0.3, top - 0.55 - k * 0.08)], fill=alpha(hexc("#6a6e76"), 170), width=0.01)
    crack(c, [(cx + hw + 0.1, top - 0.95), (cx + hw + 0.2, top - 0.7), (cx + hw + 0.15, top - 0.5)], seed=idx)
    hand = (cx - hw - 0.02, base + 0.55)
    c.ellipse(hand[0], hand[1], 0.07, 0.05, fill=hexc("#9a9ea6"), outline=OUTLINE, width=0.02)
    for k in range(4):
        c.line([(hand[0] - 0.02 + k * 0.02, hand[1] - 0.02), (hand[0] - 0.08 + k * 0.025, hand[1] - 0.12)], fill=OUTLINE, width=0.03)
        c.line([(hand[0] - 0.02 + k * 0.02, hand[1] - 0.02), (hand[0] - 0.08 + k * 0.025, hand[1] - 0.12)], fill=hexc("#9a9ea6"), width=0.016)
    cobweb(c, cx + 0.13, top, 0.16, 1, -1, seed=idx)
    dust(c, cx - 0.2, top - 0.6, cx + 0.2, top - 0.3, 6, seed=idx)
    VA.moss(c, x0 + 0.1, y0 + 0.05, 0.08, seed=idx)


def _zersplitterte_bank(p, c, x0, y0, x1, y1, idx, rnd):
    """Zersplitterte Kirchenbank, Blick nach Norden wie die anderen (Lehne an der Suedkante): das rechte Ende ist
    eingebrochen, die Lehne haengt schief, Holzsplitter und ein Gebetbuch am Boden."""
    seat_h, back_h = 0.45, 0.95
    # linke Wange steht, rechte liegt umgekippt
    p.box(x0, y0, x0 + 0.1, y1, 0, back_h, WALNUT_L, WALNUT, w=0.025)
    c.poly([(x1 - 0.15, y0 - 0.02), (x1 + 0.3, y0 + 0.02), (x1 + 0.32, y0 + 0.1), (x1 - 0.13, y0 + 0.06)], fill=WALNUT, outline=OUTLINE, width=0.02)
    # Sitz: links auf Hoehe, rechts abgesackt
    sl, sr = y0 + 0.12 + seat_h * K, y0 + 0.12 + 0.15 * K
    c.poly([(x0 + 0.1, sl - 0.04), (x1 - 0.1, sr - 0.03), (x1 - 0.1, sr), (x0 + 0.1, sl)], fill=WALNUT, outline=OUTLINE, width=0.02)
    c.poly([(x0 + 0.1, sl), (x1 - 0.1, sr), (x1 - 0.1, sr + (y1 - y0 - 0.16)), (x0 + 0.1, sl + (y1 - y0 - 0.16))], fill=WALNUT_L, outline=OUTLINE, width=0.02)
    # Lehne vorn, schief und gebrochen
    tl, tr = y0 + back_h * K, y0 + 0.5 * K
    c.poly([(x0 + 0.1, y0 + 0.02), (x1 - 0.1, y0 + 0.02), (x1 - 0.1, tr), (x0 + 0.1, tl)], fill=WALNUT, outline=OUTLINE, width=0.025)
    c.poly([(x0 + 0.16, y0 + 0.1), (x0 + 0.9, y0 + 0.1), (x0 + 0.9, tl - 0.3), (x0 + 0.16, tl - 0.16)], fill=shade(WALNUT, 0.9), outline=WALNUT_D, width=0.012)
    c.poly([(x0 + 0.1, tl - 0.03), (x1 - 0.1, tr - 0.03), (x1 - 0.1, tr + 0.03), (x0 + 0.1, tl + 0.04)], fill=WALNUT_L, outline=OUTLINE, width=0.02)
    bx = (x0 + x1) / 2 + 0.2                                                                       # Bruchkante mit Splittern
    for k in range(5):
        sx = bx + k * 0.08
        c.poly([(sx, tr + 0.02 + k * 0.01), (sx + 0.03, tr + 0.02 + k * 0.01), (sx + 0.04, tr + 0.14 + 0.04 * (k % 2))], fill=WOOD_LIGHT, outline=OUTLINE, width=0.008)
    for k in range(4):                                                                             # Splitter am Boden
        sx = x1 - 0.5 + k * 0.12
        c.poly([(sx, y0 - 0.04), (sx + 0.08, y0 - 0.1 + 0.02 * k), (sx + 0.1, y0 - 0.06 + 0.02 * k)], fill=WOOD_LIGHT, outline=OUTLINE, width=0.008)
    c.poly([(x1 - 0.25, y0 - 0.1), (x1 + 0.05, y0 - 0.13), (x1 + 0.08, y0 - 0.02), (x1 - 0.22, y0 + 0.01)], fill=WOOD_LIGHT, outline=OUTLINE, width=0.012)
    c.rect(x0 + 0.3, y0 - 0.12, x0 + 0.48, y0 - 0.02, fill=hexc("#3a2a3a"), outline=OUTLINE, width=0.01)   # Gebetbuch am Boden
    c.line([(x0 + 0.36, y0 - 0.07), (x0 + 0.42, y0 - 0.07)], fill=BRASS, width=0.008)
    cobweb(c, x0, y1 + back_h * K, 0.14, 1, -1, seed=idx)


# ------------------------------------------------------------------ Halle, Regie, Maske

def _regiestuhl(p, c, x0, y0, x1, y1, idx, rnd):
    """Regiestuhl: Holz-Klappgestell, Stoffsitz und Lehne."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w = x1 - x0
    for sx in (x0 + 0.08, x1 - 0.08):
        c.line([(sx, y0 + 0.02), (sx + 0.1, y0 + 0.55 * K + 0.1)], fill=OUTLINE, width=0.035)
        c.line([(sx, y0 + 0.02), (sx + 0.1, y0 + 0.55 * K + 0.1)], fill=WOOD_LIGHT, width=0.02)
        c.line([(sx + 0.1, y0 + 0.02), (sx, y0 + 0.55 * K + 0.1)], fill=OUTLINE, width=0.035)
        c.line([(sx + 0.1, y0 + 0.02), (sx, y0 + 0.55 * K + 0.1)], fill=WOOD_LIGHT, width=0.02)
    c.poly([(x0 + 0.03, y0 + 0.55 * K), (x1 - 0.03, y0 + 0.55 * K), (x1 - 0.03, y1 + 0.55 * K), (x0 + 0.03, y1 + 0.55 * K)], fill=MATTE, outline=OUTLINE, width=0.015)
    for sx in (x0 + 0.06, x1 - 0.06):
        c.line([(sx, y1 + 0.55 * K), (sx, y1 + 1.1 * K)], fill=OUTLINE, width=0.035)
        c.line([(sx, y1 + 0.55 * K), (sx, y1 + 1.1 * K)], fill=WOOD_LIGHT, width=0.02)
    c.rect(x0 + 0.06, y1 + 0.85 * K, x1 - 0.06, y1 + 1.1 * K, fill=MATTE, outline=OUTLINE, width=0.015)
    c.text(cx, y1 + 0.975 * K, "CREW" if w < 0.75 else "DIRECTOR", 0.04, CREAM)


def _regiestuhl_director(p, c, x0, y0, x1, y1, idx, rnd):
    _regiestuhl(p, c, x0, y0, x1 + 0.1, y1, idx, rnd)


def _kronleuchter_boden(p, c, x0, y0, x1, y1, idx, rnd):
    """Abgestuerzter Kronleuchter: Messingarme verbogen, Kristalle verstreut, Kette nach oben abgerissen."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    c.ellipse(cx, cy, rx, ry, outline=OUTLINE, width=0.05)
    c.ellipse(cx, cy, rx, ry, outline=BRASS_D, width=0.025)
    for k in range(8):
        a = math.pi * 2 * k / 8 + 0.2
        ex, ey = cx + rx * 0.95 * math.cos(a), cy + ry * 0.95 * math.sin(a)
        c.line([(cx, cy + 0.15), (ex, ey)], fill=OUTLINE, width=0.03)
        c.line([(cx, cy + 0.15), (ex, ey)], fill=BRASS, width=0.015)
        c.rect(ex - 0.02, ey, ex + 0.02, ey + 0.1, fill=CREAM, outline=OUTLINE, width=0.008)
    c.ellipse(cx, cy + 0.15, 0.1, 0.06, fill=BRASS, outline=OUTLINE, width=0.015)
    c.line([(cx, cy + 0.2), (cx + 0.08, cy + 0.5), (cx - 0.05, cy + 0.7)], fill=BRASS_D, width=0.02)
    for _ in range(14):
        sx, sy = cx + rnd.uniform(-rx * 1.4, rx * 1.4), cy + rnd.uniform(-ry * 1.3, ry * 1.1)
        c.poly([(sx, sy), (sx + 0.03, sy + 0.015), (sx + 0.01, sy + 0.04)], fill=alpha(hexc("#dfe8f0"), 200), outline=OUTLINE, width=0.006)


def _muellcontainer(p, c, x0, y0, x1, y1, idx, rnd):
    """Muellcontainer der Crew: Metallkasten mit Deckel halb offen, Saecke, Gaffer-Aufschrift."""
    p.box(x0, y0, x1, y1, 0, 1.0, shade(hexc("#4a5a6a"), 1.15), hexc("#4a5a6a"))
    fz = y0
    c.line([(x0 + 0.05, fz + 0.3), (x1 - 0.05, fz + 0.3)], fill=shade(hexc("#4a5a6a"), 0.7), width=0.012)
    gaffer(c, x0 + 0.15, fz + 0.2, x1 - 0.15, fz + 0.2, 0.05)
    c.text((x0 + x1) / 2, fz + 0.2, "SET WASTE", 0.045, OUTLINE)
    zt = y1 + 1.0 * K
    c.poly([(x0 - 0.02, zt), (x1 + 0.02, zt), (x1 + 0.08, zt + 0.22), (x0 + 0.04, zt + 0.22)], fill=shade(hexc("#4a5a6a"), 1.25), outline=OUTLINE, width=0.02)
    for k in range(3):
        bx = x0 + 0.25 + k * 0.4
        c.ellipse(bx, y0 + 1.0 * K + 0.08, 0.17, 0.1, fill=MATTE, outline=OUTLINE, width=0.015)
        c.line([(bx - 0.04, y0 + 1.0 * K + 0.16), (bx + 0.03, y0 + 1.0 * K + 0.2)], fill=MATTE_L, width=0.01)
    c.rect(x1 - 0.2, fz + 0.4 * K, x1 - 0.1, fz + 0.4 * K + 0.3, fill=hexc("#c88a5a"), outline=OUTLINE, width=0.01)   # Donutschachtel ragt raus


def _mischpult(p, c, x0, y0, x1, y1, idx, rnd):
    """Tonmischpult auf Rollwagen: Fader, Regler, Kopfhoerer, Kabel."""
    p.box(x0, y0, x1, y1, 0, 0.8, MATTE_L, MATTE)
    zt = y0 + 0.8 * K
    c.poly([(x0, zt), (x1, zt), (x1, y1 + 0.8 * K + 0.02), (x0, y1 + 0.8 * K + 0.02)], fill=MATTE_L, outline=OUTLINE, width=0.015)
    n = max(3, int((y1 - y0) / 0.16))
    for k in range(n):
        fy = zt + 0.06 + k * (y1 - y0 - 0.1) / n
        c.line([(x0 + 0.08, fy), (x1 - 0.12, fy)], fill=MATTE_D, width=0.012)
        fx = x0 + 0.12 + rnd.uniform(0, x1 - x0 - 0.3)
        c.rect(fx - 0.025, fy - 0.015, fx + 0.025, fy + 0.015, fill=STEEL, outline=OUTLINE, width=0.008)
        c.ellipse(x1 - 0.06, fy, 0.008, 0.008, fill=hexc("#4caf50") if k % 3 else RED)
    cable(c, [(x0 + 0.1, y0), (x0 - 0.1, y0 - 0.15), (x0 - 0.2, y0 - 0.3)], seed=idx, w=0.02)


def _perueckenkoepfe(p, c, x0, y0, x1, y1, idx, rnd):
    """Regalbrett an der Westwand mit drei Perueckenkoepfen, neu 24.10.: Holzstaender, Koepfe mit Gesicht (Brauen,
    Wimpern, Mund), drei verschiedene Peruecken (schwarze Lockenhaube, blonder Bob mit Pony, rote lange Wellen),
    einer zur Wand gedreht, ein Handspiegel und Haarnadeln auf dem Brett."""
    p.box(x0, y0, x1, y1, 0, 0.9, WALNUT_L, WALNUT)
    c.rect(x0 + 0.03, y0 + 0.2 * K, x1 - 0.03, y0 + 0.75 * K, outline=WALNUT_D, width=0.012)                 # Tuerfuge
    c.ellipse((x0 + x1) / 2 + 0.1, y0 + 0.47 * K, 0.018, 0.014, fill=BRASS, outline=OUTLINE, width=0.01)
    zt = y0 + 0.9 * K
    n = 3
    for k in range(n):
        hy = zt + 0.04 + k * (y1 - y0 - 0.12) / (n - 1) * 0.5
        hx = (x0 + x1) / 2 + (k - 1) * 0.03
        c.rect(hx - 0.035, hy, hx + 0.035, hy + 0.09, fill=WALNUT_D, outline=OUTLINE, width=0.012)          # Staender
        c.ellipse(hx, hy, 0.06, 0.02, fill=WALNUT, outline=OUTLINE, width=0.01)
        c.ellipse(hx, hy + 0.2, 0.085, 0.11, fill=PALE, outline=OUTLINE, width=0.014)                        # Kopf
        wig = (hexc("#2a2026"), hexc("#d8b25a"), hexc("#9a2a22"))[(k + idx) % 3]
        if k == 2:                                                                                      # zur Wand gedreht
            c.ellipse(hx, hy + 0.22, 0.09, 0.1, fill=wig, outline=OUTLINE, width=0.012)
            for j in range(3):
                c.line([(hx - 0.05 + j * 0.05, hy + 0.14), (hx - 0.04 + j * 0.05, hy + 0.3)], fill=shade(wig, 1.4), width=0.008)
            continue
        c.line([(hx - 0.045, hy + 0.23), (hx - 0.015, hy + 0.235)], fill=OUTLINE, width=0.012)              # Brauen
        c.line([(hx + 0.015, hy + 0.235), (hx + 0.045, hy + 0.23)], fill=OUTLINE, width=0.012)
        for s in (-1, 1):                                                                               # Augen mit Wimpern
            c.ellipse(hx + s * 0.03, hy + 0.2, 0.016, 0.012, fill=(250, 246, 240, 255), outline=OUTLINE, width=0.008)
            c.ellipse(hx + s * 0.03, hy + 0.2, 0.007, 0.007, fill=OUTLINE)
            c.line([(hx + s * 0.045, hy + 0.21), (hx + s * 0.06, hy + 0.225)], fill=OUTLINE, width=0.008)
        c.line([(hx - 0.02, hy + 0.14), (hx + 0.02, hy + 0.14)], fill=hexc("#b0304a"), width=0.012)         # Mund
        if (k + idx) % 3 == 0:                                                                          # Lockenhaube
            c.ellipse(hx, hy + 0.27, 0.1, 0.07, fill=wig, outline=OUTLINE, width=0.012)
            for j in range(5):
                a = math.pi * (0.15 + j * 0.175)
                c.ellipse(hx + 0.095 * math.cos(a), hy + 0.24 + 0.06 * math.sin(a), 0.03, 0.03, fill=wig, outline=OUTLINE, width=0.01)
            c.ellipse(hx - 0.03, hy + 0.3, 0.025, 0.012, fill=shade(wig, 1.8))
        elif (k + idx) % 3 == 1:                                                                        # blonder Bob mit Pony
            c.poly([(hx - 0.1, hy + 0.28), (hx + 0.1, hy + 0.28), (hx + 0.1, hy + 0.12), (hx + 0.07, hy + 0.1), (hx + 0.07, hy + 0.25),
                    (hx - 0.07, hy + 0.25), (hx - 0.07, hy + 0.1), (hx - 0.1, hy + 0.12)], fill=wig, outline=OUTLINE, width=0.012)
            c.poly([(hx - 0.08, hy + 0.3), (hx + 0.08, hy + 0.3), (hx + 0.06, hy + 0.25), (hx - 0.06, hy + 0.25)], fill=wig, outline=OUTLINE, width=0.01)
            c.line([(hx - 0.04, hy + 0.3), (hx - 0.03, hy + 0.14)], fill=shade(wig, 1.25), width=0.01)
        else:                                                                                           # rote lange Wellen
            c.poly(VA.HD.wobble([(hx - 0.11, hy + 0.3), (hx + 0.11, hy + 0.3), (hx + 0.13, hy + 0.02), (hx + 0.08, hy - 0.02), (hx + 0.07, hy + 0.26),
                                 (hx - 0.07, hy + 0.26), (hx - 0.08, hy - 0.02), (hx - 0.13, hy + 0.02)], amp=0.01, seed=idx + k, step=0.04, closed=True),
                   fill=wig, outline=OUTLINE, width=0.012)
            c.line([(hx - 0.1, hy + 0.26), (hx - 0.11, hy + 0.04)], fill=shade(wig, 1.3), width=0.01)
    # Handspiegel und Haarnadeln vorn auf dem Brett
    mx, my = x1 - 0.1, zt + 0.06
    c.ellipse(mx, my + 0.08, 0.05, 0.04, fill=BRASS, outline=OUTLINE, width=0.012)
    c.ellipse(mx, my + 0.08, 0.035, 0.028, fill=hexc("#aebfd0"))
    c.line([(mx, my + 0.04), (mx + 0.02, my - 0.04)], fill=BRASS, width=0.015)
    for j in range(3):
        c.line([(x0 + 0.06 + j * 0.03, zt + 0.03), (x0 + 0.1 + j * 0.03, zt + 0.08)], fill=hexc("#2a2a30"), width=0.006)


def _kunstblutregal(p, c, x0, y0, x1, y1, idx, rnd):
    """Nordwand der Maske: Regal mit Kunstblutflaschen und Schminkdosen, darueber Spiegel mit Gluehbirnen
    und Lippenstift-Schrift GET OUT; Blut tropft vom Brett."""
    p.box(x0, y0, x1, y1, 0, 0.95, shade(LINEN, 0.95), shade(LINEN, 0.8))
    zt = y0 + 0.95 * K
    for k in range(6):
        bx = x0 + 0.15 + k * (x1 - x0 - 0.3) / 5
        col = (BLOOD, hexc("#c8402a"), hexc("#7a4a2a"), hexc("#e0d0b0"))[(k + idx) % 4]
        bottle(c, bx, zt + 0.02, 0.2 + (k % 2) * 0.08, col, CREAM if k % 2 else None, 0.028)
    c.ellipse(x1 - 0.22, zt + 0.08, 0.06, 0.035, fill=hexc("#e0c0c8"), outline=OUTLINE, width=0.01)     # Puderdose
    blood_drips(c, x0 + 0.3, zt - 0.02, 4, 0.16, seed=idx)
    # Spiegel ueber dem Regal
    my0, my1 = zt + 0.45, zt + 1.15
    c.rect(x0 + 0.2, my0, x1 - 0.2, my1, fill=WALNUT_D, outline=OUTLINE, width=0.02)
    c.rect(x0 + 0.26, my0 + 0.06, x1 - 0.26, my1 - 0.06, fill=hexc("#9ab0c0"), outline=OUTLINE, width=0.012)
    c.line([(x0 + 0.3, my1 - 0.1), (x1 - 0.4, my0 + 0.1)], fill=alpha(hexc("#ffffff"), 70), width=0.03)
    for k in range(7):
        lx = x0 + 0.26 + k * (x1 - x0 - 0.52) / 6
        for ly in (my0 + 0.02, my1 - 0.02):
            c.ellipse(lx, ly, 0.025, 0.025, fill=hexc("#fff0c8"), outline=OUTLINE, width=0.008)
            c.glow(lx, ly, 0.05, WARM, 0.4)
    c.text((x0 + x1) / 2, (my0 + my1) / 2, "GET OUT", 0.1, hexc("#c8203a"))


# ------------------------------------------------------------------ Galerie, Jagdzimmer

def _portrait(p, c, x0, y0, x1, y1, idx, rnd, variant=None):
    """Ahnenportraet an der Wand (an Ost- oder Westwand), zerkratzte Augen bei jedem zweiten.
    variant "l"/"r": Blick nach links/rechts (Mitternachtsuhr, Hinweis auf die gemeldete Leiche)."""
    gaze = {"l": -1, "r": 1}.get(variant, 0)
    vertical = (y1 - y0) > (x1 - x0)
    if vertical:
        # Wandbild entlang einer senkrechten Wand: von vorn gezeichnet, Breite = Wandlaenge
        fx0, fx1 = x0 - 0.3, x1 + 0.3
        fy0, fy1 = y0 + 1.0 * K, y0 + 1.0 * K + (y1 - y0) * 0.9
        picture(c, (fx0 + fx1) / 2 - 0.3, fy0, (fx0 + fx1) / 2 + 0.3, fy1, hexc("#8a6a2a") if idx % 2 else WALNUT_D, hexc("#4a3a3a"), idx, scratched=(idx % 2 == 0), gaze=gaze)
    else:
        fy0, fy1 = y0 + 1.0 * K, y0 + 1.0 * K + 0.9
        picture(c, x0, fy0, x1, fy1, hexc("#8a6a2a") if idx % 2 else WALNUT_D, hexc("#4a3a3a"), idx, scratched=(idx % 2 == 0), gaze=gaze)


def _leerer_rahmen(p, c, x0, y0, x1, y1, idx, rnd):
    """Leerer Rahmen: die Figur ist aus dem Bild verschwunden, nur Tapete dahinter."""
    cx = (x0 + x1) / 2
    fy0, fy1 = y0 + 1.0 * K, y0 + 1.0 * K + (y1 - y0) * 0.9
    picture(c, cx - 0.3, fy0, cx + 0.3, fy1, hexc("#8a6a2a"), hexc("#4a3a3a"), idx, empty=True)
    c.text(cx, fy1 + 0.06, "?", 0.08, alpha(CREAM, 120))


def _buesten_saeule(p, c, x0, y0, x1, y1, idx, rnd):
    """Marmorbueste auf kannelierter Saeule, neu 24.10.: Plinthe, Saeulenschaft mit Kanneluren und Lichtkante,
    Kapitell, Namensplakette, Bueste eines baertigen Hausherrn mit Lorbeerkranz; ein Auge fehlt (dunkle Hoehle),
    Riss durch die Wange, Staub."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    m, m_l, m_d = hexc("#b4b8c0"), hexc("#d0d4dc"), hexc("#80848c")
    p.cyl(cx, cy, r, 0, 0.1, m_l, m, ry=r * 0.5)
    p.cyl(cx, cy, r * 0.82, 0.1, 0.08, m_l, m_d, ry=r * 0.42)
    sh = 1.0
    p.cyl(cx, cy, r * 0.62, 0.18, sh, m_l, m, ry=r * 0.32)
    fb, ft = cy + 0.18 * K, cy + (0.18 + sh) * K
    for k in range(4):                                                                                      # Kanneluren
        kx = cx - r * 0.45 + k * r * 0.3
        c.line([(kx, fb + 0.04), (kx, ft - 0.03)], fill=alpha(m_d, 190), width=0.012)
    c.line([(cx - r * 0.55, fb + 0.04), (cx - r * 0.55, ft - 0.03)], fill=alpha((255, 255, 255, 255), 140), width=0.016)
    p.cyl(cx, cy, r * 0.82, 1.18, 0.08, m_l, m_d, ry=r * 0.42)                                              # Kapitell
    p.cyl(cx, cy, r * 0.95, 1.26, 0.06, m_l, m, ry=r * 0.48)
    c.rect(cx - 0.1, fb + 0.3, cx + 0.1, fb + 0.4, fill=BRASS, outline=OUTLINE, width=0.012)                   # Plakette
    c.text(cx, fb + 0.35, "LORD H.", 0.04, hexc("#2a2422"))
    zt = cy + 1.32 * K
    # Bueste: Sockelchen, Schultern mit Gewandfalten, Hals, Kopf, Bart, Lorbeer
    c.rect(cx - 0.1, zt, cx + 0.1, zt + 0.08, fill=m_d, outline=OUTLINE, width=0.015)
    c.poly([(cx - 0.24, zt + 0.08), (cx + 0.24, zt + 0.08), (cx + 0.2, zt + 0.3), (cx + 0.08, zt + 0.36), (cx - 0.08, zt + 0.36), (cx - 0.2, zt + 0.3)],
           fill=m_l, outline=OUTLINE, width=0.02)
    for k in range(3):
        c.line([(cx - 0.16 + k * 0.08, zt + 0.1), (cx - 0.12 + k * 0.06, zt + 0.3)], fill=alpha(m_d, 170), width=0.012)
    c.rect(cx - 0.055, zt + 0.34, cx + 0.055, zt + 0.44, fill=m, outline=OUTLINE, width=0.015)               # Hals
    c.ellipse(cx, zt + 0.56, 0.115, 0.14, fill=m_l, outline=OUTLINE, width=0.02)                            # Kopf
    c.poly([(cx - 0.11, zt + 0.5), (cx + 0.11, zt + 0.5), (cx + 0.09, zt + 0.36), (cx, zt + 0.3), (cx - 0.09, zt + 0.36)], fill=m, outline=OUTLINE, width=0.015)   # Bart
    for k in range(4):
        c.line([(cx - 0.06 + k * 0.04, zt + 0.48), (cx - 0.05 + k * 0.035, zt + 0.36)], fill=alpha(m_d, 170), width=0.01)
    c.line([(cx - 0.03, zt + 0.52), (cx + 0.03, zt + 0.52)], fill=alpha(m_d, 200), width=0.012)             # Mund
    c.line([(cx, zt + 0.58), (cx - 0.015, zt + 0.54), (cx + 0.015, zt + 0.54)], fill=alpha(m_d, 170), width=0.01)   # Nase
    c.ellipse(cx - 0.045, zt + 0.6, 0.02, 0.016, fill=m, outline=OUTLINE, width=0.01)                      # Auge links
    c.ellipse(cx - 0.045, zt + 0.6, 0.008, 0.008, fill=m_d)
    c.ellipse(cx + 0.045, zt + 0.6, 0.024, 0.022, fill=hexc("#1a1c22"), outline=OUTLINE, width=0.01)       # fehlendes Auge
    c.line([(cx - 0.06, zt + 0.64), (cx - 0.025, zt + 0.645)], fill=alpha(m_d, 200), width=0.01)
    c.line([(cx + 0.025, zt + 0.645), (cx + 0.065, zt + 0.64)], fill=alpha(m_d, 200), width=0.01)
    crack(c, [(cx + 0.09, zt + 0.46), (cx + 0.06, zt + 0.56), (cx + 0.1, zt + 0.66)], seed=idx)
    for k in range(7):                                                                                      # Lorbeerkranz
        a = math.pi * (0.1 + k * 0.133)
        lx, ly = cx + 0.12 * math.cos(a), zt + 0.62 + 0.1 * math.sin(a)
        c.poly([(lx - 0.03, ly), (lx, ly + 0.02), (lx + 0.03, ly), (lx, ly - 0.02)], fill=m_l if k % 2 else m, outline=OUTLINE, width=0.008)
    c.ellipse(cx - 0.04, zt + 0.66, 0.012, 0.008, fill=(255, 255, 255, 160))
    dust(c, cx - 0.2, zt + 0.1, cx + 0.2, zt + 0.3, 4, seed=idx)


def _ruestung(p, c, x0, y0, x1, y1, idx, rnd):
    """Ritterruestung, neu 24.10.: Holzsockel mit Messingrand, Eisenschuhe, Beinschienen mit Knieschalen,
    Bauchreifen, Brustplatte mit Mittelgrat und Nieten, Schulterstuecke, Panzerhandschuhe, Topfhelm mit offenem
    Visier (rote Augen dahinter), Federbusch, Hellebarde links, Wappenschild rechts."""
    cx = (x0 + x1) / 2
    p.box(x0, y0, x1, y1, 0, 0.15, hexc("#8c9098"), hexc("#7c8088"))
    c.rect(x0 + 0.03, y0 + 0.02, x1 - 0.03, y0 + 0.15 * K - 0.02, outline=BRASS_D, width=0.01)
    base = y0 + 0.15 * K
    col, col_l, col_d = hexc("#a2a8b4"), hexc("#d0d6de"), hexc("#6a7080")

    def plate(pts, w=0.02, fill=None):
        c.poly(pts, fill=fill or col, outline=OUTLINE, width=w)

    for s in (-1, 1):                                                                                       # Fuesse und Beine
        lx = cx + s * 0.11
        plate([(lx - 0.09, base), (lx + 0.09 + s * 0.04, base), (lx + 0.07 + s * 0.04, base + 0.08), (lx - 0.07, base + 0.08)])
        plate([(lx - 0.07, base + 0.08), (lx + 0.07, base + 0.08), (lx + 0.075, base + 0.42), (lx - 0.075, base + 0.42)])
        c.line([(lx - 0.03, base + 0.1), (lx - 0.03, base + 0.4)], fill=col_l, width=0.012)
        c.ellipse(lx, base + 0.45, 0.075, 0.055, fill=col_l, outline=OUTLINE, width=0.015)                    # Knieschale
        plate([(lx - 0.075, base + 0.48), (lx + 0.075, base + 0.48), (lx + 0.08, base + 0.7), (lx - 0.08, base + 0.7)])
    for k in range(3):                                                                                      # Bauchreifen
        yy = base + 0.68 + k * 0.07
        plate([(cx - 0.22 + k * 0.01, yy), (cx + 0.22 - k * 0.01, yy), (cx + 0.22 - k * 0.01, yy + 0.07), (cx - 0.22 + k * 0.01, yy + 0.07)])
    plate([(cx - 0.24, base + 0.88), (cx + 0.24, base + 0.88), (cx + 0.28, base + 1.18), (cx + 0.2, base + 1.32), (cx - 0.2, base + 1.32), (cx - 0.28, base + 1.18)], w=0.025)   # Brust
    c.line([(cx, base + 0.9), (cx, base + 1.3)], fill=col_l, width=0.02)
    c.line([(cx - 0.2, base + 0.95), (cx - 0.08, base + 1.25)], fill=alpha(col_d, 160), width=0.012)
    for sx, sy in ((-0.2, 1.26), (0.2, 1.26), (-0.22, 1.0), (0.22, 1.0)):
        c.ellipse(cx + sx, base + sy, 0.012, 0.012, fill=col_d, outline=OUTLINE, width=0.006)
    for s in (-1, 1):                                                                                       # Schultern und Arme
        plate([(cx + s * 0.18, base + 1.34), (cx + s * 0.42, base + 1.3), (cx + s * 0.4, base + 1.14), (cx + s * 0.22, base + 1.18)], w=0.02, fill=col_l)
        plate([(cx + s * 0.3, base + 1.16), (cx + s * 0.42, base + 1.14), (cx + s * 0.44, base + 0.7), (cx + s * 0.32, base + 0.7)])
        c.ellipse(cx + s * 0.37, base + 0.92, 0.065, 0.05, fill=col_l, outline=OUTLINE, width=0.012)          # Ellbogen
        plate([(cx + s * 0.31, base + 0.72), (cx + s * 0.45, base + 0.72), (cx + s * 0.46, base + 0.56), (cx + s * 0.3, base + 0.56)], fill=col_d)   # Handschuh
        for k in range(3):
            c.line([(cx + s * (0.33 + k * 0.04), base + 0.58), (cx + s * (0.33 + k * 0.04), base + 0.7)], fill=OUTLINE, width=0.008)
    # Helm
    hy = base + 1.5
    plate([(cx - 0.15, base + 1.32), (cx + 0.15, base + 1.32), (cx + 0.16, hy + 0.1), (cx + 0.1, hy + 0.2), (cx - 0.1, hy + 0.2), (cx - 0.16, hy + 0.1)], w=0.025)
    c.rect(cx - 0.12, hy - 0.08, cx + 0.12, hy + 0.04, fill=hexc("#0b0d10"), outline=OUTLINE, width=0.012)   # offenes Visier
    for s in (-1, 1):
        c.ellipse(cx + s * 0.05, hy - 0.02, 0.014, 0.012, fill=RED)
        c.glow(cx + s * 0.05, hy - 0.02, 0.05, RED, 0.5)
    plate([(cx - 0.13, hy + 0.04), (cx + 0.13, hy + 0.04), (cx + 0.1, hy + 0.12), (cx - 0.1, hy + 0.12)], fill=col_l)    # Visier hochgeklappt
    for k in range(4):
        c.line([(cx - 0.08 + k * 0.05, hy + 0.05), (cx - 0.08 + k * 0.05, hy + 0.11)], fill=OUTLINE, width=0.008)
    c.line([(cx - 0.1, hy + 0.2), (cx, hy + 0.24), (cx + 0.1, hy + 0.2)], fill=col_l, width=0.02)
    for k, (dx, dy) in enumerate(((0.0, 0.3), (-0.07, 0.36), (0.07, 0.36), (-0.12, 0.3), (0.12, 0.3))):      # Federbusch
        c.poly([(cx + dx - 0.03, hy + 0.22), (cx + dx + 0.03, hy + 0.22), (cx + dx * 1.3 + 0.01, hy + dy + 0.12), (cx + dx * 1.3 - 0.02, hy + dy + 0.1)],
               fill=hexc("#a02a34") if k % 2 == 0 else hexc("#c8c0b0"), outline=OUTLINE, width=0.01)
    # Hellebarde links, Wappenschild rechts
    px_ = cx - 0.42
    c.line([(px_, base), (px_ + 0.03, base + 1.9)], fill=OUTLINE, width=0.04)
    c.line([(px_, base), (px_ + 0.03, base + 1.9)], fill=WALNUT, width=0.022)
    plate([(px_ + 0.03, base + 1.9), (px_ + 0.03, base + 2.05), (px_ - 0.02, base + 1.95), (px_ - 0.02, base + 1.78)], fill=STEEL)
    plate([(px_ + 0.03, base + 1.86), (px_ + 0.17, base + 1.8), (px_ + 0.14, base + 1.62), (px_ + 0.03, base + 1.66)], fill=STEEL)
    c.line([(px_ + 0.03, base + 1.72), (px_ - 0.08, base + 1.7)], fill=STEEL, width=0.025)
    sx_ = cx + 0.46
    c.poly([(sx_ - 0.13, base + 1.1), (sx_ + 0.13, base + 1.1), (sx_ + 0.13, base + 0.8), (sx_, base + 0.62), (sx_ - 0.13, base + 0.8)],
           fill=hexc("#8a1a22"), outline=OUTLINE, width=0.02)
    c.line([(sx_, base + 0.66), (sx_, base + 1.08)], fill=BRASS, width=0.02)
    c.line([(sx_ - 0.11, base + 0.92), (sx_ + 0.11, base + 0.92)], fill=BRASS, width=0.02)
    c.ellipse(sx_ - 0.06, base + 1.0, 0.03, 0.03, fill=BRASS, outline=OUTLINE, width=0.008)
    cobweb(c, cx + 0.42, base + 1.3, 0.12, 1, 1, seed=idx)


def _standspiegel(p, c, x0, y0, x1, y1, idx, rnd):
    """Standspiegel, gesprungen; im Spiegel ein Schemen, der nicht im Raum steht."""
    cx = (x0 + x1) / 2
    for sx in (x0 + 0.05, x1 - 0.05):
        c.line([(sx, y0 + 0.02), (sx, y0 + 0.4)], fill=OUTLINE, width=0.035)
        c.line([(sx, y0 + 0.02), (sx, y0 + 0.4)], fill=WALNUT, width=0.02)
    top = y1 + 1.8 * K
    c.ellipse(cx, (y0 + 0.3 + top) / 2, (x1 - x0) / 2 + 0.05, (top - y0 - 0.3) / 2, fill=WALNUT_D, outline=OUTLINE, width=0.02)
    c.ellipse(cx, (y0 + 0.3 + top) / 2, (x1 - x0) / 2 - 0.02, (top - y0 - 0.3) / 2 - 0.07, fill=hexc("#9ab0c0"), outline=OUTLINE, width=0.012)
    c.ellipse(cx + 0.02, (y0 + 0.3 + top) / 2 - 0.1, 0.08, 0.2, fill=alpha(hexc("#50606c"), 120))
    c.ellipse(cx + 0.02, (y0 + 0.3 + top) / 2 + 0.12, 0.05, 0.06, fill=alpha(hexc("#50606c"), 140))
    crack(c, [(cx - 0.15, top - 0.2), (cx - 0.02, (y0 + 0.3 + top) / 2 + 0.05), (cx + 0.12, y0 + 0.5)], seed=idx)
    crack(c, [(cx - 0.02, (y0 + 0.3 + top) / 2 + 0.05), (cx + 0.18, (y0 + 0.3 + top) / 2 + 0.2)], seed=idx + 1)
    c.line([(cx - 0.12, top - 0.3), (cx - 0.05, top - 0.12)], fill=alpha(hexc("#ffffff"), 80), width=0.02)


def _geweihe(p, c, x0, y0, x1, y1, idx, rnd):
    """Geweihe an der Nordwand auf Holzschilden."""
    n = 3
    for k in range(n):
        gx = x0 + (x1 - x0) * (k + 0.5) / n
        gy = y0 + 1.5 * K
        c.poly([(gx - 0.12, gy - 0.1), (gx + 0.12, gy - 0.1), (gx + 0.1, gy + 0.14), (gx, gy + 0.2), (gx - 0.1, gy + 0.14)], fill=WALNUT, outline=OUTLINE, width=0.012)
        for s in (-1, 1):
            pts = [(gx, gy + 0.1), (gx + s * 0.08, gy + 0.22), (gx + s * 0.18, gy + 0.4), (gx + s * 0.15, gy + 0.5)]
            c.line(pts, fill=OUTLINE, width=0.035)
            c.line(pts, fill=hexc("#d8ccb0"), width=0.02)
            c.line([(gx + s * 0.08, gy + 0.22), (gx + s * 0.2, gy + 0.26)], fill=OUTLINE, width=0.03)
            c.line([(gx + s * 0.08, gy + 0.22), (gx + s * 0.2, gy + 0.26)], fill=hexc("#d8ccb0"), width=0.016)
        if k == 1:
            c.ellipse(gx, gy + 0.05, 0.05, 0.04, fill=PALE, outline=OUTLINE, width=0.01)     # Schaedel
            c.ellipse(gx - 0.02, gy + 0.05, 0.01, 0.012, fill=OUTLINE)
            c.ellipse(gx + 0.02, gy + 0.05, 0.01, 0.012, fill=OUTLINE)


def _hirschkopf(p, c, x0, y0, x1, y1, idx, rnd):
    """Praeparierter Hirschkopf an der Ostwand, Glasaugen leuchten."""
    cx = (x0 + x1) / 2
    gy = y0 + 1.4 * K
    c.poly([(cx - 0.2, gy), (cx + 0.2, gy), (cx + 0.18, gy + 0.5), (cx, gy + 0.6), (cx - 0.18, gy + 0.5)], fill=WALNUT, outline=OUTLINE, width=0.015)
    c.poly([(cx - 0.08, gy + 0.08), (cx + 0.08, gy + 0.08), (cx + 0.13, gy + 0.32), (cx - 0.13, gy + 0.32)], fill=hexc("#8a6a4a"), outline=OUTLINE, width=0.015)
    c.ellipse(cx, gy + 0.36, 0.14, 0.11, fill=hexc("#9a7a5a"), outline=OUTLINE, width=0.015)
    c.ellipse(cx, gy + 0.1, 0.05, 0.03, fill=hexc("#2a2420"))
    for s in (-1, 1):
        c.ellipse(cx + s * 0.07, gy + 0.38, 0.02, 0.02, fill=hexc("#e8e050"), outline=OUTLINE, width=0.008)
        c.glow(cx + s * 0.07, gy + 0.38, 0.05, hexc("#e8e050"), 0.6)
        pts = [(cx + s * 0.08, gy + 0.45), (cx + s * 0.16, gy + 0.62), (cx + s * 0.3, gy + 0.78), (cx + s * 0.26, gy + 0.9)]
        c.line(pts, fill=OUTLINE, width=0.035)
        c.line(pts, fill=hexc("#d8ccb0"), width=0.02)
        c.line([(cx + s * 0.16, gy + 0.62), (cx + s * 0.32, gy + 0.6)], fill=OUTLINE, width=0.03)
        c.line([(cx + s * 0.16, gy + 0.62), (cx + s * 0.32, gy + 0.6)], fill=hexc("#d8ccb0"), width=0.016)


def _fledermaeuse(p, c, x0, y0, x1, y1, idx, rnd):
    """Fledermaeuse unter der Decke: drei haengend, eine fliegt."""
    top = y0 + 2.3 * K
    for k in range(3):
        bx = x0 + 0.25 + k * (x1 - x0 - 0.5) / 2
        c.line([(bx, top + 0.02), (bx, top - 0.06)], fill=OUTLINE, width=0.012)
        c.poly([(bx - 0.05, top - 0.06), (bx + 0.05, top - 0.06), (bx + 0.03, top - 0.22), (bx - 0.03, top - 0.22)], fill=hexc("#101014"), outline=OUTLINE, width=0.01)
        c.ellipse(bx, top - 0.25, 0.035, 0.03, fill=hexc("#101014"))
        c.ellipse(bx - 0.012, top - 0.25, 0.006, 0.006, fill=RED)
        c.ellipse(bx + 0.012, top - 0.25, 0.006, 0.006, fill=RED)
    fx, fy = x1 - 0.2, top - 0.5
    c.poly([(fx, fy), (fx - 0.12, fy + 0.07), (fx - 0.16, fy - 0.03), (fx - 0.06, fy - 0.05), (fx, fy - 0.1),
            (fx + 0.06, fy - 0.05), (fx + 0.16, fy - 0.03), (fx + 0.12, fy + 0.07)], fill=hexc("#101014"))


# ------------------------------------------------------------------ Jagdzimmer, Kaminzimmer, Arbeitszimmer

def _billardtisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Billardtisch: Nussholzrahmen, gruenes Tuch, Kugeln, zwei Queues, eine Kugel rollt von selbst."""
    p.box(x0, y0, x1, y1, 0, 0.8, WALNUT_L, WALNUT)
    zt = y0 + 0.8 * K
    c.poly([(x0 + 0.08, zt + 0.05), (x1 - 0.08, zt + 0.05), (x1 - 0.08, y1 + 0.8 * K - 0.05), (x0 + 0.08, y1 + 0.8 * K - 0.05)], fill=hexc("#2f6b3f"), outline=shade(hexc("#2f6b3f"), 0.6), width=0.012)
    for px, py in ((x0 + 0.1, zt + 0.07), (x1 - 0.1, zt + 0.07), (x0 + 0.1, y1 + 0.8 * K - 0.07), (x1 - 0.1, y1 + 0.8 * K - 0.07), ((x0 + x1) / 2, zt + 0.06), ((x0 + x1) / 2, y1 + 0.8 * K - 0.06)):
        c.ellipse(px, py, 0.035, 0.025, fill=hexc("#0b0d10"))
    cols = (RED, hexc("#e8d040"), hexc("#3a6ac8"), hexc("#e8e8e8"), hexc("#8a3aa8"), MATTE_D)
    for k in range(6):
        bx, by = x0 + 0.5 + rnd.uniform(0, x1 - x0 - 1.0), zt + 0.12 + rnd.uniform(0, y1 - y0 - 0.25)
        c.ellipse(bx, by, 0.035, 0.03, fill=cols[k], outline=OUTLINE, width=0.008)
    c.line([(x0 + 0.3, zt + 0.1), (x1 - 0.5, zt + 0.3)], fill=OUTLINE, width=0.03)
    c.line([(x0 + 0.3, zt + 0.1), (x1 - 0.5, zt + 0.3)], fill=WOOD_LIGHT, width=0.016)
    c.line([(x1 - 0.3, zt + 0.12), (x1 - 0.1, zt + 0.5)], fill=OUTLINE, width=0.03)
    c.line([(x1 - 0.3, zt + 0.12), (x1 - 0.1, zt + 0.5)], fill=WOOD_LIGHT, width=0.016)
    for px in (x0 + 0.12, x1 - 0.12):
        c.rect(px - 0.06, y0 + 0.02, px + 0.06, y0 + 0.8 * K, fill=WALNUT_D, outline=OUTLINE, width=0.012)


def _globusbar(p, c, x0, y0, x1, y1, idx, rnd):
    """Globusbar, aufgeklappt, mit Flaschen und Glaesern darin."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    for a in (0.5, 2.6, 4.7):
        c.line([(cx, cy + 0.3 * K), (cx + r * math.cos(a), cy + r * 0.55 * math.sin(a))], fill=OUTLINE, width=0.035)
        c.line([(cx, cy + 0.3 * K), (cx + r * math.cos(a), cy + r * 0.55 * math.sin(a))], fill=WALNUT, width=0.02)
    gz = cy + 0.75 * K
    c.ellipse(cx, gz, r, r * 0.5, fill=hexc("#c8b888"), outline=OUTLINE, width=0.02)       # untere Halbkugel
    c.rect(cx - r, gz - r * 0.5, cx + r, gz, fill=hexc("#c8b888"))
    c.ellipse(cx, gz - r * 0.5, r, r * 0.4, fill=hexc("#b8a878"), outline=OUTLINE, width=0.02)
    c.ellipse(cx, gz, r * 0.85, r * 0.42, fill=hexc("#3a2418"))
    bottle(c, cx - 0.1, gz - 0.02, 0.26, hexc("#6a3a1a"), CREAM, 0.03)
    bottle(c, cx + 0.06, gz, 0.2, hexc("#3a4a2a"), None, 0.025)
    c.rect(cx + 0.15, gz, cx + 0.21, gz + 0.09, fill=GLASS_C, outline=OUTLINE, width=0.008)
    c.ellipse(cx + 0.02, gz + 0.32 + r * 0.5, r * 0.9, r * 0.35, fill=hexc("#c8b888"), outline=OUTLINE, width=0.02)   # offener Deckel hinten
    for (ox, oy, rx, ry) in ((-0.08, 0.0, 0.07, 0.05), (0.08, 0.02, 0.05, 0.06)):
        c.ellipse(cx + 0.02 + ox, gz + 0.32 + r * 0.5 + oy, rx, ry, fill=hexc("#8a7a4a"))


def _beistelltisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Beistelltisch mit Karaffe und zwei Glaesern, eines umgekippt."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    p.cyl(cx, cy, 0.04, 0, 0.6, WALNUT_L, WALNUT, ry=0.02)
    p.cyl(cx, cy, r, 0.6, 0.04, WALNUT_L, WALNUT, ry=r * 0.55)
    zt = cy + 0.64 * K
    c.poly([(cx - 0.06, zt), (cx + 0.06, zt), (cx + 0.05, zt + 0.14), (cx + 0.02, zt + 0.2), (cx - 0.02, zt + 0.2), (cx - 0.05, zt + 0.14)], fill=alpha(hexc("#c08a3a"), 200), outline=OUTLINE, width=0.01)
    c.ellipse(cx, zt + 0.21, 0.025, 0.012, fill=GLASS_C, outline=OUTLINE, width=0.008)
    c.rect(cx + 0.1, zt, cx + 0.16, zt + 0.08, fill=GLASS_C, outline=OUTLINE, width=0.008)
    c.rect(cx + 0.1, zt + 0.01, cx + 0.16, zt + 0.04, fill=alpha(hexc("#c08a3a"), 200))
    c.poly([(cx - 0.2, zt + 0.02), (cx - 0.12, zt + 0.0), (cx - 0.11, zt + 0.05), (cx - 0.19, zt + 0.07)], fill=GLASS_C, outline=OUTLINE, width=0.008)
    c.ellipse(cx - 0.24, zt + 0.0, 0.04, 0.015, fill=alpha(hexc("#c08a3a"), 160))


def _schuerhaken(p, c, x0, y0, x1, y1, idx, rnd):
    """Kaminbesteck im Staender: Schuerhaken, Schaufel, Besen."""
    cx = (x0 + x1) / 2
    c.ellipse(cx, y0 + 0.08, 0.14, 0.06, fill=IRON, outline=OUTLINE, width=0.015)
    c.rect(cx - 0.015, y0 + 0.08, cx + 0.015, y0 + 0.8, fill=IRON, outline=OUTLINE, width=0.01)
    c.ellipse(cx, y0 + 0.8, 0.09, 0.03, fill=IRON_L, outline=OUTLINE, width=0.012)
    for k, dx in enumerate((-0.07, 0.0, 0.07)):
        c.line([(cx + dx, y0 + 0.15), (cx + dx * 1.3, y0 + 0.78)], fill=OUTLINE, width=0.025)
        c.line([(cx + dx, y0 + 0.15), (cx + dx * 1.3, y0 + 0.78)], fill=IRON_L, width=0.012)
        c.ellipse(cx + dx * 1.3, y0 + 0.78, 0.015, 0.015, fill=BRASS, outline=OUTLINE, width=0.006)
    c.line([(cx - 0.07, y0 + 0.15), (cx - 0.12, y0 + 0.1)], fill=IRON_L, width=0.014)
    c.poly([(cx - 0.02, y0 + 0.1), (cx + 0.03, y0 + 0.1), (cx + 0.03, y0 + 0.18), (cx - 0.02, y0 + 0.18)], fill=IRON_L, outline=OUTLINE, width=0.008)
    for j in range(4):
        c.line([(cx + 0.07 + j * 0.01, y0 + 0.15), (cx + 0.06 + j * 0.015, y0 + 0.05)], fill=hexc("#c8a860"), width=0.008)


def _holzkorb(p, c, x0, y0, x1, y1, idx, rnd):
    """Weidenkorb mit Holzscheiten, ein Scheit mit Gesicht in der Maserung."""
    p.box(x0, y0, x1, y1, 0, 0.45, shade(WOOD_LIGHT, 1.05), hexc("#9a7a4a"))
    fz = y0
    for k in range(5):
        c.line([(x0 + 0.03, fz + 0.04 + k * 0.045), (x1 - 0.03, fz + 0.04 + k * 0.045)], fill=shade(hexc("#9a7a4a"), 0.75), width=0.01)
    for j in range(6):
        c.line([(x0 + 0.08 + j * 0.12, fz + 0.03), (x0 + 0.1 + j * 0.12, fz + 0.45 * K - 0.02)], fill=shade(hexc("#9a7a4a"), 0.8), width=0.008)
    zt = y0 + 0.45 * K
    for k in range(4):
        lx = x0 + 0.1 + k * 0.17
        c.ellipse(lx, zt + 0.08 + (k % 2) * 0.04, 0.07, 0.05, fill=hexc("#8a5a34"), outline=OUTLINE, width=0.012)
        c.ellipse(lx, zt + 0.08 + (k % 2) * 0.04, 0.04, 0.028, fill=hexc("#c8a060"))
        c.ellipse(lx, zt + 0.08 + (k % 2) * 0.04, 0.015, 0.01, outline=hexc("#8a5a34"), width=0.006)
    c.ellipse(x0 + 0.27, zt + 0.1, 0.008, 0.008, fill=OUTLINE)
    c.ellipse(x0 + 0.3, zt + 0.1, 0.008, 0.008, fill=OUTLINE)


def _schaukelstuhl(p, c, x0, y0, x1, y1, idx, rnd):
    """Schaukelstuhl mit Decke, Kufen, leicht nach vorn gekippt."""
    cx = (x0 + x1) / 2
    for sx in (x0 + 0.1, x1 - 0.1):
        c.line([(sx - 0.1, y0 + 0.04), (sx, y0 + 0.0), (sx + 0.15, y0 + 0.03), (sx + 0.25, y0 + 0.1)], fill=OUTLINE, width=0.035)
        c.line([(sx - 0.1, y0 + 0.04), (sx, y0 + 0.0), (sx + 0.15, y0 + 0.03), (sx + 0.25, y0 + 0.1)], fill=WALNUT, width=0.02)
    chair_simple(p, c, cx, (y0 + y1) / 2, x1 - x0 - 0.2, y1 - y0 - 0.3, 0.08, WALNUT, back=False)
    top = y1 + 0.5 * K
    for k in range(5):
        bx = x0 + 0.15 + k * (x1 - x0 - 0.3) / 4
        c.line([(bx, top), (bx + 0.03, top + 0.6)], fill=OUTLINE, width=0.03)
        c.line([(bx, top), (bx + 0.03, top + 0.6)], fill=WALNUT_L, width=0.016)
    c.rect(x0 + 0.1, top + 0.55, x1 - 0.07, top + 0.62, fill=WALNUT, outline=OUTLINE, width=0.012)
    c.poly([(x0 + 0.12, top + 0.05), (x1 - 0.12, top + 0.05), (x1 - 0.05, top + 0.45), (x0 + 0.2, top + 0.5)], fill=hexc("#8a6a5a"), outline=OUTLINE, width=0.015)
    c.line([(x0 + 0.3, top + 0.1), (x0 + 0.35, top + 0.45)], fill=alpha(hexc("#5a4a3a"), 150), width=0.012)


def _kinderschuh(p, c, x0, y0, x1, y1, idx, rnd):
    """Kleiner Kinderschuh vor dem Kamin, verrusst."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c.poly([(cx - 0.12, cy - 0.04), (cx + 0.1, cy - 0.05), (cx + 0.14, cy + 0.02), (cx + 0.06, cy + 0.08), (cx - 0.1, cy + 0.06)], fill=hexc("#5a3a2a"), outline=OUTLINE, width=0.012)
    c.line([(cx - 0.02, cy + 0.0), (cx + 0.04, cy + 0.05)], fill=CREAM, width=0.008)
    c.ellipse(cx + 0.02, cy - 0.02, 0.03, 0.015, fill=alpha((20, 18, 18, 255), 140))


def _safe(p, c, x0, y0, x1, y1, idx, rnd):
    """Tresor an der Westwand, Tuer offen, leer, Zahlenschloss."""
    p.box(x0, y0, x1, y1, 0, 1.1, IRON_L, IRON)
    fz = y0
    c.rect(x0 + 0.03, fz + 0.05, x1 - 0.03, fz + 1.1 * K - 0.05, fill=hexc("#0b0d10"), outline=OUTLINE, width=0.012)
    c.rect(x0 + 0.06, fz + 0.3, x1 - 0.06, fz + 0.34, fill=IRON_D)
    c.poly([(x1 - 0.03, fz + 0.05), (x1 + 0.3, fz + 0.12), (x1 + 0.3, fz + 1.1 * K + 0.02), (x1 - 0.03, fz + 1.1 * K - 0.05)], fill=IRON_L, outline=OUTLINE, width=0.015)
    c.ellipse(x1 + 0.14, fz + 0.3, 0.05, 0.05, fill=STEEL, outline=OUTLINE, width=0.012)
    for k in range(8):
        a = math.pi * 2 * k / 8
        c.line([(x1 + 0.14 + 0.03 * math.cos(a), fz + 0.3 + 0.03 * math.sin(a)), (x1 + 0.14 + 0.045 * math.cos(a), fz + 0.3 + 0.045 * math.sin(a))], fill=OUTLINE, width=0.006)
    c.line([(x1 + 0.08, fz + 0.45), (x1 + 0.2, fz + 0.45)], fill=STEEL, width=0.02)
    c.poly([(x0 + 0.08, fz + 0.08), (x0 + 0.2, fz + 0.08), (x0 + 0.19, fz + 0.16), (x0 + 0.07, fz + 0.16)], fill=CREAM, outline=OUTLINE, width=0.006)   # ein Zettel


def _aktenkisten(p, c, x0, y0, x1, y1, idx, rnd):
    """Aktenkisten gestapelt, beschriftet, eine offen mit Papieren."""
    col = hexc("#b8a070")
    p.box(x0, y0, x1 - 0.4, y1, 0, 0.35, shade(col, 1.1), col)
    p.box(x0 + 0.03, y0 + 0.02, x1 - 0.45, y1 - 0.05, 0.35, 0.35, shade(col, 1.15), shade(col, 0.95))
    p.box(x0 + 0.06, y0 + 0.04, x1 - 0.5, y1 - 0.1, 0.7, 0.3, shade(col, 1.2), shade(col, 0.9))
    for k, label in enumerate(("1931", "1954", "SCRIPT")):
        c.text((x0 + x1 - 0.42) / 2, y0 + 0.17 * K + k * 0.35 * K + 0.02 * k, label, 0.04, hexc("#3a2a1a"))
    p.box(x1 - 0.35, y0 + 0.1, x1, y1 - 0.2, 0, 0.3, shade(col, 1.1), col)
    zt = y1 - 0.2 + 0.3 * K
    for k in range(4):
        c.poly([(x1 - 0.32 + k * 0.03, zt + 0.02 + k * 0.02), (x1 - 0.05 + k * 0.03, zt + 0.0 + k * 0.02), (x1 - 0.06 + k * 0.03, zt + 0.18 + k * 0.02), (x1 - 0.33 + k * 0.03, zt + 0.2 + k * 0.02)], fill=CREAM, outline=OUTLINE, width=0.008)
    c.poly([(x1 - 0.1, y0 - 0.02), (x1 + 0.15, y0 - 0.06), (x1 + 0.16, y0 + 0.08), (x1 - 0.09, y0 + 0.12)], fill=CREAM, outline=OUTLINE, width=0.008)


def _pinnwand(p, c, x0, y0, x1, y1, idx, rnd):
    """Pinnwand an der Nordwand: Call Sheets, Fotos, Faden zwischen Nadeln, ein Foto mit ausgeschnittenem Kopf."""
    fy0, fy1 = wall_board(p, c, x0, y0, x1, y1, 0.9, 1.1, hexc("#8a6a44"))
    c.rect(x0 + 0.04, fy0 + 0.04, x1 - 0.04, fy1 - 0.04, fill=hexc("#b89a6a"))
    pins = []
    for k in range(7):
        px, py = rnd.uniform(x0 + 0.2, x1 - 0.2), rnd.uniform(fy0 + 0.15, fy1 - 0.15)
        w, h = rnd.uniform(0.18, 0.3), rnd.uniform(0.18, 0.28)
        col = CREAM if k % 3 else hexc("#d8d0c8")
        c.poly([(px - w / 2, py - h / 2), (px + w / 2, py - h / 2 + 0.01), (px + w / 2 - 0.01, py + h / 2), (px - w / 2, py + h / 2 - 0.01)], fill=col, outline=OUTLINE, width=0.008)
        if k % 3 == 0:                                                                        # Foto
            c.rect(px - w / 2 + 0.02, py - h / 2 + 0.02, px + w / 2 - 0.02, py + h / 2 - 0.05, fill=hexc("#6a7a6a"))
            c.ellipse(px, py, 0.03, 0.04, fill=PALE)
            if k == 3:
                c.rect(px - 0.035, py - 0.05, px + 0.035, py + 0.05, fill=hexc("#b89a6a"))   # Kopf ausgeschnitten
        else:
            for j in range(3):
                c.line([(px - w / 2 + 0.03, py + h / 2 - 0.05 - j * 0.05), (px + w / 2 - 0.03, py + h / 2 - 0.05 - j * 0.05)], fill=alpha(OUTLINE, 110), width=0.005)
        pin = (px, py + h / 2 - 0.02)
        c.ellipse(pin[0], pin[1], 0.012, 0.012, fill=RED if k % 2 else hexc("#3a6ac8"), outline=OUTLINE, width=0.006)
        pins.append(pin)
    for a, b in zip(pins, pins[1:]):
        c.line([a, b], fill=alpha(RED, 160), width=0.006)
    c.text((x0 + x1) / 2, fy1 - 0.08, "PRODUCTION", 0.035, hexc("#3a2a1a"))


def _lueftungsgitter(p, c, x0, y0, x1, y1, idx, rnd):
    """Lueftungsgitter an der Ostwand, ein Lamellenstab verbogen, dahinter dunkel."""
    cx = (x0 + x1) / 2
    gy0, gy1 = y0 + 0.9 * K, y0 + 0.9 * K + 0.5
    c.rect(cx - 0.3, gy0, cx + 0.3, gy1, fill=IRON, outline=OUTLINE, width=0.015)
    c.rect(cx - 0.26, gy0 + 0.04, cx + 0.26, gy1 - 0.04, fill=hexc("#0b0d10"))
    for k in range(6):
        ly = gy0 + 0.07 + k * 0.065
        if k == 3:
            c.line([(cx - 0.24, ly), (cx - 0.05, ly + 0.04), (cx + 0.24, ly - 0.01)], fill=IRON_L, width=0.02)
        else:
            c.line([(cx - 0.24, ly), (cx + 0.24, ly)], fill=IRON_L, width=0.02)
    for sx, sy in ((cx - 0.27, gy0 + 0.03), (cx + 0.27, gy0 + 0.03), (cx - 0.27, gy1 - 0.03), (cx + 0.27, gy1 - 0.03)):
        c.ellipse(sx, sy, 0.01, 0.01, fill=STEEL, outline=OUTLINE, width=0.005)
    smoke(c, cx + 0.1, gy1 + 0.02, seed=idx, h=0.25)


def _schreibmaschine(p, c, x0, y0, x1, y1, idx, rnd):
    """Schreibmaschine (steht auf dem Schreibtisch, Hoehe mitgezeichnet) mit endloser Seite LEAVE LEAVE LEAVE."""
    z = 0.78
    cx = (x0 + x1) / 2
    base = y0 + z * K
    c.poly([(x0, base), (x1, base), (x1 - 0.03, base + 0.16), (x0 + 0.03, base + 0.16)], fill=MATTE, outline=OUTLINE, width=0.015)
    for k in range(3):
        for j in range(8):
            c.ellipse(x0 + 0.08 + j * (x1 - x0 - 0.16) / 7 + (k % 2) * 0.02, base + 0.04 + k * 0.035, 0.012, 0.01, fill=CREAM, outline=OUTLINE, width=0.004)
    c.rect(x0 + 0.02, base + 0.16, x1 - 0.02, base + 0.22, fill=MATTE_D, outline=OUTLINE, width=0.01)
    c.poly([(cx - 0.18, base + 0.2), (cx + 0.18, base + 0.2), (cx + 0.16, base + 0.75), (cx - 0.2, base + 0.78)], fill=CREAM, outline=OUTLINE, width=0.01)
    for k in range(7):
        c.text(cx - 0.01, base + 0.28 + k * 0.065, "LEAVE LEAVE LEAVE", 0.028, OUTLINE)
    c.text(cx - 0.01, base + 0.74, "LEAVE", 0.028, RED)


def _nop_shape(*a, **k):
    return None


# ------------------------------------------------------------------ Registrierung

HOUSE_H = {
    "kupferkessel": 1.8, "mangel": 1.2, "seifenkisten": 0.9, "hackblock": 1.0, "craftservice": 1.4, "topfregal": 2.2,
    "speiseaufzug": 1.8, "fleischerhaken": 2.6, "waescheleine": 2.4, "seance_wand": 2.5, "wandteppich": 2.3,
    "umgestuerzter_stuhl": 0.3, "kristallkugel_tisch": 1.6, "phonograph": 1.4, "bandregal": 2.2, "walkie_station": 1.1,
    "drehstuhl": 1.2, "tonband_boden": 0.2, "kleiderstange": 2.0, "maskenregal": 2.3, "schneiderpuppe": 1.8,
    "sarg_angelehnt": 2.2, "nebelmaschine": 0.6, "orrery": 1.5, "buecherstapel": 0.8, "sternkarte_datum": 2.1,
    "rohre": 2.1, "handabdruck_russ": 1.6, "garderobe": 2.1, "klingelbrett": 1.9, "rauchendes_buch": 0.5, "leiter": 2.5,
    "globus": 1.4, "lesesessel": 1.4, "laterne": 0.7, "engelsstatue_tuch": 2.4, "zersplitterte_bank": 1.0,
    "regiestuhl": 1.2, "regiestuhl_director": 1.2, "kronleuchter_boden": 0.8, "muellcontainer": 1.3, "mischpult": 1.0,
    "perueckenkoepfe": 1.5, "kunstblutregal": 2.3, "portrait": 2.0, "leerer_rahmen": 2.0, "buesten_saeule": 1.9,
    "ruestung": 2.3, "standspiegel": 2.0, "geweihe": 2.3, "hirschkopf": 2.3, "fledermaeuse": 2.5, "billardtisch": 1.0,
    "globusbar": 1.3, "beistelltisch": 0.8, "schuerhaken": 1.0, "holzkorb": 0.7, "schaukelstuhl": 1.3, "kinderschuh": 0.2,
    "safe": 1.3, "aktenkisten": 1.2, "pinnwand": 2.1, "lueftungsgitter": 1.7, "schreibmaschine": 1.3,
    "drehregal": 2.4,
}
HOUSE_PAD = {"laterne": 0.8, "kristallkugel_tisch": 0.5, "nebelmaschine": 0.8, "waescheleine": 0.5, "seance_wand": 0.7,
             "kleiderstange": 0.5, "topfregal": 0.5, "fleischerhaken": 0.4, "rohre": 0.5, "hirschkopf": 0.6,
             "portrait": 0.5, "leerer_rahmen": 0.5, "geweihe": 0.5, "kunstblutregal": 0.5, "sarg_angelehnt": 0.4,
             "ruestung": 0.6, "schreibmaschine": 0.5, "lueftungsgitter": 0.5, "sternkarte_datum": 0.4, "safe": 0.5,
             "garderobe": 0.5, "bandregal": 0.9, "leiter": 0.4, "billardtisch": 0.6, "globusbar": 0.5, "phonograph": 0.6,
             "tonband_boden": 0.4, "rauchendes_buch": 0.5, "umgestuerzter_stuhl": 0.4, "speiseaufzug": 0.5,
             "klingelbrett": 0.5, "handabdruck_russ": 0.5, "wandteppich": 0.4, "pinnwand": 0.4, "walkie_station": 0.5}
NO_SHADOW_KINDS = {"topfregal", "speiseaufzug", "fleischerhaken", "waescheleine", "seance_wand", "wandteppich",
                   "umgestuerzter_stuhl", "tonband_boden", "sternkarte_datum", "rohre", "handabdruck_russ",
                   "klingelbrett", "rauchendes_buch", "portrait", "leerer_rahmen", "geweihe", "hirschkopf",
                   "fledermaeuse", "kinderschuh", "pinnwand", "lueftungsgitter", "schreibmaschine", "kronleuchter_boden"}


def register(h, pad, no_shadow, fns):
    VA.PROP_H.update(h)
    VA.PROP_PAD.update(pad)
    VA.NO_SHADOW.update(no_shadow)
    VA._KIND_FN.update(fns)
    VA.KINDS.update(h)


register(HOUSE_H, HOUSE_PAD, NO_SHADOW_KINDS, {k: globals()["_" + k] for k in HOUSE_H})

import villa_art3  # noqa: E402,F401  (Garten und Gruft, registriert sich selbst)
