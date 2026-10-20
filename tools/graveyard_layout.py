# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# graveyard_layout.py - Ravenhollow Cemetery: Grundriss und Ausstattung (Weltmeter, x Osten, y Norden).
#
# gen_graveyard.py baut daraus Waende, Raeume, Konsolen und map.json; graveyard_floor.py malt den Boden,
# graveyard_art.py zeichnet die Objekte. Objekte: (Art, Form, Modus); Modus "opaque" sperrt Weg und Sicht,
# "glass" nur den Weg, "deco" gar nichts (flache Dinge, die trotzdem als Sprite ueber dem Boden liegen).

WALL = 0.5
PATH_W = 2.8
CORNER = 1.6
BOUNDS = (-25.0, -21.0, 25.0, 21.0)

# key, Name, System, Innenraum, Oeffnungen (Seite, von, bis, "door"|"gap")
BUILDINGS = [
    ("chapel", "Chapel", "Cafeteria", (-5, -4, 5, 4),
     [("W", -1.25, 1.25, "door"), ("E", -1.25, 1.25, "door"), ("N", -4.65, -2.15, "door"), ("S", -1.25, 1.25, "gap")]),
    ("coffins", "Coffin Store", "Storage", (-22, -4, -14, 3),
     [("E", -1.25, 1.25, "door"), ("N", -19.25, -16.75, "door"), ("S", -19.25, -16.75, "door")]),
    ("well", "Well House", "UpperEngine", (-11, 10, -5, 16),
     [("S", -9.25, -6.75, "door"), ("E", 11.75, 14.25, "door"), ("W", 11.75, 14.25, "gap")]),
    ("mausoleum", "Mausoleum", "LifeSupp", (14, 10, 22, 16),
     [("W", 11.75, 14.25, "gap"), ("S", 16.75, 19.25, "gap")]),
    ("morgue", "Morgue", "MedBay", (15, -3, 22, 3),
     [("W", -1.25, 1.25, "door"), ("N", 16.75, 19.25, "gap")]),
    ("crematorium", "Crematorium", "LowerEngine", (-22, -17, -14, -10),
     [("N", -19.25, -16.75, "door"), ("E", -14.75, -12.25, "door")]),
    ("office", "Caretaker's Office", "Admin", (-11, -17, -5, -11),
     [("W", -14.75, -12.25, "gap"), ("E", -15.75, -13.25, "gap")]),
    ("gatehouse", "Gatehouse", "Comms", (-3, -18, 3, -12),
     [("N", -1.25, 1.25, "gap"), ("W", -15.75, -13.25, "gap")]),
    ("lanterns", "Lantern Shed", "Electrical", (6, -17, 11, -12),
     [("N", 7.25, 9.75, "door"), ("E", -15.75, -13.25, "gap")]),
    ("lodge", "Watchman's Lodge", "Security", (15, -18, 22, -11),
     [("W", -15.75, -13.25, "door"), ("N", 17.25, 19.75, "gap")]),
]
# offene Flaechen: key, Name, System, Rechteck
CLEARINGS = [
    ("belltower", "Bell Tower", "Reactor", (-22, 9, -14, 17)),
    ("graves", "Old Graves", "Nav", (-3, 8, 11, 18)),
    ("roost", "Raven Roost", "Weapons", (-12, -3, -7, 6)),
    ("wards", "Ward Stones", "Shields", (7, -4, 12, 4)),
]
# Kieswege (Mittellinien)
PATHS = [
    [(-14, 0), (-5, 0)],                 # Sargkammer O -> Rabenhorst -> Kapelle W
    [(5, 0), (15, 0)],                   # Kapelle O -> Waechtersteine -> Leichenhalle W
    [(-3.4, 4), (-3.4, 6.6), (-1.0, 9.2)],  # Kapelle N (Seitentuer neben dem Altar) -> Alte Graeber
    [(0, -4), (0, -12)],                 # Kapelle S -> Torhaus
    [(-18, 3), (-18, 9.5)],              # Sargkammer N -> Glockenturm
    [(-18, -4), (-18, -10)],             # Sargkammer S -> Krematorium
    [(-8, 10), (-8, 5.5)],               # Brunnenhaus S -> Rabenhorst
    [(-5, 13), (-2.5, 13)],              # Brunnenhaus O -> Alte Graeber
    [(-14.5, 13), (-11, 13)],            # Glockenturm -> Brunnenhaus W
    [(10.5, 13), (14, 13)],              # Alte Graeber O -> Mausoleum W
    [(18, 10), (18, 3)],                 # Mausoleum S -> Leichenhalle N
    [(-14, -13.5), (-11, -13.5)],        # Krematorium O -> Verwaltung W
    [(-5, -14.5), (-3, -14.5)],          # Verwaltung O -> Torhaus W
    [(0, -9), (18.5, -9)],               # suedliche Gasse
    [(8.5, -12), (8.5, -9)],             # Laternenschuppen N
    [(18.5, -11), (18.5, -9)],           # Waechterhaus N
    [(9.5, -3.5), (9.5, -9)],            # Waechtersteine S -> Gasse
    [(11, -14.5), (15, -14.5)],          # Laternenschuppen O -> Waechterhaus W
]

SPAWN = (0.0, 1.0)
SPAWN_RADIUS = 1.8
EMERGENCY = (0.0, 2.75)               # Totenglocke auf dem Lesepult vor dem Altar
SURVEILLANCE = (20.6, -11.7)          # Waechterhaus: Spiegelpult
ADMIN_TABLE = (-8.0, -14.0)           # Verwaltung: Grabplan-Tisch
FREEPLAY = (3.8, -3.2)
FIXED = {
    "Reactor/UpperHandConsole/0": (-20.6, 15.6),     # Death Knell: zwei Glockenseile
    "Reactor/LowerHandConsole/1": (-15.4, 10.4),
    "LifeSupp/NoOxyConsole/0": (20.8, 15.2),         # Miasma: Mausoleum + Verwaltung
    "Admin/NoOxyConsole/1": (-5.8, -11.6),
    "Electrical/SwitchConsole/0": (10.3, -12.6),
    "Comms/FixCommsConsole/0": (2.3, -17.3),
    "MedBay/MedScanner/0": (20.8, -2.2),
}
VENTS = {
    0: (-16.6, 15.6), 3: (-1.4, 16.6), 12: (9.6, 16.6), 6: (15.0, 15.2),
    1: (-21.0, -3.2), 5: (-11.2, 5.0), 13: (11.4, 3.2), 7: (21.0, 2.2),
    2: (-21.0, -16.2), 9: (-10.2, -16.2), 10: (-2.2, -17.2), 11: (6.8, -16.2), 8: (21.0, -17.2),
}
VENT_NETS = [[0, 3, 12, 6], [1, 5, 13, 7], [2, 9, 10, 11, 8]]
VENT_BRIDGES = [[3, 5], [7, 8]]
CAMERAS = [(-3.4, 6.0), (-8.6, -1.6), (9.5, -6.6), (18.0, 6.6)]

# ------------------------------------------------------------------ Ausstattung
# Art, Form, Modus. Formen wie museum_art.shape_bounds: ("rect", x0, y0, x1, y1) | ("circle", cx, cy, r)
PROPS = [
    # Chapel: Altar an der Nordwand, Kandelaber, vier Kirchenbaenke, Taufbecken, Opferkerzen
    ("altar", ("rect", -1.4, 3.35, 1.4, 3.95), "glass"),
    ("kandelaber", ("circle", -1.8, 3.45, 0.22), "glass"),
    ("kandelaber", ("circle", 1.8, 3.45, 0.22), "glass"),
    ("kirchenbank", ("rect", -3.7, -2.5, -1.3, -1.9), "glass"),
    ("kirchenbank", ("rect", 1.3, -2.5, 3.7, -1.9), "glass"),
    ("kirchenbank", ("rect", -3.7, -1.15, -1.3, -0.55), "glass"),
    ("kirchenbank", ("rect", 1.3, -1.15, 3.7, -0.55), "glass"),
    ("taufbecken", ("circle", -4.3, -3.3, 0.38), "glass"),
    ("opferkerzen", ("rect", 3.6, 2.7, 4.6, 3.3), "glass"),

    # Coffin Store: Saergestapel, Hobelbank, angelehnte Saerge, Bretter, offener Sarg auf Boecken
    ("sargstapel", ("rect", -21.6, 0.2, -19.8, 2.6), "opaque"),
    ("hobelbank", ("rect", -15.0, 1.5, -14.2, 2.8), "glass"),
    ("sarg_stehend", ("rect", -21.95, -1.7, -21.35, -0.5), "glass"),
    ("bretter", ("rect", -16.3, -3.75, -14.5, -3.2), "glass"),
    ("sarg_bock", ("rect", -19.1, -1.7, -17.3, -1.05), "glass"),

    # Well House: Brunnen mit Dach und Kurbel, Trog, Faesser
    ("brunnen", ("circle", -8.0, 13.0, 0.78), "glass"),
    ("trog", ("rect", -10.75, 15.0, -9.45, 15.55), "glass"),
    ("fass", ("circle", -5.55, 15.4, 0.3), "glass"),
    ("fass", ("circle", -5.6, 10.55, 0.3), "glass"),

    # Mausoleum (Gruft): zwei Sarkophage, Saeulen, Urnen
    ("sarkophag", ("rect", 15.9, 12.0, 17.9, 13.0), "glass"),
    ("sarkophag", ("rect", 18.7, 12.0, 20.7, 13.0), "glass"),
    ("saeule", ("circle", 14.6, 10.6, 0.24), "glass"),
    ("saeule", ("circle", 21.4, 10.6, 0.24), "glass"),
    ("urne", ("circle", 21.45, 13.2, 0.2), "glass"),

    # Morgue: zwei Obduktionstische, Instrumentenschrank, Rolltrage
    ("obduktionstisch", ("rect", 16.8, -1.7, 18.6, -0.9), "glass"),
    ("obduktionstisch", ("rect", 19.4, 0.5, 21.2, 1.3), "glass"),
    ("instrumentenschrank", ("rect", 15.2, 1.95, 16.4, 2.75), "glass"),

    # Crematorium: Ofen, Kohlehaufen, Aschewagen
    ("ofen", ("rect", -21.6, -13.0, -19.0, -11.2), "opaque"),
    ("kohlen", ("rect", -15.5, -11.3, -14.3, -10.45), "glass"),
    ("aschewagen", ("rect", -17.6, -16.65, -16.6, -15.9), "glass"),

    # Caretaker's Office: Schreibtisch, Aktenschrank, Ofen
    ("schreibtisch", ("rect", -10.6, -11.85, -9.1, -11.25), "glass"),
    ("aktenschrank", ("rect", -7.5, -11.75, -6.65, -11.2), "glass"),
    ("kanonenofen", ("circle", -5.65, -16.35, 0.3), "glass"),

    # Gatehouse: Waechterpult, Laternenstaender
    ("waechterpult", ("rect", 1.65, -13.05, 2.75, -12.35), "glass"),
    ("laternenpfahl", ("circle", -2.45, -12.55, 0.14), "glass"),

    # Lantern Shed: Oelfass (Regale und Werkbank sind die Konsolen selbst)
    ("fass", ("circle", 10.5, -16.5, 0.28), "glass"),

    # Watchman's Lodge: Bett, Ofen, Tisch
    ("bett", ("rect", 15.3, -17.75, 16.35, -16.0), "glass"),
    ("kanonenofen", ("circle", 21.45, -14.6, 0.32), "glass"),
    ("tisch", ("rect", 18.0, -16.45, 19.2, -15.65), "glass"),

    # Bell Tower: Glockenturm (Sockel = Sichtsperre)
    ("glockenturm", ("rect", -19.0, 11.8, -17.0, 13.8), "opaque"),

    # Old Graves: acht Grabsteine, Engel in der Mitte
    *[("grabstein", ("rect", x - 0.5, y - 0.2, x + 0.5, y + 0.2), "glass") for x in (0.5, 3.0, 5.5, 8.0) for y in (10.4, 15.8)],
    ("engel", ("circle", 4.25, 13.1, 0.42), "glass"),

    # Raven Roost: toter Baum (Stamm sperrt Sicht)
    ("rabenbaum", ("circle", -9.5, 2.0, 0.4), "opaque"),

    # Ward Stones: vier Menhire um den Runenkreis
    ("menhir", ("rect", 7.6, 2.45, 8.25, 2.95), "opaque"),
    ("menhir", ("rect", 9.9, 2.85, 10.55, 3.35), "opaque"),
    ("menhir", ("rect", 7.6, -2.85, 8.25, -2.35), "opaque"),
    ("menhir", ("rect", 11.05, -2.55, 11.7, -2.05), "opaque"),

    # Wege: Laternenpfaehle und Baenke am Rand
    ("laternenpfahl", ("circle", -2.15, 5.6, 0.14), "glass"),
    ("laternenpfahl", ("circle", 1.15, -6.2, 0.14), "glass"),
    ("laternenpfahl", ("circle", 4.5, -7.75, 0.14), "glass"),
    ("laternenpfahl", ("circle", 14.0, -10.25, 0.14), "glass"),
    ("laternenpfahl", ("circle", -12.4, 1.15, 0.14), "glass"),
    ("laternenpfahl", ("circle", 13.6, 1.15, 0.14), "glass"),
    ("laternenpfahl", ("circle", -16.85, -7.0, 0.14), "glass"),
    ("laternenpfahl", ("circle", 19.15, 6.5, 0.14), "glass"),
    ("parkbank", ("rect", 2.2, -10.35, 3.6, -9.95), "glass"),
    ("parkbank", ("rect", 12.0, 13.95, 13.4, 14.35), "glass"),
]

SKELD_CONSOLES = {
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

TASK_NAMES = {
    "FixWiring": "Rewire the Grave Lamps", "SwipeCard": "Sign the Burial Register", "CalibrateDistributor": "Trim the Lantern Wicks",
    "ChartCourse": "Map the Graves", "CleanO2Filter": "Sweep the Crypt", "DivertPower": "Light the Path",
    "PrimeShields": "Relight the Ward Candles", "StabilizeSteering": "Straighten a Headstone", "UnlockManifolds": "Unlock the Ossuary",
    "UploadData": "Copy the Epitaphs", "AlignEngineOutput": "Wind the Well Crank", "ClearAsteroids": "Shoo the Ravens",
    "EmptyGarbage": "Clear the Wreaths", "FuelEngines": "Stoke the Furnace", "InspectSample": "Identify the Ashes",
    "StartReactor": "Ring the Bell", "SubmitScan": "Identify the Remains",
    "ResetReactor": "Death Knell", "RestoreOxy": "Miasma", "FixLights": "Lanterns Out", "FixComms": "Gate Bell Silent",
}
