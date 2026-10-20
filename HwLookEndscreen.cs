// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Halloween end screen (idea E3, option 2100 "Halloween Look", see HwLook.cs).
 *
 * EndGameManager.SetEverythingUp postfix (after TOR's postfix that rebuilds the winner figures and the bonus line):
 * a full-screen backdrop behind everything, picked from the result:
 *   impostor win  (TOR win condition Default + an impostor game-over reason)        end_bg_impostor.png, moon night
 *   crew win      (Default + a crew reason, or "Lovers And Crewmates")              end_bg_crew.png, first morning light
 *   neutral win   (everything else: Jester, Jackal, Arsonist, Vulture, Lovers, UC and Halloween win reasons)
 *                                                                                   end_bg_neutral.png, cemetery gate
 * Leaves and candies fall in front of the backdrop and behind the figures (a Reactor coroutine, ends with the scene).
 * The game's dark background layer (and a star field, where there is one) is switched off while the backdrop stands; TOR's texts, the bar and the figures are not
 * touched. The three backdrops (0.4 to 0.65 MB each as PNG, 8 MB as texture) are embedded and decoded only when the
 * end screen opens; the texture is released when the end screen goes away.
 */

using System;
using System.Collections;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HwLookEndscreen {
        private const string Folder = "endscreen";
        internal enum Kind { Impostor, Crew, Neutral }


        internal static Kind LastKind;
        internal static string LastInfo = "";
        internal static int DiagHidden;

        // SetEverythingUp, not Start: Start is a tiny Il2Cpp method and a detour on it took the game down on the
        // scene change (self test 2026-10-20, the dedup trap). TOR and Zombie Outbreak use SetEverythingUp as well;
        // Priority.Low runs after TOR's postfix that rebuilds the winner figures.
        [HarmonyPatch(typeof(EndGameManager), nameof(EndGameManager.SetEverythingUp))]
        static class StartPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix(EndGameManager __instance) {
                try {
                    if (!HwLook.LookEnabled || __instance == null) return;
                    Apply(__instance, Classify());
                } catch (Exception e) { HwLook.Warn($"end screen failed: {e}"); }
            }
        }

        internal static Kind Classify() {
            int reason = -1, wc = -1;
            try { reason = (int)TheOtherRoles.Patches.OnGameEndPatch.gameOverReason; } catch { }
            wc = HalloweenModeRules.GetWinCondition();
            Kind k;
            bool impReason = reason == (int)GameOverReason.ImpostorByKill || reason == (int)GameOverReason.ImpostorBySabotage
                || reason == (int)GameOverReason.ImpostorByVote || reason == (int)GameOverReason.ImpostorDisconnect;
            bool crewReason = reason == (int)GameOverReason.HumansByTask || reason == (int)GameOverReason.HumansByVote
                || reason == (int)GameOverReason.HumansDisconnect;
            if (wc == 0 && impReason) k = Kind.Impostor;
            else if ((wc == 0 && crewReason) || wc == 1) k = Kind.Crew;       // 1 = LoversTeamWin ("Lovers And Crewmates")
            else if (wc == 0 && reason == -1) k = Kind.Crew;
            else k = Kind.Neutral;
            LastInfo = $"reason {reason}, win condition {wc}";
            return k;
        }

        private static GameObject current;
        private static Texture2D currentTex;

        internal static void Apply(EndGameManager egm, Kind kind) {
            Clear();
            var cam = Camera.main;
            if (cam == null) return;
            LastKind = kind;
            string file = kind switch { Kind.Impostor => "end_bg_impostor.png", Kind.Crew => "end_bg_crew.png", _ => "end_bg_neutral.png" };
            var tex = HwArt.LoadTexture(Folder, file);
            if (tex == null) { HwLook.Warn($"{file} missing"); return; }
            currentTex = tex;
            int layer = egm.gameObject.layer;
            var root = new GameObject("HwLookEnd") { layer = layer };
            current = root;
            // on the camera axis, far behind everything of the end screen (figures sit between -8 and 0 local z)
            float zBack = egm.transform.position.z + 40f;
            float camZ = cam.transform.position.z;
            if (cam.farClipPlane > 0f && zBack - camZ > cam.farClipPlane * 0.9f) zBack = camZ + cam.farClipPlane * 0.9f;
            root.transform.position = new Vector3(cam.transform.position.x, cam.transform.position.y, zBack);
            root.transform.SetParent(egm.transform, true);                 // goes away with the end screen

            float viewH = cam.orthographicSize * 2f, viewW = viewH * cam.aspect;
            // cover the view (crop the longer side), plus a margin so a slight camera shake shows no edge
            float scale = Mathf.Max(viewW / (tex.width / 100f), viewH / (tex.height / 100f)) * 1.02f;
            var bgSprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), 100f);
            bgSprite.hideFlags |= HideFlags.HideAndDontSave;
            var bg = HwLook.NewRenderer("Backdrop", root.transform, bgSprite, Vector3.zero, layer);
            bg.transform.localScale = new Vector3(scale, scale, 1f);

            // the game's star field and its glow go dark behind the backdrop; the bar behind the title stays
            DiagHidden = 0;
            try {
                foreach (var r in egm.GetComponentsInChildren<Renderer>(true)) {
                    if (r == null || r.transform.IsChildOf(root.transform)) continue;
                    if (egm.BackgroundBar != null && r.Pointer == egm.BackgroundBar.Pointer) continue;
                    var ps = r.GetComponent<ParticleSystem>();
                    string n = r.gameObject.name.ToLowerInvariant();
                    // BackgroundLayer: the dark full-screen gradient in front of everything behind the figures
                    if (ps != null || n.Contains("star") || n == "backgroundlayer") { r.enabled = false; DiagHidden++; }
                }
                if (egm.Foreground != null) { egm.Foreground.enabled = false; DiagHidden++; }
            } catch (Exception e) { HwLook.Warn($"star field: {e.Message}"); }

            // falling leaves and candies, in front of the backdrop, behind the figures
            var parts = new List<Sprite>();
            for (int i = 1; i <= 4; i++) {
                var l = HwArt.Get(Folder, $"end_leaf_{i}.png", 0.42f, new Vector2(0.5f, 0.5f), null);
                if (l != null) parts.Add(l);
                var c = HwArt.Get(Folder, $"end_candy_{i}.png", 0.36f, new Vector2(0.5f, 0.5f), null);
                if (c != null) parts.Add(c);
            }
            var fall = new GameObject("Falling") { layer = layer };
            fall.transform.SetParent(root.transform, false);
            // between backdrop and figures: world z just behind the end screen's own plane
            fall.transform.position = new Vector3(root.transform.position.x, root.transform.position.y, egm.transform.position.z + 2f);
            var bits = new List<Bit>();
            var rng = new System.Random(1031);
            if (parts.Count > 0) {
                for (int i = 0; i < 26; i++) {
                    var sr = HwLook.NewRenderer("Bit" + i, fall.transform, parts[i % parts.Count], Vector3.zero, layer);
                    var b = new Bit { R = sr };
                    Respawn(b, rng, viewW, viewH, true);
                    bits.Add(b);
                }
            }
            HwLook.Log($"end screen: {kind} ({LastInfo}), backdrop {tex.width}x{tex.height} scale {scale:F3} z {zBack:F1}, cam z {camZ:F1} far {cam.farClipPlane:F0}, hidden {DiagHidden}, falling {bits.Count}");
            Reactor.Utilities.Coroutines.Start(Fall(root, bits, rng, viewW, viewH));
        }

        private sealed class Bit { public SpriteRenderer R; public Vector2 P; public float Vy, Sway, Phase, Spin, Rot, Scale; }

        private static void Respawn(Bit b, System.Random rng, float w, float h, bool anywhere) {
            float R() => (float)rng.NextDouble();
            b.P = new Vector2((R() - 0.5f) * w * 1.05f, anywhere ? (R() - 0.5f) * h : h * 0.5f + 0.3f + R() * 0.6f);
            b.Vy = 0.35f + R() * 0.45f;
            b.Sway = 0.15f + R() * 0.35f;
            b.Phase = R() * 6.28f;
            b.Spin = (R() - 0.5f) * 140f;
            b.Rot = R() * 360f;
            b.Scale = 0.75f + R() * 0.5f;
            b.R.transform.localScale = new Vector3(b.Scale, b.Scale, 1f);
        }

        private static IEnumerator Fall(GameObject root, List<Bit> bits, System.Random rng, float w, float h) {
            while (root != null) {
                float dt = Mathf.Min(Time.deltaTime, 0.05f), t = Time.time;
                foreach (var b in bits) {
                    if (b.R == null) continue;
                    b.P.y -= b.Vy * dt;
                    b.Rot += b.Spin * dt;
                    float x = b.P.x + Mathf.Sin(t * 1.1f + b.Phase) * b.Sway;
                    b.R.transform.localPosition = new Vector3(x, b.P.y, 0f);
                    b.R.transform.localRotation = Quaternion.Euler(0f, 0f, b.Rot);
                    if (b.P.y < -h * 0.5f - 0.5f) Respawn(b, rng, w, h, false);
                }
                yield return null;
            }
            if (currentTex != null && current == null) { try { UnityEngine.Object.Destroy(currentTex); } catch { } currentTex = null; }
        }

        internal static void Clear() {
            try { if (current != null) UnityEngine.Object.Destroy(current); } catch { }
            current = null;
            if (currentTex != null) { try { UnityEngine.Object.Destroy(currentTex); } catch { } currentTex = null; }
        }
    }
}
