#!/usr/bin/env python3
"""Calibrazione Meccanismi A (kVos) e B (kLo) su T4 — Sessione 12.

Uso:
  python calibrate_mech12.py --kvos <v> --klo <v> [etichetta]
  (default: default calibrati del core, ovvero senza flag k-vos/k-lo)

Genera i toni 100 Hz / 1 kHz / 10 kHz a -20 dBFS RMS (convenzione v3),
li renderizza con l'harness (mix) e riporta per frequenza:
  - A1 (dBFS peak) e armoniche H2..H5 (dB relativa, % del fondamentale)
  - THD totale (convenzione v3: picchi H2..H10)
Target HW (misura T4, sessione 12):
  100 Hz : H2 -54.7 dB (0.184%), H3 -50.9 dB (0.320%), H4 -69.3, H5 -69.2, THD 0.343%
  1 kHz  : H2 -70.3 dB (0.0311%), H3 -77.9, H4 -94.6, H5 -96.8, THD 0.0332%
  10 kHz : H2 -69.3 dB (0.0345%), H3 -81.3, H4 -97.0, THD 0.0352%
"""

import argparse
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "build" / "Release" / "ddx_harness.exe"
OUTDIR = ROOT / "build" / "calib_mech12"
SR = 96000
FREQS = [100, 1000, 10000]
LEVEL = -20.0

N_FFT = 1 << 20
N_SEG = 5
SIGNAL_LEN = N_SEG * N_FFT + 2 * 96000
FADE_SAMPLES = int(0.01 * SR)

HW = {
    100:    {"h2": -54.7, "h3": -50.9, "h4": -69.3, "h5": -69.2, "thd": 0.343},
    1000:   {"h2": -70.3, "h3": -77.9, "h4": -94.6, "h5": -96.8, "thd": 0.0332},
    10000:  {"h2": -69.3, "h3": -81.3, "h4": -97.0, "h5": None,  "thd": 0.0352},
}


def generate_tone(freq, level_dbfs_rms, length=SIGNAL_LEN):
    amplitude = math.sqrt(2) * 10 ** (level_dbfs_rms / 20.0)
    t = np.arange(length) / SR
    x = amplitude * np.sin(2 * np.pi * freq * t)
    fade = np.ones(length)
    fade[:FADE_SAMPLES] = np.linspace(0, 1, FADE_SAMPLES)
    fade[-FADE_SAMPLES:] = np.linspace(1, 0, FADE_SAMPLES)
    x *= fade
    return x.astype(np.float32)


def run_harness(input_path, output_path, kvos, klo):
    if output_path.exists():
        output_path.unlink()
    cmd = [str(HARNESS), str(input_path), str(output_path),
           "--range", "512", "--delay-level", "1", "--emit", "mix"]
    if kvos is not None:
        cmd += ["--k-vos", f"{kvos:.6f}"]
    if klo is not None:
        cmd += ["--k-lo", f"{klo:.6f}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Harness failed: {' '.join(cmd)}\n{result.stderr}")
    return output_path


def harmonics(output_path, f0):
    sr_read, x = wavfile.read(str(output_path))
    if x.ndim > 1:
        x = x[:, 0]
    x = x.astype(np.float64)
    x = x[96000:-96000]
    rows = []
    for i in range(N_SEG):
        s = x[i * N_FFT:(i + 1) * N_FFT]
        w = s * np.hanning(len(s))
        X = np.abs(np.fft.rfft(w, len(s)))
        f = np.fft.rfftfreq(len(s), 1.0 / SR)

        def amp(fr):
            m = (f > fr * 0.99) & (f < fr * 1.01)
            return float(np.max(X[m])) if m.any() else 0.0

        h1 = amp(f0)
        a1_peak = 4.0 * h1 / len(s)
        rel = {k: amp(f0 * k) for k in range(2, 6)}
        thd_har = 0.0
        for k in range(2, 11):
            thd_har += amp(f0 * k) ** 2
        rows.append({
            "a1_dbfs": 20 * math.log10(a1_peak + 1e-30),
            "h2_db": 20 * math.log10(rel[2] / h1 + 1e-30),
            "h3_db": 20 * math.log10(rel[3] / h1 + 1e-30),
            "h4_db": 20 * math.log10(rel[4] / h1 + 1e-30),
            "h5_db": 20 * math.log10(rel[5] / h1 + 1e-30),
            "h2_pct": 100.0 * rel[2] / h1,
            "h3_pct": 100.0 * rel[3] / h1,
            "thd_pct": 100.0 * math.sqrt(thd_har) / h1,
        })
    out = {}
    for key in rows[0]:
        vals = [r[key] for r in rows]
        out[key] = float(np.mean(vals))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kvos", type=float, default=None)
    ap.add_argument("--klo", type=float, default=None)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    if not HARNESS.exists():
        print(f"Harness non trovato: {HARNESS}")
        return 1
    OUTDIR.mkdir(parents=True, exist_ok=True)

    print(f"=== Calibrazione Meccanismi A/B: kvos={args.kvos} klo={args.klo} {args.label} ===")
    for freq in FREQS:
        input_wav = OUTDIR / f"input_{freq}Hz_{int(LEVEL)}dB.wav"
        if not input_wav.exists():
            wavfile.write(str(input_wav), SR, generate_tone(freq, LEVEL))
        out_wav = OUTDIR / f"out_{freq}Hz_kv{args.kvos}_kl{args.klo}.wav"
        run_harness(input_wav, out_wav, args.kvos, args.klo)
        h = harmonics(out_wav, freq)
        hw = HW[freq]
        out_wav.unlink()
        h5_s = f"{h['h5_db']:+7.1f}" if hw["h5"] is not None else "     n/a"
        print(f"{freq:5d} Hz  A1={h['a1_dbfs']:+7.1f} dBFS | "
              f"H2={h['h2_db']:+7.1f} dB ({h['h2_pct']:.4f}%) | "
              f"H3={h['h3_db']:+7.1f} dB ({h['h3_pct']:.4f}%) | "
              f"H4={h['h4_db']:+7.1f} | H5 {h5_s} | "
              f"THD={h['thd_pct']:.4f}%")
        print(f"        HW: H2={hw['h2']:+.1f}  H3={hw['h3']:+.1f}  "
              f"H4={hw['h4']:+.1f}  THD={hw['thd']:.4f}%  | "
              f"gap: H2={h['h2_db']-hw['h2']:+.1f} dB "
              f"H3={h['h3_db']-hw['h3']:+.1f} dB "
              f"THD={20*math.log10(h['thd_pct']/hw['thd']):+.1f} dB")

    # Chiave di calibrazione closed-form (A su dry, A_dry = picco tono -20 dBFS RMS):
    a_dry = math.sqrt(2) * 10 ** (LEVEL / 20.0)
    print(f"\nChiusura forma (A su dry): A_dry = {a_dry:.5f} (peak)")
    print(f"  kVos per H2@1k = 0.0311%:  kVos = {2*0.000311/a_dry:.5f}")
    print(f"  kVos per H2@10k= 0.0345%:  kVos = {2*0.000345/a_dry:.5f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
