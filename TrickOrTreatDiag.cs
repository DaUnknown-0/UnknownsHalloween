// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Self test of Trick or Treat (only with the environment variable UC_HALLOWEEN_DIAG=candy).
 *
 * Needs a freeplay round that starts on its own (Unknown's Atlas ForceMap = vanilla:Skeld). Then: candies are
 * scattered, the player walks up to one and eats it with the Use button, all twelve kinds are laid out for a
 * picture, and every effect is forced once with log lines (speed measured by walking, vision radius, shield
 * results, task counts, emergencies) and screenshots of the visible ones into <game>\UCShots\candy\.
 * Ends with "[Halloween/Treats] diag: all done" and quits. Nothing here runs without the variable.
 *
 * UC_HALLOWEEN_DIAG=cabinets: the cabinets on the own maps (Atlas ForceMap = museum, villa ...; on Skeld the
 * candies have to stay on the floor). Placement log, an overview, SEARCH on the button, progress, an empty and a
 * full cabinet, break-offs (moving, letting go), host refusals, the redistribution after a meeting and the Midnight
 * Bonbon from a cabinet. Screenshots into <game>\UCShots\cabinets\.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using TheOtherRoles;

namespace UnknownsHalloween {
    internal static class TrickOrTreatDiag {
        private static readonly string Mode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        internal static readonly bool Cabinets = Mode == "cabinets";
        internal static readonly bool On = Mode == "candy" || Cabinets;
        private const string P = TrickOrTreat.LogPrefix + " diag:";

        private static List<(float wait, Action act)> steps;
        private static int step;
        private static float at = -1f, roundSeen = -1f;
        private static string dir;
        private static float walk;

        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{P} {s}");

        internal static void DriveWalk(PlayerPhysics ph) {
            if (!On || walk == 0f || ph.body == null) return;
            ph.body.velocity = new Vector2(walk * ph.TrueSpeed, 0f);
        }

        internal static void Tick() {
            if (!On) return;
            try {
                var lp = PlayerControl.LocalPlayer;
                bool round = ShipStatus.Instance != null && lp != null && AmongUsClient.Instance != null
                    && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay;
                if (!round) return;
                if (steps == null) {
                    if (roundSeen < 0f) roundSeen = Time.time;
                    if (Time.time - roundSeen < 4f) return;
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
            try { ScreenCapture.CaptureScreenshot(Path.Combine(dir, name + ".png")); } catch (Exception e) { Log($"shot {name}: {e.Message}"); }
        }

        private static void ClearLocal() {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null) return;
            foreach (var a in TrickOrTreat.List(lp.PlayerId).ToList()) TrickOrTreat.End(a, "diag");
        }

        private static float Radius(PlayerControl lp) {
            try { return ShipStatus.Instance.CalculateLightRadius(lp.Data); } catch { return -1f; }
        }

        private static PlayerControl Dummy(PlayerControl lp) =>
            PlayerControl.AllPlayerControls.ToArray().FirstOrDefault(p => p != null && p != lp && TrickOrTreat.IsAlive(p));

        private static int PoisonCount() => TrickOrTreat.candies.Count(c => c.Kind == TrickOrTreat.PoisonKind);

        private static string Snake(string n) => new string(n.ToLowerInvariant().Select(ch => char.IsLetterOrDigit(ch) ? ch : '_').ToArray());

        private static string J(string s) {
            if (s == null) return "null";
            var sb = new System.Text.StringBuilder("\"");
            foreach (char ch in s) {
                if (ch == '"' || ch == '\\') sb.Append('\\').Append(ch);
                else if (ch == '\n') sb.Append("\\n");
                else if (ch < 32) sb.Append(' ');
                else sb.Append(ch);
            }
            return sb.Append('"').ToString();
        }

        private static string Category(Treat fx) {
            var c = TreatFx.Tint(fx);
            if (c.g > 0.9f && c.r < 0.7f) return "good";
            if (c.r > 0.9f && c.g < 0.6f) return "bad";
            return "odd";
        }

        private static void ExportKinds() {
            try {
                var kd = Path.Combine(dir, "kinds");
                Directory.CreateDirectory(kd);
                for (int k = 0; k <= TrickOrTreat.KindCount; k++) {
                    // the delivered picture as it is embedded; the DXT texture has no CPU copy to encode
                    var png = TreatFx.ReadTreatRes(TreatFx.KindFile(k)) ?? ImageConversion.EncodeToPNG(TreatFx.KindTexture(k)).ToArray();
                    File.WriteAllBytes(Path.Combine(kd, Snake(TrickOrTreat.KindNames[k]) + ".png"), png);
                }
                var sb = new System.Text.StringBuilder();
                sb.Append("{\n  \"note\": \"texts as shown on the eater's card; 'until the next meeting' follows the menu setting (here 1 meeting)\",\n  \"effects\": [\n");
                for (int i = 0; i < (int)Treat.Count; i++) {
                    var fx = (Treat)i;
                    string Txt(bool imp, bool de) { TrickOrTreat.LangOverride = de; try { return TreatFx.Line(fx, imp, byte.MaxValue); } finally { TrickOrTreat.LangOverride = null; } }
                    string ce = Txt(false, false), cd = Txt(false, true), ie = Txt(true, false), idd = Txt(true, true);
                    sb.Append($"    {{ \"id\": {i}, \"key\": {J(fx.ToString())}, \"name\": {J(TreatFx.Name(fx))}, \"category\": {J(Category(fx))}, "
                        + $"\"crew\": {{ \"en\": {J(ce)}, \"de\": {J(cd)} }}, \"impostor\": {(ie == ce && idd == cd ? "null" : $"{{ \"en\": {J(ie)}, \"de\": {J(idd)} }}")} }},\n");
                }
                sb.Append($"    {{ \"id\": {TrickOrTreat.FxPoison}, \"key\": \"MidnightBonbon\", \"name\": \"Midnight Bonbon\", \"category\": \"deadly\", "
                    + $"\"crew\": {{ \"en\": {J(TreatFx.PoisonLine(false))}, \"de\": {J(TreatFx.PoisonLine(true))} }}, \"impostor\": null }}\n  ],\n  \"kinds\": [\n");
                for (int k = 0; k <= TrickOrTreat.KindCount; k++)
                    sb.Append($"    {{ \"id\": {k}, \"name\": {J(TrickOrTreat.KindNames[k])}, \"file\": {J(Snake(TrickOrTreat.KindNames[k]) + ".png")}, \"fixed\": {(k == TrickOrTreat.PoisonKind ? "true" : "false")}, \"effect\": {(k == TrickOrTreat.PoisonKind ? "\"deadly\"" : "\"drawn each round\"")} }}{(k < TrickOrTreat.KindCount ? "," : "")}\n");
                sb.Append("  ]\n}\n");
                File.WriteAllText(Path.Combine(kd, "effects.json"), sb.ToString(), new System.Text.UTF8Encoding(false));
                Log($"exported {TrickOrTreat.KindCount + 1} kind drawings and effects.json to {kd}");
            } catch (Exception e) { Log($"export failed: {e}"); }
        }

        private static void Build(PlayerControl lp) {
            if (Cabinets) { BuildCabinets(lp); return; }
            dir = Path.Combine(BepInEx.Paths.GameRootPath, "UCShots", "candy");
            Directory.CreateDirectory(dir);
            var s = new List<(float, Action)>();
            void Add(float w, Action a) => s.Add((w, a));
            Vector2 home = lp.GetTruePosition();
            float x0 = 0f;

            // the drawings of all 13 kinds as PNG plus every card text as JSON (for the docs)
            Add(0f, () => ExportKinds());
            // the menu: open, flip a few switches, check that a round only uses what is on
            Add(0.2f, () => { Log($"menu: rules {TreatSettings.Current}, can edit {TreatSettings.CanEdit()}"); TreatMenu.Open(); });
            Add(0.8f, () => { Log($"menu open {TreatMenu.IsOpen}"); Shot("menu_open"); });
            Add(0.2f, () => {
                var r = TreatSettings.Current;
                r.Enabled = true;
                r.Count = 9;
                r.Kinds = (1u << 0) | (1u << 4) | (1u << 10);
                r.Effects = (1u << (int)Treat.SugarRush) | (1u << (int)Treat.NightOwl);
                TreatSettings.Changed();
                TreatMenu.RefreshIfOpen();
                Log($"menu changed: {TreatSettings.Current}");
            });
            Add(0.6f, () => Shot("menu_changed"));
            Add(0.2f, () => {
                TreatMenu.Close();
                TrickOrTreat.HostSpawn();
                var r = TreatSettings.Current;
                var normal = TrickOrTreat.candies.Where(c => c.Kind != TrickOrTreat.PoisonKind).ToList();
                bool kindsOk = normal.All(c => (r.Kinds & (1u << c.Kind)) != 0);
                bool fxOk = normal.All(c => (r.Effects & (1u << (int)TrickOrTreat.EffectOf(c.Kind))) != 0);
                Log($"rules check: {normal.Count} candies (want 9) + {PoisonCount()} deadly (want 1), kinds only active {kindsOk}, effects only active {fxOk}: "
                    + string.Join(" ", normal.Select(c => TrickOrTreat.KindNames[c.Kind] + "=" + TrickOrTreat.EffectOf(c.Kind))));
                r.Kinds = TreatSettings.AllKinds;
                r.Effects = TreatSettings.AllEffects;
                r.Count = 6;
                TreatSettings.Changed();
                TrickOrTreat.candies.Clear();
                TreatFx.RebuildCandies();
            });
            Add(0.3f, () => {
                Log($"start, host {TrickOrTreat.AmHost()}, players {PlayerControl.AllPlayerControls.Count}, map {ShipStatus.Instance.name}");
                TrickOrTreat.HostSpawn();
                Log($"spawned {TrickOrTreat.candies.Count} candies, part {TrickOrTreat.phase}, deadly {PoisonCount()}");
            });
            // walk up to the first candy, the Use button should offer EAT
            Add(1.0f, () => {
                var c = TrickOrTreat.candies.FirstOrDefault(k => k.Kind != TrickOrTreat.PoisonKind);
                if (c != null) lp.NetTransform.SnapTo(c.Pos + new Vector2(0.45f, 0.05f));
            });
            Add(1.2f, () => { Log($"near candy: use button owned {TreatUse.Owned}, label '{TreatUse.Label}'"); Shot("candy_near"); });
            Add(0.1f, () => { TreatUse.OnClick(); Log($"after click: eaten {TrickOrTreat.candies.Count(c => c.Eaten)}, state {TrickOrTreat.DiagState()}"); });
            Add(0.5f, () => Shot("candy_card"));
            // all twelve kinds in a row, for the picture
            Add(0.3f, () => {
                lp.NetTransform.SnapTo(home);
                ClearLocal();
            });
            Add(0.6f, () => {
                var pos = lp.GetTruePosition();
                TrickOrTreat.candies.Clear();
                for (int k = 0; k <= TrickOrTreat.KindCount; k++)
                    TrickOrTreat.candies.Add(new TrickOrTreat.Candy { Index = (byte)(100 + k), Kind = (byte)k,
                        Pos = k == TrickOrTreat.PoisonKind ? pos + new Vector2(3.2f, 0.1f) : pos + new Vector2(-2.2f + (k % 6) * 0.88f, (k < 6 ? 1.1f : -0.9f)) });
                TreatFx.RebuildCandies();
            });
            Add(0.8f, () => Shot("candy_kinds"));
            Add(0.1f, () => { TrickOrTreat.candies.Clear(); TreatFx.RebuildCandies(); });

            // speed: one second of walking without and with Sugar Rush
            Add(0.3f, () => { x0 = lp.transform.position.x; walk = 1f; });
            Add(1.0f, () => { walk = 0f; Log(FormattableString.Invariant($"walk plain: {lp.transform.position.x - x0:F2}")); });
            Add(0.4f, () => { TrickOrTreat.DiagEat(Treat.SugarRush); x0 = lp.transform.position.x; walk = -1f; });
            Add(1.0f, () => { walk = 0f; Log(FormattableString.Invariant($"walk sugar rush: {x0 - lp.transform.position.x:F2}, mult {TrickOrTreat.SpeedMult(lp.PlayerId):F2}")); ClearLocal(); });
            Add(0.2f, () => { foreach (var fx in new[] { Treat.CinnamonStick, Treat.RockCandy, Treat.HardCandy, Treat.Brittle, Treat.Nausea, Treat.ShrinkSherbet, Treat.BigBite }) { TrickOrTreat.DiagEat(fx); Log(FormattableString.Invariant($"speed {fx}: {TrickOrTreat.SpeedMult(lp.PlayerId):F3}")); ClearLocal(); } });

            // vision
            Add(0.3f, () => {
                float b = Radius(lp);
                foreach (var fx in new[] { Treat.NightOwl, Treat.FogFudge, Treat.Brittle, Treat.LightsOut }) {
                    TrickOrTreat.DiagEat(fx);
                    Log(FormattableString.Invariant($"vision {fx}: {Radius(lp):F2} (base {b:F2})"));
                    ClearLocal();
                }
            });

            // shields
            Add(0.3f, () => {
                var d = Dummy(lp);
                if (d == null) { Log("no dummy for the shield test"); return; }
                TrickOrTreat.DiagEat(Treat.IronTaffy);
                var r1 = Helpers.checkMuderAttempt(d, lp);
                var r2 = Helpers.checkMuderAttempt(d, lp);
                Log($"iron taffy (crew): first {r1}, second {r2}");
                TrickOrTreat.DiagEat(Treat.HardCandy);
                var r3 = Helpers.checkMuderAttempt(d, lp);
                var r4 = Helpers.checkMuderAttempt(d, lp);
                Log($"hard candy: first {r3}, second {r4}, state {TrickOrTreat.DiagState()}");
                ClearLocal();
            });
            Add(0.6f, () => Shot("candy_shield_card"));

            // Butterfingers: a console of one of my tasks
            Add(0.3f, () => {
                try {
                    Console con = null;
                    foreach (var c in UnityEngine.Object.FindObjectsOfType<Console>()) {
                        var t = c.FindTask(lp);
                        if (t != null && t.TryCast<NormalPlayerTask>() != null) { con = c; break; }
                    }
                    if (con == null) { Log("butterfingers: no task console found"); return; }
                    var pos = lp.transform.position;
                    lp.NetTransform.SnapTo(con.transform.position);
                    con.CanUse(lp.Data, out bool u1, out bool c1);
                    TrickOrTreat.DiagEat(Treat.Butterfingers);
                    con.CanUse(lp.Data, out bool u2, out bool c2);
                    Log($"butterfingers: console {con.name} before canUse {u1}/couldUse {c1}, after {u2}/{c2}");
                    ClearLocal();
                    lp.NetTransform.SnapTo(home);
                } catch (Exception e) { Log($"butterfingers failed: {e.Message}"); }
            });

            // tasks and emergencies
            int open0 = 0;
            Add(0.5f, () => { open0 = TrickOrTreat.OpenTasks(lp).Count; Log($"tasks open {open0} of {lp.myTasks.Count}"); TrickOrTreat.DiagEat(Treat.ShortcutCaramel); });
            Add(0.6f, () => { Log($"after shortcut caramel: open {TrickOrTreat.OpenTasks(lp).Count}"); TrickOrTreat.DiagEat(Treat.PrizeInside); });
            Add(0.6f, () => { Log($"after prize inside: open {TrickOrTreat.OpenTasks(lp).Count}, steps {string.Join(",", TrickOrTreat.OpenTasks(lp).Select(t => t.TaskStep + "/" + t.MaxStep))}"); TrickOrTreat.DiagEat(Treat.ExtraChore); });
            Add(2.0f, () => { Log($"after extra chore: tasks {lp.myTasks.Count}, data {lp.Data.Tasks.Count}, open {TrickOrTreat.OpenTasks(lp).Count}"); });
            Add(0.3f, () => {
                int e0 = lp.RemainingEmergencies;
                TrickOrTreat.DiagEat(Treat.LuckyLolly);
                int e1 = lp.RemainingEmergencies;
                TrickOrTreat.DiagEat(Treat.Gobstopper);
                int e2 = lp.RemainingEmergencies;
                Log($"emergencies: start {e0}, lucky lolly {e1}, gobstopper {e2}");
            });
            Add(0.2f, () => { TrickOrTreat.DiagMeeting(); Log($"after a meeting: emergencies {lp.RemainingEmergencies}, state '{TrickOrTreat.DiagState()}'"); });
            Add(1.0f, () => Log($"respawned after the meeting: part {TrickOrTreat.phase}, {TrickOrTreat.candies.Count} candies, deadly {PoisonCount()}"));
            // a dummy eats the Midnight Bonbon: dead, body on the spot
            PlayerControl victim = null;
            Vector2 victimAt = default;
            Add(0.3f, () => {
                var c = TrickOrTreat.candies.FirstOrDefault(k => k.Kind == TrickOrTreat.PoisonKind && !k.Eaten);
                victim = PlayerControl.AllPlayerControls.ToArray().LastOrDefault(p => p != null && p != lp && TrickOrTreat.IsAlive(p));
                if (c == null || victim == null) { Log($"poison test: candy {c != null}, dummy {victim != null}"); return; }
                victimAt = c.Pos;
                victim.NetTransform.SnapTo(c.Pos);
                lp.NetTransform.SnapTo(c.Pos + new Vector2(1.4f, 0.2f));
            });
            Add(0.6f, () => {
                var c = TrickOrTreat.candies.FirstOrDefault(k => k.Kind == TrickOrTreat.PoisonKind && !k.Eaten);
                if (c == null || victim == null) return;
                Shot("poison_before");
                TrickOrTreat.HostPoison(victim, TrickOrTreat.phase, c.Index);
            });
            Add(1.2f, () => {
                if (victim == null) return;
                var body = UnityEngine.Object.FindObjectsOfType<DeadBody>().FirstOrDefault(b => b != null && b.ParentId == victim.PlayerId);
                Log(FormattableString.Invariant($"poison test: dummy dead {victim.Data.IsDead}, body {(body != null ? $"at {body.transform.position.x:F1},{body.transform.position.y:F1} (ate at {victimAt.x:F1},{victimAt.y:F1})" : "missing")}, candy eaten {TrickOrTreat.candies.Count(k => k.Kind == TrickOrTreat.PoisonKind && k.Eaten)}"));
                Shot("poison_body");
            });

            // the effects with a picture
            void Visual(Treat fx, float wait, string shot, float shot2 = -1f) {
                Add(0.4f, () => { ClearLocal(); TrickOrTreat.DiagEat(fx); Log($"{fx}: state {TrickOrTreat.DiagState()}"); });
                Add(wait, () => Shot(shot));
                if (shot2 > 0f) Add(shot2, () => Shot(shot + "_b"));
            }
            Add(0.2f, () => { lp.NetTransform.SnapTo(home); var d = Dummy(lp); if (d != null) d.NetTransform.SnapTo(home + new Vector2(1.3f, 0f)); });
            Visual(Treat.Glowing, 0.8f, "fx_glowing");
            Visual(Treat.CrowCompany, 0.8f, "fx_crows", 0.35f);
            Visual(Treat.EchoDrop, 0.6f, "fx_echo");
            Visual(Treat.Jinkies, 0.8f, "fx_jinkies");
            Visual(Treat.Nausea, 1.3f, "fx_nausea");
            Visual(Treat.LightsOut, 1.2f, "fx_lightsout");
            Visual(Treat.FogFudge, 1.2f, "fx_fog");
            Visual(Treat.NothingQ, 2.6f, "fx_nothing", 0.5f);
            Add(0.1f, () => Log($"nothing? task line: {TreatFx.FakeTaskLine()}"));
            Visual(Treat.SwapSweet, 0.8f, "fx_swap");
            Visual(Treat.ShrinkSherbet, 0.6f, "fx_shrink");
            Add(0.1f, () => Log(FormattableString.Invariant($"shrink scale {lp.transform.localScale.x:F3}")));
            Visual(Treat.BigBite, 0.6f, "fx_bigbite");
            Add(0.1f, () => Log(FormattableString.Invariant($"big bite scale {lp.transform.localScale.x:F3}")));
            Add(0.3f, () => { ClearLocal(); Log(FormattableString.Invariant($"size back {lp.transform.localScale.x:F3}")); TrickOrTreat.DiagEat(Treat.Earmuffs); Log(FormattableString.Invariant($"earmuffs: listener volume {AudioListener.volume:F2}")); });
            Add(0.3f, () => { ClearLocal(); Log(FormattableString.Invariant($"earmuffs over: listener volume {AudioListener.volume:F2}")); TrickOrTreat.DiagEat(Treat.Hiccups); });
            Add(1.6f, () => { ClearLocal(); });
            // Guiding Mint: nothing to find, then a body
            Visual(Treat.GuidingMint, 0.6f, "fx_mint_none");
            Add(0.3f, () => {
                var d = Dummy(lp);
                if (d == null) return;
                d.NetTransform.SnapTo(home + new Vector2(-7f, -1f));
            });
            Add(0.4f, () => { var d = Dummy(lp); if (d != null) d.MurderPlayer(d, MurderResultFlags.Succeeded); });
            Visual(Treat.GuidingMint, 0.8f, "fx_mint_body");
            // Regurgitate, Volatile Starlight
            Add(0.4f, () => {
                ClearLocal();
                TrickOrTreat.DiagEat(Treat.NightOwl);
                string before = TrickOrTreat.DiagState();
                TrickOrTreat.DiagEat(Treat.Regurgitate);
                Log($"regurgitate: before '{before}', after '{TrickOrTreat.DiagState()}'");
            });
            Add(0.6f, () => Shot("fx_regurgitate"));
            Add(0.3f, () => { ClearLocal(); TrickOrTreat.DiagEat(Treat.VolatileStarlight); Log($"volatile: state '{TrickOrTreat.DiagState()}'"); });
            Add(0.6f, () => Shot("fx_volatile"));
            // a whole-round effect ends with the meeting, a dead eater loses his effects
            Add(0.3f, () => {
                ClearLocal();
                TrickOrTreat.DiagEat(Treat.CinnamonStick);
                TrickOrTreat.DiagEat(Treat.FogFudge);
                Log($"before meeting: '{TrickOrTreat.DiagState()}'");
                TrickOrTreat.DiagMeeting();
                Log($"after meeting: '{TrickOrTreat.DiagState()}'");
                var d = Dummy(lp);
                if (d != null) {
                    TrickOrTreat.DiagEatAs(d, Treat.CrowCompany);
                    Log($"dummy ate: '{TrickOrTreat.DiagState()}'");
                    d.MurderPlayer(d, MurderResultFlags.Succeeded);
                }
            });
            Add(0.5f, () => Log($"after the dummy died: '{TrickOrTreat.DiagState()}'"));
            // the real path once more: walk to a fresh candy and press E-equivalent
            Add(0.3f, () => {
                var c = TrickOrTreat.candies.FirstOrDefault(k => !k.Eaten);
                if (c != null) lp.NetTransform.SnapTo(c.Pos + new Vector2(-0.4f, 0f));
            });
            Add(1.0f, () => { TreatUse.OnClick(); Log($"second candy: state '{TrickOrTreat.DiagState()}'"); });
            Add(0.6f, () => Shot("candy_card2"));
            // last: the local player eats the Midnight Bonbon and reads the card as a ghost
            Add(0.5f, () => {
                TrickOrTreat.DiagMeeting();
            });
            Add(1.0f, () => {
                var c = TrickOrTreat.candies.FirstOrDefault(k => k.Kind == TrickOrTreat.PoisonKind && !k.Eaten);
                Log($"last spawn: deadly {PoisonCount()}");
                if (c == null) return;
                lp.NetTransform.SnapTo(c.Pos + new Vector2(0.4f, 0f));
            });
            Add(0.8f, () => { Log($"near the bonbon: use button owned {TreatUse.Owned}"); TreatUse.OnClick(); });
            Add(0.8f, () => { Log($"local ate the bonbon: dead {lp.Data.IsDead}"); Shot("poison_self_card"); });
            Add(1.0f, () => Log("all done"));
            Add(0.5f, () => Application.Quit());
            steps = s;
        }

        // ================================================================ cabinets
        private static string Cab(TreatCabinets.Cabinet c) {
            if (c == null) return "none";
            var k = TrickOrTreat.candies.FirstOrDefault(x => x.Cab == c.Index && !x.Eaten);
            return FormattableString.Invariant($"#{c.Index} ({c.Pos.x:F2},{c.Pos.y:F2}) {c.Room} open {c.Open} holds {(k != null ? TrickOrTreat.KindNames[k.Kind] : "nothing")}");
        }

        private static TreatCabinets.Cabinet Holding(Func<TrickOrTreat.Candy, bool> which) {
            foreach (var c in TreatCabinets.cabinets) {
                if (c.Open) continue;
                var k = TrickOrTreat.candies.FirstOrDefault(x => x.Cab == c.Index && !x.Eaten);
                if (which(k)) return c;
            }
            return null;
        }

        private static Action overviewRestore;
        // SnapTo moves the transform; the feet (true position) sit a bit lower
        private static void SnapFeet(PlayerControl lp, Vector2 feet) =>
            lp.NetTransform.SnapTo(feet + ((Vector2)lp.transform.position - lp.GetTruePosition()));
        private static void Overview(string name) {
            var cam = Camera.main;
            if (cam == null) return;
            float size = cam.orthographicSize;
            GameObject shadow = null;
            try { shadow = HudManager.Instance.ShadowQuad != null ? HudManager.Instance.ShadowQuad.gameObject : null; } catch { }
            cam.orthographicSize = size * 3.2f;
            if (shadow != null) shadow.SetActive(false);
            Shot(name);
            overviewRestore = () => { cam.orthographicSize = size; if (shadow != null) shadow.SetActive(true); };
        }

        private static void BuildCabinets(PlayerControl lp) {
            dir = Path.Combine(BepInEx.Paths.GameRootPath, "UCShots", "cabinets");
            Directory.CreateDirectory(dir);
            var s = new List<(float, Action)>();
            void Add(float w, Action a) => s.Add((w, a));
            TreatCabinets.Cabinet E = null, F = null, G = null, P2 = null;
            List<Vector2> before = null;
            string style = TreatCabinets.Style();

            Add(0f, () => {
                var r = TreatSettings.Current;
                r.Enabled = true;
                r.Count = 6;
                r.Poison = true;
                r.Kinds = TreatSettings.AllKinds;
                r.Effects = TreatSettings.AllEffects;
                TreatSettings.Changed();
                Log($"cabinets: map key '{TreatCabinets.MapKey() ?? "null"}', style '{style ?? "none (floor)"}', ship {ShipStatus.Instance.name}");
                foreach (var st in TreatCabinets.Styles) for (int k = 0; k < 3; k++) TreatCabinets.CabSprite(st, k);
                TreatCabinets.SearchIcon();
                Log($"cabinet pictures from files: {TreatCabinets.fromFile.Count}/18, search icon from file {TreatCabinets.SearchIconFromFile}");
                TrickOrTreat.HostSpawn();
                Log($"spawn: {TreatCabinets.cabinets.Count} cabinets, {TrickOrTreat.candies.Count} candies, in cabinets {TrickOrTreat.candies.Count(c => c.Cab != TreatCabinets.None)}, on the floor {TrickOrTreat.candies.Count(c => c.Cab == TreatCabinets.None)}, deadly {PoisonCount()}");
                foreach (var c in TreatCabinets.cabinets) Log("  cabinet " + Cab(c));
            });
            if (style == null) {
                // original map: floor candies as before
                Add(0.5f, () => {
                    // a candy away from consoles (a console in range takes the Use button, as before)
                    var cons = UnityEngine.Object.FindObjectsOfType<Console>().Select(k => (Vector2)k.transform.position).ToList();
                    var c = TrickOrTreat.candies.Where(k => k.Kind != TrickOrTreat.PoisonKind)
                        .OrderByDescending(k => cons.Count == 0 ? 0f : cons.Min(q => (q - k.Pos).sqrMagnitude)).FirstOrDefault();
                    if (c != null) SnapFeet(lp, c.Pos + new Vector2(0.4f, 0f));
                });
                Add(1.2f, () => { Log($"floor candy near: use button owned {TreatUse.Owned}, label '{TreatUse.Label}', cabinets {TreatCabinets.cabinets.Count}"); Shot("floor_candy"); });
                Add(0.5f, () => Overview("floor_overview"));
                Add(0.5f, () => overviewRestore?.Invoke());
                Add(0.5f, () => Log("all done"));
                Add(0.5f, () => Application.Quit());
                steps = s;
                return;
            }
            Add(0.6f, () => Overview("overview"));
            Add(0.6f, () => overviewRestore?.Invoke());
            // an empty cabinet: SEARCH, progress, open + "empty"
            Add(0.3f, () => {
                E = Holding(k => k == null);
                Log("empty cabinet: " + Cab(E));
                if (E != null) SnapFeet(lp, E.Front);
            });
            Add(1.0f, () => { Log($"near: use button owned {TreatUse.Owned}, label '{TreatUse.Label}', target #{TreatCabinets.Target(lp)?.Index}"); Shot("cabinet_near"); });
            Add(0.1f, () => { TreatCabinets.DiagHold = true; TreatCabinets.DiagStart(E); });
            Add(1.0f, () => { Log(FormattableString.Invariant($"searching: progress {TreatCabinets.Progress:F2}, label '{TreatUse.Label}'")); Shot("search_progress"); });
            Add(1.25f, () => { Log($"after 2 s: {Cab(E)}, hint '{TreatFx.HintShown}'"); Shot("cabinet_empty"); TreatCabinets.DiagHold = false; });
            // the host refuses a second search of the open cabinet and a searcher too far away
            Add(0.3f, () => {
                if (E == null) return;
                int eaten = TrickOrTreat.candies.Count(k => k.Eaten);
                TreatCabinets.HostSearch(lp, TrickOrTreat.phase, E.Index);
                var far = TreatCabinets.cabinets.Where(c => !c.Open).OrderByDescending(c => (c.Pos - lp.GetTruePosition()).sqrMagnitude).FirstOrDefault();
                if (far != null) TreatCabinets.HostSearch(lp, TrickOrTreat.phase, far.Index);
                Log($"refusals: twice -> eaten {TrickOrTreat.candies.Count(k => k.Eaten)} (was {eaten}), far cabinet -> {Cab(far)}");
            });
            // break-offs: moving, letting go
            Add(0.3f, () => {
                F = Holding(k => k == null) ?? Holding(k => k != null && k.Kind != TrickOrTreat.PoisonKind);
                Log("break-off cabinet: " + Cab(F));
                if (F != null) SnapFeet(lp, F.Front);
            });
            Add(1.0f, () => { TreatCabinets.DiagHold = true; TreatCabinets.DiagStart(F); });
            Add(0.7f, () => { if (F != null) SnapFeet(lp, F.Front + new Vector2(0.4f, 0f)); });
            Add(0.3f, () => Log($"moved: searching {TreatCabinets.Searching}, broken off '{TreatCabinets.LastCancel}', {Cab(F)}"));
            Add(0.2f, () => { if (F != null) SnapFeet(lp, F.Front); });
            Add(0.8f, () => TreatCabinets.DiagStart(F));
            Add(0.6f, () => TreatCabinets.DiagHold = false);
            Add(0.2f, () => Log($"let go: searching {TreatCabinets.Searching}, broken off '{TreatCabinets.LastCancel}', {Cab(F)}"));
            // a full cabinet: the card
            Add(0.3f, () => {
                G = Holding(k => k != null && k.Kind != TrickOrTreat.PoisonKind);
                Log("full cabinet: " + Cab(G));
                if (G != null) SnapFeet(lp, G.Front);
            });
            Add(1.0f, () => { TreatCabinets.DiagHold = true; TreatCabinets.DiagStart(G); });
            Add(1.0f, () => Shot("search_progress_full"));
            Add(1.3f, () => { Log($"found: {Cab(G)}, eaten {TrickOrTreat.candies.Count(k => k.Eaten)}, state '{TrickOrTreat.DiagState()}'"); Shot("cabinet_found"); TreatCabinets.DiagHold = false; });
            Add(0.8f, () => Shot("cabinet_open"));
            // the meeting: same cabinets, all closed, new contents
            Add(0.3f, () => {
                before = TreatCabinets.cabinets.Select(c => c.Pos).ToList();
                Log("contents before: " + string.Join(" ", TrickOrTreat.candies.Where(k => k.Cab != TreatCabinets.None).Select(k => $"{k.Cab}={TrickOrTreat.KindNames[k.Kind]}{(k.Eaten ? "(eaten)" : "")}"))
                    + $", open {TreatCabinets.cabinets.Count(c => c.Open)}");
                TrickOrTreat.DiagMeeting();
            });
            Add(1.0f, () => {
                var now = TreatCabinets.cabinets.Select(c => c.Pos).ToList();
                bool same = before != null && before.Count == now.Count && before.Zip(now, (a, b) => (a - b).sqrMagnitude < 0.0001f).All(x => x);
                Log($"after the meeting: part {TrickOrTreat.phase}, same cabinets {same} ({now.Count}), open {TreatCabinets.cabinets.Count(c => c.Open)}, contents: "
                    + string.Join(" ", TrickOrTreat.candies.Where(k => k.Cab != TreatCabinets.None).Select(k => $"{k.Cab}={TrickOrTreat.KindNames[k.Kind]}")));
                if (E != null) SnapFeet(lp, E.Front);
            });
            Add(1.0f, () => Shot("after_meeting"));
            // the Midnight Bonbon from a cabinet, then a ghost cannot search
            Add(0.3f, () => {
                P2 = Holding(k => k != null && k.Kind == TrickOrTreat.PoisonKind);
                Log("deadly cabinet: " + Cab(P2));
                if (P2 != null) SnapFeet(lp, P2.Front);
            });
            Add(1.0f, () => { if (P2 != null) Log(FormattableString.Invariant($"at the deadly cabinet: {Vector2.Distance(lp.GetTruePosition(), P2.Pos):F2} away, can move {lp.CanMove}")); TreatCabinets.DiagHold = true; TreatCabinets.DiagStart(P2); });
            Add(2.4f, () => { TreatCabinets.DiagHold = false; Log($"bonbon: dead {lp.Data.IsDead}, {Cab(P2)}"); Shot("cabinet_bonbon"); });
            Add(0.6f, () => {
                var other = TreatCabinets.cabinets.FirstOrDefault(c => !c.Open);
                if (other != null) SnapFeet(lp, other.Front);
            });
            Add(0.8f, () => Log($"ghost near a cabinet: use button owned {TreatUse.Owned}, target {(TreatUse.Owned ? "yes" : "-")}"));
            Add(0.5f, () => Log("all done"));
            Add(0.5f, () => Application.Quit());
            steps = s;
        }
    }
}
