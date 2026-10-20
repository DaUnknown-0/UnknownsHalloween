// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Lobby games (2026-10-20): two things to do while the lobby fills up, both only in the lobby, both host switches.
 *   - Pumpkin Carving (PumpkinCarving.cs): everybody carves a face on a 24x24 grid in 60 s; the faces glow on
 *     lanterns in the lobby with the carver's name; the host can start a vote, the winner stands at the spawn
 *     point of the map in the next round. Off by default (host switch in the card).
 *   - Boo! (BooTag.cs): lobby tag. The host starts a round, a random player becomes the ghost (Angel Ghost
 *     costume) and turns others into ghosts with the Use button; the last one left wears a crown until the game
 *     starts. Only on the host's button press.
 *
 * Entry: two items in the UTS lobby menu (AppDomain contract "UTS.LobbyMenu.Add", order 61 and 62, next to
 * Trick or Treat at 60). Without UTS there is no entry (the lobby menu belongs to UTS).
 *
 * Network: module byte 242 on UC's channel 230, host-authoritative, small messages only (a face is 72 bytes, the
 * host spreads face broadcasts out to one every 0.25 s: data bursts used to get players dropped by the server).
 *   Sub 0  rules       host -> all     [carving on][boo seconds]
 *   Sub 1  carve       guest -> host   [72 bytes]                       (my face, to the host only)
 *   Sub 2  face        host -> all     [player][72 bytes]               (a joiner gets them addressed to him)
 *   Sub 3  remove      host -> all     [player]                         (host deleted it / carver left)
 *   Sub 4  vote        host -> all     [phase 0 none/1 open/2 result][seconds][n] n x [player][votes]
 *                                      phase 2 adds [winner][72 bytes][name]
 *   Sub 5  ballot      guest -> host   [player voted for]
 *   Sub 9  hello       guest -> host   [version]                        (I have the mod: may play Boo!)
 *   Sub 10 boo         host -> all     [phase 0 off/1 running/2 over][seconds][n] n x ghost [m] m x crowned
 *   Sub 11 touch       ghost -> host   [player touched]
 * Host settings live in BepInEx/config/com.daunknown.unknownshalloween.lobby.cfg.
 *
 * Lifetime: everything is keyed to the lobby (AmongUsClient.GameId). Joining a lobby, leaving it or a new game id
 * clears it (the resetVariables lobby-leak trap: resetVariables only runs at the round start). Boo! also ends with
 * the game start; carvings stay for the whole lobby session, the vote winner for the next round.
 * Self test: UC_HALLOWEEN_DIAG=carving / boo (LobbyGamesDiag.cs).
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using Hazel;
using UnityEngine;
using UnknownsCollection;

namespace UnknownsHalloween {
    internal static class LobbyGames {
        internal const string LogPrefix = "[Halloween/Lobby]";
        internal const byte RpcId = 242;
        internal const byte SubRules = 0, SubCarve = 1, SubFace = 2, SubRemove = 3, SubVote = 4, SubBallot = 5,
                            SubHello = 9, SubBoo = 10, SubTouch = 11;
        private const byte HelloVersion = 1;

        internal static readonly Color Pumpkin = new Color(1f, 0.55f, 0.12f);
        internal static readonly Color Ghost = new Color(0.62f, 0.74f, 0.96f);

        // ---- rules (host's, or the host's last message) ----
        internal static bool CarvingOn;
        internal static int BooSeconds = 90;

        private static ConfigFile cfg;
        private static ConfigEntry<bool> cCarving;
        private static ConfigEntry<int> cBoo;

        internal static bool AmHost() => AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost;
        internal static bool FreePlay() { try { return AmongUsClient.Instance != null && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay; } catch { return false; } }
        internal static bool De() => TrickOrTreat.De();
        internal static string T(string en, string de) => De() ? de : en;

        /// <summary>In a lobby (not in a round). The self tests also count freeplay as one.</summary>
        internal static bool InLobby() {
            if (LobbyGamesDiag.Active && ShipStatus.Instance != null && FreePlay()) return PlayerControl.LocalPlayer != null;
            return LobbyBehaviour.Instance != null && ShipStatus.Instance == null && PlayerControl.LocalPlayer != null;
        }

        internal static bool CanEdit() {
            var ac = AmongUsClient.Instance;
            if (ac == null) return false;
            return ac.AmHost || FreePlay();
        }

        // ---- boot ----
        private static bool booted;
        internal static void Boot() {
            if (booted) return;
            booted = true;
            try {
                LoadConfig();
                UCRpc.Register(RpcId, Handle);
                UCFx.RegisterTick(Tick);
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} self registration failed: {e}");
            }
        }

        private static void LoadConfig() {
            try {
                cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, "com.daunknown.unknownshalloween.lobby.cfg"), true);
                cCarving = cfg.Bind("Pumpkin Carving", "Enabled", false, "Players may carve pumpkins in the lobby (host setting, sent to everyone).");
                cBoo = cfg.Bind("Boo", "Seconds", 90, "Length of a Boo! round in seconds (60-120).");
                FromConfig();
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} config failed: {e}"); }
        }

        private static void FromConfig() {
            if (cfg == null) return;
            CarvingOn = cCarving.Value;
            BooSeconds = Mathf.Clamp(cBoo.Value, 60, 120);
        }

        internal static void RulesChanged() {
            if (!CanEdit()) return;
            BooSeconds = Mathf.Clamp(BooSeconds, 60, 120);
            if (cfg != null) {
                cCarving.Value = CarvingOn;
                cBoo.Value = BooSeconds;
                try { cfg.Save(); } catch { }
            }
            SendRules();
            if (!CarvingOn) { PumpkinCarvingUI.CloseCarve(); if (PumpkinCarving.VotePhase == 1) PumpkinCarving.HostEndVote(false); }
            LobbyCards.RefreshIfOpen();
        }

        private static void SendRules() {
            if (!AmHost()) return;
            Send(SubRules, w => { w.Write(CarvingOn); w.Write((byte)BooSeconds); });
        }

        // ---- network ----
        /// <summary>Sends on channel 230 / module 242; target -1 = everybody, otherwise one client id.</summary>
        internal static void Send(byte sub, Action<MessageWriter> write, int target = -1) {
            if (FreePlay()) return;
            try {
                var ac = AmongUsClient.Instance;
                var lp = PlayerControl.LocalPlayer;
                if (ac == null || lp == null) return;
                MessageWriter w;
                if (target < 0) w = UCRpc.Begin(RpcId);
                else {
                    w = ac.StartRpcImmediately(lp.NetId, UCRpc.CallId, SendOption.Reliable, target);
                    w.Write(RpcId);
                }
                w.Write(sub);
                write(w);
                ac.FinishRpcImmediately(w);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} send {sub} failed: {e.Message}"); }
        }

        internal static void SendToHost(byte sub, Action<MessageWriter> write) {
            var ac = AmongUsClient.Instance;
            if (ac == null) return;
            Send(sub, write, ac.HostId);
        }

        private static void Handle(MessageReader r) {
            try {
                byte sub = r.ReadByte();
                var sender = UCRpc.Sender;
                switch (sub) {
                    case SubRules: {
                        bool on = r.ReadBoolean();
                        int secs = r.ReadByte();
                        if (!UCRpc.RequireHost("Lobby.Rules")) return;
                        bool changed = on != CarvingOn || secs != BooSeconds;
                        CarvingOn = on;
                        BooSeconds = Mathf.Clamp(secs, 60, 120);
                        if (!helloSent) { helloSent = true; SendToHost(SubHello, w => w.Write(HelloVersion)); }
                        if (changed) {
                            if (!CarvingOn) PumpkinCarvingUI.CloseCarve();
                            LobbyCards.RefreshIfOpen();
                        }
                        break;
                    }
                    case SubHello: {
                        r.ReadByte();
                        if (AmHost() && sender != null) {
                            if (modded.Add(sender.PlayerId))
                                HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} player {sender.PlayerId} has the lobby games");
                        }
                        break;
                    }
                    case SubCarve: case SubFace: case SubRemove: case SubVote: case SubBallot:
                        PumpkinCarving.HandleRpc(sub, r, sender);
                        break;
                    case SubBoo: case SubTouch:
                        BooTag.HandleRpc(sub, r, sender);
                        break;
                }
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} HandleRpc failed: {e}"); }
        }

        // ---- who has the mod (host side; Boo! only picks among them) ----
        internal static readonly HashSet<byte> modded = new();
        private static bool helloSent;

        internal static bool HasMod(PlayerControl p) {
            if (p == null) return false;
            if (p == PlayerControl.LocalPlayer || FreePlay() || LobbyGamesDiag.Active) return true;
            return modded.Contains(p.PlayerId);
        }

        // ---- lifetime ----
        private static int gameId = int.MinValue;
        private static bool wasLobby;
        private static float rulesAt = -1f, resendAt;

        internal static int CurrentGameId() {
            try {
                var ac = AmongUsClient.Instance;
                if (ac == null || ac.GameState == InnerNet.InnerNetClient.GameStates.NotJoined) return int.MinValue;
                return ac.GameId;
            } catch { return int.MinValue; }
        }

        private static void Tick() {
            try {
                LobbyGamesDiag.Tick();
                int gid = CurrentGameId();
                if (gid != gameId) {
                    // left the lobby or a new one: nothing from before may survive
                    if (gameId != int.MinValue || gid == int.MinValue) ClearSession(gid == int.MinValue ? "left the lobby" : "new lobby");
                    gameId = gid;
                }
                bool lobby = InLobby();
                if (!lobby) {
                    if (wasLobby) { wasLobby = false; BooTag.Reset("lobby over"); PumpkinCarvingUI.CloseAll(); LobbyCards.Close(); }
                    PumpkinCarving.RoundTick();
                    return;
                }
                if (!wasLobby) { wasLobby = true; PumpkinCarving.LobbyAgain(); }
                LobbyCards.Tick();
                if (AmHost()) {
                    float t = Time.realtimeSinceStartup;
                    if (rulesAt > 0f && t >= rulesAt) { rulesAt = -1f; SendRules(); }
                    if (t >= resendAt) { resendAt = t + 20f; SendRules(); }       // safety net for a lost join message
                }
                PumpkinCarving.LobbyTick();
                PumpkinCarvingUI.Tick();
                BooTag.Tick();
            } catch (Exception e) {
                if (!tickLogged) { tickLogged = true; HalloweenPlugin.Logger?.LogError($"{LogPrefix} tick failed (logged once): {e}"); }
            }
        }
        private static bool tickLogged;

        internal static void ClearSession(string why) {
            string state = "-";
            try { var ac = AmongUsClient.Instance; if (ac != null) state = $"{ac.GameState}/{ac.NetworkMode}, last disconnect {ac.LastDisconnectReason}"; } catch { }
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} session cleared ({why}; {state})");
            modded.Clear();
            helloSent = false;
            BooTag.Reset(why);
            PumpkinCarving.Clear();
            PumpkinCarvingUI.CloseAll();
            LobbyCards.Close();
            wasLobby = false;
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class JoinedPatch {
            static bool Prepare() { Boot(); return true; }
            public static void Postfix() {
                try {
                    // a different lobby: nothing from before survives; the same one again (back from a round): the
                    // carvings stay, Boo! does not
                    int gid = CurrentGameId();
                    if (gid != gameId) ClearSession("joined a lobby"); else BooTag.Reset("back in the lobby");
                    gameId = gid;
                    if (AmHost()) { FromConfig(); rulesAt = Time.realtimeSinceStartup + 1f; }
                    else { CarvingOn = false; BooSeconds = 90; }
                } catch { }
            }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnPlayerJoined))]
        static class PlayerJoinedPatch {
            public static void Postfix([HarmonyArgument(0)] InnerNet.ClientData data) {
                try {
                    if (!AmHost()) return;
                    rulesAt = Time.realtimeSinceStartup + 2f;
                    if (data != null) PumpkinCarving.QueueAllFor(data.Id);
                    BooTag.SendStateSoon();
                } catch { }
            }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnPlayerLeft))]
        static class PlayerLeftPatch {
            public static void Postfix() {
                try { if (AmHost()) { PumpkinCarving.HostDropLeavers(); BooTag.HostDropLeavers(); } } catch { }
            }
        }

        [HarmonyPatch(typeof(GameStartManager), nameof(GameStartManager.BeginGame))]
        static class BeginGamePatch {
            public static void Postfix() { try { BooTag.HostStop("game start"); PumpkinCarving.HostEndVote(true); } catch { } }
        }

        // ---- lobby menu entries (UTS) ----
        private const string AddKey = "UTS.LobbyMenu.Add";
        private static bool registered;
        private static float nextTry;

        internal static void TryRegisterMenu() {
            if (registered || Time.realtimeSinceStartup < nextTry) return;
            nextTry = Time.realtimeSinceStartup + 1f;
            try {
                if (AppDomain.CurrentDomain.GetData(AddKey) is not Action<string, int, Func<bool>, Func<string>, Action, Color> add) return;
                add("halloween.carving", 61, () => LobbyBehaviour.Instance != null,
                    () => "Pumpkin Carving" + (CarvingOn ? T(" (on)", " (an)") : ""), LobbyCards.OpenCarving, Pumpkin);
                add("halloween.boo", 62, () => LobbyBehaviour.Instance != null,
                    () => "Boo!" + (BooTag.Running ? T(" (running)", " (läuft)") : ""), LobbyCards.OpenBoo, Ghost);
                registered = true;
                HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} menu entries added to the UTS lobby menu.");
            } catch (Exception e) { registered = true; HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} lobby menu entries failed: {e.Message}"); }
        }

        internal static string NameOf(byte pid) {
            if (PumpkinCarving.FakeNames.TryGetValue(pid, out var n)) return n;
            try {
                foreach (var p in PlayerControl.AllPlayerControls.ToArray())
                    if (p != null && p.PlayerId == pid && p.Data != null) return p.Data.PlayerName;
            } catch { }
            return "?";
        }
    }

    /// <summary>The two cards behind the lobby menu entries (HalloweenUI look).</summary>
    internal static class LobbyCards {
        private static GameObject root;
        private static int which;               // 1 carving, 2 boo
        private static float refreshAt;
        internal static bool IsOpen => root != null;

        internal static void Close() { if (root != null) UnityEngine.Object.Destroy(root); root = null; which = 0; }
        internal static void RefreshIfOpen() { if (root != null) { int w = which; Close(); if (w == 1) OpenCarving(); else if (w == 2) OpenBoo(); } }
        internal static void OpenCarving() => Open(1);
        internal static void OpenBoo() => Open(2);

        internal static void Tick() {
            LobbyGames.TryRegisterMenu();
            if (root == null) return;
            if (Input.GetKeyDown(KeyCode.Escape)) { Close(); return; }
            // the live parts (timers, counts): rebuilt when something shown has changed, checked twice a second
            if (Time.realtimeSinceStartup < refreshAt) return;
            refreshAt = Time.realtimeSinceStartup + 0.5f;
            if (Signature() != shown) RefreshIfOpen();
        }

        private static string T(string en, string de) => LobbyGames.T(en, de);

        private static string shown = "";
        private static string Signature() => which == 1
            ? $"{PumpkinCarving.Version}/{(PumpkinCarving.VotePhase == 1 ? PumpkinCarving.VoteSecondsLeft() : -1)}/{LobbyGames.CarvingOn}"
            : $"{BooTag.Phase}/{(BooTag.Running ? BooTag.SecondsLeft() : -1)}/{BooTag.Ghosts.Count}/{BooTag.Crowned.Count}/{LobbyGames.BooSeconds}";

        private static void Open(int kind) {
            try {
                Close();
                which = kind;
                shown = Signature();
                refreshAt = Time.realtimeSinceStartup + 1f;
                root = HalloweenUI.Canvas(kind == 1 ? "PumpkinCarvingMenu" : "BooMenu", 9500, true);
                HalloweenUI.Backdrop(root, Close);
                if (kind == 1) BuildCarving(); else BuildBoo();
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"{LobbyGames.LogPrefix} card failed: {e}");
                Close();
            }
        }

        private const float Pad = 34f;

        private static void Header(GameObject card, string title, Color color, bool edit) {
            HalloweenUI.Title(card, title, 16f, 34f, color);
            HalloweenUI.Button(card, "X", new Vector2(-HalloweenUI.FrameW - 12f, -HalloweenUI.FrameW - 12f), new Vector2(54f, 54f), HalloweenUI.Red, Close,
                out _, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 36f);
            HalloweenUI.Text(card, edit ? T("You are the host.", "Du bist der Host.") : T("The host decides.", "Der Host entscheidet."),
                18f, edit ? HalloweenUI.Muted : HalloweenUI.Warn, new Vector2(470f, -36f), new Vector2(420f, 30f));
        }

        private static GameObject Btn(GameObject card, string label, float x, float y, float w, Color c, Action click, float font = 20f) =>
            HalloweenUI.Button(card, label, new Vector2(x, y), new Vector2(w, 50f), c, click, out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), font);

        // ---------------------------------------------------------------- Pumpkin Carving card
        private static void BuildCarving() {
            const float W = 1180f;
            int rows = Mathf.Clamp((Mathf.Min(PumpkinCarving.Faces.Count, 20) + 4) / 5, 1, 4);
            float H = 420f + rows * 116f;
            bool edit = LobbyGames.CanEdit();
            var card = HalloweenUI.CenterPanel(root, new Vector2(W, H));
            Header(card, "Pumpkin Carving", LobbyGames.Pumpkin, edit);
            float y = -120f;
            HalloweenUI.Text(card, T("Carve a face in 60 seconds. It glows on a lantern in the lobby with your name. The host can start a vote: the winner stands at the spawn point next round.",
                                     "Schnitze in 60 Sekunden ein Gesicht. Es leuchtet auf einer Laterne in der Lobby, mit deinem Namen. Der Host kann abstimmen lassen: der Sieger steht in der nächsten Runde am Startpunkt."),
                19f, HalloweenUI.Muted, new Vector2(Pad, y), new Vector2(W - 2 * Pad, 60f));
            y -= 84f;
            float x = Pad;
            if (edit) {
                Btn(card, LobbyGames.CarvingOn ? T("Carving: on", "Schnitzen: an") : T("Carving: off", "Schnitzen: aus"), x, y, 260f,
                    LobbyGames.CarvingOn ? HalloweenUI.Green : HalloweenUI.Grey, () => { LobbyGames.CarvingOn = !LobbyGames.CarvingOn; LobbyGames.RulesChanged(); });
                x += 280f;
            }
            if (LobbyGames.CarvingOn) {
                bool mine = PumpkinCarving.Faces.ContainsKey(PlayerControl.LocalPlayer.PlayerId);
                Btn(card, mine ? T("Carve again", "Neu schnitzen") : T("Carve!", "Schnitzen!"), x, y, 260f, LobbyGames.Pumpkin, () => { Close(); PumpkinCarvingUI.OpenCarve(); });
                x += 280f;
                if (PumpkinCarving.VotePhase == 1)
                    Btn(card, T("Vote", "Abstimmen"), x, y, 220f, HalloweenUI.Blue, () => { Close(); PumpkinCarvingUI.OpenVote(); });
                else if (edit)
                    Btn(card, T("Start vote", "Abstimmung starten"), x, y, 280f, PumpkinCarving.Faces.Count >= 2 ? HalloweenUI.Blue : HalloweenUI.Grey,
                        () => { if (PumpkinCarving.HostStartVote()) { Close(); PumpkinCarvingUI.OpenVote(); } });
                x += 300f;
                if (edit && PumpkinCarving.VotePhase == 1)
                    Btn(card, T("End vote", "Abstimmung beenden"), x, y, 260f, HalloweenUI.Amber, () => PumpkinCarving.HostEndVote(false));
            } else if (!edit) {
                HalloweenUI.Text(card, T("The host has not switched carving on.", "Der Host hat das Schnitzen nicht eingeschaltet."), 22f, HalloweenUI.Warn,
                    new Vector2(Pad, y - 10f), new Vector2(700f, 34f));
            }
            y -= 76f;

            string status = PumpkinCarving.VotePhase == 1
                ? T($"Vote running: {PumpkinCarving.VoteSecondsLeft()} s left, {PumpkinCarving.BallotCount} vote(s).", $"Abstimmung läuft: noch {PumpkinCarving.VoteSecondsLeft()} s, {PumpkinCarving.BallotCount} Stimme(n).")
                : PumpkinCarving.WinnerFace != null
                    ? T($"Winner: {PumpkinCarving.WinnerName}. Their pumpkin stands at the spawn point next round.", $"Sieger: {PumpkinCarving.WinnerName}. Sein Kürbis steht in der nächsten Runde am Startpunkt.")
                    : T($"{PumpkinCarving.Faces.Count} pumpkin(s) carved.", $"{PumpkinCarving.Faces.Count} Kürbis(se) geschnitzt.");
            HalloweenUI.Text(card, status, 22f, Color.white, new Vector2(Pad, y), new Vector2(W - 2 * Pad, 34f), TMPro.FontStyles.Bold);
            y -= 50f;

            // the carvings, the host can delete each one
            const int cols = 5;
            float tw = (W - 2 * Pad - (cols - 1) * 14f) / cols, th = 104f;
            int i = 0;
            foreach (var kv in PumpkinCarving.Faces.OrderBy(k => k.Key)) {
                byte pid = kv.Key;
                var pos = new Vector2(Pad + (i % cols) * (tw + 14f), y - (i / cols) * (th + 12f));
                var tile = new GameObject("Tile");
                tile.transform.SetParent(card.transform, false);
                var rt = HalloweenUI.Rect(tile, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
                rt.anchoredPosition = pos; rt.sizeDelta = new Vector2(tw, th);
                HalloweenUI.Stretch(HalloweenUI.Rounded(tile, HalloweenUI.Field, HalloweenUI.RadiusTile));
                PumpkinCarvingUI.LanternImage(tile, kv.Value, new Vector2(8f, -8f), 88f, pid == PumpkinCarving.WinnerId);
                HalloweenUI.Text(tile, LobbyGames.NameOf(pid), 18f, Color.white, new Vector2(104f, -14f), new Vector2(tw - 112f, 50f), TMPro.FontStyles.Bold);
                if (edit)
                    HalloweenUI.Button(tile, T("Delete", "Löschen"), new Vector2(104f, -58f), new Vector2(110f, 36f), HalloweenUI.Red,
                        () => { PumpkinCarving.HostRemove(pid, "deleted by the host"); RefreshIfOpen(); }, out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 16f);
                i++;
                if (i >= 20) break;
            }
            if (i == 0)
                HalloweenUI.Text(card, T("No pumpkins yet.", "Noch keine Kürbisse."), 20f, HalloweenUI.Muted, new Vector2(Pad, y), new Vector2(600f, 30f));
        }

        // ---------------------------------------------------------------- Boo! card
        private static void BuildBoo() {
            const float W = 1000f, H = 560f;
            bool edit = LobbyGames.CanEdit();
            var card = HalloweenUI.CenterPanel(root, new Vector2(W, H));
            Header(card, "Boo!", LobbyGames.Ghost, edit);
            float y = -120f;
            HalloweenUI.Text(card, T("Lobby tag: one player becomes a ghost and turns others into ghosts with the Use button. The last one left wears a crown until the game starts.",
                                     "Lobby-Fangen: ein Spieler wird zum Geist und verwandelt andere mit dem Benutzen-Knopf. Wer zuletzt übrig ist, trägt bis zum Spielstart eine Krone."),
                19f, HalloweenUI.Muted, new Vector2(Pad, y), new Vector2(W - 2 * Pad, 60f));
            y -= 90f;
            if (edit) {
                if (BooTag.Running) Btn(card, T("Stop Boo!", "Boo! abbrechen"), Pad, y, 260f, HalloweenUI.Red, () => { BooTag.HostStop("stopped by the host"); RefreshIfOpen(); });
                else Btn(card, T("Start Boo!", "Boo! starten"), Pad, y, 260f, BooTag.CanStart(out _) ? HalloweenUI.Green : HalloweenUI.Grey,
                    () => { if (BooTag.HostStart(out var why)) Close(); else { HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} Boo! not started: {why}"); RefreshIfOpen(); } });
                float x = Pad + 300f;
                HalloweenUI.Text(card, T("Length", "Dauer"), 18f, HalloweenUI.Muted, new Vector2(x, y + 22f), new Vector2(200f, 24f));
                HalloweenUI.Button(card, "-", new Vector2(x, y), new Vector2(50f, 50f), HalloweenUI.Teal,
                    () => { LobbyGames.BooSeconds = Mathf.Max(60, LobbyGames.BooSeconds - 15); LobbyGames.RulesChanged(); }, out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 30f);
                HalloweenUI.Text(card, $"{LobbyGames.BooSeconds} s", 24f, Color.white, new Vector2(x + 56f, y - 8f), new Vector2(110f, 34f), TMPro.FontStyles.Bold, TMPro.TextAlignmentOptions.Center);
                HalloweenUI.Button(card, "+", new Vector2(x + 172f, y), new Vector2(50f, 50f), HalloweenUI.Teal,
                    () => { LobbyGames.BooSeconds = Mathf.Min(120, LobbyGames.BooSeconds + 15); LobbyGames.RulesChanged(); }, out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 30f);
                if (!BooTag.Running && !BooTag.CanStart(out var why))
                    HalloweenUI.Text(card, why, 18f, HalloweenUI.Warn, new Vector2(Pad, y - 60f), new Vector2(W - 2 * Pad, 30f));
            }
            y -= 120f;
            HalloweenUI.Text(card, BooTag.StatusLine(), 24f, Color.white, new Vector2(Pad, y), new Vector2(W - 2 * Pad, 80f), TMPro.FontStyles.Bold);
        }
    }
}
