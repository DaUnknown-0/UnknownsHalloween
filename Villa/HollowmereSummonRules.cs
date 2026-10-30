// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.

using System;
using System.Collections.Generic;
using System.Linq;

namespace UnknownsHalloween;

// Append wire values; existing saved and network values must not move.
internal enum SummonBeing : byte
{
    Diablo = 0, Baal = 1, Mephisto = 2, Tyrael = 3, Castiel = 4, Bobby = 5, Ghost = 6,
    Cthulhu = 7, ShadowPact = 8,
}

internal static class HollowmereSummonRules
{
    internal static readonly int[] EasyGood = { 4, 1, 3, 5, 2 };
    internal static readonly int[] PactCode = { 2, 5, 1, 4, 3 };
    internal static readonly IReadOnlyDictionary<SummonBeing, int[]> HardCodes = new Dictionary<SummonBeing, int[]>
    {
        [SummonBeing.Diablo] = new[] { 1, 2, 3, 4, 5 },
        [SummonBeing.Baal] = new[] { 5, 4, 3, 2, 1 },
        [SummonBeing.Mephisto] = new[] { 1, 3, 5, 2, 4 },
        [SummonBeing.Tyrael] = new[] { 4, 2, 5, 3, 1 },
        [SummonBeing.Castiel] = new[] { 4, 1, 3, 5, 2 },
        [SummonBeing.Bobby] = new[] { 4, 5, 1, 2, 3 },
        [SummonBeing.Cthulhu] = new[] { 2, 4, 1, 5, 3 },
    };
    private static readonly SummonBeing[] Demons = { SummonBeing.Diablo, SummonBeing.Baal, SummonBeing.Mephisto, SummonBeing.Cthulhu };

    internal static bool IsDemon(SummonBeing being) => Array.IndexOf(Demons, being) >= 0;
    internal static bool ShowPactPage(bool isImpostor, bool bookAllowed) => isImpostor && bookAllowed;

    internal static SummonBeing Pick(int mode, int[] order, bool hasRead, bool isImpostor, Random random)
    {
        if (!hasRead) return SummonBeing.Ghost;
        if (isImpostor && order.SequenceEqual(PactCode)) return SummonBeing.ShadowPact;
        if (mode == 0)
            return order.SequenceEqual(EasyGood) ? (SummonBeing)(3 + random.Next(3)) : Demons[random.Next(Demons.Length)];
        foreach (var pair in HardCodes)
            if (order.SequenceEqual(pair.Value)) return pair.Key;
        return Demons[random.Next(Demons.Length)];
    }
}
