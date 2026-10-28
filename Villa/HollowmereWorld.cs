// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld - die Mechaniken von Hollowmere Manor (Audit 15.10., Schritt 4): Geheimgaenge,
// Mitternachtsuhr, Kerzen und Dunkelheit. Haengt ueber AtlasMapDef.World (IAtlasMapWorld, Atlas-API 2)
// an Atlas: OnBuilt nach dem Kartenbau, Tick jeden Frame der Runde, VisionFactor in der Lichtberechnung,
// OnDestroy beim Abbau. Die Daten (Secrets, Clock, DarkRooms) kommen aus den generierten Klassen
// (tools/gen_villa.py aus villa_layout.SECRETS/CLOCK/DARK).
//
// Geheimgaenge: Use-Knopf "ENTER" einen Schritt vor dem Moebel (lebende Spieler aller Teams, nicht im Vent,
// nichts offen). Der Durchgang dauert 1,2 s: eigene schwarze Flaeche blendet ein, nach 0,5 s steht der
// Spieler am Ausgang (RpcSnapTo, wie der Vent-Ausstieg), dann blendet sie aus. Jeder Durchgang geht als
// RPC an alle (Modul 236, Sub 2): das Moebel am Eingang bewegt sich sichtbar (Regal dreht, Teppich lupft,
// Klappe ruckelt) und ist in Hoerweite zu hoeren. Abklingzeit je Spieler (Option 1963), damit niemand im
// Kreis flieht. Das ist eine Alternative zu Vents, die auch Crewmates hilft.
//
// Mitternachtsuhr: der Host zaehlt (Option 1964, Standard 90 s; steht waehrend Meeting, Rauswurf und
// kritischer Sabotage), 5 s vorher Vorwarnung (Sub 3/0: Ticken, Pendel schwingt), dann der Schlag (Sub 3/1):
// drei Gongs, 3 s Lichtflackern (Sichtradius und Scheinwerfer), alle offenen Tueren fuer n Sekunden zu
// (Option 1965; der Host schaltet die Tueren direkt, SetDoorway + Doors-System dirty, damit die Tuer-
// Abklingzeiten der Impostor unberuehrt bleiben), und die Portraets der Galerie blicken in Richtung der
// zuletzt gemeldeten Leiche (Option 1966, Prefix auf PlayerControl.StartMeeting merkt sich die Leiche).
//
// Tauschbilder: der Generator legt je Prop Varianten in den Konsolen-Atlas ("Prop/<Art>/<x>/<y>/<Variante>",
// gleiche Groesse, Anker unten links); hier wird nur das Sprite des Renderers getauscht.
//
// Kerzen und Dunkelheit: in den dunklen Raeumen (DarkRooms) sieht man weniger (Option 1967). Die Kandelaber
// starten erloschen; Use-Knopf "LIGHT" zuendet einen an (jeder an alle, Sub 4), er brennt n Sekunden (Option
// 1968) und hebt im Umkreis die Dunkelheit auf. Bei der Licht-Sabotage gehen die Scheinwerfer aus, und in
// Kerzennaehe gilt fuer die Crew wieder der volle Radius (Ausgleich gegen TORs Lerp(Min, Max, Schalter)).
// Impostor koennen brennende Kerzen ausblasen ("BLOW OUT", Abklingzeit Option 1969; Empfaenger pruefen, dass
// der Absender Impostor ist). Alles nur ueber den Sichtradius (User 15.10.), Uebergaenge weich (2/s).
//
// Optionen (ID-Registry.md, Block 1960-1969): 1962 Secret Passages, 1963 Secret Passage Cooldown, 1964 Midnight
// Clock, 1965 Clock Doors Shut, 1966 Portrait Hint, 1967 Dark Room Vision, 1968 Candle Burn Time, 1969 Candle
// Blow-Out Cooldown.
//
// Autotest: UC_HALLOWEEN_DIAG mit "secret:<key>[+<key>...]", "clock" und/oder "candle" (nur im Atlas-Autotest,
// Freeplay mit ForceMap); laeuft nach den Ansichtsfotos von Atlas, Fotos nach AtlasShots/task_secret_*.png,
// task_clock_*.png, task_candle_*.png, am Ende "[Halloween/Villa] diag: all done".

using System;
using System.Collections.Generic;
using System.Globalization;
using HarmonyLib;
using TheOtherRoles;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld : IAtlasMapWorld
{
    private const string LogPrefix = "[Halloween/Villa]";
    internal const byte SubSecret = 2;                 // [player][secret][dir]  jeder -> alle (Animation, Ton)
    internal const byte SubClock = 3;                  // [phase] 0 Vorwarnung, 1 Schlag  Host -> alle
    internal const byte SubCandle = 4;                 // [kerze][an]  jeder -> alle (aus nur von Impostorn)
    private const float PassSecs = 1.2f, SnapAt = 0.5f, Reach = 1.0f, WarnSecs = 5f, CandleRadius = 3.5f;

    public static CustomOption Secrets, SecretCooldown, ClockInterval, ClockDoors, PortraitHint, DarkVision, CandleBurn, BlowOut;
    private static readonly string[] ClockChoices = { "90 s", "60 s", "120 s", "180 s", "Off" };
    private static readonly float[] ClockSeconds = { 90f, 60f, 120f, 180f, 0f };
    // Auswahl statt Kommazahl: TORs Create(float) akkumuliert Schrittfehler (Memory "TOR-Float-Options-Falle")
    private static readonly string[] DarkChoices = { "50%", "40%", "60%", "70%", "Off" };
    private static readonly float[] DarkFactors = { 0.5f, 0.4f, 0.6f, 0.7f, 1f };
    private static readonly string[] BlowChoices = { "30 s", "20 s", "45 s", "60 s", "Off" };
    private static readonly float[] BlowSeconds = { 30f, 20f, 45f, 60f, -1f };
    private static HollowmereWorld _current;           // die Welt der laufenden Runde (RPC-Handler, Patches)
    private static float _secretWaitUntil;             // lokale Abklingzeit (Reset in OnBuilt)
    private static Vector2? _lastBody;                 // zuletzt gemeldete Leiche (Prefix StartMeeting)

    private readonly AtlasMapDef _d;
    private readonly (string Key, string Prop, Vector2 Entry, Vector2 Exit, bool Both)[] _secrets;
    private readonly Vector2 _clock;
    private readonly string[] _darkRooms;
    private Transform _root;

    // Moebel je Geheimgang: Renderer mit Ruhelage (Skalierung, Position) fuer die Bewegung beim Durchgang
    private readonly List<(SpriteRenderer Sr, Vector3 Scale, Vector3 Pos, float Width)>[] _secretProps;
    private readonly float[] _animAt;

    // Props mit Tauschbildern
    private sealed class PropVar
    {
        public SpriteRenderer Sr; public Sprite Orig; public readonly Dictionary<string, Sprite> Vars = new();
        public Vector2 Pos; public string Shown;
    }
    private readonly List<PropVar> _clockProps = new(), _portraits = new(), _spots = new(), _candles = new(), _armors = new();

    // Kerzen: Brennende bis, dunkle Raumflaechen, weiche Uebergaenge, eigene Ausblas-Abklingzeit
    private float[] _burnUntil = Array.Empty<float>();
    private readonly List<Vector2[]> _darkAreas = new();
    private float _dark, _cand, _blowWaitUntil;

    // laufender Durchgang des lokalen Spielers
    private bool _passing, _snapped;
    private float _passT;
    private Vector2 _passTo;
    private GameObject _cover;
    private SpriteRenderer _coverSr;
    private Texture2D _coverTex;

    // Uhr
    private float _clockAt = -1f, _doorsOpenAt, _flickerUntil, _pendulumUntil, _portraitShakeAt = -10f, _lastStrike = -1f;
    private int _strikes;
    private bool _warned;
    private readonly List<PlainDoor> _shut = new();
    private readonly List<(float At, string Clip, float Vol)> _sounds = new();

    internal static void Init()
    {
        try
        {
            Secrets = CustomOption.Create(1962, CustomOption.CustomOptionType.General, "Secret Passages", true, null, false, null, "Hollowmere Manor");
            SecretCooldown = CustomOption.Create(1963, CustomOption.CustomOptionType.General, "Secret Passage Cooldown", 10f, 0f, 30f, 5f, Secrets);
            ClockInterval = CustomOption.Create(1964, CustomOption.CustomOptionType.General, "Midnight Clock", ClockChoices, null, false, null, "Hollowmere Manor");
            ClockDoors = CustomOption.Create(1965, CustomOption.CustomOptionType.General, "Clock Shuts Doors For", 4f, 0f, 10f, 1f, ClockInterval);
            PortraitHint = CustomOption.Create(1966, CustomOption.CustomOptionType.General, "Portraits Look At Last Body", true, ClockInterval);
            DarkVision = CustomOption.Create(1967, CustomOption.CustomOptionType.General, "Dark Room Vision", DarkChoices, null, false, null, "Hollowmere Manor");
            CandleBurn = CustomOption.Create(1968, CustomOption.CustomOptionType.General, "Candle Burn Time", 60f, 20f, 120f, 10f, DarkVision);
            BlowOut = CustomOption.Create(1969, CustomOption.CustomOptionType.General, "Impostor Blow-Out Cooldown", BlowChoices, DarkVision);
            // 1961 war bis 24.10. "Hollowmere Intro"; als "Weeping Angels Attack" erbte sie den gespeicherten Wert der alten
            // Option (bei vielen aus), deshalb seit 25.10. 1951. 1961 bleibt frei, damit alte Presets nichts umschalten.
            AngelAttack = CustomOption.Create(1951, CustomOption.CustomOptionType.General, "Weeping Angels Attack", true, null, false, null, "Hollowmere Manor");
            AngelMove = CustomOption.Create(1952, CustomOption.CustomOptionType.General, "Weeping Angels Move", true, AngelAttack);
            AngelBreakout = CustomOption.Create(1953, CustomOption.CustomOptionType.General, "Angel Breakout Sabotage", true, AngelAttack);
            // 28.10. (Feedback DrSuspect, n26/n27): zwei weitere Verhaltensweisen der Engel zur Wahl
            AngelBehaviour = CustomOption.Create(1955, CustomOption.CustomOptionType.General, "Weeping Angels Behaviour",
                new[] { "Gaze", "Awaken", "Stages" }, AngelAttack);
            // 28.10. (n40-n43): Beschwoerung am Pentagramm, Buch in der Bibliothek (HollowmereWorld.Summon.cs)
            Summoning = CustomOption.Create(1954, CustomOption.CustomOptionType.General, "Summoning Circle",
                new[] { "Easy", "Hard", "Off" }, null, false, null, "Hollowmere Manor");
            // 28.10. (n52): im Dixi-Klo des Crew Camps verstecken (HollowmereWorld.Dixi.cs)
            DixiHide = CustomOption.Create(1956, CustomOption.CustomOptionType.General, "Hide In The Portable Toilet", true, null, false, null, "Hollowmere Manor");
            AngelReplayRegister();
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} options failed: {e}"); }
        try
        {
            var h = new Harmony(HalloweenPlugin.PluginGuid + ".villaworld");
            h.Patch(AccessTools.Method(typeof(PlayerControl), nameof(PlayerControl.StartMeeting)),
                prefix: new HarmonyMethod(typeof(HollowmereWorld), nameof(PlayerControl_StartMeeting_Prefix)));
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} patching failed (no portrait hint): {e}"); }
    }

    public HollowmereWorld(AtlasMapDef d, (string, string, Vector2, Vector2, bool)[] secrets, Vector2 clock, string[] darkRooms)
    {
        _d = d;
        _secrets = secrets ?? Array.Empty<(string, string, Vector2, Vector2, bool)>();
        _clock = clock;
        _darkRooms = darkRooms ?? Array.Empty<string>();
        _secretProps = new List<(SpriteRenderer, Vector3, Vector3, float)>[_secrets.Length];
        _animAt = new float[_secrets.Length];
    }

    private static bool SecretsOn => Secrets == null || Secrets.getBool();
    private static float CooldownSecs => SecretCooldown != null ? SecretCooldown.getFloat() : 10f;
    private static bool HintOn => PortraitHint == null || PortraitHint.getBool();
    private static float DoorSecs => ClockDoors != null ? ClockDoors.getFloat() : 4f;
    private float ClockSecs()
    {
        if (_diagClock) return 12f;
        int sel = ClockInterval != null ? ClockInterval.getSelection() : 0;
        return sel >= 0 && sel < ClockSeconds.Length ? ClockSeconds[sel] : 90f;
    }
    private static bool AmHost => AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost;
    private static float DarkFactor
    {
        get { int s = DarkVision != null ? DarkVision.getSelection() : 0; return s >= 0 && s < DarkFactors.Length ? DarkFactors[s] : 0.5f; }
    }
    private static float BurnSecs => CandleBurn != null ? CandleBurn.getFloat() : 60f;
    private static float BlowSecs
    {
        get { int s = BlowOut != null ? BlowOut.getSelection() : 0; return s >= 0 && s < BlowSeconds.Length ? BlowSeconds[s] : 30f; }
    }

    private static bool IsImpostor(PlayerControl p)
    {
        try { return p != null && p.Data != null && p.Data.Role != null && p.Data.Role.IsImpostor; } catch { return false; }
    }

    private static bool LightsOut()
    {
        try
        {
            var ship = ShipStatus.Instance;
            if (ship == null || !ship.Systems.ContainsKey(SystemTypes.Electrical)) return false;
            var s = ship.Systems[SystemTypes.Electrical].TryCast<SwitchSystem>();
            return s != null && s.ActualSwitches != s.ExpectedSwitches;
        }
        catch { return false; }
    }

    private static bool Inside(Vector2 p, Vector2[] poly)
    {
        bool c = false;
        for (int i = 0, j = poly.Length - 1; i < poly.Length; j = i++)
            if ((poly[i].y > p.y) != (poly[j].y > p.y) &&
                p.x < (poly[j].x - poly[i].x) * (p.y - poly[i].y) / (poly[j].y - poly[i].y) + poly[i].x) c = !c;
        return c;
    }

    private bool InDark(Vector2 p)
    {
        foreach (var a in _darkAreas) if (Inside(p, a)) return true;
        return false;
    }

    /// <summary>Sichtverbindung zur Kerze (gleiche Schattenmaske wie die Sicht): kein Kerzenschein durch Waende (Bericht 25.10.).</summary>
    private static bool CandleVisible(Vector2 p, Vector2 candle)
    {
        try { return !PhysicsHelpers.AnythingBetween(p, candle + new Vector2(0f, 0.3f), Constants.ShadowMask, false); }
        catch { return true; }
    }

    private int NearestLitCandle(Vector2 p, float radius)
    {
        float now = Time.time;
        for (int i = 0; i < _candles.Count; i++)
            if (now < _burnUntil[i] && Vector2.Distance(p, _candles[i].Pos) < radius && CandleVisible(p, _candles[i].Pos)) return i;
        return -1;
    }

    // ------------------------------------------------------------------ IAtlasMapWorld

    public void OnBuilt(Transform worldRoot)
    {
        _root = worldRoot;
        _current = this;
        _secretWaitUntil = 0f;
        _lastBody = null;
        _passing = false;
        _clockAt = -1f; _warned = false; _shut.Clear(); _sounds.Clear(); _strikes = 0; _lastStrike = -1f;
        _flickerUntil = _pendulumUntil = 0f;
        for (int i = 0; i < _secrets.Length; i++)
        {
            var s = _secrets[i];
            _secretProps[i] = new List<(SpriteRenderer, Vector3, Vector3, float)>();
            _animAt[i] = -10f;
            // das Moebel am Eingang; am Ausgang die zweite Aufzugklappe bzw. die Bodenplatte des Tunnels
            string exitKind = s.Key == "dumbwaiter" ? s.Prop : s.Key == "tunnel" ? "tunnelausgang" : null;
            foreach (var p in AtlasMaps.Props(s.Prop))
                if (Vector2.Distance(p.Pos, s.Entry) <= 2.5f) AddProp(i, p.Renderer);
            if (exitKind != null)
                foreach (var p in AtlasMaps.Props(exitKind))
                    if (Vector2.Distance(p.Pos, s.Exit) <= 2.5f) AddProp(i, p.Renderer);
        }
        Collect("standuhr", _clockProps, "p1", "p2");
        Collect("portrait", _portraits, "l", "r");
        // 28.10. (n13): weitere Bilder in der Galerie schauen beim Hinweis genauso; Ruestungen drehen den Kopf zum Spieler (n14)
        foreach (var k in new[] { "portrait_dame", "portrait_offizier", "portrait_katze", "portrait_maedchen" })
        {
            var more = new List<PropVar>();
            Collect(k, more, "l", "r");
            _portraits.AddRange(more);
        }
        Collect("ruestung", _armors, "l", "r");
        Collect("scheinwerfer", _spots, "off");
        Collect("kandelaber", _candles, "off");
        Collect("brunnen_blut", _angels, "turn", "step");             // Weeping Angels (HollowmereWorld.Angel.cs)
        Collect("weeping_angel", _graveAngels, "turn", "step");
        AngelReset();
        try { RitualBuild(); } catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} pentagram failed: {e.Message}"); }   // HollowmereWorld.Ritual.cs
        GraveReset();                                                                                                                       // HollowmereWorld.Grave.cs
        _burnUntil = new float[_candles.Count];
        foreach (var pv in _candles) Show(pv, "off");                  // die Kerzen starten erloschen
        _darkAreas.Clear();
        var dark = new HashSet<string>(_darkRooms);
        if (_d.Rooms != null) foreach (var r in _d.Rooms) if (dark.Contains(r.Key) && r.Area != null && r.Area.Length >= 3) _darkAreas.Add(r.Area);
        _dark = _cand = 0f; _blowWaitUntil = 0f;
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} world ready: {_secrets.Length} secret passage(s) ({(SecretsOn ? "on" : "off")}), props {string.Join("/", Array.ConvertAll(_secretProps, l => l.Count.ToString()))}, clock {ClockSecs():F0} s at {_clock.x:F1}/{_clock.y:F1} ({_clockProps.Count} prop, {_portraits.Count} portraits, {_spots.Count} spots), {_candles.Count} candle(s), dark areas {_darkAreas.Count} (vision {DarkFactor:P0})");
        DiagArm();
    }

    private void AddProp(int i, SpriteRenderer sr)
    {
        if (sr == null) return;
        float w = sr.sprite != null ? sr.sprite.bounds.size.x : 1f;
        _secretProps[i].Add((sr, sr.transform.localScale, sr.transform.position, w));
    }

    /// <summary>Alle Props einer Art mit ihren Tauschbildern aus dem Konsolen-Atlas (fehlende Varianten bleiben leer).</summary>
    private void Collect(string kind, List<PropVar> into, params string[] vars)
    {
        into.Clear();
        foreach (var p in AtlasMaps.Props(kind))
        {
            if (p.Renderer == null || p.Index < 0 || p.Index >= _d.Props.Length) continue;
            var def = _d.Props[p.Index];
            var pv = new PropVar { Sr = p.Renderer, Orig = p.Renderer.sprite, Pos = p.Pos };
            string key = $"Prop/{def.Kind}/{def.WorldX.ToString("F3", CultureInfo.InvariantCulture)}/{def.WorldY.ToString("F3", CultureInfo.InvariantCulture)}";
            foreach (var v in vars)
            {
                var sp = AtlasMaps.SpriteFor($"{key}/{v}");
                if (sp != null) pv.Vars[v] = sp;
            }
            if (pv.Vars.Count == 0) HalloweenPlugin.Logger.LogWarning($"{LogPrefix} no variant sprites for {key} (regenerate + repack?)");
            into.Add(pv);
        }
    }

    private float _nextArmor;

    /// <summary>Ruestungen drehen den Helm zum naechsten lebenden Spieler in 3,5 m (nur lokal, rein kosmetisch).</summary>
    private void ArmorTick()
    {
        if (_armors.Count == 0 || Time.time < _nextArmor) return;
        _nextArmor = Time.time + 0.2f;
        var all = PlayerControl.AllPlayerControls;
        foreach (var pv in _armors)
        {
            if (pv.Sr == null) continue;
            float best = 3.5f * 3.5f; Vector2 at = default; bool any = false;
            foreach (var pc in all)
            {
                if (pc == null || pc.Data == null || pc.Data.IsDead || !pc.Visible) continue;
                Vector2 d = pc.GetTruePosition() - pv.Pos;
                if (d.sqrMagnitude < best) { best = d.sqrMagnitude; at = d; any = true; }
            }
            Show(pv, !any || Mathf.Abs(at.x) < 0.45f ? null : at.x < 0f ? "l" : "r");
        }
    }

    private static void Show(PropVar pv, string var)
    {
        if (pv.Sr == null || pv.Shown == var) return;
        var sp = var == null ? pv.Orig : (pv.Vars.TryGetValue(var, out var s) ? s : pv.Orig);
        if (pv.Sr.sprite != sp) pv.Sr.sprite = sp;
        pv.Shown = var;
    }

    public void Tick(float dt)
    {
        try { AngelTick(); } catch (Exception e) { AngelError(e); }
        try { BreakoutFrame(); } catch (Exception e) { AngelError(e); }
        try { RitualTick(); } catch (Exception e) { RitualError(e); }
        try { GraveTick(); } catch { }
        try { DixiTick(); } catch (Exception e) { RitualError(e); }
        try { CurioTick(); } catch (Exception e) { RitualError(e); }
        AnimTick();
        ArmorTick();
        ClockTick(dt);
        CandleTick(dt);
        if (_passing) { PassTick(dt); return; }
        DiagTick();
        if (OfferSecrets()) return;
        OfferCandles();
    }

    private bool OfferSecrets()
    {
        if (!SecretsOn || _secrets.Length == 0 || PlayerControl.LocalPlayer == null) return false;
        bool wait = Time.time < _secretWaitUntil;
        for (int i = 0; i < _secrets.Length; i++)
        {
            var s = _secrets[i];
            if (AtlasMaps.CanReach(s.Entry, Reach))
            {
                int idx = i;
                AtlasMaps.OfferUse(wait ? $"WAIT {Mathf.CeilToInt(_secretWaitUntil - Time.time)}" : "ENTER", "task_villa_btn_secret.png", () => Use(idx, 0), enabled: !wait);
                return true;
            }
            if (s.Both && AtlasMaps.CanReach(s.Exit, Reach))
            {
                int idx = i;
                AtlasMaps.OfferUse(wait ? $"WAIT {Mathf.CeilToInt(_secretWaitUntil - Time.time)}" : "ENTER", "task_villa_btn_secret.png", () => Use(idx, 1), enabled: !wait);
                return true;
            }
        }
        return false;
    }

    private void OfferCandles()
    {
        if (DarkFactor >= 1f || _candles.Count == 0) return;
        var lp = PlayerControl.LocalPlayer;
        if (lp == null) return;
        float now = Time.time;
        for (int i = 0; i < _candles.Count; i++)
        {
            if (!AtlasMaps.CanReach(_candles[i].Pos, Reach + 0.2f)) continue;
            int idx = i;
            bool lit = now < _burnUntil[i];
            if (!lit)
            {
                AtlasMaps.OfferUse("LIGHT", "task_villa_btn_candle.png", () => SetCandle(idx, true, true));
                return;
            }
            if (IsImpostor(lp) && BlowSecs >= 0f)
            {
                bool wait = now < _blowWaitUntil;
                AtlasMaps.OfferUse(wait ? $"WAIT {Mathf.CeilToInt(_blowWaitUntil - now)}" : "BLOW OUT", "task_villa_btn_blow.png",
                    () => { SetCandle(idx, false, true); _blowWaitUntil = Time.time + BlowSecs; }, enabled: !wait);
            }
            return;
        }
    }

    /// <summary>Kerze an- oder ausmachen; send = vom lokalen Spieler ausgeloest (an alle weitergeben).</summary>
    private void SetCandle(int idx, bool on, bool send)
    {
        if (idx < 0 || idx >= _candles.Count) return;
        _burnUntil[idx] = on ? Time.time + BurnSecs : 0f;
        Show(_candles[idx], on ? null : "off");
        float vol = 0f;
        try { var lp = PlayerControl.LocalPlayer; if (lp != null) vol = Mathf.Clamp01(1f - Vector2.Distance(lp.GetTruePosition(), _candles[idx].Pos) / 9f); } catch { }
        if (vol > 0.02f) AtlasMaps.Sfx(on ? "click" : "whoosh", (on ? 0.7f : 0.5f) * vol);
        if (send) SendCandle(idx, on);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} candle {idx} {(on ? $"lit for {BurnSecs:F0} s" : "out")}");
    }

    private void CandleTick(float dt)
    {
        float now = Time.time;
        for (int i = 0; i < _candles.Count; i++)
            if (_burnUntil[i] > 0f && now >= _burnUntil[i]) { _burnUntil[i] = 0f; Show(_candles[i], "off"); }
        // weiche Uebergaenge: Dunkelheit (im dunklen Raum) und Kerzenschein (nahe einer brennenden Kerze)
        float tDark = 0f, tCand = 0f;
        var lp = PlayerControl.LocalPlayer;
        if (lp != null && lp.Data != null && !lp.Data.IsDead && DarkFactor < 1f)
        {
            var pos = lp.GetTruePosition();
            tDark = InDark(pos) ? 1f : 0f;
            tCand = NearestLitCandle(pos, CandleRadius) >= 0 ? 1f : 0f;
        }
        _dark = Mathf.MoveTowards(_dark, tDark, dt * 2f);
        _cand = Mathf.MoveTowards(_cand, tCand, dt * 2f);
    }

    public float VisionFactor(Vector2 pos)
    {
        float f = Mathf.Lerp(1f, DarkFactor, _dark * (1f - _cand));
        // Licht-Sabotage: in Kerzennaehe gilt fuer die Crew der volle Radius (TOR: Lerp(Min, Max, Schalter/255))
        if (_cand > 0f && LightsOut())
        {
            try
            {
                var lp = PlayerControl.LocalPlayer;
                var ship = ShipStatus.Instance;
                if (lp != null && ship != null && !TheOtherRoles.Helpers.hasImpVision(lp.Data))
                {
                    var sw = ship.Systems[SystemTypes.Electrical].TryCast<SwitchSystem>();
                    float now = Mathf.Lerp(ship.MinLightRadius, ship.MaxLightRadius, sw.Value / 255f);
                    float boost = Mathf.Clamp(ship.MaxLightRadius / Mathf.Max(0.05f, now), 1f, 5f);
                    f *= Mathf.Lerp(1f, boost, _cand);
                }
            }
            catch { }
        }
        // Lichtflackern beim Uhrschlag
        if (Time.time < _flickerUntil && !FlickerOn(Time.time)) f *= 0.45f;
        return f;
    }

    private static bool FlickerOn(float t) => Mathf.PerlinNoise(t * 9f, 1.3f) > 0.45f;

    public void OnDestroy()
    {
        EndPass(true);
        _sounds.Clear();
        _shut.Clear();
        RitualDestroy();
        AngelMoveDestroy();
        if (_current == this) _current = null;
    }

    // ------------------------------------------------------------------ Durchgang

    private void Use(int idx, int dir)
    {
        if (_passing || idx < 0 || idx >= _secrets.Length) return;
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || lp.Data == null || lp.Data.IsDead) return;
        var s = _secrets[idx];
        _passTo = dir == 0 ? s.Exit : s.Entry;
        _passing = true; _snapped = false; _passT = 0f;
        try { lp.moveable = false; } catch { }
        MakeCover();
        SendSecret(idx, dir);
        PlaySecret(idx);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} secret {s.Key}: {(dir == 0 ? "entry -> exit" : "exit -> entry")}");
    }

    private void PassTick(float dt)
    {
        _passT += dt;
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || lp.Data == null || lp.Data.IsDead || MeetingHud.Instance != null) { EndPass(false); return; }
        float a = _passT < 0.4f ? _passT / 0.4f : _passT < 0.8f ? 1f : Mathf.Clamp01((PassSecs - _passT) / 0.4f);
        FitCover(a);
        if (!_snapped && _passT >= SnapAt)
        {
            _snapped = true;
            try { lp.NetTransform.RpcSnapTo(_passTo); }
            catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} snap failed: {e.Message}"); }
        }
        if (_passT >= PassSecs) EndPass(false);
    }

    private void EndPass(bool destroying)
    {
        if (!_passing && _cover == null) return;
        _passing = false;
        try { var lp = PlayerControl.LocalPlayer; if (lp != null && !destroying) lp.moveable = true; } catch { }
        if (_cover != null) { try { Object.Destroy(_cover); } catch { } _cover = null; _coverSr = null; }
        if (_coverTex != null) { try { Object.Destroy(_coverTex); } catch { } _coverTex = null; }
        if (!destroying) _secretWaitUntil = Time.time + CooldownSecs;
    }

    // Schwarze Flaeche ueber allem, wie beim Vorspann (HollowmereIntro): an der Ebene von HudManager.FullScreen,
    // nicht an FullScreen selbst (TOR blitzt damit, und sein Ende schaltet FullScreen ab).
    private void MakeCover()
    {
        try
        {
            var fs = HudManager.InstanceExists ? HudManager.Instance.FullScreen : null;
            int layer = fs != null ? fs.gameObject.layer : 5;
            _cover = new GameObject("Hollowmere_Passage") { layer = layer };
            if (fs != null && fs.transform.parent != null)
            {
                var parent = fs.transform.parent;
                _cover.transform.SetParent(parent, false);
                _cover.transform.localPosition = new Vector3(0f, 0f, fs.transform.localPosition.z - 1f);
                var ls = parent.lossyScale;
                _cover.transform.localScale = new Vector3(1f / Mathf.Max(0.0001f, ls.x), 1f / Mathf.Max(0.0001f, ls.y), 1f);
            }
            else if (Camera.main != null)
            {
                _cover.transform.SetParent(Camera.main.transform, false);
                _cover.transform.localPosition = new Vector3(0f, 0f, 5f);
            }
            _coverTex = new Texture2D(2, 2, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave };
            _coverTex.SetPixels(new[] { Color.black, Color.black, Color.black, Color.black });
            _coverTex.Apply();
            var quad = new GameObject("black") { layer = layer };
            quad.transform.SetParent(_cover.transform, false);
            _coverSr = quad.AddComponent<SpriteRenderer>();
            _coverSr.sprite = Sprite.Create(_coverTex, new Rect(0, 0, 2, 2), new Vector2(0.5f, 0.5f), 2f);
            if (fs != null) { _coverSr.sortingLayerID = fs.sortingLayerID; _coverSr.sortingOrder = fs.sortingOrder + 10; }
            else _coverSr.sortingOrder = 32000;
            FitCover(0f);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} cover failed: {e.Message}"); }
    }

    private void FitCover(float alpha)
    {
        if (_coverSr == null) return;
        try
        {
            var cam = Camera.main;
            if (cam != null)
            {
                float h = cam.orthographicSize * 2f, w = h * cam.aspect;
                _coverSr.transform.localScale = new Vector3(w * 1.1f, h * 1.1f, 1f);
            }
            _coverSr.color = new Color(0f, 0f, 0f, alpha);
        }
        catch { }
    }

    // ------------------------------------------------------------------ Netz

    private static void SendSecret(int idx, int dir)
    {
        try
        {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || AmongUsClient.Instance == null) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubSecret);
            w.Write(lp.PlayerId);
            w.Write((byte)idx);
            w.Write((byte)dir);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} send failed: {e.Message}"); }
    }

    private static void SendCandle(int idx, bool on)
    {
        try
        {
            if (PlayerControl.LocalPlayer == null || AmongUsClient.Instance == null) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubCandle);
            w.Write((byte)idx);
            w.Write(on);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} candle send failed: {e.Message}"); }
    }

    private static void SendClock(byte phase)
    {
        try
        {
            if (PlayerControl.LocalPlayer == null || AmongUsClient.Instance == null) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubClock);
            w.Write(phase);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} clock send failed: {e.Message}"); }
    }

    /// <summary>Sub-Codes ab 2 auf Modul 236 (HollowmereIntro.HandleRpc reicht sie her).</summary>
    internal static void HandleRpc(byte sub, Hazel.MessageReader reader)
    {
        var w = _current;
        if (sub == SubSecret)
        {
            byte player = reader.ReadByte();
            int idx = reader.ReadByte(), dir = reader.ReadByte();
            if (w == null || idx >= w._secrets.Length) return;
            w.PlaySecret(idx);
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} secret {w._secrets[idx].Key} used by player {player}");
        }
        else if (sub == SubClock)
        {
            byte phase = reader.ReadByte();
            if (w == null || !UCRpc.RequireHost("Hollowmere.Clock")) return;
            w.ApplyClock(phase);
        }
        else if (sub == SubAngelVictim)
        {
            HandleAngelRpc(reader);
        }
        else if (sub == SubScenePreview)
        {
            HalloweenCostumes.HandleScenePreview(reader);
        }
        else if (sub == SubAngelMove || sub == SubBreakout || sub == SubSealHold || sub == SubBlink)
        {
            HandleAngelMoveRpc(sub, reader);
        }
        else if (sub == SubCandle)
        {
            int idx = reader.ReadByte();
            bool on = reader.ReadBoolean();
            if (w == null || idx >= w._candles.Count) return;
            // ausblasen duerfen nur Impostor (Absender pruefen, nicht dem Paket glauben)
            if (!on && !IsImpostor(UCRpc.Sender))
            {
                HalloweenPlugin.Logger.LogWarning($"{LogPrefix} candle blow-out from non-impostor {UCRpc.Sender?.PlayerId.ToString() ?? "?"} ignored");
                return;
            }
            w.SetCandle(idx, on, false);
        }
    }

    /// <summary>Moebel bewegen und Geraeusch nach Entfernung (Eingang oder Ausgang, je nachdem, was naeher liegt).</summary>
    private void PlaySecret(int idx)
    {
        var s = _secrets[idx];
        _animAt[idx] = Time.time;
        float vol = 0f;
        try
        {
            var lp = PlayerControl.LocalPlayer;
            if (lp != null)
            {
                var me = lp.GetTruePosition();
                float d = Mathf.Min(Vector2.Distance(me, s.Entry), Vector2.Distance(me, s.Exit));
                vol = Mathf.Clamp01(1f - d / 12f);
            }
        }
        catch { }
        if (vol <= 0.02f) return;
        string clip = s.Key switch { "bookcase" => "creak", "tapestry" => "whoosh", "dumbwaiter" => "clack", _ => "grind" };
        AtlasMaps.Sfx(clip, 0.9f * vol);
    }

    private void AnimTick()
    {
        const float Dur = 0.9f;
        float now = Time.time;
        for (int i = 0; i < _secrets.Length; i++)
        {
            float t = now - _animAt[i];
            if (t > Dur + 0.1f || _secretProps[i] == null) continue;
            float k = Mathf.Clamp01(t / Dur);
            bool done = t >= Dur;
            foreach (var (sr, scale, pos, width) in _secretProps[i])
            {
                if (sr == null) continue;
                var tr = sr.transform;
                if (done) { tr.localScale = scale; tr.position = pos; continue; }
                switch (_secrets[i].Key)
                {
                    case "bookcase":
                        // Drehung um die Mittelachse: Breite auf Null und zurueck, Mitte bleibt
                        float sx = Mathf.Max(0.08f, Mathf.Abs(Mathf.Cos(k * Mathf.PI)));
                        tr.localScale = new Vector3(scale.x * sx, scale.y, scale.z);
                        tr.position = new Vector3(pos.x + width * (1f - sx) / 2f, pos.y, pos.z);
                        break;
                    case "tapestry":
                        // der Teppich lupft (Drehpunkt unten) und schwingt nach
                        float lift = Mathf.Sin(k * Mathf.PI) * 0.14f;
                        tr.localScale = new Vector3(scale.x, scale.y * (1f + lift), scale.z);
                        tr.position = new Vector3(pos.x + Mathf.Sin(k * Mathf.PI * 3f) * 0.03f, pos.y, pos.z);
                        break;
                    default:
                        // Klappe und Tunnelplatte ruckeln
                        tr.position = new Vector3(pos.x, pos.y + Mathf.Abs(Mathf.Sin(k * Mathf.PI * 4f)) * 0.06f * (1f - k), pos.z);
                        break;
                }
            }
        }
    }

    // ------------------------------------------------------------------ Mitternachtsuhr

    private static bool ClockPaused()
    {
        try
        {
            if (MeetingHud.Instance != null || ExileController.Instance != null) return true;
            var ship = ShipStatus.Instance;
            if (ship == null) return true;
            var r = ship.Systems.ContainsKey(SystemTypes.Reactor) ? ship.Systems[SystemTypes.Reactor].TryCast<ReactorSystemType>() : null;
            var o = ship.Systems.ContainsKey(SystemTypes.LifeSupp) ? ship.Systems[SystemTypes.LifeSupp].TryCast<LifeSuppSystemType>() : null;
            return (r != null && r.IsActive) || (o != null && o.IsActive);
        }
        catch { return false; }
    }

    private void ClockTick(float dt)
    {
        float now = Time.time;
        // Geraeusche nach Zeitplan (alle Clients)
        for (int i = _sounds.Count - 1; i >= 0; i--)
            if (now >= _sounds[i].At) { AtlasMaps.Sfx(_sounds[i].Clip, _sounds[i].Vol); _sounds.RemoveAt(i); }
        // Pendel, Flackern der Scheinwerfer, Wackeln der Portraets
        if (_clockProps.Count > 0)
        {
            string pend = now < _pendulumUntil ? ((int)(now * 4f) % 2 == 0 ? "p1" : "p2") : null;
            foreach (var pv in _clockProps) Show(pv, pend);
        }
        if (_spots.Count > 0)
        {
            // Scheinwerfer: aus bei Licht-Sabotage, flackernd beim Uhrschlag
            string spot = LightsOut() || (now < _flickerUntil && !FlickerOn(now)) ? "off" : null;
            foreach (var pv in _spots) Show(pv, spot);
        }
        float shake = now - _portraitShakeAt;
        if (shake < 0.9f && _portraits.Count > 0)
        {
            float ang = Mathf.Sin(shake * 22f) * 4f * (1f - shake / 0.9f);
            foreach (var pv in _portraits) if (pv.Sr != null) pv.Sr.transform.localRotation = Quaternion.Euler(0f, 0f, ang);
        }
        else if (shake < 1.0f && _portraits.Count > 0)
            foreach (var pv in _portraits) if (pv.Sr != null) pv.Sr.transform.localRotation = Quaternion.identity;
        // Host: Timer, Vorwarnung, Schlag, Tueren
        if (!AmHost) return;
        float iv = ClockSecs();
        if (_shut.Count > 0 && now >= _doorsOpenAt) OpenDoors();
        if (iv <= 0f) return;
        if (_clockAt < 0f) _clockAt = now + iv;
        if (ClockPaused()) { _clockAt += dt; return; }
        if (!_warned && now >= _clockAt - WarnSecs) { _warned = true; SendClock(0); ApplyClock(0); }
        if (now >= _clockAt)
        {
            _warned = false;
            _clockAt = now + iv;
            SendClock(1);
            ApplyClock(1);
            ShutDoors();
        }
    }

    /// <summary>Vorwarnung (0) oder Schlag (1) auf diesem Client zeigen.</summary>
    private void ApplyClock(byte phase)
    {
        float now = Time.time;
        if (phase == 0)
        {
            _pendulumUntil = now + WarnSecs + 0.5f;
            for (int k = 0; k < 5; k++) _sounds.Add((now + k, "clock", 0.55f));
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} clock: warning");
            return;
        }
        _strikes++;
        _lastStrike = now;
        _flickerUntil = now + 3f;
        _pendulumUntil = now + 3f;
        _sounds.Add((now, "boom", 0.45f));
        for (int k = 0; k < 3; k++) _sounds.Add((now + k * 1.15f, "chime", 0.9f));
        // Portraets blicken zur zuletzt gemeldeten Leiche
        string looks = "-";
        if (HintOn && _lastBody.HasValue && _portraits.Count > 0)
        {
            looks = "";
            foreach (var pv in _portraits)
            {
                string dir = _lastBody.Value.x < pv.Pos.x - 0.3f ? "l" : _lastBody.Value.x > pv.Pos.x + 0.3f ? "r" : null;
                Show(pv, dir);
                looks += dir ?? "o";
            }
            _portraitShakeAt = now;
        }
        else foreach (var pv in _portraits) Show(pv, null);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} clock: strike #{_strikes}, portraits {looks}");
    }

    private static void DoorsDirty()
    {
        try
        {
            var ship = ShipStatus.Instance;
            if (ship == null || !ship.Systems.ContainsKey(SystemTypes.Doors)) return;
            var ds = ship.Systems[SystemTypes.Doors].TryCast<DoorsSystemType>();
            if (ds != null) ds.IsDirty = true;
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} doors dirty failed: {e.Message}"); }
    }

    private void ShutDoors()
    {
        float secs = DoorSecs;
        if (secs <= 0f) return;
        _shut.Clear();
        try
        {
            var ship = ShipStatus.Instance;
            if (ship == null || ship.AllDoors == null) return;
            foreach (var d in ship.AllDoors)
            {
                var pd = d != null ? d.TryCast<PlainDoor>() : null;
                if (pd == null || !pd.Open) continue;
                pd.SetDoorway(false);
                _shut.Add(pd);
            }
            DoorsDirty();
            _doorsOpenAt = Time.time + secs;
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} clock: {_shut.Count} door(s) shut for {secs:F0} s");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} shut doors failed: {e.Message}"); }
    }

    private void OpenDoors()
    {
        int n = 0;
        foreach (var pd in _shut)
        {
            try { if (pd != null && !pd.Open) { pd.SetDoorway(true); n++; } } catch { }
        }
        _shut.Clear();
        DoorsDirty();
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} clock: {n} door(s) reopened");
    }

    /// <summary>Jeder Client: beim Meeting-Start die Position der gemeldeten Leiche merken (Portraet-Hinweis).</summary>
    internal static void PlayerControl_StartMeeting_Prefix([HarmonyArgument(0)] NetworkedPlayerInfo target)
    {
        try
        {
            if (_current == null || target == null) return;
            foreach (var db in Object.FindObjectsOfType<DeadBody>())
                if (db != null && db.ParentId == target.PlayerId) { _lastBody = db.TruePosition; break; }
            if (_lastBody.HasValue) HalloweenPlugin.Logger.LogInfo($"{LogPrefix} last body at {_lastBody.Value.x:F1}/{_lastBody.Value.y:F1}");
        }
        catch { }
    }

    // ------------------------------------------------------------------ Autotest

    private readonly List<string> _diagTasks = new();
    private int _diagStep = -1, _diagTask;
    private float _diagAt;
    private bool _diagDarkLogged, _diagClock;
    private int _diagStrikesSeen;

    private void DiagArm()
    {
        _diagTasks.Clear();
        _diagStep = -1;
        _diagClock = false;
        string env = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        if (!AtlasMaps.AutotestRun) return;
        foreach (var part in env.Split(','))
        {
            var p = part.Trim();
            if (p.StartsWith("secret:", StringComparison.Ordinal))
            {
                foreach (var k in p.Substring(7).Split('+'))
                    if (!string.IsNullOrWhiteSpace(k)) _diagTasks.Add("secret:" + k.Trim());
            }
            else if (p == "clock") { _diagTasks.Add("clock"); _diagClock = true; }
            else if (p == "candle") _diagTasks.Add("candle");
            else if (p == "angels") _diagTasks.Add("angels");
        }
        if (_diagTasks.Count == 0) return;
        // erst nach den Ansichtsfotos von Atlas (AtlasMapShot teleportiert den Spieler ~20 s lang herum und laesst
        // zuletzt die Kameras offen), wie der Minispiel-Autotest von Atlas
        _diagTask = 0; _diagStep = 0; _diagAt = Time.time + 28f;
        if (_diagClock) _clockAt = Time.time + 60f;                   // die Uhr wartet, bis der Test sie braucht
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: {string.Join(",", _diagTasks)}");
    }

    private static int ClosedDoors()
    {
        int n = 0;
        try { foreach (var d in ShipStatus.Instance.AllDoors) { var pd = d != null ? d.TryCast<PlainDoor>() : null; if (pd != null && !pd.Open) n++; } } catch { }
        return n;
    }

    private void DiagTick()
    {
        if (_diagStep < 0 || Time.time < _diagAt) return;
        if (_diagTask >= _diagTasks.Count) { _diagStep = -1; HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: all done"); return; }
        var lp = PlayerControl.LocalPlayer;
        if (_diagStep == 0 && Minigame.Instance != null) { try { Minigame.Instance.ForceClose(); } catch { } _diagAt = Time.time + 1.5f; return; }
        string task = _diagTasks[_diagTask];
        if (task == "clock") { DiagClock(lp); return; }
        if (task == "candle") { DiagCandle(lp); return; }
        if (task == "angels") { DiagAngels(lp); return; }
        int idx = Array.FindIndex(_secrets, s => s.Key == task.Substring(7));
        if (idx < 0)
        {
            HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag: no secret '{task}' on this variant");
            _diagTask++; _diagStep = 0; return;
        }
        var sec = _secrets[idx];
        string tag = $"secret_{sec.Key}";
        switch (_diagStep)
        {
            case 0:
                try { lp.NetTransform.RpcSnapTo(sec.Entry + new Vector2(0f, -0.4f)); } catch { }
                _diagStep = 1; _diagAt = Time.time + 1f;
                break;
            case 1:
                AtlasMaps.Shot(tag, "before");
                _diagDarkLogged = false;
                Use(idx, 0);
                _diagStep = 2; _diagAt = Time.time + 0.35f;
                break;
            case 2:
                AtlasMaps.Shot(tag, "mid");
                _diagStep = 3; _diagAt = Time.time + 1.6f;
                break;
            case 3:
                AtlasMaps.Shot(tag, "after");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: {sec.Key} player at {lp.GetTruePosition().x:F2}/{lp.GetTruePosition().y:F2}, exit {sec.Exit.x:F2}/{sec.Exit.y:F2}");
                if (sec.Both) { _secretWaitUntil = 0f; _diagStep = 4; _diagAt = Time.time + 0.5f; }
                else { _diagTask++; _diagStep = 0; _diagAt = Time.time + 1f; }
                break;
            case 4:
                Use(idx, 1);
                _diagStep = 5; _diagAt = Time.time + 1.9f;
                break;
            case 5:
                AtlasMaps.Shot(tag, "back");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: {sec.Key} back at {lp.GetTruePosition().x:F2}/{lp.GetTruePosition().y:F2}, entry {sec.Entry.x:F2}/{sec.Entry.y:F2}");
                _diagTask++; _diagStep = 0; _diagAt = Time.time + 1f;
                break;
        }
    }

    private int _diagCandle = -1;

    private string DiagRadius(PlayerControl lp)
    {
        float r = -1f;
        try { r = ShipStatus.Instance.CalculateLightRadius(lp.Data); } catch { }
        return $"radius {r:F2} (dark {_dark:F2}, candle {_cand:F2}, lights {(LightsOut() ? "OUT" : "on")})";
    }

    /// <summary>Kerzen-Test: an eine Kerze im dunklen Raum, Radius dunkel/angezuendet, Licht-Sabotage nah und fern,
    /// Kerze ausblasen.</summary>
    private void DiagCandle(PlayerControl lp)
    {
        float now = Time.time;
        switch (_diagStep)
        {
            case 0:
                _diagCandle = -1;
                for (int i = 0; i < _candles.Count && _diagCandle < 0; i++) if (InDark(_candles[i].Pos + new Vector2(0f, -0.8f))) _diagCandle = i;
                if (_diagCandle < 0) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag: no candle in a dark room"); _diagTask++; return; }
                try { lp.NetTransform.RpcSnapTo(_candles[_diagCandle].Pos + new Vector2(0f, -0.8f)); } catch { }
                _diagStep = 1; _diagAt = now + 3f;
                break;
            case 1:
                // ScreenCapture nimmt erst am Frame-Ende auf: anzuenden erst im naechsten Schritt
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: candle {_diagCandle} unlit, {DiagRadius(lp)}");
                AtlasMaps.Shot("candle", "unlit");
                _diagStep = 10; _diagAt = now + 0.3f;
                break;
            case 10:
                SetCandle(_diagCandle, true, true);
                _diagStep = 2; _diagAt = now + 2.5f;
                break;
            case 2:
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: candle lit, {DiagRadius(lp)}");
                AtlasMaps.Shot("candle", "lit");
                try { ShipStatus.Instance.RpcUpdateSystem(SystemTypes.Sabotage, (byte)SystemTypes.Electrical); } catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag: sabotage failed: {e.Message}"); }
                _diagStep = 3; _diagAt = now + 5f;
                break;
            case 3:
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: lights out near candle, {DiagRadius(lp)}");
                AtlasMaps.Shot("candle", "sab_near");
                try { lp.NetTransform.RpcSnapTo(_clock + new Vector2(0f, -0.9f)); } catch { }
                _diagStep = 4; _diagAt = now + 3f;
                break;
            case 4:
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: lights out in the hall, {DiagRadius(lp)}");
                AtlasMaps.Shot("candle", "sab_far");
                try
                {
                    var sw = ShipStatus.Instance.Systems[SystemTypes.Electrical].TryCast<SwitchSystem>();
                    sw.ActualSwitches = sw.ExpectedSwitches;
                    sw.IsDirty = true;
                }
                catch { }
                try { lp.NetTransform.RpcSnapTo(_candles[_diagCandle].Pos + new Vector2(0f, -0.8f)); } catch { }
                _diagStep = 5; _diagAt = now + 2f;
                break;
            case 5:
                SetCandle(_diagCandle, false, true);
                _diagStep = 6; _diagAt = now + 2.5f;
                break;
            case 6:
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: candle blown out, {DiagRadius(lp)}");
                AtlasMaps.Shot("candle", "blown");
                _diagTask++; _diagStep = 0; _diagAt = now + 1f;
                break;
        }
    }

    /// <summary>Uhr-Test: vor die Uhr, Vorwarnung und Schlag fotografieren, Tueren zu und wieder auf, dann mit
    /// einer gemerkten Leiche links der Galerie den Portraet-Blick beim naechsten Schlag.</summary>
    private void DiagClock(PlayerControl lp)
    {
        float now = Time.time;
        switch (_diagStep)
        {
            case 0:
                try { lp.NetTransform.RpcSnapTo(_clock + new Vector2(0f, -0.9f)); } catch { }
                _diagStrikesSeen = _strikes;
                _clockAt = now + WarnSecs + 3f;                      // Vorwarnung in 3 s
                _warned = false;
                _diagStep = 1; _diagAt = now + 0.5f;
                break;
            case 1:
                if (!_warned) { _diagAt = now + 0.2f; return; }
                _diagStep = 2; _diagAt = now + 1.2f;
                break;
            case 2:
                AtlasMaps.Shot("clock", "warn");
                _diagStep = 3; _diagAt = now + 0.2f;
                break;
            case 3:
                if (_strikes == _diagStrikesSeen) { _diagAt = now + 0.1f; return; }
                _diagStep = 4; _diagAt = now + 0.45f;
                break;
            case 4:
                AtlasMaps.Shot("clock", "strike");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: clock strike, doors closed {ClosedDoors()}, flicker {(Time.time < _flickerUntil ? "on" : "off")}");
                try { var d0 = ShipStatus.Instance.AllDoors[0]; lp.NetTransform.RpcSnapTo((Vector2)d0.transform.position + new Vector2(1.2f, -1.2f)); } catch { }
                _diagStep = 5; _diagAt = now + 0.8f;
                break;
            case 5:
                AtlasMaps.Shot("clock", "doorsshut");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: doors closed {ClosedDoors()} at +{Time.time - _lastStrike:F1} s");
                _diagStep = 6; _diagAt = _lastStrike + DoorSecs + 1.5f;
                break;
            case 6:
                AtlasMaps.Shot("clock", "doorsopen");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: doors closed {ClosedDoors()} at +{Time.time - _lastStrike:F1} s");
                // Portraet-Hinweis: Leiche links der Galerie, Spieler mitten hinein, naechster Schlag bald
                if (_portraits.Count > 0)
                {
                    float gx = 0f, gy = 0f;
                    foreach (var pv in _portraits) { gx += pv.Pos.x; gy += pv.Pos.y; }
                    gx /= _portraits.Count; gy /= _portraits.Count;
                    _lastBody = new Vector2(gx - 6f, gy);
                    try { lp.NetTransform.RpcSnapTo(new Vector2(gx - 0.8f, gy)); } catch { }
                    _diagStrikesSeen = _strikes;
                    _clockAt = now + WarnSecs + 1f;
                    _warned = false;
                    _diagStep = 7; _diagAt = now + 0.5f;
                }
                else { _diagTask++; _diagStep = 0; }
                break;
            case 7:
                if (_strikes == _diagStrikesSeen) { _diagAt = now + 0.1f; return; }
                _diagStep = 8; _diagAt = now + 0.6f;
                break;
            case 8:
                AtlasMaps.Shot("clock", "portraits");
                _diagStep = 9; _diagAt = now + 3.5f;
                break;
            case 9:
                AtlasMaps.Shot("clock", "portraits2");
                _diagTask++; _diagStep = 0; _diagAt = now + 1f;
                break;
        }
    }
}
