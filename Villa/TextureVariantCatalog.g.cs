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
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 20002000L, "23b1bea688ac73ecdd35975d6dbcb62534164140ad6b829dc70fa0f4070db0ce"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 19954049L, "7f4362627b61fdb8b0514608f1204e303d9aa98f3239bcaafa24eb95a39df581"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 19442383L, "e87edd89e77347f956a16e7efac015e79c57edb946645b3478e45fbeb1b7e98a"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 20107509L, "51143e950d0eabfce688668d126e0561a7853698f52565c856987dbeabebc4ec"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 20104985L, "74c32385f03dec6ef6abe36db3eb3ac31d4ef200cb63d38cb0c8b09b6c6895ca"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 20104872L, "ac421a7877d91b343758f8860f8d163c1216a1503dd8b558214f6db4c1569a1b"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 19584579L, "6057837e1ab3608b70aaccbcd92092dfdd0fefca459ae9c5d7c58d7d4c271d2b"),
    };
}
