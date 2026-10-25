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
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 19705653L, "23fbbaa8c461d7fb5c5ac9e1140e02f8f997f2291268aca1ba0c94254aa52a3d"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 19672053L, "9208fcbf8faa7716e15d4308a2261ce4caef2d45a483320bb8e740b86c100add"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 18905185L, "895b2dc95c6a844f23dd2ad067537ce2c677692891655be35019515dabe9e7a4"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 19530517L, "5b1875a4750d4cef8af7d8586a1b4345c5dabebc304f0dcacd01fc2044403184"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 19515704L, "ccda0751596ed2c9fa8bf65f132fcd3182b210e5ff17fde4ea9165e18013531e"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 19535628L, "f9ad7e8614560ff674364c3f77ee72ace28506d5256688dfd45369377c07a1c8"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 19060822L, "124d3a9e72365c8c0a82311f05f75c1749bdbd9cdeae55b8c6b63ca65b0e06d2"),
    };
}
