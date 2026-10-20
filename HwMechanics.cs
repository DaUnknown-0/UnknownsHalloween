// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * Shared plumbing of three Halloween mechanics (2026-10-20, ideas A6, C1, C2):
 *
 *   - HwScaredyCat.cs     Scaredy-Cat (crew modifier): sees a body, screams, everybody reads the room.
 *   - HwMirrors.cs        Haunted Mirrors: a few mirrors on the walls show every player as themselves.
 *   - HwPhantomParade.cs  Phantom Parade (impostor sabotage): look-alike phantoms walk the map for a while.
 *
 * One RPC module byte for all three: 241 on UC's channel 230 (the Banshee is 237, Trick or Treat 238).
 *   Sub 0 scaredy set      host -> all   [playerId]  (255 = taken away)
 *   Sub 1 scaredy saw      carrier -> host [bodyId]
 *   Sub 2 scaredy scream   host -> all   [carrier][bodyId][room]  (SystemTypes, 255 = no room)
 *   Sub 3 phantom request  impostor -> host
 *   Sub 4 phantom start    host -> all   [seed int][speed float][seconds float][n] n x [playerId]
 *   Sub 5 phantom touch    any -> host   [index]
 *   Sub 6 phantom dissolve host -> all   [index]
 *   Sub 7 phantom end      host -> all
 * The mirrors need no network traffic (every client knows every DefaultOutfit).
 *
 * Options 2060-2079 (see ID-Registry.md), display sentinel RoleId 238 for the Scaredy-Cat.
 * Registration like the Banshee: Boot() from a HarmonyPrepare, postfixes on UC through reflection, Unknown's
 * Collection itself knows nothing about these features.
 *
 * Artwork: Resources/hw2026/<scaredy|mirror|phantom>/<file>.png (embedded). Missing files are drawn at runtime,
 * so the delivered pictures take over without a code change.
 */

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Hazel;
using UnityEngine;
using TheOtherRoles;
using UnknownsCollection;

namespace UnknownsHalloween {
    internal static class HwMechanics {
        internal const string LogPrefix = "[Halloween/Mechanics]";
        internal const byte RpcId = 241;

        internal const byte SubScaredySet = 0, SubScaredySaw = 1, SubScaredyScream = 2;
        internal const byte SubPhantomRequest = 3, SubPhantomStart = 4, SubPhantomTouch = 5, SubPhantomDissolve = 6, SubPhantomEnd = 7;

        internal static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");
        internal static void Warn(string s) => HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {s}");

        // ---- helpers ----
        internal static bool AmHost() => AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost;
        internal static bool IsAlive(PlayerControl p) => p != null && p.Data != null && !p.Data.IsDead && !p.Data.Disconnected;
        internal static bool InMeeting() => MeetingHud.Instance != null || ExileController.Instance != null;
        internal static bool FreePlay() { try { return AmongUsClient.Instance != null && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay; } catch { return false; } }
        internal static bool InRound() {
            try {
                var ac = AmongUsClient.Instance;
                return ac != null && (ac.GameState == InnerNet.InnerNetClient.GameStates.Started || ac.NetworkMode == NetworkModes.FreePlay)
                    && ShipStatus.Instance != null && PlayerControl.LocalPlayer != null;
            } catch { return false; }
        }
        internal static bool IsImp(PlayerControl p) { try { return p != null && p.Data != null && p.Data.Role != null && p.Data.Role.IsImpostor; } catch { return false; } }
        internal static bool? LangOverride;
        internal static bool De() { if (LangOverride.HasValue) return LangOverride.Value; try { return UCLocalization.ActiveCode == "german"; } catch { return false; } }

        /// <summary>"UnknownsAtlas.ActiveMap" (set by Atlas while one of its maps stands), null on the original maps.</summary>
        internal static string AtlasMap() {
            try { return (AppDomain.CurrentDomain.GetData("UnknownsAtlas.ActiveMap") as string)?.ToLowerInvariant(); } catch { return null; }
        }

        internal static float FeetOffset(PlayerControl p) {
            try {
                float f = p.transform.position.y - p.GetTruePosition().y;
                return f >= -0.1f && f <= 1f ? f : 0.36f;
            } catch { return 0.36f; }
        }

        // ---- rooms ----
        /// <summary>The room a point lies in; a real room wins over a hallway. Null when none.</summary>
        internal static PlainShipRoom RoomAt(Vector2 p) {
            var ship = ShipStatus.Instance;
            if (ship == null) return null;
            PlainShipRoom hall = null;
            try {
                foreach (var r in ship.AllRooms) {
                    if (r == null || r.roomArea == null || r.RoomId == SystemTypes.Outside) continue;
                    if (!r.roomArea.OverlapPoint(p)) continue;
                    if (r.RoomId == SystemTypes.Hallway) { hall ??= r; continue; }
                    return r;
                }
            } catch { }
            return hall;
        }

        /// <summary>The shown name of a room (Atlas maps rename the SystemTypes through TranslationController).</summary>
        internal static string RoomName(byte room) {
            if (room == byte.MaxValue) return null;
            var sys = (SystemTypes)room;
            if (sys == SystemTypes.Hallway) return De() ? "einem Gang" : "a hallway";
            try {
                var tc = DestroyableSingleton<TranslationController>.Instance;
                if (tc != null) { var s = tc.GetString(sys); if (!string.IsNullOrEmpty(s)) return s; }
            } catch { }
            return sys.ToString();
        }

        // ---- RPC ----
        internal static void Send(byte sub, Action<MessageWriter> write) {
            if (FreePlay()) return;                         // nobody to tell
            try {
                var w = UCRpc.Begin(RpcId);
                w.Write(sub);
                write?.Invoke(w);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} send {sub} failed: {e}"); }
        }

        private static void HandleModuleRpc(MessageReader r) {
            try {
                byte sub = r.ReadByte();
                switch (sub) {
                    case SubScaredySet: case SubScaredySaw: case SubScaredyScream:
                        HwScaredyCat.HandleRpc(sub, r); break;
                    case SubPhantomRequest: case SubPhantomStart: case SubPhantomTouch: case SubPhantomDissolve: case SubPhantomEnd:
                        HwPhantomParade.HandleRpc(sub, r); break;
                    default: Warn($"unknown sub {sub}"); break;
                }
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} rpc failed: {e}"); }
        }

        // ---- self registration ----
        private static bool booted;
        private static void Boot() {
            if (booted) return;
            booted = true;
            try {
                HwScaredyCat.CreateOptions();
                HwMirrors.CreateOptions();
                HwPhantomParade.CreateOptions();
                UCRpc.Register(RpcId, HandleModuleRpc);
                UCFx.RegisterTick(Tick);
                var h = new Harmony("daunknown.unknownshalloween.mechanics");
                void Post(Type t, string method, string postfix) {
                    var m = AccessTools.Method(t, method);
                    if (m != null) h.Patch(m, postfix: new HarmonyMethod(typeof(HwMechanics), postfix));
                    else Warn($"{t.Name}.{method} not found - that registration is skipped.");
                }
                Post(typeof(TeslaVersionHandshake), "AnyUCRoleEnabled", nameof(HandshakePostfix));
                Post(typeof(UCPromotion), "HasAnyModifier", nameof(HasAnyModifierPostfix));
                Log("registered (Scaredy-Cat, Haunted Mirrors, Phantom Parade).");
            } catch (Exception e) {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} self registration failed: {e}");
            }
        }

        // Every client needs the Halloween DLL as soon as one of the three is switched on.
        private static void HandshakePostfix(ref bool __result) {
            try { if (HwScaredyCat.Enabled() || HwMirrors.Enabled() || HwPhantomParade.Enabled()) __result = true; } catch { }
        }

        // The Scaredy-Cat counts as a modifier for UC's own pickers (no two modifiers on one player).
        private static void HasAnyModifierPostfix(PlayerControl p, ref bool __result) {
            try { if (!__result && HwScaredyCat.IsCarrier(p)) __result = true; } catch { }
        }

        private static void Tick() {
            try { HwScaredyCat.Tick(); } catch (Exception e) { Warn($"scaredy tick: {e.Message}"); }
            try { HwMirrors.Tick(); } catch (Exception e) { Warn($"mirror tick: {e.Message}"); }
            try { HwPhantomParade.Tick(); } catch (Exception e) { Warn($"phantom tick: {e.Message}"); }
            try { HwMechanicsDiag.Tick(); } catch (Exception e) { Warn($"diag tick: {e.Message}"); }
        }

        // ---- resets ----
        internal static void FullReset() {
            try { HwScaredyCat.Reset(); } catch (Exception e) { Warn($"scaredy reset: {e.Message}"); }
            try { HwMirrors.Reset(); } catch (Exception e) { Warn($"mirror reset: {e.Message}"); }
            try { HwPhantomParade.Reset(); } catch (Exception e) { Warn($"phantom reset: {e.Message}"); }
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

        // A meeting ends the parade and the scream marks.
        [HarmonyPatch(typeof(MeetingHud), nameof(MeetingHud.Start))]
        static class MeetingStartPatch {
            public static void Postfix() {
                try { HwScaredyCat.OnMeeting(); } catch { }
                try { HwPhantomParade.OnMeeting(); } catch { }
            }
        }
    }

    /// <summary>Embedded pictures under Resources/hw2026/&lt;folder&gt;/ with a runtime drawing as fallback.</summary>
    internal static class HwArt {
        private const string Res = "UnknownsHalloween.Resources.hw2026.";
        private static readonly Dictionary<string, Sprite> cache = new();
        internal static readonly HashSet<string> fromFile = new();

        internal static byte[] Read(string folder, string file) {
            try {
                using var stream = System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream(Res + folder + "." + file);
                if (stream == null) return null;
                var data = new byte[stream.Length];
                int read = 0;
                while (read < data.Length) {
                    int n = stream.Read(data, read, data.Length - read);
                    if (n <= 0) break;
                    read += n;
                }
                return read == data.Length ? data : null;
            } catch { return null; }
        }

        internal static Texture2D LoadTexture(string folder, string file) {
            try {
                var data = Read(folder, file);
                if (data == null) return null;
                var tex = new Texture2D(2, 2, TextureFormat.ARGB32, false) { name = "hw_" + file };
                if (!ImageConversion.LoadImage(tex, data, false)) { UnityEngine.Object.Destroy(tex); return null; }
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.filterMode = FilterMode.Bilinear;
                tex.Apply(false, true);
                tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
                return tex;
            } catch { return null; }
        }

        /// <summary>A sprite of the delivered picture or, without it, of the drawing. worldWidth = width in units.</summary>
        internal static Sprite Get(string folder, string file, float worldWidth, Vector2 pivot, Func<TreatFx.Canvas> draw) {
            string key = folder + "/" + file + "@" + worldWidth.ToString("F3");
            if (cache.TryGetValue(key, out var s) && s != null) return s;
            var tex = LoadTexture(folder, file);
            if (tex != null) fromFile.Add(folder + "/" + file);
            else if (draw != null) tex = draw().ToTexture("hw_" + file);
            if (tex == null) return null;
            s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, tex.width / Mathf.Max(0.01f, worldWidth));
            s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            cache[key] = s;
            return s;
        }

        internal static Color C(float r, float g, float b, float a = 1f) => new Color(r, g, b, a);
    }
}
