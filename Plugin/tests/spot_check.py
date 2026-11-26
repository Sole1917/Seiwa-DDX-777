#!/usr/bin/env python3
"""spot_check.py — misura THD a 100 Hz / 1 kHz / 10 kHz @ -20 dBFS con flag dati.

usage: python tests/spot_check.py <label> [flag harness extra...]
   esempio: python tests/spot_check.py baseline
   esempio: python tests/spot_check.py krect003 --k-rect 0.003
Variante: --variant full|comp_off|dist_off (default full)
"""
import math
import subprocess
import sys
import tempfile
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
FREQS = [100, 1000, 10000]


def db(x):
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-12))


def gen_tone(freq, level_dbfs_rms=-20.0, length=SIGNAL_LEN):
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


def run(label, extra, variant="full", freqs=FREQS):
    cmd_base = [str(HARNESS)]
    var = {"full": [], "comp_off": ["--char-comp-off"],
           "dist_off": ["--char-dist-off"]}[variant]
    print(f"\n=== {label} | variant={variant} | extra={extra} ===")
    print(f"{'freq':>7} | {'THD %':>9} | {'THD dB':>7} | note")
    res = {}
    with tempfile.TemporaryDirectory() as td:
        for fq in freqs:
            inp = Path(td) / f"in_{fq}.wav"
            outp = Path(td) / f"out_{fq}.wav"
            wavfile.write(str(inp), SR, gen_tone(fq))
            cmd = cmd_base + [str(inp), str(outp),
                               "--range", "512", "--delay-level", "1",
                               "--emit", "mix"] + var + extra
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"  {fq:7d} | ERRORE: {r.stderr.strip()[:120]}")
                res[fq] = None
                continue
            s, x = wavfile.read(str(outp))
            if x.ndim > 1:
                x = x[:, 0]
            x = x.astype(np.float64)[96000:-96000]
            thds = [thd1(x[i * N_FFT:(i + 1) * N_FFT], fq) for i in range(N_SEG)]
            m, sd = float(np.mean(thds)), float(np.std(thds))
            dbv = 20 * math.log10(m / 100) if m > 0 else -200
            res[fq] = m
            print(f"{fq:>7d} | {m:>8.4f}% | {dbv:>7.1f} | ±{sd:.4f}")
    return res


if __name__ == "__main__":
    args = sys.argv[1:]
    label = "test"
    variant = "full"
    extra = []
    i = 1 if args else 0
    if args:
        label = args[0]
    j = i
    while j < len(args):
        if args[j] == "--variant":
            variant = args[j + 1]
            j += 2
        else:
            extra.append(args[j])
            j += 1
    run(label, extra, variant)
