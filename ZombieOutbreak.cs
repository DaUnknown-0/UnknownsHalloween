// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * ZOMBIE OUTBREAK (game mode, Halloween idea B1, default off)
 *
 * One start zombie per six players (option). Whoever a zombie catches does not die: three seconds later (option)
 * he is a zombie himself, wears the corpse costume (HalloweenCorpse) in his own colour, walks a little slower and
 * gets the infect button. No meetings, no roles. The survivors win when the clock runs out (about 4 min, option)
 * or when all still open tasks are done; the zombies win when nobody is left.
 *
 * WHO THE START ZOMBIES ARE: the vanilla Impostors. In this mode the host's impostor count is replaced by
 * floor(players / players-per-zombie), at least 1 (TOR's own limit of 3 stays), through a postfix on
 * GetAdjustedNumImpostors, a game method TOR already patches (no new detour). So every client knows the start
 * zombies without a message, the impostors have no real tasks, and no crewmate has to be converted at the start.
 * Their vanilla kill button is hidden and disarmed (KillButton.DoClick: target cleared before TOR's prefix, the
 * Illusionist pattern); everybody infects with the same custom button (Jackal pattern), host-authoritative.
 *
 * NO ROLES: TOR's role assignment (assignRoles, modifiers included), the drafts (TOR RoleDraft.isEnabled, UC's
 * DraftWillRun) and UC's intro picks are skipped, the code of Unknown's Hunt copied (no dependency); the intro
 * picks of this mod (Xenomorph, Banshee) are skipped through prefixes on their pick postfixes.
 *
 * TASKS: the task win is server-authoritative, so an infected player's tasks leave the game server-visibly
 * (RpcSetTasks with an empty list, the Xenomorph's way; not in freeplay, where an empty list opens the practice
 * popup). With every infection the bar therefore shrinks to what the survivors still have to do, and a full bar
 * ends the round as HumansByTask - the survivors' win. The LAST survivor's tasks are never stripped: the zombies
 * win first (an empty bar would read as "all tasks done").
 *
 * ENDING: a host-side RpcEndGame prefix lets only the mode's own ends (win reasons 36 zombies, 37 survivors) and
 * the task win through while the mode runs; parity and "no killer left" mean nothing here. The winners are
 * rebuilt in the OnGameEnd postfix from the zombie set snapshotted in its prefix; own banner lines (TOR banner
 * slots 17/18).
 *
 * RPC module 240 (shared with Sole Survivor), subtypes 0-4. Options 2040-2046. See ID-Registry.md.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using AmongUs.GameOptions;
using HarmonyLib;
using Hazel;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using UnityEngine;
using TheOtherRoles;
using TheOtherRoles.Patches;
using UnknownsCollection;
using Types = TheOtherRoles.CustomOption.CustomOptionType;
using R = UnknownsHalloween.HalloweenModeRules;

namespace UnknownsHalloween {
    public static class ZombieOutbreak {
        internal static readonly Color Green = new Color(0.47f, 0.86f, 0.27f);

        internal const int ZombieWinReason = 36;
        internal const int SurvivorWinReason = 37;
        private const int ZombieBanner = 17, SurvivorBanner = 18;

        private const byte SubStart = 0;      // seconds (float), host
        private const byte SubInfectReq = 1;  // zombie, target - the zombie's client -> host
        private const byte SubBitten = 2;     // target, zombie, delay (float) - host
        private const byte SubTurned = 3;     // playerId - host
        private const byte SubTimer = 4;      // remaining seconds (float) - host (self test only)

        // ---- options (2040-2046) ----
        public static CustomOption Enabled, PlayersPerZombie, RoundTime, InfectCooldown, ZombieSpeed, TurnDelay, ZombieVents;
        private static readonly string[] TimeLabels = { "2 min", "3 min", "4 min", "5 min", "6 min", "8 min" };
        private static readonly float[] TimeSeconds = { 120f, 180f, 240f, 300f, 360f, 480f };
        private static readonly string[] CooldownLabels = { "5s", "10s", "15s", "20s", "25s", "30s" };
        private static readonly string[] SpeedLabels = { "70%", "75%", "80%", "85%", "90%", "95%", "100%" };
        private static readonly string[] DelayLabels = { "1s", "2s", "3s", "4s", "5s" };

        private static CustomOption Make(int id, string name, string[] labels, string def, CustomOption parent, bool header = false, string heading = "") =>
            new CustomOption(id, Types.General, name, labels, def, parent, header, null, heading);

        internal static void CreateOptions() {
            try {
                Enabled = CustomOption.Create(2040, Types.General, "Zombie Outbreak", false, null, true, null, "Zombie Outbreak");
                PlayersPerZombie = CustomOption.Create(2041, Types.General, "Players Per Start Zombie", 6f, 4f, 10f, 1f, Enabled);
                RoundTime = Make(2042, "Zombie Outbreak Round Time", TimeLabels, "4 min", Enabled);
                InfectCooldown = Make(2043, "Infect Cooldown", CooldownLabels, "15s", Enabled);
                ZombieSpeed = Make(2044, "Zombie Speed", SpeedLabels, "85%", Enabled);
                TurnDelay = Make(2045, "Time Until A Bitten Player Turns", DelayLabels, "3s", Enabled);
                ZombieVents = CustomOption.Create(2046, Types.General, "Zombies Can Use Vents", false, Enabled);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{R.LogPrefix} zombie options failed: {e}"); }
        }

        private static int Sel(CustomOption o, int fallback) { try { return o == null ? fallback : o.getSelection(); } catch { return fallback; } }
        private static float RoundSeconds() => TimeSeconds[Mathf.Clamp(Sel(RoundTime, 2), 0, TimeSeconds.Length - 1)];
        internal static float Cooldown() => 5f + 5f * Mathf.Clamp(Sel(InfectCooldown, 2), 0, CooldownLabels.Length - 1);
        private static float SpeedFactor() => 0.70f + 0.05f * Mathf.Clamp(Sel(ZombieSpeed, 3), 0, SpeedLabels.Length - 1);
        private static float Delay() => 1f + Mathf.Clamp(Sel(TurnDelay, 2), 0, DelayLabels.Length - 1);
        private static float PerZombie() { try { return PlayersPerZombie?.getFloat() ?? 6f; } catch { return 6f; } }

        // ---- self test switch (HalloweenModeDiag) ----
        internal static readonly string DiagMode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        internal static readonly bool Diag = DiagMode == "zombie" || DiagMode.StartsWith("zombie:", StringComparison.Ordinal);

        /// The host switched the mode on (TOR syncs the option to every client).
        public static bool OptionOn { get { if (Diag) return true; try { return Enabled != null && Enabled.getBool(); } catch { return false; } } }
        /// The mode is running: option on and a round in progress.
        public static bool Active => OptionOn && R.InRound();

        // ---- state ----
        private static readonly HashSet<byte> turned = new();            // infected crewmates (start zombies are the impostors)
        private static readonly Dictionary<byte, float> bitten = new();  // playerId -> local time of the turn
        private static readonly Dictionary<byte, float> lastInfect = new();   // host: zombie -> last accepted bite
        private static readonly HashSet<byte> looked = new();            // players that got the corpse look
        private static readonly Dictionary<byte, float> nextLookTry = new();
        private static bool started, introDone, endSent, gameEnding;
        private static float endAt, nextHostTick, startSeenAt = -1f;
        private static string corpseHat;
        private static bool corpseLogged;

        public static bool IsZombie(PlayerControl p) =>
            p != null && p.Data != null && (turned.Contains(p.PlayerId) || R.IsImpostor(p));
        public static bool IsBitten(byte id) => bitten.ContainsKey(id);
        private static bool IsHuman(PlayerControl p) => R.IsAlive(p) && !IsZombie(p);
        private static IEnumerable<PlayerControl> Players() => PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null);
        internal static int Humans() => Players().Count(IsHuman);
        internal static int Zombies() => Players().Count(p => R.IsAlive(p) && IsZombie(p));
        internal static float Remaining() => started ? Mathf.Max(0f, endAt - Time.time) : -1f;
        internal static bool Started => started;
        private static bool LocalZombie() { var lp = PlayerControl.LocalPlayer; return Active && R.IsAlive(lp) && IsZombie(lp); }

        internal static bool MayVent(PlayerControl p) => IsZombie(p) && (ZombieVents?.getBool() ?? false);

        private static string Tr(string key) {
            bool de = R.German();
            switch (key) {
                case "infect": return de ? "INFIZIEREN" : "INFECT";
                case "intro_z": return de ? "ZOMBIE OUTBREAK: Du bist ein Zombie. Infiziere alle, bevor die Zeit abläuft. Keine Meetings."
                                          : "ZOMBIE OUTBREAK: you are a zombie. Infect everybody before the time runs out. No meetings.";
                case "intro_h": return de ? "ZOMBIE OUTBREAK: Überlebe bis zum Ende der Zeit oder schafft alle Aufgaben. Wer gebissen wird, wird selbst zum Zombie. Keine Meetings."
                                          : "ZOMBIE OUTBREAK: survive until the time is up or finish all tasks. Whoever is bitten turns into a zombie. No meetings.";
                case "bitten": return de ? "Du wurdest gebissen ..." : "You have been bitten ...";
                case "turned": return de ? "Du bist jetzt ein Zombie. Infiziere die Überlebenden!" : "You are a zombie now. Infect the survivors!";
                case "line": return de ? "ZOMBIE OUTBREAK  {0}   Überlebende {1}  ·  Zombies {2}" : "ZOMBIE OUTBREAK  {0}   Survivors {1}  ·  Zombies {2}";
                case "win_z": return de ? "Die Zombies haben alle erwischt" : "The Zombies Got Everybody";
                case "win_s": return de ? "Die Überlebenden haben durchgehalten" : "The Survivors Held Out";
                default: return key;
            }
        }

        // ==================================================================== registration

        private static bool booted;
        private static void Boot() {
            if (booted) return;
            booted = true;
            try {
                CreateOptions();
                SoleSurvivor.CreateOptions();
                R.Register();
                PatchForeign(new Harmony("daunknown.unknownshalloween.zombie"));
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{R.LogPrefix} registration failed: {e}"); }
        }

        // No roles in this mode (Unknown's Hunt's PatchForeign, extended by the drafts and this mod's own picks).
        private static void PatchForeign(Harmony h) {
            void Pre(Type t, string method, string prefix, bool getter = false) {
                try {
                    var m = t == null ? null : (getter ? AccessTools.PropertyGetter(t, method) : AccessTools.Method(t, method));
                    if (m != null) h.Patch(m, prefix: new HarmonyMethod(typeof(ZombieOutbreak), prefix));
                    else R.Warn($"{t?.Name ?? "?"}.{method} not found - roles could still be handed out in Zombie Outbreak.");
                } catch (Exception e) { R.Warn($"patch {method}: {e.Message}"); }
            }
            var torAsm = typeof(CustomOption).Assembly;
            Pre(torAsm.GetType("TheOtherRoles.Patches.RoleManagerSelectRolesPatch"), "assignRoles", nameof(SkipWhenOn));
            Pre(torAsm.GetType("TheOtherRoles.Modules.RoleDraft") ?? torAsm.GetTypes().FirstOrDefault(t => t.Name == "RoleDraft"), "isEnabled", nameof(FalseWhenOn), true);
            Pre(typeof(UCPromotion), "RunPicks", nameof(SkipWhenOn));
            Pre(typeof(UCRoleDraft), "DraftWillRun", nameof(FalseWhenOn));
            Pre(AccessTools.Inner(typeof(Xenomorph), "IntroEndPickPatch"), "Postfix", nameof(SkipWhenOnQuiet));
            Pre(AccessTools.Inner(typeof(Banshee), "IntroEndPickPatch"), "Postfix", nameof(SkipWhenOnQuiet));
        }

        private static bool SkipWhenOn() {
            if (!OptionOn) return true;
            R.Log("Zombie Outbreak is on - role assignment skipped.");
            return false;
        }
        private static bool SkipWhenOnQuiet() => !OptionOn;
        private static bool FalseWhenOn(ref bool __result) {
            if (!OptionOn) return true;
            __result = false;
            return false;
        }

        // The impostor count of this mode: one start zombie per N players.
        [HarmonyPatch(typeof(IGameOptionsExtensions), nameof(IGameOptionsExtensions.GetAdjustedNumImpostors))]
        static class ImpostorCountPatch {
            [HarmonyPriority(Priority.Last)]
            public static void Postfix([HarmonyArgument(1)] int playerCount, ref int __result) {
                try {
                    if (!OptionOn || Diag) return;
                    if (GameOptionsManager.Instance.CurrentGameOptions.GameMode != GameModes.Normal) return;
                    __result = Mathf.Clamp(Mathf.FloorToInt(playerCount / Mathf.Max(2f, PerZombie())), 1, 3);
                } catch { }
            }
        }

        // ==================================================================== RPC

        internal static void HandleRpc(byte sub, MessageReader r) {
            switch (sub) {
                case SubStart: { float s = r.ReadSingle(); if (UCRpc.RequireHost("Zombie.Start")) ApplyStart(s); break; }
                case SubInfectReq: {
                    byte z = r.ReadByte(), t = r.ReadByte();
                    if (!R.AmHost) break;
                    if (UCRpc.Sender == null || UCRpc.Sender.PlayerId != z) { R.Warn($"infect request for {z} sent by {UCRpc.Sender?.PlayerId} - ignored"); break; }
                    HostInfect(z, t);
                    break;
                }
                case SubBitten: { byte t = r.ReadByte(), z = r.ReadByte(); float d = r.ReadSingle(); if (UCRpc.RequireHost("Zombie.Bitten")) ApplyBitten(t, z, d); break; }
                case SubTurned: { byte id = r.ReadByte(); if (UCRpc.RequireHost("Zombie.Turned")) ApplyTurned(id); break; }
                case SubTimer: { float s = r.ReadSingle(); if (UCRpc.RequireHost("Zombie.Timer")) endAt = Time.time + s; break; }
            }
        }

        private static void SendStart(float seconds) {
            try {
                var w = R.Begin(SubStart); w.Write(seconds);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch (Exception e) { R.Warn($"start send failed: {e.Message}"); }
            ApplyStart(seconds);
        }

        internal static void RequestInfect(byte zombie, byte target) {
            if (R.AmHost) { HostInfect(zombie, target); return; }
            try {
                var w = R.Begin(SubInfectReq); w.Write(zombie); w.Write(target);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch (Exception e) { R.Warn($"infect request failed: {e.Message}"); }
        }

        private static void SendBitten(byte target, byte zombie, float delay) {
            try {
                var w = R.Begin(SubBitten); w.Write(target); w.Write(zombie); w.Write(delay);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch (Exception e) { R.Warn($"bitten send failed: {e.Message}"); }
            ApplyBitten(target, zombie, delay);
        }

        internal static void SendTurned(byte id) {
            try {
                var w = R.Begin(SubTurned); w.Write(id);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch (Exception e) { R.Warn($"turned send failed: {e.Message}"); }
            ApplyTurned(id);
            if (R.AmHost) HostAfterTurn(id);
        }

        internal static void SendTimer(float seconds) {
            try {
                var w = R.Begin(SubTimer); w.Write(seconds);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch { }
            endAt = Time.time + seconds;
        }

        // ==================================================================== host logic

        /// Host: a zombie asks to bite. Checked against the host's own view (alive, distance, cooldown).
        internal static string HostInfect(byte zombie, byte target) {
            if (!Active || !started || endSent) return "not running";
            var z = Helpers.playerById(zombie);
            var t = Helpers.playerById(target);
            if (!R.IsAlive(z) || !IsZombie(z)) return "biter is no living zombie";
            if (!IsHuman(t) || bitten.ContainsKey(target)) return "target is no free survivor";
            if (R.InMeeting()) return "meeting";
            float range = 1.8f;
            try { range = GameOptionsData.KillDistances[Mathf.Clamp(GameOptionsManager.Instance.currentNormalGameOptions.KillDistance, 0, 2)] + 1.2f; } catch { }
            float d = Vector2.Distance(z.GetTruePosition(), t.GetTruePosition());
            if (d > range) return $"too far ({d:F1} > {range:F1})";
            if (lastInfect.TryGetValue(zombie, out float last) && Time.time - last < Cooldown() * 0.75f) return "cooldown";
            lastInfect[zombie] = Time.time;
            SendBitten(target, zombie, Delay());
            return "bitten";
        }

        private static void HostAfterTurn(byte id) {
            if (endSent) return;
            if (Humans() == 0) {
                // the last survivor: the zombies win before his tasks could empty the bar
                endSent = true;
                R.EndRound((GameOverReason)ZombieWinReason);
                return;
            }
            var p = Helpers.playerById(id);
            if (p == null || p.Data == null || R.IsImpostor(p) || R.FreePlay) return;
            try { p.Data.RpcSetTasks(new Il2CppStructArray<byte>(0)); }
            catch (Exception e) { R.Warn($"task strip of {id} failed: {e.Message}"); }
        }

        private static void HostTick() {
            if (endSent) return;
            if (!started) {
                if (!(introDone || R.FreePlay)) return;
                if (startSeenAt < 0f) startSeenAt = Time.time;
                if (Time.time - startSeenAt < 1f) return;
                SendStart(RoundSeconds());
                return;
            }
            foreach (var kv in bitten.ToList())
                if (Time.time >= kv.Value) SendTurned(kv.Key);
            if (endSent) return;
            int humans = Humans(), zombies = Zombies();
            if (humans == 0) { endSent = true; R.EndRound((GameOverReason)ZombieWinReason); return; }
            if (zombies == 0 && !R.FreePlay) { endSent = true; R.EndRound((GameOverReason)SurvivorWinReason); return; }
            if (Time.time >= endAt) { endSent = true; R.EndRound((GameOverReason)SurvivorWinReason); }
        }

        // ==================================================================== applied on every client

        private static void ApplyStart(float seconds) {
            started = true;
            gameEnding = false;
            endAt = Time.time + Mathf.Clamp(seconds, 5f, 900f);
            R.Log($"round started: {seconds:F0} s, {Zombies()} zombie(s), {Humans()} survivor(s)");
            R.Chat(LocalZombie() ? Tr("intro_z") : Tr("intro_h"));
            if (LocalZombie() && infectButton != null) { infectButton.MaxTimer = Cooldown(); infectButton.Timer = 10f; }
        }

        private static void ApplyBitten(byte target, byte zombie, float delay) {
            bitten[target] = Time.time + Mathf.Clamp(delay, 0.5f, 10f);
            var t = Helpers.playerById(target);
            R.Log($"{t?.Data?.PlayerName ?? target.ToString()} bitten by {Helpers.playerById(zombie)?.Data?.PlayerName ?? zombie.ToString()}");
            var lp = PlayerControl.LocalPlayer;
            if (lp != null && lp.PlayerId == target) {
                try { Helpers.showFlash(Green, delay, Tr("bitten")); } catch { }
            }
            if (lp != null && lp.PlayerId == zombie && infectButton != null) infectButton.Timer = infectButton.MaxTimer;
        }

        private static void ApplyTurned(byte id) {
            bitten.Remove(id);
            if (!turned.Add(id)) return;
            nextLookTry.Remove(id);
            var p = Helpers.playerById(id);
            R.Log($"{p?.Data?.PlayerName ?? id.ToString()} turned ({Zombies()} zombies, {Humans()} survivors)");
            var lp = PlayerControl.LocalPlayer;
            if (lp != null && lp.PlayerId == id) {
                R.Chat(Tr("turned"));
                try { if (Minigame.Instance != null) Minigame.Instance.Close(); } catch { }
                if (infectButton != null) { infectButton.MaxTimer = Cooldown(); infectButton.Timer = Cooldown(); }
            }
        }

        // ==================================================================== look, HUD, buttons

        private static string CorpseHat() {
            if (corpseHat != null) return corpseHat;
            try { corpseHat = UCHats.HatIdOf(HalloweenCorpse.HatName); } catch { }
            if (string.IsNullOrEmpty(corpseHat) || !HalloweenCostumes.HatsRegistered) {
                if (!corpseLogged) { corpseLogged = true; R.Warn("corpse costume not registered (yet) - zombies keep their own look."); }
                corpseHat = null;
                return null;
            }
            return corpseHat;
        }

        private static bool TorLookActive(PlayerControl p) {
            try {
                if (Camouflager.camouflageTimer > 0f || Helpers.MushroomSabotageActive()) return true;
                if (Morphling.morphTimer > 0f && Morphling.morphling == p) return true;
            } catch { }
            return false;
        }

        private static void TickLooks() {
            if (gameEnding) return;
            string hat = CorpseHat();
            if (hat == null) return;
            foreach (var p in Players()) {
                if (!R.IsAlive(p) || !IsZombie(p) || TorLookActive(p)) continue;
                try {
                    var hp = p.cosmetics != null ? p.cosmetics.hat : null;
                    bool wearing = hp != null && hp.Hat != null && hp.Hat.ProductId == hat;
                    if (wearing) { looked.Add(p.PlayerId); continue; }
                    if (nextLookTry.TryGetValue(p.PlayerId, out float at) && Time.time < at) continue;
                    nextLookTry[p.PlayerId] = Time.time + 0.5f;
                    p.setLook(p.Data.PlayerName, p.Data.DefaultOutfit.ColorId, hat, "", "", "");
                    looked.Add(p.PlayerId);
                } catch { nextLookTry[p.PlayerId] = Time.time + 2f; }
            }
        }

        private static void RestoreLooks() {
            // At the end of a round the players go with the scene; touching their hats then throws in
            // HatParent.UpdateMaterial (self test 2026-10-20). Only a mode switched off mid-round needs the look back.
            if (!R.InRound() || gameEnding) { looked.Clear(); nextLookTry.Clear(); return; }
            foreach (var id in looked) {
                try { var p = Helpers.playerById(id); if (p != null && p.Data != null) p.setDefaultLook(); } catch { }
            }
            looked.Clear();
            nextLookTry.Clear();
        }

        private static SpriteRenderer tint;
        private static void TickTint() {
            bool want = LocalZombie() && !R.InMeeting() && DiagMode != "zombie:notint";
            if (!want) { if (tint != null) tint.gameObject.SetActive(false); return; }
            var cam = Camera.main;
            if (cam == null) return;
            if (tint == null) {
                var go = new GameObject("ZombieTint") { layer = PlayerControl.LocalPlayer.gameObject.layer };
                tint = go.AddComponent<SpriteRenderer>();
                tint.sprite = HalloweenModeArt.TintOverlay();
                tint.drawMode = SpriteDrawMode.Tiled;
                tint.color = new Color(1f, 1f, 1f, 0.16f);
            }
            tint.gameObject.SetActive(true);
            float h = cam.orthographicSize * 2f + 1f, w = h * cam.aspect + 1f;
            tint.size = new Vector2(w, h);
            var c = cam.transform.position;
            tint.transform.position = new Vector3(c.x, c.y, -1.2f);
        }

        private static TheOtherRoles.Objects.CustomButton infectButton;
        private static PlayerControl currentTarget;

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Start))]
        static class HudStartPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix(HudManager __instance) {
                try {
                    infectButton = new TheOtherRoles.Objects.CustomButton(
                        () => {
                            if (!LocalZombie() || currentTarget == null) return;
                            RequestInfect(PlayerControl.LocalPlayer.PlayerId, currentTarget.PlayerId);
                            infectButton.Timer = infectButton.MaxTimer;
                            currentTarget = null;
                        },
                        () => LocalZombie(),
                        () => currentTarget != null && PlayerControl.LocalPlayer.CanMove && started,
                        () => { if (infectButton != null) infectButton.Timer = infectButton.MaxTimer; },
                        HalloweenModeArt.InfectButton(),
                        TheOtherRoles.Objects.CustomButton.ButtonPositions.upperRowRight,
                        __instance, KeyCode.Q, false, Tr("infect"));
                    infectButton.MaxTimer = Cooldown();
                    infectButton.Timer = 10f;
                } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{R.LogPrefix} infect button failed: {e}"); }
            }
        }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class HudUpdatePatch {
            [HarmonyPriority(Priority.Low)]   // after TOR's name pass: zombie names turn green
            public static void Postfix(HudManager __instance) {
                try {
                    R.TickFreeplayEnd();
                    if (!Active) { if (started || turned.Count > 0 || looked.Count > 0 || bitten.Count > 0) Reset(); return; }
                    TickLooks();
                    TickTint();

                    // the vanilla kill and sabotage buttons belong to no one here
                    if (__instance.KillButton != null && __instance.KillButton.gameObject.activeSelf) __instance.KillButton.ToggleVisible(false);
                    if (__instance.SabotageButton != null && __instance.SabotageButton.gameObject.activeSelf) __instance.SabotageButton.ToggleVisible(false);

                    foreach (var p in Players()) {
                        if (!IsZombie(p) || p.cosmetics == null || p.cosmetics.nameText == null) continue;
                        if (p.cosmetics.nameText.color != Green) p.cosmetics.nameText.color = Green;
                    }

                    if (LocalZombie() && !R.InMeeting()) {
                        if (infectButton != null) infectButton.MaxTimer = Cooldown();
                        var untargetable = Players().Where(p => IsZombie(p) || bitten.ContainsKey(p.PlayerId)).ToList();
                        currentTarget = PlayerControlFixedUpdatePatch.setTarget(false, false, untargetable);
                        if (currentTarget != null) PlayerControlFixedUpdatePatch.setPlayerOutline(currentTarget, Green);
                    } else currentTarget = null;

                    R.HudLine(started && !SoleSurvivor.Active ? string.Format(Tr("line"), R.Clock(Remaining()), Humans(), Zombies()) : "");

                    if (Time.realtimeSinceStartup < nextHostTick) return;
                    nextHostTick = Time.realtimeSinceStartup + 0.25f;
                    if (R.AmHost) HostTick();
                } catch (Exception e) {
                    if (!tickLogged) { tickLogged = true; HalloweenPlugin.Logger?.LogError($"{R.LogPrefix} zombie tick failed (logged once): {e}"); }
                }
            }
        }
        private static bool tickLogged;

        // The vanilla kill button (start zombies are impostors) never kills here: the target is cleared before TOR's
        // prefix reads it (HarmonyX runs every prefix), and the bite goes through the host instead.
        [HarmonyPatch(typeof(KillButton), nameof(KillButton.DoClick))]
        static class KillButtonPatch {
            [HarmonyPriority(Priority.First)]
            public static bool Prefix(KillButton __instance) {
                try {
                    if (!Active || __instance == null) return true;
                    var target = __instance.currentTarget;
                    __instance.SetTarget(null);
                    if (target != null && LocalZombie() && !__instance.isCoolingDown && (infectButton == null || infectButton.Timer <= 0f)) {
                        RequestInfect(PlayerControl.LocalPlayer.PlayerId, target.PlayerId);
                        if (infectButton != null) infectButton.Timer = infectButton.MaxTimer;
                    }
                    return false;
                } catch { return true; }
            }
        }

        // Zombies shamble: the owner's client moves the player (movement is client-authoritative).
        [HarmonyPatch(typeof(PlayerPhysics), nameof(PlayerPhysics.FixedUpdate))]
        static class SpeedPatch {
            public static void Postfix(PlayerPhysics __instance) {
                try {
                    if (!Active || __instance == null || !__instance.AmOwner || __instance.body == null) return;
                    if (!IsZombie(__instance.myPlayer)) return;
                    __instance.body.velocity *= SpeedFactor();
                } catch { }
            }
        }

        // Only infected players can vent at all through TOR's rule, and only with the option.
        [HarmonyPatch(typeof(Helpers), nameof(Helpers.roleCanUseVents))]
        static class VentRolePatch {
            public static void Postfix(PlayerControl player, ref bool __result) {
                try { if (Active && player != null) __result = MayVent(player); } catch { }
            }
        }

        // Infected players' tasks never count (backstop for the frames before the host's strip lands, and freeplay).
        private static MethodInfo taskSubtract;
        [HarmonyPatch(typeof(GameData), nameof(GameData.RecomputeTaskCounts))]
        static class TaskPatch {
            public static void Postfix(GameData __instance) {
                try {
                    if (turned.Count == 0 || !OptionOn) return;
                    taskSubtract ??= AccessTools.Method(typeof(UCPromotion).Assembly.GetType("UnknownsCollection.UCTaskCount"), "Subtract");
                    if (taskSubtract == null) return;
                    foreach (var id in turned) {
                        var p = Helpers.playerById(id);
                        if (p != null && p.Data != null && !R.IsImpostor(p)) taskSubtract.Invoke(null, new object[] { __instance, p.Data });
                    }
                } catch { }
            }
        }

        // ==================================================================== ending

        // Host: while the mode runs, only its own ends and the server's task win go through.
        [HarmonyPatch(typeof(GameManager), nameof(GameManager.RpcEndGame))]
        static class EndGuardPatch {
            private static float nextLog;
            [HarmonyPriority(Priority.First)]
            public static bool Prefix(ref GameOverReason endReason) {
                try {
                    if (!R.AmHost || !Active || !started) return true;
                    int r = (int)endReason;
                    if (R.AllowEnd || r == ZombieWinReason || r == SurvivorWinReason || endReason == GameOverReason.HumansByTask) return true;
                    if (Time.time >= nextLog) { nextLog = Time.time + 5f; R.Log($"Zombie Outbreak: end reason {r} suppressed."); }
                    return false;
                } catch { return true; }
            }
        }

        private static bool snapActive;
        private static readonly HashSet<byte> snapZombies = new();
        private static int snapReason = -1;

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameEnd))]
        static class OnGameEndPatch {
            [HarmonyPriority(Priority.Last)]
            public static void Prefix() {
                snapActive = OptionOn && started;
                snapZombies.Clear();
                snapReason = -1;
                if (snapActive) foreach (var p in Players()) if (IsZombie(p)) snapZombies.Add(p.PlayerId);
                // take the corpse costumes off while the players still exist (not during the scene teardown)
                RestoreLooks();
                gameEnding = true;
            }

            [HarmonyPriority(Priority.Last)]
            public static void Postfix() {
                try {
                    if (!snapActive) return;
                    int r = (int)TheOtherRoles.Patches.OnGameEndPatch.gameOverReason;
                    bool zombiesWon = r == ZombieWinReason;
                    bool survivorsWon = r == SurvivorWinReason || r == (int)GameOverReason.HumansByTask;
                    if (!zombiesWon && !survivorsWon) return;
                    snapReason = zombiesWon ? ZombieWinReason : SurvivorWinReason;
                    var winners = EndGameResult.CachedWinners;
                    winners.Clear();
                    foreach (var p in Players()) {
                        if (p.Data.Disconnected) continue;
                        bool z = snapZombies.Contains(p.PlayerId);
                        if (z == zombiesWon) winners.Add(new CachedPlayerData(p.Data));
                    }
                    R.SetWinCondition(zombiesWon ? ZombieBanner : SurvivorBanner);
                    R.Log($"round over: {(zombiesWon ? "zombies" : "survivors")} win ({winners.Count} winner(s))");
                } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{R.LogPrefix} zombie OnGameEnd failed: {e}"); }
            }
        }

        [HarmonyPatch(typeof(EndGameManager), nameof(EndGameManager.SetEverythingUp))]
        static class EndScreenPatch {
            [HarmonyPriority(Priority.Last)]
            public static void Postfix(EndGameManager __instance) {
                if (snapReason == ZombieWinReason) R.BonusText(__instance, Tr("win_z"), Green, true);
                else if (snapReason == SurvivorWinReason) R.BonusText(__instance, Tr("win_s"), new Color(1f, 0.85f, 0.4f), true);
            }
        }

        // ==================================================================== self test hooks

        internal static void DiagTurn(byte id) { if (R.AmHost) SendTurned(id); }
        internal static string DiagState() =>
            $"active {Active}, started {started}, left {Remaining():F0}s, zombies {Zombies()}, humans {Humans()}, bitten {bitten.Count}, corpse '{CorpseHat() ?? "-"}', speed {SpeedFactor():F2}, art infect {HalloweenModeArt.HasDelivered("zombie_infect_button.png")}";
        internal static string DiagWearing(PlayerControl p) {
            try { return p.cosmetics.hat.Hat != null ? p.cosmetics.hat.Hat.ProductId : "-"; } catch { return "?"; }
        }

        // ==================================================================== reset

        private static void Reset() {
            RestoreLooks();
            turned.Clear();
            bitten.Clear();
            lastInfect.Clear();
            started = false;
            endSent = false;
            startSeenAt = -1f;
            currentTarget = null;
            try { if (tint != null) UnityEngine.Object.Destroy(tint.gameObject); } catch { }
            tint = null;
            if (!SoleSurvivor.Active) R.ClearHud();
        }

        [HarmonyPatch(typeof(IntroCutscene), nameof(IntroCutscene.OnDestroy))]
        static class IntroEndPatch {
            public static void Postfix() => introDone = true;
        }

        [HarmonyPatch(typeof(RPCProcedure), nameof(RPCProcedure.resetVariables))]
        static class ResetPatch {
            // Called by this plugin's PatchAll during Load(): options and the RPC handler exist from the start.
            static bool Prepare() { Boot(); return true; }
            public static void Postfix() { Reset(); introDone = false; }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class LobbyResetPatch {
            public static void Postfix() { gameEnding = false; Reset(); introDone = false; snapActive = false; snapReason = -1; }
        }
    }
}
