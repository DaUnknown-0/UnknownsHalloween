# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_intro.py - der handgezeichnete Vorspann von Hollowmere Manor (Villa/HollowmereIntro.cs spielt ihn).
#
# 7 s, 12 Bilder pro Sekunde, 960 x 540 (gezeichnet in 1920 x 1080 und verkleinert), JPG nach
# Resources/villa/villa_intro_000.jpg ... Dazu tools/_villa_intro/intro_preview.webp (animiert) und
# intro_storyboard.png (jedes 6. Bild).
#
# Fuenf Einstellungen, harte Schnitte wie im Film:
#   A 0,0 - 1,8 s  Gewitternacht, Regen, ein Blitz zeigt die Villa auf dem Huegel, langsame Fahrt hinein
#   B 1,8 - 3,0 s  die Regieklappe "HOLLOWMERE MANOR / SCENE 1 / TAKE 1" faehrt ins Bild und schlaegt zu
#   C 3,0 - 4,6 s  Eingangshalle: die Crew stellt einen Scheinwerfer auf, der Lichtkegel geht an
#   D 4,6 - 5,8 s  Kandelaber nah: ein Windstoss, die Kerzen gehen eine nach der anderen aus
#   E 5,8 - 7,0 s  im Dunkeln das Ahnenportraet, die Augen gehen auf, Schnitt ins Schwarz
# Handgezeichnet: alle Umrisse zittern (handdraw.wobble) und "kochen" im 6-Bilder-Takt (neuer Zufall
# alle 2 Bilder), Filmkorn und Vignette ueber jedem Bild. Keine fremden Figuren, keine Marken.
#
#   python tools/villa_intro.py

import math
import os
import random
import sys
from pathlib import Path

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)

from PIL import Image, ImageDraw, ImageFilter, ImageFont   # noqa: E402

import handdraw as HD                                      # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "Resources" / "villa"
PREV = HERE / "_villa_intro"
FPS = 12
LENGTH = 7.0
W, H = 1920, 1080                 # Zeichenflaeche (2x), Ausgabe 960 x 540
INK = (16, 12, 20, 255)
FONT_DIR = r"C:\Windows\Fonts"

NIGHT_T, NIGHT_B = (20, 22, 48), (58, 36, 72)
HOUSE, HOUSE_L, ROOF = (34, 30, 44), (58, 52, 70), (24, 20, 32)
WIN = (255, 196, 96)
MOON = (232, 228, 206)
WALL, WALL_D = (96, 34, 48), (72, 24, 36)
WOOD, WOOD_D = (110, 72, 46), (70, 46, 30)
BRASS = (196, 156, 80)
CREW = [((198, 40, 50), (120, 20, 30)), ((60, 190, 210), (30, 110, 130)), ((236, 200, 60), (160, 120, 20))]


def font(size, bold=True):
    for name in (("impact.ttf",) if bold else ()) + ("arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
        except OSError:
            continue
    return ImageFont.load_default()


class Frame:
    def __init__(self, idx, bg=(0, 0, 0)):
        self.idx = idx
        self.boil = idx // 2                      # neue Linien alle 2 Bilder = 6 "Zeichnungen" pro Sekunde
        self.img = Image.new("RGBA", (W, H), bg + (255,))
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def seed(self, k):
        return k * 131 + self.boil * 7

    def poly(self, pts, fill, outline=INK, w=7, amp=2.6, k=0):
        q = HD.wobble(pts, amp=amp, seed=self.seed(k), step=16, closed=True)
        if fill is not None:
            self.d.polygon(q, fill=fill)
        if outline is not None and w > 0:
            HD.ink(self.d, q, outline, w, seed=self.seed(k) + 3, var=0.25, closed=True)

    def line(self, pts, col=INK, w=7, amp=2.0, k=0):
        q = HD.wobble(pts, amp=amp, seed=self.seed(k), step=16)
        HD.ink(self.d, q, col, w, seed=self.seed(k) + 5, var=0.25)

    def ell(self, cx, cy, rx, ry, fill, outline=INK, w=7, k=0):
        n = max(16, int((rx + ry) * 0.25))
        pts = [(cx + rx * math.cos(t * math.tau / n), cy + ry * math.sin(t * math.tau / n)) for t in range(n)]
        self.poly(pts, fill, outline, w, amp=min(3.0, (rx + ry) * 0.02), k=k)

    def glow(self, cx, cy, r, col, a=120, blur=40):
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (a,))
        self.img.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def layer(self, fn, blur=0):
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(ImageDraw.Draw(g, "RGBA"))
        if blur:
            g = g.filter(ImageFilter.GaussianBlur(blur))
        self.img.alpha_composite(g)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def overlay(self, col, a):
        if a <= 0:
            return
        self.img.alpha_composite(Image.new("RGBA", (W, H), col + (int(a),)))
        self.d = ImageDraw.Draw(self.img, "RGBA")


def ease_out(u):
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def gradient(f, top, bot, y0=0, y1=H):
    for y in range(y0, y1, 4):
        t = (y - y0) / max(1, y1 - y0)
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        f.d.rectangle([0, y, W, y + 4], fill=c + (255,))


def crewmate(f, x, y, s, cols, flip=False, k=0, bob=0.0):
    """Crewmate im Stil der Kartengrafik: Kapsel, Rucksack, Beine, Visier. (x, y) = Fusspunkt, s = Hoehe px."""
    body, dark = cols
    y = y - bob
    sx = -1 if flip else 1
    X = lambda u: x + u * s * sx
    Y = lambda v: y - v * s
    for lx in (-0.2, 0.05):
        f.poly([(X(lx), Y(0.22)), (X(lx + 0.17), Y(0.22)), (X(lx + 0.17), Y(0.0)), (X(lx), Y(0.0))], body + (255,), k=k + 1, w=6)
    f.poly([(X(-0.42), Y(0.78)), (X(-0.22), Y(0.78)), (X(-0.22), Y(0.3)), (X(-0.42), Y(0.3))], dark + (255,), k=k + 2, w=6)
    pts = []
    for t in range(0, 181, 15):                                       # Kopfbogen
        a = math.radians(t)
        pts.append((X(0.02 + 0.28 * math.cos(a)), Y(0.8 + 0.25 * math.sin(a))))
    pts += [(X(-0.26), Y(0.2)), (X(-0.2), Y(0.14)), (X(0.24), Y(0.14)), (X(0.3), Y(0.2))]
    f.poly(pts, body + (255,), k=k + 3, w=7)
    f.poly([(X(0.02), Y(0.9)), (X(0.38), Y(0.9)), (X(0.38), Y(0.66)), (X(0.02), Y(0.66))], (150, 204, 226, 255), k=k + 4, w=6, amp=1.5)
    f.d.rectangle([min(X(0.1), X(0.26)), Y(0.86), max(X(0.1), X(0.26)), Y(0.8)], fill=(226, 242, 250, 255))


def villa(f, cx, base, sc, lit, k=0):
    """Villa-Silhouette auf dem Huegel (sc = Breite in px)."""
    s = sc
    P = lambda u, v: (cx + u * s, base - v * s)
    house = HOUSE_L if lit else HOUSE
    roof = (70, 64, 86) if lit else ROOF
    # Fluegel
    for sx in (-1, 1):
        f.poly([P(sx * 0.18, 0), P(sx * 0.46, 0), P(sx * 0.46, 0.2), P(sx * 0.18, 0.2)], house + (255,), k=k + 1 + sx)
        f.poly([P(sx * 0.15, 0.2), P(sx * 0.32, 0.34), P(sx * 0.49, 0.2)], roof + (255,), k=k + 3 + sx)
        f.line([P(sx * 0.4, 0.28), P(sx * 0.4, 0.36)], w=9, k=k + 5 + sx)                     # Schornstein
    # Mittelbau mit Turm
    f.poly([P(-0.19, 0), P(0.19, 0), P(0.19, 0.3), P(-0.19, 0.3)], house + (255,), k=k + 8)
    f.poly([P(-0.22, 0.3), P(0.0, 0.42), P(0.22, 0.3)], roof + (255,), k=k + 9)
    f.poly([P(-0.07, 0.3), P(0.07, 0.3), P(0.07, 0.56), P(-0.07, 0.56)], house + (255,), k=k + 10)
    f.poly([P(-0.1, 0.56), P(0.0, 0.76), P(0.1, 0.56)], roof + (255,), k=k + 11)
    f.line([P(0.0, 0.76), P(0.0, 0.84)], w=6, k=k + 12)
    # Fenster (eines bleibt dunkel), Tuer
    wins = [(-0.38, 0.09), (-0.27, 0.09), (0.27, 0.09), (0.38, 0.09), (-0.11, 0.18), (0.11, 0.18), (0.0, 0.44), (-0.11, 0.06)]
    for i, (u, v) in enumerate(wins):
        on = i != 4 and (lit or (f.idx + i) % 23 != 0)
        if on:
            f.glow(*P(u, v), 0.035 * s, WIN, 70, 18)
        f.poly([P(u - 0.022, v - 0.035), P(u + 0.022, v - 0.035), P(u + 0.022, v + 0.035), P(u - 0.022, v + 0.035)],
               (WIN if on else (40, 20, 30)) + (255,), k=k + 20 + i, w=5, amp=1.2)
    f.poly([P(-0.035, 0), P(0.035, 0), P(0.035, 0.09), P(-0.035, 0.09)], (52, 20, 30, 255), k=k + 30, w=5, amp=1.2)


def shot_exterior(f, t, flash):
    zoom = 1.0 + 0.1 * min(1.0, t / 1.8)
    gradient(f, NIGHT_T if not flash else (120, 130, 180), NIGHT_B if not flash else (150, 130, 170))
    rnd = random.Random(7)
    # Mond und Wolken
    f.glow(420, 230, 150, MOON, 70, 50)
    f.ell(420, 230, 92, 92, MOON + (255,), w=6, k=1)
    f.d.ellipse([380, 200, 410, 225], fill=(206, 200, 176, 255))
    for i in range(6):
        cx = (rnd.uniform(-200, W) + t * 60 * (1 + i % 3)) % (W + 400) - 200
        cy = rnd.uniform(120, 420)
        col = (44, 40, 70, 235) if not flash else (150, 150, 190, 235)
        f.ell(cx, cy, rnd.uniform(160, 260), rnd.uniform(40, 70), col, outline=(20, 16, 30, 255), w=5, k=40 + i)
    # Blitz
    if flash:
        pts = [(1320, 0), (1270, 160), (1330, 190), (1240, 380), (1300, 400), (1220, 560)]
        f.layer(lambda d: d.line(pts, fill=(220, 230, 255, 160), width=40), blur=18)
        f.line(pts, col=(245, 248, 255, 255), w=10, amp=6, k=60)
    # Huegel, Baum, Zaun, Grabsteine
    cx, base = W / 2, 830
    sc = 880 * zoom
    f.ell(W / 2, 1120 + 40 * (zoom - 1), 1300 * zoom, 360, (26, 34, 30, 255), w=8, k=70)
    villa(f, cx, base, sc, flash, k=100)
    tree = [(250, 900), (300, 640), (240, 520), (310, 600), (330, 480), (360, 610), (420, 560), (350, 680), (330, 900)]
    f.poly(tree, (18, 16, 22, 255), k=80)
    for i in range(14):
        x = 520 + i * 70
        f.line([(x, 960), (x, 900)], col=(30, 28, 36, 255), w=8, k=90 + i)
        f.d.polygon([(x - 8, 900), (x, 884), (x + 8, 900)], fill=(30, 28, 36, 255))
    f.line([(510, 925), (1500, 925)], col=(30, 28, 36, 255), w=7, k=110)
    for gx in (1560, 1660, 1760):
        f.poly([(gx - 30, 1000), (gx + 30, 1000), (gx + 30, 930), (gx, 905), (gx - 30, 930)], (96, 98, 108, 255), k=120 + gx)
    # Regen
    def rain(d):
        r = random.Random(f.idx)
        for _ in range(260):
            x, y = r.uniform(0, W + 200), r.uniform(-100, H)
            d.line([(x, y), (x - 30, y + 90)], fill=(170, 180, 220, 90), width=3)
    f.layer(rain)
    if flash:
        f.overlay((255, 255, 255), 120)


def clapper(f, t, darkbg):
    """Regieklappe: faehrt von unten hoch, die Klappe schlaegt bei 2,45 s zu."""
    if darkbg:
        f.overlay((0, 0, 0), 120)
    u = ease_out((t - 1.8) / 0.4)
    cx, cy = W / 2, 1300 - u * 720
    bw, bh = 820, 470
    shake = 0
    closed = t >= 2.45
    if 2.45 <= t < 2.65:
        shake = 14 * math.sin((t - 2.45) * 90)
    cx += shake
    # Tafel
    f.poly([(cx - bw / 2, cy - bh / 2), (cx + bw / 2, cy - bh / 2), (cx + bw / 2, cy + bh / 2), (cx - bw / 2, cy + bh / 2)],
           (24, 24, 30, 255), w=10, k=200)
    for i in range(1, 4):
        y = cy - bh / 2 + i * bh / 4 + 20
        f.line([(cx - bw / 2 + 30, y), (cx + bw / 2 - 30, y)], col=(220, 220, 214, 255), w=5, k=210 + i)
    f.line([(cx, cy - bh / 2 + bh / 4 + 20), (cx, cy + bh / 2 - 30)], col=(220, 220, 214, 255), w=5, k=215)
    big, mid = font(84), font(54)
    f.d.text((cx, cy - bh / 2 + 70), "HOLLOWMERE MANOR", font=big, fill=(240, 236, 226, 255), anchor="mm")
    f.d.text((cx - bw / 4, cy - bh / 2 + bh / 4 + 85), "SCENE 1", font=mid, fill=(240, 236, 226, 255), anchor="mm")
    f.d.text((cx + bw / 4, cy - bh / 2 + bh / 4 + 85), "TAKE 1", font=mid, fill=(240, 236, 226, 255), anchor="mm")
    f.d.text((cx - bw / 4, cy + bh / 2 - 75), "DIR. ?", font=font(44), fill=(200, 196, 186, 255), anchor="mm")
    f.d.text((cx + bw / 4, cy + bh / 2 - 75), "NIGHT", font=font(44), fill=(200, 196, 186, 255), anchor="mm")
    # Klappe (Stange) mit Streifen, Gelenk links oben
    ang = 0.0 if closed else math.radians(28 * min(1.0, max(0.0, (2.45 - t) / 0.25)) if t > 2.2 else 28)
    hx, hy = cx - bw / 2, cy - bh / 2
    L, T = bw, 70

    def R(u, v):
        return (hx + u * math.cos(ang) + v * math.sin(ang), hy - u * math.sin(ang) - v * math.cos(ang) + (0 if closed else 0))
    f.poly([R(0, 0), R(L, 0), R(L, T), R(0, T)], (236, 236, 232, 255), w=10, k=220)
    for i in range(7):
        u0 = 30 + i * 115
        f.poly([R(u0, 4), R(u0 + 60, 4), R(u0 + 95, T - 4), R(u0 + 35, T - 4)], (20, 20, 24, 255), outline=None, k=230 + i)
    if 2.45 <= t < 2.6:                                                     # Schlaglinien
        for a in range(-60, 61, 30):
            r0, r1 = 120, 220
            x0, y0 = hx + 400 + r0 * math.sin(math.radians(a)), hy - r0 * math.cos(math.radians(a)) * 0.6
            x1, y1 = hx + 400 + r1 * math.sin(math.radians(a)), hy - r1 * math.cos(math.radians(a)) * 0.6
            f.line([(x0, y0), (x1, y1)], col=(255, 255, 255, 255), w=8, k=240 + a)


def shot_hall(f, t):
    gradient(f, WALL, WALL_D, 0, 640)
    rnd = random.Random(3)
    for row in range(5):                                                    # Damast
        for col in range(12):
            x, y = 80 + col * 160 + (80 if row % 2 else 0), 70 + row * 110
            f.d.ellipse([x - 22, y - 34, x + 22, y + 34], outline=(124, 50, 64, 255), width=5)
            f.d.ellipse([x - 8, y - 16, x + 8, y + 16], fill=(124, 50, 64, 255))
    f.poly([(0, 600), (W, 600), (W, 660), (0, 660)], WOOD + (255,), k=300)                 # Vertaefelung
    gradient(f, (120, 80, 50), (70, 46, 30), 660, H)                                         # Parkett
    for i in range(-10, 30):
        x = i * 110
        f.d.line([(x, 660), (x - 300, H)], fill=(60, 40, 26, 120), width=4)
    # Treppe und Portrait im Hintergrund
    f.poly([(1250, 640), (1650, 640), (1650, 300), (1580, 300), (1580, 360), (1500, 360), (1500, 420), (1420, 420),
            (1420, 480), (1340, 480), (1340, 540), (1250, 540)], (62, 40, 30, 255), k=310)
    f.poly([(560, 150), (800, 150), (800, 450), (560, 450)], BRASS + (255,), k=320)
    f.poly([(590, 180), (770, 180), (770, 420), (590, 420)], (30, 26, 34, 255), k=321, w=5)
    f.poly([(640, 420), (720, 420), (740, 300), (680, 240), (620, 300)], (14, 12, 18, 255), outline=None, k=322)
    # Scheinwerfer geht an (3,5 s)
    on = t >= 3.5
    lx, ly = 1300, 560
    if on:
        a = min(1.0, (t - 3.5) / 0.15)

        def beam(d):
            d.polygon([(lx - 30, ly - 40), (lx - 30, ly + 30), (200, 1000), (40, 420)], fill=(255, 226, 160, int(90 * a)))
        f.layer(beam, blur=30)
        f.glow(lx - 30, ly - 5, 90, (255, 230, 170), int(160 * a), 30)
    f.line([(lx + 40, ly + 20), (lx - 30, 900)], w=8, k=330)
    f.line([(lx + 40, ly + 20), (lx + 110, 900)], w=8, k=331)
    f.line([(lx + 40, ly + 20), (lx + 40, 900)], w=8, k=332)
    f.poly([(lx - 50, ly - 50), (lx + 60, ly - 40), (lx + 60, ly + 40), (lx - 50, ly + 40)], (40, 40, 46, 255), k=333)
    f.ell(lx - 50, ly - 5, 22, 48, ((255, 236, 190) if on else (90, 90, 100)) + (255,), w=6, k=334)
    # Crew: Rot am Scheinwerfer, Cyan mit Tonangel, Gelb mit Kamera
    bob = lambda ph: 6 * abs(math.sin((t + ph) * 6))
    crewmate(f, 1480, 960, 330, CREW[0], flip=True, k=400, bob=bob(0.0))
    crewmate(f, 820, 990, 350, CREW[1], k=420, bob=bob(0.3))
    f.line([(900, 780), (1060, 470)], col=(60, 60, 66, 255), w=10, k=440)                    # Tonangel
    f.ell(1080, 440, 46, 26, (90, 86, 80, 255), w=6, k=441)
    crewmate(f, 400, 1000, 360, CREW[2], k=460, bob=bob(0.6))
    f.poly([(470, 760), (610, 760), (610, 840), (470, 840)], (36, 36, 42, 255), k=480)        # Kamera auf Schulter
    f.ell(640, 800, 30, 30, (24, 24, 30, 255), w=6, k=481)
    f.d.ellipse([500, 770, 516, 786], fill=(220, 40, 40, 255))
    f.overlay((10, 10, 30), 40)


def shot_candles(f, t):
    gradient(f, (24, 18, 30), (10, 8, 16))
    outs = [5.1, 5.22, 5.34]
    lit = [t < o for o in outs]
    glow_a = sum(lit) / 3
    if glow_a > 0:
        f.glow(W / 2, 420, 520, (255, 190, 100), int(110 * glow_a), 80)
    # Kandelaber
    cx = W / 2
    f.poly([(cx - 26, 1080), (cx + 26, 1080), (cx + 20, 640), (cx - 20, 640)], BRASS + (255,), k=500)
    f.ell(cx, 1060, 170, 40, BRASS + (255,), k=501)
    f.line([(cx - 330, 520), (cx - 330, 600), (cx, 660), (cx + 330, 600), (cx + 330, 520)], col=BRASS + (255,), w=26, k=502)
    f.line([(cx - 330, 520), (cx - 330, 600), (cx, 660), (cx + 330, 600), (cx + 330, 520)], w=8, k=503)
    gust = max(0.0, min(1.0, (t - 4.95) / 0.15))
    for i, x in enumerate((cx - 330, cx, cx + 330)):
        top = 300 if i == 1 else 340
        f.poly([(x - 34, 520 if i != 1 else 480), (x + 34, 520 if i != 1 else 480), (x + 34, top), (x - 34, top)], (232, 224, 204, 255), k=510 + i)
        f.d.polygon([(x - 34, top), (x + 34, top), (x + 30, top + 30), (x - 30, top + 40)], fill=(244, 238, 220, 255))
        if lit[i]:
            lean = -40 * gust + 10 * math.sin(t * 20 + i)
            fl = [(x - 18, top - 4), (x + 18, top - 4), (x + 6 + lean * 0.5, top - 60), (x + lean, top - 110), (x - 6 + lean * 0.5, top - 60)]
            f.glow(x + lean * 0.4, top - 50, 60, (255, 200, 110), 150, 25)
            f.poly(fl, (255, 196, 80, 255), outline=(150, 70, 20, 255), w=5, k=520 + i)
            f.poly([(x - 8, top - 6), (x + 8, top - 6), (x + lean * 0.6, top - 70)], (255, 246, 210, 255), outline=None, k=530 + i)
        else:
            age = t - outs[i]
            for j in range(3):                                               # Rauchfaden
                pts = [(x + 12 * math.sin(age * 4 + j + s * 0.02) + j * 6, top - 10 - s) for s in range(0, int(80 + age * 260), 20)]
                if len(pts) > 1:
                    f.line(pts, col=(180, 180, 196, max(0, int(170 - age * 200))), w=5, amp=4, k=540 + i * 3 + j)
    f.overlay((0, 0, 20), int(160 * (1 - glow_a)))


def shot_portrait(f, t):
    f.img.paste((6, 6, 12, 255), [0, 0, W, H])
    f.d = ImageDraw.Draw(f.img, "RGBA")
    f.glow(W / 2 + 300, 200, 500, (90, 110, 170), 50, 120)                  # Mondlicht von rechts oben
    x0, y0, x1, y1 = W / 2 - 300, 140, W / 2 + 300, 940
    f.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], (130, 104, 56, 255), k=600, w=10)
    f.poly([(x0 + 50, y0 + 50), (x1 - 50, y0 + 50), (x1 - 50, y1 - 50), (x0 + 50, y1 - 50)], (28, 26, 38, 255), k=601, w=8)
    for cx_, cy_ in ((x0 + 25, y0 + 25), (x1 - 25, y0 + 25), (x0 + 25, y1 - 25), (x1 - 25, y1 - 25)):
        f.ell(cx_, cy_, 22, 22, (170, 140, 76, 255), w=5, k=602 + int(cx_))
    # gemalter Hausherr: Kapuzen-Silhouette ohne Gesicht
    cx = W / 2
    f.poly([(cx - 220, y1 - 50), (cx - 180, 620), (cx - 120, 520), (cx - 110, 360), (cx, 300), (cx + 110, 360), (cx + 120, 520),
            (cx + 180, 620), (cx + 220, y1 - 50)], (16, 14, 22, 255), outline=(40, 36, 52, 255), w=6, k=610)
    f.ell(cx, 450, 92, 112, (10, 9, 14, 255), outline=None, k=611)
    # Augen gehen auf (6,1 s), werden schmal (6,5 s)
    if t >= 6.1:
        open_ = min(1.0, (t - 6.1) / 0.12)
        if t >= 6.5:
            open_ = max(0.25, 1.0 - (t - 6.5) / 0.1 * 0.75)
        for ex in (cx - 44, cx + 44):
            f.glow(ex, 440, 70, (255, 214, 90), int(170 * open_), 25)
            f.d.ellipse([ex - 30, 440 - 13 * open_, ex + 30, 440 + 13 * open_], fill=(255, 226, 120, 255))
            f.d.ellipse([ex - 7, 440 - 10 * open_, ex + 7, 440 + 10 * open_], fill=(40, 10, 10, 255))
    if t >= 6.66:
        f.overlay((0, 0, 0), min(255, (t - 6.66) / 0.12 * 255))


def finish(f, rnd):
    """Filmkorn und Vignette, dann auf 960 x 540."""
    img = f.img.convert("RGB")
    vig = Image.new("L", (W // 8, H // 8), 0)
    ImageDraw.Draw(vig).ellipse([-W // 40, -H // 40, W // 8 + W // 40, H // 8 + H // 40], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(22)).resize((W, H), Image.BICUBIC)
    img = Image.composite(img, Image.new("RGB", (W, H), (0, 0, 0)), vig.point(lambda v: int(90 + v * 0.65)))
    img = img.resize((W // 2, H // 2), Image.LANCZOS)
    img = HD.paper_grain(img, 0.05, seed=f.idx)
    return img


def render_frame(i):
    t = i / FPS
    f = Frame(i)
    rnd = random.Random(i)
    if t < 1.8:
        flash = 0.55 <= t < 0.72
        shot_exterior(f, t, flash)
    elif t < 3.0:
        shot_exterior(f, 1.8, False)
        clapper(f, t, darkbg=True)
    elif t < 4.6:
        shot_hall(f, t)
    elif t < 5.8:
        shot_candles(f, t)
    else:
        shot_portrait(f, t)
    return finish(f, rnd)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PREV.mkdir(exist_ok=True)
    for old in OUT.glob("villa_intro_*.jpg"):
        old.unlink()
    n = int(LENGTH * FPS)
    frames = []
    total = 0
    for i in range(n):
        img = render_frame(i)
        p = OUT / f"villa_intro_{i:03d}.jpg"
        img.save(p, quality=80, optimize=True)
        total += p.stat().st_size
        frames.append(img)
    frames[0].save(PREV / "intro_preview.webp", save_all=True, append_images=frames[1:], duration=int(1000 / FPS), loop=0, quality=80)
    picks = frames[::6]
    cols = 4
    sheet = Image.new("RGB", (cols * 480, ((len(picks) + cols - 1) // cols) * 270), (0, 0, 0))
    dd = ImageDraw.Draw(sheet)
    for k, im in enumerate(picks):
        x, y = (k % cols) * 480, (k // cols) * 270
        sheet.paste(im.resize((480, 270)), (x, y))
        dd.text((x + 8, y + 6), f"{k * 6 / FPS:.1f} s", fill=(255, 200, 80))
    sheet.save(PREV / "intro_storyboard.png")
    print(f"intro: {n} frames, {total / 1e6:.2f} MB, preview + storyboard in {PREV}")


if __name__ == "__main__":
    main()
