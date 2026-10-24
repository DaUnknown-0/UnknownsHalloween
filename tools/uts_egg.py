# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# uts_egg.py - Easter Egg "Laptop fuer den Geist des Mod-Autors" (Nachtrag zum Auftrag 2026-10-24, TOR Forgotten Fixes).
#
#   python tools/uts_egg.py     -> assets/uts_egg/egg_laptop_1..8.png (256 x 200, Alpha), tools/_uts_egg/sheet.png
#
# Aufgeklappter Laptop in Dreiviertelansicht von vorn, Bildschirm zum Betrachter: dunkler Bildschirm mit gruenen
# Codezeilen (#4ADE80) als Striche und Bloecke (keine lesbare Schrift, das Bild wird gespiegelt), ein paar Woerter in
# Gelb, Blau und Violett, Einrueckungen; pro Bild rollt der Code genau eine Zeile nach oben (nahtlose Schleife ueber
# acht Bilder), unten ein Cursor, der in vier der acht Bilder sichtbar ist; leichter Bildschirmschein. Alle acht Bilder
# deckungsgleich, nur der Bildschirminhalt aendert sich. Im Spiel 0,5 Einheiten breit (ca. 64 px), daher wenige kraeftige
# Formen und dicke Umrisse. Gezeichnet mit museum_art.Canvas in Pixelkoordinaten (ppm = 1, y von unten).

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from museum_art import Canvas, OUTLINE, alpha, hexc, shade  # noqa: E402

ASSETS = HERE.parent / "assets" / "uts_egg"
PREVIEW = HERE / "_uts_egg"
W, H = 256, 200
N = 8

SHELL = hexc("#6a7280")
SHELL_L = hexc("#8a94a4")
SHELL_D = hexc("#3f4650")
BEZEL = hexc("#2a2e36")
SCREEN = hexc("#0b1812")
CODE = hexc("#4ADE80")
CODE_D = hexc("#2a9a56")
WORD = {"y": hexc("#facc15"), "b": hexc("#60a5fa"), "p": hexc("#c084fc"), "o": hexc("#fb923c")}
KEY = hexc("#2e333c")
KEY_L = hexc("#4a515c")
STICKER = hexc("#f97316")

# Bildschirmrechteck (leicht nach hinten gekippt, Perspektive): unten links, unten rechts, oben rechts, oben links
SCR = [(48, 118), (208, 118), (214, 20), (42, 20)]
INNER = [(58, 110), (198, 110), (203, 30), (53, 30)]

# Codezeilen der Schleife: (Einrueckung in Stufen, Segmente: (Breite, Farbe)) ; Farbe None = gruen
LINES = [
    (0, ((16, "p"), (30, None), (10, "y"))),
    (1, ((22, None), (8, "b"), (26, None))),
    (1, ((34, None), (14, "o"))),
    (2, ((12, "b"), (40, None))),
    (2, ((26, None), (12, "y"), (16, None))),
    (1, ((18, "p"), (34, None))),
    (0, ((44, None), (10, "b"))),
    (1, ((30, None),)),
]
ROW_H = 10.5


def Y(y):
    """Pixel von oben -> Canvas-y (von unten)."""
    return H - y


def laptop(frame):
    c = Canvas(0, 0, W, H, 1)
    rnd = random.Random(3)
    P = lambda pts: [(x, Y(y)) for x, y in pts]
    # weicher Schein des Bildschirms (sehr zart) und Schatten unter dem Geraet
    c.soft_shadow(P([(36, 182), (232, 182), (238, 194), (30, 194)]), 90, 5)
    c.glow(128, Y(70), 110, CODE, 0.16)
    # Unterteil: Deckflaeche (Tastaturdeck) als Trapez, Vorderkante dunkel
    deck = [(30, 172), (226, 172), (210, 122), (46, 122)]
    front = [(30, 172), (226, 172), (226, 184), (30, 184)]
    c.poly(P(front), fill=SHELL_D, outline=OUTLINE, width=5)
    c.poly(P(deck), fill=SHELL, outline=OUTLINE, width=5)
    c.line(P([(40, 170), (216, 170)]), fill=SHELL_L, width=2.5)
    # Tastatur: Reihen mit Tasten in Perspektive, Leertaste, Touchpad
    rows = 4
    for r in range(rows):
        t0, t1 = r / rows, (r + 1) / rows
        yy0, yy1 = 128 + t0 * 34, 128 + t1 * 34
        x0a, x1a = 58 + t0 * (-14), 198 + t0 * 14
        x0b, x1b = 58 + t1 * (-14), 198 + t1 * 14
        nk = 12 if r < 3 else 3
        for k in range(nk):
            u0, u1 = k / nk + 0.08 / nk, (k + 1) / nk - 0.08 / nk
            if r == 3 and k == 1:
                u0, u1 = 0.3, 0.7
            quad = [(x0a + (x1a - x0a) * u0, yy0 + 0.6), (x0a + (x1a - x0a) * u1, yy0 + 0.6), (x0b + (x1b - x0b) * u1, yy1 - 0.6), (x0b + (x1b - x0b) * u0, yy1 - 0.6)]
            c.poly(P(quad), fill=KEY, outline=alpha(OUTLINE, 160), width=1.2)
            c.line(P([(quad[0][0] + 1, quad[0][1] + 1.2), (quad[1][0] - 1, quad[1][1] + 1.2)]), fill=KEY_L, width=1.0)
    c.poly(P([(104, 164), (152, 164), (154, 170), (102, 170)]), fill=SHELL_D, outline=alpha(OUTLINE, 200), width=1.5)   # Touchpad
    # Scharnier
    c.poly(P([(50, 116), (206, 116), (208, 124), (48, 124)]), fill=SHELL_D, outline=OUTLINE, width=4)
    # Deckel mit Bezel, Bildschirm
    c.poly(P(SCR), fill=BEZEL, outline=OUTLINE, width=5)
    c.line(P([(46, 114), (210, 114)]), fill=shade(BEZEL, 1.5), width=2)
    c.poly(P(INNER), fill=SCREEN, outline=alpha(OUTLINE, 220), width=2.5)
    # Codezeilen (Schleife: Zeile i des Bildes = LINES[(i + frame) % N])
    visible = 7
    top = 36.0
    for i in range(visible):
        ln_idx = (i + frame) % N
        indent, segs = LINES[ln_idx]
        y = top + i * ROW_H
        # Perspektive: der Bildschirm wird nach unten etwas breiter
        t = (y - 30) / 80.0
        xl = 53 + (58 - 53) * t + 8 + indent * 11
        xr = 203 + (198 - 203) * t - 8
        x = xl
        for wdt, col in segs:
            if x + wdt > xr:
                wdt = max(0, xr - x)
            if wdt <= 0:
                break
            c.poly(P([(x, y), (x + wdt, y), (x + wdt, y + 5.5), (x, y + 5.5)]), fill=CODE if col is None else WORD[col])
            if col is None and wdt > 20:
                c.poly(P([(x + 2, y + 1.5), (x + wdt * 0.5, y + 1.5), (x + wdt * 0.5, y + 2.6), (x + 2, y + 2.6)]), fill=alpha((255, 255, 255, 255), 70))
            x += wdt + 6
    # Zeilennummern-Striche links, Scrollbalken rechts
    for i in range(visible):
        y = top + i * ROW_H
        t = (y - 30) / 80.0
        xl = 53 + (58 - 53) * t + 2
        c.poly(P([(xl, y + 1), (xl + 3, y + 1), (xl + 3, y + 4.5), (xl, y + 4.5)]), fill=CODE_D)
    c.poly(P([(198, 34), (201, 34), (200, 106), (197, 106)]), fill=alpha(CODE_D, 120))
    sb = 34 + 7 * ((frame * 3) % 8)      # wandert ueber die Schleife und springt nicht am Nahtpunkt
    c.poly(P([(196.5, sb), (200.5, sb), (201, sb + 14), (197, sb + 14)]), fill=CODE)
    # Cursor (blinkt: in vier der acht Bilder sichtbar), Terminalzeile unten
    if (frame // 2) % 2 == 0:
        y = top + visible * ROW_H
        c.poly(P([(62, y), (70, y), (70, y + 6), (62, y + 6)]), fill=CODE)
    # Bildschirmglanz und Scanlinien-Andeutung
    c.poly(P([(58, 32), (86, 32), (68, 108), (56, 108)]), fill=alpha((255, 255, 255, 255), 14))
    for k in range(5):
        yy = 42 + k * 14
        c.line(P([(56, yy), (200, yy)]), fill=alpha((255, 255, 255, 255), 10), width=1)
    # Aufkleber auf dem Deckelrand (oben links auf dem Bezel) und Kamera-Punkt
    c.ellipse(62, Y(25), 4.5, 4.5, fill=STICKER, outline=OUTLINE, width=1.5)
    c.ellipse(62, Y(25), 1.6, 1.6, fill=hexc("#fde68a"))
    c.ellipse(128, Y(25), 2.2, 2.2, fill=SHELL_L, outline=alpha(OUTLINE, 200), width=1)
    # Lichtkante am Deckel
    c.line(P([(44, 22), (212, 22)]), fill=shade(BEZEL, 1.6), width=2)
    return c.finish()


def ghost(c, x, y, s=1.0, a=255):
    """Einfacher Geist (Bettlaken, Among-Us-Visor) fuer die Vorschau; nur Vergleichsmassstab."""
    P = lambda pts: [(px, Y(py)) for px, py in pts]
    body = [(x - 40 * s, y + 50 * s), (x - 40 * s, y - 20 * s), (x - 30 * s, y - 50 * s), (x, y - 62 * s), (x + 30 * s, y - 50 * s), (x + 40 * s, y - 20 * s), (x + 40 * s, y + 50 * s)]
    hem = [(x + 40 * s - k * 16 * s, y + 50 * s + (8 * s if k % 2 else 0)) for k in range(6)]
    col = (226, 228, 240, a)
    c.poly(P(body + hem), fill=col, outline=(20, 20, 30, a), width=4)
    c.poly(P([(x - 26 * s, y - 36 * s), (x + 22 * s, y - 36 * s), (x + 26 * s, y - 20 * s), (x - 22 * s, y - 16 * s)]), fill=(140, 200, 230, a), outline=(20, 20, 30, a), width=3)
    c.ellipse(x + 10 * s, Y(y - 30 * s), 6 * s, 3 * s, fill=(240, 250, 255, a))


def sheet(frames):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    pad = 16
    sh = Image.new("RGB", (4 * (W + pad) + pad, 2 * (H + 40) + 300), (60, 62, 72))
    d = ImageDraw.Draw(sh)
    for i, im in enumerate(frames):
        x, y = pad + (i % 4) * (W + pad), 30 + (i // 4) * (H + 40)
        d.rectangle([x, y, x + W, y + H], outline=(90, 94, 104))
        sh.paste(im, (x, y), im)
        d.text((x, y - 24), "egg_laptop_%d.png" % (i + 1), font=font, fill=(255, 255, 255))
    # Vorschau in Spielgroesse: Laptop 0,5 Einheiten (64 px) neben einem Geist von 0,8 Einheiten (102 px), 85 % Deckkraft
    y0 = 2 * (H + 40) + 20
    d.text((pad, y0), "Vorschau 1:1 in Spielgroesse (Laptop 64 px breit, Geist 0,8 Einheiten, 85 % Deckkraft)", font=font, fill=(255, 255, 255))
    bg = Image.new("RGBA", (sh.width - 2 * pad, 240), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bg)
    for gx in range(0, bg.width, 24):
        for gy in range(0, bg.height, 24):
            bd.rectangle([gx, gy, gx + 23, gy + 23], fill=(92, 94, 104, 255) if (gx // 24 + gy // 24) % 2 else (76, 78, 88, 255))
    for k in range(4):
        x = 90 + k * 260
        c = Canvas(0, 0, 220, 220, 1)
        ghost(c, 90, 110, s=1.0, a=255)
        g = c.finish()
        g.putalpha(g.getchannel("A").point(lambda v: int(v * 0.85)))
        bg.alpha_composite(g, (x - 60, 10))
        small = frames[k * 2].resize((64, 50), Image.LANCZOS)
        small.putalpha(small.getchannel("A").point(lambda v: int(v * 0.85)))
        bg.alpha_composite(small, (x + 40, 118))
    sh.paste(bg, (pad, y0 + 30), bg)
    return sh


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)
    frames = [laptop(k) for k in range(N)]
    for k, im in enumerate(frames):
        assert im.size == (W, H), im.size
        im.save(ASSETS / ("egg_laptop_%d.png" % (k + 1)), optimize=True)
    sheet(frames).save(PREVIEW / "sheet.png", optimize=True)
    print(f"{N} Bilder nach {ASSETS}, Uebersicht {PREVIEW / 'sheet.png'}")


if __name__ == "__main__":
    main()
