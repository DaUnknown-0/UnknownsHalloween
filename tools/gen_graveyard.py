# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_graveyard.py - Ravenhollow Cemetery (Friedhof mit Gruft) im Atlas-Dateiformat (Atlas docs/MAP_FORMAT.md):
# schreibt map.json, Bodenkacheln, Objekt- und Konsolen-Atlanten, Minimap, Logo und Symbol nach Resources/graveyard/.
# GraveyardMap.cs bettet den Ordner ein und laesst Atlas die Datei lesen (AtlasMapFile.Read).
#
#   python tools/gen_graveyard.py                 alles
#   python tools/gen_graveyard.py --fast          Boden mit 40 px/m (schneller Probelauf; endgueltig 128 px/m)
#   danach: python ../UnknownsAtlas/tools/pack_textures.py Resources/graveyard graveyard
#
# Grundriss und Ausstattung: graveyard_layout.py. Grafik: graveyard_floor.py (Boden), graveyard_art.py (Objekte),
# graveyard_consoles.py (Konsolen, Vents, Tueren, Kameras). Fehlt ein Grafikmodul, bleibt dort die Graybox.

import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import Point, LineString, box
from shapely.affinity import translate
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
OUT = PROJECT / "Resources" / "graveyard"
PREVIEW = HERE / "_graveyard"
sys.path.insert(0, str(PROJECT.parent / "UnknownsAtlas" / "tools"))
sys.path.insert(0, str(HERE))
import map_labels  # noqa: E402  (aus Atlas)
import museum_art as A  # noqa: E402  (pack, shape_bounds)
import graveyard_layout as L  # noqa: E402

KEY = "graveyard"
FLOOR_PPM = 128
PROP_PPM = 160
BOUNDS = L.BOUNDS
BX0, BY0, BX1, BY1 = BOUNDS
WALL = L.WALL


def shape_geom(s):
    if s[0] == "rect":
        return box(*s[1:5])
    if s[0] == "circle":
        return Point(s[1], s[2]).buffer(s[3], 12)
    if s[0] == "ellipse":
        from shapely import affinity
        return affinity.scale(Point(s[1], s[2]).buffer(1, 16), s[3], s[4])
    raise ValueError(s)


def opening_rect(inner, side, a, b):
    x0, y0, x1, y1 = inner
    t = WALL
    if side == "N":
        return box(a, y1 - 0.01, b, y1 + t + 0.01)
    if side == "S":
        return box(a, y0 - t - 0.01, b, y0 + 0.01)
    if side == "E":
        return box(x1 - 0.01, a, x1 + t + 0.01, b)
    return box(x0 - t - 0.01, a, x0 + 0.01, b)


def clearing(rect):
    x0, y0, x1, y1 = rect
    return box(x0 + L.CORNER, y0 + L.CORNER, x1 - L.CORNER, y1 - L.CORNER).buffer(L.CORNER, 16)


def build():
    outdoor = [clearing(rect) for _k, _n, _s, rect in L.CLEARINGS]
    for pts in L.PATHS:
        outdoor.append(LineString(pts).buffer(L.PATH_W / 2, 16))
    outdoor = unary_union(outdoor).intersection(box(*BOUNDS))
    shells, inners, openings, doors = [], [], [], []
    for key, _n, _s, inner, dl in L.BUILDINGS:
        x0, y0, x1, y1 = inner
        shells.append(box(x0 - WALL, y0 - WALL, x1 + WALL, y1 + WALL))
        inners.append(box(*inner))
        for side, a, b, kind in dl:
            o = opening_rect(inner, side, a, b)
            openings.append(o)
            doors.append((key, side, a, b, kind, o))
    walk = outdoor.difference(unary_union(shells))
    walk = unary_union([walk] + inners + openings).buffer(0)
    return walk, outdoor, shells, doors


def rooms(walk):
    out = {}
    for key, name, sysname, inner, _d in L.BUILDINGS:
        out[key] = (name, sysname, box(*inner))
    for key, name, sysname, rect in L.CLEARINGS:
        g = clearing(rect).intersection(walk)
        g = g.difference(unary_union([box(*b[3]).buffer(WALL) for b in L.BUILDINGS]))
        if g.geom_type != "Polygon":
            g = max(g.geoms, key=lambda p: p.area)
        out[key] = (name, sysname, g)
    return out


def geom_parts(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


def rings_of(g):
    out = []
    for p in geom_parts(g):
        out.append(list(p.exterior.coords)[:-1])
        for h in p.interiors:
            out.append(list(h.coords)[:-1])
    return out


def obstacles():
    return [shape_geom(L.hit_shape(s, k)) for k, s, m in L.PROPS if m in ("opaque", "glass")]


def place_consoles(walk, rms, doors, obst):
    placed = {}
    free = walk.difference(unary_union(obst).buffer(0.5)).buffer(0)
    edge = walk.boundary
    taken = [Point(p) for p in list(L.FIXED.values()) + [L.EMERGENCY, L.SURVEILLANCE, L.ADMIN_TABLE, L.FREEPLAY, L.SPAWN]]
    taken += [Point(p) for p in L.VENTS.values()] + [Point(p) for p in L.CAMERAS]
    door_pts = [o.centroid for *_r, o in doors]
    for key, (name, sysname, g) in rms.items():
        keys = [k for k in L.SKELD_CONSOLES.get(sysname, []) if k not in L.FIXED]
        cands = []
        for part in geom_parts(g.buffer(-0.55)):
            line = part.exterior
            n = max(16, int(line.length / 0.3))
            for i in range(n):
                p = line.interpolate(i / n, normalized=True)
                if edge.distance(p) > 0.75 or not free.contains(p):
                    continue
                if min([p.distance(q) for q in door_pts] + [99]) < 1.6:
                    continue
                cands.append(p)
        chosen = []
        for k in keys:
            best, score = None, -1e9
            for need in (1.3, 1.0, 0.8):
                for p in cands:
                    dd = min([p.distance(q) for q in chosen + taken] + [99])
                    if dd < need:
                        continue
                    sc = min(dd, 4.0) + 0.1 * (p.y - g.centroid.y)
                    if sc > score:
                        best, score = p, sc
                if best is not None:
                    break
            if best is None:
                best = g.representative_point()
                print(f"WARN no spot for {k} in {name}")
            chosen.append(best)
            placed[k] = (round(best.x, 2), round(best.y, 2))
        taken.extend(chosen)
    placed.update(L.FIXED)
    return placed


def check_reach(walk, rms, doors, obst, consoles):
    """Begehbarkeit pruefen: Spielerkreis (0,3 m) gegen Waende und Hindernisse; alle Raeume, Konsolen und Vents in
    einer Zusammenhangskomponente, kein Hindernis direkt vor einer Tuer."""
    free = walk.buffer(-0.28).difference(unary_union(obst).buffer(0.28)).buffer(0)
    comps = sorted(geom_parts(free), key=lambda g: -g.area)
    main = comps[0]
    bad = 0
    for k, (_n, _s, g) in rms.items():
        if g.intersection(main).area < 1.0:
            print(f"WARN room {k} not reachable")
            bad += 1
    pts = [(k, Point(p)) for k, p in consoles.items()] + [(f"vent {v}", Point(p)) for v, p in L.VENTS.items()]
    pts += [("emergency", Point(L.EMERGENCY)), ("spawn", Point(L.SPAWN))]
    for name, pt in pts:
        if main.distance(pt) > 0.75:
            print(f"WARN not reachable: {name} ({main.distance(pt):.2f} m from the main area)")
            bad += 1
    for key, side, a, b, kind, o in doors:
        through = o.buffer(0.05).intersection(free)
        if through.is_empty or through.area < 0.2:
            print(f"WARN door/gap {key}-{side} blocked")
            bad += 1
    small = [round(g.area, 1) for g in comps[1:] if g.area > 0.5]
    print(f"reach check: {len(comps)} free component(s){' ' + str(small) if small else ''}, {bad} problem(s)")


def P(x, y, s):
    return ((x - BX0) * s, (BY1 - y) * s)


def font(size):
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except OSError:
        return ImageFont.load_default()


# ------------------------------------------------------------------ Kontext fuer die Grafikmodule

class Ctx:
    """Alles, was Boden, Objekte und Konsolen ueber die Karte wissen muessen (Weltmeter)."""

    def __init__(self, walk, outdoor, shells, doors, rms, consoles):
        self.walk, self.outdoor, self.shells, self.doors, self.rooms = walk, outdoor, shells, doors, rms
        self.consoles = consoles
        self.bounds = BOUNDS
        self.layout = L
        self.buildings = {b[0]: b for b in L.BUILDINGS}
        self.clearings = {c[0]: c for c in L.CLEARINGS}

    def room_at(self, x, y):
        pt = Point(x, y)
        best = None
        for key, (_n, _s, g) in self.rooms.items():
            if g.buffer(0.3).contains(pt) and (best is None or g.area < self.rooms[best][2].area):
                best = key
        return best


# ------------------------------------------------------------------ Boden

def render_floor(ctx, ppm):
    img = None
    try:
        import graveyard_floor as GF
        img = GF.render(ctx, ppm)
    except ImportError as e:
        print(f"note: graveyard_floor missing ({e}) - graybox floor")
    if img is None:
        img = graybox_floor(ctx, ppm)
    OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    img.save(PREVIEW / "preview_floor.jpg", quality=88)
    ww, hh = img.size
    for old in OUT.glob(f"{KEY}_floor_*.jpg"):
        old.unlink()
    cols, rows = math.ceil(ww / 1024), math.ceil(hh / 1024)
    tw, th = (ww // cols) // 4 * 4, (hh // rows) // 4 * 4
    tiles, i = [], 0
    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * tw, r * th
            x1 = ww if c == cols - 1 else x0 + tw
            y1 = hh if r == rows - 1 else y0 + th
            w4, h4 = (x1 - x0) // 4 * 4, (y1 - y0) // 4 * 4
            img.crop((x0, y0, x0 + w4, y0 + h4)).save(OUT / f"{KEY}_floor_{i}.jpg", quality=90)
            tiles.append((i, BX0 + x0 / ppm, BY1 - (y0 + h4) / ppm, w4, h4))
            i += 1
    print(f"floor {ww}x{hh} in {len(tiles)} tile(s)")
    return tiles


def graybox_floor(ctx, s):
    ww, hh = int((BX1 - BX0) * s), int((BY1 - BY0) * s)
    img = Image.new("RGB", (ww, hh), (14, 20, 18))
    d = ImageDraw.Draw(img, "RGBA")
    for sh in ctx.shells:
        d.polygon([P(*q, s) for q in sh.exterior.coords], fill=(44, 40, 46))
    for p in geom_parts(ctx.walk):
        d.polygon([P(*q, s) for q in p.exterior.coords], fill=(104, 100, 96))
        for h in p.interiors:
            d.polygon([P(*q, s) for q in h.coords], fill=(14, 20, 18))
    return img


# ------------------------------------------------------------------ Objekte

def graybox_prop(kind, shp):
    print(f"WARN no art for prop '{kind}' - graybox block")
    x0, y0, x1, y1 = A.shape_bounds(shp)
    pad = 0.1
    w, h = max(1, int((x1 - x0 + 2 * pad) * PROP_PPM)), max(1, int((y1 - y0 + 2 * pad + 0.5) * PROP_PPM))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([pad * PROP_PPM, pad * PROP_PPM, w - pad * PROP_PPM, h - pad * PROP_PPM], fill=(150, 150, 150, 255), outline=(20, 20, 26, 255), width=4)
    return im, x0 - pad, y0 - pad, y0


def render_props(ctx):
    """Alle Objekte zeichnen und packen. Rueckgabe: Liste der props[]-Eintraege (map.json)."""
    try:
        import graveyard_art as GA
    except ImportError as e:
        print(f"note: graveyard_art missing ({e}) - no props")
        return [], {}
    images, meta = [], []
    variants = {}
    for i, (kind, shp, _mode) in enumerate(L.PROPS):
        if kind in GA._KIND_FN:
            im, wx, wy, base = GA.draw(kind, shp, i, PROP_PPM, ctx=ctx)
        else:
            im, wx, wy, base = graybox_prop(kind, shp)
        images.append((i, im))
        fx0, _, fx1, _ = A.shape_bounds(shp)
        meta.append((kind, wx, wy, base, fx0, fx1))
        for var in GA.VARIANTS.get(kind, ()):
            im2, wx2, wy2, _b = GA.draw(kind, shp, i, PROP_PPM, ctx=ctx, variant=var)
            if im2.size != im.size:
                print(f"WARN variant {kind}/{var}: size differs")
            variants[f"Prop/{kind}/{wx:.3f}/{wy:.3f}/{var}"] = (im2, (wx - wx2) * PROP_PPM, (wy - wy2) * PROP_PPM)
    atlases, placed = A.pack(images, max_w=2048, max_h=2048)
    for old in OUT.glob(f"{KEY}_props_*.png"):
        old.unlink()
    for k, atlas in enumerate(atlases):
        atlas.save(OUT / f"{KEY}_props_{k}.png", optimize=True)
    out = []
    for i in range(len(images)):
        kind, wx, wy, base, fx0, fx1 = meta[i]
        page, x, y, ww, hh = placed[i]
        out.append({"kind": kind, "atlas": page, "x": x, "y": atlases[page].height - y - hh, "w": ww, "h": hh,
                    "worldX": round(wx, 4), "worldY": round(wy, 4), "baseY": round(base, 4),
                    "footX0": round(fx0, 4), "footX1": round(fx1, 4)})
    print(f"props {len(out)} in {len(atlases)} atlas(es)")
    return out, variants


# ------------------------------------------------------------------ Konsolen, Vents, Tueren, Kameras

def render_consoles(ctx, door_slots, prop_variants):
    try:
        import graveyard_consoles as GC
    except ImportError as e:
        print(f"note: graveyard_consoles missing ({e}) - Skeld console images stay")
        return []
    sprites = GC.render_all(ctx, PROP_PPM, door_slots)       # {key: (img, ax, ay)} ax/ay = Anker px (links, unten)
    sprites.update(prop_variants)
    names, by_content = {}, {}
    for key in sorted(sprites):
        img, ax, ay = sprites[key]
        h = (img.size, round(ax, 2), round(ay, 2), hashlib.md5(img.tobytes()).hexdigest())
        by_content.setdefault(h, []).append(key)
    uniq = list(by_content.items())
    images = []
    for i, (h, keys) in enumerate(uniq):
        img, ax, ay = sprites[keys[0]]
        if not keys[0].startswith("Prop/"):
            img = img.filter(ImageFilter.GaussianBlur(0.4))
        images.append((i, img))
    atlases, placed = A.pack(images, max_w=2048, max_h=2048)
    for old in OUT.glob(f"{KEY}_consoles_*.png"):
        old.unlink()
    for k, atlas in enumerate(atlases):
        atlas.save(OUT / f"{KEY}_consoles_{k}.png", optimize=True)
    out = []
    for i, (h, keys) in enumerate(uniq):
        page, x, y, w, hh = placed[i]
        _img, ax, ay = sprites[keys[0]]
        for key in keys:
            out.append({"key": key, "atlas": page, "x": x, "y": atlases[page].height - y - hh, "w": w, "h": hh,
                        "pivotX": round(ax / w, 4), "pivotY": round(ay / hh, 4)})
    out.sort(key=lambda e: e["key"])
    print(f"console sprites {len(out)} ({len(uniq)} unique) in {len(atlases)} atlas(es)")
    return out


# ------------------------------------------------------------------ Minimap, Logo, Symbol

MAP_LABELS = []


def minimap(ctx):
    try:
        import graveyard_minimap as GM
        img = GM.render(ctx, MAP_LABELS)
        img.save(OUT / f"{KEY}_minimap.png", optimize=True)
        return
    except ImportError:
        pass
    s = 24
    ww, hh = int((BX1 - BX0) * s), int((BY1 - BY0) * s)
    img = Image.new("RGBA", (ww, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    Pt = lambda x, y: ((x - BX0) * s, (BY1 - y) * s)
    for p in geom_parts(ctx.walk):
        d.polygon([Pt(*q) for q in p.exterior.coords], fill=(214, 224, 214, 235))
        for h in p.interiors:
            d.polygon([Pt(*q) for q in h.coords], fill=(0, 0, 0, 0))
    for p in geom_parts(ctx.walk):
        for ring in [p.exterior] + list(p.interiors):
            d.line([Pt(*q) for q in ring.coords], fill=(26, 30, 28, 255), width=4, joint="curve")
    f = font(16)
    MAP_LABELS.clear()
    for key, (name, _s, g) in ctx.rooms.items():
        c = g.representative_point()
        map_labels.place(d, f, name, c.x, c.y, g.buffer(-0.2), s, Pt, (26, 30, 28, 255), MAP_LABELS)
    img.save(OUT / f"{KEY}_minimap.png", optimize=True)


def button_and_icon():
    try:
        import graveyard_brand as GB
        GB.render(OUT, KEY, PREVIEW)
        return
    except ImportError:
        pass
    b = Image.new("RGBA", (1000, 250), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.rounded_rectangle([10, 30, 990, 220], 40, fill=(20, 26, 24, 235), outline=(150, 170, 150), width=8)
    d.text((500, 125), "RAVENHOLLOW", font=font(110), fill=(200, 220, 196), anchor="mm")
    b.save(OUT / f"button_{KEY}.png", optimize=True)
    i = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(i)
    d.ellipse([8, 8, 248, 248], fill=(20, 26, 24, 255), outline=(150, 170, 150), width=8)
    i.save(OUT / f"icon_{KEY}.png", optimize=True)


# ------------------------------------------------------------------ map.json

def v2(p):
    return [round(p[0], 4), round(p[1], 4)]


def door_group(key):
    return next(b[2] for b in L.BUILDINGS if b[0] == key)


def door_slots(doors):
    vert, hori = [], []
    for key, side, a0, b0, kind, o in doors:
        if kind != "door":
            continue
        c = o.centroid
        slot = {"label": f"{key}-{side}", "x": round(c.x, 3), "y": round(c.y, 3), "length": round(b0 - a0, 2),
                "group": door_group(key), "seeThrough": False}
        (vert if side in "EW" else hori).append(slot)
    return vert, hori


def emit(ctx, tiles, ppm, props, console_sprites, extra):
    walk, rms, consoles = ctx.walk, ctx.rooms, ctx.consoles
    full = box(BX0 - 5, BY0 - 5, BX1 + 5, BY1 + 5)
    solid = full.difference(walk)
    move = walk.difference(translate(solid, 0, -0.3)).buffer(0)
    # Sicht-/Lichtkanten nur an Gebaeuden und am Kartenrand; Grabfelder und Hecken draussen sperren nur den Weg
    # (User 24.10.: "Bei Waenden, die draussen sind, nur Kollision, keine Lichtblockade")
    open_air = box(BX0, BY0, BX1, BY1).difference(unary_union(ctx.shells))
    shadow = unary_union([open_air, walk, translate(walk, 0, 0.45)]).buffer(0)
    opaque = [shape_geom(L.hit_shape(s, k)) for k, s, m in L.PROPS if m == "opaque"]
    glass = [shape_geom(L.hit_shape(s, k)) for k, s, m in L.PROPS if m == "glass"]
    edges = unary_union([LineString(r + [r[0]]) for r in rings_of(walk)])
    room_u = unary_union([g for _n, _s, g in rms.values()])
    halls = [g for g in geom_parts(walk.difference(room_u).buffer(0)) if g.area > 1.0]
    vert, hori = door_slots(ctx.doors)
    buttons = {}
    for key, (name, sysname, g) in rms.items():
        if sysname in ("Cafeteria", "Storage", "UpperEngine", "LowerEngine", "Security", "MedBay",
                       "Electrical", "Reactor", "LifeSupp", "Comms") and sysname not in buttons:
            c = g.representative_point()
            buttons[sysname] = v2((c.x, c.y + 0.8))
    data = {
        "format": 1, "key": KEY, "displayName": "Ravenhollow Cemetery", "resourcePrefix": KEY, "builtInEffects": False,
        "minX": BX0, "minY": BY0, "maxX": BX1, "maxY": BY1,
        "walls": [[v2(q) for q in r] for r in rings_of(move)],
        "shadowWalls": [[v2(q) for q in r] for r in rings_of(shadow)],
        "opaque": [[v2(q) for q in list(p.exterior.coords)[:-1]] for p in opaque],
        "opaqueCastsShadow": [p.distance(edges) > 0.08 for p in opaque],
        "glass": [[v2(q) for q in list(p.exterior.coords)[:-1]] for p in glass],
        "hallways": [[v2(q) for q in list(h.exterior.coords)[:-1]] for h in halls],
        "rooms": [{"key": k, "name": n, "room": s_, "area": [v2(q) for q in list(g.exterior.coords)[:-1]]}
                  for k, (n, s_, g) in rms.items()],
        "floorPixelsPerMeter": ppm,
        "floorTiles": [{"index": i, "x": round(wx, 4), "y": round(wy, 4), "w": w, "h": h} for i, wx, wy, w, h in tiles],
        "propPixelsPerMeter": PROP_PPM, "props": props, "consoleSprites": console_sprites,
        "noFadeKinds": extra.get("noFadeKinds", []),
        "consoles": {k: v2(p) for k, p in sorted(consoles.items())},
        "emergencyButton": v2(L.EMERGENCY), "surveillanceConsole": v2(L.SURVEILLANCE), "adminTable": v2(L.ADMIN_TABLE),
        "freeplayLaptop": v2(L.FREEPLAY), "spawn": v2(L.SPAWN), "spawnRadius": L.SPAWN_RADIUS,
        "vents": {str(k): v2(p) for k, p in L.VENTS.items()},
        "ventNetworks": L.VENT_NETS, "ventBridges": L.VENT_BRIDGES,
        "verticalDoors": vert, "horizontalDoors": hori,
        "cameras": [v2(p) for p in L.CAMERAS], "cameraViews": {},
        "mapButtons": buttons,
        "mapLabels": [{"x": round(x, 3), "y": round(y, 3), "halfW": round(hw, 3), "halfH": round(hh, 3)} for x, y, hw, hh in MAP_LABELS],
        "cameraColor": [0.05, 0.07, 0.08],
        "minLight": 1.0, "maxLight": 5.0,
        "viewSpots": [v2(L.SPAWN), v2((3.0, 13.0)), v2((-18.0, 10.2)), v2((18.0, 13.0)), v2((19.0, -14.5))],
        "taskNames": L.TASK_NAMES,
        "customTasks": extra.get("customTasks", {}), "taskArt": extra.get("taskArt", {}), "taskText": extra.get("taskText", {}),
    }
    (OUT / "map.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"map.json: rooms {len(rms)}, doors {len(vert)}V/{len(hori)}H, consoles {len(consoles)}, vents {len(L.VENTS)}, "
          f"hallways {len(halls)}, props {len(props)}, sprites {len(console_sprites)}")


def preview(ctx):
    s = 40
    im = Image.open(PREVIEW / "preview_floor.jpg").convert("RGB")
    im = im.resize((int((BX1 - BX0) * s), int((BY1 - BY0) * s)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for _k, shp, m in L.PROPS:
        g = shape_geom(shp)
        d.polygon([P(*q, s) for q in g.exterior.coords], outline=(255, 80, 80) if m == "opaque" else (80, 200, 255))
    for k, p in ctx.consoles.items():
        x, y = P(*p, s)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 230, 0), outline=(0, 0, 0))
    for v, p in L.VENTS.items():
        x, y = P(*p, s)
        d.rectangle([x - 8, y - 5, x + 8, y + 5], fill=(60, 200, 90), outline=(0, 0, 0))
        d.text((x, y), str(v), fill=(0, 0, 0), anchor="mm", font=font(10))
    for p in L.CAMERAS:
        x, y = P(*p, s)
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(220, 60, 60), outline=(0, 0, 0))
    for key, side, a0, b0, kind, o in ctx.doors:
        if kind == "door":
            d.polygon([P(*q, s) for q in o.exterior.coords], outline=(60, 120, 255), width=3)
    im.save(PREVIEW / "preview.png")
    print(PREVIEW / "preview.png", im.size)


def main(argv):
    ppm = 40 if "--fast" in argv else FLOOR_PPM
    walk, outdoor, shells, doors = build()
    rms = rooms(walk)
    obst = obstacles()
    consoles = place_consoles(walk, rms, doors, obst)
    free = walk.difference(unary_union(obst).buffer(0.25))
    for k, p in list(consoles.items()) + [("Emergency", L.EMERGENCY), ("Surveillance", L.SURVEILLANCE), ("Admin", L.ADMIN_TABLE),
                                          ("Freeplay", L.FREEPLAY)] + [(f"Vent{v}", p) for v, p in L.VENTS.items()] + \
                                         [(f"Cam{i}", p) for i, p in enumerate(L.CAMERAS)]:
        dd = free.distance(Point(p))
        if dd > 0.6:
            print(f"WARN {k} at {p} not reachable ({dd:.2f} m)")
    check_reach(walk, rms, doors, obst, consoles)
    ctx = Ctx(walk, outdoor, shells, doors, rms, consoles)
    (PREVIEW).mkdir(exist_ok=True)
    (PREVIEW / "consoles.json").write_text(json.dumps({k: list(v) for k, v in consoles.items()}, indent=1), encoding="utf-8")
    only = [a for a in argv if a.startswith("--only=")]
    only = set(only[0][7:].split(",")) if only else None
    tiles = render_floor(ctx, ppm) if not only or "floor" in only else json.loads((PREVIEW / "tiles.json").read_text())
    (PREVIEW / "tiles.json").write_text(json.dumps(tiles))
    props, variants = render_props(ctx)
    vert, hori = door_slots(doors)
    sprites = render_consoles(ctx, vert + hori, variants)
    minimap(ctx)
    button_and_icon()
    extra = {}
    try:
        import graveyard_tasks as GT
        extra = GT.map_extra(OUT)
    except ImportError:
        pass
    emit(ctx, tiles, ppm, props, sprites, extra)
    preview(ctx)


if __name__ == "__main__":
    main(sys.argv[1:])
