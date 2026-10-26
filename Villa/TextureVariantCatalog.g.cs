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
        ("villa", "auswahl", "Claude's pick (GPT + previous)", "Claudes Auswahl (GPT + bisher)", "villa_auswahl.hwp", 19721381L, "97a924888b4835a55ddfc3ded2f38a9c4e02ea1b595e8259b19dae868439f631"),
        ("villa", "gpt", "GPT (25.10.)", "GPT (25.10.)", "villa_gpt.hwp", 19699048L, "baa91a34d1bd9fb25cf510e12df040daed2a8c09dfc06729f79b290ec6219fb8"),
        ("villa", "qwen", "Qwen 2.1 (25.10., partial)", "Qwen 2.1 (25.10., teilweise)", "villa_qwen.hwp", 18919151L, "2bf491ee5703bad08b0590ca8d1afe3acaca2385f21561a54dfaa971544f1d83"),
        ("villa", "v7", "Release 0.1.3.5 (24.10.)", "Release 0.1.3.5 (24.10.)", "villa_v7.hwp", 19522833L, "44bf50b7f41247d7b57c8e7080deb1b2a79b5c72828f8cd3607b4d295ff5fd9b"),
        ("villa", "v6", "Release 0.1.3.4 (24.10.)", "Release 0.1.3.4 (24.10.)", "villa_v6.hwp", 19506651L, "b8c8279b352636e8ed8106a9db6cc93ffbe77a0f0f3dd700e5f77ab597c27efa"),
        ("villa", "v5", "Release 0.1.3.3 (24.10.)", "Release 0.1.3.3 (24.10.)", "villa_v5.hwp", 19515438L, "41501b36085fc86dac1b831a04de3ad3909093f41a1fb2745da5231e28f74879"),
        ("villa", "v1", "Release 0.1.3.2 (first art, 20.10.)", "Release 0.1.3.2 (erste Grafik, 20.10.)", "villa_v1.hwp", 19042365L, "056f70b381ec7b5e41023e0519d213384c8213730c0dc733d0288e27ed5c7276"),
    };
}
