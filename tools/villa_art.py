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

from PIL import Image, ImageDraw, ImageFilter   # noqa: E402

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

PROP_H = {"standuhr": 2.3, "seance_tisch": 0.8, "buecherregal": 2.6, "kamin": 1.7, "kamin_gross": 2.5, "kandelaber": 1.6,
          "kandelaber_aus": 1.6, "filmkamera": 1.7, "scheinwerfer": 2.0, "schminktisch": 1.9, "sessel": 1.1,
          "sarg": 0.6, "grabstein": 1.0, "aggregat": 2.0, "absperrung": 1.0,
          # seit dem Stilblatt: alle Objektarten aus villa_layout.OPAQUE/GLASS plus die Barrikade
          "freitreppe": 2.6, "herd": 2.0, "funktisch": 1.5, "kisten": 1.7, "kessel": 2.2, "altar": 3.4,
          "monitorwand": 2.1, "gewehrschrank": 2.2, "zelt": 2.6, "hecke": 1.3, "kuechentisch": 1.1,
          "waschzuber": 0.8, "requisiten": 1.7, "teleskop": 1.9, "kohlen": 1.1, "lesetisch": 1.3,
          "kirchenbank": 1.0, "baer": 2.5, "schreibtisch": 1.4, "catering": 1.5, "urne": 1.5,
          "gartenbank": 1.0, "pflanztisch": 1.6, "brunnen": 1.9, "barrikade": 2.0,
          # Moebelstapel am Fuss der Freitreppe (das Obergeschoss gibt es nicht)
          "treppensperre": 2.2}
KINDS = set(PROP_H)
NO_SHADOW = set()        # Arten ohne Bodenschatten (Wandbilder, Haengendes, Bodenkram; villa_art2 traegt ein)
# Leinwandrand je Objekt (Standard 0,3 m): Lichtkegel, Glutschein und Lichtlachen reichen ueber die Grundflaeche
PROP_PAD = {"scheinwerfer": 2.3, "kamin": 0.8, "kamin_gross": 1.0, "kandelaber": 1.3, "kandelaber_aus": 0.5, "aggregat": 0.6,
            "filmkamera": 0.6, "seance_tisch": 0.5, "standuhr": 0.35, "schminktisch": 0.4,
            "lesetisch": 0.7, "schreibtisch": 0.6, "altar": 0.6, "kessel": 0.5, "zelt": 0.6, "funktisch": 0.5,
            "monitorwand": 0.5, "herd": 0.5, "kuechentisch": 0.4, "brunnen": 0.7, "teleskop": 0.4, "catering": 0.4,
            "treppensperre": 0.4}


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

def _standuhr(p, c, x0, y0, x1, y1, idx, rnd, variant=None):
    # variant "p1"/"p2": Pendel nach links/rechts, Zeiger auf Mitternacht (Mitternachtsuhr-Mechanik)
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
    px = cx + {"p1": -0.06, "p2": 0.06}.get(variant, 0.0)
    c.line([(cx, fy + (gz1 - 0.05) * K), (px, fy + (gz0 + 0.2) * K)], fill=BRASS, width=0.015)
    c.ellipse(px, fy + (gz0 + 0.2) * K, 0.07, 0.06, fill=BRASS, outline=BRASS_D, width=0.015)
    c.ellipse(px - 0.02, fy + (gz0 + 0.24) * K, 0.02, 0.015, fill=BRASS_L)
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
    minute = 0 if variant else 50 + (idx * 7) % 10
    ah = math.pi / 2 - ((12 if variant else 11) + minute / 60) / 12 * math.tau
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


def _kamin(p, c, x0, y0, x1, y1, idx, rnd, hgt=1.5):
    w = x1 - x0
    cx = (x0 + x1) / 2
    s = hgt / 1.5                                                                      # kamin_gross: hoeher
    stone = MARBLE if idx % 2 == 0 else STONE_L
    floor_light(c, cx, y0 - 0.25 * s, 1.2 * s, 0.5 * s, EMBER, 0.35, seed=idx)        # Glutschein davor
    p.box(x0, y0, x1, y1, 0, hgt, shade(stone, 1.05), stone)
    for k in range(4):                                                                 # Marmoradern
        vx = rnd.uniform(x0 + 0.05, x1 - 0.05)
        c.line(HD.wobble([(vx, y0 + 0.05), (vx + rnd.uniform(-0.2, 0.2), y0 + (hgt - 0.05) * K)], amp=0.03, seed=idx * 5 + k, step=0.05),
               fill=alpha(shade(stone, 0.7), 120), width=0.01)
    # Feuerraum mit Rundbogen, innen russschwarz; Glutbett, Scheite, Flammen, Feuerboecke
    ox0, ox1 = x0 + w * 0.22, x1 - w * 0.22
    oy0, oy1 = y0 + 0.08 * K, y0 + 1.0 * s * K
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
    p.box(x0 - 0.05, y0 - 0.04, x1 + 0.05, y1, hgt, 0.12, shade(stone, 1.12), shade(stone, 0.9))
    sy = y0 + 0.2 + (hgt + 0.12) * K
    for k, sx in enumerate((x0 + 0.3, x1 - 0.3)):
        c.ellipse(sx, sy, 0.05, 0.025, fill=BRASS, outline=OUTLINE, width=0.012)
        c.line([(sx, sy), (sx, sy + 0.12)], fill=OUTLINE, width=0.035)
        c.line([(sx, sy), (sx, sy + 0.12)], fill=BRASS, width=0.02)
        candle(c, sx, sy + 0.12, 0.14 if k == 0 else 0.1, True, r=0.028, seed=idx * 3 + k)
    c.ellipse(cx, sy + 0.02, 0.08, 0.035, fill=BRASS_D, outline=OUTLINE, width=0.012)
    c.poly([(cx - 0.08, sy + 0.03), (cx + 0.08, sy + 0.03), (cx + 0.05, sy + 0.2), (cx + 0.04, sy + 0.26), (cx - 0.04, sy + 0.26), (cx - 0.05, sy + 0.2)],
           fill=BRASS, outline=OUTLINE, width=0.015)
    c.line([(cx - 0.03, sy + 0.06), (cx - 0.03, sy + 0.18)], fill=BRASS_L, width=0.01)
    cobweb(c, x1 + 0.05, y0 - 0.04 + hgt * K, 0.2, -1, -1, seed=idx + 2)


def _kamin_gross(p, c, x0, y0, x1, y1, idx, rnd):
    """Grosser Kamin im Seance Parlour (User 25.10., "ein fetter Kamin statt der Ouija-Wand"): wie _kamin, 2,2 m hoch."""
    _kamin(p, c, x0, y0, x1, y1, idx, rnd, hgt=2.2)


def _kandelaber(p, c, x0, y0, x1, y1, idx, rnd, lit=True, variant=None):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    if variant == "off":                                                                    # Tauschbild: erloschen
        lit = False
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


_SPOT_IMG = "villa_scheinwerfer.png"      # 25.10.: GPT, Lampe zeigt nach links; Linse bei (30 %, 17,5 %) des Bilds
_SPOT_LENS = (0.30, 0.175)


def _spot_image(c, fx, hy, cy, dir_, off):
    """Lampe und Stativ aus dem Bild: Linse genau auf den Kegelursprung (fx, hy), Fuesse knapp unter cy; dir_ > 0 spiegelt
    (Lampe nach rechts). off: Linse dunkel (Tauschbild "Licht aus")."""
    path = os.path.join(_IMG_DIR, _SPOT_IMG)
    if not os.path.exists(path):
        return False
    src = Image.open(path).convert("RGBA")
    if off:
        px = src.load()
        for yy in range(int(src.height * 0.35)):
            for xx in range(src.width):
                r, g, b, a = px[xx, yy]
                if a > 0 and r > 200 and g > 175 and b > 110:
                    px[xx, yy] = (72, 66, 58, a)
    lx = _SPOT_LENS[0]
    if dir_ > 0:
        src = src.transpose(Image.FLIP_LEFT_RIGHT)
        lx = 1 - lx
    h_m = (hy - (cy - 0.35)) / (1 - _SPOT_LENS[1])
    w_m = h_m * src.width / src.height
    left, top = fx - lx * w_m, hy + _SPOT_LENS[1] * h_m
    im = src.resize((max(1, round(w_m * c.s)), max(1, round(h_m * c.s))), Image.LANCZOS)
    x, y = c.p(left, top)
    layer = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    layer.paste(im, (int(round(x)), int(round(y))))
    c.img.alpha_composite(layer)
    return True


def _scheinwerfer(p, c, x0, y0, x1, y1, idx, rnd, variant=None):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    dir_ = -1 if idx % 2 == 0 else 1
    col = (WARM, MOON, MOON)[idx % 3]              # mehr kaltes Mondlicht als warmes Wolfram
    hx, hy = cx, cy + 1.75 * K
    fx = hx + dir_ * 0.17
    ex, ey = cx + dir_ * 1.9, cy - 0.35
    if variant != "off":                                                                   # Tauschbild "off": kein Licht
        floor_light(c, ex, ey, 1.0, 0.5, col, 0.5, seed=idx)                              # Lichtkegel auf dem Boden
        for s, a_ in ((1.0, 26), (0.7, 26), (0.4, 28)):
            c.poly([(fx, hy + 0.08), (ex + dir_ * 0.9 * s, ey + 0.35 * s), (ex + dir_ * 1.0 * s, ey), (ex + dir_ * 0.9 * s, ey - 0.35 * s),
                    (ex - dir_ * 0.2 * s, ey - 0.5 * s), (fx, hy - 0.08)], fill=alpha(col, a_))
    if _spot_image(c, fx, hy, cy, dir_, variant == "off"):                                 # GPT-Lampe (User 25.10.)
        if variant != "off":
            c.glow(fx, hy, 0.5, col, 0.8)
        return
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
    """Gusseiserner Kuechenherd, neu 24.10. (User: "zu viele Stile in einem, naeher am comichaften Among-Us-Stil"):
    ein Material, eine Schattenstufe, wenige klare Teile. Schwarzer Herdkasten mit zwei Ofentueren (Messinggriffe,
    eine mit Glut), Backofenfenster, vier Kochringe, ein grosser Topf mit Deckel und Dampf, Ofenrohr zur Kupferhaube."""
    w = x1 - x0
    cx = (x0 + x1) / 2
    body = IRON
    body_l = IRON_L
    body_d = IRON_D
    H = 0.95
    p.box(x0, y0, x1, y1, 0, H, body_l, body)
    fy = y0
    fh = H * K
    # Sockelleiste und Fussblech
    c.rect(x0 + 0.02, fy + 0.02, x1 - 0.02, fy + 0.07, fill=body_d)
    # zwei Ofentueren links und rechts, dazwischen ein schmales Backofenfenster
    for k, (dx0, dx1) in enumerate(((x0 + 0.12, cx - 0.42), (cx + 0.42, x1 - 0.12))):
        c.rect(dx0, fy + 0.12, dx1, fy + fh - 0.1, fill=body_d, outline=OUTLINE, width=0.025)
        c.rect(dx0 + 0.05, fy + 0.17, dx1 - 0.05, fy + fh - 0.15, outline=body_l, width=0.012)
        hy = fy + (fh - 0.1 + 0.12) / 2
        c.line([(dx0 + 0.15, hy), (dx1 - 0.15, hy)], fill=OUTLINE, width=0.045)
        c.line([(dx0 + 0.15, hy), (dx1 - 0.15, hy)], fill=BRASS, width=0.025)
        if k == 0:                                                                               # Glut hinter dem Rost
            c.glow((dx0 + dx1) / 2, fy + 0.22, 0.28, EMBER, 0.55)
            c.rect(dx0 + 0.12, fy + 0.19, dx1 - 0.12, fy + 0.26, fill=EMBER, outline=OUTLINE, width=0.012)
            for i in range(4):
                gx = dx0 + 0.16 + i * (dx1 - dx0 - 0.32) / 3
                c.line([(gx, fy + 0.19), (gx, fy + 0.26)], fill=OUTLINE, width=0.012)
    c.rect(cx - 0.3, fy + 0.16, cx + 0.3, fy + fh - 0.14, fill=body_d, outline=OUTLINE, width=0.025)        # Backofen
    c.rect(cx - 0.22, fy + 0.22, cx + 0.22, fy + fh - 0.22, fill=hexc("#2a1e18"), outline=OUTLINE, width=0.015)
    c.line([(cx - 0.18, fy + fh - 0.26), (cx - 0.08, fy + fh - 0.26)], fill=alpha((255, 255, 255, 255), 90), width=0.015)
    c.line([(cx - 0.2, fy + 0.11), (cx + 0.2, fy + 0.11)], fill=OUTLINE, width=0.04)                        # Griffstange
    c.line([(cx - 0.2, fy + 0.11), (cx + 0.2, fy + 0.11)], fill=BRASS, width=0.022)
    # Herdplatte mit vier Kochringen
    zt = y0 + H * K
    c.rect(x0 + 0.03, zt + 0.02, x1 - 0.03, y1 + H * K - 0.02, fill=shade(body, 0.9))
    for k in range(4):
        hx = x0 + 0.35 + k * (w - 0.7) / 3
        c.ellipse(hx, zt + 0.25, 0.16, 0.08, fill=body_d, outline=OUTLINE, width=0.02)
        c.ellipse(hx, zt + 0.25, 0.1, 0.05, outline=body_l, width=0.012)
        c.ellipse(hx, zt + 0.25, 0.04, 0.02, fill=body_l)
    # grosser Topf mit Deckel auf dem zweiten Ring, Dampf
    tx = x0 + 0.35 + (w - 0.7) / 3
    pot = hexc("#3a3e46")
    p.cyl(tx, y0 + 0.32, 0.2, H, 0.3, shade(pot, 1.2), pot, ry=0.1)
    c.ellipse(tx, y0 + 0.32 + (H + 0.3) * K, 0.22, 0.11, fill=shade(pot, 1.25), outline=OUTLINE, width=0.025)   # Deckel
    c.ellipse(tx, y0 + 0.32 + (H + 0.3) * K + 0.05, 0.04, 0.025, fill=BRASS, outline=OUTLINE, width=0.015)       # Knauf
    for sx in (-1, 1):                                                                               # Henkel
        c.line([(tx + sx * 0.2, y0 + 0.32 + (H + 0.15) * K), (tx + sx * 0.27, y0 + 0.32 + (H + 0.15) * K)], fill=OUTLINE, width=0.045)
        c.line([(tx + sx * 0.2, y0 + 0.32 + (H + 0.15) * K), (tx + sx * 0.27, y0 + 0.32 + (H + 0.15) * K)], fill=pot, width=0.022)
    for k in range(3):                                                                               # Dampf
        c.ellipse(tx + 0.06 + k * 0.05, y0 + 0.32 + (H + 0.3) * K + 0.12 + k * 0.1, 0.07 + k * 0.02, 0.05 + k * 0.015,
                  fill=alpha((225, 225, 235, 255), 90 - k * 22))
    # Ofenrohr und Kupferhaube an der Rueckwand (ein Ton, eine Schattenstufe)
    hy = y1 + 1.35 * K
    c.rect(cx - 0.1, zt + 0.25, cx + 0.1, hy, fill=body, outline=OUTLINE, width=0.025)
    c.line([(cx - 0.06, zt + 0.3), (cx - 0.06, hy - 0.05)], fill=body_l, width=0.015)
    c.poly([(x0 + 0.1, hy), (x1 - 0.1, hy), (x1 - 0.45, hy + 0.5), (x0 + 0.45, hy + 0.5)], fill=COPPER, outline=OUTLINE, width=0.03)
    c.poly([(x0 + 0.1, hy), (x1 - 0.1, hy), (x1 - 0.14, hy + 0.08), (x0 + 0.14, hy + 0.08)], fill=shade(COPPER, 0.72))
    c.line([(x0 + 0.5, hy + 0.44), (x1 - 0.5, hy + 0.44)], fill=shade(COPPER, 1.3), width=0.02)
    c.rect(cx - 0.14, hy + 0.5, cx + 0.14, hy + 0.72, fill=shade(COPPER, 0.85), outline=OUTLINE, width=0.025)
    # Geschirrtuch am Griff (ein Farbtupfer)
    c.poly([(x1 - 0.45, fy + 0.11), (x1 - 0.25, fy + 0.11), (x1 - 0.23, fy + 0.4), (x1 - 0.47, fy + 0.4)], fill=hexc("#8a9ab0"), outline=OUTLINE, width=0.015)
    c.line([(x1 - 0.36, fy + 0.14), (x1 - 0.35, fy + 0.37)], fill=shade(hexc("#8a9ab0"), 0.8), width=0.012)
    cobweb(c, x1 - 0.12, hy, 0.2, -1, 1, seed=idx)


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
    """Altar an der Nordwand (seit 24.10., breit in x, flach in y): Steintisch mit weissem Altartuch und Spitzensaum,
    zwei Messingleuchter mit Kerzen, aufgeschlagene Bibel, Kelch, vertrocknete Blumen, darueber an der Wand ein
    grosses dunkles Holzkreuz mit Messingenden (Teil des Sprites, PROP_H 3,4)."""
    cx = (x0 + x1) / 2
    H = 0.95
    p.box(x0, y0, x1, y1, 0, H, STONE_L, STONE)
    for k in range(3):                                                                               # Steinfugen
        c.line([(x0 + 0.1 + k * (x1 - x0 - 0.2) / 2, y0 + 0.08), (x0 + 0.1 + k * (x1 - x0 - 0.2) / 2, y0 + H * K - 0.08)], fill=alpha(STONE_D, 180), width=0.012)
    c.line([(x0 + 0.08, y0 + H * K * 0.45), (x1 - 0.08, y0 + H * K * 0.45)], fill=alpha(STONE_D, 180), width=0.012)
    c.rect(x0 + 0.1, y0 + H * K * 0.5, x1 - 0.1, y0 + H * K - 0.1, outline=alpha(STONE_D, 120), width=0.01)
    c.poly([(cx - 0.05, y0 + 0.1), (cx + 0.05, y0 + 0.1), (cx + 0.05, y0 + 0.36), (cx - 0.05, y0 + 0.36)], fill=STONE_D)   # Kreuz im Stein
    c.rect(cx - 0.14, y0 + 0.24, cx + 0.14, y0 + 0.3, fill=STONE_D)
    crack(c, [(x0 + 0.3, y0 + 0.03), (x0 + 0.36, y0 + 0.25), (x0 + 0.3, y0 + 0.45)], seed=idx)
    zt = y0 + H * K
    # Altartuch: haengt vorn ueber (Saum mit Spitzenkante), liegt auf der Platte
    hem = zt - 0.14
    c.rect(x0 + 0.04, hem, x1 - 0.04, zt + 0.02, fill=CREAM, outline=OUTLINE, width=0.015)
    for k in range(int((x1 - x0) / 0.12)):
        sx = x0 + 0.1 + k * 0.12
        c.ellipse(sx, hem, 0.04, 0.025, fill=CREAM, outline=OUTLINE, width=0.012)
        c.ellipse(sx, hem + 0.045, 0.012, 0.012, fill=alpha(STONE_D, 140))
    c.line([(x0 + 0.08, hem + 0.09), (x1 - 0.08, hem + 0.09)], fill=BRASS_D, width=0.01)
    c.rect(x0 + 0.04, zt, x1 - 0.04, y1 + H * K - 0.03, fill=CREAM, outline=OUTLINE, width=0.015)
    for k in range(4):
        c.line([(x0 + 0.3 + k * 0.5, zt + 0.03), (x0 + 0.33 + k * 0.5, y1 + H * K - 0.06)], fill=alpha(CREAM_D, 120), width=0.01)
    dust(c, x0 + 0.1, zt + 0.02, x1 - 0.1, y1 + H * K - 0.05, 8, seed=idx)
    ty = (zt + y1 + H * K) / 2
    # Leuchter mit Kerzen
    for k, lx in enumerate((x0 + 0.35, x1 - 0.35)):
        c.ellipse(lx, ty - 0.05, 0.07, 0.03, fill=BRASS, outline=OUTLINE, width=0.012)
        c.line([(lx, ty - 0.05), (lx, ty + 0.1)], fill=OUTLINE, width=0.04)
        c.line([(lx, ty - 0.05), (lx, ty + 0.1)], fill=BRASS, width=0.022)
        c.ellipse(lx, ty + 0.1, 0.045, 0.02, fill=BRASS, outline=OUTLINE, width=0.012)
        candle(c, lx, ty + 0.1, 0.2 if k == 0 else 0.15, True, r=0.03, seed=idx + k)
    # Bibel (aufgeschlagen, rotes Lesezeichen) und Kelch
    bx = cx - 0.3
    c.poly([(bx - 0.2, ty - 0.14), (bx + 0.2, ty - 0.14), (bx + 0.22, ty + 0.12), (bx - 0.22, ty + 0.12)], fill=WALNUT_D, outline=OUTLINE, width=0.015)
    c.poly([(bx - 0.18, ty - 0.11), (bx, ty - 0.1), (bx, ty + 0.1), (bx - 0.19, ty + 0.09)], fill=PARCH, outline=OUTLINE, width=0.01)
    c.poly([(bx, ty - 0.1), (bx + 0.18, ty - 0.11), (bx + 0.19, ty + 0.09), (bx, ty + 0.1)], fill=PARCH, outline=OUTLINE, width=0.01)
    for k in range(4):
        c.line([(bx - 0.15, ty - 0.05 + k * 0.04), (bx - 0.03, ty - 0.05 + k * 0.04)], fill=alpha(OUTLINE, 110), width=0.006)
        c.line([(bx + 0.03, ty - 0.05 + k * 0.04), (bx + 0.15, ty - 0.05 + k * 0.04)], fill=alpha(OUTLINE, 110), width=0.006)
    c.line([(bx + 0.06, ty - 0.1), (bx + 0.08, ty - 0.2)], fill=hexc("#a02a34"), width=0.02)
    kx = cx + 0.3
    c.ellipse(kx, ty - 0.08, 0.08, 0.035, fill=BRASS, outline=OUTLINE, width=0.012)
    c.line([(kx, ty - 0.08), (kx, ty + 0.06)], fill=BRASS_D, width=0.03)
    c.poly([(kx - 0.09, ty + 0.06), (kx + 0.09, ty + 0.06), (kx + 0.07, ty + 0.2), (kx - 0.07, ty + 0.2)], fill=BRASS, outline=OUTLINE, width=0.012)
    c.ellipse(kx, ty + 0.2, 0.07, 0.03, fill=BRASS_L, outline=OUTLINE, width=0.012)
    c.line([(kx - 0.05, ty + 0.08), (kx - 0.04, ty + 0.17)], fill=BRASS_L, width=0.012)
    vx, vy = cx, ty + 0.02                                                                           # vertrocknete Blumen in Vase
    c.poly([(vx - 0.04, vy - 0.06), (vx + 0.04, vy - 0.06), (vx + 0.03, vy + 0.08), (vx - 0.03, vy + 0.08)], fill=STONE_D, outline=OUTLINE, width=0.01)
    for k in range(5):
        a = math.pi * 0.3 + k * math.pi * 0.1
        c.line([(vx, vy + 0.06), (vx + 0.16 * math.cos(a), vy + 0.08 + 0.16 * math.sin(a))], fill=hexc("#6a5a3a"), width=0.01)
        c.ellipse(vx + 0.16 * math.cos(a), vy + 0.08 + 0.16 * math.sin(a), 0.02, 0.016, fill=hexc("#8a6a46"), outline=OUTLINE, width=0.006)
    # Wandkreuz ueber dem Altar (an der Nordwand, deshalb ueber der Platte gezeichnet)
    wall = y1 + H * K
    cz0, cz1 = wall + 0.25, wall + 1.3
    arm = wall + 0.95
    for col, wd in ((OUTLINE, 0.03), (None, 0)):
        pass
    c.rect(cx - 0.07, cz0, cx + 0.07, cz1, fill=WALNUT_D, outline=OUTLINE, width=0.03)
    c.rect(cx - 0.42, arm - 0.065, cx + 0.42, arm + 0.065, fill=WALNUT_D, outline=OUTLINE, width=0.03)
    c.line([(cx - 0.04, cz0 + 0.03), (cx - 0.04, cz1 - 0.03)], fill=WALNUT, width=0.02)
    c.line([(cx - 0.39, arm + 0.03), (cx + 0.39, arm + 0.03)], fill=WALNUT, width=0.02)
    for ex_, ey_, w_, h_ in ((cx, cz1, 0.1, 0.05), (cx - 0.42, arm, 0.05, 0.09), (cx + 0.42, arm, 0.05, 0.09), (cx, cz0, 0.1, 0.05)):
        c.rect(ex_ - w_, ey_ - h_, ex_ + w_, ey_ + h_, fill=BRASS, outline=OUTLINE, width=0.015)
    c.ellipse(cx, arm, 0.06, 0.06, fill=BRASS, outline=OUTLINE, width=0.015)
    c.glow(cx, arm, 0.9, WARM, 0.18)
    cobweb(c, cx + 0.42, arm + 0.065, 0.16, 1, 1, seed=idx)


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
    """Kuechentisch, neu 24.10. (User: "Dinge auf dem Tisch nicht im Among-Us-Stil"): schwerer Holztisch mit
    Zarge, darauf wenige grosse, klar lesbare Dinge im Comicstil: Brotlaib auf Brett mit Messer, Obstschale mit
    Aepfeln, Tonkrug, Kerzenhalter, Kochbuch. Kein Kunstblut."""
    w = x1 - x0
    cx = (x0 + x1) / 2
    p.box(x0, y0, x1, y1, 0, 0.8, WALNUT_L, WALNUT)
    for lx in (x0 + 0.06, x1 - 0.14):
        c.rect(lx, y0 + 0.05, lx + 0.08, y0 + 0.75 * K, fill=WALNUT_D, outline=OUTLINE, width=0.015)
    c.rect(x0 + 0.14, y0 + 0.1 * K, x1 - 0.14, y0 + 0.62 * K, fill=alpha((0, 0, 0, 255), 110))           # Schatten unter der Platte
    c.rect(x0, y0 + 0.62 * K, x1, y0 + 0.8 * K, fill=WALNUT, outline=OUTLINE, width=0.025)             # Zarge
    c.line([(x0 + 0.05, y0 + 0.78 * K), (x1 - 0.05, y0 + 0.78 * K)], fill=WALNUT_L, width=0.012)
    zt = y0 + 0.8 * K
    d = y1 - y0
    for k in range(3):                                                                            # Maserung der Platte
        yy = zt + 0.1 + k * (d - 0.2) / 2
        c.line(HD.wobble([(x0 + 0.1, yy), (x1 - 0.1, yy + 0.01)], amp=0.006, seed=idx + k, step=0.1), fill=alpha(WALNUT_D, 110), width=0.008)
    # Schneidbrett mit Brotlaib und Messer (links)
    bx, by = x0 + w * 0.3, zt + d * 0.45
    c.poly([(bx - 0.36, by - 0.16), (bx + 0.36, by - 0.16), (bx + 0.38, by + 0.14), (bx - 0.34, by + 0.14)], fill=hexc("#b08a5a"), outline=OUTLINE, width=0.02)
    c.ellipse(bx + 0.34, by - 0.01, 0.025, 0.025, fill=alpha(OUTLINE, 200))
    loaf = hexc("#c98a4a")
    c.ellipse(bx - 0.08, by + 0.02, 0.22, 0.12, fill=loaf, outline=OUTLINE, width=0.02)
    c.ellipse(bx - 0.08, by + 0.06, 0.16, 0.06, fill=shade(loaf, 1.2))
    for k in range(3):
        c.line([(bx - 0.2 + k * 0.1, by + 0.1), (bx - 0.12 + k * 0.1, by + 0.0)], fill=shade(loaf, 0.65), width=0.015)
    c.rect(bx + 0.22, by - 0.1, bx + 0.3, by + 0.04, fill=shade(loaf, 1.1), outline=OUTLINE, width=0.015)      # Scheibe
    kx, ky = bx + 0.02, by - 0.1
    c.poly([(kx, ky), (kx + 0.3, ky - 0.03), (kx + 0.32, ky + 0.01), (kx + 0.02, ky + 0.04)], fill=STEEL, outline=OUTLINE, width=0.015)   # Messer
    c.rect(kx - 0.12, ky - 0.015, kx, ky + 0.045, fill=WALNUT_D, outline=OUTLINE, width=0.015)
    # Obstschale mit Aepfeln (Mitte)
    ox, oy = cx + 0.05, zt + d * 0.72
    c.ellipse(ox, oy - 0.02, 0.22, 0.09, fill=hexc("#6a7a8a"), outline=OUTLINE, width=0.02)
    c.ellipse(ox, oy + 0.02, 0.17, 0.05, fill=hexc("#4a5a6a"))
    for k, (dx, dy, col) in enumerate(((-0.1, 0.03, "#c83a30"), (0.02, 0.06, "#c83a30"), (0.12, 0.02, "#8ab040"), (-0.03, -0.01, "#c83a30"))):
        ax, ay = ox + dx, oy + dy
        c.ellipse(ax, ay, 0.06, 0.055, fill=hexc(col), outline=OUTLINE, width=0.015)
        c.ellipse(ax - 0.02, ay + 0.02, 0.015, 0.012, fill=(255, 255, 255, 170))
        c.line([(ax, ay + 0.05), (ax + 0.01, ay + 0.08)], fill=WALNUT_D, width=0.012)
    # Tonkrug (rechts hinten) und Kerzenhalter (rechts vorn), Kochbuch
    jx, jy = x1 - 0.45, zt + d * 0.62
    jug = hexc("#8a6a4a")
    c.poly([(jx - 0.1, jy), (jx + 0.1, jy), (jx + 0.13, jy + 0.14), (jx + 0.09, jy + 0.3), (jx - 0.09, jy + 0.3), (jx - 0.13, jy + 0.14)], fill=jug, outline=OUTLINE, width=0.02)
    c.ellipse(jx, jy + 0.3, 0.09, 0.035, fill=shade(jug, 1.2), outline=OUTLINE, width=0.015)
    c.line([(jx + 0.12, jy + 0.26), (jx + 0.22, jy + 0.18), (jx + 0.12, jy + 0.08)], fill=OUTLINE, width=0.05)
    c.line([(jx + 0.12, jy + 0.26), (jx + 0.22, jy + 0.18), (jx + 0.12, jy + 0.08)], fill=jug, width=0.025)
    c.line([(jx - 0.07, jy + 0.06), (jx - 0.06, jy + 0.24)], fill=shade(jug, 1.3), width=0.015)
    hx, hy = x1 - 0.35, zt + d * 0.25
    c.ellipse(hx, hy, 0.07, 0.03, fill=BRASS, outline=OUTLINE, width=0.012)
    c.ellipse(hx, hy + 0.03, 0.03, 0.015, fill=BRASS_D)
    candle(c, hx, hy + 0.03, 0.14, True, r=0.025, seed=idx)
    cb = (x0 + w * 0.62, zt + d * 0.22)                                                               # Kochbuch
    c.poly([(cb[0] - 0.16, cb[1] - 0.09), (cb[0] + 0.16, cb[1] - 0.1), (cb[0] + 0.17, cb[1] + 0.1), (cb[0] - 0.15, cb[1] + 0.11)], fill=hexc("#4a6a3a"), outline=OUTLINE, width=0.015)
    c.line([(cb[0] - 0.13, cb[1] + 0.09), (cb[0] + 0.14, cb[1] + 0.08)], fill=CREAM, width=0.02)
    c.rect(cb[0] - 0.08, cb[1] - 0.04, cb[0] + 0.08, cb[1] + 0.03, fill=CREAM, outline=OUTLINE, width=0.008)
    c.rect(x1 - 0.95, zt + 0.06, x1 - 0.62, zt + 0.13, fill=hexc("#8a9ab0"), outline=OUTLINE, width=0.012)   # Geschirrtuch
    c.line([(x1 - 0.9, zt + 0.095), (x1 - 0.67, zt + 0.095)], fill=shade(hexc("#8a9ab0"), 0.8), width=0.008)


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
    """Kirchenbank mit Blick nach Norden zum Altar (User 24.10.): die hohe Rueckenlehne steht an der SUEDkante,
    man sieht ihre Rueckseite mit dem Gesangbuchbrett, dahinter den Sitz; Wangen mit Kugelknauf an beiden Enden."""
    seat_h, back_h = 0.45, 0.95
    # Wangen (Seitenteile) hinten sichtbar
    for wx in (x0, x1 - 0.1):
        p.box(wx, y0, wx + 0.1, y1, 0, back_h, WALNUT_L, WALNUT, w=0.025)
        c.ellipse(wx + 0.05, y0 + back_h * K + 0.03, 0.045, 0.035, fill=WALNUT_L, outline=OUTLINE, width=0.02)      # Knauf
    # Sitz (hinter der Lehne, Deckflaeche sichtbar)
    p.box(x0 + 0.1, y0 + 0.12, x1 - 0.1, y1 - 0.04, seat_h - 0.06, 0.06, WALNUT_L, WALNUT, w=0.025)
    zt = y0 + 0.12 + seat_h * K
    for k in range(3):                                                                            # Maserung Sitz
        c.line(HD.wobble([(x0 + 0.2, zt + 0.03 + k * 0.05), (x1 - 0.2, zt + 0.035 + k * 0.05)], amp=0.004, seed=idx + k, step=0.1), fill=alpha(WALNUT_D, 100), width=0.006)
    bx = x0 + (x1 - x0) * (0.3 if idx % 2 else 0.65)                                              # Gesangbuch auf dem Sitz
    c.rect(bx - 0.08, zt + 0.08, bx + 0.08, zt + 0.17, fill=lift("#2a2a3a", 1.5), outline=OUTLINE, width=0.012)
    c.line([(bx - 0.03, zt + 0.125), (bx + 0.03, zt + 0.125)], fill=BRASS, width=0.008)
    # Rueckenlehne an der Suedkante: Rueckseite mit Rahmen und Fuellungen, oben Gesangbuchbrett
    fb, ft = y0 + 0.02, y0 + back_h * K
    c.rect(x0 + 0.1, fb, x1 - 0.1, ft, fill=WALNUT, outline=OUTLINE, width=0.025)
    c.rect(x0 + 0.12, fb + 0.02, x1 - 0.12, fb + 0.06, fill=WALNUT_D)
    n = max(2, int((x1 - x0) / 0.6))
    for k in range(n):
        px0 = x0 + 0.16 + k * (x1 - x0 - 0.32) / n
        px1 = px0 + (x1 - x0 - 0.32) / n - 0.06
        c.rect(px0, fb + 0.1, px1, ft - 0.16, fill=shade(WALNUT, 0.9), outline=WALNUT_D, width=0.012)
        c.line([(px0 + 0.02, ft - 0.18), (px1 - 0.02, ft - 0.18)], fill=WALNUT_L, width=0.008)
    c.rect(x0 + 0.08, ft - 0.1, x1 - 0.08, ft - 0.03, fill=WALNUT_L, outline=OUTLINE, width=0.02)        # Buchbrett (Kante)
    c.rect(x0 + 0.1, ft - 0.03, x1 - 0.1, ft + 0.04, fill=WALNUT, outline=OUTLINE, width=0.02)          # Lehnenkrone
    c.line([(x0 + 0.14, ft + 0.02), (x1 - 0.14, ft + 0.02)], fill=alpha((255, 255, 255, 255), 50), width=0.01)
    hb = x0 + (x1 - x0) * (0.7 if idx % 2 else 0.3)                                               # Gesangbuch im Brett
    c.rect(hb - 0.07, ft - 0.1, hb + 0.07, ft - 0.03, fill=hexc("#5a2a3a"), outline=OUTLINE, width=0.01)
    cobweb(c, x1, y1 + back_h * K, 0.16, -1, -1, seed=idx)
    c.rect(x0 + 0.1, zt + 0.01, x1 - 0.1, zt + 0.02, fill=alpha((0, 0, 0, 255), 40))


def _baer(p, c, x0, y0, x1, y1, idx, rnd):
    """Praeparierter Braunbaer, von Grund auf neu nach dem Fotovorbild des Users (Nachtrag 3): ruhig aufrecht auf
    den Hinterbeinen, Vorderpranken locker vor der Brust haengend, Krallen hell und sichtbar, Kopf leicht erhoben und
    nach links in den Raum gedreht (der Baer steht an der Ostwand), Maul geschlossen, dunkle Nase, kleine Glasaugen
    mit Lichtpunkt, kleine runde Ohren, breiter Nacken mit Schulterbuckel. Warmes Braun, dunklere Arme und Beine,
    hellere Schnauze, wenige klare Fellgruppen, echte Baerenproportionen. Dunkler Sockel mit Messingschild "URSUS".
    Schraege Aufsicht, Standlinie und Fussflaeche unveraendert."""
    cx = (x0 + x1) / 2
    fur = hexc("#8a5a30")
    fur_l = hexc("#b07c48")
    fur_d = hexc("#5e3a1c")
    limb = hexc("#6a4322")
    muzzle = hexc("#caa272")
    claw = hexc("#ece4d0")
    dark = lift("#2a2420", 1.5)
    ow = A.OUT_W
    # Sockel mit Messingschild
    p.box(x0, y0, x1, y1, 0, 0.22, shade(dark, 1.3), dark)
    c.line([(x0 + 0.03, y0 + 0.19), (x1 - 0.03, y0 + 0.19)], fill=alpha((255, 255, 255, 255), 40), width=0.012)
    c.rect(cx - 0.19, y0 + 0.04, cx + 0.19, y0 + 0.1, fill=BRASS, outline=OUTLINE, width=0.01)
    c.text(cx, y0 + 0.07, "URSUS", 0.04, hexc("#2a2422"))
    fy = y0 + 0.22 * K + 0.36            # Fusslinie auf dem Sockel

    def P(x, y):
        return (cx + x, fy + y)

    def wob(pts, seed, amp=0.015):
        return HD.wobble([P(x, y) for x, y in pts], amp=amp, seed=idx * 7 + seed, step=0.05, closed=True)

    def shag(pts, fill, seed, amp=0.03, tooth=0.09):
        """Fellgruppe mit grober Zackenkante, ohne Kontur."""
        rs = random.Random(idx * 7 + seed)
        src = [P(x, y) for x, y in pts]
        out = []
        n = len(src)
        for i in range(n):
            a, b = src[i], src[(i + 1) % n]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            steps = max(1, int(L / tooth))
            for k in range(steps):
                t = k / steps
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
                d = (amp if k % 2 else 0) * rs.uniform(0.6, 1.1)
                out.append((x + nx * d, y + ny * d))
        c.poly(out, fill=fill)

    def limb_stroke(pts, w):
        """Gliedmasse als dicker Strich mit runden Gelenken: erst Kontur, dann Fuellung."""
        q = [P(x, y) for x, y in pts]
        for col, ww in ((OUTLINE, w + 2 * ow), (limb, w)):
            c.line(q, fill=col, width=ww)
            for x, y in q:
                c.ellipse(x, y, ww / 2, ww / 2, fill=col)

    def claws(x, y, n, spread, size, s=1):
        for k in range(n):
            kx = cx + x - spread * (n - 1) / 2 + k * spread
            c.poly([(kx - size * 0.45, fy + y), (kx + size * 0.45, fy + y), (kx + s * size * 0.1, fy + y - size * 1.6)],
                   fill=claw, outline=OUTLINE, width=0.011)

    # Hinterlaeufe: kurz und kraeftig, dunkler, breite Pranken mit hellen Krallen nach vorn
    for s in (-1, 1):
        lx = s * 0.27
        c.poly(wob([(lx - 0.2, 0.08), (lx - 0.24, 0.5), (lx - 0.1, 0.72), (lx + 0.16, 0.72), (lx + 0.24, 0.5), (lx + 0.2, 0.08)], 1 + s), fill=limb, outline=OUTLINE, width=ow)
        c.line([P(lx + s * 0.08, 0.18), P(lx + s * 0.1, 0.52)], fill=alpha(fur_d, 170), width=0.035)
        c.ellipse(cx + lx + s * 0.02, fy + 0.05, 0.23, 0.085, fill=fur_d, outline=OUTLINE, width=ow)
        claws(lx + s * 0.02, -0.02, 4, 0.1, 0.055)
    # Rumpf: eine Silhouette, Huefte und Bauch breit, nach oben leicht schmaler, rechts der Schulterbuckel und
    # der breite Nacken (der Kopf ist nach links gedreht, deshalb zeigt sich der Buckel rechts vom Kopf)
    body = [(-0.5, 0.42), (-0.6, 0.8), (-0.58, 1.1), (-0.48, 1.42), (-0.4, 1.62), (-0.26, 1.76), (-0.08, 1.82),
            (0.12, 1.92), (0.32, 1.9), (0.44, 1.76), (0.5, 1.5), (0.56, 1.15), (0.58, 0.8), (0.5, 0.42), (0.25, 0.34), (0, 0.36), (-0.25, 0.34)]
    c.poly(wob(body, 3, amp=0.02), fill=fur, outline=OUTLINE, width=ow)
    shag([(0.0, 1.55), (0.14, 1.86), (0.3, 1.86), (0.42, 1.7), (0.42, 1.45), (0.2, 1.35)], fur_d, 4)                       # Buckel und Nacken
    shag([(0.3, 0.5), (0.52, 0.8), (0.52, 1.3), (0.4, 1.45), (0.3, 1.1)], alpha(fur_d, 150), 5)                           # rechte Flanke
    shag([(-0.22, 0.5), (0.0, 0.46), (0.2, 0.52), (0.14, 1.0), (0.04, 1.4), (-0.12, 1.4), (-0.24, 1.0)], fur_l, 6)        # helle Brust und Bauch
    shag([(-0.56, 1.0), (-0.44, 0.9), (-0.4, 1.35), (-0.5, 1.4)], alpha(fur_d, 110), 7)                                     # linke Flanke
    # Vorderpranken: haengen locker vor der Brust, Ellbogen aussen, Pranken fast beieinander vor dem Bauch
    for s in (-1, 1):
        limb_stroke([(s * 0.38, 1.5), (s * 0.47, 1.1), (s * 0.17, 0.9)], 0.24)
        c.line([P(s * 0.3, 1.46), P(s * 0.38, 1.15)], fill=alpha(fur_d, 140), width=0.03)
        c.ellipse(cx + s * 0.16, fy + 0.86, 0.135, 0.1, fill=fur_d, outline=OUTLINE, width=ow)                             # Pranke
        c.ellipse(cx + s * 0.16, fy + 0.88, 0.08, 0.05, fill=alpha(limb, 200))
        claws(s * 0.16, 0.8, 4, 0.062, 0.05, s)
    # Kopf: klein, leicht erhoben, nach links gedreht; Ohren zuerst (liegen hinter dem Kopf)
    hx, hy = -0.1, 1.98
    for ex_, ey_, r in ((hx - 0.16, hy + 0.19, 0.065), (hx + 0.2, hy + 0.15, 0.08)):
        c.ellipse(cx + ex_, fy + ey_, r, r * 0.92, fill=fur, outline=OUTLINE, width=ow)
        c.ellipse(cx + ex_, fy + ey_, r * 0.5, r * 0.45, fill=fur_d)
    c.poly(wob([(hx - 0.2, hy - 0.2), (hx - 0.3, hy - 0.04), (hx - 0.24, hy + 0.14), (hx - 0.08, hy + 0.24), (hx + 0.14, hy + 0.23),
                (hx + 0.27, hy + 0.1), (hx + 0.28, hy - 0.1), (hx + 0.16, hy - 0.26), (hx - 0.04, hy - 0.28)], 8, amp=0.01),
           fill=fur, outline=OUTLINE, width=ow)
    shag([(hx + 0.04, hy - 0.22), (hx + 0.24, hy - 0.12), (hx + 0.22, hy + 0.04), (hx + 0.06, hy - 0.02)], alpha(fur_l, 120), 9, amp=0.02, tooth=0.05)   # Wange
    # Schnauze nach links, Nase dunkel, Maul geschlossen
    c.poly(wob([(hx - 0.1, hy + 0.04), (hx - 0.3, hy + 0.0), (hx - 0.4, hy - 0.05), (hx - 0.4, hy - 0.15), (hx - 0.3, hy - 0.22), (hx - 0.1, hy - 0.21)], 10, amp=0.008),
           fill=muzzle, outline=OUTLINE, width=ow)
    c.line([P(hx - 0.14, hy - 0.06), P(hx - 0.3, hy - 0.05)], fill=alpha(shade(muzzle, 0.85), 200), width=0.02)                                  # Nasenruecken
    c.line([P(hx - 0.33, hy - 0.17), P(hx - 0.16, hy - 0.16)], fill=alpha(OUTLINE, 210), width=0.013)                                           # Maul
    c.line([P(hx - 0.33, hy - 0.17), P(hx - 0.36, hy - 0.13)], fill=alpha(OUTLINE, 210), width=0.011)
    c.ellipse(cx + hx - 0.39, fy + hy - 0.08, 0.05, 0.04, fill=hexc("#1a1418"), outline=OUTLINE, width=0.014)                                   # Nase
    c.ellipse(cx + hx - 0.405, fy + hy - 0.065, 0.014, 0.01, fill=(255, 255, 255, 140))
    # kleine Glasaugen mit Lichtpunkt, Brauen
    for ex_, ey_ in ((hx - 0.2, hy + 0.07), (hx + 0.04, hy + 0.09)):
        c.ellipse(cx + ex_, fy + ey_, 0.027, 0.027, fill=hexc("#4a2e10"), outline=OUTLINE, width=0.012)
        c.ellipse(cx + ex_, fy + ey_, 0.013, 0.013, fill=hexc("#1a1418"))
        c.ellipse(cx + ex_ - 0.008, fy + ey_ + 0.01, 0.006, 0.006, fill=(255, 255, 255, 240))
    c.line([P(hx - 0.26, hy + 0.13), P(hx - 0.14, hy + 0.14)], fill=alpha(fur_d, 190), width=0.016)
    c.line([P(hx - 0.02, hy + 0.15), P(hx + 0.1, hy + 0.13)], fill=alpha(fur_d, 190), width=0.016)
    cobweb(c, cx + 0.5, fy + 1.3, 0.16, -1, 1, seed=idx)
    dust(c, cx - 0.3, fy + 1.6, cx + 0.3, fy + 1.75, 4, seed=idx)


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


def fountain_statue(c, cx, base, idx=0, pose=None):
    """Weeping Angel (Nachtrag 3, Vorbild Doctor Who) auf dem Saeulenkopf des Brunnens; base = Bild-y der Fuesse.
    Steinengel mit grossen angelegten Fluegeln, langem Gewand mit Faltenwurf, Kopf leicht gesenkt, verwittert.
    pose None: beide Haende vor den Augen. "turn": Haende unten, eine halb erhoben, Kopf zum Betrachter mit grimmiger
    Fratze (aufgerissenes Maul mit Steinzaehnen, leere Augen, gefurchte Stirn). "step": ein Stueck vorgerueckt (steht
    vorn auf dem Saeulenkopf, groesser), weit vorgebeugt, ein Arm greift zum Betrachter, Fluegel halb offen, Fratze.
    Wird nur von brunnen_blut gezeichnet (Grundbild und Tauschbilder), nicht mehr vom Brunnen selbst."""
    col, col_l, col_d = STONE, STONE_L, STONE_D
    s = 1.0
    if pose == "step":
        s = 1.12
        base -= 0.22                      # vorn auf dem Saeulenkopf (zum Betrachter = nach Sueden)
    grim = pose in ("turn", "step")
    wing_open = 0.0 if pose != "step" else 0.6

    def X(dx):
        return cx + dx * s

    def Z(dz):
        return base + dz * s

    def pt(dx, dz):
        return (X(dx), Z(dz))

    # Fluegel (hinten): angelegt, geschwungene Aussenkante, Spitzen bis fast zum Saum; bei "step" halb geoeffnet
    for sx in (-1, 1):
        w = 0.5 + 0.35 * wing_open
        wing = [pt(sx * 0.14, 1.25), pt(sx * (0.26 + 0.1 * wing_open), 1.62), pt(sx * (0.42 + 0.15 * wing_open), 1.72), pt(sx * (w + 0.08), 1.6),
                pt(sx * (w + 0.18), 1.35), pt(sx * (w + 0.16), 1.0), pt(sx * (w + 0.04), 0.62), pt(sx * (0.5 + 0.1 * wing_open), 0.3),
                pt(sx * (0.4 + 0.1 * wing_open), 0.22), pt(sx * 0.3, 0.42), pt(sx * 0.26, 0.9)]
        wing = HD.wobble(wing, amp=0.01, seed=idx + (3 if sx > 0 else 5), step=0.08, closed=True)
        c.poly(wing, fill=col_l, outline=OUTLINE, width=A.OUT_W)
        for row in range(3):
            for k in range(5):
                t = 0.08 + k * 0.2
                fx = sx * (0.28 + (w - 0.2) * t + row * 0.04)
                fz = 0.32 + 1.2 * t - row * 0.22
                c.line([pt(fx, fz), pt(fx - sx * 0.02, fz - 0.16)], fill=alpha(col_d, 170), width=0.011)
                c.ellipse(X(fx - sx * 0.02), Z(fz - 0.17), 0.03 * s, 0.02 * s, outline=alpha(col_d, 170), width=0.008)
        c.line([pt(sx * 0.3, 1.58), pt(sx * (w + 0.06), 1.4)], fill=alpha((255, 255, 255, 255), 100), width=0.016)
    # Gewand mit Faltenwurf, welliger Saum auf dem Saeulenkopf
    gown = HD.wobble([pt(-0.36, 0.0), pt(0.36, 0.0), pt(0.28, 0.55), pt(0.22, 0.95), pt(-0.22, 0.95), pt(-0.28, 0.55)],
                     amp=0.012, seed=idx, step=0.06, closed=True)
    c.poly(gown, fill=col, outline=OUTLINE, width=A.OUT_W)
    for k in range(6):
        c.line(HD.wobble([pt(-0.17 + k * 0.07, 0.9), pt(-0.27 + k * 0.11, 0.05)], amp=0.01, seed=idx + k, step=0.05), fill=alpha(col_d, 160), width=0.014)
    c.line([pt(-0.24, 0.1), pt(-0.17, 0.85)], fill=alpha((255, 255, 255, 255), 100), width=0.022)
    for k in range(5):
        c.ellipse(X(-0.28 + k * 0.14), Z(0.0), 0.07 * s, 0.03 * s, fill=col, outline=OUTLINE, width=0.014)
    c.rect(X(-0.2), Z(0.92), X(0.2), Z(0.98), fill=col_d, outline=OUTLINE, width=0.012)            # Guertel
    # Oberkoerper (bei "step" weit vorgebeugt: breiter und niedriger)
    lean = 0.12 if pose == "step" else 0.0
    c.poly([pt(-0.24, 0.96), pt(0.24, 0.96), pt(0.22 + lean, 1.26 - lean), pt(-0.22 + lean, 1.26 - lean)], fill=col, outline=OUTLINE, width=A.OUT_W)
    c.line([pt(-0.18, 1.0), pt(-0.16 + lean, 1.22 - lean)], fill=alpha((255, 255, 255, 255), 90), width=0.016)
    hz = 1.4 - lean * 1.5
    hx = lean * 1.2
    # Arme je Pose
    if pose is None:
        for sx in (-1, 1):                                                                    # Haende vor den Augen
            c.line([pt(sx * 0.22, 1.2), pt(sx * 0.34, 1.34), pt(sx * 0.08, hz + 0.02)], fill=OUTLINE, width=0.095)
            c.line([pt(sx * 0.22, 1.2), pt(sx * 0.34, 1.34), pt(sx * 0.08, hz + 0.02)], fill=col_l, width=0.06)
    elif pose == "turn":
        c.line([pt(-0.2, 1.2), pt(-0.3, 1.0), pt(-0.26, 0.74)], fill=OUTLINE, width=0.075)         # linker Arm haengt
        c.line([pt(-0.2, 1.2), pt(-0.3, 1.0), pt(-0.26, 0.74)], fill=col_l, width=0.045)
        c.ellipse(X(-0.26), Z(0.72), 0.06 * s, 0.05 * s, fill=col_l, outline=OUTLINE, width=0.015)
        c.line([pt(0.2, 1.2), pt(0.36, 1.1), pt(0.32, 1.36)], fill=OUTLINE, width=0.075)            # rechter halb erhoben
        c.line([pt(0.2, 1.2), pt(0.36, 1.1), pt(0.32, 1.36)], fill=col_l, width=0.045)
        hand = pt(0.32, 1.4)
        c.ellipse(hand[0], hand[1], 0.065 * s, 0.055 * s, fill=col_l, outline=OUTLINE, width=0.015)
        for k in range(4):
            a = math.pi * (0.25 + k * 0.17)
            c.line([hand, (hand[0] + 0.1 * s * math.cos(a), hand[1] + 0.1 * s * math.sin(a))], fill=OUTLINE, width=0.03)
            c.line([hand, (hand[0] + 0.1 * s * math.cos(a), hand[1] + 0.1 * s * math.sin(a))], fill=col_l, width=0.014)
    else:
        c.line([pt(-0.2, 1.2), pt(-0.34, 1.02), pt(-0.3, 0.8)], fill=OUTLINE, width=0.075)         # linker Arm zurueck
        c.line([pt(-0.2, 1.2), pt(-0.34, 1.02), pt(-0.3, 0.8)], fill=col_l, width=0.045)
        c.ellipse(X(-0.3), Z(0.78), 0.06 * s, 0.05 * s, fill=col_l, outline=OUTLINE, width=0.015)
        c.line([pt(0.22, 1.2), pt(0.42, 1.08), pt(0.38, 0.72)], fill=OUTLINE, width=0.085)          # rechter Arm greift nach vorn (zum Betrachter = nach unten)
        c.line([pt(0.22, 1.2), pt(0.42, 1.08), pt(0.38, 0.72)], fill=col_l, width=0.052)
        hand = pt(0.38, 0.64)
        c.ellipse(hand[0], hand[1], 0.1 * s, 0.085 * s, fill=col_l, outline=OUTLINE, width=0.02)    # grosse greifende Hand
        for k in range(4):
            a = math.pi * (1.15 + k * 0.23)
            tip = (hand[0] + 0.15 * s * math.cos(a), hand[1] + 0.15 * s * math.sin(a))
            c.line([hand, tip], fill=OUTLINE, width=0.04)
            c.line([hand, tip], fill=col_l, width=0.02)
            c.poly([(tip[0] - 0.015, tip[1]), (tip[0] + 0.015, tip[1]), (tip[0] + 0.004 * math.cos(a), tip[1] + 0.05 * math.sin(a))], fill=col_d, outline=OUTLINE, width=0.01)
    # Kopf: gesenkt mit Haar (Grundbild) oder Fratze zum Betrachter
    c.ellipse(X(hx), Z(hz), 0.13 * s, 0.14 * s, fill=col_l, outline=OUTLINE, width=A.OUT_W)
    c.ellipse(X(hx - 0.01), Z(hz + 0.09), 0.145 * s, 0.075 * s, fill=col, outline=OUTLINE, width=0.015)       # Haar
    for k in range(4):
        c.line([pt(hx - 0.1 + k * 0.065, hz + 0.15), pt(hx - 0.13 + k * 0.08, hz + 0.02)], fill=alpha(col_d, 150), width=0.01)
    if not grim:
        c.poly([pt(-0.1, hz - 0.1), pt(0.1, hz - 0.1), pt(0.11, hz + 0.05), pt(-0.11, hz + 0.05)], fill=shade(col_l, 1.08), outline=OUTLINE, width=0.015)   # Haende vor den Augen
        for k in range(5):
            c.line([pt(-0.08 + k * 0.04, hz - 0.08), pt(-0.08 + k * 0.04, hz + 0.03)], fill=alpha(col_d, 170), width=0.006)
        c.line([pt(-0.03, hz - 0.11), pt(0.03, hz - 0.11)], fill=alpha(col_d, 150), width=0.01)   # Mund darunter
    else:
        for sx in (-1, 1):                                                                    # leere Augen, gefurchte Stirn
            c.ellipse(X(hx + sx * 0.05), Z(hz + 0.02), 0.032 * s, 0.03 * s, fill=hexc("#1a1c22"), outline=OUTLINE, width=0.012)
            c.line([pt(hx + sx * 0.01, hz + 0.07), pt(hx + sx * 0.09, hz + 0.05)], fill=OUTLINE, width=0.022)
        c.line([pt(hx - 0.03, hz + 0.1), pt(hx + 0.03, hz + 0.1)], fill=alpha(col_d, 200), width=0.01)
        c.line([pt(hx - 0.02, hz + 0.13), pt(hx + 0.02, hz + 0.13)], fill=alpha(col_d, 200), width=0.01)
        c.poly([pt(hx - 0.075, hz - 0.04), pt(hx + 0.075, hz - 0.04), pt(hx + 0.06, hz - 0.12), pt(hx - 0.06, hz - 0.12)], fill=hexc("#1a1c22"), outline=OUTLINE, width=0.015)   # Maul
        for k in range(5):
            tx = hx - 0.06 + k * 0.03
            c.poly([pt(tx - 0.012, hz - 0.04), pt(tx + 0.012, hz - 0.04), pt(tx, hz - 0.075)], fill=col_l, outline=OUTLINE, width=0.006)
            c.poly([pt(tx - 0.01, hz - 0.12), pt(tx + 0.01, hz - 0.12), pt(tx, hz - 0.09)], fill=col_l, outline=OUTLINE, width=0.006)
        c.line([pt(hx, hz + 0.0), pt(hx - 0.012, hz - 0.03), pt(hx + 0.012, hz - 0.03)], fill=alpha(col_d, 200), width=0.01)
    # Verwitterung: Flechten, Moos am Saum, Risse
    rs = random.Random(idx + 3)
    for k in range(7):
        c.ellipse(X(rs.uniform(-0.45, 0.45)), Z(rs.uniform(0.2, 1.5)), 0.02, 0.013, fill=alpha(hexc("#b8c070"), 150))
    moss(c, X(-0.2), Z(0.04), 0.08, seed=idx)
    crack(c, [pt(0.1, 0.2), pt(0.05, 0.5), pt(0.12, 0.75)], seed=idx)
    cobweb(c, X(0.42), Z(1.2), 0.1, 1, -1, seed=idx)


def _brunnen(p, c, x0, y0, x1, y1, idx, rnd):
    """Brunnen (24.10.): ovales Becken (Kollision Ellipse 2,4 x 1,5 m um (cx, cy - 0,05)) mit Steinkranz aus Bloecken
    und Deckplatten, dunkles Wasser mit Mondreflex und Laub, kannelierte Mittelsaeule mit Kapitell, Moos, Risse,
    Pfuetze. Die Figur (Weeping Angel) zeichnet seit Nachtrag 3 nur brunnen_blut (Grundbild und Tauschbilder)."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - 0.05
    rx, ry = 1.2, 0.75
    wall_h = 0.5
    zt = wall_h * K
    c.ellipse(cx, cy, rx, ry, fill=STONE, outline=OUTLINE, width=A.OUT_W)
    c.rect(cx - rx, cy, cx + rx, cy + zt, fill=STONE)
    c.line([(cx - rx, cy), (cx - rx, cy + zt)], fill=OUTLINE, width=A.OUT_W)
    c.line([(cx + rx, cy), (cx + rx, cy + zt)], fill=OUTLINE, width=A.OUT_W)
    c.poly([(cx - rx + 0.03, cy + 0.02), (cx + rx - 0.03, cy + 0.02), (cx + rx - 0.03, cy + 0.08), (cx - rx + 0.03, cy + 0.08)], fill=STONE_D)
    for k in range(13):
        a = math.pi + k * math.pi / 12
        bx = cx + rx * math.cos(a)
        byy = cy + ry * math.sin(a)
        c.line([(bx, byy + 0.03), (bx, byy + zt - 0.02)], fill=alpha(STONE_D, 170), width=0.014)
    c.line([(cx - rx + 0.2, cy + zt * 0.5 - ry * 0.5), (cx + rx - 0.2, cy + zt * 0.5 - ry * 0.5)], fill=alpha(STONE_D, 120), width=0.012)
    top = cy + zt
    c.ellipse(cx, top, rx, ry, fill=STONE_L, outline=OUTLINE, width=A.OUT_W)
    for k in range(16):
        a = k * math.tau / 16
        c.line([(cx + (rx - 0.26) * math.cos(a), top + (ry - 0.16) * math.sin(a)), (cx + (rx - 0.02) * math.cos(a), top + (ry - 0.02) * math.sin(a))],
               fill=alpha(STONE_D, 170), width=0.012)
    c.ellipse(cx, top, rx - 0.04, ry - 0.03, outline=alpha((255, 255, 255, 255), 70), width=0.015)
    wx, wy = rx - 0.26, ry - 0.16
    c.ellipse(cx, top, wx, wy, fill=hexc("#243038"), outline=STONE_D, width=0.02)
    c.ellipse(cx, top + 0.02, wx - 0.08, wy - 0.06, fill=hexc("#2a3a44"))
    c.ellipse(cx - wx * 0.35, top + 0.1, wx * 0.3, wy * 0.12, fill=alpha(MOON, 70))
    c.ellipse(cx - wx * 0.33, top + 0.11, wx * 0.14, wy * 0.05, fill=alpha(MOON, 110))
    for k in range(3):
        c.ellipse(cx, top + 0.06, 0.4 + k * 0.14, 0.14 + k * 0.05, outline=alpha(MOON, 60 - k * 15), width=0.012)
    for k in range(6):
        lx, ly = cx + rnd.uniform(-wx * 0.7, wx * 0.7), top + rnd.uniform(-wy * 0.5, wy * 0.6)
        c.poly([(lx - 0.045, ly), (lx, ly + 0.025), (lx + 0.045, ly), (lx, ly - 0.025)], fill=rnd.choice((hexc("#8a5a34"), hexc("#a8803c"))), outline=OUTLINE, width=0.006)
    crack(c, [(cx + rx * 0.5, cy + 0.03), (cx + rx * 0.45, cy + 0.25 * K), (cx + rx * 0.55, cy + 0.48 * K)], seed=idx)
    moss(c, cx - rx * 0.6, cy + 0.1, 0.12, seed=idx)
    moss(c, cx + rx * 0.3, top - 0.02, 0.1, seed=idx + 1)
    moss(c, cx - rx * 0.85, top + 0.05, 0.08, seed=idx + 2)
    fountain_column(c, cx, top + 0.12, idx)
    c.ellipse(cx + rx * 0.95, cy - ry * 0.4, 0.14, 0.06, fill=alpha(hexc("#243038"), 150))


def fountain_column(c, cx, base, idx=0):
    """Kannelierte Saeule in der Beckenmitte mit Basis und Kapitell; base = Bild-y des Saeulenfusses, Oberkante
    (Standflaeche der Figur) liegt bei base + 0,6."""
    col, col_l, col_d = STONE, STONE_L, STONE_D
    c.ellipse(cx, base, 0.3, 0.14, fill=col_l, outline=OUTLINE, width=0.025)
    c.rect(cx - 0.17, base, cx + 0.17, base + 0.5, fill=col, outline=OUTLINE, width=A.OUT_W)
    for k in range(4):
        c.line([(cx - 0.11 + k * 0.07, base + 0.04), (cx - 0.11 + k * 0.07, base + 0.46)], fill=alpha(col_d, 170), width=0.012)
    c.line([(cx - 0.14, base + 0.04), (cx - 0.14, base + 0.46)], fill=alpha((255, 255, 255, 255), 110), width=0.016)
    c.rect(cx - 0.22, base + 0.5, cx + 0.22, base + 0.6, fill=col_l, outline=OUTLINE, width=0.025)
    c.ellipse(cx, base + 0.6, 0.22, 0.09, fill=col_l, outline=OUTLINE, width=0.02)                   # Saeulenkopf (Standflaeche)
    moss(c, cx + 0.1, base + 0.08, 0.1, seed=idx)
    for sx in (-1, 1):                                                                              # Wasser laeuft an der Saeule herab
        c.line([(cx + sx * 0.19, base + 0.5), (cx + sx * 0.24, base + 0.3), (cx + sx * 0.26, base + 0.05)], fill=alpha(hexc("#9fc4e0"), 140), width=0.02)


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


def _stuhl(p, c, x, y, w, d, z, idx, inverted=False, splay=0.0):
    """Esszimmerstuhl (Nussholz) mit Standpunkt (x, y) = vordere linke Ecke, auf Hoehe z. inverted: steht
    kopfueber (Sitz unten, Beine zeigen nach oben, leicht gespreizt), die Lehne haengt hinten herab."""
    seat_h, leg_h, back_h = 0.06, 0.46, 0.5
    leg = WALNUT_D
    if not inverted:
        for (lx, ly) in ((x + 0.04, y + 0.05), (x + w - 0.04, y + 0.05), (x + 0.06, y + d - 0.06), (x + w - 0.06, y + d - 0.06)):
            c.line([(lx, ly + z * K), (lx, ly + (z + leg_h) * K)], fill=OUTLINE, width=0.05)
            c.line([(lx, ly + z * K), (lx, ly + (z + leg_h) * K)], fill=leg, width=0.03)
        c.line([(x + 0.04, y + 0.05 + (z + leg_h * 0.45) * K), (x + w - 0.04, y + 0.05 + (z + leg_h * 0.45) * K)], fill=OUTLINE, width=0.035)   # Zarge
        c.line([(x + 0.04, y + 0.05 + (z + leg_h * 0.45) * K), (x + w - 0.04, y + 0.05 + (z + leg_h * 0.45) * K)], fill=leg, width=0.018)
        p.box(x, y, x + w, y + d, z + leg_h, seat_h, BORDEAUX, WALNUT, w=0.03)                    # Sitz mit Samtpolster
        bz = z + leg_h + seat_h
        p.box(x + 0.02, y + d - 0.08, x + w - 0.02, y + d, bz, back_h, WALNUT_L, WALNUT, w=0.03)   # Lehne
        for k in range(3):                                                                          # Sprossen
            sx = x + 0.02 + (k + 1) * (w - 0.04) / 4
            c.line([(sx, y + d - 0.08 + (bz + 0.06) * K), (sx, y + d - 0.08 + (bz + back_h - 0.06) * K)], fill=shade(WALNUT, 0.7), width=0.014)
    else:
        bz = z
        p.box(x + 0.02, y + d - 0.08, x + w - 0.02, y + d, bz - back_h * 0.9, back_h * 0.9, WALNUT_L, WALNUT, w=0.03)   # Lehne haengt hinten vom Sitz herab
        p.box(x, y, x + w, y + d, bz, seat_h, WALNUT_L, BORDEAUX, w=0.03)                          # Sitz (Unterseite oben)
        tz = bz + seat_h
        for (lx, ly, sp) in ((x + 0.04, y + 0.05, -1), (x + w - 0.04, y + 0.05, 1), (x + 0.06, y + d - 0.06, -0.6), (x + w - 0.06, y + d - 0.06, 0.6)):
            ex = lx + sp * splay
            c.line([(lx, ly + tz * K), (ex, ly + (tz + leg_h) * K)], fill=OUTLINE, width=0.05)
            c.line([(lx, ly + tz * K), (ex, ly + (tz + leg_h) * K)], fill=leg, width=0.03)
            c.ellipse(ex, ly + (tz + leg_h) * K, 0.02, 0.014, fill=WALNUT_L, outline=OUTLINE, width=0.012)
        c.line([(x + 0.04 - splay * 0.45, y + 0.05 + (tz + leg_h * 0.45) * K), (x + w - 0.04 + splay * 0.45, y + 0.05 + (tz + leg_h * 0.45) * K)], fill=OUTLINE, width=0.035)
        c.line([(x + 0.04 - splay * 0.45, y + 0.05 + (tz + leg_h * 0.45) * K), (x + w - 0.04 + splay * 0.45, y + 0.05 + (tz + leg_h * 0.45) * K)], fill=leg, width=0.018)


def _treppensperre(p, c, x0, y0, x1, y1, idx, rnd):
    """Moebelstapel, der die Freitreppe versperrt: Kiste mit zwei Stuehlen darauf (der obere kopfueber,
    Beine nach oben), hochkant gestelltes Sofa unter einem Staublaken, Kommode mit Requisitenkiste, ein
    angelehnter Teppichrollen-Laeufer; davor gekreuztes Gaffer-Band mit Schild CLOSED, Spinnweben, Staub."""
    sheet = hexc("#c9c4b8")
    sheet_d, sheet_l = shade(sheet, 0.72), shade(sheet, 1.08)
    crate = lift("#6a4a2c", 1.5)
    # --- links: Kiste, darauf ein Stuhl, darauf ein zweiter kopfueber
    kx0, kx1 = x0, x0 + 0.85
    ky0, ky1 = y0 + 0.2, y0 + 0.9
    p.box(kx0, ky0, kx1, ky1, 0, 0.6, shade(crate, 1.15), crate)
    for k in range(2):
        c.line([(kx0 + 0.04, ky0 + 0.05 + k * 0.14), (kx1 - 0.04, ky0 + 0.05 + k * 0.14)], fill=shade(crate, 0.7), width=0.012)
    c.rect(kx0 + 0.03, ky0 + 0.04, kx0 + 0.1, ky0 + 0.6 * K - 0.03, fill=shade(crate, 0.85), outline=OUTLINE, width=0.012)
    c.rect(kx1 - 0.1, ky0 + 0.04, kx1 - 0.03, ky0 + 0.6 * K - 0.03, fill=shade(crate, 0.85), outline=OUTLINE, width=0.012)
    c.text((kx0 + kx1) / 2, ky0 + 0.3 * K, "PROPS", 0.08, alpha(OUTLINE, 170))
    sx, sy = kx0 + 0.18, ky0 + 0.12
    _stuhl(p, c, sx, sy, 0.46, 0.46, 0.6, idx)
    _stuhl(p, c, sx + 0.03, sy + 0.02, 0.44, 0.44, 0.6 + 0.46 + 0.06, idx, inverted=True, splay=0.07)
    # --- Mitte links: Sofa hochkant (steht auf der Armlehne), Lehne hinten, Sitzpolster als Wulst links
    vel = BORDEAUX
    vel_l, vel_d = shade(vel, 1.2), shade(vel, 0.78)
    fx0, fx1 = x0 + 0.95, x0 + 1.9
    fy0, fy1 = y0 + 0.1, y0 + 1.0
    SH = 1.95
    p.box(fx0, fy1 - 0.3, fx1, fy1, 0, SH, vel_l, vel)                                              # Rueckenlehne (Platte)
    for row, z in enumerate((0.45, 0.8, 1.15, 1.5)):                                                # Knopfheftung
        for k in range(3):
            bx = fx0 + 0.18 + (k + (0.5 if row % 2 else 0)) * 0.26
            if bx < fx1 - 0.08:
                c.ellipse(bx, fy1 - 0.3 + z * K, 0.014, 0.011, fill=vel_d)
    p.box(fx0, fy0, fx0 + 0.36, fy1 - 0.3, 0.3, SH - 0.6, vel_l, vel_d, w=0.04)                     # Sitzpolster (senkrecht)
    c.line([(fx0 + 0.04, fy0 + 0.5 * K), (fx0 + 0.04, fy0 + (SH - 0.5) * K)], fill=shade(vel, 1.35), width=0.012)   # Paspel
    for zz in (0.0, SH - 0.3):                                                                       # Armlehnen oben und unten
        p.box(fx0 - 0.02, fy0, fx1 + 0.02, fy1 - 0.25, zz, 0.3, vel_l, vel, w=0.04)
    for (lz, ly) in ((0.25, fy0 + 0.15), (SH - 0.45, fy0 + 0.15)):                                  # Fuesse zeigen nach links
        c.line([(fx0 - 0.02, ly + lz * K), (fx0 - 0.14, ly + (lz - 0.04) * K)], fill=OUTLINE, width=0.05)
        c.line([(fx0 - 0.02, ly + lz * K), (fx0 - 0.14, ly + (lz - 0.04) * K)], fill=WALNUT_L, width=0.03)
    # Staublaken ueber dem oberen Teil: haengt vorn in Falten herab, Saum zittrig
    top = fy1 + SH * K
    hem = HD.wobble([(fx0 - 0.08, fy0 + 1.05 * K), (fx0 + 0.3, fy0 + 0.95 * K), (fx0 + 0.6, fy0 + 1.12 * K), (fx1 + 0.08, fy0 + 1.0 * K)],
                    amp=0.02, seed=idx, step=0.08)
    drape = [(fx0 - 0.08, top + 0.02), (fx1 + 0.1, top + 0.02), (fx1 + 0.1, fy0 + 1.0 * K)] + list(reversed(hem))[:-1]
    c.poly(drape, fill=sheet, outline=OUTLINE, width=0.035)
    c.poly([(fx0 - 0.05, top), (fx1 + 0.07, top), (fx1 + 0.05, top + 0.06), (fx0 - 0.03, top + 0.06)], fill=sheet_l)   # Oberseite
    for k in range(5):                                                                              # Falten
        fxk = fx0 + 0.1 + k * 0.2
        c.line(HD.wobble([(fxk, top - 0.04), (fxk + rnd.uniform(-0.05, 0.05), fy0 + 1.1 * K + rnd.uniform(-0.03, 0.03))], amp=0.015, seed=idx + k, step=0.06),
               fill=alpha(sheet_d, 160), width=0.014)
    c.line(hem, fill=sheet_d, width=0.012)
    # --- Mitte rechts: Kommode (Nussholz, zwei Schubladen, Messinggriffe), darauf Requisitenkiste
    dx0, dx1 = x0 + 2.0, x0 + 2.95
    dy0, dy1 = y0 + 0.25, y0 + 0.85
    p.box(dx0, dy0, dx1, dy1, 0, 1.0, WALNUT_L, WALNUT)
    c.rect(dx0 + 0.02, dy0 + 0.02, dx1 - 0.02, dy0 + 0.08 * K, fill=WALNUT_D)                       # Sockel
    for z in (0.12, 0.56):
        c.rect(dx0 + 0.07, dy0 + z * K, dx1 - 0.07, dy0 + (z + 0.38) * K, fill=shade(WALNUT, 0.92), outline=OUTLINE, width=0.02)
        c.line([(dx0 + 0.1, dy0 + (z + 0.36) * K), (dx1 - 0.1, dy0 + (z + 0.36) * K)], fill=WALNUT_L, width=0.01)
        for gx in (dx0 + 0.28, dx1 - 0.28):
            c.ellipse(gx, dy0 + (z + 0.19) * K, 0.045, 0.03, outline=OUTLINE, width=0.03)
            c.ellipse(gx, dy0 + (z + 0.19) * K, 0.045, 0.03, outline=BRASS, width=0.014)
            c.ellipse(gx, dy0 + (z + 0.21) * K, 0.012, 0.01, fill=BRASS_L)
    c.rect(dx0 + 0.07, dy0 + 0.56 * K, dx0 + 0.11, dy0 + 0.94 * K, fill=shade(WALNUT, 0.55))        # eine Schublade steht offen (Schattenspalt)
    cx0, cx1 = dx0 + 0.1, dx1 - 0.1
    cy0, cy1 = dy0 + 0.05, dy1 - 0.05
    p.box(cx0, cy0, cx1, cy1, 1.0, 0.55, shade(crate, 1.1), shade(crate, 0.95))
    c.rect(cx0 + 0.03, cy0 + 1.0 * K + 0.04, cx0 + 0.09, cy0 + 1.55 * K - 0.03, fill=shade(crate, 0.85), outline=OUTLINE, width=0.012)
    c.rect(cx1 - 0.09, cy0 + 1.0 * K + 0.04, cx1 - 0.03, cy0 + 1.55 * K - 0.03, fill=shade(crate, 0.85), outline=OUTLINE, width=0.012)
    c.text((cx0 + cx1) / 2, cy0 + 1.28 * K, "FRAGILE", 0.065, alpha(hexc("#b03030"), 200))
    dust(c, cx0 + 0.1, cy0 + 0.05 + 1.55 * K, cx1 - 0.1, cy1 - 0.05 + 1.55 * K, 7, seed=idx)
    # --- rechts: Teppichrolle (Laeufer, Bordeaux) lehnt schraeg an der Kiste
    rx0, ry0 = x1 - 0.12, y0 + 0.3
    rx1, ry1 = dx1 - 0.25, cy0 + 1.62 * K
    ang = math.atan2(ry1 - ry0, rx1 - rx0)
    nx, ny = -math.sin(ang) * 0.11, math.cos(ang) * 0.11
    roll = [(rx0 + nx, ry0 + ny), (rx1 + nx, ry1 + ny), (rx1 - nx, ry1 - ny), (rx0 - nx, ry0 - ny)]
    c.poly(roll, fill=BORDEAUX_D, outline=OUTLINE, width=A.OUT_W)
    c.line([(rx0 + nx * 0.5, ry0 + ny * 0.5), (rx1 + nx * 0.5, ry1 + ny * 0.5)], fill=shade(BORDEAUX, 1.15), width=0.03)
    c.line([(rx0 - nx * 0.5, ry0 - ny * 0.5), (rx1 - nx * 0.5, ry1 - ny * 0.5)], fill=shade(BORDEAUX_D, 0.75), width=0.025)
    c.ellipse(rx0, ry0, 0.11, 0.11, fill=shade(BORDEAUX, 1.05), outline=OUTLINE, width=A.OUT_W)   # Stirnseite der Rolle (Spirale)
    c.ellipse(rx0, ry0, 0.07, 0.07, outline=shade(BORDEAUX_D, 0.8), width=0.014)
    c.ellipse(rx0 + 0.01, ry0 - 0.01, 0.03, 0.03, outline=shade(BORDEAUX_D, 0.8), width=0.012)
    c.line([(rx0 - 0.08, ry0 + nx * 0.4), (rx1 - 0.1, ry1 - 0.02)], fill=alpha(BRASS, 150), width=0.012)   # Messingstange steckt in der Rolle
    # --- Gaffer-Band gekreuzt ueber die Front, Schild CLOSED am Kreuzungspunkt
    gz = 1.15
    ga = (kx0 + 0.1, ky0 + (gz - 0.55) * K)
    gb = (dx1 + 0.05, dy0 + (gz + 0.3) * K)
    gaffer(c, ga[0], ga[1], gb[0], gb[1], 0.05)
    c.line([ga, gb], fill=alpha(MATTE_D, 180), width=0.012)
    gc_ = (kx0 + 0.1, ky0 + (gz + 0.45) * K)
    gd = (dx1 + 0.05, dy0 + (gz - 0.45) * K)
    gaffer(c, gc_[0], gc_[1], gd[0], gd[1], 0.05)
    c.line([gc_, gd], fill=alpha(MATTE_D, 180), width=0.012)
    mx = (ga[0] + gb[0]) / 2
    my = (ga[1] + gb[1] + gc_[1] + gd[1]) / 4
    c.rect(mx - 0.33, my - 0.17, mx + 0.33, my + 0.17, fill=CREAM, outline=OUTLINE, width=0.02)
    c.line([(mx - 0.3, my + 0.14), (mx + 0.3, my + 0.14)], fill=CREAM_D, width=0.01)
    c.text(mx, my + 0.075, "SET", 0.06, alpha(OUTLINE, 200))
    c.text(mx, my - 0.04, "CLOSED", 0.12, OUTLINE)
    c.line([(mx - 0.2, my - 0.13), (mx + 0.2, my - 0.13)], fill=BLOOD, width=0.012)
    gaffer(c, mx - 0.2, my + 0.17, mx - 0.08, my + 0.12, 0.035)                                     # Schild mit Tape befestigt
    gaffer(c, mx + 0.08, my + 0.12, mx + 0.2, my + 0.17, 0.035)
    # --- Spinnweben und Staub
    cobweb(c, sx + 0.03, sy + 0.02 + (0.6 + 0.52 + 0.46) * K, 0.22, 1, -1, seed=idx)                # zwischen den Stuhlbeinen
    cobweb(c, fx1 + 0.1, top + 0.02, 0.2, 1, -1, seed=idx + 1)                                      # Sofa-Oberkante zur Kommode
    cobweb(c, dx1, cy0 + 1.55 * K, 0.16, -1, 1, seed=idx + 2)
    dust(c, fx0, top + 0.01, fx1, top + 0.05, 6, seed=idx + 3)
    # --- Horror-Schicht (Audit 15.10.): genagelte Bretter quer ueber den Aufgang, Kratzspuren auf dem Laken,
    #     eine Hand unter dem Saum, Blut am Fuss der Sperre
    plank = shade(WALNUT_L, 0.9)
    for (ax, ay, bx, by) in ((x0 + 0.05, top + 0.12, x1 - 0.05, top + 0.42), (x0 + 0.05, top + 0.5, x1 - 0.05, top + 0.22)):
        ang = math.atan2(by - ay, bx - ax)
        nx, ny = -math.sin(ang) * 0.09, math.cos(ang) * 0.09
        c.poly([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)], fill=plank, outline=OUTLINE, width=0.03)
        c.line([(ax + nx * 0.5, ay + ny * 0.5), (bx + nx * 0.5, by + ny * 0.5)], fill=shade(plank, 1.25), width=0.015)
        for t in (0.08, 0.5, 0.92):
            px_, py_ = ax + (bx - ax) * t, ay + (by - ay) * t
            c.ellipse(px_, py_, 0.016, 0.016, fill=STEEL, outline=OUTLINE, width=0.008)
    chalk_text(c, (x0 + x1) / 2, top + 0.3, "KEEP OUT", 0.1)
    for k in range(3):                                                                              # Kratzer im Laken
        sx_ = fx0 + 0.45 + k * 0.09
        c.line(HD.wobble([(sx_, top - 0.25), (sx_ + 0.12, fy0 + 1.25 * K)], amp=0.01, seed=idx + 10 + k, step=0.05),
               fill=shade(sheet_d, 0.75), width=0.016)
        c.line([(sx_ + 0.12, fy0 + 1.25 * K), (sx_ + 0.14, fy0 + 1.18 * K)], fill=BLOOD, width=0.012)
    hx_, hy_ = hem[1][0], hem[1][1] - 0.02                                                        # Hand unter dem Saum
    pale = hexc("#b9b0a6")
    c.poly([(hx_ - 0.07, hy_), (hx_ + 0.07, hy_ + 0.01), (hx_ + 0.06, hy_ - 0.08), (hx_ - 0.08, hy_ - 0.07)], fill=pale, outline=OUTLINE, width=0.014)
    for k, (fdx, fl) in enumerate(((-0.065, 0.07), (-0.025, 0.1), (0.015, 0.1), (0.05, 0.08))):
        c.line([(hx_ + fdx, hy_ - 0.07), (hx_ + fdx + 0.01, hy_ - 0.07 - fl)], fill=pale, width=0.028)
        c.line([(hx_ + fdx, hy_ - 0.07), (hx_ + fdx + 0.01, hy_ - 0.07 - fl)], fill=OUTLINE, width=0.036)
        c.line([(hx_ + fdx, hy_ - 0.07), (hx_ + fdx + 0.01, hy_ - 0.07 - fl)], fill=pale, width=0.022)
    blood_pool(c, hx_ + 0.1, fy0 + 0.02, 0.16, 0.06, seed=idx + 5, a=210)
    blood_drips(c, fx0 + 0.9, fy0 + 1.0 * K, 3, 0.1, seed=idx + 6)


_KIND_FN = {"standuhr": _standuhr, "seance_tisch": _seance_tisch, "buecherregal": _buecherregal, "kamin": _kamin, "kamin_gross": _kamin_gross,
            "kandelaber": _kandelaber, "kandelaber_aus": lambda *a: _kandelaber(*a, lit=False), "filmkamera": _filmkamera,
            "scheinwerfer": _scheinwerfer, "schminktisch": _schminktisch, "sessel": _sessel, "sarg": _sarg,
            "grabstein": _grabstein, "aggregat": _aggregat, "absperrung": _absperrung,
            "freitreppe": _freitreppe, "herd": _herd, "funktisch": _funktisch, "kisten": _kisten, "kessel": _kessel,
            "altar": _altar, "monitorwand": _monitorwand, "gewehrschrank": _gewehrschrank, "zelt": _zelt, "hecke": _hecke,
            "kuechentisch": _kuechentisch, "waschzuber": _waschzuber, "requisiten": _requisiten, "teleskop": _teleskop,
            "kohlen": _kohlen, "lesetisch": _lesetisch, "kirchenbank": _kirchenbank, "baer": _baer,
            "schreibtisch": _schreibtisch, "catering": _catering, "urne": _urne, "gartenbank": _gartenbank,
            "pflanztisch": _pflanztisch, "brunnen": _brunnen, "barrikade": _barrikade, "treppensperre": _treppensperre}


# Objekte aus einem fertigen Bild statt prozedural (Datei in tools/villa_assets/, Hoehe des ganzen Sprites in Metern).
# Der Baer kommt seit 24.10. aus einem vom User gelieferten Bild (gerade Vorderansicht, Blick nach Westen in den Raum).
IMAGE_PROPS = {"baer": ("villa_baer.png", 3.0),
               "kamin_gross": ("villa_kamin_gross.png", 2.6),      # 25.10.: GPT, Vorderansicht, Seance Parlour
               "requisiten": ("villa_requisiten.png", 1.35),       # 25.10.: GPT, Requisitentisch in der Box Room
               "engelsstatue_tuch": ("villa_engel_betend.png", 2.5)}   # 25.10.: GPT, betender Engel statt Tuchstatue (Kapelle)
_IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "villa_assets")


def _image_prop(kind, shape, ppm):
    """Sprite aus IMAGE_PROPS: Unterkante des Bilds (Sockel) auf der Standlinie, waagerecht mittig ueber der Fussflaeche,
    weicher Schatten darunter. None, wenn die Datei fehlt (dann zeichnet die Art wie bisher)."""
    file, height = IMAGE_PROPS[kind]
    path = os.path.join(_IMG_DIR, file)
    if not os.path.exists(path):
        return None
    x0, y0, x1, y1 = A.shape_bounds(shape)
    src = Image.open(path).convert("RGBA")
    h = int(round(height * ppm))
    w = int(round(src.width * h / src.height))
    im = src.resize((w, h), Image.LANCZOS)
    pad = int(0.12 * ppm)
    canvas = Image.new("RGBA", (w + 2 * pad, h + pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([pad + w * 0.06, h - 0.16 * ppm, pad + w * 0.97, h + 0.07 * ppm], fill=(0, 0, 0, 105))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(0.06 * ppm)))
    canvas.alpha_composite(im, (pad, 0))
    cx = (x0 + x1) / 2
    return canvas, cx - canvas.width / 2 / ppm, y0 - pad / ppm, y0


def draw(kind, shape, idx, ppm, variant=None):
    """Ein Objekt als Sprite: (RGBA-Bild, welt_x_links, welt_y_unten, standlinie_y). Vertrag wie park_art.draw.
    variant: Tauschbild derselben Art und Groesse (Mechaniken: Pendel, Blick, Licht aus), nur Arten mit
    variant-Parameter; gen_villa legt sie unter "Prop/<Art>/<x>/<y>/<Variante>" in den Konsolen-Atlas."""
    if kind in IMAGE_PROPS and variant is None:
        got = _image_prop(kind, shape, ppm)
        if got is not None:
            return got
    x0, y0, x1, y1 = A.shape_bounds(shape)
    h = PROP_H[kind]
    p = Prop(x0, y0, x1, y1, h, ppm, pad=PROP_PAD.get(kind, 0.3))
    c = p.c
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rnd = random.Random(idx * 131 + 7)
    if shape[0] in ("circle", "ellipse"):
        rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
        c.soft_shadow([(cx + 0.08 + rx * math.cos(t * math.pi / 12), cy - 0.08 + ry * math.sin(t * math.pi / 12)) for t in range(24)], 100, 0.1)
    elif kind not in ("absperrung", "hecke", "kohlen") and kind not in NO_SHADOW:
        c.soft_shadow([(x0 + 0.08, y0 - 0.1), (x1 + 0.12, y0 - 0.1), (x1 + 0.12, y1), (x0 + 0.08, y1)], 95, 0.09)
    if variant is None:
        _KIND_FN[kind](p, c, x0, y0, x1, y1, idx, rnd)
    else:
        _KIND_FN[kind](p, c, x0, y0, x1, y1, idx, rnd, variant=variant)
    return c.finish(), c.x0, c.y0, p.base_y
