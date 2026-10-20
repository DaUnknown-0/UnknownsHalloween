// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Trick or Treat on the own maps (2026-10-20): the candies hide in cabinets instead of lying on the floor.
 *
 *  - Own maps = the Atlas maps museum, wald, park, train and the Halloween maps villa, graveyard. Which one stands
 *    is read from the AppDomain entry "UnknownsAtlas.ActiveMap" (set by Atlas once the map is built, null on the
 *    original maps), so this file needs no Atlas types. The map key is also the cabinet style.
 *  - The host places the cabinets once per round at the first spawn (twice as many as candies), against the walls
 *    of the rooms: from every reachable floor point (TrickOrTreat.BuildReachable) a ray goes north; when it ends
 *    on an Atlas wall ("Wall_<i>", not furniture), the wall is straight over the cabinet's width, the footprint and
 *    the floor in front are free and no console, vent or door is near, that is a candidate. Picked round-robin
 *    over the rooms with a minimum spacing, hallways last; side walls only when the north walls run out.
 *    Sub 6 carries the positions to everybody.
 *  - Every spawn (round start, after every meeting) the host puts the candies into random cabinets: a candy in a
 *    cabinet has the cabinet's position in Sub 0, the clients match it. All cabinets close again.
 *  - Searching: the Use button says SEARCH; hold it (or E) for two seconds without moving. Moving, letting go, a
 *    meeting or death break it off. Then Sub 7 asks the host, which checks distance and state and answers with
 *    Sub 8 (the cabinet stands open for everybody); a candy inside is eaten through the normal HostEat path.
 *  - Pictures: Resources/treats/cabinet_<style>_closed.png, _open.png, _glow.png (160x200, all three congruent,
 *    stand line at y 178 from the top, floor shadow below; Grafik-Lieferung 2026-10-20) and cabinet_search_icon.png
 *    (128x128). The glow lies over the cabinet while it is searched and fades over the open one. Missing files are
 *    drawn at runtime (Draw*), so a new picture only needs to be dropped in and built.
 *  - No collider: the cabinets never block a path. World layer 11, depth by the foot line like Atlas' props.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using Hazel;
using UnityEngine;
using TheOtherRoles;
using UnknownsCollection;

namespace UnknownsHalloween {
    internal static class TreatCabinets {
        private const string LogPrefix = TrickOrTreat.LogPrefix;
        internal const byte None = 255;
        internal static readonly string[] Styles = { "museum", "wald", "park", "train", "villa", "graveyard" };

        internal const float Width = 0.8f, Height = 1.0f;     // world units of the 160x200 picture
        private const float PicW = 160f, PicH = 200f, FloorPx = 22f;   // stand line 178 px from the top, the floor shadow below it
        private const float Depth = 0.3f;                      // foot line in front of the wall
        internal const float SearchSeconds = 2f;

        internal sealed class Cabinet {
            public byte Index;
            public Vector2 Pos;                     // foot line middle (true-position space, like the candies)
            public Vector2 Front = Vector2.down;    // host only: where the player stands
            public bool Open, Pending;
            public float PendingAt, GlowUntil;
            public string Room = "";               // host only, for the log
            public GameObject Go;
            public SpriteRenderer Sr, GlowSr;
        }

        internal static readonly List<Cabinet> cabinets = new();
        internal static bool Any => cabinets.Count > 0;
        private static IntPtr placedFor;
        private static readonly System.Random rnd = new System.Random();

        // ================================================================ map
        internal static string MapKey() {
            try { return AppDomain.CurrentDomain.GetData("UnknownsAtlas.ActiveMap") as string; } catch { return null; }
        }

        /// <summary>Cabinet style of the map that stands, null on the original maps (candies on the floor).</summary>
        internal static string Style() {
            var k = MapKey();
            if (string.IsNullOrEmpty(k) || ShipStatus.Instance == null) return null;
            k = k.ToLowerInvariant();
            return Styles.Contains(k) ? k : null;
        }

        internal static float SearchRange() => Mathf.Max(TrickOrTreat.Range(), 0.95f);

        // Atlas' own Use button (lookout, gondola, secret passages, candles ...): AtlasUse._owned through reflection,
        // no Atlas types here. While a station holds the button, candies and cabinets leave it alone.
        private static System.Reflection.FieldInfo atlasOwned;
        private static bool atlasOwnedTried;
        internal static bool AtlasOwnsUse() {
            try {
                if (!atlasOwnedTried) {
                    atlasOwnedTried = true;
                    var t = AppDomain.CurrentDomain.GetAssemblies().Select(a => a.GetType("UnknownsAtlas.AtlasUse", false)).FirstOrDefault(x => x != null);
                    atlasOwned = t?.GetField("_owned", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic);
                }
                return atlasOwned != null && MapKey() != null && (bool)atlasOwned.GetValue(null);
            } catch { return false; }
        }

        // interactive furniture of the Halloween maps (secret passages, grandfather clock, candelabras): no cabinet in front
        private static readonly string[] UsableKinds = { "wandteppich", "drehregal", "speiseaufzug", "tunneleingang", "standuhr", "kandelaber" };
        private static List<Vector2> UsableProps() {
            var l = new List<Vector2>();
            try {
                var root = GameObject.Find("Atlas_Props");
                if (root == null) return l;
                foreach (var sr in root.GetComponentsInChildren<SpriteRenderer>()) {
                    if (sr == null) continue;
                    string n = sr.gameObject.name;
                    foreach (var k in UsableKinds)
                        if (n.StartsWith("Prop_" + k, StringComparison.OrdinalIgnoreCase)) { var b = sr.bounds; l.Add(new Vector2(b.center.x, b.min.y)); break; }
                }
            } catch { }
            return l;
        }

        // ================================================================ placement (host)
        private struct Cand { public Vector2 Foot, Front; public PlainShipRoom Room; public int Tier; }

        private static bool IsWall(Collider2D c) {
            try { return c != null && c.gameObject.name.StartsWith("Wall_", StringComparison.Ordinal); } catch { return false; }
        }

        private static bool FirstHit(Vector2 from, Vector2 dir, float dist, int mask, out RaycastHit2D hit) {
            hit = default;
            bool any = false;
            try {
                foreach (var h in Physics2D.RaycastAll(from, dir, dist, mask)) {
                    if (h.collider == null || h.collider.isTrigger) continue;
                    if (!any || h.distance < hit.distance) { hit = h; any = true; }
                }
            } catch { return false; }
            return any;
        }

        // Things with a Use range of their own. The big ones (emergency button, admin table, cameras, the freeplay
        // laptop) reach far: their range would take the Use button away from the cabinet (test 20.10., Museum foyer).
        private static List<Vector2> Avoid(ShipStatus ship, List<Vector2> far) {
            var l = new List<Vector2>();
            try { foreach (var c in UnityEngine.Object.FindObjectsOfType<Console>()) if (c != null) l.Add(c.transform.position); } catch { }
            try { foreach (var v in ship.AllVents) if (v != null) l.Add(v.transform.position); } catch { }
            try { foreach (var c in UnityEngine.Object.FindObjectsOfType<SystemConsole>()) if (c != null) far.Add(c.transform.position); } catch { }
            try { foreach (var c in UnityEngine.Object.FindObjectsOfType<MapConsole>()) if (c != null) far.Add(c.transform.position); } catch { }
            try { foreach (var c in UnityEngine.Object.FindObjectsOfType<OptionsConsole>()) if (c != null) far.Add(c.transform.position); } catch { }
            try { foreach (var c in UnityEngine.Object.FindObjectsOfType<DeconControl>()) if (c != null) far.Add(c.transform.position); } catch { }
            try { foreach (var c in UnityEngine.Object.FindObjectsOfType<PlatformConsole>()) if (c != null) far.Add(c.transform.position); } catch { }
            try { foreach (var c in UnityEngine.Object.FindObjectsOfType<ZiplineConsole>()) if (c != null) far.Add(c.transform.position); } catch { }
            far.AddRange(UsableProps());
            try {
                // the secret passages' entries and exits of Hollowmere Manor (they are spots, not always props)
                if (MapKey() == HollowmereMap.Key)
                    foreach (var sec in (HollowmereMap.Large ? VillaLarge.Secrets : VillaSmall.Secrets)) { far.Add(sec.Entry); far.Add(sec.Exit); }
            } catch { }
            return l;
        }
        private static List<Vector2> farAvoid = new();

        private static List<Vector2> Doors(ShipStatus ship) {
            var l = new List<Vector2>();
            try { foreach (var d in ship.AllDoors) if (d != null) l.Add(d.transform.position); } catch { }
            return l;
        }

        // Atlas' furniture pictures (no collider of their own for flat or wall-hung things): a cabinet should not
        // cover a painting or stand in a shelf. Huge pictures (canopies, backdrops) do not count.
        private static List<Bounds> PropBounds() {
            var l = new List<Bounds>();
            try {
                var root = GameObject.Find("Atlas_Props");
                if (root == null) return l;
                foreach (var sr in root.GetComponentsInChildren<SpriteRenderer>()) {
                    if (sr == null || sr.sprite == null) continue;
                    var b = sr.bounds;
                    if (b.size.x * b.size.y > 10f) continue;
                    l.Add(b);
                }
            } catch { }
            return l;
        }

        private static bool Near(List<Vector2> pts, Vector2 p, float r) {
            foreach (var q in pts) if ((q - p).sqrMagnitude < r * r) return true;
            return false;
        }

        private static int rejWall, rejFlush, rejFree, rejNear, rejProp;
        private static readonly Dictionary<string, int> rejHits = new();
        private static readonly Dictionary<string, int> roomCands = new();

        // North wall above p (the usual "against the back wall" look). Tier 0 clean, 1 overlaps a furniture picture.
        private static bool TryNorth(Vector2 p, PlainShipRoom room, int mask, int fullMask, List<Vector2> avoid, List<Vector2> doors, List<Bounds> props, out Cand c) {
            c = default;
            if (!FirstHit(p, Vector2.up, 7f, mask, out var hit) || !IsWall(hit.collider) || hit.normal.y > -0.8f) {
                rejWall++;
                string key = hit.collider == null ? "nothing" : (IsWall(hit.collider) ? "slanted wall" : hit.collider.gameObject.name.Split('_', '(')[0]);
                rejHits[key] = rejHits.TryGetValue(key, out int k) ? k + 1 : 1;
                return false;
            }
            float wy = hit.point.y;
            var foot = new Vector2(p.x, wy - Depth);
            if ((foot - p).y < -0.05f) { rejWall++; return false; }        // the sample stood right at the wall already
            foreach (float dx in new[] { -0.36f, 0.36f }) {
                var from = new Vector2(foot.x + dx, foot.y - 0.15f);
                if (!FirstHit(from, Vector2.up, 1.2f, mask, out var h2) || !IsWall(h2.collider) || Mathf.Abs(h2.point.y - wy) > 0.08f) { rejFlush++; return false; }
            }
            if (TrickOrTreat.Blocked(foot, 0.2f, fullMask) || TrickOrTreat.Blocked(foot + new Vector2(-0.3f, 0f), 0.2f, fullMask)
                || TrickOrTreat.Blocked(foot + new Vector2(0.3f, 0f), 0.2f, fullMask) || TrickOrTreat.Blocked(foot + new Vector2(0f, -1.0f), 0.32f, fullMask)) { rejFree++; return false; }
            var front = foot + new Vector2(0f, -0.45f);
            if (TrickOrTreat.Blocked(front, 0.3f, fullMask) || !TrickOrTreat.Clear(p, front, mask)) { rejFree++; return false; }
            if (Near(avoid, foot, 1.3f) || Near(avoid, front, 1.1f) || Near(doors, foot, 1.6f) || Near(farAvoid, foot, 2.4f) || Near(farAvoid, front, 2.2f)) { rejNear++; return false; }
            int tier = 0;
            var box = new Bounds(new Vector3(foot.x, foot.y + Height * 0.5f, 0f), new Vector3(Width * 0.9f, Height, 100f));
            foreach (var b in props) {
                var bb = new Bounds(new Vector3(b.center.x, b.center.y, 0f), new Vector3(b.size.x, b.size.y, 100f));
                if (bb.Intersects(box)) { tier = 1; break; }
            }
            if (tier == 1) rejProp++;
            c = new Cand { Foot = foot, Front = front, Room = room, Tier = tier };
            return true;
        }

        // Side walls (west/east) as the last resort.
        private static bool TrySide(Vector2 p, Vector2 dir, PlainShipRoom room, int mask, int fullMask, List<Vector2> avoid, List<Vector2> doors, out Cand c) {
            c = default;
            if (!FirstHit(p, dir, 6f, mask, out var hit) || !IsWall(hit.collider) || Mathf.Abs(hit.normal.x) < 0.8f) return false;
            float wx = hit.point.x;
            var foot = new Vector2(wx - dir.x * (Width * 0.5f + 0.08f), p.y);
            foreach (float dy in new[] { -0.3f, 0.3f }) {
                var from = new Vector2(foot.x, foot.y + dy);
                if (!FirstHit(from, dir, 1.2f, mask, out var h2) || !IsWall(h2.collider) || Mathf.Abs(h2.point.x - wx) > 0.08f) return false;
            }
            if (TrickOrTreat.Blocked(foot, 0.25f, fullMask) || TrickOrTreat.Blocked(foot + new Vector2(0f, 0.45f), 0.2f, fullMask)
                || TrickOrTreat.Blocked(foot - dir * 1.0f, 0.32f, fullMask)) return false;
            var front = foot - dir * 0.5f + new Vector2(0f, -0.15f);
            if (!TrickOrTreat.Clear(p, front, mask)) return false;
            if (Near(avoid, foot, 1.3f) || Near(doors, foot, 1.6f) || Near(farAvoid, foot, 2.4f) || Near(farAvoid, front, 2.2f)) return false;
            c = new Cand { Foot = foot, Front = front, Room = room, Tier = 2 };
            return true;
        }

        private static List<Cand> Place(int n) {
            var ship = ShipStatus.Instance;
            var picked = new List<Cand>();
            if (ship == null || n <= 0) return picked;
            if (TrickOrTreat.reachShip != ship.Pointer || TrickOrTreat.reachable.Count == 0) TrickOrTreat.BuildReachable(ship);
            int mask = Constants.ShipAndObjectsMask, fullMask = Constants.ShipAndAllObjectsMask;
            farAvoid = new List<Vector2>();
            var avoid = Avoid(ship, farAvoid);
            var doors = Doors(ship);
            var props = PropBounds();
            rejWall = rejFlush = rejFree = rejNear = rejProp = 0;
            rejHits.Clear();
            var cands = new List<Cand>();
            foreach (var (p, room) in TrickOrTreat.reachable) {
                if (TryNorth(p, room, mask, fullMask, avoid, doors, props, out var c)) cands.Add(c);
                else if (TrySide(p, rnd.Next(2) == 0 ? Vector2.left : Vector2.right, room, mask, fullMask, avoid, doors, out var s)) cands.Add(s);
            }
            bool Spread(Vector2 p, float min) {
                foreach (var q in picked) {
                    var d = q.Foot - p;
                    // side by side along one wall needs the cabinet width plus a gap; elsewhere the full spacing
                    if (Mathf.Abs(d.y) < 0.5f ? Mathf.Abs(d.x) < Mathf.Max(min, Width + 0.6f) : d.sqrMagnitude < min * min) return false;
                }
                return true;
            }
            // Round-robin over the rooms (random order, hallways last), one cabinet per room and round, so every
            // room gets one before any room gets a second (test 20.10., villa: north walls alone covered 6 of 19
            // rooms). Inside a room the best spot first: a clean north wall, then a side wall, then a north wall in
            // front of a furniture picture. Spacing 2.6, then 1.5 if the cabinets run short.
            int Rank(Cand c) => c.Tier == 0 ? 0 : c.Tier == 2 ? 1 : 2;
            var byRoom = cands.GroupBy(c => c.Room != null ? c.Room.Pointer : IntPtr.Zero)    // native room: wrappers differ
                .Select(g => (hall: g.First().Room != null && g.First().Room.RoomId == SystemTypes.Hallway,
                              list: g.OrderBy(c => Rank(c)).ThenBy(_ => rnd.Next()).ToList()))
                .OrderBy(g => g.hall ? 1 : 0).ThenBy(_ => rnd.Next()).ToList();
            var passLog = new List<string>();
            foreach (float min in new[] { 2.6f, 1.5f }) {
                for (int round = 0; round < 40 && picked.Count < n; round++) {
                    bool any = false;
                    foreach (var g in byRoom) {
                        if (picked.Count >= n) break;
                        for (int i = 0; i < g.list.Count; i++) {
                            if (!Spread(g.list[i].Foot, min)) continue;
                            picked.Add(g.list[i]);
                            g.list.RemoveAt(i);
                            any = true;
                            break;
                        }
                    }
                    if (!any) break;
                }
                passLog.Add($"{min:F1}: {byRoom.Count} rooms -> {picked.Count}");
            }
            var rooms = picked.Where(c => c.Room != null).Select(c => c.Room.Pointer).Distinct().Count();
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} cabinets: {picked.Count}/{n} placed in {rooms} rooms from {cands.Count} wall spots "
                + $"(tier {picked.Count(c => c.Tier == 0)}/{picked.Count(c => c.Tier == 1)}/{picked.Count(c => c.Tier == 2)}; rejected: no wall {rejWall}, "
                + $"not flush {rejFlush}, not free {rejFree}, near console/vent/door {rejNear}, over furniture {rejProp}; first hits {string.Join(",", rejHits.Select(kv => kv.Key + "=" + kv.Value))}; "
                + $"passes {string.Join(" | ", passLog)}; spots per room {string.Join(",", cands.GroupBy(c => c.Room != null ? c.Room.RoomId.ToString() : "?").Select(g => g.Key + "=" + g.Count()))})");
            return picked;
        }

        /// <summary>Host, every spawn on an own map: the cabinets of the round (placed and sent once).</summary>
        internal static void HostEnsure(int n) {
            var ship = ShipStatus.Instance;
            if (ship == null) return;
            if (cabinets.Count > 0 && placedFor == ship.Pointer) return;
            var picked = Place(Mathf.Min(n, 200));
            var list = new List<Cabinet>();
            for (int i = 0; i < picked.Count; i++)
                list.Add(new Cabinet { Index = (byte)i, Pos = R(picked[i].Foot), Front = picked[i].Front, Room = picked[i].Room != null ? picked[i].Room.RoomId.ToString() : "?" });
            TrickOrTreat.Send(TrickOrTreat.SubCabinets, w => {
                w.Write((byte)list.Count);
                foreach (var c in list) { w.Write((short)Mathf.RoundToInt(c.Pos.x * 100f)); w.Write((short)Mathf.RoundToInt(c.Pos.y * 100f)); }
            });
            Apply(list);
        }

        private static Vector2 R(Vector2 p) => new Vector2(Mathf.Round(p.x * 100f) / 100f, Mathf.Round(p.y * 100f) / 100f);

        /// <summary>Host: positions for want candies, each in its own random cabinet.</summary>
        internal static List<Vector2> HostFill(int want) =>
            cabinets.OrderBy(_ => rnd.Next()).Take(want).Select(c => c.Pos).ToList();

        private static void Apply(List<Cabinet> list) {
            DestroyObjects();
            cabinets.Clear();
            cabinets.AddRange(list);
            placedFor = ShipStatus.Instance != null ? ShipStatus.Instance.Pointer : IntPtr.Zero;
            Rebuild();
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} cabinets of the round ({Style() ?? "?"}): {list.Count} " + string.Join(" ", list.Select(c => FormattableString.Invariant($"[{c.Index} {c.Pos.x:F1},{c.Pos.y:F1}{(c.Room != "" ? " " + c.Room : "")}]"))));
        }

        /// <summary>Every client, after Sub 0: close all cabinets, the candies at a cabinet's spot move in.</summary>
        internal static void OnSpawn() {
            CancelSearch();
            foreach (var c in cabinets) { c.Open = false; c.Pending = false; }
            int inside = 0;
            foreach (var k in TrickOrTreat.candies) {
                k.Cab = None;
                if (cabinets.Count == 0) continue;
                foreach (var c in cabinets)
                    if ((c.Pos - k.Pos).sqrMagnitude < 0.0004f) { k.Cab = c.Index; inside++; break; }
            }
            RefreshSprites();
            if (cabinets.Count > 0)
                HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} part {TrickOrTreat.phase}: {inside} of {TrickOrTreat.candies.Count} candies in {cabinets.Count} cabinets: "
                    + string.Join(" ", TrickOrTreat.candies.Where(k => k.Cab != None).Select(k => $"{k.Cab}={TrickOrTreat.KindNames[k.Kind]}")));
        }

        // ================================================================ network
        internal static void HandleRpc(byte sub, MessageReader r) {
            switch (sub) {
                case TrickOrTreat.SubCabinets: {
                    int n = r.ReadByte();
                    var list = new List<Cabinet>();
                    for (int i = 0; i < n; i++) {
                        float x = r.ReadInt16() / 100f, y = r.ReadInt16() / 100f;
                        list.Add(new Cabinet { Index = (byte)i, Pos = new Vector2(x, y) });
                    }
                    if (UCRpc.RequireHost("Treats.Cabinets")) Apply(list);
                    break;
                }
                case TrickOrTreat.SubSearchReq: {
                    byte ph = r.ReadByte(), idx = r.ReadByte();
                    if (TrickOrTreat.AmHost()) HostSearch(UCRpc.Sender, ph, idx);
                    break;
                }
                case TrickOrTreat.SubSearched: {
                    byte ph = r.ReadByte(), idx = r.ReadByte(), pid = r.ReadByte(), ci = r.ReadByte();
                    if (UCRpc.RequireHost("Treats.Searched")) ApplySearched(ph, idx, pid, ci);
                    break;
                }
            }
        }

        private static void RequestSearch(Cabinet c) {
            var lp = PlayerControl.LocalPlayer;
            if (c == null || c.Open || c.Pending || !TrickOrTreat.IsAlive(lp)) return;
            if (TrickOrTreat.AmHost()) { HostSearch(lp, TrickOrTreat.phase, c.Index); return; }
            c.Pending = true;
            c.PendingAt = Time.time;
            byte ph = TrickOrTreat.phase, idx = c.Index;
            TrickOrTreat.Send(TrickOrTreat.SubSearchReq, w => { w.Write(ph); w.Write(idx); });
        }

        /// <summary>Host: check the searcher, open the cabinet for everybody, a candy inside goes the HostEat way.</summary>
        internal static void HostSearch(PlayerControl p, byte ph, byte idx) {
            try {
                if (!TrickOrTreat.AmHost() || p == null || !TrickOrTreat.IsAlive(p) || TrickOrTreat.InMeeting()) return;
                if (ph != TrickOrTreat.phase) return;
                var cab = cabinets.FirstOrDefault(c => c.Index == idx);
                if (cab == null || cab.Open) return;                                      // nobody empties a cabinet twice
                float d = Vector2.Distance(p.GetTruePosition(), cab.Pos);
                if (d > SearchRange() + 0.9f) {                                           // latency slack like HostEat
                    HalloweenPlugin.Logger?.LogInfo(FormattableString.Invariant($"{LogPrefix} search of cabinet {idx} by {p.Data?.PlayerName} refused: {d:F2} away"));
                    return;
                }
                var candy = TrickOrTreat.candies.FirstOrDefault(k => k.Cab == idx && !k.Eaten);
                byte ci = candy != null ? candy.Index : None;
                byte pid = p.PlayerId;
                TrickOrTreat.Send(TrickOrTreat.SubSearched, w => { w.Write(ph); w.Write(idx); w.Write(pid); w.Write(ci); });
                ApplySearched(ph, idx, pid, ci);
                if (candy != null) TrickOrTreat.HostEat(p, ph, candy.Index, null);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} HostSearch failed: {e}"); }
        }

        private static void ApplySearched(byte ph, byte idx, byte pid, byte ci) {
            if (ph != TrickOrTreat.phase) return;
            var cab = cabinets.FirstOrDefault(c => c.Index == idx);
            if (cab == null) return;
            cab.Open = true;
            cab.Pending = false;
            cab.GlowUntil = Time.time + 1.2f;
            if (searching == cab) CancelSearch();
            RefreshSprite(cab);
            var p = Helpers.playerById(pid);
            bool local = PlayerControl.LocalPlayer != null && PlayerControl.LocalPlayer.PlayerId == pid;
            if (local && ci == None) TreatFx.ShowHint(TrickOrTreat.De() ? "Leer." : "Empty.");
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {p?.Data?.PlayerName ?? pid.ToString()} searched cabinet {idx}: {(ci == None ? "empty" : "candy " + ci)}.");
        }

        // ================================================================ searching (local player)
        private enum Source { Key, Mouse, Click, Diag }
        private static Cabinet searching;
        private static Source source;
        private static float searchStart, mouseDownAt = -100f;
        private static Vector2 searchFrom;
        internal static bool DiagHold;
        internal static string LastCancel = "";

        internal static bool Searching => searching != null;
        internal static float Progress => searching == null ? 0f : Mathf.Clamp01((Time.time - searchStart) / SearchSeconds);
        internal static Cabinet SearchingCabinet => searching;

        /// <summary>The closed cabinet the local player could search right now (or the one being searched).</summary>
        internal static Cabinet Target(PlayerControl lp) {
            if (cabinets.Count == 0 || lp == null) return null;
            var me = lp.GetTruePosition();
            float range = SearchRange();
            if (searching != null && !searching.Open && Vector2.Distance(me, searching.Pos) <= range) return searching;
            Cabinet best = null;
            float bd = range;
            foreach (var c in cabinets) {
                if (c.Open || c.Pending) continue;
                float d = Vector2.Distance(me, c.Pos);
                if (d <= bd) { bd = d; best = c; }
            }
            return best;
        }

        private static bool OverButton(ActionButton ub) {
            try {
                var cam = TreatFx.UiCam();
                if (cam == null || ub == null) return false;
                var wp = (Vector2)cam.ScreenToWorldPoint(Input.mousePosition);
                foreach (var col in ub.GetComponentsInChildren<Collider2D>()) if (col != null && col.OverlapPoint(wp)) return true;
            } catch { }
            return false;
        }

        private static void Start(Cabinet c, Source s) {
            var lp = PlayerControl.LocalPlayer;
            if (c == null || c.Open || c.Pending || lp == null) return;
            searching = c;
            source = s;
            searchStart = Time.time;
            searchFrom = lp.GetTruePosition();
            LastCancel = "";
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} searching cabinet {c.Index} ({s}).");
        }

        internal static void CancelSearch(string why = null) {
            if (searching != null && why != null) {
                LastCancel = why;
                HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} search of cabinet {searching.Index} broken off: {why}.");
            }
            searching = null;
            ShowBar(false);
        }

        /// <summary>From TreatUse.Tick every frame in the round: press, hold, break-offs, the glow and the bar.</summary>
        internal static void TickSearch(PlayerControl lp, ActionButton ub, Cabinet target) {
            if (cabinets.Count == 0) return;
            float now = Time.time;
            foreach (var c in cabinets) if (c.Pending && now - c.PendingAt > 3f) c.Pending = false;   // the host said nothing
            if (searching != null) {
                bool held = source switch {
                    Source.Key => Input.GetKey(KeyCode.E),
                    Source.Mouse => Input.GetMouseButton(0),
                    Source.Diag => DiagHold,
                    _ => true,
                };
                string why = null;
                if (!TrickOrTreat.IsAlive(lp)) why = "death";
                else if (TrickOrTreat.InMeeting()) why = "meeting";
                else if (searching.Open) why = "opened by someone else";
                else if (Vector2.Distance(lp.GetTruePosition(), searchFrom) > 0.1f) why = "moved";
                else if (target != searching) why = "out of reach" + VanillaTarget(ub);
                else if (!held) why = "released";
                if (why != null) CancelSearch(why);
                else if (now - searchStart >= SearchSeconds) {
                    var c = searching;
                    CancelSearch();
                    RequestSearch(c);
                }
            }
            if (searching == null && target != null && ub != null) {
                if (Input.GetKeyDown(KeyCode.E) && TreatUse.KeyboardFree()) Start(target, Source.Key);
                else if (Input.GetMouseButtonDown(0) && OverButton(ub)) { mouseDownAt = now; Start(target, Source.Mouse); }
            }
            foreach (var c in cabinets) {
                if (c.GlowSr == null) continue;
                // the glow lies over the cabinet while it is being searched (growing with the progress) and fades
                // over the open cabinet afterwards
                float a = 0f;
                if (c == searching) a = (0.35f + 0.65f * Progress) * (0.85f + 0.15f * Mathf.Sin(now * 9f));
                else if (now < c.GlowUntil) a = Mathf.Clamp01((c.GlowUntil - now) / 1.2f);
                c.GlowSr.enabled = a > 0.01f;
                if (a > 0.01f) c.GlowSr.color = new Color(1f, 1f, 1f, a);
            }
            TickBar();
        }

        /// <summary>The Use button's click listener (mouse up, controller): a press seen by TickSearch wins.</summary>
        internal static void OnClick(Cabinet c) {
            if (searching != null) return;
            if (Input.GetMouseButton(0)) { mouseDownAt = Time.time; Start(c, Source.Mouse); return; }
            if (Time.time - mouseDownAt < 10f) return;      // the release of a hold that already ran or broke off
            Start(c, Source.Click);
        }

        internal static void DiagStart(Cabinet c) => Start(c, Source.Diag);

        private static string VanillaTarget(ActionButton _) {
            try {
                var ub = HudManager.InstanceExists ? HudManager.Instance.UseButton : null;
                if (ub == null || ub.currentTarget == null) return "";
                var mb = ub.currentTarget.TryCast<MonoBehaviour>();
                return " (Use button busy: " + (mb != null ? mb.name + " " + mb.GetIl2CppType().Name : "?") + ")";
            } catch { return ""; }
        }

        // ---- progress bar over the cabinet (UI layer, above the light system's shadow) ----
        private static SpriteRenderer barBack, barFill;
        private static void ShowBar(bool on) {
            if (barBack != null) barBack.enabled = on;
            if (barFill != null) barFill.enabled = on;
        }

        private static void TickBar() {
            if (searching == null) { ShowBar(false); return; }
            if (barBack == null) {
                barBack = TreatFx.UiSr("TreatSearchBarBack", TreatFx.Pixel(), 310);
                barFill = TreatFx.UiSr("TreatSearchBarFill", TreatFx.Pixel(), 311);
                barBack.color = new Color(0.06f, 0.04f, 0.08f, 0.85f);
                barFill.color = TrickOrTreat.Orange;
            }
            if (!TreatFx.ToUi(new Vector3(searching.Pos.x, searching.Pos.y + Height + 0.18f, 0f), out var ui)) { ShowBar(false); return; }
            float u = TreatFx.UiPerWorld();
            float w = 0.78f * u, h = 0.11f * u, p = Progress;
            barBack.transform.position = new Vector3(ui.x, ui.y, -55f);
            barBack.transform.localScale = new Vector3(w + 0.04f * u, h + 0.04f * u, 1f);
            barFill.transform.position = new Vector3(ui.x - w * 0.5f + w * p * 0.5f, ui.y, -56f);
            barFill.transform.localScale = new Vector3(Mathf.Max(0.0001f, w * p), h, 1f);
            ShowBar(true);
        }

        // ================================================================ world objects
        private static GameObject root;

        private static void Rebuild() {
            DestroyObjects();
            if (cabinets.Count == 0 || ShipStatus.Instance == null) return;
            if (root == null) root = new GameObject("TrickOrTreatCabinets") { layer = 11 };
            float feet = FeetOffset();
            string style = Style() ?? "museum";
            foreach (var c in cabinets) {
                var go = new GameObject("cabinet" + c.Index) { layer = 11 };
                go.transform.SetParent(root.transform, false);
                go.transform.position = new Vector3(c.Pos.x, c.Pos.y, (c.Pos.y + feet) / 1000f);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = CabSprite(style, c.Open ? 1 : 0);
                var g = new GameObject("glow") { layer = 11 };
                g.transform.SetParent(go.transform, false);
                g.transform.localPosition = new Vector3(0f, 0f, -0.0002f);
                var gsr = g.AddComponent<SpriteRenderer>();
                gsr.sprite = CabSprite(style, 2);
                gsr.enabled = false;
                c.Go = go; c.Sr = sr; c.GlowSr = gsr;
            }
        }

        private static float FeetOffset() {
            try {
                var lp = PlayerControl.LocalPlayer;
                float f = lp.transform.position.y - lp.GetTruePosition().y;
                return f >= 0f && f <= 1f ? f : 0.36f;
            } catch { return 0.36f; }
        }

        private static void RefreshSprite(Cabinet c) {
            if (c?.Sr == null) return;
            string style = Style() ?? "museum";
            c.Sr.sprite = CabSprite(style, c.Open ? 1 : 0);
        }

        private static void RefreshSprites() { foreach (var c in cabinets) RefreshSprite(c); }

        private static void DestroyObjects() {
            foreach (var c in cabinets) {
                if (c.Go != null) UnityEngine.Object.Destroy(c.Go);
                c.Go = null; c.Sr = null; c.GlowSr = null;
            }
        }

        internal static void Clear() {
            CancelSearch();
            DestroyObjects();
            cabinets.Clear();
            placedFor = IntPtr.Zero;
            if (root != null) UnityEngine.Object.Destroy(root);
            root = null;
            DiagHold = false;
        }

        // ================================================================ pictures
        private static readonly Dictionary<string, Sprite> sprites = new();
        internal static readonly HashSet<string> fromFile = new();
        private static readonly string[] StateNames = { "closed", "open", "glow" };

        /// <summary>File name of a cabinet picture, e.g. cabinet_villa_open.png.</summary>
        internal static string FileOf(string style, int state) => $"cabinet_{style}_{StateNames[state]}.png";

        internal static Sprite CabSprite(string style, int state) {
            string file = FileOf(style, state);
            if (sprites.TryGetValue(file, out var s) && s != null) return s;
            var tex = TreatFx.LoadTreatTexture(file);
            if (tex != null) fromFile.Add(file);
            else tex = Drawn(style, state).ToTexture("treat_" + file);
            s = UnityEngine.Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, FloorPx / PicH), tex.width / Width);
            s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            sprites[file] = s;
            return s;
        }

        /// <summary>The runtime drawing (placeholder) as a canvas, also for the self test's export.</summary>
        internal static TreatFx.Canvas Drawn(string style, int state) {
            var cv = new TreatFx.Canvas((int)PicW, (int)PicH);
            if (state == 2) DrawGlow(cv);
            else DrawCabinet(cv, style, state == 1);
            return cv;
        }

        private static Sprite searchIcon;
        internal static bool SearchIconFromFile;
        internal static Sprite SearchIcon() {
            if (searchIcon != null) return searchIcon;
            var tex = TreatFx.LoadTreatTexture("cabinet_search_icon.png");
            SearchIconFromFile = tex != null;
            if (tex == null) tex = DrawnSearchIcon().ToTexture("treat_cabinet_search_icon");
            searchIcon = UnityEngine.Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width / (TreatUse.IconWidth * 1.0f));
            searchIcon.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return searchIcon;
        }

        private static Color C(float r, float g, float b, float a = 1f) => new Color(r, g, b, a);

        private sealed class Pal { public Color Body, Dark, Light, Trim, Inside, Handle; }

        private static Pal PaletteOf(string style) {
            switch (style) {
                case "museum": return new Pal { Body = C(0.50f, 0.32f, 0.18f), Dark = C(0.30f, 0.18f, 0.10f), Light = C(0.66f, 0.46f, 0.28f), Trim = C(0.80f, 0.64f, 0.30f), Inside = C(0.12f, 0.10f, 0.12f), Handle = C(0.92f, 0.78f, 0.38f) };
                case "wald": return new Pal { Body = C(0.47f, 0.33f, 0.19f), Dark = C(0.28f, 0.19f, 0.10f), Light = C(0.60f, 0.45f, 0.27f), Trim = C(0.32f, 0.45f, 0.20f), Inside = C(0.10f, 0.08f, 0.06f), Handle = C(0.35f, 0.35f, 0.36f) };
                case "park": return new Pal { Body = C(0.82f, 0.16f, 0.18f), Dark = C(0.52f, 0.08f, 0.12f), Light = C(0.98f, 0.94f, 0.88f), Trim = C(0.98f, 0.78f, 0.22f), Inside = C(0.16f, 0.06f, 0.14f), Handle = C(0.98f, 0.84f, 0.30f) };
                case "train": return new Pal { Body = C(0.38f, 0.45f, 0.52f), Dark = C(0.22f, 0.27f, 0.32f), Light = C(0.56f, 0.63f, 0.70f), Trim = C(0.66f, 0.54f, 0.30f), Inside = C(0.08f, 0.09f, 0.11f), Handle = C(0.82f, 0.84f, 0.86f) };
                case "villa": return new Pal { Body = C(0.32f, 0.13f, 0.11f), Dark = C(0.18f, 0.07f, 0.07f), Light = C(0.44f, 0.20f, 0.16f), Trim = C(0.78f, 0.60f, 0.26f), Inside = C(0.07f, 0.04f, 0.06f), Handle = C(0.90f, 0.74f, 0.34f) };
                default: return new Pal { Body = C(0.40f, 0.42f, 0.38f), Dark = C(0.24f, 0.26f, 0.24f), Light = C(0.54f, 0.56f, 0.50f), Trim = C(0.46f, 0.52f, 0.40f), Inside = C(0.06f, 0.07f, 0.06f), Handle = C(0.62f, 0.60f, 0.52f) };
            }
        }

        // 160x200, y from the bottom; body x 16-144, floor band y 0-20 (shadow and plinth), top at about y 196.
        private static void DrawCabinet(TreatFx.Canvas cv, string style, bool open) {
            var p = PaletteOf(style);
            cv.Ellipse(80f, 12f, 72f, 9f, C(0f, 0f, 0f, 0.45f));
            cv.Rect(14f, 12f, 146f, 26f, p.Dark);                           // plinth
            cv.Rect(18f, 24f, 142f, 184f, p.Body);                          // carcass
            cv.Rect(18f, 24f, 24f, 184f, p.Dark);
            cv.Rect(136f, 24f, 142f, 184f, p.Dark);
            // top: per style
            switch (style) {
                case "villa":
                    cv.Rect(10f, 180f, 150f, 190f, p.Trim);
                    cv.Ellipse(80f, 188f, 40f, 11f, p.Body);
                    cv.Ring(80f, 188f, 40f, 11f, 2.5f, p.Trim);
                    cv.Disc(80f, 196f, 3.5f, p.Trim);
                    break;
                case "park":
                    cv.Rect(10f, 180f, 150f, 192f, p.Trim);
                    for (int i = 0; i < 7; i++) cv.Tri(12f + i * 20f, 192f, 32f + i * 20f, 192f, 22f + i * 20f, 199f, i % 2 == 0 ? p.Body : p.Light);
                    break;
                case "train":
                    cv.Rect(12f, 182f, 148f, 192f, p.Dark);
                    for (int i = 0; i < 6; i++) cv.Disc(22f + i * 23f, 187f, 2.2f, p.Handle);
                    break;
                case "wald":
                    cv.Rect(10f, 180f, 150f, 192f, p.Dark);
                    cv.Ellipse(40f, 193f, 22f, 5f, p.Trim);
                    cv.Ellipse(112f, 194f, 18f, 4f, p.Trim);
                    break;
                case "graveyard":
                    cv.Rect(12f, 180f, 148f, 190f, p.Dark);
                    cv.Tri(12f, 190f, 148f, 190f, 80f, 199f, p.Dark);
                    break;
                default:
                    cv.Rect(10f, 180f, 150f, 192f, p.Trim);
                    cv.Rect(56f, 183f, 104f, 189f, p.Dark);
                    break;
            }
            float x0 = 26f, xm = 80f, x1 = 134f, y0 = 32f, y1 = 174f;
            if (open) {
                cv.Rect(x0, y0, x1, y1, p.Inside);
                for (int i = 1; i < 3; i++) cv.Rect(x0, y0 + i * 47f - 2f, x1, y0 + i * 47f + 2f, p.Dark);
                // the two doors swung open to the sides
                cv.Tri(x0, y0, x0, y1, 3f, y1 - 8f, p.Light);
                cv.Tri(x0, y0, 3f, y1 - 8f, 3f, y0 + 8f, p.Light);
                cv.Line(x0 - 2f, y0 + 2f, x0 - 2f, y1 - 2f, 2f, p.Dark);
                cv.Tri(x1, y0, x1, y1, 157f, y1 - 8f, p.Light);
                cv.Tri(x1, y0, 157f, y1 - 8f, 157f, y0 + 8f, p.Light);
                cv.Line(x1 + 2f, y0 + 2f, x1 + 2f, y1 - 2f, 2f, p.Dark);
                cv.Disc(8f, (y0 + y1) / 2f, 3f, p.Handle);
                cv.Disc(152f, (y0 + y1) / 2f, 3f, p.Handle);
                // a few cobwebs and dust inside
                cv.Line(x0, y1 - 14f, x0 + 14f, y1, 1f, C(0.8f, 0.8f, 0.85f, 0.35f));
                cv.Line(x0, y1 - 24f, x0 + 24f, y1, 1f, C(0.8f, 0.8f, 0.85f, 0.25f));
            } else {
                foreach (var (a, b) in new[] { (x0, xm - 2f), (xm + 2f, x1) }) {
                    cv.Rect(a, y0, b, y1, p.Light);
                    cv.Rect(a + 5f, y0 + 6f, b - 5f, y1 - 6f, p.Body);
                    DrawDoorDetail(cv, style, p, a + 5f, y0 + 6f, b - 5f, y1 - 6f);
                }
                cv.Rect(xm - 2f, y0, xm + 2f, y1, p.Dark);
                cv.Disc(xm - 8f, (y0 + y1) / 2f, 4f, p.Handle);
                cv.Disc(xm + 8f, (y0 + y1) / 2f, 4f, p.Handle);
                if (style == "train") { cv.Rect(xm - 14f, y1 - 26f, xm + 14f, y1 - 14f, p.Trim); }
            }
            cv.Outline(C(0.06f, 0.04f, 0.06f), 2);
        }

        private static void DrawDoorDetail(TreatFx.Canvas cv, string style, Pal p, float a, float b0, float b, float t) {
            float w = b - a, h = t - b0, cx = (a + b) / 2f;
            switch (style) {
                case "museum":      // glass panes with a reflection
                    cv.Rect(a + 3f, b0 + h * 0.45f, b - 3f, t - 3f, C(0.55f, 0.74f, 0.84f, 0.75f));
                    cv.Line(a + 8f, t - 10f, a + w * 0.6f, b0 + h * 0.55f, 2f, C(1f, 1f, 1f, 0.5f));
                    cv.Rect(a + 3f, b0 + 4f, b - 3f, b0 + h * 0.38f, p.Dark);
                    break;
                case "wald":        // planks and an iron band
                    for (int i = 1; i < 5; i++) cv.Line(a, b0 + h * i / 5f, b, b0 + h * i / 5f, 1.5f, p.Dark);
                    cv.Rect(a, b0 + h * 0.7f, b, b0 + h * 0.7f + 5f, p.Handle);
                    break;
                case "park":        // stripes and a star
                    for (int i = 0; i < 4; i++) cv.Rect(a + i * w / 4f, b0, a + i * w / 4f + w / 8f, t, p.Light);
                    cv.Disc(cx, t - 16f, 7f, p.Trim);
                    break;
                case "train":       // slats and rivets
                    for (int i = 0; i < 6; i++) cv.Rect(a + 4f, t - 16f - i * 7f, b - 4f, t - 13f - i * 7f, p.Dark);
                    cv.Disc(a + 4f, b0 + 4f, 1.8f, p.Handle); cv.Disc(b - 4f, b0 + 4f, 1.8f, p.Handle);
                    break;
                case "villa":       // carved arch panel
                    cv.Rect(a + 5f, b0 + 6f, b - 5f, t - 18f, p.Dark);
                    cv.Ellipse(cx, t - 18f, w / 2f - 5f, 10f, p.Dark);
                    cv.Rect(a + 8f, b0 + 9f, b - 8f, t - 20f, p.Light);
                    cv.Ellipse(cx, t - 20f, w / 2f - 8f, 8f, p.Light);
                    break;
                default:            // graveyard: a cross and a crack
                    cv.Rect(cx - 2.5f, b0 + h * 0.35f, cx + 2.5f, t - 10f, p.Dark);
                    cv.Rect(cx - 10f, t - 30f, cx + 10f, t - 25f, p.Dark);
                    cv.Line(a + 4f, b0 + 10f, a + 14f, b0 + 30f, 1.2f, C(0.1f, 0.1f, 0.1f, 0.7f));
                    break;
            }
        }

        // the highlight around the carcass when the cabinet is the Use target
        private static void DrawGlow(TreatFx.Canvas cv) {
            var sil = new TreatFx.Canvas((int)PicW, (int)PicH);
            sil.Rect(14f, 12f, 146f, 192f, Color.white);
            var rim = new TreatFx.Canvas((int)PicW, (int)PicH);
            Array.Copy(sil.Px, rim.Px, sil.Px.Length);
            rim.Outline(C(1f, 0.72f, 0.25f, 1f), 6);
            for (int i = 0; i < rim.Px.Length; i++) {
                if (sil.Px[i].a > 0.01f) { rim.Px[i] = C(1f, 0.72f, 0.25f, 0f); continue; }
                var q = rim.Px[i];
                cv.Px[i] = new Color(q.r, q.g, q.b, q.a * 0.9f);
            }
        }

        // magnifying glass over a small cabinet, 128x128
        internal static TreatFx.Canvas DrawnSearchIcon() {
            var cv = new TreatFx.Canvas(128, 128);
            var p = PaletteOf("villa");
            cv.Rect(18f, 14f, 78f, 104f, p.Body);
            cv.Rect(22f, 20f, 47f, 98f, p.Light);
            cv.Rect(49f, 20f, 74f, 98f, p.Light);
            cv.Disc(44f, 58f, 3f, p.Handle);
            cv.Disc(52f, 58f, 3f, p.Handle);
            cv.Line(86f, 46f, 114f, 16f, 11f, C(0.30f, 0.20f, 0.12f));
            cv.Disc(78f, 60f, 26f, C(0.70f, 0.86f, 0.95f, 0.55f));
            cv.Ring(78f, 60f, 26f, 26f, 7f, C(0.92f, 0.92f, 0.95f));
            cv.Line(66f, 74f, 74f, 80f, 3f, C(1f, 1f, 1f, 0.8f));
            cv.Outline(C(0.06f, 0.04f, 0.06f), 3);
            return cv;
        }
    }
}
