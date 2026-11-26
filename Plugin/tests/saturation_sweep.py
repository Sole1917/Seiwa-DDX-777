#!/usr/bin/env python3
"""
saturation_sweep.py — curva THD vs LEVEL (P3, Sessione 13c).

Sweep del pot LEVEL 0 -> +20 dB (input 1 kHz -20 dBFS): misura il THD
dell'uscita MIX con i 3 stadi di saturazione fisica (JFET 2SK118, M5221P
soft clip, NE571 gain cell hard limit) ai valori fisici dai datasheet.

THD totale: metodo identico a verify.py (thd_percent) -> confrontabile
1:1 col baseline e col HW (0.033 % a 1 kHz, T4).

Curva attesa (spec):
    LEVEL 0        THD basso (JFET lineare)
    LEVEL medio    THD cresce (JFET quadratico)
    LEVEL alto     THD accelera (M5221 soft-clip + NE571 hard limit)

Regola di decisione (utente): a LEVEL operativo (~+6 dB), THD 1 kHz vs
HW 0.033%:  entro 3 dB -> ok; 3-6 dB -> accettabile (documentare);
> 6 dB -> NON regolare kJfet, indagare la scala analogico-digitale.

Uso:
    python tests/saturation_sweep.py
"""

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "build" / "Release" / "ddx_harness.exe"
OUTDIR = ROOT / "build" / "verify_out"
SR = 96000
F0 = 1000.0
HW_THD_1K = 0.033  # % (misura HW T4, sessione 11/12)

# THD totale: metodo identico a verify.py (stessa funzione -> baseline
# confrontabile 1:1)
sys.path.insert(0, str(ROOT / "tests"))
import verify as V  # noqa: E402


def run_harness(inp, outp, *args):
    outp = Path(outp)
    if outp.exists():
        outp.unlink()
    cmd = [str(HARNESS), str(inp), str(outp)] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"harness failed: {r.stderr}")


def harmonics(x, sr, f0):
    """H2%/H3% (metodo locale, solo per dettaglio nel report)."""
    a, b = int(0.2 * len(x)), int(0.8 * len(x))
    w = x[a:b] * np.hanning(b - a)
    nfft = 1 << int(math.ceil(math.log2(len(w))))
    X = np.abs(np.fft.rfft(w, nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / sr)

    def peak(fr):
        m = (f > fr * 0.99) & (f < fr * 1.01)
        return float(np.max(X[m])) if m.any() else 0.0

    p1 = peak(f0)
    if p1 <= 0:
        return 0.0, 0.0
    return peak(f0 * 2) / p1 * 100.0, peak(f0 * 3) / p1 * 100.0


def main():
    if not HARNESS.exists():
        print(f"harness non trovato: {HARNESS}")
        return 2

    OUTDIR.mkdir(parents=True, exist_ok=True)

    print(f"{'LEVEL':>6} {'THD%':>9} {'H2%':>9} {'H3%':>9}  vs HW 0.033%")
    lv, thd_vals, h2_vals, h3_vals = [], [], [], []

    for db in range(0, 21, 2):
        n = int(3.0 * SR)
        t = np.arange(n) / SR
        x = (0.1 * 10 ** (db / 20.0)) * np.sin(2 * np.pi * F0 * t)
        nf = int(0.01 * SR)
        x[:nf] *= np.linspace(0, 1, nf)
        x[-nf:] *= np.linspace(1, 0, nf)
        inp = OUTDIR / f"sat_in_{db}.wav"
        wavfile.write(str(inp), SR, x.astype(np.float32))
        outp = OUTDIR / f"sat_out_{db}.wav"
        run_harness(inp, outp, "--range", "512", "--delay-level", "1")
        thd_ = V.thd_percent(str(outp), F0)
        sr, y = wavfile.read(str(outp))
        h2_, h3_ = harmonics(y.astype(np.float64), sr, F0)
        d_db = 20 * math.log10(max(thd_, 1e-4) / HW_THD_1K)
        print(f"{db:5d} dB {thd_:8.4f} {h2_:9.4f} {h3_:9.4f}  {d_db:+6.1f} dB")
        lv.append(db)
        thd_vals.append(thd_)
        h2_vals.append(h2_)
        h3_vals.append(h3_)

    # regola di decisione a LEVEL operativo +6 dB
    t6, h2_6, h3_6 = thd_vals[3], h2_vals[3], h3_vals[3]
    d6 = 20 * math.log10(max(t6, 1e-4) / HW_THD_1K)
    print(f"\nTHD a LEVEL +6 dB: {t6:.4f} % (H2 {h2_6:.4f} %, H3 {h3_6:.4f} %)"
          f" -> {d6:+.1f} dB vs HW {HW_THD_1K}%")
    if abs(d6) <= 3:
        print("verdetto: OTTIMO (entro 3 dB dai valori fisici)")
    elif abs(d6) <= 6:
        print("verdetto: ACCETTABILE (3-6 dB: documentare lo scostamento)")
    else:
        print("verdetto: > 6 dB -> NON regolare kJfet: indagare la scala "
              "analogico-digitale / livello di misura HW (vedi report)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.semilogy(lv, thd_vals, "o-", label="THD (2-11h)")
        ax.semilogy(lv, h2_vals, "s--", label="H2", alpha=0.6)
        ax.semilogy(lv, h3_vals, "^--", label="H3", alpha=0.6)
        ax.axhline(HW_THD_1K, color="r", ls=":",
                   label=f"HW 1 kHz: {HW_THD_1K} %")
        ax.axvline(6, color="gray", ls=":", alpha=0.5)
        ax.set_xlabel("LEVEL pot (dB)")
        ax.set_ylabel("THD (%)")
        ax.set_title("DDX-777: THD vs LEVEL (saturazione ingresso 13c)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        png = OUTDIR / "saturation_thd_vs_level.png"
        fig.tight_layout()
        fig.savefig(png, dpi=120)
        print(f"plot: {png}")
    except Exception as e:
        print(f"plot saltato: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
