// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Self test of the lobby games, only with UC_HALLOWEEN_DIAG=carving, boo or lobbygames (both).
 * From the main menu it hosts a local lobby, adds four dummies through TOR Debug Unlock (reflection, F key's
 * SpawnDummy; without that plugin the Boo! part is skipped) and then:
 *   carving: carving window with a drawn face, lanterns with names, the vote with ballots, the result, the crowned
 *            winner lantern;
 *   boo:     a Boo! round with the local player as the first ghost, the BOO! button, every touch, the crown;
 *   then the game is started: the winner pumpkin at the spawn point, Boo! looks and crowns gone.
 * Screenshots into <game>\UCShots\lobbygames\, ends with "[Halloween/Lobby] diag: all done" and quits.
 */

using System;
using System.Collections;
using System.IO;
using System.Linq;
using HarmonyLib;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class LobbyGamesDiag {
        private static readonly string Mode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        internal static readonly bool Active = Mode == "carving" || Mode == "boo" || Mode == "lobbygames" || Mode == "winner";
        private static readonly bool DoWinner = Mode == "winner";
        private static readonly bool DoCarving = Mode == "carving" || Mode == "lobbygames";
        private static readonly bool DoBoo = Mode == "boo" || Mode == "lobbygames";
        internal static bool HoldTimer => Active;
        internal static bool ForceLocalGhost => Active;
        private const string P = LobbyGames.LogPrefix + " diag:";
        private static string dir;
        private static bool started;

        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{P} [{Time.realtimeSinceStartup:F1}] {s}");

        internal static void Tick() { }

        [HarmonyPatch(typeof(MainMenuManager), nameof(MainMenuManager.Start))]
        static class MenuPatch {
            static void Postfix() {
                if (!Active || started) return;
                // AmongUsClient lives across the scene changes (menu, lobby, round), the coroutine with it
                var host = AmongUsClient.Instance;
                if (host == null) { Log("no AmongUsClient"); return; }
                started = true;
                BepInEx.Unity.IL2CPP.Utils.MonoBehaviourExtensions.StartCoroutine(host, Run());
            }
        }

        private static IEnumerator Wait(float s) { float end = Time.realtimeSinceStartup + s; while (Time.realtimeSinceStartup < end) yield return null; }

        private static IEnumerator Shot(string name) {
            yield return new WaitForEndOfFrame();
            try {
                var tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0);
                tex.Apply();
                File.WriteAllBytes(Path.Combine(dir, name + ".png"), ImageConversion.EncodeToPNG(tex));
                UnityEngine.Object.Destroy(tex);
                Log($"screenshot {name}.png");
            } catch (Exception e) { Log($"screenshot {name} failed: {e.Message}"); }
        }

        private static void Snap(PlayerControl p, Vector2 at) {
            try { p.transform.position = new Vector3(at.x, at.y, p.transform.position.z); } catch { }
            try { p.NetTransform.SnapTo(at); } catch { }
        }

        // the camera straight onto a spot (the local player cannot be moved during the lobby walk-in)
        private static void Look(Vector2 at) {
            try {
                var cam = HudManager.Instance.PlayerCam;
                cam.Locked = true;
                cam.transform.position = new Vector3(at.x, at.y, cam.transform.position.z);
            } catch (Exception e) { Log($"look failed: {e.Message}"); }
        }

        private static void Unlook() { try { HudManager.Instance.PlayerCam.Locked = false; } catch { } }

        private static PlayerControl[] Others() =>
            PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p != PlayerControl.LocalPlayer && p.Data != null).ToArray();

        // Self test only: Forgotten Fixes locks the host's lobby until the lobby password is typed (the hash file is
        // fetched online). The test process has no password, so the gate is marked unlocked by reflection; the gate
        // hides its panel and gives the movement back on its next lobby frame.
        private static void UnlockPasswordGate() {
            try {
                var t = AccessTools.TypeByName("UsefulTORStuff.LobbyPasswordGate");
                var prop = t != null ? AccessTools.Property(t, "Unlocked") : null;
                if (prop == null) { Log("no LobbyPasswordGate"); return; }
                prop.SetValue(null, true);
                AppDomain.CurrentDomain.SetData("LobbyPasswordGate.Unlocked", true);
                Log("lobby password gate unlocked for the self test");
            } catch (Exception e) { Log($"gate unlock failed: {e.Message}"); }
        }

        private static bool SpawnDummy() {
            try {
                var t = AccessTools.TypeByName("TOR_DebugUnlock.DebugKeyPatch");
                var m = t != null ? AccessTools.Method(t, "SpawnDummy") : null;
                if (m == null) { Log("TOR Debug Unlock not found: no dummies"); return false; }
                return m.Invoke(null, null) is bool b && b;
            } catch (Exception e) { Log($"dummy spawn failed: {e.Message}"); return false; }
        }

        private static IEnumerator Run() {
            dir = Path.Combine(BepInEx.Paths.GameRootPath, "UCShots", "lobbygames");
            Directory.CreateDirectory(dir);
            Log($"mode {Mode}: waiting for the main menu");
            yield return Wait(8f);
            if (DoWinner) { yield return WinnerFreeplay(); yield return Quit(); yield break; }
            try {
                var host = UnityEngine.Object.FindObjectOfType<HostLocalGameButton>(true);
                if (host == null) Log("no HostLocalGameButton");
                else {
                    for (var tr = host.transform; tr != null; tr = tr.parent) if (!tr.gameObject.activeSelf) tr.gameObject.SetActive(true);
                    host.NetworkMode = NetworkModes.LocalGame;
                    host.OnClick();
                    Log("hosting a local lobby");
                }
            } catch (Exception e) { Log("host failed: " + e.Message); }
            float t0 = Time.realtimeSinceStartup;
            while ((LobbyBehaviour.Instance == null || PlayerControl.LocalPlayer == null) && Time.realtimeSinceStartup - t0 < 60f) yield return null;
            if (LobbyBehaviour.Instance == null) { Log("no lobby after 60 s"); yield return Quit(); yield break; }
            yield return Wait(5f);
            var lp = PlayerControl.LocalPlayer;
            Log($"lobby up: local player {lp.PlayerId} at {lp.transform.position.x:F2},{lp.transform.position.y:F2}, host {LobbyGames.AmHost()}");

            UnlockPasswordGate();
            yield return Wait(1f);
            Log($"after the gate: moveable {lp.moveable}, can move {lp.CanMove}");

            // the debug dummies get the local lobby dropped with "Error" after about 25 s, so only the Boo! part uses them
            int dummies = 0;
            if (DoBoo) for (int i = 0; i < 4; i++) { if (SpawnDummy()) dummies++; yield return Wait(0.6f); }
            yield return Wait(3f);
            string[] names = { "Wednesday", "Morticia", "Gomez", "Pugsley" };
            var others = Others();
            var c = (Vector3)PumpkinCarving.SpawnCenter();
            for (int i = 0; i < others.Length; i++) {
                try { others[i].RpcSetName(names[i % names.Length]); } catch { }
                Snap(others[i], new Vector2(c.x - 2.2f + i * 1.45f, c.y + 0.4f));
            }
            Log($"{dummies} dummies, {others.Length} other players");
            yield return Wait(1f);

            if (DoBoo && others.Length >= 2) yield return Boo(lp, others);
            else if (DoBoo) Log("Boo! skipped: needs dummies");
            if (LobbyBehaviour.Instance == null) { Log("lobby gone after Boo!"); yield return Quit(); yield break; }
            if (DoCarving) yield return Carving(lp, others);
            if (LobbyBehaviour.Instance == null) { Log("lobby gone after carving"); yield return Quit(); yield break; }
            yield return GameStart();
            yield return Quit();
        }

        // a jack-o'-lantern face: triangle eyes, a triangle nose, a toothy grin
        private static void DrawFace() {
            PumpkinCarvingUI.Big = false;
            PumpkinCarvingUI.Mirror = true;
            for (int r = 0; r <= 3; r++)                                   // eyes: triangles, tip up
                for (int col = 7 - r; col <= 7 + r; col++) PumpkinCarvingUI.Stamp(col, 5 + r, false);
            for (int r = 0; r <= 2; r++)                                   // nose
                for (int col = 11 - r; col <= 11; col++) PumpkinCarvingUI.Stamp(col, 11 + r, false);
            for (int col = 3; col <= 11; col++)                            // grin with teeth
                for (int row = 15; row <= 19; row++) {
                    bool tooth = (col % 3 == 0 && row == 15) || (col % 3 == 2 && row == 19);
                    bool corner = col < 5 && row == 19 || col == 3 && row == 18;
                    if (!tooth && !corner) PumpkinCarvingUI.Stamp(col, row, false);
                }
            PumpkinCarvingUI.Mirror = false;
        }

        private static byte[] Pattern(int seed) {
            var b = new byte[PumpkinCarving.Bytes];
            var r = new System.Random(seed);
            // round eyes, a different mouth per dummy
            int ey = 6 + r.Next(3), ex = 6 + r.Next(2), er = 2 + r.Next(2);
            for (int row = 0; row < 24; row++)
                for (int col = 0; col < 24; col++) {
                    float d1 = new Vector2(col - ex, row - ey).magnitude, d2 = new Vector2(col - (23 - ex), row - ey).magnitude;
                    if (d1 <= er || d2 <= er) PumpkinCarving.Set(b, col, row, true);
                    int my = 16 + (int)(Mathf.Sin(col * (0.4f + seed * 0.1f)) * (1 + seed % 3));
                    if (col >= 4 && col <= 19 && row >= my && row <= my + 1 + seed % 2) PumpkinCarving.Set(b, col, row, true);
                }
            return b;
        }

        private static IEnumerator Carving(PlayerControl lp, PlayerControl[] others) {
            LobbyGames.CarvingOn = true;
            LobbyGames.RulesChanged();
            LobbyCards.OpenCarving();
            yield return Wait(1f);
            yield return Shot("carving_card_empty");
            LobbyCards.Close();
            PumpkinCarvingUI.OpenCarve();
            yield return Wait(1.5f);
            DrawFace();
            yield return Wait(2f);
            Log($"carving window open {PumpkinCarvingUI.CarveOpen}, {PumpkinCarving.Count(PumpkinCarvingUI.Bits)} cells carved, moveable {lp.moveable}");
            yield return Shot("carve_window");
            PumpkinCarvingUI.Submit();
            Log($"submitted: faces {PumpkinCarving.Faces.Count}, moveable again {lp.moveable}");
            // without dummies: four stand-in carvers (ids 200-203, names only on this client)
            var carvers = others.Select(o => o.PlayerId).ToList();
            if (carvers.Count == 0) {
                string[] fake = { "Wednesday", "Morticia", "Gomez", "Pugsley" };
                for (int i = 0; i < 4; i++) { byte id = (byte)(200 + i); PumpkinCarving.FakeNames[id] = fake[i]; carvers.Add(id); }
            }
            for (int i = 0; i < carvers.Count; i++) PumpkinCarving.HostStore(carvers[i], Pattern(i + 1));
            yield return Wait(1.5f);
            var spots = PumpkinCarving.LanternSpots(PumpkinCarving.Faces.Count);
            Log("lanterns at " + string.Join("; ", spots.Select(s => $"{s.x:F2},{s.y:F2}")));
            var mid = spots.Aggregate(Vector2.zero, (a, s) => a + s) / spots.Count;
            Snap(lp, mid + new Vector2(0f, 0.9f));
            Look(mid + new Vector2(0f, 0.6f));
            yield return Wait(1.5f);
            Log($"local player now at {lp.transform.position.x:F2},{lp.transform.position.y:F2}, camera at {Camera.main.transform.position.x:F2},{Camera.main.transform.position.y:F2} size {Camera.main.orthographicSize:F2}");
            yield return Shot("lanterns");

            PumpkinCarving.HostStartVote();
            PumpkinCarvingUI.OpenVote();
            yield return Wait(1f);
            PumpkinCarving.CastLocal(carvers[0]);
            for (int i = 0; i < carvers.Count; i++) PumpkinCarving.HostBallot(carvers[i], i == 0 ? lp.PlayerId : carvers[0]);
            yield return Wait(1.5f);
            Log($"vote: {PumpkinCarving.BallotCount} ballots, tally " + string.Join(", ", PumpkinCarving.Tally.Select(kv => $"{LobbyGames.NameOf(kv.Key)}={kv.Value}")));
            yield return Shot("vote");
            PumpkinCarving.HostEndVote(false);
            yield return Wait(1.5f);
            Log($"result: winner {PumpkinCarving.WinnerName} ({PumpkinCarving.WinnerId}), window {PumpkinCarvingUI.VoteOpen}");
            yield return Shot("vote_result");
            PumpkinCarvingUI.CloseVote();
            yield return Wait(1f);
            yield return Shot("lanterns_winner");
            Unlook();
            LobbyCards.OpenCarving();
            yield return Wait(1f);
            yield return Shot("carving_card");
            LobbyCards.Close();
        }

        private static IEnumerator Boo(PlayerControl lp, PlayerControl[] others) {
            var c = (Vector3)PumpkinCarving.SpawnCenter();
            for (int i = 0; i < others.Length; i++) Snap(others[i], new Vector2(c.x - 2.2f + i * 1.45f, c.y + 0.6f));
            Snap(lp, new Vector2(c.x, c.y - 0.3f));
            yield return Wait(1f);
            LobbyCards.OpenBoo();
            yield return Wait(1f);
            yield return Shot("boo_card");
            LobbyCards.Close();
            bool ok = BooTag.HostStart(out var why);
            Log($"Boo! start {ok} {why}; ghosts {string.Join(",", BooTag.Ghosts)}");
            yield return Wait(1.5f);
            Log($"local hat {HatOf(lp)}");
            yield return Shot("boo_start");
            for (int i = 0; i < others.Length; i++) {
                var o = others[i];
                Snap(lp, (Vector2)o.transform.position + new Vector2(-0.55f, 0f));
                yield return Wait(0.8f);
                var target = BooTag.Target();
                Log($"next to {o.Data.PlayerName}: target {(target != null ? target.Data.PlayerName : "-")}, button owned {BooUse.Owned}, label '{(HudManager.InstanceExists ? HudManager.Instance.UseButton.buttonLabelText.text : "")}'");
                if (i == 0) yield return Shot("boo_button");
                if (!BooTag.Running) break;
                BooUse.OnClick();
                yield return Wait(0.2f);
                if (i == 0) yield return Shot("boo_converted");
                yield return Wait(0.8f);
                Log($"after touch: ghosts {BooTag.Ghosts.Count}, phase {BooTag.Phase}, hat of {o.Data.PlayerName}: {HatOf(o)}");
                if (!BooTag.Running) break;
            }
            yield return Wait(1f);
            var crowned = BooTag.Crowned.Select(id => others.FirstOrDefault(p => p.PlayerId == id)).FirstOrDefault(p => p != null);
            if (crowned != null) Snap(lp, (Vector2)crowned.transform.position + new Vector2(-0.9f, -0.3f));
            yield return Wait(1.2f);
            Log($"Boo! phase {BooTag.Phase}, crowned {string.Join(",", BooTag.Crowned.Select(LobbyGames.NameOf))}, local hat {HatOf(lp)}");
            yield return Shot("boo_crown");
        }

        private static string HatOf(PlayerControl p) {
            try { return p.cosmetics.hat.Hat != null ? p.cosmetics.hat.Hat.ProdId : "none"; } catch { return "?"; }
        }

        private static IEnumerator GameStart() {
            Log($"starting the game (winner {PumpkinCarving.WinnerName}, boo phase {BooTag.Phase})");
            try {
                if (GameStartManager.InstanceExists) GameStartManager.Instance.BeginGame();
                else Log("no GameStartManager");
            } catch (Exception e) { Log("BeginGame failed: " + e.Message); }
            float t0 = Time.realtimeSinceStartup;
            while (ShipStatus.Instance == null && Time.realtimeSinceStartup - t0 < 45f) yield return null;
            if (ShipStatus.Instance == null) { Log("no round after 45 s"); yield break; }
            Log($"round: ship {ShipStatus.Instance.name}; boo phase {BooTag.Phase}, ghosts {BooTag.Ghosts.Count}, crowns {BooTag.Crowned.Count}");
            t0 = Time.realtimeSinceStartup;
            while (!PumpkinCarving.WinnerStanding && Time.realtimeSinceStartup - t0 < 25f) yield return null;
            yield return Wait(2f);
            try {
                var lp = PlayerControl.LocalPlayer;
                Log($"winner pumpkin standing {PumpkinCarving.WinnerStanding} at {PumpkinCarving.WinnerPosition()}; local at {lp.transform.position}");
                Log("hats after the start: " + string.Join(", ", PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null).Select(p => $"{p.Data.PlayerName}={HatOf(p)}")));
                if (PumpkinCarving.WinnerStanding) Look((Vector2)PumpkinCarving.WinnerPosition() + new Vector2(0f, 0.3f));
            } catch (Exception e) { Log($"round check failed: {e}"); }
            yield return Wait(1f);
            yield return Shot("winner_spawn");
        }

        // UC_HALLOWEEN_DIAG=winner: a freeplay round (dummies, no instant end) with a vote winner as if the lobby had
        // chosen one, to see the pumpkin at the spawn point.
        private static IEnumerator WinnerFreeplay() {
            try {
                var popover = UnityEngine.Object.FindObjectOfType<FreeplayPopover>(true);
                for (var t = popover.transform; t != null; t = t.parent) if (!t.gameObject.activeSelf) t.gameObject.SetActive(true);
                popover.Show();
                popover.PlayMap(MapNames.Skeld);
                Log("freeplay on the Skeld started");
            } catch (Exception e) { Log($"freeplay failed: {e.Message}"); yield break; }
            float t0 = Time.realtimeSinceStartup;
            while ((ShipStatus.Instance == null || PlayerControl.LocalPlayer == null) && Time.realtimeSinceStartup - t0 < 60f) yield return null;
            yield return Wait(2f);
            // only now: joining the freeplay game clears the session (OnGameJoined)
            PumpkinCarvingUI.Bits = new byte[PumpkinCarving.Bytes];
            DrawFace();
            PumpkinCarving.WinnerFace = (byte[])PumpkinCarvingUI.Bits.Clone();
            PumpkinCarving.WinnerName = "Wednesday";
            PumpkinCarving.WinnerId = 1;
            t0 = Time.realtimeSinceStartup;
            while (!PumpkinCarving.WinnerStanding && Time.realtimeSinceStartup - t0 < 20f) yield return null;
            yield return Wait(3f);
            try {
                var lp = PlayerControl.LocalPlayer;
                Log($"winner pumpkin standing {PumpkinCarving.WinnerStanding} at {PumpkinCarving.WinnerPosition()}, local at {lp.transform.position}");
                Snap(lp, (Vector2)PumpkinCarving.WinnerPosition() + new Vector2(-0.8f, -0.6f));
            } catch (Exception e) { Log($"winner check failed: {e.Message}"); }
            yield return Wait(1.5f);
            yield return Shot("winner_spawn");
        }

        private static IEnumerator Quit() {
            Log("all done");
            yield return Wait(1f);
            Application.Quit();
        }
    }
}
