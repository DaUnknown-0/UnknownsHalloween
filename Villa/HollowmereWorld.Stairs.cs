// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Stairs - Treppen ins Obergeschoss ohne Knopf (17.11., User: "seamless, man laeuft einfach die Treppe hoch").
//
// Das Obergeschoss liegt als eigene Flaeche noerdlich des Hauses (VillaUpper.g.cs, Host-Option 1970). Jede Treppe hat unten eine
// Ausloeselinie auf den Stufen (nur nach Norden ueberschritten) und oben eine am Treppenschacht (nur nach Sueden). Wer sie in
// Gehrichtung ueberschreitet, steht ohne Blende am anderen Ende, x bleibt gleich, die Kamera springt mit (FollowerCamera
// .SnapToTarget, sonst fliegt sie ueber die Karte). Der Ankunftspunkt liegt jeweils 0,7 m hinter der Gegenlinie, damit niemand
// hin und her springt. Die anderen sehen den Wechsel ueber RpcSnapTo wie einen Vent-Ausstieg; ein eigenes RPC braucht es nicht.
// Nicht im Vent, nicht in einem Minispiel, nicht im Meeting, nicht waehrend eines Geheimgangs; Geister nehmen die Treppe auch.
//
// Autotest: UC_HALLOWEEN_DIAG mit "stairs" (laeuft jede Treppe hoch und wieder runter, Fotos unten/oben/zurueck).

using System;
using UnityEngine;
using UnknownsAtlas;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    private (string Key, float X0, float X1, float DownTrigger, float DownArrive, float UpTrigger, float UpArrive)[] _stairs =
        Array.Empty<(string, float, float, float, float, float, float)>();
    private Vector2 _stairPrev;
    private bool _stairHasPrev;
    private float _stairWaitUntil;
    private int _stairUses;

    /// <summary>Treppen dieser Runde (nur mit Obergeschoss, HollowmereMap.WithUpper).</summary>
    internal void SetStairs((string, float, float, float, float, float, float)[] stairs)
        => _stairs = stairs ?? Array.Empty<(string, float, float, float, float, float, float)>();

    private void StairsReset() { _stairHasPrev = false; _stairWaitUntil = 0f; _stairUses = 0; _diagWalk = 0; }

    private void StairsTick()
    {
        if (_stairs.Length == 0) return;
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || lp.Data == null) return;
        DiagWalkStep(lp);
        if (MeetingHud.Instance != null || ExileController.Instance != null || _passing || lp.inVent || lp.walkingToVent
            || Minigame.Instance != null)
        {
            _stairHasPrev = false;
            return;
        }
        var pos = lp.GetTruePosition();
        if (!_stairHasPrev) { _stairPrev = pos; _stairHasPrev = true; return; }
        var prev = _stairPrev;
        _stairPrev = pos;
        if (Time.time < _stairWaitUntil) return;
        foreach (var s in _stairs)
        {
            if (pos.x < s.X0 || pos.x > s.X1) continue;
            // unten auf den Stufen nach Norden ueber die Linie (Welt: y waechst nach Norden)
            if (prev.y < s.DownTrigger && pos.y >= s.DownTrigger && pos.y < s.DownTrigger + 1.5f)
            {
                Climb(lp, new Vector2(pos.x, s.UpArrive), s.Key, "up");
                return;
            }
            // oben im Treppenschacht nach Sueden ueber die Linie
            if (prev.y > s.UpTrigger && pos.y <= s.UpTrigger && pos.y > s.UpTrigger - 1.5f)
            {
                Climb(lp, new Vector2(pos.x, s.DownArrive), s.Key, "down");
                return;
            }
        }
    }

    private void Climb(PlayerControl lp, Vector2 dest, string key, string dir)
    {
        try
        {
            // RpcSnapTo setzt die Transform-Lage; GetTruePosition liegt um den Kollider-Versatz darunter
            var off = lp.GetTruePosition() - (Vector2)lp.transform.position;
            lp.NetTransform.RpcSnapTo(dest - off);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} stairs: snap failed: {e.Message}"); return; }
        try { if (HudManager.InstanceExists && HudManager.Instance.PlayerCam != null) HudManager.Instance.PlayerCam.SnapToTarget(); } catch { }
        _stairPrev = dest;
        _stairWaitUntil = Time.time + 0.35f;
        _diagWalk = 0;                      // Autotest: am anderen Ende stehen bleiben
        _stairUses++;
        float vol = 0.35f;
        AtlasMaps.Sfx("creak", vol);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} stairs {key} {dir}: now at {dest.x:F2}/{dest.y:F2} (uses {_stairUses})");
    }

    // ------------------------------------------------------------------ Autotest "stairs"

    private int _diagWalk;          // +1 = nach Norden laufen, -1 = nach Sueden, 0 = stehen
    private int _diagStair;

    /// <summary>Laufen ohne Tastatur: je Bild ein kleiner Schritt (2,5 m/s) ueber die NetTransform (den Koerper direkt zu
    /// verschieben ueberschreibt das Spiel, Test 17.11.), damit die Treppe wie beim echten Gehen von Bild zu Bild ueberschritten wird.</summary>
    private void DiagWalkStep(PlayerControl lp)
    {
        if (_diagWalk == 0) return;
        try { lp.NetTransform.SnapTo((Vector2)lp.transform.position + new Vector2(0f, _diagWalk * 2.5f * Time.deltaTime)); }
        catch { }
    }

    // Rundgang "uptour" (18.11.): jeden Raum oben und beide Treppenfuesse fotografieren (Weltmeter, Plan x - 17 / 14 - y)
    private static readonly (string Tag, Vector2 Pos)[] TourSpots =
    {
        ("landing", new(0.0f, 23.4f)), ("master", new(10.0f, 22.9f)), ("nursery", new(-10.0f, 23.0f)), ("corridor", new(0.0f, 27.4f)),
        ("attic", new(-10.0f, 32.0f)), ("darkroom", new(-1.0f, 32.0f)), ("bath", new(4.5f, 32.0f)), ("sewing", new(11.0f, 32.0f)),
        ("hall_stairs", new(0.0f, 2.6f)), ("kitchen_stairs", new(-12.0f, 11.6f)), ("fireplace", new(14.6f, -1.8f)), ("study", new(14.6f, -7.6f)),
    };
    private int _tourI;

    private void DiagTour(PlayerControl lp)
    {
        if (_tourI >= TourSpots.Length) { _tourI = 0; _diagTask++; _diagStep = 0; _diagAt = Time.time + 0.5f; return; }
        var s = TourSpots[_tourI];
        if (_diagStep == 0)
        {
            try { lp.NetTransform.RpcSnapTo(s.Pos - (lp.GetTruePosition() - (Vector2)lp.transform.position)); } catch { }
            try { if (HudManager.InstanceExists) HudManager.Instance.PlayerCam.SnapToTarget(); } catch { }
            _diagStep = 1; _diagAt = Time.time + 1.2f;
            return;
        }
        AtlasMaps.Shot("tour", s.Tag);
        _tourI++;
        _diagStep = 0; _diagAt = Time.time + 0.4f;
    }

    private void DiagStairs(PlayerControl lp)
    {
        if (_stairs.Length == 0)
        {
            HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag: stairs: no upper floor in this round (option 1970 off?) - FAIL");
            _diagTask++; _diagStep = 0; return;
        }
        if (_diagStair >= _stairs.Length) { _diagStair = 0; _diagTask++; _diagStep = 0; _diagAt = Time.time + 0.5f; return; }
        var s = _stairs[_diagStair];
        float x = (s.X0 + s.X1) / 2f;
        string tag = $"stairs_{s.Key}";
        var p = lp.GetTruePosition();
        switch (_diagStep)
        {
            case 0:
                Climb(lp, new Vector2(x, s.DownTrigger - 0.7f), s.Key, "diag-start");
                _stairUses--;
                _diagStep = 1; _diagAt = Time.time + 1.0f;
                break;
            case 1:
                AtlasMaps.Shot(tag, "bottom");
                _diagWalk = 1;
                _diagStep = 2; _diagAt = Time.time + 1.2f;
                break;
            case 2:
                _diagWalk = 0;
                bool up = Mathf.Abs(p.y - s.UpArrive) < 2.0f;
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: stairs {s.Key} up: at {p.x:F2}/{p.y:F2}, expected y ~{s.UpArrive:F2} -> {(up ? "PASS" : "FAIL")}");
                _diagStep = 3; _diagAt = Time.time + 0.6f;
                break;
            case 3:
                AtlasMaps.Shot(tag, "top");
                _diagWalk = -1;
                _diagStep = 4; _diagAt = Time.time + 1.4f;
                break;
            case 4:
                _diagWalk = 0;
                bool down = Mathf.Abs(p.y - s.DownArrive) < 2.0f;
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: stairs {s.Key} down: at {p.x:F2}/{p.y:F2}, expected y ~{s.DownArrive:F2} -> {(down ? "PASS" : "FAIL")}");
                _diagStep = 5; _diagAt = Time.time + 0.6f;
                break;
            case 5:
                AtlasMaps.Shot(tag, "back");
                _diagStair++;
                _diagStep = 0; _diagAt = Time.time + 0.5f;
                break;
        }
    }
}
