// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * HalloweenGameSkin - the game's own menu sprites for HalloweenUI (User 2026-11-13: the menus have to really look like
 * Among Us). A copy of the lookup in TOR - Forgotten Fixes' GameUI.cs, because this mod must not depend on it: the
 * sprites of the settings window are found by name among the loaded ones and pinned (DontUnloadUnusedAsset) when a
 * lobby is up, so a menu opened in a round (Trick or Treat) still has them. Missing ones: HalloweenUI draws its own.
 */

using System;
using System.Collections.Generic;
using HarmonyLib;
using Il2CppInterop.Runtime;
using UnityEngine;

namespace UnknownsHalloween {

    internal static class HalloweenGameSkin {
        internal static readonly Color TabText = new Color32(0x10, 0x58, 0x4B, 0xFF);

        private static readonly string[] Wanted = {
            "IMAGE-PanelBG", "IMAGE-TitleDivider", "IMAGE-FieldCube", "IMAGE-LabelCube", "CTAInactive", "CTAActive",
            "BUTTON-ExitStandard", "BUTTON-ExitHover", "IMAGE-Subheader", "BUTTON-CheckboxInactive",
        };
        private static readonly Dictionary<string, Sprite> sprites = new();
        private static float searchedAt = -100f;

        internal static Sprite Sprite(string name) {
            if (sprites.TryGetValue(name, out var s) && s != null) return s;
            Search();
            return sprites.TryGetValue(name, out s) ? s : null;
        }

        internal static bool Ready => Sprite("IMAGE-FieldCube") != null && Sprite("CTAInactive") != null;

        [HarmonyPatch(typeof(LobbyBehaviour), nameof(LobbyBehaviour.Start))]
        private static class LobbyWarm {
            public static void Postfix() { try { searchedAt = -100f; Search(); } catch { } }
        }

        private static void Search() {
            if (sprites.Count >= Wanted.Length || Time.realtimeSinceStartup - searchedAt < 2f) return;
            searchedAt = Time.realtimeSinceStartup;
            try {
                var want = new HashSet<string>(Wanted);
                foreach (var o in Resources.FindObjectsOfTypeAll(Il2CppType.Of<Sprite>())) {
                    var sp = o.TryCast<Sprite>();
                    if (sp == null || !want.Contains(sp.name) || sprites.ContainsKey(sp.name)) continue;
                    sp.hideFlags |= HideFlags.DontUnloadUnusedAsset;
                    if (sp.texture != null) sp.texture.hideFlags |= HideFlags.DontUnloadUnusedAsset;
                    sprites[sp.name] = sp;
                }
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"[HalloweenGameSkin] sprite search failed: {e.Message}"); }
        }
    }
}
