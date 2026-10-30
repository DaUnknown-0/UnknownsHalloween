// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

using System;
using UnityEngine;

namespace UnknownsHalloween;

internal sealed partial class HollowmereWorld
{
    private static Sprite _cthulhuFireSprite;

    private static Sprite CthulhuFireSprite()
    {
        if (_cthulhuFireSprite != null) return _cthulhuFireSprite;
        string resource = SummonRes + "summon_cthulhu_fire.png";
        if (!HalloweenAssets.Exists(resource)) return null;
        var texture = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        if (!ImageConversion.LoadImage(texture, HalloweenAssets.Read(resource), false)) return null;
        texture.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        _cthulhuFireSprite = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height),
            new Vector2(0.5f, 0.5f), texture.height / 1.8f);
        _cthulhuFireSprite.hideFlags |= HideFlags.HideAndDontSave | HideFlags.DontUnloadUnusedAsset;
        return _cthulhuFireSprite;
    }

    private void CthulhuFire(Vector2 position)
    {
        Spawn(CthulhuFireSprite(), position + new Vector2(0f, 0.5f), Vector2.zero, Color.white, 0f, 0.32f);
    }

    private void PactSpent(byte player)
    {
        PactProtected.Remove(player);
        if (PlayerControl.LocalPlayer != null && PlayerControl.LocalPlayer.PlayerId == player)
            Toast("The Shadow Pact absorbed a demonic attack. Its protection is spent.");
    }
}
