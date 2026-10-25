// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// GraveyardWorld.Ritual - Easter Egg am Runenkreis der Waechtersteine (User 2026-10-24).
//
// An den fuenf Spitzen des Pentagramms (Mitte 9,5 / 0,0, Stern auf 80 % verkleinert, tools/graveyard_floor.py) steht je
// eine Kerze. Lebende Spieler zuenden sie mit dem Use-Knopf an ("LIGHT"); jede Kerze geht als RPC an alle. Brennen alle
// fuenf, ruft der Host den Daemon: er steigt fuer 6,66 s in der Mitte auf, und wer in dieser Zeit im Kreis steht, stirbt
// (Host-autoritativ ueber TORs UncheckedMurderPlayer wie die Midnight-Bonbon-Vergiftung, kein Schild haelt es auf). Das
// Opfer sieht die Kill-Szene "demon" (Resources/hats/hk_demon_*), sonst gar keine. Danach und bei jedem Meeting gehen
// alle Kerzen aus.
//
// Grafik: Resources/hw2026/graveyard_egg/ (Fable, Auftrag 2026-10-24). Fehlt sie, zeichnet der Code einfache Ersatzformen.
// RPC: Modul 236 (HollowmereIntro.RpcModule), Sub 20 Kerze (jeder -> alle), 21 Ritual (Host -> alle), 22 Opfer (Host -> alle).

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Hazel;
using TheOtherRoles;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;
using static TheOtherRoles.TheOtherRoles;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

internal sealed partial class GraveyardWorld
{
    internal const byte SubFirst = 20;
    private const byte SubRitualCandle = 20;       // [kerze]           jeder -> alle
    private const byte SubRitualStart = 21;        // -                 Host -> alle
    private const byte SubRitualVictim = 22;       // [spieler]         Host -> alle, vor dem Kill

    private static readonly Vector2 RitualCenter = new(9.5f, 0f);
    private const float StarRx = 1.52f, StarRy = 1.216f;          // Sternspitzen (graveyard_floor.py, 80 %)
    // Todeszone: innerer Bereich (60 % des Kreiderings), die Kerzen an den Spitzen liegen deutlich ausserhalb (User 24.10.:
    // "nicht ganz so gross", wer gerade beschwoert, soll nicht direkt sterben)
    private const float KillRx = 1.1f, KillRy = 0.88f;
    private const float RitualSecs = 6.66f;
    private const float KillFrom = 2.0f;                           // erst nach 2 s toeten: Zeit, um aus dem Kreis zu gehen
    private const float CandleReach = 0.9f;
    private const float RitualPpm = 160f;
    private const string EggRes = "UnknownsHalloween.Resources.hw2026.graveyard_egg.";
    internal const float Fps = 12f;

    // Kill-Szene (Fable, Auftrag 2026-10-24: 48 Bilder, Blitze 0-basiert bei 22 und 36, letztes Bild 0,5 s stehen lassen)
    internal const string DemonScene = "demon";
    internal const int DemonFrames = 48;
    internal static readonly int[] DemonFlashes = { 22, 36 };
    internal const float DemonHold = 0.5f;

    private static GraveyardWorld _current;
    internal static readonly HashSet<byte> DemonVictims = new();   // auch das Pentagramm der Manor (HollowmereWorld.Ritual.cs)

    private readonly Vector2[] _candlePos = new Vector2[5];
    private readonly SpriteRenderer[] _candleSr = new SpriteRenderer[5];
    private readonly SpriteRenderer[] _candleGlow = new SpriteRenderer[5];
    private readonly bool[] _lit = new bool[5];
    private SpriteRenderer _demonSr, _floorGlow;
    private Transform _ritualRoot;
    private float _ritualStart = -1f, _nextKillCheck;
    private bool _inMeeting;

    internal static Sprite _candleOff, _floorGlowSprite, _candleGlowSprite;
    internal static Sprite[] _candleOn, _rise, _idle, _sink;
    private static bool _artTried;

    // ------------------------------------------------------------------ Aufbau

    private void RitualBuild()
    {
        _current = this;
        DemonVictims.Clear();
        LoadArt();
        // Der worldRoot von Atlas haengt am Schiff (Versatz und Skalierung des Skeld-Prefabs). Wie Atlas' eigene Kartenebene
        // (Atlas_Museum) auf Weltposition 0 und Massstab 1 setzen, sonst stehen die Kerzen neben dem Pentagramm (Spieltest 24.10.).
        _ritualRoot = new GameObject("Ravenhollow_Ritual").transform;
        _ritualRoot.SetParent(_root, false);
        var ls = _root.lossyScale;
        _ritualRoot.localScale = new Vector3(1f / ls.x, 1f / ls.y, 1f / ls.z);
        _ritualRoot.position = Vector3.zero;
        for (int k = 0; k < 5; k++)
        {
            float a = Mathf.PI / 2f + k * 2f * Mathf.PI * 2f / 5f;
            _candlePos[k] = RitualCenter + new Vector2(StarRx * Mathf.Cos(a), StarRy * Mathf.Sin(a));
            var go = new GameObject($"RitualCandle_{k}") { layer = _root.gameObject.layer };
            go.transform.SetParent(_ritualRoot, false);
            go.transform.localPosition = new Vector3(_candlePos[k].x, _candlePos[k].y, Depth(_candlePos[k].y));
            _candleSr[k] = go.AddComponent<SpriteRenderer>();
            _candleSr[k].sprite = _candleOff;
            _lit[k] = false;
            if (_candleGlowSprite != null)
            {
                // warmer Schein um die Flamme (0,45 m ueber der Standlinie), nur solange die Kerze brennt
                var g = new GameObject($"RitualCandleGlow_{k}") { layer = _root.gameObject.layer };
                g.transform.SetParent(go.transform, false);
                g.transform.localPosition = new Vector3(0f, 0.42f, 0.0001f);
                _candleGlow[k] = g.AddComponent<SpriteRenderer>();
                _candleGlow[k].sprite = _candleGlowSprite;
                g.SetActive(false);
            }
        }
        _ritualStart = -1f;
    }

    private void RitualDestroy()
    {
        if (_ritualRoot != null) Object.Destroy(_ritualRoot.gameObject);
        _ritualRoot = null;
        _demonSr = _floorGlow = null;
        if (_current == this) _current = null;
    }

    internal static float Depth(float standY) => (standY + 0.3636f) / 1000f - 0.0002f;

    // ------------------------------------------------------------------ Ablauf

    private void RitualTick(float dt)
    {
        if (_ritualRoot == null) return;
        float now = Time.time;
        bool meeting = MeetingHud.Instance != null || ExileController.Instance != null;
        if (meeting && !_inMeeting)
        {
            for (int k = 0; k < 5; k++) SetLit(k, false);
            EndRitual();
        }
        _inMeeting = meeting;

        // Flackern der brennenden Kerzen
        int fi = (int)(now * Fps);
        for (int k = 0; k < 5; k++)
        {
            if (_lit[k] && _candleSr[k] != null && _candleOn != null && _candleOn.Length > 0)
                _candleSr[k].sprite = _candleOn[(fi + k * 3) % _candleOn.Length];
            if (_lit[k] && _candleGlow[k] != null)
                _candleGlow[k].color = new Color(1f, 1f, 1f, 0.8f + 0.2f * Mathf.Sin(now * 9f + k * 1.7f));
        }

        if (_ritualStart >= 0f)
        {
            float t = now - _ritualStart;
            AnimateDemon(t);
            if (AmHost && t >= KillFrom && t <= RitualSecs && now >= _nextKillCheck)
            {
                _nextKillCheck = now + 0.1f;
                HostKillInside();
            }
            if (t > RitualSecs + (_sink?.Length ?? 0) / Fps) EndRitual(true);
            return;
        }
        if (!meeting) OfferRitualCandle();
    }

    private void OfferRitualCandle()
    {
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || lp.Data == null || lp.Data.IsDead) return;
        for (int k = 0; k < 5; k++)
        {
            if (_lit[k] || !AtlasMaps.CanReach(_candlePos[k], CandleReach)) continue;
            int idx = k;
            AtlasMaps.OfferUse("LIGHT", "task_gy_icon_candle.png", () => LightLocal(idx));
            return;
        }
    }

    private void LightLocal(int idx)
    {
        if (_lit[idx] || _ritualStart >= 0f) return;
        SetLit(idx, true);
        SendRitual(SubRitualCandle, w => w.Write((byte)idx));
        HostCheckAllLit();
    }

    private void SetLit(int idx, bool on)
    {
        if (idx < 0 || idx >= 5 || _lit[idx] == on) return;
        _lit[idx] = on;
        if (_candleSr[idx] != null) _candleSr[idx].sprite = on && _candleOn != null && _candleOn.Length > 0 ? _candleOn[0] : _candleOff;
        if (_candleGlow[idx] != null) _candleGlow[idx].gameObject.SetActive(on);
        if (on)
        {
            float vol = 0f;
            try { var lp = PlayerControl.LocalPlayer; if (lp != null) vol = Mathf.Clamp01(1f - Vector2.Distance(lp.GetTruePosition(), _candlePos[idx]) / 9f); } catch { }
            if (vol > 0.02f) AtlasMaps.Sfx("click", 0.7f * vol);
        }
    }

    private void HostCheckAllLit()
    {
        if (!AmHost || _ritualStart >= 0f || _inMeeting || _lit.Any(x => !x)) return;
        SendRitual(SubRitualStart, null);
        StartRitual();
    }

    private void StartRitual()
    {
        if (_ritualStart >= 0f) return;
        _ritualStart = Time.time;
        _nextKillCheck = 0f;
        var layer = _root.gameObject.layer;
        if (_floorGlow == null)
        {
            var g = new GameObject("RitualFloorGlow") { layer = layer };
            g.transform.SetParent(_ritualRoot, false);
            g.transform.localPosition = new Vector3(RitualCenter.x, RitualCenter.y, AtlasMuseumBuilderFloorZ - 1.5f);
            _floorGlow = g.AddComponent<SpriteRenderer>();
            _floorGlow.sprite = _floorGlowSprite;
        }
        if (_demonSr == null)
        {
            var d = new GameObject("RitualDemon") { layer = layer };
            d.transform.SetParent(_ritualRoot, false);
            var feet = RitualCenter + new Vector2(0f, -0.25f);
            d.transform.localPosition = new Vector3(feet.x, feet.y, Depth(feet.y));
            _demonSr = d.AddComponent<SpriteRenderer>();
        }
        _floorGlow.gameObject.SetActive(true);
        _demonSr.gameObject.SetActive(true);
        PlayClip(ref _bellClip, "ravenhollow_knell", SynthBell, 0.9f);
        AtlasMaps.Sfx("whoosh", 0.8f);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} pentagram: all candles lit, the demon rises for {RitualSecs:F2} s");
    }

    private void AnimateDemon(float t)
    {
        if (_demonSr == null) return;
        Sprite s = null;
        int f = (int)(t * Fps);
        int nRise = _rise?.Length ?? 0, nSink = _sink?.Length ?? 0;
        if (f < nRise) s = _rise[f];
        else if (t <= RitualSecs) s = _idle != null && _idle.Length > 0 ? _idle[(f - nRise) % _idle.Length] : (nRise > 0 ? _rise[nRise - 1] : null);
        else if (nSink > 0) s = _sink[Mathf.Min(nSink - 1, (int)((t - RitualSecs) * Fps))];
        _demonSr.sprite = s;
        if (_floorGlow != null)
        {
            float pulse = 0.75f + 0.25f * Mathf.Sin(t * 7f);
            float fade = t <= RitualSecs ? Mathf.Clamp01(t / 0.4f) : Mathf.Clamp01(1f - (t - RitualSecs) / 0.6f);
            _floorGlow.color = new Color(1f, 1f, 1f, pulse * fade);
        }
    }

    private void EndRitual(bool candlesOut = false)
    {
        if (_ritualStart < 0f) return;
        _ritualStart = -1f;
        if (_demonSr != null) _demonSr.gameObject.SetActive(false);
        if (_floorGlow != null) _floorGlow.gameObject.SetActive(false);
        if (candlesOut)
        {
            for (int k = 0; k < 5; k++) SetLit(k, false);
            AtlasMaps.Sfx("whoosh", 0.4f);
        }
    }

    private static bool InsideCircle(Vector2 p)
    {
        float dx = (p.x - RitualCenter.x) / KillRx, dy = (p.y - RitualCenter.y) / KillRy;
        return dx * dx + dy * dy <= 1f;
    }

    // ------------------------------------------------------------------ Host: toeten

    private static void HostKillInside()
    {
        foreach (var p in PlayerControl.AllPlayerControls.ToArray())
        {
            try
            {
                if (p == null || p.Data == null || p.Data.IsDead || p.Data.Disconnected || p.inVent) continue;
                if (!InsideCircle(p.GetTruePosition())) continue;
                byte pid = p.PlayerId;
                SendRitual(SubRitualVictim, w => w.Write(pid));
                MarkVictim(pid);
                bool freeplay = AmongUsClient.Instance != null && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay;
                if (freeplay) p.MurderPlayer(p, MurderResultFlags.Succeeded);
                else Helpers.MurderPlayer(p, p, false);
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} pentagram: the demon took {p.Data.PlayerName}");
            }
            catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} demon kill failed: {e.Message}"); }
        }
    }

    // Opfer merken (alle Clients) und auf dem eigenen Client die Kill-Szene spielen
    internal static void MarkVictim(byte pid)
    {
        DemonVictims.Add(pid);
        try
        {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || lp.PlayerId != pid) return;
            int color = lp.Data != null ? lp.Data.DefaultOutfit.ColorId : 0;
            if (!HalloweenCostumes.PlayStandaloneScene(DemonScene, DemonFrames, DemonFlashes, DemonHold, color))
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} demon kill scene not delivered yet - no overlay");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} demon scene failed: {e.Message}"); }
    }

    // ------------------------------------------------------------------ Netz

    private static void SendRitual(byte sub, Action<MessageWriter> body)
    {
        try
        {
            if (PlayerControl.LocalPlayer == null || AmongUsClient.Instance == null) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(sub);
            body?.Invoke(w);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} ritual send failed: {e.Message}"); }
    }

    internal static void HandleRpc(byte sub, MessageReader reader)
    {
        var w = _current;
        if (sub == SubRitualCandle)
        {
            int idx = reader.ReadByte();
            if (w == null || idx >= 5) return;
            var sender = UCRpc.Sender;
            if (sender == null || sender.Data == null || sender.Data.IsDead) return;     // Geister zuenden nichts an
            w.SetLit(idx, true);
            w.HostCheckAllLit();
        }
        else if (sub == SubRitualStart)
        {
            if (w == null || !UCRpc.RequireHost("Ravenhollow.Ritual")) return;
            for (int k = 0; k < 5; k++) w.SetLit(k, true);
            w.StartRitual();
        }
        else if (sub == SubRitualVictim)
        {
            byte pid = reader.ReadByte();
            if (!UCRpc.RequireHost("Ravenhollow.Victim")) return;
            MarkVictim(pid);
        }
    }

    private void RitualError(Exception e)
    {
        if (_ritualErrorLogged) return;
        _ritualErrorLogged = true;
        HalloweenPlugin.Logger.LogError($"{LogPrefix} ritual tick failed (logged once): {e}");
    }
    private static bool _ritualErrorLogged;
    private static bool AmHost => AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost;
    internal const float AtlasMuseumBuilderFloorZ = 9f;            // AtlasMuseumBuilder.FloorZ (internal)

    // ------------------------------------------------------------------ Grafik

    internal static void LoadArt()
    {
        if (_artTried) return;
        _artTried = true;
        _candleOff = Art("egg_candle_off.png", true) ?? PaintCandle(false, 0);
        _candleOn = Frames("egg_candle_on_", 4, true);
        if (_candleOn.Length == 0) _candleOn = new[] { PaintCandle(true, 0), PaintCandle(true, 1) };
        _rise = Frames("egg_demon_rise_", 12, true);
        _idle = Frames("egg_demon_idle_", 8, true);
        _sink = Frames("egg_demon_sink_", 8, true);
        if (_idle.Length == 0 && _rise.Length == 0) _idle = new[] { PaintDemon() };
        _floorGlowSprite = Art("egg_demon_floor_glow.png", false) ?? PaintGlow();
        _candleGlowSprite = Art("egg_candle_glow.png", false);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} pentagram art: candle {(_candleOn.Length > 2 ? "delivered" : "fallback")}, demon {_rise.Length}/{_idle.Length}/{_sink.Length} frames");
    }

    private static Sprite[] Frames(string prefix, int max, bool feet)
    {
        var list = new List<Sprite>();
        for (int i = 1; i <= max; i++)
        {
            var s = Art($"{prefix}{i}.png", feet);
            if (s == null) break;
            list.Add(s);
        }
        return list.ToArray();
    }

    private static void Keep(Object o) { if (o != null) o.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset; }

    /// <summary>Geliefertes Bild als Sprite (160 px/m); feet = Pivot unten Mitte (Standlinie), sonst Mitte.</summary>
    private static Sprite Art(string file, bool feet)
    {
        try
        {
            if (!HalloweenAssets.Exists(EggRes + file)) return null;
            var data = HalloweenAssets.Read(EggRes + file);
            if (data == null || data.Length == 0) return null;
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            if (!ImageConversion.LoadImage(tex, data, false)) return null;
            Keep(tex);
            var sp = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), feet ? new Vector2(0.5f, 0f) : new Vector2(0.5f, 0.5f), RitualPpm);
            Keep(sp);
            return sp;
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} egg art {file}: {e.Message}"); return null; }
    }

    internal static Sprite Painted(int w, int h, Vector2 pivot, Func<int, int, Color32> px)
    {
        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
        var arr = new Color32[w * h];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) arr[y * w + x] = px(x, y);
        tex.SetPixels32(arr);
        tex.Apply(false, false);
        Keep(tex);
        var sp = Sprite.Create(tex, new Rect(0, 0, w, h), pivot, RitualPpm);
        Keep(sp);
        return sp;
    }

    // Ersatz, bis Fables Bilder da sind: Wachskerze mit Umriss, optional Flamme
    private static Sprite PaintCandle(bool lit, int phase)
    {
        var ink = new Color32(22, 18, 26, 255);
        var wax = new Color32(232, 224, 200, 255);
        var flame = new Color32(255, 196, 64, 255);
        return Painted(32, 64, new Vector2(0.5f, 0f), (x, y) =>
        {
            bool body = x >= 10 && x <= 21 && y >= 2 && y <= 36;
            bool edge = body && (x == 10 || x == 21 || y == 2 || y == 36);
            if (edge) return ink;
            if (body) return wax;
            if (lit)
            {
                float fx = (x - 15.5f - (phase == 1 ? 1f : 0f)) / 4.5f, fy = (y - 46f) / 9f;
                if (fx * fx + fy * fy <= 1f) return flame;
            }
            return new Color32(0, 0, 0, 0);
        });
    }

    private static Sprite PaintDemon()
    {
        return Painted(160, 320, new Vector2(0.5f, 0f), (x, y) =>
        {
            float fx = (x - 80f) / 60f, fy = (y - 140f) / 140f;
            bool body = fx * fx + fy * fy <= 1f;
            bool hornL = y > 250 && y < 310 && Math.Abs(x - (40 + (y - 250) / 3)) < 6;
            bool hornR = y > 250 && y < 310 && Math.Abs(x - (120 - (y - 250) / 3)) < 6;
            bool eye = y > 205 && y < 220 && (Math.Abs(x - 62) < 8 || Math.Abs(x - 98) < 8);
            if (eye) return new Color32(255, 70, 40, 255);
            if (body || hornL || hornR) return new Color32(48, 10, 16, 235);
            return new Color32(0, 0, 0, 0);
        });
    }

    private static Sprite PaintGlow()
    {
        return Painted(256, 205, new Vector2(0.5f, 0.5f), (x, y) =>
        {
            float fx = (x - 128f) / 128f, fy = (y - 102.5f) / 102.5f;
            float d = Mathf.Sqrt(fx * fx + fy * fy);
            byte a = (byte)(Mathf.Clamp01(1f - d) * 150f);
            return new Color32(220, 30, 20, a);
        });
    }

    // ------------------------------------------------------------------ TOR-Nacharbeit (wie TrickOrTreat.PoisonMurderPatch)

    private static string _firstKillBefore;
    private static System.Reflection.FieldInfo _firstKillField;

    [HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.MurderPlayer))]
    private static class DemonMurderPatch
    {
        [HarmonyPriority(Priority.First)]
        public static void Prefix([HarmonyArgument(0)] PlayerControl target)
        {
            try
            {
                if (target == null || !DemonVictims.Contains(target.PlayerId)) return;
                _firstKillField ??= AccessTools.Field(AccessTools.TypeByName("TheOtherRoles.TORMapOptions"), "firstKillName");
                _firstKillBefore = _firstKillField?.GetValue(null) as string;
            }
            catch { }
        }

        [HarmonyPriority(Priority.Last)]
        public static void Postfix(PlayerControl __instance, [HarmonyArgument(0)] PlayerControl target)
        {
            try
            {
                if (target == null || __instance == null || __instance.PlayerId != target.PlayerId || !DemonVictims.Contains(target.PlayerId)) return;
                // kein Erstkill-Schild fuer die naechste Runde, kein Bait-Selbstbericht
                if (string.IsNullOrEmpty(_firstKillBefore) && _firstKillField != null) _firstKillField.SetValue(null, "");
                foreach (var k in Bait.active.Keys.ToList()) if (k.player != null && k.player.PlayerId == target.PlayerId) Bait.active.Remove(k);
            }
            catch { }
        }
    }

    // Kein Vanilla-Overlay ("toetet sich selbst"); die Szene spielt MarkVictim. Zuerst, damit die Kostuem-Szenen still bleiben.
    [HarmonyPatch(typeof(KillOverlay), nameof(KillOverlay.ShowKillAnimation), typeof(NetworkedPlayerInfo), typeof(NetworkedPlayerInfo))]
    private static class DemonOverlayPatch
    {
        [HarmonyPriority(Priority.First)]
        public static bool Prefix([HarmonyArgument(0)] NetworkedPlayerInfo killer, [HarmonyArgument(1)] NetworkedPlayerInfo victim)
        {
            try
            {
                if (killer != null && victim != null && killer.PlayerId == victim.PlayerId && DemonVictims.Contains(victim.PlayerId)) return false;
            }
            catch { }
            return true;
        }
    }

    // Geister- und Endbildschirm-Zeile: "killed by <sich selbst>" wird zum Daemon
    [HarmonyPatch(typeof(RoleInfo), nameof(RoleInfo.GetRolesString))]
    private static class DemonRoleStringPatch
    {
        public static void Postfix(PlayerControl p, ref string __result)
        {
            try
            {
                if (DemonVictims.Count == 0 || p == null || __result == null || !DemonVictims.Contains(p.PlayerId) || p.Data == null || !p.Data.IsDead) return;
                int i = __result.IndexOf(" - killed by ", StringComparison.Ordinal);
                if (i >= 0) __result = __result.Substring(0, i) + " - <color=#C0392B>The Demon</color>";
            }
            catch { }
        }
    }
}
