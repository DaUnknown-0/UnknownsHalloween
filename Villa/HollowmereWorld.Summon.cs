// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Summon - die Beschwoerung am Pentagramm des Seance Parlour (Feedback DrSuspect 28.10., n40-n43; Regeln vom User).
//
// - Kerzen: oben = 1, dann im Uhrzeigersinn 2-5 (Sternspitzen k: 1 -> 0, 2 -> 2, 3 -> 4, 4 -> 1, 5 -> 3). Wer sie anzuendet, ist egal;
//   der Host merkt sich die Reihenfolge. Wer die fuenfte anzuendet, beschwoert.
// - Option 1954 "Summoning Circle": Easy (Standard) = 4-1-3-5-2 ruft einen Guten (Tyrael, Castiel oder Bobby, gewuerfelt), jede
//   andere Folge einen Daemon (Diablo, Baal oder Mephisto). Hard = jedes Wesen hat seine Folge (Buchseiten), Castiel und Bobby
//   stehen in einem zweiten, versteckten Buch im Arbeitszimmer; jede andere Folge = ein gewuerfelter Daemon. Off = wie frueher:
//   brennen alle fuenf, steht der alte Daemon im Kreis (HollowmereWorld.Ritual.cs).
// - Buch: Lesetisch der Long Library ("READ"). Hoechstens die Haelfte der Spieler darf es lesen (Host vergibt, "geheime Aufgabe"
//   als Textzeile in der Aufgabenliste). Wer beschwoert, ohne gelesen zu haben, ruft einen Geist, der ihn toetet: die Leiche
//   liegt in zwei Haelften.
// - Wirkung (Host): Daemonen geben den Impostorn eine Ruestung bis zum naechsten Meeting und toeten 2-3 Spieler, die ihnen zu nahe
//   kommen (Diablo/Baal mit Feuer: verkohlte Leiche; Mephisto mit Gift: Tod nach 6 s oder beim Meeting, gruene Leiche).
//   Tyrael: Ruestung fuer Crew und Neutrale bis zum naechsten Meeting. Castiel: Gnade (Schutz vor dem Rauswurf im naechsten
//   Meeting) fuer Crew und Neutrale; Auftritt mit flackerndem Licht, Funken und Fluegelschatten. Bobby: die Weeping Angels schlafen
//   bis zum naechsten Meeting. Die Wesen bleiben 25 s, der Geist 4 s.
// - Klaenge: Resources/hw2026/villa_summon/summon_<wesen>.wav (tools/gen_summon_audio.py, eigene TTS-Zeilen und Stinger);
//   BepInEx/config/UnknownsHalloween/sounds/summon_<wesen>.wav|.ogg ersetzt sie, wenn der Spieler dort selbst etwas ablegt.
// RPC Modul 236: Sub 33 Wesen [wesen][beschwoerer] (Host), 34 Opfer [spieler][art] (Host, vor dem Kill), 35 Segen [art][n][ids]
// (Host), 36 Ruestung gebrochen [spieler] (jeder), 37 Lesen [buch] (jeder -> Host), 38 Lesen-Antwort [spieler][ok][buch] (Host).

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using HarmonyLib;
using Hazel;
using TheOtherRoles;
using TMPro;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    public static CustomOption Summoning;
    private const byte SubSummon = 33, SubSummonVictim = 34, SubBlessing = 35, SubArmorBroken = 36, SubRead = 37, SubReadResult = 38;

    private enum Being : byte { Diablo, Baal, Mephisto, Tyrael, Castiel, Bobby, Ghost }
    private static readonly string[] BeingKey = { "diablo", "baal", "mephisto", "tyrael", "castiel", "bobby", "ghost" };
    private static readonly string[] BeingName = { "Diablo", "Baal", "Mephisto", "Tyrael", "Castiel", "Bobby", "a restless ghost" };
    private static readonly Color[] BeingGlow =
    {
        new(1f, 0.35f, 0.15f), new(0.7f, 0.35f, 1f), new(0.45f, 1f, 0.35f), new(1f, 0.9f, 0.5f), new(0.75f, 0.85f, 1f), new(0.55f, 0.85f, 1f), new(0.8f, 0.9f, 1f),
    };
    // Kerzennummer (1 oben, im Uhrzeigersinn) -> Sternspitze k in HollowmereWorld.Ritual.cs
    private static readonly int[] NumberToTip = { -1, 0, 2, 4, 1, 3 };
    private static readonly int[] EasyGood = { 4, 1, 3, 5, 2 };
    private static readonly int[][] HardCodes =
    {
        new[] { 1, 2, 3, 4, 5 },   // Diablo
        new[] { 5, 4, 3, 2, 1 },   // Baal
        new[] { 1, 3, 5, 2, 4 },   // Mephisto
        new[] { 4, 2, 5, 3, 1 },   // Tyrael
        new[] { 4, 1, 3, 5, 2 },   // Castiel (zweites Buch)
        new[] { 4, 5, 1, 2, 3 },   // Bobby (zweites Buch)
    };
    private const float SummonSecs = 25f, GhostSecs = 4f, DemonReach = 1.7f, PoisonDelay = 6f, ReadReach = 1.0f;

    // Buecher (Weltmeter): Lesetisch der Long Library, Regal im Arbeitszimmer (nur Hard)
    private static readonly Vector2 BookMain = new(5.5f - 17f, 14f - 17.25f);
    private static readonly Vector2 BookHidden = new(32.3f - 17f, 14f - 19.15f);

    private static int SummonMode { get { try { return Summoning == null ? 0 : Summoning.getSelection(); } catch { return 0; } } }   // 0 Easy, 1 Hard, 2 Off

    // Host: Reihenfolge der Kerzen (Nummern 1-5) und wer zuletzt angezuendet hat
    private readonly List<int> _litOrder = new();
    private byte _lastLighter = 255;
    // alle Clients
    private static readonly HashSet<byte> Readers = new(), ArmorBlessed = new(), Graced = new();
    private readonly Dictionary<byte, (int Kind, float At)> _pendingBodies = new();
    private readonly Dictionary<byte, Sprite> _splitTop = new();
    private readonly Dictionary<byte, Material> _splitMat = new();
    private readonly List<(byte Pid, float At)> _poisoned = new();
    private Being _being;
    private byte _summoner = 255;
    private float _summonAt = -1f, _nextDemonKill;
    private int _demonKillsLeft;
    private SpriteRenderer _beingSr, _beingGlow, _wingShadow;
    private readonly List<(SpriteRenderer Sr, float Born, Vector2 V)> _fx = new();
    private bool _secretTaskAdded, _graceArmed;
    private static Sprite _sparkSprite, _puffSprite, _wingSprite;
    private static readonly Dictionary<string, Sprite> BeingSprites = new();
    private static readonly Dictionary<string, AudioClip> SummonClips = new();

    private const string SummonRes = "UnknownsHalloween.Resources.hw2026.villa_summon.";

    // ------------------------------------------------------------------ Zuruecksetzen (RitualBuild ruft es)

    private void SummonReset()
    {
        _litOrder.Clear();
        _lastLighter = 255;
        Readers.Clear(); ArmorBlessed.Clear(); Graced.Clear();
        _pendingBodies.Clear(); _splitTop.Clear(); _splitMat.Clear(); _poisoned.Clear();
        _summonAt = -1f; _summoner = 255;
        _beingSr = _beingGlow = _wingShadow = null;
        _fx.Clear();
        _secretTaskAdded = false;
        _graceArmed = false;
        CloseBook();
        DixiReset();                                                       // HollowmereWorld.Dixi.cs
    }

    // ------------------------------------------------------------------ Kerzen (aus Ritual.cs)

    /// <summary>Host: eine Kerze wurde angezuendet (eigene oder per RPC). Liefert true, wenn die Beschwoerung uebernimmt.</summary>
    private bool SummonCandleLit(int tip, byte lighter)
    {
        if (SummonMode == 2) return false;
        int number = Array.IndexOf(NumberToTip, tip);
        if (number > 0 && !_litOrder.Contains(number)) _litOrder.Add(number);
        _lastLighter = lighter;
        return true;
    }

    /// <summary>Host: alle fuenf brennen -> welches Wesen?</summary>
    private Being PickBeing()
    {
        var order = _litOrder.ToArray();
        if (_lastLighter == 255 || !Readers.Contains(_lastLighter)) return Being.Ghost;
        var rnd = new System.Random();
        Being Demon() => (Being)rnd.Next(0, 3);
        if (SummonMode == 0)
            return order.SequenceEqual(EasyGood) ? (Being)(3 + rnd.Next(0, 3)) : Demon();
        for (int b = 0; b < HardCodes.Length; b++)
            if (order.SequenceEqual(HardCodes[b])) return (Being)b;
        return Demon();
    }

    private void HostStartSummon()
    {
        var being = PickBeing();
        byte summoner = _lastLighter;
        SendRitual(SubSummon, w => { w.Write((byte)being); w.Write(summoner); });
        StartSummon(being, summoner);
        HostSummonEffects(being, summoner);
    }

    // ------------------------------------------------------------------ Auftritt (alle Clients)

    private void StartSummon(Being being, byte summoner)
    {
        if (_ritualRoot == null) return;
        _being = being;
        _summoner = summoner;
        _summonAt = Time.time;
        _nextDemonKill = Time.time + 1.2f;
        _demonKillsLeft = being <= Being.Mephisto ? 2 + new System.Random().Next(0, 2) : 0;
        int layer = _root.gameObject.layer;
        if (_beingGlow == null)
        {
            var g = new GameObject("SummonGlow") { layer = layer };
            g.transform.SetParent(_ritualRoot, false);
            g.transform.localPosition = new Vector3(RitualCenter.x, RitualCenter.y, GraveyardWorld.AtlasMuseumBuilderFloorZ - 1.5f);
            g.transform.localScale = new Vector3(RitualScale, RitualScale, 1f);
            _beingGlow = g.AddComponent<SpriteRenderer>();
            _beingGlow.sprite = GraveyardWorld._floorGlowSprite;
        }
        if (_beingSr == null)
        {
            var d = new GameObject("SummonBeing") { layer = layer };
            d.transform.SetParent(_ritualRoot, false);
            var feet = RitualCenter + new Vector2(0f, -0.2f);
            d.transform.localPosition = new Vector3(feet.x, feet.y, GraveyardWorld.Depth(feet.y));
            _beingSr = d.AddComponent<SpriteRenderer>();
        }
        _beingSr.sprite = BeingSprite(being);
        _beingSr.color = being == Being.Ghost ? new Color(0.8f, 0.9f, 1f, 0.75f) : Color.white;
        _beingGlow.color = BeingGlow[(int)being];
        _beingSr.gameObject.SetActive(true);
        _beingGlow.gameObject.SetActive(true);
        if (being == Being.Bobby) AngelsAsleep = true;                 // jeder Client, bis zum Meeting (Angel.cs)
        if (being == Being.Castiel) CastielEntrance();
        PlaySummonSound(BeingKey[(int)being]);
        if (PlayerControl.LocalPlayer != null && PlayerControl.LocalPlayer.PlayerId == summoner && being != Being.Ghost)
            Toast($"You summoned {BeingName[(int)being]}.");
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} summoning: {BeingName[(int)being]} by player {summoner} (order {string.Join("-", _litOrder)})");
    }

    private void SummonTick()
    {
        float now = Time.time;
        BodyTick(now);
        FxTick(now);
        BookTick();
        SecretTaskTick();
        if (_poisoned.Count > 0 && AmHost)
        {
            bool meeting = MeetingHud.Instance != null;
            for (int i = _poisoned.Count - 1; i >= 0; i--)
                if (meeting || now >= _poisoned[i].At) { var pid = _poisoned[i].Pid; _poisoned.RemoveAt(i); HostKill(pid, 1, false); }
        }
        if (_summonAt < 0f) return;
        float t = now - _summonAt;
        float dur = _being == Being.Ghost ? GhostSecs : SummonSecs;
        // Aufstieg 1 s (von unten aufgerichtet), sanftes Schweben, am Ende 1 s Absinken
        float rise = Mathf.Clamp01(t / 1f), sink = Mathf.Clamp01((t - dur) / 1f);
        if (_beingSr != null)
        {
            float k = rise * (1f - sink);
            _beingSr.transform.localScale = new Vector3(1f, Mathf.Max(0.01f, k), 1f);
            float bob = _being == Being.Mephisto || _being == Being.Ghost || _being == Being.Bobby ? 0.08f * Mathf.Sin(t * 2.2f) : 0f;
            var feet = RitualCenter + new Vector2(0f, -0.2f + bob);
            _beingSr.transform.localPosition = new Vector3(feet.x, feet.y, GraveyardWorld.Depth(RitualCenter.y - 0.2f));
        }
        if (_beingGlow != null)
        {
            var c = BeingGlow[(int)_being];
            _beingGlow.color = new Color(c.r, c.g, c.b, (0.7f + 0.3f * Mathf.Sin(t * 6f)) * rise * (1f - sink));
        }
        if (_being == Being.Castiel && _wingShadow != null)
            _wingShadow.color = new Color(0f, 0f, 0f, 0.55f * Mathf.Clamp01(t / 0.6f) * Mathf.Clamp01((2.6f - t) / 0.8f));
        if (_being <= Being.Mephisto && (_being == Being.Diablo || _being == Being.Baal) && now >= _nextFireFx)
        {
            _nextFireFx = now + 0.12f;
            Spawn(_puffSprite ??= PaintPuff(), RitualCenter + new Vector2(UnityEngine.Random.Range(-0.6f, 0.6f), UnityEngine.Random.Range(-0.3f, 0.2f)),
                new Vector2(0f, 0.9f), new Color(1f, 0.45f, 0.1f, 0.8f));
        }
        if (AmHost && _demonKillsLeft > 0 && t > 1f && t < dur && now >= _nextDemonKill)
        {
            _nextDemonKill = now + 0.25f;
            HostDemonKill();
        }
        if (t > dur + 1f) EndSummon();
    }

    private float _nextFireFx;

    private void EndSummon()
    {
        _summonAt = -1f;
        if (_beingSr != null) _beingSr.gameObject.SetActive(false);
        if (_beingGlow != null) _beingGlow.gameObject.SetActive(false);
        if (_wingShadow != null) _wingShadow.gameObject.SetActive(false);
        for (int k = 0; k < 5; k++) SetRitualLit(k, false);
        _litOrder.Clear();
        AtlasMaps.Sfx("whoosh", 0.4f);
    }

    private bool SummonRunning => _summonAt >= 0f;

    // ------------------------------------------------------------------ Wirkung (Host)

    private void HostSummonEffects(Being being, byte summoner)
    {
        var alive = PlayerControl.AllPlayerControls.ToArray().Where(p => p != null && p.Data != null && !p.Data.IsDead && !p.Data.Disconnected).ToList();
        switch (being)
        {
            case Being.Ghost:
                var victim = alive.FirstOrDefault(p => p.PlayerId == summoner);
                if (victim != null) HostKill(victim.PlayerId, 2, true);
                break;
            case Being.Tyrael:
                HostBless(0, alive.Where(p => !IsImpostor(p)));
                break;
            case Being.Castiel:
                HostBless(1, alive.Where(p => !IsImpostor(p)));
                break;
            case Being.Bobby:
                break;                                                     // jeder Client: AngelsAsleep
            default:
                HostBless(0, alive.Where(IsImpostor));
                break;
        }
    }

    private void HostDemonKill()
    {
        foreach (var p in PlayerControl.AllPlayerControls.ToArray())
        {
            if (_demonKillsLeft <= 0) return;
            if (p == null || p.Data == null || p.Data.IsDead || p.Data.Disconnected || p.inVent) continue;
            if (Vector2.Distance(p.GetTruePosition(), RitualCenter) > DemonReach) continue;
            if (_poisoned.Any(x => x.Pid == p.PlayerId)) continue;
            _demonKillsLeft--;
            if (_being == Being.Mephisto)
            {
                _poisoned.Add((p.PlayerId, Time.time + PoisonDelay));
                byte pid = p.PlayerId;
                SendRitual(SubSummonVictim, w => { w.Write(pid); w.Write((byte)3); });   // 3 = vergiftet (nur Anzeige)
                MarkPoisoned(pid);
            }
            else HostKill(p.PlayerId, 0, true);
        }
    }

    /// <summary>art: 0 Feuer, 1 Gift, 2 Geist (Leiche in zwei Haelften).</summary>
    private void HostKill(byte pid, int kind, bool announce)
    {
        var p = PlayerControl.AllPlayerControls.ToArray().FirstOrDefault(x => x != null && x.PlayerId == pid);
        if (p == null || p.Data == null || p.Data.IsDead) return;
        SendRitual(SubSummonVictim, w => { w.Write(pid); w.Write((byte)kind); });
        NoteVictim(pid, kind);
        GraveyardWorld.MarkVictim(pid);
        try
        {
            bool freeplay = AmongUsClient.Instance != null && AmongUsClient.Instance.NetworkMode == NetworkModes.FreePlay;
            if (freeplay) p.MurderPlayer(p, MurderResultFlags.Succeeded);
            else Helpers.MurderPlayer(p, p, false);
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} summoning: {BeingName[(int)_being]} took {p.Data.PlayerName} ({(kind == 0 ? "fire" : kind == 1 ? "poison" : "ghost")})");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} summon kill failed: {e.Message}"); }
    }

    private void HostBless(byte kind, IEnumerable<PlayerControl> who)
    {
        var ids = who.Select(p => p.PlayerId).ToList();
        SendRitual(SubBlessing, w => { w.Write(kind); w.Write((byte)ids.Count); foreach (var id in ids) w.Write(id); });
        ApplyBlessing(kind, ids);
    }

    private static void ApplyBlessing(byte kind, List<byte> ids)
    {
        var set = kind == 0 ? ArmorBlessed : Graced;
        foreach (var id in ids) set.Add(id);
        var lp = PlayerControl.LocalPlayer;
        if (lp != null && ids.Contains(lp.PlayerId))
            _current?.Toast(kind == 0 ? "A blessing armours you until the next meeting." : "Castiel's grace will shield you from the next vote.");
    }

    // ------------------------------------------------------------------ Meeting: Segen enden, Gnade wirkt (Host)

    private bool _summonMeeting;

    private void SummonMeetingTick()
    {
        bool meeting = MeetingHud.Instance != null || ExileController.Instance != null;
        if (meeting && !_summonMeeting)
        {
            ArmorBlessed.Clear();                                          // Ruestung bis zum naechsten Meeting
            _graceArmed = Graced.Count > 0;
            if (SummonRunning) EndSummon();
            CloseBook();
        }
        if (!meeting && _summonMeeting && _graceArmed) { Graced.Clear(); _graceArmed = false; }   // Gnade: genau dieses Meeting
        _summonMeeting = meeting;
    }

    [HarmonyPatch(typeof(MeetingHud), nameof(MeetingHud.RpcVotingComplete))]
    private static class GracePatch
    {
        [HarmonyPriority(Priority.High)]
        private static void Prefix([HarmonyArgument(1)] ref NetworkedPlayerInfo exiled, [HarmonyArgument(2)] ref bool tie)
        {
            try
            {
                if (exiled == null || !Graced.Contains(exiled.PlayerId) || exiled.IsDead) return;
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} summoning: Castiel's grace kept {exiled.PlayerName} in the game (host)");
                Graced.Remove(exiled.PlayerId);
                exiled = null;
                tie = false;
            }
            catch (Exception e) { HalloweenPlugin.Logger.LogError($"{LogPrefix} grace failed: {e.Message}"); }
        }
    }

    /// <summary>Ruestung aus der Beschwoerung wie TORs Armored: der erste Mordversuch scheitert (Helpers.checkArmored laeuft beim
    /// Moerder; UTS' Mehrfach-Ruestung haengt sich genauso an).</summary>
    [HarmonyPatch(typeof(Helpers), nameof(Helpers.checkArmored))]
    private static class ArmorPatch
    {
        private static void Postfix(PlayerControl target, bool breakShield, bool showShield, bool additionalCondition, ref bool __result)
        {
            try
            {
                if (__result || target == null || !additionalCondition || !ArmorBlessed.Contains(target.PlayerId)) return;
                if (breakShield)
                {
                    byte pid = target.PlayerId;
                    ArmorBlessed.Remove(pid);
                    SendRitual(SubArmorBroken, w => w.Write(pid));
                }
                if (showShield) target.ShowFailedMurder();
                __result = true;
            }
            catch { }
        }
    }

    // ------------------------------------------------------------------ Leichen: verkohlt, vergiftet, zerteilt

    private void NoteVictim(byte pid, int kind)
    {
        _pendingBodies[pid] = (kind, Time.time);
        if (kind == 2) CaptureTopHalf(pid);
    }

    private void MarkPoisoned(byte pid)
    {
        var p = PlayerControl.AllPlayerControls.ToArray().FirstOrDefault(x => x != null && x.PlayerId == pid);
        if (p == null) return;
        try { foreach (var sr in p.GetComponentsInChildren<SpriteRenderer>()) if (sr != null && sr.gameObject.activeInHierarchy) sr.color = Color.Lerp(sr.color, new Color(0.6f, 1f, 0.5f), 0.35f); } catch { }
        if (PlayerControl.LocalPlayer != null && PlayerControl.LocalPlayer.PlayerId == pid) Toast("Mephisto's poison burns in your veins...");
    }

    private void CaptureTopHalf(byte pid)
    {
        try
        {
            var p = PlayerControl.AllPlayerControls.ToArray().FirstOrDefault(x => x != null && x.PlayerId == pid);
            var body = p?.cosmetics?.currentBodySprite?.BodySprite;
            if (body == null || body.sprite == null) return;
            var s = body.sprite;
            var r = s.textureRect;
            var top = Sprite.Create(s.texture, new Rect(r.x, r.y + r.height * 0.45f, r.width, r.height * 0.55f), new Vector2(0.5f, 0.1f), s.pixelsPerUnit);
            top.hideFlags |= HideFlags.HideAndDontSave;
            _splitTop[pid] = top;
            _splitMat[pid] = new Material(body.material);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} top half failed: {e.Message}"); }
    }

    private void BodyTick(float now)
    {
        if (_pendingBodies.Count == 0) return;
        DeadBody[] bodies;
        try { bodies = Object.FindObjectsOfType<DeadBody>(); } catch { return; }
        foreach (var pid in _pendingBodies.Keys.ToList())
        {
            var (kind, at) = _pendingBodies[pid];
            var b = bodies.FirstOrDefault(x => x != null && x.ParentId == pid);
            if (b == null) { if (now - at > 6f) _pendingBodies.Remove(pid); continue; }
            _pendingBodies.Remove(pid);
            try
            {
                if (kind == 0)
                {
                    foreach (var sr in b.GetComponentsInChildren<SpriteRenderer>()) if (sr != null) sr.color = new Color(0.2f, 0.16f, 0.14f, sr.color.a);
                    for (int i = 0; i < 10; i++)
                        Spawn(_puffSprite ??= PaintPuff(), (Vector2)b.transform.position + new Vector2(UnityEngine.Random.Range(-0.3f, 0.3f), 0.1f),
                            new Vector2(UnityEngine.Random.Range(-0.1f, 0.1f), 0.5f), new Color(0.25f, 0.25f, 0.25f, 0.7f), i * 0.35f, 2.5f);
                }
                else if (kind == 1)
                {
                    foreach (var sr in b.GetComponentsInChildren<SpriteRenderer>()) if (sr != null) sr.color = new Color(0.55f, 0.9f, 0.45f, sr.color.a);
                }
                else if (kind == 2 && _splitTop.TryGetValue(pid, out var top))
                {
                    var go = new GameObject("SplitTop") { layer = b.gameObject.layer };
                    go.transform.SetParent(b.transform, false);
                    go.transform.localPosition = new Vector3(0.62f, 0.05f, -0.0005f);
                    go.transform.localEulerAngles = new Vector3(0f, 0f, -78f);
                    var sr = go.AddComponent<SpriteRenderer>();
                    sr.sprite = top;
                    if (_splitMat.TryGetValue(pid, out var m) && m != null) sr.material = m;
                    var p = PlayerControl.AllPlayerControls.ToArray().FirstOrDefault(x => x != null && x.PlayerId == pid);
                    if (p != null && p.Data != null) PlayerMaterial.SetColors(p.Data.DefaultOutfit.ColorId, sr);
                }
            }
            catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} body look failed: {e.Message}"); }
        }
    }

    // ------------------------------------------------------------------ Castiel: Licht flackert und platzt, Funken, Fluegelschatten

    private void CastielEntrance()
    {
        _flickerUntil = Time.time + 2.6f;                                  // Sicht flackert, Scheinwerfer gehen aus (Uhr-Mechanik)
        foreach (var pv in _candles)
        {
            if (Vector2.Distance(pv.Pos, RitualCenter) > 9f) continue;
            for (int i = 0; i < 12; i++)
                Spawn(_sparkSprite ??= PaintSpark(), pv.Pos + new Vector2(0f, 1.2f),
                    new Vector2(UnityEngine.Random.Range(-1.6f, 1.6f), UnityEngine.Random.Range(-0.4f, 1.8f)), new Color(1f, 0.9f, 0.55f), 0.55f + i * 0.02f, 0.8f, true);
        }
        if (_wingShadow == null && _ritualRoot != null)
        {
            var go = new GameObject("CastielWings") { layer = _root.gameObject.layer };
            go.transform.SetParent(_ritualRoot, false);
            // an der Nordwand hinter dem Kreis (Kamin), ueber allem im Raum
            go.transform.localPosition = new Vector3(RitualCenter.x, RitualCenter.y + 2.7f, GraveyardWorld.Depth(RitualCenter.y - 3f));
            _wingShadow = go.AddComponent<SpriteRenderer>();
            _wingShadow.sprite = _wingSprite ??= PaintWings();
        }
        if (_wingShadow != null) { _wingShadow.gameObject.SetActive(true); _wingShadow.color = new Color(0f, 0f, 0f, 0f); }
    }

    // ------------------------------------------------------------------ Teilchen

    private void Spawn(Sprite s, Vector2 at, Vector2 v, Color c, float delay = 0f, float life = 1.2f, bool gravity = false)
    {
        if (_ritualRoot == null || s == null) return;
        var go = new GameObject("SummonFx") { layer = _root.gameObject.layer };
        go.transform.SetParent(_ritualRoot, false);
        go.transform.localPosition = new Vector3(at.x, at.y, GraveyardWorld.Depth(at.y - 2f));
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = s; sr.color = new Color(c.r, c.g, c.b, 0f);
        _fx.Add((sr, Time.time + delay, gravity ? new Vector2(v.x, v.y) : v));
        _fxLife[sr.GetInstanceID()] = (life, c, gravity);
    }

    private readonly Dictionary<int, (float Life, Color C, bool Gravity)> _fxLife = new();

    private void FxTick(float now)
    {
        for (int i = _fx.Count - 1; i >= 0; i--)
        {
            var (sr, born, v) = _fx[i];
            if (sr == null) { _fx.RemoveAt(i); continue; }
            var (life, c, grav) = _fxLife.TryGetValue(sr.GetInstanceID(), out var l) ? l : (1.2f, Color.white, false);
            float t = now - born;
            if (t < 0f) continue;
            if (t > life) { _fxLife.Remove(sr.GetInstanceID()); Object.Destroy(sr.gameObject); _fx.RemoveAt(i); continue; }
            var vv = grav ? new Vector2(v.x, v.y - 4f * t) : v;
            sr.transform.localPosition += (Vector3)(vv * Time.deltaTime);
            float a = Mathf.Clamp01(t / 0.1f) * Mathf.Clamp01((life - t) / (life * 0.6f));
            sr.color = new Color(c.r, c.g, c.b, c.a * a);
            float sc = grav ? 1f : 1f + t * 0.8f;
            sr.transform.localScale = new Vector3(sc, sc, 1f);
        }
    }

    private static Sprite PaintPuff() => GraveyardWorld.Painted(48, 48, new Vector2(0.5f, 0.5f), (x, y) =>
    {
        float d = Vector2.Distance(new Vector2(x, y), new Vector2(24, 24)) / 24f;
        return new Color32(255, 255, 255, (byte)(255 * Mathf.Clamp01(1f - d) * Mathf.Clamp01(1f - d)));
    });

    private static Sprite PaintSpark() => GraveyardWorld.Painted(12, 12, new Vector2(0.5f, 0.5f), (x, y) =>
    {
        float d = Vector2.Distance(new Vector2(x, y), new Vector2(6, 6)) / 6f;
        return new Color32(255, 255, 255, (byte)(255 * Mathf.Clamp01(1.2f - d)));
    });

    /// <summary>Zwei grosse Fluegel als Schatten (Silhouette aus Federreihen), 4,2 x 2,2 m.</summary>
    private static Sprite PaintWings() => GraveyardWorld.Painted(672, 352, new Vector2(0.5f, 0.2f), (x, y) =>
    {
        float u = (x - 336f) / 336f, v = y / 352f;                   // u -1..1, v 0..1
        float au = Mathf.Abs(u);
        if (au < 0.08f) return new Color32(0, 0, 0, 0);
        // Fluegelkontur: oben bogenfoermig, unten Federspitzen
        float topEdge = 0.35f + 0.6f * Mathf.Sin(Mathf.Clamp01((au - 0.08f) / 0.92f) * Mathf.PI * 0.85f) * (1f - au * 0.35f);
        float feathers = 0.12f + 0.25f * au + 0.06f * Mathf.Abs(Mathf.Sin(au * 26f));
        if (v > topEdge || v < feathers) return new Color32(0, 0, 0, 0);
        float soft = Mathf.Clamp01((topEdge - v) * 12f) * Mathf.Clamp01((v - feathers) * 12f);
        return new Color32(0, 0, 0, (byte)(255 * soft));
    });

    // ------------------------------------------------------------------ Bilder und Klaenge

    private static Sprite BeingSprite(Being b)
    {
        string key = b == Being.Ghost ? "bobby" : BeingKey[(int)b];         // der Geist ist ein blasser, verzerrter Bobby-Umriss
        if (BeingSprites.TryGetValue(key, out var s) && s != null) return s;
        var res = SummonRes + $"summon_{key}.png";
        if (!HalloweenAssets.Exists(res)) return null;
        var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        if (!ImageConversion.LoadImage(tex, HalloweenAssets.Read(res), false)) return null;
        tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.03f), tex.height / 2.6f);
        s.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        BeingSprites[key] = s;
        return s;
    }

    private static void PlaySummonSound(string key)
    {
        try
        {
            var clip = SummonClip(key);
            if (clip == null) return;
            float vol = 1f;
            var lp = PlayerControl.LocalPlayer;
            if (lp != null) vol = Mathf.Clamp01(1.15f - Vector2.Distance(lp.GetTruePosition(), RitualCenter) / 18f);
            if (vol <= 0.05f) return;
            if (SoundManager.Instance != null) SoundManager.Instance.PlaySound(clip, false, vol);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} summon sound failed: {e.Message}"); }
    }

    /// <summary>Eigene Datei des Spielers (config/UnknownsHalloween/sounds/summon_&lt;wesen&gt;.wav oder .ogg) vor dem eingebauten Klang.</summary>
    private static AudioClip SummonClip(string key)
    {
        if (SummonClips.TryGetValue(key, out var c) && c != null) return c;
        try
        {
            string dir = Path.Combine(BepInEx.Paths.ConfigPath, "UnknownsHalloween", "sounds");
            foreach (var ext in new[] { ".wav", ".ogg" })
            {
                string f = Path.Combine(dir, $"summon_{key}{ext}");
                if (!File.Exists(f)) continue;
                c = ext == ".wav" ? WavClip(File.ReadAllBytes(f), key) : OggClip(f, key);
                if (c != null) { HalloweenPlugin.Logger.LogInfo($"{LogPrefix} summon sound {key}: own file {f}"); break; }
            }
        }
        catch { }
        if (c == null)
        {
            var res = SummonRes + $"summon_{key}.wav";
            if (HalloweenAssets.Exists(res)) c = WavClip(HalloweenAssets.Read(res), key);
        }
        if (c != null) SummonClips[key] = c;
        return c;
    }

    private static AudioClip WavClip(byte[] d, string name)
    {
        if (d == null || d.Length < 44) return null;
        int ch = BitConverter.ToInt16(d, 22), rate = BitConverter.ToInt32(d, 24), bits = BitConverter.ToInt16(d, 34);
        int pos = 12;
        while (pos + 8 <= d.Length)
        {
            int len = BitConverter.ToInt32(d, pos + 4);
            if (d[pos] == 'd' && d[pos + 1] == 'a' && d[pos + 2] == 't' && d[pos + 3] == 'a') { pos += 8; break; }
            pos += 8 + len;
        }
        if (bits != 16 || pos >= d.Length) return null;
        int n = (d.Length - pos) / 2;
        var f = new float[n];
        for (int i = 0; i < n; i++) f[i] = BitConverter.ToInt16(d, pos + i * 2) / 32768f;
        var clip = AudioClip.Create("summon_" + name, n / ch, ch, rate, false);
        clip.SetData(f, 0);
        clip.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        return clip;
    }

    /// <summary>Ogg ueber den NVorbis-Decoder, den Unknown's Collection mitbringt (per Reflection; fehlt er, bleibt es beim WAV).</summary>
    private static AudioClip OggClip(string file, string name)
    {
        var t = Type.GetType("NVorbis.VorbisReader, UnknownsCollection");
        if (t == null) return null;
        using var fs = File.OpenRead(file);
        var reader = Activator.CreateInstance(t, fs, false) as IDisposable;
        try
        {
            int ch = (int)t.GetProperty("Channels").GetValue(reader);
            int rate = (int)t.GetProperty("SampleRate").GetValue(reader);
            long total = Convert.ToInt64(t.GetProperty("TotalSamples").GetValue(reader));
            var buf = new float[total * ch];
            var read = t.GetMethod("ReadSamples", new[] { typeof(float[]), typeof(int), typeof(int) });
            int got = 0;
            while (got < buf.Length)
            {
                int r = (int)read.Invoke(reader, new object[] { buf, got, buf.Length - got });
                if (r <= 0) break;
                got += r;
            }
            var clip = AudioClip.Create("summon_" + name, got / ch, ch, rate, false);
            clip.SetData(buf, 0);
            clip.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            return clip;
        }
        finally { reader?.Dispose(); }
    }

    // ------------------------------------------------------------------ Buch

    private void OfferBooks()
    {
        if (SummonMode == 2 || _bookRoot != null) return;
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || lp.Data == null || lp.Data.IsDead) return;
        if (AtlasMaps.CanReach(BookMain, ReadReach)) { AtlasMaps.OfferUse("READ", "task_villa_btn_secret.png", () => RequestRead(0)); return; }
        if (SummonMode == 1 && AtlasMaps.CanReach(BookHidden, ReadReach)) AtlasMaps.OfferUse("READ", "task_villa_btn_secret.png", () => RequestRead(1));
    }

    private void RequestRead(byte book)
    {
        var lp = PlayerControl.LocalPlayer;
        if (lp == null) return;
        if (AmHost) { HostRead(lp.PlayerId, book); return; }
        SendRitual(SubRead, w => w.Write(book));
    }

    private void HostRead(byte pid, byte book)
    {
        int players = PlayerControl.AllPlayerControls.ToArray().Count(p => p != null && p.Data != null && !p.Data.Disconnected);
        int cap = Math.Max(1, players / 2);
        bool ok = Readers.Contains(pid) || Readers.Count < cap;
        if (ok) Readers.Add(pid);
        SendRitual(SubReadResult, w => { w.Write(pid); w.Write(ok); w.Write(book); });
        ReadResult(pid, ok, book);
    }

    private void ReadResult(byte pid, bool ok, byte book)
    {
        if (ok) Readers.Add(pid);
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || lp.PlayerId != pid) return;
        OpenBook(ok ? book : (byte)255);
    }

    private void SecretTaskTick()
    {
        var lp = PlayerControl.LocalPlayer;
        if (_secretTaskAdded || lp == null || !Readers.Contains(lp.PlayerId) || lp.myTasks == null) return;
        _secretTaskAdded = true;
        try
        {
            var task = new GameObject("HollowmereSecretTask").AddComponent<ImportantTextTask>();
            task.transform.SetParent(lp.transform, false);
            task.Text = "<color=#d4a017>Secret: light the five candles of the pentagram (Seance Parlour) in the right order</color>";
            lp.myTasks.Insert(0, task);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} secret task failed: {e.Message}"); }
    }

    // ---- Buch-Oberflaeche (HUD): zwei Seiten, blaettern mit Klick links/rechts oder Pfeiltasten, schliessen mit Esc oder X

    private GameObject _bookRoot;
    private int _bookPage;
    private byte _book;
    private readonly List<(string Title, Being[] Pics, string Line, string Note)> _pages = new();
    private SpriteRenderer[] _pagePics = Array.Empty<SpriteRenderer>();
    private TextMeshPro _tTitle, _tLine, _tNote, _tNav;
    private static Sprite _bookSprite, _dimSprite;

    private void OpenBook(byte book)
    {
        CloseBook();
        var hud = HudManager.InstanceExists ? HudManager.Instance : null;
        if (hud == null) return;
        _book = book;
        _pages.Clear();
        if (book == 255)
            _pages.Add(("The pages are blank", Array.Empty<Being>(), "", "The ink fades before your eyes. Too many have read this book already."));
        else if (SummonMode == 0)
        {
            _pages.Add(("The Guardians", new[] { Being.Tyrael, Being.Castiel, Being.Bobby }, "4 - 1 - 3 - 5 - 2", "Light the candles in this order and one of them will answer."));
            _pages.Add(("The Demons", new[] { Being.Diablo, Being.Baal, Being.Mephisto }, "any other order", "Diablo and Baal burn whoever comes close, Mephisto poisons them."));
            _pages.Add(("A warning", Array.Empty<Being>(), "Read before you call", "Whoever lights the last candle without having read this book calls a restless ghost. It will tear them apart."));
        }
        else
        {
            var list = book == 0 ? new[] { Being.Diablo, Being.Baal, Being.Mephisto, Being.Tyrael } : new[] { Being.Castiel, Being.Bobby };
            string[] notes =
            {
                "Lord of Terror. Burns whoever comes too close and armours the traitors.",
                "Lord of Destruction. Burns whoever comes too close and armours the traitors.",
                "Lord of Hatred. Poisons whoever comes too close and armours the traitors.",
                "The Archangel of Justice. Armours the innocent until the next meeting.",
                "An angel of the Lord. His grace shields the innocent from the next vote.",
                "An old hunter's ghost. He keeps the stone angels asleep until the next meeting.",
            };
            foreach (var b in list) _pages.Add((BeingName[(int)b], new[] { b }, string.Join(" - ", HardCodes[(int)b]), notes[(int)b]));
            _pages.Add(("A warning", Array.Empty<Being>(), "Any other order wakes a demon", "Whoever lights the last candle without having read a book calls a restless ghost. It will tear them apart."));
        }
        _bookRoot = new GameObject("HollowmereBook") { layer = 5 };
        _bookRoot.transform.SetParent(hud.transform, false);
        _bookRoot.transform.localPosition = new Vector3(0f, 0f, -60f);
        var dim = new GameObject("Dim") { layer = 5 };
        dim.transform.SetParent(_bookRoot.transform, false);
        dim.transform.localScale = new Vector3(40f, 25f, 1f);
        var dsr = dim.AddComponent<SpriteRenderer>();
        dsr.sprite = _dimSprite ??= GraveyardWorld.Painted(4, 4, new Vector2(0.5f, 0.5f), (x, y) => new Color32(255, 255, 255, 255));
        dsr.color = new Color(0f, 0f, 0f, 0.72f);
        var bk = new GameObject("Book") { layer = 5 };
        bk.transform.SetParent(_bookRoot.transform, false);
        bk.transform.localPosition = new Vector3(0f, 0f, -0.1f);
        var bsr = bk.AddComponent<SpriteRenderer>();
        bsr.sprite = _bookSprite ??= PaintBook();
        _pagePics = new SpriteRenderer[3];
        for (int i = 0; i < 3; i++)
        {
            var g = new GameObject($"Pic{i}") { layer = 5 };
            g.transform.SetParent(_bookRoot.transform, false);
            _pagePics[i] = g.AddComponent<SpriteRenderer>();
            _pagePics[i].sortingOrder = 5;
        }
        _tTitle = BookText(new Vector2(-2.0f, 1.95f), 3.2f, new Color32(70, 30, 20, 255));
        _tLine = BookText(new Vector2(2.0f, 0.75f), 3.6f, new Color32(120, 15, 15, 255));
        _tNote = BookText(new Vector2(2.0f, -0.75f), 2.0f, new Color32(60, 45, 35, 255));
        _tNav = BookText(new Vector2(0f, -2.45f), 1.8f, new Color32(230, 220, 200, 255));
        var x = BookText(new Vector2(3.95f, 2.45f), 3f, new Color32(230, 220, 200, 255));
        x.text = "X";
        _bookPage = 0;
        ShowPage();
        try { PlayerControl.LocalPlayer.moveable = false; } catch { }
        AtlasMaps.Sfx("whoosh", 0.35f);
    }

    private TextMeshPro BookText(Vector2 at, float size, Color32 c)
    {
        var g = new GameObject("Text") { layer = 5 };
        g.transform.SetParent(_bookRoot.transform, false);
        g.transform.localPosition = new Vector3(at.x, at.y, -0.3f);
        var t = g.AddComponent<TextMeshPro>();
        var f = HalloweenUI.Font();
        if (f != null) t.font = f;
        t.fontSize = size;
        t.color = c;
        t.alignment = TextAlignmentOptions.Center;
        t.enableWordWrapping = true;
        t.rectTransform.sizeDelta = new Vector2(3.4f, 1.6f);
        var mr = t.GetComponent<MeshRenderer>();
        if (mr != null) mr.sortingOrder = 6;
        return t;
    }

    private void ShowPage()
    {
        var p = _pages[_bookPage];
        _tTitle.text = p.Title;
        _tLine.text = p.Line;
        _tNote.text = p.Note;
        _tNav.text = _pages.Count > 1 ? $"<   {_bookPage + 1} / {_pages.Count}   >" : "";
        for (int i = 0; i < _pagePics.Length; i++)
        {
            var sr = _pagePics[i];
            if (i >= p.Pics.Length) { sr.sprite = null; continue; }
            sr.sprite = BeingSprite(p.Pics[i]);
            float h = p.Pics.Length == 1 ? 3.0f : 1.9f;
            float scale = sr.sprite != null ? h / sr.sprite.bounds.size.y : 1f;
            sr.transform.localScale = new Vector3(scale, scale, 1f);
            float x = p.Pics.Length == 1 ? -2.0f : -3.2f + i * 1.2f;
            float y = p.Pics.Length == 1 ? -1.75f : -0.95f - (i % 2) * 0.25f;
            sr.transform.localPosition = new Vector3(x, y, -0.2f - i * 0.01f);
        }
    }

    private void BookTick()
    {
        if (_bookRoot == null) { OfferBooks(); return; }
        bool close = Input.GetKeyDown(KeyCode.Escape) || (PlayerControl.LocalPlayer?.Data?.IsDead ?? true);
        if (Input.GetKeyDown(KeyCode.RightArrow) || Input.GetKeyDown(KeyCode.D)) Flip(1);
        if (Input.GetKeyDown(KeyCode.LeftArrow) || Input.GetKeyDown(KeyCode.A)) Flip(-1);
        if (Input.GetMouseButtonDown(0))
        {
            var cam = TreatFx.UiCam();
            if (cam != null)
            {
                var wp = (Vector2)_bookRoot.transform.InverseTransformPoint(cam.ScreenToWorldPoint(Input.mousePosition));
                if (wp.x > 3.6f && wp.y > 2.1f) close = true;
                else if (Mathf.Abs(wp.x) > 4.4f || Mathf.Abs(wp.y) > 2.8f) close = true;
                else Flip(wp.x < 0f ? -1 : 1);
            }
        }
        if (close) CloseBook();
    }

    private void Flip(int d)
    {
        int n = Mathf.Clamp(_bookPage + d, 0, _pages.Count - 1);
        if (n == _bookPage) return;
        _bookPage = n;
        ShowPage();
        AtlasMaps.Sfx("click", 0.4f);
    }

    private void CloseBook()
    {
        if (_bookRoot == null) return;
        Object.Destroy(_bookRoot);
        _bookRoot = null;
        try { if (PlayerControl.LocalPlayer != null) PlayerControl.LocalPlayer.moveable = true; } catch { }
    }

    /// <summary>Aufgeschlagenes Buch: Ledereinband, zwei Pergamentseiten mit Falz, 9 x 5,8 Einheiten.</summary>
    private static Sprite PaintBook()
    {
        const int W = 900, H = 580;
        var s = GraveyardWorld.Painted(W, H, new Vector2(0.5f, 0.5f), (x, y) =>
        {
            bool cover = x < 14 || x > W - 15 || y < 14 || y > H - 15;
            if (cover) return new Color32(70, 30, 22, 255);
            float fold = Mathf.Abs(x - W / 2f);
            float n = Mathf.PerlinNoise(x * 0.02f, y * 0.02f);
            float shade = Mathf.Clamp01(fold / 60f) * 0.25f + 0.75f;
            float edge = Mathf.Min(Mathf.Min(x - 14, W - 15 - x), Mathf.Min(y - 14, H - 15 - y));
            float age = Mathf.Clamp01(1f - edge / 40f) * 0.25f;
            float r = (236 - 30 * n) * shade * (1f - age), g = (222 - 34 * n) * shade * (1f - age * 1.2f), b = (180 - 40 * n) * shade * (1f - age * 1.5f);
            return new Color32((byte)r, (byte)g, (byte)b, 255);
        });
        return Sprite.Create(s.texture, s.rect, new Vector2(0.5f, 0.5f), 100f);
    }

    private void Toast(string text)
    {
        try { HudManager.Instance?.Notifier?.AddDisconnectMessage(text); } catch { }
    }

    // ------------------------------------------------------------------ Netz (aus HandleRitualRpc)

    internal static bool HandleSummonRpc(byte sub, MessageReader reader)
    {
        var w = _current;
        switch (sub)
        {
            case SubSummon:
            {
                var being = (Being)reader.ReadByte();
                byte summoner = reader.ReadByte();
                if (w == null || !UCRpc.RequireHost("Hollowmere.Summon")) return true;
                for (int k = 0; k < 5; k++) w.SetRitualLit(k, true);
                w.StartSummon(being, summoner);
                return true;
            }
            case SubSummonVictim:
            {
                byte pid = reader.ReadByte(); int kind = reader.ReadByte();
                if (w == null || !UCRpc.RequireHost("Hollowmere.SummonVictim")) return true;
                if (kind == 3) w.MarkPoisoned(pid);
                else { w.NoteVictim(pid, kind); GraveyardWorld.MarkVictim(pid); }
                return true;
            }
            case SubBlessing:
            {
                byte kind = reader.ReadByte(); int n = reader.ReadByte();
                var ids = new List<byte>();
                for (int i = 0; i < n; i++) ids.Add(reader.ReadByte());
                if (!UCRpc.RequireHost("Hollowmere.Blessing")) return true;
                ApplyBlessing(kind, ids);
                return true;
            }
            case SubArmorBroken:
                ArmorBlessed.Remove(reader.ReadByte());
                return true;
            case SubRead:
            {
                byte book = reader.ReadByte();
                var sender = UCRpc.Sender;
                if (w == null || !AmHost || sender == null || sender.Data == null || sender.Data.IsDead) return true;
                // nur wer wirklich am Buch steht
                var spot = book == 0 ? BookMain : BookHidden;
                if (Vector2.Distance(sender.GetTruePosition(), spot) > ReadReach + 0.8f) return true;
                w.HostRead(sender.PlayerId, book);
                return true;
            }
            case SubReadResult:
            {
                byte pid = reader.ReadByte(); bool ok = reader.ReadBoolean(); byte book = reader.ReadByte();
                if (w == null || !UCRpc.RequireHost("Hollowmere.Read")) return true;
                w.ReadResult(pid, ok, book);
                return true;
            }
        }
        return false;
    }
}
