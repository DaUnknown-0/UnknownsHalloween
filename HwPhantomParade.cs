// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * Phantom Parade (impostor sabotage, idea C2, 2026-10-20)
 *
 * For a while (30 s by default) half as many phantoms as there are living players walk over the map. They look like
 * living players (colour, name, hat, visor, skin as the player shows them right now) and walk real paths, but they do
 * no tasks. A living player who touches a phantom makes it fall apart into mist. Phantoms are not on the admin table
 * (they are no players), have no reflection in the Haunted Mirrors (HwMirrors only looks at PlayerControls) and the
 * Banshee's scream only marks the real ones (BansheeReveal iterates PlayerControls, so Banshee.cs needed no change).
 *
 *  - No network objects and no behaviour of their own: every client builds the same walking graph from the map
 *    geometry (seeded samples per room plus the vents, edges = free circle casts, doors ignored; the same idea as
 *    TrickOrTreat.BuildReachable, but without random or player-dependent input so all clients get the same graph)
 *    and the same timelines from the host's seed: random target node, shortest path, a pause "at a task", repeat.
 *  - Host-authoritative: an impostor asks (map button, Sub 3), the host checks option, uses, cooldown and meeting and
 *    sends the start (Sub 4: seed, speed, seconds, the copied players). Touches go to the host (Sub 5); it checks the
 *    distance against its own copy of the timeline and tells everybody (Sub 6). A meeting ends the parade everywhere.
 *  - Map button: a clone of a sabotage button on the sabotage map (like Atlas' crisis buttons), grey while waiting.
 *  - Impostors see the phantoms a little transparent (they know it is their illusion).
 *
 * Options 2070-2073, RPC module 241 Sub 3-7. Pictures: Resources/hw2026/phantom/icon_phantom_parade.png (256, map
 * button) and phantom_mist_1..8.png (128, the decay). Self test: UC_HALLOWEEN_DIAG=phantom (HwMechanicsDiag.cs).
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using PowerTools;
using UnityEngine;
using TheOtherRoles;
using UnknownsCollection;
using Types = TheOtherRoles.CustomOption.CustomOptionType;

namespace UnknownsHalloween {
    internal static class HwPhantomParade {
        private const string Folder = "phantom";
        internal static readonly Color Color = new Color(0.72f, 0.62f, 1.0f);

        // ---- options (2070-2073) ----
        public static CustomOption On, Duration, Cooldown, Uses;
        private static readonly string[] DurationLabels = { "20s", "25s", "30s", "40s" };
        private static readonly float[] DurationSeconds = { 20f, 25f, 30f, 40f };
        private static readonly string[] CooldownLabels = { "30s", "45s", "60s", "90s", "120s", "180s" };
        private static readonly float[] CooldownSeconds = { 30f, 45f, 60f, 90f, 120f, 180f };
        private static readonly string[] UsesLabels = { "1", "2", "3", "Unlimited" };

        internal static void CreateOptions() {
            try {
                var t = Types.Impostor;
                On = CustomOption.Create(2070, t, "Phantom Parade", false, null, true, null, "Phantom Parade");
                Duration = CustomOption.Create(2071, t, "Phantom Parade Duration", DurationLabels, On);
                Cooldown = CustomOption.Create(2072, t, "Phantom Parade Cooldown", CooldownLabels, On);
                Uses = CustomOption.Create(2073, t, "Phantom Parade Uses Per Game", UsesLabels, On);
                try { Duration.selection = 2; Cooldown.selection = 2; Uses.selection = 0; } catch { }   // 30 s, 60 s, once
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Phantoms] options failed: {e}"); }
        }

        internal static bool DiagForce;
        internal static bool Enabled() { if (DiagForce) return true; try { return On != null && On.getBool(); } catch { return false; } }
        private static float DurationFor() => DurationSeconds[Mathf.Clamp(Duration?.getSelection() ?? 2, 0, DurationSeconds.Length - 1)];
        private static float CooldownFor() => CooldownSeconds[Mathf.Clamp(Cooldown?.getSelection() ?? 2, 0, CooldownSeconds.Length - 1)];
        private static int UsesFor() { int s = Uses?.getSelection() ?? 0; return s >= 3 ? int.MaxValue : s + 1; }

        // ---- state (the same on every client) ----
        internal static bool running;
        private static float startedAt, seconds, speed;
        private static int usesDone;
        private static float readyAt;                    // cooldown end (round time), host and impostor clients alike
        private static readonly System.Random rnd = new System.Random();

        internal sealed class Leg { public float T0, T1; public Vector2 A, B; public bool Walk; }
        internal sealed class Phantom {
            public byte Index, Copy;
            public readonly List<Leg> Legs = new();
            public bool Gone, Asked;
            public GameObject Go;
            public PoolablePlayer Pp;
            public SpriteRenderer[] Srs;
            public TMPro.TextMeshPro Name;
            public SpriteAnim BodyAnim, SkinAnim;
            public AnimationClip SkinIdle, SkinRun;
            public bool AnimRun, AnimSet;
            public Vector3 Offset;                     // root - feet
            public float FeetZ;
            public Vector2 Pos;
            public bool Moving, FaceLeft;
        }
        internal static readonly List<Phantom> phantoms = new();
        internal static int DiagDissolved;

        // ================================================================ RPC
        internal static void HandleRpc(byte sub, Hazel.MessageReader r) {
            switch (sub) {
                case HwMechanics.SubPhantomRequest:
                    if (HwMechanics.AmHost()) HostRequest(UCRpc.Sender);
                    break;
                case HwMechanics.SubPhantomStart: {
                    int seed = r.ReadInt32();
                    float spd = r.ReadSingle(), secs = r.ReadSingle();
                    int n = r.ReadByte();
                    var ids = new List<byte>();
                    for (int i = 0; i < n; i++) ids.Add(r.ReadByte());
                    if (UCRpc.RequireHost("Phantom.Start")) ApplyStart(seed, spd, secs, ids);
                    break;
                }
                case HwMechanics.SubPhantomTouch: {
                    byte idx = r.ReadByte();
                    if (HwMechanics.AmHost()) HostTouch(UCRpc.Sender, idx);
                    break;
                }
                case HwMechanics.SubPhantomDissolve: {
                    byte idx = r.ReadByte();
                    if (UCRpc.RequireHost("Phantom.Dissolve")) ApplyDissolve(idx);
                    break;
                }
                case HwMechanics.SubPhantomEnd:
                    if (UCRpc.RequireHost("Phantom.End")) ApplyEnd("host");
                    break;
            }
        }

        /// <summary>The map button: the impostor asks the host.</summary>
        internal static void Request() {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null) return;
            if (HwMechanics.AmHost()) HostRequest(lp);
            else HwMechanics.Send(HwMechanics.SubPhantomRequest, null);
        }

        internal static string LastRefusal = "";
        private static bool Refuse(string why) { LastRefusal = why; HwMechanics.Log($"phantoms: request refused ({why})."); return false; }

        internal static bool HostRequest(PlayerControl from) {
            if (!Enabled()) return Refuse("off");
            if (from == null || (!HwMechanics.IsImp(from) && !DiagForce)) return Refuse("not an impostor");
            if (!HwMechanics.InRound() || HwMechanics.InMeeting()) return Refuse("no round / meeting");
            if (running) return Refuse("already running");
            if (usesDone >= UsesFor()) return Refuse("no uses left");
            if (Time.time < readyAt) return Refuse($"cooldown {readyAt - Time.time:F0} s");
            var alive = PlayerControl.AllPlayerControls.ToArray().Where(HwMechanics.IsAlive).ToList();
            if (alive.Count == 0) return Refuse("nobody alive");
            int n = Mathf.Clamp(alive.Count / 2, 1, 15);
            var ids = alive.OrderBy(_ => rnd.Next()).Take(n).Select(p => p.PlayerId).ToList();
            int seed = rnd.Next(1, int.MaxValue);
            float spd = 2.5f;
            try {
                var lp = PlayerControl.LocalPlayer;
                float mod = GameOptionsManager.Instance.CurrentGameOptions.GetFloat(AmongUs.GameOptions.FloatOptionNames.PlayerSpeedMod);
                spd = lp.MyPhysics.Speed * Mathf.Clamp(mod, 0.5f, 3f);
            } catch { }
            float secs = DurationFor();
            HwMechanics.Send(HwMechanics.SubPhantomStart, w => {
                w.Write(seed); w.Write(spd); w.Write(secs);
                w.Write((byte)ids.Count);
                foreach (var id in ids) w.Write(id);
            });
            ApplyStart(seed, spd, secs, ids);
            LastRefusal = "";
            return true;
        }

        private static void HostTouch(PlayerControl from, byte idx) {
            if (!running || from == null || !HwMechanics.IsAlive(from)) return;
            var ph = phantoms.FirstOrDefault(p => p.Index == idx);
            if (ph == null || ph.Gone) return;
            var pos = Evaluate(ph, Time.time - startedAt, out _, out _);
            float d = (from.GetTruePosition() - pos).magnitude;
            if (d > 1.8f) { HwMechanics.Log($"phantoms: touch of {idx} by {from.PlayerId} refused ({d:F1} u)."); return; }
            HwMechanics.Send(HwMechanics.SubPhantomDissolve, w => w.Write(idx));
            ApplyDissolve(idx);
        }

        // ================================================================ start / end
        private static void ApplyStart(int seed, float spd, float secs, List<byte> ids) {
            ApplyEnd("restart");
            var ship = ShipStatus.Instance;
            if (ship == null) return;
            PhantomGraph.Ensure(ship);
            if (PhantomGraph.Main.Count < 2) { HwMechanics.Warn("phantoms: no walking graph on this map."); return; }
            running = true;
            startedAt = Time.time;
            seconds = Mathf.Clamp(secs, 5f, 90f);
            speed = Mathf.Clamp(spd, 0.8f, 8f);
            usesDone++;
            readyAt = startedAt + seconds + CooldownFor();
            for (int i = 0; i < ids.Count; i++) {
                var ph = new Phantom { Index = (byte)i, Copy = ids[i] };
                BuildTimeline(ph, seed, i);
                phantoms.Add(ph);
                try { Spawn(ph); } catch (Exception e) { HwMechanics.Warn($"phantoms: spawn {i} failed: {e.Message}"); }
            }
            PlayWhoosh();
            HwMechanics.Log($"phantoms: parade of {phantoms.Count} for {seconds:F0} s (seed {seed}, speed {speed:F2}, graph {PhantomGraph.Main.Count} nodes); copies "
                + string.Join(",", ids));
        }

        private static void ApplyEnd(string why) {
            bool was = running;
            running = false;
            foreach (var ph in phantoms) DestroyVisual(ph);
            phantoms.Clear();
            if (was) HwMechanics.Log($"phantoms: parade over ({why}).");
        }

        private static void ApplyDissolve(byte idx) {
            var ph = phantoms.FirstOrDefault(p => p.Index == idx);
            if (ph == null || ph.Gone) return;
            ph.Gone = true;
            DiagDissolved++;
            Mist.Spawn(ph.Go != null ? ph.Go.transform.position : (Vector3)ph.Pos, ph.FeetZ);
            DestroyVisual(ph);
            HwMechanics.Log($"phantoms: {idx} fell apart into mist.");
        }

        internal static void OnMeeting() {
            ApplyEnd("meeting");
            readyAt = Mathf.Max(readyAt, Time.time + 10f);
        }

        internal static void Reset() {
            ApplyEnd("reset");
            usesDone = 0;
            readyAt = Time.time + 15f;           // a short wait at the start of the round, like the vanilla sabotages
            Mist.Clear();
            mapButton = null;
        }

        /// <summary>Seconds until the map button works again (0 = ready, -1 = no uses left).</summary>
        internal static float Wait() {
            if (usesDone >= UsesFor()) return -1f;
            if (running) return seconds - (Time.time - startedAt) + CooldownFor();
            return Mathf.Max(0f, readyAt - Time.time);
        }

        // ================================================================ timelines
        private static void BuildTimeline(Phantom ph, int seed, int i) {
            var g = PhantomGraph.Main;
            var rng = new System.Random(unchecked(seed * 31 + i * 7919 + 17));
            int cur = g[rng.Next(g.Count)];
            float t = (float)rng.NextDouble() * 1.2f;
            ph.Legs.Add(new Leg { T0 = 0f, T1 = t, A = PhantomGraph.Nodes[cur], B = PhantomGraph.Nodes[cur], Walk = false });
            for (int leg = 0; leg < 16 && t < seconds + 1f; leg++) {
                int target = cur;
                for (int k = 0; k < 6; k++) {
                    target = g[rng.Next(g.Count)];
                    if ((PhantomGraph.Nodes[target] - PhantomGraph.Nodes[cur]).magnitude > 6f) break;
                }
                var path = PhantomGraph.Path(cur, target);
                if (path == null || path.Count < 2) { cur = target; continue; }
                for (int k = 1; k < path.Count; k++) {
                    var a = PhantomGraph.Nodes[path[k - 1]];
                    var b = PhantomGraph.Nodes[path[k]];
                    float dt = (b - a).magnitude / speed;
                    ph.Legs.Add(new Leg { T0 = t, T1 = t + dt, A = a, B = b, Walk = true });
                    t += dt;
                }
                cur = target;
                float pause = 0.8f + (float)rng.NextDouble() * 2.6f;     // "at a task"
                var p = PhantomGraph.Nodes[cur];
                ph.Legs.Add(new Leg { T0 = t, T1 = t + pause, A = p, B = p, Walk = false });
                t += pause;
            }
        }

        internal static Vector2 Evaluate(Phantom ph, float t, out bool moving, out float dx) {
            moving = false; dx = 0f;
            if (ph.Legs.Count == 0) return Vector2.zero;
            foreach (var l in ph.Legs) {
                if (t > l.T1) continue;
                float k = l.T1 > l.T0 ? Mathf.Clamp01((t - l.T0) / (l.T1 - l.T0)) : 1f;
                moving = l.Walk;
                dx = l.B.x - l.A.x;
                return Vector2.Lerp(l.A, l.B, k);
            }
            return ph.Legs[ph.Legs.Count - 1].B;
        }

        // ================================================================ visuals
        private static PoolablePlayer Prefab() {
            try {
                var hud = HudManager.InstanceExists ? HudManager.Instance : null;
                if (hud != null && hud.IntroPrefab != null && hud.IntroPrefab.PlayerPrefab != null) return hud.IntroPrefab.PlayerPrefab;
            } catch { }
            try { return AccessTools.Field(AccessTools.TypeByName("TheOtherRoles.Patches.IntroCutsceneOnDestroyPatch"), "playerPrefab")?.GetValue(null) as PoolablePlayer; } catch { }
            return null;
        }

        private static void SetLayer(GameObject go, int layer) {
            go.layer = layer;
            foreach (var t in go.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = layer;
        }

        private static void Spawn(Phantom ph) {
            var src = Helpers.playerById(ph.Copy);
            var prefab = Prefab();
            if (src == null || prefab == null) { HwMechanics.Warn($"phantoms: no {(src == null ? "player" : "prefab")} for {ph.Index}."); return; }
            var pp = UnityEngine.Object.Instantiate(prefab);
            pp.name = "Phantom" + ph.Index;
            UnityEngine.Object.DontDestroyOnLoad(pp.gameObject);
            ph.Pp = pp;
            ph.Go = pp.gameObject;
            // the look the copied player shows right now (a morph, the camouflage or a Masquerade costume included)
            var cos = src.cosmetics;
            var outfit = new NetworkedPlayerInfo.PlayerOutfit();
            try {
                var def = src.Data.DefaultOutfit;
                outfit.ColorId = cos != null ? cos.ColorId : def.ColorId;
                outfit.HatId = cos?.hat?.Hat != null ? cos.hat.Hat.ProductId : def.HatId;
                outfit.VisorId = cos?.visor?.visorData != null ? cos.visor.visorData.ProductId : def.VisorId;
                outfit.SkinId = cos?.skin?.data != null ? cos.skin.data.ProductId : def.SkinId;
                outfit.PetId = "pet_EmptyPet";
                outfit.PlayerName = cos?.nameText != null ? cos.nameText.text : def.PlayerName;
            } catch (Exception e) { HwMechanics.Warn($"phantoms: look of {ph.Copy}: {e.Message}"); }
            try { pp.UpdateFromPlayerOutfit(outfit, PlayerMaterial.MaskType.None, false, false); } catch (Exception e) { HwMechanics.Warn($"phantoms: outfit: {e.Message}"); }
            try {
                pp.ToggleName(true);
                pp.SetName(outfit.PlayerName ?? "");
                if (cos?.nameText != null) pp.SetNameColor(cos.nameText.color);
            } catch { }
            SetLayer(pp.gameObject, 11);
            try { pp.transform.localScale = src.transform.localScale; } catch { pp.transform.localScale = new Vector3(0.7f, 0.7f, 1f); }
            // offset root - feet, measured on the copied player: body over feet the same as his
            ph.Offset = new Vector3(0f, 0.36f, 0f);
            try {
                var srcBody = cos.currentBodySprite.BodySprite.transform.position;
                var srcFeet = (Vector3)src.GetTruePosition();
                pp.transform.position = Vector3.zero;
                var ppBody = pp.cosmetics.currentBodySprite.BodySprite.transform.position;
                ph.Offset = (srcBody - srcFeet) - (ppBody - pp.transform.position);
                ph.Offset.z = 0f;
            } catch { }
            ph.FeetZ = HwMechanics.FeetOffset(src);
            try { ph.Name = pp.cosmetics.nameText; } catch { }
            WireAnimation(ph);
            ph.Srs = pp.GetComponentsInChildren<SpriteRenderer>(true).ToArray();
            Place(ph, 0f);
        }

        private static AnimationClip idleClip, runClip;
        private static void WireAnimation(Phantom ph) {
            try {
                if (idleClip == null || runClip == null) {
                    var g = PlayerControl.LocalPlayer?.MyPhysics?.Animations?.group;
                    if (g != null) { idleClip = g.IdleAnim; runClip = g.RunAnim; }
                }
                var body = ph.Pp.cosmetics.currentBodySprite.BodySprite;
                if (body != null && idleClip != null) {
                    var anim = body.GetComponent<SpriteAnim>();
                    if (anim == null) {
                        if (body.GetComponent<Animator>() == null) body.gameObject.AddComponent<Animator>();
                        anim = body.gameObject.AddComponent<SpriteAnim>();
                    }
                    ph.BodyAnim = anim;
                }
            } catch (Exception e) { HwMechanics.Warn($"phantoms: body animation: {e.Message}"); }
        }

        // skins load asynchronously: wire their animation once they are there
        private static void WireSkin(Phantom ph) {
            if (ph.SkinAnim != null || ph.Pp == null) return;
            try {
                var view = ph.Pp.GetSkinView();
                var sa = ph.Pp.GetSkinSpriteAnim();
                if (view == null || sa == null || view.IdleAnim == null || view.RunAnim == null) return;
                ph.SkinIdle = view.IdleAnim; ph.SkinRun = view.RunAnim; ph.SkinAnim = sa;
                ph.AnimSet = false;
            } catch { }
        }

        private static void Place(Phantom ph, float t) {
            var pos = Evaluate(ph, t, out bool moving, out float dx);
            ph.Pos = pos;
            if (ph.Go == null) return;
            ph.Go.transform.position = new Vector3(pos.x + ph.Offset.x, pos.y + ph.Offset.y, (pos.y + ph.FeetZ) / 1000f);
            if (Mathf.Abs(dx) > 0.02f) ph.FaceLeft = dx < 0f;
            try { ph.Pp.SetFlipX(ph.FaceLeft); } catch { }
            WireSkin(ph);
            if (!ph.AnimSet || moving != ph.AnimRun) {
                ph.AnimRun = moving;
                ph.AnimSet = true;
                try { if (ph.BodyAnim != null) ph.BodyAnim.Play(moving ? runClip : idleClip, 1f); } catch { }
                try { if (ph.SkinAnim != null) ph.SkinAnim.Play(moving ? ph.SkinRun : ph.SkinIdle, 1f); } catch { }
            }
            ph.Moving = moving;
            // fade in at the start, out at the end; impostors see through their own illusion a little
            float a = Mathf.Clamp01(t / 0.6f) * Mathf.Clamp01((seconds - t) / 0.6f);
            if (HwMechanics.IsImp(PlayerControl.LocalPlayer)) a *= 0.6f;
            SetAlpha(ph, a);
        }

        private static void SetAlpha(Phantom ph, float a) {
            if (ph.Srs != null)
                foreach (var sr in ph.Srs) {
                    if (sr == null) continue;
                    var c = sr.color;
                    if (Mathf.Abs(c.a - a) > 0.003f) sr.color = new Color(c.r, c.g, c.b, a);
                }
            try { if (ph.Name != null) ph.Name.alpha = a; } catch { }
        }

        private static void DestroyVisual(Phantom ph) {
            try { if (ph.Go != null) UnityEngine.Object.Destroy(ph.Go); } catch { }
            ph.Go = null; ph.Pp = null; ph.Srs = null; ph.Name = null; ph.BodyAnim = null; ph.SkinAnim = null;
        }

        // ================================================================ per frame
        internal static void Tick() {
            Mist.Tick();
            if (!running) return;
            if (!HwMechanics.InRound()) { ApplyEnd("no round"); return; }
            float t = Time.time - startedAt;
            if (t >= seconds) {
                if (HwMechanics.AmHost()) { HwMechanics.Send(HwMechanics.SubPhantomEnd, null); ApplyEnd("time"); }
                else if (t >= seconds + 1.5f) ApplyEnd("time (local)");
                else foreach (var ph in phantoms) SetAlpha(ph, 0f);
                return;
            }
            var lp = PlayerControl.LocalPlayer;
            bool canTouch = HwMechanics.IsAlive(lp) && !HwMechanics.InMeeting();
            var me = canTouch ? lp.GetTruePosition() : Vector2.zero;
            foreach (var ph in phantoms) {
                if (ph.Gone) continue;
                // a lost visual (scene change, destroyed object) is rebuilt instead of leaving a hole in the parade
                if (ph.Go == null && ph.Pp == null) { try { Spawn(ph); } catch { } }
                Place(ph, t);
                if (!canTouch || ph.Asked || t < 0.6f) continue;
                if ((ph.Pos - me).magnitude < 0.5f) {
                    ph.Asked = true;
                    if (HwMechanics.AmHost()) HostTouch(lp, ph.Index);
                    else { byte idx = ph.Index; HwMechanics.Send(HwMechanics.SubPhantomTouch, w => w.Write(idx)); }
                }
            }
        }

        // ================================================================ map button
        private static SpriteRenderer mapButton;

        [HarmonyPatch(typeof(MapBehaviour), nameof(MapBehaviour.Show))]
        static class MapShowPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix(MapBehaviour __instance) {
                try { BindMap(__instance); } catch (Exception e) { HwMechanics.Warn($"phantoms: map button: {e.Message}"); }
            }
        }

        [HarmonyPatch(typeof(MapBehaviour), nameof(MapBehaviour.FixedUpdate))]
        static class MapTickPatch {
            public static void Postfix() {
                try {
                    if (mapButton == null) return;
                    float w = Wait();
                    mapButton.color = running ? new Color(1f, 0.55f, 0.55f) : w != 0f ? new Color(0.5f, 0.5f, 0.5f) : Color.white;
                } catch { }
            }
        }

        internal static bool MapButtonShown => mapButton != null && mapButton.gameObject.activeInHierarchy;
        internal static Vector3 MapButtonPos => mapButton != null ? mapButton.transform.position : Vector3.zero;

        private static void BindMap(MapBehaviour map) {
            var ov = map?.infectedOverlay;
            var ship = ShipStatus.Instance;
            if (ov == null || ov.rooms == null || ship == null) return;
            const string Name = "Hw_PhantomParade";
            var t = ov.transform.Find(Name);
            bool want = Enabled() && (HwMechanics.IsImp(PlayerControl.LocalPlayer) || DiagForce) && HwMechanics.InRound();
            if (!want) { if (t != null) t.gameObject.SetActive(false); mapButton = null; return; }
            SpriteRenderer template = null;
            foreach (var r in ov.rooms) if (r != null && r.special != null) { template = r.special; break; }
            if (template == null) return;
            if (t == null) {
                var go = UnityEngine.Object.Instantiate(template.gameObject, ov.transform);
                go.name = Name;
                t = go.transform;
            }
            t.gameObject.SetActive(true);
            var parent = map.HerePoint != null ? map.HerePoint.transform.parent : map.transform;
            float sx = Mathf.Sign(ship.transform.localScale.x);
            float size = template.sprite != null ? template.sprite.bounds.size.x * template.transform.lossyScale.x : 0.4f;
            // the middle of the biggest room, moved down until no other map button is in the way
            Vector2 world = ButtonWorldSpot(ship);
            var wp = parent.TransformPoint(new Vector3(world.x / ship.MapScale * sx, world.y / ship.MapScale, 0f));
            var others = new List<Vector3>();
            foreach (var r in ov.rooms) {
                if (r == null) continue;
                if (r.special != null && r.special.gameObject.activeInHierarchy) others.Add(r.special.transform.position);
                if (r.door != null && r.door.gameObject.activeInHierarchy) others.Add(r.door.transform.position);
            }
            for (int ci = 0; ci < ov.transform.childCount; ci++) {
                var c = ov.transform.GetChild(ci);
                if (c != null && c != t && c.name.StartsWith("Atlas_VCrisis") && c.gameObject.activeSelf) others.Add(c.position);
            }
            for (int k = 0; k < 6 && others.Any(o => ((Vector2)(o - wp)).magnitude < size * 1.1f); k++) wp += new Vector3(0f, -size * 1.1f, 0f);
            t.position = new Vector3(wp.x, wp.y, template.transform.position.z);
            var sr = t.GetComponent<SpriteRenderer>();
            if (sr != null && template.sprite != null) sr.sprite = IconSprite(template.sprite.bounds.size.x);
            var bb = t.GetComponent<ButtonBehavior>();
            if (bb != null) {
                bb.OnClick = new UnityEngine.UI.Button.ButtonClickedEvent();
                bb.OnClick.AddListener((Action)(() => { if (Wait() == 0f && !running) Request(); }));
            }
            mapButton = sr;
        }

        private static Vector2 ButtonWorldSpot(ShipStatus ship) {
            PlainShipRoom best = null;
            float area = -1f;
            try {
                foreach (var r in ship.AllRooms) {
                    if (r == null || r.roomArea == null || r.RoomId == SystemTypes.Outside || r.RoomId == SystemTypes.Hallway) continue;
                    var s = r.roomArea.bounds.size;
                    if (s.x * s.y > area) { area = s.x * s.y; best = r; }
                }
            } catch { }
            return best != null ? (Vector2)best.roomArea.bounds.center : Vector2.zero;
        }

        // ================================================================ pictures and sound
        internal static Sprite IconSprite(float size) =>
            HwArt.Get(Folder, "icon_phantom_parade.png", size, new Vector2(0.5f, 0.5f), DrawIcon);

        internal static TreatFx.Canvas DrawIcon() {
            var cv = new TreatFx.Canvas(256, 256);
            var ink = HwArt.C(0.12f, 0.08f, 0.16f);
            cv.Disc(128f, 128f, 122f, ink);
            cv.Disc(128f, 128f, 112f, HwArt.C(0.42f, 0.30f, 0.62f));
            cv.Disc(128f, 128f, 100f, HwArt.C(0.30f, 0.20f, 0.46f));
            // three marching ghosts, the front one big
            void Ghost(float cx, float cy, float s, float a) {
                var w = HwArt.C(0.95f, 0.95f, 1f, a);
                cv.Ellipse(cx, cy + 14f * s, 30f * s, 34f * s, w);
                cv.Rect(cx - 30f * s, cy - 22f * s, cx + 30f * s, cy + 14f * s, w);
                for (int k = 0; k < 4; k++) cv.Disc(cx - 22.5f * s + k * 15f * s, cy - 22f * s, 7.5f * s, w);
                cv.Ellipse(cx - 11f * s, cy + 18f * s, 5f * s, 8f * s, ink);
                cv.Ellipse(cx + 11f * s, cy + 18f * s, 5f * s, 8f * s, ink);
                cv.Ellipse(cx, cy + 2f * s, 6f * s, 7f * s, ink);
            }
            Ghost(78f, 128f, 0.7f, 0.55f);
            Ghost(178f, 132f, 0.7f, 0.55f);
            Ghost(128f, 116f, 1.15f, 1f);
            return cv;
        }

        private static AudioClip whoosh;
        private static void PlayWhoosh() {
            try {
                if (!Constants.ShouldPlaySfx() || SoundManager.Instance == null) return;
                if (whoosh == null) {
                    const int rate = 44100;
                    float len = 1.8f;
                    int n = (int)(rate * len);
                    var data = new float[n];
                    var noise = new System.Random(7);
                    float lp = 0f, lp2 = 0f;
                    double ph = 0;
                    for (int i = 0; i < n; i++) {
                        float t = (float)i / rate, u = t / len;
                        float cut = Mathf.Lerp(0.02f, 0.12f, Mathf.Sin(u * Mathf.PI));
                        lp += ((float)noise.NextDouble() * 2f - 1f - lp) * cut;
                        lp2 += (lp - lp2) * cut;
                        ph += 2 * Math.PI * Mathf.Lerp(220f, 330f, u) / rate;
                        float env = Mathf.Sin(u * Mathf.PI);
                        data[i] = env * (0.6f * lp2 + 0.12f * (float)Math.Sin(ph) * (1f + 0.3f * Mathf.Sin(t * 30f)));
                    }
                    whoosh = AudioClip.Create("phantom_whoosh", n, 1, rate, false);
                    whoosh.SetData(data, 0);
                    whoosh.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                }
                SoundManager.Instance.PlaySound(whoosh, false, 0.7f);
            } catch { }
        }

        // ================================================================ mist (the decay)
        internal static class Mist {
            private sealed class Puff { public SpriteRenderer Sr; public float Start; }
            private static readonly List<Puff> puffs = new();
            private const int Frames = 8;
            private const float Life = 0.7f;
            private static Sprite[] frames;

            internal static Sprite Frame(int i) {
                frames ??= new Sprite[Frames];
                if (frames[i] != null) return frames[i];
                frames[i] = HwArt.Get(Folder, $"phantom_mist_{i + 1}.png", 1.2f, new Vector2(0.5f, 0.3f), () => DrawMist(i));
                return frames[i];
            }

            internal static TreatFx.Canvas DrawMist(int i) {
                var cv = new TreatFx.Canvas(128, 128);
                float k = i / (float)(Frames - 1);
                var rng = new System.Random(21);
                for (int b = 0; b < 14; b++) {
                    float ang = (float)rng.NextDouble() * Mathf.PI * 2f, rr = (float)rng.NextDouble();
                    float cx = 64f + Mathf.Cos(ang) * rr * (14f + 34f * k), cy = 50f + Mathf.Sin(ang) * rr * (10f + 22f * k) + 30f * k;
                    float size = (10f + 8f * (float)rng.NextDouble()) * (0.8f + 0.9f * k);
                    cv.Disc(cx, cy, size, HwArt.C(0.85f, 0.85f, 0.95f, 0.5f * (1f - k * 0.85f)));
                }
                cv.Disc(64f, 50f + 20f * k, 18f * (1f - k), HwArt.C(1f, 1f, 1f, 0.6f * (1f - k)));
                return cv;
            }

            internal static void Spawn(Vector3 at, float feetZ) {
                var go = new GameObject("PhantomMist") { layer = 11 };
                UnityEngine.Object.DontDestroyOnLoad(go);
                go.transform.position = new Vector3(at.x, at.y - 0.2f, at.z - 0.01f);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = Frame(0);
                puffs.Add(new Puff { Sr = sr, Start = Time.time });
            }

            internal static void Tick() {
                for (int i = puffs.Count - 1; i >= 0; i--) {
                    var p = puffs[i];
                    float t = Time.time - p.Start;
                    if (p.Sr == null || t >= Life) { if (p.Sr != null) UnityEngine.Object.Destroy(p.Sr.gameObject); puffs.RemoveAt(i); continue; }
                    p.Sr.sprite = Frame(Mathf.Clamp((int)(t / Life * Frames), 0, Frames - 1));
                }
            }

            internal static void Clear() {
                foreach (var p in puffs) if (p.Sr != null) UnityEngine.Object.Destroy(p.Sr.gameObject);
                puffs.Clear();
            }
        }
    }

    /// <summary>The walking graph of the phantoms, the same on every client: deterministic samples per room (seeded
    /// by the room, not by chance) plus the free spots next to the vents, edges = free circle casts (doors ignored).
    /// Only nodes connected to a vent count (no islands behind walls or in space).</summary>
    internal static class PhantomGraph {
        internal static readonly List<Vector2> Nodes = new();
        internal static readonly List<List<(int to, float len)>> Edges = new();
        internal static readonly List<int> Main = new();
        private static IntPtr builtFor;
        private static string builtMap;
        private const float Radius = 0.25f, MaxEdge = 4.5f;
        private static readonly Dictionary<int, bool> doorCache = new();

        private static bool IsDoor(Collider2D c) {
            if (c == null) return false;
            int id = c.GetInstanceID();
            if (doorCache.TryGetValue(id, out var d)) return d;
            try { d = c.GetComponentInParent<OpenableDoor>() != null || c.gameObject.name.IndexOf("door", StringComparison.OrdinalIgnoreCase) >= 0; } catch { d = false; }
            doorCache[id] = d;
            return d;
        }

        private static bool Blocked(Vector2 p, float r, int mask) {
            try { foreach (var c in Physics2D.OverlapCircleAll(p, r, mask)) if (c != null && !c.isTrigger && !IsDoor(c)) return true; } catch { return true; }
            return false;
        }

        private static bool Clear(Vector2 a, Vector2 b, int mask) {
            var d = b - a;
            float len = d.magnitude;
            if (len < 0.01f) return true;
            try { foreach (var h in Physics2D.CircleCastAll(a, Radius, d / len, len, mask)) if (h.collider != null && !h.collider.isTrigger && !IsDoor(h.collider)) return false; } catch { return false; }
            return true;
        }

        internal static void Ensure(ShipStatus ship) {
            string map = HwMechanics.AtlasMap();
            if (builtFor == ship.Pointer && builtMap == map && Main.Count > 0) return;
            builtFor = ship.Pointer;
            builtMap = map;
            Build(ship);
        }

        private static void Build(ShipStatus ship) {
            var sw = System.Diagnostics.Stopwatch.StartNew();
            Nodes.Clear(); Edges.Clear(); Main.Clear(); doorCache.Clear();
            int mask = Constants.ShipAndObjectsMask;
            var ventNodes = new HashSet<int>();
            try {
                foreach (var v in ship.AllVents.ToArray().Where(v => v != null).OrderBy(v => v.Id)) {
                    var c = (Vector2)v.transform.position;
                    foreach (var off in new[] { new Vector2(0.7f, 0f), new Vector2(-0.7f, 0f), new Vector2(0f, -0.6f), new Vector2(0f, 0.6f) })
                        if (!Blocked(c + off, 0.3f, mask)) { ventNodes.Add(Nodes.Count); Nodes.Add(c + off); }
                }
            } catch { }
            var rooms = new List<PlainShipRoom>();
            try { foreach (var r in ship.AllRooms) if (r != null && r.roomArea != null) rooms.Add(r); } catch { }
            rooms = rooms.OrderBy(r => (int)r.RoomId).ThenBy(r => r.roomArea.bounds.center.x).ThenBy(r => r.roomArea.bounds.center.y).ToList();
            for (int ri = 0; ri < rooms.Count; ri++) {
                var room = rooms[ri];
                var bb = room.roomArea.bounds;
                var rng = new System.Random(1009 + (int)room.RoomId * 7919 + ri * 131);
                int want = Mathf.Clamp(Mathf.RoundToInt(bb.size.x * bb.size.y / 2.2f), 6, room.RoomId == SystemTypes.Outside ? 160 : 70);
                for (int t = 0; t < want * 4 && want > 0; t++) {
                    var p = new Vector2(Mathf.Lerp(bb.min.x, bb.max.x, (float)rng.NextDouble()), Mathf.Lerp(bb.min.y, bb.max.y, (float)rng.NextDouble()));
                    if (!room.roomArea.OverlapPoint(p) || Blocked(p, 0.38f, mask)) continue;
                    Nodes.Add(p);
                    want--;
                }
            }
            for (int i = 0; i < Nodes.Count; i++) Edges.Add(new List<(int, float)>());
            for (int i = 0; i < Nodes.Count; i++) {
                var near = new List<(int j, float d)>();
                for (int j = i + 1; j < Nodes.Count; j++) {
                    float d = (Nodes[j] - Nodes[i]).magnitude;
                    if (d < MaxEdge && d > 0.05f) near.Add((j, d));
                }
                foreach (var (j, d) in near.OrderBy(x => x.d).Take(10)) {
                    if (!Clear(Nodes[i], Nodes[j], mask)) continue;
                    Edges[i].Add((j, d));
                    Edges[j].Add((i, d));
                }
            }
            // connected to a vent (or, without vents, the biggest island)
            var comp = new int[Nodes.Count];
            for (int i = 0; i < comp.Length; i++) comp[i] = -1;
            int nc = 0;
            var sizes = new List<int>();
            for (int s = 0; s < Nodes.Count; s++) {
                if (comp[s] >= 0) continue;
                int size = 0;
                var q = new Queue<int>();
                q.Enqueue(s); comp[s] = nc;
                while (q.Count > 0) {
                    int u = q.Dequeue(); size++;
                    foreach (var (to, _) in Edges[u]) if (comp[to] < 0) { comp[to] = nc; q.Enqueue(to); }
                }
                sizes.Add(size);
                nc++;
            }
            var keep = new HashSet<int>(ventNodes.Select(v => comp[v]).Where(c => c >= 0 && sizes[c] >= 8));
            if (keep.Count == 0 && sizes.Count > 0) keep.Add(sizes.IndexOf(sizes.Max()));
            for (int i = 0; i < Nodes.Count; i++) if (keep.Contains(comp[i])) Main.Add(i);
            HwMechanics.Log($"phantoms: graph {Nodes.Count} nodes, {Edges.Sum(e => e.Count) / 2} edges, {Main.Count} walkable in {keep.Count} part(s), {sw.ElapsedMilliseconds} ms");
        }

        /// <summary>Shortest path (Dijkstra with a small binary heap), node indices from a to b, null when none.</summary>
        internal static List<int> Path(int a, int b) {
            int n = Nodes.Count;
            var dist = new float[n];
            var prev = new int[n];
            for (int i = 0; i < n; i++) { dist[i] = float.MaxValue; prev[i] = -1; }
            var heap = new List<(float d, int u)>();
            void Push(float d, int u) {
                heap.Add((d, u));
                int i = heap.Count - 1;
                while (i > 0) { int p = (i - 1) / 2; if (heap[p].d <= heap[i].d) break; (heap[p], heap[i]) = (heap[i], heap[p]); i = p; }
            }
            (float d, int u) Pop() {
                var top = heap[0];
                heap[0] = heap[heap.Count - 1];
                heap.RemoveAt(heap.Count - 1);
                int i = 0;
                while (true) {
                    int l = 2 * i + 1, r = l + 1, m = i;
                    if (l < heap.Count && heap[l].d < heap[m].d) m = l;
                    if (r < heap.Count && heap[r].d < heap[m].d) m = r;
                    if (m == i) break;
                    (heap[m], heap[i]) = (heap[i], heap[m]); i = m;
                }
                return top;
            }
            dist[a] = 0f;
            Push(0f, a);
            while (heap.Count > 0) {
                var (d, u) = Pop();
                if (d > dist[u]) continue;
                if (u == b) break;
                foreach (var (to, len) in Edges[u]) {
                    float nd = d + len;
                    if (nd < dist[to]) { dist[to] = nd; prev[to] = u; Push(nd, to); }
                }
            }
            if (dist[b] == float.MaxValue) return null;
            var path = new List<int>();
            for (int v = b; v >= 0; v = prev[v]) path.Add(v);
            path.Reverse();
            return path;
        }
    }
}
