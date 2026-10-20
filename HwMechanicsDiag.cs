// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Self test of the three mechanics (only with UC_HALLOWEEN_DIAG = scaredy, mirror, phantom or mechanics = all three).
 * Needs a freeplay round that starts on its own (Unknown's Atlas ForceMap). Screenshots go to
 * <game>\UCShots\hw2026\, the log lines start with "[Halloween/Mechanics] diag:". Ends with "diag: all done" and quits.
 *
 *  - scaredy: the local player becomes the Scaredy-Cat, a dummy dies next to him (scream with banner and mark), a second
 *    dummy dies far away behind walls (no scream), the same body twice (no second scream).
 *  - mirror: the mirrors of the map, the local player in front of one (own colour), morphed into the Xenomorph costume
 *    in black (the reflection keeps the real colour), a dummy next to him (two reflections), the fog.
 *  - phantom: the graph built twice (same result), the sabotage map with the button, a click on it, phantoms walking
 *    (follow shots next to a real dummy), a touch (mist), the end of the parade.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using TheOtherRoles;

namespace UnknownsHalloween {
    internal static class HwMechanicsDiag {
        private static readonly string Mode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        private static bool All => Mode == "mechanics";
        internal static readonly bool On = Mode == "scaredy" || Mode == "mirror" || Mode == "phantom" || Mode == "mechanics";

        private static List<(float wait, Action act)> steps;
        private static int step;
        private static float at = -1f, roundSeen = -1f;
        private static string dir;

        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{HwMechanics.LogPrefix} diag: {s}");

        internal static void Tick() {
            if (!On) return;
            try {
                var lp = PlayerControl.LocalPlayer;
                bool round = ShipStatus.Instance != null && lp != null && HwMechanics.FreePlay();
                if (!round) return;
                if (steps == null) {
                    if (roundSeen < 0f) roundSeen = Time.time;
                    if (Time.time - roundSeen < 5f) return;
                    Build(lp);
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

        private static void Shot(string name) {
            try { ScreenCapture.CaptureScreenshot(Path.Combine(dir, name + ".png")); Log($"shot {name}"); } catch (Exception e) { Log($"shot {name}: {e.Message}"); }
        }

        private static void SnapFeet(PlayerControl p, Vector2 feet) =>
            p.NetTransform.SnapTo(feet + ((Vector2)p.transform.position - p.GetTruePosition()));

        private static List<PlayerControl> Dummies(PlayerControl lp) =>
            PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p != lp && HwMechanics.IsAlive(p)).ToList();

        private static void Build(PlayerControl lp) {
            dir = Path.Combine(BepInEx.Paths.GameRootPath, "UCShots", "hw2026");
            Directory.CreateDirectory(dir);
            steps = new List<(float, Action)>();
            HwMechanics.LangOverride = true;           // German texts on the pictures
            Vector2 home = lp.GetTruePosition();
            steps.Add((0f, () => Log($"start: map {ShipStatus.Instance.name}, atlas '{HwMechanics.AtlasMap() ?? "null"}', players {PlayerControl.AllPlayerControls.Count}, host {HwMechanics.AmHost()}")));
            if (Mode == "scaredy" || All) Scaredy(lp, home);
            if (Mode == "mirror" || All) Mirror(lp, home);
            if (Mode == "phantom" || All) Phantom(lp, home);
            steps.Add((1.0f, () => {
                Log($"pictures from files: {HwArt.fromFile.Count} ({string.Join(", ", HwArt.fromFile)})");
                Log("all done");
            }));
            steps.Add((0.5f, () => Application.Quit()));
        }

        // ---------------------------------------------------------------- Scaredy-Cat
        private static void Scaredy(PlayerControl lp, Vector2 home) {
            PlayerControl near = null, far = null;
            int before = 0;
            void Add(float w, Action a) => steps.Add((w, a));
            Add(0.2f, () => {
                SnapFeet(lp, home);
                HwScaredyCat.DiagMakeLocal();
                var roles = RoleInfo.getRoleInfoForPlayer(lp, true);
                Log($"scaredy: carrier local {HwScaredyCat.IsLocalCarrier()}, role infos [{string.Join(", ", roles.Select(r => r.name))}], counts as modifier {UnknownsCollection.UCPromotion.HasAnyModifier(lp)}");
                var d = Dummies(lp);
                near = d.ElementAtOrDefault(0);
                far = d.ElementAtOrDefault(1);
                if (near != null) SnapFeet(near, home + new Vector2(1.8f, 0.2f));
                // far away: the farthest walkable vent spot, behind walls
                if (far != null) {
                    var vents = ShipStatus.Instance.AllVents.ToArray().Where(v => v != null).OrderByDescending(v => ((Vector2)v.transform.position - home).sqrMagnitude).ToList();
                    if (vents.Count > 0) SnapFeet(far, (Vector2)vents[0].transform.position + new Vector2(0.7f, 0f));
                }
                before = HwScaredyCat.DiagScreams;
            });
            Add(0.6f, () => { if (far != null) far.MurderPlayer(far, MurderResultFlags.Succeeded); });
            Add(1.0f, () => Log($"scaredy: far body -> screams {HwScaredyCat.DiagScreams - before} (want 0)"));
            Add(0.2f, () => { if (near != null) near.MurderPlayer(near, MurderResultFlags.Succeeded); });
            Add(0.45f, () => Shot("scaredy_scream_pop"));
            Add(0.6f, () => {
                Log($"scaredy: near body -> screams {HwScaredyCat.DiagScreams - before} (want 1), text \"{HwScaredyCat.LastText}\"");
                Shot("scaredy_scream");
            });
            // the same body again: nothing (the carrier remembers it, the host too)
            Add(0.3f, () => { SnapFeet(lp, home + new Vector2(-3f, 0f)); });
            Add(0.6f, () => SnapFeet(lp, home));
            Add(0.8f, () => Log($"scaredy: same body again -> screams {HwScaredyCat.DiagScreams - before} (want 1)"));
            // English text too
            Add(0.1f, () => { HwMechanics.LangOverride = false; Log($"scaredy: english \"{(HwMechanics.RoomName((byte)SystemTypes.Cafeteria))}\" -> {HwMechanics.RoomName(255) ?? "null"}"); HwMechanics.LangOverride = true; });
            Add(4.5f, () => { Log($"scaredy: mark gone after its time"); Shot("scaredy_after"); });
        }

        // ---------------------------------------------------------------- Haunted Mirrors
        private static void Mirror(PlayerControl lp, Vector2 home) {
            void Add(float w, Action a) => steps.Add((w, a));
            HwMirrors.Mirror m = null;
            PlayerControl d = null;
            Add(0.2f, () => {
                HwMirrors.DiagForce = true;
                HwMirrors.Clear();
            });
            Add(0.4f, () => {
                Log($"mirror: {HwMirrors.mirrors.Count} mirrors, style {HwMirrors.Style}: " + string.Join("; ", HwMirrors.mirrors.Select(x => $"{x.Room} at ({x.Foot.x:F2}, {x.Foot.y:F2})")));
                m = HwMirrors.mirrors.FirstOrDefault();
                if (m == null) return;
                SnapFeet(lp, m.Foot + new Vector2(0.15f, -0.8f));
                d = Dummies(lp).FirstOrDefault();
                if (d != null) SnapFeet(d, home);
            });
            Add(0.8f, () => { Log($"mirror: own reflection shown {HwMirrors.DiagShown} (want 1), colour {lp.Data.DefaultOutfit.ColorId}"); Shot("mirror_self"); });
            Add(0.2f, () => {
                if (m != null) { m.FogUntil = -1f; m.SeenSince = -1f; }
                // the Xenomorph look in black: the reflection keeps the real colour
                lp.setLook(lp.Data.PlayerName, 6, "hat_Halloween_Xenomorph", "", "", "");
                if (d != null && m != null) SnapFeet(d, m.Foot + new Vector2(-0.7f, -1.1f));
                if (m != null) { m.SeenSince = -1f; }
            });
            Add(0.9f, () => {
                Log($"mirror: costumed (shows colour {lp.cosmetics.ColorId}, real {lp.Data.DefaultOutfit.ColorId}), reflections {HwMirrors.DiagShown} (want 2)");
                Shot("mirror_costumed");
            });
            Add(0.2f, () => {
                // a morph into the dummy (TOR's Morphling path is setLook as well)
                if (d != null) { var o = d.Data.DefaultOutfit; lp.setLook(o.PlayerName, o.ColorId, o.HatId, o.VisorId, o.SkinId, o.PetId); }
                if (d != null && m != null) SnapFeet(d, home);
                if (m != null) { m.FogUntil = -1f; m.SeenSince = -1f; }
            });
            Add(0.9f, () => { Log($"mirror: morphed into {d?.Data?.PlayerName} (shows {lp.cosmetics.ColorId}), reflection {HwMirrors.DiagShown}"); Shot("mirror_morphed"); });
            Add(1.6f, () => { Log($"mirror: after 2.5 s in front, fogged {m != null && m.FogUntil > Time.time}, reflections {HwMirrors.DiagShown} (want 0)"); Shot("mirror_fogged"); });
            Add(0.2f, () => {
                var o = lp.Data.DefaultOutfit;
                lp.setLook(o.PlayerName, o.ColorId, o.HatId, o.VisorId, o.SkinId, o.PetId);
                SnapFeet(lp, home);
                HwMirrors.DiagForce = false;
            });
        }

        // ---------------------------------------------------------------- Phantom Parade
        private static void Phantom(PlayerControl lp, Vector2 home) {
            void Add(float w, Action a) => steps.Add((w, a));
            PlayerControl d = null;
            Add(0.3f, () => {
                HwPhantomParade.DiagForce = true;
                SnapFeet(lp, home);
                var ship = ShipStatus.Instance;
                PhantomGraph.Ensure(ship);
                int n1 = PhantomGraph.Nodes.Count, m1 = PhantomGraph.Main.Count;
                float h1 = PhantomGraph.Nodes.Sum(p => p.x * 0.37f + p.y);
                // force a second build: the same geometry has to give the same graph
                typeof(PhantomGraph).GetField("builtFor", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static)?.SetValue(null, IntPtr.Zero);
                PhantomGraph.Ensure(ship);
                float h2 = PhantomGraph.Nodes.Sum(p => p.x * 0.37f + p.y);
                Log($"phantom: graph twice: nodes {n1}/{PhantomGraph.Nodes.Count}, walkable {m1}/{PhantomGraph.Main.Count}, hash {h1:F3}/{h2:F3} -> same {n1 == PhantomGraph.Nodes.Count && Mathf.Abs(h1 - h2) < 0.001f}");
                try { HudManager.Instance.ToggleMapVisible(new MapOptions { Mode = MapOptions.Modes.Sabotage }); } catch (Exception e) { Log($"phantom: map: {e.Message}"); }
            });
            Add(1.0f, () => { Log($"phantom: map button shown {HwPhantomParade.MapButtonShown} at {HwPhantomParade.MapButtonPos}, wait {HwPhantomParade.Wait():F1}"); Shot("phantom_mapbutton"); });
            Add(0.2f, () => {
                // what the click does; the freeplay round has no cooldown start
                typeof(HwPhantomParade).GetField("readyAt", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static)?.SetValue(null, 0f);
                try {
                    var ov = MapBehaviour.Instance.infectedOverlay;
                    var bb = ov.transform.Find("Hw_PhantomParade")?.GetComponent<ButtonBehavior>();
                    if (bb != null) bb.OnClick.Invoke(); else { Log("phantom: no button to click, asking directly"); HwPhantomParade.Request(); }
                } catch (Exception e) { Log($"phantom: click: {e.Message}"); }
                Log($"phantom: after click running {HwPhantomParade.running}, phantoms {HwPhantomParade.phantoms.Count} (alive {PlayerControl.AllPlayerControls.ToArray().Count(HwMechanics.IsAlive)}), refusal '{HwPhantomParade.LastRefusal}'");
            });
            Add(0.6f, () => Shot("phantom_mapbutton_running"));
            Add(0.2f, () => { try { MapBehaviour.Instance.Close(); } catch { } });
            // follow phantom 0 with a real dummy next to it for comparison
            for (int k = 0; k < 3; k++) {
                int kk = k;
                Add(0.1f, () => {
                    var ph = HwPhantomParade.phantoms.Where(p => !p.Gone).ElementAtOrDefault(kk);
                    if (ph == null) return;
                    SnapFeet(lp, ph.Pos + new Vector2(-1.6f, -0.9f));
                    d ??= Dummies(lp).FirstOrDefault();
                    if (d != null) SnapFeet(d, ph.Pos + new Vector2(1.2f, 0f));
                });
                Add(1.1f, () => {
                    var ph = HwPhantomParade.phantoms.Where(p => !p.Gone).ElementAtOrDefault(kk);
                    Log($"phantom: follow {kk}: at ({ph?.Pos.x:F2}, {ph?.Pos.y:F2}) moving {ph?.Moving}, copy of {ph?.Copy}, visual {ph?.Go != null}");
                    Shot($"phantom_walk_{kk}");
                });
            }
            // walking for a while: positions change
            Vector2 p0 = default;
            Add(0.1f, () => { var ph = HwPhantomParade.phantoms.FirstOrDefault(p => !p.Gone); if (ph != null) p0 = ph.Pos; });
            Add(2.0f, () => { var ph = HwPhantomParade.phantoms.FirstOrDefault(p => !p.Gone); Log($"phantom: moved {(ph != null ? (ph.Pos - p0).magnitude : -1f):F2} u in 2 s"); });
            // the touch: step onto a phantom
            int before = 0;
            Add(0.1f, () => {
                before = HwPhantomParade.DiagDissolved;
                var ph = HwPhantomParade.phantoms.FirstOrDefault(p => !p.Gone);
                if (ph != null) SnapFeet(lp, ph.Pos + new Vector2(1.2f, 0f));
            });
            Add(0.5f, () => {
                var ph = HwPhantomParade.phantoms.FirstOrDefault(p => !p.Gone);
                if (ph != null) SnapFeet(lp, ph.Pos);
            });
            Add(0.2f, () => Shot("phantom_mist"));
            Add(0.3f, () => { Log($"phantom: touched -> dissolved {HwPhantomParade.DiagDissolved - before} (want 1)"); Shot("phantom_after_touch"); });
            Add(0.2f, () => { HwPhantomParade.OnMeeting(); Log($"phantom: meeting ends it: running {HwPhantomParade.running}, left {HwPhantomParade.phantoms.Count}"); });
            Add(0.2f, () => { Log($"phantom: second request (uses 1): {HwPhantomParade.HostRequest(lp)} '{HwPhantomParade.LastRefusal}'"); HwPhantomParade.DiagForce = false; });
        }
    }
}
