# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_consoles.py - Task-Bloecke (Konsolen-Sprites) und Vents von Hollowmere Manor.
#
# Wie park_consoles.py (Unknown's Atlas) auf dem Baukasten von wald_consoles.py: gleiche Montage je
# Wandseite (N/S/E/W/frei), eigene Farben je Raum (Haus: dunkles Nussholz mit Messing/Bordeaux, Filmcrew:
# mattschwarz mit Gaffer-Gelb, Garten/Gruft: Stein und Eisen). Eigene Motive fuer den Notfallknopf
# (Regieklappe auf einem Beistelltisch) und die Garten-Vents (gusseiserner Gully); Vents im Haus sind die
# Bodenluke aus wald_vents.py.
#
# SCHNITTSTELLE (gen_villa.render_consoles):
#   render_all(ppm, brief) -> {(Variante, Schluessel): (PIL.Image RGBA, Anker-x px, Anker-y px)}
#   brief = Liste aus _villa/console_brief.json: {variant, key, x, y, room, wall}; wall in Plan-Richtung
#   (N = Nordwand), also dieselbe Bedeutung wie im Wald.

import math
import os
import sys

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)

import wald_consoles as WC                                   # noqa: E402
import wald_vents as WV                                      # noqa: E402
import villa_console_art as VCA                              # noqa: E402
from museum_art import Canvas, K, OUTLINE, alpha, hexc, lift, shade  # noqa: E402

WALNUT = hexc("#6e4a30")
WALNUT_L = hexc("#8e6440")
BRASS = lift("#9c7c3c", 1.25)
BORDEAUX = hexc("#7a2a36")
GEAR = hexc("#2c2e34")             # mattschwarzes Filmgeraet
GAFFER = hexc("#e2bc3a")
STONE = hexc("#7c8088")
IRON = hexc("#3c3e46")
MOSS = hexc("#4f6a3c")

TINT = {
    "kitchen": (shade(WALNUT, 1.05), hexc("#b0b4b8")), "laundry": (hexc("#8a8e92"), hexc("#5a7a9a")),
    "seance": (WALNUT, BORDEAUX), "radio": (GEAR, GAFFER), "boxroom": (WALNUT_L, BRASS),
    "observatory": (WALNUT, BRASS), "boiler": (hexc("#5c6268"), hexc("#c8742c")), "westhall": (WALNUT, BRASS),
    "library": (WALNUT, BORDEAUX), "chapel": (STONE, BRASS), "hall": (WALNUT, BRASS),
    "booth": (GEAR, GAFFER), "vestibule": (WALNUT, BRASS), "makeup": (hexc("#d8d0c4"), BORDEAUX),
    "gallery": (WALNUT, BRASS), "trophy": (WALNUT, hexc("#5a6a3a")), "fireplace": (WALNUT, hexc("#c8742c")),
    "study": (WALNUT, BRASS),
    "terrace": (STONE, IRON), "driveway": (GEAR, GAFFER), "crewcamp": (GEAR, GAFFER),
    "greenhouse": (hexc("#4f6a52"), hexc("#c8d0c0")), "fountain": (STONE, MOSS), "graveyard": (STONE, IRON),
    "crypt": (STONE, BRASS), "-": (WALNUT, BRASS),
}
OUTDOOR = {"terrace", "driveway", "crewcamp", "fountain", "graveyard"}


def slate_table(ppm):
    """Notfallknopf: runder Beistelltisch, darauf die Regieklappe und ein roter Pilzknopf."""
    b = WC.Block(-0.45, -0.3, 0.45, 0.3, 1.25 * K, ppm)
    c = b.c
    b.shadow(-0.38, -0.22, 0.38, 0.22)
    b.cyl(0.0, -0.02, 0.07, 0.0, 0.62, shade(WALNUT, 0.8), WALNUT, ry=0.04)                  # Saeule
    b.cyl(0.0, -0.05, 0.4, 0.62, 0.06, WALNUT_L, WALNUT, ry=0.24)                              # Tischplatte
    top = 0.68 * K
    # Klappe: Schiefertafel mit Schrift, Klappstange schraeg offen (schwarz-weiss gestreift)
    c.poly([(-0.3, -0.12 + top), (0.02, -0.12 + top), (0.02, 0.1 + top), (-0.3, 0.1 + top)], fill=hexc("#20222a"), outline=OUTLINE, width=0.02)
    for k in range(3):
        c.line([(-0.27, -0.06 + top + k * 0.05), (-0.01, -0.06 + top + k * 0.05)], fill=hexc("#d8d8d8"), width=0.008)
    stick = [(-0.31, 0.11 + top), (0.03, 0.11 + top), (0.05, 0.2 + top), (-0.29, 0.2 + top)]
    c.poly(stick, fill=hexc("#f0f0f0"), outline=OUTLINE, width=0.018)
    for k in range(4):
        x = -0.28 + k * 0.08
        c.poly([(x, 0.115 + top), (x + 0.04, 0.115 + top), (x + 0.055, 0.195 + top), (x + 0.015, 0.195 + top)], fill=hexc("#18181c"))
    # roter Knopf unter Glashaube
    c.ellipse(0.2, 0.0 + top, 0.11, 0.07, fill=hexc("#3a3a40"), outline=OUTLINE, width=0.018)
    c.ellipse(0.2, 0.05 + top, 0.075, 0.05, fill=hexc("#d83a3a"), outline=OUTLINE, width=0.015)
    c.ellipse(0.18, 0.07 + top, 0.025, 0.015, fill=hexc("#ff9a9a"))
    c.glow(0.2, 0.06 + top, 0.18, hexc("#ff4a4a"), 0.3)
    return b.result()


HERD_IRON = hexc("#4e5058")        # Gusseisen wie villa_art._herd (Beine, Schaelchen)
BUN = hexc("#d8a35a")
BUN_D = shade(BUN, 0.78)
PATTY = hexc("#5a3420")
PATTY_RAW = hexc("#8a3a34")
LETTUCE = hexc("#6fae3c")
TOMATO = hexc("#d8392c")
CHEESE = hexc("#f0c43a")
PAPER = hexc("#e8dcb4")


def burger_station(ppm):
    """Make Burger (Kueche): niedriger Anrichtetisch frei vor dem Herd. Gusseisernes Gestell mit Ablage
    (Mehlsack, Brotkiste), Holzplatte mit Stahlkante; darauf Schneidbrett mit halb gebautem Burger und
    Wender, Teller mit rohen Patties, Schaelchen fuer Salat, Tomaten und Kaese, Broetchenkorb, zwei
    Saucenflaschen und ein Bestellzettel auf dem Spiess. Hoehe 0,93 m, damit der Herd dahinter sichtbar
    bleibt."""
    body, trim = TINT["kitchen"]
    wood = shade(body, 1.2)
    wood_l = shade(body, 1.45)
    b = WC.Block(-0.48, -0.28, 0.48, 0.28, 1.5 * K, ppm)
    c = b.c
    x0, y0, x1, y1 = -0.45, -0.25, 0.45, 0.25
    H = 0.85                                                     # Gestellhoehe, Platte 0,08 obendrauf
    b.shadow(x0, y0, x1, y1)
    leg = 0.03
    # hintere Beine, Ablage, Zeug auf der Ablage, vordere Beine, zuletzt die Platte
    for lx in (x0 + 0.06, x1 - 0.06):
        b.box(lx - leg, y1 - 0.06 - leg, lx + leg, y1 - 0.06 + leg, 0, H, shade(HERD_IRON, 1.3), HERD_IRON, w=0.02)
    b.box(x0 + 0.03, y0 + 0.03, x1 - 0.03, y1 - 0.03, 0.22, 0.04, wood, shade(wood, 0.8), w=0.02)
    zs = 0.26 * K                                                # Ablage-Oberflaeche (Bildversatz)
    sx, sy = x0 + 0.2, y0 + 0.16 + zs                            # Mehlsack, liegt mit zugebundenem Hals nach rechts
    sack = shade(hexc("#dcd4bc"), 0.85)
    c.ellipse(sx, sy, 0.15, 0.1, fill=sack, outline=OUTLINE, width=0.015)
    c.poly([(sx + 0.12, sy + 0.03), (sx + 0.2, sy + 0.05), (sx + 0.21, sy - 0.02), (sx + 0.12, sy - 0.04)], fill=sack, outline=OUTLINE, width=0.015)
    c.line([(sx + 0.145, sy + 0.045), (sx + 0.15, sy - 0.045)], fill=hexc("#6e5234"), width=0.014)
    c.line([(sx - 0.1, sy + 0.04), (sx + 0.02, sy + 0.06)], fill=shade(sack, 0.7), width=0.008)
    c.line([(sx - 0.08, sy - 0.05), (sx + 0.05, sy - 0.03)], fill=shade(sack, 0.7), width=0.008)
    c.text(sx - 0.02, sy, "FLOUR", 0.03, shade(sack, 0.5))
    b.box(x0 + 0.46, y0 + 0.07, x1 - 0.08, y1 - 0.12, 0.26, 0.16, wood_l, wood, w=0.02)   # Brotkiste
    for k in range(3):
        c.ellipse(x0 + 0.52 + k * 0.1, y0 + 0.1 + 0.42 * K + 0.08, 0.05, 0.035, fill=BUN, outline=OUTLINE, width=0.012)
    for lx in (x0 + 0.06, x1 - 0.06):
        b.box(lx - leg, y0 + 0.06 - leg, lx + leg, y0 + 0.06 + leg, 0, H, shade(HERD_IRON, 1.3), HERD_IRON, w=0.02)
    b.box(x0, y0, x1, y1, H, 0.08, wood_l, wood, w=0.025)        # Holzplatte
    c.rect(x0 + 0.012, y0 + (H + 0.065) * K, x1 - 0.012, y0 + (H + 0.08) * K - 0.012, fill=trim)   # Stahlkante
    zt = (H + 0.08) * K                                          # Bildversatz der Plattenoberflaeche
    for d in (-0.1, 0.05, 0.18):                                 # Bretterfugen der Platte
        c.line([(x0 + 0.03, d + zt), (x1 - 0.03, d + zt)], fill=shade(wood, 0.72), width=0.01)
    # Geschirrtuch ueber der Vorderkante
    tw = [(0.3, y0 + H * K + 0.02), (0.42, y0 + H * K + 0.02), (0.41, y0 + 0.5 * K), (0.31, y0 + 0.52 * K)]
    c.poly(tw, fill=hexc("#8aa0b4"), outline=OUTLINE, width=0.015)
    for k in range(3):
        c.line([(0.325 + k * 0.035, y0 + H * K), (0.325 + k * 0.035, y0 + 0.52 * K)], fill=hexc("#5a7088"), width=0.008)

    def top(x, d):
        return x, d + zt

    # Schneidbrett mit halb gebautem Burger
    bx0, bd0, bx1, bd1 = -0.42, -0.2, -0.04, 0.08
    c.poly([top(bx0, bd0), top(bx1, bd0), top(bx1 + 0.01, bd1), top(bx0 + 0.01, bd1)], fill=hexc("#c9a46a"), outline=OUTLINE, width=0.015)
    c.line([top(bx0 + 0.03, bd0 + 0.02), top(bx1 - 0.02, bd0 + 0.02)], fill=alpha(OUTLINE, 70), width=0.008)
    c.ellipse(*top(bx1 - 0.04, bd1 - 0.04), 0.012, 0.008, fill=OUTLINE)                       # Aufhaengeloch
    ux, ud = -0.24, -0.06
    layers = ((0.0, 0.11, 0.055, BUN_D, BUN), (0.03, 0.105, 0.05, PATTY, PATTY), (0.05, 0.1, 0.045, shade(CHEESE, 0.85), CHEESE),
              (0.065, 0.12, 0.05, shade(LETTUCE, 0.8), LETTUCE), (0.09, 0.11, 0.06, BUN_D, BUN))
    for k, (z, rx, ry, side, topc) in enumerate(layers):
        px_, py_ = top(ux, ud + z)
        if k == 2:                                                                            # Kaese: Scheibe mit Ecken
            c.poly([(px_ - rx, py_ - ry * 0.4), (px_ + rx * 0.9, py_ - ry * 0.7), (px_ + rx, py_ + ry * 0.5), (px_ - rx * 0.8, py_ + ry * 0.8)],
                   fill=topc, outline=OUTLINE, width=0.012)
            continue
        if k == 3:                                                                            # Salat: welliger Rand
            pts = []
            for i in range(14):
                a = i / 14 * 6.2832
                f = 1.0 if i % 2 else 0.8
                pts.append((px_ + math.cos(a) * rx * f, py_ + math.sin(a) * ry * f))
            c.poly(pts, fill=topc, outline=OUTLINE, width=0.012)
            continue
        c.rect(px_ - rx, py_, px_ + rx, py_ + 0.02, fill=side)
        c.ellipse(px_, py_, rx, ry, fill=side, outline=OUTLINE, width=0.012)
        c.ellipse(px_, py_ + 0.02, rx, ry, fill=topc, outline=OUTLINE, width=0.012)
    sx_, sy_ = top(ux, ud + 0.11)
    for dx, dy in ((-0.04, 0.0), (0.01, 0.02), (0.04, -0.01), (-0.01, -0.03), (0.03, 0.03)):   # Sesam
        c.ellipse(sx_ + dx, sy_ + dy, 0.009, 0.006, fill=hexc("#f4e4b0"))
    # Wender quer auf dem Brett
    wx, wd = -0.1, 0.0
    c.line([top(wx, wd), top(wx + 0.06, wd - 0.14)], fill=OUTLINE, width=0.03)
    c.line([top(wx, wd), top(wx + 0.06, wd - 0.14)], fill=hexc("#2a2a30"), width=0.018)
    c.poly([top(wx - 0.05, wd + 0.01), top(wx + 0.04, wd - 0.01), top(wx + 0.06, wd + 0.07), top(wx - 0.03, wd + 0.09)],
           fill=hexc("#a8b0b8"), outline=OUTLINE, width=0.012)
    # Teller mit rohen Patties
    px_, py_ = top(0.07, -0.13)
    c.ellipse(px_, py_, 0.13, 0.065, fill=hexc("#dcdcd4"), outline=OUTLINE, width=0.015)
    c.ellipse(px_, py_, 0.1, 0.048, outline=hexc("#b8b8b0"), width=0.008)
    for dx, dy in ((-0.045, -0.005), (0.04, 0.0), (-0.005, 0.03)):
        c.rect(px_ + dx - 0.045, py_ + dy, px_ + dx + 0.045, py_ + dy + 0.015, fill=shade(PATTY_RAW, 0.7))
        c.ellipse(px_ + dx, py_ + dy, 0.045, 0.025, fill=shade(PATTY_RAW, 0.7), outline=OUTLINE, width=0.01)
        c.ellipse(px_ + dx, py_ + dy + 0.015, 0.045, 0.025, fill=PATTY_RAW, outline=OUTLINE, width=0.01)

    def bowl(x, d, rx, inner):
        px_, py_ = top(x, d)
        ry = rx * 0.55
        c.rect(px_ - rx, py_, px_ + rx, py_ + 0.04, fill=shade(HERD_IRON, 0.85))
        c.line([(px_ - rx, py_), (px_ - rx, py_ + 0.04)], fill=OUTLINE, width=0.012)
        c.line([(px_ + rx, py_), (px_ + rx, py_ + 0.04)], fill=OUTLINE, width=0.012)
        c.ellipse(px_, py_, rx, ry, fill=shade(HERD_IRON, 0.85), outline=OUTLINE, width=0.012)
        c.ellipse(px_, py_ + 0.04, rx, ry, fill=shade(HERD_IRON, 1.3), outline=OUTLINE, width=0.012)
        c.ellipse(px_, py_ + 0.04, rx * 0.8, ry * 0.75, fill=shade(HERD_IRON, 0.7))
        inner(px_, py_ + 0.045)

    def salad(px_, py_):
        for dx, dy, r in ((-0.03, 0.0, 0.03), (0.02, 0.01, 0.028), (0.0, -0.015, 0.025), (0.035, -0.01, 0.02)):
            c.ellipse(px_ + dx, py_ + dy, r, r * 0.7, fill=LETTUCE, outline=shade(LETTUCE, 0.6), width=0.008)

    def tomatoes(px_, py_):
        for dx, dy in ((-0.03, 0.0), (0.025, 0.005), (-0.005, -0.012)):
            c.ellipse(px_ + dx, py_ + dy, 0.03, 0.02, fill=TOMATO, outline=OUTLINE, width=0.008)
            c.ellipse(px_ + dx, py_ + dy, 0.018, 0.011, fill=shade(TOMATO, 1.25))

    def cheese(px_, py_):
        for k in range(3):                                                                    # Scheibenstapel
            dy = -0.012 + k * 0.012
            c.poly([(px_ - 0.045, py_ + dy - 0.018), (px_ + 0.045, py_ + dy - 0.018), (px_ + 0.04, py_ + dy + 0.018), (px_ - 0.05, py_ + dy + 0.018)],
                   fill=CHEESE if k == 2 else shade(CHEESE, 0.85), outline=OUTLINE, width=0.008)

    bowl(0.1, 0.14, 0.085, salad)
    bowl(0.3, 0.13, 0.08, tomatoes)
    bowl(0.29, -0.08, 0.075, cheese)
    # Broetchenkorb hinten in der Mitte
    kx, ky = top(-0.12, 0.17)
    c.rect(kx - 0.11, ky, kx + 0.11, ky + 0.05, fill=shade(wood, 0.8))
    c.line([(kx - 0.11, ky), (kx - 0.11, ky + 0.05)], fill=OUTLINE, width=0.012)
    c.line([(kx + 0.11, ky), (kx + 0.11, ky + 0.05)], fill=OUTLINE, width=0.012)
    c.ellipse(kx, ky, 0.11, 0.06, fill=shade(wood, 0.8), outline=OUTLINE, width=0.012)
    for yy in (ky + 0.015, ky + 0.035):
        c.line([(kx - 0.1, yy), (kx + 0.1, yy)], fill=shade(wood, 1.15), width=0.006)
    c.ellipse(kx, ky + 0.05, 0.11, 0.06, fill=wood, outline=OUTLINE, width=0.012)
    for dx, dy in ((-0.05, 0.01), (0.03, 0.0), (-0.01, 0.035)):
        c.ellipse(kx + dx, ky + 0.05 + dy, 0.045, 0.03, fill=BUN, outline=OUTLINE, width=0.01)
        c.ellipse(kx + dx - 0.012, ky + 0.05 + dy + 0.01, 0.015, 0.008, fill=shade(BUN, 1.2))
    # Saucenflaschen vorn rechts
    for x, d, col in ((0.38, -0.2, TOMATO), (0.41, -0.06, hexc("#e8b830"))):
        px_, py_ = top(x, d)
        c.rect(px_ - 0.03, py_, px_ + 0.03, py_ + 0.14, fill=col, outline=OUTLINE, width=0.012)
        c.ellipse(px_, py_, 0.03, 0.016, fill=col, outline=OUTLINE, width=0.012)
        c.ellipse(px_, py_ + 0.14, 0.03, 0.016, fill=shade(col, 1.15), outline=OUTLINE, width=0.012)
        c.poly([(px_ - 0.012, py_ + 0.15), (px_ + 0.012, py_ + 0.15), (px_ + 0.004, py_ + 0.2), (px_ - 0.004, py_ + 0.2)], fill=hexc("#2a2a30"), outline=OUTLINE, width=0.01)
        c.line([(px_ - 0.02, py_ + 0.02), (px_ - 0.02, py_ + 0.12)], fill=alpha((255, 255, 255, 255), 90), width=0.008)
    # Bestellzettel auf dem Spiess (hinten links)
    qx, qy = top(-0.36, 0.19)
    c.ellipse(qx, qy, 0.045, 0.025, fill=shade(HERD_IRON, 0.9), outline=OUTLINE, width=0.012)
    c.line([(qx, qy + 0.01), (qx, qy + 0.38)], fill=OUTLINE, width=0.022)
    c.line([(qx, qy + 0.01), (qx, qy + 0.38)], fill=hexc("#a8b0b8"), width=0.01)
    c.poly([(qx - 0.1, qy + 0.2), (qx + 0.1, qy + 0.21), (qx + 0.09, qy + 0.36), (qx - 0.11, qy + 0.35)], fill=PAPER, outline=OUTLINE, width=0.012)
    c.text(qx - 0.005, qy + 0.315, "ORDER", 0.038, OUTLINE)
    for k in range(3):
        c.line([(qx - 0.07, qy + 0.27 - k * 0.03), (qx + 0.02 + k * 0.02, qy + 0.272 - k * 0.03)], fill=shade(PAPER, 0.5), width=0.007)
    c.ellipse(qx, qy + 0.3, 0.006, 0.006, fill=OUTLINE)                                     # Einstich
    return b.result()


def gully(ppm, seed=0):
    """Garten-Vent: gusseiserner Gully in einem Steinrahmen, Deckel halb aufgeschoben (offen gezeichnet)."""
    c = Canvas(-0.62, -0.5, 0.62, 0.5, ppm)
    c.soft_shadow([(-0.48, -0.34), (0.52, -0.34), (0.52, 0.36), (-0.48, 0.36)], 90, 0.06)
    c.poly([(-0.5, -0.36), (0.5, -0.36), (0.5, 0.36), (-0.5, 0.36)], fill=shade(STONE, 0.95), outline=OUTLINE, width=0.04)
    c.poly([(-0.36, -0.24), (0.36, -0.24), (0.36, 0.24), (-0.36, 0.24)], fill=hexc("#0b0d10"), outline=OUTLINE, width=0.03)
    c.poly([(-0.36, 0.12), (0.36, 0.12), (0.36, 0.24), (-0.36, 0.24)], fill=hexc("#22201e"))          # Rueckwand
    for k in range(5):                                                                                 # Rost (halb)
        x = -0.3 + k * 0.15
        c.line([(x, -0.24), (x, 0.0)], fill=IRON, width=0.035)
    c.line([(-0.36, -0.02), (0.36, -0.02)], fill=IRON, width=0.03)
    # aufgeschobener Deckel ueber der Suedkante
    c.poly([(-0.42, -0.46), (0.3, -0.46), (0.3, -0.18), (-0.42, -0.18)], fill=shade(IRON, 1.2), outline=OUTLINE, width=0.035)
    for k in range(4):
        y = -0.42 + k * 0.07
        c.line([(-0.36, y), (0.24, y)], fill=shade(IRON, 0.8), width=0.014)
    c.line([(-0.42, -0.19), (0.3, -0.19)], fill=shade(IRON, 1.6), width=0.012)
    for x, y in ((-0.44, 0.3), (0.42, -0.3), (0.44, 0.28)):                                           # Moos in den Fugen
        c.ellipse(x, y, 0.06, 0.035, fill=MOSS)
    return WV._result(c, ppm)


GULLY_SLIDE = 0.46                 # Weg des Gussdeckels nach Sueden im letzten Bild (m)


def gully_frames(ppm, seed=0):
    """Garten-Vent als Bildfolge fuer die Ein-/Ausstiegsanimation: [0] Gussdeckel liegt geschlossen im
    Steinrahmen, [5] nach Sueden aufgeschoben (Haltung wie gully()); dazwischen rutscht der Deckel Bild
    fuer Bild weiter und gibt den Schacht von Norden her frei. Der Deckel ist hier so gross wie die
    Oeffnung (bei gully() war er nur ein Teilstueck), deshalb reicht die Leinwand weiter nach Sueden als
    bei gully(); Groesse und Anker (Mitte der Oeffnung) sind ueber alle Bilder gleich.
    Rueckgabe: Liste aus (PIL RGBA, anchor_x_px, anchor_y_px)."""
    frames = []
    lid = shade(IRON, 1.2)
    for k in range(6):
        t = k / 5
        slide = GULLY_SLIDE * t
        c = Canvas(-0.62, -0.84, 0.62, 0.5, ppm)
        c.soft_shadow([(-0.48, -0.34), (0.52, -0.34), (0.52, 0.36), (-0.48, 0.36)], 90, 0.06)
        c.poly([(-0.5, -0.36), (0.5, -0.36), (0.5, 0.36), (-0.5, 0.36)], fill=shade(STONE, 0.95), outline=OUTLINE, width=0.04)
        c.poly([(-0.36, -0.24), (0.36, -0.24), (0.36, 0.24), (-0.36, 0.24)], fill=hexc("#0b0d10"), outline=OUTLINE, width=0.03)
        c.poly([(-0.36, 0.12), (0.36, 0.12), (0.36, 0.24), (-0.36, 0.24)], fill=hexc("#22201e"))      # Rueckwand
        for j in range(5):                                                                             # Rost (halb)
            x = -0.3 + j * 0.15
            c.line([(x, -0.24), (x, 0.0)], fill=IRON, width=0.035)
        c.line([(-0.36, -0.02), (0.36, -0.02)], fill=IRON, width=0.03)
        # Gussdeckel: deckt geschlossen die Oeffnung samt Lippe, rutscht nach Sueden und etwas nach Westen
        px0, px1 = -0.38 - 0.04 * t, 0.38 - 0.04 * t
        py0, py1 = -0.25 - slide, 0.25 - slide
        if k:
            c.soft_shadow([(px0 + 0.04, py0 - 0.06), (px1 + 0.05, py0 - 0.06), (px1 + 0.05, py1 - 0.02), (px0 + 0.04, py1 - 0.02)], 110, 0.04)
        c.poly([(px0, py0), (px1, py0), (px1, py1), (px0, py1)], fill=lid, outline=OUTLINE, width=0.035)
        for j in range(6):                                                                             # Rillen
            y = py0 + 0.07 + j * 0.07
            c.line([(px0 + 0.06, y), (px1 - 0.06, y)], fill=shade(IRON, 0.8), width=0.014)
        for x in (px0 + 0.12, px1 - 0.12):                                                             # Hebeschlitze
            c.ellipse(x, py1 - 0.09, 0.035, 0.016, fill=hexc("#1a1c20"), outline=OUTLINE, width=0.012)
        c.line([(px0 + 0.02, py1 - 0.012), (px1 - 0.02, py1 - 0.012)], fill=shade(IRON, 1.6), width=0.012)
        c.line([(px1 - 0.015, py0 + 0.03), (px1 - 0.015, py1 - 0.03)], fill=shade(IRON, 0.6), width=0.012)
        c.rect(px0, py0 - 0.025, px1, py0, fill=shade(IRON, 0.7), outline=OUTLINE, width=0.02)        # Stirn (Dicke)
        for x, y in ((-0.44, 0.3), (0.42, -0.3), (0.44, 0.28)):                                       # Moos in den Fugen
            if not (px0 < x < px1 and py0 < y < py1):
                c.ellipse(x, y, 0.06, 0.035, fill=MOSS)
        frames.append(WV._result(c, ppm))
    return frames


def clean(spr):
    """Weiche Schattenraender entfernen (wie wald_vents._result): das Spiel faerbt beim Hervorheben jeden
    Pixel mit Deckkraft ein, ein halbtransparenter Bodenschatten wurde so zum weissen Fleck unter dem
    Block (Test 09.10.: Regieklappe)."""
    from PIL import ImageChops, ImageFilter
    img, ax, ay = spr
    a = img.getchannel("A")
    # Schwelle 120 statt wald_vents.ALPHA_MIN (64): Block.shadow malt den Bodenschatten mit Deckkraft ~90,
    # der blieb sonst stehen und leuchtete beim Hervorheben weiss (zweiter Test 09.10.)
    mask = a.point(lambda v: 255 if v >= 120 else 0)
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    img = img.copy()
    img.putalpha(ImageChops.multiply(a, mask))
    return img, ax, ay


def render_all(ppm, brief):
    out = {k: clean(v) for k, v in _render_all(ppm, brief).items()}
    return out


# Konsolen aus einem fertigen Bild (28.10., GPT-Boegen 18-20): Name -> (Datei in tools/villa_assets, Hoehe in m).
# Anker = Mitte der Unterkante. gpt_standard.py laesst diese Namen aus (sonst kaeme das alte GPT-Bild zurueck).
IMAGE_CONSOLES = {
    "EmergencyButton": ("villa_notfalltisch.png", 1.15),
    "MakeBurger": ("villa_herd_gross.png", 1.9),          # der grosse Herd selbst ist die Burger-Konsole (n66)
    "FuelEngineConsole@kitchen": ("villa_holzkorb_kueche.png", 0.85),   # 29.10. abends (n16): Holzkorb statt Gasflasche ("ich fuerchte Explosionen"); aus der GPT-Zelle des Holzkorbs
    "UnlockSafe": ("villa_safe.png", 1.3),                # Airship-Tresor im Arbeitszimmer (n33)
    "WaterBench": ("villa_pflanzbank.png", 1.25),         # Pflanzen giessen, Gewaechshaus (n24)
    "Campfire": ("villa_lagerfeuer.png", 1.2),            # Marshmallows, Crew Camp (n62)
    "Catering": ("villa_catering.png", 1.35),             # Essen und Trinken, Vorplatz (n56)
    "PressureValve": ("villa_druckventil.png", 1.25),      # Kesseldruck ablassen, Heizungskeller (n64)
    "CampGenerator": ("villa_generator.png", 1.2),        # Generator im Crew Camp statt in der Kueche (n67)
}


def image_console(name, ppm):
    from PIL import Image
    import os
    file, h = IMAGE_CONSOLES[name]
    src = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "villa_assets", file)).convert("RGBA")
    hh = int(round(h * ppm)); ww = int(round(src.width * hh / src.height))
    im = src.resize((ww, hh), Image.LANCZOS)
    pad = 4
    out = Image.new("RGBA", (ww + 2 * pad, hh + 2 * pad), (0, 0, 0, 0))
    out.alpha_composite(im, (pad, pad))
    return out, out.width / 2, pad + 0.04 * ppm


def _render_all(ppm, brief):
    WC.TINT.update(TINT)
    WC.CLEARINGS = OUTDOOR
    out = {}
    for r in brief:
        v, key, room, wall = r["variant"], r["key"], r["room"], r["wall"]
        parts = key.split("/")
        name = parts[1] if len(parts) == 3 else key
        if key.startswith("Vent/"):
            # Ruhebild = geschlossen; "Vent/<id>/1".."/5" spielt Atlas beim Ein- und Aussteigen ab (letztes = offen)
            vid = int(key.split("/")[1])
            frames = gully_frames(ppm, vid) if room in OUTDOOR or room == "greenhouse" else VCA.grate_frames(ppm, seed=vid)
            out[(v, key)] = frames[0]
            for k, fr in enumerate(frames[1:], 1):
                out[(v, f"{key}/{k}")] = fr
            continue
        img_name = key if key in IMAGE_CONSOLES else (f"{name}@{room}" if f"{name}@{room}" in IMAGE_CONSOLES else name)
        if img_name in IMAGE_CONSOLES:
            spr = image_console(img_name, ppm)
        elif key == "EmergencyButton":
            spr = slate_table(ppm)
        elif (name, room) in getattr(VCA, "BY_NAME_ROOM", {}):
            # raumabhaengige Villa-Motive (24.10.: Kohlenkasten in der Kueche)
            spr = VCA.BY_NAME_ROOM[(name, room)](ppm, sum(ord(ch) for ch in key) % 7)
        elif name in VCA.BY_NAME:
            # Villa-eigene Motive (Audit 15.10.); idx variiert Details je Konsole. 28.10. abends: der Seance-Tisch mit dem
            # Ouija-Brett ("Set the Seance Table") groesser
            scale = {"StartReactorConsole": 1.9, "StabilizeSteeringConsole": 2.5}.get(name, 1.0)
            spr = VCA.BY_NAME[name](ppm * scale, sum(ord(ch) for ch in key) % 7)
        elif key == "SurveillanceConsole":
            spr = WC.ranger_desk(ppm)
        elif key == "AdminTable":
            spr = WC.map_board(ppm)
        elif key == "FreeplayLaptop":
            spr = WC.crate_laptop(ppm)
        elif name == "SwipeCardConsole":
            spr = WC.id_reader(ppm, room)
        elif name == "MakeBurger":
            spr = burger_station(ppm)
        elif name == "MedScanner":
            spr = WC.floor_scanner(ppm * 0.85)                # 28.10. n35: Schminkstuhl etwas kleiner
        elif name == "MedBayConsole":
            spr = WC.microscope_bench(ppm)
        elif name == "CleanFilterConsole":
            spr = WC.water_filter(ppm)
        elif name == "FuelEngineConsole":
            spr = WC.fuel_station(ppm, room)
        elif name == "AlignEngineConsole":
            spr = WC.gauge_post(ppm, room)
        elif name == "gasCanConsole":
            spr = WC.jerrycan_rack(ppm)
        elif name == "StabilizeSteeringConsole":
            spr = WC.theodolite(ppm * 2.8)                   # Rueckfall fuer Karten ohne Villa-eigenes Teleskop
        elif name == "FixCommsConsole":
            spr = WC.radio_set(ppm)
        else:
            kind = WC._kind_of(name)
            if name == "StartReactorConsole":
                kind = "keypad"
            if kind is None:
                continue
            kw = {}
            if kind == "keypad":
                kw = dict(red=(name == "NoOxyConsole"))
            if kind == "data":
                kw = dict(upload=(name != "DataConsole"))
            spr = WC.generic(kind, wall, room, ppm, **kw)
        out[(v, key)] = spr
    return out
