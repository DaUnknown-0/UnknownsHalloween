// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Self test of the two game modes, only with the environment variable UC_HALLOWEEN_DIAG set to
 *   zombie            infection with the turn, zombie look, meeting lock, zombie win
 *   zombie:survivors  a dummy zombie, the clock runs out, survivor win
 *   finalgirl         a dummy impostor, parity held back, finale with darkness, arrow and exit, escape (crew win)
 *   finalgirl:timeout the same finale, the time runs out (impostor win)
 * Needs a freeplay round that starts on its own (Unknown's Atlas ForceMap = vanilla:Skeld). Screenshots go to
 * <game>\UCShots\hw2026zombie\, the run ends with "[HalloweenModes] diag: all done" and quits. The timeline is a
 * Reactor coroutine, so it survives the change into the end screen.
 */

using System;
using System.Collections;
using System.IO;
using System.Linq;
using AmongUs.GameOptions;
using HarmonyLib;
using UnityEngine;
using R = UnknownsHalloween.HalloweenModeRules;

namespace UnknownsHalloween {
    internal static class HalloweenModeDiag {
        private static string Mode => ZombieOutbreak.DiagMode;
        private static bool On => ZombieOutbreak.Diag || FinalGirl.Diag;
        private static bool running;
        private static float roundSeen = -1f;
        private static string dir;

        private static void Log(string s) => R.Log("diag: " + s);

        private static void Shot(string name) {
            try { ScreenCapture.CaptureScreenshot(Path.Combine(dir, name + ".png")); Log("shot " + name); }
            catch (Exception e) { Log($"shot {name}: {e.Message}"); }
        }

        private static IEnumerator Wait(float seconds) {
            float until = Time.realtimeSinceStartup + seconds;
            while (Time.realtimeSinceStartup < until) yield return null;
        }

        private static PlayerControl[] Dummies(PlayerControl lp) =>
            PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p != lp && R.IsAlive(p)).ToArray();

        // walking for the self test (before the modes' speed postfixes: Priority.First)
        private static float walk;
        private static void Walk(float dir) => walk = dir;

        [HarmonyPatch(typeof(PlayerPhysics), nameof(PlayerPhysics.FixedUpdate))]
        static class WalkPatch {
            [HarmonyPriority(Priority.First)]
            public static void Postfix(PlayerPhysics __instance) {
                try {
                    if (!On || walk == 0f || __instance == null || !__instance.AmOwner || __instance.body == null) return;
                    __instance.body.velocity = new Vector2(walk * 2.5f, 0f);
                } catch { }
            }
        }

        private static void Snap(PlayerControl p, Vector2 at) {
            try { p.NetTransform.SnapTo(at); }
            catch (Exception e) {
                Log("snap failed (" + e.GetType().Name + ") - moving the transform instead");
                try { p.transform.position = new Vector3(at.x, at.y, p.transform.position.z); } catch { }
            }
        }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class StartPatch {
            public static void Postfix() {
                if (!On || running) return;
                try {
                    if (!R.FreePlay || ShipStatus.Instance == null || PlayerControl.LocalPlayer == null) return;
                    if (roundSeen < 0f) roundSeen = Time.realtimeSinceStartup;
                    if (Time.realtimeSinceStartup - roundSeen < 4f) return;
                    running = true;
                    dir = Path.Combine(BepInEx.Paths.GameRootPath, "UCShots", "hw2026zombie");
                    Directory.CreateDirectory(dir);
                    Reactor.Utilities.Coroutines.Start(Mode.StartsWith("zombie") ? Zombie() : Final());
                } catch (Exception e) { Log("start failed: " + e); }
            }
        }

        private static IEnumerator Quit() {
            yield return Wait(1f);
            Log("all done");
            yield return Wait(0.5f);
            Application.Quit();
        }

        // ---------------------------------------------------------------- Zombie Outbreak

        private static IEnumerator Zombie() {
            var lp = PlayerControl.LocalPlayer;
            bool survivors = Mode == "zombie:survivors";
            Log($"mode {Mode} | {ZombieOutbreak.DiagState()} | dummies {Dummies(lp).Length}");
            Shot("z01_start");
            var dummies = Dummies(lp);
            if (dummies.Length < 2) { Log("not enough dummies"); yield return Quit(); yield break; }
            var d1 = dummies[0];

            if (!survivors) {
                ZombieOutbreak.DiagTurn(lp.PlayerId);
                yield return Wait(1.5f);
                Log($"local turned | wearing {ZombieOutbreak.DiagWearing(lp)} | {ZombieOutbreak.DiagState()}");
                Shot("z02_self_zombie");
                Snap(d1, lp.GetTruePosition() + new Vector2(0.9f, 0f));
                yield return Wait(0.6f);
                // a bite from too far must be refused
                Log("far bite: " + ZombieOutbreak.HostInfect(lp.PlayerId, dummies[1].PlayerId));
                Log("bite: " + ZombieOutbreak.HostInfect(lp.PlayerId, d1.PlayerId));
                Log("second bite at once (cooldown): " + ZombieOutbreak.HostInfect(lp.PlayerId, d1.PlayerId));
                yield return Wait(0.5f);
                Log($"bitten {ZombieOutbreak.IsBitten(d1.PlayerId)}, dummy zombie {ZombieOutbreak.IsZombie(d1)}");
                Shot("z03_bitten");
                yield return Wait(3.2f);
                Log($"after the delay: dummy zombie {ZombieOutbreak.IsZombie(d1)}, wearing {ZombieOutbreak.DiagWearing(d1)} | {ZombieOutbreak.DiagState()}");
                Shot("z04_turned");
                // walk a little: the corpse costume walking, the zombie speed
                Vector2 before = lp.GetTruePosition();
                Walk(1f);
                yield return Wait(1.0f);
                Walk(0f);
                Log($"walked {Vector2.Distance(before, lp.GetTruePosition()):F2} units in 1 s (diag walk speed 2.5 x zombie factor)");
                Shot("z05_walk");
                // meetings are locked
                try { lp.CmdReportDeadBody(null); } catch (Exception e) { Log("report: " + e.Message); }
                yield return Wait(1.2f);
                Log($"emergency call -> meeting open: {MeetingHud.Instance != null}");
                Shot("z06_no_meeting");
                // the zombies win: everybody else turns
                foreach (var p in Dummies(lp)) if (!ZombieOutbreak.IsZombie(p)) ZombieOutbreak.DiagTurn(p.PlayerId);
                Log($"all turned | {ZombieOutbreak.DiagState()}");
                yield return Wait(1.0f);
                Shot("z07_horde");
                yield return Wait(5.0f);
                Shot("z08_zombies_win");
            } else {
                ZombieOutbreak.DiagTurn(d1.PlayerId);
                Snap(d1, lp.GetTruePosition() + new Vector2(1.2f, 0f));
                yield return Wait(1.5f);
                Log($"dummy zombie {ZombieOutbreak.IsZombie(d1)}, wearing {ZombieOutbreak.DiagWearing(d1)} | {ZombieOutbreak.DiagState()}");
                Shot("s01_dummy_zombie");
                ZombieOutbreak.SendTimer(4f);
                yield return Wait(1.0f);
                Shot("s02_clock");
                yield return Wait(8.0f);
                Shot("s03_survivors_win");
            }
            yield return Quit();
        }

        // ---------------------------------------------------------------- Final Girl

        private static IEnumerator Final() {
            var lp = PlayerControl.LocalPlayer;
            bool timeout = Mode == "finalgirl:timeout";
            if (timeout) FinalGirl.DiagLimit = 6f;
            FinalGirl.DiagIgnoreTasks = true;
            var dummies = Dummies(lp);
            Log($"mode {Mode} | dummies {dummies.Length} | {FinalGirl.DiagState()}");
            if (dummies.Length < 1) { Log("no dummy"); yield return Quit(); yield break; }
            var imp = dummies[0];
            try { imp.RpcSetRole(RoleTypes.Impostor, true); } catch (Exception e) { Log("RpcSetRole: " + e.Message); }
            yield return Wait(0.5f);
            if (!R.IsImpostor(imp)) { try { RoleManager.Instance.SetRole(imp, RoleTypes.Impostor); } catch (Exception e) { Log("SetRole: " + e.Message); } }
            Snap(imp, lp.GetTruePosition() + new Vector2(-2.5f, 0f));
            // the others die (Exiled() threw on freeplay dummies; the corpse probe's self-murder works)
            foreach (var p in dummies.Skip(1)) {
                try { TheOtherRoles.RPCProcedure.uncheckedExilePlayer(p.PlayerId); } catch (Exception e) { Log("exile: " + e.GetType().Name); }
                if (R.IsAlive(p)) { try { p.Die(DeathReason.Exile, false); } catch (Exception e) { Log("die: " + e.GetType().Name); } }
                if (R.IsAlive(p)) { try { p.Data.IsDead = true; } catch { } }
            }
            yield return Wait(1.0f);
            Log("dummies dead: " + string.Join(", ", dummies.Skip(1).Select(p => $"{p.Data?.PlayerName}={p.Data?.IsDead}")));
            Log($"impostor dummy {R.IsImpostor(imp)}, alive {PlayerControl.AllPlayerControls.ToArray().Count(R.IsAlive)}");
            FinalGirl.Conditions(out var found, out string why);
            Log($"conditions: {why}");
            Shot("f01_before");
            // what TOR sends at parity
            try { GameManager.Instance.RpcEndGame(GameOverReason.ImpostorByKill, false); } catch (Exception e) { Log("RpcEndGame: " + e.Message); }
            Log($"after the parity end: {FinalGirl.DiagState()}");
            yield return Wait(2.5f);
            Log($"finale | {FinalGirl.DiagState()} | light me {FinalGirl.DiagLight(lp):F2}, impostor {FinalGirl.DiagLight(imp):F2}");
            Shot("f02_finale_start");
            try { lp.CmdReportDeadBody(null); } catch (Exception e) { Log("report: " + e.Message); }
            yield return Wait(1.0f);
            Log($"emergency call -> meeting open: {MeetingHud.Instance != null}");
            Walk(1f);
            yield return Wait(0.6f);
            Walk(0f);
            Shot("f03_flashlight");
            if (!timeout) {
                var exit = FinalGirl.ExitPos;
                Snap(lp, exit + new Vector2(-2.6f, 0f));
                yield return Wait(1.0f);
                Shot("f04_exit_near");
                Snap(lp, exit);
                yield return Wait(1.5f);
                Log($"at the exit | {FinalGirl.DiagState()}");
                yield return Wait(4.5f);
                Shot("f05_escaped");
            } else {
                yield return Wait(10f);
                Shot("f05_caught");
            }
            yield return Quit();
        }
    }
}
