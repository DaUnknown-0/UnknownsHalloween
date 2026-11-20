// Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
// Licensed under GPL-3.0-or-later. See LICENSE for details.
//
// AUTOMATISCH ERZEUGT von tools/build_texture_variants.py - NICHT VON HAND AENDERN.
// Grafik-Fassungen der Halloween-Karten fuer das Vergleichsmenue der Testversionen (TextureVersions).
// File null = die installierte Fassung aus den normalen Paketen; sonst ein Paket unter files/variants/ im Asset-Repo.

namespace UnknownsHalloween;

internal static class TextureVariantCatalog
{
    public static readonly (string Map, string Id, string LabelEn, string LabelDe, string File, long Size, string Sha256)[] Variants =
    {
        ("villa", "installed", "Current art (installed)", "Aktuelle Grafik (installiert)", null, 0L, null),
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 24260842L, "94a8c1155639483b1b39a420b3f906044bc7d53e77361f396c4f05b4d1c8c397"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 24212690L, "7c31cbcbf031b87c65e2cd987985731055fa35569336ff3102da3b7340737583"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 23728137L, "c15a1bfdc8a04ec061d5b840fa4c94ae542094a39ee436015755ec763293eb04"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 24379721L, "b200eed455d8205e4edc3e59b149cd55354f7e2e78d290bb062f52cb16a847ee"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 24383437L, "56b7f896735b12a5d8152252e732a501abfcbcdf547b6349db5c051092c6e0d4"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 24381850L, "16dd732a6829c5f953b842e6b2c7fe7e1d1693d7093192d57110b3cfb3d6c9a6"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 23886282L, "07b2d662393972a3185417a876605fdc1f109b5b516f5811da6e6d3f2fe1e6e7"),
    };
}
