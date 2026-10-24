# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_villa.py - Hollowmere Manor: villa_layout.py -> Bodenkacheln, Objekte, Minimaps (je Variante) und
# Villa/VillaSmall.g.cs + Villa/VillaLarge.g.cs (gleiches Datenformat wie die Atlas-Karten, siehe
# UnknownsAtlas/tools/gen_park.py, von dem dieser Generator abgeleitet ist).
#
#   python tools/gen_villa.py            Graybox (40 px/m)
#   python tools/gen_villa.py --ppm 128  hoehere Bodenaufloesung
#
# Beide Varianten teilen Boden und Objekte: der Boden zeigt immer die grosse Karte, die kleine nimmt nur
# die Kacheln des Hauses und verrammelt die drei Aussentueren (Prop "barrikade"). Jede Variante hat eigene
# Waende, Raeume, Konsolen, Vents, Tueren, Kameras und eine eigene Minimap.
# Objekte, die villa_art.py (Fable-Stilblatt) schon zeichnet, kommen von dort, alle anderen als Graybox-Block.

import hashlib
import heapq
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from shapely import affinity, contains_xy
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ATLAS_TOOLS = PROJECT.parent / "UnknownsAtlas" / "tools"
sys.path.insert(0, str(ATLAS_TOOLS))
sys.path.insert(0, str(HERE))

import museum_art as A          # noqa: E402  (pack, shape_bounds)
import map_labels               # noqa: E402
import villa_layout as L        # noqa: E402

try:
    import villa_art as VA      # Fable-Stilblatt; fehlt er, bleibt alles Graybox
    import villa_art2           # Einrichtung seit dem Audit 15.10. (traegt sich in villa_art ein)
except Exception as e:          # noqa: BLE001
    VA = None
    print(f"note: villa_art not usable ({e}) - props stay graybox")

ASSETS = PROJECT / "Resources" / "villa"
OUT_CS = PROJECT / "Villa"
PREVIEW = HERE / "_villa"

FLOOR_PPM = 40
PROP_PPM = 160
SPEED = 2.5                     # m/s, wie docs/KARTEN_VERKLEINERUNG.md
OX, OY = L.ORIGIN

# Bodenkacheln: Raster in Plan-Metern, so geschnitten, dass das Haus (0..34 x 0..24) genau 6 Kacheln belegt
TILE_X = [0.0, 11.5, 23.0, 34.0, 42.0, 50.0]
TILE_Y = [0.0, 12.0, 24.0, 30.0, 36.0]

VOID = (14, 12, 18)
WALL_TOP = (40, 30, 36)
HEDGE_TOP = (34, 58, 34)
ROOM_COL = {
    "kitchen": (176, 160, 130), "laundry": (150, 150, 140), "seance": (120, 70, 80), "radio": (130, 120, 104),
    "boxroom": (120, 104, 90), "observatory": (90, 100, 130), "boiler": (100, 90, 84), "westhall": (140, 120, 100),
    "library": (110, 80, 60), "chapel": (110, 110, 120), "hall": (160, 130, 96), "booth": (90, 90, 96),
    "vestibule": (140, 120, 100), "makeup": (170, 140, 150), "gallery": (130, 100, 90), "trophy": (130, 110, 80),
    "fireplace": (150, 90, 70), "study": (120, 100, 70), "terrace": (130, 126, 116), "driveway": (150, 144, 130),
    "crewcamp": (110, 120, 90), "greenhouse": (110, 140, 110), "fountain": (90, 110, 90), "graveyard": (80, 90, 70),
    "crypt": (90, 90, 96),
}
KIND_COL = {
    "freitreppe": (120, 60, 50), "standuhr": (90, 60, 40), "herd": (60, 60, 64), "funktisch": (70, 70, 60),
    "kisten": (140, 110, 70), "kessel": (80, 60, 50), "buecherregal": (100, 70, 40), "altar": (200, 190, 170),
    "monitorwand": (30, 30, 40), "schminktisch": (220, 200, 200), "gewehrschrank": (90, 60, 40), "kamin": (120, 70, 60),
    "aggregat": (200, 170, 40), "zelt": (60, 80, 60), "hecke": (40, 80, 40), "filmkamera": (30, 30, 30),
    "scheinwerfer": (40, 40, 40), "seance_tisch": (80, 40, 40), "kandelaber": (220, 180, 80), "kuechentisch": (160, 120, 80),
    "waschzuber": (150, 150, 160), "requisiten": (150, 120, 90), "teleskop": (180, 150, 70), "kohlen": (40, 40, 40),
    "lesetisch": (120, 80, 50), "kirchenbank": (110, 80, 50), "baer": (90, 60, 40), "sessel": (120, 40, 50),
    "schreibtisch": (110, 80, 50), "catering": (200, 200, 200), "absperrung": (230, 200, 40), "urne": (150, 150, 150),
    "gartenbank": (110, 90, 70), "pflanztisch": (100, 120, 90), "brunnen": (130, 130, 140), "grabstein": (150, 150, 155),
    "sarg": (120, 110, 100), "barrikade": (130, 90, 50), "treppensperre": (150, 100, 70),
}

SKELD_CONSOLES = {   # wie gen_park.py
    "Cafeteria": ["Cafeteria/DataConsole/2", "Cafeteria/FixWiringConsole/4", "Cafeteria/GarbageConsole/2"],
    "Admin": ["Admin/SwipeCardConsole/0", "Admin/UploadDataConsole/0", "Admin/FixWiringConsole/2"],
    "Security": ["Security/DivertPowerConsole/1", "Security/FixWiringConsole/5"],
    "Electrical": ["Electrical/CalibrateConsole/0", "Electrical/DivertPowerConsole/0",
                   "Electrical/UploadDataConsole/0", "Electrical/FixWiringConsole/0"],
    "Reactor": ["Reactor/StartReactorConsole/2", "Reactor/UnlockManifoldsConsole/2"],
    "Weapons": ["Weapons/WeaponConsole/0", "Weapons/UploadDataConsole/1", "Weapons/DivertPowerConsole/1"],
    "Nav": ["Nav/ChartCourseConsole/0", "Nav/StabilizeSteeringConsole/0", "Nav/UploadDataConsole/0",
            "Nav/DivertPowerConsole/1", "Nav/FixWiringConsole/3"],
    "Shields": ["Shields/ShieldConsole/0", "Shields/DivertPowerConsole/1"],
    "Comms": ["Comms/UploadDataConsole/1", "Comms/DivertPowerConsole/1"],
    "UpperEngine": ["UpperEngine/AlignEngineConsole/0", "UpperEngine/FuelEngineConsole/0",
                    "UpperEngine/DivertPowerConsole/1"],
    "LowerEngine": ["LowerEngine/AlignEngineConsole/1", "LowerEngine/FuelEngineConsole/0",
                    "LowerEngine/DivertPowerConsole/1"],
    "MedBay": ["MedBay/MedBayConsole/0"],
    "Storage": ["Storage/gasCanConsole/0", "Storage/FixWiringConsole/1", "Storage/AirlockConsole/0"],
    "LifeSupp": ["LifeSupp/CleanFilterConsole/0", "LifeSupp/GarbageConsole/0", "LifeSupp/DivertPowerConsole/1"],
}
DOOR_SYSTEMS = ("Cafeteria", "Storage", "UpperEngine", "LowerEngine", "Security", "MedBay",
                "Electrical", "Reactor", "LifeSupp", "Comms")


# ------------------------------------------------------------------ Geometrie

def W(g):
    """Plan-Meter (y nach Sueden) -> Atlas-Weltmeter (y nach Norden, Spawn-Naehe bei 0/0)."""
    return affinity.affine_transform(g, [1, 0, 0, -1, -OX, OY])


def wp(p):
    return (p[0] - OX, OY - p[1])


def shape(s):
    k = s[0]
    if k == "rect":
        return box(*s[1:5])
    if k == "circle":
        return Point(s[1], s[2]).buffer(s[3], 24)
    if k == "ellipse":
        return affinity.scale(Point(s[1], s[2]).buffer(1, 32), s[3], s[4])
    raise ValueError(k)


def wshape(s):
    """Hindernis-Form in Weltmetern (fuer die Prop-Tupel, die museum_art/villa_art erwarten)."""
    k = s[0]
    if k == "rect":
        x0, y0, x1, y1 = s[1:5]
        return ("rect", x0 - OX, OY - y1, x1 - OX, OY - y0)
    if k == "circle":
        return ("circle", s[1] - OX, OY - s[2], s[3])
    return ("ellipse", s[1] - OX, OY - s[2], s[3], s[4])


def areas_of(v):
    return [a for a in L.AREAS if v in a[3]]


def opening_box(o):
    ax, at, a, b = o[:4]
    t = L.WALL / 2 + 0.01
    return box(at - t, a, at + t, b) if ax == "x" else box(a, at - t, b, at + t)


def area_geom(a, areas):
    g = box(*a[2]).buffer(-L.WALL / 2, join_style=2)
    outer = box(*a[2])
    for b in areas:
        if b is not a and box(*b[2]).within(outer) and not box(*b[2]).equals(outer):
            g = g.difference(box(*b[2]).buffer(L.WALL / 2, join_style=2))
    return g


def build(v):
    """Plan-Geometrie einer Variante: begehbare Flaeche, Flaeche je Bereich, Oeffnungen dieser Variante."""
    areas = areas_of(v)
    geoms = {a[0]: area_geom(a, areas) for a in areas}
    opens = [o for o in L.OPENINGS if v in o[4]]
    walk = unary_union(list(geoms.values()) + [opening_box(o) for o in opens]).buffer(0)
    return walk, geoms, opens


def geom_parts(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


def props_of(v):
    """Alle Objekte der Variante: (Form, Art, opaque?)."""
    out = [(s, k, True) for s, k, vs in L.OPAQUE if v in vs] + [(s, k, False) for s, k, vs in L.GLASS if v in vs]
    out += [(s, k, None) for s, k, vs in getattr(L, "DECOR", []) if v in vs]      # None = ohne Kollision
    return out


def barricades(v):
    if v != "small":
        return []
    out = []
    for ax, at, a, b in L.BARRICADES:
        t = L.WALL / 2
        out.append((("rect", at - t, a, at + t, b) if ax == "x" else ("rect", a, at - t, b, at + t), "barrikade"))
    return out


# ------------------------------------------------------------------ Pruefungen

def walk_time(walk, spawn):
    """Weitester Laufweg ab Spawn: Raster 0,25 m, 0,3 m Wandabstand, 8 Nachbarn."""
    cell = 0.25
    free = walk.buffer(-0.3)
    x0, y0, x1, y1 = walk.bounds
    nx, ny = int((x1 - x0) / cell) + 1, int((y1 - y0) / cell) + 1
    xs = x0 + (np.arange(nx) + 0.5) * cell
    ys = y0 + (np.arange(ny) + 0.5) * cell
    gx, gy = np.meshgrid(xs, ys)
    ok = contains_xy(free, gx, gy)
    dist = np.full(ok.shape, np.inf)
    si, sj = int((spawn[0] - x0) / cell), int((spawn[1] - y0) / cell)
    if not ok[sj, si]:
        print("WARN spawn not on free floor")
    dist[sj, si] = 0.0
    pq = [(0.0, sj, si)]
    nbr = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    while pq:
        d, j, i = heapq.heappop(pq)
        if d > dist[j, i]:
            continue
        for di, dj, w in nbr:
            a, b = i + di, j + dj
            if a < 0 or b < 0 or a >= nx or b >= ny or not ok[b, a]:
                continue
            if di and dj and (not ok[j, a] or not ok[b, i]):
                continue
            nd = d + w * cell
            if nd < dist[b, a]:
                dist[b, a] = nd
                heapq.heappush(pq, (nd, b, a))
    reach = np.where(ok & np.isfinite(dist), dist, -1)
    k = np.unravel_index(np.argmax(reach), reach.shape)
    unreached = int(np.sum(ok & ~np.isfinite(dist)))
    return float(reach[k]), (float(xs[k[1]]), float(ys[k[0]])), unreached


# ------------------------------------------------------------------ Boden (geteilt, grosse Karte)

def render_floor(ppm):
    # Kartengrafik (Fable, villa_floor.render_map): grosse Karte in Plan-Lage, (50 x 36 m) * ppm
    try:
        import villa_floor as VF
        if hasattr(VF, "render_map"):
            img = VF.render_map(ppm).convert("RGB")
            return save_floor(img, ppm)
    except Exception as e:      # noqa: BLE001
        print(f"WARN villa_floor.render_map failed ({e}) - graybox floor")
    walk, geoms, opens = build("large")
    bx0, by0, bx1, by1 = L.VARIANTS["large"]
    img = Image.new("RGB", (int((bx1 - bx0) * ppm), int((by1 - by0) * ppm)), VOID)
    d = ImageDraw.Draw(img, "RGBA")
    P = lambda x, y: ((x - bx0) * ppm, (y - by0) * ppm)        # Plan: y nach unten wie das Bild

    def poly(g, fill):
        for p in geom_parts(g):
            d.polygon([P(*q) for q in p.exterior.coords], fill=fill)
            for h in p.interiors:
                d.polygon([P(*q) for q in h.coords], fill=VOID)

    # Waende: Huelle jedes Bereichs (Haus dunkel, Garten als Hecke), danach Boden + Oeffnungen darueber
    for a in areas_of("large"):
        garden = a[0] in ("terrace", "driveway", "crewcamp", "fountain", "graveyard")
        poly(box(*a[2]), HEDGE_TOP if garden else WALL_TOP)
    for key, g in geoms.items():
        poly(g, ROOM_COL.get(key, (140, 140, 140)))
    for o in opens:
        poly(opening_box(o), (120, 110, 100))
    for key in L.DARK:
        if key in geoms:
            poly(geoms[key], (20, 30, 70, 60))
    for x in range(int(bx0), int(bx1) + 1):
        d.line([P(x, by0), P(x, by1)], fill=(0, 0, 0, 22), width=1)
    for y in range(int(by0), int(by1) + 1):
        d.line([P(bx0, y), P(bx1, y)], fill=(0, 0, 0, 22), width=1)
    try:
        font = ImageFont.truetype("arialbd.ttf", max(10, int(ppm * 0.7)))
    except OSError:
        font = ImageFont.load_default()
    for a in areas_of("large"):
        c = geoms[a[0]].representative_point()
        d.text(P(c.x, c.y), a[1], font=font, fill=(255, 255, 255, 120), anchor="mm")
    return save_floor(img, ppm)


def save_floor(img, ppm):
    PREVIEW.mkdir(exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    img.save(PREVIEW / "floor_preview.jpg", quality=85)
    for old in ASSETS.glob("villa_floor_*.jpg"):
        old.unlink()
    tiles = []      # (Index, Welt-x links, Welt-y unten, w, h, Plan-Rechteck)
    i = 0
    for r in range(len(TILE_Y) - 1):
        for c in range(len(TILE_X) - 1):
            px0, px1, py0, py1 = TILE_X[c], TILE_X[c + 1], TILE_Y[r], TILE_Y[r + 1]
            x0, y0 = int(round(px0 * ppm)), int(round(py0 * ppm))
            w4 = (int(round(px1 * ppm)) - x0) // 4 * 4
            h4 = (int(round(py1 * ppm)) - y0) // 4 * 4
            img.crop((x0, y0, x0 + w4, y0 + h4)).save(ASSETS / f"villa_floor_{i}.jpg", quality=85)
            tiles.append((i, x0 / ppm - OX, OY - (y0 + h4) / ppm, w4, h4, (px0, py0, px1, py1)))
            i += 1
    print(f"floor {img.width}x{img.height} in {len(tiles)} tiles")
    return tiles


# ------------------------------------------------------------------ Objekte (geteilter Atlas)

def draw_block(kind, ws):
    if VA is not None and kind in getattr(VA, "KINDS", ()):
        try:
            return VA.draw(kind, ws, abs(hash((kind, ws))) % 997, PROP_PPM)
        except Exception as e:      # noqa: BLE001
            print(f"WARN villa_art.draw({kind}) failed: {e} - graybox block")
    g = shape(ws)
    x0, y0, x1, y1 = g.bounds
    pad = 0.1
    w = max(1, int((x1 - x0 + 2 * pad) * PROP_PPM))
    h = max(1, int((y1 - y0 + 2 * pad) * PROP_PPM))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    Pp = lambda x, y: ((x - x0 + pad) * PROP_PPM, (y1 + pad - y) * PROP_PPM)
    col = KIND_COL.get(kind, (150, 150, 150))
    dd.polygon([Pp(*q) for q in g.exterior.coords], fill=col + (255,), outline=(20, 20, 26, 255))
    return im, x0 - pad, y0 - pad, y0


# Tauschbilder fuer die Mechaniken (HollowmereWorld): gleiche Art und Groesse, anderer Zustand. Sie liegen im
# Konsolen-Atlas unter "Prop/<Art>/<welt_x>/<welt_y>/<Variante>" (3 Dezimalen wie in der g.cs), Anker unten links
# wie das Prop selbst, damit der Renderer nur das Sprite tauscht.
PROP_VARIANTS = {"portrait": ("l", "r"), "standuhr": ("p1", "p2"), "scheinwerfer": ("off",), "kandelaber": ("off",)}
PROP_VARIANT_SPRITES = {}


def render_props():
    """Alle Objekte beider Varianten einmal zeichnen und packen. Rueckgabe: {(Art, Weltform): Prop-Tupel}."""
    uniq = {}
    for v in L.VARIANTS:
        for s, k, _o in props_of(v):
            uniq.setdefault((k, wshape(s)), None)
        for s, k in barricades(v):
            uniq.setdefault((k, wshape(s)), None)
    keys = list(uniq)
    images, meta = [], []
    for i, (kind, ws) in enumerate(keys):
        im, wx, wy, base = draw_block(kind, ws)
        images.append((i, im))
        fx0, _, fx1, _ = A.shape_bounds(ws)
        meta.append((kind, wx, wy, base, fx0, fx1))
        for var in PROP_VARIANTS.get(kind, ()):
            try:
                im2, wx2, wy2, _b = VA.draw(kind, ws, abs(hash((kind, ws))) % 997, PROP_PPM, variant=var)
            except Exception as e:      # noqa: BLE001
                print(f"WARN variant {kind}/{var} failed: {e}")
                continue
            if im2.size != im.size or abs(wx2 - wx) > 1e-6 or abs(wy2 - wy) > 1e-6:
                print(f"WARN variant {kind}/{var}: size/anchor differs ({im2.size} vs {im.size})")
            # Anker so, dass das Tauschbild an der Stelle des Originals sitzt (Prop-Pivot = unten links bei wx/wy)
            PROP_VARIANT_SPRITES[f"Prop/{kind}/{wx:.3f}/{wy:.3f}/{var}"] = (im2, (wx - wx2) * PROP_PPM, (wy - wy2) * PROP_PPM)
    atlases, placed = A.pack(images, max_w=2048, max_h=2048)
    for old in ASSETS.glob("villa_props_*.png"):
        old.unlink()
    for k, atlas in enumerate(atlases):
        atlas.save(ASSETS / f"villa_props_{k}.png", optimize=True)
    out = {}
    for i, key in enumerate(keys):
        kind, wx, wy, base, fx0, fx1 = meta[i]
        page, x, y, ww, hh = placed[i]
        out[key] = (kind, page, x, atlases[page].height - y - hh, ww, hh, wx, wy, base, fx0, fx1)
    print(f"props {len(out)} in {len(atlases)} atlas(es)")
    return out


# ------------------------------------------------------------------ Konsolen (wie gen_park.py, Weltmeter)

def place_consoles(v, walk_w, rooms_w, door_pts, obstacles_w):
    placed = {}
    free = walk_w.difference(unary_union(obstacles_w).buffer(0.5)).buffer(0) if obstacles_w else walk_w
    edge = walk_w.boundary
    fixed = {k: wp(p) for k, p in L.FIXED.items()}
    fixed.update({k: wp(p) for k, p in getattr(L, "FIXED_" + v.upper(), {}).items()})
    taken = [Point(p) for p in list(fixed.values())] + \
            [Point(wp(p)) for p in (L.EMERGENCY, L.SURVEILLANCE, L.ADMIN_TABLE, L.FREEPLAY, L.SPAWN)]
    taken += [Point(wp(p)) for p in L.VENTS[v].values()] + [Point(wp(p)) for p in L.CAMERAS[v]]
    # Geheimgaenge und Standuhr brauchen freie Wand: dort keine Konsole
    for _key, _prop, ent, ext, _both, vs in L.SECRETS:
        if v in vs:
            taken += [Point(wp(ent)), Point(wp(ext))]
    taken.append(Point(wp(L.CLOCK)))
    for key, (name, sysname, g) in rooms_w.items():
        keys = [k for k in SKELD_CONSOLES.get(sysname, []) if k not in fixed]
        if not keys:
            continue
        ring = g.buffer(-0.55)
        cands = []
        for part in geom_parts(ring):
            line = part.exterior
            n = max(16, int(line.length / 0.3))
            for i in range(n):
                p = line.interpolate(i / n, normalized=True)
                if edge.distance(p) > 0.75 or not free.contains(p):
                    continue
                if min([p.distance(q) for q in door_pts] + [99]) < 1.5:
                    continue
                cands.append(p)
        chosen = []
        for k in keys:
            best, score = None, -1e9
            for p in cands:
                dd = min([p.distance(q) for q in chosen + taken] + [99])
                if dd < 1.2:
                    continue
                sc = min(dd, 4.0) + 0.15 * (p.y - g.centroid.y)      # Nordwand bevorzugt
                if sc > score:
                    best, score = p, sc
            if best is None:
                best = g.representative_point()
                print(f"WARN [{v}] no spot for {k} in {name}")
            chosen.append(best)
            placed[k] = (round(best.x, 2), round(best.y, 2))
        taken.extend(chosen)
    for k, p in fixed.items():
        placed[k] = p
    return placed


# ------------------------------------------------------------------ Task-Bloecke (Fable, villa_consoles)

def area_at(p):
    """Bereich (key) unter einem Plan-Punkt, innerster zuerst (Gruft vor Friedhof)."""
    best = None
    for a in L.AREAS:
        x0, y0, x1, y1 = a[2]
        if x0 - 0.3 <= p[0] <= x1 + 0.3 and y0 - 0.3 <= p[1] <= y1 + 0.3:
            if best is None or (x1 - x0) * (y1 - y0) < (best[2][2] - best[2][0]) * (best[2][3] - best[2][1]):
                best = a
    return best


def wall_side(p, a):
    x0, y0, x1, y1 = a[2]
    d = {"N": p[1] - y0, "S": y1 - p[1], "W": p[0] - x0, "E": x1 - p[0]}      # Plan: Norden = kleines y
    side = min(d, key=d.get)
    return side if d[side] < 1.0 else "-"


def write_console_brief(all_consoles):
    """tools/_villa/console_brief.json: jede Konsole beider Varianten mit Plan-Lage, Raum und Wandseite."""
    import json
    rows = {}
    for v, consoles in all_consoles.items():
        pts = {k: (p[0] + OX, OY - p[1]) for k, p in consoles.items()}          # Welt -> Plan
        pts.update({"EmergencyButton": L.EMERGENCY, "SurveillanceConsole": L.SURVEILLANCE,
                    "AdminTable": L.ADMIN_TABLE, "FreeplayLaptop": L.FREEPLAY})
        for vid, p in L.VENTS[v].items():
            pts[f"Vent/{vid}"] = p
        for k, p in pts.items():
            a = area_at(p)
            rows.setdefault(f"{v}:{k}", {"variant": v, "key": k, "x": round(p[0], 2), "y": round(p[1], 2),
                                          "room": a[0] if a else "-", "wall": wall_side(p, a) if a else "-"})
    PREVIEW.mkdir(exist_ok=True)
    (PREVIEW / "console_brief.json").write_text(json.dumps(sorted(rows.values(), key=lambda r: (r["variant"], r["key"])),
                                                            indent=1), encoding="utf-8")


def render_consoles(all_consoles):
    """Task-Bloecke beider Varianten in einen Atlas. Gleicher Schluessel in beiden Varianten = ein Sprite,
    solange Raum und Wandseite gleich sind; sonst bekommt die grosse Variante "<key>@large"."""
    try:
        import villa_consoles as VC
    except Exception as e:      # noqa: BLE001
        print(f"note: villa_consoles not usable ({e}) - Skeld console images stay")
        return {"small": [], "large": []}
    import json
    brief = json.loads((PREVIEW / "console_brief.json").read_text(encoding="utf-8"))
    sprites = VC.render_all(PROP_PPM, brief)          # {(variant, key): (img, ax, ay)}
    sprites.update(render_doors_cams(PROP_PPM))
    for v in L.VARIANTS:                              # Tauschbilder der Mechaniken (render_props), je Variante
        for key, spr in PROP_VARIANT_SPRITES.items():
            sprites[(v, key)] = spr
    names, per_variant = {}, {"small": {}, "large": {}}
    by_content = {}                                   # gleiche Bilder unter verschiedenen Schluesseln (Tueren) nur einmal
    for (v, key), spr in sorted(sprites.items(), key=lambda kv: (kv[0][0] != "small", kv[0][1])):
        name = key
        if name in names:
            old = names[name]
            if old[0].size != spr[0].size or old[0].tobytes() != spr[0].tobytes() or old[1:] != spr[1:]:
                name = f"{key}@{v}"                   # andere Wand oder anderer Raum in dieser Variante
        if name not in names:
            h = (spr[0].size, spr[1], spr[2], hashlib.md5(spr[0].tobytes()).hexdigest())
            if h in by_content:
                name = by_content[h]
            else:
                by_content[h] = name
        names.setdefault(name, spr)
        per_variant[v][key] = (name, spr)
    for old in ASSETS.glob("villa_consoles_*.png"):
        old.unlink()
    keys = sorted(names)
    # Tauschbilder ("Prop/...") ohne den Weichzeichner: sie ersetzen 1:1 ein ungefiltertes Prop-Bild
    images = [(i, names[k][0] if k.startswith("Prop/") else names[k][0].filter(ImageFilter.GaussianBlur(0.45))) for i, k in enumerate(keys)]
    atlases, placed = A.pack(images, max_w=2048, max_h=2048)
    for k, atlas in enumerate(atlases):
        atlas.save(ASSETS / f"villa_consoles_{k}.png", optimize=True)
    entry = {}
    for i, name in enumerate(keys):
        page, x, y, w, h = placed[i]
        _im, ax, ay = names[name]
        entry[name] = (page, x, atlases[page].height - y - h, w, h, ax / w, ay / h)
    out = {}
    for v in per_variant:
        out[v] = [(key,) + entry[name] for key, (name, _s) in sorted(per_variant[v].items())]
    print(f"consoles {len(keys)} sprites in {len(atlases)} atlas(es)")
    return out


def render_doors_cams(ppm):
    """Tuer-Bildsaetze ("Door/<label>", "/1".."/5") und Kameras ("Camera/<i>", "/on") je Variante
    (villa_doors.py). Gleiche Art und Achse = gleiche Bilder; render_consoles legt sie nur einmal ab."""
    import villa_doors as VD
    out = {}
    cache = {}
    for v in L.VARIANTS:
        for o in L.OPENINGS:
            t = o[4].get(v)
            if not t or t == "open":
                continue
            ax, at, a0, b0 = o[:4]
            label = f"{ax}{at:g}-{(a0 + b0) / 2:g}"
            kind = L.DOOR_KIND.get((ax, at, (a0 + b0) / 2), "wood")
            if (kind, ax) not in cache:
                cache[(kind, ax)] = VD.door_frames(kind, ax, ppm)
            frames = cache[(kind, ax)]
            out[(v, f"Door/{label}")] = frames[0]
            for k, fr in enumerate(frames[1:], 1):
                out[(v, f"Door/{label}/{k}")] = fr
        if "cam" not in cache:
            cache["cam"] = (VD.camera(ppm, False), VD.camera(ppm, True))
        for i in range(len(L.CAMERAS[v])):
            out[(v, f"Camera/{i}")] = cache["cam"][0]
            out[(v, f"Camera/{i}/on")] = cache["cam"][1]
    return out


# ------------------------------------------------------------------ Minimap (je Variante)

def label_point(g, name, obst):
    free = g.buffer(-0.3).difference(obst)
    half_w, half_h = max(1.0, len(name) * 0.26), 0.55
    c = g.centroid
    best, best_d = None, 1e9
    x0, y0, x1, y1 = g.bounds
    steps = 30
    for i in range(steps + 1):
        for j in range(steps + 1):
            px, py = x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * j / steps
            if not free.contains(box(px - half_w, py - half_h, px + half_w, py + half_h)):
                continue
            dd = (px - c.x) ** 2 + (py - c.y) ** 2
            if dd < best_d:
                best, best_d = Point(px, py), dd
    return best if best is not None else g.representative_point()


def minimap(v, walk_w, rooms_w, obst_w, vents_w):
    s = 24
    bx0, by0, bx1, by1 = L.VARIANTS[v]
    wx0, wx1, wy0, wy1 = bx0 - OX, bx1 - OX, OY - by1, OY - by0
    img = Image.new("RGBA", (int((wx1 - wx0) * s), int((wy1 - wy0) * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    P = lambda x, y: ((x - wx0) * s, (wy1 - y) * s)
    for p in geom_parts(walk_w):
        d.polygon([P(*q) for q in p.exterior.coords], fill=(226, 214, 232, 235))
        for h in p.interiors:
            d.polygon([P(*q) for q in h.coords], fill=(0, 0, 0, 0))
    for p in geom_parts(walk_w):
        for ring in [p.exterior] + list(p.interiors):
            d.line([P(*q) for q in ring.coords], fill=(34, 20, 30, 255), width=4, joint="curve")
    try:
        font = ImageFont.truetype("arialbd.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    obst = unary_union(obst_w + [box(x - 1.1, y - 0.7, x + 1.1, y + 0.7) for x, y in vents_w]).buffer(0.3) \
        if obst_w else Point(1e6, 1e6).buffer(0.1)
    labels = []
    by_name = {}
    for key, (name, _s, g) in rooms_w.items():
        by_name.setdefault(name, []).append(g)
    area = walk_w.buffer(0.15)
    for name, gs in by_name.items():
        c = label_point(max(gs, key=lambda g: g.area), name, obst)
        map_labels.place(d, font, name, c.x, c.y, area, s, P, (34, 20, 30, 255), labels)
    img.save(ASSETS / f"villa_minimap_{v}.png", optimize=True)
    return labels


# ------------------------------------------------------------------ C#

def v2(p):
    return f"new({p[0]:.3f}f, {p[1]:.3f}f)"


def chain(points):
    return "new Vector2[] { " + ", ".join(v2(p) for p in points) + " }"


def rings_of(g):
    out = []
    for p in geom_parts(g):
        out.append(list(p.exterior.coords)[:-1])
        for h in p.interiors:
            out.append(list(h.coords)[:-1])
    return out


def emit(v, walk_w, rooms_w, opens, tiles, props, consoles, labels, console_sprites=()):
    cls = "VillaSmall" if v == "small" else "VillaLarge"
    bx0, by0, bx1, by1 = L.VARIANTS[v]
    wx0, wx1, wy0, wy1 = bx0 - OX, bx1 - OX, OY - by1, OY - by0
    full = box(wx0 - 5, wy0 - 5, wx1 + 5, wy1 + 5)
    solid = full.difference(walk_w)
    move = walk_w.difference(affinity.translate(solid, 0, -0.3)).buffer(0)
    shadow = unary_union([walk_w, affinity.translate(walk_w, 0, 0.45)]).buffer(0)
    items = props_of(v)
    opaque = [W(shape(L.hit_shape(s, k))) for s, k, o in items if o is True]
    glass = [W(shape(L.hit_shape(s, k))) for s, k, o in items if o is False]
    edges = unary_union([LineString(r + [r[0]]) for r in rings_of(walk_w)])
    casts = [p.distance(edges) > 0.08 for p in opaque]
    room_u = unary_union([g for _n, _s, g in rooms_w.values()])
    halls = [g for g in geom_parts(walk_w.difference(room_u).buffer(0)) if g.area > 1.0]
    my_tiles = [t for t in tiles if t[5][2] <= bx1 + 1e-6 and t[5][3] <= by1 + 1e-6]
    my_props = [props[(k, wshape(s))] for s, k, _o in items] + [props[(k, wshape(s))] for s, k in barricades(v)]

    Ls = []
    a = Ls.append
    a("// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0")
    a("// Licensed under GPL-3.0-or-later. See LICENSE for details.")
    a("//")
    a("// AUTOMATISCH ERZEUGT von tools/gen_villa.py aus tools/villa_layout.py - NICHT VON HAND AENDERN.")
    a(f"// Hollowmere Manor, Variante {v}: Geometrie, Raeume, Kacheln, Objekte, Plaetze der Skeld-Mechanik (Weltmeter).")
    a("")
    a("using System.Collections.Generic;")
    a("using UnityEngine;")
    a("using UnknownsAtlas;")
    a("")
    a("namespace UnknownsHalloween;")
    a("")
    a(f"internal static class {cls}")
    a("{")
    a(f"    public const float MinX = {wx0:.2f}f, MinY = {wy0:.2f}f, MaxX = {wx1:.2f}f, MaxY = {wy1:.2f}f;")
    for name, g in (("Walls", move), ("ShadowWalls", shadow)):
        a(f"    public static readonly Vector2[][] {name} =\n    {{")
        for r in rings_of(g):
            a(f"        {chain(r)},")
        a("    };")
    a("    public static readonly Vector2[][] Opaque =\n    {")
    for p in opaque:
        a(f"        {chain(list(p.exterior.coords)[:-1])},")
    a("    };")
    a("    public static readonly bool[] OpaqueCastsShadow = { " + ", ".join("true" if c else "false" for c in casts) + " };")
    a("    public static readonly Vector2[][] Glass =\n    {")
    for p in glass:
        a(f"        {chain(list(p.exterior.coords)[:-1])},")
    a("    };")
    a("    public static readonly (string Key, string Name, SystemTypes Room, Vector2[] Area)[] Rooms =\n    {")
    for key, (name, sysname, g) in rooms_w.items():
        a(f"        (\"{key}\", \"{name}\", SystemTypes.{sysname}, {chain(list(g.exterior.coords)[:-1])}),")
    a("    };")
    a("    public static readonly Vector2[][] Hallways =\n    {")
    for h in halls:
        a(f"        {chain(list(h.exterior.coords)[:-1])},")
    a("    };")
    a("    public static readonly (float X, float Y, float HalfW, float HalfH)[] MapLabels =\n    {")
    for lx, ly, hw, hh in labels:
        a(f"        ({lx:.3f}f, {ly:.3f}f, {hw:.3f}f, {hh:.3f}f),")
    a("    };")
    a(f"    public const float FloorPixelsPerMeter = {FLOOR_PPM}f;")
    a("    public static readonly (int Index, float WorldX, float WorldY, int W, int H)[] FloorTiles =\n    {")
    for i, twx, twy, tw, th, _r in my_tiles:
        a(f"        ({i}, {twx:.4f}f, {twy:.4f}f, {tw}, {th}),")
    a("    };")
    a(f"    public const float PropPixelsPerMeter = {PROP_PPM}f;")
    a("    public static readonly (string Kind, int Atlas, int X, int Y, int W, int H, float WorldX, float WorldY, float BaseY, float FootX0, float FootX1)[] Props =\n    {")
    for kind, page, x, y, ww, hh, pwx, pwy, base, fx0, fx1 in my_props:
        a(f"        (\"{kind}\", {page}, {x}, {y}, {ww}, {hh}, {pwx:.3f}f, {pwy:.3f}f, {base:.3f}f, {fx0:.3f}f, {fx1:.3f}f),")
    a("    };")
    a("    public static readonly (string Key, int Atlas, int X, int Y, int W, int H, float PivotX, float PivotY)[] ConsoleSprites =\n    {")
    for key, page, x, y, ww, hh, px, py in console_sprites:
        a(f"        (\"{key}\", {page}, {x}, {y}, {ww}, {hh}, {px:.4f}f, {py:.4f}f),")
    a("    };")
    a("")
    a("    public static readonly Dictionary<string, Vector2> Consoles = new()\n    {")
    for k, p in sorted(consoles.items()):
        a(f"        [\"{k}\"] = {v2(p)},")
    a("    };")
    for name, p in (("EmergencyButton", L.EMERGENCY), ("SurveillanceConsole", L.SURVEILLANCE),
                    ("AdminTable", L.ADMIN_TABLE), ("FreeplayLaptop", L.FREEPLAY), ("Spawn", L.SPAWN)):
        a(f"    public static readonly Vector2 {name} = {v2(wp(p))};")
    a(f"    public const float SpawnRadius = {L.SPAWN_RADIUS}f;")
    a("    public static readonly Dictionary<int, Vector2> Vents = new()\n    {")
    for vid, p in L.VENTS[v].items():
        a(f"        [{vid}] = {v2(wp(p))},")
    a("    };")
    a("    public static readonly int[][] VentNetworks =\n    {")
    for net in L.VENT_NETS[v]:
        a("        new[] { " + ", ".join(map(str, net)) + " },")
    a("    };")
    vert, hori = [], []
    for o in opens:
        t = o[4][v]
        if t == "open":
            continue
        _door, group = t
        ax, at, a0, b0 = o[:4]
        c = W(opening_box(o)).centroid
        label = f"{ax}{at:g}-{(a0 + b0) / 2:g}"
        (vert if ax == "x" else hori).append((label, c.x, c.y, b0 - a0, group))
    for nm, lst in (("VerticalDoors", vert), ("HorizontalDoors", hori)):
        a(f"    public static readonly AtlasMuseumLayout.DoorSlot[] {nm} =\n    {{")
        for label, cx, cy, length, grp in lst:
            a(f"        new(\"{label}\", {cx:.3f}f, {cy:.3f}f, {length:.2f}f, SystemTypes.{grp}, seeThrough: false),")
        a("    };")
    a("    public static readonly Vector2[] Cameras =\n    {")
    for p in L.CAMERAS[v]:
        a(f"        {v2(wp(p))},")
    a("    };")
    a("    public static readonly Dictionary<SystemTypes, Vector2> MapButtons = new()\n    {")
    done = set()
    for key, (name, sysname, g) in rooms_w.items():
        if sysname in DOOR_SYSTEMS and sysname not in done:
            c = g.representative_point()
            a(f"        [SystemTypes.{sysname}] = {v2((c.x, c.y + 0.8))},")
            done.add(sysname)
    a("    };")
    a("    /// <summary>Geheimgaenge (HollowmereWorld): Schluessel, Moebel-Art, Eingang, Ausgang, beide Richtungen.</summary>")
    a("    public static readonly (string Key, string Prop, Vector2 Entry, Vector2 Exit, bool Both)[] Secrets =\n    {")
    for key, prop, ent, ext, both, vs in L.SECRETS:
        if v in vs:
            a(f"        (\"{key}\", \"{prop}\", {v2(wp(ent))}, {v2(wp(ext))}, {'true' if both else 'false'}),")
    a("    };")
    a("    /// <summary>Standuhr in der Halle (Mitternachtsuhr), Standpunkt davor.</summary>")
    a(f"    public static readonly Vector2 Clock = {v2(wp(L.CLOCK))};")
    a("    /// <summary>Raeume mit schwaecherem Licht (Mechanik Kerzen und Dunkelheit).</summary>")
    a("    public static readonly string[] DarkRooms = { " + ", ".join(f"\"{k}\"" for k in sorted(L.DARK) if k in rooms_w or True) + " };")
    a("}")
    OUT_CS.mkdir(exist_ok=True)
    (OUT_CS / f"{cls}.g.cs").write_text("\n".join(Ls) + "\n", encoding="utf-8")
    groups = {}
    for _l, _x, _y, _len, grp in vert + hori:
        groups[grp] = groups.get(grp, 0) + 1
    print(f"[{v}] doors {len(vert)}V/{len(hori)}H {groups}, consoles {len(consoles)}, hallways {len(halls)}, rooms {len(rooms_w)}, tiles {len(my_tiles)}, props {len(my_props)}")
    if len(vert) != 7 or len(hori) != 6:
        print(f"WARN [{v}] door count must be 7V/6H")


# ------------------------------------------------------------------ Ablauf

def main(argv):
    global FLOOR_PPM
    if "--ppm" in argv:
        FLOOR_PPM = int(argv[argv.index("--ppm") + 1])
    ASSETS.mkdir(parents=True, exist_ok=True)
    tiles = render_floor(FLOOR_PPM)
    props = render_props()
    report = []
    data = {}
    for v in L.VARIANTS:
        walk, geoms, opens = build(v)
        walk_w = W(walk)
        rooms_w = {}
        for a in areas_of(v):
            sysname = a[4].get(v)
            if sysname:
                g = W(geoms[a[0]])
                if g.geom_type != "Polygon":
                    g = max(geom_parts(g), key=lambda p: p.area)
                rooms_w[a[0]] = (a[1], sysname, g)
        systems = {s for _n, s, _g in rooms_w.values()}
        missing = [s for s in SKELD_CONSOLES if s not in systems]
        if missing:
            print(f"WARN [{v}] systems without a room: {missing}")
        obstacles_w = [W(shape(L.hit_shape(s, k))) for s, k, o in props_of(v) if o is not None]
        door_pts = [W(opening_box(o)).centroid for o in opens]
        consoles = place_consoles(v, walk_w, rooms_w, door_pts, obstacles_w)
        free = walk_w.difference(unary_union(obstacles_w).buffer(0.25)) if obstacles_w else walk_w
        for k, p in list(consoles.items()) + [(f"Vent{i}", wp(p)) for i, p in L.VENTS[v].items()] + \
                [("Emergency", wp(L.EMERGENCY)), ("Surveillance", wp(L.SURVEILLANCE)), ("Admin", wp(L.ADMIN_TABLE))]:
            dd = free.distance(Point(p))
            if dd > 0.6:
                print(f"WARN [{v}] {k} at {p} not reachable ({dd:.2f} m)")
        far, far_pt, unreached = walk_time(walk_w, wp(L.SPAWN))
        report.append((v, far, far_pt, unreached))
        labels = minimap(v, walk_w, rooms_w, obstacles_w, [wp(p) for p in L.VENTS[v].values()])
        data[v] = (walk_w, rooms_w, opens, consoles, labels)
        preview(v, walk_w, consoles, obstacles_w)
    write_console_brief({v: d[3] for v, d in data.items()})
    sprites = render_consoles({v: d[3] for v, d in data.items()})
    for v, (walk_w, rooms_w, opens, consoles, labels) in data.items():
        emit(v, walk_w, rooms_w, opens, tiles, props, consoles, labels, sprites.get(v, []))
    copy_buttons()
    for v, far, far_pt, unreached in report:
        print(f"[{v}] farthest walk {far:.1f} m = {far / SPEED:.1f} s at {far_pt[0]:.1f}/{far_pt[1]:.1f}, unreached cells {unreached}")


def copy_buttons():
    """Freeplay-Logo und Lobby-Symbol (Fable, villa_buttons.render) nach Resources/villa."""
    try:
        import villa_buttons as VB
    except Exception as e:      # noqa: BLE001
        print(f"note: villa_buttons not usable ({e}) - text label button")
        return
    button, icon = VB.render()
    button.save(ASSETS / "button_villa.png", optimize=True)
    icon.save(ASSETS / "icon_villa.png", optimize=True)
    print(f"buttons {button.size} / {icon.size}")


def preview(v, walk_w, consoles, obstacles_w):
    """Kontrollbild in Weltlage: begehbar, Hindernisse, Konsolen (gelb), Vents (violett)."""
    s = 20
    bx0, by0, bx1, by1 = L.VARIANTS[v]
    wx0, wx1, wy0, wy1 = bx0 - OX, bx1 - OX, OY - by1, OY - by0
    img = Image.new("RGB", (int((wx1 - wx0) * s), int((wy1 - wy0) * s)), VOID)
    d = ImageDraw.Draw(img)
    P = lambda x, y: ((x - wx0) * s, (wy1 - y) * s)
    for p in geom_parts(walk_w):
        d.polygon([P(*q) for q in p.exterior.coords], fill=(150, 140, 125))
        for h in p.interiors:
            d.polygon([P(*q) for q in h.coords], fill=VOID)
    for g in obstacles_w:
        d.polygon([P(*q) for q in g.exterior.coords], fill=(90, 60, 50), outline=(0, 0, 0))
    for k, p in consoles.items():
        x, y = P(*p)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 220, 0), outline=(0, 0, 0))
    for p in L.VENTS[v].values():
        x, y = P(*wp(p))
        d.rectangle([x - 6, y - 4, x + 6, y + 4], fill=(160, 120, 230), outline=(0, 0, 0))
    PREVIEW.mkdir(exist_ok=True)
    img.save(PREVIEW / f"preview_{v}.png")


if __name__ == "__main__":
    main(sys.argv[1:])
