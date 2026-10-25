// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Ritual - das Pentagramm von Ravenhollow auch in Hollowmere Manor (User 2026-10-25: "an einem Ort, den du
// dir aussuchst"): im Seance Parlour, links vom Seance-Tisch (Welt -4,0 / 10,25, beide Kartengroessen). Ablauf wie auf dem
// Friedhof (GraveyardWorld.Ritual.cs): fuenf Kerzen an den Sternspitzen, lebende Spieler zuenden sie mit "LIGHT" an; brennen
// alle, ruft der Host den Daemon, der 6,66 s in der Mitte steht, und wer ab 2 s im inneren Kreis steht, stirbt (Szene "demon",
// "The Demon" in der Rollenzeile, kein Erstkill-Schild, kein Bait-Bericht: die Patches und Opferliste des Friedhofs).
//
// Platz: 85 % des Friedhofssterns, damit die Kerze an der rechten Spitze 1,15 m Abstand zur Reaktor-Konsole an der linken
// Tischkante (-2,0 / 9,8) haelt und der Todeskreis 1 m davor endet. Der Stern ist hier keine Bodentextur, sondern ein zur
// Laufzeit gemaltes Bodenbild (Kreidekreis in getrocknetem Blut), Atlanten und F9-Fassungen bleiben unberuehrt.
// RPC: Modul 236, Sub 30 Kerze (jeder -> alle), 31 Ritual (Host -> alle), 32 Opfer (Host -> alle).

using System;
using System.Linq;
using Hazel;
using TheOtherRoles;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    internal const byte SubRitualFirst = 30;
    private const byte SubRitualCandle = 30;       // [kerze]    jeder -> alle
    private const byte SubRitualStart = 31;        // -          Host -> alle
    private const byte SubRitualVictim = 32;       // [spieler]  Host -> alle, vor dem Kill

    private static readonly Vector2 RitualCenter = new(-4.0f, 10.25f);
    private const float RitualScale = 0.85f;
    private const float StarRx = 1.52f * RitualScale, StarRy = 1.216f * RitualScale;   // Sternspitzen
    private const float KillRx = 1.1f * RitualScale, KillRy = 0.88f * RitualScale;     // Todeszone (innerer Kreis)
    private const float RitualSecs = 6.66f;
    private const float KillFrom = 2.0f;
    private const float RitualCandleReach = 0.9f;
    private const float RitualPpm = 160f;

    private readonly Vector2[] _ritualCandlePos = new Vector2[5];
    private readonly SpriteRenderer[] _ritualCandleSr = new SpriteRenderer[5];
    private readonly SpriteRenderer[] _ritualCandleGlow = new SpriteRenderer[5];
    private readonly bool[] _ritualLit = new bool[5];
    private SpriteRenderer _demonSr, _ritualFloorGlow;
    private Transform _ritualRoot;
    private float _ritualStart = -1f, _nextRitualKill;
    private bool _ritualMeeting, _ritualErrorLogged;
    private static Sprite _pentagramSprite;

    // ------------------------------------------------------------------ Aufbau

    private void RitualBuild()
    {
        GraveyardWorld.LoadArt();
        _pentagramSprite ??= PaintPentagram();
        // wie auf dem Friedhof: eigene Ebene auf Weltposition 0 und Massstab 1 (der worldRoot haengt am Schiff)
        _ritualRoot = new GameObject("Hollowmere_Ritual").transform;
        _ritualRoot.SetParent(_root, false);
        var ls = _root.lossyScale;
        _ritualRoot.localScale = new Vector3(1f / ls.x, 1f / ls.y, 1f / ls.z);
        _ritualRoot.position = Vector3.zero;
        int layer = _root.gameObject.layer;

        var floor = new GameObject("RitualPentagram") { layer = layer };
        floor.transform.SetParent(_ritualRoot, false);
        floor.transform.localPosition = new Vector3(RitualCenter.x, RitualCenter.y, GraveyardWorld.AtlasMuseumBuilderFloorZ - 1.4f);
        floor.AddComponent<SpriteRenderer>().sprite = _pentagramSprite;

        for (int k = 0; k < 5; k++)
        {
            float a = Mathf.PI / 2f + k * 2f * Mathf.PI * 2f / 5f;
            _ritualCandlePos[k] = RitualCenter + new Vector2(StarRx * Mathf.Cos(a), StarRy * Mathf.Sin(a));
            var go = new GameObject($"RitualCandle_{k}") { layer = layer };
            go.transform.SetParent(_ritualRoot, false);
            go.transform.localPosition = new Vector3(_ritualCandlePos[k].x, _ritualCandlePos[k].y, GraveyardWorld.Depth(_ritualCandlePos[k].y));
            _ritualCandleSr[k] = go.AddComponent<SpriteRenderer>();
            _ritualCandleSr[k].sprite = GraveyardWorld._candleOff;
            _ritualLit[k] = false;
            if (GraveyardWorld._candleGlowSprite != null)
            {
                var g = new GameObject($"RitualCandleGlow_{k}") { layer = layer };
                g.transform.SetParent(go.transform, false);
                g.transform.localPosition = new Vector3(0f, 0.42f, 0.0001f);
                _ritualCandleGlow[k] = g.AddComponent<SpriteRenderer>();
                _ritualCandleGlow[k].sprite = GraveyardWorld._candleGlowSprite;
                g.SetActive(false);
            }
        }
        _ritualStart = -1f;
        _demonSr = _ritualFloorGlow = null;
    }

    private void RitualDestroy()
    {
        if (_ritualRoot != null) Object.Destroy(_ritualRoot.gameObject);
        _ritualRoot = null;
        _demonSr = _ritualFloorGlow = null;
    }

    // ------------------------------------------------------------------ Ablauf

    private void RitualTick()
    {
        if (_ritualRoot == null) return;
        float now = Time.time;
        bool meeting = MeetingHud.Instance != null || ExileController.Instance != null;
        if (meeting && !_ritualMeeting)
        {
            for (int k = 0; k < 5; k++) SetRitualLit(k, false);
            EndRitual();
        }
        _ritualMeeting = meeting;

        var on = GraveyardWorld._candleOn;
        int fi = (int)(now * GraveyardWorld.Fps);
        for (int k = 0; k < 5; k++)
        {
            if (_ritualLit[k] && _ritualCandleSr[k] != null && on != null && on.Length > 0) _ritualCandleSr[k].sprite = on[(fi + k * 3) % on.Length];
            if (_ritualLit[k] && _ritualCandleGlow[k] != null)
                _ritualCandleGlow[k].color = new Color(1f, 1f, 1f, 0.8f + 0.2f * Mathf.Sin(now * 9f + k * 1.7f));
        }

        if (_ritualStart >= 0f)
        {
            float t = now - _ritualStart;
            AnimateDemon(t);
            if (AmHost && t >= KillFrom && t <= RitualSecs && now >= _nextRitualKill)
            {
                _nextRitualKill = now + 0.1f;
                HostRitualKill();
            }
            if (t > RitualSecs + (GraveyardWorld._sink?.Length ?? 0) / GraveyardWorld.Fps) EndRitual(true);
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
            if (_ritualLit[k] || !AtlasMaps.CanReach(_ritualCandlePos[k], RitualCandleReach)) continue;
            int idx = k;
            AtlasMaps.OfferUse("LIGHT", "task_villa_btn_candle.png", () => LightRitualLocal(idx));
            return;
        }
    }

    private void LightRitualLocal(int idx)
    {
        if (_ritualLit[idx] || _ritualStart >= 0f) return;
        SetRitualLit(idx, true);
        SendRitual(SubRitualCandle, w => w.Write((byte)idx));
        HostCheckRitual();
    }

    private void SetRitualLit(int idx, bool lit)
    {
        if (idx < 0 || idx >= 5 || _ritualLit[idx] == lit) return;
        _ritualLit[idx] = lit;
        var on = GraveyardWorld._candleOn;
        if (_ritualCandleSr[idx] != null) _ritualCandleSr[idx].sprite = lit && on != null && on.Length > 0 ? on[0] : GraveyardWorld._candleOff;
        if (_ritualCandleGlow[idx] != null) _ritualCandleGlow[idx].gameObject.SetActive(lit);
        if (lit)
        {
            float vol = 0f;
            try { var lp = PlayerControl.LocalPlayer; if (lp != null) vol = Mathf.Clamp01(1f - Vector2.Distance(lp.GetTruePosition(), _ritualCandlePos[idx]) / 9f); } catch { }
            if (vol > 0.02f) AtlasMaps.Sfx("click", 0.7f * vol);
        }
    }

    private void HostCheckRitual()
    {
        if (!AmHost || _ritualStart >= 0f || _ritualMeeting || _ritualLit.Any(x => !x)) return;
        SendRitual(SubRitualStart, null);
        StartRitual();
    }

    private void StartRitual()
    {
        if (_ritualStart >= 0f || _ritualRoot == null) return;
        _ritualStart = Time.time;
        _nextRitualKill = 0f;
        int layer = _root.gameObject.layer;
        if (_ritualFloorGlow == null)
        {
            var g = new GameObject("RitualFloorGlow") { layer = layer };
            g.transform.SetParent(_ritualRoot, false);
            g.transform.localPosition = new Vector3(RitualCenter.x, RitualCenter.y, GraveyardWorld.AtlasMuseumBuilderFloorZ - 1.5f);
            g.transform.localScale = new Vector3(RitualScale, RitualScale, 1f);
            _ritualFloorGlow = g.AddComponent<SpriteRenderer>();
            _ritualFloorGlow.sprite = GraveyardWorld._floorGlowSprite;
        }
        if (_demonSr == null)
        {
            var d = new GameObject("RitualDemon") { layer = layer };
            d.transform.SetParent(_ritualRoot, false);
            var feet = RitualCenter + new Vector2(0f, -0.25f * RitualScale);
            d.transform.localPosition = new Vector3(feet.x, feet.y, GraveyardWorld.Depth(feet.y));
            _demonSr = d.AddComponent<SpriteRenderer>();
        }
        _ritualFloorGlow.gameObject.SetActive(true);
        _demonSr.gameObject.SetActive(true);
        GraveyardWorld.PlayKnell(0.9f);
        AtlasMaps.Sfx("whoosh", 0.8f);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} pentagram: all candles lit, the demon rises for {RitualSecs:F2} s");
    }

    private void AnimateDemon(float t)
    {
        if (_demonSr == null) return;
        var rise = GraveyardWorld._rise; var idle = GraveyardWorld._idle; var sink = GraveyardWorld._sink;
        Sprite s = null;
        int f = (int)(t * GraveyardWorld.Fps);
        int nRise = rise?.Length ?? 0, nSink = sink?.Length ?? 0;
        if (f < nRise) s = rise[f];
        else if (t <= RitualSecs) s = idle != null && idle.Length > 0 ? idle[(f - nRise) % idle.Length] : (nRise > 0 ? rise[nRise - 1] : null);
        else if (nSink > 0) s = sink[Mathf.Min(nSink - 1, (int)((t - RitualSecs) * GraveyardWorld.Fps))];
        _demonSr.sprite = s;
        if (_ritualFloorGlow != null)
        {
            float pulse = 0.75f + 0.25f * Mathf.Sin(t * 7f);
            float fade = t <= RitualSecs ? Mathf.Clamp01(t / 0.4f) : Mathf.Clamp01(1f - (t - RitualSecs) / 0.6f);
            _ritualFloorGlow.color = new Color(1f, 1f, 1f, pulse * fade);
        }
    }

    private void EndRitual(bool candlesOut = false)
    {
        if (_ritualStart < 0f) return;
        _ritualStart = -1f;
        if (_demonSr != null) _demonSr.gameObject.SetActive(false);
        if (_ritualFloorGlow != null) _ritualFloorGlow.gameObject.SetActive(false);
        if (candlesOut)
        {
            for (int k = 0; k < 5; k++) SetRitualLit(k, false);
            AtlasMaps.Sfx("whoosh", 0.4f);
        }
    }

    private static bool InsideRitualCircle(Vector2 p)
    {
        float dx = (p.x - RitualCenter.x) / KillRx, dy = (p.y - RitualCenter.y) / KillRy;
        return dx * dx + dy * dy <= 1f;
    }

    // ------------------------------------------------------------------ Host: toeten

    private static void HostRitualKill()
    {
        foreach (var p in PlayerControl.AllPlayerControls.ToArray())
        {
            try
            {
                if (p == null || p.Data == null || p.Data.IsDead || p.Data.Disconnected || p.inVent) continue;
                if (!InsideRitualCircle(p.GetTruePosition())) continue;
                byte pid = p.PlayerId;
                SendRitual(SubRitualVictim, w => w.Write(pid));
                GraveyardWorld.MarkVictim(pid);
                bool freeplay = AmongUsClient.Instance != null && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay;
                if (freeplay) p.MurderPlayer(p, MurderResultFlags.Succeeded);
                else Helpers.MurderPlayer(p, p, false);
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} pentagram: the demon took {p.Data.PlayerName}");
            }
            catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} demon kill failed: {e.Message}"); }
        }
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

    internal static void HandleRitualRpc(byte sub, MessageReader reader)
    {
        var w = _current;
        if (sub == SubRitualCandle)
        {
            int idx = reader.ReadByte();
            if (w == null || idx >= 5) return;
            var sender = UCRpc.Sender;
            if (sender == null || sender.Data == null || sender.Data.IsDead) return;     // Geister zuenden nichts an
            w.SetRitualLit(idx, true);
            w.HostCheckRitual();
        }
        else if (sub == SubRitualStart)
        {
            if (w == null || !UCRpc.RequireHost("Hollowmere.Ritual")) return;
            for (int k = 0; k < 5; k++) w.SetRitualLit(k, true);
            w.StartRitual();
        }
        else if (sub == SubRitualVictim)
        {
            byte pid = reader.ReadByte();
            if (!UCRpc.RequireHost("Hollowmere.RitualVictim")) return;
            GraveyardWorld.MarkVictim(pid);
        }
    }

    private void RitualError(Exception e)
    {
        if (_ritualErrorLogged) return;
        _ritualErrorLogged = true;
        HalloweenPlugin.Logger.LogError($"{LogPrefix} pentagram failed (logged once): {e}");
    }

    // ------------------------------------------------------------------ Bodenbild

    /// <summary>Pentagramm in getrocknetem Blut: zwei Ringe um die Spitzen, der Stern (Spitze k zu k+2), leicht ausgefranst.</summary>
    private static Sprite PaintPentagram()
    {
        float rx = StarRx * 1.16f, ry = StarRy * 1.16f;                    // Aussenring
        int w = Mathf.CeilToInt((rx + 0.12f) * 2f * RitualPpm), h = Mathf.CeilToInt((ry + 0.12f) * 2f * RitualPpm);
        float cx = w / 2f, cy = h / 2f;
        var tips = new Vector2[5];
        for (int k = 0; k < 5; k++)
        {
            float a = Mathf.PI / 2f + k * 2f * Mathf.PI / 5f;
            tips[k] = new Vector2(cx + StarRx * RitualPpm * Mathf.Cos(a), cy + StarRy * RitualPpm * Mathf.Sin(a));
        }
        float line = 0.045f * RitualPpm;                                    // halbe Strichbreite in Pixeln
        var ink = new Color32(110, 14, 18, 0);
        return GraveyardWorld.Painted(w, h, new Vector2(0.5f, 0.5f), (x, y) =>
        {
            var p = new Vector2(x + 0.5f, y + 0.5f);
            float d = float.MaxValue;
            for (int k = 0; k < 5; k++) d = Mathf.Min(d, SegDist(p, tips[k], tips[(k + 2) % 5]));
            float ex = (p.x - cx) / RitualPpm, ey = (p.y - cy) / RitualPpm;
            float e1 = Mathf.Sqrt(ex * ex / (rx * rx) + ey * ey / (ry * ry));
            float e2 = Mathf.Sqrt(ex * ex / (StarRx * StarRx * 1.03f) + ey * ey / (StarRy * StarRy * 1.03f));
            float ringScale = Mathf.Min(rx, ry) * RitualPpm;
            d = Mathf.Min(d, Mathf.Abs(e1 - 1f) * ringScale);
            d = Mathf.Min(d, Mathf.Abs(e2 - 1f) * ringScale * 0.9f + 0.6f);
            float a = Mathf.Clamp01(line + 1f - d);
            if (a <= 0f) return new Color32(0, 0, 0, 0);
            float n = Mathf.PerlinNoise(x * 0.09f, y * 0.09f);                // getrocknet, nicht ueberall gleich deckend
            return new Color32(ink.r, ink.g, ink.b, (byte)(a * (150f + 90f * n)));
        });
    }

    private static float SegDist(Vector2 p, Vector2 a, Vector2 b)
    {
        var ab = b - a;
        float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / Mathf.Max(1e-4f, ab.sqrMagnitude));
        return Vector2.Distance(p, a + ab * t);
    }
}
