# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_art3.py - Ravenhollow Cemetery: Krematorium, Verwaltung, Torhaus, Waechterhaus und alles im Freien
# (Glockenturm, Rabenbaum, Engel, Menhire, Laternenpfaehle, Baenke). Traegt sich ueber graveyard_art.kind() ein.

import math
import random

import graveyard_art as G
from graveyard_art import (BONE, BRASS, BRASS_D, BRASS_L, CREAM, IRON, IRON_D, IRON_L, K, MARBLE, MOSS, OUTLINE, RUST,
                           GRANITE, WOOD, WOOD_D, WOOD_L, OAK, alpha, candle, flame, grass_tufts, hexc, kind, lichen,
                           moss, shade)
import graveyard_art2 as G2
from graveyard_art2 import STONE, STONE_L, STONE_D, STEEL, STEEL_D, STEEL_L, book, skull, planks_front
import handdraw as HD

OUT_W = G.OUT_W
BRICK = hexc("#8a4a3a")
BRICK_D = shade(BRICK, 0.7)
EMBER = hexc("#ff7a2a")
EMBER_L = hexc("#ffc060")
BRONZE = hexc("#9a7240")
BRONZE_L = hexc("#d0a868")
SLATE_ROOF = hexc("#3e4250")
RUNE = hexc("#7ae0d0")


def brick_face(c, x0, x1, yb, yt, col=BRICK, seed=0, bw=0.24, bh=0.075):
    rnd = random.Random(seed)
    rows = max(1, int((yt - yb) / bh))
    for r in range(rows):
        y0 = yb + r * (yt - yb) / rows
        y1 = y0 + (yt - yb) / rows
        off = (r % 2) * bw / 2
        x = x0 - off
        while x < x1:
            a, b = max(x0, x + 0.006), min(x1, x + bw - 0.006)
            if b > a + 0.02:
                c.rect(a, y0 + 0.006, b, y1 - 0.006, fill=shade(col, rnd.uniform(0.85, 1.12)))
            x += bw
        c.line([(x0, y1), (x1, y1)], fill=alpha(shade(col, 0.45), 200), width=0.008)


def stone_face(c, x0, x1, yb, yt, col=STONE, seed=0, sw=0.36, sh=0.17):
    for st in HD.stone_grid(x0, yb, x1, yt, sw, sh, seed=seed, joint=0.02, jitter=0.15, tilt=0.0, skip=0.0, split=0.1, merge=0.05,
                            periodic=False, bond=0.5, rounding=0.05):
        t = 1 + st.tone * 0.1
        pts = [(min(max(x, x0), x1), min(max(y, yb), yt)) for x, y in st.pts]
        c.poly(pts, fill=shade(col, t), outline=alpha(OUTLINE, 220), width=0.012)


# ------------------------------------------------------------------ Krematorium

@kind("ofen", 4.6, pad=1.2)
def _ofen(p, c, x0, y0, x1, y1, idx, rnd):
    """Kremationsofen: gemauerter Block mit Eisentuer (Glut in den Schlitzen), Schienenschlitten davor, Manometer,
    Russfahnen, Schornsteinrohr; warmer Glutschein auf dem Boden."""
    w = x1 - x0
    cx = (x0 + x1) / 2
    H = 2.0
    c.glow(cx, y0 - 0.3, 1.4, EMBER, 0.45)
    p.box(x0, y0, x1, y1, 0, H, shade(BRICK, 0.8), BRICK)
    fy = y0
    brick_face(c, x0 + 0.03, x1 - 0.03, fy + 0.03, fy + H * K - 0.03, seed=idx)
    for k in range(5):                                                                # Russfahne ueber der Tuer
        c.rect(cx - 0.6 + k * 0.08, fy + 0.75, cx + 0.6 - k * 0.08, fy + H * K - 0.02, fill=(10, 8, 8, 34))
    dx0, dx1 = cx - 0.5, cx + 0.5
    dt = fy + 0.82
    arch = [(dx0, fy + 0.1), (dx1, fy + 0.1), (dx1, dt - 0.15)] + [(cx + 0.5 * math.cos(t), dt - 0.15 + 0.17 * math.sin(t)) for t in [j * math.pi / 10 for j in range(11)]] + [(dx0, dt - 0.15)]
    c.poly([(x * 1.0 + (x - cx) * 0.12, y + (0.04 if y > fy + 0.2 else -0.03)) for x, y in arch], fill=hexc("#5a5658"), outline=OUTLINE, width=0.03)   # Steinbogen
    c.poly(arch, fill=IRON, outline=OUTLINE, width=0.035)
    for k in range(4):                                                                # Glutschlitze
        sy = fy + 0.22 + k * 0.1
        c.rect(cx - 0.32, sy, cx + 0.32, sy + 0.035, fill=EMBER, outline=OUTLINE, width=0.01)
        c.rect(cx - 0.28, sy + 0.01, cx + 0.28, sy + 0.025, fill=EMBER_L)
    c.glow(cx, fy + 0.38, 0.6, EMBER, 0.5)
    for (rx, ry) in ((dx0 + 0.06, fy + 0.15), (dx1 - 0.06, fy + 0.15), (dx0 + 0.06, dt - 0.2), (dx1 - 0.06, dt - 0.2)):
        c.ellipse(rx, ry, 0.022, 0.022, fill=IRON_L, outline=OUTLINE, width=0.008)
    c.line([(dx1 - 0.02, fy + 0.45), (dx1 + 0.18, fy + 0.45)], fill=OUTLINE, width=0.05)                         # Griff
    c.line([(dx1 - 0.02, fy + 0.45), (dx1 + 0.18, fy + 0.45)], fill=STEEL, width=0.025)
    gx, gy = x1 - 0.32, fy + 0.85                                                     # Manometer
    c.ellipse(gx, gy, 0.11, 0.11, fill=CREAM, outline=OUTLINE, width=0.025)
    c.ellipse(gx, gy, 0.08, 0.08, outline=BRASS_D, width=0.01)
    c.line([(gx, gy), (gx + 0.06, gy + 0.04)], fill=hexc("#b02020"), width=0.014)
    c.line([(gx, gy - 0.11), (gx, gy - 0.3)], fill=OUTLINE, width=0.035)
    c.line([(gx, gy - 0.11), (gx, gy - 0.3)], fill=STEEL_D, width=0.018)
    ty = y0 + H * K                                                                   # Ofendach: Blech, Russ, Rohr hinten
    tt = y1 + H * K
    c.rect(x0 + 0.05, ty + 0.05, x1 - 0.05, tt - 0.05, fill=hexc("#4a4448"))
    for k in range(1, 5):
        xx = x0 + k * w / 5
        c.line([(xx, ty + 0.06), (xx, tt - 0.06)], fill=alpha(OUTLINE, 160), width=0.012)
        for j in range(4):
            c.ellipse(xx, ty + 0.15 + j * (tt - ty - 0.3) / 3, 0.015, 0.015, fill=hexc("#6a6468"))
    for k in range(6):
        c.poly(HD.wobble_ellipse(rnd.uniform(x0 + 0.3, x1 - 0.3), rnd.uniform(ty + 0.2, tt - 0.2), rnd.uniform(0.15, 0.3), 0.1, amp=0.02, seed=idx + k), fill=(14, 12, 12, 70))
    c.line([(x0 + 0.08, tt - 0.07), (x1 - 0.08, tt - 0.07)], fill=alpha(G.MOON, 90), width=0.015)
    px_, pb = x0 + w * 0.32, tt - 0.25
    c.ellipse(px_, pb, 0.22, 0.09, fill=IRON_D, outline=OUTLINE, width=0.03)
    c.rect(px_ - 0.18, pb, px_ + 0.18, pb + 1.25, fill=IRON_D, outline=OUTLINE, width=0.04)
    for k in range(3):
        c.rect(px_ - 0.2, pb + 0.25 + k * 0.33, px_ + 0.2, pb + 0.3 + k * 0.33, fill=IRON, outline=OUTLINE, width=0.015)
    c.line([(px_ - 0.12, pb + 0.04), (px_ - 0.12, pb + 1.2)], fill=alpha(IRON_L, 200), width=0.02)
    c.ellipse(px_, pb + 1.25, 0.18, 0.07, fill=hexc("#16141a"), outline=OUTLINE, width=0.03)
    for k in range(3):                                                                # Rauch
        c.ellipse(px_ + 0.08 + k * 0.1, pb + 1.45 + k * 0.2, 0.16 + k * 0.06, 0.09 + k * 0.03, fill=alpha((150, 150, 160, 255), 60 - k * 15))
    c.line([(x0 + 0.06, y0 + 0.08), (x0 + 0.1, y0 + 0.6)], fill=hexc("#6a4a30"), width=0.03)                     # Schuerhaken
    c.line([(x0 + 0.1, y0 + 0.6), (x0 + 0.16, y0 + 0.66)], fill=STEEL_D, width=0.02)
    for k in range(2):                                                                # Schienen des Sargschlittens
        sx = cx - 0.3 + k * 0.6
        c.line([(sx, y0 - 0.95), (sx, y0 + 0.08)], fill=OUTLINE, width=0.05)
        c.line([(sx, y0 - 0.95), (sx, y0 + 0.08)], fill=STEEL, width=0.025)
    for k in range(5):
        c.line([(cx - 0.38, y0 - 0.9 + k * 0.22), (cx + 0.38, y0 - 0.9 + k * 0.22)], fill=hexc("#4a3a2e"), width=0.035)


@kind("kohlen", 0.8, pad=0.4)
def _kohlen(p, c, x0, y0, x1, y1, idx, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, d = x1 - x0, y1 - y0
    pile = HD.wobble_ellipse(cx, cy + 0.1, w / 2, d / 2 + 0.15, amp=0.04, seed=idx)
    c.poly(pile, fill=hexc("#1e1e24"), outline=OUTLINE, width=0.03)
    for _ in range(90):
        a = rnd.uniform(0, math.tau)
        rr = rnd.random() ** 0.6
        x = cx + math.cos(a) * w / 2 * rr * 0.9
        y = cy + 0.1 + math.sin(a) * (d / 2 + 0.1) * rr * 0.9 + (1 - rr) * 0.15
        s_ = rnd.uniform(0.03, 0.06)
        q = [(x + s_ * math.cos(t + a), y + s_ * 0.8 * math.sin(t + a)) for t in (0, 1.9, 3.3, 4.8)]
        c.poly(q, fill=rnd.choice([hexc("#26262e"), hexc("#30303a"), hexc("#1a1a20")]), outline=alpha(OUTLINE, 220), width=0.006)
        c.line([q[0], q[1]], fill=alpha(hexc("#7a80a0"), 140), width=0.006)
    sx, sy = cx + w * 0.2, cy + 0.15                                                  # Schaufel im Haufen
    c.line([(sx, sy), (sx + 0.15, sy + 0.55)], fill=OUTLINE, width=0.05)
    c.line([(sx, sy), (sx + 0.15, sy + 0.55)], fill=hexc("#7a5434"), width=0.028)
    c.poly([(sx - 0.09, sy - 0.05), (sx + 0.07, sy - 0.07), (sx + 0.05, sy + 0.1), (sx - 0.07, sy + 0.1)], fill=STEEL_D, outline=OUTLINE, width=0.02)
    c.rect(sx + 0.11, sy + 0.53, sx + 0.21, sy + 0.58, fill=hexc("#7a5434"), outline=OUTLINE, width=0.012)


@kind("aschewagen", 0.9, pad=0.35)
def _aschewagen(p, c, x0, y0, x1, y1, idx, rnd):
    w = x1 - x0
    cx = (x0 + x1) / 2
    for wx in (x0 + 0.15, x1 - 0.15):                                                 # Raeder
        c.ellipse(wx, y0 + 0.1, 0.12, 0.12, fill=IRON_D, outline=OUTLINE, width=0.025)
        c.ellipse(wx, y0 + 0.1, 0.04, 0.04, fill=IRON_L)
    p.box(x0, y0 + 0.08, x1, y1, 0.15, 0.35, IRON_L, IRON)
    ty = y0 + 0.08 + 0.5 * K
    c.rect(x0 + 0.06, ty + 0.04, x1 - 0.06, y1 + 0.5 * K - 0.05, fill=hexc("#8a8682"))
    for _ in range(30):
        c.ellipse(rnd.uniform(x0 + 0.1, x1 - 0.1), rnd.uniform(ty + 0.06, y1 + 0.5 * K - 0.08), 0.03, 0.02, fill=rnd.choice([hexc("#a8a49e"), hexc("#6a6662")]))
    for k, col in enumerate((BRONZE, hexc("#4a5a6a"), hexc("#6a4a3a"))):              # Urnen
        ux, uy = x0 + 0.22 + k * (w - 0.44) / 2, ty + 0.1
        c.poly([(ux - 0.05, uy), (ux + 0.05, uy), (ux + 0.09, uy + 0.12), (ux + 0.06, uy + 0.22), (ux - 0.06, uy + 0.22), (ux - 0.09, uy + 0.12)],
               fill=col, outline=OUTLINE, width=0.015)
        c.rect(ux - 0.05, uy + 0.22, ux + 0.05, uy + 0.26, fill=shade(col, 0.8), outline=OUTLINE, width=0.01)
        c.line([(ux - 0.06, uy + 0.06), (ux - 0.06, uy + 0.18)], fill=alpha(shade(col, 1.4), 200), width=0.01)
    c.line([(x1, y0 + 0.4), (x1 + 0.25, y0 + 0.55)], fill=OUTLINE, width=0.045)                                   # Griff
    c.line([(x1, y0 + 0.4), (x1 + 0.25, y0 + 0.55)], fill=IRON_L, width=0.022)


# ------------------------------------------------------------------ Verwaltung, Torhaus, Waechterhaus

@kind("schreibtisch", 1.5, pad=0.6)
def _schreibtisch(p, c, x0, y0, x1, y1, idx, rnd):
    """Schreibtisch des Totengraebers: Bankerlampe (an), Grabregister, Tintenfass mit Feder, Papiere, Schaedel als
    Briefbeschwerer, Kerzenstummel."""
    w = x1 - x0
    H = 0.85
    for lx in (x0 + 0.04, x1 - 0.12):
        p.box(lx, y0 + 0.03, lx + 0.08, y0 + 0.1, 0, H - 0.05, shade(OAK, 1.1), shade(OAK, 0.8), w=0.03)
    p.box(x0 + 0.05, y0 + 0.08, x0 + 0.5, y1 - 0.05, 0, H - 0.08, shade(OAK, 1.05), shade(OAK, 0.88))           # Schubladenblock
    for k in range(3):
        sy = y0 + 0.08 + 0.05 + k * 0.13
        c.rect(x0 + 0.09, sy, x0 + 0.46, sy + 0.1, outline=alpha(OUTLINE, 220), width=0.01)
        c.rect(x0 + 0.24, sy + 0.04, x0 + 0.31, sy + 0.06, fill=BRASS)
    p.box(x0, y0, x1, y1, H - 0.08, 0.08, shade(OAK, 1.2), OAK)
    ty = y0 + H * K
    c.rect(x0 + 0.5, ty + 0.06, x1 - 0.35, y1 + H * K - 0.08, fill=hexc("#3e5a46"), outline=alpha(OUTLINE, 200), width=0.01)   # Schreibunterlage
    book(c, x0 + 0.78, ty + 0.12, 0.16, 0.14, col=hexc("#4a2a22"), open_=True)
    for k in range(3):                                                                # lose Blaetter
        ax, ay = x0 + 0.22 + k * 0.06, ty + 0.12 + k * 0.02
        c.poly([(ax - 0.1, ay), (ax + 0.08, ay - 0.02), (ax + 0.1, ay + 0.14), (ax - 0.08, ay + 0.16)], fill=hexc("#e0d6bc"), outline=OUTLINE, width=0.008)
        c.line([(ax - 0.06, ay + 0.06), (ax + 0.05, ay + 0.05)], fill=alpha(hexc("#5a4a3a"), 200), width=0.005)
    ix, iy = x1 - 0.5, ty + 0.18                                                      # Tintenfass mit Feder
    c.rect(ix - 0.04, iy, ix + 0.04, iy + 0.06, fill=hexc("#1a1a24"), outline=OUTLINE, width=0.01)
    c.line([(ix + 0.01, iy + 0.06), (ix + 0.12, iy + 0.22)], fill=hexc("#e8e4dc"), width=0.012)
    c.line([(ix + 0.05, iy + 0.12), (ix + 0.12, iy + 0.22)], fill=hexc("#d0ccc4"), width=0.03)
    skull(c, x1 - 0.22, ty + 0.06, 0.8)
    lx, ly = x1 - 0.18, ty + 0.25                                                     # Bankerlampe
    c.glow(lx, ly + 0.2, 0.8, G.WARM, 0.4)
    c.ellipse(lx, ly, 0.06, 0.02, fill=BRASS, outline=OUTLINE, width=0.01)
    c.line([(lx, ly), (lx, ly + 0.2)], fill=BRASS_D, width=0.016)
    c.poly([(lx - 0.13, ly + 0.2), (lx + 0.13, ly + 0.2), (lx + 0.1, ly + 0.28), (lx - 0.1, ly + 0.28)], fill=G2.hexc("#2e6a4a") if hasattr(G2, "hexc") else hexc("#2e6a4a"),
           outline=OUTLINE, width=0.015)
    c.line([(lx - 0.11, ly + 0.2), (lx + 0.11, ly + 0.2)], fill=hexc("#ffe6a8"), width=0.012)
    candle(c, x0 + 0.08, ty + 0.2, 0.05, lit=False, r=0.02, seed=idx)


@kind("aktenschrank", 1.8, pad=0.3)
def _aktenschrank(p, c, x0, y0, x1, y1, idx, rnd):
    H = 1.7
    p.box(x0, y0, x1, y1, 0, H, shade(OAK, 1.18), OAK)
    fy = y0
    cols, rows = 2, 4
    w = (x1 - x0 - 0.1) / cols
    hh = (H * K - 0.12) / rows
    for r in range(rows):
        for k in range(cols):
            dx0 = x0 + 0.05 + k * w
            dy0 = fy + 0.06 + r * hh
            open_ = (r == 1 and k == 0)
            if open_:
                c.rect(dx0 + 0.02, dy0 + 0.02, dx0 + w - 0.02, dy0 + hh - 0.02, fill=hexc("#1e1612"))
                c.rect(dx0 - 0.02, dy0 - 0.06, dx0 + w + 0.02, dy0 + hh * 0.55, fill=shade(OAK, 1.05), outline=OUTLINE, width=0.015)
                for j in range(5):                                                    # Karteikarten
                    c.rect(dx0 + 0.03 + j * 0.06, dy0 + hh * 0.5, dx0 + 0.07 + j * 0.06, dy0 + hh * 0.75, fill=hexc("#e2d8bc"), outline=OUTLINE, width=0.006)
                continue
            c.rect(dx0 + 0.02, dy0 + 0.02, dx0 + w - 0.02, dy0 + hh - 0.02, fill=shade(OAK, 0.95), outline=OUTLINE, width=0.012)
            c.rect(dx0 + w / 2 - 0.05, dy0 + hh * 0.55, dx0 + w / 2 + 0.05, dy0 + hh * 0.7, fill=hexc("#e2d8bc"), outline=OUTLINE, width=0.006)
            c.rect(dx0 + w / 2 - 0.04, dy0 + hh * 0.3, dx0 + w / 2 + 0.04, dy0 + hh * 0.38, fill=BRASS, outline=OUTLINE, width=0.006)
    ty = y0 + H * K
    for k in range(3):
        book(c, x0 + 0.15 + k * 0.17, ty + 0.1 + k * 0.01, 0.15, 0.08, col=[hexc("#5a2228"), hexc("#2a3a4a"), hexc("#3a4a2a")][k])
    G2.candlestick(c, x1 - 0.12, ty + 0.12, 0.12, lit=False, seed=idx)


@kind("kanonenofen", 2.6, pad=0.7)
def _kanonenofen(p, c, x0, y0, x1, y1, idx, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    for a in (-0.6, 0.6):
        c.line([(cx + math.sin(a) * r * 0.7, cy - 0.04), (cx + math.sin(a) * r * 0.5, cy + 0.12)], fill=OUTLINE, width=0.05)
        c.line([(cx + math.sin(a) * r * 0.7, cy - 0.04), (cx + math.sin(a) * r * 0.5, cy + 0.12)], fill=IRON, width=0.028)
    body = cy + 0.12
    c.ellipse(cx, body + 0.35, r * 1.05, 0.42, fill=IRON, outline=OUTLINE, width=OUT_W)
    c.ellipse(cx - r * 0.35, body + 0.48, r * 0.3, 0.18, fill=alpha(IRON_L, 160))
    c.rect(cx - 0.11, body + 0.18, cx + 0.11, body + 0.36, fill=hexc("#2a1a14"), outline=OUTLINE, width=0.015)   # Feuertuer
    for k in range(3):
        c.line([(cx - 0.08 + k * 0.08, body + 0.2), (cx - 0.08 + k * 0.08, body + 0.34)], fill=EMBER, width=0.02)
    c.glow(cx, body + 0.27, 0.55, EMBER, 0.45)
    c.ellipse(cx, body + 0.72, r * 0.8, 0.12, fill=IRON_D, outline=OUTLINE, width=0.03)
    pt = cy + 2.3 * K                                                                 # Ofenrohr
    c.rect(cx - 0.07, body + 0.72, cx + 0.07, pt, fill=IRON_D, outline=OUTLINE, width=0.03)
    c.line([(cx - 0.035, body + 0.75), (cx - 0.035, pt - 0.02)], fill=alpha(IRON_L, 180), width=0.012)
    c.rect(cx - 0.09, pt - 0.3, cx + 0.09, pt - 0.26, fill=IRON, outline=OUTLINE, width=0.012)
    kx = cx + r * 0.45                                                                # Kessel
    c.ellipse(kx, body + 0.78, 0.09, 0.05, fill=hexc("#5a6a7a"), outline=OUTLINE, width=0.015)
    c.line([(kx + 0.08, body + 0.8), (kx + 0.16, body + 0.86)], fill=hexc("#5a6a7a"), width=0.02)
    c.ellipse(kx + 0.03, body + 0.95, 0.06, 0.03, fill=alpha((210, 210, 220, 255), 70))


@kind("waechterpult", 1.4, pad=0.6)
def _waechterpult(p, c, x0, y0, x1, y1, idx, rnd):
    H = 0.95
    p.box(x0, y0, x1, y1, 0, H, shade(OAK, 1.15), shade(OAK, 0.92))
    planks_front(c, x0, x1, y0 + 0.02, y0 + H * K - 0.02, OAK, n=4, seed=idx, vertical=True)
    ty = y0 + H * K
    book(c, x0 + 0.35, ty + 0.1, 0.16, 0.13, col=hexc("#2a2a3a"), open_=True)
    bx, by = x1 - 0.3, ty + 0.12                                                      # Handglocke
    c.poly([(bx - 0.08, by), (bx + 0.08, by), (bx + 0.05, by + 0.12), (bx - 0.05, by + 0.12)], fill=BRASS, outline=OUTLINE, width=0.015)
    c.line([(bx, by + 0.12), (bx, by + 0.22)], fill=hexc("#5a3a24"), width=0.025)
    c.line([(bx - 0.05, by + 0.02), (bx - 0.035, by + 0.1)], fill=BRASS_L, width=0.01)
    for k in range(5):                                                                # Schluesselring
        a = k / 5 * math.tau
        c.line([(x1 - 0.12, ty + 0.3), (x1 - 0.12 + 0.07 * math.cos(a), ty + 0.3 + 0.05 * math.sin(a))], fill=BRASS_D, width=0.012)
    c.ellipse(x1 - 0.12, ty + 0.3, 0.03, 0.025, outline=IRON_L, width=0.01)
    lx, ly = x0 + 0.12, ty + 0.3                                                      # Laterne
    _lantern(c, lx, ly, 0.75, lit=True)


def _lantern(c, x, y, s=1.0, lit=True):
    """Kleine Sturmlaterne (Fuss bei x, y)."""
    if lit:
        c.glow(x, y + 0.14 * s, 0.6 * s, G.WARM, 0.5)
    c.rect(x - 0.07 * s, y, x + 0.07 * s, y + 0.03 * s, fill=IRON, outline=OUTLINE, width=0.012)
    c.rect(x - 0.06 * s, y + 0.03 * s, x + 0.06 * s, y + 0.2 * s, fill=hexc("#ffd890") if lit else hexc("#3a3e48"), outline=OUTLINE, width=0.012)
    if lit:
        c.ellipse(x, y + 0.1 * s, 0.025 * s, 0.045 * s, fill=hexc("#fff4c8"))
    for dx in (-0.06, 0.06):
        c.line([(x + dx * s, y + 0.03 * s), (x + dx * s, y + 0.2 * s)], fill=IRON, width=0.014)
    c.poly([(x - 0.08 * s, y + 0.2 * s), (x + 0.08 * s, y + 0.2 * s), (x, y + 0.27 * s)], fill=IRON, outline=OUTLINE, width=0.012)
    c.ellipse(x, y + 0.3 * s, 0.03 * s, 0.03 * s, outline=IRON, width=0.012)


@kind("bett", 0.9, pad=0.3)
def _bett(p, c, x0, y0, x1, y1, idx, rnd):
    """Pritsche des Waechters (laengs Nord-Sued): Holzrahmen, Strohsack, zerwuehlte Wolldecke, Kissen, Nachttopf,
    Stiefel."""
    H = 0.45
    p.box(x0, y0, x1, y1, 0, H, shade(OAK, 1.1), shade(OAK, 0.9))
    p.box(x0, y1 - 0.08, x1, y1, H, 0.4, shade(OAK, 1.15), OAK, w=0.035)               # Kopfteil (Norden)
    ty = H * K
    c.rect(x0 + 0.05, y0 + ty + 0.04, x1 - 0.05, y1 + ty - 0.1, fill=hexc("#b8a878"), outline=OUTLINE, width=0.015)
    blanket = [(x0 + 0.04, y0 + ty + 0.03), (x1 - 0.04, y0 + ty + 0.05), (x1 - 0.02, y1 + ty - 0.55), (x0 + 0.5, y1 + ty - 0.45), (x0 + 0.02, y1 + ty - 0.6)]
    c.poly(blanket, fill=hexc("#5a6a5a"), outline=OUTLINE, width=0.02)
    for k in range(4):
        c.line([(x0 + 0.08 + k * 0.22, y0 + ty + 0.06), (x0 + 0.12 + k * 0.2, y1 + ty - 0.55)], fill=alpha(hexc("#3e4a3e"), 220), width=0.012)
    c.line([(x0 + 0.04, y0 + ty + 0.12), (x1 - 0.04, y0 + ty + 0.14)], fill=hexc("#8a3a3a"), width=0.02)          # Streifen
    c.ellipse((x0 + x1) / 2, y1 + ty - 0.25, 0.3, 0.12, fill=hexc("#e2dccb"), outline=OUTLINE, width=0.015)
    c.ellipse(x1 + 0.15, y0 + 0.15, 0.09, 0.05, fill=hexc("#c8c0b0"), outline=OUTLINE, width=0.012)                # Nachttopf
    c.ellipse(x1 + 0.15, y0 + 0.17, 0.065, 0.03, fill=hexc("#7a7060"))
    for k in range(2):                                                                # Stiefel
        bx = x0 - 0.12 + k * 0.1
        c.rect(bx - 0.035, y0 + 0.05, bx + 0.035, y0 + 0.25, fill=hexc("#3a2a22"), outline=OUTLINE, width=0.012)
        c.ellipse(bx + 0.02, y0 + 0.05, 0.06, 0.03, fill=hexc("#3a2a22"), outline=OUTLINE, width=0.012)


@kind("tisch", 1.0, pad=0.6)
def _tisch(p, c, x0, y0, x1, y1, idx, rnd):
    H = 0.78
    cx = (x0 + x1) / 2
    for lx in (x0 + 0.06, x1 - 0.12):
        c.rect(lx, y0 + 0.05, lx + 0.06, y0 + 0.05 + H * K, fill=shade(OAK, 0.85), outline=OUTLINE, width=0.02)
    p.box(x0, y0, x1, y1, H - 0.06, 0.06, shade(OAK, 1.2), OAK)
    ty = y0 + H * K
    c.ellipse(cx - 0.2, ty + 0.25, 0.14, 0.07, fill=hexc("#c8c0b0"), outline=OUTLINE, width=0.012)                 # Teller mit Brot
    c.ellipse(cx - 0.2, ty + 0.26, 0.08, 0.04, fill=hexc("#b07a40"), outline=OUTLINE, width=0.01)
    c.rect(cx + 0.1, ty + 0.18, cx + 0.18, ty + 0.3, fill=hexc("#6a6a74"), outline=OUTLINE, width=0.012)          # Becher
    c.ellipse(cx + 0.14, ty + 0.3, 0.04, 0.015, fill=hexc("#3a2a20"))
    for k in range(5):                                                                # Spielkarten
        ax, ay = cx + 0.25 + k * 0.04, ty + 0.1 + (k % 2) * 0.02
        c.rect(ax - 0.035, ay, ax + 0.035, ay + 0.06, fill=hexc("#e8e0cc"), outline=OUTLINE, width=0.006)
        c.ellipse(ax, ay + 0.03, 0.01, 0.01, fill=hexc("#a02a2a") if k % 2 else hexc("#1a1a22"))
    candle(c, cx - 0.45, ty + 0.12, 0.08, lit=True, r=0.025, seed=idx)
    sx = x1 + 0.05                                                                    # Stuhl
    c.rect(sx, y0 + 0.1, sx + 0.06, y0 + 0.1 + 0.45 * K, fill=OAK, outline=OUTLINE, width=0.02)
    p.box(sx, y0 + 0.05, sx + 0.4, y0 + 0.45, 0.45, 0.05, shade(OAK, 1.15), OAK, w=0.03)
    c.rect(sx + 0.34, y0 + 0.45 + 0.45 * K, sx + 0.4, y0 + 0.45 + 0.95 * K, fill=OAK, outline=OUTLINE, width=0.02)


# ------------------------------------------------------------------ im Freien

@kind("glockenturm", 6.4, pad=0.6)
def _glockenturm(p, c, x0, y0, x1, y1, idx, rnd):
    """Glockenturm: Bruchsteinschaft mit Rundbogentuer und Schiessscharte, offene Glockenstube mit Bronzeglocke und
    Seil, Schieferpyramide mit Kreuz und Wetterhahn-Rabe, Moos und Efeu."""
    w = x1 - x0
    cx = (x0 + x1) / 2
    Hs = 3.4                                                                          # Schaft
    c.rect(x0, y0, x1, y0 + Hs * K, fill=STONE, outline=OUTLINE, width=OUT_W)        # nur die Front (Dach deckt die Oberseite)
    fy = y0
    stone_face(c, x0 + 0.03, x1 - 0.03, fy + 0.03, fy + Hs * K - 0.03, seed=idx)
    for k in range(3):                                                                # feuchter Fuss
        c.rect(x0 + 0.03, fy + 0.03, x1 - 0.03, fy + 0.15 * (k + 1), fill=(8, 12, 20, 34))
    dx0, dx1 = cx - 0.38, cx + 0.38                                                   # Tuer
    dt = fy + 1.15
    door = [(dx0, fy + 0.04), (dx1, fy + 0.04), (dx1, dt - 0.38)] + [(cx + 0.38 * math.cos(t), dt - 0.38 + 0.38 * math.sin(t)) for t in [j * math.pi / 12 for j in range(13)]] + [(dx0, dt - 0.38)]
    c.poly([(cx + (x - cx) * 1.2, fy + 0.04 + (y - fy - 0.04) * 1.08) for x, y in door], fill=STONE_L, outline=OUTLINE, width=0.03)
    c.poly(door, fill=hexc("#4a3628"), outline=OUTLINE, width=0.035)
    for k in range(4):
        x = dx0 + 0.15 + k * 0.16
        c.line([(x, fy + 0.06), (x, dt - 0.1 if abs(x - cx) < 0.2 else dt - 0.3)], fill=alpha(OUTLINE, 200), width=0.012)
    for yy in (fy + 0.25, fy + 0.7):                                                  # Beschlaege
        c.line([(dx0 + 0.04, yy), (dx1 - 0.04, yy)], fill=IRON, width=0.035)
        for k in range(5):
            c.ellipse(dx0 + 0.1 + k * 0.14, yy, 0.018, 0.018, fill=IRON_L)
    c.ellipse(cx + 0.22, fy + 0.5, 0.05, 0.05, outline=IRON_L, width=0.015)            # Ring
    c.rect(cx - 0.05, fy + 1.4, cx + 0.05, fy + 1.65, fill=hexc("#0e1016"), outline=OUTLINE, width=0.02)            # Schiessscharte
    vine = HD.wobble([(x0 + 0.1, fy), (x0 + 0.3, fy + 0.6), (x0 + 0.15, fy + 1.1), (x0 + 0.35, fy + 1.5)], amp=0.04, seed=idx, step=0.05)
    c.line(vine, fill=hexc("#2e4a30"), width=0.018)
    for k, (lx, ly) in enumerate(vine[::2]):
        for sgn in (-1, 1):
            c.poly([(lx + sgn * 0.04, ly + 0.03), (lx + sgn * 0.07, ly), (lx + sgn * 0.04, ly - 0.03), (lx + sgn * 0.01, ly)],
                   fill=hexc("#4e7c50") if (k + sgn) % 2 else hexc("#3e6a48"), outline=alpha(OUTLINE, 200), width=0.006)
    moss(c, x1 - 0.3, fy + 0.08, 0.14, seed=idx)
    # Glockenstube: Gesims, offene Bogen, Glocke
    gb = fy + Hs * K
    c.rect(x0 - 0.08, gb - 0.04, x1 + 0.08, gb + 0.1, fill=STONE_L, outline=OUTLINE, width=0.035)
    sb = gb + 0.1
    st = sb + 1.0
    c.rect(x0 + 0.02, sb, x1 - 0.02, st, fill=hexc("#10121a"))                         # Innenraum dunkel
    by = sb + 0.12                                                                    # Glocke
    bell = [(cx - 0.36, by), (cx + 0.36, by), (cx + 0.3, by + 0.08), (cx + 0.22, by + 0.45), (cx + 0.14, by + 0.6), (cx - 0.14, by + 0.6),
            (cx - 0.22, by + 0.45), (cx - 0.3, by + 0.08)]
    c.glow(cx, by + 0.3, 0.6, MOON_GLOW, 0.25)
    c.line([(cx, by + 0.6), (cx, st - 0.05)], fill=OUTLINE, width=0.08)                # Joch
    c.rect(cx - 0.45, st - 0.14, cx + 0.45, st - 0.06, fill=OAK, outline=OUTLINE, width=0.025)
    c.poly(bell, fill=BRONZE, outline=OUTLINE, width=0.04)
    c.poly([(cx - 0.28, by + 0.08), (cx - 0.16, by + 0.08), (cx - 0.1, by + 0.5), (cx - 0.16, by + 0.52)], fill=alpha(BRONZE_L, 200))
    c.line([(cx - 0.33, by + 0.06), (cx + 0.33, by + 0.06)], fill=shade(BRONZE, 0.7), width=0.02)
    c.line([(cx - 0.25, by + 0.36), (cx + 0.25, by + 0.36)], fill=shade(BRONZE, 0.75), width=0.012)
    c.ellipse(cx + 0.05, by - 0.05, 0.05, 0.05, fill=IRON_D, outline=OUTLINE, width=0.012)                           # Kloeppel
    c.line([(cx + 0.18, by + 0.4), (cx + 0.22, sb - 0.1), (cx + 0.2, fy + 1.9)], fill=hexc("#b0946a"), width=0.022)   # Seil
    for sx in (x0, x1 - 0.14):                                                        # Eckpfeiler mit einem weiten Bogen
        c.rect(sx, sb, sx + 0.14, st, fill=STONE, outline=OUTLINE, width=0.03)
        c.line([(sx + 0.03, sb + 0.02), (sx + 0.03, st - 0.02)], fill=alpha(G.MOON, 110), width=0.012)
    for (ax0, ax1) in ((x0 + 0.14, x1 - 0.14),):
        acx, r_ = (ax0 + ax1) / 2, (ax1 - ax0) / 2
        c.poly([(ax0, st), (ax1, st), (ax1, st - 0.1)] + [(acx + r_ * math.cos(t), st - 0.1 - 0.12 * math.sin(t)) for t in [j * math.pi / 10 for j in range(11)]] + [(ax0, st - 0.1)],
               fill=STONE, outline=OUTLINE, width=0.025)
    c.rect(x0 - 0.06, st, x1 + 0.06, st + 0.12, fill=STONE_L, outline=OUTLINE, width=0.03)
    # Pyramidendach mit Schiefer, Kreuz, Rabe
    rb = st + 0.12
    apex = rb + 1.35
    roof = [(x0 - 0.15, rb), (x1 + 0.15, rb), (cx, apex)]
    c.poly(roof, fill=SLATE_ROOF, outline=OUTLINE, width=OUT_W)
    for k in range(7):
        yy = rb + 0.08 + k * 0.17
        t = (yy - rb) / (apex - rb)
        xa = x0 - 0.15 + (cx - x0 + 0.15) * t
        xb = x1 + 0.15 - (x1 + 0.15 - cx) * t
        c.line([(xa + 0.02, yy), (xb - 0.02, yy)], fill=alpha(OUTLINE, 150), width=0.012)
        n = max(1, int((xb - xa) / 0.12))
        for j in range(n):
            sx = xa + (j + 0.5 + (k % 2) * 0.5) * (xb - xa) / (n + 0.5)
            c.line([(sx, yy), (sx, yy - 0.15)], fill=alpha(OUTLINE, 100), width=0.008)
    c.line([(x0 - 0.1, rb + 0.02), (cx - 0.05, apex - 0.05)], fill=alpha(G.MOON, 120), width=0.025)
    c.line([(cx, apex), (cx, apex + 0.4)], fill=OUTLINE, width=0.05)
    c.line([(cx, apex), (cx, apex + 0.4)], fill=IRON, width=0.03)
    c.line([(cx - 0.12, apex + 0.28), (cx + 0.12, apex + 0.28)], fill=OUTLINE, width=0.05)
    c.line([(cx - 0.12, apex + 0.28), (cx + 0.12, apex + 0.28)], fill=IRON, width=0.03)
    G.raven(c, cx + 0.02, apex + 0.42, 1, 0.9)


MOON_GLOW = hexc("#c4d4ea")


@kind("engel", 2.6, pad=0.6)
def _engel(p, c, x0, y0, x1, y1, idx, rnd):
    """Weinender Engel der alten Graeber, neu 24.10. (User: "alle Statuen neu und detailreicher"): zweistufiger
    Marmorsockel mit Inschrift und Kranz, Engel im langen Gewand mit Faltenwurf und Guertel, Oberkoerper leicht
    gebeugt, Haende vor dem Gesicht (ein Auge blickt hindurch), langes Haar, grosse ausgebreitete Fluegel mit drei
    Federreihen, Moos und Flechten, Risse."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = (x1 - x0) / 2
    col = shade(MARBLE, 0.94)
    col_l, col_d = shade(col, 1.08), shade(col, 0.72)
    p.box(cx - r - 0.05, cy - r * 0.7, cx + r + 0.05, cy + r * 0.7, 0, 0.18, col_l, shade(col, 0.82))
    p.box(cx - r * 0.78, cy - r * 0.55, cx + r * 0.78, cy + r * 0.55, 0.18, 0.5, col_l, shade(col, 0.9))
    fy = cy - r * 0.55
    c.rect(cx - r * 0.6, fy + 0.26 * K, cx + r * 0.6, fy + 0.6 * K, outline=alpha(col_d, 220), width=0.012)
    c.text(cx, fy + 0.43 * K, "REQUIESCAT", 0.045, col_d)
    for k in range(3):
        c.line([(cx - r * 0.7 + k * r * 0.7, cy - r * 0.68), (cx - r * 0.7 + k * r * 0.7, cy - r * 0.7 + 0.16 * K)], fill=alpha(col_d, 170), width=0.01)
    G.wreath(c, cx + r * 0.5, cy - r * 0.76, 0.14, rnd)
    base = cy - r * 0.2 + 0.68 * K
    # Fluegel (hinten): drei Federreihen, Lichtkante
    for sx in (-1, 1):
        wing = [(cx + sx * 0.1, base + 0.5), (cx + sx * 0.3, base + 0.95), (cx + sx * 0.58, base + 1.45), (cx + sx * 0.7, base + 1.25),
                (cx + sx * 0.68, base + 0.8), (cx + sx * 0.56, base + 0.42), (cx + sx * 0.36, base + 0.18), (cx + sx * 0.18, base + 0.14)]
        c.poly(wing, fill=col_l, outline=OUTLINE, width=0.035)
        for row in range(3):
            for k in range(4):
                t = 0.15 + k * 0.22
                fx = cx + sx * (0.16 + 0.5 * t + row * 0.04)
                fyy = base + 0.22 + 1.0 * t - row * 0.17
                c.line([(fx, fyy), (fx - sx * 0.03, fyy - 0.14)], fill=alpha(col_d, 170), width=0.01)
                c.ellipse(fx - sx * 0.03, fyy - 0.15, 0.028, 0.02, outline=alpha(col_d, 170), width=0.008)
        c.line([(cx + sx * 0.32, base + 0.98), (cx + sx * 0.58, base + 1.4)], fill=alpha((255, 255, 255, 255), 100), width=0.016)
    # Gewand mit Falten, Saum, Guertel
    gown = HD.wobble([(cx - 0.3, base), (cx + 0.3, base), (cx + 0.23, base + 0.7), (cx + 0.18, base + 1.1), (cx - 0.18, base + 1.1), (cx - 0.23, base + 0.7)],
                     amp=0.012, seed=idx, step=0.06, closed=True)
    c.poly(gown, fill=col, outline=OUTLINE, width=0.035)
    for k in range(5):
        c.line(HD.wobble([(cx - 0.14 + k * 0.07, base + 1.05), (cx - 0.22 + k * 0.11, base + 0.04)], amp=0.01, seed=idx + k, step=0.05), fill=alpha(col_d, 170), width=0.012)
    c.line([(cx - 0.2, base + 0.1), (cx - 0.14, base + 1.0)], fill=alpha((255, 255, 255, 255), 100), width=0.02)
    for k in range(4):
        c.ellipse(cx - 0.22 + k * 0.15, base, 0.07, 0.03, fill=col, outline=OUTLINE, width=0.014)
    c.ellipse(cx + 0.08, base + 0.02, 0.07, 0.03, fill=col_l, outline=OUTLINE, width=0.012)
    c.rect(cx - 0.17, base + 1.05, cx + 0.17, base + 1.11, fill=col_d, outline=OUTLINE, width=0.012)
    # Oberkoerper, Kopf, Haar, Arme, Haende
    c.poly([(cx - 0.2, base + 1.1), (cx + 0.2, base + 1.1), (cx + 0.16, base + 1.38), (cx - 0.16, base + 1.38)], fill=col, outline=OUTLINE, width=0.035)
    hy = base + 1.47
    c.ellipse(cx, hy, 0.13, 0.14, fill=col_l, outline=OUTLINE, width=0.03)
    c.ellipse(cx - 0.01, hy + 0.08, 0.145, 0.085, fill=col, outline=OUTLINE, width=0.015)
    for k in range(4):
        c.line([(cx - 0.1 + k * 0.065, hy + 0.14), (cx - 0.13 + k * 0.08, hy - 0.02)], fill=alpha(col_d, 160), width=0.01)
    for sx in (-1, 1):
        c.line([(cx + sx * 0.18, base + 1.26), (cx + sx * 0.2, base + 1.38), (cx + sx * 0.06, hy - 0.02)], fill=OUTLINE, width=0.075)
        c.line([(cx + sx * 0.18, base + 1.26), (cx + sx * 0.2, base + 1.38), (cx + sx * 0.06, hy - 0.02)], fill=col_l, width=0.045)
    c.poly([(cx - 0.1, hy - 0.1), (cx + 0.1, hy - 0.1), (cx + 0.11, hy + 0.05), (cx - 0.11, hy + 0.05)], fill=shade(col_l, 1.06), outline=OUTLINE, width=0.015)
    for k in range(5):
        c.line([(cx - 0.08 + k * 0.04, hy - 0.08), (cx - 0.08 + k * 0.04, hy + 0.03)], fill=alpha(col_d, 180), width=0.006)
    c.ellipse(cx + 0.045, hy - 0.02, 0.01, 0.014, fill=hexc("#1a1e2a"))
    c.line([(cx + 0.03, hy - 0.1), (cx + 0.035, hy - 0.22)], fill=alpha(hexc("#1a1e2a"), 150), width=0.01)      # Traenenspur
    G.crack(c, [(cx - 0.1, base + 0.2), (cx - 0.05, base + 0.5), (cx - 0.12, base + 0.8)], seed=idx)
    lichen(c, cx - 0.5, base, cx + 0.5, base + 1.2, 12, seed=idx)
    moss(c, cx - r * 0.5, cy - r * 0.6 + 0.05, 0.1, seed=idx)
    moss(c, cx + r * 0.3, cy - r * 0.55 + 0.3, 0.08, seed=idx + 1)


@kind("rabenbaum", 5.4, pad=2.8)
def _rabenbaum(p, c, x0, y0, x1, y1, idx, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    G.tree_dead(c, cx, cy - 0.3, 5.0, rnd, seed=idx + 3, ravens=0)
    for k, (dx, dy, f) in enumerate(((-1.2, 3.4, 1), (0.9, 3.9, -1), (-0.4, 4.4, 1), (1.6, 3.1, -1), (0.3, 3.0, 1), (-1.8, 2.7, -1))):
        G.raven(c, cx + dx, cy + dy, f, 1.1)
    _lantern(c, cx + 0.65, cy + 1.5, 0.9, lit=True)                                    # Laterne am Ast
    c.line([(cx + 0.65, cy + 1.77), (cx + 0.6, cy + 2.15)], fill=IRON, width=0.012)


@kind("menhir", 2.0, pad=0.6)
def _menhir(p, c, x0, y0, x1, y1, idx, rnd):
    """Menhir der Waechtersteine: unregelmaessiger Langstein, eingeritzte Runen mit schwachem Tuerkisglimmen,
    Flechten, Moos, Kerzenstummel und Opfergaben am Fuss."""
    cx = (x0 + x1) / 2
    w = x1 - x0
    H = (1.6 + 0.25 * (idx % 3)) * K
    yb = y0 + 0.05
    sh_ = [(x0 + 0.02, yb), (x1 - 0.04, yb), (x1 + 0.02, yb + H * 0.4), (x1 - 0.06, yb + H * 0.85), (cx + w * 0.15, yb + H),
           (cx - w * 0.2, yb + H * 0.95), (x0 + 0.04, yb + H * 0.7), (x0 - 0.02, yb + H * 0.3)]
    sh_ = HD.wobble(sh_ + [sh_[0]], amp=0.02, seed=idx, step=0.1)[:-1]
    c.poly([(x + 0.06, y + 0.1) for x, y in sh_], fill=shade(STONE, 1.2), outline=OUTLINE, width=OUT_W)
    c.poly(sh_, fill=shade(STONE, 0.95), outline=OUTLINE, width=OUT_W)
    c.line([(x0 + 0.06, yb + 0.1), (x0 + 0.04, yb + H * 0.65)], fill=alpha(G.MOON, 120), width=0.02)
    glyphs = [[(0, 0), (0, 0.16), (0.07, 0.1)], [(0, 0), (0.06, 0.16), (0.12, 0)], [(0, 0.16), (0.06, 0.08), (0, 0), (0.06, -0.02)], [(0, 0), (0, 0.16), (0.08, 0.16)]]
    for k in range(3):
        g = glyphs[(idx + k) % len(glyphs)]
        gx, gy = cx - 0.06, yb + H * (0.25 + k * 0.22)
        pts = [(gx + px_, gy + py_) for px_, py_ in g]
        c.line(pts, fill=alpha(RUNE, 70), width=0.05)
        c.line(pts, fill=alpha(shade(STONE, 0.5), 255), width=0.02)
        c.line(pts, fill=alpha(RUNE, 200), width=0.008)
    c.glow(cx, yb + H * 0.45, 0.5, RUNE, 0.15)
    lichen(c, x0, yb, x1, yb + H, 12, seed=idx)
    moss(c, x0 + 0.1, yb + 0.05, 0.1, seed=idx)
    for k in range(2):
        candle(c, x0 - 0.1 + k * (w + 0.2), y0 - 0.1, 0.05 + 0.03 * k, lit=(idx + k) % 2 == 0, r=0.022, seed=idx + k)
    if idx % 2:
        G.bouquet(c, x1 + 0.05, y0 - 0.12, rnd, dead=True, s=0.8)


@kind("laternenpfahl", 2.8, pad=1.4, variants=("off",))
def _laternenpfahl(p, c, x0, y0, x1, y1, idx, rnd, variant=None):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    top = cy + 2.3 * K
    lit = variant != "off"
    if lit:
        c.glow(cx, top + 0.15, 1.2, G.WARM, 0.35)
    c.ellipse(cx, cy, 0.14, 0.06, fill=IRON, outline=OUTLINE, width=0.025)
    c.rect(cx - 0.06, cy, cx + 0.06, cy + 0.2, fill=IRON, outline=OUTLINE, width=0.025)
    c.line([(cx, cy + 0.2), (cx, top)], fill=OUTLINE, width=0.07)
    c.line([(cx, cy + 0.2), (cx, top)], fill=IRON, width=0.04)
    c.line([(cx - 0.012, cy + 0.22), (cx - 0.012, top - 0.02)], fill=alpha(IRON_L, 200), width=0.01)
    for sx in (-1, 1):                                                                # Zierschnoerkel
        c.line([(cx, top - 0.25), (cx + sx * 0.1, top - 0.18), (cx + sx * 0.08, top - 0.08)], fill=OUTLINE, width=0.035)
        c.line([(cx, top - 0.25), (cx + sx * 0.1, top - 0.18), (cx + sx * 0.08, top - 0.08)], fill=IRON, width=0.016)
    c.rect(cx - 0.12, top, cx + 0.12, top + 0.04, fill=IRON, outline=OUTLINE, width=0.015)
    c.poly([(cx - 0.1, top + 0.04), (cx + 0.1, top + 0.04), (cx + 0.13, top + 0.3), (cx - 0.13, top + 0.3)],
           fill=hexc("#ffd890") if lit else hexc("#2e3440"), outline=OUTLINE, width=0.02)
    if lit:
        c.ellipse(cx, top + 0.16, 0.035, 0.07, fill=hexc("#fff4c8"))
    else:
        c.line([(cx - 0.06, top + 0.08), (cx - 0.03, top + 0.26)], fill=alpha(G.MOON, 120), width=0.014)
        c.line([(cx, top + 0.1), (cx, top + 0.15)], fill=OUTLINE, width=0.01)
    for dx in (-0.115, 0.0, 0.115):
        c.line([(cx + dx * 0.9, top + 0.04), (cx + dx * 1.1, top + 0.3)], fill=IRON, width=0.014)
    c.poly([(cx - 0.17, top + 0.3), (cx + 0.17, top + 0.3), (cx, top + 0.46)], fill=IRON, outline=OUTLINE, width=0.02)
    c.ellipse(cx, top + 0.49, 0.03, 0.03, fill=IRON, outline=OUTLINE, width=0.01)
    if idx % 3 == 1:
        G.raven(c, cx + 0.02, top + 0.5, -1 if idx % 2 else 1, 0.9)


@kind("parkbank", 1.0, pad=0.35)
def _parkbank(p, c, x0, y0, x1, y1, idx, rnd):
    """Friedhofsbank: gusseiserne Wangen mit Schnoerkel, Sitz- und Lehnenlatten, Laub darauf."""
    H = 0.45
    for sx in (x0 + 0.06, x1 - 0.06):
        for col_, wd in ((OUTLINE, 0.06), (IRON, 0.035)):
            c.line([(sx, y0 + 0.02), (sx, y0 + H * K), (sx + 0.0, y1 + 0.85 * K)], fill=col_, width=wd)
        c.line([(sx, y0 + H * K - 0.05), (sx + 0.05, y0 + H * K - 0.12), (sx + 0.02, y0 + 0.08)], fill=IRON, width=0.016)
    for k in range(3):                                                                # Sitzlatten
        yy = y0 + 0.04 + k * 0.11
        p.box(x0, yy, x1, yy + 0.09, H, 0.035, shade(OAK, 1.2), OAK, w=0.025)
    for k in range(3):                                                                # Lehnenlatten
        yy = y1 + (0.55 + k * 0.12) * K
        c.rect(x0 + 0.02, yy, x1 - 0.02, yy + 0.06, fill=shade(OAK, 1.05), outline=OUTLINE, width=0.022)
        c.line([(x0 + 0.05, yy + 0.045), (x1 - 0.05, yy + 0.045)], fill=alpha(shade(OAK, 1.35), 200), width=0.008)
    for _ in range(5):
        lx, ly = rnd.uniform(x0 + 0.1, x1 - 0.1), y0 + 0.1 + H * K + rnd.uniform(0, 0.25)
        a = rnd.uniform(0, math.pi)
        c.poly([(lx + 0.05 * math.cos(a), ly + 0.05 * math.sin(a)), (lx - 0.02 * math.sin(a), ly + 0.02 * math.cos(a)),
                (lx - 0.05 * math.cos(a), ly - 0.05 * math.sin(a)), (lx + 0.02 * math.sin(a), ly - 0.02 * math.cos(a))],
               fill=rnd.choice(G.LEAF), outline=alpha(OUTLINE, 160), width=0.006)
