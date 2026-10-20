// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// GraveyardMap - die Halloween-Karte "Ravenhollow Cemetery" (Friedhof mit Gruft) fuer Unknown's Atlas (2026-10-17).
//
// Erste Halloween-Karte im Atlas-Dateiformat: tools/gen_graveyard.py schreibt map.json und das Kartenpaket nach
// Resources/graveyard, die csproj bettet sie als "UnknownsHalloween.Resources.graveyard.<datei>" ein, und Atlas liest die
// Datei (AtlasMapFile.Read, ab Atlas mit Kartenformat). Mit aelterem Atlas meldet sich die Karte einfach nicht an.
// Grafik: tools/gen_graveyard.py (Boden, Objekte, Konsolen); Mechaniken: GraveyardWorld.cs.

using System;
using System.IO;
using System.Reflection;
using UnknownsAtlas;

namespace UnknownsHalloween;

internal static class GraveyardMap
{
    public const string Key = "graveyard";
    private const string Ns = "UnknownsHalloween.Resources.graveyard";

    internal static void Register()
    {
        if (typeof(AtlasMaps).Assembly.GetType("UnknownsAtlas.AtlasMapFile") == null)
        {
            HalloweenPlugin.Logger.LogWarning("[Halloween/Graveyard] Unknown's Atlas is too old for map files - Ravenhollow Cemetery not registered");
            return;
        }
        RegisterWithMapFile();
    }

    // Separate method: AtlasMapFile is only resolved once the check above has passed.
    [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
    private static void RegisterWithMapFile()
    {
        // DLL plus asset packages: map.json, button, icon and minimap are embedded, the rest comes with the packages
        var asm = HalloweenAssets.ResourceAssembly;
        string json;
        using (var s = asm.GetManifestResourceStream(Ns + ".map.json"))
        {
            if (s == null) { HalloweenPlugin.Logger.LogError("[Halloween/Graveyard] map.json not embedded"); return; }
            using var r = new StreamReader(s);
            json = r.ReadToEnd();
        }
        var probe = AtlasMapFile.Read(json, asm, Ns);           // fails loud here, not at the first round
        GraveyardWorld.Init();
        // joins Atlas once floor, props, consoles, minigames and eject art are there (HalloweenAssets)
        if (!HalloweenAssets.Ready("graveyard_"))
            HalloweenPlugin.Logger.LogInfo($"[Halloween/Graveyard] {probe.DisplayName} waits for its asset packages");
        HalloweenAssets.WhenReady("graveyard_", () =>
        {
            bool ok = AtlasMaps.Register(Key, "Ravenhollow", () => Make(json, asm), asm, Ns,
                button: "button_graveyard.png", icon: "icon_graveyard.png", contentVersion: HalloweenPlugin.PluginVersion);
            HalloweenPlugin.Logger.LogInfo($"[Halloween/Graveyard] {probe.DisplayName} {(ok ? "registered with" : "NOT registered with")} Unknown's Atlas " +
                                           $"({probe.Rooms?.Length ?? 0} rooms)");
        });
    }

    // Je Bau eine frische Definition samt Welt-Mechanik (Nebel, Totenglocke, Miasma, Laternen).
    private static AtlasMapDef Make(string json, Assembly asm)
    {
        var d = AtlasMapFile.Read(json, asm, Ns);
        d.World = new GraveyardWorld(d);
        return d;
    }
}
