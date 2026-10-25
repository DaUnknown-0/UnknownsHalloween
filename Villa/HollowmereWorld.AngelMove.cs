// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.AngelMove - die Friedhofsengel der grossen Manor bewegen sich (User 25.10.), dazu Blinzeln und die
// Sabotage "Engel-Ausbruch". Die Brunnenfigur bleibt stehen (sie gehoert zum Brunnen).
//
// Spruenge (Option 1952 "Weeping Angels Move", Host-autoritativ; User 25.10.: NUR waehrend der Sabotage "Angel Breakout",
// sonst stehen die Engel fest auf ihrem Platz): schaut niemand einen Engel an und hat er einen Spieler im
// Visier (der Spieler schaut weg und der Wert hat "starrt an" erreicht, oder er hat gerade geblinzelt), springt der Engel
// hoechstens 1,5 m naeher, nie naeher als 0,8 m und nie weiter als 6 m von seinem Platz. Der Weg folgt einem Laufraster
// (0,5 m, beim ersten Tick aus den Kollidern gebaut), damit kein Engel durch eine Wand springt; vor jedem Sprung prueft eine
// Sichtlinie gegen Waende und geschlossene Tueren. Die Engel tragen dafuer eigene Kollider, die mitwandern (die statischen
// Glass-Kollider von Atlas an ihren Plaetzen werden abgeschaltet). Position als RPC Modul 236 Sub 11 (Host -> alle).
// Bei jedem Meeting stehen alle wieder auf ihrem Platz (jeder Client fuer sich).
//
// Blinzeln (Host entscheidet, nur waehrend der Sabotage): jeder Spieler, der gerade einen Engel im Blick hat, blinzelt alle 8 bis 14 s fuer einen Tick
// (0,2 s); in diesem Tick zaehlt sein Blick nicht. Schaut sonst niemand hin, kann der Engel in genau diesem Moment springen.
// Der Host meldet jeden Lidschlag (Sub 14 [spieler]); der Spieler sieht auf seinem Bildschirm zwei Augenlider kurz zu- und
// aufgehen (User 25.10.). Lokaler Schalter "Angel Blink Effect" auf UCs Einstellungsseite (AppDomain-Vertrag
// "Unknowns.Options.Toggles", Config [Weeping Angels] BlinkEffect): aus = kein Bild, geblinzelt wird trotzdem.
//
// Engel-Ausbruch (Option 1953, nur mit Friedhofsengeln): der Host fuehrt einen gemeinsamen Zornpegel. Er steigt fuer jeden
// Spieler, der einem Engel den Ruecken zukehrt (0,6/s) oder nahe bei einem steht (unter 3 m, 0,4/s), und sinkt ohne das
// langsam (0,25/s). Voll (100) -> Sabotage (Sub 12/1, nicht von Impostorn ausloesbar): 45 s Countdown, der Notfallknopf ist
// gesperrt; zwei Siegel in der Nordwestecke des Friedhofs muessen gleichzeitig gehalten werden (je ein lebender Spieler
// steht dort und drueckt "HOLD", Sub 13 jeder -> Host; 1 s gemeinsam gehalten -> behoben, Sub 12/0). Laeuft die Zeit ab
// (Sub 12/2), bewegen sich die Engel frei ueber die ganze Karte (Laufraster, zum naechsten Spieler) und toeten jeden in
// Reichweite, der sie nicht ansieht, Impostor eingeschlossen. Erst das naechste Meeting setzt alles zurueck. Nach einem
// Ausbruch ruht der Pegel 60 s.

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using TheOtherRoles;
using TMPro;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;
using Object = UnityEngine.Object;
using Random = UnityEngine.Random;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    public static CustomOption AngelMove, AngelBreakout;
    internal const byte SubAngelMove = 11;       // [slot][x][y]           Host -> alle
    internal const byte SubBreakout = 12;        // [phase] 0 Ende, 1 Countdown, 2 Ausbruch   Host -> alle
    internal const byte SubSealHold = 13;        // [siegel][an]           jeder -> Host
    internal const byte SubScenePreview = 15;   // [spieler][szene]         Host -> alle (Role Control, HalloweenCostumes.PreviewFor)
    internal const byte SubBlink = 14;           // [spieler]              Host -> alle (nur der Spieler selbst zeigt den Lidschlag)
    internal static BepInEx.Configuration.ConfigEntry<bool> BlinkEffect;

    private const float JumpMax = 1.5f, JumpKeep = 0.8f, JumpEvery = 0.8f, RampageEvery = 0.6f, HomeLeash = 6f;
    private const float BlinkMin = 8f, BlinkMax = 14f;
    private const float WrathFull = 100f, WrathAway = 0.6f, WrathNear = 0.4f, WrathNearDist = 3f, WrathCalm = 0.25f, WrathRest = 60f;
    private const float BreakoutSecs = 45f, SealReach = 0.9f, SealHostReach = 1.4f, SealHoldNeed = 1f;
    private const float Cell = 0.5f;
    private const int MaskWalls = (1 << 9) | (1 << 12);   // AtlasMuseumBuilder.LayerShip, LayerShortObjects

    // Nordwestecke des Friedhofs (Plan 41,3 / 14,9 und 41,3 / 19,4, User 25.10. Bild 93)
    private static readonly Vector2[] SealPos = { new(41.3f - 17f, 14f - 14.9f), new(41.3f - 17f, 14f - 19.4f) };

    private static bool AngelMoveOn { get { try { return AngelMove == null || AngelMove.getBool(); } catch { return true; } } }
    private static bool AngelBreakoutOn { get { try { return AngelBreakout == null || AngelBreakout.getBool(); } catch { return true; } } }

    // Laufraster
    private bool _moveReady, _moveFailed;
    private Vector2 _gridMin;
    private int _gw, _gh;
    private bool[] _walk;
    private byte[] _pass;                        // Bit 0: nach rechts frei, Bit 1: nach oben frei

    // Blinzeln (Host)
    private readonly Dictionary<byte, float> _blinkAt = new();
    private readonly HashSet<byte> _blinking = new();

    // Ausbruch
    private float _wrath, _wrathRestUntil;
    private int _breakout;                       // 0 ruhig, 1 Countdown, 2 Ausbruch (alle Clients)
    private float _breakoutStart;                // Time.time beim Empfang (jeder Client)
    private float _sealBothSince = -1f;          // Host
    private readonly Dictionary<byte, int> _sealHolders = new();   // Host: Spieler -> Siegel
    private int _mySeal = -1;                    // lokal gehaltenes Siegel
    private SpriteRenderer[] _sealSr;
    private TheOtherRoles.Objects.Arrow[] _sealArrows;
    private TextMeshPro _breakoutText;
    private static Sprite _sealSprite;

    // ------------------------------------------------------------------ Aufbau (lazy: beim OnBuilt fehlen die Kollider noch)

    private void AngelMoveReset()
    {
        _moveReady = _moveFailed = false;
        _walk = null; _pass = null;
        _blinkAt.Clear(); _blinking.Clear();
        _wrath = 0f; _wrathRestUntil = 0f;
        _breakout = 0; _sealBothSince = -1f; _sealHolders.Clear(); _mySeal = -1;
        _sealSr = null; _sealArrows = null; _breakoutText = null;
    }

    private bool MovableAngels => _slots.Any(s => s.Movable);

    /// <summary>Einmal in der laufenden Runde: Glass-Kollider der Engelplaetze abschalten, Laufraster bauen, eigene Kollider
    /// an die Engel haengen (jeder Client, damit die Spieler ueberall gleich an den Engeln haengen bleiben).</summary>
    private void EnsureMoveReady()
    {
        if (_moveReady || _moveFailed || !MovableAngels) return;
        try
        {
            Physics2D.SyncTransforms();
            int found = 0;
            foreach (var s in _slots)
            {
                if (!s.Movable) continue;
                Bounds? box = null;
                foreach (var c in Physics2D.OverlapPointAll(s.Pos + new Vector2(0f, 0.12f), 1 << 12))
                {
                    if (c == null || c.transform.parent == null || c.transform.parent.name != "Atlas_Glass") continue;
                    box = c.bounds;
                    c.enabled = false;
                    found++;
                }
                s.ColliderSize = box.HasValue ? (Vector2)box.Value.size : new Vector2(0.7f, 0.45f);
                s.ColliderOffset = box.HasValue ? (Vector2)box.Value.center - s.Pos : new Vector2(0f, 0.22f);
            }
            if (found == 0) return;                                   // Kollider noch nicht gebaut: naechster Tick
            BuildGrid();
            foreach (var s in _slots)
            {
                if (!s.Movable) continue;
                var go = new GameObject("AngelCollider") { layer = 12 };
                go.transform.SetParent(_root, true);
                go.transform.position = new Vector3(s.Pos.x, s.Pos.y, 0f);
                var bc = go.AddComponent<BoxCollider2D>();
                bc.size = s.ColliderSize;
                bc.offset = s.ColliderOffset;
                s.Collider = bc;
            }
            _moveReady = true;
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} angel movement ready: grid {_gw}x{_gh}, {found} static collider(s) swapped");
        }
        catch (Exception e)
        {
            _moveFailed = true;
            HalloweenPlugin.Logger.LogWarning($"{LogPrefix} angel movement unavailable: {e.Message}");
        }
    }

    private void BuildGrid()
    {
        Vector2 min = new(float.MaxValue, float.MaxValue), max = new(float.MinValue, float.MinValue);
        if (_d.Rooms != null)
            foreach (var r in _d.Rooms)
                if (r.Area != null)
                    foreach (var q in r.Area) { min = Vector2.Min(min, q); max = Vector2.Max(max, q); }
        if (min.x > max.x) throw new InvalidOperationException("no room areas");
        _gridMin = min;
        _gw = Mathf.CeilToInt((max.x - min.x) / Cell) + 1;
        _gh = Mathf.CeilToInt((max.y - min.y) / Cell) + 1;
        _walk = new bool[_gw * _gh];
        _pass = new byte[_gw * _gh];
        for (int y = 0; y < _gh; y++)
            for (int x = 0; x < _gw; x++)
                _walk[y * _gw + x] = Physics2D.OverlapCircle(CellPos(y * _gw + x), 0.28f, MaskWalls) == null;
        for (int y = 0; y < _gh; y++)
            for (int x = 0; x < _gw; x++)
            {
                int i = y * _gw + x;
                if (!_walk[i]) continue;
                var c = CellPos(i);
                if (x + 1 < _gw && _walk[i + 1] && Physics2D.Linecast(c, c + new Vector2(Cell, 0f), MaskWalls).collider == null) _pass[i] |= 1;
                if (y + 1 < _gh && _walk[i + _gw] && Physics2D.Linecast(c, c + new Vector2(0f, Cell), MaskWalls).collider == null) _pass[i] |= 2;
            }
    }

    private Vector2 CellPos(int i) => _gridMin + new Vector2(i % _gw * Cell, i / _gw * Cell);

    private int CellOf(Vector2 p)
    {
        int x = Mathf.RoundToInt((p.x - _gridMin.x) / Cell), y = Mathf.RoundToInt((p.y - _gridMin.y) / Cell);
        return x < 0 || y < 0 || x >= _gw || y >= _gh ? -1 : y * _gw + x;
    }

    /// <summary>Breitensuche vom Engel zu einer Zielzelle (Zellen bis 0,7 m um die Zielpunkte); null = kein Weg.</summary>
    private List<int> PathTo(Vector2 from, List<Vector2> targets, Vector2 home, bool leash)
    {
        int start = CellOf(from);
        if (start < 0) return null;
        var goal = new HashSet<int>();
        foreach (var t in targets)
        {
            int tc = CellOf(t);
            if (tc < 0) continue;
            for (int dy = -2; dy <= 2; dy++)
                for (int dx = -2; dx <= 2; dx++)
                {
                    int x = tc % _gw + dx, y = tc / _gw + dy;
                    if (x < 0 || y < 0 || x >= _gw || y >= _gh) continue;
                    int n = y * _gw + x;
                    if (_walk[n] && Vector2.Distance(CellPos(n), t) <= 0.7f) goal.Add(n);
                }
        }
        if (goal.Count == 0) return null;
        var prev = new int[_walk.Length];
        for (int i = 0; i < prev.Length; i++) prev[i] = -2;
        var q = new Queue<int>();
        q.Enqueue(start); prev[start] = -1;
        int hit = -1, near = start;
        float nearD = Vector2.Distance(from, targets[0]);
        while (q.Count > 0)
        {
            int c = q.Dequeue();
            if (goal.Contains(c)) { hit = c; break; }
            float dc = Vector2.Distance(CellPos(c), targets[0]);
            if (dc < nearD) { nearD = dc; near = c; }
            int x = c % _gw, y = c / _gw;
            // vier Nachbarn; die Startzelle darf belegt sein (der Engel steht auf seinem Sockel)
            Try(c, x + 1 < _gw ? c + 1 : -1, (_pass[c] & 1) != 0 || c == start);
            Try(c, x > 0 ? c - 1 : -1, x > 0 && ((_pass[c - 1] & 1) != 0 || c == start));
            Try(c, y + 1 < _gh ? c + _gw : -1, (_pass[c] & 2) != 0 || c == start);
            Try(c, y > 0 ? c - _gw : -1, y > 0 && ((_pass[c - _gw] & 2) != 0 || c == start));
        }
        // an der Leine: so nah heran, wie der Umkreis um den Platz erlaubt
        if (hit < 0 && leash && near != start) hit = near;
        if (hit < 0) return null;
        var path = new List<int>();
        for (int c = hit; c >= 0; c = prev[c]) path.Add(c);
        path.Reverse();
        return path;

        void Try(int c, int n, bool open)
        {
            if (n < 0 || !open || prev[n] != -2 || !_walk[n]) return;
            if (leash && Vector2.Distance(CellPos(n), home) > HomeLeash) return;
            prev[n] = c;
            q.Enqueue(n);
        }
    }

    // ------------------------------------------------------------------ Host: Blinzeln, Spruenge, Zornpegel

    /// <summary>Wer blinzelt in diesem Tick? (Host; wer gerade einen Engel im Blick hat, alle 8 bis 14 s einen Tick lang.)
    /// Wer keinen Engel sieht, blinzelt nicht und merkt nichts davon.</summary>
    private void BlinkTick(List<PlayerControl> players, AngelSight[,] sights)
    {
        _blinking.Clear();
        if (!AmHost || _breakout == 0) return;                                // Blinzeln zaehlt nur, solange die Engel springen koennen
        float now = Time.time;
        for (int n = 0; n < players.Count; n++)
        {
            var p = players[n];
            bool sees = false;
            for (int i = 0; i < _slots.Count && !sees; i++) sees = sights[n, i] != AngelSight.Hidden;
            if (!sees) continue;                                              // Uhr laeuft weiter, Lidschlag erst mit Engel im Blick
            if (!_blinkAt.TryGetValue(p.PlayerId, out float at)) { _blinkAt[p.PlayerId] = now + Random.Range(BlinkMin, BlinkMax); continue; }
            if (now < at) continue;
            _blinking.Add(p.PlayerId);
            _blinkAt[p.PlayerId] = now + Random.Range(BlinkMin, BlinkMax);
            SendBlink(p.PlayerId);
            ShowBlinkIfMe(p.PlayerId);
        }
    }

    // ------------------------------------------------------------------ Lidschlag (lokal)

    private static SpriteRenderer _lidTop, _lidBottom;
    private static float _blinkStart = -1f;
    private const float LidClose = 0.07f, LidHold = 0.06f, LidOpen = 0.09f;

    internal static void RegisterBlinkToggle()
    {
        try
        {
            var domain = AppDomain.CurrentDomain;
            lock (domain)
            {
                if (domain.GetData("Unknowns.Options.Toggles") is not List<object> list)
                {
                    list = new List<object>();
                    domain.SetData("Unknowns.Options.Toggles", list);
                }
                list.Add(new object[] { (Func<string>)(() => "Angel Blink Effect"), (Func<bool>)(() => BlinkEffect == null || BlinkEffect.Value),
                                        (Action<bool>)(v => { if (BlinkEffect != null) BlinkEffect.Value = v; }) });
            }
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} blink toggle not registered: {e.Message}"); }
    }

    private static void ShowBlinkIfMe(byte pid)
    {
        try
        {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || lp.PlayerId != pid || lp.Data == null || lp.Data.IsDead) return;
            if (BlinkEffect != null && !BlinkEffect.Value) return;           // geblinzelt wird trotzdem (Host), nur ohne Bild
            _blinkStart = Time.time;
        }
        catch { }
    }

    /// <summary>Jeden Frame: Augenlider oben und unten schliessen sich kurz und gehen wieder auf (HUD-Ebene).</summary>
    private static void BlinkFrame()
    {
        if (_blinkStart < 0f) return;
        float t = Time.time - _blinkStart;
        float total = LidClose + LidHold + LidOpen;
        if (t > total || MeetingHud.Instance != null)
        {
            _blinkStart = -1f;
            if (_lidTop != null) _lidTop.gameObject.SetActive(false);
            if (_lidBottom != null) _lidBottom.gameObject.SetActive(false);
            return;
        }
        var hud = HudManager.InstanceExists ? HudManager.Instance : null;
        var cam = Camera.main;
        if (hud == null || cam == null) return;
        if (_lidTop == null) { _lidTop = MakeLid(hud.transform, "AngelLidTop"); _lidBottom = MakeLid(hud.transform, "AngelLidBottom"); }
        float halfH = cam.orthographicSize, halfW = halfH * cam.aspect;
        float close = t < LidClose ? t / LidClose : t < LidClose + LidHold ? 1f : 1f - (t - LidClose - LidHold) / LidOpen;
        close = Mathf.SmoothStep(0f, 1f, close);
        float lidH = halfH * 1.15f;
        foreach (var (sr, sign) in new[] { (_lidTop, 1f), (_lidBottom, -1f) })
        {
            sr.gameObject.SetActive(true);
            sr.transform.localScale = new Vector3(halfW * 2.4f, lidH / 8f, 1f);   // Sprite ist 1x8 Einheiten
            float y = sign * (halfH + lidH / 2f - close * (halfH + 0.06f));
            sr.transform.localPosition = new Vector3(0f, y, -400f);
        }
    }

    private static SpriteRenderer MakeLid(Transform parent, string name)
    {
        var go = new GameObject(name) { layer = 5 };
        go.transform.SetParent(parent, false);
        var sr = go.AddComponent<SpriteRenderer>();
        var tex = new Texture2D(1, 8, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset };
        var px = new Color32[8];
        for (int i = 0; i < 8; i++) px[i] = new Color32(6, 4, 8, (byte)(i == 0 || i == 7 ? 200 : 255));
        tex.SetPixels32(px); tex.Apply();
        sr.sprite = Sprite.Create(tex, new Rect(0, 0, 1, 8), new Vector2(0.5f, 0.5f), 1f);
        sr.sortingOrder = 1000;
        go.transform.localScale = new Vector3(1f, 1f / 8f, 1f);
        go.SetActive(false);
        return sr;
    }

    private static void SendBlink(byte pid)
    {
        try
        {
            if (PlayerControl.LocalPlayer == null || AmongUsClient.Instance == null) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubBlink);
            w.Write(pid);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} blink send failed: {e.Message}"); }
    }

    /// <summary>Host: unbeobachtete Engel springen auf ihr Ziel zu (Sub 11).</summary>
    private void AngelMoveHost(List<PlayerControl> players, AngelSight[,] sights, bool[] blinked)
    {
        // User 25.10.: die Engel verlassen ihren Platz nur waehrend "Angel Breakout" (Countdown: an der Leine, Ausbruch: frei)
        if (!AmHost || !_moveReady || _breakout == 0 || !AngelMoveOn && _breakout != 2) return;
        float now = Time.time;
        bool rampage = _breakout == 2;
        for (int i = 0; i < _slots.Count; i++)
        {
            var s = _slots[i];
            if (!s.Movable || _angelWatched[i] || now < s.NextJump) continue;
            var targets = new List<Vector2>();
            float best = float.MaxValue;
            for (int n = 0; n < players.Count; n++)
            {
                var p = players[n];
                if (p.inVent || p.onLadder) continue;
                var pos = p.GetTruePosition();
                float d = Vector2.Distance(pos, s.Pos);
                if (!rampage)
                {
                    _aggro.TryGetValue((p.PlayerId, i), out float a);
                    bool wants = sights[n, i] == AngelSight.Away && (a >= AngelStareAt || blinked[n]);
                    if (!wants || d >= best) continue;
                    best = d;
                    targets.Clear();
                }
                targets.Add(pos);
            }
            if (targets.Count == 0) continue;
            s.NextJump = now + (rampage ? RampageEvery : JumpEvery);
            var path = PathTo(s.Pos, targets, s.Home, !rampage);
            if (path == null || path.Count < 2) continue;
            var to = PickJump(s, path, targets, players);
            if (to == null) continue;
            MoveAngel(i, to.Value);
            SendAngelMove(i, to.Value);
        }
    }

    /// <summary>Weitester Wegpunkt bis 1,5 m, der nicht naeher als 0,8 m an ein Ziel geht, frei von Spielern und anderen Engeln
    /// ist und in gerader Linie erreichbar (Waende, geschlossene Tueren).</summary>
    private Vector2? PickJump(AngelSlot s, List<int> path, List<Vector2> targets, List<PlayerControl> players)
    {
        var pts = new List<Vector2>();
        float acc = 0f;
        var last = s.Pos;
        for (int k = 1; k < path.Count; k++)
        {
            var c = CellPos(path[k]);
            acc += Vector2.Distance(last, c);
            last = c;
            if (acc > JumpMax) break;
            if (targets.Any(t => Vector2.Distance(t, c) < JumpKeep)) break;
            pts.Add(c);
        }
        if (s.Collider != null) s.Collider.enabled = false;
        try
        {
            for (int k = pts.Count - 1; k >= 0; k--)
            {
                var c = pts[k];
                if (players.Any(p => Vector2.Distance(p.GetTruePosition(), c) < 0.55f)) continue;
                if (_slots.Any(o => o != s && Vector2.Distance(o.Pos, c) < 0.75f)) continue;
                if (Physics2D.Linecast(s.Pos + new Vector2(0f, 0.1f), c + new Vector2(0f, 0.1f), MaskWalls).collider != null) continue;
                return c;
            }
        }
        finally { if (s.Collider != null) s.Collider.enabled = true; }
        return null;
    }

    private void MoveAngel(int i, Vector2 to)
    {
        if (i < 0 || i >= _slots.Count) return;
        var s = _slots[i];
        var delta = to - s.Pos;
        if (delta.sqrMagnitude < 0.0001f) return;
        s.Pos = to;
        foreach (var pv in s.Props)
        {
            if (pv.Sr == null) continue;
            var t = pv.Sr.transform;
            // Tiefe wie Atlas (SortZ: y / 1000): weiter unten = weiter vorn
            t.position += new Vector3(delta.x, delta.y, delta.y / 1000f);
            pv.Pos = to;
        }
        if (s.Collider != null) s.Collider.transform.position = new Vector3(to.x, to.y, 0f);
        try
        {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null) return;
            float vol = Mathf.Clamp01(1f - Vector2.Distance(lp.GetTruePosition(), to) / 8f);
            if (vol > 0.05f) AtlasMaps.Sfx("grind", 0.35f * vol);
        }
        catch { }
    }

    /// <summary>Alle Engel zurueck auf ihren Platz (Meeting, Rundenende; jeder Client).</summary>
    private void AngelsHome()
    {
        for (int i = 0; i < _slots.Count; i++)
        {
            var s = _slots[i];
            if (!s.Movable || (s.Pos - s.Home).sqrMagnitude < 0.0001f) continue;
            var delta = s.Home - s.Pos;
            s.Pos = s.Home;
            foreach (var pv in s.Props)
            {
                if (pv.Sr == null) continue;
                pv.Sr.transform.position += new Vector3(delta.x, delta.y, delta.y / 1000f);
                pv.Pos = s.Home;
            }
            if (s.Collider != null) s.Collider.transform.position = new Vector3(s.Home.x, s.Home.y, 0f);
            s.NextJump = 0f;
        }
    }

    /// <summary>Host: Zornpegel; voll -> Engel-Ausbruch.</summary>
    private void WrathTick(List<PlayerControl> players, AngelSight[,] sights)
    {
        if (!AmHost || _breakout != 0 || !AngelBreakoutOn || !AngelAttackOn || !MovableAngels || !_moveReady) return;
        float now = Time.time;
        if (now < _wrathRestUntil) return;
        float rate = -WrathCalm;
        for (int n = 0; n < players.Count; n++)
        {
            bool away = false, near = false;
            var pos = players[n].GetTruePosition();
            for (int i = 0; i < _slots.Count; i++)
            {
                if (!_slots[i].Movable) continue;
                if (sights[n, i] == AngelSight.Away) away = true;
                if (Vector2.Distance(pos, _slots[i].Pos) < WrathNearDist) near = true;
            }
            if (away) rate += WrathAway;
            if (near) rate += WrathNear;
        }
        _wrath = Mathf.Clamp(_wrath + rate * AngelTickEvery, 0f, WrathFull);
        if (_wrath < WrathFull || CriticalSabotageActive()) return;
        _wrath = 0f;
        SendBreakout(1);
        ApplyBreakout(1);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} angel breakout: wrath full, seals needed");
    }

    private static bool CriticalSabotageActive()
    {
        try
        {
            var ship = ShipStatus.Instance;
            if (ship == null) return false;
            foreach (var t in new[] { SystemTypes.Reactor, SystemTypes.Laboratory, SystemTypes.LifeSupp, SystemTypes.HeliSabotage })
            {
                if (!ship.Systems.ContainsKey(t)) continue;
                var c = ship.Systems[t].TryCast<ICriticalSabotage>();
                if (c != null && c.IsActive) return true;
            }
        }
        catch { }
        return false;
    }

    /// <summary>Host: Siegel pruefen, Countdown ablaufen lassen.</summary>
    private void BreakoutHostTick()
    {
        if (!AmHost || _breakout != 1) return;
        float now = Time.time;
        bool[] held = new bool[SealPos.Length];
        foreach (var kv in _sealHolders.ToList())
        {
            var p = Helpers.playerById(kv.Key);
            if (p == null || p.Data == null || p.Data.IsDead || p.Data.Disconnected || Vector2.Distance(p.GetTruePosition(), SealPos[kv.Value]) > SealHostReach)
            {
                _sealHolders.Remove(kv.Key);
                continue;
            }
            held[kv.Value] = true;
        }
        if (held.All(h => h))
        {
            if (_sealBothSince < 0f) _sealBothSince = now;
            if (now - _sealBothSince >= SealHoldNeed)
            {
                SendBreakout(0);
                ApplyBreakout(0);
                _wrathRestUntil = now + WrathRest;
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} angel breakout: sealed");
                return;
            }
        }
        else _sealBothSince = -1f;
        if (now - _breakoutStart >= BreakoutSecs)
        {
            SendBreakout(2);
            ApplyBreakout(2);
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} angel breakout: the angels are loose");
        }
    }

    // ------------------------------------------------------------------ alle Clients: Zustand, Siegel, Anzeige

    private void ApplyBreakout(int phase)
    {
        _breakout = phase;
        if (phase == 1)
        {
            _breakoutStart = Time.time;
            _sealBothSince = -1f;
            _sealHolders.Clear();
            _mySeal = -1;
            AtlasMaps.Sfx("whoosh", 0.8f);
            try { GraveyardWorld.PlayKnell(0.9f); } catch { }
        }
        if (phase == 2) { try { GraveyardWorld.PlayKnell(0.9f); } catch { } }
        if (phase != 1) _mySeal = -1;
        if (phase == 0) _wrath = 0f;
        UpdateSealArt();
    }

    /// <summary>Meeting: Ausbruch vorbei, Engel zurueck (jeder Client).</summary>
    private void BreakoutMeeting()
    {
        if (_breakout != 0) ApplyBreakout(0);
        if (AmHost && _wrathRestUntil < Time.time + 10f) _wrathRestUntil = Time.time + 10f;
        _wrath = 0f;
        AngelsHome();
        HideBreakoutHud();
    }

    /// <summary>Jeden Frame: Siegel anbieten, Pfeile und Zeile oben (alle Clients).</summary>
    private void BreakoutFrame()
    {
        BlinkFrame();
        if (_breakout == 0 || !MovableAngels) { HideBreakoutHud(); return; }
        if (MeetingHud.Instance != null || ExileController.Instance != null) { HideBreakoutHud(); return; }
        var lp = PlayerControl.LocalPlayer;
        bool alive = lp != null && lp.Data != null && !lp.Data.IsDead;
        if (_breakout == 1)
        {
            float left = Mathf.Max(0f, BreakoutSecs - (Time.time - _breakoutStart));
            ShowBreakoutHud($"ANGEL BREAKOUT  {Mathf.CeilToInt(left)}s  -  hold both seals", new Color(1f, 0.35f, 0.35f));
            if (alive)
            {
                // gehaltenes Siegel loslassen, sobald man weggeht
                if (_mySeal >= 0 && !AtlasMaps.CanReach(SealPos[_mySeal], SealReach + 0.3f)) { SendSealHold(_mySeal, false); _mySeal = -1; }
                for (int k = 0; k < SealPos.Length; k++)
                {
                    if (!AtlasMaps.CanReach(SealPos[k], SealReach)) continue;
                    int idx = k;
                    if (_mySeal == idx) AtlasMaps.OfferUse("HOLDING", "task_villa_btn_candle.png", () => { }, enabled: false);
                    else AtlasMaps.OfferUse("HOLD", "task_villa_btn_candle.png", () => HoldSeal(idx));
                    break;
                }
            }
            else if (_mySeal >= 0) { SendSealHold(_mySeal, false); _mySeal = -1; }
            UpdateArrows(alive && lp != null ? lp.GetTruePosition() : (Vector2?)null);
        }
        else
        {
            ShowBreakoutHud("THE ANGELS ARE LOOSE", new Color(0.75f, 0.85f, 1f));
            UpdateArrows(null);
        }
        float pulse = 0.65f + 0.35f * Mathf.Sin(Time.time * 4f);
        if (_sealSr != null)
            for (int k = 0; k < _sealSr.Length; k++)
                if (_sealSr[k] != null) _sealSr[k].color = _mySeal == k ? new Color(0.6f, 1f, 0.7f, 1f) : new Color(1f, 0.45f + 0.2f * pulse, 0.45f, pulse);
    }

    private void HoldSeal(int k)
    {
        if (_breakout != 1) return;
        if (_mySeal >= 0 && _mySeal != k) SendSealHold(_mySeal, false);
        _mySeal = k;
        SendSealHold(k, true);
        if (AmHost) _sealHolders[PlayerControl.LocalPlayer.PlayerId] = k;
        AtlasMaps.Sfx("click", 0.7f);
    }

    private void UpdateSealArt()
    {
        bool show = _breakout == 1;
        if (show && _sealSr == null && _root != null)
        {
            _sealSprite ??= PaintSeal();
            _sealSr = new SpriteRenderer[SealPos.Length];
            int layer = _root.gameObject.layer;
            var holder = new GameObject("Hollowmere_Seals").transform;
            holder.SetParent(_root, false);
            var ls = _root.lossyScale;
            holder.localScale = new Vector3(1f / ls.x, 1f / ls.y, 1f / ls.z);
            holder.position = Vector3.zero;
            for (int k = 0; k < SealPos.Length; k++)
            {
                var go = new GameObject($"Seal_{k}") { layer = layer };
                go.transform.SetParent(holder, false);
                go.transform.localPosition = new Vector3(SealPos[k].x, SealPos[k].y, GraveyardWorld.AtlasMuseumBuilderFloorZ - 1.3f);
                _sealSr[k] = go.AddComponent<SpriteRenderer>();
                _sealSr[k].sprite = _sealSprite;
            }
        }
        if (_sealSr != null)
            foreach (var sr in _sealSr) if (sr != null && sr.gameObject.activeSelf != show) sr.gameObject.SetActive(show);
        if (!show) UpdateArrows(null);
    }

    private void UpdateArrows(Vector2? me)
    {
        if (me == null)
        {
            if (_sealArrows != null) foreach (var a in _sealArrows) if (a?.arrow != null) Object.Destroy(a.arrow);
            _sealArrows = null;
            return;
        }
        if (_sealArrows == null)
        {
            _sealArrows = new TheOtherRoles.Objects.Arrow[SealPos.Length];
            for (int k = 0; k < SealPos.Length; k++) _sealArrows[k] = new TheOtherRoles.Objects.Arrow(new Color(1f, 0.35f, 0.35f));
        }
        for (int k = 0; k < SealPos.Length; k++)
        {
            var a = _sealArrows[k];
            if (a?.arrow == null) continue;
            bool near = Vector2.Distance(me.Value, SealPos[k]) < 2f;
            if (a.arrow.activeSelf == near) a.arrow.SetActive(!near);
            if (!near) a.Update(SealPos[k], _mySeal == k ? new Color(0.6f, 1f, 0.7f) : new Color(1f, 0.35f, 0.35f));
        }
    }

    private void ShowBreakoutHud(string line, Color color)
    {
        try
        {
            var hud = HudManager.InstanceExists ? HudManager.Instance : null;
            if (hud == null) return;
            if (_breakoutText == null)
            {
                var go = new GameObject("Hollowmere_BreakoutHud") { layer = 5 };
                go.transform.SetParent(hud.transform, false);
                go.transform.localPosition = new Vector3(0f, 2.25f, -5f);   // unter Atlas' Krisenzeile (2,55)
                _breakoutText = go.AddComponent<TextMeshPro>();
                var src = hud.GetComponentInChildren<TextMeshPro>(true);
                if (src != null) { _breakoutText.font = src.font; _breakoutText.fontSharedMaterial = src.fontSharedMaterial; }
                _breakoutText.fontSize = 2.0f;   // schmal genug, dass die Aufgabenliste links frei bleibt (Autotest 25.10.)
                _breakoutText.alignment = TextAlignmentOptions.Center;
                _breakoutText.enableWordWrapping = false;
                _breakoutText.rectTransform.sizeDelta = new Vector2(10f, 1f);
                var mr = go.GetComponent<MeshRenderer>();
                if (mr != null) mr.sortingOrder = 500;
            }
            if (_breakoutText.text != line) _breakoutText.text = line;
            _breakoutText.color = color;
            if (!_breakoutText.gameObject.activeSelf) _breakoutText.gameObject.SetActive(true);
        }
        catch { }
    }

    private void HideBreakoutHud()
    {
        try { if (_breakoutText != null && _breakoutText.gameObject.activeSelf) _breakoutText.gameObject.SetActive(false); } catch { }
        if (_breakout == 0 && _sealArrows != null) UpdateArrows(null);
    }

    private void AngelMoveDestroy()
    {
        UpdateArrows(null);
        try { if (_breakoutText != null) Object.Destroy(_breakoutText.gameObject); } catch { }
        _breakoutText = null;
        foreach (var s in _slots) { try { if (s.Collider != null) Object.Destroy(s.Collider.gameObject); } catch { } s.Collider = null; }
        _breakout = 0;
    }

    /// <summary>Siegel: Kreis aus getrocknetem Blut mit Ring, Strahlen und Mittelpunkt (zur Laufzeit gemalt, ohne Schrift).</summary>
    private static Sprite PaintSeal()
    {
        const int N = 160;
        var tex = new Texture2D(N, N, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset };
        var px = new Color32[N * N];
        float c = (N - 1) / 2f;
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float dx = (x - c) / c, dy = (y - c) / c / 0.62f;        // flach auf dem Boden (Ellipse)
                float r = Mathf.Sqrt(dx * dx + dy * dy), a = Mathf.Atan2(dy, dx);
                float v = 0f;
                v = Mathf.Max(v, Band(r, 0.93f, 0.035f));
                v = Mathf.Max(v, Band(r, 0.78f, 0.022f));
                v = Mathf.Max(v, Band(r, 0.22f, 0.05f));
                if (r < 0.78f && r > 0.26f) v = Mathf.Max(v, Band(Mathf.Abs(Mathf.Sin(a * 4f)) * r, 0f, 0.03f));   // acht Strahlen
                if (r > 0.79f && r < 0.92f) v = Mathf.Max(v, 0.55f * Band(Mathf.Abs(Mathf.Sin(a * 12f)), 0f, 0.18f)); // Kerben im Ring
                byte al = (byte)Mathf.Clamp(v * 235f, 0f, 255f);
                px[y * N + x] = new Color32(255, 255, 255, al);
            }
        tex.SetPixels32(px);
        tex.Apply();
        return Sprite.Create(tex, new Rect(0, 0, N, N), new Vector2(0.5f, 0.5f), N / 1.5f);

        static float Band(float v, float at, float w) => Mathf.Clamp01(1f - Mathf.Abs(v - at) / w);
    }

    // ------------------------------------------------------------------ Autotest (UC_HALLOWEEN_DIAG=villalarge,angels)

    /// <summary>Engel-Test: in den Friedhof, Ruecken zu den rechten Engeln (Spruenge), dann Ausbruch erzwingen, Siegel
    /// fotografieren und den freien Lauf abwarten (der Spieler schaut weg und wird geholt).</summary>
    private void DiagAngels(PlayerControl lp)
    {
        float now = Time.time;
        var spot = new Vector2(44.0f - 17f, 14f - 18.3f);
        void Face()
        {
            try { lp.cosmetics.currentBodySprite.BodySprite.flipX = true; } catch { }
            try { if (Vector2.Distance(lp.GetTruePosition(), spot) > 0.4f) lp.NetTransform.RpcSnapTo(spot); } catch { }
        }
        string Where() => string.Join(" ", _slots.Where(s => s.Movable).Select(s => $"{s.Pos.x:F1}/{s.Pos.y:F1}{((s.Pos - s.Home).sqrMagnitude > 0.01f ? "*" : "")}"));
        switch (_diagStep)
        {
            case 0:
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: angels ready {_moveReady} (grid {_gw}x{_gh}), movable {_slots.Count(s => s.Movable)}");
                try { lp.NetTransform.RpcSnapTo(spot); } catch { }
                SendBreakout(1); ApplyBreakout(1);                          // Spruenge gibt es nur waehrend der Sabotage
                _diagStep = 1; _diagAt = now + 1f;
                break;
            case 1: case 2: case 3: case 4: case 5: case 6:   // 1,5 s Abstand: vor dem Kill (Wert voll nach 5 s) weiter
                Face();
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: angels t{_diagStep} player {lp.GetTruePosition().x:F1}/{lp.GetTruePosition().y:F1} dead {lp.Data.IsDead} at {Where()}");
                if (_diagStep == 3) AtlasMaps.Shot("angels", "jump");
                if (_diagStep == 2) { _blinkStart = Time.time - LidClose - 0.02f; BlinkFrame(); AtlasMaps.Shot("angels", "blink"); }
                _diagStep = _diagStep == 3 ? 7 : _diagStep + 1; _diagAt = now + 1.5f;
                if (lp.Data.IsDead) _diagStep = 7;
                break;
            case 7:
                AtlasMaps.Shot("angels", "after_jumps");
                AngelsHome();
                _aggro.Clear();
                // lebend fuer den Ausbruch: im Freeplay neu beleben geht nicht, also nur weiter, wenn noch lebendig
                try { lp.NetTransform.RpcSnapTo(SealPos[0] + new Vector2(0.4f, -0.3f)); } catch { }
                SendBreakout(1); ApplyBreakout(1);
                _diagStep = 8; _diagAt = now + 2f;
                break;
            case 8:
                AtlasMaps.Shot("angels", "breakout");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: breakout phase {_breakout}, seals {(_sealSr != null ? _sealSr.Length : 0)}, arrows {(_sealArrows != null ? _sealArrows.Length : 0)}");
                HoldSeal(0);
                _diagStep = 9; _diagAt = now + 1f;
                break;
            case 9:
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: holding seal {_mySeal}, host holders {_sealHolders.Count}");
                AtlasMaps.Shot("angels", "hold");
                try { lp.NetTransform.RpcSnapTo(spot); } catch { }
                _diagStep = 10; _diagAt = now + 45f;
                break;
            case 10: case 11: case 12: case 13: case 14: case 15: case 16: case 17:
                Face();
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: rampage t{_diagStep} phase {_breakout} dead {lp.Data.IsDead} at {Where()}");
                if (_diagStep == 10) AtlasMaps.Shot("angels", "loose");
                _diagStep++; _diagAt = now + 1.5f;
                if (lp.Data.IsDead) _diagStep = 18;
                break;
            default:
                AtlasMaps.Shot("angels", "end");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: angels done, player dead {lp.Data.IsDead}, victims {string.Join(",", AngelVictims)}");
                _diagTask++; _diagStep = 0; _diagAt = now + 1f;
                break;
        }
    }

    // ------------------------------------------------------------------ RPC

    private static void SendAngelMove(int slot, Vector2 to)
    {
        try
        {
            if (PlayerControl.LocalPlayer == null || AmongUsClient.Instance == null) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubAngelMove);
            w.Write((byte)slot);
            w.Write(to.x);
            w.Write(to.y);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} angel move send failed: {e.Message}"); }
    }

    private static void SendBreakout(int phase)
    {
        try
        {
            if (PlayerControl.LocalPlayer == null || AmongUsClient.Instance == null) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubBreakout);
            w.Write((byte)phase);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} breakout send failed: {e.Message}"); }
    }

    private static void SendSealHold(int seal, bool on)
    {
        try
        {
            if (PlayerControl.LocalPlayer == null || AmongUsClient.Instance == null || AmHost) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubSealHold);
            w.Write((byte)seal);
            w.Write(on);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} seal send failed: {e.Message}"); }
        if (AmHost && _current != null && PlayerControl.LocalPlayer != null && !on) _current._sealHolders.Remove(PlayerControl.LocalPlayer.PlayerId);
    }

    /// <summary>Sub 11-13 (aus HandleRpc).</summary>
    private static void HandleAngelMoveRpc(byte sub, Hazel.MessageReader reader)
    {
        var w = _current;
        if (sub == SubAngelMove)
        {
            int slot = reader.ReadByte();
            float x = reader.ReadSingle(), y = reader.ReadSingle();
            if (w == null || !UCRpc.RequireHost("Hollowmere.AngelMove")) return;
            if (slot < w._slots.Count && w._slots[slot].Movable) w.MoveAngel(slot, new Vector2(x, y));
        }
        else if (sub == SubBreakout)
        {
            int phase = reader.ReadByte();
            if (w == null || !UCRpc.RequireHost("Hollowmere.Breakout")) return;
            if (phase <= 2) w.ApplyBreakout(phase);
        }
        else if (sub == SubBlink)
        {
            byte pid = reader.ReadByte();
            if (!UCRpc.RequireHost("Hollowmere.Blink")) return;
            ShowBlinkIfMe(pid);
        }
        else if (sub == SubSealHold)
        {
            int seal = reader.ReadByte();
            bool on = reader.ReadBoolean();
            var from = UCRpc.Sender;
            if (w == null || !AmHost || from == null || seal >= SealPos.Length || w._breakout != 1) return;
            if (!on) { if (w._sealHolders.TryGetValue(from.PlayerId, out int had) && had == seal) w._sealHolders.Remove(from.PlayerId); return; }
            if (from.Data == null || from.Data.IsDead || Vector2.Distance(from.GetTruePosition(), SealPos[seal]) > SealHostReach) return;
            w._sealHolders[from.PlayerId] = seal;
        }
    }

    // ------------------------------------------------------------------ Notfallknopf waehrend des Countdowns gesperrt

    [HarmonyPatch(typeof(EmergencyMinigame), nameof(EmergencyMinigame.Update))]
    private static class BreakoutEmergencyPatch
    {
        [HarmonyPriority(Priority.Last)]
        public static void Postfix(EmergencyMinigame __instance)
        {
            if (_current == null || _current._breakout != 1 || __instance == null) return;
            try
            {
                __instance.StatusText.text = TranslationController.Instance.GetString(StringNames.EmergencyDuringCrisis, Array.Empty<Il2CppSystem.Object>());
                __instance.NumberText.text = string.Empty;
                __instance.ClosedLid.gameObject.SetActive(true);
                __instance.OpenLid.gameObject.SetActive(false);
                __instance.ButtonActive = false;
            }
            catch { }
        }
    }
}
