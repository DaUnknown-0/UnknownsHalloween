// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Costume ghosts (idea E2, option 2101 "Costume Ghosts", see HwLook.cs).
 *
 * Whoever dies wearing one of the Halloween costumes keeps the costume's prop as a ghost: Pumpkin Head a glowing
 * lantern head, Reaper hood and scythe, Vampire bat wings, Medusa the snakes, Spider the eight legs, Freddy hat and
 * glove, Jason the mask, Ghostface hood and mask, Xenomorph the dome. The prop (Resources/hw2026/ghosts/
 * ghostprop_<key>.png, 300 x 375, half transparent) is drawn in the costume hat's coordinate system (pivot 0.53/0.575,
 * pixelsPerUnit = width * 0.375, like HalloweenCostumes.LoadHatSprite) as a child of the ghost's HatParent, so it
 * follows the ghost's float and facing exactly like a hat would.
 *
 * Only the dead see it: the prop shows only while the LOCAL player is dead and the ghost itself is visible (the game
 * hides ghosts from the living anyway; this check keeps it that way even for a renderer the game does not know).
 * The costume is taken from the outfit worn at the moment of death (current cosmetics hat, else the default outfit),
 * so a camouflaged or morphed death shows what the others saw. Pictures are loaded on the first death that needs one
 * (32-bit process), one texture per costume, kept for the rest of the session (about 0.45 MB each).
 * Costumes without a prop picture (Thing, Predator, Sadako, BVB Fan, Angel Ghost) keep the plain ghost.
 */

using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HwLookGhosts {
        private const string Folder = "ghosts";
        private static readonly HashSet<string> Props = new() { "pumpkin", "reaper", "vampire", "medusa", "spider", "freddy", "jason", "ghostface", "xenomorph" };

        private sealed class Ghost { public string Key; public SpriteRenderer R; }
        private static readonly Dictionary<byte, Ghost> ghosts = new();
        private static readonly HashSet<byte> alive = new();
        private static readonly Dictionary<string, Sprite> sprites = new();
        private static float nextScan;

        internal static int DiagShown;
        internal static string DiagState() {
            var parts = new List<string>();
            foreach (var kv in ghosts) parts.Add($"{kv.Key}={kv.Value.Key}{(kv.Value.R != null && kv.Value.R.enabled ? "(shown)" : "")}");
            return $"tracked [{string.Join(", ", parts)}], shown {DiagShown}, textures {sprites.Count}";
        }

        internal static void Reset() {
            foreach (var g in ghosts.Values) {
                try { if (g.R != null) UnityEngine.Object.Destroy(g.R.gameObject); } catch { }
            }
            ghosts.Clear();
            alive.Clear();
            DiagShown = 0;
        }

        private static string WornHat(PlayerControl p) {
            try { var h = p.cosmetics != null && p.cosmetics.hat != null ? p.cosmetics.hat.Hat : null; if (h != null) return h.ProdId; } catch { }
            try { return p.Data.DefaultOutfit.HatId; } catch { return null; }
        }

        private static Sprite PropSprite(string key) {
            if (sprites.TryGetValue(key, out var s) && s != null) return s;
            var tex = HwArt.LoadTexture(Folder, "ghostprop_" + key + ".png");
            if (tex == null) { sprites[key] = null; return null; }
            s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.53f, 0.575f), tex.width * 0.375f);
            s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            sprites[key] = s;
            HwLook.Log($"ghost prop {key} loaded ({tex.width}x{tex.height})");
            return s;
        }

        /// <summary>From the UC tick (HudManager.Update).</summary>
        internal static void Tick() {
            if (!HwMechanics.InRound()) { if (ghosts.Count > 0 || alive.Count > 0) Reset(); return; }
            bool on = HwLook.GhostsEnabled;
            // deaths: alive -> dead transitions, the costume at that moment
            if (Time.time >= nextScan) {
                nextScan = Time.time + 0.2f;
                foreach (var p in PlayerControl.AllPlayerControls.ToArray()) {
                    if (p == null || p.Data == null) continue;
                    byte id = p.PlayerId;
                    if (!p.Data.IsDead) { alive.Add(id); if (ghosts.ContainsKey(id)) Drop(id); continue; }
                    if (!alive.Remove(id) || ghosts.ContainsKey(id)) continue;
                    string key = HalloweenCostumes.CostumeKeyOfHat(WornHat(p));
                    if (key == null || !Props.Contains(key)) continue;
                    ghosts[id] = new Ghost { Key = key };
                    HwLook.Log($"{p.Data.PlayerName} died as {key}");
                }
            }
            if (ghosts.Count == 0) { DiagShown = 0; return; }
            var me = PlayerControl.LocalPlayer;
            bool iAmDead = me != null && me.Data != null && me.Data.IsDead;
            bool meeting = HwMechanics.InMeeting();
            int shown = 0;
            foreach (var kv in ghosts) {
                var g = kv.Value;
                PlayerControl p = null;
                try { p = Helpers(kv.Key); } catch { }
                bool show = on && iAmDead && !meeting && p != null && p.Data != null && p.Data.IsDead && p.Visible && !p.inVent;
                if (show) show = Ensure(p, g);
                if (g.R != null) {
                    if (g.R.enabled != show) g.R.enabled = show;
                    if (show) { Follow(p, g.R); shown++; }
                }
            }
            DiagShown = shown;
        }

        private static PlayerControl Helpers(byte id) {
            foreach (var p in PlayerControl.AllPlayerControls.ToArray()) if (p != null && p.PlayerId == id) return p;
            return null;
        }

        private static void Drop(byte id) {
            if (ghosts.TryGetValue(id, out var g) && g.R != null) { try { UnityEngine.Object.Destroy(g.R.gameObject); } catch { } }
            ghosts.Remove(id);
        }

        private static bool Ensure(PlayerControl p, Ghost g) {
            if (g.R != null) return true;
            var hat = p.cosmetics != null ? p.cosmetics.hat : null;
            if (hat == null) return false;
            var sprite = PropSprite(g.Key);
            if (sprite == null) return false;
            var go = new GameObject("HwGhostProp_" + g.Key);
            go.transform.SetParent(hat.transform, false);
            go.transform.localPosition = new Vector3(0f, 0f, -0.0003f);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            var mat = HwLook.SpriteMaterial;
            if (mat != null) sr.sharedMaterial = mat;
            g.R = sr;
            return true;
        }

        // Layer, sorting and facing from the hat's front layer (or the ghost body), every frame.
        private static void Follow(PlayerControl p, SpriteRenderer sr) {
            SpriteRenderer refR = null;
            try { refR = p.cosmetics.hat.FrontLayer; } catch { }
            SpriteRenderer body = null;
            try { body = p.cosmetics.currentBodySprite.BodySprite; } catch { }
            var src = refR != null && refR.gameObject.activeInHierarchy ? refR : body;
            if (src == null) return;
            if (sr.gameObject.layer != src.gameObject.layer) sr.gameObject.layer = src.gameObject.layer;
            sr.sortingLayerID = src.sortingLayerID;
            sr.sortingOrder = src.sortingOrder + 1;
            bool flip = body != null ? body.flipX : src.flipX;
            if (sr.flipX != flip) sr.flipX = flip;
        }
    }
}
