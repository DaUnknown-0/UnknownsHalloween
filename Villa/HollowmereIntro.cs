// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereIntro - Vorspann von Hollowmere Manor vor dem Rollen-Intro.
//
// Seit 24.10. ein gerenderter 3D-Film (Ich-Perspektive, der Geist-Lord fuehrt durchs Haus, ~59 s, 24 Bilder pro
// Sekunde, Stimme + Geraeusche + Untertitel in Deutsch und Englisch). Abgespielt wird er von Unknown's Atlas
// (AtlasCinematic): dort liegen Host-Entscheidung (Option 1728 "Atlas: Map Intro", einmal pro Abend / jede Runde /
// aus), Ueberspringen durch den Host fuer alle und die Darstellung. Halloween meldet nur die Karte und liefert die
// Daten aus seinem Asset-Paket villa_intro.hwp (Eintraege "villa_intro/meta.json", "villa_intro/f0000.jpg" ...,
// gebaut von Assets/Cinematics/_common/make_pack.py, verpackt von tools/build_assets_repo.py).
//
// Die alte Bildfolge (84 Bilder, 12 fps) und Option 1961 "Hollowmere Intro" sind damit weg. Das Modulbyte 236 auf
// UC-Kanal 230 bleibt fuer die Mechaniken der Villa (HollowmereWorld, Sub 2+); Sub 1 (alte Intro-Ansage) wird
// ignoriert.

using System;
using System.Runtime.CompilerServices;
using Hazel;
using UnknownsCollection;

namespace UnknownsHalloween;

internal static class HollowmereIntro
{
    private const string LogPrefix = "[Halloween/VillaIntro]";
    internal const byte RpcModule = 236;            // Modulbyte auf UCRpc.CallId 230 (Hollowmere Manor)
    private const byte SubIntro = 1;
    private const string Pack = "villa_intro/";

    internal static void Init()
    {
        try { UCRpc.Register(RpcModule, HandleRpc); }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} rpc registration failed: {e}"); }
        try { RegisterWithAtlas(); }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} needs Unknown's Atlas 1.0.3.1 or newer for the intro ({e.GetType().Name})"); }
    }

    // Eigene Methode: fehlt AtlasCinematic (altes Atlas), scheitert erst ihr JIT, nicht Init.
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static void RegisterWithAtlas()
    {
        UnknownsAtlas.AtlasCinematic.RegisterIntro(HollowmereMap.Key, name => HalloweenAssets.Read(HalloweenAssets.ResRoot + Pack + name));
    }

    private static void HandleRpc(MessageReader reader)
    {
        try
        {
            byte sub = reader.ReadByte();
            if (sub == SubIntro) return;            // alte Intro-Ansage (vor 24.10.), spielt Atlas jetzt selbst
            if (sub >= HollowmereWorld.SubRitualFirst) { HollowmereWorld.HandleRitualRpc(sub, reader); return; }   // Manor-Pentagramm (25.10.)
            if (sub >= GraveyardWorld.SubFirst) { GraveyardWorld.HandleRpc(sub, reader); return; }   // Friedhof (Pentagramm, 24.10.)
            HollowmereWorld.HandleRpc(sub, reader);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} rpc failed: {e.Message}"); }
    }
}
