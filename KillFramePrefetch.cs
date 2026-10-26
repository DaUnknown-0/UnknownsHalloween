// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * KillFramePrefetch - reads and decodes the frames of a kill cutscene on a background thread (User 2026-10-26: Thing and
 * Xenomorph "sehr laggy" in the game, smooth as a GIF).
 *
 * The cutscene used to read and decode up to five PNG layers on the main thread at every frame change (ImageConversion).
 * On a busy client that took longer than a game frame, and the clock-driven playback skipped pictures. Now a worker thread
 * starts with the scene, walks all frames in order and decodes each layer into raw RGBA rows (own PNG reader: palette,
 * RGB, RGBA and grey, 8 bit and less, not interlaced; anything else falls back to ImageConversion on the main thread).
 * Identical files are decoded once (one object per picture, the blend scenes repeat many). The main thread only uploads
 * a decoded picture once (LoadRawTextureData) and keeps the sprite for repeats until the scene ends.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Threading;

namespace UnknownsHalloween {

    internal static class KillFramePrefetch {

        internal sealed class Picture {
            public byte[] Png;          // the file (crop chunk, fallback decode)
            public int W, H;
            public byte[] Rgba;         // bottom row first, as Texture2D wants it; null = decode on the main thread
        }

        private static readonly object Gate = new();
        private static Dictionary<(int frame, int layer), Picture> ready = new();
        private static Dictionary<string, Picture> byHash = new();
        private static int generation;

        /// <summary>Starts decoding a scene. pathOf(frame, layer) gives the resource name, null for a layer the scene skips.</summary>
        internal static void Start(int frames, int layers, Func<int, int, string> pathOf) {
            int gen;
            lock (Gate) {
                gen = ++generation;
                ready = new Dictionary<(int, int), Picture>();
                byHash = new Dictionary<string, Picture>();
            }
            var t = new Thread(() => Work(gen, frames, layers, pathOf)) { IsBackground = true, Name = "HalloweenKillFrames" };
            t.Start();
        }

        internal static void Stop() {
            lock (Gate) {
                generation++;
                ready = new Dictionary<(int, int), Picture>();
                byHash = new Dictionary<string, Picture>();
            }
        }

        /// <summary>The decoded picture if the worker got there already, else read and decode it right here.
        /// Null when the scene has no such file.</summary>
        internal static Picture Get(int frame, int layer, string path) {
            lock (Gate) if (ready.TryGetValue((frame, layer), out var p)) return p;
            return Load(frame, layer, path, generation);
        }

        private static void Work(int gen, int frames, int layers, Func<int, int, string> pathOf) {
            try {
                for (int f = 0; f < frames; f++)
                    for (int l = 0; l < layers; l++) {
                        lock (Gate) { if (gen != generation) return; if (ready.ContainsKey((f, l))) continue; }
                        string path = pathOf(f, l);
                        if (path != null) Load(f, l, path, gen);
                    }
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogWarning($"[Halloween] kill frame prefetch stopped: {e.Message}");
            }
        }

        private static Picture Load(int frame, int layer, string path, int gen) {
            byte[] png = HalloweenAssets.Read(path);
            if (png == null) return null;
            string hash;
            using (var md5 = MD5.Create()) hash = Convert.ToBase64String(md5.ComputeHash(png));
            Picture pic;
            lock (Gate) byHash.TryGetValue(hash, out pic);
            if (pic == null) {
                pic = new Picture { Png = png };
                try { pic.Rgba = Decode(png, out pic.W, out pic.H); } catch { pic.Rgba = null; }
            }
            lock (Gate) {
                if (gen != generation) return pic;
                if (byHash.TryGetValue(hash, out var known)) pic = known; else byHash[hash] = pic;
                ready[(frame, layer)] = pic;
            }
            return pic;
        }

        // ---- a small PNG reader: enough for the exported frames ----

        private static int Be(byte[] b, int p) => (b[p] << 24) | (b[p + 1] << 16) | (b[p + 2] << 8) | b[p + 3];

        /// <summary>RGBA, bottom row first. Null for formats it does not cover (16 bit, interlaced).</summary>
        internal static byte[] Decode(byte[] png, out int w, out int h) {
            w = h = 0;
            int depth = 0, type = 0, interlace = 0;
            byte[] plte = null, trns = null;
            var idat = new MemoryStream();
            int p = 8;
            while (p + 8 <= png.Length) {
                int len = Be(png, p);
                string id = System.Text.Encoding.ASCII.GetString(png, p + 4, 4);
                int d = p + 8;
                if (len < 0 || d + len > png.Length) return null;
                if (id == "IHDR") { w = Be(png, d); h = Be(png, d + 4); depth = png[d + 8]; type = png[d + 9]; interlace = png[d + 12]; }
                else if (id == "PLTE") { plte = new byte[len]; Buffer.BlockCopy(png, d, plte, 0, len); }
                else if (id == "tRNS") { trns = new byte[len]; Buffer.BlockCopy(png, d, trns, 0, len); }
                else if (id == "IDAT") idat.Write(png, d, len);
                else if (id == "IEND") break;
                p = d + len + 4;
            }
            if (w <= 0 || h <= 0 || interlace != 0 || depth > 8) return null;
            int channels = type switch { 0 => 1, 2 => 3, 3 => 1, 4 => 2, 6 => 4, _ => 0 };
            if (channels == 0 || (type == 3 && plte == null) || ((type == 2 || type == 4 || type == 6) && depth != 8)) return null;

            int bitsPx = channels * depth;
            int stride = (w * bitsPx + 7) / 8;
            int bpp = Math.Max(1, bitsPx / 8);
            var raw = new byte[(stride + 1) * h];
            idat.Position = 0;
            using (var z = new ZLibStream(idat, CompressionMode.Decompress)) {
                int read = 0;
                while (read < raw.Length) { int n = z.Read(raw, read, raw.Length - read); if (n <= 0) break; read += n; }
                if (read < raw.Length) return null;
            }

            var cur = new byte[stride];
            var prev = new byte[stride];
            var outp = new byte[w * h * 4];
            for (int y = 0; y < h; y++) {
                int rp = y * (stride + 1);
                int filter = raw[rp];
                for (int x = 0; x < stride; x++) {
                    int a = x >= bpp ? cur[x - bpp] : 0, b = prev[x], c = x >= bpp ? prev[x - bpp] : 0;
                    int v = raw[rp + 1 + x];
                    switch (filter) {
                        case 1: v += a; break;
                        case 2: v += b; break;
                        case 3: v += (a + b) >> 1; break;
                        case 4: {
                            int pa = Math.Abs(b - c), pb = Math.Abs(a - c), pc = Math.Abs(a + b - 2 * c);
                            v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
                            break;
                        }
                    }
                    cur[x] = (byte)v;
                }
                int o = (h - 1 - y) * w * 4;                                  // Unity: bottom row first
                for (int x = 0; x < w; x++, o += 4) {
                    byte r, g, bl, al = 255;
                    switch (type) {
                        case 6: r = cur[x * 4]; g = cur[x * 4 + 1]; bl = cur[x * 4 + 2]; al = cur[x * 4 + 3]; break;
                        case 2:
                            r = cur[x * 3]; g = cur[x * 3 + 1]; bl = cur[x * 3 + 2];
                            if (trns != null && trns.Length >= 6 && r == trns[1] && g == trns[3] && bl == trns[5]) al = 0;
                            break;
                        case 4: r = g = bl = cur[x * 2]; al = cur[x * 2 + 1]; break;
                        default: {
                            int idx;
                            if (depth == 8) idx = cur[x];
                            else {
                                int bit = x * depth;
                                idx = (cur[bit >> 3] >> (8 - depth - (bit & 7))) & ((1 << depth) - 1);
                            }
                            if (type == 3) {
                                int q = idx * 3;
                                if (q + 2 < plte.Length) { r = plte[q]; g = plte[q + 1]; bl = plte[q + 2]; } else r = g = bl = 0;
                                if (trns != null && idx < trns.Length) al = trns[idx];
                            } else {
                                int gray = depth == 8 ? idx : idx * 255 / ((1 << depth) - 1);
                                r = g = bl = (byte)gray;
                                if (trns != null && trns.Length >= 2 && idx == ((trns[0] << 8) | trns[1])) al = 0;
                            }
                            break;
                        }
                    }
                    outp[o] = r; outp[o + 1] = g; outp[o + 2] = bl; outp[o + 3] = al;
                }
                var t = prev; prev = cur; cur = t;
            }
            return outp;
        }
    }
}
