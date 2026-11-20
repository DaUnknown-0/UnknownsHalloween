// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereUpperTasks.Games - die sechs eigenen Minispiele im Obergeschoss (18.11.). Lage und Groessen passen zu den Bildern aus
// tools/gen_villa_uptasks.py (Tafel 720 x 520 Pixel = 7,2 x 5,2 Einheiten um 0/0, 100 Pixel je Einheit).
//
//   records : Sort the Family Records (Attic)    - Karteikarten nach Jahrzehnt in drei Schubladen ziehen
//   photos  : Develop the Set Photos (Darkroom)  - zwei Fotos durch Entwickler, Stopbad und Fixierer, dann an die Leine
//   dress   : Dress the Mannequin (Sewing Room)  - Kleid, Schaerpe und Schleier nach der Musterkarte anziehen
//   tapes   : Rewind the Ghost Tapes (Bedroom)   - Kurbel zurueckspulen, dann beim Abspielen drei Geister markieren
//   toys    : Put Away the Toys (Nursery)        - fuenf Spielsachen in die Kiste, die Puppe klettert einmal wieder heraus
//   bath    : Drain the Bloody Bath (Bathroom)   - Stoepsel ziehen, dann die Blutflecken aus der Wanne schrubben

using System;
using System.Collections.Generic;
using UnityEngine;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

/// <summary>Ziehbares Teil mit Ruheplatz und kleiner Rueckflug-Animation.</summary>
internal sealed class UpperPiece
{
    public SpriteRenderer Sr;
    public Vector2 Home, Pos;
    public float Grab = 0.55f;
    public int Tag, Tag2;
    public bool Gone, Busy;
    public int BaseOrder;
    private Vector2 _from, _to;
    private float _t = -1f, _dur;
    private Action _after;

    public UpperPiece(SpriteRenderer sr, Vector2 pos, int order)
    {
        Sr = sr; Home = Pos = pos; BaseOrder = order;
        UpperArt.Place(sr, pos);
    }

    public void Set(Vector2 p) { Pos = p; UpperArt.Place(Sr, p); }

    public void Fly(Vector2 to, float dur, Action after = null)
    {
        _from = Pos; _to = to; _dur = Mathf.Max(0.01f, dur); _t = 0f; _after = after; Busy = true;
    }

    public void Tick(float dt)
    {
        if (_t < 0f) return;
        _t += dt / _dur;
        float k = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(_t));
        Set(Vector2.Lerp(_from, _to, k));
        if (_t >= 1f) { _t = -1f; Busy = false; var a = _after; _after = null; a?.Invoke(); }
    }
}

/// <summary>Gemeinsame Zieh-Logik: Teil fassen (oberstes in Reichweite), mitziehen, loslassen -> Drop.</summary>
internal abstract class UpperDragGame : IUpperGame
{
    public abstract string Name { get; }
    public abstract float Progress { get; }
    public bool Done { get; protected set; }
    protected readonly List<UpperPiece> Pieces = new();
    protected UpperPiece Held;
    protected Vector2 HeldOffset;
    protected Transform Root;
    protected System.Random Rnd;

    public abstract void Build(Transform root, System.Random rnd);
    protected virtual bool CanGrab(UpperPiece p) => !p.Gone && !p.Busy;
    protected abstract void Drop(UpperPiece p);
    protected virtual void OnTick(float dt, Vector2 mouse, bool down, bool pressed) { }

    public virtual void Tick(float dt, Vector2 mouse, bool down, bool pressed)
    {
        // per Index: ein Rueckruf am Ende einer Bewegung darf neue Teile anhaengen (Foto 2 nach dem Aufhaengen von Foto 1)
        for (int i = 0; i < Pieces.Count; i++) Pieces[i].Tick(dt);
        if (!Done)
        {
            if (pressed && Held == null)
            {
                UpperPiece best = null;
                foreach (var p in Pieces)
                    if (CanGrab(p) && Vector2.Distance(p.Pos, mouse) < p.Grab && (best == null || p.Sr.sortingOrder > best.Sr.sortingOrder)) best = p;
                if (best != null)
                {
                    Held = best; HeldOffset = best.Pos - mouse;
                    UpperArt.Order(best.Sr, 40);
                    UpperArt.Sfx("click", 0.35f);
                }
            }
            if (Held != null)
            {
                if (down) Held.Set(mouse + HeldOffset);
                else { var h = Held; Held = null; UpperArt.Order(h.Sr, h.BaseOrder); Drop(h); }
            }
        }
        OnTick(dt, mouse, down, pressed);
    }

    // ---- Autotest: ein Teil fassen und an ein Ziel ziehen
    protected float SimT;
    protected int SimPhase;
    protected UpperPiece SimPiece;
    protected Vector2 SimTo, SimMouse;

    /// <summary>Zug in drei Teilen: hinfahren (0,25 s), gedrueckt ziehen (0,4 s), loslassen und kurz warten.</summary>
    protected void SimDrag(float dt, Func<(UpperPiece, Vector2)?> next, out Vector2 mouse, out bool down)
    {
        SimT += dt;
        switch (SimPhase)
        {
            case 0:
                var n = next();
                if (n == null) { mouse = SimMouse; down = false; return; }
                (SimPiece, SimTo) = n.Value;
                SimPhase = 1; SimT = 0f;
                goto case 1;
            case 1:
                SimMouse = Vector2.Lerp(SimMouse, SimPiece.Pos, Mathf.Clamp01(SimT / 0.25f));
                mouse = SimMouse; down = false;
                if (SimT >= 0.25f) { SimPhase = 2; SimT = 0f; SimMouse = SimPiece.Pos; }
                return;
            case 2:
                // erst ein Bild gedrueckt am Teil (pressed), dann ziehen
                mouse = Vector2.Lerp(SimPiece.Pos, SimTo, Mathf.Clamp01((SimT - 0.05f) / 0.4f));
                if (SimT < 0.05f) mouse = SimMouse;
                down = true;
                if (SimT >= 0.5f) { SimPhase = 3; SimT = 0f; SimMouse = SimTo; }
                return;
            default:
                mouse = SimMouse; down = false;
                if (SimT >= 0.35f) { SimPhase = 0; SimT = 0f; }
                return;
        }
    }

    public abstract void Simulate(float dt, out Vector2 mouse, out bool down);
    public virtual void Dispose() { }
}

// ============================================================ Sort the Family Records (Attic)

internal sealed class RecordsGame : UpperDragGame
{
    public override string Name => "records";
    private static readonly Vector2[] Drawers = { new(2.4f, 1.3f), new(2.4f, 0.0f), new(2.4f, -1.3f) };
    private readonly SpriteRenderer[] _drawer = new SpriteRenderer[3];
    private readonly float[] _drawerOut = new float[3];
    private readonly float[] _shake = new float[3];
    private int _filed, _total;
    private float _doneT = -1f;
    public override float Progress => _total == 0 ? 0f : (float)_filed / _total;

    public override void Build(Transform root, System.Random rnd)
    {
        Root = root; Rnd = rnd;
        UpperArt.Add(root, "task_up_records_bg.png", Vector2.zero, 0);
        for (int i = 0; i < 3; i++) _drawer[i] = UpperArt.Add(root, $"task_up_records_drawer_{i}.png", Drawers[i], 3);
        // fuenf Karten: je Jahrzehnt eine, dazu zwei weitere (alle verschieden)
        var pick = new List<(int D, int I)>();
        for (int d = 0; d < 3; d++) pick.Add((d, rnd.Next(3)));
        var rest = new List<(int, int)>();
        for (int d = 0; d < 3; d++) for (int i = 0; i < 3; i++) if (!pick.Contains((d, i))) rest.Add((d, i));
        for (int k = 0; k < 2; k++) { int j = rnd.Next(rest.Count); pick.Add(rest[j]); rest.RemoveAt(j); }
        var spots = Scatter(rnd, pick.Count, -2.75f, 0.45f, -1.65f, 1.45f, 1.05f);
        for (int k = 0; k < pick.Count; k++)
        {
            var (d, i) = pick[k];
            var sr = UpperArt.Add(root, $"task_up_records_card_{d}_{i}.png", spots[k], 10 + k);
            sr.transform.localEulerAngles = new Vector3(0, 0, (float)(rnd.NextDouble() * 16 - 8));
            Pieces.Add(new UpperPiece(sr, spots[k], 10 + k) { Tag = d, Grab = 0.6f });
        }
        _total = Pieces.Count;
    }

    internal static List<Vector2> Scatter(System.Random rnd, int n, float x0, float x1, float y0, float y1, float minDist)
    {
        var res = new List<Vector2>();
        for (int guard = 0; res.Count < n && guard < 4000; guard++)
        {
            var p = new Vector2(x0 + (float)rnd.NextDouble() * (x1 - x0), y0 + (float)rnd.NextDouble() * (y1 - y0));
            bool ok = true;
            foreach (var q in res) if (Vector2.Distance(p, q) < minDist) { ok = false; break; }
            if (ok || guard > 3000) res.Add(p);
        }
        return res;
    }

    private int DrawerAt(Vector2 p)
    {
        for (int i = 0; i < 3; i++) if (Mathf.Abs(p.x - Drawers[i].x) < 0.95f && Mathf.Abs(p.y - Drawers[i].y) < 0.6f) return i;
        return -1;
    }

    protected override void Drop(UpperPiece p)
    {
        int d = DrawerAt(p.Pos);
        if (d < 0) return;                                          // liegen lassen, wo man sie hinlegt
        if (d == p.Tag)
        {
            p.Gone = true;
            _drawerOut[d] = 1f;
            UpperArt.Order(p.Sr, 2);                                 // hinter die Schubladenfront
            p.Fly(Drawers[d] + new Vector2(-0.1f, 0.05f), 0.25f, () =>
            {
                p.Sr.enabled = false;
                _filed++;
                UpperArt.Sfx("clack", 0.5f);
                if (_filed >= _total) _doneT = 0f;
            });
        }
        else
        {
            _shake[d] = 0.4f;
            UpperArt.Sfx("thud", 0.45f);
            p.Fly(p.Home, 0.3f);
        }
    }

    protected override void OnTick(float dt, Vector2 mouse, bool down, bool pressed)
    {
        int hover = Held != null ? DrawerAt(Held.Pos) : -1;
        for (int i = 0; i < 3; i++)
        {
            float want = hover == i ? 0.6f : 0f;
            _drawerOut[i] = Mathf.MoveTowards(_drawerOut[i], want, dt * 3f);
            _shake[i] = Mathf.Max(0f, _shake[i] - dt);
            float sx = _shake[i] > 0f ? Mathf.Sin(Time.time * 60f) * 0.05f : 0f;
            UpperArt.Place(_drawer[i], Drawers[i] + new Vector2(-_drawerOut[i] * 0.3f + sx, 0f));
        }
        if (_doneT >= 0f) { _doneT += dt; if (_doneT > 0.35f) Done = true; }
    }

    public override void Simulate(float dt, out Vector2 mouse, out bool down)
        => SimDrag(dt, () =>
        {
            foreach (var p in Pieces) if (!p.Gone && !p.Busy) return (p, Drawers[p.Tag]);
            return null;
        }, out mouse, out down);
}

// ============================================================ Develop the Set Photos (Darkroom)

internal sealed class PhotosGame : UpperDragGame
{
    public override string Name => "photos";
    private static readonly Vector2[] Trays = { new(-2.15f, -1.2f), new(0.0f, -1.2f), new(2.15f, -1.2f) };
    private static readonly Vector2 Stack = new(-2.6f, 0.8f);
    private static readonly Vector2[] Slots = { new(-0.9f, 1.95f), new(1.5f, 1.95f) };     // auf der Leine
    private const int Photos = 2;
    private const float Soak = 1.3f;
    private UpperPiece _photo;
    private SpriteRenderer _img, _barBg, _bar, _hint;
    private int _hung, _need, _tray = -1;
    private float _hintT;
    private float _soak, _doneT = -1f;
    private readonly List<(SpriteRenderer Sr, float T)> _swing = new();
    public override float Progress => (_hung * 4 + _need) / (float)(Photos * 4);

    public override void Build(Transform root, System.Random rnd)
    {
        Root = root; Rnd = rnd;
        UpperArt.Add(root, "task_up_photos_bg.png", Vector2.zero, 0);
        _barBg = UpperArt.Add(root, "task_up_bar_bg.png", Vector2.zero, 20);
        _bar = UpperArt.Add(root, "task_up_bar_fill.png", Vector2.zero, 21, new Vector2(0f, 0.5f));
        ShowBar(false);
        NewPhoto();
    }

    private void NewPhoto()
    {
        var sr = UpperArt.Add(Root, "task_up_photos_paper.png", Stack, 12);
        _photo = new UpperPiece(sr, Stack, 12) { Grab = 0.65f };
        Pieces.Add(_photo);
        _img = UpperArt.Add(sr.transform, $"task_up_photos_img_{_hung % 2}.png", Vector2.zero, 13);
        _img.transform.localPosition = new Vector3(0f, 0f, -0.005f);
        _img.color = new Color(1f, 1f, 1f, 0f);
        _need = 0; _tray = -1; _soak = 0f;
    }

    private void ShowBar(bool on, Vector2 at = default)
    {
        _barBg.enabled = _bar.enabled = on;
        if (!on) return;
        UpperArt.Place(_barBg, at);
        UpperArt.Place(_bar, at + new Vector2(-0.58f, 0f));
    }

    protected override bool CanGrab(UpperPiece p) => base.CanGrab(p) && p == _photo && !(_tray >= 0 && _soak < 1f);

    protected override void Drop(UpperPiece p)
    {
        if (_need < 3)
        {
            for (int i = 0; i < 3; i++)
            {
                if (Mathf.Abs(p.Pos.x - Trays[i].x) > 0.95f || Mathf.Abs(p.Pos.y - Trays[i].y) > 0.65f) continue;
                if (i == _need)
                {
                    p.Fly(Trays[i] + new Vector2(0f, 0.05f), 0.15f);
                    p.Home = Trays[i] + new Vector2(0f, 0.05f);
                    _tray = i; _soak = 0f;
                    ShowBar(true, Trays[i] + new Vector2(0f, -0.78f));
                    UpperArt.Sfx("splash", 0.35f);
                }
                else { UpperArt.Sfx("thud", 0.45f); p.Fly(p.Home, 0.3f); }
                return;
            }
            p.Fly(p.Home, 0.3f);
            return;
        }
        var slot = Slots[_hung];
        // fertig fixiert: irgendwo in die obere Haelfte (Leine) ziehen reicht. Vorher nur 0,85 um den Leinenplatz,
        // den sah man unter der Titelleiste kaum, das Spiel wirkte nach "3. Fix" ohne Ende (User 20.11.)
        if (Vector2.Distance(p.Pos, slot + new Vector2(0f, -0.55f)) < 0.85f || p.Pos.y > 0.35f)
        {
            p.Gone = true;
            p.Fly(slot + new Vector2(0f, -0.55f), 0.15f, () =>
            {
                UpperArt.Add(Root, "task_up_photos_peg.png", slot + new Vector2(0f, 0.02f), 15);
                _swing.Add((p.Sr, 0f));
                _hung++;
                UpperArt.Sfx("click", 0.5f);
                if (_hung >= Photos) _doneT = 0f; else NewPhoto();
            });
        }
        else p.Fly(p.Home, 0.3f);
    }

    protected override void OnTick(float dt, Vector2 mouse, bool down, bool pressed)
    {
        if (_tray >= 0 && _soak < 1f && Held == null && !_photo.Busy)
        {
            _soak = Mathf.Min(1f, _soak + dt / Soak);
            _bar.transform.localScale = new Vector3(_soak, 1f, 1f);
            if (_tray == 0) _img.color = new Color(1f, 1f, 1f, Mathf.SmoothStep(0f, 1f, _soak));
            if (_tray == 1) _img.color = new Color(1f, 1f - 0.15f * Mathf.Sin(_soak * Mathf.PI), 1f, 1f);
            if (_soak >= 1f) { _need = _tray + 1; UpperArt.Sfx("ding", 0.35f); _bar.color = new Color(0.55f, 1f, 0.6f); }
        }
        if (Held == _photo && _tray >= 0) { _tray = -1; ShowBar(false); _bar.color = Color.white; }
        if (_img != null && _photo != null) _img.sortingOrder = _photo.Sr.sortingOrder + 1;      // Bild bleibt beim Ziehen auf dem Papier
        for (int i = 0; i < _swing.Count; i++)
        {
            var (sr, t) = _swing[i];
            t += dt;
            sr.transform.localEulerAngles = new Vector3(0, 0, Mathf.Sin(t * 5f) * 8f * Mathf.Exp(-t * 1.6f));
            _swing[i] = (sr, t);
        }
        // nach dem Fixieren: blinkende Klammer an der Leine zeigt, wohin das Foto gehoert
        bool wantHint = _need >= 3 && _hung < Photos && _photo != null && !_photo.Gone;
        if (wantHint && _hint == null) _hint = UpperArt.Add(Root, "task_up_photos_peg.png", Slots[_hung] + new Vector2(0f, 0.02f), 14);
        if (_hint != null)
        {
            _hint.enabled = wantHint;
            if (wantHint)
            {
                UpperArt.Place(_hint, Slots[_hung] + new Vector2(0f, 0.02f));
                _hintT += dt;
                _hint.color = new Color(1f, 1f, 1f, 0.35f + 0.35f * Mathf.Sin(_hintT * 6f));
            }
        }
        if (_doneT >= 0f) { _doneT += dt; if (_doneT > 0.5f) Done = true; }
    }

    public override void Simulate(float dt, out Vector2 mouse, out bool down)
        => SimDrag(dt, () =>
        {
            if (_photo == null || _photo.Gone || _photo.Busy || (_tray >= 0 && _soak < 1f)) return null;
            return (_photo, _need < 3 ? Trays[_need] : Slots[_hung] + new Vector2(0f, -0.55f));
        }, out mouse, out down);
}

// ============================================================ Dress the Mannequin (Sewing Room)

internal sealed class DressGame : UpperDragGame
{
    public override string Name => "dress";
    private static readonly string[] Slot = { "gown", "sash", "veil" };
    private static readonly Vector2[] Worn = { new(0.3f, -0.55f), new(0.3f, -0.33f), new(0.3f, 0.65f) };   // Kleid, Taille, Knauf
    private static readonly int[] WornOrder = { 5, 6, 7 };
    private static readonly float[] RackY = { -1.45f, -0.15f, 1.15f };
    private static readonly float[] RackScale = { 0.42f, 0.55f, 0.5f };
    private static readonly Vector2[] Card = { new(2.65f, -0.55f), new(2.65f, 0.45f), new(2.65f, 1.25f) };
    private static readonly float[] CardScale = { 0.3f, 0.45f, 0.3f };
    private readonly int[] _target = new int[3];
    private readonly bool[] _placed = new bool[3];
    private int _count;
    private float _doneT = -1f;
    private readonly List<(Transform T, float From, float To, float K)> _grow = new();
    public override float Progress => _count / 3f;

    public override void Build(Transform root, System.Random rnd)
    {
        Root = root; Rnd = rnd;
        UpperArt.Add(root, "task_up_dress_bg.png", Vector2.zero, 0);
        for (int s = 0; s < 3; s++)
        {
            _target[s] = rnd.Next(2);
            UpperArt.Add(root, $"task_up_dress_{Slot[s]}_{_target[s]}.png", Card[s], 3, scale: CardScale[s]);
            int swap = rnd.Next(2);
            for (int c = 0; c < 2; c++)
            {
                float x = (c ^ swap) == 0 ? -2.75f : -1.8f;
                var at = new Vector2(x, RackY[s]);
                var sr = UpperArt.Add(root, $"task_up_dress_{Slot[s]}_{c}.png", at, 10 + s * 2 + c, scale: RackScale[s]);
                Pieces.Add(new UpperPiece(sr, at, 10 + s * 2 + c) { Tag = s, Tag2 = c, Grab = 0.5f });
            }
        }
    }

    protected override void Drop(UpperPiece p)
    {
        bool onForm = Mathf.Abs(p.Pos.x - 0.3f) < 1.15f && p.Pos.y > -2.3f && p.Pos.y < 2.2f;
        if (!onForm) { p.Fly(p.Home, 0.3f); return; }
        int s = p.Tag;
        if (!_placed[s] && p.Tag2 == _target[s])
        {
            _placed[s] = true;
            p.Gone = true;
            p.BaseOrder = WornOrder[s];
            UpperArt.Order(p.Sr, WornOrder[s]);
            p.Fly(Worn[s], 0.2f, () => { _count++; if (_count >= 3) _doneT = 0f; });
            _grow.Add((p.Sr.transform, RackScale[s], 1f, 0f));
            UpperArt.Sfx("pop", 0.5f);
        }
        else { UpperArt.Sfx("thud", 0.45f); p.Fly(p.Home, 0.3f); }
    }

    protected override void OnTick(float dt, Vector2 mouse, bool down, bool pressed)
    {
        for (int i = 0; i < _grow.Count; i++)
        {
            var (t, a, b, k) = _grow[i];
            k = Mathf.Min(1f, k + dt / 0.25f);
            t.localScale = Vector3.one * Mathf.Lerp(a, b, Mathf.SmoothStep(0f, 1f, k));
            _grow[i] = (t, a, b, k);
        }
        // gezogenes Teil in voller Groesse ueber der Puppe, sonst Regal-Groesse
        foreach (var p in Pieces)
        {
            if (p.Gone) continue;
            float want = p == Held && Mathf.Abs(p.Pos.x - 0.3f) < 1.3f ? 1f : RackScale[p.Tag];
            float cur = p.Sr.transform.localScale.x;
            p.Sr.transform.localScale = Vector3.one * Mathf.MoveTowards(cur, want, dt * 4f);
        }
        if (_doneT >= 0f) { _doneT += dt; if (_doneT > 0.6f) Done = true; }
    }

    public override void Simulate(float dt, out Vector2 mouse, out bool down)
        => SimDrag(dt, () =>
        {
            for (int s = 0; s < 3; s++)
            {
                if (_placed[s]) continue;
                foreach (var p in Pieces) if (!p.Gone && !p.Busy && p.Tag == s && p.Tag2 == _target[s]) return (p, Worn[s]);
                return null;
            }
            return null;
        }, out mouse, out down);
}

// ============================================================ Rewind the Ghost Tapes (Master Bedroom)

internal sealed class TapesGame : IUpperGame
{
    public string Name => "tapes";
    private static readonly Vector2 Crank = new(2.45f, -0.35f);
    private static readonly Vector2 Screen = new(-0.9f, 0.85f);
    private static readonly Vector2 Button = new(0.75f, -1.35f);
    private static readonly Vector2[] Reels = { new(-2.05f, -1.35f), new(-0.85f, -1.35f) };
    private static readonly Vector2[] Lamps = { new(1.95f, 1.95f), new(2.45f, 1.95f), new(2.95f, 1.95f) };
    private const float NeedDeg = 1440f;
    private const int Hits = 3;
    private SpriteRenderer _crank, _static, _room, _ghost, _btn, _flash, _barBg, _bar;
    private readonly SpriteRenderer[] _reel = new SpriteRenderer[2];
    private readonly SpriteRenderer[] _lamp = new SpriteRenderer[3];
    private float _deg, _lastAng, _clock, _nextGhost, _ghostUntil, _flashT, _btnT, _doneT = -1f;
    private bool _grabbing, _phase2, _marked;
    private int _hits;
    private System.Random _rnd;
    public float Progress => _phase2 ? 0.5f + 0.5f * _hits / Hits : 0.5f * Mathf.Clamp01(_deg / NeedDeg);
    public bool Done { get; private set; }

    public void Build(Transform root, System.Random rnd)
    {
        _rnd = rnd;
        UpperArt.Add(root, "task_up_tapes_bg.png", Vector2.zero, 0);
        _room = UpperArt.Add(root, "task_up_tapes_room.png", Screen, 2);
        _ghost = UpperArt.Add(root, "task_up_tapes_ghost_0.png", Screen, 3);
        _ghost.enabled = false;
        _static = UpperArt.Add(root, "task_up_tapes_static.png", Screen, 4);
        _flash = UpperArt.Add(root, "task_up_tapes_flash.png", Screen, 5);
        _flash.color = new Color(1, 1, 1, 0);
        UpperArt.Add(root, "task_up_tapes_glass.png", Screen, 6);
        for (int i = 0; i < 2; i++) _reel[i] = UpperArt.Add(root, "task_up_tapes_reel.png", Reels[i], 3);
        _btn = UpperArt.Add(root, "task_up_tapes_btn.png", Button, 3);
        for (int i = 0; i < 3; i++) _lamp[i] = UpperArt.Add(root, "task_up_tapes_lamp_off.png", Lamps[i], 3);
        _crank = UpperArt.Add(root, "task_up_tapes_crank.png", Crank, 5);
        _barBg = UpperArt.Add(root, "task_up_bar_bg.png", Screen + new Vector2(0f, -1.3f), 7);
        _bar = UpperArt.Add(root, "task_up_bar_fill.png", Screen + new Vector2(-0.58f, -1.3f), 8, new Vector2(0f, 0.5f));
        _bar.transform.localScale = new Vector3(0f, 1f, 1f);
    }

    public void Tick(float dt, Vector2 mouse, bool down, bool pressed)
    {
        _clock += dt;
        if (!_phase2)
        {
            var d = mouse - Crank;
            float ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
            if (pressed && d.magnitude > 0.3f && d.magnitude < 1.3f) { _grabbing = true; _lastAng = ang; }
            if (!down) _grabbing = false;
            if (_grabbing && !Done)
            {
                float delta = Mathf.DeltaAngle(_lastAng, ang);
                _lastAng = ang;
                if (delta > 0f && delta < 60f)                       // zurueckspulen = gegen den Uhrzeigersinn
                {
                    _deg += delta;
                    _crank.transform.localEulerAngles = new Vector3(0, 0, _deg);
                    _reel[0].transform.localEulerAngles = new Vector3(0, 0, _deg * 2.2f);
                    _reel[1].transform.localEulerAngles = new Vector3(0, 0, _deg * 1.6f);
                    float k = Mathf.Clamp01(_deg / NeedDeg);
                    _reel[0].transform.localScale = Vector3.one * Mathf.Lerp(0.7f, 1.25f, k);
                    _reel[1].transform.localScale = Vector3.one * Mathf.Lerp(1.25f, 0.7f, k);
                    _bar.transform.localScale = new Vector3(k, 1f, 1f);
                }
            }
            // Bildrauschen rollt beim Spulen
            _static.transform.localPosition = new Vector3(Screen.x + Mathf.Sin(_clock * 37f) * 0.03f, Screen.y + Mathf.Sin(_clock * 23f) * 0.03f, _static.transform.localPosition.z);
            _static.color = new Color(1, 1, 1, _grabbing ? 1f : 0.85f);
            if (_deg >= NeedDeg)
            {
                _phase2 = true;
                _grabbing = false;
                _static.enabled = false;
                _barBg.enabled = _bar.enabled = false;
                _nextGhost = _clock + 0.9f;
                UpperArt.Sfx("ding", 0.4f);
            }
            return;
        }
        // Abspielen: Geist erscheint in Abstaenden, MARK druecken, solange er zu sehen ist
        if (!Done && _clock >= _nextGhost && !_ghost.enabled)
        {
            _ghost.sprite = UpperArt.Get($"task_up_tapes_ghost_{_rnd.Next(3)}.png");
            _ghost.enabled = true;
            _marked = false;
            _ghostUntil = _clock + 1.15f;
            UpperArt.Sfx("whoosh", 0.25f);
        }
        if (_ghost.enabled && _clock >= _ghostUntil)
        {
            _ghost.enabled = false;
            _nextGhost = _clock + 1.0f + (float)_rnd.NextDouble() * 1.2f;
        }
        _room.color = new Color(1, 1, 1, 0.92f + 0.08f * Mathf.Sin(_clock * 31f));
        if (pressed && !Done && Mathf.Abs(mouse.x - Button.x) < 0.5f && Mathf.Abs(mouse.y - Button.y) < 0.38f)
        {
            _btnT = 0.15f;
            if (_ghost.enabled && !_marked)
            {
                _marked = true;
                _lamp[_hits].sprite = UpperArt.Get("task_up_tapes_lamp_on.png");
                _hits++;
                _flashT = 0.35f;
                _flash.color = new Color(1f, 1f, 1f, 0.7f);
                UpperArt.Sfx("chime", 0.45f);
                if (_hits >= Hits) _doneT = 0f;
            }
            else
            {
                _flashT = 0.3f;
                _flash.color = new Color(1f, 0.2f, 0.2f, 0.5f);
                UpperArt.Sfx("thud", 0.4f);
            }
        }
        _btnT = Mathf.Max(0f, _btnT - dt);
        _btn.sprite = UpperArt.Get(_btnT > 0f ? "task_up_tapes_btn_down.png" : "task_up_tapes_btn.png");
        if (_flashT > 0f)
        {
            _flashT -= dt;
            var c = _flash.color; c.a = Mathf.Max(0f, _flashT / 0.35f) * 0.7f; _flash.color = c;
        }
        if (_doneT >= 0f) { _doneT += dt; if (_doneT > 0.6f) Done = true; }
    }

    private float _st;
    private float _simPress;

    public void Simulate(float dt, out Vector2 mouse, out bool down)
    {
        _st += dt;
        if (!_phase2)
        {
            // gegen den Uhrzeigersinn kurbeln, 1,3 Umdrehungen je Sekunde
            float a = _st * 1.3f * Mathf.PI * 2f;
            mouse = Crank + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * 0.72f;
            down = _st > 0.1f;
            return;
        }
        mouse = Button;
        _simPress = Mathf.Max(0f, _simPress - dt);
        if (_ghost.enabled && !_marked && _clock - (_ghostUntil - 1.15f) > 0.25f && _simPress <= 0f) _simPress = 0.12f;
        down = _simPress > 0.04f;
    }

    public void Dispose() { }
}

// ============================================================ Put Away the Toys (Nursery)

internal sealed class ToysGame : UpperDragGame
{
    public override string Name => "toys";
    private static readonly string[] Toys = { "blocks", "ball", "train", "doll", "jack" };
    private static readonly Vector2 Chest = new(2.25f, -1.15f);
    private SpriteRenderer _lid, _lidClosed;
    private int _in;
    private bool _popped, _closing;
    private float _popT = -1f, _closeT;
    private UpperPiece _doll;
    private (Vector2 From, Vector2 To, float T) _jump;
    public override float Progress => Mathf.Min(_in, 5) / 5f * (_popped ? 1f : 0.9f);

    public override void Build(Transform root, System.Random rnd)
    {
        Root = root; Rnd = rnd;
        UpperArt.Add(root, "task_up_toys_bg.png", Vector2.zero, 0);
        _lid = UpperArt.Add(root, "task_up_toys_lid.png", Chest + new Vector2(0f, 0.95f), 2);
        UpperArt.Add(root, "task_up_toys_chestfront.png", Chest + new Vector2(0f, -0.35f), 30);
        _lidClosed = UpperArt.Add(root, "task_up_toys_lid_closed.png", Chest + new Vector2(0f, 0.1f), 31);
        _lidClosed.enabled = false;
        var spots = RecordsGame.Scatter(rnd, Toys.Length, -2.8f, 0.6f, -1.7f, 1.5f, 1.05f);
        for (int i = 0; i < Toys.Length; i++)
        {
            var sr = UpperArt.Add(root, $"task_up_toy_{Toys[i]}.png", spots[i], 10 + i);
            var p = new UpperPiece(sr, spots[i], 10 + i) { Tag = i, Grab = 0.6f };
            Pieces.Add(p);
            if (Toys[i] == "doll") _doll = p;
        }
    }

    private static bool InChest(Vector2 p) => Mathf.Abs(p.x - Chest.x) < 1.2f && Mathf.Abs(p.y - Chest.y) < 0.75f;

    protected override bool CanGrab(UpperPiece p) => base.CanGrab(p) && !_closing && !(p == _doll && _popT >= 0f);

    protected override void Drop(UpperPiece p)
    {
        if (!InChest(p.Pos)) { return; }
        p.Gone = true;
        UpperArt.Order(p.Sr, 20 + _in);
        var spot = Chest + new Vector2((float)(Rnd.NextDouble() * 1.4 - 0.7), (float)(Rnd.NextDouble() * 0.3));
        p.Fly(spot, 0.18f, () =>
        {
            _in++;
            UpperArt.Sfx("thud", 0.4f);
            // die Puppe klettert einmal wieder heraus, sobald vier Sachen in der Kiste sind
            if (!_popped && _doll.Gone && _in >= 4) _popT = 0f;
            else if (_in >= 5 && _popped) Close();
        });
    }

    private void Close()
    {
        _closing = true;
        _closeT = 0f;
    }

    protected override void OnTick(float dt, Vector2 mouse, bool down, bool pressed)
    {
        if (_popT >= 0f)
        {
            _popT += dt;
            if (_popT > 0.55f && _jump.T == 0f)
            {
                // kichernd wieder heraus: Bogen auf einen freien Platz am Boden
                _popped = true;
                _in--;
                var to = new Vector2(-1.6f + (float)Rnd.NextDouble() * 1.8f, -1.2f + (float)Rnd.NextDouble() * 2.2f);
                _jump = (_doll.Pos, to, 0.0001f);
                UpperArt.Order(_doll.Sr, 35);
                UpperArt.Sfx("creak", 0.6f);
            }
            if (_jump.T > 0f)
            {
                _jump.T = Mathf.Min(1f, _jump.T + dt / 0.7f);
                var p = Vector2.Lerp(_jump.From, _jump.To, _jump.T) + new Vector2(0f, Mathf.Sin(_jump.T * Mathf.PI) * 1.4f);
                _doll.Set(p);
                _doll.Sr.transform.localEulerAngles = new Vector3(0, 0, _jump.T * 360f);
                if (_jump.T >= 1f)
                {
                    _doll.Sr.transform.localEulerAngles = Vector3.zero;
                    _doll.Home = _jump.To;
                    UpperArt.Order(_doll.Sr, _doll.BaseOrder);
                    _doll.Gone = false;
                    _popT = -1f;
                    _jump = default;
                }
            }
        }
        // die Puppe wackelt bedrohlich, bevor sie springt
        if (_popT >= 0f && _popT < 0.55f) _doll.Sr.transform.localEulerAngles = new Vector3(0, 0, Mathf.Sin(_popT * 50f) * 12f);
        if (_closing)
        {
            _closeT += dt;
            _lid.transform.localScale = new Vector3(1f, Mathf.Max(0f, 1f - _closeT / 0.25f), 1f);
            if (_closeT > 0.25f && !_lidClosed.enabled) { _lidClosed.enabled = true; _lid.enabled = false; UpperArt.Sfx("slam", 0.45f); }
            if (_closeT > 0.75f) Done = true;
        }
    }

    public override void Simulate(float dt, out Vector2 mouse, out bool down)
        => SimDrag(dt, () =>
        {
            foreach (var p in Pieces) if (!p.Gone && !p.Busy && CanGrab(p)) return (p, Chest);
            return null;
        }, out mouse, out down);
}

// ============================================================ Drain the Bloody Bath (Bathroom)

internal sealed class BathGame : IUpperGame
{
    public string Name => "bath";
    private static readonly Vector2 Anchor = new(2.55f, 0.55f);       // Kette haengt ueber den Wannenrand
    private static readonly Vector2 RingRest = new(2.55f, -0.45f);
    private const float PullY = -1.75f;                                // Ring so weit nach unten ziehen, dann kommt der Stoepsel
    private const float PullMin = -2.05f;
    private static readonly Vector2 Drain = new(1.25f, -0.75f);
    private static readonly Vector2[] StainSpots =
        { new(-2.0f, -0.45f), new(-1.0f, -0.95f), new(0.0f, -0.35f), new(0.85f, -0.9f), new(-1.55f, 0.1f), new(0.6f, 0.05f) };
    private SpriteRenderer _water, _swirl, _ring, _chain, _plug, _sponge;
    private readonly List<(SpriteRenderer Sr, float Dirt, SpriteRenderer Spark, float SparkT)> _stains = new();
    private Vector2 _ringPos = RingRest, _last;
    private bool _grab, _pulled, _drained, _hasLast;
    private float _drain, _doneT = -1f;
    public float Progress
    {
        get
        {
            float clean = 0f;
            foreach (var s in _stains) clean += 1f - s.Dirt;
            return (_pulled ? 0.15f : 0f) + 0.25f * _drain + (_stains.Count > 0 ? 0.6f * clean / _stains.Count : 0f);
        }
    }
    public bool Done { get; private set; }

    public void Build(Transform root, System.Random rnd)
    {
        UpperArt.Add(root, "task_up_bath_bg.png", Vector2.zero, 0);
        var spots = new List<Vector2>(StainSpots);
        for (int k = 0; k < 4; k++)
        {
            int j = rnd.Next(spots.Count);
            var sr = UpperArt.Add(root, $"task_up_bath_stain_{k % 3}.png", spots[j], 2);
            sr.transform.localEulerAngles = new Vector3(0, 0, (float)(rnd.NextDouble() * 40 - 20));
            var spark = UpperArt.Add(root, "task_up_sparkle.png", spots[j], 9);
            spark.enabled = false;
            _stains.Add((sr, 1f, spark, 0f));
            spots.RemoveAt(j);
        }
        _water = UpperArt.Add(root, "task_up_bath_water.png", new Vector2(-0.3f, -0.4f), 4);
        _swirl = UpperArt.Add(root, "task_up_bath_swirl.png", Drain, 5);
        _swirl.color = new Color(1, 1, 1, 0);
        _plug = UpperArt.Add(root, "task_up_bath_plug.png", Drain, 6);
        _plug.enabled = false;
        UpperArt.Add(root, "task_up_bath_rim.png", Vector2.zero, 7);
        _chain = UpperArt.Add(root, "task_up_bath_chain.png", Anchor, 8, new Vector2(0.5f, 1f));
        _ring = UpperArt.Add(root, "task_up_bath_ring.png", RingRest, 9);
        _sponge = UpperArt.Add(root, "task_up_bath_sponge.png", new Vector2(2.6f, -1.9f), 25);
        _sponge.enabled = false;
        Apply();
    }

    private void Apply()
    {
        UpperArt.Place(_ring, _ringPos);
        float len = Mathf.Max(0.1f, Anchor.y - _ringPos.y);
        _chain.transform.localScale = new Vector3(1f, len / 1.3f, 1f);            // Kettenbild ist 1,3 Einheiten lang
        UpperArt.Place(_chain, new Vector2(_ringPos.x, Anchor.y));
    }

    public void Tick(float dt, Vector2 mouse, bool down, bool pressed)
    {
        if (!_pulled)
        {
            if (pressed && Vector2.Distance(mouse, _ringPos) < 0.5f) _grab = true;
            if (!down) _grab = false;
            if (_grab) _ringPos = new Vector2(RingRest.x, Mathf.Clamp(mouse.y, PullMin, RingRest.y));
            else _ringPos = Vector2.MoveTowards(_ringPos, RingRest, dt * 4f);
            if (_ringPos.y <= PullY)
            {
                _pulled = true; _grab = false;
                _plug.enabled = true;
                UpperArt.Place(_plug, new Vector2(2.3f, 0.42f));
                UpperArt.Sfx("pop", 0.6f);
                UpperArt.Sfx("rush", 0.4f);
            }
            Apply();
            return;
        }
        if (!_drained)
        {
            _drain = Mathf.Min(1f, _drain + dt / 2.4f);
            float k = 1f - _drain;
            _water.transform.localScale = new Vector3(Mathf.Lerp(0.15f, 1f, k), Mathf.Lerp(0.1f, 1f, k), 1f);
            _water.transform.localPosition = new Vector3(Mathf.Lerp(Drain.x, -0.3f, k), Mathf.Lerp(Drain.y, -0.4f, k), _water.transform.localPosition.z);
            _water.color = new Color(1, 1, 1, Mathf.Clamp01(k * 1.4f));
            _swirl.color = new Color(1, 1, 1, Mathf.Sin(_drain * Mathf.PI) * 0.9f);
            _swirl.transform.localEulerAngles = new Vector3(0, 0, -_drain * 900f);
            _ringPos = Vector2.MoveTowards(_ringPos, RingRest, dt * 2f);
            Apply();
            if (_drain >= 1f) { _drained = true; _water.enabled = false; _swirl.enabled = false; _sponge.enabled = true; }
            return;
        }
        // schrubben: nur Bewegung bei gedrueckter Taste ueber einem Fleck zaehlt
        UpperArt.Place(_sponge, mouse + new Vector2(0.05f, -0.05f));
        _sponge.transform.localEulerAngles = new Vector3(0, 0, down ? Mathf.Sin(Time.time * 25f) * 10f : 0f);
        float moved = _hasLast && down ? Vector2.Distance(mouse, _last) : 0f;
        _last = mouse; _hasLast = true;
        bool allClean = true;
        for (int i = 0; i < _stains.Count; i++)
        {
            var s = _stains[i];
            if (s.Dirt > 0f && down && Vector2.Distance(mouse, s.Sr.transform.localPosition) < 0.65f)
            {
                s.Dirt = Mathf.Max(0f, s.Dirt - moved * 0.6f);
                s.Sr.color = new Color(1, 1, 1, s.Dirt);
                if (s.Dirt <= 0.02f) { s.Dirt = 0f; s.Sr.enabled = false; s.Spark.enabled = true; s.SparkT = 0.01f; UpperArt.Sfx("chime", 0.35f); }
            }
            if (s.SparkT > 0f)
            {
                s.SparkT += dt;
                s.Spark.transform.localScale = Vector3.one * (0.6f + s.SparkT * 1.2f);
                s.Spark.color = new Color(1, 1, 1, Mathf.Max(0f, 1f - s.SparkT / 0.7f));
                if (s.SparkT > 0.7f) { s.Spark.enabled = false; s.SparkT = 0f; }
            }
            if (s.Dirt > 0f) allClean = false;
            _stains[i] = s;
        }
        if (allClean && _doneT < 0f) _doneT = 0f;
        if (_doneT >= 0f) { _doneT += dt; if (_doneT > 0.6f) Done = true; }
    }

    private float _st;

    public void Simulate(float dt, out Vector2 mouse, out bool down)
    {
        _st += dt;
        if (!_pulled)
        {
            // Ring fassen und hochziehen
            if (_st < 0.3f) { mouse = _ringPos; down = false; return; }
            mouse = new Vector2(RingRest.x, Mathf.Lerp(RingRest.y, PullMin + 0.1f, Mathf.Clamp01((_st - 0.3f) / 0.6f)));
            down = true;
            return;
        }
        if (!_drained) { mouse = new Vector2(2.6f, -1.9f); down = false; return; }
        foreach (var s in _stains)
        {
            if (s.Dirt <= 0f) continue;
            Vector2 c = s.Sr.transform.localPosition;
            mouse = c + new Vector2(Mathf.Sin(_st * 14f) * 0.4f, Mathf.Sin(_st * 9f) * 0.2f);
            down = true;
            return;
        }
        mouse = Vector2.zero; down = false;
    }

    public void Dispose() { }
}
