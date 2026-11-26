#!/usr/bin/env python3
"""bandtrack.py - frequenza di risposta tone-tracked (metodo robusto agli sweep).

Per ogni frame STFT il tono del sweep ha nota frequenza g(t); si misura il
livello del bin a g(t) su ogni segnale. Le curve si confrontano come rapporto
a frequenza uguale => nessun artefatto Hanning-edge, nessun troncamento.

Uso:
  python tests/bandtrack.py
"""
import math
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy import signal as sig

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
SEGNALI = ROOT.parent / "Prep" / "Segnali_Test"
RISULTATI = SEGNALI / "Risultati"
OUTDIR = ROOT / "build" / "verify_out"

F1, F2, TSW = 20.0, 20000.0, 10.0
NPER = 16384


def load(path):
    sr, x = wavfile.read(str(path))
    dt = x.dtype
    x = x.astype(np.float64)
    if x.ndim > 1:
        x = x[:, 0]
    if np.issubdtype(dt, np.integer):
        x = x / (float(np.iinfo(dt).max) + 1.0)
    return sr, x


def ftone(t):
    """Frequenza del sweep Farina al tempo t (0..TSW); nan fuori range."""
    if t < 0.0 or t > TSW:
        return float("nan")
    return F1 * (F2 / F1) ** (t / TSW)


def tone_levels(x, sr, g, nper=NPER):
    """Ritorna (f_tone[], level_dB[]) per frame con tono dentro la finestra."""
    f, t, Z = sig.stft(x, fs=sr, nperseg=nper, noverlap=nper * 3 // 4,
                       boundary=None, padded=False)
    M = np.abs(Z)
    half = (nper / sr) / 2.0
    fs_out, lv_out = [], []
    for tc in t:
        if tc < half or tc > len(x) / sr - half:
            continue
        fc = g(tc)
        if not np.isfinite(fc):
            continue
        if not (f[3] <= fc <= f[-4]):
            continue
        k = int(np.argmin(np.abs(f - fc)))
        fs_out.append(fc)
        lv_out.append(20.0 * np.log10(np.max(M[k - 2:k + 3]) + 1e-12))
    return np.array(fs_out), np.array(lv_out)


def curve_on_grid(f, lv, grid, ref_hz=1000.0):
    """Interpola livelli su griglia log e normalizza a ref_hz."""
    c = np.interp(grid, f, lv)
    c = c - np.interp(ref_hz, grid, c)
    return c


def measure_delay(x, sr, lo=0.04, hi=1.10):
    """Ritardo eco: cross-correlazione envelope con se stesso."""
    env = np.abs(x)
    env = env - env.mean()
    n = len(env)
    max_lag = int(hi * sr)
    # correlazione via FFT
    nfft = 1 << int(math.ceil(math.log2(2 * n)))
    E = np.fft.rfft(env, nfft)
    r = np.fft.irfft(E * np.conj(E), nfft)
    r = r[:max_lag]
    lags = np.arange(max_lag) / sr
    m = (lags >= lo)
    return float(lags[m][np.argmax(r[m])])


def main():
    grid = 1000.0 * 2.0 ** (np.arange(-2.0, 4.01, 1.0 / 24.0))  # 500..16k 1/24ott

    sr, inp = load(SEGNALI / "02_sweep_log_20Hz_20kHz.wav")
    _, hw = load(RISULTATI / "T2 .wav")

    # lead-in: primo punto in cui l'envelope supera 8x la baseline (rumore)
    env_hw = np.convolve(np.abs(hw), np.ones(2000) / 2000, mode="same")
    base = float(np.median(env_hw[: int(0.3 * sr)]))
    L = float(np.argmax(env_hw > base * 8.0)) / sr
    print(f"T2 lead-in dry: {L*1000:.0f} ms")

    g_dry = lambda t: ftone(t - L)
    f_d, lv_d = tone_levels(hw, sr, g_dry)
    hw_dry = curve_on_grid(f_d, lv_d, grid)
    hw_dry = hw_dry - np.interp(1000.0, grid, hw_dry)

    # ritardo eco: prova i candidati noti ( RANGE x FACTOR della sessione 11 )
    # e scegli la curva eco con correlazione più alta vs curva dry
    cands = [0.0664, 0.2481, 0.2627, 0.5288, 0.9605]
    best, best_corr, best_d = None, -2.0, None
    m = (grid >= 500) & (grid <= 10000)
    for d in cands:
        g_e = lambda t, d=d: ftone(t - L - d)
        f_e, lv_e = tone_levels(hw, sr, g_e)
        if len(f_e) < 50:
            continue
        c = curve_on_grid(f_e, lv_e, grid)
        c = c - np.interp(1000.0, grid, c)
        cc = float(np.corrcoef(c[m], hw_dry[m])[0, 1])
        print(f"  cand {d*1000:6.1f} ms -> corr(eco,dry)={cc:.3f}")
        if cc > best_corr:
            best, best_corr, best_d = c, cc, d
    print(f"T2 eco scelto: {best_d*1000:.1f} ms (corr {best_corr:.3f})")
    if best is None:
        print("ERRORE: nessun eco trovato in T2")
        return 1
    hw_echo = best
    hw_dig = hw_echo - hw_dry
    hw_dig = hw_dig - np.interp(1000.0, grid, hw_dig)

    print("\nHW T2 - curva catena digitale (eco/dry, norm 1 kHz):")
    print(f"{'f':>8} {'dry':>7} {'eco':>7} {'dig':>7}")
    for gpt in [500, 707, 1000, 1414, 2000, 2828, 4000, 5657, 8000,
                11314, 16000]:
        i = int(np.argmin(np.abs(grid - gpt)))
        print(f"{grid[i]:8.0f} {hw_dry[i]:7.1f} {hw_echo[i]:7.1f} {hw_dig[i]:7.1f}")

    # ---- OURS: wet vs direct (stessi render harness) ----
    bw = OUTDIR / "band_wet.wav"
    bd = OUTDIR / "band_direct.wav"
    if bw.exists() and bd.exists():
        _, wet = load(bw)
        _, dr = load(bd)
        # delay del nostro render: cross-correlazione wet vs direct
        cc = sig.correlate(wet, dr, mode="full")
        lags = sig.correlation_lags(len(wet), len(dr), mode="full")
        d_ours = float(lags[np.argmax(cc)]) / sr
        print(f"\nOUR delay wet vs direct: {d_ours*1000:.1f} ms")

        g_wet = lambda t: ftone(t - d_ours)
        g_dir = lambda t: ftone(t)
        f_w, lv_w = tone_levels(wet, sr, g_wet)
        f_r, lv_r = tone_levels(dr, sr, g_dir)
        our_wet = curve_on_grid(f_w, lv_w, grid)
        our_dir = curve_on_grid(f_r, lv_r, grid)
        our_dig = our_wet - our_dir
        our_dig = our_dig - np.interp(1000.0, grid, our_dig)

        print("\nOURS - curva catena digitale (wet/direct, norm 1 kHz):")
        print(f"{'f':>8} {'dir':>7} {'wet':>7} {'dig':>7} {'HWdig':>7} {'d':>7}")
        for gpt in [500, 707, 1000, 1414, 2000, 2828, 4000, 5657, 8000,
                    11314, 16000]:
            i = int(np.argmin(np.abs(grid - gpt)))
            dd = our_dig[i] - hw_dig[i]
            print(f"{grid[i]:8.0f} {our_dir[i]:7.1f} {our_wet[i]:7.1f} "
                  f"{our_dig[i]:7.1f} {hw_dig[i]:7.1f} {dd:7.1f}")

        m = (grid >= 400) & (grid <= 14000)
        drift = np.abs(our_dig[m] - hw_dig[m])
        print(f"\nDRIFT ours-vs-HW 400-14k: mean={drift.mean():.2f} dB "
              f"max={drift.max():.2f} dB @ {grid[m][np.argmax(drift)]:.0f} Hz")
        # punto -3 dB
        for name, c in (("HW", hw_dig), ("OURS", our_dig)):
            cut = None
            for i in range(len(grid)):
                if grid[i] > 1500 and c[i] <= -3.0:
                    cut = grid[i]
                    break
            print(f"{name} -3 dB point: {cut:.0f} Hz" if cut else
                  f"{name} -3 dB point: >16 kHz")

    return 0


if __name__ == "__main__":
    sys.exit(main())
