// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Artwork of the lobby games (Pumpkin Carving, Boo!). The real pictures come from the graphics session as
 * Resources/hw2026/lobby/<file>.png (embedded, logical name UnknownsHalloween.Resources.hw2026.lobby.<file>);
 * until a file is there, a procedural stand-in of the same size and layout is drawn at runtime:
 *   carve_pumpkin.png       512x512  carving area x 136-376, y 156-396 (24x24 grid, 10 px per cell, y from the top)
 *   carve_lantern.png       160x160  face field x 40-120, y 50-130
 *   carve_lantern_glow.png  160x160  halo behind the lantern
 *   boo_button.png          256x256  the Use button while you are the ghost
 *   boo_crown.png            64x64   the crown of the last one left
 * Every texture and sprite carries HideFlags.DontUnloadUnusedAsset (the lobby scene change would unload them).
 */

using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class LobbyArt {
        private const string Res = "UnknownsHalloween.Resources.hw2026.lobby.";

        // layout of the pictures (pixels, y from the top), shared by placeholder and real art
        internal const int PumpkinSize = 512, PumpkinAreaX = 136, PumpkinAreaY = 156, PumpkinAreaW = 240;
        internal const int LanternSize = 160, LanternFaceX = 40, LanternFaceY = 50, LanternFaceW = 80;

        private static readonly Dictionary<string, Texture2D> cache = new();
        private static readonly Dictionary<string, Sprite> sprites = new();

        internal static Texture2D Pumpkin() => Get("carve_pumpkin.png", PumpkinSize, DrawPumpkin);
        internal static Texture2D Lantern() => Get("carve_lantern.png", LanternSize, DrawLantern);
        internal static Texture2D LanternGlow() => Get("carve_lantern_glow.png", LanternSize, DrawGlow);
        internal static Texture2D BooButton() => Get("boo_button.png", 256, DrawBoo);
        internal static Texture2D Crown() => Get("boo_crown.png", 64, DrawCrown);

        /// <summary>A world sprite of the texture, <paramref name="worldWidth"/> units wide, pivot in the centre.</summary>
        internal static Sprite WorldSprite(string key, Texture2D tex, float worldWidth) {
            string k = key + "@" + worldWidth.ToString("F3");
            if (sprites.TryGetValue(k, out var s) && s != null) return s;
            s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width / worldWidth);
            s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            sprites[k] = s;
            return s;
        }

        internal static Sprite UiSprite(string key, Texture2D tex) => WorldSprite("ui_" + key, tex, tex.width / 100f);

        private static Texture2D Get(string file, int size, Func<float, float, Color> draw) {
            if (cache.TryGetValue(file, out var t) && t != null) return t;
            t = LoadEmbedded(file) ?? Draw(file, size, draw);
            cache[file] = t;
            return t;
        }

        private static Texture2D LoadEmbedded(string file) {
            try {
                using var stream = System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream(Res + file);
                if (stream == null) return null;
                var data = new byte[stream.Length];
                int read = 0;
                while (read < data.Length) { int n = stream.Read(data, read, data.Length - read); if (n <= 0) break; read += n; }
                var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false) { name = "hwlobby_" + file };
                if (!ImageConversion.LoadImage(tex, data, false)) { UnityEngine.Object.Destroy(tex); return null; }
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.filterMode = FilterMode.Bilinear;
                tex.Apply(false, true);
                tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                HalloweenPlugin.Logger?.LogInfo($"{LobbyGames.LogPrefix} picture {file} ({tex.width}x{tex.height}) from the resources");
                return tex;
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"{LobbyGames.LogPrefix} picture {file} failed: {e.Message}");
                return null;
            }
        }

        // draw(x, y) with x, y in 0..1, y from the top (like the picture specs)
        private static Texture2D Draw(string file, int size, Func<float, float, Color> draw) {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false) { name = "hwlobby_placeholder_" + file };
            var px = new Color[size * size];
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                    px[y * size + x] = draw((x + 0.5f) / size, 1f - (y + 0.5f) / size);
            tex.SetPixels(px);
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.filterMode = FilterMode.Bilinear;
            tex.Apply(false, true);
            tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return tex;
        }

        private static float Edge(float d, float soft) => Mathf.Clamp01(0.5f - d / soft);

        private static readonly Color Outline = new Color(0.10f, 0.05f, 0.03f, 1f);

        // a pumpkin body: rx/ry around (cx, cy), ribbed shading, dark outline; returns colour with alpha
        private static Color Body(float x, float y, float cx, float cy, float rx, float ry, Color baseCol, float px) {
            float nx = (x - cx) / rx, ny = (y - cy) / ry;
            // the lobes: the outline bulges a little per rib
            float ang = Mathf.Atan2(ny, nx);
            float lobe = 1f + 0.035f * Mathf.Abs(Mathf.Sin(ang * 3f));
            float r = Mathf.Sqrt(nx * nx + ny * ny) / lobe;
            float d = (r - 1f) * Mathf.Min(rx, ry);
            float a = Edge(d, px * 1.5f);
            if (a <= 0f) return Color.clear;
            float rib = Mathf.Abs(Mathf.Sin(nx * Mathf.PI * 2.5f / Mathf.Max(0.35f, Mathf.Sqrt(Mathf.Max(0.05f, 1f - ny * ny)))));
            float shade = 0.72f + 0.28f * rib;
            shade *= 1f - 0.35f * Mathf.Clamp01(ny * 0.8f + 0.25f) * 0.6f;          // a little darker at the bottom
            shade += 0.18f * Mathf.Clamp01(1f - ((nx + 0.35f) * (nx + 0.35f) + (ny + 0.4f) * (ny + 0.4f)) * 3f);   // highlight
            var c = new Color(baseCol.r * shade, baseCol.g * shade, baseCol.b * shade, 1f);
            float ol = Edge(-(d + px * 3.2f), px * 1.5f);                           // outline band inside the edge
            c = Color.Lerp(c, Outline, 1f - ol);
            c.a = a;
            return c;
        }

        private static Color Stem(float x, float y, float cx, float top, float bottom, float w, float px) {
            if (y < top || y > bottom) return Color.clear;
            float t = (y - top) / (bottom - top);
            float lean = (1f - t) * w * 0.6f;
            float half = w * (0.55f + 0.45f * t);
            float d = Mathf.Abs(x - (cx + lean)) - half;
            float a = Edge(d, px * 1.5f);
            if (a <= 0f) return Color.clear;
            var c = Color.Lerp(new Color(0.36f, 0.42f, 0.16f), new Color(0.28f, 0.20f, 0.08f), t);
            if (d > -px * 3f) c = Outline;
            c.a = a;
            return c;
        }

        private static Color Over(Color under, Color over) {
            float a = over.a + under.a * (1f - over.a);
            if (a <= 0f) return Color.clear;
            var c = (over * over.a + under * under.a * (1f - over.a)) / a;
            c.a = a;
            return c;
        }

        private static Color DrawPumpkin(float x, float y) {
            const float px = 1f / 512f;
            var c = Stem(x, y, 0.5f, 0.06f, 0.20f, 0.045f, px);
            c = Over(c, Body(x, y, 0.5f, 0.54f, 0.45f, 0.40f, new Color(1f, 0.52f, 0.10f), px));
            // a faint lighter patch where the face goes, so the grid reads on the placeholder
            if (c.a > 0.9f && x > 0.265f && x < 0.735f && y > 0.305f && y < 0.775f) c = Color.Lerp(c, new Color(1f, 0.66f, 0.28f, 1f), 0.12f);
            return c;
        }

        private static Color DrawLantern(float x, float y) {
            const float px = 1f / 160f;
            var c = Stem(x, y, 0.5f, 0.10f, 0.27f, 0.06f, px);
            // lit from inside: deeper orange shell, the carved face goes on top
            c = Over(c, Body(x, y, 0.5f, 0.58f, 0.46f, 0.38f, new Color(0.90f, 0.40f, 0.06f), px));
            return c;
        }

        private static Color DrawGlow(float x, float y) {
            float d = Vector2.Distance(new Vector2(x, y), new Vector2(0.5f, 0.56f)) / 0.5f;
            float a = Mathf.Clamp01(1f - d);
            a = a * a * 0.55f;
            return new Color(1f, 0.72f, 0.25f, a);
        }

        private static Color DrawBoo(float x, float y) {
            const float px = 1f / 256f;
            // a sheet ghost: round head, wavy hem, two eyes and an open mouth
            float cx = 0.5f;
            float hem = 0.80f + 0.04f * Mathf.Sin(x * Mathf.PI * 8f);
            float d;
            if (y < 0.45f) d = Vector2.Distance(new Vector2(x, y), new Vector2(cx, 0.45f)) - 0.32f;
            else d = Mathf.Max(Mathf.Abs(x - cx) - (0.32f + (y - 0.45f) * 0.12f), y - hem);
            float a = Edge(d, px * 2f);
            if (a <= 0f) return Color.clear;
            var c = new Color(0.96f, 0.97f, 1f, 1f);
            if (d > -px * 7f) c = new Color(0.12f, 0.12f, 0.18f, 1f);
            float e1 = Vector2.Distance(new Vector2(x, y), new Vector2(0.40f, 0.42f)) - 0.05f;
            float e2 = Vector2.Distance(new Vector2(x, y), new Vector2(0.60f, 0.42f)) - 0.05f;
            float m = (new Vector2((x - 0.5f) / 0.07f, (y - 0.58f) / 0.09f)).magnitude - 1f;
            if (e1 < 0f || e2 < 0f || m < 0f) c = new Color(0.12f, 0.12f, 0.18f, 1f);
            c.a = a;
            return c;
        }

        private static Color DrawCrown(float x, float y) {
            const float px = 1f / 64f;
            // a band with three points
            float band = Mathf.Max(Mathf.Abs(x - 0.5f) - 0.40f, Mathf.Abs(y - 0.74f) - 0.12f);
            float peaks = 1f;
            for (int i = 0; i < 3; i++) {
                float pxc = 0.20f + i * 0.30f;
                float tip = 0.18f;
                float t = (y - tip) / (0.66f - tip);
                if (t < 0f || t > 1f) continue;
                float half = 0.14f * t;
                peaks = Mathf.Min(peaks, Mathf.Abs(x - pxc) - half);
            }
            float d = Mathf.Min(band, peaks);
            float a = Edge(d, px * 1.5f);
            if (a <= 0f) return Color.clear;
            var c = new Color(1f, 0.82f, 0.20f, 1f);
            if (y > 0.70f && y < 0.78f && Mathf.Abs(x - 0.5f) < 0.06f) c = new Color(0.86f, 0.18f, 0.24f, 1f);
            if (d > -px * 3f) c = new Color(0.40f, 0.24f, 0.04f, 1f);
            c.a = a;
            return c;
        }

        // ---------------------------------------------------------------- faces
        /// <summary>A 24x24 texture of a face (bit set = carved), point filtered, carved cells in the glow colour.</summary>
        internal static Texture2D FaceTexture(byte[] bits, Color lit, Texture2D reuse = null) {
            var tex = reuse;
            if (tex == null) {
                tex = new Texture2D(PumpkinCarving.Grid, PumpkinCarving.Grid, TextureFormat.RGBA32, false) { name = "hwlobby_face" };
                tex.filterMode = FilterMode.Point;
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            }
            const int n = PumpkinCarving.Grid;
            var px = new Color32[n * n];
            Color32 on = lit, off = new Color32(0, 0, 0, 0);
            for (int row = 0; row < n; row++)
                for (int col = 0; col < n; col++)
                    px[(n - 1 - row) * n + col] = PumpkinCarving.Get(bits, col, row) ? on : off;
            tex.SetPixels32(px);
            tex.Apply(false, false);
            return tex;
        }

        private static Texture2D gridLines;
        /// <summary>Faint grid lines for the carving area (24 cells of 10 px).</summary>
        internal static Texture2D GridLines() {
            if (gridLines != null) return gridLines;
            const int n = PumpkinCarving.Grid * 10 + 1;
            gridLines = new Texture2D(n, n, TextureFormat.RGBA32, false) { name = "hwlobby_grid" };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++) {
                    bool line = x % 10 == 0 || y % 10 == 0;
                    bool major = x % 60 == 0 || y % 60 == 0;
                    px[y * n + x] = line ? new Color32(40, 16, 4, (byte)(major ? 110 : 55)) : new Color32(0, 0, 0, 0);
                }
            gridLines.SetPixels32(px);
            gridLines.filterMode = FilterMode.Point;
            gridLines.wrapMode = TextureWrapMode.Clamp;
            gridLines.Apply(false, true);
            gridLines.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return gridLines;
        }
    }
}
