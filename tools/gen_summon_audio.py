# Unknown's Halloween - Copyright (C) 2026 DaUnknown-0
# Licensed under GPL-3.0-or-later. See LICENSE for details.
#
# gen_summon_audio.py - Klaenge der Beschwoerung in Hollowmere (28.10.): je Wesen ein Stinger (synthetisch, numpy) und eine
# eigene Sprachzeile (Gemini-TTS, eigene Texte, keine Spiel- oder Serienzitate ausser der vom User gewuenschten Bobby-Zeile).
# Ausgabe: Resources/hw2026/villa_summon/summon_<wesen>.wav (Mono, 22050 Hz, 16 bit). Die Zeilen werden zwischengespeichert
# (tools/_villa/summon_tts/), ein zweiter Lauf ruft Gemini nicht erneut.
# Aufruf: python tools/gen_summon_audio.py [--no-tts]

import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "Resources" / "hw2026" / "villa_summon"
CACHE = HERE / "_villa" / "summon_tts"
sys.path.insert(0, str(HERE.parent.parent / "Assets" / "Cinematics" / "_common"))
SR = 22050
rng = np.random.default_rng(28)

LINES = {
    "diablo": ("Charon", "Say in a very deep, monstrous, growling demonic voice, slow and menacing", "Your fear feeds the fire. Burn!"),
    "baal": ("Algenib", "Say in a rasping, ancient, monstrous demon voice, cold and cruel", "Everything you love will turn to ash."),
    "mephisto": ("Enceladus", "Say in a cold, hissing, whispering demonic voice, full of hatred", "Hatred is the purest poison."),
    "tyrael": ("Orus", "Say in a noble, powerful, resonant archangel voice, solemn and calm", "Justice has answered your call."),
    "castiel": ("Iapetus", "Say in a calm, deep, gravelly, earnest voice with no emotion", "Be not afraid. I am here to watch over you."),
    "bobby": ("Gacrux", "Say in a rough, tired, gruff voice of an old hunter, deadpan", "Saving people, hunting things."),
    "ghost": ("Enceladus", "Whisper in an eerie, breathy ghost voice, slow", "You were not invited."),
}


def t(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, a=0.01, r=0.3):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def noise(sec):
    return rng.standard_normal(int(sec * SR))


def lowpass(x, k):
    # einfache Glaettung (gleitender Mittelwert) als Tiefpass
    k = max(1, int(k))
    return np.convolve(x, np.ones(k) / k, mode="same")


def reverb(x, wet=0.35, room=0.42):
    out = x.copy()
    for d, g in ((0.031, 0.6), (0.047, 0.5), (0.071, 0.42), (0.113, 0.33), (0.167, 0.25), (0.241, 0.18)):
        n = int(d * SR / room * 0.42)
        y = np.zeros_like(x); y[n:] = x[:-n] * g
        out += wet * y
    return out


def boom(sec=1.6, f0=48):
    tt = t(sec)
    f = f0 * np.exp(-tt * 1.4)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) + 0.4 * lowpass(noise(sec), 40)) * np.exp(-tt * 2.2)


def fire(sec=2.0):
    n = noise(sec)
    crackle = (rng.random(len(n)) > 0.9985) * rng.standard_normal(len(n)) * 3
    roar = lowpass(n, 30) * 2.5
    return (roar + lowpass(crackle, 3)) * env(len(n), 0.3, 0.6)


def choir(sec=2.4, root=220.0):
    tt = t(sec)
    y = np.zeros_like(tt)
    for k, ratio in enumerate((1, 1.25, 1.5, 2.0, 2.5)):
        for det in (-0.6, 0.0, 0.7):
            f = root * ratio + det
            y += np.sin(2 * np.pi * f * tt + k) * (0.5 + 0.5 * np.sin(2 * np.pi * 5.2 * tt + k)) * 0.06
    return reverb(y * env(len(tt), 0.7, 0.8), 0.5)


def sparks(sec=1.6):
    n = noise(sec)
    pops = (rng.random(len(n)) > 0.996) * 1.0
    y = np.convolve(pops, np.exp(-np.arange(200) / 25.0) * rng.standard_normal(200), mode="same")
    buzz = np.sign(np.sin(2 * np.pi * 120 * t(sec))) * 0.08 * (rng.random(len(n)) > 0.3)
    return (y * 0.5 + buzz) * env(len(n), 0.01, 0.4)


def shatter(sec=0.9):
    n = noise(sec)
    hp = n - lowpass(n, 6)
    tt = t(sec)
    tinkles = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * (8 + i)) * 0.1 for i, f in enumerate(rng.uniform(2500, 6500, 14)))
    return (hp * np.exp(-tt * 7) * 0.9 + tinkles)


def wings(sec=1.2):
    y = np.zeros(int(sec * SR))
    for k in range(3):
        st = int((0.1 + k * 0.35) * SR)
        burst = lowpass(noise(0.25), 18) * np.hanning(int(0.25 * SR)) * 1.6
        y[st:st + len(burst)] += burst[:len(y) - st]
    return y


def rock_riff():
    """Eigenes Riff im Stil der 70er (Powerchords, verzerrt), keine bekannte Melodie: E5 E5 G5 A5 | E5 D5 E5 (Halbe)."""
    bpm = 132
    beat = 60 / bpm
    notes = [(82.4, 0.5), (82.4, 0.5), (98.0, 0.5), (110.0, 1.0), (82.4, 0.5), (73.4, 0.5), (82.4, 1.5)]
    out = []
    for f, b in notes:
        tt = t(b * beat)
        y = np.zeros_like(tt)
        for mult in (1.0, 1.5, 2.0):
            for det in (-0.4, 0.4):
                y += np.sign(np.sin(2 * np.pi * (f * mult + det) * tt)) * 0.18 + np.sin(2 * np.pi * (f * mult + det) * tt) * 0.2
        y = np.tanh(lowpass(y, 4) * 2.2)
        out.append(y * env(len(tt), 0.005, 0.05) * np.exp(-tt * 0.6))
    riff = np.concatenate(out)
    # Schlagzeug: Bassdrum auf 1 und 3, Snare auf 2 und 4
    drums = np.zeros_like(riff)
    for k in range(int(len(riff) / (beat * SR))):
        st = int(k * beat * SR)
        hit = boom(0.25, 70 if k % 2 == 0 else 180) * (0.9 if k % 2 == 0 else 0.4)
        if k % 2:
            hit = hit + lowpass(noise(0.25), 2) * np.exp(-t(0.25) * 18) * 0.5
        drums[st:st + len(hit)] += hit[:len(drums) - st]
    return riff * 0.7 + drums * 0.6


def wail(sec=1.8):
    tt = t(sec)
    f = 520 + 160 * np.sin(2 * np.pi * 0.7 * tt) + 40 * np.sin(2 * np.pi * 6 * tt)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return reverb(np.sin(ph) * 0.3 * env(len(tt), 0.4, 0.6) + lowpass(noise(sec), 6) * 0.05, 0.6)


def resample(x, sr_from):
    if sr_from == SR:
        return x
    n = int(len(x) * SR / sr_from)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def pitch(x, factor):
    """Tonhoehe und Tempo zusammen (einfaches Umrechnen): < 1 = tiefer und langsamer."""
    n = int(len(x) / factor)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def voice(name, use_tts):
    path = CACHE / f"{name}.npy"
    if path.exists():
        return np.load(path)
    if not use_tts:
        return np.zeros(int(0.2 * SR))
    from gemini_tts import GeminiTTS
    v, style, text = LINES[name]
    # Stil als speech_metadata (Gemini 3): der erste Versuch mit "Say in ...: Text" sprach die Regieanweisung mit
    import io
    import soundfile as sf
    try:
        _s, _rate, _mime, raw = GeminiTTS().say_v3(text, v, style)
        data, sr = sf.read(io.BytesIO(raw), dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)
    except Exception as e:      # noqa: BLE001  (Kontingent des 3er-Modells): Gemini 2.5, dort ist "Say in ...:" die Stilangabe
        print("   v3 nicht verfuegbar:", type(e).__name__, "-> gemini-2.5-flash-preview-tts")
        data, sr = GeminiTTS().say(f"{style}: {text}", v, model="gemini-2.5-flash-preview-tts")
    x = resample(np.asarray(data, dtype=np.float64), sr)
    # Stille vorn und hinten weg
    w = int(0.02 * SR)
    r = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, "same"))
    on = np.nonzero(r > 0.01)[0]
    if len(on):
        x = x[max(0, on[0] - w): on[-1] + 4 * w]
    CACHE.mkdir(parents=True, exist_ok=True)
    np.save(path, x)
    return x


def fx_voice(name, x):
    if name in ("diablo", "baal"):
        x = pitch(x, 0.78)
        sub = pitch(x, 0.5)[:len(x)]                         # eine Oktave darunter, mitlaufend
        sub = np.pad(sub, (0, len(x) - len(sub)))
        x = np.tanh(x * 2.4) * 0.7 + 0.35 * sub
        return reverb(np.tanh(x * 1.5), 0.4)
    if name == "mephisto":
        x = pitch(x, 0.86)
        return reverb(x + 0.3 * np.roll(x, int(0.013 * SR)), 0.45)
    if name == "tyrael":
        return reverb(x + 0.25 * np.roll(x, int(0.019 * SR)), 0.55)
    if name == "castiel":
        return reverb(x, 0.25)
    if name == "ghost":
        return reverb(pitch(x, 0.92), 0.7)
    return x


def mix(*parts):
    """parts: (Startsekunde, Signal, Pegel)"""
    end = max(int(s * SR) + len(sig) for s, sig, _ in parts)
    y = np.zeros(end)
    for s, sig, g in parts:
        st = int(s * SR)
        y[st:st + len(sig)] += sig * g
    return y


def norm(y, peak=0.89):
    m = np.max(np.abs(y)) or 1.0
    return y / m * peak


def save(name, y):
    OUT.mkdir(parents=True, exist_ok=True)
    y = np.clip(norm(y), -1, 1)
    with wave.open(str(OUT / f"summon_{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    print(f"summon_{name}.wav {len(y) / SR:.1f} s")


def main():
    use_tts = "--no-tts" not in sys.argv
    for name in LINES:
        v = fx_voice(name, voice(name, use_tts))
        if name in ("diablo", "baal"):
            y = mix((0, boom(), 1.0), (0.1, fire(2.6), 0.5), (1.3, v, 1.1))
        elif name == "mephisto":
            y = mix((0, boom(1.4, 40), 0.8), (0.2, lowpass(noise(2.5), 12) * env(int(2.5 * SR), 0.6, 0.8), 0.35), (1.2, v, 1.1))
        elif name == "tyrael":
            y = mix((0, choir(3.2, 220), 1.0), (0.0, boom(1.2, 60), 0.4), (1.4, v, 1.2))
        elif name == "castiel":
            y = mix((0, sparks(1.6), 0.9), (0.55, shatter(), 0.8), (0.9, wings(), 0.9), (1.9, v, 1.2))
        elif name == "bobby":
            r = rock_riff()
            y = mix((0, r, 0.8), (len(r) / SR - 0.3, v, 1.25))
        else:
            y = mix((0, wail(), 0.9), (1.0, v, 1.2), (2.4, lowpass(noise(0.4), 2) * np.exp(-t(0.4) * 10), 0.9))
        save(name, y)


if __name__ == "__main__":
    main()
