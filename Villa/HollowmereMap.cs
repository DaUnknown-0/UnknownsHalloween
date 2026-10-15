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

    internal static void Register()
    {
        try
        {
            Size = CustomOption.Create(1960, CustomOption.CustomOptionType.General, "Hollowmere Manor Size",
                new[] { "Small", "Large" }, null, true, null, "Hollowmere Manor");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"[Halloween/Villa] size option failed: {e}"); }

        HollowmereIntro.Init();

        bool ok = AtlasMaps.Register(Key, "Hollowmere", Make, typeof(HollowmereMap).Assembly, ResourceNamespace,
            button: "button_villa.png", icon: "icon_villa.png", contentVersion: HalloweenPlugin.PluginVersion);
        HalloweenPlugin.Logger.LogInfo($"[Halloween/Villa] {DisplayName} {(ok ? "registered with" : "NOT registered with")} Unknown's Atlas (API {AtlasMaps.ApiVersion})");
    }

    // Diagnose: UC_HALLOWEEN_DIAG=villalarge erzwingt die grosse Variante (Autotest ohne Eingriff in die TOR-Optionen)
    internal static bool Large =>
        (Size != null && Size.getSelection() == 1) ||
        (Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "").Contains("villalarge");

    private static AtlasMapDef Make()
    {
        var d = Large ? FromLarge() : FromSmall();
        d.Key = Key;
        d.DisplayName = DisplayName;
        d.ResourcePrefix = "villa";
        d.ResourceAssembly = typeof(HollowmereMap).Assembly;
        d.ResourceNamespace = ResourceNamespace;
        d.BuiltInEffects = false;
        d.CameraColor = new Color(0x16 / 255f, 0x10 / 255f, 0x14 / 255f);
        d.TaskNames = TaskNames();
        return d;
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
    };
}
