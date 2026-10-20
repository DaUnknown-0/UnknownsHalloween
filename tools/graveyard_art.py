# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_art.py - Ravenhollow Cemetery: alle Objekte (Requisiten) im Among-Us-Stil.
#
# Regeln wie museum_art.py / villa_art.py (Unknown's Atlas, Hollowmere Manor): kraeftige Umrisse (OUT_W),
# flache Flaechen mit Licht- und Schattenkante, schraege Aufsicht K = 0,55 (Hoehe z erscheint als y + z*K),
# Standlinie = Kollision, weicher Bodenschatten nach Suedost. Weltmeter, y nach oben.
#
# Vertrag: draw(kind, shape, idx, ppm, ctx=None, variant=None) -> (RGBA, welt_x_links, welt_y_unten, standlinie_y).
# Dieselben Zeichner malen auch die Grabfelder und Baeume in den Boden (graveyard_floor.py, 80 px/m).
#
# Palette "Mondnacht": blaugrauer Granit, verwitterter Sandstein, Schiefer, Marmor; Moos und Flechten; kaltes
# Mondlicht als Glanzkante; warme Toene nur an Lichtquellen (Grablichter, Kerzen, Laternen, Ofenglut).

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS_TOOLS = os.path.normpath(os.path.join(HERE, "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)
sys.path.insert(0, HERE)

import museum_art as A                      # noqa: E402
import handdraw as HD                       # noqa: E402
from museum_art import K, OUTLINE, Prop, alpha, hexc, lift, shade   # noqa: E402

from PIL import Image, ImageDraw            # noqa: E402

# ------------------------------------------------------------------ Palette

GRANITE = lift("#5c6070", 1.55)
SANDSTONE = lift("#7a6e5a", 1.55)
SLATE = lift("#3e4450", 1.6)
MARBLE = hexc("#cdcac0")
MOSSY = lift("#4e5a50", 1.6)
STONES = [GRANITE, SANDSTONE, SLATE, MARBLE, MOSSY, GRANITE]
MOSS = hexc("#5f8a4c")
MOSS_D = hexc("#44663a")
LICHEN = hexc("#b8c070")
EARTH = lift("#3e3226", 1.6)
EARTH_D = shade(EARTH, 0.75)
GRASS = hexc("#4f7a5c")
GRASS_L = hexc("#7aa070")
WOOD = lift("#4a3c30", 1.6)
WOOD_D = shade(WOOD, 0.72)
WOOD_L = shade(WOOD, 1.22)
OAK = lift("#5a4028", 1.6)
IRON = hexc("#4a4c56")
IRON_L = shade(IRON, 1.35)
IRON_D = shade(IRON, 0.7)
RUST = hexc("#8a5434")
BRASS = hexc("#ac8a48")
BRASS_D = shade(BRASS, 0.68)
BRASS_L = hexc("#dcc27a")
CREAM = hexc("#dcd4bc")
BONE = hexc("#d6cdb4")
VELVET = lift("#4a1a26", 1.6)
RED_LAMP = hexc("#b0283a")
FLAME = hexc("#ffb43c")
FLAME_CORE = hexc("#fff4c8")
WARM = hexc("#ffd28a")
MOON = hexc("#c4d4ea")
FLOWER = [hexc("#9a3a4a"), hexc("#c8b860"), hexc("#d8d0c8"), hexc("#7a5a9a"), hexc("#b86a3a")]
DEAD_FLOWER = [hexc("#6a4a3a"), hexc("#7a6040"), hexc("#5a4048")]
LEAF = [hexc("#9a5a2e"), hexc("#7c4a2c"), hexc("#a8803c"), hexc("#6e3e32")]
YEW = lift("#1e3428", 1.7)
YEW_L = shade(YEW, 1.3)
YEW_D = shade(YEW, 0.72)
BARK = lift("#3a3430", 1.6)
BARK_L = shade(BARK, 1.3)
BARK_D = shade(BARK, 0.7)

OUT_W = A.OUT_W


# ------------------------------------------------------------------ Kleinteile

def flame(c, x, y, s=1.0, glow=True):
    if glow:
        c.glow(x, y + 0.04 * s, 0.45 * s, WARM, 0.45)
        c.glow(x, y + 0.03 * s, 0.16 * s, FLAME_CORE, 0.8)
    c.poly([(x - 0.028 * s, y), (x + 0.028 * s, y), (x + 0.02 * s, y + 0.055 * s), (x, y + 0.11 * s), (x - 0.02 * s, y + 0.055 * s)],
           fill=FLAME, outline=shade(FLAME, 0.7), width=0.01 * s)
    c.poly([(x - 0.011 * s, y + 0.008), (x + 0.011 * s, y + 0.008), (x, y + 0.05 * s)], fill=FLAME_CORE)


def candle(c, x, y, h, lit=True, r=0.03, seed=0):
    rnd = random.Random(seed)
    top = y + h
    c.rect(x - r, y, x + r, top, fill=CREAM, outline=OUTLINE, width=0.012)
    c.line([(x - r + 0.007, y + 0.01), (x - r + 0.007, top - 0.01)], fill=shade(CREAM, 1.08), width=0.007)
    c.ellipse(x, top, r, r * 0.45, fill=shade(CREAM, 1.08), outline=OUTLINE, width=0.012)
    for _ in range(2):
        wx = x + rnd.choice((-1, 1)) * r * 0.75
        wy = top - rnd.uniform(0.02, max(0.03, h * 0.5))
        c.line([(wx, top - 0.01), (wx, wy)], fill=shade(CREAM, 1.05), width=0.012)
    if lit:
        flame(c, x, top + 0.008, 0.85)
    else:
        c.line([(x, top), (x, top + 0.022)], fill=OUTLINE, width=0.01)


def grave_light(c, x, y, s=1.0, lit=True, col=None):
    """Grablicht: rotes Glas mit Messingdeckel, innen Flamme (leuchtet durch)."""
    col = col or RED_LAMP
    if lit:
        c.glow(x, y + 0.08 * s, 0.38 * s, hexc("#ff7a5a"), 0.4)
    c.rect(x - 0.045 * s, y, x + 0.045 * s, y + 0.12 * s, fill=alpha(col, 235), outline=OUTLINE, width=0.012 * s)
    if lit:
        c.ellipse(x, y + 0.06 * s, 0.022 * s, 0.035 * s, fill=hexc("#ffd080"))
        c.ellipse(x, y + 0.06 * s, 0.01 * s, 0.018 * s, fill=FLAME_CORE)
    c.line([(x - 0.03 * s, y + 0.02 * s), (x - 0.03 * s, y + 0.1 * s)], fill=alpha((255, 255, 255, 255), 90), width=0.008 * s)
    c.poly([(x - 0.052 * s, y + 0.12 * s), (x + 0.052 * s, y + 0.12 * s), (x + 0.03 * s, y + 0.155 * s), (x - 0.03 * s, y + 0.155 * s)],
           fill=BRASS, outline=OUTLINE, width=0.01 * s)
    c.ellipse(x, y + 0.165 * s, 0.014 * s, 0.01 * s, fill=BRASS_D)


def moss(c, x, y, r, seed=0, col=None):
    rnd = random.Random(seed)
    col = col or MOSS
    for _ in range(5):
        c.ellipse(x + rnd.uniform(-r, r), y + rnd.uniform(-r * 0.5, r * 0.5), r * rnd.uniform(0.3, 0.6), r * rnd.uniform(0.2, 0.4),
                  fill=alpha(col, 175))
    for _ in range(4):
        c.ellipse(x + rnd.uniform(-r, r), y + rnd.uniform(-r * 0.4, r * 0.4), r * 0.12, r * 0.1, fill=alpha(shade(col, 1.3), 200))


def lichen(c, x0, y0, x1, y1, n, seed=0):
    rnd = random.Random(seed)
    for _ in range(n):
        c.ellipse(rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(0.008, 0.016), rnd.uniform(0.006, 0.012), fill=alpha(LICHEN, 150))


def ring(c, cx, cy, r_out, r_in, col, n=40):
    """Kreisring als Flaeche (innen durchsichtig) mit Umriss aussen und innen."""
    for k in range(n):
        a0, a1 = k / n * math.tau, (k + 1) / n * math.tau
        c.poly([(cx + r_out * math.cos(a0), cy + r_out * math.sin(a0)), (cx + r_out * math.cos(a1), cy + r_out * math.sin(a1)),
                (cx + r_in * math.cos(a1), cy + r_in * math.sin(a1)), (cx + r_in * math.cos(a0), cy + r_in * math.sin(a0))], fill=col)
    c.line([(cx + r_out * math.cos(k / n * math.tau), cy + r_out * math.sin(k / n * math.tau)) for k in range(n + 1)], fill=OUTLINE, width=0.02)
    c.line([(cx + r_in * math.cos(k / n * math.tau), cy + r_in * math.sin(k / n * math.tau)) for k in range(n + 1)], fill=OUTLINE, width=0.016)


def crack(c, pts, seed=0, col=None, w=0.012):
    c.line(HD.wobble(pts, amp=0.01, seed=seed, step=0.035), fill=col or alpha(OUTLINE, 200), width=w)


def grass_tufts(c, x0, x1, y, rnd, n=6, h=0.08, cols=None):
    cols = cols or [GRASS, GRASS_L, shade(GRASS, 0.8)]
    for _ in range(n):
        for seg in HD.tuft(rnd.uniform(x0, x1), y + rnd.uniform(-0.02, 0.02), rnd, n=rnd.randint(3, 5), h=h):
            c.line(seg, fill=rnd.choice(cols), width=0.012)


def bouquet(c, x, y, rnd, dead=False, s=1.0):
    """Strauss im Becher oder lose: Stiele, Blueten (frisch oder welk)."""
    cols = DEAD_FLOWER if dead else FLOWER
    for k in range(5):
        a = math.radians(rnd.uniform(-35, 35))
        ln = rnd.uniform(0.1, 0.18) * s
        ex, ey = x + math.sin(a) * ln, y + math.cos(a) * ln
        c.line([(x, y), (ex, ey)], fill=hexc("#4a6a3a") if not dead else hexc("#5a5040"), width=0.01 * s)
        col = rnd.choice(cols)
        c.ellipse(ex, ey, 0.03 * s, 0.026 * s, fill=col, outline=OUTLINE, width=0.008 * s)
        c.ellipse(ex - 0.008 * s, ey + 0.006 * s, 0.01 * s, 0.008 * s, fill=shade(col, 1.35))


def wreath(c, x, y, r, rnd):
    """Liegender Kranz (Aufsicht, gestaucht) aus Tannengruen mit Schleife."""
    for k in range(18):
        a = k / 18 * math.tau
        c.ellipse(x + r * math.cos(a), y + r * 0.55 * math.sin(a), r * 0.32, r * 0.22,
                  fill=hexc("#3c6a48") if k % 2 else hexc("#2e5a3c"), outline=alpha(OUTLINE, 160), width=0.006)
    c.ellipse(x, y, r * 0.55, r * 0.3, fill=alpha(EARTH, 255))
    for k in range(5):
        a = rnd.uniform(0, math.tau)
        c.ellipse(x + r * math.cos(a), y + r * 0.55 * math.sin(a), 0.018, 0.016, fill=hexc("#b02a34"))
    c.poly([(x - 0.02, y - r * 0.5), (x + 0.02, y - r * 0.5), (x + 0.06, y - r * 0.5 - 0.1), (x + 0.02, y - r * 0.5 - 0.09),
            (x, y - r * 0.5 - 0.03), (x - 0.02, y - r * 0.5 - 0.09), (x - 0.06, y - r * 0.5 - 0.1)], fill=hexc("#7a2030"), outline=OUTLINE, width=0.008)


# ------------------------------------------------------------------ Grabstein-Formen (Vorderansicht)

def _front_shape(form, x0, x1, yb, h):
    """Umriss der Vorderseite (Bildkoordinaten in Weltmetern: y nach oben, Hoehe schon mal K)."""
    w = x1 - x0
    cx = (x0 + x1) / 2
    yt = yb + h
    if form == "round":
        r = w / 2
        ys = yt - r * 0.8
        return [(x0, yb), (x1, yb), (x1, ys)] + [(cx + r * math.cos(t), ys + r * 0.8 * math.sin(t)) for t in [k * math.pi / 12 for k in range(13)]] + [(x0, ys)]
    if form == "gothic":
        ys = yt - w * 0.55
        pts = [(x0, yb), (x1, yb), (x1, ys)]
        for k in range(1, 8):
            t = k / 8
            pts.append((x1 - w / 2 * (1 - math.cos(t * math.pi / 2)) ** 0.9, ys + (yt - ys) * math.sin(t * math.pi / 2)))
        pts.append((cx, yt))
        for k in range(7, 0, -1):
            t = k / 8
            pts.append((x0 + w / 2 * (1 - math.cos(t * math.pi / 2)) ** 0.9, ys + (yt - ys) * math.sin(t * math.pi / 2)))
        pts.append((x0, ys))
        return pts
    if form == "shoulder":
        s = w * 0.18
        return [(x0, yb), (x1, yb), (x1, yt - s), (x1 - s, yt - s), (x1 - s, yt), (x0 + s, yt), (x0 + s, yt - s), (x0, yt - s)]
    if form == "scroll":
        r = w * 0.18
        pts = [(x0, yb), (x1, yb), (x1, yt - r * 1.4)]
        pts += [(x1 - r + r * math.cos(t), yt - r * 1.4 + r * 0.8 * math.sin(t)) for t in [k * math.pi / 6 for k in range(7)]]
        pts += [(cx + w * 0.22 * math.cos(t), yt - w * 0.12 + w * 0.12 * math.sin(t)) for t in [k * math.pi / 8 for k in range(9)]][::-1][::-1]
        pts += [(x0 + r + r * math.cos(t), yt - r * 1.4 + r * 0.8 * math.sin(t)) for t in [k * math.pi / 6 for k in range(7)]]
        pts.append((x0, yt - r * 1.4))
        return pts
    return [(x0, yb), (x1, yb), (x1, yt), (x0, yt)]                                   # flat


def slab(c, form, x0, x1, yb, h, d, col, seed=0, tilt=0.0):
    """Grabplatte mit Dicke d (Bild-Hoehe der Oberkante = d*K): Rueckseite versetzt hell (Mondlicht oben), Vorderseite
    in col mit Kantenlicht links, Schattenkante rechts. tilt kippt um die Fussmitte (rad, positiv = nach rechts)."""
    front = _front_shape(form, x0, x1, yb, h)
    cx = (x0 + x1) / 2
    if tilt:
        ca, sa = math.cos(tilt), math.sin(tilt)
        front = [(cx + (x - cx) * ca + (y - yb) * sa, yb - (x - cx) * sa + (y - yb) * ca) for x, y in front]
    back = [(x + d * 0.15, y + d * K) for x, y in front]
    c.poly(back, fill=shade(col, 1.2), outline=OUTLINE, width=OUT_W * 0.8)
    for i in range(len(front)):                                                       # Seitenflaechen zwischen vorne und hinten
        a, b = front[i], front[(i + 1) % len(front)]
        ab, bb = back[i], back[(i + 1) % len(front)]
        if b[1] > a[1] - 1e-6 and a[0] > cx - 1e-6:
            c.poly([a, b, bb, ab], fill=shade(col, 0.82))
    c.poly(front, fill=col, outline=OUTLINE, width=OUT_W * 0.8)
    xs = [p[0] for p in front]
    ys = [p[1] for p in front]
    c.line([(min(xs) + 0.025, yb + 0.03), (min(xs) + 0.025, max(ys) - 0.06)], fill=alpha(shade(col, 1.25), 200), width=0.014)   # Mondkante links
    c.line([(max(xs) - 0.02, yb + 0.03), (max(xs) - 0.02, max(ys) - 0.08)], fill=alpha(shade(col, 0.7), 170), width=0.014)
    c.rect(min(xs) + 0.02, yb + 0.005, max(xs) - 0.02, yb + 0.05, fill=alpha((0, 0, 0, 255), 60))                             # Erdkante
    return front


def inscription(c, x0, x1, y0, y1, col, rnd, cross=True, name=True):
    cx = (x0 + x1) / 2
    w = x1 - x0
    dark = alpha(shade(col, 0.55), 230)
    lite = alpha(shade(col, 1.18), 150)
    y = y1
    if cross:
        c.line([(cx, y - 0.02), (cx, y - 0.12)], fill=dark, width=0.016)
        c.line([(cx - 0.035, y - 0.05), (cx + 0.035, y - 0.05)], fill=dark, width=0.016)
        y -= 0.16
    if name:                                                                          # Name (breiter) und Daten (kurz)
        c.line([(cx - w * 0.3, y), (cx + w * 0.3, y)], fill=dark, width=0.018)
        c.line([(cx - w * 0.3, y + 0.008), (cx + w * 0.3, y + 0.008)], fill=lite, width=0.006)
        y -= 0.06
    for k in range(rnd.randint(1, 3)):
        if y < y0:
            break
        ln = w * rnd.uniform(0.25, 0.5)
        c.line([(cx - ln / 2, y), (cx + ln / 2, y)], fill=dark, width=0.01)
        y -= 0.045


def grave_bed(c, x0, x1, y_top, y_bot, style, rnd, seed=0):
    """Grabstelle vor dem Stein (Aufsicht). Der Huegel ist nur Licht und Schatten auf dem Untergrund (passt auf Rasen
    wie auf Wildgras): Schlagschatten rechts unten, Licht links oben, Grasring am Rand. Dazu Steineinfassung mit Kies,
    Efeubett oder Blumenbeet in einer Buchseinfassung."""
    cx, cy = (x0 + x1) / 2, (y_top + y_bot) / 2
    rx, ry = (x1 - x0) / 2, (y_top - y_bot) / 2
    if style == "mound":
        c.poly(HD.wobble_ellipse(cx + 0.05, cy - 0.06, rx * 0.98, ry * 0.98, amp=0.02, seed=seed), fill=(4, 8, 10, 95))
        c.poly(HD.wobble_ellipse(cx, cy, rx * 0.92, ry * 0.94, amp=0.02, seed=seed + 1), fill=(150, 190, 150, 26))
        c.poly(HD.wobble_ellipse(cx - rx * 0.18, cy + ry * 0.15, rx * 0.55, ry * 0.6, amp=0.02, seed=seed + 2), fill=(190, 220, 190, 34))
        c.poly(HD.wobble_ellipse(cx + rx * 0.05, cy - ry * 0.05, rx * 0.35, ry * 0.4, amp=0.03, seed=seed + 3), fill=(70, 56, 42, 120))   # Erde in der Mitte
        for k in range(14):                                                           # Grasring
            a = k / 14 * math.tau
            gx, gy = cx + rx * 0.88 * math.cos(a), cy + ry * 0.9 * math.sin(a)
            for seg in HD.tuft(gx, gy, rnd, n=3, h=0.07):
                c.line(seg, fill=rnd.choice([GRASS, GRASS_L, shade(GRASS, 0.75)]), width=0.012)
        for _ in range(3):
            c.ellipse(rnd.uniform(x0 + 0.12, x1 - 0.12), rnd.uniform(y_bot + 0.15, y_top - 0.15), 0.016, 0.012, fill=hexc("#8a8278"),
                      outline=alpha(OUTLINE, 160), width=0.005)
    elif style == "curb":
        c.rect(x0 + 0.03, y_bot - 0.03, x1 + 0.03, y_top - 0.03, fill=(0, 0, 0, 80))
        c.rect(x0, y_bot, x1, y_top, fill=shade(GRANITE, 0.92), outline=OUTLINE, width=0.02)
        c.rect(x0 + 0.06, y_bot + 0.06, x1 - 0.06, y_top - 0.05, fill=hexc("#6e6e74"), outline=alpha(OUTLINE, 200), width=0.012)
        for _ in range(55):
            gx, gy = rnd.uniform(x0 + 0.08, x1 - 0.08), rnd.uniform(y_bot + 0.08, y_top - 0.07)
            c.ellipse(gx, gy, 0.011, 0.008, fill=rnd.choice([hexc("#9a9aa0"), hexc("#7e7e86"), hexc("#b4b0a8"), hexc("#5e5e66")]))
        c.line([(x0 + 0.02, y_top - 0.015), (x1 - 0.02, y_top - 0.015)], fill=alpha(shade(GRANITE, 1.35), 220), width=0.012)
        c.line([(x0 + 0.015, y_bot + 0.02), (x0 + 0.015, y_top - 0.02)], fill=alpha(shade(GRANITE, 1.25), 200), width=0.01)
        grass_tufts(c, x0, x1, y_bot - 0.01, rnd, n=3, h=0.06)
    elif style == "flowers":                                                         # Beet in Buchseinfassung
        c.rect(x0 + 0.03, y_bot - 0.03, x1 + 0.03, y_top - 0.03, fill=(0, 0, 0, 80))
        c.rect(x0, y_bot, x1, y_top, fill=hexc("#2e5238"), outline=OUTLINE, width=0.018)
        for k in range(int((x1 - x0) / 0.07) + 1):                                    # Buchs-Kugeln am Rand
            for yy in (y_bot + 0.03, y_top - 0.03):
                c.ellipse(x0 + 0.035 + k * 0.07, yy, 0.04, 0.032, fill=hexc("#3e6a48"), outline=alpha(OUTLINE, 160), width=0.005)
        c.rect(x0 + 0.08, y_bot + 0.08, x1 - 0.08, y_top - 0.08, fill=EARTH_D)
        for _ in range(int((x1 - x0) * (y_top - y_bot) * 45)):
            fx, fy = rnd.uniform(x0 + 0.12, x1 - 0.12), rnd.uniform(y_bot + 0.12, y_top - 0.12)
            col = rnd.choice(FLOWER + DEAD_FLOWER)
            c.ellipse(fx, fy, 0.026, 0.022, fill=col, outline=alpha(OUTLINE, 180), width=0.005)
            c.ellipse(fx - 0.006, fy + 0.006, 0.009, 0.007, fill=shade(col, 1.4))
    else:                                                                             # Efeubett
        c.rect(x0 + 0.03, y_bot - 0.03, x1 + 0.03, y_top - 0.03, fill=(0, 0, 0, 80))
        c.rect(x0 + 0.03, y_bot, x1 - 0.03, y_top, fill=EARTH_D, outline=alpha(OUTLINE, 220), width=0.018)
        for _ in range(int((x1 - x0) * (y_top - y_bot) * 110)):
            lx, ly = rnd.uniform(x0 + 0.06, x1 - 0.06), rnd.uniform(y_bot + 0.05, y_top - 0.05)
            col = rnd.choice([hexc("#3e6a48"), hexc("#4e7c50"), hexc("#2e5a3a"), hexc("#5a8a58")])
            c.poly([(lx, ly + 0.03), (lx + 0.028, ly + 0.005), (lx + 0.016, ly - 0.025), (lx - 0.016, ly - 0.025), (lx - 0.028, ly + 0.005)],
                   fill=col, outline=alpha(OUTLINE, 150), width=0.005)
            c.line([(lx, ly + 0.025), (lx, ly - 0.015)], fill=alpha(shade(col, 0.7), 200), width=0.004)


# ------------------------------------------------------------------ Grabstein (Requisit) und Grab (Feld)

FORMS = ["round", "gothic", "shoulder", "celtic", "obelisk", "broken", "wood", "iron", "angel", "scroll", "flat", "round"]


def headstone(p, c, cx, yb, form, w, h, col, rnd, idx):
    """Grabstein mit Fuss bei (cx, yb): w Breite, h Hoehe (Meter). Rueckgabe: Oberkante (Bild-y)."""
    x0, x1 = cx - w / 2, cx + w / 2
    d = 0.14
    if form in ("round", "gothic", "shoulder", "scroll", "flat"):
        p.box(x0 - 0.05, yb, x1 + 0.05, yb + d + 0.06, 0, 0.08, shade(col, 1.08), shade(col, 0.9), w=OUT_W * 0.7)     # Sockel
        fb = yb + 0.08 * K
        hh = h * K
        front = slab(c, form, x0, x1, fb, hh, d, col, seed=idx)
        inscription(c, x0 + 0.05, x1 - 0.05, fb + hh * 0.2, fb + hh - (w * 0.3 if form in ("round", "gothic") else 0.06), col, rnd,
                    cross=form != "scroll", name=True)
        if form == "gothic":                                                          # Dreipass oben
            c.ellipse(cx, fb + hh - w * 0.32, 0.035, 0.035, outline=alpha(shade(col, 0.55), 230), width=0.012)
        if form == "scroll":                                                          # eingeritzter Lorbeer
            for s in (-1, 1):
                for k in range(4):
                    lx, ly = cx + s * (0.04 + k * 0.03), fb + hh * 0.75 - k * 0.025
                    c.ellipse(lx, ly, 0.018, 0.01, fill=alpha(shade(col, 0.62), 220))
        if rnd.random() < 0.55:
            moss(c, x0 + 0.06, fb + 0.06, 0.08, seed=idx)
        lichen(c, x0 + 0.04, fb + 0.05, x1 - 0.04, fb + hh - 0.05, 6, seed=idx)
        if rnd.random() < 0.4:
            crack(c, [(x1 - 0.06, fb + hh * 0.9), (x1 - 0.12, fb + hh * 0.55), (x1 - 0.08, fb + hh * 0.3)], seed=idx)
        return fb + hh + d * K
    if form == "broken":                                                              # abgebrochen, Oberteil liegt im Gras
        p.box(x0 - 0.05, yb, x1 + 0.05, yb + d + 0.06, 0, 0.08, shade(col, 1.08), shade(col, 0.9), w=OUT_W * 0.7)
        fb = yb + 0.08 * K
        hh = h * K * 0.55
        front = [(x0, fb), (x1, fb), (x1, fb + hh * 0.8), (x1 - w * 0.25, fb + hh), (cx, fb + hh * 0.7), (x0 + w * 0.2, fb + hh * 0.95), (x0, fb + hh * 0.85)]
        back = [(x + 0.02, y + d * K) for x, y in front]
        c.poly(back, fill=shade(col, 1.2), outline=OUTLINE, width=OUT_W * 0.8)
        c.poly(front, fill=col, outline=OUTLINE, width=OUT_W * 0.8)
        c.poly([(x1 - w * 0.25, fb + hh), (cx, fb + hh * 0.7), (x0 + w * 0.2, fb + hh * 0.95), (x0 + w * 0.2 + 0.02, fb + hh * 0.95 + d * K),
                (cx + 0.02, fb + hh * 0.7 + d * K), (x1 - w * 0.25 + 0.02, fb + hh + d * K)], fill=shade(col, 1.35), outline=OUTLINE, width=0.015)
        inscription(c, x0 + 0.05, x1 - 0.05, fb + 0.04, fb + hh * 0.6, col, rnd, cross=False, name=True)
        # Bruchstueck liegt rechts davor (gekippt)
        bx = x1 + 0.05
        piece = [(bx, yb - 0.05), (bx + 0.32, yb - 0.12), (bx + 0.36, yb + 0.02), (bx + 0.05, yb + 0.1)]
        c.poly([(x, y + 0.05) for x, y in piece], fill=shade(col, 1.18), outline=OUTLINE, width=0.03)
        c.poly(piece, fill=col, outline=OUTLINE, width=0.03)
        c.ellipse(bx + 0.18, yb - 0.02, 0.08, 0.025, fill=alpha(shade(col, 0.55), 200))
        moss(c, bx + 0.1, yb - 0.05, 0.06, seed=idx + 3)
        return fb + hh + d * K
    if form == "celtic":                                                              # Radkreuz auf Sockel
        p.box(x0 - 0.02, yb, x1 + 0.02, yb + 0.22, 0, 0.22, shade(col, 1.08), col, w=OUT_W * 0.8)
        fb = yb + 0.22 * K
        sw = w * 0.22
        top = fb + h * K * 0.8
        arm = fb + h * K * 0.55
        r = w * 0.36
        ring(c, cx + 0.02, arm + 0.035, r, r - 0.085, shade(col, 1.25))                                        # Ring (Oberkante)
        ring(c, cx, arm, r, r - 0.085, col)
        c.rect(cx - sw / 2 + 0.02, fb + 0.02, cx + sw / 2 + 0.02, top + 0.04, fill=shade(col, 1.2), outline=OUTLINE, width=OUT_W * 0.8)
        c.rect(cx - sw / 2, fb, cx + sw / 2, top, fill=col, outline=OUTLINE, width=OUT_W * 0.8)
        c.rect(cx - w / 2 + 0.02, arm - sw / 2 + 0.04, cx + w / 2 + 0.02, arm + sw / 2 + 0.04, fill=shade(col, 1.2), outline=OUTLINE, width=OUT_W * 0.8)
        c.rect(cx - w / 2, arm - sw / 2, cx + w / 2, arm + sw / 2, fill=col, outline=OUTLINE, width=OUT_W * 0.8)
        c.rect(cx - sw / 2 + 0.01, arm - sw / 2 + 0.01, cx + sw / 2 - 0.01, arm + sw / 2 - 0.01, fill=col)
        for k in range(4):                                                            # Knotenmuster
            c.line([(cx - sw * 0.25, fb + 0.08 + k * 0.09), (cx + sw * 0.25, fb + 0.12 + k * 0.09)], fill=alpha(shade(col, 0.6), 200), width=0.01)
        c.ellipse(cx, arm, sw * 0.28, sw * 0.28, outline=alpha(shade(col, 0.6), 220), width=0.012)
        for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):        # Ring vorn ueber den Armen
            c.line([(cx + (r - 0.03) * math.cos(a + d_), arm + (r - 0.03) * math.sin(a + d_)) for d_ in (-0.28, -0.14, 0, 0.14, 0.28)],
                   fill=col, width=0.05)
        c.line([(cx - sw / 2 + 0.02, fb + 0.03), (cx - sw / 2 + 0.02, top - 0.03)], fill=alpha(shade(col, 1.3), 200), width=0.012)
        moss(c, cx - w * 0.3, yb + 0.1, 0.08, seed=idx)
        return top + 0.06
    if form == "obelisk":                                                             # Stufensockel, schlanker Obelisk, Urne
        p.box(x0 - 0.06, yb, x1 + 0.06, yb + 0.3, 0, 0.14, shade(col, 1.1), shade(col, 0.92), w=OUT_W * 0.8)
        p.box(x0 + 0.04, yb + 0.05, x1 - 0.04, yb + 0.25, 0.14, 0.18, shade(col, 1.1), col, w=OUT_W * 0.8)
        fb = yb + 0.05 + 0.32 * K
        ob_w = w * 0.48
        top = fb + h * K * 1.15
        c.poly([(cx - ob_w / 2 + 0.03, fb + 0.06), (cx + ob_w / 2 + 0.03, fb + 0.06), (cx + ob_w * 0.3 + 0.03, top), (cx + 0.03, top + 0.09), (cx - ob_w * 0.3 + 0.03, top)],
               fill=shade(col, 1.2), outline=OUTLINE, width=OUT_W * 0.8)
        c.poly([(cx - ob_w / 2, fb), (cx + ob_w / 2, fb), (cx + ob_w * 0.3, top - 0.02), (cx, top + 0.06), (cx - ob_w * 0.3, top - 0.02)],
               fill=col, outline=OUTLINE, width=OUT_W * 0.8)
        c.line([(cx, fb + 0.02), (cx, top + 0.04)], fill=alpha(shade(col, 0.82), 200), width=0.01)
        c.line([(cx - ob_w / 2 + 0.03, fb + 0.03), (cx - ob_w * 0.3 + 0.02, top - 0.04)], fill=alpha(shade(col, 1.3), 200), width=0.012)
        c.rect(x0 + 0.08, yb + 0.05 + 0.16 * K, x1 - 0.08, yb + 0.05 + 0.28 * K, outline=alpha(shade(col, 0.6), 220), width=0.01)
        c.ellipse(cx, fb + h * K * 0.35, 0.045, 0.045, outline=alpha(shade(col, 0.55), 230), width=0.012)
        lichen(c, cx - ob_w / 3, fb, cx + ob_w / 3, top - 0.1, 8, seed=idx)
        return top + 0.1
    if form == "wood":                                                                # verwittertes Holzkreuz
        sw = 0.07
        top = yb + h * K * 1.05
        arm = yb + h * K * 0.72
        for dx, dy, f in ((0.02, 0.03, 1.15), (0, 0, 1.0)):
            c.rect(cx - sw / 2 + dx, yb + dy, cx + sw / 2 + dx, top + dy, fill=shade(WOOD, f), outline=OUTLINE, width=0.035)
            c.rect(cx - w * 0.36 + dx, arm - sw / 2 + dy, cx + w * 0.36 + dx, arm + sw / 2 + dy, fill=shade(WOOD, f), outline=OUTLINE, width=0.035)
        c.rect(cx - sw / 2 + 0.008, yb + 0.02, cx + sw / 2 - 0.008, top - 0.01, fill=WOOD)
        for k in range(3):
            c.line([(cx - 0.012 + k * 0.012, yb + 0.05), (cx - 0.012 + k * 0.012 + 0.004, top - 0.05)], fill=alpha(WOOD_D, 200), width=0.005)
        c.ellipse(cx, arm, 0.012, 0.012, fill=IRON_D)
        c.rect(cx - 0.07, arm - 0.12, cx + 0.07, arm - 0.06, fill=hexc("#c8bca0"), outline=OUTLINE, width=0.008)       # Namensschild
        c.line([(cx - 0.05, arm - 0.09), (cx + 0.05, arm - 0.09)], fill=hexc("#5a4a3a"), width=0.006)
        if rnd.random() < 0.6:                                                        # Kranz am Kreuz
            for k in range(12):
                a = k / 12 * math.tau
                c.ellipse(cx + 0.09 * math.cos(a), arm + 0.09 * math.sin(a), 0.03, 0.025, fill=hexc("#3c6a48") if k % 2 else hexc("#2e5a3c"))
            c.ellipse(cx, arm - 0.09, 0.02, 0.02, fill=hexc("#a02a34"))
        return top + 0.04
    if form == "iron":                                                                # Gusseisenkreuz mit Schnoerkeln
        top = yb + h * K * 1.0
        arm = yb + h * K * 0.7
        c.rect(cx - 0.12, yb - 0.02, cx + 0.12, yb + 0.06, fill=shade(GRANITE, 0.9), outline=OUTLINE, width=0.02)
        for col_, wd in ((OUTLINE, 0.06), (IRON, 0.034)):
            c.line([(cx, yb + 0.04), (cx, top)], fill=col_, width=wd)
            c.line([(cx - w * 0.36, arm), (cx + w * 0.36, arm)], fill=col_, width=wd)
        for sx in (-1, 1):
            for col_, wd in ((OUTLINE, 0.035), (IRON, 0.016)):
                c.line([(cx, arm - 0.04), (cx + sx * 0.06, arm - 0.08), (cx + sx * 0.1, arm - 0.04), (cx + sx * 0.08, arm)], fill=col_, width=wd)
                c.line([(cx + sx * w * 0.36, arm), (cx + sx * w * 0.36, arm + 0.04)], fill=col_, width=wd)
        for col_, wd in ((OUTLINE, 0.03), (IRON_L, 0.014)):
            c.ellipse(cx, arm, 0.05, 0.05, outline=col_, width=wd)
        c.poly([(cx, top + 0.06), (cx + 0.03, top), (cx, top - 0.02), (cx - 0.03, top)], fill=IRON, outline=OUTLINE, width=0.012)
        c.line([(cx - 0.012, yb + 0.06), (cx - 0.012, top - 0.04)], fill=alpha(IRON_L, 200), width=0.008)
        for _ in range(4):
            c.ellipse(cx + rnd.uniform(-0.01, 0.01), rnd.uniform(yb + 0.06, top), 0.01, 0.016, fill=alpha(RUST, 200))
        return top + 0.08
    if form == "angel":                                                               # trauernder Engel auf Sockel
        p.box(x0, yb, x1, yb + 0.3, 0, 0.32, shade(col, 1.08), col, w=OUT_W * 0.8)
        fb = yb + 0.32 * K
        c.rect(x0 + 0.06, yb + 0.08 * K, x1 - 0.06, yb + 0.26 * K, outline=alpha(shade(col, 0.6), 220), width=0.01)
        gy = fb + 0.03
        for sx in (-1, 1):                                                            # Fluegel, gesenkt
            c.poly([(cx + sx * 0.05, gy + 0.3), (cx + sx * 0.26, gy + 0.42), (cx + sx * 0.3, gy + 0.3), (cx + sx * 0.22, gy + 0.08), (cx + sx * 0.1, gy + 0.02)],
                   fill=shade(col, 1.12), outline=OUTLINE, width=0.03)
            for k in range(3):
                c.line([(cx + sx * 0.12, gy + 0.1 + k * 0.08), (cx + sx * 0.25, gy + 0.18 + k * 0.07)], fill=alpha(shade(col, 0.75), 200), width=0.008)
        c.poly([(cx - 0.13, gy), (cx + 0.13, gy), (cx + 0.08, gy + 0.34), (cx - 0.08, gy + 0.34)], fill=col, outline=OUTLINE, width=0.03)   # Gewand
        for k in range(3):
            c.line([(cx - 0.06 + k * 0.06, gy + 0.02), (cx - 0.04 + k * 0.04, gy + 0.3)], fill=alpha(shade(col, 0.72), 200), width=0.008)
        c.ellipse(cx, gy + 0.39, 0.065, 0.06, fill=shade(col, 1.08), outline=OUTLINE, width=0.03)                       # gesenkter Kopf
        c.ellipse(cx + 0.015, gy + 0.37, 0.035, 0.025, fill=shade(col, 0.6))
        c.poly([(cx - 0.05, gy + 0.22), (cx + 0.03, gy + 0.3), (cx + 0.05, gy + 0.26), (cx - 0.02, gy + 0.18)], fill=shade(col, 1.15), outline=OUTLINE, width=0.015)  # Haende
        lichen(c, cx - 0.1, gy, cx + 0.1, gy + 0.3, 5, seed=idx)
        c.line([(cx + 0.02, gy + 0.35), (cx + 0.025, gy + 0.3)], fill=alpha(hexc("#1a1e2a"), 160), width=0.008)         # Traenenspur
        return gy + 0.46
    return yb


def _feldgrab(p, c, x0, y0, x1, y1, idx, rnd, form=None, bed=True):
    """Grab im Feld: Stein am Nordende (y1), davor die Grabstelle bis y0. Grundflaeche = ganze Grabstelle."""
    cx = (x0 + x1) / 2
    form = form or FORMS[idx % len(FORMS)]
    col = shade(STONES[(idx * 7 + 3) % len(STONES)], rnd.uniform(0.9, 1.05))
    w = min(x1 - x0 - 0.08, rnd.uniform(0.58, 0.76))
    h = {"obelisk": 1.05, "celtic": 1.25, "angel": 1.0, "wood": 0.95, "iron": 0.95, "flat": 0.55, "broken": 1.2}.get(form, rnd.uniform(0.85, 1.1))
    stone_y = y1 - 0.25
    if bed:
        style = ("mound", "curb", "ivy", "mound", "flowers", "curb")[(idx * 5 + 1) % 6]
        grave_bed(c, x0 + 0.04, x1 - 0.04, stone_y - 0.04, y0 + 0.04, style, rnd, seed=idx)
    top = headstone(p, c, cx, stone_y, form, w, h, col, rnd, idx)
    if bed:                                                                           # Grabschmuck auf dem Bett
        u = (idx * 13) % 5
        my = stone_y - 0.35
        if u == 0:
            grave_light(c, cx - 0.12, my, lit=rnd.random() < 0.7)
            bouquet(c, cx + 0.12, my - 0.02, rnd, dead=rnd.random() < 0.5)
        elif u == 1 and style != "flowers":
            wreath(c, cx, (stone_y + y0) / 2, 0.16, rnd)
        elif u == 2:
            grave_light(c, cx, my, lit=True)
        elif u == 3:
            bouquet(c, cx - 0.08, my, rnd, dead=True)
            for _ in range(3):
                A.leaf_ = None
        else:
            for _ in range(6):                                                        # Laub auf dem Grab
                lx, ly = rnd.uniform(x0 + 0.1, x1 - 0.1), rnd.uniform(y0 + 0.1, stone_y - 0.1)
                a = rnd.uniform(0, math.pi)
                col_ = rnd.choice(LEAF)
                c.poly([(lx + 0.05 * math.cos(a), ly + 0.05 * math.sin(a)), (lx - 0.02 * math.sin(a), ly + 0.02 * math.cos(a)),
                        (lx - 0.05 * math.cos(a), ly - 0.05 * math.sin(a)), (lx + 0.02 * math.sin(a), ly - 0.02 * math.cos(a))],
                       fill=col_, outline=alpha(OUTLINE, 160), width=0.006)
    grass_tufts(c, cx - w / 2 - 0.08, cx + w / 2 + 0.08, stone_y, rnd, n=5, h=0.08)
    return top


def _grabstein(p, c, x0, y0, x1, y1, idx, rnd):
    """Requisit (Alte Graeber): Grundflaeche = Stein selbst, das Bett malt der Boden."""
    cx = (x0 + x1) / 2
    form = ["round", "celtic", "gothic", "angel", "shoulder", "obelisk", "scroll", "broken"][idx % 8]
    col = shade(STONES[(idx * 5 + 1) % len(STONES)], 1.0)
    w = (x1 - x0) * (0.8 if form not in ("celtic",) else 0.9)
    h = {"obelisk": 1.0, "celtic": 1.15, "angel": 0.9, "broken": 1.05}.get(form, 0.95)
    headstone(p, c, cx, y0 + 0.02, form, w, h, col, rnd, idx)
    grass_tufts(c, x0, x1, y0 + 0.02, rnd, n=6, h=0.09)
    if idx % 3 == 0:
        grave_light(c, x0 + 0.08, y0 - 0.06, lit=True)


# ------------------------------------------------------------------ Baeume (Boden der Grabfelder und Wald)

def tree_dead(c, x, y, h, rnd, seed=0, ravens=0):
    """Kahler Baum: Stamm mit Wurzeln, verzweigte Aeste (rekursiv), Mondkante, optional Raben."""
    def branch(px, py, ang, ln, wd, depth):
        if depth == 0 or ln < 0.06:
            return
        ex = px + math.cos(ang) * ln
        ey = py + math.sin(ang) * ln
        pts = HD.wobble([(px, py), (ex, ey)], amp=ln * 0.06, seed=seed + depth * 13 + int(ln * 100), step=max(0.03, ln / 5))
        c.line(pts, fill=OUTLINE, width=wd + 0.03)
        c.line(pts, fill=BARK, width=wd)
        if wd > 0.04:
            c.line([(q[0] - wd * 0.25, q[1]) for q in pts], fill=alpha(BARK_L, 200), width=wd * 0.3)
        n = 2 if depth > 1 else rnd.randint(1, 3)
        for k in range(n):
            na = ang + rnd.uniform(0.25, 0.7) * (1 if k % 2 else -1)
            branch(ex, ey, na, ln * rnd.uniform(0.55, 0.75), wd * 0.62, depth - 1)
        if depth <= 2 and rnd.random() < 0.6:
            branch(ex, ey, ang + rnd.uniform(-0.2, 0.2), ln * 0.6, wd * 0.6, depth - 1)

    c.soft_shadow([(x - 0.3, y - 0.12), (x + 0.5, y - 0.18), (x + 0.6, y + 0.05), (x - 0.2, y + 0.1)], 90, 0.08)
    for a, ln in ((math.pi + 0.3, 0.35), (-0.25, 0.32), (math.pi + 1.2, 0.2), (-1.1, 0.22)):                          # Wurzeln
        pts = HD.wobble([(x, y + 0.05), (x + math.cos(a) * ln, y + math.sin(a) * ln * 0.4)], amp=0.02, seed=seed + int(a * 10), step=0.05)
        c.line(pts, fill=OUTLINE, width=0.1)
        c.line(pts, fill=BARK_D, width=0.06)
    tw = 0.22 * h / 2.5
    trunk = HD.wobble([(x, y), (x + 0.04, y + h * 0.35), (x - 0.03, y + h * 0.55)], amp=0.02, seed=seed, step=0.08)
    c.line(trunk, fill=OUTLINE, width=tw + 0.05)
    c.line(trunk, fill=BARK, width=tw)
    c.line([(q[0] - tw * 0.3, q[1]) for q in trunk], fill=alpha(BARK_L, 210), width=tw * 0.25)
    for k in range(4):                                                                # Rinde
        yy = y + 0.1 + k * h * 0.11
        c.line([(x - tw * 0.3, yy), (x + tw * 0.2, yy + 0.05)], fill=alpha(BARK_D, 220), width=0.012)
    c.ellipse(x + 0.02, y + h * 0.25, tw * 0.22, tw * 0.3, fill=hexc("#1a1612"), outline=alpha(BARK_D, 255), width=0.012)   # Astloch
    ox, oy = trunk[-1]
    for a, f in ((math.pi / 2 + 0.5, 1.0), (math.pi / 2 - 0.55, 0.95), (math.pi / 2 + 0.05, 0.8), (math.pi / 2 + 1.1, 0.7), (math.pi / 2 - 1.15, 0.7)):
        branch(ox, oy, a + rnd.uniform(-0.1, 0.1), h * 0.28 * f, tw * 0.62, 4)
    for k in range(ravens):
        rx, ry = x + rnd.uniform(-h * 0.25, h * 0.25), y + h * rnd.uniform(0.6, 0.85)
        raven(c, rx, ry, rnd.choice((-1, 1)), 0.9)


def raven(c, x, y, facing=1, s=1.0, flying=False):
    """Rabe (sitzend): Koerper, Kopf mit Schnabel, Schwanz, Glanz, gelbes Auge."""
    f = facing
    body = [(x - 0.09 * s * f, y), (x + 0.06 * s * f, y + 0.01 * s), (x + 0.09 * s * f, y + 0.07 * s), (x + 0.02 * s * f, y + 0.11 * s), (x - 0.08 * s * f, y + 0.07 * s)]
    c.poly([(x - 0.08 * s * f, y + 0.02 * s), (x - 0.2 * s * f, y - 0.04 * s), (x - 0.17 * s * f, y + 0.0 * s), (x - 0.06 * s * f, y + 0.05 * s)],
           fill=hexc("#1c1c24"), outline=OUTLINE, width=0.012 * s)
    c.poly(body, fill=hexc("#22222c"), outline=OUTLINE, width=0.014 * s)
    c.ellipse(x + 0.08 * s * f, y + 0.12 * s, 0.045 * s, 0.04 * s, fill=hexc("#24242e"), outline=OUTLINE, width=0.012 * s)
    c.poly([(x + 0.115 * s * f, y + 0.13 * s), (x + 0.19 * s * f, y + 0.11 * s), (x + 0.115 * s * f, y + 0.105 * s)], fill=hexc("#34343c"), outline=OUTLINE, width=0.008 * s)
    c.ellipse(x + 0.09 * s * f, y + 0.13 * s, 0.01 * s, 0.01 * s, fill=hexc("#e8d060"))
    c.line([(x - 0.04 * s * f, y + 0.08 * s), (x + 0.04 * s * f, y + 0.095 * s)], fill=alpha(hexc("#6a7aa8"), 180), width=0.012 * s)   # Glanz
    c.line([(x, y), (x - 0.01 * s * f, y - 0.04 * s)], fill=hexc("#2a2a30"), width=0.01 * s)
    c.line([(x + 0.03 * s * f, y), (x + 0.03 * s * f, y - 0.04 * s)], fill=hexc("#2a2a30"), width=0.01 * s)


def tree_yew(c, x, y, h, rnd, seed=0):
    """Eibe: dunkle, unregelmaessige Saeulenkrone. Silhouette aus vielen Laubbuescheln (ein Umriss aussen),
    innen Schattenpartien rechts unten, Mondlicht-Bueschel links oben, rote Arillus-Beeren, kurzer roter Stamm."""
    c.soft_shadow([(x - 0.35, y - 0.15), (x + 0.7, y - 0.22), (x + 0.8, y + 0.2), (x - 0.25, y + 0.2)], 110, 0.1)
    c.poly([(x - 0.13, y - 0.02), (x + 0.11, y - 0.02), (x + 0.07, y + 0.5), (x - 0.09, y + 0.5)], fill=hexc("#4a2e26"), outline=OUTLINE, width=0.03)
    c.line([(x - 0.07, y + 0.02), (x - 0.05, y + 0.45)], fill=hexc("#6a4436"), width=0.014)
    for a_, ln in ((math.pi + 0.35, 0.16), (-0.3, 0.14)):                            # Wurzelansatz
        c.line([(x, y + 0.02), (x + math.cos(a_) * ln, y + math.sin(a_) * ln * 0.3)], fill=OUTLINE, width=0.06)
        c.line([(x, y + 0.02), (x + math.cos(a_) * ln, y + math.sin(a_) * ln * 0.3)], fill=hexc("#4a2e26"), width=0.035)
    tufts = []
    n = int(h * 20)
    lean = rnd.uniform(-0.06, 0.06)
    for _ in range(n):
        t = rnd.random() ** 0.8
        width = (0.5 * math.sin(math.pi * (0.25 + 0.75 * t)) ** 0.7 * (1 - t * 0.55) + 0.05) * h / 2.8
        yy = y + 0.38 + t * (h - 0.5)
        bx = x + lean * t + rnd.uniform(-1, 1) * width * 0.7
        r = rnd.uniform(0.2, 0.3) * (1 - t * 0.45)
        tufts.append((bx, yy, r))
    def tuft_poly(bx, by, r, sd):
        pts = []
        for k in range(14):                                                           # Bueschel mit leicht gewelltem Rand
            a = k / 14 * math.tau
            rr = r * (1.0 if k % 2 == 0 else 0.9) * random.Random(sd + k).uniform(0.94, 1.04)
            pts.append((bx + rr * math.cos(a), by + rr * 0.85 * math.sin(a)))
        return pts
    for i, (bx, by, r) in enumerate(tufts):                                           # Umriss (alle Bueschel dick)
        c.poly(tuft_poly(bx, by, r, seed + i), fill=OUTLINE, outline=OUTLINE, width=0.05)
    for i, (bx, by, r) in enumerate(tufts):                                           # Grundton
        c.poly(tuft_poly(bx, by, r, seed + i), fill=YEW)
    for i, (bx, by, r) in enumerate(sorted(tufts, key=lambda t: -t[1])):              # Schatten rechts unten, Licht links oben
        side = (bx - x) / (h * 0.25) - (by - y) / h
        if side > 0.2:
            c.poly(tuft_poly(bx + r * 0.15, by - r * 0.12, r * 0.7, seed + 300 + i), fill=YEW_D)
        elif side < -0.55:
            c.poly(tuft_poly(bx - r * 0.15, by + r * 0.15, r * 0.55, seed + 600 + i), fill=YEW_L)
        for k in range(3):                                                            # Nadelstriche
            a = rnd.uniform(0.6, 2.5)
            c.line([(bx - 0.04, by), (bx - 0.04 + math.cos(a) * r * 0.6, by + math.sin(a) * r * 0.5)], fill=alpha(YEW_D if side > -0.3 else YEW_L, 170), width=0.01)
    for i, (bx, by, r) in enumerate(tufts):
        if i % 9 == 0:
            c.ellipse(bx + rnd.uniform(-r * 0.4, r * 0.4), by + rnd.uniform(-r * 0.3, r * 0.3), 0.024, 0.024, fill=hexc("#d03040"), outline=OUTLINE, width=0.008)
    top = max(tufts, key=lambda t: t[1])
    c.ellipse(top[0] - 0.05, top[1] + 0.05, 0.08, 0.05, fill=alpha(MOON, 80))


def bush(c, x, y, r, rnd, seed=0, col=None):
    col = col or hexc("#2e4a3a")
    c.soft_shadow([(x - r, y - r * 0.4), (x + r * 1.3, y - r * 0.5), (x + r * 1.3, y + r * 0.2), (x - r, y + r * 0.2)], 90, 0.08)
    blobs = [(x + rnd.uniform(-r * 0.6, r * 0.6), y + rnd.uniform(0, r * 0.6), r * rnd.uniform(0.45, 0.65)) for _ in range(6)]
    blobs.sort(key=lambda b: -b[1])
    for i, (bx, by, rr) in enumerate(blobs):
        c.poly(HD.wobble_ellipse(bx, by, rr, rr * 0.85, amp=0.015, seed=seed + i), fill=col, outline=OUTLINE, width=0.03)
        c.poly(HD.wobble_ellipse(bx - rr * 0.25, by + rr * 0.25, rr * 0.45, rr * 0.3, amp=0.01, seed=seed + 20 + i), fill=shade(col, 1.3))


# ------------------------------------------------------------------ Registrierung

PROP_H = {"grabstein": 1.2, "feldgrab": 1.2, "baum_tot": 3.6, "eibe": 3.0, "busch": 0.8}
PROP_PAD = {"baum_tot": 2.2, "eibe": 0.9, "feldgrab": 0.45, "grabstein": 0.45}
VARIANTS = {}
_KIND_FN = {}


def kind(name, h, pad=0.3, variants=()):
    def deco(fn):
        _KIND_FN[name] = fn
        PROP_H[name] = h
        PROP_PAD[name] = pad
        if variants:
            VARIANTS[name] = tuple(variants)
        return fn
    return deco


_KIND_FN.update({
    "grabstein": _grabstein,
    "feldgrab": _feldgrab,
    "baum_tot": lambda p, c, x0, y0, x1, y1, idx, rnd: tree_dead(c, (x0 + x1) / 2, (y0 + y1) / 2, 3.4, rnd, seed=idx, ravens=idx % 3),
    "eibe": lambda p, c, x0, y0, x1, y1, idx, rnd: tree_yew(c, (x0 + x1) / 2, (y0 + y1) / 2, 2.8, rnd, seed=idx),
    "busch": lambda p, c, x0, y0, x1, y1, idx, rnd: bush(c, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, rnd, seed=idx),
})
NO_SHADOW = {"baum_tot", "eibe", "busch", "feldgrab"}

import graveyard_art2  # noqa: F401,E402  (Einrichtung: Kapelle, Sargkammer, Brunnenhaus, Gruft, Leichenhalle)
import graveyard_art3  # noqa: F401,E402  (Krematorium, Verwaltung, Torhaus, Waechterhaus, im Freien)


def draw(kind_, shape, idx, ppm, ctx=None, variant=None, **kw):
    """Ein Objekt als Sprite: (RGBA-Bild, welt_x_links, welt_y_unten, standlinie_y)."""
    x0, y0, x1, y1 = A.shape_bounds(shape)
    h = PROP_H[kind_]
    p = Prop(x0, y0, x1, y1, h, ppm, pad=PROP_PAD.get(kind_, 0.3))
    c = p.c
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rnd = random.Random(idx * 131 + 7)
    if kind_ not in NO_SHADOW:
        if shape[0] in ("circle", "ellipse"):
            rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
            c.soft_shadow([(cx + 0.08 + rx * math.cos(t * math.pi / 12), cy - 0.08 + ry * math.sin(t * math.pi / 12)) for t in range(24)], 100, 0.1)
        else:
            c.soft_shadow([(x0 + 0.08, y0 - 0.1), (x1 + 0.12, y0 - 0.1), (x1 + 0.12, y1), (x0 + 0.08, y1)], 95, 0.09)
    fn = _KIND_FN[kind_]
    if variant is None:
        fn(p, c, x0, y0, x1, y1, idx, rnd, **kw)
    else:
        fn(p, c, x0, y0, x1, y1, idx, rnd, variant=variant, **kw)
    return c.finish(), c.x0, c.y0, p.base_y


if __name__ == "__main__":
    # Musterblatt: python graveyard_art.py out.png [arten...]
    out = sys.argv[1] if len(sys.argv) > 1 else "art.png"
    kinds = sys.argv[2:] or ["feldgrab"]
    tiles = []
    for kd in kinds:
        n = 12 if kd in ("feldgrab", "grabstein") else 3
        for i in range(n):
            if kd == "feldgrab":
                shp = ("rect", 0, 0, 0.9, 1.9)
            elif kd == "grabstein":
                shp = ("rect", 0, 0, 1.0, 0.4)
            else:
                shp = ("rect", 0, 0, 1.0, 1.0)
            im, *_ = draw(kd, shp, i, 160)
            tiles.append(im)
    W = sum(t.width for t in tiles[:12]) + 12 * 8
    rows = [tiles[i:i + 12] for i in range(0, len(tiles), 12)]
    H = sum(max(t.height for t in r) + 8 for r in rows)
    sheet = Image.new("RGBA", (max(W, 400), H), (70, 92, 80, 255))
    y = 0
    for r in rows:
        x = 0
        for t in r:
            sheet.alpha_composite(t, (x, y))
            x += t.width + 8
        y += max(t.height for t in r) + 8
    sheet.save(out)
    print(sheet.size)
