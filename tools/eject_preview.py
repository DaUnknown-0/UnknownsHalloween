# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# eject_preview.py - Bilderbogen einer Rauswurf-Szene ohne Spielstart: spielt die Szenen-JSON mit derselben
# Auswertung wie EjectEngine.cs ab (Keyframes mit Easing und Bogen, Wobble, Flicker, Eltern inkl. "player",
# Kamera mit Grenzen, Reihenfolge nach z, Partikel deterministisch simuliert) und legt Einzelbilder nebeneinander.
# Der Spieler ist eine Platzhalter-Crewfigur (1 Einheit hoch, wie die Engine ihn normiert).
#
#   python tools/eject_preview.py <szenen.json> <out.png> [scene_id ...] [--frames 8] [--w 660]

import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SEARCH = [HERE.parent / "Resources" / "villa", HERE.parent / "Resources" / "graveyard_eject"]
PPU = 180.0
VIEW_W, VIEW_H = 11.0, 6.2
_cache = {}


def sprite(name):
    if name not in _cache:
        for d in SEARCH:
            p = d / name
            if p.exists():
                _cache[name] = Image.open(p).convert("RGBA")
                break
        else:
            print("WARN missing sprite", name)
            _cache[name] = Image.new("RGBA", (8, 8), (255, 0, 255, 255))
    return _cache[name]


def ease(e, u):
    if e == "lin":
        return u
    if e == "in":
        return u * u
    if e == "out":
        return 1 - (1 - u) * (1 - u)
    if e == "back":
        c = 1.70158; v = u - 1
        return 1 + v * v * ((c + 1) * v + c)
    if e == "inback":
        c = 1.70158
        return u * u * ((c + 1) * u - c)
    if e == "hold":
        return 0.0 if u < 1 else 1.0
    return u * u * (3 - 2 * u)


def tracks_of(keys):
    tr = {}
    for k in keys or []:
        t, props = k[0], k[1]
        e = k[2] if len(k) > 2 else "io"
        arc = props.get("arc", 0.0)
        for name, v in props.items():
            if name == "arc":
                continue
            tr.setdefault(name, []).append((t, v, e, arc if name == "y" else 0.0))
    for name in tr:
        tr[name].sort(key=lambda x: x[0])
    return tr


def sample(tr, t, default):
    if not tr:
        return default
    if t <= tr[0][0]:
        return tr[0][1]
    for i in range(1, len(tr)):
        tn, vn, en, arc = tr[i]
        if t < tn:
            tp, vp = tr[i - 1][0], tr[i - 1][1]
            u = (t - tp) / max(1e-6, tn - tp)
            if en == "hold":
                return vp
            v = vp + (vn - vp) * ease(en, u)
            if arc:
                v += arc * 4 * u * (1 - u)
            return v
    return tr[-1][1]


def env(t, t0, t1):
    if t0 is None:
        return 1.0
    if t < t0 or t > t1:
        return 0.0
    return min(1.0, (t - t0) / 0.12) * min(1.0, (t1 - t) / 0.12)


def flick(f, t):
    if not f:
        return 1.0
    e = env(t, f.get("t0"), f.get("t1"))
    if e <= 0:
        return 1.0
    w = 2 * math.pi * f["f"]
    n = 0.5 + 0.5 * (0.5 * math.sin(w * t) + 0.3 * math.sin(w * 1.73 * t + 1.3) + 0.2 * math.sin(w * 2.71 * t + 2.1))
    return 1 - f["amp"] * n * e


def local(o, tr, t):
    def g(p, d):
        return sample(tr.get(p), t, o.get(p, d))
    L = {"x": g("x", 0), "y": g("y", 0), "rot": g("rot", 0), "sx": g("sx", 1), "sy": g("sy", 1), "s": g("s", 1),
         "a": g("a", 1), "b": g("b", 1), "flip": g("flip", 1)}
    for w in o.get("wobble", []):
        e = env(t, w.get("t0"), w.get("t1"))
        if e > 0 and w["p"] in L:
            L[w["p"]] += w["amp"] * math.sin(2 * math.pi * w["f"] * t + w.get("ph", 0)) * e
    fl = -1 if L["flip"] < 0 else 1
    return {"X": L["x"], "Y": L["y"], "Rot": L["rot"], "Sx": L["s"] * L["sx"] * fl, "Sy": L["s"] * L["sy"],
            "A": L["a"] * flick(o.get("flicker"), t), "B": L["b"]}


def compose(W, P):
    if P is None:
        return W
    r = math.radians(P["Rot"])
    lx, ly = W["X"] * P["Sx"], W["Y"] * P["Sy"]
    sign = 1 if P["Sx"] * P["Sy"] >= 0 else -1
    return {"X": P["X"] + lx * math.cos(r) - ly * math.sin(r), "Y": P["Y"] + lx * math.sin(r) + ly * math.cos(r),
            "Rot": P["Rot"] + W["Rot"] * sign, "Sx": W["Sx"] * P["Sx"], "Sy": W["Sy"] * P["Sy"], "A": W["A"] * P["A"], "B": W["B"]}


def hexcol(h):
    if not h:
        return (255, 255, 255)
    n = int(h[1:], 16)
    return (n >> 16 & 255, n >> 8 & 255, n & 255)


def crewmate():
    """Platzhalter: Crewmate in Rot, Koerperhoehe = 180 px (1 Einheit), Mitte = Koerpermitte."""
    im = Image.new("RGBA", (150, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 70, 38, 150], 12, fill=(150, 20, 30, 255), outline=(10, 10, 14, 255), width=6)
    d.rounded_rectangle([28, 6, 132, 176], 46, fill=(200, 30, 40, 255), outline=(10, 10, 14, 255), width=7)
    d.rounded_rectangle([62, 34, 142, 84], 24, fill=(140, 200, 230, 255), outline=(10, 10, 14, 255), width=6)
    return im


class Sim:
    def __init__(self, scene, seed=7):
        self.sc = scene
        self.rng = random.Random(seed)
        self.parts = []
        self.acc = [0.0] * len(scene["emitters"])
        self.t = 0.0

    def step_to(self, t1, dt=1 / 30):
        while self.t < t1 - 1e-9:
            t0 = self.t
            t = min(t1, t0 + dt)
            d = t - t0
            for i, em in enumerate(self.sc["emitters"]):
                if "burst" in em:
                    if t0 <= em["burst"] < t:
                        for _ in range(em.get("n", 1)):
                            self.spawn(em)
                    continue
                if em.get("t0", 0) <= t0 < em.get("t1", 0):
                    self.acc[i] += em.get("rate", 0) * d
                    while self.acc[i] >= 1:
                        self.acc[i] -= 1
                        self.spawn(em)
            for p in list(self.parts):
                em = p["em"]
                acc = em.get("acc", [0, 0]); drag = em.get("drag", 0)
                p["vx"] += acc[0] * d; p["vy"] += acc[1] * d
                k = max(0, 1 - drag * d); p["vx"] *= k; p["vy"] *= k
                p["x"] += p["vx"] * d; p["y"] += p["vy"] * d; p["rot"] += p["spin"] * d
                p["scale"] *= max(0, 1 + em.get("grow", 0) * d); p["age"] += d
                if p["age"] >= p["life"]:
                    self.parts.remove(p)
            self.t = t

    def spawn(self, em):
        R = lambda a, b: a + (b - a) * self.rng.random()
        ar, ve = em.get("area", [0, 0, 0, 0]), em.get("vel", [0, 0, 0, 0])
        self.parts.append({"em": em, "x": R(ar[0], ar[2]), "y": R(ar[1], ar[3]), "vx": R(ve[0], ve[2]), "vy": R(ve[1], ve[3]),
                           "life": R(*em.get("life", [1, 1])), "age": 0.0, "sz": R(*em.get("size", [0.2, 0.2])), "scale": 1.0,
                           "rot": R(*em.get("rot", [0, 0])), "spin": R(*em.get("spin", [0, 0]))})


def paste(canvas, im, x, y, rot, sx, sy, a, tint, b, pivot, scale):
    """im (180 px/Einheit) bei Welt (x, y) [px auf canvas], Pivot in Bildanteilen (unten links = 0,0)."""
    w, h = im.size
    tw, th = max(1, int(abs(w * sx * scale))), max(1, int(abs(h * sy * scale)))
    if tw > 6000 or th > 6000:
        return
    img = im.resize((tw, th), Image.BILINEAR)
    if sx < 0:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if sy < 0:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    if tint != (255, 255, 255) or b != 1:
        r, g, bl, al = img.split()
        r = r.point(lambda v: int(v * tint[0] / 255 * b)); g = g.point(lambda v: int(v * tint[1] / 255 * b)); bl = bl.point(lambda v: int(v * tint[2] / 255 * b))
        img = Image.merge("RGBA", (r, g, bl, al))
    if a < 1:
        img.putalpha(img.getchannel("A").point(lambda v: int(v * max(0, a))))
    px_, py_ = pivot[0] if sx >= 0 else 1 - pivot[0], pivot[1] if sy >= 0 else 1 - pivot[1]
    big = Image.new("RGBA", (tw * 3, th * 3), (0, 0, 0, 0))
    big.paste(img, (tw, th))
    cxp, cyp = tw + px_ * tw, th + (1 - py_) * th
    big = big.rotate(rot, center=(cxp, cyp), resample=Image.BILINEAR)
    canvas.alpha_composite(big, (int(round(x - cxp)), int(round(y - cyp))))


def render(scene, t, sim, W=660):
    H = int(W * VIEW_H / VIEW_W)
    s_unit = W / VIEW_W                            # px pro Einheit bei Zoom 1
    cam = tracks_of(scene.get("camera"))
    z = sample(cam.get("z"), t, 1); cx = sample(cam.get("x"), t, 0); cy = sample(cam.get("y"), t, 0)
    bw, bh = scene.get("bounds", [12, 6.8])
    hx, hy = max(0, bw / 2 - VIEW_W / 2 / z), max(0, bh / 2 - VIEW_H / 2 / z)
    cx, cy = max(-hx, min(hx, cx)), max(-hy, min(hy, cy))
    k = s_unit * z
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    P = lambda X, Y: (W / 2 + (X - cx) * k, H / 2 - (Y - cy) * k)
    scale = k / PPU
    objs = scene["objects"]
    trs = {o["id"]: tracks_of(o.get("keys")) for o in objs}
    pl = scene.get("player", {})
    ptr = tracks_of(pl.get("keys"))
    m = {}
    layers = []
    for i, o in enumerate(objs):
        if o.get("parent") == "player":
            continue
        Wl = compose(local(o, trs[o["id"]], t), m.get(o.get("parent")))
        depth = o.get("depth", 1)
        if not o.get("screen") and o.get("parent") is None and depth != 1:
            Wl["X"] += cx * (1 - depth); Wl["Y"] += cy * (1 - depth)
        m[o["id"]] = Wl
        layers.append((o.get("z", 0), i, o, Wl))
    PW = compose(local(pl, ptr, t), m.get(pl.get("parent")))
    hidden = scene.get("skip") or ("hide" in pl and t >= pl["hide"])
    m["player"] = PW
    for i, o in enumerate(objs):
        if o.get("parent") == "player":
            Wl = compose(local(o, trs[o["id"]], t), PW)
            m[o["id"]] = Wl
            layers.append((o.get("z", 0), i, o, Wl))
    items = [(z_ if z_ < 0 else z_ + 0.5, i, "obj", o, Wl) for z_, i, o, Wl in layers]
    if not hidden:
        items.append((0, -1, "player", None, PW))
    for p in sim.parts:
        items.append((p["em"]["z"] if p["em"]["z"] < 0 else p["em"]["z"] + 0.5, 10000, "part", p, None))
    items.sort(key=lambda it: (it[0], it[1]))
    for _z, _i, kind, o, Wl in items:
        if kind == "obj":
            if not o.get("sprite") or Wl["A"] <= 0.003:
                continue
            im = sprite(o["sprite"])
            if o.get("screen"):
                x, y = W / 2 + Wl["X"] * s_unit, H / 2 - Wl["Y"] * s_unit
                paste(canvas, im, x, y, Wl["Rot"], Wl["Sx"], Wl["Sy"], min(1, Wl["A"]), hexcol(o.get("tint")), Wl["B"], o.get("pivot", [0.5, 0.5]), s_unit / PPU)
            else:
                x, y = P(Wl["X"], Wl["Y"])
                paste(canvas, im, x, y, Wl["Rot"], Wl["Sx"], Wl["Sy"], min(1, Wl["A"]), hexcol(o.get("tint")), Wl["B"], o.get("pivot", [0.5, 0.5]), scale)
        elif kind == "player":
            if Wl["A"] <= 0.003:
                continue
            x, y = P(Wl["X"], Wl["Y"])
            paste(canvas, PLAYER, x, y, Wl["Rot"], Wl["Sx"], Wl["Sy"], min(1, Wl["A"]), (255, 255, 255), 1, (0.5, 0.5), scale)
        else:
            p = o
            em = p["em"]
            u = p["age"] / p["life"]
            fade = em.get("fade", [0.15, 0.35])
            a = em.get("a", 1) * min(1, min(u / max(1e-3, fade[0]), (1 - u) / max(1e-3, fade[1])))
            im = sprite(em["sprite"])
            kk = p["sz"] / max(im.width / PPU, im.height / PPU) * p["scale"]
            rot = p["rot"]
            if em.get("stretch") and (p["vx"] or p["vy"]):
                rot = math.degrees(math.atan2(p["vx"], -p["vy"]))
            x, y = P(p["x"], p["y"])
            paste(canvas, im, x, y, rot, kk, kk, max(0, a), hexcol(em.get("tint")), 1, (0.5, 0.5), scale)
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W, int(H * 0.8 / VIEW_H * 0.6)], fill=(0, 0, 0, 255))      # Kinobalken (ungefaehr)
    d.rectangle([0, H - int(H * 0.55 / VIEW_H * 0.6), W, H], fill=(0, 0, 0, 255))
    d.text((6, H - 14), f"{scene['id']} t={t:.2f}", fill=(255, 255, 255, 200))
    return canvas


PLAYER = crewmate()


def sheet(doc, out, ids=None, frames=8, W=660, at=None):
    scenes = [s for s in doc["scenes"] if not ids or s["id"] in ids]
    H = int(W * VIEW_H / VIEW_W)
    cols = 4
    if at:
        frames = len(at)
    rows_per = math.ceil(frames / cols)
    img = Image.new("RGB", (cols * W, len(scenes) * rows_per * H), (20, 20, 20))
    for si, sc in enumerate(scenes):
        sim = Sim(sc)
        times = at or [sc["length"] * (k + 0.5) / frames for k in range(frames)]
        for k, t in enumerate(times):
            sim.step_to(t)
            fr = render(sc, t, sim, W)
            if at:
                ImageDraw.Draw(fr).text((6, 4), f"{t:.2f}s", fill=(255, 255, 0))
            img.paste(fr.convert("RGB"), ((k % cols) * W, (si * rows_per + k // cols) * H))
    img.save(out, quality=88)
    print(out, img.size)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    frames = 8
    W = 660
    at = None
    for a in sys.argv[1:]:
        if a.startswith("--frames="):
            frames = int(a.split("=")[1])
        if a.startswith("--w="):
            W = int(a.split("=")[1])
        if a.startswith("--at="):
            at = [float(v) for v in a.split("=")[1].split(",")]
    doc = json.load(open(args[0], encoding="utf-8"))
    sheet(doc, args[1], args[2:] or None, frames, W, at)
