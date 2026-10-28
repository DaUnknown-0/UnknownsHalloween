// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Curios - zwei kleine geheime Interaktionen (Feedback DrSuspect 28.10., n75/n85), rein zur Stimmung:
// - Phonograph im Seance Parlour: "PLAY" spielt eine von drei eigenen kurzen Melodien (Spieluhr, Walzer, Trauermarsch) mit
//   Knistern, fuer alle in Hoerweite.
// - Funktisch im Radio Room: "TUNE" gibt Rauschen, Morsepiepen und dazwischen eine fluesternde Stimme (die Geisterzeile der
//   Beschwoerung), ebenfalls fuer alle in Hoerweite. Kein Mikrofon (die Idee mit eigener Aufnahme war ein "vielleicht").
// Beides hat 20 s Abklingzeit je Spieler. RPC Modul 236 Sub 41 [was][variante] (jeder -> alle).

using System;
using System.Collections.Generic;
using Hazel;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    private const byte SubCurio = 41;
    private const float CurioReach = 1.0f, CurioCooldown = 20f;
    // Weltmeter: vor dem Phonographen (Plan 22,2 / 6,8) und vor dem Funktisch (Plan 24,4 / 1,25)
    private static readonly Vector2 PhonographSpot = new(22.0f - 17f, 14f - 6.8f);
    private static readonly Vector2 RadioSpot = new(24.4f - 17f, 14f - 1.25f);
    private float _curioReady;
    private static readonly Dictionary<string, AudioClip> CurioClips = new();

    private void CurioTick()
    {
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || lp.Data == null || lp.Data.IsDead || MeetingHud.Instance != null) return;
        bool ready = Time.time >= _curioReady;
        if (AtlasMaps.CanReach(PhonographSpot, CurioReach))
            AtlasMaps.OfferUse(ready ? "PLAY" : $"WAIT {Mathf.CeilToInt(_curioReady - Time.time)}", "task_villa_btn_secret.png", () => UseCurio(0), enabled: ready);
        else if (AtlasMaps.CanReach(RadioSpot, CurioReach))
            AtlasMaps.OfferUse(ready ? "TUNE" : $"WAIT {Mathf.CeilToInt(_curioReady - Time.time)}", "task_villa_btn_secret.png", () => UseCurio(1), enabled: ready);
    }

    private void UseCurio(byte what)
    {
        if (Time.time < _curioReady) return;
        _curioReady = Time.time + CurioCooldown;
        byte variant = (byte)UnityEngine.Random.Range(0, 3);
        try
        {
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubCurio); w.Write(what); w.Write(variant);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch { }
        PlayCurio(what, variant);
    }

    private static void PlayCurio(byte what, byte variant)
    {
        try
        {
            var lp = PlayerControl.LocalPlayer;
            var at = what == 0 ? PhonographSpot : RadioSpot;
            float vol = lp == null ? 1f : Mathf.Clamp01(1.1f - Vector2.Distance(lp.GetTruePosition(), at) / 14f);
            if (vol <= 0.05f || SoundManager.Instance == null) return;
            var clip = what == 0 ? Phonograph(variant) : Radio(variant);
            if (clip != null) SoundManager.Instance.PlaySound(clip, false, vol);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} curio sound failed: {e.Message}"); }
    }

    internal static bool HandleCurioRpc(byte sub, MessageReader reader)
    {
        if (sub != SubCurio) return false;
        byte what = reader.ReadByte(), variant = reader.ReadByte();
        if (what <= 1 && variant <= 2) PlayCurio(what, variant);
        return true;
    }

    // ------------------------------------------------------------------ Klaenge (synthetisch)

    private static AudioClip Phonograph(int v)
    {
        string key = "phono" + v;
        if (CurioClips.TryGetValue(key, out var c) && c != null) return c;
        // eigene Melodien (Halbtoene ueber A3); Notenlaenge in Schlaegen
        (int Semi, float Beats)[] tune = v switch
        {
            0 => new[] { (12, 1f), (15, 1f), (19, 1f), (24, 2f), (22, 1f), (19, 1f), (15, 2f), (17, 1f), (14, 1f), (12, 3f) },          // Spieluhr
            1 => new[] { (7, 1f), (12, 1f), (12, 1f), (11, 1f), (14, 1f), (14, 1f), (12, 1f), (16, 1f), (16, 1f), (14, 3f) },          // Walzer (3/4)
            _ => new[] { (0, 1.5f), (0, 0.5f), (0, 1f), (3, 1.5f), (2, 0.5f), (2, 1f), (0, 1f), (-1, 1f), (0, 3f) },                    // Trauermarsch
        };
        float beat = v == 1 ? 0.32f : v == 0 ? 0.28f : 0.5f;
        float len = 0f; foreach (var n in tune) len += n.Beats * beat;
        len += 1.2f;
        var rnd = new System.Random(40 + v);
        var starts = new List<(float T, float F, float D)>();
        float at = 0.4f;
        foreach (var n in tune) { starts.Add((at, 220f * Mathf.Pow(2f, n.Semi / 12f), n.Beats * beat)); at += n.Beats * beat; }
        c = TreatFx.MakeClip(key, len, (t, L) =>
        {
            float s = 0f;
            foreach (var (st, f, d) in starts)
            {
                float u = t - st;
                if (u < 0f || u > d + 0.9f) continue;
                float env = Mathf.Exp(-u * (v == 0 ? 3.5f : 2.2f)) * Mathf.Clamp01(u / 0.005f);
                s += env * (Mathf.Sin(2 * Mathf.PI * f * u) + 0.3f * Mathf.Sin(4 * Mathf.PI * f * u) + (v == 0 ? 0.2f * Mathf.Sin(6.1f * Mathf.PI * f * u) : 0f));
            }
            // Grammophon: Bandbegrenzung grob nachgeahmt durch Leiern, dazu Knistern und Rauschen
            float wow = 1f + 0.004f * Mathf.Sin(2 * Mathf.PI * 0.55f * t);
            float crackle = rnd.NextDouble() > 0.9993 ? (float)(rnd.NextDouble() * 2 - 1) * 0.8f : 0f;
            float hiss = (float)(rnd.NextDouble() * 2 - 1) * 0.025f;
            float fade = Mathf.Clamp01(t / 0.3f) * Mathf.Clamp01((L - t) / 0.8f);
            return (0.32f * s * wow + crackle + hiss) * fade;
        });
        CurioClips[key] = c;
        return c;
    }

    private static AudioClip Radio(int v)
    {
        string key = "radio" + v;
        if (CurioClips.TryGetValue(key, out var c) && c != null) return c;
        var whisper = SummonClip("ghost");
        float[] wdata = null; int wrate = 22050;
        if (whisper != null)
        {
            wdata = new float[whisper.samples * whisper.channels];
            whisper.GetData(wdata, 0);
            wrate = whisper.frequency;
        }
        var rnd = new System.Random(77 + v);
        float wStart = 1.2f + v * 0.4f;
        float wLen = wdata != null ? wdata.Length / (float)wrate : 0f;
        float len = Mathf.Max(3.5f, wStart + wLen + 0.8f);
        // Morse: kurze und lange Piepser vor der Stimme (zufaellige Folge je Variante)
        var beeps = new List<(float T, float D)>();
        float bt = 0.3f;
        for (int i = 0; i < 6; i++) { float d = rnd.NextDouble() > 0.5 ? 0.18f : 0.06f; beeps.Add((bt, d)); bt += d + 0.07f; }
        float lp = 0f;
        c = TreatFx.MakeClip(key, len, (t, L) =>
        {
            float n = (float)(rnd.NextDouble() * 2 - 1);
            lp += (n - lp) * 0.35f;                                         // Rauschen, leicht gedaempft
            float tuning = 0.5f + 0.5f * Mathf.Sin(2 * Mathf.PI * 0.4f * t);
            float s = lp * 0.22f * (0.5f + 0.5f * tuning);
            foreach (var (bs, bd) in beeps) if (t >= bs && t < bs + bd) s += 0.25f * Mathf.Sin(2 * Mathf.PI * 760f * t);
            if (wdata != null && t >= wStart)
            {
                int i = (int)((t - wStart) * wrate);
                if (i < wdata.Length) s += wdata[i] * 0.85f * (0.75f + 0.25f * Mathf.Sin(2 * Mathf.PI * 7f * t));
            }
            return s * Mathf.Clamp01(t / 0.1f) * Mathf.Clamp01((L - t) / 0.4f);
        });
        CurioClips[key] = c;
        return c;
    }
}
