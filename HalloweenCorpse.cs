// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * HalloweenCorpse - a costume that makes the wearer look like the game's own corpse (the lower half
 * with the bone sticking out, User 2026-10-07).
 *
 * Probe (UC_HALLOWEEN_DIAG=corpse): kills a freeplay dummy and logs how the game draws the corpse
 * relative to the player (renderer offsets, sprite rects, pivots, scale), and saves the raw sprite
 * pixels, so the costume can draw the same sprite in the same place.
 */

using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace UnknownsHalloween {
    public static class HalloweenCorpse {

        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo("[Halloween] corpse: " + s);

        // ==================== the costume ====================
        //
        // A hat like the other costumes, but in place of painted frames it draws the game's own corpse
        // sprite (hw_corpse.png, rendered once from the game's "Dead0027" by the probe below) on the
        // hat's front layer, at the spot and scale the game gives a real corpse, and hides the body,
        // skin and visor meanwhile. The hat is adaptive, so the player shader colours the sprite's
        // colour keys exactly like a real corpse of that player.
        // Measured (probe 2026-10-07): corpse renderer at (-0.0384, -0.2504) from the player at
        // renderer scale 0.35, the same scale as the body; pivot (33.5, 77) of 149 x 162 px at 100 ppu.

        internal const string HatName = "Halloween Corpse";
        internal const string FileName = "UC_HW_corpse.png";
        private const string ResName = "hw_corpse.png";
        private static readonly Vector2 Offset = new Vector2(-0.0384f, -0.2504f) / 0.35f;   // in body scale units
        private static Sprite sprite;
        private static bool spriteTried;

        /// <summary>The hat entry for the registration (null when the image is missing).</summary>
        internal static TheOtherRoles.Modules.CustomHats.CustomHat MakeHat(Func<string, string, bool> extract) {
            if (!extract(ResName, FileName)) return null;
            return new TheOtherRoles.Modules.CustomHats.CustomHat {
                Name = HatName, Author = "DaUnknown-0", Package = "Unknown's Halloween",
                Resource = FileName, Adaptive = true, Bounce = false, Behind = false,
            };
        }

        private static Sprite CorpseSprite() {
            if (sprite != null || spriteTried) return sprite;
            spriteTried = true;
            try {
                using var stream = System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream("UnknownsHalloween.Resources.hats." + ResName);
                if (stream == null) return null;
                var data = new byte[stream.Length];
                int read = 0;
                while (read < data.Length) { int n = stream.Read(data, read, data.Length - read); if (n <= 0) break; read += n; }
                var tex = new Texture2D(2, 2, TextureFormat.ARGB32, false);
                if (!ImageConversion.LoadImage(tex, data, false)) return null;
                tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(33.5f / tex.width, 77f / tex.height), 100f);
                sprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            } catch (Exception e) { Log("sprite load failed: " + e.Message); }
            return sprite;
        }

        // What was hidden or moved on one player, to put back when the costume comes off.
        private sealed class Hidden {
            public Transform Body, Skin, Visor, Front;
            public Vector3 BodyScale, SkinScale, VisorScale, FrontScale, FrontPos;
            public float Lossy;
        }
        private static readonly Dictionary<int, Hidden> hidden = new();
        private static readonly Dictionary<int, (CosmeticsLayer co, PlayerControl pc)> owners = new();

        private static (CosmeticsLayer co, PlayerControl pc) OwnerOf(HatParent hat) {
            int id = hat.GetInstanceID();
            if (owners.TryGetValue(id, out var e) && e.co != null) return e;
            CosmeticsLayer co = null; PlayerControl pc = null;
            try { co = hat.GetComponentInParent<CosmeticsLayer>(); pc = hat.GetComponentInParent<PlayerControl>(); } catch { }
            if (owners.Count > 256) owners.Clear();
            owners[id] = (co, pc);
            return (co, pc);
        }

        private static void Scale0(Transform t) { if (t != null && t.localScale != Vector3.zero) t.localScale = Vector3.zero; }

        private static void Restore(int id) {
            if (!hidden.TryGetValue(id, out var h)) return;
            hidden.Remove(id);
            try {
                if (h.Body != null) h.Body.localScale = h.BodyScale;
                if (h.Skin != null) h.Skin.localScale = h.SkinScale;
                if (h.Visor != null) h.Visor.localScale = h.VisorScale;
                if (h.Front != null) { h.Front.localScale = h.FrontScale; h.Front.localPosition = h.FrontPos; }
            } catch { }
        }

        /// <summary>
        /// Called from the hat update. True when this hat is the corpse costume (handled here);
        /// for any other hat it puts a previously hidden body back and returns false.
        /// </summary>
        internal static bool Handle(HatParent hat) {
            if (hat == null) return false;
            var (co, pc) = OwnerOf(hat);
            int id = co != null ? co.GetInstanceID() : 0;
            bool isCorpse = hat.Hat != null && hat.Hat.name == HatName;
            if (!isCorpse) { if (hidden.Count > 0 && id != 0) Restore(id); return false; }
            if (co == null) return true;     // a hat chip without a crewmate: the plain image is fine

            var front = hat.FrontLayer;
            SpriteRenderer body = null;
            try { body = co.currentBodySprite != null ? co.currentBodySprite.BodySprite : null; } catch { }
            bool dead = false, away = false;
            try {
                if (pc != null) {
                    dead = pc.Data != null && pc.Data.IsDead;
                    away = pc.onLadder || pc.inVent || pc.inMovingPlat;
                }
            } catch { }
            if (front == null || body == null || dead || away || co.CurrentBodyType != PlayerBodyTypes.Normal) {
                // ghost, ladder, vent, platform, horse/long mode: the plain crewmate, no corpse
                Restore(id);
                if (front != null && dead) Scale0(front.transform);
                return true;
            }

            if (!hidden.TryGetValue(id, out var h)) {
                h = new Hidden {
                    Body = body.transform, BodyScale = body.transform.localScale,
                    Front = front.transform, FrontScale = front.transform.localScale, FrontPos = front.transform.localPosition,
                };
                try { if (co.skin != null) { h.Skin = co.skin.transform; h.SkinScale = h.Skin.localScale; } } catch { }
                try { if (co.visor != null) { h.Visor = co.visor.transform; h.VisorScale = h.Visor.localScale; } } catch { }
                var bp = body.transform.parent;
                h.Lossy = Mathf.Abs((bp != null ? bp.lossyScale.x : 1f) * h.BodyScale.x);
                if (hidden.Count > 256) hidden.Clear();
                hidden[id] = h;
            }
            Scale0(h.Body); Scale0(h.Skin); Scale0(h.Visor);

            var sp = CorpseSprite();
            if (sp == null) return true;
            if (front.sprite != sp) front.sprite = sp;
            bool flip = body.flipX;
            front.flipX = flip;
            var par = front.transform.parent;
            float pl = par != null ? Mathf.Abs(par.lossyScale.x) : 1f;
            float k = pl > 1e-5f ? h.Lossy / pl : 1f;
            var want = new Vector3(k, k, 1f);
            if (front.transform.localScale != want) front.transform.localScale = want;
            var b = body.transform.position;
            float ox = (flip ? -Offset.x : Offset.x) * h.Lossy, oy = Offset.y * h.Lossy;
            front.transform.position = new Vector3(b.x + ox, b.y + oy, front.transform.position.z);
            return true;
        }

        internal static void ResetAll() {
            foreach (var id in new List<int>(hidden.Keys)) Restore(id);
            owners.Clear();
        }


        private static string Describe(SpriteRenderer sr, Vector3 origin) {
            if (sr == null) return "null";
            var sp = sr.sprite;
            string s = FormattableString.Invariant(
                $"'{sr.name}' en {sr.enabled} pos {(sr.transform.position - origin).x:F4} {(sr.transform.position - origin).y:F4} local {sr.transform.localPosition.x:F4} {sr.transform.localPosition.y:F4} lossy {sr.transform.lossyScale.x:F4} {sr.transform.lossyScale.y:F4} flip {sr.flipX} order {sr.sortingOrder} mat '{sr.sharedMaterial?.name}' shader '{sr.sharedMaterial?.shader?.name}'");
            if (sp != null)
                s += FormattableString.Invariant(
                    $" sprite '{sp.name}' rect {sp.rect.x:F0} {sp.rect.y:F0} {sp.rect.width:F0} {sp.rect.height:F0} texRect {sp.textureRect.x:F0} {sp.textureRect.y:F0} pivot {sp.pivot.x:F2} {sp.pivot.y:F2} ppu {sp.pixelsPerUnit:F2} tex '{sp.texture?.name}' {sp.texture?.width}x{sp.texture?.height} packed {sp.packed}");
            return s;
        }

        // The sprite's raw pixels (the colour-key channels the player shader reads), rendered with an
        // own camera and the plain sprite shader: the game's textures are not CPU-readable, and a
        // blit + textureRect crop came out shifted.
        internal static void DumpSprite(Sprite sp, string file) {
            if (sp == null) return;
            int w = Mathf.CeilToInt(sp.rect.width), h = Mathf.CeilToInt(sp.rect.height);
            const int Layer = 31;
            var root = new Vector3(5000f, 5000f, 0f);
            GameObject go = null, camGo = null;
            var rt = new RenderTexture(w, h, 16, RenderTextureFormat.ARGB32);
            var prev = RenderTexture.active;
            try {
                go = new GameObject("CorpseProbeSprite") { layer = Layer };
                go.transform.position = root;
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = sp;
                sr.sharedMaterial = new Material(Shader.Find("Sprites/Default"));
                float ppu = sp.pixelsPerUnit;
                var center = root + new Vector3((w / 2f - sp.pivot.x) / ppu, (h / 2f - sp.pivot.y) / ppu, 0f);
                camGo = new GameObject("CorpseProbeCam");
                camGo.transform.position = center + new Vector3(0f, 0f, -10f);
                var cam = camGo.AddComponent<Camera>();
                cam.orthographic = true;
                cam.orthographicSize = h / ppu / 2f;
                cam.aspect = (float)w / h;
                cam.cullingMask = 1 << Layer;
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = new Color(0f, 0f, 0f, 0f);
                cam.targetTexture = rt;
                cam.enabled = false;
                cam.Render();
                RenderTexture.active = rt;
                var outTex = new Texture2D(w, h, TextureFormat.RGBA32, false);
                outTex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
                outTex.Apply();
                File.WriteAllBytes(file, ImageConversion.EncodeToPNG(outTex));
                UnityEngine.Object.Destroy(outTex);
                Log($"dumped '{sp.name}' {w}x{h} -> {file}");
            } catch (Exception e) {
                Log($"dump '{sp.name}' failed: {e.Message}");
            } finally {
                RenderTexture.active = prev;
                if (camGo != null) { camGo.GetComponent<Camera>().targetTexture = null; UnityEngine.Object.Destroy(camGo); }
                if (go != null) UnityEngine.Object.Destroy(go);
                rt.Release();
            }
        }

        internal static void ProbeSteps(PlayerControl lp, List<(float, Action)> steps, string dir, Action<string> shot) {
            void Add(float wait, Action act) => steps.Add((wait, act));
            PlayerControl victim = null;
            Vector3 victimPos = Vector3.zero;
            Add(0.5f, () => {
                foreach (var p in PlayerControl.AllPlayerControls) if (p != null && p != lp) { victim = p; break; }
                if (victim == null) { Log("no dummy"); return; }
                // next to the local player, so the camera sees both
                victim.NetTransform.SnapTo((Vector2)lp.transform.position + new Vector2(1.2f, 0f));
            });
            Add(0.8f, () => {
                if (victim == null) return;
                victimPos = victim.transform.position;
                var body = victim.cosmetics.currentBodySprite.BodySprite;
                Log($"victim alive: player scale {victim.transform.lossyScale.x:F4}, body {Describe(body, victimPos)}");
                Log($"victim cosmetics local {victim.cosmetics.transform.localPosition.x:F4} {victim.cosmetics.transform.localPosition.y:F4}, skin {Describe(victim.cosmetics.skin?.layer, victimPos)}");
                DumpSprite(body.sprite, Path.Combine(dir, "raw_body_idle.png"));
                shot("corpse_before");
                victim.MurderPlayer(victim, MurderResultFlags.Succeeded);
            });
            Add(0.3f, () => {
                foreach (var db in UnityEngine.Object.FindObjectsOfType<DeadBody>())
                    foreach (var r in db.bodyRenderers) Log($"t0.3 {Describe(r, victimPos)}");
            });
            Add(2.5f, () => {
                foreach (var db in UnityEngine.Object.FindObjectsOfType<DeadBody>()) {
                    Log(FormattableString.Invariant($"dead body {db.name} at {(db.transform.position - victimPos).x:F4} {(db.transform.position - victimPos).y:F4} scale {db.transform.lossyScale.x:F4} parent {db.ParentId}"));
                    foreach (var r in db.bodyRenderers) {
                        Log($"t2.8 {Describe(r, victimPos)}");
                        if (r != null && r.sprite != null) DumpSprite(r.sprite, Path.Combine(dir, "raw_corpse_" + r.name + ".png"));
                    }
                    if (db.bloodSplatter != null) Log($"blood {Describe(db.bloodSplatter, victimPos)}");
                }
                try {
                    var pre = GameManager.Instance.DeadBodyPrefab;
                    foreach (var r in pre.bodyRenderers) Log($"prefab {Describe(r, Vector3.zero)}");
                } catch (Exception e) { Log("prefab: " + e.Message); }
                shot("corpse_after");
            });
            // the costume next to the real corpse: standing, mirrored, taken off again
            Add(0.5f, () => { try { lp.RpcSetHat(UnknownsCollection.UCHats.HatIdOf(HatName)); } catch (Exception e) { Log("hat: " + e.Message); } });
            Add(1.5f, () => shot("costume_idle"));
            Add(0.5f, () => { try { lp.MyPhysics.FlipX = true; } catch (Exception e) { Log("flip: " + e.Message); } });
            Add(1.0f, () => shot("costume_flip"));
            Add(0.5f, () => { try { lp.MyPhysics.FlipX = false; lp.RpcSetHat("hat_NoHat"); } catch { } });
            Add(1.0f, () => shot("costume_off"));
            Add(0.6f, () => shot("flush"));
        }
    }
}
