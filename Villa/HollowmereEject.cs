// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereEject - eigene Rauswurf-Szenen auf Hollowmere Manor.
//
// Gleiches Prinzip wie die Atlas-Karten und die Void-Szene von Unknown's Collection: die Szene spielt die
// geteilte Engine (Villa/EjectEngine.cs, wortgleich zu Atlas/UC bis auf die namespace-Zeile) aus
// Resources/villa/villa_eject.json, die Grafik liegt daneben als villa_eject_*.png. Atlas selbst hat fuer
// den Schluessel "villa" keine Szenen und laesst den Rauswurf in Ruhe; die Void-Szene von UC hat Vorrang.
//
// Auswahl: deterministisch aus Spiel-Id, Zahl der Toten, Rauswurf-Nummer und Spieler, damit jeder Client
// dieselbe Szene zeigt, ohne eigenen Netzverkehr. Fehlt die JSON (Grafik noch nicht fertig), bleibt der
// Vanilla-Rauswurf.

using System;
using System.Collections.Generic;
using System.Linq;
using BepInEx.Unity.IL2CPP.Utils.Collections;
using HarmonyLib;
using UnityEngine;

namespace UnknownsHalloween;

[HarmonyPatch]
internal static class HollowmereEject
{
    private const string LogPrefix = "[Halloween/VillaEject]";
    private const string VoidKey = "UnknownsCollection.VoidScene";
    private const string AtlasMapKey = "UnknownsAtlas.ActiveMap";

    private static EjectEngine.Doc _doc;
    private static bool _docTried;
    private static ExileController _seen;
    private static int _exiles;

    private static bool VillaActive()
    {
        try { return AppDomain.CurrentDomain.GetData(AtlasMapKey) as string == HollowmereMap.Key; }
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
            _doc = EjectEngine.LoadDoc("villa_eject.json");
            if (_doc != null) HalloweenPlugin.Logger.LogInfo($"{LogPrefix} {_doc.Scenes.Count} scene(s) loaded");
            return _doc;
        }
    }

    // HudManager.Update statt ExileController.Begin: so haelt es auch Atlas (kein Detour auf Begin).
    [HarmonyPostfix]
    [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
    internal static void HudManager_Update_Postfix()
    {
        if (!VillaActive()) { _seen = null; return; }
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

    private static void Start(ExileController ec)
    {
        var doc = Doc;
        if (doc == null) return;
        bool skip = ec.initData == null || ec.initData.networkedPlayer == null;
        var list = doc.Scenes.Where(s => s.Skip == skip).ToList();
        if (list.Count == 0) return;
        int pid = skip ? 255 : ec.initData.networkedPlayer.PlayerId;
        int dead = 0;
        foreach (var p in GameData.Instance.AllPlayers) if (p != null && p.IsDead) dead++;
        int game = AmongUsClient.Instance != null ? AmongUsClient.Instance.GameId : 0;
        var def = list[new System.Random(pid * 7919 + dead * 104729 + game + _exiles * 31).Next(list.Count)];
        _exiles++;
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
