// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// GraveyardEject - eigene Rauswurf-Szenen auf Ravenhollow Cemetery.
//
// Gleiches Prinzip wie HollowmereEject: die geteilte Engine (Villa/EjectEngine.cs) spielt die Szenen aus
// Resources/graveyard_eject/graveyard_eject.json (Regie: tools/graveyard_eject.py, Grafik:
// tools/gen_graveyard_eject.py). Atlas hat fuer den Schluessel "graveyard" keine Szenen und laesst den
// Rauswurf in Ruhe; die Void-Szene von UC hat Vorrang.
//
// Auswahl: deterministisch aus Spiel-Id, Zahl der Toten, Rauswurf-Nummer und Spieler, damit jeder Client
// dieselbe Szene zeigt, ohne eigenen Netzverkehr. Szenen mit "special_" am Anfang sind aus der Zufallsauswahl
// genommen: "special_sadako" spielt genau dann, wenn der Ausgeworfene das Sadako-Kostuem traegt (der Hut ist
// Teil des synchronisierten Outfits, also sehen alle dasselbe).
//
// Test: UC_HALLOWEEN_EJECT=grave,belfry,... erzwingt die Szenen in dieser Reihenfolge (n-ter Rauswurf -> n-ter
// Eintrag, danach von vorn). Ein Eintrag passt nur, wenn er zur Art des Rauswurfs passt (Skip oder Spieler).

using System;
using System.Linq;
using BepInEx.Unity.IL2CPP.Utils.Collections;
using HarmonyLib;

namespace UnknownsHalloween;

[HarmonyPatch]
internal static class GraveyardEject
{
    private const string LogPrefix = "[Halloween/GraveyardEject]";
    private const string VoidKey = "UnknownsCollection.VoidScene";
    private const string AtlasMapKey = "UnknownsAtlas.ActiveMap";
    private const string SpecialPrefix = "special_";

    private static EjectEngine.Doc _doc;
    private static bool _docTried;
    private static ExileController _seen;
    private static int _exiles;
    private static readonly string[] Forced = (Environment.GetEnvironmentVariable("UC_HALLOWEEN_EJECT") ?? "")
        .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

    private static bool GraveyardActive()
    {
        try { return AppDomain.CurrentDomain.GetData(AtlasMapKey) as string == GraveyardMap.Key; }
        catch { return false; }
    }

    private static bool VoidClaimed()
    {
        try { return AppDomain.CurrentDomain.GetData(VoidKey) is bool b && b; } catch { return false; }
    }

    private static EjectEngine.Doc Doc
    {
        get
        {
            if (_docTried) return _doc;
            _docTried = true;
            EjectEngine.Log = m => HalloweenPlugin.Logger.LogInfo($"{LogPrefix} {m}");
            EjectEngine.Warn = m => HalloweenPlugin.Logger.LogWarning($"{LogPrefix} {m}");
            _doc = EjectEngine.LoadDoc("graveyard_eject.json");
            if (_doc != null) HalloweenPlugin.Logger.LogInfo($"{LogPrefix} {_doc.Scenes.Count} scene(s) loaded");
            return _doc;
        }
    }

    // HudManager.Update statt ExileController.Begin: so haelt es auch Atlas (kein Detour auf Begin).
    [HarmonyPostfix]
    [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
    internal static void HudManager_Update_Postfix()
    {
        if (!GraveyardActive()) { _seen = null; return; }
        try
        {
            var ec = ExileController.Instance;
            if (ec == null) { _seen = null; return; }
            if (ec == _seen) return;
            _seen = ec;
            if (ec.TryCast<SkeldExileController>() == null) return;      // Atlas-Karten sind technisch die Skeld
            if (VoidClaimed()) return;
            Start(ec);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} hook failed: {e}"); }
    }

    /// <summary>Sonderszene fuer das Kostuem des Ausgeworfenen ("special_sadako" ...), sonst null.</summary>
    private static EjectEngine.SceneDef Special(EjectEngine.Doc doc, NetworkedPlayerInfo who)
    {
        string costume = null;
        try { costume = HalloweenCostumes.CostumeKeyOfHat(who.DefaultOutfit?.HatId); } catch { }
        if (costume == null) return null;
        return doc.Scenes.FirstOrDefault(s => !s.Skip && s.Id == SpecialPrefix + costume);
    }

    private static void Start(ExileController ec)
    {
        var doc = Doc;
        if (doc == null) return;
        bool skip = ec.initData == null || ec.initData.networkedPlayer == null;
        int n = _exiles++;
        EjectEngine.SceneDef def = null;
        if (Forced.Length > 0)
            def = doc.Scenes.FirstOrDefault(s => s.Skip == skip && s.Id == Forced[n % Forced.Length]);
        if (def == null && !skip)
            def = Special(doc, ec.initData.networkedPlayer);
        if (def == null)
        {
            var list = doc.Scenes.Where(s => s.Skip == skip && !s.Id.StartsWith(SpecialPrefix, StringComparison.Ordinal)).ToList();
            if (list.Count == 0) return;
            int pid = skip ? 255 : ec.initData.networkedPlayer.PlayerId;
            int dead = 0;
            foreach (var p in GameData.Instance.AllPlayers) if (p != null && p.IsDead) dead++;
            int game = AmongUsClient.Instance != null ? AmongUsClient.Instance.GameId : 0;
            def = list[new Random(pid * 7919 + dead * 104729 + game + n * 31).Next(list.Count)];
        }
        var run = new EjectEngine.Run(def, doc);
        try { run.Setup(ec, null); }
        catch (Exception e)
        {
            HalloweenPlugin.Logger.LogError($"{LogPrefix} setup of {def.Id} failed, vanilla animation stays: {e}");
            run.Release();
            return;
        }
        ec.StopAllCoroutines();
        ec.StartCoroutine(EjectEngine.Play(run).WrapToIl2Cpp());
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} scene {def.Id} (player {(run.P != null ? "yes" : "none")})");
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
    internal static void AmongUsClient_OnGameJoined_Postfix() => _exiles = 0;
}
