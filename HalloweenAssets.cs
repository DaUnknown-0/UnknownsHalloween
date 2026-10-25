// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HalloweenAssets - die grossen Bilder kommen aus dem Asset-Repo statt aus der DLL (Muster: Atlas' AtlasAssetStore).
//
// Kostuem-, Kill- und Spinnenbein-Bilder sowie Boden, Objekte, Konsolen, Minispiele, Vorspann und Rauswurf von
// Hollowmere Manor und Ravenhollow Cemetery liegen in Paketen (.hwp, Liste in HalloweenAssetCatalog.g.cs, erzeugt von
// tools/build_assets_repo.py) im Ordner BepInEx/halloween-assets. Ablauf:
//   - Start (aus Load, vor PatchAll): Pakete, deren Groesse und Zeitstempel zum zuletzt bestaetigten Stand passen
//     (verified.txt), gelten sofort als da; damit stehen Kostueme und Karten beim normalen Start ohne Warten bereit.
//     Danach prueft ein Hintergrund-Task jedes Paket voll (SHA-256); was fehlt oder abweicht, wird geladen.
//   - Download: raw.githubusercontent.com am Katalog-Tag, anonym (klappt, sobald das Repo oeffentlich ist), im
//     Hintergrund, vier gleichzeitig, Wiederholung mit Pause. Antwortet das Repo mit 401/403/404 (privat oder noch
//     nicht angelegt), schreibt der Store EINE Zeile ins Log und versucht es erst beim naechsten Start wieder; die
//     Mod laeuft dann ohne Kostueme und ohne die beiden Karten.
//   - Wer etwas braucht, fragt Ready("hats_") usw. oder meldet sich mit WhenReady an (Kostueme, Karten melden sich
//     dann nachtraeglich an, sobald ihre Pakete da sind).
//   - Aufraeumen: sind alle Pakete bestaetigt, loescht der Store im eigenen Ordner alles, was nicht zum Katalog
//     gehoert (alte Pakete, Fremddateien); halbe Downloads (.part) beim Start. Nie ausserhalb des Ordners.
// Lesen: Open/Read/Exists nehmen den Ressourcennamen ("UnknownsHalloween.Resources.hats.hw_freddy_1.png"); zuerst
// die DLL, dann die bestaetigten Pakete. ResourceAssembly verpackt das fuer Atlas (AtlasMapDef.ResourceAssembly).
//
// Paketformat HWP1: "HWP1", uint32 Anzahl, je Eintrag uint16 Namenslaenge, Name (UTF-8, ohne
// "UnknownsHalloween.Resources."), uint64 Offset, uint32 Laenge; danach die Dateien hintereinander.

using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;

namespace UnknownsHalloween;

internal static class HalloweenAssets
{
    private const string LogPrefix = "[Halloween/Assets]";
    internal const string ResRoot = "UnknownsHalloween.Resources.";
    internal const string DefaultSourceBase = "https://raw.githubusercontent.com/DaUnknown-0/UnknownsHalloween-Assets/";
    private const string StampFile = "verified.txt";
    private const int Parallel = 4;
    private const int MaxTries = 3;
    private static readonly float[] Backoff = { 0f, 15f, 60f };

    internal static string Folder => Path.Combine(BepInEx.Paths.BepInExRootPath, "halloween-assets");
    internal static string Source { get; private set; } = DefaultSourceBase + HalloweenAssetCatalog.Tag + "/files/";

    /// <summary>DLL plus Pakete als "Assembly" fuer Atlas (Kartenpaket, Knoepfe, Minispielbilder).</summary>
    internal static readonly Assembly ResourceAssembly = new HalloweenResourceAssembly();
    private static readonly Assembly Own = typeof(HalloweenAssets).Assembly;

    private sealed class Entry
    {
        public string Name, Sha256;
        public long Size;
        public long OkLength, OkTicks;                   // bestaetigter Stand; 0 = nicht bestaetigt
        public long StatAt;                              // Environment.TickCount64 der letzten Pruefung am Ort
        public Dictionary<string, (long Off, int Len)> Index;
        public int Tries;
        public float RetryAt;
    }

    private static readonly Entry[] Entries = HalloweenAssetCatalog.Files
        .Select(f => new Entry { Name = f.Name, Size = f.Size, Sha256 = f.Sha256 }).ToArray();
    private static readonly Dictionary<string, Entry> ByName = Entries.ToDictionary(e => e.Name, StringComparer.OrdinalIgnoreCase);
    private static readonly object Gate = new();
    private static readonly List<string> Queue = new();
    private static readonly List<(string Prefix, Action Run)> Waiting = new();
    private static MonoBehaviour _host;
    private static volatile bool _saving;
    private static bool _verifying, _verified, _unavailable, _stampsDirty, _cleaned, _gaveUpLogged;
    private static int _active, _loaded;

    private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");
    private static void Warn(string s) => HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {s}");

    internal static int Total => Entries.Length;
    internal static int ReadyCount { get { lock (Gate) return Entries.Count(e => e.OkLength > 0); } }

    /// <summary>Alle Pakete, deren Name mit prefix beginnt ("hats_", "villa_", "graveyard_"), bestaetigt?</summary>
    internal static bool Ready(string prefix)
    {
        lock (Gate)
            return Entries.Where(e => e.Name.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)).All(e => e.OkLength > 0);
    }

    /// <summary>action sofort ausfuehren, wenn die Pakete da sind, sonst (im Hauptthread) sobald sie da sind.</summary>
    internal static void WhenReady(string prefix, Action action)
    {
        if (Ready(prefix)) { Run(prefix, action); return; }
        lock (Waiting) Waiting.Add((prefix, action));
    }

    private static void Run(string prefix, Action a)
    {
        try { a(); } catch (Exception e) { HalloweenPlugin.Logger?.LogError($"{LogPrefix} start of {prefix}* content failed: {e}"); }
    }

    // ------------------------------------------------------------------ Lesen

    /// <summary>Stream einer Ressource: eingebettet, sonst aus einem bestaetigten Paket, sonst null.</summary>
    internal static Stream Open(string res)
    {
        var s = Own.GetManifestResourceStream(res);
        if (s != null) return s;
        var data = ReadPacked(res);
        return data == null ? null : new MemoryStream(data, false);
    }

    /// <summary>Bytes einer Ressource (eingebettet oder aus einem Paket), sonst null.</summary>
    internal static byte[] Read(string res)
    {
        using (var s = Own.GetManifestResourceStream(res))
            if (s != null)
            {
                var data = new byte[s.Length];
                int read = 0;
                while (read < data.Length) { int n = s.Read(data, read, data.Length - read); if (n <= 0) break; read += n; }
                return read == data.Length ? data : null;
            }
        return ReadPacked(res);
    }

    internal static bool Exists(string res)
    {
        try { if (Own.GetManifestResourceInfo(res) != null) return true; } catch { }
        return Locate(res, out _, out _) != null;
    }

    internal static IEnumerable<string> PackedNames()
    {
        lock (Gate)
            return Entries.Where(e => e.OkLength > 0 && e.Index != null).SelectMany(e => e.Index.Keys).Select(k => ResRoot + k).ToList();
    }

    private static Entry Locate(string res, out long off, out int len)
    {
        off = 0; len = 0;
        if (res == null || !res.StartsWith(ResRoot, StringComparison.Ordinal)) return null;
        string key = res.Substring(ResRoot.Length);
        lock (Gate)
            foreach (var e in Entries)
                if (e.OkLength > 0 && e.Index != null && e.Index.TryGetValue(key, out var at)) { off = at.Off; len = at.Len; return e; }
        return null;
    }

    private static byte[] ReadPacked(string res)
    {
        var e = Locate(res, out long off, out int len);
        if (e == null || !Confirmed(e)) return null;
        try
        {
            using var fs = new FileStream(PathOf(e.Name), FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
            fs.Seek(off, SeekOrigin.Begin);
            var data = new byte[len];
            int read = 0;
            while (read < len) { int n = fs.Read(data, read, len - read); if (n <= 0) break; read += n; }
            return read == len ? data : null;
        }
        catch { return null; }
    }

    private static string PathOf(string file) => Path.Combine(Folder, file);

    /// <summary>Bestaetigt und seitdem am Ort unveraendert (Groesse + Zeitstempel, hoechstens einmal pro Sekunde gestat).</summary>
    private static bool Confirmed(Entry e)
    {
        long now = Environment.TickCount64;
        lock (Gate)
        {
            if (e.OkLength == 0) return false;
            if (now - e.StatAt < 1000) return true;
        }
        try
        {
            var fi = new FileInfo(PathOf(e.Name));
            if (fi.Exists && fi.Length == e.OkLength && fi.LastWriteTimeUtc.Ticks == e.OkTicks) { lock (Gate) e.StatAt = now; return true; }
        }
        catch { }
        lock (Gate) { e.OkLength = 0; e.Index = null; }
        lock (Queue) if (!_unavailable && !Queue.Contains(e.Name)) Queue.Add(e.Name);
        Warn($"{e.Name} changed on disk, loading it again");
        return false;
    }

    /// <summary>Inhaltsverzeichnis eines Pakets lesen (ohne Unity-Aufrufe). null bei kaputtem Paket.</summary>
    private static Dictionary<string, (long, int)> ReadIndex(string path, long size)
    {
        try
        {
            using var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
            using var br = new BinaryReader(fs, Encoding.UTF8);
            if (Encoding.ASCII.GetString(br.ReadBytes(4)) != "HWP1") return null;
            int count = br.ReadInt32();
            var map = new Dictionary<string, (long, int)>(count, StringComparer.Ordinal);
            for (int i = 0; i < count; i++)
            {
                int n = br.ReadUInt16();
                string name = Encoding.UTF8.GetString(br.ReadBytes(n));
                long off = (long)br.ReadUInt64();
                int len = (int)br.ReadUInt32();
                if (off < 0 || off + len > size) return null;
                map[name] = (off, len);
            }
            return map;
        }
        catch { return null; }
    }

    // ------------------------------------------------------------------ Start und Pruefen

    /// <summary>Aus HalloweenPlugin.Load (vor PatchAll): Quelle, Altlasten, schnelle Bestaetigung, Hintergrundpruefung.</summary>
    internal static void Start(MonoBehaviour host, string sourceOverride)
    {
        _host = host;
        string s = sourceOverride?.Trim();
        if (!string.IsNullOrEmpty(s))
        {
            if (!s.EndsWith("/")) s += "/";
            if (s.StartsWith(DefaultSourceBase, StringComparison.Ordinal) || s.StartsWith("http://127.0.0.1:", StringComparison.Ordinal))
                Source = s;
            else Warn($"download source '{s}' ignored (only the asset repository or a local test server)");
        }
        try
        {
            Directory.CreateDirectory(Folder);
            foreach (var part in Directory.GetFiles(Folder, "*.part"))
                try { File.Delete(part); } catch { }
        }
        catch (Exception e) { Warn($"folder: {e.Message}"); }
        int quick = TrustStamps();
        Log($"{quick}/{Total} packages ready from the last check ({Folder})");
        VerifyAll();
    }

    /// <summary>Pakete, deren Datei genau dem zuletzt bestaetigten Stand entspricht, sofort freigeben.</summary>
    private static int TrustStamps()
    {
        int n = 0;
        try
        {
            string path = PathOf(StampFile);
            if (!File.Exists(path)) return 0;
            foreach (var line in File.ReadAllLines(path))
            {
                var p = line.Split('\t');
                if (p.Length != 4 || !ByName.TryGetValue(p[0], out var e) || p[3] != e.Sha256) continue;
                if (!long.TryParse(p[1], out long len) || !long.TryParse(p[2], out long ticks) || len != e.Size) continue;
                var fi = new FileInfo(PathOf(e.Name));
                if (!fi.Exists || fi.Length != len || fi.LastWriteTimeUtc.Ticks != ticks) continue;
                var idx = ReadIndex(fi.FullName, len);
                if (idx == null) continue;
                lock (Gate) { e.OkLength = len; e.OkTicks = ticks; e.Index = idx; e.StatAt = Environment.TickCount64; }
                n++;
            }
        }
        catch (Exception ex) { Warn($"{StampFile} unreadable ({ex.Message}), checking everything"); }
        return n;
    }

    private static void SaveStamps()
    {
        try
        {
            List<string> lines;
            lock (Gate) lines = Entries.Where(e => e.OkLength > 0).Select(e => $"{e.Name}\t{e.OkLength}\t{e.OkTicks}\t{e.Sha256}").ToList();
            string path = PathOf(StampFile), tmp = path + ".part";
            File.WriteAllLines(tmp, lines);
            File.Move(tmp, path, true);
        }
        catch { }
    }

    private static void VerifyAll()
    {
        if (_verifying) return;
        _verifying = true;
        Task.Run(() =>
        {
            var sw = System.Diagnostics.Stopwatch.StartNew();
            var bad = Entries.Where(e => !Check(e)).Select(e => e.Name).ToList();
            return (bad, sw.ElapsedMilliseconds);
        }).ContinueWith(t =>
        {
            _verifying = false;
            _verified = true;
            _stampsDirty = true;
            if (t.IsFaulted) { Warn($"check failed: {t.Exception?.GetBaseException().Message}"); return; }
            var (bad, ms) = t.Result;
            if (bad.Count == 0) Log($"all {Total} packages present and verified ({ms} ms)");
            else
            {
                Log($"{Total - bad.Count}/{Total} packages verified, {bad.Count} missing or changed ({ms} ms), loading from {Source}");
                lock (Queue) foreach (var n in bad) if (!Queue.Contains(n)) Queue.Add(n);
            }
        });
    }

    /// <summary>Ein Paket voll pruefen (Groesse, SHA-256, Inhaltsverzeichnis). Hintergrund.</summary>
    private static bool Check(Entry e)
    {
        try
        {
            var fi = new FileInfo(PathOf(e.Name));
            if (!fi.Exists || fi.Length != e.Size) { Unconfirm(e); return false; }
            string hash;
            using (var fs = new FileStream(fi.FullName, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
            using (var sha = SHA256.Create())
                hash = Convert.ToHexString(sha.ComputeHash(fs)).ToLowerInvariant();
            if (hash != e.Sha256) { Unconfirm(e); return false; }
            var idx = ReadIndex(fi.FullName, fi.Length);
            if (idx == null) { Unconfirm(e); return false; }
            fi.Refresh();
            lock (Gate) { e.OkLength = fi.Length; e.OkTicks = fi.LastWriteTimeUtc.Ticks; e.Index = idx; e.StatAt = Environment.TickCount64; }
            return true;
        }
        catch { Unconfirm(e); return false; }
    }

    private static void Unconfirm(Entry e) { lock (Gate) { e.OkLength = 0; e.Index = null; } }

    // ------------------------------------------------------------------ Takt (Hauptthread)

    internal static void Tick()
    {
        if (_host == null) return;
        if (_stampsDirty && _active == 0 && !_saving)
        {
            _stampsDirty = false;
            _saving = true;
            Task.Run(() => { SaveStamps(); _saving = false; });
        }
        if (Waiting.Count > 0)
        {
            List<(string, Action)> due;
            lock (Waiting) { due = Waiting.Where(w => Ready(w.Prefix)).ToList(); foreach (var d in due) Waiting.Remove(d); }
            foreach (var (prefix, a) in due) { Log($"{prefix}* packages ready, starting that content"); Run(prefix, a); }
        }
        if (_verified && !_cleaned && !_verifying && !_saving && !_stampsDirty && _active == 0 && ReadyCount == Total)
        {
            _cleaned = true;
            _saving = true;                                   // no stamp write while the folder is cleaned
            Task.Run(() => { Cleanup(); _saving = false; });
        }
        if (_unavailable) return;
        lock (Queue)
        {
            int scanned = 0;
            while (_active < Parallel && Queue.Count > 0 && scanned < Queue.Count)
            {
                string n = Queue[0];
                var e = ByName[n];
                if (Time.realtimeSinceStartup < e.RetryAt) { Queue.RemoveAt(0); Queue.Add(n); scanned++; continue; }
                Queue.RemoveAt(0);
                if (e.Tries >= MaxTries) continue;
                e.Tries++;
                _active++;
                BepInEx.Unity.IL2CPP.Utils.MonoBehaviourExtensions.StartCoroutine(_host, Fetch(e));
            }
        }
    }

    private static IEnumerator Fetch(Entry e)
    {
        var www = new UnityWebRequest();
        www.SetMethod(UnityWebRequest.UnityWebRequestMethod.Get);
        www.SetUrl(Source + Uri.EscapeDataString(e.Name));
        www.SetRequestHeader("User-Agent", $"UnknownsHalloween/{HalloweenPlugin.PluginVersion}");
        www.downloadHandler = new DownloadHandlerBuffer();
        www.timeout = 120;
        var op = www.SendWebRequest();
        while (!op.isDone) yield return null;
        byte[] data = null;
        string error = null;
        long code = www.responseCode;
        if (www.isNetworkError || www.isHttpError) error = code > 0 ? $"HTTP {code}" : www.error ?? "network error";
        else data = www.downloadHandler.data;
        www.downloadHandler.Dispose();
        www.Dispose();
        if (error == null)
        {
            var write = Task.Run(() => Store(e, data));
            while (!write.IsCompleted) yield return null;
            error = write.IsFaulted ? write.Exception?.GetBaseException().Message : write.Result;
        }
        _active--;
        if (error == null)
        {
            _loaded++;
            _stampsDirty = true;
            if (_active == 0 && ReadyCount == Total) Log($"all {Total} packages ready ({_loaded} downloaded since start)");
            yield break;
        }
        if (code == 401 || code == 403 || code == 404)
        {
            // Repo privat oder (noch) nicht da: eine Zeile, kein weiterer Versuch in dieser Sitzung.
            if (!_unavailable)
            {
                _unavailable = true;
                lock (Queue) Queue.Clear();
                Log($"asset repository not available ({error.Trim()}); Halloween costumes and maps stay off until " +
                    $"the packages are in {Folder} (next start tries again)");
            }
            yield break;
        }
        if (e.Tries < MaxTries)
        {
            e.RetryAt = Time.realtimeSinceStartup + Backoff[Math.Min(e.Tries, Backoff.Length - 1)];
            lock (Queue) Queue.Add(e.Name);
        }
        else if (!_gaveUpLogged)
        {
            _gaveUpLogged = true;
            Warn($"download failed ({error.Trim()}), giving up until the next start; content of missing packages stays off");
        }
    }

    /// <summary>Hintergrund: Groesse, SHA-256 und Inhaltsverzeichnis pruefen, daneben schreiben, an den Platz schieben.</summary>
    private static string Store(Entry e, byte[] data)
    {
        if (data == null || data.Length != e.Size) return $"size {data?.Length ?? 0} instead of {e.Size}";
        string hash;
        using (var sha = SHA256.Create()) hash = Convert.ToHexString(sha.ComputeHash(data)).ToLowerInvariant();
        if (hash != e.Sha256) return "checksum does not match";
        Directory.CreateDirectory(Folder);
        string path = PathOf(e.Name), tmp = path + ".part";
        File.WriteAllBytes(tmp, data);
        File.Move(tmp, path, true);
        var fi = new FileInfo(path);
        var idx = ReadIndex(path, fi.Length);
        if (idx == null) return "package index unreadable";
        lock (Gate) { e.OkLength = fi.Length; e.OkTicks = fi.LastWriteTimeUtc.Ticks; e.Index = idx; e.StatAt = Environment.TickCount64; }
        return null;
    }

    /// <summary>Alles im eigenen Ordner loeschen, was nicht zum aktuellen Katalog gehoert (nur Dateien, keine Unterordner).</summary>
    private static void Cleanup()
    {
        try
        {
            string root = Path.GetFullPath(Folder);
            var gone = new List<string>();
            long bytes = 0;
            foreach (var f in Directory.GetFiles(root))
            {
                string name = Path.GetFileName(f);
                if (ByName.ContainsKey(name) || name.Equals(StampFile, StringComparison.OrdinalIgnoreCase)) continue;
                if (!string.Equals(Path.GetDirectoryName(Path.GetFullPath(f)), root, StringComparison.OrdinalIgnoreCase)) continue;
                try { long len = new FileInfo(f).Length; File.Delete(f); gone.Add(name); bytes += len; } catch { }
            }
            if (gone.Count > 0)
                Log($"removed {gone.Count} file(s) that are not part of catalog {HalloweenAssetCatalog.Tag} ({bytes / 1024} KB): " +
                    string.Join(", ", gone.Take(10)) + (gone.Count > 10 ? ", ..." : ""));
        }
        catch (Exception e) { Warn($"cleanup failed: {e.Message}"); }
    }
}

/// <summary>Ressourcen der DLL plus der Pakete als "eingebettete Ressourcen" (fuer AtlasMapDef.ResourceAssembly).</summary>
internal sealed class HalloweenResourceAssembly : Assembly
{
    private static readonly Assembly Own = typeof(HalloweenResourceAssembly).Assembly;

    public override Stream GetManifestResourceStream(string name) => HalloweenAssets.Open(name);

    public override ManifestResourceInfo GetManifestResourceInfo(string resourceName) =>
        HalloweenAssets.Exists(resourceName) ? new ManifestResourceInfo(this, resourceName, ResourceLocation.Embedded) : null;

    public override string[] GetManifestResourceNames() =>
        Own.GetManifestResourceNames().Concat(HalloweenAssets.PackedNames()).Distinct().ToArray();

    public override string FullName => "UnknownsHalloween.Resources+Assets";
}

/// <summary>Takt fuer den Store (Downloads, Nachmeldungen).</summary>
public class HalloweenAssetHost : MonoBehaviour
{
    public HalloweenAssetHost(IntPtr ptr) : base(ptr) { }
    private void Update()
    {
        HalloweenAssets.Tick();
        try { TextureVersions.Tick(this); }
        catch (Exception e) { HalloweenPlugin.Logger?.LogError($"[Halloween/MapArt] {e.Message}"); }
    }
}
