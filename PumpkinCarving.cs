// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Pumpkin Carving (lobby game, see LobbyGames.cs for the network layout). State, host logic, the lanterns in the
 * lobby and the winner pumpkin at the spawn point; the windows are in PumpkinCarvingUI.cs.
 *
 * A face is a 24x24 bit mask, 72 bytes, bit (row * 24 + col), row 0 at the top, set = carved (glows).
 * The host keeps the faces, sends each one once to everybody and all of them to a joiner (addressed to him),
 * one message every 0.25 s. The lanterns are world objects (layer 11) under the lobby, so they go with it.
 * The vote: 30 s, one vote per player, not for yourself; most votes wins, a tie is drawn by the host. The winner's
 * face travels in the result message, so the pumpkin at the spawn point does not depend on the carver staying.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Hazel;
using UnityEngine;
using UnknownsCollection;

namespace UnknownsHalloween {
    internal static class PumpkinCarving {
        internal const int Grid = 24, Bytes = Grid * Grid / 8;
        internal const float VoteSeconds = 30f;
        internal const byte None = 255;
        internal static readonly Color Lit = new Color(1f, 0.86f, 0.40f);

        internal static bool Get(byte[] bits, int col, int row) {
            if (bits == null || col < 0 || row < 0 || col >= Grid || row >= Grid) return false;
            int i = row * Grid + col;
            return (bits[i >> 3] & (1 << (i & 7))) != 0;
        }

        internal static void Set(byte[] bits, int col, int row, bool on) {
            if (bits == null || col < 0 || row < 0 || col >= Grid || row >= Grid) return;
            int i = row * Grid + col;
            if (on) bits[i >> 3] |= (byte)(1 << (i & 7)); else bits[i >> 3] &= (byte)~(1 << (i & 7));
        }

        internal static int Count(byte[] bits) { int n = 0; if (bits != null) foreach (var b in bits) for (int k = 0; k < 8; k++) n += (b >> k) & 1; return n; }

        // ---- state (same on every client) ----
        internal static readonly Dictionary<byte, byte[]> Faces = new();
        internal static readonly Dictionary<byte, string> FakeNames = new();       // self test only
        internal static int VotePhase;                    // 0 none, 1 open, 2 result
        private static float voteEndsAt;
        internal static readonly Dictionary<byte, int> Tally = new();
        internal static int BallotCount => Tally.Values.Sum();
        internal static byte MyBallot = None;
        internal static byte WinnerId = None;
        internal static byte[] WinnerFace;
        internal static string WinnerName = "";
        private static bool winnerShown;                  // stood at a spawn point: gone when back in the lobby
        internal static int Version;                      // bumps on every change (the windows rebuild on it)

        // ---- host only ----
        private static readonly Dictionary<byte, byte> ballots = new();
        private static readonly List<(int target, byte pid)> queue = new();
        private static readonly Dictionary<byte, float> lastCarve = new();
        private static float nextSend, voteSendAt = -1f;
        private static readonly System.Random rnd = new System.Random();

        internal static int VoteSecondsLeft() => Mathf.Max(0, Mathf.CeilToInt(voteEndsAt - Time.realtimeSinceStartup));

        internal static void Clear() {
            Faces.Clear();
            FakeNames.Clear();
            VotePhase = 0;
            Tally.Clear();
            ballots.Clear();
            queue.Clear();
            lastCarve.Clear();
            MyBallot = None;
            WinnerId = None;
            WinnerFace = null;
            WinnerName = "";
            winnerShown = false;
            voteSendAt = -1f;
            Version++;
            DestroyLanterns();
            DestroyWinner();
            layoutDone = false;
        }

        // ================================================================ network
        private static byte[] ReadFace(MessageReader r) {
            var b = new byte[Bytes];
            for (int i = 0; i < Bytes; i++) b[i] = r.ReadByte();
            return b;
        }

        private static void WriteFace(MessageWriter w, byte[] b) { for (int i = 0; i < Bytes; i++) w.Write(b[i]); }

        internal static void HandleRpc(byte sub, MessageReader r, PlayerControl sender) {
            switch (sub) {
                case LobbyGames.SubCarve: {
                    var bits = ReadFace(r);
                    if (!LobbyGames.AmHost() || sender == null || !LobbyGames.CarvingOn || !LobbyGames.InLobby()) return;
                    float t = Time.realtimeSinceStartup;
                    if (lastCarve.TryGetValue(sender.PlayerId, out float last) && t - last < 3f) return;     // no flooding
                    lastCarve[sender.PlayerId] = t;
                    HostStore(sender.PlayerId, bits);
                    break;
                }
                case LobbyGames.SubFace: {
                    byte pid = r.ReadByte();
                    var bits = ReadFace(r);
                    if (!UCRpc.RequireHost("Carving.Face")) return;
                    Faces[pid] = bits;
                    Changed();
                    break;
                }
                case LobbyGames.SubRemove: {
                    byte pid = r.ReadByte();
                    if (!UCRpc.RequireHost("Carving.Remove")) return;
                    if (Faces.Remove(pid)) Changed();
                    break;
                }
                case LobbyGames.SubVote: {
                    int phase = r.ReadByte(), secs = r.ReadByte(), n = r.ReadByte();
                    var tally = new Dictionary<byte, int>();
                    for (int i = 0; i < n; i++) { byte pid = r.ReadByte(); tally[pid] = r.ReadByte(); }
                    byte winner = None; byte[] face = null; string name = "";
                    if (phase == 2) { winner = r.ReadByte(); face = ReadFace(r); name = r.ReadString(); }
                    if (!UCRpc.RequireHost("Carving.Vote")) return;
                    ApplyVote(phase, secs, tally, winner, face, name);
                    break;
                }
                case LobbyGames.SubBallot: {
                    byte target = r.ReadByte();
                    if (!LobbyGames.AmHost() || sender == null) return;
                    HostBallot(sender.PlayerId, target);
                    break;
                }
            }
        }

        private static void Changed() { Version++; lanternsDirty = true; }

        // ================================================================ carving
        /// <summary>The local player finished a face.</summary>
        internal static void SubmitLocal(byte[] bits) {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || bits == null) return;
            var copy = (byte[])bits.Clone();
            HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} carved a face ({Count(copy)} of {Grid * Grid} cells)");
            if (LobbyGames.AmHost()) { HostStore(lp.PlayerId, copy); return; }
            Faces[lp.PlayerId] = copy;            // shown at once, the host's echo confirms it
            Changed();
            LobbyGames.SendToHost(LobbyGames.SubCarve, w => WriteFace(w, copy));
        }

        internal static void HostStore(byte pid, byte[] bits) {
            Faces[pid] = (byte[])bits.Clone();
            Changed();
            queue.RemoveAll(q => q.pid == pid && q.target < 0);
            queue.Add((-1, pid));
        }

        internal static void HostRemove(byte pid, string why) {
            if (!LobbyGames.CanEdit()) return;
            if (!Faces.Remove(pid)) return;
            HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} pumpkin of {pid} removed ({why})");
            queue.RemoveAll(q => q.pid == pid);
            ballots.Remove(pid);
            foreach (var k in ballots.Where(kv => kv.Value == pid).Select(kv => kv.Key).ToList()) ballots.Remove(k);
            FakeNames.Remove(pid);
            Changed();
            LobbyGames.Send(LobbyGames.SubRemove, w => w.Write(pid));
            if (VotePhase == 1) { Recount(); SendVoteSoon(); }
        }

        internal static void HostDropLeavers() {
            var here = new HashSet<byte>(PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null && !p.Data.Disconnected).Select(p => p.PlayerId));
            foreach (var pid in Faces.Keys.ToList())
                if (!here.Contains(pid) && !FakeNames.ContainsKey(pid)) HostRemove(pid, "left");
        }

        /// <summary>A player joined: every face once, addressed to him, plus the vote state.</summary>
        internal static void QueueAllFor(int clientId) {
            foreach (var pid in Faces.Keys) queue.Add((clientId, pid));
            if (VotePhase != 0) voteSendAt = Time.realtimeSinceStartup + 0.5f + Faces.Count * 0.25f;
        }

        // ================================================================ vote
        internal static bool HostStartVote() {
            if (!LobbyGames.CanEdit() || VotePhase == 1 || Faces.Count < 2) return false;
            VotePhase = 1;
            voteEndsAt = Time.realtimeSinceStartup + VoteSeconds;
            ballots.Clear();
            Tally.Clear();
            MyBallot = None;
            WinnerId = None; WinnerFace = null; WinnerName = ""; winnerShown = false;
            Version++;
            HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} vote started ({Faces.Count} pumpkins)");
            SendVote();
            return true;
        }

        internal static void CastLocal(byte target) {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || VotePhase != 1 || target == lp.PlayerId || !Faces.ContainsKey(target)) return;
            MyBallot = target;
            Version++;
            if (LobbyGames.AmHost()) HostBallot(lp.PlayerId, target);
            else LobbyGames.SendToHost(LobbyGames.SubBallot, w => w.Write(target));
        }

        internal static void HostBallot(byte voter, byte target) {
            if (VotePhase != 1 || voter == target || !Faces.ContainsKey(target)) return;
            ballots[voter] = target;
            Recount();
            SendVoteSoon();
        }

        private static void Recount() {
            Tally.Clear();
            foreach (var t in ballots.Values) Tally[t] = (Tally.TryGetValue(t, out int n) ? n : 0) + 1;
            Version++;
        }

        private static void SendVoteSoon() { if (voteSendAt < 0f) voteSendAt = Time.realtimeSinceStartup + 0.4f; }

        /// <summary>Ends the vote (time up, host button, game start). No vote at all: no winner.</summary>
        internal static void HostEndVote(bool gameStart) {
            if (!LobbyGames.CanEdit() || VotePhase != 1) return;
            Recount();
            byte winner = None;
            if (Tally.Count > 0) {
                int best = Tally.Values.Max();
                var top = Tally.Where(kv => kv.Value == best && Faces.ContainsKey(kv.Key)).Select(kv => kv.Key).ToList();
                if (top.Count > 0) winner = top[rnd.Next(top.Count)];
            }
            if (winner != None) {
                VotePhase = 2;
                WinnerId = winner;
                WinnerFace = (byte[])Faces[winner].Clone();
                WinnerName = LobbyGames.NameOf(winner);
                winnerShown = false;
            } else {
                VotePhase = 0;
            }
            HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} vote over{(gameStart ? " (game start)" : "")}: "
                + (winner != None ? $"winner {WinnerName} ({winner}) with {Tally[winner]} vote(s)" : "no votes, no winner")
                + "; " + string.Join(", ", Tally.Select(kv => $"{kv.Key}={kv.Value}")));
            Version++;
            lanternsDirty = true;
            SendVote();
        }

        private static void SendVote(int target = -1) {
            voteSendAt = -1f;
            int phase = VotePhase, secs = VoteSecondsLeft();
            var tally = Tally.ToList();
            byte winner = WinnerId; var face = WinnerFace; string name = WinnerName ?? "";
            LobbyGames.Send(LobbyGames.SubVote, w => {
                w.Write((byte)phase);
                w.Write((byte)Mathf.Clamp(secs, 0, 255));
                w.Write((byte)tally.Count);
                foreach (var kv in tally) { w.Write(kv.Key); w.Write((byte)Mathf.Clamp(kv.Value, 0, 255)); }
                if (phase == 2) { w.Write(winner); WriteFace(w, face); w.Write(name.Length > 40 ? name.Substring(0, 40) : name); }
            }, target);
        }

        private static void ApplyVote(int phase, int secs, Dictionary<byte, int> tally, byte winner, byte[] face, string name) {
            int before = VotePhase;
            VotePhase = phase;
            voteEndsAt = Time.realtimeSinceStartup + secs;
            Tally.Clear();
            foreach (var kv in tally) Tally[kv.Key] = kv.Value;
            if (phase == 1 && before != 1) MyBallot = None;
            if (phase == 2) { WinnerId = winner; WinnerFace = face; WinnerName = name; winnerShown = false; }
            if (phase == 0) { WinnerId = None; WinnerFace = null; WinnerName = ""; }
            Version++;
            lanternsDirty = true;
            if (phase == 1 && before != 1) PumpkinCarvingUI.OpenVote();          // the vote comes to everybody
            if (phase == 2 && before == 1) PumpkinCarvingUI.ShowResult();
            if (phase == 0) PumpkinCarvingUI.CloseVote();
        }

        // ================================================================ ticks
        internal static void LobbyTick() {
            float t = Time.realtimeSinceStartup;
            if (LobbyGames.AmHost()) {
                if (queue.Count > 0 && t >= nextSend) {
                    nextSend = t + 0.25f;
                    var (target, pid) = queue[0];
                    queue.RemoveAt(0);
                    if (Faces.TryGetValue(pid, out var bits)) {
                        var copy = (byte[])bits.Clone();
                        LobbyGames.Send(LobbyGames.SubFace, w => { w.Write(pid); WriteFace(w, copy); }, target);
                    }
                }
                if (VotePhase == 1) {
                    int voters = PlayerControl.AllPlayerControls.ToArray().Count(p => p != null && p.Data != null && !p.Data.Disconnected && LobbyGames.HasMod(p)
                                                                                   && !(Faces.Count == 1 && Faces.ContainsKey(p.PlayerId)));
                    if (t >= voteEndsAt || (ballots.Count >= voters && voters > 0 && !LobbyGamesDiag.Active)) HostEndVote(false);
                }
                if (voteSendAt > 0f && t >= voteSendAt) SendVote();
            }
            if (lanternsDirty || (lanternRoot == null && Faces.Count > 0)) BuildLanterns();
            Flicker(t);
        }

        /// <summary>Back in the lobby: the winner stood at a spawn point in the round that just ended, so it goes.</summary>
        internal static void LobbyAgain() {
            DestroyWinner();
            if (winnerShown) {
                HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} winner pumpkin of {WinnerName} done (stood one round)");
                WinnerId = None; WinnerFace = null; WinnerName = ""; winnerShown = false;
                if (VotePhase == 2) VotePhase = 0;
                Version++;
            }
            lanternsDirty = true;
        }

        private static bool introDone;
        internal static void RoundTick() {
            var ship = ShipStatus.Instance;
            if (ship == null || PlayerControl.LocalPlayer == null) { introDone = false; DestroyWinner(); return; }
            if (WinnerFace == null) { DestroyWinner(); return; }
            if (winnerObj == null && (introDone || LobbyGames.FreePlay())) SpawnWinner(ship);
            Flicker(Time.realtimeSinceStartup);
        }

        [HarmonyPatch(typeof(IntroCutscene), nameof(IntroCutscene.OnDestroy))]
        static class IntroEndPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix() { introDone = true; }
        }

        // ================================================================ lanterns in the lobby
        private static bool lanternsDirty;
        private static GameObject lanternRoot;
        private sealed class Lamp { public SpriteRenderer Glow, Face; public float Seed; }
        private static readonly List<Lamp> lamps = new();
        private static GameObject winnerObj;
        private static readonly Dictionary<byte, Texture2D> faceTex = new();

        internal const float LanternWidth = 0.62f;

        private static void DestroyLanterns() {
            if (lanternRoot != null) UnityEngine.Object.Destroy(lanternRoot);
            lanternRoot = null;
            lamps.RemoveAll(l => l.Glow == null || l.Glow.transform.parent == null);
        }

        private static void DestroyWinner() {
            if (winnerObj != null) UnityEngine.Object.Destroy(winnerObj);
            winnerObj = null;
        }

        /// <summary>Where the lanterns stand: a row (two when many) in front of the circle the players spawn in.</summary>
        internal static List<Vector2> LanternSpots(int n) {
            var spots = new List<Vector2>();
            if (n <= 0) return spots;
            LobbyLayout(out var center, out float radius, out var room);
            int perRow = Mathf.Min(n, 8);
            float width = Mathf.Min(room.size.x * 0.8f, Mathf.Max(radius * 2f + 1.6f, 4.5f));
            for (int i = 0; i < n; i++) {
                int row = i / perRow, col = i % perRow;
                int inRow = Mathf.Min(perRow, n - row * perRow);
                float step = inRow > 1 ? Mathf.Min(0.95f, width / (inRow - 1)) : 0f;
                float x = center.x + (col - (inRow - 1) / 2f) * step;
                float y = center.y - radius - 0.75f - row * 0.85f;
                y = Mathf.Max(y, room.min.y + 0.6f);                     // stay inside the walls
                spots.Add(new Vector2(x, y));
            }
            return spots;
        }

        private static bool layoutDone;
        private static Vector2 spawnCenter;
        private static float spawnRadius;
        private static Bounds roomBounds;

        /// <summary>The spawn circle (LobbyBehaviour.SpawnPositions) and the room inside the lobby's wall colliders.</summary>
        internal static void LobbyLayout(out Vector2 center, out float radius, out Bounds room) {
            var lobby = LobbyBehaviour.Instance;
            if (!layoutDone && lobby != null) {
                layoutDone = true;
                spawnCenter = Vector2.zero; spawnRadius = 1.2f;
                roomBounds = new Bounds(Vector3.zero, new Vector3(8f, 5f, 0f));
                try {
                    var sp = lobby.SpawnPositions;
                    if (sp != null && sp.Length > 0) {
                        var sum = Vector2.zero;
                        foreach (var v in sp) sum += (Vector2)v;
                        spawnCenter = sum / sp.Length;
                        float r = 0f;
                        foreach (var v in sp) r = Mathf.Max(r, Vector2.Distance(spawnCenter, v));
                        spawnRadius = Mathf.Max(0.6f, r);
                    }
                } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LobbyGames.LogPrefix} spawn positions: {e.Message}"); }
                try {
                    bool any = false;
                    foreach (var c in lobby.GetComponentsInChildren<Collider2D>(true)) {
                        if (c == null || c.isTrigger) continue;
                        var b = c.bounds;
                        if (b.size.x * b.size.y > 400f) continue;
                        if (!any) { roomBounds = b; any = true; } else roomBounds.Encapsulate(b);
                    }
                    if (!any) roomBounds = new Bounds(spawnCenter, new Vector3(8f, 5f, 0f));
                } catch { }
                HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} lobby layout: spawn centre {spawnCenter.x:F2},{spawnCenter.y:F2} radius {spawnRadius:F2}, "
                    + $"walls {roomBounds.min.x:F2},{roomBounds.min.y:F2} .. {roomBounds.max.x:F2},{roomBounds.max.y:F2}");
            }
            center = spawnCenter; radius = spawnRadius; room = roomBounds;
        }

        internal static Vector2 SpawnCenter() { LobbyLayout(out var c, out _, out _); return c; }

        private static void BuildLanterns() {
            lanternsDirty = false;
            DestroyLanterns();
            lamps.Clear();
            var lobby = LobbyBehaviour.Instance;
            if (Faces.Count == 0 || lobby == null) return;
            lanternRoot = new GameObject("PumpkinLanterns") { layer = 11 };
            lanternRoot.transform.SetParent(lobby.transform, false);
            lanternRoot.transform.position = Vector3.zero;
            var order = Faces.Keys.OrderBy(k => k).ToList();
            var spots = LanternSpots(order.Count);
            for (int i = 0; i < order.Count; i++) {
                byte pid = order[i];
                var go = Lantern(lanternRoot.transform, Faces[pid], pid, LanternWidth, LobbyGames.NameOf(pid), pid == WinnerId);
                go.transform.position = new Vector3(spots[i].x, spots[i].y, spots[i].y / 1000f + 0.0005f);
            }
        }

        /// <summary>One lantern: halo, pumpkin, face, name (and a crown for the winner).</summary>
        private static GameObject Lantern(Transform parent, byte[] bits, byte pid, float width, string name, bool winner) {
            var go = new GameObject($"Lantern_{pid}") { layer = 11 };
            go.transform.SetParent(parent, false);
            var lamp = new Lamp { Seed = pid * 1.37f + 0.5f };

            lamp.Glow = Renderer(go, "Glow", LobbyArt.WorldSprite("glow", LobbyArt.LanternGlow(), width * 1.9f), new Vector3(0f, 0f, 0.002f));
            Renderer(go, "Body", LobbyArt.WorldSprite("lantern", LobbyArt.Lantern(), width), Vector3.zero);
            // the face field: x 40-120, y 50-130 of 160 (centre 80/90: 10 px below the middle)
            float faceW = width * LobbyArt.LanternFaceW / LobbyArt.LanternSize;
            float faceDy = -width * ((LobbyArt.LanternFaceY + LobbyArt.LanternFaceW / 2f) - LobbyArt.LanternSize / 2f) / LobbyArt.LanternSize;
            float faceDx = width * ((LobbyArt.LanternFaceX + LobbyArt.LanternFaceW / 2f) - LobbyArt.LanternSize / 2f) / LobbyArt.LanternSize;
            var tex = FaceTex(pid, bits);
            var fs = Sprite.Create(tex, new Rect(0, 0, Grid, Grid), new Vector2(0.5f, 0.5f), Grid / faceW);
            fs.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            lamp.Face = Renderer(go, "Face", fs, new Vector3(faceDx, faceDy, -0.001f));
            if (winner) Renderer(go, "Crown", LobbyArt.WorldSprite("crown", LobbyArt.Crown(), width * 0.42f), new Vector3(0f, width * 0.58f, -0.0015f));
            Label(go, name, new Vector3(0f, -width * 0.62f, -0.002f), winner ? new Color(1f, 0.85f, 0.3f) : Color.white, 1.35f);
            lamps.Add(lamp);
            return go;
        }

        private static Texture2D FaceTex(byte pid, byte[] bits) {
            faceTex.TryGetValue(pid, out var reuse);
            var t = LobbyArt.FaceTexture(bits, Lit, reuse);
            faceTex[pid] = t;
            return t;
        }

        private static SpriteRenderer Renderer(GameObject parent, string name, Sprite sprite, Vector3 local) {
            var go = new GameObject(name) { layer = 11 };
            go.transform.SetParent(parent.transform, false);
            go.transform.localPosition = local;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            return sr;
        }

        internal static TMPro.TextMeshPro Label(GameObject parent, string text, Vector3 local, Color color, float size) {
            var go = new GameObject("Name") { layer = 11 };
            go.transform.SetParent(parent.transform, false);
            go.transform.localPosition = local;
            var t = go.AddComponent<TMPro.TextMeshPro>();
            var f = HalloweenUI.Font();
            if (f != null) t.font = f;
            t.fontSize = size;
            t.fontStyle = TMPro.FontStyles.Bold;
            t.alignment = TMPro.TextAlignmentOptions.Center;
            t.enableWordWrapping = false;
            t.color = color;
            t.outlineColor = new Color32(0, 0, 0, 255);
            t.outlineWidth = 0.22f;
            t.rectTransform.sizeDelta = new Vector2(3f, 0.4f);
            t.text = text ?? "";
            return t;
        }

        private static void Flicker(float t) {
            for (int i = lamps.Count - 1; i >= 0; i--) {
                var l = lamps[i];
                if (l.Glow == null || l.Face == null) { lamps.RemoveAt(i); continue; }
                float f = Mathf.PerlinNoise(t * 2.6f, l.Seed);
                l.Glow.color = new Color(1f, 1f, 1f, 0.55f + 0.45f * f);
                float k = 0.82f + 0.18f * f;
                l.Face.color = new Color(k, k, k, 1f);
            }
        }

        // ================================================================ the winner at the spawn point
        private static void SpawnWinner(ShipStatus ship) {
            try {
                Vector2 at = ship.InitialSpawnCenter;
                winnerObj = new GameObject("WinnerPumpkin") { layer = 11 };
                winnerObj.transform.SetParent(ship.transform, false);
                winnerObj.transform.position = new Vector3(at.x, at.y, at.y / 1000f + 0.0005f);
                var go = Lantern(winnerObj.transform, WinnerFace, WinnerId, 0.95f, LobbyGames.T("Best pumpkin: ", "Bester Kürbis: ") + WinnerName, true);
                go.transform.localPosition = Vector3.zero;
                winnerShown = true;
                HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} winner pumpkin of {WinnerName} at the spawn point {at.x:F2},{at.y:F2}");
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LobbyGames.LogPrefix} winner pumpkin failed: {e.Message}"); winnerObj = null; }
        }

        internal static Vector3 WinnerPosition() => winnerObj != null ? winnerObj.transform.position : Vector3.zero;
        internal static bool WinnerStanding => winnerObj != null;
    }
}
