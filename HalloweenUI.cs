// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * HalloweenUI - a copy of the pieces of Useful TOR Stuff's VanillaUI that the Trick or Treat menu needs
 * (deep blue cards, thick pale outline, capsule buttons, the game's fonts). Copied, not referenced:
 * Unknown's Halloween must not depend on UTS. Keep the look in step with UsefulTORStuff/VanillaUI.cs.
 */

using System;
using System.Collections.Generic;
using Il2CppInterop.Runtime;
using UnityEngine;
using UnityEngine.UI;

namespace UnknownsHalloween {

    internal static class HalloweenUI {
        // ---- Modal lock (audit 21.10., rebuilt 24.10.) ----
        // A uGUI backdrop only swallows uGUI clicks. The game's own buttons are collider-based PassiveButtons and
        // kept reacting under a menu, the hotkeys (use, report, kill, map, TOR's ability keys) fired anyway, and with
        // mouse control a click on a card walked the player towards the cursor. The first lock switched off the
        // PassiveButtons that existed when a menu opened, but buttons made later stayed live, and only two menus used
        // it (User 24.10.: "Trick-or-Treat oder Omens verhindern nicht, dass man im Hintergrund noch weitere Knoepfe
        // drueckt").
        //
        // Now: every blocking canvas (Canvas(..., blocking: true)) counts as an open menu while it is alive and
        // active, no Close call needed. While one is open, prefixes swallow PassiveButton clicks, vanilla's hotkeys
        // (KeyboardJoystick.HandleHud) and TOR's button hotkeys (CustomButton.onClickEvent), and the local player
        // stands still. ModalLock(owner, ...) still works for a menu that wants to block without its own canvas.
        private static readonly HashSet<string> lockOwners = new HashSet<string>();
        private static readonly List<GameObject> modals = new List<GameObject>();
        private static bool frozeHim;
        private static int checkedFrame = -1;
        private static bool openCache;

        /// <summary>Is a Halloween menu open (blocking canvas alive and active, or a ModalLock owner)?</summary>
        internal static string ModalDebug() { var sb = new System.Text.StringBuilder($"owners {lockOwners.Count}, canvases {modals.Count}"); foreach (var g in modals) { try { sb.Append(g == null ? " [null]" : $" [{g.name} self {g.activeSelf} hier {g.activeInHierarchy}]"); } catch (Exception e) { sb.Append(" [ex " + e.Message + "]"); } } return sb.ToString(); }

        internal static bool ModalOpen {
            get {
                int f = Time.frameCount;
                if (f == checkedFrame) return openCache;
                checkedFrame = f;
                bool open = lockOwners.Count > 0;
                for (int i = modals.Count - 1; i >= 0; i--) {
                    var go = modals[i];
                    bool alive = false;
                    try {
                        // 28.10. (DrSuspect: "nur E geht, Mausklicks auf Use usw. nicht"): ein Menue zaehlt nur, solange
                        // seine Canvas aktiv UND eingeschaltet ist; eine ausgeblendete Canvas blockierte sonst unsichtbar
                        var cv = go != null ? go.GetComponent<Canvas>() : null;
                        alive = go != null && go.activeInHierarchy && (cv == null || cv.enabled);
                    } catch { }
                    if (go == null) { modals.RemoveAt(i); continue; }
                    if (alive) open = true;
                }
                if (open && !openCache) LogBlock();
                openCache = open;
                return open;
            }
        }

        // A menu that dies with its scene never calls Close: forget the owners then.
        [HarmonyLib.HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class ModalResetJoin { public static void Postfix() => ModalReset(); }
        [HarmonyLib.HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameEnd))]
        static class ModalResetEnd { public static void Postfix() => ModalReset(); }
        [HarmonyLib.HarmonyPatch(typeof(MainMenuManager), nameof(MainMenuManager.Start))]
        static class ModalResetMenu { public static void Postfix() => ModalReset(); }

        private static float lastBlockLog = -100f;

        /// <summary>Welches Menue gerade sperrt (hoechstens alle 30 s eine Zeile): zeigt bei "Klicks gehen nicht" den Schuldigen.</summary>
        private static void LogBlock() {
            if (Time.realtimeSinceStartup - lastBlockLog < 30f) return;
            lastBlockLog = Time.realtimeSinceStartup;
            try { HalloweenPlugin.Logger?.LogInfo("[Halloween/UI] menu lock on: " + ModalDebug() + " owners: " + string.Join(",", lockOwners)); } catch { }
        }

        internal static void ModalReset() {
            lockOwners.Clear();
            checkedFrame = -1;
            frozeHim = false;
        }

        internal static void ModalLock(string owner, GameObject root, bool on) {
            if (on) lockOwners.Add(owner); else lockOwners.Remove(owner);
            checkedFrame = -1;
        }

        // Swallow clicks on the game's buttons while a menu is open (Il2Cpp methods, safe from tiering).
        [HarmonyLib.HarmonyPatch(typeof(PassiveButton), nameof(PassiveButton.ReceiveClickDown))]
        static class BlockClickDown { public static bool Prefix() => !ModalOpen; }
        [HarmonyLib.HarmonyPatch(typeof(PassiveButton), nameof(PassiveButton.ReceiveClickUp))]
        static class BlockClickUp { public static bool Prefix() => !ModalOpen; }
        [HarmonyLib.HarmonyPatch(typeof(PassiveButton), nameof(PassiveButton.ReceiveRepeatDown))]
        static class BlockRepeat { public static bool Prefix() => !ModalOpen; }

        // Vanilla hotkeys (use, report, kill, map, sabotage).
        [HarmonyLib.HarmonyPatch]
        static class BlockHotkeys {
            static System.Reflection.MethodBase TargetMethod() => HarmonyLib.AccessTools.Method(typeof(KeyboardJoystick), "HandleHud");
            static bool Prepare() => TargetMethod() != null;
            public static bool Prefix() => !ModalOpen;
        }

        // TOR's ability buttons fire their action through CustomButton.onClickEvent (hotkey and click). A managed
        // method: tiering may drop this prefix in a long session, the PassiveButton block still holds the clicks.
        [HarmonyLib.HarmonyPatch]
        static class BlockTorButtons {
            static System.Reflection.MethodBase TargetMethod() =>
                HarmonyLib.AccessTools.Method(typeof(TheOtherRoles.Objects.CustomButton), "onClickEvent");
            static bool Prepare() => TargetMethod() != null;
            public static bool Prefix() => !ModalOpen;
        }

        // Keep the player still while a menu is open (moveable can be set back by the game meanwhile).
        [HarmonyLib.HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class FreezeTick {
            public static void Postfix() {
                try {
                    var lp = PlayerControl.LocalPlayer;
                    if (lp == null) return;
                    if (ModalOpen) {
                        if (lp.moveable) { lp.moveable = false; frozeHim = true; }
                    } else if (frozeHim) {
                        // only what this lock froze; a meeting or exile that started meanwhile handles moveable itself
                        frozeHim = false;
                        if (MeetingHud.Instance == null && ExileController.Instance == null) lp.moveable = true;
                    }
                } catch { }
            }
        }

        internal static readonly Color Frame = new Color(0.72f, 0.78f, 0.84f);         // thick pale outline
        internal static readonly Color Body = new Color(0.09f, 0.11f, 0.15f);
        internal static readonly Color Field = new Color(0.14f, 0.17f, 0.22f);          // section boxes, rows
        internal static readonly Color FieldLight = new Color(0.21f, 0.26f, 0.33f);     // selected / hovered row
        internal static readonly Color TitleColor = Color.white;
        internal static readonly Color TextColor = Color.white;
        internal static readonly Color Muted = new Color(0.66f, 0.72f, 0.80f);
        internal static readonly Color Rule = new Color(0.30f, 0.36f, 0.44f);
        internal static readonly Color Shadow = new Color(0f, 0f, 0f, 0.55f);
        internal static readonly Color BackdropColor = new Color(0f, 0f, 0f, 0.72f);
        // buttons
        internal static readonly Color Teal = new Color(0.16f, 0.70f, 0.66f);
        internal static readonly Color TealBright = new Color(0.36f, 0.88f, 0.82f);     // the selected tab
        internal static readonly Color Green = new Color(0.30f, 0.74f, 0.42f);
        internal static readonly Color Amber = new Color(0.94f, 0.66f, 0.18f);
        internal static readonly Color Red = new Color(0.86f, 0.28f, 0.32f);
        internal static readonly Color Grey = new Color(0.36f, 0.42f, 0.50f);           // neutral
        internal static readonly Color Blue = new Color(0.30f, 0.56f, 0.90f);
        internal static readonly Color Pink = new Color(0.90f, 0.42f, 0.74f);
        // status text
        internal static readonly Color Good = new Color(0.62f, 1f, 0.63f);
        internal static readonly Color Warn = new Color(1f, 0.82f, 0.5f);
        internal static readonly Color Bad = new Color(1f, 0.5f, 0.5f);

        internal const float FrameW = 5f;                                              // the outline's width
        internal const int RadiusPanel = 22, RadiusBox = 10, RadiusButton = 16, RadiusTile = 12;
        // ====================================================================
        // Canvas and backdrop
        // ====================================================================
        public static GameObject Canvas(string name, int order, bool blocking) {
            var go = new GameObject(name);
            UnityEngine.Object.DontDestroyOnLoad(go);
            var canvas = go.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = order;
            var scaler = go.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            var ray = go.AddComponent<GraphicRaycaster>();
            if (blocking) {
                ray.blockingObjects = GraphicRaycaster.BlockingObjects.All;
                modals.Add(go);                          // counts as an open menu while alive and active (ModalOpen)
                checkedFrame = -1;
            }
            return go;
        }

        /// <summary>Dims the whole screen; a click on it runs onClick (usually: close).</summary>
        public static GameObject Backdrop(GameObject root, Action onClick) {
            var go = new GameObject("Backdrop");
            go.transform.SetParent(root.transform, false);
            Stretch(go);
            var img = go.AddComponent<Image>();
            img.sprite = Solid();
            img.color = BackdropColor;
            if (onClick != null) go.AddComponent<Button>().onClick.AddListener((UnityEngine.Events.UnityAction)(() => onClick()));
            return go;
        }

        // ====================================================================
        // Panel: frame + body + shadow. Children are placed on the returned object, so the frame
        // width has to be allowed for (FrameW on every side).
        // ====================================================================
        public static GameObject Panel(GameObject parent, Vector2 size, Vector2 anchor, Vector2 pivot, Vector2 pos) {
            var go = new GameObject("Panel");
            go.transform.SetParent(parent.transform, false);
            var rt = Rect(go, anchor, anchor, pivot);
            rt.sizeDelta = size; rt.anchoredPosition = pos;

            // hard offset shadow, dark body, thick pale outline on top (the game's heavy-outline look)
            Stretch(Named(Rounded(go, Shadow, RadiusPanel), "Shadow")).anchoredPosition = new Vector2(8, -10);
            var body = Rounded(go, Body, RadiusPanel);
            Stretch(body);
            body.GetComponent<Image>().raycastTarget = true;   // swallows clicks so the backdrop behind does not close
            Stretch(Ring(go, Frame, RadiusPanel, (int)FrameW));
            return go;
        }
        /// <summary>A panel centred on the screen.</summary>
        public static GameObject CenterPanel(GameObject root, Vector2 size) =>
            Panel(root, size, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero);

        public static float Title(GameObject panel, string text, float top = 16f, float size = 34f, Color? color = null) {
            // a slanted tab in the accent colour hanging from the top-left corner, the title on it
            float h = size * 1.2f + 14f;
            float w = Mathf.Clamp(text.Length * size * 0.62f + 90f, 260f, 760f);
            var tab = new GameObject("TitleTab");
            tab.transform.SetParent(panel.transform, false);
            var trt = Rect(tab, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
            trt.anchoredPosition = new Vector2(FrameW + 18f, -FrameW - top + 6f);
            trt.sizeDelta = new Vector2(w, h);
            var img = tab.AddComponent<Image>();
            img.sprite = Slant();
            img.type = Image.Type.Sliced;
            img.color = color ?? Teal;
            img.raycastTarget = false;

            var t = Label(tab, text, size * 1.15f, TitleColor, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f),
                          Vector2.zero, new Vector2(-60f, 0f), TMPro.TextAlignmentOptions.Left, TMPro.FontStyles.UpperCase);
            t.rectTransform.offsetMin = new Vector2(22f, 0f);
            Heading(t);
            return -FrameW - top - h - 4f;
        }

        /// <summary>
        /// Gives a label the game's handwriting heading face (Brook) when it has the glyphs, and marks it
        /// so SetText keeps that face on later text changes.
        /// </summary>
        public static void Heading(TMPro.TextMeshProUGUI t) {
            if (t == null) return;
            t.gameObject.name = "H";
            var f = HeadingFont();
            if (f != null && GlyphsOk(f, t.text)) { t.font = f; t.fontStyle &= ~TMPro.FontStyles.Bold; }
            t.characterSpacing = 1f;
        }
        // ====================================================================
        // Buttons
        // ====================================================================
        public static GameObject Button(GameObject parent, string label, Vector2 pos, Vector2 size, Color color, Action onClick,
                                        out TMPro.TextMeshProUGUI text, Vector2? anchorMin = null, Vector2? anchorMax = null,
                                        Vector2? pivot = null, float fontSize = 0f) {
            var go = new GameObject("Btn");
            go.transform.SetParent(parent.transform, false);
            var rt = Rect(go, anchorMin ?? new Vector2(0.5f, 0), anchorMax ?? new Vector2(0.5f, 0), pivot ?? new Vector2(0.5f, 0));
            rt.anchoredPosition = pos; rt.sizeDelta = size;

            // a capsule: flat colour, hard drop shadow, a darker outline of the same hue
            int radius = Mathf.Clamp(Mathf.RoundToInt(size.y / 2f) - 1, 4, 30);
            Stretch(Named(Rounded(go, Shadow, radius), "Shadow")).anchoredPosition = new Vector2(3, -5);
            var fill = Rounded(go, color, radius);
            Stretch(fill);
            var edge = Ring(go, Darker(color), radius, 3);
            edge.name = "Edge";
            Stretch(edge);

            if (fontSize <= 0f) fontSize = Mathf.Clamp(size.y * 0.6f, 15f, 34f);
            text = Label(go, label, fontSize, LabelColor(color), Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f),
                         Vector2.zero, new Vector2(-14, 0), TMPro.TextAlignmentOptions.Center, TMPro.FontStyles.UpperCase);
            Heading(text);
            text.enableAutoSizing = true; text.fontSizeMin = 11; text.fontSizeMax = fontSize;
            text.enableWordWrapping = false;

            Hover(go, RadiusButton, onClick);
            return go;
        }

        public static GameObject Button(GameObject parent, string label, Vector2 pos, Vector2 size, Color color, Action onClick,
                                        Vector2? anchorMin = null, Vector2? anchorMax = null, Vector2? pivot = null) =>
            Button(parent, label, pos, size, color, onClick, out _, anchorMin, anchorMax, pivot);

        /// <summary>
        /// The close control of every panel: the game's white square with a black X in the top-right
        /// corner (the label is kept for callers, the X needs none).
        /// </summary>
        public static GameObject CloseButton(GameObject panel, string label, Action onClose, float width = 240f) {
            var go = Button(panel, "X", new Vector2(-FrameW - 10f, -FrameW - 10f), new Vector2(54f, 54f), Red, onClose,
                            out var text, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), 40f);
            go.name = "Close";
            text.fontStyle |= TMPro.FontStyles.Bold;
            return go;
        }

        /// <summary>Recolours a button built by Button(): fill, outline and label.</summary>
        public static void Recolor(GameObject button, Color color) {
            if (button == null) return;
            var fill = button.transform.Find("Fill");
            if (fill != null) fill.GetComponent<Image>().color = color;
            var edge = button.transform.Find("Edge");
            if (edge != null) edge.GetComponent<Image>().color = Darker(color);
            var t = button.GetComponentInChildren<TMPro.TextMeshProUGUI>();
            if (t != null) t.color = LabelColor(color);
        }

        private static Color Darker(Color c) => new Color(c.r * 0.55f, c.g * 0.55f, c.b * 0.55f, c.a);

        // white labels like the game's buttons; dark only on a nearly white fill
        public static Color LabelColor(Color fill) {
            float lum = 0.299f * fill.r + 0.587f * fill.g + 0.114f * fill.b;
            return lum < 0.8f ? Color.white : new Color(0.1f, 0.1f, 0.1f);
        }
        // ====================================================================
        // Text
        // ====================================================================
        public static TMPro.TextMeshProUGUI Label(GameObject parent, string text, float size, Color color,
                Vector2 anchorMin, Vector2 anchorMax, Vector2 pivot, Vector2 pos, Vector2 sizeDelta,
                TMPro.TextAlignmentOptions align, TMPro.FontStyles style = TMPro.FontStyles.Normal) {
            var go = new GameObject("L");
            go.transform.SetParent(parent.transform, false);
            var rt = Rect(go, anchorMin, anchorMax, pivot);
            rt.anchoredPosition = pos; rt.sizeDelta = sizeDelta;
            var t = go.AddComponent<TMPro.TextMeshProUGUI>();
            t.fontSize = size; t.fontStyle = style; t.color = color;
            t.alignment = align; t.enableWordWrapping = true;
            t.raycastTarget = false;
            SetText(t, text);
            return t;
        }

        /// <summary>Text positioned by its top-left corner, top-left aligned.</summary>
        public static TMPro.TextMeshProUGUI Text(GameObject parent, string text, float size, Color color, Vector2 topLeft, Vector2 box,
                                                 TMPro.FontStyles style = TMPro.FontStyles.Normal,
                                                 TMPro.TextAlignmentOptions align = TMPro.TextAlignmentOptions.TopLeft) =>
            Label(parent, text, size, color, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), topLeft, box, align, style);

        /// <summary>Sets the text and picks the font: the game's where it has every glyph, TMP's default otherwise.</summary>
        public static void SetText(TMPro.TextMeshProUGUI t, string text) {
            if (t == null) return;
            text = text ?? "";
            // labels marked by Heading() keep the handwriting face while it has the glyphs
            var game = t.gameObject.name == "H" ? HeadingFont() : null;
            if (game == null || !GlyphsOk(game, text)) game = Font();
            var target = game != null && GlyphsOk(game, text) ? game : DefaultFont();
            if (target != null && t.font != target) t.font = target;
            if (t.text != text) t.text = text;
        }

        private static TMPro.TMP_FontAsset gameFont, headingFont, defaultFont;
        private static float fontSearchedAt = -100f;
        private static bool fontsLogged;

        private static TMPro.TMP_FontAsset DefaultFont() {
            if (defaultFont == null) { try { defaultFont = TMPro.TMP_Settings.defaultFontAsset; } catch { } }
            return defaultFont;
        }

        /// <summary>The game's body face (Barlow, upright bold) for labels and values.</summary>
        public static TMPro.TMP_FontAsset Font() {
            if (gameFont == null) SearchFonts();
            return gameFont;
        }

        /// <summary>The game's handwriting heading face (Brook: GAME SETTINGS, PLAY, EDIT), null until found.</summary>
        public static TMPro.TMP_FontAsset HeadingFont() {
            if (headingFont == null) SearchFonts();
            return headingFont;
        }

        // Both faces are picked by name from the loaded font assets (once every few seconds until
        // found). Picking by name, not from a HUD label: the lobby's player counter turned out to be
        // the italic Barlow cut (2026-10-07), which made every panel look slanted.
        private static void SearchFonts() {
            if (Time.realtimeSinceStartup - fontSearchedAt < 3f) return;
            fontSearchedAt = Time.realtimeSinceStartup;
            try {
                var all = Resources.FindObjectsOfTypeAll(Il2CppType.Of<TMPro.TMP_FontAsset>());
                var names = new List<string>();
                int bodyScore = -1, headScore = -1;
                foreach (var o in all) {
                    var f = o.TryCast<TMPro.TMP_FontAsset>();
                    if (f == null) continue;
                    names.Add(f.name);
                    string n = f.name.ToLowerInvariant();
                    if (n.Contains("outline") || n.Contains("italic") || n.Contains("masked")) continue;
                    if (n.Contains("barlow")) {
                        // the plain bold cut first, then any upright Barlow
                        int score = n.Contains("bold") ? 3 : n.Contains("semibold") ? 2 : 1;
                        if (score > bodyScore) { bodyScore = score; gameFont = f; }
                    } else if (n.Contains("brook")) {
                        int score = n.Contains("sdf") ? 2 : 1;
                        if (score > headScore) { headScore = score; headingFont = f; }
                    }
                }
                if (!fontsLogged && names.Count > 0) {
                    fontsLogged = true;
                    HalloweenPlugin.Logger?.LogInfo($"[VanillaUI] fonts: body={(gameFont != null ? gameFont.name : "-")}, "
                        + $"heading={(headingFont != null ? headingFont.name : "-")}; loaded: {string.Join(", ", names)}");
                }
            } catch (Exception ex) {
                HalloweenPlugin.Logger?.LogWarning($"[VanillaUI] font search failed: {ex.Message}");
            }
        }

        private static bool GlyphsOk(TMPro.TMP_FontAsset font, string text) {
            try { return font.HasCharacters(text); } catch { return false; }
        }
        private static Sprite Draw(int w, int h, Func<float, float, float> alpha) {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var px = new Color[w * h];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                    px[y * w + x] = new Color(1f, 1f, 1f, alpha(x + 0.5f, h - (y + 0.5f)));   // y down, like a drawing
            tex.SetPixels(px);
            tex.filterMode = FilterMode.Bilinear;
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply(false, true);
            var s = Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 100f);
            tex.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            s.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            return s;
        }
        // ====================================================================
        // Shapes
        // ====================================================================
        private static Sprite solid;

        public static Sprite Solid() {
            if (solid != null) return solid;
            var tex = new Texture2D(1, 1);
            tex.SetPixel(0, 0, Color.white);
            tex.Apply();
            solid = Sprite.Create(tex, new Rect(0, 0, 1, 1), new Vector2(0.5f, 0.5f));
            tex.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            solid.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            return solid;
        }

        /// <summary>A filled, sliced rounded rectangle with the given corner radius (canvas units).</summary>
        // the drop shadows are Rounded too; renamed so Find("Fill") gets the real fill
        private static GameObject Named(GameObject go, string name) { go.name = name; return go; }

        public static GameObject Rounded(GameObject parent, Color color, int radius) {
            var go = new GameObject(radius <= 1 ? "Rule" : "Fill");
            go.transform.SetParent(parent.transform, false);
            go.AddComponent<RectTransform>();
            var img = go.AddComponent<Image>();
            img.sprite = RoundedSprite(Mathf.Max(radius, 1));
            img.type = Image.Type.Sliced;
            img.color = color;
            img.raycastTarget = false;
            return go;
        }

        private static readonly Dictionary<int, Sprite> roundedCache = new Dictionary<int, Sprite>();

        public static Sprite RoundedSprite(int radius) {
            if (roundedCache.TryGetValue(radius, out var cached) && cached != null) return cached;
            int n = radius * 2 + 4;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
            var px = new Color[n * n];
            float half = n / 2f;
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++) {
                    float qx = Mathf.Abs(x + 0.5f - half) - (half - radius);
                    float qy = Mathf.Abs(y + 0.5f - half) - (half - radius);
                    float outside = new Vector2(Mathf.Max(qx, 0), Mathf.Max(qy, 0)).magnitude + Mathf.Min(Mathf.Max(qx, qy), 0) - radius;
                    px[y * n + x] = new Color(1f, 1f, 1f, Mathf.Clamp01(0.5f - outside));
                }
            tex.SetPixels(px);
            tex.filterMode = FilterMode.Bilinear;
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply(false, true);
            float b = radius + 2;
            var sprite = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f, 0,
                                       SpriteMeshType.FullRect, new Vector4(b, b, b, b));
            tex.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            sprite.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            roundedCache[radius] = sprite;
            return sprite;
        }

        /// <summary>A rounded ring (outline only) of the given radius and border width, sliced.</summary>
        public static GameObject Ring(GameObject parent, Color color, int radius, int border) {
            var go = new GameObject("Outline");
            go.transform.SetParent(parent.transform, false);
            go.AddComponent<RectTransform>();
            var img = go.AddComponent<Image>();
            img.sprite = RingSprite(Mathf.Max(radius, 2), Mathf.Clamp(border, 1, radius));
            img.type = Image.Type.Sliced;
            img.color = color;
            img.raycastTarget = false;
            return go;
        }

        private static readonly Dictionary<int, Sprite> ringCache = new Dictionary<int, Sprite>();

        private static Sprite RingSprite(int radius, int border) {
            int key = radius * 100 + border;
            if (ringCache.TryGetValue(key, out var cached) && cached != null) return cached;
            int n = radius * 2 + 4;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
            var px = new Color[n * n];
            float half = n / 2f;
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++) {
                    float qx = Mathf.Abs(x + 0.5f - half) - (half - radius);
                    float qy = Mathf.Abs(y + 0.5f - half) - (half - radius);
                    float outside = new Vector2(Mathf.Max(qx, 0), Mathf.Max(qy, 0)).magnitude + Mathf.Min(Mathf.Max(qx, qy), 0) - radius;
                    float a = Mathf.Clamp01(0.5f - outside) * Mathf.Clamp01(outside + border + 0.5f);
                    px[y * n + x] = new Color(1f, 1f, 1f, a);
                }
            tex.SetPixels(px);
            tex.filterMode = FilterMode.Bilinear;
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply(false, true);
            float b = radius + 2;
            var sprite = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f, 0,
                                       SpriteMeshType.FullRect, new Vector4(b, b, b, b));
            tex.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            sprite.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            ringCache[key] = sprite;
            return sprite;
        }

        // The slanted tab of the settings screen's section headers ("IMPOSTORS"): square on the
        // left, the right edge leaning. Sliced so the slant keeps its angle at any width.
        private static Sprite slant;

        public static Sprite Slant() {
            if (slant != null) return slant;
            const int h = 48, lean = 22, w = 40 + lean + 8;
            slant = Draw(w, h, (x, y) => {
                // left and bottom edges straight, top-left corner rounded (r 8), right edge leaning
                float r = 8f;
                float cx = Mathf.Max(x, r), cy = Mathf.Min(y, h - r);
                float corner = (x < r && y > h - r) ? Mathf.Clamp01(r - Mathf.Sqrt((x - r) * (x - r) + (y - (h - r)) * (y - (h - r))) + 0.5f) : 1f;
                float rightEdge = w - 1f - lean * (1f - y / h);   // leans: wide at the bottom, narrow at the top
                float a = Mathf.Clamp01(rightEdge - x + 0.5f);
                return corner * a;
            });
            slant = Sprite.Create(slant.texture, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 100f, 0,
                                  SpriteMeshType.FullRect, new Vector4(12, 2, lean + 8, 2));
            slant.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            return slant;
        }

        // A translucent veil over the whole target: invisible at rest, white on hover, dark while pressed.
        public static void Hover(GameObject target, int radius, Action onClick) {
            // the Button tints the image's own colour, so that stays white and the states carry the alpha
            var veil = Rounded(target, Color.white, radius);
            Stretch(veil);
            var vimg = veil.GetComponent<Image>();
            vimg.raycastTarget = true;
            var b = veil.AddComponent<Button>();
            b.targetGraphic = vimg;
            var c = b.colors;
            c.normalColor = new Color(1f, 1f, 1f, 0f);
            c.highlightedColor = new Color(1f, 1f, 1f, 0.2f);
            c.pressedColor = new Color(0f, 0f, 0f, 0.25f);
            c.selectedColor = new Color(1f, 1f, 1f, 0f);
            c.colorMultiplier = 1f;
            c.fadeDuration = 0.06f;
            b.colors = c;
            // the Button applies its normal colour in Start, one frame later: without this the veil is
            // solid white for that frame (seen as a white flash and bleached screenshots, 2026-10-07)
            vimg.CrossFadeColor(c.normalColor, 0f, true, true);
            if (onClick != null) b.onClick.AddListener((UnityEngine.Events.UnityAction)(() => onClick()));
        }
        // ====================================================================
        // Rect helpers
        // ====================================================================
        public static RectTransform Rect(GameObject go, Vector2 anchorMin, Vector2 anchorMax, Vector2 pivot) {
            var rt = go.GetComponent<RectTransform>();
            if (rt == null) rt = go.AddComponent<RectTransform>();
            rt.anchorMin = anchorMin; rt.anchorMax = anchorMax; rt.pivot = pivot;
            return rt;
        }

        public static RectTransform Stretch(GameObject go) {
            var rt = Rect(go, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f));
            rt.sizeDelta = Vector2.zero; rt.anchoredPosition = Vector2.zero;
            return rt;
        }

        public static RectTransform Inset(RectTransform rt, float margin) {
            rt.offsetMin = new Vector2(margin, margin);
            rt.offsetMax = new Vector2(-margin, -margin);
            return rt;
        }

        /// <summary>Canvas scale factor of a screen-space canvas (for screen-to-canvas conversions).</summary>
        public static float Scale(GameObject canvasRoot) {
            var c = canvasRoot != null ? canvasRoot.GetComponent<Canvas>() : null;
            return c != null && c.scaleFactor > 0f ? c.scaleFactor : 1f;
        }
    }
}
