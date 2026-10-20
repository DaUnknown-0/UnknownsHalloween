// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Omens: everything you see (Omens.cs holds the rules and the network).
 *
 *  - The card: Resources/hw2026/omens/omen_card.png (640x200; picture field x 26-194, text field x 210-614) with
 *    omen_<key>.png (256x256) in the picture field, name and line on the right. Top of the screen, every client.
 *  - Thunderstorm: fx_rain.png (512x512, seamless) scrolls over the screen while the omen holds; a lightning strike
 *    flashes the screen white and lifts the sight for 0.2 s, then 1 s of afterglow (Omens.VisionPatch).
 *  - Raven Omen: fx_raven_1..6.png (128x128 flight frames), three ravens circling over each body.
 * Missing pictures are drawn at runtime (placeholders), so the delivered files only need to be dropped into the
 * folder and embedded (csproj glob), no code change.
 * All screen overlays live on the UI camera (layer 5, above the light system's shadow) with a NEGATIVE sorting
 * order, so they stay under the HUD buttons; only the card sorts above (it sits at the top centre, away from them).
 */

using System;
using System.Collections.Generic;
using System.Linq;
using TMPro;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class OmensFx {
        private const string LogPrefix = Omens.LogPrefix;
        private const string ResRoot = "UnknownsHalloween.Resources.hw2026.";

        // ================================================================ pictures
        internal static byte[] ReadRes(string folder, string file) {
            try {
                using var stream = System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream(ResRoot + folder + "." + file);
                if (stream == null) return null;
                var data = new byte[stream.Length];
                int read = 0;
                while (read < data.Length) {
                    int n = stream.Read(data, read, data.Length - read);
                    if (n <= 0) break;
                    read += n;
                }
                return read == data.Length ? data : null;
            } catch { return null; }
        }

        internal static readonly HashSet<string> fromFile = new();

        /// <summary>A delivered picture as a sprite (1 unit wide), or the runtime drawing.</summary>
        internal static Sprite Load(string folder, string file, Func<TreatFx.Canvas> draw, bool tiled = false) {
            Texture2D tex = null;
            try {
                var data = ReadRes(folder, file);
                if (data != null) {
                    tex = new Texture2D(2, 2, TextureFormat.ARGB32, !tiled) { name = "hw26_" + file };
                    if (ImageConversion.LoadImage(tex, data, false)) {
                        tex.wrapMode = tiled ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
                        tex.filterMode = FilterMode.Bilinear;
                        if (tex.width % 4 == 0 && tex.height % 4 == 0) { try { tex.Compress(true); } catch { } }
                        tex.Apply(false, true);
                        fromFile.Add(folder + "/" + file);
                    } else { UnityEngine.Object.Destroy(tex); tex = null; }
                }
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} picture {file} failed: {e.Message}"); tex = null; }
            if (tex == null) {
                try {
                    var c = draw();
                    tex = c.ToTexture("hw26_" + file);
                    tex.wrapMode = tiled ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
                } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} drawing {file} failed: {e.Message}"); return null; }
            }
            tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            var s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width, 0, SpriteMeshType.FullRect);
            s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return s;
        }

        private static Sprite[] omenIcons;
        internal static Sprite Icon(Omen o) {
            omenIcons ??= new Sprite[(int)Omen.Count];
            int i = Mathf.Clamp((int)o, 0, (int)Omen.Count - 1);
            if (omenIcons[i] == null) omenIcons[i] = Load("omens", $"omen_{Omens.Keys[i]}.png", () => DrawIcon((Omen)i));
            return omenIcons[i];
        }

        private static Sprite cardSprite, rainSprite;
        private static Sprite[] ravenSprites;
        internal static Sprite Card() => cardSprite ??= Load("omens", "omen_card.png", DrawCard);
        internal static Sprite Rain() => rainSprite ??= Load("omens", "fx_rain.png", DrawRain, true);
        internal static Sprite Raven(int frame) {
            ravenSprites ??= new Sprite[6];
            int f = ((frame % 6) + 6) % 6;
            if (ravenSprites[f] == null) ravenSprites[f] = Load("omens", $"fx_raven_{f + 1}.png", () => DrawRaven(f));
            return ravenSprites[f];
        }

        private static Color C(float r, float g, float b, float a = 1f) => new Color(r, g, b, a);

        // ---- placeholders (Canvas has y up: row 0 is the bottom) ----
        internal static TreatFx.Canvas DrawIcon(Omen o) {
            var c = new TreatFx.Canvas(128, 128);
            switch (o) {
                case Omen.Raven:
                    c.Disc(64, 70, 46, C(0.32f, 0.26f, 0.42f, 0.55f));
                    DrawBird(c, 64, 62, 2.4f, 0.4f, C(0.06f, 0.05f, 0.08f));
                    break;
                case Omen.NewMoon:
                    c.Disc(64, 64, 44, C(0.13f, 0.14f, 0.22f));
                    c.Ring(64, 64, 44, 44, 3f, C(0.55f, 0.62f, 0.86f, 0.9f));
                    for (int i = 0; i < 6; i++) c.Disc(16 + i * 19, 112 - (i % 2) * 90, 2.2f, C(0.9f, 0.92f, 1f));
                    break;
                case Omen.FullMoon:
                    c.Disc(64, 64, 52, C(1f, 0.95f, 0.7f, 0.25f));
                    c.Disc(64, 64, 44, C(1f, 0.94f, 0.7f));
                    c.Disc(48, 76, 9, C(0.88f, 0.8f, 0.55f));
                    c.Disc(78, 54, 12, C(0.88f, 0.8f, 0.55f));
                    c.Disc(70, 84, 5, C(0.88f, 0.8f, 0.55f));
                    break;
                case Omen.BatNight:
                    c.Disc(64, 70, 44, C(0.62f, 0.36f, 0.72f, 0.8f));
                    DrawBat(c, 64, 60, 2.6f, 0.2f, C(0.07f, 0.04f, 0.09f));
                    break;
                case Omen.Harvest:
                    c.Ellipse(64, 52, 44, 34, C(0.95f, 0.5f, 0.1f));
                    c.Ellipse(50, 52, 16, 32, C(0.85f, 0.42f, 0.06f));
                    c.Ellipse(78, 52, 16, 32, C(0.85f, 0.42f, 0.06f));
                    c.Ellipse(64, 52, 12, 33, C(1f, 0.58f, 0.16f));
                    c.Rect(60, 82, 68, 100, C(0.36f, 0.5f, 0.16f));
                    c.Tri(68, 96, 88, 104, 72, 90, C(0.4f, 0.62f, 0.2f));
                    break;
                case Omen.SilentNight:
                    c.Disc(64, 64, 42, C(0.85f, 0.92f, 1f));
                    c.Erase(80, 76, 38);
                    for (int i = 0; i < 5; i++) c.Disc(84 + (i % 2) * 18, 30 + i * 18, 2.4f, C(0.9f, 0.95f, 1f));
                    break;
                case Omen.Thunderstorm:
                    c.Ellipse(64, 84, 44, 20, C(0.42f, 0.46f, 0.55f));
                    c.Disc(44, 92, 18, C(0.48f, 0.52f, 0.6f));
                    c.Disc(76, 98, 22, C(0.5f, 0.54f, 0.62f));
                    c.Tri(70, 70, 50, 40, 64, 40, C(1f, 0.9f, 0.3f));
                    c.Tri(60, 46, 74, 46, 52, 10, C(1f, 0.9f, 0.3f));
                    break;
            }
            c.Outline(C(0f, 0f, 0f, 0.85f), 2);
            return c;
        }

        // wing 0..1 = up..down
        internal static void DrawBird(TreatFx.Canvas c, float x, float y, float s, float wing, Color col) {
            c.Ellipse(x, y, 13 * s, 5.5f * s, col);
            c.Disc(x + 13 * s, y + 3 * s, 5 * s, col);
            c.Tri(x + 17 * s, y + 4 * s, x + 25 * s, y + 2 * s, x + 17 * s, y + 0.5f * s, C(0.8f, 0.62f, 0.15f));
            c.Tri(x - 12 * s, y, x - 22 * s, y + 5 * s, x - 22 * s, y - 5 * s, col);
            float wy = Mathf.Lerp(18f, -16f, wing) * s;
            c.Tri(x - 6 * s, y + 2 * s, x + 7 * s, y + 2 * s, x - 9 * s, y + wy, col);
            c.Tri(x - 2 * s, y + 2 * s, x + 9 * s, y + 2 * s, x + 3 * s, y + wy * 0.85f, col);
        }

        internal static void DrawBat(TreatFx.Canvas c, float x, float y, float s, float wing, Color col) {
            c.Ellipse(x, y, 5 * s, 7 * s, col);
            c.Disc(x, y + 8 * s, 4 * s, col);
            c.Tri(x - 3 * s, y + 10 * s, x - 1 * s, y + 10 * s, x - 3.5f * s, y + 15 * s, col);
            c.Tri(x + 3 * s, y + 10 * s, x + 1 * s, y + 10 * s, x + 3.5f * s, y + 15 * s, col);
            float tip = Mathf.Lerp(10f, -8f, wing) * s;
            foreach (int side in new[] { -1, 1 }) {
                c.Tri(x, y + 4 * s, x + side * 22 * s, y + tip + 4 * s, x + side * 4 * s, y - 4 * s, col);
                c.Tri(x + side * 8 * s, y, x + side * 22 * s, y + tip + 4 * s, x + side * 16 * s, y + tip - 4 * s, col);
            }
        }

        private static TreatFx.Canvas DrawCard() {
            var c = new TreatFx.Canvas(640, 200);
            c.Rect(4, 4, 636, 196, C(0.78f, 0.7f, 0.9f));
            c.Rect(9, 9, 631, 191, C(0.1f, 0.07f, 0.15f, 0.97f));
            c.Rect(26, 16, 194, 184, C(0.18f, 0.13f, 0.26f));       // picture field
            c.Rect(214, 126, 610, 129, C(0.5f, 0.42f, 0.62f));      // divider (title above, line below)
            return c;
        }

        private static TreatFx.Canvas DrawRain() {
            var c = new TreatFx.Canvas(128, 128);
            var r = new System.Random(7);
            for (int i = 0; i < 26; i++) {
                float x = r.Next(128), y = r.Next(128), len = 10 + r.Next(14);
                var col = C(0.75f, 0.82f, 1f, 0.35f + (float)r.NextDouble() * 0.35f);
                for (int ox = -128; ox <= 128; ox += 128)          // seamless: wrap every streak
                    for (int oy = -128; oy <= 128; oy += 128)
                        c.Line(x + ox, y + oy, x + ox - len * 0.28f, y + oy - len, 1.1f, col);
            }
            return c;
        }

        private static TreatFx.Canvas DrawRaven(int f) {
            var c = new TreatFx.Canvas(128, 128);
            float wing = 0.5f + 0.5f * Mathf.Sin(f / 6f * Mathf.PI * 2f);
            DrawBird(c, 58, 62, 2.3f, wing, C(0.06f, 0.05f, 0.08f));
            c.Disc(91, 70, 1.6f, C(1f, 0.85f, 0.35f));
            return c;
        }

        // ================================================================ screen helpers
        internal static void Cover(SpriteRenderer sr, float z, float extra = 1.05f) {
            var uiCam = TreatFx.UiCam();
            if (uiCam == null || sr == null) return;
            var c = uiCam.transform.position;
            sr.transform.position = new Vector3(c.x, c.y, z);
            float h = uiCam.orthographicSize * 2.2f;
            sr.transform.localScale = new Vector3(h * uiCam.aspect * extra, h, 1f);
        }

        // ================================================================ the card
        private static GameObject cardRoot;
        private static SpriteRenderer cardBack, cardIcon;
        private static TextMeshPro cardTitle, cardBody;
        private static float cardAt = -100f, cardLife;
        private static Omen cardOmen = Omen.None;
        internal static string CardShown => cardRoot != null && cardRoot.activeSelf ? Omens.Names[(int)cardOmen] : "";

        internal static void ShowCard(Omen o, float life) {
            try {
                if (o == Omen.None || o >= Omen.Count) return;
                var hud = HudManager.InstanceExists ? HudManager.Instance : null;
                if (hud == null) return;
                if (cardRoot == null) {
                    cardRoot = new GameObject("OmenCard") { layer = 5 };
                    cardRoot.transform.SetParent(hud.transform, false);
                    cardBack = TreatFx.UiSr("back", Card(), 300);
                    cardBack.transform.SetParent(cardRoot.transform, false);
                    cardIcon = TreatFx.UiSr("icon", Icon(o), 302);
                    cardIcon.transform.SetParent(cardRoot.transform, false);
                    cardTitle = TreatFx.NewText("OmenCardTitle");
                    if (cardTitle != null) {
                        cardTitle.transform.SetParent(cardRoot.transform, false);
                        cardTitle.alignment = TextAlignmentOptions.BottomLeft;
                        cardTitle.sortingOrder = 305;
                    }
                    cardBody = TreatFx.NewText("OmenCardBody");
                    if (cardBody != null) {
                        cardBody.transform.SetParent(cardRoot.transform, false);
                        cardBody.alignment = TextAlignmentOptions.TopLeft;
                        cardBody.sortingOrder = 305;
                    }
                }
                bool de = TrickOrTreat.De();
                cardOmen = o;
                cardIcon.sprite = Icon(o);
                if (cardTitle != null) cardTitle.text = $"<size=62%><color=#C8B8E8>{(de ? "Omen der Runde" : "Omen of the round")}</color></size>\n<color=#{ColorUtility.ToHtmlStringRGB(Omens.Tints[(int)o])}>{Omens.Names[(int)o]}</color>";
                if (cardBody != null) cardBody.text = Omens.Line(o, de);
                cardAt = Time.time;
                cardLife = life;
                cardRoot.SetActive(true);
                LayoutCard();
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} card failed: {e.Message}"); }
        }

        private const float CardPxW = 640f, CardPxH = 200f;
        private const float IconX = 110f, IconY = 100f, IconPx = 156f;
        private const float TextX = 228f, TextR = 604f, TitleR = 568f,   // the delivered card has a moon top right
                              TitleTop = 20f, TitleBottom = 72f, BodyTop = 84f, BodyBottom = 180f;
        private static float textBase = -1f;

        private static void LayoutCard() {
            var uiCam = TreatFx.UiCam();
            if (uiCam == null || cardRoot == null) return;
            var top = uiCam.ViewportToWorldPoint(new Vector3(0.5f, 0.8f, 10f));
            float w = uiCam.orthographicSize * uiCam.aspect;
            float cw = Mathf.Min(5.8f, w * 1.5f), u = cw / CardPxW;
            float l = top.x - cw / 2f, tp = top.y + CardPxH * u / 2f;
            Vector3 At(float px, float py, float z) => new Vector3(l + px * u, tp - py * u, z);
            cardBack.transform.position = new Vector3(top.x, top.y, -60f);
            cardBack.transform.localScale = new Vector3(cw, cw, 1f);
            cardIcon.transform.position = At(IconX, IconY, -61f);
            float iconUnits = cardIcon.sprite != null ? cardIcon.sprite.bounds.size.x : 1f;
            cardIcon.transform.localScale = Vector3.one * (IconPx * u / Mathf.Max(iconUnits, 0.01f));
            const float ts = 0.42f;
            if (cardTitle != null) {
                if (textBase < 0f) textBase = cardTitle.fontSize;
                cardTitle.transform.position = At(TextX, TitleBottom, -61f);
                cardTitle.transform.localScale = Vector3.one * ts;
                cardTitle.rectTransform.pivot = new Vector2(0f, 0f);
                cardTitle.rectTransform.sizeDelta = new Vector2((TitleR - TextX) * u / ts, (TitleBottom - TitleTop) * u / ts);
                cardTitle.enableWordWrapping = false;
                cardTitle.enableAutoSizing = true;
                cardTitle.fontSizeMax = textBase * 1.15f;
                cardTitle.fontSizeMin = textBase * 0.3f;
            }
            if (cardBody != null) {
                cardBody.transform.position = At(TextX, BodyTop, -61f);
                cardBody.transform.localScale = Vector3.one * ts;
                cardBody.rectTransform.pivot = new Vector2(0f, 1f);
                cardBody.rectTransform.sizeDelta = new Vector2((TextR - TextX) * u / ts, (BodyBottom - BodyTop) * u / ts);
                cardBody.enableWordWrapping = true;
                cardBody.enableAutoSizing = true;
                float b = textBase > 0f ? textBase : cardBody.fontSize;
                cardBody.fontSizeMax = b * 0.7f;
                cardBody.fontSizeMin = b * 0.22f;
            }
        }

        private static void TickCard(bool meeting) {
            if (cardRoot == null || !cardRoot.activeSelf) return;
            float t = Time.time - cardAt;
            if (t > cardLife || meeting) { cardRoot.SetActive(false); return; }
            float a = Mathf.Clamp01(t / 0.3f) * (1f - Mathf.Clamp01((t - (cardLife - 0.8f)) / 0.8f));
            LayoutCard();
            float pop = 1f + 0.12f * Mathf.Max(0f, 1f - t / 0.3f);
            cardIcon.transform.localScale *= pop;
            cardBack.color = new Color(1f, 1f, 1f, a);
            cardIcon.color = new Color(1f, 1f, 1f, a);
            if (cardTitle != null) cardTitle.alpha = a;
            if (cardBody != null) cardBody.alpha = a;
        }

        // ================================================================ thunderstorm
        private static SpriteRenderer rainSr, flashSr;
        private static float strikeAt = -100f;
        private static System.Random stormRng;
        private static float nextStrike = -1f;
        internal static int Strikes;

        internal static void OnOmen() {
            stormRng = null;
            nextStrike = -1f;
            strikeAt = -100f;
            Strikes = 0;
            ClearRavens();
        }

        /// <summary>0..1: how much the lightning lifts the sight right now.</summary>
        internal static float LightningBoost() {
            float t = Time.time - strikeAt;
            if (t < 0f || t > 1.2f) return 0f;
            if (t <= 0.2f) return 1f;
            float k = 1f - (t - 0.2f) / 1f;
            return k * k;
        }

        internal static float FullSight() {
            var main = Camera.main;
            if (main == null) return 8f;
            float h = main.orthographicSize;
            return h * Mathf.Sqrt(1f + main.aspect * main.aspect) + 0.6f;
        }

        internal static void Strike() {
            strikeAt = Time.time;
            Strikes++;
            HalloweenPlugin.Logger?.LogInfo(FormattableString.Invariant($"{LogPrefix} lightning #{Strikes} at {Omens.playClock:F1} s of play"));
        }

        private static void TickStorm(bool hide) {
            bool on = !hide && Omens.current == Omen.Thunderstorm;
            if (on) {
                // the strike times come from the host's seed: every client counts the same play seconds
                stormRng ??= new System.Random(Omens.seed ^ 0x51A7);
                if (nextStrike < 0f) nextStrike = 40f + (float)stormRng.NextDouble() * 50f;
                if (Omens.playClock >= nextStrike) {
                    nextStrike += 40f + (float)stormRng.NextDouble() * 50f;
                    Strike();
                }
            }
            // rain
            if (!on) { if (rainSr != null) rainSr.enabled = false; }
            else {
                if (rainSr == null) {
                    rainSr = TreatFx.UiSr("OmenRain", Rain(), -60);
                    rainSr.drawMode = SpriteDrawMode.Tiled;
                }
                var uiCam = TreatFx.UiCam();
                if (uiCam != null) {
                    const float tile = 2.2f;
                    float hh = uiCam.orthographicSize * 2.3f, ww = hh * uiCam.aspect * 1.1f;
                    rainSr.transform.localScale = Vector3.one * tile;          // the sprite is 1 unit: size in tiles
                    rainSr.size = new Vector2(ww / tile + 2f, hh / tile + 2f);
                    float t = Time.time;
                    float oy = -((t * 3.2f) % 1f) * tile, ox = ((t * 0.9f) % 1f) * tile;
                    var c = uiCam.transform.position;
                    rainSr.transform.position = new Vector3(c.x + ox, c.y + oy, -45f);
                    rainSr.color = new Color(1f, 1f, 1f, 0.55f);
                }
                rainSr.enabled = true;
            }
            // flash
            float ft = Time.time - strikeAt;
            if (hide || ft < 0f || ft > 1.2f) { if (flashSr != null) flashSr.enabled = false; return; }
            if (flashSr == null) flashSr = TreatFx.UiSr("OmenFlash", TreatFx.Pixel(), -58);
            Cover(flashSr, -46f);
            float a;
            if (ft < 0.06f) a = 0.8f;
            else if (ft < 0.1f) a = 0.35f;                 // the flicker
            else if (ft < 0.2f) a = 0.65f;
            else a = 0.22f * (1f - (ft - 0.2f) / 1f);
            flashSr.color = new Color(0.93f, 0.96f, 1f, a);
            flashSr.enabled = true;
        }

        // ================================================================ ravens
        private static readonly Dictionary<byte, SpriteRenderer[]> ravens = new();
        internal static int RavensShown => ravens.Values.Count(a => a != null && a[0] != null && a[0].enabled);

        internal static void TickRavens(List<Omens.Kill> show) {
            var want = new HashSet<byte>();
            if (show != null) {
                float k = TreatFx.UiPerWorld(), t = Time.time;
                foreach (var kill in show) {
                    want.Add(kill.Victim);
                    if (!ravens.TryGetValue(kill.Victim, out var srs) || srs == null || srs[0] == null) {
                        srs = new SpriteRenderer[3];
                        for (int i = 0; i < 3; i++) srs[i] = TreatFx.UiSr("raven", Raven(0), -52);
                        ravens[kill.Victim] = srs;
                    }
                    float since = t - kill.At - Omens.RavenDelay;
                    float fade = Mathf.Clamp01(since / 1.5f);
                    for (int i = 0; i < 3; i++) {
                        float ang = t * (1.1f + 0.15f * i) + i * (Mathf.PI * 2f / 3f) + kill.Victim;
                        float r = 0.9f + 0.15f * Mathf.Sin(t * 0.8f + i * 2f);
                        var world = (Vector3)kill.Pos + new Vector3(Mathf.Cos(ang) * r, 1.5f + Mathf.Sin(ang) * r * 0.35f + 0.08f * Mathf.Sin(t * 2.3f + i), 0f);
                        var sr = srs[i];
                        if (!TreatFx.ToUi(world, out var ui)) { sr.enabled = false; continue; }
                        sr.transform.position = ui + new Vector3(0f, 0f, 0.3f * i);
                        sr.transform.localScale = Vector3.one * 0.75f * k;
                        sr.sprite = Raven((int)(t * 10f) + i * 2);
                        sr.flipX = Mathf.Sin(ang) > 0f;
                        sr.color = new Color(1f, 1f, 1f, fade);
                        sr.enabled = true;
                    }
                }
            }
            foreach (var id in ravens.Keys.ToList()) {
                if (want.Contains(id)) continue;
                foreach (var sr in ravens[id]) if (sr != null) UnityEngine.Object.Destroy(sr.gameObject);
                ravens.Remove(id);
            }
        }

        internal static void ClearRavens() => TickRavens(null);

        // ================================================================ per frame / reset
        internal static void Tick(bool hide) {
            TickCard(hide && TrickOrTreat.InMeeting());
            TickStorm(hide);
            if (hide) ClearRavens();
        }

        internal static void Clear() {
            ClearRavens();
            if (rainSr != null) rainSr.enabled = false;
            if (flashSr != null) flashSr.enabled = false;
            if (cardRoot != null) cardRoot.SetActive(false);
            strikeAt = -100f;
            stormRng = null;
            nextStrike = -1f;
        }
    }
}
