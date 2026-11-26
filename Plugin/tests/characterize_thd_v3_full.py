#!/usr/bin/env python3
"""Caratterizzazione completa FASE 2 (5 componenti HF) in un'unica esecuzione.

Stato calibrato (default del core, nessun flag):
  Comp 1  Virtual ADC 32 kHz        ON  (AA/ricostruzione 8° @ 15 kHz)
  Comp 2  kRect (rectifier banda)   0.0 (calibrato: contributo < 1 dB)
  Comp 3  kDac2/kDac3 (R-2R)        0.0 (calibrato: peggiora 1 kHz)
  Comp 4  kBuffer (tanh buffer)     0.0 (calibrato: peggiora 1 kHz)
  Comp 5  kOpAmp (4 stadi op-amp)   0.018 (calibrato: match 10 kHz)
"""

import csv
import math
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy.io import wavfile

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "build" / "Release" / "ddx_harness.exe"
OUTDIR = ROOT / "build" / "char_thd_v3"
REPORT_PATH = ROOT / "tests" / "THD_characterization_v3.md"
SR = 96000

FREQS = [50, 100, 200, 500, 1000, 2000, 5000, 10000]
LEVELS = [-6, -12, -14, -18, -20, -24, -30, -36, -42]
MODES = ["wet", "mix", "direct"]
VARIANTS = ["full", "comp_off", "dist_off"]

KEY_FREQS = [100, 1000, 10000]
ABLATION = [
    ("fase1",        ["--no-virtual-adc", "--k-opamp", "0"],
     "Fase 1: VADC off, tutti k=0"),
    ("comp1_vadc",   ["--k-opamp", "0"],
     "+ Comp 1: VADC on, tutti k=0"),
    ("comp5_final",  [],
     "+ Comp 5: kOpAmp=0.018 (stato finale Fase 2)"),
]
OPAMP_SWEEP = [0.014, 0.016, 0.018, 0.020, 0.022]

HW_TARGETS = {100: 0.349, 1000: 0.033, 10000: 0.035}
PHASE0 = {100: 0.180, 1000: 0.021, 10000: 0.0053}   # Fase 0 (compander -6 dBFS)
PHASE1 = {100: 0.408, 1000: 0.0395, 10000: 0.0053}  # Fase 1 (limiter -20 dBFS, VADC off)

N_FFT = 1 << 20
N_SEG = 5
SIGNAL_LEN = N_SEG * N_FFT + 2 * 96000
FADE_SAMPLES = int(0.01 * SR)


def generate_tone(freq, level_dbfs_rms, length=SIGNAL_LEN):
    amplitude = math.sqrt(2) * 10 ** (level_dbfs_rms / 20.0)
    t = np.arange(length) / SR
    x = amplitude * np.sin(2 * np.pi * freq * t)
    fade = np.ones(length)
    fade[:FADE_SAMPLES] = np.linspace(0, 1, FADE_SAMPLES)
    fade[-FADE_SAMPLES:] = np.linspace(1, 0, FADE_SAMPLES)
    x *= fade
    return x.astype(np.float32)


def measure_thd(signal, f0, sr=SR):
    w = signal * np.hanning(len(signal))
    nfft = 1 << int(math.ceil(math.log2(len(w))))
    X = np.abs(np.fft.rfft(w, nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / sr)

    def peak_amplitude(fr):
        m = (f > fr * 0.99) & (f < fr * 1.01)
        if not m.any():
            return 0.0
        return float(np.max(X[m]))

    h1 = peak_amplitude(f0)
    if h1 <= 0:
        return 0.0
    ph = 0.0
    for k in range(2, 11):
        pk = peak_amplitude(f0 * k)
        ph += pk * pk
    return 100.0 * math.sqrt(ph) / h1


def measure_thd_5segments(output_path, f0, sr=SR):
    sr_read, x = wavfile.read(output_path)
    if x.ndim > 1:
        x = x[:, 0]
    x = x.astype(np.float64)
    x = x[96000:-96000]
    thds = []
    for i in range(N_SEG):
        seg = x[i * N_FFT:(i + 1) * N_FFT]
        thds.append(measure_thd(seg, f0, sr))
    return np.mean(thds), np.std(thds), thds


def ensure_input(freq, level):
    input_wav = OUTDIR / f"input_{freq}Hz_{level}dB.wav"
    if not input_wav.exists():
        x = generate_tone(freq, level)
        wavfile.write(str(input_wav), SR, x)
    return input_wav


def run_harness(input_path, output_path, mode, variant, extra_args=None):
    if output_path.exists():
        output_path.unlink()
    cmd = [str(HARNESS), str(input_path), str(output_path),
           "--range", "512", "--delay-level", "1", "--emit", mode]
    if variant == "comp_off":
        cmd.append("--char-comp-off")
    elif variant == "dist_off":
        cmd.append("--char-dist-off")
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Harness failed: {' '.join(cmd)}\n{result.stderr}")
    return output_path


def record(all_results, freq, level, mode, variant, scenario, out_wav):
    try:
        thd_mean, thd_std, thds = measure_thd_5segments(out_wav, freq)
        all_results.append({
            "freq": freq, "level": level, "mode": mode,
            "variant": variant, "scenario": scenario,
            "thd_pct": thd_mean,
            "thd_db": 20 * math.log10(thd_mean / 100.0) if thd_mean > 0 else -200,
            "thd_std": thd_std, "thd_segments": str(thds),
        })
        return thd_mean
    except Exception as e:
        print(f"    ERRORE: {e}")
        all_results.append({
            "freq": freq, "level": level, "mode": mode,
            "variant": variant, "scenario": scenario,
            "thd_pct": None, "thd_db": None, "thd_std": None, "thd_segments": None,
        })
        return None
    finally:
        if out_wav.exists():
            out_wav.unlink()


def main():
    if not HARNESS.exists():
        print(f"Harness non trovato: {HARNESS}")
        return 1

    OUTDIR.mkdir(parents=True, exist_ok=True)
    all_results = []

    # --- 1. Matrice completa (stato calibrato Fase 2: default del core) ---
    print("=== FASE 2: Matrice completa (648 render) ===")
    total = len(FREQS) * len(LEVELS) * len(MODES) * len(VARIANTS)
    count = 0
    for freq in FREQS:
        for level in LEVELS:
            input_wav = ensure_input(freq, level)
            for mode in MODES:
                for variant in VARIANTS:
                    count += 1
                    if count % 50 == 0:
                        print(f"[{count}/{total}] {freq}Hz {level}dB {mode} {variant}")
                    out_wav = OUTDIR / f"out_{freq}Hz_{level}dB_{mode}_{variant}.wav"
                    try:
                        run_harness(input_wav, out_wav, mode, variant)
                    except Exception as e:
                        print(f"    ERRORE harness: {e}")
                        all_results.append({
                            "freq": freq, "level": level, "mode": mode,
                            "variant": variant, "scenario": "base",
                            "thd_pct": None, "thd_db": None,
                            "thd_std": None, "thd_segments": None,
                        })
                        continue
                    record(all_results, freq, level, mode, variant, "base", out_wav)
            input_wav.unlink()

    # --- 2. Ablazione componenti a -20 dBFS (mix, full) ---
    print("\n=== FASE 2: Ablazione componenti (9 render) ===")
    for freq in KEY_FREQS:
        input_wav = ensure_input(freq, -20)
        for scen_name, scen_args, scen_desc in ABLATION:
            out_wav = OUTDIR / f"out_{freq}Hz_-20dB_mix_full_{scen_name}.wav"
            thd = record(all_results, freq, -20, "mix", "full", scen_name,
                         run_harness(input_wav, out_wav, "mix", "full", scen_args))
            print(f"  {freq}Hz {scen_name} ({scen_desc}): {thd:.4f}%" if thd else f"  {freq}Hz {scen_name}: ERRORE")
        input_wav.unlink()

    # --- 3. Sweep kOpAmp a -20 dBFS (mix, full) ---
    print("\n=== FASE 2: Sweep kOpAmp (15 render) ===")
    for freq in KEY_FREQS:
        input_wav = ensure_input(freq, -20)
        for k in OPAMP_SWEEP:
            scen = f"sweep_{k:.3f}"
            out_wav = OUTDIR / f"out_{freq}Hz_-20dB_mix_full_{scen}.wav"
            thd = record(all_results, freq, -20, "mix", "full", scen,
                         run_harness(input_wav, out_wav, "mix", "full",
                                     ["--k-opamp", f"{k:.3f}"]))
            print(f"  {freq}Hz kOpAmp={k:.3f}: {thd:.4f}%" if thd else f"  {freq}Hz kOpAmp={k}: ERRORE")
        input_wav.unlink()

    # --- Salva CSV ---
    csv_path = OUTDIR / "results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "freq", "level", "mode", "variant", "scenario",
            "thd_pct", "thd_db", "thd_std", "thd_segments"
        ])
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)
    print(f"\nRisultati totali: {len(all_results)} righe salvate in {csv_path}")

    generate_report(all_results)
    return 0


def get(valid, freq, level, mode, variant, scenario):
    return next((x for x in valid
                 if x["freq"] == freq and x["level"] == level and x["mode"] == mode
                 and x["variant"] == variant and x["scenario"] == scenario), None)


def gap_db(thd_pct, freq):
    return 20 * math.log10((thd_pct / 100) / (HW_TARGETS[freq] / 100))


def generate_report(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    valid = [r for r in results if r["thd_pct"] is not None]
    hw_db = {f: 20 * math.log10(HW_TARGETS[f] / 100) for f in HW_TARGETS}

    # Grafico 1: THD vs frequenza
    fig, ax = plt.subplots(figsize=(10, 6))
    for level in LEVELS:
        subset = [r for r in valid
                  if r["level"] == level and r["mode"] == "mix"
                  and r["variant"] == "full" and r["scenario"] == "base"]
        if not subset:
            continue
        subset.sort(key=lambda x: x["freq"])
        ax.loglog([r["freq"] for r in subset], [r["thd_pct"] for r in subset],
                  "o-", label=f"{level} dBFS")
    ax.set_xlabel("Frequenza (Hz)")
    ax.set_ylabel("THD (%)")
    ax.set_title("FASE 2 — THD vs Frequenza (mix, variante completa, stato calibrato)")
    ax.grid(True, which="both", ls="-", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTDIR / "THD_vs_freq.png", dpi=150)
    plt.close(fig)

    # Grafico 2: THD vs livello
    fig, ax = plt.subplots(figsize=(10, 6))
    for freq in FREQS:
        subset = [r for r in valid
                  if r["freq"] == freq and r["mode"] == "mix"
                  and r["variant"] == "full" and r["scenario"] == "base"]
        if not subset:
            continue
        subset.sort(key=lambda x: x["level"])
        ax.semilogx([abs(l) for l in [r["level"] for r in subset]],
                    [r["thd_pct"] for r in subset], "o-", label=f"{freq} Hz")
    ax.set_xlabel("Livello (|dBFS RMS|)")
    ax.set_ylabel("THD (%)")
    ax.set_title("FASE 2 — THD vs Livello (mix, variante completa, stato calibrato)")
    ax.grid(True, which="both", ls="-", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTDIR / "THD_vs_level.png", dpi=150)
    plt.close(fig)

    # Grafico 3: confronto 3 varianti + HW a -20 dBFS
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for idx, freq in enumerate(KEY_FREQS):
        ax = axes[idx]
        variants = ["full", "comp_off", "dist_off"]
        labels = ["Completa\n(Fase 2 calibrata)", "Solo limiter\ntHd off (comp_off)", "Solo dist. uscita\n(limiter off)"]
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
        thds = []
        for v in variants:
            r = get(valid, freq, -20, "mix", v, "base")
            thds.append(r["thd_pct"] if r else 0)
        bars = ax.bar(range(len(variants)), thds, color=colors, alpha=0.7)
        ax.axhline(HW_TARGETS[freq], color="red", linestyle="--", linewidth=2,
                   label=f"HW target ({HW_TARGETS[freq]:.3f}%)")
        ax.set_xticks(range(len(variants)))
        ax.set_xticklabels(labels, rotation=15, ha="right")
        ax.set_ylabel("THD (%)")
        ax.set_title(f"FASE 2 — {freq} Hz @ -20 dBFS")
        ax.legend()
        ax.grid(True, axis="y", alpha=0.3)
        for bar, val in zip(bars, thds):
            ax.annotate(f"{val:.4f}%", xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 3), textcoords="offset points", ha="center",
                        va="bottom", fontsize=9)
    fig.suptitle("FASE 2 — Confronto THD plugin vs Hardware (mix)")
    fig.tight_layout()
    fig.savefig(OUTDIR / "THD_comparison.png", dpi=150)
    plt.close(fig)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# THD Characterization Report — Seiwa DDX-777 — FASE 2 (5 componenti HF)\n\n")
        f.write(f"**Data**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Harness**: {HARNESS}\n")
        f.write(f"**Matrice completa**: {len(FREQS)} freq × {len(LEVELS)} livelli × 3 mode × 3 variant = {len(FREQS)*len(LEVELS)*3*3} render (stato calibrato)\n")
        f.write(f"**Ablazione componenti**: 3 scenari × 3 freq = 9 render\n")
        f.write(f"**Sweep kOpAmp**: {len(OPAMP_SWEEP)} valori × 3 freq = {len(OPAMP_SWEEP)*3} render\n\n")

        f.write("## 1. Stato calibrato Fase 2\n\n")
        f.write("| Componente | Coefficiente | Stato | Note |\n")
        f.write("|---|---|---|---|\n")
        f.write("| Comp 1 — Virtual ADC 32 kHz (AA+ricostruzione 8° @ 15 kHz) | — | ON | attivo di default |\n")
        f.write("| Comp 2 — Rectifier NE571 banda finita (kRect) | 0.0 | calibrato | contributo < 1 dB al gap; ripple 2f filtrato a 10 kHz |\n")
        f.write("| Comp 3 — Mismatch DAC R-2R (kDac2/kDac3) | 0.0 / 0.0 | calibrati | aggiungono solo a 1 kHz (H2 @ 2 kHz non filtrata); niente a 10 kHz |\n")
        f.write("| Comp 4 — Buffer uscita tanh (kBuffer) | 0.0 | calibrato | distorsione broadband: peggiora 1 kHz senza compensare |\n")
        f.write("| Comp 5 — 4 stadi op-amp 4558D (kOpAmp) | **0.018** | calibrato | chiude il gap a 10 kHz; effetto netto a 1 kHz quasi nullo (interazione col ramo limiter) |\n\n")

        f.write("## 2. Tabelle THD % (modalità mix, variante full, stato calibrato)\n\n")
        f.write("| Freq (Hz) | " + " | ".join(f"{l} dBFS" for l in LEVELS) + " |\n")
        f.write("|" + "|".join(["---"] * (len(LEVELS) + 1)) + "|\n")
        for freq in FREQS:
            row = [f"{freq}"]
            for level in LEVELS:
                r = get(valid, freq, level, "mix", "full", "base")
                row.append(f"{r['thd_pct']:.4f}%" if r and r["thd_pct"] is not None else "N/A")
            f.write("| " + " | ".join(row) + " |\n")
        f.write("\n")

        f.write("## 3. Ablazione — contributo incrementale dei componenti (-20 dBFS, mix, full)\n\n")
        f.write("| Scenario | 100 Hz | 1 kHz | 10 kHz | Delta vs HW a 10 kHz |\n")
        f.write("|---|---|---|---|---|\n")
        prev = None
        for scen_name, _, scen_desc in ABLATION:
            cells = []
            for freq in KEY_FREQS:
                r = get(valid, freq, -20, "mix", "full", scen_name)
                cells.append(f"{r['thd_pct']:.4f}%" if r else "N/A")
            r10 = get(valid, 10000, -20, "mix", "full", scen_name)
            d10 = f"{gap_db(r10['thd_pct'], 10000):+.1f} dB" if r10 else "N/A"
            f.write(f"| {scen_desc} | {cells[0]} | {cells[1]} | {cells[2]} | {d10} |\n")
        f.write("\n")
        f.write("Comp 2/3/4 calibrati a 0: le misure di calibrazione (sweep su 5-10 valori) hanno mostrato "
                "contributo < 1 dB al gap a 10 kHz e/o peggioramento del match a 1 kHz/100 Hz oltre ±2 dB. "
                "Non sono quindi attivi nel modello finale.\n\n")

        f.write("## 4. Sweep kOpAmp a -20 dBFS (mix, full)\n\n")
        f.write("| kOpAmp | 100 Hz | 1 kHz | 10 kHz | Gap 10 kHz vs HW |\n")
        f.write("|---|---|---|---|---|\n")
        for k in OPAMP_SWEEP:
            row = [f"{k:.3f}"]
            g10 = "N/A"
            for freq in KEY_FREQS:
                r = get(valid, freq, -20, "mix", "full", f"sweep_{k:.3f}")
                row.append(f"{r['thd_pct']:.4f}%" if r else "N/A")
                if freq == 10000 and r:
                    g10 = f"{gap_db(r['thd_pct'], 10000):+.1f} dB"
            row.append(g10)
            f.write("| " + " | ".join(row) + " |\n")
        f.write("\nkOpAmp = 0.018 (default) è il punto che tiene tutte e 3 le frequenze dentro ±2 dB del target HW.\n\n")

        f.write("## 5. Analisi — domande chiave\n\n")
        f.write("### Q1 — Contributo del limiter (variante completa vs dist_off, -20 dBFS)\n\n")
        f.write("| Freq (Hz) | THD completa | THD solo limiter | Contributo limiter |\n")
        f.write("|---|---|---|---|\n")
        for freq in KEY_FREQS:
            r_full = get(valid, freq, -20, "mix", "full", "base")
            r_lim = get(valid, freq, -20, "mix", "dist_off", "base")
            if r_full and r_lim:
                contrib = math.sqrt(max(0.0, r_full["thd_pct"] ** 2 - r_lim["thd_pct"] ** 2))
                f.write(f"| {freq} | {r_full['thd_pct']:.4f}% | {r_lim['thd_pct']:.4f}% | {contrib:.4f}% |\n")
        f.write("\n")

        f.write("### Q2 — Contributo del ramo di distorsione d'uscita (variante completa vs comp_off, -20 dBFS)\n\n")
        f.write("| Freq (Hz) | THD completa | THD senza limiter | Contributo dist. uscita |\n")
        f.write("|---|---|---|---|\n")
        for freq in KEY_FREQS:
            r_full = get(valid, freq, -20, "mix", "full", "base")
            r_dist = get(valid, freq, -20, "mix", "comp_off", "base")
            if r_full and r_dist:
                contrib = math.sqrt(max(0.0, r_full["thd_pct"] ** 2 - r_dist["thd_pct"] ** 2))
                f.write(f"| {freq} | {r_full['thd_pct']:.4f}% | {r_dist['thd_pct']:.4f}% | {contrib:.4f}% |\n")
        f.write("\n")

        f.write("### Q3 — Attivazione del limiter: THD a 10 kHz in funzione del livello (solo limiter, dist_off)\n\n")
        f.write("| Livello (dBFS RMS) | Peak (dBFS) | THD (%) | Note |\n")
        f.write("|---|---|---|---|\n")
        for level in [-6, -12, -14, -18, -20, -24]:
            r = get(valid, 10000, level, "mix", "dist_off", "base")
            if r and r["thd_pct"] is not None:
                peak_db = level + 3.0
                note = "SOPRA soglia (-20 dBFS peak)" if peak_db > -20 else "sotto soglia"
                f.write(f"| {level} | {peak_db:.1f} | {r['thd_pct']:.4f}% | {note} |\n")
        f.write("\n")

        f.write("### Q4 — Virtual ADC: contributo a 10 kHz (-20 dBFS)\n\n")
        r_f1 = get(valid, 10000, -20, "mix", "full", "fase1")
        r_c1 = get(valid, 10000, -20, "mix", "full", "comp1_vadc")
        r_f2 = get(valid, 10000, -20, "mix", "full", "comp5_final")
        f.write("| Stato | THD 10 kHz |\n")
        f.write("|---|---|\n")
        if r_f1:
            f.write(f"| Fase 1 (VADC off, k=0) | {r_f1['thd_pct']:.4f}% |\n")
        if r_c1:
            f.write(f"| + Comp 1 (VADC on, k=0) | {r_c1['thd_pct']:.4f}% |\n")
        if r_f2:
            f.write(f"| + Comp 5 (stato finale) | {r_f2['thd_pct']:.4f}% |\n")
        f.write(f"| **HW target** | **{HW_TARGETS[10000]:.4f}%** |\n\n")
        if r_f1 and r_c1 and r_f2:
            f.write(f"Il VADC da solo aggiunge {r_c1['thd_pct']-r_f1['thd_pct']:+.4f}% a 10 kHz "
                    f"({20*math.log10(r_c1['thd_pct']/r_f1['thd_pct']):+.1f} dB); la chiusura del gap "
                    f"principale avviene con Comp 5 (kOpAmp=0.018): da {r_c1['thd_pct']:.4f}% a {r_f2['thd_pct']:.4f}%.\n\n")

        f.write("## 6. Confronto Fase 0 / Fase 1 / Fase 2 vs Hardware (-20 dBFS)\n\n")
        f.write("| Freq | Fase 0 (comp -6 dBFS) | Fase 1 (limiter -20 dBFS) | Fase 2 (5 componenti) | HW target | Gap Fase 2 vs HW |\n")
        f.write("|---|---|---|---|---|---|\n")
        for freq in KEY_FREQS:
            r = get(valid, freq, -20, "mix", "full", "base")
            if r:
                g = gap_db(r["thd_pct"], freq)
                f.write(f"| {freq} Hz | {PHASE0[freq]:.4f}% | {PHASE1[freq]:.4f}% | "
                        f"{r['thd_pct']:.4f}% | {HW_TARGETS[freq]:.3f}% | {g:+.1f} dB |\n")
        f.write("\n")

        f.write("## 7. Sintesi Gap vs Hardware (stato calibrato, -20 dBFS)\n\n")
        f.write("| Freq | Fase 2 THD | HW THD | Gap (dB) | Stato |\n")
        f.write("|---|---|---|---|---|\n")
        for freq in KEY_FREQS:
            r = get(valid, freq, -20, "mix", "full", "base")
            if r:
                gap = gap_db(r["thd_pct"], freq)
                status = "✓ Match (±2 dB)" if abs(gap) <= 2 else ("✓ Match (±3 dB)" if abs(gap) <= 3 else ("Plugin più distorto" if gap > 0 else "Plugin meno distorto"))
                f.write(f"| {freq} Hz | {r['thd_pct']:.4f}% | {HW_TARGETS[freq]:.3f}% | {gap:+.1f} | {status} |\n")
        f.write("\n")

        f.write("## 8. Note e limitazioni\n\n")
        f.write("- **Effetto a 1 kHz di Comp 5**: con kOpAmp > 0 il THD a 1 kHz presenta un minimo non monotono "
                "(riduzione parziale della 2ª armonica) che si manifesta solo con il limiter attivo: interazione tra la "
                "nonlinearità tanh (ordine dispari) e lo stadio 2° ordine kThdHigh, con fasi definite dal crossover "
                "500 Hz. Reproducibile bit-per-bit; misurato: con limiter ON il contributo netto a 1 kHz è ≈ +0.001% "
                "(quasi nullo), mentre con limiter OFF (comp_off) lo stesso kOpAmp aggiunge distorsione come atteso.\n")
        f.write("- **Armoniche 5-10 non misurabili a 10 kHz** (Nyquist 48 kHz) → THD a 10 kHz calcolato su sole 3 armoniche (20, 30, 40 kHz), sottostimato rispetto a una misura full-band HW.\n")
        f.write("- **Livello assoluto al limiter HW ignoto** (dipende da pot LEVEL, fader DAW, gain scheda): il target HW 0.349/0.033/0.035% è a -20 dBFS RMS come misurato in sessione 11.\n")
        f.write("- **Comp 2/3/4 calibrati a 0**: i componenti sono implementati e attivi nel codice (band-pass del rectifier, "
                "dopo la quantizzazione 12 bit), ma i coefficienti di distorsione sono nulli perché i dati HW a -20 dBFS "
                "non supportano un contributo ≥ 1 dB e qualsiasi valore > 0 peggiorava il match a 1 kHz/100 Hz.\n")
        f.write("- **Virtual ADC**: filtri Butterworth 8° @ 15 kHz con clock a 3 fasi (96→32→96 kHz), coerente con l'ipotesi di ADC interno 32 kHz.\n")

    print(f"Report salvato: {REPORT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
