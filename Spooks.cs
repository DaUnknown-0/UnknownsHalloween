// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Spook moments (2026-10-20): every one to two minutes of play something harmless happens somewhere on the map,
 * the same for everybody: a ghost drifts along a wall, bats flutter through a passage, a spider lets itself down
 * from the ceiling, a pumpkin grins out of a corner. None of it looks like a game signal (no bodies, no players,
 * no sabotage). World objects on layer 11, so the light system hides them outside your sight like everything else.
 *
 *  - Spots: at the start of the round the host picks up to 24 spots from the reachable floor points of the map
 *    (TrickOrTreat.BuildReachable: works on every vanilla map and on the Atlas and Halloween maps alike) and tests
 *    them per kind: ghost and spider need a wall straight north (ceiling), the pumpkin a corner, the bats a clear
 *    line of six units. Sub 2 carries seed and spots; times and spot order come from the seed on every client and
 *    count play seconds only (no meetings, from the end of the intro).
 *  - Midnight: when the host's own clock strikes 00:00, Sub 3 goes out; every client plays the moment as soon as no
 *    meeting and no intro is running: twelve strikes as writing with a screen shake, the screen darkens, a full
 *    moon drifts across. Once per night.
 *  - Pictures: Resources/hw2026/spook/spook_ghost.png (256), spook_bat_1..6.png (96), spook_spider.png (96),
 *    spook_pumpkin.png (128), spook_moon.png (512). Placeholders are drawn at runtime until they are there.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using TMPro;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class Spooks {
        private const string LogPrefix = "[Halloween/Spooks]";
        internal enum Kind : byte { Ghost, Bats, Spider, Pumpkin, Count }
        internal sealed class Spot { public Vector2 Pos; public Kind Kind; public byte Param; }

        internal static bool On() => OmensDiag.Spook || OmenSettings.Current.Spooks;

        internal static readonly List<Spot> spots = new();
        private static int seed;
        private static System.Random rng;
        private static float next = -1f;
        internal static int Played;

        // ================================================================ plan (host)
        private static readonly System.Random rnd = new System.Random();

        private static float Hit(Vector2 p, Vector2 dir, float max, int mask) {
            float best = float.MaxValue;
            try {
                foreach (var h in Physics2D.RaycastAll(p, dir, max, mask))
                    if (h.collider != null && !h.collider.isTrigger && h.distance > 0.01f && h.distance < best) best = h.distance;
            } catch { }
            return best;
        }

        private static readonly Vector2[] Dirs = {
            new Vector2(1, 0), new Vector2(0.71f, 0.71f), new Vector2(0, 1), new Vector2(-0.71f, 0.71f),
            new Vector2(-1, 0), new Vector2(-0.71f, -0.71f), new Vector2(0, -1), new Vector2(0.71f, -0.71f),
        };

        internal static List<Spot> PickSpots() {
            var list = new List<Spot>();
            var ship = ShipStatus.Instance;
            if (ship == null) return list;
            if (TrickOrTreat.reachShip != ship.Pointer || TrickOrTreat.reachable.Count == 0) TrickOrTreat.BuildReachable(ship);
            int mask = Constants.ShipAndObjectsMask;
            var pts = TrickOrTreat.reachable.Select(x => x.p).OrderBy(_ => rnd.Next()).ToList();
            var per = new int[(int)Kind.Count];
            bool Spread(Vector2 p, Kind k) {
                foreach (var s in list) if ((s.Pos - p).sqrMagnitude < (s.Kind == k ? 16f : 2.25f)) return false;
                return true;
            }
            foreach (var p in pts) {
                if (list.Count >= 24) break;
                // try the rarer kinds first, so every kind gets its share
                foreach (var k in Enumerable.Range(0, (int)Kind.Count).Select(i => (Kind)i).OrderBy(k => per[(int)k])) {
                    if (per[(int)k] >= 6) continue;
                    Spot s = null;
                    switch (k) {
                        case Kind.Ghost: {
                            float up = Hit(p, Vector2.up, 3f, mask);
                            if (up < 0.8f || up > 3f) break;
                            var at = p + Vector2.up * (up - 0.55f);
                            if (Hit(at, Vector2.right, 1.6f, mask) < 1.6f || Hit(at, Vector2.left, 1.6f, mask) < 1.6f) break;
                            s = new Spot { Pos = at, Kind = k, Param = (byte)rnd.Next(2) };
                            break;
                        }
                        case Kind.Spider: {
                            float up = Hit(p, Vector2.up, 3.5f, mask);
                            if (up < 1.1f || up > 3.5f) break;
                            s = new Spot { Pos = p, Kind = k, Param = (byte)Mathf.Clamp(Mathf.RoundToInt((up - 0.15f) * 10f), 5, 34) };
                            break;
                        }
                        case Kind.Pumpkin: {
                            float l = Hit(p, Vector2.left, 1.1f, mask), r = Hit(p, Vector2.right, 1.1f, mask);
                            float d = Hit(p, Vector2.down, 1.1f, mask), u = Hit(p, Vector2.up, 1.1f, mask);
                            if (Mathf.Min(l, r) > 1.1f || Mathf.Min(d, u) > 1.1f) break;
                            s = new Spot { Pos = p, Kind = k };
                            break;
                        }
                        case Kind.Bats: {
                            int di = rnd.Next(8);
                            var dir = Dirs[di];
                            if (!TrickOrTreat.Clear(p - dir * 3f, p + dir * 3f, mask)) break;
                            s = new Spot { Pos = p, Kind = k, Param = (byte)di };
                            break;
                        }
                    }
                    if (s == null || !Spread(s.Pos, k)) continue;
                    list.Add(s);
                    per[(int)k]++;
                    break;
                }
            }
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} spots: " + string.Join(", ", Enumerable.Range(0, (int)Kind.Count).Select(i => $"{(Kind)i} {per[i]}"))
                + $" (from {pts.Count} reachable points, map {TreatCabinets.MapKey() ?? "vanilla " + ship.Type})");
            return list;
        }

        internal static void HostPlan() {
            try {
                if (!On() || !TrickOrTreat.AmHost()) return;
                var list = PickSpots();
                int s = rnd.Next(1, int.MaxValue);
                Omens.Send(Omens.SubSpooks, w => {
                    w.Write(s);
                    w.Write((byte)list.Count);
                    foreach (var p in list) {
                        w.Write((short)Mathf.RoundToInt(p.Pos.x * 100f));
                        w.Write((short)Mathf.RoundToInt(p.Pos.y * 100f));
                        w.Write((byte)p.Kind);
                        w.Write(p.Param);
                    }
                });
                foreach (var p in list) p.Pos = new Vector2(Mathf.Round(p.Pos.x * 100f) / 100f, Mathf.Round(p.Pos.y * 100f) / 100f);
                ApplyPlan(s, list);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} plan failed: {e}"); }
        }

        internal static void ApplyPlan(int s, List<Spot> list) {
            seed = s;
            spots.Clear();
            spots.AddRange(list);
            rng = null;
            next = -1f;
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} plan of the round: {list.Count} spots, seed {s}");
        }

        // ================================================================ moments (every client)
        private sealed class Moment {
            public Kind Kind; public Vector2 Pos; public byte Param; public float At, Life;
            public GameObject Root; public SpriteRenderer[] Parts; public SpriteRenderer Thread, Glow;
        }
        private static readonly List<Moment> moments = new();
        internal static string LastMoment = "";

        private static Sprite ghostSprite, spiderSprite, pumpkinSprite, moonSprite;
        private static Sprite[] batSprites;
        internal static Sprite Ghost() => ghostSprite ??= OmensFx.Load("spook", "spook_ghost.png", DrawGhost);
        internal static Sprite Spider() => spiderSprite ??= OmensFx.Load("spook", "spook_spider.png", DrawSpider);
        internal static Sprite Pumpkin() => pumpkinSprite ??= OmensFx.Load("spook", "spook_pumpkin.png", DrawPumpkin);
        internal static Sprite Moon() => moonSprite ??= OmensFx.Load("spook", "spook_moon.png", DrawMoon);
        internal static Sprite Bat(int f) {
            batSprites ??= new Sprite[6];
            int i = ((f % 6) + 6) % 6;
            if (batSprites[i] == null) batSprites[i] = OmensFx.Load("spook", $"spook_bat_{i + 1}.png", () => DrawBat(i));
            return batSprites[i];
        }

        internal static void Play(Spot s) {
            try {
                var m = new Moment { Kind = s.Kind, Pos = s.Pos, Param = s.Param, At = Time.time };
                m.Root = new GameObject("Spook_" + s.Kind) { layer = 11 };
                SpriteRenderer Part(string name, Sprite sp) {
                    var go = new GameObject(name) { layer = 11 };
                    go.transform.SetParent(m.Root.transform, false);
                    var sr = go.AddComponent<SpriteRenderer>();
                    sr.sprite = sp;
                    return sr;
                }
                switch (s.Kind) {
                    case Kind.Ghost: m.Life = 5.5f; m.Parts = new[] { Part("ghost", Ghost()) }; break;
                    case Kind.Bats: m.Life = 3f; m.Parts = Enumerable.Range(0, 5).Select(i => Part("bat" + i, Bat(i))).ToArray(); break;
                    case Kind.Spider:
                        m.Life = 6.5f;
                        m.Thread = Part("thread", TreatFx.Pixel());
                        m.Thread.color = new Color(0.85f, 0.85f, 0.9f, 0.55f);
                        m.Parts = new[] { Part("spider", Spider()) };
                        break;
                    case Kind.Pumpkin:
                        m.Life = 4.2f;
                        m.Glow = Part("glow", TreatFx.Glow());
                        m.Glow.color = new Color(1f, 0.55f, 0.12f, 0f);
                        m.Parts = new[] { Part("pumpkin", Pumpkin()) };
                        break;
                }
                moments.Add(m);
                Played++;
                LastMoment = s.Kind.ToString();
                HalloweenPlugin.Logger?.LogInfo(FormattableString.Invariant($"{LogPrefix} moment #{Played}: {s.Kind} at {s.Pos.x:F1},{s.Pos.y:F1} ({Omens.playClock:F0} s of play)"));
                TickMoment(m, 0f);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} moment failed: {e.Message}"); }
        }

        private static float Fade(float t, float life, float fin, float fout) =>
            Mathf.Clamp01(t / fin) * (1f - Mathf.Clamp01((t - (life - fout)) / fout));

        private static void TickMoment(Moment m, float t) {
            float z = m.Pos.y / 1000f - 0.6f;
            switch (m.Kind) {
                case Kind.Ghost: {
                    float dir = m.Param == 0 ? 1f : -1f;
                    float k = t / m.Life;
                    var p = m.Pos + new Vector2(dir * Mathf.Lerp(-1.7f, 1.7f, k), 0.12f * Mathf.Sin(t * 2.2f));
                    var sr = m.Parts[0];
                    sr.transform.position = new Vector3(p.x, p.y, (p.y - 0.5f) / 1000f);     // depth by its foot line: behind players in front of the wall
                    sr.transform.localScale = Vector3.one * 1.15f;
                    sr.flipX = dir < 0f;
                    sr.color = new Color(0.92f, 0.96f, 1f, 0.6f * Fade(t, m.Life, 1.2f, 1.4f));
                    break;
                }
                case Kind.Bats: {
                    var dir = Dirs[m.Param % 8];
                    var side = new Vector2(-dir.y, dir.x);
                    for (int i = 0; i < m.Parts.Length; i++) {
                        float lag = i * 0.12f, k = Mathf.Clamp01((t - lag) / (m.Life - 0.6f));
                        var p = m.Pos + dir * Mathf.Lerp(-3.4f, 3.4f, k) + side * (((i * 37) % 9 - 4) * 0.13f + 0.12f * Mathf.Sin(t * 9f + i * 1.7f))
                                + Vector2.up * (0.9f + 0.1f * Mathf.Sin(t * 11f + i));
                        var sr = m.Parts[i];
                        sr.transform.position = new Vector3(p.x, p.y, z - 0.01f * i);
                        sr.transform.localScale = Vector3.one * (0.36f + 0.04f * (i % 3));
                        sr.sprite = Bat((int)(t * 16f) + i * 2);
                        sr.flipX = dir.x < 0f;
                        sr.color = new Color(1f, 1f, 1f, k > 0f && k < 1f ? 1f : 0f);
                    }
                    break;
                }
                case Kind.Spider: {
                    float top = m.Param / 10f, low = 0.95f;
                    float drop = t < 1.6f ? Mathf.SmoothStep(0f, 1f, t / 1.6f) : t < m.Life - 1.6f ? 1f : Mathf.SmoothStep(1f, 0f, (t - (m.Life - 1.6f)) / 1.6f);
                    float y = Mathf.Lerp(top, low, drop);
                    float sway = drop >= 1f ? 0.05f * Mathf.Sin(t * 2.4f) : 0f;
                    var anchor = m.Pos + Vector2.up * top;
                    var sp = m.Pos + new Vector2(sway, y);
                    var sr = m.Parts[0];
                    sr.transform.position = new Vector3(sp.x, sp.y, z);
                    sr.transform.localScale = Vector3.one * 0.38f;
                    sr.transform.localRotation = Quaternion.Euler(0f, 0f, sway * 120f);
                    sr.color = Color.white;
                    float len = Mathf.Max(0.01f, top - y + 0.12f);
                    m.Thread.transform.position = new Vector3((anchor.x + sp.x) / 2f, anchor.y - len / 2f + 0.06f, z + 0.001f);
                    m.Thread.transform.localScale = new Vector3(0.018f, len, 1f);
                    break;
                }
                case Kind.Pumpkin: {
                    float a = Fade(t, m.Life, 0.4f, 0.7f);
                    float pop = t < 0.4f ? Mathf.Lerp(0.6f, 1.08f, t / 0.4f) : 1f + 0.03f * Mathf.Sin(t * 5f);
                    var sr = m.Parts[0];
                    sr.transform.position = new Vector3(m.Pos.x, m.Pos.y + 0.18f, m.Pos.y / 1000f + 0.0005f);
                    sr.transform.localScale = Vector3.one * 0.58f * pop;
                    sr.color = new Color(1f, 1f, 1f, a);
                    m.Glow.transform.position = new Vector3(m.Pos.x, m.Pos.y + 0.2f, m.Pos.y / 1000f + 0.001f);
                    m.Glow.transform.localScale = Vector3.one * 1.4f;
                    m.Glow.color = new Color(1f, 0.55f, 0.12f, 0.45f * a * (0.85f + 0.15f * Mathf.Sin(t * 7f)));
                    break;
                }
            }
        }

        // ================================================================ midnight
        private static bool midnightPending;
        private static float midnightAt = -1f;
        private static DateTime lastMidnight = DateTime.MinValue;
        private static SpriteRenderer darkSr, moonSr, moonGlow;
        private static TextMeshPro strikeText;
        private static int lastStrike;
        internal static bool MidnightRunning => midnightAt > 0f;
        internal static int MidnightStrikes => lastStrike;
        private const float MidnightLife = 14.5f, FirstStrike = 1.2f, StrikeGap = 0.9f;

        internal static void QueueMidnight() {
            midnightPending = true;
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} midnight: queued");
        }

        private static void HostClock() {
            if (!TrickOrTreat.AmHost() || !On()) return;
            var now = DateTime.Now;
            if (now.Hour != 0 || now.Minute != 0 || lastMidnight == now.Date) return;
            lastMidnight = now.Date;
            Omens.Send(Omens.SubMidnight, _ => { });
            QueueMidnight();
        }

        private static void StartMidnight() {
            midnightPending = false;
            midnightAt = Time.time;
            lastStrike = 0;
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} midnight: the clock strikes twelve");
        }

        private static void TickMidnight(bool hide) {
            if (midnightAt < 0f) return;
            float t = Time.time - midnightAt;
            if (hide || t > MidnightLife) { StopMidnight(); return; }
            var uiCam = TreatFx.UiCam();
            if (uiCam == null) return;
            // darkness
            if (darkSr == null) darkSr = TreatFx.UiSr("MidnightDark", TreatFx.Pixel(), -62);
            OmensFx.Cover(darkSr, -44f);
            float dark = Mathf.Clamp01(t / FirstStrike) * (1f - Mathf.Clamp01((t - (MidnightLife - 1.6f)) / 1.6f));
            darkSr.color = new Color(0.02f, 0.01f, 0.06f, 0.55f * dark);
            darkSr.enabled = true;
            // the full moon drifts across the top
            if (moonSr == null) { moonSr = TreatFx.UiSr("MidnightMoon", Moon(), -54); moonGlow = TreatFx.UiSr("MidnightMoonGlow", TreatFx.Glow(), -55); }
            float k = t / MidnightLife;
            var mp = uiCam.ViewportToWorldPoint(new Vector3(Mathf.Lerp(-0.1f, 1.1f, k), 0.8f + 0.06f * Mathf.Sin(k * Mathf.PI), 10f));
            moonSr.transform.position = new Vector3(mp.x, mp.y, -43f);
            moonSr.transform.localScale = Vector3.one * uiCam.orthographicSize * 0.62f;
            moonSr.color = new Color(1f, 1f, 1f, dark);
            moonSr.enabled = true;
            moonGlow.transform.position = new Vector3(mp.x, mp.y, -42.9f);
            moonGlow.transform.localScale = Vector3.one * uiCam.orthographicSize * 1.25f;
            moonGlow.color = new Color(1f, 0.95f, 0.75f, 0.35f * dark);
            moonGlow.enabled = true;
            // the strikes
            int strike = t < FirstStrike ? 0 : Mathf.Min(12, 1 + (int)((t - FirstStrike) / StrikeGap));
            if (strike != lastStrike) {
                lastStrike = strike;
                try { if (HudManager.InstanceExists && HudManager.Instance.PlayerCam != null) HudManager.Instance.PlayerCam.ShakeScreen(0.3f, strike == 12 ? 0.5f : 0.25f); } catch { }
            }
            if (strike == 0) { if (strikeText != null) strikeText.gameObject.SetActive(false); return; }
            if (strikeText == null) {
                strikeText = TreatFx.NewText("MidnightStrike");
                if (strikeText == null) return;
                strikeText.alignment = TextAlignmentOptions.Center;
                strikeText.rectTransform.pivot = new Vector2(0.5f, 0.5f);
                strikeText.rectTransform.sizeDelta = new Vector2(12f, 4f);
                strikeText.sortingOrder = -40;
            }
            bool de = TrickOrTreat.De();
            float since = t - FirstStrike - (strike - 1) * StrikeGap;
            bool last = strike == 12 && since > StrikeGap * 0.6f;
            strikeText.text = last
                ? $"<color=#FFE9A8>{(de ? "Mitternacht" : "Midnight")}</color>"
                : $"<color=#FFE9A8>Dong</color>\n<size=45%><color=#C8B8E8>{strike} / 12</color></size>";
            var at = uiCam.ViewportToWorldPoint(new Vector3(0.5f, 0.56f, 10f));
            float jit = since < 0.25f ? 0.03f : 0f;
            strikeText.transform.position = new Vector3(at.x + UnityEngine.Random.Range(-jit, jit), at.y + UnityEngine.Random.Range(-jit, jit), -41f);
            float pop = last ? 1.1f : 1f + 0.35f * Mathf.Max(0f, 1f - since / 0.3f);
            strikeText.transform.localScale = Vector3.one * 0.9f * pop;
            strikeText.alpha = last ? Mathf.Clamp01(1f - (t - (MidnightLife - 1.2f)) / 1.2f) : Mathf.Clamp01(1.2f - since / StrikeGap);
            strikeText.gameObject.SetActive(true);
        }

        private static void StopMidnight() {
            midnightAt = -1f;
            if (darkSr != null) darkSr.enabled = false;
            if (moonSr != null) moonSr.enabled = false;
            if (moonGlow != null) moonGlow.enabled = false;
            if (strikeText != null) strikeText.gameObject.SetActive(false);
        }

        // ================================================================ per frame
        /// <summary>hide = meeting or intro: moments wait, the midnight moment waits (or stops when a meeting starts).</summary>
        internal static void Tick(bool hide) {
            HostClock();
            if (hide) {
                foreach (var m in moments) if (m.Root != null) UnityEngine.Object.Destroy(m.Root);
                moments.Clear();
                TickMidnight(true);
                return;
            }
            if (midnightPending && midnightAt < 0f) StartMidnight();
            TickMidnight(false);
            if (On() && spots.Count > 0 && seed != 0) {
                rng ??= new System.Random(seed);
                if (next < 0f) next = (OmensDiag.Spook ? 5f : 60f) + (float)rng.NextDouble() * 60f;
                if (Omens.playClock >= next) {
                    next += 60f + (float)rng.NextDouble() * 60f;
                    Play(spots[rng.Next(spots.Count)]);
                }
            }
            for (int i = moments.Count - 1; i >= 0; i--) {
                var m = moments[i];
                float t = Time.time - m.At;
                if (m.Root == null || t > m.Life) { if (m.Root != null) UnityEngine.Object.Destroy(m.Root); moments.RemoveAt(i); continue; }
                TickMoment(m, t);
            }
        }

        internal static void Reset() {
            foreach (var m in moments) if (m.Root != null) UnityEngine.Object.Destroy(m.Root);
            moments.Clear();
            spots.Clear();
            seed = 0;
            rng = null;
            next = -1f;
            midnightPending = false;
            StopMidnight();
        }

        // ================================================================ placeholders (y up)
        private static Color C(float r, float g, float b, float a = 1f) => new Color(r, g, b, a);

        private static TreatFx.Canvas DrawGhost() {
            var c = new TreatFx.Canvas(256, 256);
            var w = C(0.95f, 0.97f, 1f, 0.92f);
            c.Disc(128, 168, 62, w);
            c.Rect(66, 70, 190, 168, w);
            for (int i = 0; i < 4; i++) c.Disc(81 + i * 31.3f, 70, 16, w);
            for (int i = 0; i < 3; i++) c.Erase(96 + i * 31.3f, 56, 13);
            c.Ellipse(106, 172, 10, 15, C(0.1f, 0.1f, 0.16f));
            c.Ellipse(150, 172, 10, 15, C(0.1f, 0.1f, 0.16f));
            c.Ellipse(128, 136, 12, 9, C(0.1f, 0.1f, 0.16f, 0.85f));
            return c;
        }

        private static TreatFx.Canvas DrawBat(int f) {
            var c = new TreatFx.Canvas(96, 96);
            float wing = 0.5f + 0.5f * Mathf.Sin(f / 6f * Mathf.PI * 2f);
            OmensFx.DrawBat(c, 48, 42, 1.9f, wing, C(0.08f, 0.05f, 0.1f));
            c.Disc(45, 58, 1.3f, C(1f, 0.5f, 0.4f));
            c.Disc(51, 58, 1.3f, C(1f, 0.5f, 0.4f));
            return c;
        }

        private static TreatFx.Canvas DrawSpider() {
            var c = new TreatFx.Canvas(96, 96);
            var b = C(0.1f, 0.08f, 0.1f);
            for (int s = -1; s <= 1; s += 2)
                for (int i = 0; i < 4; i++) {
                    float y = 50 - i * 6;
                    c.Line(48, y, 48 + s * 22, y + 8 - i * 3, 3f, b);
                    c.Line(48 + s * 22, y + 8 - i * 3, 48 + s * 32, y - 10 - i * 4, 2.5f, b);
                }
            c.Ellipse(48, 40, 14, 17, b);
            c.Disc(48, 60, 9, b);
            c.Disc(44, 62, 2.2f, C(1f, 0.3f, 0.3f));
            c.Disc(52, 62, 2.2f, C(1f, 0.3f, 0.3f));
            return c;
        }

        private static TreatFx.Canvas DrawPumpkin() {
            var c = new TreatFx.Canvas(128, 128);
            c.Ellipse(64, 54, 50, 40, C(0.93f, 0.48f, 0.09f));
            c.Ellipse(46, 54, 18, 38, C(0.82f, 0.4f, 0.05f));
            c.Ellipse(82, 54, 18, 38, C(0.82f, 0.4f, 0.05f));
            c.Ellipse(64, 54, 14, 39, C(1f, 0.56f, 0.14f));
            c.Rect(59, 90, 69, 106, C(0.35f, 0.48f, 0.15f));
            var face = C(1f, 0.88f, 0.35f);
            c.Tri(38, 66, 56, 66, 47, 80, face);
            c.Tri(72, 66, 90, 66, 81, 80, face);
            c.Tri(58, 52, 70, 52, 64, 62, face);
            c.Tri(32, 42, 96, 42, 64, 24, face);
            c.Rect(48, 38, 54, 43, C(0.93f, 0.48f, 0.09f));
            c.Rect(74, 38, 80, 43, C(0.93f, 0.48f, 0.09f));
            c.Outline(C(0.2f, 0.08f, 0.02f, 0.9f), 2);
            return c;
        }

        private static TreatFx.Canvas DrawMoon() {
            var c = new TreatFx.Canvas(256, 256);
            c.Disc(128, 128, 112, C(1f, 0.96f, 0.78f));
            c.Disc(92, 160, 22, C(0.9f, 0.84f, 0.64f));
            c.Disc(160, 100, 30, C(0.9f, 0.84f, 0.64f));
            c.Disc(150, 176, 12, C(0.9f, 0.84f, 0.64f));
            c.Disc(84, 92, 14, C(0.9f, 0.84f, 0.64f));
            return c;
        }
    }
}
