// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Angel - Weeping Angels in Hollowmere Manor (User 2026-10-24, Vorbild Doctor Who): die Brunnenfigur im
// Fountain Court (Art brunnen_blut) und die Engel auf dem Friedhof der grossen Manor (Art weeping_angel, statt der
// Grabsteine). Grundpose: Haende vor den Augen.
//
// Aggressivitaet (User 25.10., pro Spieler und Engel): jeder Engel hat mit jedem lebenden Spieler einen eigenen Wert.
// - in Sichtweite (Bildausschnitt um den Spieler, Lichtradius, keine Wand dazwischen), aber der Spieler schaut weg
//   (Blickrichtung des Crewmates links/rechts, der Engel steht hinter ihm): der Wert steigt, der Engel geht Stufe fuer
//   Stufe von "Haende vor den Augen" ueber "starrt an" (turn) zu "greift an" (step);
// - angeschaut: der Wert faellt auf 0 und steigt danach neu (1,6 pro Sekunde), springt also nicht sofort wieder hoch;
// - global (User 25.10.): schaut IRGENDEIN lebender Spieler einen Engel an, steht er fuer alle mit den Haenden vor den
//   Augen da und toetet niemanden; sonst zeigt er allen die Stufe des hoechsten Werts, den ein Spieler mit ihm hat;
// - Sichtweite fuer alle wie ein normaler Crewmate (Impostor und Rollen mit mehr Sicht sehen nicht weiter);
// - gar nicht in Sichtweite (auch im Vent, auf der Leiter, tot): der Wert sinkt langsam, er regt sich wieder ab.
// Der Host rechnet die Werte fuer alle Spieler, jeder Client dieselbe Formel fuer den eigenen Spieler und zeigt die Pose
// danach (nichts wird gesendet; Tauschbilder "Prop/<art>/<x>/<y>/turn|step", gen_villa PROP_VARIANTS).
//
// Angriff (Host-autoritativ, Option 1951 "Weeping Angels Attack", Standard an): voller Wert, weggeschaut und hoechstens
// 1,5 m entfernt -> "zurueck in die Zeit geschickt": Tod ueber TORs UncheckedMurderPlayer wie beim Pentagramm, ohne Schild,
// ohne Erstkill-Schild, ohne Bait-Selbstbericht; die Rollenzeile sagt "sent back in time". Weiter weg bleibt der Engel in
// der Angriffspose, bis man naeher kommt oder er sich abregt. Das Opfer sieht die Kill-Szene seines Engels
// (hk_angel_a<n>_*). RPC Modul 236 Sub 10 (Host -> alle, vor dem Kill). Ist die Option aus, wechseln nur die Posen.

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using TheOtherRoles;
using UnityEngine;
using UnknownsCollection;
using static TheOtherRoles.TheOtherRoles;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    public static CustomOption AngelAttack;
    internal const byte SubAngelVictim = 10;     // [spieler]  Host -> alle, vor dem Kill

    private sealed class AngelSlot
    {
        public readonly List<PropVar> Props = new();
        public Vector2 Pos;                     // Mitte der Standlinie; Abstand und Blickrichtung messen dagegen
        public string Pose;                     // null = Haende vor den Augen
    }

    private enum AngelSight { Hidden, Away, Watched }

    private readonly List<PropVar> _angels = new(), _graveAngels = new();
    private readonly List<AngelSlot> _slots = new();
    private readonly Dictionary<(byte Player, int Slot), float> _aggro = new();   // alle Spieler, auf jedem Client
    private float _nextAngelTick;
    private bool[] _angelWatched = Array.Empty<bool>();   // je Engel: schaut gerade irgendein lebender Spieler hin
    private bool _angelErrorLogged;
    private static readonly HashSet<byte> AngelVictims = new();

    // Brunnenfigur: Plan 31,0 / 31,05 = Brunnenmitte
    private static readonly Vector2 FountainAngel = new(31.0f - 17.0f, 14.0f - 31.05f);

    private const float AngelReach = 1.5f;       // Meter, nur fuer den Kill (25.10.: 3 m war zu weit)
    private const float AngelStareAt = 3f;       // Wert ab "starrt an" (turn)
    private const float AngelStepAt = 6f;        // Wert ab "greift an" (step)
    private const float AngelKillAt = 8f;        // voller Wert: Kill in Reichweite; hoeher steigt er nicht
    private const float AngelGainAway = 1.6f;    // pro Sekunde, sichtbar und weggeschaut (Anstarren ~2 s, Angriff ~4 s, Kill 5 s)
    private const float AngelGainWatched = 0.4f; // pro Sekunde, angeschaut (Pose steht, Wert waechst)
    private const float AngelCalm = 0.5f;        // pro Sekunde ausser Sicht (von voll bis ruhig 16 s)
    private const float AngelTickEvery = 0.2f;

    // Engel-Varianten (User 25.10.): vier Gestalten (a1 Trauerengel, a2 verhuellter Engel, a3 Putte, a4 Ruinenengel), je mit
    // eigenen Karten-Posen (in den Atlanten, je Platz eigene Rechtecke) und eigener Kill-Szene hk_angel_a<n>_*. Die Friedhofs-
    // engel bekommen reihum eine Variante, sortiert nach Position (x, dann y): rechnet jeder Client gleich, ohne RPC. Der
    // Brunnenengel ist a1. tools: villa_qwen/angel_scene.py (GPT-Schluesselbilder, "Blink"-Ablauf mit drei Blitzen).
    private const int AngelVariants = 4;
    private const int AngelSceneFrames = 48;
    private static readonly int[] AngelSceneFlashes = { 13, 25, 37 };
    private const float AngelSceneHold = 0.4f;
    private static readonly List<(Vector2 Pos, int Variant)> AngelVariantAt = new();

    /// <summary>Kill-Szene des Engels, der dem Opfer am naechsten steht.</summary>
    private static string AngelSceneFor(Vector2 victim)
    {
        int v = 1; float best = float.MaxValue;
        foreach (var (pos, variant) in AngelVariantAt)
        {
            float d = (pos - victim).sqrMagnitude;
            if (d < best) { best = d; v = variant; }
        }
        return $"angel_a{v}";
    }

    private static bool AngelAttackOn { get { try { return AngelAttack == null || AngelAttack.getBool(); } catch { return true; } } }

    private void AngelReset()
    {
        _slots.Clear();
        _aggro.Clear();
        AngelVictims.Clear();
        if (_angels.Count > 0)
        {
            var s = new AngelSlot { Pos = FountainAngel };
            s.Props.AddRange(_angels);
            _slots.Add(s);
        }
        foreach (var pv in _graveAngels)
        {
            var s = new AngelSlot { Pos = pv.Pos };
            s.Props.Add(pv);
            _slots.Add(s);
        }
        foreach (var s in _slots) SetPose(s, null);
        AngelVariantAt.Clear();
        if (_angels.Count > 0) AngelVariantAt.Add((FountainAngel, 1));
        int i = 0;
        foreach (var pv in _graveAngels.OrderBy(p => p.Pos.x).ThenBy(p => p.Pos.y))
            AngelVariantAt.Add((pv.Pos, i++ % AngelVariants + 1));
        if (_slots.Count > 0)
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} weeping angels: {_slots.Count} (attack {(AngelAttackOn ? "on" : "off")})");
    }

    private void AngelTick()
    {
        if (_slots.Count == 0) return;
        float now = Time.time;
        if (MeetingHud.Instance != null || ExileController.Instance != null)
        {
            foreach (var s in _slots) if (s.Pose != null) SetPose(s, null);
            _aggro.Clear();
            return;
        }
        if (now < _nextAngelTick) return;
        _nextAngelTick = now + AngelTickEvery;
        AngelAggroTick();
        // Bild, fuer alle gleich (User 25.10. "Engel global"): schaut irgendein lebender Spieler hin, Haende vor den Augen;
        // sonst die Stufe des hoechsten Werts, den ein Spieler mit diesem Engel hat
        for (int i = 0; i < _slots.Count; i++)
        {
            var s = _slots[i];
            float top = 0f;
            foreach (var kv in _aggro) if (kv.Key.Slot == i && kv.Value > top) top = kv.Value;
            string pose = i < _angelWatched.Length && _angelWatched[i] ? null : PoseFor(top);
            if (pose != s.Pose) SetPose(s, pose);
        }
    }

    private static void SetPose(AngelSlot s, string pose)
    {
        s.Pose = pose;
        foreach (var pv in s.Props) Show(pv, pose);
    }

    private static string PoseFor(float aggro) => aggro >= AngelStepAt ? "step" : aggro >= AngelStareAt ? "turn" : null;

    private static float NextAggro(float aggro, AngelSight sight, float dt) => sight switch
    {
        AngelSight.Away => Mathf.Min(AngelKillAt, aggro + AngelGainAway * dt),
        AngelSight.Watched => Mathf.Min(AngelKillAt, aggro + AngelGainWatched * dt),
        _ => Mathf.Max(0f, aggro - AngelCalm * dt),
    };

    /// <summary>Wie steht der Spieler zum Engel? Tote, Spieler im Vent oder auf der Leiter zaehlen als ausser Sicht.</summary>
    private static AngelSight SightOf(PlayerControl p, AngelSlot s)
    {
        if (p == null || p.Data == null || p.Data.IsDead || p.Data.Disconnected || p.inVent || p.onLadder) return AngelSight.Hidden;
        if (!AngelInSight(p, s.Pos)) return AngelSight.Hidden;
        return LooksAway(p, s.Pos) ? AngelSight.Away : AngelSight.Watched;
    }

    /// <summary>Schaut der Spieler vom Engel weg? Blickrichtung = Ausrichtung des Crewmates (links/rechts); der Engel muss
    /// hinter ihm stehen. Steht er fast genau ueber oder unter ihm, zaehlt das als Hinsehen.</summary>
    private static bool LooksAway(PlayerControl p, Vector2 angel)
    {
        bool left;
        try { left = p.cosmetics.currentBodySprite.BodySprite.flipX; } catch { return false; }
        float dx = angel.x - p.GetTruePosition().x;
        if (Mathf.Abs(dx) < 0.3f) return false;
        return left ? dx > 0f : dx < 0f;
    }

    /// <summary>Hat der Spieler den Engel in Sichtweite? Fuss oder Kopf im Bildausschnitt um den Spieler (Kameragroesse des
    /// eigenen Clients, die Kamera folgt dem Spieler), in Lichtweite und ohne Wand dazwischen. Rechnet fuer jeden Spieler
    /// gleich, damit Host (Kill) und Client (Bild) dasselbe Ergebnis haben.</summary>
    private static bool AngelInSight(PlayerControl p, Vector2 feet)
    {
        var me = p.GetTruePosition();
        var cam = Camera.main;
        float halfH = cam != null && cam.orthographic ? cam.orthographicSize : 3f;
        float halfW = halfH * (cam != null && cam.aspect > 0.1f ? cam.aspect : 16f / 9f);
        halfH *= 1.05f; halfW *= 1.05f;
        float radius = CrewSightRadius() + 0.6f;
        return PointInSight(me, feet, halfW, halfH, radius) || PointInSight(me, feet + new Vector2(0f, 1.6f), halfW, halfH, radius);
    }

    /// <summary>Sicht eines normalen Crewmates (Lichtschalter, CrewLightMod), fuer alle Spieler gleich: Impostor und Rollen
    /// mit mehr Sicht (Lighter ...) sehen die Engel nicht weiter als ein Crewmate (User 25.10.).</summary>
    private static float CrewSightRadius()
    {
        try
        {
            var ship = ShipStatus.Instance;
            if (ship == null) return 6f;
            float lights = 1f;
            if (ship.Systems.ContainsKey(SystemTypes.Electrical))
            {
                var sw = ship.Systems[SystemTypes.Electrical].TryCast<SwitchSystem>();
                if (sw != null) lights = sw.Value / 255f;
            }
            return Mathf.Lerp(ship.MinLightRadius, ship.MaxLightRadius, lights) * GameOptionsManager.Instance.currentNormalGameOptions.CrewLightMod;
        }
        catch { return 6f; }
    }

    private static bool PointInSight(Vector2 me, Vector2 pt, float halfW, float halfH, float radius)
    {
        var d = pt - me;
        if (Mathf.Abs(d.x) > halfW || Mathf.Abs(d.y) > halfH || d.magnitude > radius) return false;
        try { return !PhysicsHelpers.AnythingBetween(me, pt, Constants.ShadowMask, false); } catch { return true; }
    }

    // ------------------------------------------------------------------ Werte aller Spieler (jeder Client), Angriff (Host)

    /// <summary>Jeder Client rechnet die Werte aller Spieler mit derselben Formel (das Replay zeigt sie fuer jeden); nur der
    /// Host toetet.</summary>
    private void AngelAggroTick()
    {
        // erst alle Blicke: schaut irgendein lebender Spieler einen Engel an, ist er fuer alle eingefroren (kein Kill)
        var players = PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null && !p.Data.IsDead && !p.Data.Disconnected).ToList();
        if (_angelWatched.Length != _slots.Count) _angelWatched = new bool[_slots.Count];
        Array.Clear(_angelWatched, 0, _angelWatched.Length);
        var sights = new AngelSight[players.Count, _slots.Count];
        for (int n = 0; n < players.Count; n++)
            for (int i = 0; i < _slots.Count; i++)
            {
                sights[n, i] = SightOf(players[n], _slots[i]);
                if (sights[n, i] == AngelSight.Watched) _angelWatched[i] = true;
            }
        var present = new HashSet<byte>();
        for (int n = 0; n < players.Count; n++)
        {
            var p = players[n];
            byte pid = p.PlayerId;
            present.Add(pid);
            for (int i = 0; i < _slots.Count; i++)
            {
                var s = _slots[i];
                var key = (pid, i);
                _aggro.TryGetValue(key, out float aggro);
                var sight = sights[n, i];
                // angeschaut (von irgendwem): zurueck auf 0 (User 25.10.), danach steigt er neu von unten
                aggro = _angelWatched[i] ? 0f : NextAggro(aggro, sight, AngelTickEvery);
                if (aggro <= 0f) _aggro.Remove(key); else _aggro[key] = aggro;
                if (!AmHost || !AngelAttackOn || _angelWatched[i] || sight != AngelSight.Away || aggro < AngelKillAt) continue;
                if (Vector2.Distance(p.GetTruePosition(), s.Pos) > AngelReach) continue;
                KillByAngel(p);
                present.Remove(pid);
                break;
            }
        }
        foreach (var k in _aggro.Keys.ToList()) if (!present.Contains(k.Player)) _aggro.Remove(k);
    }

    // ------------------------------------------------------------------ Round Replay (UTS, RoundReplayMarkers.cs)

    private static readonly string[] AngelVariantNames = { "Mourning angel", "Hooded angel", "Cherub", "Ruined angel" };

    /// <summary>Einmal beim Start: die Engel als Replay-Marker fuer UTS (AppDomain, ohne Verweis). Die Funktionen lesen die
    /// Welt der laufenden Runde; ausserhalb von Hollowmere liefern sie nichts.</summary>
    internal static void AngelReplayRegister()
    {
        try
        {
            AppDomain.CurrentDomain.SetData("UTS.ReplayMarkers.Layout", (Func<string>)AngelReplayLayout);
            AppDomain.CurrentDomain.SetData("UTS.ReplayMarkers.Values", (Func<byte, float[]>)AngelReplayValues);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} replay markers not registered: {e.Message}"); }
    }

    private static string AngelReplayLayout()
    {
        var w = _current;
        if (w == null || w._slots.Count == 0) return null;
        var ci = System.Globalization.CultureInfo.InvariantCulture;
        var sb = new System.Text.StringBuilder("Weeping Angels: aggression");
        sb.Append('|').Append((AngelStareAt / AngelKillAt).ToString(ci)).Append('|').Append((AngelStepAt / AngelKillAt).ToString(ci));
        foreach (var s in w._slots)
        {
            int v = 1;
            foreach (var (pos, variant) in AngelVariantAt) if ((pos - s.Pos).sqrMagnitude < 0.01f) { v = variant; break; }
            sb.Append('\n').Append(AngelVariantNames[(v - 1) % AngelVariantNames.Length])
              .Append('|').Append(s.Pos.x.ToString(ci)).Append('|').Append(s.Pos.y.ToString(ci));
        }
        return sb.ToString();
    }

    private static float[] AngelReplayValues(byte pid)
    {
        var w = _current;
        if (w == null || w._slots.Count == 0) return null;
        float[] res = null;
        for (int i = 0; i < w._slots.Count; i++)
        {
            if (!w._aggro.TryGetValue((pid, i), out float a) || a <= 0f) continue;
            res ??= new float[w._slots.Count];
            res[i] = a / AngelKillAt;
        }
        return res;
    }

    private static void KillByAngel(PlayerControl p)
    {
        try
        {
            byte pid = p.PlayerId;
            SendAngelVictim(pid);
            MarkAngelVictim(pid);
            bool freeplay = AmongUsClient.Instance != null && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay;
            if (freeplay) p.MurderPlayer(p, MurderResultFlags.Succeeded);
            else Helpers.MurderPlayer(p, p, false);
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} weeping angel sent {p.Data?.PlayerName} back in time");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} angel kill failed: {e.Message}"); }
    }

    // Opfer merken (alle Clients) und auf dem eigenen Client die Kill-Szene spielen
    private static void MarkAngelVictim(byte pid)
    {
        AngelVictims.Add(pid);
        try
        {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || lp.PlayerId != pid) return;
            int color = lp.Data != null ? lp.Data.DefaultOutfit.ColorId : 0;
            string scene = AngelSceneFor(lp.GetTruePosition());
            if (!HalloweenCostumes.PlayStandaloneScene(scene, AngelSceneFrames, AngelSceneFlashes, AngelSceneHold, color))
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} angel kill scene {scene} not delivered yet - no overlay");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} angel scene failed: {e.Message}"); }
    }

    private static void SendAngelVictim(byte pid)
    {
        try
        {
            if (PlayerControl.LocalPlayer == null || AmongUsClient.Instance == null) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubAngelVictim);
            w.Write(pid);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} angel send failed: {e.Message}"); }
    }

    private static void HandleAngelRpc(Hazel.MessageReader reader)
    {
        byte pid = reader.ReadByte();
        if (!UCRpc.RequireHost("Hollowmere.Angel")) return;
        MarkAngelVictim(pid);
    }

    private void AngelError(Exception e)
    {
        if (_angelErrorLogged) return;
        _angelErrorLogged = true;
        HalloweenPlugin.Logger.LogError($"{LogPrefix} weeping angels failed (logged once): {e}");
    }

    // ------------------------------------------------------------------ TOR-Nacharbeit (wie GraveyardWorld.Ritual)

    private static string _angelFirstKillBefore;
    private static System.Reflection.FieldInfo _angelFirstKillField;

    [HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.MurderPlayer))]
    private static class AngelMurderPatch
    {
        [HarmonyPriority(Priority.First)]
        public static void Prefix([HarmonyArgument(0)] PlayerControl target)
        {
            try
            {
                if (target == null || !AngelVictims.Contains(target.PlayerId)) return;
                _angelFirstKillField ??= AccessTools.Field(AccessTools.TypeByName("TheOtherRoles.TORMapOptions"), "firstKillName");
                _angelFirstKillBefore = _angelFirstKillField?.GetValue(null) as string;
            }
            catch { }
        }

        [HarmonyPriority(Priority.Last)]
        public static void Postfix(PlayerControl __instance, [HarmonyArgument(0)] PlayerControl target)
        {
            try
            {
                if (target == null || __instance == null || __instance.PlayerId != target.PlayerId || !AngelVictims.Contains(target.PlayerId)) return;
                if (string.IsNullOrEmpty(_angelFirstKillBefore) && _angelFirstKillField != null) _angelFirstKillField.SetValue(null, "");
                foreach (var k in Bait.active.Keys.ToList()) if (k.player != null && k.player.PlayerId == target.PlayerId) Bait.active.Remove(k);
            }
            catch { }
        }
    }

    // Kein Vanilla-Overlay ("toetet sich selbst"); die Szene spielt MarkAngelVictim.
    [HarmonyPatch(typeof(KillOverlay), nameof(KillOverlay.ShowKillAnimation), typeof(NetworkedPlayerInfo), typeof(NetworkedPlayerInfo))]
    private static class AngelOverlayPatch
    {
        [HarmonyPriority(Priority.First)]
        public static bool Prefix([HarmonyArgument(0)] NetworkedPlayerInfo killer, [HarmonyArgument(1)] NetworkedPlayerInfo victim)
        {
            try
            {
                if (killer != null && victim != null && killer.PlayerId == victim.PlayerId && AngelVictims.Contains(victim.PlayerId)) return false;
            }
            catch { }
            return true;
        }
    }

    [HarmonyPatch(typeof(RoleInfo), nameof(RoleInfo.GetRolesString))]
    private static class AngelRoleStringPatch
    {
        public static void Postfix(PlayerControl p, ref string __result)
        {
            try
            {
                if (AngelVictims.Count == 0 || p == null || __result == null || !AngelVictims.Contains(p.PlayerId) || p.Data == null || !p.Data.IsDead) return;
                int i = __result.IndexOf(" - killed by ", StringComparison.Ordinal);
                if (i >= 0) __result = __result.Substring(0, i) + " - <color=#9FB4C7>sent back in time</color>";
            }
            catch { }
        }
    }
}
