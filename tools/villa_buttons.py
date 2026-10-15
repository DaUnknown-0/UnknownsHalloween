# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_buttons.py - Freeplay-Logo "the MANOR" (1000 x 250) und rundes Lobby-Symbol (256 x 256) fuer
# Hollowmere Manor, im Format der Atlas-Knoepfe (UnknownsAtlas/tools/gen_buttons.py, gen_icons.py):
# Pille mit Icon links und Schriftzug mit Verlauf und doppelter Kontur, Symbol mit flachen Tonstufen,
# Glanzkanten und dicker dunkler Kontur.
#
# SCHNITTSTELLE (gen_villa.copy_buttons): render() -> (button RGBA 1000x250, icon RGBA 256x256)

import math
import os
import sys

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)

from PIL import Image, ImageDraw, ImageFilter      # noqa: E402

import gen_buttons as GB                            # noqa: E402
import gen_icons as GI                              # noqa: E402

NIGHT = (24, 22, 44)
NIGHT_L = (58, 46, 86)
HOUSE = (30, 26, 40)
HOUSE_L = (52, 44, 64)
WINDOW = (255, 196, 92)
MOON = (236, 232, 206)
BOLT = (200, 220, 255)
INK = (16, 12, 22)
TOP, MID, BOT = (236, 232, 214), (176, 160, 196), (96, 64, 120)     # Knochenweiss -> Flieder -> Pflaume


def _villa(d, w, h, ox, oy, sc, line):
    """Villa-Silhouette (Mittelbau mit Turm, zwei Fluegel, Giebel), Fenster beleuchtet. Masse in Bruchteilen."""
    def P(x, y):
        return (ox + x * sc, oy + y * sc)
    ol = INK + (255,)
    body = [P(-0.42, 0.0), P(-0.42, -0.2), P(-0.3, -0.3), P(-0.18, -0.2), P(-0.18, -0.28), P(-0.08, -0.28),
            P(-0.08, -0.48), P(0.0, -0.62), P(0.08, -0.48), P(0.08, -0.28), P(0.18, -0.28), P(0.18, -0.2),
            P(0.3, -0.32), P(0.42, -0.2), P(0.42, 0.0)]
    d.polygon(body, fill=HOUSE + (255,), outline=ol, width=line)
    d.line([P(0.0, -0.62), P(0.0, -0.7)], fill=ol, width=line)
    for x, y in ((-0.34, -0.12), (-0.24, -0.12), (0.24, -0.12), (0.34, -0.12), (-0.03, -0.4), (0.0, -0.18)):
        d.rectangle([P(x - 0.025, y - 0.04), P(x + 0.025, y + 0.04)], fill=WINDOW + (255,), outline=ol, width=max(1, line // 2))
    d.rectangle([P(-0.13, -0.16), P(-0.07, -0.08)], fill=(60, 20, 30, 255), outline=ol, width=max(1, line // 2))   # dunkles Fenster


def draw_villa_icon(box):
    """Nacht-Scheibe, Mond mit Wolke, Blitz, Villa auf dem Huegel, Grabsteine (fuer das Freeplay-Logo)."""
    w, h = GB.s(box[0]), GB.s(box[1])
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    line = max(2, int(0.016 * w))
    sky_mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sky_mask).ellipse((0, 0, w - 1, h - 1), fill=255)
    img.paste(GB.gradient_v((w, h), [(0.0, NIGHT), (0.6, NIGHT_L), (1.0, (90, 54, 110))]), (0, 0), sky_mask)
    d = ImageDraw.Draw(img)
    # Mond mit Lichthof
    mx, my, mr = 0.7 * w, 0.26 * h, 0.13 * w
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((mx - mr * 1.6, my - mr * 1.6, mx + mr * 1.6, my + mr * 1.6), fill=MOON + (90,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(line * 3)))
    d = ImageDraw.Draw(img)
    d.ellipse((mx - mr, my - mr, mx + mr, my + mr), fill=MOON + (255,))
    d.ellipse((mx - mr * 0.5, my - mr * 0.4, mx - mr * 0.2, my - mr * 0.1), fill=(206, 200, 176, 255))
    # Blitz links
    pts = [(0.2 * w, 0.06 * h), (0.27 * w, 0.24 * h), (0.22 * w, 0.25 * h), (0.31 * w, 0.44 * h)]
    d.line(pts, fill=BOLT + (255,), width=line * 2, joint="curve")
    # Huegel und Villa
    ground = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ground)
    gd.ellipse((-0.3 * w, 0.72 * h, 1.3 * w, 1.6 * h), fill=(28, 34, 30, 255), outline=INK + (255,), width=line)
    ground.putalpha(Image.composite(ground.split()[3], Image.new("L", (w, h), 0), sky_mask))
    img.alpha_composite(ground)
    d = ImageDraw.Draw(img)
    _villa(d, w, h, 0.5 * w, 0.8 * h, 0.95 * w, line)
    for gx, tilt in ((0.16, -0.12), (0.84, 0.1), (0.72, -0.05)):           # Grabsteine
        cx, cy = gx * w, 0.9 * h
        d.rounded_rectangle((cx - 0.035 * w, cy - 0.08 * h, cx + 0.035 * w, cy), radius=line * 2, fill=(110, 112, 120, 255),
                            outline=INK + (255,), width=line)
    return img


def render_button():
    return GB.render_button("MANOR", draw_villa_icon, [(0.0, TOP), (0.3, MID), (0.72, MID), (1.0, BOT)], MID,
                            hi_col=(250, 246, 236), dark_col=INK)


def render_icon():
    """Rundes Symbol fuer den Lobby-Kartenwaehler (Kreis und Ring bringt der Vanilla-Knopf mit)."""
    c = GI.Icon()
    house, house_l, roof = (60, 52, 76, 255), (84, 74, 104, 255), (40, 34, 52, 255)
    win = (255, 200, 96, 255)
    # Mond hinter dem Turm
    c.glow(176, 70, 40, (236, 232, 206, 110), 10)
    c.d.ellipse([146 * GI.S, 40 * GI.S, 206 * GI.S, 100 * GI.S], fill=(236, 232, 206, 255))
    # Fluegel, Mittelbau, Turm
    c.rect(34, 136, 92, 214, house)
    c.poly([(26, 140), (63, 104), (100, 140)], roof, sh=(0.1, 0.25))
    c.rect(164, 136, 222, 214, house)
    c.poly([(156, 140), (193, 104), (230, 140)], roof, sh=(0.1, 0.25))
    c.rect(88, 120, 168, 214, house_l)
    c.rect(110, 70, 146, 122, house_l)
    c.poly([(102, 74), (128, 30), (154, 74)], roof, sh=(0.1, 0.25))
    c.line([(128, 30), (128, 16)], GI.INK, 6)
    for x, y in ((46, 160), (70, 160), (176, 160), (200, 160), (120, 86), (100, 146), (146, 146)):
        c.glow(x + 6, y + 9, 10, (255, 190, 90, 90), 4)
        c.rect(x, y, x + 12, y + 18, win, lw=5 * GI.S, sh=(0.0, 0.15))
    c.rect(116, 176, 140, 214, (52, 20, 30, 255), lw=6 * GI.S)            # Tuer
    c.d.ellipse([134 * GI.S, 194 * GI.S, 138 * GI.S, 198 * GI.S], fill=(220, 180, 100, 255))
    return c.img.resize((256, 256), Image.LANCZOS)


def render():
    return render_button(), render_icon()


if __name__ == "__main__":
    b, i = render()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_villa")
    os.makedirs(out, exist_ok=True)
    b.save(os.path.join(out, "button_villa_preview.png"))
    i.save(os.path.join(out, "icon_villa_preview.png"))
    print("ok", b.size, i.size)
