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
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 19676926L, "737bb56b2685cbe4bf2102c0c8777e9d7057e5bd27cb1f3ff2f5a6f1a9f4d95b"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 19676149L, "e0b9518ae5e5c3e870e3c7d30e358307779bd79fb3a40db3b71e4dd473b61dda"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 18905602L, "de03cf89d6594f9422b23f400f02e61dfb7bc54fbc4b6da61a4340bd2b25fc27"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 19478639L, "6b1b29713b6e27687f3f48f19b05febb76ec450a4398ebd288b26122288554aa"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 19462679L, "19456d15679b2ef15e1b5170f024072f129911653a66c5a51ab35833dd4ff6e7"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 19504715L, "f3ad506e96f19466b1e232fdf6fa6dbcc0fa123bc14c5bb980bcaca20c7a9209"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 19035491L, "d6b66635fec04b3d9f96258d5eac50b7a25e3c01ca69d3d602e5a03b46c9caf6"),
    };
}
