// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Self test of the omens and the spook moments (only with the environment variable UC_HALLOWEEN_DIAG=omens or =spook).
 *
 * Needs a freeplay round that starts on its own (Unknown's Atlas ForceMap). omens: every omen is forced once
 * with its card (screenshot each), vision radius per omen, the ravens 20 s after a real kill on a dummy, Bat Night's
 * second break of Comms, Harvest's candy factor, Silent Night's emergency cooldown, a lightning strike with rain.
 * spook: the spots of the plan, every kind of moment once next to the player, then the midnight moment (forced).
 * Screenshots into <game>\UCShots\omens\ and \spook\. Ends with "[Halloween/Omens] diag: all done" and quits.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class OmensDiag {
        private static readonly string Mode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        internal static readonly bool Omens = Mode == "omens";
        internal static readonly bool Spook = Mode == "spook";
        internal static readonly bool On = Omens || Spook;
        private const string P = UnknownsHalloween.Omens.LogPrefix + " diag:";

        private static List<(float wait, Action act)> steps;
        private static int step;
        private static float at = -1f, roundSeen = -1f;
        private static string dir;

        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{P} {s}");

        internal static void Tick() {
            if (!On) return;
            try {
                var lp = PlayerControl.LocalPlayer;
                bool round = ShipStatus.Instance != null && lp != null && AmongUsClient.Instance != null
                    && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay;
                if (!round) return;
                if (steps == null) {
                    if (roundSeen < 0f) roundSeen = Time.time;
                    if (Time.time - roundSeen < 5f) return;
                    steps = new List<(float, Action)>();
                    dir = Path.Combine(BepInEx.Paths.GameRootPath, "UCShots", Omens ? "omens" : "spook");
                    Directory.CreateDirectory(dir);
                    if (Omens) BuildOmens(lp); else BuildSpook(lp);
                    steps.Add((1.0f, () => Log("all done")));
                    steps.Add((0.5f, () => Application.Quit()));
                    step = 0;
                    at = Time.time + steps[0].wait;
                }
                while (step < steps.Count && Time.time >= at) {
                    try { steps[step].act(); } catch (Exception e) { Log($"step {step} failed: {e}"); }
                    step++;
                    if (step < steps.Count) at = Time.time + steps[step].wait;
                }
            } catch (Exception e) { Log($"tick failed: {e.Message}"); }
        }

        private static void Add(float wait, Action a) => steps.Add((wait, a));
        private static void Shot(string name) {
            try { ScreenCapture.CaptureScreenshot(Path.Combine(dir, name + ".png")); Log($"shot {name}"); } catch (Exception e) { Log($"shot {name}: {e.Message}"); }
        }
        private static float Radius() {
            try { return ShipStatus.Instance.CalculateLightRadius(PlayerControl.LocalPlayer.Data); } catch { return -1f; }
        }
        private static string F(float v) => v.ToString("F2", System.Globalization.CultureInfo.InvariantCulture);

        private static void BuildOmens(PlayerControl lp) {
            float r0 = 0f;
            Add(0.5f, () => {
                r0 = Radius();
                Log($"base vision radius {F(r0)}, intro done {UnknownsHalloween.Omens.introDone}, omen {UnknownsHalloween.Omens.current}, werewolf hook {UnknownsHalloween.Omens.DiagWolfHook}");
                Log("pictures from files: " + (OmensFx.fromFile.Count == 0 ? "none (placeholders)" : string.Join(", ", OmensFx.fromFile)));
            });
            for (int i = 0; i < (int)Omen.Count; i++) {
                var o = (Omen)i;
                Add(0.8f, () => UnknownsHalloween.Omens.DiagForce(o));
                Add(1.4f, () => {
                    Shot("omen_" + UnknownsHalloween.Omens.Keys[(int)o]);
                    float r = Radius();
                    Log($"{UnknownsHalloween.Omens.Names[(int)o]}: card '{OmensFx.CardShown}', vision {F(r)} (x{F(r0 > 0f ? r / r0 : 0f)})");
                });
                switch (o) {
                    case Omen.Raven: {
                        PlayerControl dummy = null;
                        Add(5.5f, () => {
                            dummy = PlayerControl.AllPlayerControls.ToArray().FirstOrDefault(p => p != null && p != lp && TrickOrTreat.IsAlive(p));
                            if (dummy == null) { Log("raven: no dummy"); return; }
                            try { dummy.NetTransform.SnapTo(lp.GetTruePosition() + new Vector2(0.9f, 0f)); } catch { }
                        });
                        Add(0.6f, () => {
                            if (dummy == null) return;
                            lp.MurderPlayer(dummy, MurderResultFlags.Succeeded);
                            Log($"raven: killed {dummy.Data?.PlayerName}, kills tracked {UnknownsHalloween.Omens.kills.Count}");
                        });
                        Add(10f, () => Log($"raven: 10 s after the kill, ravens shown {OmensFx.RavensShown} (expected 0)"));
                        Add(11.5f, () => { Shot("raven_ravens"); Log($"raven: 21.5 s after the kill, ravens shown {OmensFx.RavensShown}"); });
                        break;
                    }
                    case Omen.BatNight:
                        Add(5.5f, () => {
                            try { ShipStatus.Instance.RpcUpdateSystem(SystemTypes.Sabotage, (byte)SystemTypes.Comms); } catch (Exception e) { Log("bat: sabotage failed " + e.Message); }
                        });
                        Add(2f, () => { Log($"bat: comms active {UnknownsHalloween.Omens.CommsActive()}"); Shot("batnight_comms"); });
                        Add(0.5f, () => { try { ShipStatus.Instance.RpcUpdateSystem(SystemTypes.Comms, 0); } catch (Exception e) { Log("bat: repair failed " + e.Message); } });
                        Add(1f, () => Log($"bat: right after the first fix: comms active {UnknownsHalloween.Omens.CommsActive()}, state '{UnknownsHalloween.Omens.DiagBat}'"));
                        Add(2f, () => { Log($"bat: 3 s after the first fix: comms active {UnknownsHalloween.Omens.CommsActive()}, state '{UnknownsHalloween.Omens.DiagBat}'"); });
                        Add(0.5f, () => { try { ShipStatus.Instance.RpcUpdateSystem(SystemTypes.Comms, 0); } catch { } });
                        Add(2.5f, () => Log($"bat: after the second fix: comms active {UnknownsHalloween.Omens.CommsActive()}, state '{UnknownsHalloween.Omens.DiagBat}'"));
                        break;
                    case Omen.Harvest:
                        Add(0.3f, () => Log($"harvest: candy factor {UnknownsHalloween.Omens.CandyFactor()}, candies per spawn {TrickOrTreat.Count()} (Trick or Treat on: {TrickOrTreat.On()})"));
                        break;
                    case Omen.SilentNight:
                        Add(0.3f, () => Log($"silent night: emergency cooldown {F(UnknownsHalloween.Omens.DiagEmergency())} s"));
                        break;
                    case Omen.Thunderstorm:
                        Add(5f, () => Shot("thunder_rain"));
                        Add(0.4f, () => OmensFx.Strike());
                        Add(0.03f, () => { Shot("thunder_flash"); Log($"thunder: vision during the strike {F(Radius())} (full sight {F(OmensFx.FullSight())})"); });
                        Add(0.5f, () => { Shot("thunder_afterglow"); Log($"thunder: afterglow vision {F(Radius())}"); });
                        Add(1.5f, () => Log($"thunder: vision after the strike {F(Radius())}"));
                        Add(0.2f, () => {
                            // the seeded schedule of the round
                            var rng = new System.Random(UnknownsHalloween.Omens.seed ^ 0x51A7);
                            float t = 0f; var list = new List<string>();
                            for (int k = 0; k < 6; k++) { t += 40f + (float)rng.NextDouble() * 50f; list.Add(F(t)); }
                            Log("thunder: strike times of the seed " + string.Join(", ", list));
                        });
                        break;
                }
            }
            Add(0.5f, () => { OmensMenu.Open(); });
            Add(1.0f, () => { Log($"menu open {OmensMenu.IsOpen}"); Shot("menu"); });
            Add(0.5f, () => OmensMenu.Close());
        }

        private static Spooks.Spot SpotFor(PlayerControl lp, Spooks.Kind k) {
            var me = lp.GetTruePosition();
            var s = Spooks.spots.Where(x => x.Kind == k).OrderBy(x => (x.Pos - me).sqrMagnitude).FirstOrDefault();
            return s ?? new Spooks.Spot { Pos = me + new Vector2(0.8f, 0.4f), Kind = k, Param = (byte)(k == Spooks.Kind.Spider ? 22 : 0) };
        }

        private static void BuildSpook(PlayerControl lp) {
            Add(0.5f, () => {
                Log($"plan: {Spooks.spots.Count} spots: " + string.Join(", ", Enumerable.Range(0, (int)Spooks.Kind.Count).Select(i => $"{(Spooks.Kind)i} {Spooks.spots.Count(s => (int)s.Kind == i)}")));
                Log("pictures from files: " + (OmensFx.fromFile.Count == 0 ? "none (placeholders)" : string.Join(", ", OmensFx.fromFile)));
            });
            var peaks = new Dictionary<Spooks.Kind, float> { { Spooks.Kind.Ghost, 2.6f }, { Spooks.Kind.Bats, 1.2f }, { Spooks.Kind.Spider, 2.8f }, { Spooks.Kind.Pumpkin, 1.3f } };
            for (int i = 0; i < (int)Spooks.Kind.Count; i++) {
                var k = (Spooks.Kind)i;
                Spooks.Spot s = null;
                Add(1.0f, () => {
                    s = SpotFor(lp, k);
                    var stand = k == Spooks.Kind.Ghost ? s.Pos + new Vector2(0f, -1.1f) : s.Pos + new Vector2(-0.9f, -0.3f);
                    try { lp.NetTransform.SnapTo(stand); } catch { }
                    Log(FormattableString.Invariant($"{k}: spot {s.Pos.x:F1},{s.Pos.y:F1} param {s.Param}"));
                });
                Add(1.2f, () => Spooks.Play(s));
                Add(peaks[k], () => Shot("spook_" + k.ToString().ToLowerInvariant()));
            }
            Add(4f, () => { Log($"moments played {Spooks.Played}"); Spooks.QueueMidnight(); });
            Add(3.6f, () => { Shot("midnight_strikes"); Log($"midnight: strike {Spooks.MidnightStrikes}"); });
            Add(5.0f, () => { Shot("midnight_moon"); Log($"midnight: strike {Spooks.MidnightStrikes}"); });
            Add(3.4f, () => { Shot("midnight_twelve"); Log($"midnight: strike {Spooks.MidnightStrikes}, running {Spooks.MidnightRunning}"); });
            Add(4.5f, () => Log($"midnight: running after the end {Spooks.MidnightRunning}"));
        }
    }
}
