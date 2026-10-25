// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Grave - Easter Egg (User 2026-10-25): das offene Grab unten links auf dem Friedhof der grossen Manor (Art
// offenes_grab) wird nach dem ersten Meeting, in dem es Tote gibt, zum Grab eines dieser Toten: zugeschuettet, Grabstein
// mit "R.I.P." und Namen. Erst nach dem Meeting, dann ist der Tod ohnehin allen bekannt. Sind bis dahin mehrere
// gestorben, bekommt es der mit der kleinsten Spieler-Id (nicht der zuerst Gestorbene: die Reihenfolge waere eine
// Spielinformation, Easter Eggs verraten nichts).
// - Der Autor (Mo): darunter "still coding" und ein aufgeklappter Laptop mit laufendem Matrix-Code auf dem Grabhuegel.
// - Da Fishbone (DrSuspect): sein Haustier huepft froehlich neben dem Grab (Bild seines Haustiers, solange er lebte gemerkt).
// Erkennung wie UTS EasterEggCoding: SHA-256 von PUID bzw. Friend-Code (kein Klartext im Repo). Rein kosmetisch, jeder
// Client lokal, kein RPC. Grafik Resources/hw2026/villa_egg/ (GPT), Namen als Text (Bild-KIs schreiben keine Namen).

using System;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;
using UnknownsAtlas;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    private static readonly string[] GraveOwnerHashes =
    {
        "d10f0e308524211c45d93ec3300efca28e35488ea35598196c67b1ababb7fc19",   // Mo: PUID
        "cf2eab42fba217e7af4237f7a3bcd35402f2790602e07d92c6344096701480c6",   // Mo: Friend-Code
    };
    private static readonly string[] GraveFishboneHashes =
    {
        "6000e7a041af292fa9c437cf6d85c0c0d813f67d354b55298fe25f5cb9c8a124",   // Da Fishbone: PUID
        "646c6a52f202d55d7d40ebd1c2f998647e45116f73281b9b6669952243df6bc2",   // Da Fishbone: Friend-Code
    };
    private const string GraveRes = "UnknownsHalloween.Resources.hw2026.villa_egg.egg_grave_filled.png";
    private const string LaptopRes = "UnknownsHalloween.Resources.hw2026.villa_egg.egg_laptop.png";
    private static readonly Vector2 GraveNameAt = new(0.495f, 0.665f);   // Steinmitte, Anteil des Sprites von links/unten
    private static readonly Vector2 GraveMoundAt = new(0.5f, 0.36f);     // Mitte des Grabhuegels
    private static readonly Rect LaptopScreen = new(0.125f, 0.445f, 0.74f, 0.49f);   // Bildschirm, Anteil von links/unten
    private const int MatrixW = 40, MatrixH = 26;

    private SpriteRenderer _graveSr;
    private bool _graveShown, _graveSawMeeting;
    private float _graveNoMeetingSince = -1f;
    private GameObject _graveText, _gravePet;
    private Vector3 _gravePetBase;
    // Matrix-Code auf dem Laptop
    private Texture2D _matrixTex;
    private Color32[] _matrixPx;
    private float[] _matrixHead;
    private float[] _matrixSpeed;
    private float _nextMatrix;
    // Haustier von Da Fishbone, gemerkt solange er lebt
    private Sprite _fishbonePetSprite;
    private Material _fishbonePetMat;

    private void GraveReset()
    {
        _graveShown = _graveSawMeeting = false;
        _graveNoMeetingSince = -1f;
        _graveText = _gravePet = null;
        _graveSr = null;
        _matrixTex = null;
        _tasksTrimmed = false;
        try { TrimTasks(); } catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} task trim failed: {e.Message}"); }
        _fishbonePetSprite = null; _fishbonePetMat = null;
        try
        {
            var props = AtlasMaps.Props("offenes_grab");
            if (props.Count > 0) _graveSr = props[0].Renderer;
        }
        catch { }
    }

    private void GraveTick()
    {
        if (!_tasksTrimmed) { try { TrimTasks(); } catch { } }
        if (_graveSr == null) return;
        if (_graveShown) { GraveAnimate(); return; }
        RememberFishbonePet();
        bool meeting = MeetingHud.Instance != null || ExileController.Instance != null;
        if (meeting) { _graveSawMeeting = true; _graveNoMeetingSince = -1f; return; }
        if (!_graveSawMeeting) return;
        // Meeting vorbei: eine Sekunde ohne MeetingHud und Rauswurf abwarten (dazwischen kann ein Bild ohne beides liegen,
        // und beim Rauswurf ist der Tod erst nach dem Bild gesetzt)
        if (_graveNoMeetingSince < 0f) { _graveNoMeetingSince = Time.time; return; }
        if (Time.time - _graveNoMeetingSince < 1f) return;
        _graveSawMeeting = false;
        PlayerControl pick = null;
        foreach (var p in PlayerControl.AllPlayerControls.ToArray())
        {
            if (p == null || p.Data == null || !p.Data.IsDead || p.Data.Disconnected) continue;
            if (pick == null || p.PlayerId < pick.PlayerId) pick = p;
        }
        if (pick != null) ShowGrave(pick);
    }

    // ------------------------------------------------------------------ Task ohne Konsole

    private bool _tasksTrimmed;

    /// <summary>Die Weapons-Konsole (Fledermaus-Fenster) gibt es seit 25.10. nicht mehr (villa_layout.DROP_CONSOLES); ohne sie
    /// waere "Clear Asteroids" unloesbar und die Crew koennte nicht ueber Tasks gewinnen. Deshalb fliegt der Task aus den
    /// Listen der Karte, bevor der Host Tasks verteilt (Kartenbau und erster Tick, beides harmlos doppelt).</summary>
    private void TrimTasks()
    {
        if (_tasksTrimmed) return;
        var ship = ShipStatus.Instance;
        if (ship == null) return;
        _tasksTrimmed = true;
        int before = Count(ship.CommonTasks) + Count(ship.ShortTasks) + Count(ship.LongTasks);
        ship.CommonTasks = WithoutAsteroids(ship.CommonTasks);
        ship.ShortTasks = WithoutAsteroids(ship.ShortTasks);
        ship.LongTasks = WithoutAsteroids(ship.LongTasks);
        int after = Count(ship.CommonTasks) + Count(ship.ShortTasks) + Count(ship.LongTasks);
        if (after != before) HalloweenPlugin.Logger.LogInfo($"{LogPrefix} removed {before - after} task(s) without console (Clear Asteroids)");
    }

    private static int Count(Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<NormalPlayerTask> a) => a?.Length ?? 0;

    private static Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<NormalPlayerTask> WithoutAsteroids(
        Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<NormalPlayerTask> a)
    {
        if (a == null) return a;
        var keep = new System.Collections.Generic.List<NormalPlayerTask>();
        foreach (var t in a) if (t == null || t.TaskType != TaskTypes.ClearAsteroids) keep.Add(t);
        return keep.Count == a.Length ? a : new Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<NormalPlayerTask>(keep.ToArray());
    }

    private static bool GraveMatches(PlayerControl p, string[] hashes)
    {
        try { return p != null && p.Data != null && (HashIn(p.Data.Puid, hashes) || HashIn(p.Data.FriendCode, hashes)); }
        catch { return false; }
    }

    private static bool HashIn(string id, string[] hashes)
    {
        if (string.IsNullOrEmpty(id)) return false;
        using var sha = SHA256.Create();
        var hash = sha.ComputeHash(Encoding.UTF8.GetBytes(id));
        var sb = new StringBuilder(64);
        foreach (byte b in hash) sb.Append(b.ToString("x2"));
        string h = sb.ToString();
        foreach (var o in hashes) if (o == h) return true;
        return false;
    }

    private float _nextPetLook;

    private void RememberFishbonePet()
    {
        if (Time.time < _nextPetLook) return;
        _nextPetLook = Time.time + 2f;
        try
        {
            foreach (var p in PlayerControl.AllPlayerControls.ToArray())
            {
                if (p == null || p.Data == null || p.Data.IsDead || !GraveMatches(p, GraveFishboneHashes)) continue;
                var pet = p.cosmetics != null ? p.cosmetics.currentPet : null;
                var sr = pet != null ? pet.GetComponentInChildren<SpriteRenderer>() : null;
                if (sr == null || sr.sprite == null) return;
                _fishbonePetSprite = sr.sprite;
                _fishbonePetMat = sr.sharedMaterial;
                return;
            }
        }
        catch { }
    }

    private static Sprite LoadEggSprite(string res, Vector2 pivot, float ppu)
    {
        if (!HalloweenAssets.Exists(res)) return null;
        var data = HalloweenAssets.Read(res);
        var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        if (data == null || !ImageConversion.LoadImage(tex, data, false)) return null;
        tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        var sp = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, ppu);
        sp.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        return sp;
    }

    private SpriteRenderer GraveChild(string name, Sprite sprite, Vector3 local, int order)
    {
        var go = new GameObject(name) { layer = _graveSr.gameObject.layer };
        go.transform.SetParent(_graveSr.transform, false);
        go.transform.localPosition = local;
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = sprite;
        sr.sortingLayerID = _graveSr.sortingLayerID;
        sr.sortingOrder = _graveSr.sortingOrder + order;
        return sr;
    }

    private void ShowGrave(PlayerControl p)
    {
        try
        {
            var orig = _graveSr.sprite;
            if (orig == null) return;
            var size = orig.rect.size;
            float ppu = orig.pixelsPerUnit;
            var pivot = new Vector2(orig.pivot.x / size.x, orig.pivot.y / size.y);
            var grave = LoadEggSprite(GraveRes, pivot, ppu);
            if (grave == null) return;
            _graveSr.sprite = grave;
            _graveShown = true;
            Vector3 At(Vector2 frac, float z) => new((frac.x - pivot.x) * size.x / ppu, (frac.y - pivot.y) * size.y / ppu, z);
            bool owner = GraveMatches(p, GraveOwnerHashes);
            string name = p.Data.PlayerName ?? "?";

            // Inschrift: dunkles Grau, wie eingemeisselt
            _graveText = new GameObject("GraveInscription") { layer = _graveSr.gameObject.layer };
            _graveText.transform.SetParent(_graveSr.transform, false);
            _graveText.transform.localPosition = At(GraveNameAt, -0.001f);
            var t = _graveText.AddComponent<TMPro.TextMeshPro>();
            var f = HalloweenUI.Font();
            if (f != null) t.font = f;
            t.fontStyle = TMPro.FontStyles.Bold;
            t.alignment = TMPro.TextAlignmentOptions.Center;
            t.enableWordWrapping = false;
            t.enableAutoSizing = true; t.fontSizeMin = 0.3f; t.fontSizeMax = 0.9f;
            t.color = new Color32(58, 58, 64, 255);
            t.rectTransform.sizeDelta = new Vector2(size.x * 0.24f / ppu, size.y * (owner ? 0.2f : 0.16f) / ppu);
            t.text = owner ? $"R.I.P.\n{name}\n<size=70%>still coding</size>" : $"R.I.P.\n{name}";
            var mr = t.GetComponent<MeshRenderer>();
            if (mr != null) { mr.sortingLayerID = _graveSr.sortingLayerID; mr.sortingOrder = _graveSr.sortingOrder + 1; }

            if (owner) ShowLaptop(At(GraveMoundAt, -0.002f), ppu);
            if (GraveMatches(p, GraveFishboneHashes) && _fishbonePetSprite != null)
            {
                var pet = GraveChild("GravePet", _fishbonePetSprite, At(new Vector2(0.86f, 0.1f), -0.003f), 3);
                if (_fishbonePetMat != null) pet.sharedMaterial = _fishbonePetMat;
                _gravePet = pet.gameObject;
                _gravePetBase = pet.transform.localPosition;
            }
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} the open grave is taken now");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} grave egg failed: {e.Message}"); }
    }

    private void ShowLaptop(Vector3 at, float ppu)
    {
        var lap = LoadEggSprite(LaptopRes, new Vector2(0.5f, 0.5f), 1f);
        if (lap == null) return;
        // Laptop 0,55 m breit
        float scale = 0.55f / lap.rect.width;
        var lsr = GraveChild("GraveLaptop", lap, at, 2);
        lsr.transform.localScale = new Vector3(scale, scale, 1f);          // Einheiten wie das Grab-Sprite (Meter)
        // Matrix-Code: kleine Textur, Punktfilter, Spalten mit fallenden hellen Koepfen
        _matrixTex = new Texture2D(MatrixW, MatrixH, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
        _matrixTex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        _matrixPx = new Color32[MatrixW * MatrixH];
        _matrixHead = new float[MatrixW];
        _matrixSpeed = new float[MatrixW];
        for (int x = 0; x < MatrixW; x++) { _matrixHead[x] = UnityEngine.Random.Range(0f, MatrixH); _matrixSpeed[x] = UnityEngine.Random.Range(0.35f, 1.1f); }
        var mx = Sprite.Create(_matrixTex, new Rect(0, 0, MatrixW, MatrixH), new Vector2(0.5f, 0.5f), 1f);
        mx.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        var msr = new GameObject("GraveLaptopScreen") { layer = lsr.gameObject.layer };
        msr.transform.SetParent(lsr.transform, false);
        float w = lap.rect.width, h = lap.rect.height;
        msr.transform.localPosition = new Vector3((LaptopScreen.center.x - 0.5f) * w, (LaptopScreen.center.y - 0.5f) * h, -0.0005f);
        msr.transform.localScale = new Vector3(LaptopScreen.width * w / MatrixW, LaptopScreen.height * h / MatrixH, 1f);
        var s = msr.AddComponent<SpriteRenderer>();
        s.sprite = mx;
        s.sortingLayerID = lsr.sortingLayerID;
        s.sortingOrder = lsr.sortingOrder + 1;
        StepMatrix();
    }

    private void GraveAnimate()
    {
        float now = Time.time;
        if (_matrixTex != null && now >= _nextMatrix) { _nextMatrix = now + 0.07f; StepMatrix(); }
        if (_gravePet != null)
        {
            // froehlich: kleine Huepfer, ab und zu umdrehen
            float hop = Mathf.Abs(Mathf.Sin(now * 5f)) * 0.12f;
            _gravePet.transform.localPosition = _gravePetBase + new Vector3(0f, hop, 0f);
            var sr = _gravePet.GetComponent<SpriteRenderer>();
            if (sr != null) sr.flipX = Mathf.Repeat(now, 6f) > 3f;
        }
    }

    private void StepMatrix()
    {
        for (int i = 0; i < _matrixPx.Length; i++)
        {
            var c = _matrixPx[i];
            _matrixPx[i] = new Color32((byte)(c.r * 0.82f), (byte)(c.g * 0.86f), (byte)(c.b * 0.82f), 255);   // Spur verblasst
        }
        for (int x = 0; x < MatrixW; x++)
        {
            _matrixHead[x] -= _matrixSpeed[x];
            if (_matrixHead[x] < -6f) { _matrixHead[x] = MatrixH + UnityEngine.Random.Range(0f, 8f); _matrixSpeed[x] = UnityEngine.Random.Range(0.35f, 1.1f); }
            int y = Mathf.RoundToInt(_matrixHead[x]);
            if (y < 0 || y >= MatrixH) continue;
            // Kopf hell, dahinter gruen; kleine Luecken lassen es nach Zeichen aussehen
            _matrixPx[y * MatrixW + x] = UnityEngine.Random.value < 0.85f ? new Color32(190, 255, 190, 255) : new Color32(0, 0, 0, 255);
            if (y + 1 < MatrixH && UnityEngine.Random.value < 0.7f) _matrixPx[(y + 1) * MatrixW + x] = new Color32(40, 220, 70, 255);
        }
        _matrixTex.SetPixels32(_matrixPx);
        _matrixTex.Apply(false, false);
    }
}
