// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// GraveyardWorld - die Mechaniken von Ravenhollow Cemetery (2026-10-17). Haengt ueber AtlasMapDef.World
// (IAtlasMapWorld) an Atlas: OnBuilt nach dem Kartenbau, Tick jeden Frame, VisionFactor in der Lichtberechnung,
// OnDestroy beim Abbau. Alles laeuft lokal auf jedem Client und haengt nur am Zustand, den das Spiel ohnehin
// synchronisiert (Sabotagen), also kein eigenes RPC.
//
//   Nebel:        weiche Nebelbaenke ziehen mit dem Wind ueber die Karte (vor den Spielern, schwach deckend).
//                 Option 1990 (Light / Thick / Off).
//   Totenglocke:  waehrend der Reaktor-Sabotage ("Death Knell") schlaegt alle 2,8 s die Glocke; jeder Schlag
//                 drueckt kurz die Sicht (Option 1992). Der Klang wird zur Laufzeit synthetisiert (Glockenpartiale).
//   Miasma:       waehrend der Sauerstoff-Sabotage faerbt sich der Nebel giftgruen und wird dichter, die Sicht sinkt
//                 auf den Wert von Option 1991.
//   Laternen aus: bei der Licht-Sabotage zeigen Laternenpfaehle und Kandelaber ihr erloschenes Tauschbild
//                 ("Prop/<Art>/<x>/<y>/off" im Konsolen-Atlas, tools/graveyard_art3.py).
//   Atmosphaere:  ab und zu ein Rabenschrei oder ein Kauz in der Ferne.
//   Pentagramm:   Easter Egg an den Waechtersteinen (GraveyardWorld.Ritual.cs, 2026-10-24), eigenes RPC.

using System;
using System.Collections.Generic;
using System.Globalization;
using TheOtherRoles;
using UnityEngine;
using UnknownsAtlas;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

internal sealed partial class GraveyardWorld : IAtlasMapWorld
{
    private const string LogPrefix = "[Halloween/Graveyard]";
    private const float KnellEvery = 2.8f;

    public static CustomOption Fog, MiasmaVision, KnellDarkens;
    private static readonly string[] FogChoices = { "Light", "Thick", "Off" };
    // 20.10.: Light 0,19 war im Spiel kaum zu sehen (Spitzendeckung effektiv ~0,12 nach Bankfaktor, Atmen, Texturprofil)
    private static readonly float[] FogAlpha = { 0.34f, 0.52f, 0f };
    private static readonly string[] MiasmaChoices = { "75%", "60%", "90%", "Off" };
    private static readonly float[] MiasmaFactors = { 0.75f, 0.6f, 0.9f, 1f };

    private readonly AtlasMapDef _d;
    private Transform _root;

    private sealed class Bank { public SpriteRenderer Sr; public Vector2 Pos, Vel; public float Size, Alpha, Phase; }
    private readonly List<Bank> _banks = new();
    private static Texture2D _fogTex;
    private static Sprite _fogSprite;
    private static AudioClip _bellClip, _cawClip;

    private sealed class PropVar { public SpriteRenderer Sr; public Sprite Orig, Off; }
    private readonly List<PropVar> _lamps = new();
    private bool _lampsOff;

    private float _miasma, _knellPulse, _nextKnell, _nextAmbient;

    public GraveyardWorld(AtlasMapDef d) { _d = d; }

    internal static void Init()
    {
        try
        {
            var g = CustomOption.CustomOptionType.General;
            Fog = CustomOption.Create(1990, g, "Ravenhollow Fog", FogChoices, null, true, null, "Ravenhollow Cemetery");
            MiasmaVision = CustomOption.Create(1991, g, "Miasma Vision", MiasmaChoices);
            KnellDarkens = CustomOption.Create(1992, g, "Death Knell Dims Vision", true);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} options failed: {e}"); }
    }

    private static int Sel(CustomOption o, int max) { try { return o == null ? 0 : Mathf.Clamp(o.getSelection(), 0, max - 1); } catch { return 0; } }
    private static float FogA => FogAlpha[Sel(Fog, FogAlpha.Length)];
    private static float MiasmaF => MiasmaFactors[Sel(MiasmaVision, MiasmaFactors.Length)];
    private static bool KnellOn { get { try { return KnellDarkens == null || KnellDarkens.getBool(); } catch { return true; } } }

    // ------------------------------------------------------------------ IAtlasMapWorld

    public void OnBuilt(Transform worldRoot)
    {
        _root = worldRoot;
        _banks.Clear();
        _miasma = _knellPulse = 0f;
        _nextKnell = 0f;
        _nextAmbient = Time.time + UnityEngine.Random.Range(8f, 20f);
        try { MakeFog(); } catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} fog failed: {e.Message}"); }
        CollectLamps("laternenpfahl");
        CollectLamps("kandelaber");
        _lampsOff = false;
        try { RitualBuild(); } catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} ritual failed: {e.Message}"); }
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} world ready: fog banks {_banks.Count} (alpha {FogA:F2}), lamps {_lamps.Count}, miasma vision {MiasmaF:P0}, knell dims {KnellOn}");
    }

    public void Tick(float dt)
    {
        float now = Time.time;
        try { RitualTick(dt); } catch (Exception e) { RitualError(e); }
        bool reactor = false, oxy = false, lights = false;
        try
        {
            var ship = ShipStatus.Instance;
            if (ship != null && MeetingHud.Instance == null)
            {
                if (ship.Systems.ContainsKey(SystemTypes.Reactor)) { var r = ship.Systems[SystemTypes.Reactor].TryCast<ReactorSystemType>(); reactor = r != null && r.IsActive; }
                if (ship.Systems.ContainsKey(SystemTypes.LifeSupp)) { var o = ship.Systems[SystemTypes.LifeSupp].TryCast<LifeSuppSystemType>(); oxy = o != null && o.IsActive; }
                if (ship.Systems.ContainsKey(SystemTypes.Electrical)) { var s = ship.Systems[SystemTypes.Electrical].TryCast<SwitchSystem>(); lights = s != null && s.ActualSwitches != s.ExpectedSwitches; }
            }
        }
        catch { }

        // Totenglocke
        if (reactor)
        {
            if (now >= _nextKnell)
            {
                _nextKnell = now + KnellEvery;
                _knellPulse = 1f;
                PlayClip(ref _bellClip, "ravenhollow_knell", SynthBell, 0.75f);
            }
        }
        else _nextKnell = 0f;
        _knellPulse = Mathf.MoveTowards(_knellPulse, 0f, dt / 0.7f);

        // Miasma
        _miasma = Mathf.MoveTowards(_miasma, oxy ? 1f : 0f, dt * 0.5f);
        FogTick(dt);

        // Laternen
        if (lights != _lampsOff)
        {
            _lampsOff = lights;
            foreach (var pv in _lamps)
                if (pv.Sr != null) pv.Sr.sprite = lights && pv.Off != null ? pv.Off : pv.Orig;
            if (lights) AtlasMaps.Sfx("whoosh", 0.35f);
        }

        // Rabenschrei, Kauz
        if (now >= _nextAmbient)
        {
            _nextAmbient = now + UnityEngine.Random.Range(22f, 48f);
            if (MeetingHud.Instance == null)
            {
                if (UnityEngine.Random.value < 0.65f) PlayClip(ref _cawClip, "ravenhollow_caw", SynthCaw, 0.22f);
                else AtlasMaps.Sfx("owl", 0.18f);
            }
        }
    }

    public float VisionFactor(Vector2 pos)
    {
        float f = 1f;
        if (_miasma > 0f) f *= Mathf.Lerp(1f, MiasmaF, _miasma);
        if (_knellPulse > 0f && KnellOn) f *= 1f - 0.3f * Mathf.SmoothStep(0f, 1f, _knellPulse);
        return f;
    }

    public void OnDestroy()
    {
        foreach (var b in _banks) if (b.Sr != null) Object.Destroy(b.Sr.gameObject);
        _banks.Clear();
        _lamps.Clear();
        RitualDestroy();
    }

    // ------------------------------------------------------------------ Nebel

    private void MakeFog()
    {
        if (FogA <= 0f || _root == null) return;
        if (_fogSprite == null)
        {
            const int N = 128;
            _fogTex = new Texture2D(N, N, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave, wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[N * N];
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float u = (x + 0.5f) / N * 2f - 1f, v = (y + 0.5f) / N * 2f - 1f;
                    float r = Mathf.Sqrt(u * u + v * v * 1.6f);
                    float n = Mathf.PerlinNoise(x * 0.05f + 3.1f, y * 0.05f + 7.7f) * 0.6f + Mathf.PerlinNoise(x * 0.12f, y * 0.12f + 2f) * 0.4f;
                    float a = Mathf.Clamp01(1f - r) * Mathf.Clamp01(0.35f + n);
                    a = a * a * (3f - 2f * a);
                    px[y * N + x] = new Color32(255, 255, 255, (byte)(a * 255f));
                }
            _fogTex.SetPixels32(px);
            _fogTex.Apply();
            _fogSprite = Sprite.Create(_fogTex, new Rect(0, 0, N, N), new Vector2(0.5f, 0.5f), N);
            _fogSprite.hideFlags |= HideFlags.HideAndDontSave;
        }
        int layer = _root.gameObject.layer;
        // a STABLE hash: string.GetHashCode is random per process under .NET 6, so every client laid the
        // banks somewhere else and one player stood in thick fog where another stood free (audit 21.10.)
        int seed = unchecked((int)2166136261);
        foreach (char ch in _d.Key ?? "") seed = unchecked((seed ^ ch) * 16777619);
        var rnd = new System.Random(seed ^ 0x5eed);
        float W = _d.MaxX - _d.MinX, H = _d.MaxY - _d.MinY;
        int count = 22;
        for (int i = 0; i < count; i++)
        {
            var go = new GameObject($"Ravenhollow_Fog_{i}") { layer = layer };
            go.transform.SetParent(_root, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = _fogSprite;
            sr.sortingOrder = 400;
            var b = new Bank
            {
                Sr = sr,
                Pos = new Vector2(_d.MinX + (float)rnd.NextDouble() * W, _d.MinY + (float)rnd.NextDouble() * H),
                Vel = new Vector2(0.18f + (float)rnd.NextDouble() * 0.16f, ((float)rnd.NextDouble() - 0.5f) * 0.06f),
                Size = 6f + (float)rnd.NextDouble() * 6f,
                Alpha = 0.6f + (float)rnd.NextDouble() * 0.4f,
                Phase = (float)rnd.NextDouble() * 6.28f,
            };
            go.transform.localScale = new Vector3(b.Size * 1.6f, b.Size, 1f);
            _banks.Add(b);
        }
        FogTick(0f);
    }

    private void FogTick(float dt)
    {
        if (_banks.Count == 0) return;
        float baseA = FogA;
        float t = Time.time;
        var fogCol = new Color(0.78f, 0.84f, 0.88f);
        var miasmaCol = new Color(0.55f, 0.86f, 0.32f);
        var col = Color.Lerp(fogCol, miasmaCol, _miasma);
        float aMul = Mathf.Lerp(1f, 2.2f, _miasma);
        float pad = 8f;
        foreach (var b in _banks)
        {
            if (b.Sr == null) continue;
            b.Pos += b.Vel * dt * Mathf.Lerp(1f, 0.4f, _miasma);
            if (b.Pos.x > _d.MaxX + pad) b.Pos.x = _d.MinX - pad;
            if (b.Pos.y > _d.MaxY + pad) b.Pos.y = _d.MinY - pad;
            if (b.Pos.y < _d.MinY - pad) b.Pos.y = _d.MaxY + pad;
            float breathe = 0.75f + 0.25f * Mathf.Sin(t * 0.21f + b.Phase);
            b.Sr.transform.position = new Vector3(b.Pos.x, b.Pos.y, -3f);
            b.Sr.color = new Color(col.r, col.g, col.b, Mathf.Clamp01(baseA * b.Alpha * breathe * aMul));
        }
    }

    // ------------------------------------------------------------------ Laternen

    private void CollectLamps(string kind)
    {
        foreach (var p in AtlasMaps.Props(kind))
        {
            if (p.Renderer == null || p.Index < 0 || p.Index >= _d.Props.Length) continue;
            var def = _d.Props[p.Index];
            string key = $"Prop/{def.Kind}/{def.WorldX.ToString("F3", CultureInfo.InvariantCulture)}/{def.WorldY.ToString("F3", CultureInfo.InvariantCulture)}/off";
            var off = AtlasMaps.SpriteFor(key);
            if (off == null) HalloweenPlugin.Logger.LogWarning($"{LogPrefix} no 'off' sprite for {key}");
            _lamps.Add(new PropVar { Sr = p.Renderer, Orig = p.Renderer.sprite, Off = off });
        }
    }

    // ------------------------------------------------------------------ Klaenge (zur Laufzeit synthetisiert)

    private const int Rate = 44100;

    private static void PlayClip(ref AudioClip clip, string name, Func<float[]> synth, float vol)
    {
        try
        {
            if (clip == null)
            {
                var s = synth();
                clip = AudioClip.Create(name, s.Length, 1, Rate, false);
                clip.hideFlags |= HideFlags.HideAndDontSave;
                clip.SetData(s, 0);
            }
            SoundManager.Instance.PlaySound(clip, false, vol);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} sound {name} failed: {e.Message}"); }
    }

    /// <summary>Grosse Kirchenglocke (G2): Hum, Prime, Moll-Terz, Quinte, Nominal und Obertoene mit eigenen
    /// Abklingzeiten, kurzer Anschlag aus gefiltertem Rauschen, leichte Schwebung.</summary>
    private static float[] SynthBell()
    {
        const float f0 = 98f;
        (float r, float a, float d)[] parts = { (0.5f, 0.55f, 0.9f), (1f, 0.75f, 1.4f), (1.19f, 0.5f, 2.0f), (1.5f, 0.35f, 2.6f),
                                                (2f, 0.55f, 3.2f), (2.51f, 0.22f, 4.5f), (2.99f, 0.16f, 5.5f), (4.17f, 0.1f, 7f), (5.43f, 0.06f, 9f) };
        int n = (int)(Rate * 4.2f);
        var s = new float[n];
        var rnd = new System.Random(7);
        float y = 0f;
        for (int i = 0; i < n; i++)
        {
            float t = (float)i / Rate;
            float v = 0f;
            foreach (var p in parts)
            {
                float f = f0 * p.r;
                v += p.a * Mathf.Exp(-t * p.d) * Mathf.Sin(2f * Mathf.PI * f * t) * (1f + 0.04f * Mathf.Sin(2f * Mathf.PI * 1.3f * t));
            }
            if (t < 0.03f) { y += 0.3f * ((float)(rnd.NextDouble() * 2 - 1) - y); v += y * (1f - t / 0.03f) * 1.5f; }
            s[i] = v * Mathf.Min(1f, t / 0.004f);
        }
        float max = 0.001f;
        foreach (var v in s) max = Mathf.Max(max, Mathf.Abs(v));
        for (int i = 0; i < n; i++) s[i] = s[i] / max * 0.85f;
        return s;
    }

    /// <summary>Rabenschrei: zwei raue "Kraah", Saegezahn mit fallender Tonhoehe plus Rauschen, Formant ueber
    /// einen einfachen Tiefpass.</summary>
    private static float[] SynthCaw()
    {
        int n = (int)(Rate * 0.95f);
        var s = new float[n];
        var rnd = new System.Random(11);
        float phase = 0f, lp = 0f;
        for (int i = 0; i < n; i++)
        {
            float t = (float)i / Rate;
            float local = t < 0.38f ? t : t - 0.5f;
            if (t >= 0.38f && t < 0.5f) { s[i] = 0f; continue; }
            float len = 0.36f;
            if (local < 0f || local > len) { s[i] = 0f; continue; }
            float k = local / len;
            float f = Mathf.Lerp(720f, 520f, k);
            phase += f / Rate;
            float saw = 2f * (phase - Mathf.Floor(phase)) - 1f;
            float noise = (float)(rnd.NextDouble() * 2 - 1);
            float raw = saw * 0.7f + noise * 0.45f;
            lp += 0.35f * (raw - lp);
            float env = Mathf.Sin(Mathf.PI * Mathf.Min(1f, k * 1.3f)) * (1f - 0.3f * k);
            s[i] = (raw * 0.4f + lp * 0.6f) * env * 0.6f;
        }
        return s;
    }
}
