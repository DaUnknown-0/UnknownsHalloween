// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// TextureVersions - nur in Testversionen (vierstellige Version): F9 oeffnet ein Menue, in dem man die Grafik der
// Halloween-Karten zwischen Fassungen umschaltet, um alt und neu zu vergleichen, auch mitten in einer Runde.
//
// Fassungen stehen in TextureVariantCatalog.g.cs (tools/build_texture_variants.py). Die installierte kommt aus den
// normalen Paketen (HalloweenAssets), jede andere ist ein eigenes Paket (HWP1) mit denselben .atx-Namen, schon auf die
// AKTUELLE Atlas-Aufteilung umgepackt (Sprites alter Staende sitzen an den heutigen Rechtecken). Darum genuegt zur
// Laufzeit ein Kopieren auf der Grafikkarte: Graphics.CopyTexture schreibt die andere Fassung in die Texturen, die
// Atlas fuer die Karte schon geladen hat (AtlasAssets.MapTextures, per Reflection, Atlas bleibt unveraendert). Alle
// Sprites samt Tuer- und Vent-Animationen zeigen sofort die andere Grafik.
// Pakete laedt das Menue bei Bedarf nach BepInEx/halloween-assets/variants (mit Fortschrittsbalken); der Store raeumt
// nur Dateien im Hauptordner auf, der Unterordner bleibt. Die Wahl gilt bis zum Spielende; baut Atlas die Karte neu
// (naechste Runde), wendet Tick sie auf die frischen Texturen wieder an.

using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

namespace UnknownsHalloween;

internal static class TextureVersions
{
    private const string LogPrefix = "[Halloween/MapArt]";
    internal const KeyCode Hotkey = KeyCode.F9;
    private const string InstalledId = "installed";

    /// <summary>Nur Testversionen (System.Version.Revision > 0, also vierstellig).</summary>
    internal static bool Enabled => HalloweenPlugin.Version.Revision > 0;

    private static string Folder => Path.Combine(HalloweenAssets.Folder, "variants");
    private static string Source => HalloweenAssets.Source + "variants/";

    private static readonly Dictionary<string, string> Chosen = new();        // Karte -> Fassungs-Id
    private static readonly Dictionary<int, string> Applied = new();          // Textur-InstanceID -> Fassungs-Id
    private static readonly HashSet<string> Verified = new();                 // Pakete mit gepruefter Pruefsumme
    private static readonly HashSet<string> MismatchLogged = new();
    internal static bool Busy { get; private set; }
    internal static float Progress { get; private set; }
    internal static string Status { get; private set; } = "";
    private static FieldInfo _mapTextures;
    private static bool _reflected;
    private static MonoBehaviour _host;

    private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");
    private static void Warn(string s) => HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {s}");

    internal static IEnumerable<(string Map, string Id, string LabelEn, string LabelDe, string File, long Size, string Sha256)> Of(string map) =>
        TextureVariantCatalog.Variants.Where(v => v.Map == map);

    internal static string ChosenId(string map) => Chosen.TryGetValue(map, out var id) ? id : InstalledId;

    /// <summary>Aus HalloweenAssetHost.Update: Taste, Menue, erneutes Anwenden nach einem Kartenneubau.</summary>
    internal static void Tick(MonoBehaviour host)
    {
        if (!Enabled) return;
        _host = host;
        if (Input.GetKeyDown(Hotkey)) TextureVersionsMenu.Toggle();
        TextureVersionsMenu.Tick();
        if (Diag.Contains("maptour")) TourTick();
        else if (Diag.Contains("mapart")) DiagTick();
        if (Busy || Time.frameCount % 30 != 0) return;
        foreach (var (map, id) in Chosen.ToList())
        {
            // frisch geladene Texturen (neue Runde) zeigen die installierte Fassung und stehen nicht in Applied
            if (LiveTextures(map).Any(t => (Applied.TryGetValue(t.Tex.GetInstanceID(), out var a) ? a : InstalledId) != id))
            {
                var v = Of(map).FirstOrDefault(x => x.Id == id);
                if (v.Id != null && (v.File == null || PackageReady(v.File, v.Size))) Choose(map, id);
            }
        }
    }

    /// <summary>Fassung waehlen: Paket bei Bedarf laden, dann auf die geladenen Kartentexturen anwenden.</summary>
    internal static void Choose(string map, string id)
    {
        if (Busy || _host == null) return;
        var v = Of(map).FirstOrDefault(x => x.Id == id);
        if (v.Id == null) return;
        Chosen[map] = id;
        BepInEx.Unity.IL2CPP.Utils.MonoBehaviourExtensions.StartCoroutine(_host, Run(v));
    }

    internal static bool PackageReady(string file, long size)
    {
        try { var fi = new FileInfo(Path.Combine(Folder, file)); return fi.Exists && fi.Length == size; }
        catch { return false; }
    }

    // ------------------------------------------------------------------ Ablauf

    private static IEnumerator Run((string Map, string Id, string LabelEn, string LabelDe, string File, long Size, string Sha256) v)
    {
        Busy = true;
        Progress = 0f;
        Dictionary<string, (long Off, int Len)> index = null;
        string pkg = null;
        if (v.File != null)
        {
            pkg = Path.Combine(Folder, v.File);
            if (!PackageReady(v.File, v.Size))
            {
                var dl = Download(v.File, v.Size, v.Sha256);
                while (dl.MoveNext()) yield return dl.Current;
                if (!PackageReady(v.File, v.Size)) { Busy = false; yield break; }
            }
            if (!Verified.Contains(v.File))
            {
                Status = De("Pruefe Paket ...", "Checking package ...");
                var check = Task.Run(() => Sha(pkg) == v.Sha256);
                while (!check.IsCompleted) yield return null;
                if (check.IsFaulted || !check.Result)
                {
                    Status = De("Paket beschaedigt, wird neu geladen", "Package damaged, loading it again");
                    try { File.Delete(pkg); } catch { }
                    Busy = false;
                    yield break;
                }
                Verified.Add(v.File);
            }
            index = ReadIndex(pkg);
            if (index == null) { Status = De("Paket unlesbar", "Package unreadable"); Busy = false; yield break; }
        }

        var live = LiveTextures(v.Map);
        if (live.Count == 0)
        {
            Status = De("Gewaehlt, wirkt sobald die Karte geladen ist", "Chosen, applies once the map is loaded");
            Progress = 1f;
            Busy = false;
            yield break;
        }
        int done = 0, copied = 0;
        foreach (var (atx, tex) in live)
        {
            Status = De($"Wende an {done + 1} / {live.Count}", $"Applying {done + 1} / {live.Count}");
            byte[] raw = null;
            string res = HalloweenAssets.ResRoot + atx;
            var read = Task.Run(() => pkg != null ? ReadEntry(pkg, index, atx) : HalloweenAssets.Read(res));
            while (!read.IsCompleted) yield return null;
            if (!read.IsFaulted) raw = read.Result;
            var decode = Task.Run(() => Decode(raw));
            while (!decode.IsCompleted) yield return null;
            var p = decode.IsFaulted ? null : decode.Result;
            if (tex != null && p != null && Copy(p, tex)) { Applied[tex.GetInstanceID()] = v.Id; copied++; }
            else if (tex != null && MismatchLogged.Add(v.Id + atx))
                Warn($"{atx}: {(p == null ? "missing in this version" : $"{p.Width}x{p.Height} {p.Format}/{p.Mips} vs {tex.width}x{tex.height} {tex.format}/{tex.mipmapCount}")}, kept");
            done++;
            Progress = done / (float)live.Count;
            yield return null;
        }
        Log($"{v.Map}: {v.Id} applied to {copied} of {live.Count} textures");
        Status = De($"{v.LabelDe} aktiv", $"{v.LabelEn} active");
        Busy = false;
    }

    private static IEnumerator Download(string file, long size, string sha)
    {
        Directory.CreateDirectory(Folder);
        var www = new UnityWebRequest();
        www.SetMethod(UnityWebRequest.UnityWebRequestMethod.Get);
        www.SetUrl(Source + Uri.EscapeDataString(file));
        www.SetRequestHeader("User-Agent", $"UnknownsHalloween/{HalloweenPlugin.PluginVersion}");
        www.downloadHandler = new DownloadHandlerBuffer();
        www.timeout = 300;
        var op = www.SendWebRequest();
        while (!op.isDone)
        {
            float got = www.downloadProgress * size;
            Progress = Mathf.Clamp01(www.downloadProgress) * 0.9f;
            Status = De($"Lade {got / 1048576f:F1} / {size / 1048576f:F1} MB", $"Downloading {got / 1048576f:F1} / {size / 1048576f:F1} MB");
            yield return null;
        }
        string error = null;
        byte[] data = null;
        if (www.isNetworkError || www.isHttpError) error = www.responseCode > 0 ? $"HTTP {www.responseCode}" : www.error ?? "network error";
        else data = www.downloadHandler.data;
        www.downloadHandler.Dispose();
        www.Dispose();
        if (error == null)
        {
            Status = De("Pruefe Paket ...", "Checking package ...");
            var store = Task.Run(() =>
            {
                if (data == null || data.Length != size) return $"size {data?.Length ?? 0} instead of {size}";
                string got;
                using (var s = SHA256.Create()) got = Convert.ToHexString(s.ComputeHash(data)).ToLowerInvariant();
                if (got != sha) return "checksum does not match";
                string path = Path.Combine(Folder, file), tmp = path + ".part";
                File.WriteAllBytes(tmp, data);
                File.Move(tmp, path, true);
                return null;
            });
            while (!store.IsCompleted) yield return null;
            error = store.IsFaulted ? store.Exception?.GetBaseException().Message : store.Result;
            if (error == null) Verified.Add(file);
        }
        if (error != null)
        {
            Warn($"{file}: download failed ({error})");
            Status = De($"Download fehlgeschlagen ({error})", $"Download failed ({error})");
        }
    }

    // ------------------------------------------------------------------ Texturen

    /// <summary>Die von Atlas fuer die Karte geladenen Atlanten und Bodenkacheln, mit dem .atx-Namen der Fassung.</summary>
    internal static List<(string Atx, Texture2D Tex)> LiveTextures(string map)
    {
        var list = new List<(string, Texture2D)>();
        var dict = MapTextures();
        if (dict == null) return list;
        string prefix = HalloweenAssets.ResRoot;   // Villa-Ressourcen liegen ohne Ordnerpraefix ("...Resources.villa_props_0.png")
        foreach (var kv in dict)
        {
            if (kv.Value == null || !kv.Key.StartsWith(prefix, StringComparison.Ordinal)) continue;
            string file = kv.Key.Substring(prefix.Length);
            int dot = file.LastIndexOf('.');
            string stem = dot > 0 ? file.Substring(0, dot) : file;
            if (!stem.StartsWith(map + "_props_") && !stem.StartsWith(map + "_consoles_") && !stem.StartsWith(map + "_floor_")) continue;
            list.Add((stem + ".atx", kv.Value));
        }
        return list.OrderBy(t => t.Item1, StringComparer.Ordinal).ToList();
    }

    private static Dictionary<string, Texture2D> MapTextures()
    {
        if (!_reflected)
        {
            _reflected = true;
            try
            {
                var t = Type.GetType("UnknownsAtlas.AtlasAssets, UnknownsAtlas");
                _mapTextures = t?.GetField("MapTextures", BindingFlags.NonPublic | BindingFlags.Static);
                if (_mapTextures == null) Warn("Unknown's Atlas texture cache not found, map art versions are off");
            }
            catch (Exception e) { Warn($"reflection failed: {e.Message}"); }
        }
        try { return _mapTextures?.GetValue(null) as Dictionary<string, Texture2D>; }
        catch { return null; }
    }

    private sealed class Packed { public int Width, Height, Mips; public TextureFormat Format; public byte[] Data; }

    /// <summary>.atx (siehe UnknownsAtlas AtlasTexturePack): 28 Byte Kopf, dann die DXT-Mip-Kette, raw Deflate.</summary>
    private static Packed Decode(byte[] atx)
    {
        if (atx == null || atx.Length < 28 || atx[0] != 'A' || atx[1] != 'T' || atx[2] != 'X' || atx[3] != '1' || atx[5] != 1) return null;
        var fmt = (TextureFormat)atx[4];
        int w = BitConverter.ToInt32(atx, 8), h = BitConverter.ToInt32(atx, 12), mips = BitConverter.ToInt32(atx, 16), raw = BitConverter.ToInt32(atx, 20);
        if (w <= 0 || h <= 0 || mips <= 0 || raw <= 0) return null;
        var data = new byte[raw];
        using (var z = new DeflateStream(new MemoryStream(atx, 28, atx.Length - 28), CompressionMode.Decompress))
        {
            int read = 0;
            while (read < raw) { int n = z.Read(data, read, raw - read); if (n <= 0) return null; read += n; }
        }
        return new Packed { Width = w, Height = h, Mips = mips, Format = fmt, Data = data };
    }

    /// <summary>Hauptthread: Zwischentextur hochladen und auf der GPU in die Kartentextur kopieren.</summary>
    private static bool Copy(Packed p, Texture2D dst)
    {
        if (p.Width != dst.width || p.Height != dst.height || p.Format != dst.format || p.Mips != dst.mipmapCount) return false;
        if (SystemInfo.copyTextureSupport == UnityEngine.Rendering.CopyTextureSupport.None) return false;
        Texture2D tmp = null;
        try
        {
            tmp = new Texture2D(p.Width, p.Height, p.Format, p.Mips, false);
            var pin = GCHandle.Alloc(p.Data, GCHandleType.Pinned);
            try { tmp.LoadRawTextureData(pin.AddrOfPinnedObject(), p.Data.Length); }
            finally { pin.Free(); }
            tmp.Apply(false, false);
            Graphics.CopyTexture(tmp, dst);
            return true;
        }
        catch (Exception e) { Warn($"copy failed: {e.Message}"); return false; }
        finally { if (tmp != null) UnityEngine.Object.Destroy(tmp); }
    }

    // ------------------------------------------------------------------ Pakete (HWP1, wie HalloweenAssets)

    private static Dictionary<string, (long Off, int Len)> ReadIndex(string path)
    {
        try
        {
            long size = new FileInfo(path).Length;
            using var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
            using var br = new BinaryReader(fs, Encoding.UTF8);
            if (Encoding.ASCII.GetString(br.ReadBytes(4)) != "HWP1") return null;
            int count = br.ReadInt32();
            var map = new Dictionary<string, (long, int)>(count, StringComparer.Ordinal);
            for (int i = 0; i < count; i++)
            {
                string name = Encoding.UTF8.GetString(br.ReadBytes(br.ReadUInt16()));
                long off = (long)br.ReadUInt64();
                int len = (int)br.ReadUInt32();
                if (off < 0 || off + len > size) return null;
                map[name] = (off, len);
            }
            return map;
        }
        catch { return null; }
    }

    /// <summary>Eintrag "villa_props_0.atx" (Namen wie im Store, Villa ohne Ordnerpraefix).</summary>
    private static byte[] ReadEntry(string path, Dictionary<string, (long Off, int Len)> index, string atx)
    {
        if (index == null) return null;
        (long Off, int Len) at = default;
        bool found = index.TryGetValue(atx, out at);
        if (!found) foreach (var kv in index) if (kv.Key.EndsWith("." + atx, StringComparison.Ordinal) || kv.Key.EndsWith("/" + atx, StringComparison.Ordinal)) { at = kv.Value; found = true; break; }
        if (!found) return null;
        using var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        fs.Seek(at.Off, SeekOrigin.Begin);
        var data = new byte[at.Len];
        int read = 0;
        while (read < at.Len) { int n = fs.Read(data, read, at.Len - read); if (n <= 0) return null; read += n; }
        return data;
    }

    private static string Sha(string path)
    {
        using var s = SHA256.Create();
        using var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        return Convert.ToHexString(s.ComputeHash(fs)).ToLowerInvariant();
    }

    internal static string De(string de, string en) => TrickOrTreat.De() ? de : en;

    // ------------------------------------------------------------------ Selbsttest (UC_HALLOWEEN_DIAG=mapart)
    // 30 s nach dem Laden der Villa jede Fassung anwenden und fotografieren (AtlasShots/mapart_<i>_<id>.png), dann das
    // Menue offen fotografieren, zurueck auf die installierte Fassung, "diag: all done" fuer das Testskript.
    private static readonly string Diag = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
    private static float _diagSeen = -1f, _diagNext;
    private static int _diagStep;

    // Rundgang (UC_HALLOWEEN_DIAG=villalarge,maptour): Spieler vor jedes Objekt setzen, je Fassung aus MAPTOUR_IDS
    // (Standard "qwen,vorqwen") ein Foto AtlasShots/tour_<n>_<id>.png. Orte: Konsolen-Schluessel oder "x/y".
    private static readonly string[] TourSpots =
        (Environment.GetEnvironmentVariable("UC_HALLOWEEN_MAPTOUR") ?? "Weapons/WeaponConsole/0;Nav/ChartCourseConsole/0;Reactor/UnlockManifoldsConsole/2;27.3/-7.45")
        .Split(';', StringSplitOptions.RemoveEmptyEntries);
    private static readonly string[] TourIds = (Environment.GetEnvironmentVariable("UC_HALLOWEEN_MAPTOUR_IDS") ?? "qwen,vorqwen").Split(',');

    private static void TourTick()
    {
        float now = Time.realtimeSinceStartup;
        if (_diagStep < 0 || Busy || now < _diagNext) return;
        if (LiveTextures(HollowmereMap.Key).Count == 0) return;
        if (_diagSeen < 0f) { _diagSeen = now; _diagNext = now + 30f; return; }
        string shots = Path.Combine(BepInEx.Paths.GameRootPath, "AtlasShots");
        Directory.CreateDirectory(shots);
        int per = 1 + 2 * TourIds.Length, spot = _diagStep / per, k = _diagStep % per;
        if (spot >= TourSpots.Length)
        {
            Choose(HollowmereMap.Key, InstalledId);
            HalloweenPlugin.Logger?.LogInfo("[Halloween/Villa] diag: all done (maptour)");
            _diagStep = -2;
            return;
        }
        if (k == 0)
        {
            Vector2 at;
            string s = TourSpots[spot];
            var parts = s.Split('/');
            if (parts.Length == 2 && float.TryParse(parts[0], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float x)
                && float.TryParse(parts[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float y)) at = new Vector2(x, y);
            else if (VillaLarge.Consoles.TryGetValue(s, out var c)) at = c;
            else { Warn($"diag: spot {s} unknown"); _diagStep += per; return; }
            try { PlayerControl.LocalPlayer.NetTransform.RpcSnapTo(at + new Vector2(0f, -1.3f)); } catch (Exception e) { Warn($"diag: snap failed {e.Message}"); }
            Log($"diag: tour spot {spot} {s} at {at}");
            _diagNext = now + 1.5f;
        }
        else if (k % 2 == 1) { Choose(HollowmereMap.Key, TourIds[(k - 1) / 2]); _diagNext = now + 1.5f; }
        else { ScreenCapture.CaptureScreenshot(Path.Combine(shots, $"tour_{spot}_{TourIds[(k - 2) / 2]}.png")); _diagNext = now + 1.2f; }
        _diagStep++;
    }

    private static void DiagTick()
    {
        float now = Time.realtimeSinceStartup;
        if (_diagStep < 0 || Busy || now < _diagNext) return;
        if (LiveTextures(HollowmereMap.Key).Count == 0) return;
        if (_diagSeen < 0f) { _diagSeen = now; _diagNext = now + 30f; return; }
        var vs = Of(HollowmereMap.Key).ToList();
        string shots = Path.Combine(BepInEx.Paths.GameRootPath, "AtlasShots");
        Directory.CreateDirectory(shots);
        int i = _diagStep / 2;
        if (i < vs.Count)
        {
            if (_diagStep % 2 == 0) { Log($"diag: applying {vs[i].Id}"); Choose(HollowmereMap.Key, vs[i].Id); _diagNext = now + 1.5f; }
            else { ScreenCapture.CaptureScreenshot(Path.Combine(shots, $"mapart_{i}_{vs[i].Id}.png")); Log($"diag: shot {vs[i].Id} ({Status})"); _diagNext = now + 1.5f; }
            _diagStep++;
            return;
        }
        switch (_diagStep - 2 * vs.Count)
        {
            case 0: TextureVersionsMenu.Open(); _diagNext = now + 1.5f; break;
            case 1: ScreenCapture.CaptureScreenshot(Path.Combine(shots, "mapart_menu.png")); _diagNext = now + 1.5f; break;
            case 2: TextureVersionsMenu.Close(); Choose(HollowmereMap.Key, InstalledId); _diagNext = now + 3f; break;
            default:
                HalloweenPlugin.Logger?.LogInfo("[Halloween/Villa] diag: all done (mapart)");
                _diagStep = -2;
                return;
        }
        _diagStep++;
    }
}

/// <summary>Das F9-Menue: Fassungen der aktuellen (oder zuletzt gespielten) Halloween-Karte, Fortschrittsbalken.</summary>
internal static class TextureVersionsMenu
{
    private static GameObject root;
    private static RectTransform fill;
    private static TMPro.TextMeshProUGUI status;
    private static string builtFor = "";
    private const float W = 980f, Pad = 34f, Row = 78f;
    private static readonly Color Accent = new Color(0.55f, 0.42f, 0.82f);

    internal static void Toggle() { if (root != null) Close(); else Open(); }
    internal static void Close() { if (root != null) UnityEngine.Object.Destroy(root); root = null; fill = null; status = null; }

    private static string D(string de, string en) => TextureVersions.De(de, en);

    internal static void Open()
    {
        try
        {
            Close();
            const string map = HollowmereMap.Key;
            var variants = TextureVersions.Of(map).ToList();
            float h = 205f + variants.Count * Row + 85f;
            root = HalloweenUI.Canvas("MapArtVersions", 9600, true);
            HalloweenUI.Backdrop(root, Close);
            var card = HalloweenUI.CenterPanel(root, new Vector2(W, h));
            float y = HalloweenUI.Title(card, D("Kartengrafik", "Map art"), 16f, 34f, Accent);
            HalloweenUI.CloseButton(card, "", Close);
            HalloweenUI.Text(card, D("Testversion: Fassungen von Hollowmere Manor vergleichen. Wirkt sofort, auch mitten in der Runde, und nur bei dir. F9 schliesst.",
                                     "Test version: compare versions of Hollowmere Manor. Applies at once, even mid-round, and only for you. F9 closes."),
                20f, HalloweenUI.Muted, new Vector2(Pad, y - 6f), new Vector2(W - 2 * Pad, 70f));
            y -= 92f;
            string chosen = TextureVersions.ChosenId(map);
            foreach (var v in variants)
            {
                bool on = v.Id == chosen;
                string label = TrickOrTreat.De() ? v.LabelDe : v.LabelEn;
                string id = v.Id;
                HalloweenUI.Button(card, label, new Vector2(Pad, y), new Vector2(620f, Row - 16f), on ? HalloweenUI.Teal : HalloweenUI.Grey,
                    () => { TextureVersions.Choose(map, id); Rebuild(); }, out _, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), 26f);
                string state = v.File == null ? D("installiert", "installed")
                    : TextureVersions.PackageReady(v.File, v.Size) ? D("geladen", "downloaded")
                    : D($"{v.Size / 1048576f:F1} MB laden", $"{v.Size / 1048576f:F1} MB download");
                HalloweenUI.Text(card, (on ? D("aktiv  ·  ", "active  ·  ") : "") + state, 20f, on ? HalloweenUI.Good : HalloweenUI.Muted,
                    new Vector2(Pad + 650f, y - 18f), new Vector2(W - 2 * Pad - 650f, 40f));
                y -= Row;
            }
            y -= 10f;
            var bar = HalloweenUI.Rounded(card, HalloweenUI.Field, 8);
            var brt = HalloweenUI.Rect(bar, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1));
            brt.anchoredPosition = new Vector2(Pad, y); brt.sizeDelta = new Vector2(W - 2 * Pad, 22f);
            var f = HalloweenUI.Rounded(bar, Accent, 8);
            fill = HalloweenUI.Rect(f, new Vector2(0, 0), new Vector2(0, 1), new Vector2(0, 0.5f));
            fill.anchoredPosition = Vector2.zero; fill.sizeDelta = new Vector2(0f, 0f);
            status = HalloweenUI.Text(card, "", 20f, HalloweenUI.TextColor, new Vector2(Pad, y - 32f), new Vector2(W - 2 * Pad, 34f));
            builtFor = chosen + TextureVersions.Busy;
            Tick();
        }
        catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Halloween/MapArt] menu failed: {e}"); Close(); }
    }

    private static void Rebuild() { if (root != null) Open(); }

    internal static void Tick()
    {
        if (root == null) return;
        if (Input.GetKeyDown(KeyCode.Escape)) { Close(); return; }
        string key = TextureVersions.ChosenId(HollowmereMap.Key) + TextureVersions.Busy;
        if (key != builtFor) { Rebuild(); return; }
        if (fill != null)
        {
            float wmax = W - 2 * Pad;
            float p = TextureVersions.Busy || TextureVersions.Progress > 0f ? TextureVersions.Progress : 0f;
            fill.sizeDelta = new Vector2(Mathf.Max(0f, wmax * p), 0f);
        }
        if (status != null) HalloweenUI.SetText(status, TextureVersions.Status);
    }
}
