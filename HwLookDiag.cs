// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Self test of the Halloween look (only with UC_HALLOWEEN_DIAG = meeting, ghosts, endscreen or hwlook = all three in
 * this order). Needs a freeplay round that starts on its own (Unknown's Atlas ForceMap = vanilla:<map>).
 * Screenshots go to <game>\UCShots\hwlook\, log lines start with "[Halloween/Look] diag:", the run ends with
 * "diag: all done" and quits.
 *
 *  - meeting:   emergency meeting (decoration), votes for a dummy (ghost tokens), the exile with Confirm Ejects on
 *               (lead + game line), a second meeting and exile with Confirm Ejects off (neutral lead only).
 *  - ghosts:    the local player in the Reaper costume, a dummy in the Pumpkin Head costume dies next to him (alive:
 *               nothing to see), then the local player dies too (both ghosts with their props).
 *  - endscreen: the local player and a dummy in the Vampire costume become impostors, impostor win by kill; on the
 *               end screen the three backdrops one after another.
 */

using System;
using System.Collections;
using System.IO;
using System.Linq;
using AmongUs.GameOptions;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using UnityEngine;
using TheOtherRoles;

namespace UnknownsHalloween {
    internal static class HwLookDiag {
        private static bool running;
        private static float roundSeen = -1f;
        private static string dir;
        private static string Mode => HwLook.DiagMode;
        private static bool Has(string m) => Mode == m || Mode == "hwlook" || (m == "endscreen" && Mode.StartsWith("endscreen"));

        private static void Log(string s) => HwLook.Log("diag: " + s);

        private static void Shot(string name) {
            try { ScreenCapture.CaptureScreenshot(Path.Combine(dir, name + ".png")); Log("shot " + name); }
            catch (Exception e) { Log($"shot {name}: {e.Message}"); }
        }

        private static IEnumerator Wait(float seconds) {
            float until = Time.realtimeSinceStartup + seconds;
            while (Time.realtimeSinceStartup < until) yield return null;
        }

        private static IEnumerator WaitFor(Func<bool> cond, float max) {
            float until = Time.realtimeSinceStartup + max;
            while (Time.realtimeSinceStartup < until) {
                bool ok = false;
                try { ok = cond(); } catch { }
                if (ok) yield break;
                yield return null;
            }
        }

        private static PlayerControl[] Dummies(PlayerControl lp) =>
            PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p != lp && HwMechanics.IsAlive(p)).ToArray();

        private static void Snap(PlayerControl p, Vector2 at) {
            try { p.NetTransform.SnapTo(at); } catch { try { p.transform.position = new Vector3(at.x, at.y, p.transform.position.z); } catch { } }
        }

        private static void Wear(PlayerControl p, string hatName) {
            string id = null;
            try { id = UnknownsCollection.UCHats.HatIdOf(hatName); } catch { }
            if (id == null) { Log($"no hat id for {hatName}"); return; }
            var o = p.Data.DefaultOutfit;
            p.setLook(o.PlayerName, o.ColorId, id, "", "", "");
            Log($"{o.PlayerName} wears {hatName} ({id}) -> key {HalloweenCostumes.CostumeKeyOfHat(id) ?? "null"}");
        }

        internal static void Tick() {
            if (!HwLook.DiagOn || running) return;
            if (!HwMechanics.FreePlay() || ShipStatus.Instance == null || PlayerControl.LocalPlayer == null) return;
            if (roundSeen < 0f) roundSeen = Time.realtimeSinceStartup;
            if (Time.realtimeSinceStartup - roundSeen < 5f) return;
            running = true;
            dir = Path.Combine(BepInEx.Paths.GameRootPath, "UCShots", "hwlook");
            Directory.CreateDirectory(dir);
            HwLook.LangOverride = true;
            Reactor.Utilities.Coroutines.Start(Run());
        }

        private static IEnumerator Run() {
            var lp = PlayerControl.LocalPlayer;
            Log($"start: mode {Mode}, map {ShipStatus.Instance.name}, atlas '{HwMechanics.AtlasMap() ?? "null"}', players {PlayerControl.AllPlayerControls.Count}, costumes {HalloweenCostumes.HatsRegistered}");
            if (Has("meeting")) {
                yield return Meeting(lp, true, "a");
                yield return Meeting(lp, false, "b");
            }
            if (Mode == "guessspell") yield return GuessSpell(lp);
            if (Has("ghosts")) yield return Ghosts(lp);
            if (Has("endscreen")) yield return End(lp);
            yield return Wait(1f);
            Log($"pictures from files: {HwArt.fromFile.Count} ({string.Join(", ", HwArt.fromFile)})");
            Log("all done");
            yield return Wait(0.5f);
            Application.Quit();
        }

        private static string Where(Component c) {
            if (c == null) return "null";
            var p = c.transform.position;
            string b = "";
            var r = c.GetComponent<Renderer>();
            if (r != null) b = $" bounds {r.bounds.min.x:F2}..{r.bounds.max.x:F2} x {r.bounds.min.y:F2}..{r.bounds.max.y:F2}";
            return $"({p.x:F2}, {p.y:F2}, {p.z:F2}){b}";
        }

        // UC_HALLOWEEN_DIAG = guessspell: a meeting, a hit (the local player guesses a dummy right), a misfire (a dummy
        // guesses wrong and dies itself) - HwGuessSpell must play once per shot.
        private static IEnumerator GuessSpell(PlayerControl lp) {
            var d = Dummies(lp);
            if (d.Length < 3) { Log("not enough dummies"); yield break; }
            try { lp.CmdReportDeadBody(null); } catch (Exception e) { Log("report: " + e.Message); }
            yield return WaitFor(() => MeetingHud.Instance != null, 5f);
            yield return WaitFor(() => MeetingHud.Instance.state != MeetingHud.VoteStates.Animating, 12f);
            yield return Wait(1.5f);
            int before = HwGuessSpell.Plays;
            try { RPCProcedure.guesserShoot(lp.PlayerId, d[0].PlayerId, d[0].PlayerId, (byte)RoleId.Crewmate); } catch (Exception e) { Log("hit: " + e.Message); }
            yield return Wait(2.5f);
            Log($"guess spell after the hit: {HwGuessSpell.Plays - before} play(s)");
            Shot("g01_hit");
            try { RPCProcedure.guesserShoot(d[1].PlayerId, d[1].PlayerId, d[2].PlayerId, (byte)RoleId.Sheriff); } catch (Exception e) { Log("misfire: " + e.Message); }
            yield return Wait(2.5f);
            Log($"guess spell after the misfire: {HwGuessSpell.Plays - before} play(s) in total (expected 2)");
        }

        private static IEnumerator Meeting(PlayerControl lp, bool confirm, string tag) {
            try { GameOptionsManager.Instance.CurrentGameOptions.SetBool(BoolOptionNames.ConfirmImpostor, confirm); } catch (Exception e) { Log("confirm: " + e.Message); }
            try { GameManager.Instance.LogicOptions.currentGameOptions.SetBool(BoolOptionNames.ConfirmImpostor, confirm); } catch (Exception e) { Log("confirm (logic): " + e.Message); }
            var dummies = Dummies(lp);
            if (dummies.Length < 2) { Log("not enough dummies for a meeting"); yield break; }
            var target = dummies[0];
            try { lp.CmdReportDeadBody(null); } catch (Exception e) { Log("report: " + e.Message); }
            yield return WaitFor(() => MeetingHud.Instance != null, 5f);
            yield return WaitFor(() => MeetingHud.Instance.state != MeetingHud.VoteStates.Animating, 12f);
            yield return Wait(1.5f);
            var hud = MeetingHud.Instance;
            if (hud == null) { Log("no meeting"); yield break; }
            try {
                var cam = Camera.main;
                Log($"meeting {tag}: decorations {HwLookMeeting.DiagDecorations}, cam ({cam.transform.position.x:F2}, {cam.transform.position.y:F2}, {cam.transform.position.z:F2}) size {cam.orthographicSize:F2} aspect {cam.aspect:F3}");
                Log($"  hud {Where(hud)} glass {Where(hud.Glass)} black {Where(hud.BlackBackground)} title {Where(hud.TitleText)} skip {Where(hud.SkipVoteButton)}");
                var st = hud.playerStates;
                if (st != null && st.Length > 0) Log($"  plate0 {Where(st[0])} bg {Where(st[0].Background)} plateLast {Where(st[st.Length - 1])}");
                try { Log($"  chat {Where(HudManager.Instance.Chat)} chatButton {Where(HudManager.Instance.Chat.chatButton)}"); } catch { }
                var root = hud.transform.Find("HwLookMeeting");
                if (root != null) foreach (var r in root.GetComponentsInChildren<SpriteRenderer>()) Log($"  deco {r.name} {Where(r)}");
            } catch (Exception e) { Log("dump: " + e.Message); }
            Shot($"m01_meeting_{tag}");
            yield return Wait(0.3f);
            // everybody votes for the target, the local player skips
            try {
                var players = PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null && !p.Data.IsDead).ToArray();
                var states = new Il2CppStructArray<MeetingHud.VoterState>(players.Length);
                for (int i = 0; i < players.Length; i++) {
                    var s = new MeetingHud.VoterState();
                    s.VoterId = players[i].PlayerId;
                    s.VotedForId = players[i] == lp ? (byte)253 : target.PlayerId;
                    states[i] = s;
                }
                hud.VotingComplete(states, target.Data, false);
                Log($"voting complete: {players.Length} votes, exiled {target.Data.PlayerName}");
            } catch (Exception e) { Log("voting: " + e); }
            yield return Wait(1.6f);
            Log($"vote ghosts {HwLookMeeting.DiagVoteGhosts}");
            Shot($"m02_results_{tag}");
            yield return WaitFor(() => ExileController.Instance != null, 7f);
            if (ExileController.Instance == null && MeetingHud.Instance != null) {
                Log($"no exile after the results (state {MeetingHud.Instance.state}) - closing the meeting");
                try { MeetingHud.Instance.Close(); } catch (Exception e) { Log("close: " + e.Message); }
                yield return WaitFor(() => ExileController.Instance != null, 6f);
            }
            if (ExileController.Instance == null) {
                Log("still no exile - starting the cutscene by hand");
                try {
                    var ec = UnityEngine.Object.Instantiate(ShipStatus.Instance.ExileCutscenePrefab, HudManager.Instance.transform);
                    ec.transform.localPosition = new Vector3(0f, 0f, -60f);
                    ec.BeginForGameplay(target.Data, false);
                    if (MeetingHud.Instance != null) UnityEngine.Object.Destroy(MeetingHud.Instance.gameObject);
                } catch (Exception e) { Log("manual exile: " + e.Message); }
                yield return WaitFor(() => ExileController.Instance != null, 3f);
            }
            if (ExileController.Instance == null) { Log("no exile"); yield break; }
            yield return Wait(0.4f);
            Log($"exile {tag}: controller {ExileController.Instance.GetIl2CppType().Name}, line \"{ExileController.Instance.completeString}\"");
            yield return Wait(3.2f);
            Shot($"m03_exile_{tag}_{(confirm ? "confirm" : "neutral")}");
            yield return Wait(2.6f);
            Shot($"m04_exile_{tag}_{(confirm ? "confirm" : "neutral")}_later");
            yield return WaitFor(() => ExileController.Instance == null, 12f);
            if (ExileController.Instance != null) {
                Log("exile still up after 12 s - removing it");
                try { UnityEngine.Object.Destroy(ExileController.Instance.gameObject); } catch { }
            }
            yield return Wait(1.5f);
        }

        private static IEnumerator Ghosts(PlayerControl lp) {
            var dummies = Dummies(lp);
            if (dummies.Length < 1) { Log("no dummy for the ghosts"); yield break; }
            var d = dummies[0];
            Wear(lp, "Halloween Reaper");
            Wear(d, "Halloween Pumpkin Head");
            Snap(d, lp.GetTruePosition() + new Vector2(1.3f, 0.1f));
            yield return Wait(1.0f);
            Shot("g00_costumes");
            try { d.MurderPlayer(d, MurderResultFlags.Succeeded); } catch (Exception e) { Log("murder dummy: " + e.Message); }
            yield return Wait(1.2f);
            Log($"dummy dead, local alive: {HwLookGhosts.DiagState()} (want shown 0)");
            Shot("g01_alive_sees_nothing");
            try { lp.MurderPlayer(lp, MurderResultFlags.Succeeded); } catch (Exception e) { Log("murder local: " + e.Message); }
            yield return Wait(2.0f);
            try {
                var hat = d.cosmetics.hat;
                Log($"dead dummy hat: active {hat.gameObject.activeInHierarchy}, front enabled {hat.FrontLayer?.enabled}, alpha {hat.FrontLayer?.color.a:F2}, sprite {hat.FrontLayer?.sprite?.name}, visible {d.Visible}");
            } catch (Exception e) { Log("hat dump: " + e.Message); }
            Log($"both dead: {HwLookGhosts.DiagState()} (want shown 2)");
            Shot("g02_ghosts");
            // move a bit apart and face left: the props follow
            Snap(d, lp.GetTruePosition() + new Vector2(-1.4f, 0.4f));
            yield return Wait(1.0f);
            Shot("g03_ghosts_moved");
        }

        private static IEnumerator End(PlayerControl lp) {
            var dummies = Dummies(lp);
            // Gegenproben zum Absturz beim Spielende (21.10.): setLook mit einem Vanilla-Hut bzw. das Kostuem als echter
            // Outfit-Hut (RpcSetHat) statt ueber setLook.
            if (Mode.StartsWith("endscreen:vanillalook") || Mode.StartsWith("endscreen:outfit")) {
                string hid = null;
                if (Mode.StartsWith("endscreen:outfit")) { try { hid = UnknownsCollection.UCHats.HatIdOf("Halloween Vampire"); } catch { } }
                else {
                    try {
                        foreach (var h in HatManager.Instance.allHats)
                            if (h != null && h.ProdId != null && h.ProdId != "hat_NoHat" && !h.ProdId.Contains("Halloween") && !h.name.Contains("Halloween")) { hid = h.ProdId; break; }
                    } catch (Exception e) { Log("hat list: " + e.Message); }
                }
                Log($"probe {Mode}: hat {hid ?? "null"}");
                var who = Mode.Contains(":self") ? new[] { lp } : Mode.Contains(":dummy") ? new[] { dummies.FirstOrDefault() } : new[] { lp, dummies.FirstOrDefault() };
                foreach (var pc in who) {
                    if (pc == null || hid == null) continue;
                    try {
                        if (Mode.StartsWith("endscreen:outfit")) pc.RpcSetHat(hid);
                        else { var o = pc.Data.DefaultOutfit; pc.setLook(o.PlayerName, o.ColorId, hid, "", "", ""); }
                    } catch (Exception e) { Log("probe wear: " + e.Message); }
                }
                yield return Wait(Mode.EndsWith(":slow") ? 6f : 0.8f);
                Log("ending with HumansByTask (probe)");
                try { GameManager.Instance.RpcEndGame(GameOverReason.HumansByTask, false); } catch (Exception e) { Log("RpcEndGame: " + e.Message); }
                float until2 = Time.realtimeSinceStartup + 15f;
                EndGameManager egm2 = null;
                while (egm2 == null && Time.realtimeSinceStartup < until2) {
                    try { egm2 = UnityEngine.Object.FindObjectOfType<EndGameManager>(); } catch { }
                    yield return null;
                }
                Log(egm2 == null ? "probe: no end screen" : "probe: end screen reached");
                if (egm2 != null) { yield return Wait(2.0f); Shot("probe_end"); }
                yield break;
            }
            bool plain = Mode == "endscreen:plain" || Mode == "endscreen:plaincrew";
            var d = plain ? null : dummies.FirstOrDefault();
            if (plain) Log("plain: no costumes, no roles");
            else if (d != null) {
                Wear(d, "Halloween Vampire");
                if (Mode != "endscreen:costume") try { RoleManager.Instance.SetRole(d, RoleTypes.Impostor); } catch (Exception e) { Log("role dummy: " + e.Message); }
            }
            bool costumeOnly = Mode == "endscreen:costume";
            if (!plain) {
                if (!(lp.Data?.IsDead ?? false)) Wear(lp, "Halloween Ghostface");
                if (!costumeOnly) try { RoleManager.Instance.SetRole(lp, RoleTypes.Impostor); } catch (Exception e) { Log("role local: " + e.Message); }
            }
            yield return Wait(0.8f);
            var reason = costumeOnly || Mode == "endscreen:plaincrew" ? GameOverReason.HumansByTask : GameOverReason.ImpostorByKill;
            Log($"ending with {reason}");
            try { GameManager.Instance.RpcEndGame(reason, false); } catch (Exception e) { Log("RpcEndGame: " + e.Message); }
            EndGameManager egm = null;
            float until = Time.realtimeSinceStartup + 15f;
            while (egm == null && Time.realtimeSinceStartup < until) {
                try { egm = UnityEngine.Object.FindObjectOfType<EndGameManager>(); } catch { }
                yield return null;
            }
            if (egm == null) { Log("no end screen"); yield break; }
            yield return Wait(3.0f);
            try {
                Log($"end screen: real kind {HwLookEndscreen.LastKind} ({HwLookEndscreen.LastInfo}), hidden {HwLookEndscreen.DiagHidden}");
                foreach (var r in egm.GetComponentsInChildren<Renderer>(true))
                    Log($"  r {r.gameObject.name} [{r.GetIl2CppType().Name}] en {r.enabled} act {r.gameObject.activeInHierarchy} {Where(r)}");
                foreach (var pp in egm.GetComponentsInChildren<PoolablePlayer>(true)) {
                    string hat = "-";
                    try { hat = pp.cosmetics.hat.Hat != null ? pp.cosmetics.hat.Hat.name : "-"; } catch { }
                    Log($"  winner {pp.cosmetics.nameText.text.Replace("\n", " / ")} hat {hat} front {pp.cosmetics.hat.FrontLayer?.sprite?.name}");
                }
            } catch (Exception e) { Log("end dump: " + e.Message); }
            Shot("e01_end_real");
            foreach (var k in new[] { HwLookEndscreen.Kind.Crew, HwLookEndscreen.Kind.Neutral, HwLookEndscreen.Kind.Impostor }) {
                yield return Wait(0.5f);
                try { HwLookEndscreen.Apply(egm, k); } catch (Exception e) { Log($"apply {k}: {e.Message}"); }
                yield return Wait(1.8f);
                Shot($"e02_end_{k.ToString().ToLowerInvariant()}");
            }
        }
    }
}
