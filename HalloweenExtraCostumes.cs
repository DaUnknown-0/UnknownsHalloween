// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HalloweenExtraCostumes - Kostueme ohne Mod-Update (User 30.10.: "baue das so, dass ich später einfach Kostüme hinzufügen
// kann, ohne Updates zu benötigen").
//
// Beim Start laedt die Mod extra/costumes.json aus dem Asset-Repo (Zweig main, nicht der Katalog-Tag der DLL). Jeder Eintrag
// beschreibt ein Kostuem (Schluessel, Name im Shop, Verhalten wie Fliegen oder Spielerfarbe) und nennt sein Bildpaket
// (extra/<paket>.hwp, Format HWP1 wie die Katalogpakete) mit Groesse und SHA-256. Die Pakete laedt und prueft HalloweenAssets
// wie alle anderen (Ablage BepInEx/halloween-assets/extra/); sobald eines bestaetigt ist, kommt das Kostuem in den Shop
// (HalloweenCostumes.AddOnline). Ohne Netz gilt die zuletzt geladene Liste.
//
// Ein neues Kostuem: Bilder nach ExtraCostumes/<key>/ legen, tools/build_extra_costume.py <key> ... laufen lassen, im
// Asset-Repo committen und auf main pushen. Fertig; jeder Spieler mit dieser Mod-Version bekommt es beim naechsten Start.
//
// Grenzen: nur Bilder und Daten, kein Code. Ein Kostuem bekommt keine eigene Host-Option (Options-IDs muessen fest bleiben);
// seine Kill-Szene folgt dem Hauptschalter. Was diese Version nicht kennt, steht hinter "minVersion" und wird uebersprungen.

using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using UnityEngine;
using UnityEngine.Networking;

namespace UnknownsHalloween;

internal static class HalloweenExtraCostumes
{
    private const string LogPrefix = "[Halloween/Extra]";
    private const string ManifestName = "costumes.json";
    private const int MaxCostumes = 64;
    private const long MaxPackage = 64L * 1024 * 1024;

    /// <summary>Ein Kostuem aus der Online-Liste, geprueft.</summary>
    internal sealed class Def
    {
        public string Key, Name, Package, Sha256;
        public long Size;
        public bool HasLegs, HasAccent, HidesBody, NoLiveBob, StillWalk, KillerLayers;
        public float WalkFps = 10f, IdleFps = 10f, KillHold;
        public int WalkIntro, KillFrames;
        public int[] Flashes;
        public string KillKey;                      // Bildschluessel der Kill-Szene (hk_<KillKey>_...), Standard: Key
        public List<AltScene> Alt;                  // weitere Szenen; eine von allen wird je Kill gewuerfelt
    }

    internal sealed class AltScene
    {
        public string Key;
        public int Frames;
        public int[] Flashes;
        public float Hold;
        public bool Killer;
    }

    /// <summary>Ein Update-Paket: ersetzt beliebige Dateien von Mod und Katalog, solange es in der Liste steht.</summary>
    internal sealed class UpdatePack
    {
        public string Package, Sha256;
        public long Size;
    }

    /// <summary>Geaenderte Daten eines eingebauten Kostuems; null = bleibt, wie es ist.</summary>
    internal sealed class Tweak
    {
        public string Key;
        public float? WalkFps, IdleFps;
        public int? WalkIntro;
        public bool? HasAccent, HasLegs, NoLiveBob, StillWalk, HidesBody;
        public Def Kill;                            // nur KillKey, KillFrames, Flashes, KillHold, KillerLayers, Alt
    }

    internal sealed class Manifest
    {
        public readonly List<Def> Costumes = new();
        public readonly List<UpdatePack> Updates = new();
        public readonly List<Tweak> Tweaks = new();
    }

    // ---------------------------------------------------------------- Updates und Tweaks
    //
    // Update-Pakete wirken ohne Neustart: Kostuem-Bilder werden neu geladen, TORs Hut-Daten erneuert, Kill-Szenen lesen ihre
    // Bilder ohnehin bei jedem Kill frisch. Steht ein Paket nicht mehr in der Liste, gilt wieder das Original. Tweaks
    // greifen erst, wenn alle Pakete da sind, damit Bildzahl und Bilder zusammenpassen.

    private static readonly HashSet<string> _activeUpdates = new(StringComparer.OrdinalIgnoreCase);
    private static HashSet<string> _wantedUpdates = new(StringComparer.OrdinalIgnoreCase);
    private static List<Tweak> _tweaks = new();
    private static int _updatesPending;

    private static void ApplyUpdates(Manifest m)
    {
        _wantedUpdates = new HashSet<string>(m.Updates.Select(u => u.Package), StringComparer.OrdinalIgnoreCase);
        _tweaks = m.Tweaks;
        var fresh = m.Updates.Where(u => !_activeUpdates.Contains(u.Package)).ToList();
        _updatesPending = fresh.Count;
        foreach (var u in fresh)
            HalloweenAssets.AddExtra(u.Package, u.Size, u.Sha256, SourceBase + u.Package, Path.Combine(Folder, u.Package));
        foreach (var u in fresh)
        {
            string name = u.Package;
            HalloweenAssets.WhenReady(name, () => UpdateReady(name));
        }
        if (fresh.Count == 0) FinishUpdates(new List<string>());
    }

    private static void UpdateReady(string package)
    {
        if (!_wantedUpdates.Contains(package)) { HalloweenAssets.RemoveExtra(package); return; }   // inzwischen ueberholt
        _activeUpdates.Add(package);
        var changed = HalloweenAssets.PackageFiles(package);
        Log($"update package {package} ready ({changed.Count} file(s))");
        if (--_updatesPending <= 0) FinishUpdates(changed);
        else HalloweenCostumes.ResourcesChanged(changed);
    }

    private static void FinishUpdates(List<string> changed)
    {
        foreach (var old in _activeUpdates.Where(p => !_wantedUpdates.Contains(p)).ToList())
        {
            changed.AddRange(HalloweenAssets.PackageFiles(old));
            HalloweenAssets.RemoveExtra(old);
            _activeUpdates.Remove(old);
        }
        if (changed.Count > 0) HalloweenCostumes.ResourcesChanged(changed);
        HalloweenCostumes.ApplyTweaks(_tweaks);
    }

    private static readonly Regex KeyRx = new("^[a-z][a-z0-9]{1,23}$");
    private static readonly Regex PackRx = new("^extra_[a-z0-9_]{1,60}\\.hwp$");
    private static readonly Regex ShaRx = new("^[0-9a-f]{64}$");

    internal static string Folder => Path.Combine(HalloweenAssets.Folder, "extra");

    /// <summary>Quelle der Liste und Pakete: Asset-Repo (main) oder, beim lokalen Testserver, dessen Ordner extra/.</summary>
    internal static string SourceBase
    {
        get
        {
            string s = HalloweenAssets.Source;
            if (s.StartsWith("http://127.0.0.1:", StringComparison.Ordinal))
                return (s.EndsWith("files/", StringComparison.Ordinal) ? s.Substring(0, s.Length - "files/".Length) : s) + "extra/";
            return HalloweenAssets.DefaultSourceBase + "main/extra/";
        }
    }

    private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");
    private static void Warn(string s) => HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {s}");

    private static MonoBehaviour _host;
    private static bool _loading;
    private static float _lastLoad = -999f;

    /// <summary>Aus HalloweenPlugin.Load nach HalloweenAssets.Start.</summary>
    internal static void Start(MonoBehaviour host)
    {
        _host = host;
        try { Directory.CreateDirectory(Folder); } catch (Exception e) { Warn($"folder: {e.Message}"); }
        _loading = true;
        _lastLoad = Time.realtimeSinceStartup;
        BepInEx.Unity.IL2CPP.Utils.MonoBehaviourExtensions.StartCoroutine(host, Load(true));
    }

    /// <summary>Liste erneut laden (User 30.10.: bei jedem Lobby-Join und per /loadcostumes fuer alle). Neue Kostueme kommen
    /// dazu, geaenderte bekommen ihr neues Paket. forced: Befehl, sonst hoechstens einmal pro Minute.</summary>
    internal static void Refresh(bool forced, string why)
    {
        if (_host == null || _loading) return;
        float now = Time.realtimeSinceStartup;
        if (now - _lastLoad < (forced ? 5f : 60f)) return;
        _loading = true;
        _lastLoad = now;
        Log($"checking the online costume list again ({why})");
        BepInEx.Unity.IL2CPP.Utils.MonoBehaviourExtensions.StartCoroutine(_host, Load(false));
    }

    // _loading wird an jedem Ausgang zurueckgesetzt (kein verschachtelter Coroutine-Aufruf: der Il2Cpp-Wrapper wartet
    // nicht verlaesslich auf innere IEnumerator)
    private static IEnumerator Load(bool startup)
    {
        string url = SourceBase + ManifestName + "?t=" + DateTime.UtcNow.Ticks / TimeSpan.TicksPerMinute;
        var www = new UnityWebRequest();
        www.SetMethod(UnityWebRequest.UnityWebRequestMethod.Get);
        www.SetUrl(url);
        www.SetRequestHeader("User-Agent", $"UnknownsHalloween/{HalloweenPlugin.PluginVersion}");
        www.downloadHandler = new DownloadHandlerBuffer();
        www.timeout = 20;
        var op = www.SendWebRequest();
        while (!op.isDone) yield return null;
        _loading = false;
        string text = null;
        bool fresh = false;
        long code = www.responseCode;
        if (!www.isNetworkError && !www.isHttpError) { text = www.downloadHandler.text; fresh = true; }
        else if (code == 404) Log("no online costume list in the asset repository (404)");
        else Warn($"online costume list not loaded ({(code > 0 ? "HTTP " + code : www.error)}), using the last one");
        www.downloadHandler.Dispose();
        www.Dispose();

        _loading = false;
        string cache = Path.Combine(Folder, ManifestName);
        if (text == null)
        {
            if (code == 404 || !startup) yield break;            // geloescht bzw. Nachladen ohne Netz: Stand bleibt
            try { if (File.Exists(cache)) text = File.ReadAllText(cache, Encoding.UTF8); } catch { }
            if (text == null) yield break;
        }
        if (!startup && text == _applied) yield break;            // nichts Neues

        Manifest manifest;
        try { manifest = Parse(text); }
        catch (Exception e)
        {
            Warn($"online costume list unreadable: {e.Message}");
            yield break;
        }
        _applied = text;
        if (fresh)
        {
            try { File.WriteAllText(cache + ".part", text, Encoding.UTF8); File.Move(cache + ".part", cache, true); } catch { }
            // nur beim Start aufraeumen: spaeter koennte ein ersetztes Paket noch in Gebrauch sein
            if (startup) CleanUp(manifest);
        }
        var defs = manifest.Costumes;
        Log($"{defs.Count} online costume(s): {string.Join(", ", defs.Select(d => d.Key))}; {manifest.Updates.Count} update package(s), {manifest.Tweaks.Count} tweak(s)");
        foreach (var d in defs)
        {
            HalloweenAssets.AddExtra(d.Package, d.Size, d.Sha256, SourceBase + d.Package, Path.Combine(Folder, d.Package));
            try { HalloweenCostumes.AddOnline(d); }
            catch (Exception e) { Warn($"{d.Key}: {e.Message}"); }
        }
        try { ApplyUpdates(manifest); }
        catch (Exception e) { Warn($"updates: {e.Message}"); }
    }

    private static string _applied;

    // ---------------------------------------------------------------- Ausloeser

    // jeder Lobby-Join (hoechstens einmal pro Minute)
    [HarmonyLib.HarmonyPatch(typeof(AmongUsClient), nameof(AmongUsClient.OnGameJoined))]
    private static class JoinedPatch
    {
        private static void Postfix() { try { Refresh(false, "lobby joined"); } catch { } }
    }

    internal const string Command = "/loadcostumes";

    // /loadcostumes: nur der Mod-Autor (HalloweenOwner); laedt bei sich und schickt allen in der Lobby den Auftrag
    // (HalloweenHandshake Sub 1, der Empfaenger prueft den Absender selbst noch einmal).
    [HarmonyLib.HarmonyPatch(typeof(ChatController), nameof(ChatController.SendChat))]
    private static class CommandPatch
    {
        [HarmonyLib.HarmonyPriority(HarmonyLib.Priority.First)]
        private static bool Prefix(ChatController __instance)
        {
            try
            {
                if (__instance == null || __instance.freeChatField == null) return true;
                string text = __instance.freeChatField.Text;
                if (string.IsNullOrEmpty(text) || text.Trim().ToLowerInvariant() != Command) return true;
                __instance.freeChatField.Clear();
                __instance.quickChatMenu?.Clear();
                var lp = PlayerControl.LocalPlayer;
                if (!HalloweenOwner.Is(lp))
                {
                    __instance.AddChat(lp, "Unknown's Halloween: this command is only for the mod author.");
                    return false;
                }
                _lastLoad = -999f;
                Refresh(true, Command);
                bool sent = HalloweenHandshake.SendReloadCostumes();
                __instance.AddChat(lp, sent ? "Unknown's Halloween: costume list is being reloaded for everyone in the lobby."
                                            : "Unknown's Halloween: costume list is being reloaded.");
                return false;
            }
            catch (Exception e)
            {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} {Command}: {e}");
                return true;
            }
        }
    }

    // Alte Pakete (nicht mehr in der Liste) und halbe Downloads im eigenen Ordner loeschen.
    private static void CleanUp(Manifest m)
    {
        try
        {
            var keep = new HashSet<string>(m.Costumes.Select(d => d.Package).Concat(m.Updates.Select(u => u.Package)), StringComparer.OrdinalIgnoreCase) { ManifestName };
            foreach (var f in Directory.GetFiles(Folder))
            {
                string n = Path.GetFileName(f);
                if (keep.Contains(n)) continue;
                if (!n.EndsWith(".hwp", StringComparison.OrdinalIgnoreCase) && !n.EndsWith(".part", StringComparison.OrdinalIgnoreCase)) continue;
                try { File.Delete(f); Log($"removed {n} (no longer listed)"); } catch { }
            }
        }
        catch { }
    }

    internal static Manifest Parse(string json)
    {
        using var doc = JsonDocument.Parse(json);
        var root = doc.RootElement;
        int format = root.TryGetProperty("format", out var fmt) && fmt.ValueKind == JsonValueKind.Number ? fmt.GetInt32() : 0;
        if (format != 1) throw new FormatException($"format {format} is not supported by this version");
        var m = new Manifest();
        var list = m.Costumes;
        if (root.TryGetProperty("updates", out var ups) && ups.ValueKind == JsonValueKind.Array)
            foreach (var e in ups.EnumerateArray())
                try { var u = ReadUpdate(e); if (u != null) m.Updates.Add(u); }
                catch (Exception ex) { Warn($"update skipped: {ex.Message}"); }
        if (root.TryGetProperty("tweaks", out var tws) && tws.ValueKind == JsonValueKind.Array)
            foreach (var e in tws.EnumerateArray())
                try { var t = ReadTweak(e); if (t != null) m.Tweaks.Add(t); }
                catch (Exception ex) { Warn($"tweak skipped: {ex.Message}"); }
        if (!root.TryGetProperty("costumes", out var arr) || arr.ValueKind != JsonValueKind.Array) return m;
        foreach (var e in arr.EnumerateArray())
        {
            if (list.Count >= MaxCostumes) { Warn($"more than {MaxCostumes} online costumes, the rest is skipped"); break; }
            try
            {
                var d = Read(e);
                if (d == null) continue;
                if (list.Any(x => x.Key == d.Key || x.Name == d.Name || x.Package == d.Package))
                {
                    Warn($"{d.Key}: key, name or package listed twice, skipped");
                    continue;
                }
                list.Add(d);
            }
            catch (Exception ex) { Warn($"entry skipped: {ex.Message}"); }
        }
        return m;
    }

    private static bool VersionOk(JsonElement e, string what)
    {
        if (!e.TryGetProperty("minVersion", out var v) || v.ValueKind != JsonValueKind.String) return true;
        string min = v.GetString();
        if (Version.TryParse(min, out var need) && HalloweenPlugin.Version >= need) return true;
        Log($"{what} needs Unknown's Halloween {min} or newer, skipped");
        return false;
    }

    private static UpdatePack ReadUpdate(JsonElement e)
    {
        string S(string p) => e.TryGetProperty(p, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
        var u = new UpdatePack { Package = S("package"), Sha256 = S("sha256")?.ToLowerInvariant() };
        if (u.Package == null || !PackRx.IsMatch(u.Package)) throw new FormatException($"bad package name '{u.Package}'");
        if (u.Sha256 == null || !ShaRx.IsMatch(u.Sha256)) throw new FormatException($"{u.Package}: bad sha256");
        if (!e.TryGetProperty("size", out var sz) || sz.ValueKind != JsonValueKind.Number || !sz.TryGetInt64(out u.Size) || u.Size < 8 || u.Size > MaxPackage)
            throw new FormatException($"{u.Package}: bad size");
        return VersionOk(e, u.Package) ? u : null;
    }

    private static Tweak ReadTweak(JsonElement e)
    {
        bool? B(string p) => e.TryGetProperty(p, out var v) && (v.ValueKind == JsonValueKind.True || v.ValueKind == JsonValueKind.False) ? v.GetBoolean() : null;
        float? N(string p, float min, float max) => e.TryGetProperty(p, out var v) && v.ValueKind == JsonValueKind.Number ? Mathf.Clamp((float)v.GetDouble(), min, max) : null;
        var t = new Tweak { Key = e.TryGetProperty("key", out var k) && k.ValueKind == JsonValueKind.String ? k.GetString() : null };
        if (t.Key == null || !KeyRx.IsMatch(t.Key)) throw new FormatException($"bad key '{t.Key}'");
        t.WalkFps = N("walkFps", 1f, 30f);
        t.IdleFps = N("idleFps", 0.5f, 30f);
        var intro = N("walkIntro", 0f, 16f);
        t.WalkIntro = intro.HasValue ? (int)intro.Value : null;
        t.HasAccent = B("hasAccent"); t.HasLegs = B("hasLegs"); t.NoLiveBob = B("noLiveBob");
        t.StillWalk = B("stillWalk"); t.HidesBody = B("hidesBody");
        if (e.TryGetProperty("kill", out var kill) && kill.ValueKind == JsonValueKind.Object)
        {
            t.Kill = new Def();
            ReadKill(kill, t.Kill);
        }
        return VersionOk(e, $"tweak {t.Key}") ? t : null;
    }

    private static readonly Regex SceneRx = new("^[a-z][a-z0-9_]{1,31}$");

    private static int[] ReadFlashes(JsonElement k) =>
        k.TryGetProperty("flashes", out var fl) && fl.ValueKind == JsonValueKind.Array
            ? fl.EnumerateArray().Where(x => x.ValueKind == JsonValueKind.Number).Select(x => x.GetInt32()).Where(x => x >= 0 && x < 200).Take(16).ToArray()
            : new int[0];

    private static string ReadSceneKey(JsonElement k)
    {
        if (!k.TryGetProperty("key", out var v) || v.ValueKind != JsonValueKind.String) return null;
        string s = v.GetString();
        if (s == null || !SceneRx.IsMatch(s)) throw new FormatException($"bad scene key '{s}'");
        return s;
    }

    private static void ReadKill(JsonElement k, Def d)
    {
        d.KillKey = ReadSceneKey(k);
        d.KillFrames = k.TryGetProperty("frames", out var f) && f.ValueKind == JsonValueKind.Number ? Math.Clamp(f.GetInt32(), 0, 200) : 0;
        d.KillHold = k.TryGetProperty("hold", out var h) && h.ValueKind == JsonValueKind.Number ? Mathf.Clamp((float)h.GetDouble(), 0f, 5f) : 0f;
        d.KillerLayers = k.TryGetProperty("killerLayers", out var kl) && kl.ValueKind == JsonValueKind.True;
        d.Flashes = ReadFlashes(k);
        if (!k.TryGetProperty("alt", out var alt) || alt.ValueKind != JsonValueKind.Array) return;
        d.Alt = new List<AltScene>();
        foreach (var a in alt.EnumerateArray().Take(8))
        {
            string key = ReadSceneKey(a);
            int frames = a.TryGetProperty("frames", out var af) && af.ValueKind == JsonValueKind.Number ? Math.Clamp(af.GetInt32(), 0, 200) : 0;
            if (key == null || frames <= 0) continue;
            d.Alt.Add(new AltScene {
                Key = key, Frames = frames, Flashes = ReadFlashes(a),
                Hold = a.TryGetProperty("hold", out var ah) && ah.ValueKind == JsonValueKind.Number ? Mathf.Clamp((float)ah.GetDouble(), 0f, 5f) : 0f,
                Killer = a.TryGetProperty("killerLayers", out var akl) && akl.ValueKind == JsonValueKind.True,
            });
        }
    }

    private static Def Read(JsonElement e)
    {
        string Str(string p) => e.TryGetProperty(p, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
        bool Bool(string p) => e.TryGetProperty(p, out var v) && v.ValueKind == JsonValueKind.True;
        float Num(string p, float def, float min, float max) =>
            e.TryGetProperty(p, out var v) && v.ValueKind == JsonValueKind.Number ? Mathf.Clamp((float)v.GetDouble(), min, max) : def;

        var d = new Def { Key = Str("key"), Name = Str("name"), Package = Str("package"), Sha256 = Str("sha256")?.ToLowerInvariant() };
        if (d.Key == null || !KeyRx.IsMatch(d.Key)) throw new FormatException($"bad key '{d.Key}'");
        string min = Str("minVersion");
        if (min != null && (!Version.TryParse(min, out var need) || HalloweenPlugin.Version < need))
        {
            Log($"{d.Key} needs Unknown's Halloween {min} or newer, skipped");
            return null;
        }
        if (d.Name == null || d.Name.Length < 3 || d.Name.Length > 40 || d.Name.Any(char.IsControl) || d.Name.Contains('<'))
            throw new FormatException($"{d.Key}: bad name");
        if (d.Package == null || !PackRx.IsMatch(d.Package)) throw new FormatException($"{d.Key}: bad package name");
        if (d.Sha256 == null || !ShaRx.IsMatch(d.Sha256)) throw new FormatException($"{d.Key}: bad sha256");
        if (!e.TryGetProperty("size", out var sz) || sz.ValueKind != JsonValueKind.Number || !sz.TryGetInt64(out d.Size) || d.Size < 8 || d.Size > MaxPackage)
            throw new FormatException($"{d.Key}: bad size");
        d.HasLegs = Bool("hasLegs");
        d.HasAccent = Bool("hasAccent");
        d.HidesBody = Bool("hidesBody");
        d.NoLiveBob = Bool("noLiveBob");
        d.StillWalk = Bool("stillWalk");
        d.WalkFps = Num("walkFps", 10f, 1f, 30f);
        d.IdleFps = Num("idleFps", 10f, 0.5f, 30f);
        d.WalkIntro = (int)Num("walkIntro", 0f, 0f, 16f);
        if (e.TryGetProperty("kill", out var k) && k.ValueKind == JsonValueKind.Object) ReadKill(k, d);
        return d;
    }
}
