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
    "Nav/FixWiringConsole/3": (33.4, 4.65),               # Sternwarte, Nordostecke an der Wand (n78, 28.10. abends)
    # Aufgabe aus Airship (Atlas ForeignTasks): Burger braten am Herd der Kueche (User 15.10.)
    "LowerEngine/MakeBurger/0": (1.6, 1.35),             # 28.10.: der grosse Herd ist jetzt die Konsole selbst (n66)
    # 28.10. Feedback DrSuspect (Atlas-Reiter aus Airship, HollowmereMap.ForeignTasks)
    "Admin/UnlockSafe/0": (33.3, 19.75),                  # Tresor an der Ostwand, Tuer nach links (n33)
    "Electrical/PressureValve/0": (2.55, 10.75),          # Druckventil rechts neben dem Kessel (n64)
    "Admin/FixWiringConsole/2": (27.6, 18.75),            # Elektro auf die linke Raumseite (n33)
    "Weapons/UploadDataConsole/1": (31.85, 12.55),        # stand hinter dem Baeren (n18)
    "Nav/StabilizeSteeringConsole/0": (30.6, 6.15),       # Teleskop in die Raummitte, ersetzt das zweite Teleskop (n80/n81)
    "Nav/UploadDataConsole/0": (28.4, 7.45),
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
    "Storage/WaterBench/0": (44.0, 7.0),                  # Pflanzen giessen, Gewaechshaus (n24)
    "UpperEngine/Campfire/0": (5.2, 29.05),               # Marshmallows am Lagerfeuer (n62)
    "UpperEngine/CampGenerator/0": (9.2, 24.95),          # Generator im Crew Camp statt in der Kueche (n67)
    "MainHall/Catering/0": (18.8, 29.15),                 # Essen und Trinken, zwei Tische am Vorplatz (n56)
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

# Kameras, die in die andere Richtung schauen (28.10., n02/n25/n37): Index in CAMERAS je Variante
CAMERA_FLIP = {"small": {0, 2}, "large": {0, 1, 3}}
# Objekte, deren Bild gespiegelt wird (28.10. abends: Licht zeigt in die andere Richtung), (Art, Form) wie in OPAQUE/GLASS
FLIP = {("scheinwerfer", ("circle", 21.8, 9.4, 0.35)), ("lichtstativ", ("circle", 22.5, 25.5, 0.3))}

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
# nur gross (28.10., n67): der Generator steht nicht mehr in der Kueche, "Tune the Generator" ist ein eigener Reiter im Crew Camp;
# HollowmereWorld.TrimTasks nimmt "Align Engine Output" auf der grossen Manor aus den Listen
DROP_CONSOLES_LARGE = {"LowerEngine/AlignEngineConsole/1", "UpperEngine/AlignEngineConsole/0"}
# Wagen-Konsolen, die naeher an die Wand ruecken (0,3 m nach Norden, wo Platz ist; User 25.10. "alle DAILIES nach oben")
NUDGE_NORTH = ("DataConsole", "UploadDataConsole")

THICK_WALLS = [(11.0, 8.0, 23.0, 8.8),        # Halle, Nordwand zum Seance Parlour
               (26.0, 8.0, 34.0, 8.8),        # Trophy Room, Nordwand (Geweihe, Fledermaeuse); Tueroeffnungen bleiben frei
               (26.0, 13.0, 34.0, 13.8)]      # Kaminzimmer, Nordwand (25.10.: "angedeutete Waende hochziehen")

# ------------------------------------------------------------------ Hindernisse (Plan-Meter)
# ("rect", x0, y0, x1, y1) | ("circle", cx, cy, r) | ("ellipse", cx, cy, rx, ry); Art = Sprite-Art.
# OPAQUE sperrt Weg und Sicht, GLASS nur den Weg. Varianten wie bei den Bereichen.
OPAQUE = [
    (("rect", 15.0, 8.2, 19.0, 10.4), "freitreppe", B),
    (("rect", 12.0, 8.85, 12.7, 9.3), "standuhr", B),
    (("rect", 23.3, 0.25, 25.5, 0.85), "funktisch", B),
    (("rect", 0.25, 9.0, 1.8, 10.8), "kessel", B),
    (("rect", 0.25, 15.0, 0.7, 18.2), "buecherregal", B),
    (("rect", 10.55, 15.5, 11.0, 17.5), "drehregal", B),          # Long Library, Ostwand: Drehbuecherregal (Geheimgang)
    (("rect", 6.0, 18.3, 10.7, 18.75), "buecherregal", B),
    (("rect", 7.0, 19.25, 9.4, 19.85), "altar", B),             # Chapel, Nordwand mit Wandkreuz (User 24.10.: wie eine echte Kirche, Baenke blicken zum Altar)
    (("rect", 11.3, 23.25, 14.7, 23.8), "monitorwand", B),
    (("rect", 19.9, 23.3, 21.6, 23.8), "dosenregal", B),         # Makeup, Suedwand: Regal mit Schminkdosen, Puder, Tiegeln (User 24.10.)
    (("rect", 30.5, 13.85, 32.8, 14.45), "kamin", B),                # Kaminzimmer (25.10.: vor die dicke Nordwand)
    (("rect", 15.0, 0.25, 19.0, 1.0), "kamin_gross", B),            # Seance, Nordwand (25.10.: statt Ouija-Wand), Baerenfell davor im Boden
    (("rect", 31.0, 18.25, 33.6, 18.7), "buecherregal", B),
    # Garten
    (("rect", 0.6, 33.6, 3.6, 35.4), "aggregat", L),
    (("rect", 6.5, 30.0, 10.0, 33.0), "zelt", L),
]
GLASS = [
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
    (("rect", 5.2, 12.6, 7.0, 13.6), "kohlen", B),
    (("circle", 2.4, 15.5, 0.25), "kandelaber", B),
    (("rect", 5.8, 20.9, 7.8, 21.35), "kirchenbank", B),         # Chapel: zwei Bankbloecke mit Mittelgang zum Altar
    (("rect", 8.6, 20.9, 10.6, 21.35), "kirchenbank", B),
    (("rect", 5.8, 21.9, 7.8, 22.35), "kirchenbank", B),
    (("rect", 8.6, 21.9, 10.6, 22.35), "kirchenbank", B),
    (("circle", 6.55, 19.7, 0.25), "kandelaber", B),             # links und rechts vom Altar
    (("circle", 9.85, 19.7, 0.25), "kandelaber", B),
    (("rect", 32.6, 11.0, 33.7, 12.6), "baer", B),
    (("rect", 30.0, 15.4, 30.9, 16.2), "sessel", B),
    (("rect", 31.6, 16.4, 32.5, 17.2), "sessel", B),
    # Garten
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
    (("rect", 41.25, 30.85, 41.95, 31.30), "engelsstatue_tuch", L),   # 28.10. (User): unter dem Grab ein netter, betender Engel statt Weeping Angel
    (("circle", 43.0, 34.5, 0.25), "kandelaber", L),
    (("rect", 44.9, 30.9, 46.9, 31.6), "sarg", L),                   # 28.10. abends 0,3 m nach links
    (("rect", 44.9, 33.4, 46.9, 34.1), "sarg", L),
]


# ------------------------------------------------------------------ Einrichtung seit dem Audit 15.10. (Schritt 2)
# Gleiche Form wie oben. DECOR = Objekte ohne Kollision (Wandbilder, Haengendes, Umgestuerztes, Bodenkram); sie
# werden gezeichnet und sortiert wie Props, sperren aber weder Weg noch Sicht.
OPAQUE += [
    (("rect", 10.1, 1.2, 10.75, 2.4), "kupferkessel", B),           # Laundry, Ostwand
    (("rect", 8.25, 12.2, 8.7, 13.9), "garderobe", B),               # Long Library, Nordarm Westwand
    (("rect", 1.0, 26.0, 4.0, 28.8), "zelt_aufgeschlitzt", L),       # Crew Camp
]
GLASS += [
    (("rect", 5.6, 1.0, 6.4, 1.8), "hackblock", B),                  # Kitchen
    (("rect", 7.3, 0.3, 8.35, 1.05), "mangel", B),                   # Laundry, Nordwestecke (stand bis 24.10. vor der Kuechentuer)
    (("rect", 7.3, 7.0, 8.0, 7.75), "seifenkisten", B),              # Laundry, Suedwestecke
    (("circle", 13.0, 6.45, 0.5), "kristallkugel_tisch", B),         # Seance Parlour (28.10. abends groesser)
    (("rect", 21.85, 5.75, 22.6, 6.4), "phonograph", B),             # Seance Parlour, Ostwand suedlich der Radio-Oeffnung (25.10.)
    (("rect", 26.3, 3.2, 26.75, 4.0), "walkie_station", B),          # Radio Room, Ostwand
    (("circle", 24.4, 2.2, 0.3), "drehstuhl", B),                    # Radio Room
    (("circle", 28.4, 3.2, 0.3), "schneiderpuppe", B),           # Prop Store / Box Room (25.10.: stand im neuen Requisitentisch)
    (("rect", 32.2, 2.6, 33.0, 3.7), "sarg_angelehnt", B),           # Prop Store
    (("circle", 2.0, 17.8, 0.3), "globus", B),                       # Long Library
    (("rect", 8.0, 15.2, 8.9, 16.0), "lesesessel", B),               # Long Library
    (("rect", 3.2, 18.2, 3.8, 18.75), "buecherstapel", B),           # Long Library, Suedwand
    (("circle", 10.4, 8.6, 0.2), "laterne", B),                      # Long Library, Nordarm
    (("rect", 5.8, 22.9, 7.8, 23.35), "zersplitterte_bank", B),      # Chapel, dritte Reihe links (rechts liegt Vent 2)
    (("rect", 14.1, 20.4, 14.75, 21.1), "regiestuhl_director", B),   # Director's Booth
    (("rect", 11.3, 20.5, 11.75, 21.8), "mischpult", B),             # Director's Booth, Westwand
    (("rect", 19.3, 20.3, 19.75, 21.3), "perueckenkoepfe", B),       # Makeup, Westwand
    (("circle", 24.0, 9.3, 0.25), "buesten_saeule", B),              # Portrait Gallery
    (("rect", 25.2, 19.0, 25.8, 19.6), "ruestung", B),               # Portrait Gallery
    (("rect", 23.3, 23.0, 23.8, 23.7), "standspiegel", B),           # Portrait Gallery, Suedwestecke
    (("rect", 28.5, 10.2, 31.3, 11.7), "billardtisch", B),           # Trophy Room
    (("circle", 31.3, 15.6, 0.25), "beistelltisch", B),              # Fireplace Room, zwischen den Sesseln
    (("rect", 33.2, 13.9, 33.6, 14.4), "schuerhaken", B),            # Fireplace Room, neben dem Kamin
    (("rect", 33.0, 14.0, 33.75, 14.8), "holzkorb", B),              # Fireplace Room, Ostwand
    (("rect", 26.4, 16.6, 27.2, 17.5), "schaukelstuhl", B),          # Fireplace Room
    (("rect", 26.3, 22.6, 27.4, 23.7), "aktenkisten", B),            # Study, Suedwestecke
    (("circle", 37.0, 14.0, 0.6), "gartentisch", L),                 # Terrace
    (("rect", 34.3, 7.0, 34.9, 8.0), "kuebelpflanze", L),            # Terrace, Hauswand
    (("rect", 34.3, 22.0, 34.9, 23.0), "kuebelpflanze", L),          # Terrace, Hauswand
    (("circle", 22.5, 25.5, 0.3), "lichtstativ", L),                 # Driveway
    (("circle", 15.8, 28.6, 0.3), "lichtstativ", L),                 # Driveway (28.10. abends nach Suedwesten)
    (("rect", 6.0, 26.2, 7.8, 27.0), "campingtisch", L),             # Crew Camp
    (("rect", 0.9, 30.2, 4.3, 31.9), "jeep", L),                     # Crew Camp, Westseite (User 24.10.)
    (("circle", 5.0, 34.6, 0.45), "kabeltrommel", L),                # Crew Camp
    (("circle", 9.0, 27.0, 0.35), "scheinwerfer", L),                # Crew Camp
    (("rect", 40.4, 10.6, 41.2, 11.5), "giesskannen", L),            # Greenhouse, Suedwestecke
    (("circle", 48.8, 10.8, 0.4), "schlauchtrommel", L),             # Greenhouse, Suedostecke
    (("circle", 26.5, 33.0, 0.35), "sonnenuhr", L),                  # Fountain Court
    (("rect", 41.2, 26.6, 42.6, 28.6), "offenes_grab", L),           # Graveyard
    (("rect", 44.0, 24.4, 44.9, 24.7), "grabstein_hausherr", L),     # Graveyard
    (("rect", 47.8, 30.4, 49.3, 31.4), "sarkophag", L),              # Family Crypt
]
# 28.10. Feedback DrSuspect (85 Notizen, scratchpad fb/PLAN.md): Schatten weg = GLASS statt OPAQUE (Kollision bleibt), neue
# Bild-Arten aus den GPT-Boegen 18-22 (villa_art.IMAGE_PROPS), unsichtbare Sperren unter den grossen Bild-Konsolen
GLASS += [
    (("rect", 15.2, 9.7, 18.8, 10.9), "treppensperre", B),         # n01
    (("rect", 0.7, 0.25, 2.5, 1.25), "unsichtbar", B),             # Fussflaeche des grossen Herds (Burger-Konsole, n66)
    (("rect", 32.1, 0.25, 33.75, 1.1), "kisten", B),               # Box Room, Nordostecke (n83)
    (("rect", 26.5, 8.85, 28.2, 9.3), "gewehrschrank", B),         # n15: kleiner, ohne Sichtschatten
    (("rect", 26.0, 4.6, 26.75, 5.6), "bandregal", B),             # n72: kleiner
    (("rect", 0.4, 19.3, 1.2, 19.9), "engelsstatue_tuch", B),      # n48
    (("rect", 19.3, 20.25, 21.9, 20.7), "schminkspiegel", B),      # n35
    (("rect", 35.0, 3.0, 37.5, 5.0), "kamerakran", L),             # n20/n32/n61
    (("rect", 38.6, 24.0, 39.6, 25.0), "statue_schleier", L),      # n59
    (("rect", 12.6, 24.6, 15.4, 26.3), "van", L),                  # n53
    (("rect", 10.8, 24.4, 11.7, 25.6), "dixi", L),                 # n52 (Versteck: HollowmereWorld.Dixi.cs)
    (("rect", 47.2, 3.6, 49.0, 5.2), "riesenpflanze", L),          # n23
    (("rect", 44.3, 34.6, 45.3, 35.7), "tunneleingang", L),        # n29
    (("rect", 0.8, 23.1, 1.6, 23.7), "tunnelausgang", L),          # n51
    (("rect", 19.6, 16.45, 21.0, 17.25), "kamerawagen", B),        # n06: Dolly mit Kamera auf der Schiene, Blick nach Westen
    (("rect", 4.9, 16.1, 6.1, 16.9), "lesetisch", B),              # n44: kleiner
    (("rect", 28.5, 0.3, 30.4, 0.7), "kleiderstange", B),          # Box Room, Nordwand (kuerzer, Platz fuers Maskenregal)
    (("rect", 30.6, 0.25, 31.9, 0.7), "maskenregal", L),           # n83: an der Nordwand statt ueber den Kisten
    (("rect", 19.2, 24.25, 20.0, 24.67), "nebelmaschine", L),      # n84: draussen am Set statt in der Abstellkammer
    (("circle", 28.6, 6.0, 0.35), "orrery", B),                    # Sternwarte: auf den Platz des alten Teleskops
    (("rect", 33.35, 4.75, 33.75, 5.25), "buecherstapel", B),      # n81: kleiner
    (("rect", 13.3, 13.0, 13.9, 13.6), "regiestuhl", B),           # n03: 75 %
    (("ellipse", 14.0, 15.5, 1.4, 1.05), "kronleuchter_boden", B), # n04: 175 %
    (("circle", 26.6, 12.5, 0.35), "globusbar", B),                # n19: untere linke Ecke, Laufweg frei
    (("rect", 23.25, 13.4, 23.85, 14.0), "ruestung", B),           # n14: zwei Ruestungen statt zwei Bildern
    (("rect", 25.15, 12.4, 25.75, 13.0), "ruestung", B),
    (("rect", 23.25, 18.65, 23.85, 19.25), "ruestung", B),         # n11
    (("rect", 0.3, 5.9, 1.7, 7.1), "craftservice", B),             # n71: Snacks sichtbar, Kollision kleiner (HITBOX); 28.10. abends nach Norden
    (("rect", 32.75, 19.2, 33.75, 19.75), "unsichtbar", B),        # Fussflaeche des Tresors (Konsole, ganze Breite)
    (("rect", 2.15, 10.3, 2.95, 10.75), "unsichtbar", B),          # Fussflaeche des Druckventils
    (("rect", 43.3, 6.65, 44.7, 7.0), "unsichtbar", L),            # Pflanzbank
    (("circle", 5.2, 28.85, 0.45), "unsichtbar", L),               # Lagerfeuer
    (("rect", 8.75, 24.55, 9.65, 24.95), "unsichtbar", L),         # Generator
    (("rect", 17.9, 29.3, 19.7, 29.75), "unsichtbar", L),          # Catering-Tisch
    (("rect", 20.1, 28.95, 22.1, 29.75), "getraenketisch", L),     # n56: zweiter Tisch mit Getraenken
    # n57/n60: Laternenpfaehle mit Zweck: sie saeumen die Wege durch Terrasse und Brunnenhof
    (("circle", 35.0, 13.4, 0.18), "laternenpfahl", L), (("circle", 35.0, 17.6, 0.18), "laternenpfahl", L),
    (("circle", 39.3, 16.4, 0.18), "laternenpfahl", L), (("circle", 39.3, 20.3, 0.18), "laternenpfahl", L),
    (("circle", 25.6, 26.6, 0.18), "laternenpfahl", L), (("circle", 25.6, 29.9, 0.18), "laternenpfahl", L),
    (("circle", 35.2, 26.6, 0.18), "laternenpfahl", L), (("circle", 38.8, 26.6, 0.18), "laternenpfahl", L),
    (("circle", 38.6, 29.6, 0.18), "laternenpfahl", L), (("circle", 38.6, 33.6, 0.18), "laternenpfahl", L),
    # n28/n30 (User 28.10. abends: "keine Chandeliers, sondern Kerzenstaender"): drei Standleuchter in der Familiengruft statt
    # der Fackeln, links und rechts hinter dem Tor und zwischen den Saergen (lassen sich wie alle Kandelaber anzuenden)
    (("circle", 45.0, 29.7, 0.25), "kandelaber", L),
    (("circle", 49.25, 32.3, 0.25), "kandelaber", L),
    (("circle", 46.2, 32.5, 0.25), "kandelaber", L),
]
DECOR = [
    (("rect", 0.6, 2.6, 1.6, 2.9), "fleischerhaken", B),             # Kitchen, haengt von der Decke
    (("rect", 7.4, 6.2, 10.6, 6.5), "waescheleine", B),              # Laundry, Laken wie Gestalten
    (("rect", 20.0, 7.5, 22.0, 7.75), "wandteppich", B),             # Seance, Suedwand (Geheimgang zur Halle)
    (("rect", 2.5, 8.25, 6.0, 8.55), "rohre", B),                    # Boiler Room, Nordwand
    (("rect", 0.25, 11.5, 0.55, 12.5), "handabdruck_russ", B),       # Boiler Room, Westwand
    (("rect", 10.75, 12.9, 11.0, 13.9), "klingelbrett", B),          # Long Library, Nordarm Ostwand
    (("rect", 4.0, 15.2, 4.5, 15.5), "rauchendes_buch", B),          # Long Library, am Boden
    (("rect", 29.0, 8.85, 31.0, 9.1), "geweihe", L),                 # Trophy Room, Nordwand (gross: an der zugemauerten Oeffnung)
    (("rect", 28.5, 8.85, 29.95, 9.1), "geweihe", ("small",)),       # klein: links neben der Tuer
    (("rect", 33.5, 8.8, 33.75, 9.8), "hirschkopf", B),              # Trophy Room, Ostwand
    (("rect", 31.5, 8.85, 33.0, 9.1), "fledermaeuse", L),            # Trophy Room, unter der Decke
    (("rect", 32.55, 8.85, 33.4, 9.1), "fledermaeuse", ("small",)),  # klein: rechts neben der Tuer
    (("rect", 31.5, 14.55, 31.8, 14.75), "kinderschuh", B),            # Fireplace Room, vor dem Kamin
    (("rect", 33.5, 21.2, 33.75, 22.0), "lueftungsgitter", B),       # Study, Ostwand
    (("rect", 38.0, 2.3, 39.8, 2.6), "vogelschwarm", L),             # Terrace, auf der Balustrade
    (("rect", 7.2, 34.2, 8.8, 34.9), "schlafsack", L),               # Crew Camp
    (("rect", 49.55, 6.0, 49.75, 8.0), "kletterpflanzen", L),        # Greenhouse, Ostwand
    (("rect", 30.6, 32.25, 31.4, 32.45), "brunnen_blut", L),
    # 28.10. (Feedback DrSuspect)
    (("rect", 2.9, 0.2, 5.5, 0.6), "topfregal", B),                  # n69: groesser
    (("rect", 24.3, 5.95, 25.6, 6.95), "tonband_boden", B),          # n73: groesser, frei vor dem Regal
    (("rect", 32.1, 4.25, 32.9, 4.45), "sternkarte", B),             # n82: kleine Sternkarte an der Sternwarten-Wand
    # n13 + Feedback 2 Nr. 3: drei Doctor-Gemaelde (Crewmates im Kostuem) und die Katze; ganz im Raum, nicht halb in der Wand
    (("rect", 23.85, 15.5, 24.05, 16.5), "portrait_dame", B),
    (("rect", 23.85, 16.95, 24.05, 17.95), "portrait_maedchen", B),
    (("rect", 24.95, 14.4, 25.15, 15.4), "portrait_offizier", B),
    (("rect", 24.95, 23.0, 25.15, 23.8), "portrait_katze", B),
         # Fountain Court, rotes Wasser + Schleierstatue (vor dem Brunnen)
    (("rect", 42.5, 16.1, 43.3, 16.4), "kraehen", L),                # Graveyard, auf den Steinen
    (("rect", 44.25, 29.0, 44.45, 32.0), "nischen_urnen", L),        # Family Crypt, Westwand
    (("rect", 49.55, 29.0, 49.75, 32.0), "nischen_urnen", L),        # Family Crypt, Ostwand
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
    # Fable-Pruefung 25.10. (_reviews/hollowmere-large/KOLLISION.md): Kollision passend zur GPT-Zeichnung
    ("kupferkessel", ("rect", 10.1, 1.2, 10.75, 2.4)): ("rect", 10.1, 1.85, 10.75, 2.4),
    ("bandregal", ("rect", 25.65, 4.3, 26.75, 5.9)): ("rect", 25.7, 5.0, 26.75, 5.9),
    ("herd", ("rect", 0.3, 0.25, 2.8, 0.85)): ("rect", 0.75, 0.25, 2.5, 0.85),
    ("waschzuber", ("circle", 9.0, 1.3, 0.55)): ("ellipse", 8.93, 1.25, 0.53, 0.38),
    ("seance_tisch", ("ellipse", 13.0, 1.95, 1.4, 0.85)): ("ellipse", 13.0, 2.2, 0.95, 0.55),   # 28.10. n77: kleiner
    ("kristallkugel_tisch", ("circle", 13.0, 6.45, 0.5)): ("circle", 13.0, 6.25, 0.4),
    ("funktisch", ("rect", 23.3, 0.25, 25.5, 0.85)): ("rect", 23.8, 0.25, 25.0, 0.85),
    ("kleiderstange", ("rect", 28.5, 0.3, 30.4, 0.7)): ("rect", 28.5, 0.45, 30.4, 1.05),
    ("teleskop", ("circle", 28.6, 6.0, 0.55)): ("ellipse", 28.62, 5.95, 0.38, 0.22),
    ("lesetisch", ("rect", 4.9, 16.1, 6.1, 16.9)): ("rect", 5.15, 16.5, 5.85, 16.9),
    ("kirchenbank", ("rect", 5.8, 20.9, 7.8, 21.35)): ("rect", 6.15, 20.9, 7.45, 21.35),
    ("kirchenbank", ("rect", 8.6, 20.9, 10.6, 21.35)): ("rect", 8.95, 20.9, 10.25, 21.35),
    ("kirchenbank", ("rect", 5.8, 21.9, 7.8, 22.35)): ("rect", 6.15, 21.9, 7.45, 22.35),
    ("kirchenbank", ("rect", 8.6, 21.9, 10.6, 22.35)): ("rect", 8.95, 21.9, 10.25, 22.35),
    ("zersplitterte_bank", ("rect", 5.8, 22.9, 7.8, 23.35)): ("rect", 6.4, 22.9, 7.5, 23.4),
    ("mischpult", ("rect", 11.3, 20.5, 11.75, 21.8)): ("rect", 11.2, 21.4, 11.8, 22.0),
    ("schminkspiegel", ("rect", 19.3, 20.25, 21.9, 20.7)): ("rect", 19.7, 20.25, 21.5, 20.7),
    ("gewehrschrank", ("rect", 26.5, 8.85, 28.2, 9.3)): ("rect", 26.95, 8.85, 27.75, 9.3),
    ("billardtisch", ("rect", 28.5, 10.2, 31.3, 11.7)): ("rect", 28.7, 10.2, 31.1, 11.7),
    ("kamin", ("rect", 30.5, 13.85, 32.8, 14.45)): ("rect", 30.75, 13.85, 32.55, 14.45),
    ("beistelltisch", ("circle", 31.3, 15.6, 0.25)): ("circle", 31.3, 15.45, 0.22),
    ("buecherregal", ("rect", 31.0, 18.25, 33.6, 18.7)): ("rect", 31.45, 18.25, 33.15, 18.7),
    ("schreibtisch", ("rect", 29.0, 22.7, 31.4, 23.6)): ("rect", 29.45, 22.7, 30.95, 23.6),
    ("kamerakran", ("rect", 35.0, 3.0, 37.5, 5.0)): ("rect", 35.1, 4.1, 36.6, 5.0),
    ("urne", ("circle", 37.0, 10.0, 0.4)): ("circle", 37.0, 9.9, 0.32),
    ("kuebelpflanze", ("rect", 34.3, 7.0, 34.9, 8.0)): ("rect", 34.3, 7.4, 35.1, 8.0),
    ("kuebelpflanze", ("rect", 34.3, 22.0, 34.9, 23.0)): ("rect", 34.3, 22.4, 35.1, 23.0),
    ("absperrung", ("rect", 13.0, 29.35, 15.0, 29.65)): ("rect", 13.45, 29.35, 14.55, 29.65),
    ("getraenketisch", ("rect", 20.1, 28.95, 22.1, 29.75)): ("rect", 20.3, 29.25, 21.9, 29.75),
    ("lichtstativ", ("circle", 22.5, 25.5, 0.3)): ("ellipse", 22.62, 25.55, 0.5, 0.25),
    ("lichtstativ", ("circle", 15.8, 28.6, 0.3)): ("ellipse", 15.92, 28.65, 0.5, 0.25),
    ("campingtisch", ("rect", 6.0, 26.2, 7.8, 27.0)): ("rect", 6.35, 26.3, 7.45, 27.0),
    ("kabeltrommel", ("circle", 5.0, 34.6, 0.45)): ("ellipse", 5.35, 34.5, 0.52, 0.32),
    ("riesenpflanze", ("rect", 47.2, 3.6, 49.0, 5.2)): ("rect", 47.65, 4.35, 48.9, 4.95),
    ("schlauchtrommel", ("circle", 48.8, 10.8, 0.4)): ("ellipse", 48.95, 10.8, 0.55, 0.35),
    ("giesskannen", ("rect", 40.4, 10.6, 41.2, 11.5)): ("rect", 40.5, 10.85, 41.25, 11.3),
    ("kandelaber", ("circle", 19.55, 0.75, 0.25)): ("circle", 19.55, 1.05, 0.23),
    ("kandelaber", ("circle", 22.0, 6.9, 0.25)): ("circle", 22.0, 7.2, 0.23),
    ("kandelaber", ("circle", 2.4, 15.5, 0.25)): ("circle", 2.4, 15.8, 0.23),
    ("kandelaber", ("circle", 6.55, 19.7, 0.25)): ("circle", 6.55, 20.0, 0.23),
    ("kandelaber", ("circle", 9.85, 19.7, 0.25)): ("circle", 9.85, 20.0, 0.23),
    ("kandelaber", ("circle", 43.0, 34.5, 0.25)): ("circle", 43.0, 34.8, 0.23),
    ("laterne", ("circle", 10.4, 8.6, 0.2)): ("circle", 10.27, 8.85, 0.12),
    ("laterne", ("circle", 37.0, 20.0, 0.2)): ("circle", 36.87, 20.25, 0.12),
    ("laterne", ("circle", 34.5, 28.5, 0.2)): ("circle", 34.37, 28.75, 0.12),
    ("laterne", ("circle", 27.5, 28.5, 0.2)): ("circle", 27.37, 28.75, 0.12),
    ('kuebelpflanze', ('rect', 34.3, 7.0, 34.9, 8.0)): ('rect', 34.35, 6.9, 34.75, 8.0),   # Kollisionspruefung 26.10. VL-1
    ('kuebelpflanze', ('rect', 34.3, 22.0, 34.9, 23.0)): ('rect', 34.35, 21.9, 34.75, 23.0),   # Kollisionspruefung 26.10. VL-1
    ('zelt_aufgeschlitzt', ('rect', 1.0, 26.0, 4.0, 28.8)): ('rect', 0.85, 27.2, 4.15, 28.8),   # 28.10.: bis zu den Heringen
    ('zelt', ('rect', 6.5, 30.0, 10.0, 33.0)): ('rect', 6.35, 31.6, 10.15, 33.1),               # 28.10.: bis zu den Heringen
    ("bandregal", ("rect", 26.0, 4.6, 26.75, 5.6)): ("rect", 26.1, 5.1, 26.75, 5.6),   # 28.10. n72
    ("orrery", ("circle", 28.6, 6.0, 0.35)): ("circle", 28.6, 5.9, 0.3),
    ("globusbar", ("circle", 26.6, 12.5, 0.35)): ("circle", 26.6, 12.4, 0.3),     # 28.10. n19
    # 28.10. Feedback DrSuspect
    ("sessel", ("rect", 14.9, 1.65, 15.8, 2.45)): ("rect", 15.0, 2.0, 15.7, 2.45),          # n38
    ("sessel", ("rect", 18.2, 1.65, 19.1, 2.45)): ("rect", 18.3, 2.0, 19.0, 2.45),
    ("offenes_grab", ("rect", 41.2, 26.6, 42.6, 28.6)): ("rect", 41.3, 27.35, 42.5, 28.4),   # n31/n58, 28.10. abends etwas breiter
    ("craftservice", ("rect", 0.3, 5.9, 1.7, 7.1)): ("rect", 0.35, 6.55, 1.6, 7.1),         # n71
    # Hitbox-Pruefung 28.10. abends (_reviews/villa_large/kollision, gegen die sichtbaren Fusskanten der GPT-Bilder)
    ("ruestung", ("rect", 23.25, 13.4, 23.85, 14.0)): ("rect", 23.25, 13.65, 24.1, 14.0),     # ganzer Holzsockel
    ("ruestung", ("rect", 25.15, 12.4, 25.75, 13.0)): ("rect", 25.0, 12.65, 25.8, 13.0),
    ("ruestung", ("rect", 23.25, 18.65, 23.85, 19.25)): ("rect", 23.25, 18.9, 24.1, 19.25),
    ("ruestung", ("rect", 25.2, 19.0, 25.8, 19.6)): ("rect", 25.05, 19.25, 25.8, 19.6),
    ("kamerawagen", ("rect", 19.6, 16.45, 21.0, 17.25)): ("rect", 19.25, 16.75, 21.35, 17.25),   # Wagen ist 2,1 m breit
    ("kronleuchter_boden", ("ellipse", 14.0, 15.5, 1.4, 1.05)): ("ellipse", 14.0, 16.1, 1.2, 0.42),
    ("kuechentisch", ("rect", 2.2, 3.6, 4.6, 5.0)): ("rect", 2.5, 4.3, 4.3, 5.0),
    ("schminkspiegel", ("rect", 19.3, 20.25, 21.9, 20.7)): ("rect", 19.7, 20.25, 21.5, 20.7),
    ("kandelaber", ("circle", 45.0, 29.7, 0.25)): ("circle", 45.0, 30.0, 0.23),
    ("kandelaber", ("circle", 49.25, 32.3, 0.25)): ("circle", 49.25, 32.6, 0.23),
    ("kandelaber", ("circle", 46.2, 32.5, 0.25)): ("circle", 46.2, 32.8, 0.23),
}


def hit_shape(s, kind):
    return HITBOX.get((kind, s), s)


def in_variant(variants, v):
    return v in variants
