# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_console_art.py - die eigenen Konsolenmotive von Hollowmere Manor (Audit 15.10.: vorher kamen sie aus
# dem Forest, wald_consoles.py). Jede Funktion liefert (PIL RGBA, anker_x_px, anker_y_px) wie WC.Block.result;
# der Anker ist die Konsolenposition, Standlinie = Suedkante der Grundflaeche. Gleicher Strich wie villa_art
# (Umrisse, K-Aufsicht, Licht von Nordwest, warmes Kerzen- und kaltes Geraetelicht).
#
# Motive, nach Konsolenname (villa_consoles._render_all):
#   DivertPower -> distro_box (Verteiler-Flightcase der Crew)      Data/UploadData -> dailies_cart (Bandwagen)
#   FixWiring   -> dimmer_junction (Dimmer-Anschlusskasten)       Garbage/Airlock -> trash_stand (Setmuell)
#   NoOxy       -> damper_wheel (Kaminklappe)                     UnlockManifolds -> puzzle_box
#   Upper/LowerHand -> hand_plate (Messing-Handplatte)             Switch -> fuse_board (Porzellansicherungen)
#   Calibrate   -> dimmer_rack                                    ChartCourse -> star_lectern
#   Weapon      -> bat_window (Fenster mit Laeden)                Shield -> candle_stand (Ward Candles)
#   StartReactor -> ouija_table                                   Surveillance -> video_village (Monitorwagen)
#   AdminTable  -> plan_table (Planungstisch)                     FreeplayLaptop -> clapper_crate
#   SwipeCard   -> callsheet_post (Klemmbrett am Pfosten)          MedScanner -> ringlight_mat (Bodenring)
#   MedBay      -> blood_bench (Kunstblut-Theke)                  CleanFilter -> flue_hatch (Rauchfangklappe)
#   FuelEngine  -> fuel_drum (Fass mit Handpumpe)                 AlignEngine -> small_generator
#   gasCan      -> can_pallet (Kanisterpalette)                   StabilizeSteering -> eyepiece_desk (Okularpult)
#   FixComms    -> old_radio (Dreissigerjahre-Radio)              Vents im Haus -> grate_frames (Heizungsgitter)

import math
import os
import random
import sys

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import wald_consoles as WC                                        # noqa: E402  (Block)
import villa_art as VA                                            # noqa: E402  (Palette, Kerzen, Kabel, Flaschen ...)
from museum_art import Canvas, K, OUTLINE, OUT_W, alpha, hexc, shade  # noqa: E402

WALNUT, WALNUT_D, WALNUT_L = VA.WALNUT, VA.WALNUT_D, VA.WALNUT_L
BRASS, BRASS_D, BRASS_L = VA.BRASS, VA.BRASS_D, VA.BRASS_L
IRON, IRON_L, IRON_D = VA.IRON, VA.IRON_L, VA.IRON_D
MATTE, MATTE_L, MATTE_D, STEEL = VA.MATTE, VA.MATTE_L, VA.MATTE_D, VA.STEEL
GAFFER, CREAM, PARCH, BLOOD, BLOOD_L = VA.GAFFER, VA.CREAM, VA.PARCH, VA.BLOOD, VA.BLOOD_L
WARM, CANDLE = VA.WARM, VA.CANDLE
PORCELAIN = hexc("#e6e2d6")
BRICK = hexc("#8a4a3a")
BRICK_D = shade(BRICK, 0.7)
RED = hexc("#c83a30")
YELLOW = hexc("#e8b830")
BLUE = hexc("#3a6ac8")
PINK = hexc("#d860a8")
GREEN = hexc("#4caf50")
SCREEN = hexc("#1a2430")
SCREEN_L = hexc("#3c6a7a")
TALLY = hexc("#ff3a3a")
PETROL = hexc("#b8322a")


def _label(c, x, y, text, size=0.07, col=OUTLINE, tape=True, w=None):
    """Gaffer-Tape-Etikett mit Schrift (nur ASCII)."""
    w = w or (len(text) * size * 0.62 + 0.08)
    if tape:
        c.rect(x - w / 2, y - size * 0.7, x + w / 2, y + size * 0.7, fill=GAFFER)
        c.line([(x - w / 2, y - size * 0.7), (x + w / 2, y - size * 0.7)], fill=shade(GAFFER, 0.8), width=0.008)
    c.text(x, y, text, size, col)


def _knob(c, x, y, r, ang=0.0, col=MATTE_D):
    c.ellipse(x, y, r, r, fill=col, outline=OUTLINE, width=0.012)
    c.line([(x, y), (x + r * 0.7 * math.cos(ang), y + r * 0.7 * math.sin(ang))], fill=STEEL, width=0.008)


def _socket(c, x, y, col, r=0.035):
    c.ellipse(x, y, r, r, fill=col, outline=OUTLINE, width=0.012)
    c.ellipse(x, y, r * 0.45, r * 0.45, fill=MATTE_D)


def _screws(c, r):
    x0, y0, x1, y1 = r
    for sx, sy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        c.ellipse(sx, sy, 0.012, 0.012, fill=STEEL, outline=OUTLINE, width=0.006)


# ------------------------------------------------------------------ Crew-Technik

def distro_box(ppm, idx=0):
    """Verteilerkasten: schwarzer Flightcase mit Alu-Kanten auf Rollen, Buchsenfeld, Hauptschalter, Kabel."""
    b = WC.Block(-0.42, -0.26, 0.42, 0.26, 1.15 * K, ppm)
    c = b.c
    b.shadow(-0.36, -0.2, 0.36, 0.2)
    for rx in (-0.28, 0.28):
        c.ellipse(rx, -0.18, 0.05, 0.03, fill=MATTE_D, outline=OUTLINE, width=0.012)
    b.box(-0.36, -0.16, 0.36, 0.2, 0.08, 0.9, MATTE_L, MATTE)
    fz = -0.16 + 0.08 * K
    ft = fz + 0.9 * K
    for ex in (-0.36, 0.36):                                      # Alu-Kanten
        c.line([(ex, fz + 0.02), (ex, ft - 0.02)], fill=STEEL, width=0.025)
    c.line([(-0.34, ft - 0.015), (0.34, ft - 0.015)], fill=STEEL, width=0.02)
    _screws(c, (-0.33, fz + 0.04, 0.33, ft - 0.04))
    # Buchsenfeld
    c.rect(-0.3, fz + 0.1, 0.12, ft - 0.08, fill=MATTE_D, outline=OUTLINE, width=0.012)
    cols = (RED, BLUE, YELLOW, PINK, GREEN, STEEL)
    for k in range(6):
        sx = -0.24 + (k % 3) * 0.14
        sy = fz + 0.2 + (k // 3) * 0.14
        _socket(c, sx, sy, cols[(k + idx) % 6])
    _label(c, -0.09, ft - 0.03, "DISTRO " + str(1 + idx % 4), 0.055)
    # Hauptschalter rot mit Glas
    c.rect(0.17, fz + 0.12, 0.31, fz + 0.3, fill=MATTE_L, outline=OUTLINE, width=0.012)
    c.ellipse(0.24, fz + 0.21, 0.045, 0.045, fill=RED, outline=OUTLINE, width=0.012)
    c.ellipse(0.23, fz + 0.225, 0.014, 0.01, fill=hexc("#ff9a90"))
    c.glow(0.24, fz + 0.21, 0.09, RED, 0.35)
    c.ellipse(0.24, fz + 0.38, 0.02, 0.02, fill=GREEN)
    c.glow(0.24, fz + 0.38, 0.05, GREEN, 0.5)
    VA.gaffer(c, 0.14, fz + 0.45, 0.33, fz + 0.47, 0.03)
    # Kabel aus dem Kasten nach rechts auf den Boden
    VA.cable(c, [(0.36, fz + 0.2), (0.52, fz + 0.05), (0.6, -0.22)], seed=idx)
    VA.cable(c, [(0.36, fz + 0.3), (0.5, fz + 0.18), (0.62, -0.1)], seed=idx + 3)
    return b.result()


def dailies_cart(ppm, idx=0):
    """Bandwagen: Holzwagen mit Tonbandgeraet (zwei Spulen), Filmdosen, Klemmbrett."""
    b = WC.Block(-0.45, -0.28, 0.45, 0.3, 1.3 * K, ppm)
    c = b.c
    b.shadow(-0.38, -0.22, 0.38, 0.24)
    for rx in (-0.3, 0.3):
        c.ellipse(rx, -0.2, 0.06, 0.035, fill=MATTE_D, outline=OUTLINE, width=0.012)
    b.box(-0.38, -0.18, 0.38, 0.24, 0.1, 0.7, WALNUT_L, WALNUT)
    fz = -0.18 + 0.1 * K
    WC.planks(c, (-0.35, fz + 0.03, 0.35, fz + 0.7 * K - 0.03), WALNUT)
    zt = -0.18 + 0.8 * K
    # Tonbandgeraet
    b.box(-0.32, -0.1, 0.12, 0.2, 0.8, 0.28, MATTE_L, MATTE)
    dz = -0.1 + 0.8 * K + 0.28 * K
    for sx in (-0.21, 0.01):
        c.ellipse(sx, dz + 0.1, 0.1, 0.075, fill=hexc("#8a6a3a"), outline=OUTLINE, width=0.015)
        c.ellipse(sx, dz + 0.1, 0.06, 0.045, fill=hexc("#5a4224"))
        c.ellipse(sx, dz + 0.1, 0.018, 0.014, fill=STEEL)
    c.line([(-0.21, dz + 0.17), (0.01, dz + 0.17)], fill=hexc("#5a4224"), width=0.012)
    c.rect(-0.3, fz + 0.72 * K + 0.02, -0.26, fz + 0.72 * K + 0.08, fill=hexc("#1e1c18"))
    _knob(c, -0.1, dz + 0.0, 0.025, 0.4)
    c.ellipse(0.06, dz + 0.02, 0.014, 0.014, fill=RED)
    c.glow(0.06, dz + 0.02, 0.04, RED, 0.5)
    # Filmdosen gestapelt rechts
    for k in range(3):
        cz = zt + k * 0.07
        c.ellipse(0.26, cz, 0.11, 0.07, fill=STEEL if k % 2 == 0 else shade(STEEL, 0.85), outline=OUTLINE, width=0.015)
        c.rect(0.15, cz - 0.035, 0.37, cz, fill=shade(STEEL, 0.8))
        c.line([(0.15, cz - 0.035), (0.15, cz)], fill=OUTLINE, width=0.015)
        c.line([(0.37, cz - 0.035), (0.37, cz)], fill=OUTLINE, width=0.015)
    c.ellipse(0.26, zt + 0.14, 0.11, 0.07, fill=STEEL, outline=OUTLINE, width=0.015)
    VA.gaffer(c, 0.17, zt + 0.14, 0.33, zt + 0.15, 0.035)
    _label(c, 0.0, fz + 0.3, "DAILIES", 0.06)
    c.poly([(-0.3, fz + 0.45), (-0.1, fz + 0.47), (-0.12, fz + 0.62), (-0.32, fz + 0.6)], fill=CREAM, outline=OUTLINE, width=0.01)
    for k in range(3):
        c.line([(-0.28, fz + 0.49 + k * 0.035), (-0.14, fz + 0.5 + k * 0.035)], fill=alpha(OUTLINE, 110), width=0.006)
    return b.result()


def dimmer_junction(ppm, idx=0):
    """Dimmer-Anschlusskasten: schwarzer Kasten auf Stativfuss, offener Deckel, vier farbige Buchsen mit Kabeln."""
    b = WC.Block(-0.34, -0.22, 0.34, 0.24, 1.55 * K, ppm)
    c = b.c
    b.shadow(-0.26, -0.16, 0.26, 0.18)
    c.rect(-0.04, -0.16, 0.04, -0.16 + 0.55 * K, fill=MATTE, outline=OUTLINE, width=0.02)
    for lx in (-0.22, 0.22):
        c.line([(lx, -0.14), (0.0, -0.16 + 0.3 * K)], fill=OUTLINE, width=0.04)
        c.line([(lx, -0.14), (0.0, -0.16 + 0.3 * K)], fill=MATTE_L, width=0.022)
    b.box(-0.26, -0.1, 0.26, 0.18, 0.55, 0.62, MATTE_L, MATTE)
    fz = -0.1 + 0.55 * K
    ft = fz + 0.62 * K
    _screws(c, (-0.23, fz + 0.03, 0.23, ft - 0.03))
    cols = (RED, BLUE, YELLOW, PINK)
    for k in range(4):
        sx = -0.18 + k * 0.12
        _socket(c, sx, fz + 0.14, cols[(k + idx) % 4], 0.04)
        VA.cable(c, [(sx, fz + 0.1), (sx + 0.03 * (k - 1.5), fz - 0.1), (sx + 0.08 * (k - 1.5), -0.24)], seed=idx * 7 + k, w=0.022, col=shade(cols[(k + idx) % 4], 0.6))
    _label(c, 0.0, ft - 0.08, "DIMMER " + "ABCDEF"[idx % 6], 0.055)
    # offener Deckel (steht nach hinten hoch) mit Schaltplan innen
    lid_y = 0.18 + 1.17 * K
    c.poly([(-0.26, lid_y - 0.02), (0.26, lid_y - 0.02), (0.24, lid_y + 0.3), (-0.24, lid_y + 0.3)], fill=MATTE_L, outline=OUTLINE, width=0.02)
    c.poly([(-0.2, lid_y + 0.03), (0.2, lid_y + 0.03), (0.19, lid_y + 0.25), (-0.19, lid_y + 0.25)], fill=PARCH)
    for k in range(4):
        c.line([(-0.16, lid_y + 0.07 + k * 0.045), (0.14, lid_y + 0.07 + k * 0.045)], fill=alpha(OUTLINE, 110), width=0.006)
    c.ellipse(0.2, ft - 0.08, 0.016, 0.016, fill=GREEN)
    c.glow(0.2, ft - 0.08, 0.045, GREEN, 0.5)
    return b.result()


def trash_stand(ppm, idx=0):
    """Setmuell: Ringstaender mit schwarzem Sack, Becher und Gaffer-Rollen obendrauf, Etikett."""
    b = WC.Block(-0.32, -0.28, 0.32, 0.28, 1.1 * K, ppm)
    c = b.c
    b.shadow(-0.26, -0.22, 0.26, 0.22)
    for lx in (-0.22, 0.22):
        c.line([(lx, -0.2), (lx * 0.9, -0.2 + 0.85 * K)], fill=OUTLINE, width=0.035)
        c.line([(lx, -0.2), (lx * 0.9, -0.2 + 0.85 * K)], fill=STEEL, width=0.018)
    # Sack
    rnd = random.Random(idx)
    pts = []
    for k in range(14):
        a = math.pi * 2 * k / 14
        r = 0.22 + rnd.uniform(-0.02, 0.03)
        pts.append((r * math.cos(a), -0.02 + 0.4 * K + r * 0.95 * math.sin(a)))
    c.poly(pts, fill=MATTE, outline=OUTLINE, width=0.025)
    c.line([(-0.12, 0.0 + 0.6 * K), (-0.02, 0.1 + 0.6 * K)], fill=MATTE_L, width=0.012)
    c.line([(0.06, -0.05 + 0.5 * K), (0.14, 0.05 + 0.5 * K)], fill=MATTE_L, width=0.012)
    # Ring oben mit Sackrand
    ry = -0.2 + 0.85 * K
    c.ellipse(0.0, ry, 0.23, 0.09, fill=shade(MATTE, 0.8), outline=OUTLINE, width=0.025)
    c.ellipse(0.0, ry, 0.19, 0.065, fill=MATTE_D)
    c.ellipse(0.0, ry + 0.01, 0.23, 0.09, outline=STEEL, width=0.015)
    # Becher und Gaffer-Rolle ragen heraus
    c.poly([(-0.1, ry + 0.02), (-0.02, ry + 0.02), (-0.03, ry + 0.16), (-0.09, ry + 0.16)], fill=CREAM, outline=OUTLINE, width=0.012)
    c.line([(-0.09, ry + 0.1), (-0.03, ry + 0.1)], fill=BLOOD_L, width=0.012)
    c.ellipse(0.09, ry + 0.06, 0.055, 0.04, fill=GAFFER, outline=OUTLINE, width=0.012)
    c.ellipse(0.09, ry + 0.06, 0.022, 0.016, fill=MATTE_D)
    c.ellipse(0.0, ry + 0.09, 0.03, 0.02, fill=BLOOD_L, outline=OUTLINE, width=0.01)
    _label(c, 0.0, -0.1 + 0.45 * K, "SET WASTE", 0.05)
    return b.result()


def dimmer_rack(ppm, idx=0):
    """Dimmer-Rack: schwarzes Standpult mit drei Fadern, Pegelanzeigen und Steckdosenleiste."""
    b = WC.Block(-0.42, -0.26, 0.42, 0.26, 1.35 * K, ppm)
    c = b.c
    b.shadow(-0.36, -0.2, 0.36, 0.2)
    b.box(-0.36, -0.2, 0.36, 0.2, 0, 0.7, MATTE_L, MATTE)
    # schraeges Pult
    zt = -0.2 + 0.7 * K
    c.poly([(-0.36, zt), (0.36, zt), (0.36, zt + 0.4 + 0.1), (-0.36, zt + 0.4 + 0.1)], fill=MATTE_L, outline=OUTLINE, width=0.025)
    c.line([(-0.33, zt + 0.47), (0.33, zt + 0.47)], fill=shade(MATTE_L, 1.3), width=0.015)
    rnd = random.Random(idx)
    for k in range(3):
        fx = -0.24 + k * 0.24
        c.rect(fx - 0.015, zt + 0.08, fx + 0.015, zt + 0.4, fill=MATTE_D, outline=OUTLINE, width=0.01)
        pos = zt + 0.12 + rnd.uniform(0.0, 0.24)
        c.rect(fx - 0.05, pos - 0.025, fx + 0.05, pos + 0.025, fill=STEEL, outline=OUTLINE, width=0.012)
        c.line([(fx - 0.04, pos), (fx + 0.04, pos)], fill=MATTE_D, width=0.008)
        for j in range(5):                                         # Pegel-LEDs
            ly = zt + 0.1 + j * 0.065
            on = ly < pos
            col = (GREEN if j < 3 else YELLOW if j < 4 else RED) if on else MATTE_D
            c.ellipse(fx + 0.07, ly, 0.012, 0.012, fill=col)
            if on:
                c.glow(fx + 0.07, ly, 0.03, col, 0.4)
        _label(c, fx, zt + 0.03, "CH" + str(k + 1), 0.04, tape=False, col=STEEL)
    c.rect(-0.3, -0.2 + 0.2 * K, 0.3, -0.2 + 0.32 * K, fill=MATTE_D, outline=OUTLINE, width=0.012)
    for k in range(4):
        _socket(c, -0.21 + k * 0.14, -0.2 + 0.26 * K, MATTE_L, 0.025)
    VA.cable(c, [(0.36, -0.2 + 0.26 * K), (0.5, -0.2 + 0.1 * K), (0.6, -0.26)], seed=idx)
    VA.gaffer(c, -0.34, zt + 0.02, -0.1, zt + 0.02, 0.035)
    return b.result()


def video_village(ppm, idx=0):
    """Monitorwagen der Regie: Rollwagen mit zwei Monitoren (Kamerabild mit Rauschen), Kopfhoerer, Kaffee."""
    b = WC.Block(-0.5, -0.3, 0.5, 0.3, 1.6 * K, ppm)
    c = b.c
    b.shadow(-0.42, -0.24, 0.42, 0.24)
    for rx in (-0.34, 0.34):
        c.ellipse(rx, -0.22, 0.05, 0.03, fill=MATTE_D, outline=OUTLINE, width=0.012)
    b.box(-0.42, -0.18, 0.42, 0.24, 0.08, 0.75, MATTE_L, MATTE)
    fz = -0.18 + 0.08 * K
    c.rect(-0.38, fz + 0.1, -0.06, fz + 0.3, fill=MATTE_D, outline=OUTLINE, width=0.012)   # Schublade
    c.line([(-0.3, fz + 0.2), (-0.14, fz + 0.2)], fill=STEEL, width=0.012)
    zt = -0.18 + 0.83 * K
    for k, mx in enumerate((-0.2, 0.2)):
        c.rect(mx - 0.19, zt + 0.05, mx + 0.19, zt + 0.36, fill=MATTE, outline=OUTLINE, width=0.02)
        c.rect(mx - 0.16, zt + 0.08, mx + 0.16, zt + 0.33, fill=SCREEN)
        c.glow(mx, zt + 0.2, 0.2, SCREEN_L, 0.4)
        rnd = random.Random(idx * 3 + k)
        for _ in range(26):                                        # Rauschen
            c.ellipse(mx + rnd.uniform(-0.15, 0.15), zt + rnd.uniform(0.09, 0.32), 0.006, 0.004, fill=alpha(SCREEN_L, rnd.randint(60, 180)))
        c.rect(mx - 0.14, zt + 0.1, mx - 0.02, zt + 0.13, fill=alpha(SCREEN_L, 150))
        c.line([(mx - 0.13, zt + 0.115), (mx - 0.04, zt + 0.115)], fill=hexc("#dfe8f0"), width=0.01)
        c.ellipse(mx + 0.13, zt + 0.3, 0.012, 0.012, fill=TALLY)
        c.rect(mx - 0.03, zt + 0.0, mx + 0.03, zt + 0.05, fill=MATTE)
    _label(c, 0.0, zt - 0.02, "VIDEO VILLAGE", 0.045)
    # Kopfhoerer und Kaffeebecher auf der Ablage
    c.ellipse(0.32, zt + 0.42, 0.07, 0.05, outline=OUTLINE, width=0.03)
    c.ellipse(0.32, zt + 0.42, 0.07, 0.05, outline=MATTE_L, width=0.015)
    c.ellipse(-0.36, zt + 0.42, 0.03, 0.03, fill=CREAM, outline=OUTLINE, width=0.012)
    c.ellipse(-0.36, zt + 0.42, 0.018, 0.012, fill=hexc("#5a3a1a"))
    VA.cable(c, [(0.42, fz + 0.3), (0.55, fz + 0.1), (0.62, -0.28)], seed=idx)
    return b.result()


def clapper_crate(ppm, idx=0):
    """Freeplay: Regieklappe lehnt an einer Requisitenkiste, Kaffeebecher daneben."""
    b = WC.Block(-0.34, -0.26, 0.34, 0.26, 1.0 * K, ppm)
    c = b.c
    b.shadow(-0.26, -0.2, 0.26, 0.18)
    b.box(-0.26, -0.18, 0.26, 0.18, 0, 0.5, WALNUT_L, WALNUT)
    fz = -0.18
    c.line([(-0.23, fz + 0.04), (0.23, fz + 0.5 * K - 0.04)], fill=WALNUT_D, width=0.025)
    c.line([(0.23, fz + 0.04), (-0.23, fz + 0.5 * K - 0.04)], fill=WALNUT_D, width=0.025)
    _label(c, 0.0, fz + 0.5 * K - 0.08, "PROPS", 0.05, tape=False, col=shade(WALNUT_D, 0.7))
    zt = fz + 0.5 * K + 0.18 * 0.5
    # Klappe
    c.poly([(-0.2, zt), (0.14, zt), (0.16, zt + 0.26), (-0.18, zt + 0.28)], fill=hexc("#20222a"), outline=OUTLINE, width=0.018)
    for k in range(3):
        c.line([(-0.16, zt + 0.06 + k * 0.06), (0.12, zt + 0.055 + k * 0.06)], fill=hexc("#d8d8d8"), width=0.007)
    stick = [(-0.21, zt + 0.29), (0.15, zt + 0.27), (0.19, zt + 0.36), (-0.17, zt + 0.38)]
    c.poly(stick, fill=hexc("#f0f0f0"), outline=OUTLINE, width=0.015)
    for k in range(4):
        x = -0.18 + k * 0.085
        c.poly([(x, zt + 0.29), (x + 0.04, zt + 0.288), (x + 0.055, zt + 0.37), (x + 0.015, zt + 0.375)], fill=hexc("#18181c"))
    c.ellipse(0.24, zt + 0.05, 0.035, 0.03, fill=CREAM, outline=OUTLINE, width=0.012)
    c.ellipse(0.24, zt + 0.05, 0.02, 0.014, fill=hexc("#5a3a1a"))
    return b.result()


def callsheet_post(ppm, idx=0):
    """Call Sheet: Klemmbrett am Haken eines Holzpfostens, Stift an der Schnur, Zettel darunter."""
    b = WC.Block(-0.28, -0.2, 0.28, 0.22, 1.6 * K, ppm)
    c = b.c
    b.shadow(-0.12, -0.14, 0.12, 0.12)
    b.box(-0.08, -0.14, 0.08, 0.1, 0, 1.5, WALNUT_L, WALNUT)
    top = -0.14 + 1.5 * K
    c.line([(-0.05, -0.1), (-0.05, top - 0.05)], fill=WALNUT_D, width=0.01)
    # Haken und Klemmbrett
    c.ellipse(0.0, top - 0.1, 0.02, 0.02, fill=BRASS, outline=OUTLINE, width=0.01)
    bx0, by0, bx1, by1 = -0.2, top - 0.72, 0.2, top - 0.14
    c.poly([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], fill=hexc("#8a6a44"), outline=OUTLINE, width=0.018)
    c.poly([(bx0 + 0.03, by0 + 0.03), (bx1 - 0.03, by0 + 0.03), (bx1 - 0.03, by1 - 0.08), (bx0 + 0.03, by1 - 0.08)], fill=CREAM, outline=shade(CREAM, 0.7), width=0.008)
    c.rect(-0.07, by1 - 0.12, 0.07, by1 - 0.03, fill=STEEL, outline=OUTLINE, width=0.012)
    c.text(0.0, by1 - 0.17, "CALL SHEET", 0.04, OUTLINE)
    for k in range(6):
        ly = by1 - 0.24 - k * 0.055
        c.line([(bx0 + 0.06, ly), (bx1 - 0.06, ly)], fill=alpha(OUTLINE, 120), width=0.006)
        c.ellipse(bx0 + 0.07, ly, 0.012, 0.012, outline=OUTLINE, width=0.006)
    c.line([(bx0 + 0.06, by1 - 0.295), (bx0 + 0.085, by1 - 0.28)], fill=RED, width=0.008)
    c.line([(bx0 + 0.085, by1 - 0.28), (bx0 + 0.1, by1 - 0.31)], fill=RED, width=0.008)
    # Stift an Schnur
    c.line([(bx1, by1 - 0.05), (bx1 + 0.05, by0 + 0.1), (bx1 + 0.02, by0 - 0.05)], fill=alpha(OUTLINE, 160), width=0.006)
    c.line([(bx1 + 0.02, by0 - 0.05), (bx1 + 0.06, by0 - 0.2)], fill=BLUE, width=0.02)
    c.line([(bx1 + 0.02, by0 - 0.05), (bx1 + 0.06, by0 - 0.2)], fill=OUTLINE, width=0.028)
    c.line([(bx1 + 0.025, by0 - 0.06), (bx1 + 0.055, by0 - 0.19)], fill=BLUE, width=0.014)
    VA.gaffer(c, -0.08, top - 0.9, 0.08, top - 0.9, 0.03)
    return b.result()


def plan_table(ppm, idx=0):
    """Planungstisch: Zeichentisch mit dem Grundriss des Hauses, Nadeln, Lineal, Lampe, Kaffee."""
    b = WC.Block(-0.58, -0.36, 0.58, 0.36, 1.1 * K, ppm)
    c = b.c
    b.shadow(-0.5, -0.3, 0.5, 0.3)
    for lx in (-0.44, 0.44):
        c.rect(lx - 0.03, -0.3, lx + 0.03, -0.3 + 0.78 * K, fill=WALNUT, outline=OUTLINE, width=0.015)
    b.box(-0.5, -0.3, 0.5, 0.3, 0.78, 0.05, WALNUT_L, WALNUT)
    zt = -0.3 + 0.83 * K
    # Plan: aufgerolltes Pergament mit Grundriss
    c.poly([(-0.44, zt + 0.05), (0.36, zt + 0.03), (0.38, zt + 0.5), (-0.42, zt + 0.52)], fill=PARCH, outline=OUTLINE, width=0.012)
    rnd = random.Random(idx)
    lines = [((-0.38, zt + 0.1), (0.3, zt + 0.1)), ((-0.38, zt + 0.1), (-0.38, zt + 0.46)), ((0.3, zt + 0.1), (0.3, zt + 0.46)),
             ((-0.38, zt + 0.46), (0.3, zt + 0.46)), ((-0.1, zt + 0.1), (-0.1, zt + 0.46)), ((0.1, zt + 0.1), (0.1, zt + 0.28)),
             ((-0.38, zt + 0.28), (-0.1, zt + 0.28)), ((0.1, zt + 0.28), (0.3, zt + 0.28))]
    for a, bb in lines:
        c.line([a, bb], fill=hexc("#3a3a60"), width=0.008)
    for k in range(5):
        px, py = rnd.uniform(-0.34, 0.26), rnd.uniform(zt + 0.14, zt + 0.42)
        c.ellipse(px, py, 0.014, 0.014, fill=RED if k % 2 else GREEN, outline=OUTLINE, width=0.006)
    c.text(-0.04, zt + 0.56, "HOLLOWMERE", 0.045, hexc("#3a3a60"))
    c.rect(0.32, zt + 0.08, 0.46, zt + 0.42, fill=shade(PARCH, 0.9), outline=OUTLINE, width=0.012)      # Rolle
    c.line([(0.34, zt + 0.1), (0.34, zt + 0.4)], fill=shade(PARCH, 1.1), width=0.012)
    c.line([(-0.4, zt + 0.14), (-0.12, zt + 0.12)], fill=STEEL, width=0.018)                               # Lineal
    VA.banker_lamp(c, 0.42, zt + 0.44, 0.75)
    c.ellipse(-0.46, zt + 0.48, 0.03, 0.03, fill=CREAM, outline=OUTLINE, width=0.012)
    c.ellipse(-0.46, zt + 0.48, 0.018, 0.012, fill=hexc("#5a3a1a"))
    return b.result()


def ringlight_mat(ppm, idx=0):
    """Maske: runde Bodenmatte mit Ringlicht (liegt unter dem Spieler), Kabel zum Rand."""
    c = Canvas(-0.75, -0.62, 0.75, 0.62, ppm)
    c.ellipse(0.0, 0.0, 0.62, 0.46, fill=hexc("#2a2228"), outline=OUTLINE, width=0.03)
    c.ellipse(0.0, 0.0, 0.52, 0.38, outline=hexc("#4a3a44"), width=0.02)
    c.glow(0.0, 0.0, 0.5, WARM, 0.25)
    n = 14
    for k in range(n):
        a = math.pi * 2 * k / n
        lx, ly = 0.5 * math.cos(a), 0.36 * math.sin(a)
        c.ellipse(lx, ly, 0.035, 0.03, fill=hexc("#fff0c8"), outline=OUTLINE, width=0.012)
        c.glow(lx, ly, 0.07, WARM, 0.5)
    c.text(0.0, -0.3, "MAKEUP", 0.05, hexc("#6a5a64"))
    VA.cable(c, [(0.58, 0.1), (0.68, 0.2), (0.72, 0.4)], seed=idx)
    img = c.finish()
    return img, int(round((0 - c.x0) * ppm)), int(round((0 - c.y0) * ppm))


def blood_bench(ppm, idx=0):
    """Kunstblut-Theke: Tisch mit Flaschen, Trichter, Schuessel Blut, Handtuch, Rezeptzettel."""
    b = WC.Block(-0.52, -0.28, 0.52, 0.28, 1.15 * K, ppm)
    c = b.c
    b.shadow(-0.45, -0.22, 0.45, 0.22)
    b.box(-0.45, -0.22, 0.45, 0.22, 0, 0.8, shade(CREAM, 0.8), shade(CREAM, 0.65))
    fz = -0.22
    c.rect(-0.4, fz + 0.2 * K, -0.1, fz + 0.6 * K, outline=shade(CREAM, 0.5), width=0.012)
    c.ellipse(-0.25, fz + 0.4 * K, 0.02, 0.016, fill=BRASS)
    zt = fz + 0.8 * K
    VA.bottle(c, -0.36, zt + 0.02, 0.28, BLOOD, CREAM)
    VA.bottle(c, -0.26, zt + 0.0, 0.22, hexc("#c8402a"), None, 0.025)
    VA.bottle(c, -0.18, zt + 0.03, 0.3, hexc("#7a4a2a"), PARCH)
    # Schuessel mit Blut
    c.ellipse(0.08, zt + 0.1, 0.13, 0.08, fill=shade(CREAM, 0.9), outline=OUTLINE, width=0.015)
    c.ellipse(0.08, zt + 0.11, 0.1, 0.055, fill=BLOOD)
    c.ellipse(0.05, zt + 0.12, 0.03, 0.015, fill=BLOOD_L)
    VA.blood_drips(c, 0.2, zt + 0.06, 3, 0.12, seed=idx)
    # Trichter und Loeffel
    c.poly([(0.3, zt + 0.3), (0.42, zt + 0.3), (0.37, zt + 0.16), (0.35, zt + 0.16)], fill=STEEL, outline=OUTLINE, width=0.012)
    c.rect(0.35, zt + 0.08, 0.37, zt + 0.16, fill=STEEL, outline=OUTLINE, width=0.01)
    c.line([(0.16, zt + 0.26), (0.26, zt + 0.12)], fill=STEEL, width=0.015)
    c.ellipse(0.27, zt + 0.1, 0.025, 0.018, fill=BLOOD, outline=OUTLINE, width=0.01)
    # Handtuch und Zettel
    c.poly([(0.22, fz + 0.45), (0.42, fz + 0.45), (0.44, fz + 0.2), (0.24, fz + 0.2)], fill=hexc("#d8d0c4"), outline=OUTLINE, width=0.012)
    VA.blood_pool(c, 0.33, fz + 0.3, 0.05, 0.03, seed=idx, a=200)
    c.poly([(-0.42, fz + 0.5), (-0.24, fz + 0.52), (-0.25, fz + 0.66), (-0.43, fz + 0.64)], fill=CREAM, outline=OUTLINE, width=0.01)
    c.text(-0.335, fz + 0.58, "RECIPE", 0.035, OUTLINE)
    return b.result()


def flue_hatch(ppm, idx=0):
    """Rauchfangklappe: Ziegelstumpf mit eiserner Klappe und Ring, Russfahne, Kaminbesen daneben."""
    b = WC.Block(-0.38, -0.24, 0.38, 0.26, 1.4 * K, ppm)
    c = b.c
    b.shadow(-0.3, -0.18, 0.3, 0.2)
    b.box(-0.3, -0.18, 0.3, 0.2, 0, 1.2, shade(BRICK, 1.1), BRICK)
    fz = -0.18
    ft = fz + 1.2 * K
    # Ziegelfugen
    y = fz + 0.08
    row = 0
    while y < ft - 0.05:
        c.line([(-0.28, y), (0.28, y)], fill=BRICK_D, width=0.01)
        x = -0.28 + (0.09 if row % 2 else 0.0)
        while x < 0.28:
            c.line([(x, y), (x, min(ft - 0.03, y + 0.08))], fill=BRICK_D, width=0.008)
            x += 0.18
        y += 0.085
        row += 1
    # Klappe
    c.rect(-0.17, fz + 0.2, 0.17, fz + 0.52, fill=IRON, outline=OUTLINE, width=0.02)
    c.rect(-0.14, fz + 0.23, 0.14, fz + 0.49, outline=IRON_D, width=0.01)
    for sx, sy in ((-0.14, fz + 0.26), (0.14, fz + 0.26), (-0.14, fz + 0.46), (0.14, fz + 0.46)):
        c.ellipse(sx, sy, 0.012, 0.012, fill=IRON_L, outline=OUTLINE, width=0.006)
    c.ellipse(0.0, fz + 0.33, 0.05, 0.045, outline=OUTLINE, width=0.04)
    c.ellipse(0.0, fz + 0.33, 0.05, 0.045, outline=IRON_L, width=0.018)
    # Russ
    c.poly([(-0.1, fz + 0.52), (0.1, fz + 0.52), (0.16, ft - 0.02), (-0.16, ft - 0.02)], fill=alpha((20, 18, 18, 255), 140))
    for k in range(5):
        c.ellipse(-0.06 + k * 0.03, fz + 0.14 - (k % 2) * 0.03, 0.025, 0.012, fill=alpha((20, 18, 18, 255), 160))
    # Besen rechts
    c.line([(0.36, -0.2), (0.42, ft + 0.3)], fill=OUTLINE, width=0.035)
    c.line([(0.36, -0.2), (0.42, ft + 0.3)], fill=WALNUT_L, width=0.02)
    c.ellipse(0.43, ft + 0.36, 0.08, 0.06, fill=hexc("#2a2826"), outline=OUTLINE, width=0.015)
    for k in range(7):
        a = math.pi * k / 6
        c.line([(0.43, ft + 0.36), (0.43 + 0.1 * math.cos(a), ft + 0.36 + 0.08 * math.sin(a))], fill=hexc("#3a3836"), width=0.008)
    return b.result()


def fuel_drum(ppm, idx=0):
    """Treibstoff: rotes Fass mit Handpumpe und Schlauch, Kanister daneben, Warnschild."""
    b = WC.Block(-0.38, -0.3, 0.38, 0.3, 1.25 * K, ppm)
    c = b.c
    b.shadow(-0.3, -0.24, 0.3, 0.2)
    b.cyl(-0.08, -0.1, 0.24, 0, 0.95, shade(PETROL, 1.15), PETROL, ry=0.13)
    fz = -0.1
    for ry in (0.25, 0.6):
        c.ellipse(-0.08, fz + ry * K, 0.24, 0.13, outline=shade(PETROL, 0.6), width=0.015)
    c.line([(-0.28, fz + 0.1), (-0.28, fz + 0.9 * K)], fill=shade(PETROL, 1.3), width=0.015)
    zt = fz + 0.95 * K
    c.text(-0.08, fz + 0.42 * K, "FUEL", 0.07, hexc("#f0e0d0"))
    # Handpumpe
    c.rect(-0.03, zt - 0.02, 0.03, zt + 0.3, fill=STEEL, outline=OUTLINE, width=0.015)
    c.line([(-0.1, zt + 0.3), (0.16, zt + 0.42)], fill=OUTLINE, width=0.04)
    c.line([(-0.1, zt + 0.3), (0.16, zt + 0.42)], fill=STEEL, width=0.022)
    c.ellipse(0.16, zt + 0.42, 0.025, 0.02, fill=MATTE_D, outline=OUTLINE, width=0.01)
    VA.cable(c, [(0.0, zt + 0.1), (0.2, zt + 0.02), (0.32, fz + 0.2 * K), (0.3, -0.26)], seed=idx, w=0.03, col=hexc("#3a3a3a"))
    # Kanister rechts vorn
    b.box(0.14, -0.3, 0.36, -0.14, 0, 0.5, shade(hexc("#4a6a3a"), 1.2), hexc("#4a6a3a"))
    c.rect(0.19, -0.3 + 0.15 * K, 0.31, -0.3 + 0.35 * K, outline=OUTLINE, width=0.01)
    c.line([(0.2, -0.3 + 0.52 * K + 0.03), (0.3, -0.3 + 0.52 * K + 0.03)], fill=OUTLINE, width=0.02)
    _label(c, 0.25, -0.3 + 0.25 * K, "10 L", 0.04)
    return b.result()


def coal_bin(ppm, idx=0):
    """Kuechen-Variante der Treibstoffkonsole (User 24.10.: das Fass wirkte in der Kueche fehl am Platz): Kohlenkasten
    aus Gusseisen mit offenem Deckel, Kohlebrocken darin und davor, Kohlenschaufel angelehnt, kleiner Eimer, Russ."""
    b = WC.Block(-0.38, -0.3, 0.38, 0.3, 1.1 * K, ppm)
    c = b.c
    b.shadow(-0.3, -0.24, 0.3, 0.2)
    coal = hexc("#1e2026")
    coal_l = hexc("#3a3e48")
    b.box(-0.3, -0.22, 0.14, 0.18, 0, 0.55, IRON_L, IRON)
    fz = -0.22
    ft = fz + 0.55 * K
    c.rect(-0.26, fz + 0.06, 0.1, ft - 0.06, outline=IRON_D, width=0.015)                               # Fuellung
    c.line([(-0.2, fz + 0.1), (-0.2, ft - 0.1)], fill=IRON_L, width=0.01)
    for sx, sy in ((-0.27, fz + 0.05), (0.11, fz + 0.05), (-0.27, ft - 0.05), (0.11, ft - 0.05)):
        c.ellipse(sx, sy, 0.012, 0.012, fill=STEEL, outline=OUTLINE, width=0.006)
    _label(c, -0.08, fz + 0.5 * K * 0.55, "COAL", 0.055, col=PORCELAIN, tape=False)
    # offener Deckel (nach hinten geklappt) und Kohle im Kasten
    zt = -0.22 + 0.55 * K
    c.rect(-0.28, zt + 0.02, 0.12, 0.18 + 0.55 * K, fill=coal)
    rs = random.Random(idx)
    for _ in range(14):
        x, y = rs.uniform(-0.25, 0.09), rs.uniform(zt + 0.05, 0.16 + 0.55 * K)
        c.poly([(x - 0.035, y), (x - 0.01, y + 0.03), (x + 0.03, y + 0.02), (x + 0.035, y - 0.015), (x, y - 0.03)], fill=coal_l if rs.random() < 0.5 else coal, outline=OUTLINE, width=0.008)
        c.ellipse(x - 0.012, y + 0.01, 0.008, 0.005, fill=alpha((255, 255, 255, 255), 90))
    c.poly([(-0.3, 0.18 + 0.55 * K), (0.14, 0.18 + 0.55 * K), (0.12, 0.18 + 0.55 * K + 0.3), (-0.28, 0.18 + 0.55 * K + 0.3)], fill=IRON_L, outline=OUTLINE, width=0.02)   # Deckel
    c.line([(-0.24, 0.18 + 0.55 * K + 0.26), (0.08, 0.18 + 0.55 * K + 0.26)], fill=IRON_D, width=0.012)
    c.ellipse(-0.08, 0.18 + 0.55 * K + 0.15, 0.03, 0.02, fill=BRASS, outline=OUTLINE, width=0.01)
    # Kohlenschaufel angelehnt (rechts), Brocken am Boden, Eimer
    c.line([(0.2, -0.24), (0.3, 0.42)], fill=OUTLINE, width=0.04)
    c.line([(0.2, -0.24), (0.3, 0.42)], fill=WALNUT, width=0.022)
    c.poly([(0.1, -0.26), (0.3, -0.24), (0.3, -0.1), (0.12, -0.08)], fill=STEEL, outline=OUTLINE, width=0.015)
    c.line([(0.14, -0.22), (0.27, -0.21)], fill=alpha((255, 255, 255, 255), 120), width=0.008)
    c.ellipse(0.3, 0.42, 0.03, 0.02, fill=WALNUT_D, outline=OUTLINE, width=0.01)
    for x, y in ((-0.34, -0.27), (-0.1, -0.29), (0.02, -0.26)):
        c.poly([(x - 0.03, y), (x - 0.01, y + 0.025), (x + 0.025, y + 0.015), (x + 0.03, y - 0.012), (x, y - 0.025)], fill=coal, outline=OUTLINE, width=0.008)
    b.cyl(0.3, 0.1, 0.09, 0, 0.22, IRON_L, IRON, ry=0.045)                                                  # Eimer
    c.line([(0.21, 0.1 + 0.2 * K), (0.3, 0.1 + 0.2 * K + 0.1), (0.39, 0.1 + 0.2 * K)], fill=OUTLINE, width=0.025)
    c.line([(0.21, 0.1 + 0.2 * K), (0.3, 0.1 + 0.2 * K + 0.1), (0.39, 0.1 + 0.2 * K)], fill=IRON_L, width=0.012)
    c.ellipse(0.3, 0.1 + 0.22 * K, 0.07, 0.03, fill=coal)
    c.ellipse(-0.05, -0.2, 0.12, 0.03, fill=alpha((0, 0, 0, 255), 70))                                        # Russ
    return b.result()


def small_generator(ppm, idx=0):
    """Tragbares Aggregat der Crew: gelb-schwarz, Drehzahlmesser, Starterseil, Auspuff mit Rauch, Kanister."""
    b = WC.Block(-0.48, -0.3, 0.48, 0.3, 1.1 * K, ppm)
    c = b.c
    b.shadow(-0.4, -0.24, 0.4, 0.24)
    for lx in (-0.34, 0.34):
        c.line([(lx, -0.24), (lx, -0.24 + 0.12 * K)], fill=OUTLINE, width=0.03)
    b.box(-0.4, -0.2, 0.4, 0.24, 0.12, 0.6, shade(YELLOW, 1.1), shade(YELLOW, 0.85))
    fz = -0.2 + 0.12 * K
    ft = fz + 0.6 * K
    c.rect(-0.36, fz + 0.03, -0.06, ft - 0.03, fill=MATTE, outline=OUTLINE, width=0.012)   # Motorblock-Gitter
    for k in range(5):
        c.line([(-0.34, fz + 0.06 + k * 0.05), (-0.08, fz + 0.06 + k * 0.05)], fill=MATTE_L, width=0.008)
    # Drehzahlmesser und Schalter
    c.ellipse(0.16, fz + 0.18, 0.08, 0.08, fill=CREAM, outline=OUTLINE, width=0.015)
    c.line([(0.16, fz + 0.18), (0.16 + 0.055 * math.cos(2.4), fz + 0.18 + 0.055 * math.sin(2.4))], fill=RED, width=0.01)
    c.ellipse(0.16, fz + 0.18, 0.012, 0.012, fill=OUTLINE)
    c.line([(0.1, fz + 0.24), (0.22, fz + 0.24)], fill=alpha(OUTLINE, 120), width=0.006)
    _knob(c, 0.32, fz + 0.1, 0.03, 1.0, RED)
    _knob(c, 0.32, fz + 0.26, 0.025, -0.5)
    # Griff oben, Auspuff, Starterseil
    zt = -0.2 + 0.72 * K
    c.rect(-0.3, zt + 0.08, 0.3, zt + 0.13, fill=MATTE, outline=OUTLINE, width=0.015)
    c.rect(-0.28, zt + 0.0, -0.24, zt + 0.1, fill=MATTE)
    c.rect(0.24, zt + 0.0, 0.28, zt + 0.1, fill=MATTE)
    c.rect(0.3, zt - 0.02, 0.48, zt + 0.04, fill=STEEL, outline=OUTLINE, width=0.012)
    VA.smoke(c, 0.47, zt + 0.06, seed=idx, h=0.3)
    c.line([(-0.2, fz + 0.3), (-0.5, fz + 0.1)], fill=hexc("#d8c890"), width=0.012)
    c.rect(-0.54, fz + 0.04, -0.48, fz + 0.14, fill=MATTE, outline=OUTLINE, width=0.01)
    VA.gaffer(c, -0.1, ft - 0.05, 0.12, ft - 0.05, 0.03)
    _label(c, 0.02, fz + 0.4, "GEN " + str(1 + idx % 2), 0.045, tape=False, col=MATTE)
    return b.result()


def can_pallet(ppm, idx=0):
    """Kanisterpalette: Holzpalette mit vier Kanistern (gruen und rot), Gaffer-Etikett."""
    b = WC.Block(-0.5, -0.32, 0.5, 0.32, 0.9 * K, ppm)
    c = b.c
    b.shadow(-0.44, -0.26, 0.44, 0.26)
    b.box(-0.44, -0.26, 0.44, 0.26, 0, 0.12, WALNUT_L, WALNUT)
    fz = -0.26
    for k in range(5):
        c.line([(-0.4 + k * 0.2, fz + 0.12 * K + 0.03), (-0.4 + k * 0.2, fz + 0.12 * K + 0.5)], fill=WALNUT_D, width=0.01)
    cols = (hexc("#4a6a3a"), PETROL, hexc("#4a6a3a"), hexc("#6a6a3a"))
    for k, (cx, cy) in enumerate(((-0.3, 0.02), (-0.06, 0.04), (0.18, 0.02), (0.36, -0.1))):
        col = cols[(k + idx) % 4]
        b.box(cx - 0.11, cy - 0.12, cx + 0.11, cy + 0.08, 0.12, 0.5, shade(col, 1.2), col)
        gz = cy - 0.12 + 0.12 * K
        c.rect(cx - 0.07, gz + 0.12, cx + 0.07, gz + 0.24, outline=OUTLINE, width=0.01)
        c.line([(cx - 0.05, gz + 0.5 * K + 0.03), (cx + 0.05, gz + 0.5 * K + 0.03)], fill=OUTLINE, width=0.02)
        c.ellipse(cx + 0.07, gz + 0.5 * K + 0.01, 0.02, 0.014, fill=MATTE, outline=OUTLINE, width=0.008)
    _label(c, -0.1, fz + 0.05, "PETROL", 0.045)
    return b.result()


# ------------------------------------------------------------------ Villa

def damper_wheel(ppm, idx=0):
    """Kaminklappe: gusseisernes Rohr aus dem Boden mit grossem Handrad, Messingschild, Rostspuren."""
    b = WC.Block(-0.3, -0.24, 0.3, 0.24, 1.45 * K, ppm)
    c = b.c
    b.shadow(-0.16, -0.18, 0.16, 0.14)
    b.cyl(0.0, -0.1, 0.1, 0, 1.1, IRON_L, IRON, ry=0.05)
    fz = -0.1
    for ry in (0.2, 0.9):
        c.ellipse(0.0, fz + ry * K, 0.12, 0.06, fill=IRON_L, outline=OUTLINE, width=0.015)   # Flansche
    c.line([(-0.07, fz + 0.1), (-0.07, fz + 1.0 * K)], fill=shade(IRON, 1.35), width=0.012)
    hy = fz + 0.62 * K
    # Handrad: Ellipse mit Speichen
    c.ellipse(0.0, hy, 0.22, 0.2, outline=OUTLINE, width=0.06)
    c.ellipse(0.0, hy, 0.22, 0.2, outline=IRON_L, width=0.03)
    for k in range(6):
        a = math.pi * k / 3 + idx * 0.3
        c.line([(0.0, hy), (0.2 * math.cos(a), hy + 0.18 * math.sin(a))], fill=OUTLINE, width=0.03)
        c.line([(0.0, hy), (0.2 * math.cos(a), hy + 0.18 * math.sin(a))], fill=IRON_L, width=0.014)
    c.ellipse(0.0, hy, 0.05, 0.05, fill=IRON, outline=OUTLINE, width=0.015)
    c.ellipse(0.0, hy, 0.02, 0.02, fill=BRASS)
    # Messingschild
    c.rect(-0.1, fz + 0.3 * K, 0.1, fz + 0.3 * K + 0.08, fill=BRASS, outline=OUTLINE, width=0.012)
    c.text(0.0, fz + 0.3 * K + 0.04, "FLUE", 0.035, BRASS_D)
    for k in range(3):                                                                            # Rost
        c.ellipse(0.06 + k * 0.01, fz + 0.15 + k * 0.04, 0.025, 0.015, fill=alpha(hexc("#8a4a2a"), 150))
    return b.result()


def puzzle_box(ppm, idx=0):
    """Puzzle-Box: Nussholz-Saeule mit kunstvoller Holzbox (Intarsien, Messingschloss), Kerze daneben."""
    b = WC.Block(-0.3, -0.24, 0.3, 0.24, 1.2 * K, ppm)
    c = b.c
    b.shadow(-0.18, -0.18, 0.18, 0.14)
    b.box(-0.18, -0.16, 0.18, 0.12, 0, 0.85, WALNUT_L, WALNUT)
    b.box(-0.2, -0.18, 0.2, 0.14, 0.85, 0.05, WALNUT_L, WALNUT_D)
    fz = -0.16
    c.rect(-0.12, fz + 0.15, 0.12, fz + 0.75 * K, outline=WALNUT_D, width=0.012)
    zt = -0.18 + 0.9 * K
    bx0, by0, bx1, by1 = -0.14, zt + 0.02, 0.14, zt + 0.2
    b.box(bx0, -0.1, bx1, 0.06, 0.9, 0.22, shade(hexc("#9a6a3a"), 1.1), hexc("#7a4a2a"))
    fzb = -0.1 + 0.9 * K
    # Intarsien: Rauten und Mittelstern
    for k in range(3):
        cx = -0.08 + k * 0.08
        c.poly([(cx, fzb + 0.03), (cx + 0.025, fzb + 0.06), (cx, fzb + 0.09), (cx - 0.025, fzb + 0.06)], fill=BRASS_L, outline=BRASS_D, width=0.006)
    top = 0.06 + 1.12 * K
    c.ellipse(0.0, top - 0.06, 0.05, 0.03, outline=BRASS_L, width=0.008)
    c.ellipse(0.0, top - 0.06, 0.02, 0.012, fill=BRASS)
    c.rect(-0.02, fzb + 0.05, 0.02, fzb + 0.1, fill=BRASS, outline=OUTLINE, width=0.008)
    c.ellipse(0.0, fzb + 0.075, 0.006, 0.006, fill=OUTLINE)
    VA.candle(c, 0.24, zt - 0.02, 0.14, True, seed=idx)
    VA.cobweb(c, -0.2, zt + 0.2, 0.1, 1, -1, seed=idx)
    return b.result()


def hand_plate(ppm, idx=0):
    """Handplatte am Seance-Tisch: kleines Podest mit Messingplatte und Handumriss, Kerzenschein."""
    b = WC.Block(-0.28, -0.22, 0.28, 0.22, 0.95 * K, ppm)
    c = b.c
    b.shadow(-0.2, -0.16, 0.2, 0.14)
    b.box(-0.2, -0.16, 0.2, 0.14, 0, 0.75, WALNUT_L, WALNUT)
    fz = -0.16
    c.rect(-0.14, fz + 0.1, 0.14, fz + 0.65 * K, outline=WALNUT_D, width=0.012)
    zt = -0.16 + 0.75 * K
    c.poly([(-0.17, zt + 0.02), (0.17, zt + 0.02), (0.17, zt + 0.28), (-0.17, zt + 0.28)], fill=BRASS, outline=OUTLINE, width=0.015)
    c.line([(-0.15, zt + 0.26), (0.15, zt + 0.26)], fill=BRASS_L, width=0.01)
    # Handumriss
    px, py = 0.0, zt + 0.08
    c.ellipse(px, py + 0.04, 0.05, 0.05, fill=BRASS_D)
    for k, (dx, ln) in enumerate(((-0.05, 0.07), (-0.02, 0.1), (0.015, 0.11), (0.045, 0.09))):
        c.line([(px + dx, py + 0.07), (px + dx * 1.3, py + 0.07 + ln)], fill=BRASS_D, width=0.022)
    c.line([(px - 0.05, py + 0.03), (px - 0.1, py + 0.07)], fill=BRASS_D, width=0.022)
    c.glow(px, py + 0.08, 0.14, WARM, 0.3)
    c.text(0.0, zt + 0.235, "PLACE HAND", 0.025, BRASS_D)
    return b.result()


def fuse_board(ppm, idx=0):
    """Sicherungstafel: Holzbrett auf Pfosten mit sechs Porzellansicherungen, Messerschalter, Warnschild."""
    b = WC.Block(-0.4, -0.2, 0.4, 0.22, 1.65 * K, ppm)
    c = b.c
    b.shadow(-0.3, -0.14, 0.3, 0.14)
    for px in (-0.26, 0.26):
        c.rect(px - 0.03, -0.14, px + 0.03, -0.14 + 1.55 * K, fill=WALNUT, outline=OUTLINE, width=0.015)
    by0, by1 = -0.14 + 0.5 * K, -0.14 + 1.5 * K
    c.rect(-0.34, by0, 0.34, by1, fill=WALNUT_L, outline=OUTLINE, width=0.02)
    WC.planks(c, (-0.32, by0 + 0.02, 0.32, by1 - 0.02), WALNUT_L, 0.12)
    rnd = random.Random(idx)
    for k in range(6):
        sx = -0.25 + (k % 3) * 0.17
        sy = by0 + 0.12 + (k // 3) * 0.24
        c.rect(sx - 0.06, sy - 0.03, sx + 0.06, sy + 0.03, fill=MATTE_D, outline=OUTLINE, width=0.01)
        c.rect(sx - 0.035, sy - 0.08, sx + 0.035, sy + 0.08, fill=PORCELAIN, outline=OUTLINE, width=0.012)
        c.line([(sx - 0.025, sy - 0.06), (sx - 0.025, sy + 0.06)], fill=shade(PORCELAIN, 1.08), width=0.008)
        c.ellipse(sx, sy + 0.1, 0.012, 0.012, fill=GREEN if rnd.random() > 0.2 else RED)
        c.line([(sx, sy + 0.08), (sx, sy + 0.1)], fill=OUTLINE, width=0.006)
    # Messerschalter rechts
    c.rect(0.14, by1 - 0.28, 0.3, by1 - 0.06, fill=MATTE_D, outline=OUTLINE, width=0.012)
    c.line([(0.22, by1 - 0.24), (0.3, by1 - 0.08)], fill=OUTLINE, width=0.04)
    c.line([(0.22, by1 - 0.24), (0.3, by1 - 0.08)], fill=BRASS, width=0.022)
    c.ellipse(0.22, by1 - 0.24, 0.02, 0.02, fill=BRASS_D, outline=OUTLINE, width=0.008)
    c.ellipse(0.3, by1 - 0.08, 0.025, 0.02, fill=MATTE, outline=OUTLINE, width=0.008)
    _label(c, -0.12, by1 - 0.1, "MAIN", 0.045)
    c.poly([(-0.3, by0 - 0.02), (-0.14, by0 - 0.02), (-0.22, by0 - 0.14)], fill=YELLOW, outline=OUTLINE, width=0.01)
    c.text(-0.22, by0 - 0.06, "!", 0.05, OUTLINE)
    VA.cable(c, [(-0.3, by0 + 0.02), (-0.4, by0 - 0.1), (-0.42, -0.2)], seed=idx, w=0.025)
    return b.result()


def star_lectern(ppm, idx=0):
    """Sternkarten-Pult: Messingsaeule mit schraegem Pult, Pergamentkarte mit Sternbild, Zirkel."""
    b = WC.Block(-0.34, -0.26, 0.34, 0.26, 1.25 * K, ppm)
    c = b.c
    b.shadow(-0.24, -0.2, 0.24, 0.16)
    c.ellipse(0.0, -0.14, 0.2, 0.08, fill=BRASS_D, outline=OUTLINE, width=0.02)
    b.cyl(0.0, -0.14, 0.05, 0.04, 0.85, BRASS_L, BRASS, ry=0.025)
    zt = -0.14 + 0.9 * K
    c.poly([(-0.3, zt), (0.3, zt), (0.3, zt + 0.42), (-0.3, zt + 0.42)], fill=WALNUT, outline=OUTLINE, width=0.02)
    c.poly([(-0.26, zt + 0.04), (0.26, zt + 0.04), (0.26, zt + 0.38), (-0.26, zt + 0.38)], fill=PARCH, outline=shade(PARCH, 0.6), width=0.008)
    rnd = random.Random(idx)
    stars = [(rnd.uniform(-0.22, 0.22), rnd.uniform(zt + 0.08, zt + 0.34)) for _ in range(12)]
    for sx, sy in stars:
        c.ellipse(sx, sy, 0.008, 0.008, fill=hexc("#3a3a60"))
    path = sorted(stars[:6])
    c.line(path, fill=hexc("#3a3a60"), width=0.006)
    c.ellipse(0.0, zt + 0.21, 0.2, 0.14, outline=alpha(hexc("#3a3a60"), 120), width=0.006)
    c.line([(-0.24, zt + 0.02), (0.24, zt + 0.02)], fill=BRASS_L, width=0.015)
    c.line([(0.12, zt + 0.12), (0.2, zt + 0.3)], fill=STEEL, width=0.012)                      # Zirkel
    c.line([(0.2, zt + 0.3), (0.26, zt + 0.14)], fill=STEEL, width=0.012)
    c.ellipse(0.2, zt + 0.3, 0.015, 0.015, fill=BRASS, outline=OUTLINE, width=0.008)
    VA.candle(c, -0.3, zt + 0.3, 0.12, True, seed=idx)
    return b.result()


def bat_window(ppm, idx=0):
    """Fenster mit Laeden auf Wandstueck, ein Laden offen, Fledermaus im Rahmen, Besen angelehnt."""
    b = WC.Block(-0.52, -0.2, 0.52, 0.22, 2.0 * K, ppm)
    c = b.c
    b.shadow(-0.44, -0.14, 0.44, 0.14)
    b.box(-0.44, -0.14, 0.44, 0.16, 0, 1.9, shade(VA.BORDEAUX, 0.9), VA.BORDEAUX_D)
    fz = -0.14
    wx0, wy0, wx1, wy1 = -0.26, fz + 0.5, 0.26, fz + 1.0
    c.rect(wx0 - 0.04, wy0 - 0.04, wx1 + 0.04, wy1 + 0.04, fill=WALNUT_L, outline=OUTLINE, width=0.02)
    c.rect(wx0, wy0, wx1, wy1, fill=hexc("#1a2234"), outline=OUTLINE, width=0.015)
    c.glow(0.0, (wy0 + wy1) / 2, 0.24, hexc("#8ab0d8"), 0.25)
    c.ellipse(0.12, wy1 - 0.12, 0.06, 0.06, fill=hexc("#d8e0f0"))                               # Mond
    c.line([(0.0, wy0), (0.0, wy1)], fill=WALNUT_L, width=0.02)
    c.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=WALNUT_L, width=0.02)
    # Fledermaus
    bx, by_ = -0.1, wy0 + 0.2
    c.poly([(bx, by_), (bx - 0.09, by_ + 0.06), (bx - 0.12, by_ - 0.02), (bx - 0.05, by_ - 0.04), (bx, by_ - 0.08),
            (bx + 0.05, by_ - 0.04), (bx + 0.12, by_ - 0.02), (bx + 0.09, by_ + 0.06)], fill=hexc("#101014"))
    c.ellipse(bx - 0.012, by_ - 0.02, 0.006, 0.006, fill=RED)
    c.ellipse(bx + 0.012, by_ - 0.02, 0.006, 0.006, fill=RED)
    # Laeden: links zu, rechts offen (schraeg)
    c.rect(wx0 - 0.3, wy0 - 0.02, wx0 - 0.06, wy1 + 0.02, fill=WALNUT, outline=OUTLINE, width=0.015)
    for k in range(6):
        c.line([(wx0 - 0.28, wy0 + 0.06 + k * 0.075), (wx0 - 0.08, wy0 + 0.04 + k * 0.075)], fill=WALNUT_D, width=0.01)
    c.poly([(wx1 + 0.06, wy0 - 0.02), (wx1 + 0.22, wy0 + 0.06), (wx1 + 0.22, wy1 - 0.06), (wx1 + 0.06, wy1 + 0.02)], fill=WALNUT_L, outline=OUTLINE, width=0.015)
    c.rect(wx0 - 0.06, wy0 - 0.1, wx1 + 0.06, wy0 - 0.04, fill=WALNUT_L, outline=OUTLINE, width=0.015)   # Fensterbank
    VA.cobweb(c, wx0 - 0.04, wy1 + 0.04, 0.12, 1, -1, seed=idx)
    # Besen
    c.line([(0.4, -0.18), (0.34, fz + 1.1)], fill=OUTLINE, width=0.035)
    c.line([(0.4, -0.18), (0.34, fz + 1.1)], fill=WALNUT_L, width=0.02)
    c.poly([(0.44, -0.2), (0.3, -0.2), (0.33, -0.02), (0.41, -0.02)], fill=hexc("#c8a860"), outline=OUTLINE, width=0.012)
    return b.result()


def candle_stand(ppm, idx=0):
    """Ward Candles: schmiedeeiserner Kerzenstaender mit fuenf Kerzen, Wachstropfen, Kreidezeichen am Boden."""
    b = WC.Block(-0.32, -0.26, 0.32, 0.26, 1.45 * K, ppm)
    c = b.c
    b.shadow(-0.22, -0.2, 0.22, 0.16)
    c.ellipse(0.0, -0.14, 0.2, 0.08, fill=IRON, outline=OUTLINE, width=0.02)
    c.ellipse(0.0, -0.14, 0.26, 0.11, outline=alpha(CREAM, 140), width=0.008)                   # Kreidekreis
    c.rect(-0.025, -0.14, 0.025, -0.14 + 1.0 * K, fill=IRON, outline=OUTLINE, width=0.015)
    top = -0.14 + 1.0 * K
    c.ellipse(0.0, top, 0.24, 0.07, fill=IRON_L, outline=OUTLINE, width=0.02)
    c.ellipse(0.0, top, 0.18, 0.045, fill=IRON)
    lit = [True, True, False, True, True]
    for k in range(5):
        a = math.pi * 2 * k / 5 + 0.3
        cx, cy = 0.17 * math.cos(a), top + 0.045 * math.sin(a)
        c.ellipse(cx, cy, 0.04, 0.018, fill=IRON_D, outline=OUTLINE, width=0.01)
        VA.candle(c, cx, cy, 0.14 + (k % 3) * 0.04, lit[(k + idx) % 5], seed=idx + k)
    for k in range(3):                                                                            # Wachs an der Stange
        c.line([(0.012, top - 0.05 - k * 0.1), (0.012, top - 0.12 - k * 0.1)], fill=CREAM, width=0.012)
    return b.result()


def ouija_table(ppm, idx=0):
    """Ouija-Tisch: runder Beistelltisch mit Brett (Buchstaben, YES/NO), Planchette, Kerze."""
    b = WC.Block(-0.42, -0.28, 0.42, 0.28, 1.0 * K, ppm)
    c = b.c
    b.shadow(-0.34, -0.22, 0.34, 0.2)
    b.cyl(0.0, -0.02, 0.07, 0.0, 0.6, shade(WALNUT, 0.8), WALNUT, ry=0.04)
    b.cyl(0.0, -0.05, 0.36, 0.6, 0.06, WALNUT_L, WALNUT, ry=0.22)
    zt = -0.05 + 0.66 * K
    c.poly([(-0.3, zt + 0.02), (0.3, zt + 0.02), (0.26, zt + 0.34), (-0.26, zt + 0.34)], fill=PARCH, outline=OUTLINE, width=0.015)
    c.text(0.0, zt + 0.28, "A B C D E F G H I J K L M", 0.026, OUTLINE)
    c.text(0.0, zt + 0.22, "N O P Q R S T U V W X Y Z", 0.026, OUTLINE)
    c.text(0.0, zt + 0.16, "1 2 3 4 5 6 7 8 9 0", 0.026, OUTLINE)
    c.text(-0.2, zt + 0.08, "YES", 0.03, OUTLINE)
    c.text(0.2, zt + 0.08, "NO", 0.03, OUTLINE)
    c.text(0.0, zt + 0.07, "GOODBYE", 0.026, OUTLINE)
    c.ellipse(-0.22, zt + 0.3, 0.025, 0.02, fill=hexc("#e8c050"))                                 # Sonne/Mond
    c.ellipse(0.22, zt + 0.3, 0.025, 0.02, fill=hexc("#d8e0f0"))
    # Planchette (Herzform mit Loch)
    px, py = 0.04 + 0.03 * (idx % 3), zt + 0.2
    c.poly([(px - 0.07, py + 0.05), (px, py + 0.08), (px + 0.07, py + 0.05), (px, py - 0.07)], fill=shade(WALNUT_L, 1.1), outline=OUTLINE, width=0.012)
    c.ellipse(px, py + 0.02, 0.022, 0.018, fill=PARCH, outline=OUTLINE, width=0.008)
    VA.candle(c, -0.36, zt + 0.2, 0.12, True, seed=idx)
    c.glow(0.0, zt + 0.2, 0.3, hexc("#a0c8c0"), 0.12)
    return b.result()


def eyepiece_desk(ppm, idx=0):
    """Okularpult: Messing-Dreibein mit Okularrohr zum Himmel, Fokusring, Notizbuch mit Mondphasen."""
    b = WC.Block(-0.36, -0.26, 0.36, 0.26, 1.35 * K, ppm)
    c = b.c
    b.shadow(-0.26, -0.2, 0.26, 0.16)
    for lx, ly in ((-0.22, -0.16), (0.24, -0.14), (0.02, 0.1)):
        c.line([(lx, ly), (0.0, -0.1 + 0.9 * K)], fill=OUTLINE, width=0.04)
        c.line([(lx, ly), (0.0, -0.1 + 0.9 * K)], fill=BRASS, width=0.022)
        c.ellipse(lx, ly, 0.03, 0.02, fill=BRASS_D)
    hz = -0.1 + 0.9 * K
    c.ellipse(0.0, hz, 0.06, 0.04, fill=BRASS_L, outline=OUTLINE, width=0.015)
    # Rohr schraeg nach oben rechts
    c.line([(-0.02, hz), (0.18, hz + 0.34)], fill=OUTLINE, width=0.09)
    c.line([(-0.02, hz), (0.18, hz + 0.34)], fill=BRASS, width=0.065)
    c.line([(0.0, hz + 0.02), (0.17, hz + 0.31)], fill=BRASS_L, width=0.015)
    c.ellipse(0.19, hz + 0.36, 0.045, 0.045, fill=BRASS_D, outline=OUTLINE, width=0.015)
    c.ellipse(0.19, hz + 0.36, 0.025, 0.025, fill=hexc("#1a2234"))
    c.ellipse(0.06, hz + 0.14, 0.05, 0.05, outline=OUTLINE, width=0.035)                         # Fokusring
    c.ellipse(0.06, hz + 0.14, 0.05, 0.05, outline=BRASS_L, width=0.015)
    c.ellipse(-0.05, hz - 0.04, 0.03, 0.03, fill=BRASS_D, outline=OUTLINE, width=0.012)         # Okular
    c.ellipse(-0.05, hz - 0.04, 0.012, 0.012, fill=hexc("#1a2234"))
    # Notizbuch am Boden
    c.poly([(0.14, -0.22), (0.34, -0.2), (0.33, -0.06), (0.13, -0.08)], fill=hexc("#5a3a60"), outline=OUTLINE, width=0.012)
    for k in range(4):
        c.ellipse(0.18 + k * 0.04, -0.14, 0.012, 0.012, fill=CREAM if k % 2 == 0 else hexc("#1a2234"), outline=OUTLINE, width=0.004)
    return b.result()


def old_radio(ppm, idx=0):
    """Dreissigerjahre-Radio: Beistelltisch, Kathedralen-Gehaeuse mit Stoffbespannung, leuchtende Skala, Antenne."""
    b = WC.Block(-0.42, -0.26, 0.42, 0.26, 1.2 * K, ppm)
    c = b.c
    b.shadow(-0.34, -0.2, 0.34, 0.2)
    for lx in (-0.3, 0.3):
        c.rect(lx - 0.025, -0.2, lx + 0.025, -0.2 + 0.7 * K, fill=WALNUT, outline=OUTLINE, width=0.012)
    b.box(-0.34, -0.2, 0.34, 0.2, 0.7, 0.05, WALNUT_L, WALNUT)
    zt = -0.2 + 0.75 * K
    # Gehaeuse mit Rundbogen
    rx0, rx1 = -0.22, 0.22
    c.rect(rx0, zt + 0.03, rx1, zt + 0.3, fill=WALNUT_L, outline=OUTLINE, width=0.018)
    c.ellipse(0.0, zt + 0.3, 0.22, 0.16, fill=WALNUT_L, outline=OUTLINE, width=0.018)
    c.rect(rx0 + 0.018, zt + 0.3, rx1 - 0.018, zt + 0.32, fill=WALNUT_L)
    c.rect(rx0 + 0.018, zt + 0.045, rx1 - 0.018, zt + 0.3, fill=WALNUT_L)
    # Lautsprecherstoff im Bogen
    c.ellipse(0.0, zt + 0.3, 0.15, 0.11, fill=hexc("#b89a62"), outline=WALNUT_D, width=0.012)
    for k in range(5):
        c.line([(-0.13 + k * 0.065, zt + 0.22), (-0.13 + k * 0.065, zt + 0.4)], fill=alpha(WALNUT_D, 120), width=0.005)
    c.rect(-0.02, zt + 0.2, 0.02, zt + 0.4, fill=WALNUT_D)
    # Skala leuchtend, Zeiger, Knoepfe
    c.rect(-0.16, zt + 0.08, 0.16, zt + 0.17, fill=hexc("#2a2418"), outline=OUTLINE, width=0.012)
    c.glow(0.0, zt + 0.125, 0.18, hexc("#e8a83c"), 0.4)
    for k in range(9):
        sx = -0.14 + k * 0.035
        c.line([(sx, zt + 0.1), (sx, zt + 0.13 if k % 2 == 0 else zt + 0.12)], fill=hexc("#f0c060"), width=0.006)
    c.line([(0.05 + 0.02 * (idx % 3), zt + 0.09), (0.05 + 0.02 * (idx % 3), zt + 0.16)], fill=RED, width=0.008)
    _knob(c, -0.17, zt + 0.045 + 0.0, 0.022, 0.8, WALNUT_D)
    _knob(c, 0.17, zt + 0.045, 0.022, -0.4, WALNUT_D)
    # Antenne und Kopfhoerer
    c.line([(0.2, zt + 0.42), (0.34, zt + 0.72)], fill=STEEL, width=0.012)
    c.ellipse(0.34, zt + 0.72, 0.012, 0.012, fill=STEEL)
    c.ellipse(-0.3, zt + 0.12, 0.07, 0.05, outline=OUTLINE, width=0.03)
    c.ellipse(-0.3, zt + 0.12, 0.07, 0.05, outline=MATTE_L, width=0.015)
    VA.cable(c, [(-0.24, zt + 0.1), (-0.3, zt - 0.1), (-0.38, -0.24)], seed=idx, w=0.015)
    return b.result()


# ------------------------------------------------------------------ Heizungsgitter (Vents im Haus)

GRATE_W, GRATE_H = 0.72, 0.52


def grate_frames(ppm, seed=0):
    """Gusseisernes Heizungsgitter im Boden, 6 Bilder: [0] zu, der Rost klappt an der Nordkante hoch, [5] offen
    (Schacht sichtbar). Alle Bilder gleich gross, Anker = Mitte der Oeffnung."""
    out = []
    w, h = GRATE_W / 2, GRATE_H / 2
    lift_max = 0.42
    x0, y0, x1, y1 = -w - 0.18, -h - 0.16, w + 0.18, h + lift_max + 0.2
    for k in range(6):
        f = k / 5
        c = Canvas(x0, y0, x1, y1, ppm)
        c.soft_shadow([(-w - 0.02, -h - 0.06), (w + 0.08, -h - 0.06), (w + 0.08, h), (-w - 0.02, h)], 70, 0.05)
        # Rahmen mit Schraubloechern
        c.rect(-w - 0.08, -h - 0.08, w + 0.08, h + 0.08, fill=IRON, outline=OUTLINE, width=0.03)
        c.rect(-w - 0.05, -h - 0.05, w + 0.05, h + 0.05, outline=IRON_L, width=0.01)
        for sx, sy in ((-w - 0.04, -h - 0.04), (w + 0.04, -h - 0.04), (-w - 0.04, h + 0.04), (w + 0.04, h + 0.04)):
            c.ellipse(sx, sy, 0.014, 0.014, fill=IRON_D, outline=OUTLINE, width=0.006)
        # Schacht
        c.rect(-w, -h, w, h, fill=hexc("#0b0d10"), outline=OUTLINE, width=0.02)
        if f > 0.15:
            c.rect(-w + 0.03, h - 0.14, w - 0.03, h - 0.02, fill=hexc("#2a1c10"))                 # Rueckwand
            c.line([(-0.18, h - 0.08), (0.18, h - 0.08)], fill=hexc("#8a6a45"), width=0.02)      # Sprosse
        # Rost: Suedkante hebt sich (Trapez), Staebe laufen mit
        lift = lift_max * f
        shrink = 0.08 * f
        ps = [(-w, -h + lift), (w, -h + lift), (w - shrink, h + 0.04 * f), (-w + shrink, h + 0.04 * f)]
        c.poly(ps, fill=IRON, outline=OUTLINE, width=0.025)
        # Staebe (laengs) und Querstreben als Linien innerhalb des Trapezes
        def P(u, v):
            ax, ay = ps[3][0] + u * (ps[2][0] - ps[3][0]), ps[3][1]
            bx, by = ps[0][0] + u * (ps[1][0] - ps[0][0]), ps[0][1]
            return (bx + v * (ax - bx), by + v * (ay - by))
        for i in range(1, 8):
            u = i / 8
            c.line([P(u, 0.05), P(u, 0.95)], fill=hexc("#101216"), width=0.03)
            c.line([P(u - 0.012, 0.05), P(u - 0.012, 0.95)], fill=IRON_L, width=0.006)
        for v in (0.33, 0.66):
            c.line([P(0.03, v), P(0.97, v)], fill=IRON_L, width=0.012)
        c.ellipse(*P(0.5, 0.15), 0.03, 0.02, outline=IRON_L, width=0.012)                           # Griffschlaufe
        if f > 0.3:                                                                                # Rostkante (Dicke)
            c.poly([ps[0], ps[1], (ps[1][0], ps[1][1] - 0.04), (ps[0][0], ps[0][1] - 0.04)], fill=IRON_D, outline=OUTLINE, width=0.015)
        img = c.finish()
        out.append((img, int(round((0 - c.x0) * ppm)), int(round((0 - c.y0) * ppm))))
    return out


# ------------------------------------------------------------------ Zuordnung

BY_NAME = {
    "DivertPowerConsole": distro_box, "DataConsole": dailies_cart, "UploadDataConsole": dailies_cart,
    "FixWiringConsole": dimmer_junction, "GarbageConsole": trash_stand, "AirlockConsole": trash_stand,
    "NoOxyConsole": damper_wheel, "UnlockManifoldsConsole": puzzle_box,
    "UpperHandConsole": hand_plate, "LowerHandConsole": hand_plate, "SwitchConsole": fuse_board,
    "CalibrateConsole": dimmer_rack, "ChartCourseConsole": star_lectern, "WeaponConsole": bat_window,
    "ShieldConsole": candle_stand, "StartReactorConsole": ouija_table,
    "SurveillanceConsole": video_village, "AdminTable": plan_table, "FreeplayLaptop": clapper_crate,
    "SwipeCardConsole": callsheet_post, "MedScanner": ringlight_mat, "MedBayConsole": blood_bench,
    "CleanFilterConsole": flue_hatch, "FuelEngineConsole": fuel_drum, "AlignEngineConsole": small_generator,
    "gasCanConsole": can_pallet, "StabilizeSteeringConsole": eyepiece_desk, "FixCommsConsole": old_radio,
}

# Motive, die vom Raum abhaengen (User 24.10.: in der Kueche ein Kohlenkasten statt des Treibstofffasses; im Crew
# Camp bleibt das Fass). villa_consoles._render_all prueft diese Tabelle vor BY_NAME.
BY_NAME_ROOM = {
    ("FuelEngineConsole", "kitchen"): coal_bin,
}


if __name__ == "__main__":
    from PIL import Image
    tiles = []
    for name, fn in sorted(BY_NAME.items(), key=lambda kv: kv[1].__name__):
        if fn in [t[0] for t in tiles]:
            continue
        img, ax, ay = fn(128, 1)
        tiles.append((fn, img))
        print(f"{fn.__name__:18s} {img.size} anchor ({ax},{ay})")
    tiles += [(None, fr[0]) for fr in grate_frames(128)]
    cols = 6
    tw = max(t[1].width for t in tiles) + 16
    th = max(t[1].height for t in tiles) + 16
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * tw, rows * th), (96, 80, 64, 255))
    for i, (_fn, im) in enumerate(tiles):
        x, y = (i % cols) * tw + 8, (i // cols) * th + th - 8 - im.height
        sheet.paste(im, (x, y), im)
    os.makedirs("_vent_anim", exist_ok=True)
    sheet.save("_vent_anim/consoles_new.png")
    print(sheet.size)
