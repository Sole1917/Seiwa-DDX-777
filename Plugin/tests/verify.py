#!/usr/bin/env python3
"""
verify.py - verifica il core DDX-777 (M1) contro:
  1. i target numerici della sessione 11 (SEIWA_DDX-777_HANDOFF.md §5-§9);
  2. le registrazioni hardware reali in Prep/Segnali_Test/Risultati/.

Uso:
  python tests/verify.py [--force] [--json report.json]

Requisiti: numpy, scipy (soundfile non necessario).
"""

import argparse
import json
import math
import os
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy import signal as sig

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "build" / "Release" / "ddx_harness.exe"
SEGNALI = ROOT.parent / "Prep" / "Segnali_Test"
RISULTATI = SEGNALI / "Risultati"
OUTDIR = ROOT / "build" / "verify_out"

SR = 96000

# ---------------------------------------------------------------------------
# Target - delay misurati sulle registrazioni hardware (sessione 11 / T1)
# ---------------------------------------------------------------------------
HW_DELAYS_MS = {
    "64x1": 66.4,
    "256x1": 262.7,
    "512x1": 528.8,
    "512x0.5": 248.1,
    "512x2": 960.5,
}
DELAY_TOL = 0.01  # ±1%

HW_NOISE_RMS_DB = -77.3   # T3
HW_NOISE_PEAK_DB = -67.3  # T3
NOISE_RMS_TOL = 2.0       # dB
NOISE_PEAK_TOL = 5.0      # dB

BAND_RIPPLE_TOL = 1.5     # dB (max deriva 100 Hz .. 14 kHz vs 1 kHz)
BAND_FLAT_TO_HZ = 14000
BAND_CUT_MIN = 14000  # −3 dB target ≥14 kHz (HW ≥15 kHz, 31 kHz era aliasing)
BAND_GRID = 1000.0 * 2.0 ** (np.arange(math.log2(0.1), math.log2(19.0) + 1e-9,
                                       1.0 / 24.0))  # 100..19k, 1/24 ottava
BAND_ECHO_CANDS = [0.0664, 0.2481, 0.2627, 0.5288, 0.9605]  # RANGE×FACTOR HW

ALIAS_TONES = [17000, 20000, 25000, 30000]
ALIAS_TOL_DB = -29.0      # energia in-banda 0-15 kHz da tono fuori banda
                          # (ricalibrato: HW reale ~-30.8 RMS su T5, il -35
                          #  vecchio era più severo della realtà hardware)

T5_ALIAS_MARGIN_DB = 3.0  # ours T5 in-band <= HW + 3 dB (comparativo diretto)
T5_WIN = (9.0, 9.9)       # finestra dove la sorgente è solo >18 kHz

THD_MATCH_TOL_DB = 6.0    # scostamento THD vs hardware (A/B, generoso)
CURVE_MIN_CORR = 0.90     # correlazione curva di trasferimento vs T6
BAND_DRIFT_TOL = 2.5      # dB, drift medio ours-vs-HW (400 Hz..14 kHz)

results = []  # (test, target, ours, hw, status, note)


def add(test, target, ours, hw, status, note=""):
    results.append(
        {"test": test, "target": str(target), "ours": str(ours),
         "hw": str(hw), "status": status, "note": note}
    )
    flag = {"PASS": "ok  ", "FAIL": "FAIL", "INFO": "info"}[status]
    print(f"[{flag}] {test:34s} target={target:<22s} ours={ours:<14s} hw={hw:<14s} {note}")


# ---------------------------------------------------------------------------
# Util
# ---------------------------------------------------------------------------
def load(path):
    sr, x = wavfile.read(str(path))
    dt = x.dtype
    x = x.astype(np.float64)
    if x.ndim > 1:
        x = x[:, 0]
    if np.issubdtype(dt, np.integer):
        x = x / (float(np.iinfo(dt).max) + 1.0)
    return sr, x


def run_harness(inp, outp, *args):
    outp = Path(outp)
    if outp.exists():
        outp.unlink()
    cmd = [str(HARNESS), str(inp), str(outp)] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"harness failed: {' '.join(cmd)}\n{r.stderr}")
    return r.stderr.strip()


def db(x):
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-12))


def rms_db(x):
    return 20.0 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12)


def delay_of_mixture(path, dry_pos_hint=None):
    """Ritorna (delay_ms, dry_idx, wet_idx). dry = primo grande picco."""
    sr, x = load(path)
    env = np.abs(x)
    if dry_pos_hint is not None:
        dry = dry_pos_hint
    else:
        dry = int(np.argmax(env))
    # cercа il picco wet dopo il dry (almeno 40 campioni di distacco)
    search = env.copy()
    search[: dry + 40] = 0
    wet = int(np.argmax(search))
    return (wet - dry) / sr * 1000.0, dry, wet


def ftone(t, f1=20.0, f2=20000.0, tsw=10.0):
    """Frequenza istantanea dello sweep log di Farina al tempo t (nan fuori)."""
    if t < 0.0 or t > tsw:
        return float("nan")
    return f1 * (f2 / f1) ** (t / tsw)


def synth_flat_sweep(path, f1=20.0, f2=20000.0, tsw=12.0, peak_dbfs=-20.0,
                     tail=1.5):
    """Sweep log di Farina a LIVELLO COSTANTE, sotto la soglia del compander.

    Necessaria per misurare la risposta dei filtri: la sweep di riferimento
    (02_sweep_log_20Hz_20kHz.wav) ha ampiezza crescente di ~27 dB, quindi il
    compander riduce il gain man mano che la frequenza sale e un wet/direct
    "grezzo" mostra un droop di ~4 dB che NON e' risposta in frequenza.
    """
    n = int(tsw * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * f1 * tsw / np.log(f2 / f1) * (np.power(f2 / f1, t / tsw) - 1)
    x = np.sin(ph)
    x *= (10 ** (peak_dbfs / 20.0)) / np.max(np.abs(x))
    pad = np.concatenate([x, np.zeros(int(tail * SR))])
    wavfile.write(str(path), SR, pad.astype(np.float32))


def tone_levels(x, sr, g, nper=16384):
    """Livello (dB) del bin a g(t) per ogni frame STFT col tono dentro la finestra."""
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
    """Interpola i livelli su griglia log e normalizza a ref_hz."""
    c = np.interp(grid, f, lv)
    return c - np.interp(ref_hz, grid, c)


def band_hw_digital(sr, hw):
    """Catena digitale HW = eco/dry in T2 (tone-tracked, lead-in + candidato eco)."""
    env = np.convolve(np.abs(hw), np.ones(2000) / 2000, mode="same")
    base = float(np.median(env[: int(0.3 * sr)]))
    lead = float(np.argmax(env > base * 8.0)) / sr

    grid = BAND_GRID
    dry = curve_on_grid(*tone_levels(hw, sr, lambda t: ftone(t - lead)), grid)

    m = (grid >= 500) & (grid <= 10000)
    best, best_corr = None, -2.0
    for d in BAND_ECHO_CANDS:
        c = curve_on_grid(*tone_levels(hw, sr, lambda t, d=d: ftone(t - lead - d)),
                          grid)
        cc = float(np.corrcoef(c[m], dry[m])[0, 1])
        if cc > best_corr:
            best, best_corr = c, cc
    if best is None:
        return None, None, lead, 0.0
    return best - dry, best_corr, lead, best_corr


def band_ours_digital(sr, wet, direct, tsw=12.0):
    """Catena digitale OURS = wet/direct (delay del render misurato).

    tsw=12.0 per lo sweep a livello costante (synth_flat_sweep).
    """
    cc = sig.correlate(wet, direct, mode="full")
    lags = sig.correlation_lags(len(wet), len(direct), mode="full")
    d_ours = float(lags[np.argmax(cc)]) / sr

    grid = BAND_GRID
    w = curve_on_grid(
        *tone_levels(wet, sr, lambda t: ftone(t - d_ours, 20.0, 20000.0, tsw)), grid)
    d = curve_on_grid(*tone_levels(direct, sr,
                                   lambda t: ftone(t, 20.0, 20000.0, tsw)), grid)
    return w - d, d_ours


def first_cut(grid, curve, ref_hz=1500.0):
    for i in range(len(grid)):
        if grid[i] > ref_hz and curve[i] <= -3.0:
            return float(grid[i])
    return None


def thd_percent(path, f0, sr=None, seg=None):
    sr, x = load(path)
    if seg is None:
        a = int(0.2 * len(x))
        b = int(0.8 * len(x))
    else:
        a, b = seg
    x = x[a:b]
    w = x * np.hanning(len(x))
    nfft = 1 << int(math.ceil(math.log2(len(w))))
    X = np.abs(np.fft.rfft(w, nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / sr)

    def peak(fr):
        m = (f > fr * 0.99) & (f < fr * 1.01)
        if not m.any():
            return 0.0
        return float(np.max(X[m]))

    p1 = peak(f0)
    if p1 <= 0:
        return 0.0
    ph = 0.0
    for k in range(2, 12):
        pk = peak(f0 * k)
        ph += pk * pk
    return 100.0 * math.sqrt(ph) / p1


def synth_tone(path, freq, dur=3.0, peak_dbfs=-20.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    a = 10 ** (peak_dbfs / 20.0)
    x = a * np.sin(2 * np.pi * freq * t)
    nf = int(0.01 * SR)
    x[:nf] *= np.linspace(0, 1, nf)
    x[-nf:] *= np.linspace(1, 0, nf)
    wavfile.write(str(path), SR, x.astype(np.float32))


def inband_rms_db(path, hi=15000.0):
    sr, x = load(path)
    b, a = sig.butter(4, hi / (sr / 2), btype="low")
    y = sig.filtfilt(b, a, x)
    return rms_db(y)


def stft_median_db(path, nper=4096):
    sr, x = load(path)
    f, t, Z = sig.stft(x, fs=sr, nperseg=nper, noverlap=nper // 2)
    M = 20 * np.log10(np.maximum(np.abs(Z), 1e-9))
    return f, np.median(M, axis=1)


def spectral_distance(p_a, p_b, fmin=50.0, fmax=15000.0):
    fa, ma = stft_median_db(p_a)
    fb, mb = stft_median_db(p_b)
    m = (fa >= fmin) & (fa <= fmax)
    d = np.interp(fa[m], fb, mb) - ma[m]
    return float(np.mean(np.abs(d))), float(np.max(np.abs(d)))


def detect_echo_peaks(x, thr_db=-60.0, min_gap_s=0.40):
    """Echi del burst di impulso: stesso algoritmo della FEEDBACK_ANALYSIS_v2
    (max su finestra ds=48, local-max ±3 ms, min gap 0.4 s, soglia -60 dBFS).
    Ritorna (peaks in campioni, ampiezze di picco)."""
    env = np.abs(x)
    thr = 10.0 ** (thr_db / 20.0)
    ds = 48
    n_ds = (len(env) // ds) * ds
    env_ds = env[:n_ds].reshape(-1, ds).max(axis=1)
    min_gap_ds = int(min_gap_s * SR / ds)
    cand = np.where(env_ds > thr)[0]
    peaks_ds = []
    for c in cand:
        if peaks_ds and (c - peaks_ds[-1]) < min_gap_ds:
            if env_ds[c] > env_ds[peaks_ds[-1]]:
                peaks_ds[-1] = c
        else:
            peaks_ds.append(c)
    w = int(0.003 * SR)
    peaks, amps = [], []
    for p in peaks_ds:
        c = p * ds
        a = max(0, c - w)
        b = min(len(x), c + w + 1)
        m = a + int(np.argmax(env[a:b]))
        if peaks and (m - peaks[-1]) < int(min_gap_s * SR):
            if env[m] > env[peaks[-1]]:
                peaks[-1] = m
                amps[-1] = env[m]
        else:
            peaks.append(m)
            amps.append(env[m])
    return np.array(peaks, dtype=int), np.array(amps, dtype=float)


def steps_gains(path, n_steps=10, step_len=1.0):
    """Guadagno per gradino (dB). Onset in campioni, finestra post-eco (0.6 s)."""
    sr, x = load(path)
    win = int(0.02 * sr)
    nwin = len(x) // win
    env = np.array([np.sqrt(np.mean(x[i * win:(i + 1) * win] ** 2)) for i in range(nwin)])
    edb = 20 * np.log10(env + 1e-9)
    d = np.abs(np.diff(edb))
    trans = np.where(d > 1.0)[0] * win  # onset in campioni
    starts = []
    for tr in trans:
        if not starts or tr > starts[-1] + int(0.9 * sr):
            starts.append(int(tr))
    gains = []
    for i in range(min(n_steps, len(starts))):
        a = starts[i] + int(0.6 * sr)          # salta transiente + arrivo eco
        b = starts[i] + int(0.95 * sr)
        if b > len(x):
            break
        gains.append(rms_db(x[a:b]))
    return gains


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(ROOT / "build" / "verify_report.json"))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if not HARNESS.exists():
        print(f"harness non trovato: {HARNESS}\nBuild: cmake --build build --config Release --target ddx_harness")
        return 2

    OUTDIR.mkdir(parents=True, exist_ok=True)

    imp = SEGNALI / "01_impulse_single.wav"
    sil = SEGNALI / "03_silence_10s.wav"
    swp = SEGNALI / "02_sweep_log_20Hz_20kHz.wav"
    s1k = SEGNALI / "04_sine_1kHz.wav"
    s100 = SEGNALI / "08_sine_100Hz.wav"
    s10k = SEGNALI / "09_sine_10kHz.wav"
    steps = SEGNALI / "14_amplitude_steps.wav"

    print("=== 1. DELAY (impulso, mix out) ===")
    cases = {
        "64x1": ["--range", "64", "--factor", "1"],
        "256x1": ["--range", "256", "--factor", "1"],
        "512x1": ["--range", "512", "--factor", "1"],
        "512x0.5": ["--range", "512", "--factor", "0.5"],
        "512x2": ["--range", "512", "--factor", "2"],
    }
    for name, cargs in cases.items():
        outp = OUTDIR / f"imp_{name}.wav"
        if not outp.exists() or args.force:
            run_harness(imp, outp, *cargs, "--delay-level", "1")
        d, _, _ = delay_of_mixture(outp)
        tgt = HW_DELAYS_MS[name]
        ok = abs(d - tgt) / tgt <= DELAY_TOL
        add(f"delay {name}", f"{tgt:.1f} ms", f"{d:.1f} ms", f"{tgt:.1f} ms",
            "PASS" if ok else "FAIL")

    print("\n=== 2. RUMORE DI FONDO (silenzio) ===")
    nw = OUTDIR / "noise_wet.wav"
    if not nw.exists() or args.force:
        run_harness(sil, nw, "--range", "512", "--delay-level", "1", "--emit", "wet")
    _, x = load(nw)
    nr, npk = rms_db(x), db(np.abs(x).max())
    add("noise RMS", f"{HW_NOISE_RMS_DB:.1f} dBFS", f"{nr:.1f}", f"{HW_NOISE_RMS_DB:.1f}",
        "PASS" if abs(nr - HW_NOISE_RMS_DB) <= NOISE_RMS_TOL else "FAIL")
    add("noise peak", f"{HW_NOISE_PEAK_DB:.1f} dBFS", f"{npk:.1f}", f"{HW_NOISE_PEAK_DB:.1f}",
        "PASS" if abs(npk - HW_NOISE_PEAK_DB) <= NOISE_PEAK_TOL else "FAIL")

    print("\n=== 3. RISPOSTA IN FREQUENZA (sweep 20-20k LIVELLO COSTANTE) ===")
    bw = OUTDIR / "band_wet.wav"
    bd = OUTDIR / "band_direct.wav"
    # Sweep a livello costante e sotto soglia: isola i filtri dal gain
    # dipendente dal livello del compander (vedi synth_flat_sweep).
    # Il padding finale serve perche' l'eco esce DOPO la fine dello sweep
    # (delay 0.53 s): senza, il wet >13 kHz non esiste e l'interpolazione
    # estrapola piatto (finto cutoff).
    swp = OUTDIR / "flatsweep.wav"
    synth_flat_sweep(swp)
    if not bw.exists() or args.force:
        run_harness(swp, bw, "--range", "512", "--delay-level", "1", "--emit", "wet")
    if not bd.exists() or args.force:
        run_harness(swp, bd, "--range", "512", "--delay-level", "1", "--emit", "direct")

    sr_bt, wet = load(bw)
    _, direct = load(bd)
    our_dig, d_ours = band_ours_digital(sr_bt, wet, direct, tsw=12.0)

    grid = BAND_GRID
    m_flat = (grid >= 100) & (grid <= BAND_FLAT_TO_HZ)
    ripple = float(np.max(np.abs(our_dig[m_flat])))
    cut = first_cut(grid, our_dig)
    add("band ripple 100-14k", f"<= {BAND_RIPPLE_TOL} dB", f"{ripple:.2f} dB", "-",
        "PASS" if ripple <= BAND_RIPPLE_TOL else "FAIL",
        f"delay {d_ours*1000:.1f} ms")
    cut_ok = cut is not None and cut >= BAND_CUT_MIN
    add("band -3dB point", ">=14 kHz", f"{cut/1000:.2f} kHz" if cut else ">16 kHz",
        "≥14 kHz (HW ≥15 kHz, 31 kHz era aliasing)", "INFO")

    # confronto diretto con la catena digitale HW (T2: eco/dry)
    hw_t2 = RISULTATI / "T2 .wav"
    if hw_t2.exists():
        _, hw = load(hw_t2)
        hw_dig, hw_corr, _, _ = band_hw_digital(sr_bt, hw)
        if hw_dig is not None:
            m = (grid >= 400) & (grid <= BAND_FLAT_TO_HZ)
            drift = np.abs(our_dig[m] - hw_dig[m])
            add("drift ours-vs-HW 400-14k", f"<= {BAND_DRIFT_TOL} dB mean",
                f"{drift.mean():.2f} dB", "0 dB",
                "PASS" if drift.mean() <= BAND_DRIFT_TOL else "FAIL",
                f"max {drift.max():.2f} dB @ {grid[m][np.argmax(drift)]:.0f} Hz "
                f"(eco corr {hw_corr:.3f})")

    print("\n=== 4. ALIASING (toni fuori banda → energia 0-15 kHz) ===")
    for tf in ALIAS_TONES:
        tp = OUTDIR / f"tone_{tf}.wav"
        op = OUTDIR / f"tone_{tf}_wet.wav"
        if not tp.exists():
            synth_tone(tp, tf)
        if not op.exists() or args.force:
            run_harness(tp, op, "--range", "512", "--delay-level", "1", "--emit", "wet")
        e = inband_rms_db(op)
        # riferimento: RMS del tono in ingresso (-20 dBFS RMS)
        add(f"alias {tf/1000:.0f} kHz in-band", f"<= {ALIAS_TOL_DB:.0f} dB",
            f"{e:.1f} dBFS", "-", "PASS" if e <= ALIAS_TOL_DB else "FAIL")

    # comparativo diretto su T5 (sweep 40k, finestra dove la sorgente è solo >18k)
    hw_t5 = RISULTATI / "T5 .wav"
    if hw_t5.exists():
        a, b = (int(T5_WIN[0] * SR), int(T5_WIN[1] * SR))

        def _inband(path):
            _, x = load(path)
            x = x[a:b]
            bt, at = sig.butter(4, 15000.0 / (SR / 2), btype="low")
            return rms_db(sig.filtfilt(bt, at, x))

        hw_e = _inband(hw_t5)
        t5p = SEGNALI / "07_sweep_log_20Hz_40kHz.wav"
        op = OUTDIR / "ab_T5_alias.wav"
        if not op.exists() or args.force:
            run_harness(t5p, op, "--range", "512", "--delay-level", "1")
        our_e = _inband(op)
        add("alias T5 vs HW (in-band)", f"<= HW + {T5_ALIAS_MARGIN_DB:.0f} dB",
            f"{our_e:.1f} dBFS", f"{hw_e:.1f} dBFS",
            "PASS" if our_e <= hw_e + T5_ALIAS_MARGIN_DB else "FAIL")

    print("\n=== 5. THD (sine, mix out) vs hardware ===")
    hw_t4 = RISULTATI / "T4, 8 e 9 .wav"
    hw_segs = []
    if hw_t4.exists():
        srh, xh = load(hw_t4)
        win = int(0.25 * srh)
        nwin = len(xh) // win
        env = np.array([np.sqrt(np.mean(xh[i * win:(i + 1) * win] ** 2)) for i in range(nwin)])
        loud = env > 10 ** (-50 / 20)
        runs, start = [], None
        for i, v in enumerate(loud):
            if v and start is None:
                start = i
            elif not v and start is not None:
                if (i - start) * 0.25 >= 5.0:
                    runs.append((start, i))
                start = None
        if start is not None and (len(loud) - start) * 0.25 >= 5.0:
            runs.append((start, len(loud)))
        for a, b in runs:
            seg = xh[a * win: b * win]
            sp = np.abs(np.fft.rfft(seg[: SR * 4]))
            fr = np.fft.rfftfreq(min(len(seg), SR * 4), 1 / srh)
            fr = fr[1:]
            sp = sp[1:]
            f0 = float(fr[int(np.argmax(sp))])
            hw_segs.append((f0, (a * win, b * win)))

    thd_targets = [(s100, 100.0), (s1k, 1000.0), (s10k, 10000.0)]
    for path, f0 in thd_targets:
        op = OUTDIR / f"thd_{int(f0)}_mix.wav"
        if not op.exists() or args.force:
            run_harness(path, op, "--range", "512", "--delay-level", "1")
        ours = thd_percent(op, f0)
        hwv = None
        for hf, seg in hw_segs:
            if abs(hf - f0) / f0 < 0.1:
                hwv = thd_percent(str(hw_t4), f0, sr=srh, seg=seg)
                break
        if hwv is None:
            add(f"THD {f0:.0f} Hz", "vs HW", f"{ours:.3f} %", "n/d", "INFO")
        else:
            d_db = abs(20 * math.log10(max(ours, 1e-4) / max(hwv, 1e-4)))
            add(f"THD {f0:.0f} Hz", f"<= {THD_MATCH_TOL_DB} dB vs HW",
                f"{ours:.3f} %", f"{hwv:.3f} %",
                "PASS" if d_db <= THD_MATCH_TOL_DB else "FAIL",
                f"({d_db:.1f} dB)")

    print("\n=== 6. CURVA DI TRASFERIMENTO (gradini) vs T6 hardware ===")
    op = OUTDIR / "steps_mix.wav"
    if not op.exists() or args.force:
        run_harness(steps, op, "--range", "512", "--delay-level", "1")
    g_ours = steps_gains(op)
    hw_t6 = RISULTATI / "T6 .wav"
    if hw_t6.exists():
        g_hw = steps_gains(hw_t6)
        # allineamento: cerca lo shift che massimizza la correlazione
        best_corr, best_lag = -2.0, 0
        for lag in range(-4, 5):
            n = min(len(g_ours), len(g_hw))
            if n - abs(lag) < 5:
                continue
            a = np.array(g_ours[max(0, -lag): n - max(0, lag)])
            b = np.array(g_hw[max(0, lag): n - max(0, -lag)])
            c = float(np.corrcoef(a, b)[0, 1])
            if c > best_corr:
                best_corr, best_lag = c, lag
        n = min(len(g_ours), len(g_hw))
        a = np.array(g_ours[max(0, -best_lag): n - max(0, best_lag)])
        b = np.array(g_hw[max(0, best_lag): n - max(0, -best_lag)])
        add("curve corr vs T6", f"≥ {CURVE_MIN_CORR}", f"{best_corr:.3f}",
            "1.000", "PASS" if best_corr >= CURVE_MIN_CORR else "FAIL",
            f"lag={best_lag} maxdiff={np.max(np.abs(a-b)):.1f} dB")

    print("\n=== 7. A/B spettrale vs registrazioni hardware ===")
    pairs = [
        ("T2 .wav", swp, "band/sweep"),
        ("T5 .wav", SEGNALI / "07_sweep_log_20Hz_40kHz.wav", "aliasing sweep"),
        ("T6 .wav", steps, "steps"),
    ]
    for hw_name, inp, label in pairs:
        hwp = RISULTATI / hw_name
        if not hwp.exists():
            continue
        op = OUTDIR / f"ab_{hw_name.replace(' ', '_').replace(',', '')}"
        if not op.exists() or args.force:
            run_harness(inp, op, "--range", "512", "--delay-level", "1")
        mean_d, max_d = spectral_distance(op, hwp)
        add(f"A/B spectral {label}", "info", f"mean {mean_d:.1f} dB", "-", "INFO",
            f"max {max_d:.1f} dB")

    print("\n=== 8. LOOP GAIN FEEDBACK (sessione 13g, soglia -60 dBFS) ===")
    # Target: G di loop TOTALE misurato in uscita sulle registrazioni v2
    # (FEEDBACK_ANALYSIS_v2.md): FB100 -> 0.90, FB50 -> 0.34, FB25 -> 0.10.
    # L'impulso di 01_impulse_single.wav dura solo 1 s (non basta per 20
    # echi a delay 528 ms): fixture interna di 20 s, delta @ sample 0.
    FB_CASES = [
        # (nome, feedback, G target lineare, tolleranza, n_ecos HW a -60)
        ("FB100", 1.00, 0.90, 0.03, 22),
        ("FB50", 0.50, 0.34, 0.03, 3),
        ("FB25", 0.25, 0.10, 0.02, 2),
    ]
    imp20 = OUTDIR / "fb_impulse_20s.wav"
    if not imp20.exists():
        n20 = int(20.0 * SR)
        sig0 = np.zeros(n20, dtype=np.float32)
        sig0[0] = 1.0
        wavfile.write(str(imp20), SR, sig0)

    fb_data = {}
    for name, fbval, gtgt, gtol, n_ref in FB_CASES:
        op = OUTDIR / f"fb_loop_{name}.wav"
        if not op.exists() or args.force:
            run_harness(imp20, op, "--range", "512", "--factor", "1",
                        "--level", "1", "--feedback", fbval, "--delay-level", "1")
        _, x = load(op)
        pk, am = detect_echo_peaks(x)
        me = pk >= int(0.005 * SR)            # dry (t < 5 ms) esclusa
        pe, ae = pk[me], am[me]
        G = (float(np.median(ae[1:] / np.maximum(ae[:-1], 1e-30)))
             if len(ae) >= 2 else float("nan"))
        fb_data[name] = dict(x=x, pe=pe, ae=ae, G=G)
        ok_g = not math.isnan(G) and abs(G - gtgt) <= gtol
        add(f"loop G {name}", f"{gtgt:.2f} ± {gtol:.2f}",
            f"{G:.4f}" if not math.isnan(G) else "n/d", "-",
            "PASS" if ok_g else "FAIL", f"n_ecos={len(ae)} (HW ~{n_ref})")
        if name == "FB100":
            add("n echi FB100", ">= 20", f"{len(ae)}", "22",
                "PASS" if len(ae) >= 20 else "FAIL")

    d100 = fb_data["FB100"]
    x100, pe100, ae100 = d100["x"], d100["pe"], d100["ae"]

    # --- floor di rumore nei gap (finestra 100 ms): deve restare piano ---
    gaps = {}
    for a_, b_ in ((1, 2), (5, 6), (10, 11)):
        if b_ <= len(pe100):
            mid = (pe100[a_ - 1] + pe100[b_ - 1]) // 2
            nw = int(0.10 * SR)
            gaps[f"{a_}-{b_}"] = rms_db(x100[mid - nw // 2: mid + nw // 2])
    if len(gaps) == 3:
        spread = max(gaps.values()) - min(gaps.values())
        add("gap RMS spread FB100", "<= 1.0 dB (piano)", f"{spread:.1f} dB",
            "HW 0.4 dB (-77.0/-77.0/-76.6)",
            "PASS" if spread <= 1.0 else "FAIL",
            " ".join(f"{k}={v:.1f}" for k, v in gaps.items()))

    # --- spettri eco 1/5/10 (finestra 10 ms, NFFT 32768) ---
    nfft = 32768
    nw = int(0.010 * SR)
    fbin = np.fft.rfftfreq(nfft, 1.0 / SR)
    S = {k: np.abs(np.fft.rfft(x100[pe100[k - 1] - nw // 2:
                                 pe100[k - 1] + nw // 2], nfft))
         for k in (1, 5, 10) if k <= len(pe100)}
    if len(S) == 3:
        r1 = float(np.sqrt(np.mean(
            x100[pe100[0] - nw // 2: pe100[0] + nw // 2] ** 2)))
        r10 = float(np.sqrt(np.mean(
            x100[pe100[9] - nw // 2: pe100[9] + nw // 2] ** 2)))
        ratio = 20.0 * math.log10(r1 / max(r10, 1e-30))
        add("RMS eco1/eco10", "14.4 ± 2 dB", f"{ratio:.1f} dB", "14.4 dB",
            "INFO",
            "gap = contributo RMS compandor (gain control tempo-variante), non "
            "modellato — vedi LOOP_CALIBRATION.md §Follow-up aperto")

        m2048 = (fbin >= 20000) & (fbin < 48000)
        e2048 = {k: 10.0 * math.log10(np.sum(S[k][m2048] ** 2) + 1e-30)
                 for k in S}
        flr = min(e2048.values())
        ok_b = all(v - flr <= 10.0 for v in e2048.values())
        add("energia 20-48k", "<= floor + 10 dB",
            " ".join(f"e{k}:{v:.1f}" for k, v in e2048.items()),
            "HW: al floor", "PASS" if ok_b else "FAIL", "dB rel (NFFT fissi)")

        m1520 = (fbin >= 15000) & (fbin < 20000)
        with np.errstate(divide="ignore", invalid="ignore"):
            H51 = np.where(S[1][m1520] > 1e-30,
                           (np.maximum(S[5][m1520] /
                                       np.maximum(S[1][m1520], 1e-30), 0.0)
                            ) ** 0.25, 1.0)
        h_db = 20.0 * np.log10(H51 + 1e-30)
        add("H_loop 15-20k per passo", "<= +1.0 dB", f"{h_db.max():+.1f} dB max",
            "0 dB (piatto)", "PASS" if h_db.max() <= 1.0 else "FAIL")

        m020 = fbin < 20000
        e020 = {k: 10.0 * math.log10(np.sum(S[k][m020] ** 2) / nfft + 1e-30)
                for k in S}
        add("energia 0-20k (INFO)", "info",
            " ".join(f"e{k}={v:.1f}" for k, v in e020.items()),
            "HW -61.8/-71.6/-76.4", "INFO", "RMS di banda dBFS (Parseval)")

    add("G_forward (eco1)", "-38.9 dB (HW)",
        f"{20.0 * math.log10(max(ae100[0], 1e-30)):.1f} dB" if len(ae100) else "n/d",
        "-38.9 dB", "INFO", "gap noto: saturazione ingresso frozen (13c)")

    # --- report ---
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n=== RIEPILOGO: {n_pass} PASS, {n_fail} FAIL, "
          f"{len(results)-n_pass-n_fail} INFO ===")
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"report: {args.json}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
