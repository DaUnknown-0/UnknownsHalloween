# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_art.py - Hollowmere Manor (Spukvilla als Horrorfilm-Set) im Among-Us-Stil: Objekte des Stilblatts.
#
# Gleiche Regeln wie museum_art.py / park_art.py (Unknown's Atlas): kraeftige Umrisse (OUTLINE, OUT_W),
# flache Flaechen mit Licht- und Schattenkante, schraege Aufsicht K = 0,55 (Hoehe z erscheint als y + z*K),
# Standlinie = Kollision, weicher Bodenschatten, 160 px/m. Weltkoordinaten in Metern, y nach oben (Norden).
#
# Palette: verfallene Pracht (dunkles Nussholz, Bordeaux, angelaufenes Messing, Staub, Spinnweben) plus
# Filmset-Technik (mattschwarze Kameras und Scheinwerfer, gelbes Gaffer-Tape, Kabel). Warmes Kerzen- und
# Wolframlicht gegen kaltes Mondlicht. Alle Werte sind fuer 2D angehoben (lift), weil das Spiel alles
# ausserhalb des Sichtkegels abdunkelt: dunkle Stimmung ueber Farbton und Kontrast, nicht ueber Schwarz.
#
# Vertrag: draw(kind, shape, idx, ppm) wie park_art.draw; shape = ("rect", x0, y0, x1, y1) |
# ("circle", cx, cy, r) | ("ellipse", cx, cy, rx, ry) = Kollisionsflaeche am Boden. Rueckgabe
# (PIL.Image RGBA, welt_x_links, welt_y_unten, standlinie_y). idx variiert Details deterministisch.

import math
import os
import random
import sys

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)

import museum_art as A                      # noqa: E402
import handdraw as HD                       # noqa: E402
from museum_art import K, OUTLINE, Prop, alpha, hexc, lift, shade   # noqa: E402

from PIL import Image, ImageDraw            # noqa: E402

# ------------------------------------------------------------------ Palette

WALNUT = lift("#4a3220", 1.7)          # dunkles Nussholz
WALNUT_D = shade(WALNUT, 0.72)
WALNUT_L = shade(WALNUT, 1.25)
BORDEAUX = lift("#561e28", 1.5)        # Damast-Tapete, Samt (seit der Abnahme etwas kuehler und stumpfer)
BORDEAUX_D = shade(BORDEAUX, 0.75)
PLUM = lift("#382444", 1.55)
BRASS = hexc("#ac8a48")                # angelaufenes Messing
BRASS_D = shade(BRASS, 0.68)
BRASS_L = hexc("#dcc27a")
CREAM = hexc("#dcd4bc")
CREAM_D = shade(CREAM, 0.8)
PARCH = hexc("#d0c29c")                # Pergament, Zifferblatt
STONE = lift("#64666c", 1.35)          # Grabstein, Gruft (blaugrau)
STONE_D = shade(STONE, 0.72)
STONE_L = shade(STONE, 1.15)
MARBLE = hexc("#c8c4ba")
IRON = hexc("#4e5058")                 # Gusseisen (Kessel, Herd, Gitter)
IRON_L = shade(IRON, 1.3)
IRON_D = shade(IRON, 0.7)
COPPER = hexc("#a86a44")
BLOOD = hexc("#8a1a22")                # Kunstblut (dunkel, matt)
BLOOD_L = hexc("#b8262e")
CANVAS = hexc("#6a705c")               # Zeltplane, Planen
CANVAS_D = shade(CANVAS, 0.75)
LAMP_GREEN = hexc("#2e6a4a")           # Bankerlampe
LEATHER = hexc("#4a5a44")              # gruenes Schreibtischleder
MATTE = hexc("#34343c")                # mattschwarze Filmtechnik (angehoben)
MATTE_L = hexc("#4e5058")
MATTE_D = hexc("#232328")
STEEL = hexc("#8a8e98")
GAFFER = hexc("#e8c23a")               # gelbes Gaffer-Tape
OLIVE = hexc("#5a6050")                # Aggregat
OLIVE_L = shade(OLIVE, 1.25)
BULB = hexc("#ffe6a8")
CANDLE = hexc("#fff0c2")
FLAME = hexc("#ffb43c")
FLAME_CORE = hexc("#fff4c8")
WARM = hexc("#ffd28a")                 # Wolfram- und Kerzenlicht
MOON = hexc("#b9cde0")                 # kaltes Mondlicht
EMBER = hexc("#ff8a3c")
GLASS = alpha(hexc("#c4d8e8"), 170)
WEB = alpha(hexc("#e8ecf2"), 115)
MOSS = hexc("#6f9a4e")

PROP_H = {"standuhr": 2.3, "seance_tisch": 0.8, "buecherregal": 2.6, "kamin": 1.7, "kandelaber": 1.6,
          "kandelaber_aus": 1.6, "filmkamera": 1.7, "scheinwerfer": 2.0, "schminktisch": 1.9, "sessel": 1.1,
          "sarg": 0.6, "grabstein": 1.0, "aggregat": 2.0, "absperrung": 1.0,
          # seit dem Stilblatt: alle Objektarten aus villa_layout.OPAQUE/GLASS plus die Barrikade
          "freitreppe": 2.6, "herd": 2.0, "funktisch": 1.5, "kisten": 1.7, "kessel": 2.2, "altar": 1.4,
          "monitorwand": 2.1, "gewehrschrank": 2.2, "zelt": 2.6, "hecke": 1.3, "kuechentisch": 1.1,
          "waschzuber": 0.8, "requisiten": 1.7, "teleskop": 1.9, "kohlen": 1.1, "lesetisch": 1.3,
          "kirchenbank": 1.0, "baer": 2.5, "schreibtisch": 1.4, "catering": 1.5, "urne": 1.5,
          "gartenbank": 1.0, "pflanztisch": 1.6, "brunnen": 1.9, "barrikade": 2.0}
KINDS = set(PROP_H)
# Leinwandrand je Objekt (Standard 0,3 m): Lichtkegel, Glutschein und Lichtlachen reichen ueber die Grundflaeche
PROP_PAD = {"scheinwerfer": 2.3, "kamin": 0.8, "kandelaber": 1.3, "kandelaber_aus": 0.5, "aggregat": 0.6,
            "filmkamera": 0.6, "seance_tisch": 0.5, "standuhr": 0.35, "schminktisch": 0.4,
            "lesetisch": 0.7, "schreibtisch": 0.6, "altar": 0.6, "kessel": 0.5, "zelt": 0.6, "funktisch": 0.5,
            "monitorwand": 0.5, "herd": 0.5, "kuechentisch": 0.4, "brunnen": 0.5, "teleskop": 0.4, "catering": 0.4}


# ------------------------------------------------------------------ gemeinsame Teile

def floor_light(c, cx, cy, rx, ry, color, strength=0.45, seed=1):
    """Lichtlache auf dem Boden: weicher elliptischer Verlauf plus flacher, leicht zittriger Kern
    (Cel-Shading: zwei Stufen statt Fotoverlauf), wie park_art.light_pool."""
    w, h = c.px(rx * 2), c.px(ry * 2)
    if w < 4 or h < 4:
        return
    g = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(g)
    steps = 20
    for i in range(steps):
        f = i / steps
        ex, ey = (1 - f) * w / 2, (1 - f) * h / 2
        gd.ellipse([w / 2 - ex, h / 2 - ey, w / 2 + ex, h / 2 + ey], fill=int(255 * strength * (f ** 1.5)))
    layer = Image.new("RGBA", (w, h), color[:3] + (0,))
    layer.putalpha(g)
    x, y = c.p(cx - rx, cy + ry)
    x, y = int(x), int(y)
    cx0, cy0 = max(0, x), max(0, y)
    cx1, cy1 = min(c.w, x + w), min(c.h, y + h)
    if cx1 > cx0 and cy1 > cy0:
        c.img.alpha_composite(layer.crop((cx0 - x, cy0 - y, cx1 - x, cy1 - y)), (cx0, cy0))
    core = HD.wobble_ellipse(cx, cy - ry * 0.05, rx * 0.55, ry * 0.55, amp=0.02, seed=seed)
    c.poly(core, fill=alpha(color, int(255 * strength * 0.35)))


def flame(c, x, y, s=1.0, glow=True):
    """Kerzenflamme (Tropfen nach oben) mit hellem Kern; glow: Lichthof dazu."""
    if glow:
        c.glow(x, y + 0.04 * s, 0.5 * s, WARM, 0.5)
        c.glow(x, y + 0.03 * s, 0.18 * s, CANDLE, 0.8)
    c.poly([(x - 0.03 * s, y), (x + 0.03 * s, y), (x + 0.02 * s, y + 0.06 * s), (x, y + 0.12 * s), (x - 0.02 * s, y + 0.06 * s)],
           fill=FLAME, outline=shade(FLAME, 0.7), width=0.012)
    c.poly([(x - 0.012 * s, y + 0.008), (x + 0.012 * s, y + 0.008), (x, y + 0.055 * s)], fill=FLAME_CORE)


def smoke(c, x, y, seed=0, h=0.35):
    """Duenner Rauchfaden einer erloschenen Kerze (zittrig, nach oben verblassend)."""
    pts = [(x + 0.03 * math.sin(k * 1.9 + seed), y + h * k / 6) for k in range(7)]
    pts = HD.wobble(pts, amp=0.012, seed=seed, step=0.03)
    c.line(pts, fill=alpha((205, 205, 215, 255), 110), width=0.018)
    c.line(pts[3:], fill=alpha((205, 205, 215, 255), 55), width=0.035)


def candle(c, x, y, h, lit, r=0.035, seed=0, smoke_=True):
    """Kerze (Standpunkt x, y im Bild): Creme-Zylinder mit Wachsnasen; brennend mit Flamme, sonst Docht."""
    rnd = random.Random(seed)
    top = y + h
    c.rect(x - r, y, x + r, top, fill=CREAM, outline=OUTLINE, width=0.015)
    c.line([(x - r + 0.008, y + 0.01), (x - r + 0.008, top - 0.01)], fill=shade(CREAM, 1.08), width=0.008)
    c.ellipse(x, top, r, r * 0.45, fill=shade(CREAM, 1.08), outline=OUTLINE, width=0.015)
    for _ in range(2):
        wx = x + rnd.choice((-1, 1)) * r * 0.75
        wy = top - rnd.uniform(0.02, max(0.03, h * 0.5))
        c.line([(wx, top - 0.01), (wx, wy)], fill=shade(CREAM, 1.05), width=0.014)
        c.ellipse(wx, wy, 0.013, 0.01, fill=shade(CREAM, 1.05))
    if lit:
        flame(c, x, top + 0.01)
    else:
        c.line([(x, top), (x, top + 0.025)], fill=OUTLINE, width=0.012)
        if smoke_:
            smoke(c, x, top + 0.03, seed)


def cobweb(c, x, y, size, qx, qy, seed=0):
    """Spinnwebe in einer Ecke bei (x, y); qx/qy (+1/-1) = Richtung, in die sich die Webe spannt."""
    rnd = random.Random(seed)
    n = 5
    for k in range(n + 1):
        a = (math.pi / 2) * k / n
        c.line([(x, y), (x + qx * size * math.cos(a), y + qy * size * math.sin(a))], fill=WEB, width=0.008)
    for r in (0.3, 0.55, 0.8, 1.0):
        pts = []
        for k in range(n + 1):
            a = (math.pi / 2) * k / n
            rr = r * size * rnd.uniform(0.88, 1.0)
            pts.append((x + qx * rr * math.cos(a), y + qy * rr * math.sin(a)))
        c.line(pts, fill=WEB, width=0.007)


def gaffer(c, x0, y0, x1, y1, w=0.05):
    """Streifen gelbes Gaffer-Tape."""
    c.line([(x0, y0), (x1, y1)], fill=GAFFER, width=w)
    c.line([(x0, y0), (x1, y1)], fill=alpha(shade(GAFFER, 0.8), 120), width=w * 0.25)


def cable(c, pts, seed=0, w=0.035, col=MATTE_D):
    """Kabel: zittrige Linie, dunkel mit schmalem Glanzstreifen."""
    pts = HD.wobble(pts, amp=0.015, seed=seed, step=0.06)
    c.line(pts, fill=alpha((0, 0, 0, 255), 60), width=w * 1.8)
    c.line(pts, fill=col, width=w)
    c.line(pts, fill=alpha(STEEL, 110), width=w * 0.3)


def moss(c, x, y, r, seed=0, col=MOSS):
    rnd = random.Random(seed)
    for _ in range(4):
        c.ellipse(x + rnd.uniform(-r, r), y + rnd.uniform(-r * 0.5, r * 0.5), r * rnd.uniform(0.3, 0.6),
                  r * rnd.uniform(0.2, 0.4), fill=alpha(col, 165))


def crack(c, pts, seed=0, col=None):
    c.line(HD.wobble(pts, amp=0.012, seed=seed, step=0.04), fill=col or alpha(OUTLINE, 190), width=0.012)


def dust(c, x0, y0, x1, y1, n, seed=0):
    """Helle Staubpunkte auf einer Deckflaeche."""
    rnd = random.Random(seed)
    for _ in range(n):
        c.ellipse(rnd.uniform(x0, x1), rnd.uniform(y0, y1), 0.008, 0.006, fill=alpha(CREAM, 120))


# ------------------------------------------------------------------ die Objekte

def _standuhr(p, c, x0, y0, x1, y1, idx, rnd):
    w = x1 - x0
    cx = (x0 + x1) / 2
    p.box(x0, y0, x1, y1, 0, 0.3, WALNUT_L, WALNUT_D)                               # Sockel
    tx0, tx1 = x0 + w * 0.12, x1 - w * 0.12
    fy = y0 + 0.04
    p.box(tx0, fy, tx1, y1 - 0.04, 0.3, 1.25, WALNUT_L, WALNUT)                    # Rumpf
    # Pendelfenster: dunkles Glas im Messingrahmen, Pendel mit Glanz, Glasreflex
    gx0, gx1 = tx0 + 0.06, tx1 - 0.06
    gz0, gz1 = 0.45, 1.4
    c.rect(gx0, fy + gz0 * K, gx1, fy + gz1 * K, fill=hexc("#2a2430"), outline=BRASS_D, width=0.02)
    c.line([(cx, fy + (gz1 - 0.05) * K), (cx, fy + (gz0 + 0.2) * K)], fill=BRASS, width=0.015)
    c.ellipse(cx, fy + (gz0 + 0.2) * K, 0.07, 0.06, fill=BRASS, outline=BRASS_D, width=0.015)
    c.ellipse(cx - 0.02, fy + (gz0 + 0.24) * K, 0.02, 0.015, fill=BRASS_L)
    c.line([(gx0 + 0.02, fy + gz1 * K - 0.03), (gx0 + 0.02, fy + gz0 * K + 0.12)], fill=alpha((255, 255, 255, 255), 55), width=0.012)
    # Kopf mit Zifferblatt (Messinglunette, Pergament, Striche, Zeiger kurz vor Mitternacht)
    hx0, hx1 = x0 + w * 0.04, x1 - w * 0.04
    hy = y0 + 0.02
    p.box(hx0, hy, hx1, y1 - 0.02, 1.55, 0.55, WALNUT_L, WALNUT)
    fr = min(w * 0.36, 0.26)
    fcx, fcy = cx, hy + 1.82 * K
    c.ellipse(fcx, fcy, fr, fr * 0.9, fill=BRASS, outline=OUTLINE, width=0.025)
    c.ellipse(fcx, fcy, fr * 0.84, fr * 0.84 * 0.9, fill=PARCH, outline=BRASS_D, width=0.012)
    for k in range(12):
        a = k * math.pi / 6
        r1 = fr * 0.84 * (0.76 if k % 3 == 0 else 0.86)
        c.line([(fcx + r1 * math.cos(a), fcy + r1 * 0.9 * math.sin(a)),
                (fcx + fr * 0.8 * math.cos(a), fcy + fr * 0.8 * 0.9 * math.sin(a))],
               fill=OUTLINE, width=0.02 if k % 3 == 0 else 0.012)
    minute = 50 + (idx * 7) % 10
    ah = math.pi / 2 - (11 + minute / 60) / 12 * math.tau
    am = math.pi / 2 - minute / 60 * math.tau
    c.line([(fcx, fcy), (fcx + fr * 0.45 * math.cos(ah), fcy + fr * 0.45 * 0.9 * math.sin(ah))], fill=OUTLINE, width=0.025)
    c.line([(fcx, fcy), (fcx + fr * 0.68 * math.cos(am), fcy + fr * 0.68 * 0.9 * math.sin(am))], fill=OUTLINE, width=0.018)
    c.ellipse(fcx, fcy, 0.02, 0.018, fill=BRASS_D)
    # Krone: geschwungener Giebel mit Knauf; Spinnwebe und Staub an der Haube
    top = hy + 2.1 * K
    c.poly([(hx0 - 0.02, top), (hx1 + 0.02, top), (hx1 + 0.02, top + 0.05), (cx + 0.12, top + 0.05), (cx + 0.06, top + 0.14),
            (cx, top + 0.11), (cx - 0.06, top + 0.14), (cx - 0.12, top + 0.05), (hx0 - 0.02, top + 0.05)],
           fill=WALNUT_L, outline=OUTLINE, width=0.03)
    c.line([(cx, top + 0.11), (cx, top + 0.2)], fill=OUTLINE, width=0.025)
    c.ellipse(cx, top + 0.21, 0.03, 0.03, fill=BRASS, outline=OUTLINE, width=0.015)
    cobweb(c, hx1 + 0.02, top + 0.05, 0.16, -1, -1, seed=idx)
    dust(c, hx0 + 0.05, top + 0.06, hx1 - 0.05, y1 - 0.04 + 2.1 * K, 6, seed=idx)


def _seance_tisch(p, c, x0, y0, x1, y1, idx, rnd):
    w, d = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = w / 2, d / 2
    cloth = PLUM if idx % 2 == 0 else BORDEAUX
    p.cyl(cx, cy, rx, 0, 0.8, shade(cloth, 1.15), cloth, ry=ry)
    yb = cy
    for k in range(7):                                                                 # Falten
        t = math.pi + (k + 0.5) * math.pi / 7
        fx, fy = cx + rx * 0.92 * math.cos(t), yb + ry * math.sin(t)
        c.line([(fx, fy + 0.08), (fx + 0.02 * (1 if k % 2 else -1), yb + 0.8 * K - 0.1)], fill=shade(cloth, 0.78), width=0.02)
    c.line([(cx + rx * math.cos(math.pi + k * math.pi / 40), yb + 0.1 + ry * math.sin(math.pi + k * math.pi / 40)) for k in range(41)],
           fill=BRASS_D, width=0.014)                                                  # Saumborte
    for k in range(26):                                                                # Goldfransen
        t = math.pi + (k + 0.5) * math.pi / 26
        fx, fy = cx + rx * math.cos(t), yb + ry * math.sin(t)
        c.line([(fx, fy + 0.1), (fx, fy + 0.03)], fill=BRASS, width=0.012)
    yt = cy + 0.8 * K
    f = ry / rx
    # Ouija-Brett: Pergament mit Buchstabenboegen, Zahlenreihe, Sonne und Mond; Planchette daneben
    bw, bh = min(0.62, rx * 0.65), min(0.42, rx * 0.44) * f * 1.4
    bx, by = cx - rx * 0.15, yt + ry * 0.05
    c.rect(bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2, fill=PARCH, outline=OUTLINE, width=0.02)
    c.rect(bx - bw / 2 + 0.03, by - bh / 2 + 0.02, bx + bw / 2 - 0.03, by + bh / 2 - 0.02, outline=WALNUT_D, width=0.008)
    for arc_r in (bw * 0.42, bw * 0.3):
        for k in range(13):
            t = math.pi * 0.15 + math.pi * 0.7 * k / 12
            lx, ly = bx + arc_r * math.cos(t), by - bh * 0.3 + arc_r * 0.55 * math.sin(t)
            c.line([(lx, ly - 0.012), (lx, ly + 0.012)], fill=WALNUT_D, width=0.01)
    for k in range(10):
        lx = bx - bw * 0.36 + bw * 0.72 * k / 9
        c.line([(lx, by - bh * 0.36), (lx, by - bh * 0.36 + 0.02)], fill=WALNUT_D, width=0.01)
    c.ellipse(bx - bw * 0.4, by + bh * 0.3, 0.035, 0.03, fill=BRASS, outline=WALNUT_D, width=0.008)
    c.ellipse(bx + bw * 0.4, by + bh * 0.3, 0.035, 0.03, fill=CREAM, outline=WALNUT_D, width=0.008)
    c.ellipse(bx + bw * 0.4 + 0.015, by + bh * 0.3 + 0.005, 0.03, 0.026, fill=PARCH)
    px_, py_ = bx + bw * 0.12, by - bh * 0.02
    c.poly([(px_ - 0.08, py_ + 0.03), (px_ - 0.05, py_ + 0.06), (px_, py_ + 0.04), (px_ + 0.05, py_ + 0.06), (px_ + 0.08, py_ + 0.03), (px_, py_ - 0.07)],
           fill=WALNUT, outline=OUTLINE, width=0.015)
    c.ellipse(px_, py_ + 0.01, 0.022, 0.018, fill=GLASS, outline=BRASS_D, width=0.008)
    # Kristallkugel auf Messingfuss mit kaltem Schein
    kx, ky = cx + rx * 0.55, yt + ry * 0.1
    c.ellipse(kx, ky - 0.02, 0.1, 0.045, fill=BRASS, outline=OUTLINE, width=0.015)
    c.glow(kx, ky + 0.13, 0.42, hexc("#b8a8ff"), 0.5)
    c.ellipse(kx, ky + 0.13, 0.12, 0.12, fill=alpha(hexc("#cfd6f4"), 225), outline=OUTLINE, width=0.02)
    c.ellipse(kx + 0.02, ky + 0.1, 0.05, 0.04, fill=alpha(hexc("#9a8cff"), 90))
    c.ellipse(kx - 0.04, ky + 0.17, 0.035, 0.025, fill=alpha((255, 255, 255, 255), 190))
    # Tarotkarten und drei Kerzen auf Messingstaendern
    for k in range(3):
        tx, ty = cx + rx * 0.12 + k * 0.09, yt - ry * 0.55 + k * 0.012
        c.rect(tx - 0.035, ty - 0.03, tx + 0.035, ty + 0.03, fill=hexc("#2e3a68") if k < 2 else PARCH, outline=OUTLINE, width=0.01)
        if k < 2:
            c.rect(tx - 0.025, ty - 0.02, tx + 0.025, ty + 0.02, outline=BRASS, width=0.006)
        else:
            c.ellipse(tx, ty, 0.015, 0.012, fill=BRASS)
    for k, (sx, sy, hh) in enumerate(((cx - rx * 0.62, yt + ry * 0.25, 0.16), (cx - rx * 0.5, yt - ry * 0.3, 0.12), (cx + rx * 0.2, yt + ry * 0.55, 0.14))):
        c.ellipse(sx, sy, 0.05, 0.025, fill=BRASS, outline=OUTLINE, width=0.012)
        c.line([(sx, sy), (sx, sy + 0.1)], fill=OUTLINE, width=0.035)
        c.line([(sx, sy), (sx, sy + 0.1)], fill=BRASS, width=0.02)
        candle(c, sx, sy + 0.1, hh, True, r=0.028, seed=idx * 3 + k)


def _buecherregal(p, c, x0, y0, x1, y1, idx, rnd):
    H = 2.6
    p.box(x0, y0, x1, y1, 0, H, WALNUT_L, WALNUT)
    ix0, ix1 = x0 + 0.07, x1 - 0.07
    c.rect(ix0, y0 + 0.08 * K, ix1, y0 + 2.42 * K, fill=shade(WALNUT_D, 0.8))        # Rueckwand im Schatten
    cols = [lift("#5a1e22", 1.5), lift("#1e3a2a", 1.6), lift("#1e2a4a", 1.6), hexc("#b48a3c"), lift("#4a3020", 1.5),
            CREAM_D, hexc("#2c2a30"), lift("#4a2a52", 1.5)]
    for si in range(5):
        z = 0.12 + si * 0.5
        sy = y0 + z * K
        c.rect(ix0 - 0.02, sy, ix1 + 0.02, sy + 0.04, fill=WALNUT_L, outline=OUTLINE, width=0.015)     # Brett
        c.line([(ix0, sy - 0.012), (ix1, sy - 0.012)], fill=alpha((0, 0, 0, 255), 90), width=0.02)
        by0 = sy + 0.04
        xa = ix0 + 0.03
        while xa < ix1 - 0.05:
            u = rnd.random()
            if u < 0.08:                                                               # Luecke
                xa += rnd.uniform(0.05, 0.15)
                continue
            if u < 0.17 and xa < ix1 - 0.3:                                            # liegender Stapel
                for k in range(rnd.randint(2, 4)):
                    bw = rnd.uniform(0.16, 0.24)
                    c.rect(xa, by0 + k * 0.035, xa + bw, by0 + (k + 1) * 0.035, fill=rnd.choice(cols), outline=OUTLINE, width=0.012)
                xa += 0.28
                continue
            if u < 0.22 and si in (1, 3) and xa < ix1 - 0.2:                           # Deko: Glas oder Kerze
                if si == 1:
                    c.rect(xa + 0.01, by0, xa + 0.09, by0 + 0.12, fill=alpha(hexc("#6aa07a"), 190), outline=OUTLINE, width=0.012)
                    c.ellipse(xa + 0.05, by0 + 0.12, 0.04, 0.015, fill=hexc("#8ab890"), outline=OUTLINE, width=0.012)
                    c.ellipse(xa + 0.05, by0 + 0.05, 0.02, 0.025, fill=alpha(hexc("#2e4a30"), 160))
                else:
                    candle(c, xa + 0.05, by0, 0.1, False, r=0.025, seed=idx + si, smoke_=False)
                xa += 0.14
                continue
            bw = rnd.uniform(0.035, 0.08)
            bh = rnd.uniform(0.2, 0.34) * K * 1.35
            lean = rnd.uniform(-0.025, 0.025) if rnd.random() < 0.25 else 0.0
            col = rnd.choice(cols)
            c.poly([(xa, by0), (xa + bw, by0), (xa + bw + lean, by0 + bh), (xa + lean, by0 + bh)], fill=col, outline=OUTLINE, width=0.012)
            if rnd.random() < 0.7:
                for fz in (0.82, 0.72):
                    c.line([(xa + 0.008 + lean * fz, by0 + bh * fz), (xa + bw - 0.008 + lean * fz, by0 + bh * fz)], fill=BRASS_L, width=0.006)
            xa += bw + 0.006
    c.rect(x0, y0 + 2.46 * K, x1, y0 + 2.6 * K, fill=WALNUT_L, outline=OUTLINE, width=0.02)           # Kranzgesims
    c.line([(x0 + 0.02, y0 + 2.5 * K), (x1 - 0.02, y0 + 2.5 * K)], fill=WALNUT_D, width=0.012)
    cobweb(c, ix0, y0 + 2.42 * K, 0.22, 1, -1, seed=idx)
    dust(c, x0 + 0.05, y0 + 2.6 * K + 0.03, x1 - 0.05, y1 + 2.6 * K - 0.03, 10, seed=idx + 1)


def _kamin(p, c, x0, y0, x1, y1, idx, rnd):
    w = x1 - x0
    cx = (x0 + x1) / 2
    stone = MARBLE if idx % 2 == 0 else STONE_L
    floor_light(c, cx, y0 - 0.25, 1.2, 0.5, EMBER, 0.35, seed=idx)                    # Glutschein davor
    p.box(x0, y0, x1, y1, 0, 1.5, shade(stone, 1.05), stone)
    for k in range(4):                                                                 # Marmoradern
        vx = rnd.uniform(x0 + 0.05, x1 - 0.05)
        c.line(HD.wobble([(vx, y0 + 0.05), (vx + rnd.uniform(-0.2, 0.2), y0 + 1.45 * K)], amp=0.03, seed=idx * 5 + k, step=0.05),
               fill=alpha(shade(stone, 0.7), 120), width=0.01)
    # Feuerraum mit Rundbogen, innen russschwarz; Glutbett, Scheite, Flammen, Feuerboecke
    ox0, ox1 = x0 + w * 0.22, x1 - w * 0.22
    oy0, oy1 = y0 + 0.08 * K, y0 + 1.0 * K
    inner = hexc("#2a1c18")
    c.rect(ox0, oy0, ox1, oy1 - 0.12, fill=inner, outline=OUTLINE, width=0.03)
    c.ellipse(cx, oy1 - 0.12, (ox1 - ox0) / 2, 0.14, fill=inner, outline=OUTLINE, width=0.03)
    c.rect(ox0 + 0.016, oy0 + 0.016, ox1 - 0.016, oy1 - 0.12, fill=inner)
    c.glow(cx, oy0 + 0.1, 0.75, EMBER, 0.75)
    c.glow(cx, oy0 + 0.08, 0.35, hexc("#ffd060"), 0.8)
    c.ellipse(cx, oy0 + 0.06, (ox1 - ox0) * 0.42, 0.05, fill=hexc("#ff7a30"))
    for _ in range(14):
        c.ellipse(cx + rnd.uniform(-(ox1 - ox0) * 0.38, (ox1 - ox0) * 0.38), oy0 + 0.06 + rnd.uniform(-0.03, 0.03), 0.015, 0.01, fill=hexc("#ffd060"))
    for (lx0, lz0, lx1, lz1) in ((cx - 0.3, 0.1, cx + 0.25, 0.2), (cx - 0.22, 0.2, cx + 0.3, 0.12)):
        c.line([(lx0, y0 + lz0 * K + 0.02), (lx1, y0 + lz1 * K + 0.02)], fill=OUTLINE, width=0.1)
        c.line([(lx0, y0 + lz0 * K + 0.02), (lx1, y0 + lz1 * K + 0.02)], fill=lift("#4a2e1c", 1.4), width=0.07)
        c.line([(lx0 + 0.05, y0 + lz0 * K + 0.03), (lx1 - 0.05, y0 + lz1 * K + 0.03)], fill=alpha(EMBER, 150), width=0.02)
    for k, fx in enumerate((cx - 0.15, cx + 0.02, cx + 0.17)):
        flame(c, fx, oy0 + 0.1, s=1.5 if k == 1 else 1.1, glow=False)
    for ax in (ox0 + 0.1, ox1 - 0.1):
        c.line([(ax, oy0 + 0.02), (ax, oy0 + 0.18)], fill=BRASS_D, width=0.025)
        c.ellipse(ax, oy0 + 0.19, 0.025, 0.02, fill=BRASS, outline=OUTLINE, width=0.01)
    c.ellipse(cx, oy1 + 0.1, (ox1 - ox0) * 0.4, 0.07, fill=alpha((20, 14, 10, 255), 70))              # Russ
    # Sims als eigener Vorsprung; darauf Kerzen und eine Urne; Spinnwebe unter dem Sims
    p.box(x0 - 0.05, y0 - 0.04, x1 + 0.05, y1, 1.5, 0.12, shade(stone, 1.12), shade(stone, 0.9))
    sy = y0 + 0.2 + 1.62 * K
    for k, sx in enumerate((x0 + 0.3, x1 - 0.3)):
        c.ellipse(sx, sy, 0.05, 0.025, fill=BRASS, outline=OUTLINE, width=0.012)
        c.line([(sx, sy), (sx, sy + 0.12)], fill=OUTLINE, width=0.035)
        c.line([(sx, sy), (sx, sy + 0.12)], fill=BRASS, width=0.02)
        candle(c, sx, sy + 0.12, 0.14 if k == 0 else 0.1, True, r=0.028, seed=idx * 3 + k)
    c.ellipse(cx, sy + 0.02, 0.08, 0.035, fill=BRASS_D, outline=OUTLINE, width=0.012)
    c.poly([(cx - 0.08, sy + 0.03), (cx + 0.08, sy + 0.03), (cx + 0.05, sy + 0.2), (cx + 0.04, sy + 0.26), (cx - 0.04, sy + 0.26), (cx - 0.05, sy + 0.2)],
           fill=BRASS, outline=OUTLINE, width=0.015)
    c.line([(cx - 0.03, sy + 0.06), (cx - 0.03, sy + 0.18)], fill=BRASS_L, width=0.01)
    cobweb(c, x1 + 0.05, y0 - 0.04 + 1.5 * K, 0.2, -1, -1, seed=idx + 2)


def _kandelaber(p, c, x0, y0, x1, y1, idx, rnd, lit=True):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    if lit:
        floor_light(c, cx, cy - 0.05, 1.15, 0.65, WARM, 0.42, seed=idx)
    c.ellipse(cx, cy, r, r * 0.5, fill=BRASS_D, outline=OUTLINE, width=0.025)              # Fuss
    c.ellipse(cx, cy + 0.03, r * 0.55, r * 0.28, fill=BRASS, outline=OUTLINE, width=0.02)
    top = cy + 1.2 * K
    c.line([(cx, cy + 0.02), (cx, top + 0.1)], fill=OUTLINE, width=0.06)
    c.line([(cx, cy + 0.02), (cx, top + 0.1)], fill=BRASS, width=0.035)
    c.line([(cx - 0.008, cy + 0.1), (cx - 0.008, top)], fill=BRASS_L, width=0.008)
    for z in (0.35, 0.75):                                                                  # Knaeufe
        c.ellipse(cx, cy + z * K, 0.035, 0.025, fill=BRASS, outline=OUTLINE, width=0.015)
    arms = [(cx, top + 0.1)]
    for sx in (-1, 1):                                                                      # geschwungene Arme
        pts = [(cx, top - 0.05), (cx + sx * 0.1, top - 0.08), (cx + sx * 0.2, top), (cx + sx * 0.21, top + 0.06)]
        c.line(pts, fill=OUTLINE, width=0.045)
        c.line(pts, fill=BRASS, width=0.025)
        arms.append((cx + sx * 0.21, top + 0.06))
    for k, (ax, ay) in enumerate(arms):
        c.ellipse(ax, ay, 0.045, 0.02, fill=BRASS, outline=OUTLINE, width=0.015)            # Tropfschale
        candle(c, ax, ay, 0.16 if k == 0 else 0.12, lit, r=0.028, seed=idx * 7 + k)


def _filmkamera(p, c, x0, y0, x1, y1, idx, rnd):
    w = x1 - x0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    dir_ = -1 if idx % 2 == 0 else 1
    for wx in (x0 + 0.14, x1 - 0.14):                                                      # Rollen
        c.ellipse(wx, y0 + 0.06, 0.08, 0.06, fill=MATTE_D, outline=OUTLINE, width=0.02)
        c.ellipse(wx, y0 + 0.06, 0.03, 0.022, fill=STEEL)
    p.box(x0, y0 + 0.02, x1, y1, 0.1, 0.16, MATTE_L, MATTE)                               # Dolly-Plattform
    gaffer(c, x0 + 0.1, y0 + 0.02 + 0.18 * K, x0 + 0.4, y0 + 0.02 + 0.18 * K, 0.04)
    bx = cx - dir_ * (w * 0.42)                                                            # Schubbuegel hinten
    bar = [(bx, y1 - 0.05 + 0.26 * K), (bx, y1 - 0.05 + 1.0 * K), (bx - dir_ * 0.1, y1 - 0.05 + 1.05 * K)]
    c.line(bar, fill=OUTLINE, width=0.05)
    c.line(bar, fill=STEEL, width=0.025)
    p.cyl(cx, cy, 0.07, 0.26, 0.86, MATTE_L, MATTE, ry=0.035)                              # Saeule mit Kurbel
    c.line([(cx + 0.07, cy + 0.7 * K), (cx + 0.16, cy + 0.72 * K)], fill=OUTLINE, width=0.03)
    c.ellipse(cx + 0.16, cy + 0.72 * K, 0.025, 0.02, fill=BRASS, outline=OUTLINE, width=0.012)
    p.box(cx - 0.12, cy - 0.08, cx + 0.12, cy + 0.08, 1.12, 0.1, MATTE_L, MATTE_D, w=0.03)  # Kopf
    bz0, bh = 1.22, 0.3
    bx0, bx1 = cx - 0.28, cx + 0.28
    byf = cy - 0.12
    p.box(bx0, byf, bx1, cy + 0.12, bz0, bh, MATTE_L, MATTE)                               # Kamerakoerper
    fz = byf + (bz0 + bh / 2) * K
    lx = bx1 if dir_ > 0 else bx0                                                          # Objektiv
    le = lx + dir_ * 0.26
    c.poly([(lx, fz - 0.06), (le, fz - 0.07), (le, fz + 0.07), (lx, fz + 0.06)], fill=MATTE_D, outline=OUTLINE, width=0.025)
    for fr in (0.08, 0.16):
        c.line([(lx + dir_ * fr, fz - 0.062), (lx + dir_ * fr, fz + 0.062)], fill=STEEL, width=0.012)
    c.ellipse(le, fz, 0.025, 0.07, fill=hexc("#3a4e6a"), outline=OUTLINE, width=0.02)
    c.ellipse(le - dir_ * 0.005, fz + 0.02, 0.01, 0.025, fill=alpha(hexc("#cfe4ff"), 180))
    mx0, mx1 = le + dir_ * 0.02, le + dir_ * 0.14                                          # Kompendium
    c.poly([(mx0, fz - 0.1), (mx1, fz - 0.13), (mx1, fz + 0.13), (mx0, fz + 0.1)], fill=MATTE, outline=OUTLINE, width=0.025)
    c.line([(mx1, fz - 0.13), (mx1, fz + 0.13)], fill=MATTE_L, width=0.02)
    tz = byf + (bz0 + bh) * K                                                              # Filmmagazin
    for k in (-1, 1):
        c.ellipse(cx + k * 0.11 - dir_ * 0.04, tz + 0.1, 0.11, 0.1, fill=MATTE, outline=OUTLINE, width=0.025)
        c.ellipse(cx + k * 0.11 - dir_ * 0.04, tz + 0.1, 0.06, 0.055, fill=MATTE_L, outline=OUTLINE, width=0.012)
    vx = bx0 if dir_ > 0 else bx1                                                          # Sucher hinten
    c.line([(vx, fz + 0.09), (vx - dir_ * 0.1, fz + 0.14)], fill=OUTLINE, width=0.05)
    c.line([(vx, fz + 0.09), (vx - dir_ * 0.1, fz + 0.14)], fill=MATTE_L, width=0.03)
    c.ellipse(vx - dir_ * 0.11, fz + 0.145, 0.025, 0.02, fill=MATTE_D, outline=OUTLINE, width=0.012)
    c.glow(vx + dir_ * 0.06, fz + 0.1, 0.08, hexc("#ff4040"), 0.8)                         # REC-Lampe
    c.ellipse(vx + dir_ * 0.06, fz + 0.1, 0.012, 0.012, fill=hexc("#ff5050"))
    gaffer(c, cx - 0.1, fz - 0.08, cx + 0.1, fz - 0.08, 0.035)
    cable(c, [(vx - dir_ * 0.02, fz - 0.05), (vx - dir_ * 0.15, fz - 0.4), (vx - dir_ * 0.2, y0 - 0.05), (vx - dir_ * 0.5, y0 - 0.1)], seed=idx)


def _scheinwerfer(p, c, x0, y0, x1, y1, idx, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    dir_ = -1 if idx % 2 == 0 else 1
    col = (WARM, MOON, MOON)[idx % 3]              # mehr kaltes Mondlicht als warmes Wolfram
    hx, hy = cx, cy + 1.75 * K
    fx = hx + dir_ * 0.17
    ex, ey = cx + dir_ * 1.9, cy - 0.35
    floor_light(c, ex, ey, 1.0, 0.5, col, 0.5, seed=idx)                                  # Lichtkegel auf dem Boden
    for s, a_ in ((1.0, 26), (0.7, 26), (0.4, 28)):
        c.poly([(fx, hy + 0.08), (ex + dir_ * 0.9 * s, ey + 0.35 * s), (ex + dir_ * 1.0 * s, ey), (ex + dir_ * 0.9 * s, ey - 0.35 * s),
                (ex - dir_ * 0.2 * s, ey - 0.5 * s), (fx, hy - 0.08)], fill=alpha(col, a_))
    for (lx, ly) in ((cx - 0.3, cy - 0.22), (cx + 0.3, cy - 0.2), (cx + 0.05, cy + 0.3)):     # Stativbeine
        c.line([(cx, cy + 0.55 * K), (lx, ly)], fill=OUTLINE, width=0.05)
        c.line([(cx, cy + 0.55 * K), (lx, ly)], fill=MATTE_L, width=0.025)
        c.ellipse(lx, ly, 0.035, 0.02, fill=MATTE_D, outline=OUTLINE, width=0.012)
    sx, sy = cx + 0.18, cy - 0.1 + 0.3 * K                                                 # Sandsack
    c.poly(HD.wobble_ellipse(sx, sy, 0.1, 0.06, amp=0.01, seed=idx), fill=lift("#4a3a2a", 1.5), outline=OUTLINE, width=0.02)
    c.line([(sx - 0.08, sy + 0.005), (sx + 0.08, sy + 0.005)], fill=OUTLINE, width=0.012)
    c.line([(cx, cy), (cx, hy - 0.05)], fill=OUTLINE, width=0.07)                            # Saeule
    c.line([(cx, cy), (cx, hy - 0.05)], fill=MATTE_L, width=0.04)
    c.line([(cx - 0.01, cy + 0.1), (cx - 0.01, hy - 0.1)], fill=alpha(STEEL, 150), width=0.008)
    c.ellipse(cx, cy + 0.9 * K, 0.04, 0.03, fill=MATTE_D, outline=OUTLINE, width=0.015)
    gaffer(c, cx - 0.05, cy + 0.6 * K, cx + 0.05, cy + 0.63 * K, 0.05)
    c.line([(cx, hy - 0.05), (cx - dir_ * 0.1, hy - 0.08), (cx - dir_ * 0.1, hy)], fill=OUTLINE, width=0.04)   # Buegel
    bx0, bx1 = min(hx - dir_ * 0.2, fx), max(hx - dir_ * 0.2, fx)
    c.rect(bx0, hy - 0.11, bx1, hy + 0.11, fill=MATTE, outline=OUTLINE, width=0.03)          # Lampenkopf
    c.ellipse(hx - dir_ * 0.2, hy, 0.05, 0.11, fill=MATTE_L, outline=OUTLINE, width=0.03)
    for k in range(3):
        vx = hx - dir_ * 0.1 + dir_ * k * 0.04
        c.line([(vx, hy + 0.06), (vx, hy + 0.09)], fill=MATTE_D, width=0.012)
    c.glow(fx, hy, 0.5, col, 0.8)
    c.ellipse(fx, hy, 0.04, 0.11, fill=shade(col, 1.05), outline=OUTLINE, width=0.025)       # Fresnel-Linse
    c.ellipse(fx, hy, 0.02, 0.06, fill=hexc("#ffffff"))
    for k in range(2):
        c.ellipse(fx, hy, 0.03 - k * 0.01, 0.09 - k * 0.025, outline=alpha(OUTLINE, 110), width=0.006)
    for sgn in (1, -1):                                                                     # Torbleche
        c.line([(fx, hy + sgn * 0.11), (fx + dir_ * 0.1, hy + sgn * 0.2)], fill=OUTLINE, width=0.04)
        c.line([(fx, hy + sgn * 0.11), (fx + dir_ * 0.1, hy + sgn * 0.2)], fill=MATTE_L, width=0.02)
    cable(c, [(hx - dir_ * 0.2, hy - 0.08), (cx - dir_ * 0.1, cy + 1.0 * K), (cx + dir_ * 0.05, cy + 0.3 * K),
              (cx - dir_ * 0.3, cy - 0.15), (cx - dir_ * 0.7, cy - 0.2)], seed=idx + 3)


def _schminktisch(p, c, x0, y0, x1, y1, idx, rnd):
    w = x1 - x0
    cx = (x0 + x1) / 2
    p.box(x0, y0, x1, y1, 0, 0.75, WALNUT_L, WALNUT)
    n = 3
    for k in range(n):                                                                      # Schubladen
        dx0 = x0 + 0.06 + k * (w - 0.12) / n
        dx1 = dx0 + (w - 0.12) / n - 0.05
        c.rect(dx0, y0 + 0.2 * K, dx1, y0 + 0.62 * K, outline=WALNUT_D, width=0.015)
        c.ellipse((dx0 + dx1) / 2, y0 + 0.41 * K, 0.02, 0.016, fill=BRASS, outline=OUTLINE, width=0.01)
    mx0, mx1 = x0 + 0.08, x1 - 0.08                                                        # Spiegelaufsatz
    my = y1 - 0.06
    p.box(mx0, my, mx1, y1, 0.75, 1.15, MATTE_L, hexc("#3a2e26"))
    gy0, gy1 = my + 0.9 * K, my + 1.8 * K
    gx0, gx1 = mx0 + 0.14, mx1 - 0.14
    c.rect(gx0, gy0, gx1, gy1, fill=hexc("#aebfd0"), outline=OUTLINE, width=0.02)
    c.line([(gx0 + 0.1, gy0 + 0.05), (gx0 + 0.35, gy1 - 0.05)], fill=alpha((255, 255, 255, 255), 110), width=0.05)
    c.line([(gx0 + 0.45, gy0 + 0.05), (gx0 + 0.6, gy1 - 0.1)], fill=alpha((255, 255, 255, 255), 70), width=0.03)
    if idx % 2 == 1:                                                                        # Sprung im Spiegel
        crack(c, [(gx1 - 0.15, gy1), (gx1 - 0.3, gy0 + 0.2), (gx1 - 0.2, gy0)], seed=idx)
        crack(c, [(gx1 - 0.3, gy0 + 0.2), (gx1 - 0.45, gy0 + 0.1)], seed=idx + 1)
    pts = [(gx0 - 0.07, gy0 + 0.08 + k * (gy1 - gy0 - 0.16) / 4) for k in range(5)]
    pts += [(gx1 + 0.07, gy0 + 0.08 + k * (gy1 - gy0 - 0.16) / 4) for k in range(5)]
    nb = max(3, int((gx1 - gx0) / 0.16))
    pts += [(gx0 + (gx1 - gx0) * (k + 0.5) / nb, gy1 + 0.07) for k in range(nb)]
    c.glow(cx, (gy0 + gy1) / 2, 0.9, WARM, 0.25)
    for k, (bx, by) in enumerate(pts):                                                      # Gluehbirnen, einzelne durchgebrannt
        dead = (k * 7 + idx) % 11 == 0
        if not dead:
            c.glow(bx, by, 0.16, BULB, 0.5)
        c.ellipse(bx, by, 0.03, 0.03, fill=(BULB if not dead else hexc("#6a6050")), outline=OUTLINE, width=0.012)
    ty = y0 + 0.75 * K                                                                      # Krimskrams auf der Platte
    for k, (ox, col) in enumerate(((0.2, hexc("#c83a3a")), (0.32, hexc("#5a7a9a")), (0.42, hexc("#e0d0a0")))):
        bx = x0 + ox
        c.rect(bx - 0.025, ty + 0.12, bx + 0.025, ty + 0.12 + 0.1 - k * 0.015, fill=col, outline=OUTLINE, width=0.012)
        c.rect(bx - 0.015, ty + 0.22 - k * 0.015, bx + 0.015, ty + 0.25 - k * 0.015, fill=MATTE_D, outline=OUTLINE, width=0.01)
    c.line([(x0 + 0.2, ty + 0.1), (x0 + 0.2, ty + 0.05)], fill=hexc("#c83a3a"), width=0.012)                         # Kunstblut-Tropfen
    c.ellipse(x0 + 0.21, ty + 0.05, 0.015, 0.01, fill=hexc("#c83a3a"))
    c.ellipse(cx - 0.1, ty + 0.2, 0.07, 0.04, fill=PARCH, outline=OUTLINE, width=0.012)                                # Puderdose
    c.line([(cx + 0.1, ty + 0.16), (cx + 0.3, ty + 0.26)], fill=WALNUT_D, width=0.02)                                 # Pinsel
    c.poly([(cx + 0.3, ty + 0.26), (cx + 0.38, ty + 0.32), (cx + 0.34, ty + 0.22)], fill=hexc("#8a6a4a"), outline=OUTLINE, width=0.01)
    c.poly([(x1 - 0.5, ty + 0.1), (x1 - 0.2, ty + 0.12), (x1 - 0.22, ty + 0.34), (x1 - 0.52, ty + 0.32)], fill=CREAM, outline=OUTLINE, width=0.012)  # Drehbuch
    for k in range(4):
        c.line([(x1 - 0.46, ty + 0.15 + k * 0.045), (x1 - 0.27, ty + 0.16 + k * 0.045)], fill=alpha(OUTLINE, 120), width=0.008)
    c.ellipse(x1 - 0.36, ty + 0.33, 0.03, 0.012, fill=STEEL, outline=OUTLINE, width=0.008)                           # Klammer


def _sessel(p, c, x0, y0, x1, y1, idx, rnd):
    vel = (PLUM, BORDEAUX, lift("#1e3a2a", 1.7))[idx % 3]
    sheet = idx % 4 == 3
    if sheet:
        vel = hexc("#c9c4b8")
    vel_l, vel_d = shade(vel, 1.2), shade(vel, 0.78)
    for lx in (x0 + 0.06, x1 - 0.12):                                                       # Fuesse
        p.box(lx, y0 + 0.08, lx + 0.06, y0 + 0.14, 0, 0.12, WALNUT_L, WALNUT_D, w=0.02)
    bx0, bx1 = x0 + 0.1, x1 - 0.1
    p.box(bx0, y1 - 0.2, bx1, y1, 0.12, 1.0, vel_l, vel)                                   # Rueckenlehne
    by = y1 - 0.2
    if not sheet:                                                                           # Knopfheftung
        for row, z in enumerate((0.45, 0.7, 0.95)):
            for k in range(4):
                bx = bx0 + 0.1 + (k + (0.5 if row % 2 else 0)) * (bx1 - bx0 - 0.2) / 3.5
                if bx < bx1 - 0.05:
                    c.ellipse(bx, by + z * K, 0.014, 0.011, fill=vel_d)
    for (wx0, wx1) in ((x0, bx0), (bx1, x1)):                                               # Ohren
        p.box(wx0, y1 - 0.42, wx1, y1 - 0.2, 0.55, 0.57, vel_l, vel_d, w=0.04)
    p.box(x0 + 0.17, y0 + 0.12, x1 - 0.17, y1 - 0.2, 0.12, 0.38, vel_l, vel)                 # Sitzkissen
    c.line([(x0 + 0.2, y0 + 0.12 + 0.5 * K - 0.02), (x1 - 0.2, y0 + 0.12 + 0.5 * K - 0.02)], fill=shade(vel, 1.35), width=0.012)   # Paspel
    for (ax0, ax1) in ((x0, x0 + 0.17), (x1 - 0.17, x1)):                                   # Armlehnen
        p.box(ax0, y0 + 0.1, ax1, y1 - 0.2, 0.12, 0.55, vel_l, vel, w=0.04)
    if sheet:                                                                               # Staubtuch: Falten
        for k in range(5):
            fx = x0 + 0.12 + k * (x1 - x0 - 0.24) / 4
            c.line(HD.wobble([(fx, y0 + 0.15), (fx + rnd.uniform(-0.06, 0.06), y1 - 0.2 + 1.0 * K)], amp=0.02, seed=idx + k, step=0.06),
                   fill=alpha(shade(vel, 0.7), 150), width=0.012)
    if idx % 4 == 1:
        cobweb(c, x1, y1 - 0.2 + 1.12 * K, 0.18, -1, -1, seed=idx)


def _sarg(p, c, x0, y0, x1, y1, idx, rnd):
    w, d = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    H = 0.6
    if idx % 2 == 0:
        # Holzsarg: sechseckiger Grundriss (Fussende links, Schultern bei 68 %), Deckel ggf. verschoben
        xs = x0 + w * 0.68
        base = [(x0, cy - d * 0.25), (xs, y0), (x1, cy - d * 0.3), (x1, cy + d * 0.3), (xs, y1), (x0, cy + d * 0.25)]
        wood = WALNUT if idx % 4 == 0 else lift("#3a2a22", 1.6)
        ajar = idx % 4 == 2
        for a, b in ((base[0], base[1]), (base[1], base[2])):
            c.poly([a, b, (b[0], b[1] + H * K), (a[0], a[1] + H * K)], fill=shade(wood, 0.85), outline=OUTLINE, width=A.OUT_W)
            c.line([(a[0] + 0.03, a[1] + H * K - 0.03), (b[0] - 0.03, b[1] + H * K - 0.03)], fill=shade(wood, 1.15), width=0.02)
            c.rect(a[0] + 0.03, min(a[1], b[1]) + 0.03, b[0] - 0.03, min(a[1], b[1]) + 0.1, fill=alpha((0, 0, 0, 255), 50))
        for (a, b, t) in ((base[0], base[1], 0.35), (base[0], base[1], 0.75), (base[1], base[2], 0.5)):    # Messinggriffe
            gx, gy = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + H * K * 0.45
            c.ellipse(gx, gy, 0.06, 0.03, outline=BRASS, width=0.015)
            c.rect(gx - 0.07, gy - 0.01, gx + 0.07, gy + 0.01, fill=BRASS_D)
        lid = [(x, y + H * K) for x, y in base]
        if ajar:
            c.poly(lid, fill=hexc("#1c1418"), outline=OUTLINE, width=A.OUT_W)
            c.poly([(x + (cx - x) * 0.15, y + (cy + H * K - y) * 0.2) for x, y in lid], fill=BORDEAUX_D)
            lid = [(x + 0.12, y + 0.08) for x, y in lid]
        c.poly(lid, fill=shade(wood, 1.1), outline=OUTLINE, width=A.OUT_W)
        c.line([(lid[0][0] + 0.06, (lid[0][1] + lid[5][1]) / 2), (lid[2][0] - 0.06, (lid[2][1] + lid[3][1]) / 2)], fill=shade(wood, 1.25), width=0.015)
        c.line([(lid[1][0], lid[1][1] + 0.04), (lid[4][0], lid[4][1] - 0.04)], fill=shade(wood, 0.8), width=0.012)
        px_ = lid[2][0] - 0.35
        c.rect(px_ - 0.08, cy + H * K - 0.03 + (0.08 if ajar else 0), px_ + 0.08, cy + H * K + 0.03 + (0.08 if ajar else 0), fill=BRASS, outline=OUTLINE, width=0.012)
    else:
        # Steinsarkophag: Kasten mit Reliefrahmen und Rosette, schwerer Deckel (ggf. verschoben), Risse, Moos
        ajar = idx % 4 == 3
        p.box(x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05, 0, 0.5, STONE_L, STONE)
        fy = y0 + 0.05
        c.rect(x0 + 0.15, fy + 0.08 * K, x1 - 0.15, fy + 0.42 * K, outline=STONE_D, width=0.015)
        c.ellipse(cx, fy + 0.25 * K, 0.08, 0.06, outline=STONE_D, width=0.015)
        for k in range(4):
            a = k * math.pi / 2
            c.ellipse(cx + 0.045 * math.cos(a), fy + 0.25 * K + 0.035 * math.sin(a), 0.025, 0.02, fill=shade(STONE, 0.9), outline=STONE_D, width=0.01)
        crack(c, [(x0 + 0.3, fy + 0.02), (x0 + 0.42, fy + 0.3 * K), (x0 + 0.36, fy + 0.48 * K)], seed=idx)
        if ajar:
            c.rect(x0 + 0.05, y0 + 0.05 + 0.5 * K, x0 + 0.2, y1 - 0.05 + 0.5 * K, fill=hexc("#1c1418"))
        lx0 = x0 + (0.15 if ajar else 0)
        p.box(lx0, y0, lx0 + w, y1, 0.5, 0.12, STONE_L, shade(STONE_L, 0.9))
        c.line([(lx0 + 0.04, y0 + 0.62 * K + 0.04), (lx0 + w - 0.04, y0 + 0.62 * K + 0.04)], fill=STONE_D, width=0.012)
        c.rect(lx0 + 0.2, y0 + 0.15 + 0.62 * K, lx0 + w - 0.2, y1 - 0.15 + 0.62 * K, outline=STONE_D, width=0.012)
        crack(c, [(lx0 + w * 0.6, y1 + 0.62 * K), (lx0 + w * 0.55, cy + 0.62 * K), (lx0 + w * 0.62, y0 + 0.62 * K)], seed=idx + 1)
        moss(c, x0 + 0.12, y0 + 0.06, 0.12, seed=idx)
        moss(c, x1 - 0.2, y0 + 0.1 + 0.3 * K, 0.1, seed=idx + 1)
    dust(c, x0 + 0.2, cy + H * K - 0.05, x1 - 0.2, cy + H * K + 0.05, 5, seed=idx)


def _grabstein(p, c, x0, y0, x1, y1, idx, rnd):
    w = x1 - x0
    cx = (x0 + x1) / 2
    form = idx % 4
    p.box(x0, y0, x1, y1, 0, 0.12, STONE_L, STONE)                                         # Sockelplatte
    fy = y0 + 0.08
    if form == 0:                                                                           # Kreuz
        p.box(cx - 0.08, fy, cx + 0.08, y1 - 0.08, 0.12, 0.88, STONE_L, STONE, w=0.04)
        p.box(cx - 0.3, fy, cx + 0.3, y1 - 0.08, 0.6, 0.14, STONE_L, STONE, w=0.04)
        c.line([(cx - 0.06, fy + 0.3 * K), (cx - 0.06, fy + 0.55 * K)], fill=STONE_D, width=0.01)
    elif form == 1:                                                                         # Rundbogen mit Inschrift
        tx0, tx1 = x0 + w * 0.15, x1 - w * 0.15
        p.box(tx0, fy, tx1, y1 - 0.08, 0.12, 0.65, STONE_L, STONE, w=0.04)
        ty = fy + 0.77 * K
        c.ellipse(cx, ty, (tx1 - tx0) / 2, 0.16, fill=STONE, outline=OUTLINE, width=0.04)
        c.rect(tx0 + 0.02, ty - 0.1, tx1 - 0.02, ty + 0.02, fill=STONE)
        c.line([(tx0 + 0.03, ty + 0.14), (tx1 - 0.03, ty + 0.14)], fill=shade(STONE, 1.18), width=0.012)
        c.line([(cx, fy + 0.6 * K), (cx, fy + 0.72 * K)], fill=STONE_D, width=0.018)
        c.line([(cx - 0.04, fy + 0.68 * K), (cx + 0.04, fy + 0.68 * K)], fill=STONE_D, width=0.018)
        for k in range(3):
            ln = (0.3, 0.22, 0.26)[k] * (tx1 - tx0) / 0.56
            c.line([(cx - ln / 2, fy + (0.5 - k * 0.1) * K), (cx + ln / 2, fy + (0.5 - k * 0.1) * K)], fill=STONE_D, width=0.012)
        crack(c, [(tx1 - 0.08, ty + 0.1), (tx1 - 0.14, fy + 0.4 * K), (tx1 - 0.1, fy + 0.25 * K)], seed=idx)
    elif form == 2:                                                                         # schief gesackte Platte
        a = math.radians(-12 if idx % 8 == 2 else 11)
        bw, bh = w * 0.34, 0.78 * K
        base = (cx, fy + 0.12 * K)
        def R(px_, py_):
            return (base[0] + px_ * math.cos(a) - py_ * math.sin(a), base[1] + px_ * math.sin(a) + py_ * math.cos(a))
        front = [R(-bw, 0), R(bw, 0), R(bw, bh), R(-bw, bh)]
        c.poly([front[3], front[2], (front[2][0], front[2][1] + 0.1), (front[3][0], front[3][1] + 0.1)], fill=STONE_L, outline=OUTLINE, width=0.04)
        c.poly(front, fill=STONE, outline=OUTLINE, width=0.04)
        c.line([R(-bw + 0.03, bh - 0.03), R(bw - 0.03, bh - 0.03)], fill=shade(STONE, 1.18), width=0.015)
        for k in range(3):
            c.line([R(-bw * 0.6, bh * (0.62 - k * 0.14)), R(bw * 0.6, bh * (0.62 - k * 0.14))], fill=STONE_D, width=0.012)
        crack(c, [R(bw * 0.2, bh), R(bw * 0.05, bh * 0.6), R(bw * 0.3, bh * 0.3)], seed=idx)
        moss(c, cx - 0.1, fy + 0.1, 0.12, seed=idx)
    else:                                                                                   # Engel-Sockel, Figur ohne Gesicht
        p.box(x0 + 0.1, fy, x1 - 0.1, y1 - 0.08, 0.12, 0.38, STONE_L, STONE, w=0.04)
        c.rect(x0 + 0.16, fy + 0.18 * K, x1 - 0.16, fy + 0.42 * K, outline=STONE_D, width=0.012)
        gy = fy + 0.5 * K
        for sx in (-1, 1):                                                                  # Fluegel
            c.poly([(cx + sx * 0.06, gy + 0.08), (cx + sx * 0.3, gy + 0.3), (cx + sx * 0.26, gy + 0.12), (cx + sx * 0.14, gy + 0.02)],
                   fill=STONE_L, outline=OUTLINE, width=0.03)
        c.poly([(cx - 0.14, gy), (cx + 0.14, gy), (cx + 0.09, gy + 0.3), (cx - 0.09, gy + 0.3)], fill=STONE, outline=OUTLINE, width=0.03)   # Gewand
        c.ellipse(cx, gy + 0.33, 0.07, 0.065, fill=STONE_L, outline=OUTLINE, width=0.03)                                            # Kapuze
        c.ellipse(cx, gy + 0.31, 0.04, 0.035, fill=shade(STONE, 0.55))                                                              # Schatten statt Gesicht
        c.line([(cx - 0.05, gy + 0.08), (cx - 0.02, gy + 0.22)], fill=STONE_D, width=0.01)
        c.line([(cx + 0.05, gy + 0.08), (cx + 0.02, gy + 0.22)], fill=STONE_D, width=0.01)
    for k in range(5):                                                                      # Flechten und Grasbueschel am Fuss
        c.ellipse(rnd.uniform(x0 + 0.1, x1 - 0.1), rnd.uniform(fy + 0.1, fy + 0.3), 0.012, 0.009, fill=alpha(hexc("#b8c070"), 150))
    for seg in HD.tuft(x0 + 0.12, y0 + 0.02, rnd, n=4, h=0.08) + HD.tuft(x1 - 0.14, y0 + 0.02, rnd, n=3, h=0.07):
        c.line(seg, fill=hexc("#6c9450"), width=0.012)


def _aggregat(p, c, x0, y0, x1, y1, idx, rnd):
    cy = (y0 + y1) / 2
    bx0, bx1 = x0 + 0.5, x1 - 0.08
    for (ya, yb) in ((cy + 0.02, cy + 0.12), (cy + 0.02, cy - 0.1)):                           # Deichsel
        c.line([(x0 + 0.05, ya), (bx0 + 0.05, yb)], fill=OUTLINE, width=0.07)
        c.line([(x0 + 0.05, ya), (bx0 + 0.05, yb)], fill=MATTE_L, width=0.04)
    c.ellipse(x0 + 0.1, cy - 0.02, 0.03, 0.03, fill=MATTE_D, outline=OUTLINE, width=0.015)
    c.line([(x0 + 0.18, cy + 0.04), (x0 + 0.18, cy - 0.12)], fill=OUTLINE, width=0.035)
    c.ellipse(x0 + 0.18, cy - 0.14, 0.05, 0.04, fill=MATTE_D, outline=OUTLINE, width=0.02)      # Stuetzrad
    for wx in (bx0 + 0.5, bx1 - 0.5):                                                        # Raeder
        c.ellipse(wx, y0 + 0.22, 0.24, 0.2, fill=MATTE_D, outline=OUTLINE, width=0.03)
        c.ellipse(wx, y0 + 0.22, 0.1, 0.085, fill=STEEL, outline=OUTLINE, width=0.015)
        c.ellipse(wx, y0 + 0.22, 0.03, 0.025, fill=MATTE_D)
    p.box(bx0, y0 + 0.02, bx1, y1 - 0.05, 0.42, 1.35, OLIVE_L, OLIVE)                          # Aufbau
    fy = y0 + 0.02
    fz0, fz1 = fy + 0.42 * K, fy + 1.77 * K
    for wx in (bx0 + 0.5, bx1 - 0.5):                                                        # Kotfluegel
        c.poly([(wx - 0.3, fz0), (wx - 0.26, fz0 + 0.06), (wx + 0.26, fz0 + 0.06), (wx + 0.3, fz0)], fill=MATTE, outline=OUTLINE, width=0.02)
    hz = fz0 + 0.07                                                                          # Warnstreifen
    n = int((bx1 - bx0 - 0.04) / 0.12)
    for k in range(n):
        xa = bx0 + 0.02 + k * 0.12
        c.poly([(xa, hz), (xa + 0.06, hz), (xa + 0.1, hz + 0.08), (xa + 0.04, hz + 0.08)], fill=GAFFER if k % 2 == 0 else MATTE_D)
    c.rect(bx0 + 0.02, hz, bx1 - 0.02, hz + 0.08, outline=OUTLINE, width=0.015)
    gx0, gx1 = bx0 + 0.12, bx0 + (bx1 - bx0) * 0.5                                          # Lueftungsgitter
    c.rect(gx0, fz0 + 0.2, gx1, fz1 - 0.08, fill=shade(OLIVE, 0.8), outline=OUTLINE, width=0.02)
    yy = fz0 + 0.24
    while yy < fz1 - 0.12:
        c.line([(gx0 + 0.03, yy), (gx1 - 0.03, yy)], fill=MATTE_D, width=0.018)
        c.line([(gx0 + 0.03, yy + 0.02), (gx1 - 0.03, yy + 0.02)], fill=shade(OLIVE_L, 1.1), width=0.008)
        yy += 0.05
    px0, px1 = gx1 + 0.12, bx1 - 0.12                                                        # Schaltkasten
    c.rect(px0, fz0 + 0.24, px1, fz1 - 0.12, fill=MATTE, outline=OUTLINE, width=0.02)
    for k in range(2):
        ix = px0 + 0.1 + k * 0.16
        c.ellipse(ix, fz1 - 0.24, 0.05, 0.045, fill=CREAM, outline=OUTLINE, width=0.012)
        c.line([(ix, fz1 - 0.24), (ix + 0.03, fz1 - 0.21)], fill=OUTLINE, width=0.01)
    for k in range(3):
        sx = px0 + 0.08 + k * 0.12
        c.rect(sx - 0.035, fz0 + 0.3, sx + 0.035, fz0 + 0.37, fill=MATTE_D, outline=GAFFER, width=0.01)
        c.ellipse(sx, fz0 + 0.335, 0.015, 0.012, fill=MATTE_L)
    c.glow(px1 - 0.06, fz1 - 0.18, 0.08, hexc("#50ff80"), 0.8)
    c.ellipse(px1 - 0.06, fz1 - 0.18, 0.012, 0.012, fill=hexc("#80ffa0"))
    tx, ty = px0 + (px1 - px0) * 0.5, fz0 + 0.12                                            # Warndreieck mit Blitz
    c.poly([(tx - 0.07, ty - 0.03), (tx + 0.07, ty - 0.03), (tx, ty + 0.1)], fill=GAFFER, outline=OUTLINE, width=0.012)
    c.line([(tx + 0.015, ty + 0.06), (tx - 0.01, ty + 0.03), (tx + 0.01, ty + 0.03), (tx - 0.015, ty)], fill=OUTLINE, width=0.01)
    ex, ey = bx1 - 0.35, fz1 + 0.3                                                           # Auspuff mit Regenklappe, Rauch
    c.line([(ex, ey), (ex, ey + 0.3)], fill=OUTLINE, width=0.09)
    c.line([(ex, ey), (ex, ey + 0.3)], fill=MATTE_L, width=0.06)
    c.poly([(ex - 0.06, ey + 0.3), (ex + 0.06, ey + 0.3), (ex + 0.05, ey + 0.36), (ex - 0.07, ey + 0.34)], fill=MATTE, outline=OUTLINE, width=0.02)
    for k in range(3):
        c.ellipse(ex + 0.06 + k * 0.1, ey + 0.42 + k * 0.1, 0.05 + k * 0.025, 0.04 + k * 0.02, fill=alpha((200, 200, 210, 255), 90 - k * 22))
    c.ellipse(bx0 + 0.5, fz1 + 0.2, 0.05, 0.03, fill=MATTE_D, outline=OUTLINE, width=0.015)    # Tankdeckel
    cable(c, [(px0 + 0.08, fz0 + 0.3), (px0 + 0.15, fz0 + 0.02), (bx1 + 0.1, y0 - 0.05), (x1 + 0.35, y0 - 0.12)], seed=idx)


def _absperrung(p, c, x0, y0, x1, y1, idx, rnd):
    cy = (y0 + y1) / 2
    red = idx % 2 == 1
    ca, cb = (hexc("#e04040"), hexc("#f0ece0")) if red else (GAFFER, MATTE_D)
    posts = (x0 + 0.12, x1 - 0.12)
    zt = 0.95
    for px_ in posts:
        c.soft_shadow(HD.wobble_ellipse(px_ + 0.03, cy - 0.03, 0.15, 0.08), 90, 0.04)
        c.ellipse(px_, cy, 0.14, 0.07, fill=MATTE_D, outline=OUTLINE, width=0.02)
        c.line([(px_, cy), (px_, cy + zt * K)], fill=OUTLINE, width=0.06)
        c.line([(px_, cy), (px_, cy + zt * K)], fill=MATTE_L, width=0.035)
        for k in range(5):
            za = cy + (0.1 + k * 0.17) * K
            c.line([(px_, za), (px_, za + 0.045)], fill=(hexc("#f0ece0") if red else GAFFER), width=0.035)
        c.ellipse(px_, cy + zt * K, 0.03, 0.02, fill=MATTE_D, outline=OUTLINE, width=0.012)

    def band(z, sag, n=18):
        ax, bx = posts
        top, bot = [], []
        for k in range(n + 1):
            t = k / n
            y = cy + z * K - sag * 4 * t * (1 - t)
            top.append((ax + (bx - ax) * t, y + 0.035))
            bot.append((ax + (bx - ax) * t, y - 0.035))
        sh = 0.5 / n * (bx - ax)
        for k in range(n):
            c.poly([top[k], top[k + 1], (bot[k + 1][0] - sh, bot[k + 1][1]), (bot[k][0] - sh, bot[k][1])], fill=ca if k % 2 == 0 else cb)
        c.line(top, fill=OUTLINE, width=0.015)
        c.line(bot, fill=OUTLINE, width=0.015)

    band(0.85, 0.08)
    if idx % 3 != 1:
        band(0.45, 0.06)
    if idx % 3 == 0:                                                                        # Hinweiskarte
        mx = (posts[0] + posts[1]) / 2
        c.rect(mx - 0.14, cy + 0.85 * K - 0.2, mx + 0.14, cy + 0.85 * K - 0.05, fill=CREAM, outline=OUTLINE, width=0.015)
        c.text(mx, cy + 0.85 * K - 0.125, "SET", 0.08, OUTLINE)


# ------------------------------------------------------------------ Horror-Requisiten (gemeinsame Teile)

def blood_pool(c, x, y, rx, ry, seed=0, a=235):
    """Kunstblutlache: zittrige dunkle Ellipse, matter Kern, ein Glanzpunkt, Ausfransungen."""
    rnd = random.Random(seed)
    c.poly(HD.wobble_ellipse(x, y, rx, ry, amp=min(rx, ry) * 0.18, seed=seed), fill=alpha(BLOOD, a))
    c.poly(HD.wobble_ellipse(x + rx * 0.1, y - ry * 0.05, rx * 0.6, ry * 0.55, amp=0.01, seed=seed + 1), fill=alpha(shade(BLOOD, 0.85), a))
    for _ in range(4):
        ang = rnd.uniform(0, math.tau)
        d = rnd.uniform(0.9, 1.5)
        c.ellipse(x + math.cos(ang) * rx * d, y + math.sin(ang) * ry * d, rx * 0.12, ry * 0.12, fill=alpha(BLOOD, a))
    c.ellipse(x - rx * 0.3, y + ry * 0.3, rx * 0.12, ry * 0.08, fill=alpha((255, 255, 255, 255), 70))


def blood_drips(c, x, y, n, length, seed=0):
    """Tropfspuren nach unten (im Bild) von einer Kante bei (x, y)."""
    rnd = random.Random(seed)
    for k in range(n):
        dx = rnd.uniform(-0.08, 0.08) * n
        ln = length * rnd.uniform(0.4, 1.0)
        c.line([(x + dx, y), (x + dx, y - ln)], fill=BLOOD, width=0.016)
        c.ellipse(x + dx, y - ln, 0.012, 0.014, fill=BLOOD)


def knife(c, x, y, ang, s=1.0, blade=STEEL):
    """Requisiten-Messer (liegend): Klinge mit Glanz, dunkler Griff mit Nieten."""
    ca, sa = math.cos(ang), math.sin(ang)

    def R(u, v):
        return (x + u * ca - v * sa, y + u * sa + v * ca)
    c.poly([R(0, -0.02 * s), R(0.22 * s, -0.02 * s), R(0.3 * s, 0.0), R(0.22 * s, 0.025 * s), R(0, 0.025 * s)], fill=blade, outline=OUTLINE, width=0.012)
    c.line([R(0.02 * s, 0.005 * s), R(0.24 * s, 0.005 * s)], fill=alpha((255, 255, 255, 255), 150), width=0.008)
    c.poly([R(-0.12 * s, -0.025 * s), R(0, -0.025 * s), R(0, 0.025 * s), R(-0.12 * s, 0.025 * s)], fill=hexc("#2a2226"), outline=OUTLINE, width=0.012)
    for u in (-0.09, -0.04):
        c.ellipse(*R(u * s, 0), 0.006, 0.006, fill=BRASS)


def bottle(c, x, y, h, col, label=None, r=0.03):
    """Flasche (Kunstblut, Chemie): Zylinder mit Hals, Etikett, Glanz."""
    c.rect(x - r, y, x + r, y + h * 0.7, fill=col, outline=OUTLINE, width=0.012)
    c.ellipse(x, y + h * 0.7, r, r * 0.4, fill=shade(col, 1.1), outline=OUTLINE, width=0.012)
    c.rect(x - r * 0.4, y + h * 0.7, x + r * 0.4, y + h, fill=col, outline=OUTLINE, width=0.012)
    c.ellipse(x, y + h, r * 0.45, r * 0.2, fill=MATTE_D, outline=OUTLINE, width=0.01)
    if label:
        c.rect(x - r * 0.8, y + h * 0.2, x + r * 0.8, y + h * 0.5, fill=label, outline=OUTLINE, width=0.008)
    c.line([(x - r * 0.6, y + h * 0.08), (x - r * 0.6, y + h * 0.62)], fill=alpha((255, 255, 255, 255), 90), width=0.008)


def book_stack(c, x, y, n, w=0.22, rnd=None):
    rnd = rnd or random.Random(n)
    cols = [lift("#5a1e22", 1.4), lift("#1e3a2a", 1.5), lift("#1e2a4a", 1.5), hexc("#a8843c"), CREAM_D]
    for k in range(n):
        dx = rnd.uniform(-0.02, 0.02)
        c.rect(x + dx, y + k * 0.035, x + dx + w, y + (k + 1) * 0.035, fill=rnd.choice(cols), outline=OUTLINE, width=0.012)
        c.line([(x + dx + 0.02, y + k * 0.035 + 0.012), (x + dx + w - 0.02, y + k * 0.035 + 0.012)], fill=alpha(CREAM, 160), width=0.006)


def banker_lamp(c, x, y, s=1.0):
    """Bankerlampe: Messingfuss, gruener Glasschirm, warmer Schein."""
    c.glow(x, y + 0.12 * s, 0.55 * s, WARM, 0.5)
    c.ellipse(x, y, 0.07 * s, 0.03 * s, fill=BRASS, outline=OUTLINE, width=0.012)
    c.line([(x, y), (x, y + 0.22 * s)], fill=OUTLINE, width=0.03)
    c.line([(x, y), (x, y + 0.22 * s)], fill=BRASS, width=0.016)
    c.poly([(x - 0.14 * s, y + 0.2 * s), (x + 0.14 * s, y + 0.2 * s), (x + 0.1 * s, y + 0.3 * s), (x - 0.1 * s, y + 0.3 * s)],
           fill=LAMP_GREEN, outline=OUTLINE, width=0.015)
    c.rect(x - 0.12 * s, y + 0.2 * s, x + 0.12 * s, y + 0.225 * s, fill=BULB)
    c.line([(x - 0.08 * s, y + 0.28 * s), (x + 0.02 * s, y + 0.28 * s)], fill=shade(LAMP_GREEN, 1.4), width=0.01)


def chalk_text(c, x, y, s, size, col=None):
    c.text(x, y, s, size, col or alpha((236, 232, 224, 255), 200))


def hedge_mass(c, x0, y0, x1, y1, h, seed=0):
    """Heckenblock in schraeger Aufsicht: dunkler Fuss, Blaetterballen ueber die ganze Masse, Lichtkanten."""
    rnd = random.Random(seed)
    base = lift("#1e3a26", 1.3)
    c.poly([(x0, y0), (x1, y0), (x1, y1 + h * K), (x0, y1 + h * K)], fill=shade(base, 0.8), outline=OUTLINE, width=A.OUT_W)
    blobs = []
    y = y0 + 0.05
    while y < y1 + h * K:
        x = x0 + 0.05
        while x < x1:
            r = rnd.uniform(0.18, 0.3)
            blobs.append((x + rnd.uniform(-0.05, 0.05), y + rnd.uniform(-0.04, 0.04), r, rnd.uniform(0.85, 1.25)))
            x += r * 1.2
        y += 0.2
    blobs.sort(key=lambda b: -b[1])
    for i, (bx, by, r, t) in enumerate(blobs):
        pts = HD.wobble_ellipse(bx, by, r, r * 0.8, amp=0.015, seed=i + seed)
        col = shade(base, t)
        c.poly(pts, fill=col, outline=shade(OUTLINE, 1.0), width=0.025)
        c.poly(HD.wobble_ellipse(bx - r * 0.25, by + r * 0.3, r * 0.45, r * 0.3, amp=0.01, seed=i + 7), fill=shade(col, 1.3))
        if rnd.random() < 0.15:
            c.ellipse(bx + rnd.uniform(-r * 0.4, r * 0.4), by + rnd.uniform(-r * 0.3, r * 0.3), 0.02, 0.02, fill=hexc("#b83c48"), outline=OUTLINE, width=0.01)
    c.rect(x0, y0, x1, y0 + 0.08, fill=alpha((0, 0, 0, 255), 90))


# ------------------------------------------------------------------ die neuen Objekte

def _freitreppe(p, c, x0, y0, x1, y1, idx, rnd):
    """Freitreppe: sieben Stufen steigen nach hinten (Norden), Podest, Balustraden mit Handlauf, roter
    Laeufer mit Messingstangen, Schleifspur im Laeufer, Spinnwebe am Pfosten."""
    n = 7
    rise = 0.22
    land = 0.6
    d = (y1 - y0 - land) / n
    sx0, sx1 = x0 + 0.3, x1 - 0.3
    runner = BORDEAUX_D
    # Podest zuerst, dann die Stufen von hinten nach vorn
    p.box(sx0, y1 - land, sx1, y1, n * rise, 0.1, STONE_L, STONE)
    c.rect(sx0 + 0.6, y1 - land + 0.02 + (n * rise + 0.1) * K, sx1 - 0.6, y1 - 0.02 + (n * rise + 0.1) * K, fill=runner)
    for k in range(n - 1, -1, -1):
        ya, yb = y0 + k * d, y0 + (k + 1) * d
        p.box(sx0, ya, sx1, yb, k * rise, rise, STONE_L, STONE)
        zt = ya + (k + 1) * rise * K
        c.rect(sx0 + 0.6, zt + 0.015, sx1 - 0.6, yb + (k + 1) * rise * K - 0.01, fill=runner)               # Laeufer auf der Trittflaeche
        c.rect(sx0 + 0.6, ya + k * rise * K + 0.02, sx1 - 0.6, zt - 0.02, fill=shade(runner, 0.8))          # Laeufer an der Setzstufe
        c.line([(sx0 + 0.62, zt + 0.02), (sx1 - 0.62, zt + 0.02)], fill=BRASS, width=0.014)                 # Messingstange
        c.line([(sx0 + 0.65, zt + 0.04), (sx1 - 0.65, zt + 0.04)], fill=alpha((255, 255, 255, 255), 50), width=0.01)
        if idx % 2 == 0 and k in (2, 3, 4):                                                                # Schleifspur
            c.line([(sx0 + 1.3 + k * 0.04, ya + k * rise * K + 0.02), (sx0 + 1.4, yb + (k + 1) * rise * K)], fill=alpha(BLOOD, 170), width=0.09)
    # Balustraden: Wangen als Parallelogramm, Docken, Handlauf, Pfosten mit Kugel
    for bx0, bx1 in ((x0, sx0), (sx1, x1)):
        bot = [(bx0, y0 + 0.05), (bx1, y0 + 0.05), (bx1, y1 - land + n * rise * K), (bx0, y1 - land + n * rise * K)]
        c.poly(bot, fill=STONE, outline=OUTLINE, width=A.OUT_W)
        c.line([(bx0 + 0.03, y0 + 0.07), (bx0 + 0.03, y1 - land + n * rise * K - 0.03)], fill=STONE_L, width=0.016)
        for k in range(n):
            by = y0 + 0.15 + k * d
            bz = (k + 0.5) * rise * K
            c.line([((bx0 + bx1) / 2, by + bz), ((bx0 + bx1) / 2, by + bz + 0.75 * K)], fill=OUTLINE, width=0.05)
            c.line([((bx0 + bx1) / 2, by + bz), ((bx0 + bx1) / 2, by + bz + 0.75 * K)], fill=WALNUT_L, width=0.03)
        rail = [((bx0 + bx1) / 2, y0 + 0.1 + 0.8 * K), ((bx0 + bx1) / 2, y1 - land + (n * rise + 0.8) * K)]
        c.line(rail, fill=OUTLINE, width=0.07)
        c.line(rail, fill=WALNUT, width=0.045)
        c.line([(rail[0][0] - 0.01, rail[0][1]), (rail[1][0] - 0.01, rail[1][1])], fill=WALNUT_L, width=0.012)
        px_ = (bx0 + bx1) / 2
        p.box(px_ - 0.09, y0, px_ + 0.09, y0 + 0.18, 0, 0.95, WALNUT_L, WALNUT)
        c.ellipse(px_, y0 + 0.1 + 1.02 * K, 0.08, 0.075, fill=BRASS, outline=OUTLINE, width=0.02)
        c.ellipse(px_ - 0.025, y0 + 0.1 + 1.02 * K + 0.025, 0.02, 0.016, fill=BRASS_L)
    cobweb(c, x0 + 0.15, y0 + 0.1 + 1.02 * K, 0.25, 1, 1, seed=idx)
    dust(c, sx0 + 0.7, y1 - land + 0.1 + (n * rise + 0.1) * K, sx1 - 0.7, y1 - 0.05 + (n * rise + 0.1) * K, 10, seed=idx)


def _herd(p, c, x0, y0, x1, y1, idx, rnd):
    """Gusseiserner Kuechenherd: Ofentueren mit Messinggriffen, Kochplatten, grosser Topf mit Dampf,
    Kupferhaube an der Wand, Glut in einer Tuer."""
    w = x1 - x0
    cx = (x0 + x1) / 2
    p.box(x0, y0, x1, y1, 0, 0.95, IRON_L, IRON)
    fy = y0
    for k in range(3):                                                                           # Ofentueren
        dx0 = x0 + 0.1 + k * (w - 0.2) / 3
        dx1 = dx0 + (w - 0.2) / 3 - 0.08
        c.rect(dx0, fy + 0.2 * K, dx1, fy + 0.75 * K, fill=IRON_D, outline=OUTLINE, width=0.02)
        c.rect(dx0 + 0.04, fy + 0.26 * K, dx1 - 0.04, fy + 0.69 * K, outline=IRON_L, width=0.01)
        c.line([(dx0 + 0.1, fy + 0.47 * K), (dx1 - 0.1, fy + 0.47 * K)], fill=OUTLINE, width=0.035)
        c.line([(dx0 + 0.1, fy + 0.47 * K), (dx1 - 0.1, fy + 0.47 * K)], fill=BRASS, width=0.02)
        if k == 1:                                                                               # Glutschlitz
            c.glow((dx0 + dx1) / 2, fy + 0.33 * K, 0.25, EMBER, 0.6)
            c.rect(dx0 + 0.12, fy + 0.3 * K, dx1 - 0.12, fy + 0.36 * K, fill=EMBER, outline=OUTLINE, width=0.01)
    c.rect(x0 + 0.02, fy + 0.02, x1 - 0.02, fy + 0.1 * K, fill=IRON_D)                              # Sockelleiste
    zt = y0 + 0.95 * K
    for k in range(4):                                                                           # Kochplatten
        hx = x0 + 0.35 + k * (w - 0.7) / 3
        c.ellipse(hx, zt + 0.22, 0.14, 0.07, fill=IRON_D, outline=OUTLINE, width=0.015)
        c.ellipse(hx, zt + 0.22, 0.09, 0.045, outline=IRON_L, width=0.008)
    # grosser Topf auf der zweiten Platte, Dampf
    tx = x0 + 0.35 + (w - 0.7) / 3
    p.cyl(tx, y0 + 0.3, 0.18, 0.95, 0.3, hexc("#3a3e46"), MATTE, ry=0.09)
    c.ellipse(tx, y0 + 0.3 + 1.25 * K, 0.15, 0.07, fill=hexc("#5a2a2e"))
    for k in range(3):
        c.ellipse(tx + 0.05 + k * 0.06, y0 + 0.3 + 1.3 * K + 0.1 + k * 0.1, 0.06 + k * 0.02, 0.05 + k * 0.015, fill=alpha((210, 210, 220, 255), 80 - k * 20))
    c.line([(tx - 0.2, y0 + 0.3 + 1.1 * K), (tx - 0.24, y0 + 0.3 + 1.1 * K)], fill=OUTLINE, width=0.04)
    c.line([(tx + 0.2, y0 + 0.3 + 1.1 * K), (tx + 0.24, y0 + 0.3 + 1.1 * K)], fill=OUTLINE, width=0.04)
    # Pfanne und Kelle
    c.ellipse(x1 - 0.5, zt + 0.25, 0.13, 0.06, fill=MATTE, outline=OUTLINE, width=0.015)
    c.line([(x1 - 0.38, zt + 0.25), (x1 - 0.18, zt + 0.3)], fill=OUTLINE, width=0.03)
    # Kupferhaube an der Rueckwand
    hy = y1 + 1.3 * K
    c.poly([(x0 + 0.2, hy), (x1 - 0.2, hy), (x1 - 0.5, hy + 0.5), (x0 + 0.5, hy + 0.5)], fill=COPPER, outline=OUTLINE, width=0.03)
    c.line([(x0 + 0.55, hy + 0.45), (x1 - 0.55, hy + 0.45)], fill=shade(COPPER, 1.3), width=0.015)
    c.rect(x0 + 0.3, hy, x1 - 0.3, hy + 0.06, fill=shade(COPPER, 0.75))
    c.rect(cx - 0.15, hy + 0.5, cx + 0.15, hy + 0.7, fill=shade(COPPER, 0.85), outline=OUTLINE, width=0.025)
    c.ellipse(x0 + 0.42, hy + 0.3, 0.08, 0.05, fill=alpha((0, 0, 0, 255), 60))                       # Russfleck
    cobweb(c, x1 - 0.2, hy, 0.2, -1, 1, seed=idx)


def _funktisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Funktisch: Holztisch, Roehrenfunkgeraet mit Skala und Knoepfen, Kopfhoerer, Mikrofon, Morsetaste,
    Schreiblampe, Zettel."""
    p.box(x0, y0, x1, y1, 0, 0.78, WALNUT_L, WALNUT)
    c.rect(x0 + 0.1, y0 + 0.25 * K, x0 + 0.5, y0 + 0.6 * K, outline=WALNUT_D, width=0.012)
    c.ellipse(x0 + 0.3, y0 + 0.42 * K, 0.02, 0.016, fill=BRASS)
    zt = y0 + 0.78 * K
    cx = (x0 + x1) / 2
    # Funkgeraet (olivgrau, Bakelit-Front)
    gx0, gx1 = cx - 0.5, cx + 0.3
    p.box(gx0, y0 + 0.15, gx1, y1 - 0.08, 0.78, 0.5, hexc("#6a6e62"), hexc("#50544c"))
    fz = y0 + 0.15 + 0.78 * K
    c.rect(gx0 + 0.06, fz + 0.14, gx1 - 0.3, fz + 0.24, fill=hexc("#2a2418"), outline=OUTLINE, width=0.012)   # Skala
    c.glow((gx0 + gx1 - 0.24) / 2, fz + 0.19, 0.25, hexc("#e8a83c"), 0.35)
    for k in range(9):
        sx = gx0 + 0.09 + k * (gx1 - gx0 - 0.42) / 8
        c.line([(sx, fz + 0.16), (sx, fz + 0.2 if k % 2 == 0 else fz + 0.185)], fill=hexc("#f0c060"), width=0.008)
    c.line([(gx0 + 0.3, fz + 0.15), (gx0 + 0.3, fz + 0.23)], fill=hexc("#ff5040"), width=0.01)
    for k in range(3):                                                                           # Drehknoepfe
        kx = gx0 + 0.1 + k * 0.14
        c.ellipse(kx, fz + 0.07, 0.03, 0.03, fill=MATTE_D, outline=OUTLINE, width=0.012)
        c.line([(kx, fz + 0.07), (kx + 0.02 * math.cos(k + idx), fz + 0.07 + 0.02 * math.sin(k + idx))], fill=STEEL, width=0.008)
    c.ellipse(gx1 - 0.16, fz + 0.16, 0.08, 0.06, fill=hexc("#1e1c18"), outline=OUTLINE, width=0.012)        # VU-Meter
    c.ellipse(gx1 - 0.16, fz + 0.16, 0.06, 0.045, fill=PARCH)
    c.line([(gx1 - 0.16, fz + 0.14), (gx1 - 0.12, fz + 0.2)], fill=hexc("#c03030"), width=0.01)
    c.rect(gx1 - 0.26, fz + 0.03, gx1 - 0.06, fz + 0.09, fill=MATTE_D, outline=OUTLINE, width=0.01)          # Lautsprechergitter
    for k in range(4):
        c.line([(gx1 - 0.25, fz + 0.04 + k * 0.014), (gx1 - 0.07, fz + 0.04 + k * 0.014)], fill=hexc("#6a6e62"), width=0.005)
    c.glow(gx0 + 0.04, fz + 0.3, 0.06, hexc("#ff4040"), 0.8)
    c.ellipse(gx0 + 0.04, fz + 0.3, 0.012, 0.012, fill=hexc("#ff5050"))
    # Mikrofon auf Standfuss rechts, Kopfhoerer links, Morsetaste vorn
    mx = gx1 + 0.25
    c.ellipse(mx, zt + 0.2, 0.06, 0.03, fill=MATTE_D, outline=OUTLINE, width=0.012)
    c.line([(mx, zt + 0.2), (mx, zt + 0.5)], fill=OUTLINE, width=0.035)
    c.line([(mx, zt + 0.2), (mx, zt + 0.5)], fill=STEEL, width=0.018)
    c.rect(mx - 0.05, zt + 0.5, mx + 0.05, zt + 0.66, fill=STEEL, outline=OUTLINE, width=0.015)
    for k in range(4):
        c.line([(mx - 0.04, zt + 0.52 + k * 0.035), (mx + 0.04, zt + 0.52 + k * 0.035)], fill=MATTE_D, width=0.006)
    hx = x0 + 0.3
    c.ellipse(hx, zt + 0.22, 0.1, 0.07, outline=OUTLINE, width=0.035)
    c.ellipse(hx, zt + 0.22, 0.1, 0.07, outline=MATTE_L, width=0.018)
    c.ellipse(hx - 0.09, zt + 0.2, 0.035, 0.035, fill=MATTE_D, outline=OUTLINE, width=0.012)
    c.ellipse(hx + 0.09, zt + 0.2, 0.035, 0.035, fill=MATTE_D, outline=OUTLINE, width=0.012)
    cable(c, [(hx + 0.1, zt + 0.18), (hx + 0.3, zt + 0.1), (gx0 + 0.02, zt + 0.12)], seed=idx, w=0.012)
    kx = gx0 + 0.15
    c.rect(kx - 0.08, zt + 0.02, kx + 0.08, zt + 0.08, fill=WALNUT_D, outline=OUTLINE, width=0.012)
    c.line([(kx - 0.05, zt + 0.08), (kx + 0.06, zt + 0.12)], fill=OUTLINE, width=0.025)
    c.ellipse(kx + 0.06, zt + 0.12, 0.018, 0.015, fill=MATTE_D, outline=OUTLINE, width=0.01)
    banker_lamp(c, x1 - 0.25, zt + 0.1, 0.8)
    c.poly([(x0 + 0.55, zt + 0.06), (x0 + 0.8, zt + 0.04), (x0 + 0.82, zt + 0.2), (x0 + 0.57, zt + 0.22)], fill=CREAM, outline=OUTLINE, width=0.01)
    for k in range(3):
        c.line([(x0 + 0.6, zt + 0.09 + k * 0.035), (x0 + 0.76, zt + 0.085 + k * 0.035)], fill=alpha(OUTLINE, 120), width=0.006)


def _kisten(p, c, x0, y0, x1, y1, idx, rnd):
    """Kisten: Holzkisten mit Stempeln, schwarze Filmkoffer mit Stahlkanten, oben eine Filmdose, Kabelrolle."""
    w, d = x1 - x0, y1 - y0
    crate = lift("#6a4a2c", 1.5)
    c1 = (x0, y0, x0 + w * 0.5, y1 - 0.1)
    p.box(*c1, 0, 0.6, shade(crate, 1.15), crate)
    for k in range(2):
        c.line([(c1[0] + 0.04, c1[1] + 0.05 + k * 0.14), (c1[2] - 0.04, c1[1] + 0.05 + k * 0.14)], fill=shade(crate, 0.7), width=0.012)
    c.rect(c1[0] + 0.03, c1[1] + 0.04, c1[0] + 0.1, c1[1] + 0.6 * K - 0.03, fill=shade(crate, 0.85), outline=OUTLINE, width=0.012)
    c.rect(c1[2] - 0.1, c1[1] + 0.04, c1[2] - 0.03, c1[1] + 0.6 * K - 0.03, fill=shade(crate, 0.85), outline=OUTLINE, width=0.012)
    c.text((c1[0] + c1[2]) / 2, c1[1] + 0.3 * K, "PROPS", 0.08, alpha(OUTLINE, 170))
    p.box(c1[0] + 0.1, c1[1] + 0.15, c1[2] - 0.1, c1[3] - 0.1, 0.6, 0.45, shade(crate, 1.1), shade(crate, 0.95))
    c.text((c1[0] + c1[2]) / 2, c1[1] + 0.15 + 0.82 * K, "FRAGILE", 0.06, alpha(hexc("#b03030"), 200))
    # Filmkoffer rechts (schwarz, Stahlkanten, Schnappschloesser)
    k1 = (x0 + w * 0.52, y0 + 0.05, x1, y1 - 0.15)
    p.box(*k1, 0, 0.5, MATTE_L, MATTE)
    k2 = (x0 + w * 0.56, y0 + 0.1, x1 - 0.05, y1 - 0.2)
    p.box(*k2, 0.5, 0.45, MATTE_L, MATTE)
    for (bx0, by0, bx1, by1, z0, h) in (k1 + (0, 0.5), k2 + (0.5, 0.45)):
        fz = by0 + z0 * K
        c.line([(bx0 + 0.02, fz + h * K * 0.5), (bx1 - 0.02, fz + h * K * 0.5)], fill=STEEL, width=0.012)
        for sx in (bx0 + 0.12, bx1 - 0.12):
            c.rect(sx - 0.04, fz + h * K * 0.5 - 0.03, sx + 0.04, fz + h * K * 0.5 + 0.03, fill=STEEL, outline=OUTLINE, width=0.01)
        for cxp, cyp in ((bx0, fz), (bx1, fz), (bx0, fz + h * K), (bx1, fz + h * K)):
            c.ellipse(cxp, cyp, 0.03, 0.025, fill=STEEL, outline=OUTLINE, width=0.012)
        gaffer(c, bx0 + 0.2, fz + h * K * 0.78, bx1 - 0.25, fz + h * K * 0.8, 0.035)
    # Filmdose oben, Kabelrolle davor
    tz = k2[1] + 0.95 * K
    c.ellipse((k2[0] + k2[2]) / 2, tz + 0.1, 0.17, 0.08, fill=STEEL, outline=OUTLINE, width=0.02)
    c.ellipse((k2[0] + k2[2]) / 2, tz + 0.1, 0.05, 0.025, fill=MATTE_D, outline=OUTLINE, width=0.012)
    c.ellipse((k2[0] + k2[2]) / 2, tz + 0.1, 0.11, 0.05, outline=alpha(OUTLINE, 120), width=0.008)
    rx, ry = x0 + 0.25, y0 - 0.05
    c.ellipse(rx, ry, 0.16, 0.08, fill=MATTE_D, outline=OUTLINE, width=0.02)
    for r in (0.12, 0.08):
        c.ellipse(rx, ry, r, r * 0.5, outline=MATTE_L, width=0.012)
    cable(c, [(rx + 0.15, ry), (rx + 0.4, ry - 0.06), (x1 + 0.1, ry - 0.1)], seed=idx)
    dust(c, c1[0] + 0.15, c1[1] + 0.15 + 1.05 * K, c1[2] - 0.15, c1[3] - 0.1 + 1.05 * K, 6, seed=idx)
    cobweb(c, k2[2] - 0.05, k2[1] + 0.95 * K, 0.14, -1, 1, seed=idx + 1)


def _kessel(p, c, x0, y0, x1, y1, idx, rnd):
    """Heizkessel: genieteter Eisenzylinder, Feuertuer mit Glut, Manometer, Rohre mit Ventilrad, Dampf."""
    cx = (x0 + x1) / 2
    r = (x1 - x0) / 2 - 0.1
    cy = y0 + 0.35
    p.box(x0, y0, x1, y0 + 0.25, 0, 0.25, STONE_L, STONE)                                          # Sockel
    p.cyl(cx, cy, r, 0.25, 1.6, IRON_L, IRON, ry=r * 0.5)
    fb = cy + 0.25 * K
    for z in (0.35, 0.9, 1.45):                                                                    # Nietbaender
        c.line([(cx - r + 0.02, fb + z * K), (cx + r - 0.02, fb + z * K)], fill=IRON_D, width=0.03)
        for k in range(7):
            c.ellipse(cx - r + 0.08 + k * (2 * r - 0.16) / 6, fb + z * K, 0.012, 0.012, fill=IRON_L, outline=OUTLINE, width=0.006)
    c.line([(cx - r + 0.05, fb + 0.05), (cx - r + 0.05, fb + 1.55 * K)], fill=alpha((255, 255, 255, 255), 50), width=0.02)
    # Feuertuer mit Glut
    c.rect(cx - 0.22, fb + 0.45 * K, cx + 0.22, fb + 0.85 * K, fill=IRON_D, outline=OUTLINE, width=0.025)
    c.glow(cx, fb + 0.62 * K, 0.35, EMBER, 0.7)
    c.rect(cx - 0.15, fb + 0.52 * K, cx + 0.15, fb + 0.62 * K, fill=EMBER, outline=OUTLINE, width=0.012)
    for k in range(4):
        c.line([(cx - 0.12 + k * 0.08, fb + 0.52 * K), (cx - 0.12 + k * 0.08, fb + 0.62 * K)], fill=IRON_D, width=0.015)
    c.line([(cx + 0.24, fb + 0.6 * K), (cx + 0.34, fb + 0.62 * K)], fill=OUTLINE, width=0.03)
    c.ellipse(cx + 0.34, fb + 0.62 * K, 0.025, 0.02, fill=BRASS, outline=OUTLINE, width=0.01)
    floor_light(c, cx, y0 - 0.2, 0.9, 0.35, EMBER, 0.25, seed=idx)
    # Manometer
    c.ellipse(cx - 0.05, fb + 1.2 * K, 0.11, 0.1, fill=BRASS, outline=OUTLINE, width=0.02)
    c.ellipse(cx - 0.05, fb + 1.2 * K, 0.08, 0.072, fill=PARCH, outline=OUTLINE, width=0.01)
    for k in range(7):
        a = math.pi * 0.15 + k * math.pi * 0.7 / 6
        c.line([(cx - 0.05 + 0.06 * math.cos(a), fb + 1.2 * K + 0.055 * math.sin(a)), (cx - 0.05 + 0.075 * math.cos(a), fb + 1.2 * K + 0.068 * math.sin(a))],
               fill=OUTLINE, width=0.008)
    c.line([(cx - 0.05, fb + 1.2 * K), (cx - 0.05 + 0.06 * math.cos(0.5), fb + 1.2 * K + 0.055 * math.sin(0.5))], fill=hexc("#c03030"), width=0.012)
    # Rohre: eines nach oben mit Ventilrad, eines zur Seite in die Wand
    top = cy + 1.85 * K
    c.ellipse(cx, top, r, r * 0.5, fill=IRON_L, outline=OUTLINE, width=A.OUT_W)
    c.ellipse(cx, top, r * 0.7, r * 0.35, fill=IRON, outline=IRON_D, width=0.015)
    px_ = cx + r * 0.4
    c.line([(px_, top), (px_, top + 0.45)], fill=OUTLINE, width=0.11)
    c.line([(px_, top), (px_, top + 0.45)], fill=IRON_L, width=0.08)
    c.line([(px_ - 0.02, top + 0.02), (px_ - 0.02, top + 0.43)], fill=alpha((255, 255, 255, 255), 60), width=0.015)
    c.ellipse(px_, top + 0.28, 0.09, 0.05, fill=hexc("#8a2a2a"), outline=OUTLINE, width=0.02)
    c.ellipse(px_, top + 0.28, 0.03, 0.018, fill=IRON_D, outline=OUTLINE, width=0.01)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        c.line([(px_, top + 0.28), (px_ + 0.085 * math.cos(a), top + 0.28 + 0.045 * math.sin(a))], fill=hexc("#8a2a2a"), width=0.015)
    sx = cx - r * 0.5
    c.line([(sx, top - 0.02), (sx, top + 0.25), (x1 + 0.3, top + 0.25)], fill=OUTLINE, width=0.09)
    c.line([(sx, top - 0.02), (sx, top + 0.25), (x1 + 0.3, top + 0.25)], fill=IRON_L, width=0.06)
    for k in range(3):                                                                            # Dampf
        c.ellipse(px_ + 0.08 + k * 0.08, top + 0.55 + k * 0.1, 0.05 + k * 0.025, 0.04 + k * 0.02, fill=alpha((210, 210, 220, 255), 85 - k * 22))
    c.ellipse(cx + r * 0.3, fb + 0.2 * K, 0.1, 0.05, fill=alpha(hexc("#8a4a2a"), 150))               # Rostfleck
    cable(c, [(x0 + 0.1, y0 - 0.02), (x0 - 0.2, y0 - 0.1), (x0 - 0.4, y0 - 0.05)], seed=idx)


def _altar(p, c, x0, y0, x1, y1, idx, rnd):
    """Altar an der Westwand (schmal in x, lang in y): Steintisch, staubiges Tuch, zwei Kerzen, Kelch,
    aufgeschlagenes Buch, vertrocknete Blumen."""
    p.box(x0, y0, x1, y1, 0, 0.95, STONE_L, STONE)
    c.rect(x0 + 0.08, y0 + 0.15 * K, x1 - 0.08, y0 + 0.8 * K, outline=STONE_D, width=0.015)
    c.ellipse((x0 + x1) / 2, y0 + 0.47 * K, 0.08, 0.1, outline=STONE_D, width=0.012)
    crack(c, [(x0 + 0.15, y0 + 0.05), (x0 + 0.22, y0 + 0.4 * K), (x0 + 0.18, y0 + 0.7 * K)], seed=idx)
    zt = y0 + 0.95 * K
    cloth = (x0 + 0.05, zt + 0.08, x1 - 0.05, y1 + 0.95 * K - 0.1)
    c.rect(*cloth, fill=CREAM_D, outline=OUTLINE, width=0.015)
    c.rect(x0 - 0.02, zt - 0.1, x0 + 0.05, zt + 0.1, fill=CREAM_D, outline=OUTLINE, width=0.015)       # haengender Saum
    for k in range(3):
        c.line([(cloth[0] + 0.05 + k * 0.2, cloth[1] + 0.05), (cloth[0] + 0.08 + k * 0.2, cloth[3] - 0.05)], fill=alpha(shade(CREAM_D, 0.8), 120), width=0.01)
    c.line([(cloth[0] + 0.03, cloth[1] + 0.03), (cloth[2] - 0.03, cloth[1] + 0.03)], fill=BRASS_D, width=0.008)
    cy = (cloth[1] + cloth[3]) / 2
    for k, sy in enumerate((cloth[1] + 0.25, cloth[3] - 0.25)):
        c.ellipse((x0 + x1) / 2, sy, 0.05, 0.025, fill=BRASS, outline=OUTLINE, width=0.012)
        c.line([((x0 + x1) / 2, sy), ((x0 + x1) / 2, sy + 0.1)], fill=OUTLINE, width=0.035)
        c.line([((x0 + x1) / 2, sy), ((x0 + x1) / 2, sy + 0.1)], fill=BRASS, width=0.02)
        candle(c, (x0 + x1) / 2, sy + 0.1, 0.18 if k == 0 else 0.13, idx % 3 != 1 or k == 0, r=0.028, seed=idx + k)
    kx = (x0 + x1) / 2 - 0.12
    c.ellipse(kx, cy - 0.1, 0.05, 0.022, fill=BRASS, outline=OUTLINE, width=0.012)                      # Kelch
    c.line([(kx, cy - 0.1), (kx, cy)], fill=BRASS_D, width=0.025)
    c.poly([(kx - 0.06, cy), (kx + 0.06, cy), (kx + 0.05, cy + 0.08), (kx - 0.05, cy + 0.08)], fill=BRASS, outline=OUTLINE, width=0.012)
    c.ellipse(kx, cy + 0.08, 0.05, 0.02, fill=shade(BLOOD, 0.9), outline=OUTLINE, width=0.01)
    bx = (x0 + x1) / 2 + 0.12
    c.poly([(bx - 0.13, cy - 0.08), (bx + 0.13, cy - 0.08), (bx + 0.14, cy + 0.1), (bx - 0.14, cy + 0.1)], fill=WALNUT_D, outline=OUTLINE, width=0.012)
    c.poly([(bx - 0.12, cy - 0.06), (bx, cy - 0.05), (bx, cy + 0.09), (bx - 0.12, cy + 0.08)], fill=PARCH, outline=OUTLINE, width=0.008)
    c.poly([(bx, cy - 0.05), (bx + 0.12, cy - 0.06), (bx + 0.12, cy + 0.08), (bx, cy + 0.09)], fill=PARCH, outline=OUTLINE, width=0.008)
    for k in range(3):
        c.line([(bx - 0.1, cy - 0.02 + k * 0.03), (bx - 0.02, cy - 0.02 + k * 0.03)], fill=alpha(OUTLINE, 110), width=0.005)
        c.line([(bx + 0.02, cy - 0.02 + k * 0.03), (bx + 0.1, cy - 0.02 + k * 0.03)], fill=alpha(OUTLINE, 110), width=0.005)
    vx, vy = (x0 + x1) / 2, cloth[3] - 0.08                                                           # vertrocknete Blumen
    c.ellipse(vx, vy, 0.04, 0.025, fill=STONE_D, outline=OUTLINE, width=0.01)
    for k in range(5):
        a = math.pi * 0.3 + k * math.pi * 0.1
        c.line([(vx, vy + 0.02), (vx + 0.14 * math.cos(a), vy + 0.14 * math.sin(a))], fill=hexc("#6a5a3a"), width=0.01)
        c.ellipse(vx + 0.14 * math.cos(a), vy + 0.14 * math.sin(a), 0.018, 0.014, fill=hexc("#8a6a46"), outline=OUTLINE, width=0.006)
    cobweb(c, x0, y1 + 0.95 * K, 0.18, 1, -1, seed=idx)
    dust(c, cloth[0], cloth[1], cloth[2], cloth[3], 8, seed=idx)


def _monitorwand(p, c, x0, y0, x1, y1, idx, rnd):
    """Monitorwand der Regie: Stahlgestell, zwei Reihen Roehrenmonitore mit kaltem Bild (ein Schirm tot,
    einer rauscht), Kabelbaum, Beschriftungsstreifen, rote Betriebslampen."""
    w = x1 - x0
    p.box(x0, y0, x1, y1, 0, 0.12, MATTE_L, MATTE)                                                  # Fussrahmen
    for px_ in (x0 + 0.1, x1 - 0.1):
        c.line([(px_, y0 + 0.1), (px_, y0 + 0.1 + 2.0 * K)], fill=OUTLINE, width=0.06)
        c.line([(px_, y0 + 0.1), (px_, y0 + 0.1 + 2.0 * K)], fill=MATTE_L, width=0.035)
    n = max(3, int(w / 0.8))
    mw = (w - 0.3) / n
    for row in range(2):
        zb = y0 + 0.1 + (0.25 + row * 0.9) * K
        c.rect(x0 + 0.08, zb - 0.03, x1 - 0.08, zb + 0.01, fill=MATTE_L, outline=OUTLINE, width=0.015)   # Ablage
        for k in range(n):
            mx0 = x0 + 0.15 + k * mw
            mx1 = mx0 + mw - 0.06
            c.rect(mx0, zb, mx1, zb + 0.72 * K, fill=hexc("#3a3c44"), outline=OUTLINE, width=0.025)
            dead = (k + row * 3 + idx) % 7 == 0
            noise = (k + row + idx) % 5 == 1
            sc = (mx0 + 0.04, zb + 0.05, mx1 - 0.04, zb + 0.72 * K - 0.05)
            if dead:
                c.rect(*sc, fill=hexc("#1a1c22"), outline=OUTLINE, width=0.012)
            elif noise:
                c.rect(*sc, fill=hexc("#9aa0a8"), outline=OUTLINE, width=0.012)
                for _ in range(40):
                    c.rect(rnd.uniform(sc[0], sc[2] - 0.02), rnd.uniform(sc[1], sc[3] - 0.01), rnd.uniform(sc[0], sc[2]), rnd.uniform(sc[1], sc[3]),
                           fill=alpha(hexc("#30343a"), 120))
            else:
                col = hexc("#4a6a72") if (k + row) % 2 else hexc("#52607a")
                c.rect(*sc, fill=col, outline=OUTLINE, width=0.012)
                c.glow((sc[0] + sc[2]) / 2, (sc[1] + sc[3]) / 2, 0.3, hexc("#9ad0e0"), 0.25)
                # Raumskizze: Wandstriche, ein Rechteck, eine Figur
                c.rect(sc[0] + 0.03, sc[1] + 0.04, sc[2] - 0.03, sc[3] - 0.04, outline=shade(col, 1.5), width=0.008)
                c.rect(sc[0] + 0.08, sc[1] + 0.08, sc[0] + 0.16, sc[1] + 0.14, fill=shade(col, 0.7))
                c.ellipse(sc[2] - 0.1, sc[1] + 0.1, 0.012, 0.016, fill=shade(col, 1.6))
                for yy in (0.3, 0.6):
                    c.line([(sc[0] + 0.02, sc[1] + (sc[3] - sc[1]) * yy), (sc[2] - 0.02, sc[1] + (sc[3] - sc[1]) * yy)], fill=alpha((255, 255, 255, 255), 30), width=0.006)
            c.ellipse(mx1 - 0.03, zb + 0.03, 0.008, 0.008, fill=hexc("#ff5050") if not dead else hexc("#5a3030"))
            c.rect(mx0 + 0.02, zb + 0.72 * K + 0.01, mx0 + 0.16, zb + 0.72 * K + 0.04, fill=GAFFER)            # Beschriftung
            c.line([(mx0 + 0.04, zb + 0.72 * K + 0.025), (mx0 + 0.12, zb + 0.72 * K + 0.025)], fill=OUTLINE, width=0.008)
    for k in range(3):                                                                            # Kabelbaum
        cable(c, [(x0 + 0.4 + k * 0.5, y0 + 0.1 + 0.25 * K), (x0 + 0.5 + k * 0.5, y0 - 0.05), (x0 + 0.2 + k * 0.7, y0 - 0.12)], seed=idx + k, w=0.02)
    gaffer(c, x0 + 0.3, y0 + 0.14 * K, x0 + 0.9, y0 + 0.14 * K + 0.01, 0.04)
    cobweb(c, x1 - 0.1, y0 + 0.1 + 2.0 * K, 0.16, -1, -1, seed=idx)


def _gewehrschrank(p, c, x0, y0, x1, y1, idx, rnd):
    """Gewehrschrank: Nussholz mit zwei Glastueren, dahinter Jagdgewehre (Silhouetten), Schloss,
    Geweih auf dem Kranz, eine Tuer einen Spalt offen."""
    w = x1 - x0
    H = 2.0
    p.box(x0, y0, x1, y1, 0, H, WALNUT_L, WALNUT)
    fz = y0
    c.rect(x0 + 0.05, fz + 0.08 * K, x1 - 0.05, fz + 0.35 * K, outline=WALNUT_D, width=0.012)          # Sockelschublade
    c.ellipse((x0 + x1) / 2, fz + 0.21 * K, 0.02, 0.016, fill=BRASS, outline=OUTLINE, width=0.01)
    gx0, gx1 = x0 + 0.08, x1 - 0.08
    gz0, gz1 = fz + 0.42 * K, fz + 1.85 * K
    c.rect(gx0, gz0, gx1, gz1, fill=hexc("#2a2228"), outline=OUTLINE, width=0.02)
    n = max(3, int(w / 0.4))
    for k in range(n):                                                                            # Gewehre
        rx = gx0 + 0.15 + k * (gx1 - gx0 - 0.3) / max(1, n - 1)
        c.line([(rx, gz0 + 0.05), (rx + 0.03, gz1 - 0.1)], fill=OUTLINE, width=0.05)
        c.line([(rx, gz0 + 0.05), (rx + 0.03, gz1 - 0.1)], fill=lift("#4a2e1c", 1.4), width=0.03)
        c.line([(rx + 0.015, gz0 + 0.5), (rx + 0.03, gz1 - 0.08)], fill=STEEL, width=0.014)
        c.rect(rx - 0.03, gz0 + 0.35, rx + 0.04, gz0 + 0.42, fill=WALNUT_D, outline=OUTLINE, width=0.01)
    c.line([(gx0, gz0), (gx0, gz1)], fill=OUTLINE, width=0.02)
    mid = (gx0 + gx1) / 2
    for (ax, bx) in ((gx0, mid), (mid, gx1)):                                                      # Glastueren
        c.rect(ax + 0.01, gz0 + 0.01, bx - 0.01, gz1 - 0.01, fill=alpha(hexc("#b8c8d8"), 60), outline=WALNUT_D, width=0.025)
        c.line([(ax + 0.08, gz1 - 0.1), (ax + 0.3, gz0 + 0.1)], fill=alpha((255, 255, 255, 255), 60), width=0.03)
    c.ellipse(mid - 0.03, (gz0 + gz1) / 2, 0.018, 0.015, fill=BRASS, outline=OUTLINE, width=0.01)
    c.ellipse(mid + 0.03, (gz0 + gz1) / 2, 0.018, 0.015, fill=BRASS, outline=OUTLINE, width=0.01)
    if idx % 2 == 1:                                                                               # Tuer offen: dunkler Spalt
        c.rect(mid, gz0 + 0.01, mid + 0.05, gz1 - 0.01, fill=hexc("#16121a"))
    top = y1 + H * K
    c.rect(x0 - 0.03, top - 0.08, x1 + 0.03, top, fill=WALNUT_L, outline=OUTLINE, width=0.02)          # Kranz
    ax = (x0 + x1) / 2
    for sx in (-1, 1):                                                                            # Geweih
        pts = [(ax, top + 0.02), (ax + sx * 0.08, top + 0.1), (ax + sx * 0.18, top + 0.14), (ax + sx * 0.22, top + 0.24)]
        c.line(pts, fill=OUTLINE, width=0.04)
        c.line(pts, fill=CREAM_D, width=0.022)
        c.line([(ax + sx * 0.12, top + 0.115), (ax + sx * 0.1, top + 0.2)], fill=OUTLINE, width=0.035)
        c.line([(ax + sx * 0.12, top + 0.115), (ax + sx * 0.1, top + 0.2)], fill=CREAM_D, width=0.018)
    c.ellipse(ax, top + 0.04, 0.045, 0.03, fill=WALNUT_D, outline=OUTLINE, width=0.012)
    dust(c, x0 + 0.1, top + 0.02, x1 - 0.1, y1 + H * K - 0.02, 6, seed=idx)
    cobweb(c, x0 + 0.08, gz1, 0.14, 1, -1, seed=idx)


def _zelt(p, c, x0, y0, x1, y1, idx, rnd):
    """Crew-Pavillon: vier Stangen, Walmdach aus Plane, offene Front mit Kisten und Haengelampe,
    Spannseile, Tape-Beschriftung."""
    w, d = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    ze, zp = 2.0, 2.55
    inner = hexc("#2a2c30")
    # Innenraum (dunkel) mit Kisten
    c.poly([(x0 + 0.1, y0 + 0.1), (x1 - 0.1, y0 + 0.1), (x1 - 0.1, y1 - 0.1 + ze * K), (x0 + 0.1, y1 - 0.1 + ze * K)], fill=inner)
    crate = lift("#6a4a2c", 1.4)
    p.box(x0 + 0.5, y0 + 0.9, x0 + 1.3, y0 + 1.5, 0, 0.55, shade(crate, 1.15), crate)
    p.box(x1 - 1.4, y0 + 0.8, x1 - 0.5, y0 + 1.4, 0, 0.5, MATTE_L, MATTE)
    c.line([(x1 - 1.35, y0 + 0.8 + 0.25 * K), (x1 - 0.55, y0 + 0.8 + 0.25 * K)], fill=STEEL, width=0.012)
    p.box(x0 + 0.6, y0 + 1.5, x0 + 1.2, y0 + 1.9, 0.55, 0.4, shade(crate, 1.1), shade(crate, 0.95))
    # Haengelampe mit warmem Schein
    c.glow(cx, y0 + 1.0 + 1.0 * K, 0.9, WARM, 0.35)
    c.line([(cx, y0 + 1.0 + 1.9 * K), (cx, y0 + 1.0 + 1.55 * K)], fill=MATTE_D, width=0.012)
    c.poly([(cx - 0.12, y0 + 1.0 + 1.55 * K), (cx + 0.12, y0 + 1.0 + 1.55 * K), (cx + 0.07, y0 + 1.0 + 1.62 * K), (cx - 0.07, y0 + 1.0 + 1.62 * K)],
           fill=MATTE, outline=OUTLINE, width=0.015)
    c.ellipse(cx, y0 + 1.0 + 1.53 * K, 0.04, 0.03, fill=BULB)
    # Stangen (vordere), Dach, hintere Stangen stehen unter dem Dach
    for px_, py_ in ((x0 + 0.1, y0 + 0.1), (x1 - 0.1, y0 + 0.1)):
        c.line([(px_, py_), (px_, py_ + ze * K)], fill=OUTLINE, width=0.06)
        c.line([(px_, py_), (px_, py_ + ze * K)], fill=STEEL, width=0.035)
    f0, f1 = y0 + ze * K, y1 + ze * K
    peak = (cx, (y0 + y1) / 2 + zp * K)
    roof = [(x0 - 0.05, f0), (x1 + 0.05, f0), (x1 + 0.05, f1), (x0 - 0.05, f1)]
    c.poly([roof[0], roof[1], peak], fill=shade(CANVAS, 1.1), outline=OUTLINE, width=A.OUT_W)         # Suedflaeche
    c.poly([roof[1], roof[2], peak], fill=shade(CANVAS, 0.85), outline=OUTLINE, width=A.OUT_W)        # Ost
    c.poly([roof[2], roof[3], peak], fill=shade(CANVAS, 0.95), outline=OUTLINE, width=A.OUT_W)        # Nord
    c.poly([roof[3], roof[0], peak], fill=shade(CANVAS, 1.2), outline=OUTLINE, width=A.OUT_W)         # West
    for k in range(4):                                                                            # Planenfalten
        t = (k + 1) / 5
        c.line([(x0 + w * t, f0 + 0.02), (cx + (x0 + w * t - cx) * 0.2, peak[1] - 0.05)], fill=alpha(CANVAS_D, 110), width=0.012)
    c.rect(x0 - 0.05, f0 - 0.1, x1 + 0.05, f0 + 0.02, fill=CANVAS_D, outline=OUTLINE, width=0.025)   # Volant
    xx = x0
    while xx < x1:
        c.poly([(xx, f0 - 0.1), (xx + 0.15, f0 - 0.1), (xx + 0.075, f0 - 0.17)], fill=CANVAS_D, outline=OUTLINE, width=0.015)
        xx += 0.15
    c.ellipse(peak[0], peak[1], 0.05, 0.03, fill=STEEL, outline=OUTLINE, width=0.015)
    gaffer(c, x0 + 0.3, f0 - 0.05, x0 + 0.9, f0 - 0.05, 0.05)
    c.text(x0 + 0.6, f0 - 0.05, "CREW", 0.045, OUTLINE)
    for px_, sx in ((x0 + 0.1, -1), (x1 - 0.1, 1)):                                                # Spannseile mit Heringen
        c.line([(px_, f0 - 0.02), (px_ + sx * 0.45, y0 - 0.25)], fill=alpha(CREAM_D, 200), width=0.012)
        c.line([(px_ + sx * 0.45, y0 - 0.25), (px_ + sx * 0.48, y0 - 0.19)], fill=OUTLINE, width=0.03)
    cable(c, [(x1 - 0.9, y0 + 0.8), (x1 - 0.5, y0 + 0.3), (x1 + 0.2, y0 - 0.1)], seed=idx)
    c.ellipse(x0 + 0.5, y0 - 0.02, 0.15, 0.07, fill=alpha(hexc("#4a4034"), 120))                     # festgetretener Boden


def _hecke(p, c, x0, y0, x1, y1, idx, rnd):
    hedge_mass(c, x0, y0, x1, y1, 1.2, seed=idx)


def _kuechentisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Kuechentisch: schwerer Holztisch, Hackbrett mit Beil und Requisiten-Messern, Kunstblut auf dem
    Brett und Tropfen an der Kante, Schuessel, Mehlsack, Flasche Kunstblut."""
    w = x1 - x0
    p.box(x0, y0, x1, y1, 0, 0.8, WALNUT_L, WALNUT)
    for lx in (x0 + 0.06, x1 - 0.14):
        c.rect(lx, y0 + 0.05, lx + 0.08, y0 + 0.75 * K, fill=WALNUT_D, outline=OUTLINE, width=0.015)
    c.rect(x0 + 0.14, y0 + 0.1 * K, x1 - 0.14, y0 + 0.62 * K, fill=alpha((0, 0, 0, 255), 110))           # Schatten unter der Platte
    c.rect(x0, y0 + 0.62 * K, x1, y0 + 0.8 * K, fill=WALNUT, outline=OUTLINE, width=0.025)             # Zarge
    zt = y0 + 0.8 * K
    for k in range(3):                                                                            # Maserung der Platte
        yy = zt + 0.1 + k * (y1 - y0 - 0.2) / 2
        c.line(HD.wobble([(x0 + 0.1, yy), (x1 - 0.1, yy + 0.01)], amp=0.006, seed=idx + k, step=0.1), fill=alpha(WALNUT_D, 110), width=0.008)
    bx, by = x0 + w * 0.35, zt + (y1 - y0) * 0.45
    c.poly([(bx - 0.32, by - 0.14), (bx + 0.32, by - 0.14), (bx + 0.34, by + 0.14), (bx - 0.3, by + 0.14)], fill=CREAM_D, outline=OUTLINE, width=0.015)   # Hackbrett
    blood_pool(c, bx + 0.05, by + 0.02, 0.14, 0.07, seed=idx, a=220)
    c.line([(bx + 0.15, by + 0.08), (bx + 0.33, by - 0.1)], fill=alpha(BLOOD, 160), width=0.03)
    knife(c, bx - 0.25, by - 0.05, 0.15, 0.9)
    knife(c, bx + 0.05, by + 0.1, -0.5, 0.75)
    # Beil steckt im Brett
    hx = bx - 0.05
    c.line([(hx, by - 0.02), (hx + 0.1, by + 0.28)], fill=OUTLINE, width=0.05)
    c.line([(hx, by - 0.02), (hx + 0.1, by + 0.28)], fill=WALNUT_D, width=0.03)
    c.poly([(hx - 0.08, by - 0.1), (hx + 0.1, by - 0.1), (hx + 0.08, by + 0.04), (hx - 0.04, by + 0.04)], fill=STEEL, outline=OUTLINE, width=0.015)
    c.line([(hx - 0.06, by - 0.08), (hx + 0.07, by - 0.08)], fill=alpha((255, 255, 255, 255), 130), width=0.008)
    blood_drips(c, x0 + w * 0.3, zt, 3, 0.2, seed=idx)
    c.ellipse(x1 - 0.5, zt + 0.25, 0.16, 0.08, fill=hexc("#8a9aa8"), outline=OUTLINE, width=0.015)      # Schuessel
    c.ellipse(x1 - 0.5, zt + 0.27, 0.11, 0.05, fill=hexc("#5a6a78"))
    sx, sy = x0 + 0.35, zt + (y1 - y0) * 0.8                                                        # Mehlsack
    c.poly(HD.wobble_ellipse(sx, sy, 0.2, 0.12, amp=0.015, seed=idx), fill=CREAM_D, outline=OUTLINE, width=0.015)
    c.line([(sx - 0.08, sy + 0.1), (sx + 0.08, sy + 0.12)], fill=OUTLINE, width=0.012)
    c.ellipse(sx + 0.22, sy - 0.06, 0.06, 0.03, fill=alpha(CREAM, 200))
    bottle(c, x1 - 0.25, zt + 0.5, 0.28, BLOOD_L, label=CREAM, r=0.035)
    c.text(x1 - 0.25, zt + 0.6, "FX", 0.035, OUTLINE)
    c.rect(x1 - 0.9, zt + 0.05, x1 - 0.55, zt + 0.12, fill=hexc("#6a7a8a"), outline=OUTLINE, width=0.01)   # Lappen
    blood_pool(c, x1 - 0.72, zt + 0.09, 0.05, 0.02, seed=idx + 2, a=160)


def _waschzuber(p, c, x0, y0, x1, y1, idx, rnd):
    """Waschzuber: Holzfass mit Eisenreifen, dunkles Wasser mit rot ausgewaschenem Tuch, Waschbrett."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    p.cyl(cx, cy, r, 0, 0.6, WALNUT_D, WALNUT, ry=r * 0.5)
    for k in range(9):                                                                            # Dauben
        sx = cx - r + 0.05 + k * (2 * r - 0.1) / 8
        c.line([(sx, cy + 0.02), (sx, cy + 0.6 * K - 0.02)], fill=alpha(WALNUT_D, 170), width=0.012)
    for z in (0.12, 0.48):
        c.line([(cx - r + 0.01, cy + z * K), (cx + r - 0.01, cy + z * K)], fill=IRON, width=0.035)
        c.line([(cx - r + 0.03, cy + z * K + 0.012), (cx + r - 0.03, cy + z * K + 0.012)], fill=IRON_L, width=0.008)
    top = cy + 0.6 * K
    c.ellipse(cx, top, r - 0.05, (r - 0.05) * 0.5, fill=hexc("#3a4a56"), outline=WALNUT_D, width=0.012)
    c.ellipse(cx - 0.1, top + 0.05, r * 0.4, r * 0.15, fill=alpha(MOON, 60))
    c.poly(HD.wobble_ellipse(cx + 0.12, top - 0.03, 0.2, 0.08, amp=0.02, seed=idx), fill=hexc("#b8a8a0"), outline=OUTLINE, width=0.012)   # Tuch
    c.poly(HD.wobble_ellipse(cx + 0.16, top - 0.03, 0.1, 0.045, amp=0.015, seed=idx + 1), fill=alpha(BLOOD, 120))
    c.poly(HD.wobble_ellipse(cx + 0.3, top - 0.06, 0.15, 0.05, amp=0.01, seed=idx + 2), fill=alpha(BLOOD, 70))
    # Waschbrett lehnt am Zuber
    bx = cx - r - 0.05
    c.poly([(bx - 0.12, cy - 0.1), (bx + 0.1, cy - 0.12), (bx + 0.16, cy + 0.6), (bx - 0.06, cy + 0.62)], fill=WALNUT_L, outline=OUTLINE, width=0.02)
    for k in range(7):
        c.line([(bx - 0.08 + k * 0.012, cy + 0.05 + k * 0.07), (bx + 0.1 + k * 0.012, cy + 0.03 + k * 0.07)], fill=STEEL, width=0.012)
    c.ellipse(cx + r * 0.5, cy - r * 0.35, 0.12, 0.05, fill=alpha(hexc("#3a4a56"), 120))             # Pfuetze
    c.ellipse(cx + r * 0.55, cy - r * 0.35, 0.05, 0.02, fill=alpha(BLOOD, 90))


def _requisiten(p, c, x0, y0, x1, y1, idx, rnd):
    """Requisitenwagen: Stahlregal auf Rollen mit drei Boeden: Schaedel (Plastik), Gummimesser, Flaschen
    Kunstblut, Bandagen, eine Kunsthand, Laterne, Beschriftung."""
    w = x1 - x0
    for wx in (x0 + 0.12, x1 - 0.12):
        c.ellipse(wx, y0 + 0.04, 0.05, 0.035, fill=MATTE_D, outline=OUTLINE, width=0.015)
    for px_ in (x0 + 0.05, x1 - 0.05):
        c.line([(px_, y0 + 0.06), (px_, y0 + 0.06 + 1.5 * K)], fill=OUTLINE, width=0.05)
        c.line([(px_, y0 + 0.06), (px_, y0 + 0.06 + 1.5 * K)], fill=STEEL, width=0.028)
    for k, z in enumerate((0.15, 0.75, 1.35)):
        p.box(x0, y0 + 0.02, x1, y1, z, 0.04, shade(STEEL, 1.1), shade(STEEL, 0.8), w=0.02)
        zt = y0 + 0.02 + (z + 0.04) * K
        yt0, yt1 = zt + 0.05, y1 + (z + 0.04) * K - 0.05
        if k == 0:
            for j in range(3):
                bottle(c, x0 + 0.18 + j * 0.12, yt0 + 0.02, 0.26, BLOOD_L if j < 2 else hexc("#4a7a9a"), label=CREAM, r=0.03)
            c.rect(x1 - 0.45, yt0, x1 - 0.1, yt0 + 0.12, fill=CREAM, outline=OUTLINE, width=0.012)                # Bandagen
            c.ellipse(x1 - 0.3, yt0 + 0.12, 0.12, 0.04, fill=CREAM_D, outline=OUTLINE, width=0.012)
        elif k == 1:
            sx, sy = x0 + 0.25, yt0 + 0.08
            c.ellipse(sx, sy + 0.08, 0.1, 0.09, fill=CREAM, outline=OUTLINE, width=0.02)                           # Schaedel
            c.rect(sx - 0.06, sy - 0.02, sx + 0.06, sy + 0.03, fill=CREAM_D, outline=OUTLINE, width=0.015)
            for ex in (-0.04, 0.04):
                c.ellipse(sx + ex, sy + 0.08, 0.03, 0.03, fill=hexc("#1a1418"))
            c.poly([(sx - 0.012, sy + 0.05), (sx + 0.012, sy + 0.05), (sx, sy + 0.02)], fill=hexc("#1a1418"))
            for j in range(4):
                c.line([(sx - 0.045 + j * 0.03, sy - 0.02), (sx - 0.045 + j * 0.03, sy + 0.02)], fill=alpha(OUTLINE, 150), width=0.006)
            knife(c, x0 + 0.55, yt0 + 0.08, 0.2, 0.8, blade=hexc("#9aa0a8"))
            knife(c, x0 + 0.6, yt0 + 0.16, -0.1, 0.7, blade=hexc("#b0b4b8"))
            hx = x1 - 0.2
            c.poly([(hx - 0.06, yt0), (hx + 0.06, yt0), (hx + 0.07, yt0 + 0.12), (hx - 0.07, yt0 + 0.12)], fill=hexc("#d8b8a8"), outline=OUTLINE, width=0.012)   # Kunsthand
            for j in range(4):
                c.line([(hx - 0.05 + j * 0.033, yt0 + 0.12), (hx - 0.05 + j * 0.033, yt0 + 0.2)], fill=hexc("#d8b8a8"), width=0.022)
                c.line([(hx - 0.05 + j * 0.033, yt0 + 0.12), (hx - 0.05 + j * 0.033, yt0 + 0.2)], fill=alpha(OUTLINE, 160), width=0.004)
            c.ellipse(hx, yt0 + 0.01, 0.06, 0.02, fill=alpha(BLOOD, 170))
        else:
            lx = x0 + 0.3
            c.rect(lx - 0.08, yt0 + 0.02, lx + 0.08, yt0 + 0.24, fill=alpha(hexc("#c8d8e8"), 160), outline=OUTLINE, width=0.015)   # Laterne
            c.rect(lx - 0.1, yt0, lx + 0.1, yt0 + 0.03, fill=IRON, outline=OUTLINE, width=0.012)
            c.rect(lx - 0.1, yt0 + 0.24, lx + 0.1, yt0 + 0.27, fill=IRON, outline=OUTLINE, width=0.012)
            c.line([(lx - 0.07, yt0 + 0.27), (lx, yt0 + 0.34), (lx + 0.07, yt0 + 0.27)], fill=IRON, width=0.012)
            flame(c, lx, yt0 + 0.07, 0.9)
            c.rect(x0 + 0.55, yt0 + 0.02, x1 - 0.1, yt0 + 0.14, fill=hexc("#5a4a3a"), outline=OUTLINE, width=0.012)   # Koffer
            c.rect(x0 + 0.57, yt0 + 0.14, x1 - 0.12, yt0 + 0.3, fill=hexc("#4a3a2c"), outline=OUTLINE, width=0.012)
            for j in range(3):
                c.ellipse(x0 + 0.68 + j * 0.12, yt0 + 0.21, 0.025, 0.02, fill=rnd.choice((BLOOD_L, CREAM, hexc("#8a9a6a"))), outline=OUTLINE, width=0.008)
    gaffer(c, x0 + 0.1, y0 + 0.06 + 0.7 * K, x0 + 0.5, y0 + 0.06 + 0.7 * K, 0.04)
    c.text(x0 + 0.3, y0 + 0.06 + 0.7 * K, "FX", 0.035, OUTLINE)
    cable(c, [(x1 - 0.1, y0 + 0.1), (x1 + 0.15, y0 - 0.05), (x1 + 0.35, y0 - 0.02)], seed=idx)


def _teleskop(p, c, x0, y0, x1, y1, idx, rnd):
    """Teleskop: Holzstativ, Messingtubus nach oben rechts, Okular unten, Sternkarte am Boden."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    c.poly([(cx - 0.25, cy - 0.15), (cx + 0.2, cy - 0.2), (cx + 0.22, cy), (cx - 0.23, cy + 0.05)], fill=PARCH, outline=OUTLINE, width=0.012)   # Sternkarte
    for k in range(6):
        c.ellipse(cx - 0.18 + k * 0.07, cy - 0.12 + (k % 3) * 0.05, 0.008, 0.008, fill=WALNUT_D)
    c.ellipse(cx - 0.02, cy - 0.08, 0.07, 0.04, outline=WALNUT_D, width=0.006)
    top = (cx, cy + 1.15 * K)
    for lx, ly in ((cx - r * 0.8, cy - r * 0.3), (cx + r * 0.8, cy - r * 0.25), (cx + r * 0.1, cy + r * 0.45)):
        c.line([top, (lx, ly)], fill=OUTLINE, width=0.05)
        c.line([top, (lx, ly)], fill=WALNUT, width=0.028)
        c.ellipse(lx, ly, 0.03, 0.018, fill=BRASS, outline=OUTLINE, width=0.01)
    c.ellipse(top[0], top[1], 0.06, 0.04, fill=BRASS, outline=OUTLINE, width=0.015)
    a = math.radians(38)
    L0 = 0.25
    ex, ey = cx - math.cos(a) * L0, top[1] - math.sin(a) * L0
    fx, fy = cx + math.cos(a) * 0.75, top[1] + math.sin(a) * 0.75
    nx, ny = -math.sin(a) * 0.07, math.cos(a) * 0.07
    c.poly([(ex + nx * 0.7, ey + ny * 0.7), (fx + nx, fy + ny), (fx - nx, fy - ny), (ex - nx * 0.7, ey - ny * 0.7)], fill=BRASS, outline=OUTLINE, width=0.025)
    c.line([(ex + nx * 0.4, ey + ny * 0.4), (fx + nx * 0.6, fy + ny * 0.6)], fill=BRASS_L, width=0.015)
    for t in (0.3, 0.6):
        px_, py_ = ex + (fx - ex) * t, ey + (fy - ey) * t
        c.line([(px_ + nx, py_ + ny), (px_ - nx, py_ - ny)], fill=BRASS_D, width=0.018)
    c.ellipse(fx, fy, 0.075, 0.075, fill=BRASS_D, outline=OUTLINE, width=0.02)
    c.ellipse(fx, fy, 0.05, 0.05, fill=hexc("#2a3a52"))
    c.ellipse(fx - 0.015, fy + 0.015, 0.015, 0.012, fill=alpha((255, 255, 255, 255), 180))
    c.ellipse(ex, ey, 0.04, 0.04, fill=MATTE_D, outline=OUTLINE, width=0.015)
    c.rect(cx - 0.05, top[1] - 0.02, cx + 0.05, top[1] + 0.12, fill=BRASS_D, outline=OUTLINE, width=0.012)
    cobweb(c, cx + r * 0.8, cy - r * 0.25 + 0.3, 0.12, -1, 1, seed=idx)


def _kohlen(p, c, x0, y0, x1, y1, idx, rnd):
    """Kohlenhaufen: Kohlebrocken mit Glanz, Schaufel steckt drin, Eimer, Staub am Boden."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    c.ellipse(cx, cy, rx * 1.05, ry * 0.9, fill=alpha((10, 8, 10, 255), 120))
    c.poly(HD.wobble_ellipse(cx, cy + 0.15, rx * 0.95, ry * 0.9, amp=0.03, seed=idx), fill=hexc("#2a282c"), outline=OUTLINE, width=A.OUT_W)
    for i in range(60):
        a = rnd.uniform(0, math.tau)
        d = rnd.uniform(0, 0.95)
        px_, py_ = cx + math.cos(a) * rx * 0.85 * d, cy + 0.15 + math.sin(a) * ry * 0.75 * d + (1 - d) * 0.2
        s = rnd.uniform(0.04, 0.09)
        pts = [(px_ + s * math.cos(t) * rnd.uniform(0.7, 1.1), py_ + s * 0.7 * math.sin(t) * rnd.uniform(0.7, 1.1)) for t in [k * math.tau / 6 for k in range(6)]]
        c.poly(pts, fill=hexc("#34323a") if i % 3 else hexc("#2a282e"), outline=OUTLINE, width=0.012)
        c.line([(pts[1][0], pts[1][1] - 0.01), (pts[2][0] + 0.01, pts[2][1])], fill=alpha((200, 210, 230, 255), 90), width=0.008)
    sx, sy = cx + rx * 0.4, cy + 0.3
    c.line([(sx, sy), (sx + 0.25, sy + 0.55)], fill=OUTLINE, width=0.05)
    c.line([(sx, sy), (sx + 0.25, sy + 0.55)], fill=WALNUT_L, width=0.03)
    c.rect(sx + 0.2, sy + 0.55, sx + 0.3, sy + 0.62, fill=WALNUT_D, outline=OUTLINE, width=0.012)
    c.poly([(sx - 0.14, sy + 0.02), (sx + 0.1, sy - 0.04), (sx + 0.13, sy + 0.14), (sx - 0.1, sy + 0.2)], fill=STEEL, outline=OUTLINE, width=0.02)
    bx, by = x0 + 0.25, y0 + 0.05
    p.cyl(bx, by, 0.14, 0, 0.3, hexc("#3a3c44"), IRON, ry=0.07)
    c.ellipse(bx, by + 0.3 * K, 0.11, 0.05, fill=hexc("#1e1c20"))
    c.ellipse(bx, by + 0.3 * K + 0.08, 0.14, 0.07, outline=OUTLINE, width=0.03)
    c.ellipse(bx, by + 0.3 * K + 0.08, 0.14, 0.07, outline=STEEL, width=0.015)
    for _ in range(8):
        c.ellipse(rnd.uniform(x0 - 0.1, x1 + 0.1), rnd.uniform(y0 - 0.15, y0 + 0.1), 0.02, 0.012, fill=alpha((20, 18, 22, 255), 140))


def _lesetisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Lesetisch: Nussholz, Bankerlampe (Lichtinsel), aufgeschlagenes Buch, Buecherstapel, Tintenfass mit
    Feder, Lupe, ein Zettel mit Blutfingerabdruck."""
    p.box(x0, y0, x1, y1, 0, 0.78, WALNUT_L, WALNUT)
    for lx in (x0 + 0.06, x1 - 0.12):
        c.rect(lx, y0 + 0.04, lx + 0.06, y0 + 0.66 * K, fill=WALNUT_D, outline=OUTLINE, width=0.015)
    c.rect(x0 + 0.12, y0 + 0.08 * K, x1 - 0.12, y0 + 0.6 * K, fill=alpha((0, 0, 0, 255), 110))
    c.rect(x0, y0 + 0.6 * K, x1, y0 + 0.78 * K, fill=WALNUT, outline=OUTLINE, width=0.025)
    zt = y0 + 0.78 * K
    cx = (x0 + x1) / 2
    floor_light(c, cx + 0.2, y0 - 0.1, 0.9, 0.4, WARM, 0.2, seed=idx)
    banker_lamp(c, x1 - 0.4, zt + 0.35, 1.0)
    bx, by = cx - 0.1, zt + 0.22
    c.poly([(bx - 0.26, by - 0.14), (bx + 0.26, by - 0.14), (bx + 0.28, by + 0.14), (bx - 0.28, by + 0.14)], fill=lift("#5a1e22", 1.4), outline=OUTLINE, width=0.015)
    c.poly([(bx - 0.24, by - 0.12), (bx, by - 0.1), (bx, by + 0.12), (bx - 0.25, by + 0.11)], fill=PARCH, outline=OUTLINE, width=0.01)
    c.poly([(bx, by - 0.1), (bx + 0.24, by - 0.12), (bx + 0.25, by + 0.11), (bx, by + 0.12)], fill=PARCH, outline=OUTLINE, width=0.01)
    for k in range(5):
        c.line([(bx - 0.2, by - 0.06 + k * 0.035), (bx - 0.05, by - 0.06 + k * 0.035)], fill=alpha(OUTLINE, 110), width=0.005)
        c.line([(bx + 0.05, by - 0.06 + k * 0.035), (bx + 0.2, by - 0.06 + k * 0.035)], fill=alpha(OUTLINE, 110), width=0.005)
    c.ellipse(bx + 0.14, by + 0.04, 0.03, 0.02, fill=alpha(BLOOD, 150))                                # Fingerabdruck
    book_stack(c, x0 + 0.15, zt + 0.3, 4, rnd=rnd)
    ix, iy = x0 + 0.5, zt + 0.1
    c.rect(ix - 0.04, iy, ix + 0.04, iy + 0.07, fill=hexc("#2a2e44"), outline=OUTLINE, width=0.012)
    c.line([(ix + 0.02, iy + 0.07), (ix + 0.14, iy + 0.3)], fill=CREAM, width=0.016)
    c.line([(ix + 0.02, iy + 0.07), (ix + 0.14, iy + 0.3)], fill=alpha(OUTLINE, 120), width=0.004)
    lx, ly = x1 - 0.75, zt + 0.12
    c.ellipse(lx, ly, 0.06, 0.05, fill=alpha(GLASS, 150), outline=BRASS, width=0.015)
    c.line([(lx + 0.05, ly - 0.03), (lx + 0.16, ly - 0.1)], fill=OUTLINE, width=0.03)
    c.line([(lx + 0.05, ly - 0.03), (lx + 0.16, ly - 0.1)], fill=WALNUT_D, width=0.018)
    candle(c, x0 + 0.3, zt + 0.1, 0.12, idx % 2 == 0, r=0.025, seed=idx)
    dust(c, x0 + 0.1, zt + 0.05, x1 - 0.1, y1 + 0.78 * K - 0.05, 6, seed=idx)


def _kirchenbank(p, c, x0, y0, x1, y1, idx, rnd):
    """Kirchenbank: Sitzbrett auf Wangen, hohe Rueckenlehne, Gesangbuch, Spinnwebe an einem Ende."""
    for wx in (x0 + 0.02, x1 - 0.1):
        c.rect(wx, y0 + 0.02, wx + 0.08, y0 + 0.02 + 0.45 * K, fill=WALNUT_D, outline=OUTLINE, width=0.015)
    p.box(x0, y0 + 0.05, x1, y1 - 0.12, 0.42, 0.06, WALNUT_L, WALNUT, w=0.025)
    p.box(x0, y1 - 0.14, x1, y1, 0.45, 0.5, WALNUT_L, WALNUT, w=0.025)
    fy = y1 - 0.14 + 0.45 * K
    for k in range(int((x1 - x0) / 0.5)):                                                        # Lehnenbretter
        sx = x0 + 0.25 + k * 0.5
        c.line([(sx, fy + 0.03), (sx, fy + 0.5 * K - 0.03)], fill=WALNUT_D, width=0.01)
    c.line([(x0 + 0.03, fy + 0.5 * K - 0.02), (x1 - 0.03, fy + 0.5 * K - 0.02)], fill=alpha((255, 255, 255, 255), 40), width=0.01)
    zt = y0 + 0.05 + 0.48 * K
    for k in range(3):                                                                            # Maserung Sitz
        c.line(HD.wobble([(x0 + 0.2, zt + 0.03 + k * 0.03), (x1 - 0.2, zt + 0.035 + k * 0.03)], amp=0.004, seed=idx + k, step=0.1), fill=alpha(WALNUT_D, 100), width=0.006)
    bx = x0 + (x1 - x0) * (0.3 if idx % 2 else 0.65)
    c.rect(bx - 0.08, zt + 0.02, bx + 0.08, zt + 0.1, fill=lift("#2a2a3a", 1.5), outline=OUTLINE, width=0.012)
    c.line([(bx - 0.03, zt + 0.06), (bx + 0.03, zt + 0.06)], fill=BRASS, width=0.008)
    c.ellipse(bx + 0.2, zt + 0.07, 0.04, 0.02, fill=alpha(CREAM, 150))
    cobweb(c, x1, y1 + 0.95 * K, 0.16, -1, -1, seed=idx)
    c.rect(x0 + 0.1, zt + 0.01, x1 - 0.1, zt + 0.02, fill=alpha((0, 0, 0, 255), 40))


def _baer(p, c, x0, y0, x1, y1, idx, rnd):
    """Praeparierter Baer: steht aufgerichtet auf Holzsockel, Arme erhoben, offenes Maul, Glasaugen."""
    cx = (x0 + x1) / 2
    fur = lift("#3a2a1e", 1.6)
    fur_l = shade(fur, 1.3)
    fur_d = shade(fur, 0.72)
    p.box(x0, y0, x1, y1, 0, 0.18, WALNUT_L, WALNUT)
    c.rect(x0 + 0.05, y0 + 0.02, x1 - 0.05, y0 + 0.16 * K, outline=BRASS_D, width=0.01)
    by = y0 + 0.3 + 0.18 * K
    for lx in (cx - 0.22, cx + 0.22):                                                             # Beine
        c.poly([(lx - 0.16, by), (lx + 0.16, by), (lx + 0.12, by + 0.6), (lx - 0.12, by + 0.6)], fill=fur, outline=OUTLINE, width=A.OUT_W)
        for k in range(4):
            c.line([(lx - 0.12 + k * 0.08, by + 0.02), (lx - 0.12 + k * 0.08, by - 0.04)], fill=OUTLINE, width=0.02)
    body = HD.wobble_ellipse(cx, by + 1.0, 0.5, 0.6, amp=0.02, seed=idx)
    c.poly(body, fill=fur, outline=OUTLINE, width=A.OUT_W)
    c.poly(HD.wobble_ellipse(cx + 0.05, by + 0.9, 0.3, 0.4, amp=0.015, seed=idx + 1), fill=fur_l)
    c.poly(HD.wobble_ellipse(cx - 0.3, by + 1.0, 0.18, 0.5, amp=0.015, seed=idx + 2), fill=alpha(fur_d, 160))
    for sx in (-1, 1):                                                                            # Arme erhoben
        pts = [(cx + sx * 0.38, by + 1.2), (cx + sx * 0.62, by + 1.4), (cx + sx * 0.7, by + 1.75), (cx + sx * 0.52, by + 1.78), (cx + sx * 0.46, by + 1.5), (cx + sx * 0.3, by + 1.45)]
        c.poly(pts, fill=fur, outline=OUTLINE, width=A.OUT_W)
        c.line([(cx + sx * 0.44, by + 1.3), (cx + sx * 0.6, by + 1.6)], fill=fur_l, width=0.03)
        for k in range(4):
            c.line([(cx + sx * (0.5 + k * 0.06), by + 1.77), (cx + sx * (0.5 + k * 0.06), by + 1.85)], fill=OUTLINE, width=0.02)
    hx, hy = cx, by + 1.75
    c.ellipse(hx, hy, 0.3, 0.26, fill=fur, outline=OUTLINE, width=A.OUT_W)
    for sx in (-1, 1):
        c.ellipse(hx + sx * 0.24, hy + 0.2, 0.08, 0.08, fill=fur, outline=OUTLINE, width=0.03)
        c.ellipse(hx + sx * 0.24, hy + 0.2, 0.04, 0.04, fill=fur_d)
    c.ellipse(hx, hy - 0.08, 0.17, 0.13, fill=fur_l, outline=OUTLINE, width=0.025)                   # Schnauze
    c.poly([(hx - 0.14, hy - 0.1), (hx + 0.14, hy - 0.1), (hx + 0.1, hy - 0.22), (hx - 0.1, hy - 0.22)], fill=hexc("#5a1e26"), outline=OUTLINE, width=0.025)   # Maul
    for k in range(4):
        c.poly([(hx - 0.1 + k * 0.065, hy - 0.1), (hx - 0.06 + k * 0.065, hy - 0.1), (hx - 0.08 + k * 0.065, hy - 0.16)], fill=CREAM)
    c.ellipse(hx, hy + 0.02, 0.05, 0.035, fill=hexc("#1a1418"), outline=OUTLINE, width=0.015)
    for sx in (-1, 1):
        c.ellipse(hx + sx * 0.1, hy + 0.1, 0.03, 0.03, fill=hexc("#1a1418"), outline=OUTLINE, width=0.012)
        c.ellipse(hx + sx * 0.1 - 0.01, hy + 0.11, 0.01, 0.01, fill=hexc("#f0e0c0"))
    c.rect(cx - 0.12, y0 + 0.06 * K + 0.02, cx + 0.12, y0 + 0.14 * K + 0.02, fill=BRASS, outline=OUTLINE, width=0.01)   # Messingschild
    cobweb(c, cx + 0.7, by + 1.75, 0.14, -1, -1, seed=idx)
    dust(c, cx - 0.4, by + 1.2, cx + 0.4, by + 1.5, 5, seed=idx)


def _schreibtisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Schreibtisch: Nussholz mit Schubladen, gruenes Leder, Schreibmaschine, Bankerlampe, Papiere,
    Tintenfass, Brieföffner (Requisite) und ein Glas mit rotem Rest."""
    w = x1 - x0
    p.box(x0, y0, x1, y1, 0, 0.78, WALNUT_L, WALNUT)
    for k in range(2):
        for sx in (x0 + 0.1, x1 - 0.55):
            c.rect(sx, y0 + (0.12 + k * 0.3) * K, sx + 0.45, y0 + (0.36 + k * 0.3) * K, outline=WALNUT_D, width=0.012)
            c.ellipse(sx + 0.225, y0 + (0.24 + k * 0.3) * K, 0.02, 0.014, fill=BRASS, outline=OUTLINE, width=0.01)
    c.rect(x0 + 0.6, y0 + 0.06 * K, x1 - 0.6, y0 + 0.62 * K, fill=alpha((0, 0, 0, 255), 110))         # Beinraum
    zt = y0 + 0.78 * K
    c.rect(x0 + 0.06, zt + 0.05, x1 - 0.06, y1 + 0.78 * K - 0.05, fill=LEATHER, outline=WALNUT_D, width=0.012)
    c.rect(x0 + 0.1, zt + 0.08, x1 - 0.1, y1 + 0.78 * K - 0.08, outline=alpha(BRASS, 140), width=0.006)
    banker_lamp(c, x1 - 0.35, zt + 0.3, 1.0)
    # Schreibmaschine
    tx, ty = x0 + w * 0.4, zt + 0.12
    c.rect(tx - 0.25, ty, tx + 0.25, ty + 0.14, fill=MATTE, outline=OUTLINE, width=0.02)
    for row in range(3):
        for k in range(8):
            c.ellipse(tx - 0.2 + k * 0.055 + row * 0.012, ty + 0.03 + row * 0.035, 0.014, 0.012, fill=hexc("#d8d0c0"), outline=OUTLINE, width=0.006)
    c.rect(tx - 0.22, ty + 0.14, tx + 0.22, ty + 0.3, fill=MATTE_L, outline=OUTLINE, width=0.02)
    c.rect(tx - 0.28, ty + 0.28, tx + 0.28, ty + 0.34, fill=MATTE_D, outline=OUTLINE, width=0.015)
    c.poly([(tx - 0.12, ty + 0.34), (tx + 0.12, ty + 0.34), (tx + 0.1, ty + 0.5), (tx - 0.14, ty + 0.5)], fill=CREAM, outline=OUTLINE, width=0.012)
    for k in range(3):
        c.line([(tx - 0.1, ty + 0.38 + k * 0.035), (tx + 0.06, ty + 0.38 + k * 0.035)], fill=alpha(OUTLINE, 110), width=0.005)
    # Papiere, Tintenfass, Brieföffner, Glas
    for k in range(3):
        px_, py_ = x0 + 0.35 + k * 0.08, zt + 0.35 - k * 0.04
        c.poly([(px_ - 0.12, py_), (px_ + 0.12, py_ + 0.02), (px_ + 0.1, py_ + 0.18), (px_ - 0.14, py_ + 0.16)], fill=CREAM if k % 2 else PARCH, outline=OUTLINE, width=0.01)
    c.ellipse(x0 + 0.4, zt + 0.42, 0.03, 0.02, fill=alpha(BLOOD, 140))
    ix = x1 - 0.8
    c.rect(ix - 0.04, zt + 0.1, ix + 0.04, zt + 0.17, fill=hexc("#2a2e44"), outline=OUTLINE, width=0.012)
    c.line([(ix + 0.02, zt + 0.17), (ix + 0.12, zt + 0.36)], fill=CREAM, width=0.016)
    knife(c, x1 - 1.1, zt + 0.5, 0.3, 0.7, blade=BRASS_L)
    gx = x1 - 0.65
    c.rect(gx - 0.035, zt + 0.1, gx + 0.035, zt + 0.22, fill=alpha(GLASS, 180), outline=OUTLINE, width=0.012)
    c.rect(gx - 0.03, zt + 0.1, gx + 0.03, zt + 0.14, fill=alpha(BLOOD_L, 200))
    c.ellipse(gx, zt + 0.22, 0.035, 0.014, fill=alpha(GLASS, 200), outline=OUTLINE, width=0.01)
    dust(c, x0 + 0.1, zt + 0.06, x1 - 0.1, y1 + 0.78 * K - 0.06, 6, seed=idx)


def _catering(p, c, x0, y0, x1, y1, idx, rnd):
    """Catering-Tisch: Klapptisch mit weisser Decke, Kaffeekanne aus Stahl mit Dampf, Becherstapel,
    Tablett mit Broten, Thermoskanne, Obstschale, Klemmbrett."""
    w = x1 - x0
    for lx in (x0 + 0.1, x1 - 0.14):
        c.line([(lx, y0 + 0.05), (lx + 0.02, y0 + 0.05 + 0.75 * K)], fill=OUTLINE, width=0.04)
        c.line([(lx, y0 + 0.05), (lx + 0.02, y0 + 0.05 + 0.75 * K)], fill=STEEL, width=0.022)
    p.box(x0, y0, x1, y1, 0.72, 0.06, CREAM, CREAM_D, w=0.025)
    c.rect(x0 - 0.02, y0 + 0.2 * K, x1 + 0.02, y0 + 0.78 * K, fill=CREAM_D, outline=OUTLINE, width=0.025)   # haengende Decke vorn
    for k in range(5):
        c.line([(x0 + 0.1 + k * (w - 0.2) / 4, y0 + 0.22 * K), (x0 + 0.12 + k * (w - 0.2) / 4, y0 + 0.76 * K)], fill=alpha(shade(CREAM_D, 0.8), 110), width=0.01)
    c.ellipse(x0 + 0.6, y0 + 0.5 * K, 0.06, 0.04, fill=alpha(hexc("#6a4a2a"), 120))                 # Kaffeefleck
    zt = y0 + 0.78 * K
    ux = x0 + 0.35
    p.cyl(ux, y0 + 0.25, 0.14, 0.78, 0.45, hexc("#c8ccd4"), STEEL, ry=0.07)
    c.ellipse(ux, y0 + 0.25 + 1.23 * K, 0.08, 0.04, fill=MATTE_D, outline=OUTLINE, width=0.012)
    c.rect(ux + 0.1, y0 + 0.25 + 0.9 * K, ux + 0.17, y0 + 0.25 + 1.0 * K, fill=MATTE_D, outline=OUTLINE, width=0.01)   # Hahn
    c.line([(ux - 0.1, y0 + 0.25 + 0.85 * K), (ux - 0.1, y0 + 0.25 + 1.15 * K)], fill=alpha((255, 255, 255, 255), 90), width=0.012)
    for k in range(3):
        c.ellipse(ux + 0.05 + k * 0.06, y0 + 0.25 + 1.3 * K + 0.1 + k * 0.08, 0.04 + k * 0.015, 0.03 + k * 0.012, fill=alpha((210, 210, 220, 255), 80 - k * 20))
    for k in range(4):                                                                            # Becherstapel
        bx = x0 + 0.7 + (k % 2) * 0.13
        bz = zt + 0.1 + (k // 2) * 0.09
        c.poly([(bx - 0.05, bz), (bx + 0.05, bz), (bx + 0.06, bz + 0.1), (bx - 0.06, bz + 0.1)], fill=CREAM, outline=OUTLINE, width=0.012)
    tx = x0 + w * 0.6
    c.rect(tx - 0.3, zt + 0.08, tx + 0.3, zt + 0.3, fill=STEEL, outline=OUTLINE, width=0.015)        # Tablett
    for k in range(4):
        c.ellipse(tx - 0.2 + k * 0.13, zt + 0.19, 0.055, 0.04, fill=hexc("#c8a060"), outline=OUTLINE, width=0.01)
        c.ellipse(tx - 0.2 + k * 0.13, zt + 0.2, 0.04, 0.02, fill=hexc("#7a9a5a"))
    bottle(c, x1 - 0.45, zt + 0.12, 0.3, hexc("#3a5a4a"), r=0.045)
    c.ellipse(x1 - 0.2, zt + 0.18, 0.1, 0.05, fill=hexc("#8a9aa8"), outline=OUTLINE, width=0.012)
    for k in range(3):
        c.ellipse(x1 - 0.24 + k * 0.045, zt + 0.22, 0.035, 0.03, fill=hexc("#9a4a3a") if k % 2 else hexc("#8a9a4a"), outline=OUTLINE, width=0.01)
    c.poly([(x0 + 1.1, zt + 0.4), (x0 + 1.32, zt + 0.42), (x0 + 1.3, zt + 0.66), (x0 + 1.08, zt + 0.64)], fill=WALNUT_D, outline=OUTLINE, width=0.012)
    c.poly([(x0 + 1.12, zt + 0.42), (x0 + 1.3, zt + 0.44), (x0 + 1.28, zt + 0.62), (x0 + 1.1, zt + 0.6)], fill=CREAM, outline=OUTLINE, width=0.008)
    c.rect(x0 + 1.15, zt + 0.63, x0 + 1.25, zt + 0.67, fill=STEEL, outline=OUTLINE, width=0.008)
    gaffer(c, x0 + 0.1, y0 + 0.4 * K, x0 + 0.5, y0 + 0.4 * K, 0.04)
    c.text(x0 + 0.3, y0 + 0.4 * K, "CREW", 0.035, OUTLINE)


def _urne(p, c, x0, y0, x1, y1, idx, rnd):
    """Steinurne auf Sockel mit Henkeln, Moos, vertrocknetem Efeu, Riss."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    p.box(cx - r * 0.7, cy - r * 0.45, cx + r * 0.7, cy + r * 0.45, 0, 0.5, STONE_L, STONE)
    c.rect(cx - r * 0.6, cy - r * 0.45 + 0.1 * K, cx + r * 0.6, cy - r * 0.45 + 0.42 * K, outline=STONE_D, width=0.012)
    zb = cy + 0.5 * K
    c.ellipse(cx, zb, r * 0.3, r * 0.14, fill=STONE_L, outline=OUTLINE, width=0.02)
    c.poly([(cx - r * 0.28, zb), (cx + r * 0.28, zb), (cx + r * 0.75, zb + 0.35), (cx + r * 0.8, zb + 0.6), (cx + r * 0.55, zb + 0.7),
            (cx - r * 0.55, zb + 0.7), (cx - r * 0.8, zb + 0.6), (cx - r * 0.75, zb + 0.35)], fill=STONE, outline=OUTLINE, width=A.OUT_W)
    c.line([(cx - r * 0.55, zb + 0.1), (cx - r * 0.65, zb + 0.5)], fill=STONE_L, width=0.025)
    c.ellipse(cx, zb + 0.7, r * 0.6, r * 0.25, fill=STONE_L, outline=OUTLINE, width=0.025)
    c.ellipse(cx, zb + 0.7, r * 0.45, r * 0.18, fill=hexc("#2a2a26"))
    for sx in (-1, 1):
        c.ellipse(cx + sx * r * 0.82, zb + 0.5, 0.06, 0.07, outline=OUTLINE, width=0.05)
        c.ellipse(cx + sx * r * 0.82, zb + 0.5, 0.06, 0.07, outline=STONE_L, width=0.025)
    crack(c, [(cx + r * 0.3, zb + 0.65), (cx + r * 0.2, zb + 0.4), (cx + r * 0.35, zb + 0.15)], seed=idx)
    moss(c, cx - r * 0.4, zb + 0.3, 0.1, seed=idx)
    for k in range(3):                                                                            # vertrockneter Efeu haengt
        vine = HD.wobble([(cx + r * (0.3 - k * 0.3), zb + 0.72), (cx + r * (0.5 - k * 0.4), zb + 0.4 - k * 0.1), (cx + r * (0.6 - k * 0.5), zb + 0.05 - k * 0.1)], amp=0.015, seed=idx + k, step=0.05)
        c.line(vine, fill=hexc("#6a5a3a"), width=0.012)
        for lx, ly in vine[::3]:
            c.poly([(lx, ly), (lx + 0.03, ly - 0.02), (lx + 0.015, ly - 0.05), (lx - 0.015, ly - 0.05), (lx - 0.03, ly - 0.02)], fill=hexc("#8a7a4a"), outline=OUTLINE, width=0.006)


def _gartenbank(p, c, x0, y0, x1, y1, idx, rnd):
    """Gartenbank laengs der Ostwand (lang in y), Blick nach Westen: Holzlatten auf Gusseisenfuessen,
    Rueckenlehne an der Ostseite, Laub auf der Sitzflaeche."""
    wood = lift("#5a4a34", 1.5)
    for fy in (y0 + 0.15, y1 - 0.15):
        c.line([(x0 + 0.1, fy), (x1 - 0.2, fy)], fill=OUTLINE, width=0.05)
        c.line([(x0 + 0.1, fy), (x1 - 0.2, fy)], fill=IRON, width=0.03)
        c.line([(x0 + 0.15, fy), (x0 + 0.15, fy + 0.45 * K)], fill=OUTLINE, width=0.05)
        c.line([(x0 + 0.15, fy), (x0 + 0.15, fy + 0.45 * K)], fill=IRON, width=0.03)
    p.box(x0 + 0.05, y0, x1 - 0.25, y1, 0.45, 0.05, shade(wood, 1.15), wood, w=0.025)
    zt = y0 + 0.5 * K
    for k in range(4):                                                                            # Latten
        lx = x0 + 0.1 + k * (x1 - x0 - 0.4) / 4
        c.line([(lx, zt + 0.03), (lx, y1 + 0.5 * K - 0.03)], fill=shade(wood, 0.7), width=0.012)
    p.box(x1 - 0.25, y0 + 0.02, x1 - 0.1, y1 - 0.02, 0.5, 0.5, shade(wood, 1.15), shade(wood, 0.9), w=0.025)
    for k in range(3):
        c.line([(x1 - 0.22, y0 + 0.02 + (0.6 + k * 0.12) * K), (x1 - 0.13, y0 + 0.02 + (0.6 + k * 0.12) * K)], fill=shade(wood, 0.7), width=0.01)
    for k in range(4):                                                                            # Laub
        lx, ly = rnd.uniform(x0 + 0.15, x1 - 0.35), rnd.uniform(zt + 0.1, y1 + 0.5 * K - 0.1)
        c.poly([(lx - 0.04, ly), (lx, ly + 0.025), (lx + 0.04, ly), (lx, ly - 0.025)], fill=hexc("#a8663a") if k % 2 else hexc("#8a4a30"), outline=OUTLINE, width=0.006)
    c.rect(x0 + 0.05, y0 + 0.02, x1 - 0.25, y0 + 0.45 * K, fill=alpha((0, 0, 0, 255), 60))


def _pflanztisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Pflanztisch im Gewaechshaus: Holztisch, Tontoepfe mit verdorrten oder wuchernden Pflanzen,
    Giesskanne, Erde, Samentueten, Toepfe darunter."""
    w = x1 - x0
    wood = lift("#6a5038", 1.4)
    p.box(x0, y0, x1, y1, 0, 0.85, shade(wood, 1.15), wood)
    c.rect(x0 + 0.1, y0 + 0.1 * K, x1 - 0.1, y0 + 0.7 * K, fill=alpha((0, 0, 0, 255), 120))
    for k in range(int(w / 0.5)):                                                                 # Toepfe unter dem Tisch
        tx = x0 + 0.3 + k * 0.5
        c.poly([(tx - 0.08, y0 + 0.08), (tx + 0.08, y0 + 0.08), (tx + 0.1, y0 + 0.2), (tx - 0.1, y0 + 0.2)], fill=hexc("#a05c40"), outline=OUTLINE, width=0.012)
    for g in range(3):
        yy = y0 + 0.85 * K + 0.08 + g * 0.12
        c.line([(x0 + 0.05, yy), (x1 - 0.05, yy)], fill=shade(wood, 0.72), width=0.01)
    zt = y0 + 0.85 * K
    n = max(3, int(w / 0.55))
    for k in range(n):
        tx = x0 + 0.3 + k * (w - 0.6) / max(1, n - 1)
        ty = zt + 0.12 + (k % 2) * 0.12
        pot = hexc("#a05c40") if k % 3 else hexc("#7a8a84")
        c.poly([(tx - 0.1, ty), (tx + 0.1, ty), (tx + 0.12, ty + 0.2), (tx - 0.12, ty + 0.2)], fill=pot, outline=OUTLINE, width=0.015)
        c.rect(tx - 0.13, ty + 0.18, tx + 0.13, ty + 0.23, fill=shade(pot, 1.15), outline=OUTLINE, width=0.012)
        c.ellipse(tx, ty + 0.23, 0.11, 0.03, fill=hexc("#3a2e24"))
        kind_ = (k + idx) % 3
        if kind_ == 0:                                                                            # verdorrt
            for j in range(4):
                a = math.pi * 0.35 + j * 0.2
                c.line([(tx, ty + 0.24), (tx + 0.18 * math.cos(a), ty + 0.24 + 0.2 * math.sin(a))], fill=hexc("#7a6a4a"), width=0.012)
        elif kind_ == 1:                                                                          # wuchernd, haengt ueber
            for j in range(5):
                a = math.pi * 0.1 + j * 0.2
                pts = HD.wobble([(tx, ty + 0.24), (tx + 0.25 * math.cos(a), ty + 0.1 + 0.25 * math.sin(a)), (tx + 0.4 * math.cos(a), ty - 0.1 + 0.2 * math.sin(a))], amp=0.01, seed=idx + j, step=0.05)
                c.line(pts, fill=hexc("#4a6a3a"), width=0.014)
                for lx, ly in pts[1::2]:
                    c.ellipse(lx, ly, 0.03, 0.02, fill=hexc("#5a7a46"), outline=OUTLINE, width=0.006)
        else:                                                                                     # Blattpflanze, bleich
            for j in range(5):
                a = math.pi * 0.2 + j * 0.15
                c.poly([(tx, ty + 0.24), (tx + 0.2 * math.cos(a) - 0.03, ty + 0.24 + 0.2 * math.sin(a)), (tx + 0.25 * math.cos(a), ty + 0.26 + 0.26 * math.sin(a)),
                        (tx + 0.2 * math.cos(a) + 0.03, ty + 0.24 + 0.2 * math.sin(a))], fill=hexc("#7a9a7a"), outline=OUTLINE, width=0.01)
    gx = x1 - 0.5
    c.poly([(gx - 0.1, zt + 0.05), (gx + 0.1, zt + 0.05), (gx + 0.12, zt + 0.3), (gx - 0.12, zt + 0.3)], fill=hexc("#6a7a78"), outline=OUTLINE, width=0.015)   # Giesskanne
    c.line([(gx + 0.1, zt + 0.22), (gx + 0.28, zt + 0.36)], fill=OUTLINE, width=0.04)
    c.line([(gx + 0.1, zt + 0.22), (gx + 0.28, zt + 0.36)], fill=hexc("#6a7a78"), width=0.022)
    c.ellipse(gx, zt + 0.33, 0.07, 0.04, outline=OUTLINE, width=0.03)
    c.ellipse(gx, zt + 0.33, 0.07, 0.04, outline=hexc("#6a7a78"), width=0.015)
    c.poly(HD.wobble_ellipse(x0 + 0.8, zt + 0.08, 0.2, 0.05, amp=0.01, seed=idx), fill=hexc("#3a2e24"))        # Erde verschuettet
    for k in range(2):
        c.rect(x0 + 1.1 + k * 0.12, zt + 0.1, x0 + 1.19 + k * 0.12, zt + 0.22, fill=PARCH, outline=OUTLINE, width=0.01)
        c.ellipse(x0 + 1.145 + k * 0.12, zt + 0.16, 0.02, 0.02, fill=hexc("#8a4a4a") if k else hexc("#6a8a4a"))
    cobweb(c, x0, y1 + 0.85 * K, 0.18, 1, -1, seed=idx)


def _brunnen(p, c, x0, y0, x1, y1, idx, rnd):
    """Brunnen: Steinbecken mit dunklem Wasser und Mondreflex, Mittelsaeule mit verhuellter Figur ohne
    Gesicht, Moos, Risse, Laub auf dem Wasser."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    p.cyl(cx, cy, r, 0, 0.5, STONE_L, STONE, ry=r * 0.5)
    for k in range(10):
        a = math.pi + k * math.pi / 9
        c.line([(cx + r * math.cos(a), cy + r * 0.5 * math.sin(a) + 0.02), (cx + r * math.cos(a), cy + r * 0.5 * math.sin(a) + 0.5 * K - 0.02)], fill=alpha(STONE_D, 150), width=0.012)
    top = cy + 0.5 * K
    c.ellipse(cx, top, r - 0.18, (r - 0.18) * 0.5, fill=hexc("#243038"), outline=STONE_D, width=0.02)
    c.ellipse(cx - r * 0.3, top + 0.08, r * 0.3, r * 0.08, fill=alpha(MOON, 70))
    c.ellipse(cx - r * 0.28, top + 0.09, r * 0.14, r * 0.035, fill=alpha(MOON, 110))
    for k in range(5):                                                                            # Laub auf dem Wasser
        lx, ly = cx + rnd.uniform(-r * 0.6, r * 0.6), top + rnd.uniform(-r * 0.3, r * 0.3)
        c.poly([(lx - 0.04, ly), (lx, ly + 0.02), (lx + 0.04, ly), (lx, ly - 0.02)], fill=hexc("#8a5a34"), outline=OUTLINE, width=0.006)
    crack(c, [(cx + r * 0.5, cy + 0.03), (cx + r * 0.45, cy + 0.25 * K), (cx + r * 0.55, cy + 0.48 * K)], seed=idx)
    moss(c, cx - r * 0.6, cy + 0.1, 0.12, seed=idx)
    moss(c, cx + r * 0.2, top - 0.02, 0.1, seed=idx + 1)
    # Mittelsaeule und Figur
    p.cyl(cx, cy + 0.1, 0.22, 0.5, 0.5, STONE_L, STONE, ry=0.11)
    fz = cy + 0.1 + 1.0 * K
    c.poly([(cx - 0.22, fz), (cx + 0.22, fz), (cx + 0.16, fz + 0.7), (cx - 0.16, fz + 0.7)], fill=STONE, outline=OUTLINE, width=A.OUT_W)    # Gewand
    for k in range(3):
        c.line([(cx - 0.12 + k * 0.1, fz + 0.05), (cx - 0.08 + k * 0.08, fz + 0.6)], fill=STONE_D, width=0.012)
    c.poly([(cx - 0.16, fz + 0.5), (cx - 0.34, fz + 0.3), (cx - 0.3, fz + 0.22), (cx - 0.14, fz + 0.38)], fill=STONE_L, outline=OUTLINE, width=0.03)   # Arm haelt Schale
    c.ellipse(cx - 0.34, fz + 0.26, 0.09, 0.04, fill=STONE_L, outline=OUTLINE, width=0.02)
    c.ellipse(cx, fz + 0.76, 0.12, 0.11, fill=STONE_L, outline=OUTLINE, width=A.OUT_W)                  # Kapuze
    c.ellipse(cx, fz + 0.73, 0.07, 0.06, fill=shade(STONE, 0.5))
    c.ellipse(cx + 0.1, fz + 0.4, 0.06, 0.03, fill=alpha(MOSS, 150))
    cobweb(c, cx + 0.16, fz + 0.7, 0.12, 1, -1, seed=idx)
    c.ellipse(cx + r * 0.9, cy - r * 0.3, 0.12, 0.05, fill=alpha(hexc("#243038"), 150))               # Pfuetze


def _barrikade(p, c, x0, y0, x1, y1, idx, rnd):
    """Verrammelte Tuer: Bretter kreuzweise vor der Oeffnung (Wandhoehe), Naegel, Absperrband."""
    w, d = x1 - x0, y1 - y0
    H = 2.0
    plank = lift("#6a4e34", 1.35)
    wall = hexc("#3a2c34")
    p.box(x0, y0, x1, y1, 0, H, shade(wall, 1.15), wall)
    if w >= d:                                                                                    # waagerechte Wand: Bretter auf der Front
        fx0, fy0, fx1, fy1 = x0, y0, x1, y0 + H * K
        boards = [((fx0 + 0.05, fy0 + 0.1), (fx1 - 0.05, fy0 + 0.35)), ((fx0 + 0.05, fy1 - 0.15), (fx1 - 0.05, fy1 - 0.4)),
                  ((fx0 + 0.1, fy0 + 0.05), (fx1 - 0.1, fy1 - 0.05)), ((fx0 + 0.1, fy1 - 0.05), (fx1 - 0.1, fy0 + 0.05))]
    else:                                                                                         # senkrechte Wand: Bretter auf der Deckflaeche
        fx0, fy0, fx1, fy1 = x0, y0 + H * K, x1, y1 + H * K
        boards = [((fx0 - 0.02, fy0 + 0.1), (fx1 + 0.02, fy0 + 0.25)), ((fx0 - 0.02, fy1 - 0.25), (fx1 + 0.02, fy1 - 0.1)),
                  ((fx0 - 0.05, fy0 + 0.05), (fx1 + 0.05, fy1 - 0.05)), ((fx0 - 0.05, fy1 - 0.05), (fx1 + 0.05, fy0 + 0.05))]
    for k, (a, b) in enumerate(boards):
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        nx, ny = -math.sin(ang) * 0.06, math.cos(ang) * 0.06
        pts = [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]
        pts = HD.wobble(pts, amp=0.006, seed=idx + k, step=0.06, closed=True)
        col = shade(plank, 1 + (k % 3 - 1) * 0.1)
        c.poly(pts, fill=col, outline=OUTLINE, width=0.025)
        c.line([(a[0] + nx * 0.5, a[1] + ny * 0.5), (b[0] + nx * 0.5, b[1] + ny * 0.5)], fill=shade(col, 1.25), width=0.01)
        c.line([(a[0] - nx * 0.4, a[1] - ny * 0.4), (b[0] - nx * 0.4, b[1] - ny * 0.4)], fill=shade(col, 0.75), width=0.01)
        for t in (0.08, 0.92):
            c.ellipse(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 0.012, 0.012, fill=IRON_L, outline=OUTLINE, width=0.006)
    if w >= d:
        c.line([(fx0 - 0.1, fy0 + 0.55), (fx1 + 0.1, fy0 + 0.7)], fill=GAFFER, width=0.05)
        c.line([(fx0 - 0.1, fy0 + 0.55), (fx1 + 0.1, fy0 + 0.7)], fill=alpha(MATTE_D, 200), width=0.012)
    cobweb(c, fx1, fy1, 0.14, -1, -1, seed=idx)


_KIND_FN = {"standuhr": _standuhr, "seance_tisch": _seance_tisch, "buecherregal": _buecherregal, "kamin": _kamin,
            "kandelaber": _kandelaber, "kandelaber_aus": lambda *a: _kandelaber(*a, lit=False), "filmkamera": _filmkamera,
            "scheinwerfer": _scheinwerfer, "schminktisch": _schminktisch, "sessel": _sessel, "sarg": _sarg,
            "grabstein": _grabstein, "aggregat": _aggregat, "absperrung": _absperrung,
            "freitreppe": _freitreppe, "herd": _herd, "funktisch": _funktisch, "kisten": _kisten, "kessel": _kessel,
            "altar": _altar, "monitorwand": _monitorwand, "gewehrschrank": _gewehrschrank, "zelt": _zelt, "hecke": _hecke,
            "kuechentisch": _kuechentisch, "waschzuber": _waschzuber, "requisiten": _requisiten, "teleskop": _teleskop,
            "kohlen": _kohlen, "lesetisch": _lesetisch, "kirchenbank": _kirchenbank, "baer": _baer,
            "schreibtisch": _schreibtisch, "catering": _catering, "urne": _urne, "gartenbank": _gartenbank,
            "pflanztisch": _pflanztisch, "brunnen": _brunnen, "barrikade": _barrikade}


def draw(kind, shape, idx, ppm):
    """Ein Objekt als Sprite: (RGBA-Bild, welt_x_links, welt_y_unten, standlinie_y). Vertrag wie park_art.draw."""
    x0, y0, x1, y1 = A.shape_bounds(shape)
    h = PROP_H[kind]
    p = Prop(x0, y0, x1, y1, h, ppm, pad=PROP_PAD.get(kind, 0.3))
    c = p.c
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rnd = random.Random(idx * 131 + 7)
    if shape[0] in ("circle", "ellipse"):
        rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
        c.soft_shadow([(cx + 0.08 + rx * math.cos(t * math.pi / 12), cy - 0.08 + ry * math.sin(t * math.pi / 12)) for t in range(24)], 100, 0.1)
    elif kind not in ("absperrung", "hecke", "kohlen"):
        c.soft_shadow([(x0 + 0.08, y0 - 0.1), (x1 + 0.12, y0 - 0.1), (x1 + 0.12, y1), (x0 + 0.08, y1)], 95, 0.09)
    _KIND_FN[kind](p, c, x0, y0, x1, y1, idx, rnd)
    return c.finish(), c.x0, c.y0, p.base_y
