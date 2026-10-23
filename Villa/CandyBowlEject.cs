// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// CandyBowlEject - die Rauswurf-Szene "Die Suessigkeitenschuessel" auf den Vanilla-Karten.
//
// Sobald die Halloween-Optik (Option 2100) an ist, spielt ein echter Rauswurf auf Skeld, Mira, Polus, Airship und
// Fungle nicht mehr die Weltraum-Animation des Spiels, sondern die Szene aus Resources/candy_eject/candy_eject.json
// (Regie: tools/candy_eject.py, Grafik: tools/gen_candy_eject.py, Klaenge: tools/gen_candy_sfx.py) ueber die geteilte
// Engine (Villa/EjectEngine.cs). Die Bilder kommen mit dem Paket candy_eject.hwp (plus den Partikeln aus
// villa_eject.hwp); solange eines fehlt, bleibt der Vanilla-Rauswurf. Skips und Unentschieden gehoeren weiter der
// Void-Szene von Unknown's Collection, Atlas- und Halloween-Karten haben eigene Szenen, Submerged bleibt unberuehrt.
//
// Jeder Client entscheidet fuer sich (rein kosmetisch, kein Netzverkehr); Spieler ohne die Mod sehen die Vanilla-
// Animation. Die Textzeile bekommt einen passenden Vorspann (HwLookMeeting, Pool "candy"), egal in welcher
// Reihenfolge die beiden HudManager.Update-Haken denselben ExileController zuerst sehen.
//
// Test: UC_HALLOWEEN_EJECT=bowl erzwingt die Szene (wie bei den Friedhofsszenen; nur Spieler-Szenen passen).

using System;
using System.Linq;
using BepInEx.Unity.IL2CPP.Utils.Collections;
using HarmonyLib;

namespace UnknownsHalloween;

[HarmonyPatch]
internal static class CandyBowlEject
{
    private const string LogPrefix = "[Halloween/CandyEject]";
    private const string VoidKey = "UnknownsCollection.VoidScene";

    private static EjectEngine.Doc _doc;
    private static bool _docTried, _warnedPackages;
    private static ExileController _seen;
    private static int _exiles;
    private static readonly string[] Forced = (Environment.GetEnvironmentVariable("UC_HALLOWEEN_EJECT") ?? "")
        .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

    /// <summary>Der ExileController, auf dem die Szene gerade laeuft (fuer den Vorspann der Textzeile).</summary>
    internal static ExileController Playing;

    private static bool VoidClaimed()
    {
        try { return AppDomain.CurrentDomain.GetData(VoidKey) is bool b && b; } catch { return false; }
    }

    private static bool PackagesReady => HalloweenAssets.Ready("candy_eject") && HalloweenAssets.Ready("villa_eject");

    private static EjectEngine.Doc Doc
    {
        get
        {
            if (_docTried) return _doc;
            _docTried = true;
            EjectEngine.Log = m => HalloweenPlugin.Logger.LogInfo($"{LogPrefix} {m}");
            EjectEngine.Warn = m => HalloweenPlugin.Logger.LogWarning($"{LogPrefix} {m}");
            _doc = EjectEngine.LoadDoc("candy_eject.json");
            if (_doc != null) HalloweenPlugin.Logger.LogInfo($"{LogPrefix} {_doc.Scenes.Count} scene(s) loaded");
            return _doc;
        }
    }

    // HudManager.Update statt ExileController.Begin (kein Detour auf eine kleine Spielmethode), wie die anderen Szenen.
    [HarmonyPostfix]
    [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
    internal static void HudManager_Update_Postfix()
    {
        try
        {
            var ec = ExileController.Instance;
            if (ec == null) { _seen = null; Playing = null; return; }
            if (ec == _seen) return;
            _seen = ec;
            if (!HwLook.LookEnabled) return;
            if (HwMechanics.AtlasMap() != null) return;                        // Atlas- und Halloween-Karten: eigene Szenen
            if (VoidClaimed()) return;
            if (ec.initData == null || ec.initData.networkedPlayer == null) return;   // Skip oder Unentschieden: Void
            if (HwLookMeeting.MapKind(ec) == null) return;                      // Submerged und Unbekanntes
            if (!PackagesReady)
            {
                if (!_warnedPackages) { _warnedPackages = true; HalloweenPlugin.Logger.LogInfo($"{LogPrefix} packages not ready yet, vanilla animation stays"); }
                return;
            }
            Start(ec);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} hook failed: {e}"); }
    }

    private static void Start(ExileController ec)
    {
        var doc = Doc;
        if (doc == null) return;
        int n = _exiles++;
        EjectEngine.SceneDef def = null;
        if (Forced.Length > 0)
            def = doc.Scenes.FirstOrDefault(s => !s.Skip && s.Id == Forced[n % Forced.Length]);
        if (def == null)
        {
            var list = doc.Scenes.Where(s => !s.Skip).ToList();
            if (list.Count == 0) return;
            int pid = ec.initData.networkedPlayer.PlayerId;
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
        Playing = ec;
        try { HwLookMeeting.CandyLead(ec); } catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} lead line: {e.Message}"); }
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} scene {def.Id} on {HwLookMeeting.MapKind(ec)} (player {(run.P != null ? "yes" : "none")})");
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
    internal static void AmongUsClient_OnGameJoined_Postfix() { _exiles = 0; Playing = null; _seen = null; }
}
