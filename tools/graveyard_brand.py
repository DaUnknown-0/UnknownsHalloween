# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_brand.py - Freeplay-Logo "the GRAVEYARD" (1000 x 250) und rundes Lobby-Symbol (256 x 256) fuer
# Ravenhollow Cemetery, im Format der Atlas-Knoepfe (wie villa_buttons.py): Pille mit Bild links und Schriftzug
# mit Verlauf und doppelter Kontur; Symbol mit flachen Tonstufen, Glanzkanten und dicker dunkler Kontur.
#
# SCHNITTSTELLE (gen_graveyard.button_and_icon): render(out_dir, key, preview_dir)

import math
import os
import sys

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)

from PIL import Image, ImageDraw, ImageFilter      # noqa: E402

import gen_buttons as GB                            # noqa: E402
import gen_icons as GI                              # noqa: E402

NIGHT = (16, 26, 30)
NIGHT_L = (34, 58, 60)
FOG = (120, 150, 150)
STONE = (92, 98, 112)
STONE_L = (128, 136, 152)
DARK = (22, 24, 30)
MOON = (232, 236, 214)
BELL = (196, 150, 80)
INK = (12, 14, 18)
TOP, MID, BOT = (226, 236, 222), (150, 182, 160), (52, 92, 76)        # Knochenweiss -> Moosgruen -> Tannendunkel


def draw_icon_scene(box):
    """Nachtscheibe: Vollmond mit Hof, Glockenturm mit Glocke, kahler Baum mit Raben, Grabsteine, Nebelband."""
    w, h = GB.s(box[0]), GB.s(box[1])
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    line = max(2, int(0.016 * w))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, w - 1, h - 1), fill=255)
    img.paste(GB.gradient_v((w, h), [(0.0, NIGHT), (0.65, NIGHT_L), (1.0, (40, 70, 64))]), (0, 0), mask)
    mx, my, mr = 0.32 * w, 0.28 * h, 0.15 * w                                          # Mond
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((mx - mr * 1.7, my - mr * 1.7, mx + mr * 1.7, my + mr * 1.7), fill=MOON + (80,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(line * 3)))
    d = ImageDraw.Draw(img)
    d.ellipse((mx - mr, my - mr, mx + mr, my + mr), fill=MOON + (255,))
    for cx, cy, r in ((-0.35, -0.2, 0.22), (0.25, 0.3, 0.16), (-0.1, 0.35, 0.1)):
        d.ellipse((mx + cx * mr - r * mr, my + cy * mr - r * mr, mx + cx * mr + r * mr, my + cy * mr + r * mr), fill=(206, 210, 188, 255))
    ol = INK + (255,)
    ground = Image.new("RGBA", (w, h), (0, 0, 0, 0))                                   # Huegel
    gd = ImageDraw.Draw(ground)
    gd.ellipse((-0.3 * w, 0.74 * h, 1.3 * w, 1.6 * h), fill=(26, 40, 34, 255), outline=ol, width=line)
    ground.putalpha(Image.composite(ground.split()[3], Image.new("L", (w, h), 0), mask))
    img.alpha_composite(ground)
    d = ImageDraw.Draw(img)
    tx, tb = 0.66 * w, 0.84 * h                                                         # Glockenturm
    tw = 0.17 * w
    d.rectangle((tx - tw / 2, tb - 0.36 * h, tx + tw / 2, tb), fill=STONE + (255,), outline=ol, width=line)
    d.rectangle((tx - tw / 2, tb - 0.52 * h, tx + tw / 2, tb - 0.36 * h), fill=DARK + (255,), outline=ol, width=line)
    d.polygon([(tx - 0.035 * w, tb - 0.38 * h), (tx + 0.035 * w, tb - 0.38 * h), (tx + 0.025 * w, tb - 0.47 * h), (tx - 0.025 * w, tb - 0.47 * h)],
              fill=BELL + (255,), outline=ol)
    d.polygon([(tx - tw / 2 - 0.02 * w, tb - 0.52 * h), (tx + tw / 2 + 0.02 * w, tb - 0.52 * h), (tx, tb - 0.72 * h)], fill=(52, 56, 70, 255), outline=ol)
    d.line([(tx, tb - 0.72 * h), (tx, tb - 0.8 * h)], fill=ol, width=line)
    d.line([(tx - 0.03 * w, tb - 0.77 * h), (tx + 0.03 * w, tb - 0.77 * h)], fill=ol, width=line)
    d.rounded_rectangle((tx - 0.03 * w, tb - 0.12 * h, tx + 0.03 * w, tb), radius=line * 2, fill=(70, 50, 36, 255), outline=ol, width=max(1, line // 2))
    d.line([(tx - tw / 2 + line, tb - 0.35 * h), (tx - tw / 2 + line, tb - 0.02 * h)], fill=STONE_L + (255,), width=max(1, line // 2))
    bx, bb = 0.2 * w, 0.88 * h                                                         # kahler Baum
    def br(x, y, a, ln, wd, depth):
        if depth == 0:
            return
        ex, ey = x + math.cos(a) * ln, y - math.sin(a) * ln
        d.line([(x, y), (ex, ey)], fill=ol, width=int(wd))
        for s_ in (-0.45, 0.4):
            br(ex, ey, a + s_, ln * 0.68, max(1, wd * 0.65), depth - 1)
    br(bx, bb, math.pi / 2, 0.2 * h, line * 2.2, 5)
    for rx, ry in ((0.12, 0.54), (0.27, 0.5)):                                        # Raben
        x, y = rx * w, ry * h
        d.ellipse((x - 0.03 * w, y - 0.02 * h, x + 0.03 * w, y + 0.02 * h), fill=ol)
        d.ellipse((x + 0.015 * w, y - 0.04 * h, x + 0.045 * w, y - 0.01 * h), fill=ol)
        d.polygon([(x + 0.04 * w, y - 0.03 * h), (x + 0.07 * w, y - 0.022 * h), (x + 0.04 * w, y - 0.018 * h)], fill=ol)
    for gx, tilt in ((0.36, 0), (0.48, 1), (0.88, 0)):                                 # Grabsteine
        cx, cy = gx * w, 0.93 * h
        d.rounded_rectangle((cx - 0.04 * w, cy - 0.11 * h, cx + 0.04 * w, cy), radius=line * 2, fill=STONE_L + (255,), outline=ol, width=line)
        d.line([(cx, cy - 0.09 * h), (cx, cy - 0.04 * h)], fill=DARK + (255,), width=max(1, line // 2))
        d.line([(cx - 0.018 * w, cy - 0.075 * h), (cx + 0.018 * w, cy - 0.075 * h)], fill=DARK + (255,), width=max(1, line // 2))
    fog = Image.new("RGBA", (w, h), (0, 0, 0, 0))                                      # Nebelband
    ImageDraw.Draw(fog).ellipse((-0.1 * w, 0.8 * h, 1.1 * w, 0.98 * h), fill=FOG + (110,))
    fog = fog.filter(ImageFilter.GaussianBlur(line * 3))
    fog.putalpha(Image.composite(fog.split()[3], Image.new("L", (w, h), 0), mask))
    img.alpha_composite(fog)
    return img


def render_button():
    return GB.render_button("GRAVEYARD", draw_icon_scene, [(0.0, TOP), (0.3, MID), (0.72, MID), (1.0, BOT)], MID,
                            hi_col=(246, 250, 240), dark_col=INK)


def render_icon():
    """Rundes Lobby-Symbol: Glockenturm vor Vollmond, Grabsteine, ein Rabe."""
    c = GI.Icon()
    c.glow(86, 70, 44, (232, 236, 214, 110), 10)
    c.d.ellipse([52 * GI.S, 36 * GI.S, 120 * GI.S, 104 * GI.S], fill=(232, 236, 214, 255))
    stone, stone_l, dark, roof = (92, 98, 112, 255), (128, 136, 152, 255), (22, 24, 30, 255), (52, 56, 70, 255)
    c.rect(112, 120, 172, 220, stone)                                                  # Turmschaft
    c.rect(112, 74, 172, 122, dark)                                                    # Glockenstube
    c.poly([(134, 84), (150, 84), (154, 96), (156, 108), (164, 116), (120, 116), (128, 108), (130, 96)], (204, 156, 84, 255), sh=(0.12, 0.25))   # Glocke
    c.d.ellipse([137 * GI.S, 114 * GI.S, 147 * GI.S, 124 * GI.S], fill=GI.INK)
    c.poly([(104, 76), (180, 76), (142, 22)], roof, sh=(0.1, 0.25))
    c.line([(142, 22), (142, 8)], GI.INK, 6)
    c.line([(134, 14), (150, 14)], GI.INK, 6)
    c.rect(132, 184, 152, 220, (70, 50, 36, 255), lw=6 * GI.S)                        # Tuer
    for x, h_ in ((44, 46), (76, 36), (198, 34), (232, 26)):                           # Grabsteine
        top = 226 - h_ + 16
        c.poly([(x - 16, 226), (x + 16, 226)] + [(x + 16 * math.cos(t), top - 16 * math.sin(t)) for t in [k * math.pi / 10 for k in range(11)]],
               stone_l, sh=(0.1, 0.2))
        c.line([(x, top - 6), (x, top + 8)], (60, 64, 76, 255), 4)
        c.line([(x - 6, top - 1), (x + 6, top - 1)], (60, 64, 76, 255), 4)
    raven = (24, 26, 34, 255)                                                         # Rabe auf dem Grabstein rechts
    c.poly([(178, 176), (190, 168), (186, 182)], raven, sh=(0.0, 0.0))                 # Schwanz
    c.d.ellipse([184 * GI.S, 160 * GI.S, 212 * GI.S, 184 * GI.S], fill=raven, outline=GI.INK, width=5 * GI.S)
    c.d.ellipse([202 * GI.S, 150 * GI.S, 220 * GI.S, 168 * GI.S], fill=raven, outline=GI.INK, width=5 * GI.S)
    c.poly([(218, 156), (232, 160), (218, 163)], (60, 62, 70, 255), sh=(0.0, 0.0))     # Schnabel
    c.d.ellipse([209 * GI.S, 155 * GI.S, 213 * GI.S, 159 * GI.S], fill=(232, 200, 90, 255))
    c.line([(196, 184), (196, 192)], GI.INK, 4)
    c.line([(202, 184), (202, 192)], GI.INK, 4)
    return c.img.resize((256, 256), Image.LANCZOS)


def render(out_dir, key, preview_dir=None):
    b, i = render_button(), render_icon()
    b.save(os.path.join(out_dir, f"button_{key}.png"), optimize=True)
    i.save(os.path.join(out_dir, f"icon_{key}.png"), optimize=True)
    if preview_dir:
        os.makedirs(preview_dir, exist_ok=True)
        s = Image.new("RGBA", (b.width + i.width + 30, max(b.height, i.height) + 20), (40, 52, 70, 255))
        s.alpha_composite(b, (10, 10))
        s.alpha_composite(i, (b.width + 20, 10))
        s.save(os.path.join(preview_dir, "brand_preview.png"))
    return b, i
