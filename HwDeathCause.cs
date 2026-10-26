// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * HwDeathCause - who killed a player that "killed himself" (User 2026-10-26).
 *
 * The Midnight Bonbon and the demon of the pentagram (Manor and cemetery) kill through TOR's own murder path with
 * victim = killer. TOR, the kill feeds and the round export therefore saw a self kill. Two fixes:
 *   - AppDomain "Unknowns.DeathCause" (Func<byte, string>): the cause for a dead player id, null for a normal death.
 *     Read by the kill feed for ghosts, the round replay and the round export; none of them knows this mod.
 *   - TOR's Medium: the soul tells what took it instead of "my killer is the <own role>" or "a darker color killed me".
 */

using System;
using System.Runtime.CompilerServices;
using HarmonyLib;
using TheOtherRoles;
using static TheOtherRoles.TheOtherRoles;

namespace UnknownsHalloween
{
    internal static class HwDeathCause
    {
        internal const string AppKey = "Unknowns.DeathCause";
        internal const string Bonbon = "Midnight Bonbon";
        internal const string Demon = "The Demon";

        internal static void Register()
        {
            try { AppDomain.CurrentDomain.SetData(AppKey, (Func<byte, string>)Of); }
            catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"[Halloween] death cause not registered: {e.Message}"); }
        }

        internal static string Of(byte pid)
        {
            try
            {
                if (TrickOrTreat.poisoned.Contains(pid)) return Bonbon;
                if (IsDemonVictim(pid)) return Demon;
            }
            catch { }
            return null;
        }

        // own method: GraveyardWorld lives with the Atlas maps and may not load without Unknown's Atlas
        [MethodImpl(MethodImplOptions.NoInlining)]
        private static bool IsDemonVictim(byte pid)
        {
            try { return GraveyardWorld.DemonVictims.Contains(pid); } catch { return false; }
        }

        private static readonly Random rnd = new();

        private static readonly (string en, string de)[] BonbonLines =
        {
            ("It was wrapped so nicely. Silver foil, a violet shimmer... nobody wraps a candy like that unless it is a trap.",
             "So hübsch eingewickelt. Silberfolie, violetter Schimmer ... so packt man nur eine Falle ein."),
            ("Midnight Bonbon. Tastes like dark chocolate, regret and a little bit of afterlife.",
             "Midnight Bonbon. Schmeckt nach Zartbitter, Reue und ein bisschen Jenseits."),
            ("Mom always said: never take candy from strangers. She never said anything about candy just lying around.",
             "Mama hat immer gesagt: Nimm keine Süßigkeiten von Fremden. Von herumliegenden hat sie nichts gesagt."),
            ("No impostor needed. I managed this all by myself, with one single bite.",
             "Dafür brauchte es keinen Impostor. Das habe ich ganz allein geschafft, mit einem einzigen Bissen."),
        };

        private static readonly (string en, string de)[] DemonLines =
        {
            ("Five candles, one circle, zero common sense. The Demon only had to wait.",
             "Fünf Kerzen, ein Kreis, null Verstand. The Demon musste nur warten."),
            ("Pro tip: when the floor starts glowing red, do not stand on it.",
             "Kleiner Tipp: Wenn der Boden rot glüht, stell dich nicht drauf."),
            ("I wanted to see what happens when all the candles burn. Now I know. It has horns.",
             "Ich wollte wissen, was passiert, wenn alle Kerzen brennen. Jetzt weiß ich es. Es hat Hörner."),
            ("Nobody killed me. Something came up from below and took me with it.",
             "Mich hat niemand getötet. Etwas kam von unten herauf und hat mich mitgenommen."),
        };

        // The soul's answer. TOR only takes its special lines (Sheriff misfire, Lovers, ...) for real self kills; the
        // random rest reads the "killer", who is the victim here. Keeps TOR's appendix ("When you asked, ...").
        [HarmonyPatch(typeof(Medium), nameof(Medium.getInfo))]
        static class MediumInfoPatch
        {
            public static void Postfix(PlayerControl target, PlayerControl killer, ref string __result)
            {
                try
                {
                    if (target == null || killer == null || target.PlayerId != killer.PlayerId || __result == null) return;
                    string cause = Of(target.PlayerId);
                    if (cause == null) return;
                    var lines = cause == Bonbon ? BonbonLines : DemonLines;
                    var pick = lines[rnd.Next(lines.Length)];
                    string line = TrickOrTreat.De() ? pick.de : pick.en;
                    string header = (target.Data?.PlayerName ?? "?") + "'s Soul:\n";
                    int extra = __result.IndexOf("\nWhen you asked", StringComparison.Ordinal);
                    __result = header + line + (extra >= 0 ? __result.Substring(extra) : "");
                }
                catch { }
            }
        }
    }
}
