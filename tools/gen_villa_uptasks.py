# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_villa_uptasks.py - Grafik der sechs eigenen Minispiele im Obergeschoss von Hollowmere Manor (18.11.).
#
# Prozedural im Stil der Villa-Minispiele (gen_villa_tasks.py: flache Toene, Glanz, dicke dunkle Kontur, Villa-Palette). Lagen und
# Groessen passen zu Villa/HollowmereUpperTasks.Games.cs: Tafel 720 x 520 Pixel = 7,2 x 5,2 Einheiten um die Mitte, 100 Pixel je
# Einheit, Einheit y nach oben. Ausgabe: Resources/villa/task_up_*.png (landet ueber build_assets_repo im Paket villa_map).
#
#   python tools/gen_villa_uptasks.py            -> alle Bilder
#   python tools/gen_villa_uptasks.py --sheet    -> zusaetzlich tools/_villa/uptasks_sheet.png (Uebersicht)

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ATLAS = HERE.parent.parent / "UnknownsAtlas"
sys.path.insert(0, str(ATLAS / "tools"))
sys.path.insert(0, str(HERE))
import gen_tasks as G                                           # noqa: E402
from gen_tasks import C, INK, S, label, mix, dark, light       # noqa: E402
import gen_villa_tasks as V                                     # noqa: E402  (Villa-Palette, damask, candle_glow)

OUT = HERE.parent / "Resources" / "villa"
G.OUT = OUT
W, H = 720, 520
ASSETS = HERE / "villa_assets"

WALNUT, WALNUT_L, WALNUT_D = V.WALNUT, V.WALNUT_L, V.WALNUT_D
BORDEAUX, BORDEAUX_L, BORDEAUX_D = V.BORDEAUX, V.BORDEAUX_L, V.BORDEAUX_D
BRASS, BRASS_L, BRASS_D = V.BRASS, V.BRASS_L, V.BRASS_D
PORC, PORC_D, CREAM, PARCH = V.PORC, V.PORC_D, V.CREAM, V.PARCH
BLOOD, BLOOD_L = V.BLOOD, V.BLOOD_L
SEPIA, SEPIA_D, SEPIA_L = (170, 132, 92, 255), (112, 82, 54, 255), (214, 184, 140, 255)
GREEN, RED = V.GREEN, V.RED


def X(u):
    return W / 2 + u * 100


def Y(u):
    return H / 2 - u * 100


def frame(c, inner=(40, 30, 34, 255)):
    """Holzrahmen aller Tafeln (wie die Villa-Minispiele) mit Innenflaeche."""
    c.rrect(4, 4, 716, 516, 26, WALNUT_D, lw=8, sh=(0.12, 0.2))
    c.grain(4, 4, 716, 516, 0.07, seed=11)
    c.rrect(22, 22, 698, 498, 16, inner, lw=5)


def title(c, text, x=360, y=40, px=22, fill=(236, 222, 190, 255)):
    # Schild aus Messing mit dunkler Schrift
    f = G.font(px)
    b = c.d.textbbox((0, 0), text, font=f)
    w = (b[2] - b[0]) / S + 34
    c.rrect(x - w / 2, y - 17, x + w / 2, y + 17, 8, BRASS, lw=4, sh=(0.25, 0.25))
    label(c, x, y, text, px, INK)


def portrait(name, w, h):
    """Ausschnitt eines vorhandenen GPT-Bildes der Villa (Gemaelde) fuer die Karteikarten."""
    p = ASSETS / name
    if not p.exists():
        return None
    im = Image.open(p).convert("RGBA")
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    im.thumbnail((w * S, h * S), Image.LANCZOS)
    return im


def sepia(im):
    g = im.convert("L")
    r = g.point(lambda v: min(255, int(v * 1.07 + 12)))
    gg = g.point(lambda v: int(v * 0.86 + 8))
    b = g.point(lambda v: int(v * 0.62))
    out = Image.merge("RGB", (r, gg, b)).convert("RGBA")
    out.putalpha(im.getchannel("A"))
    return out


# ------------------------------------------------------------------ gemeinsam

def common():
    c = C(72, 72)
    c.ell(36, 38, 31, 31, (60, 20, 20, 120), lw=0)
    c.ell(36, 36, 31, 31, (226, 222, 214, 255), lw=6, sh=(0.1, 0.18))
    c.line([(24, 24), (48, 48)], INK, 9)
    c.line([(48, 24), (24, 48)], INK, 9)
    c.glint(28, 24, 9, 5, 120, rot=35)
    c.save("task_up_close.png")
    c = C(124, 20)
    c.rrect(2, 2, 122, 18, 8, (30, 24, 26, 255), lw=3)
    c.save("task_up_bar_bg.png")
    c = C(116, 12)
    c.rrect(0, 0, 116, 12, 6, (255, 214, 120, 255), lw=0)
    c.glint(40, 3, 40, 2, 90)
    c.save("task_up_bar_fill.png")
    c = C(96, 96)
    for a in range(4):
        ang = a * math.pi / 2
        c.poly([(48, 48), (48 + math.cos(ang + 0.18) * 14, 48 + math.sin(ang + 0.18) * 14),
                (48 + math.cos(ang) * 46, 48 + math.sin(ang) * 46), (48 + math.cos(ang - 0.18) * 14, 48 + math.sin(ang - 0.18) * 14)],
               (255, 250, 220, 255), lw=0)
    c.glow(48, 48, 18, 18, (255, 255, 230, 200), 6)
    c.save("task_up_sparkle.png")


# ------------------------------------------------------------------ records (Attic)

DECADES = [("1880s", ["1881", "1884", "1889"]), ("1900s", ["1902", "1905", "1909"]), ("1920s", ["1921", "1926", "1928"])]
DRAWER_COL = [(150, 98, 60, 255), (128, 84, 52, 255), (108, 72, 46, 255)]


def records():
    c = C(W, H)
    frame(c, (52, 40, 32, 255))
    # Schreibtischplatte (Leder mit Holzkante)
    c.rrect(30, 70, 470, 490, 12, WALNUT, lw=5, sh=(0.1, 0.18))
    c.grain(30, 70, 470, 490, 0.08, seed=3)
    c.rrect(50, 90, 450, 470, 10, (66, 92, 70, 255), lw=4, sh=(0.08, 0.15))
    c.mottle(0.05, 12, seed=4)
    # Tintenfass und Feder als Beiwerk
    c.ell(420, 120, 20, 14, (30, 30, 40, 255), lw=4)
    c.line([(420, 108), (448, 76)], (230, 226, 210, 255), 4)
    # Aktenschrank rechts
    x0, x1 = X(1.55), X(3.25)
    c.rrect(x0, 60, x1, 500, 10, WALNUT_D, lw=6, sh=(0.1, 0.2))
    c.grain(x0, 60, x1, 500, 0.08, seed=5)
    for i, (dec, _) in enumerate(DECADES):
        cx, cy = X(2.4), Y([1.3, 0.0, -1.3][i])
        c.rrect(cx - 78, cy - 50, cx + 78, cy + 50, 6, (24, 16, 14, 255), lw=4)     # Oeffnung
    title(c, "FILE THE RECORDS BY DECADE", x=250, y=44, px=18)
    c.vignette(0.3)
    c.save("task_up_records_bg.png")
    for i, (dec, _) in enumerate(DECADES):
        c = C(160, 100)
        c.rrect(4, 4, 156, 96, 8, DRAWER_COL[i], lw=5, sh=(0.15, 0.25))
        c.grain(4, 4, 156, 96, 0.08, seed=20 + i)
        c.rrect(36, 18, 124, 46, 4, BRASS_L, lw=3, sh=(0.2, 0.2))
        label(c, 80, 32, dec, 18, INK)
        c.rrect(56, 62, 104, 78, 8, BRASS, lw=3, sh=(0.3, 0.3))                  # Griff
        c.glint(68, 66, 10, 3, 120)
        c.save(f"task_up_records_drawer_{i}.png")
    faces = ["villa_familienportrait.png", "villa_gemaelde_hausherrin.png", "villa_portrait_dame.png", "villa_portrait_offizier.png",
             "villa_portrait_maedchen.png", "villa_bilder_gruppe.png"]
    k = 0
    for d, (dec, years) in enumerate(DECADES):
        for i, yr in enumerate(years):
            c = C(130, 96)
            c.rrect(4, 4, 126, 92, 6, (232, 220, 190, 255), lw=4, sh=(0.05, 0.12))
            c.mottle(0.05, 6, seed=40 + k)
            c.rrect(12, 12, 62, 84, 3, SEPIA_D, lw=3)
            face = portrait(faces[k % len(faces)], 46, 68)
            if face is not None:
                face = sepia(face)
                c.img.alpha_composite(face, (int((37 - face.width / S / 2) * S), int((48 - face.height / S / 2) * S)))
                c.d = ImageDraw.Draw(c.img)
            c.rrect(12, 12, 62, 84, 3, None, lw=3)
            label(c, 95, 34, yr, 20, (60, 40, 30, 255))
            for ly in (56, 66, 76):
                c.line([(72, ly), (118, ly)], (150, 130, 110, 255), 2)
            c.save(f"task_up_records_card_{d}_{i}.png")
            k += 1


# ------------------------------------------------------------------ photos (Darkroom)

TRAY_LIQ = [(206, 178, 92, 255), (196, 196, 176, 255), (122, 150, 168, 255)]
TRAY_TXT = ["DEVELOP", "STOP", "FIX"]


def ghost_scene(c, x0, y0, w, h, seed, ghost=True):
    """Kleine Szene: Halle der Villa mit Treppe, optional ein Geist (Laken)."""
    rnd = random.Random(seed)
    c.rrect(x0, y0, x0 + w, y0 + h, 2, (78, 66, 60, 255), lw=0)
    c.d.rectangle([x0 * S, (y0 + h * 0.62) * S, (x0 + w) * S, (y0 + h) * S], fill=(110, 84, 60, 255))
    # Fenster und Treppe
    c.rrect(x0 + w * 0.08, y0 + h * 0.12, x0 + w * 0.28, y0 + h * 0.5, 2, (150, 160, 170, 255), lw=2)
    for k in range(5):
        sx = x0 + w * (0.55 + k * 0.07)
        sy = y0 + h * (0.62 - k * 0.09)
        c.d.rectangle([sx * S, sy * S, (sx + w * 0.3) * S, (sy + h * 0.09) * S], fill=(90, 64, 48, 255))
    if ghost:
        gx = x0 + w * rnd.uniform(0.3, 0.55)
        gy = y0 + h * 0.3
        gw, gh = w * 0.2, h * 0.55
        c.glow(gx + gw / 2, gy + gh / 2, gw * 0.8, gh * 0.6, (255, 255, 255, 90), 6)
        c.poly([(gx, gy + gh), (gx + gw * 0.05, gy + gh * 0.3), (gx + gw * 0.5, gy), (gx + gw * 0.95, gy + gh * 0.3), (gx + gw, gy + gh),
                (gx + gw * 0.8, gy + gh * 0.9), (gx + gw * 0.6, gy + gh), (gx + gw * 0.4, gy + gh * 0.9), (gx + gw * 0.2, gy + gh)],
               (240, 240, 236, 230), lw=2, outline=(60, 60, 60, 255))
        c.ell(gx + gw * 0.38, gy + gh * 0.28, gw * 0.07, gh * 0.06, INK, lw=0)
        c.ell(gx + gw * 0.62, gy + gh * 0.28, gw * 0.07, gh * 0.06, INK, lw=0)


def photos():
    c = C(W, H)
    frame(c, (34, 10, 12, 255))
    c.glow(360, 70, 260, 140, (200, 30, 30, 90), 30)              # Rotlicht
    c.ell(360, 36, 26, 16, (220, 40, 40, 255), lw=4)
    c.glint(352, 32, 10, 4, 160)
    # Waescheleine
    c.line([(30, Y(1.95)), (690, Y(1.95))], (200, 180, 160, 255), 3)
    # Papierstapel
    for k in range(4):
        c.rrect(X(-2.6) - 70 + k * 2, Y(0.8) - 52 - k * 3, X(-2.6) + 70 + k * 2, Y(0.8) + 52 - k * 3, 3, (236, 232, 222, 255), lw=3)
    label(c, X(-2.6), Y(0.8) + 70, "PHOTO PAPER", 14, (220, 180, 170, 255))
    # Arbeitstisch und Schalen
    c.rrect(26, Y(-0.45), 694, 494, 8, (70, 52, 44, 255), lw=5, sh=(0.08, 0.2))
    for i, (tx, liq, txt) in enumerate(zip([-2.15, 0.0, 2.15], TRAY_LIQ, TRAY_TXT)):
        cx, cy = X(tx), Y(-1.2)
        c.rrect(cx - 96, cy - 64, cx + 96, cy + 64, 12, (200, 200, 196, 255), lw=5, sh=(0.1, 0.25))
        c.rrect(cx - 82, cy - 50, cx + 82, cy + 50, 8, liq, lw=3)
        c.glint(cx - 40, cy - 36, 30, 5, 70)
        label(c, cx, Y(-2.13), f"{i + 1}. {txt}", 16, (236, 200, 190, 255))
    title(c, "DEVELOP THE SET PHOTOS", x=170, y=40, px=17)
    c.vignette(0.35)
    c.save("task_up_photos_bg.png")
    c = C(140, 105)
    c.rrect(3, 3, 137, 102, 3, (246, 244, 236, 255), lw=4)
    c.save("task_up_photos_paper.png")
    for i in range(2):
        c = C(140, 105)
        ghost_scene(c, 12, 12, 116, 81, seed=7 + i * 13)
        c.rrect(3, 3, 137, 102, 3, None, lw=4)
        img = c.img.resize((140, 105), Image.LANCZOS)
        img = sepia(img) if i == 1 else img
        # Rand bleibt weiss, damit das Bild auf dem Papier erscheint
        base = Image.new("RGBA", (140, 105), (0, 0, 0, 0))
        base.alpha_composite(img.crop((10, 10, 130, 95)), (10, 10))
        base.save(OUT / f"task_up_photos_img_{i}.png")
        print(OUT / f"task_up_photos_img_{i}.png", base.size)
    c = C(40, 60)
    c.rrect(10, 4, 30, 56, 4, (196, 160, 110, 255), lw=4, sh=(0.2, 0.2))
    c.line([(20, 10), (20, 50)], (120, 90, 60, 255), 3)
    c.save("task_up_photos_peg.png")


# ------------------------------------------------------------------ dress (Sewing Room)

GOWN = [((236, 226, 204, 255), "ivory"), ((150, 26, 40, 255), "crimson")]
SASH = [((216, 176, 74, 255), "gold"), ((120, 82, 160, 255), "violet")]
VEIL = [((246, 246, 250, 210), "white"), ((36, 32, 40, 225), "black")]


def dress_form(c, cx, top):
    """Schneiderpuppe ohne Kopf: Knauf, Torso, Staender, Fuss (Einheiten-Lage wie DressGame.Worn)."""
    c.rrect(cx - 8, top + 210, cx + 8, top + 372, 4, BRASS_D, lw=4)
    c.poly([(cx - 70, top + 384), (cx + 70, top + 384), (cx + 40, top + 364), (cx - 40, top + 364)], WALNUT, lw=5)
    c.ell(cx, top, 16, 14, BRASS, lw=4, sh=(0.3, 0.3))
    c.rrect(cx - 10, top + 10, cx + 10, top + 34, 4, (200, 190, 170, 255), lw=4)
    c.poly([(cx - 64, top + 46), (cx + 64, top + 46), (cx + 78, top + 110), (cx + 60, top + 190), (cx + 76, top + 236),
            (cx - 76, top + 236), (cx - 60, top + 190), (cx - 78, top + 110)], (214, 200, 176, 255), lw=6, sh=(0.12, 0.2))
    c.mottle(0.04, 8, seed=9)
    c.line([(cx, top + 50), (cx, top + 232)], (170, 150, 130, 255), 3)


def gown(col):
    c = C(230, 260)
    sk = col[0]
    c.poly([(80, 8), (150, 8), (164, 70), (150, 108), (226, 252), (4, 252), (80, 108), (66, 70)], sk, lw=6, sh=(0.18, 0.25))
    for k in range(4):
        x = 40 + k * 50
        c.line([(115, 110), (x, 250)], dark(sk, 0.82), 3)
    c.poly([(66, 70), (164, 70), (150, 108), (80, 108)], dark(sk, 0.9), lw=4)
    for k in range(6):
        c.ell(86 + k * 12, 40, 3, 3, light(sk, 0.4), lw=0)
    return c


def sash(col):
    c = C(200, 60)
    s = col[0]
    c.rrect(10, 18, 190, 42, 10, s, lw=5, sh=(0.25, 0.25))
    c.poly([(100, 30), (62, 6), (66, 54)], s, lw=5)
    c.poly([(100, 30), (138, 6), (134, 54)], s, lw=5)
    c.ell(100, 30, 12, 12, dark(s, 0.85), lw=4)
    return c


def veil(col):
    c = C(200, 230)
    v = col[0]
    c.poly([(100, 10), (150, 40), (196, 226), (4, 226), (50, 40)], v, lw=5, outline=(60, 56, 64, 255))
    for x in (40, 80, 120, 160):
        c.line([(100, 30), (x, 222)], (190, 186, 196, 160) if v[0] > 128 else (70, 66, 80, 200), 2)
    c.ell(100, 18, 30, 12, (220, 210, 230, 255) if v[0] > 128 else (60, 50, 60, 255), lw=4)
    for k in range(5):
        c.ell(76 + k * 12, 18, 4, 4, (240, 230, 250, 255), lw=0)
    return c


def dress():
    c = C(W, H)
    frame(c)
    V.damask(c, 26, 26, 694, 494, seed=13)
    c.d.rectangle([26 * S, 400 * S, 694 * S, 494 * S], fill=(90, 60, 44, 255))
    c.grain(26, 400, 694, 494, 0.08, seed=14)
    # Kleiderstange links
    c.rrect(40, Y(2.05) - 6, 330, Y(2.05) + 6, 6, BRASS, lw=4, sh=(0.3, 0.3))
    c.rrect(40, Y(2.05), 52, 480, 4, BRASS_D, lw=4)
    c.rrect(318, Y(2.05), 330, 480, 4, BRASS_D, lw=4)
    # Puppe (Kleid sitzt bei y -0,55, Schaerpe 0,32, Schleier 1,3)
    dress_form(c, X(0.3), Y(1.62))
    # Musterkarte rechts
    c.rrect(X(2.65) - 80, Y(1.95), X(2.65) + 80, Y(-1.4), 8, (232, 220, 190, 255), lw=5, sh=(0.05, 0.15))
    c.mottle(0.04, 8, seed=15)
    label(c, X(2.65), Y(1.95) + 20, "PATTERN", 18, INK)
    for yy in (Y(-1.4) - 26,):
        label(c, X(2.65), yy, "No. 13", 14, (90, 60, 50, 255))
    title(c, "DRESS THE MANNEQUIN", x=200, y=40, px=17)
    c.vignette(0.3)
    c.save("task_up_dress_bg.png")
    for i, col in enumerate(GOWN):
        gown(col).save(f"task_up_dress_gown_{i}.png")
    for i, col in enumerate(SASH):
        sash(col).save(f"task_up_dress_sash_{i}.png")
    for i, col in enumerate(VEIL):
        veil(col).save(f"task_up_dress_veil_{i}.png")


# ------------------------------------------------------------------ tapes (Master Bedroom)

def tapes():
    c = C(W, H)
    frame(c, (44, 26, 32, 255))
    V.damask(c, 26, 26, 694, 380, seed=21)
    c.d.rectangle([26 * S, 380 * S, 694 * S, 494 * S], fill=(96, 64, 48, 255))
    c.grain(26, 380, 694, 494, 0.08, seed=22)
    # Fernseher (Bildschirm 3,4 x 2,2 um -0,9/0,85)
    sx, sy = X(-0.9), Y(0.85)
    c.rrect(sx - 200, sy - 135, sx + 200, sy + 135, 26, (110, 78, 54, 255), lw=6, sh=(0.12, 0.22))
    c.grain(sx - 200, sy - 135, sx + 200, sy + 135, 0.07, seed=23)
    c.rrect(sx - 176, sy - 116, sx + 176, sy + 116, 18, (20, 20, 24, 255), lw=5)
    # Videorekorder (-0,9/-1,35, 4,6 x 1,0)
    vx, vy = X(-0.9), Y(-1.35)
    c.rrect(vx - 236, vy - 52, vx + 236, vy + 52, 8, (54, 54, 62, 255), lw=6, sh=(0.15, 0.25))
    c.brushed(0.04, seed=24)
    c.rrect(X(-2.05) - 46, vy - 38, X(-0.85) + 46, vy + 38, 6, (26, 24, 30, 255), lw=4)       # Kassettenfenster
    c.line([(X(-2.05), vy + 22), (X(-0.85), vy + 22)], (60, 44, 34, 255), 6)                   # Band
    label(c, X(0.75), vy + 46, "MARK", 14, (230, 220, 210, 255))
    # Kurbelgehaeuse rechts
    kx, ky = X(2.45), Y(-0.35)
    c.ell(kx, ky, 100, 100, (70, 56, 50, 255), lw=6, sh=(0.15, 0.25))
    c.arc([kx - 116, ky - 116, kx + 116, ky + 116], 200, 330, (236, 200, 120, 255), 6)
    c.poly([(kx - 112, ky - 36), (kx - 92, ky - 62), (kx - 128, ky - 60)], (236, 200, 120, 255), lw=0)
    label(c, kx, ky + 124, "REWIND", 16, (236, 220, 190, 255))
    # Lampen-Leiste "GHOSTS"
    c.rrect(X(1.6), Y(2.25), X(3.3), Y(1.65), 8, (40, 30, 30, 255), lw=4)
    label(c, X(2.45), Y(1.5), "GHOSTS", 14, (236, 220, 190, 255))
    title(c, "REWIND THE GHOST TAPES", x=X(-0.9), y=Y(-0.45) + 2, px=13)
    c.vignette(0.3)
    c.save("task_up_tapes_bg.png")
    # Bildschirme 340 x 220
    rnd = random.Random(5)
    img = Image.new("RGBA", (340, 220))
    px = img.load()
    for yy in range(220):
        band = 40 if (yy // 6) % 7 == 0 else 0
        for xx in range(340):
            v = rnd.randint(30, 200) + band
            px[xx, yy] = (min(255, v), min(255, v), min(255, v + 10), 255)
    img.save(OUT / "task_up_tapes_static.png")
    c = C(340, 220)
    ghost_scene(c, 0, 0, 340, 220, seed=1, ghost=False)
    c.save("task_up_tapes_room.png")
    for i in range(3):
        c = C(340, 220)
        ghost_scene(c, 0, 0, 340, 220, seed=1, ghost=False)
        gx = [70, 170, 250][i]
        gy = [70, 50, 80][i]
        c.glow(gx + 30, gy + 50, 50, 60, (255, 255, 255, 110), 10)
        c.poly([(gx, gy + 110), (gx + 4, gy + 30), (gx + 30, gy), (gx + 56, gy + 30), (gx + 60, gy + 110), (gx + 46, gy + 98),
                (gx + 30, gy + 110), (gx + 14, gy + 98)], (240, 240, 236, 235), lw=3, outline=(70, 70, 70, 255))
        c.ell(gx + 22, gy + 34, 5, 7, INK, lw=0)
        c.ell(gx + 38, gy + 34, 5, 7, INK, lw=0)
        c.ell(gx + 30, gy + 54, 6, 8, (40, 20, 24, 255), lw=0)
        c.save(f"task_up_tapes_ghost_{i}.png")
    c = C(340, 220)
    c.rrect(0, 0, 340, 220, 4, (255, 255, 255, 255), lw=0)
    c.save("task_up_tapes_flash.png")
    c = C(352, 232)
    c.rrect(6, 6, 346, 226, 18, None, lw=8, outline=(20, 20, 24, 255))
    for yy in range(10, 226, 6):
        c.line([(10, yy), (342, yy)], (0, 0, 0, 40), 1)
    c.glint(90, 40, 70, 14, 50, rot=-8)
    c.save("task_up_tapes_glass.png")
    c = C(64, 64)
    c.ell(32, 32, 29, 29, (60, 44, 34, 255), lw=4)
    c.ell(32, 32, 14, 14, (200, 200, 206, 255), lw=4)
    for a in range(3):
        ang = a * 2 * math.pi / 3
        c.line([(32, 32), (32 + math.cos(ang) * 12, 32 + math.sin(ang) * 12)], INK, 4)
    c.save("task_up_tapes_reel.png")
    c = C(190, 190)
    c.ell(95, 95, 84, 84, (150, 120, 70, 255), lw=6, sh=(0.2, 0.3))
    c.ell(95, 95, 62, 62, (120, 92, 54, 255), lw=4)
    for a in range(6):
        ang = a * math.pi / 3
        c.line([(95 + math.cos(ang) * 18, 95 + math.sin(ang) * 18), (95 + math.cos(ang) * 60, 95 + math.sin(ang) * 60)], BRASS_D, 8)
    c.ell(95, 95, 18, 18, BRASS, lw=4, sh=(0.3, 0.3))
    c.ell(95 + 64, 95, 16, 16, (180, 40, 40, 255), lw=4, sh=(0.3, 0.3))          # Griff
    c.glint(150, 88, 6, 3, 160)
    c.save("task_up_tapes_crank.png")
    for name, dy, col in (("task_up_tapes_btn.png", 0, (200, 40, 40, 255)), ("task_up_tapes_btn_down.png", 5, (150, 30, 30, 255))):
        c = C(100, 70)
        c.rrect(6, 14, 94, 64, 10, (40, 40, 44, 255), lw=4)
        c.rrect(14, 8 + dy, 86, 50 + dy, 10, col, lw=5, sh=(0.25, 0.25))
        c.ell(50, 29 + dy, 9, 9, (250, 230, 230, 255), lw=0)
        c.save(name)
    for name, col in (("task_up_tapes_lamp_off.png", (70, 50, 46, 255)), ("task_up_tapes_lamp_on.png", (140, 255, 170, 255))):
        c = C(40, 40)
        if "on" in name:
            c.glow(20, 20, 18, 18, (140, 255, 170, 140), 5)
        c.ell(20, 20, 13, 13, col, lw=4, sh=(0.25, 0.2))
        c.glint(16, 15, 5, 3, 140)
        c.save(name)


# ------------------------------------------------------------------ toys (Nursery)

def toys():
    c = C(W, H)
    frame(c)
    for k in range(12):                                         # Dielen
        y0 = 26 + k * 40
        c.d.rectangle([26 * S, y0 * S, 694 * S, (y0 + 40) * S], fill=(118 - (k % 3) * 8, 98 - (k % 3) * 6, 74, 255))
        c.line([(26, y0), (694, y0)], (60, 46, 36, 255), 3)
    c.grain(26, 26, 694, 494, 0.06, seed=31)
    c.ell(X(-1.1), Y(0.0), 230, 160, (120, 60, 74, 255), lw=5)
    c.ell(X(-1.1), Y(0.0), 200, 134, (150, 82, 96, 255), lw=3)
    c.mottle(0.05, 10, seed=32)
    # Kiste (Inneres; Vorderwand und Deckel sind eigene Bilder)
    cx, cy = X(2.25), Y(-1.15)
    c.rrect(cx - 130, cy - 70, cx + 130, cy + 80, 10, (70, 44, 30, 255), lw=6)
    c.rrect(cx - 116, cy - 58, cx + 116, cy + 60, 8, (34, 22, 16, 255), lw=0)
    title(c, "PUT AWAY THE TOYS", x=170, y=40, px=17)
    c.vignette(0.3)
    c.save("task_up_toys_bg.png")
    c = C(270, 100)
    c.rrect(4, 4, 266, 96, 10, (176, 112, 62, 255), lw=6, sh=(0.15, 0.25))
    c.grain(4, 4, 266, 96, 0.08, seed=33)
    for x in (60, 135, 210):
        c.rrect(x - 26, 22, x + 26, 78, 6, (214, 170, 90, 255), lw=4)
    label(c, 60, 50, "A", 26, BORDEAUX)
    label(c, 135, 50, "B", 26, (40, 80, 140, 255))
    label(c, 210, 50, "C", 26, (60, 120, 60, 255))
    c.save("task_up_toys_chestfront.png")
    c = C(270, 70)
    c.rrect(4, 4, 266, 66, 10, (160, 100, 56, 255), lw=6, sh=(0.2, 0.25))
    c.grain(4, 4, 266, 66, 0.08, seed=34)
    c.save("task_up_toys_lid.png")
    c = C(270, 170)
    c.rrect(4, 4, 266, 166, 10, (176, 112, 62, 255), lw=6, sh=(0.15, 0.25))
    c.grain(4, 4, 266, 166, 0.08, seed=35)
    c.rrect(110, 70, 160, 100, 6, BRASS, lw=4, sh=(0.3, 0.3))
    c.save("task_up_toys_lid_closed.png")
    # Spielsachen
    c = C(120, 110)
    for (x, y, col, ch) in ((10, 50, (200, 60, 60, 255), "H"), (62, 50, (60, 110, 190, 255), "M"), (36, 6, (230, 190, 60, 255), "O")):
        c.rrect(x, y, x + 50, y + 50, 6, col, lw=5, sh=(0.2, 0.25))
        label(c, x + 25, y + 25, ch, 24, (250, 246, 236, 255))
    c.save("task_up_toy_blocks.png")
    c = C(110, 110)
    c.ell(55, 55, 48, 48, (230, 70, 70, 255), lw=6, sh=(0.2, 0.25))
    c.arc([7, 7, 103, 103], 200, 340, (250, 240, 220, 255), 12)
    c.arc([7, 7, 103, 103], 20, 160, (70, 120, 200, 255), 12)
    c.glint(36, 34, 12, 7, 130, rot=30)
    c.save("task_up_toy_ball.png")
    c = C(150, 100)
    c.rrect(10, 30, 100, 76, 6, (40, 110, 70, 255), lw=5, sh=(0.2, 0.25))
    c.rrect(70, 8, 100, 36, 4, (40, 110, 70, 255), lw=5)
    c.rrect(100, 44, 142, 76, 6, (200, 60, 50, 255), lw=5)
    c.rrect(22, 14, 40, 32, 3, (60, 60, 64, 255), lw=4)
    for x in (30, 70, 120):
        c.ell(x, 82, 13, 13, (40, 40, 44, 255), lw=4)
        c.ell(x, 82, 4, 4, BRASS_L, lw=0)
    c.save("task_up_toy_train.png")
    c = C(100, 140)
    c.poly([(20, 136), (50, 60), (80, 136)], (220, 150, 170, 255), lw=5, sh=(0.15, 0.25))
    c.ell(50, 44, 30, 32, (246, 226, 210, 255), lw=5, sh=(0.1, 0.15))
    c.arc([18, 8, 82, 70], 180, 360, (120, 70, 40, 255), 14)
    c.ell(39, 44, 6, 7, INK, lw=0)
    c.ell(61, 44, 6, 7, INK, lw=0)
    c.ell(37, 41, 2, 2, (255, 255, 255, 255), lw=0)
    c.ell(59, 41, 2, 2, (255, 255, 255, 255), lw=0)
    c.arc([38, 52, 62, 66], 20, 160, (160, 40, 50, 255), 3)
    c.line([(46, 22), (42, 48)], (120, 40, 40, 160), 2)                      # Riss im Porzellan
    c.save("task_up_toy_doll.png")
    c = C(110, 140)
    c.rrect(10, 70, 100, 136, 6, (90, 60, 140, 255), lw=5, sh=(0.2, 0.25))
    label(c, 55, 103, "?", 34, (240, 220, 120, 255))
    for k in range(4):
        c.ell(55, 64 - k * 8, 10, 4, (180, 180, 186, 255), lw=3)
    c.ell(55, 26, 22, 22, (246, 236, 220, 255), lw=5)
    c.poly([(33, 18), (55, 0), (77, 18)], (210, 50, 50, 255), lw=4)
    c.ell(47, 26, 4, 4, INK, lw=0)
    c.ell(63, 26, 4, 4, INK, lw=0)
    c.arc([42, 26, 68, 40], 10, 170, INK, 3)
    c.save("task_up_toy_jack.png")


# ------------------------------------------------------------------ bath (Bathroom)

def bath():
    c = C(W, H)
    frame(c, (40, 50, 56, 255))
    for yy in range(26, 494, 34):                                # Fliesen
        for xx in range(26, 694, 34):
            col = (206, 214, 214, 255) if ((xx // 34 + yy // 34) % 2) else (176, 190, 190, 255)
            c.d.rectangle([xx * S, yy * S, (xx + 33) * S, (yy + 33) * S], fill=col)
    c.mottle(0.05, 10, seed=41)
    c.glow(150, 300, 90, 40, (140, 20, 20, 60), 18)
    # Wanne: Innenflaeche um -0,3/-0,4, 5,1 x 2,1 (Wasser 500 x 210), Rand drumherum
    cx, cy = X(-0.3), Y(-0.4)
    c.glow(cx, cy + 60, 290, 120, (40, 30, 30, 110), 14)       # weicher Schatten
    for fx in (-220, 220):
        c.poly([(cx + fx - 22, cy + 120), (cx + fx + 22, cy + 120), (cx + fx + 30, cy + 168), (cx + fx - 30, cy + 168)],
               BRASS, lw=5, sh=(0.3, 0.3))
    c.ell(cx, cy, 290, 136, (240, 238, 232, 255), lw=6, sh=(0.08, 0.2))
    c.ell(cx, cy, 255, 106, (226, 228, 226, 255), lw=4, sh=(0.0, 0.18))
    # Abfluss mit Stoepsel und Kette im Becken
    dx, dy = X(1.25), Y(-0.75)
    c.ell(dx, dy, 18, 10, (60, 60, 64, 255), lw=3)
    c.line([(dx + 10, dy - 4), (X(2.3), Y(0.42))], (150, 150, 156, 255), 3)
    title(c, "DRAIN THE BATH, SCRUB IT CLEAN", x=250, y=40, px=16)
    c.vignette(0.3)
    c.save("task_up_bath_bg.png")
    # Randring als Ueberlagerung (verdeckt den Wasserrand)
    c = C(W, H)
    c.ell(cx, cy, 290, 136, None, lw=0)
    ring = Image.new("L", (W * S, H * S), 0)
    rd = ImageDraw.Draw(ring)
    rd.ellipse([(cx - 290) * S, (cy - 136) * S, (cx + 290) * S, (cy + 136) * S], fill=255)
    rd.ellipse([(cx - 252) * S, (cy - 103) * S, (cx + 252) * S, (cy + 103) * S], fill=0)
    rim = Image.new("RGBA", (W * S, H * S), (240, 238, 232, 255))
    c.img.paste(rim, (0, 0), ring)
    c.d = ImageDraw.Draw(c.img)
    c.ell(cx, cy, 290, 136, None, lw=6)
    c.ell(cx, cy, 253, 104, None, lw=4)
    c.glint(cx - 160, cy - 118, 70, 6, 120)
    c.save("task_up_bath_rim.png")
    c = C(500, 210)
    c.ell(250, 105, 248, 103, (150, 18, 26, 255), lw=0)
    c.ell(250, 112, 220, 80, (120, 10, 18, 255), lw=0)
    c.glint(170, 60, 90, 10, 70)
    c.glint(320, 140, 40, 5, 50)
    c.save("task_up_bath_water.png")
    c = C(120, 80)
    for k in range(3):
        c.arc([10 + k * 14, 6 + k * 8, 110 - k * 14, 74 - k * 8], k * 60, k * 60 + 250, (110, 10, 20, 220), 6)
    c.save("task_up_bath_swirl.png")
    c = C(50, 40)
    c.ell(25, 20, 20, 14, (40, 40, 44, 255), lw=4, sh=(0.2, 0.2))
    c.save("task_up_bath_plug.png")
    c = C(30, 130)
    for k in range(9):
        c.ell(15, 8 + k * 14, 6, 8, (170, 170, 176, 255), lw=3)
    c.save("task_up_bath_chain.png")
    c = C(70, 70)
    c.ell(35, 35, 28, 28, None, lw=10, outline=BRASS_D)
    c.ell(35, 35, 28, 28, None, lw=6, outline=BRASS_L)
    c.save("task_up_bath_ring.png")
    for i in range(3):
        c = C(150, 100)
        rnd = random.Random(50 + i)
        pts = []
        for k in range(14):
            a = k * 2 * math.pi / 14
            r = rnd.uniform(0.6, 1.0)
            pts.append((75 + math.cos(a) * 62 * r, 50 + math.sin(a) * 38 * r))
        c.poly(pts, (150, 24, 30, 230), lw=0)
        for k in range(5):
            x = rnd.uniform(30, 120)
            c.line([(x, 50), (x + rnd.uniform(-6, 6), 50 + rnd.uniform(25, 45))], (130, 16, 24, 220), rnd.uniform(4, 8))
        c.glint(60, 36, 16, 4, 60)
        c.save(f"task_up_bath_stain_{i}.png")
    c = C(110, 80)
    c.rrect(8, 12, 102, 72, 18, (240, 210, 90, 255), lw=5, sh=(0.2, 0.25))
    for k in range(10):
        c.ell(20 + (k * 37) % 76, 24 + (k * 23) % 40, 4, 3, (210, 170, 60, 255), lw=0)
    c.rrect(8, 50, 102, 72, 10, (60, 140, 90, 255), lw=4)
    c.save("task_up_bath_sponge.png")


def sheet():
    names = sorted(p.name for p in OUT.glob("task_up_*_bg.png"))
    ims = [Image.open(OUT / n).convert("RGB") for n in names]
    out = Image.new("RGB", (W * 3 + 40, H * 2 + 30), (24, 24, 24))
    for i, im in enumerate(ims):
        out.paste(im, (10 + (i % 3) * (W + 10), 10 + (i // 3) * (H + 10)))
    (HERE / "_villa").mkdir(exist_ok=True)
    out.save(HERE / "_villa" / "uptasks_sheet.png")


if __name__ == "__main__":
    common()
    records()
    photos()
    dress()
    tapes()
    toys()
    bath()
    if "--sheet" in sys.argv:
        sheet()
