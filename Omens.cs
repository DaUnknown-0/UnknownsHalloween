// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Omens (2026-10-20): at the start of every round the host draws one omen from the pot; everybody gets a card
 * (name plus one line) and the omen's rule holds for the whole round.
 *
 *   Raven Omen    ravens circle over every body 20 s after the kill (every client sees them, above the shadow)
 *   New Moon      vision of everybody x0.8
 *   Full Moon     vision of everybody x1.15; UC's Werewolf stays transformed 50 % longer
 *   Bat Night     a Comms sabotage has to be fixed twice (the host breaks it once more after the first fix)
 *   Harvest       twice as many candies (only in the pot while Trick or Treat is on)
 *   Silent Night  the emergency button stays locked for 60 s after the round start and after every meeting
 *   Thunderstorm  lightning from the host's seed every 40 to 90 s: 0.2 s full sight, 1 s afterglow, rain on screen.
 *                 No thunder: the synthetic sounds failed on 2026-10-05.
 *
 * Spook moments (Spooks.cs) share the menu, the rules message and the RPC module.
 *
 * Network: module byte 239 on UC's channel 230 (Banshee 237, Trick or Treat 238). Host-authoritative:
 *   Sub 0 rules   host -> all  [omens on][pot byte][spooks on]
 *   Sub 1 omen    host -> all  [omen or 255][seed int]                    (once per round, before the intro ends)
 *   Sub 2 spooks  host -> all  [seed int][n] n x [x short*100][y short*100][kind][param]   (once per round)
 *   Sub 3 midnight host -> all []                                         (the host's clock struck 00:00)
 * No TOR options (own menu, OmensMenu.cs); the host's choice lives in BepInEx/config/com.daunknown.unknownshalloween.omens.cfg.
 * Self test: UC_HALLOWEEN_DIAG=omens or =spook (OmensDiag.cs).
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using Hazel;
using UnityEngine;
using TheOtherRoles;
using UnknownsCollection;

namespace UnknownsHalloween {
    internal enum Omen : byte { Raven, NewMoon, FullMoon, BatNight, Harvest, SilentNight, Thunderstorm, Count, None = 255 }

    internal sealed class OmenRules {
        public bool Enabled;
        public byte Pot = OmenSettings.AllOmens;
        public bool Spooks;

        public OmenRules Clone() => (OmenRules)MemberwiseClone();
        public void Write(MessageWriter w) { w.Write(Enabled); w.Write(Pot); w.Write(Spooks); }
        public static OmenRules Read(MessageReader r) => new OmenRules { Enabled = r.ReadBoolean(), Pot = r.ReadByte(), Spooks = r.ReadBoolean() };
        public override string ToString() => $"omens {Enabled} (pot {string.Join(",", Enumerable.Range(0, (int)Omen.Count).Where(i => (Pot & (1 << i)) != 0).Select(i => ((Omen)i).ToString()))}), spooks {Spooks}";
    }

    internal static class OmenSettings {
        internal const byte AllOmens = (1 << (int)Omen.Count) - 1;
        internal static OmenRules Current = new OmenRules();

        private static ConfigFile cfg;
        private static ConfigEntry<bool> cEnabled, cSpooks;
        private static ConfigEntry<string> cOff;

        internal static void Load() {
            try {
                cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, "com.daunknown.unknownshalloween.omens.cfg"), true);
                cEnabled = cfg.Bind("Omens", "Enabled", false, "An omen of the round (host setting, sent to everyone).");
                cOff = cfg.Bind("Omens", "Disabled Omens", "", "Omens that are not in the pot, comma separated.");
                cSpooks = cfg.Bind("Spook Moments", "Enabled", false, "Harmless spook moments every one to two minutes plus the midnight moment.");
                Current = FromConfig();
                HalloweenPlugin.Logger?.LogInfo($"{Omens.LogPrefix} rules from the config: {Current}");
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{Omens.LogPrefix} config failed: {e}"); }
        }

        private static OmenRules FromConfig() {
            var r = new OmenRules();
            if (cfg == null) return r;
            r.Enabled = cEnabled.Value;
            r.Spooks = cSpooks.Value;
            var off = new HashSet<string>((cOff.Value ?? "").Split(',').Select(x => x.Trim()).Where(x => x.Length > 0));
            r.Pot = 0;
            for (int i = 0; i < (int)Omen.Count; i++) if (!off.Contains(((Omen)i).ToString())) r.Pot |= (byte)(1 << i);
            if (r.Pot == 0) r.Pot = AllOmens;
            return r;
        }

        private static void Save() {
            if (cfg == null) return;
            cEnabled.Value = Current.Enabled;
            cSpooks.Value = Current.Spooks;
            cOff.Value = string.Join(",", Enumerable.Range(0, (int)Omen.Count).Where(i => (Current.Pot & (1 << i)) == 0).Select(i => ((Omen)i).ToString()));
            try { cfg.Save(); } catch { }
        }

        internal static bool CanEdit() => TreatSettings.CanEdit();

        internal static void Changed() {
            if (!CanEdit()) return;
            if ((Current.Pot & AllOmens) == 0) Current.Pot = AllOmens;
            Save();
            Broadcast();
        }

        internal static void Broadcast() {
            if (!TrickOrTreat.AmHost()) return;
            var r = Current.Clone();
            Omens.Send(Omens.SubRules, r.Write);
        }

        internal static void ApplyFromHost(OmenRules r) {
            bool changed = r.ToString() != Current.ToString();
            Current = r;
            if (changed) {
                HalloweenPlugin.Logger?.LogInfo($"{Omens.LogPrefix} rules from the host: {r}");
                OmensMenu.RefreshIfOpen();
            }
        }

        private static float sendAt = -1f, resendAt;
        internal static void Tick() {
            if (!TrickOrTreat.AmHost()) return;
            float t = Time.realtimeSinceStartup;
            if (sendAt > 0f && t >= sendAt) { sendAt = -1f; Broadcast(); }
            if (LobbyBehaviour.Instance != null && t >= resendAt) { resendAt = t + 20f; Broadcast(); }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
        static class JoinedPatch {
            static bool Prepare() { Omens.Boot(); return true; }
            public static void Postfix() {
                try {
                    if (TrickOrTreat.AmHost()) { Current = FromConfig(); sendAt = Time.realtimeSinceStartup + 1.2f; }
                    else Current = new OmenRules();
                    OmensMenu.Close();
                    Omens.FullReset();
                } catch { }
            }
        }

        [HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnPlayerJoined))]
        static class PlayerJoinedPatch {
            public static void Postfix() { if (TrickOrTreat.AmHost()) sendAt = Time.realtimeSinceStartup + 2.2f; }
        }

        [HarmonyPatch(typeof(GameStartManager), nameof(GameStartManager.BeginGame))]
        static class BeginGamePatch {
            public static void Postfix() { try { Broadcast(); } catch { } }
        }
    }

    internal static class Omens {
        internal const string LogPrefix = "[Halloween/Omens]";
        internal const byte RpcId = 239;
        internal const byte SubRules = 0, SubOmen = 1, SubSpooks = 2, SubMidnight = 3;

        internal static readonly string[] Keys = { "raven", "newmoon", "fullmoon", "batnight", "harvest", "silentnight", "thunderstorm" };
        internal static readonly string[] Names = { "Raven Omen", "New Moon", "Full Moon", "Bat Night", "Harvest", "Silent Night", "Thunderstorm" };
        internal static readonly Color[] Tints = {
            new Color(0.62f, 0.55f, 0.78f), new Color(0.55f, 0.62f, 0.86f), new Color(1f, 0.92f, 0.62f), new Color(0.78f, 0.45f, 0.85f),
            new Color(1f, 0.6f, 0.18f), new Color(0.65f, 0.86f, 1f), new Color(0.8f, 0.88f, 1f),
        };

        internal static string Line(Omen o, bool de) {
            switch (o) {
                case Omen.Raven: return de ? "20 s nach einem Kill kreisen Raben über der Leiche. Alle sehen sie." : "20 s after a kill, ravens circle over the body. Everybody sees them.";
                case Omen.NewMoon: return de ? "Kein Mondlicht: alle sehen 20 % weniger." : "No moonlight: everybody sees 20 % less.";
                case Omen.FullMoon: return de ? "Helle Nacht: alle sehen etwas weiter, der Werewolf bleibt länger verwandelt." : "A bright night: everybody sees a little further, the Werewolf stays transformed longer.";
                case Omen.BatNight: return de ? "Fledermäuse in den Kabeln: Comms-Sabotage muss zweimal repariert werden." : "Bats in the cables: a Comms sabotage has to be fixed twice.";
                case Omen.Harvest: return de ? "Reiche Ernte: doppelt so viele Süßigkeiten." : "A rich harvest: twice as many candies.";
                case Omen.SilentNight: return de ? "Der Notfallknopf schweigt 60 s nach Rundenstart und nach jedem Meeting." : "The emergency button stays silent for 60 s after the start and after every meeting.";
                case Omen.Thunderstorm: return de ? "Ab und zu erhellt ein Blitz alles bis zum Bildschirmrand." : "Now and then lightning lights up everything to the edge of the screen.";
            }
            return "";
        }

        // ---- state (the same on every client) ----
        internal static Omen current = Omen.None;
        internal static int seed;
        private static bool drawn;                 // host: the omen (and the spook plan) of this round went out
        private static bool wasInRound, wasMeeting;
        internal static bool introDone;
        private static float roundSeenAt = -1f;
        internal static float playClock;           // seconds of play this round (no meetings, from the end of the intro)
        private static bool cardShown;
        private static float meetingEndAt = -100f;
        private static readonly System.Random rnd = new System.Random();

        internal static bool On() => OmensDiag.Omens || OmenSettings.Current.Enabled;
        internal static bool Is(Omen o) => current == o && TrickOrTreat.InRound();

        // ---- self registration ----
        private static bool booted;
        internal static void Boot() {
            if (booted) return;
            booted = true;
            try {
                OmenSettings.Load();
                UCRpc.Register(RpcId, HandleRpc);
                UCFx.RegisterTick(Tick);
                var h = new Harmony("daunknown.unknownshalloween.omens");
                var m = AccessTools.Method(typeof(TeslaVersionHandshake), "AnyUCRoleEnabled");
                if (m != null) h.Patch(m, postfix: new HarmonyMethod(typeof(Omens), nameof(HandshakePostfix)));
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} self registration failed: {e}"); }
        }

        private static void HandshakePostfix(ref bool __result) {
            try { if (OmenSettings.Current.Enabled || OmenSettings.Current.Spooks) __result = true; } catch { }
        }

        // ================================================================ RPC
        internal static void Send(byte sub, Action<MessageWriter> write) {
            if (TrickOrTreat.FreePlay()) return;
            try {
                var w = UCRpc.Begin(RpcId);
                w.Write(sub);
                write(w);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} send {sub} failed: {e}"); }
        }

        private static void HandleRpc(MessageReader r) {
            try {
                byte sub = r.ReadByte();
                switch (sub) {
                    case SubRules: {
                        var rules = OmenRules.Read(r);
                        if (UCRpc.RequireHost("Omens.Rules")) OmenSettings.ApplyFromHost(rules);
                        break;
                    }
                    case SubOmen: {
                        byte o = r.ReadByte();
                        int s = r.ReadInt32();
                        if (UCRpc.RequireHost("Omens.Omen")) ApplyOmen((Omen)o, s);
                        break;
                    }
                    case SubSpooks: {
                        int s = r.ReadInt32();
                        int n = r.ReadByte();
                        var list = new List<Spooks.Spot>();
                        for (int i = 0; i < n; i++) {
                            float x = r.ReadInt16() / 100f, y = r.ReadInt16() / 100f;
                            list.Add(new Spooks.Spot { Pos = new Vector2(x, y), Kind = (Spooks.Kind)r.ReadByte(), Param = r.ReadByte() });
                        }
                        if (UCRpc.RequireHost("Omens.Spooks")) Spooks.ApplyPlan(s, list);
                        break;
                    }
                    case SubMidnight:
                        if (UCRpc.RequireHost("Omens.Midnight")) Spooks.QueueMidnight();
                        break;
                }
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} HandleRpc failed: {e}"); }
        }

        // ================================================================ draw (host)
        /// <summary>Host: draw the omen of the round (once) and send it. Also called by Trick or Treat's spawn (Harvest).</summary>
        internal static void EnsureDrawn() {
            try {
                if (drawn || !TrickOrTreat.AmHost() || !TrickOrTreat.InRound()) return;
                if (!TrickOrTreat.FreePlay() && !HalloweenHandshake.Ready()) { drawn = true; return; }
                drawn = true;
                if (On()) {
                    var pot = Enumerable.Range(0, (int)Omen.Count).Where(i => (OmenSettings.Current.Pot & (1 << i)) != 0).Select(i => (Omen)i).ToList();
                    if (!TrickOrTreat.On()) pot.Remove(Omen.Harvest);
                    Omen o = pot.Count > 0 ? pot[rnd.Next(pot.Count)] : Omen.None;
                    if (OmensDiag.Omens) o = Omen.None;      // the self test forces them one by one
                    int s = rnd.Next(1, int.MaxValue);
                    Send(SubOmen, w => { w.Write((byte)o); w.Write(s); });
                    ApplyOmen(o, s);
                }
                Spooks.HostPlan();
            } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} draw failed: {e}"); }
        }

        internal static void ApplyOmen(Omen o, int s) {
            current = o;
            seed = s;
            cardShown = false;
            OmensFx.OnOmen();
            HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} omen of the round: {(o == Omen.None ? "none" : Names[(int)o])} (seed {s})");
        }

        /// <summary>Candy multiplier for Trick or Treat's spawn (Harvest).</summary>
        internal static int CandyFactor() {
            try {
                EnsureDrawn();
                return current == Omen.Harvest ? 2 : 1;
            } catch { return 1; }
        }

        // ================================================================ tick (every frame, every client)
        private static bool tickErrorLogged;
        internal static void Tick() {
            try {
                OmenSettings.Tick();
                OmensMenu.Tick();
                OmensDiag.Tick();
                bool round = TrickOrTreat.InRound();
                if (!round) {
                    if (wasInRound) FullReset();
                    return;
                }
                if (!wasInRound) { wasInRound = true; roundSeenAt = Time.time; if (TrickOrTreat.FreePlay()) introDone = true; }
                if (!introDone && Time.time - roundSeenAt > 15f) introDone = true;     // no intro seen (late hook, odd client)
                if (TrickOrTreat.AmHost() && !drawn && Time.time - roundSeenAt > 1.5f) EnsureDrawn();

                bool meeting = TrickOrTreat.InMeeting();
                if (meeting) {
                    if (!wasMeeting) OnMeetingStart();
                    wasMeeting = true;
                    OmensFx.Tick(true);
                    Spooks.Tick(true);
                    return;
                }
                if (wasMeeting) { wasMeeting = false; meetingEndAt = Time.time; if (current != Omen.None) OmensFx.ShowCard(current, 4f); }
                if (!introDone) { OmensFx.Tick(true); Spooks.Tick(true); return; }
                if (!cardShown && current != Omen.None) { cardShown = true; OmensFx.ShowCard(current, 6.5f); SilentNightStart(); }
                playClock += Time.deltaTime;
                TickSilentNight();
                TickFullMoon();
                TickBatNight();
                TickRavens();
                OmensFx.Tick(false);
                Spooks.Tick(false);
            } catch (Exception e) {
                if (!tickErrorLogged) { tickErrorLogged = true; HalloweenPlugin.Logger?.LogError($"{LogPrefix} tick failed (logged once): {e}"); }
            }
        }

        private static void OnMeetingStart() {
            kills.Clear();
            OmensFx.ClearRavens();
        }

        internal static void FullReset() {
            current = Omen.None;
            seed = 0;
            drawn = false;
            wasInRound = false;
            wasMeeting = false;
            introDone = false;
            roundSeenAt = -1f;
            playClock = 0f;
            cardShown = false;
            meetingEndAt = -100f;
            kills.Clear();
            wolfExtended = false;
            commsWasActive = false;
            commsRebroken = false;
            rebreakAt = -1f;
            silentUntil = -1f;
            OmensFx.Clear();
            Spooks.Reset();
        }

        // ---- Silent Night: the emergency cooldown at least 60 s after the start and after every meeting ----
        private static float silentUntil = -1f;
        private static void SilentNightStart() { if (current == Omen.SilentNight) silentUntil = Time.time + 60f; }
        private static void TickSilentNight() {
            if (current != Omen.SilentNight) return;
            if (Time.time - meetingEndAt < 0.5f) silentUntil = Time.time + 60f;
            float left = silentUntil - Time.time;
            if (left <= 0f) return;
            try {
                var ship = ShipStatus.Instance;
                // for the first seconds the game itself may still write its own cooldown: keep the higher one
                if (ship != null && ship.EmergencyCooldown < left - 0.05f) ship.EmergencyCooldown = left;
            } catch { }
        }
        internal static float DiagEmergency() { try { return ShipStatus.Instance.EmergencyCooldown; } catch { return -1f; } }

        // ---- Full Moon: the Werewolf's form lasts 50 % longer (UC's own timer, every client) ----
        private static bool wolfExtended;
        private static System.Reflection.FieldInfo formEndField;
        internal static bool DiagWolfHook => (formEndField ??= AccessTools.Field(typeof(Werewolf), "formEndTime")) != null;
        private static void TickFullMoon() {
            if (current != Omen.FullMoon) return;
            try {
                bool form = Werewolf.wolfForm;
                if (!form) { wolfExtended = false; return; }
                if (wolfExtended) return;
                wolfExtended = true;
                formEndField ??= AccessTools.Field(typeof(Werewolf), "formEndTime");
                if (formEndField == null) return;
                float dur = Werewolf.FormDuration != null ? Werewolf.FormDuration.getFloat() : 12f;
                float end = (float)formEndField.GetValue(null);
                formEndField.SetValue(null, end + dur * 0.5f);
                HalloweenPlugin.Logger?.LogInfo(FormattableString.Invariant($"{LogPrefix} Full Moon: Werewolf form +{dur * 0.5f:F1} s"));
            } catch { }
        }

        // ---- Bat Night: the host breaks Comms once more after the first fix ----
        private static bool commsWasActive, commsRebroken;
        private static float rebreakAt = -1f;
        internal static string DiagBat = "";
        internal static bool CommsActive() {
            try {
                var ship = ShipStatus.Instance;
                if (ship == null || !ship.Systems.TryGetValue(SystemTypes.Comms, out var raw) || raw == null) return false;
                var hud = raw.TryCast<HudOverrideSystemType>();
                if (hud != null) return hud.IsActive;
                var hq = raw.TryCast<HqHudSystemType>();
                return hq != null && hq.IsActive;
            } catch { return false; }
        }
        private static void TickBatNight() {
            if (current != Omen.BatNight || !TrickOrTreat.AmHost()) return;
            bool active = CommsActive();
            if (commsWasActive && !active) {
                if (!commsRebroken) { rebreakAt = Time.time + 1.5f; DiagBat = "fixed once"; }
                else { commsRebroken = false; DiagBat = "fixed twice"; }
            }
            commsWasActive = active;
            if (rebreakAt > 0f && Time.time >= rebreakAt) {
                rebreakAt = -1f;
                if (active) return;
                try {
                    var ship = ShipStatus.Instance;
                    if (ship.Systems.TryGetValue(SystemTypes.Sabotage, out var s) && s != null) {
                        var sab = s.TryCast<SabotageSystemType>();
                        if (sab != null) sab.Timer = 0f;       // the host checks its own cooldown
                    }
                    ship.RpcUpdateSystem(SystemTypes.Sabotage, (byte)SystemTypes.Comms);
                    commsRebroken = true;
                    DiagBat = "broken again";
                    HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} Bat Night: Comms broke once more.");
                } catch (Exception e) { HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} Bat Night re-break failed: {e.Message}"); }
            }
        }

        // ---- Raven Omen: kills seen on this client, ravens 20 s later over the body ----
        internal sealed class Kill { public byte Victim; public Vector2 Pos; public float At; public bool Gone; }
        internal static readonly List<Kill> kills = new();
        private static float bodyCheckAt;
        internal const float RavenDelay = 20f;

        internal static void OnKill(PlayerControl target) {
            if (current != Omen.Raven || target == null) return;
            kills.Add(new Kill { Victim = target.PlayerId, Pos = target.GetTruePosition(), At = Time.time });
        }

        private static void TickRavens() {
            if (current != Omen.Raven || kills.Count == 0) { OmensFx.TickRavens(null); return; }
            if (Time.time >= bodyCheckAt) {
                bodyCheckAt = Time.time + 0.5f;
                try {
                    var bodies = UnityEngine.Object.FindObjectsOfType<DeadBody>();
                    foreach (var k in kills) {
                        if (k.Gone || Time.time - k.At < RavenDelay - 0.6f) continue;
                        bool there = false;
                        foreach (var b in bodies) if (b != null && b.ParentId == k.Victim) { there = true; k.Pos = b.TruePosition; break; }
                        if (!there) k.Gone = true;       // cleaned, eaten, dragged off the map ...
                    }
                } catch { }
            }
            OmensFx.TickRavens(kills.Where(k => !k.Gone && Time.time - k.At >= RavenDelay).ToList());
        }

        [HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.MurderPlayer))]
        static class KillPatch {
            public static void Postfix([HarmonyArgument(0)] PlayerControl target) {
                try { if (target != null && target.Data != null && target.Data.IsDead) OnKill(target); } catch { }
            }
        }

        // ---- vision: New Moon, Full Moon, lightning ----
        [HarmonyPatch(typeof(ShipStatus), nameof(ShipStatus.CalculateLightRadius))]
        static class VisionPatch {
            [HarmonyPriority(Priority.Last)]
            public static void Postfix(ref float __result, [HarmonyArgument(0)] NetworkedPlayerInfo p) {
                try {
                    if (current == Omen.None || p == null || p.IsDead) return;
                    if (current == Omen.NewMoon) __result *= 0.8f;
                    else if (current == Omen.FullMoon) __result *= 1.15f;
                    else if (current == Omen.Thunderstorm) {
                        float b = OmensFx.LightningBoost();
                        if (b > 0f) __result = Mathf.Lerp(__result, Mathf.Max(__result, OmensFx.FullSight()), b);
                    }
                } catch { }
            }
        }

        [HarmonyPatch(typeof(IntroCutscene), nameof(IntroCutscene.OnDestroy))]
        static class IntroEndPatch {
            public static void Postfix() { introDone = true; }
        }

        // ---- self test hooks ----
        internal static void DiagForce(Omen o) {
            ApplyOmen(o, seed != 0 ? seed : 12345);
            cardShown = true;
            OmensFx.ShowCard(o, 6.5f);
            SilentNightStart();
        }
    }
}
