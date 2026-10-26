// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * SOLE SURVIVOR (evening event, Halloween idea B2, default off)
 *
 * Would the Impostors win by parity (kill or vote), is no killing neutral alive any more, and has the last
 * crewmate (or have the last two, option) done all of their own tasks, the round does not end: the finale starts.
 * The light goes out, only the survivors carry a flashlight, the Impostors stand frozen for 5 s (option), and at a
 * far point of the map an exit opens that only the survivors get an arrow to (everybody can see the exit itself).
 * A survivor who reaches it wins the round for the crew; otherwise, when the time runs out (option) or the last
 * survivor dies, the Impostors win. Meetings, sabotage, vents and ghost tasks are locked during the finale. At most
 * once per game.
 *
 * DESIGN OF THE TASK CONDITION (User concern: "maybe too strong if the dead do not do their tasks")
 * The survivors' own tasks are always required. Option "Dead Crew Tasks Needed" adds the share of the DEAD
 * crewmates' tasks that must be done as well: Not Counted / 50 % (default) / 75 % / 100 %. Ghosts can keep doing
 * their tasks right up to the finale (vanilla behaviour, nothing is locked before), so a ghost who slacks costs his
 * team the finale, and a team that keeps tasking as ghosts earns it. In the finale itself ghost tasks are locked:
 * the crew task win is server-authoritative, and finishing the bar there would end the showdown without the
 * survivor. Non-killing neutrals (Jester, Lawyer ...) do not stop the finale and are no survivors.
 *
 * HOST-AUTHORITATIVE: a host-side prefix on GameManager.RpcEndGame (the Xenomorph's end-guard pattern) swallows the
 * parity win and arms the finale; it starts once no meeting, exile or Airship spawn choice is open (the WrapUp
 * coroutine has finished), so a parity reached by a vote works too. Guards of other roles that already skipped the
 * end (__runOriginal false) are respected. The exit is a vent position far from the survivors, picked by the host.
 * The survivor's own client reports reaching it; the host checks the distance and ends the round as HumansByTask
 * (TOR computes the crew's winners) with an own banner line, or as ImpostorByKill.
 *
 * DARKNESS: own overlay (Atlas' flashlight recipe rebuilt, no dependency): black with a cone in the walking
 * direction, only on the survivors' screens. Impostors' sight is halved through CalculateLightRadius. An Atlas
 * blackout or crisis keeps running untouched; its overlay simply stacks.
 *
 * RPC module 240 (shared with Zombie Outbreak), subtypes 10-12. Options 2050-2055. See ID-Registry.md.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Hazel;
using UnityEngine;
using TheOtherRoles;
using UnknownsCollection;
using Types = TheOtherRoles.CustomOption.CustomOptionType;
using R = UnknownsHalloween.HalloweenModeRules;

namespace UnknownsHalloween {
    public static class SoleSurvivor {
        internal static readonly Color Pink = new Color(1f, 0.45f, 0.70f);
        private const int Banner = 19;

        private const byte SubStart = 10;     // x, y, freeze, limit (floats), n, ids - host
        private const byte SubReached = 11;   // playerId - the survivor -> host
        private const byte SubEscaped = 12;   // playerId - host

        // ---- options (2050-2055) ----
        public static CustomOption Enabled, Survivors, DeadTasks, EscapeTime, Freeze, SurvivorSpeed;
        private static readonly string[] SurvivorLabels = { "1", "1-2" };
        private static readonly string[] DeadTaskLabels = { "Not Counted", "50%", "75%", "100%" };
        private static readonly float[] DeadTaskShare = { 0f, 0.5f, 0.75f, 1f };
        private static readonly string[] EscapeLabels = { "30s", "45s", "60s", "90s", "120s" };
        private static readonly float[] EscapeSeconds = { 30f, 45f, 60f, 90f, 120f };
        private static readonly string[] FreezeLabels = { "3s", "5s", "8s", "10s" };
        private static readonly float[] FreezeSeconds = { 3f, 5f, 8f, 10f };
        private static readonly string[] SpeedLabels = { "100%", "110%", "120%", "130%" };

        private static CustomOption Make(int id, string name, string[] labels, string def, CustomOption parent) =>
            new CustomOption(id, Types.General, name, labels, def, parent, false, null, "");

        internal static void CreateOptions() {
            try {
                Enabled = CustomOption.Create(2050, Types.General, "Sole Survivor", false, null, true, null, "Sole Survivor");
                Survivors = Make(2051, "Sole Survivor: Last Survivors", SurvivorLabels, "1-2", Enabled);
                DeadTasks = Make(2052, "Sole Survivor: Dead Crew Tasks Needed", DeadTaskLabels, "50%", Enabled);
                EscapeTime = Make(2053, "Sole Survivor: Escape Time", EscapeLabels, "60s", Enabled);
                Freeze = Make(2054, "Sole Survivor: Killer Freeze", FreezeLabels, "5s", Enabled);
                SurvivorSpeed = Make(2055, "Sole Survivor: Survivor Speed", SpeedLabels, "110%", Enabled);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{R.LogPrefix} sole survivor options failed: {e}"); }
        }

        private static int Sel(CustomOption o, int fallback) { try { return o == null ? fallback : o.getSelection(); } catch { return fallback; } }
        private static int MaxSurvivors() => Sel(Survivors, 1) == 0 ? 1 : 2;
        private static float DeadShare() => DeadTaskShare[Mathf.Clamp(Sel(DeadTasks, 1), 0, DeadTaskShare.Length - 1)];
        private static float Limit() => DiagLimit > 0f ? DiagLimit : EscapeSeconds[Mathf.Clamp(Sel(EscapeTime, 2), 0, EscapeSeconds.Length - 1)];
        private static float FreezeFor() => FreezeSeconds[Mathf.Clamp(Sel(Freeze, 1), 0, FreezeSeconds.Length - 1)];
        private static float SpeedFactor() => 1f + 0.1f * Mathf.Clamp(Sel(SurvivorSpeed, 1), 0, SpeedLabels.Length - 1);

        // ---- self test (HalloweenModeDiag) ----
        internal static readonly bool Diag = ZombieOutbreak.DiagMode == "solesurvivor" || ZombieOutbreak.DiagMode.StartsWith("solesurvivor:", StringComparison.Ordinal);
        internal static float DiagLimit = -1f;
        internal static bool DiagIgnoreTasks;

        internal static bool OptionOn { get { if (Diag) return true; try { return Enabled != null && Enabled.getBool(); } catch { return false; } } }

        // ---- state ----
        private static bool used, pending, active, ending;
        private static float pendingClearSince = -1f;
        private static readonly HashSet<byte> survivors = new();
        private static Vector2 exitPos;
        private static float freezeUntil, endAt, nextHostTick, nextReachSend;
        private static byte escapedId = byte.MaxValue;

        /// The finale is running (every client knows it from the start message).
        public static bool Active => active && R.InRound();
        internal static bool Pending => pending;
        internal static bool Used => used;
        internal static Vector2 ExitPos => exitPos;
        private static bool IsSurvivor(PlayerControl p) => p != null && survivors.Contains(p.PlayerId);
        private static bool LocalSurvivor() { var lp = PlayerControl.LocalPlayer; return Active && R.IsAlive(lp) && IsSurvivor(lp); }

        private static string Tr(string key) {
            bool de = R.German();
            switch (key) {
                case "start_s": return de ? "SOLE SURVIVOR: Das Licht ist aus. Folge dem Pfeil zum Ausgang und entkomme!" : "SOLE SURVIVOR: the lights are out. Follow the arrow to the exit and get out!";
                case "start_i": return de ? "SOLE SURVIVOR: Die Letzten fliehen zum Ausgang. Gleich kannst du dich bewegen. Lass niemanden entkommen!" : "SOLE SURVIVOR: the last ones run for the exit. You can move in a moment. Let nobody escape!";
                case "start_g": return de ? "SOLE SURVIVOR: das Finale läuft. Geister-Aufgaben sind gesperrt." : "SOLE SURVIVOR: the finale is on. Ghost tasks are locked.";
                case "line_s": return de ? "SOLE SURVIVOR  {0}   Finde den Ausgang!" : "SOLE SURVIVOR  {0}   Find the exit!";
                case "line_i": return de ? "SOLE SURVIVOR  {0}   Lass sie nicht entkommen!" : "SOLE SURVIVOR  {0}   Do not let them escape!";
                case "line_f": return de ? "SOLE SURVIVOR  {0}   Eingefroren: {1}" : "SOLE SURVIVOR  {0}   Frozen: {1}";
                case "line_g": return "SOLE SURVIVOR  {0}";
                case "escaped": return de ? "{0} ist entkommen!" : "{0} escaped!";
                case "win_c": return de ? "Sole Survivor entkommen" : "The Sole Survivor Escaped";
                case "win_i": return de ? "Niemand ist entkommen" : "Nobody Escaped";
                default: return key;
            }
        }

        // ==================================================================== the trigger (host)

        private static readonly HashSet<string> KillerNeutrals = new() { "Jackal", "Sidekick", "Thief", "Arsonist", "Pelican", "Stalker", "Xenomorph", "Necromancer" };

        /// Every condition of the finale; survivors are the living crewmates when they hold.
        internal static bool Conditions(out List<PlayerControl> found, out string why) {
            found = new List<PlayerControl>();
            var all = PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null).ToList();
            var alive = all.Where(R.IsAlive).ToList();
            if (!alive.Any(R.IsImpostor)) { why = "no impostor alive"; return false; }
            int deadDone = 0, deadTotal = 0;
            foreach (var p in all) {
                bool imp = R.IsImpostor(p);
                List<RoleInfo> roles = null;
                try { roles = RoleInfo.getRoleInfoForPlayer(p, false); } catch { }
                bool neutral = roles != null && roles.Any(ri => ri != null && ri.isNeutral);
                bool killer = roles != null && roles.Any(ri => ri != null && KillerNeutrals.Contains(ri.name));
                if (R.IsAlive(p)) {
                    if (imp) continue;
                    if (killer) { why = $"killing neutral alive ({p.Data.PlayerName})"; return false; }
                    if (neutral) continue;                  // Jester, Lawyer ...: no survivor, no obstacle
                    found.Add(p);
                } else if (!imp && !neutral) {
                    try { var (d, t) = TasksHandler.taskInfo(p.Data); deadDone += d; deadTotal += t; } catch { }
                }
            }
            if (found.Count == 0) { why = "no crewmate alive"; return false; }
            if (found.Count > MaxSurvivors() && DiagIgnoreTasks && PlayerControl.LocalPlayer != null && found.Any(f => f.PlayerId == PlayerControl.LocalPlayer.PlayerId)) {
                // self test: freeplay dummies do not stay dead, the local player stands in for "the last crewmate"
                R.Log($"diag: {found.Count} crewmates alive - the self test keeps only the local player");
                found = new List<PlayerControl> { PlayerControl.LocalPlayer };
            }
            if (found.Count > MaxSurvivors()) { why = $"{found.Count} crewmates alive (max {MaxSurvivors()})"; return false; }
            foreach (var p in found) {
                var (d, t) = TasksHandler.taskInfo(p.Data);
                if (d < t) {
                    if (DiagIgnoreTasks) { R.Log($"diag: {p.Data.PlayerName} has {d}/{t} own tasks - ignored for the self test"); continue; }
                    why = $"{p.Data.PlayerName} has {d}/{t} own tasks"; return false;
                }
            }
            float need = DeadShare();
            if (need > 0f && deadTotal > 0 && deadDone < Mathf.CeilToInt(deadTotal * need - 0.001f)) {
                if (DiagIgnoreTasks) R.Log($"diag: dead crew tasks {deadDone}/{deadTotal} (need {need:P0}) - ignored for the self test");
                else {
                why = $"dead crew tasks {deadDone}/{deadTotal} (need {need:P0})"; return false;
                }
            }
            why = $"ok: {found.Count} survivor(s), dead crew tasks {deadDone}/{deadTotal}";
            return true;
        }

        private static string lastWhy;

        [HarmonyPatch(typeof(GameManager), nameof(GameManager.RpcEndGame))]
        static class EndGuardPatch {
            [HarmonyPriority(Priority.Low)]   // after the role guards (Xenomorph, Pelican, Hunt ...: Priority.First)
            public static bool Prefix(ref GameOverReason endReason, bool __runOriginal) {
                try {
                    if (!R.AmHost || !__runOriginal || R.AllowEnd || ending) return true;
                    if (ZombieOutbreak.Active) return true;
                    if (pending || active) {
                        // the finale decides; a sabotage, a disconnect or a full task bar still end the round
                        return endReason == GameOverReason.ImpostorBySabotage || endReason == GameOverReason.HumansByTask
                            || endReason == GameOverReason.ImpostorDisconnect || endReason == GameOverReason.HumansDisconnect;
                    }
                    if (!OptionOn || used || !R.InRound()) return true;
                    if (endReason != GameOverReason.ImpostorByKill && endReason != GameOverReason.ImpostorByVote) return true;
                    if (!Conditions(out var found, out string why)) {
                        if (why != lastWhy) { lastWhy = why; R.Log($"Sole Survivor: no finale ({why})."); }
                        return true;
                    }
                    used = true;
                    pending = true;
                    pendingClearSince = -1f;
                    survivors.Clear();
                    foreach (var p in found) survivors.Add(p.PlayerId);
                    R.Log($"Sole Survivor: parity win ({(int)endReason}) held back - {why}.");
                    return false;
                } catch (Exception e) {
                    HalloweenPlugin.Logger?.LogError($"{R.LogPrefix} sole survivor guard failed: {e}");
                    return true;
                }
            }
        }

        // ==================================================================== host

        private static bool SceneClear() {
            if (R.InMeeting()) return false;
            try { if (Minigame.Instance != null && Minigame.Instance.TryCast<SpawnInMinigame>() != null) return false; } catch { }
            return true;
        }

        private static Vector2 PickExit(List<PlayerControl> from) {
            var spots = new List<Vector2>();
            try { foreach (var v in ShipStatus.Instance.AllVents) if (v != null) spots.Add(v.transform.position); } catch { }
            if (spots.Count == 0) {
                try { spots.Add(ShipStatus.Instance.MeetingSpawnCenter); spots.Add(ShipStatus.Instance.InitialSpawnCenter); } catch { }
            }
            if (spots.Count == 0) return from.Count > 0 ? from[0].GetTruePosition() : Vector2.zero;
            float Score(Vector2 s) => from.Count == 0 ? 0f : from.Min(p => Vector2.Distance(p.GetTruePosition(), s));
            var ranked = spots.OrderByDescending(Score).ToList();
            // far, but not always the single farthest corner: one of the top quarter
            int top = Mathf.Max(1, ranked.Count / 4);
            return ranked[new System.Random().Next(top)];
        }

        private static void HostTick() {
            if (pending) {
                var alive = survivors.Select(Helpers.playerById).Where(R.IsAlive).ToList();
                if (alive.Count == 0) { pending = false; End(GameOverReason.ImpostorByKill); return; }
                if (!SceneClear()) { pendingClearSince = -1f; return; }
                if (pendingClearSince < 0f) { pendingClearSince = Time.time; return; }
                if (Time.time - pendingClearSince < 1.5f) return;
                pending = false;
                // a meeting in the waiting time can change everything (the last impostor voted out): ask again, and
                // without a finale TOR's end check runs normally on the next frame (audit N-9)
                if (!Conditions(out _, out string why)) { R.Log($"Sole Survivor: finale dropped after the wait ({why})."); used = true; return; }
                SendStart(PickExit(alive), FreezeFor(), Limit(), alive.Select(p => p.PlayerId).ToList());
                return;
            }
            if (!active) return;
            bool anyAlive = survivors.Any(id => R.IsAlive(Helpers.playerById(id)));
            if (!anyAlive) { End(GameOverReason.ImpostorByKill); return; }
            if (!PlayerControl.AllPlayerControls.ToArray().Any(p => R.IsAlive(p) && R.IsImpostor(p))) { End(GameOverReason.HumansByTask); return; }
            if (Time.time >= endAt) End(GameOverReason.ImpostorByKill);
        }

        private static void End(GameOverReason reason) {
            if (ending) return;
            ending = true;
            R.EndRound(reason);
        }

        private static void HostReached(byte id) {
            if (!active || ending) return;
            var p = Helpers.playerById(id);
            if (!R.IsAlive(p) || !IsSurvivor(p)) return;
            float d = Vector2.Distance(p.GetTruePosition(), exitPos);
            if (d > 2.0f) { R.Warn($"Sole Survivor: {p.Data.PlayerName} reported the exit from {d:F1} away - ignored."); return; }
            try {
                var w = R.Begin(SubEscaped); w.Write(id);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch { }
            ApplyEscaped(id);
            End(GameOverReason.HumansByTask);
        }

        // ==================================================================== RPC

        internal static void HandleRpc(byte sub, MessageReader r) {
            switch (sub) {
                case SubStart: {
                    float x = r.ReadSingle(), y = r.ReadSingle(), fr = r.ReadSingle(), lim = r.ReadSingle();
                    int n = r.ReadByte();
                    var ids = new List<byte>();
                    for (int i = 0; i < n; i++) ids.Add(r.ReadByte());
                    if (UCRpc.RequireHost("SoleSurvivor.Start")) ApplyStart(new Vector2(x, y), fr, lim, ids);
                    break;
                }
                case SubReached: {
                    byte id = r.ReadByte();
                    if (R.AmHost && UCRpc.Sender != null && UCRpc.Sender.PlayerId == id) HostReached(id);
                    break;
                }
                case SubEscaped: { byte id = r.ReadByte(); if (UCRpc.RequireHost("SoleSurvivor.Escaped")) ApplyEscaped(id); break; }
            }
        }

        private static void SendStart(Vector2 pos, float freeze, float limit, List<byte> ids) {
            try {
                var w = R.Begin(SubStart);
                w.Write(pos.x); w.Write(pos.y); w.Write(freeze); w.Write(limit);
                w.Write((byte)ids.Count);
                foreach (var id in ids) w.Write(id);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch (Exception e) { R.Warn($"finale start send failed: {e.Message}"); }
            ApplyStart(pos, freeze, limit, ids);
        }

        private static void SendReached(byte id) {
            if (R.AmHost) { HostReached(id); return; }
            try {
                var w = R.Begin(SubReached); w.Write(id);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch { }
        }

        // ==================================================================== applied on every client

        private static void ApplyStart(Vector2 pos, float freeze, float limit, List<byte> ids) {
            used = true;
            pending = false;
            active = true;
            exitPos = pos;
            survivors.Clear();
            foreach (var id in ids) survivors.Add(id);
            freezeUntil = Time.time + Mathf.Clamp(freeze, 0f, 20f);
            endAt = Time.time + Mathf.Clamp(limit, 5f, 300f);
            R.Log($"finale started: exit {pos.x:F1}/{pos.y:F1}, survivors {string.Join(",", ids)}, freeze {freeze:F0}s, limit {limit:F0}s");
            BuildPortal();
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || lp.Data == null) return;
            if (!HalloweenPlugin.Calm) { try { Helpers.showFlash(Pink, 1.2f); } catch { } }
            if (IsSurvivor(lp)) R.Chat(Tr("start_s"));
            else if (R.IsImpostor(lp) && !lp.Data.IsDead) {
                R.Chat(Tr("start_i"));
                try { if (lp.killTimer < freeze + 1f) lp.SetKillTimer(freeze + 1f); } catch { }
                try { if (lp.inVent && Vent.currentVent != null) lp.MyPhysics.RpcExitVent(Vent.currentVent.Id); } catch { }
            } else {
                R.Chat(Tr("start_g"));
                try { if (lp.Data.IsDead && Minigame.Instance != null) Minigame.Instance.Close(); } catch { }
            }
        }

        private static void ApplyEscaped(byte id) {
            escapedId = id;
            var p = Helpers.playerById(id);
            R.Log($"finale: {p?.Data?.PlayerName ?? id.ToString()} reached the exit");
            R.Chat(string.Format(Tr("escaped"), p?.Data?.PlayerName ?? "?"));
        }

        // ==================================================================== portal, arrow, darkness

        private static GameObject portalGo;
        private static SpriteRenderer portalSr;
        private static TheOtherRoles.Objects.Arrow arrow;
        private static SpriteRenderer dark;
        private static Vector2 look = Vector2.right;

        private static void BuildPortal() {
            try {
                if (portalGo != null) UnityEngine.Object.Destroy(portalGo);
                // layer 11: the ship camera does not render procedural world objects on the default layer
                portalGo = new GameObject("SoleSurvivorExit") { layer = 11 };
                portalGo.transform.position = new Vector3(exitPos.x, exitPos.y, exitPos.y / 1000f - 0.05f);
                portalSr = portalGo.AddComponent<SpriteRenderer>();
                portalSr.sprite = HalloweenModeArt.ExitPortal()[0];
                // a soft glow so the exit reads in the dark
                var glow = new GameObject("Glow") { layer = 11 };
                glow.transform.SetParent(portalGo.transform, false);
                glow.transform.localPosition = new Vector3(0f, 0f, 0.01f);
                glow.transform.localScale = new Vector3(2.2f, 2.2f, 1f);
                var g = glow.AddComponent<SpriteRenderer>();
                g.sprite = UCFx.Dot;
                g.color = new Color(Pink.r, Pink.g, Pink.b, 0.35f);
            } catch (Exception e) { R.Warn($"portal failed: {e.Message}"); }
        }

        private static void TickVisuals() {
            var lp = PlayerControl.LocalPlayer;
            if (portalSr != null) {
                var frames = HalloweenModeArt.ExitPortal();
                portalSr.sprite = frames[Mathf.FloorToInt(Time.time * 10f) % frames.Length];
                float s = 1f + 0.05f * Mathf.Sin(Time.time * 3f);
                portalGo.transform.localScale = new Vector3(s, s, 1f);
            }
            bool surv = LocalSurvivor() && !R.InMeeting();
            // arrow: survivors only
            if (surv) {
                if (arrow == null || arrow.arrow == null) {
                    arrow = new TheOtherRoles.Objects.Arrow(Color.white);
                    try { arrow.image.sprite = HalloweenModeArt.Arrow(); } catch { }
                }
                arrow.arrow.SetActive(true);
                arrow.Update(exitPos);
            } else if (arrow != null && arrow.arrow != null) arrow.arrow.SetActive(false);
            // darkness with the flashlight cone: survivors only (in the world just in front of the players, behind the HUD)
            if (surv) {
                if (dark == null) {
                    var go = new GameObject("SoleSurvivorDark") { layer = lp.gameObject.layer };
                    dark = go.AddComponent<SpriteRenderer>();
                    dark.sprite = HalloweenModeArt.FlashlightCone();
                }
                dark.gameObject.SetActive(true);
                try {
                    var v = lp.MyPhysics != null && lp.MyPhysics.body != null ? lp.MyPhysics.body.velocity : Vector2.zero;
                    if (v.sqrMagnitude > 0.02f) look = Vector2.Lerp(look, v.normalized, 0.2f).normalized;
                } catch { }
                var p = lp.transform.position;
                dark.transform.position = new Vector3(p.x, p.y, -1f);
                dark.transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(look.y, look.x) * Mathf.Rad2Deg);
            } else if (dark != null) dark.gameObject.SetActive(false);
        }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class HudUpdatePatch {
            [HarmonyPriority(Priority.Last)]
            public static void Postfix() {
                try {
                    if (!R.InRound()) { if (active || pending || used || portalGo != null) Reset(); return; }
                    if (Active) {
                        TickVisuals();
                        var lp = PlayerControl.LocalPlayer;
                        string clock = R.Clock(endAt - Time.time);
                        string line;
                        if (LocalSurvivor()) line = string.Format(Tr("line_s"), clock);
                        else if (R.IsAlive(lp) && R.IsImpostor(lp)) line = Time.time < freezeUntil ? string.Format(Tr("line_f"), clock, R.Clock(freezeUntil - Time.time)) : string.Format(Tr("line_i"), clock);
                        else line = string.Format(Tr("line_g"), clock);
                        R.HudLine(line);
                        if (HudManager.Instance != null && HudManager.Instance.SabotageButton != null && HudManager.Instance.SabotageButton.gameObject.activeSelf)
                            HudManager.Instance.SabotageButton.ToggleVisible(false);
                        // the survivor reports the exit himself (the host checks the distance)
                        if (LocalSurvivor() && !lp.inVent && Vector2.Distance(lp.GetTruePosition(), exitPos) <= 1.0f && Time.time >= nextReachSend) {
                            nextReachSend = Time.time + 1f;
                            SendReached(lp.PlayerId);
                        }
                    }
                    if (Time.realtimeSinceStartup < nextHostTick) return;
                    nextHostTick = Time.realtimeSinceStartup + 0.25f;
                    if (R.AmHost && (pending || active)) HostTick();
                } catch (Exception e) {
                    if (!tickLogged) { tickLogged = true; HalloweenPlugin.Logger?.LogError($"{R.LogPrefix} sole survivor tick failed (logged once): {e}"); }
                }
            }
        }
        private static bool tickLogged;

        // Impostors frozen at the start, survivors a little faster (the owner's client moves the player).
        [HarmonyPatch(typeof(PlayerPhysics), nameof(PlayerPhysics.FixedUpdate))]
        static class MovePatch {
            public static void Postfix(PlayerPhysics __instance) {
                try {
                    if (!Active || __instance == null || !__instance.AmOwner || __instance.body == null || __instance.myPlayer == null) return;
                    var p = __instance.myPlayer;
                    if (!R.IsAlive(p)) return;
                    if (R.IsImpostor(p) && Time.time < freezeUntil) __instance.body.velocity = Vector2.zero;
                    else if (IsSurvivor(p)) __instance.body.velocity *= SpeedFactor();
                } catch { }
            }
        }

        // The light goes out: impostors see half as far, the survivors' sight is the flashlight (overlay above), so
        // their radius is opened up to the cone's reach. Priority 50: after UCVision/Xenomorph (Low), before ChanceMod's
        // multiplier (Last).
        [HarmonyPatch(typeof(ShipStatus), nameof(ShipStatus.CalculateLightRadius))]
        static class VisionPatch {
            [HarmonyPriority(50)]
            public static void Postfix(ref float __result, [HarmonyArgument(0)] NetworkedPlayerInfo p) {
                try {
                    if (!Active || p == null || p.IsDead || p.Object == null) return;
                    if (p.Role != null && p.Role.IsImpostor) __result *= 0.5f;
                    else if (IsSurvivor(p.Object)) __result = Mathf.Max(__result, 4.8f);
                } catch { }
            }
        }

        // ==================================================================== end screen

        private static bool snapActive;
        private static int snapEscaped = byte.MaxValue;
        private static int snapReason = -1;

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameEnd))]
        static class OnGameEndPatch {
            [HarmonyPriority(Priority.Last)]
            public static void Prefix() { snapActive = active; snapEscaped = escapedId; snapReason = -1; }

            [HarmonyPriority(Priority.Last)]
            public static void Postfix() {
                try {
                    if (!snapActive) return;
                    snapReason = (int)TheOtherRoles.Patches.OnGameEndPatch.gameOverReason;
                    // TOR's own line only for its Default banner; Lovers, Jackal ... keep theirs
                    if (R.GetWinCondition() == 0) R.SetWinCondition(Banner);
                    else snapReason = -2;
                } catch { }
            }
        }

        [HarmonyPatch(typeof(EndGameManager), nameof(EndGameManager.SetEverythingUp))]
        static class EndScreenPatch {
            [HarmonyPriority(Priority.Last)]
            public static void Postfix(EndGameManager __instance) {
                if (!snapActive || snapReason == -2) return;
                if (snapReason == (int)GameOverReason.HumansByTask) {
                    string who = null;
                    try { if (snapEscaped != byte.MaxValue) who = GameData.Instance?.GetPlayerById((byte)snapEscaped)?.PlayerName; } catch { }
                    R.BonusText(__instance, who != null ? string.Format(Tr("escaped"), who) : Tr("win_c"), Pink, true);
                } else if (snapReason >= 0) {
                    R.BonusText(__instance, Tr("win_i"), new Color(1f, 0.2f, 0.2f), true);
                }
            }
        }

        // ==================================================================== self test hooks

        internal static string DiagState() =>
            $"used {used}, pending {pending}, active {Active}, survivors {string.Join(",", survivors)}, exit {exitPos.x:F1}/{exitPos.y:F1}, left {(active ? endAt - Time.time : -1f):F0}s, frozen {(active && Time.time < freezeUntil)}";
        internal static float DiagLight(PlayerControl p) { try { return ShipStatus.Instance.CalculateLightRadius(p.Data); } catch { return -1f; } }

        // ==================================================================== reset

        private static void Reset() {
            used = pending = active = ending = false;
            pendingClearSince = -1f;
            survivors.Clear();
            escapedId = byte.MaxValue;
            lastWhy = null;
            try { if (portalGo != null) UnityEngine.Object.Destroy(portalGo); } catch { }
            portalGo = null; portalSr = null;
            try { if (arrow != null && arrow.arrow != null) UnityEngine.Object.Destroy(arrow.arrow); } catch { }
            arrow = null;
            try { if (dark != null) UnityEngine.Object.Destroy(dark.gameObject); } catch { }
            dark = null;
            if (!ZombieOutbreak.Active) R.ClearHud();
        }

        [HarmonyPatch(typeof(RPCProcedure), nameof(RPCProcedure.resetVariables))]
        static class ResetPatch {
            public static void Postfix() => Reset();
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class LobbyResetPatch {
            public static void Postfix() { Reset(); snapActive = false; }
        }
    }
}
