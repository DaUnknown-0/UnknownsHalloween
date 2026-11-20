// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereUpperTasks - eigene Minispiele fuer die sechs Aufgaben im Obergeschoss von Hollowmere Manor (18.11., User: "eigene
// Aufgaben statt umbenannter Airship-Minispiele").
//
// Die Aufgaben selbst bleiben Atlas-Reiter aus Airship (HollowmereMap.BorrowedUpper): Atlas kopiert den NormalPlayerTask, setzt die
// Konsole und nummeriert wie der Host (Verteilung, RpcSetTasks, RpcCompleteTask und der Taskwin bleiben vanilla). Nur das Minispiel
// wird getauscht, genau wie Atlas es fuer seine eigenen Bausteine tut (AtlasTasks): PlayerTask.MinigamePrefab an den Aufgaben des
// LOKALEN Spielers, viermal pro Sekunde abgeglichen, nie an den Prefabs der Schiffslisten (Assets). Die Prefabs haengen unter einem
// inaktiven Halter am ShipStatus und sterben mit der Runde.
//
// HwUpperMinigame ist wie AtlasMinigame eine eingeschleuste Minigame-Unterklasse, die nichts ueberschreibt: Console.Use
// instanziiert sie, das vanilla Begin setzt MyTask/MyNormTask und spielt die Oeffnung. Welches Spiel drinsteckt, steht im
// GameObject-Namen ("HwUpper_records"), weil verwaltete Felder beim Instantiate nicht mitkopiert werden.
//
// Eingabe wie in den vanilla Minispielen ueber die Spielklasse Controller (Maus, Touch und Controller-Zeiger), Rueckfall auf die
// Maus. Abschluss: alle Schritte der Aufgabe (die geliehenen Airship-Aufgaben haben teils zwei Schritte oder einen Zeitgeber, hier ist
// jede Aufgabe ein Besuch), NormalPlayerTask.NextStep meldet RpcCompleteTask wie vanilla.
//
// Autotest: UC_HALLOWEEN_DIAG mit "uptasks" (alle sechs: Aufgabe zuweisen, zur Konsole, Console.Use, das Spiel spielt sich selbst,
// Fotos, Pruefung "complete"). Grafik: tools/gen_villa_uptasks.py -> Resources/villa/task_up_*.png (Paket villa_map).

using System;
using System.Collections.Generic;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using UnknownsAtlas;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

internal static class HollowmereUpperTasks
{
    internal const string LogPrefix = "[Halloween/UpperTasks]";

    /// <summary>Aufgabe -> Spiel. Reihenfolge = Reihenfolge des Autotests.</summary>
    internal static readonly (TaskTypes Type, string Kind)[] Kinds =
    {
        (TaskTypes.SortRecords, "records"),        // Attic
        (TaskTypes.DevelopPhotos, "photos"),       // Darkroom
        (TaskTypes.DressMannequin, "dress"),       // Sewing Room
        (TaskTypes.RewindTapes, "tapes"),          // Master Bedroom
        (TaskTypes.PutAwayRifles, "toys"),         // Nursery
        (TaskTypes.StartFans, "bath"),             // Bathroom
    };

    private static bool _registered;
    private static GameObject _holder;
    private static readonly Dictionary<TaskTypes, Minigame> Prefabs = new();
    private static float _nextSwap;

    internal static void Init()
    {
        if (_registered) return;
        try { ClassInjector.RegisterTypeInIl2Cpp<HwUpperMinigame>(); _registered = true; }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} register failed: {e}"); }
    }

    internal static IUpperGame Create(string kind) => kind switch
    {
        "records" => new RecordsGame(),
        "photos" => new PhotosGame(),
        "dress" => new DressGame(),
        "tapes" => new TapesGame(),
        "toys" => new ToysGame(),
        "bath" => new BathGame(),
        _ => null,
    };

    /// <summary>Aus HollowmereWorld.Tick (nur mit Obergeschoss): Minispiele an den eigenen Aufgaben tauschen.</summary>
    internal static void Tick()
    {
        if (!_registered || Time.time < _nextSwap) return;
        _nextSwap = Time.time + 0.25f;
        var ship = ShipStatus.Instance;
        var lp = PlayerControl.LocalPlayer;
        if (ship == null || lp == null || lp.myTasks == null) return;
        if (_holder == null)
        {
            Prefabs.Clear();
            _holder = new GameObject("HwUpperTaskPrefabs");
            _holder.SetActive(false);
            _holder.transform.SetParent(ship.transform, false);
            foreach (var (type, kind) in Kinds)
            {
                var go = new GameObject($"HwUpper_{kind}") { layer = 5 };
                go.transform.SetParent(_holder.transform, false);
                var mg = go.AddComponent<HwUpperMinigame>();
                mg.TransType = TransitionType.SlideBottom;
                Prefabs[type] = mg;
            }
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} {Prefabs.Count} minigame prefabs");
        }
        foreach (var t in lp.myTasks)
        {
            if (t == null || !Prefabs.TryGetValue(t.TaskType, out var mg)) continue;
            if (t.MinigamePrefab == mg) continue;
            t.MinigamePrefab = mg;
            // ein Besuch erledigt die Aufgabe: kein "(0/2)" und kein Zeitgeber in der Aufgabenliste (nur die lokale Instanz)
            var n = t.TryCast<NormalPlayerTask>();
            if (n != null && !n.IsComplete && n.taskStep == 0 && n.MaxStep > 1) { n.MaxStep = 1; n.ShowTaskStep = false; }
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} {t.TaskType} -> {mg.name}");
        }
    }

    /// <summary>Runde vorbei (HollowmereWorld.OnDestroy).</summary>
    internal static void Reset()
    {
        _holder = null;           // haengt am ShipStatus und stirbt mit ihm
        Prefabs.Clear();
        UpperArt.Clear();
    }

    internal static void Complete(NormalPlayerTask task)
    {
        int before = task.taskStep, max = task.MaxStep;
        for (int guard = 0; guard < 64 && !task.IsComplete; guard++) task.NextStep();
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} {task.TaskType}: step {before} -> {task.taskStep} of {max}, complete {task.IsComplete}");
    }
}

/// <summary>Ein eigenes Minispiel oben. Koordinaten im Lokalraum des Minispiels (Tafel 7,2 x 5,2 Einheiten um 0/0).</summary>
internal interface IUpperGame
{
    string Name { get; }
    float Progress { get; }
    bool Done { get; }
    void Build(Transform root, System.Random rnd);
    void Tick(float dt, Vector2 mouse, bool down, bool pressed);
    /// <summary>Spielt sich selbst (Autotest): Eingabe dieses Bildes.</summary>
    void Simulate(float dt, out Vector2 mouse, out bool down);
    void Dispose();
}

public class HwUpperMinigame : Minigame
{
    public HwUpperMinigame(IntPtr ptr) : base(ptr) { }

    internal static bool DiagAuto;
    internal static float DiagProgress;
    internal static string DiagOpen;

    private IUpperGame _game;
    private SpriteRenderer _close;
    private bool _done, _wasDown;
    private float _opened, _doneAt;
    private Vector2 _lastMouse;

    public void Awake()
    {
        // wie AtlasMinigame: der Il2Cpp-Konstruktor laeuft nicht, Minigame.Begin/Close loggen ueber logger
        try { if (logger == null) logger = new Logger("HwUpperMinigame", (Logger.Level)1, (Logger.Category)0); }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{HollowmereUpperTasks.LogPrefix} logger: {e.Message}"); }
        PinLogger();
    }

    // Logger festhalten (Atlas-Absturz 24.09.: der il2cpp-GC verfolgt das Basisfeld einer eingeschleusten Klasse nicht)
    private nint _loggerHandle;
    private static IntPtr _loggerField;

    private void PinLogger()
    {
        try
        {
            if (_loggerField == IntPtr.Zero)
                _loggerField = Il2CppInterop.Runtime.IL2CPP.il2cpp_class_get_field_from_name(
                    Il2CppInterop.Runtime.Il2CppClassPointerStore<Minigame>.NativeClassPtr, "logger");
            if (_loggerField == IntPtr.Zero || _loggerHandle != 0) return;
            uint off = Il2CppInterop.Runtime.IL2CPP.il2cpp_field_get_offset(_loggerField);
            IntPtr lg = System.Runtime.InteropServices.Marshal.ReadIntPtr(Pointer + (int)off);
            if (lg != IntPtr.Zero) _loggerHandle = Il2CppInterop.Runtime.IL2CPP.il2cpp_gchandle_new(lg, false);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{HollowmereUpperTasks.LogPrefix} logger pin failed: {e.Message}"); }
    }

    public void Start()
    {
        PinLogger();
        try
        {
            string kind = name.Replace("(Clone)", "").Replace("HwUpper_", "");
            _game = HollowmereUpperTasks.Create(kind);
            if (_game == null) { HalloweenPlugin.Logger.LogError($"{HollowmereUpperTasks.LogPrefix} unknown kind '{kind}'"); Close(); return; }
            gameObject.layer = 5;
            _game.Build(transform, new System.Random(Environment.TickCount));
            _close = UpperArt.Add(transform, "task_up_close.png", new Vector2(-3.25f, 2.25f), 30);
            _opened = Time.realtimeSinceStartup;
            DiagOpen = kind;
            HalloweenPlugin.Logger.LogInfo($"{HollowmereUpperTasks.LogPrefix} {kind} opened (task {(MyTask != null ? MyTask.TaskType.ToString() : "none")})");
        }
        catch (Exception e)
        {
            HalloweenPlugin.Logger.LogError($"{HollowmereUpperTasks.LogPrefix} start failed: {e}");
            _done = true;
            try { StartCoroutine(CoStartClose(0.3f)); } catch { }
        }
    }

    /// <summary>
    /// Zeiger im Lokalraum, wie AtlasMinigame: Maus ueber Camera.main. Ein selbst angelegter Controller des Spiels lieferte
    /// im echten Spiel keine brauchbare Position, die Minispiele liessen sich nicht bedienen (User 20.11.: "Tasks oben nicht
    /// loesbar"); der Autotest fuhr ueber Simulate und hat das nicht gesehen.
    /// </summary>
    private void ReadInput(out Vector2 mouse, out bool down)
    {
        var cam = Camera.main;
        var w = cam != null ? cam.ScreenToWorldPoint(Input.mousePosition) : Vector3.zero;
        mouse = transform.InverseTransformPoint(w);
        down = Input.GetMouseButton(0);
    }

    public void Update()
    {
        if (_game == null) return;
        if (_done)
        {
            // Schlussanimation weiterlaufen lassen, ohne Eingabe
            try { _game.Tick(Time.deltaTime, _lastMouse, false, false); } catch { }
            return;
        }
        if (amClosing != CloseState.None) return;
        try
        {
            float dt = Time.deltaTime;
            Vector2 mouse; bool down;
            if (DiagAuto) _game.Simulate(dt, out mouse, out down);
            else ReadInput(out mouse, out down);
            bool pressed = down && !_wasDown;
            _wasDown = down;
            _lastMouse = mouse;
            if (pressed && _close != null && Vector2.Distance(mouse, _close.transform.localPosition) < 0.35f) { Close(); return; }
            _game.Tick(dt, mouse, down, pressed);
            DiagProgress = _game.Progress;
            if (_game.Done)
            {
                _done = true;
                _doneAt = Time.realtimeSinceStartup;
                HalloweenPlugin.Logger.LogInfo($"{HollowmereUpperTasks.LogPrefix} {_game.Name} solved in {_doneAt - _opened:F1}s");
                if (MyNormTask != null) HollowmereUpperTasks.Complete(MyNormTask);
                else HalloweenPlugin.Logger.LogWarning($"{HollowmereUpperTasks.LogPrefix} {_game.Name}: no task to complete");
                StartCoroutine(CoStartClose(1.1f));
            }
        }
        catch (Exception e)
        {
            HalloweenPlugin.Logger.LogError($"{HollowmereUpperTasks.LogPrefix} update failed: {e}");
            _done = true;
            try { StartCoroutine(CoStartClose(0.3f)); } catch { }
        }
    }

    public void OnDestroy()
    {
        try { _game?.Dispose(); } catch { }
        if (_loggerHandle != 0)
        {
            try { Il2CppInterop.Runtime.IL2CPP.il2cpp_gchandle_free(_loggerHandle); } catch { }
            _loggerHandle = 0;
        }
    }
}

/// <summary>Bilder der Minispiele (Resources/villa/task_up_*.png aus dem Paket villa_map), 100 Pixel je Einheit.</summary>
internal static class UpperArt
{
    private static readonly Dictionary<string, Sprite> Cache = new();
    private static readonly List<Texture2D> Textures = new();
    private static readonly HashSet<string> Missing = new();

    internal static Sprite Get(string file, Vector2? pivot = null)
    {
        var pv = pivot ?? new Vector2(0.5f, 0.5f);
        string key = $"{file}@{pv.x:F2},{pv.y:F2}";
        if (Cache.TryGetValue(key, out var s) && s != null) return s;
        Texture2D tex = null;
        foreach (var t in Textures) if (t != null && t.name == file) { tex = t; break; }
        if (tex == null)
        {
            var data = HalloweenAssets.Read(HalloweenAssets.ResRoot + file);          // Paket villa_map: Schluessel ohne Ordner
            if (data == null)
            {
                if (Missing.Add(file)) HalloweenPlugin.Logger.LogWarning($"{HollowmereUpperTasks.LogPrefix} missing {file}");
                return null;
            }
            tex = new Texture2D(2, 2, TextureFormat.RGBA32, false) { name = file };
            if (!ImageConversion.LoadImage(tex, data, false)) return null;
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.filterMode = FilterMode.Bilinear;
            tex.hideFlags = HideFlags.HideAndDontSave;          // ueberlebt UnloadUnusedAssets (Laufzeit-Texturen)
            Textures.Add(tex);
        }
        s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pv, 100f);
        s.hideFlags = HideFlags.HideAndDontSave;
        Cache[key] = s;
        return s;
    }

    internal static SpriteRenderer Add(Transform parent, string file, Vector2 pos, int order, Vector2? pivot = null, float scale = 1f)
    {
        var go = new GameObject(file) { layer = 5 };
        go.transform.SetParent(parent, false);
        go.transform.localPosition = new Vector3(pos.x, pos.y, -order * 0.01f);
        go.transform.localScale = Vector3.one * scale;
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = Get(file, pivot);
        sr.sortingOrder = order;
        return sr;
    }

    internal static void Place(SpriteRenderer sr, Vector2 pos)
    {
        var t = sr.transform;
        t.localPosition = new Vector3(pos.x, pos.y, t.localPosition.z);
    }

    internal static void Order(SpriteRenderer sr, int order)
    {
        sr.sortingOrder = order;
        var t = sr.transform;
        t.localPosition = new Vector3(t.localPosition.x, t.localPosition.y, -order * 0.01f);
    }

    internal static void Clear()
    {
        Cache.Clear();
        Missing.Clear();
        foreach (var t in Textures) try { if (t != null) Object.Destroy(t); } catch { }
        Textures.Clear();
    }

    internal static void Sfx(string clip, float vol = 0.5f)
    {
        try { AtlasMaps.Sfx(clip, vol); } catch { }
    }
}
