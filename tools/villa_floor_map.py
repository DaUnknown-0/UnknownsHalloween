# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_floor_map.py - das ganze Bodenbild von Hollowmere Manor (grosse Karte, Plan-Lage).
#
# Baut auf dem abgenommenen Stilblatt auf (villa_floor.py: Materialkacheln, Wandstirnseiten, Bodendetails)
# und folgt dem Aufbau von park_floor.render (Unknown's Atlas):
#   1. Leerraum zwischen den Bereichen als dunkle Baum- und Heckenmasse
#   2. Boden je Bereich aus der passenden Kachel, Schwellen in den Oeffnungen, Teppiche
#   3. Wandkrone (Haus dunkel, Garten Hecke), Stirnseiten der Nordwaende in der Wandmasse
#   4. Umgebungsschatten an allen Raendern, Kontaktschatten unter den Nordwaenden, Tuschekante
#   5. Bodendeko (Filmset und Horror), mit Abstand zu Konsolen, Vents und Oeffnungen
#   6. Dunkle Raeume (villa_layout.DARK) etwas dunkler, Papierkorn
# Koordinaten: Plan-Meter (x nach Osten, y nach Sueden) = Bildrichtung; Pixel = Meter * ppm.

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep

import handdraw as HD
import villa_floor as VF
import villa_layout as L

HERE = Path(__file__).resolve().parent
W_M, H_M = 50.0, 36.0
OUTLINE = (14, 12, 18)

MAT = {
    "kitchen": "fliesen_schachbrett", "laundry": "steinplatten", "seance": "parkett", "radio": "dielen",
    "boxroom": "dielen", "observatory": "dielen", "boiler": "steinplatten", "westhall": "parkett",
    "library": "teppich", "chapel": "steinplatten", "hall": "parkett", "booth": "dielen",
    "vestibule": "fliesen_schachbrett", "makeup": "dielen", "gallery": "parkett", "trophy": "parkett",
    "fireplace": "teppich", "study": "teppich", "terrace": "terrasse", "driveway": "kies",
    "crewcamp": "wiese", "greenhouse": "glashausfliesen", "fountain": "terrasse", "graveyard": "friedhofserde",
    "crypt": "steinplatten",
}
GARDEN = {"terrace", "driveway", "crewcamp", "fountain", "graveyard"}
STYLE = {  # Wandstirnseite ueber dem Raum (Nordwand)
    "kitchen": "putz", "laundry": "putz", "boxroom": "putz", "boiler": "stein", "chapel": "stein",
    "crypt": "stein", "greenhouse": "glashaus",
}
HOUSE = box(-0.3, -0.3, 34.3, 24.3)
WALL_TOP = (36, 26, 32)
HEDGE_TOP = (26, 46, 32)


class Canvas:
    def __init__(self, ppm):
        self.ppm = ppm
        self.w, self.h = int(round(W_M * ppm)), int(round(H_M * ppm))
        self.img = Image.new("RGB", (self.w, self.h), (12, 14, 14))

    def P(self, x, y):
        return (x * self.ppm, y * self.ppm)

    def Pw(self, x, y):
        """Fuer die Bodendetails aus villa_floor.py, die in Weltrichtung rechnen (y nach oben):
        dort mit y = -Plan-y aufrufen."""
        return (x * self.ppm, -y * self.ppm)

    def draw(self):
        return ImageDraw.Draw(self.img, "RGBA")

    def mask(self, g, size=None, origin=(0.0, 0.0)):
        w, h = size or (self.w, self.h)
        m = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(m)
        ox, oy = origin
        for p in parts(g):
            d.polygon([((x - ox) * self.ppm, (y - oy) * self.ppm) for x, y in p.exterior.coords], fill=255)
            for hole in p.interiors:
                d.polygon([((x - ox) * self.ppm, (y - oy) * self.ppm) for x, y in hole.coords], fill=0)
        return m

    def fill_tile(self, tile, g, tone=None):
        """Kachel (am Weltraster ausgerichtet) in die Flaeche g legen, nur im Rechteck um g."""
        if g.is_empty:
            return
        x0, y0, x1, y1 = g.bounds
        px0, py0 = max(0, int(x0 * self.ppm) - 2), max(0, int(y0 * self.ppm) - 2)
        px1, py1 = min(self.w, int(x1 * self.ppm) + 3), min(self.h, int(y1 * self.ppm) + 3)
        if px1 <= px0 or py1 <= py0:
            return
        tw, th = tile.size
        crop = Image.new("RGB", (px1 - px0, py1 - py0))
        for ty in range((py0 // th) * th, py1, th):
            for tx in range((px0 // tw) * tw, px1, tw):
                crop.paste(tile, (tx - px0, ty - py0))
        if tone is not None:
            crop = Image.eval(crop, lambda v: int(v * tone))
        m = self.mask(g, (px1 - px0, py1 - py0), (px0 / self.ppm, py0 / self.ppm))
        self.img.paste(crop, (px0, py0), m)

    def soft(self, fn, blur_m):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        fn(ImageDraw.Draw(layer, "RGBA"))
        layer = layer.filter(ImageFilter.GaussianBlur(max(1, blur_m * self.ppm)))
        base = self.img.convert("RGBA")
        base.alpha_composite(layer)
        self.img = base.convert("RGB")


def parts(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


# ------------------------------------------------------------------ Leerraum: Baeume und Hecken

def void_mass(C, rnd):
    d = C.draw()
    for _ in range(int(W_M * H_M * 0.9)):
        x, y = rnd.uniform(-1, W_M + 1), rnd.uniform(-1, H_M + 1)
        r = rnd.uniform(0.5, 1.4)
        col = rnd.choice([(20, 34, 26), (16, 28, 22), (24, 40, 30), (14, 22, 20)])
        d.ellipse([*C.P(x - r, y - r), *C.P(x + r, y + r)], fill=col)
    for _ in range(int(W_M * H_M * 0.5)):                                     # Lichtkanten der Kronen
        x, y = rnd.uniform(0, W_M), rnd.uniform(0, H_M)
        r = rnd.uniform(0.25, 0.6)
        d.arc([*C.P(x - r, y - r), *C.P(x + r, y + r)], 200, 300, fill=(46, 66, 52, 140), width=max(1, int(0.04 * C.ppm)))


# ------------------------------------------------------------------ Waende

def face_depth(pclip, x0, x1, y, hmax):
    """Wie weit die feste Masse von der Kante y nach NORDEN (kleineres y) reicht (unteres Drittel)."""
    xs = [x0 + 0.05 + k * 0.1 for k in range(max(1, int((x1 - x0 - 0.1) / 0.1) + 1))]
    depths = []
    for x in xs:
        h = 0.0
        while h + 0.05 <= hmax + 1e-6 and pclip.contains(Point(x, y - h - 0.05 + 0.01)):
            h += 0.05
        depths.append(h)
    depths.sort()
    return min(hmax, depths[len(depths) // 3])


def owner(pt, geoms):
    best = None
    for key, g in geoms.items():
        if g.buffer(0.35).contains(pt):
            if best is None or g.area < geoms[best].area:
                best = key
    return best


def faces(C, walk, geoms):
    solid = box(-5, -5, W_M + 5, H_M + 5).difference(walk)
    pclip = prep(solid)
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
                # Nordwand: oben feste Masse, unten begehbar
                if not (solid.contains(Point(mx, y - 0.05)) and walk.contains(Point(mx, y + 0.05))):
                    continue
                room = owner(Point(mx, y + 0.3), geoms)
                inside_house = HOUSE.contains(Point(mx, y - 0.05))
                if room in GARDEN:
                    style = "ziegel" if inside_house else ("zaun" if room == "graveyard" else "hecke")
                    hmax = 1.0
                else:
                    style = STYLE.get(room, "tapete")
                    hmax = 0.4 if y > 0.6 else 0.9                              # Innenwand = Wandmasse
                    for tb in getattr(L, "THICK_WALLS", []):                     # dickere Wand: Flaeche so hoch wie die Masse
                        if abs(y - tb[3]) < 0.05 and xb > tb[0] and xa < tb[2]:
                            hmax = max(hmax, tb[3] - tb[1] + L.WALL / 2)
                fh = face_depth(pclip, xa, xb, y, hmax)
                if fh < 0.15:
                    continue
                img = VF.wall_front(xb - xa, fh, style, C.ppm, seed=int(xa * 7 + y * 3))
                px, py = int(round(xa * C.ppm)), int(round((y - fh) * C.ppm))
                face = Polygon([(xa, y - fh), (xb, y - fh), (xb, y), (xa, y)]).intersection(solid.buffer(0.001))
                m = C.mask(face, img.size, (xa, y - fh))
                if img.mode == "RGBA":
                    m = ImageChops.multiply(m, img.getchannel("A").resize(m.size))
                C.img.paste(img.convert("RGB").resize(m.size), (px, py), m)
                shadows.append(Polygon([(xa, y), (xb, y), (xb, y + 0.3), (xa, y + 0.3)]).intersection(walk))
                n += 1

    def draw_sh(d):
        for g in shadows:
            for q in parts(g):
                d.polygon([C.P(*c) for c in q.exterior.coords], fill=(0, 0, 0, 90))
    C.soft(draw_sh, 0.1)
    return n


def ambient(C, walk):
    s = 8
    small = Image.new("L", (int(W_M * s), int(H_M * s)), 255)
    d = ImageDraw.Draw(small)
    for p in parts(walk):
        d.polygon([(x * s, y * s) for x, y in p.exterior.coords], fill=0)
        for h in p.interiors:
            d.polygon([(x * s, y * s) for x, y in h.coords], fill=255)
    small = small.filter(ImageFilter.GaussianBlur(0.35 * s)).resize(C.img.size, Image.BICUBIC)
    amount = ImageChops.multiply(small, C.mask(walk)).point(lambda v: int(v * 0.6))
    C.img = Image.composite(Image.new("RGB", C.img.size, (6, 4, 10)), C.img, amount)


# ------------------------------------------------------------------ Deko

class Avoid:
    """Konsolen, Vents, Spielpunkte und Oeffnungen: dort keine Bodendeko (0,8 m Abstand)."""

    def __init__(self, opens):
        pts = []
        brief = HERE / "_villa" / "console_brief.json"
        if brief.exists():
            for r in json.loads(brief.read_text(encoding="utf-8")):
                pts.append(Point(r["x"], r["y"]))
        for p in (L.SPAWN, L.EMERGENCY, L.SURVEILLANCE, L.ADMIN_TABLE, L.FREEPLAY, L.CLOCK):
            pts.append(Point(p))
        g = [p.buffer(0.8) for p in pts]
        for o in opens:
            ax, at, a, b = o[:4]
            g.append(box(at - 1.0, a - 0.2, at + 1.0, b + 0.2) if ax == "x" else box(a - 0.2, at - 1.0, b + 0.2, at + 1.0))
        self.g = prep(unary_union(g))

    def ok(self, x0, y0, x1, y1):
        return not self.g.intersects(box(x0, y0, x1, y1))


def chalk_outline(d, C, x, y, s, rot, seed):
    """Kreide-Umriss eines liegenden Crewmates (Tatort am Set)."""
    body = [(-0.35, -0.45), (0.0, -0.62), (0.32, -0.5), (0.4, -0.1), (0.38, 0.45), (0.2, 0.5), (0.18, 0.25),
            (-0.05, 0.25), (-0.08, 0.5), (-0.28, 0.5), (-0.36, 0.2), (-0.55, 0.15), (-0.58, -0.25), (-0.38, -0.3)]
    c, sn = math.cos(rot), math.sin(rot)
    pts = [(x + (px * c - py * sn) * s, y + (px * sn + py * c) * s) for px, py in body]
    q = HD.wobble(pts + [pts[0]], amp=0.01, seed=seed, step=0.05)
    d.line([C.P(*p) for p in q], fill=(232, 228, 220, 190), width=max(1, int(0.03 * C.ppm)), joint="curve")


def blood(d, C, x, y, r, rnd, drips=True):
    pts = HD.wobble_ellipse(x, y, r, r * 0.65, amp=r * 0.18, seed=rnd.randint(0, 999))
    d.polygon([C.P(*p) for p in pts], fill=(92, 10, 18, 230))
    d.polygon([C.P(px + 0.02, py - 0.02) for px, py in HD.wobble_ellipse(x, y, r * 0.55, r * 0.35, amp=r * 0.1, seed=3)], fill=(130, 20, 30, 200))
    d.ellipse([*C.P(x - r * 0.25, y - r * 0.3), *C.P(x - r * 0.05, y - r * 0.2)], fill=(200, 120, 120, 120))
    if drips:
        for _ in range(rnd.randint(3, 6)):
            a = rnd.uniform(0, math.tau)
            dd = rnd.uniform(r * 1.2, r * 2.2)
            rr = rnd.uniform(0.02, 0.06)
            cx, cy = x + math.cos(a) * dd, y + math.sin(a) * dd * 0.7
            d.ellipse([*C.P(cx - rr, cy - rr * 0.7), *C.P(cx + rr, cy + rr * 0.7)], fill=(92, 10, 18, 220))


def footprints(d, C, pts, rnd):
    """Blutige Fussspuren entlang einer Linie."""
    ls = LineString(pts)
    k, side = 0.0, 1
    while k < ls.length:
        a = ls.interpolate(k)
        b = ls.interpolate(min(ls.length, k + 0.05))
        ang = math.atan2(b.y - a.y, b.x - a.x)
        nx, ny = -math.sin(ang) * 0.09 * side, math.cos(ang) * 0.09 * side
        alpha = int(200 * (1 - k / max(ls.length, 0.1)) + 30)
        cx, cy = a.x + nx, a.y + ny
        d.ellipse([*C.P(cx - 0.06, cy - 0.04), *C.P(cx + 0.06, cy + 0.04)], fill=(92, 10, 18, alpha))
        side = -side
        k += 0.32


def rug(C, cx, cy, rx, ry, ppm):
    """Runder Teppich (Seance): Teppichkachel als Ellipse mit Ornamentrand."""
    tile = VF.material_tile("teppich", ppm, seed=7)
    g = Point(cx, cy).buffer(1, 48)
    from shapely import affinity
    g = affinity.scale(g, rx, ry)
    C.fill_tile(tile, g)
    d = C.draw()
    d.ellipse([*C.P(cx - rx, cy - ry), *C.P(cx + rx, cy + ry)], outline=(196, 160, 90, 230), width=max(1, int(0.06 * ppm)))
    d.ellipse([*C.P(cx - rx + 0.12, cy - ry + 0.1), *C.P(cx + rx - 0.12, cy + ry - 0.1)], outline=(80, 22, 30, 255), width=max(1, int(0.03 * ppm)))


def runner(C, x0, y0, x1, y1, ppm):
    """Laeufer (Teppichstreifen) mit Rand, z. B. durch die Portraetgalerie."""
    C.fill_tile(VF.material_tile("teppich", ppm, seed=11), box(x0, y0, x1, y1))
    d = C.draw()
    for xx in (x0 + 0.06, x1 - 0.06):
        d.line([C.P(xx, y0), C.P(xx, y1)], fill=(196, 160, 90, 220), width=max(1, int(0.05 * ppm)))


def grave_mound(d, C, x, y, rnd):
    """Grabhuegel vor einem Friedhofsengel (25.10., vorher flaches dunkles Rechteck): Steinrand, gerundete Erde mit
    Lichtkante oben, dunkle Erdklumpen, Grasbueschel an den Raendern, manchmal ein paar Blumen."""
    ppm = C.ppm
    img = Path(__file__).resolve().parent / "villa_assets" / "villa_grabhuegel.png"
    if img.exists():                                                                   # GPT-Erdhuegel (25.10.)
        m = Image.open(img).convert("RGBA")
        mw = int(round(0.95 * ppm)); mh = int(round(1.3 * ppm))                 # auf Grablaenge gestreckt
        m = m.resize((mw, mh), Image.LANCZOS)
        if rnd.random() < 0.5: m = m.transpose(Image.FLIP_LEFT_RIGHT)
        px0, py0 = C.P(x, y + 0.7)
        C.img.paste(m.convert("RGB"), (int(px0 - mw / 2), int(py0 - mh / 2)), m.getchannel("A"))
        return
    px = lambda m: max(1, int(m * ppm))
    x0, x1, y0, y1 = x - 0.44, x + 0.44, y, y + 1.32
    rim = HD.wobble_rect(x0 - 0.06, y0 - 0.06, x1 + 0.06, y1 + 0.06, amp=0.02, seed=int(x * 7 + y))
    d.polygon([C.P(*p) for p in rim], fill=(96, 94, 90, 235), outline=(28, 26, 26, 255), width=px(0.025))
    for k in range(14):                                                              # Fugen im Steinrand
        t = k / 14.0
        if k % 2:
            yy = y0 - 0.06 + t * (y1 - y0 + 0.12)
            d.line([C.P(x0 - 0.06, yy), C.P(x0, yy)], fill=(60, 58, 56, 200), width=px(0.012))
            d.line([C.P(x1, yy), C.P(x1 + 0.06, yy)], fill=(60, 58, 56, 200), width=px(0.012))
    soil = HD.wobble_rect(x0 + 0.01, y0 + 0.01, x1 - 0.01, y1 - 0.01, amp=0.035, seed=int(x * 13 + y))
    d.polygon([C.P(*p) for p in soil], fill=(78, 56, 40, 255), outline=(30, 22, 16, 255), width=px(0.02))
    hl = HD.wobble_rect(x0 + 0.1, y0 + 0.08, x1 - 0.1, y0 + 0.55, amp=0.03, seed=int(x * 17 + y))   # Lichtkante (Kopfende)
    d.polygon([C.P(*p) for p in hl], fill=(104, 78, 56, 255))
    for _ in range(16):                                                               # Erdklumpen
        cx, cy, r = rnd.uniform(x0 + 0.08, x1 - 0.08), rnd.uniform(y0 + 0.1, y1 - 0.08), rnd.uniform(0.025, 0.05)
        d.ellipse([*C.P(cx - r, cy - r * 0.7), *C.P(cx + r, cy + r * 0.7)], fill=(52, 36, 26, 255))
        d.ellipse([*C.P(cx - r * 0.5, cy - r * 0.6), *C.P(cx + r * 0.2, cy - r * 0.1)], fill=(120, 94, 70, 200))
    for _ in range(5):                                                                # Gras an den Raendern
        side = rnd.choice((x0 + 0.04, x1 - 0.04))
        gy = rnd.uniform(y0 + 0.2, y1 - 0.1)
        for b in range(4):
            a = -0.9 + b * 0.6
            d.line([C.P(side, gy), C.P(side + 0.07 * math.sin(a), gy - 0.12 * math.cos(a) * 0.8)], fill=(70, 120, 52, 255), width=px(0.018))
    if rnd.random() < 0.5:                                                            # ein paar Blumen
        fx, fy = rnd.uniform(x0 + 0.15, x1 - 0.15), rnd.uniform(y0 + 0.6, y1 - 0.3)
        for k in range(3):
            ox, oy = fx + (k - 1) * 0.07, fy + (k % 2) * 0.05
            d.ellipse([*C.P(ox - 0.035, oy - 0.03), *C.P(ox + 0.035, oy + 0.03)],
                      fill=rnd.choice(((220, 220, 230, 255), (170, 120, 210, 255), (200, 70, 80, 255))), outline=(30, 24, 24, 255))


def horror_floor(d, C, rnd, av):
    """Bodenspuren der Horror-Schicht (Audit 15.10.): Schleifspur zur Treppe, Russ-Fussspuren aus dem Kamin,
    Kreidekreis unter dem Seance-Tisch, Blut in Kueche und Waschkueche, Glasscherben und Wurzeln im Gewaechshaus,
    Kratzspuren vor der Grufttuer, Kabelbuendel im Heizungskeller, Papiere im Arbeitszimmer."""
    ppm = C.ppm
    px = lambda m: max(1, int(m * ppm))
    # Schleifspur: vom Kreide-Umriss in der Halle zur Treppe (zwei dunkle Streifen, aussen verwischt)
    for off in (-0.12, 0.12):
        pts = [(17.0, 17.4 + off), (17.1, 15.0 + off), (16.9, 12.6 + off), (17.0, 11.0 + off)]
        d.line([C.P(*q) for q in HD.wobble(pts, amp=0.03, seed=41, step=0.1)], fill=(60, 10, 16, 150), width=px(0.08), joint="curve")
    footprints(d, C, [(17.3, 17.0), (17.6, 14.5), (17.4, 12.0), (17.2, 11.0)], rnd)
    # (Kreidekreis unter dem Seance-Tisch seit 25.10. entfernt: dort liegt jetzt das Pentagramm der Mod, HollowmereWorld.Ritual.cs)
    # Baerenfell vor dem grossen Kamin im Seance Parlour (25.10., Vorlage villa_assets/villa_baerenfell.png)
    rug_path = Path(__file__).resolve().parent / "villa_assets" / "villa_baerenfell.png"
    if rug_path.exists():
        rug = Image.open(rug_path).convert("RGBA").rotate(90, expand=True)   # Kopf nach links (User 25.10.)
        rw = int(round(1.9 * ppm)); rh = int(round(rug.height * rw / rug.width))
        rug = rug.resize((rw, rh), Image.LANCZOS)
        rx, ry = C.P(17.0, 2.05)
        C.img.paste(rug.convert("RGB"), (int(rx - rw / 2), int(ry - rh / 2)), rug.getchannel("A"))
    # Russ-Fussspuren aus dem Kamin ins Zimmer, werden schwaecher
    pts = [(31.6, 14.8), (31.2, 15.5), (30.4, 16.2), (29.4, 16.9)]          # ab dem Kamin (25.10. vor die dicke Wand geruckt)
    ls = LineString(pts)
    k, side = 0.0, 1
    while k < ls.length:
        q = ls.interpolate(k)
        qq = ls.interpolate(min(ls.length, k + 0.05))
        ang = math.atan2(qq.y - q.y, qq.x - q.x)
        nx, ny = -math.sin(ang) * 0.09 * side, math.cos(ang) * 0.09 * side
        al = int(170 * (1 - k / max(ls.length, 0.1)) + 20)
        d.ellipse([*C.P(q.x + nx - 0.06, q.y + ny - 0.04), *C.P(q.x + nx + 0.06, q.y + ny + 0.04)], fill=(20, 18, 18, al))
        side = -side
        k += 0.3
    # Blut: Kueche beim Hackblock, Waschkueche unter der Leine, Prop Store vor dem Sarg
    for x, y, r in ((6.0, 2.3, 0.2), (8.4, 7.0, 0.16), (32.6, 3.9, 0.14)):
        if av.ok(x - r - 0.3, y - r - 0.3, x + r + 0.3, y + r + 0.3):
            blood(d, C, x, y, r, rnd)
    # Gewaechshaus: Glasscherben (helle Splitter) und Wurzeln, die durch den Boden brechen
    for _ in range(30):
        x, y = rnd.uniform(40.6, 49.4), rnd.uniform(2.6, 11.4)
        if 42.0 <= x <= 48.0 and (3.9 <= y <= 5.0 or 8.4 <= y <= 9.5):
            continue
        s_ = rnd.uniform(0.04, 0.1)
        ang = rnd.uniform(0, math.tau)
        tri = [(x + s_ * math.cos(ang + t), y + s_ * 0.7 * math.sin(ang + t)) for t in (0, 2.3, 4.2)]
        d.polygon([C.P(*q) for q in tri], fill=(196, 216, 232, 150), outline=(14, 16, 20, 200))
    for k in range(3):
        pts = [(49.4, 6.2 + k * 1.6), (48.2, 6.5 + k * 1.5), (47.0, 6.1 + k * 1.7), (45.8, 6.6 + k * 1.6)]
        d.line([C.P(*q) for q in HD.wobble(pts, amp=0.05, seed=50 + k, step=0.08)], fill=(70, 50, 30, 200), width=px(0.07), joint="curve")
    # Kratzspuren vor der Grufttuer (innen), Kabelbuendel im Heizungskeller, Papiere im Arbeitszimmer
    for k in range(4):
        x0 = 46.1 + k * 0.4
        d.line([C.P(x0, 28.6), C.P(x0 + 0.1, 29.9)], fill=(40, 36, 36, 180), width=px(0.025))
    VF.floor_cable(d, C.Pw, ppm, [(2.6, -8.9), (3.4, -9.6), (4.8, -9.3), (6.2, -9.9), (6.8, -11.0)], seed=9)
    VF.floor_cable(d, C.Pw, ppm, [(2.3, -9.2), (3.0, -10.4), (4.4, -11.2), (5.0, -12.2)], seed=10)
    for k in range(6):
        x, y = rnd.uniform(27.0, 33.0), rnd.uniform(19.4, 22.4)
        ang = rnd.uniform(-0.4, 0.4)
        w, h = 0.21, 0.3
        pts = [(x + (-w / 2) * math.cos(ang) - (-h / 2) * math.sin(ang), y + (-w / 2) * math.sin(ang) + (-h / 2) * math.cos(ang)),
               (x + (w / 2) * math.cos(ang) - (-h / 2) * math.sin(ang), y + (w / 2) * math.sin(ang) + (-h / 2) * math.cos(ang)),
               (x + (w / 2) * math.cos(ang) - (h / 2) * math.sin(ang), y + (w / 2) * math.sin(ang) + (h / 2) * math.cos(ang)),
               (x + (-w / 2) * math.cos(ang) - (h / 2) * math.sin(ang), y + (-w / 2) * math.sin(ang) + (h / 2) * math.cos(ang))]
        d.polygon([C.P(*q) for q in pts], fill=(220, 212, 190, 230), outline=(14, 16, 20, 200))


def decorate(C, walk, geoms, opens, rnd):
    av = Avoid(opens)
    ppm = C.ppm
    # Teppiche zuerst (gehoeren zum Boden)
    rug(C, 17.0, 4.3, 2.3, 1.6, ppm)                                          # Seance-Tisch
    runner(C, 23.7, 8.6, 25.3, 23.6, ppm)                                     # Portraetgalerie
    rug(C, 31.0, 16.2, 1.9, 1.1, ppm)                                         # Kaminzimmer vor dem Kamin
    d = C.draw()
    # Filmset in der Halle: Dollyschiene unter der Kamera, Kabel zum Scheinwerfer, Tape-Marken
    neg = lambda pts: [(x, -y) for x, y in pts]
    VF.floor_dolly_rail(d, C.Pw, ppm, 13.6, -17.25, 22.6)
    VF.floor_cable(d, C.Pw, ppm, neg([(12.4, 18.8), (13.2, 19.4), (15.0, 19.5), (16.4, 19.2), (19.8, 17.6)]), seed=3)
    VF.floor_cable(d, C.Pw, ppm, neg([(21.8, 9.6), (22.4, 11.0), (22.6, 13.5), (21.9, 15.8), (20.6, 16.6)]), seed=4)
    VF.floor_tape_strip(d, C.Pw, ppm, 15.6, -19.35, 15.6, -19.65)
    for x, y, k, a in ((14.6, 12.6, "T", 0.2), (19.6, 12.2, "X", 0.0), (18.4, 18.4, "L", 1.2)):
        if av.ok(x - 0.2, y - 0.2, x + 0.2, y + 0.2):
            VF.floor_tape_mark(d, C.Pw, ppm, x, -y, k, a)
    # Tatort: Kreide-Umrisse und Kunstblut
    # (dritter Umriss seit 25.10. in der Family Crypt neben der Blutlache, vorher mitten auf einem Grab des Friedhofs)
    for x, y, s, r, seed in ((6.0, 16.6, 1.0, 0.5, 21), (24.5, 19.0, 0.9, -0.3, 22), (48.6, 29.9, 1.0, 0.4, 23)):
        if av.ok(x - 0.7, y - 0.7, x + 0.7, y + 0.7):
            chalk_outline(d, C, x, y, s, r, seed)
    for x, y, r in ((20.3, 22.6, 0.22), (5.4, 17.2, 0.3), (9.6, 4.2, 0.18), (47.0, 30.6, 0.35), (24.6, 13.6, 0.16)):
        if av.ok(x - r - 0.3, y - r - 0.3, x + r + 0.3, y + r + 0.3):
            blood(d, C, x, y, r, rnd)
    footprints(d, C, [(24.5, 19.4), (24.6, 16.0), (24.3, 12.4)], rnd)
    footprints(d, C, [(46.6, 30.0), (44.0, 27.0), (41.2, 25.0)], rnd)
    # Spinnweben in dunklen Ecken, Laub draussen
    for key in L.DARK:
        g = geoms.get(key)
        if g is None:
            continue
        x0, y0, x1, y1 = g.bounds
        for (cx, cy, qx, qy) in ((x0, y0, 1, 1), (x1, y0, -1, 1)):
            if av.ok(min(cx, cx + qx * 0.6), min(cy, cy + qy * 0.6), max(cx, cx + qx * 0.6), max(cy, cy + qy * 0.6)):
                VF.floor_cobweb_corner(d, C.Pw, ppm, cx, -cy, 0.6, qx, -qy, seed=int(cx * 10 + cy))
    for key in ("terrace", "driveway", "crewcamp", "fountain", "graveyard"):
        g = geoms.get(key)
        if g is None:
            continue
        x0, y0, x1, y1 = g.bounds
        VF.floor_leaves(d, C.Pw, ppm, x0, -y1, x1, -y0, n=int(g.area * 1.2), seed=len(key))
    horror_floor(d, C, rnd, av)
    # Reifenspuren auf dem Kies, Grabhuegel auf dem Friedhof
    for off in (-0.55, 0.55):
        d.line([C.P(12.2, 27.6 + off), C.P(17.5, 27.1 + off), C.P(23.8, 27.8 + off)], fill=(70, 66, 58, 120), width=max(1, int(0.22 * ppm)), joint="curve")
    for x, y in ((42.9, 17.3), (45.4, 17.3), (47.9, 17.3), (42.9, 21.3), (45.4, 21.3), (47.9, 21.3), (42.9, 25.3), (45.4, 25.3)):
        if av.ok(x - 0.5, y - 0.2, x + 0.5, y + 1.4):
            grave_mound(d, C, x, y, random.Random(int(x * 100 + y)))


# ------------------------------------------------------------------ Ablauf

def render(ppm):
    import gen_villa as G
    walk, geoms, opens = G.build("large")
    rnd = random.Random(13)
    C = Canvas(ppm)
    void_mass(C, rnd)
    # Wandkrone: Bereichs-Rechtecke ohne begehbare Flaeche (Haus dunkel, Garten Hecke, Gewaechshaus Glasrahmen)
    d = C.draw()
    for a in L.AREAS:
        r = box(*a[2])
        col = HEDGE_TOP if a[0] in GARDEN else WALL_TOP
        for p in parts(r.difference(walk)):
            d.polygon([C.P(*q) for q in p.exterior.coords], fill=col)
    # Boeden
    tone = {"terrace": 0.78, "fountain": 0.66, "greenhouse": 0.78, "driveway": 0.85}   # helle Aussenflaechen daempfen
    for key, g in geoms.items():
        C.fill_tile(VF.material_tile(MAT.get(key, "parkett"), ppm, seed=len(key)), g, tone=tone.get(key))
    # Schwellen in den Oeffnungen
    for o in opens:
        g = G.opening_box(o)
        ext = not HOUSE.buffer(-0.5).contains(g.centroid)
        C.fill_tile(VF.material_tile("terrasse" if ext else "dielen", ppm, seed=5), g, tone=0.8)
    decorate(C, walk, geoms, opens, rnd)
    ambient(C, walk)
    n = faces(C, walk, geoms)
    # dunkle Raeume deutlich dunkler und kaelter
    for key in L.DARK:
        g = geoms.get(key)
        if g is None:
            continue
        m = C.mask(g).point(lambda v: int(v * 0.42))
        C.img = Image.composite(Image.new("RGB", C.img.size, (12, 14, 30)), C.img, m)
    # User-Vorgabe "insgesamt duesterer": kuehl, entsaettigt, etwas dunkler (das Spiel dunkelt zusaetzlich
    # ausserhalb des Sichtkegels ab, also nicht ins Schwarze)
    from PIL import ImageOps
    C.img = Image.blend(C.img, ImageOps.grayscale(C.img).convert("RGB"), 0.2)
    r, g_, b = C.img.split()
    C.img = Image.merge("RGB", (r.point(lambda v: int(v * 0.82)), g_.point(lambda v: int(v * 0.85)), b.point(lambda v: int(v * 0.95))))
    # Tuschekante um alle begehbaren Flaechen
    d = C.draw()
    for k, p in enumerate(parts(walk)):
        for j, ring in enumerate([p.exterior] + list(p.interiors)):
            pts = HD.wobble(list(ring.coords), amp=0.008, seed=900 + k * 50 + j, step=0.1, closed=True)
            HD.ink(d, [C.P(*q) for q in pts], OUTLINE + (255,), max(2, int(0.05 * ppm)), seed=k * 50 + j, var=0.2, closed=True)
    C.img = HD.paper_grain(C.img, 0.03, seed=4)
    print(f"villa floor map: {C.img.size}, {n} wall faces")
    return C.img
