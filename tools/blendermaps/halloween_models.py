# Unknown's Halloween - Requisiten-Modelle fuer BlenderMaps (Villa "Hollowmere Manor", Friedhof "Ravenhollow Cemetery").
#
# Privater Teil von Assets/BlenderMaps/rooms/_atlas_models.py: alle Arten, die nur auf villa/graveyard vorkommen, und
# die Kartenvarianten oeffentlicher Arten (Hexenkessel, Villa-Herd, Monitorwand, Technikkisten, Stein-Sarkophag).
# Geladen ueber bm_ext_halloween.py (api.add_models) am Ende von _atlas_models.py; meldet sich dort mit AM.model()
# bzw. AM.variant() an. Gemeinsame Helfer (cabinet, doors, candle, ...) kommen aus _atlas_models.

import math
import random
import sys

from PIL import Image
from shapely import affinity
from shapely.geometry import box as sbox

import bm_ext

sys.path.insert(0, str(bm_ext.ROOT / "rooms"))
import _atlas_models as AM                                                                                          # noqa: E402
import bm_models as M                                                                                               # noqa: E402
from bm_spec import box, cyl, lathe, tube, obox, prism, tooth, blob, boulder, rot3, slab                             # noqa: E402
from _atlas_models import (K, OL, WOOD, WOOD_D, WALNUT, BRASS, _sh, legs4, candle, drawers, doors, cabinet,         # noqa: E402
                           shelves, pic, panel_south, roof_gable, tripod, ladder, chair, armchair, counter, lamp_glow, disc_s,
                           wheel, sarcophagus_poly, kind_shelf, kind_cabinet_doors, kind_desk, it_lamp, it_book,
                           it_paper, it_typewriter, it_candle)

model = AM.model
OWN = ("villa", "graveyard")


# ------------------------------------------------------------------------------------------------ Hilfen

def it_skull(P, h, dx=0.0, dy=0.0):
    x, y = P.cx + dx, P.cy + dy
    return [blob(x, y, h + 0.07, 0.07, 0.08, 0.07, (P.m("bone", (226, 218, 196)), P.m("bone_d", (190, 180, 160))), seed=P.seed, seg=10, rings=6)]


def coffin(P, cx, cy, L, w, z0, h, rgb, yaw=0.0, lid=True, open_=False):
    body, dk = P.m("coffin", rgb), P.m("coffin_d", _sh(rgb, 0.7))
    pg = sarcophagus_poly(cx, cy, L, w, yaw)
    out = [prism(pg, z0, z0 + h, body, bevel=0.012, outline=OL)]
    if lid and not open_:
        out.append(prism(pg.buffer(0.012), z0 + h, z0 + h + 0.04, dk, bevel=0.01, outline=OL))
        # Kreuz auf dem Deckel
        cr = P.m("cross", BRASS)
        v = rot3((0, 0.1, 0), yaw, 0)
        out.append(obox((cx + v[0], cy + v[1], z0 + h + 0.045), (0.03, L * 0.45, 0.01), cr, yaw=yaw))
        out.append(obox((cx + v[0] * 1.8, cy + v[1] * 1.8, z0 + h + 0.045), (w * 0.5, 0.03, 0.01), cr, yaw=yaw))
    if open_:
        out.append(prism(pg.buffer(-0.03), z0 + 0.02, z0 + h - 0.03, P.m("coffin_in", (200, 190, 170))))
    return out


# ------------------------------------------------------------------------------------------------ Modelle

# ---- Regale, Schraenke

@model("bandregal", "maskenregal", "buecherregal", "drehregal", "requisiten")
def m_regal(P):
    pal = {"bandregal": (124, 88, 56), "maskenregal": (120, 84, 54), "buecherregal": (118, 80, 50), "drehregal": (122, 84, 52),
           "requisiten": (170, 176, 184)}
    rgb = pal.get(P.kind, (150, 105, 62))
    out = kind_shelf(P, rgb)
    if P.kind == "maskenregal":
        for k in range(3):
            z = 0.08 + (P.h - 0.13) * (k + 0.2) / 3 + 0.0
            out.append(blob(P.cx, P.y0 + 0.2, z + 0.1, 0.08, 0.06, 0.1, (P.m("mask", (230, 226, 220)), P.m("mask_d", (190, 186, 180))), seed=k, seg=10, rings=6))
    if P.kind == "requisiten":
        out += it_skull(P, 0.08 + (P.h - 0.13) * 1.2 / 3, dx=-P.w * 0.25, dy=-P.d * 0.1)
        out.append(lathe(P.cx + 0.2, P.y0 + 0.2, [(0.0, 0.1), (0.05, 0.1), (0.05, 0.3), (0.0, 0.3)], P.g("jar", (200, 70, 70), 1.2), seg=10))
    if P.kind == "drehregal":
        out.append(lamp_glow(P, P.cx, P.y0 + 0.1, P.h + 0.1, r=0.06, s=2.5))
    return out


# Kleiderstange: gleicher Koerper wie die oeffentliche Garderobe (Stange auf Rollen)
model("kleiderstange")(AM.m_garderobe)


@model("topfregal")
def m_topfregal(P):
    z0, z1 = P.zvis()
    zr = max(1.5, z1 - 0.1)
    out = [tube([(P.vx0, P.base + 0.1, zr), (P.vx1, P.base + 0.1, zr)], 0.014, P.m("rail", (90, 92, 98)), seg=8)]
    for x in (P.vx0 + 0.05, P.vx1 - 0.05):
        out.append(tube([(x, P.base + 0.1, zr), (x, P.base + 0.0, zr + 0.25)], 0.01, P.m("rail", (90, 92, 98)), seg=6))
    for j in range(5):
        x = P.vx0 + 0.2 + (P.vx1 - P.vx0 - 0.4) * j / 4
        out.append(tube([(x, P.base + 0.1, zr), (x, P.base + 0.1, zr - 0.1)], 0.005, P.m("hook", (60, 60, 64)), seg=4))
        out.append(lathe(x, P.base + 0.1, [(0.0, zr - 0.3), (0.09, zr - 0.3), (0.1, zr - 0.12), (0.0, zr - 0.1)], P.m("pot", (176, 110, 70)), seg=12, outline=OL))
    return out


# ---- Sitzmoebel

@model("parkbank", "kirchenbank", "zersplitterte_bank")
def m_benches(P):
    k = P.kind
    if k == "kirchenbank":
        d = min(P.d, 0.6)
        out = M.bench(P.ctx, P.nm, P.x0, P.y0, P.x1, P.y0 + d * 0.75, h=0.45, rgb=(150, 105, 62), leg_rgb=(110, 72, 46))
        out.append(box(P.cx, P.y0 + d - 0.03, P.w, 0.05, 0.45, min(P.h, 1.0), P.m("back", (150, 105, 62)), bevel=0.01, outline=OL))
        for x in (P.x0 + 0.03, P.x1 - 0.03):
            out.append(box(x, P.y0 + d / 2, 0.05, d, 0.0, min(P.h, 1.05), P.m("end", (130, 90, 54)), outline=OL))
        return out
    if k == "zersplitterte_bank":
        out = M.bench(P.ctx, P.nm, P.x0, P.y0, P.x1 - 0.5, P.y1, h=0.44, rgb=(150, 105, 62), leg_rgb=(110, 72, 46), slats=3)
        for j in range(4):
            out.append(obox((P.x1 - 0.25 + P.rnd.uniform(-0.1, 0.1), P.cy + P.rnd.uniform(-0.2, 0.2), 0.02), (0.3, 0.05, 0.02), P.m("splint", (170, 120, 70)), yaw=P.rnd.uniform(-40, 40)))
        return out
    # Parkbank mit Lehne
    out = M.bench(P.ctx, P.nm, P.x0, P.y0, P.x1, P.y1, h=0.44, rgb=(150, 105, 62), leg_rgb=(90, 94, 100), slats=4)
    out.append(box(P.cx, P.y1 - 0.04, P.w, 0.05, 0.6, 0.9, P.m("back", (150, 105, 62)), bevel=0.01, outline=OL))
    out.append(box(P.cx, P.y1 - 0.04, P.w, 0.05, 0.44, 0.55, P.m("back", (150, 105, 62)), bevel=0.01, outline=OL))
    for x in (P.x0 + 0.06, P.x1 - 0.06):
        out.append(box(x, P.y1 - 0.04, 0.04, 0.05, 0.44, 0.9, P.m("leg2", (90, 94, 100))))
    return out


# ---- weitere Familien (aus _atlas_models.py herausgeloest)

@model("aktenschrank", "instrumentenschrank", "gewehrschrank", "kunstblutregal", "walkie_station", "safe", "speiseaufzug")
def m_cabinets(P):
    k = P.kind
    if k == "aktenschrank":
        out = cabinet(P, P.x0, P.y0, P.x1, P.y0 + min(P.d, 0.5), 0.0, P.h, (150, 105, 62))
        out += drawers(P, P.x0 + 0.03, P.x1 - 0.03, P.y0, 0.06, P.h - 0.05, 2, P.m("drawer", (165, 118, 70)), P.m("knob", BRASS), rows=4)
        return out
    if k == "instrumentenschrank":
        out = kind_cabinet_doors(P, (232, 234, 236), nd=2, glass=True, drawers_n=2)
        for j in range(8):
            x = P.x0 + 0.1 + (P.w - 0.2) * (j + 0.5) / 8
            out.append(cyl(x, P.y0 + 0.2, 0.03, P.h * 0.45, P.h * 0.45 + 0.16, P.g(f"jar{j % 3}", [(180, 90, 90), (120, 170, 110), (230, 200, 120)][j % 3], 1.1), seg=8))
        return out
    if k == "gewehrschrank":
        out = kind_cabinet_doors(P, (118, 78, 48), nd=2, glass=True)
        for j in range(5):
            x = P.x0 + 0.12 + (P.w - 0.24) * j / 4
            out.append(tube([(x, P.y0 + 0.2, 0.15), (x + 0.03, P.y0 + 0.2, P.h - 0.2)], 0.014, P.m("rifle", (70, 50, 40)), seg=6))
        ant = P.m("antler", (226, 214, 186))
        for sx in (-1, 1):
            out.append(tube([(P.cx + sx * 0.08, P.y0 + 0.15, P.h), (P.cx + sx * 0.22, P.y0 + 0.15, P.h + 0.22), (P.cx + sx * 0.3, P.y0 + 0.15, P.h + 0.3)], 0.014, ant, seg=6))
            out.append(tube([(P.cx + sx * 0.17, P.y0 + 0.15, P.h + 0.14), (P.cx + sx * 0.1, P.y0 + 0.15, P.h + 0.28)], 0.011, ant, seg=6))
        return out
    if k == "kunstblutregal":
        h = min(P.h * 0.45, 0.9)
        out = counter(P, P.x0, P.y0, P.x1, P.y0 + min(P.d, 0.5), h, (200, 196, 190), (226, 224, 220))
        for j in range(7):
            x = P.x0 + 0.12 + (P.w - 0.24) * j / 6
            out.append(lathe(x, P.y0 + 0.2, [(0.0, h), (0.03, h), (0.03, h + 0.14), (0.012, h + 0.17), (0.012, h + 0.22), (0.0, h + 0.22)], P.m("bottle", (190, 40, 40)), seg=8))
        mz0, mz1 = h + 0.25, P.h - 0.05
        mirror = box(P.cx, P.y0 + 0.08, P.w - 0.2, 0.03, mz0, mz1, P.m("mframe", (120, 80, 40)), outline=OL)
        out.append(mirror)
        im = Image.new("RGB", (256, 128), (150, 190, 210))
        from PIL import ImageDraw, ImageFont
        dr = ImageDraw.Draw(im)
        try:
            f = ImageFont.truetype("arialbd.ttf", 44)
        except Exception:
            f = ImageFont.load_default()
        dr.text((128, 64), "GET OUT", fill=(190, 30, 30), font=f, anchor="mm")
        g = box(P.cx, P.y0 + 0.06, P.w - 0.3, 0.012, mz0 + 0.05, mz1 - 0.05, P.m("mglass", (150, 190, 210)))
        g["front"] = P.tex("getout", im)
        out.append(g)
        for j in range(8):
            out.append(lamp_glow(P, P.x0 + 0.15 + (P.w - 0.3) * j / 7, P.y0 + 0.05, mz1 - 0.02, r=0.025, s=2.6))
        return out
    if k == "walkie_station":
        out = cabinet(P, P.x0, P.y0, P.x1, P.y0 + min(P.d, 0.4), 0.0, P.h, (52, 54, 60), (30, 30, 34))
        for j in range(4):
            x = P.x0 + 0.1 + (P.w - 0.2) * (j + 0.5) / 4
            out.append(box(x, P.y0 + 0.1, 0.07, 0.05, P.h * 0.55, P.h * 0.75, P.m("radio", (40, 42, 48)), outline=OL))
            out.append(cyl(x, P.y0 + 0.1, 0.006, P.h * 0.75, P.h * 0.95, P.m("ant", (90, 90, 96)), seg=6))
            out.append(cyl(x, P.y0 - 0.005, 0.01, P.h * 0.6, P.h * 0.62, P.g("led", (80, 230, 90), 2.0), seg=6))
        out.append(box(P.cx, P.y0 - 0.006, P.w - 0.1, 0.012, P.h * 0.4, P.h * 0.44, P.g("strip", (240, 200, 60), 1.3)))
        return out
    if k == "safe":
        d = min(P.d, 0.6)
        out = cabinet(P, P.x0, P.y0, P.x1, P.y0 + d, 0.0, P.h, (46, 48, 54), (30, 30, 34))
        # offene Tuer: um 100 Grad nach Osten aufgeschwenkt
        out.append(obox((P.x1 + 0.02, P.y0 - P.w * 0.45, P.h / 2), (0.04, P.w - 0.05, P.h - 0.1), P.m("sdoor", (56, 58, 64)), yaw=10.0, outline=OL))
        out.append(cyl(P.x1 + 0.05, P.y0 - P.w * 0.45, 0.05, P.h * 0.5 - 0.05, P.h * 0.5 + 0.05, P.m("dial", (180, 184, 190)), seg=12))
        out.append(box(P.cx, P.y0 + d / 2, P.w - 0.1, d - 0.1, 0.1, P.h - 0.1, P.m("safe_in", (24, 24, 28))))
        out.append(box(P.cx, P.y0 + 0.15, 0.18, 0.12, 0.12, 0.2, P.m("cash", (210, 200, 160))))
        return out
    if k == "speiseaufzug":
        z0, z1 = P.zvis()
        out = [box(P.cx, P.base + 0.06, P.vx1 - P.vx0, 0.12, z0, z1, P.m("hatch_frame", (118, 80, 50)), bevel=0.01, outline=OL),
               box(P.cx, P.base - 0.005, P.vx1 - P.vx0 - 0.1, 0.012, z0 + 0.05, z1 - 0.05, P.m("hatch", (150, 105, 62)), outline=OL),
               cyl(P.cx, P.base - 0.015, 0.012, (z0 + z1) / 2, (z0 + z1) / 2 + 0.03, P.m("knob", BRASS), seg=6)]
        return out
    return None


@model("tisch", "kuechentisch", "beistelltisch", "lesetisch", "schreibtisch", "hackblock", "obduktionstisch", "hobelbank",
       "funktisch", "schminktisch", "waechterpult", "kristallkugel_tisch", "seance_tisch")
def m_tables(P):
    k = P.kind
    if k == "tisch":
        out = kind_desk(P, WOOD, drawers_side=False, items=[lambda P, h: it_candle(P, h, dx=-P.w * 0.3), lambda P, h: [cyl(P.cx, P.cy, 0.09, h, h + 0.008, P.m("plate", (230, 228, 220)), seg=16)]])
        out += chair(P, P.x1 + 0.28, P.cy, yaw=90.0, rgb=WOOD_D)
        return out
    if k == "kuechentisch":
        out = kind_desk(P, (176, 126, 80), h=min(P.h, 0.8), drawers_side=False)
        out.append(obox((P.cx - 0.1, P.cy, min(P.h, 0.8) + 0.01), (0.32, 0.08, 0.02), P.m("cleaver", (190, 194, 200)), yaw=25.0))
        out.append(cyl(P.cx - 0.05, P.cy + 0.02, 0.12, min(P.h, 0.8), min(P.h, 0.8) + 0.003, P.m("blood", (130, 20, 24)), seg=16, ry=0.08))
        out.append(lathe(P.x1 - 0.25, P.cy, [(0.0, min(P.h, 0.8)), (0.03, min(P.h, 0.8)), (0.03, min(P.h, 0.8) + 0.12), (0.012, min(P.h, 0.8) + 0.16), (0.0, min(P.h, 0.8) + 0.2)], P.m("bottle", (200, 40, 40)), seg=8))
        return out
    if k == "beistelltisch":
        h = min(P.h, 0.7)
        out = M.table(P.ctx, P.nm, P.x0, P.y0, P.x1, P.y1, h=h, top_rgb=WALNUT, leg_rgb=WOOD_D, pedestal=True, round_=True)
        out.append(lathe(P.cx, P.cy, [(0.0, h), (0.035, h), (0.035, h + 0.16), (0.014, h + 0.2), (0.014, h + 0.26), (0.0, h + 0.26)], P.m("bottle", (190, 150, 60)), seg=8))
        out.append(cyl(P.cx - 0.12, P.cy, 0.03, h, h + 0.08, P.glass("tumbler", a=120), seg=8))
        return out
    if k == "lesetisch":
        return kind_desk(P, WOOD, h=min(P.h, 0.76), drawers_side=False, items=[it_lamp, it_book, lambda P, h: it_candle(P, h, dx=-P.w * 0.35)])
    if k == "schreibtisch":
        green = P.sc.key == "villa"
        out = kind_desk(P, (118, 80, 50), h=min(P.h, 0.78), items=[it_lamp, lambda P, h: it_paper(P, h, dx=-0.25, dy=0.05)])
        if green:
            out.append(box(P.cx, P.cy, P.w - 0.12, P.d - 0.12, min(P.h, 0.78), min(P.h, 0.78) + 0.004, P.m("leather", (60, 92, 70))))
            out += it_typewriter(P, min(P.h, 0.78) + 0.004, dx=0.1)
        else:
            out += it_book(P, min(P.h, 0.78), dx=0.05)
            out += it_skull(P, min(P.h, 0.78), dx=P.w * 0.3, dy=-0.1)
        return out
    if k == "hackblock":
        h = min(P.h, 0.85)
        out = [box(P.cx, P.cy, P.w, P.d, 0.0, h, P.m("block", (150, 105, 62)), bevel=0.02, outline=OL),
               box(P.cx, P.cy, P.w - 0.1, P.d - 0.1, h, h + 0.004, P.m("blood", (130, 20, 24))),
               obox((P.cx, P.cy + 0.05, h + 0.012), (0.34, 0.06, 0.012), P.m("knife", (200, 204, 210)), yaw=-30.0)]
        return out
    if k == "obduktionstisch":
        h = min(P.h, 0.85)
        out = [box(P.cx, P.cy, P.w, P.d, h - 0.06, h, P.m("steel", (196, 202, 208)), bevel=0.012, outline=OL),
               box(P.cx, P.cy, P.w - 0.1, P.d - 0.1, h - 0.02, h + 0.002, P.m("steel_d", (170, 176, 184)))]
        out += legs4(P, P.x0, P.y0, P.x1, P.y1, 0.0, h - 0.06, P.m("leg", (120, 126, 134)), s=0.05, inset=0.1)
        out.append(cyl(P.cx + 0.3, P.cy, 0.04, h, h + 0.01, P.m("tray", (90, 94, 100)), seg=10))
        return out
    if k == "hobelbank":
        h = min(P.h, 0.85)
        out = M.table(P.ctx, P.nm, P.x0, P.y0, P.x1, P.y1, h=h, top_rgb=(166, 118, 72), leg_rgb=(110, 72, 46), thick=0.09)
        out.append(box(P.x1 - 0.08, P.cy, 0.1, 0.24, h - 0.06, h + 0.04, P.m("vise", (90, 94, 100)), outline=OL))
        for j in range(5):
            out.append(blob(P.cx + P.rnd.uniform(-0.4, 0.4), P.y0 - 0.15 + P.rnd.uniform(-0.1, 0.1), 0.0, 0.05, 0.03, 0.02, (P.m("shav", (220, 190, 130)), P.m("shav", (220, 190, 130))), seed=j, seg=6, rings=3))
        return out
    if k == "funktisch":
        h = min(P.h, 0.78)
        out = kind_desk(P, (118, 80, 50), h=h, drawers_side=True, items=[lambda P, h: it_lamp(P, h, dx=0.9, rgb=(70, 140, 80))])
        out.append(box(P.cx, P.cy + 0.05, 0.6, 0.35, h, h + 0.3, P.m("radio", (56, 58, 64)), bevel=0.01, outline=OL))
        out.append(box(P.cx, P.cy - 0.13, 0.4, 0.01, h + 0.08, h + 0.24, P.g("dialglass", (120, 200, 160), 1.3)))
        out.append(cyl(P.cx + 0.4, P.cy - 0.1, 0.012, h, h + 0.22, P.m("mic", (90, 90, 96)), seg=6))
        out.append(lathe(P.cx + 0.4, P.cy - 0.1, [(0.0, h + 0.2), (0.04, h + 0.24), (0.0, h + 0.3)], P.m("mic", (90, 90, 96)), seg=8))
        return out
    if k == "schminktisch":
        h = min(P.h * 0.4, 0.78)
        out = counter(P, P.x0, P.y0, P.x1, P.y0 + min(P.d, 0.55), h, (150, 105, 62), (170, 122, 76))
        out += drawers(P, P.x0 + 0.05, P.x1 - 0.05, P.y0, 0.1, h - 0.1, 3, P.m("drawer", (160, 112, 66)), P.m("knob", BRASS))
        z1 = P.h - 0.05
        out.append(box(P.cx, P.y0 + 0.4, P.w - 0.15, 0.04, h + 0.1, z1, P.m("mframe", (120, 80, 40)), outline=OL))
        out.append(box(P.cx, P.y0 + 0.375, P.w - 0.3, 0.012, h + 0.18, z1 - 0.08, P.m("mirror", (170, 205, 225))))
        for j in range(9):
            out.append(lamp_glow(P, P.x0 + 0.1 + (P.w - 0.2) * j / 8, P.y0 + 0.36, z1 - 0.03, r=0.025, s=2.6))
        for j in range(3):
            out.append(cyl(P.x0 + 0.25 + j * 0.1, P.y0 + 0.15, 0.02, h, h + 0.12, P.m(f"flask{j}", [(190, 40, 40), (60, 60, 60), (230, 230, 220)][j]), seg=8))
        return out
    if k == "waechterpult":
        h = min(P.h * 0.45, 0.95)
        out = counter(P, P.x0, P.y0, P.x1, P.y1, h, (150, 105, 62), (166, 118, 72))
        out += doors(P, P.x0 + 0.04, P.x1 - 0.04, P.y0, 0.08, h - 0.08, 3, P.m("door", (158, 110, 66)), P.m("knob", BRASS))
        out += it_book(P, h, dx=0.0)
        out.append(cyl(P.x0 + 0.2, P.cy, 0.05, h, h + 0.16, P.g("lant", (255, 210, 120), 2.2), seg=8))
        return out
    if k == "kristallkugel_tisch":
        h = min(P.h * 0.7, 0.7)
        out = M.table(P.ctx, P.nm, P.x0, P.y0, P.x1, P.y1, h=h, top_rgb=(90, 40, 50), leg_rgb=(60, 40, 30), pedestal=True, round_=True)
        out.append(cyl(P.cx, P.cy, 0.06, h, h + 0.03, P.m("stand", BRASS), seg=12))
        out.append(lathe(P.cx, P.cy, [(0.0, h + 0.03), (0.08, h + 0.06), (0.1, h + 0.13), (0.08, h + 0.2), (0.0, h + 0.23)], P.g("ball", (180, 220, 255), 2.4), seg=14))
        return out
    if k == "seance_tisch":
        h = min(P.h * 0.7, 0.72)
        out = M.table(P.ctx, P.nm, P.x0, P.y0, P.x1, P.y1, h=h, top_rgb=(150, 40, 60), leg_rgb=(60, 40, 30), pedestal=True, round_=True)
        out.append(box(P.cx, P.cy, P.w, P.d, h - 0.12, h - 0.05, P.m("cloth", (130, 32, 50))))
        out.append(cyl(P.cx, P.cy, P.w / 2 + 0.01, h - 0.3, h - 0.1, P.m("cloth", (130, 32, 50)), ry=P.d / 2 + 0.01, seg=32))
        for a in (30, 150, 270):
            out += candle(P, P.cx + P.w * 0.35 * math.cos(math.radians(a)), P.cy + P.d * 0.35 * math.sin(math.radians(a)), h, 0.14)
        out.append(lathe(P.cx + 0.3, P.cy - 0.1, [(0.0, h), (0.07, h + 0.03), (0.09, h + 0.1), (0.07, h + 0.17), (0.0, h + 0.2)], P.g("ball", (180, 220, 255), 2.2), seg=12))
        out.append(box(P.cx - 0.2, P.cy, 0.3, 0.2, h, h + 0.005, P.m("board", (226, 214, 180)), rot=-10.0))
        return out
    return None


@model("sessel", "lesesessel", "schaukelstuhl", "drehstuhl", "regiestuhl", "regiestuhl_director", "umgestuerzter_stuhl")
def m_chairs(P):
    k = P.kind
    if k == "sessel":
        return armchair(P, P.x0, P.y0, P.x1, P.y1, (120, 70, 160), (90, 50, 120))
    if k == "lesesessel":
        return armchair(P, P.x0, P.y0, P.x1, P.y1, (40, 110, 90), (30, 80, 66))
    if k == "schaukelstuhl":
        out = chair(P, P.cx, P.cy, yaw=0.0, rgb=(120, 80, 50), seat_z=0.4, w=min(P.w, 0.5), back_h=0.55)
        for sx in (-1, 1):
            out.append(tube([(P.cx + sx * 0.22, P.cy - 0.4, 0.05), (P.cx + sx * 0.22, P.cy, 0.0), (P.cx + sx * 0.22, P.cy + 0.4, 0.05)], 0.015, P.m("rocker", (120, 80, 50)), seg=6))
        return out
    if k == "drehstuhl":
        from bm_spec import office_chair
        return office_chair(P.ctx, P.nm, P.cx, P.cy, (120, 80, 50), (40, 40, 44), OL, back="N", w=min(P.w, 0.5))
    if k.startswith("regiestuhl"):
        w = min(P.w, 0.55)
        cv = P.m("canvas", (60, 62, 72))
        wood = P.m("wood", (150, 105, 62))
        out = [box(P.cx, P.cy, w, w * 0.8, 0.44, 0.46, cv, outline=OL),
               box(P.cx, P.cy + w * 0.4, w, 0.02, 0.7, 0.9, cv, outline=OL)]
        im = Image.new("RGB", (160, 40), (60, 62, 72))
        from PIL import ImageDraw, ImageFont
        try:
            f = ImageFont.truetype("arialbd.ttf", 20)
        except Exception:
            f = ImageFont.load_default()
        ImageDraw.Draw(im).text((80, 20), "DIRECTOR", fill=(220, 220, 220), font=f, anchor="mm")
        out[-1]["front"] = P.tex("dir", im)
        for sx in (-1, 1):
            out.append(tube([(P.cx + sx * w * 0.45, P.cy - w * 0.4, 0.0), (P.cx + sx * w * 0.45, P.cy + w * 0.4, 0.44)], 0.014, wood, seg=6))
            out.append(tube([(P.cx + sx * w * 0.45, P.cy + w * 0.4, 0.0), (P.cx + sx * w * 0.45, P.cy - w * 0.4, 0.44)], 0.014, wood, seg=6))
            out.append(cyl(P.cx + sx * w * 0.45, P.cy + w * 0.4, 0.014, 0.44, 0.92, wood, seg=6))
        return out
    if k == "umgestuerzter_stuhl":
        # liegender Stuhl: Sitzflaeche senkrecht, Beine nach Osten
        wood = P.m("wood", (150, 105, 62))
        w = 0.42
        out = [obox((P.cx - 0.1, P.cy, 0.21), (0.04, w, w), wood, outline=OL),
               obox((P.cx - 0.1 - 0.45, P.cy, 0.21), (0.04, w, w * 0.9), wood, outline=OL)]
        for sy in (-1, 1):
            for z in (0.05, 0.37):
                out.append(tube([(P.cx - 0.08, P.cy + sy * w * 0.42, z), (P.cx + 0.35, P.cy + sy * w * 0.42, z)], 0.016, wood, seg=6))
        return out
    return None


@model("craftservice")
def m_counters(P):
    k = P.kind
    if k == "craftservice":
        h = min(P.h * 0.5, 0.9)
        out = cabinet(P, P.x0, P.y0, P.x0 + P.w * 0.65, P.y0 + min(P.d, 0.5), 0.0, h, (150, 105, 62))
        out += doors(P, P.x0 + 0.03, P.x0 + P.w * 0.65 - 0.03, P.y0, 0.06, h - 0.05, 2, P.m("door", (160, 112, 66)), P.m("knob", BRASS))
        out.append(lathe(P.x0 + P.w * 0.3, P.y0 + 0.25, [(0.0, h), (0.1, h), (0.1, h + 0.3), (0.06, h + 0.33), (0.0, h + 0.34)], P.m("urn", (190, 194, 200)), seg=14, outline=OL))
        out.append(box(P.x0 + P.w * 0.3, P.y0 + 0.1, 0.22, 0.12, h, h + 0.05, P.m("box", (230, 170, 190)), outline=OL))
        out.append(box(P.x1 - 0.2, P.y0 + 0.2, 0.3, 0.3, 0.0, 0.22, P.m("crate", (120, 80, 50)), outline=OL))
        for j in range(2):
            out.append(cyl(P.x1 - 0.3 + j * 0.14, P.y0 + 0.2, 0.04, 0.22, 0.32, P.m("cup", (236, 236, 230)), seg=8))
        return out
    return None


@model("kupferkessel", "nebelmaschine", "filmkamera", "scheinwerfer", "ofen", "kanonenofen", "mangel", "phonograph", "orrery",
       "teleskop", "globus", "globusbar", "laternenpfahl", "laterne", "kandelaber", "saeule", "menhir", "taufbecken", "urne",
       "opferkerzen", "kamin", "altar", "brunnen", "trog", "fass", "waschzuber")
def m_machines(P):
    k = P.kind
    cx, cy, w, d, h = P.cx, P.cy, P.w, P.d, P.h
    if k == "kupferkessel":
        r = min(w, d) * 0.42
        out = [box(cx, cy, w * 0.9, d * 0.9, 0.0, 0.35, P.m("stove", (130, 70, 50)), outline=OL),
               box(cx, P.y0 + 0.03, w * 0.5, 0.02, 0.05, 0.25, P.m("stove_d", (40, 30, 30))),
               lathe(cx, cy, [(0.0, 0.35), (r * 0.9, 0.35), (r, 0.5), (r, h - 0.15), (r * 0.95, h), (0.0, h)], P.m("copper", (184, 110, 70)), seg=24, outline=OL),
               cyl(cx, cy, r * 0.9, h - 0.02, h, P.m("brew", (90, 60, 40)), seg=20)]
        for j in range(2):
            out.append(blob(cx + 0.08 * j, cy, h + 0.15 + j * 0.2, 0.08, 0.08, 0.1, (P.m("steam", (200, 200, 210)), P.m("steam", (200, 200, 210))), seed=j, seg=8, rings=4))
        return out
    if k == "nebelmaschine":
        out = [box(P.x1 - 0.4, cy, 0.7, min(d, 0.5), 0.0, 0.35, P.m("body", (40, 42, 48)), bevel=0.012, outline=OL),
               obox((P.x1 - 0.4, cy + 0.1, 0.5), (0.6, 0.02, 0.3), P.m("lid", (50, 52, 58)), roll=-70.0, outline=OL),
               cyl(P.x1 - 0.2, P.y0 + 0.01, 0.012, 0.2, 0.22, P.g("led", (80, 230, 90), 2.0), seg=6)]
        for j in range(4):
            out.append(blob(P.x0 + 0.2 + j * 0.25, cy + P.rnd.uniform(-0.15, 0.15), 0.12, 0.22, 0.18, 0.12, (P.m("fog", (200, 200, 210)), P.m("fog", (200, 200, 210))), seed=j, seg=8, rings=4))
        return out
    if k == "filmkamera":
        dk, st = P.m("cam", (50, 52, 58)), P.m("steel", (150, 156, 164))
        out = [box(cx, cy, w * 0.6, min(d, 0.6), 0.0, 0.1, dk, outline=OL)]
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            out.append(cyl(cx + sx * w * 0.27, cy + sy * min(d, 0.6) * 0.42, 0.05, 0.0, 0.1, P.m("wheel", (30, 30, 34)), seg=10))
        out.append(cyl(cx, cy, 0.03, 0.1, h * 0.62, st, seg=8))
        out.append(box(cx, cy, 0.45, 0.3, h * 0.62, h * 0.85, dk, bevel=0.01, outline=OL))
        for sx in (-1, 1):
            out.append(wheel(P, cx + sx * 0.14, cy, h * 0.85 + 0.12, 0.13, 0.04, dk, axis="y"))
        zl = h * 0.74
        out.append(lathe(cx, P.y0 - 0.05, [(0.0, zl - 0.08), (0.06, zl - 0.08), (0.08, zl + 0.08), (0.0, zl + 0.08)], dk, seg=12, outline=OL, tilt=(-90.0, 90.0, zl)))
        out.append(tube([(P.x1 - 0.1, cy, 0.9), (P.x1 + 0.4, cy, 0.3)], 0.012, st, seg=6))
        return out
    if k == "scheinwerfer":
        st = P.m("steel", (120, 126, 134))
        px, py = P.x1 - 0.3, cy
        out = tripod(P, px, py, 1.1, spread=0.3, r=0.014, mat=st)
        out.append(lathe(px, py, [(0.0, 1.08), (0.13, 1.08), (0.16, 1.33), (0.0, 1.33)], P.m("head", (60, 62, 70)), seg=14, outline=OL, tilt=(70.0, 60.0, 1.2)))
        out.append(lathe(px, py, [(0.0, 1.33), (0.15, 1.33), (0.0, 1.34)], P.g("lens", (255, 250, 230), 3.0), seg=14, tilt=(70.0, 60.0, 1.2)))
        # Lichtkegel auf dem Boden (flach, leuchtend)
        ell = affinity.scale(sbox(P.x0, P.y0, P.x0 + w * 0.6, P.y1).centroid.buffer(1.0, 32), w * 0.3, d * 0.35)
        out.append(prism(affinity.rotate(ell, 20.0), 0.0, 0.004, P.g("beam", (200, 220, 240), 0.8)))
        return out
    if k == "ofen":
        brick, steel = P.m("brick", (130, 70, 56)), P.m("steel", (70, 72, 80))
        hb = h * 0.55
        out = [box(cx, cy, w, d, 0.0, hb, brick, outline=OL),
               box(cx, cy, w * 0.85, d * 0.85, hb, h * 0.75, steel, bevel=0.01, outline=OL),
               cyl(P.x0 + w * 0.25, cy, 0.14, h * 0.75, h, steel, seg=14, outline=OL),
               box(cx, P.y0 + 0.012, w * 0.3, 0.03, hb * 0.25, hb * 0.65, P.m("door", (90, 92, 100)), outline=OL),
               box(cx, P.y0 + 0.0, w * 0.22, 0.012, hb * 0.3, hb * 0.6, P.g("fire", (255, 150, 60), 2.4)),
               cyl(cx + w * 0.2, P.y0 + 0.01, 0.03, hb * 0.45, hb * 0.5, P.g("led", (230, 70, 60), 2.0), seg=8)]
        for j in range(3):
            out.append(box(cx + w * 0.3, P.y0 - 0.1 + j * 0.25, 0.3, 0.05, 0.02, 0.05, P.m("rail", (80, 82, 90))))
        for j in range(2):
            out.append(blob(P.x0 + w * 0.25, cy, h + 0.2 + j * 0.25, 0.1, 0.1, 0.12, (P.m("smoke", (180, 180, 190)), P.m("smoke", (180, 180, 190))), seed=j, seg=8, rings=4))
        return out
    if k == "kanonenofen":
        iron = P.m("iron", (60, 56, 60))
        r = min(w, d) * 0.3
        out = [cyl(cx, cy, r * 1.1, 0.0, 0.05, iron, seg=16, outline=OL),
               lathe(cx, cy, [(0.0, 0.05), (r * 0.6, 0.05), (r, 0.3), (r, h * 0.55), (r * 0.6, h * 0.68), (0.0, h * 0.7)], P.m("belly", (90, 60, 50)), seg=20, outline=OL),
               cyl(cx, cy, 0.06, h * 0.7, h, iron, seg=12),
               box(cx, cy - r + 0.01, r * 0.8, 0.02, 0.2, 0.42, P.g("grate", (255, 150, 50), 2.4)),
               lathe(cx, cy, [(0.0, h), (0.12, h), (0.12, h + 0.02), (0.0, h + 0.02)], iron, seg=12)]
        for z in (0.3, h * 0.5):
            out.append(lathe(cx, cy, [(r * 0.98, z), (r * 1.04, z), (r * 1.04, z + 0.03), (r * 0.98, z + 0.03)], iron, seg=20))
        return out
    if k == "mangel":
        wood = P.m("wood", (150, 105, 62))
        out = [box(cx, cy, w, min(d, 0.7), 0.0, 0.55, wood, outline=OL),
               box(cx, cy, w, 0.06, 0.55, h - 0.1, wood, outline=OL)]
        for z in (h - 0.35, h - 0.2):
            out.append(lathe(cx, cy, [(0.0, z - w / 2 + 0.05), (0.07, z - w / 2 + 0.05), (0.07, z + w / 2 - 0.05), (0.0, z + w / 2 - 0.05)], P.m("roller", (170, 120, 70)), seg=14, outline=OL, tilt=(90.0, 0.0, z)))
        out.append(tube([(P.x1 - 0.05, cy, h - 0.2), (P.x1 + 0.25, cy, h - 0.05)], 0.015, P.m("crank", (60, 60, 64)), seg=6))
        out.append(obox((cx, P.y0 - 0.15, 0.35), (w * 0.6, 0.02, 0.4), P.m("sheet", (236, 236, 230)), roll=-25.0))
        return out
    if k == "phonograph":
        out = cabinet(P, P.x0, P.y0, P.x1, P.y0 + min(d, 0.5), 0.0, h * 0.45, (118, 80, 50))
        out += doors(P, P.x0 + 0.03, P.x1 - 0.03, P.y0, 0.06, h * 0.45 - 0.05, 1, P.m("door", (128, 86, 54)), P.m("knob", BRASS))
        out.append(cyl(cx - 0.1, cy + 0.1, 0.15, h * 0.45, h * 0.45 + 0.01, P.m("record", (30, 30, 34)), seg=20))
        zh = h * 0.45 + 0.1
        out.append(lathe(cx + 0.15, cy + 0.05, [(0.0, zh), (0.03, zh), (0.09, zh + 0.35), (0.2, zh + 0.5), (0.18, zh + 0.52), (0.0, zh + 0.52)], P.m("horn", (201, 162, 76)), seg=16, outline=OL, tilt=(45.0, 0.0, zh)))
        return out
    if k == "orrery":
        out = [cyl(cx, cy, min(w, d) * 0.4, 0.0, 0.06, P.m("base", (118, 80, 50)), seg=20, outline=OL),
               cyl(cx, cy, 0.03, 0.06, h * 0.55, P.m("column", (60, 44, 34)), seg=10),
               lathe(cx, cy, [(0.0, h * 0.55), (0.05, h * 0.57), (0.06, h * 0.63), (0.0, h * 0.66)], P.g("sun", (240, 200, 80), 2.4), seg=12)]
        for j, (r, c) in enumerate(((0.15, (200, 120, 60)), (0.26, (80, 120, 200)), (0.38, (200, 80, 60)))):
            z = h * 0.6
            out.append(lathe(cx, cy, [(r - 0.005, z - 0.003), (r + 0.005, z - 0.003), (r + 0.005, z + 0.003), (r - 0.005, z + 0.003)], P.m("ring", BRASS), seg=32))
            a = j * 2.1
            out.append(lathe(cx + r * math.cos(a), cy + r * math.sin(a), [(0.0, z - 0.02), (0.022, z), (0.0, z + 0.02)], P.m(f"planet{j}", c), seg=8))
        return out
    if k == "teleskop":
        st = P.m("wood", (150, 105, 62))
        out = tripod(P, cx, cy, 1.0, spread=0.35, r=0.014, mat=st)
        out.append(lathe(cx, cy, [(0.0, 0.7), (0.05, 0.7), (0.06, 1.55), (0.07, 1.6), (0.0, 1.6)], P.m("tube", (201, 162, 76)), seg=14, outline=OL, tilt=(-55.0, 0.0, 1.15)))
        return out
    if k in ("globus", "globusbar"):
        st = P.m("wood", (118, 80, 50))
        r = min(w, d) * 0.4
        zc = h * 0.55
        out = tripod(P, cx, cy, zc - r * 0.5, spread=0.3, r=0.014, mat=st)
        if k == "globus":
            out.append(lathe(cx, cy, [(0.0, zc - r), (r * 0.7, zc - r * 0.7), (r, zc), (r * 0.7, zc + r * 0.7), (0.0, zc + r)], P.m("globe", (226, 206, 150)), seg=18, outline=OL))
            out.append(lathe(cx, cy, [(r * 1.05, zc - 0.01), (r * 1.1, zc - 0.01), (r * 1.1, zc + 0.01), (r * 1.05, zc + 0.01)], P.m("ring", BRASS), seg=24, tilt=(20.0, 0.0, zc)))
            out.append(tube([(cx, cy - r * 0.4, zc - r), (cx, cy - r * 0.4, zc + r + 0.05), (cx, cy, zc + r + 0.05)], 0.01, P.m("ring", BRASS), seg=6))
            return out
        out.append(lathe(cx, cy, [(0.0, zc - r), (r * 0.7, zc - r * 0.7), (r, zc), (r * 0.96, zc + 0.02), (0.0, zc + 0.02)], P.m("globe", (226, 206, 150)), seg=18, outline=OL))
        out.append(lathe(cx, cy + r * 0.6, [(0.0, zc + 0.05), (r, zc + 0.05), (r * 0.7, zc + 0.05 + r * 0.7), (0.0, zc + 0.05 + r)], P.m("globe", (226, 206, 150)), seg=18, outline=OL, tilt=(-60.0, 0.0, zc + 0.05)))
        for j in range(3):
            x = cx - 0.1 + j * 0.1
            out.append(lathe(x, cy, [(0.0, zc), (0.025, zc), (0.025, zc + 0.14), (0.01, zc + 0.17), (0.01, zc + 0.22), (0.0, zc + 0.22)], P.m(f"bottle{j}", [(80, 40, 30), (60, 90, 60), (160, 110, 40)][j]), seg=8))
        return out
    if k == "laternenpfahl":
        st = P.m("post", (50, 52, 58))
        x = (P.vx0 + P.vx1) / 2
        y = P.base + 0.15
        out = [cyl(x, y, 0.1, 0.0, 0.06, st, seg=12, outline=OL), cyl(x, y, 0.03, 0.06, h - 0.3, st, seg=10)]
        out.append(lathe(x, y, [(0.0, h - 0.3), (0.12, h - 0.3), (0.12, h - 0.1), (0.0, h)], P.g("lamp", (255, 220, 140), 2.8), seg=8))
        out.append(lathe(x, y, [(0.0, h - 0.32), (0.15, h - 0.3), (0.0, h - 0.3)], st, seg=8))
        out.append(lathe(x, y, [(0.0, h - 0.1), (0.15, h - 0.1), (0.0, h + 0.04)], st, seg=8))
        return out
    if k == "laterne":
        x, y = cx, cy
        return [cyl(x, y, 0.09, 0.0, 0.03, P.m("base", (60, 60, 64)), seg=10),
                box(x, y, 0.12, 0.12, 0.03, 0.26, P.g("glass", (255, 220, 140), 2.6), bevel=0.01),
                lathe(x, y, [(0.0, 0.26), (0.08, 0.26), (0.0, 0.33)], P.m("base", (60, 60, 64)), seg=8),
                tube([(x - 0.06, y, 0.33), (x, y, 0.42), (x + 0.06, y, 0.33)], 0.006, P.m("base", (60, 60, 64)), seg=5)]
    if k == "kandelaber":
        iron = P.m("iron", (50, 48, 54))
        x, y = cx, P.base + 0.2
        out = [lathe(x, y, [(0.0, 0.0), (0.12, 0.0), (0.04, 0.05), (0.03, 0.06), (0.0, 0.06)], iron, seg=10), cyl(x, y, 0.018, 0.06, h - 0.3, iron, seg=8)]
        for sx in (-1, 0, 1):
            top = h - 0.3 + (0.08 if sx == 0 else 0.0)
            if sx:
                out.append(tube([(x, y, h - 0.4), (x + sx * 0.12, y, h - 0.3), (x + sx * 0.12, y, top)], 0.008, iron, seg=5))
            out += candle(P, x + sx * 0.12, y, top, 0.14, 0.014)
        return out
    if k == "saeule":
        r = w * 0.3
        stone = P.m("stone", (220, 216, 206))
        out = [box(cx, cy, w, min(d, w), 0.0, 0.15, stone, bevel=0.01, outline=OL),
               cyl(cx, cy, r, 0.15, h - 0.15, stone, seg=20, outline=OL),
               box(cx, cy, w * 0.9, min(d, w) * 0.9, h - 0.15, h, stone, bevel=0.01, outline=OL)]
        pts = [(cx + r * 1.02 * math.cos(t * 0.9), cy + r * 1.02 * math.sin(t * 0.9), 0.2 + (h - 0.5) * t / 7) for t in range(8)]
        out.append(tube(pts, 0.012, P.m("ivy", (60, 110, 60)), seg=5))
        return out
    if k == "menhir":
        mats = (P.m("rock", (140, 136, 160)), P.m("rock_d", (100, 96, 122)), None)
        out = [boulder(cx, cy + 0.1, w * 0.42, min(d, 0.7) * 0.4, h, mats, seed=P.seed, seg=12, rings=8, cap=1.0, outline=OL)]
        for j in range(3):
            out.append(box(cx + P.rnd.uniform(-0.15, 0.15), P.y0 - 0.02, 0.06, 0.012, h * 0.3 + j * 0.2, h * 0.3 + j * 0.2 + 0.12, P.g("rune", (90, 230, 160), 2.4)))
        out.append(blob(P.x1 - 0.2, P.y0, 0.0, 0.08, 0.06, 0.06, (P.m("moss", (70, 120, 60)), P.m("moss", (70, 120, 60))), seed=1, seg=6, rings=3))
        return out
    if k == "taufbecken":
        stone = P.m("stone", (200, 204, 216))
        return [lathe(cx, cy, [(0.0, 0.0), (0.3, 0.0), (0.2, 0.06), (0.1, 0.1), (0.08, 0.6), (0.14, 0.68), (0.35, 0.78), (0.38, 0.9), (0.0, 0.9)], stone, seg=24, outline=OL),
                cyl(cx, cy, 0.3, 0.86, 0.88, P.g("water", (40, 60, 110), 0.8), seg=24)]
    if k == "urne":
        stone = P.m("stone", (190, 194, 204))
        hb = h * 0.5
        return [box(cx, cy, w * 0.8, min(d, 0.6), 0.0, hb, stone, bevel=0.012, outline=OL),
                lathe(cx, cy, [(0.0, hb), (0.1, hb), (0.06, hb + 0.05), (0.14, hb + 0.25), (0.08, hb + 0.4), (0.1, hb + 0.45), (0.0, hb + 0.45)], P.m("urn", (201, 162, 76)), seg=16, outline=OL)]
    if k == "opferkerzen":
        wood = P.m("wood", (118, 80, 50))
        out = []
        for j in range(3):
            z = 0.5 + j * 0.2
            yy = P.y0 + 0.12 + j * 0.2
            out.append(box(cx, yy, w - j * 0.3, 0.16, z - 0.04, z, wood, outline=OL))
            n = 6 - j
            for i in range(n):
                out += candle(P, P.x0 + 0.15 + j * 0.15 + (w - 0.3 - j * 0.3) * (i + 0.5) / n, yy, z, 0.08 + P.rnd.uniform(0, 0.05), 0.014)
        for x in (P.x0 + 0.05, P.x1 - 0.05):
            out.append(box(x, cy, 0.04, min(d, 0.6), 0.0, 0.48, wood))
        out.append(box(cx, P.y0 + 0.1, 0.2, 0.12, 0.0, 0.08, P.m("box", (201, 162, 76))))
        return out
    if k == "kamin":
        stone = P.m("stone", (232, 230, 226))
        hd = min(d, 0.7)
        out = [box(cx, cy, w, hd, 0.0, h * 0.8, stone, outline=OL),
               box(cx, cy, w + 0.1, hd + 0.05, h * 0.8, h * 0.88, stone, bevel=0.015, outline=OL),
               box(cx, P.y0 + 0.3, w * 0.55, 0.012, 0.05, h * 0.55, P.m("hearth", (30, 26, 26))),
               box(cx, P.y0 + 0.1, w * 0.3, 0.12, 0.1, 0.2, P.m("log", (60, 40, 30)), rot=10.0),
               lathe(cx, P.y0 + 0.15, [(0.0, 0.08), (0.14, 0.14), (0.08, 0.35), (0.0, 0.5)], P.g("fire", (255, 150, 50), 2.6), seg=10),
               prism(affinity.scale(sbox(P.x0, P.y0 - 0.3, P.x1, P.y0).centroid.buffer(1.0, 24), w * 0.4, 0.3), 0.0, 0.003, P.g("fireglow", (200, 120, 50), 0.6))]
        # Kaminbogen: dunkle Oeffnung an der Front
        out.append(box(cx, P.y0 + 0.012, w * 0.5, 0.024, 0.0, h * 0.5, P.m("hearth", (30, 26, 26))))
        for sx in (-1, 1):
            out += candle(P, cx + sx * w * 0.35, cy, h * 0.88, 0.12)
        out.append(lathe(cx, cy, [(0.0, h * 0.88), (0.06, h * 0.88), (0.04, h * 0.88 + 0.12), (0.0, h * 0.88 + 0.14)], P.m("vase", (201, 162, 76)), seg=10))
        return out
    if k == "altar":
        stone = P.m("stone", (226, 228, 232))
        hb = min(h * 0.4, 1.0)
        out = [box(cx, cy, w, min(d, 0.9), 0.0, hb, stone, bevel=0.01, outline=OL),
               box(cx, cy, w + 0.06, min(d, 0.9) + 0.06, hb - 0.04, hb, stone, bevel=0.01, outline=OL),
               box(cx, cy, w * 0.9, min(d, 0.9) * 0.9, hb, hb + 0.01, P.m("cloth", (150, 40, 50)))]
        for sx in (-1, 1):
            out += candle(P, cx + sx * w * 0.38, cy, hb, 0.18)
        out += it_book(P, hb + 0.01, dx=-0.15)
        out.append(lathe(cx + 0.2, cy, [(0.0, hb), (0.04, hb), (0.015, hb + 0.08), (0.04, hb + 0.14), (0.0, hb + 0.15)], P.m("chalice", BRASS), seg=10))
        if P.sc.key == "graveyard":
            cr = P.m("cross", (118, 80, 50))
            out.append(box(cx, cy + 0.2, 0.08, 0.08, hb, h, cr))
            out.append(box(cx, cy + 0.2, w * 0.35, 0.06, h - 0.55, h - 0.47, cr))
        else:
            out.append(box(cx, P.y1 - 0.06, w, 0.1, hb, h, P.m("back", (236, 232, 220)), outline=OL))
            out.append(box(cx, P.y1 - 0.12, w * 0.5, 0.012, hb + 0.3, hb + 0.5, P.m("plaque", (120, 100, 70))))
            out += candle(P, cx, P.y1 - 0.15, hb + 0.55, 0.12)
        return out
    if k == "brunnen":
        stone = P.m("stone", (190, 194, 204))
        r = w * 0.42
        out = [lathe(cx, cy, [(0.0, 0.0), (r, 0.0), (r, 0.75), (r * 0.78, 0.75), (r * 0.78, 0.1), (0.0, 0.1)], stone, seg=24, outline=OL),
               cyl(cx, cy, r * 0.76, 0.4, 0.42, P.g("water", (30, 40, 70), 0.6), seg=20)]
        for sx in (-1, 1):
            out.append(box(cx + sx * (r - 0.05), cy, 0.08, 0.08, 0.75, h - 0.25, P.m("post", (118, 80, 50))))
        out.append(tube([(cx - r, cy, h - 0.45), (cx + r, cy, h - 0.45)], 0.03, P.m("post", (118, 80, 50)), seg=8))
        out.append(roof_gable(P, cx - r, cy - 0.35, cx + r, cy + 0.35, h - 0.3, h, P.m("roof", (90, 70, 66)), over=0.15, along="x"))
        out.append(lathe(cx, cy, [(0.0, 0.5), (0.08, 0.5), (0.08, 0.62), (0.0, 0.62)], P.m("bucket", (118, 80, 50)), seg=10))
        out.append(tube([(cx, cy, h - 0.45), (cx, cy, 0.62)], 0.006, P.m("rope", (160, 140, 100)), seg=5))
        return out
    if k == "trog":
        stone = P.m("stone", (200, 204, 212))
        hh = min(h, 0.6)
        return [box(cx, cy, w, min(d, 0.8), 0.0, hh, stone, bevel=0.012, outline=OL),
                box(cx, cy, w - 0.12, min(d, 0.8) - 0.12, hh - 0.05, hh - 0.04, P.g("water", (40, 50, 80), 0.6)),
                blob(cx + 0.2, cy, hh - 0.04, 0.06, 0.05, 0.02, (P.m("algae", (90, 140, 70)), P.m("algae", (90, 140, 70))), seed=2, seg=6, rings=3)]
    if k == "fass":
        from bm_spec import barrel
        return barrel(P.ctx, cx, cy, min(w, d) * 0.42, min(h, 1.0), prefix=P.nm + "_barrel")
    if k == "waschzuber":
        r = min(w, d) * 0.42
        out = [lathe(cx, cy, [(0.0, 0.0), (r * 0.9, 0.0), (r, 0.5), (r * 0.94, 0.5), (r * 0.84, 0.08), (0.0, 0.08)], P.m("tub", (150, 105, 62)), seg=22, outline=OL),
               cyl(cx, cy, r * 0.84, 0.42, 0.44, P.g("water", (80, 110, 140), 0.6), seg=20),
               cyl(cx + 0.1, cy, 0.12, 0.44, 0.45, P.m("stain", (140, 40, 50)), seg=12)]
        for z in (0.12, 0.4):
            out.append(lathe(cx, cy, [(r * 0.98, z), (r * 1.03, z), (r * 1.03, z + 0.03), (r * 0.98, z + 0.03)], P.m("band", (70, 70, 76)), seg=22))
        out.append(obox((P.x0 + 0.15, cy, 0.4), (0.3, 0.02, 0.7), P.m("board", (170, 120, 70)), roll=0.0, pitch=25.0, outline=OL))
        return out
    return None


@model("aktenkisten", "seifenkisten", "muellcontainer", "holzkorb", "bretter", "kohlen", "sargstapel", "sarg_stehend",
       "sarg_bock", "sarg_angelehnt", "barrikade", "treppensperre", "aschewagen", "billardtisch")
def m_containers(P):
    k = P.kind
    cx, cy, w, d, h = P.cx, P.cy, P.w, P.d, P.h
    if k == "aktenkisten":
        out = []
        for j, (dx, hh) in enumerate(((-0.3, 0.9), (0.3, 0.7))):
            out += M.crate_stack(P.ctx, f"{P.nm}_{j}", cx + dx * w * 0.6, cy, 0.5, hh * 0.5, n=2, rgb=(214, 196, 150), dark=(160, 140, 100), seed=j)
        out.append(box(P.x1 - 0.1, P.y0 + 0.1, 0.22, 0.3, 0.0, 0.01, P.m("paper", (236, 236, 230)), rot=10.0))
        return out
    if k == "seifenkisten":
        return M.crate_stack(P.ctx, P.nm, cx, cy, min(w, d) * 0.8, 0.4, n=2, rgb=(205, 165, 110), dark=(150, 110, 70), seed=P.seed)
    if k == "muellcontainer":
        blue = P.m("bin", (70, 100, 140))
        out = [box(cx, cy, w, d, 0.1, h * 0.75, blue, bevel=0.02, outline=OL),
               obox((cx, cy + d * 0.3, h * 0.75 + 0.15), (w + 0.04, d * 0.9, 0.04), P.m("lid", (56, 80, 112)), roll=-35.0, outline=OL),
               box(cx, P.y0 - 0.004, w - 0.2, 0.008, h * 0.4, h * 0.46, P.g("stripe", (240, 200, 60), 1.2))]
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            out.append(cyl(cx + sx * (w / 2 - 0.1), cy + sy * (d / 2 - 0.1), 0.05, 0.0, 0.1, P.m("wheel", (30, 30, 34)), seg=8))
        for j in range(3):
            out.append(blob(P.x0 + 0.25 + j * (w - 0.5) / 2, cy, h * 0.75, 0.16, 0.14, 0.14, (P.m("bag", (40, 40, 48)), P.m("bag_d", (30, 30, 36))), seed=j, seg=8, rings=4))
        return out
    if k == "holzkorb":
        out = [box(cx, cy, w, min(d, 0.6), 0.0, min(h, 0.6), P.m("basket", (190, 150, 90)), bevel=0.02, outline=OL)]
        for j in range(4):
            out.append(box(cx, cy, w - 0.02, min(d, 0.6) - 0.02, 0.1 + j * 0.12, 0.11 + j * 0.12, P.m("weave", (150, 110, 60))))
        for j in range(3):
            zl = min(h, 0.6) + 0.05
            out.append(lathe(P.x0 + 0.2 + j * (w - 0.4) / 2, cy, [(0.0, zl - 0.2), (0.07, zl - 0.2), (0.07, zl + 0.2), (0.0, zl + 0.2)], P.m("log", (120, 80, 50)), seg=10, outline=OL, tilt=(90.0, 0.0, zl)))
        return out
    if k == "bretter":
        out = []
        for j in range(5):
            out.append(box(cx + P.rnd.uniform(-0.05, 0.05), cy, w * 0.9, 0.2 + j * 0.0, 0.03 * j, 0.03 * j + 0.03, P.m(f"board{j % 2}", [(190, 140, 90), (170, 125, 80)][j % 2]), rot=P.rnd.uniform(-3, 3), outline=OL))
        out.append(obox((cx, cy + 0.06, 0.17), (0.4, 0.1, 0.012), P.m("saw", (190, 194, 200)), yaw=5.0))
        return out
    if k == "kohlen":
        out = [blob(cx, cy, 0.0, w * 0.45, d * 0.45, 0.3, (P.m("coal", (36, 34, 36)), P.m("coal_d", (24, 22, 24))), seed=P.seed, seg=16, rings=6, outline=OL)]
        for j in range(14):
            a, rr = P.rnd.uniform(0, 6.28), P.rnd.uniform(0.2, 0.95)
            out.append(blob(cx + w * 0.4 * rr * math.cos(a), cy + d * 0.4 * rr * math.sin(a), 0.3 * (1 - rr * rr) * 0.9, 0.05, 0.04, 0.04, (P.m("lump", (50, 48, 52)), P.m("coal_d", (24, 22, 24))), seed=j, seg=6, rings=3))
        out.append(tube([(cx + 0.2, cy + 0.1, 0.25), (cx + 0.5, cy + 0.35, 0.75)], 0.015, P.m("shaft", (150, 105, 62)), seg=6))
        out.append(obox((cx + 0.14, cy + 0.05, 0.22), (0.2, 0.24, 0.015), P.m("blade", (90, 94, 100)), yaw=35.0, pitch=50.0))
        out.append(lathe(P.x0 + 0.25, P.y0 + 0.15, [(0.0, 0.0), (0.1, 0.0), (0.11, 0.22), (0.0, 0.22)], P.m("bucket", (60, 62, 70)), seg=12, outline=OL))
        return out
    if k == "sargstapel":
        out = coffin(P, cx, cy, min(d, 2.2), min(w, 0.8), 0.0, 0.4, (150, 105, 62), yaw=0.0)
        out += coffin(P, cx - 0.05, cy + 0.05, min(d, 2.2), min(w, 0.8), 0.44, 0.4, (165, 118, 70), yaw=6.0)
        return out
    if k == "sarg_stehend":
        out = []
        for j, (dx, lean) in enumerate(((-0.25, -8.0), (0.25, 10.0))):
            L = min(h, 2.0)
            pg = sarcophagus_poly(0.0, 0.0, L, 0.6, 0.0)
            # stehend: Sechseck in (x, z) als Scheibe, leicht gekippt nach Norden (an der Wand)
            out.append(slab(affinity.translate(pg, cx + dx, L / 2 + 0.02), P.y0 + 0.25, 0.3, P.m(f"coffin{j}", (150, 105, 62)), outline=OL, rot=0.0))
            cr = P.m("cross", (201, 162, 76))
            out.append(box(cx + dx, P.y0 + 0.09, 0.03, 0.01, L * 0.3, L * 0.7, cr))
            out.append(box(cx + dx, P.y0 + 0.09, 0.2, 0.01, L * 0.55, L * 0.58, cr))
        return out
    if k == "sarg_bock":
        wood = P.m("trestle", (118, 80, 50))
        out = []
        for x in (P.x0 + 0.3, P.x1 - 0.5):
            for sy in (-1, 1):
                out.append(tube([(x, cy + sy * 0.3, 0.0), (x, cy, 0.5)], 0.02, wood, seg=6))
        out += coffin(P, cx - 0.1, cy, min(w, 2.4) * 0.85, min(d, 0.9), 0.5, 0.4, (236, 232, 220), yaw=90.0, lid=False, open_=True)
        out.append(obox((P.x1 - 0.12, cy, 0.5), (0.03, min(d, 0.9) * 0.9, min(w, 2.4) * 0.8), P.m("lid", (226, 222, 210)), pitch=70.0, outline=OL))
        return out
    if k == "sarg_angelehnt":
        L = min(h, 2.4)
        out = [obox((cx, P.y0 + 0.22, L / 2 + 0.05), (min(w, 0.7), 0.3, L), P.m("coffin", (150, 105, 62)), roll=-12.0, outline=OL),
               obox((cx, P.y0 + 0.05, L / 2 + 0.08), (min(w, 0.7) - 0.1, 0.02, L - 0.1), P.m("coffin_in", (60, 44, 34)), roll=-12.0)]
        for j in range(3):
            out.append(obox((cx, P.y0 + 0.06 + j * 0.0, 0.3 + j * (L - 0.6) / 2), (min(w, 0.7) - 0.1, 0.02, 0.03), P.m("coffin_d", (118, 80, 50)), roll=-12.0))
        return out
    if k == "barrikade":
        z0, z1 = P.zvis()
        z1 = max(z1, 1.8)
        out = [box(cx, P.base + 0.08, P.vx1 - P.vx0, 0.12, 0.0, z1, P.m("door", (60, 44, 70)), outline=OL)]
        wood = P.m("plank", (170, 125, 80))
        for j, (a, zc) in enumerate(((18.0, z1 * 0.3), (-22.0, z1 * 0.5), (12.0, z1 * 0.7))):
            out.append(obox((cx, P.base, zc), (P.vx1 - P.vx0 + 0.1, 0.03, 0.14), wood, pitch=a, outline=OL))
        out.append(obox((cx, P.base - 0.03, z1 * 0.55), (P.vx1 - P.vx0 + 0.3, 0.005, 0.03), P.m("tape", (240, 200, 60)), pitch=-5.0))
        return out
    if k == "treppensperre":
        out = M.crate_stack(P.ctx, P.nm + "_a", P.x0 + 0.5, cy, 0.6, 0.5, n=2, rgb=(190, 140, 90), dark=(130, 90, 55), seed=P.seed)
        out += M.crate_stack(P.ctx, P.nm + "_b", P.x1 - 0.5, cy, 0.7, 0.5, n=1, rgb=(190, 140, 90), dark=(130, 90, 55), seed=P.seed + 1)
        out.append(blob(cx, cy, 0.0, 0.45, 0.4, 1.1, (P.m("sheet", (230, 228, 220)), P.m("sheet_d", (190, 188, 180))), seed=P.seed, seg=12, rings=6, outline=OL))
        out.append(box(P.x1 - 0.7, cy - 0.1, 0.3, 0.3, 0.0, 0.5, P.m("pink", (190, 60, 90)), bevel=0.02, outline=OL))
        wood = P.m("plank", (170, 125, 80))
        out.append(obox((cx, P.y1 - 0.1, 1.5), (w + 0.2, 0.04, 0.14), wood, pitch=6.0, outline=OL))
        out.append(obox((cx, P.y1 - 0.14, 1.3), (w + 0.2, 0.04, 0.14), wood, pitch=-8.0, outline=OL))
        im = Image.new("RGB", (160, 64), (236, 236, 230))
        from PIL import ImageDraw, ImageFont
        try:
            f = ImageFont.truetype("arialbd.ttf", 34)
        except Exception:
            f = ImageFont.load_default()
        ImageDraw.Draw(im).text((80, 32), "CLOSED", fill=(30, 30, 30), font=f, anchor="mm")
        s = box(cx, P.y0 + 0.1, 0.5, 0.012, 0.75, 0.95, P.m("sign", (236, 236, 230)), outline=OL)
        s["front"] = P.tex("closed", im)
        out.append(s)
        out.append(obox((cx, P.y0 + 0.05, 0.6), (w * 0.9, 0.005, 0.03), P.m("tape", (240, 200, 60)), pitch=-12.0))
        return out
    if k == "aschewagen":
        steel = P.m("cart", (90, 94, 100))
        hb = 0.55
        out = [box(cx, cy, w, min(d, 0.8), 0.25, hb, steel, bevel=0.012, outline=OL),
               box(cx, cy, w - 0.08, min(d, 0.8) - 0.08, hb - 0.03, hb, P.m("ash", (120, 116, 110)))]
        for sx in (-1, 1):
            for yy in (cy - 0.25, cy + 0.25):
                out.append(wheel(P, cx + sx * (w / 2 - 0.08), yy, 0.14, 0.14, 0.05, P.m("wheel", (40, 40, 44)), axis="x"))
        for j, c in enumerate(((200, 150, 80), (90, 120, 160), (190, 120, 90))):
            x = P.x0 + 0.25 + (w - 0.5) * j / 2
            out.append(lathe(x, cy, [(0.0, hb), (0.08, hb), (0.05, hb + 0.05), (0.11, hb + 0.2), (0.06, hb + 0.3), (0.0, hb + 0.3)], P.m(f"urn{j}", c), seg=10, outline=OL))
        out.append(tube([(P.x1, cy, 0.5), (P.x1 + 0.4, cy, 0.7)], 0.015, steel, seg=6))
        return out
    if k == "billardtisch":
        return M.pool_table(P.ctx, P.nm, P.x0, P.y0, P.x1, P.y1, h=0.8, felt=(40, 110, 60), wood=(110, 72, 46), seed=P.seed)
    return None


@model("standuhr", "engelsstatue_tuch", "engel", "baer", "ruestung", "buesten_saeule", "standspiegel", "schneiderpuppe",
       "perueckenkoepfe", "leiter", "schuerhaken", "freitreppe", "grabstein", "glockenturm", "rabenbaum")
def m_figures(P):
    k = P.kind
    cx, cy, w, d, h = P.cx, P.cy, P.w, P.d, P.h
    if k == "standuhr":
        wood = P.m("wood", (118, 80, 50))
        dd = min(d, 0.45)
        out = cabinet(P, P.x0, P.y0, P.x1, P.y0 + dd, 0.0, h, (118, 80, 50))
        out.append(box(cx, P.y0 + 0.012, w - 0.1, 0.012, 0.15, h * 0.6, P.g("glass", (60, 50, 50), 0.4)))
        out.append(disc_s(P, cx, P.y0 + 0.012, h * 0.73 + w * 0.1, w * 0.32, 0.015, P.m("dial", (236, 232, 220)), seg=20, outline=OL))
        zd = h * 0.73 + w * 0.1
        out.append(box(cx, P.y0 - 0.006, 0.012, 0.004, zd, zd + w * 0.26, P.m("hand", (30, 30, 30))))
        out.append(box(cx + w * 0.08, P.y0 - 0.006, w * 0.18, 0.004, zd - 0.005, zd + 0.005, P.m("hand", (30, 30, 30))))
        out.append(tube([(cx, P.y0 + 0.08, h * 0.6), (cx + 0.04, P.y0 + 0.08, 0.3)], 0.006, P.m("rod", BRASS), seg=5))
        out.append(lathe(cx + 0.04, P.y0 + 0.08, [(0.0, 0.22), (0.05, 0.27), (0.0, 0.32)], P.m("bob", BRASS), seg=10))
        out.append(box(cx, P.y0 + dd / 2, w + 0.06, dd + 0.06, h - 0.06, h, wood, bevel=0.015, outline=OL))
        out.append(lathe(cx, P.y0 + dd / 2, [(0.0, h), (0.08, h), (0.0, h + 0.16)], wood, seg=10))
        return out
    if k in ("engelsstatue_tuch", "engel"):
        stone = P.m("stone", (220, 220, 226))
        hb = h * 0.3
        out = [box(cx, cy, w * 0.9, min(d, 0.8), 0.0, hb, stone, bevel=0.015, outline=OL)]
        if k == "engelsstatue_tuch":
            hs = h - hb
            out.append(lathe(cx, cy, [(0.0, hb), (w * 0.38, hb), (w * 0.34, hb + hs * 0.35), (w * 0.26, hb + hs * 0.6), (w * 0.22, hb + hs * 0.75), (w * 0.14, hb + hs * 0.9), (0.0, hb + hs)],
                             P.m("sheet", (236, 232, 222)), seg=16, outline=OL))
            out.append(obox((cx + w * 0.3, cy, hb + hs * 0.55), (0.03, 0.3, hs * 0.45), P.m("sheet_d", (190, 186, 176)), yaw=20.0, pitch=15.0))
            return out
        out.append(lathe(cx, cy, [(0.0, hb), (w * 0.22, hb), (w * 0.2, hb + (h - hb) * 0.75), (w * 0.08, hb + (h - hb) * 0.8), (0.0, hb + (h - hb) * 0.82)], stone, seg=14, outline=OL))
        out.append(lathe(cx, cy, [(0.0, hb + (h - hb) * 0.8), (0.07, hb + (h - hb) * 0.82), (0.08, hb + (h - hb) * 0.93), (0.0, hb + (h - hb) * 1.0)], stone, seg=12))
        for sx in (-1, 1):
            out.append(obox((cx + sx * w * 0.3, cy + 0.1, hb + (h - hb) * 0.65), (w * 0.3, 0.06, (h - hb) * 0.6), stone, yaw=sx * 10.0, pitch=sx * 18.0, outline=OL))
        out.append(blob(cx + 0.1, P.y0 + 0.1, hb, 0.08, 0.06, 0.06, (P.m("wreath", (70, 110, 60)), P.m("wreath", (70, 110, 60))), seed=1, seg=6, rings=3))
        return out
    if k == "baer":
        fur = (P.m("fur", (120, 80, 50)), P.m("fur_d", (90, 60, 36)))
        hb = 0.2
        out = [box(cx, cy, w * 0.9, min(d, 0.8), 0.0, hb, P.m("plinth", (150, 105, 62)), bevel=0.01, outline=OL),
               blob(cx, cy, hb, w * 0.33, min(d, 0.8) * 0.33, h * 0.68, fur, seed=P.seed, seg=12, rings=8, outline=OL),
               blob(cx, cy - 0.05, hb + h * 0.68, w * 0.2, 0.18, h * 0.22, fur, seed=P.seed + 1, seg=10, rings=6, outline=OL),
               blob(cx, cy - 0.2, hb + h * 0.72, 0.07, 0.08, 0.06, (P.m("snout", (200, 160, 120)), P.m("snout", (200, 160, 120))), seed=2, seg=6, rings=3)]
        for sx in (-1, 1):
            out.append(obox((cx + sx * w * 0.42, cy, hb + h * 0.72), (0.14, 0.14, h * 0.45), P.m("fur", (120, 80, 50)), yaw=0.0, pitch=sx * -25.0, outline=OL))
            out.append(blob(cx + sx * w * 0.14, cy - 0.06, hb + h * 0.88, 0.05, 0.04, 0.05, fur, seed=3, seg=6, rings=3))
        return out
    if k == "ruestung":
        steel = (P.m("armor", (170, 176, 184)), P.m("armor_d", (120, 126, 134)))
        hb = 0.12
        out = [box(cx, cy, w * 0.7, min(d, 0.6), 0.0, hb, P.m("plinth", (40, 40, 46)), outline=OL)]
        zs = hb
        for name, (rx, ry, hh) in (("legs", (0.14, 0.12, 0.85)), ("torso", (0.22, 0.16, 0.6)), ("head", (0.11, 0.11, 0.3))):
            out.append(blob(cx, cy, zs, rx, ry, hh, steel, seed=P.seed, seg=10, rings=6, outline=OL))
            zs += hh
        for sx in (-1, 1):
            out.append(obox((cx + sx * 0.3, cy, hb + 1.2), (0.1, 0.1, 0.6), P.m("armor", (170, 176, 184)), outline=OL))
        out.append(box(cx, cy - 0.11, 0.1, 0.01, hb + 1.5, hb + 1.56, P.m("visor", (30, 30, 34))))
        out.append(tube([(cx + 0.42, cy, 0.0), (cx + 0.42, cy, h + 0.1)], 0.015, P.m("shaft", (118, 80, 50)), seg=6))
        out.append(obox((cx + 0.42, cy, h), (0.3, 0.02, 0.35), P.m("blade", (190, 194, 200)), outline=OL))
        return out
    if k == "buesten_saeule":
        stone = P.m("stone", (200, 204, 210))
        hc = h * 0.6
        out = [cyl(cx, cy, w * 0.4, 0.0, 0.08, P.m("foot", (30, 30, 34)), seg=16, outline=OL),
               lathe(cx, cy, [(0.0, 0.08), (w * 0.3, 0.08), (w * 0.26, 0.2), (w * 0.26, hc - 0.1), (w * 0.32, hc), (0.0, hc)], stone, seg=18, outline=OL),
               blob(cx, cy, hc, w * 0.25, 0.14, (h - hc) * 0.55, (stone, P.m("stone_d", (150, 154, 160))), seed=P.seed, seg=10, rings=5),
               lathe(cx, cy, [(0.0, hc + (h - hc) * 0.5), (0.08, hc + (h - hc) * 0.55), (0.09, hc + (h - hc) * 0.85), (0.0, hc + (h - hc) * 1.0)], stone, seg=12),
               box(cx, cy, 0.2, 0.2, hc + (h - hc) * 0.92, hc + (h - hc) * 0.96, stone)]
        return out
    if k == "standspiegel":
        wood = P.m("wood", (118, 80, 50))
        out = []
        for sx in (-1, 1):
            out.append(cyl(cx + sx * w * 0.42, cy, 0.02, 0.0, h * 0.7, wood, seg=8))
            out.append(tube([(cx + sx * w * 0.42, cy - 0.2, 0.0), (cx + sx * w * 0.42, cy + 0.2, 0.0)], 0.02, wood, seg=6))
        ell = affinity.scale(sbox(0, 0, 1, 1).centroid.buffer(1.0, 32), w * 0.4, h * 0.42)
        ell = affinity.translate(ell, cx, h * 0.52)
        out.append(slab(ell, cy, 0.04, wood, outline=OL))
        out.append(slab(affinity.scale(ell, 0.9, 0.92), cy - 0.025, 0.012, P.m("mirror", (170, 205, 225))))
        return out
    if k == "schneiderpuppe":
        out = tripod(P, cx, cy, 0.9, spread=0.28, r=0.014, mat=P.m("wood", (118, 80, 50)))
        out.append(cyl(cx, cy, 0.02, 0.9, 1.1, P.m("wood", (118, 80, 50)), seg=8))
        out.append(blob(cx, cy, 1.1, 0.2, 0.14, 0.6, (P.m("cloth", (236, 232, 222)), P.m("cloth_d", (140, 50, 70))), seed=P.seed, seg=12, rings=8, outline=OL))
        return out
    if k == "perueckenkoepfe":
        out = cabinet(P, P.x0, P.y0, P.x1, P.y0 + min(d, 0.45), 0.0, h * 0.4, (118, 80, 50))
        out += shelves(P, P.x0 + 0.03, P.y0 + 0.03, P.x1 - 0.03, P.y0 + min(d, 0.45) - 0.03, h * 0.4, h, 2, P.m("board", (128, 86, 54)), items=False)
        for j, c in enumerate(((230, 200, 80), (190, 60, 60))):
            z = h * 0.4 + (h * 0.6) * (j + 0.2) / 2
            out.append(lathe(cx, P.y0 + 0.2, [(0.0, z), (0.05, z), (0.04, z + 0.06), (0.09, z + 0.14), (0.08, z + 0.24), (0.0, z + 0.28)], P.m("head", (226, 206, 180)), seg=12, outline=OL))
            out.append(blob(cx, P.y0 + 0.2, z + 0.18, 0.1, 0.1, 0.12, (P.m(f"wig{j}", c), P.m(f"wig{j}_d", _sh(c, 0.7))), seed=j, seg=8, rings=4))
        return out
    if k == "leiter":
        return ladder(P, cx, P.base + 0.35, P.base + 0.35, 0.0, h, P.m("rung", (150, 105, 62)), w=min(w, 0.5), lean=0.4)
    if k == "schuerhaken":
        iron = P.m("iron", (50, 48, 54))
        out = [cyl(cx, cy, 0.14, 0.0, 0.03, iron, seg=12, outline=OL), cyl(cx, cy, 0.1, 0.03, 0.05, iron, seg=12)]
        for j in range(3):
            a = math.radians(120 * j)
            x, y = cx + 0.06 * math.cos(a), cy + 0.06 * math.sin(a)
            out.append(cyl(x, y, 0.008, 0.05, h - 0.05, iron, seg=6))
            out.append(lathe(x, y, [(0.0, h - 0.06), (0.018, h - 0.05), (0.018, h - 0.02), (0.0, h)], P.m("knob", BRASS), seg=6))
        out.append(cyl(cx, cy, 0.02, 0.05, 0.9, iron, seg=8))
        out.append(lathe(cx, cy, [(0.08, 0.86), (0.1, 0.86), (0.1, 0.89), (0.08, 0.89)], iron, seg=10))
        return out
    if k == "freitreppe":
        red, wood = P.m("carpet", (130, 30, 50)), P.m("rail", (118, 80, 50))
        n = 7
        out = []
        for j in range(n):
            z1 = h * (j + 1) / n
            yy = P.y0 + d * (j + 0.5) / n
            out.append(box(cx, yy, w, d / n, 0.0, z1, P.m("step", (200, 200, 206)), outline=OL))
            out.append(box(cx, yy, w * 0.6, d / n, z1, z1 + 0.006, red))
        for sx in (-1, 1):
            x = cx + sx * (w / 2 - 0.06)
            out.append(tube([(x, P.y0, 0.9), (x, P.y1, h + 0.9)], 0.03, wood, seg=8))
            for j in range(0, n + 1, 2):
                z = h * j / n
                yy = P.y0 + d * j / n
                out.append(cyl(x, yy, 0.02, z, z + 0.9, wood, seg=6))
        return out
    if k == "grabstein":
        stone = (P.m("stone", (150, 170, 150)), P.m("stone_d", (110, 126, 110)), None)
        out = []
        for j, (dx, dy, hh, lean) in enumerate(((-0.7, 0.05, 0.9, -10.0), (-0.15, 0.1, 1.1, 5.0), (0.35, 0.0, 0.8, 15.0), (0.7, -0.1, 0.4, 40.0))):
            x, y = cx + dx * w * 0.38, cy + dy
            out.append(obox((x, y, hh / 2 * math.cos(math.radians(lean))), (0.4, 0.12, hh), P.m("stone", (150, 170, 150)), yaw=P.rnd.uniform(-10, 10), roll=lean, outline=OL))
            out.append(lathe(x, y + 0.0, [(0.0, 0.0), (0.2, 0.0), (0.0, 0.12)], P.m("stone", (150, 170, 150)), seg=10, tilt=(lean, 0.0, hh * math.cos(math.radians(lean)))))
        out.append(cyl(P.x0 + 0.1, P.y0 + 0.1, 0.02, 0.0, 0.5, P.m("post", (50, 48, 54)), seg=6))
        out.append(box(P.x0 + 0.1, P.y0 + 0.1, 0.1, 0.1, 0.5, 0.66, P.g("lantern", (255, 110, 70), 2.6), bevel=0.01))
        out.append(blob(cx + 0.2, P.y0 + 0.15, 0.0, 0.1, 0.07, 0.05, (P.m("grass", (90, 130, 70)), P.m("grass", (90, 130, 70))), seed=2, seg=6, rings=3))
        return out
    if k == "glockenturm":
        stone = P.m("stone", (170, 174, 184))
        dd = min(d, w)
        hb = h * 0.62
        out = [box(cx, cy, w, dd, 0.0, hb, stone, outline=OL),
               box(cx, cy, w * 0.9, dd * 0.9, hb, h * 0.8, P.m("belfry", (60, 56, 64)), outline=OL)]
        for sx in (-1, 1):
            out.append(box(cx + sx * w * 0.45, cy, w * 0.08, dd * 0.92, hb, h * 0.8, stone))
        out.append(box(cx, cy, w * 0.92, dd * 0.08, hb, h * 0.8, stone))
        out.append(lathe(cx, cy, [(0.0, hb + 0.1), (0.1, hb + 0.12), (0.2, hb + 0.35), (0.24, hb + 0.4), (0.0, hb + 0.4)], P.m("bell", BRASS), seg=16, outline=OL))
        out.append(box(cx, cy, w + 0.15, dd + 0.15, h * 0.8, h * 0.84, stone, bevel=0.02, outline=OL))
        # Spitzdach als Pyramide
        out.append(tooth((cx, cy, h * 0.84), min(w, dd) + 0.1, h * 0.16, P.m("roof", (70, 72, 84))))
        out.append(box(cx, P.y0 + 0.012, w * 0.3, 0.024, 0.0, hb * 0.35, P.m("door", (118, 80, 50)), outline=OL))
        out.append(prism(affinity.scale(sbox(cx - 0.3, P.y0 - 0.1, cx + 0.3, P.y0 + 0.1).centroid.buffer(1.0, 12), 0.3, 0.1), 0.0, 0.3 * hb * 0.35 / 0.3 * 0 + 0.002, stone))
        for sx in (-1, 1):
            out.append(box(cx + sx * w * 0.3, P.y0 + 0.005, 0.1, 0.01, hb * 0.5, hb * 0.65, P.m("window", (40, 40, 50))))
        out.append(cyl(cx, cy, 0.01, h, h + 0.4, P.m("spire", (50, 48, 54)), seg=6))
        return out
    if k == "rabenbaum":
        bark = P.m("bark", (120, 110, 100))
        x, y = cx, P.base + 0.3
        out = [lathe(x, y, [(0.0, 0.0), (0.28, 0.0), (0.18, 0.5), (0.14, h * 0.5), (0.0, h * 0.55)], bark, seg=12, outline=OL)]
        rnd = random.Random(P.seed)
        def branch(p0, ang, length, r, depth):
            if depth == 0 or length < 0.3:
                return
            a = math.radians(ang)
            p1 = (p0[0] + length * math.cos(a) * 0.8, p0[1] + rnd.uniform(-0.2, 0.2) * length, p0[2] + length * math.sin(a))
            out.append(tube([p0, p1], r, bark, seg=6))
            for da in (rnd.uniform(15, 45), -rnd.uniform(15, 45)):
                branch(p1, ang + da, length * 0.65, r * 0.6, depth - 1)
        for ang in (60, 95, 125, 150, 30):
            branch((x, y, h * 0.45), ang, h * 0.3, 0.05, 4)
        for j in range(3):
            bx, by, bz = x + rnd.uniform(-1.5, 1.5), y + rnd.uniform(-0.3, 0.3), h * rnd.uniform(0.6, 0.9)
            out.append(blob(bx, by, bz, 0.08, 0.05, 0.06, (P.m("raven", (28, 26, 32)), P.m("raven", (28, 26, 32))), seed=j, seg=6, rings=3))
        out.append(box(x + 0.05, y - 0.15, 0.08, 0.08, h * 0.3, h * 0.3 + 0.1, P.g("lantern", (255, 200, 110), 2.4)))
        return out
    return None


@model("portrait", "leerer_rahmen", "pinnwand", "sternkarte_datum", "wandteppich", "seance_wand", "hirschkopf", "geweihe",
       "lueftungsgitter", "klingelbrett", "handabdruck_russ", "rohre", "fleischerhaken", "waescheleine", "fledermaeuse")
def m_walls(P):
    k = P.kind
    z0, z1 = P.zvis()
    y = P.base + 0.02
    cx = (P.vx0 + P.vx1) / 2
    if k == "portrait":
        return pic(P, (90, 60, 36), depth=0.05, border=0.06, gold=True)
    if k == "leerer_rahmen":
        out = pic(P, (120, 80, 40), depth=0.05, border=0.06, img=False, gold=True)
        out.append(box(cx, y - 0.004, P.vx1 - P.vx0 - 0.12, 0.012, z0 + 0.06, z1 - 0.06, P.m("canvas", (150, 40, 60))))
        return out
    if k == "pinnwand":
        out = pic(P, (118, 80, 50), depth=0.04, border=0.05, bg=(200, 170, 120))
        return out
    if k == "sternkarte_datum":
        out = pic(P, (60, 44, 34), depth=0.04, border=0.05, bg=(30, 34, 60))
        return out
    if k == "wandteppich":
        out = [tube([(P.vx0, y + 0.02, z1), (P.vx1, y + 0.02, z1)], 0.02, P.m("rod", (118, 80, 50)), seg=8)]
        out.append(panel_south(P, P.vx0 + 0.05, P.vx1 - 0.05, y, z0, z1 - 0.03, P.vx0 + 0.05, P.base + z0 * K, P.vx1 - 0.05, P.base + (z1 - 0.03) * K, suf="tap", depth=0.02, mat=P.m("tap_side", (120, 30, 50)), bg=(120, 30, 50)))
        return out
    if k == "seance_wand":
        out = []
        for sx in (-1, 1):
            xx = cx + sx * (P.vx1 - P.vx0) * 0.38
            out.append(box(xx, y + 0.06, 0.5, 0.1, z0 + 0.1, z1 - 0.1, P.m("curtain", (110, 30, 50)), bevel=0.02, outline=OL))
            out.append(cyl(xx, y + 0.06, 0.03, z0 + 0.1, z1 - 0.1, P.m("curtain_d", (80, 20, 36)), seg=8))
            out += candle(P, cx + sx * (P.vx1 - P.vx0) * 0.2, y + 0.05, (z0 + z1) / 2 + 0.05, 0.1, 0.012)
            out.append(box(cx + sx * (P.vx1 - P.vx0) * 0.2, y + 0.04, 0.12, 0.06, (z0 + z1) / 2, (z0 + z1) / 2 + 0.05, P.m("sconce", BRASS)))
        out.append(box(cx, y + 0.02, (P.vx1 - P.vx0) * 0.3, 0.03, (z0 + z1) / 2 - 0.2, (z0 + z1) / 2 + 0.2, P.m("plaque", (226, 206, 160)), bevel=0.005, outline=OL))
        for j in range(5):
            out.append(box(cx, y + 0.003, (P.vx1 - P.vx0) * 0.22, 0.004, (z0 + z1) / 2 - 0.14 + j * 0.06, (z0 + z1) / 2 - 0.12 + j * 0.06, P.m("text", (90, 70, 50))))
        return out
    if k == "hirschkopf":
        fur = P.m("fur", (150, 105, 62))
        zc = (z0 + z1) / 2
        out = [box(cx, y + 0.02, 0.3, 0.04, zc - 0.25, zc + 0.15, P.m("plaque", (118, 80, 50)), bevel=0.01, outline=OL),
               blob(cx, y - 0.15, zc - 0.1, 0.1, 0.18, 0.14, (fur, P.m("fur_d", (110, 72, 46))), seed=P.seed, seg=8, rings=5),
               blob(cx, y - 0.3, zc - 0.14, 0.06, 0.1, 0.06, (fur, P.m("fur_d", (110, 72, 46))), seed=1, seg=6, rings=3)]
        ant = P.m("antler", (226, 214, 186))
        for sx in (-1, 1):
            out.append(tube([(cx + sx * 0.06, y - 0.12, zc + 0.02), (cx + sx * 0.2, y - 0.1, zc + 0.25), (cx + sx * 0.28, y - 0.08, zc + 0.4)], 0.014, ant, seg=6))
            out.append(tube([(cx + sx * 0.16, y - 0.1, zc + 0.18), (cx + sx * 0.08, y - 0.12, zc + 0.32)], 0.01, ant, seg=5))
        return out
    if k == "geweihe":
        ant = P.m("antler", (226, 214, 186))
        out = []
        for j in range(3):
            xx = P.vx0 + (P.vx1 - P.vx0) * (j + 0.5) / 3
            zc = (z0 + z1) / 2
            out.append(box(xx, y + 0.02, 0.22, 0.04, zc - 0.15, zc + 0.08, P.m("plaque", (118, 80, 50)), bevel=0.01, outline=OL))
            for sx in (-1, 1):
                out.append(tube([(xx + sx * 0.04, y - 0.02, zc + 0.05), (xx + sx * 0.16, y - 0.04, zc + 0.3), (xx + sx * 0.22, y - 0.03, zc + 0.42)], 0.012, ant, seg=6))
                out.append(tube([(xx + sx * 0.12, y - 0.04, zc + 0.22), (xx + sx * 0.06, y - 0.05, zc + 0.36)], 0.009, ant, seg=5))
        return out
    if k == "lueftungsgitter":
        zc = max(z0, 0.3)
        out = M.vent_grate(P.ctx, P.nm, cx - 0.2, 0.0, cx + 0.2, 0.3, z=0.0, rgb=(60, 60, 66), slots=5)
        # vent_grate liegt flach; hier senkrecht an die Wand: eigener Kasten mit Schlitzen
        out = [box(cx, y + 0.02, 0.4, 0.04, zc, zc + 0.32, P.m("grille", (60, 60, 66)), bevel=0.005, outline=OL)]
        for j in range(5):
            out.append(box(cx, y - 0.002, 0.32, 0.006, zc + 0.04 + j * 0.055, zc + 0.06 + j * 0.055, P.m("slot", (26, 26, 30))))
        out.append(blob(cx, y - 0.05, zc + 0.5, 0.05, 0.04, 0.1, (P.m("smoke", (190, 190, 200)), P.m("smoke", (190, 190, 200))), seed=1, seg=6, rings=3))
        return out
    if k == "klingelbrett":
        zc = (z0 + z1) / 2
        out = [box(cx, y + 0.03, 0.3, 0.06, zc - 0.22, zc + 0.22, P.m("board", (118, 80, 50)), bevel=0.008, outline=OL),
               box(cx, y - 0.002, 0.22, 0.004, zc - 0.16, zc + 0.16, P.m("paper", (236, 232, 220)))]
        for j in range(4):
            out.append(box(cx - 0.06, y - 0.01, 0.08, 0.02, zc - 0.12 + j * 0.07, zc - 0.1 + j * 0.07, P.m("bell", BRASS)))
            out.append(cyl(cx + 0.07, y - 0.012, 0.012, zc - 0.11 + j * 0.07, zc - 0.09 + j * 0.07, P.m("btn", (40, 40, 44)), seg=6))
        return out
    if k == "handabdruck_russ":
        zc = (z0 + z1) / 2
        out = [blob(cx, y - 0.004, zc, 0.05, 0.004, 0.07, (P.m("soot", (40, 36, 36)), P.m("soot", (40, 36, 36))), seed=1, seg=6, rings=3)]
        for j in range(4):
            out.append(box(cx - 0.04 + j * 0.027, y - 0.004, 0.012, 0.004, zc - 0.35, zc, P.m("soot", (40, 36, 36))))
        return out
    if k == "rohre":
        pipe = P.m("pipe", (120, 126, 134))
        zc = max(z1 - 0.25, 1.3)
        out = [tube([(P.vx0, y + 0.1, zc), (P.vx1, y + 0.1, zc)], 0.05, pipe, seg=10), tube([(P.vx0, y + 0.1, zc - 0.16), (P.vx1, y + 0.1, zc - 0.16)], 0.035, pipe, seg=8)]
        for j in range(4):
            xx = P.vx0 + (P.vx1 - P.vx0) * (j + 0.5) / 4
            out.append(lathe(xx, y + 0.1, [(0.055, zc - 0.03), (0.07, zc - 0.03), (0.07, zc + 0.03), (0.055, zc + 0.03)], P.m("flange", (90, 94, 100)), seg=10, tilt=(90.0, 0.0, zc)))
        out.append(lathe(cx, y + 0.1, [(0.0, zc + 0.04), (0.05, zc + 0.04), (0.05, zc + 0.14), (0.0, zc + 0.14)], P.m("valve", (190, 40, 40)), seg=8))
        out.append(blob(cx + 0.4, y + 0.1, zc + 0.15, 0.04, 0.04, 0.08, (P.m("steam", (200, 200, 210)), P.m("steam", (200, 200, 210))), seed=1, seg=6, rings=3))
        return out
    if k == "fleischerhaken":
        chain, hook = P.m("chain", (120, 122, 128)), P.m("hook", (150, 152, 158))
        zt = 1.73
        out = []
        for j in range(3):
            xx = P.vx0 + 0.2 + (P.vx1 - P.vx0 - 0.4) * j / 2
            zb = zt - 0.45 - (j % 2) * 0.15
            out.append(tube([(xx, y + 0.25, zt), (xx, y + 0.25, zb)], 0.006, chain, seg=4))
            out.append(tube([(xx, y + 0.25, zb), (xx + 0.03, y + 0.25, zb - 0.08), (xx + 0.07, y + 0.25, zb - 0.04)], 0.008, hook, seg=5))
        out.append(lathe(cx, y + 0.25, [(0.0, zt - 0.95), (0.09, zt - 0.95), (0.11, zt - 0.65), (0.0, zt - 0.65)], P.m("bucket", (170, 174, 180)), seg=12, outline=OL))
        out.append(cyl(cx, y + 0.25, 0.05, 0.0, 0.004, P.m("blood", (130, 20, 24)), seg=10))
        return out
    if k == "waescheleine":
        post = P.m("post", (118, 80, 50))
        zl = min(z1, 1.6)
        out = [cyl(P.vx0 + 0.05, P.base + 0.25, 0.025, 0.0, zl + 0.05, post, seg=8), cyl(P.vx1 - 0.05, P.base + 0.25, 0.025, 0.0, zl + 0.05, post, seg=8),
               tube([(P.vx0 + 0.05, P.base + 0.25, zl), (P.vx1 - 0.05, P.base + 0.25, zl)], 0.006, P.m("line", (220, 220, 210)), seg=4)]
        for j in range(3):
            xx = P.vx0 + 0.4 + (P.vx1 - P.vx0 - 0.8) * j / 2
            s = box(xx, P.base + 0.25, 0.55, 0.012, zl - 0.75, zl, P.m("sheet", (236, 234, 224)), outline=OL)
            out.append(s)
            if j == 1:
                out.append(blob(xx, P.base + 0.24, zl - 0.45, 0.05, 0.004, 0.07, (P.m("blood", (150, 30, 40)), P.m("blood", (150, 30, 40))), seed=2, seg=6, rings=3))
        return out
    if k == "fledermaeuse":
        bat = (P.m("bat", (30, 26, 36)), P.m("bat", (30, 26, 36)))
        zt = 1.7
        out = []
        for j in range(3):
            xx = P.vx0 + 0.3 + (P.vx1 - P.vx0 - 0.6) * j / 2
            out.append(blob(xx, P.base + 0.3, zt - 0.3, 0.05, 0.04, 0.16, bat, seed=j, seg=6, rings=4))
            out.append(cyl(xx, P.base + 0.3, 0.01, zt - 0.14, zt, P.m("bat", (30, 26, 36)), seg=4))
            out.append(cyl(xx - 0.015, P.base + 0.26, 0.006, zt - 0.3 + 0.12, zt - 0.3 + 0.125, P.g("eye", (230, 60, 60), 2.0), seg=4))
        out.append(obox((cx, P.base + 0.3, zt - 0.6), (0.4, 0.04, 0.12), P.m("bat", (30, 26, 36)), pitch=10.0))
        return out
    return None


@model("tonband_boden", "kinderschuh", "rauchendes_buch", "buecherstapel", "kronleuchter_boden", "schreibmaschine")
def m_floor(P):
    k = P.kind
    cx, cy = (P.vx0 + P.vx1) / 2, P.base + 0.15
    if k == "tonband_boden":
        out = [cyl(cx - 0.3, cy, 0.14, 0.0, 0.02, P.m("reel", (200, 190, 150)), seg=20, outline=OL), cyl(cx - 0.3, cy, 0.04, 0.02, 0.03, P.m("hub", (60, 60, 64)), seg=10)]
        pts = [(cx - 0.15 + j * 0.08, cy + (0.06 if j % 2 else -0.06), 0.004) for j in range(8)]
        out.append(tube(pts, 0.004, P.m("tape", (90, 60, 40)), seg=4))
        return out
    if k == "kinderschuh":
        return [obox((cx, cy, 0.04), (0.2, 0.1, 0.07), P.m("shoe", (90, 50, 36)), yaw=25.0, outline=OL),
                obox((cx + 0.03, cy + 0.02, 0.085), (0.1, 0.06, 0.02), P.m("sole", (226, 220, 200)), yaw=25.0)]
    if k == "rauchendes_buch":
        out = [obox((cx - 0.14, cy, 0.012), (0.26, 0.34, 0.025), P.m("page", (236, 230, 210)), pitch=6.0, outline=OL),
               obox((cx + 0.14, cy, 0.012), (0.26, 0.34, 0.025), P.m("page", (236, 230, 210)), pitch=-6.0, outline=OL),
               cyl(cx + 0.1, cy + 0.05, 0.04, 0.025, 0.028, P.m("burn", (60, 40, 30)), seg=10)]
        for j in range(3):
            out.append(blob(cx + 0.1 + j * 0.03, cy + 0.05, 0.12 + j * 0.18, 0.04, 0.04, 0.09, (P.m("smoke", (200, 200, 210)), P.m("smoke", (200, 200, 210))), seed=j, seg=6, rings=3))
        return out
    if k == "buecherstapel":
        out = []
        z = 0.0
        for j in range(6):
            c = [(170, 60, 60), (60, 90, 150), (80, 130, 90), (200, 170, 80), (236, 232, 220), (120, 80, 120)][j]
            out.append(box(cx + P.rnd.uniform(-0.02, 0.02), cy + P.rnd.uniform(-0.02, 0.02), 0.26, 0.2, z, z + 0.035, P.m(f"bk{j}", c), rot=P.rnd.uniform(-15, 15), outline=OL))
            z += 0.035
        out.append(obox((cx + 0.3, cy + 0.6, 0.012), (0.22, 0.28, 0.025), P.m("page", (236, 230, 210)), yaw=10.0))
        return out
    if k == "kronleuchter_boden":
        br = P.m("brass", BRASS)
        r = min(P.w, P.d) * 0.42
        out = [lathe(cx, cy, [(r - 0.02, 0.03), (r, 0.03), (r, 0.06), (r - 0.02, 0.06)], br, seg=32, outline=OL),
               cyl(cx, cy, 0.08, 0.0, 0.1, br, seg=12)]
        for j in range(8):
            a = math.radians(j * 45)
            out.append(tube([(cx, cy, 0.09), (cx + r * math.cos(a), cy + r * math.sin(a), 0.05)], 0.012, br, seg=6))
            out += candle(P, cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a), 0.06, 0.08, 0.012, lit=False)
        out.append(tube([(cx, cy, 0.1), (cx + 0.2, cy + 0.1, 0.5)], 0.01, br, seg=6))
        for j in range(5):
            out.append(blob(cx + P.rnd.uniform(-r, r), cy + P.rnd.uniform(-r, r), 0.0, 0.015, 0.015, 0.01, (P.m("shard", (220, 230, 240)), P.m("shard", (220, 230, 240))), seed=j, seg=5, rings=2))
        return out
    if k == "schreibmaschine":
        out = M.table(P.ctx, P.nm, P.x0 + 0.2, P.y0, P.x1 - 0.2, P.y0 + min(P.d, 0.5), h=0.7, top_rgb=WOOD, leg_rgb=WOOD_D)
        out += it_typewriter(P, 0.7, dx=0.0, dy=min(P.d, 0.5) / 2 - P.d / 2)
        return out
    return None


# ---- Kartenvarianten oeffentlicher Arten


def _v_villa_kessel(P):
    cx, cy, w, d, h = P.cx, P.cy, P.w, P.d, P.h
    # Hexenkessel auf Feuerstelle
    out = [cyl(cx, cy, w * 0.42, 0.0, 0.1, P.m("hearth", (70, 66, 64)), seg=20, outline=OL),
           lathe(cx, cy, [(0.0, 0.12), (w * 0.3, 0.12), (w * 0.4, 0.5), (w * 0.36, 0.75), (w * 0.4, 0.8), (0.0, 0.8)], P.m("pot", (70, 74, 82)), seg=24, outline=OL),
           cyl(cx, cy, w * 0.34, 0.78, 0.8, P.g("brew", (110, 200, 110), 1.6), seg=20),
           lathe(cx, cy, [(0.0, 0.0), (w * 0.2, 0.04), (w * 0.12, 0.2), (0.0, 0.3)], P.g("fire", (255, 160, 50), 2.4), seg=10)]
    for j in range(3):
        out.append(blob(cx + P.rnd.uniform(-0.1, 0.1), cy + P.rnd.uniform(-0.1, 0.1), 0.95 + j * 0.25, 0.1, 0.1, 0.12, (P.m("steam", (200, 200, 210)), P.m("steam", (200, 200, 210))), seed=j, seg=8, rings=4))
    return out


def _v_villa_monitorwand(P):
    cx, cy, w, d, h = P.cx, P.cy, P.w, P.d, P.h
    hs = 0.35
    out = [box(cx, cy, w, min(d, 0.5), 0.0, hs, P.m("stand", (50, 52, 58)), outline=OL)]
    for r in range(2):
        for c in range(4):
            x = P.x0 + w * (c + 0.5) / 4
            z = hs + 0.05 + r * (h - hs - 0.1) / 2
            out += M.monitor(P.ctx, f"{P.nm}_m{r}{c}", x, P.y0 + 0.25, z, w / 4 - 0.06, (h - hs - 0.1) / 2 - 0.08, yaw=0.0, stand=False, screen=None)
    return out


def _v_villa_herd(P):
    cx, cy, w, d, h = P.cx, P.cy, P.w, P.d, P.h
    hc = min(h * 0.45, 0.95)
    yf = cy - min(d, 0.7) / 2
    out = [box(cx, cy, w, min(d, 0.7), 0.0, hc, P.m("body", (90, 96, 104)), bevel=0.01, outline=OL),
           box(cx, cy, w, min(d, 0.7), hc, hc + 0.03, P.m("top", (60, 62, 68)), outline=OL)]
    out += doors(P, P.x0 + 0.05, P.x1 - 0.05, yf, 0.1, hc - 0.1, 3, P.m("ovdoor", (80, 84, 92)), P.m("knob", (170, 174, 180)))
    out.append(box(cx, yf - 0.03, w * 0.3, 0.012, hc * 0.35, hc * 0.5, P.g("fire", (255, 150, 60), 2.0)))
    for j in range(4):
        out.append(cyl(P.x0 + 0.3 + (w - 0.6) * j / 3, cy, 0.1, hc + 0.03, hc + 0.045, P.m("burner", (40, 40, 44)), seg=14))
    out.append(lathe(P.x0 + 0.3 + (w - 0.6) / 3, cy, [(0.0, hc + 0.04), (0.13, hc + 0.04), (0.14, hc + 0.2), (0.0, hc + 0.2)], P.m("pot", (170, 60, 60)), seg=14, outline=OL))
    # Abzugshaube
    out.append(box(cx, cy + 0.1, w * 0.8, 0.5, h - 0.35, h - 0.05, P.m("hood", (150, 105, 62)), bevel=0.02, outline=OL))
    out.append(box(cx, cy + 0.1, w * 0.4, 0.3, h - 0.05, h + 0.3, P.m("hood", (150, 105, 62)), outline=OL))
    return out


def _v_villa_kisten(P):
    cx, cy, w, d, h = P.cx, P.cy, P.w, P.d, P.h
    out = M.crate_stack(P.ctx, P.nm + "_a", P.x0 + 0.4, cy, 0.7, 0.6, n=2, rgb=(190, 140, 90), dark=(130, 90, 55), seed=P.seed)
    out.append(box(P.x1 - 0.45, cy, 0.7, min(d, 0.6), 0.0, 0.5, P.m("case", (50, 52, 58)), bevel=0.02, outline=OL))
    out.append(box(P.x1 - 0.45, cy, 0.66, min(d, 0.6) - 0.04, 0.5, 0.53, P.m("case_d", (70, 72, 80))))
    out.append(cyl(P.x1 - 0.45, cy - 0.2, 0.18, 0.53, 0.56, P.m("reel", (90, 92, 100)), seg=16))
    out.append(tube([(P.x0 + 0.2, P.y0 - 0.1, 0.02), (P.x0 + 0.6, P.y0 - 0.25, 0.02), (P.x1 - 0.3, P.y0 - 0.15, 0.02)], 0.012, P.m("cable", (30, 30, 34)), seg=6))
    return out


def _v_own_sarkophag(P):
    cx, cy, w, d, h = P.cx, P.cy, P.w, P.d, P.h
    stone = P.m("stone", (200, 204, 216))
    out = [box(cx, cy, w, d, 0.0, 0.55, stone, bevel=0.015, outline=OL),
           box(cx, cy, w + 0.08, d + 0.08, 0.55, 0.7, stone, bevel=0.02, outline=OL),
           blob(cx, cy, 0.7, w * 0.38, d * 0.3, 0.14, (P.m("effigy", (190, 194, 206)), P.m("effigy_d", (150, 154, 166))), seed=P.seed, seg=12, rings=5),
           lathe(cx + w * 0.3, cy, [(0.0, 0.84), (0.09, 0.86), (0.07, 0.98), (0.0, 1.0)], P.m("effigy", (190, 194, 206)), seg=10)]
    for j in range(5):
        out.append(box(P.x0 + 0.2 + (w - 0.4) * j / 4, P.y0 + 0.01, 0.08, 0.02, 0.1, 0.45, P.m("pilaster", (170, 174, 186))))
    for sx in (-1, 1):
        out += candle(P, cx + sx * (w / 2 + 0.12), P.y0 + 0.1, 0.0, 0.3, 0.02)
    return out


_VILLA = {"kessel": _v_villa_kessel, "monitorwand": _v_villa_monitorwand, "herd": _v_villa_herd, "kisten": _v_villa_kisten}


@AM.variant
def own_variants(P, kind):
    """Oeffentliche Arten, die auf villa/graveyard anders aussehen (frueher Zweige in _atlas_models.py)."""
    key = P.sc.key
    if key == "villa" and kind in _VILLA:
        return _VILLA[kind](P)
    if key in OWN and kind == "sarkophag":
        return _v_own_sarkophag(P)
    return None
