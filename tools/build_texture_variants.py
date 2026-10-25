# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# Baut die Grafik-Fassungen fuer das Vergleichsmenue der Testversionen (Villa/TextureVersions.cs, Taste F9).
#
# Jede Fassung wird auf die AKTUELLE Atlas-Aufteilung der Villa umgepackt: fuer jedes Sprite der heutigen
# Kartendateien (Villa/VillaSmall.g.cs + VillaLarge.g.cs, Tabellen Props und ConsoleSprites) wird das gleichnamige
# Sprite der alten Fassung aus deren Atlas geschnitten (Rechtecke aus der .g.cs jenes Stands, Git-Historie) und auf das
# heutige Rechteck gesetzt. Fehlt es dort (neues Objekt), bleibt das heutige Bild. Bodenkacheln nur bei gleicher Groesse.
# So genuegt zur Laufzeit Graphics.CopyTexture in die geladenen Texturen, auch Tuer- und Vent-Animationen stimmen.
#
# Quellen alter Staende: Paket files/villa_map.hwp am Tag des Asset-Repos (../UnknownsHalloween-Assets, git show),
# Rechtecke aus der .g.cs am Commit der Mod-Version, die diesen Tag nutzte. Die Fassung "vor Qwen" kommt aus
# tools/_villa_vorqwen (Kopie der Atlas-Quellen vom 25.10. vor dem Neumalen, gleiche Aufteilung wie heute).
#
# Ausgabe: ../UnknownsHalloween-Assets/files/variants/villa_<id>.hwp und Villa/TextureVariantCatalog.g.cs.
# Aufruf: python tools/build_texture_variants.py

import collections
import hashlib
import io
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT.parent / "UnknownsHalloween-Assets"
OUT = ASSETS / "files" / "variants"
CS = ROOT / "Villa" / "TextureVariantCatalog.g.cs"
sys.path.insert(0, str(ROOT.parent / "UnknownsAtlas" / "tools"))
import pack_textures  # noqa: E402

INSTALLED = ("Previous art (installed)", "Bisherige Grafik (installiert)")
# id, Label en, Label de, Quelle: ("dir", Ordner) oder ("tag", Asset-Tag, Commit der Mod mit passender .g.cs)
VERSIONS = [
    ("auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", ("dir", ROOT / "tools" / "_villa_auswahl")),
    ("gpt", "GPT (25.10.)", "GPT (25.10.)", ("dir", ROOT / "tools" / "_villa_gpt")),
    ("qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", ("dir", ROOT / "tools" / "_villa_qwen")),
    ("v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", ("tag", "v7", "1d03826")),
    ("v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", ("tag", "v6", "970122f")),
    ("v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", ("tag", "v5", "0ac85ca")),
    ("v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", ("tag", "v1", "e3f5b7d")),
]
ROW = re.compile(r'\("([^"]+)", (\d+), (\d+), (\d+), (\d+), (\d+), ')
PROW = re.compile(r'\("([^"]+)", (\d+), (\d+), (\d+), (\d+), (\d+), ([-\d.]+)f, ([-\d.]+)f, ([-\d.]+)f')


def layout(texts):
    """Sprite-Schluessel -> (Atlas-Art, Seite, x, y, w, h) aus den .g.cs-Texten (y Unity, unten links), dazu je Objekt-Sprite
    die Kartenpositionen seiner Platzierungen (fuer die Zuordnung zwischen Fassungen)."""
    out, pos = {}, collections.defaultdict(list)
    for t in texts:
        i, j, k = t.index("Props ="), t.index("ConsoleSprites ="), t.index("Consoles = new()")
        for m in PROW.finditer(t[i:j]):
            kind, rect = m.group(1), tuple(map(int, m.groups()[1:6]))
            key = ("p", kind, rect)
            out[key] = ("props",) + rect
            pos[key].append((float(m.group(7)), float(m.group(9))))
        for m in ROW.finditer(t[j:k]):
            out[("c", m.group(1))] = ("consoles",) + tuple(map(int, m.groups()[1:]))
    return out, pos


def match(cur, cur_pos, old, old_pos):
    """Heutiger Schluessel -> Eintrag der alten Fassung: Konsolen nach Namen, Objekte nach Art und naechster Platzierung
    (die Reihenfolge gleichartiger Objekte wechselt zwischen Staenden, etwa bei gespiegelten Scheinwerfern)."""
    by_kind = collections.defaultdict(list)
    for k in old:
        if k[0] == "p": by_kind[k[1]].append(k)
    res = {}
    for key in cur:
        if key[0] == "c":
            if key in old: res[key] = old[key]
            continue
        cands = by_kind.get(key[1])
        if not cands: continue
        def d(ok):
            return min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in cur_pos[key] for b in old_pos[ok])
        res[key] = old[min(cands, key=d)]
    return res


def floor_sizes(text):
    i = text.index("FloorTiles =")
    return {int(a): (int(w), int(h)) for a, w, h in re.findall(r"\((\d+), [-\d.]+f, [-\d.]+f, (\d+), (\d+)\)", text[i:i + 4000])}


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout


def read_hwp(data):
    n = struct.unpack("<i", data[4:8])[0]
    pos, items = 8, {}
    for _ in range(n):
        nl = struct.unpack("<H", data[pos:pos + 2])[0]
        name = data[pos + 2:pos + 2 + nl].decode("utf-8")
        off, ln = struct.unpack("<QI", data[pos + 2 + nl:pos + 14 + nl])
        pos += 14 + nl
        items[name] = data[off:off + ln]
    return items


def write_hwp(path, items):
    names = [n.encode("utf-8") for n, _ in items]
    off = 8 + sum(2 + len(n) + 12 for n in names)
    head = bytearray(b"HWP1" + struct.pack("<i", len(items)))
    for (n, d), nb in zip(items, names):
        head += struct.pack("<H", len(nb)) + nb + struct.pack("<QI", off, len(d))
        off += len(d)
    data = bytes(head) + b"".join(d for _, d in items)
    path.write_bytes(data)
    return data


def decode_atx(blob):
    """Oberste Mip-Stufe einer .atx als PIL-Bild (DDS-Kopf davor, PIL dekodiert DXT1/DXT5)."""
    fmt, w, h = blob[4], *struct.unpack("<ii", blob[8:16])
    raw = zlib.decompress(blob[28:], -15)
    top = ((w + 3) // 4) * ((h + 3) // 4) * (8 if fmt == 10 else 16)
    fourcc = b"DXT1" if fmt == 10 else b"DXT5"
    hdr = struct.pack("<4sIIIIIII44sII4s5I", b"DDS ", 124, 0x81007, h, w, top, 0, 1, b"\0" * 44, 32, 4, fourcc, 0, 0, 0, 0, 0)
    hdr += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    img = Image.open(io.BytesIO(hdr + raw[:top]))
    img = img.convert("RGBA" if fmt == 12 else "RGB")
    return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)   # Unity-Zeilen von unten


def sheets_from_tag(tag):
    items = read_hwp(git(ASSETS, "show", f"{tag}:files/villa_map.hwp"))
    out = {}
    for name, blob in items.items():
        m = re.fullmatch(r"villa_(props|consoles|floor)_(\d+)\.(atx|png|jpg)", name)
        if not m: continue
        img = decode_atx(blob) if name.endswith(".atx") else Image.open(io.BytesIO(blob))
        out[(m.group(1), int(m.group(2)))] = img
    return out


def sheets_from_dir(folder):
    out = {}
    for p in Path(folder).iterdir():
        m = re.fullmatch(r"villa_(props|consoles|floor)_(\d+)\.(png|jpg)", p.name)
        if m: out[(m.group(1), int(m.group(2)))] = Image.open(p)
    return out


def crop(img, rect):
    x, y, w, h = rect[-4:]
    top = img.height - y - h
    return img.crop((x, top, x + w, top + h))


def main():
    cur_texts = [(ROOT / "Villa" / f).read_text(encoding="utf-8") for f in ("VillaSmall.g.cs", "VillaLarge.g.cs")]
    cur, cur_pos = layout(cur_texts)
    cur_floor = floor_sizes(cur_texts[1]) | floor_sizes(cur_texts[0])
    base = sheets_from_dir(ROOT / "tools" / "_villa_vorqwen")      # heutige Aufteilung, Ersatz fuer fehlende Sprites
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for vid, en, de, src in VERSIONS:
        if src[0] == "dir":
            old_sheets, old = sheets_from_dir(src[1]), dict(cur)
        else:
            old_sheets = sheets_from_tag(src[1])
            ol, op = layout([git(ROOT, "show", f"{src[2]}:Villa/{f}").decode("utf-8") for f in ("VillaSmall.g.cs", "VillaLarge.g.cs")])
            old = match(cur, cur_pos, ol, op)
        new = {k: Image.new(img.mode, img.size, (0, 0, 0, 0) if img.mode == "RGBA" else (0, 0, 0))
               for k, img in base.items() if k[0] != "floor"}
        hit = miss = 0
        for key, rect in cur.items():
            kind, page = rect[0], rect[1]
            if (kind, page) not in new: continue
            o = old.get(key)
            if o and (o[0], o[1]) in old_sheets:
                sheet = old_sheets[(o[0], o[1])]
                if sheet.mode != new[(kind, page)].mode: sheet = old_sheets[(o[0], o[1])] = sheet.convert(new[(kind, page)].mode)
                sp = crop(sheet, o)
                if sp.size != (rect[4], rect[5]): sp = sp.resize((rect[4], rect[5]), Image.LANCZOS)
                hit += 1
            else:
                sp = crop(base[(kind, page)], rect); miss += 1
            new[(kind, page)].paste(sp, (rect[2], new[(kind, page)].height - rect[3] - rect[5]))
        floors = 0
        for (kind, i), img in base.items():
            if kind != "floor": continue
            o = old_sheets.get(("floor", i))
            use = o if o is not None and o.size == img.size else img
            floors += use is o
            new[("floor", i)] = use.convert("RGB")
        items = []
        with tempfile.TemporaryDirectory() as tmp:
            for (kind, i), img in sorted(new.items()):
                p = Path(tmp) / f"villa_{kind}_{i}.{'jpg' if kind == 'floor' else 'png'}"
                img.save(p, quality=95) if kind == "floor" else img.save(p)
                out_path = pack_textures.pack(str(p))[0]
                items.append((f"villa_{kind}_{i}.atx", Path(out_path).read_bytes()))
        data = write_hwp(OUT / f"villa_{vid}.hwp", items)
        rows.append((vid, en, de, f"villa_{vid}.hwp", len(data), hashlib.sha256(data).hexdigest()))
        print(f"{vid}: {hit} Sprites aus der Fassung, {miss} ergaenzt, {floors} Bodenkacheln, {len(data) / 1048576:.1f} MB")
    lines = ["// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0",
             "// Licensed under GPL-3.0-or-later. See LICENSE for details.",
             "//",
             "// AUTOMATISCH ERZEUGT von tools/build_texture_variants.py - NICHT VON HAND AENDERN.",
             "// Grafik-Fassungen der Halloween-Karten fuer das Vergleichsmenue der Testversionen (TextureVersions).",
             "// File null = die installierte Fassung aus den normalen Paketen; sonst ein Paket unter files/variants/ im Asset-Repo.",
             "",
             "namespace UnknownsHalloween;",
             "",
             "internal static class TextureVariantCatalog",
             "{",
             "    public static readonly (string Map, string Id, string LabelEn, string LabelDe, string File, long Size, string Sha256)[] Variants =",
             "    {",
             f"        (\"villa\", \"installed\", \"{INSTALLED[0]}\", \"{INSTALLED[1]}\", null, 0L, null),"]
    for vid, en, de, f, size, sha in rows:
        lines.append(f"        (\"villa\", \"{vid}\", \"{en}\", \"{de}\", \"{f}\", {size}L, \"{sha}\"),")
    lines += ["    };", "}", ""]
    CS.write_text("\n".join(lines), encoding="utf-8")
    print(f"Katalog -> {CS.name}")


if __name__ == "__main__":
    main()
