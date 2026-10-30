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

        List<Def> defs;
        try { defs = Parse(text); }
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
            if (startup) CleanUp(defs);
        }
        Log($"{defs.Count} online costume(s): {string.Join(", ", defs.Select(d => d.Key))}");
        foreach (var d in defs)
        {
            HalloweenAssets.AddExtra(d.Package, d.Size, d.Sha256, SourceBase + d.Package, Path.Combine(Folder, d.Package));
            try { HalloweenCostumes.AddOnline(d); }
            catch (Exception e) { Warn($"{d.Key}: {e.Message}"); }
        }
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
    private static void CleanUp(List<Def> defs)
    {
        try
        {
            var keep = new HashSet<string>(defs.Select(d => d.Package), StringComparer.OrdinalIgnoreCase) { ManifestName };
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

    internal static List<Def> Parse(string json)
    {
        using var doc = JsonDocument.Parse(json);
        var root = doc.RootElement;
        int format = root.TryGetProperty("format", out var fmt) && fmt.ValueKind == JsonValueKind.Number ? fmt.GetInt32() : 0;
        if (format != 1) throw new FormatException($"format {format} is not supported by this version");
        var list = new List<Def>();
        if (!root.TryGetProperty("costumes", out var arr) || arr.ValueKind != JsonValueKind.Array) return list;
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
        return list;
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
        if (e.TryGetProperty("kill", out var k) && k.ValueKind == JsonValueKind.Object)
        {
            d.KillFrames = k.TryGetProperty("frames", out var f) && f.ValueKind == JsonValueKind.Number ? Math.Clamp(f.GetInt32(), 0, 200) : 0;
            d.KillHold = k.TryGetProperty("hold", out var h) && h.ValueKind == JsonValueKind.Number ? Mathf.Clamp((float)h.GetDouble(), 0f, 5f) : 0f;
            d.KillerLayers = k.TryGetProperty("killerLayers", out var kl) && kl.ValueKind == JsonValueKind.True;
            d.Flashes = k.TryGetProperty("flashes", out var fl) && fl.ValueKind == JsonValueKind.Array
                ? fl.EnumerateArray().Where(x => x.ValueKind == JsonValueKind.Number).Select(x => x.GetInt32()).Where(x => x >= 0 && x < 200).Take(16).ToArray()
                : new int[0];
        }
        return d;
    }
}
