// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereMap - die Halloween-Karte "Hollowmere Manor" (Spukvilla als Horrorfilm-Set) fuer Unknown's Atlas.
//
// Atlas baut sie wie seine eigenen Karten (Relocate-in-Place auf der Skeld); dieses Plugin liefert nur die
// Daten (Villa/VillaSmall.g.cs, Villa/VillaLarge.g.cs aus tools/gen_villa.py) und die eingebettete Grafik
// (Resources/villa). Atlas ist eine weiche Abhaengigkeit: fehlt es, meldet sich die Karte einfach nicht an.
// Alle Zugriffe auf Atlas-Typen stehen in dieser Klasse, die nur nach der Pruefung im Plugin beruehrt wird.
//
// Groesse: Host-Option 1960 (Small = nur das Haus, Large = mit Garten, Friedhof und Gruft). Atlas ruft die
// Factory vor jedem Kartenbau neu auf, die Option gilt also ab der naechsten Runde.
// Obergeschoss (17.11.): Host-Option 1970, fuer beide Groessen; WithUpper fuegt Villa/VillaUpper.g.cs ein (eigene Flaeche
// noerdlich des Hauses, Treppen ohne Knopf in HollowmereWorld.Stairs, Sperre vor der Freitreppe weg).

using System;
using System.Collections.Generic;
using TheOtherRoles;
using UnityEngine;
using UnknownsAtlas;

namespace UnknownsHalloween;

internal static class HollowmereMap
{
    public const string Key = "villa";
    public const string DisplayName = "Hollowmere Manor";
    private const string ResourceNamespace = "UnknownsHalloween.Resources";

    public static CustomOption Size;
    public static CustomOption UpperFloor;

    internal static void Register()
    {
        try
        {
            Size = CustomOption.Create(1960, CustomOption.CustomOptionType.General, "Hollowmere Manor Size",
                new[] { "Small", "Large" }, null, true, null, "Hollowmere Manor");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"[Halloween/Villa] size option failed: {e}"); }
        try
        {
            UpperFloor = CustomOption.Create(1970, CustomOption.CustomOptionType.General, "Hollowmere Upper Floor", true, null, false, null, "Hollowmere Manor");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"[Halloween/Villa] upper floor option failed: {e}"); }

        // Mechaniken brauchen Atlas-API 2 (AtlasMapDef.World, ab Atlas 1.0.0.2). AtlasMaps.ApiVersion ist eine
        // Konstante und wird hier eingebacken, also zur Laufzeit am Feld pruefen: mit aelterem Atlas waere jeder
        // Kartenbau an d.World gescheitert.
        if (typeof(AtlasMapDef).GetField("World") == null)
        {
            HalloweenPlugin.Logger.LogError($"[Halloween/Villa] {DisplayName} needs Unknown's Atlas 1.0.0.2 or newer - map not registered");
            return;
        }

        HollowmereIntro.Init();
        HollowmereWorld.Init();
        HollowmereUpperTasks.Init();

        // Floor, props, consoles, minigames, intro and eject art come from the asset packages (HalloweenAssets): the map
        // joins Atlas only once they are there, right away on a normal start, otherwise as soon as the download is done.
        if (!HalloweenAssets.Ready("villa_"))
            HalloweenPlugin.Logger.LogInfo($"[Halloween/Villa] {DisplayName} waits for its asset packages");
        HalloweenAssets.WhenReady("villa_", JoinAtlas);
    }

    private static void JoinAtlas()
    {
        bool ok = AtlasMaps.Register(Key, "Hollowmere", Make, HalloweenAssets.ResourceAssembly, ResourceNamespace,
            button: "button_villa.png", icon: "icon_villa.png", contentVersion: HalloweenPlugin.PluginVersion);
        HalloweenPlugin.Logger.LogInfo($"[Halloween/Villa] {DisplayName} {(ok ? "registered with" : "NOT registered with")} Unknown's Atlas (API {AtlasMaps.ApiVersion})");
    }

    // Diagnose: UC_HALLOWEEN_DIAG=villalarge erzwingt die grosse Variante (Autotest ohne Eingriff in die TOR-Optionen)
    internal static bool Large =>
        !(Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "").Contains("villasmall") &&
        ((Size != null && Size.getSelection() == 1) ||
         (Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "").Contains("villalarge"));

    // Diagnose: UC_HALLOWEEN_DIAG=villanoup schaltet das Obergeschoss ab, villaup erzwingt es
    internal static bool Upper =>
        !(Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "").Contains("villanoup") &&
        (UpperFloor == null || UpperFloor.getBool() || (Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "").Contains("villaup"));

    // "Make Burger" aus Airship am Herd der Kueche (Kueche = LowerEngine); Atlas laedt dafuer Airship mit.
    // 28.10. (Feedback DrSuspect): weitere Airship-Aufgaben als Reiter. Airship ist ohnehin geladen, die Reiter kosten also keine
    // Ladezeit; bis auf den Tresor (Airship-Original, n33) zeigen sie Atlas-Minispiele mit Villa-Grafik (CustomTasks unten).
    // Reihenfolge nie umstellen: jeder Eintrag reserviert einen Task-Index, alle Clients muessen dieselbe Liste bauen.
    private static readonly (TaskTypes, int, string, SystemTypes)[] BorrowedSmall =
    {
        (TaskTypes.MakeBurger, 4, "LowerEngine/MakeBurger/0", SystemTypes.LowerEngine),
        (TaskTypes.UnlockSafe, 4, "Admin/UnlockSafe/0", SystemTypes.Admin),                   // Tresor im Arbeitszimmer
        (TaskTypes.ResetBreakers, 4, "Electrical/PressureValve/0", SystemTypes.Electrical),   // Kesseldruck ablassen (n64)
    };
    private static readonly (TaskTypes, int, string, SystemTypes)[] BorrowedLarge =
    {
        (TaskTypes.MakeBurger, 4, "LowerEngine/MakeBurger/0", SystemTypes.LowerEngine),
        (TaskTypes.UnlockSafe, 4, "Admin/UnlockSafe/0", SystemTypes.Admin),
        (TaskTypes.ResetBreakers, 4, "Electrical/PressureValve/0", SystemTypes.Electrical),
        (TaskTypes.FixShower, 4, "Storage/WaterBench/0", SystemTypes.Storage),                // Pflanzen giessen (n24)
        (TaskTypes.CleanToilet, 4, "UpperEngine/Campfire/0", SystemTypes.UpperEngine),        // Marshmallows (n62)
        (TaskTypes.PutAwayPistols, 4, "UpperEngine/CampGenerator/0", SystemTypes.UpperEngine),// Generator im Crew Camp (n67)
        (TaskTypes.PolishRuby, 4, "MainHall/Catering/0", SystemTypes.MainHall),               // Essen und Trinken (n56)
        (TaskTypes.PickUpTowels, 4, "Storage/FeedPlant/0", SystemTypes.Storage),              // Riesenpflanze fuettern (n23, 05.11.)
    };
    // Obergeschoss (17.11.): hinter die Listen beider Groessen gehaengt, die Reihenfolge davor bleibt
    private static readonly (TaskTypes, int, string, SystemTypes)[] BorrowedUpper =
    {
        (TaskTypes.SortRecords, 4, "VaultRoom/SortRecords/0", SystemTypes.VaultRoom),          // Attic
        (TaskTypes.DevelopPhotos, 4, "Cockpit/DevelopPhotos/0", SystemTypes.Cockpit),          // Darkroom
        (TaskTypes.DressMannequin, 4, "Armory/DressMannequin/0", SystemTypes.Armory),          // Sewing Room
        (TaskTypes.RewindTapes, 4, "Office/RewindTapes/0", SystemTypes.Office),                // Master Bedroom
        // 18.11.: zwei weitere Aufgaben oben (Kinderstube, Bad), wieder hinten angehaengt
        (TaskTypes.PutAwayRifles, 4, "Specimens/PutAwayRifles/0", SystemTypes.Specimens),     // Nursery
        (TaskTypes.StartFans, 4, "Brig/StartFans/0", SystemTypes.Brig),                        // Bathroom
    };

    private static AtlasMapDef Make()
    {
        var d = Large ? FromLarge() : FromSmall();
        d.Key = Key;
        d.DisplayName = DisplayName;
        d.ResourcePrefix = "villa";
        d.ResourceAssembly = HalloweenAssets.ResourceAssembly;
        d.ResourceNamespace = ResourceNamespace;
        d.BuiltInEffects = false;
        d.CameraColor = new Color(0x16 / 255f, 0x10 / 255f, 0x14 / 255f);
        // Kameras etwas weiter herausgezoomt (User 28.10.); Feld gibt es erst ab dem Atlas mit CameraZoom, daher per Reflection
        typeof(AtlasMapDef).GetField("CameraZoom")?.SetValue(d, 1.35f);
        // Oberteile hoher Moebel an Innenwaenden ueber dem Sichtschatten (28.10.; Feld gibt es erst ab dem Atlas mit PropTops)
        typeof(AtlasMapDef).GetField("PropTops")?.SetValue(d, Large ? VillaLarge.PropTops : VillaSmall.PropTops);
        d.TaskNames = TaskNames();
        d.CustomTasks = CustomTasks();
        d.TaskArt = TaskArt();
        d.TaskText = TaskText();
        bool upper = Upper;
        if (upper) WithUpper(d, Large);
        // Mechaniken (Geheimgaenge, Uhr, Kerzen): je Bau ein frisches Objekt, Atlas ruft es ueber IAtlasMapWorld
        var dark = Large ? VillaLarge.DarkRooms : VillaSmall.DarkRooms;
        if (upper) dark = Cat(dark, VillaUpper.DarkRooms);
        var world = Large
            ? new HollowmereWorld(d, VillaLarge.Secrets, VillaLarge.Clock, dark)
            : new HollowmereWorld(d, VillaSmall.Secrets, VillaSmall.Clock, dark);
        if (upper) world.SetStairs(VillaUpper.Stairs);
        d.World = world;
        HalloweenPlugin.Logger.LogInfo($"[Halloween/Villa] building {(Large ? "large" : "small")} {(upper ? "with" : "without")} the upper floor");
        return d;
    }

    private static T[] Cat<T>(T[] a, T[] b)
    {
        var r = new T[(a?.Length ?? 0) + (b?.Length ?? 0)];
        a?.CopyTo(r, 0);
        b?.CopyTo(r, a?.Length ?? 0);
        return r;
    }

    /// <summary>Obergeschoss einfuegen (Option 1970): Flaeche, Raeume, Objekte, Aufgaben, Vents und eine Kamera oben; unten fallen
    /// die Kollision der Freitreppe und die Sperre weg (Bretterhaufen seitlich), die Dienstbotentreppe kommt in die Kueche.</summary>
    private static void WithUpper(AtlasMapDef d, bool large)
    {
        var dropO = new HashSet<int>(large ? VillaUpper.LargeDropOpaque : VillaUpper.SmallDropOpaque);
        var dropG = new HashSet<int>(large ? VillaUpper.LargeDropGlass : VillaUpper.SmallDropGlass);
        var op = new List<Vector2[]>();
        var casts = new List<bool>();
        for (int i = 0; i < d.Opaque.Length; i++)
        {
            if (dropO.Contains(i)) continue;
            op.Add(d.Opaque[i]);
            casts.Add(d.OpaqueCastsShadow == null || i >= d.OpaqueCastsShadow.Length || d.OpaqueCastsShadow[i]);
        }
        op.AddRange(VillaUpper.Opaque);
        casts.AddRange(VillaUpper.OpaqueCastsShadow);
        d.Opaque = op.ToArray();
        d.OpaqueCastsShadow = casts.ToArray();
        var gl = new List<Vector2[]>();
        for (int i = 0; i < d.Glass.Length; i++) if (!dropG.Contains(i)) gl.Add(d.Glass[i]);
        gl.AddRange(VillaUpper.Glass);
        d.Glass = gl.ToArray();

        d.Walls = Cat(d.Walls, VillaUpper.Walls);
        d.ShadowWalls = Cat(d.ShadowWalls, VillaUpper.ShadowWalls);
        d.Rooms = Cat(d.Rooms, VillaUpper.Rooms);
        d.Hallways = Cat(d.Hallways, VillaUpper.Hallways);
        d.FloorTiles = Cat(d.FloorTiles, VillaUpper.FloorTiles);

        // Objekte: Sperre -> Bretterhaufen (gleicher Index, PropTops bleiben gueltig), Freitreppe nach hinten sortiert
        var props = d.Props.Clone() as (string Kind, int Atlas, int X, int Y, int W, int H, float WorldX, float WorldY, float BaseY, float FootX0, float FootX1)[];
        int sperre = large ? VillaUpper.LargeSperreProp : VillaUpper.SmallSperreProp;
        int treppe = large ? VillaUpper.LargeTreppeProp : VillaUpper.SmallTreppeProp;
        if (sperre >= 0 && sperre < props.Length) props[sperre] = VillaUpper.ReplaceProp;
        if (treppe >= 0 && treppe < props.Length) props[treppe].BaseY = VillaUpper.FreitreppeBaseY;
        int ground = props.Length;
        d.Props = Cat(props, VillaUpper.Props);
        var topsField = typeof(AtlasMapDef).GetField("PropTops");
        if (topsField != null)
        {
            var tops = new Dictionary<int, float>((topsField.GetValue(d) as Dictionary<int, float>) ?? new Dictionary<int, float>());
            tops.Remove(sperre);
            foreach (var kv in VillaUpper.PropTops) tops[ground + kv.Key] = kv.Value;
            topsField.SetValue(d, tops);
        }
        foreach (var k in VillaUpper.NoFadeKinds) d.NoFadeKinds.Add(k);

        // Konsolenbilder: gleicher Schluessel oben gewinnt (Vent 10 liegt klein im Dachboden statt im Garten)
        var sprites = new List<(string Key, int Atlas, int X, int Y, int W, int H, float PivotX, float PivotY)>();
        var up = large ? VillaUpper.LargeConsoleSprites : VillaUpper.SmallConsoleSprites;
        var upKeys = new HashSet<string>();
        foreach (var s in up) upKeys.Add(s.Key);
        foreach (var s in d.ConsoleSprites) if (!upKeys.Contains(s.Key)) sprites.Add(s);
        sprites.AddRange(up);
        d.ConsoleSprites = sprites.ToArray();

        d.Consoles = new Dictionary<string, Vector2>(d.Consoles);
        foreach (var kv in VillaUpper.Consoles) d.Consoles[kv.Key] = kv.Value;
        d.ForeignTasks = Cat(d.ForeignTasks, BorrowedUpper);

        d.Vents = new Dictionary<int, Vector2>(d.Vents);
        foreach (var kv in large ? VillaUpper.LargeVents : VillaUpper.SmallVents) d.Vents[kv.Key] = kv.Value;
        d.VentNetworks = large ? VillaUpper.LargeVentNetworks : VillaUpper.SmallVentNetworks;

        var cams = d.Cameras.Clone() as Vector2[];
        int ci = large ? VillaUpper.LargeCameraIndex : VillaUpper.SmallCameraIndex;
        if (ci >= 0 && ci < cams.Length) cams[ci] = large ? VillaUpper.LargeCameraPos : VillaUpper.SmallCameraPos;
        d.Cameras = cams;

        d.MinX = large ? VillaUpper.LargeMinX : VillaUpper.SmallMinX;
        d.MinY = large ? VillaUpper.LargeMinY : VillaUpper.SmallMinY;
        d.MaxX = large ? VillaUpper.LargeMaxX : VillaUpper.SmallMaxX;
        d.MaxY = large ? VillaUpper.LargeMaxY : VillaUpper.SmallMaxY;
        d.MapLabels = large ? VillaUpper.LargeMapLabels : VillaUpper.SmallMapLabels;
        d.MinimapFile = large ? "villa_minimap_large_up.png" : "villa_minimap_small_up.png";
        d.ViewSpots = Cat(d.ViewSpots, new Vector2[] { new(0f, 22.0f) });
    }

    private static AtlasMapDef FromSmall() => new()
    {
        MinimapFile = "villa_minimap_small.png",
        MinX = VillaSmall.MinX, MinY = VillaSmall.MinY, MaxX = VillaSmall.MaxX, MaxY = VillaSmall.MaxY,
        Walls = VillaSmall.Walls, ShadowWalls = VillaSmall.ShadowWalls,
        Opaque = VillaSmall.Opaque, OpaqueCastsShadow = VillaSmall.OpaqueCastsShadow,
        Glass = VillaSmall.Glass, Rooms = VillaSmall.Rooms, Hallways = VillaSmall.Hallways,
        FloorPixelsPerMeter = VillaSmall.FloorPixelsPerMeter, FloorTiles = VillaSmall.FloorTiles,
        PropPixelsPerMeter = VillaSmall.PropPixelsPerMeter, Props = VillaSmall.Props,
        ConsoleSprites = VillaSmall.ConsoleSprites,
        Consoles = VillaSmall.Consoles,
        ForeignTasks = BorrowedSmall,
        EmergencyButton = VillaSmall.EmergencyButton, SurveillanceConsole = VillaSmall.SurveillanceConsole,
        AdminTable = VillaSmall.AdminTable, FreeplayLaptop = VillaSmall.FreeplayLaptop,
        Spawn = VillaSmall.Spawn, SpawnRadius = VillaSmall.SpawnRadius,
        Vents = VillaSmall.Vents, VentNetworks = VillaSmall.VentNetworks,
        VerticalDoors = VillaSmall.VerticalDoors, HorizontalDoors = VillaSmall.HorizontalDoors,
        Cameras = VillaSmall.Cameras, MapButtons = VillaSmall.MapButtons, MapLabels = VillaSmall.MapLabels,
        // Halle (Spawn), Seance-Salon, Bibliothek, Kaminzimmer, Regie mit den Kameras
        ViewSpots = new Vector2[] { new(0f, -1.0f), new(0f, 11.0f), new(-12.0f, -2.5f), new(13.0f, -1.5f), new(-4.0f, -8.8f) },
    };

    private static AtlasMapDef FromLarge() => new()
    {
        MinimapFile = "villa_minimap_large.png",
        MinX = VillaLarge.MinX, MinY = VillaLarge.MinY, MaxX = VillaLarge.MaxX, MaxY = VillaLarge.MaxY,
        Walls = VillaLarge.Walls, ShadowWalls = VillaLarge.ShadowWalls,
        Opaque = VillaLarge.Opaque, OpaqueCastsShadow = VillaLarge.OpaqueCastsShadow,
        Glass = VillaLarge.Glass, Rooms = VillaLarge.Rooms, Hallways = VillaLarge.Hallways,
        FloorPixelsPerMeter = VillaLarge.FloorPixelsPerMeter, FloorTiles = VillaLarge.FloorTiles,
        PropPixelsPerMeter = VillaLarge.PropPixelsPerMeter, Props = VillaLarge.Props,
        ConsoleSprites = VillaLarge.ConsoleSprites,
        Consoles = VillaLarge.Consoles,
        ForeignTasks = BorrowedLarge,
        EmergencyButton = VillaLarge.EmergencyButton, SurveillanceConsole = VillaLarge.SurveillanceConsole,
        AdminTable = VillaLarge.AdminTable, FreeplayLaptop = VillaLarge.FreeplayLaptop,
        Spawn = VillaLarge.Spawn, SpawnRadius = VillaLarge.SpawnRadius,
        Vents = VillaLarge.Vents, VentNetworks = VillaLarge.VentNetworks,
        VerticalDoors = VillaLarge.VerticalDoors, HorizontalDoors = VillaLarge.HorizontalDoors,
        Cameras = VillaLarge.Cameras, MapButtons = VillaLarge.MapButtons, MapLabels = VillaLarge.MapLabels,
        // Halle (Spawn), Vorplatz, Friedhof, Brunnenhof, Gewaechshaus
        ViewSpots = new Vector2[] { new(0f, -1.0f), new(1.0f, -13.0f), new(28.0f, -6.0f), new(17.0f, -15.0f), new(28.0f, 7.0f) },
    };

    // Jeder Karten-Task reitet auf einem Skeld-TaskType (wie bei den Atlas-Karten); Minispiele bleiben
    // vorerst die der Skeld, eigene folgen spaeter.
    // Minispiele (Audit 15.10., Schritt 3): Atlas-Bausteine mit Villa-Grafik (tools/gen_villa_tasks.py, Resources/villa),
    // Atlas laedt Minispiel-Bilder zuerst aus dieser DLL. "spirit" ist das Geisterbrett fuer den Seance-Tisch.
    private static Dictionary<TaskTypes, string> CustomTasks() => new()
    {
        { TaskTypes.FixWiring, "splice" }, { TaskTypes.SwipeCard, "timecard" }, { TaskTypes.CalibrateDistributor, "climate" },
        { TaskTypes.ChartCourse, "constellation" }, { TaskTypes.CleanO2Filter, "dust" }, { TaskTypes.DivertPower, "route" },
        { TaskTypes.PrimeShields, "lanterns" }, { TaskTypes.StabilizeSteering, "projector" }, { TaskTypes.UnlockManifolds, "hiero" },
        { TaskTypes.UploadData, "audio" }, { TaskTypes.AlignEngineOutput, "generator" }, { TaskTypes.ClearAsteroids, "moths" },
        { TaskTypes.EmptyGarbage, "bins" }, { TaskTypes.FuelEngines, "refuel" }, { TaskTypes.InspectSample, "pigment" },
        { TaskTypes.StartReactor, "spirit" },
        { TaskTypes.RestoreOxy, "waterworks" }, { TaskTypes.FixLights, "fusebox" },
        // Airship-Reiter (28.10.)
        { TaskTypes.ResetBreakers, "valves" }, { TaskTypes.FixShower, "watering" }, { TaskTypes.CleanToilet, "roast" },
        { TaskTypes.PutAwayPistols, "generator" }, { TaskTypes.PolishRuby, "lunch" },
        // 05.11. (Feedback 28.10., n23): die Riesenpflanze im Gewaechshaus fuettern
        { TaskTypes.PickUpTowels, "feed" },
    };

    private static Dictionary<string, string> TaskArt() => new()
    {
        // Tafeln
        { "task_museum_panel.png", "task_villa_panel.png" }, { "task_wald_panel.png", "task_villa_panel.png" },
        { "task_shop_panel.png", "task_villa_panel.png" }, { "task_steel_panel.png", "task_villa_machine.png" },
        // Sweep the Chimney
        { "dust:task_museum_dino.png", "task_villa_flue.png" }, { "dust:task_museum_dust.png", "task_villa_soot.png" },
        { "dust:task_brush.png", "task_villa_brush.png" },
        // Shoo the Bats
        { "moths:task_gallery.png", "task_villa_window.png" }, { "moths:task_moth.png", "task_villa_bat.png" },
        { "moths:task_torch.png", "task_villa_broom.png" }, { "moths:task_jar.png", "task_villa_openwindow.png" },
        // Light the Ward Candles
        { "lanterns:task_dock_night.png", "task_villa_chapel.png" }, { "lanterns:task_lantern_on.png", "task_villa_candle_on.png" },
        { "lanterns:task_lantern_off.png", "task_villa_candle_off.png" },
        // Balance the Dimmer Board, Tune the Generator, Refuel the Generators
        { "climate:task_gauge_band.png", "task_villa_gauge_band.png" }, { "climate:task_needle.png", "task_villa_needle.png" },
        { "generator:task_generator.png", "task_villa_generator.png" },
        { "refuel:task_boiler.png", "task_villa_drum.png" }, { "refuel:task_can.png", "task_villa_jerrycan.png" },
        // Chart the Stars, Focus the Telescope
        { "constellation:task_card.png", "task_villa_starcard.png" }, { "constellation:task_sky.png", "task_villa_sky.png" },
        { "projector:task_sky.png", "task_villa_moonsky.png" },
        // Mix the Fake Blood
        { "pigment:task_vial.png", "task_villa_vial.png" }, { "pigment:task_strip.png", "task_villa_strip.png" },
        // Back Up the Dailies
        { "audio:task_photo.png", "task_villa_reelcan.png" }, { "audio:task_deer.png", "task_villa_scene.png" },
        { "audio:task_pc.png", "task_villa_recorder.png" }, { "audio:task_dock.png", "task_villa_reeldock.png" },
        { "audio:task_sdcard.png", "task_villa_tape.png" }, { "audio:task_audioguide.png", "task_villa_reel.png" },
        { "audio:task_icon_dino.png", "task_villa_icon_candle.png" }, { "audio:task_icon_mummy.png", "task_villa_icon_skull.png" },
        { "audio:task_icon_planet.png", "task_villa_icon_bat.png" }, { "audio:task_icon_gem.png", "task_villa_icon_key.png" },
        { "audio:task_icon_painting.png", "task_villa_icon_raven.png" },
        // Sign the Call Sheet
        { "timecard:task_timecard.png", "task_villa_callsheet.png" }, { "timecard:task_clock.png", "task_villa_watch.png" },
        // Take Out the Trash
        { "bins:task_bin_paper.png", "task_villa_bin_paper.png" }, { "bins:task_bin_glass.png", "task_villa_bin_glass.png" },
        { "bins:task_bin_rest.png", "task_villa_bin_rest.png" }, { "bins:task_container.png", "task_villa_container.png" },
        { "bins:task_trash_brochure.png", "task_villa_trash_brochure.png" }, { "bins:task_trash_ticket.png", "task_villa_trash_ticket.png" },
        { "bins:task_trash_bottle.png", "task_villa_trash_bottle.png" }, { "bins:task_trash_jar.png", "task_villa_trash_jar.png" },
        { "bins:task_trash_wrapper.png", "task_villa_trash_wrapper.png" }, { "bins:task_trash_apple.png", "task_villa_trash_apple.png" },
        // Route Generator Power, Set Lights Down
        { "route:task_socket.png", "task_villa_socket.png" }, { "route:task_plug.png", "task_villa_plug.png" },
        { "route:task_switch_plate.png", "task_villa_switchplate.png" }, { "route:task_switch_lever.png", "task_villa_switchlever.png" },
        { "fusebox:task_fuse_ok.png", "task_villa_fuse_ok.png" }, { "fusebox:task_fuse_dead.png", "task_villa_fuse_dead.png" },
        { "fusebox:task_fuse_new.png", "task_villa_fuse_new.png" },
        { "fusebox:task_switch_plate.png", "task_villa_switchplate.png" }, { "fusebox:task_switch_lever.png", "task_villa_switchlever.png" },
        // Open the Puzzle Box
        { "hiero:task_cartouche.png", "task_villa_tile.png" },
        { "hiero:task_glyph0.png", "task_villa_rune0.png" }, { "hiero:task_glyph1.png", "task_villa_rune1.png" },
        { "hiero:task_glyph2.png", "task_villa_rune2.png" }, { "hiero:task_glyph3.png", "task_villa_rune3.png" },
        { "hiero:task_glyph4.png", "task_villa_rune4.png" }, { "hiero:task_glyph5.png", "task_villa_rune5.png" },
        { "hiero:task_glyph6.png", "task_villa_rune6.png" }, { "hiero:task_glyph7.png", "task_villa_rune7.png" },
        { "hiero:task_glyph8.png", "task_villa_rune8.png" }, { "hiero:task_glyph9.png", "task_villa_rune9.png" },
        // Smoke in the Chimney
        { "waterworks:task_pipes.png", "task_villa_pipes.png" }, { "waterworks:task_valve.png", "task_villa_wheel.png" },
        { "waterworks:task_card.png", "task_villa_plan.png" },
        // Water the Plants, Roast Marshmallows, Grab Lunch (28.10., GPT-Bogen 21)
        { "watering:task_hold_center.png", "task_villa_water_bench.png" }, { "watering:task_hold_off.png", "task_villa_plant_dry.png" },
        { "watering:task_hold_on.png", "task_villa_plant_wet.png" }, { "watering:task_hold_tool.png", "task_villa_wateringcan.png" },
        { "roast:task_hold_center.png", "task_villa_campfire.png" }, { "roast:task_hold_off.png", "task_villa_marsh_raw.png" },
        { "roast:task_hold_on.png", "task_villa_marsh_gold.png" },
        { "lunch:task_bin_paper.png", "task_villa_plate.png" }, { "lunch:task_bin_glass.png", "task_villa_tray.png" },
        { "lunch:task_bin_rest.png", "task_villa_trashbag.png" },
        { "lunch:task_trash_brochure.png", "task_villa_sandwich.png" }, { "lunch:task_trash_ticket.png", "task_villa_cookie.png" },
        { "lunch:task_trash_bottle.png", "task_villa_soda.png" }, { "lunch:task_trash_jar.png", "task_villa_coffee.png" },
        { "lunch:task_trash_wrapper.png", "task_villa_napkin.png" }, { "lunch:task_trash_apple.png", "task_villa_peel.png" },
        // Feed the Plant (05.11.): Fleisch an jedes der vier Maeuler halten
        { "feed:task_hold_center.png", "task_villa_feed_plant.png" }, { "feed:task_hold_off.png", "task_villa_feed_hungry.png" },
        { "feed:task_hold_on.png", "task_villa_feed_fed.png" }, { "feed:task_hold_tool.png", "task_villa_feed_meat.png" },
    };

    private static Dictionary<string, string> TaskText() => new()
    {
        { "audio:FIND THE ANIMAL", "FIND THE SCENE" }, { "audio:EXHIBIT", "SCENE" },
        { "audio:TRACK 1", "REEL 1" }, { "audio:TRACK 2", "REEL 2" }, { "audio:TRACK 3", "REEL 3" },
        { "bins:PAPER", "SCRIPTS" }, { "bins:GLASS", "BOTTLES" }, { "bins:OTHER", "PROPS" },
        { "climate:TEMP", "KEY" }, { "climate:HUMIDITY", "FILL" }, { "climate:LIGHT", "BACK" },
        { "waterworks:PLAN", "FLUE" },
        { "watering:HOLD ON EACH ONE", "WATER EACH PLANT" }, { "watering:DONE", "ALL WATERED" },
        { "roast:HOLD ON EACH ONE", "TOAST EACH ONE" }, { "roast:DONE", "PERFECTLY GOLDEN" },
        { "lunch:PAPER", "FOOD" }, { "lunch:GLASS", "DRINKS" }, { "lunch:OTHER", "TRASH" },
        { "feed:HOLD ON EACH ONE", "FEED EVERY MOUTH" }, { "feed:DONE", "FED AND HAPPY" },
    };

    private static Dictionary<TaskTypes, string> TaskNames() => new()
    {
        { TaskTypes.FixWiring, "Rewire the Set Lights" },
        { TaskTypes.SwipeCard, "Sign the Call Sheet" },
        { TaskTypes.CalibrateDistributor, "Balance the Dimmer Board" },
        { TaskTypes.ChartCourse, "Chart the Stars" },
        { TaskTypes.CleanO2Filter, "Sweep the Chimney" },
        { TaskTypes.DivertPower, "Route Generator Power" },
        { TaskTypes.PrimeShields, "Light the Ward Candles" },
        { TaskTypes.StabilizeSteering, "Focus the Telescope" },
        { TaskTypes.UnlockManifolds, "Open the Puzzle Box" },
        { TaskTypes.UploadData, "Back Up the Dailies" },
        { TaskTypes.AlignEngineOutput, "Tune the Generator" },
        { TaskTypes.ClearAsteroids, "Shoo the Bats" },
        { TaskTypes.EmptyGarbage, "Take Out the Trash" },
        { TaskTypes.FuelEngines, "Refuel the Generators" },
        { TaskTypes.InspectSample, "Mix the Fake Blood" },
        { TaskTypes.StartReactor, "Set the Seance Table" },
        { TaskTypes.SubmitScan, "Makeup Check" },
        { TaskTypes.ResetReactor, "The Ritual Escalates" },
        { TaskTypes.RestoreOxy, "Smoke in the Chimney" },
        { TaskTypes.FixLights, "Set Lights Down" },
        { TaskTypes.FixComms, "Radio Silence" },
        { TaskTypes.MakeBurger, "Make Burger" },
        { TaskTypes.UnlockSafe, "Unlock the Safe" },
        { TaskTypes.ResetBreakers, "Release the Boiler Pressure" },
        { TaskTypes.FixShower, "Water the Plants" },
        { TaskTypes.CleanToilet, "Roast Marshmallows" },
        { TaskTypes.PutAwayPistols, "Tune the Generator" },
        { TaskTypes.PolishRuby, "Grab Lunch" },
        { TaskTypes.PickUpTowels, "Feed the Plant" },
        // Obergeschoss (17.11.)
        { TaskTypes.SortRecords, "Sort the Family Records" },
        { TaskTypes.DevelopPhotos, "Develop the Set Photos" },
        { TaskTypes.DressMannequin, "Dress the Mannequin" },
        { TaskTypes.RewindTapes, "Rewind the Ghost Tapes" },
        { TaskTypes.PutAwayRifles, "Put Away the Toys" },
        { TaskTypes.StartFans, "Drain the Bloody Bath" },
    };
}
