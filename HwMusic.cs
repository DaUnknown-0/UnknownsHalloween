// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

/*
 * Halloween music (idea D5, 2026-10-20): four public-domain horror classics as extra choices in the music manager of
 * TOR - Forgotten Fixes (UTS), through its neutral track contract (UTS does not know this mod):
 *   AppDomain "UTS.Music.AddTrack"  Action<string id, string title, string group, string path, string flags>
 *
 *   Danse Macabre                     Saint-Saens (1874)   suggested: lobby
 *   Night on Bald Mountain            Mussorgsky (1867)    suggested: Role Draft
 *   Toccata in D Minor                Bach (BWV 565)       suggested: menu music
 *   In the Hall of the Mountain King  Grieg (1875)         suggested: reactor, flag "tempo": the less time the
 *                                                          critical sabotage has left, the faster it plays
 * Only the compositions are public domain, so there is no recording in here: every piece is rendered from the notes
 * by our own synthesizer (tools/render_classics.py, on top of Assets/MusicGen/synth.py), Ogg Vorbis 44.1 kHz stereo,
 * embedded as Resources/hw2026/music/*.ogg. UTS decodes files from disk, so they are written once to
 * BepInEx/cache/UnknownsHalloween/music (rewritten only when the embedded file differs). They show on every tab of
 * the music manager; which tab plays which piece stays every player's own choice, nothing is switched on by itself.
 *
 * Registered once UTS has published the contract (main menu, lobby, every few seconds otherwise); without UTS
 * nothing happens. Self test: UC_HALLOWEEN_DIAG=music (logs extraction and registration).
 */

using System;
using System.IO;
using System.Linq;
using HarmonyLib;
using UnityEngine;

namespace UnknownsHalloween {
    internal static class HwMusic {
        private const string LogPrefix = "[Halloween/Music]";
        private static void Log(string s) => HalloweenPlugin.Logger?.LogInfo($"{LogPrefix} {s}");
        private static void Warn(string s) => HalloweenPlugin.Logger?.LogWarning($"{LogPrefix} {s}");

        private const string AddTrackKey = "UTS.Music.AddTrack";
        private const string ResPrefix = "UnknownsHalloween.Resources.hw2026.music.";

        private sealed class Piece {
            public string Id, File, Title, Composer, Flags;
        }

        private static readonly Piece[] Pieces = {
            new Piece { Id = "hw.dansemacabre", File = "danse_macabre.ogg", Title = "Danse Macabre", Composer = "Saint-Saëns", Flags = "" },
            new Piece { Id = "hw.baldmountain", File = "bald_mountain.ogg", Title = "Night on Bald Mountain", Composer = "Mussorgsky", Flags = "" },
            new Piece { Id = "hw.toccata", File = "toccata.ogg", Title = "Toccata in D Minor", Composer = "Bach", Flags = "" },
            new Piece { Id = "hw.mountainking", File = "mountain_king.ogg", Title = "In the Hall of the Mountain King", Composer = "Grieg", Flags = "tempo" },
        };

        internal static string Folder => Path.Combine(BepInEx.Paths.CachePath, "UnknownsHalloween", "music");

        private static bool registered;
        private static float nextTry;
        internal static int Registered { get; private set; }

        internal static void TryRegister() {
            if (registered || Time.realtimeSinceStartup < nextTry) return;
            nextTry = Time.realtimeSinceStartup + 3f;
            if (AppDomain.CurrentDomain.GetData(AddTrackKey) is not Action<string, string, string, string, string> add) return;
            registered = true;
            try {
                var asm = typeof(HwMusic).Assembly;
                Directory.CreateDirectory(Folder);
                foreach (var p in Pieces) {
                    string path = Path.Combine(Folder, p.File);
                    try {
                        using var s = asm.GetManifestResourceStream(ResPrefix + p.File);
                        if (s == null) { Warn($"{p.File} is not embedded - skipped"); continue; }
                        var bytes = new byte[s.Length];
                        int read = 0;
                        while (read < bytes.Length) { int n = s.Read(bytes, read, bytes.Length - read); if (n <= 0) break; read += n; }
                        bool same = File.Exists(path) && new FileInfo(path).Length == bytes.Length && File.ReadAllBytes(path).SequenceEqual(bytes);
                        if (!same) {
                            string tmp = path + ".tmp";
                            File.WriteAllBytes(tmp, bytes);
                            File.Move(tmp, path, true);
                        }
                        add(p.Id, p.Title, "Halloween · " + p.Composer, path, p.Flags);
                        Registered++;
                        if (Diag) Log($"diag: {p.Id} -> {path} ({bytes.Length / 1024} KB{(same ? ", cached" : ", written")}{(p.Flags.Length > 0 ? ", " + p.Flags : "")})");
                    } catch (Exception e) { Warn($"{p.File}: {e.Message}"); }
                }
                Log($"{Registered} piece(s) added to the music manager.");
            } catch (Exception e) { Warn($"registration failed: {e.Message}"); }
            if (Diag) Log("diag: music done");
        }

        [HarmonyPatch(typeof(MainMenuManager), nameof(MainMenuManager.Start))]
        static class MenuPatch { public static void Postfix() { nextTry = 0f; TryRegister(); } }

        [HarmonyPatch(typeof(LobbyBehaviour), nameof(LobbyBehaviour.Start))]
        static class LobbyPatch { public static void Postfix() { nextTry = 0f; TryRegister(); } }

        [HarmonyPatch(typeof(HudManager), nameof(HudManager.Update))]
        static class HudPatch { public static void Postfix() { if (!registered) TryRegister(); } }

        private static readonly string DiagMode = Environment.GetEnvironmentVariable("UC_HALLOWEEN_DIAG") ?? "";
        internal static readonly bool Diag = DiagMode.Split(',').Any(x => x.Trim() == "music");
    }
}
