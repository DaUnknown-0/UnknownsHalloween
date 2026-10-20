// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereIntro - handgezeichneter Vorspann von Hollowmere Manor vor dem Rollen-Intro.
//
// Der Vorspann ist eine Bildfolge (Resources/villa/villa_intro_000.jpg ..., 12 Bilder pro Sekunde, aus
// tools/villa_intro.py), die bildschirmfuellend VOR dem normalen Intro laeuft: der Postfix auf
// IntroCutscene.CoBegin legt die Koroutine des Spiels in eine eigene, die erst den Vorspann zeigt und dann
// das Original Schritt fuer Schritt weiterreicht. Rollen-Anzeige, TOR-Patches und Rundenstart bleiben
// unveraendert, nur spaeter. Weil jeder Client denselben Vorspann sieht, startet die Runde fuer alle gleich.
//
// Wer ihn sieht, entscheidet der Host beim Druck auf Start (Option 1961: erste Runde in dieser Lobby, jede
// Runde, aus) und verteilt es ueber UC-Kanal 230, Modul 236. Ohne Nachricht vom Host spielt kein Client den
// Vorspann (zum Beispiel ein Host ohne diese Mod). Abbrechen per Taste gibt es bewusst nicht: wer frueher
// fertig waere, liefe frueher los.
//
// Speicher: es lebt immer nur EIN Bild (eine Textur, per LoadImage ueberschrieben); jedes Bild wird erst
// geladen, wenn es dran ist (~80 KB JPG je Bild).

using System;
using System.Collections;
using System.IO;
using BepInEx.Unity.IL2CPP.Utils.Collections;
using HarmonyLib;
using Hazel;
using TheOtherRoles;
using UnityEngine;
using UnknownsCollection;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

// Kein [HarmonyPatch] an der Klasse: die Patches beruehren Atlas-Typen und werden deshalb erst in Init()
// gesetzt, das nur bei installiertem Atlas laeuft (HollowmereMap.Register).
internal static class HollowmereIntro
{
    private const string LogPrefix = "[Halloween/VillaIntro]";
    internal const byte RpcModule = 236;            // Modulbyte auf UCRpc.CallId 230 (Hollowmere Manor)
    private const byte SubIntro = 1;
    private const float Fps = 12f;
    private const string FramePrefix = "UnknownsHalloween.Resources.villa_intro_";

    public static CustomOption Mode;                // 0 = erste Runde, 1 = jede Runde, 2 = aus
    private static bool _playNext;                  // Entscheidung des Hosts fuer die naechste Runde
    private static bool _hostShownThisLobby;
    private static int _frameCount = -1;

    internal static void Init()
    {
        try
        {
            Mode = CustomOption.Create(1961, CustomOption.CustomOptionType.General, "Hollowmere Intro",
                new[] { "First Round", "Every Round", "Off" });
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} option failed: {e}"); }
        try { UCRpc.Register(RpcModule, HandleRpc); }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} rpc registration failed: {e}"); }
        try
        {
            var h = new Harmony(HalloweenPlugin.PluginGuid + ".villaintro");
            h.Patch(AccessTools.Method(typeof(GameStartManager), nameof(GameStartManager.BeginGame)),
                prefix: new HarmonyMethod(typeof(HollowmereIntro), nameof(GameStartManager_BeginGame_Prefix)));
            h.Patch(AccessTools.Method(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined)),
                postfix: new HarmonyMethod(typeof(HollowmereIntro), nameof(AmongUsClient_OnGameJoined_Postfix)));
            h.Patch(AccessTools.Method(typeof(IntroCutscene), nameof(IntroCutscene.CoBegin)),
                postfix: new HarmonyMethod(typeof(HollowmereIntro), nameof(IntroCutscene_CoBegin_Postfix)));
            h.Patch(AccessTools.Method(typeof(HudManager), nameof(HudManager.Update)),
                postfix: new HarmonyMethod(typeof(HollowmereIntro), nameof(HudManager_Update_WatchdogPostfix)));
            h.Patch(AccessTools.Method(typeof(IntroCutscene), nameof(IntroCutscene.OnDestroy)),
                postfix: new HarmonyMethod(typeof(HollowmereIntro), nameof(IntroCutscene_OnDestroy_Postfix)));
            if (Diag)
                h.Patch(AccessTools.Method(typeof(HudManager), nameof(HudManager.Update)),
                    postfix: new HarmonyMethod(typeof(HollowmereIntro), nameof(HudManager_Update_DiagPostfix)));
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} patching failed, no intro: {e}"); }
    }

    // Der Vorspann laeuft in der Intro-Koroutine des Spiels. Bricht die ab (Intro vorzeitig zerstoert, im Test
    // 15.10. nach einem Rollenwechsel per Role Control mitten im Intro), kam Play() nie bei Cleanup() an und
    // die schwarze Flaeche blieb fuer die ganze Runde liegen. Deshalb raeumt hier ein Waechter auf, sobald die
    // Spielzeit des Vorspanns um ist.
    private static float _deadline = -1f;

    internal static void HudManager_Update_WatchdogPostfix()
    {
        if (_root == null || _deadline < 0f || Time.time < _deadline) return;
        HalloweenPlugin.Logger.LogWarning($"{LogPrefix} intro was cut off, overlay removed by the watchdog");
        Cleanup();
        _playing = false;
    }

    // ------------------------------------------------------------------ Diagnose (Autotest im Freeplay)

    private static bool Diag => (Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "").Contains("villaintro");
    private static float _diagAt = -1f;
    private static bool _diagDone;

    // Das Freeplay spielt kein Rollen-Intro: der Vorspann startet hier 2 s nach dem Kartenbau einmal und
    // fotografiert sich selbst (AtlasShots/intro_<t>.png).
    internal static void HudManager_Update_DiagPostfix(HudManager __instance)
    {
        try
        {
            if (_diagDone || UnknownsAtlas.AtlasMaps.ActiveKey != HollowmereMap.Key) return;
            if (_diagAt < 0f) { _diagAt = Time.time + 2f; return; }
            if (Time.time < _diagAt) return;
            _diagDone = true;
            // "villaintro2": wie im echten Rundenstart, ueber dem echten Rollen-Intro des Spiels
            if ((Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "").Contains("villaintro2"))
                __instance.StartCoroutine(DiagRealIntro(__instance).WrapToIl2Cpp());
            else
                __instance.StartCoroutine(DiagRun().WrapToIl2Cpp());
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} diag failed: {e}"); _diagDone = true; }
    }

    private static IEnumerator DiagRun()
    {
        float[] at = { 0.62f, 2.6f, 3.9f, 5.0f, 6.3f };
        int next = 0;
        float t0 = Time.time;
        var play = Play();
        string dir = Path.Combine(BepInEx.Paths.GameRootPath, "AtlasShots");
        Directory.CreateDirectory(dir);
        while (play.MoveNext())
        {
            float t = Time.time - t0;
            if (next < at.Length && t >= at[next])
            {
                string file = Path.Combine(dir, $"intro_{at[next]:0.0}s_{DateTime.Now:HHmmss}.png".Replace(',', '.'));
                ScreenCapture.CaptureScreenshot(file);
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag shot -> {file}");
                next++;
            }
            yield return play.Current;
        }
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: intro played to the end");
    }

    // Echtes Rollen-Intro im Freeplay: Prefab erzeugen und CoBegin starten (der Postfix haengt den Vorspann davor),
    // dabei fotografieren und alle Renderer von Intro und Vorspann protokollieren. Spieltest 17.10.: im echten
    // Rundenstart war nur oben ein Streifen des Vorspanns zu sehen, darunter schwarz.
    private static IEnumerator DiagRealIntro(HudManager hud)
    {
        string dir = Path.Combine(BepInEx.Paths.GameRootPath, "AtlasShots");
        Directory.CreateDirectory(dir);
        IntroCutscene intro = null;
        try
        {
            intro = Object.Instantiate(hud.IntroPrefab, hud.transform);
            hud.StartCoroutine(intro.CoBegin());
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag2: real intro started");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} diag2: intro failed: {e}"); }
        float t0 = Time.time;
        float[] at = { 1.0f, 3.0f, 5.5f };
        int next = 0;
        bool dumped = false;
        while (Time.time - t0 < 9f)
        {
            float t = Time.time - t0;
            if (!dumped && t >= 1.5f) { dumped = true; DiagDump(intro); }
            if (next < at.Length && t >= at[next])
            {
                ScreenCapture.CaptureScreenshot(Path.Combine(dir, $"intro2_{at[next]:0.0}s.png".Replace(',', '.')));
                next++;
            }
            yield return null;
        }
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag: all done");
        Application.Quit();
    }

    private static void DiagDump(IntroCutscene intro)
    {
        void One(string tag, Renderer r, Transform stop)
        {
            if (r == null) return;
            string path = r.name;
            for (var t = r.transform.parent; t != null && t != stop; t = t.parent) path = t.name + "/" + path;
            var b = r.bounds;
            HalloweenPlugin.Logger.LogInfo(FormattableString.Invariant(
                $"{LogPrefix} r {tag} {path} on {(r.enabled && r.gameObject.activeInHierarchy ? 1 : 0)} layer {r.sortingLayerName}({SortingLayer.GetLayerValueFromID(r.sortingLayerID)}) order {r.sortingOrder} go {r.gameObject.layer} z {r.transform.position.z:R} bounds {b.min.x:F2},{b.min.y:F2}..{b.max.x:F2},{b.max.y:F2}"));
        }
        try
        {
            if (intro != null) foreach (var r in intro.GetComponentsInChildren<Renderer>(true)) One("intro", r, intro.transform);
            if (_root != null) foreach (var r in _root.GetComponentsInChildren<Renderer>(true)) One("villa", r, _root.transform);
            var fs = HudManager.InstanceExists ? HudManager.Instance.FullScreen : null;
            if (fs != null) One("hud", fs, null);
            foreach (var c in Camera.allCameras)
                HalloweenPlugin.Logger.LogInfo(FormattableString.Invariant(
                    $"{LogPrefix} cam {c.name} depth {c.depth} mask {c.cullingMask} ortho {c.orthographicSize:F2} pos {c.transform.position.x:F2},{c.transform.position.y:F2},{c.transform.position.z:F2}"));
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag dump: {e.Message}"); }
    }

    // ------------------------------------------------------------------ Entscheidung des Hosts

    internal static void GameStartManager_BeginGame_Prefix()
    {
        try
        {
            var ac = AmongUsClient.Instance;
            if (ac == null || !ac.AmHost || PlayerControl.LocalPlayer == null) return;
            bool villa = UnknownsAtlas.AtlasMaps.SelectedKey == HollowmereMap.Key;
            int mode = Mode?.getSelection() ?? 0;
            bool play = villa && FrameCount() > 0 && (mode == 1 || (mode == 0 && !_hostShownThisLobby));
            if (play && mode == 0) _hostShownThisLobby = true;
            _playNext = play;
            var w = UCRpc.Begin(RpcModule);
            w.Write(SubIntro);
            w.Write(play);
            ac.FinishRpcImmediately(w);
            if (villa) HalloweenPlugin.Logger.LogInfo($"{LogPrefix} host: intro {(play ? "on" : "off")} for this round");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} host decision failed: {e.Message}"); }
    }

    private static void HandleRpc(MessageReader reader)
    {
        try
        {
            byte sub = reader.ReadByte();
            if (sub != SubIntro) { HollowmereWorld.HandleRpc(sub, reader); return; }   // Mechaniken (Sub 2+)
            bool play = reader.ReadBoolean();
            if (UCRpc.RequireHost("Hollowmere.Intro")) _playNext = play;
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} rpc failed: {e.Message}"); }
    }

    internal static void AmongUsClient_OnGameJoined_Postfix()
    {
        _playNext = false;
        _hostShownThisLobby = false;
    }

    // ------------------------------------------------------------------ Einhaengen vor dem Rollen-Intro

    private static IntroCutscene _intro;            // das Rollen-Intro, vor dem der Vorspann laeuft (Sortierung, Diagnose)

    internal static void IntroCutscene_CoBegin_Postfix(IntroCutscene __instance, ref Il2CppSystem.Collections.IEnumerator __result)
    {
        try
        {
            _intro = __instance;
            // Diagnose: UC_HALLOWEEN_DIAG=villaintro spielt den Vorspann auch ohne Host-Entscheidung (Freeplay)
            bool diag = (Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "").Contains("villaintro");
            if ((!_playNext && !diag) || __result == null) return;
            _playNext = false;
            if (UnknownsAtlas.AtlasMaps.ActiveKey != HollowmereMap.Key) return;
            __result = Wrap(__result).WrapToIl2Cpp();
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} wrap failed, plain intro: {e}"); }
    }

    // Der Vorspann laeuft als eigene Koroutine auf dem HudManager, nicht in der Intro-Koroutine: wird die
    // IntroCutscene vorzeitig zerstoert (15.10.: Rollenwechsel per Role Control, Solo-Runde), stirbt ihre
    // Koroutine mitten im Vorspann, und die schwarze Flaeche blieb liegen. Hier wartet das Intro nur, bis
    // der Vorspann fertig ist; IntroCutscene.OnDestroy raeumt ihn zusaetzlich sofort weg.
    private static IEnumerator Wrap(Il2CppSystem.Collections.IEnumerator original)
    {
        if (HudManager.InstanceExists)
        {
            _playing = true;
            HudManager.Instance.StartCoroutine(Guarded().WrapToIl2Cpp());
            while (_playing) yield return null;
        }
        // danach das Original unveraendert weiterreichen
        while (original.MoveNext()) yield return original.Current;
    }

    private static bool _playing;

    private static IEnumerator Guarded()
    {
        var play = Play();
        while (true)
        {
            object step;
            try { if (!play.MoveNext()) break; step = play.Current; }
            catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} playback failed: {e}"); break; }
            yield return step;
        }
        Cleanup();
        _playing = false;
    }

    internal static void IntroCutscene_OnDestroy_Postfix()
    {
        if (_root == null) return;
        HalloweenPlugin.Logger.LogWarning($"{LogPrefix} intro ended early, overlay removed");
        Cleanup();
        _playing = false;
    }

    // ------------------------------------------------------------------ Abspielen

    private static GameObject _root;
    private static Texture2D _tex;

    private static int FrameCount()
    {
        if (_frameCount >= 0) return _frameCount;
        int n = 0;
        while (HalloweenAssets.Exists($"{FramePrefix}{n:000}.jpg")) n++;
        _frameCount = n;
        return n;
    }

    private static byte[] FrameBytes(int i)
    {
        using Stream s = HalloweenAssets.Open($"{FramePrefix}{i:000}.jpg");
        if (s == null) return null;
        var data = new byte[s.Length];
        int read = 0;
        while (read < data.Length) { int n = s.Read(data, read, data.Length - read); if (n <= 0) break; read += n; }
        return read == data.Length ? data : null;
    }

    private static IEnumerator Play()
    {
        int frames = FrameCount();
        var cam = Camera.main;
        var first = frames > 0 ? FrameBytes(0) : null;
        if (cam == null || first == null) yield break;

        _tex = new Texture2D(2, 2, TextureFormat.RGB24, false) { hideFlags = HideFlags.HideAndDontSave };
        if (!ImageConversion.LoadImage(_tex, first, false)) { Cleanup(); yield break; }
        _tex.filterMode = FilterMode.Bilinear;
        _tex.wrapMode = TextureWrapMode.Clamp;

        // Bildschirmfuellend und ueber ALLEM: wie die Bildschirmabdunkelung des Spiels (HudManager.FullScreen,
        // gleiche Ebene, Sortierschicht und Tiefe knapp davor). Am Hauptkamera-Kind lag der Vorspann im
        // Test 09.10. unter der HUD-Leiste, die eine eigene UI-Kamera zeichnet. Schwarzer Rand bei anderem
        // Seitenverhaeltnis.
        var fs = HudManager.InstanceExists ? HudManager.Instance.FullScreen : null;
        _layer = fs != null ? fs.gameObject.layer : 5;
        _sortLayer = fs != null ? fs.sortingLayerID : 0;
        _baseOrder = fs != null ? fs.sortingOrder + 10 : 32000;
        _root = new GameObject("Hollowmere_Intro") { layer = _layer };
        if (fs != null && fs.transform.parent != null)
        {
            var parent = fs.transform.parent;
            _root.transform.SetParent(parent, false);
            _root.transform.localPosition = new Vector3(0f, 0f, fs.transform.localPosition.z - 1f);
            var ls = parent.lossyScale;
            _root.transform.localScale = new Vector3(1f / Mathf.Max(0.0001f, ls.x), 1f / Mathf.Max(0.0001f, ls.y), 1f);
        }
        else
        {
            _root.transform.SetParent(cam.transform, false);
            _root.transform.localPosition = new Vector3(0f, 0f, 5f);
        }
        // Groesse aus der Kamera, die diese Ebene WIRKLICH zeichnet (die UI-Kamera der HUD-Ebene), nicht aus
        // Camera.main: in der Lobby bzw. auf der Villa zoomt die Hauptkamera anders, dann war der Vorspann
        // ~1,5x zu gross und verschoben (User 17.10.: nur ein Streifen der Filmklappe oben sichtbar).
        var view = RenderCameraFor(_layer) ?? cam;
        if (view != cam)
        {
            // mittig vor diese Kamera, mit ausgeglichenem Massstab der Eltern
            var vp = _root.transform.parent != null ? _root.transform.parent : null;
            _root.transform.SetParent(view.transform, false);
            _root.transform.localPosition = new Vector3(0f, 0f, Mathf.Max(view.nearClipPlane + 0.5f, 1f));
            _root.transform.localRotation = Quaternion.identity;
            var vls = view.transform.lossyScale;
            _root.transform.localScale = new Vector3(1f / Mathf.Max(0.0001f, vls.x), 1f / Mathf.Max(0.0001f, vls.y), 1f);
        }
        cam = view;
        // Das Rollen-Intro ist schon aufgebaut, waehrend der Vorspann laeuft (es wartet nur). Seine schwarzen Ebenen
        // (BackgroundLayer, ForegroundFade, FrontMost) lagen trotz niedrigerer Sortierung VOR dem Vorspann (Tiefe
        // z -309..-325 gegen -9); sichtbar blieb nur oben ein Streifen bis y 5,40 (Spieltest und Selbsttest 17.10.).
        // Deshalb wird das Intro fuer die Dauer des Vorspanns ausgeblendet (es hat da noch nicht angefangen).
        HideIntro();
        float h = cam.orthographicSize * 2f, w = h * cam.aspect;
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} drawn by camera '{cam.name}' (ortho {cam.orthographicSize:F2}, aspect {cam.aspect:F2}, layer {_layer})");
        var black = MakeQuad("black", Color.black, 0);
        black.transform.localScale = new Vector3(w * 1.05f, h * 1.05f, 1f);
        var go = new GameObject("frame") { layer = _layer };
        go.transform.SetParent(_root.transform, false);
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = Sprite.Create(_tex, new Rect(0, 0, _tex.width, _tex.height), new Vector2(0.5f, 0.5f), 100f);
        sr.sortingLayerID = _sortLayer;
        sr.sortingOrder = _baseOrder + 1;
        float sx = w / (_tex.width / 100f), sy = h / (_tex.height / 100f);
        float s = Mathf.Min(sx, sy);
        go.transform.localScale = new Vector3(s, s, 1f);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} playing {frames} frames ({frames / Fps:F1} s)");

        float t0 = Time.time;
        _deadline = t0 + frames / Fps + 1f;
        int shown = 0;
        while (true)
        {
            float t = Time.time - t0;
            try
            {
                float ch = cam.orthographicSize * 2f, cw = ch * cam.aspect;
                black.transform.localScale = new Vector3(cw * 1.1f, ch * 1.1f, 1f);
                float fs2 = Mathf.Min(cw / (_tex.width / 100f), ch / (_tex.height / 100f));
                go.transform.localScale = new Vector3(fs2, fs2, 1f);
            }
            catch { }
            int want = Mathf.Min(frames - 1, (int)(t * Fps));
            if (want != shown)
            {
                var bytes = FrameBytes(want);
                if (bytes != null) ImageConversion.LoadImage(_tex, bytes, false);
                shown = want;
            }
            // die letzten 0,3 s ausblenden, dann geht es mit dem Rollen-Intro weiter
            float end = frames / Fps;
            if (t >= end - 0.3f) sr.color = new Color(1f, 1f, 1f, Mathf.Clamp01((end - t) / 0.3f));
            if (t >= end) break;
            yield return null;
        }
        Cleanup();
    }

    private static int _layer = 5, _sortLayer, _baseOrder = 32000;

    /// Die orthografische Kamera, die die Ebene zeichnet und am weitesten vorn rendert (hoechste depth).
    private static Camera RenderCameraFor(int layer)
    {
        Camera best = null;
        try
        {
            foreach (var c in Camera.allCameras)
            {
                if (c == null || !c.enabled || !c.orthographic || (c.cullingMask & (1 << layer)) == 0) continue;
                if (best == null || c.depth > best.depth) best = c;
            }
        }
        catch { }
        return best;
    }

    private static GameObject MakeQuad(string name, Color c, int order)
    {
        var go = new GameObject(name) { layer = _layer };
        go.transform.SetParent(_root.transform, false);
        var sr = go.AddComponent<SpriteRenderer>();
        var tex = new Texture2D(1, 1) { hideFlags = HideFlags.HideAndDontSave };
        tex.SetPixel(0, 0, Color.white);
        tex.Apply();
        sr.sprite = Sprite.Create(tex, new Rect(0, 0, 1, 1), new Vector2(0.5f, 0.5f), 1f);
        sr.color = c;
        sr.sortingLayerID = _sortLayer;
        sr.sortingOrder = _baseOrder + order;
        return go;
    }

    // Renderer des Rollen-Intros, die der Vorspann ausgeblendet hat (werden genau so wieder eingeschaltet).
    private static readonly System.Collections.Generic.List<Renderer> _hiddenIntro = new();
    private static float _introMinZ;

    private static void HideIntro()
    {
        _hiddenIntro.Clear();
        _introMinZ = 0f;
        try
        {
            if (_intro == null) return;
            foreach (var r in _intro.GetComponentsInChildren<Renderer>(true))
            {
                if (r == null) continue;
                _introMinZ = Mathf.Min(_introMinZ, r.transform.position.z);
                if (!r.enabled) continue;
                r.enabled = false;
                _hiddenIntro.Add(r);
            }
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} role intro hidden while the intro plays ({_hiddenIntro.Count} renderer(s), front z {_introMinZ:F0})");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} hiding the role intro failed: {e.Message}"); }
    }

    private static void RestoreIntro()
    {
        foreach (var r in _hiddenIntro)
        {
            try { if (r != null) r.enabled = true; } catch { }
        }
        _hiddenIntro.Clear();
    }

    private static void Cleanup()
    {
        RestoreIntro();
        try { if (_root != null) Object.Destroy(_root); } catch { }
        try { if (_tex != null) Object.Destroy(_tex); } catch { }
        _root = null;
        _tex = null;
        _deadline = -1f;
    }
}
