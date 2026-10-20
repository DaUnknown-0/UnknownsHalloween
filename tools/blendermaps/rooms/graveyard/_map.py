# graveyard (Unknown's Halloween) - Requisiten aus den Sprites des Spiels, Grundriss = Collider (BlenderMaps rooms/_atlas_props.py).

import sys

import bm_ext

sys.path.insert(0, str(bm_ext.ROOT / "rooms"))
import _atlas_props as AP                                                         # noqa: E402


def extra(sc, ctx):
    return AP.build(sc, ctx)


def adjust(sc):
    AP.room_heights(sc)
