// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Trick or Treat menu (2026-10-20, replaces the TOR options 1940-1943): one card with
 *   on/off, the deadly Midnight Bonbon (on/off), candies per meeting, how many meetings whole-round effects last, pickup range,
 *   one switch per candy kind (which kinds show up) and one per effect (which effects go into the pot),
 *   "all on" / "all off" per list.
 * At least one kind and one effect stay on. With fewer active effects than active kinds the effects are
 * handed out twice (TrickOrTreat.EnsureMapping), so any combination is valid.
 *
 * Entry: an item in the UTS lobby menu (AppDomain contract "UTS.LobbyMenu.Add", order 60); without UTS a small
 * button of its own in the bottom-left lobby corner.
 * Only the host changes anything; guests see the same card read-only. The host's choice lives in
 * BepInEx/config/com.daunknown.unknownshalloween.treats.cfg and goes to everyone over module 238 Sub 5:
 * when a player joins, on every change, when the game starts and with the first spawn of the round
 * (the spawn message itself also carries the active kinds and effects).
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
using UnityEngine.UI;

namespace UnknownsHalloween {
    internal sealed class TreatRules {
        public bool Enabled;
        public int Count = 6;
        public int Meetings = 1;
        public int Range = 1;
        public uint Kinds = TreatSettings.AllKinds;
        public uint Effects = TreatSettings.AllEffects;
        public bool Poison = true;              // one Midnight Bonbon per spawn

        public TreatRules Clone() => (TreatRules)MemberwiseClone();

        public void Write(MessageWriter w) {
            w.Write(Enabled);
            w.Write((byte)Count);
            w.Write((byte)Meetings);
            w.Write((byte)Range);
            w.Write((ushort)Kinds);
            w.Write(Effects);
            w.Write(Poison);
        }

        public static TreatRules Read(MessageReader r) => new TreatRules {
            Enabled = r.ReadBoolean(), Count = r.ReadByte(), Meetings = r.ReadByte(), Range = r.ReadByte(),
            Kinds = r.ReadUInt16(), Effects = r.ReadUInt32(), Poison = r.ReadBoolean(),
        };

        public override string ToString() =>
            $"on {Enabled}, {Count} per meeting, {Meetings} meeting(s), range {Range}, kinds {Count1(Kinds)}/12, effects {Count1(Effects)}/{(int)Treat.Count}, deadly {Poison}";
        internal static int Count1(uint m) { int n = 0; while (m != 0) { n += (int)(m & 1); m >>= 1; } return n; }
    }

    internal static class TreatSettings {
        internal const uint AllKinds = (1u << TrickOrTreat.KindCount) - 1;
        internal static readonly uint AllEffects = (1u << (int)Treat.Count) - 1;

        /// <summary>The rules that apply right now: the host's own, or the last ones the host sent.</summary>
        internal static TreatRules Current = new TreatRules();

        private static ConfigFile cfg;
        private static ConfigEntry<bool> cEnabled, cPoison;
        private static ConfigEntry<int> cCount, cMeetings, cRange;
        private static ConfigEntry<string> cKindsOff, cEffectsOff;

        internal static void Load() {
            try {
                cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, "com.daunknown.unknownshalloween.treats.cfg"), true);
                cEnabled = cfg.Bind("Trick or Treat", "Enabled", false, "Candies on the map (host setting, sent to everyone).");
                cCount = cfg.Bind("Trick or Treat", "Candies Per Meeting", 6, "How many candies the host scatters at the start and after every meeting (1-20).");
                cMeetings = cfg.Bind("Trick or Treat", "Round Effects Last Meetings", 1, "Whole-round effects end with this meeting after eating (1-3).");
                cRange = cfg.Bind("Trick or Treat", "Pickup Range", 1, "0 short, 1 normal, 2 long.");
                cPoison = cfg.Bind("Trick or Treat", "Deadly Candy", true, "One Midnight Bonbon per spawn: whoever eats it dies.");
                cKindsOff = cfg.Bind("Trick or Treat", "Disabled Candies", "", "Candy kinds that do not show up, comma separated.");
                cEffectsOff = cfg.Bind("Trick or Treat", "Disabled Effects", "", "Effects that are not in the pot, comma separated.");
                Current = FromConfig();
                HalloweenPlugin.Logger?.LogInfo($"{TrickOrTreat.LogPrefix} rules from the config: {Current}");
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{TrickOrTreat.LogPrefix} config failed: {e}");
            }
        }

        private static TreatRules FromConfig() {
            var r = new TreatRules();
            if (cfg == null) return r;
            r.Enabled = cEnabled.Value;
            r.Count = Mathf.Clamp(cCount.Value, 1, 20);
            r.Meetings = Mathf.Clamp(cMeetings.Value, 1, 3);
            r.Range = Mathf.Clamp(cRange.Value, 0, 2);
            r.Poison = cPoison.Value;
            var koff = Split(cKindsOff.Value);
            r.Kinds = 0;
            for (int k = 0; k < TrickOrTreat.KindCount; k++) if (!koff.Contains(TrickOrTreat.KindNames[k])) r.Kinds |= 1u << k;
            var eoff = Split(cEffectsOff.Value);
            r.Effects = 0;
            for (int i = 0; i < (int)Treat.Count; i++) if (!eoff.Contains(((Treat)i).ToString())) r.Effects |= 1u << i;
            if (r.Kinds == 0) r.Kinds = AllKinds;
            if (r.Effects == 0) r.Effects = AllEffects;
            return r;
        }

        private static HashSet<string> Split(string s) =>
            new HashSet<string>((s ?? "").Split(',').Select(x => x.Trim()).Where(x => x.Length > 0));

        private static void Save() {
            if (cfg == null) return;
            var r = Current;
            cEnabled.Value = r.Enabled;
            cCount.Value = r.Count;
            cMeetings.Value = r.Meetings;
            cRange.Value = r.Range;
            cPoison.Value = r.Poison;
            cKindsOff.Value = string.Join(",", Enumerable.Range(0, TrickOrTreat.KindCount).Where(k => (r.Kinds & (1u << k)) == 0).Select(k => TrickOrTreat.KindNames[k]));
            cEffectsOff.Value = string.Join(",", Enumerable.Range(0, (int)Treat.Count).Where(i => (r.Effects & (1u << i)) == 0).Select(i => ((Treat)i).ToString()));
            try { cfg.Save(); } catch { }
        }

        /// <summary>May this client change the rules? The host, or anybody outside an online lobby (menus, freeplay).</summary>
        internal static bool CanEdit() {
            var ac = AmongUsClient.Instance;
            if (ac == null) return true;
            try { if (ac.NetworkMode == NetworkModes.FreePlay) return true; } catch { }
            return ac.AmHost;
        }

        /// <summary>The host changed something in the menu.</summary>
        internal static void Changed() {
            if (!CanEdit()) return;
            if (Current.Kinds == 0) Current.Kinds = AllKinds;
            if (Current.Effects == 0) Current.Effects = AllEffects;
            Save();
            Broadcast();
        }

        internal static void Broadcast() {
            if (!TrickOrTreat.AmHost()) return;
            var r = Current.Clone();
            TrickOrTreat.Send(TrickOrTreat.SubRules, r.Write);
        }

        internal static void ApplyFromHost(TreatRules r) {
            r.Count = Mathf.Clamp(r.Count, 1, 20);
            r.Meetings = Mathf.Clamp(r.Meetings, 1, 3);
            r.Range = Mathf.Clamp(r.Range, 0, 2);
            bool changed = r.ToString() != Current.ToString() || r.Kinds != Current.Kinds || r.Effects != Current.Effects || r.Poison != Current.Poison;
            Current = r;
            if (changed) {
                HalloweenPlugin.Logger?.LogInfo($"{TrickOrTreat.LogPrefix} rules from the host: {r}");
                TreatMenu.RefreshIfOpen();
            }
        }

        // ---- when to send ----
        private static float sendAt = -1f, resendAt;
        internal static void Tick() {
            if (!TrickOrTreat.AmHost()) return;
            float t = Time.realtimeSinceStartup;
            if (sendAt > 0f && t >= sendAt) { sendAt = -1f; Broadcast(); }
            // in the lobby every 20 s as a safety net (a guest whose join message got lost)
            if (LobbyBehaviour.Instance != null && t >= resendAt) { resendAt = t + 20f; Broadcast(); }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class JoinedPatch {
            public static void Postfix() {
                try {
                    // the host plays by its own config; a guest waits for the host (off until then)
                    if (TrickOrTreat.AmHost()) { Current = FromConfig(); sendAt = Time.realtimeSinceStartup + 1f; }
                    else Current = new TreatRules();
                    TreatMenu.Close();
                } catch { }
            }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnPlayerJoined))]
        static class PlayerJoinedPatch {
            public static void Postfix() { if (TrickOrTreat.AmHost()) sendAt = Time.realtimeSinceStartup + 2f; }
        }

        [HarmonyPatch(typeof(GameStartManager), nameof(GameStartManager.BeginGame))]
        static class BeginGamePatch {
            public static void Postfix() { try { Broadcast(); } catch { } }
        }
    }

    /// <summary>The card itself (screen-space canvas in HalloweenUI's look).</summary>
    internal static class TreatMenu {
        private static GameObject root;
        internal static bool IsOpen => root != null;

        internal static void Toggle() { if (root != null) Close(); else Open(); }

        internal static void Close() {
            if (root != null) UnityEngine.Object.Destroy(root);
            root = null;
        }

        internal static void RefreshIfOpen() { if (root != null) { Close(); Open(); } }

        private static string T(string en, string de) => TrickOrTreat.De() ? de : en;
        private static readonly string[] RangeNames = { "Short", "Normal", "Long" };
        private static readonly string[] RangeNamesDe = { "Kurz", "Normal", "Weit" };

        private const float W = 1580f, H = 960f, Pad = 34f;

        internal static void Open() {
            try {
                Close();
                bool edit = TreatSettings.CanEdit();
                var r = TreatSettings.Current;
                root = HalloweenUI.Canvas("TrickOrTreatMenu", 9500, true);
                HalloweenUI.Backdrop(root, Close);
                var card = HalloweenUI.CenterPanel(root, new Vector2(W, H));
                float y = HalloweenUI.Title(card, "Trick or Treat", 16f, 34f, TrickOrTreat.Orange);
                // the pumpkin pail (candy_menu_icon.png) right of the title tab
                Icon(card, TreatFx.MenuIcon(), new Vector2(HalloweenUI.FrameW + 18f + Mathf.Clamp(14 * 34f * 0.62f + 90f, 260f, 760f) + 14f, -HalloweenUI.FrameW - 6f), 72f,
                     new Vector2(0, 1));
                HalloweenUI.Button(card, "X", new Vector2(-HalloweenUI.FrameW - 12f, -HalloweenUI.FrameW - 12f), new Vector2(54f, 54f), HalloweenUI.Red, Close,
                    out _, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 36f);
                HalloweenUI.Text(card, edit
                        ? T("Host settings: saved and sent to every player.", "Host-Einstellungen: gespeichert und an alle Spieler geschickt.")
                        : T("Read only: the host decides.", "Nur lesen: der Host entscheidet."),
                    18f, edit ? HalloweenUI.Muted : HalloweenUI.Warn, new Vector2(Pad + 560f, -36f), new Vector2(700f, 30f));

                Action Do(Action change) => () => {
                    if (!TreatSettings.CanEdit()) return;
                    change();
                    TreatSettings.Changed();
                    RefreshIfOpen();
                };

                // ---- general row ----
                y -= 14f;
                float x = Pad;
                HalloweenUI.Button(card, r.Enabled ? T("On", "An") : T("Off", "Aus"), new Vector2(x, y), new Vector2(170f, 56f),
                    r.Enabled ? HalloweenUI.Green : HalloweenUI.Grey, Do(() => r.Enabled = !r.Enabled), out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
                x += 200f;
                Stepper(card, ref x, y, T("Candies per meeting", "Süßigkeiten pro Meeting"), r.Count.ToString(),
                    Do(() => r.Count = Mathf.Max(1, r.Count - 1)), Do(() => r.Count = Mathf.Min(20, r.Count + 1)), edit);
                Stepper(card, ref x, y, T("Round effects last", "Rundeneffekte halten"), r.Meetings + (r.Meetings == 1 ? T(" meeting", " Meeting") : T(" meetings", " Meetings")),
                    Do(() => r.Meetings = Mathf.Max(1, r.Meetings - 1)), Do(() => r.Meetings = Mathf.Min(3, r.Meetings + 1)), edit);
                HalloweenUI.Text(card, T("Pickup range", "Aufhebe-Reichweite"), 18f, HalloweenUI.Muted, new Vector2(x, y + 2f), new Vector2(240f, 24f));
                HalloweenUI.Button(card, (TrickOrTreat.De() ? RangeNamesDe : RangeNames)[Mathf.Clamp(r.Range, 0, 2)], new Vector2(x, y - 22f), new Vector2(200f, 44f),
                    HalloweenUI.Blue, Do(() => r.Range = (r.Range + 1) % 3), out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
                x += 230f;
                HalloweenUI.Text(card, T("Deadly candy", "Tödliche Süßigkeit"), 18f, HalloweenUI.Muted, new Vector2(x, y + 2f), new Vector2(300f, 24f));
                var pb = HalloweenUI.Button(card, "Midnight Bonbon", new Vector2(x, y - 22f), new Vector2(300f, 44f),
                    r.Poison ? new Color(0.42f, 0.22f, 0.62f) : HalloweenUI.Grey, Do(() => r.Poison = !r.Poison), out var ptxt,
                    new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 19f);
                ptxt.rectTransform.offsetMin = new Vector2(46f, 0f);
                if (!r.Poison) ptxt.color = HalloweenUI.Muted;
                var pic = new GameObject("Icon");
                pic.transform.SetParent(pb.transform, false);
                var prt = HalloweenUI.Rect(pic, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(0, 0.5f));
                prt.anchoredPosition = new Vector2(6f, 0f);
                prt.sizeDelta = new Vector2(40f, 40f);
                var pimg = pic.AddComponent<Image>();
                pimg.sprite = TreatFx.KindSprite(TrickOrTreat.PoisonKind);
                pimg.preserveAspect = true;
                pimg.raycastTarget = false;
                y -= 96f;

                // ---- candy kinds ----
                y = Section(card, y, T("Candies", "Süßigkeiten") + $"  ({TreatRules.Count1(r.Kinds)}/12)",
                    Do(() => r.Kinds = TreatSettings.AllKinds), Do(() => r.Kinds = 1u));
                const int kCols = 6;
                float kw = (W - 2 * Pad - (kCols - 1) * 12f) / kCols;
                for (int k = 0; k < TrickOrTreat.KindCount; k++) {
                    int kk = k;
                    bool on = (r.Kinds & (1u << k)) != 0;
                    var pos = new Vector2(Pad + (k % kCols) * (kw + 12f), y - (k / kCols) * 62f);
                    var b = HalloweenUI.Button(card, TrickOrTreat.KindNames[k], pos, new Vector2(kw, 52f), on ? HalloweenUI.Green : HalloweenUI.Grey,
                        Do(() => { uint m = r.Kinds ^ (1u << kk); if (m != 0) r.Kinds = m; }), out var txt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 19f);
                    txt.rectTransform.offsetMin = new Vector2(52f, 0f);
                    if (!on) txt.color = HalloweenUI.Muted;
                    var icon = new GameObject("Icon");
                    icon.transform.SetParent(b.transform, false);
                    var irt = HalloweenUI.Rect(icon, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(0, 0.5f));
                    irt.anchoredPosition = new Vector2(8f, 0f);
                    irt.sizeDelta = new Vector2(44f, 44f);
                    var img = icon.AddComponent<Image>();
                    img.sprite = TreatFx.KindSprite(k);
                    img.preserveAspect = true;
                    img.raycastTarget = false;
                    if (!on) img.color = new Color(1f, 1f, 1f, 0.45f);
                }
                y -= 2 * 62f + 18f;

                // ---- effects ----
                int eOn = TreatRules.Count1(r.Effects), kOn = TreatRules.Count1(r.Kinds);
                string note = eOn < kOn ? T($"  fewer effects than candies: some are handed out twice", $"  weniger Effekte als Sorten: manche werden doppelt vergeben") : "";
                y = Section(card, y, T("Effects", "Effekte") + $"  ({eOn}/{(int)Treat.Count}){note}",
                    Do(() => r.Effects = TreatSettings.AllEffects), Do(() => r.Effects = 1u << (int)Treat.SugarRush));
                const int eCols = 5;
                float ew = (W - 2 * Pad - (eCols - 1) * 12f) / eCols;
                for (int i = 0; i < (int)Treat.Count; i++) {
                    int ii = i;
                    bool on = (r.Effects & (1u << i)) != 0;
                    var pos = new Vector2(Pad + (i % eCols) * (ew + 12f), y - (i / eCols) * 54f);
                    var col = on ? Dim(TreatFx.Tint((Treat)i)) : HalloweenUI.Grey;
                    HalloweenUI.Button(card, TreatFx.Name((Treat)i), pos, new Vector2(ew, 44f), col,
                        Do(() => { uint m = r.Effects ^ (1u << ii); if (m != 0) r.Effects = m; }), out var txt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 18f);
                    if (!on) txt.color = HalloweenUI.Muted;
                }
                y -= 6 * 54f;
                HalloweenUI.Text(card, T("Green: helps, red: hinders, purple: odd. The effect of each kind is drawn anew every round.",
                                          "Grün: hilft, Rot: stört, Lila: seltsam. Welche Sorte was bewirkt, wird jede Runde neu gelost."),
                    16f, HalloweenUI.Muted, new Vector2(Pad, y - 6f), new Vector2(W - 2 * Pad, 26f));
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"{TrickOrTreat.LogPrefix} menu failed: {e}");
                Close();
            }
        }

        private static Color Dim(Color c) => new Color(c.r * 0.62f, c.g * 0.62f, c.b * 0.62f, 1f);

        private static void Stepper(GameObject card, ref float x, float y, string label, string value, Action minus, Action plus, bool edit) {
            HalloweenUI.Text(card, label, 18f, HalloweenUI.Muted, new Vector2(x, y + 2f), new Vector2(300f, 24f));
            var c = edit ? HalloweenUI.Teal : HalloweenUI.Grey;
            HalloweenUI.Button(card, "-", new Vector2(x, y - 22f), new Vector2(50f, 44f), c, minus, out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 30f);
            HalloweenUI.Text(card, value, 24f, Color.white, new Vector2(x + 56f, y - 30f), new Vector2(150f, 34f), TMPro.FontStyles.Bold, TMPro.TextAlignmentOptions.Center);
            HalloweenUI.Button(card, "+", new Vector2(x + 212f, y - 22f), new Vector2(50f, 44f), c, plus, out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 30f);
            x += 310f;
        }

        // A section heading with "all on" / "all off"; returns the y below it.
        private static float Section(GameObject card, float y, string title, Action allOn, Action allOff) {
            HalloweenUI.Text(card, title, 24f, Color.white, new Vector2(Pad, y), new Vector2(1000f, 34f), TMPro.FontStyles.Bold);
            float bx = -Pad;
            HalloweenUI.Button(card, T("All off", "Alle aus"), new Vector2(bx, y + 2f), new Vector2(150f, 38f), HalloweenUI.Grey, allOff,
                out _, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 18f);
            HalloweenUI.Button(card, T("All on", "Alle an"), new Vector2(bx - 162f, y + 2f), new Vector2(150f, 38f), HalloweenUI.Green, allOn,
                out _, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 18f);
            return y - 48f;
        }

        // ---- entry: the UTS lobby menu, or our own corner button ----
        private const string AddKey = "UTS.LobbyMenu.Add";
        private static bool registered;
        private static float nextTry, lobbySince = -1f;
        private static GameObject fallback;

        internal static void Tick() {
            try {
                if (root != null && Input.GetKeyDown(KeyCode.Escape)) Close();
                bool lobby = LobbyBehaviour.Instance != null && ShipStatus.Instance == null;
                if (!lobby) {
                    lobbySince = -1f;
                    if (fallback != null) fallback.SetActive(false);
                    if (root != null && ShipStatus.Instance != null && !TrickOrTreatDiag.On) Close();
                    return;
                }
                if (lobbySince < 0f) lobbySince = Time.realtimeSinceStartup;
                if (!registered && Time.realtimeSinceStartup >= nextTry) {
                    nextTry = Time.realtimeSinceStartup + 1f;
                    TryRegister();
                }
                bool wantFallback = !registered && Time.realtimeSinceStartup - lobbySince > 3f;
                if (wantFallback && fallback == null) BuildFallback();
                if (fallback != null && fallback.activeSelf != wantFallback) fallback.SetActive(wantFallback);
            } catch { }
        }

        private static void TryRegister() {
            try {
                if (AppDomain.CurrentDomain.GetData(AddKey) is not Action<string, int, Func<bool>, Func<string>, Action, Color> add) return;
                add("halloween.trickortreat", 60,
                    () => LobbyBehaviour.Instance != null,
                    () => "Trick or Treat" + (TreatSettings.Current.Enabled ? T(" (on)", " (an)") : ""),
                    Open, TrickOrTreat.Orange);
                registered = true;
                if (fallback != null) { UnityEngine.Object.Destroy(fallback); fallback = null; }
                HalloweenPlugin.Logger?.LogInfo($"{TrickOrTreat.LogPrefix} menu entry added to the UTS lobby menu.");
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{TrickOrTreat.LogPrefix} lobby menu entry failed: {e.Message}"); registered = true; }
        }

        private static void Icon(GameObject parent, Sprite sprite, Vector2 pos, float size, Vector2 anchor) {
            if (sprite == null) return;
            var go = new GameObject("MenuIcon");
            go.transform.SetParent(parent.transform, false);
            var rt = HalloweenUI.Rect(go, anchor, anchor, anchor);
            rt.anchoredPosition = pos;
            rt.sizeDelta = new Vector2(size, size);
            var img = go.AddComponent<Image>();
            img.sprite = sprite;
            img.preserveAspect = true;
            img.raycastTarget = false;
        }

        private static void BuildFallback() {
            try {
                fallback = HalloweenUI.Canvas("TrickOrTreatButton", 9000, false);
                float x = 20f;
                try { if (AppDomain.CurrentDomain.GetData("UTS.LobbyButtons.NextFreeX") is float f && f > 0f) x = f; } catch { }
                var b = HalloweenUI.Button(fallback, "Trick or Treat", new Vector2(x, 20f), new Vector2(270f, 58f), TrickOrTreat.Orange, Toggle,
                    out var txt, Vector2.zero, Vector2.zero, Vector2.zero, 22f);
                txt.rectTransform.offsetMin = new Vector2(48f, 0f);
                Icon(b, TreatFx.MenuIcon(), new Vector2(6f, 0f), 46f, new Vector2(0, 0.5f));

            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"{TrickOrTreat.LogPrefix} lobby button failed: {e.Message}");
            }
        }
    }
}
