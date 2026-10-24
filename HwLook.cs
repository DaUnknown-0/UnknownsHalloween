// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Halloween look (2026-10-20, ideas D3, E2, E3). Three purely cosmetic features, every client draws them on its own:
 *
 *   - HwLookMeeting.cs    meeting room in Halloween dress (cobwebs, flickering candles, vote tokens as little ghosts,
 *                         a bat on Skip) and Halloween exile lines on the original maps.
 *   - HwLookEndscreen.cs  end screen backdrop (impostor win: moon night, crew win: first morning light, neutral win:
 *                         cemetery gate) with falling leaves and candies. TOR's win texts stay as they are.
 *   - HwLookGhosts.cs     costume ghosts: whoever dies in a Halloween costume haunts on with the costume's prop on the
 *                         standard ghost. Only the dead see it (ghosts are invisible to the living anyway).
 *
 * Options 2100-2119 (ID-Registry.md): 2100 "Halloween Look" (meeting + end screen), 2101 "Costume Ghosts".
 * Both default ON: this is a Halloween mod, both are cosmetic only (no information, no balance), and a host who
 * does not want them switches them off. The host's value counts for everybody (TOR option sync); nothing here sends
 * a message, so the reserved module byte 243 on UC's channel 230 stays unused.
 *
 * Artwork: Resources/hw2026/<meeting|endscreen|ghosts>/ (embedded, loaded on first use through HwArt).
 */

using System;
using HarmonyLib;
using TheOtherRoles;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HwLook {
        internal const string LogPrefix = "[Halloween/Look]";
        internal static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");
        internal static void Warn(string s) => HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {s}");

        internal static CustomOption LookOption, GhostOption;

        // self test: UC_HALLOWEEN_DIAG = meeting | endscreen | ghosts | hwlook (all three)
        internal static readonly string DiagMode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        internal static bool DiagOn => DiagMode == "meeting" || DiagMode.StartsWith("endscreen") || DiagMode == "ghosts" || DiagMode == "hwlook" || DiagMode == "guessspell";

        private static bool On(CustomOption o) {
            try { return o == null || o.getBool(); } catch { return true; }
        }

        internal static bool LookEnabled => DiagOn || On(LookOption);
        internal static bool GhostsEnabled => DiagOn || On(GhostOption);

        private static bool booted;
        private static void Boot() {
            if (booted) return;
            booted = true;
            try {
                var g = CustomOption.CustomOptionType.General;
                LookOption = CustomOption.Create(2100, g, "Halloween Look (Meeting, End Screen)", true, null, true, null, "Halloween Look");
                GhostOption = CustomOption.Create(2101, g, "Costume Ghosts", true, null, false);
                HwGuessSpell.Option = CustomOption.Create(2102, g, "Guesser Spell Sound", true, null, false);
                UnknownsCollection.UCFx.RegisterTick(Tick);
                Log("registered (meeting room, end screen, costume ghosts).");
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} registration failed: {e}");
            }
        }

        private static void Tick() {
            try { HwLookGhosts.Tick(); } catch (Exception e) { Warn($"ghost tick: {e.Message}"); }
            try { HwLookMeeting.ExileTick(); } catch (Exception e) { Warn($"exile tick: {e.Message}"); }
            try { HwLookDiag.Tick(); } catch (Exception e) { Warn($"diag tick: {e.Message}"); }
        }

        internal static void FullReset() {
            try { HwLookGhosts.Reset(); } catch (Exception e) { Warn($"ghost reset: {e.Message}"); }
            try { HwLookMeeting.Reset(); } catch (Exception e) { Warn($"meeting reset: {e.Message}"); }
        }

        [HarmonyPatch(typeof(RPCProcedure), nameof(RPCProcedure.resetVariables))]
        static class ResetPatch {
            static bool Prepare() { Boot(); return true; }
            public static void Postfix() => FullReset();
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class LobbyResetPatch {
            public static void Postfix() => FullReset();
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameEnd))]
        static class GameEndResetPatch {
            public static void Postfix() => FullReset();
        }

        // ---- shared helpers ----

        internal static bool? LangOverride;
        internal static bool De() {
            if (LangOverride.HasValue) return LangOverride.Value;
            try { return UnknownsCollection.UCLocalization.ActiveCode == "german"; } catch { return false; }
        }

        /// <summary>A plain sprite renderer (default sprite material) as a child of <paramref name="parent"/>.</summary>
        internal static SpriteRenderer NewRenderer(string name, Transform parent, Sprite sprite, Vector3 localPos, int layer) {
            var go = new GameObject(name) { layer = layer };
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            return sr;
        }

        private static Material spriteMat;
        /// <summary>Unity's default sprite material (vertex colour tint, respects sprite masks).</summary>
        internal static Material SpriteMaterial {
            get {
                if (spriteMat != null) return spriteMat;
                try {
                    var sh = Shader.Find("Sprites/Default");
                    if (sh != null) {
                        spriteMat = new Material(sh) { name = "HwLookSprite" };
                        spriteMat.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                    }
                } catch { }
                return spriteMat;
            }
        }
    }
}
