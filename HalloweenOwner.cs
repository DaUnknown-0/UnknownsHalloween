// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// HalloweenOwner - erkennt den Mod-Autor (Mo) an PUID bzw. Friend-Code, gespeichert nur als SHA-256 (wie das Grab-Easter-Egg in
// HollowmereWorld.Grave.cs). Bisher nur fuer /loadcostumes (HalloweenExtraCostumes).

using System.Security.Cryptography;
using System.Text;

namespace UnknownsHalloween;

internal static class HalloweenOwner
{
    private static readonly string[] Hashes =
    {
        "d10f0e308524211c45d93ec3300efca28e35488ea35598196c67b1ababb7fc19",   // Mo: PUID
        "cf2eab42fba217e7af4237f7a3bcd35402f2790602e07d92c6344096701480c6",   // Mo: Friend-Code
    };

    internal static bool Is(PlayerControl p)
    {
        try { return p != null && p.Data != null && (HashIn(p.Data.Puid) || HashIn(p.Data.FriendCode)); }
        catch { return false; }
    }

    private static bool HashIn(string id)
    {
        if (string.IsNullOrEmpty(id)) return false;
        using var sha = SHA256.Create();
        var hash = sha.ComputeHash(Encoding.UTF8.GetBytes(id));
        var sb = new StringBuilder(64);
        foreach (byte b in hash) sb.Append(b.ToString("x2"));
        string h = sb.ToString();
        foreach (var o in Hashes) if (o == h) return true;
        return false;
    }
}
