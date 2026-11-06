// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Dixi - im Dixi-Klo des Crew Camps verstecken (Feedback DrSuspect 28.10., n52; Option 1956, Standard an).
// Vor der Tuer: Use-Knopf "HIDE". Drinnen ist man fuer alle anderen unsichtbar, steht still und sieht nur durch ein Guckloch
// in der Tuer (schwarzer Bildschirm mit kleinem runden Ausschnitt). "LEAVE", ein Meeting oder der eigene Tod holen einen heraus.
// 05.11. (Feedback 29.10., User-Entscheidung): drinnen kann niemand getoetet werden (TOR-Kill, UC-Rollen, Engel, Daemonen).
// Dafuer ist die Zeit am Stueck begrenzt (Option 1958, Standard 20 s, auch "Unlimited"), danach ist das Klo fuer einen selbst
// gesperrt (Option 1959, Standard 30 s). Die Tuer geht beim Rein- und Rausgehen kurz auf, sobald das Bild dafuer da ist
// (Resources/hw2026/villa_extra/dixi_open.png, gleiche Kamera und Standlinie wie das Kartenbild).
// RPC Modul 236 Sub 40 [spieler][drin] (jeder -> alle, nur fuer sich selbst; der Absender wird geprueft).

using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Hazel;
using TheOtherRoles;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    public static CustomOption DixiHide, DixiTime, DixiCooldown;
    private const byte SubDixi = 40;
    private const float DixiReach = 0.9f, DoorOpenFor = 0.55f;
    private static readonly HashSet<byte> Hiders = new();
    private Vector2 _dixiSpot;
    private bool _dixiKnown, _inDixi;
    private float _dixiEnteredAt, _dixiReadyAt, _doorClosesAt;
    private GameObject _peephole;
    private static Sprite _peepSprite;
    private SpriteRenderer _dixiRenderer;
    private Sprite _dixiClosed, _dixiOpen;

    private static bool DixiOn { get { try { return DixiHide == null || DixiHide.getBool(); } catch { return true; } } }

    /// <summary>Sekunden am Stueck, 0 = unbegrenzt.</summary>
    private static float DixiLimit
    {
        get
        {
            try
            {
                if (DixiTime == null) return 20f;
                string s = DixiTime.selections[DixiTime.selection].ToString();
                return s.EndsWith("s") && float.TryParse(s.TrimEnd('s'), out float v) ? v : 0f;
            }
            catch { return 20f; }
        }
    }

    private static float DixiWait { get { try { return DixiCooldown == null ? 30f : DixiCooldown.getFloat(); } catch { return 30f; } } }

    /// <summary>Drinnen im Dixi und damit vor jedem Kill geschuetzt.</summary>
    internal static bool DixiProtects(PlayerControl p) => p != null && _current != null && DixiOn && Hiders.Contains(p.PlayerId);

    private void DixiReset()
    {
        try
        {
            foreach (var p in PlayerControl.AllPlayerControls.ToArray())
                if (p != null && Hiders.Contains(p.PlayerId)) SetPetShown(p, true);
        }
        catch { }
        Hiders.Clear();
        _inDixi = false;
        _dixiKnown = false;
        _dixiReadyAt = 0f;
        _doorClosesAt = 0f;
        if (_peephole != null) Object.Destroy(_peephole);
        _peephole = null;
        _dixiRenderer = null;
        _dixiClosed = _dixiOpen = null;
        var props = AtlasMaps.Props("dixi");
        if (props.Count > 0)
        {
            _dixiSpot = props[0].Pos + new Vector2(0f, -0.5f);
            _dixiKnown = true;
            _dixiRenderer = props[0].Renderer;
            _dixiClosed = _dixiRenderer != null ? _dixiRenderer.sprite : null;
        }
    }

    private void DixiTick()
    {
        // Verstecken der anderen: jeden Frame, das Spiel und andere Mods schalten Visible gern wieder ein. Das Haustier haengt
        // nicht an Visible (28.10. abends: man sah es neben dem Dixi), es wird eigens aus- und beim Verlassen wieder eingeschaltet.
        if (Hiders.Count > 0)
            foreach (var p in PlayerControl.AllPlayerControls.ToArray())
            {
                if (p == null || !Hiders.Contains(p.PlayerId)) continue;
                if (p != PlayerControl.LocalPlayer && p.Visible) p.Visible = false;
                SetPetShown(p, false);
            }
        if (_doorClosesAt > 0f && Time.time >= _doorClosesAt) { _doorClosesAt = 0f; SetDoor(false); }
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || lp.Data == null) return;
        bool meeting = MeetingHud.Instance != null || ExileController.Instance != null;
        if (_inDixi)
        {
            if (meeting || lp.Data.IsDead) { LeaveDixi(); return; }
            float limit = DixiLimit, left = limit - (Time.time - _dixiEnteredAt);
            if (limit > 0f && left <= 0f) { LeaveDixi(); return; }
            if (lp.moveable) lp.moveable = false;
            StopBody(lp);
            AtlasMaps.OfferUse(limit > 0f ? $"LEAVE {Mathf.CeilToInt(left)}" : "LEAVE", "task_villa_btn_secret.png", LeaveDixi, always: true);
            return;
        }
        if (!_dixiKnown || !DixiOn || meeting || lp.Data.IsDead) return;
        if (!AtlasMaps.CanReach(_dixiSpot, DixiReach)) return;
        if (Time.time < _dixiReadyAt)
            AtlasMaps.OfferUse($"WAIT {Mathf.CeilToInt(_dixiReadyAt - Time.time)}", "task_villa_btn_secret.png", () => { }, enabled: false);
        else AtlasMaps.OfferUse("HIDE", "task_villa_btn_secret.png", EnterDixi);
    }

    private void EnterDixi()
    {
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || _inDixi || Time.time < _dixiReadyAt) return;
        _inDixi = true;
        _dixiEnteredAt = Time.time;
        lp.moveable = false;
        // stehen bleiben und vor die Tuer setzen (28.10. abends: wer beim Betreten lief, rutschte weiter)
        StopBody(lp);
        try { lp.NetTransform.RpcSnapTo(_dixiSpot); } catch { }
        Hiders.Add(lp.PlayerId);
        SendDixi(true);
        OpenDoorBriefly();
        ShowPeephole(true);
        AtlasMaps.Sfx("clack", 0.7f);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} dixi: hiding (limit {DixiLimit:0}s)");
    }

    private void LeaveDixi()
    {
        var lp = PlayerControl.LocalPlayer;
        if (!_inDixi) return;
        _inDixi = false;
        _dixiReadyAt = Time.time + DixiWait;
        if (lp != null)
        {
            lp.moveable = true;
            Hiders.Remove(lp.PlayerId);
            SetPetShown(lp, true);
        }
        SendDixi(false);
        OpenDoorBriefly();
        ShowPeephole(false);
        AtlasMaps.Sfx("creak", 0.6f);
    }

    // ------------------------------------------------------------------ Tuer

    private void OpenDoorBriefly()
    {
        if (!SetDoor(true)) return;
        _doorClosesAt = Time.time + DoorOpenFor;
    }

    /// <summary>Tauscht das Kartenbild gegen die offene Tuer (gleiche Groesse und Standlinie). False ohne Bild.</summary>
    private bool SetDoor(bool open)
    {
        try
        {
            if (_dixiRenderer == null || _dixiClosed == null) return false;
            if (open && _dixiOpen == null)
            {
                var tex = HwArt.LoadTexture("villa_extra", "dixi_open.png");
                if (tex == null) return false;
                // gleiche Weltgroesse wie das geschlossene Kartenbild, Anker unten mittig wie dort
                var b = _dixiClosed.bounds.size;
                var pivot = new Vector2(_dixiClosed.pivot.x / _dixiClosed.rect.width, _dixiClosed.pivot.y / _dixiClosed.rect.height);
                _dixiOpen = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, tex.height / Mathf.Max(0.01f, b.y));
                _dixiOpen.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            }
            _dixiRenderer.sprite = open ? _dixiOpen : _dixiClosed;
            return true;
        }
        catch { return false; }
    }

    /// <summary>Fremde Spieler: die Tuer geht auch fuer alle anderen kurz auf.</summary>
    private static void RemoteDoor()
    {
        var w = _current;
        if (w == null) return;
        w.OpenDoorBriefly();
    }

    private static void StopBody(PlayerControl p)
    {
        try { if (p.MyPhysics != null && p.MyPhysics.body != null) p.MyPhysics.body.velocity = Vector2.zero; } catch { }
    }

    private static void SetPetShown(PlayerControl p, bool on)
    {
        try
        {
            var pet = p.cosmetics != null ? p.cosmetics.currentPet : null;
            if (pet == null) return;
            foreach (var r in pet.GetComponentsInChildren<Renderer>(true))
                if (r != null && r.enabled != on) r.enabled = on;
        }
        catch { }
    }

    private void ShowPeephole(bool on)
    {
        if (!on) { if (_peephole != null) Object.Destroy(_peephole); _peephole = null; return; }
        var hud = HudManager.InstanceExists ? HudManager.Instance : null;
        if (hud == null) return;
        _peephole = new GameObject("DixiPeephole") { layer = 5 };
        _peephole.transform.SetParent(hud.transform, false);
        _peephole.transform.localPosition = new Vector3(0f, 0f, 5f);
        _peephole.transform.localScale = new Vector3(5f, 5f, 1f);
        var sr = _peephole.AddComponent<SpriteRenderer>();
        sr.sprite = _peepSprite ??= PaintPeephole();
        sr.sortingOrder = -5;                                              // hinter den Knoepfen
    }

    /// <summary>Schwarz mit einem kleinen, weich berandeten Loch in der Mitte (ein Fuenftel der Bildhoehe), 4,8 x 4,8 Einheiten bei Massstab 1.</summary>
    private static Sprite PaintPeephole() => GraveyardWorld.Painted(480, 480, new Vector2(0.5f, 0.5f), (x, y) =>
    {
        float d = Vector2.Distance(new Vector2(x, y), new Vector2(240f, 240f));
        float a = Mathf.Clamp01((d - 16f) / 8f);
        return new Color32(6, 8, 14, (byte)(255 * a));
    });

    private static void SendDixi(bool inside)
    {
        try
        {
            var lp = PlayerControl.LocalPlayer;
            if (lp == null || AmongUsClient.Instance == null) return;
            var w = UCRpc.Begin(HollowmereIntro.RpcModule);
            w.Write(SubDixi);
            w.Write(lp.PlayerId);
            w.Write(inside);
            AmongUsClient.Instance.FinishRpcImmediately(w);
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} dixi send failed: {e.Message}"); }
    }

    internal static bool HandleDixiRpc(byte sub, MessageReader reader)
    {
        if (sub != SubDixi) return false;
        byte pid = reader.ReadByte();
        bool inside = reader.ReadBoolean();
        var sender = UCRpc.Sender;
        if (sender == null || sender.PlayerId != pid) return true;           // nur fuer sich selbst
        if (inside) Hiders.Add(pid);
        else
        {
            Hiders.Remove(pid);
            SetPetShown(sender, true);
            var lp = PlayerControl.LocalPlayer;
            if (sender.Data != null && (!sender.Data.IsDead || (lp != null && lp.Data != null && lp.Data.IsDead))) sender.Visible = true;
        }
        RemoteDoor();
        return true;
    }

    // ------------------------------------------------------------------ Autotest (UC_HALLOWEEN_DIAG=villalarge,dixi)

    private void DiagDixi(PlayerControl lp)
    {
        switch (_diagStep)
        {
            case 0:
                if (!_dixiKnown) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag dixi: no dixi on this variant"); _diagTask++; return; }
                try { lp.NetTransform.RpcSnapTo(_dixiSpot); } catch { }
                _diagStep = 1; _diagAt = Time.time + 1f; return;
            case 1:
                AtlasMaps.Shot("dixi", "before");
                EnterDixi();
                _diagStep = 2; _diagAt = Time.time + 0.25f; return;
            case 2:
                AtlasMaps.Shot("dixi", "door_open_enter");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag dixi: inside {_inDixi}, protected {DixiProtects(lp)}, limit {DixiLimit:0}s, " +
                                               $"kill check {Helpers.checkMuderAttempt(lp, lp)}, door image {(_dixiOpen != null ? "yes" : "no")}");
                _diagStep = 3; _diagAt = Time.time + 1.5f; return;
            case 3:
                AtlasMaps.Shot("dixi", "inside");
                LeaveDixi();
                _diagStep = 4; _diagAt = Time.time + 0.25f; return;
            case 4:
                AtlasMaps.Shot("dixi", "door_open_leave");
                _diagStep = 5; _diagAt = Time.time + 1f; return;
            case 5:
            {
                AtlasMaps.Shot("dixi", "cooldown");
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag dixi: outside {!_inDixi}, protected {DixiProtects(lp)}, " +
                                               $"cooldown left {Mathf.Max(0f, _dixiReadyAt - Time.time):0.0}s");
                // echter Kill-Versuch an einer Freeplay-Puppe, die als versteckt gilt: muss am MurderPlayer-Guard scheitern
                var dummy = PlayerControl.AllPlayerControls.ToArray().FirstOrDefault(p => p != null && p != lp && p.Data != null && !p.Data.IsDead);
                if (dummy == null) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag dixi: no dummy for the kill test"); _diagStep = 7; return; }
                Hiders.Add(dummy.PlayerId);
                try { lp.MurderPlayer(dummy, MurderResultFlags.Succeeded); } catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} diag dixi: {e.Message}"); }
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} diag dixi: kill on hidden dummy {dummy.Data.PlayerName} -> dead {dummy.Data.IsDead}");
                Hiders.Remove(dummy.PlayerId);
                _diagStep = 7; _diagAt = Time.time + 0.5f; return;
            }
            default:
                _diagTask++; _diagStep = 0; _diagAt = Time.time + 1f; return;
        }
    }

    /// <summary>Drinnen kein Kill, verlaessliche Stelle: PlayerControl.MurderPlayer ist eine Il2Cpp-Spielmethode (der Detour haelt, anders
    /// als bei heissen TOR-Methoden unter Tiered Compilation) und laeuft fuer jeden Kill auf allen Clients; alle kennen die Versteckten
    /// (Sub 40), also blocken alle gleich. Gilt fuer TOR-, UC- und Vanilla-Kills.</summary>
    [HarmonyPatch(typeof(PlayerControl), nameof(PlayerControl.MurderPlayer))]
    private static class DixiMurderGuard
    {
        private static bool Prefix(PlayerControl __instance, PlayerControl target)
        {
            try
            {
                if (target == null || target == __instance || !DixiProtects(target)) return true;
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} dixi: murder of {target.Data?.PlayerName} by {__instance?.Data?.PlayerName} blocked (hiding)");
                return false;
            }
            catch { return true; }
        }
    }

    /// <summary>Zusaetzlich frueh beim Moerder, damit TOR gar nicht erst zuschlaegt (kann unter Tiering ausfallen, dann greift der
    /// Guard oben).</summary>
    [HarmonyPatch(typeof(Helpers), nameof(Helpers.checkMuderAttempt))]
    private static class DixiKillPatch
    {
        private static void Postfix(PlayerControl target, ref MurderAttemptResult __result)
        {
            try
            {
                if (__result != MurderAttemptResult.PerformKill && __result != MurderAttemptResult.DelayVampireKill) return;
                if (!DixiProtects(target)) return;
                __result = MurderAttemptResult.SuppressKill;
                HalloweenPlugin.Logger.LogInfo($"{LogPrefix} dixi: kill on {target.Data?.PlayerName} blocked (hiding)");
            }
            catch { }
        }
    }
}
