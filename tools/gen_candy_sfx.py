# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_candy_sfx.py - die vier eigenen Klaenge der Schuessel-Szene -> Resources/candy_eject/sfx_<name>.wav
#
# Villa/EjectEngine.cs (EjectSynth.LoadWav) zieht eine eingebettete Aufnahme sfx_<name>.wav (PCM 16 bit, 22050 Hz,
# mono) dem Synth-Klang gleichen Namens vor; die Regie (candy_eject.py) nennt sie wie jeden anderen Klang.
# Alles hier ist synthetisch (Rauschen, Impulse, Resonatoren), keine Aufnahmen, deterministisch (feste Seeds).
#
#   rustle  Bonbonpapier raschelt (Landung im Haufen, Griff)
#   munch   ein Biss mit Knacken und Kauen
#   gulp    zwei Schluckgeraeusche mit absinkendem Ton
#   burp    tiefer, rauer Ruelpser mit Vibrato
#
#     python tools/gen_candy_sfx.py

import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

SR = 22050
OUT = Path(__file__).resolve().parent.parent / "Resources" / "candy_eject"


def t_axis(sec):
    return np.arange(int(SR * sec)) / SR


def env_ad(n, attack, release, hold=0.0):
    """Huellkurve: linearer Anstieg, Halten, exponentielles Ausklingen (Zeiten in s)."""
    t = np.arange(n) / SR
    e = np.ones(n)
    a = max(1, int(attack * SR))
    e[:a] = np.linspace(0, 1, a)
    start = attack + hold
    tail = t > start
    e[tail] *= np.exp(-(t[tail] - start) / max(1e-3, release))
    return e


def bandpass(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], btype="band")
    return signal.lfilter(b, a, x)


def lowpass(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2))
    return signal.lfilter(b, a, x)


def resonator(x, f, q):
    b, a = signal.iirpeak(f / (SR / 2), q)
    return signal.lfilter(b, a, x)


def normalize(x, peak=0.8):
    m = np.abs(x).max()
    return x / m * peak if m > 0 else x


def save(name, x):
    x = normalize(x)
    # kurze Ein- und Ausblendung gegen Klicks
    k = int(SR * 0.004)
    x[:k] *= np.linspace(0, 1, k)
    x[-k:] *= np.linspace(1, 0, k)
    sf.write(OUT / f"sfx_{name}.wav", (x * 32767).astype(np.int16), SR, subtype="PCM_16")
    print(f"  sfx_{name}.wav {len(x) / SR:.2f} s  rms {np.sqrt((x ** 2).mean()):.3f}")


def rustle(rng):
    n = int(SR * 0.6)
    x = np.zeros(n)
    # viele kleine Knister-Impulse, dichter am Anfang
    for _ in range(110):
        at = int(rng.random() ** 1.7 * n * 0.9)
        ln = int(SR * rng.uniform(0.002, 0.006))
        burst_ = rng.standard_normal(ln) * np.exp(-np.arange(ln) / (ln / 3))
        burst_ = bandpass(burst_, rng.uniform(1800, 3500), rng.uniform(5000, 8000))
        x[at:at + ln] += burst_ * rng.uniform(0.4, 1.0)
    # Papierknistern: hochpass-gefiltertes Rauschen mit unruhiger Lautstaerke
    noise = rng.standard_normal(n)
    noise = bandpass(noise, 2500, 9000)
    mod = 0.5 + 0.5 * np.abs(lowpass(rng.standard_normal(n), 60, 1)) * 6
    x += noise * np.clip(mod, 0, 1.5) * 0.25
    return x * env_ad(n, 0.01, 0.22, hold=0.05)


def munch(rng):
    n = int(SR * 0.34)
    t = t_axis(0.34)
    # Krach: Rauschen, dessen Tiefpass von hell nach dumpf wandert
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    seg = int(SR * 0.02)
    for i in range(0, n, seg):
        fc = 4500 * math.exp(-i / n * 2.2) + 500
        out[i:i + seg] = lowpass(noise[i:i + seg], fc)
    out *= env_ad(n, 0.004, 0.08, hold=0.03)
    # Knackimpulse
    for at in sorted(rng.uniform(0.0, 0.2, 9)):
        i = int(at * SR)
        ln = int(SR * 0.004)
        out[i:i + ln] += rng.standard_normal(ln) * np.exp(-np.arange(ln) / (ln / 2.5)) * rng.uniform(0.8, 1.6)
    # dumpfer Schlag beim Zubeissen
    thump = np.sin(2 * np.pi * (95 - 50 * t) * t) * np.exp(-t * 22) * 1.3
    return out * 0.9 + thump


def gulp(rng):
    n = int(SR * 0.5)
    t = t_axis(0.5)
    x = np.zeros(n)
    # zwei Schlucke: sinkender Ton mit Formant, jeweils mit eigener Huelle
    for at, f0, f1, dur in ((0.0, 420, 150, 0.2), (0.22, 360, 110, 0.24)):
        i0, ln = int(at * SR), int(dur * SR)
        tt = np.arange(ln) / SR
        f = f0 * (f1 / f0) ** (tt / dur)
        ph = 2 * np.pi * np.cumsum(f) / SR
        tone = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
        tone = resonator(tone, 500, 3) * 0.6 + tone * 0.4
        e = np.sin(np.pi * tt / dur) ** 0.6
        x[i0:i0 + ln] += tone * e * 0.7
        # kleiner Kehlkopf-Klick am Ende
        k = int(SR * 0.006)
        x[i0 + ln - k:i0 + ln] += rng.standard_normal(k) * np.exp(-np.arange(k) / (k / 3)) * 0.5
    # Tiefpass-Rauschen als "Fluessigkeit"
    x += lowpass(rng.standard_normal(n), 900) * 0.12 * env_ad(n, 0.02, 0.2, hold=0.2)
    return x


def burp(rng):
    dur = 0.75
    n = int(SR * dur)
    t = t_axis(dur)
    # Impulsfolge mit sinkender Grundfrequenz und Jitter
    f = 88 * (0.62 ** (t / dur)) * (1 + 0.05 * np.sin(2 * np.pi * 6.5 * t))
    ph = np.cumsum(f) / SR
    x = np.zeros(n)
    next_pulse = 0.0
    k = 0
    while k < n:
        if ph[k] >= next_pulse:
            ln = int(SR * 0.0025)
            x[k:k + ln] += np.exp(-np.arange(ln) / (ln / 2)) * rng.uniform(0.8, 1.2)
            next_pulse += 1 + rng.uniform(-0.08, 0.08)
        k += 1
    # Rachen-Resonanzen und Rauheit
    y = resonator(x, 380, 4) * 1.0 + resonator(x, 1150, 6) * 0.5 + resonator(x, 2400, 8) * 0.2
    y *= 1 - 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t))
    y += lowpass(rng.standard_normal(n), 1800) * 0.18 * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t))
    e = env_ad(n, 0.05, 0.16, hold=0.42)
    return y * e


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)
    save("rustle", rustle(rng))
    save("munch", munch(rng))
    save("gulp", gulp(rng))
    save("burp", burp(rng))


if __name__ == "__main__":
    main()
