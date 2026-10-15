# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_floor.py - Boeden, Wandstirnseiten und Bodendetails von Hollowmere Manor (Stilblatt).
#
# Wie park_floor.py (Unknown's Atlas) arbeitet die Villa mit nahtlosen Musterkacheln (2 x 2 m): jedes
# Material ist eine Kachel, Perioden sind Teiler der Kachel, jede Form wird an den neun Kachelversaetzen
# gezeichnet. Stil "Among Us, leicht handgezeichnet" (handdraw.py): unregelmaessige Fugen, Zittern im
# Umriss, Kantenlicht oben/links, Fugenschatten unten/rechts, Abnutzung, Papierkorn zum Schluss.
# Wandstirnseiten (wall_front) sind die Nordwaende im Bodenbild; ihre Hoehe ist schon in Bildmetern
# (also mal K gerechnet). Farben angehoben, weil das Spiel ausserhalb des Sichtkegels abdunkelt.

import math
import os
import random
import sys

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)

import numpy as np                          # noqa: E402
from PIL import Image, ImageDraw, ImageFilter   # noqa: E402

import museum_art as A                      # noqa: E402
import handdraw as HD                       # noqa: E402

TILE_M = 2.0
SS = 2
OUTLINE = (14, 12, 18)
GRAIN = 0.03
MATERIALS = ["parkett", "dielen", "fliesen_schachbrett", "steinplatten", "teppich", "kies", "terrasse", "wiese",
             "friedhofserde", "glashausfliesen"]
WALL_STYLES = ["tapete", "ziegel", "stein", "hecke", "zaun", "putz", "glashaus"]

# Palette (RGB)
WALNUT = (125, 85, 54)
WALNUT_D = (90, 61, 39)
WALNUT_L = (156, 106, 68)
BORDEAUX = (132, 46, 60)              # seit der Abnahme kuehler und stumpfer
BORDEAUX_D = (100, 34, 46)
BORDEAUX_L = (156, 68, 80)
BRASS = (180, 142, 70)
CREAM = (230, 220, 194)
IRON = (58, 56, 64)
IRON_L = (96, 94, 104)
HEDGE = (38, 70, 46)
GAFFER = (232, 194, 58)


# ------------------------------------------------------------------ Zeichenflaeche

class Sheet:
    """Zeichenflaeche in Bildkoordinaten (u rechts, v unten, Meter) mit Supersampling. periodic=True:
    jede Form wird an den neun Versaetzen gezeichnet (nahtlose Kachel, Kantenlaenge w_m = h_m)."""

    def __init__(self, w_m, h_m, ppm, base, periodic=False, mode="RGB", ss=SS):
        self.w_m, self.h_m, self.ppm = w_m, h_m, ppm
        self.n = (max(1, int(round(w_m * ppm))), max(1, int(round(h_m * ppm))))
        self.N = (self.n[0] * ss, self.n[1] * ss)
        self.sx, self.sy = self.N[0] / w_m, self.N[1] / h_m
        self.img = Image.new(mode, self.N, base)
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.offs = [(dx, dy) for dx in (-w_m, 0, w_m) for dy in (-h_m, 0, h_m)] if periodic else [(0.0, 0.0)]

    def px(self, m):
        return max(1, int(round(m * self.sx)))

    def P(self, pts, dx=0.0, dy=0.0):
        return [((x + dx) * self.sx, (y + dy) * self.sy) for x, y in pts]

    def _offs(self, x0, y0, x1, y1):
        for dx, dy in self.offs:
            if x1 + dx < -0.02 or x0 + dx > self.w_m + 0.02 or y1 + dy < -0.02 or y0 + dy > self.h_m + 0.02:
                continue
            yield dx, dy

    def poly(self, pts, fill=None, outline=None, width=0.0):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for dx, dy in self._offs(min(xs), min(ys), max(xs), max(ys)):
            q = self.P(pts, dx, dy)
            if fill is not None:
                self.d.polygon(q, fill=fill)
            if outline is not None:
                self.d.line(q + [q[0]], fill=outline, width=self.px(width), joint="curve")

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=0.0):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, outline, width)

    def line(self, pts, fill, width):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for dx, dy in self._offs(min(xs) - width, min(ys) - width, max(xs) + width, max(ys) + width):
            self.d.line(self.P(pts, dx, dy), fill=fill, width=self.px(width), joint="curve")

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=0.0):
        for dx, dy in self._offs(cx - rx, cy - ry, cx + rx, cy + ry):
            a, b = self.P([(cx - rx, cy - ry), (cx + rx, cy + ry)], dx, dy)
            self.d.ellipse([a, b], fill=fill, outline=outline, width=self.px(width) if outline else 0)

    def ink(self, pts, fill, width, seed=0, var=0.25, closed=True):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for dx, dy in self._offs(min(xs), min(ys), max(xs), max(ys)):
            HD.ink(self.d, self.P(pts, dx, dy), fill, self.px(width), seed=seed, var=var, closed=closed)

    def blend(self, fn, blur=0.0):
        """Fuer RGBA-Flaechen: fn(draw) auf eigener Ebene, dann ueberblenden (PIL mischt auf RGBA nicht)."""
        layer = Image.new("RGBA", self.N, (0, 0, 0, 0))
        fn(ImageDraw.Draw(layer, "RGBA"))
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(self.px(blur)))
        self.img.alpha_composite(layer)

    def finish(self, grain=GRAIN, seed=1):
        img = self.img.resize(self.n, Image.LANCZOS)
        if grain and img.mode == "RGB":
            img = HD.paper_grain(img, grain, seed)
        return img


def _tone(col, f):
    return tuple(max(0, min(255, int(v * f))) for v in col[:3])


def _tint(col, t):
    return tuple(max(0, min(255, int(col[k] * t[k]))) for k in range(3))


def _wave(w, h, periods, seed):
    """Periodisches Rauschen (Summe ganzzahliger Sinuswellen) auf einer w x h Flaeche, -1..1."""
    rnd = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    x = xx / w * 2 * math.pi
    y = yy / h * 2 * math.pi
    v = np.zeros((h, w), np.float32)
    for p in periods:
        for _ in range(2):
            kx, ky = int(rnd.integers(-p, p + 1)), int(rnd.integers(-p, p + 1))
            if kx == 0 and ky == 0:
                ky = p
            v += np.sin(kx * x + ky * y + rnd.uniform(0, 6.3)) / max(1, p) ** 0.6
    v /= max(1e-6, float(np.abs(v).max()))
    return v


def mottle(img, amount, seed, periods=(2, 3, 5)):
    """Fleckige Helligkeit (periodisch, also nahtlos) ueber ein RGB-Bild."""
    a = np.asarray(img).astype(np.float32)
    f = 1 + _wave(img.width, img.height, periods, seed) * amount
    return Image.fromarray(np.clip(a * f[..., None], 0, 255).astype(np.uint8), "RGB")


def shrink(pts, m):
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for x, y in pts:
        dx, dy = x - cx, y - cy
        ln = math.hypot(dx, dy) or 1.0
        out.append((x - dx / ln * m, y - dy / ln * m))
    return out


def edge_light(sh, pts, light, dark, w, thresh=0.3):
    """Kantenlicht oben/links, Schatten unten/rechts an einem konvexen Polygon (Bildkoordinaten)."""
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        if ln < 1e-6:
            continue
        nx, ny = -dy / ln, dx / ln
        if (cx - a[0]) * nx + (cy - a[1]) * ny < 0:
            nx, ny = -nx, -ny
        s = (-nx - ny) / math.sqrt(2)
        if s < -thresh:
            sh.poly(HD.edge_strip(pts, k, w), fill=dark)
        elif s > thresh:
            sh.poly(HD.edge_strip(pts, k, w), fill=light)


def leaf(sh, x, y, ln, ang, col, seed=0):
    """Welkes Blatt: spitze Ellipse mit Mittelrippe."""
    c, s = math.cos(ang), math.sin(ang)
    pts = []
    for k in range(10):
        t = k / 10 * math.tau
        px_, py_ = math.cos(t) * ln / 2, math.sin(t) * ln * 0.22 * (1 - 0.3 * abs(math.cos(t)))
        pts.append((x + px_ * c - py_ * s, y + px_ * s + py_ * c))
    sh.poly(pts, fill=col, outline=_tone(col, 0.6), width=0.008)
    sh.line([(x - c * ln * 0.4, y - s * ln * 0.4), (x + c * ln * 0.4, y + s * ln * 0.4)], fill=_tone(col, 0.65), width=0.006)


def tufts(sh, rnd, n, cols, h=0.08, region=None):
    T = sh.w_m
    for _ in range(n):
        x, y = rnd.uniform(0, T), rnd.uniform(0, T)
        col = rnd.choice(cols)
        for seg in HD.tuft(x, y, rnd, n=rnd.randint(3, 5), h=h, spread=0.04):
            (ax, ay), (bx, by) = seg
            sh.line([(ax, ay), (bx, ay - (by - ay))], fill=col, width=0.012)    # Bild-v nach unten: Halme nach oben


# ------------------------------------------------------------------ Materialkacheln

def tile_parkett(ppm, seed=1, base=(152, 104, 60)):
    """Fischgraet-Parkett (Halle, Salons). Gitter im um 45 Grad gedrehten Rahmen (Einheit w = Stabbreite):
    waagrechte Staebe [k, k+n] x [k, k+1], senkrechte [k+n, k+n+1] x [k-n+1, k+1], naechste Bahn um 2n in u
    verschoben. Die Periode ist sqrt(2) * L; mit L = T / (q * sqrt(2)) passen q Perioden in die Kachel."""
    T = TILE_M
    q, n = 2, 6
    L = T / (q * math.sqrt(2))
    w = L / n
    sh = Sheet(T, T, ppm, (62, 44, 30), periodic=True)
    rnd = random.Random(seed)
    c45 = math.sqrt(0.5)

    def rot(u, v):
        return ((u - v) * c45 * w + T / 2, (u + v) * c45 * w)

    planks = []
    for m in range(-4, 5):
        for k in range(-3 * n, 3 * n):
            for (u0, v0, u1, v1) in ((k + 2 * n * m, k, k + n + 2 * n * m, k + 1), (k + n + 2 * n * m, k - n + 1, k + n + 1 + 2 * n * m, k + 1)):
                pts = [rot(u0, v0), rot(u1, v0), rot(u1, v1), rot(u0, v1)]
                cx = sum(p[0] for p in pts) / 4
                cy = sum(p[1] for p in pts) / 4
                if 0 <= cx < T and 0 <= cy < T:
                    planks.append(pts)
    tints = [(1, 1, 1)] * 5 + [(1.08, 1.0, 0.92), (0.94, 0.96, 1.02), (1.12, 1.02, 0.9), (0.9, 0.86, 0.84)]
    for i, pts in enumerate(planks):
        col = _tint(_tone(base, 1 + rnd.uniform(-0.1, 0.1)), rnd.choice(tints))
        q_ = shrink(pts, 0.006)
        q_ = HD.wobble(q_, amp=0.004, seed=seed * 50 + i, step=0.05, closed=True)
        sh.poly(q_, fill=col)
        # Maserung laengs (zwei Linien), Lichtkante, Schattenkante, zittriger Umriss
        (ax, ay), (bx, by), (cx_, cy_), (dx_, dy_) = pts
        for f in (0.32, 0.68):
            p0 = (ax + (dx_ - ax) * f, ay + (dy_ - ay) * f)
            p1 = (bx + (cx_ - bx) * f, by + (cy_ - by) * f)
            p0 = (p0[0] + (p1[0] - p0[0]) * 0.08, p0[1] + (p1[1] - p0[1]) * 0.08)
            p1 = (p1[0] + (p0[0] - p1[0]) * 0.08, p1[1] + (p0[1] - p1[1]) * 0.08)
            sh.line(HD.wobble([p0, p1], amp=0.006, seed=i + 3, step=0.05), fill=_tone(col, 0.86) + (160,), width=0.007)
        edge_light(sh, q_, _tone(col, 1.18) + (170,), (0, 0, 0, 70), 0.012)
        sh.ink(q_, (48, 32, 22, 255), 0.012, seed=i, var=0.3)
        u = rnd.random()
        if u < 0.08:                                                                  # blank gelaufen
            sh.ellipse((ax + cx_) / 2, (ay + cy_) / 2, 0.12, 0.05, fill=(255, 240, 210, 40))
        elif u < 0.13:                                                                # Wasserfleck
            sh.poly(HD.wobble_ellipse((ax + cx_) / 2, (ay + cy_) / 2, 0.08, 0.06, amp=0.015, seed=i), fill=(40, 24, 14, 55))
    img = mottle(sh.finish(seed=seed), 0.05, seed)
    return img


def tile_dielen(ppm, seed=1, base=(114, 98, 78)):
    """Alte Holzdielen (Dachboden): Reihen 0,2 m, Bretter mit versetzten Stoessen, Astloecher, Nagelkoepfe,
    einzelne Bretter fehlen (Blick ins Dunkel)."""
    T = TILE_M
    sh = Sheet(T, T, ppm, (40, 30, 22), periodic=True)
    rnd = random.Random(seed)
    rows = 10
    bh = T / rows
    for r in range(rows):
        v0, v1 = r * bh + 0.008, (r + 1) * bh - 0.008
        cuts = sorted(rnd.uniform(0, T) for _ in range(rnd.randint(1, 2)))
        for i, u0 in enumerate(cuts):
            u1 = cuts[i + 1] if i + 1 < len(cuts) else cuts[0] + T
            if u1 - u0 < 0.15:
                continue
            u0, u1 = u0 + 0.006, u1 - 0.006
            pts = HD.wobble([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], amp=0.004, seed=seed * 40 + r * 7 + i, step=0.06, closed=True)
            if rnd.random() < 0.04:                                                   # fehlendes Brett
                sh.poly(pts, fill=(24, 18, 14))
                for _ in range(3):
                    sx = rnd.uniform(u0, u1)
                    sh.line([(sx, v0), (sx + rnd.uniform(-0.05, 0.05), v0 + 0.04)], fill=(90, 70, 50), width=0.008)
                continue
            col = _tint(_tone(base, 1 + rnd.uniform(-0.12, 0.1)), rnd.choice([(1, 1, 1), (0.95, 0.95, 1.0), (1.06, 1.0, 0.9), (0.9, 0.9, 0.9)]))
            sh.poly(pts, fill=col)
            for g in range(rnd.randint(2, 3)):                                        # Maserung
                vv = v0 + bh * (0.2 + 0.3 * g + rnd.uniform(-0.05, 0.05))
                sh.line(HD.wobble([(u0 + 0.03, vv), (u1 - 0.03, vv + rnd.uniform(-0.02, 0.02))], amp=0.008, seed=r * 11 + g, step=0.08),
                        fill=_tone(col, 0.85) + (170,), width=0.006)
            if rnd.random() < 0.2:                                                    # Astloch
                kx, ky = rnd.uniform(u0 + 0.1, u1 - 0.1), (v0 + v1) / 2 + rnd.uniform(-0.03, 0.03)
                sh.ellipse(kx, ky, 0.025, 0.018, fill=_tone(col, 0.6), outline=_tone(col, 0.45), width=0.006)
                sh.ellipse(kx, ky, 0.01, 0.007, fill=_tone(col, 0.4))
            for nx in (u0 + 0.04, u1 - 0.04):                                         # Nagelkoepfe
                for ny in (v0 + 0.04, v1 - 0.04):
                    sh.ellipse(nx, ny, 0.008, 0.008, fill=(70, 60, 56), outline=(40, 32, 30), width=0.004)
            edge_light(sh, pts, _tone(col, 1.2) + (150,), (0, 0, 0, 80), 0.012)
            sh.ink(pts, (36, 26, 18, 255), 0.012, seed=r * 5 + i, var=0.3)
            if rnd.random() < 0.15:                                                   # Kratzer
                kx = rnd.uniform(u0 + 0.1, u1 - 0.1)
                sh.line([(kx, v0 + 0.03), (kx + rnd.uniform(0.1, 0.3), v1 - 0.03)], fill=(220, 200, 170, 90), width=0.005)
    for _ in range(40):                                                               # Staub
        sh.ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.006, 0.005, fill=(230, 220, 200, 70))
    return mottle(sh.finish(seed=seed), 0.05, seed + 1)


def tile_fliesen(ppm, seed=1, dark=(64, 68, 80), light=(192, 192, 182), grout=(90, 88, 86)):
    """Schachbrett-Fliesen 0,25 m (Kueche): leicht schief, abgenutzt, einzelne gesprungen oder abgeschlagen."""
    T = TILE_M
    sh = Sheet(T, T, ppm, grout, periodic=True)
    rnd = random.Random(seed)
    for r, c, pts in HD.jitter_grid(0, 0, T, T, 0.25, seed=seed, jitter=0.04, periodic=True):
        col = _tone(dark if (r + c) % 2 else light, 1 + rnd.uniform(-0.07, 0.07))
        q = shrink(pts, 0.006)
        if rnd.random() < 0.1:
            q = HD.chip(q, rnd, 0.2)
        sh.poly(q, fill=col)
        edge_light(sh, q, _tone(col, 1.15) + (170,), (0, 0, 0, 70), 0.012)
        sh.ink(q, (40, 36, 36, 255), 0.008, seed=r * 9 + c, var=0.3)
        if rnd.random() < 0.08:
            sh.line(HD.crack(q, rnd), fill=(30, 26, 26, 200), width=0.008)
        if rnd.random() < 0.12:                                                       # Schmutzfleck
            cx = sum(p[0] for p in q) / 4
            cy = sum(p[1] for p in q) / 4
            sh.poly(HD.wobble_ellipse(cx, cy, 0.07, 0.05, amp=0.012, seed=r + c), fill=(60, 44, 30, 45))
    return mottle(sh.finish(seed=seed), 0.06, seed + 2)


def tile_steinplatten(ppm, seed=1, base=(104, 108, 120), joint=(58, 58, 64)):
    """Steinplatten (Keller, Kapelle, Gruft): grau-blau, Laeuferverband, abgesackt, Moos in den Fugen."""
    T = TILE_M
    sh = Sheet(T, T, ppm, joint, periodic=True)
    rnd = random.Random(seed)
    stones = HD.stone_grid(0, 0, T, T, 0.7, 0.45, seed=seed, joint=0.03, jitter=0.12, tilt=0.02, skip=0.0, split=0.1,
                           merge=0.04, periodic=True, bond=0.5, rounding=0.05)
    for i, st in enumerate(stones):
        pts = st.chip or st.pts
        col = _tone(base, (1 + st.tone * 0.08) * (0.82 if st.sunk else 1.0) * (1.1 if st.worn else 1.0))
        col = _tint(col, rnd.choice([(1, 1, 1), (1, 1, 1), (1.04, 1.0, 0.94), (0.94, 0.98, 1.06)]))
        sh.poly(pts, fill=col)
        edge_light(sh, pts, _tone(col, 1.16) + (160,), (0, 0, 0, 75), 0.014)
        sh.ink(pts, (34, 32, 36, 255), 0.012, seed=i, var=0.3)
        if st.crack:
            sh.line(st.crack, fill=(30, 28, 32, 190), width=0.008)
        if rnd.random() < 0.25:                                                       # Moos an der Fuge
            for _ in range(5):
                sh.ellipse(rnd.uniform(st.x0, st.x1), st.y1 - rnd.uniform(0, 0.03), 0.014, 0.01, fill=(92, 130, 70, 170))
        if rnd.random() < 0.1:                                                        # feuchter Fleck
            sh.poly(HD.wobble_ellipse((st.x0 + st.x1) / 2, (st.y0 + st.y1) / 2, 0.12, 0.07, amp=0.02, seed=i), fill=(20, 24, 34, 50))
    return mottle(sh.finish(seed=seed), 0.05, seed + 3)


def tile_teppich(ppm, seed=1, base=BORDEAUX):
    """Bordeaux-Teppich (Bibliothek, Arbeitszimmer): Rautengitter mit Vierpass-Medaillons und Goldpunkten,
    Flor leicht fleckig, einzelne verblasste Stellen. Die Ornamentkante liefert teppich_kante()."""
    T = TILE_M
    sh = Sheet(T, T, ppm, base, periodic=True)
    rnd = random.Random(seed)
    P = 0.5
    dark, light = _tone(base, 0.78), _tone(base, 1.18)
    for i in range(int(T / P)):
        for j in range(int(T / P)):
            x, y = i * P, j * P
            sh.line([(x, y + P / 2), (x + P / 2, y), (x + P, y + P / 2), (x + P / 2, y + P), (x, y + P / 2)], fill=dark, width=0.012)   # Raute
            cx, cy = x + P / 2, y + P / 2
            for k in range(4):                                                        # Vierpass
                a = k * math.pi / 2
                sh.ellipse(cx + 0.06 * math.cos(a), cy + 0.06 * math.sin(a), 0.045, 0.045, fill=light)
            sh.ellipse(cx, cy, 0.03, 0.03, fill=base)
            sh.ellipse(cx, cy, 0.012, 0.012, fill=BRASS)
            for k in range(4):                                                        # Goldpunkte an den Rautenecken
                ex, ey = (x, cy) if k == 0 else (cx, y) if k == 1 else (x + P, cy) if k == 2 else (cx, y + P)
                sh.ellipse(ex, ey, 0.014, 0.014, fill=_tone(BRASS, 0.9))
            sh.poly([(cx - 0.05, y + 0.05), (cx, y + 0.1), (cx + 0.05, y + 0.05), (cx, y)], fill=dark)   # kleine Raute am Rand
    for _ in range(3):                                                                # verblasste Stellen
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.3, 0.2, amp=0.03, seed=rnd.randint(0, 99)), fill=(255, 240, 220, 22))
    sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.12, 0.09, amp=0.02, seed=5), fill=(40, 10, 20, 70))   # Weinfleck
    img = mottle(sh.finish(grain=0.045, seed=seed), 0.06, seed + 4, periods=(3, 5, 8))
    return img


def teppich_kante(length_m, ppm, seed=1, width_m=0.3, base=BORDEAUX):
    """Ornamentkante des Teppichs (Maeander in Gold zwischen zwei Goldlinien), waagrechter Streifen RGB."""
    sh = Sheet(length_m, width_m, ppm, _tone(base, 0.85))
    gold = _tone(BRASS, 1.05)
    sh.line([(0, 0.03), (length_m, 0.03)], fill=gold, width=0.012)
    sh.line([(0, width_m - 0.03), (length_m, width_m - 0.03)], fill=gold, width=0.012)
    s = 0.12
    x = 0.0
    while x < length_m:
        y0, y1 = width_m / 2 - 0.08, width_m / 2 + 0.08
        pts = [(x, y1), (x, y0), (x + s * 0.75, y0), (x + s * 0.75, y1 - 0.05), (x + s * 0.3, y1 - 0.05), (x + s * 0.3, y0 + 0.05), (x + s * 0.5, y0 + 0.05)]
        sh.line(pts, fill=gold, width=0.012)
        x += s
    return mottle(sh.finish(grain=0.04, seed=seed), 0.05, seed + 9)


def tile_kies(ppm, seed=1, base=(134, 128, 114)):
    """Kies (Vorplatz): Sandgrund mit hunderten kleinen Steinen in Grau, Beige und Braun."""
    T = TILE_M
    sh = Sheet(T, T, ppm, base, periodic=True)
    rnd = random.Random(seed)
    for _ in range(6):
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.35, 0.2, amp=0.04, seed=rnd.randint(0, 99)), fill=(90, 80, 66, 50))
    pal = [(140, 136, 130), (170, 156, 130), (128, 110, 92), (190, 186, 176), (150, 140, 120), (110, 104, 100)]
    for i in range(900):
        x, y = rnd.uniform(0, T), rnd.uniform(0, T)
        rx, ry = rnd.uniform(0.015, 0.04), rnd.uniform(0.012, 0.03)
        a = rnd.uniform(0, math.pi)
        col = _tone(rnd.choice(pal), 1 + rnd.uniform(-0.08, 0.08))
        pts = [(x + rx * math.cos(t) * math.cos(a) - ry * math.sin(t) * math.sin(a), y + rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a))
               for t in [k * math.tau / 8 for k in range(8)]]
        sh.poly(pts, fill=col, outline=_tone(col, 0.55) + (170,), width=0.006)
        sh.ellipse(x - rx * 0.3, y - ry * 0.3, rx * 0.3, ry * 0.3, fill=(255, 250, 240, 90))
    return mottle(sh.finish(seed=seed), 0.05, seed + 5)


def tile_terrasse(ppm, seed=1, base=(146, 142, 126), joint=(74, 72, 66)):
    """Natursteinplatten der Terrasse: unregelmaessig, abgerundet, Gras und Moos in den Fugen."""
    T = TILE_M
    sh = Sheet(T, T, ppm, joint, periodic=True)
    rnd = random.Random(seed)
    stones = HD.stone_grid(0, 0, T, T, 0.95, 0.6, seed=seed, joint=0.04, jitter=0.2, tilt=0.025, skip=0.02, split=0.15,
                           merge=0.05, periodic=True, bond=None, rounding=0.1)
    for i, st in enumerate(stones):
        pts = st.chip or st.pts
        if st.gap:
            sh.poly(pts, fill=(96, 92, 70))
            for _ in range(6):
                for seg in HD.tuft(rnd.uniform(st.x0 + 0.05, st.x1 - 0.05), rnd.uniform(st.y0 + 0.05, st.y1 - 0.05), rnd, n=3, h=0.06):
                    (ax, ay), (bx, by) = seg
                    sh.line([(ax, ay), (bx, ay - (by - ay))], fill=(104, 136, 66), width=0.012)
            continue
        col = _tint(_tone(base, (1 + st.tone * 0.09) * (0.85 if st.sunk else 1.0) * (1.08 if st.worn else 1.0)),
                    rnd.choice([(1, 1, 1), (1.05, 1.0, 0.92), (0.95, 0.97, 1.04), (1, 1, 1)]))
        sh.poly(pts, fill=col)
        edge_light(sh, pts, _tone(col, 1.14) + (160,), (0, 0, 0, 75), 0.016)
        sh.ink(pts, (50, 44, 36, 255), 0.013, seed=i, var=0.3)
        if st.crack:
            sh.line(st.crack, fill=(50, 44, 36, 200), width=0.008)
        for _ in range(3):                                                            # Flechten
            sh.ellipse(rnd.uniform(st.x0, st.x1), rnd.uniform(st.y0, st.y1), 0.018, 0.014, fill=(184, 190, 120, 110))
        if rnd.random() < 0.3:                                                        # Gras in der Fuge
            for seg in HD.tuft(rnd.uniform(st.x0, st.x1), st.y1 + 0.01, rnd, n=4, h=0.07):
                (ax, ay), (bx, by) = seg
                sh.line([(ax, ay), (bx, ay - (by - ay))], fill=(104, 136, 66), width=0.012)
        if rnd.random() < 0.2:
            sh.poly(HD.wobble_ellipse(st.x0 + 0.08, st.y1 - 0.06, 0.07, 0.04, amp=0.015, seed=i), fill=(92, 130, 70, 150))
    return mottle(sh.finish(seed=seed), 0.05, seed + 6)


def tile_wiese(ppm, seed=1, base=(64, 90, 60)):
    """Verwilderte Wiese: fleckiges Gruen, kahle Stellen, viele Halmbueschel, Samenstaende, welke Blaetter."""
    T = TILE_M
    sh = Sheet(T, T, ppm, base, periodic=True)
    rnd = random.Random(seed)
    for _ in range(4):                                                                # kahle Erde
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.3, 0.18, amp=0.04, seed=rnd.randint(0, 99)), fill=(110, 88, 64, 120))
    for _ in range(6):
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.4, 0.3, amp=0.05, seed=rnd.randint(0, 99)), fill=(60, 96, 50, 90))
    tufts(sh, rnd, 420, [(104, 140, 80), (56, 82, 50), (124, 134, 82)], h=0.09)
    for _ in range(14):                                                               # Samenstaende und Blueten
        x, y = rnd.uniform(0, T), rnd.uniform(0, T)
        sh.line([(x, y), (x + rnd.uniform(-0.03, 0.03), y - 0.14)], fill=(90, 120, 60), width=0.01)
        if rnd.random() < 0.5:
            sh.ellipse(x, y - 0.15, 0.03, 0.03, fill=(236, 236, 226, 170))
        else:
            sh.ellipse(x, y - 0.15, 0.02, 0.02, fill=(238, 214, 90))
    for _ in range(10):
        leaf(sh, rnd.uniform(0, T), rnd.uniform(0, T), rnd.uniform(0.06, 0.1), rnd.uniform(0, math.pi), rnd.choice([(150, 90, 40), (120, 70, 40)]))
    for _ in range(5):
        sh.ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.03, 0.022, fill=(136, 132, 124), outline=(60, 56, 50), width=0.006)
    return mottle(sh.finish(seed=seed), 0.08, seed + 7, periods=(2, 3, 6))


def tile_friedhofserde(ppm, seed=1, base=(90, 78, 64)):
    """Friedhofserde: feuchte Erde, Grasbueschel, Laub in Orange und Braun, Zweige, kleine Steine."""
    T = TILE_M
    sh = Sheet(T, T, ppm, base, periodic=True)
    rnd = random.Random(seed)
    for _ in range(6):
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.35, 0.22, amp=0.05, seed=rnd.randint(0, 99)), fill=(60, 44, 32, 70))
    for _ in range(60):
        x, y = rnd.uniform(0, T), rnd.uniform(0, T)
        sh.ellipse(x, y, rnd.uniform(0.01, 0.025), rnd.uniform(0.008, 0.018), fill=(128, 116, 100), outline=(56, 48, 40, 160), width=0.005)
    tufts(sh, rnd, 130, [(128, 140, 70), (90, 112, 60)], h=0.08)
    for _ in range(8):                                                                # Zweige
        x, y = rnd.uniform(0, T), rnd.uniform(0, T)
        a = rnd.uniform(0, math.pi)
        ln = rnd.uniform(0.15, 0.35)
        pts = HD.wobble([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], amp=0.01, seed=rnd.randint(0, 99), step=0.05)
        sh.line(pts, fill=(70, 50, 34), width=0.012)
        sh.line([pts[len(pts) // 2], (pts[len(pts) // 2][0] + math.cos(a + 0.8) * 0.08, pts[len(pts) // 2][1] + math.sin(a + 0.8) * 0.08)], fill=(70, 50, 34), width=0.008)
    for _ in range(45):
        leaf(sh, rnd.uniform(0, T), rnd.uniform(0, T), rnd.uniform(0.07, 0.12), rnd.uniform(0, math.pi),
             rnd.choice([(196, 112, 50), (164, 82, 40), (206, 154, 62), (124, 72, 40), (180, 60, 40)]))
    return mottle(sh.finish(seed=seed), 0.07, seed + 8)


def tile_glashaus(ppm, seed=1, base=(156, 106, 86), grout=(108, 104, 96)):
    """Gewaechshausfliesen 0,2 m in Terrakotta mit gruener Patina, Moos in den Fugen, einzelne fehlen."""
    T = TILE_M
    sh = Sheet(T, T, ppm, grout, periodic=True)
    rnd = random.Random(seed)
    for r, c, pts in HD.jitter_grid(0, 0, T, T, 0.2, seed=seed, jitter=0.05, periodic=True):
        q = shrink(pts, 0.006)
        cx = sum(p[0] for p in q) / 4
        cy = sum(p[1] for p in q) / 4
        if rnd.random() < 0.03:                                                       # fehlende Fliese: Erde
            sh.poly(q, fill=(72, 58, 44))
            for _ in range(3):
                sh.ellipse(cx + rnd.uniform(-0.06, 0.06), cy + rnd.uniform(-0.06, 0.06), 0.012, 0.009, fill=(120, 108, 96))
            continue
        col = _tint(_tone(base, 1 + rnd.uniform(-0.08, 0.08)), rnd.choice([(1, 1, 1), (1, 1, 1), (0.95, 1.0, 1.0), (1.05, 0.97, 0.9)]))
        if rnd.random() < 0.1:
            q = HD.chip(q, rnd, 0.2)
        sh.poly(q, fill=col)
        sh.poly([q[0], (q[0][0] + (q[1][0] - q[0][0]) * 0.5, q[0][1] + (q[1][1] - q[0][1]) * 0.5), (cx, cy), (q[0][0] + (q[3][0] - q[0][0]) * 0.5, q[0][1] + (q[3][1] - q[0][1]) * 0.5)],
                fill=(255, 240, 220, 28))                                             # Glasurglanz
        if rnd.random() < 0.35:                                                       # Patina
            for _ in range(rnd.randint(1, 3)):
                sh.poly(HD.wobble_ellipse(cx + rnd.uniform(-0.06, 0.06), cy + rnd.uniform(-0.06, 0.06), rnd.uniform(0.03, 0.07), rnd.uniform(0.02, 0.05), amp=0.01, seed=r * 13 + c),
                        fill=(96, 150, 118, 120))
        edge_light(sh, q, _tone(col, 1.15) + (160,), (0, 0, 0, 70), 0.01)
        sh.ink(q, (60, 40, 30, 255), 0.008, seed=r * 7 + c, var=0.3)
        if rnd.random() < 0.08:
            sh.line(HD.crack(q, rnd), fill=(50, 34, 26, 200), width=0.007)
    for _ in range(50):                                                               # Moos in den Fugen
        sh.ellipse(rnd.uniform(0, T), round(rnd.uniform(0, T) / 0.2) * 0.2 + rnd.uniform(-0.01, 0.01), 0.014, 0.01, fill=(84, 128, 70, 180))
    return mottle(sh.finish(seed=seed), 0.05, seed + 10)


_TILE_FN = {"parkett": tile_parkett, "dielen": tile_dielen, "fliesen_schachbrett": tile_fliesen, "steinplatten": tile_steinplatten,
            "teppich": tile_teppich, "kies": tile_kies, "terrasse": tile_terrasse, "wiese": tile_wiese,
            "friedhofserde": tile_friedhofserde, "glashausfliesen": tile_glashaus}


def material_tile(name, ppm, seed=1):
    """Nahtlose Kachel (TILE_M x TILE_M m) als PIL.Image RGB."""
    return _TILE_FN[name](ppm, seed)


# ------------------------------------------------------------------ Wandstirnseiten

def _damask(sh, x, y, s, col_a, col_b):
    """Ein Damast-Motiv (Ogee-Raute mit dreiblaettriger Palmette und Punkten), Mitte (x, y), Hoehe s."""
    w = s * 0.6
    pts = [(x, y - s / 2), (x + w * 0.35, y - s * 0.3), (x + w / 2, y), (x + w * 0.35, y + s * 0.3), (x, y + s / 2),
           (x - w * 0.35, y + s * 0.3), (x - w / 2, y), (x - w * 0.35, y - s * 0.3)]
    sh.poly(pts, outline=col_a, width=0.012)
    sh.ellipse(x, y + s * 0.05, w * 0.12, s * 0.22, fill=col_b)
    for sx in (-1, 1):
        sh.poly([(x, y + s * 0.12), (x + sx * w * 0.3, y - s * 0.1), (x + sx * w * 0.22, y + s * 0.15), (x, y + s * 0.25)], fill=col_b)
    sh.ellipse(x, y - s * 0.3, 0.012, 0.012, fill=col_a)
    sh.ellipse(x, y + s * 0.38, 0.012, 0.012, fill=col_a)
    for sx in (-1, 1):
        sh.ellipse(x + sx * w * 0.42, y, 0.01, 0.01, fill=col_b)


def _wall_tapete_compact(W, H, ppm, seed):
    """Innenwand (0,4 m Wandmasse): Gesims, schmales Damastband, Stuhlleiste, Vertaefelung, Fussleiste."""
    sh = Sheet(W, H, ppm, BORDEAUX)
    rnd = random.Random(seed)
    corn = min(0.05, H * 0.15)
    rail_v = H * 0.55
    s = max(0.12, (rail_v - corn) * 0.8)
    x = 0.12
    col = 0
    while x < W + 0.2:
        _damask(sh, x, corn + (rail_v - corn) / 2, s, BORDEAUX_D, BORDEAUX_L)
        x += s * 1.2
        col += 1
    sh.poly(HD.wobble_ellipse(rnd.uniform(0.2, max(0.3, W - 0.2)), corn + 0.05, 0.2, 0.06, amp=0.02, seed=seed + 3), fill=(30, 10, 14, 60))
    sh.rect(0, 0, W, corn, fill=(190, 180, 162))
    sh.line([(0, corn + 0.005), (W, corn + 0.005)], fill=(40, 10, 14, 120), width=0.01)
    sh.rect(0, rail_v, W, H, fill=WALNUT)
    sh.rect(0, rail_v, W, rail_v + 0.03, fill=WALNUT_L)
    sh.line([(0, rail_v + 0.035), (W, rail_v + 0.035)], fill=(0, 0, 0, 110), width=0.01)
    pw = 0.6
    nx = max(1, int(round(W / pw)))
    pw = W / nx
    base_v = H - 0.05
    for k in range(nx):
        q = [(k * pw + 0.05, rail_v + 0.06), ((k + 1) * pw - 0.05, rail_v + 0.06), ((k + 1) * pw - 0.05, base_v - 0.03), (k * pw + 0.05, base_v - 0.03)]
        if q[2][1] - q[0][1] < 0.04:
            continue
        sh.poly(q, fill=_tone(WALNUT, 1.08))
        edge_light(sh, q, _tone(WALNUT_L, 1.1) + (200,), (0, 0, 0, 90), 0.012)
        sh.ink(q, (60, 40, 26, 255), 0.008, seed=k, var=0.3)
    sh.rect(0, base_v, W, H, fill=WALNUT_D)
    sh.rect(0, H - 0.02, W, H, fill=(40, 28, 20))
    sh.rect(0, base_v - 0.02, W, base_v, fill=(0, 0, 0, 40))
    return mottle(sh.finish(grain=0.025, seed=seed), 0.04, seed + 11).convert("RGBA")


def _wall_tapete(W, H, ppm, seed):
    if H < 0.7:
        return _wall_tapete_compact(W, H, ppm, seed)
    sh = Sheet(W, H, ppm, BORDEAUX)
    rnd = random.Random(seed)
    corn = 0.06
    rail_v = H * 0.6
    # Damast: zwei Spalten versetzt, dezent (dunkler Umriss, hellere Palmette)
    s = 0.34
    col = 0
    x = 0.2
    while x < W + 0.2:
        y = corn + 0.2 + (s * 0.5 if col % 2 else 0)
        while y < rail_v:
            _damask(sh, x, y, s, BORDEAUX_D, BORDEAUX_L)
            y += s * 1.05
        x += 0.42
        col += 1
    # Wasserflecken, loser Tapetenfetzen mit Putz dahinter, Spinnwebe in der Ecke
    for _ in range(2):
        sx = rnd.uniform(0.2, W - 0.2)
        sh.poly(HD.wobble_ellipse(sx, corn + 0.1, 0.25, 0.12, amp=0.03, seed=seed + 3), fill=(30, 10, 14, 70))
        sh.poly(HD.wobble_ellipse(sx, corn + 0.2, 0.18, 0.14, amp=0.03, seed=seed + 4), fill=(30, 10, 14, 45))
    if W > 1.5:
        tx = rnd.uniform(0.3, W - 0.6)
        tear = [(tx, corn + 0.02), (tx + 0.3, corn + 0.02), (tx + 0.22, corn + 0.18), (tx + 0.28, corn + 0.32), (tx + 0.1, corn + 0.26), (tx + 0.04, corn + 0.14)]
        tear = HD.wobble(tear, amp=0.01, seed=seed, step=0.04, closed=True)
        sh.poly(tear, fill=(190, 176, 150))
        for k in range(4):
            sh.line([(tx + 0.04 + k * 0.06, corn + 0.04), (tx + 0.06 + k * 0.06, corn + 0.12)], fill=(150, 136, 112), width=0.006)
        sh.ink(tear, (60, 20, 26, 255), 0.01, seed=seed, var=0.3)
        sh.poly([(tx + 0.1, corn + 0.26), (tx + 0.28, corn + 0.32), (tx + 0.2, corn + 0.42)], fill=BORDEAUX_D, outline=(60, 20, 26), width=0.008)   # haengender Fetzen
    # leerer Bilderrahmen, leicht schief
    if W >= 2.0:
        fx = rnd.uniform(0.5, W - 0.5)
        fy = corn + (rail_v - corn) * 0.5
        a = math.radians(rnd.uniform(-5, 5))
        def R(px_, py_):
            return (fx + px_ * math.cos(a) - py_ * math.sin(a), fy + px_ * math.sin(a) + py_ * math.cos(a))
        fr = [R(-0.22, -0.16), R(0.22, -0.16), R(0.22, 0.16), R(-0.22, 0.16)]
        sh.poly(fr, fill=(60, 48, 40), outline=OUTLINE, width=0.02)
        sh.poly([R(-0.19, -0.13), R(0.19, -0.13), R(0.19, 0.13), R(-0.19, 0.13)], fill=(28, 22, 24))
        sh.poly(fr, outline=BRASS, width=0.025)
        for k in range(8):
            sh.ellipse(*R(-0.19 + k * 0.054, -0.16), 0.012, 0.012, fill=(214, 176, 90))
            sh.ellipse(*R(-0.19 + k * 0.054, 0.16), 0.012, 0.012, fill=(214, 176, 90))
        sh.line([R(0, -0.16), R(0, -0.26)], fill=(40, 34, 36), width=0.008)
    # Gesims, Bilderleiste
    sh.rect(0, 0, W, corn, fill=(202, 192, 172))
    sh.line([(0, corn - 0.012), (W, corn - 0.012)], fill=(150, 140, 122), width=0.012)
    sh.line([(0, corn + 0.006), (W, corn + 0.006)], fill=(40, 10, 14, 120), width=0.012)
    sh.line([(0, corn + 0.07), (W, corn + 0.07)], fill=WALNUT_D, width=0.014)
    # Vertaefelung: Stuhlleiste, Felder mit erhabenem Spiegel, Fussleiste
    sh.rect(0, rail_v, W, H, fill=WALNUT)
    sh.rect(0, rail_v, W, rail_v + 0.04, fill=WALNUT_L, outline=None)
    sh.line([(0, rail_v + 0.045), (W, rail_v + 0.045)], fill=(0, 0, 0, 110), width=0.012)
    base_v = H - 0.09
    pw = 0.6
    nx = max(1, int(round(W / pw)))
    pw = W / nx
    for k in range(nx):
        px0, px1 = k * pw + 0.05, (k + 1) * pw - 0.05
        py0, py1 = rail_v + 0.09, base_v - 0.05
        if py1 - py0 < 0.08:
            continue
        sh.rect(px0, py0, px1, py1, fill=WALNUT_D)
        q = [(px0 + 0.04, py0 + 0.04), (px1 - 0.04, py0 + 0.04), (px1 - 0.04, py1 - 0.04), (px0 + 0.04, py1 - 0.04)]
        sh.poly(q, fill=_tone(WALNUT, 1.08))
        edge_light(sh, q, _tone(WALNUT_L, 1.1) + (200,), (0, 0, 0, 90), 0.014)
        for g in range(3):                                                            # Maserung
            gy = py0 + 0.08 + g * (py1 - py0 - 0.16) / 2
            sh.line(HD.wobble([(px0 + 0.08, gy), (px1 - 0.08, gy + 0.01)], amp=0.006, seed=k * 3 + g, step=0.06), fill=_tone(WALNUT, 0.85) + (140,), width=0.006)
        sh.ink(q, (60, 40, 26, 255), 0.01, seed=k, var=0.3)
    sh.rect(0, base_v, W, H, fill=WALNUT_D)
    sh.line([(0, base_v + 0.01), (W, base_v + 0.01)], fill=WALNUT_L, width=0.012)
    sh.rect(0, H - 0.03, W, H, fill=(40, 28, 20))
    # Staubschleier an der Fussleiste, Spinnwebe oben in einer Ecke
    sh.rect(0, base_v - 0.03, W, base_v, fill=(0, 0, 0, 40))
    cx, qx = (0.0, 1) if seed % 2 == 0 else (W, -1)
    for k in range(6):
        a = (math.pi / 2) * k / 5
        sh.line([(cx, corn), (cx + qx * 0.3 * math.cos(a), corn + 0.3 * math.sin(a))], fill=(232, 236, 242, 110), width=0.006)
    for r in (0.1, 0.18, 0.26):
        sh.line([(cx + qx * r * math.cos((math.pi / 2) * k / 5) * rnd.uniform(0.9, 1), corn + r * math.sin((math.pi / 2) * k / 5)) for k in range(6)],
                fill=(232, 236, 242, 100), width=0.005)
    return mottle(sh.finish(grain=0.025, seed=seed), 0.04, seed + 11).convert("RGBA")


def _wall_ziegel(W, H, ppm, seed):
    sh = Sheet(W, H, ppm, (120, 110, 98))
    rnd = random.Random(seed)
    stones = HD.stone_grid(0, 0, W, H, 0.24, 0.085, seed=seed, joint=0.012, jitter=0.08, tilt=0.0, skip=0.0, split=0.0,
                           merge=0.0, periodic=False, bond=0.5)
    base = (152, 86, 66)
    for i, st in enumerate(stones):
        pts = st.chip or st.pts
        col = _tint(_tone(base, 1 + st.tone * 0.1), rnd.choice([(1, 1, 1), (1, 1, 1), (0.8, 0.78, 0.84), (1.1, 1.2, 1.25), (0.9, 0.7, 0.6)]))
        sh.poly(pts, fill=col)
        edge_light(sh, pts, _tone(col, 1.18) + (150,), (0, 0, 0, 80), 0.008)
        sh.ink(pts, (56, 36, 30, 255), 0.007, seed=i, var=0.3)
        if st.crack:
            sh.line(st.crack, fill=(40, 26, 22, 180), width=0.006)
    sh.rect(0, H - 0.25, W, H, fill=(20, 16, 14, 50))                                  # Spritzwasser, dunkler Fuss
    sh.rect(0, H - 0.1, W, H, fill=(20, 16, 14, 60))
    for _ in range(6):                                                                # Moos
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, W), H - rnd.uniform(0.02, 0.2), 0.06, 0.03, amp=0.012, seed=rnd.randint(0, 99)), fill=(84, 120, 66, 150))
    if W > 1.2:                                                                       # Efeu an einer Seite
        vx = rnd.uniform(0.2, W - 0.2)
        vine = HD.wobble([(vx, H), (vx + rnd.uniform(-0.15, 0.15), H * 0.6), (vx + rnd.uniform(-0.2, 0.2), H * 0.25)], amp=0.03, seed=seed, step=0.05)
        sh.line(vine, fill=(50, 70, 40), width=0.012)
        for k, (lx, ly) in enumerate(vine[::2]):
            sh.poly([(lx, ly), (lx + 0.04, ly - 0.03), (lx + 0.02, ly - 0.07), (lx - 0.02, ly - 0.07), (lx - 0.04, ly - 0.03)],
                    fill=(70, 112, 60) if k % 2 else (88, 128, 70), outline=(30, 50, 30), width=0.005)
    return mottle(sh.finish(grain=0.025, seed=seed), 0.04, seed + 12).convert("RGBA")


def _wall_stein(W, H, ppm, seed):
    sh = Sheet(W, H, ppm, (66, 64, 66))
    rnd = random.Random(seed)
    stones = HD.stone_grid(0, 0, W, H, 0.5, 0.26, seed=seed, joint=0.03, jitter=0.2, tilt=0.02, skip=0.0, split=0.15,
                           merge=0.06, periodic=False, bond=None, rounding=0.1)
    base = (122, 120, 124)
    for i, st in enumerate(stones):
        pts = st.chip or st.pts
        col = _tint(_tone(base, (1 + st.tone * 0.1) * (0.85 if st.sunk else 1.0)), rnd.choice([(1, 1, 1), (1.04, 1.0, 0.94), (0.94, 0.98, 1.06)]))
        sh.poly(pts, fill=col)
        edge_light(sh, pts, _tone(col, 1.18) + (160,), (0, 0, 0, 90), 0.016)
        sh.ink(pts, (34, 32, 36, 255), 0.013, seed=i, var=0.3)
        if st.crack:
            sh.line(st.crack, fill=(30, 28, 32, 200), width=0.008)
    for k in range(3):                                                                # feuchter Fuss
        sh.rect(0, H - 0.12 * (k + 1), W, H, fill=(10, 14, 24, 35))
    for _ in range(8):
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, W), H - rnd.uniform(0.02, 0.3), 0.07, 0.035, amp=0.015, seed=rnd.randint(0, 99)), fill=(84, 124, 70, 150))
    cx, qx = (W, -1) if seed % 2 else (0.0, 1)
    for k in range(6):
        a = (math.pi / 2) * k / 5
        sh.line([(cx, 0), (cx + qx * 0.28 * math.cos(a), 0.28 * math.sin(a))], fill=(232, 236, 242, 100), width=0.006)
    for r in (0.1, 0.18, 0.25):
        sh.line([(cx + qx * r * math.cos((math.pi / 2) * k / 5), r * math.sin((math.pi / 2) * k / 5)) for k in range(6)], fill=(232, 236, 242, 90), width=0.005)
    return mottle(sh.finish(grain=0.025, seed=seed), 0.05, seed + 13).convert("RGBA")


def _wall_hecke(W, H, ppm, seed):
    """Hecke wie park_floor.draw_hedge: Blaetterballen in zwei Gruentoenen, zittriger Umriss, Lichtkante,
    Beeren, dunkler Fuss. Oben unregelmaessig (transparent), damit die Wandkrone nicht glatt abschneidet."""
    sh = Sheet(W, H, ppm, (0, 0, 0, 0), mode="RGBA")
    rnd = random.Random(seed)
    sh.rect(0, H * 0.4, W, H, fill=(28, 54, 36, 255))
    blobs = []
    x = -0.05
    while x < W + 0.3:
        r = rnd.uniform(0.2, 0.34)
        v = r * 0.95 + rnd.uniform(0, max(0.0, H - r * 1.6))
        blobs.append((x, v, r, rnd.uniform(0.85, 1.25)))
        x += r * 1.15
    blobs.sort(key=lambda b: -b[1])
    for i, (bx, by, r, t) in enumerate(blobs):
        pts = HD.wobble_ellipse(bx, by, r, r * 0.9, amp=0.02, seed=i + seed)
        col = _tone(HEDGE, t)
        sh.poly(pts, fill=col + (255,))
        sh.ink(pts, (10, 22, 14, 255), 0.025, seed=i, var=0.3)
        hl = HD.wobble_ellipse(bx - r * 0.25, by - r * 0.3, r * 0.5, r * 0.35, amp=0.01, seed=i + 7)
        # Lichtkante nur innerhalb des Ballens: kleine Ellipse liegt im Ballen
        sh.poly(hl, fill=_tone(col, 1.35) + (255,))
        if rnd.random() < 0.25:
            for _ in range(3):
                sh.ellipse(bx + rnd.uniform(-r * 0.5, r * 0.5), by + rnd.uniform(-r * 0.4, r * 0.4), 0.022, 0.022, fill=(200, 60, 70, 255), outline=(60, 20, 24, 255), width=0.01)
    sh.blend(lambda d: d.rectangle([sh.P([(0, H - 0.1)])[0], sh.P([(W, H)])[0]], fill=(0, 0, 0, 110)))
    return sh.finish(grain=0)


def _wall_zaun(W, H, ppm, seed):
    """Schmiedeeiserner Zaun, durchsichtig: Steinsockel, Staebe mit Speerspitzen, zwei Riegel, Schnoerkel,
    Rost, eine Spinnwebe."""
    sh = Sheet(W, H, ppm, (0, 0, 0, 0), mode="RGBA")
    rnd = random.Random(seed)
    pl = 0.12
    sh.rect(0, H - pl, W, H, fill=(118, 116, 120, 255), outline=(30, 28, 32, 255), width=0.012)
    x = 0.0
    while x < W:
        sh.line([(x, H - pl + 0.02), (x, H - 0.02)], fill=(80, 78, 84, 255), width=0.008)
        x += rnd.uniform(0.35, 0.6)
    sh.line([(0, H - pl + 0.012), (W, H - pl + 0.012)], fill=(170, 168, 172, 255), width=0.01)
    top_rail, bot_rail = min(0.2, H * 0.35), H - pl - 0.18
    rails = (top_rail, bot_rail) if bot_rail > top_rail + 0.12 else (top_rail,)
    for rv in rails:
        sh.line([(0, rv), (W, rv)], fill=(30, 28, 32, 255), width=0.05)
        sh.line([(0, rv), (W, rv)], fill=IRON + (255,), width=0.03)
        sh.line([(0, rv - 0.01), (W, rv - 0.01)], fill=IRON_L + (255,), width=0.006)
    step = 0.16
    n = max(2, int(round(W / step)))
    step = W / n
    for k in range(n + 1):
        x = k * step
        big = k % 5 == 0
        top = 0.0 if big else 0.06
        sh.line([(x, top + 0.05), (x, H - pl)], fill=(30, 28, 32, 255), width=0.05)
        sh.line([(x, top + 0.05), (x, H - pl)], fill=IRON + (255,), width=0.028)
        sh.line([(x - 0.008, top + 0.08), (x - 0.008, H - pl - 0.02)], fill=IRON_L + (255,), width=0.006)
        if big:
            sh.ellipse(x, 0.07, 0.035, 0.035, fill=IRON + (255,), outline=(30, 28, 32, 255), width=0.012)
            sh.ellipse(x - 0.012, 0.058, 0.01, 0.01, fill=IRON_L + (255,))
        else:
            sh.poly([(x, top), (x + 0.028, top + 0.08), (x, top + 0.11), (x - 0.028, top + 0.08)], fill=IRON + (255,), outline=(30, 28, 32, 255), width=0.012)
        if k < n:                                                                     # Schnoerkel unter dem oberen Riegel
            cx = x + step / 2
            for sx in (-1, 1):
                pts = [(cx + sx * 0.005, top_rail + 0.02), (cx + sx * 0.04, top_rail + 0.05), (cx + sx * 0.045, top_rail + 0.1), (cx + sx * 0.015, top_rail + 0.13), (cx + sx * 0.0, top_rail + 0.1)]
                sh.line(pts, fill=(30, 28, 32, 255), width=0.03)
                sh.line(pts, fill=IRON + (255,), width=0.014)
    for _ in range(int(W * 12)):                                                      # Rost
        x = round(rnd.uniform(0, W) / step) * step
        sh.ellipse(x + rnd.uniform(-0.01, 0.01), rnd.uniform(0.2, H - pl), 0.012, 0.02, fill=(170, 90, 40, 255))
    wx = round(rnd.uniform(0.2, max(0.21, W - 0.3)) / step) * step                    # Spinnwebe zwischen zwei Staeben

    def web(d):
        for k in range(5):
            d.line(sh.P([(wx, top_rail), (wx + step * (k / 4), top_rail + 0.25 * (1 - k / 4) + 0.02)]), fill=(232, 236, 242, 120), width=sh.px(0.006))
        for r in (0.35, 0.65, 0.95):
            d.line(sh.P([(wx + step * r * (k / 4), top_rail + 0.25 * r * (1 - k / 4) + 0.02 * (1 - r) + 0.012 * math.sin(k)) for k in range(5)]),
                   fill=(232, 236, 242, 110), width=sh.px(0.005))
    sh.blend(web)
    return sh.finish(grain=0)


def _wall_putz(W, H, ppm, seed):
    """Fleckiger Putz (Kueche, Waschkueche, Abstellkammer): graugruen, Risse, Schimmel am Fuss,
    unten eine Reihe weisser Wandfliesen."""
    base = (146, 150, 138)
    sh = Sheet(W, H, ppm, base)
    rnd = random.Random(seed)
    for _ in range(int(W * 2) + 1):
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, W), rnd.uniform(0, H * 0.6), rnd.uniform(0.1, 0.3), rnd.uniform(0.05, 0.12), amp=0.03, seed=rnd.randint(0, 99)),
                fill=(70, 60, 50, 45))
    for _ in range(max(1, int(W / 1.2))):
        x = rnd.uniform(0.1, max(0.2, W - 0.1))
        pts = HD.wobble([(x, 0), (x + rnd.uniform(-0.1, 0.1), H * 0.3), (x + rnd.uniform(-0.15, 0.15), H * 0.55)], amp=0.015, seed=rnd.randint(0, 99), step=0.04)
        sh.line(pts, fill=(60, 56, 50, 200), width=0.008)
    tile_v = max(0.0, H - 0.3) if H > 0.5 else H * 0.45
    sh.rect(0, tile_v, W, H, fill=(96, 94, 90))
    for r, c, pts in HD.jitter_grid(0, tile_v, W, H, 0.15, seed=seed, jitter=0.02, periodic=False):
        q = shrink(pts, 0.005)
        col = _tone((204, 206, 198), 1 + rnd.uniform(-0.06, 0.06))
        sh.poly(q, fill=col)
        edge_light(sh, q, _tone(col, 1.12) + (160,), (0, 0, 0, 60), 0.008)
        if rnd.random() < 0.06:
            sh.line(HD.crack(q, rnd), fill=(50, 48, 46, 200), width=0.006)
    sh.line([(0, tile_v), (W, tile_v)], fill=(60, 56, 50), width=0.012)
    for _ in range(int(W * 3)):
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, W), H - rnd.uniform(0.0, 0.08), 0.05, 0.03, amp=0.01, seed=rnd.randint(0, 99)), fill=(40, 60, 40, 110))
    sh.rect(0, H - 0.02, W, H, fill=(40, 36, 34))
    return mottle(sh.finish(grain=0.025, seed=seed), 0.04, seed + 14).convert("RGBA")


def _wall_glashaus(W, H, ppm, seed):
    """Gewaechshauswand: weiss gestrichenes Eisengeruest, Glasscheiben mit Nachtblau und Beschlag,
    Ziegelsockel, eine Scheibe gesprungen."""
    sh = Sheet(W, H, ppm, (0, 0, 0, 0), mode="RGBA")
    rnd = random.Random(seed)
    sock = min(0.25, H * 0.4)
    sh.rect(0, 0, W, H - sock, fill=(30, 40, 56, 255))
    for _ in range(int(W * 2) + 1):
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, W), rnd.uniform(0, H - sock), 0.3, 0.12, amp=0.03, seed=rnd.randint(0, 99)), fill=(140, 170, 190, 40))
    step = 0.5
    n = max(1, int(round(W / step)))
    step = W / n
    for k in range(n + 1):
        x = k * step
        sh.line([(x, 0), (x, H - sock)], fill=(214, 216, 210, 255), width=0.035)
        sh.line([(x + 0.012, 0), (x + 0.012, H - sock)], fill=(120, 124, 120, 255), width=0.006)
    for v in (0.0, (H - sock) * 0.5):
        sh.line([(0, v), (W, v)], fill=(214, 216, 210, 255), width=0.03)
    for k in range(n):                                                                # Glanzstreifen je Scheibe
        x = k * step
        sh.line([(x + 0.08, (H - sock) * 0.08), (x + 0.2, (H - sock) * 0.42)], fill=(220, 236, 250, 70), width=0.025)
    if n > 1:
        k = rnd.randint(0, n - 1)
        cx, cy = k * step + step / 2, (H - sock) * 0.3
        for a in (0.4, 1.9, 3.4, 4.6, 5.6):
            sh.line([(cx, cy), (cx + 0.2 * math.cos(a), cy + 0.12 * math.sin(a))], fill=(230, 240, 250, 200), width=0.006)
    stones = HD.stone_grid(0, H - sock, W, H, 0.24, 0.085, seed=seed, joint=0.012, jitter=0.08, tilt=0.0, skip=0.0, split=0.0, merge=0.0, periodic=False, bond=0.5)
    for i, st in enumerate(stones):
        col = _tone((136, 84, 68), 1 + st.tone * 0.1)
        sh.poly(st.pts, fill=col + (255,))
        sh.ink(st.pts, (56, 36, 30, 255), 0.007, seed=i, var=0.3)
    sh.rect(0, H - 0.03, W, H, fill=(30, 22, 20, 255))
    return sh.finish(grain=0)


def wall_front(width_m, height_m, style, ppm, seed=1):
    """Stirnseite einer Nordwand im Bodenbild (Hoehe in Bildmetern, also schon mal K gerechnet) als RGBA."""
    fn = {"tapete": _wall_tapete, "ziegel": _wall_ziegel, "stein": _wall_stein, "hecke": _wall_hecke, "zaun": _wall_zaun,
          "putz": _wall_putz, "glashaus": _wall_glashaus}[style]
    return fn(width_m, height_m, ppm, seed)


# ------------------------------------------------------------------ Bodendetails
# Alle zeichnen auf einen ImageDraw d (Modus "RGBA" auf RGB-Bild) mit P(x, y) -> Pixel (Weltmeter -> px).

def floor_cable(d, P, ppm, pts, seed=1, width=0.035, col=(30, 30, 36)):
    """Kabel auf dem Boden: zittrige Linie mit weichem Schatten und Glanzstreifen."""
    q = [P(*p) for p in HD.wobble(pts, amp=0.02, seed=seed, step=0.08)]
    d.line(q, fill=(0, 0, 0, 70), width=max(1, int(width * 2.2 * ppm)), joint="curve")
    d.line(q, fill=col, width=max(1, int(width * ppm)), joint="curve")
    d.line([(x - 1, y - 1) for x, y in q], fill=(100, 102, 112, 110), width=max(1, int(width * 0.3 * ppm)), joint="curve")


def floor_tape_strip(d, P, ppm, x0, y0, x1, y1, w=0.05, col=GAFFER):
    """Gaffer-Tape-Streifen (z. B. ueber einem Kabel)."""
    d.line([P(x0, y0), P(x1, y1)], fill=col + (235,), width=max(1, int(w * ppm)))
    d.line([P(x0, y0), P(x1, y1)], fill=(0, 0, 0, 40), width=max(1, int(w * 0.25 * ppm)))


def floor_tape_mark(d, P, ppm, x, y, kind="T", ang=0.0, col=GAFFER):
    """Positionsmarke der Crew aus Tape: T, X oder L, Winkel ang (rad)."""
    c, s = math.cos(ang), math.sin(ang)

    def R(px_, py_):
        return P(x + px_ * c - py_ * s, y + px_ * s + py_ * c)

    w = max(1, int(0.05 * ppm))
    if kind == "T":
        d.line([R(-0.14, 0.1), R(0.14, 0.1)], fill=col + (235,), width=w)
        d.line([R(0, 0.1), R(0, -0.14)], fill=col + (235,), width=w)
    elif kind == "X":
        d.line([R(-0.1, -0.1), R(0.1, 0.1)], fill=col + (235,), width=w)
        d.line([R(-0.1, 0.1), R(0.1, -0.1)], fill=col + (235,), width=w)
    else:
        d.line([R(-0.12, 0.12), R(-0.12, -0.12), R(0.12, -0.12)], fill=col + (235,), width=w)


def floor_dolly_rail(d, P, ppm, x0, y, x1, gauge=0.62):
    """Dollyschiene quer: Schwellen alle 0,8 m, zwei Rohrschienen mit Glanz, Endstopper."""
    x = x0 + 0.2
    while x < x1 - 0.1:
        d.polygon([P(x - 0.05, y - gauge / 2 - 0.12), P(x + 0.05, y - gauge / 2 - 0.12), P(x + 0.05, y + gauge / 2 + 0.12), P(x - 0.05, y + gauge / 2 + 0.12)],
                  fill=(52, 52, 58), outline=(14, 12, 18))
        x += 0.8
    for ry in (y - gauge / 2, y + gauge / 2):
        d.line([P(x0, ry), P(x1, ry)], fill=(0, 0, 0, 80), width=max(1, int(0.09 * ppm)))
        d.line([P(x0, ry), P(x1, ry)], fill=(14, 12, 18), width=max(1, int(0.07 * ppm)))
        d.line([P(x0, ry), P(x1, ry)], fill=(120, 124, 134), width=max(1, int(0.04 * ppm)))
        d.line([P(x0, ry + 0.012), P(x1, ry + 0.012)], fill=(200, 204, 214), width=max(1, int(0.012 * ppm)))
    for ex in (x0, x1):
        d.rectangle([P(ex - 0.03, y + gauge / 2 + 0.06), P(ex + 0.03, y - gauge / 2 - 0.06)], fill=(60, 60, 66), outline=(14, 12, 18))


def floor_chalk_cross(d, P, ppm, x, y, size=0.22, seed=1):
    """Kreidekreuz (Markierung, Ritual): zwei zittrige weisse Striche."""
    for pts in (((x - size / 2, y - size / 2), (x + size / 2, y + size / 2)), ((x - size / 2, y + size / 2), (x + size / 2, y - size / 2))):
        q = [P(*p) for p in HD.wobble(list(pts), amp=0.01, seed=seed, step=0.04)]
        d.line(q, fill=(236, 232, 224, 170), width=max(1, int(0.025 * ppm)), joint="curve")


def floor_cobweb_corner(d, P, ppm, x, y, size=0.5, qx=1, qy=-1, seed=1):
    """Spinnweben-Ecke auf dem Boden (Ecke bei x, y; qx/qy Richtung in Weltmetern)."""
    rnd = random.Random(seed)
    n = 6
    for k in range(n + 1):
        a = (math.pi / 2) * k / n
        d.line([P(x, y), P(x + qx * size * math.cos(a), y + qy * size * math.sin(a))], fill=(232, 236, 242, 100), width=max(1, int(0.008 * ppm)))
    for r in (0.25, 0.45, 0.65, 0.85, 1.0):
        pts = [P(x + qx * r * size * rnd.uniform(0.9, 1.0) * math.cos((math.pi / 2) * k / n), y + qy * r * size * rnd.uniform(0.9, 1.0) * math.sin((math.pi / 2) * k / n)) for k in range(n + 1)]
        d.line(pts, fill=(232, 236, 242, 95), width=max(1, int(0.006 * ppm)), joint="curve")


def floor_leaves(d, P, ppm, x0, y0, x1, y1, n=20, seed=1):
    """Welkes Laub verstreut (Weltrechteck)."""
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        ln = rnd.uniform(0.07, 0.12)
        a = rnd.uniform(0, math.pi)
        col = rnd.choice([(196, 112, 50), (164, 82, 40), (206, 154, 62), (124, 72, 40)])
        c, s = math.cos(a), math.sin(a)
        pts = []
        for k in range(10):
            t = k / 10 * math.tau
            px_, py_ = math.cos(t) * ln / 2, math.sin(t) * ln * 0.22 * (1 - 0.3 * abs(math.cos(t)))
            pts.append(P(x + px_ * c - py_ * s, y + px_ * s + py_ * c))
        d.polygon(pts, fill=col, outline=_tone(col, 0.6))


# ------------------------------------------------------------------ ganzes Bodenbild

def render_map(ppm):
    """Bodenbild der grossen Karte in Plan-Lage, (50 x 36 m) * ppm (villa_floor_map.py)."""
    import villa_floor_map
    return villa_floor_map.render(ppm)
