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
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 20075136L, "ba85a7ba849599b0e790e6e3f2d8b96e22bcf36570b0e15becd8662c5c0ee8cd"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 20027185L, "749543e58c768b81cb783b1d5885977ffd745b957894ec730ce4e7bf83f8db1b"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 19499965L, "c80fe4817436acaa434d05f4f5dbead8c90a349b30530cd2181fd47e65968766"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 20192667L, "e710dffd9bd85e76ccd40062658b6efc575d725259f6b08755398d21205ab200"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 20184337L, "1149473e60c2dc557e9c8d87464e769b674492f7910eec71c6a499260d6ab4f8"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 20182670L, "25e9a0c88f1b49f66db23ae4a2994b995edb8e3ab68d0bf6e3e56e24d0060050"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 19674411L, "26a10c18a3c9ddea6dc0d0a548f3204fd7572c0858d069f2d489dfe6889a03b8"),
    };
}
