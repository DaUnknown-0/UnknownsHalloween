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
    # seit 15.10. L-foermig: der alte Westflur (8-11 x 8-14) ist der Nordarm, der Heizungskeller wird ausgeschnitten
    ("library", "Long Library", (0, 8, 11, 19), B, {"small": "Records", "large": "Records"}),
    ("chapel", "Chapel", (0, 19, 11, 24), B, {"small": "Shields", "large": "Lounge"}),
    # seit 15.10. T-foermig: das alte Vestibuel (15-19 x 20-24) ist der Suedarm mit der Haustuer; Regie und Maske
    # liegen darin und werden ausgeschnitten
    ("hall", "Entrance Hall", (11, 8, 23, 24), B, {"small": "Cafeteria", "large": "Cafeteria"}),
    ("booth", "Director's Booth", (11, 20, 15, 24), B, {"small": "Security", "large": "Security"}),
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
    ("y", 8, 8.2, 10.7, {"small": ("door", "UpperEngine"), "large": "open"}),                   # Laundry - Library (Nordarm)
    ("y", 8, 23.5, 25.5, {"small": "open", "large": "open"}),                                   # Radio - Gallery
    ("x", 27, 0.75, 3.25, {"small": ("door", "Storage"), "large": "open"}),                     # Radio - Box Room
    ("y", 4, 29.5, 32.0, {"small": ("door", "Storage"), "large": "open"}),                      # Box Room - Observatory
    ("y", 8, 30.0, 32.5, {"small": ("door", "Storage")}),                                       # Observatory - Trophy (gross seit 25.10. zugemauert: Wand fuer Geweihe und Fledermaeuse)
    ("y", 8, 2.0, 4.5, {"small": ("door", "LowerEngine"), "large": ("door", "LowerEngine")}),   # Kitchen - Boiler
    # Mitte
    ("x", 8, 9.5, 12.0, {"small": ("door", "Electrical"), "large": ("door", "Electrical")}),    # Library (Nordarm) - Boiler
    ("x", 11, 10.25, 12.75, {"small": ("door", "Cafeteria"), "large": ("door", "Cafeteria")}), # Library (Nordarm) - Hall
    ("y", 14, 2.0, 4.5, {"small": "open", "large": "open"}),                                    # Boiler - Library
    ("y", 19, 3.0, 5.5, {"small": ("door", "Cafeteria"), "large": "open"}),                     # Library - Chapel (klein: Tuer statt Halle-Vestibuel)
    ("x", 23, 10.25, 12.75, {"small": ("door", "Cafeteria"), "large": ("door", "Cafeteria")}), # Hall - Gallery
    ("y", 20, 11.75, 14.25, {"small": ("door", "Security"), "large": ("door", "Security")}),   # Hall - Booth
    ("x", 15, 21.5, 23.5, {"small": "open", "large": "open"}),                                  # Booth - Hall (Suedarm)
    ("x", 19, 21.5, 23.5, {"small": "open", "large": "open"}),                                  # Hall (Suedarm) - Makeup
    ("x", 23, 21.0, 23.5, {"small": ("door", "MedBay"), "large": ("door", "MedBay")}),         # Makeup - Gallery
    ("x", 26, 9.5, 12.0, {"small": "open", "large": "open"}),                                   # Gallery - Trophy
    ("x", 26, 14.5, 16.5, {"small": "open", "large": "open"}),                                  # Gallery - Fireplace
    ("x", 26, 20.0, 22.5, {"small": "open", "large": "open"}),                                  # Gallery - Study
    ("y", 13, 27.0, 29.5, {"small": "open", "large": "open"}),                                  # Trophy - Fireplace
    ("y", 18, 27.0, 29.5, {"small": "open", "large": "open"}),                                  # Fireplace - Study
    # Aussen (nur gross; in "small" verrammelt, siehe BARRICADES)
    ("y", 24, 15.75, 18.25, {"large": ("door", "Cafeteria")}),                                  # Hall (Suedarm) - Driveway (Haustuer)
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

# Tuerart je Oeffnung (Grafik, villa_doors.py): Garten-Tore aus Schmiedeeisen, Haus- und Hintertuer schwer,
# alles andere Holz mit Messing. Schluessel = (Achse, Lage, Mitte) wie das DoorSlot-Label.
DOOR_KIND = {("x", 40, 6.25): "iron", ("y", 26, 37): "iron", ("y", 28, 47): "iron", ("x", 12, 27.75): "iron",
             ("y", 24, 17): "heavy", ("y", 24, 4.25): "heavy"}

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
    "Reactor/UpperHandConsole/0": (12.3, 3.2),           # 25.10.: an der Suedseite des Tischs in der Nordwestecke
    "Reactor/LowerHandConsole/1": (13.8, 3.2),
    "Reactor/UnlockManifoldsConsole/2": (20.4, 0.6),      # Puzzle-Box rechts neben dem Kamin (stand am Tisch)
    # Kamin raucht (O2): Kaminklappe + Lueftung im Arbeitszimmer
    "LifeSupp/NoOxyConsole/0": (29.6, 14.5),
    "Admin/NoOxyConsole/1": (33.3, 20.4),
    "Electrical/SwitchConsole/0": (6.9, 8.9),             # Sicherungskasten im Heizungskeller
    "Comms/FixCommsConsole/0": (26.3, 1.6),               # Funkraum, Ostwand
    "MedBay/MedScanner/0": (21.4, 21.4),                  # Schminkstuhl
    "Security/FixWiringConsole/5": (11.45, 22.4),         # Regie, Westwand (zu eng fuer die Automatik)
    "Nav/FixWiringConsole/3": (27.6, 7.3),                # Sternwarte, Suedwestecke
    # Aufgabe aus Airship (Atlas ForeignTasks): Burger braten am Herd der Kueche (User 15.10.)
    "LowerEngine/MakeBurger/0": (1.55, 1.25),
}

# Feste Konsolen nur einer Variante (seit der Einrichtung 15.10. finden sie sonst keinen freien Wandplatz)
FIXED_SMALL = {
    "Storage/gasCanConsole/0": (31.4, 1.4),              # Prop Store, zwischen Kleiderstange und Kisten
    "Storage/FixWiringConsole/1": (27.6, 3.65),          # Prop Store, Suedwestecke
    "Storage/AirlockConsole/0": (31.3, 3.7),             # Prop Store, Suedwand
}
# Nur gross: Crew Camp (UpperEngine) - Umleitung neben die Triebwerksausrichtung an der Hauswand (User 24.10.)
FIXED_LARGE = {
    "UpperEngine/DivertPowerConsole/1": (7.1, 24.6),
}
FIXED_BOTH_EXTRA = {
    "Security/DivertPowerConsole/1": (12.6, 21.2),       # Regie
    "MedBay/MedBayConsole/0": (22.5, 20.7),              # Maske, rechts vom Kunstblutregal
    "LifeSupp/DivertPowerConsole/1": (29.2, 17.45),      # Kaminzimmer, Suedwand (25.10.: in der Suedostecke lag Vent 8 in ihrer Fussflaeche)
}
FIXED.update(FIXED_BOTH_EXTRA)

# Vents (Skeld-Ids, Netze): small 3 Netze, large dazu das Garten-Netz
VENTS = {
    "small": {0: (5.6, 6.6), 1: (6.0, 11.4), 2: (9.6, 22.8),
              3: (21.8, 1.2), 5: (1.0, 18.45), 6: (22.3, 23.1),
              7: (33.1, 7.2), 8: (33.1, 17.2), 9: (33.1, 23.2)},
    "large": {0: (5.6, 6.6), 1: (6.0, 11.4), 2: (9.6, 22.8),
              3: (21.8, 1.2), 5: (1.0, 18.45), 6: (22.3, 23.1),
              7: (33.1, 7.2), 8: (33.1, 17.2), 9: (33.1, 23.2),
              10: (10.8, 34.8), 11: (26.0, 34.8), 12: (48.8, 3.2), 13: (48.8, 34.8)},
}
VENT_NETS = {
    "small": [[0, 1, 2], [3, 5, 6], [7, 8, 9]],
    "large": [[0, 1, 2], [3, 5, 6], [7, 8, 9], [10, 11, 12, 13]],
}

CAMERAS = {
    "small": [(11.7, 9.4), (25.4, 9.2), (11.75, 0.55), (2.0, 14.6)],      # Seance-Kamera seit 25.10. in der Nordwestecke (stand vor dem Kamin)
    "large": [(11.7, 9.4), (11.75, 0.55), (12.6, 24.6), (40.6, 14.6)],
}

# Geheimgaenge (Mechanik, Schritt 4 des Audits 15.10.): Schluessel, Moebel-Art am Eingang (bewegt sich beim
# Durchgang; der Speiseaufzug hat an beiden Enden eine Klappe), Eingang, Ausgang (Plan-Meter, jeweils einen
# Schritt vor dem Moebel), beide Richtungen, Varianten. Use-Knopf "ENTER" in 1 m Naehe, Teleport nach 0,5 s.
SECRETS = [
    ("tapestry", "wandteppich", (21.0, 7.1), (21.0, 9.45), False, B),         # Seance -> Halle, Einbahn
    ("bookcase", "drehregal", (10.0, 16.5), (11.8, 16.5), True, B),          # Bibliothek <-> Halle
    ("dumbwaiter", "speiseaufzug", (6.3, 5.5), (26.3, 6.8), False, B),       # Kueche -> Funkraum, Einbahn
    ("tunnel", "tunneleingang", (44.8, 34.2), (1.4, 22.7), False, L),        # Gruft -> Kapelle, Einbahn; Ausgang einen Schritt VOR der Klappe (lag 17.10. im Hindernis 0.8-1.6/23.1-23.7, man steckte fest)
]

# Mitternachtsuhr (Mechanik spaeter): die Standuhr in der Halle
CLOCK = (12.35, 9.25)                 # 25.10.: Hallen-Nordwand 0,6 m dicker (THICK_WALLS)

# Dickere Wandmasse (Plan-Rechtecke, nicht begehbar): die Wandflaeche (villa_floor_map) reicht so hoch wie die Masse, man
# sieht nicht mehr ueber die Wand in den Raum dahinter (User 25.10., Hallen-Nordwand zum Seance Parlour)
# Konsolen, die es auf Hollowmere nicht gibt (25.10.: das Fledermaus-Fenster; HollowmereWorld nimmt den Task "Clear Asteroids"
# aus den Task-Listen, sonst bekaeme jemand einen unloesbaren Task)
DROP_CONSOLES = {"Weapons/WeaponConsole/0"}
# Wagen-Konsolen, die naeher an die Wand ruecken (0,3 m nach Norden, wo Platz ist; User 25.10. "alle DAILIES nach oben")
NUDGE_NORTH = ("DataConsole", "UploadDataConsole")

THICK_WALLS = [(11.0, 8.0, 23.0, 8.8),        # Halle, Nordwand zum Seance Parlour
               (26.0, 8.0, 34.0, 8.8)]        # Trophy Room, Nordwand (Geweihe, Fledermaeuse); Tueroeffnungen bleiben frei

# ------------------------------------------------------------------ Hindernisse (Plan-Meter)
# ("rect", x0, y0, x1, y1) | ("circle", cx, cy, r) | ("ellipse", cx, cy, rx, ry); Art = Sprite-Art.
# OPAQUE sperrt Weg und Sicht, GLASS nur den Weg. Varianten wie bei den Bereichen.
OPAQUE = [
    (("rect", 15.0, 8.2, 19.0, 10.4), "freitreppe", B),
    (("rect", 15.2, 9.7, 18.8, 10.9), "treppensperre", B),     # Moebel am Treppenfuss: oben ist nichts (User 15.10.)
    (("rect", 12.0, 8.85, 12.7, 9.3), "standuhr", B),
    (("rect", 0.3, 0.25, 2.8, 0.85), "herd", B),
    (("rect", 23.3, 0.25, 25.5, 0.85), "funktisch", B),
    (("rect", 32.0, 0.25, 33.75, 1.2), "kisten", B),
    (("rect", 0.25, 9.0, 1.8, 10.8), "kessel", B),
    (("rect", 0.25, 15.0, 0.7, 18.2), "buecherregal", B),
    (("rect", 10.55, 15.5, 11.0, 17.5), "drehregal", B),          # Long Library, Ostwand: Drehbuecherregal (Geheimgang)
    (("rect", 6.0, 18.3, 10.7, 18.75), "buecherregal", B),
    (("rect", 7.0, 19.25, 9.4, 19.85), "altar", B),             # Chapel, Nordwand mit Wandkreuz (User 24.10.: wie eine echte Kirche, Baenke blicken zum Altar)
    (("rect", 11.3, 23.25, 14.7, 23.8), "monitorwand", B),
    (("rect", 19.9, 23.3, 21.6, 23.8), "dosenregal", B),         # Makeup, Suedwand: Regal mit Schminkdosen, Puder, Tiegeln (User 24.10.)
    (("rect", 26.3, 8.85, 28.4, 9.3), "gewehrschrank", B),
    (("rect", 30.5, 13.25, 32.8, 13.85), "kamin", B),
    (("rect", 15.0, 0.25, 19.0, 1.0), "kamin_gross", B),            # Seance, Nordwand (25.10.: statt Ouija-Wand), Baerenfell davor im Boden
    (("rect", 31.0, 18.25, 33.6, 18.7), "buecherregal", B),
    # Garten
    (("rect", 0.6, 33.6, 3.6, 35.4), "aggregat", L),
    (("rect", 6.5, 30.0, 10.0, 33.0), "zelt", L),
]
GLASS = [
    (("ellipse", 20.3, 16.8, 0.55, 0.4), "filmkamera", B),
    (("circle", 12.4, 18.6, 0.35), "scheinwerfer", B),
    (("circle", 21.8, 9.4, 0.35), "scheinwerfer", B),
    (("ellipse", 13.0, 1.95, 1.4, 0.85), "seance_tisch", B),     # 25.10.: Nordwestecke, ganz nach oben (Raummitte = Pentagramm)
    (("rect", 14.9, 1.65, 15.8, 2.45), "sessel", B),              # Seance: zwei Sessel vor dem Kamin, das Baerenfell dazwischen
    (("rect", 18.2, 1.65, 19.1, 2.45), "sessel", B),
    (("circle", 19.55, 0.75, 0.25), "kandelaber", B),             # Seance: rechts neben dem Kamin (25.10.)
    (("circle", 22.0, 6.9, 0.25), "kandelaber", B),
    (("rect", 2.2, 3.6, 4.6, 5.0), "kuechentisch", B),
    (("circle", 9.0, 1.3, 0.55), "waschzuber", B),
    (("rect", 29.2, 1.6, 31.2, 2.5), "requisiten", B),            # Box Room, Raummitte (25.10.)
    (("circle", 28.6, 6.0, 0.55), "teleskop", B),
    (("rect", 5.2, 12.6, 7.0, 13.6), "kohlen", B),
    (("rect", 4.5, 16.0, 6.5, 17.0), "lesetisch", B),
    (("circle", 2.4, 15.5, 0.25), "kandelaber", B),
    (("rect", 5.8, 20.9, 7.8, 21.35), "kirchenbank", B),         # Chapel: zwei Bankbloecke mit Mittelgang zum Altar
    (("rect", 8.6, 20.9, 10.6, 21.35), "kirchenbank", B),
    (("rect", 5.8, 21.9, 7.8, 22.35), "kirchenbank", B),
    (("rect", 8.6, 21.9, 10.6, 22.35), "kirchenbank", B),
    (("circle", 6.55, 19.7, 0.25), "kandelaber", B),             # links und rechts vom Altar
    (("circle", 9.85, 19.7, 0.25), "kandelaber", B),
    (("rect", 32.6, 11.0, 33.7, 12.6), "baer", B),
    (("rect", 30.0, 15.4, 30.9, 16.2), "sessel", B),
    (("rect", 33.25, 18.8, 33.7, 19.7), "safe", B),                  # Study, Ostwand (25.10.: vorher Westwand mit Sichtschatten)
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
    (("rect", 42.55, 16.25, 43.25, 16.70), "weeping_angel", L),
    (("rect", 45.05, 16.25, 45.75, 16.70), "weeping_angel", L),
    (("rect", 47.55, 16.25, 48.25, 16.70), "weeping_angel", L),
    (("rect", 42.55, 20.25, 43.25, 20.70), "weeping_angel", L),
    (("rect", 45.05, 20.25, 45.75, 20.70), "weeping_angel", L),
    (("rect", 47.55, 20.25, 48.25, 20.70), "weeping_angel", L),
    (("rect", 42.55, 24.25, 43.25, 24.70), "weeping_angel", L),
    (("rect", 45.05, 24.25, 45.75, 24.70), "weeping_angel", L),
    (("rect", 41.25, 30.85, 41.95, 31.30), "weeping_angel", L),
    (("circle", 43.0, 34.5, 0.25), "kandelaber", L),
    (("rect", 45.2, 30.9, 47.2, 31.6), "sarg", L),
    (("rect", 45.2, 33.4, 47.2, 34.1), "sarg", L),
]


# ------------------------------------------------------------------ Einrichtung seit dem Audit 15.10. (Schritt 2)
# Gleiche Form wie oben. DECOR = Objekte ohne Kollision (Wandbilder, Haengendes, Umgestuerztes, Bodenkram); sie
# werden gezeichnet und sortiert wie Props, sperren aber weder Weg noch Sicht.
OPAQUE += [
    (("rect", 10.1, 1.2, 10.75, 2.4), "kupferkessel", B),           # Laundry, Ostwand
    (("rect", 26.3, 4.3, 26.75, 5.9), "bandregal", B),                # Radio Room, Ostwand (stand bis 21.10. vor der Tuer, bis 24.10. frei mitten im Raum)
    (("rect", 33.3, 1.6, 33.75, 3.6), "maskenregal", B),             # Prop Store, Ostwand
    (("rect", 8.25, 12.2, 8.7, 13.9), "garderobe", B),               # Long Library, Nordarm Westwand
    (("rect", 0.4, 19.3, 1.2, 19.9), "engelsstatue_tuch", B),        # Chapel, Nordwestecke
    (("rect", 15.25, 22.5, 15.7, 23.8), "garderobe", B),             # Entrance Hall, Suedarm Westwand
    (("rect", 21.4, 19.3, 22.7, 19.8), "muellcontainer", B),         # Entrance Hall, Suedwand vor der Maske
    (("rect", 19.3, 20.25, 21.9, 20.7), "schminkspiegel", B),        # Makeup, Nordwand: Schminktisch mit Gluehbirnenspiegel (User 24.10.: Garderobe wie frueher)
    (("rect", 35.0, 3.0, 37.5, 5.0), "kamerakran", L),               # Terrace
    (("rect", 38.6, 24.0, 39.6, 25.0), "statue_schleier", L),        # Terrace, Suedostecke
    (("rect", 12.6, 24.6, 15.4, 26.3), "van", L),                    # Driveway
    (("rect", 1.0, 26.0, 4.0, 28.8), "zelt_aufgeschlitzt", L),       # Crew Camp
    (("rect", 10.8, 24.4, 11.7, 25.6), "dixi", L),                   # Crew Camp, Ostwand
    (("rect", 47.2, 3.6, 49.0, 5.2), "riesenpflanze", L),            # Greenhouse
    (("rect", 44.3, 34.6, 45.3, 35.7), "tunneleingang", L),          # Family Crypt, Suedwestecke
    (("rect", 0.8, 23.1, 1.6, 23.7), "tunnelausgang", L),            # Chapel, Suedwestecke: das andere Tunnelende
]
GLASS += [
    (("rect", 5.6, 1.0, 6.4, 1.8), "hackblock", B),                  # Kitchen
    (("rect", 0.3, 6.4, 1.7, 7.6), "craftservice", B),               # Kitchen, Suedwestecke (stand bis 24.10. vor der Waschkuechentuer)
    (("rect", 7.3, 0.3, 8.35, 1.05), "mangel", B),                   # Laundry, Nordwestecke (stand bis 24.10. vor der Kuechentuer)
    (("rect", 7.3, 7.0, 8.0, 7.75), "seifenkisten", B),              # Laundry, Suedwestecke
    (("circle", 13.0, 6.5, 0.35), "kristallkugel_tisch", B),         # Seance Parlour
    (("rect", 21.85, 5.75, 22.6, 6.4), "phonograph", B),             # Seance Parlour, Ostwand suedlich der Radio-Oeffnung (25.10.)
    (("rect", 26.3, 3.2, 26.75, 4.0), "walkie_station", B),          # Radio Room, Ostwand
    (("circle", 24.4, 2.2, 0.3), "drehstuhl", B),                    # Radio Room
    (("rect", 28.5, 0.3, 31.0, 0.7), "kleiderstange", B),            # Prop Store, Nordwand
    (("circle", 28.4, 3.2, 0.3), "schneiderpuppe", B),           # Prop Store / Box Room (25.10.: stand im neuen Requisitentisch)
    (("rect", 32.2, 2.6, 33.0, 3.7), "sarg_angelehnt", B),           # Prop Store
    (("rect", 27.3, 0.3, 28.1, 0.72), "nebelmaschine", B),           # Prop Store, Nordwestecke (stand bis 24.10. vor der Tuer zur Sternwarte)
    (("circle", 31.5, 5.0, 0.35), "orrery", B),                      # Observatory
    (("rect", 33.2, 4.6, 33.75, 5.4), "buecherstapel", B),           # Observatory, Ostwand (lag bis 24.10. neben Vent 7)
    (("rect", 6.9, 17.6, 7.3, 18.3), "leiter", B),                   # Long Library, am Suedregal
    (("circle", 2.0, 17.8, 0.3), "globus", B),                       # Long Library
    (("rect", 8.0, 15.2, 8.9, 16.0), "lesesessel", B),               # Long Library
    (("rect", 3.2, 18.2, 3.8, 18.75), "buecherstapel", B),           # Long Library, Suedwand
    (("circle", 10.4, 8.6, 0.2), "laterne", B),                      # Long Library, Nordarm
    (("rect", 5.8, 22.9, 7.8, 23.35), "zersplitterte_bank", B),      # Chapel, dritte Reihe links (rechts liegt Vent 2)
    (("rect", 13.2, 12.8, 14.0, 13.6), "regiestuhl", B),             # Entrance Hall
    (("ellipse", 14.0, 15.5, 0.8, 0.6), "kronleuchter_boden", B),    # Entrance Hall, abgestuerzt
    (("rect", 14.1, 20.4, 14.75, 21.1), "regiestuhl_director", B),   # Director's Booth
    (("rect", 11.3, 20.5, 11.75, 21.8), "mischpult", B),             # Director's Booth, Westwand
    (("rect", 19.3, 20.3, 19.75, 21.3), "perueckenkoepfe", B),       # Makeup, Westwand
    (("circle", 24.0, 9.3, 0.25), "buesten_saeule", B),              # Portrait Gallery
    (("rect", 25.2, 19.0, 25.8, 19.6), "ruestung", B),               # Portrait Gallery
    (("rect", 23.3, 23.0, 23.8, 23.7), "standspiegel", B),           # Portrait Gallery, Suedwestecke
    (("rect", 28.5, 10.2, 31.3, 11.7), "billardtisch", B),           # Trophy Room
    (("circle", 27.0, 11.8, 0.35), "globusbar", B),                  # Trophy Room
    (("circle", 31.3, 15.6, 0.25), "beistelltisch", B),              # Fireplace Room, zwischen den Sesseln
    (("rect", 33.2, 13.3, 33.6, 13.8), "schuerhaken", B),            # Fireplace Room, neben dem Kamin
    (("rect", 33.0, 14.0, 33.75, 14.8), "holzkorb", B),              # Fireplace Room, Ostwand
    (("rect", 26.4, 16.6, 27.2, 17.5), "schaukelstuhl", B),          # Fireplace Room
    (("rect", 26.3, 22.6, 27.4, 23.7), "aktenkisten", B),            # Study, Suedwestecke
    (("circle", 37.0, 14.0, 0.6), "gartentisch", L),                 # Terrace
    (("rect", 34.3, 7.0, 34.9, 8.0), "kuebelpflanze", L),            # Terrace, Hauswand
    (("rect", 34.3, 22.0, 34.9, 23.0), "kuebelpflanze", L),          # Terrace, Hauswand
    (("circle", 37.0, 20.0, 0.2), "laterne", L),                     # Terrace
    (("circle", 22.5, 25.5, 0.3), "lichtstativ", L),                 # Driveway
    (("circle", 16.5, 28.0, 0.3), "lichtstativ", L),                 # Driveway
    (("rect", 6.0, 26.2, 7.8, 27.0), "campingtisch", L),             # Crew Camp
    (("rect", 0.9, 30.2, 4.3, 31.9), "jeep", L),                     # Crew Camp, Westseite (User 24.10.)
    (("circle", 5.0, 34.6, 0.45), "kabeltrommel", L),                # Crew Camp
    (("circle", 9.0, 27.0, 0.35), "scheinwerfer", L),                # Crew Camp
    (("rect", 40.4, 10.6, 41.2, 11.5), "giesskannen", L),            # Greenhouse, Suedwestecke
    (("circle", 48.8, 10.8, 0.4), "schlauchtrommel", L),             # Greenhouse, Suedostecke
    (("circle", 26.5, 33.0, 0.35), "sonnenuhr", L),                  # Fountain Court
    (("circle", 34.5, 28.5, 0.2), "laterne", L),                     # Fountain Court
    (("circle", 27.5, 28.5, 0.2), "laterne", L),                     # Fountain Court
    (("rect", 41.2, 26.6, 42.6, 28.6), "offenes_grab", L),           # Graveyard
    (("rect", 44.0, 24.4, 44.9, 24.7), "grabstein_hausherr", L),     # Graveyard
    (("rect", 47.8, 30.4, 49.3, 31.4), "sarkophag", L),              # Family Crypt
]
DECOR = [
    (("rect", 3.2, 0.25, 5.2, 0.6), "topfregal", B),                 # Kitchen, Nordwand
    (("rect", 6.75, 5.0, 7.0, 6.0), "speiseaufzug", B),              # Kitchen, Ostwand (Geheimgang)
    (("rect", 26.75, 6.3, 27.0, 7.3), "speiseaufzug", B),            # Radio Room, Ostwand: das andere Ende des Aufzugs
    (("rect", 0.6, 2.6, 1.6, 2.9), "fleischerhaken", B),             # Kitchen, haengt von der Decke
    (("rect", 7.4, 6.2, 10.6, 6.5), "waescheleine", B),              # Laundry, Laken wie Gestalten
    (("rect", 20.0, 7.5, 22.0, 7.75), "wandteppich", B),             # Seance, Suedwand (Geheimgang zur Halle)
    (("rect", 14.0, 6.6, 14.9, 7.2), "umgestuerzter_stuhl", B),      # Seance
    (("rect", 24.8, 5.6, 25.8, 6.4), "tonband_boden", B),            # Radio Room, abgewickelte Spule
    (("rect", 29.5, 4.25, 31.5, 4.5), "sternkarte_datum", B),        # Observatory, Nordwand
    (("rect", 2.5, 8.25, 6.0, 8.55), "rohre", B),                    # Boiler Room, Nordwand
    (("rect", 0.25, 11.5, 0.55, 12.5), "handabdruck_russ", B),       # Boiler Room, Westwand
    (("rect", 10.75, 12.9, 11.0, 13.9), "klingelbrett", B),          # Long Library, Nordarm Ostwand
    (("rect", 4.0, 15.2, 4.5, 15.5), "rauchendes_buch", B),          # Long Library, am Boden
    (("rect", 23.25, 13.5, 23.45, 14.5), "portrait", B),             # Portrait Gallery, Westwand
    (("rect", 23.25, 15.5, 23.45, 16.5), "portrait", B),
    (("rect", 23.25, 17.5, 23.45, 18.5), "portrait", B),
    (("rect", 25.55, 12.3, 25.75, 13.3), "portrait", B),             # Portrait Gallery, Ostwand
    (("rect", 25.55, 17.0, 25.75, 18.0), "portrait", B),
    (("rect", 25.55, 23.0, 25.75, 23.8), "portrait", B),
    (("rect", 23.25, 19.5, 23.45, 20.5), "leerer_rahmen", B),        # Portrait Gallery, Westwand
    (("rect", 29.0, 8.85, 31.0, 9.1), "geweihe", L),                 # Trophy Room, Nordwand (gross: an der zugemauerten Oeffnung)
    (("rect", 28.5, 8.85, 29.95, 9.1), "geweihe", ("small",)),       # klein: links neben der Tuer
    (("rect", 33.5, 8.8, 33.75, 9.8), "hirschkopf", B),              # Trophy Room, Ostwand
    (("rect", 31.5, 8.85, 33.0, 9.1), "fledermaeuse", L),            # Trophy Room, unter der Decke
    (("rect", 32.55, 8.85, 33.4, 9.1), "fledermaeuse", ("small",)),  # klein: rechts neben der Tuer
    (("rect", 31.5, 13.9, 31.8, 14.1), "kinderschuh", B),            # Fireplace Room, vor dem Kamin
    (("rect", 33.5, 21.2, 33.75, 22.0), "lueftungsgitter", B),       # Study, Ostwand
    (("rect", 29.6, 23.65, 30.2, 23.9), "schreibmaschine", B),      # Study, auf dem Schreibtisch (Standlinie vor dem Tisch, Hoehe mitgezeichnet)
    (("rect", 38.0, 2.3, 39.8, 2.6), "vogelschwarm", L),             # Terrace, auf der Balustrade
    (("rect", 7.2, 34.2, 8.8, 34.9), "schlafsack", L),               # Crew Camp
    (("rect", 49.55, 6.0, 49.75, 8.0), "kletterpflanzen", L),        # Greenhouse, Ostwand
    (("rect", 30.6, 32.25, 31.4, 32.45), "brunnen_blut", L),         # Fountain Court, rotes Wasser + Schleierstatue (vor dem Brunnen)
    (("rect", 42.5, 16.1, 43.3, 16.4), "kraehen", L),                # Graveyard, auf den Steinen
    (("rect", 44.25, 29.0, 44.45, 32.0), "nischen_urnen", L),        # Family Crypt, Westwand
    (("rect", 49.55, 29.0, 49.75, 32.0), "nischen_urnen", L),        # Family Crypt, Ostwand
    (("rect", 44.6, 28.25, 44.9, 28.5), "wandfackel", L),            # Family Crypt, Nordwand
    (("rect", 49.1, 28.25, 49.4, 28.5), "wandfackel", L),
    (("rect", 48.0, 33.0, 48.6, 33.4), "zerbrochene_urne", L),       # Family Crypt, am Boden
]

# Kollision abweichend vom Zeichen-Rechteck (User 24.10.: "Hitbox anpassen"): (Art, Form) -> Kollisionsform. Das Sprite
# wird weiter aus der Form in OPAQUE/GLASS gezeichnet, gesperrt ist nur die Fussflaeche.
HITBOX = {
    ("teleskop", ("circle", 28.6, 6.0, 0.55)): ("circle", 28.6, 6.15, 0.3),          # nur das Stativ
    ("aggregat", ("rect", 0.6, 33.6, 3.6, 35.4)): ("rect", 1.1, 34.3, 3.55, 35.4),    # Fussflaeche statt Dach
    ("brunnen", ("circle", 31.0, 31.0, 1.2)): ("ellipse", 31.0, 31.05, 1.2, 0.75),   # Becken ist oval
    ("laterne", ("circle", 10.4, 8.6, 0.2)): ("circle", 10.4, 8.65, 0.12),
    ("baer", ("rect", 32.6, 11.0, 33.7, 12.6)): ("rect", 32.6, 12.0, 33.7, 12.6),     # 25.10.: nur der Sockel (Figur von vorn)
    ("laterne", ("circle", 37.0, 20.0, 0.2)): ("circle", 37.0, 20.05, 0.12),
    ("laterne", ("circle", 34.5, 28.5, 0.2)): ("circle", 34.5, 28.55, 0.12),
    ("laterne", ("circle", 27.5, 28.5, 0.2)): ("circle", 27.5, 28.55, 0.12),
}


def hit_shape(s, kind):
    return HITBOX.get((kind, s), s)


def in_variant(variants, v):
    return v in variants
