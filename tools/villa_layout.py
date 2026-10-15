# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# villa_layout.py - Hollowmere Manor (Arbeitstitel), Grundriss fuer beide Varianten.
#
# Konzept: docs/villa/hollowmere.html (Spukvilla als Horrorfilm-Set). Das Haus (34 x 24 m) ist der Kern
# und in beiden Varianten gleich; "large" oeffnet zusaetzlich Terrasse, Vorplatz, Crew-Lager, Gewaechshaus,
# Brunnenhof, Friedhof und Familiengruft.
#
# KOORDINATEN: Plan-Meter wie auf der Vorschauseite, x nach Osten, y nach SUEDEN (Bildschirm). Der
# Generator (gen_villa.py) rechnet in Atlas-Weltmeter um: wx = x - ORIGIN[0], wy = ORIGIN[1] - y
# (Spawn liegt dann bei 0/0).
#
# Bereiche: (key, Anzeigename, Rechteck, Varianten, System je Variante). Das Rechteck reicht bis in die
# Wandmitte; begehbar ist es um WALL/2 eingerueckt. Ein Bereich, der in einem anderen liegt (Gruft im
# Friedhof), wird aus diesem ausgeschnitten. System: Skeld-SystemType (Tasks, Sabotagen, Tuergruppen)
# oder ein freier Typ nur fuer den Raumnamen (Records, HallOfPortraits ... wie im Park) oder None = Gang.
#
# Oeffnungen: (Achse, Lage, von, bis, {Variante: Art}). Achse "x" = senkrechte Wand bei x = Lage, Spanne
# in y; "y" = waagerechte Wand. Art "open" | ("door", Tuergruppe). Fehlt die Variante, ist die Wand dort zu.
# Die 13 Skeld-Tueren je Variante: 7 senkrecht + 6 waagerecht, Gruppen Cafeteria 3, Storage 3,
# UpperEngine 2, LowerEngine 2, Security 1, MedBay 1, Electrical 1.

ORIGIN = (17.0, 14.0)
WALL = 0.4
VARIANTS = {"small": (0.0, 0.0, 34.0, 24.0), "large": (0.0, 0.0, 50.0, 36.0)}

B = ("small", "large")
L = ("large",)

AREAS = [
    # ----------------------------------------------------------------- Haus, Nordreihe
    ("kitchen", "Kitchen", (0, 0, 7, 8), B, {"small": "LowerEngine", "large": "LowerEngine"}),
    ("laundry", "Laundry", (7, 0, 11, 8), B, {"small": "UpperEngine", "large": "Showers"}),
    ("seance", "Seance Parlour", (11, 0, 23, 8), B, {"small": "Reactor", "large": "Reactor"}),
    ("radio", "Radio Room", (23, 0, 27, 8), B, {"small": "Comms", "large": "Comms"}),
    ("boxroom", "Box Room", (27, 0, 34, 4), B, {"small": "Storage", "large": "CargoBay"}),
    ("observatory", "Observatory", (27, 4, 34, 8), B, {"small": "Nav", "large": "Nav"}),
    # ----------------------------------------------------------------- Haus, Mitte
    ("boiler", "Boiler Room", (0, 8, 8, 14), B, {"small": "Electrical", "large": "Electrical"}),
    ("westhall", "West Hall", (8, 8, 11, 14), B, {"small": None, "large": None}),
    ("library", "Library", (0, 14, 11, 19), B, {"small": "Records", "large": "Records"}),
    ("chapel", "Chapel", (0, 19, 11, 24), B, {"small": "Shields", "large": "Lounge"}),
    ("hall", "Entrance Hall", (11, 8, 23, 20), B, {"small": "Cafeteria", "large": "Cafeteria"}),
    ("booth", "Director's Booth", (11, 20, 15, 24), B, {"small": "Security", "large": "Security"}),
    ("vestibule", "Vestibule", (15, 20, 19, 24), B, {"small": None, "large": None}),
    ("makeup", "Makeup", (19, 20, 23, 24), B, {"small": "MedBay", "large": "MedBay"}),
    ("gallery", "Portrait Gallery", (23, 8, 26, 24), B, {"small": "HallOfPortraits", "large": "HallOfPortraits"}),
    ("trophy", "Trophy Room", (26, 8, 34, 13), B, {"small": "Weapons", "large": "Weapons"}),
    ("fireplace", "Fireplace Room", (26, 13, 34, 18), B, {"small": "LifeSupp", "large": "LifeSupp"}),
    ("study", "Study", (26, 18, 34, 24), B, {"small": "Admin", "large": "Admin"}),
    # ----------------------------------------------------------------- Garten (nur gross)
    ("terrace", "Terrace", (34, 2, 40, 26), L, {"large": "Balcony"}),
    ("driveway", "Driveway", (12, 24, 24, 30), L, {"large": "MainHall"}),
    ("crewcamp", "Crew Camp", (0, 24, 12, 36), L, {"large": "UpperEngine"}),
    ("greenhouse", "Greenhouse", (40, 2, 50, 12), L, {"large": "Storage"}),
    ("fountain", "Fountain Court", (24, 26, 40, 36), L, {"large": "Greenhouse"}),
    ("graveyard", "Graveyard", (40, 14, 50, 36), L, {"large": "Laboratory"}),
    ("crypt", "Family Crypt", (44, 28, 50, 36), L, {"large": "Shields"}),
]

# Raeume, deren Licht schwaecher ist (Mechanik "Kerzen & Dunkelheit", spaeter); die Vorschau toent sie
DARK = {"seance", "boxroom", "boiler", "library", "chapel", "fountain", "graveyard", "crypt"}

OPENINGS = [
    # Nordreihe
    ("x", 7, 3.0, 5.5, {"small": ("door", "LowerEngine"), "large": ("door", "LowerEngine")}),   # Kitchen - Laundry
    ("x", 11, 3.0, 5.5, {"small": ("door", "UpperEngine"), "large": "open"}),                   # Laundry - Seance
    ("x", 23, 3.0, 5.5, {"small": "open", "large": "open"}),                                    # Seance - Radio
    ("y", 8, 8.3, 10.7, {"small": ("door", "UpperEngine"), "large": "open"}),                   # Laundry - West Hall
    ("y", 8, 23.5, 25.5, {"small": "open", "large": "open"}),                                   # Radio - Gallery
    ("x", 27, 0.75, 3.25, {"small": ("door", "Storage"), "large": "open"}),                     # Radio - Box Room
    ("y", 4, 29.5, 32.0, {"small": ("door", "Storage"), "large": "open"}),                      # Box Room - Observatory
    ("y", 8, 30.0, 32.5, {"small": ("door", "Storage"), "large": "open"}),                      # Observatory - Trophy
    ("y", 8, 2.0, 4.5, {"small": ("door", "LowerEngine"), "large": ("door", "LowerEngine")}),   # Kitchen - Boiler
    # Mitte
    ("x", 8, 9.5, 12.0, {"small": ("door", "Electrical"), "large": ("door", "Electrical")}),    # West Hall - Boiler
    ("x", 11, 10.25, 12.75, {"small": ("door", "Cafeteria"), "large": ("door", "Cafeteria")}), # West Hall - Hall
    ("y", 14, 8.5, 10.5, {"small": "open", "large": "open"}),                                   # West Hall - Library
    ("y", 14, 2.0, 4.5, {"small": "open", "large": "open"}),                                    # Boiler - Library
    ("y", 19, 3.0, 5.5, {"small": "open", "large": "open"}),                                    # Library - Chapel
    ("x", 23, 10.25, 12.75, {"small": ("door", "Cafeteria"), "large": ("door", "Cafeteria")}), # Hall - Gallery
    ("y", 20, 15.75, 18.25, {"small": ("door", "Cafeteria"), "large": "open"}),                 # Hall - Vestibule
    ("y", 20, 11.75, 14.25, {"small": ("door", "Security"), "large": ("door", "Security")}),   # Hall - Booth
    ("x", 15, 21.5, 23.5, {"small": "open", "large": "open"}),                                  # Booth - Vestibule
    ("x", 19, 21.5, 23.5, {"small": "open", "large": "open"}),                                  # Vestibule - Makeup
    ("x", 23, 21.0, 23.5, {"small": ("door", "MedBay"), "large": ("door", "MedBay")}),         # Makeup - Gallery
    ("x", 26, 9.5, 12.0, {"small": "open", "large": "open"}),                                   # Gallery - Trophy
    ("x", 26, 14.5, 16.5, {"small": "open", "large": "open"}),                                  # Gallery - Fireplace
    ("x", 26, 20.0, 22.5, {"small": "open", "large": "open"}),                                  # Gallery - Study
    ("y", 13, 27.0, 29.5, {"small": "open", "large": "open"}),                                  # Trophy - Fireplace
    ("y", 18, 27.0, 29.5, {"small": "open", "large": "open"}),                                  # Fireplace - Study
    # Aussen (nur gross; in "small" verrammelt, siehe BARRICADES)
    ("y", 24, 15.75, 18.25, {"large": ("door", "Cafeteria")}),                                  # Vestibule - Driveway (Haustuer)
    ("x", 34, 14.5, 16.5, {"large": "open"}),                                                   # Fireplace - Terrace (Terrassentuer)
    ("y", 24, 3.0, 5.5, {"large": ("door", "UpperEngine")}),                                    # Chapel - Crew Camp (Hintertuer)
    ("x", 12, 26.5, 29.0, {"large": ("door", "UpperEngine")}),                                  # Driveway - Crew Camp
    ("x", 24, 26.5, 29.5, {"large": "open"}),                                                   # Driveway - Fountain Court
    ("y", 26, 35.75, 38.25, {"large": ("door", "Storage")}),                                    # Terrace - Fountain Court
    ("x", 40, 5.0, 7.5, {"large": ("door", "Storage")}),                                        # Terrace - Greenhouse
    ("x", 40, 17.0, 19.5, {"large": "open"}),                                                   # Terrace - Graveyard (Friedhofstor)
    ("x", 40, 30.0, 33.0, {"large": "open"}),                                                   # Fountain Court - Graveyard
    ("y", 28, 45.75, 48.25, {"large": ("door", "Storage")}),                                    # Graveyard - Crypt (Gruft-Tor)
]

# Aussenoeffnungen des Hauses, die in "small" verrammelt sind (Bretter vor der Tuer, Prop "barrikade")
BARRICADES = [("y", 24, 15.75, 18.25), ("x", 34, 14.5, 16.5), ("y", 24, 3.0, 5.5)]

# ------------------------------------------------------------------ Spielpunkte (Plan-Meter)
SPAWN = (17.0, 13.2)
SPAWN_RADIUS = 2.0
EMERGENCY = (17.0, 15.6)              # Regieklappe auf einem Tischchen mitten in der Halle
SURVEILLANCE = (13.0, 22.8)           # Regie: vor der Monitorwand (Suedwand)
ADMIN_TABLE = (30.2, 22.2)            # Arbeitszimmer: vor dem Schreibtisch mit dem Grundriss
FREEPLAY = (21.6, 18.6)

FIXED = {
    # Ritual eskaliert (Reaktor): beide Enden des Seance-Tischs
    "Reactor/UpperHandConsole/0": (15.0, 4.2),
    "Reactor/LowerHandConsole/1": (19.0, 4.2),
    # Kamin raucht (O2): Kaminklappe + Lueftung im Arbeitszimmer
    "LifeSupp/NoOxyConsole/0": (29.6, 14.5),
    "Admin/NoOxyConsole/1": (33.3, 20.4),
    "Electrical/SwitchConsole/0": (6.9, 8.9),             # Sicherungskasten im Heizungskeller
    "Comms/FixCommsConsole/0": (26.3, 1.6),               # Funkraum, Ostwand
    "MedBay/MedScanner/0": (21.4, 21.4),                  # Schminkstuhl
    "Security/FixWiringConsole/5": (11.45, 22.4),         # Regie, Westwand (zu eng fuer die Automatik)
    "Nav/FixWiringConsole/3": (27.6, 7.3),                # Sternwarte, Suedwestecke
}

# Vents (Skeld-Ids, Netze): small 3 Netze, large dazu das Garten-Netz
VENTS = {
    "small": {0: (5.6, 6.6), 1: (5.6, 12.6), 2: (9.6, 22.8),
              3: (21.8, 1.2), 5: (1.4, 17.8), 6: (22.2, 20.8),
              7: (33.1, 7.2), 8: (33.1, 17.2), 9: (33.1, 23.2)},
    "large": {0: (5.6, 6.6), 1: (5.6, 12.6), 2: (9.6, 22.8),
              3: (21.8, 1.2), 5: (1.4, 17.8), 6: (22.2, 20.8),
              7: (33.1, 7.2), 8: (33.1, 17.2), 9: (33.1, 23.2),
              10: (10.8, 34.8), 11: (26.0, 34.8), 12: (48.8, 3.2), 13: (48.8, 34.8)},
}
VENT_NETS = {
    "small": [[0, 1, 2], [3, 5, 6], [7, 8, 9]],
    "large": [[0, 1, 2], [3, 5, 6], [7, 8, 9], [10, 11, 12, 13]],
}

CAMERAS = {
    "small": [(11.7, 9.4), (25.4, 9.2), (16.0, 0.6), (2.0, 14.6)],
    "large": [(11.7, 9.4), (16.0, 0.6), (12.6, 24.6), (40.6, 14.6)],
}

# Geheimgaenge (Mechanik spaeter): Wand-Durchgaenge (Achse, Lage, von, bis) oder Sprungpaare
SECRETS = [
    ("tapestry", "wall", ("y", 8, 20.0, 22.0), "seance>hall", B),            # Wandteppich, Einbahn
    ("bookcase", "wall", ("x", 11, 15.5, 17.5), "both", B),                  # Drehbuecherregal
    ("dumbwaiter", "jump", ((6.2, 0.7), (26.3, 6.8)), "kitchen>radio", B),   # Speiseaufzug, Einbahn nach oben
    ("tunnel", "jump", ((47.0, 35.3), (1.2, 23.3)), "crypt>chapel", L),      # Gruft-Tunnel, Einbahn
]

# Mitternachtsuhr (Mechanik spaeter): die Standuhr in der Halle
CLOCK = (12.35, 8.7)

# ------------------------------------------------------------------ Hindernisse (Plan-Meter)
# ("rect", x0, y0, x1, y1) | ("circle", cx, cy, r) | ("ellipse", cx, cy, rx, ry); Art = Sprite-Art.
# OPAQUE sperrt Weg und Sicht, GLASS nur den Weg. Varianten wie bei den Bereichen.
OPAQUE = [
    (("rect", 15.0, 8.2, 19.0, 10.4), "freitreppe", B),
    (("rect", 12.0, 8.25, 12.7, 8.7), "standuhr", B),
    (("rect", 0.3, 0.25, 2.8, 0.85), "herd", B),
    (("rect", 23.3, 0.25, 25.5, 0.85), "funktisch", B),
    (("rect", 32.0, 0.25, 33.75, 1.2), "kisten", B),
    (("rect", 0.25, 9.0, 1.8, 10.8), "kessel", B),
    (("rect", 0.25, 15.0, 0.7, 18.2), "buecherregal", B),
    (("rect", 6.0, 18.3, 10.7, 18.75), "buecherregal", B),
    (("rect", 0.25, 20.6, 1.0, 22.6), "altar", B),
    (("rect", 11.3, 23.25, 14.7, 23.8), "monitorwand", B),
    (("rect", 19.3, 23.25, 21.6, 23.8), "schminktisch", B),
    (("rect", 26.3, 8.25, 28.4, 8.7), "gewehrschrank", B),
    (("rect", 30.5, 13.25, 32.8, 13.85), "kamin", B),
    (("rect", 31.0, 18.25, 33.6, 18.7), "buecherregal", B),
    # Garten
    (("rect", 0.6, 33.6, 3.6, 35.4), "aggregat", L),
    (("rect", 6.5, 30.0, 10.0, 33.0), "zelt", L),
    (("rect", 35.5, 32.5, 39.7, 33.1), "hecke", L),
    (("rect", 35.5, 33.1, 36.1, 35.7), "hecke", L),
]
GLASS = [
    (("ellipse", 20.3, 16.8, 0.55, 0.4), "filmkamera", B),
    (("circle", 12.4, 18.6, 0.35), "scheinwerfer", B),
    (("circle", 21.8, 9.4, 0.35), "scheinwerfer", B),
    (("ellipse", 17.0, 4.2, 1.4, 0.85), "seance_tisch", B),
    (("circle", 12.1, 1.0, 0.25), "kandelaber", B),
    (("circle", 22.0, 6.9, 0.25), "kandelaber", B),
    (("rect", 2.2, 3.6, 4.6, 5.0), "kuechentisch", B),
    (("circle", 9.0, 1.3, 0.55), "waschzuber", B),
    (("rect", 28.0, 2.6, 29.2, 3.6), "requisiten", B),
    (("circle", 28.6, 6.0, 0.55), "teleskop", B),
    (("rect", 5.2, 12.6, 7.0, 13.6), "kohlen", B),
    (("rect", 4.5, 16.0, 6.5, 17.0), "lesetisch", B),
    (("circle", 2.4, 15.5, 0.25), "kandelaber", B),
    (("rect", 3.5, 20.6, 7.5, 21.1), "kirchenbank", B),
    (("rect", 3.5, 22.3, 7.5, 22.8), "kirchenbank", B),
    (("circle", 9.6, 20.4, 0.25), "kandelaber", B),
    (("rect", 32.6, 11.0, 33.7, 12.6), "baer", B),
    (("rect", 30.0, 15.4, 30.9, 16.2), "sessel", B),
    (("rect", 31.6, 16.4, 32.5, 17.2), "sessel", B),
    (("rect", 29.0, 22.7, 31.4, 23.6), "schreibtisch", B),
    # Garten
    (("rect", 19.5, 28.8, 22.0, 29.6), "catering", L),
    (("rect", 13.0, 29.35, 15.0, 29.65), "absperrung", L),
    (("circle", 37.0, 10.0, 0.4), "urne", L),
    (("rect", 38.6, 20.5, 39.5, 22.5), "gartenbank", L),
    (("rect", 42.0, 8.5, 48.0, 9.4), "pflanztisch", L),
    (("rect", 42.0, 4.0, 46.0, 4.9), "pflanztisch", L),
    (("circle", 31.0, 31.0, 1.2), "brunnen", L),
    (("rect", 42.5, 16.4, 43.3, 16.7), "grabstein", L),
    (("rect", 45.0, 16.4, 45.8, 16.7), "grabstein", L),
    (("rect", 47.5, 16.4, 48.3, 16.7), "grabstein", L),
    (("rect", 42.5, 20.4, 43.3, 20.7), "grabstein", L),
    (("rect", 45.0, 20.4, 45.8, 20.7), "grabstein", L),
    (("rect", 47.5, 20.4, 48.3, 20.7), "grabstein", L),
    (("rect", 42.5, 24.4, 43.3, 24.7), "grabstein", L),
    (("rect", 45.0, 24.4, 45.8, 24.7), "grabstein", L),
    (("rect", 41.2, 31.0, 42.0, 31.3), "grabstein", L),
    (("circle", 43.0, 34.5, 0.25), "kandelaber", L),
    (("rect", 45.2, 30.9, 47.2, 31.6), "sarg", L),
    (("rect", 45.2, 33.4, 47.2, 34.1), "sarg", L),
]


def in_variant(variants, v):
    return v in variants
