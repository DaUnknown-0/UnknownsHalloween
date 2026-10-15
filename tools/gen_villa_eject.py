# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_villa_eject.py - Grafik der Rauswurf-Szenen auf Hollowmere Manor -> Resources/villa/villa_eject_*.png|jpg
#
# Konventionen wie UnknownsAtlas/tools/gen_eject.py: gezeichnet in 100 px pro Szenen-Einheit mit 3x
# Supersampling, exportiert mit K = 1,8 (180 px pro Einheit). Hintergruende 12 x 6,8 Einheiten, deckend,
# JPG; alles andere PNG mit Alpha. Die Regie (villa_eject.py) nennt die Dateien flach, das Spiel laedt sie
# als eingebettete Ressourcen UnknownsHalloween.Resources.<datei>.
#
# Stil: Villa-Stilblatt (villa_art.py), aber duesterer und kaelter: entsaettigte Bordeaux- und Nussholz-
# Toene, Kerzen und Scheinwerfer als warme Inseln, Mondlicht und Wetterleuchten. Umrisse zittern leicht
# (handdraw.wobble/ink), Flaechen flach mit Licht- und Schattenkante.
#
#     python tools/gen_villa_eject.py            alle Dateien
#     python tools/gen_villa_eject.py --common   zusaetzlich task_eject_vignette.png und task_eject_px.png,
#                                                die Villa/EjectEngine.cs fuer Vignette, Blitz und Kinobalken
#                                                unter denselben Namen wie Atlas erwartet

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ATLAS_TOOLS = HERE.parent.parent / "UnknownsAtlas" / "tools"
sys.path.insert(0, str(ATLAS_TOOLS))
sys.path.insert(0, str(HERE))
from gen_tasks import C, S, light, font, label        # noqa: E402
from gen_eject import grad, rect, leaf                 # noqa: E402
import handdraw as HD                                  # noqa: E402

OUT = HERE.parent / "Resources" / "villa"
K = 1.8                                   # Export: 180 px pro Einheit
BW, BH = 1200, 680                        # Hintergrund 12 x 6,8 Einheiten
JPG_Q = 84

# ------------------------------------------------------------------ Palette (RGBA): kalt, entsaettigt
INK = (24, 22, 30, 255)
NIGHT, NIGHT_L = (14, 16, 28, 255), (36, 40, 62, 255)
WALL, WALL_M, WALL_D = (70, 36, 48, 255), (88, 48, 62, 255), (46, 24, 33, 255)
PLUM, PLUM_M, PLUM_D = (54, 34, 60, 255), (70, 46, 78, 255), (34, 22, 40, 255)
WAIN, WAIN_L, WAIN_D = (62, 44, 32, 255), (84, 62, 44, 255), (40, 28, 20, 255)
FLOOR, FLOOR_D = (64, 46, 33, 255), (40, 29, 22, 255)
STONE, STONE_D, STONE_L = (104, 106, 108, 255), (68, 70, 74, 255), (132, 134, 136, 255)
BRASS, BRASS_L, BRASS_D = (172, 136, 72, 255), (224, 194, 112, 255), (112, 86, 42, 255)
MATTE, MATTE_L, MATTE_D = (44, 44, 52, 255), (72, 74, 84, 255), (26, 26, 32, 255)
STEEL = (132, 136, 146, 255)
GAFFER = (226, 190, 58, 255)
CREAM, CREAM_D = (226, 216, 190, 255), (182, 170, 144, 255)
WARM = (255, 205, 130, 255)
MOON = (184, 204, 228, 255)
PURPLE = (160, 122, 255, 255)
FLAME, FLAME_CORE = (255, 176, 60, 255), (255, 244, 200, 255)
GRASS, GRASS_L, EARTH, EARTH_D = (46, 58, 40, 255), (74, 92, 58, 255), (54, 44, 36, 255), (34, 28, 24, 255)
VELVET, VELVET_D, VELVET_L = (96, 28, 40, 255), (62, 18, 28, 255), (124, 44, 58, 255)
WOOD, WOOD_D = (122, 88, 56, 255), (84, 58, 36, 255)
CHALK = (232, 230, 220, 255)
CREW = {"blue": ((38, 62, 196, 255), (22, 32, 120, 255)), "orange": ((228, 126, 28, 255), (164, 66, 22, 255))}


def a4(col, a):
    return tuple(col[:3]) + (a,)


def ux(x):
    return BW / 2 + x * 100


def uy(y):
    return BH / 2 - y * 100


# ------------------------------------------------------------------ Hand-gezeichnete Grundformen (Pixel)

def wob(pts, seed=0, amp=1.3, closed=True, step=9):
    return HD.wobble(list(pts), amp=amp, seed=seed, step=step, closed=closed)


def hpoly(c, pts, fill, lw=5, outline=INK, seed=0, amp=1.3, sh=None):
    """Polygon mit zitternder Kontur und leicht schwankender Strichstaerke."""
    p = wob(pts, seed, amp, True)
    pp = c.P(p)
    if fill is not None:
        c.d.polygon(pp, fill=fill)
        if sh:
            m, md = c.mask()
            md.polygon(pp, fill=255)
            c.shade(m, *sh)
    if lw:
        HD.ink(c.d, pp, outline, lw * S, seed=seed, var=0.22, closed=True)


def hrect(c, x0, y0, x1, y1, fill, **kw):
    hpoly(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, **kw)


def ell_pts(cx, cy, rx, ry, n=None, a0=0.0, a1=math.tau):
    n = n or max(16, int((rx + ry) * math.pi / 8))
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def hell(c, cx, cy, rx, ry, fill, **kw):
    hpoly(c, ell_pts(cx, cy, rx, ry)[:-1], fill, **kw)


def rr_pts(x0, y0, x1, y1, r):
    """Rechteck mit runden Ecken als Polygon; r = Radius oder (oben, unten)."""
    rt, rb = (r, r) if not isinstance(r, tuple) else r
    rt = min(rt, (x1 - x0) / 2, (y1 - y0) / 2)
    rb = min(rb, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = []
    for (cx, cy, a0, rr) in ((x1 - rt, y0 + rt, -90, rt), (x1 - rb, y1 - rb, 0, rb), (x0 + rb, y1 - rb, 90, rb), (x0 + rt, y0 + rt, 180, rt)):
        for k in range(7):
            a = math.radians(a0 + 90 * k / 6)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def hrr(c, x0, y0, x1, y1, r, fill, **kw):
    hpoly(c, rr_pts(x0, y0, x1, y1, r), fill, **kw)


def hline(c, pts, fill, w, seed=0, amp=1.0, var=0.2):
    p = wob(pts, seed, amp, closed=False)
    HD.ink(c.d, c.P(p), fill, max(1, w * S), seed=seed, var=var)


def apoly(c, pts, fill):
    """Halbtransparentes Polygon, echt ueberblendet (ImageDraw ersetzt sonst die Pixel)."""
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon(c.P(pts), fill=fill)
    c.img.alpha_composite(g)
    c.d = ImageDraw.Draw(c.img)


def aline(c, pts, fill, w):
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).line(c.P(pts), fill=fill, width=int(w * S), joint="curve")
    c.img.alpha_composite(g)
    c.d = ImageDraw.Draw(c.img)


def grad_rect(c, x0, y0, x1, y1, top, bottom):
    """Vertikaler Verlauf nur im Rechteck (Zielpixel)."""
    X0, Y0, X1, Y1 = int(x0 * S), int(y0 * S), int(x1 * S), int(y1 * S)
    h = max(1, Y1 - Y0)
    t = (np.arange(h, dtype=np.float32) / max(1, h - 1))[:, None, None]
    a, b = np.array(top[:3], np.float32), np.array(bottom[:3], np.float32)
    band = (a * (1 - t) + b * t)
    arr = np.asarray(c.img).astype(np.float32)
    arr[Y0:Y1, X0:X1, :3] = band
    arr[Y0:Y1, X0:X1, 3] = 255
    c.img = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
    c.d = ImageDraw.Draw(c.img)


def blur(c, r):
    c.img = c.img.filter(ImageFilter.GaussianBlur(r * S))
    c.d = ImageDraw.Draw(c.img)


def save(c, name):
    img = c.img.resize((round(c.w * K), round(c.h * K)), Image.LANCZOS)
    img.save(OUT / name, optimize=True)
    print(f"  {name} {img.size[0]}x{img.size[1]} {(OUT / name).stat().st_size // 1024} KB")


def save_bg(c, name):
    img = c.img.resize((round(c.w * K), round(c.h * K)), Image.LANCZOS).convert("RGB")
    img = HD.paper_grain(img, amount=0.035, seed=11, scale=2)
    img.save(OUT / name, "JPEG", quality=JPG_Q, optimize=True, progressive=True)
    print(f"  {name} {img.size[0]}x{img.size[1]} {(OUT / name).stat().st_size // 1024} KB")


def radial(size, stops, name, squash=1.0):
    n = size * S
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.sqrt(((xx - n / 2) / (n / 2)) ** 2 + ((yy - n / 2) / (n / 2 * squash)) ** 2)
    rs, as_ = zip(*stops)
    a = np.interp(r, rs, as_)
    img = np.zeros((n, n, 4), np.uint8)
    img[..., :3] = 255
    img[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(img, "RGBA").resize((round(size * K), round(size * K)), Image.LANCZOS)
    im.save(OUT / name, optimize=True)
    print(f"  {name} {im.size[0]}x{im.size[1]}")


# ------------------------------------------------------------------ Figuren

def crew(c, x, y, h, col, col_d, flip=1, seed=0, visor=(150, 200, 225, 255)):
    """Crewmate wie im Vorschau-Kino: Koerper h px hoch, (x, y) = Koerpermitte, Blick nach rechts."""
    lw = max(3, h * 0.045)

    def R(u0, v0, w, hh, r):
        xa, xb = x + flip * u0 * h, x + flip * (u0 + w) * h
        return rr_pts(min(xa, xb), y - (v0 + hh) * h, max(xa, xb), y - v0 * h, r * h if not isinstance(r, tuple) else (r[0] * h, r[1] * h))

    hpoly(c, R(-0.46, -0.2, 0.2, 0.44, 0.09), col_d, lw, seed=seed + 1, sh=(0.1, 0.2))
    hpoly(c, R(-0.28, -0.5, 0.2, 0.3, 0.08), col_d, lw, seed=seed + 2)
    hpoly(c, R(0.08, -0.5, 0.2, 0.3, 0.08), col, lw, seed=seed + 3, sh=(0.05, 0.25))
    hpoly(c, R(-0.33, -0.34, 0.66, 0.84, (0.33, 0.12)), col, lw, seed=seed + 4, sh=(0.14, 0.24))
    hpoly(c, R(0.0, 0.1, 0.42, 0.24, 0.12), visor, lw * 0.9, seed=seed + 5, sh=(0.1, 0.25))
    c.d.polygon(c.P(R(0.1, 0.23, 0.2, 0.06, 0.03)), fill=(255, 255, 255, 215))


def candle_px(c, x, y, h, r=10, seed=0, lit=False):
    """Kerze mit Standpunkt (x, y) unten, h hoch; Flamme kommt als Sprite (lit nur fuer Hintergruende)."""
    hrect(c, x - r, y - h, x + r, y, CREAM, lw=3, seed=seed, sh=(0.1, 0.2))
    hell(c, x, y - h, r, r * 0.4, light(CREAM, 0.1), lw=3, seed=seed + 1)
    c.line([(x - r * 0.6, y - h + 4), (x - r * 0.6, y - h * 0.5)], light(CREAM, 0.2), 2)
    c.line([(x, y - h), (x, y - h - 5)], INK, 2)
    if lit:
        flame_px(c, x, y - h - 4, 1.0)


def flame_px(c, x, y, s=1.0, glow=True):
    if glow:
        c.glow(x, y - 8 * s, 26 * s, 30 * s, a4(WARM, 90), 10 * s)
    hpoly(c, [(x - 7 * s, y), (x + 7 * s, y), (x + 5 * s, y - 12 * s), (x, y - 26 * s), (x - 5 * s, y - 12 * s)], FLAME, lw=2,
          outline=(170, 90, 30, 255), seed=5, amp=0.8)
    c.d.polygon(c.P([(x - 3 * s, y - 2), (x + 3 * s, y - 2), (x, y - 13 * s)]), fill=FLAME_CORE)


def cobweb_px(c, x, y, size, qx, qy, seed=0):
    rnd = random.Random(seed)
    col = (225, 230, 240, 70)
    n = 5
    for k in range(n + 1):
        a = (math.pi / 2) * k / n
        aline(c, [(x, y), (x + qx * size * math.cos(a), y + qy * size * math.sin(a))], col, 1.5)
    for r in (0.3, 0.55, 0.8, 1.0):
        pts = []
        for k in range(n + 1):
            a = (math.pi / 2) * k / n
            rr = r * size * rnd.uniform(0.86, 1.0)
            pts.append((x + qx * rr * math.cos(a), y + qy * rr * math.sin(a)))
        aline(c, pts, col, 1.2)


def cable(c, pts, seed=0, w=4):
    p = wob(pts, seed, amp=3, closed=False, step=14)
    aline(c, p, (0, 0, 0, 70), w * 1.8)
    c.line(p, MATTE_D, w)
    aline(c, p, a4(STEEL, 90), w * 0.3)


def gaffer(c, x0, y0, x1, y1, w=6):
    c.line([(x0, y0), (x1, y1)], GAFFER, w)
    aline(c, [(x0, y0), (x1, y1)], a4((160, 130, 30), 120), w * 0.25)


# ------------------------------------------------------------------ Innenraum-Grundlage

def damask(c, x0, y0, x1, y1, motif, seed=1):
    rnd = random.Random(seed)
    row = 0
    y = y0 + 20
    while y < y1:
        x = x0 + (40 if row % 2 else 5)
        while x < x1:
            k = rnd.uniform(0.9, 1.1)
            pts = [(x, y - 16 * k), (x + 7 * k, y - 5 * k), (x + 12 * k, y + 2 * k), (x + 5 * k, y + 9 * k), (x, y + 17 * k),
                   (x - 5 * k, y + 9 * k), (x - 12 * k, y + 2 * k), (x - 7 * k, y - 5 * k)]
            apoly(c, wob(pts, seed + int(x) + int(y), amp=0.9, step=7), motif)
            c.d.polygon(c.P([(x, y - 7 * k), (x + 4 * k, y + 1 * k), (x, y + 8 * k), (x - 4 * k, y + 1 * k)]), fill=a4(motif, 255))
            x += 70
        y += 46
        row += 1


def interior(c, seed=1, wall=WALL, motif=WALL_M, wall_d=WALL_D, wain_top=330, floor=465):
    grad(c, light(wall, 0.04), wall_d, 0, wain_top)
    damask(c, 0, 44, BW, wain_top, a4(motif, 150), seed)
    hrect(c, -10, 16, BW + 10, 44, WAIN_D, lw=4, seed=seed)                        # Gesims
    c.line([(0, 44), (BW, 44)], a4(WAIN_L, 140), 2)
    hrect(c, -10, wain_top, BW + 10, floor, WAIN, lw=4, seed=seed + 1)             # Vertaefelung
    c.line([(0, wain_top + 4), (BW, wain_top + 4)], WAIN_L, 4)
    for i, x in enumerate(range(-40 + (seed * 37) % 80, BW + 60, 150)):
        hrect(c, x + 14, wain_top + 24, x + 136, floor - 32, WAIN_D, lw=3, seed=seed + 10 + i)
        hrect(c, x + 26, wain_top + 36, x + 124, floor - 44, WAIN, lw=2, seed=seed + 20 + i)
        c.line([(x + 26, wain_top + 36), (x + 124, wain_top + 36)], a4(WAIN_L, 150), 2)
    rect(c, 0, floor - 16, BW, floor, WAIN_D)                                         # Fussleiste
    c.line([(0, floor - 16), (BW, floor - 16)], a4(WAIN_L, 120), 2)
    grad(c, FLOOR, FLOOR_D, floor, BH)                                                # Dielen
    rnd = random.Random(seed)
    y, row = floor, 0
    while y < BH + 40:
        h = 32 + row * 5
        c.line([(0, y), (BW, y)], a4(FLOOR_D, 220), 2)
        x = -rnd.uniform(0, 300)
        while x < BW:
            w = rnd.uniform(200, 380)
            c.line([(x + w, y + 2), (x + w, y + h - 2)], a4(FLOOR_D, 220), 2)
            x += w
        y += h
        row += 1
    c.grain(0, floor, BW, BH, amount=0.05, seed=seed, freq=0.5)
    cobweb_px(c, 0, 44, 95, 1, 1, seed)
    cobweb_px(c, BW, 44, 70, -1, 1, seed + 1)
    c.mottle(0.05, cell=14, seed=seed)


def frame_portrait(c, cx, cy, rx, ry, seed=0, eyes_open=False):
    """Ovales Portraet im Goldrahmen: ein Crewmate als alter Meister, Visier dunkel, Augen geschlossen."""
    hell(c, cx, cy, rx + 14, ry + 14, BRASS_D, lw=5, seed=seed)
    hell(c, cx, cy, rx + 6, ry + 6, BRASS, lw=0, seed=seed + 1, sh=(0.2, 0.35))
    hell(c, cx, cy, rx, ry, (36, 30, 34, 255), lw=4, seed=seed + 2)
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=255)
    mask = g.split()[3]
    tmp = C(c.w, c.h)
    tmp.d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=(44, 36, 40, 255))
    crew(tmp, cx - rx * 0.1, cy + ry * 0.25, ry * 1.25, (58, 50, 60, 255), (40, 34, 42, 255), seed=seed + 3, visor=(56, 60, 72, 255))
    hpoly(tmp, [(cx - rx * 0.5, cy + ry * 0.05), (cx + rx * 0.45, cy + ry * 0.05), (cx + rx * 0.35, cy + ry * 0.28), (cx - rx * 0.4, cy + ry * 0.28)],
          CREAM_D, lw=3, seed=seed + 4)                                           # Halskrause
    tmp.d.line(tmp.P([(cx + rx * 0.05, cy - ry * 0.28), (cx + rx * 0.4, cy - ry * 0.28)]), fill=(90, 96, 110, 255), width=3 * S)
    tmp.glow(cx + rx * 0.15, cy - ry * 0.5, rx * 0.8, ry * 0.5, (120, 100, 90, 60), 20)
    c.img.paste(tmp.img, (0, 0), mask)
    c.d = ImageDraw.Draw(c.img)
    hell(c, cx, cy, rx, ry, None, lw=4, seed=seed + 2)


def candelabra_px(c, cx, floor, seed=0):
    """Bodenkandelaber aus Messing, drei Kerzen ohne Flammen (Flammen sind Sprites)."""
    hell(c, cx, floor - 6, 34, 14, BRASS_D, lw=4, seed=seed)
    hell(c, cx, floor - 8, 20, 9, BRASS, lw=3, seed=seed + 1)
    top = floor - 170
    hline(c, [(cx, floor - 10), (cx, top)], INK, 10, seed=seed)
    hline(c, [(cx, floor - 10), (cx, top)], BRASS, 6, seed=seed)
    for z in (50, 100):
        hell(c, cx, floor - z, 7, 5, BRASS, lw=3, seed=seed + z)
    arms = [(cx, top - 10)]
    for sx in (-1, 1):
        pts = [(cx, top), (cx + sx * 10, top - 4), (cx + sx * 20, top + 4), (cx + sx * 22, top + 10)]
        hline(c, pts, INK, 7, seed=seed + 5)
        hline(c, pts, BRASS, 4, seed=seed + 5)
        arms.append((cx + sx * 22, top + 8))
    for k, (ax, ay) in enumerate(arms):
        hell(c, ax, ay, 9, 4, BRASS, lw=3, seed=seed + k)
        candle_px(c, ax, ay, 16 if k == 0 else 12, r=5, seed=seed + k)


# ================================================================== Gemeinsame Sprites

def common(extra=False):
    radial(128, [(0, 1), (0.35, 0.55), (1, 0)], "villa_eject_glow.png")
    radial(24, [(0, 1), (0.5, 0.6), (1, 0)], "villa_eject_mote.png")

    c = C(120, 120)                                                                           # Staub-/Rauchballen
    rnd = random.Random(5)
    for _ in range(14):
        x, y, r = rnd.uniform(35, 85), rnd.uniform(38, 82), rnd.uniform(16, 30)
        c.ell(x, y, r, r * 0.85, (255, 255, 255, 120), lw=0)
    blur(c, 6)
    save(c, "villa_eject_puff.png")

    c = C(400, 120)                                                                           # Nebelschwade
    rnd = random.Random(6)
    for _ in range(26):
        x, y = rnd.uniform(40, 360), rnd.uniform(45, 75)
        c.ell(x, y, rnd.uniform(30, 70), rnd.uniform(14, 28), (255, 255, 255, 70), lw=0)
    blur(c, 10)
    save(c, "villa_eject_mist.png")

    c = C(300, 130)                                                                           # Wolke
    rnd = random.Random(8)
    for _ in range(18):
        x, y = rnd.uniform(50, 250), rnd.uniform(45, 85)
        c.ell(x, y, rnd.uniform(35, 70), rnd.uniform(22, 40), (255, 255, 255, 150), lw=0)
    blur(c, 7)
    save(c, "villa_eject_cloud.png")

    c = C(8, 70)                                                                              # Regenstreifen
    for i in range(70):
        a = int(40 + 200 * (i / 69) ** 1.5)
        c.d.rectangle([2 * S, i * S, 6 * S, (i + 1) * S], fill=(255, 255, 255, a))
    save(c, "villa_eject_streak.png")

    c = C(24, 30)                                                                             # Tropfen
    c.d.polygon(c.P([(12, 2), (19, 16), (12, 28), (5, 16)]), fill=(255, 255, 255, 230))
    c.ell(12, 19, 7, 8, (255, 255, 255, 230), lw=0)
    c.glint(9, 16, 2, 3, 200)
    save(c, "villa_eject_droplet.png")

    c = C(120, 50)                                                                            # Ring
    c.d.ellipse([6 * S, 6 * S, 114 * S, 44 * S], outline=(255, 255, 255, 220), width=4 * S)
    save(c, "villa_eject_ripple.png")

    c = C(40, 20)                                                                             # Laub (welk)
    leaf(c, 3, 10, 34, 13, 0, (255, 255, 255, 255))
    c.line([(4, 10), (34, 10)], (190, 190, 190, 255), 1.5)
    save(c, "villa_eject_leaf.png")

    c = C(40, 64)                                                                             # Kerzenflamme
    c.glow(20, 38, 16, 24, (255, 150, 40, 150), 5)
    hpoly(c, [(20, 4), (30, 30), (32, 46), (20, 60), (8, 46), (10, 30)], FLAME, lw=2, outline=(170, 90, 30, 255), seed=1, amp=0.8)
    c.d.polygon(c.P([(20, 22), (26, 38), (26, 48), (20, 56), (14, 48), (14, 38)]), fill=FLAME_CORE)
    save(c, "villa_eject_flame.png")

    c = C(16, 16)                                                                             # Vollflaeche
    c.d.rectangle([0, 0, 16 * S, 16 * S], fill=(255, 255, 255, 255))
    save(c, "villa_eject_px.png")

    # Lichtkegel (Spitze links, Pivot 0 / 0,5)
    n_w, n_h = 360, 180
    yy, xx = np.mgrid[0:n_h * S, 0:n_w * S].astype(np.float32)
    u = xx / (n_w * S)
    half = 0.06 + 0.44 * u
    v = np.abs(yy / (n_h * S) - 0.5)
    edge = np.clip(1 - v / np.maximum(half, 1e-3), 0, 1) ** 0.7
    a = edge * (1 - u) ** 1.1 * 0.8
    img = np.zeros((n_h * S, n_w * S, 4), np.uint8)
    img[..., :3] = 255
    img[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img, "RGBA").resize((round(n_w * K), round(n_h * K)), Image.LANCZOS).save(OUT / "villa_eject_cone.png", optimize=True)
    print("  villa_eject_cone.png")

    c = C(200, 200)                                                                           # Strudel
    pts = []
    for k in range(260):
        t = k / 259
        a = t * math.tau * 2.6
        r = 6 + 88 * t
        pts.append((100 + r * math.cos(a), 100 + r * math.sin(a)))
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for k in range(len(pts) - 1):
        t = k / (len(pts) - 1)
        w = int((3 + 9 * (1 - t)) * S)
        gd.line([c.P([pts[k]])[0], c.P([pts[k + 1]])[0]], fill=(255, 255, 255, int(90 + 160 * (1 - t))), width=w)
    c.img.alpha_composite(g.filter(ImageFilter.GaussianBlur(2 * S)))
    c.img.alpha_composite(g)
    save(c, "villa_eject_swirl.png")

    c = C(70, 24)                                                                             # Augen (zwei Schlitze)
    for x in (18, 52):
        c.glow(x, 12, 14, 9, (200, 230, 255, 160), 4)
        hpoly(c, [(x - 12, 12), (x - 5, 6), (x + 5, 6), (x + 12, 12), (x + 5, 18), (x - 5, 18)], (240, 250, 255, 255), lw=0, seed=x, amp=0.6)
        c.ell(x, 12, 3, 4, (40, 60, 90, 255), lw=0)
    save(c, "villa_eject_eyes.png")

    c = C(130, 130)                                                                           # Schatten (Silhouette)
    crew(c, 62, 68, 100, (0, 0, 0, 255), (0, 0, 0, 255), seed=2, visor=(0, 0, 0, 255))
    blur(c, 5)
    save(c, "villa_eject_shadow.png")

    c = C(220, 400)                                                                           # Blitz
    rnd = random.Random(3)
    pts, x, y = [(110, 0)], 110, 0
    while y < 380:
        y += rnd.uniform(28, 55)
        x += rnd.uniform(-45, 45)
        pts.append((min(210, max(10, x)), y))
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).line(c.P(pts), fill=(170, 200, 255, 200), width=14 * S, joint="curve")
    c.img.alpha_composite(g.filter(ImageFilter.GaussianBlur(9 * S)))
    for i in range(2, len(pts) - 2, 3):                                                       # Nebenaeste
        bx, by = pts[i]
        side = rnd.choice((-1, 1))
        c.line([(bx, by), (bx + side * rnd.uniform(25, 55), by + rnd.uniform(20, 50)), (bx + side * rnd.uniform(40, 70), by + rnd.uniform(50, 90))],
               (235, 242, 255, 255), 2.5)
    c.line(pts, (240, 246, 255, 255), 4)
    c.d = ImageDraw.Draw(c.img)
    save(c, "villa_eject_bolt.png")

    if extra:
        n = 220
        yy, xx = np.mgrid[0:n * S, 0:n * S].astype(np.float32)
        r = np.sqrt(((xx - n * S / 2) / (n * S / 2)) ** 2 + ((yy - n * S / 2) / (n * S / 2)) ** 2) / math.sqrt(2)
        a = np.clip((r - 0.45) / 0.55, 0, 1) ** 1.6 * 0.85
        img = np.zeros((n * S, n * S, 4), np.uint8)
        img[..., 3] = (a * 255).astype(np.uint8)
        Image.fromarray(img, "RGBA").resize((round(n * K), round(n * K)), Image.LANCZOS).save(OUT / "task_eject_vignette.png", optimize=True)
        c = C(16, 16)
        c.d.rectangle([0, 0, 16 * S, 16 * S], fill=(255, 255, 255, 255))
        save(c, "task_eject_px.png")
        print("  task_eject_vignette.png")


# ================================================================== Szene 1: Aus dem Fenster

def window():
    c = C(BW, BH)
    interior(c, seed=1)
    WX, WY, WW, WH = ux(1.8), uy(1.0), 260, 300
    x0, y0, x1, y1 = WX - WW / 2, WY - WH / 2, WX + WW / 2, WY + WH / 2
    grad_rect(c, x0, y0, x1, y1, (46, 54, 84), (16, 18, 30))                                    # Sturmhimmel
    rnd = random.Random(4)
    for _ in range(9):                                                                        # Wolkenfetzen
        cx, cy = rnd.uniform(x0, x1), rnd.uniform(y0 + 20, y0 + 150)
        c.glow(cx, cy, rnd.uniform(40, 80), rnd.uniform(16, 30), (70, 78, 108, 110), 10)
    hills = [(x0 - 10, y1 + 10), (x0 - 10, y1 - 70), (x0 + 60, y1 - 95), (x0 + 130, y1 - 80), (x0 + 200, y1 - 110), (x1 + 10, y1 - 85), (x1 + 10, y1 + 10)]
    hpoly(c, hills, (12, 14, 22, 255), lw=0, seed=2, amp=2)
    for k, (tx, th) in enumerate(((x0 + 40, 60), (x0 + 95, 44), (x1 - 50, 70))):             # kahle Baeume
        hline(c, [(tx, y1 - 70), (tx + 4, y1 - 70 - th)], (10, 12, 18, 255), 4, seed=k)
        hline(c, [(tx + 2, y1 - 90 - th * 0.3), (tx - 16, y1 - 110 - th * 0.5)], (10, 12, 18, 255), 2.5, seed=k + 3)
        hline(c, [(tx + 3, y1 - 80 - th * 0.5), (tx + 20, y1 - 100 - th * 0.7)], (10, 12, 18, 255), 2.5, seed=k + 6)
    g = Image.new("RGBA", c.img.size, (0, 0, 0, 0))                                           # Regenschleier
    gd = ImageDraw.Draw(g)
    for _ in range(140):
        rx, ry = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        gd.line([(rx * S, ry * S), ((rx - 4) * S, (ry + 22) * S)], fill=(170, 190, 230, 60), width=S)
    c.img.alpha_composite(g)
    c.d = ImageDraw.Draw(c.img)
    hrect(c, x0 - 22, y0 - 22, x1 + 22, y1 + 6, None, lw=0)
    for (ax, ay, bx, by) in ((x0 - 22, y0 - 22, x0, y1), (x1, y0 - 22, x1 + 22, y1), (x0 - 22, y0 - 22, x1 + 22, y0)):
        hrect(c, ax, ay, bx, by, WAIN_D, lw=4, seed=int(ax))                                  # Laibung
    c.line([(x0 - 20, y0 - 20), (x1 + 20, y0 - 20)], a4(WAIN_L, 120), 2)
    hrect(c, x0 - 34, y1, x1 + 34, y1 + 18, STONE_D, lw=4, seed=9, sh=(0.2, 0.3))             # Sims
    for k in range(5):                                                                        # Regenwasser auf dem Sims
        c.ell(x0 + 20 + k * 55, y1 + 9, 10, 2, (120, 140, 170, 120), lw=0)
    # Wandkerze links: Messingarm und Kerze (Flamme als Sprite bei (-3,3 / 0,62))
    sx, sy = ux(-3.3), uy(0.62)
    hell(c, sx, sy + 55, 22, 9, BRASS_D, lw=3, seed=3)
    hline(c, [(sx, sy + 52), (sx, sy + 22)], INK, 8, seed=3)
    hline(c, [(sx, sy + 52), (sx, sy + 22)], BRASS, 5, seed=3)
    hell(c, sx, sy + 20, 11, 5, BRASS, lw=3, seed=4)
    candle_px(c, sx, sy + 18, 20, r=6, seed=4)
    c.glow(sx, sy + 70, 90, 40, (255, 200, 120, 40), 25)                                       # schwacher Schein auf der Wand
    c.vignette(0.55)
    save_bg(c, "villa_eject_window_bg.jpg")

    # Fensterfluegel (Angel links, 1,3 x 3,0)
    c = C(130, 300)
    hrect(c, 4, 4, 126, 296, WAIN_D, lw=5, seed=1, sh=(0.1, 0.2))
    for row in range(3):
        for col in range(2):
            gx0, gy0 = 16 + col * 52, 16 + row * 92
            c.d.rectangle([gx0 * S, gy0 * S, (gx0 + 46) * S, (gy0 + 84) * S], fill=(58, 70, 102, 140))
            hrect(c, gx0, gy0, gx0 + 46, gy0 + 84, None, lw=3, seed=row * 2 + col)
            c.d.line(c.P([(gx0 + 6, gy0 + 78), (gx0 + 40, gy0 + 8)]), fill=(200, 215, 240, 50), width=5 * S)
    for hy in (40, 260):                                                                      # Scharniere
        hrr(c, 0, hy - 10, 10, hy + 10, 3, BRASS_D, lw=2, seed=hy)
    hell(c, 112, 150, 5, 9, BRASS, lw=2, seed=7)                                              # Griff
    save(c, "villa_eject_shutter.png")

    # Vorhang (Pivot oben Mitte, 1,1 x 3,3)
    c = C(110, 330)
    hpoly(c, [(6, 6), (104, 6), (100, 324), (10, 324)], VELVET, lw=4, seed=2, sh=(0.08, 0.3))
    for k in range(6):
        fx = 14 + k * 16
        hline(c, [(fx, 10), (fx + 3, 320)], VELVET_D if k % 2 else VELVET_L, 5, seed=k, amp=2.5)
    hrect(c, 0, 0, 110, 10, BRASS_D, lw=3, seed=5)
    for k in range(4):
        hell(c, 14 + k * 27, 5, 5, 5, BRASS, lw=2, seed=k)
    hline(c, [(8, 200), (102, 214)], BRASS_D, 6, seed=9)                                      # Raffhalter
    save(c, "villa_eject_curtain.png")


# ================================================================== Szene 2: Der alte Brunnen

def cold_moon(c, x, y, r):
    c.glow(x, y, r * 4.5, r * 4.5, (140, 165, 215, 40), r * 1.6)
    c.glow(x, y, r * 1.8, r * 1.8, (205, 220, 245, 70), r * 0.6)
    hell(c, x, y, r, r, (222, 228, 236, 255), lw=0, seed=3, amp=0.6)
    for dx, dy, rr in ((0.3, -0.2, 0.22), (-0.35, 0.3, 0.15), (0.1, 0.45, 0.1), (-0.3, -0.35, 0.09)):
        c.ell(x + r * dx, y + r * dy, r * rr, r * rr, (200, 206, 216, 255), lw=0)


def bush_line(c, y, col, seed, x0=-20, x1=None, r=(28, 60)):
    rnd = random.Random(seed)
    x = x0
    x1 = c.w + 40 if x1 is None else x1
    while x < x1:
        rr = rnd.uniform(*r)
        hell(c, x, y - rr * 0.4, rr, rr * 0.9, col, lw=0, seed=int(x), amp=2)
        x += rr * rnd.uniform(0.6, 1.1)
    rect(c, 0, y, c.w, y + 40, col)


def well():
    c = C(BW, BH)
    grad(c, NIGHT, (30, 34, 54), 0, 320)
    rnd = random.Random(4)
    for _ in range(90):
        x, y, r = rnd.uniform(0, BW), rnd.uniform(0, 260), rnd.choice((0.8, 1, 1, 1.4))
        c.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(230, 236, 255, rnd.randint(90, 200)))
    cold_moon(c, ux(-3.4), uy(2.0), 46)
    bush_line(c, 300, (18, 24, 30, 255), 5, r=(40, 90))                                       # Hecken hinten
    bush_line(c, 318, (24, 32, 36, 255), 6, r=(26, 50))
    # Zaun aus Schmiedeeisen
    for x in range(-10, BW + 20, 24):
        hline(c, [(x, 330), (x, 262)], MATTE_D, 3.5, seed=x, amp=0.6)
        c.d.polygon(c.P([(x - 4, 266), (x + 4, 266), (x, 254)]), fill=MATTE_D)
    for yy in (276, 312):
        hline(c, [(-10, yy), (BW + 10, yy)], MATTE_D, 4, seed=yy, amp=0.8)
    # Boden
    grad(c, EARTH, EARTH_D, 330, BH)
    for _ in range(260):                                                                      # Gras
        x, y = rnd.uniform(0, BW), rnd.uniform(335, BH)
        for (a, b) in HD.tuft(x, y, rnd, n=3, h=14, spread=4):
            c.line([a, b], GRASS_L if rnd.random() < 0.3 else GRASS, 1.5)
    for _ in range(110):                                                                      # Laub
        x, y = rnd.uniform(0, BW), rnd.uniform(335, BH)
        leaf(c, x, y, rnd.uniform(9, 16), rnd.uniform(4, 7), rnd.uniform(0, 360), rnd.choice(((120, 70, 40, 255), (96, 60, 34, 255), (130, 90, 40, 255))))
    for (gx, gy, gw, gh, seed) in ((ux(-4.3), uy(-0.3), 44, 70, 1), (ux(4.1), uy(-0.1), 40, 62, 2), (ux(-5.2), uy(-1.4), 50, 50, 3)):    # Grabsteine
        hrect(c, gx - gw * 0.7, gy + gh, gx + gw * 0.7, gy + gh + 14, STONE_D, lw=4, seed=seed)
        hrr(c, gx - gw / 2, gy, gx + gw / 2, gy + gh + 4, (gw / 2, 4), STONE_D, lw=4, seed=seed + 5, sh=(0.15, 0.3))
        hline(c, [(gx, gy + 14), (gx, gy + 36)], STONE, 3, seed=seed)
        hline(c, [(gx - 8, gy + 22), (gx + 8, gy + 22)], STONE, 3, seed=seed + 1)
    c.glow(ux(0), uy(-1.6), 260, 70, (120, 150, 200, 35), 40)                                 # Mondschein um den Brunnen
    for x, y, w in ((300, 520, 160), (900, 600, 220), (560, 650, 180)):                        # Bodennebel
        c.glow(x, y, w, 22, (150, 165, 190, 55), 24)
    c.vignette(0.6)
    save_bg(c, "villa_eject_well_bg.jpg")

    # Brunnen hinten: Pfosten, Dach, Welle, Seil, Laterne, hintere Haelfte des Kranzes, Schacht
    c = C(260, 300)
    cx, g = 130, 300
    hell(c, cx, g - 100, 95, 30, STONE_L, lw=5, seed=1, sh=(0.1, 0.3))                        # Kranz (Oberseite)
    hell(c, cx, g - 100, 78, 22, (16, 16, 22, 255), lw=4, seed=2)                             # Schacht
    for sx in (-1, 1):                                                                        # Pfosten
        px = cx + sx * 90
        hrect(c, px - 8, g - 235, px + 8, g - 70, WOOD_D, lw=4, seed=3 + sx, sh=(0.1, 0.25))
        c.line([(px - 5, g - 230), (px - 5, g - 80)], WOOD, 3)
    hrect(c, cx - 100, g - 212, cx + 100, g - 198, WOOD_D, lw=4, seed=6)                      # Querbalken
    hell(c, cx, g - 205, 20, 9, WOOD, lw=3, seed=7)                                           # Welle
    hline(c, [(cx, g - 200), (cx, g - 118)], (120, 108, 86, 255), 3, seed=8, amp=1.5)         # Seil
    hline(c, [(cx, g - 200), (cx, g - 118)], (80, 70, 56, 255), 1, seed=9, amp=1.5)
    roof = [(cx - 125, g - 212), (cx, g - 290), (cx + 125, g - 212), (cx + 110, g - 206), (cx, g - 274), (cx - 110, g - 206)]
    hpoly(c, roof, WOOD_D, lw=5, seed=10, sh=(0.1, 0.2))
    for k in range(5):                                                                        # Schindelreihen
        t = k / 5
        hline(c, [(cx - 125 + 125 * t, g - 212 - 78 * t), (cx, g - 290 + 2)], (70, 48, 30, 255), 2, seed=20 + k)
        hline(c, [(cx + 125 - 125 * t, g - 212 - 78 * t), (cx, g - 290 + 2)], (70, 48, 30, 255), 2, seed=30 + k)
    hline(c, [(cx - 50, g - 212), (cx - 50, g - 150)], (90, 80, 64, 255), 2.5, seed=11)        # Laterne am Haken
    c.glow(cx - 50, g - 140, 40, 40, (255, 200, 120, 120), 10)
    hrr(c, cx - 62, g - 160, cx - 38, g - 122, 3, (40, 34, 30, 255), lw=4, seed=12)
    c.d.rectangle(c.P([(cx - 58, g - 155), (cx - 42, g - 127)]), fill=(255, 215, 140, 255))
    hpoly(c, [(cx - 64, g - 160), (cx - 36, g - 160), (cx - 50, g - 172)], (40, 34, 30, 255), lw=3, seed=13)
    cobweb_px(c, cx + 90, g - 206, 36, -1, 1, seed=1)
    save(c, "villa_eject_well_back.png")

    # Brunnen vorn: Steinzylinder mit vorderer Kranzhaelfte (Pivot unten Mitte, 2,0 x 1,4)
    c = C(200, 140)
    cx, g = 100, 138
    rnd = random.Random(2)
    hpoly(c, [(cx - 80, g), (cx + 80, g), (cx + 80, g - 100), (cx - 80, g - 100)], STONE, lw=0, seed=1)
    for row in range(4):                                                                      # Steinreihen
        y = g - 22 - row * 24
        off = 0 if row % 2 else 24
        x = cx - 80 - off
        while x < cx + 80:
            w = rnd.uniform(36, 54)
            col = (STONE, STONE_D, (90, 92, 96, 255))[rnd.randint(0, 2)]
            hpoly(c, [(max(cx - 80, x) + 2, y - 10), (min(cx + 80, x + w) - 2, y - 10), (min(cx + 80, x + w) - 2, y + 10), (max(cx - 80, x) + 2, y + 10)],
                  col, lw=2, outline=STONE_D, seed=int(x) + row, amp=1)
            x += w
    hline(c, [(cx - 80, g), (cx - 80, g - 100)], INK, 5, seed=3)
    hline(c, [(cx + 80, g), (cx + 80, g - 100)], INK, 5, seed=4)
    ring = ell_pts(cx, g - 100, 95, 30, 40, 0, math.pi) + ell_pts(cx, g - 100, 78, 22, 40, math.pi, 0)
    hpoly(c, ring, STONE_L, lw=5, seed=5, sh=(0.15, 0.3))
    for k in range(5):                                                                        # Moos
        mx, my = cx + rnd.uniform(-70, 70), g - rnd.uniform(10, 90)
        c.ell(mx, my, rnd.uniform(6, 12), rnd.uniform(3, 6), (70, 100, 60, 170), lw=0)
    save(c, "villa_eject_well_front.png")

    c = C(50, 60)                                                                              # Kurbel (Pivot Mitte)
    hell(c, 25, 30, 9, 9, BRASS_D, lw=3, seed=1)
    hline(c, [(25, 30), (25, 8)], INK, 8, seed=2)
    hline(c, [(25, 30), (25, 8)], BRASS, 5, seed=2)
    hline(c, [(25, 8), (42, 8)], INK, 8, seed=3)
    hline(c, [(25, 8), (42, 8)], WOOD, 5, seed=3)
    hell(c, 25, 30, 4, 4, BRASS_L, lw=0, seed=4)
    save(c, "villa_eject_crank.png")


# ================================================================== Szene 3: Die Kristallkugel

def seance():
    c = C(BW, BH)
    interior(c, seed=3, wall=PLUM, motif=PLUM_M, wall_d=PLUM_D)
    frame_portrait(c, ux(-2.75), uy(1.3), 62, 82, seed=2)
    # Kamin rechts mit schwacher Glut
    fx0, fy0, fx1, fy1 = ux(3.0), uy(0.35), ux(4.6), uy(-1.25)
    hrect(c, fx0 - 14, fy0 - 12, fx1 + 14, fy0 + 10, STONE_D, lw=4, seed=5, sh=(0.2, 0.3))
    hrect(c, fx0, fy0 + 10, fx1, fy1, STONE_D, lw=4, seed=6)
    hrect(c, fx0 + 26, fy0 + 40, fx1 - 26, fy1 - 6, (18, 14, 14, 255), lw=4, seed=7)
    c.glow((fx0 + fx1) / 2, fy1 - 20, 56, 20, (255, 110, 40, 120), 14)
    for k in range(7):
        c.ell((fx0 + fx1) / 2 + random.Random(k).uniform(-40, 40), fy1 - 18 + random.Random(k + 9).uniform(-4, 4), 4, 2.5, (255, 150, 60, 255), lw=0)
    c.glow((fx0 + fx1) / 2, fy1 + 30, 150, 36, (255, 120, 50, 40), 26)
    for k, hx in enumerate((fx0 + 20, fx1 - 20)):                                            # Kerzen auf dem Sims (aus)
        candle_px(c, hx, fy0 - 12, 18, r=6, seed=k)
    hrr(c, fx0 + 60, fy0 - 50, fx1 - 60, fy0 - 14, 4, (30, 26, 30, 255), lw=3, seed=8)        # dunkler Spiegel
    # Teppich
    hell(c, ux(0.9), uy(-2.0), 330, 62, VELVET_D, lw=4, seed=9)
    hell(c, ux(0.9), uy(-2.0), 290, 50, None, lw=2, outline=a4(BRASS_D, 160), seed=10)
    c.vignette(0.6)
    save_bg(c, "villa_eject_seance_bg.jpg")

    # Tisch mit Decke (Pivot unten Mitte, 2,9 x 2,15)
    c = C(290, 215)
    cx, g = 145, 212
    top = 70
    cloth = [(cx - 120, top), (cx + 120, top), (cx + 128, g - 6), (cx - 128, g - 6)]
    hpoly(c, cloth, VELVET, lw=5, seed=1, sh=(0.1, 0.3))
    for k in range(7):                                                                        # Falten
        fx = cx - 100 + k * 33
        hline(c, [(fx, top + 10), (fx + 3, g - 14)], VELVET_D if k % 2 else VELVET_L, 4, seed=k, amp=2)
    for k in range(20):                                                                       # Fransen
        c.line([(cx - 123 + k * 13, g - 8), (cx - 123 + k * 13, g)], BRASS, 2)
    hell(c, cx, top, 128, 40, VELVET_L, lw=5, seed=2, sh=(0.15, 0.2))
    hell(c, cx, top, 110, 30, None, lw=2, outline=a4(BRASS_D, 180), seed=3)
    # Ouija-Brett
    bx, by = cx - 20, top + 2
    hrect(c, bx - 52, by - 24, bx + 52, by + 24, (188, 168, 128, 255), lw=3, seed=4)
    for k in range(13):
        a = math.pi * 0.15 + math.pi * 0.7 * k / 12
        c.line([(bx + 40 * math.cos(a), by - 4 + 16 * math.sin(a) - 2), (bx + 40 * math.cos(a), by - 4 + 16 * math.sin(a) + 2)], WOOD_D, 1.5)
        c.line([(bx + 28 * math.cos(a), by + 2 + 11 * math.sin(a) - 2), (bx + 28 * math.cos(a), by + 2 + 11 * math.sin(a) + 2)], WOOD_D, 1.5)
    c.ell(bx - 40, by + 14, 6, 5, BRASS, lw=2)
    c.ell(bx + 40, by + 14, 6, 5, CREAM, lw=2)
    hpoly(c, [(bx - 10, by - 6), (bx + 6, by - 2), (bx + 2, by + 8), (bx - 12, by + 4)], WOOD_D, lw=2, seed=5)
    for k in range(3):                                                                        # Tarot
        tx, ty = cx + 70 + k * 12, top - 14 + k * 2
        hrect(c, tx - 7, ty - 9, tx + 7, ty + 9, (50, 60, 110, 255) if k < 2 else (188, 168, 128, 255), lw=2, seed=6 + k)
    save(c, "villa_eject_table.png")

    # Kristallkugel auf Messingfuss (Pivot unten Mitte, 0,9 x 1,0)
    c = C(90, 100)
    hell(c, 45, 92, 30, 8, BRASS_D, lw=3, seed=1)
    hpoly(c, [(28, 90), (62, 90), (56, 76), (34, 76)], BRASS, lw=3, seed=2, sh=(0.2, 0.3))
    c.glow(45, 48, 36, 36, (160, 130, 255, 110), 8)
    hell(c, 45, 46, 32, 32, (196, 200, 236, 215), lw=4, seed=3)
    c.ell(50, 54, 14, 10, (150, 120, 255, 90), lw=0)
    c.ell(34, 36, 9, 6, (255, 255, 255, 190), lw=0)
    save(c, "villa_eject_ball.png")

    c = C(24, 60)                                                                              # Kerze mit Messinghalter
    hell(c, 12, 56, 11, 4, BRASS, lw=2, seed=1)
    candle_px(c, 12, 54, 40, r=6, seed=2)
    save(c, "villa_eject_candle.png")


# ================================================================== Szene 4 und Skip 2: das Set

def set_bg():
    c = C(BW, BH)
    interior(c, seed=4, wall=(56, 34, 42, 255), motif=(70, 44, 54, 255), wall_d=(38, 22, 28, 255))
    for (px, py, seed) in ((ux(-4.4), uy(1.4), 1), (ux(1.0), uy(1.5), 2)):                    # Portraets, verhangen
        hrect(c, px - 60, py - 76, px + 60, py + 76, BRASS_D, lw=4, seed=seed)
        hpoly(c, [(px - 66, py - 84), (px + 66, py - 80), (px + 58, py + 50), (px + 20, py + 84), (px - 62, py + 70)],
              (150, 146, 136, 255), lw=4, seed=seed + 5, sh=(0.1, 0.25))
    # Dolly-Schienen, Kabel, Sandsack, C-Stand, Markierung
    for yy in (546, 574):
        hline(c, [(-10, yy), (BW + 10, yy)], MATTE_D, 7, seed=yy, amp=0.8)
        c.line([(0, yy - 2), (BW, yy - 2)], a4(STEEL, 90), 2)
    for x in range(30, BW, 72):
        hrect(c, x, 536, x + 14, 584, MATTE, lw=3, seed=x)
    cable(c, [(ux(-2.6), 470), (ux(-3.4), 500), (ux(-4.6), 520), (ux(-6.2), 600)], seed=1)
    cable(c, [(ux(3.6), 470), (ux(4.4), 530), (ux(5.3), 540), (ux(6.3), 620)], seed=2)
    cable(c, [(ux(2.0), 500), (ux(1.0), 640), (ux(-0.8), 660)], seed=3, w=3)
    hpoly(c, HD.wobble([(ux(5.0) - 30, 462), (ux(5.0) + 30, 462), (ux(5.0) + 26, 440), (ux(5.0) - 26, 440)], amp=3, seed=4, step=12, closed=True),
          (84, 70, 52, 255), lw=4, seed=4, sh=(0.1, 0.25))                                   # Sandsack
    hline(c, [(ux(5.2), 462), (ux(5.2), 300)], MATTE_L, 5, seed=5)                            # C-Stand
    hline(c, [(ux(5.2), 300), (ux(5.9), 262)], MATTE_L, 4, seed=6)
    hrect(c, ux(5.9) - 20, 244, ux(5.9) + 20, 270, MATTE, lw=3, seed=7)
    gaffer(c, ux(0.3) - 16, uy(-1.28) - 12, ux(0.3) + 16, uy(-1.28) + 12, 7)                 # Marke
    gaffer(c, ux(0.3) - 16, uy(-1.28) + 12, ux(0.3) + 16, uy(-1.28) - 12, 7)
    gaffer(c, ux(-1.6), 500, ux(-1.2), 498, 5)
    c.vignette(0.6)
    save_bg(c, "villa_eject_set_bg.jpg")

    # Filmkamera auf Dolly (Pivot unten Mitte, 2,0 x 2,7), Objektiv nach rechts
    c = C(200, 270)
    g = 268
    for wx in (40, 160):
        hell(c, wx, g - 8, 14, 9, MATTE_D, lw=3, seed=wx)
        c.ell(wx, g - 8, 5, 3.5, STEEL, lw=0)
    hrect(c, 20, g - 30, 180, g - 12, MATTE, lw=4, seed=1, sh=(0.2, 0.3))
    gaffer(c, 40, g - 20, 80, g - 20, 5)
    hline(c, [(36, g - 30), (36, g - 120), (22, g - 128)], INK, 8, seed=2)                    # Schubbuegel
    hline(c, [(36, g - 30), (36, g - 120), (22, g - 128)], STEEL, 4, seed=2)
    hrect(c, 92, g - 150, 108, g - 30, MATTE_L, lw=4, seed=3, sh=(0.0, 0.2))                   # Saeule
    hell(c, 118, g - 120, 5, 4, BRASS, lw=2, seed=4)
    c.line([(108, g - 118), (118, g - 120)], INK, 3)
    hrect(c, 80, g - 168, 120, g - 150, MATTE_L, lw=4, seed=5)                                 # Kopf
    hrect(c, 56, g - 218, 150, g - 166, MATTE, lw=4, seed=6, sh=(0.15, 0.25))                   # Koerper
    hpoly(c, [(150, g - 204), (178, g - 207), (178, g - 177), (150, g - 180)], MATTE_D, lw=4, seed=7)     # Objektiv
    for fr in (158, 168):
        c.line([(fr, g - 206), (fr, g - 178)], STEEL, 2)
    hell(c, 178, g - 192, 5, 15, (58, 78, 106, 255), lw=3, seed=8)
    c.ell(177, g - 188, 2, 5, (207, 228, 255, 180), lw=0)
    hpoly(c, [(180, g - 212), (196, g - 218), (196, g - 166), (180, g - 172)], MATTE, lw=4, seed=9)       # Kompendium
    for k in (-1, 1):                                                                         # Magazin
        hell(c, 103 + k * 22, g - 236, 22, 20, MATTE, lw=4, seed=10 + k)
        hell(c, 103 + k * 22, g - 236, 12, 11, MATTE_L, lw=2, seed=12 + k)
    hline(c, [(56, g - 196), (40, g - 206)], INK, 8, seed=14)                                 # Sucher
    hline(c, [(56, g - 196), (40, g - 206)], MATTE_L, 5, seed=14)
    hell(c, 38, g - 207, 5, 4, MATTE_D, lw=2, seed=15)
    c.ell(64, g - 212, 3, 3, (255, 80, 80, 255), lw=0)                                        # REC (Glow ist Sprite)
    gaffer(c, 90, g - 184, 120, g - 184, 5)
    cable(c, [(60, g - 170), (46, g - 120), (30, g - 40), (6, g - 10)], seed=3, w=3)
    save(c, "villa_eject_camera.png")

    # Scheinwerfer auf Stativ (Pivot unten Mitte, 1,5 x 3,3), Kopf nach links unten gerichtet
    c = C(150, 330)
    g, cx = 328, 75
    for (lx, ly) in ((cx - 50, g - 6), (cx + 48, g - 4), (cx + 10, g - 24)):                  # Beine
        hline(c, [(cx, g - 90), (lx, ly)], INK, 8, seed=int(lx))
        hline(c, [(cx, g - 90), (lx, ly)], MATTE_L, 4, seed=int(lx))
        hell(c, lx, ly, 6, 3, MATTE_D, lw=2, seed=int(ly))
    hpoly(c, HD.wobble([(cx + 10, g - 2), (cx + 44, g - 2), (cx + 40, g - 18), (cx + 14, g - 18)], amp=2, seed=1, step=10, closed=True),
          (84, 70, 52, 255), lw=3, seed=1)                                                   # Sandsack
    hline(c, [(cx, g - 60), (cx, g - 290)], INK, 12, seed=2)                                  # Saeule
    hline(c, [(cx, g - 60), (cx, g - 290)], MATTE_L, 7, seed=2)
    c.line([(cx - 2, g - 80), (cx - 2, g - 280)], a4(STEEL, 150), 1.5)
    hell(c, cx, g - 170, 7, 5, MATTE_D, lw=3, seed=3)
    gaffer(c, cx - 8, g - 120, cx + 8, g - 118, 7)
    hline(c, [(cx, g - 290), (cx + 14, g - 296), (cx + 14, g - 306)], INK, 7, seed=4)         # Buegel
    hx, hy = cx - 8, g - 300                                                                   # Lampenkopf, gekippt
    head = [(hx + 26, hy - 22), (hx + 40, hy + 6), (hx - 10, hy + 30), (hx - 24, hy + 2)]
    hpoly(c, head, MATTE, lw=5, seed=5, sh=(0.15, 0.25))
    hell(c, hx + 33, hy - 8, 6, 14, MATTE_L, lw=3, seed=6)
    for k in range(3):
        c.line([(hx + 30 - k * 5, hy - 2 + k * 4), (hx + 34 - k * 5, hy + 2 + k * 4)], MATTE_D, 2)
    c.glow(hx - 17, hy + 16, 24, 24, (255, 224, 170, 200), 6)                                 # Fresnel-Linse
    hell(c, hx - 17, hy + 16, 9, 16, (255, 236, 200, 255), lw=4, seed=7)
    c.ell(hx - 19, hy + 12, 3, 6, (255, 255, 255, 255), lw=0)
    for sgn in (1, -1):                                                                       # Torbleche
        hline(c, [(hx - 10 - sgn * 7, hy + 16 - sgn * 17), (hx - 34 - sgn * 10, hy + 20 - sgn * 24)], INK, 6, seed=8 + sgn)
        hline(c, [(hx - 10 - sgn * 7, hy + 16 - sgn * 17), (hx - 34 - sgn * 10, hy + 20 - sgn * 24)], MATTE_L, 3, seed=8 + sgn)
    cable(c, [(hx + 30, hy - 10), (cx + 20, g - 230), (cx - 10, g - 150), (cx + 20, g - 30), (cx + 60, g - 6)], seed=9, w=3)
    save(c, "villa_eject_lamp.png")

    # Filmklappe: Tafel (3,0 x 2,2) und Klappe (3,0 x 0,5, Pivot links oben)
    c = C(300, 220)
    hrect(c, 6, 50, 294, 214, MATTE_D, lw=6, seed=1, sh=(0.05, 0.1))
    for k in range(7):                                                                        # Streifen unten am Scharnier
        x = 6 + k * 44
        hpoly(c, [(x, 50), (x + 22, 50), (x + 34, 76), (x + 12, 76)], CHALK, lw=0, seed=k, amp=0.8)
    hrect(c, 6, 50, 294, 76, None, lw=5, seed=2)
    for yy in (120, 164):
        c.line([(14, yy), (286, yy)], CHALK, 2)
    label(c, 150, 98, "HOLLOWMERE MANOR", 22, fill=CHALK)
    label(c, 80, 142, "SCENE  1", 18, fill=CHALK)
    label(c, 220, 142, "TAKE  1", 18, fill=CHALK)
    label(c, 80, 188, "DIR.  ?", 15, fill=CHALK)
    label(c, 220, 188, "NIGHT", 15, fill=CHALK)
    save(c, "villa_eject_clap_base.png")

    c = C(300, 50)
    hrect(c, 4, 6, 296, 46, MATTE_D, lw=5, seed=3)
    for k in range(7):
        x = 4 + k * 44
        hpoly(c, [(x, 6), (x + 22, 6), (x + 34, 46), (x + 12, 46)], CHALK, lw=0, seed=k + 10, amp=0.8)
    hrect(c, 4, 6, 296, 46, None, lw=5, seed=3)
    hell(c, 16, 26, 6, 6, STEEL, lw=3, seed=4)                                                # Scharnierbolzen
    save(c, "villa_eject_clap_top.png")

    # Buehnenhaken (5,2 x 1,4, Pivot rechts Mitte): Stange nach rechts, Haken links
    c = C(520, 140)
    pole = [(520, 70), (96, 70)]
    hline(c, pole, INK, 20, seed=1, amp=1.5)
    hline(c, pole, WOOD, 13, seed=1, amp=1.5)
    c.line([(500, 65), (110, 65)], a4((160, 124, 84), 150), 3)
    crook = [(100, 70), (60, 72), (26, 56), (18, 30), (36, 12), (68, 14), (88, 34)]
    hline(c, crook, INK, 24, seed=2, amp=1.2)
    hline(c, crook, BRASS, 16, seed=2, amp=1.2)
    c.line(crook[1:], a4(BRASS_L, 160), 4)
    for x in (120, 134):                                                                      # Zwinge
        c.line([(x, 60), (x, 80)], STEEL, 4)
    save(c, "villa_eject_hook.png")

    # Regiestuhl (1,5 x 1,9, Pivot unten Mitte)
    c = C(150, 190)
    g = 188
    for (a, b) in (((20, g - 4), (130, g - 100)), ((130, g - 4), (20, g - 100))):             # X-Gestell
        hline(c, [a, b], INK, 9, seed=int(a[0]))
        hline(c, [a, b], WOOD, 5, seed=int(a[0]))
    hrect(c, 16, g - 108, 134, g - 92, (70, 22, 32, 255), lw=4, seed=3, sh=(0.1, 0.2))        # Sitz
    for x in (28, 122):
        hline(c, [(x, g - 108), (x, g - 182)], INK, 9, seed=x)
        hline(c, [(x, g - 108), (x, g - 182)], WOOD, 5, seed=x)
        hell(c, x, g - 184, 5, 5, WOOD_D, lw=3, seed=x + 1)
    hrect(c, 24, g - 176, 126, g - 130, (70, 22, 32, 255), lw=4, seed=4, sh=(0.12, 0.2))      # Lehne
    label(c, 75, g - 153, "DIRECTOR", 13, fill=CREAM)
    save(c, "villa_eject_chair.png")

    # Crew: A mit Headset und Klemmbrett, B mit Muetze und Megafon (beide Blick nach rechts, 1,2 x 1,3)
    c = C(120, 130)
    crew(c, 58, 68, 100, *CREW["blue"], seed=1)
    hline(c, ell_pts(58, 50, 40, 36, 24, math.pi * 1.1, math.pi * 1.9), MATTE_D, 5, seed=2, amp=0.8)      # Headset-Buegel
    hell(c, 24, 58, 7, 9, MATTE_D, lw=3, seed=3)
    hline(c, [(24, 66), (34, 80), (54, 82)], MATTE_D, 2.5, seed=4)                             # Mikrofonarm
    hell(c, 55, 83, 3, 3, MATTE_D, lw=0)
    hrect(c, 76, 76, 110, 116, WOOD_D, lw=3, seed=5)                                           # Klemmbrett
    hrect(c, 80, 82, 106, 112, CREAM, lw=2, seed=6)
    for k in range(4):
        c.line([(84, 88 + k * 6), (102, 88 + k * 6)], a4(INK, 120), 1.5)
    hrect(c, 88, 72, 98, 80, STEEL, lw=2, seed=7)
    save(c, "villa_eject_crew_a.png")

    c = C(120, 130)
    crew(c, 58, 68, 100, *CREW["orange"], seed=4)
    hpoly(c, [(22, 36), (90, 30), (98, 38), (30, 44)], MATTE, lw=3, seed=8, sh=(0.1, 0.2))   # Schirmmuetze
    hpoly(c, [(26, 36), (86, 31), (82, 16), (40, 18)], MATTE, lw=3, seed=9, sh=(0.2, 0.2))
    hpoly(c, [(88, 60), (112, 50), (116, 84), (90, 76)], (190, 60, 50, 255), lw=3, seed=10, sh=(0.15, 0.25))   # Megafon
    hrect(c, 72, 62, 90, 74, MATTE, lw=3, seed=11)
    hell(c, 114, 67, 5, 17, (120, 30, 30, 255), lw=3, seed=12)
    save(c, "villa_eject_crew_b.png")


# ================================================================== Skip 1: Mitternacht

def hall():
    c = C(BW, BH)
    interior(c, seed=5)
    # Fenster rechts (dunkle Scheiben; Wetterleuchten ist ein Glow-Sprite dahinter)
    wx, wy, ww, wh = ux(4.2), uy(1.3), 150, 230
    hrect(c, wx - ww / 2 - 16, wy - wh / 2 - 16, wx + ww / 2 + 16, wy + wh / 2 + 10, WAIN_D, lw=4, seed=1)
    grad_rect(c, wx - ww / 2, wy - wh / 2, wx + ww / 2, wy + wh / 2, (34, 40, 62), (14, 16, 28))
    for col in range(2):
        for row in range(3):
            gx0, gy0 = wx - ww / 2 + 6 + col * 72, wy - wh / 2 + 6 + row * 74
            hrect(c, gx0, gy0, gx0 + 66, gy0 + 68, None, lw=4, seed=row * 2 + col)
            c.d.line(c.P([(gx0 + 10, gy0 + 60), (gx0 + 56, gy0 + 10)]), fill=(200, 215, 240, 40), width=5 * S)
    hrect(c, wx - ww / 2 - 26, wy + wh / 2 + 10, wx + ww / 2 + 26, wy + wh / 2 + 26, STONE_D, lw=4, seed=9, sh=(0.2, 0.3))
    for sx in (-1, 1):                                                                        # Vorhaenge
        px = wx + sx * (ww / 2 + 30)
        hpoly(c, [(px - 18, wy - wh / 2 - 20), (px + 18, wy - wh / 2 - 20), (px + 22 * sx, wy + wh / 2 + 40), (px - 22 * sx, wy + wh / 2 + 40)],
              VELVET, lw=4, seed=20 + sx, sh=(0.08, 0.3))
    for cx in (ux(-2.6), ux(2.6)):
        candelabra_px(c, cx, uy(-1.25), seed=int(cx))
    hell(c, ux(0), uy(-2.1), 300, 50, VELVET_D, lw=4, seed=7)                                 # Laeufer
    hell(c, ux(0), uy(-2.1), 260, 40, None, lw=2, outline=a4(BRASS_D, 160), seed=8)
    hrr(c, ux(-5.0) - 70, uy(1.7) - 60, ux(-5.0) + 70, uy(1.7) + 60, 6, (30, 26, 30, 255), lw=4, seed=11)   # blinder Spiegel
    hrr(c, ux(-5.0) - 60, uy(1.7) - 50, ux(-5.0) + 60, uy(1.7) + 50, 4, None, lw=3, outline=BRASS_D, seed=12)
    c.vignette(0.6)
    save_bg(c, "villa_eject_hall_bg.jpg")

    # Standuhr (Pivot unten Mitte, 1,5 x 3,1): Pendelfenster lokal 0,55..1,65, Zifferblatt lokal 2,72
    c = C(150, 310)
    cx, g = 75, 308
    hrect(c, 8, g - 24, 142, g - 2, WAIN_L, lw=5, seed=1, sh=(0.1, 0.25))                      # Sockel
    hrect(c, 18, g - 196, 132, g - 24, WAIN, lw=5, seed=2, sh=(0.08, 0.22))                    # Rumpf
    hrect(c, 44, g - 165, 106, g - 55, (26, 22, 30, 255), lw=3, outline=BRASS_D, seed=3)       # Pendelfenster
    c.d.line(c.P([(48, g - 60), (48, g - 158)]), fill=(255, 255, 255, 50), width=3 * S)
    hrect(c, 12, g - 300, 138, g - 196, WAIN, lw=5, seed=4, sh=(0.1, 0.2))                     # Kopf
    hell(c, cx, g - 272, 42, 40, BRASS, lw=4, seed=5)
    hell(c, cx, g - 272, 35, 33, (200, 186, 150, 255), lw=2, outline=BRASS_D, seed=6)
    for k in range(12):
        a = k * math.pi / 6
        r1 = 35 * (0.74 if k % 3 == 0 else 0.84)
        c.line([(cx + r1 * math.cos(a), g - 272 + r1 * 0.95 * math.sin(a)), (cx + 32 * math.cos(a), g - 272 + 32 * 0.95 * math.sin(a))],
               INK, 3 if k % 3 == 0 else 1.5)
    c.ell(cx, g - 272, 3, 3, BRASS_D, lw=0)
    crown = [(8, g - 300), (142, g - 300), (142, g - 306), (cx + 14, g - 306), (cx + 7, g - 318), (cx, g - 314), (cx - 7, g - 318), (cx - 14, g - 306), (8, g - 306)]
    hpoly(c, crown, WAIN_L, lw=4, seed=7)
    hell(c, cx, g - 320, 4, 4, BRASS, lw=2, seed=8)
    cobweb_px(c, 140, g - 300, 26, -1, 1, seed=2)
    save(c, "villa_eject_pendulum.png") if False else None
    save(c, "villa_eject_clock.png")

    c = C(30, 120)                                                                             # Pendel (Pivot oben)
    hline(c, [(15, 4), (15, 96)], INK, 5, seed=1)
    hline(c, [(15, 4), (15, 96)], BRASS, 3, seed=1)
    hell(c, 15, 102, 13, 13, BRASS, lw=3, seed=2, sh=(0.2, 0.3))
    c.ell(11, 98, 4, 3, BRASS_L, lw=0)
    save(c, "villa_eject_pendulum.png")

    c = C(12, 44)                                                                              # Stundenzeiger (Pivot 0,5 / 0,86)
    hpoly(c, [(6, 2), (10, 30), (6, 42), (2, 30)], INK, lw=0, seed=1, amp=0.4)
    save(c, "villa_eject_hand_h.png")
    c = C(10, 60)                                                                              # Minutenzeiger
    hpoly(c, [(5, 1), (8, 42), (5, 58), (2, 42)], INK, lw=0, seed=2, amp=0.4)
    save(c, "villa_eject_hand_m.png")


# ================================================================== Hauptprogramm

def main():
    extra = "--common" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in (lambda: common(extra), window, well, seance, set_bg, hall):
        print(fn.__name__ if hasattr(fn, "__name__") and fn.__name__ != "<lambda>" else "common")
        fn()
    try:
        from villa_eject import sprites as needed
        missing = [n for n in needed() if not (OUT / n).exists()]
        if missing:
            print("FEHLT:", ", ".join(missing))
    except ImportError:
        pass
    total = sum(p.stat().st_size for p in OUT.glob("villa_eject*"))
    print(f"villa_eject* gesamt: {total / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
