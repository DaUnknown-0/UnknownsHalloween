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
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 19983142L, "378d14698586acff7d76eddb1a898c698950549ec6bffcf3fc8b021e80fd72ac"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 19960819L, "5e8e9dc542113fb69533918c0bdba4fdc66b76f6a79c906765b44cff2302786a"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 19406609L, "5a7f681cb48b121b53677f04eb4ed2e1485022e27dea986bb25eaf4d64792545"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 20150539L, "c33dd3491fd8b89eb39983acbd67b451ca359041ed56b762739ff56bffb614da"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 20127795L, "cf847d996c1c729c9e8bad070102c6e91276c061cc25c34396cdaae203bc1b8e"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 20119137L, "cac7c873ca061a3a74779f509b11f7d31b0d789b43889934697765593ccd6a62"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 19630679L, "9a005acdf90371926c9e1d05e1b1272d6d4ff51e7956db3b234e8c93eb07e01e"),
    };
}
