/*
 * Live spider legs (2026-10-17): the spider costume's eight legs are worked out every frame instead of
 * coming from a pre-rendered loop. Model: the spidertron from Factorio. Every foot sticks to a fixed
 * point of the map while the player walks on; once a foot leaves its reach around its rest point, that
 * one leg steps in a high arc to a new point ahead. Two walking groups take turns, starts within a
 * group are staggered; on stopping the legs step back into their rest pose, later one leg now and then
 * fidgets. The crewmate itself stays in its idle pose (HalloweenCostumes.StillWalkPatch).
 *
 * Logic and numbers are a 1:1 port of tmp/halloween_hats_v2/spider_live.py (Fable, branch spider-live);
 * the drawing follows spider_live_preview.py. All geometry is in "bean units" of the 300 x 375 hat
 * picture; SpiderLegData.g.cs holds projection, legs, parts and logic constants (generated).
 *
 * Differences to the reference, all because the game drives things the simulation decided itself:
 *   - facing comes from the costume's real flip (the game turns body and hat), not from vx hysteresis;
 *   - the body position is the player's real position, the velocity is measured from it (smoothed),
 *     so remote players walk the same way;
 *   - a jump (vent, meeting, kill teleport) or a longer pause puts all feet back to rest.
 *
 * Rendering: per hat two groups of child renderers, the far legs under the hat's back layer (behind the
 * crewmate), the near legs under the front layer. Order inside a group via tiny z steps, the same trick
 * as the accent layer. The groups are mirrored by scale when the costume is flipped.
 */

using System;
using System.Collections.Generic;
using UnityEngine;
using static UnknownsHalloween.SpiderLegData;

namespace UnknownsHalloween {
    internal static class SpiderLegs {
        private const string Res = "UnknownsHalloween.Resources.hats.";
        private static readonly float SinPhi = Mathf.Sin(PhiDeg * Mathf.Deg2Rad), CosPhi = Mathf.Cos(PhiDeg * Mathf.Deg2Rad);
        private static readonly float SinEps = Mathf.Sin(EpsDeg * Mathf.Deg2Rad), CosEps = Mathf.Cos(EpsDeg * Mathf.Deg2Rad);
        // Hat sprites (HalloweenCostumes.LoadHatSprite): pixelsPerUnit = width * 0.375, so the picture is
        // 1 / 0.375 hat units wide at any resolution. One bean unit = OutScale * FitK px of 600.
        private const float BeanToHat = OutScale * FitK / (600f * 0.375f);

        private sealed class LegSt {
            public float Fx, Fy, Z;                 // foot on the map (bean units), height
            public bool Swinging;
            public float Sx, Sy, Tx, Ty, T, Dur, Lift;
        }

        private sealed class Rend { public SpriteRenderer Femur, Tibia, Knee, Foot, Cuff; }

        private sealed class St {
            public float BodyX, BodyY, Vx, Vy;
            public int Facing = 1;
            public char Active = 'A';
            public float SinceStart = 99f, Stopped = 99f, Quiet, Fidget;
            public uint Rng;
            public readonly LegSt[] Legs = new LegSt[SpiderLegData.Legs.Length];
            public bool Init;
            public float LastSeen;
            public GameObject FarRoot, NearRoot;
            public Rend[] R;
            public readonly int[] Order = new int[SpiderLegData.Legs.Length];
            public readonly float[] Depth = new float[SpiderLegData.Legs.Length];
        }

        private static readonly Dictionary<int, St> states = new();
        private static readonly Dictionary<string, Sprite> sprites = new();
        private static bool loadFailed;

        // ---------------------------------------------------------------- random (spider_live.Rng)
        private static void Seed(St st, uint seed) { unchecked { st.Rng = seed * 2654435761u + 12345u; } }
        private static float Next(St st) { unchecked { st.Rng = 1664525u * st.Rng + 1013904223u; } return st.Rng / 4294967296f; }
        private static float Uniform(St st, float a, float b) => a + (b - a) * Next(st);

        // ---------------------------------------------------------------- geometry (spider_rig.py)
        private static Vector2 Project(float f, float l, float z) =>
            new Vector2(Cx + SinPhi * f + CosPhi * l, GroundY - CosEps * z + SinEps * (CosPhi * f - SinPhi * l));

        private static float DepthOf(float f, float l) => CosPhi * f - SinPhi * l;

        private static Vector3 ReachableFoot(Vector3 c, Vector3 foot, float la, float lb) {
            var d = foot - c;
            float n = d.magnitude, max = la + lb - 1f;
            if (n <= max || n < 1e-6f) return foot;
            return c + d * (max / n);
        }

        private static Vector3 Knee3d(Vector3 c, Vector3 foot, float la, float lb) {
            var dv = foot - c;
            float d = dv.magnitude;
            float n = d > 1e-6f ? d : 1f;
            var u = dv / n;
            d = Mathf.Max(Mathf.Abs(la - lb) + 1f, Mathf.Min(la + lb - 1f, d));
            var p = new Vector3(-u.z * u.x, -u.z * u.y, 1f - u.z * u.z);
            float pn = p.magnitude;
            p = pn < 1e-6f ? new Vector3(0f, 0f, 1f) : p / pn;
            float a = (la * la - lb * lb + d * d) / (2f * d);
            float h = Mathf.Sqrt(Mathf.Max(0f, la * la - a * a));
            return c + u * a + p * h;
        }

        // Distance of a foot from its rest point in units of Reach, elliptic: a crewmate seen from the side has
        // little room for feet up and down the screen (the hips are only ~60 above the floor), least upwards.
        private static float GroundDist(float df, float dv) {
            float sv = dv * GroundVScale;
            float rv = sv > 0f ? ReachUp : ReachDown;
            float e = sv * Reach / rv;
            return Mathf.Sqrt(df * df + e * e);
        }

        // Lookahead along the map's up/down to match the elliptic reach (map units per unit of lookahead).
        private static float VLook(float dirV) => (dirV > 0f ? ReachUp : ReachDown) / Reach / GroundVScale;

        // Ground point of a foot (f along facing, v up the map, z lift) -> 3D foot for the knee. The floor is the map,
        // which the game shows 1:1 (top-down), so a planted foot has to shift on screen exactly like the floor:
        // keep the rest foot's depth, reach the screen height through z (may go below 0).
        private static Vector3 GroundTo3d(Leg leg, float f, float v, float z) {
            var p0 = Project(leg.RestF, leg.RestL, 0f);
            float x = p0.x + (f - leg.RestF), y = p0.y - v * GroundVScale;
            float f3 = (x - Cx - CosPhi * leg.RestL) / SinPhi;
            float z3 = (GroundY + SinEps * (CosPhi * f3 - SinPhi * leg.RestL) - y) / CosEps;
            return new Vector3(f3, leg.RestL, z3 + z);
        }

        // Hip, knee, foot in picture space (bean units, y down) for a foot (f, v, z) on the ground. No clamp to the
        // picture's edges any more: the legs are sprites of their own, and the clamp made feet slide.
        private static void ImagePoints(Leg leg, Vector3 ground, out Vector2 r, out Vector2 k, out Vector2 t) {
            var c = new Vector3(leg.HipF, leg.HipL, leg.HipZ);
            var foot = ReachableFoot(c, GroundTo3d(leg, ground.x, ground.y, ground.z), leg.Femur, leg.Tibia);
            var kn = Knee3d(c, foot, leg.Femur, leg.Tibia);
            r = Project(c.x, c.y, c.z); k = Project(kn.x, kn.y, kn.z); t = Project(foot.x, foot.y, foot.z);
            if (!float.IsNaN(leg.KneeYMin) && k.y < leg.KneeYMin) k.y = leg.KneeYMin;
            if (leg.Near && k.x >= FaceX0 && k.x <= FaceX1 && k.y < FaceY1) k.y = FaceY1;   // never over the face
        }

        // ---------------------------------------------------------------- state
        private static Vector2 ToWorld(St st, float f, float l) => new Vector2(st.BodyX + st.Facing * f, st.BodyY + l);
        private static Vector2 ToLocal(St st, float x, float y) => new Vector2(st.Facing * (x - st.BodyX), y - st.BodyY);

        private static void ResetFeet(St st, float x, float y, int facing) {
            st.BodyX = x; st.BodyY = y; st.Facing = facing; st.Vx = st.Vy = 0f;
            st.Active = 'A'; st.SinceStart = 99f; st.Stopped = 99f; st.Quiet = 0f;
            for (int i = 0; i < Legs.Length; i++) {
                var w = ToWorld(st, Legs[i].RestF, 0f);                    // ground point: v = 0
                st.Legs[i] = new LegSt { Fx = w.x, Fy = w.y };
            }
            st.Fidget = Uniform(st, FidgetIntervalMin, FidgetIntervalMax);
            st.Init = true;
        }

        private static float SwingFraction(LegSt ls) => ls.Swinging ? Mathf.Min(1f, ls.T / ls.Dur) : 1f;

        private static void StartStep(St st, int i, float tf, float tl, float vx, float vy, float duration = -1f, float lift = -1f) {
            var leg = Legs[i];
            var ls = st.Legs[i];
            var f0 = ToLocal(st, ls.Fx, ls.Fy);
            float dist = Mathf.Sqrt((tf - f0.x) * (tf - f0.x) + (tl - f0.y) * (tl - f0.y));
            if (duration < 0f) {
                float sp = Mathf.Max(StepSpeed, StepSpeedFactor * Mathf.Sqrt(vx * vx + vy * vy));
                duration = Mathf.Clamp(dist / sp, StepDurationMin, StepDurationMax);
            }
            if (lift < 0f) lift = leg.Lift * Mathf.Clamp(dist / LiftRefDistance, LiftScaleMin, LiftScaleMax);
            var w = ToWorld(st, tf, tl);
            ls.Swinging = true;
            ls.Sx = ls.Fx; ls.Sy = ls.Fy;
            // the body keeps moving during the step: aim where the foot must land relative to it
            ls.Tx = w.x + vx * duration; ls.Ty = w.y + vy * duration;
            ls.T = 0f; ls.Dur = duration; ls.Lift = lift;
            st.SinceStart = 0f;
            st.Quiet = 0f;
        }

        private static void AdvanceSwings(St st, float dt) {
            foreach (var ls in st.Legs) {
                if (!ls.Swinging) continue;
                ls.T += dt;
                float u = Mathf.Min(1f, ls.T / ls.Dur);
                float e = Mathf.Pow(u, SwingXPower);
                ls.Fx = ls.Sx + (ls.Tx - ls.Sx) * e;
                ls.Fy = ls.Sy + (ls.Ty - ls.Sy) * e;
                ls.Z = ls.Lift * Mathf.Pow(Mathf.Sin(Mathf.PI * u), SwingZPower);
                if (u >= 1f) { ls.Swinging = false; ls.Z = 0f; ls.Fx = ls.Tx; ls.Fy = ls.Ty; }
            }
        }

        // spider_live.update; the body has already been moved to the player's position.
        private static void Step(St st, float dt, float vx, float vy) {
            float speed = Mathf.Sqrt(vx * vx + vy * vy);
            bool moving = speed > SpeedEpsilon;
            float dirF = 0f, dirL = 0f;
            if (moving) { dirF = st.Facing * vx / speed; dirL = vy / speed; st.Stopped = 0f; } else st.Stopped += dt;
            AdvanceSwings(st, dt);
            st.SinceStart += dt;
            // hard limit: a planted foot slides along rather than trailing further (only at extreme speed)
            for (int i = 0; i < Legs.Length; i++) {
                var ls = st.Legs[i];
                if (ls.Swinging) continue;
                var p = ToLocal(st, ls.Fx, ls.Fy);
                float df = p.x - Legs[i].RestF, dl = p.y, d = GroundDist(df, dl);
                if (d <= HardReach) continue;
                float k = HardReach / d;
                var w = ToWorld(st, Legs[i].RestF + df * k, dl * k);
                ls.Fx = w.x; ls.Fy = w.y;
            }

            // need per leg: distance of the foot from its rest point (costume space)
            needCount = 0;
            for (int i = 0; i < Legs.Length; i++) {
                var ls = st.Legs[i];
                if (ls.Swinging) continue;
                var p = ToLocal(st, ls.Fx, ls.Fy);
                float d = GroundDist(p.x - Legs[i].RestF, p.y);
                if (moving) { if (d > Reach) Need(d / Reach, i); }
                else if (st.Stopped > SettleDelay && d > SettleTolerance) Need(d / Reach + 0.5f, i);
            }
            // most urgent first (Python: sort reverse on (urgency, index))
            Array.Sort(needUrg, needIdx, 0, needCount);
            Array.Reverse(needUrg, 0, needCount);
            Array.Reverse(needIdx, 0, needCount);

            int swinging = 0;
            foreach (var ls in st.Legs) if (ls.Swinging) swinging++;
            if (needCount > 0) {
                st.Quiet = 0f;
                bool hurry = needCount >= HurryOverdue || needUrg[0] * Reach > EmergencyReach;
                int maxSw = hurry ? MaxSwingingHurry : MaxSwinging;
                float stagger = Stagger * (hurry ? 0.5f : 1f);
                char active = st.Active;
                bool activeDone = true;
                for (int i = 0; i < Legs.Length; i++)
                    if (st.Legs[i].Swinging && Legs[i].Group == active && SwingFraction(st.Legs[i]) < 1f - GroupOverlap) activeDone = false;
                bool activeNeeds = false, otherNeeds = false;
                for (int k = 0; k < needCount; k++) { if (Legs[needIdx[k]].Group == active) activeNeeds = true; else otherNeeds = true; }
                if (activeDone && !activeNeeds && otherNeeds) st.Active = active = active == 'A' ? 'B' : 'A';
                if (swinging < maxSw && st.SinceStart >= stagger) {
                    for (int k = 0; k < needCount; k++) {
                        int i = needIdx[k];
                        bool emergency = needUrg[k] * Reach > EmergencyReach;
                        if (Legs[i].Group != active && !(emergency || hurry)) continue;
                        if (moving) {
                            float look = Mathf.Min(LookaheadMax, speed * LookaheadTime);
                            float tf = Legs[i].RestF + dirF * look + Uniform(st, -TargetRandom, TargetRandom);
                            float tl = dirL * look * VLook(dirL) + Uniform(st, -TargetRandom, TargetRandom);
                            StartStep(st, i, tf, tl, vx, vy);
                        } else {
                            float tf = Legs[i].RestF + Uniform(st, -SettleRandom, SettleRandom);
                            float tl = Uniform(st, -SettleRandom, SettleRandom);
                            StartStep(st, i, tf, tl, 0f, 0f);
                        }
                        break;      // one start per call, stagger does the spacing
                    }
                }
            } else if (swinging == 0 && !moving) {
                // idle fidget: after a quiet spell one leg now and then lifts briefly and sets down a little off
                st.Quiet += dt;
                if (st.Quiet > FidgetDelay) {
                    st.Fidget -= dt;
                    if (st.Fidget <= 0f) {
                        st.Fidget = Uniform(st, FidgetIntervalMin, FidgetIntervalMax);
                        bool near = Next(st) < FidgetNearProbability;
                        int pool = 0;
                        for (int i = 0; i < Legs.Length; i++) if (Legs[i].Near == near) pool++;
                        int pick = (int)(Next(st) * pool) % Mathf.Max(1, pool), i2 = -1;
                        for (int i = 0; i < Legs.Length; i++) if (Legs[i].Near == near && pick-- == 0) { i2 = i; break; }
                        if (i2 >= 0) {
                            float ang = Uniform(st, 0f, 2f * Mathf.PI), r = Uniform(st, 0.3f, 1f) * FidgetShift;
                            StartStep(st, i2, Legs[i2].RestF + Mathf.Cos(ang) * r, Mathf.Sin(ang) * r, 0f, 0f, FidgetDuration, FidgetLift);
                        }
                    }
                }
            } else {
                st.Quiet = swinging > 0 ? 0f : st.Quiet + dt;
            }
        }

        private static int needCount;
        private static readonly float[] needUrg = new float[8];
        private static readonly int[] needIdx = new int[8];
        private static void Need(float urgency, int i) { needUrg[needCount] = urgency; needIdx[needCount] = i; needCount++; }

        // ---------------------------------------------------------------- sprites
        // file -> Time.time of the next try (a package that arrives later is still picked up)
        private static readonly Dictionary<string, float> missing = new Dictionary<string, float>();
        private static Sprite PartSprite(Part p) {
            if (p == null) return null;
            if (sprites.TryGetValue(p.File, out var s) && s != null) return s;
            // a part that failed is not opened again every frame, only every 10 s (audit 21.10.)
            if (missing.TryGetValue(p.File, out float retry) && Time.time < retry) return null;
            try {
                using var stream = HalloweenAssets.Open(Res + p.File);
                if (stream == null) { missing[p.File] = Time.time + 10f; return null; }
                var data = new byte[stream.Length];
                int read = 0;
                while (read < data.Length) { int n = stream.Read(data, read, data.Length - read); if (n <= 0) break; read += n; }
                var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (!ImageConversion.LoadImage(tex, data, false)) { UnityEngine.Object.Destroy(tex); missing[p.File] = Time.time + 10f; return null; }
                tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                // p.Ppu pixels per bean unit -> pixels per hat unit
                s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(p.PivotX, p.PivotY), p.Ppu / BeanToHat);
                s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                sprites[p.File] = s;
                return s;
            } catch (Exception e) {
                if (!loadFailed) { loadFailed = true; HalloweenPlugin.Logger?.LogWarning($"[Halloween] spider leg part {p.File}: {e.Message}"); }
                return null;
            }
        }

        private static SpriteRenderer MakeSr(Transform parent, string name) {
            var go = new GameObject(name) { layer = parent.gameObject.layer };
            go.transform.SetParent(parent, false);
            return go.AddComponent<SpriteRenderer>();
        }

        private static void EnsureRenderers(St st, SpriteRenderer front, SpriteRenderer back) {
            if (st.FarRoot != null && st.NearRoot != null) return;
            if (st.FarRoot != null) UnityEngine.Object.Destroy(st.FarRoot);
            if (st.NearRoot != null) UnityEngine.Object.Destroy(st.NearRoot);
            st.FarRoot = new GameObject("SpiderLegsFar") { layer = back.gameObject.layer };
            st.FarRoot.transform.SetParent(back.transform, false);
            st.NearRoot = new GameObject("SpiderLegsNear") { layer = front.gameObject.layer };
            st.NearRoot.transform.SetParent(front.transform, false);
            st.R = new Rend[Legs.Length];
            for (int i = 0; i < Legs.Length; i++) {
                var root = (Legs[i].Near ? st.NearRoot : st.FarRoot).transform;
                st.R[i] = new Rend {
                    Femur = MakeSr(root, Legs[i].Id + "_femur"), Tibia = MakeSr(root, Legs[i].Id + "_tibia"),
                    Knee = MakeSr(root, Legs[i].Id + "_knee"), Foot = MakeSr(root, Legs[i].Id + "_foot"),
                    Cuff = Parts[i].Cuff != null ? MakeSr(root, Legs[i].Id + "_cuff") : null,
                };
            }
        }

        // picture space (bean units, y down) -> hat-local units of the layer the legs hang under
        private static Vector2 ToHat(Vector2 p, Sprite hatSprite) {
            float px = OutScale * (FitK * (p.x + ShiftX) + FitTx), py = OutScale * (FitK * p.y + FitTy);
            var rect = hatSprite.rect;
            float ppu = hatSprite.pixelsPerUnit;
            return new Vector2((px / 600f * rect.width - hatSprite.pivot.x) / ppu,
                               ((1f - py / 750f) * rect.height - hatSprite.pivot.y) / ppu);
        }

        private static void Place(SpriteRenderer sr, Sprite sprite, Vector2 pos, float angleDeg, float scaleX, float z,
                                  SpriteRenderer layer, Color tint) {
            if (sr == null) return;
            if (sr.sprite != sprite) sr.sprite = sprite;
            var t = sr.transform;
            t.localPosition = new Vector3(pos.x, pos.y, z);
            t.localRotation = Quaternion.Euler(0f, 0f, angleDeg);
            t.localScale = new Vector3(scaleX, 1f, 1f);
            if (sr.sharedMaterial != layer.sharedMaterial) sr.sharedMaterial = layer.sharedMaterial;
            sr.maskInteraction = layer.maskInteraction;
            sr.sortingLayerID = layer.sortingLayerID;
            sr.sortingOrder = layer.sortingOrder;
            sr.color = tint;
            if (!sr.enabled) sr.enabled = true;
        }

        private static void SetZ(SpriteRenderer sr, float worldZ) {
            if (sr == null) return;
            var t = sr.transform;
            var p = t.position;
            t.position = new Vector3(p.x, p.y, worldZ);
        }

        private static Part Variant(Part[] set, float length) {
            Part best = set[0];
            float bestR = float.MaxValue;
            foreach (var p in set) {
                float r = Mathf.Abs(Mathf.Log(Mathf.Max(1e-3f, length) / p.Length));
                if (r < bestR) { bestR = r; best = p; }
            }
            return best;
        }

        private static void Segment(SpriteRenderer sr, Part[] set, Vector2 a, Vector2 b, Sprite hatSprite, float z, SpriteRenderer layer, Color tint) {
            float len = Vector2.Distance(a, b);                         // bean units (picture space)
            var p = Variant(set, len);
            var ha = ToHat(a, hatSprite);
            var hb = ToHat(b, hatSprite);
            float ang = Mathf.Atan2(hb.y - ha.y, hb.x - ha.x) * Mathf.Rad2Deg;
            Place(sr, PartSprite(p), ha, ang, len / Mathf.Max(1e-3f, p.Length), z, layer, tint);
        }

        // ---------------------------------------------------------------- entry points

        /// <summary>Moves and draws the legs of this hat for the current frame. False = could not run
        /// (the caller then shows the classic frames with painted legs).</summary>
        internal static bool Drive(HatParent hat, PlayerControl pc, SpriteRenderer front, SpriteRenderer back) {
            if (hat == null || pc == null || front == null || back == null || front.sprite == null) return false;
            int id = hat.GetInstanceID();
            if (!states.TryGetValue(id, out var st)) {
                if (states.Count > 64) Clear();
                st = new St();
                Seed(st, (uint)(7 + pc.PlayerId));
                states[id] = st;
            }
            EnsureRenderers(st, front, back);

            // player position in bean units on the map
            float scale = Mathf.Abs(front.transform.lossyScale.x) * BeanToHat;     // world units per bean unit
            if (scale < 1e-6f) return false;
            Vector2 wp = pc.transform.position;
            float x = wp.x / scale, y = wp.y / scale;
            int facing = front.flipX ? -1 : 1;
            float dt = Time.deltaTime;
            float now = Time.time;
            bool jump = st.Init && dt > 0f && new Vector2(x - st.BodyX, y - st.BodyY).magnitude > 80f + 1500f * dt;
            if (!st.Init || jump || now - st.LastSeen > 0.5f) ResetFeet(st, x, y, facing);
            st.LastSeen = now;

            if (dt > 0f) {
                if (facing != st.Facing) {
                    // the game turned body and costume: mirror the feet at the player, the gait just carries on
                    st.Facing = facing;
                    foreach (var ls in st.Legs) { ls.Fx = 2f * st.BodyX - ls.Fx; ls.Sx = 2f * st.BodyX - ls.Sx; ls.Tx = 2f * st.BodyX - ls.Tx; }
                }
                float vx = (x - st.BodyX) / dt, vy = (y - st.BodyY) / dt;
                float k = 1f - Mathf.Exp(-dt * 14f);                  // network jitter of remote players
                st.Vx += (vx - st.Vx) * k; st.Vy += (vy - st.Vy) * k;
                st.BodyX = x; st.BodyY = y;
                Step(st, Mathf.Min(dt, 0.1f), st.Vx, st.Vy);
            }

            // draw: far legs behind the crewmate, near legs in front, each group back to front by depth
            var hatSprite = front.sprite;
            var tint = new Color(1f, 1f, 1f, front.color.a);
            float flip = front.flipX ? -1f : 1f;
            st.FarRoot.transform.localScale = new Vector3(flip, 1f, 1f);
            st.NearRoot.transform.localScale = new Vector3(flip, 1f, 1f);
            for (int i = 0; i < Legs.Length; i++) {
                var p = ToLocal(st, st.Legs[i].Fx, st.Legs[i].Fy);
                var f3 = GroundTo3d(Legs[i], p.x, p.y, 0f);
                st.Depth[i] = DepthOf((Legs[i].HipF + f3.x) * 0.5f, (Legs[i].HipL + f3.y) * 0.5f);
                st.Order[i] = i;
            }
            Array.Sort(st.Order, (a, b) => st.Depth[a].CompareTo(st.Depth[b]));
            // z (world): the game separates a player's layers by 1e-7 steps (measured 2026-10-17: back
            // layer +1e-7, body 0, skin -1e-7, front layer -2e-7, visor -3e-7; all order 0, same queue).
            // Far legs go just behind the back layer, near legs just in front of the visor, in 5e-8 steps:
            // fine enough not to reach other players (their z differs by y / 1000), coarse enough for floats.
            SpriteRenderer body = null;
            try { body = pc.cosmetics != null && pc.cosmetics.currentBodySprite != null ? pc.cosmetics.currentBodySprite.BodySprite : null; } catch { }
            float backZ = back.transform.position.z, frontZ = front.transform.position.z;
            int farRank = 0, nearRank = 0;
            LogOnce(st, pc, front, back, body, scale);
            foreach (int i in st.Order) {
                var leg = Legs[i];
                var ls = st.Legs[i];
                var p = ToLocal(st, ls.Fx, ls.Fy);
                ImagePoints(leg, new Vector3(p.x, p.y, ls.Z), out var r, out var kn, out var t);
                var parts = Parts[i];
                var rd = st.R[i];
                var layer = leg.Near ? front : back;
                Segment(rd.Femur, parts.Femur, r, kn, hatSprite, 0f, layer, tint);
                Segment(rd.Tibia, parts.Tibia, kn, t, hatSprite, 0f, layer, tint);
                var hk = ToHat(kn, hatSprite);
                var ht = ToHat(t, hatSprite);
                float tibAng = Mathf.Atan2(ht.y - hk.y, ht.x - hk.x) * Mathf.Rad2Deg;
                Place(rd.Knee, PartSprite(parts.Knee), hk, 0f, 1f, 0f, layer, tint);
                Place(rd.Foot, PartSprite(parts.Foot), ht, tibAng, 1f, 0f, layer, tint);
                if (rd.Cuff != null) {
                    var hr = ToHat(r, hatSprite);
                    float femAng = Mathf.Atan2(hk.y - hr.y, hk.x - hr.x) * Mathf.Rad2Deg;
                    Place(rd.Cuff, PartSprite(parts.Cuff), hr, femAng, 1f, 0f, layer, tint);
                }
                // back to front: later parts (and nearer legs) get the smaller z
                if (leg.Near) {
                    SetZ(rd.Femur, frontZ - 1e-6f - (nearRank * 5 + 0) * 5e-8f);
                    SetZ(rd.Tibia, frontZ - 1e-6f - (nearRank * 5 + 1) * 5e-8f);
                    SetZ(rd.Knee, frontZ - 1e-6f - (nearRank * 5 + 2) * 5e-8f);
                    SetZ(rd.Foot, frontZ - 1e-6f - (nearRank * 5 + 3) * 5e-8f);
                    SetZ(rd.Cuff, frontZ - 1e-6f - (nearRank * 5 + 4) * 5e-8f);
                    nearRank++;
                } else {
                    for (int s = 0; s < 4; s++)
                        SetZ(s == 0 ? rd.Femur : s == 1 ? rd.Tibia : s == 2 ? rd.Knee : rd.Foot, backZ + 1e-7f + (15 - (farRank * 4 + s)) * 5e-8f);
                    farRank++;
                }
            }
            if (!st.FarRoot.activeSelf) st.FarRoot.SetActive(true);
            if (!st.NearRoot.activeSelf) st.NearRoot.SetActive(true);
            return true;
        }

        // One log line per session for calibration after a playtest: layer depths and sorting, the
        // scale, and the local player's measured speed in bean units (the reference was tuned at 60-100,
        // the game runs at roughly 350 at speed 1.0).
        private static bool logged;
        private static float logSpeedSum, logSpeedTime;
        private static void LogOnce(St st, PlayerControl pc, SpriteRenderer front, SpriteRenderer back, SpriteRenderer body, float scale) {
            if (logged || pc == null || !pc.AmOwner) return;
            float speed = Mathf.Sqrt(st.Vx * st.Vx + st.Vy * st.Vy);
            if (speed < 50f) return;                                  // wait until the player really walks
            logSpeedSum += speed * Time.deltaTime; logSpeedTime += Time.deltaTime;
            if (logSpeedTime < 1f) return;
            logged = true;
            HalloweenPlugin.Logger?.LogInfo($"[Halloween] spider legs: speed {logSpeedSum / logSpeedTime:F0} bean/s, world per bean {scale:F5}, " +
                $"z back {back.transform.position.z:F6} body {(body != null ? body.transform.position.z.ToString("F6") : "-")} front {front.transform.position.z:F6}, " +
                $"order back {back.sortingOrder} body {(body != null ? body.sortingOrder.ToString() : "-")} front {front.sortingOrder}");
        }

        /// <summary>Hides the legs of this hat (ladder, vent, other hat, no owner ...).</summary>
        internal static void Hide(HatParent hat) {
            if (hat == null || states.Count == 0) return;
            if (!states.TryGetValue(hat.GetInstanceID(), out var st)) return;
            if (st.FarRoot != null && st.FarRoot.activeSelf) st.FarRoot.SetActive(false);
            if (st.NearRoot != null && st.NearRoot.activeSelf) st.NearRoot.SetActive(false);
        }

        internal static void Clear() {
            foreach (var st in states.Values) {
                if (st.FarRoot != null) UnityEngine.Object.Destroy(st.FarRoot);
                if (st.NearRoot != null) UnityEngine.Object.Destroy(st.NearRoot);
            }
            states.Clear();
        }
    }
}
