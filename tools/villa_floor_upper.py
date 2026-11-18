# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_floor_upper.py - Bodenbild des Obergeschosses von Hollowmere Manor (17.11., villa_layout.UPPER_*).
#
# Gleicher Aufbau wie villa_floor_map.render (Leerraum, Wandkrone, Boeden, Stirnseiten der Nordwaende, Umgebungsschatten,
# Tuschekante, Papierkorn) und dieselben Bausteine; gerechnet wird in lokalen Metern ab der linken oberen Ecke von
# UPPER_BOUNDS. Dazu die zwei Treppenschaechte (Stufen fuehren nach Sueden hinab ins Dunkle, Gelaender links und rechts),
# Laeufer im Flur, Teppich im Schlafzimmer, Rotlicht in der Dunkelkammer und etwas Horror am Boden.

import math
import random

from PIL import Image, ImageOps
from shapely import affinity
from shapely.geometry import box

import handdraw as HD
import villa_floor as VF
import villa_floor_map as FM
import villa_layout as L


def _local(g):
    ux0, uy0 = L.UPPER_BOUNDS[0], L.UPPER_BOUNDS[1]
    return affinity.translate(g, -ux0, -uy0)


def stairwell(C, x0, y0, x1, y1, ppm):
    """Treppenschacht von oben: Stufen fuehren nach Sueden hinab und werden dunkler, Gelaender auf beiden Seiten."""
    d = C.draw()
    n = 7
    h = (y1 - y0) / n
    for k in range(n):
        ya, yb = y0 + k * h, y0 + (k + 1) * h
        f = 1.0 - k / (n + 0.5)
        tread = tuple(int(c * (0.35 + 0.65 * f)) for c in VF.WALNUT)
        riser = tuple(int(c * (0.2 + 0.45 * f)) for c in VF.WALNUT_D)
        d.rectangle([*C.P(x0, ya), *C.P(x1, yb)], fill=riser)
        d.rectangle([*C.P(x0, ya), *C.P(x1, yb - h * 0.35)], fill=tread)
        # roter Laeufer mittig, wie auf der Freitreppe unten
        rw = (x1 - x0) * 0.62
        cx = (x0 + x1) / 2
        run = tuple(int(c * (0.3 + 0.7 * f)) for c in VF.BORDEAUX)
        d.rectangle([*C.P(cx - rw / 2, ya), *C.P(cx + rw / 2, yb - h * 0.35)], fill=run)
        gold = tuple(int(c * (0.3 + 0.7 * f)) for c in VF.BRASS)
        d.line([C.P(cx - rw / 2 + 0.05, yb - h * 0.38), C.P(cx + rw / 2 - 0.05, yb - h * 0.38)], fill=gold, width=max(1, int(0.03 * ppm)))
        d.line([C.P(x0, yb - h * 0.35), C.P(x1, yb - h * 0.35)], fill=(10, 8, 12), width=max(1, int(0.025 * ppm)))
    # Schwaerze am unteren Ende
    def fade(dd):
        dd.rectangle([*C.P(x0, y1 - 0.45), *C.P(x1, y1)], fill=(0, 0, 0, 200))
    C.soft(fade, 0.25)
    d = C.draw()
    # Gelaender: Handlauf und Docken auf beiden Seiten
    for xr in (x0 - 0.15, x1 + 0.15):
        d.rectangle([*C.P(xr - 0.07, y0), *C.P(xr + 0.07, y1 - 0.15)], fill=VF.WALNUT_D, outline=(14, 10, 12))
        yy = y0 + 0.12
        while yy < y1 - 0.2:
            d.ellipse([*C.P(xr - 0.05, yy - 0.04), *C.P(xr + 0.05, yy + 0.04)], fill=VF.WALNUT_L, outline=(14, 10, 12))
            yy += 0.22


def render(ppm):
    """Bodenbild des Obergeschosses in UPPER_BOUNDS, (32 x 18 m) * ppm."""
    import gen_villa as G
    walk, geoms, opens = G.build_upper()
    walk, geoms = _local(walk), {k: _local(g) for k, g in geoms.items()}
    ux0, uy0, ux1, uy1 = L.UPPER_BOUNDS
    old = (FM.W_M, FM.H_M, dict(FM.STYLE), FM.OUTER_NORTH_Y)
    FM.W_M, FM.H_M = ux1 - ux0, uy1 - uy0
    FM.OUTER_NORTH_Y = 1.6
    FM.STYLE.update(L.UPPER_STYLE)
    try:
        rnd = random.Random(17)
        C = FM.Canvas(ppm)
        FM.void_mass(C, rnd)
        d = C.draw()
        for a in L.UPPER_AREAS:
            r = _local(box(*a[2]))
            for p in FM.parts(r.difference(walk)):
                d.polygon([C.P(*q) for q in p.exterior.coords], fill=FM.WALL_TOP)
        for key, g in geoms.items():
            C.fill_tile(VF.material_tile(L.UPPER_MAT.get(key, "parkett"), ppm, seed=len(key) + 40), g,
                        tone=0.9 if key == "ucorridor" else None)
        for o in opens:
            C.fill_tile(VF.material_tile("dielen", ppm, seed=5), _local(G.opening_box(o)), tone=0.8)
        # Laeufer im Flur, Teppich im Schlafzimmer und in der Kinderstube
        FM.runner(C, 2.6 - ux0, -13.95 - uy0, 31.4 - ux0, -13.05 - uy0, ppm)
        FM.rug(C, 25.3 - ux0, -8.0 - uy0, 1.8, 1.0, ppm)
        FM.rug(C, 7.0 - ux0, -9.2 - uy0, 1.6, 0.9, ppm)
        FM.rug(C, 17.0 - ux0, -9.9 - uy0, 2.0, 0.9, ppm)            # Upper Landing
        FM.rug(C, 28.0 - ux0, -18.7 - uy0, 1.5, 0.8, ppm)           # Sewing Room
        C.fill_tile(VF.material_tile("teppich", ppm, seed=23), box(19.7 - ux0, -20.75 - uy0, 21.1 - ux0, -20.2 - uy0))   # Badvorleger vor der Wanne (18.11.)
        # Treppenschaechte
        for st in L.UPPER_STAIRS:
            x0, y0, x1, y1 = st[6]
            stairwell(C, x0 - ux0, y0 - uy0, x1 - ux0, y1 - uy0, ppm)
        # Horror: Fussspuren vom Treppenschacht ins Kinderzimmer, Blut im Bad, Kreide im Dachboden
        d = C.draw()
        FM.footprints(d, C, [(16.2 - ux0, -8.3 - uy0), (13.5 - ux0, -9.4 - uy0), (10.6 - ux0, -9.6 - uy0), (8.0 - ux0, -8.0 - uy0)], rnd)
        FM.blood(d, C, 21.8 - ux0, -19.2 - uy0, 0.3, rnd)
        FM.blood(d, C, 26.0 - ux0, -9.2 - uy0, 0.18, rnd)
        FM.chalk_outline(d, C, 6.5 - ux0, -18.8 - uy0, 1.0, 0.7, 31)
        # Spinnweben in den Ecken aller Raeume (Nordecken, wo keine Oeffnung ist)
        for a_ in L.UPPER_AREAS:
            x0_, y0_, x1_, y1_ = a_[2]
            for (cx, cy, qx, qy) in ((x0_ + 0.2, y0_ + 0.2, 1, 1), (x1_ - 0.2, y0_ + 0.2, -1, 1), (x0_ + 0.2, y1_ - 0.2, 1, -1)):
                VF.floor_cobweb_corner(d, C.Pw, ppm, cx - ux0, -(cy - uy0), 0.55, qx, -qy, seed=int(cx * 10 + cy))
        # Kinderstube: Kreide-Huepfspiel auf den Dielen
        hx, hy = 9.6, -9.0
        for k, (dx, dy) in enumerate(((0, 0), (0, -0.5), (-0.25, -1.0), (0.25, -1.0), (0, -1.5), (-0.25, -2.0), (0.25, -2.0), (0, -2.5))):
            x_, y_ = hx + dx - ux0, hy + dy - uy0
            d.rectangle([*C.P(x_ - 0.22, y_ - 0.22), *C.P(x_ + 0.22, y_ + 0.22)], outline=(226, 222, 210, 170), width=max(1, int(0.025 * ppm)))
        # Dunkelkammer: verstreute Fotos am Boden
        for _ in range(9):
            x_, y_ = rnd.uniform(14.0, 18.2) - ux0, rnd.uniform(-20.4, -16.0) - uy0
            ang = rnd.uniform(-0.6, 0.6)
            w_, h_ = 0.22, 0.17
            pts = [(x_ + px * math.cos(ang) - py * math.sin(ang), y_ + px * math.sin(ang) + py * math.cos(ang))
                   for px, py in ((-w_ / 2, -h_ / 2), (w_ / 2, -h_ / 2), (w_ / 2, h_ / 2), (-w_ / 2, h_ / 2))]
            d.polygon([C.P(*q) for q in pts], fill=(214, 206, 188, 235), outline=(20, 16, 18, 220))
        # Bad: Wasser mit Blut, nasse Spuren hinaus in den Flur
        d.ellipse([*C.P(19.9 - ux0, -20.6 - uy0), *C.P(21.9 - ux0, -19.9 - uy0)], fill=(70, 30, 40, 120))
        FM.footprints(d, C, [(21.0 - ux0, -20.0 - uy0), (21.4 - ux0, -17.0 - uy0), (21.5 - ux0, -14.6 - uy0), (17.0 - ux0, -13.4 - uy0)], rnd)
        # Naehzimmer: Stecknadeln und Garnreste
        for _ in range(26):
            x_, y_ = rnd.uniform(25.0, 31.0) - ux0, rnd.uniform(-21.0, -16.0) - uy0
            d.line([C.P(x_, y_), C.P(x_ + rnd.uniform(-0.08, 0.08), y_ + rnd.uniform(-0.08, 0.08))], fill=(200, 200, 210, 200), width=max(1, int(0.012 * ppm)))
        for _ in range(4):
            x_, y_ = rnd.uniform(25.0, 31.0) - ux0, rnd.uniform(-21.0, -16.0) - uy0
            d.arc([*C.P(x_ - 0.3, y_ - 0.2), *C.P(x_ + 0.3, y_ + 0.2)], rnd.uniform(0, 180), rnd.uniform(200, 360),
                  fill=rnd.choice([(170, 40, 60, 210), (60, 90, 160, 210), (210, 190, 60, 210)]), width=max(1, int(0.015 * ppm)))
        # Dachboden: Staubschleifspuren (etwas wurde zum Koffer geschleift) und Wachstropfen am Flur
        d.line([C.P(4.0 - ux0, -16.0 - uy0), C.P(6.0 - ux0, -18.0 - uy0), C.P(8.0 - ux0, -20.0 - uy0)], fill=(120, 110, 96, 90), width=max(1, int(0.35 * ppm)), joint="curve")
        FM.blood(d, C, 6.2 - ux0, -10.6 - uy0, 0.12, rnd)
        FM.blood(d, C, 12.3 - ux0, -13.6 - uy0, 0.15, rnd)
        FM.ambient(C, walk)
        n = FM.faces(C, walk, geoms)
        for key in L.UPPER_DARK:
            g = geoms.get(key)
            if g is None:
                continue
            m = C.mask(g).point(lambda v: int(v * 0.42))
            C.img = Image.composite(Image.new("RGB", C.img.size, (12, 14, 30)), C.img, m)
        # Dunkelkammer: Rotlicht
        g = geoms.get("darkroom")
        if g is not None:
            m = C.mask(g).point(lambda v: int(v * 0.38))
            C.img = Image.composite(Image.new("RGB", C.img.size, (150, 18, 24)), C.img, m)
        C.img = Image.blend(C.img, ImageOps.grayscale(C.img).convert("RGB"), 0.2)
        r, g_, b = C.img.split()
        C.img = Image.merge("RGB", (r.point(lambda v: int(v * 0.82)), g_.point(lambda v: int(v * 0.85)), b.point(lambda v: int(v * 0.95))))
        d = C.draw()
        for k, p in enumerate(FM.parts(walk)):
            for j, ring in enumerate([p.exterior] + list(p.interiors)):
                pts = HD.wobble(list(ring.coords), amp=0.008, seed=700 + k * 50 + j, step=0.1, closed=True)
                HD.ink(d, [C.P(*q) for q in pts], FM.OUTLINE + (255,), max(2, int(0.05 * ppm)), seed=k * 50 + j, var=0.2, closed=True)
        C.img = HD.paper_grain(C.img, 0.03, seed=9)
        print(f"villa upper floor: {C.img.size}, {n} wall faces")
        return C.img
    finally:
        FM.W_M, FM.H_M, FM.OUTER_NORTH_Y = old[0], old[1], old[3]
        FM.STYLE.clear(); FM.STYLE.update(old[2])
