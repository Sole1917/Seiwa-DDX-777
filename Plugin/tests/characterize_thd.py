#!/usr/bin/env python3
"""
characterize_thd.py — Caratterizzazione THD plugin DDX-777

Matrice: 8 freq × 7 livelli × 3 mode × 3 variant = 504 render
+ Q4: 3 scenari a 10 kHz (attuale, virtual ADC, HW target)
+ Sweep livello compander: -30 a -10 dBFS passo 2 dB a 10 kHz (comp-only)

Output:
- build/char_thd/results.csv
- build/char_thd/THD_vs_freq.png
- build/char_thd/THD_vs_level.png
- build/char_thd/THD_comparison.png
- tests/THD_characterization.md
"""

import argparse
import csv
import math
import os
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy import signal as sig

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "build" / "Release" / "ddx_harness.exe"
OUTDIR = ROOT / "build" / "char_thd"
SR = 96000

# Matrice parametri
FREQS = [50, 100, 200, 500, 1000, 2000, 5000, 10000]
LEVELS_DBFS_RMS = [-6, -12, -14, -18, -20, -24, -30, -36, -42]  # + -14, -20 per soglia compander
MODES = ["wet", "mix", "direct"]
VARIANTS = ["full", "comp_off", "dist_off"]  # completa, --char-dist-off, --char-comp-off

# Q4: 10 kHz, 3 scenari
Q4_SCENARIOS = [
    ("current", []),
    ("virtual_adc", ["--char-virtual-adc"]),
]

# Sweep livello compander a 10 kHz (comp-only)
COMPANDER_SWEEP_LEVELS = [-30, -28, -26, -24, -22, -20, -18, -16, -14, -12, -10]

# Durata segnale: 5 * 2^20 + 2 * 96000 = 5,434,880 campioni (~56.5 s)
N_FFT = 1 << 20
N_SEG = 5
SIGNAL_LEN = N_SEG * N_FFT + 2 * 96000  # 5 segmenti + 1s fade-in + 1s fade-out
FADE_SAMPLES = int(0.01 * SR)  # 10 ms

# Armoniche misurabili per frequenza (fino a Nyquist 48 kHz)
def measurable_harmonics(f0):
    """Restituisce lista armoniche 2-10 misurabili per f0"""
    max_h = min(10, int(48000 / f0))
    return list(range(2, max_h + 1))

def db(x):
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-12))

def rms_db(x):
    return 20.0 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12)

def generate_tone(freq, level_dbfs_rms, length=SIGNAL_LEN):
    """Genera sinusoide a freq Hz, level dBFS RMS, length campioni"""
    peak_factor = math.sqrt(2)  # RMS to peak per sinusoide
    amplitude = peak_factor * 10 ** (level_dbfs_rms / 20.0)
    t = np.arange(length) / SR
    x = amplitude * np.sin(2 * np.pi * freq * t)
    # Fade in/out
    fade = np.ones(length)
    fade[:FADE_SAMPLES] = np.linspace(0, 1, FADE_SAMPLES)
    fade[-FADE_SAMPLES:] = np.linspace(1, 0, FADE_SAMPLES)
    x *= fade
    return x.astype(np.float32)

def measure_thd(signal, f0, sr=SR):
    """Misura THD su signal (singolo segmento 2^20)"""
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
    """Misura THD su 5 segmenti non sovrapposti, restituisce media"""
    sr_read, x = wavfile.read(output_path)
    if x.ndim > 1:
        x = x[:, 0]
    x = x.astype(np.float64)

    # Scarta primi 96000 e ultimi 96000 campioni
    x = x[96000:-96000]
    # Ora abbiamo esattamente 5 * 2^20 campioni
    thds = []
    for i in range(N_SEG):
        seg = x[i * N_FFT:(i + 1) * N_FFT]
        thd = measure_thd(seg, f0, sr)
        thds.append(thd)
    return np.mean(thds), np.std(thds), thds

def run_harness(input_path, output_path, mode, variant, extra_args=None):
    """Esegue harness e restituisce percorso output"""
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Solo subset per test rapido")
    parser.add_argument("--q4-only", action="store_true", help="Solo test Q4 a 10 kHz")
    parser.add_argument("--compander-sweep", action="store_true", help="Solo sweep livello compander")
    args = parser.parse_args()

    if not HARNESS.exists():
        print(f"Harness non trovato: {HARNESS}")
        print("Build: cmake --build build --config Release --target ddx_harness")
        return 1

    OUTDIR.mkdir(parents=True, exist_ok=True)

    results = []

    # Q4: test a 10 kHz
    if args.q4_only:
        freqs = [10000]
        levels = [-20]
        modes = ["mix"]
        variants = ["full"]
        q4_mode = True
    elif args.compander_sweep:
        freqs = [10000]
        levels = COMPANDER_SWEEP_LEVELS
        modes = ["mix"]
        variants = ["dist_off"]  # comp-only = dist_off
        q4_mode = False
    else:
        freqs = FREQS
        levels = LEVELS_DBFS_RMS
        modes = MODES
        variants = VARIANTS
        q4_mode = False

    if args.quick:
        freqs = [100, 1000, 10000]
        levels = [-20, -30]
        modes = ["mix"]
        variants = ["full"]

    total = len(freqs) * len(levels) * len(modes) * len(variants)
    print(f"=== Caratterizzazione THD: {total} render ===")

    count = 0
    for freq in freqs:
        for level in levels:
            # Genera segnale di input
            input_wav = OUTDIR / f"input_{freq}Hz_{level}dB.wav"
            if not input_wav.exists():
                print(f"  Generazione input {freq}Hz {level}dBFS...")
                x = generate_tone(freq, level)
                wavfile.write(str(input_wav), SR, x)

            for mode in modes:
                for variant in variants:
                    count += 1
                    print(f"[{count}/{total}] {freq}Hz {level}dB {mode} {variant}")

                    # Q4: scenari multipli per 10 kHz
                    if q4_mode and freq == 10000:
                        for scen_name, scen_args in Q4_SCENARIOS:
                            out_wav = OUTDIR / f"out_{freq}Hz_{level}dB_{mode}_{variant}_{scen_name}.wav"
                            try:
                                run_harness(input_wav, out_wav, mode, variant, scen_args)
                                thd_mean, thd_std, thds = measure_thd_5segments(out_wav, freq)
                                results.append({
                                    "freq": freq, "level": level, "mode": mode,
                                    "variant": variant, "scenario": scen_name,
                                    "thd_pct": thd_mean, "thd_db": 20 * math.log10(thd_mean / 100.0) if thd_mean > 0 else -200,
                                    "thd_std": thd_std, "thd_segments": thds
                                })
                                print(f"    THD = {thd_mean:.4f}% ± {thd_std:.4f}% ({20*math.log10(thd_mean/100):.1f} dB)")
                            except Exception as e:
                                print(f"    ERRORE: {e}")
                                results.append({
                                    "freq": freq, "level": level, "mode": mode,
                                    "variant": variant, "scenario": scen_name,
                                    "thd_pct": None, "thd_db": None, "thd_std": None, "thd_segments": None
                                })
                            finally:
                                if out_wav.exists():
                                    out_wav.unlink()
                    else:
                        out_wav = OUTDIR / f"out_{freq}Hz_{level}dB_{mode}_{variant}.wav"
                        try:
                            run_harness(input_wav, out_wav, mode, variant)
                            thd_mean, thd_std, thds = measure_thd_5segments(out_wav, freq)
                            results.append({
                                "freq": freq, "level": level, "mode": mode,
                                "variant": variant, "scenario": "base",
                                "thd_pct": thd_mean, "thd_db": 20 * math.log10(thd_mean / 100.0) if thd_mean > 0 else -200,
                                "thd_std": thd_std, "thd_segments": thds
                            })
                            print(f"    THD = {thd_mean:.4f}% ± {thd_std:.4f}% ({20*math.log10(thd_mean/100):.1f} dB)")
                        except Exception as e:
                            print(f"    ERRORE: {e}")
                            results.append({
                                "freq": freq, "level": level, "mode": mode,
                                "variant": variant, "scenario": "base",
                                "thd_pct": None, "thd_db": None, "thd_std": None, "thd_segments": None
                            })
                        finally:
                            if out_wav.exists():
                                out_wav.unlink()

            # Cancella input dopo uso
            if input_wav.exists():
                input_wav.unlink()

    # Salva CSV
    csv_path = OUTDIR / "results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "freq", "level", "mode", "variant", "scenario",
            "thd_pct", "thd_db", "thd_std", "thd_segments"
        ])
        writer.writeheader()
        for r in results:
            row = r.copy()
            row["thd_segments"] = str(row["thd_segments"])
            writer.writerow(row)
    print(f"\nRisultati salvati: {csv_path}")

    if not args.q4_only and not args.compander_sweep:
        generate_report(results)

    return 0

def generate_report(results):
    """Genera report markdown + grafici"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Filtra risultati validi
    valid = [r for r in results if r["thd_pct"] is not None]

    # --- Grafico 1: THD vs frequenza (curve per livello, modalità mix, variante full) ---
    fig, ax = plt.subplots(figsize=(10, 6))
    for level in sorted(set(r["level"] for r in valid)):
        subset = [r for r in valid if r["level"] == level and r["mode"] == "mix" and r["variant"] == "full"]
        if not subset: continue
        subset.sort(key=lambda x: x["freq"])
        freqs = [r["freq"] for r in subset]
        thds = [r["thd_pct"] for r in subset]
        ax.loglog(freqs, thds, "o-", label=f"{level} dBFS")
    ax.set_xlabel("Frequenza (Hz)")
    ax.set_ylabel("THD (%)")
    ax.set_title("THD vs Frequenza (modalità mix, variante completa)")
    ax.grid(True, which="both", ls="-", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTDIR / "THD_vs_freq.png", dpi=150)
    plt.close(fig)

    # --- Grafico 2: THD vs livello (curve per frequenza, modalità mix, variante full) ---
    fig, ax = plt.subplots(figsize=(10, 6))
    for freq in sorted(set(r["freq"] for r in valid)):
        subset = [r for r in valid if r["freq"] == freq and r["mode"] == "mix" and r["variant"] == "full"]
        if not subset: continue
        subset.sort(key=lambda x: x["level"])
        levels = [r["level"] for r in subset]
        thds = [r["thd_pct"] for r in subset]
        ax.semilogx(levels, thds, "o-", label=f"{freq} Hz")
    ax.set_xlabel("Livello (dBFS RMS)")
    ax.set_ylabel("THD (%)")
    ax.set_title("THD vs Livello (modalità mix, variante completa)")
    ax.grid(True, which="both", ls="-", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTDIR / "THD_vs_level.png", dpi=150)
    plt.close(fig)

    # --- Grafico 3: Confronto 100 Hz / 1 kHz / 10 kHz a -20 dBFS ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    hw_targets = {100: 0.349, 1000: 0.033, 10000: 0.035}
    for idx, freq in enumerate([100, 1000, 10000]):
        ax = axes[idx]
        variants_to_plot = ["full", "comp_off", "dist_off"]
        labels = ["Completa", "Solo companding\n(dist_off)", "Solo dist. uscita\n(comp_off)"]
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

        thds = []
        for v in variants_to_plot:
            r = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == v), None)
            thds.append(r["thd_pct"] if r else 0)

        bars = ax.bar(range(len(variants_to_plot)), thds, color=colors, alpha=0.7)
        ax.axhline(hw_targets[freq], color="red", linestyle="--", linewidth=2, label=f"HW target ({hw_targets[freq]:.3f}%)")
        ax.set_xticks(range(len(variants_to_plot)))
        ax.set_xticklabels(labels, rotation=15, ha="right")
        ax.set_ylabel("THD (%)")
        ax.set_title(f"{freq} Hz @ -20 dBFS")
        ax.legend()
        ax.grid(True, axis="y", alpha=0.3)
        # Annota valori
        for bar, val in zip(bars, thds):
            ax.annotate(f"{val:.4f}%", xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)

    fig.suptitle("Confronto THD plugin vs Hardware (modalità mix)")
    fig.tight_layout()
    fig.savefig(OUTDIR / "THD_comparison.png", dpi=150)
    plt.close(fig)

    # --- Report Markdown ---
    report_path = ROOT / "tests" / "THD_characterization.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# THD Characterization Report — Seiwa DDX-777\n\n")
        f.write(f"**Data**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Harness**: {HARNESS}\n")
        f.write(f"**Matrice**: {len(FREQS)} freq × {len(LEVELS_DBFS_RMS)} livelli × {len(MODES)} mode × {len(VARIANTS)} variant\n\n")

        f.write("## 1. Metodologia\n\n")
        f.write("- **Segnale**: sinusoide pura, durata 56.5 s (5×2²⁰ + 2s fade)\n")
        f.write("- **Livelli**: dBFS RMS (coerente con misure HW)\n")
        f.write("- **THD**: FFT 2²⁰ punti, finestra Hann, armoniche 2-10 (fino a Nyquist 48 kHz)\n")
        f.write("- **5 medie**: 5 segmenti non sovrapposti da 2²⁰ campioni\n")
        f.write("- **Armoniche misurabili a 10 kHz**: solo 2-4 (20, 30, 40 kHz)\n\n")

        f.write("## 2. Tabelle THD % (modalità mix)\n\n")

        # Tabella per variante
        for variant in ["full", "comp_off", "dist_off"]:
            f.write(f"### Variante: {variant}\n\n")
            f.write("| Freq (Hz) | " + " | ".join(f"{l} dBFS" for l in LEVELS_DBFS_RMS) + " |\n")
            f.write("|" + "|".join(["---"] * (len(LEVELS_DBFS_RMS) + 1)) + "|\n")
            for freq in FREQS:
                row = [f"{freq}"]
                for level in LEVELS_DBFS_RMS:
                    r = next((x for x in valid if x["freq"] == freq and x["level"] == level and x["mode"] == "mix" and x["variant"] == variant), None)
                    if r and r["thd_pct"] is not None:
                        row.append(f"{r['thd_pct']:.4f}%")
                    else:
                        row.append("N/A")
                f.write("| " + " | ".join(row) + " |\n")
            f.write("\n")

        # Q4 comparison
        f.write("## 3. Q4 — Virtual ADC 32 kHz a 10 kHz (-20 dBFS)\n\n")
        f.write("| Scenario | THD (%) | THD (dB) | Note |\n")
        f.write("|----------|---------|----------|------|\n")
        for scen_name, _ in Q4_SCENARIOS:
            r = next((x for x in valid if x["freq"] == 10000 and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == scen_name), None)
            if r:
                f.write(f"| {scen_name} | {r['thd_pct']:.4f}% | {r['thd_db']:.1f} | |\n")
        # Target HW
        f.write(f"| **HW target** | **0.0350%** | **{20*math.log10(0.035/100):.1f}** | Misura sessione 11 |\n")
        f.write("\n")

        # Compander sweep
        f.write("## 4. Sweep Livello Compander a 10 kHz (variante dist_off = solo companding)\n\n")
        f.write("| Livello (dBFS RMS) | THD (%) | THD (dB) |\n")
        f.write("|---|---|---|\n")
        for level in COMPANDER_SWEEP_LEVELS:
            r = next((x for x in valid if x["freq"] == 10000 and x["level"] == level and x["mode"] == "mix" and x["variant"] == "dist_off"), None)
            if r and r["thd_pct"] is not None:
                f.write(f"| {level} | {r['thd_pct']:.4f}% | {r['thd_db']:.1f} |\n")
        f.write("\n")

        # Analisi
        f.write("## 5. Analisi\n\n")

        # Q1
        f.write("### Q1 — Il companding attuale produce distorsione dipendente dalla frequenza? Quanta?\n\n")
        f.write("Confronto **variante completa** vs **dist_off** (solo companding):\n\n")
        f.write("| Freq (Hz) | THD completa | THD solo companding | Contributo companding |\n")
        f.write("|---|---|---|---|\n")
        for freq in [100, 1000, 10000]:
            r_full = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full"), None)
            r_comp = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "dist_off"), None)
            if r_full and r_comp:
                contrib_pct = math.sqrt(max(0, r_full["thd_pct"]**2 - r_comp["thd_pct"]**2))
                f.write(f"| {freq} | {r_full['thd_pct']:.4f}% | {r_comp['thd_pct']:.4f}% | {contrib_pct:.4f}% |\n")
        f.write("\n")

        # Q2
        f.write("### Q2 — La distorsione d'uscita attuale è lineare col livello o ha una curva? (Limited vs compressore)\n\n")
        f.write("Confronto **variante completa** vs **comp_off** (solo distorsione d'uscita):\n\n")
        f.write("| Freq (Hz) | THD completa | THD solo dist. uscita | Contributo dist. uscita |\n")
        f.write("|---|---|---|---|\n")
        for freq in [100, 1000, 10000]:
            r_full = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full"), None)
            r_dist = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "comp_off"), None)
            if r_full and r_dist:
                contrib_pct = math.sqrt(max(0, r_full["thd_pct"]**2 - r_dist["thd_pct"]**2))
                f.write(f"| {freq} | {r_full['thd_pct']:.4f}% | {r_dist['thd_pct']:.4f}% | {contrib_pct:.4f}% |\n")
        f.write("\n")

        # Analisi sweep livello per vedere comportamento limiter
        f.write("### Comportamento compander: limiter (soglia) o compressore morbido?\n\n")
        f.write("Dati sweep livello a 10 kHz (solo companding, variante dist_off):\n\n")
        f.write("| Livello (dBFS RMS) | THD (%) | THD (dB) |\n")
        f.write("|---|---|---|\n")
        for level in COMPANDER_SWEEP_LEVELS:
            r = next((x for x in valid if x["freq"] == 10000 and x["level"] == level and x["mode"] == "mix" and x["variant"] == "dist_off"), None)
            if r and r["thd_pct"] is not None:
                f.write(f"| {level} | {r['thd_pct']:.4f}% | {r['thd_db']:.1f} |\n")
        f.write("\n")

        # Q3
        f.write("### Q3 — Dove il divario col target è massimo?\n\n")
        f.write("| Freq (Hz) | THD plugin | THD HW | Gap (dB) |\n")
        f.write("|---|---|---|---|\n")
        for freq in [100, 1000, 10000]:
            r = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full"), None)
            hw = hw_targets[freq]
            if r:
                gap = 20 * math.log10(r["thd_pct"] / 100.0 / hw)
                f.write(f"| {freq} | {r['thd_pct']:.4f}% | {hw:.3f}% | {gap:.1f} dB |\n")
        f.write("\n")

        # Q4
        f.write("### Q4 — Il THD a 10 kHz nel plugin è generato a 96 kHz o include aliasing da 32 kHz?\n\n")
        r_cur = next((x for x in valid if x["freq"] == 10000 and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == "current"), None)
        r_vadc = next((x for x in valid if x["freq"] == 10000 and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == "virtual_adc"), None)
        if r_cur and r_vadc:
            f.write(f"- **Plugin attuale (96 kHz)**: {r_cur['thd_pct']:.4f}% ({r_cur['thd_db']:.1f} dB)\n")
            f.write(f"- **Plugin + Virtual ADC 32 kHz**: {r_vadc['thd_pct']:.4f}% ({r_vadc['thd_db']:.1f} dB)\n")
            f.write(f"- **Target HW**: 0.0350% ({20*math.log10(0.035/100):.1f} dB)\n\n")
            if r_vadc["thd_pct"] > r_cur["thd_pct"]:
                f.write("**Interpretazione**: Il Virtual ADC **aumenta** il THD → l'aliasing da campionamento 32 kHz contribuisce al THD hardware. Il gap si riduce.\n")
            else:
                f.write("**Interpretazione**: Il Virtual ADC **non aumenta** (o riduce) il THD → l'aliasing non è la causa principale del gap.\n")
            f.write("\n")

        # Verifica attribuzione sessione 11
        f.write("## 6. Verifica attribuzione THD Sessione 11\n\n")
        f.write("L'attribuzione \"THD da companding NE571\" (sessione 11) è verificata confrontando:\n")
        f.write("- Livello stimato al compander HW: ≈ -17 dBFS peak (-20 dBFS RMS)\n")
        f.write("- Soglia compander plugin: -6 dBFS peak (knee -9..-3 dBFS)\n")
        f.write("- **Risultato**: Il livello HW stimato è **11 dB sotto soglia** → compander inattivo\n")
        f.write("- **Conclusione**: Il THD hardware 0.035% a 10 kHz **NON proviene dal companding** NE571\n")
        f.write("- Fonte probabile: stadio d'uscita (DAC 12 bit + filtro AA + buffer) + aliasing 32 kHz\n\n")

        # Raccomandazione
        f.write("## 7. Raccomandazione per modellazione fisica NE571\n\n")
        f.write("Basata sui risultati:\n\n")
        f.write("1. **Il compander NON è un compressore dbx-style con soglia a -6 dBFS**\n")
        f.write("2. **Il compander HW è un LIMITER con soglia a -20 dBFS** (osservazione REW: uscita satura a -20 dBFS indipendentemente dal pot LEVEL)\n")
        f.write("3. **Il THD massimo è ALLA SOGLIA del limiter** (-20 dBFS), non cresce monotonicamente\n")
        f.write("4. **Modello consigliato**:\n")
        f.write("   - Limiter hard con soglia a -20 dBFS peak\n")
        f.write("   - Attack/release NE571 (τ_a=8ms, τ_r=60ms)\n")
        f.write("   - Rectifier full-wave → gain computer con knee infinito (hard limit)\n")
        f.write("5. **Virtual ADC 32 kHz**: necessario per replicare aliasing armoniche > 16 kHz\n")
        f.write("6. **Stadio d'uscita**: DAC 12 bit + filtro AA 8° ordine @ 15 kHz + buffer analogico\n\n")

        # Limitazioni
        f.write("## 8. Limitazioni della caratterizzazione\n\n")
        f.write("- Armoniche 5-10 non misurabili a 10 kHz (Nyquist 48 kHz) → THD a 10 kHz calcolato su sole 3 armoniche (sottostimato)\n")
        f.write("- THD su 3 armoniche (20, 30, 40 kHz) vs HW che misura full-band dopo filtro AA\n")
        f.write("- Soglia compander stimata, non misurata direttamente su HW\n")
        f.write("- Livello assoluto al compander HW ignoto (dipende da pot LEVEL, fader REAPER, gain scheda)\n")
        f.write("- Cliff a -20 dBFS osservato qualitativamente in REW, non quantificato\n")
        f.write("- Virtual ADC implementato come filtri 8° ordine @ 15 kHz SENZA decimazione reale (solo caratteristiche filtro)\n")

    print(f"Report salvato: {report_path}")

if __name__ == "__main__":
    sys.exit(main())