# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_floor.py - das ganze Bodenbild von Ravenhollow Cemetery (Weltlage, y nach oben).
#
# Aufbau (wie villa_floor_map.py, aber in Weltkoordinaten):
#   1. Wald ausserhalb der Friedhofsmauer, Grabfelder (Gras) innerhalb
#   2. Grabreihen, Familiengruefte, Eiben, kahle Baeume, Bueesche in den Grabfeldern (nicht begehbar, gemalt)
#   3. Boeden: Kies auf den Wegen, Gras/Pflaster auf den Lichtungen, Material je Gebaeude
#   4. Bodendeko je Raum (Teppich, Grabplatten, Runenkreis, Grabhuegel, Russ, Pfuetzen ...), mit Abstand
#      zu Konsolen, Vents, Spielpunkten und Oeffnungen
#   5. Bordsteine an den Kieswegen, Umgebungsschatten, Wandkronen, Stirnseiten der Nordwaende, Fassaden
#   6. Lichtlachen (Laternen, Kerzen, Ofen), Mondflecken, Farbgrading, Tuschekante, Papierkorn

import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep

import handdraw as HD
import graveyard_mats as M
import graveyard_art as GA

INK = (16, 16, 22, 255)
WALL_TOP = (46, 46, 54)
CEMETERY_WALL = (-23.3, -19.3, 23.3, 19.3)        # Innenkante der Friedhofsmauer
CEMETERY_WALL_T = 0.6

ROOM_MAT = {   # Gebaeude: (Material, Seed, Ton, Extra)
    "chapel": ("grabplatten", 3, 1.0, {}),
    "coffins": ("dielen", 4, 1.0, {"base": (110, 96, 80)}),
    "well": ("kopfstein", 5, 1.0, {}),
    "mausoleum": ("marmor", 6, 0.95, {}),
    "morgue": ("kacheln", 7, 0.95, {}),
    "crematorium": ("ziegel", 8, 0.8, {"base": (104, 70, 60)}),
    "office": ("dielen", 9, 1.0, {"base": (112, 92, 74)}),
    "gatehouse": ("kopfstein", 10, 0.95, {}),
    "lanterns": ("dielen", 11, 0.95, {"base": (98, 90, 82)}),
    "lodge": ("dielen", 12, 1.0, {"base": (116, 98, 80)}),
}
WALL_STYLE = {"chapel": "kapelle", "coffins": "holz", "well": "stein", "mausoleum": "gruft", "morgue": "leichenhalle",
              "crematorium": "krema", "office": "holz", "gatehouse": "stein", "lanterns": "holz", "lodge": "holz"}
WALL_TOOLS = {"coffins": [("saege", 0.2), ("schaufel", 0.45), ("seil", 0.7)],
              "office": [("schluessel", 0.55), ("karte", 0.82), ("uhr", 0.3)],
              "lanterns": [("laterne", 0.15), ("laterne", 0.3), ("laterne", 0.45), ("laterne", 0.6), ("laterne", 0.75), ("laterne", 0.9)],
              "lodge": [("gewehr", 0.35), ("bild", 0.6), ("laterne", 0.85)]}


class Canvas:
    def __init__(self, bounds, ppm):
        self.bx0, self.by0, self.bx1, self.by1 = bounds
        self.ppm = ppm
        self.w, self.h = int(round((self.bx1 - self.bx0) * ppm)), int(round((self.by1 - self.by0) * ppm))
        self.img = Image.new("RGB", (self.w, self.h), (14, 18, 18))

    def P(self, x, y):
        return ((x - self.bx0) * self.ppm, (self.by1 - y) * self.ppm)

    def Ps(self, pts):
        return [self.P(*p) for p in pts]

    def px(self, m):
        return max(1, int(round(m * self.ppm)))

    def draw(self):
        return ImageDraw.Draw(self.img, "RGBA")

    def bbox_px(self, g, pad=0.1):
        x0, y0, x1, y1 = g.bounds
        a = self.P(x0 - pad, y1 + pad)
        b = self.P(x1 + pad, y0 - pad)
        return max(0, int(a[0])), max(0, int(a[1])), min(self.w, int(b[0]) + 1), min(self.h, int(b[1]) + 1)

    def mask(self, g, rect=None):
        """L-Maske von g, im Pixelrechteck rect (x0, y0, x1, y1) oder bildweit."""
        rx0, ry0, rx1, ry1 = rect or (0, 0, self.w, self.h)
        m = Image.new("L", (rx1 - rx0, ry1 - ry0), 0)
        d = ImageDraw.Draw(m)
        for p in parts(g):
            d.polygon([(x - rx0, y - ry0) for x, y in self.Ps(p.exterior.coords)], fill=255)
            for hole in p.interiors:
                d.polygon([(x - rx0, y - ry0) for x, y in self.Ps(hole.coords)], fill=0)
        return m

    def fill_tile(self, tile, g, tone=None, feather=0):
        if g.is_empty:
            return
        r = self.bbox_px(g, 0.05 + feather)
        if r[2] <= r[0] or r[3] <= r[1]:
            return
        tw, th = tile.size
        crop = Image.new("RGB", (r[2] - r[0], r[3] - r[1]))
        for ty in range((r[1] // th) * th, r[3], th):
            for tx in range((r[0] // tw) * tw, r[2], tw):
                crop.paste(tile, (tx - r[0], ty - r[1]))
        if tone is not None and tone != 1.0:
            crop = Image.eval(crop, lambda v: min(255, int(v * tone)))
        m = self.mask(g, r)
        if feather:
            m = m.filter(ImageFilter.GaussianBlur(feather * self.ppm))
        self.img.paste(crop, r[:2], m)

    def paste_sprite(self, im, wx, wy):
        """Sprite aus graveyard_art (Ursprung = links unten bei wx, wy, gleiche ppm) aufs Bild (nur im eigenen Rechteck)."""
        x, y = self.P(wx, wy)
        x, y = int(round(x)), int(round(y - im.height))
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + im.width), min(self.h, y + im.height)
        if x1 <= x0 or y1 <= y0:
            return
        region = self.img.crop((x0, y0, x1, y1)).convert("RGBA")
        region.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)))
        self.img.paste(region.convert("RGB"), (x0, y0))

    def overlay(self, fn, blur=0.0, rect=None):
        """fn(draw) auf eigener RGBA-Ebene (optional nur im Pixelrechteck), weich, ueberblenden."""
        rx0, ry0, rx1, ry1 = rect or (0, 0, self.w, self.h)
        layer = Image.new("RGBA", (rx1 - rx0, ry1 - ry0), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer, "RGBA")
        fn(d, rx0, ry0)
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(max(1, blur * self.ppm)))
        base = self.img.convert("RGBA")
        base.alpha_composite(layer, (rx0, ry0))
        self.img = base.convert("RGB")


def parts(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


# ------------------------------------------------------------------ Gebiete

class Areas:
    def __init__(self, ctx):
        L = ctx.layout
        self.ctx = ctx
        bx0, by0, bx1, by1 = ctx.bounds
        self.all = box(bx0, by0, bx1, by1)
        self.walk = ctx.walk
        self.shells = unary_union(ctx.shells)
        cw = box(*CEMETERY_WALL)
        self.wall_ring = cw.buffer(CEMETERY_WALL_T, join_style=2).difference(cw)
        self.inside = cw
        self.field = cw.difference(self.walk).difference(self.shells).buffer(0)
        self.forest = self.all.difference(cw.buffer(CEMETERY_WALL_T, join_style=2))
        self.inner = {k: box(*b[3]) for k, b in ctx.buildings.items()}
        self.house = unary_union(list(self.inner.values()))
        self.outdoor = self.walk.difference(self.shells.buffer(0.01)).difference(self.house).buffer(0)
        self.clearing = {k: g for k, (_n, _s, g) in ctx.rooms.items() if k in ctx.clearings}
        self.paths = self.outdoor.difference(unary_union(list(self.clearing.values()))).buffer(0)
        avoid = [Point(p).buffer(0.75) for p in list(ctx.consoles.values()) + list(L.VENTS.values()) + list(L.CAMERAS) +
                 [L.EMERGENCY, L.SURVEILLANCE, L.ADMIN_TABLE, L.FREEPLAY]]
        for key, side, a, b, kind, o in ctx.doors:
            avoid.append(o.buffer(0.9))
        for _k, s, m in L.PROPS:
            avoid.append(shape_geom(s).buffer(0.25))
        self.avoid = prep(unary_union(avoid))
        self.spawn = Point(L.SPAWN).buffer(L.SPAWN_RADIUS + 0.3)

    def free(self, g):
        return not self.avoid.intersects(g)


def shape_geom(s):
    if s[0] == "rect":
        return box(*s[1:5])
    if s[0] == "circle":
        return Point(s[1], s[2]).buffer(s[3], 12)
    return affinity.scale(Point(s[1], s[2]).buffer(1, 16), s[3], s[4])


# ------------------------------------------------------------------ 1+2: Wald, Grabfelder

def forest(C, A_, rnd):
    """Waldmasse ausserhalb der Mauer: Kronen in vier Toenen, Lichtkanten, ein paar kahle Silhouetten."""
    def fn(d, ox, oy):
        P = lambda x, y: (C.P(x, y)[0] - ox, C.P(x, y)[1] - oy)
        bx0, by0, bx1, by1 = A_.ctx.bounds
        cols = [(18, 30, 26), (14, 24, 22), (22, 36, 30), (12, 20, 20), (26, 40, 34)]
        for _ in range(int((bx1 - bx0) * (by1 - by0) * 0.45)):
            x, y = rnd.uniform(bx0 - 1, bx1 + 1), rnd.uniform(by0 - 1, by1 + 1)
            if A_.inside.buffer(CEMETERY_WALL_T + 0.6).contains(Point(x, y)):
                continue
            r = rnd.uniform(0.7, 1.5)
            col = rnd.choice(cols)
            pts = HD.wobble_ellipse(x, y, r, r * 0.9, amp=0.08, seed=rnd.randint(0, 9999))
            d.polygon([P(*q) for q in pts], fill=col + (255,), outline=(6, 10, 10, 255))
            d.polygon([P(*q) for q in HD.wobble_ellipse(x - r * 0.25, y + r * 0.25, r * 0.5, r * 0.35, amp=0.04, seed=rnd.randint(0, 9999))],
                      fill=tuple(min(255, int(v * 1.35)) for v in col) + (255,))
    C.overlay(fn)


def grave_fields(C, A_, rnd, ppm):
    """Grabfelder: Gras, Reihen von Graebern, Familiengruefte, Eiben und kahle Baeume, alles gemalt (nicht begehbar)."""
    C.fill_tile(M.tile("wildgras", ppm, 21), A_.field.buffer(0.02))
    C.fill_tile(M.tile("wildgras", ppm, 22), A_.forest.buffer(0.02).intersection(A_.all), tone=0.55)
    fld = A_.field.buffer(-0.12)
    pf = prep(fld)
    placed = []                                                                       # (y, kind, shape, idx)
    # Baeume zuerst (grosse Kronen brauchen Platz), dann Grabreihen
    trees = []
    for k in range(2600):
        x, y = rnd.uniform(-23, 23), rnd.uniform(-19, 19)
        tree = "eibe" if rnd.random() < 0.55 else "baum_tot"
        foot = box(x - (0.9 if tree == "eibe" else 1.6), y - 0.4, x + (0.9 if tree == "eibe" else 1.6), y + (2.6 if tree == "eibe" else 3.4))
        if not pf.contains(foot):
            continue
        if any(Point(x, y).distance(Point(t[0], t[1])) < 2.8 for t in trees):
            continue
        trees.append((x, y, tree))
        if len(trees) >= 22:
            break
    trunks = [Point(x, y).buffer(0.55) for x, y, _t in trees]
    feet = []
    idx = 0
    for y in np.arange(18.9, -19.0, -0.3):
        xs = list(np.arange(-23.0, 23.0, 0.3))
        rnd.shuffle(xs)
        for x in xs:
            x = x + rnd.uniform(-0.06, 0.06)
            foot = box(x - 0.47, y - 1.5, x + 0.47, y + 0.9)
            if not pf.contains(foot):
                continue
            core = box(x - 0.5, y - 1.62, x + 0.5, y + 0.3)
            if any(core.intersects(f) for f in feet) or any(t.intersects(core) for t in trunks):
                continue
            feet.append(core)
            if rnd.random() < 0.12:                                                   # Luecken in den Reihen
                continue
            placed.append((y, "feldgrab", ("rect", x - 0.45, y - 1.5, x + 0.45, y), idx))
            idx += 1
    for x, y, tree in trees:
        placed.append((y, tree, ("rect", x - 0.4, y - 0.2, x + 0.4, y + 0.2), idx))
        idx += 1
    for k in range(40):                                                               # Bueesche zwischen den Reihen
        x, y = rnd.uniform(-23, 23), rnd.uniform(-19, 19)
        r = rnd.uniform(0.3, 0.5)
        if pf.contains(box(x - r - 0.2, y - r, x + r + 0.3, y + r * 1.4)):
            placed.append((y, "busch", ("rect", x - r, y - r * 0.5, x + r, y + r * 0.5), idx))
            idx += 1
    placed.sort(key=lambda t: -t[0])                                                  # Norden zuerst
    for _y, kd, shp, i in placed:
        im, wx, wy, _b = GA.draw(kd, shp, i, ppm)
        C.paste_sprite(im, wx, wy)
    print(f"  grave fields: {sum(1 for p in placed if p[1] == 'feldgrab')} graves, {len(trees)} trees")


# ------------------------------------------------------------------ 3: Boeden

def floors(C, A_, ppm):
    ctx = A_.ctx
    C.fill_tile(M.tile("kies", ppm, 31), A_.paths.buffer(0.03), tone=0.92)
    for key, g in A_.clearing.items():
        if key == "belltower":
            C.fill_tile(M.tile("rasen", ppm, 33), g, tone=0.95)
            plaza = Point(-18.0, 12.6).buffer(3.4, 32).intersection(g)
            C.fill_tile(M.tile("kopfstein", ppm, 34), plaza, feather=0.12)
        elif key == "roost":
            C.fill_tile(M.tile("rasen", ppm, 35), g, tone=0.92)
            C.fill_tile(M.tile("erde", ppm, 36), Point(-9.5, 1.8).buffer(1.7, 24).intersection(g), feather=0.25)
        else:
            C.fill_tile(M.tile("rasen", ppm, 37 + len(key)), g)
    for key, inner in A_.inner.items():
        mat, seed, tone, kw = ROOM_MAT[key]
        C.fill_tile(M.tile(mat, ppm, seed, **kw), inner, tone=tone)
    for key, side, a, b, kind, o in ctx.doors:                                        # Schwellen
        C.fill_tile(M.tile("grabplatten", ppm, 41), o.buffer(0.02), tone=0.85)


def trails(C, A_, ppm, rnd):
    """Ausgetretene Pfade ueber das Gras der Lichtungen (Erde mit weichem Rand) zwischen den Eingaengen."""
    lines = [
        [(0.0, 8.0), (0.6, 10.0), (2.2, 12.2), (4.0, 12.6)], [(-2.6, 13.0), (0.0, 13.2), (2.4, 12.8)],
        [(10.6, 13.0), (8.6, 13.2), (6.2, 12.9)], [(-14.4, 13.0), (-15.8, 12.8)], [(-18.0, 9.2), (-18.0, 10.6)],
        [(-8.0, 5.8), (-8.4, 4.0), (-9.0, 3.0)], [(-12.0, 0.0), (-10.6, 0.6)], [(-7.0, 0.0), (-8.4, 0.8)],
    ]
    g = unary_union([LineString(HD.wobble(l, amp=0.08, seed=k, step=0.4)).buffer(0.38, 8) for k, l in enumerate(lines)])
    g = g.intersection(unary_union(list(A_.clearing.values())))
    C.fill_tile(M.tile("erde", ppm, 45), g, tone=0.9, feather=0.03)

    def edge(d, ox, oy):                                                              # Grasbueschel am Pfadrand, Fussspuren
        P = lambda x, y: (C.P(x, y)[0] - ox, C.P(x, y)[1] - oy)
        for part in parts(g):
            ring = part.exterior
            n = int(ring.length / 0.09)
            for k in range(n):
                q = ring.interpolate(k / n, normalized=True)
                for seg in HD.tuft(q.x, q.y, rnd, n=3, h=0.07):
                    d.line([P(*v) for v in seg], fill=rnd.choice([(84, 118, 88, 255), (60, 88, 68, 255), (104, 136, 100, 255)]), width=C.px(0.014))
    C.overlay(edge)


def curbs(C, A_, rnd):
    """Bordsteine: kleine Granitsteine entlang der Kieswege, wo Kies an Grabfeld grenzt."""
    edge = A_.paths.boundary
    near_field = A_.field.buffer(0.05)
    segs = []
    for line in (edge.geoms if hasattr(edge, "geoms") else [edge]):
        coords = list(line.coords)
        for i in range(len(coords) - 1):
            a, b = coords[i], coords[i + 1]
            ln = math.dist(a, b)
            if ln < 0.05:
                continue
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if near_field.contains(Point(mid)):
                segs.append((a, b, ln))

    def fn(d, ox, oy):
        P = lambda x, y: (C.P(x, y)[0] - ox, C.P(x, y)[1] - oy)
        for a, b, ln in segs:
            ux, uy = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
            nx, ny = -uy, ux
            test = Point(a[0] + ux * ln / 2 + nx * 0.1, a[1] + uy * ln / 2 + ny * 0.1)
            if not A_.paths.contains(test):
                nx, ny = -nx, -ny
            t = 0.0
            while t < ln:
                s = min(rnd.uniform(0.2, 0.28), ln - t)
                if s < 0.06:
                    break
                p0 = (a[0] + ux * t, a[1] + uy * t)
                p1 = (a[0] + ux * (t + s - 0.02), a[1] + uy * (t + s - 0.02))
                q = [p0, p1, (p1[0] + nx * 0.12, p1[1] + ny * 0.12), (p0[0] + nx * 0.12, p0[1] + ny * 0.12)]
                tone = rnd.uniform(0.85, 1.12)
                col = tuple(int(v * tone) for v in (128, 128, 136))
                d.polygon([P(*v) for v in q], fill=col + (255,), outline=(30, 30, 36, 255))
                d.line([P(*q[0]), P(*q[1])], fill=(168, 170, 180, 200), width=max(1, C.px(0.02)))
                t += s
    C.overlay(fn)


# ------------------------------------------------------------------ 4: Bodendeko je Raum

def wobble_poly(d, P, pts, fill, outline=None, w=1):
    d.polygon([P(*q) for q in pts], fill=fill, outline=outline)


def decor(C, A_, ppm, rnd):
    L = A_.ctx.layout
    px = C.px

    def fn(d, ox, oy):
        P = lambda x, y: (C.P(x, y)[0] - ox, C.P(x, y)[1] - oy)
        # Kapelle: roter Laeufer vom Suedeingang zum Altar mit Goldborte, Wachstropfen, Grabplatte vor dem Altar
        x0, x1 = -0.62, 0.62
        d.rectangle([P(x0, 3.35), P(x1, -4.0)], fill=(112, 30, 40, 255))
        for k in range(14):                                                           # Florstreifen
            yy = -4.0 + k * 0.53
            d.line([P(x0 + 0.08, yy), P(x1 - 0.08, yy)], fill=(96, 24, 34, 255), width=px(0.03))
        for xx in (x0 + 0.05, x1 - 0.05):
            d.line([P(xx, -4.0), P(xx, 3.35)], fill=(196, 160, 80, 255), width=px(0.04))
        for k in range(8):
            yy = -3.6 + k * 0.95
            d.polygon([P(0, yy + 0.12), P(0.12, yy), P(0, yy - 0.12), P(-0.12, yy)], outline=(196, 160, 80, 200))
        for _ in range(9):
            x, y = rnd.uniform(-0.5, 0.5), rnd.uniform(-3.8, 3.0)
            d.ellipse([P(x - 0.03, y + 0.02), P(x + 0.03, y - 0.02)], fill=(236, 226, 196, 210))
        # Gruft: Bodenplatte "Ossuarium" mit Eisenring, Kerzenreste, Staub; Treppe in die Tiefe hinter dem Sarkophag
        gx, gy = 17.0, 14.6
        d.rectangle([P(gx - 0.7, gy + 0.5), P(gx + 0.7, gy - 0.5)], fill=(150, 150, 146, 255), outline=INK, width=px(0.03))
        d.rectangle([P(gx - 0.6, gy + 0.4), P(gx + 0.6, gy - 0.4)], outline=(90, 90, 88, 255), width=px(0.015))
        d.ellipse([P(gx - 0.12, gy + 0.09), P(gx + 0.12, gy - 0.09)], outline=(70, 70, 76, 255), width=px(0.03))
        for k in range(3):
            d.line([P(gx - 0.45, gy - 0.25 + k * 0.06), P(gx + 0.45, gy - 0.25 + k * 0.06)], fill=(100, 100, 98, 255), width=px(0.012))
        for k, (x, y) in enumerate(((14.6, 15.3), (15.6, 11.0), (21.3, 11.6), (21.0, 13.9))):
            for j in range(3):
                d.ellipse([P(x + j * 0.08 - 0.03, y + 0.02), P(x + j * 0.08 + 0.03, y - 0.03)], fill=(232, 222, 190, 230))
        # Leichenhalle: Ablauf mit Gitter, Rinne, Flecken
        dx, dy = 18.4, 0.0
        d.ellipse([P(dx - 0.2, dy + 0.15), P(dx + 0.2, dy - 0.15)], fill=(70, 74, 76, 255), outline=INK, width=px(0.02))
        for k in range(5):
            d.line([P(dx - 0.15 + k * 0.075, dy + 0.1), P(dx - 0.15 + k * 0.075, dy - 0.1)], fill=(30, 32, 34, 255), width=px(0.015))
        for x, y, r in ((17.7, -1.0, 0.18), (20.1, 0.4, 0.14), (18.8, -2.4, 0.1)):
            if A_.free(Point(x, y).buffer(r)):
                pts = HD.wobble_ellipse(x, y, r, r * 0.7, amp=r * 0.2, seed=int(x * 10))
                d.polygon([P(*q) for q in pts], fill=(110, 30, 36, 160))
        # Krematorium: Asche und Glutspur vor dem Ofen, Fussspuren in der Asche
        for k in range(30):
            x, y = rnd.uniform(-21.5, -19.2), rnd.uniform(-14.4, -13.1)
            d.ellipse([P(x - 0.05, y + 0.03), P(x + 0.05, y - 0.03)], fill=(150, 146, 140, 140))
        for k in range(6):
            x, y = -20.0 + k * 0.45, -14.0 - (k % 2) * 0.16
            d.ellipse([P(x - 0.06, y + 0.04), P(x + 0.06, y - 0.04)], fill=(40, 36, 36, 160))
        # Brunnenhaus: Pfuetzen um den Brunnen, Rinne zum Ablauf
        for x, y, r in ((-9.4, 12.2, 0.35), (-6.8, 13.9, 0.25), (-7.6, 11.6, 0.2)):
            pts = HD.wobble_ellipse(x, y, r, r * 0.6, amp=r * 0.15, seed=int(-x * 10))
            d.polygon([P(*q) for q in pts], fill=(40, 60, 90, 120))
            d.line([P(x - r * 0.4, y + r * 0.2), P(x - r * 0.1, y + r * 0.3)], fill=(190, 210, 240, 120), width=px(0.02))
        d.line([P(-8.0, 12.2), P(-8.0, 10.6), P(-8.4, 10.0)], fill=(36, 40, 46, 200), width=px(0.12))
        # Verwaltung: Teppich unter dem Grabplan-Tisch
        rx0, ry0, rx1, ry1 = -9.6, -15.2, -6.4, -12.8
        d.rectangle([P(rx0, ry1), P(rx1, ry0)], fill=(52, 76, 64, 255), outline=INK, width=px(0.03))
        d.rectangle([P(rx0 + 0.12, ry1 - 0.12), P(rx1 - 0.12, ry0 + 0.12)], outline=(176, 150, 90, 255), width=px(0.03))
        for k in range(int((rx1 - rx0) / 0.25)):
            x = rx0 + 0.18 + k * 0.25
            d.line([P(x, ry0 - 0.02), P(x, ry0 - 0.1)], fill=(176, 150, 90, 255), width=px(0.012))
            d.line([P(x, ry1 + 0.02), P(x, ry1 + 0.1)], fill=(176, 150, 90, 255), width=px(0.012))
        # Waechterhaus: Flickenteppich (oval) vor dem Ofen
        cx, cy = 19.8, -14.6
        for k, col in enumerate(((120, 60, 50), (150, 130, 90), (70, 90, 110), (130, 80, 60), (90, 110, 80))):
            r = 1.2 - k * 0.2
            d.ellipse([P(cx - r, cy + r * 0.6), P(cx + r, cy - r * 0.6)], fill=col + (255,), outline=INK if k == 0 else None, width=px(0.02))
        # Laternenschuppen: Oelflecken
        for x, y, r in ((8.6, -14.6, 0.3), (9.6, -13.6, 0.18)):
            pts = HD.wobble_ellipse(x, y, r, r * 0.6, amp=r * 0.2, seed=int(x * 7))
            d.polygon([P(*q) for q in pts], fill=(20, 20, 26, 120))
            d.line([P(x - r * 0.4, y), P(x + r * 0.2, y + r * 0.2)], fill=(120, 100, 160, 90), width=px(0.03))
        # Sargkammer: Saegespaene und Holzlocken um die Hobelbank und den Sargbock
        for _ in range(60):
            x, y = rnd.uniform(-19.6, -14.6), rnd.uniform(-2.2, 2.6)
            if A_.free(Point(x, y).buffer(0.05)):
                a = rnd.uniform(0, math.tau)
                d.arc([P(x - 0.05, y + 0.03), P(x + 0.05, y - 0.03)], math.degrees(a), math.degrees(a) + 200, fill=(200, 170, 120, 220), width=px(0.012))
        # Waechtersteine: Runenkreis (Kalk), Runen, Kerzenreste
        cx, cy = 9.5, 0.0
        for r, wdt in ((1.84, 0.05), (1.64, 0.025)):        # seit 24.10. 80 % (User)
            d.ellipse([P(cx - r, cy + r * 0.8), P(cx + r, cy - r * 0.8)], outline=(214, 220, 206, 170), width=px(wdt))
        for k in range(12):
            a = k / 12 * math.tau
            rx, ry = cx + 1.744 * math.cos(a), cy + 1.744 * 0.8 * math.sin(a)
            rr = random.Random(k)
            pts = [(rx + rr.uniform(-0.07, 0.07), ry + rr.uniform(-0.07, 0.07)) for _ in range(3)]
            d.line([P(*q) for q in pts], fill=(214, 220, 206, 190), width=px(0.022))
        for k in range(5):
            a1 = math.pi / 2 + k * 2 * math.tau / 5
            a2 = math.pi / 2 + (k + 1) * 2 * math.tau / 5
            d.line([P(cx + 1.52 * math.cos(a1), cy + 1.216 * math.sin(a1)), P(cx + 1.52 * math.cos(a2), cy + 1.216 * math.sin(a2))],
                   fill=(214, 220, 206, 90), width=px(0.02))
        # Rabenhorst: Federn und Kot unter dem Baum
        for _ in range(26):
            x, y = rnd.uniform(-11.0, -8.0), rnd.uniform(0.6, 3.4)
            if rnd.random() < 0.5:
                a = rnd.uniform(0, math.pi)
                d.line([P(x, y), P(x + 0.12 * math.cos(a), y + 0.12 * math.sin(a))], fill=(30, 30, 38, 230), width=px(0.03))
                d.line([P(x, y), P(x + 0.12 * math.cos(a), y + 0.12 * math.sin(a))], fill=(80, 90, 120, 160), width=px(0.008))
            else:
                d.ellipse([P(x - 0.02, y + 0.015), P(x + 0.02, y - 0.015)], fill=(220, 220, 214, 200))
        # Laub auf allen Aussenflaechen
        for _ in range(int(A_.outdoor.area * 0.9)):
            x, y = rnd.uniform(-22, 22), rnd.uniform(-19, 19)
            if not A_.outdoor.contains(Point(x, y)):
                continue
            a = rnd.uniform(0, math.pi)
            ln = rnd.uniform(0.06, 0.1)
            col = rnd.choice(GA.LEAF)
            q = [(x + ln * math.cos(a), y + ln * math.sin(a)), (x - 0.25 * ln * math.sin(a), y + 0.25 * ln * math.cos(a)),
                 (x - ln * math.cos(a), y - ln * math.sin(a)), (x + 0.25 * ln * math.sin(a), y - 0.25 * ln * math.cos(a))]
            d.polygon([P(*v) for v in q], fill=col, outline=(30, 20, 16, 200))
    C.overlay(fn)
    # Alte Graeber: Grabbetten vor den acht Grabsteinen (gleiche Zeichner wie die Grabfelder)
    styles = ["mound", "curb", "flowers", "mound", "ivy", "curb", "mound", "flowers"]
    for k, (gx, gy) in enumerate([(x, y) for x in (0.5, 3.0, 5.5, 8.0) for y in (10.4, 15.8)]):
        y_top, y_bot = gy - 0.22, gy - 1.6
        c = GA.A.Canvas(gx - 0.65, y_bot - 0.2, gx + 0.65, y_top + 0.2, ppm)
        brnd = random.Random(k * 17 + 3)
        GA.grave_bed(c, gx - 0.5, gx + 0.5, y_top, y_bot, styles[k], brnd, seed=k)
        if k % 2 == 0:
            GA.grave_light(c, gx - 0.25, y_top - 0.3, lit=True)
        if k % 3 == 1:
            GA.bouquet(c, gx + 0.2, y_top - 0.32, brnd, dead=k % 2 == 1)
        if k == 5:
            GA.wreath(c, gx, (y_top + y_bot) / 2, 0.17, brnd)
        C.paste_sprite(c.finish(), c.x0, c.y0)


# ------------------------------------------------------------------ 5: Schatten, Wandkronen, Stirnseiten

def ambient(C, walk):
    s = 8
    bx0, by0, bx1, by1 = C.bx0, C.by0, C.bx1, C.by1
    small = Image.new("L", (int((bx1 - bx0) * s), int((by1 - by0) * s)), 255)
    d = ImageDraw.Draw(small)
    Pt = lambda x, y: ((x - bx0) * s, (by1 - y) * s)
    for p in parts(walk):
        d.polygon([Pt(*q) for q in p.exterior.coords], fill=0)
        for h in p.interiors:
            d.polygon([Pt(*q) for q in h.coords], fill=255)
    small = small.filter(ImageFilter.GaussianBlur(0.32 * s)).resize(C.img.size, Image.BICUBIC)
    amount = ImageChops.multiply(small, C.mask(walk)).point(lambda v: int(v * 0.62))
    C.img = Image.composite(Image.new("RGB", C.img.size, (6, 6, 12)), C.img, amount)


NORTH_FACE = 0.95          # Bildhoehe der Nordwand-Stirnseite innen (Wandhoehe * K)


def building_mass(A_):
    """Sichtbare Wandmasse je Gebaeude: Schale plus die nach Norden versetzte Krone ueber der Nordwand (schraege
    Aufsicht: die Nordwand zeigt ihre Stirnseite, ihre Krone liegt um die Wandhoehe weiter noerdlich). Ohne
    begehbare Flaeche (Wege vor einer Nordtuer bleiben frei)."""
    out = {}
    for key, inner in A_.inner.items():
        x0, y0, x1, y1 = inner.bounds
        m = box(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + NORTH_FACE + 0.5).difference(inner)
        out[key] = m.difference(A_.walk).buffer(0)
    return out


def wall_tops(C, A_, ppm, rnd):
    """Wandkronen (dunkler Schiefer, helle Abdeckkante, Moos) der Gebaeude und der Friedhofsmauer."""
    masses = building_mass(A_)
    A_.masses = masses
    faces_g = unary_union([box(g.bounds[0], g.bounds[1], g.bounds[2], g.bounds[3] + NORTH_FACE) for g in A_.inner.values()])
    tops = unary_union(list(masses.values()) + [A_.wall_ring]).difference(faces_g).buffer(0)
    tile = M.tile("grabplatten", ppm, 51)
    tile = Image.eval(tile, lambda v: int(v * 0.42))
    C.fill_tile(tile, tops)

    def sh(d, ox, oy):
        P = lambda x, y: (C.P(x, y)[0] - ox, C.P(x, y)[1] - oy)
        for g in masses.values():
            for q in parts(affinity.translate(g, 0.18, -0.12).difference(g).difference(A_.walk)):
                d.polygon([P(*c) for c in q.exterior.coords], fill=(0, 0, 8, 110))
    C.overlay(sh, blur=0.08)

    def fn(d, ox, oy):
        P = lambda x, y: (C.P(x, y)[0] - ox, C.P(x, y)[1] - oy)
        for p in parts(tops):
            for ring in [p.exterior] + list(p.interiors):
                pts = HD.wobble(list(ring.coords), amp=0.006, seed=int(p.area * 10), step=0.1, closed=True)
                d.line([P(*q) for q in pts], fill=(110, 112, 124, 255), width=C.px(0.06), joint="curve")
        for _ in range(int(tops.area * 6)):
            x, y = rnd.uniform(-24, 24), rnd.uniform(-20, 20)
            if tops.contains(Point(x, y)):
                r = rnd.uniform(0.04, 0.09)
                d.ellipse([P(x - r, y + r * 0.7), P(x + r, y - r * 0.7)], fill=(70, 104, 64, 170))
    C.overlay(fn)


def face_depth(solid, x0, x1, y, hmax):
    xs = [x0 + 0.05 + k * 0.1 for k in range(max(1, int((x1 - x0 - 0.1) / 0.1) + 1))]
    depths = []
    for x in xs:
        h = 0.0
        while h + 0.05 <= hmax + 1e-6 and solid.contains(Point(x, y + h + 0.04)):
            h += 0.05
        depths.append(h)
    depths.sort()
    return min(hmax, depths[len(depths) // 3])


def paste_face(C, img, solid_g, xa, xb, y, fh):
    """Stirnseite (RGBA, Hoehe fh in Bildmetern) ueber der Kante y (Nordrichtung) einsetzen, auf solid beschnitten."""
    face = box(xa, y, xb, y + fh).intersection(solid_g.buffer(0.001))
    if face.is_empty:
        return
    x, yy = C.P(xa, y + fh)
    x, yy = int(round(x)), int(round(yy))
    w, h = int(round((xb - xa) * C.ppm)), int(round(fh * C.ppm))
    img = img.resize((max(1, w), max(1, h)))
    m = C.mask(face, (x, yy, x + w, yy + h))
    m = ImageChops.multiply(m, img.getchannel("A"))
    C.img.paste(img.convert("RGB"), (x, yy), m)


def faces(C, A_, ppm):
    """Stirnseiten der Nordwaende (innen: Raumstil, aussen: Zaun/Hecke/Fassade) und Suedfassaden ueber dem Gras."""
    walk = A_.walk
    solid = box(-30, -30, 30, 30).difference(walk)
    psolid = prep(solid)
    shadows = []
    n = 0
    for p in parts(walk):
        for ring in [list(p.exterior.coords)] + [list(h.coords) for h in p.interiors]:
            for i in range(len(ring) - 1):
                (x0, y0), (x1, y1) = ring[i], ring[i + 1]
                if abs(y1 - y0) > 1e-6 or abs(x1 - x0) < 0.05:
                    continue
                y = y0
                xa, xb = min(x0, x1), max(x0, x1)
                mx = (xa + xb) / 2
                if not (psolid.contains(Point(mx, y + 0.05)) and walk.contains(Point(mx, y - 0.05))):
                    continue
                room = A_.ctx.room_at(mx, y - 0.3)
                in_house = A_.house.contains(Point(mx, y - 0.05))
                north_shell = A_.shells.contains(Point(mx, y + 0.1))
                if in_house:
                    style = WALL_STYLE.get(room, "stein")
                    hmax = NORTH_FACE
                elif north_shell:
                    style, hmax = "fassade", 0.5
                elif room in ("belltower", "roost", "wards"):
                    style, hmax = "hecke", 0.95
                else:
                    style, hmax = "zaun", 0.8
                fh = NORTH_FACE if in_house else face_depth(psolid, xa, xb, y, hmax)
                if fh < 0.15:
                    continue
                seed = int(abs(xa) * 7 + abs(y) * 3)
                if style == "holz":
                    img = M.wall_holz(xb - xa, fh, ppm, seed, tools=WALL_TOOLS.get(room))
                else:
                    img = M.wall_front(xb - xa, fh, style, ppm, seed)
                paste_face(C, img, solid, xa, xb, y, fh)
                shadows.append(box(xa, y - 0.32, xb, y).intersection(walk))
                n += 1
    # Suedfassaden der Gebaeude, wo suedlich Grabfeld liegt (die Wanddicke zeigt die Aussenwand)
    for key, b in A_.ctx.buildings.items():
        x0, y0, x1, y1 = b[3]
        yb = y0 - 0.5
        segs = box(x0 - 0.5, yb - 0.01, x1 + 0.5, yb + 0.01).difference(walk.buffer(0.02))
        for s_ in parts(segs.buffer(0)):
            sx0, _, sx1, _ = s_.bounds
            if sx1 - sx0 < 0.4:
                continue
            img = M.wall_fassade(sx1 - sx0, 0.5, ppm, int(abs(sx0) * 11 + abs(yb)), window=key not in ("mausoleum",))
            paste_face(C, img, A_.shells, sx0, sx1, yb, 0.5)
    # Friedhofsmauer: Innenseite der Nordmauer sichtbar
    wx0, wy0, wx1, wy1 = CEMETERY_WALL
    img = M.wall_front(wx1 - wx0, CEMETERY_WALL_T, "stein", ppm, 77)
    paste_face(C, img, A_.wall_ring, wx0, wx1, wy1, CEMETERY_WALL_T)

    def fn(d, ox, oy):
        P = lambda x, y: (C.P(x, y)[0] - ox, C.P(x, y)[1] - oy)
        for g in shadows:
            for q in parts(g):
                d.polygon([P(*c) for c in q.exterior.coords], fill=(0, 0, 10, 100))
    C.overlay(fn, blur=0.1)
    return n


def gate(C, ppm):
    """Haupttor in der Suedmauer unter dem Torhaus: Torpfeiler mit Laternen, Gittertor, Weg in den Wald."""
    def fn(d, ox, oy):
        P = lambda x, y: (C.P(x, y)[0] - ox, C.P(x, y)[1] - oy)
        wy0 = CEMETERY_WALL[1]
        d.rectangle([P(-1.6, wy0 + 0.6), P(1.6, -21.0)], fill=(70, 62, 52, 255))       # Weg nach draussen
        for k in range(24):
            x = random.Random(k).uniform(-1.4, 1.4)
            y = random.Random(k + 50).uniform(-21, wy0)
            d.ellipse([P(x - 0.04, y + 0.03), P(x + 0.04, y - 0.03)], fill=(110, 104, 96, 255))
        d.rectangle([P(-1.5, wy0 + 0.1), P(1.5, wy0 - CEMETERY_WALL_T - 0.1)], fill=(24, 24, 28, 255))
        for k in range(15):                                                           # Gitterstaebe
            x = -1.45 + k * 0.2
            d.line([P(x, wy0 + 0.05), P(x, wy0 - 0.65)], fill=(70, 72, 82, 255), width=C.px(0.04))
        d.line([P(-1.5, wy0 - 0.3), P(1.5, wy0 - 0.3)], fill=(70, 72, 82, 255), width=C.px(0.05))
        for sx in (-1, 1):
            x = sx * 1.85
            d.rectangle([P(x - 0.35, wy0 + 0.25), P(x + 0.35, wy0 - 0.85)], fill=(96, 96, 106, 255), outline=INK, width=C.px(0.04))
            d.rectangle([P(x - 0.25, wy0 + 0.15), P(x + 0.25, wy0 - 0.75)], fill=(120, 120, 130, 255))
            d.ellipse([P(x - 0.16, wy0 - 0.15), P(x + 0.16, wy0 - 0.45)], fill=(255, 220, 140, 255), outline=INK, width=C.px(0.03))
    C.overlay(fn)
    glow(C, [(-1.85, CEMETERY_WALL[1] - 0.3, 1.6, (255, 200, 120), 0.45), (1.85, CEMETERY_WALL[1] - 0.3, 1.6, (255, 200, 120), 0.45)])


# ------------------------------------------------------------------ 6: Licht, Grading, Tusche

def glow(C, lights):
    """Lichtlachen: (x, y, r, Farbe, Staerke) - weicher Verlauf, additiv aufgehellt."""
    for x, y, r, col, s in lights:
        rx0, ry0 = C.P(x - r, y + r)
        rx1, ry1 = C.P(x + r, y - r)
        rx0, ry0, rx1, ry1 = int(rx0), int(ry0), int(rx1), int(ry1)
        w, h = rx1 - rx0, ry1 - ry0
        if w < 4:
            continue
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dd = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        f = np.clip(1 - dd, 0, 1) ** 1.8 * s
        cx0, cy0 = max(0, rx0), max(0, ry0)
        cx1, cy1 = min(C.w, rx1), min(C.h, ry1)
        if cx1 <= cx0 or cy1 <= cy0:
            continue
        f = f[cy0 - ry0:cy1 - ry0, cx0 - rx0:cx1 - rx0]
        a = np.asarray(C.img.crop((cx0, cy0, cx1, cy1))).astype(np.float32)
        col_ = np.array(col, np.float32)
        a = a + (col_ * 0.55 - a * 0.25) * f[..., None] + a * f[..., None] * 0.35
        C.img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (cx0, cy0))


def lights(C, A_):
    L = A_.ctx.layout
    out = []
    for kd, s, _m in L.PROPS:
        x0, y0, x1, y1 = GA.A.shape_bounds(s)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if kd == "laternenpfahl":
            out.append((cx + 0.1, cy - 0.3, 2.3, (255, 196, 120), 0.5))
        elif kd == "kandelaber":
            out.append((cx, cy - 0.2, 1.8, (255, 200, 130), 0.45))
        elif kd == "opferkerzen":
            out.append((cx, cy - 0.3, 1.4, (255, 190, 110), 0.45))
        elif kd == "ofen":
            out.append((cx + 0.2, y0 - 0.6, 2.6, (255, 120, 50), 0.55))
        elif kd == "kanonenofen":
            out.append((cx, cy - 0.3, 1.5, (255, 130, 60), 0.45))
        elif kd == "altar":
            out.append((cx, y0 - 0.3, 2.2, (255, 210, 150), 0.35))
    out.append((-8.0, -11.9, 1.6, (255, 210, 140), 0.35))                             # Schreibtischlampe Verwaltung
    out.append((19.2, -12.0, 1.8, (170, 200, 255), 0.35))                             # Spiegelpult Waechterhaus (kalt)
    out.append((18.4, 0.6, 2.8, (190, 220, 210), 0.3))                                # Leichenhalle (kalt, Neon)
    glow(C, out)


def moonlight(C, A_, rnd):
    """Kalte Mondflecken auf Lichtungen und Wegen (durchs Laub gebrochen)."""
    out = []
    for key, g in A_.clearing.items():
        for _ in range(3):
            p = g.representative_point()
            x, y = p.x + rnd.uniform(-2, 2), p.y + rnd.uniform(-2, 2)
            if g.contains(Point(x, y)):
                out.append((x, y, rnd.uniform(1.2, 2.0), (150, 170, 210), 0.22))
    glow(C, out)


def grade(C):
    img = C.img
    img = Image.blend(img, ImageOps.grayscale(img).convert("RGB"), 0.12)
    r, g, b = img.split()
    img = Image.merge("RGB", (r.point(lambda v: int(v * 0.86)), g.point(lambda v: int(v * 0.92)), b.point(lambda v: min(255, int(v * 1.0 + 4)))))
    C.img = img


def ink(C, walk):
    d = C.draw()
    for k, p in enumerate(parts(walk)):
        for j, ring in enumerate([p.exterior] + list(p.interiors)):
            pts = HD.wobble(list(ring.coords), amp=0.008, seed=900 + k * 50 + j, step=0.1, closed=True)
            HD.ink(d, C.Ps(pts), INK, max(2, C.px(0.05)), seed=k * 50 + j, var=0.2, closed=True)


def render(ctx, ppm):
    rnd = random.Random(17)
    C = Canvas(ctx.bounds, ppm)
    A_ = Areas(ctx)
    print("  forest")
    forest(C, A_, rnd)
    print("  grave fields")
    grave_fields(C, A_, rnd, ppm)
    print("  floors")
    floors(C, A_, ppm)
    trails(C, A_, ppm, rnd)
    print("  decor")
    decor(C, A_, ppm, rnd)
    curbs(C, A_, rnd)
    ambient(C, ctx.walk)
    print("  walls")
    wall_tops(C, A_, ppm, rnd)
    n = faces(C, A_, ppm)
    gate(C, ppm)
    print("  light")
    lights(C, A_)
    moonlight(C, A_, rnd)
    grade(C)
    ink(C, ctx.walk)
    C.img = HD.paper_grain(C.img, 0.025, seed=4)
    print(f"graveyard floor: {C.img.size}, {n} wall faces")
    return C.img
