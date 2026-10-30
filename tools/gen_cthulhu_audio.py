# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
"""Original synthetic storm stinger for Cthulhu; no voice, samples or network calls."""
from pathlib import Path
import wave
import numpy as np


def main():
    rate = 22050
    time = np.arange(int(2.8 * rate)) / rate
    rng = np.random.default_rng(20261029)
    noise = rng.standard_normal(len(time))
    rumble = np.convolve(noise, np.ones(121) / 121, mode="same")
    rumble /= max(0.001, np.max(np.abs(rumble)))
    phase = 2 * np.pi * (67 * time + 36 * (1 - np.exp(-2 * time)))
    low = np.sin(phase) + 0.24 * np.sin(phase * 1.49)
    crack = noise * (np.exp(-time * 35) + 0.7 * np.exp(-np.abs(time - 0.17) * 55))
    envelope = (1 - np.exp(-time * 300)) * np.exp(-time * 1.4)
    samples = (0.34 * low + 0.42 * rumble + 0.24 * crack) * envelope
    samples[-2205:] *= np.linspace(1, 0, 2205)
    pcm = (np.tanh(samples * 1.3) * 0.8 * 32767).astype("<i2")
    output = Path(__file__).resolve().parent.parent / "Resources/hw2026/villa_summon/summon_cthulhu.wav"
    with wave.open(str(output), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(pcm.tobytes())
    print("Original Cthulhu storm stinger generated.")


if __name__ == "__main__":
    main()
