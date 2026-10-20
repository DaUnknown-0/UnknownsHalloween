// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Artwork of the two game modes (Zombie Outbreak, Final Girl).
 *
 * Every picture is looked up first as a delivered file under Resources/hw2026/zombie/ (embedded through the
 * wildcard in UnknownsHalloween.csproj, or from an asset package), and only when it is missing a placeholder is
 * painted at runtime. The graphics session can therefore drop the real files in without any code change:
 *   zombie_infect_button.png  256 x 256   the infect button
 *   zombie_tint_overlay.png   256 x 256   seamless tile, the zombie's own green view (drawn tiled, faint)
 *   exit_portal_<1-8>.png     200 x 200   the Final Girl exit, eight animation frames
 *   finalgirl_arrow.png        64 x 64    the survivors' arrow to the exit (pointing right, like TOR's arrow)
 */

using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HalloweenModeArt {
        private const string ResPrefix = "UnknownsHalloween.Resources.hw2026.zombie.";
        private static readonly Dictionary<string, Sprite> cache = new();

        private static void Keep(UnityEngine.Object o) { if (o != null) o.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset; }

        /// <summary>The delivered file as a sprite, or null when it is not there.</summary>
        private static Sprite Delivered(string file, float ppu, bool tiled) {
            try {
                var data = HalloweenAssets.Read(ResPrefix + file);
                if (data == null || data.Length == 0) return null;
                var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (!ImageConversion.LoadImage(tex, data, false)) return null;
                tex.wrapMode = tiled ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
                Keep(tex);
                var sp = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), ppu, 0, SpriteMeshType.FullRect);
                Keep(sp);
                return sp;
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"[HalloweenModes] art {file}: {e.Message}");
                return null;
            }
        }

        private static Sprite Painted(int w, int h, float ppu, bool tiled, Func<int, int, Color> px) {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { wrapMode = tiled ? TextureWrapMode.Repeat : TextureWrapMode.Clamp };
            var arr = new Color32[w * h];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++) arr[y * w + x] = px(x, y);
            tex.SetPixels32(arr);
            tex.Apply(false, false);
            Keep(tex);
            var sp = Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), ppu, 0, SpriteMeshType.FullRect);
            Keep(sp);
            return sp;
        }

        private static Sprite Get(string key, Func<Sprite> load) {
            if (cache.TryGetValue(key, out var s) && s != null) return s;
            s = load();
            cache[key] = s;
            return s;
        }

        /// <summary>True when the delivered file exists (for the log of the self test).</summary>
        internal static bool HasDelivered(string file) {
            try { return HalloweenAssets.Exists(ResPrefix + file); } catch { return false; }
        }

        // ---- infect button: dark green disc, light rim, three red claw marks ----
        internal static Sprite InfectButton() => Get("infect", () => Delivered("zombie_infect_button.png", 230f, false) ?? Painted(256, 256, 230f, false, (x, y) => {
            float dx = x - 127.5f, dy = y - 127.5f, r = Mathf.Sqrt(dx * dx + dy * dy) / 120f;
            if (r > 1f) return new Color(0, 0, 0, 0);
            float edge = Mathf.Clamp01((1f - r) * 30f);
            var c = Color.Lerp(new Color(0.10f, 0.28f, 0.08f), new Color(0.30f, 0.62f, 0.18f), 1f - r);
            if (r > 0.88f) c = new Color(0.62f, 0.95f, 0.35f);
            // three slanted claw marks
            for (int k = -1; k <= 1; k++) {
                float u = (dx * 0.80f + dy * 0.60f) - k * 34f;     // across the stroke
                float v = (-dx * 0.60f + dy * 0.80f);               // along the stroke
                float len = 70f - Mathf.Abs(k) * 12f;
                float wdt = 9f * Mathf.Clamp01(1f - Mathf.Abs(v) / len);
                if (Mathf.Abs(v) < len && Mathf.Abs(u) < wdt) c = Color.Lerp(new Color(0.55f, 0.02f, 0.02f), new Color(0.95f, 0.15f, 0.1f), Mathf.Abs(u) / Mathf.Max(1f, wdt));
            }
            c.a = edge;
            return c;
        }));

        // ---- seamless green tile: integer frequencies on the 256 period keep the edges matching ----
        internal static Sprite TintOverlay() => Get("tint", () => Delivered("zombie_tint_overlay.png", 64f, true) ?? Painted(256, 256, 64f, true, (x, y) => {
            float tx = x / 256f * Mathf.PI * 2f, ty = y / 256f * Mathf.PI * 2f;
            float n = Mathf.Sin(tx * 3f + 1.3f) * Mathf.Cos(ty * 2f + 0.4f) * 0.5f
                    + Mathf.Sin(tx * 5f + ty * 4f + 2.1f) * 0.3f
                    + Mathf.Cos(tx * 9f - ty * 7f + 0.7f) * 0.2f;
            float v = 0.5f + 0.5f * n;
            return new Color(0.25f + 0.15f * v, 0.75f + 0.2f * v, 0.15f, 0.35f + 0.65f * v);
        }));

        // ---- exit portal: warm light ring with turning spiral arms, eight frames ----
        private static Sprite[] portal;
        internal static Sprite[] ExitPortal() {
            if (portal != null) return portal;
            var frames = new Sprite[8];
            for (int i = 0; i < 8; i++) {
                int f = i;
                frames[i] = Delivered($"exit_portal_{i + 1}.png", 100f, false) ?? Painted(200, 200, 100f, false, (x, y) => {
                    float dx = x - 99.5f, dy = y - 99.5f, r = Mathf.Sqrt(dx * dx + dy * dy) / 96f;
                    if (r > 1f) return new Color(0, 0, 0, 0);
                    float ang = Mathf.Atan2(dy, dx) + f * (Mathf.PI * 2f / 8f / 3f);
                    float spiral = 0.5f + 0.5f * Mathf.Sin(ang * 3f + r * 9f);
                    float ring = Mathf.Clamp01(1f - Mathf.Abs(r - 0.82f) / 0.12f);
                    float core = Mathf.Clamp01(1f - r / 0.45f);
                    float a = Mathf.Max(ring, Mathf.Max(core * 0.9f, spiral * 0.55f * (1f - r)));
                    var c = Color.Lerp(new Color(1f, 0.55f, 0.75f), new Color(1f, 0.97f, 0.85f), Mathf.Max(core, ring * 0.6f));
                    c.a = Mathf.Clamp01(a) * Mathf.Clamp01((1f - r) * 12f);
                    return c;
                });
            }
            portal = frames;
            return portal;
        }

        // ---- arrow to the exit: pointing right like TOR's Arrow.png (150 px at 200 ppu -> 64 px at 85 ppu) ----
        internal static Sprite Arrow() => Get("arrow", () => Delivered("finalgirl_arrow.png", 85f, false) ?? Painted(64, 64, 85f, false, (x, y) => {
            float px = x + 0.5f, py = y + 0.5f - 32f;
            // triangle from (8, +-26) to (58, 0) with a notch at the back
            float t = (px - 8f) / 50f;
            if (t < 0f || t > 1f) return new Color(0, 0, 0, 0);
            float half = 26f * (1f - t);
            float notch = px < 22f ? (22f - px) * 1.2f : 0f;     // the V cut into the back
            if (Mathf.Abs(py) > half || Mathf.Abs(py) < notch) return new Color(0, 0, 0, 0);
            bool rim = Mathf.Abs(py) > half - 3.5f || px > 55f;
            return rim ? new Color(0.25f, 0.05f, 0.12f, 1f) : Color.Lerp(new Color(1f, 0.45f, 0.7f), new Color(1f, 0.85f, 0.92f), Mathf.Clamp01(0.5f + py / 52f));
        }));

        /// <summary>Darkness with a light: a small circle around the player and a cone towards +x (Atlas' blackout recipe).</summary>
        private static Sprite cone;
        internal const float ConeWorld = 30f;
        internal static Sprite FlashlightCone() {
            if (cone != null) return cone;
            const int N = 512;
            float ppu = N / ConeWorld;
            cone = Painted(N, N, ppu, false, (x, y) => {
                float wx = (x + 0.5f - N / 2f) / ppu, wy = (y + 0.5f - N / 2f) / ppu;
                float r = Mathf.Sqrt(wx * wx + wy * wy);
                float ang = Mathf.Abs(Mathf.Atan2(wy, wx)) * Mathf.Rad2Deg;
                float lightCircle = Mathf.Clamp01((1.0f - r) / 0.3f);
                float lightCone = wx > 0f ? Mathf.Clamp01((28f - ang) / 7f) * Mathf.Clamp01((4.6f - r) / 1.4f) : 0f;
                float light = Mathf.Max(lightCircle, lightCone);
                return new Color32(0, 0, 0, (byte)(252f * (1f - light)));
            });
            return cone;
        }
    }
}
