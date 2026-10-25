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
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 19725243L, "409eee55098d0d6b385ace6d73d3fb8027c1a49683cd15668fc330aa76e624dd"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 19691643L, "d381634256a0113baf8d5ddd63d381d0861c6366158e6b946d24711b4a559aa6"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 18905304L, "0e955833a627a9bcddf099c2d747a92054f4cdabdad1e2e16e64cdb839e730ce"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 19517622L, "836e59cdd3eb42cc6066e499d5baad88a98973866cf5855c3f6e84727e8d9bbd"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 19502480L, "bda8f57d23a7e4378281f32186d383d31e5a3d69acf9fdf36c57e37f1b807dec"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 19515076L, "82b4c1da2ea99fcd61bc799b317f6c2f5e3a994c1e0b170e34b634d478a6bf83"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 18993475L, "2c313585adeed0d36d90904365079e12f2f3cfd8822980ecabc5fa49283e7f84"),
    };
}
