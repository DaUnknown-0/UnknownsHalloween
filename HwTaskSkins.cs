// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Halloween task skins (2026-10-21, idea E1). Five vanilla tasks get a Halloween look, the mechanics stay exactly
 * the same (colliders, hit areas, timings, task data are never touched):
 *
 *   - Fuel Engines (RefuelStage):          the gas can becomes a witch's cauldron, the fill a green brew.
 *   - Clear Asteroids (WeaponsMinigame):   the asteroids become bats (no spinning), a hit leaves a puff.
 *   - Empty Garbage (EmptyGarbageMinigame): the garbage becomes candy wrappers. Leaves (O2 chute) and the rare
 *                                          special objects stay vanilla.
 *   - Prime Shields (ShieldMinigame):      the seven hexes become pumpkin facets, off and lit.
 *   - Divert Power (DivertPowerMinigame):  the slider handles become lanterns; the one that has been pushed all
 *                                          the way up lights. Divert Power instead of Fix Wiring: its sliders are
 *                                          the only switches among the two, while the wiring task lives on the
 *                                          wire colours, which must stay readable.
 *
 * How: a postfix on Begin of each minigame (all five are substantial methods, none of them is patched by TOR, UTS
 * or UC) swaps sprites by field / object name, sized to the vanilla sprite. New renderers (pumpkin facets,
 * lanterns, cauldron) hang under the vanilla object and sit just in front of the minigame's FillQuad (z -60),
 * which writes depth. The changing parts (facet on/off, lantern light, brew level, new bats) follow in the
 * HudManager.Update tick while the minigame is open. No detour on any small Il2Cpp method.
 *
 * Option 2140 "Halloween Tasks" (General, own heading), default ON: purely cosmetic, every client draws for
 * itself, nothing is sent (no RPC). The host's value counts for everybody through TOR's option sync.
 *
 * Artwork: Resources/hw2026/tasks/ (embedded). A missing file leaves that part vanilla.
 */

using System;
using System.Collections.Generic;
using HarmonyLib;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using TheOtherRoles;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HwTaskSkins {
        internal const string LogPrefix = "[Halloween/Tasks]";
        internal static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");
        internal static void Warn(string s) => HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {s}");

        private const string Folder = "tasks";
        internal const string Marker = "HwTaskSkin";

        internal static CustomOption On;

        // self test: UC_HALLOWEEN_DIAG = tasks (HwTaskSkinsDiag.cs)
        internal static readonly string DiagMode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        internal static bool DiagOn => DiagMode == "tasks";
        /// <summary>Diag only: open the next minigame without skins (vanilla comparison shot).</summary>
        internal static bool DiagVanilla;

        internal static bool Enabled {
            get {
                if (DiagOn) return !DiagVanilla;
                try { return On == null || On.getBool(); } catch { return true; }
            }
        }

        private static bool booted;
        private static void Boot() {
            if (booted) return;
            booted = true;
            try {
                On = CustomOption.Create(2140, CustomOption.CustomOptionType.General, "Halloween Tasks", true, null, true, null, "Halloween Tasks");
                HwHauntedTasks.Create();               // option 2141 right below
                UnknownsCollection.UCFx.RegisterTick(Tick);
                if (DiagOn) UnknownsCollection.UCFx.RegisterTick(HwTaskSkinsDiag.Tick);
                Log("registered (fuel, asteroids, garbage, shields, divert power).");
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} registration failed: {e}");
            }
        }

        [HarmonyPatch(typeof(RPCProcedure), nameof(RPCProcedure.resetVariables))]
        static class BootPatch {
            static bool Prepare() { Boot(); return true; }
            public static void Postfix() { live.Clear(); }
        }

        // ---- sprites ----

        private static readonly Dictionary<string, Vector2> dims = new();

        /// <summary>Pixel size of a task picture, zero when the file is missing.</summary>
        private static Vector2 Dims(string file) {
            if (dims.TryGetValue(file, out var d)) return d;
            var s = HwArt.Get(Folder, file, 1f, new Vector2(0.5f, 0.5f), null);
            d = s != null ? new Vector2(s.rect.width, s.rect.height) : Vector2.zero;
            dims[file] = d;
            return d;
        }

        internal static bool Has(string file) => Dims(file).x > 0f;

        /// <summary>The picture scaled to fit inside a box of boxW x boxH units (centre pivot), null when missing.</summary>
        internal static Sprite Fit(string file, float boxW, float boxH) {
            var d = Dims(file);
            if (d.x <= 0f || boxW <= 0f || boxH <= 0f) return null;
            float k = Mathf.Min(boxW / d.x, boxH / d.y);
            return HwArt.Get(Folder, file, d.x * k, new Vector2(0.5f, 0.5f), null);
        }

        /// <summary>The picture with the given width in units and a custom pivot (own cache key per pivot).</summary>
        private static readonly Dictionary<string, Sprite> pivoted = new();
        internal static Sprite WithPivot(string file, float worldWidth, Vector2 pivot) {
            string key = $"{file}@{worldWidth:F3}@{pivot.x:F2},{pivot.y:F2}";
            if (pivoted.TryGetValue(key, out var s) && s != null) return s;
            var tex = HwArt.LoadTexture(Folder, file);
            if (tex == null) return null;
            s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, tex.width / Mathf.Max(0.01f, worldWidth));
            s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            pivoted[key] = s;
            return s;
        }

        /// <summary>Local size of a renderer's sprite (sprite units, before the object's scale).</summary>
        internal static Vector2 LocalSize(SpriteRenderer sr) {
            try { if (sr != null && sr.sprite != null) { var b = sr.sprite.bounds.size; return new Vector2(b.x, b.y); } } catch { }
            return Vector2.zero;
        }

        // ---- overlays ----

        /// <summary>World z just in front of the minigame's FillQuad (it writes depth), fallback root z - 10.5.</summary>
        internal static float OverlayZ(Minigame mg) {
            try {
                foreach (var r in mg.GetComponentsInChildren<Renderer>(true))
                    if (r != null && r.name == "FillQuad") return r.transform.position.z - 0.5f;
                // MultistageMinigame: the FillQuad belongs to the parent
                var p = mg.transform.parent;
                if (p != null) {
                    var parentMg = p.GetComponentInParent<Minigame>();
                    if (parentMg != null)
                        foreach (var r in parentMg.GetComponentsInChildren<Renderer>(true))
                            if (r != null && r.name == "FillQuad") return r.transform.position.z - 0.5f;
                }
            } catch { }
            return mg.transform.position.z - 10.5f;
        }

        /// <summary>A new renderer under <paramref name="host"/> at the centre of its sprite, in front of the FillQuad.</summary>
        internal static SpriteRenderer Overlay(SpriteRenderer host, Sprite sprite, float z, Vector2 offset = default) {
            var go = new GameObject(Marker) { layer = host.gameObject.layer };
            go.transform.SetParent(host.transform, false);
            Vector3 c = Vector3.zero;
            try { c = host.transform.InverseTransformPoint(host.bounds.center); } catch { }
            go.transform.localPosition = new Vector3(c.x + offset.x, c.y + offset.y, 0f);
            var wp = go.transform.position;
            go.transform.position = new Vector3(wp.x, wp.y, z);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingLayerID = host.sortingLayerID;
            sr.sortingOrder = host.sortingOrder + 1;
            var m = HwLook.SpriteMaterial;
            if (m != null) sr.sharedMaterial = m;
            return sr;
        }

        // ---- live skins (updated in the tick while their minigame is open) ----

        private abstract class Skin {
            internal Minigame Owner;
            internal abstract void Update();
        }
        private static readonly List<Skin> live = new();

        private static int lastSeen;
        private static int pendingFrames;
        internal static int DiagPolled;

        /// <summary>Safety net next to the Begin postfixes: a minigame that opened without them gets its skin here.</summary>
        private static void Poll() {
            var cur = Minigame.Instance;
            if (cur == null) { lastSeen = 0; return; }
            int id = cur.GetInstanceID();
            if (id != lastSeen) { lastSeen = id; pendingFrames = 10; }
            if (pendingFrames <= 0) return;
            pendingFrames--;
            if (!Enabled) { pendingFrames = 0; return; }
            foreach (var m in cur.GetComponentsInChildren<Minigame>()) {
                if (m == null || m.transform.Find(Marker) != null) continue;
                int before = DiagApplied;
                var sh = m.TryCast<ShieldMinigame>(); if (sh != null) ApplyShields(sh);
                var dv = m.TryCast<DivertPowerMinigame>(); if (dv != null) ApplyDivert(dv);
                var wm = m.TryCast<WeaponsMinigame>(); if (wm != null) ApplyWeapons(wm);
                var gm = m.TryCast<EmptyGarbageMinigame>(); if (gm != null) ApplyGarbage(gm);
                var rf = m.TryCast<RefuelStage>(); if (rf != null) ApplyFuel(rf);
                if (DiagApplied != before) { DiagPolled++; Log($"skin applied by the poll: {m.name}"); }
            }
        }

        private static void Tick() {
            try { Poll(); } catch (Exception e) { Warn("poll: " + e.Message); pendingFrames = 0; }
            for (int i = live.Count - 1; i >= 0; i--) {
                var s = live[i];
                bool gone;
                try { gone = s.Owner == null || s.Owner.gameObject == null; } catch { gone = true; }
                if (gone) { live.RemoveAt(i); continue; }
                try { s.Update(); } catch (Exception e) { Warn($"{s.GetType().Name} update: {e.Message}"); live.RemoveAt(i); }
            }
        }

        private static bool Claim(Minigame mg) {
            if (mg == null || !Enabled) return false;
            if (mg.transform.Find(Marker) != null) return false;
            var go = new GameObject(Marker);
            go.transform.SetParent(mg.transform, false);
            return true;
        }

        internal static int DiagApplied;
        internal static string DiagLast = "";

        // ---- Prime Shields ----

        private sealed class ShieldSkin : Skin {
            internal ShieldMinigame Mg;
            internal SpriteRenderer[] Van, Ov;
            internal Sprite Off, OnS;
            internal override void Update() {
                int bits = Mg.shields;
                for (int i = 0; i < Van.Length; i++) {
                    if (Van[i] == null || Ov[i] == null) continue;
                    Van[i].enabled = false;
                    var want = (bits & (1 << i)) != 0 ? OnS : Off;
                    if (Ov[i].sprite != want) Ov[i].sprite = want;
                }
            }
        }

        internal static void ApplyShields(ShieldMinigame mg) {
            if (!Has("task_hw_pumpkin_hex_off.png") || !Has("task_hw_pumpkin_hex_on.png")) return;
            if (!Claim(mg)) return;
            var shields = mg.Shields;
            if (shields == null || shields.Length == 0) return;
            float z = OverlayZ(mg);
            var skin = new ShieldSkin { Owner = mg, Mg = mg, Van = new SpriteRenderer[shields.Length], Ov = new SpriteRenderer[shields.Length] };
            for (int i = 0; i < shields.Length; i++) {
                var v = shields[i];
                if (v == null) continue;
                var size = LocalSize(v);
                var off = Fit("task_hw_pumpkin_hex_off.png", size.x, size.y);
                var on = Fit("task_hw_pumpkin_hex_on.png", size.x, size.y);
                if (off == null || on == null) continue;
                skin.Off = off; skin.OnS = on;
                skin.Van[i] = v;
                skin.Ov[i] = Overlay(v, off, z);
            }
            skin.Update();
            live.Add(skin);
            DiagApplied++; DiagLast = $"shields {shields.Length}";
        }

        // ---- Divert Power ----

        private sealed class DivertSkin : Skin {
            internal DivertPowerMinigame Mg;
            internal SpriteRenderer[] Van, Ov;
            internal Sprite Off, OnS;
            internal override void Update() {
                int target = Mg.sliderId;
                float top = Mg.SliderY.max;
                bool done = false;
                try { done = Mg.MyNormTask != null && Mg.MyNormTask.IsComplete; } catch { }
                for (int i = 0; i < Van.Length; i++) {
                    if (Van[i] == null || Ov[i] == null) continue;
                    Van[i].enabled = false;
                    bool lit = false;
                    if (i == target) {
                        float y = Mg.Sliders[i].transform.localPosition.y;
                        lit = done || y >= top - 0.02f;
                    }
                    var want = lit ? OnS : Off;
                    if (Ov[i].sprite != want) Ov[i].sprite = want;
                    var c = Van[i].color;
                    Ov[i].color = new Color(Mathf.Max(c.r, 0.35f), Mathf.Max(c.g, 0.35f), Mathf.Max(c.b, 0.35f), c.a);
                }
            }
        }

        internal static float LanternHeightFactor = 1.6f;

        internal static void ApplyDivert(DivertPowerMinigame mg) {
            if (!Has("task_hw_lantern_off.png") || !Has("task_hw_lantern_on.png")) return;
            if (!Claim(mg)) return;
            var sliders = mg.Sliders;
            if (sliders == null || sliders.Length == 0) return;
            float z = OverlayZ(mg);
            var skin = new DivertSkin { Owner = mg, Mg = mg, Van = new SpriteRenderer[sliders.Length], Ov = new SpriteRenderer[sliders.Length] };
            for (int i = 0; i < sliders.Length; i++) {
                if (sliders[i] == null) continue;
                var v = sliders[i].GetComponent<SpriteRenderer>() ?? sliders[i].GetComponentInChildren<SpriteRenderer>();
                if (v == null) continue;
                var size = LocalSize(v);
                float h = Mathf.Max(size.x, size.y) * LanternHeightFactor;
                var off = Fit("task_hw_lantern_off.png", h, h);
                var on = Fit("task_hw_lantern_on.png", h, h);
                if (off == null || on == null) continue;
                skin.Off = off; skin.OnS = on;
                skin.Van[i] = v;
                skin.Ov[i] = Overlay(v, off, z);
                // the switch's drop shadow would show as a grey box behind the lantern
                foreach (var c in sliders[i].GetComponentsInChildren<SpriteRenderer>(true))
                    if (c != null && c != v && c.name.Contains("Shadow")) c.enabled = false;
            }
            skin.Update();
            live.Add(skin);
            DiagApplied++; DiagLast = $"divert {sliders.Length}";
        }

        // ---- Clear Asteroids ----

        private sealed class WeaponsSkin : Skin {
            internal WeaponsMinigame Mg;
            internal readonly HashSet<int> done = new();
            internal override void Update() {
                var pool = Mg.asteroidPool;
                if (pool == null) return;
                Sweep(pool.activeChildren, true);
                Sweep(pool.inactiveChildren, false);
            }
            private void Sweep(Il2CppSystem.Collections.Generic.List<PoolableBehavior> list, bool active) {
                if (list == null) return;
                for (int i = 0; i < list.Count; i++) {
                    var a = list[i]?.TryCast<Asteroid>();
                    if (a == null) continue;
                    if (done.Add(a.GetInstanceID())) Swap(a);
                    if (active) a.transform.localRotation = Quaternion.identity;
                }
            }
        }

        private static void Swap(Asteroid a) {
            var imgs = a.AsteroidImages;
            if (imgs == null || imgs.Length == 0) return;
            var broken = a.BrokenImages;
            var newImgs = new Il2CppReferenceArray<Sprite>(imgs.Length);
            var newBroken = broken != null ? new Il2CppReferenceArray<Sprite>(broken.Length) : null;
            for (int k = 0; k < imgs.Length; k++) {
                var orig = imgs[k];
                Sprite bat = null;
                if (orig != null) {
                    var b = orig.bounds.size;
                    float m = Mathf.Max(b.x, b.y);
                    bat = Fit($"task_hw_bat_{k % 4 + 1}.png", m, m);
                }
                newImgs[k] = bat ?? orig;
            }
            if (newBroken != null) {
                for (int k = 0; k < broken.Length; k++) {
                    var orig = broken[k];
                    Sprite poof = null;
                    if (orig != null) {
                        var b = orig.bounds.size;
                        float m = Mathf.Max(b.x, b.y);
                        poof = Fit("task_hw_bat_poof.png", m, m);
                    }
                    newBroken[k] = poof ?? orig;
                }
            }
            var sr = a.GetComponent<SpriteRenderer>();
            int idx = a.imgIdx;
            a.AsteroidImages = newImgs;
            if (newBroken != null) a.BrokenImages = newBroken;
            a.RotateSpeed = new FloatRange(0f, 0f);
            try {
                if (sr != null && idx >= 0 && idx < imgs.Length && sr.sprite == imgs[idx]) sr.sprite = newImgs[idx];
            } catch { }
        }

        internal static void ApplyWeapons(WeaponsMinigame mg) {
            if (!Has("task_hw_bat_1.png")) return;
            if (!Claim(mg)) return;
            var skin = new WeaponsSkin { Owner = mg, Mg = mg };
            skin.Update();
            live.Add(skin);
            DiagApplied++; DiagLast = $"weapons pool {mg.asteroidPool?.activeChildren?.Count ?? -1}/{mg.asteroidPool?.inactiveChildren?.Count ?? -1}";
        }

        // ---- Empty Garbage ----

        private sealed class GarbageSkin : Skin {
            internal EmptyGarbageMinigame Mg;
            internal readonly HashSet<string> garbageNames = new();
            internal readonly HashSet<int> done = new();
            internal int Swapped;
            internal override void Update() {
                var objs = Mg.Objects;
                if (objs == null) return;
                for (int i = 0; i < objs.Length; i++) {
                    var o = objs[i];
                    if (o == null) continue;
                    if (!done.Add(o.GetInstanceID())) continue;
                    var sp = o.sprite;
                    if (sp == null || !garbageNames.Contains(sp.name)) continue;
                    var b = sp.bounds.size;
                    var w = Fit($"task_hw_wrapper_{(i % 6) + 1}.png", b.x * 1.1f, b.y * 1.1f);
                    if (w == null) continue;
                    o.sprite = w;
                    Swapped++;
                }
            }
        }

        internal static void ApplyGarbage(EmptyGarbageMinigame mg) {
            if (!Has("task_hw_wrapper_1.png")) return;
            if (!Claim(mg)) return;
            var skin = new GarbageSkin { Owner = mg, Mg = mg };
            var prefabs = mg.GarbagePrefabs;
            if (prefabs != null)
                for (int i = 0; i < prefabs.Length; i++)
                    if (prefabs[i] != null && prefabs[i].sprite != null) skin.garbageNames.Add(prefabs[i].sprite.name);
            skin.Update();
            live.Add(skin);
            DiagApplied++; DiagLast = $"garbage prefabs {skin.garbageNames.Count}, swapped {skin.Swapped}";
        }

        // ---- Fuel Engines ----

        private static readonly Color BrewGreen = new Color(0.47f, 0.83f, 0.27f, 1f);
        private const int BrewLevels = 24;
        // the brew picture: the liquid spans these pixel rows, counted from the bottom of the 400 px canvas
        private const float BrewBottomPx = 55f, BrewTopPx = 300f;

        private sealed class FuelSkin : Skin {
            internal VerticalGauge Gauge;
            internal SpriteRenderer Brew;
            internal Sprite[] Levels;
            private int last = -1;
            internal override void Update() {
                if (Gauge == null || Brew == null) return;
                float v = Mathf.Clamp01(Gauge.value / Mathf.Max(0.01f, Gauge.MaxValue));
                int idx = Mathf.RoundToInt(v * BrewLevels);
                if (idx == last) return;
                last = idx;
                Brew.enabled = idx > 0;
                if (idx > 0) Brew.sprite = Levels[idx];
            }
        }

        private static Texture2D brewTex;
        private static readonly Dictionary<string, Sprite[]> brewLevels = new();
        /// <summary>The brew cropped from the bottom at BrewLevels + 1 fill levels (pivot at the canvas bottom).</summary>
        private static Sprite[] BrewSprites(float worldWidth) {
            string key = worldWidth.ToString("F3");
            if (brewLevels.TryGetValue(key, out var arr) && arr != null && arr[BrewLevels] != null) return arr;
            if (brewTex == null) brewTex = HwArt.LoadTexture(Folder, "task_hw_fuel_brew.png");
            if (brewTex == null) return null;
            float ppu = brewTex.width / Mathf.Max(0.01f, worldWidth);
            float scale = brewTex.height / 400f;
            arr = new Sprite[BrewLevels + 1];
            for (int i = 1; i <= BrewLevels; i++) {
                float h = (BrewBottomPx + (BrewTopPx - BrewBottomPx) * i / BrewLevels) * scale;
                if (i == BrewLevels) h = brewTex.height; // full: the bubbles above the surface too
                var sp = Sprite.Create(brewTex, new Rect(0, 0, brewTex.width, Mathf.Min(h, brewTex.height)), new Vector2(0.5f, 0f), ppu);
                sp.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                arr[i] = sp;
            }
            brewLevels[key] = arr;
            return arr;
        }

        private static readonly Dictionary<string, Sprite> patches = new();
        /// <summary>A plain panel patch: vertical gradient from top to bottom colour, 1 x 1 unit (scaled by the object).</summary>
        private static Sprite Patch(Color top, Color bottom) {
            string key = top.ToString() + bottom.ToString();
            if (patches.TryGetValue(key, out var s) && s != null) return s;
            var tex = new Texture2D(8, 32, TextureFormat.ARGB32, false) { name = "hw_task_patch", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            for (int y = 0; y < 32; y++) {
                var c = Color.Lerp(bottom, top, y / 31f);
                for (int x = 0; x < 8; x++) tex.SetPixel(x, y, c);
            }
            tex.Apply(false, true);
            tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            // 8 x 32 px shown as 1 x 1 unit: the object's scale gives the real size
            s = Sprite.Create(tex, new Rect(0, 0, 8, 32), new Vector2(0.5f, 0.5f), 8f);
            s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            patches[key] = s;
            return s;
        }

        private static SpriteRenderer Part(string name, Transform parent, Sprite sprite, Vector2 local, float z, int order) {
            var go = new GameObject(name) { layer = parent.gameObject.layer };
            go.transform.SetParent(parent, false);
            go.transform.localPosition = new Vector3(local.x, local.y, 0f);
            var wp = go.transform.position;
            go.transform.position = new Vector3(wp.x, wp.y, z);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = order;
            var m = HwLook.SpriteMaterial;
            if (m != null) sr.sharedMaterial = m;
            return sr;
        }

        /// <summary>Panel colour of the refuel station at a local height (measured on the vanilla screenshots).</summary>
        private static Color PanelAt(float localY) {
            var top = new Color(90f / 255f, 93f / 255f, 99f / 255f);
            var bottom = new Color(66f / 255f, 66f / 255f, 66f / 255f);
            return Color.Lerp(bottom, top, Mathf.InverseLerp(-1.6f, 2.1f, localY));
        }

        /// <summary>Cauldron with brew over the can drawn into the station's background.</summary>
        private static FuelSkin BuildCauldron(RefuelStage mg, SpriteRenderer bg, Vector2 patchCenter, Vector2 patchSize,
                                              Vector2 potCenter, float potWidth, float rot, VerticalGauge gauge) {
            var levels = BrewSprites(potWidth);
            var pot = HwArt.Get(Folder, "task_hw_fuel_cauldron.png", potWidth, new Vector2(0.5f, 0.5f), null);
            if (levels == null || pot == null || gauge == null) return null;
            float z = OverlayZ(mg);
            var root = new GameObject(Marker) { layer = bg.gameObject.layer };
            root.transform.SetParent(bg.transform, false);
            int order = bg.sortingOrder + 5;
            var patch = Part("patch", root.transform, Patch(PanelAt(patchCenter.y + patchSize.y / 2f), PanelAt(patchCenter.y - patchSize.y / 2f)), patchCenter, z, order);
            patch.transform.localScale = new Vector3(patchSize.x, patchSize.y / 4f, 1f); // the sprite is 1 x 4 units
            var potGo = new GameObject("pot") { layer = bg.gameObject.layer };
            potGo.transform.SetParent(root.transform, false);
            potGo.transform.localPosition = new Vector3(potCenter.x, potCenter.y, 0f);
            potGo.transform.localEulerAngles = new Vector3(0f, 0f, rot);
            Part("cauldron", potGo.transform, pot, Vector2.zero, z - 0.01f, order + 1);
            var brew = Part("brew", potGo.transform, levels[BrewLevels], new Vector2(0f, -potWidth / 2f), z - 0.02f, order + 2);
            var skin = new FuelSkin { Owner = mg, Gauge = gauge, Brew = brew, Levels = levels };
            skin.Update();
            return skin;
        }

        internal static void ApplyFuel(RefuelStage mg) {
            if (!Claim(mg)) return;
            int tinted = 0;
            foreach (var sr in mg.GetComponentsInChildren<SpriteRenderer>(true))
                if (sr != null && sr.name == "BackFillColor") { sr.color = BrewGreen; tinted++; }
            string what = "fill green only";
            if (Has("task_hw_fuel_cauldron.png") && Has("task_hw_fuel_brew.png")) {
                var bg = mg.transform.Find("Background")?.GetComponent<SpriteRenderer>();
                string sn = bg?.sprite?.name ?? "";
                FuelSkin skin = null;
                if (sn == "engineFuel_gasCanBase") {
                    // first stage: the big gas can (outline in the background picture, fill = destGauge)
                    skin = BuildCauldron(mg, bg, new Vector2(-0.19f, 0.33f), new Vector2(2.9f, 3.6f), new Vector2(-0.19f, 0.25f), 2.75f, 0f, mg.destGauge);
                    what = "cauldron (can)";
                } else if (sn == "engineFuel_fillBase" && mg.srcGauge != null) {
                    // second stage: the small tilted can that pours into the engine tube (fill = srcGauge)
                    var sp = mg.srcGauge.transform.localPosition;
                    skin = BuildCauldron(mg, bg, new Vector2(0.47f, 2.0f), new Vector2(0.95f, 0.72f), new Vector2(sp.x, sp.y), 0.9f, mg.srcGauge.transform.localEulerAngles.z, mg.srcGauge);
                    what = "cauldron (pouring)";
                } else what = $"fill green only (background '{sn}')";
                if (skin != null) live.Add(skin);
            }
            DiagApplied++; DiagLast = $"fuel {what}, fills tinted {tinted}";
        }

        // ---- patches (Begin of each minigame; all substantial methods) ----

        [HarmonyPatch(typeof(ShieldMinigame), nameof(ShieldMinigame.Begin))]
        static class ShieldBegin {
            public static void Postfix(ShieldMinigame __instance) {
                try { ApplyShields(__instance); } catch (Exception e) { Warn("shields: " + e); }
            }
        }

        [HarmonyPatch(typeof(DivertPowerMinigame), nameof(DivertPowerMinigame.Begin))]
        static class DivertBegin {
            public static void Postfix(DivertPowerMinigame __instance) {
                try { ApplyDivert(__instance); } catch (Exception e) { Warn("divert: " + e); }
            }
        }

        [HarmonyPatch(typeof(WeaponsMinigame), nameof(WeaponsMinigame.Begin))]
        static class WeaponsBegin {
            public static void Postfix(WeaponsMinigame __instance) {
                try { ApplyWeapons(__instance); } catch (Exception e) { Warn("weapons: " + e); }
            }
        }

        [HarmonyPatch(typeof(EmptyGarbageMinigame), nameof(EmptyGarbageMinigame.Begin))]
        static class GarbageBegin {
            public static void Postfix(EmptyGarbageMinigame __instance) {
                try { ApplyGarbage(__instance); } catch (Exception e) { Warn("garbage: " + e); }
            }
        }

        [HarmonyPatch(typeof(RefuelStage), nameof(RefuelStage.Begin))]
        static class FuelBegin {
            public static void Postfix(RefuelStage __instance) {
                try { ApplyFuel(__instance); } catch (Exception e) { Warn("fuel: " + e); }
            }
        }
    }
}
