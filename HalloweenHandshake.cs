// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
// Based on The Other Roles (https://github.com/TheOtherRolesAU/TheOtherRoles), GPL-3.0.

/*
 * Who has Unknown's Halloween (2026-10-21, audit H-1). Until now every Halloween feature only asked UC's handshake
 * (TeslaVersionHandshake.EveryoneHasMod), which says nothing about this plugin: a guest with UC but without
 * Halloween became a Zombie Outbreak start zombie that really killed, a Xenomorph without buttons, or the last
 * crewmate of Sole Survivor who never saw the exit.
 *
 *  - Every client says hello to everyone: its Halloween version (four parts) and whether its costume packages are
 *    loaded (HalloweenCostumes.HatsRegistered). Sent once a local player exists, again whenever somebody joins.
 *  - EveryoneHasHalloween(): every other client in the lobby said hello with the same version.
 *    EveryoneHasPacks(): additionally everybody has the costume packages (Masquerade needs them, audit M-4).
 *  - Lobby: while a Halloween feature with gameplay effect is on and somebody is missing, the host sees a warning
 *    with the names and the game does not start (UC's own gate does the same for UC roles). Cosmetics (costumes,
 *    Halloween look, task skins) do not count, a guest without the mod just does not see them.
 *  - In the round the role picks and Trick or Treat / Omens check Ready() as a second safety net.
 *
 * RPC module byte 244 on UC's channel 230 (see ID-Registry.md): Sub 0 hello [major][minor][build][revision][packs].
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
    internal static class HalloweenHandshake {
        private const string LogPrefix = "[Halloween/Handshake]";
        internal const byte RpcId = 244;
        private const byte SubHello = 0;

        private sealed class Peer { public Version Version; public bool Packs; }
        private static readonly Dictionary<int, Peer> peers = new();       // by ClientId
        private static bool sent;

        private static Version Local => HalloweenPlugin.Version;
        private static bool FreePlay() { try { return AmongUsClient.Instance != null && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay; } catch { return false; } }

        private static bool booted;
        internal static void Boot() {
            if (booted) return;
            booted = true;
            try { UCRpc.Register(RpcId, Handle); } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} registration failed: {e}"); }
        }

        // ---------------------------------------------------------------- network
        private static void SendHello() {
            var ac = AmongUsClient.Instance;
            if (ac == null || PlayerControl.LocalPlayer == null || FreePlay()) return;
            var v = Local;
            bool packs = HalloweenCostumes.HatsRegistered;
            try {
                var w = UCRpc.Begin(RpcId);
                w.Write(SubHello);
                w.Write((byte)Math.Max(0, v.Major)); w.Write((byte)Math.Max(0, v.Minor));
                w.Write((byte)Math.Max(0, v.Build)); w.Write((byte)Math.Max(0, v.Revision));
                w.Write(packs);
                ac.FinishRpcImmediately(w);
                sent = true;
            } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} hello failed: {e.Message}"); }
        }

        private static void Handle(MessageReader r) {
            try {
                byte sub = r.ReadByte();
                if (sub != SubHello) return;
                byte a = r.ReadByte(), b = r.ReadByte(), c = r.ReadByte(), d = r.ReadByte();
                bool packs = r.ReadBoolean();
                var sender = UCRpc.Sender;
                if (sender == null) return;
                var v = new Version(a, b, c, d);
                bool known = peers.TryGetValue(sender.OwnerId, out var old);
                peers[sender.OwnerId] = new Peer { Version = v, Packs = packs };
                if (!known || old.Version != v || old.Packs != packs)
                    HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {sender.Data?.PlayerName ?? "#" + sender.OwnerId}: Halloween {v}{(packs ? "" : ", no costume packages")}");
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} hello read failed: {e}"); }
        }

        // ---------------------------------------------------------------- queries
        private static IEnumerable<InnerNet.ClientData> Others() {
            var ac = AmongUsClient.Instance;
            if (ac == null || ac.allClients == null) yield break;
            for (int i = 0; i < ac.allClients.Count; i++) {
                var c = ac.allClients[i];
                if (c == null || c.Character == null || c.Id == ac.ClientId || c.Character == PlayerControl.LocalPlayer) continue;
                yield return c;
            }
        }

        private static string Name(InnerNet.ClientData c) {
            try { return c.Character.Data?.PlayerName ?? c.PlayerName ?? $"#{c.Id}"; } catch { return $"#{c.Id}"; }
        }

        /// <summary>Every other player runs the same Halloween version. True in freeplay and outside a game.</summary>
        internal static bool EveryoneHasHalloween() => Missing(false).Count == 0;

        /// <summary>Same version and the costume packages everywhere (the local ones included).</summary>
        internal static bool EveryoneHasPacks() => HalloweenCostumes.HatsRegistered && Missing(true).Count == 0;

        /// <summary>UC's check plus this one: what the role picks and the candy/omen spawns ask.</summary>
        internal static bool Ready() {
            try { return TeslaVersionHandshake.EveryoneHasMod() && EveryoneHasHalloween(); } catch { return false; }
        }

        private static List<string> Missing(bool packs) {
            var list = new List<string>();
            try {
                if (AmongUsClient.Instance == null || FreePlay()) return list;
                foreach (var c in Others()) {
                    if (!peers.TryGetValue(c.Id, out var p)) list.Add(Name(c));
                    else if (p.Version != Local) list.Add($"{Name(c)} (v{p.Version})");
                    else if (packs && !p.Packs) list.Add($"{Name(c)} ({(De() ? "ohne Kostüm-Pakete" : "no costume packages")})");
                }
            } catch { }
            return list;
        }

        private static bool De() { try { return UCLocalization.ActiveCode == "german"; } catch { return false; } }

        // Features with a gameplay effect: these need the plugin on every client.
        internal static bool AnyFeatureOn() {
            try {
                return (Xenomorph.SpawnRate != null && Xenomorph.SpawnRate.getSelection() > 0)
                    || (Banshee.SpawnRate != null && Banshee.SpawnRate.getSelection() > 0)
                    || HwScaredyCat.Enabled() || HwMirrors.Enabled() || HwPhantomParade.Enabled()
                    || TreatSettings.Current.Enabled || OmenSettings.Current.Enabled || OmenSettings.Current.Spooks
                    || ZombieOutbreak.OptionOn || SoleSurvivor.OptionOn || Masquerade.ModeOn;
            } catch { return false; }
        }

        /// <summary>What keeps the game from starting, empty when nothing does.</summary>
        internal static List<string> Blockers() {
            if (!AnyFeatureOn()) return new List<string>();
            return Masquerade.ModeOn ? Missing(true).Concat(HalloweenCostumes.HatsRegistered ? Array.Empty<string>() : new[] { De() ? "Host ohne Kostüm-Pakete" : "host without costume packages" }).ToList()
                                     : Missing(false);
        }

        // ---------------------------------------------------------------- lifetime
        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class JoinedPatch {
            static bool Prepare() { Boot(); return true; }
            public static void Postfix() { peers.Clear(); sent = false; }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnPlayerJoined))]
        static class PlayerJoinedPatch {
            public static void Postfix() { try { SendHello(); } catch { } }      // the newcomer has to hear everybody again
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnPlayerLeft))]
        static class PlayerLeftPatch {
            public static void Postfix([HarmonyArgument(0)] InnerNet.ClientData data) {
                try { if (data != null) peers.Remove(data.Id); } catch { }
            }
        }

        // the lobby: first hello as soon as the local player exists, then the host's warning
        [HarmonyPatch(typeof(GameStartManager), nameof(GameStartManager.Update))]
        static class LobbyPatch {
            private static float nextCheck;
            private static List<string> blockers = new();
            private static bool lastPacks;

            [HarmonyPriority(Priority.Low - 1)]           // after UC's own warning in the same text
            public static void Postfix(GameStartManager __instance) {
                try {
                    if (PlayerControl.LocalPlayer != null && (!sent || lastPacks != HalloweenCostumes.HatsRegistered)) {
                        lastPacks = HalloweenCostumes.HatsRegistered;
                        SendHello();
                    }
                    var ac = AmongUsClient.Instance;
                    if (ac == null || !ac.AmHost || __instance.startState == GameStartManager.StartingStates.Countdown) return;
                    if (Time.unscaledTime >= nextCheck) { nextCheck = Time.unscaledTime + 0.5f; blockers = Blockers(); }
                    if (blockers.Count == 0) return;
                    var text = __instance.GameStartText;
                    if (text == null) return;
                    const string marker = "Unknown's Halloween";
                    if (text.text != null && text.text.Contains(marker)) return;
                    string msg = De() ? $"<color=#FF7518FF>{marker} fehlt oder ist anders: {string.Join(", ", blockers)}</color>"
                                      : $"<color=#FF7518FF>{marker} missing or different: {string.Join(", ", blockers)}</color>";
                    text.text = string.IsNullOrEmpty(text.text) ? msg : text.text + "\n" + msg;
                    __instance.GameStartTextParent.SetActive(true);
                } catch { }
            }
        }

        // the host cannot start while a Halloween feature is on and somebody lacks the plugin
        [HarmonyPatch(typeof(GameStartManager), nameof(GameStartManager.BeginGame))]
        static class BeginGameGatePatch {
            public static bool Prefix() {
                try {
                    var ac = AmongUsClient.Instance;
                    if (ac == null || !ac.AmHost || FreePlay()) return true;
                    var b = Blockers();
                    if (b.Count == 0) return true;
                    string msg = De() ? $"Start gesperrt: Unknown's Halloween fehlt bei {string.Join(", ", b)}. Halloween-Rollen und -Modi ausschalten oder die Mod installieren lassen."
                                      : $"Start blocked: Unknown's Halloween missing for {string.Join(", ", b)}. Turn the Halloween roles and modes off or have them install the mod.";
                    try { HudManager.Instance?.Notifier?.AddDisconnectMessage(msg); } catch { }
                    HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {msg}");
                    return false;
                } catch { return true; }
            }
        }
    }
}
