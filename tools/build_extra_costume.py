# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# build_extra_costume.py <key> [<key> ...] | --remove <key>: Online-Kostueme ohne Mod-Update (HalloweenExtraCostumes.cs).
#
# Quelle: ExtraCostumes/<key>/ mit costume.json (Name und Verhalten, siehe unten) und den Bildern unter denselben Namen
# wie bei den eingebauten Kostuemen:
#   hw_<key>_1.png .. _16.png      Stehen (1 bis 16 Bilder; hw_<key>_main.png = 450 breiter Ausschnitt fuer breite Leinwand)
#   hw_<key>_acc_N.png             Spielerfarbe-Masken zum Stehen (bei "hasAccent")
#   hw_<key>_walk_N.png / _walk_acc_N.png   Laufen (bei "stillWalk" beliebig viele, sonst 12)
#   hw_<key>_climb.png, hw_<key>_back.png   Leiter, Rueckebene (beide optional)
#   hk_<key>_...                   Kill-Szene (optional, wie die eingebauten Szenen)
# Ergebnis: ../UnknownsHalloween-Assets/extra/extra_<key>_<sha8>.hwp und der Eintrag in extra/costumes.json. Danach im
# Asset-Repo committen und main pushen; ein Tag ist nicht noetig. Alte Pakete des Kostuems werden geloescht.
#
# costume.json (alles ausser "name" optional):
#   {"name": "Halloween Bat", "hidesBody": true, "hasAccent": true, "stillWalk": true, "walkFps": 12, "idleFps": 6,
#    "walkIntro": 4, "hasLegs": false, "noLiveBob": false, "minVersion": "1.0.2",
#    "kill": {"frames": 48, "flashes": [12, 30], "hold": 0.4, "killerLayers": false}}

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets_repo import write_pack, ROOT, REPO  # noqa: E402

SRC = ROOT / "ExtraCostumes"
OUT = REPO / "extra"
MANIFEST = OUT / "costumes.json"
FLAGS = ["hidesBody", "hasAccent", "stillWalk", "hasLegs", "noLiveBob"]
NUMS = ["walkFps", "idleFps", "walkIntro"]


def load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"format": 1, "costumes": []}


def save_manifest(m):
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def drop_old(key, keep=None):
    for p in OUT.glob(f"extra_{key}_*.hwp"):
        if p.name != keep:
            p.unlink()
            print(f"  removed {p.name}")


def build(key):
    assert re.fullmatch(r"[a-z][a-z0-9]{1,23}", key), f"bad key {key}"
    folder = SRC / key
    meta = json.loads((folder / "costume.json").read_text(encoding="utf-8"))
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix == ".png"
                   and (p.name.startswith(f"hw_{key}_") or p.name.startswith(f"hk_{key}_")))
    assert any(p.name == f"hw_{key}_1.png" for p in files), f"hw_{key}_1.png missing in {folder}"
    items = [("hats." + p.name, p.read_bytes()) for p in files]
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / f"extra_{key}_tmp.hwp"
    data = write_pack(tmp, items)
    sha = hashlib.sha256(data).hexdigest()
    name = f"extra_{key}_{sha[:8]}.hwp"
    tmp.replace(OUT / name)
    drop_old(key, keep=name)
    entry = {"key": key, "name": meta["name"], "package": name, "size": len(data), "sha256": sha}
    for f in FLAGS:
        if meta.get(f): entry[f] = True
    for n in NUMS:
        if n in meta: entry[n] = meta[n]
    for opt in ("minVersion", "kill"):
        if opt in meta: entry[opt] = meta[opt]
    m = load_manifest()
    m["costumes"] = [c for c in m["costumes"] if c["key"] != key] + [entry]
    save_manifest(m)
    print(f"{key}: {len(items)} Bilder, {len(data) / 1048576:.2f} MB -> extra/{name}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__ or "build_extra_costume.py <key> ... | --remove <key>")
        return
    if args[0] == "--remove":
        m = load_manifest()
        for key in args[1:]:
            m["costumes"] = [c for c in m["costumes"] if c["key"] != key]
            drop_old(key)
            print(f"{key}: aus der Liste genommen")
        save_manifest(m)
        return
    for key in args:
        build(key)
    print(f"Liste: {MANIFEST}")
    print("Jetzt im Asset-Repo committen und main pushen (kein Tag noetig).")


if __name__ == "__main__":
    main()
