// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.RadioMic - echte Funkdurchsage am Funktisch im Radio Room (Feedback DrSuspect 28.10., n85; User 05.11.:
// "Host kann einstellen, wer es nutzen kann. Bei default ist Host + Suspect + ich an").
//
// Option 2160 "Radio Microphone": Selected Players / Everyone / Off (Standard Selected Players). Ausgewaehlt sind immer der Host
// und die Spieler aus BepInEx/config/UnknownsHalloween/radio_mic.txt (je Zeile der SHA-256 von PUID oder Friend-Code, "#" fuer
// Kommentare; beim ersten Start mit Mo und DrSuspect angelegt). Der Host pflegt die Liste im Lobby-Menue "Radio Microphone"
// (HollowmereWorld.RadioMicMenu.cs, seit 06.11.) oder im Chat: "/mic <Name>" schaltet einen Spieler an oder aus, "/mic" zeigt sie.
// Auch sich selbst kann er abschalten (Zeile "host-off"). Er verteilt die erlaubten Spieler-Ids beim Rundenbau und nach jeder
// Aenderung (Sub 42).
//
// Wer darf, sieht am Funktisch "SPEAK" statt "TUNE": 3 Sekunden Aufnahme ueber Unitys Microphone, dann geht die Durchsage als
// IMA-ADPCM (6 kHz, 4 Bit, rund 9 KB) in Teilen an alle (Sub 43 [id][teil][von][daten]); hoechstens 5 Teile pro Sekunde, damit
// der Server keinen Schub sieht. Alle in Hoerweite des Funktischs hoeren sie mit Rauschen und Knacken. 30 s Abklingzeit je
// Spieler, Empfaenger pruefen Erlaubnis und Abstand selbst. Nichts wird gespeichert.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using BepInEx;
using HarmonyLib;
using Hazel;
using TheOtherRoles;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    public static CustomOption RadioMic;
    private const byte SubMicAllowed = 42, SubMicPart = 43;
    private const int MicRate = 6000, MicSeconds = 3, MicChunk = 800;
    private const float MicCooldown = 30f, MicPartGap = 0.2f;

    private static readonly HashSet<byte> MicAllowed = new();
    private static readonly Dictionary<(byte Pid, ushort Msg), byte[][]> MicIncoming = new();
    private static readonly Dictionary<byte, float> MicLastFrom = new();
    private static readonly Queue<byte[]> MicOutgoing = new();
    private static ushort _micMsgId;
    private bool _micRecording, _micSentList;
    private float _micRecordStarted, _micReady, _micNextPart;
    private AudioClip _micClip;
    private int _micClipRate;

    private static string MicListPath => Path.Combine(Paths.ConfigPath, "UnknownsHalloween", "radio_mic.txt");

    /// <summary>0 = Selected Players, 1 = Everyone, 2 = Off.</summary>
    private static int MicMode { get { try { return RadioMic == null ? 0 : RadioMic.getSelection(); } catch { return 0; } } }

    private static bool MicMayUse(PlayerControl p)
    {
        if (p == null || MicMode == 2) return false;
        return MicMode == 1 || MicAllowed.Contains(p.PlayerId);
    }

    // ------------------------------------------------------------------ Liste (nur Host)

    // 06.11. (User): der Host darf auch sich selbst abschalten; das steht als Zeile "host-off" in der Datei
    private static bool _micHostOff;

    private static HashSet<string> LoadMicList()
    {
        var set = new HashSet<string>();
        try
        {
            if (!File.Exists(MicListPath))
            {
                Directory.CreateDirectory(Path.GetDirectoryName(MicListPath));
                File.WriteAllLines(MicListPath, new[]
                {
                    "# Radio Microphone (Hollowmere): who may speak besides the host. One SHA-256 of a PUID or friend code per line.",
                    "# Edit in the lobby menu (Radio Microphone) or with the chat command /mic <name>. \"host-off\": the host may not speak either.",
                    GraveOwnerHashes[0], GraveOwnerHashes[1], GraveFishboneHashes[0], GraveFishboneHashes[1],
                });
            }
            _micHostOff = false;
            foreach (var line in File.ReadAllLines(MicListPath))
            {
                string s = line.Trim();
                if (s.Equals("host-off", StringComparison.OrdinalIgnoreCase)) _micHostOff = true;
                else if (s.Length == 64 && !s.StartsWith("#")) set.Add(s.ToLowerInvariant());
            }
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} radio_mic.txt: {e.Message}"); }
        return set;
    }

    private static void SaveMicList(HashSet<string> set)
    {
        try
        {
            var lines = new List<string>
            {
                "# Radio Microphone (Hollowmere): who may speak besides the host. One SHA-256 of a PUID or friend code per line.",
                "# Edit in the lobby menu (Radio Microphone) or with the chat command /mic <name>. \"host-off\": the host may not speak either.",
            };
            if (_micHostOff) lines.Add("host-off");
            lines.AddRange(set);
            File.WriteAllLines(MicListPath, lines);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} radio_mic.txt not saved: {e.Message}"); }
    }

    /// <summary>Host-Sicht: steht der Spieler auf der Liste (der Host selbst, solange nicht "host-off")?</summary>
    private static bool MicListed(PlayerControl p, HashSet<string> list) =>
        p != null && ((p.AmOwner && !_micHostOff) || MicHashesOf(p).Any(list.Contains));

    /// <summary>Host: einen Spieler an- oder abschalten, speichern, an alle schicken. null = nicht moeglich (keine Konto-Id).</summary>
    private static bool? MicToggle(PlayerControl target)
    {
        var list = LoadMicList();
        var hashes = MicHashesOf(target).ToList();
        if (hashes.Count == 0 && !target.AmOwner) return null;
        bool on = !MicListed(target, list);
        foreach (var h in hashes) { if (on) list.Add(h); else list.Remove(h); }
        if (target.AmOwner) _micHostOff = !on;
        SaveMicList(list);
        HostSendMicList();
        return on;
    }

    private static IEnumerable<string> MicHashesOf(PlayerControl p)
    {
        var d = p?.Data;
        if (d == null) yield break;
        if (!string.IsNullOrEmpty(d.Puid)) yield return Sha(d.Puid);
        if (!string.IsNullOrEmpty(d.FriendCode)) yield return Sha(d.FriendCode);
    }

    private static string Sha(string s)
    {
        using var sha = SHA256.Create();
        var sb = new StringBuilder(64);
        foreach (byte b in sha.ComputeHash(Encoding.UTF8.GetBytes(s))) sb.Append(b.ToString("x2"));
        return sb.ToString();
    }

    /// <summary>Host: erlaubte Spieler bestimmen und an alle schicken.</summary>
    private static void HostSendMicList()
    {
        if (AmongUsClient.Instance == null || !AmongUsClient.Instance.AmHost) return;
        var list = LoadMicList();
        MicAllowed.Clear();
        foreach (var p in PlayerControl.AllPlayerControls.ToArray())
        {
            if (p == null || p.Data == null) continue;
            if (MicListed(p, list)) MicAllowed.Add(p.PlayerId);
        }
        try
        {
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubMicAllowed);
            w.Write((byte)MicAllowed.Count);
            foreach (var id in MicAllowed) w.Write(id);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} mic list send failed: {e.Message}"); }
    }

    private void MicReset()
    {
        MicIncoming.Clear();
        MicOutgoing.Clear();
        MicLastFrom.Clear();
        _micRecording = false;
        _micSentList = false;
        _micReady = 0f;
    }

    // ------------------------------------------------------------------ Takt

    /// <summary>Am Funktisch: true, wenn der Knopf hier vergeben wurde (dann kein "TUNE").</summary>
    private bool MicOffer()
    {
        var lp = PlayerControl.LocalPlayer;
        if (!MicMayUse(lp)) return false;
        if (_micRecording)
        {
            int left = Mathf.Max(1, Mathf.CeilToInt(MicSeconds - (Time.time - _micRecordStarted)));
            AtlasMaps.OfferUse($"REC {left}", "task_villa_btn_secret.png", () => { }, always: true, enabled: false);
            return true;
        }
        if (!AtlasMaps.CanReach(RadioSpot, CurioReach)) return false;
        bool ready = Time.time >= _micReady && MicOutgoing.Count == 0;
        AtlasMaps.OfferUse(ready ? "SPEAK" : $"WAIT {Mathf.CeilToInt(Mathf.Max(_micReady - Time.time, 1f))}", "task_villa_btn_secret.png",
                           StartRecording, enabled: ready);
        return true;
    }

    private void MicTick()
    {
        if (!_micSentList && AmongUsClient.Instance != null && AmongUsClient.Instance.AmHost && PlayerControl.AllPlayerControls.Count > 0)
        {
            _micSentList = true;
            HostSendMicList();
        }
        if (_micRecording && Time.time - _micRecordStarted >= MicSeconds + 0.1f) FinishRecording();
        if (MicOutgoing.Count > 0 && Time.time >= _micNextPart)
        {
            _micNextPart = Time.time + MicPartGap;
            var part = MicOutgoing.Dequeue();
            try
            {
                var w = UCRpc.Begin(HollowmereIntro.RpcModule);
                w.Write(SubMicPart);
                w.WriteBytesAndSize(part);
                AmongUsClient.Instance.FinishRpcImmediately(w);
            }
            catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} mic part send failed: {e.Message}"); }
        }
    }

    private void StartRecording()
    {
        if (_micRecording || Time.time < _micReady || MeetingHud.Instance != null) return;
        try
        {
            if (Microphone.devices == null || Microphone.devices.Length == 0)
            {
                HalloweenPlugin.Logger.LogWarning($"{LogPrefix} radio: no microphone");
                _micReady = Time.time + 5f;
                return;
            }
            Microphone.GetDeviceCaps(null, out int min, out int max);
            _micClipRate = max == 0 ? 16000 : Mathf.Clamp(16000, Mathf.Max(min, 1), max);
            _micClip = Microphone.Start(null, false, MicSeconds, _micClipRate);
            _micRecording = _micClip != null;
            _micRecordStarted = Time.time;
            if (_micRecording) AtlasMaps.Sfx("clack", 0.4f);
        }
        catch (Exception e)
        {
            HalloweenPlugin.Logger.LogWarning($"{LogPrefix} radio: microphone failed: {e.Message}");
            _micReady = Time.time + 5f;
        }
    }

    private void FinishRecording()
    {
        _micRecording = false;
        _micReady = Time.time + MicCooldown;
        float[] raw = null;
        int rate = _micClipRate;
        try
        {
            if (_micClip != null)
            {
                // 06.11. (User: nichts zu hoeren): unter Il2Cpp kopiert ein float[] als Argument in ein neues natives Array,
                // GetData fuellte nur diese Kopie und raw blieb stumm. Darum ins native Array lesen und danach umkopieren.
                var buf = new Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppStructArray<float>(_micClip.samples * _micClip.channels);
                _micClip.GetData(buf, 0);
                raw = new float[buf.Length];
                for (int i = 0; i < raw.Length; i++) raw[i] = buf[i];
                if (_micClip.channels > 1) raw = Mono(raw, _micClip.channels);
                if (_micClip.frequency > 0) rate = _micClip.frequency;
            }
            Microphone.End(null);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} radio: reading the microphone failed: {e.Message}"); }
        if (raw == null || raw.Length == 0) return;
        float peak = 0f;
        foreach (var v in raw) peak = Mathf.Max(peak, Mathf.Abs(v));

        var pcm = Normalize(Resample(raw, rate, MicRate));
        byte[] adpcm = ImaEncode(pcm);
        var lp = PlayerControl.LocalPlayer;
        if (lp == null) return;
        ushort msg = ++_micMsgId;
        int total = (adpcm.Length + MicChunk - 1) / MicChunk;
        for (int i = 0; i < total; i++)
        {
            int len = Math.Min(MicChunk, adpcm.Length - i * MicChunk);
            var part = new byte[6 + len];
            part[0] = lp.PlayerId;
            part[1] = (byte)(msg & 0xFF); part[2] = (byte)(msg >> 8);
            part[3] = (byte)i; part[4] = (byte)total;
            part[5] = 0;
            Buffer.BlockCopy(adpcm, i * MicChunk, part, 6, len);
            MicOutgoing.Enqueue(part);
        }
        PlayVoice(pcm);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} radio: {pcm.Length / (float)MicRate:0.0} s recorded at {rate} Hz, peak {peak:0.000}" +
                                       $"{(peak < 0.01f ? " (silent: microphone muted?)" : "")}, {adpcm.Length} bytes in {total} parts");
    }

    // ------------------------------------------------------------------ Empfang

    private static bool HandleMicRpc(byte sub, MessageReader reader)
    {
        if (sub == SubMicAllowed)
        {
            int n = reader.ReadByte();
            var ids = new List<byte>();
            for (int i = 0; i < n; i++) ids.Add(reader.ReadByte());
            var sender = UCRpc.Sender;
            if (sender == null || AmongUsClient.Instance == null || sender.OwnerId != AmongUsClient.Instance.HostId) return true;
            MicAllowed.Clear();
            foreach (var id in ids) MicAllowed.Add(id);
            return true;
        }
        if (sub != SubMicPart) return false;
        byte[] part = reader.ReadBytesAndSize();
        var from = UCRpc.Sender;
        if (part == null || part.Length < 7 || from == null || part[0] != from.PlayerId || !MicMayUse(from)) return true;
        ushort msg = (ushort)(part[1] | part[2] << 8);
        int idx = part[3], total = part[4];
        if (total < 1 || total > 20 || idx >= total) return true;
        var key = (from.PlayerId, msg);
        if (!MicIncoming.TryGetValue(key, out var parts) || parts.Length != total)
        {
            // eine neue Durchsage desselben Spielers erst nach der Abklingzeit
            if (MicLastFrom.TryGetValue(from.PlayerId, out float last) && Time.time - last < MicCooldown - 5f) return true;
            MicIncoming[key] = parts = new byte[total][];
        }
        parts[idx] = part.Skip(6).ToArray();
        if (parts.Any(p => p == null)) return true;
        MicIncoming.Remove(key);
        MicLastFrom[from.PlayerId] = Time.time;
        var all = parts.SelectMany(p => p).ToArray();
        PlayVoice(ImaDecode(all));
        return true;
    }

    private static void PlayVoice(float[] pcm)
    {
        try
        {
            var lp = PlayerControl.LocalPlayer;
            float vol = lp == null ? 1f : Mathf.Clamp01(1.15f - Vector2.Distance(lp.GetTruePosition(), RadioSpot) / 14f);
            if (vol <= 0.05f || SoundManager.Instance == null || pcm == null || pcm.Length == 0) return;
            // Funk: kurzes Rauschen davor und danach (Sprechtaste), leises Rauschen darunter, harte Begrenzung
            int pad = MicRate / 5;
            var outBuf = new float[pcm.Length + 2 * pad];
            var rnd = new System.Random(pcm.Length);
            for (int i = 0; i < outBuf.Length; i++)
            {
                float noise = (float)(rnd.NextDouble() * 2 - 1);
                bool voice = i >= pad && i < pad + pcm.Length;
                float s = voice ? pcm[i - pad] * 0.9f + noise * 0.035f : noise * 0.2f;
                outBuf[i] = Mathf.Clamp(s * 1.3f, -0.8f, 0.8f);
            }
            // abgespielt mit 24 kHz, linear hochgerechnet: 6 kHz als Clip-Rate ist fuer die Audio-Ausgabe ungewoehnlich
            const int up = 4;
            var play = new float[outBuf.Length * up];
            for (int i = 0; i < play.Length; i++)
            {
                int a = i / up, b = Math.Min(a + 1, outBuf.Length - 1);
                play[i] = Mathf.Lerp(outBuf[a], outBuf[b], (i % up) / (float)up);
            }
            var clip = AudioClip.Create("hollowmere_radio_voice", play.Length, 1, MicRate * up, false);
            clip.SetData(play, 0);
            SoundManager.Instance.PlaySound(clip, false, vol);
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} radio voice: {pcm.Length / (float)MicRate:0.0} s at volume {vol:0.00}");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} radio voice failed: {e.Message}"); }
    }

    // ------------------------------------------------------------------ Audio

    private static float[] Mono(float[] x, int ch)
    {
        var m = new float[x.Length / ch];
        for (int i = 0; i < m.Length; i++) { float s = 0f; for (int c = 0; c < ch; c++) s += x[i * ch + c]; m[i] = s / ch; }
        return m;
    }

    /// <summary>Linear auf die Zielrate, vorher grob tiefpassgefiltert (Mittel ueber das Verhaeltnis).</summary>
    private static float[] Resample(float[] x, int from, int to)
    {
        if (from == to) return x;
        int n = (int)((long)x.Length * to / from);
        var y = new float[n];
        double step = (double)from / to;
        int win = Math.Max(1, (int)step);
        for (int i = 0; i < n; i++)
        {
            int a = (int)(i * step);
            float s = 0f; int c = 0;
            for (int k = 0; k < win && a + k < x.Length; k++) { s += x[a + k]; c++; }
            y[i] = c > 0 ? s / c : 0f;
        }
        return y;
    }

    private static float[] Normalize(float[] x)
    {
        float peak = 0f;
        foreach (var v in x) peak = Mathf.Max(peak, Mathf.Abs(v));
        if (peak < 0.01f) return x;
        float g = Mathf.Min(0.9f / peak, 8f);
        for (int i = 0; i < x.Length; i++) x[i] *= g;
        return x;
    }

    private static readonly int[] ImaStep =
    {
        7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
        130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166,
        1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845,
        8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767,
    };
    private static readonly int[] ImaIndex = { -1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8 };

    /// <summary>IMA-ADPCM, 4 Bit je Abtastwert, Startwerte 0.</summary>
    private static byte[] ImaEncode(float[] pcm)
    {
        var outB = new byte[(pcm.Length + 1) / 2];
        int pred = 0, index = 0;
        for (int i = 0; i < pcm.Length; i++)
        {
            int sample = Mathf.Clamp((int)(pcm[i] * 32767f), -32768, 32767);
            int step = ImaStep[index], diff = sample - pred, code = 0;
            if (diff < 0) { code = 8; diff = -diff; }
            int delta = step >> 3;
            if (diff >= step) { code |= 4; diff -= step; delta += step; }
            step >>= 1;
            if (diff >= step) { code |= 2; diff -= step; delta += step; }
            step >>= 1;
            if (diff >= step) { code |= 1; delta += step; }
            pred = Mathf.Clamp((code & 8) != 0 ? pred - delta : pred + delta, -32768, 32767);
            index = Mathf.Clamp(index + ImaIndex[code], 0, 88);
            if ((i & 1) == 0) outB[i >> 1] = (byte)code; else outB[i >> 1] |= (byte)(code << 4);
        }
        return outB;
    }

    private static float[] ImaDecode(byte[] data)
    {
        var pcm = new float[data.Length * 2];
        int pred = 0, index = 0;
        for (int i = 0; i < pcm.Length; i++)
        {
            int code = (i & 1) == 0 ? data[i >> 1] & 0x0F : data[i >> 1] >> 4;
            int step = ImaStep[index], delta = step >> 3;
            if ((code & 4) != 0) delta += step;
            if ((code & 2) != 0) delta += step >> 1;
            if ((code & 1) != 0) delta += step >> 2;
            pred = Mathf.Clamp((code & 8) != 0 ? pred - delta : pred + delta, -32768, 32767);
            index = Mathf.Clamp(index + ImaIndex[code], 0, 88);
            pcm[i] = pred / 32768f;
        }
        return pcm;
    }

    // ------------------------------------------------------------------ Autotest (UC_HALLOWEEN_DIAG=villalarge,mic)

    private void DiagMic(PlayerControl lp)
    {
        switch (_diagStep)
        {
            case 0:
            {
                // Kodierung: 1 s Sprachaehnliches (zwei Toene mit Huellkurve) hin und zurueck, Abstand Signal/Fehler
                var x = new float[MicRate];
                for (int i = 0; i < x.Length; i++)
                    x[i] = 0.6f * Mathf.Sin(2 * Mathf.PI * 220f * i / MicRate) * Mathf.Sin(Mathf.PI * i / x.Length) + 0.2f * Mathf.Sin(2 * Mathf.PI * 660f * i / MicRate);
                var y = ImaDecode(ImaEncode(x));
                double sig = 0, err = 0;
                for (int i = 0; i < x.Length; i++) { sig += x[i] * x[i]; err += (x[i] - y[i]) * (x[i] - y[i]); }
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag mic: ADPCM {x.Length} samples -> {ImaEncode(x).Length} bytes, SNR {10 * Math.Log10(sig / Math.Max(err, 1e-9)):0.0} dB, " +
                                               $"allowed {MicMayUse(lp)} (mode {MicMode}, list {MicAllowed.Count}), devices {SafeDevices()}");
                try { lp.NetTransform.RpcSnapTo(RadioSpot); } catch { }
                _diagStep = 1; _diagAt = Time.time + 1f; return;
            }
            case 1:
                AtlasMaps.Shot("mic", "radio");
                StartRecording();
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag mic: recording {_micRecording}");
                _diagStep = 2; _diagAt = Time.time + MicSeconds + 0.6f; return;
            default:
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag mic: queued parts {MicOutgoing.Count}, cooldown {Mathf.Max(0f, _micReady - Time.time):0}s");
                _diagTask++; _diagStep = 0; _diagAt = Time.time + 1f; return;
        }
    }

    private static string SafeDevices()
    {
        try { return Microphone.devices == null ? "none" : Microphone.devices.Length.ToString(); }
        catch (Exception e) { return "error " + e.Message; }
    }

    // ------------------------------------------------------------------ Chat: /mic

    [HarmonyPatch(typeof(ChatController), nameof(ChatController.SendChat))]
    private static class MicCommandPatch
    {
        [HarmonyPriority(Priority.First)]
        private static bool Prefix(ChatController __instance)
        {
            try
            {
                if (__instance == null || __instance.freeChatField == null) return true;
                string text = (__instance.freeChatField.Text ?? "").Trim();
                if (!text.StartsWith("/mic", StringComparison.OrdinalIgnoreCase) || (text.Length > 4 && text[4] != ' ')) return true;
                __instance.freeChatField.Clear();
                __instance.quickChatMenu?.Clear();
                var lp = PlayerControl.LocalPlayer;
                if (AmongUsClient.Instance == null || !AmongUsClient.Instance.AmHost)
                {
                    __instance.AddChat(lp, "Radio Microphone: only the host can change who may speak.");
                    return false;
                }
                string arg = text.Length > 5 ? text.Substring(5).Trim() : "";
                var players = PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null).ToList();
                if (arg.Length > 0)
                {
                    var target = players.FirstOrDefault(p => string.Equals(p.Data.PlayerName, arg, StringComparison.OrdinalIgnoreCase))
                                 ?? players.FirstOrDefault(p => p.Data.PlayerName.IndexOf(arg, StringComparison.OrdinalIgnoreCase) >= 0);
                    if (target == null) { __instance.AddChat(lp, $"Radio Microphone: no player called \"{arg}\" here."); return false; }
                    bool? on = MicToggle(target);
                    if (on == null) { __instance.AddChat(lp, $"Radio Microphone: {target.Data.PlayerName} has no account id."); return false; }
                    __instance.AddChat(lp, $"Radio Microphone: {target.Data.PlayerName} {(on.Value ? "may speak now" : "may no longer speak")}.");
                    MicMenu.RefreshIfOpen();
                    return false;
                }
                var list = LoadMicList();
                var names = players.Where(p => MicListed(p, list)).Select(p => p.Data.PlayerName);
                string mode = MicMode == 1 ? "everyone" : MicMode == 2 ? "off" : "selected players";
                __instance.AddChat(lp, $"Radio Microphone ({mode}): {string.Join(", ", names)}. Toggle someone with /mic <name>.");
                return false;
            }
            catch (Exception e)
            {
                HalloweenPlugin.Logger?.LogError($"{LogPrefix} /mic: {e}");
                return true;
            }
        }
    }
}
