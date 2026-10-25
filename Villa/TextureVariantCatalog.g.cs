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
        ("villa", "installed", "Previous art (installed)", "Bisherige Grafik (installiert)", null, 0L, null),
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 19675072L, "72343396e84fcf21379927459f27b0f086b47883dae58e9bc56231ab90dcb0b9"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 19692202L, "73dd32868078295d3357598202cf71399dcedeb5f4d1daa9713d6d4dea4c3293"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 18907764L, "2bfb0c9bfd777be56cf75d2105726cf6c20940ed3f6acf2819c3a38fd7919e0a"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 19208012L, "089ab21bd32e1663f92602aede81154baca42ea5b8e0adcacfa66243b8eb3de5"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 19223889L, "cafa673cb3bc624a949f28f81299496439a117bb43cc2b3c44c5f7e03e89a844"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 19253770L, "b01e97826cbc1652b5fa804e74a00a3880481750acf8f58f3b40d3a6ca927a7e"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 18775585L, "8c15362a624d65b10bbe97ef8a9d76f60bd84cc205dbb12a1609ea593bdbec47"),
    };
}
