// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Dixi - im Dixi-Klo des Crew Camps verstecken (Feedback DrSuspect 28.10., n52; Option 1956, Standard an).
// Vor der Tuer: Use-Knopf "HIDE". Drinnen ist man fuer alle anderen unsichtbar, steht still und sieht nur durch ein Guckloch
// in der Tuer (schwarzer Bildschirm mit kleinem runden Ausschnitt). "LEAVE", ein Meeting oder der eigene Tod holen einen heraus.
// Ein Impostor, der weiss, dass jemand drin ist, kann trotzdem toeten (wie die Schraenke in Horrorfilmen).
// RPC Modul 236 Sub 40 [spieler][drin] (jeder -> alle, nur fuer sich selbst; der Absender wird geprueft).

using System;
using System.Collections.Generic;
using System.Linq;
using Hazel;
using TheOtherRoles;
using UnityEngine;
using UnknownsAtlas;
using UnknownsCollection;
using Object = UnityEngine.Object;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    public static CustomOption DixiHide;
    private const byte SubDixi = 40;
    private const float DixiReach = 0.9f;
    private static readonly HashSet<byte> Hiders = new();
    private Vector2 _dixiSpot;
    private bool _dixiKnown, _inDixi;
    private GameObject _peephole;
    private static Sprite _peepSprite;

    private static bool DixiOn { get { try { return DixiHide == null || DixiHide.getBool(); } catch { return true; } } }

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
        if (_peephole != null) Object.Destroy(_peephole);
        _peephole = null;
        var props = AtlasMaps.Props("dixi");
        if (props.Count > 0) { _dixiSpot = props[0].Pos + new Vector2(0f, -0.5f); _dixiKnown = true; }
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
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || lp.Data == null) return;
        bool meeting = MeetingHud.Instance != null || ExileController.Instance != null;
        if (_inDixi)
        {
            if (meeting || lp.Data.IsDead) { LeaveDixi(); return; }
            if (lp.moveable) lp.moveable = false;
            StopBody(lp);
            AtlasMaps.OfferUse("LEAVE", "task_villa_btn_secret.png", LeaveDixi, always: true);
            return;
        }
        if (!_dixiKnown || !DixiOn || meeting || lp.Data.IsDead) return;
        if (AtlasMaps.CanReach(_dixiSpot, DixiReach)) AtlasMaps.OfferUse("HIDE", "task_villa_btn_secret.png", EnterDixi);
    }

    private void EnterDixi()
    {
        var lp = PlayerControl.LocalPlayer;
        if (lp == null || _inDixi) return;
        _inDixi = true;
        lp.moveable = false;
        // stehen bleiben und vor die Tuer setzen (28.10. abends: wer beim Betreten lief, rutschte weiter)
        StopBody(lp);
        try { lp.NetTransform.RpcSnapTo(_dixiSpot); } catch { }
        Hiders.Add(lp.PlayerId);
        SendDixi(true);
        ShowPeephole(true);
        AtlasMaps.Sfx("clack", 0.7f);
        HalloweenPlugin.Logger.LogInfo($"{LogPrefix} dixi: hiding");
    }

    private void LeaveDixi()
    {
        var lp = PlayerControl.LocalPlayer;
        if (!_inDixi) return;
        _inDixi = false;
        if (lp != null)
        {
            lp.moveable = true;
            Hiders.Remove(lp.PlayerId);
            SetPetShown(lp, true);
        }
        SendDixi(false);
        ShowPeephole(false);
        AtlasMaps.Sfx("creak", 0.6f);
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
        return true;
    }
}
