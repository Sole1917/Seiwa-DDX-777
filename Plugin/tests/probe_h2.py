"""Probe H2@20 kHz: tono identico a verify.py (3.0 s, -20 dBFS PEAK) vs calibrazione."""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "build" / "Release" / "ddx_harness.exe"
OUT = ROOT / "build" / "calib_mech12"
OUT.mkdir(parents=True, exist_ok=True)
SR = 96000


def tone(path, freq, amp):
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    x = amp * np.sin(2 * np.pi * freq * t)
    nf = int(0.01 * SR)
    x[:nf] *= np.linspace(0, 1, nf)
    x[-nf:] *= np.linspace(1, 0, nf)
    wavfile.write(str(path), SR, x.astype(np.float32))


def render(inp, outp, extra=()):
    if outp.exists():
        outp.unlink()
    subprocess.run([str(HARNESS), str(inp), str(outp),
                    "--range", "512", "--delay-level", "1"] + list(extra),
                   check=True, capture_output=True, text=True)


def measure(path, f0):
    sr, x = wavfile.read(str(path))
    x = x.astype(np.float64)
    a, b = int(0.2 * len(x)), int(0.8 * len(x))
    x = x[a:b]
    w = x * np.hanning(len(x))
    nfft = 1 << int(math.ceil(math.log2(len(w))))
    X = np.abs(np.fft.rfft(w, nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / sr)

    def pk(fr):
        m = (f > fr * 0.99) & (f < fr * 1.01)
        return float(np.max(X[m])) if m.any() else 0.0

    p1 = pk(f0)
    db = lambda v: 20 * math.log10(max(v, 1e-30))
    print(f"    A1@{f0/1000:.0f}k = {db(p1):7.1f} dBFS | "
          f"H2@{2*f0/1000:4.0f}k = {db(pk(2*f0)):7.1f} dBFS ({100*pk(2*f0)/p1:8.4f}%) | "
          f"H3@{3*f0/1000:4.0f}k = {db(pk(3*f0)):7.1f} dBFS ({100*pk(3*f0)/p1:8.4f}%)")


for tag, amp in [("verify(-20dBFSpeak)", 0.1), ("calib(-20dBFSrms)", 0.141421356)]:
    for f0 in (100, 1000, 10000):
        inp = OUT / f"probe_{tag}_{f0}.wav"
        outp = OUT / f"probeout_{tag}_{f0}.wav"
        tone(inp, f0, amp)
        render(inp, outp)
        print(f"{tag} {f0:5d} Hz:")
        measure(outp, f0)
    # stessa verifica con kVos spento (solo 10 kHz)
    outp = OUT / f"probeout_nokvos_{tag}.wav"
    render(inp, outp, ["--k-vos", "0"])
    print(f"{tag} 10000 Hz (kVos=0):")
    measure(outp, 10000)
