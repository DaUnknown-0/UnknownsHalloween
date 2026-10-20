# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_minimap.py - Minimap von Ravenhollow Cemetery im Stil der Villa-Minimap (Among-Us-Karte): begehbare
# Flaeche hell, Gebaeudemauern als dicke dunkle Baender mit Tuerluecken, Raender der Wege und Lichtungen als
# Linie, Raumnamen zentriert (Atlas map_labels, damit Sabotage- und Admin-Symbole ausweichen).
#
# SCHNITTSTELLE (gen_graveyard.minimap): render(ctx, labels_out) -> RGBA; labels_out bekommt (x, y, halbB, halbH).

from PIL import Image, ImageDraw, ImageFont
from shapely.ops import unary_union

import map_labels

S = 24                                    # px je m
FILL = (213, 205, 222, 255)
WALL = (36, 44, 70, 255)
TEXT = (30, 28, 44, 255)


def parts(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


def font(size):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except OSError:
        return ImageFont.load_default()


def render(ctx, labels_out):
    bx0, by0, bx1, by1 = ctx.bounds
    w, h = int((bx1 - bx0) * S), int((by1 - by0) * S)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    Pt = lambda x, y: ((x - bx0) * S, (by1 - y) * S)
    walk = ctx.walk
    for p in parts(walk):
        d.polygon([Pt(*q) for q in p.exterior.coords], fill=FILL)
        for hole in p.interiors:
            d.polygon([Pt(*q) for q in hole.coords], fill=(0, 0, 0, 0))
    shells = unary_union(ctx.shells).difference(walk)
    for p in parts(shells):                                                            # Gebaeudemauern
        d.polygon([Pt(*q) for q in p.exterior.coords], fill=WALL)
        for hole in p.interiors:
            d.polygon([Pt(*q) for q in hole.coords], fill=FILL)
    for p in parts(walk):                                                              # Aussenraender
        for ring in [p.exterior] + list(p.interiors):
            d.line([Pt(*q) for q in ring.coords], fill=WALL, width=4, joint="curve")
    f = font(17)
    labels_out.clear()
    for key, (name, _s, g) in ctx.rooms.items():
        c = g.representative_point()
        map_labels.place(d, f, name, c.x, c.y, g.buffer(-0.2), S, Pt, TEXT, labels_out)
    return img
