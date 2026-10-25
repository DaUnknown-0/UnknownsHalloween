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
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 19713338L, "6dc1134e2409234261dabaf0ef5cd954a61c26efc894f74bbd83d6a3f7071925"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 19666707L, "d3c5680a7bab4394d370ae743075164e9e7213bedb6bc7d7288400507a7a5898"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 18914354L, "0b203172ccc70bf2d900324175de491bf4715cd994ffab44efe02865a7d69567"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 19306663L, "812fd32cc42b7c6ea4cbb5c3d3e8837721905b39a7e233aa01d84a6a23c7dacb"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 19283686L, "0c41ad71182bc1924320608ad2d2f1c101a40222742cdf368aa792b59c3c28cf"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 19232711L, "ac21038d8d5772671ae43525e8684b8ce7b761f5a0cf0be9898b8ea81852b3dd"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 18740249L, "018bd7333f3df08a580c2e74d51bdf2f6a52567212636fa50bc05c5c3397779f"),
    };
}
