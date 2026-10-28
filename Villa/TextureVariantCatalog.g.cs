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
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 19946585L, "a04d6b1801b72c0be1631e41bd57190fa17499d13f1f3fdfa1d2c118f401f45f"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 19924565L, "0dd364cc870c99c0e66256985422e479f3dc95feaaea06d44f1c55e903e80944"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 19354658L, "3778de841b07e0e00b7c954bc098e6016ff0c7bf6b91cbcbd72c7b87bfda6d2c"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 20083218L, "ccca1d661472792d168d4efbae6b0e49d839df921990bb8d78ee45fe05eafc02"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 20061631L, "cc96c7fe110a2039300265c9866aabd2334c199e4c1868f74941a29980f6152a"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 20046047L, "9bdfcf2c1109241c04966f0d6c14119413b95a4b8b92a36978908484510e1f44"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 19563963L, "60928785b94491aa7ae71a5e8e9994c1a93f5e1114c62b5ce1022a11e5c15436"),
    };
}
