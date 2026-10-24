# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# build_assets_repo.py [tag]: grosse Bilder aus der DLL auslagern (Muster: UnknownsAtlas/tools/build_assets_repo.py).
#
# Packt alle Dateien, die Halloween zur Laufzeit aus dem Asset-Repo laedt, zu Paketen (.hwp) in
# ../UnknownsHalloween-Assets/files/, schreibt dort catalog.json und erzeugt HalloweenAssetCatalog.g.cs (Paketname,
# Groesse, SHA-256, Tag). Danach im Asset-Repo committen, Tag setzen (v1, v2 ...) und pushen; derselbe Tag steht dann
# im Katalog der DLL. Dateien im Ordner files/, die nicht mehr zum Katalog gehoeren, werden geloescht.
#
# Pakete statt Einzeldateien: allein die Kostueme sind gut 5000 Bilder. Ein Paket ist eine einfache Liste
# (Format HWP1, siehe HalloweenAssets.cs) mit den Ressourcennamen, wie die csproj sie vergeben wuerde
# ("hats.hw_freddy_1.png", "villa_floor_0.atx", "graveyard.task_gy_panel.png" ...). Der Code fragt weiter nach dem
# Ressourcennamen; HalloweenAssets sucht erst in der DLL, dann in den Paketen.
#
# Ausgelagert: alle Kostuem-, Kill- und Spinnenbein-Bilder (Resources/hats), Boden-, Objekt- und Konsolenatlanten
# (.atx), Minispielbilder, Vorspann und Rauswurfgrafik von Villa und Friedhof. In der DLL bleibt, was vor dem Download
# gebraucht wird: Rollen-Symbole, Suessigkeiten, Kartenknoepfe und -symbole, Minikarten, map.json und die
# Rauswurf-Regie (JSON). KEEP unten muss zu den EmbeddedResource-Eintraegen der csproj passen.

import fnmatch
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "Resources"
REPO = ROOT.parent / "UnknownsHalloween-Assets"
CS = ROOT / "HalloweenAssetCatalog.g.cs"

# Ordner -> (Praefix des Ressourcennamens wie in der csproj, Dateien, die eingebettet bleiben)
FOLDERS = {
    "hats": ("hats.", ["hw_xenomorph_icon.png", "hw_banshee_icon.png"]),
    "villa": ("", ["button_villa.png", "icon_villa.png", "villa_minimap_*.png", "task_eject_*.png", "*.json", "*.wav"]),
    "graveyard": ("graveyard.", ["map.json", "button_graveyard.png", "icon_graveyard.png", "graveyard_minimap.png"]),
    "graveyard_eject": ("", ["*.json"]),
    "candy_eject": ("", ["*.json", "*.wav"]),
}
# Gerenderte Vorspanne (Assets/Cinematics/_common/make_pack.py, Format HWP1): Paketname -> (Namenspraefix, Datei).
# Eigener Paketname ohne "villa_", damit die Karte nicht auf den grossen Film wartet (HollowmereMap: WhenReady("villa_")).
CINE_PACKS = {
    "cine_villa": ("villa_intro/", ROOT.parent / "Assets" / "Cinematics" / "manor" / "manor_intro.cine"),
}

# Quellbilder der .atx (pack_textures.py-Eingang) werden nie eingebettet und nicht ausgeliefert
SOURCES = ["*_floor_*.jpg", "*_props_*.png", "*_consoles_*.png"]


def pack_of(folder, name):
    stem = name.rsplit(".", 1)[0]
    if folder == "hats":
        return "hats_" + "_".join(stem.split("_")[:2])          # hats_hw_freddy, hats_hk_xenobite, hats_hl_spider
    if folder == "villa":
        if name.startswith("villa_intro_"): return "villa_intro"
        if name.startswith("villa_eject_"): return "villa_eject"
        return "villa_map"
    if folder == "graveyard":
        return "graveyard_map"
    if folder == "candy_eject":
        return "candy_eject"
    return "graveyard_eject"


def write_pack(path, items):
    """HWP1: 'HWP1', uint32 Anzahl, je Eintrag uint16 Namenslaenge, Name (UTF-8), uint64 Offset, uint32 Laenge; dann Daten."""
    names = [n.encode("utf-8") for n, _ in items]
    head = 8 + sum(2 + len(n) + 12 for n in names)
    out = bytearray(b"HWP1" + struct.pack("<I", len(items)))
    off = head
    for (n, data), nb in zip(items, names):
        out += struct.pack("<H", len(nb)) + nb + struct.pack("<QI", off, len(data))
        off += len(data)
    for _, data in items:
        out += data
    data = bytes(out)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return data


def read_pack(path):
    data = path.read_bytes()
    assert data[:4] == b"HWP1", path
    count, = struct.unpack_from("<I", data, 4)
    pos, items = 8, []
    for _ in range(count):
        nl, = struct.unpack_from("<H", data, pos); pos += 2
        name = data[pos:pos + nl].decode("utf-8"); pos += nl
        off, ln = struct.unpack_from("<QI", data, pos); pos += 12
        items.append((name, data[off:off + ln]))
    return items


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "v1"
    packs = {}
    for pack, (prefix, path) in CINE_PACKS.items():
        packs[pack] = [(prefix + n, d) for n, d in read_pack(path)]
    for folder, (prefix, keep) in FOLDERS.items():
        for p in sorted((RES / folder).iterdir(), key=lambda p: p.name):
            if not p.is_file(): continue
            if any(fnmatch.fnmatch(p.name, k) for k in keep + SOURCES): continue
            packs.setdefault(pack_of(folder, p.name), []).append((prefix + p.name, p.read_bytes()))
    out = REPO / "files"
    out.mkdir(parents=True, exist_ok=True)
    keep_files = {n + ".hwp" for n in packs}
    for old in out.iterdir():
        if old.name not in keep_files:
            old.unlink()
            print(f"removed {old.name}")
    entries = []
    for name in sorted(packs):
        data = write_pack(out / (name + ".hwp"), packs[name])
        entries.append({"name": name + ".hwp", "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                        "files": len(packs[name])})
    (REPO / "catalog.json").write_text(json.dumps({"tag": tag, "files": entries}, indent=1), encoding="utf-8")
    lines = ["// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0",
             "// Licensed under GPL-3.0-or-later. See LICENSE for details.",
             "//",
             "// AUTOMATISCH ERZEUGT von tools/build_assets_repo.py - NICHT VON HAND AENDERN.",
             "// Pakete, die Halloween aus dem Asset-Repo laedt (HalloweenAssets), mit Groesse und SHA-256.",
             "",
             "namespace UnknownsHalloween;",
             "",
             "internal static class HalloweenAssetCatalog",
             "{",
             f"    public const string Tag = \"{tag}\";",
             "",
             "    public static readonly (string Name, long Size, string Sha256)[] Files =",
             "    {"]
    for e in entries:
        lines.append(f"        (\"{e['name']}\", {e['size']}L, \"{e['sha256']}\"),")
    lines += ["    };", "}", ""]
    CS.write_text("\n".join(lines), encoding="utf-8")
    total = sum(e["size"] for e in entries)
    print(f"{len(entries)} Pakete, {sum(e['files'] for e in entries)} Dateien, {total / 1048576:.1f} MB -> {out}")
    print(f"Katalog {tag} -> {CS.name}")


if __name__ == "__main__":
    main()
