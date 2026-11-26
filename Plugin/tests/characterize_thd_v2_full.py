#!/usr/bin/env python3
"""Caratterizzazione completa FASE 1 in un'unica esecuzione"""

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
OUTDIR = ROOT / "build" / "char_thd_v2"
REPORT_PATH = ROOT / "tests" / "THD_characterization_v2.md"
SR = 96000

FREQS = [50, 100, 200, 500, 1000, 2000, 5000, 10000]
LEVELS = [-6, -12, -14, -18, -20, -24, -30, -36, -42]
MODES = ["wet", "mix", "direct"]
VARIANTS = ["full", "comp_off", "dist_off"]

Q4_SCENARIOS = [
    ("current", []),
    ("virtual_adc", ["--char-virtual-adc"]),
]

COMP_SWEEP = [-30, -28, -26, -24, -22, -20, -18, -16, -14, -12, -10]

N_FFT = 1 << 20
N_SEG = 5
SIGNAL_LEN = N_SEG * N_FFT + 2 * 96000
FADE_SAMPLES = int(0.01 * SR)

def generate_tone(freq, level_dbfs_rms, length=SIGNAL_LEN):
    peak_factor = math.sqrt(2)
    amplitude = peak_factor * 10 ** (level_dbfs_rms / 20.0)
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
        thd = measure_thd(seg, f0, sr)
        thds.append(thd)
    return np.mean(thds), np.std(thds), thds

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

def main():
    if not HARNESS.exists():
        print(f"Harness non trovato: {HARNESS}")
        return 1

    OUTDIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    # --- 1. Matrice completa ---
    print("=== FASE 1: Matrice completa (648 render) ===")
    total = len(FREQS) * len(LEVELS) * len(MODES) * len(VARIANTS)
    count = 0

    for freq in FREQS:
        for level in LEVELS:
            input_wav = OUTDIR / f"input_{freq}Hz_{level}dB.wav"
            if not input_wav.exists():
                print(f"  Generazione input {freq}Hz {level}dBFS...")
                x = generate_tone(freq, level)
                wavfile.write(str(input_wav), SR, x)

            for mode in MODES:
                for variant in VARIANTS:
                    count += 1
                    if count % 50 == 0:
                        print(f"[{count}/{total}] {freq}Hz {level}dB {mode} {variant}")

                    out_wav = OUTDIR / f"out_{freq}Hz_{level}dB_{mode}_{variant}.wav"
                    try:
                        run_harness(input_wav, out_wav, mode, variant)
                        thd_mean, thd_std, thds = measure_thd_5segments(out_wav, freq)
                        all_results.append({
                            "freq": freq, "level": level, "mode": mode,
                            "variant": variant, "scenario": "base",
                            "thd_pct": thd_mean, "thd_db": 20 * math.log10(thd_mean / 100.0) if thd_mean > 0 else -200,
                            "thd_std": thd_std, "thd_segments": str(thds)
                        })
                    except Exception as e:
                        print(f"    ERRORE: {e}")
                        all_results.append({
                            "freq": freq, "level": level, "mode": mode,
                            "variant": variant, "scenario": "base",
                            "thd_pct": None, "thd_db": None, "thd_std": None, "thd_segments": None
                        })
                    finally:
                        if out_wav.exists():
                            out_wav.unlink()

            if input_wav.exists():
                input_wav.unlink()

    # --- 2. Q4: 10 kHz -20 dBFS con virtual ADC ---
    print("\n=== FASE 1: Q4 Virtual ADC (2 render) ===")
    freq = 10000
    level = -20
    input_wav = OUTDIR / f"input_{freq}Hz_{level}dB.wav"
    if not input_wav.exists():
        x = generate_tone(freq, level)
        wavfile.write(str(input_wav), SR, x)

    for scen_name, scen_args in Q4_SCENARIOS:
        out_wav = OUTDIR / f"out_{freq}Hz_{level}dB_mix_full_{scen_name}.wav"
        try:
            run_harness(input_wav, out_wav, "mix", "full", scen_args)
            thd_mean, thd_std, thds = measure_thd_5segments(out_wav, freq)
            all_results.append({
                "freq": freq, "level": level, "mode": "mix",
                "variant": "full", "scenario": scen_name,
                "thd_pct": thd_mean, "thd_db": 20 * math.log10(thd_mean / 100.0) if thd_mean > 0 else -200,
                "thd_std": thd_std, "thd_segments": str(thds)
            })
            print(f"  Q4 {scen_name}: THD = {thd_mean:.4f}% ({20*math.log10(thd_mean/100):.1f} dB)")
        except Exception as e:
            print(f"    ERRORE: {e}")
        finally:
            if out_wav.exists():
                out_wav.unlink()

    if input_wav.exists():
        input_wav.unlink()

    # --- 3. Sweep limiter a 10 kHz ---
    print("\n=== FASE 1: Sweep limiter 10 kHz (11 render) ===")
    freq = 10000
    for level in COMP_SWEEP:
        input_wav = OUTDIR / f"input_{freq}Hz_{level}dB.wav"
        if not input_wav.exists():
            x = generate_tone(freq, level)
            wavfile.write(str(input_wav), SR, x)

        out_wav = OUTDIR / f"out_{freq}Hz_{level}dB_mix_dist_off.wav"
        try:
            run_harness(input_wav, out_wav, "mix", "dist_off")
            thd_mean, thd_std, thds = measure_thd_5segments(out_wav, freq)
            all_results.append({
                "freq": freq, "level": level, "mode": "mix",
                "variant": "dist_off", "scenario": "base",
                "thd_pct": thd_mean, "thd_db": 20 * math.log10(thd_mean / 100.0) if thd_mean > 0 else -200,
                "thd_std": thd_std, "thd_segments": str(thds)
            })
            print(f"  {level} dBFS: THD = {thd_mean:.4f}% ({20*math.log10(thd_mean/100):.1f} dB)")
        except Exception as e:
            print(f"    ERRORE: {e}")
        finally:
            if out_wav.exists():
                out_wav.unlink()

        if input_wav.exists():
            input_wav.unlink()

    # Salva CSV combinato
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

    # Genera report
    generate_report(all_results)
    return 0

def generate_report(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    valid = [r for r in results if r["thd_pct"] is not None]
    hw_targets = {100: 0.349, 1000: 0.033, 10000: 0.035}
    hw_db = {f: 20*math.log10(hw_targets[f]/100) for f in hw_targets}
    phase0 = {100: 0.180, 1000: 0.021, 10000: 0.0053}
    phase0_db = {100: -44.9, 1000: -67.8, 10000: -85.5}

    # Grafico 1: THD vs frequenza
    fig, ax = plt.subplots(figsize=(10, 6))
    for level in LEVELS:
        subset = [r for r in valid if r["level"] == level and r["mode"] == "mix" and r["variant"] == "full" and r["scenario"] == "base"]
        if not subset: continue
        subset.sort(key=lambda x: x["freq"])
        freqs = [r["freq"] for r in subset]
        thds = [r["thd_pct"] for r in subset]
        ax.loglog(freqs, thds, "o-", label=f"{level} dBFS")
    ax.set_xlabel("Frequenza (Hz)")
    ax.set_ylabel("THD (%)")
    ax.set_title("FASE 1 — THD vs Frequenza (modalità mix, variante completa)")
    ax.grid(True, which="both", ls="-", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTDIR / "THD_vs_freq.png", dpi=150)
    plt.close(fig)

    # Grafico 2: THD vs livello
    fig, ax = plt.subplots(figsize=(10, 6))
    for freq in FREQS:
        subset = [r for r in valid if r["freq"] == freq and r["mode"] == "mix" and r["variant"] == "full" and r["scenario"] == "base"]
        if not subset: continue
        subset.sort(key=lambda x: x["level"])
        levels = [r["level"] for r in subset]
        thds = [r["thd_pct"] for r in subset]
        ax.semilogx([abs(l) for l in levels], thds, "o-", label=f"{freq} Hz")
    ax.set_xlabel("Livello (|dBFS RMS|)")
    ax.set_ylabel("THD (%)")
    ax.set_title("FASE 1 — THD vs Livello (modalità mix, variante completa)")
    ax.grid(True, which="both", ls="-", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTDIR / "THD_vs_level.png", dpi=150)
    plt.close(fig)

    # Grafico 3: Confronto
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for idx, freq in enumerate([100, 1000, 10000]):
        ax = axes[idx]
        variants_to_plot = ["full", "comp_off", "dist_off"]
        labels = ["Completa", "Solo limiter\n(dist_off)", "Solo dist. uscita\n(comp_off)"]
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
        thds = []
        for v in variants_to_plot:
            r = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == v and x["scenario"] == "base"), None)
            thds.append(r["thd_pct"] if r else 0)
        bars = ax.bar(range(len(variants_to_plot)), thds, color=colors, alpha=0.7)
        ax.axhline(hw_targets[freq], color="red", linestyle="--", linewidth=2, label=f"HW target ({hw_targets[freq]:.3f}%)")
        ax.set_xticks(range(len(variants_to_plot)))
        ax.set_xticklabels(labels, rotation=15, ha="right")
        ax.set_ylabel("THD (%)")
        ax.set_title(f"FASE 1 — {freq} Hz @ -20 dBFS")
        ax.legend()
        ax.grid(True, axis="y", alpha=0.3)
        for bar, val in zip(bars, thds):
            ax.annotate(f"{val:.4f}%", xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)
    fig.suptitle("FASE 1 — Confronto THD plugin vs Hardware (modalità mix)")
    fig.tight_layout()
    fig.savefig(OUTDIR / "THD_comparison.png", dpi=150)
    plt.close(fig)

    # Report Markdown
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# THD Characterization Report — Seiwa DDX-777 — FASE 1 (Limiter -20 dBFS)\n\n")
        f.write(f"**Data**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Harness**: {HARNESS}\n")
        f.write(f"**Matrice completa**: {len(FREQS)} freq × {len(LEVELS)} livelli × 3 mode × 3 variant = {len(FREQS)*len(LEVELS)*3*3} render\n")
        f.write(f"**Q4**: 2 scenari a 10 kHz (-20 dBFS)\n")
        f.write(f"**Sweep limiter**: {len(COMP_SWEEP)} livelli a 10 kHz (dist_off)\n\n")

        f.write("## 1. Metodologia\n\n")
        f.write("- **Segnale**: sinusoide pura, durata 56.5 s (5×2²⁰ + 2s fade)\n")
        f.write("- **Livelli**: dBFS RMS (coerente con misure HW)\n")
        f.write("- **THD**: FFT 2²⁰ punti, finestra Hann, armoniche 2-10 (fino a Nyquist 48 kHz)\n")
        f.write("- **5 medie**: 5 segmenti non sovrapposti da 2²⁰ campioni\n")
        f.write("- **Armoniche misurabili a 10 kHz**: solo 2-4 (20, 30, 40 kHz)\n")
        f.write("- **Limiter**: soglia -20 dBFS peak, attack 8 ms, release 60 ms, hard knee\n\n")

        f.write("## 2. Tabelle THD % (modalità mix, variante full)\n\n")
        f.write("| Freq (Hz) | " + " | ".join(f"{l} dBFS" for l in LEVELS) + " |\n")
        f.write("|" + "|".join(["---"] * (len(LEVELS) + 1)) + "|\n")
        for freq in FREQS:
            row = [f"{freq}"]
            for level in LEVELS:
                r = next((x for x in valid if x["freq"] == freq and x["level"] == level and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == "base"), None)
                if r and r["thd_pct"] is not None:
                    row.append(f"{r['thd_pct']:.4f}%")
                else:
                    row.append("N/A")
            f.write("| " + " | ".join(row) + " |\n")
        f.write("\n")

        # Q4
        f.write("## 3. Q4 — Virtual ADC 32 kHz a 10 kHz (-20 dBFS)\n\n")
        f.write("| Scenario | THD (%) | THD (dB) | Note |\n")
        f.write("|----------|---------|----------|------|\n")
        r_cur = next((x for x in valid if x["freq"] == 10000 and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == "current"), None)
        r_vadc = next((x for x in valid if x["freq"] == 10000 and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == "virtual_adc"), None)
        if r_cur:
            f.write(f"| Plugin attuale (96 kHz) | {r_cur['thd_pct']:.4f}% | {r_cur['thd_db']:.1f} | |\n")
        if r_vadc:
            f.write(f"| Plugin + Virtual ADC 32 kHz | {r_vadc['thd_pct']:.4f}% | {r_vadc['thd_db']:.1f} | Filtri 8° @ 15 kHz |\n")
        f.write(f"| **HW target** | **0.0350%** | **{hw_db[10000]:.1f}** | Misura sessione 11 |\n\n")

        # Sweep
        f.write("## 4. Sweep Livello Limiter a 10 kHz (variante dist_off = solo limiter)\n\n")
        f.write("| Livello (dBFS RMS) | Peak (dBFS) | THD (%) | THD (dB) | Note |\n")
        f.write("|---|---|---|---|---|\n")
        for level in COMP_SWEEP:
            r = next((x for x in valid if x["freq"] == 10000 and x["level"] == level and x["mode"] == "mix" and x["variant"] == "dist_off" and x["scenario"] == "base"), None)
            if r and r["thd_pct"] is not None:
                peak_db = level + 3.0
                note = "SOPRA soglia (-20 dBFS peak)" if peak_db > -20 else "sotto soglia"
                f.write(f"| {level} | {peak_db:.1f} | {r['thd_pct']:.4f}% | {r['thd_db']:.1f} | {note} |\n")
        f.write("\n")

        # Analisi
        f.write("## 5. Analisi FASE 1\n\n")

        f.write("### Confronto Fase 0 (compander -6 dBFS) vs Fase 1 (limiter -20 dBFS)\n\n")
        f.write("| Freq | Fase 0 THD | Fase 1 THD | HW THD | Delta Fase1 vs HW (dB) |\n")
        f.write("|------|------------|------------|--------|------------------------|\n")
        for freq in [100, 1000, 10000]:
            r = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == "base"), None)
            if r:
                gap_db = 20 * math.log10((r["thd_pct"]/100) / (hw_targets[freq]/100))
                f.write(f"| {freq} Hz | {phase0[freq]:.4f}% ({phase0_db[freq]:.1f} dB) | {r['thd_pct']:.4f}% ({r['thd_db']:.1f} dB) | {hw_targets[freq]:.3f}% ({hw_db[freq]:.1f} dB) | {gap_db:+.1f} dB |\n")
        f.write("\n")

        f.write("### Q1 — Con il limiter a -20 dBFS, il THD a 100 Hz sale o scende? Di quanto?\n\n")
        f.write("Confronto **variante completa** vs **dist_off** (solo limiter):\n\n")
        f.write("| Freq (Hz) | THD completa | THD solo limiter | Contributo limiter |\n")
        f.write("|---|---|---|---|\n")
        for freq in [100, 1000, 10000]:
            r_full = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == "base"), None)
            r_lim = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "dist_off" and x["scenario"] == "base"), None)
            if r_full and r_lim:
                contrib_pct = math.sqrt(max(0, r_full["thd_pct"]**2 - r_lim["thd_pct"]**2))
                f.write(f"| {freq} | {r_full['thd_pct']:.4f}% | {r_lim['thd_pct']:.4f}% | {contrib_pct:.4f}% |\n")
        f.write("\n")

        f.write("### Q2 — Con il limiter a -20 dBFS, il THD a 10 kHz sale o scende? Il gap di 16.4 dB si riduce?\n\n")
        f.write("Confronto **variante completa** vs **comp_off** (solo distorsione uscita):\n\n")
        f.write("| Freq (Hz) | THD completa | THD solo dist. uscita | Contributo dist. uscita |\n")
        f.write("|---|---|---|---|\n")
        for freq in [100, 1000, 10000]:
            r_full = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == "base"), None)
            r_dist = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "comp_off" and x["scenario"] == "base"), None)
            if r_full and r_dist:
                contrib_pct = math.sqrt(max(0, r_full["thd_pct"]**2 - r_dist["thd_pct"]**2))
                f.write(f"| {freq} | {r_full['thd_pct']:.4f}% | {r_dist['thd_pct']:.4f}% | {contrib_pct:.4f}% |\n")
        f.write("\n")

        f.write("### Q3 — Il limiter hard introduce distorsione di clipping ai livelli sopra soglia? A quali livelli si attiva?\n\n")
        f.write("Sweep livello a 10 kHz (solo limiter, variante dist_off):\n\n")
        f.write("| Livello (dBFS RMS) | Peak (dBFS) | THD (%) | THD (dB) | Note |\n")
        f.write("|---|---|---|---|---|\n")
        for level in COMP_SWEEP:
            r = next((x for x in valid if x["freq"] == 10000 and x["level"] == level and x["mode"] == "mix" and x["variant"] == "dist_off" and x["scenario"] == "base"), None)
            if r and r["thd_pct"] is not None:
                peak_db = level + 3.0
                note = "SOPRA soglia (-20 dBFS peak)" if peak_db > -20 else "sotto soglia"
                f.write(f"| {level} | {peak_db:.1f} | {r['thd_pct']:.4f}% | {r['thd_db']:.1f} | {note} |\n")
        f.write("\n")

        f.write("### Q4 — Il virtual ADC 32 kHz ora contribuisce di più al THD a 10 kHz?\n\n")
        if r_cur and r_vadc:
            f.write(f"- **Plugin attuale (96 kHz)**: {r_cur['thd_pct']:.4f}% ({r_cur['thd_db']:.1f} dB)\n")
            f.write(f"- **Plugin + Virtual ADC 32 kHz**: {r_vadc['thd_pct']:.4f}% ({r_vadc['thd_db']:.1f} dB)\n")
            f.write(f"- **Target HW**: 0.0350% ({hw_db[10000]:.1f} dB)\n\n")
            if r_vadc["thd_pct"] > r_cur["thd_pct"]:
                diff_db = r_vadc["thd_db"] - r_cur["thd_db"]
                f.write(f"**Interpretazione**: Il Virtual ADC **aumenta** il THD di {diff_db:.1f} dB. L'aliasing contribuisce.\n")
            else:
                f.write("**Interpretazione**: Il Virtual ADC **non aumenta** (o riduce) il THD.\n")
            f.write("\n")

        f.write("## 6. Sintesi Gap vs Hardware\n\n")
        f.write("| Freq | Fase 1 THD | HW THD | Gap (dB) | Stato |\n")
        f.write("|------|------------|--------|----------|-------|\n")
        for freq in [100, 1000, 10000]:
            r = next((x for x in valid if x["freq"] == freq and x["level"] == -20 and x["mode"] == "mix" and x["variant"] == "full" and x["scenario"] == "base"), None)
            if r:
                gap = 20 * math.log10((r["thd_pct"]/100) / (hw_targets[freq]/100))
                if abs(gap) < 3:
                    status = "✓ Match (±3 dB)"
                elif gap > 0:
                    status = f"Plugin +{gap:.1f} dB (più distorto)"
                else:
                    status = f"Plugin {gap:.1f} dB (meno distorto)"
                f.write(f"| {freq} Hz | {r['thd_pct']:.4f}% | {hw_targets[freq]:.3f}% | {gap:+.1f} | {status} |\n")
        f.write("\n")

        f.write("## 7. Limitazioni\n\n")
        f.write("- Armoniche 5-10 non misurabili a 10 kHz (Nyquist 48 kHz) → THD a 10 kHz calcolato su sole 3 armoniche (sottostimato)\n")
        f.write("- THD su 3 armoniche (20, 30, 40 kHz) vs HW che misura full-band dopo filtro AA\n")
        f.write("- Livello assoluto al limiter HW ignoto (dipende da pot LEVEL, fader REAPER, gain scheda)\n")
        f.write("- Virtual ADC implementato come filtri 8° ordine @ 15 kHz SENZA decimazione reale (solo caratteristiche filtro)\n")

    print(f"Report salvato: {REPORT_PATH}")

if __name__ == "__main__":
    sys.exit(main())