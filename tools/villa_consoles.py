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

import os
import sys

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)

import wald_consoles as WC                                   # noqa: E402
import wald_vents as WV                                      # noqa: E402
from museum_art import Canvas, K, OUTLINE, hexc, lift, shade  # noqa: E402

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


def _render_all(ppm, brief):
    WC.TINT.update(TINT)
    WC.CLEARINGS = OUTDOOR
    out = {}
    for r in brief:
        v, key, room, wall = r["variant"], r["key"], r["room"], r["wall"]
        parts = key.split("/")
        name = parts[1] if len(parts) == 3 else key
        if key.startswith("Vent/"):
            vid = int(key.split("/")[1])
            out[(v, key)] = gully(ppm, vid) if room in OUTDOOR or room == "greenhouse" else WV.hatch(ppm, seed=vid)
            continue
        if key == "EmergencyButton":
            spr = slate_table(ppm)
        elif key == "SurveillanceConsole":
            spr = WC.ranger_desk(ppm)
        elif key == "AdminTable":
            spr = WC.map_board(ppm)
        elif key == "FreeplayLaptop":
            spr = WC.crate_laptop(ppm)
        elif name == "SwipeCardConsole":
            spr = WC.id_reader(ppm, room)
        elif name == "MedScanner":
            spr = WC.floor_scanner(ppm)
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
            spr = WC.theodolite(ppm)
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
