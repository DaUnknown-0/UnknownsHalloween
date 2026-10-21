/*
 * Masquerade Ball (2026-10-17): a game mode of Unknown's Halloween. At the start of the round and after every
 * meeting each living player gets one of the Halloween costumes at random and their name disappears; with
 * "Same Color For All" (default) the colours go too, so the costume is the only thing that tells players apart,
 * and it changes after every meeting. In meetings everybody shows up as themselves.
 * Impostors still see each other's names (as with TOR's own hidden-name rule). Voice chat gives voices away,
 * the mode is meant for confusion on the map, not as a perfect disguise.
 *
 * No network traffic: every client draws the same costumes from the same seed (game id + meeting count +
 * player id).
 * The look goes through TOR's setLook, the same path the Camouflager uses; while a camouflage, a morph or the
 * Fungle mushroom mix-up runs, TOR's look wins and the masquerade comes back afterwards.
 * Names: TOR rewrites every name each frame (UpdatePatch in HudManager.Update), so the masquerade clears them
 * afterwards in its own HudManager.Update postfix (a game method, safe from the tiering detour loss).
 *
 * Costumes in the draw: everything except the Xenomorph (role look), the angel ghost (reads as a dead player)
 * and the corpse costume.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using TheOtherRoles;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class Masquerade {
        private const string LogPrefix = "[Halloween/Masquerade]";
        private const int BlackColor = 6;                   // the colour TOR's Camouflager uses
        private static readonly string[] PoolNames = {
            "Halloween Freddy", "Halloween Jason", "Halloween Ghostface", "Halloween Thing",
            "Halloween Predator", "Halloween Sadako", "Halloween Spider", "Halloween BVB Fan",
        };

        public static CustomOption Mode, SameColor;

        internal static void CreateOptions() {
            try {
                var g = CustomOption.CustomOptionType.General;
                Mode = CustomOption.Create(1980, g, "Masquerade Ball", false, null, true, null, "Masquerade Ball");
                SameColor = CustomOption.Create(1981, g, "Masquerade: Same Color For All", true, Mode);
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} options failed: {e}");
            }
        }

        /// <summary>The mode switch as the host set it (HalloweenHandshake gates the start on everybody's packages).</summary>
        internal static bool ModeOn => On(Mode, false);

        private static bool On(CustomOption o, bool fallback) {
            if (Diag && o == Mode) return true;
            try { return o == null ? fallback : o.getBool(); } catch { return fallback; }
        }

        // Self test (UC_HALLOWEEN_DIAG=masquerade): on without the host option, freeplay has no role intro.
        internal static readonly bool Diag = (Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "") == "masquerade";

        /// <summary>Self test: what the end of a meeting does (next part, new costumes).</summary>
        internal static void DiagNextPart() {
            phase++;
            assigned.Clear();
            nextCheck = 0f;
        }

        private static bool introDone;
        private static bool masked;                          // looks applied right now
        private static bool wasMeeting;
        private static int phase;                            // 0 = first part of the round, +1 after every meeting
        private static float nextCheck;
        private static readonly Dictionary<byte, string> assigned = new();
        private static List<string> pool;

        private static bool InRound() {
            try {
                var ac = AmongUsClient.Instance;
                // freeplay stays in "Joined" for the whole round
                return ac != null && (ac.GameState == InnerNet.InnerNetClient.GameStates.Started || ac.NetworkMode == NetworkModes.FreePlay)
                    && ShipStatus.Instance != null && PlayerControl.LocalPlayer != null;
            } catch { return false; }
        }

        private static bool InMeeting() => MeetingHud.Instance != null || ExileController.Instance != null;

        // TOR's own look overrides win while they run.
        private static bool TorLookActive(PlayerControl p) {
            try {
                if (Camouflager.camouflageTimer > 0f || Helpers.MushroomSabotageActive()) return true;
                if (Morphling.morphTimer > 0f && Morphling.morphling == p) return true;
                if (Xenomorph.IsTransformed(p.PlayerId)) return true;
            } catch { }
            return false;
        }

        /// <summary>From the UC tick (every frame).</summary>
        private static float diagLogAt;

        internal static void Tick() {
            try {
                if (!HalloweenCostumes.HatsRegistered) return;      // no costume packages, nothing to dress up in
                if (Diag && Time.time >= diagLogAt) {
                    diagLogAt = Time.time + 2f;
                    string state = "-";
                    try { state = AmongUsClient.Instance != null ? AmongUsClient.Instance.GameState.ToString() + "/" + AmongUsClient.Instance.NetworkMode : "no client"; } catch { }
                    HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} diag: inRound {InRound()} state {state} ship {ShipStatus.Instance != null} intro {introDone} masked {masked} assigned {assigned.Count}");
                }
                if (!InRound()) {
                    if (masked || assigned.Count > 0) Reset();
                    introDone = false;
                    phase = 0;
                    return;
                }
                if (!On(Mode, false) || !(introDone || Diag)) {
                    if (masked) RestoreAll();
                    return;
                }
                if (InMeeting()) {
                    if (masked) RestoreAll();
                    wasMeeting = true;
                    return;
                }
                if (wasMeeting) {
                    wasMeeting = false;
                    phase++;
                    assigned.Clear();
                }
                if (assigned.Count == 0) Assign();
                if (Time.time < nextCheck) return;
                nextCheck = Time.time + 0.25f;
                Apply();
            } catch (Exception e) {
                if (!loggedError) { loggedError = true; HalloweenPlugin.Logger?.LogError($"{LogPrefix} tick failed (logged once): {e}"); }
            }
        }

        private static bool loggedError;

        private static void Assign() {
            if (pool == null) {
                pool = PoolNames.Select(UCHatsId).Where(id => !string.IsNullOrEmpty(id)).ToList();
                HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {pool.Count} costume(s) in the draw");
            }
            if (pool.Count == 0) return;
            foreach (var data in GameData.Instance.AllPlayers.ToArray())
                assigned[data.PlayerId] = HatFor(data.PlayerId);
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} part {phase}: {assigned.Count} player(s) dressed up");
        }

        // Same game id, part and player id give the same costume on every client - no message needed, and a
        // player who shows up after the draw (freeplay dummies) still gets the matching one.
        private static string HatFor(byte playerId) {
            int gameId = 0;
            try { gameId = AmongUsClient.Instance.GameId; } catch { }
            var rng = new System.Random(unchecked(gameId * 7919 + phase * 104729 + playerId * 1009 + 17));
            return pool[rng.Next(pool.Count)];
        }

        private static string UCHatsId(string hatName) {
            try { return UnknownsCollection.UCHats.HatIdOf(hatName); } catch { return null; }
        }

        private static void Apply() {
            bool sameColor = On(SameColor, true);
            foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                if (p == null || p.Data == null || p.Data.IsDead || p.Data.Disconnected) continue;
                if (!assigned.TryGetValue(p.PlayerId, out var hatId)) {
                    if (pool == null || pool.Count == 0) continue;
                    assigned[p.PlayerId] = hatId = HatFor(p.PlayerId);
                }
                if (TorLookActive(p)) continue;
                string worn = null;
                try { worn = p.cosmetics.hat.Hat != null ? p.cosmetics.hat.Hat.ProdId : null; } catch { }
                if (worn == hatId && masked) continue;
                int color = sameColor ? BlackColor : p.Data.DefaultOutfit.ColorId;
                p.setLook("", color, hatId, "", "", "");
            }
            masked = true;
        }

        private static void RestoreAll() {
            foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                try {
                    if (p == null || p.Data == null || TorLookActive(p)) continue;
                    p.setDefaultLook();
                } catch { }
            }
            masked = false;
        }

        private static void Reset() {
            masked = false;
            wasMeeting = false;
            assigned.Clear();
        }

        [HarmonyPatch(typeof(IntroCutscene), nameof(IntroCutscene.OnDestroy))]
        static class IntroEndPatch {
            static void Postfix() => introDone = true;
        }

        // After TOR's name update (UpdatePatch): names of other players stay empty while masked.
        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class NamePatch {
            [HarmonyPriority(Priority.Last)]
            static void Postfix() {
                if (!masked) return;
                try {
                    var me = PlayerControl.LocalPlayer;
                    if (me == null || me.Data == null) return;
                    bool meImp = me.Data.Role != null && me.Data.Role.IsImpostor;
                    foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                        if (p == null || p == me || p.Data == null) continue;
                        if (meImp && p.Data.Role != null && p.Data.Role.IsImpostor) continue;    // impostors know each other
                        var t = p.cosmetics != null ? p.cosmetics.nameText : null;
                        if (t != null && t.text.Length > 0) t.text = "";
                    }
                } catch { }
            }
        }
    }
}
