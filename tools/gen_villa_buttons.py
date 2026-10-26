# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_villa_buttons.py - Symbole fuer den Use-Knopf auf Hollowmere Manor (Atlas-Mechaniken), im Stil der
# Atlas-Knoepfe (UnknownsAtlas/tools/gen_climb_button.py): flache Flaechen, zwei Tonstufen, Glanzkante,
# dicke dunkle Kontur, 256 x 256, Beschriftung setzt das Spiel darunter.
#
#   python tools/gen_villa_buttons.py   ->  Resources/villa/task_villa_btn_secret.png (Geheimgang)
#                                           Resources/villa/task_villa_btn_candle.png (Kerze anzuenden)
#                                           Resources/villa/task_villa_btn_blow.png   (Kerze ausblasen)
#                                           Resources/villa/task_villa_btn_pet.png    (Haustier am Grab streicheln)

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "Resources" / "villa"
S = 4
N = 256 * S
INK = (29, 27, 33, 255)
LW = 10 * S

WALNUT = (118, 74, 46, 255)
WALNUT_D = (78, 48, 30, 255)
WALNUT_L = (166, 112, 72, 255)
BRASS = (214, 176, 84, 255)
BRASS_D = (150, 116, 44, 255)
DARK = (14, 12, 18, 255)
WHITE = (246, 244, 240, 255)
CREAM = (240, 226, 190, 255)
CREAM_D = (196, 176, 130, 255)
FLAME = (255, 196, 70, 255)
FLAME_L = (255, 242, 180, 255)
FLAME_D = (236, 120, 40, 255)
SMOKE = (150, 150, 160, 255)
PINK = (238, 88, 120, 255)
PINK_D = (186, 52, 84, 255)
PINK_L = (255, 170, 190, 255)


def canvas():
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def P(pts):
    return [(x * S, y * S) for x, y in pts]


def poly(d, pts, fill, lw=LW):
    d.polygon(P(pts), fill=fill)
    if lw:
        d.line(P(pts + [pts[0]]), fill=INK, width=lw, joint="curve")
        r = lw / 2
        for x, y in P(pts):
            d.ellipse([x - r, y - r, x + r, y + r], fill=INK)


def ell(d, cx, cy, rx, ry, fill, lw=LW):
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill, outline=INK if lw else None, width=lw)


def line(d, pts, fill, w):
    d.line(P(pts), fill=fill, width=int(w * S), joint="curve")
    r = w * S / 2
    for x, y in P(pts):
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def save(img, name):
    img = img.resize((256, 256), Image.LANCZOS)
    img.save(OUT / name)
    print(OUT / name, img.size)


def secret():
    """Wandvertaefelung, als Geheimtuer aufgeschwenkt: dunkler Spalt dahinter, Pfeil hinein."""
    img, d = canvas()
    # Wand (Rahmenleisten) hinten
    poly(d, [(20, 40), (236, 40), (236, 230), (20, 230)], WALNUT_D)
    # dunkler Durchgang
    poly(d, [(84, 58), (176, 58), (176, 212), (84, 212)], DARK)
    # Tuerblatt perspektivisch aufgeschwenkt (Scharnier links)
    door = [(84, 58), (150, 86), (150, 196), (84, 212)]
    poly(d, door, WALNUT)
    poly(d, [(92, 72), (140, 94), (140, 186), (92, 198)], WALNUT_L, lw=5 * S)
    line(d, [(96, 78), (136, 97)], WALNUT_D, 4)
    # Messinggriff
    ell(d, 138, 140, 7, 9, BRASS, lw=5 * S)
    # Pfeil hinein (weiss), von rechts unten in den Spalt
    arrow = [(228, 196), (196, 196), (196, 180), (160, 150), (196, 120), (196, 104), (228, 104)]
    poly(d, [(160, 150), (210, 110), (210, 132), (232, 132), (232, 168), (210, 168), (210, 190)], WHITE)
    _ = arrow
    return img


def candle(lit=True):
    """Kerze mit Streichholzflamme (anzuenden) oder mit Rauchfaden und Atem (ausblasen)."""
    img, d = canvas()
    # Kerze
    poly(d, [(92, 110), (164, 110), (160, 236), (96, 236)], CREAM)
    poly(d, [(100, 122), (120, 122), (118, 226), (104, 226)], CREAM_D, lw=0)
    line(d, [(96, 236), (160, 236)], INK, 10)
    # Wachsnasen
    poly(d, [(92, 110), (110, 110), (108, 140), (98, 146), (90, 130)], CREAM, lw=6 * S)
    # Docht
    line(d, [(128, 110), (128, 92)], INK, 8)
    if lit:
        # Flamme (Tropfen) mit hellem Kern
        pts = [(128 + 26 * math.sin(a) * (1 - 0.35 * (1 + math.cos(a)) / 2), 94 - 34 * (1 + math.cos(a)) / 2 + 6)
               for a in [i / 24 * 2 * math.pi for i in range(25)]]
        poly(d, [(x, y - 6) for x, y in pts], FLAME, lw=7 * S)
        poly(d, [(128 + (x - 128) * 0.45, 100 + (y - 100) * 0.5) for x, y in pts], FLAME_L, lw=0)
        # Streichholz von rechts
        line(d, [(236, 190), (158, 112)], INK, 16)
        line(d, [(236, 190), (158, 112)], WALNUT_L, 9)
        ell(d, 156, 110, 12, 12, FLAME_D, lw=6 * S)
    else:
        # Rauchfaden
        line(d, [(128, 92), (136, 74), (124, 56), (134, 36), (126, 22)], INK, 12)
        line(d, [(128, 92), (136, 74), (124, 56), (134, 36), (126, 22)], SMOKE, 6)
        # Atemstoss von rechts (drei Linien)
        for k, (y, l) in enumerate(((70, 60), (88, 72), (106, 60))):
            line(d, [(238, y), (238 - l, y + (k - 1) * 4)], INK, 14)
            line(d, [(238, y), (238 - l, y + (k - 1) * 4)], WHITE, 7)
    return img


def pet():
    """Grosses Herz mit weissem Pfotenabdruck (User 26.10.: das Haustier am Grab streicheln)."""
    img, d = canvas()
    heart = []
    for i in range(64):
        t = i / 64 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        heart.append((128 + x * 6.6, 122 - y * 6.6))
    poly(d, heart, PINK)
    poly(d, [(128 + (x - 128) * 0.78 - 8, 122 + (y - 122) * 0.78 - 8) for x, y in heart[40:60]] + [(128, 122)], PINK_L, lw=0)
    # Pfote: Ballen und vier Zehen
    ell(d, 128, 150, 30, 24, WHITE, lw=6 * S)
    for cx, cy in ((92, 112), (114, 94), (142, 94), (164, 112)):
        ell(d, cx, cy, 12, 15, WHITE, lw=6 * S)
    return img


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    save(secret(), "task_villa_btn_secret.png")
    save(candle(True), "task_villa_btn_candle.png")
    save(candle(False), "task_villa_btn_blow.png")
    save(pet(), "task_villa_btn_pet.png")
