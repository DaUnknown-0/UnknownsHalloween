// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Halloween meeting room (idea D3, option 2100 "Halloween Look", see HwLook.cs).
 *
 * MeetingHud.Start postfix: cobwebs in the two top corners of the screen, a candle group with flickering flames at the
 * bottom middle of the tablet (behind the name plates), a bat next to the Skip button. The decoration hangs
 * under the MeetingHud and dies with it. While the results show, the vote tokens (the little crewmates the game
 * "bloops" next to each name) become little ghosts in the voter's colour; the colour is read back from the token's
 * own player material, so anonymous votes stay grey and whatever TOR's PopulateResults did still counts.
 * Everything that moves runs in one Reactor coroutine that ends with the meeting.
 *
 * Exile lines: on the original maps (Skeld, Mira, Polus, Airship, Fungle) the typewriter line of a real ejection gets a
 * Halloween lead ("Rot verschwindet in der Nacht."). With Confirm Ejects on, the line the game and TOR built stays
 * behind the lead (TOR's role text, Jester and Tiebreaker included); with Confirm Ejects off the neutral lead replaces
 * the vanilla "was ejected", so it never says more than the game would. Skips and ties stay as they are (the Void of
 * Unknown's Collection owns those). Atlas maps, the Halloween maps (Atlas keys) and Submerged have their own exile
 * scenes and are left alone. The swap happens on the first tick that sees the new ExileController, before HandleText
 * starts typing (same hook style as HollowmereEject: no detour on ExileController.Begin).
 */

using System;
using System.Collections;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HwLookMeeting {
        private const string Folder = "meeting";

        // diag readouts
        internal static int DiagVoteGhosts, DiagDecorations;
        internal static string LastExileText = "";

        internal static void Reset() {
            seenExile = null;
            exiles = 0;
        }

        // ================================================================ meeting decoration

        [HarmonyPatch(typeof(MeetingHud), nameof(MeetingHud.Start))]
        static class StartPatch {
            [HarmonyPriority(Priority.Low)]
            public static void Postfix(MeetingHud __instance) {
                try {
                    if (!HwLook.LookEnabled || __instance == null) return;
                    Decorate(__instance);
                } catch (Exception e) { HwLook.Warn($"meeting decoration failed: {e}"); }
            }
        }

        private sealed class Flame { public SpriteRenderer R; public float Phase, Speed; public Vector3 Scale; }

        private static void Decorate(MeetingHud hud) {
            var cam = Camera.main;
            if (cam == null) return;
            int layer = hud.gameObject.layer;
            var root = new GameObject("HwLookMeeting") { layer = layer };
            root.transform.SetParent(hud.transform, false);
            root.transform.localPosition = Vector3.zero;

            // Depth: in front of the tablet, behind the player plates' own content does not matter here (corners only);
            // behind the chat (HUD z about -40 and less) so an open chat covers the webs.
            float z = DecorZ(hud);
            Vector3 Local(float vx, float vy) {
                var w = cam.ViewportToWorldPoint(new Vector3(vx, vy, 0f));
                var l = root.transform.InverseTransformPoint(w);
                return new Vector3(l.x, l.y, z);
            }
            float viewH = cam.orthographicSize * 2f;
            float scaleFix = 1f / Mathf.Max(0.0001f, root.transform.lossyScale.y);
            float webW = viewH * 0.22f * scaleFix;

            var tl = HwArt.Get(Folder, "meeting_web_tl.png", webW, new Vector2(0f, 1f), null);
            var tr = HwArt.Get(Folder, "meeting_web_tr.png", webW, new Vector2(1f, 1f), null);
            if (tl != null) { var r = HwLook.NewRenderer("Web_TL", root.transform, tl, Local(0f, 1f), layer); r.color = new Color(1f, 1f, 1f, 0.9f); }
            if (tr != null) { var r = HwLook.NewRenderer("Web_TR", root.transform, tr, Local(1f, 1f), layer); r.color = new Color(1f, 1f, 1f, 0.9f); }

            // candles bottom left, flames on the wicks (wick pixels from the artwork report, image 512 x 256)
            var flames = new List<Flame>();
            float candleW = viewH * 0.25f * scaleFix;
            var candles = HwArt.Get(Folder, "meeting_candles.png", candleW, new Vector2(0.5f, 0f), null);
            var flameFrames = new Sprite[4];
            float ppu = 512f / candleW;
            for (int i = 0; i < 4; i++) flameFrames[i] = HwArt.Get(Folder, $"meeting_flame_{i + 1}.png", 48f / ppu, new Vector2(0.5f, 0.04f), null);
            if (candles != null) {
                var c = HwLook.NewRenderer("Candles", root.transform, candles, CandlePos(hud, root.transform, Local(0.5f, 0.02f)), layer);
                if (flameFrames[0] != null) {
                    int[,] wicks = { { 110, 102 }, { 176, 58 }, { 256, 32 }, { 336, 72 }, { 402, 118 } };
                    for (int k = 0; k < 5; k++) {
                        var pos = new Vector3(wicks[k, 0] / ppu - candleW * 0.5f, (256 - wicks[k, 1]) / ppu, -0.001f);
                        var f = HwLook.NewRenderer("Flame" + k, c.transform, flameFrames[k % 4], pos, layer);
                        flames.Add(new Flame { R = f, Phase = k * 1.37f, Speed = 7f + k * 0.9f, Scale = Vector3.one });
                    }
                }
            }

            // bat next to Skip
            var bat = HwArt.Get(Folder, "skip_bat.png", 0.5f, new Vector2(0f, 0.5f), null);
            SpriteRenderer skipBat = null;
            if (bat != null && hud.SkipVoteButton != null) skipBat = AttachRight(hud.SkipVoteButton.transform, bat, layer, "SkipBat");

            DiagDecorations = (tl != null ? 1 : 0) + (tr != null ? 1 : 0) + (candles != null ? 1 : 0) + flames.Count + (skipBat != null ? 1 : 0);
            HwLook.Log($"meeting dressed: {DiagDecorations} part(s), z {z:F2}, view {viewH:F2}");
            Reactor.Utilities.Coroutines.Start(Animate(hud, root, flames, flameFrames, skipBat, bat));
        }

        /// <summary>Candles: bottom middle of the tablet, behind the name plates (in front of the tablet itself).</summary>
        private static Vector3 CandlePos(MeetingHud hud, Transform root, Vector3 fallback) {
            // The tablet stands centred on the camera (about 85 % of the view height); its lower frame sits at about
            // 8 % of the view. Bounds are not ready yet in Start, so the camera decides. z: a little behind the
            // name plates (plates sit about 0.9 in front of the MeetingHud), in front of the tablet.
            try {
                var cam = Camera.main;
                var w = cam.ViewportToWorldPoint(new Vector3(0.5f, 0.078f, 0f));
                var l = root.InverseTransformPoint(w);
                return new Vector3(l.x, l.y, -0.5f);
            } catch { return fallback; }
        }

        /// <summary>Local z for the corner decoration: just in front of the meeting's glass/background.</summary>
        private static float DecorZ(MeetingHud hud) {
            try {
                if (hud.Glass != null) return hud.transform.InverseTransformPoint(hud.Glass.transform.position).z - 0.5f;
            } catch { }
            return -0.5f;
        }

        /// <summary>A sprite (pivot on its left edge) just right of the widest renderer under <paramref name="t"/>.</summary>
        private static SpriteRenderer AttachRight(Transform t, Sprite sprite, int layer, string name) {
            Bounds? best = null;
            foreach (var r in t.GetComponentsInChildren<SpriteRenderer>(true)) {
                if (r == null || r.sprite == null || !r.gameObject.activeInHierarchy) continue;
                var b = r.bounds;
                if (best == null || b.size.x > best.Value.size.x) best = b;
            }
            Vector3 world = best != null
                ? new Vector3(best.Value.max.x + 0.06f, best.Value.center.y, t.position.z - 0.05f)
                : t.position + new Vector3(0.6f, 0f, -0.05f);
            var sr = HwLook.NewRenderer(name, t, sprite, Vector3.zero, layer);
            sr.transform.position = world;
            var s = t.lossyScale;
            sr.transform.localScale = new Vector3(1f / Mathf.Max(0.0001f, s.x), 1f / Mathf.Max(0.0001f, s.y), 1f);
            return sr;
        }

        private static IEnumerator Animate(MeetingHud hud, GameObject root, List<Flame> flames, Sprite[] frames, SpriteRenderer skipBat, Sprite bat) {
            var swapped = new HashSet<int>();
            float nextScan = 0f;
            DiagVoteGhosts = 0;
            while (hud != null && root != null) {
                float t = Time.time;
                // flames: four frames as a loop, each flame on its own clock, a little flicker in size and light
                for (int i = 0; i < flames.Count; i++) {
                    var f = flames[i];
                    if (f.R == null) continue;
                    int fi = Mathf.FloorToInt(t * f.Speed + f.Phase * 3f) & 3;
                    if (frames[fi] != null && f.R.sprite != frames[fi]) f.R.sprite = frames[fi];
                    float n = Mathf.PerlinNoise(t * 3.1f + f.Phase, f.Phase * 7f);
                    float s = 0.88f + 0.24f * n;
                    f.R.transform.localScale = new Vector3(0.95f + 0.1f * (1f - n), s, 1f);
                    f.R.color = new Color(1f, 1f, 1f, 0.78f + 0.22f * n);
                }
                // the skip bat flaps a little
                if (skipBat != null) skipBat.transform.localRotation = Quaternion.Euler(0f, 0f, Mathf.Sin(t * 2.2f) * 6f);

                if (t >= nextScan) {
                    nextScan = t + 0.1f;
                    try { ScanVotes(hud, swapped); } catch (Exception e) { HwLook.Warn($"vote scan: {e.Message}"); nextScan = t + 2f; }
                }
                yield return null;
            }
        }

        private static readonly int BodyColorId = Shader.PropertyToID("_BodyColor");

        // The tokens are instances of MeetingHud.PlayerVotePrefab under a PlayerVoteArea or under SkippedVoting.
        private static void ScanVotes(MeetingHud hud, HashSet<int> swapped) {
            if (hud.PlayerVotePrefab == null) return;
            var token = hud.PlayerVotePrefab.sprite;
            if (token == null) return;
            var areas = hud.playerStates;
            if (areas == null) return;
            Sprite ghost = null;
            void Check(Transform parent) {
                if (parent == null) return;
                for (int c = 0; c < parent.childCount; c++) {
                    var ch = parent.GetChild(c);
                    if (ch == null) continue;
                    var sr = ch.GetComponent<SpriteRenderer>();
                    if (sr == null || sr.sprite != token) continue;
                    int id = sr.GetInstanceID();
                    if (swapped.Contains(id)) continue;
                    swapped.Add(id);
                    Color body = new Color(0.6f, 0.6f, 0.6f);
                    try { var m = sr.material; if (m != null && m.HasProperty(BodyColorId)) body = m.GetColor(BodyColorId); } catch { }
                    if (ghost == null) ghost = HwArt.Get(Folder, "vote_ghost.png", token.bounds.size.x * 1.1f, new Vector2(0.5f, 0.5f), null);
                    if (ghost == null) return;
                    var mat = HwLook.SpriteMaterial;
                    if (mat == null) return;
                    sr.sharedMaterial = mat;
                    sr.sprite = ghost;
                    sr.color = Brighten(body, sr.color.a);
                    DiagVoteGhosts++;
                }
            }
            foreach (var a in areas) if (a != null) Check(a.transform);
            if (hud.SkippedVoting != null) Check(hud.SkippedVoting.transform);
        }

        // A white ghost tinted with the body colour; very dark colours (black, brown) get a little lift so the face reads.
        private static Color Brighten(Color c, float alpha) {
            float l = 0.299f * c.r + 0.587f * c.g + 0.114f * c.b;
            if (l < 0.22f) c = Color.Lerp(c, Color.white, 0.22f - l);
            c.a = alpha <= 0f ? 1f : alpha;
            return c;
        }

        // ================================================================ exile lines

        private static ExileController seenExile;
        private static int exiles;

        internal static void ExileTick() {
            var ec = ExileController.Instance;
            if (ec == null) { seenExile = null; return; }
            if (ec == seenExile) return;
            seenExile = ec;
            if (!HwLook.LookEnabled) return;
            try { Rewrite(ec); } catch (Exception e) { HwLook.Warn($"exile line failed: {e.Message}"); }
        }

        private static string MapKind(ExileController ec) {
            if (ec.TryCast<AirshipExileController>() != null) return "airship";
            if (ec.TryCast<PbExileController>() != null) return "polus";
            if (ec.TryCast<MiraExileController>() != null) return "mira";
            if (ec.TryCast<FungleExileController>() != null) return "fungle";
            if (ec.TryCast<SkeldExileController>() != null) return "skeld";
            return null;                                   // Submerged and anything else with its own controller
        }

        private static void Rewrite(ExileController ec) {
            var init = ec.initData;
            if (init == null || init.networkedPlayer == null) return;          // skip or tie
            if (HwMechanics.AtlasMap() != null) return;                        // Atlas and Halloween maps: own scenes
            try { if (AppDomain.CurrentDomain.GetData("UnknownsCollection.VoidScene") is bool b && b) return; } catch { }
            string kind = MapKind(ec);
            if (kind == null) return;
            string name = null;
            try { name = init.outfit != null ? init.outfit.PlayerName : null; } catch { }
            if (string.IsNullOrEmpty(name)) name = init.networkedPlayer.PlayerName;
            int game = 0;
            try { game = AmongUsClient.Instance.GameId; } catch { }
            int seed = unchecked(game * 31 + init.networkedPlayer.PlayerId * 977 + exiles * 7919);
            exiles++;
            string lead = string.Format(PickLead(kind, seed), name);
            string before = ec.completeString ?? "";
            string after = init.confirmImpostor && before.Length > 0 ? lead + " " + before : lead;
            ec.completeString = after;
            LastExileText = after;
            HwLook.Log($"exile line ({kind}, confirm {init.confirmImpostor}): \"{after}\"");
        }

        private static readonly string[] GenericDe = {
            "{0} verschwindet in der Nacht.",
            "Die Geister holen {0}.",
            "{0} spukt ab jetzt woanders.",
            "Der Nebel verschluckt {0}.",
        };
        private static readonly string[] GenericEn = {
            "{0} vanishes into the night.",
            "The ghosts take {0}.",
            "{0} haunts somewhere else now.",
            "The fog swallows {0}.",
        };

        private static string MapLead(string kind, bool de) => kind switch {
            "skeld" => de ? "{0} treibt hinaus in die Sternennacht." : "{0} drifts off into the starry night.",
            "mira" => de ? "{0} fällt durch die Wolken in die Nacht." : "{0} falls through the clouds into the night.",
            "polus" => de ? "{0} versinkt im Hexenkessel." : "{0} sinks into the witch's cauldron.",
            "airship" => de ? "{0} stürzt in die mondlose Tiefe." : "{0} plunges into the moonless deep.",
            "fungle" => de ? "{0} verschwindet im Spukwald." : "{0} disappears into the haunted woods.",
            _ => null,
        };

        private static string PickLead(string kind, int seed) {
            bool de = HwLook.De();
            var pool = de ? GenericDe : GenericEn;
            var rng = new System.Random(seed);
            int i = rng.Next(pool.Length + 1);
            return i == pool.Length ? (MapLead(kind, de) ?? pool[0]) : pool[i];
        }
    }
}
