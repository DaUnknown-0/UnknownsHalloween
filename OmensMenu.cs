// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Omens menu (2026-10-20): one card with omens on/off, one switch per omen (which omens lie in the pot, "all on" /
 * "all off"; at least one stays in) and the spook moments on/off (with the midnight moment). Both off by default.
 * Entry: an item in the UTS lobby menu (AppDomain contract "UTS.LobbyMenu.Add", order 61); without UTS a small
 * button of its own in the bottom-left lobby corner, right of the Trick or Treat one.
 * Only the host changes anything; guests see the same card read-only. Sent over module 239 Sub 0 (OmenSettings).
 */

using System;
using UnityEngine;
using UnityEngine.UI;

namespace UnknownsHalloween {
    internal static class OmensMenu {
        private static GameObject root;
        internal static bool IsOpen => root != null;
        private static readonly Color Accent = new Color(0.55f, 0.42f, 0.82f);

        internal static void Toggle() { if (root != null) Close(); else Open(); }
        internal static void Close() { if (root != null) UnityEngine.Object.Destroy(root); root = null; }
        internal static void RefreshIfOpen() { if (root != null) { Close(); Open(); } }

        private static string T(string en, string de) => TrickOrTreat.De() ? de : en;
        private const float W = 1240f, H = 600f, Pad = 34f;

        internal static void Open() {
            try {
                Close();
                bool edit = OmenSettings.CanEdit();
                var r = OmenSettings.Current;
                root = HalloweenUI.Canvas("OmensMenu", 9500, true);
                HalloweenUI.Backdrop(root, Close);
                var card = HalloweenUI.CenterPanel(root, new Vector2(W, H));
                float y = HalloweenUI.Title(card, T("Omens", "Omen"), 16f, 34f, Accent);
                HalloweenUI.Button(card, "X", new Vector2(-HalloweenUI.FrameW - 12f, -HalloweenUI.FrameW - 12f), new Vector2(54f, 54f), HalloweenUI.Red, Close,
                    out _, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 36f);
                HalloweenUI.Text(card, edit
                        ? T("Host settings: saved and sent to every player.", "Host-Einstellungen: gespeichert und an alle Spieler geschickt.")
                        : T("Read only: the host decides.", "Nur lesen: der Host entscheidet."),
                    18f, edit ? HalloweenUI.Muted : HalloweenUI.Warn, new Vector2(Pad + 400f, -36f), new Vector2(700f, 30f));

                Action Do(Action change) => () => {
                    if (!OmenSettings.CanEdit()) return;
                    change();
                    OmenSettings.Changed();
                    RefreshIfOpen();
                };

                // ---- omens ----
                y -= 14f;
                HalloweenUI.Button(card, r.Enabled ? T("On", "An") : T("Off", "Aus"), new Vector2(Pad, y), new Vector2(170f, 56f),
                    r.Enabled ? HalloweenUI.Green : HalloweenUI.Grey, Do(() => r.Enabled = !r.Enabled), out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
                HalloweenUI.Text(card, T("At the start of every round the host draws one omen from the pot. Everybody gets a card, the rule holds for the round.",
                                         "Zu Rundenbeginn zieht der Host ein Omen aus dem Topf. Alle bekommen eine Karte, die Regel gilt die ganze Runde."),
                    18f, HalloweenUI.Muted, new Vector2(Pad + 200f, y - 2f), new Vector2(W - 2 * Pad - 200f, 60f));
                y -= 86f;

                int n = 0;
                for (int i = 0; i < (int)Omen.Count; i++) if ((r.Pot & (1 << i)) != 0) n++;
                y = Section(card, y, T("In the pot", "Im Topf") + $"  ({n}/{(int)Omen.Count})",
                    Do(() => r.Pot = OmenSettings.AllOmens), Do(() => r.Pot = 1 << (int)Omen.FullMoon));
                const int cols = 4;
                float bw = (W - 2 * Pad - (cols - 1) * 12f) / cols;
                for (int i = 0; i < (int)Omen.Count; i++) {
                    int ii = i;
                    bool on = (r.Pot & (1 << i)) != 0;
                    var pos = new Vector2(Pad + (i % cols) * (bw + 12f), y - (i / cols) * 66f);
                    var b = HalloweenUI.Button(card, Omens.Names[i], pos, new Vector2(bw, 56f), on ? Dim(Omens.Tints[i]) : HalloweenUI.Grey,
                        Do(() => { int m = r.Pot ^ (1 << ii); if ((m & OmenSettings.AllOmens) != 0) r.Pot = (byte)m; }), out var txt,
                        new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 19f);
                    txt.rectTransform.offsetMin = new Vector2(54f, 0f);
                    if (!on) txt.color = HalloweenUI.Muted;
                    var icon = new GameObject("Icon");
                    icon.transform.SetParent(b.transform, false);
                    var irt = HalloweenUI.Rect(icon, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(0, 0.5f));
                    irt.anchoredPosition = new Vector2(8f, 0f);
                    irt.sizeDelta = new Vector2(46f, 46f);
                    var img = icon.AddComponent<Image>();
                    img.sprite = OmensFx.Icon((Omen)i);
                    img.preserveAspect = true;
                    img.raycastTarget = false;
                    if (!on) img.color = new Color(1f, 1f, 1f, 0.45f);
                }
                y -= 2 * 66f + 6f;
                bool harvestOff = (r.Pot & (1 << (int)Omen.Harvest)) != 0 && !TreatSettings.Current.Enabled;
                HalloweenUI.Text(card, harvestOff
                        ? T("Harvest only comes up while Trick or Treat is on.", "Harvest kommt nur, wenn Trick or Treat an ist.")
                        : T("Thunderstorm: lightning every 40 to 90 s, rain on screen. Raven Omen: ravens over every body after 20 s.",
                            "Thunderstorm: Blitze alle 40 bis 90 s, Regen auf dem Bild. Raven Omen: Raben über jeder Leiche nach 20 s."),
                    16f, harvestOff ? HalloweenUI.Warn : HalloweenUI.Muted, new Vector2(Pad, y), new Vector2(W - 2 * Pad, 26f));
                y -= 50f;

                // ---- spook moments ----
                HalloweenUI.Text(card, T("Spook moments", "Spukmomente"), 24f, Color.white, new Vector2(Pad, y), new Vector2(600f, 34f), TMPro.FontStyles.Bold);
                y -= 44f;
                HalloweenUI.Button(card, r.Spooks ? T("On", "An") : T("Off", "Aus"), new Vector2(Pad, y), new Vector2(170f, 56f),
                    r.Spooks ? HalloweenUI.Green : HalloweenUI.Grey, Do(() => r.Spooks = !r.Spooks), out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
                HalloweenUI.Text(card, T("Every one to two minutes something harmless happens on the map: a ghost, bats, a spider, a grinning pumpkin. At real midnight on the host's clock the clock strikes twelve for everybody.",
                                         "Alle ein bis zwei Minuten passiert auf der Karte etwas Harmloses: ein Geist, Fledermäuse, eine Spinne, ein grinsender Kürbis. Um echte Mitternacht der Host-Uhr schlägt es für alle zwölf."),
                    18f, HalloweenUI.Muted, new Vector2(Pad + 200f, y - 2f), new Vector2(W - 2 * Pad - 200f, 80f));
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"{Omens.LogPrefix} menu failed: {e}");
                Close();
            }
        }

        private static Color Dim(Color c) => new Color(c.r * 0.6f, c.g * 0.6f, c.b * 0.6f, 1f);

        private static float Section(GameObject card, float y, string title, Action allOn, Action allOff) {
            HalloweenUI.Text(card, title, 24f, Color.white, new Vector2(Pad, y), new Vector2(800f, 34f), TMPro.FontStyles.Bold);
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
                    if (root != null && ShipStatus.Instance != null && !OmensDiag.On) Close();
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

        private static string Label() {
            var r = OmenSettings.Current;
            string s = T("Omens", "Omen");
            if (r.Enabled && r.Spooks) return s + T(" (on, spooks)", " (an, Spuk)");
            if (r.Enabled) return s + T(" (on)", " (an)");
            if (r.Spooks) return s + T(" (spooks)", " (Spuk)");
            return s;
        }

        private static void TryRegister() {
            try {
                if (AppDomain.CurrentDomain.GetData(AddKey) is not Action<string, int, Func<bool>, Func<string>, Action, Color> add) return;
                add("halloween.omens", 61, () => LobbyBehaviour.Instance != null, Label, Open, Accent);
                registered = true;
                if (fallback != null) { UnityEngine.Object.Destroy(fallback); fallback = null; }
                HalloweenPlugin.Logger?.LogInfo($"{Omens.LogPrefix} menu entry added to the UTS lobby menu.");
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{Omens.LogPrefix} lobby menu entry failed: {e.Message}"); registered = true; }
        }

        private static void BuildFallback() {
            try {
                fallback = HalloweenUI.Canvas("OmensButton", 9000, false);
                float x = 20f;
                try { if (AppDomain.CurrentDomain.GetData("UTS.LobbyButtons.NextFreeX") is float f && f > 0f) x = f; } catch { }
                x += 290f;      // right of the Trick or Treat button
                var b = HalloweenUI.Button(fallback, T("Omens", "Omen"), new Vector2(x, 20f), new Vector2(200f, 58f), Accent, Toggle,
                    out var txt, Vector2.zero, Vector2.zero, Vector2.zero, 22f);
                txt.rectTransform.offsetMin = new Vector2(48f, 0f);
                var go = new GameObject("MenuIcon");
                go.transform.SetParent(b.transform, false);
                var rt = HalloweenUI.Rect(go, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(0, 0.5f));
                rt.anchoredPosition = new Vector2(6f, 0f);
                rt.sizeDelta = new Vector2(46f, 46f);
                var img = go.AddComponent<Image>();
                img.sprite = OmensFx.Icon(Omen.FullMoon);
                img.preserveAspect = true;
                img.raycastTarget = false;
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{Omens.LogPrefix} lobby button failed: {e.Message}"); }
        }
    }
}
