// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * Haunted Tasks (2026-10-21, idea H7): now and then a task fights back.
 *
 *  - Option 2141 "Haunted Tasks" (under "Halloween Tasks"): how often an opened task is haunted, Off/10/20/30 %.
 *  - Fix Wiring: the first wire put right jumps out again a moment later (never the last one, that would already
 *    have finished the task).
 *  - Every other normal task: the panel slams shut after a few seconds. Finished steps stay finished, so it only
 *    costs time. Sabotage fixes, the emergency button, cameras and admin are never haunted.
 *  - Purely local: every client rolls for its own tasks, nothing goes over the network. Only the minigames are
 *    touched from a tick (no detour on small Il2Cpp methods, see the Minigame.Close lesson).
 */

using System;
using UnityEngine;
using TheOtherRoles;

namespace UnknownsHalloween {
    internal static class HwHauntedTasks {
        private const string LogPrefix = "[Halloween/HauntedTasks]";
        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");

        internal static CustomOption Chance;
        private static readonly string[] Chances = { "Off", "10%", "20%", "30%" };
        private static readonly System.Random rnd = new System.Random();

        // self test: UC_HALLOWEEN_DIAG = haunted (every task is haunted)
        private static bool DiagOn => HwTaskSkins.DiagMode == "haunted" || TrickOrTreatDiag.On;

        private static float Probability() {
            if (DiagOn) return 1f;
            try { return Chance == null ? 0f : Chance.getSelection() * 0.1f; } catch { return 0f; }
        }

        /// <summary>Called from HwTaskSkins.Boot right after option 2140, so it sits under the same heading.</summary>
        internal static void Create() {
            try {
                Chance = CustomOption.Create(2141, CustomOption.CustomOptionType.General, "Haunted Tasks", Chances, null, false);
                UnknownsCollection.UCFx.RegisterTick(Tick);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} registration failed: {e}"); }
        }

        private enum Plan { None, Wire, Slam }
        private static IntPtr seen;
        private static Plan plan;
        private static float at, slamAt;
        private static int wireIndex = -1;

        private static void Tick() {
            try {
                var mg = Minigame.Instance;
                if (mg == null) { seen = IntPtr.Zero; plan = Plan.None; return; }
                if (mg.Pointer != seen) {
                    seen = mg.Pointer;
                    plan = Plan.None;
                    wireIndex = -1;
                    if (!Haunts(mg) || rnd.NextDouble() >= Probability()) return;
                    if (mg.TryCast<WireMinigame>() != null) plan = Plan.Wire;
                    else { plan = Plan.Slam; slamAt = Time.time + 1.5f + (float)rnd.NextDouble() * 2.5f; }
                    Log($"{mg.GetType().Name} is haunted ({plan}).");
                    return;
                }
                if (mg.amClosing != Minigame.CloseState.None) { plan = Plan.None; return; }
                if (plan == Plan.Wire) TickWire(mg.TryCast<WireMinigame>());
                else if (plan == Plan.Slam && Time.time >= slamAt) {
                    plan = Plan.None;
                    Spook();
                    mg.Close();
                    Log("the task slammed shut.");
                }
            } catch (Exception e) { plan = Plan.None; HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} tick: {e.Message}"); }
        }

        private static bool Haunts(Minigame mg) {
            if (!TrickOrTreat.InRound() || TrickOrTreat.InMeeting()) return false;
            var lp = PlayerControl.LocalPlayer;
            if (!TrickOrTreat.IsAlive(lp)) return false;                 // ghosts do their tasks in peace
            var task = mg.MyNormTask;
            if (task == null || task.IsComplete) return false;
            try { if (PlayerTask.TaskIsEmergency(task)) return false; } catch { return false; }
            return true;
        }

        private static void TickWire(WireMinigame wm) {
            if (wm == null) { plan = Plan.None; return; }
            int n = wm.ActualWires.Length, right = 0, first = -1;
            for (int i = 0; i < n; i++)
                if (wm.ActualWires[i] == wm.ExpectedWires[i]) { right++; if (first < 0) first = i; }
            if (wireIndex < 0) {
                if (right == 0) return;
                if (right >= n) { plan = Plan.None; return; }
                wireIndex = first;
                at = Time.time + 0.45f;
                return;
            }
            if (Time.time < at) return;
            plan = Plan.None;
            if (right >= n || wm.ActualWires[wireIndex] != wm.ExpectedWires[wireIndex]) return;
            wm.ActualWires[wireIndex] = -1;
            try { var w = wm.LeftNodes[wireIndex]; w.ResetLine(w.BaseWorldPos, true); } catch { }
            try { wm.UpdateLights(); } catch { }
            Spook();
            Log($"wire {wireIndex} jumped out.");
        }

        private static void Spook() {
            TreatFx.Play(Giggle(), 0.6f, 0f);
            TreatFx.ShowHint(TrickOrTreat.De() ? "Die Aufgabe spukt!" : "The task is haunted!");
        }

        internal static string DiagPlan => plan.ToString();

        private static AudioClip giggle;
        private static AudioClip Giggle() {
            if (giggle != null) return giggle;
            double ph = 0;
            giggle = TreatFx.MakeClip("hw_haunted_giggle", 0.9f, (t, len) => {
                // a breathy ghost giggle: four falling "hee" pulses with vibrato
                float pulse = (t * 4.6f) % 1f;
                float env = Mathf.Clamp01(pulse / 0.08f) * Mathf.Clamp01((0.55f - pulse) / 0.3f) * Mathf.Clamp01((len - t) / 0.2f);
                float f = 760f - t * 260f + 18f * Mathf.Sin(t * 40f);
                ph += 2 * Math.PI * f / 44100;
                return 0.35f * env * (float)(Math.Sin(ph) + 0.3 * Math.Sin(ph * 2.01));
            });
            return giggle;
        }
    }
}
