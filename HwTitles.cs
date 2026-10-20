// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * Halloween titles of the evening (idea F2, 2026-10-20): five titles in the session statistics of TOR - Forgotten
 * Fixes (UTS), next to its own ones, through the neutral title contract there (UTS does not know this mod):
 *   AppDomain "UTS.SessionStats.AddTitle"  Action<string id, int order, Func<string> name, Func<int, string> value>
 *   AppDomain "UTS.SessionStats.Count"     Action<string id, byte playerId, int amount>
 * Registered once UTS has published the contract (tried on the main menu, in the lobby and every few seconds of the
 * tick); without UTS nothing happens.
 *
 *   Final Girl      most often the last crewmate alive when a round ends (no impostor, no neutral)
 *   Candy Glutton   most candies eaten (Trick or Treat, the Midnight Bonbon included)
 *   Midnight Snack  most often caught by the Midnight Bonbon
 *   Most Haunted    most often the first to die in a round (disconnects do not count)
 *   Mirror Gazer    most often seen in a Haunted Mirror (each new visit in front of a mirror counts once)
 *
 * Every client counts what it sees, the same way UTS keeps its own statistics, and the host's numbers are shown:
 * candies come from Trick or Treat's host-sent "eaten" message (hook in TrickOrTreat.ApplyEaten), deaths and the end
 * of the round are seen by everybody, the mirrors are pure geometry (HwMirrors places them alike on every client and
 * shows the same players). No message of our own, so no RPC byte.
 *
 * Option 2120 (General tab, heading "Halloween Titles"): on by default; off = nothing is counted.
 * Self test: UC_HALLOWEEN_DIAG=titles (freeplay: counts for the dummies through every path, logs what UTS took).
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using UnityEngine;
using TheOtherRoles;
using UnknownsCollection;
using Types = TheOtherRoles.CustomOption.CustomOptionType;

namespace UnknownsHalloween {
    internal static class HwTitles {
        private const string LogPrefix = "[Halloween/Titles]";
        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");
        private static void Warn(string s) => HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {s}");

        internal const string FinalGirlId = "hw.finalgirl", CandyId = "hw.candy", MidnightId = "hw.midnight",
                              HauntedId = "hw.haunted", MirrorId = "hw.mirror";

        private const string AddTitleKey = "UTS.SessionStats.AddTitle", CountKey = "UTS.SessionStats.Count";

        // ---- option 2120 ----
        public static CustomOption On;
        internal static void CreateOptions() {
            try {
                On = CustomOption.Create(2120, Types.General, "Halloween Titles Of The Evening", true, null, true, null, "Halloween Titles");
            } catch (Exception e) { Warn($"options failed: {e.Message}"); }
        }
        private static bool Counting() { if (Diag) return true; try { return On == null || On.getBool(); } catch { return true; } }

        private static bool De() => HwMechanics.De();

        // ---- registration with UTS ----
        private static bool registered;
        private static float nextTry;
        private static Action<string, byte, int> count;

        internal static void TryRegister() {
            if (registered || Time.realtimeSinceStartup < nextTry) return;
            nextTry = Time.realtimeSinceStartup + 3f;
            try {
                if (AppDomain.CurrentDomain.GetData(AddTitleKey) is not Action<string, int, Func<string>, Func<int, string>> add) return;
                count = AppDomain.CurrentDomain.GetData(CountKey) as Action<string, byte, int>;
                // after UTS' own nine titles, in the order of the idea list
                add(FinalGirlId, 100, () => "Final Girl",
                    n => De() ? $"{n}x als letzte Crew übrig" : $"last crewmate standing {n}x");
                add(CandyId, 101, () => "Candy Glutton",
                    n => De() ? $"{n} Süßigkeiten gegessen" : $"{n} {(n == 1 ? "candy" : "candies")} eaten");
                add(MidnightId, 102, () => "Midnight Snack",
                    n => De() ? $"{n}x vom Midnight Bonbon erwischt" : $"caught by the Midnight Bonbon {n}x");
                add(HauntedId, 103, () => "Most Haunted",
                    n => De() ? $"{n}x als Erste(r) gestorben" : $"died first {n}x");
                add(MirrorId, 104, () => "Mirror Gazer",
                    n => De() ? $"{n}x im Spukspiegel gesehen" : $"seen in the haunted mirrors {n}x");
                registered = true;
                Log($"five titles added to the session statistics (counting {(count != null ? "ready" : "MISSING")}).");
            } catch (Exception e) { registered = true; Warn($"registration failed: {e.Message}"); }
        }

        internal static int Counted;   // diagnostics: counts handed to UTS this session

        private static void Count(string id, byte pid, int n = 1) {
            if (!Counting()) return;
            if (count == null) { TryRegister(); if (count == null) return; }
            try { count(id, pid, n); Counted++; }
            catch (Exception e) { Warn($"count {id} failed: {e.Message}"); }
        }

        // ---- hooks of the other Halloween features ----
        /// <summary>Trick or Treat: a player ate a candy (every client, from the host's eaten message).</summary>
        internal static void OnCandyEaten(byte pid, bool midnight) {
            Count(CandyId, pid);
            if (midnight) Count(MidnightId, pid);
        }

        // ---- per round: first death, mirrors ----
        private static IntPtr roundShip;
        private static readonly HashSet<byte> dead = new();
        private static bool firstDeathCounted;
        private const float MirrorReach = 2.6f;                     // as HwMirrors.Reach
        private static readonly Dictionary<(int, byte), float> inFront = new();   // (mirror, player) -> last seen

        private static void NewRound() {
            dead.Clear();
            inFront.Clear();
            firstDeathCounted = false;
            // whoever is already dead at the start (a ghost joining late) is no first death
            foreach (var p in PlayerControl.AllPlayerControls.ToArray())
                if (p != null && p.Data != null && p.Data.IsDead) dead.Add(p.PlayerId);
        }

        internal static void Tick() {
            TryRegister();
            DiagTick();
            if (!HwMechanics.InRound()) { roundShip = IntPtr.Zero; return; }
            var ship = ShipStatus.Instance;
            if (ship.Pointer != roundShip) { roundShip = ship.Pointer; NewRound(); }
            if (HwMechanics.FreePlay() && !Diag) return;            // freeplay dummies die and stand up again

            foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                if (p == null || p.Data == null || p.Data.Disconnected || !p.Data.IsDead || dead.Contains(p.PlayerId)) continue;
                dead.Add(p.PlayerId);
                if (!firstDeathCounted) {
                    firstDeathCounted = true;
                    Count(HauntedId, p.PlayerId);
                    Log($"first death of the round: {p.Data.PlayerName}");
                }
            }
            MirrorTick();
        }

        // a new visit in front of a mirror counts once; leaving for 4 s ends the visit
        private static void MirrorTick() {
            if (!HwMirrors.Enabled() || HwMechanics.InMeeting() || HwMirrors.mirrors.Count == 0) { inFront.Clear(); return; }
            float now = Time.time;
            for (int i = 0; i < HwMirrors.mirrors.Count; i++) {
                var m = HwMirrors.mirrors[i];
                if (m?.Go == null) continue;
                var front = m.Foot + new Vector2(0f, -0.55f);
                foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                    if (!HwMechanics.IsAlive(p)) continue;
                    try { if (p.inVent) continue; } catch { }
                    var pos = p.GetTruePosition();
                    if ((pos - front).magnitude >= MirrorReach || pos.y >= m.Foot.y + 0.2f) continue;
                    var key = (i, p.PlayerId);
                    if (!inFront.TryGetValue(key, out var last) || now - last > 4f) Count(MirrorId, p.PlayerId);
                    inFront[key] = now;
                }
            }
        }

        // ---- the end of the round: the last crewmate standing ----
        internal static void RoundEnded() {
            try {
                if (!HwMechanics.InRound() && !Diag) return;
                var crew = new List<PlayerControl>();
                foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                    if (!HwMechanics.IsAlive(p) || HwMechanics.IsImp(p)) continue;
                    List<RoleInfo> roles = null;
                    try { roles = RoleInfo.getRoleInfoForPlayer(p, false); } catch { }
                    if (roles != null && roles.Any(r => r != null && r.isNeutral)) continue;
                    crew.Add(p);
                }
                if (crew.Count == 1) {
                    Count(FinalGirlId, crew[0].PlayerId);
                    Log($"last crewmate standing: {crew[0].Data?.PlayerName}");
                }
            } catch (Exception e) { Warn($"round end: {e.Message}"); }
        }

        // ---- patches ----
        private static bool booted;
        private static void Boot() {
            if (booted) return;
            booted = true;
            try {
                CreateOptions();
                UCFx.RegisterTick(Tick);
                Log("set up (option 2120).");
            } catch (Exception e) { Warn($"setup failed: {e.Message}"); }
        }

        // In the OnGameEnd PREFIX: the players' state is still that of the round (TOR's postfix clears its statics).
        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameEnd))]
        static class GameEndPatch {
            static bool Prepare() { Boot(); return true; }
            [HarmonyPriority(Priority.First)]
            public static void Prefix() { if (!HwMechanics.FreePlay()) RoundEnded(); }
        }

        [HarmonyPatch(typeof(MainMenuManager), nameof(MainMenuManager.Start))]
        static class MenuPatch { public static void Postfix() { nextTry = 0f; TryRegister(); } }

        [HarmonyPatch(typeof(LobbyBehaviour), nameof(LobbyBehaviour.Start))]
        static class LobbyPatch { public static void Postfix() { nextTry = 0f; TryRegister(); } }

        // ---- self test: UC_HALLOWEEN_DIAG=titles (or a comma list containing it) ----
        private static readonly string DiagMode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        internal static readonly bool Diag = DiagMode.Split(',').Any(x => x.Trim() == "titles");
        private static float diagAt = -1f;
        private static bool diagDone;

        private static void DiagTick() {
            if (!Diag || diagDone) return;
            if (!HwMechanics.InRound() || !HwMechanics.FreePlay()) { diagAt = -1f; return; }
            if (diagAt < 0f) { diagAt = Time.realtimeSinceStartup + 3f; return; }
            if (Time.realtimeSinceStartup < diagAt) return;
            diagDone = true;
            try {
                var ps = PlayerControl.AllPlayerControls.ToArray().Where(p => p != null).ToList();
                Log($"diag: registered {registered}, contract {(count != null ? "found" : "missing")}, {ps.Count} figure(s)");
                if (ps.Count == 0) return;
                int before = Counted;
                // through the real hooks: candies (one of them the Midnight Bonbon), first death, last crewmate
                for (int i = 0; i < 5; i++) OnCandyEaten(ps[i % ps.Count].PlayerId, false);
                OnCandyEaten(ps[0].PlayerId, true);
                OnCandyEaten(ps[0].PlayerId, true);
                Count(HauntedId, ps[Mathf.Min(1, ps.Count - 1)].PlayerId, 3);
                Count(FinalGirlId, ps[ps.Count - 1].PlayerId, 2);
                Count(MirrorId, ps[Mathf.Min(2, ps.Count - 1)].PlayerId, 4);
                RoundEnded();
                Log($"diag: {Counted - before} count(s) handed to UTS (candy 7, midnight 2, haunted 1, final girl 1 + RoundEnded, mirror 1)");
            } catch (Exception e) { Warn($"diag failed: {e}"); }
            Log("diag: titles done");
        }
    }
}
