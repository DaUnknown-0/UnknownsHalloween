// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * Haunted Mirrors (idea C1, 2026-10-20)
 *
 * A few mirrors hang on the walls. Whoever stands in front of one shows up in it as themselves: in their real colour
 * from the DefaultOutfit, even while morphed, camouflaged, in a Masquerade costume or as the Xenomorph. Everybody who
 * sees the mirror sees the reflection (a world object on layer 11 under the light system's shadow). After a
 * reflection the glass fogs up for a while (option), so a mirror is a short glimpse, not a permanent scanner.
 *
 *  - Places, the same on every client without any message (pure geometry):
 *      Hollowmere Manor: above the dressing table (Atlas prop "schminktisch"), Ravenhollow Cemetery: the north wall
 *      of the chapel, original maps: two or three north walls of the biggest rooms, other Atlas maps (option): two.
 *    A north wall = a straight wall face found by a ray going north from inside the room, with free floor in front.
 *  - The reflection is an own renderer (a bean drawn at runtime, tinted with Palette.PlayerColors/ShadowColors of
 *    DefaultOutfit.ColorId, the way the kill scenes tint their victims). Phantoms of the Phantom Parade are no
 *    PlayerControls, so they have no reflection. Ghosts, players in vents and an invisible Ninja have none either.
 *  - Pictures: Resources/hw2026/mirror/mirror_<vanilla|villa|graveyard>.png (160x220, glass free at x 30-130 and
 *    y 30-170 from the top) and mirror_glass.png (100x140, behind the reflection). Missing files are drawn at runtime.
 *
 * Options 2065-2067, no RPC. Self test: UC_HALLOWEEN_DIAG=mirror (HwMechanicsDiag.cs).
 */

using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using TheOtherRoles;
using Types = TheOtherRoles.CustomOption.CustomOptionType;

namespace UnknownsHalloween {
    internal static class HwMirrors {
        private const string Folder = "mirror";

        // ---- options (2065-2067) ----
        public static CustomOption On, FogTime, OnAtlas;
        private static readonly string[] FogLabels = { "Off", "5s", "10s", "15s" };
        private static readonly float[] FogSeconds = { 0f, 5f, 10f, 15f };

        internal static void CreateOptions() {
            try {
                var g = Types.General;
                On = CustomOption.Create(2065, g, "Haunted Mirrors", false, null, true, null, "Haunted Mirrors");
                FogTime = CustomOption.Create(2066, g, "Mirrors Fog After A Reflection", FogLabels, On);
                OnAtlas = CustomOption.Create(2067, g, "Haunted Mirrors On Atlas Maps", true, On);
                try { FogTime.selection = 2; } catch { }        // 10 s
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Mirrors] options failed: {e}"); }
        }

        internal static bool DiagForce;
        internal static bool Enabled() { if (DiagForce) return true; try { return On != null && On.getBool(); } catch { return false; } }
        private static float FogFor() => FogSeconds[Mathf.Clamp(FogTime?.getSelection() ?? 2, 0, FogSeconds.Length - 1)];
        private static bool AtlasAllowed() { if (DiagForce) return true; try { return OnAtlas == null || OnAtlas.getBool(); } catch { return true; } }

        // ---- geometry of the picture (px of the 160x220 frame) ----
        internal const float Width = 0.8f;                                // world units across
        private const float PicW = 160f, PicH = 220f;
        private const float GlassX0 = 30f, GlassX1 = 130f, GlassTop = 30f, GlassBottom = 170f;     // from the top
        private static float U(float px) => px / PicW * Width;
        internal static float Height => U(PicH);
        private static Vector2 GlassCenter => new Vector2(0f, U(PicH - (GlassTop + GlassBottom) * 0.5f));   // from the foot (pivot bottom middle)
        private static Vector2 GlassSize => new Vector2(U(GlassX1 - GlassX0), U(GlassBottom - GlassTop));
        private const float Reach = 2.6f;                                 // how far in front a player still shows up
        private const int MaxShown = 3;

        internal sealed class Mirror {
            public Vector2 Foot;            // bottom middle, on the wall line
            public string Room = "";
            public GameObject Go;
            public SpriteRenderer Glass, Fog, Frame;
            public readonly List<(SpriteRenderer body, SpriteRenderer shade, SpriteRenderer visor)> Refl = new();
            public float SeenSince = -1f, FogUntil = -1f, FogStart = -1f;
            public readonly Dictionary<byte, Vector2> LastPos = new();
        }

        internal static readonly List<Mirror> mirrors = new();
        private static IntPtr placedFor;
        private static string placedMap;
        internal static string Style = "vanilla";
        internal static int DiagShown;                     // self test: reflections drawn in the last frame
        internal static readonly List<string> DiagLog = new();

        // ================================================================ placement
        private static bool IsAtlasWall(Collider2D c) {
            try { return c != null && c.gameObject.name.StartsWith("Wall_", StringComparison.Ordinal); } catch { return false; }
        }

        private static bool IsDoor(Collider2D c) {
            try {
                if (c == null) return false;
                if (c.GetComponentInParent<OpenableDoor>() != null) return true;
                return c.gameObject.name.IndexOf("door", StringComparison.OrdinalIgnoreCase) >= 0;
            } catch { return false; }
        }

        private static bool FirstHit(Vector2 from, Vector2 dir, float dist, int mask, bool atlas, out RaycastHit2D hit) {
            hit = default;
            bool any = false;
            try {
                foreach (var h in Physics2D.RaycastAll(from, dir, dist, mask)) {
                    if (h.collider == null || h.collider.isTrigger) continue;
                    if (atlas && !IsAtlasWall(h.collider)) continue;          // furniture on the Atlas maps is skipped
                    if (!any || h.distance < hit.distance) { hit = h; any = true; }
                }
            } catch { return false; }
            return any;
        }

        private static bool Blocked(Vector2 p, float r, int mask) {
            try { foreach (var c in Physics2D.OverlapCircleAll(p, r, mask)) if (c != null && !c.isTrigger) return true; } catch { return true; }
            return false;
        }

        /// <summary>A straight north wall above a point of the room: the foot of a mirror, or null.</summary>
        private static Vector2? NorthWall(PlainShipRoom room, Vector2 p, bool atlas) {
            int mask = Constants.ShipAndObjectsMask;
            if (!FirstHit(p, Vector2.up, 12f, mask, atlas, out var hit) || hit.normal.y > -0.8f || IsDoor(hit.collider)) return null;
            float wy = hit.point.y;
            // straight over the mirror's width
            foreach (float dx in new[] { -Width * 0.5f, Width * 0.5f }) {
                var from = new Vector2(hit.point.x + dx, wy - 0.4f);
                if (!FirstHit(from, Vector2.up, 1.0f, mask, atlas, out var h2) || Mathf.Abs(h2.point.y - wy) > 0.08f || IsDoor(h2.collider)) return null;
            }
            // free floor in front (somebody has to be able to stand there)
            if (Blocked(new Vector2(hit.point.x, wy - 0.55f), 0.3f, mask)) return null;
            // the wall belongs to this room (not a far wall seen through a door gap)
            if (room != null && room.roomArea != null && !room.roomArea.OverlapPoint(new Vector2(hit.point.x, wy - 0.3f))) return null;
            return new Vector2(hit.point.x, wy + 0.02f);
        }

        private static Vector2? WallOfRoom(PlainShipRoom room, bool atlas) {
            if (room == null || room.roomArea == null) return null;
            var bb = room.roomArea.bounds;
            foreach (float fy in new[] { 0.45f, 0.3f, 0.6f })
                foreach (float fx in new[] { 0.5f, 0.38f, 0.62f, 0.25f, 0.75f }) {
                    var p = new Vector2(Mathf.Lerp(bb.min.x, bb.max.x, fx), Mathf.Lerp(bb.min.y, bb.max.y, fy));
                    if (!room.roomArea.OverlapPoint(p) || Blocked(p, 0.3f, Constants.ShipAndObjectsMask)) continue;
                    var w = NorthWall(room, p, atlas);
                    if (w.HasValue) return w;
                }
            return null;
        }

        private static float Area(PlainShipRoom r) { try { var s = r.roomArea.bounds.size; return s.x * s.y; } catch { return 0f; } }

        private static List<(Vector2 foot, string room)> FindSpots(ShipStatus ship, string atlasMap) {
            var spots = new List<(Vector2, string)>();
            var rooms = new List<PlainShipRoom>();
            try { foreach (var r in ship.AllRooms) if (r != null && r.roomArea != null && r.RoomId != SystemTypes.Outside && r.RoomId != SystemTypes.Hallway) rooms.Add(r); } catch { }
            bool atlas = atlasMap != null;
            if (atlasMap == "villa") {
                // above the dressing table(s)
                try {
                    var root = GameObject.Find("Atlas_Props");
                    if (root != null)
                        foreach (var sr in root.GetComponentsInChildren<SpriteRenderer>()) {
                            if (sr == null || !sr.gameObject.name.StartsWith("Prop_schminktisch", StringComparison.OrdinalIgnoreCase)) continue;
                            var b = sr.bounds;
                            var room = HwMechanics.RoomAt(new Vector2(b.center.x, b.min.y));
                            // the wall behind the table: north from the floor in front of it
                            var w = NorthWall(room, new Vector2(b.center.x, b.min.y - 0.3f), true);
                            var foot = w ?? new Vector2(b.center.x, b.max.y - 0.15f);
                            if (spots.All(s => (s.Item1 - foot).sqrMagnitude > 4f)) spots.Add((foot, room != null ? room.RoomId.ToString() : "?"));
                        }
                } catch (Exception e) { HwMechanics.Warn($"mirrors: villa props: {e.Message}"); }
                return spots;
            }
            if (atlasMap == "graveyard") {
                // the chapel carries SystemTypes.Cafeteria (map.json, key "chapel")
                var chapel = rooms.FirstOrDefault(r => r.RoomId == SystemTypes.Cafeteria);
                var w = WallOfRoom(chapel, true);
                if (w.HasValue) spots.Add((w.Value, "chapel"));
                return spots;
            }
            int want = atlas ? 2 : 3;
            foreach (var r in rooms.OrderByDescending(Area).ThenBy(r => (int)r.RoomId)) {
                if (spots.Count >= want) break;
                var w = WallOfRoom(r, atlas);
                if (!w.HasValue) continue;
                if (spots.Any(s => (s.Item1 - w.Value).sqrMagnitude < 8f * 8f)) continue;
                spots.Add((w.Value, r.RoomId.ToString()));
            }
            return spots;
        }

        private static void EnsurePlaced() {
            var ship = ShipStatus.Instance;
            if (ship == null) return;
            string map = HwMechanics.AtlasMap();
            if (placedFor == ship.Pointer && placedMap == map && (mirrors.Count == 0 || mirrors[0].Go != null)) return;
            Clear();
            placedFor = ship.Pointer;
            placedMap = map;
            if (map != null && map != "villa" && map != "graveyard" && !AtlasAllowed()) { HwMechanics.Log($"mirrors: none on Atlas map {map} (option)."); return; }
            Style = map == "villa" ? "villa" : map == "graveyard" ? "graveyard" : "vanilla";
            foreach (var (foot, room) in FindSpots(ship, map)) {
                var m = new Mirror { Foot = foot, Room = room };
                Build(m);
                mirrors.Add(m);
            }
            HwMechanics.Log($"mirrors: {mirrors.Count} on {(map ?? ship.name)}: " + string.Join(", ", mirrors.Select(m => $"{m.Room} ({m.Foot.x:F2}, {m.Foot.y:F2})")));
        }

        // ================================================================ objects
        private static GameObject root;

        private static SpriteRenderer Part(GameObject parent, string name, Sprite s, Vector3 local) {
            var go = new GameObject(name) { layer = 11 };
            go.transform.SetParent(parent.transform, false);
            go.transform.localPosition = local;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = s;
            return sr;
        }

        private static void Build(Mirror m) {
            if (root == null) { root = new GameObject("HauntedMirrors") { layer = 11 }; }
            float feet = 0.36f;
            try { feet = HwMechanics.FeetOffset(PlayerControl.LocalPlayer); } catch { }
            var go = new GameObject("mirror_" + m.Room) { layer = 11 };
            go.transform.SetParent(root.transform, false);
            go.transform.position = new Vector3(m.Foot.x, m.Foot.y, (m.Foot.y + feet) / 1000f);
            m.Go = go;
            var gc = GlassCenter;
            // back to front: glass, reflections, fog, frame (the frame covers the glass edges)
            m.Glass = Part(go, "glass", GlassSprite(), new Vector3(gc.x, gc.y, 0f));
            for (int i = 0; i < MaxShown; i++) {
                float z = -0.00002f - i * 0.000004f;
                var b = Part(go, "refl" + i, BeanSprite(0), new Vector3(0f, 0f, z));
                var sh = Part(b.gameObject, "shade", BeanSprite(1), new Vector3(0f, 0f, -0.000001f));
                var v = Part(b.gameObject, "visor", BeanSprite(2), new Vector3(0f, 0f, -0.000002f));
                b.enabled = sh.enabled = v.enabled = false;
                m.Refl.Add((b, sh, v));
            }
            m.Fog = Part(go, "fog", FogSprite(), new Vector3(gc.x, gc.y, -0.00004f));
            m.Fog.color = new Color(1f, 1f, 1f, 0f);
            m.Frame = Part(go, "frame", FrameSprite(Style), new Vector3(0f, 0f, -0.00005f));
        }

        internal static void Clear() {
            foreach (var m in mirrors) if (m.Go != null) UnityEngine.Object.Destroy(m.Go);
            mirrors.Clear();
            if (root != null) UnityEngine.Object.Destroy(root);
            root = null;
            placedFor = IntPtr.Zero;
            placedMap = null;
        }

        internal static void Reset() => Clear();

        // ================================================================ per frame
        private static bool Reflectable(PlayerControl p) {
            if (p == null || p.Data == null || p.Data.IsDead || p.Data.Disconnected) return false;
            try { if (p.inVent) return false; } catch { }
            try { if (Ninja.ninja != null && p == Ninja.ninja && Ninja.isInvisble) return false; } catch { }
            return true;
        }

        // reused every frame instead of a LINQ chain per mirror (audit 21.10.)
        private static readonly List<PlayerControl> playersBuf = new List<PlayerControl>();
        private static readonly List<(PlayerControl p, float d, Vector2 pos)> nearBuf = new List<(PlayerControl, float, Vector2)>();

        internal static void Tick() {
            if (!Enabled() || !HwMechanics.InRound()) { if (mirrors.Count > 0 || root != null) Clear(); DiagShown = 0; return; }
            EnsurePlaced();
            if (mirrors.Count == 0) return;
            bool meeting = HwMechanics.InMeeting();
            int shown = 0;
            var players = playersBuf;
            players.Clear();
            if (!meeting) foreach (var p in PlayerControl.AllPlayerControls) if (Reflectable(p)) players.Add(p);
            foreach (var m in mirrors) {
                if (m.Go == null) continue;
                var front = m.Foot + new Vector2(0f, -0.55f);
                var near = nearBuf;
                near.Clear();
                foreach (var p in players) {
                    var pos = p.GetTruePosition();
                    float d = (pos - front).magnitude;
                    if (d >= Reach || pos.y >= m.Foot.y + 0.2f) continue;
                    int at = near.Count;
                    while (at > 0 && near[at - 1].d > d) at--;   // sorted insert, nearest first
                    if (at >= MaxShown) continue;
                    near.Insert(at, (p, d, pos));
                    if (near.Count > MaxShown) near.RemoveAt(MaxShown);
                }
                // fog: after a reflection stayed for 1.5 s, the glass fogs up
                float fog = FogFor();
                bool fogged = m.FogUntil > Time.time;
                if (!fogged && fog > 0f) {
                    if (near.Count > 0) { if (m.SeenSince < 0f) m.SeenSince = Time.time; }
                    else m.SeenSince = -1f;
                    if (m.SeenSince > 0f && Time.time - m.SeenSince > 1.5f) { m.FogStart = Time.time; m.FogUntil = Time.time + fog; m.SeenSince = -1f; fogged = true; }
                }
                float fogA = 0f;
                if (m.FogUntil > Time.time) {
                    float t = Time.time - m.FogStart, left = m.FogUntil - Time.time;
                    fogA = Mathf.Clamp01(t / 0.8f) * Mathf.Clamp01(left / 1.2f);
                }
                if (m.Fog != null) m.Fog.color = new Color(0.92f, 0.94f, 0.97f, 0.88f * fogA);
                var gc = GlassCenter;
                var gs = GlassSize;
                for (int i = 0; i < m.Refl.Count; i++) {
                    var (b, sh, v) = m.Refl[i];
                    if (b == null) continue;
                    if (i >= near.Count) { b.enabled = sh.enabled = v.enabled = false; continue; }
                    var (p, d, pos) = near[i];
                    int cid = 0;
                    try { cid = p.Data.DefaultOutfit.ColorId; } catch { }
                    Color body = Color.white, shade = Color.gray;
                    try { body = Palette.PlayerColors[cid]; shade = Palette.ShadowColors[cid]; } catch { }
                    // closer = bigger, a little parallax across the glass, never outside it
                    float k = Mathf.Clamp01(d / Reach);
                    float size = Mathf.Lerp(0.62f, 0.44f, k) * Mathf.Min(1f, gs.y / 0.85f);
                    float x = Mathf.Clamp((pos.x - m.Foot.x) * 0.45f, -gs.x * 0.5f + size * 0.42f, gs.x * 0.5f - size * 0.42f);
                    bool moving = m.LastPos.TryGetValue(p.PlayerId, out var last) && (pos - last).sqrMagnitude > 0.00002f;
                    m.LastPos[p.PlayerId] = pos;
                    float bob = moving ? Mathf.Abs(Mathf.Sin(Time.time * 11f + p.PlayerId)) * 0.025f : 0f;
                    float y = gc.y - gs.y * 0.5f + size * 0.5f + 0.03f + bob + k * 0.08f;
                    bool flip = false;
                    try { flip = p.cosmetics.FlipX; } catch { }
                    b.transform.localPosition = new Vector3(x, y, b.transform.localPosition.z);
                    b.transform.localScale = new Vector3(flip ? -size : size, size, 1f);
                    // ghostly: a touch transparent, fading in with nearness, gone under the fog
                    float a = Mathf.Clamp01((Reach - d) / 0.6f) * 0.9f * (1f - fogA);
                    b.color = new Color(body.r, body.g, body.b, a);
                    sh.color = new Color(shade.r, shade.g, shade.b, a);
                    v.color = new Color(0.66f, 0.80f, 0.86f, a);
                    b.enabled = sh.enabled = v.enabled = a > 0.01f;
                    if (b.enabled) shown++;
                }
            }
            DiagShown = shown;
        }

        // ================================================================ pictures
        private static Sprite[] bean = new Sprite[3];

        /// <summary>0 body mask, 1 shade mask, 2 visor; 128 px, 1 unit, pivot in the middle.</summary>
        internal static Sprite BeanSprite(int part) {
            if (bean[part] != null) return bean[part];
            var cv = new TreatFx.Canvas(128, 128);
            var w = Color.white;
            switch (part) {
                case 0:
                    cv.Ellipse(58f, 74f, 34f, 42f, w);                 // body
                    cv.Rect(24f, 30f, 92f, 74f, w);
                    cv.Ellipse(96f, 64f, 12f, 24f, w);                 // backpack
                    cv.Ellipse(38f, 22f, 13f, 14f, w);                 // legs
                    cv.Ellipse(76f, 22f, 13f, 14f, w);
                    cv.Outline(HwArt.C(0.05f, 0.05f, 0.07f), 4);
                    break;
                case 1:
                    cv.Rect(24f, 30f, 92f, 46f, w);                    // lower body shadow
                    cv.Ellipse(98f, 56f, 9f, 18f, w);
                    cv.Ellipse(38f, 20f, 11f, 10f, w);
                    cv.Ellipse(76f, 20f, 11f, 10f, w);
                    break;
                default:
                    cv.Ellipse(44f, 82f, 24f, 14f, HwArt.C(0.05f, 0.05f, 0.07f));
                    cv.Ellipse(44f, 82f, 21f, 11f, w);
                    cv.Ellipse(38f, 86f, 9f, 4f, HwArt.C(1f, 1f, 1f));
                    break;
            }
            var tex = cv.ToTexture("hw_mirror_bean" + part);
            bean[part] = Sprite.Create(tex, new Rect(0, 0, 128, 128), new Vector2(0.5f, 0.5f), 128f);
            bean[part].hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return bean[part];
        }

        internal static Sprite FrameSprite(string style) =>
            HwArt.Get(Folder, $"mirror_{style}.png", Width, new Vector2(0.5f, 0f), () => DrawFrame(style));

        internal static Sprite GlassSprite() =>
            HwArt.Get(Folder, "mirror_glass.png", GlassSize.x, new Vector2(0.5f, 0.5f), DrawGlass);

        private static Sprite fogSprite;
        private static Sprite FogSprite() {
            if (fogSprite != null) return fogSprite;
            var cv = new TreatFx.Canvas(100, 140);
            var rng = new System.Random(3);
            for (int i = 0; i < 70; i++)
                cv.Disc((float)rng.NextDouble() * 100f, (float)rng.NextDouble() * 140f, 8f + (float)rng.NextDouble() * 16f, HwArt.C(1f, 1f, 1f, 0.22f));
            for (int i = 0; i < 9; i++) {
                float x = 8f + i * 10.5f, y0 = 20f + (float)rng.NextDouble() * 80f;
                cv.Line(x, y0, x + 1f, y0 - 14f - (float)rng.NextDouble() * 18f, 1.5f, HwArt.C(0.75f, 0.82f, 0.9f, 0.5f));    // droplet trails
            }
            var tex = cv.ToTexture("hw_mirror_fog");
            fogSprite = Sprite.Create(tex, new Rect(0, 0, 100, 140), new Vector2(0.5f, 0.5f), 100f / GlassSize.x);
            fogSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return fogSprite;
        }

        // 160x220, y from the bottom; glass free at x 30-130, y 50-190 (= 30-170 from the top)
        internal static TreatFx.Canvas DrawFrame(string style) {
            var cv = new TreatFx.Canvas((int)PicW, (int)PicH);
            Color frame, dark, light;
            switch (style) {
                case "villa": frame = HwArt.C(0.78f, 0.60f, 0.26f); dark = HwArt.C(0.45f, 0.32f, 0.12f); light = HwArt.C(0.95f, 0.82f, 0.45f); break;
                case "graveyard": frame = HwArt.C(0.42f, 0.44f, 0.42f); dark = HwArt.C(0.22f, 0.24f, 0.23f); light = HwArt.C(0.62f, 0.64f, 0.60f); break;
                default: frame = HwArt.C(0.70f, 0.72f, 0.76f); dark = HwArt.C(0.38f, 0.40f, 0.45f); light = HwArt.C(0.90f, 0.92f, 0.95f); break;
            }
            cv.Rect(18f, 34f, 142f, 206f, dark);
            cv.Rect(21f, 37f, 139f, 203f, frame);
            cv.Rect(24f, 40f, 136f, 200f, light);
            cv.Rect(27f, 44f, 133f, 196f, frame);
            // crest on top, a little shelf below
            if (style == "villa") {
                cv.Ellipse(80f, 208f, 30f, 10f, frame); cv.Ring(80f, 208f, 30f, 10f, 2f, dark); cv.Disc(80f, 216f, 4f, light);
                cv.Disc(22f, 204f, 6f, frame); cv.Disc(138f, 204f, 6f, frame);
            } else if (style == "graveyard") {
                cv.Tri(52f, 206f, 108f, 206f, 80f, 219f, frame); cv.Disc(80f, 210f, 3f, dark);
            } else {
                cv.Rect(64f, 206f, 96f, 212f, frame);
            }
            cv.Rect(14f, 26f, 146f, 36f, dark);
            cv.Rect(16f, 28f, 144f, 34f, frame);
            cv.Ellipse(80f, 14f, 60f, 8f, HwArt.C(0f, 0f, 0f, 0.0f));
            // the glass stays free
            for (int y = 50; y < 190; y++) for (int x = 30; x < 130; x++) cv.Px[y * cv.W + x] = new Color(0f, 0f, 0f, 0f);
            cv.Outline(HwArt.C(0.05f, 0.04f, 0.04f, 0.9f), 2);
            for (int y = 51; y < 189; y++) for (int x = 31; x < 129; x++) cv.Px[y * cv.W + x] = new Color(0f, 0f, 0f, 0f);
            return cv;
        }

        internal static TreatFx.Canvas DrawGlass() {
            var cv = new TreatFx.Canvas(100, 140);
            for (int y = 0; y < 140; y++)
                for (int x = 0; x < 100; x++) {
                    float t = y / 139f;
                    cv.Px[y * 100 + x] = new Color(Mathf.Lerp(0.10f, 0.20f, t), Mathf.Lerp(0.13f, 0.24f, t), Mathf.Lerp(0.18f, 0.32f, t), 1f);
                }
            // two diagonal shine bands
            cv.Tri(8f, 140f, 30f, 140f, -40f, 20f, HwArt.C(1f, 1f, 1f, 0.10f));
            cv.Tri(-40f, 20f, -18f, 20f, 30f, 140f, HwArt.C(1f, 1f, 1f, 0.10f));
            cv.Tri(44f, 140f, 54f, 140f, 4f, 40f, HwArt.C(1f, 1f, 1f, 0.07f));
            return cv;
        }
    }
}
