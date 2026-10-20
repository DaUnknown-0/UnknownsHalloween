# Unknown's Halloween - Erweiterung fuer Assets/BlenderMaps (privat, nicht veroeffentlichen).
#
# Meldet die Karten villa (Hollowmere Manor) und graveyard (Ravenhollow Cemetery) bei BlenderMaps an: Vorlage fuer
# atlas_import.py, Szenen-Einstellungen fuer bm_scene.py, Raumdateien (rooms/<karte>/_map.py) und die Requisiten-
# Modelle (halloween_models.py). BlenderMaps laedt diese Datei nur, wenn bm_local.json auf diesen Ordner zeigt:
#   {"ext_dirs": ["../../UnknownsHalloween/tools/blendermaps"]}
# register() importiert nichts aus BlenderMaps (bm_ext.py ruft es beim Import von bm_ref/bm_scene/atlas_import auf).

from pathlib import Path

HERE = Path(__file__).resolve().parent
HALLO = HERE.parent.parent                    # UnknownsHalloween/

SCENES = {
    "villa": {"hull": (27, 22, 29), "space": (22, 19, 26), "ceiling": (92, 68, 54), "world": (22, 19, 30), "k": 0.55, "H": 1.73, "ship": "hull_mask", "smooth_tex": True,
              "cap_art": True, "north_stop": 0.3, "hull_tol": 14, "rim": [(16, 17, 20, 0.03)]},
    "graveyard": {"hull": (46, 46, 54), "space": (13, 22, 27), "world": (22, 32, 48), "k": 0.55, "H": 1.73, "ship": "hull_mask", "smooth_tex": True,
                  "cap_art": True, "north_stop": 0.3, "sky_all": True, "rim": [(16, 17, 20, 0.03)]},
}

# Quelle: VillaSmall.g.cs (C#-Arrays wie <Map>Data.cs) bzw. map.json (Atlas-Dateiformat) aus diesem Repo
SOURCES = {
    "villa": {"cs": HALLO / "Villa" / "VillaSmall.g.cs", "layout": None, "assets": HALLO / "Resources" / "villa",
              "prefix": "villa"},
    "graveyard": {"json": HALLO / "Resources" / "graveyard" / "map.json", "assets": HALLO / "Resources" / "graveyard",
                  "prefix": "graveyard"},
}


def register(api):
    for key in ("villa", "graveyard"):
        api.add_map(key, source=SOURCES[key], scene=SCENES[key], rooms=HERE / "rooms" / key)
    api.add_models(HERE / "halloween_models.py")
