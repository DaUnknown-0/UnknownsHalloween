# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_consoles.py - Ravenhollow Cemetery: Bilder fuer alle Konsolen, Vents, Tueren und Kameras.
#
# SCHNITTSTELLE (gen_graveyard.render_consoles):
#   render_all(ctx, ppm, door_slots) -> {key: (PIL RGBA, anker_x_px, anker_y_px)}; Anker von links unten = der
#   Konsolenpunkt (Weltlage). Schluessel wie AtlasMuseumBuilder: Konsolen-Key, "EmergencyButton",
#   "SurveillanceConsole", "AdminTable", "FreeplayLaptop", "Vent/<id>" (+ "/1".."/5"), "Door/<label>" (+ "/1"..),
#   "Camera/<i>" (+ "/on").
#
# Regeln: keine weichen Schatten und Lichthoefe im Bild (das Spiel faerbt beim Hervorheben jeden Pixel mit Deckkraft
# ein, villa_consoles.clean schneidet alles unter Deckkraft 120 ab); Licht malt der Boden. Gleicher Stil wie die
# Objekte (graveyard_art): kraeftige Umrisse, K = 0,55, Mondlicht als Glanzkante.

import math
import random

import graveyard_art as G
import graveyard_art2 as G2
import graveyard_art3 as G3
import villa_console_art as VCA
import villa_consoles as VC
import villa_doors as VD
from museum_art import Canvas, K, OUTLINE, alpha, hexc, lift, shade
import handdraw as HD

OUT_W = G.OUT_W
STONE, STONE_L, STONE_D = G2.STONE, G2.STONE_L, G2.STONE_D
OAK, WOOD, WOOD_D = G.OAK, G.WOOD, G.WOOD_D
IRON, IRON_L, IRON_D = G.IRON, G.IRON_L, G.IRON_D
BRASS, BRASS_D, BRASS_L = G.BRASS, G.BRASS_D, G.BRASS_L
BRONZE, BRONZE_L = G3.BRONZE, G3.BRONZE_L
PARCH = hexc("#d8ccaa")
MIASMA = hexc("#9ad070")
EYE = hexc("#ff3a2a")


def result(c, ppm):
    return VC.clean((c.finish(), int(round((0 - c.x0) * ppm)), int(round((0 - c.y0) * ppm))))


def box(c, x0, y0, x1, y1, z0, h, top, front, w=OUT_W):
    """Kasten in schraeger Aufsicht wie museum_art.Prop.box, direkt auf eine Leinwand."""
    fb, ft = y0 + z0 * K, y0 + (z0 + h) * K
    c.poly([(x0, fb), (x1, fb), (x1, ft), (x0, ft)], fill=front, outline=OUTLINE, width=w)
    c.poly([(x0, ft), (x1, ft), (x1, y1 + (z0 + h) * K), (x0, y1 + (z0 + h) * K)], fill=top, outline=OUTLINE, width=w)
    c.line([(x0 + w, ft - w * 0.8), (x1 - w, ft - w * 0.8)], fill=shade(front, 1.3), width=w * 0.6)


def post(c, x, y0, y1, col=OAK, w=0.08):
    c.rect(x - w / 2, y0, x + w / 2, y1, fill=col, outline=OUTLINE, width=0.025)
    c.line([(x - w / 2 + 0.015, y0 + 0.02), (x - w / 2 + 0.015, y1 - 0.02)], fill=shade(col, 1.35), width=0.012)


def lantern(c, x, y, s=1.0, lit=True):
    c.rect(x - 0.07 * s, y, x + 0.07 * s, y + 0.03 * s, fill=IRON, outline=OUTLINE, width=0.012)
    c.rect(x - 0.06 * s, y + 0.03 * s, x + 0.06 * s, y + 0.2 * s, fill=hexc("#ffd890") if lit else hexc("#3a3e48"), outline=OUTLINE, width=0.012)
    if lit:
        c.ellipse(x, y + 0.11 * s, 0.022 * s, 0.045 * s, fill=hexc("#fff4c8"))
    for dx in (-0.06, 0.06):
        c.line([(x + dx * s, y + 0.03 * s), (x + dx * s, y + 0.2 * s)], fill=IRON, width=0.014)
    c.poly([(x - 0.08 * s, y + 0.2 * s), (x + 0.08 * s, y + 0.2 * s), (x, y + 0.27 * s)], fill=IRON, outline=OUTLINE, width=0.012)
    c.ellipse(x, y + 0.3 * s, 0.03 * s, 0.03 * s, outline=IRON, width=0.012)


# ------------------------------------------------------------------ Motive

def lampenkasten(ppm, idx=0):
    """Rewire the Grave Lamps: gusseiserner Verteilerkasten auf Steinpfosten, Kabel in den Boden, Grablampe oben."""
    c = Canvas(-0.45, -0.3, 0.45, 1.35, ppm)
    box(c, -0.14, -0.1, 0.14, 0.1, 0, 0.75, STONE_L, STONE)
    G3.stone_face(c, -0.13, 0.13, -0.09, -0.1 + 0.75 * K, seed=idx, sw=0.13, sh=0.08)
    by = -0.1 + 0.75 * K
    c.rect(-0.22, by - 0.32, 0.22, by + 0.05, fill=IRON, outline=OUTLINE, width=0.03)
    c.rect(-0.18, by - 0.28, 0.18, by + 0.01, fill=hexc("#1c1e24"), outline=OUTLINE, width=0.015)
    for k, col in enumerate((hexc("#c03a30"), hexc("#3a70c0"), hexc("#d8b040"))):     # lose Draehte im offenen Kasten
        x = -0.12 + k * 0.12
        c.line([(x, by - 0.02), (x + 0.03, by - 0.14), (x - 0.02, by - 0.25)], fill=OUTLINE, width=0.03)
        c.line([(x, by - 0.02), (x + 0.03, by - 0.14), (x - 0.02, by - 0.25)], fill=col, width=0.016)
    c.poly([(0.22, by - 0.32), (0.36, by - 0.36), (0.36, by + 0.02), (0.22, by + 0.05)], fill=IRON_L, outline=OUTLINE, width=0.025)  # offene Klappe
    c.line([(0.0, -0.1), (0.05, -0.2), (0.25, -0.24)], fill=OUTLINE, width=0.04)
    c.line([(0.0, -0.1), (0.05, -0.2), (0.25, -0.24)], fill=hexc("#2a2a30"), width=0.022)
    lantern(c, 0.0, by + 0.05, 0.9, lit=idx % 2 == 0)
    G.moss(c, -0.1, -0.08, 0.06, seed=idx)
    return result(c, ppm)


def register(ppm, idx=0):
    """Sign the Burial Register: Lesepult mit dickem Grabregister, Federkiel, Tintenfass, Kerze."""
    c = Canvas(-0.5, -0.3, 0.5, 1.3, ppm)
    c.poly([(-0.18, -0.12), (0.18, -0.12), (0.12, -0.04), (-0.12, -0.04)], fill=OAK, outline=OUTLINE, width=0.025)
    post(c, 0.0, -0.06, 0.55, OAK, 0.1)
    top = 0.55
    c.poly([(-0.36, top), (0.36, top), (0.32, top + 0.32), (-0.32, top + 0.32)], fill=shade(OAK, 1.1), outline=OUTLINE, width=0.035)
    c.poly([(-0.36, top), (0.36, top), (0.36, top - 0.05), (-0.36, top - 0.05)], fill=shade(OAK, 0.8), outline=OUTLINE, width=0.02)
    c.poly([(-0.3, top + 0.04), (0.0, top + 0.02), (0.0, top + 0.3), (-0.29, top + 0.31)], fill=PARCH, outline=OUTLINE, width=0.015)
    c.poly([(0.3, top + 0.04), (0.0, top + 0.02), (0.0, top + 0.3), (0.29, top + 0.31)], fill=shade(PARCH, 0.95), outline=OUTLINE, width=0.015)
    for k in range(6):                                                                # Eintraege
        y = top + 0.08 + k * 0.035
        c.line([(-0.26, y), (-0.04, y - 0.003)], fill=alpha(hexc("#4a3a2a"), 220), width=0.006)
        if k < 4:
            c.line([(0.04, y - 0.003), (0.22 - k * 0.03, y)], fill=alpha(hexc("#4a3a2a"), 220), width=0.006)
    c.line([(0.04, top + 0.24), (0.14, top + 0.24)], fill=hexc("#8a1a22"), width=0.008)
    c.line([(0.0, top + 0.02), (0.0, top + 0.3)], fill=hexc("#5a1a1a"), width=0.014)
    c.line([(0.14, top + 0.2), (0.32, top + 0.42)], fill=hexc("#e8e4dc"), width=0.012)  # Feder
    c.line([(0.22, top + 0.3), (0.32, top + 0.42)], fill=hexc("#d0ccc4"), width=0.03)
    c.rect(0.26, top + 0.06, 0.33, top + 0.12, fill=hexc("#1a1a24"), outline=OUTLINE, width=0.01)
    G.candle(c, -0.3, top + 0.1, 0.1, lit=True, r=0.022, seed=idx)
    return result(c, ppm)


def abklatsch(ppm, idx=0):
    """Copy the Epitaphs: Staffelei mit Abklatsch-Papier einer Grabinschrift, Kohlestift, Papierrolle."""
    c = Canvas(-0.5, -0.35, 0.5, 1.4, ppm)
    for lx, ly in ((-0.25, -0.15), (0.25, -0.15), (0.0, 0.1)):
        c.line([(lx, ly), (0.0, 1.05)], fill=OUTLINE, width=0.055)
        c.line([(lx, ly), (0.0, 1.05)], fill=OAK, width=0.032)
    c.rect(-0.32, 0.3, 0.32, 0.34, fill=OAK, outline=OUTLINE, width=0.02)
    c.rect(-0.3, 0.34, 0.3, 0.95, fill=hexc("#e8e2d0"), outline=OUTLINE, width=0.025)
    c.rect(-0.26, 0.38, 0.26, 0.9, fill=hexc("#3a3a40"))                              # Kohleabrieb
    for k in range(25):
        x, y = random.Random(k + idx).uniform(-0.24, 0.24), random.Random(k * 7).uniform(0.4, 0.88)
        c.ellipse(x, y, 0.012, 0.008, fill=hexc("#5a5a62"))
    c.line([(-0.04, 0.82), (-0.04, 0.68)], fill=hexc("#e8e2d0"), width=0.02)          # ausgesparte Schrift (hell)
    c.line([(-0.1, 0.77), (0.02, 0.77)], fill=hexc("#e8e2d0"), width=0.02)
    for k in range(3):
        ln = (0.36, 0.28, 0.32)[k]
        c.line([(-ln / 2, 0.6 - k * 0.07), (ln / 2, 0.6 - k * 0.07)], fill=hexc("#e8e2d0"), width=0.016)
    c.ellipse(0.0, 0.92, 0.18, 0.04, fill=None, outline=hexc("#e8e2d0"), width=0.014)
    c.rect(0.22, 0.31, 0.3, 0.33, fill=hexc("#1a1a1e"))                               # Kohlestift
    c.poly([(0.25, -0.2), (0.45, -0.25), (0.47, -0.17), (0.27, -0.12)], fill=hexc("#e8e2d0"), outline=OUTLINE, width=0.015)   # Rolle
    c.ellipse(0.46, -0.21, 0.025, 0.04, fill=hexc("#c8c0a8"), outline=OUTLINE, width=0.01)
    return result(c, ppm)


def laternenschalter(ppm, idx=0):
    """Light the Path: Holzpfosten mit Hebel und Ventilrad, an dem eine Laterne haengt (Gasleitung im Boden)."""
    c = Canvas(-0.4, -0.3, 0.45, 1.4, ppm)
    post(c, 0.0, -0.1, 1.0, OAK, 0.11)
    c.rect(-0.1, 0.45, 0.1, 0.75, fill=IRON, outline=OUTLINE, width=0.025)
    up = idx % 2 == 0
    c.line([(0.0, 0.6), (0.18, 0.6 + (0.18 if up else -0.18))], fill=OUTLINE, width=0.05)
    c.line([(0.0, 0.6), (0.18, 0.6 + (0.18 if up else -0.18))], fill=IRON_L, width=0.025)
    c.ellipse(0.18, 0.6 + (0.18 if up else -0.18), 0.04, 0.04, fill=hexc("#a02a2a"), outline=OUTLINE, width=0.012)
    c.ellipse(0.0, 0.6, 0.03, 0.03, fill=BRASS)
    c.line([(0.0, 0.95), (0.22, 0.95), (0.22, 0.9)], fill=OUTLINE, width=0.04)
    c.line([(0.0, 0.95), (0.22, 0.95), (0.22, 0.9)], fill=IRON, width=0.02)
    lantern(c, 0.22, 0.6, 0.9, lit=up)
    c.line([(0.0, -0.1), (-0.15, -0.18), (-0.38, -0.2)], fill=OUTLINE, width=0.045)
    c.line([(0.0, -0.1), (-0.15, -0.18), (-0.38, -0.2)], fill=hexc("#5a5a62"), width=0.025)
    return result(c, ppm)


def oelverteiler(ppm, idx=0):
    """Light the Path (Laternenschuppen): Wandbrett mit Oelkanne, drei Ventilen und Leitungen zu den Laternen."""
    c = Canvas(-0.55, -0.25, 0.55, 1.3, ppm)
    c.rect(-0.45, 0.0, 0.45, 1.0, fill=OAK, outline=OUTLINE, width=0.035)
    G2.planks_front(c, -0.45, 0.45, 0.02, 0.98, OAK, n=5, seed=idx, vertical=True)
    c.ellipse(0.0, 0.8, 0.2, 0.12, fill=BRASS, outline=OUTLINE, width=0.03)            # Oeltank
    c.rect(-0.2, 0.62, 0.2, 0.8, fill=BRASS, outline=OUTLINE, width=0.03)
    c.ellipse(0.0, 0.62, 0.2, 0.06, fill=BRASS_D, outline=OUTLINE, width=0.02)
    c.line([(-0.12, 0.66), (-0.12, 0.86)], fill=BRASS_L, width=0.02)
    for k in range(3):
        x = -0.3 + k * 0.3
        c.line([(0.0, 0.62), (x, 0.45), (x, 0.05)], fill=OUTLINE, width=0.04)
        c.line([(0.0, 0.62), (x, 0.45), (x, 0.05)], fill=hexc("#8a6a44"), width=0.02)
        c.ellipse(x, 0.35, 0.06, 0.06, fill=hexc("#a02a2a"), outline=OUTLINE, width=0.015)
        for a in range(4):
            c.line([(x, 0.35), (x + 0.06 * math.cos(a * math.pi / 2 + 0.4), 0.35 + 0.06 * math.sin(a * math.pi / 2 + 0.4))], fill=hexc("#701a1a"), width=0.01)
        c.rect(x - 0.05, 0.12, x + 0.05, 0.2, fill=hexc("#e8dcb0"), outline=OUTLINE, width=0.008)
    return result(c, ppm)


def dochtbank(ppm, idx=0):
    """Trim the Lantern Wicks: Werkbank mit drei Laternen (eine offen), Dochtschere, Dochtrolle, Oelflasche."""
    c = Canvas(-0.6, -0.3, 0.6, 1.2, ppm)
    for lx in (-0.45, 0.39):
        c.rect(lx, -0.18, lx + 0.06, -0.18 + 0.75 * K, fill=shade(OAK, 0.85), outline=OUTLINE, width=0.02)
    box(c, -0.5, -0.2, 0.5, 0.15, 0.7, 0.07, shade(OAK, 1.2), OAK)
    ty = -0.2 + 0.77 * K
    for k, lit in enumerate((True, False, True)):
        lantern(c, -0.3 + k * 0.28, ty + 0.06, 0.95, lit=lit)
    c.line([(0.32, ty + 0.05), (0.42, ty + 0.12)], fill=hexc("#9aa2ac"), width=0.014)  # Schere
    c.line([(0.32, ty + 0.12), (0.42, ty + 0.05)], fill=hexc("#9aa2ac"), width=0.014)
    c.ellipse(0.3, ty + 0.04, 0.02, 0.02, outline=hexc("#9aa2ac"), width=0.008)
    c.ellipse(-0.45, ty + 0.08, 0.05, 0.05, fill=hexc("#e8dcc0"), outline=OUTLINE, width=0.012)   # Dochtrolle
    c.rect(0.4, ty + 0.03, 0.46, ty + 0.2, fill=alpha(hexc("#c8a040"), 230), outline=OUTLINE, width=0.01)
    return result(c, ppm)


def grabplan(ppm, idx=0):
    """Map the Graves: Kartenstaender mit gerahmtem Friedhofsplan, Nadeln, Laterne am Haken."""
    c = Canvas(-0.55, -0.25, 0.55, 1.45, ppm)
    post(c, -0.35, -0.12, 0.95, OAK, 0.07)
    post(c, 0.35, -0.12, 0.95, OAK, 0.07)
    c.rect(-0.42, 0.35, 0.42, 1.0, fill=OAK, outline=OUTLINE, width=0.035)
    c.rect(-0.37, 0.4, 0.37, 0.95, fill=PARCH, outline=OUTLINE, width=0.015)
    rnd = random.Random(idx)
    for r in range(4):                                                                # Grabreihen im Plan
        for k in range(6):
            x, y = -0.31 + k * 0.11, 0.48 + r * 0.12
            c.rect(x, y, x + 0.07, y + 0.05, outline=alpha(hexc("#6a5a3a"), 230), width=0.006)
            if rnd.random() < 0.3:
                c.line([(x + 0.01, y + 0.01), (x + 0.06, y + 0.04)], fill=hexc("#5a4a3a"), width=0.006)
    c.line([(-0.37, 0.67), (0.37, 0.67)], fill=alpha(hexc("#8a7a5a"), 220), width=0.02)  # Hauptweg
    for k in range(4):                                                                # Nadeln
        x, y = rnd.uniform(-0.3, 0.3), rnd.uniform(0.45, 0.9)
        c.ellipse(x, y, 0.018, 0.018, fill=hexc("#c02a30") if k % 2 else hexc("#2a6ac0"), outline=OUTLINE, width=0.006)
    c.rect(-0.12, 0.96, 0.12, 1.02, fill=BRASS, outline=OUTLINE, width=0.008)
    return result(c, ppm)


def besen(ppm, idx=0):
    """Sweep the Crypt: Reisigbesen und Kehrschaufel an einer Kiste mit Knochenstaub und einem Schaedel."""
    c = Canvas(-0.5, -0.3, 0.5, 1.2, ppm)
    box(c, -0.3, -0.18, 0.2, 0.12, 0, 0.35, shade(OAK, 1.1), OAK)
    ty = -0.18 + 0.35 * K
    c.rect(-0.27, ty + 0.02, 0.17, 0.12 + 0.35 * K - 0.02, fill=hexc("#a8a49c"))
    G2.skull(c, -0.06, ty + 0.02, 0.9)
    for k in range(3):
        c.line([(0.06 + k * 0.03, ty + 0.05), (0.12 + k * 0.03, ty + 0.12)], fill=G.BONE, width=0.025)
    c.line([(0.32, -0.15), (0.2, 0.95)], fill=OUTLINE, width=0.05)                     # Besenstiel
    c.line([(0.32, -0.15), (0.2, 0.95)], fill=hexc("#8a6a44"), width=0.028)
    for k in range(9):
        a = -0.5 + k * 0.12
        c.line([(0.31, -0.1), (0.33 + math.sin(a) * 0.14, -0.3)], fill=hexc("#a08050"), width=0.014)
    c.line([(0.25, -0.12), (0.4, -0.12)], fill=hexc("#5a4a30"), width=0.02)
    c.poly([(-0.48, -0.25), (-0.3, -0.25), (-0.32, -0.1), (-0.46, -0.1)], fill=IRON_L, outline=OUTLINE, width=0.02)   # Kehrschaufel
    c.line([(-0.39, -0.1), (-0.39, 0.12)], fill=IRON, width=0.025)
    for _ in range(12):
        x, y = random.Random(_).uniform(-0.45, 0.4), random.Random(_ + 9).uniform(-0.28, -0.2)
        c.ellipse(x, y, 0.02, 0.012, fill=hexc("#9a968e"))
    return result(c, ppm)


def kerzenstein(ppm, idx=0):
    """Relight the Ward Candles: flacher Runenstein mit sieben Kerzen im Kreis, Wachsnasen, Runen."""
    c = Canvas(-0.6, -0.4, 0.6, 0.8, ppm)
    pts = HD.wobble_ellipse(0.0, 0.0, 0.48, 0.3, amp=0.03, seed=idx)
    c.poly([(x, y - 0.08) for x, y in pts], fill=STONE_D, outline=OUTLINE, width=0.04)
    c.poly(pts, fill=STONE, outline=OUTLINE, width=0.04)
    c.ellipse(0.0, 0.0, 0.3, 0.17, outline=alpha(G3.RUNE, 200), width=0.012)
    for k in range(7):
        a = math.pi / 2 + k * math.tau / 7
        x, y = 0.34 * math.cos(a), 0.2 * math.sin(a)
        G.candle(c, x, y, 0.08 + 0.04 * ((k + idx) % 3), lit=k % 3 != 1, r=0.026, seed=idx * 7 + k)
    for k in range(3):
        a = k * 2.1
        c.line([(0.1 * math.cos(a), 0.06 * math.sin(a)), (0.1 * math.cos(a) + 0.05, 0.06 * math.sin(a) + 0.03)], fill=alpha(G3.RUNE, 220), width=0.012)
    return result(c, ppm)


def schiefer_stein(ppm, idx=0):
    """Straighten a Headstone: schief gesackter Grabstein, Seil um den Stein zu einem Holzpflock, Schaufel."""
    c = Canvas(-0.6, -0.35, 0.6, 1.15, ppm)
    c.poly(HD.wobble_ellipse(0.0, -0.1, 0.4, 0.16, amp=0.02, seed=idx), fill=G.EARTH, outline=OUTLINE, width=0.02)
    G.slab(c, "round", -0.24, 0.24, -0.05, 0.62, 0.12, shade(G.GRANITE, 1.05), seed=idx, tilt=0.32)
    c.line([(0.12, 0.4), (0.42, -0.05)], fill=hexc("#b0946a"), width=0.022)
    c.line([(0.12, 0.4), (0.42, -0.05)], fill=alpha(hexc("#6a5030"), 200), width=0.008)
    c.poly([(0.38, -0.25), (0.46, -0.25), (0.45, 0.02), (0.39, 0.02)], fill=OAK, outline=OUTLINE, width=0.02)
    c.line([(-0.42, -0.25), (-0.5, 0.45)], fill=OUTLINE, width=0.045)                 # Schaufel
    c.line([(-0.42, -0.25), (-0.5, 0.45)], fill=hexc("#7a5434"), width=0.025)
    c.poly([(-0.48, -0.32), (-0.34, -0.32), (-0.36, -0.15), (-0.46, -0.15)], fill=hexc("#8a9098"), outline=OUTLINE, width=0.02)
    return result(c, ppm)


def ossuar(ppm, idx=0):
    """Unlock the Ossuary: Beinhaus-Nische mit Schaedeln hinter einem Gitter, schweres Vorhaengeschloss."""
    c = Canvas(-0.55, -0.3, 0.55, 1.3, ppm)
    box(c, -0.45, -0.15, 0.45, 0.15, 0, 1.7, STONE_L, STONE)
    G3.stone_face(c, -0.44, 0.44, -0.14, -0.15 + 1.7 * K - 0.02, seed=idx, sw=0.24, sh=0.12)
    nx0, nx1, ny0, ny1 = -0.3, 0.3, 0.05, 0.75
    arch = [(nx0, ny0), (nx1, ny0), (nx1, ny1 - 0.15)] + [(0.3 * math.cos(t), ny1 - 0.15 + 0.15 * math.sin(t)) for t in [j * math.pi / 10 for j in range(11)]] + [(nx0, ny1 - 0.15)]
    c.poly(arch, fill=hexc("#120e10"), outline=OUTLINE, width=0.03)
    for r in range(3):                                                                # Schaedelreihen
        for k in range(4 - (r == 2)):
            G2.skull(c, -0.21 + k * 0.14 + (0.07 if r == 2 else 0), ny0 + 0.04 + r * 0.17, 0.85, col=shade(G.BONE, 0.85 + 0.05 * r))
    for k in range(6):                                                                # Gitter
        x = nx0 + 0.05 + k * 0.1
        c.line([(x, ny0), (x, ny1 - 0.02)], fill=OUTLINE, width=0.035)
        c.line([(x, ny0), (x, ny1 - 0.02)], fill=IRON_L, width=0.016)
    for y in (ny0 + 0.25, ny0 + 0.5):
        c.line([(nx0, y), (nx1, y)], fill=OUTLINE, width=0.035)
        c.line([(nx0, y), (nx1, y)], fill=IRON_L, width=0.016)
    c.ellipse(0.0, ny0 + 0.36, 0.06, 0.07, outline=IRON_D, width=0.025)              # Schloss
    c.rect(-0.08, ny0 + 0.2, 0.08, ny0 + 0.34, fill=BRASS, outline=OUTLINE, width=0.02)
    c.ellipse(0.0, ny0 + 0.28, 0.015, 0.02, fill=OUTLINE)
    return result(c, ppm)


def kurbelwinde(ppm, idx=0):
    """Wind the Well Crank: Seilwinde mit grossem Speichenrad und Kurbel auf einem Holzbock, Seil zum Brunnen."""
    c = Canvas(-0.6, -0.3, 0.6, 1.3, ppm)
    for x in (-0.35, 0.35):
        c.poly([(x - 0.12, -0.15), (x + 0.12, -0.15), (x + 0.03, 0.75), (x - 0.03, 0.75)], fill=OAK, outline=OUTLINE, width=0.025)
    c.rect(-0.4, 0.6, 0.4, 0.68, fill=shade(OAK, 0.85), outline=OUTLINE, width=0.02)   # Welle
    for k in range(5):
        c.line([(-0.28 + k * 0.1, 0.6), (-0.25 + k * 0.1, 0.68)], fill=hexc("#b0946a"), width=0.025)
    wx, wy = 0.0, 0.64                                                                # Speichenrad
    for col_, wd in ((OUTLINE, 0.06), (IRON, 0.035)):
        c.ellipse(wx, wy, 0.3, 0.3, outline=col_, width=wd)
    for k in range(6):
        a = k * math.pi / 3 + idx * 0.3
        c.line([(wx, wy), (wx + 0.28 * math.cos(a), wy + 0.28 * math.sin(a))], fill=OUTLINE, width=0.035)
        c.line([(wx, wy), (wx + 0.28 * math.cos(a), wy + 0.28 * math.sin(a))], fill=IRON_L, width=0.016)
    c.ellipse(wx, wy, 0.05, 0.05, fill=IRON_D, outline=OUTLINE, width=0.015)
    c.line([(0.3, 0.64), (0.48, 0.64), (0.48, 0.5)], fill=OUTLINE, width=0.05)
    c.line([(0.3, 0.64), (0.48, 0.64), (0.48, 0.5)], fill=IRON_L, width=0.025)
    c.rect(0.45, 0.4, 0.51, 0.52, fill=hexc("#7a5434"), outline=OUTLINE, width=0.012)
    return result(c, ppm)


def vogelscheuche(ppm, idx=0):
    """Shoo the Ravens: Vogelscheuche mit Kuerbiskopf, Fetzenmantel und Hut, zwei Raben auf den Armen."""
    c = Canvas(-0.7, -0.3, 0.7, 1.75, ppm)
    post(c, 0.0, -0.12, 1.2, OAK, 0.08)
    c.line([(-0.55, 0.92), (0.55, 0.92)], fill=OUTLINE, width=0.07)
    c.line([(-0.55, 0.92), (0.55, 0.92)], fill=OAK, width=0.045)
    coat = [(-0.5, 0.97), (0.5, 0.97), (0.3, 0.88), (0.24, 0.35), (0.12, 0.42), (0.02, 0.3), (-0.12, 0.4), (-0.24, 0.33), (-0.3, 0.88)]
    c.poly(coat, fill=hexc("#4a4a3a"), outline=OUTLINE, width=0.035)
    for k in range(4):                                                                # Flicken und Stroh
        c.rect(-0.18 + k * 0.1, 0.55 + (k % 2) * 0.15, -0.1 + k * 0.1, 0.62 + (k % 2) * 0.15, fill=hexc("#7a3a2a") if k % 2 else hexc("#3a5a6a"), outline=OUTLINE, width=0.008)
    for sx in (-1, 1):
        for k in range(4):
            c.line([(sx * 0.52, 0.94), (sx * (0.58 + k * 0.02), 0.86 - k * 0.03)], fill=hexc("#d8b860"), width=0.012)
    c.ellipse(0.0, 1.12, 0.17, 0.15, fill=hexc("#d07a2a"), outline=OUTLINE, width=0.03)   # Kuerbiskopf
    for k in (-0.08, 0.08):
        c.line([(k, 1.0), (k * 0.6, 1.25)], fill=alpha(hexc("#a05a1a"), 220), width=0.012)
    for sx in (-1, 1):
        c.poly([(sx * 0.07, 1.15), (sx * 0.03, 1.1), (sx * 0.1, 1.1)], fill=hexc("#ffd060"))
    c.poly([(-0.08, 1.05), (0.08, 1.05), (0.04, 1.02), (0.0, 1.05), (-0.04, 1.02)], fill=hexc("#ffd060"))
    c.poly([(-0.22, 1.22), (0.22, 1.22), (0.12, 1.28), (0.05, 1.48), (-0.08, 1.4), (-0.12, 1.28)], fill=hexc("#2a2a30"), outline=OUTLINE, width=0.025)  # Hut
    G.raven(c, -0.45, 0.97, 1, 1.0)
    G.raven(c, 0.5, 0.97, -1, 1.0)
    return result(c, ppm)


def kranzkiste(ppm, idx=0):
    """Clear the Wreaths: Bretterkiste voll alter Kraenze und welker Blumen, Schleifen haengen heraus."""
    c = Canvas(-0.55, -0.3, 0.55, 1.0, ppm)
    rnd = random.Random(idx)
    box(c, -0.4, -0.15, 0.4, 0.25, 0, 0.5, shade(OAK, 0.95), OAK)
    G2.planks_front(c, -0.4, 0.4, -0.13, -0.15 + 0.5 * K - 0.02, OAK, n=3, seed=idx)
    ty = -0.15 + 0.5 * K
    for k in range(3):
        G.wreath(c, -0.18 + k * 0.18, ty + 0.12 + (k % 2) * 0.05, 0.13, rnd)
    G.bouquet(c, 0.28, ty + 0.05, rnd, dead=True, s=0.9)
    c.poly([(-0.3, ty), (-0.26, ty), (-0.24, ty - 0.2), (-0.3, ty - 0.18)], fill=hexc("#6a1a2a"), outline=OUTLINE, width=0.008)
    c.rect(-0.12, -0.05, 0.12, 0.05, fill=hexc("#e8dcb0"), outline=OUTLINE, width=0.008)
    return result(c, ppm)


def kohlenkasten(ppm, idx=0):
    """Stoke the Furnace: Kohleneimer mit Schaufel und ein Stapel Scheitholz."""
    c = Canvas(-0.55, -0.3, 0.55, 0.95, ppm)
    for k in range(3):                                                                # Scheitholz
        for j in range(3 - k):
            x = -0.42 + j * 0.13 + k * 0.065
            y = -0.15 + k * 0.1
            c.ellipse(x, y, 0.07, 0.06, fill=hexc("#8a6a44"), outline=OUTLINE, width=0.015)
            c.ellipse(x, y, 0.035, 0.03, outline=hexc("#5a4030"), width=0.008)
    c.poly([(0.0, -0.18), (0.36, -0.18), (0.42, 0.25), (-0.06, 0.25)], fill=IRON, outline=OUTLINE, width=0.03)
    c.ellipse(0.18, 0.25, 0.24, 0.07, fill=hexc("#1e1e24"), outline=OUTLINE, width=0.02)
    for k in range(8):
        c.ellipse(0.06 + k * 0.035, 0.27 + (k % 2) * 0.02, 0.03, 0.022, fill=hexc("#2a2a34"), outline=alpha(OUTLINE, 200), width=0.006)
    c.line([(0.12, 0.25), (0.3, 0.65)], fill=OUTLINE, width=0.045)
    c.line([(0.12, 0.25), (0.3, 0.65)], fill=hexc("#7a5434"), width=0.025)
    c.line([(-0.02, 0.1), (0.38, 0.1)], fill=IRON_L, width=0.012)
    return result(c, ppm)


def oelkanister(ppm, idx=0):
    """Stoke the Furnace (Sargkammer): Regal mit Lampenoel-Kanistern und Trichter."""
    c = Canvas(-0.55, -0.3, 0.55, 1.2, ppm)
    for x in (-0.42, 0.38):
        c.rect(x, -0.12, x + 0.05, 0.95, fill=OAK, outline=OUTLINE, width=0.02)
    for k, y in enumerate((0.0, 0.45)):
        c.rect(-0.42, y, 0.43, y + 0.05, fill=shade(OAK, 1.1), outline=OUTLINE, width=0.02)
        for j in range(3):
            x = -0.28 + j * 0.27
            col = (hexc("#8a2a2a"), hexc("#3a5a3a"), hexc("#7a6a3a"))[(j + k) % 3]
            c.rect(x - 0.1, y + 0.05, x + 0.1, y + 0.34, fill=col, outline=OUTLINE, width=0.02)
            c.rect(x + 0.02, y + 0.34, x + 0.07, y + 0.4, fill=IRON, outline=OUTLINE, width=0.01)
            c.line([(x - 0.06, y + 0.38), (x + 0.0, y + 0.38)], fill=IRON, width=0.02)
            c.line([(x - 0.08, y + 0.08), (x - 0.08, y + 0.3)], fill=alpha(shade(col, 1.4), 200), width=0.012)
    c.poly([(0.28, 0.95), (0.42, 0.95), (0.37, 0.85), (0.33, 0.85)], fill=IRON_L, outline=OUTLINE, width=0.012)
    return result(c, ppm)


def aschentisch(ppm, idx=0):
    """Identify the Ashes: Tisch mit Urnen, Waage, Lupe und Etiketten."""
    c = Canvas(-0.6, -0.3, 0.6, 1.1, ppm)
    for lx in (-0.45, 0.39):
        c.rect(lx, -0.18, lx + 0.06, -0.18 + 0.75 * K, fill=shade(OAK, 0.85), outline=OUTLINE, width=0.02)
    box(c, -0.5, -0.2, 0.5, 0.18, 0.7, 0.07, hexc("#d8d8d0"), OAK)
    ty = -0.2 + 0.77 * K
    for k, col in enumerate((BRONZE, hexc("#4a5a6a"), hexc("#6a4a3a"))):
        ux, uy = -0.35 + k * 0.17, ty + 0.12
        c.poly([(ux - 0.045, uy), (ux + 0.045, uy), (ux + 0.07, uy + 0.1), (ux + 0.05, uy + 0.18), (ux - 0.05, uy + 0.18), (ux - 0.07, uy + 0.1)],
               fill=col, outline=OUTLINE, width=0.012)
        c.rect(ux - 0.04, uy + 0.18, ux + 0.04, uy + 0.21, fill=shade(col, 0.8), outline=OUTLINE, width=0.008)
        c.rect(ux - 0.035, uy + 0.05, ux + 0.035, uy + 0.09, fill=hexc("#e8dcb0"))
    c.line([(0.2, ty + 0.1), (0.2, ty + 0.32)], fill=BRASS_D, width=0.016)               # Waage
    c.line([(0.06, ty + 0.3), (0.34, ty + 0.32)], fill=BRASS, width=0.014)
    for x, y in ((0.06, ty + 0.3), (0.34, ty + 0.32)):
        c.line([(x, y), (x, y - 0.08)], fill=BRASS_D, width=0.006)
        c.ellipse(x, y - 0.09, 0.05, 0.015, fill=BRASS, outline=OUTLINE, width=0.008)
    c.ellipse(0.4, ty + 0.06, 0.05, 0.04, fill=alpha(hexc("#c8dce8"), 200), outline=BRASS_D, width=0.012)   # Lupe
    c.line([(0.44, ty + 0.03), (0.48, ty - 0.01)], fill=hexc("#5a3a24"), width=0.02)
    return result(c, ppm)


def pruefplatte(ppm, idx=0):
    """Identify the Remains (Bodenblock): Marmorplatte im Boden mit Kreidekreis und Messzeichen."""
    c = Canvas(-0.6, -0.45, 0.6, 0.45, ppm)
    c.rect(-0.5, -0.35, 0.5, 0.35, fill=hexc("#c8c6be"), outline=OUTLINE, width=0.03)
    c.rect(-0.44, -0.29, 0.44, 0.29, outline=hexc("#8a8880"), width=0.012)
    c.ellipse(0.0, 0.0, 0.3, 0.2, outline=hexc("#f0f0ea"), width=0.016)
    for k in range(8):
        a = k * math.pi / 4
        c.line([(0.3 * math.cos(a), 0.2 * math.sin(a)), (0.36 * math.cos(a), 0.24 * math.sin(a))], fill=hexc("#f0f0ea"), width=0.012)
    for k in range(4):
        c.line([(-0.4 + k * 0.05, -0.27), (-0.4 + k * 0.05, -0.22 if k % 2 else -0.24)], fill=hexc("#5a5a5a"), width=0.006)
    c.ellipse(0.18, -0.12, 0.05, 0.03, fill=hexc("#7a1a24"))
    return result(c, ppm)


def glockenstuhl(ppm, idx=0):
    """Ring the Bell: kleine Bronzeglocke im Holzjoch auf zwei Pfosten, Zugseil mit Knoten."""
    c = Canvas(-0.55, -0.3, 0.55, 1.5, ppm)
    for x in (-0.38, 0.38):
        post(c, x, -0.12, 1.15, OAK, 0.09)
    c.rect(-0.46, 1.08, 0.46, 1.18, fill=shade(OAK, 1.1), outline=OUTLINE, width=0.025)
    c.poly([(-0.46, 1.18), (0.46, 1.18), (0.3, 1.3), (-0.3, 1.3)], fill=G3.SLATE_ROOF, outline=OUTLINE, width=0.025)
    by = 0.62
    bell = [(-0.2, by), (0.2, by), (0.17, by + 0.05), (0.12, by + 0.28), (0.07, by + 0.38), (-0.07, by + 0.38), (-0.12, by + 0.28), (-0.17, by + 0.05)]
    c.line([(0.0, by + 0.38), (0.0, 1.08)], fill=OUTLINE, width=0.05)
    c.poly(bell, fill=BRONZE, outline=OUTLINE, width=0.03)
    c.poly([(-0.15, by + 0.05), (-0.09, by + 0.05), (-0.05, by + 0.3), (-0.08, by + 0.32)], fill=alpha(BRONZE_L, 210))
    c.line([(-0.18, by + 0.04), (0.18, by + 0.04)], fill=shade(BRONZE, 0.7), width=0.014)
    c.ellipse(0.02, by - 0.03, 0.035, 0.035, fill=IRON_D, outline=OUTLINE, width=0.01)
    c.line([(0.12, by + 0.2), (0.16, 0.2), (0.15, -0.05)], fill=hexc("#b0946a"), width=0.022)
    for y in (0.3, 0.1):
        c.ellipse(0.155, y, 0.025, 0.02, fill=hexc("#b0946a"), outline=OUTLINE, width=0.008)
    return result(c, ppm)


def miasma_gitter(ppm, idx=0):
    """Miasma: Gruftschacht mit Gussgitter, gruener Faulnisdunst steigt auf, Ventilrad zum Schliessen."""
    c = Canvas(-0.55, -0.35, 0.55, 1.15, ppm)
    c.rect(-0.42, -0.28, 0.42, 0.28, fill=STONE, outline=OUTLINE, width=0.035)
    c.rect(-0.32, -0.2, 0.32, 0.2, fill=hexc("#0e140c"), outline=OUTLINE, width=0.025)
    for k in range(6):
        x = -0.27 + k * 0.108
        c.line([(x, -0.2), (x, 0.2)], fill=OUTLINE, width=0.035)
        c.line([(x, -0.2), (x, 0.2)], fill=IRON_L, width=0.015)
    for k in range(4):                                                                # Dunstfahnen (deckend, kein Glow)
        x = -0.15 + k * 0.1
        pts = HD.wobble([(x, 0.1), (x + 0.05, 0.4), (x - 0.03, 0.65), (x + 0.04, 0.85)], amp=0.03, seed=idx * 5 + k, step=0.06)
        c.line(pts, fill=alpha(MIASMA, 170), width=0.06)
        c.line(pts, fill=alpha(shade(MIASMA, 1.2), 200), width=0.02)
    c.line([(0.42, 0.05), (0.52, 0.05), (0.52, 0.35)], fill=OUTLINE, width=0.05)        # Rohr mit Ventilrad
    c.line([(0.42, 0.05), (0.52, 0.05), (0.52, 0.35)], fill=hexc("#7a6a4a"), width=0.028)
    c.ellipse(0.52, 0.4, 0.08, 0.08, outline=hexc("#a02a2a"), width=0.025)
    c.line([(0.44, 0.4), (0.6, 0.4)], fill=hexc("#a02a2a"), width=0.018)
    c.line([(0.52, 0.32), (0.52, 0.48)], fill=hexc("#a02a2a"), width=0.018)
    return result(c, ppm)


def glockenseil(ppm, idx=0):
    """Death Knell: Glockenseil mit Griffwulst, haengt von einem Balken auf zwei Pfosten (Zugstelle)."""
    c = Canvas(-0.45, -0.25, 0.45, 1.55, ppm)
    for x in (-0.3, 0.3):
        post(c, x, -0.1, 1.25, OAK, 0.08)
    c.rect(-0.38, 1.2, 0.38, 1.28, fill=shade(OAK, 1.1), outline=OUTLINE, width=0.025)
    c.ellipse(0.0, 1.24, 0.06, 0.06, fill=IRON, outline=OUTLINE, width=0.015)          # Umlenkrolle
    rope = HD.wobble([(0.0, 1.22), (0.01, 0.8), (-0.01, 0.35)], amp=0.01, seed=idx, step=0.05)
    c.line(rope, fill=OUTLINE, width=0.045)
    c.line(rope, fill=hexc("#b0946a"), width=0.026)
    for k in range(10):
        y = 0.4 + k * 0.08
        c.line([(-0.012, y), (0.012, y + 0.03)], fill=hexc("#7a6040"), width=0.008)
    c.ellipse(-0.01, 0.42, 0.06, 0.1, fill=hexc("#8a2a2a"), outline=OUTLINE, width=0.02)   # Griffwulst (Sally)
    for k in range(4):
        c.line([(-0.06, 0.36 + k * 0.035), (0.04, 0.38 + k * 0.035)], fill=hexc("#d8b860"), width=0.01)
    c.line([(-0.01, 0.32), (-0.02, 0.15), (0.03, 0.05)], fill=hexc("#b0946a"), width=0.02)
    return result(c, ppm)


def laternenhebel(ppm, idx=0):
    """Lanterns Out: Hebelkasten mit Glasroehren der Laternenkreise (eine durchgebrannt), grosser Haupthebel."""
    c = Canvas(-0.55, -0.25, 0.55, 1.35, ppm)
    c.rect(-0.42, 0.05, 0.42, 1.05, fill=IRON, outline=OUTLINE, width=0.035)
    c.rect(-0.36, 0.11, 0.36, 0.99, fill=hexc("#22242a"), outline=OUTLINE, width=0.015)
    for k in range(4):
        x = -0.25 + k * 0.17
        dead = k == (idx % 4)
        c.rect(x - 0.05, 0.55, x + 0.05, 0.9, fill=alpha(hexc("#c8d8e0"), 200), outline=OUTLINE, width=0.012)
        c.rect(x - 0.035, 0.58, x + 0.035, 0.87, fill=hexc("#3a3a40") if dead else hexc("#ffd070"))
        c.rect(x - 0.06, 0.52, x + 0.06, 0.56, fill=BRASS, outline=OUTLINE, width=0.008)
        c.rect(x - 0.06, 0.89, x + 0.06, 0.93, fill=BRASS, outline=OUTLINE, width=0.008)
    c.rect(-0.12, 0.18, 0.12, 0.42, fill=IRON_L, outline=OUTLINE, width=0.02)
    c.line([(0.0, 0.3), (0.2, 0.2)], fill=OUTLINE, width=0.06)
    c.line([(0.0, 0.3), (0.2, 0.2)], fill=hexc("#a02a2a"), width=0.035)
    c.ellipse(0.2, 0.2, 0.045, 0.045, fill=hexc("#1a1a1e"), outline=OUTLINE, width=0.012)
    return result(c, ppm)


def torglocke(ppm, idx=0):
    """Gate Bell Silent: Torglocke an geschwungenem Wandarm auf einem Pfosten, Zugkette, Schild."""
    c = Canvas(-0.5, -0.25, 0.55, 1.6, ppm)
    post(c, -0.25, -0.12, 1.3, STONE, 0.14)
    arm = [(-0.18, 1.2), (0.05, 1.25), (0.22, 1.18)]
    c.line(arm, fill=OUTLINE, width=0.05)
    c.line(arm, fill=IRON, width=0.025)
    by = 0.86
    bell = [(0.06, by), (0.38, by), (0.34, by + 0.05), (0.29, by + 0.22), (0.25, by + 0.3), (0.19, by + 0.3), (0.15, by + 0.22), (0.1, by + 0.05)]
    c.line([(0.22, by + 0.3), (0.22, 1.18)], fill=OUTLINE, width=0.03)
    c.poly(bell, fill=BRONZE, outline=OUTLINE, width=0.025)
    c.line([(0.12, by + 0.06), (0.17, by + 0.24)], fill=alpha(BRONZE_L, 210), width=0.02)
    c.ellipse(0.22, by - 0.03, 0.03, 0.03, fill=IRON_D, outline=OUTLINE, width=0.01)
    for k in range(8):                                                                # Zugkette
        c.ellipse(0.24 + (k % 2) * 0.01, by - 0.08 - k * 0.07, 0.018, 0.03, outline=IRON_L, width=0.008)
    c.rect(-0.38, 0.45, -0.12, 0.62, fill=hexc("#d8ccaa"), outline=OUTLINE, width=0.012)
    c.line([(-0.34, 0.55), (-0.16, 0.55)], fill=hexc("#4a3a2a"), width=0.008)
    c.line([(-0.34, 0.51), (-0.2, 0.51)], fill=hexc("#4a3a2a"), width=0.008)
    return result(c, ppm)


def totenglocke(ppm, idx=0):
    """EmergencyButton: Lesepult vor dem Altar mit der Totenglocke unter einer Glasglocke, rotes Samttuch."""
    c = Canvas(-0.5, -0.3, 0.5, 1.4, ppm)
    c.poly([(-0.22, -0.14), (0.22, -0.14), (0.15, -0.04), (-0.15, -0.04)], fill=OAK, outline=OUTLINE, width=0.025)
    post(c, 0.0, -0.06, 0.6, OAK, 0.12)
    c.poly([(-0.32, 0.58), (0.32, 0.58), (0.36, 0.72), (-0.36, 0.72)], fill=hexc("#7a1e2a"), outline=OUTLINE, width=0.03)
    c.line([(-0.33, 0.6), (0.33, 0.6)], fill=G2.GOLD, width=0.016)
    for k in range(9):
        c.line([(-0.3 + k * 0.075, 0.58), (-0.3 + k * 0.075, 0.54)], fill=G2.GOLD, width=0.008)
    bx, by = 0.0, 0.74
    c.poly([(bx - 0.13, by), (bx + 0.13, by), (bx + 0.1, by + 0.06), (bx + 0.07, by + 0.24), (bx - 0.07, by + 0.24), (bx - 0.1, by + 0.06)],
           fill=BRONZE, outline=OUTLINE, width=0.02)
    c.line([(bx, by + 0.24), (bx, by + 0.36)], fill=hexc("#3a2a20"), width=0.04)
    c.ellipse(bx, by + 0.38, 0.035, 0.03, fill=hexc("#3a2a20"), outline=OUTLINE, width=0.01)
    c.line([(bx - 0.07, by + 0.06), (bx - 0.04, by + 0.2)], fill=alpha(BRONZE_L, 220), width=0.014)
    dome = [(bx - 0.2, by - 0.01)] + [(bx + 0.2 * math.cos(t), by + 0.32 + 0.16 * math.sin(t)) for t in [math.pi - j * math.pi / 12 for j in range(13)]] + [(bx + 0.2, by - 0.01)]
    c.line(dome, fill=alpha(hexc("#d8e8f4"), 200), width=0.02)
    c.line([(bx - 0.14, by + 0.1), (bx - 0.13, by + 0.36)], fill=alpha((255, 255, 255, 255), 160), width=0.02)
    c.ellipse(bx, by - 0.01, 0.21, 0.03, fill=BRASS, outline=OUTLINE, width=0.012)
    return result(c, ppm)


def spiegelpult(ppm, idx=0):
    """SurveillanceConsole: Pult des Waechters mit vier Spiegeln in Rahmen (zeigen die Wasserspeier-Blicke) und
    einer Kristallkugel."""
    c = Canvas(-0.7, -0.3, 0.7, 1.35, ppm)
    box(c, -0.6, -0.2, 0.6, 0.15, 0, 0.8, shade(OAK, 1.15), OAK)
    G2.planks_front(c, -0.6, 0.6, -0.18, -0.2 + 0.8 * K - 0.02, OAK, n=4, seed=idx, vertical=True)
    ty = -0.2 + 0.8 * K
    for k in range(4):                                                                # Spiegel auf Staendern
        x = -0.45 + k * 0.3
        y = ty + 0.25
        c.line([(x, ty + 0.05), (x, y)], fill=BRASS_D, width=0.02)
        c.ellipse(x, y + 0.13, 0.12, 0.15, fill=BRASS, outline=OUTLINE, width=0.025)
        c.ellipse(x, y + 0.13, 0.095, 0.12, fill=hexc("#2a3a50"))
        c.ellipse(x - 0.02, y + 0.18, 0.05, 0.06, fill=hexc("#3e5670"))
        c.poly([(x - 0.06, y + 0.06), (x + 0.06, y + 0.06), (x, y + 0.16)], fill=hexc("#1e2838"))   # Silhouette
        c.line([(x - 0.06, y + 0.22), (x - 0.03, y + 0.25)], fill=alpha((255, 255, 255, 255), 170), width=0.012)
    c.ellipse(0.0, ty + 0.1, 0.07, 0.03, fill=BRASS_D, outline=OUTLINE, width=0.01)
    c.ellipse(0.0, ty + 0.16, 0.07, 0.07, fill=alpha(hexc("#c8b8f4"), 230), outline=OUTLINE, width=0.015)
    c.ellipse(-0.02, ty + 0.18, 0.025, 0.02, fill=alpha((255, 255, 255, 255), 200))
    return result(c, ppm)


def grabplantisch(ppm, idx=0):
    """AdminTable: grosser Tisch mit dem Gesamtplan des Friedhofs, Kerzen an den Ecken, Lineal, Stecknadeln."""
    c = Canvas(-1.0, -0.6, 1.0, 1.0, ppm)
    for lx, ly in ((-0.8, -0.45), (0.74, -0.45)):
        c.rect(lx, ly, lx + 0.07, ly + 0.8 * K, fill=shade(OAK, 0.85), outline=OUTLINE, width=0.025)
    box(c, -0.85, -0.5, 0.85, 0.45, 0.75, 0.08, shade(OAK, 1.15), OAK)
    ty = -0.5 + 0.83 * K
    tt = 0.45 + 0.83 * K
    c.rect(-0.75, ty + 0.06, 0.75, tt - 0.06, fill=PARCH, outline=OUTLINE, width=0.02)
    rnd = random.Random(idx)
    for (x0, y0, x1, y1) in ((-0.6, ty + 0.15, -0.3, ty + 0.4), (-0.15, ty + 0.12, 0.15, ty + 0.35), (0.3, ty + 0.15, 0.6, ty + 0.42),
                             (-0.6, tt - 0.4, -0.3, tt - 0.15), (0.3, tt - 0.4, 0.6, tt - 0.15)):
        c.rect(x0, y0, x1, y1, outline=hexc("#6a5a3a"), width=0.01)
        for k in range(8):
            gx, gy = rnd.uniform(x0 + 0.03, x1 - 0.06), rnd.uniform(y0 + 0.03, y1 - 0.05)
            c.rect(gx, gy, gx + 0.03, gy + 0.02, fill=hexc("#8a7a5a"))
    c.line([(-0.75, (ty + tt) / 2), (0.75, (ty + tt) / 2)], fill=hexc("#a8987a"), width=0.04)
    c.line([(0.0, ty + 0.06), (0.0, tt - 0.06)], fill=hexc("#a8987a"), width=0.04)
    c.ellipse(-0.1, tt - 0.25, 0.1, 0.08, outline=hexc("#a02a2a"), width=0.012)
    c.line([(0.4, ty + 0.5), (0.7, ty + 0.62)], fill=hexc("#c8a060"), width=0.03)
    for (x, y) in ((-0.78, ty + 0.05), (0.78, ty + 0.05)):
        G.candle(c, x, y, 0.12, lit=True, r=0.03, seed=int(x * 10) + idx)
    return result(c, ppm)


def kiste(ppm, idx=0):
    """FreeplayLaptop: Holzkiste mit einem aufgeschlagenen Notizbuch und einer Laterne."""
    c = Canvas(-0.45, -0.3, 0.45, 0.9, ppm)
    box(c, -0.32, -0.2, 0.32, 0.2, 0, 0.45, shade(OAK, 1.1), OAK)
    G2.planks_front(c, -0.32, 0.32, -0.18, -0.2 + 0.45 * K - 0.02, OAK, n=3, seed=idx)
    ty = -0.2 + 0.45 * K
    G2.book(c, -0.05, ty + 0.12, 0.14, 0.12, open_=True)
    lantern(c, 0.22, ty + 0.08, 0.8, lit=True)
    return result(c, ppm)


BY_NAME = {
    "FixWiringConsole": lampenkasten, "SwipeCardConsole": register, "UploadDataConsole": abklatsch, "DataConsole": abklatsch,
    "DivertPowerConsole": laternenschalter, "CalibrateConsole": dochtbank, "ChartCourseConsole": grabplan,
    "CleanFilterConsole": besen, "ShieldConsole": kerzenstein, "StabilizeSteeringConsole": schiefer_stein,
    "UnlockManifoldsConsole": ossuar, "AlignEngineConsole": kurbelwinde, "WeaponConsole": vogelscheuche,
    "GarbageConsole": kranzkiste, "AirlockConsole": kranzkiste, "FuelEngineConsole": kohlenkasten, "gasCanConsole": oelkanister,
    "MedBayConsole": aschentisch, "MedScanner": pruefplatte, "StartReactorConsole": glockenstuhl, "NoOxyConsole": miasma_gitter,
    "UpperHandConsole": glockenseil, "LowerHandConsole": glockenseil, "SwitchConsole": laternenhebel, "FixCommsConsole": torglocke,
}
SPECIAL = {"EmergencyButton": totenglocke, "SurveillanceConsole": spiegelpult, "AdminTable": grabplantisch, "FreeplayLaptop": kiste}
OVERRIDE = {"Electrical/DivertPowerConsole/0": oelverteiler}


# ------------------------------------------------------------------ Vents

def slab_frames(ppm, seed=0):
    """Vent im Freien: Grabplatte im Rasen, rutscht nach Sueden und gibt einen Schacht mit Sprossen frei.
    6 Bilder, gleiche Groesse, Anker = Mitte der Oeffnung."""
    out = []
    rnd = random.Random(seed)
    col = shade(G.GRANITE, rnd.uniform(0.9, 1.05))
    for k in range(6):
        t = k / 5
        c = Canvas(-0.6, -0.95, 0.6, 0.55, ppm)
        c.poly(HD.wobble_ellipse(0.0, 0.0, 0.52, 0.42, amp=0.02, seed=seed), fill=hexc("#3a3428"), outline=OUTLINE, width=0.03)   # Erdrand
        c.rect(-0.34, -0.26, 0.34, 0.26, fill=hexc("#07080a"), outline=OUTLINE, width=0.03)
        c.rect(-0.34, 0.12, 0.34, 0.26, fill=hexc("#1c1a18"))
        for j in range(3):
            c.line([(-0.15, 0.2 - j * 0.12), (0.15, 0.2 - j * 0.12)], fill=hexc("#6a5a44"), width=0.022)
        slide = 0.55 * t
        px0, px1 = -0.4, 0.4
        py0, py1 = -0.32 - slide, 0.32 - slide
        c.rect(px0, py0 - 0.04, px1, py0, fill=shade(col, 0.7), outline=OUTLINE, width=0.02)
        c.rect(px0, py0, px1, py1, fill=col, outline=OUTLINE, width=0.035)
        c.rect(px0 + 0.06, py0 + 0.06, px1 - 0.06, py1 - 0.06, outline=alpha(shade(col, 0.7), 220), width=0.012)
        cx, cy = 0.0, (py0 + py1) / 2
        c.line([(cx, cy - 0.12), (cx, cy + 0.14)], fill=alpha(shade(col, 0.6), 230), width=0.02)
        c.line([(cx - 0.08, cy + 0.06), (cx + 0.08, cy + 0.06)], fill=alpha(shade(col, 0.6), 230), width=0.02)
        c.line([(px0 + 0.02, py1 - 0.015), (px1 - 0.02, py1 - 0.015)], fill=alpha(shade(col, 1.35), 220), width=0.014)
        G.lichen(c, px0 + 0.05, py0 + 0.05, px1 - 0.05, py1 - 0.05, 6, seed=seed)
        G.moss(c, px0 + 0.1, py0 + 0.06, 0.06, seed=seed)
        img = c.finish()
        out.append(VC.clean((img, int(round((0 - c.x0) * ppm)), int(round((0 - c.y0) * ppm)))))
    return out


# ------------------------------------------------------------------ Kameras

def gargoyle(ppm, on, seed=0):
    """Wasserspeier auf einer Saeule (die Kamera), neu 24.10.: Stufensockel, kannelierter Schaft mit Ring, Kapitell;
    darauf hockt der Wasserspeier mit gespannten Fledermausfluegeln (Knochenfinger, Flughaut), gekruemmtem Ruecken,
    Krallenfuessen ueber der Kante, Hoernern, langen Ohren, breitem Maul mit Zaehnen; beim Zusehen gluehen die Augen rot."""
    c = Canvas(-0.7, -0.4, 0.7, 1.9, ppm)
    gcol = shade(STONE, 0.86)
    g_l, g_d = shade(gcol, 1.18), shade(gcol, 0.72)
    c.poly([(-0.26, -0.24), (0.26, -0.24), (0.26, -0.12), (-0.26, -0.12)], fill=STONE_D, outline=OUTLINE, width=0.025)
    c.poly([(-0.2, -0.12), (0.2, -0.12), (0.2, -0.04), (-0.2, -0.04)], fill=STONE, outline=OUTLINE, width=0.02)
    c.rect(-0.14, -0.04, 0.14, 0.86, fill=STONE, outline=OUTLINE, width=0.035)
    for k in range(4):
        c.line([(-0.09 + k * 0.06, -0.02), (-0.09 + k * 0.06, 0.84)], fill=alpha(STONE_D, 220), width=0.012)
    c.line([(-0.115, -0.02), (-0.115, 0.84)], fill=alpha((255, 255, 255, 255), 120), width=0.016)
    c.rect(-0.16, 0.4, 0.16, 0.46, fill=STONE_L, outline=OUTLINE, width=0.02)                        # Ring
    c.rect(-0.2, 0.86, 0.2, 0.94, fill=STONE_L, outline=OUTLINE, width=0.03)                         # Kapitell
    c.rect(-0.24, 0.94, 0.24, 1.0, fill=STONE, outline=OUTLINE, width=0.03)
    for k in range(3):
        lx = -0.12 + k * 0.12
        c.poly([(lx - 0.04, 0.86), (lx + 0.04, 0.86), (lx, 0.93)], fill=alpha(STONE_D, 200))
    gy = 1.0
    # Fluegel (hinten): Flughaut mit Knochenfingern
    for sx in (-1, 1):
        mem = [(sx * 0.1, gy + 0.2), (sx * 0.3, gy + 0.62), (sx * 0.55, gy + 0.72), (sx * 0.6, gy + 0.46), (sx * 0.52, gy + 0.3),
               (sx * 0.56, gy + 0.14), (sx * 0.44, gy + 0.2), (sx * 0.36, gy + 0.08), (sx * 0.26, gy + 0.16), (sx * 0.2, gy + 0.06)]
        c.poly(mem, fill=g_d, outline=OUTLINE, width=0.028)
        for tip in ((sx * 0.55, gy + 0.72), (sx * 0.6, gy + 0.46), (sx * 0.56, gy + 0.14)):
            c.line([(sx * 0.12, gy + 0.24), tip], fill=OUTLINE, width=0.035)
            c.line([(sx * 0.12, gy + 0.24), tip], fill=gcol, width=0.018)
        c.ellipse(sx * 0.55, gy + 0.73, 0.02, 0.02, fill=g_l, outline=OUTLINE, width=0.01)          # Daumenkralle
    # Koerper hockend, Ruecken gekruemmt, Fuesse mit Krallen ueber der Kante
    body = [(-0.2, gy + 0.02), (0.2, gy + 0.02), (0.24, gy + 0.18), (0.18, gy + 0.36), (0.0, gy + 0.44), (-0.18, gy + 0.36), (-0.24, gy + 0.18)]
    c.poly(body, fill=gcol, outline=OUTLINE, width=0.03)
    c.poly([(-0.1, gy + 0.06), (0.12, gy + 0.06), (0.14, gy + 0.22), (0.0, gy + 0.3), (-0.12, gy + 0.22)], fill=g_l)   # Bauch heller
    for k in range(3):
        c.line([(-0.12 + k * 0.1, gy + 0.08), (-0.1 + k * 0.1, gy + 0.26)], fill=alpha(g_d, 180), width=0.01)
    for sx in (-1, 1):
        c.ellipse(sx * 0.13, gy + 0.02, 0.07, 0.045, fill=g_l, outline=OUTLINE, width=0.018)         # Fuss
        for k in range(3):
            tx = sx * 0.13 + (k - 1) * 0.035
            c.poly([(tx - 0.015, gy + 0.0), (tx + 0.015, gy + 0.0), (tx + 0.005, gy - 0.06)], fill=g_l, outline=OUTLINE, width=0.01)
        c.line([(sx * 0.22, gy + 0.3), (sx * 0.3, gy + 0.2), (sx * 0.24, gy + 0.08)], fill=OUTLINE, width=0.05)      # Arme auf den Knien
        c.line([(sx * 0.22, gy + 0.3), (sx * 0.3, gy + 0.2), (sx * 0.24, gy + 0.08)], fill=gcol, width=0.028)
    # Kopf mit Hoernern, Ohren, Brauenwulst, Maul
    hy = gy + 0.5
    c.ellipse(0.0, hy, 0.15, 0.12, fill=g_l, outline=OUTLINE, width=0.028)
    for sx in (-1, 1):
        c.poly([(sx * 0.06, hy + 0.09), (sx * 0.16, hy + 0.26), (sx * 0.12, hy + 0.07)], fill=gcol, outline=OUTLINE, width=0.014)   # Hoerner
        c.line([(sx * 0.1, hy + 0.14), (sx * 0.13, hy + 0.2)], fill=alpha(g_d, 200), width=0.008)
        c.poly([(sx * 0.13, hy + 0.02), (sx * 0.24, hy + 0.1), (sx * 0.15, hy - 0.04)], fill=gcol, outline=OUTLINE, width=0.014)   # Ohren
        c.line([(sx * 0.02, hy + 0.05), (sx * 0.1, hy + 0.06)], fill=OUTLINE, width=0.018)              # Brauen
        c.ellipse(sx * 0.055, hy + 0.01, 0.03, 0.024, fill=EYE if on else hexc("#20242c"), outline=OUTLINE, width=0.01)
        if on:
            c.ellipse(sx * 0.055, hy + 0.01, 0.012, 0.01, fill=hexc("#ffd0a0"))
    if on:
        c.glow(0.0, hy, 0.35, EYE, 0.35)
    c.poly([(-0.1, hy - 0.05), (0.1, hy - 0.05), (0.08, hy - 0.1), (-0.08, hy - 0.1)], fill=hexc("#1a1418"), outline=OUTLINE, width=0.014)   # Maul
    for k in range(4):
        tx = -0.07 + k * 0.047
        c.poly([(tx - 0.012, hy - 0.05), (tx + 0.012, hy - 0.05), (tx, hy - 0.085)], fill=hexc("#e8e4d8"))
    c.ellipse(0.0, hy - 0.02, 0.02, 0.012, fill=g_d)                                                      # Nase
    c.line([(-0.12, hy + 0.02), (-0.1, hy + 0.09)], fill=alpha(G.MOON, 150), width=0.012)
    G.lichen(c, -0.12, 0.0, 0.12, 0.8, 8, seed=seed)
    G.moss(c, -0.1, -0.08, 0.08, seed=seed)
    img = c.finish()
    return VC.clean((img, int(round((0 - c.x0) * ppm)), int(round((0 - c.y0) * ppm))))


# ------------------------------------------------------------------ Tueren

DOOR_KIND = {"chapel": "heavy", "coffins": "wood", "well": "wood", "morgue": "heavy", "crematorium": "heavy",
             "lanterns": "wood", "lodge": "wood"}


def door_frames(label, axis, ppm):
    """Villa-Tuermechanik (villa_doors) mit Friedhofspalette: verwittertes graues Eichenholz, schwarzes Eisen."""
    VD.WALNUT = hexc("#5e5248")
    VD.WALNUT_L = hexc("#7e7064")
    VD.WALNUT_D = hexc("#3e3630")
    VD.FRAME = hexc("#4a4440")
    VD.IRON = hexc("#2c2e34")
    VD.IRON_L = hexc("#5a5e68")
    VD.BRASS = hexc("#8a7a5a")
    VD.WALL_T = 0.5
    VD.FACE_Y0 = -0.25
    kind_ = DOOR_KIND.get(label.split("-")[0], "wood")
    lintel = "MEMENTO MORI" if label.startswith("chapel") else ""
    orig = VD.Canvas.text

    def text(self, x, y, s_, size_m, fill, anchor="mm"):                            # Sturz-Inschrift der Villa ersetzen
        if s_ == "HOLLOWMERE":
            if not lintel:
                return
            s_ = lintel
        orig(self, x, y, s_, size_m, fill, anchor)
    VD.Canvas.text = text
    try:
        return [VC.clean(f) for f in VD.door_frames(kind_, axis, ppm)]
    finally:
        VD.Canvas.text = orig


# ------------------------------------------------------------------ alles

def render_all(ctx, ppm, door_slots):
    out = {}
    for key in sorted(ctx.consoles):
        name = key.split("/")[1]
        fn = OVERRIDE.get(key) or BY_NAME.get(name)
        if fn is None:
            print(f"WARN no console art for {key}")
            continue
        out[key] = fn(ppm, sum(ord(ch) for ch in key) % 7)
    for key, fn in SPECIAL.items():
        out[key] = fn(ppm, 1)
    houses = [b[3] for b in ctx.layout.BUILDINGS]
    for vid, (x, y) in ctx.layout.VENTS.items():
        inside = any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in houses)
        frames = VCA.grate_frames(ppm, seed=vid) if inside else slab_frames(ppm, seed=vid)
        out[f"Vent/{vid}"] = frames[0]
        for k, fr in enumerate(frames[1:], 1):
            out[f"Vent/{vid}/{k}"] = fr
    for slot in door_slots:
        side = slot["label"].split("-")[1]
        frames = door_frames(slot["label"], "x" if side in "EW" else "y", ppm)
        out[f"Door/{slot['label']}"] = frames[0]
        for k, fr in enumerate(frames[1:], 1):
            out[f"Door/{slot['label']}/{k}"] = fr
    for i in range(len(ctx.layout.CAMERAS)):
        out[f"Camera/{i}"] = gargoyle(ppm, False, seed=i)
        out[f"Camera/{i}/on"] = gargoyle(ppm, True, seed=i)
    return out


if __name__ == "__main__":
    import sys
    from PIL import Image
    fns = list(dict.fromkeys(list(BY_NAME.values()) + list(SPECIAL.values()) + [oelverteiler]))
    tiles = [fn(160, 1)[0] for fn in fns]
    tiles += [f[0] for f in slab_frames(160, 1)[::2]]
    tiles += [gargoyle(160, False)[0], gargoyle(160, True)[0]]
    tiles += [f[0] for f in door_frames("chapel-N", "y", 160)[::2]] + [f[0] for f in door_frames("coffins-E", "x", 160)[::2]]
    cols = 8
    tw = max(t.width for t in tiles) + 12
    th = max(t.height for t in tiles) + 12
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * tw, rows * th), (70, 90, 80, 255))
    for i, im in enumerate(tiles):
        x, y = (i % cols) * tw + 6, (i // cols) * th + th - 6 - im.height
        sheet.alpha_composite(im, (x, y))
    sheet.save(sys.argv[1] if len(sys.argv) > 1 else "consoles.png")
    print(sheet.size, len(tiles))
