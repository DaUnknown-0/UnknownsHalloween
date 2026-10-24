// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HwGuessSpell - "Avada Kedavra ... KURWA!" bei jedem Guesser-Schuss (User 24.10.).
//
// - Wann: sobald im Meeting eine Spielerplatte tot wird, solange abgestimmt wird. Das ist jeder Guess: beim Treffer
//   stirbt das Ziel, beim Fehlschuss der Guesser. Beide bekommen denselben Klang, sonst verriete er, wie der Schuss
//   ausging (User: "bei jedem guess und fail guess, da sonst spielrelevante infos gegeben werden"). Stirbt ein Lover-
//   Partner im selben Moment mit, laeuft der Klang trotzdem nur einmal (Sperre 1,5 s).
// - Wie: MeetingHud.Update-Postfix (Il2Cpp, kein Patch auf TORs guesserShoot - der ist verwaltet und koennte durch
//   Tiering still ausfallen). Jeder Client spielt selbst, kein RPC. Ein Spieler, der das Meeting verlaesst, zaehlt
//   nicht (Disconnected).
// - Klang: Resources/sounds/sfx_avada.wav (2,9 s, mono, 16 bit, 22050 Hz), abgespielt ueber EjectSynth (folgt der
//   Effekt-Lautstaerke). Quelle: myinstants "avada-kedavra-kurwa" (wie YouTube P1tE7S1F4-4), auf "Avada Kedavra!
//   Kurwa!" gekuerzt.
// - Schalter: Host-Option 2102 "Guesser Spell Sound" (General, unter Halloween Look, Standard an) und lokal
//   [Sounds] GuesserSpellSound in der Config (der Clip enthaelt einen Fluch).

using System;
using System.Collections.Generic;
using BepInEx.Configuration;
using HarmonyLib;
using TheOtherRoles;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HwGuessSpell {
        internal static CustomOption Option;
        internal static ConfigEntry<bool> LocalSwitch;

        private static readonly HashSet<byte> dead = new HashSet<byte>();
        private static float lastPlay = -10f;
        internal static int Plays;                       // for the self test (HwLookDiag "guessspell")
        private const float Gap = 1.5f;

        private static bool Enabled() {
            try {
                if (LocalSwitch != null && !LocalSwitch.Value) return false;
                return Option == null || Option.getBool();
            } catch { return false; }
        }

        [HarmonyPatch(typeof(MeetingHud), nameof(MeetingHud.Start))]
        static class StartPatch {
            public static void Postfix(MeetingHud __instance) {
                dead.Clear();
                try {
                    foreach (var pva in __instance.playerStates)
                        if (pva != null && pva.AmDead) dead.Add(pva.TargetPlayerId);
                } catch { }
            }
        }

        [HarmonyPatch(typeof(MeetingHud), nameof(MeetingHud.Update))]
        static class UpdatePatch {
            public static void Postfix(MeetingHud __instance) {
                try {
                    if (__instance == null || __instance.playerStates == null) return;
                    bool voting = __instance.state != MeetingHud.VoteStates.Results && __instance.state != MeetingHud.VoteStates.Proceeding;
                    bool shot = false;
                    foreach (var pva in __instance.playerStates) {
                        if (pva == null || !pva.AmDead || !dead.Add(pva.TargetPlayerId)) continue;
                        if (!voting) continue;
                        var p = Helpers.playerById(pva.TargetPlayerId);
                        if (p != null && p.Data != null && p.Data.IsDead && !p.Data.Disconnected) shot = true;
                    }
                    if (!shot || Time.time - lastPlay < Gap || !Enabled()) return;
                    lastPlay = Time.time;
                    Plays++;
                    EjectSynth.Play("avada", 1.1f);
                    HalloweenPlugin.Logger?.LogInfo("[Halloween] guesser spell sound.");
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogWarning($"[Halloween] guesser spell: {e.Message}");
                }
            }
        }
    }
}
