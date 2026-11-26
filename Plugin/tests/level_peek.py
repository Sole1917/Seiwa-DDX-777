#!/usr/bin/env python3
"""Peek dipendente dal livello con i default calibrati Fase 2 (kOpAmp=0.018)."""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "build" / "Release" / "ddx_harness.exe"
SR = 96000
N_FFT = 1 << 20
N_SEG = 5
SIGNAL_LEN = N_SEG * N_FFT + 2 * 96000
FADE = int(0.01 * SR)


def gen_tone(freq, level_dbfs_rms, length=SIGNAL_LEN):
    amp = math.sqrt(2) * 10 ** (level_dbfs_rms / 20.0)
    t = np.arange(length) / SR
    x = amp * np.sin(2 * np.pi * freq * t)
    fade = np.ones(length)
    fade[:FADE] = np.linspace(0, 1, FADE)
    fade[-FADE:] = np.linspace(1, 0, FADE)
    return (x * fade).astype(np.float32)


def thd1(seg, f0, sr=SR):
    w = seg * np.hanning(len(seg))
    X = np.abs(np.fft.rfft(w, 1 << 20))
    f = np.fft.rfftfreq(1 << 20, 1.0 / sr)

    def pk(fr):
        m = (f > fr * 0.99) & (f < fr * 1.01)
        return float(np.max(X[m])) if m.any() else 0.0

    h1 = pk(f0)
    if h1 <= 0:
        return 0.0
    ph = sum(pk(f0 * k) ** 2 for k in range(2, 11) if f0 * k < sr / 2 - 1000)
    return 100.0 * math.sqrt(ph) / h1


def run(freq, level):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "in.wav"
        outp = Path(td) / "out.wav"
        wavfile.write(str(inp), SR, gen_tone(freq, level))
        r = subprocess.run([str(HARNESS), str(inp), str(outp),
                            "--range", "512", "--delay-level", "1",
                            "--emit", "mix"], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"ERRORE {freq} {level}: {r.stderr[:120]}")
            return None
        s, x = wavfile.read(str(outp))
        x = x.astype(np.float64)[96000:-96000]
        thds = [thd1(x[i * N_FFT:(i + 1) * N_FFT], freq) for i in range(N_SEG)]
        return float(np.mean(thds))


if __name__ == "__main__":
    hw = {100: 0.349, 1000: 0.033, 10000: 0.035}
    for freq, level in [(10000, -20), (10000, -24), (10000, -30),
                        (1000, -20), (1000, -24), (100, -20), (100, -24)]:
        v = run(freq, level)
        gap = 20 * math.log10(v / hw[freq]) if v and hw.get(freq) else float("nan")
        print(f"{freq:>7d} Hz {level:5d} dBFS -> {v:.4f}%   gap vs HW: {gap:+.2f} dB")
