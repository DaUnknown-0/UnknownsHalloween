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
//   Wer lebend daneben steht, kann es streicheln (User 2026-10-26): Use-Knopf "PET", das Tier huepft schneller, quetscht
//   sich vor Freude und Herzen steigen auf. Nur bei dem, der streichelt (lokal, wie das ganze Grab).
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
    private Vector3 _gravePetBase, _gravePetScale;
    // Streicheln: Freude bis _petJoyUntil, aufsteigende Herzen
    private const float PetReach = 1.3f, PetJoy = 1.8f;
    private float _petJoyUntil = -1f;
    private readonly System.Collections.Generic.List<(GameObject Go, float Born, float Dx)> _petHearts = new();
    private static Sprite _heartSprite;
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
        _petJoyUntil = -1f;
        _petHearts.Clear();
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
        if (after != before) HalloweenPlugin.Logger.LogInfo($"{LogPrefix} removed {before - after} task(s) without console (Clear Asteroids, large: Align Engine Output)");
    }

    private static int Count(Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<NormalPlayerTask> a) => a?.Length ?? 0;

    private static Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<NormalPlayerTask> WithoutAsteroids(
        Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<NormalPlayerTask> a)
    {
        if (a == null) return a;
        var keep = new System.Collections.Generic.List<NormalPlayerTask>();
        // 28.10.: auf der grossen Manor gibt es auch "Align Engine Output" nicht mehr (der Generator steht als eigene Aufgabe im
        // Crew Camp, villa_layout.DROP_CONSOLES_LARGE)
        bool large = HollowmereMap.Large;
        foreach (var t in a) if (t == null || (t.TaskType != TaskTypes.ClearAsteroids && !(large && t.TaskType == TaskTypes.AlignEngineOutput))) keep.Add(t);
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
            // 28.10. (n58, DrSuspect): die Halloween-Schrift war auf dem Stein schwer zu lesen; die schlichte Spielschrift
            var f = TMPro.TMP_Settings.defaultFontAsset ?? HalloweenUI.Font();
            if (f != null) t.font = f;
            // 29.10. (User: "text deutlich deutlicher"): fett, fast schwarz, groesseres Feld und eine helle Kante wie
            // eingemeisselter Stein, damit die Schrift sich vom grauen Stein abhebt
            t.fontStyle = TMPro.FontStyles.Bold;
            t.alignment = TMPro.TextAlignmentOptions.Center;
            t.enableWordWrapping = false;
            t.enableAutoSizing = true; t.fontSizeMin = 0.3f; t.fontSizeMax = 1.3f;
            t.lineSpacing = -12f;
            t.color = new Color32(22, 22, 28, 255);
            t.outlineWidth = 0.12f;
            t.outlineColor = new Color32(215, 215, 222, 200);
            t.rectTransform.sizeDelta = new Vector2(size.x * 0.29f / ppu, size.y * (owner ? 0.26f : 0.2f) / ppu);
            t.text = owner ? $"R.I.P.\n{name}\n<size=78%>still coding</size>" : $"R.I.P.\n{name}";
            var mr = t.GetComponent<MeshRenderer>();
            if (mr != null) { mr.sortingLayerID = _graveSr.sortingLayerID; mr.sortingOrder = _graveSr.sortingOrder + 1; }

            if (owner) ShowLaptop(At(GraveMoundAt, -0.002f), ppu);
            if (GraveMatches(p, GraveFishboneHashes) && _fishbonePetSprite != null)
            {
                // 28.10. (n58): kleiner und oben rechts auf dem Grabstein statt unten daneben
                var pet = GraveChild("GravePet", _fishbonePetSprite, At(new Vector2(0.86f, 0.74f), -0.003f), 3);
                pet.transform.localScale *= 0.6f;
                if (_fishbonePetMat != null) pet.sharedMaterial = _fishbonePetMat;
                _gravePet = pet.gameObject;
                _gravePetBase = pet.transform.localPosition;
                _gravePetScale = pet.transform.localScale;
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
            // froehlich: kleine Huepfer, ab und zu umdrehen; gestreichelt schneller und hoeher, mit Quetschen beim Landen
            bool joy = now < _petJoyUntil;
            float speed = joy ? 11f : 5f, s = Mathf.Sin(now * speed);
            float hop = Mathf.Abs(s) * (joy ? 0.22f : 0.12f);
            _gravePet.transform.localPosition = _gravePetBase + new Vector3(0f, hop, 0f);
            float squash = joy ? 1f - 0.18f * (1f - Mathf.Abs(s)) : 1f;
            _gravePet.transform.localScale = new Vector3(_gravePetScale.x * (2f - squash), _gravePetScale.y * squash, _gravePetScale.z);
            var sr = _gravePet.GetComponent<SpriteRenderer>();
            if (sr != null) sr.flipX = Mathf.Repeat(now, 6f) > 3f;
            PetHearts(now);
            // lebend daneben: streicheln
            var spot = (Vector2)_gravePet.transform.parent.TransformPoint(_gravePetBase);
            if (AtlasMaps.CanReach(spot, PetReach)) AtlasMaps.OfferUse("PET", "task_villa_btn_pet.png", PetGravePet);
        }
    }

    private void PetGravePet()
    {
        if (_gravePet == null) return;
        float now = Time.time;
        _petJoyUntil = now + PetJoy;
        for (int k = 0; k < 4; k++)
        {
            var go = new GameObject("GravePetHeart") { layer = _gravePet.layer };
            go.transform.SetParent(_gravePet.transform.parent, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = HeartSprite();
            var psr = _gravePet.GetComponent<SpriteRenderer>();
            if (psr != null) { sr.sortingLayerID = psr.sortingLayerID; sr.sortingOrder = psr.sortingOrder + 1; }
            _petHearts.Add((go, now + k * 0.25f, UnityEngine.Random.Range(-0.25f, 0.25f)));
            go.SetActive(false);
        }
        try { AtlasMaps.Sfx("chime", 0.5f); } catch { }
    }

    private void PetHearts(float now)
    {
        for (int i = _petHearts.Count - 1; i >= 0; i--)
        {
            var (go, born, dx) = _petHearts[i];
            if (go == null) { _petHearts.RemoveAt(i); continue; }
            float t = (now - born) / 1.4f;
            if (t < 0f) continue;
            if (t >= 1f) { UnityEngine.Object.Destroy(go); _petHearts.RemoveAt(i); continue; }
            if (!go.activeSelf) go.SetActive(true);
            // ueber dem Tier aufsteigen, leicht pendeln, groesser werden und verblassen (Welt-Einheiten ueber den Elternmassstab)
            var par = go.transform.parent;
            float ps = par != null ? Mathf.Max(0.001f, Mathf.Abs(par.lossyScale.x)) : 1f;
            var world = _gravePet.transform.parent.TransformPoint(_gravePetBase) + new Vector3(dx + Mathf.Sin(t * 9f + dx * 10f) * 0.08f, 0.45f + t * 0.9f, -0.01f);
            go.transform.position = world;
            float sc = (0.25f + 0.15f * t) / ps;
            go.transform.localScale = new Vector3(sc, sc, 1f);
            var sr = go.GetComponent<SpriteRenderer>();
            if (sr != null) sr.color = new Color(1f, 1f, 1f, 1f - t * t);
        }
    }

    // Herzkurve (u^2 + v^2 - 1)^3 - u^2 v^3 < 0 ist innen
    private static bool InHeart(float u, float v) => Mathf.Pow(u * u + v * v - 1f, 3f) - u * u * v * v * v < 0f;

    // kleines Herz, einmal gezeichnet (32 px, ein Welt-Meter bei Massstab 1)
    private static Sprite HeartSprite()
    {
        if (_heartSprite != null) return _heartSprite;
        const int N = 32;
        var tex = new Texture2D(N, N, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear };
        var px = new Color32[N * N];
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float u = (x + 0.5f) / N * 2.6f - 1.3f, v = (y + 0.5f) / N * 2.6f - 1.15f;
                px[y * N + x] = !InHeart(u, v) ? new Color32(0, 0, 0, 0)
                    : !InHeart(u / 0.8f, (v - 0.04f) / 0.8f) ? new Color32(120, 24, 48, 255)   // dunkle Kontur
                    : new Color32(240, 80, 115, 255);
            }
        tex.SetPixels32(px);
        tex.Apply(false, true);
        tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        _heartSprite = Sprite.Create(tex, new Rect(0, 0, N, N), new Vector2(0.5f, 0.5f), N);
        _heartSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        return _heartSprite;
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
