# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_tasks.py - Minispiele von Ravenhollow Cemetery: Zuordnung der Atlas-Bausteine (customTasks), Grafik
# (taskArt, Dateien task_gy_*.png in Resources/graveyard) und Texte (taskText) fuer map.json.
#
# Wie gen_villa_tasks.py: jede Datei hat exakt die Groesse der Atlas-Datei, die sie ersetzt (Drehpunkte, Fenster,
# Raster der Bausteine bleiben gueltig). Stil wie Atlas gen_tasks.py (flache Toene, Glanz, dunkle Kontur), Palette
# des Friedhofs: Granit, Schiefer, Eisen, Moos, Mondlicht, warmes Laternenlicht.
#
# SCHNITTSTELLE (gen_graveyard.main): map_extra(out_dir) -> {"customTasks", "taskArt", "taskText"}; zeichnet dabei
# alle Bilder neu.

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ATLAS = HERE.parent.parent / "UnknownsAtlas"
sys.path.insert(0, str(ATLAS / "tools"))
import gen_tasks as GT                                          # noqa: E402
from gen_tasks import C, INK, S, label, mix, dark, light       # noqa: E402

STONE, STONE_L, STONE_D = (96, 100, 112, 255), (132, 138, 152, 255), (62, 64, 74, 255)
SLATE = (54, 58, 68, 255)
IRON, IRON_L, IRON_D = (58, 60, 70, 255), (104, 108, 120, 255), (34, 36, 42, 255)
OAK, OAK_L, OAK_D = (96, 78, 60, 255), (128, 106, 82, 255), (62, 50, 40, 255)
MOSS, MOSS_L = (78, 112, 70, 255), (108, 146, 92, 255)
GRASS, GRASS_D = (56, 86, 68, 255), (36, 58, 48, 255)
BONE = (214, 206, 186, 255)
PARCH = (210, 198, 164, 255)
CREAM = (226, 218, 194, 255)
NIGHT, NIGHT_L = (18, 26, 34, 255), (36, 52, 62, 255)
MOON = (232, 238, 226, 255)
BRONZE, BRONZE_L = (154, 114, 64, 255), (208, 168, 104, 255)
LAMP = (255, 214, 140, 255)
RUNE = (122, 224, 208, 255)
MIASMA = (150, 208, 112, 255)
RED = (190, 52, 58, 255)
GREEN = (90, 176, 104, 255)


def size_of(name):
    return Image.open(ATLAS / "assets" / name).size


def like(name):
    w, h = size_of(name)
    return C(w, h)


def cobweb(c, x, y, size, qx, qy):
    col = (236, 236, 242, 95)
    for k in range(6):
        a = math.pi / 2 * k / 5
        c.line([(x, y), (x + qx * size * math.cos(a), y + qy * size * math.sin(a))], col, 2)
    for r in (0.35, 0.65, 0.95):
        pts = [(x + qx * r * size * math.cos(math.pi / 2 * k / 5), y + qy * r * size * math.sin(math.pi / 2 * k / 5)) for k in range(6)]
        c.line(pts, col, 2)


def stone_wall(c, x0, y0, x1, y1, seed=1, bw=56, bh=34, cols=None):
    rnd = random.Random(seed)
    cols = cols or [(74, 78, 90, 255), (66, 70, 82, 255), (82, 86, 98, 255)]
    c.d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=(40, 42, 50, 255))
    for row, y in enumerate(range(y0, y1, bh + 4)):
        off = (bw // 2) if row % 2 else 0
        for x in range(x0 - off, x1, bw + 4):
            a, b = max(x0, x), min(x1, x + bw)
            if b - a < 10:
                continue
            c.rrect(a, y, b, min(y1, y + bh), 4, rnd.choice(cols), lw=3, outline=(30, 32, 38, 255))
    m, md = c.mask()
    md.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=255)
    c.mottle(0.07, 14, seed=seed, mask=m)


def frame_stone(c):
    """Rahmen aus gemeisseltem Granit mit Eckrosetten (statt frame_wood)."""
    w, h = c.w, c.h
    c.rrect(2, 2, w - 2, h - 2, 18, STONE_D, lw=8, sh=(0.12, 0.2))
    c.rrect(14, 14, w - 14, h - 14, 12, STONE, lw=5, sh=(0.18, 0.25))
    for x, y in ((24, 24), (w - 24, 24), (24, h - 24), (w - 24, h - 24)):
        c.ell(x, y, 10, 10, STONE_L, lw=3)
        c.ell(x, y, 4, 4, STONE_D, lw=0)


def moss_blobs(c, pts, seed=1):
    rnd = random.Random(seed)
    for x, y, r in pts:
        for _ in range(5):
            c.ell(x + rnd.uniform(-r, r), y + rnd.uniform(-r * 0.5, r * 0.5), r * rnd.uniform(0.3, 0.6), r * rnd.uniform(0.2, 0.4),
                  MOSS if rnd.random() < 0.6 else MOSS_L, lw=0)


# ------------------------------------------------------------------ Tafeln

def gy_panel():
    c = like("task_museum_panel.png")
    frame_stone(c)
    stone_wall(c, 30, 30, 690, 490, seed=3)
    c.vignette(0.5, 30, 30, 690, 490)
    c.glow(60, 60, 70, 60, (255, 214, 140, 60), 16)
    moss_blobs(c, [(70, 470, 30), (650, 460, 24), (40, 300, 18)], seed=4)
    cobweb(c, 690, 30, 80, -1, 1)
    c.save("task_gy_panel.png")


def gy_iron_panel():
    c = like("task_steel_panel.png")
    c.rrect(4, 4, 716, 516, 22, IRON_D, lw=8, sh=(0.12, 0.2))
    c.rrect(26, 26, 694, 494, 12, IRON, lw=4, sh=(0.18, 0.25))
    for x in range(44, 680, 26):
        c.d.rectangle([x * S, 40 * S, (x + 8) * S, 480 * S], fill=IRON_L)
    m, md = c.mask()
    md.rectangle([36 * S, 36 * S, 684 * S, 484 * S], fill=255)
    c.brushed(0.05, seed=4, mask=m)
    c.vignette(0.45, 26, 26, 694, 494)
    for x in (48, 672):
        for y in (48, 472):
            c.rivet(x, y, 7, IRON_L)
    for k in range(12):                                                              # Rostfahnen unter den Nieten
        x = 60 + k * 54
        c.soft_poly([(x, 480), (x + 10, 480), (x + 6, 440)], (150, 82, 40, 70), 4)
    label(c, 360, 18, "RAVENHOLLOW", 13, (180, 186, 196, 255))
    c.save("task_gy_iron.png")


# ------------------------------------------------------------------ Sweep the Crypt (dust)

def gy_crypt():
    c = like("task_museum_dino.png")
    c.rrect(6, 6, 554, 294, 10, (64, 66, 74, 255), lw=6, sh=(0.1, 0.2))
    for row, y in enumerate(range(14, 290, 40)):                                     # Grabplatten-Boden
        for x in range(14 + (36 if row % 2 else 0), 546, 72):
            c.rrect(x, y, min(x + 68, 548), y + 36, 4, (96, 98, 108, 255) if (x + row) % 3 else (84, 86, 96, 255), lw=3, outline=(44, 46, 52, 255))
    c.rrect(170, 70, 390, 230, 8, (150, 150, 146, 255), lw=6, sh=(0.15, 0.25))     # Grabplatte mit Inschrift
    c.rrect(184, 84, 376, 216, 4, (0, 0, 0, 0), lw=3, outline=(110, 110, 106, 255))
    c.line([(280, 100), (280, 150)], (90, 90, 88, 255), 8)
    c.line([(258, 118), (302, 118)], (90, 90, 88, 255), 8)
    for k in range(3):
        c.line([(210 + k * 10, 172 + k * 14), (350 - k * 10, 172 + k * 14)], (100, 100, 98, 255), 4)
    for x, y in ((80, 240), (470, 60), (500, 250)):                                 # Knochen
        c.capsule((x - 26, y), (x + 26, y + 6), 10, BONE, lw=3)
        c.ell(x - 28, y - 4, 7, 7, BONE, lw=3); c.ell(x - 28, y + 6, 7, 7, BONE, lw=3)
        c.ell(x + 28, y + 2, 7, 7, BONE, lw=3); c.ell(x + 28, y + 12, 7, 7, BONE, lw=3)
    cobweb(c, 554, 6, 70, -1, 1)
    c.save("task_gy_crypt.png")


def gy_dust():
    w, h = size_of("task_museum_dust.png")
    rnd = np.random.default_rng(13)
    small = rnd.random((10, 18)).astype(np.float32)
    cloud = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255
    fine = rnd.random((h, w)).astype(np.float32)
    fine = np.asarray(Image.fromarray((fine * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.4)), dtype=np.float32) / 255
    v = 128 + (cloud - 0.5) * 30 + (fine - 0.5) * 22
    rgb = np.stack([v + 6, v + 4, v], axis=-1)
    a = np.full((h, w), 232, dtype=np.float32) - (cloud - 0.5) * 30
    ys = np.arange(h)[:, None]
    xs = np.arange(w)[None, :]
    edge = np.minimum(np.minimum(xs, w - 1 - xs), np.minimum(ys, h - 1 - ys)).astype(np.float32)
    a *= np.clip(edge / 3.0 + (fine - 0.5) * 0.8, 0, 1)
    img = Image.fromarray(np.clip(np.concatenate([rgb, a[..., None]], axis=-1), 0, 255).astype(np.uint8), "RGBA")
    fl = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    for _ in range(50):                                                             # Knochensplitter
        x, y = rnd.integers(0, w * 2), rnd.integers(0, h * 2)
        r = int(rnd.integers(2, 6))
        fd.ellipse([x - r, y - r, x + r * 2, y + r], fill=(222, 214, 196, 150))
    fl = fl.filter(ImageFilter.GaussianBlur(1.5)).resize((w, h), Image.LANCZOS)
    img.alpha_composite(fl)
    img.save(GT.OUT / "task_gy_dust.png")


def gy_broom():
    c = like("task_brush.png")
    c.line([(60, 66), (60, 8)], OAK_L, 9)
    c.poly([(30, 70), (90, 70), (100, 112), (20, 112)], (196, 160, 96, 255), lw=4)
    for k in range(9):
        c.line([(28 + k * 8, 76), (24 + k * 9, 110)], (150, 116, 60, 255), 3)
    c.line([(32, 78), (88, 78)], IRON, 5)
    c.save("task_gy_broom.png")


# ------------------------------------------------------------------ Shoo the Ravens (moths)

def gy_night():
    c = like("task_gallery.png")
    frame_stone(c)
    c.d.rectangle([28 * S, 28 * S, 692 * S, 492 * S], fill=NIGHT)
    rnd = random.Random(7)
    for _ in range(90):
        sx, sy = (30 + rnd.random() * 660) * S, (30 + rnd.random() * 260) * S
        c.d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(220, 226, 236, rnd.randint(120, 230)))
    c.glow(560, 120, 80, 80, (232, 238, 226, 110), 18)
    c.ell(560, 120, 48, 48, MOON, lw=0)
    for mx, my, mr in ((545, 108, 9), (575, 134, 12), (560, 100, 5)):
        c.ell(mx, my, mr, mr, (208, 214, 200, 255), lw=0)
    c.poly([(28, 380), (140, 340), (260, 360), (380, 330), (520, 356), (692, 340), (692, 492), (28, 492)], GRASS_D, lw=4)   # Huegel
    for k, x in enumerate((80, 170, 250, 330, 450, 540, 630)):                      # Grabsteine im Gegenlicht
        h = 50 + (k * 13) % 30
        y = 400 + (k * 7) % 20
        c.poly([(x - 18, y), (x + 18, y), (x + 18, y - h + 18)] + [(x + 18 * math.cos(t), y - h + 18 - 18 * math.sin(t)) for t in [j * math.pi / 8 for j in range(9)]] + [(x - 18, y - h + 18)],
               (40, 44, 54, 255), lw=4)
    c.line([(110, 470), (120, 250), (100, 180)], (30, 26, 26, 255), 14)              # kahler Baum
    for a, ln in ((2.2, 70), (1.1, 90), (1.7, 60), (0.6, 50)):
        c.line([(118, 280), (118 + ln * math.cos(a), 280 - ln * math.sin(a))], (30, 26, 26, 255), 7)
    c.vignette(0.45, 28, 28, 692, 492)
    c.save("task_gy_night.png")


def gy_raven():
    c = like("task_moth.png")
    body = (20, 20, 26, 255)
    c.poly([(70, 34), (40, 22), (10, 26), (24, 38), (6, 48), (34, 46), (52, 52), (70, 44), (84, 40)], body, lw=3)   # Fluegel
    c.ell(52, 40, 16, 10, (28, 28, 36, 255), lw=3)
    c.ell(70, 34, 9, 8, (28, 28, 36, 255), lw=3)
    c.poly([(77, 33), (88, 35), (77, 37)], (90, 90, 96, 255), lw=2)
    c.d.ellipse([70 * S, 31 * S, 73 * S, 34 * S], fill=(232, 200, 90, 255))
    c.line([(40, 34), (60, 30)], (90, 104, 150, 180), 2)
    c.save("task_gy_raven.png")


def gy_lantern_tool():
    c = like("task_torch.png")
    c.line([(70, 240), (150, 100)], OAK_D, 14)
    c.line([(70, 240), (150, 100)], OAK_L, 8)
    c.line([(150, 100), (178, 80)], IRON, 6)
    c.glow(186, 110, 60, 60, (255, 214, 140, 140), 16)
    c.rrect(160, 76, 212, 140, 6, (255, 214, 140, 255), lw=5)
    c.ell(186, 108, 8, 14, (255, 244, 210, 255), lw=0)
    c.poly([(154, 76), (218, 76), (186, 52)], IRON, lw=4)
    c.line([(160, 140), (212, 140)], IRON, 8)
    c.save("task_gy_lantern.png")


def gy_nest():
    c = like("task_jar.png")
    c.rrect(6, 6, 124, 154, 6, STONE, lw=5, sh=(0.12, 0.2))
    c.d.rectangle([18 * S, 18 * S, 112 * S, 142 * S], fill=NIGHT)
    c.ell(84, 44, 14, 14, MOON, lw=0)
    c.poly([(18, 142), (40, 110), (65, 124), (90, 100), (112, 120), (112, 142)], GRASS_D, lw=3)
    c.glow(65, 80, 40, 50, (200, 220, 255, 50), 10)
    c.save("task_gy_open.png")


# ------------------------------------------------------------------ Relight the Ward Candles (lanterns)

def gy_wards():
    c = like("task_dock_night.png")
    frame_stone(c)
    c.d.rectangle([28 * S, 28 * S, 692 * S, 492 * S], fill=NIGHT)
    c.glow(360, 120, 260, 90, (60, 90, 100, 120), 30)
    c.poly([(28, 330), (692, 330), (692, 492), (28, 492)], GRASS, lw=0)
    c.ell(360, 420, 280, 60, (0, 0, 0, 0), lw=4, outline=(214, 230, 220, 180))      # Runenkreis
    for k, (x, h) in enumerate(((110, 190), (230, 230), (490, 230), (610, 190))):    # Menhire
        y = 360
        pts = [(x - 40, y), (x + 40, y), (x + 34, y - h * 0.6), (x + 14, y - h), (x - 20, y - h + 10), (x - 38, y - h * 0.5)]
        c.poly(pts, (88, 92, 104, 255), lw=6, sh=(0.1, 0.2))
        for j in range(3):
            gy = y - 40 - j * 50
            c.line([(x - 8, gy), (x + 6, gy - 22), (x + 10, gy - 8)], RUNE, 4)
        c.glow(x, y - h * 0.5, 30, 60, (122, 224, 208, 40), 12)
    c.vignette(0.5, 28, 28, 692, 492)
    c.save("task_gy_wards.png")


def gy_candles():
    for name, lit in (("task_gy_candle_off.png", False), ("task_gy_candle_on.png", True)):
        c = C(*size_of("task_lantern_on.png"))
        if lit:
            c.glow(60, 40, 50, 60, (255, 214, 140, 140), 14)
        c.ell(60, 152, 34, 12, STONE, lw=4, sh=(0.15, 0.25))                         # Steinteller
        c.rrect(44, 62, 76, 150, 5, CREAM, lw=4, sh=(0.1, 0.2))
        c.line([(50, 72), (50, 140)], (240, 234, 216, 255), 3)
        c.ell(60, 62, 16, 6, (240, 234, 216, 255), lw=3)
        c.line([(70, 66), (70, 110)], (240, 234, 216, 255), 5)
        c.line([(52, 100), (68, 96)], RUNE, 3)                                      # eingeritzte Rune
        if lit:
            c.poly([(60, 58), (68, 44), (60, 18), (52, 44)], (255, 180, 60, 255), lw=3, outline=(160, 90, 20, 255))
            c.poly([(60, 54), (64, 44), (60, 30), (56, 44)], (255, 244, 200, 255), lw=0)
        else:
            c.line([(60, 58), (60, 50)], INK, 3)
            c.line([(60, 48), (64, 36), (58, 24)], (170, 170, 180, 140), 3)
        c.save(name)


# ------------------------------------------------------------------ Trim the Lantern Wicks (climate), Well Crank, Furnace

def gy_gauge():
    c = like("task_gauge_band.png")
    GT.dial_face(c, 140, 140, green_pil=(270 - 30, 270 + 30))
    c.ell(140, 140, 122, 122, (0, 0, 0, 0), lw=10, outline=IRON_L)
    label(c, 140, 200, "WICK", 16, IRON_D)
    c.save("task_gy_gauge.png")
    c = like("task_needle.png")
    c.poly([(2, 10), (110, 4), (118, 10), (110, 16)], (40, 40, 46, 255), lw=3)
    c.ell(12, 10, 7, 7, BRONZE, lw=3)
    c.save("task_gy_needle.png")


def gy_winch():
    c = like("task_generator.png")
    for x in (60, 240):                                                             # Holzbock
        c.poly([(x - 30, 236), (x + 30, 236), (x + 8, 70), (x - 8, 70)], OAK, lw=5, sh=(0.1, 0.2))
    c.capsule((40, 110), (260, 110), 26, OAK_D, lw=5)
    for k in range(8):
        c.line([(70 + k * 20, 98), (78 + k * 20, 122)], (176, 148, 106, 255), 6)
    c.ell(150, 110, 70, 70, (0, 0, 0, 0), lw=12, outline=INK)                         # Speichenrad
    c.ell(150, 110, 70, 70, (0, 0, 0, 0), lw=7, outline=IRON_L)
    for k in range(6):
        a = k * math.pi / 3
        c.line([(150, 110), (150 + 66 * math.cos(a), 110 + 66 * math.sin(a))], INK, 10)
        c.line([(150, 110), (150 + 66 * math.cos(a), 110 + 66 * math.sin(a))], IRON_L, 5)
    c.ell(150, 110, 14, 14, IRON, lw=4)
    c.line([(260, 110), (284, 110), (284, 150)], INK, 12)
    c.line([(260, 110), (284, 110), (284, 150)], IRON_L, 6)
    c.rrect(276, 148, 292, 176, 4, OAK_L, lw=3)
    c.line([(150, 140), (150, 236)], (176, 148, 106, 255), 5)                        # Seil zum Brunnen
    c.save("task_gy_winch.png")


def gy_furnace():
    c = like("task_boiler.png")
    c.ell(180, 380, 130, 22, (0, 0, 0, 70), lw=0)
    c.rrect(50, 60, 310, 370, 16, (128, 70, 56, 255), lw=6, sh=(0.1, 0.25), shx=(0.12, 0.16))
    for row, y in enumerate(range(70, 360, 24)):                                    # Ziegel
        for x in range(56 + (22 if row % 2 else 0), 304, 44):
            c.d.rectangle([x * S, y * S, min(x + 40, 304) * S, (y + 20) * S], fill=(140, 78, 62, 255) if (x + row) % 3 else (118, 64, 52, 255))
    c.rrect(110, 200, 250, 330, 50, IRON, lw=6, sh=(0.15, 0.25))                    # Feuertuer
    for k in range(4):
        c.rrect(130, 230 + k * 22, 230, 240 + k * 22, 3, (255, 140, 60, 255), lw=2)
    c.glow(180, 270, 80, 60, (255, 140, 60, 90), 16)
    c.rrect(150, 10, 210, 64, 4, IRON_D, lw=5)                                     # Rohr
    label(c, 180, 150, "FURNACE", 28, (236, 220, 200, 255))
    c.save("task_gy_furnace.png")


def gy_oilcan():
    c = like("task_can.png")
    # Kontrakt: Fenster x 50..130, y 70..210 bleibt transparent (Fuellstand dahinter)
    c.rrect(20, 40, 160, 230, 12, (120, 40, 40, 255), lw=6, sh=(0.1, 0.22), shx=(0.1, 0.14))
    c.d.rectangle([50 * S, 70 * S, 130 * S, 210 * S], fill=(0, 0, 0, 0))
    c.d.rectangle([48 * S, 68 * S, 132 * S, 212 * S], outline=INK, width=4 * S)
    c.rrect(60, 14, 120, 44, 6, (120, 40, 40, 255), lw=5)
    c.line([(120, 30), (152, 12)], IRON, 8)
    c.line([(64, 48), (116, 48)], (170, 80, 76, 255), 5)
    c.d.rectangle([56 * S, 214 * S, 124 * S, 224 * S], fill=CREAM)
    label(c, 90, 219, "LAMP OIL", 8, INK)
    c.save("task_gy_oilcan.png")


# ------------------------------------------------------------------ Map the Graves, Straighten a Headstone (sky)

def gy_gravecard():
    c = like("task_card.png")
    c.rrect(6, 6, 214, 174, 8, STONE, lw=5, sh=(0.2, 0.3))
    c.rrect(16, 16, 204, 164, 5, PARCH, lw=3)
    m, md = c.mask()
    md.rectangle([16 * S, 16 * S, 204 * S, 164 * S], fill=255)
    c.mottle(0.07, 10, seed=3, mask=m)
    label(c, 110, 30, "RAVENHOLLOW SKY", 11, (50, 60, 70, 255))
    pts = [(40, 70), (64, 96), (104, 124), (140, 84), (172, 112), (190, 56)]
    for x, y in pts:
        c.d.ellipse([(x - 3) * S, (y - 3) * S, (x + 3) * S, (y + 3) * S], fill=(50, 60, 70, 255))
    c.line(pts, (50, 60, 70, 200), 2)
    label(c, 110, 152, "ALL HALLOWS", 11, (150, 40, 40, 255))
    c.save("task_gy_card.png")


def gy_sky(name, moon=False):
    c = like("task_sky.png")
    c.ell(220, 220, 218, 218, NIGHT, lw=0)
    rnd = random.Random(23 if moon else 11)
    for _ in range(140):
        a, r = rnd.random() * math.tau, rnd.random() ** 0.5 * 210
        x, y = 220 + r * math.cos(a), 220 + r * math.sin(a)
        s = rnd.choice((1.5, 2, 2.5, 3))
        c.d.ellipse([(x - s) * S, (y - s) * S, (x + s) * S, (y + s) * S], fill=(220, 226, 236, rnd.randint(140, 255)))
    c.glow(220, 220, 190, 190, (50, 80, 90, 90), 30)
    if moon:
        c.glow(220, 210, 110, 110, (232, 238, 226, 90), 20)
        c.ell(220, 210, 80, 80, MOON, lw=0)
        for (mx, my, mr) in ((195, 190, 14), (240, 230, 20), (210, 240, 9), (250, 185, 7)):
            c.ell(mx, my, mr, mr, (206, 212, 200, 255), lw=0)
        for k, (rx, ry) in enumerate(((140, 300), (300, 150))):                     # Raben vor dem Mond
            c.poly([(rx, ry), (rx - 26, ry - 10), (rx - 40, ry - 2), (rx - 20, ry + 4), (rx, ry + 8), (rx + 20, ry + 4), (rx + 40, ry - 2), (rx + 26, ry - 10)],
                   (20, 22, 28, 255), lw=2)
    else:
        c.ell(360, 90, 26, 26, MOON, lw=0)
        c.ell(372, 84, 24, 24, NIGHT, lw=0)
    for (cx, cy, rx) in ((120, 340, 70), (330, 360, 60)):
        c.glow(cx, cy, rx, rx * 0.4, (100, 110, 120, 110), 16)
    c.save(name)


# ------------------------------------------------------------------ Identify the Ashes (pigment)

def gy_ashes():
    c = like("task_vial.png")
    c.rrect(14, 50, 56, 190, 14, (210, 222, 232, 110), lw=4, outline=INK, sh=(0.0, 0.0))
    c.d.rectangle([18 * S, 100 * S, 52 * S, 186 * S], fill=(120, 116, 110, 255))
    c.ell(35, 100, 17, 5, (150, 146, 138, 255), lw=0)
    c.rrect(22, 22, 48, 56, 5, BRONZE, lw=4)
    c.line([(20, 60), (20, 180)], (255, 255, 255, 110), 3)
    c.d.rectangle([16 * S, 130 * S, 54 * S, 156 * S], fill=CREAM)
    label(c, 35, 143, "ASH", 8, INK)
    c.save("task_gy_vial.png")
    c = like("task_strip.png")
    for i in range(8):
        col = mix((236, 232, 222, 255), (40, 38, 38, 255), i / 7)
        c.d.rectangle([6 * S, (8 + i * 26) * S, 44 * S, (32 + i * 26) * S], fill=col)
    c.rrect(4, 4, 46, 216, 4, (0, 0, 0, 0), lw=4, outline=INK)
    c.save("task_gy_strip.png")


# ------------------------------------------------------------------ Copy the Epitaphs (audio)

def gy_epitaphs():
    c = like("task_photo.png")                                                      # Abklatsch-Bogen
    c.rrect(10, 10, 190, 140, 6, (232, 226, 210, 255), lw=4, sh=(0.05, 0.12))
    c.rrect(22, 22, 178, 128, 4, (58, 58, 64, 255), lw=0)
    c.line([(100, 34), (100, 70)], (232, 226, 210, 255), 6)
    c.line([(84, 46), (116, 46)], (232, 226, 210, 255), 6)
    for k in range(3):
        c.line([(46, 88 + k * 12), (154, 88 + k * 12)], (232, 226, 210, 255), 4)
    c.save("task_gy_rubbing.png")
    c = like("task_deer.png")                                                       # Szenenbild: Grabstein
    c.rrect(6, 6, 154, 124, 6, NIGHT_L, lw=4, sh=(0.1, 0.2))
    c.poly([(50, 116), (110, 116), (110, 50)] + [(80 + 30 * math.cos(t), 50 - 30 * math.sin(t)) for t in [j * math.pi / 10 for j in range(11)]] + [(50, 50)],
           STONE_L, lw=4)
    c.line([(80, 40), (80, 70)], STONE_D, 5)
    c.line([(68, 52), (92, 52)], STONE_D, 5)
    label(c, 80, 92, "R.I.P.", 12, STONE_D)
    c.save("task_gy_stone.png")
    c = like("task_pc.png")                                                         # Schreibpult
    c.rrect(10, 60, 290, 230, 10, OAK, lw=6, sh=(0.15, 0.25))
    c.rrect(40, 76, 260, 200, 4, PARCH, lw=4)
    for k in range(6):
        c.line([(60, 98 + k * 16), (240 - (k % 3) * 30, 98 + k * 16)], (90, 76, 60, 255), 3)
    c.ell(250, 66, 16, 10, (30, 30, 40, 255), lw=3)
    c.line([(250, 60), (284, 18)], (236, 232, 226, 255), 5)
    c.save("task_gy_desk.png")
    c = like("task_dock.png")                                                       # Ablage
    c.rrect(6, 30, 254, 114, 8, OAK, lw=5, sh=(0.12, 0.2))
    for x in range(26, 240, 46):
        c.rrect(x, 44, x + 34, 100, 3, OAK_D, lw=3)
    c.save("task_gy_shelf.png")
    c = like("task_sdcard.png")                                                     # Papierrolle
    c.rrect(6, 8, 64, 84, 4, (232, 226, 210, 255), lw=4, sh=(0.08, 0.15))
    c.line([(14, 30), (56, 30)], (120, 110, 96, 255), 3)
    c.line([(14, 44), (50, 44)], (120, 110, 96, 255), 3)
    c.d.rectangle([12 * S, 64 * S, 58 * S, 76 * S], fill=(150, 50, 50, 255))
    c.save("task_gy_scroll.png")
    c = like("task_audioguide.png")                                                 # Federkiel und Tinte
    c.rrect(30, 130, 90, 190, 8, (30, 30, 40, 255), lw=5, sh=(0.1, 0.2))
    c.line([(60, 132), (90, 14)], (236, 232, 226, 255), 7)
    c.poly([(62, 120), (84, 30), (100, 40), (72, 124)], (226, 222, 214, 255), lw=3)
    c.save("task_gy_quill.png")


def gy_icons():
    def base():
        c = like("task_icon_dino.png")
        c.rrect(6, 6, 104, 104, 14, SLATE, lw=5, sh=(0.12, 0.2))
        c.rrect(14, 14, 96, 96, 10, (44, 70, 64, 255), lw=3)
        return c
    c = base()
    c.rrect(48, 44, 62, 86, 4, CREAM, lw=3)
    c.poly([(55, 42), (61, 30), (55, 16), (49, 30)], (255, 180, 60, 255), lw=3, outline=(160, 90, 20, 255))
    c.save("task_gy_icon_candle.png")
    c = base()
    c.ell(55, 50, 26, 28, BONE, lw=4)
    c.rrect(40, 70, 70, 90, 4, BONE, lw=3)
    c.ell(45, 48, 7, 8, INK, lw=0); c.ell(65, 48, 7, 8, INK, lw=0)
    c.poly([(55, 60), (51, 68), (59, 68)], INK, lw=0)
    c.save("task_gy_icon_skull.png")
    c = base()
    c.poly([(40, 74), (40, 50), (55, 30), (70, 50), (70, 74)], BRONZE, lw=4)          # Glocke
    c.poly([(34, 78), (76, 78), (70, 70), (40, 70)], BRONZE, lw=3)
    c.ell(55, 84, 6, 6, IRON, lw=2)
    c.save("task_gy_icon_bell.png")
    c = base()
    c.ell(40, 42, 16, 16, (180, 150, 80, 255), lw=4)
    c.ell(40, 42, 6, 6, (44, 70, 64, 255), lw=2)
    c.line([(52, 50), (84, 82)], (180, 150, 80, 255), 9)
    c.line([(74, 72), (82, 64)], (180, 150, 80, 255), 7); c.line([(66, 80), (74, 72)], (180, 150, 80, 255), 7)
    c.save("task_gy_icon_key.png")
    c = base()
    c.ell(55, 60, 22, 16, (18, 18, 24, 255), lw=4)
    c.ell(70, 46, 11, 10, (18, 18, 24, 255), lw=3)
    c.poly([(80, 46), (94, 44), (80, 40)], (110, 110, 118, 255), lw=2)
    c.ell(73, 44, 2, 2, (232, 200, 90, 255), lw=0)
    c.line([(40, 70), (30, 84)], (18, 18, 24, 255), 5)
    c.save("task_gy_icon_raven.png")


# ------------------------------------------------------------------ Sign the Burial Register (timecard)

def gy_register():
    c = like("task_timecard.png")
    c.rrect(6, 6, 124, 194, 4, PARCH, lw=4, sh=(0.05, 0.12))
    c.d.rectangle([12 * S, 12 * S, 118 * S, 34 * S], fill=(40, 44, 54, 255))
    label(c, 65, 23, "BURIAL REG.", 9, PARCH)
    for k in range(6):
        c.line([(16, 96 + k * 14), (114, 96 + k * 14)], (130, 116, 96, 255), 2)
    c.line([(40, 50), (40, 76)], (60, 56, 50, 255), 4)
    c.line([(30, 60), (50, 60)], (60, 56, 50, 255), 4)
    c.d.rectangle([16 * S, 170 * S, 114 * S, 186 * S], fill=(232, 226, 206, 255))
    c.line([(20, 182), (60, 176), (90, 184)], (40, 40, 60, 255), 2)
    c.save("task_gy_register.png")
    c = like("task_clock.png")
    c.ell(150, 150, 140, 140, BRONZE, lw=6, sh=(0.2, 0.3))
    c.ell(150, 150, 118, 118, CREAM, lw=5)
    for k in range(12):
        a = math.pi * 2 * k / 12
        r0 = 100 if k % 3 == 0 else 108
        c.line([(150 + r0 * math.cos(a), 150 + r0 * math.sin(a)), (150 + 114 * math.cos(a), 150 + 114 * math.sin(a))], INK, 4 if k % 3 == 0 else 2)
    label(c, 150, 60, "XII", 18, INK)
    label(c, 150, 200, "HOUR OF DEATH", 9, (150, 40, 40, 255))
    c.ell(150, 150, 8, 8, dark(BRONZE), lw=3)
    c.rrect(136, 2, 164, 26, 6, dark(BRONZE), lw=4)
    c.save("task_gy_watch.png")


# ------------------------------------------------------------------ Clear the Wreaths (bins)

def gy_bins():
    for key, text, col in (("paper", "WREATHS", (60, 84, 60, 255)), ("glass", "FLOWERS", (92, 64, 80, 255)), ("rest", "CANDLES", (70, 70, 80, 255))):
        c = like("task_bin_paper.png")
        c.rrect(16, 40, 154, 190, 8, OAK, lw=5, sh=(0.12, 0.22), shx=(0.1, 0.12))
        for x in range(30, 150, 24):
            c.line([(x, 48), (x, 184)], OAK_D, 3)
        c.rrect(10, 24, 160, 48, 6, col, lw=5, sh=(0.15, 0.2))
        c.d.rectangle([30 * S, 110 * S, 140 * S, 130 * S], fill=CREAM)
        label(c, 85, 120, text, 10, INK)
        c.save(f"task_gy_bin_{key}.png")
    def wreath(c):
        for k in range(14):
            a = k / 14 * math.tau
            c.ell(48 + 26 * math.cos(a), 48 + 26 * math.sin(a), 11, 9, (60, 100, 60, 255) if k % 2 else (46, 84, 52, 255), lw=2)
        c.poly([(44, 70), (52, 70), (60, 90), (48, 82), (36, 90)], (150, 40, 50, 255), lw=2)
    def flowers(c):
        for k, col in enumerate(((150, 50, 70, 255), (200, 180, 90, 255), (220, 214, 206, 255))):
            c.line([(48, 88), (30 + k * 18, 30)], (70, 100, 60, 255), 4)
            c.ell(30 + k * 18, 28, 10, 9, col, lw=3)
    def candle(c):
        c.rrect(36, 34, 60, 86, 4, CREAM, lw=3)
        c.line([(48, 34), (48, 26)], INK, 3)
        c.line([(40, 44), (40, 70)], (240, 234, 216, 255), 4)
    def ribbon(c):
        c.poly([(20, 40), (76, 40), (70, 52), (76, 64), (20, 64), (26, 52)], (130, 30, 40, 255), lw=3)
        label(c, 48, 52, "R.I.P.", 8, (220, 200, 140, 255))
    def vase(c):
        c.poly([(34, 30), (62, 30), (68, 70), (58, 86), (38, 86), (28, 70)], BRONZE, lw=3)
        c.line([(36, 40), (36, 76)], BRONZE_L, 3)
    def lantern(c):
        c.rrect(30, 30, 66, 82, 4, (190, 40, 50, 230), lw=3)
        c.rrect(28, 22, 68, 32, 3, BRONZE, lw=3)
    items = {"brochure": wreath, "ticket": ribbon, "bottle": vase, "jar": lantern, "wrapper": candle, "apple": flowers}
    for name, fn in items.items():
        c = like("task_trash_bottle.png")
        fn(c)
        c.save(f"task_gy_trash_{name}.png")
    c = like("task_container.png")                                                  # Kompostkasten
    c.rrect(30, 70, 330, 290, 8, OAK, lw=6, sh=(0.12, 0.22), shx=(0.1, 0.14))
    for y in range(90, 280, 30):
        c.line([(36, y), (324, y)], OAK_D, 4)
    c.rrect(20, 40, 340, 78, 6, OAK_L, lw=6, sh=(0.15, 0.2))
    c.d.rectangle([110 * S, 150 * S, 250 * S, 176 * S], fill=CREAM)
    label(c, 180, 163, "COMPOST", 14, INK)
    c.save("task_gy_compost.png")


# ------------------------------------------------------------------ Light the Path, Lanterns Out

def gy_route():
    c = like("task_socket.png")
    c.ell(42, 42, 36, 36, IRON, lw=5, sh=(0.15, 0.25))
    c.ell(42, 42, 22, 22, IRON_D, lw=4)
    c.ell(42, 42, 8, 8, (255, 200, 120, 255), lw=2)
    c.save("task_gy_socket.png")
    c = like("task_plug.png")
    c.rrect(12, 14, 78, 60, 10, IRON_L, lw=5, sh=(0.12, 0.2))
    c.ell(45, 36, 9, 9, BRONZE, lw=3)
    c.line([(45, 60), (45, 68)], IRON_D, 8)
    c.save("task_gy_plug.png")
    c = like("task_switch_plate.png")
    c.rrect(10, 10, 170, 270, 14, STONE, lw=5, sh=(0.08, 0.18))
    c.ell(90, 140, 54, 60, STONE_D, lw=4)
    c.ell(90, 140, 36, 42, STONE, lw=3)
    for x, y in ((26, 26), (154, 26), (26, 254), (154, 254)):
        c.rivet(x, y, 5, IRON_L)
    label(c, 90, 246, "LIT", 12, (220, 190, 110, 255))
    label(c, 90, 36, "DARK", 12, (30, 32, 38, 255))
    c.save("task_gy_switchplate.png")
    c = like("task_switch_lever.png")
    c.capsule((30, 140), (30, 24), 18, IRON_L, lw=4)
    c.ell(30, 24, 14, 14, BRONZE, lw=4)
    c.ell(30, 140, 10, 10, IRON_D, lw=3)
    c.save("task_gy_switchlever.png")


def gy_fuses():
    for name, glow in (("task_gy_fuse_ok.png", True), ("task_gy_fuse_dead.png", False), ("task_gy_fuse_new.png", None)):
        c = like("task_fuse_ok.png")
        col = (255, 214, 140, 255) if glow else ((96, 92, 86, 255) if glow is False else (236, 232, 222, 255))
        c.rrect(18, 12, 46, 88, 8, col, lw=4, sh=(0.1, 0.22))
        c.rrect(10, 4, 54, 16, 4, IRON_L, lw=3)
        c.rrect(10, 84, 54, 96, 4, IRON_L, lw=3)
        if glow:
            c.ell(32, 50, 6, 12, (255, 246, 210, 255), lw=0)
            c.glow(32, 50, 16, 20, (255, 214, 140, 110), 8)
        elif glow is False:
            c.line([(26, 34), (38, 66)], (40, 36, 34, 255), 3)
            c.ell(32, 30, 6, 4, (40, 36, 34, 200), lw=0)
        c.save(name)


# ------------------------------------------------------------------ Unlock the Ossuary (hiero)

def gy_ossuary():
    c = like("task_cartouche.png")
    c.rrect(6, 6, 114, 144, 8, (190, 182, 160, 255), lw=5, sh=(0.12, 0.22))
    c.rrect(16, 16, 104, 134, 5, (162, 154, 132, 255), lw=3)
    for x, y in ((24, 24), (96, 24), (24, 126), (96, 126)):
        c.ell(x, y, 5, 5, BONE, lw=2)
    c.save("task_gy_tile.png")
    runes = [
        [[(22, 72), (22, 8), (58, 22)], [(22, 36), (58, 50)]],
        [[(22, 72), (22, 8), (58, 30), (58, 72)]],
        [[(22, 72), (22, 8)], [(22, 20), (56, 40), (22, 60)]],
        [[(22, 72), (22, 8), (58, 28)], [(22, 36), (58, 56)]],
        [[(22, 72), (22, 8), (56, 24), (26, 42), (58, 72)]],
        [[(58, 10), (24, 40), (58, 70)]],
        [[(14, 12), (66, 68)], [(66, 12), (14, 68)]],
        [[(22, 72), (22, 8), (58, 24), (22, 42)]],
        [[(22, 72), (22, 8)], [(58, 72), (58, 8)], [(22, 28), (58, 52)]],
        [[(40, 72), (40, 8)], [(16, 54), (64, 26)]],
    ]
    for k in range(10):
        c = like("task_glyph0.png")
        for pts in runes[k]:
            c.line(pts, INK, 11)
            c.line(pts, (96, 40, 36, 255), 6)
        c.save(f"task_gy_rune{k}.png")


# ------------------------------------------------------------------ Miasma (waterworks)

def gy_pipes():
    c = like("task_pipes.png")
    stone_wall(c, 0, 0, 720, 520, seed=9, bw=70, bh=40, cols=[(60, 64, 72, 255), (54, 58, 66, 255), (66, 70, 78, 255)])
    # Kontrakt: Rohre auf y 150 und 330, Ventile zwischen x 130 und 610
    for y in (150, 330):
        c.capsule((60, y), (660, y), 34, (110, 112, 104, 255), lw=5)
        c.line([(70, y - 8), (650, y - 8)], (150, 152, 142, 255), 5)
        for x in (110, 630):
            c.rrect(x - 16, y - 26, x + 16, y + 26, 5, IRON, lw=4)
    c.capsule((360, 150), (360, 330), 30, (110, 112, 104, 255), lw=5)
    c.rrect(300, 420, 420, 500, 6, IRON_D, lw=5)                                    # Gruftgitter
    for x in range(310, 412, 16):
        c.line([(x, 424), (x, 496)], IRON_L, 4)
    c.glow(360, 430, 90, 40, (150, 208, 112, 100), 16)
    c.save("task_gy_pipes.png")
    c = like("task_valve.png")
    c.ell(80, 80, 66, 66, (0, 0, 0, 0), lw=14, outline=INK)
    c.ell(80, 80, 66, 66, (0, 0, 0, 0), lw=8, outline=(140, 40, 40, 255))
    for k in range(6):
        a = math.pi * k / 3
        c.line([(80, 80), (80 + 62 * math.cos(a), 80 + 62 * math.sin(a))], INK, 12)
        c.line([(80, 80), (80 + 62 * math.cos(a), 80 + 62 * math.sin(a))], (150, 50, 50, 255), 7)
    c.ell(80, 80, 18, 18, IRON, lw=4)
    c.save("task_gy_wheel.png")
    c = like("task_card.png")
    c.rrect(8, 8, 212, 172, 6, PARCH, lw=4, sh=(0.05, 0.12))
    c.line([(20, 44), (200, 44)], (140, 130, 110, 255), 2)
    c.save("task_gy_plan.png")


# ------------------------------------------------------------------ Zuordnung

CUSTOM_TASKS = {
    "FixWiring": "splice", "SwipeCard": "timecard", "CalibrateDistributor": "climate", "ChartCourse": "constellation",
    "CleanO2Filter": "dust", "DivertPower": "route", "PrimeShields": "lanterns", "StabilizeSteering": "projector",
    "UnlockManifolds": "hiero", "UploadData": "audio", "AlignEngineOutput": "generator", "ClearAsteroids": "moths",
    "EmptyGarbage": "bins", "FuelEngines": "refuel", "InspectSample": "pigment", "RestoreOxy": "waterworks", "FixLights": "fusebox",
}

TASK_ART = {
    "task_museum_panel.png": "task_gy_panel.png", "task_wald_panel.png": "task_gy_panel.png",
    "task_shop_panel.png": "task_gy_panel.png", "task_steel_panel.png": "task_gy_iron.png",
    "dust:task_museum_dino.png": "task_gy_crypt.png", "dust:task_museum_dust.png": "task_gy_dust.png", "dust:task_brush.png": "task_gy_broom.png",
    "moths:task_gallery.png": "task_gy_night.png", "moths:task_moth.png": "task_gy_raven.png",
    "moths:task_torch.png": "task_gy_lantern.png", "moths:task_jar.png": "task_gy_open.png",
    "lanterns:task_dock_night.png": "task_gy_wards.png", "lanterns:task_lantern_on.png": "task_gy_candle_on.png",
    "lanterns:task_lantern_off.png": "task_gy_candle_off.png",
    "climate:task_gauge_band.png": "task_gy_gauge.png", "climate:task_needle.png": "task_gy_needle.png",
    "generator:task_generator.png": "task_gy_winch.png",
    "refuel:task_boiler.png": "task_gy_furnace.png", "refuel:task_can.png": "task_gy_oilcan.png",
    "constellation:task_card.png": "task_gy_card.png", "constellation:task_sky.png": "task_gy_sky.png",
    "projector:task_sky.png": "task_gy_moonsky.png",
    "pigment:task_vial.png": "task_gy_vial.png", "pigment:task_strip.png": "task_gy_strip.png",
    "audio:task_photo.png": "task_gy_rubbing.png", "audio:task_deer.png": "task_gy_stone.png",
    "audio:task_pc.png": "task_gy_desk.png", "audio:task_dock.png": "task_gy_shelf.png",
    "audio:task_sdcard.png": "task_gy_scroll.png", "audio:task_audioguide.png": "task_gy_quill.png",
    "audio:task_icon_dino.png": "task_gy_icon_candle.png", "audio:task_icon_mummy.png": "task_gy_icon_skull.png",
    "audio:task_icon_planet.png": "task_gy_icon_bell.png", "audio:task_icon_gem.png": "task_gy_icon_key.png",
    "audio:task_icon_painting.png": "task_gy_icon_raven.png",
    "timecard:task_timecard.png": "task_gy_register.png", "timecard:task_clock.png": "task_gy_watch.png",
    "bins:task_bin_paper.png": "task_gy_bin_paper.png", "bins:task_bin_glass.png": "task_gy_bin_glass.png",
    "bins:task_bin_rest.png": "task_gy_bin_rest.png", "bins:task_container.png": "task_gy_compost.png",
    "bins:task_trash_brochure.png": "task_gy_trash_brochure.png", "bins:task_trash_ticket.png": "task_gy_trash_ticket.png",
    "bins:task_trash_bottle.png": "task_gy_trash_bottle.png", "bins:task_trash_jar.png": "task_gy_trash_jar.png",
    "bins:task_trash_wrapper.png": "task_gy_trash_wrapper.png", "bins:task_trash_apple.png": "task_gy_trash_apple.png",
    "route:task_socket.png": "task_gy_socket.png", "route:task_plug.png": "task_gy_plug.png",
    "route:task_switch_plate.png": "task_gy_switchplate.png", "route:task_switch_lever.png": "task_gy_switchlever.png",
    "fusebox:task_fuse_ok.png": "task_gy_fuse_ok.png", "fusebox:task_fuse_dead.png": "task_gy_fuse_dead.png",
    "fusebox:task_fuse_new.png": "task_gy_fuse_new.png",
    "fusebox:task_switch_plate.png": "task_gy_switchplate.png", "fusebox:task_switch_lever.png": "task_gy_switchlever.png",
    "hiero:task_cartouche.png": "task_gy_tile.png",
    **{f"hiero:task_glyph{k}.png": f"task_gy_rune{k}.png" for k in range(10)},
    "waterworks:task_pipes.png": "task_gy_pipes.png", "waterworks:task_valve.png": "task_gy_wheel.png",
    "waterworks:task_card.png": "task_gy_plan.png",
}

TASK_TEXT = {
    "audio:FIND THE ANIMAL": "FIND THE EPITAPH", "audio:EXHIBIT": "GRAVE",
    "audio:TRACK 1": "PAGE 1", "audio:TRACK 2": "PAGE 2", "audio:TRACK 3": "PAGE 3",
    "bins:PAPER": "WREATHS", "bins:GLASS": "FLOWERS", "bins:OTHER": "CANDLES",
    "climate:TEMP": "WICK", "climate:HUMIDITY": "OIL", "climate:LIGHT": "FLAME",
    "waterworks:PLAN": "VENT",
}


def render(out_dir):
    GT.OUT = Path(out_dir)
    GT.OUT.mkdir(parents=True, exist_ok=True)
    gy_panel(); gy_iron_panel()
    gy_crypt(); gy_dust(); gy_broom()
    gy_night(); gy_raven(); gy_lantern_tool(); gy_nest()
    gy_wards(); gy_candles()
    gy_gauge(); gy_winch(); gy_furnace(); gy_oilcan()
    gy_gravecard(); gy_sky("task_gy_sky.png"); gy_sky("task_gy_moonsky.png", moon=True)
    gy_ashes(); gy_epitaphs(); gy_icons(); gy_register(); gy_bins(); gy_route(); gy_fuses(); gy_ossuary(); gy_pipes()
    missing = sorted({v for v in TASK_ART.values() if not (GT.OUT / v).exists()})
    if missing:
        print("WARN task art missing:", missing)


def map_extra(out_dir):
    render(out_dir)
    return {"customTasks": CUSTOM_TASKS, "taskArt": TASK_ART, "taskText": TASK_TEXT}


if __name__ == "__main__":
    render(HERE.parent / "Resources" / "graveyard")
