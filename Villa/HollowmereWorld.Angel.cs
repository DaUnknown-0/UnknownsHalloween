// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Angel - die Brunnenfigur im Fountain Court als Weeping Angel (User 2026-10-24, Vorbild Doctor Who).
//
// Solange man hinsieht, steht der Engel mit den Haenden vor den Augen still. Nur wenn der eigene Spieler ihn gerade NICHT
// sieht (ausserhalb des Bildes, ausserhalb der Sicht oder hinter einer Wand), wechselt er selten die Pose: Kopf gedreht mit
// Fratze ("turn") oder ein Stueck vorgerueckt und greifend ("step"). Schaut man wieder hin, steht er so da; nach einer
// Weile ausser Sicht nimmt er die Haende wieder vor die Augen. Tauschbilder "Prop/brunnen_blut/<x>/<y>/turn|step" aus
// dem Konsolen-Atlas (gen_villa PROP_VARIANTS). Rein lokal und kosmetisch: jeder Client entscheidet fuer seine eigene
// Sicht, nichts wird gesendet, Kollision und Spiel bleiben unberuehrt.

using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    private readonly List<PropVar> _angels = new();
    private string _anglePose;                   // null = Haende vor den Augen
    private float _angelUnseenSince = -1f, _angelNextRoll;
    private bool _angelErrorLogged;

    // Mitte der Figur (Plan 31,0 / 31,05 = Brunnenmitte, Figur steht gut 1,5 m darueber im Bild)
    private static readonly Vector2 AngelFeet = new(31.0f - 17.0f, 14.0f - 31.05f);
    private static readonly Vector2 AngelHead = AngelFeet + new Vector2(0f, 1.6f);

    private const float AngelRollEvery = 1.5f;   // so oft wird gewuerfelt, solange er ungesehen ist
    private const float AngelMinUnseen = 3f;     // erst nach so vielen Sekunden ausser Sicht
    private const float AngelMoveChance = 0.12f; // je Wurf: Pose wechseln (selten)
    private const float AngelBackAfter = 9f;     // geaenderte Pose: nach so langer Zeit ungesehen evtl. zurueck
    private const float AngelBackChance = 0.35f;

    private void AngelReset()
    {
        _anglePose = null;
        _angelUnseenSince = -1f;
        _angelNextRoll = 0f;
        foreach (var pv in _angels) Show(pv, null);
    }

    private void AngelTick()
    {
        if (_angels.Count == 0) return;
        float now = Time.time;
        if (MeetingHud.Instance != null || ExileController.Instance != null)
        {
            // im Meeting sieht ihn keiner: danach wieder in der Grundpose
            if (_anglePose != null) SetAngelPose(null);
            _angelUnseenSince = -1f;
            return;
        }
        if (AngelSeen())
        {
            _angelUnseenSince = -1f;
            return;
        }
        if (_angelUnseenSince < 0f) { _angelUnseenSince = now; _angelNextRoll = now + AngelRollEvery; return; }
        if (now < _angelNextRoll) return;
        _angelNextRoll = now + AngelRollEvery;
        float unseen = now - _angelUnseenSince;
        if (unseen < AngelMinUnseen) return;
        var rnd = UnityEngine.Random.value;
        if (_anglePose == null)
        {
            if (rnd < AngelMoveChance) SetAngelPose(UnityEngine.Random.value < 0.65f ? "turn" : "step");
        }
        else if (unseen >= AngelBackAfter && rnd < AngelBackChance) SetAngelPose(null);
    }

    private void SetAngelPose(string pose)
    {
        _anglePose = pose;
        foreach (var pv in _angels) Show(pv, pose);
        if (DiagOnAngel) HalloweenPlugin.Logger.LogInfo($"{LogPrefix} weeping angel: {pose ?? "weeping"}");
    }

    /// <summary>Sieht der eigene Spieler den Engel? Im Bild (mit Rand), bei Lebenden zusaetzlich in Lichtweite und
    /// ohne Wand dazwischen; Geister sehen alles im Bild.</summary>
    private static bool AngelSeen()
    {
        var lp = PlayerControl.LocalPlayer;
        var cam = Camera.main;
        if (lp == null || cam == null) return false;
        bool inView = false;
        foreach (var pt in new[] { AngelFeet, AngelHead })
        {
            var v = cam.WorldToViewportPoint(new Vector3(pt.x, pt.y, 0f));
            if (v.x > -0.05f && v.x < 1.05f && v.y > -0.05f && v.y < 1.05f) { inView = true; break; }
        }
        if (!inView) return false;
        if (lp.Data == null || lp.Data.IsDead) return true;
        var me = lp.GetTruePosition();
        float radius = 6f;
        try { if (ShipStatus.Instance != null) radius = ShipStatus.Instance.CalculateLightRadius(lp.Data) + 0.6f; } catch { }
        foreach (var pt in new[] { AngelFeet, AngelHead })
        {
            if (Vector2.Distance(me, pt) > radius) continue;
            bool blocked = false;
            try { blocked = PhysicsHelpers.AnythingBetween(me, pt, Constants.ShadowMask, false); } catch { }
            if (!blocked) return true;
        }
        return false;
    }

    private static bool DiagOnAngel => Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") == "angel";

    private void AngelError(Exception e)
    {
        if (_angelErrorLogged) return;
        _angelErrorLogged = true;
        HalloweenPlugin.Logger.LogError($"{LogPrefix} weeping angel failed (logged once): {e}");
    }
}
