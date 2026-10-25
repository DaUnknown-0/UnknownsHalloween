// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HollowmereWorld.Grave - Easter Egg fuer den Autor (User 2026-10-25): stirbt er, wird das offene Grab auf dem Friedhof der
// grossen Manor (Art offenes_grab) zu seinem Grab: zugeschuettet, mit Grabstein, darauf "R.I.P." und sein Name. Erst wenn
// das naechste Meeting vorbei ist (dann ist sein Tod ohnehin allen bekannt, das Grab verraet nichts), und nur fuer ihn.
// Erkennung wie UTS EasterEggCoding: SHA-256 seiner PUID bzw. seines Friend-Codes (kein Klartext im Repo). Rein kosmetisch,
// jeder Client lokal, kein RPC. Grafik Resources/hw2026/villa_egg/egg_grave_filled.png (GPT, auf das Sprite des offenen
// Grabs eingepasst), der Name als Text auf dem Stein (Bild-KIs schreiben keine Namen).

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
        "d10f0e308524211c45d93ec3300efca28e35488ea35598196c67b1ababb7fc19",   // PUID
        "cf2eab42fba217e7af4237f7a3bcd35402f2790602e07d92c6344096701480c6",   // Friend-Code
    };
    private const string GraveRes = "UnknownsHalloween.Resources.hw2026.villa_egg.egg_grave_filled.png";
    private static readonly Vector2 GraveNameAt = new(0.495f, 0.673f);   // Steinmitte, Anteil des Sprites von links/unten

    private SpriteRenderer _graveSr;
    private bool _graveShown, _graveSawMeeting;
    private float _graveNoMeetingSince = -1f;
    private GameObject _graveText;

    private void GraveReset()
    {
        _graveShown = _graveSawMeeting = false;
        _graveNoMeetingSince = -1f;
        _graveText = null;
        _graveSr = null;
        try
        {
            var props = AtlasMaps.Props("offenes_grab");
            if (props.Count > 0) _graveSr = props[0].Renderer;
        }
        catch { }
    }

    private void GraveTick()
    {
        if (_graveSr == null || _graveShown) return;
        bool meeting = MeetingHud.Instance != null || ExileController.Instance != null;
        if (meeting) { _graveSawMeeting = true; _graveNoMeetingSince = -1f; return; }
        if (!_graveSawMeeting) return;
        // Meeting vorbei: eine Sekunde ohne MeetingHud und Rauswurf abwarten (dazwischen kann ein Bild ohne beides liegen,
        // und beim Rauswurf ist der Tod erst nach dem Bild gesetzt)
        if (_graveNoMeetingSince < 0f) { _graveNoMeetingSince = Time.time; return; }
        if (Time.time - _graveNoMeetingSince < 1f) return;
        _graveSawMeeting = false;
        var owner = GraveOwner();
        if (owner == null || owner.Data == null || !owner.Data.IsDead) return;
        ShowGrave(owner.Data.PlayerName);
    }

    private static PlayerControl GraveOwner()
    {
        foreach (var p in PlayerControl.AllPlayerControls.ToArray())
        {
            try
            {
                if (p == null || p.Data == null) continue;
                if (GraveMatches(p.Data.Puid) || GraveMatches(p.Data.FriendCode)) return p;
            }
            catch { }
        }
        return null;
    }

    private static bool GraveMatches(string id)
    {
        if (string.IsNullOrEmpty(id)) return false;
        using var sha = SHA256.Create();
        var hash = sha.ComputeHash(Encoding.UTF8.GetBytes(id));
        var sb = new StringBuilder(64);
        foreach (byte b in hash) sb.Append(b.ToString("x2"));
        string h = sb.ToString();
        foreach (var o in GraveOwnerHashes) if (o == h) return true;
        return false;
    }

    private void ShowGrave(string name)
    {
        try
        {
            var orig = _graveSr.sprite;
            if (orig == null || !HalloweenAssets.Exists(GraveRes)) return;
            var data = HalloweenAssets.Read(GraveRes);
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            if (data == null || !ImageConversion.LoadImage(tex, data, false)) return;
            tex.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            var size = orig.rect.size;
            var pivot = new Vector2(orig.pivot.x / size.x, orig.pivot.y / size.y);
            var sp = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, orig.pixelsPerUnit * tex.width / size.x);
            sp.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
            _graveSr.sprite = sp;
            _graveShown = true;

            // Inschrift: dunkles Grau, wie eingemeisselt
            float ppu = orig.pixelsPerUnit;
            var local = new Vector3((GraveNameAt.x - pivot.x) * size.x / ppu, (GraveNameAt.y - pivot.y) * size.y / ppu, -0.001f);
            _graveText = new GameObject("GraveInscription") { layer = _graveSr.gameObject.layer };
            _graveText.transform.SetParent(_graveSr.transform, false);
            _graveText.transform.localPosition = local;
            var t = _graveText.AddComponent<TMPro.TextMeshPro>();
            var f = HalloweenUI.Font();
            if (f != null) t.font = f;
            t.fontSize = 0.9f;
            t.fontStyle = TMPro.FontStyles.Bold;
            t.alignment = TMPro.TextAlignmentOptions.Center;
            t.enableWordWrapping = false;
            t.enableAutoSizing = true; t.fontSizeMin = 0.4f; t.fontSizeMax = 0.9f;
            t.color = new Color32(58, 58, 64, 255);
            t.rectTransform.sizeDelta = new Vector2(size.x * 0.24f / ppu, size.y * 0.16f / ppu);
            t.text = $"R.I.P.\n{name}";
            var mr = t.GetComponent<MeshRenderer>();
            if (mr != null) { mr.sortingLayerID = _graveSr.sortingLayerID; mr.sortingOrder = _graveSr.sortingOrder + 1; }
            HalloweenPlugin.Logger.LogInfo($"{LogPrefix} the open grave is taken now");
        }
        catch (Exception e) { HalloweenPlugin.Logger.LogWarning($"{LogPrefix} grave egg failed: {e.Message}"); }
    }
}
