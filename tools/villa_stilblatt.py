# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_stilblatt.py - Abnahmebilder fuer den Look von Hollowmere Manor (Spukvilla als Horrorfilm-Set).
#
#   python villa_stilblatt.py      erzeugt in _villa_stilblatt/:
#     stilblatt_objekte.png      alle Objektarten auf Parkett, Crewmate als Massstab, beschriftet
#     stilblatt_materialien.png  alle Materialkacheln (2 x 2 m), die Teppichkante, alle Wandstile, Bodendetails
#     szene_halle.png            12 x 7 m Eingangshalle (Parkett, Tapetenwand, Standuhr, Dolly, Kamera, Licht)
#     szene_friedhof.png         12 x 7 m Friedhof (Erde, Hecke, Zaun, Grabsteine, Steinsarg, Laterne)
#
# Alles bei 160 px/m; Weltkoordinaten in Metern, y nach oben (Norden). Zusammensetzen wie im Spiel:
# Boden, Bodendetails, Wandstirnseiten, dann Objekte nach Standlinie sortiert (Norden zuerst).

import math
import os
import sys
import time

ATLAS_TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UnknownsAtlas", "tools"))
sys.path.insert(0, ATLAS_TOOLS)

from PIL import Image, ImageDraw, ImageFilter, ImageFont   # noqa: E402

import handdraw as HD                       # noqa: E402
import villa_art as VA                      # noqa: E402
import villa_floor as VF                    # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_villa_stilblatt")
PPM = 160
BG = (22, 18, 26)
WALL_TOP = (44, 34, 44)
WALL_RIM = (78, 62, 80)

# typische Grundflaechen der Objektarten (Ursprung unten links), idx fuer das Stilblatt
OBJECTS = [
    ("standuhr", ("rect", 0, 0, 0.7, 0.45), 0),
    ("seance_tisch", ("ellipse", 1.0, 0.6, 1.0, 0.6), 0),
    ("buecherregal", ("rect", 0, 0, 2.4, 0.45), 0),
    ("kamin", ("rect", 0, 0, 2.2, 0.6), 0),
    ("kandelaber", ("rect", 0, 0, 0.45, 0.45), 0),
    ("kandelaber_aus", ("rect", 0, 0, 0.45, 0.45), 1),
    ("filmkamera", ("rect", 0, 0, 1.0, 0.7), 0),
    ("scheinwerfer", ("rect", 0, 0, 0.7, 0.7), 0),
    ("schminktisch", ("rect", 0, 0, 1.6, 0.5), 1),
    ("sessel", ("rect", 0, 0, 0.9, 0.8), 0),
    ("sessel", ("rect", 0, 0, 0.9, 0.8), 3),
    ("sarg", ("rect", 0, 0, 2.0, 0.7), 2),
    ("sarg", ("rect", 0, 0, 2.0, 0.7), 3),
    ("grabstein", ("rect", 0, 0, 0.8, 0.3), 0),
    ("grabstein", ("rect", 0, 0, 0.8, 0.3), 1),
    ("grabstein", ("rect", 0, 0, 0.8, 0.3), 2),
    ("grabstein", ("rect", 0, 0, 0.8, 0.3), 3),
    ("aggregat", ("rect", 0, 0, 3.0, 1.6), 0),
    ("absperrung", ("rect", 0, 0, 2.0, 0.3), 0),
    ("absperrung", ("rect", 0, 0, 2.0, 0.3), 1),
]


def font(size):
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(d, x, y, text, size=20, col=(240, 236, 228), anchor="la"):
    f = font(size)
    d.text((x + 2, y + 2), text, font=f, fill=(0, 0, 0, 200), anchor=anchor)
    d.text((x, y), text, font=f, fill=col, anchor=anchor)


def tile_fill(img, tile, x0, y0, x1, y1):
    """Rechteck (Pixel) mit einer Kachel fuellen, am Bildraster ausgerichtet."""
    tw, th = tile.size
    region = Image.new("RGB", (x1 - x0, y1 - y0))
    for yy in range(-(y0 % th), y1 - y0 + th, th):
        for xx in range(-(x0 % tw), x1 - x0 + tw, tw):
            region.paste(tile, (xx, yy))
    img.paste(region, (x0, y0))


def sprite_box(sprite, ppm):
    """(Bild, wx, wy, base) -> auf den sichtbaren Bereich beschnittenes Bild und Pixelversatz der
    Standlinie von dessen Oberkante (nur fuer das Blatt; die Szenen nutzen die vollen Sprites)."""
    img, wx, wy, base = sprite
    top = wy + img.height / ppm
    base_px = int(round((top - base) * ppm))
    bb = img.getbbox() or (0, 0, img.width, img.height)
    return img.crop(bb), base_px - bb[1], wx


# ------------------------------------------------------------------ Blatt 1: Objekte

def sheet_objects():
    sprites = [(k, i, sprite_box(VA.draw(k, s, i, PPM), PPM)) for k, s, i in OBJECTS]
    crew, cw, ch = HD.crewmate(PPM)
    gap = 36
    margin = 40
    max_w = 1900
    rows, widths = [[]], [crew.width + gap]
    for k, i, (img, base_px, wx) in sprites:
        if widths[-1] + img.width + gap > max_w and rows[-1]:
            rows.append([])
            widths.append(crew.width + gap)
        rows[-1].append((k, i, img, base_px))
        widths[-1] += img.width + gap
    W = max(widths) + 2 * margin
    # b = Pixel ueber der Standlinie (Objekthoehe), img.height - b = Pixel darunter (Schatten, Lichtlache)
    row_top = [max(b for _, _, _, b in row) + 40 for row in rows]
    row_h = [max(img.height - b for _, _, img, b in row) + 60 for row in rows]
    H = margin + sum(row_top[r] + row_h[r] for r in range(len(rows))) + margin
    out = Image.new("RGB", (W, H), BG)
    tile_fill(out, VF.material_tile("parkett", PPM, 1), 0, 0, W, H)
    out = out.convert("RGBA")
    d = ImageDraw.Draw(out, "RGBA")
    y = margin
    for r, row in enumerate(rows):
        base_y = y + row_top[r]
        x = margin
        HD.paste_clipped(out, crew, x, base_y - crew.height)
        label(d, x + crew.width // 2, base_y + 12, "Crewmate", 16, anchor="ma")
        x += crew.width + gap
        for k, i, img, b in row:
            HD.paste_clipped(out, img, x, base_y - b)
            label(d, x + img.width // 2, base_y + 12, f"{k} #{i}", 16, anchor="ma")
            x += img.width + gap
        d.line([(margin, base_y), (W - margin, base_y)], fill=(255, 255, 255, 40), width=1)
        y = base_y + row_h[r]
    d = ImageDraw.Draw(out, "RGBA")
    label(d, margin, 8, "Hollowmere Manor: Objekte (160 px/m, K = 0,55, Standlinie = Kollision)", 22)
    out.convert("RGB").save(os.path.join(OUT, "stilblatt_objekte.png"))


# ------------------------------------------------------------------ Blatt 2: Materialien und Waende

def sheet_materials():
    gap, margin = 32, 40
    tiles = [(m, VF.material_tile(m, PPM, 1)) for m in VF.MATERIALS]
    tw = int(VF.TILE_M * PPM)
    cols = 5
    walls_w, walls_h = 2.6, 1.65                              # 3,0 m Wand * K
    walls = [(s, VF.wall_front(walls_w, walls_h, s, PPM, 2)) for s in VF.WALL_STYLES]
    ww = int(walls_w * PPM)
    W = max(cols * (tw + gap), len(walls) * (ww + gap)) + 2 * margin
    rows_t = math.ceil(len(tiles) / cols)
    kante_h = int(0.3 * PPM)
    details_h = int(2.2 * PPM)
    H = margin + 40 + rows_t * (tw + 40 + gap) + kante_h + 60 + int(walls_h * PPM) + 90 + details_h + 60 + margin
    out = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(out, "RGBA")
    label(d, margin, 8, "Hollowmere Manor: Materialkacheln (2 x 2 m, nahtlos), Teppichkante, Wandstirnseiten, Bodendetails", 22)
    y = margin + 40
    for n, (name, tile) in enumerate(tiles):
        x = margin + (n % cols) * (tw + gap)
        yy = y + (n // cols) * (tw + 40 + gap)
        out.paste(tile, (x, yy))
        d.rectangle([x, yy, x + tw, yy + tw], outline=(255, 255, 255, 60))
        label(d, x, yy + tw + 8, name, 18)
    y += rows_t * (tw + 40 + gap)
    kante = VF.teppich_kante(3.0, PPM, 1)
    out.paste(kante, (margin, y))
    label(d, margin + kante.width + 16, y + 4, "teppich_kante (Ornamentkante, 0,3 m)", 18)
    y += kante_h + 60
    wall_bg = Image.new("RGB", (ww, int(walls_h * PPM)), (30, 44, 34))
    for n, (style, wimg) in enumerate(walls):
        x = margin + n * (ww + gap)
        out.paste(wall_bg, (x, y))                                  # dunkler Grund hinter durchsichtigen Stilen
        d.rectangle([x, y - 12, x + ww, y], fill=WALL_TOP, outline=WALL_RIM)
        out.paste(wimg, (x, y), wimg)
        label(d, x, y + wimg.height + 8, f"wall_front '{style}' (2,6 x 1,65 Bild-m)", 18)
    y += int(walls_h * PPM) + 90
    # Bodendetails auf Parkett
    strip = Image.new("RGB", (W - 2 * margin, details_h), BG)
    tile_fill(strip, VF.material_tile("parkett", PPM, 1), 0, 0, strip.width, strip.height)
    sd = ImageDraw.Draw(strip, "RGBA")
    X0, Y1 = 0.0, details_h / PPM

    def P(x, yv):
        return ((x - X0) * PPM, (Y1 - yv) * PPM)

    VF.floor_dolly_rail(sd, P, PPM, 0.4, 1.3, 5.2)
    VF.floor_cable(sd, P, PPM, [(0.3, 0.4), (1.5, 0.6), (2.6, 0.35), (4.0, 0.7), (5.4, 0.5)], seed=3)
    VF.floor_tape_strip(sd, P, PPM, 2.5, 0.2, 2.75, 0.55)
    VF.floor_tape_mark(sd, P, PPM, 6.2, 0.6, "T")
    VF.floor_tape_mark(sd, P, PPM, 6.9, 0.6, "X", 0.3)
    VF.floor_tape_mark(sd, P, PPM, 7.6, 0.6, "L")
    VF.floor_chalk_cross(sd, P, PPM, 6.6, 1.5, seed=2)
    VF.floor_cobweb_corner(sd, P, PPM, 8.6, 2.1, 0.7, 1, -1, seed=4)
    VF.floor_leaves(sd, P, PPM, 9.4, 0.3, 11.5, 2.0, 18, seed=5)
    out.paste(strip, (margin, y))
    label(d, margin, y + details_h + 8, "Bodendetails: Dollyschiene, Kabel mit Tape, Tape-Marken T/X/L, Kreidekreuz, Spinnweben-Ecke, Laub", 18)
    out.save(os.path.join(OUT, "stilblatt_materialien.png"))


# ------------------------------------------------------------------ Szenen

class Scene:
    """12 x 7 m Welt bei PPM; Boden (RGB-Kacheln), Bodendetails, Waende, dann Objekte nach Standlinie."""

    def __init__(self, W, H, bg=BG):
        self.W, self.H = W, H
        self.img = Image.new("RGB", (int(W * PPM), int(H * PPM)), bg)
        self.props = []

    def P(self, x, y):
        return ((x) * PPM, (self.H - y) * PPM)

    def floor(self, name, x0, y0, x1, y1, seed=1):
        tile = VF.material_tile(name, PPM, seed)
        tile_fill(self.img, tile, int(x0 * PPM), int((self.H - y1) * PPM), int(x1 * PPM), int((self.H - y0) * PPM))

    def draw(self):
        return ImageDraw.Draw(self.img, "RGBA")

    def crown(self, x0, y0, x1, y1):
        d = self.draw()
        d.rectangle([self.P(x0, y1), self.P(x1, y0)], fill=WALL_TOP)
        d.line([self.P(x0, y0), self.P(x1, y0)], fill=WALL_RIM, width=max(1, int(0.03 * PPM)))

    def wall(self, x0, x1, y_bottom, h_img, style, seed=1):
        wimg = VF.wall_front(x1 - x0, h_img, style, PPM, seed)
        self.props.append((y_bottom + 1000, wimg, int(x0 * PPM), int((self.H - y_bottom - h_img) * PPM)))

    def shadow_band(self, x0, x1, y, depth=0.3):
        """Weicher Kontaktschatten der Wand auf dem Boden."""
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.rectangle([self.P(x0, y), self.P(x1, y - depth)], fill=(0, 0, 0, 90))
        layer = layer.filter(ImageFilter.GaussianBlur(int(0.1 * PPM)))
        self.img = Image.alpha_composite(self.img.convert("RGBA"), layer).convert("RGB")

    def light(self, cx, cy, rx, ry, col, strength=0.4):
        """Weicher Lichtfleck (Mondlicht) auf dem Boden."""
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for k in range(8):
            f = 1 - k / 8
            ld.ellipse([self.P(cx - rx * f, cy + ry * f), self.P(cx + rx * f, cy - ry * f)], fill=col + (int(255 * strength * 0.18),))
        layer = layer.filter(ImageFilter.GaussianBlur(int(0.25 * PPM)))
        self.img = Image.alpha_composite(self.img.convert("RGBA"), layer).convert("RGB")

    def window_light(self, x, y, w, h, skew, col, strength=0.55):
        """Mondlicht durch ein (unsichtbares) Sprossenfenster: schraeges Parallelogramm mit zwei
        Sprossenschatten, weich, kalt."""
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        a = int(255 * strength)
        quad = [self.P(x, y), self.P(x + w, y + skew), self.P(x + w, y + skew + h), self.P(x, y + h)]
        ld.polygon(quad, fill=col + (a,))
        for f in (0.34, 0.67):                                      # senkrechte Sprossen
            ld.line([self.P(x + w * f, y + skew * f - 0.02), self.P(x + w * f, y + skew * f + h + 0.02)], fill=(0, 0, 0, 0), width=int(0.05 * PPM))
        ld.line([self.P(x - 0.02, y + h * 0.5), self.P(x + w + 0.02, y + skew + h * 0.5)], fill=(0, 0, 0, 0), width=int(0.05 * PPM))
        layer = layer.filter(ImageFilter.GaussianBlur(int(0.06 * PPM)))
        self.img = Image.alpha_composite(self.img.convert("RGBA"), layer).convert("RGB")
        self.light(x + w / 2, y + h / 2, w * 1.2, h * 0.9, col, strength * 0.5)

    def prop(self, kind, shape, idx):
        img, wx, wy, base = VA.draw(kind, shape, idx, PPM)
        self.props.append((base, img, int(round(wx * PPM)), int(round((self.H - wy - img.height / PPM) * PPM))))

    def crewmate(self, x, y, body=(72, 76, 88, 255)):
        img, w, h = HD.crewmate(PPM, body=body)
        self.props.append((y, img, int((x - w / 2) * PPM), int((self.H - y - h) * PPM)))

    def finish(self, title):
        out = self.img.convert("RGBA")
        for base, img, px, py in sorted(self.props, key=lambda t: -t[0]):
            HD.paste_clipped(out, img, px, py)
        d = ImageDraw.Draw(out, "RGBA")
        label(d, 12, out.height - 34, title, 20)
        return out.convert("RGB")


def scene_halle():
    s = Scene(12, 7)
    wall_y = 5.4
    s.floor("parkett", 0, 0, 12, wall_y, 1)
    s.window_light(2.6, 2.9, 1.5, 1.1, 0.5, (176, 206, 255), 0.42)          # kaltes Mondlicht durch ein Fenster im Westen
    d = s.draw()
    VF.floor_cobweb_corner(d, s.P, PPM, 0.0, wall_y, 0.8, 1, -1, seed=3)
    VF.floor_dolly_rail(d, s.P, PPM, 1.2, 2.4, 10.8)
    VF.floor_cable(d, s.P, PPM, [(5.4, 1.95), (6.4, 1.6), (8.2, 1.45), (10.2, 1.3), (12.1, 1.25)], seed=1)
    VF.floor_cable(d, s.P, PPM, [(9.3, 3.5), (10.3, 3.1), (11.2, 2.7), (12.1, 2.4)], seed=2)
    VF.floor_tape_strip(d, s.P, PPM, 8.1, 1.25, 8.3, 1.7)
    VF.floor_tape_mark(d, s.P, PPM, 4.0, 3.4, "T")
    VF.floor_tape_mark(d, s.P, PPM, 7.0, 3.7, "T", 0.2)
    VF.floor_chalk_cross(d, s.P, PPM, 3.1, 1.1, seed=2)
    VF.floor_leaves(d, s.P, PPM, 0.2, 0.2, 3.0, 1.6, 6, seed=7)
    s.shadow_band(0, 12, wall_y)
    s.crown(0, 6.95, 12, 7.0)
    s.wall(0, 12, wall_y, 1.55, "tapete", 2)
    s.prop("standuhr", ("rect", 0.7, 4.95, 1.4, 5.4), 0)
    s.prop("kandelaber", ("rect", 2.2, 4.3, 2.65, 4.75), 0)
    s.prop("kandelaber_aus", ("rect", 10.5, 4.5, 10.95, 4.95), 1)
    s.prop("filmkamera", ("rect", 5.0, 2.05, 6.0, 2.75), 0)
    s.prop("scheinwerfer", ("rect", 9.2, 3.5, 9.9, 4.2), 0)
    s.crewmate(6.4, 3.3, (200, 60, 50, 255))
    s.finish("szene_halle: Eingangshalle, 12 x 7 m, 160 px/m").save(os.path.join(OUT, "szene_halle.png"))


def scene_friedhof():
    s = Scene(12, 7)
    s.floor("friedhofserde", 0, 0, 12, 5.6, 1)
    s.floor("wiese", 6.9, 5.6, 12, 7, 2)                                      # hinter dem Zaun: Wiese im Dunkeln
    d = s.draw()
    d.rectangle([s.P(6.9, 7), s.P(12, 5.6)], fill=(10, 10, 20, 120))
    s.light(3.0, 2.2, 2.2, 1.3, (176, 206, 255), 0.45)                       # Mondflecken
    s.light(9.5, 3.0, 1.8, 1.1, (176, 206, 255), 0.35)
    d = s.draw()
    VF.floor_leaves(d, s.P, PPM, 0, 0, 12, 5.5, 50, seed=3)
    VF.floor_tape_mark(d, s.P, PPM, 7.6, 1.6, "T", -0.3)
    s.shadow_band(0, 6.9, 5.6)
    s.crown(0, 6.95, 12, 7.0)
    s.wall(0, 6.9, 5.6, 1.35, "hecke", 1)
    s.wall(6.9, 12, 5.6, 1.3, "zaun", 1)
    for n, (x, y) in enumerate(((1.1, 4.6), (2.6, 4.9), (4.2, 4.5), (1.8, 2.6), (3.7, 1.5), (8.7, 4.4), (10.5, 4.7), (9.6, 2.1))):
        s.prop("grabstein", ("rect", x, y, x + 0.8, y + 0.3), n)
    s.prop("sarg", ("rect", 6.0, 2.9, 8.0, 3.6), 3)
    s.prop("kandelaber", ("rect", 5.3, 4.5, 5.75, 4.95), 2)
    s.prop("absperrung", ("rect", 9.6, 0.9, 11.6, 1.2), 0)
    s.crewmate(5.2, 1.9, (90, 180, 90, 255))
    s.finish("szene_friedhof: Friedhof, 12 x 7 m, 160 px/m").save(os.path.join(OUT, "szene_friedhof.png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    for name, fn in (("stilblatt_objekte", sheet_objects), ("stilblatt_materialien", sheet_materials),
                     ("szene_halle", scene_halle), ("szene_friedhof", scene_friedhof)):
        t = time.time()
        fn()
        print(f"{name}.png  {time.time() - t:5.1f} s")
    print(f"fertig in {time.time() - t0:.1f} s -> {OUT}")


if __name__ == "__main__":
    main()
