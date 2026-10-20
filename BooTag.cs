// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Boo! (lobby tag, see LobbyGames.cs for the network layout). Only on the host's button press, only in the lobby.
 *   - The host picks a random player (among those with the mod) as the first ghost. Ghosts wear the Angel Ghost
 *     costume (HalloweenCostumes, through TOR's setLook like the Masquerade Ball; without the costume packages
 *     they turn white). A ghost next to somebody gets the Use button as BOO!: the touch goes to the host as a
 *     request, the host checks the distance on its side and sends the new state.
 *   - Over when one is left (or the time is up: everybody still standing). The winners wear a small crown until
 *     the game starts; the ghosts look like themselves again.
 *   - The host can stop it any time. Game start, leaving the lobby and a new lobby end it on every client
 *     (LobbyGames tick and OnGameJoined; not resetVariables, which only runs at the round start).
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Hazel;
using TheOtherRoles;
using UnityEngine;
using UnknownsCollection;

namespace UnknownsHalloween {
    internal static class BooTag {
        private const string GhostHat = "Halloween Angel Ghost";
        private const int WhiteColor = 7;
        internal const float TouchRange = 1.0f, HostRange = 1.7f;

        internal static int Phase;                     // 0 off, 1 running, 2 over (crowns)
        internal static bool Running => Phase == 1;
        internal static readonly HashSet<byte> Ghosts = new();
        internal static readonly HashSet<byte> Crowned = new();
        private static readonly HashSet<byte> players = new();       // host: who plays this round
        private static float endsAt;
        private static float sendAt = -1f;
        private static readonly System.Random rnd = new System.Random();

        internal static int SecondsLeft() => Mathf.Max(0, Mathf.CeilToInt(endsAt - Time.realtimeSinceStartup));

        private static string T(string en, string de) => LobbyGames.T(en, de);

        private static List<PlayerControl> Present() =>
            PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null && !p.Data.Disconnected).ToList();

        // ================================================================ host
        internal static bool CanStart(out string why) {
            why = "";
            if (!LobbyGames.CanEdit()) { why = T("Only the host starts Boo!.", "Nur der Host startet Boo!."); return false; }
            if (!LobbyGames.InLobby()) { why = T("Only in the lobby.", "Nur in der Lobby."); return false; }
            if (Running) { why = T("Already running.", "Läuft schon."); return false; }
            int n = Present().Count(LobbyGames.HasMod);
            if (n < 2) { why = T("Needs at least 2 players with Unknown's Halloween.", "Braucht mindestens 2 Spieler mit Unknown's Halloween."); return false; }
            return true;
        }

        internal static bool HostStart(out string why) {
            if (!CanStart(out why)) return false;
            var list = Present().Where(LobbyGames.HasMod).ToList();
            players.Clear();
            foreach (var p in list) players.Add(p.PlayerId);
            Ghosts.Clear();
            Crowned.Clear();
            var first = LobbyGamesDiag.ForceLocalGhost ? PlayerControl.LocalPlayer : list[rnd.Next(list.Count)];
            Ghosts.Add(first.PlayerId);
            Phase = 1;
            endsAt = Time.realtimeSinceStartup + LobbyGames.BooSeconds;
            HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} Boo! started: {players.Count} players, first ghost {first.PlayerId} ({LobbyGames.NameOf(first.PlayerId)}), {LobbyGames.BooSeconds} s");
            SendState();
            Applied(new HashSet<byte>());
            return true;
        }

        internal static void HostStop(string why) {
            if (!LobbyGames.CanEdit()) return;
            if (Phase == 0 && Crowned.Count == 0) return;
            HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} Boo! stopped ({why})");
            Phase = 0;
            Ghosts.Clear();
            Crowned.Clear();
            players.Clear();
            SendState();
            Applied(new HashSet<byte>());
        }

        internal static void HostTouch(byte ghost, byte target) {
            if (!Running || !Ghosts.Contains(ghost) || Ghosts.Contains(target) || !players.Contains(target)) return;
            var g = Helpers.playerById(ghost);
            var t = Helpers.playerById(target);
            if (g == null || t == null) return;
            float d = Vector2.Distance(g.GetTruePosition(), t.GetTruePosition());
            if (d > HostRange) { HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} Boo! touch {ghost} -> {target} refused ({d:F2} away)"); return; }
            var before = new HashSet<byte>(Ghosts);
            Ghosts.Add(target);
            HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} Boo! {LobbyGames.NameOf(ghost)} got {LobbyGames.NameOf(target)} ({Humans().Count} left)");
            if (Humans().Count <= 1) Finish("one left");
            SendState();
            Applied(before);
        }

        private static List<byte> Humans() {
            var here = new HashSet<byte>(Present().Select(p => p.PlayerId));
            return players.Where(id => here.Contains(id) && !Ghosts.Contains(id)).ToList();
        }

        private static void Finish(string why) {
            var winners = Humans();
            Phase = 2;
            Crowned.Clear();
            foreach (var id in winners) Crowned.Add(id);
            Ghosts.Clear();
            HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} Boo! over ({why}): crown for {string.Join(", ", winners.Select(LobbyGames.NameOf))}");
        }

        internal static void HostDropLeavers() {
            if (Phase == 0) return;
            var here = new HashSet<byte>(Present().Select(p => p.PlayerId));
            players.RemoveWhere(id => !here.Contains(id));
            Ghosts.RemoveWhere(id => !here.Contains(id));
            Crowned.RemoveWhere(id => !here.Contains(id));
            if (Running) {
                var humans = Humans();
                if (Ghosts.Count == 0 && humans.Count >= 2) {
                    byte g = humans[rnd.Next(humans.Count)];
                    Ghosts.Add(g);
                    HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} Boo! the ghost left, new ghost {g}");
                } else if (humans.Count <= 1) Finish("players left");
            }
            SendState();
            Applied(new HashSet<byte>(Ghosts));
        }

        internal static void SendStateSoon() { if (Phase != 0) sendAt = Time.realtimeSinceStartup + 2.5f; }

        private static void SendState() {
            sendAt = -1f;
            int phase = Phase, secs = SecondsLeft();
            var g = Ghosts.ToList(); var c = Crowned.ToList();
            LobbyGames.Send(LobbyGames.SubBoo, w => {
                w.Write((byte)phase);
                w.Write((byte)Mathf.Clamp(secs, 0, 255));
                w.Write((byte)g.Count); foreach (var id in g) w.Write(id);
                w.Write((byte)c.Count); foreach (var id in c) w.Write(id);
            });
        }

        // ================================================================ every client
        internal static void HandleRpc(byte sub, MessageReader r, PlayerControl sender) {
            if (sub == LobbyGames.SubTouch) {
                byte target = r.ReadByte();
                if (LobbyGames.AmHost() && sender != null) HostTouch(sender.PlayerId, target);
                return;
            }
            int phase = r.ReadByte(), secs = r.ReadByte();
            var g = new HashSet<byte>(); int n = r.ReadByte(); for (int i = 0; i < n; i++) g.Add(r.ReadByte());
            var c = new HashSet<byte>(); int m = r.ReadByte(); for (int i = 0; i < m; i++) c.Add(r.ReadByte());
            if (!UCRpc.RequireHost("Boo.State")) return;
            if (!LobbyGames.InLobby()) return;
            var before = new HashSet<byte>(Ghosts);
            Phase = phase;
            endsAt = Time.realtimeSinceStartup + secs;
            Ghosts.Clear(); foreach (var id in g) Ghosts.Add(id);
            Crowned.Clear(); foreach (var id in c) Crowned.Add(id);
            Applied(before);
        }

        /// <summary>After any state change: BOO! pops for the new ghosts, looks and crowns follow.</summary>
        private static void Applied(HashSet<byte> ghostsBefore) {
            if (Running) foreach (var id in Ghosts) if (!ghostsBefore.Contains(id) && ghostsBefore.Count > 0) Pop(id);
            nextLook = 0f;
            LobbyCards.RefreshIfOpen();
            if (Phase == 2 && Crowned.Count > 0) Banner(T("Boo! is over. Crown for ", "Boo! ist vorbei. Krone für ") + string.Join(", ", Crowned.Select(LobbyGames.NameOf)), 6f);
            if (Phase == 0) Banner("", 0f);
        }

        internal static void Reset(string why) {
            if (Phase != 0 || Crowned.Count > 0 || dressed.Count > 0)
                HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} Boo! reset ({why})");
            Phase = 0;
            Ghosts.Clear();
            Crowned.Clear();
            players.Clear();
            sendAt = -1f;
            RestoreAll();
            foreach (var kv in crowns) if (kv.Value != null) UnityEngine.Object.Destroy(kv.Value);
            crowns.Clear();
            foreach (var p in pops) if (p.Go != null) UnityEngine.Object.Destroy(p.Go);
            pops.Clear();
            if (hud != null) UnityEngine.Object.Destroy(hud);
            hud = null; hudText = null; bannerUntil = 0f;
            BooUse.Release();
        }

        internal static void Tick() {
            float t = Time.realtimeSinceStartup;
            if (LobbyGames.AmHost() && Running) {
                if (t >= endsAt) { Finish("time up"); SendState(); Applied(new HashSet<byte>()); }
                else if (sendAt > 0f && t >= sendAt) SendState();
            }
            if (t >= nextLook) { nextLook = t + 0.25f; Looks(); }
            Crowns();
            Pops();
            Hud();
            BooUse.Tick();
        }

        // ---- looks ----
        private static readonly HashSet<byte> dressed = new();
        private static float nextLook;
        private static string ghostHatId;

        private static string GhostHatId() {
            if (!string.IsNullOrEmpty(ghostHatId)) return ghostHatId;
            try { if (HalloweenCostumes.HatsRegistered) ghostHatId = UCHats.HatIdOf(GhostHat); } catch { }
            return ghostHatId;
        }

        private static void Looks() {
            string hat = GhostHatId();
            foreach (var p in Present()) {
                bool ghost = Running && Ghosts.Contains(p.PlayerId);
                try {
                    if (ghost) {
                        var o = p.Data.DefaultOutfit;
                        string worn = null;
                        try { worn = p.cosmetics.hat.Hat != null ? p.cosmetics.hat.Hat.ProdId : null; } catch { }
                        if (!string.IsNullOrEmpty(hat)) {
                            if (worn != hat || !dressed.Contains(p.PlayerId)) p.setLook(p.Data.PlayerName, o.ColorId, hat, "", o.SkinId, o.PetId);
                        } else if (!dressed.Contains(p.PlayerId)) p.setLook(p.Data.PlayerName, WhiteColor, o.HatId, o.VisorId, o.SkinId, o.PetId);
                        dressed.Add(p.PlayerId);
                    } else if (dressed.Remove(p.PlayerId)) Restore(p);
                } catch { }
            }
            dressed.RemoveWhere(id => Helpers.playerById(id) == null);
        }

        private static void Restore(PlayerControl p) {
            try {
                if (p == null || p.Data == null) return;
                var o = p.Data.DefaultOutfit;
                p.setLook(p.Data.PlayerName, o.ColorId, o.HatId, o.VisorId, o.SkinId, o.PetId);
            } catch { }
        }

        private static void RestoreAll() {
            foreach (var id in dressed.ToList()) Restore(Helpers.playerById(id));
            dressed.Clear();
        }

        // ---- crowns ----
        private static readonly Dictionary<byte, GameObject> crowns = new();

        private static void Crowns() {
            foreach (var id in crowns.Keys.ToList())
                if (!Crowned.Contains(id) || crowns[id] == null) { if (crowns[id] != null) UnityEngine.Object.Destroy(crowns[id]); crowns.Remove(id); }
            foreach (var id in Crowned) {
                var p = Helpers.playerById(id);
                if (p == null) continue;
                if (!crowns.TryGetValue(id, out var go) || go == null) {
                    go = new GameObject("BooCrown") { layer = 11 };
                    UnityEngine.Object.DontDestroyOnLoad(go);
                    var sr = go.AddComponent<SpriteRenderer>();
                    sr.sprite = LobbyArt.WorldSprite("crown", LobbyArt.Crown(), 0.34f);
                    crowns[id] = go;
                }
                var pos = p.transform.position;
                float bob = Mathf.Sin(Time.time * 3f + id) * 0.025f;
                go.transform.position = new Vector3(pos.x, pos.y + 0.80f + bob, pos.z - 0.05f);
                go.SetActive(p.Visible);
            }
        }

        // ---- BOO! popups over a new ghost ----
        private sealed class PopFx { public GameObject Go; public TMPro.TextMeshPro Text; public byte Id; public float Start; }
        private static readonly List<PopFx> pops = new();

        private static void Pop(byte id) {
            var p = Helpers.playerById(id);
            if (p == null) return;
            var go = new GameObject("BooPop") { layer = 11 };
            UnityEngine.Object.DontDestroyOnLoad(go);
            var t = PumpkinCarving.Label(go, "BOO!", Vector3.zero, new Color(0.85f, 0.92f, 1f), 3.2f);
            pops.Add(new PopFx { Go = go, Text = t, Id = id, Start = Time.time });
            try { SoundManager.Instance?.PlaySound(HudManager.Instance?.TaskCompleteSound, false, 0.6f); } catch { }
        }

        private static void Pops() {
            for (int i = pops.Count - 1; i >= 0; i--) {
                var f = pops[i];
                float age = Time.time - f.Start;
                var p = Helpers.playerById(f.Id);
                if (f.Go == null || age > 1.3f || p == null) { if (f.Go != null) UnityEngine.Object.Destroy(f.Go); pops.RemoveAt(i); continue; }
                var pos = p.transform.position;
                f.Go.transform.position = new Vector3(pos.x, pos.y + 0.9f + age * 0.5f, pos.z - 0.1f);
                float s = age < 0.15f ? Mathf.Lerp(0.4f, 1.15f, age / 0.15f) : 1f;
                f.Go.transform.localScale = new Vector3(s, s, 1f);
                if (f.Text != null) f.Text.alpha = Mathf.Clamp01(1.6f - age * 1.4f);
            }
        }

        // ---- the strip at the top (time, who is left, my role) ----
        private static GameObject hud;
        private static TMPro.TextMeshProUGUI hudText;
        private static float bannerUntil;
        private static string banner = "";

        private static void Banner(string text, float seconds) { banner = text; bannerUntil = seconds > 0f ? Time.realtimeSinceStartup + seconds : 0f; }

        private static void Hud() {
            bool show = Running || (bannerUntil > Time.realtimeSinceStartup && banner.Length > 0);
            if (!show) { if (hud != null) { UnityEngine.Object.Destroy(hud); hud = null; hudText = null; } return; }
            if (hud == null) {
                hud = HalloweenUI.Canvas("BooHud", 8900, false);
                var panel = HalloweenUI.Panel(hud, new Vector2(820f, 92f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, -118f));
                hudText = HalloweenUI.Label(panel, "", 26f, Color.white, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(-30f, -10f),
                    TMPro.TextAlignmentOptions.Center, TMPro.FontStyles.Bold);
            }
            string line;
            if (Running) {
                var lp = PlayerControl.LocalPlayer;
                bool me = lp != null && Ghosts.Contains(lp.PlayerId);
                int left = PlayerControl.AllPlayerControls.ToArray().Count(p => p != null && p.Data != null && !p.Data.Disconnected && !Ghosts.Contains(p.PlayerId)
                                                                                && (LobbyGames.AmHost() ? players.Contains(p.PlayerId) : true));
                int secs = SecondsLeft();
                string role = me ? T("<color=#A8C4FF>You are a ghost: BOO! the others.</color>", "<color=#A8C4FF>Du bist ein Geist: erschrecke die anderen!</color>")
                                 : T("<color=#FFB45A>Run from the ghosts!</color>", "<color=#FFB45A>Lauf vor den Geistern weg!</color>");
                line = $"Boo!  {secs / 60}:{secs % 60:00}   " + T($"{left} left", $"noch {left}") + "\n" + role;
            } else line = banner;
            if (hudText != null) HalloweenUI.SetText(hudText, line);
        }

        internal static string StatusLine() {
            if (Running) return T($"Running: {SecondsLeft()} s left, {Ghosts.Count} ghost(s).", $"Läuft: noch {SecondsLeft()} s, {Ghosts.Count} Geist(er).");
            if (Phase == 2 && Crowned.Count > 0) return T("Crown for ", "Krone für ") + string.Join(", ", Crowned.Select(LobbyGames.NameOf));
            return T("Not running.", "Läuft nicht.");
        }

        // ---- my touch ----
        internal static PlayerControl Target() {
            var lp = PlayerControl.LocalPlayer;
            if (!Running || lp == null || !Ghosts.Contains(lp.PlayerId)) return null;
            PlayerControl best = null; float bd = TouchRange;
            foreach (var p in Present()) {
                if (p == lp || Ghosts.Contains(p.PlayerId)) continue;
                if (LobbyGames.AmHost() && !players.Contains(p.PlayerId)) continue;
                float d = Vector2.Distance(lp.GetTruePosition(), p.GetTruePosition());
                if (d < bd) { bd = d; best = p; }
            }
            return best;
        }

        internal static void Touch(PlayerControl target) {
            var lp = PlayerControl.LocalPlayer;
            if (target == null || lp == null) return;
            if (LobbyGames.AmHost()) HostTouch(lp.PlayerId, target.PlayerId);
            else LobbyGames.SendToHost(LobbyGames.SubTouch, w => w.Write(target.PlayerId));
        }
    }

    /// <summary>The Use button as BOO! while I am a ghost next to somebody (TreatUse's pattern).</summary>
    internal static class BooUse {
        private static bool owned;
        private static IntPtr hooked;
        private static PlayerControl current;
        private static Sprite icon;
        private static float iconWidth = -1f, cooldown;
        internal static bool Owned => owned;

        internal static void Tick() {
            var hud = HudManager.InstanceExists ? HudManager.Instance : null;
            var ub = hud != null ? hud.UseButton : null;
            var lp = PlayerControl.LocalPlayer;
            PlayerControl t = null;
            if (ub != null && lp != null && lp.CanMove && Minigame.Instance == null && ub.currentTarget == null && !PumpkinCarvingUI.CarveOpen)
                t = BooTag.Target();
            if (t == null) { Release(); return; }
            try {
                if (hooked != ub.Pointer) {
                    var pb = ub.GetComponent<PassiveButton>();
                    if (pb != null) pb.OnClick.AddListener((Action)OnClick);
                    hooked = ub.Pointer;
                }
                if (!ub.gameObject.activeSelf) ub.gameObject.SetActive(true);
                if (hud.PetButton != null && hud.PetButton.gameObject.activeSelf) hud.PetButton.gameObject.SetActive(false);
                if (iconWidth < 0f && ub.graphic != null && ub.graphic.sprite != null) iconWidth = ub.graphic.sprite.bounds.size.x;
                ub.SetEnabled();
                owned = true;
                current = t;
                Paint(ub);
                if (Input.GetKeyDown(KeyCode.E) && TreatUse.KeyboardFree()) OnClick();
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LobbyGames.LogPrefix} boo button: {e.Message}"); }
        }

        private static void Paint(ActionButton ub) {
            if (current == null) return;
            if (ub.graphic != null) ub.graphic.sprite = Icon();
            if (ub.buttonLabelText != null) ub.buttonLabelText.text = "BOO!";
        }

        private static Sprite Icon() {
            if (icon != null) return icon;
            float w = iconWidth > 0f ? iconWidth : 1f;
            var tex = LobbyArt.BooButton();
            icon = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width / (w * 0.95f));
            icon.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return icon;
        }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        private static class LatePaint {
            [HarmonyPriority(Priority.Last)]
            private static void Postfix(HudManager __instance) {
                try {
                    if (!owned || current == null || __instance.UseButton == null) return;
                    if (__instance.UseButton.currentTarget != null) { owned = false; current = null; return; }
                    Paint(__instance.UseButton);
                } catch { }
            }
        }

        internal static void Release() {
            current = null;
            if (!owned) return;
            owned = false;
            try { if (HudManager.InstanceExists) HudManager.Instance.UseButton.SetTarget(null); } catch { }
        }

        internal static void OnClick() {
            if (!owned || current == null) return;
            if (Time.realtimeSinceStartup < cooldown) return;
            cooldown = Time.realtimeSinceStartup + 0.4f;
            var t = current;
            BooTag.Touch(t);
        }
    }
}
