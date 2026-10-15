# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_villa_tasks.py - Minispiel-Grafik von Hollowmere Manor (Audit 15.10., Schritt 3).
#
# Die Villa nutzt die Atlas-Bausteine (docs/TASK_KONZEPT.md im Atlas-Repo); HollowmereMap.TaskArt leitet deren
# Dateien auf die Bilder hier um. Jede Datei hat exakt die Groesse der Datei, die sie ersetzt (wird aus
# UnknownsAtlas/assets gelesen), damit Drehpunkte, Fenster und Rasterpositionen der Bausteine stimmen.
# Stil wie gen_tasks.py (flache Toene, Glanz, dunkle Kontur), Palette der Villa: Nussholz, Bordeaux-Damast,
# angelaufenes Messing, Porzellan, Crew-Schwarz mit Gaffer-Gelb, Kerzenlicht.
#
#   python tools/gen_villa_tasks.py   ->  Resources/villa/task_villa_*.png, task_spirit_*.png

import math
import os
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ATLAS = HERE.parent.parent / "UnknownsAtlas"
sys.path.insert(0, str(ATLAS / "tools"))
import gen_tasks as G                                           # noqa: E402  (C, label, frame_wood, Farben)
from gen_tasks import C, INK, S, label, mix, dark, light       # noqa: E402

OUT = HERE.parent / "Resources" / "villa"
G.OUT = OUT

WALNUT, WALNUT_L, WALNUT_D = (104, 72, 46, 255), (138, 98, 62, 255), (66, 44, 28, 255)
BORDEAUX, BORDEAUX_L, BORDEAUX_D = (96, 34, 46, 255), (122, 48, 62, 255), (62, 22, 30, 255)
BRASS, BRASS_L, BRASS_D = (172, 138, 72, 255), (220, 194, 122, 255), (110, 84, 40, 255)
PORC, PORC_D = (230, 226, 214, 255), (184, 178, 164, 255)
CREW, CREW_L, CREW_D = (52, 52, 60, 255), (78, 80, 88, 255), (32, 32, 38, 255)
GAFFER = (232, 194, 58, 255)
CREAM = (220, 212, 188, 255)
PARCH = (208, 194, 156, 255)
BLOOD, BLOOD_L = (138, 26, 34, 255), (184, 38, 46, 255)
STEEL, STEEL_L = (138, 142, 152, 255), (176, 180, 190, 255)
COPPER, COPPER_L = (176, 104, 58, 255), (214, 146, 92, 255)
NIGHT, NIGHT_L = (22, 26, 44, 255), (40, 48, 76, 255)
MOON = (232, 236, 246, 255)
WARM = (255, 210, 138, 120)
SOOT = (24, 22, 22, 255)
GREEN = (72, 176, 98, 255)
RED = (214, 62, 58, 255)


def size_of(name):
    return Image.open(ATLAS / "assets" / name).size


def like(name):
    """Leinwand in der Groesse der Atlas-Datei, die ersetzt wird."""
    w, h = size_of(name)
    return C(w, h)


def damask(c, x0, y0, x1, y1, seed=3):
    """Bordeaux-Damast: Rauten mit Ornamentpunkten."""
    c.d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=BORDEAUX)
    for y in range(y0 + 12, y1, 44):
        for i, x in enumerate(range(x0 + 10, x1, 44)):
            ox = 22 if (y // 44) % 2 else 0
            cx, cy = x + ox, y
            if cx > x1 - 6:
                continue
            pts = [(cx, cy - 14), (cx + 12, cy), (cx, cy + 14), (cx - 12, cy)]
            c.d.polygon([(px * S, py * S) for px, py in pts], fill=BORDEAUX_L)
            c.d.ellipse([(cx - 3) * S, (cy - 3) * S, (cx + 3) * S, (cy + 3) * S], fill=BORDEAUX_D)
    m, md = c.mask()
    md.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=255)
    c.mottle(0.07, 18, seed=seed, mask=m)


def candle_glow(c, x, y, r=60):
    c.glow(x, y, r, r * 0.7, (255, 214, 140, 70), 16)


def cobweb(c, x, y, size, qx, qy):
    col = (236, 236, 242, 95)
    for k in range(6):
        a = math.pi / 2 * k / 5
        c.line([(x, y), (x + qx * size * math.cos(a), y + qy * size * math.sin(a))], col, 2)
    for r in (0.35, 0.65, 0.95):
        pts = [(x + qx * r * size * math.cos(math.pi / 2 * k / 5), y + qy * r * size * math.sin(math.pi / 2 * k / 5)) for k in range(6)]
        c.line(pts, col, 2)


# ------------------------------------------------------------------ Tafeln

def villa_panel():
    c = like("task_museum_panel.png")
    G.frame_wood(c, WALNUT_D)
    c.rrect(26, 26, 694, 494, 14, BRASS, lw=4, sh=(0.22, 0.3))
    damask(c, 36, 36, 684, 484)
    c.vignette(0.5, 36, 36, 684, 484)
    candle_glow(c, 70, 70)
    candle_glow(c, 650, 70)
    cobweb(c, 684, 36, 70, -1, 1)
    for x in (48, 672):
        for y in (48, 472):
            c.rivet(x, y, 6, BRASS_L)
    c.save("task_villa_panel.png")


def villa_machine():
    c = like("task_steel_panel.png")
    c.rrect(4, 4, 716, 516, 22, CREW_D, lw=8, sh=(0.12, 0.2))
    c.rrect(26, 26, 694, 494, 12, CREW, lw=4, sh=(0.18, 0.25))
    for x in range(44, 680, 24):                                         # Rippen
        c.d.rectangle([x * S, 40 * S, (x + 10) * S, 480 * S], fill=CREW_L)
    m, md = c.mask()
    md.rectangle([36 * S, 36 * S, 684 * S, 484 * S], fill=255)
    c.brushed(0.05, seed=4, mask=m)
    c.vignette(0.4, 26, 26, 694, 494)
    for x in (14, 706):
        c.d.rectangle([(x - 6) * S, 10 * S, (x + 6) * S, 510 * S], fill=STEEL)
    for x in (48, 672):
        for y in (48, 472):
            c.rivet(x, y, 7, STEEL_L)
    c.d.rectangle([260 * S, 14 * S, 460 * S, 34 * S], fill=GAFFER)
    label(c, 360, 24, "HOLLOWMERE PICTURES", 13, INK)
    c.save("task_villa_machine.png")


# ------------------------------------------------------------------ Sweep the Chimney (dust)

def villa_flue():
    c = like("task_museum_dino.png")
    c.rrect(6, 6, 554, 294, 10, (74, 44, 36, 255), lw=6, sh=(0.1, 0.2))
    for row, y in enumerate(range(14, 290, 30)):
        for x in range(14 + (18 if row % 2 else 0), 546, 46):
            c.rrect(x, y, min(x + 42, 548), y + 26, 3, (142, 78, 58, 255) if (x + row) % 3 else (124, 66, 50, 255), lw=3, outline=(60, 34, 28, 255))
    c.rrect(200, 90, 360, 220, 8, (56, 58, 66, 255), lw=5, sh=(0.2, 0.3))     # Eisenklappe
    c.ell(280, 155, 34, 30, (70, 72, 80, 255), lw=5)
    c.ell(280, 155, 18, 16, (40, 42, 48, 255), lw=4)
    c.rivet(210, 100, 5); c.rivet(350, 100, 5); c.rivet(210, 210, 5); c.rivet(350, 210, 5)
    c.glow(280, 260, 120, 40, (255, 140, 60, 70), 14)
    c.save("task_villa_flue.png")


def villa_soot():
    w, h = 280, 150
    rnd = np.random.default_rng(11)
    small = rnd.random((10, 18)).astype(np.float32)
    cloud = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255
    fine = rnd.random((h, w)).astype(np.float32)
    fine = np.asarray(Image.fromarray((fine * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.4)), dtype=np.float32) / 255
    v = 34 + (cloud - 0.5) * 24 + (fine - 0.5) * 18
    rgb = np.stack([v + 2, v, v], axis=-1)
    a = np.full((h, w), 238, dtype=np.float32) - (cloud - 0.5) * 24
    ys = np.arange(h)[:, None]
    xs = np.arange(w)[None, :]
    edge = np.minimum(np.minimum(xs, w - 1 - xs), np.minimum(ys, h - 1 - ys)).astype(np.float32)
    a *= np.clip(edge / 3.0 + (fine - 0.5) * 0.8, 0, 1)
    img = Image.fromarray(np.clip(np.concatenate([rgb, a[..., None]], axis=-1), 0, 255).astype(np.uint8), "RGBA")
    fl = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    for _ in range(60):                                                    # Russflocken
        x, y = rnd.integers(0, w * 2), rnd.integers(0, h * 2)
        r = int(rnd.integers(2, 7))
        fd.ellipse([x - r, y - r, x + r, y + r], fill=(70, 66, 64, 90))
    fl = fl.filter(ImageFilter.GaussianBlur(2)).resize((w, h), Image.LANCZOS)
    img.alpha_composite(fl)
    img.save(OUT / "task_villa_soot.png")
    print(OUT / "task_villa_soot.png", img.size)


def villa_brush():
    c = like("task_brush.png")
    c.ell(60, 70, 40, 34, SOOT, lw=0)
    for k in range(18):
        a = math.pi * 2 * k / 18
        c.line([(60, 66), (60 + 44 * math.cos(a), 66 + 38 * math.sin(a))], (48, 46, 46, 255), 6)
    c.ell(60, 66, 14, 12, (90, 70, 50, 255), lw=4)
    c.line([(60, 66), (60, 20)], WALNUT_L, 8)
    c.save("task_villa_brush.png")


# ------------------------------------------------------------------ Shoo the Bats (moths)

def villa_window():
    c = like("task_gallery.png")
    G.frame_wood(c, WALNUT_D)
    damask(c, 30, 30, 690, 490, seed=5)
    c.vignette(0.45, 30, 30, 690, 490)
    # Fenster mit Laeden, Nacht, Mond
    c.rrect(220, 60, 500, 380, 6, WALNUT, lw=6, sh=(0.15, 0.2))
    c.d.rectangle([236 * S, 76 * S, 484 * S, 364 * S], fill=NIGHT)
    rnd = random.Random(7)
    for k in range(60):
        sx, sy = (236 + rnd.random() * 248) * S, (76 + rnd.random() * 288) * S
        c.d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(220, 226, 240, 200))
    c.glow(420, 140, 50, 50, (232, 236, 246, 120), 14)
    c.ell(420, 140, 30, 30, MOON, lw=0)
    c.line([(360, 76), (360, 364)], WALNUT, 10)
    c.line([(236, 220), (484, 220)], WALNUT, 10)
    for x0, x1 in ((120, 212), (508, 600)):                               # Laeden
        c.rrect(x0, 56, x1, 384, 4, WALNUT_L, lw=5, sh=(0.1, 0.2))
        for y in range(80, 370, 28):
            c.line([(x0 + 10, y), (x1 - 10, y - 8)], WALNUT_D, 4)
    c.rrect(200, 380, 520, 404, 4, WALNUT_L, lw=5, sh=(0.1, 0.2))        # Fensterbank
    for gx, gy in ((110, 440), (600, 440), (360, 460)):                   # Geweihe unter dem Fenster
        for s in (-1, 1):
            c.line([(gx, gy + 20), (gx + s * 18, gy), (gx + s * 34, gy - 26)], (216, 204, 176, 255), 6)
            c.line([(gx + s * 18, gy), (gx + s * 36, gy + 6)], (216, 204, 176, 255), 5)
    cobweb(c, 690, 30, 90, -1, 1)
    cobweb(c, 30, 30, 70, 1, 1)
    c.save("task_villa_window.png")


def villa_bat():
    c = like("task_moth.png")
    body = (18, 18, 24, 255)
    c.poly([(45, 38), (28, 22), (6, 30), (14, 44), (4, 56), (24, 52), (45, 62), (66, 52), (86, 56), (76, 44), (84, 30), (62, 22)], body, lw=4)
    c.ell(45, 38, 10, 9, (30, 30, 38, 255), lw=3)
    c.d.ellipse([40 * S, 34 * S, 43 * S, 37 * S], fill=RED)
    c.d.ellipse([47 * S, 34 * S, 50 * S, 37 * S], fill=RED)
    c.poly([(40, 30), (43, 22), (46, 30)], body, lw=2)
    c.poly([(44, 30), (47, 22), (50, 30)], body, lw=2)
    c.save("task_villa_bat.png")


def villa_broom():
    c = like("task_torch.png")
    c.line([(60, 230), (170, 70)], WALNUT_D, 16)
    c.line([(60, 230), (170, 70)], WALNUT_L, 10)
    c.poly([(150, 90), (200, 50), (250, 90), (220, 130), (180, 128)], (200, 164, 96, 255), lw=5)
    for k in range(9):
        c.line([(160 + k * 10, 92 - k * 4), (176 + k * 10, 128 - k * 2)], (150, 116, 60, 255), 3)
    c.line([(170, 108), (218, 72)], BRASS, 6)
    c.save("task_villa_broom.png")


def villa_openwindow():
    c = like("task_jar.png")
    c.rrect(6, 6, 124, 154, 6, WALNUT, lw=5, sh=(0.12, 0.2))
    c.d.rectangle([18 * S, 18 * S, 112 * S, 142 * S], fill=NIGHT)
    c.ell(90, 44, 16, 16, MOON, lw=0)
    c.line([(65, 18), (65, 142)], WALNUT, 6)
    c.line([(18, 80), (112, 80)], WALNUT, 6)
    c.glow(65, 80, 40, 50, (200, 220, 255, 60), 10)
    c.save("task_villa_openwindow.png")


# ------------------------------------------------------------------ Light the Ward Candles (lanterns)

def villa_chapel():
    c = like("task_dock_night.png")
    G.frame_wood(c, WALNUT_D)
    c.d.rectangle([30 * S, 30 * S, 690 * S, 490 * S], fill=(44, 46, 56, 255))
    for row, y in enumerate(range(30, 490, 40)):                           # Steinwand
        for x in range(30 + (26 if row % 2 else 0), 690, 54):
            c.rrect(x, y, min(x + 50, 690), y + 36, 3, (62, 64, 76, 255) if (x + row) % 3 else (54, 56, 66, 255), lw=3, outline=(34, 36, 44, 255))
    # Buntglasfenster
    c.poly([(300, 70), (420, 70), (430, 130), (430, 300), (290, 300), (290, 130)], (26, 28, 36, 255), lw=6)
    cols = [(150, 40, 60, 160), (40, 70, 150, 160), (200, 160, 60, 160), (40, 120, 80, 160)]
    for i, (x0, y0, x1, y1) in enumerate(((298, 136, 358, 216), (362, 136, 422, 216), (298, 220, 358, 294), (362, 220, 422, 294))):
        c.d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=cols[i])
    c.ell(360, 100, 36, 28, (200, 160, 60, 160), lw=4)
    c.vignette(0.5, 30, 30, 690, 490)
    c.rrect(60, 400, 660, 470, 6, (72, 76, 88, 255), lw=6, sh=(0.15, 0.25))   # Altarstufe
    c.rrect(40, 440, 680, 490, 4, (60, 62, 72, 255), lw=5)
    cobweb(c, 690, 30, 80, -1, 1)
    c.save("task_villa_chapel.png")


def villa_candles():
    for name, lit in (("task_villa_candle_off.png", False), ("task_villa_candle_on.png", True)):
        c = C(*size_of("task_lantern_on.png"))
        if lit:
            c.glow(60, 40, 50, 60, (255, 214, 140, 140), 14)
        c.ell(60, 150, 30, 12, (60, 62, 72, 255), lw=4, sh=(0.15, 0.25))      # Eisenfuss
        c.rrect(44, 60, 76, 150, 5, CREAM, lw=4, sh=(0.1, 0.2))
        c.line([(50, 70), (50, 140)], (236, 230, 210, 255), 3)
        c.ell(60, 60, 16, 6, (236, 230, 210, 255), lw=3)
        c.line([(52, 66), (52, 100)], (236, 230, 210, 255), 5)                 # Wachsnase
        if lit:
            c.poly([(60, 56), (68, 42), (60, 18), (52, 42)], (255, 180, 60, 255), lw=3, outline=(160, 90, 20, 255))
            c.poly([(60, 52), (64, 42), (60, 30), (56, 42)], (255, 244, 200, 255), lw=0)
        else:
            c.line([(60, 56), (60, 48)], INK, 3)
        c.save(name)


# ------------------------------------------------------------------ Dimmer, Generator, Treibstoff

def villa_gauge():
    c = like("task_gauge_band.png")
    G.dial_face(c, 140, 140, green_pil=(270 - 34, 270 + 34))
    c.ell(140, 140, 122, 122, (0, 0, 0, 0), lw=10, outline=BRASS)
    label(c, 140, 200, "DIMMER", 16, BRASS_D)
    c.save("task_villa_gauge_band.png")
    c = like("task_needle.png")
    c.poly([(2, 10), (110, 4), (118, 10), (110, 16)], (214, 62, 58, 255), lw=3)
    c.ell(12, 10, 7, 7, BRASS, lw=3)
    c.save("task_villa_needle.png")


def villa_generator():
    c = like("task_generator.png")
    c.rrect(30, 60, 270, 220, 10, (232, 184, 48, 255), lw=6, sh=(0.15, 0.22))
    c.rrect(44, 76, 150, 206, 6, CREW, lw=4)
    for y in range(90, 200, 16):
        c.line([(52, y), (142, y)], CREW_L, 4)
    c.ell(210, 120, 34, 34, CREAM, lw=5, sh=(0.1, 0.2))
    c.line([(210, 120), (232, 100)], RED, 4)
    c.ell(210, 120, 5, 5, INK, lw=0)
    c.ell(210, 180, 14, 14, RED, lw=4)
    c.rrect(60, 36, 240, 56, 6, CREW, lw=4)
    c.d.rectangle([180 * S, 60 * S, 262 * S, 70 * S], fill=GAFFER)
    c.rrect(262, 100, 296, 118, 4, STEEL, lw=3)
    for x in (60, 240):
        c.ell(x, 232, 16, 16, CREW_D, lw=4)
    label(c, 100, 46, "GEN", 12, GAFFER)
    c.save("task_villa_generator.png")


def villa_drum():
    c = like("task_boiler.png")
    c.ell(180, 380, 130, 22, (0, 0, 0, 70), lw=0)
    c.rrect(60, 40, 300, 370, 24, (176, 48, 40, 255), lw=6, sh=(0.1, 0.25), shx=(0.12, 0.16))
    for y in (120, 230, 340):
        c.line([(60, y), (300, y)], (120, 32, 28, 255), 6)
    c.ell(180, 40, 120, 24, (200, 60, 52, 255), lw=6)
    c.ell(230, 36, 12, 6, STEEL, lw=3)
    label(c, 180, 190, "FUEL", 40, (240, 224, 208, 255))
    c.poly([(150, 240), (210, 240), (180, 292)], (240, 200, 60, 255), lw=4)   # Warnzeichen
    label(c, 180, 262, "!", 20, INK)
    c.glint(100, 90, 14, 60, 60, rot=0)
    c.save("task_villa_drum.png")


def villa_jerrycan():
    c = like("task_can.png")
    # Kontrakt: Fenster x 50..130, y 70..210 bleibt transparent (Fuellstand dahinter)
    c.rrect(20, 40, 160, 230, 12, (74, 106, 58, 255), lw=6, sh=(0.1, 0.22), shx=(0.1, 0.14))
    c.d.rectangle([50 * S, 70 * S, 130 * S, 210 * S], fill=(0, 0, 0, 0))
    c.d.rectangle([48 * S, 68 * S, 132 * S, 212 * S], outline=INK, width=4 * S)
    c.rrect(60, 14, 120, 44, 6, (74, 106, 58, 255), lw=5)
    c.rrect(128, 18, 156, 34, 5, (40, 40, 46, 255), lw=4)
    c.line([(64, 48), (116, 48)], (110, 150, 90, 255), 5)
    c.d.rectangle([56 * S, 214 * S, 124 * S, 224 * S], fill=GAFFER)
    label(c, 90, 219, "10 L", 9, INK)
    c.save("task_villa_jerrycan.png")


# ------------------------------------------------------------------ Chart the Stars, Focus the Telescope

def villa_starcard():
    c = like("task_card.png")
    c.rrect(6, 6, 214, 174, 8, BRASS, lw=5, sh=(0.2, 0.3))
    c.rrect(16, 16, 204, 164, 5, PARCH, lw=3)
    m, md = c.mask()
    md.rectangle([16 * S, 16 * S, 204 * S, 164 * S], fill=255)
    c.mottle(0.07, 10, seed=3, mask=m)
    label(c, 110, 30, "HOLLOWMERE SKY", 11, (60, 50, 90, 255))
    for x, y in ((40, 60), (60, 90), (100, 120), (140, 80), (170, 110), (190, 50)):
        c.d.ellipse([(x - 3) * S, (y - 3) * S, (x + 3) * S, (y + 3) * S], fill=(60, 50, 90, 255))
    c.line([(40, 60), (60, 90), (100, 120), (140, 80), (170, 110), (190, 50)], (60, 50, 90, 200), 2)
    label(c, 110, 150, "OCT 31", 11, (160, 40, 40, 255))
    c.save("task_villa_starcard.png")


def villa_sky(name, moon=False):
    c = like("task_sky.png")
    c.ell(220, 220, 218, 218, NIGHT, lw=0)
    rnd = random.Random(21 if moon else 9)
    for _ in range(140):
        a, r = rnd.random() * math.tau, rnd.random() ** 0.5 * 210
        x, y = 220 + r * math.cos(a), 220 + r * math.sin(a)
        s = rnd.choice((1.5, 2, 2.5, 3))
        c.d.ellipse([(x - s) * S, (y - s) * S, (x + s) * S, (y + s) * S], fill=(220, 226, 240, rnd.randint(140, 255)))
    c.glow(220, 220, 190, 190, (60, 70, 110, 90), 30)
    if moon:
        c.glow(220, 210, 110, 110, (232, 236, 246, 90), 20)
        c.ell(220, 210, 80, 80, MOON, lw=0)
        for (mx, my, mr) in ((195, 190, 14), (240, 230, 20), (210, 240, 9), (250, 185, 7)):
            c.ell(mx, my, mr, mr, (206, 210, 222, 255), lw=0)
    else:
        c.ell(360, 90, 26, 26, MOON, lw=0)
        c.ell(372, 84, 24, 24, NIGHT, lw=0)                                  # Sichel
    # Wolkenfetzen
    for (cx, cy, rx) in ((120, 340, 70), (330, 360, 60)):
        c.glow(cx, cy, rx, rx * 0.4, (90, 96, 120, 110), 16)
    c.save(name)


# ------------------------------------------------------------------ Mix the Fake Blood (pigment)

def villa_vial():
    c = like("task_vial.png")
    c.rrect(14, 50, 56, 190, 14, (210, 222, 232, 110), lw=4, outline=INK, sh=(0.0, 0.0))
    c.d.rectangle([18 * S, 90 * S, 52 * S, 186 * S], fill=BLOOD)
    c.ell(35, 90, 17, 5, BLOOD_L, lw=0)
    c.rrect(22, 22, 48, 56, 5, (60, 40, 30, 255), lw=4)
    c.line([(20, 60), (20, 180)], (255, 255, 255, 110), 3)
    c.d.rectangle([16 * S, 120 * S, 54 * S, 150 * S], fill=CREAM)
    label(c, 35, 135, "BLOOD", 8, INK)
    c.save("task_villa_vial.png")
    c = like("task_strip.png")
    for i in range(8):
        col = mix((255, 120, 110, 255), (70, 8, 14, 255), i / 7)
        c.d.rectangle([6 * S, (8 + i * 26) * S, 44 * S, (32 + i * 26) * S], fill=col)
    c.rrect(4, 4, 46, 216, 4, (0, 0, 0, 0), lw=4, outline=INK)
    c.save("task_villa_strip.png")


# ------------------------------------------------------------------ Back Up the Dailies (audio)

def villa_reelcan():
    c = like("task_photo.png")
    c.rrect(10, 10, 190, 140, 10, STEEL, lw=5, sh=(0.15, 0.25))
    c.ell(100, 75, 46, 46, (120, 124, 134, 255), lw=4)
    c.ell(100, 75, 12, 12, (90, 94, 102, 255), lw=3)
    c.d.rectangle([30 * S, 108 * S, 170 * S, 132 * S], fill=GAFFER)
    label(c, 100, 120, "REEL", 12, INK)
    c.save("task_villa_reelcan.png")
    c = like("task_deer.png")                                               # Szenenbild: Regieklappe
    c.rrect(14, 30, 146, 120, 6, (32, 34, 42, 255), lw=5, sh=(0.15, 0.2))
    for k in range(5):
        c.d.polygon([((20 + k * 26) * S, 14 * S), ((36 + k * 26) * S, 14 * S), ((44 + k * 26) * S, 32 * S), ((28 + k * 26) * S, 32 * S)], fill=(240, 240, 240, 255) if k % 2 == 0 else (24, 24, 28, 255))
    c.line([(14, 32), (146, 32)], INK, 4)
    for k in range(3):
        c.line([(24, 50 + k * 20), (136, 50 + k * 20)], (200, 200, 208, 255), 2)
    label(c, 80, 60, "SCENE 13", 11, (240, 240, 240, 255))
    c.save("task_villa_scene.png")
    c = like("task_pc.png")                                                 # Bandgeraet
    c.rrect(10, 60, 290, 230, 10, CREW, lw=6, sh=(0.15, 0.25))
    for x in (90, 210):
        c.ell(x, 130, 46, 46, (138, 106, 58, 255), lw=5)
        c.ell(x, 130, 24, 24, (90, 66, 36, 255), lw=3)
        c.ell(x, 130, 7, 7, STEEL, lw=2)
    c.line([(90, 176), (210, 176)], (90, 66, 36, 255), 5)
    c.rrect(120, 196, 180, 216, 4, CREW_D, lw=3)
    c.ell(150, 206, 6, 6, RED, lw=2)
    c.d.rectangle([30 * S, 40 * S, 120 * S, 58 * S], fill=GAFFER)
    label(c, 75, 49, "DAILIES", 11, INK)
    c.save("task_villa_recorder.png")
    c = like("task_dock.png")                                               # Ablage fuer Baender
    c.rrect(6, 30, 254, 114, 8, WALNUT, lw=5, sh=(0.12, 0.2))
    for x in range(26, 240, 46):
        c.rrect(x, 44, x + 34, 100, 3, WALNUT_D, lw=3)
    c.save("task_villa_reeldock.png")
    c = like("task_sdcard.png")                                             # Bandschachtel
    c.rrect(6, 8, 64, 84, 4, (138, 106, 58, 255), lw=4, sh=(0.12, 0.2))
    c.ell(35, 40, 18, 18, (90, 66, 36, 255), lw=3)
    c.d.rectangle([12 * S, 64 * S, 58 * S, 76 * S], fill=CREAM)
    c.save("task_villa_tape.png")
    c = like("task_audioguide.png")                                         # Filmrolle
    c.ell(60, 100, 54, 54, (138, 106, 58, 255), lw=5, sh=(0.1, 0.2))
    c.ell(60, 100, 30, 30, (90, 66, 36, 255), lw=3)
    c.ell(60, 100, 9, 9, STEEL, lw=2)
    c.line([(60, 154), (60, 190)], (60, 46, 30, 255), 6)
    c.save("task_villa_reel.png")


# ------------------------------------------------------------------ Sign the Call Sheet (timecard)

def villa_callsheet():
    c = like("task_timecard.png")
    c.rrect(6, 6, 124, 194, 4, CREAM, lw=4, sh=(0.05, 0.12))
    c.d.rectangle([12 * S, 12 * S, 118 * S, 34 * S], fill=(60, 50, 90, 255))
    label(c, 65, 23, "CALL SHEET", 9, CREAM)
    for k in range(6):
        c.line([(16, 96 + k * 14), (114, 96 + k * 14)], (120, 110, 100, 255), 2)
    c.d.rectangle([16 * S, 170 * S, 114 * S, 186 * S], fill=(236, 230, 210, 255))
    c.line([(20, 182), (60, 176), (90, 184)], (40, 60, 160, 255), 2)
    c.save("task_villa_callsheet.png")
    c = like("task_clock.png")                                              # Taschenuhr des Regisseurs
    c.ell(150, 150, 140, 140, BRASS, lw=6, sh=(0.2, 0.3))
    c.ell(150, 150, 118, 118, CREAM, lw=5)
    for k in range(12):
        a = math.pi * 2 * k / 12
        r0 = 100 if k % 3 == 0 else 108
        c.line([(150 + r0 * math.cos(a), 150 + r0 * math.sin(a)), (150 + 114 * math.cos(a), 150 + 114 * math.sin(a))], INK, 4 if k % 3 == 0 else 2)
    label(c, 150, 60, "XII", 18, INK)
    label(c, 150, 200, "ACTION", 10, (160, 40, 40, 255))
    c.ell(150, 150, 8, 8, BRASS_D, lw=3)
    c.rrect(136, 2, 164, 26, 6, BRASS_D, lw=4)
    c.save("task_villa_watch.png")


# ------------------------------------------------------------------ Take Out the Trash (bins)

def villa_bins():
    for key, text, col in (("paper", "SCRIPTS", (90, 70, 50, 255)), ("glass", "BOTTLES", (60, 90, 70, 255)), ("rest", "PROPS", (60, 60, 70, 255))):
        c = like("task_bin_paper.png")
        c.rrect(16, 40, 154, 190, 8, col, lw=5, sh=(0.12, 0.22), shx=(0.1, 0.12))
        c.rrect(10, 24, 160, 48, 6, dark(col, 0.85), lw=5, sh=(0.15, 0.2))
        c.d.rectangle([30 * S, 110 * S, 140 * S, 130 * S], fill=GAFFER)
        label(c, 85, 120, text, 11, INK)
        c.save(f"task_villa_bin_{key}.png")
    items = {
        "brochure": lambda c: (c.rrect(18, 14, 78, 82, 3, CREAM, lw=4, sh=(0.05, 0.1)), [c.line([(26, 30 + k * 12), (70, 30 + k * 12)], (110, 100, 90, 255), 2) for k in range(4)], label(c, 48, 22, "SCRIPT", 7, INK)),
        "ticket": lambda c: (c.poly([(12, 30), (84, 30), (84, 66), (12, 66)], (32, 34, 42, 255), lw=4), [c.d.polygon([((16 + k * 18) * S, 14 * S), ((30 + k * 18) * S, 14 * S), ((36 + k * 18) * S, 30 * S), ((22 + k * 18) * S, 30 * S)], fill=(240, 240, 240, 255) if k % 2 == 0 else (24, 24, 28, 255)) for k in range(4)], c.line([(20, 46), (76, 46)], (200, 200, 208, 255), 2)),
        "bottle": lambda c: (c.rrect(32, 28, 64, 88, 8, BLOOD, lw=4, sh=(0.1, 0.2)), c.rrect(40, 8, 56, 32, 4, (60, 40, 30, 255), lw=3), c.d.rectangle([36 * S, 50 * S, 60 * S, 66 * S], fill=CREAM), label(c, 48, 58, "BLOOD", 6, INK)),
        "jar": lambda c: (c.rrect(20, 30, 76, 86, 10, (230, 200, 210, 255), lw=4, sh=(0.1, 0.2)), c.rrect(18, 18, 78, 36, 6, (60, 40, 50, 255), lw=4), label(c, 48, 62, "ROUGE", 7, INK)),
        "wrapper": lambda c: (c.ell(48, 48, 34, 34, GAFFER, lw=4, sh=(0.1, 0.2)), c.ell(48, 48, 14, 14, (90, 80, 40, 255), lw=3), c.line([(48, 14), (82, 48)], (200, 164, 40, 255), 2)),
        "apple": lambda c: (c.ell(48, 50, 32, 28, (200, 140, 90, 255), lw=4, sh=(0.1, 0.2)), c.ell(48, 50, 10, 9, (230, 200, 210, 255), lw=3), [c.d.ellipse([(30 + k * 9) * S - 2, (36 + (k % 2) * 20) * S - 2, (30 + k * 9) * S + 2, (36 + (k % 2) * 20) * S + 2], fill=(230, 80, 120, 255)) for k in range(5)]),
    }
    for name, fn in items.items():
        c = like("task_trash_bottle.png")
        fn(c)
        c.save(f"task_villa_trash_{name}.png")
    c = like("task_container.png")                                          # Crew-Container
    c.rrect(30, 70, 330, 290, 10, (74, 90, 106, 255), lw=6, sh=(0.12, 0.22), shx=(0.1, 0.14))
    c.rrect(20, 40, 340, 78, 8, (90, 108, 126, 255), lw=6, sh=(0.15, 0.2))
    for x in range(50, 320, 40):
        c.line([(x, 90), (x, 270)], (60, 74, 88, 255), 4)
    c.d.rectangle([90 * S, 150 * S, 270 * S, 176 * S], fill=GAFFER)
    label(c, 180, 163, "SET WASTE", 14, INK)
    c.save("task_villa_container.png")


# ------------------------------------------------------------------ Route Generator Power, Set Lights Down

def villa_route():
    c = like("task_socket.png")
    c.ell(42, 42, 36, 36, CREW, lw=5, sh=(0.15, 0.25))
    c.ell(42, 42, 22, 22, CREW_D, lw=4)
    c.ell(34, 42, 5, 5, STEEL, lw=0); c.ell(50, 42, 5, 5, STEEL, lw=0)
    c.d.rectangle([24 * S, 72 * S, 60 * S, 80 * S], fill=GAFFER)
    c.save("task_villa_socket.png")
    c = like("task_plug.png")
    c.rrect(12, 14, 78, 60, 10, CREW_L, lw=5, sh=(0.12, 0.2))
    c.ell(30, 36, 6, 6, STEEL, lw=0); c.ell(60, 36, 6, 6, STEEL, lw=0)
    c.line([(45, 60), (45, 68)], CREW_D, 8)
    c.save("task_villa_plug.png")
    c = like("task_switch_plate.png")                                       # Porzellanschalter
    c.rrect(10, 10, 170, 270, 14, PORC, lw=5, sh=(0.08, 0.18))
    c.ell(90, 140, 54, 60, PORC_D, lw=4)
    c.ell(90, 140, 36, 42, PORC, lw=3)
    c.rivet(26, 26, 5, BRASS); c.rivet(154, 26, 5, BRASS); c.rivet(26, 254, 5, BRASS); c.rivet(154, 254, 5, BRASS)
    label(c, 90, 246, "ON", 12, (90, 110, 80, 255))
    label(c, 90, 36, "OFF", 12, (140, 60, 60, 255))
    c.save("task_villa_switchplate.png")
    c = like("task_switch_lever.png")                                       # Messinghebel, Drehpunkt unten (y 140)
    c.capsule((30, 140), (30, 24), 18, BRASS, lw=4)
    c.ell(30, 24, 14, 14, BRASS_L, lw=4)
    c.ell(30, 140, 10, 10, BRASS_D, lw=3)
    c.save("task_villa_switchlever.png")


def villa_fuses():
    for name, col, glow in (("task_villa_fuse_ok.png", PORC, (190, 255, 120, 100)), ("task_villa_fuse_dead.png", (120, 110, 100, 255), None),
                            ("task_villa_fuse_new.png", (240, 236, 226, 255), None)):
        c = like("task_fuse_ok.png")
        c.rrect(18, 12, 46, 88, 8, col, lw=4, sh=(0.1, 0.22))
        c.rrect(10, 4, 54, 16, 4, BRASS, lw=3)
        c.rrect(10, 84, 54, 96, 4, BRASS, lw=3)
        c.ell(32, 50, 7, 7, (90, 60, 40, 255) if "dead" in name else (90, 160, 80, 255), lw=3)
        if "dead" in name:
            c.line([(22, 30), (42, 72)], (40, 30, 30, 255), 3)
            c.line([(42, 30), (22, 72)], (40, 30, 30, 255), 3)
        if glow:
            c.glow(32, 50, 16, 20, glow, 8)
        c.save(name)


# ------------------------------------------------------------------ Open the Puzzle Box (hiero)

def villa_puzzle():
    c = like("task_cartouche.png")
    c.rrect(6, 6, 114, 144, 8, (148, 104, 62, 255), lw=5, sh=(0.12, 0.22))
    c.rrect(16, 16, 104, 134, 5, (120, 82, 48, 255), lw=3)
    for y in (30, 120):
        c.line([(22, y), (98, y)], BRASS, 3)
    for x, y in ((22, 22), (98, 22), (22, 128), (98, 128)):
        c.d.polygon([(x * S, (y - 6) * S), ((x + 6) * S, y * S), (x * S, (y + 6) * S), ((x - 6) * S, y * S)], fill=BRASS_L)
    c.save("task_villa_tile.png")
    # Runen als Strichzeichen (Schriften ohne Runenblock zeichnen sonst Platzhalterkaesten)
    runes = [
        [[(22, 72), (22, 8), (58, 22)], [(22, 36), (58, 50)]],                      # F
        [[(22, 72), (22, 8), (58, 30), (58, 72)]],                                   # U
        [[(22, 72), (22, 8)], [(22, 20), (56, 40), (22, 60)]],                       # TH
        [[(22, 72), (22, 8), (58, 28)], [(22, 36), (58, 56)]],                       # A
        [[(22, 72), (22, 8), (56, 24), (26, 42), (58, 72)]],                         # R
        [[(58, 10), (24, 40), (58, 70)]],                                            # K
        [[(14, 12), (66, 68)], [(66, 12), (14, 68)]],                                # G
        [[(22, 72), (22, 8), (58, 24), (22, 42)]],                                   # W
        [[(22, 72), (22, 8)], [(58, 72), (58, 8)], [(22, 28), (58, 52)]],           # H
        [[(40, 72), (40, 8)], [(16, 54), (64, 26)]],                                 # N
    ]
    for k in range(10):
        c = like("task_glyph0.png")
        for pts in runes[k]:
            c.line(pts, INK, 11)
            c.line(pts, BRASS_L, 6)
        c.save(f"task_villa_rune{k}.png")


# ------------------------------------------------------------------ Smoke in the Chimney (waterworks)

def villa_pipes():
    c = like("task_pipes.png")
    # Kontrakt: Rohre auf y 150 und 330, Ventile zwischen x 130 und 610
    for y in (150, 330):
        c.capsule((60, y), (660, y), 34, COPPER, lw=5)
        c.line([(70, y - 8), (650, y - 8)], COPPER_L, 5)
        for x in (110, 630):
            c.rrect(x - 16, y - 26, x + 16, y + 26, 5, (120, 70, 40, 255), lw=4)
    c.capsule((360, 150), (360, 330), 30, COPPER, lw=5)
    c.rrect(320, 60, 400, 100, 6, (74, 44, 36, 255), lw=5)                  # Kaminansatz
    for x in range(322, 400, 20):
        c.line([(x, 62), (x, 98)], (100, 60, 46, 255), 3)
    c.save("task_villa_pipes.png")
    c = like("task_valve.png")                                              # Klappenrad
    c.ell(80, 80, 66, 66, (0, 0, 0, 0), lw=14, outline=INK)
    c.ell(80, 80, 66, 66, (0, 0, 0, 0), lw=8, outline=(70, 72, 80, 255))
    for k in range(6):
        a = math.pi * k / 3
        c.line([(80, 80), (80 + 62 * math.cos(a), 80 + 62 * math.sin(a))], INK, 12)
        c.line([(80, 80), (80 + 62 * math.cos(a), 80 + 62 * math.sin(a))], (90, 92, 100, 255), 7)
    c.ell(80, 80, 18, 18, (70, 72, 80, 255), lw=4)
    c.ell(80, 80, 7, 7, BRASS, lw=2)
    c.save("task_villa_wheel.png")
    c = like("task_card.png")                                               # Zettel mit Stellung
    c.rrect(8, 8, 212, 172, 6, CREAM, lw=4, sh=(0.05, 0.12))
    c.line([(20, 44), (200, 44)], (140, 130, 120, 255), 2)                   # Titel schreibt der Baustein (PLAN -> FLUE)
    c.save("task_villa_plan.png")


# ------------------------------------------------------------------ Set the Seance Table (spirit)

def spirit_board():
    c = C(720, 520)
    G.frame_wood(c, WALNUT_D)
    c.rrect(26, 26, 694, 494, 10, (190, 170, 124, 255), lw=5, sh=(0.1, 0.2))
    m, md = c.mask()
    md.rounded_rectangle([26 * S, 26 * S, 694 * S, 494 * S], 10 * S, fill=255)
    c.mottle(0.08, 14, seed=13, mask=m)
    c.grain(26, 26, 694, 494, 0.06, seed=6, freq=0.35, mask=m)
    c.vignette(0.3, 26, 26, 694, 494)
    ink = (40, 30, 26, 255)
    # Positionen wie SpiritMechanic: Einheiten -> Pixel (360 + x*100, 260 - y*100)
    P = lambda x, y: (360 + x * 100, 260 - y * 100)
    for i in range(13):
        label(c, *P(-2.7 + i * 0.45, 0.78), chr(ord("A") + i), 30, ink)
        label(c, *P(-2.7 + i * 0.45, 0.2), chr(ord("N") + i), 30, ink)
    for i in range(10):
        label(c, *P(-2.25 + i * 0.5, -0.42), "1234567890"[i], 24, ink)
    label(c, *P(-2.3, 1.5), "YES", 34, ink)
    label(c, *P(2.3, 1.5), "NO", 34, ink)
    label(c, *P(0, -1.15), "GOODBYE", 30, ink)
    label(c, *P(0, 1.5), "HOLLOWMERE", 18, (120, 60, 50, 255))
    # Sonne und Mond in den oberen Ecken
    c.ell(80, 90, 26, 26, (200, 160, 70, 255), lw=4)
    for k in range(12):
        a = math.pi * 2 * k / 12
        c.line([(80 + 30 * math.cos(a), 90 + 30 * math.sin(a)), (80 + 40 * math.cos(a), 90 + 40 * math.sin(a))], ink, 3)
    c.ell(640, 90, 26, 26, (220, 220, 230, 255), lw=4)
    c.ell(652, 84, 24, 24, (190, 170, 124, 255), lw=0)
    c.line([(60, 160), (660, 160)], ink, 2)
    c.line([(60, 390), (660, 390)], ink, 2)
    cobweb(c, 694, 26, 60, -1, 1)
    c.save("task_spirit_board.png")
    c = C(160, 170)                                                         # Planchette, Fenster bei (80, 95)
    c.poly([(80, 164), (14, 70), (40, 16), (80, 4), (120, 16), (146, 70)], (150, 106, 62, 255), lw=5, sh=(0.12, 0.2))
    c.ell(80, 95, 26, 26, (255, 250, 230, 150), lw=5)
    for x, y in ((40, 40), (120, 40), (80, 150)):
        c.ell(x, y, 7, 7, BRASS, lw=3)
    c.line([(30, 70), (56, 30)], (190, 150, 100, 255), 3)
    c.save("task_spirit_planchette.png")
    c = C(110, 110)
    c.glow(55, 55, 48, 48, (255, 255, 255, 255), 16)
    c.ell(55, 55, 22, 22, (255, 255, 255, 200), lw=0)
    c.save("task_spirit_glow.png")


def villa_icons():
    """Szenen-Symbole fuer Back Up the Dailies (statt der Museums-Exponate): Kerze, Schaedel, Fledermaus, Schluessel, Rabe."""
    def base():
        c = like("task_icon_dino.png")
        c.rrect(6, 6, 104, 104, 14, (32, 34, 42, 255), lw=5, sh=(0.12, 0.2))
        c.rrect(14, 14, 96, 96, 10, BORDEAUX, lw=3)
        return c
    c = base()
    c.rrect(48, 44, 62, 86, 4, CREAM, lw=3)
    c.poly([(55, 42), (61, 30), (55, 16), (49, 30)], (255, 180, 60, 255), lw=3, outline=(160, 90, 20, 255))
    c.save("task_villa_icon_candle.png")
    c = base()
    c.ell(55, 50, 26, 28, PORC, lw=4)
    c.rrect(40, 70, 70, 90, 4, PORC, lw=3)
    c.ell(45, 48, 7, 8, INK, lw=0); c.ell(65, 48, 7, 8, INK, lw=0)
    c.poly([(55, 60), (51, 68), (59, 68)], INK, lw=0)
    c.save("task_villa_icon_skull.png")
    c = base()
    c.poly([(55, 48), (40, 34), (18, 42), (26, 56), (16, 70), (36, 64), (55, 76), (74, 64), (94, 70), (84, 56), (92, 42), (70, 34)], (18, 18, 24, 255), lw=4)
    c.ell(55, 50, 8, 7, (30, 30, 38, 255), lw=3)
    c.save("task_villa_icon_bat.png")
    c = base()
    c.ell(40, 42, 16, 16, BRASS, lw=4)
    c.ell(40, 42, 6, 6, BORDEAUX, lw=2)
    c.line([(52, 50), (84, 82)], BRASS, 9)
    c.line([(74, 72), (82, 64)], BRASS, 7); c.line([(66, 80), (74, 72)], BRASS, 7)
    c.save("task_villa_icon_key.png")
    c = base()
    c.ell(55, 60, 22, 16, (18, 18, 24, 255), lw=4)
    c.ell(70, 46, 11, 10, (18, 18, 24, 255), lw=3)
    c.poly([(80, 46), (94, 44), (80, 40)], (140, 140, 48, 255), lw=2)
    c.ell(73, 44, 2, 2, RED, lw=0)
    c.line([(40, 70), (30, 84)], (18, 18, 24, 255), 5)
    c.save("task_villa_icon_raven.png")


def main():
    villa_icons()
    OUT.mkdir(parents=True, exist_ok=True)
    villa_panel(); villa_machine()
    villa_flue(); villa_soot(); villa_brush()
    villa_window(); villa_bat(); villa_broom(); villa_openwindow()
    villa_chapel(); villa_candles()
    villa_gauge(); villa_generator(); villa_drum(); villa_jerrycan()
    villa_starcard(); villa_sky("task_villa_sky.png"); villa_sky("task_villa_moonsky.png", moon=True)
    villa_vial(); villa_reelcan(); villa_callsheet(); villa_bins(); villa_route(); villa_fuses(); villa_puzzle(); villa_pipes()
    spirit_board()


if __name__ == "__main__":
    main()
