# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_egg.py - Easter Egg "Pentagramm" auf dem Ravenhollow Cemetery (Auftrag 2026-10-24, Teil C.2).
#
#   python tools/graveyard_egg.py        -> assets/graveyard_egg/*.png, tools/_graveyard_egg/sheet.png
#
# Sprites (Massstab 160 px/m wie die Props, schraege Aufsicht K = 0,55, Standlinie = unterer Bildrand Mitte):
#   egg_candle_off.png, egg_candle_on_1..4.png   96 x 128   Kerze mit Wachsnasen auf kleinem Steinsockel (0,45 m), Flackern
#   egg_candle_glow.png                          256 x 256  warmer weicher Schein, sehr transparent (auf den Boden gelegt)
#   egg_demon_rise_1..12.png                     512 x 640  der Daemon steigt aus dem Boden (Fusspunkt unten Mitte)
#   egg_demon_idle_1..8.png                      512 x 640  Schleife: Atmen, Fluegelschlag, gluehende Augen, Schwanz
#   egg_demon_sink_1..8.png                      512 x 640  versinkt wieder
#   egg_demon_floor_glow.png                     640 x 512  rotes Gluehen des Pentagramms von oben (Stern 1,52 x 1,216 m,
#                                                           Runenkreis 1,84 m, Spitzen bei 90 Grad + k * 144 Grad)
# Gezeichnet mit museum_art.Canvas (Weltmeter, Umrisse, flache Farben mit einer Schattenstufe), keine Fotos, kein Blut.

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from museum_art import Canvas, K, OUTLINE, alpha, hexc, lift, shade  # noqa: E402

ASSETS = HERE.parent / "assets" / "graveyard_egg"
PREVIEW = HERE / "_graveyard_egg"
PPM = 160

STONE = lift("#5c6070", 1.5)
STONE_L = shade(STONE, 1.2)
STONE_D = shade(STONE, 0.7)
WAX = hexc("#e8dcc0")
WAX_D = shade(WAX, 0.8)
FLAME = hexc("#ffb43c")
FLAME_CORE = hexc("#fff4c8")
FLAME_RED = hexc("#ff6a2a")
WARM = hexc("#ffd28a")
SKIN = lift("#8a1e1e", 1.35)          # Daemonenhaut (dunkles Rot)
SKIN_L = shade(SKIN, 1.3)
SKIN_D = shade(SKIN, 0.68)
HORN = hexc("#2a2026")
HORN_L = hexc("#5a4a50")
WING = lift("#4a1420", 1.25)
WING_D = shade(WING, 0.7)
EYE = hexc("#ffcc3a")
EYE_CORE = hexc("#fff6d0")
TOOTH = hexc("#f4eee0")
EMBER = hexc("#ff7a2a")
GLOW_RED = hexc("#ff3020")
SMOKE = (40, 24, 30)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


# ------------------------------------------------------------------ Kerze

def flame_shape(c, x, y, s, lean, flick):
    """Flamme: Tropfen nach oben, leicht geneigt, mit hellem Kern und kleinem Funken."""
    h = 0.14 * s * (0.9 + 0.2 * flick)
    tip = (x + lean * 0.05, y + h)
    pts = [(x - 0.035 * s, y), (x - 0.03 * s, y + 0.04 * s), (x - 0.02 * s + lean * 0.02, y + h * 0.6), tip,
           (x + 0.02 * s + lean * 0.02, y + h * 0.6), (x + 0.03 * s, y + 0.04 * s), (x + 0.035 * s, y)]
    c.poly(pts, fill=FLAME_RED, outline=shade(FLAME_RED, 0.65), width=0.01)
    c.poly([(x - 0.025 * s, y + 0.005), (x + 0.025 * s, y + 0.005), (x + 0.012 * s + lean * 0.015, y + h * 0.55), (x + lean * 0.03, y + h * 0.78),
            (x - 0.012 * s + lean * 0.015, y + h * 0.55)], fill=FLAME)
    c.poly([(x - 0.012 * s, y + 0.01), (x + 0.012 * s, y + 0.01), (x + lean * 0.01, y + h * 0.42)], fill=FLAME_CORE)


def candle(lit, variant=0):
    """96 x 128: Steinsockel (achteckig, 0,3 m), Kerze r 0,065 m, Hoehe 0,3 m, Gesamthoehe etwa 0,45 m."""
    c = Canvas(-0.3, 0.0, 0.3, 0.8, PPM)
    rnd = random.Random(7)
    # Bodenschatten
    c.soft_shadow([(-0.14 + 0.04, -0.02), (0.18, -0.02), (0.18, 0.1), (-0.1, 0.1)], 90, 0.05)
    # Sockel: achteckige Steinplatte mit Hoehe 0,12 m (Front + Deckflaeche)
    r = 0.15
    zt = 0.12 * K
    oct_b = [(r * math.cos(a), 0.06 + r * 0.5 * math.sin(a)) for a in [math.radians(22.5 + k * 45) for k in range(8)]]
    oct_t = [(x, y + zt) for x, y in oct_b]
    c.poly([oct_b[4], oct_b[5], oct_b[6], oct_b[7], oct_t[7], oct_t[6], oct_t[5], oct_t[4]], fill=STONE, outline=OUTLINE, width=0.02)
    c.line([(oct_b[5][0], oct_b[5][1] + 0.005), (oct_b[5][0], oct_t[5][1] - 0.005)], fill=STONE_D, width=0.01)
    c.line([(oct_b[6][0], oct_b[6][1] + 0.005), (oct_b[6][0], oct_t[6][1] - 0.005)], fill=STONE_D, width=0.01)
    c.poly(oct_t, fill=STONE_L, outline=OUTLINE, width=0.02)
    c.poly([(x * 0.8, 0.06 + zt + (y - 0.06 - zt) * 0.8) for x, y in oct_t], outline=alpha(STONE_D, 120), width=0.008)
    c.ellipse(-0.1, 0.035, 0.03, 0.012, fill=alpha(hexc("#5f8a4c"), 150))                              # Moos
    # Wachsreste auf dem Sockel, Kerze mit Nasen
    base_y = 0.06 + zt
    c.ellipse(0.0, base_y + 0.005, 0.1, 0.035, fill=WAX_D, outline=OUTLINE, width=0.012)
    cr = 0.065
    ch = 0.3 * K + 0.12
    c.rect(-cr, base_y, cr, base_y + ch, fill=WAX, outline=OUTLINE, width=0.02)
    c.rect(cr - 0.03, base_y + 0.01, cr - 0.005, base_y + ch - 0.01, fill=WAX_D)
    c.line([(-cr + 0.012, base_y + 0.02), (-cr + 0.012, base_y + ch - 0.02)], fill=(255, 255, 255, 140), width=0.01)
    for k, (dx, h) in enumerate(((-0.04, 0.12), (0.03, 0.08), (0.055, 0.16))):
        c.line([(dx, base_y + ch - 0.01), (dx, base_y + ch - h)], fill=WAX, width=0.018)
        c.ellipse(dx, base_y + ch - h, 0.014, 0.011, fill=WAX, outline=OUTLINE, width=0.006)
        c.line([(dx, base_y + ch - 0.01), (dx, base_y + ch - h)], fill=OUTLINE, width=0.004)
    top = base_y + ch
    c.ellipse(0.0, top, cr, cr * 0.45, fill=shade(WAX, 1.05), outline=OUTLINE, width=0.02)
    c.ellipse(0.0, top, cr * 0.6, cr * 0.26, fill=WAX_D)
    if lit:
        phase = variant / 4.0 * math.tau
        lean = 0.5 * math.sin(phase)
        flick = 0.5 + 0.5 * math.sin(phase * 2 + 0.7)
        c.glow(0.0, top + 0.1, 0.42, WARM, 0.45 + 0.1 * flick)
        c.glow(0.0, top + 0.07, 0.16, FLAME_CORE, 0.8)
        c.ellipse(0.0, top + 0.002, cr * 0.5, cr * 0.2, fill=alpha(FLAME, 200))                        # fluessiges Wachs leuchtet
        c.line([(0.0, top), (0.0 + lean * 0.01, top + 0.03)], fill=OUTLINE, width=0.012)
        flame_shape(c, 0.0, top + 0.02, 1.0, lean, flick)
        for k in range(2):                                                                                # Funken
            fx, fy = rnd.uniform(-0.06, 0.06) + lean * 0.05, top + 0.2 + rnd.uniform(0, 0.12)
            c.ellipse(fx, fy, 0.008, 0.008, fill=alpha(FLAME, 200))
    else:
        c.line([(0.0, top), (0.0, top + 0.035)], fill=OUTLINE, width=0.012)
        c.ellipse(0.0, top + 0.036, 0.01, 0.008, fill=hexc("#3a3034"))
        pts = [(0.0 + 0.02 * math.sin(k * 1.7), top + 0.05 + k * 0.045) for k in range(6)]
        c.line(pts, fill=(200, 200, 212, 90), width=0.016)
    return c.finish()


def candle_glow():
    c = Canvas(-0.8, -0.8, 0.8, 0.8, PPM)
    c.glow(0.0, 0.0, 0.8, WARM, 0.32)
    c.glow(0.0, 0.0, 0.45, hexc("#ffe0a0"), 0.25)
    img = c.finish()
    return img


# ------------------------------------------------------------------ Daemon

DEMON_S = 0.58       # Modell (Hufe 0 bis Hornspitzen 4,9) -> ca. 2,85 m Bildhoehe
DEMON_H = 4.95 * DEMON_S


def demon_body(c, dy, t_idle=0.0, wing=0.5, eyes=1.0, arms="down", mouth=0.3, scale=DEMON_S, fade=1.0):
    """Daemon (ca. 2,8 m), frontal wie die Spielfiguren (keine K-Stauchung, er steht senkrecht im Bild): Hufe,
    massige Beine, Rumpf, Arme mit Krallen, Kopf mit Hoernern, Fledermausfluegel (wing 0..1 = Schlag), Schwanz.
    dy verschiebt alles (Aufsteigen, Versinken), unterhalb der Bildunterkante ist er unsichtbar."""
    S = scale
    KZ = 1.0

    def P(x, z):
        return (x * S, dy + z * KZ * S)

    def poly(pts, **kw):
        c.poly([P(x, z) for x, z in pts], **kw)

    def ell(x, z, rx, rz, **kw):
        c.ellipse(x * S, dy + z * KZ * S, rx * S, rz * KZ * S, **kw)

    def line(pts, **kw):
        c.line([P(x, z) for x, z in pts], **kw)

    bob = 0.06 * math.sin(t_idle * math.tau)
    ow = 0.045
    # Schwanz (hinten)
    sway = 0.25 * math.sin(t_idle * math.tau + 1.0)
    tail = [(0.3, 1.4), (0.8 + sway * 0.4, 0.9), (1.1 + sway, 0.5 + abs(sway) * 0.3), (1.25 + sway * 1.2, 0.9 + sway * 0.4)]
    line(tail, fill=OUTLINE, width=0.16)
    line(tail, fill=SKIN_D, width=0.09)
    tip = tail[-1]
    poly([(tip[0] - 0.08, tip[1] - 0.05), (tip[0] + 0.12, tip[1] + 0.02), (tip[0] - 0.02, tip[1] + 0.3), (tip[0] - 0.12, tip[1] + 0.1)], fill=SKIN_D, outline=OUTLINE, width=0.03)
    # Fluegel (hinten): Flughaut mit Knochenfingern, Schlag ueber wing
    for sx in (-1, 1):
        w_ = 0.55 + 0.75 * wing
        up = 0.8 + 1.0 * wing
        root = (sx * 0.5, 2.3 + bob)
        f1 = (sx * (0.5 + w_ * 0.9), 2.4 + up + bob)
        f2 = (sx * (0.5 + w_ * 1.5), 2.1 + up * 0.55 + bob)
        f3 = (sx * (0.5 + w_ * 1.45), 1.5 + up * 0.1 + bob)
        mem = [root, (sx * (0.5 + w_ * 0.45), 2.6 + up * 0.75 + bob), f1, (sx * (0.5 + w_ * 1.2), 2.3 + up * 0.5 + bob), f2,
               (sx * (0.5 + w_ * 1.3), 1.75 + up * 0.25 + bob), f3, (sx * (0.5 + w_ * 0.9), 1.45 + bob), (sx * 0.55, 1.6 + bob)]
        poly(mem, fill=WING, outline=OUTLINE, width=ow)
        poly([(x * 0.92 + root[0] * 0.08, z * 0.92 + root[1] * 0.08) for x, z in mem[1:-1]] + [root], fill=alpha(WING_D, 120))
        for f in (f1, f2, f3):
            line([root, f], fill=OUTLINE, width=0.075)
            line([root, f], fill=SKIN_D, width=0.04)
            ell(f[0], f[1], 0.045, 0.045, fill=HORN_L, outline=OUTLINE, width=0.02)
    # Hufe und Beine
    for sx in (-1, 1):
        lx = sx * 0.38
        poly([(lx - 0.22, 0.0), (lx + 0.22, 0.0), (lx + 0.16, 0.12), (lx - 0.16, 0.12)], fill=HORN, outline=OUTLINE, width=ow)   # Huf
        line([(lx - 0.02, 0.0), (lx - 0.02, 0.11)], fill=HORN_L, width=0.03)
        poly([(lx - 0.2, 0.1), (lx + 0.2, 0.1), (lx + 0.28, 0.6), (lx + 0.3, 1.1), (lx - 0.3, 1.1), (lx - 0.26, 0.6)], fill=SKIN, outline=OUTLINE, width=ow)
        poly([(lx - 0.12, 0.2), (lx - 0.05, 0.2), (lx + 0.02, 0.6), (lx - 0.1, 1.0), (lx - 0.2, 1.0), (lx - 0.17, 0.6)], fill=SKIN_L)
        ell(lx + 0.02, 0.62, 0.14, 0.11, fill=SKIN_L, outline=alpha(SKIN_D, 200), width=0.015)                     # Knie
    # Lendenschurz aus Ketten / Fellsaum
    poly([(-0.68, 1.05), (0.68, 1.05), (0.6, 1.4 + bob), (-0.6, 1.4 + bob)], fill=HORN, outline=OUTLINE, width=ow)
    for k in range(5):
        line([(-0.5 + k * 0.25, 1.05), (-0.5 + k * 0.25 + 0.05, 1.35 + bob)], fill=HORN_L, width=0.02)
    # Rumpf (Brust breit, Bauch, Schulterbuckel)
    torso = [(-0.72, 1.3 + bob), (0.72, 1.3 + bob), (0.9, 2.0 + bob), (0.95, 2.55 + bob), (0.6, 2.75 + bob), (-0.6, 2.75 + bob),
             (-0.95, 2.55 + bob), (-0.9, 2.0 + bob)]
    poly(torso, fill=SKIN, outline=OUTLINE, width=ow)
    poly([(-0.42, 1.45 + bob), (0.42, 1.45 + bob), (0.5, 2.0 + bob), (0.36, 2.4 + bob), (-0.36, 2.4 + bob), (-0.5, 2.0 + bob)], fill=SKIN_L)   # Brust/Bauch heller
    line([(0.0, 1.5 + bob), (0.0, 2.35 + bob)], fill=alpha(SKIN_D, 200), width=0.03)
    for sx in (-1, 1):                                                                                     # Brustmuskeln, Rippen
        ell(sx * 0.28, 2.3 + bob, 0.26, 0.18, fill=SKIN_L, outline=alpha(SKIN_D, 220), width=0.02)
        for k in range(3):
            line([(sx * 0.15, 1.6 + k * 0.2 + bob), (sx * 0.45, 1.68 + k * 0.2 + bob)], fill=alpha(SKIN_D, 150), width=0.02)
    # Arme mit Krallenhaenden
    for sx in (-1, 1):
        sh = (sx * 0.9, 2.5 + bob)
        if arms == "up":
            el = (sx * 1.35, 2.9 + bob)
            hd = (sx * 1.25, 3.55 + bob)
        elif arms == "reach":
            el = (sx * 1.3, 2.0 + bob)
            hd = (sx * 1.1, 1.3 + bob)
        else:
            el = (sx * 1.25, 1.95 + bob)
            hd = (sx * 1.15, 1.25 + bob)
        for col, w_ in ((OUTLINE, 0.36), (SKIN, 0.27)):
            line([sh, el, hd], fill=col, width=w_)
        line([(sh[0] + sx * 0.03, sh[1] - 0.1), (el[0] - sx * 0.02, el[1] + 0.02)], fill=SKIN_L, width=0.07)
        ell(sh[0], sh[1] + 0.05, 0.3, 0.26, fill=SKIN, outline=OUTLINE, width=ow)                               # Schulter
        ell(sh[0] - sx * 0.05, sh[1] + 0.12, 0.17, 0.14, fill=SKIN_L)
        ell(hd[0], hd[1], 0.2, 0.18, fill=SKIN_D, outline=OUTLINE, width=ow)                                    # Hand
        for k in range(4):
            a = (-0.6 + k * 0.4) + (math.pi / 2 if arms == "up" else -math.pi / 2)
            if arms == "reach":
                a = -0.9 + k * 0.6
            kx, kz = hd[0] + 0.18 * math.cos(a), hd[1] + 0.3 * math.sin(a)
            poly([(hd[0] + 0.1 * math.cos(a + 0.5), hd[1] + 0.16 * math.sin(a + 0.5)), (kx, kz), (hd[0] + 0.1 * math.cos(a - 0.5), hd[1] + 0.16 * math.sin(a - 0.5))],
                 fill=TOOTH, outline=OUTLINE, width=0.02)
    # Hals und Kopf
    poly([(-0.3, 2.7 + bob), (0.3, 2.7 + bob), (0.26, 3.0 + bob), (-0.26, 3.0 + bob)], fill=SKIN_D, outline=OUTLINE, width=ow)
    hz = 3.35 + bob
    head = [(-0.42, hz - 0.3), (0.42, hz - 0.3), (0.5, hz + 0.05), (0.4, hz + 0.42), (0.0, hz + 0.5), (-0.4, hz + 0.42), (-0.5, hz + 0.05)]
    poly(head, fill=SKIN, outline=OUTLINE, width=ow)
    poly([(-0.3, hz - 0.25), (0.3, hz - 0.25), (0.34, hz + 0.1), (0.0, hz + 0.25), (-0.34, hz + 0.1)], fill=SKIN_L)
    for sx in (-1, 1):                                                                                     # Hoerner (gebogen)
        horn = [(sx * 0.3, hz + 0.35), (sx * 0.62, hz + 0.75), (sx * 0.5, hz + 1.25)]
        line(horn, fill=OUTLINE, width=0.24)
        line(horn, fill=HORN, width=0.16)
        line([(sx * 0.33, hz + 0.42), (sx * 0.58, hz + 0.8), (sx * 0.52, hz + 1.1)], fill=HORN_L, width=0.04)
        for k in range(3):
            q = (sx * (0.4 + k * 0.08), hz + 0.5 + k * 0.17)
            line([(q[0] - 0.06, q[1]), (q[0] + 0.06, q[1] + 0.02)], fill=alpha(OUTLINE, 160), width=0.02)
        poly([(sx * 0.5, hz + 1.2), (sx * 0.56, hz + 1.3), (sx * 0.44, hz + 1.42)], fill=HORN, outline=OUTLINE, width=0.02)
        # Augen (gluehend)
        ex, ez = sx * 0.2, hz + 0.1
        if eyes > 0.05:
            c.glow(ex * S, dy + ez * KZ * S, 0.3 * S, EYE, 0.5 * eyes)
        poly([(ex - 0.15, ez - 0.03), (ex + 0.15, ez - 0.03), (ex + 0.1, ez + 0.14), (ex - 0.1, ez + 0.1)], fill=EYE if eyes > 0.05 else HORN, outline=OUTLINE, width=0.025)
        if eyes > 0.05:
            ell(ex, ez + 0.03, 0.06, 0.05, fill=EYE_CORE)
        line([(ex - 0.16, ez + 0.14), (ex + 0.1, ez + 0.2)], fill=OUTLINE, width=0.04)                         # Brauen (zornig)
    # Nase und Maul mit Fangzaehnen
    poly([(-0.07, hz - 0.02), (0.07, hz - 0.02), (0.0, hz - 0.12)], fill=SKIN_D, outline=OUTLINE, width=0.02)
    mw, mh = 0.3, 0.06 + 0.14 * mouth
    poly([(-mw, hz - 0.14), (mw, hz - 0.14), (mw - 0.04, hz - 0.14 - mh), (-mw + 0.04, hz - 0.14 - mh)], fill=hexc("#1a0a0c"), outline=OUTLINE, width=0.025)
    for k in range(6):
        tx = -mw + 0.07 + k * (2 * mw - 0.14) / 5
        ln = 0.09 if k in (0, 5) else 0.05
        poly([(tx - 0.03, hz - 0.14), (tx + 0.03, hz - 0.14), (tx, hz - 0.14 - ln)], fill=TOOTH, outline=OUTLINE, width=0.012)
        if mouth > 0.4:
            poly([(tx - 0.025, hz - 0.14 - mh), (tx + 0.025, hz - 0.14 - mh), (tx, hz - 0.14 - mh + 0.04)], fill=TOOTH, outline=OUTLINE, width=0.01)
    if mouth > 0.4:
        c.glow(0.0, dy + (hz - 0.14 - mh / 2) * KZ * S, 0.2 * S, EMBER, 0.45)
    # Ohren / Kieferlinie
    for sx in (-1, 1):
        poly([(sx * 0.48, hz + 0.05), (sx * 0.7, hz + 0.12), (sx * 0.5, hz - 0.1)], fill=SKIN, outline=OUTLINE, width=0.025)


def embers(c, rnd, n, y0, y1, x_spread, size=0.03):
    for _ in range(n):
        x = rnd.uniform(-x_spread, x_spread)
        y = rnd.uniform(y0, y1)
        r = rnd.uniform(size * 0.4, size)
        c.glow(x, y, r * 4, EMBER, 0.35)
        c.ellipse(x, y, r, r, fill=rnd.choice((EMBER, FLAME, GLOW_RED)))


def smoke_ring(c, rnd, y, rx, a=120):
    for k in range(9):
        x = -rx + k * (2 * rx / 8) + rnd.uniform(-0.1, 0.1)
        c.ellipse(x, y + rnd.uniform(0.0, 0.15), rnd.uniform(0.18, 0.3), rnd.uniform(0.08, 0.14), fill=SMOKE + (a,))


def demon_frame(kind, i, n):
    """512 x 640: Fusspunkt unten Mitte, der Daemon steht auf der Bildunterkante."""
    c = Canvas(-1.6, 0.0, 1.6, 4.0, PPM)
    rnd = random.Random(100 + i)
    H_TOTAL = DEMON_H          # Hornspitzen in Bild-m (Modell 4,95 x DEMON_S)
    if kind == "rise":
        t = ease_out(i / (n - 1))
        dy = -(1.0 - t) * H_TOTAL
        c.glow(0.0, 0.05, 1.3, GLOW_RED, 0.45 * (0.6 + 0.4 * t))
        demon_body(c, dy, t_idle=0.0, wing=0.1 + 0.4 * t, eyes=min(1.0, t * 1.6), arms="up" if t < 0.7 else "down", mouth=0.9 * (1 - t) + 0.2)
        smoke_ring(c, rnd, 0.02, 1.0, a=140)
        embers(c, rnd, 12, 0.05, 0.8 + 1.5 * t, 1.1)
        c.glow(0.0, 0.08, 1.0, GLOW_RED, 0.3)
    elif kind == "idle":
        t = i / n
        dy = 0.0
        c.glow(0.0, 0.05, 1.1, GLOW_RED, 0.3)
        demon_body(c, dy, t_idle=t, wing=0.5 + 0.45 * math.sin(t * math.tau), eyes=0.85 + 0.15 * math.sin(t * math.tau * 2), arms="down", mouth=0.3 + 0.1 * math.sin(t * math.tau))
        smoke_ring(c, rnd, 0.0, 0.9, a=90)
        embers(c, rnd, 8, 0.05, 1.2, 1.0, size=0.025)
    else:   # sink
        t = ease(i / (n - 1))
        dy = -t * H_TOTAL
        c.glow(0.0, 0.05, 1.3, GLOW_RED, 0.45 * (1.0 - 0.5 * t))
        demon_body(c, dy, t_idle=0.0, wing=0.9 - 0.7 * t, eyes=1.0 - t * 0.8, arms="up", mouth=0.2 + 0.7 * t)
        smoke_ring(c, rnd, 0.02, 1.0, a=150)
        embers(c, rnd, 14, 0.05, 1.0 + 1.0 * (1 - t), 1.1)
        c.glow(0.0, 0.08, 1.0, GLOW_RED, 0.35)
    return c.finish()


def floor_glow():
    """640 x 512: rotes Gluehen des Pentagramms von oben (wird auf den Boden gelegt)."""
    c = Canvas(-2.0, -1.6, 2.0, 1.6, PPM)
    rx, ry = 1.52, 1.216
    c.glow(0.0, 0.0, 1.9, GLOW_RED, 0.28)
    # Runenkreis (Aussenring 1,84 / 1,64 m Radius x, 0,8 in y)
    for r, w_ in ((1.84, 0.07), (1.64, 0.035)):
        c.ellipse(0.0, 0.0, r, r * 0.8, fill=None, outline=alpha(GLOW_RED, 150), width=w_ * 2)
        c.ellipse(0.0, 0.0, r, r * 0.8, fill=None, outline=alpha(hexc("#ffb080"), 230), width=w_)
    tips = [(rx * math.cos(math.radians(90 + k * 144)), ry * math.sin(math.radians(90 + k * 144))) for k in range(5)]
    for k in range(5):
        a, b = tips[k], tips[(k + 1) % 5]
        c.line([a, b], fill=alpha(GLOW_RED, 170), width=0.12)
        c.line([a, b], fill=alpha(hexc("#ffc090"), 240), width=0.045)
    for k in range(12):                                                                                  # Runen auf dem Ring
        a = k / 12 * math.tau
        x, y = 1.744 * math.cos(a), 1.744 * 0.8 * math.sin(a)
        rr = random.Random(k)
        pts = [(x + rr.uniform(-0.07, 0.07), y + rr.uniform(-0.07, 0.07)) for _ in range(3)]
        c.line(pts, fill=alpha(hexc("#ffc090"), 230), width=0.03)
    for tx, ty in tips:
        c.glow(tx, ty, 0.35, FLAME, 0.4)
    c.glow(0.0, 0.0, 0.7, hexc("#ff6040"), 0.35)
    return c.finish()


def sheet(images):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    rows = [
        [("egg_candle_off", 2.0), ("egg_candle_on_1", 2.0), ("egg_candle_on_2", 2.0), ("egg_candle_on_3", 2.0), ("egg_candle_on_4", 2.0), ("egg_candle_glow", 1.0)],
        [("egg_demon_rise_%d" % k, 0.5) for k in (1, 3, 5, 7, 9, 11, 12)],
        [("egg_demon_idle_%d" % k, 0.5) for k in range(1, 9)],
        [("egg_demon_sink_%d" % k, 0.5) for k in range(1, 9)] + [("egg_demon_floor_glow", 0.5)],
    ]
    pad = 20
    W = max(sum(int(images[n].width * s) + pad for n, s in r) for r in rows) + pad
    H = sum(max(int(images[n].height * s) for n, s in r) + 40 + pad for r in rows) + pad
    sh = Image.new("RGB", (W, H), (46, 60, 52))
    d = ImageDraw.Draw(sh)
    y = pad
    for r in rows:
        rh = max(int(images[n].height * s) for n, s in r)
        x = pad
        for n, s in r:
            im = images[n]
            im2 = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s != 1.0 else im
            d.rectangle([x, y + 30, x + im2.width, y + 30 + im2.height], outline=(80, 100, 90))
            sh.paste(im2, (x, y + 30 + rh - im2.height), im2)
            d.text((x, y + 4), n + " %dx%d" % im.size, font=font, fill=(255, 255, 255))
            x += im2.width + pad
        y += rh + 40 + pad
    return sh


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)
    images = {"egg_candle_off": candle(False)}
    for k in range(1, 5):
        images["egg_candle_on_%d" % k] = candle(True, k - 1)
    images["egg_candle_glow"] = candle_glow()
    for k in range(1, 13):
        images["egg_demon_rise_%d" % k] = demon_frame("rise", k - 1, 12)
    for k in range(1, 9):
        images["egg_demon_idle_%d" % k] = demon_frame("idle", k - 1, 8)
    for k in range(1, 9):
        images["egg_demon_sink_%d" % k] = demon_frame("sink", k - 1, 8)
    images["egg_demon_floor_glow"] = floor_glow()
    expect = {"egg_candle": (96, 128), "egg_candle_glow": (256, 256), "egg_demon": (512, 640), "egg_demon_floor_glow": (640, 512)}
    for name, im in sorted(images.items()):
        want = expect["egg_candle_glow"] if name == "egg_candle_glow" else expect["egg_demon_floor_glow"] if name == "egg_demon_floor_glow" \
            else expect["egg_candle"] if name.startswith("egg_candle") else expect["egg_demon"]
        assert im.size == want, (name, im.size, want)
        im.save(ASSETS / (name + ".png"), optimize=True)
    sheet(images).save(PREVIEW / "sheet.png", optimize=True)
    print(f"{len(images)} Dateien nach {ASSETS}, Uebersicht {PREVIEW / 'sheet.png'}")


if __name__ == "__main__":
    main()
