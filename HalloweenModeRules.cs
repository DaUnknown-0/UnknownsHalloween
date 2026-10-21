// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Shared plumbing of the two game modes Zombie Outbreak (ZombieOutbreak.cs) and Sole Survivor (SoleSurvivor.cs):
 *
 *   - one RPC module byte (240 on UC's channel 230): subtypes 0-9 belong to the zombies, 10-19 to the finale;
 *   - the locks both modes need while they run: no meetings (report and emergency button, the pattern of
 *     Unknown's Hunt, copied, no dependency), no sabotage (vanilla sabotage map; doors stay allowed), vents
 *     per mode, ghost tasks per mode;
 *   - the end of a round in freeplay (self test): RpcEndGame has no server there, so after two seconds the end is
 *     played locally through AmongUsClient.OnGameEnd;
 *   - TOR's win-condition banner slot (reflection, like the Xenomorph).
 *
 * Locks are postfixes where TOR has a bool prefix on the same method (HarmonyX runs every prefix, only a
 * postfix has the last word), prefixes only where the original itself must not run.
 */

using System;
using System.Reflection;
using HarmonyLib;
using Hazel;
using UnityEngine;
using UnknownsCollection;

namespace UnknownsHalloween {
    internal static class HalloweenModeRules {
        internal const byte RpcId = 240;   // module byte on UCRpc.CallId 230 (see ID-Registry.md)
        internal const string LogPrefix = "[HalloweenModes]";

        internal static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");
        internal static void Warn(string s) => HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {s}");

        internal static bool AmHost => AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost;
        internal static bool FreePlay => AmongUsClient.Instance != null && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay;
        internal static bool IsAlive(PlayerControl p) => p != null && p.Data != null && !p.Data.IsDead && !p.Data.Disconnected;
        internal static bool IsImpostor(PlayerControl p) => p != null && p.Data != null && p.Data.Role != null && p.Data.Role.IsImpostor;
        internal static bool InMeeting() => MeetingHud.Instance != null || ExileController.Instance != null;

        /// A round is running (freeplay stays in "Joined" for the whole round).
        internal static bool InRound() {
            try {
                var ac = AmongUsClient.Instance;
                return ac != null && ShipStatus.Instance != null && PlayerControl.LocalPlayer != null
                    && (ac.GameState == InnerNet.InnerNetClient.GameStates.Started || ac.NetworkMode == NetworkModes.FreePlay);
            } catch { return false; }
        }

        internal static bool German() { try { return UCLocalization.ActiveCode == "german"; } catch { return false; } }

        /// Meetings, sabotage and the per-mode vent/ghost rules are in force.
        internal static bool Locked => ZombieOutbreak.Active || SoleSurvivor.Active;

        // ---------------------------------------------------------------- RPC

        private static bool registered;
        internal static void Register() {
            if (registered) return;
            registered = true;
            UCRpc.Register(RpcId, Handle);
        }

        internal static MessageWriter Begin(byte sub) {
            var w = UCRpc.Begin(RpcId);
            w.Write(sub);
            return w;
        }

        private static void Handle(MessageReader r) {
            try {
                byte sub = r.ReadByte();
                if (sub < 10) ZombieOutbreak.HandleRpc(sub, r);
                else SoleSurvivor.HandleRpc(sub, r);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} rpc failed: {e}"); }
        }

        // ---------------------------------------------------------------- ending a round

        /// Set while one of the modes ends the round itself, so the own end guards let it through.
        internal static bool AllowEnd;
        private static float freeplayEndAt = -1f;
        private static GameOverReason freeplayReason;

        internal static void EndRound(GameOverReason reason) {
            Log($"ending the round: {(int)reason}");
            AllowEnd = true;
            try { GameManager.Instance.RpcEndGame(reason, false); }
            catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} RpcEndGame failed: {e}"); }
            finally { AllowEnd = false; }
            if (FreePlay) { freeplayEndAt = Time.realtimeSinceStartup + 2f; freeplayReason = reason; }
        }

        /// Freeplay: no server answers RpcEndGame, the end is played locally (self test).
        internal static void TickFreeplayEnd() {
            if (freeplayEndAt < 0f || Time.realtimeSinceStartup < freeplayEndAt) return;
            freeplayEndAt = -1f;
            if (ShipStatus.Instance == null) return;
            try {
                Log($"freeplay: playing the end locally ({(int)freeplayReason})");
                AmongUsClient.Instance.OnGameEnd(new EndGameResult(freeplayReason, false));
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} local end failed: {e}"); }
        }

        private static FieldInfo winConditionField;
        internal static void SetWinCondition(int value) {
            try {
                var asm = typeof(TheOtherRoles.CustomOption).Assembly;
                winConditionField ??= asm.GetType("TheOtherRoles.Patches.AdditionalTempData")?.GetField("winCondition", BindingFlags.Public | BindingFlags.Static);
                var wcEnum = asm.GetType("TheOtherRoles.Patches.WinCondition");
                if (winConditionField != null && wcEnum != null) winConditionField.SetValue(null, Enum.ToObject(wcEnum, value));
            } catch (Exception e) { Warn($"SetWinCondition failed: {e.Message}"); }
        }

        internal static int GetWinCondition() {
            try {
                var asm = typeof(TheOtherRoles.CustomOption).Assembly;
                winConditionField ??= asm.GetType("TheOtherRoles.Patches.AdditionalTempData")?.GetField("winCondition", BindingFlags.Public | BindingFlags.Static);
                return winConditionField == null ? -1 : Convert.ToInt32(winConditionField.GetValue(null));
            } catch { return -1; }
        }

        /// The extra line under "Victory"/"Defeat" (TOR's own bonus line stays empty for a banner value it does not know).
        internal static void BonusText(EndGameManager egm, string text, Color color, bool tintBar) {
            try {
                if (egm == null || egm.WinText == null) return;
                var bonus = UnityEngine.Object.Instantiate(egm.WinText.gameObject);
                bonus.transform.position = new Vector3(egm.WinText.transform.position.x, egm.WinText.transform.position.y - 0.5f, egm.WinText.transform.position.z);
                bonus.transform.localScale = new Vector3(0.7f, 0.7f, 1f);
                var t = bonus.GetComponent<TMPro.TMP_Text>();
                t.text = text;
                t.color = color;
                if (tintBar && egm.BackgroundBar != null) egm.BackgroundBar.material.SetColor("_Color", color);
            } catch (Exception e) { Warn($"end text failed: {e.Message}"); }
        }

        // ---------------------------------------------------------------- HUD line (both modes)

        private static TMPro.TextMeshPro hudText;
        internal static void HudLine(string text) {
            try {
                var hud = HudManager.Instance;
                if (hud == null) return;
                if (string.IsNullOrEmpty(text)) { if (hudText != null) hudText.gameObject.SetActive(false); return; }
                if (hudText == null) {
                    if (hud.KillButton == null || hud.KillButton.cooldownTimerText == null) return;
                    var src = hud.KillButton.cooldownTimerText;
                    hudText = UnityEngine.Object.Instantiate(src, hud.transform).GetComponent<TMPro.TextMeshPro>();
                    if (hudText == null) return;
                    hudText.name = "HalloweenModeLine";
                    hudText.enableWordWrapping = false;
                    hudText.alignment = TMPro.TextAlignmentOptions.Center;
                    hudText.transform.localScale = Vector3.one * 0.45f;
                    hudText.transform.localPosition = new Vector3(0.9f, 2.2f, -50f);   // under the task bar, right of the task list
                }
                hudText.gameObject.SetActive(true);
                if (hudText.text != text) hudText.text = text;
            } catch { }
        }

        internal static void ClearHud() {
            try { if (hudText != null) UnityEngine.Object.Destroy(hudText.gameObject); } catch { }
            hudText = null;
        }

        internal static string Clock(float seconds) {
            int s = Mathf.Max(0, Mathf.CeilToInt(seconds));
            return $"{s / 60}:{s % 60:00}";
        }

        internal static void Chat(string text) {
            try {
                var lp = PlayerControl.LocalPlayer;
                if (lp != null && HudManager.Instance != null && HudManager.Instance.Chat != null) HudManager.Instance.Chat.AddChat(lp, text);
            } catch { }
        }

        // ---------------------------------------------------------------- locks (Unknown's Hunt pattern)

        // Both the report button and the emergency button end in CmdReportDeadBody.
        [HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.CmdReportDeadBody))]
        static class ReportBlockPatch {
            [HarmonyPriority(Priority.First)]
            public static bool Prefix() => !Locked;
        }

        // Host side: a report that still arrives (older client) does not open a meeting either.
        [HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.ReportDeadBody))]
        static class DirectReportBlockPatch {
            [HarmonyPriority(Priority.First)]
            public static bool Prefix() => !Locked;
        }

        [HarmonyPatch(typeof(ReportButton), nameof(ReportButton.DoClick))]
        static class ReportButtonPatch {
            public static bool Prefix() => !Locked;
        }

        [HarmonyPatch(typeof(EmergencyMinigame), nameof(EmergencyMinigame.Update))]
        static class EmergencyBlockPatch {
            public static void Postfix(EmergencyMinigame __instance) {
                try {
                    if (!Locked || __instance == null) return;
                    __instance.StatusText.text = German() ? "Keine Meetings in diesem Modus." : "No meetings in this mode.";
                    __instance.NumberText.text = string.Empty;
                    __instance.ClosedLid.gameObject.SetActive(true);
                    __instance.OpenLid.gameObject.SetActive(false);
                    __instance.ButtonActive = false;
                } catch { }
            }
        }

        // The vanilla sabotage map ends in RpcUpdateSystem(Sabotage); doors use their own call and stay allowed.
        [HarmonyPatch(typeof(ShipStatus), nameof(ShipStatus.RpcUpdateSystem), new[] { typeof(SystemTypes), typeof(byte) })]
        static class SabotageBlockPatch {
            public static bool Prefix(SystemTypes systemType) {
                try { return !(Locked && systemType == SystemTypes.Sabotage); } catch { return true; }
            }
        }

        // Vents: the mode decides (zombies per option, survivors and humans never, nobody in the finale).
        [HarmonyPatch(typeof(Vent), nameof(Vent.CanUse))]
        static class VentPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix([HarmonyArgument(0)] NetworkedPlayerInfo pc, ref float __result,
                                       [HarmonyArgument(1)] ref bool canUse, [HarmonyArgument(2)] ref bool couldUse) {
                try {
                    if (!Locked || pc == null || pc.Object == null) return;
                    bool allow = SoleSurvivor.Active ? false : ZombieOutbreak.MayVent(pc.Object);
                    if (allow) return;
                    if (pc.Object.inVent) return;   // never trap somebody inside
                    canUse = couldUse = false;
                    __result = float.MaxValue;
                } catch { }
            }
        }

        // Ghost tasks are locked in the finale (the task win is server-authoritative, see SoleSurvivor.cs).
        [HarmonyPatch(typeof(Console), nameof(Console.CanUse))]
        static class GhostTaskPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix([HarmonyArgument(0)] NetworkedPlayerInfo pc, ref float __result,
                                       [HarmonyArgument(1)] ref bool canUse, [HarmonyArgument(2)] ref bool couldUse) {
                try {
                    if (!SoleSurvivor.Active || pc == null || !pc.IsDead) return;
                    canUse = couldUse = false;
                    __result = float.MaxValue;
                } catch { }
            }
        }
    }
}
