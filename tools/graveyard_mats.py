# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_mats.py - Materialkacheln und Wandstirnseiten fuer Ravenhollow Cemetery.
#
# Baut auf villa_floor.py auf (Sheet mit Supersampling und nahtlosem Kachelmodus, mottle, edge_light, shrink,
# leaf, tufts) und auf Atlas handdraw.py (stone_grid, jitter_grid, wobble, ink, crack, chip). Alle Kacheln sind
# nahtlos (TILE_M x TILE_M m), Bildkoordinaten u rechts / v unten in Metern.
#
# Palette "Mondnacht": kuehles Blaugruen im Gras, blaugrauer Stein, Holz eher grau-braun als warm; warme Toene
# nur dort, wo Licht ist (Kerzen, Ofen, Laternen). Werte wie bei der Villa fuer 2D angehoben, weil das Spiel
# ausserhalb des Sichtkegels abdunkelt.

import math
import random

from PIL import Image, ImageDraw, ImageFilter

import villa_floor as VF
from villa_floor import Sheet, _tone, _tint, edge_light, leaf, mottle, shrink, tufts
import handdraw as HD

TILE_M = VF.TILE_M

INK = (24, 24, 30, 255)
MOSS = (84, 120, 70)
MOSS_L = (112, 150, 86)
LICHEN = (176, 184, 128)
BONE = (214, 206, 186)
IRON = (58, 58, 66)
IRON_L = (100, 100, 112)
RUST = (150, 82, 40)
CANDLE = (255, 232, 170)
GLASS_COLS = [(150, 40, 52), (40, 70, 140), (196, 150, 52), (52, 120, 80), (110, 52, 120)]


# ------------------------------------------------------------------ Boeden

def tile_nachtgras(ppm, seed=1, base=(50, 74, 62)):
    """Kurzes, feuchtes Friedhofsgras bei Nacht: blaugruen, Kleeflecken, Moospolster, kahle Erde, Laub,
    Eicheln und kleine Pilze, viele feine Halmbueschel in drei Toenen."""
    T = TILE_M
    sh = Sheet(T, T, ppm, base, periodic=True)
    rnd = random.Random(seed)
    for _ in range(5):                                                                # Toenung (gross, weich)
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), rnd.uniform(0.35, 0.6), rnd.uniform(0.25, 0.4),
                                  amp=0.06, seed=rnd.randint(0, 999)), fill=(36, 58, 50, 70))
    for _ in range(3):                                                                # kahle Erde
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), rnd.uniform(0.12, 0.22), rnd.uniform(0.08, 0.14),
                                  amp=0.03, seed=rnd.randint(0, 999)), fill=(78, 66, 54, 150))
    for _ in range(4):                                                                # Moospolster
        cx, cy = rnd.uniform(0, T), rnd.uniform(0, T)
        for k in range(9):
            sh.ellipse(cx + rnd.uniform(-0.12, 0.12), cy + rnd.uniform(-0.08, 0.08), rnd.uniform(0.03, 0.06), rnd.uniform(0.02, 0.04),
                       fill=MOSS + (150,))
        for k in range(6):
            sh.ellipse(cx + rnd.uniform(-0.1, 0.1), cy + rnd.uniform(-0.07, 0.07), 0.012, 0.01, fill=MOSS_L + (190,))
    for _ in range(5):                                                                # Klee
        cx, cy = rnd.uniform(0, T), rnd.uniform(0, T)
        for k in range(7):
            x, y = cx + rnd.uniform(-0.15, 0.15), cy + rnd.uniform(-0.1, 0.1)
            for a in (0, 2.1, 4.2):
                sh.ellipse(x + 0.014 * math.cos(a), y + 0.014 * math.sin(a), 0.012, 0.012, fill=(70, 112, 78, 220))
    tufts(sh, rnd, 520, [(84, 118, 90), (46, 70, 60), (104, 128, 96), (66, 96, 74)], h=0.075)
    for _ in range(12):                                                               # Laub
        leaf(sh, rnd.uniform(0, T), rnd.uniform(0, T), rnd.uniform(0.06, 0.1), rnd.uniform(0, math.pi),
             rnd.choice([(150, 86, 46), (124, 70, 44), (168, 124, 60), (110, 62, 50)]))
    for _ in range(3):                                                                # Eicheln
        x, y = rnd.uniform(0, T), rnd.uniform(0, T)
        sh.ellipse(x, y, 0.018, 0.024, fill=(130, 98, 56), outline=(50, 36, 24), width=0.005)
        sh.ellipse(x, y - 0.016, 0.02, 0.01, fill=(96, 80, 54), outline=(50, 36, 24), width=0.005)
    if rnd.random() < 0.8:                                                            # Pilzgruppe (Hut von oben)
        cx, cy = rnd.uniform(0.2, T - 0.2), rnd.uniform(0.2, T - 0.2)
        for k in range(rnd.randint(2, 4)):
            x, y, r = cx + rnd.uniform(-0.06, 0.06), cy + rnd.uniform(-0.05, 0.05), rnd.uniform(0.018, 0.03)
            sh.ellipse(x + 0.006, y + 0.006, r, r * 0.8, fill=(20, 30, 26, 120))
            sh.ellipse(x, y, r, r * 0.8, fill=(204, 190, 160), outline=(70, 56, 44), width=0.005)
            sh.ellipse(x - r * 0.3, y - r * 0.3, r * 0.35, r * 0.25, fill=(236, 228, 210))
    for _ in range(4):                                                                # Zweige
        x, y = rnd.uniform(0, T), rnd.uniform(0, T)
        a = rnd.uniform(0, math.pi)
        ln = rnd.uniform(0.1, 0.24)
        pts = HD.wobble([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], amp=0.008, seed=rnd.randint(0, 99), step=0.04)
        sh.line(pts, fill=(64, 50, 38), width=0.01)
    return mottle(sh.finish(seed=seed), 0.07, seed + 3, periods=(2, 3, 6))


GRASS_T = 4.0                 # Graskacheln 4 m statt 2 m: weniger sichtbare Wiederholung


def _patches(sh, rnd, T, n, rmin, rmax, col, amp=0.06):
    for _ in range(n):
        x, y = rnd.uniform(0, T), rnd.uniform(0, T)
        r = rnd.uniform(rmin, rmax)
        sh.poly(HD.wobble_ellipse(x, y, r, r * rnd.uniform(0.55, 0.85), amp=r * amp * 2, seed=rnd.randint(0, 99999)), fill=col)


def _soften(sh, radius_m):
    """Bisher Gezeichnetes nahtlos weichzeichnen (3x3 gekachelt, Mitte ausschneiden)."""
    im = sh.img
    w, h = im.size
    big = Image.new(im.mode, (w * 3, h * 3))
    for i in range(3):
        for j in range(3):
            big.paste(im, (i * w, j * h))
    big = big.filter(ImageFilter.GaussianBlur(max(1, radius_m * sh.sx)))
    sh.img = big.crop((w, h, 2 * w, 2 * h))
    sh.d = ImageDraw.Draw(sh.img, "RGBA")


def _blade_tuft(sh, x, y, rnd, h, cols, w=0.016, n=None):
    """Halmbueschel in Aufsicht-Schraege: 3-6 spitze Halme (schmale Dreiecke) faecherfoermig nach oben, dunkler
    Halm hinten, heller vorne; v nach unten, also Halme zu kleinerem v."""
    n = n or rnd.randint(3, 6)
    dark, mid, light = cols
    for k in range(n):
        a = math.radians(rnd.uniform(-38, 38))
        ln = h * rnd.uniform(0.6, 1.15)
        bx = x + rnd.uniform(-0.03, 0.03)
        tx, ty = bx + math.sin(a) * ln, y - math.cos(a) * ln
        col = dark if k == 0 else (light if k == n - 1 else mid)
        sh.poly([(bx - w, y), (bx + w, y), (tx, ty)], fill=col)


def tile_rasen(ppm, seed=1, base=(70, 102, 78)):
    """Begehbarer Friedhofsrasen (Lichtungen): ruhige, kuehle Gruenflaechen in drei Stufen (Cel-Schattierung mit
    weichen Klecksen), wenige klare Halmbueschel, Kleefelder, Gaensebluemchen, ein paar Herbstblaetter."""
    Tm = GRASS_T
    sh = Sheet(Tm, Tm, ppm, base, periodic=True)
    rnd = random.Random(seed)
    dark, light = _tone(base, 0.92), _tone(base, 1.06)
    _patches(sh, rnd, Tm, 9, 0.5, 1.0, dark + (255,))
    _patches(sh, rnd, Tm, 7, 0.35, 0.8, light + (255,))
    _patches(sh, rnd, Tm, 10, 0.12, 0.3, _tone(base, 0.9) + (255,))
    _soften(sh, 0.06)
    _patches(sh, rnd, Tm, 8, 0.08, 0.18, _tone(base, 1.06) + (255,))                  # kleine, scharfe Flecken obendrauf
    for _ in range(3):                                                                # ausgetretene, kahle Stellen
        x, y = rnd.uniform(0, Tm), rnd.uniform(0, Tm)
        sh.poly(HD.wobble_ellipse(x, y, rnd.uniform(0.15, 0.3), rnd.uniform(0.08, 0.16), amp=0.03, seed=rnd.randint(0, 999)), fill=(92, 84, 66, 140))
    cols = (_tone(base, 0.68), _tone(base, 0.95), _tone(base, 1.3))
    for _ in range(int(Tm * Tm * 9)):                                                 # Halmbueschel, locker verteilt
        _blade_tuft(sh, rnd.uniform(0, Tm), rnd.uniform(0, Tm), rnd, rnd.uniform(0.07, 0.12), cols)
    for _ in range(int(Tm * Tm * 1.2)):                                               # Klee
        cx, cy = rnd.uniform(0, Tm), rnd.uniform(0, Tm)
        for k in range(rnd.randint(4, 8)):
            x, y = cx + rnd.uniform(-0.12, 0.12), cy + rnd.uniform(-0.08, 0.08)
            for a in (90, 210, 330):
                sh.ellipse(x + 0.016 * math.cos(math.radians(a)), y - 0.016 * math.sin(math.radians(a)), 0.016, 0.015, fill=_tone(base, 1.28))
            sh.ellipse(x, y, 0.006, 0.006, fill=_tone(base, 0.8))
    for _ in range(int(Tm * Tm * 0.5)):                                               # Gaensebluemchen (bei Nacht gedeckt)
        x, y = rnd.uniform(0, Tm), rnd.uniform(0, Tm)
        for a in range(0, 360, 45):
            sh.ellipse(x + 0.022 * math.cos(math.radians(a)), y + 0.022 * math.sin(math.radians(a)), 0.012, 0.012, fill=(214, 218, 220))
        sh.ellipse(x, y, 0.012, 0.012, fill=(226, 196, 86))
    for _ in range(int(Tm * Tm * 0.8)):
        leaf(sh, rnd.uniform(0, Tm), rnd.uniform(0, Tm), rnd.uniform(0.07, 0.11), rnd.uniform(0, math.pi),
             rnd.choice([(160, 92, 48), (132, 74, 46), (176, 130, 62), (116, 64, 52)]))
    return mottle(sh.finish(grain=0.02, seed=seed), 0.05, seed + 3, periods=(1, 2, 3))


def tile_wildgras(ppm, seed=1, base=(38, 58, 52)):
    """Nicht begehbares Grabfeld-Gras: dunkel und ruhig (liest sich wie der Leerraum der Atlas-Karten), grosse
    weiche Flaechen, vereinzelt hohe Grasbueschel, Farn, Brennnesselgruppen, wenig Laub."""
    Tm = GRASS_T
    sh = Sheet(Tm, Tm, ppm, base, periodic=True)
    rnd = random.Random(seed)
    _patches(sh, rnd, Tm, 8, 0.6, 1.2, _tone(base, 0.85) + (255,))
    _patches(sh, rnd, Tm, 6, 0.4, 0.9, _tone(base, 1.1) + (255,))
    _soften(sh, 0.18)
    cols = (_tone(base, 0.7), _tone(base, 1.08), _tone(base, 1.4))
    for _ in range(int(Tm * Tm * 2.2)):                                               # hohe Bueschel
        _blade_tuft(sh, rnd.uniform(0, Tm), rnd.uniform(0, Tm), rnd, rnd.uniform(0.14, 0.22), cols, w=0.02, n=rnd.randint(5, 8))
    for _ in range(int(Tm * Tm * 0.25)):                                              # Farn
        x, y = rnd.uniform(0, Tm), rnd.uniform(0, Tm)
        for k in range(5):
            a = math.radians(-70 + k * 35)
            ln = 0.22
            tx, ty = x + math.sin(a) * ln, y - math.cos(a) * ln
            sh.line([(x, y), (tx, ty)], fill=_tone(base, 1.45), width=0.012)
            for j in range(1, 6):
                t = j / 6
                px_, py_ = x + (tx - x) * t, y + (ty - y) * t
                for sgn in (-1, 1):
                    sh.line([(px_, py_), (px_ + math.cos(a) * 0.04 * sgn * (1 - t), py_ + math.sin(a) * 0.04 * sgn * (1 - t))],
                            fill=_tone(base, 1.3), width=0.01)
    for _ in range(int(Tm * Tm * 0.3)):
        leaf(sh, rnd.uniform(0, Tm), rnd.uniform(0, Tm), rnd.uniform(0.07, 0.1), rnd.uniform(0, math.pi),
             rnd.choice([(120, 72, 44), (100, 60, 42), (132, 98, 52)]))
    return mottle(sh.finish(grain=0.015, seed=seed), 0.06, seed + 5, periods=(1, 2, 3))


def tile_kies(ppm, seed=1, base=(96, 96, 98)):
    """Friedhofskies: kuehles Grau, dichter als der Villa-Kies, Fahrspuren aus Pfuetzen, einzelne Blaetter."""
    T = TILE_M
    sh = Sheet(T, T, ppm, base, periodic=True)
    rnd = random.Random(seed)
    for _ in range(6):
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.35, 0.2, amp=0.04, seed=rnd.randint(0, 99)), fill=(70, 70, 74, 60))
    pal = [(118, 118, 122), (134, 130, 124), (100, 98, 104), (150, 148, 144), (112, 106, 100), (86, 86, 92)]
    for i in range(1100):
        x, y = rnd.uniform(0, T), rnd.uniform(0, T)
        rx, ry = rnd.uniform(0.012, 0.034), rnd.uniform(0.01, 0.026)
        a = rnd.uniform(0, math.pi)
        col = _tone(rnd.choice(pal), 1 + rnd.uniform(-0.08, 0.08))
        pts = [(x + rx * math.cos(t) * math.cos(a) - ry * math.sin(t) * math.sin(a), y + rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a))
               for t in [k * math.tau / 8 for k in range(8)]]
        sh.poly(pts, fill=col, outline=_tone(col, 0.5) + (180,), width=0.005)
        sh.ellipse(x - rx * 0.3, y - ry * 0.35, rx * 0.3, ry * 0.28, fill=(225, 232, 245, 45))
    for _ in range(4):
        leaf(sh, rnd.uniform(0, T), rnd.uniform(0, T), rnd.uniform(0.06, 0.09), rnd.uniform(0, math.pi),
             rnd.choice([(150, 86, 46), (124, 70, 44), (168, 124, 60)]))
    return mottle(sh.finish(seed=seed), 0.06, seed + 5)


def tile_kopfstein(ppm, seed=1, base=(104, 106, 114), joint=(52, 56, 52)):
    """Kopfsteinpflaster in Boegen (Brunnenhaus, Torhaus, Glockenplatz): runde Steine, Moos in den Fugen."""
    T = TILE_M
    sh = Sheet(T, T, ppm, joint, periodic=True)
    rnd = random.Random(seed)
    R = 0.5                                                                           # Bogenradius (Segmentpflaster)
    rows = int(T / 0.12)
    for r in range(rows):
        v = r * T / rows
        u = 0.0
        while u < T:
            w = rnd.uniform(0.1, 0.15)
            cu, cv = u + w / 2, v + 0.06 + 0.03 * math.cos((u % R) / R * math.tau)
            pts = HD.wobble_ellipse(cu, cv, w / 2 - 0.008, 0.052, amp=0.008, seed=r * 97 + int(u * 100))
            col = _tint(_tone(base, 1 + rnd.uniform(-0.14, 0.12)), rnd.choice([(1, 1, 1), (1.05, 1.0, 0.94), (0.94, 0.98, 1.06), (1, 1, 1)]))
            sh.poly(pts, fill=col)
            sh.ellipse(cu - w * 0.14, cv - 0.018, w * 0.2, 0.016, fill=_tone(col, 1.22) + (150,))
            sh.poly([(p[0], p[1]) for p in pts], outline=(28, 30, 32, 230), width=0.009)
            u += w
    for _ in range(70):                                                               # Moos in den Fugen
        sh.ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.012, 0.008, fill=MOSS + (180,))
    for _ in range(2):                                                                # nasse Stelle
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.22, 0.12, amp=0.03, seed=rnd.randint(0, 99)), fill=(30, 40, 60, 60))
    return mottle(sh.finish(seed=seed), 0.06, seed + 7)


def tile_grabplatten(ppm, seed=1, base=(112, 112, 122), joint=(54, 54, 60)):
    """Kapellenboden: grosse, ausgetretene Platten im Laeuferverband, einzelne Grabplatten mit eingeritztem
    Kreuz und Inschriftzeilen, blank gelaufene Mitte, Wachsflecken."""
    T = TILE_M
    sh = Sheet(T, T, ppm, joint, periodic=True)
    rnd = random.Random(seed)
    stones = HD.stone_grid(0, 0, T, T, 1.0, 0.5, seed=seed, joint=0.025, jitter=0.06, tilt=0.012, skip=0.0, split=0.05,
                           merge=0.0, periodic=True, bond=0.5, rounding=0.03)
    for i, st in enumerate(stones):
        pts = st.chip or st.pts
        col = _tint(_tone(base, (1 + st.tone * 0.08) * (0.86 if st.sunk else 1.0) * (1.08 if st.worn else 1.0)),
                    rnd.choice([(1, 1, 1), (1.03, 1.0, 0.96), (0.96, 0.98, 1.04)]))
        sh.poly(pts, fill=col)
        edge_light(sh, pts, _tone(col, 1.15) + (160,), (0, 0, 0, 80), 0.014)
        sh.ink(pts, (30, 30, 36, 255), 0.012, seed=i, var=0.3)
        cx, cy = (st.x0 + st.x1) / 2, (st.y0 + st.y1) / 2
        if (st.x1 - st.x0) > 0.7 and rnd.random() < 0.35:                            # Grabplatte
            sh.rect(st.x0 + 0.07, st.y0 + 0.06, st.x1 - 0.07, st.y1 - 0.06, outline=_tone(col, 0.72) + (220,), width=0.008)
            sh.line([(cx - 0.2, cy), (cx - 0.2, cy - 0.001)], fill=_tone(col, 0.6), width=0.004)
            sh.line([(st.x0 + 0.18, cy - 0.1), (st.x0 + 0.18, cy + 0.12)], fill=_tone(col, 0.62) + (230,), width=0.012)
            sh.line([(st.x0 + 0.12, cy - 0.04), (st.x0 + 0.24, cy - 0.04)], fill=_tone(col, 0.62) + (230,), width=0.012)
            for k in range(3):
                ln = rnd.uniform(0.25, 0.45)
                sh.line([(st.x0 + 0.34, cy - 0.08 + k * 0.07), (st.x0 + 0.34 + ln, cy - 0.08 + k * 0.07)], fill=_tone(col, 0.68) + (200,), width=0.008)
        if st.crack:
            sh.line(st.crack, fill=(26, 26, 32, 190), width=0.008)
        if rnd.random() < 0.18:                                                       # Wachsfleck
            x, y = rnd.uniform(st.x0 + 0.05, st.x1 - 0.05), rnd.uniform(st.y0 + 0.05, st.y1 - 0.05)
            sh.poly(HD.wobble_ellipse(x, y, 0.03, 0.022, amp=0.006, seed=i), fill=(236, 226, 196, 200))
    return mottle(sh.finish(seed=seed), 0.05, seed + 9)


def tile_marmor(ppm, seed=1):
    """Gruftboden: Marmorplatten 0,5 m schraeg im Wechsel hell/dunkelgruen, Adern, Spruenge, Staub."""
    T = TILE_M
    sh = Sheet(T, T, ppm, (46, 50, 52), periodic=True)
    rnd = random.Random(seed)
    s = 0.5
    for r, c, pts in HD.jitter_grid(0, 0, T, T, s, seed=seed, jitter=0.01, periodic=True):
        dark = (r + c) % 2 == 1
        col = _tone((70, 92, 86) if dark else (186, 186, 180), 1 + rnd.uniform(-0.05, 0.05))
        q = shrink(pts, 0.008)
        if rnd.random() < 0.06:
            q = HD.chip(q, rnd, 0.15)
        sh.poly(q, fill=col)
        x0 = min(p[0] for p in q); y0 = min(p[1] for p in q)
        for k in range(3):                                                            # Adern
            a = rnd.uniform(0, math.pi)
            px_, py_ = x0 + rnd.uniform(0.05, s - 0.05), y0 + rnd.uniform(0.05, s - 0.05)
            vein = HD.wobble([(px_ - math.cos(a) * 0.25, py_ - math.sin(a) * 0.25), (px_ + math.cos(a) * 0.25, py_ + math.sin(a) * 0.25)],
                             amp=0.02, seed=r * 31 + c * 7 + k, step=0.03)
            vein = [(min(max(x, x0 + 0.01), x0 + s - 0.02), min(max(y, y0 + 0.01), y0 + s - 0.02)) for x, y in vein]
            sh.line(vein, fill=(_tone(col, 1.25) if dark else _tone(col, 0.78)) + (150,), width=0.006)
        sh.poly([q[0], (q[0][0] + (q[1][0] - q[0][0]) * 0.4, q[0][1]), (q[0][0], q[0][1] + (q[3][1] - q[0][1]) * 0.4)], fill=(255, 255, 255, 30))
        edge_light(sh, q, _tone(col, 1.12) + (150,), (0, 0, 0, 70), 0.01)
        sh.ink(q, (26, 28, 30, 255), 0.009, seed=r * 7 + c, var=0.3)
        if rnd.random() < 0.12:
            sh.line(HD.crack(q, rnd), fill=(30, 30, 34, 200), width=0.007)
    for _ in range(60):
        sh.ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.008, 0.006, fill=(220, 214, 200, 80))
    return mottle(sh.finish(seed=seed), 0.05, seed + 11)


def tile_kacheln(ppm, seed=1):
    """Leichenhalle: weisse Fliesen 0,2 m mit gruengrauer Fuge, Rostspuren, Flecken, ein paar fehlen."""
    T = TILE_M
    sh = Sheet(T, T, ppm, (104, 116, 110), periodic=True)
    rnd = random.Random(seed)
    for r, c, pts in HD.jitter_grid(0, 0, T, T, 0.2, seed=seed, jitter=0.006, periodic=True):
        q = shrink(pts, 0.006)
        if rnd.random() < 0.02:
            sh.poly(q, fill=(70, 74, 72))
            continue
        col = _tint(_tone((206, 212, 206), 1 + rnd.uniform(-0.05, 0.04)), rnd.choice([(1, 1, 1), (1, 1, 1), (0.97, 1.0, 0.98), (1.0, 0.98, 0.94)]))
        if rnd.random() < 0.06:
            q = HD.chip(q, rnd, 0.18)
        sh.poly(q, fill=col)
        sh.poly([q[0], ((q[0][0] + q[1][0]) / 2, q[0][1]), (q[0][0], (q[0][1] + q[3][1]) / 2)], fill=(255, 255, 255, 50))
        edge_light(sh, q, (255, 255, 255, 120), (0, 0, 0, 55), 0.008)
        sh.ink(q, (60, 70, 66, 255), 0.006, seed=r * 7 + c, var=0.3)
        if rnd.random() < 0.05:
            sh.line(HD.crack(q, rnd), fill=(60, 64, 62, 200), width=0.006)
    for _ in range(4):
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), rnd.uniform(0.06, 0.16), rnd.uniform(0.04, 0.1), amp=0.02, seed=rnd.randint(0, 99)),
                fill=rnd.choice([(120, 100, 60, 50), (80, 90, 70, 50)]))
    return mottle(sh.finish(seed=seed), 0.04, seed + 13)


def tile_ziegel(ppm, seed=1, base=(120, 70, 56)):
    """Krematorium: Ziegelboden im Fischgraet, Russ und Asche, Hitzespruenge."""
    T = TILE_M
    sh = Sheet(T, T, ppm, (58, 50, 48), periodic=True)
    rnd = random.Random(seed)
    bw, bl = 0.1, 0.2
    n = int(T / bw)
    for i in range(-n, 2 * n):
        for j in range(-n, 2 * n):
            u0 = i * bw * 2 + j * bw
            v0 = j * bw - i * bw * 0
            for horiz in (True, False):
                if horiz:
                    x0, y0, x1, y1 = u0, v0, u0 + bl, v0 + bw
                else:
                    x0, y0, x1, y1 = u0 + bl, v0 - bw, u0 + bl + bw, v0 + bw
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                if not (0 <= cx < T and 0 <= cy < T):
                    continue
                pts = HD.wobble([(x0 + 0.005, y0 + 0.005), (x1 - 0.005, y0 + 0.005), (x1 - 0.005, y1 - 0.005), (x0 + 0.005, y1 - 0.005)],
                                amp=0.003, seed=i * 31 + j * 7 + horiz, step=0.05, closed=True)
                col = _tint(_tone(base, 1 + rnd.uniform(-0.15, 0.1)), rnd.choice([(1, 1, 1), (1.05, 0.96, 0.92), (0.9, 0.9, 0.94)]))
                sh.poly(pts, fill=col)
                edge_light(sh, pts, _tone(col, 1.15) + (140,), (0, 0, 0, 70), 0.008)
                sh.ink(pts, (34, 24, 22, 255), 0.007, seed=i + j, var=0.3)
    for _ in range(7):                                                                # Russ und Asche
        sh.poly(HD.wobble_ellipse(rnd.uniform(0, T), rnd.uniform(0, T), rnd.uniform(0.15, 0.35), rnd.uniform(0.1, 0.22), amp=0.04, seed=rnd.randint(0, 99)),
                fill=(30, 26, 26, 70))
    for _ in range(120):
        sh.ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.007, 0.006, fill=(190, 186, 180, 90))
    return mottle(sh.finish(seed=seed), 0.06, seed + 15)


def tile_dielen(ppm, seed=1, base=(102, 92, 82)):
    """Graubraune Dielen (Schuppen, Kammern): Reihen 0,2 m, versetzte Stoesse, Maserung, Astloecher, Nagelkoepfe,
    Kratzer, Staub. Ohne fehlende Bretter (die lasen sich im Spiel als Schlitze)."""
    T = TILE_M
    sh = Sheet(T, T, ppm, (40, 32, 26), periodic=True)
    rnd = random.Random(seed)
    rows = 10
    bh = T / rows
    for r in range(rows):
        v0, v1 = r * bh + 0.008, (r + 1) * bh - 0.008
        cuts = sorted(rnd.uniform(0, T) for _ in range(rnd.randint(1, 2)))
        for i, u0 in enumerate(cuts):
            u1 = cuts[i + 1] if i + 1 < len(cuts) else cuts[0] + T
            if u1 - u0 < 0.15:
                continue
            u0, u1 = u0 + 0.006, u1 - 0.006
            pts = HD.wobble([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], amp=0.004, seed=seed * 40 + r * 7 + i, step=0.06, closed=True)
            col = _tint(_tone(base, 1 + rnd.uniform(-0.12, 0.1)), rnd.choice([(1, 1, 1), (0.95, 0.96, 1.02), (1.05, 1.0, 0.92), (0.9, 0.9, 0.9)]))
            sh.poly(pts, fill=col)
            for g in range(rnd.randint(2, 3)):
                vv = v0 + bh * (0.2 + 0.3 * g + rnd.uniform(-0.05, 0.05))
                sh.line(HD.wobble([(u0 + 0.03, vv), (u1 - 0.03, vv + rnd.uniform(-0.02, 0.02))], amp=0.008, seed=r * 11 + g, step=0.08),
                        fill=_tone(col, 0.85) + (170,), width=0.006)
            if rnd.random() < 0.2:
                kx, ky = rnd.uniform(u0 + 0.1, u1 - 0.1), (v0 + v1) / 2 + rnd.uniform(-0.03, 0.03)
                sh.ellipse(kx, ky, 0.025, 0.018, fill=_tone(col, 0.6), outline=_tone(col, 0.45), width=0.006)
                sh.ellipse(kx, ky, 0.01, 0.007, fill=_tone(col, 0.4))
            for nx in (u0 + 0.04, u1 - 0.04):
                for ny in (v0 + 0.04, v1 - 0.04):
                    sh.ellipse(nx, ny, 0.008, 0.008, fill=(70, 62, 58), outline=(40, 32, 30), width=0.004)
            edge_light(sh, pts, _tone(col, 1.2) + (150,), (0, 0, 0, 80), 0.012)
            sh.ink(pts, (34, 26, 20, 255), 0.012, seed=r * 5 + i, var=0.3)
            if rnd.random() < 0.15:
                kx = rnd.uniform(u0 + 0.1, u1 - 0.1)
                sh.line([(kx, v0 + 0.03), (kx + rnd.uniform(0.1, 0.3), v1 - 0.03)], fill=(220, 200, 170, 80), width=0.005)
    for _ in range(40):
        sh.ellipse(rnd.uniform(0, T), rnd.uniform(0, T), 0.006, 0.005, fill=(230, 220, 200, 70))
    return mottle(sh.finish(seed=seed), 0.05, seed + 1)


def tile_erde(ppm, seed=1):
    return VF.tile_friedhofserde(ppm, seed, base=(76, 70, 60))


_TILES = {"rasen": tile_rasen, "wildgras": tile_wildgras, "nachtgras": tile_nachtgras, "kies": tile_kies, "kopfstein": tile_kopfstein, "grabplatten": tile_grabplatten,
          "marmor": tile_marmor, "kacheln": tile_kacheln, "ziegel": tile_ziegel, "dielen": tile_dielen, "erde": tile_erde}
_CACHE = {}


def tile(name, ppm, seed=1, **kw):
    k = (name, ppm, seed, tuple(sorted(kw.items())))
    if k not in _CACHE:
        _CACHE[k] = _TILES[name](ppm, seed, **kw)
    return _CACHE[k]


# ------------------------------------------------------------------ Wandstirnseiten (Hoehe in Bildmetern)

def _stone_base(sh, W, H, rnd, seed, base=(112, 112, 118), sw=0.5, sht=0.24):
    stones = HD.stone_grid(0, 0, W, H, sw, sht, seed=seed, joint=0.025, jitter=0.16, tilt=0.015, skip=0.0, split=0.12,
                           merge=0.05, periodic=False, bond=0.5, rounding=0.06)
    for i, st in enumerate(stones):
        pts = st.chip or st.pts
        col = _tint(_tone(base, (1 + st.tone * 0.1) * (0.86 if st.sunk else 1.0)), rnd.choice([(1, 1, 1), (1.04, 1.0, 0.95), (0.95, 0.98, 1.05)]))
        sh.poly(pts, fill=col)
        edge_light(sh, pts, _tone(col, 1.18) + (160,), (0, 0, 0, 90), 0.014)
        sh.ink(pts, (28, 28, 34, 255), 0.012, seed=i, var=0.3)
        if st.crack:
            sh.line(st.crack, fill=(26, 26, 30, 200), width=0.008)


def _foot(sh, W, H, rnd, moss=True):
    for k in range(3):                                                                # feuchter, dunkler Fuss
        sh.rect(0, H - 0.1 * (k + 1), W, H, fill=(8, 12, 20, 36))
    if moss:
        for _ in range(int(W * 4)):
            sh.poly(HD.wobble_ellipse(rnd.uniform(0, W), H - rnd.uniform(0.01, 0.2), rnd.uniform(0.04, 0.09), 0.03, amp=0.012, seed=rnd.randint(0, 999)),
                    fill=MOSS + (160,))
    sh.rect(0, H - 0.02, W, H, fill=(18, 18, 22))


def _ivy(sh, W, H, rnd, seed, n=1):
    for _ in range(n):
        vx = rnd.uniform(0.15, max(0.16, W - 0.15))
        vine = HD.wobble([(vx, 0), (vx + rnd.uniform(-0.12, 0.12), H * 0.45), (vx + rnd.uniform(-0.2, 0.2), H * 0.85)], amp=0.03, seed=seed, step=0.04)
        sh.line(vine, fill=(40, 58, 40), width=0.014)
        for k, (lx, ly) in enumerate(vine[::2]):
            for sx in (-1, 1):
                if rnd.random() < 0.7:
                    x, y = lx + sx * 0.035, ly + rnd.uniform(-0.02, 0.02)
                    sh.poly([(x, y - 0.035), (x + 0.03, y - 0.005), (x + 0.018, y + 0.03), (x - 0.018, y + 0.03), (x - 0.03, y - 0.005)],
                            fill=(62, 100, 64) if (k + sx) % 2 else (80, 122, 74), outline=(24, 40, 28), width=0.005)


def _cobweb(sh, x, y, size, qx, qy, alpha_=100):
    for k in range(6):
        a = (math.pi / 2) * k / 5
        sh.line([(x, y), (x + qx * size * math.cos(a), y + qy * size * math.sin(a))], fill=(232, 236, 242, alpha_), width=0.005)
    for r in (0.3, 0.55, 0.8, 1.0):
        sh.line([(x + qx * r * size * math.cos((math.pi / 2) * k / 5), y + qy * r * size * math.sin((math.pi / 2) * k / 5)) for k in range(6)],
                fill=(232, 236, 242, alpha_ - 10), width=0.005)


def lancet(sh, x0, x1, y_top, y_bot, rnd, seed, lit=0.6):
    """Spitzbogenfenster mit Bleiglas (Mondlicht von aussen): Steinlaibung, Rautenverglasung in Nachtblau,
    rot-goldener Randstreifen, Medaillon mit Kreuz in der Mitte, Masswerk-Dreipass im Bogen, Mondglanz."""
    w = x1 - x0
    cx = (x0 + x1) / 2
    arch = y_top + w * 0.6

    def outline_of(ax0, ax1, top):
        ww = ax1 - ax0
        c = (ax0 + ax1) / 2
        a = top + ww * 0.6
        left = [(c - ww / 2 * math.cos(t), a - ww * 0.6 * math.sin(t)) for t in [k * math.pi / 2 / 10 for k in range(11)]]
        right = [(c + ww / 2 * math.cos(t), a - ww * 0.6 * math.sin(t)) for t in [k * math.pi / 2 / 10 for k in range(10, -1, -1)]]
        return [(ax0, y_bot)] + left + right + [(ax1, y_bot)]

    sh.poly(outline_of(x0 - 0.05, x1 + 0.05, y_top - 0.05), fill=(146, 146, 152), outline=(30, 30, 36), width=0.012)   # Laibung
    glass = outline_of(x0, x1, y_top)
    sh.poly(glass, fill=(26, 40, 82))
    m = Image.new("L", sh.N, 0)
    ImageDraw.Draw(m).polygon(sh.P(glass), fill=255)
    lay = Sheet(sh.w_m, sh.h_m, sh.ppm, (0, 0, 0, 0), mode="RGBA")
    blues = [(44, 70, 140), (34, 56, 120), (60, 90, 160), (30, 48, 104)]
    d = 0.075                                                                         # Rautenfelder
    k = 0
    v = y_top - d
    while v < y_bot + d:
        u = x0 - d + (d / 2 if int((v - y_top) / (d / 2)) % 2 else 0)
        while u < x1 + d:
            col = blues[(k * 7 + int(u * 53)) % len(blues)]
            col = _tone(col, 0.85 + lit * 0.4 * rnd.uniform(0.6, 1.0))
            lay.poly([(u, v - d / 2), (u + d / 2, v), (u, v + d / 2), (u - d / 2, v)], fill=col + (255,), outline=(22, 22, 28, 255), width=0.006)
            u += d
            k += 1
        v += d / 2
    bw = 0.035                                                                        # Randstreifen rot/gold
    edge = outline_of(x0 + bw / 2, x1 - bw / 2, y_top + bw / 2)
    for i in range(len(edge) - 1):
        lay.line([edge[i], edge[i + 1]], fill=((170, 40, 48) if i % 2 else (210, 160, 60)) + (255,), width=bw)
    lay.line([(cx, arch + 0.02), (cx, y_bot)], fill=(70, 70, 76, 255), width=0.016)    # Pfosten (Masswerk)
    my = y_top + (y_bot - y_top) * 0.55                                               # Medaillon mit Kreuz
    r = w * 0.3
    lay.ellipse(cx, my, r, r, fill=(200, 150, 60, 255), outline=(22, 22, 28, 255), width=0.008)
    lay.ellipse(cx, my, r * 0.78, r * 0.78, fill=(150, 30, 44, 255), outline=(22, 22, 28, 255), width=0.006)
    lay.rect(cx - r * 0.12, my - r * 0.6, cx + r * 0.12, my + r * 0.6, fill=(236, 220, 170, 255))
    lay.rect(cx - r * 0.45, my - r * 0.25, cx + r * 0.45, my - r * 0.05, fill=(236, 220, 170, 255))
    tr = w * 0.13                                                                     # Dreipass im Bogen
    ty = arch - w * 0.12
    for a in (math.pi / 2, math.pi / 2 + 2.1, math.pi / 2 - 2.1):
        lay.ellipse(cx + tr * 0.6 * math.cos(a), ty - tr * 0.6 * math.sin(a), tr * 0.55, tr * 0.55, fill=(210, 170, 70, 255), outline=(22, 22, 28, 255), width=0.006)
    lay.line([(x0 + 0.03, arch), (x0 + 0.03, y_bot - 0.03)], fill=(210, 222, 245, 80), width=0.014)   # Mondglanz
    lay.line([(x0 + 0.06, arch + 0.04), (x0 + 0.06, my - r - 0.02)], fill=(210, 222, 245, 50), width=0.008)
    li = lay.img
    li.putalpha(Image.composite(li.getchannel("A"), Image.new("L", sh.N, 0), m))
    sh.img.paste(li, (0, 0), li) if sh.img.mode == "RGB" else sh.img.alpha_composite(li)
    sh.line(glass + [glass[0]], fill=(30, 30, 36), width=0.016)
    sh.rect(x0 - 0.07, y_bot, x1 + 0.07, y_bot + 0.04, fill=(156, 156, 162), outline=(30, 30, 36), width=0.008)   # Sohlbank


def _sconce(sh, x, y, lit=True):
    """Wandleuchter mit Kerze; Licht nur als heller Kranz an der Wand."""
    if lit:
        for r, a in ((0.22, 26), (0.14, 40), (0.08, 60)):
            sh.ellipse(x, y - 0.06, r, r * 0.9, fill=(255, 210, 140, a))
    sh.line([(x, y + 0.04), (x, y + 0.11)], fill=IRON, width=0.02)
    sh.ellipse(x, y + 0.03, 0.04, 0.015, fill=IRON_L, outline=(20, 20, 24), width=0.005)
    sh.rect(x - 0.014, y - 0.05, x + 0.014, y + 0.03, fill=(236, 226, 196), outline=(60, 50, 40), width=0.004)
    if lit:
        sh.poly([(x - 0.012, y - 0.05), (x, y - 0.1), (x + 0.012, y - 0.05)], fill=(255, 190, 80))
        sh.ellipse(x, y - 0.06, 0.005, 0.01, fill=(255, 246, 210))


def wall_kapelle(W, H, ppm, seed):
    sh = Sheet(W, H, ppm, (70, 70, 76))
    rnd = random.Random(seed)
    _stone_base(sh, W, H, rnd, seed, base=(118, 116, 124), sw=0.42, sht=0.2)
    if H > 0.6 and W > 2.0:
        n = max(1, int(W / 2.4))
        for k in range(n):
            cx = W * (k + 0.5) / n
            lancet(sh, cx - 0.22, cx + 0.22, 0.08, H - 0.22, rnd, seed + k)
        for k in range(n + 1):
            x = W * k / n
            if 0.3 < x < W - 0.3:
                _sconce(sh, x, H * 0.45)
    _foot(sh, W, H, rnd, moss=False)
    _cobweb(sh, 0 if seed % 2 else W, 0, 0.22, 1 if seed % 2 else -1, 1)
    return mottle(sh.finish(grain=0.02, seed=seed), 0.04, seed + 1).convert("RGBA")


def wall_gruft(W, H, ppm, seed):
    """Gruft: Marmorwand mit Grabnischen (Loculi) in zwei Reihen, Namensplatten, eine Nische offen."""
    sh = Sheet(W, H, ppm, (120, 120, 116))
    rnd = random.Random(seed)
    _stone_base(sh, W, H, rnd, seed, base=(150, 148, 142), sw=0.6, sht=0.3)
    if H > 0.5:
        n = max(1, int(W / 0.75))
        rows = 2 if H > 0.75 else 1
        for r in range(rows):
            for k in range(n):
                x0 = W * k / n + 0.08
                x1 = W * (k + 1) / n - 0.08
                y0 = 0.08 + r * (H - 0.2) / rows
                y1 = y0 + (H - 0.2) / rows - 0.08
                open_ = rnd.random() < 0.12
                sh.rect(x0 - 0.02, y0 - 0.02, x1 + 0.02, y1 + 0.02, fill=(90, 90, 92))
                sh.rect(x0, y0, x1, y1, fill=(28, 26, 30) if open_ else (196, 192, 182), outline=(36, 36, 40), width=0.01)
                if open_:
                    sh.ellipse((x0 + x1) / 2, y1 - 0.06, 0.05, 0.04, fill=BONE, outline=(40, 36, 30), width=0.005)
                    sh.ellipse((x0 + x1) / 2 - 0.018, y1 - 0.065, 0.012, 0.012, fill=(30, 26, 26))
                    sh.ellipse((x0 + x1) / 2 + 0.018, y1 - 0.065, 0.012, 0.012, fill=(30, 26, 26))
                else:
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    sh.rect(cx - 0.1, cy - 0.035, cx + 0.1, cy + 0.035, fill=(150, 120, 60), outline=(80, 60, 30), width=0.006)
                    for j in range(2):
                        sh.line([(cx - 0.07, cy - 0.012 + j * 0.022), (cx + 0.07, cy - 0.012 + j * 0.022)], fill=(80, 60, 30), width=0.006)
                    if rnd.random() < 0.3:                                            # Trockenblumen in der Vase
                        vx = x0 + 0.06
                        sh.rect(vx - 0.015, y1 - 0.06, vx + 0.015, y1 - 0.01, fill=(140, 110, 60))
                        for a in (-0.4, 0, 0.4):
                            sh.line([(vx, y1 - 0.06), (vx + math.sin(a) * 0.05, y1 - 0.13)], fill=(80, 70, 50), width=0.005)
                            sh.ellipse(vx + math.sin(a) * 0.05, y1 - 0.13, 0.012, 0.012, fill=(120, 50, 60))
    _foot(sh, W, H, rnd)
    _cobweb(sh, W if seed % 2 else 0, 0, 0.26, -1 if seed % 2 else 1, 1)
    return mottle(sh.finish(grain=0.02, seed=seed), 0.04, seed + 2).convert("RGBA")


def wall_leichenhalle(W, H, ppm, seed):
    """Kuehlfaecher aus Stahl in weiss gefliester Wand: Griffe, Namensschilder, eins einen Spalt offen."""
    sh = Sheet(W, H, ppm, (190, 196, 190))
    rnd = random.Random(seed)
    for r, c, pts in HD.jitter_grid(0, 0, W, H, 0.15, seed=seed, jitter=0.0, periodic=False):
        q = shrink(pts, 0.005)
        sh.poly(q, fill=_tone((206, 212, 206), 1 + rnd.uniform(-0.05, 0.04)))
        sh.ink(q, (110, 120, 116, 255), 0.005, seed=r + c, var=0.2)
    if H > 0.5 and W > 1.0:
        n = max(1, int(W / 0.6))
        rows = 2 if H > 0.75 else 1
        for r in range(rows):
            for k in range(n):
                x0 = W * k / n + 0.05
                x1 = W * (k + 1) / n - 0.05
                y0 = 0.06 + r * (H - 0.16) / rows
                y1 = y0 + (H - 0.16) / rows - 0.06
                sh.rect(x0 - 0.02, y0 - 0.02, x1 + 0.02, y1 + 0.02, fill=(90, 96, 100))
                sh.rect(x0, y0, x1, y1, fill=(150, 156, 164), outline=(40, 44, 50), width=0.01)
                sh.line([(x0 + 0.02, y0 + 0.02), (x1 - 0.02, y0 + 0.02)], fill=(200, 206, 214), width=0.008)
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                sh.rect(cx - 0.09, cy + 0.03, cx + 0.09, cy + 0.06, fill=(120, 126, 134), outline=(40, 44, 50), width=0.006)  # Griff
                sh.rect(cx - 0.05, cy - 0.06, cx + 0.05, cy - 0.02, fill=(232, 226, 206), outline=(60, 60, 60), width=0.004)  # Schild
                sh.line([(cx - 0.035, cy - 0.04), (cx + 0.035, cy - 0.04)], fill=(60, 60, 70), width=0.005)
                if rnd.random() < 0.12:                                               # Spalt offen, kalter Dunst
                    sh.rect(x0, y1 - 0.025, x1, y1, fill=(20, 24, 30))
                    for j in range(3):
                        sh.ellipse(x0 + (x1 - x0) * (0.25 + j * 0.25), y1 + 0.02, 0.07, 0.025, fill=(220, 236, 250, 60))
    _foot(sh, W, H, rnd, moss=False)
    return mottle(sh.finish(grain=0.02, seed=seed), 0.03, seed + 3).convert("RGBA")


def wall_krema(W, H, ppm, seed):
    """Ziegelwand, oben verrusst, Rauchrohr-Klappe und Schuerhaken an Nageln."""
    sh = Sheet(W, H, ppm, (60, 40, 36))
    rnd = random.Random(seed)
    stones = HD.stone_grid(0, 0, W, H, 0.24, 0.085, seed=seed, joint=0.014, jitter=0.06, tilt=0.0, skip=0.0, split=0.0, merge=0.0, periodic=False, bond=0.5)
    for i, st in enumerate(stones):
        col = _tint(_tone((136, 72, 56), 1 + st.tone * 0.12), rnd.choice([(1, 1, 1), (1.06, 0.96, 0.9), (0.9, 0.9, 0.94)]))
        sh.poly(st.pts, fill=col)
        sh.ink(st.pts, (40, 24, 20, 255), 0.007, seed=i, var=0.3)
    for k in range(6):                                                                # Russ von oben
        sh.rect(0, 0, W, H * (0.55 - k * 0.08), fill=(10, 8, 8, 40))
    if W > 1.0 and H > 0.5:
        for k in range(max(1, int(W / 2.0))):
            hx = W * (k + 0.5) / max(1, int(W / 2.0)) + 0.4
            if hx < W - 0.2:
                sh.line([(hx - 0.1, 0.15), (hx - 0.1, 0.18)], fill=(30, 30, 30), width=0.02)
                sh.line([(hx - 0.1, 0.17), (hx - 0.12, H * 0.75), (hx - 0.06, H * 0.8)], fill=IRON, width=0.016)
    _foot(sh, W, H, rnd, moss=False)
    return mottle(sh.finish(grain=0.025, seed=seed), 0.05, seed + 4).convert("RGBA")


def wall_holz(W, H, ppm, seed, tools=None):
    """Bretterwand ueber Steinsockel: senkrechte graue Bretter, Werkzeug/Gegenstaende an Naegeln."""
    sh = Sheet(W, H, ppm, (54, 46, 40))
    rnd = random.Random(seed)
    sock = min(0.22, H * 0.3)
    x = 0.0
    while x < W:
        bw = rnd.uniform(0.14, 0.2)
        col = _tint(_tone((104, 92, 80), 1 + rnd.uniform(-0.12, 0.1)), rnd.choice([(1, 1, 1), (0.96, 0.98, 1.04), (1.04, 1.0, 0.94)]))
        pts = [(x + 0.004, 0), (x + bw - 0.004, 0), (x + bw - 0.004, H - sock), (x + 0.004, H - sock)]
        sh.poly(pts, fill=col)
        for g in range(2):
            gx = x + bw * (0.3 + 0.4 * g)
            sh.line(HD.wobble([(gx, 0.02), (gx + rnd.uniform(-0.01, 0.01), H - sock - 0.02)], amp=0.004, seed=int(x * 100) + g, step=0.05),
                    fill=_tone(col, 0.85) + (170,), width=0.005)
        sh.ellipse(x + bw / 2, 0.08, 0.008, 0.008, fill=(60, 56, 54))
        sh.ellipse(x + bw / 2, H - sock - 0.08, 0.008, 0.008, fill=(60, 56, 54))
        sh.ink(pts, (30, 24, 20, 255), 0.008, seed=int(x * 50), var=0.3, closed=True)
        x += bw
    sh.line([(0, H * 0.32), (W, H * 0.32)], fill=(70, 60, 52), width=0.04)            # Querriegel
    sh.line([(0, H * 0.32 - 0.015), (W, H * 0.32 - 0.015)], fill=(120, 106, 92), width=0.008)
    stones = HD.stone_grid(0, H - sock, W, H, 0.3, 0.1, seed=seed, joint=0.014, jitter=0.1, tilt=0.0, skip=0.0, split=0.0, merge=0.0, periodic=False, bond=0.5)
    for i, st in enumerate(stones):
        col = _tone((110, 110, 116), 1 + st.tone * 0.1)
        sh.poly(st.pts, fill=col)
        sh.ink(st.pts, (30, 30, 34, 255), 0.007, seed=i, var=0.3)
    for kind, fx in (tools or []):
        hang(sh, kind, fx * W, H * 0.32, rnd)
    _foot(sh, W, H, rnd, moss=False)
    _cobweb(sh, 0 if seed % 2 else W, 0, 0.2, 1 if seed % 2 else -1, 1)
    return mottle(sh.finish(grain=0.025, seed=seed), 0.04, seed + 5).convert("RGBA")


def hang(sh, kind, x, y, rnd):
    """Gegenstand an einem Nagel bei (x, y) (Bildmeter, y nach unten = tiefer an der Wand)."""
    sh.ellipse(x, y, 0.012, 0.012, fill=(40, 40, 44))
    if kind == "saege":
        sh.poly([(x - 0.22, y + 0.02), (x + 0.18, y + 0.02), (x + 0.22, y + 0.12), (x - 0.2, y + 0.12)], fill=(176, 180, 186), outline=(30, 30, 34), width=0.008)
        for k in range(16):
            tx = x - 0.2 + k * 0.026
            sh.poly([(tx, y + 0.12), (tx + 0.013, y + 0.145), (tx + 0.026, y + 0.12)], fill=(150, 154, 160))
        sh.rect(x + 0.16, y - 0.02, x + 0.26, y + 0.13, fill=(120, 80, 48), outline=(30, 24, 20), width=0.008)
    elif kind == "schaufel":
        sh.line([(x, y), (x, y + 0.36)], fill=(130, 96, 62), width=0.02)
        sh.poly([(x - 0.06, y + 0.34), (x + 0.06, y + 0.34), (x + 0.05, y + 0.5), (x, y + 0.54), (x - 0.05, y + 0.5)], fill=(120, 124, 130), outline=(30, 30, 34), width=0.008)
        sh.ellipse(x, y + 0.01, 0.03, 0.02, outline=(130, 96, 62), width=0.01)
    elif kind == "laterne":
        sh.line([(x, y), (x, y + 0.04)], fill=IRON, width=0.008)
        sh.rect(x - 0.045, y + 0.04, x + 0.045, y + 0.16, fill=(255, 220, 140, 255) if rnd.random() < 0.4 else (60, 64, 72), outline=(30, 30, 34), width=0.01)
        sh.poly([(x - 0.06, y + 0.04), (x + 0.06, y + 0.04), (x, y + 0.0)], fill=IRON, outline=(20, 20, 24), width=0.006)
        sh.line([(x - 0.045, y + 0.16), (x + 0.045, y + 0.16)], fill=IRON, width=0.012)
    elif kind == "gewehr":
        sh.line([(x - 0.28, y + 0.04), (x + 0.24, y + 0.0)], fill=(50, 50, 56), width=0.016)
        sh.poly([(x + 0.18, y - 0.01), (x + 0.36, y + 0.02), (x + 0.36, y + 0.07), (x + 0.2, y + 0.04)], fill=(110, 70, 40), outline=(30, 20, 16), width=0.006)
    elif kind == "schluessel":
        sh.rect(x - 0.16, y + 0.01, x + 0.16, y + 0.2, fill=(96, 70, 46), outline=(30, 22, 16), width=0.008)
        for k in range(5):
            kx = x - 0.12 + k * 0.06
            sh.ellipse(kx, y + 0.06, 0.006, 0.006, fill=(40, 40, 40))
            sh.ellipse(kx, y + 0.09, 0.014, 0.014, outline=(200, 170, 80), width=0.006)
            sh.line([(kx, y + 0.1), (kx, y + 0.16)], fill=(200, 170, 80), width=0.006)
    elif kind == "karte":
        sh.rect(x - 0.2, y - 0.02, x + 0.2, y + 0.24, fill=(206, 192, 156), outline=(60, 50, 36), width=0.008)
        for k in range(4):
            for j in range(5):
                sh.rect(x - 0.16 + j * 0.065, y + 0.02 + k * 0.05, x - 0.12 + j * 0.065, y + 0.05 + k * 0.05, outline=(100, 80, 50), width=0.004)
        sh.ellipse(x + 0.06, y + 0.12, 0.02, 0.02, outline=(160, 40, 40), width=0.006)
    elif kind == "kranz":
        for k in range(14):
            a = k / 14 * math.tau
            sh.ellipse(x + 0.09 * math.cos(a), y + 0.11 + 0.09 * math.sin(a), 0.035, 0.03, fill=(46, 84, 52) if k % 2 else (60, 100, 60))
        sh.poly([(x - 0.02, y + 0.2), (x + 0.02, y + 0.2), (x + 0.04, y + 0.28), (x - 0.04, y + 0.28)], fill=(120, 30, 40))
    elif kind == "seil":
        for k in range(4):
            sh.ellipse(x, y + 0.1, 0.07 + k * 0.012, 0.09 + k * 0.012, outline=(150, 128, 92), width=0.01)
    elif kind == "uhr":
        sh.ellipse(x, y + 0.1, 0.08, 0.08, fill=(220, 210, 180), outline=(70, 50, 30), width=0.012)
        sh.line([(x, y + 0.1), (x, y + 0.05)], fill=(30, 30, 30), width=0.006)
        sh.line([(x, y + 0.1), (x + 0.04, y + 0.1)], fill=(30, 30, 30), width=0.006)
    elif kind == "bild":
        sh.rect(x - 0.13, y + 0.0, x + 0.13, y + 0.2, fill=(150, 116, 60), outline=(40, 30, 20), width=0.01)
        sh.rect(x - 0.1, y + 0.03, x + 0.1, y + 0.17, fill=(60, 70, 84))
        sh.ellipse(x, y + 0.09, 0.04, 0.05, fill=(180, 160, 140))
        sh.rect(x - 0.06, y + 0.12, x + 0.06, y + 0.17, fill=(40, 40, 50))


def wall_stein(W, H, ppm, seed):
    sh = Sheet(W, H, ppm, (64, 64, 68))
    rnd = random.Random(seed)
    _stone_base(sh, W, H, rnd, seed)
    if W > 1.4:
        _ivy(sh, W, H, rnd, seed)
    _foot(sh, W, H, rnd)
    _cobweb(sh, W if seed % 2 else 0, 0, 0.22, -1 if seed % 2 else 1, 1)
    return mottle(sh.finish(grain=0.025, seed=seed), 0.05, seed + 6).convert("RGBA")


def wall_fassade(W, H, ppm, seed, window=True):
    """Aussenseite einer Suedwand (ueber dem Leerraum): Bruchstein, ggf. kleines vergittertes Fenster, Efeu."""
    sh = Sheet(W, H, ppm, (60, 60, 64))
    rnd = random.Random(seed)
    _stone_base(sh, W, H, rnd, seed, base=(104, 104, 112), sw=0.45, sht=0.2)
    if window and W > 1.6 and H > 0.35:
        n = max(1, int(W / 2.6))
        for k in range(n):
            cx = W * (k + 0.5) / n + rnd.uniform(-0.2, 0.2)
            y0, y1 = H * 0.18, H * 0.7
            sh.rect(cx - 0.2, y0 - 0.03, cx + 0.2, y1 + 0.03, fill=(140, 140, 146), outline=(30, 30, 34), width=0.01)
            sh.rect(cx - 0.16, y0, cx + 0.16, y1, fill=(255, 210, 130) if rnd.random() < 0.35 else (24, 30, 46))
            for u in (-0.08, 0.0, 0.08):
                sh.line([(cx + u, y0), (cx + u, y1)], fill=(30, 30, 34), width=0.012)
    _ivy(sh, W, H, rnd, seed, n=max(1, int(W / 2.5)))
    _foot(sh, W, H, rnd)
    return mottle(sh.finish(grain=0.025, seed=seed), 0.05, seed + 7).convert("RGBA")


def wall_hecke(W, H, ppm, seed):
    """Eibenhecke, dunkler und blauer als die Villa-Hecke, mit roten Eibenbeeren."""
    img = VF.wall_front(W, H, "hecke", ppm, seed)
    px = img.load()
    for yy in range(img.height):
        for xx in range(img.width):
            r, g, b, a = px[xx, yy]
            if a:
                px[xx, yy] = (int(r * 0.8), int(g * 0.86), min(255, int(b * 1.02 + 6)), a)
    return img


def wall_zaun(W, H, ppm, seed):
    """Schmiedeeiserner Zaun auf Steinsockel (Villa-Zaun), mit wenig, gedecktem Rost."""
    img = VF.wall_front(W, H, "zaun", ppm, seed)
    px = img.load()
    for yy in range(img.height):
        for xx in range(img.width):
            r, g, b, a = px[xx, yy]
            if a and r > 130 and g < 110 and b < 70:                                  # Rostpunkte daempfen
                px[xx, yy] = (int(r * 0.62), int(g * 0.7), int(b * 0.85) + 10, a)
    return img


WALL_STYLES = {"kapelle": wall_kapelle, "gruft": wall_gruft, "leichenhalle": wall_leichenhalle, "krema": wall_krema,
               "holz": wall_holz, "stein": wall_stein, "fassade": wall_fassade, "hecke": wall_hecke, "zaun": wall_zaun}


def wall_front(W, H, style, ppm, seed=1, **kw):
    return WALL_STYLES[style](W, H, ppm, seed, **kw)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "mats.png"
    ppm = 80
    names = list(_TILES)
    tiles = [tile(n, ppm, 3) for n in names]
    W = sum(t.width for t in tiles) + 10 * len(tiles)
    walls = [wall_front(3.0, 0.9, s, ppm, 2) if s != "holz" else wall_holz(3.0, 0.9, ppm, 2, tools=[("saege", 0.25), ("schaufel", 0.55), ("laterne", 0.8)])
             for s in WALL_STYLES]
    H = tiles[0].height + 20 + sum(w.height + 10 for w in walls[:5])
    img = Image.new("RGB", (max(W, 3 * 260 + 30), tiles[0].height + 10 + 2 * (walls[0].height + 10) * 3), (30, 30, 30))
    x = 0
    for t in tiles:
        img.paste(t, (x, 0))
        x += t.width + 10
    y = tiles[0].height + 10
    x = 0
    for k, w in enumerate(walls):
        img.paste(w.convert("RGB"), (x, y), w)
        x += w.width + 10
        if x + w.width > img.width:
            x = 0
            y += w.height + 10
    img.save(out)
    print(img.size)
