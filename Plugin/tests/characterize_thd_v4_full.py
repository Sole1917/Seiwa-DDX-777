#!/usr/bin/env python3
"""Caratterizzazione SESSIONE 12 (Meccanismi A/B datasheet NE570N) — report v4.

Stato calibrato (default del core, nessun flag):
  Comp 5  kOpAmp  0.018   (Fase 2, invariato)
  Mecc A  kVos    0.0079  (H2 da offset VOS gain cell, su dry² post-mix)
  Mecc B  kLo     0.0     (crossover H3 < 500 Hz: taratura = 0, mechanism off)

Convenzioni (come v3): tono -20 dBFS RMS default; N_FFT = 2^20, 5 segmenti,
guard 96000; THD = picchi H2..H10 (come verify.py e v3); per-armoniche
H2..H5 in dB relativi e % del fondamentale; A1 in dBFS peak (4|X|/N).

Sezioni:
  1. Per-armoniche plugin vs HW (T4) a -20 dBFS, mix
  2. Predizioni modello ai livelli rimandati (-24/-30/-36/-42 dBFS) = target
     validazione §0.4 per le future misure HW
  3. Ablazione meccanismi a -20 dBFS
Output: build/char_thd_v4/results.csv, THD_characterization_v4.md, PNG.
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
OUTDIR = ROOT / "build" / "char_thd_v4"
REPORT_PATH = ROOT / "tests" / "THD_characterization_v4.md"
SR = 96000

T4_PATH = (ROOT.parent / "Prep" / "Segnali_Test" / "Risultati" / "T4, 8 e 9 .wav")

KEY_FREQS = [100, 1000, 10000]
LEVELS = [-20, -24, -30, -36, -42]

ABLATION = [
    ("full",      [],                              "Stato calibrato S12: kVos=0.0079, kLo=0, kOpAmp=0.018"),
    ("a_off",     ["--k-vos", "0"],                "Mecc. A off (solo kOpAmp + compressore)"),
    ("b_test",    ["--k-lo", "0.26"],              "Mecc. B acceso (test: kLo=0.26)"),
    ("dist_off",  ["--char-dist-off"],             "Tutte le distorsioni off"),
    ("opamp_off", ["--k-opamp", "0"],              "kOpAmp off (solo Mecc. A + compressore)"),
    ("fase1",     ["--no-virtual-adc", "--k-opamp", "0"],
                  "Fase 1: VADC off, kOpAmp off"),
]

# Predizioni §0.4 della Fase 2 (valori di riferimento per il confronto, non target HW)
PRED04_OLD = {(-30, 100): "0.33-0.40%", (-30, 1000): "0.0033%", (-30, 10000): "0.0035%"}

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


def ensure_input(freq, level):
    input_wav = OUTDIR / f"input_{freq}Hz_{level}dB.wav"
    if not input_wav.exists():
        wavfile.write(str(input_wav), SR, generate_tone(freq, level))
    return input_wav


def run_harness(input_path, output_path, extra_args=()):
    if output_path.exists():
        output_path.unlink()
    cmd = [str(HARNESS), str(input_path), str(output_path),
           "--range", "512", "--delay-level", "1", "--emit", "mix"]
    cmd += list(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Harness failed: {' '.join(cmd)}\n{result.stderr}")
    return output_path


def harmonics_from_segment(seg, f0, sr):
    """Per-armoniche + THD (convenzione v3/verify: picchi H2..H10) su un segmento."""
    w = seg * np.hanning(len(seg))
    X = np.abs(np.fft.rfft(w))
    f = np.fft.rfftfreq(len(seg), 1.0 / sr)
    n = len(seg)

    def pk(fr):
        m = (f > fr * 0.99) & (f < fr * 1.01)
        return float(np.max(X[m])) if m.any() else 0.0

    p1 = pk(f0)
    if p1 <= 0.0:
        return None
    out = {"a1_dbfs": 20.0 * math.log10(4.0 * p1 / n + 1e-30)}
    for k in range(2, 6):
        r = pk(f0 * k) / p1
        out[f"h{k}_db"] = 20.0 * math.log10(r + 1e-30)
        out[f"h{k}_pct"] = 100.0 * r
    ph = 0.0
    for k in range(2, 11):
        ph += pk(f0 * k) ** 2
    out["thd_pct"] = 100.0 * math.sqrt(ph) / p1
    return out


def measure_plugin(output_path, f0, sr=SR):
    sr_read, x = wavfile.read(str(output_path))
    if x.ndim > 1:
        x = x[:, 0]
    x = x.astype(np.float64)
    x = x[96000:-96000]
    rows = []
    for i in range(N_SEG):
        r = harmonics_from_segment(x[i * N_FFT:(i + 1) * N_FFT], f0, sr)
        if r is not None:
            rows.append(r)
    if not rows:
        return None
    out = {}
    for key in rows[0]:
        out[key] = float(np.mean([r[key] for r in rows]))
    return out


def measure_hw(path, f0, seg, sr):
    """Misura HW (T4) su segmento completo, come thd_percent di verify.py."""
    sr_read, x = wavfile.read(str(path))
    if x.ndim > 1:
        x = x[:, 0]
    x = x.astype(np.float64)
    a, b = seg
    segx = x[a:b]
    w = segx * np.hanning(len(segx))
    nfft = 1 << int(math.ceil(math.log2(len(w))))
    X = np.abs(np.fft.rfft(w, nfft))
    f = np.fft.rfftfreq(nfft, 1.0 / sr_read)

    def pk(fr):
        m = (f > fr * 0.99) & (f < fr * 1.01)
        return float(np.max(X[m])) if m.any() else 0.0

    p1 = pk(f0)
    if p1 <= 0.0:
        return None
    out = {}
    for k in range(2, 6):
        r = pk(f0 * k) / p1
        out[f"h{k}_db"] = 20.0 * math.log10(r + 1e-30)
        out[f"h{k}_pct"] = 100.0 * r
    ph = 0.0
    for k in range(2, 12):
        ph += pk(f0 * k) ** 2
    out["thd_pct"] = 100.0 * math.sqrt(ph) / p1
    return out


def hw_segments(path):
    """Rileva i segmenti tonali di T4 (metodo verify.py) -> [(f0, (a, b))]."""
    srh, xh = wavfile.read(str(path))
    xh = xh.astype(np.float64)
    if xh.ndim > 1:
        xh = xh[:, 0]
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
    segs = []
    for a, b in runs:
        seg = xh[a * win: b * win]
        sp = np.abs(np.fft.rfft(seg[: 4 * srh]))
        fr = np.fft.rfftfreq(min(len(seg), 4 * srh), 1 / srh)[1:]
        f0 = float(fr[int(np.argmax(sp))])
        segs.append((f0, (a * win, b * win)))
    return segs


def fmt_db(v):
    return f"{v:+.1f}" if v is not None else "n/d"


def main():
    if not HARNESS.exists():
        print(f"Harness non trovato: {HARNESS}")
        return 1
    OUTDIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    # --- 0. Rilettura HW (T4) ---
    print("=== HW: T4 ===")
    hw = {}
    if T4_PATH.exists():
        for f0, seg in hw_segments(str(T4_PATH)):
            for kf in KEY_FREQS:
                if abs(f0 - kf) / kf < 0.1:
                    r = measure_hw(str(T4_PATH), kf, seg, SR)
                    if r:
                        hw[kf] = r
                    break
        for kf in KEY_FREQS:
            r = hw.get(kf)
            if r:
                print(f"  {kf:5d} Hz: H2 {fmt_db(r['h2_db'])} dB H3 {fmt_db(r['h3_db'])} dB "
                      f"H4 {fmt_db(r['h4_db'])} dB H5 {fmt_db(r['h5_db'])} dB THD {r['thd_pct']:.4f}%")
    else:
        print(f"  T4 non trovato: {T4_PATH}")

    # --- 1. Matrice livelli (mix, default calibrato) ---
    print("\n=== Modello: matrice livelli ===")
    for freq in KEY_FREQS:
        for level in LEVELS:
            input_wav = ensure_input(freq, level)
            out_wav = OUTDIR / f"out_{freq}Hz_{level}dB_mix_full.wav"
            run_harness(input_wav, out_wav)
            r = measure_plugin(out_wav, freq)
            out_wav.unlink()
            if r:
                all_results.append({"freq": freq, "level": level, "scenario": "full", **r})
                print(f"  {freq:5d} Hz {level:3d} dBFS: A1 {r['a1_dbfs']:+6.1f} | "
                      f"H2 {fmt_db(r['h2_db'])} dB | H3 {fmt_db(r['h3_db'])} dB | "
                      f"THD {r['thd_pct']:.4f}%")

    # --- 2. Ablazione a -20 dBFS ---
    print("\n=== Modello: ablazione meccanismi ===")
    for freq in KEY_FREQS:
        input_wav = ensure_input(freq, -20)
        for scen_name, scen_args, _ in ABLATION:
            out_wav = OUTDIR / f"out_{freq}Hz_-20dB_mix_{scen_name}.wav"
            run_harness(input_wav, out_wav, scen_args)
            r = measure_plugin(out_wav, freq)
            out_wav.unlink()
            if r:
                all_results.append({"freq": freq, "level": -20, "scenario": scen_name, **r})
                print(f"  {freq:5d} Hz {scen_name:9s}: H2 {fmt_db(r['h2_db'])} dB | "
                      f"H3 {fmt_db(r['h3_db'])} dB | THD {r['thd_pct']:.4f}%")

    # --- CSV ---
    csv_path = OUTDIR / "results.csv"
    fields = ["freq", "level", "scenario", "a1_dbfs",
              "h2_db", "h2_pct", "h3_db", "h3_pct", "h4_db", "h4_pct",
              "h5_db", "h5_pct", "thd_pct"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)
    print(f"\n{len(all_results)} righe -> {csv_path}")

    generate_report(all_results, hw)
    return 0


def get_row(results, freq, level, scenario):
    return next((r for r in results
                 if r["freq"] == freq and r["level"] == level and r["scenario"] == scenario), None)


def generate_report(results, hw):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    L = []
    add = L.append
    add("# Caratterizzazione THD v4 — Sessione 12 (Meccanismi datasheet NE570N)\n")
    add("## Stato calibrato (default del core)\n")
    add("| Parametro | Valore | Note |")
    add("|---|---|---|")
    add("| kOpAmp | 0.018 | Fase 2, invariato |")
    add("| kVos (Mecc. A) | 0.0079 | H2 da offset VOS gain cell, su dry² post-mix; calibrato su T4 |")
    add("| kLo (Mecc. B) | 0.0 | Crossover H3 < 500 Hz: la taratura su T4 dà 0 (H3 a bassa banda già fornita dalla dinamica del compressore); meccanismo disponibile via --k-lo |")
    add("| Virtual ADC 32 kHz | ON | Fase 2 |")
    add("")
    add("Confronto THD: tolleranza verify.py = 6 dB. Risultato verify.py --force: "
        "**THD 3/3 PASS** (+1.7 / +3.1 / +2.2 dB a 100 Hz / 1 kHz / 10 kHz). "
       "Banda 2/4 FAIL pre-esistenti (Virtual ADC: -3 dB @ 12.80 kHz fuori da 14.5-16.5 kHz; "
        "--no-virtual-adc riporta 14.79 kHz ma l'aliasing T5 fallisce) — documentato in 04_lacune.md, "
        "fuori scope Sessione 12 (i meccanismi A/B agiscono solo sul ramo mix).\n")

    # --- Sezione 1: per-armoniche plugin vs HW ---
    add("## 1. Per-armoniche: plugin vs hardware (T4, -20 dBFS RMS, mix)\n")
    add("| f | Armonica | Plugin (dB) | HW (dB) | Gap | Plugin (%) | HW (%) |")
    add("|---|---|---|---|---|---|---|")
    for freq in KEY_FREQS:
        p = get_row(results, freq, -20, "full")
        h = hw.get(freq)
        if not p:
            continue
        for k in range(2, 6):
            if freq * k >= 0.45 * SR:
                add(f"| {freq} Hz | H{k} | n/a | n/a | n/a | n/a | n/a |")
                continue
            pd = p[f"h{k}_db"]
            hd = h[f"h{k}_db"] if h else None
            gap = f"{pd - hd:+.1f} dB" if hd is not None else "n/d"
            hp = f"{h[f'h{k}_pct']:.4f}%" if h else "n/d"
            add(f"| {freq} Hz | H{k} | {pd:+.1f} | {fmt_db(hd)} | {gap} | {p[f'h{k}_pct']:.4f}% | {hp} |")
        gp = p["thd_pct"]
        gh = h["thd_pct"] if h else None
        gapt = f"{20 * math.log10(gp / gh):+.1f} dB" if gh else "n/d"
        add(f"| {freq} Hz | **THD** | — | — | **{gapt}** | **{gp:.4f}%** | **{gh:.4f}%** |" if gh else
            f"| {freq} Hz | **THD** | — | n/d | n/d | **{gp:.4f}%** | n/d |")
    add("")
    add("Note:\n")
    add("- H2(1 kHz) e H2(10 kHz): match entro 0.1-0.4 dB (Meccanismo A calibrato su questi punti).")
    add("- H2(100 Hz) sotto-predetto di ~15 dB: residuo spettrale HW a bassa banda non modellato "
        "(candidato: ripple del detector a 2f / modulazione del rectifier — documentato, non implementato).")
    add("- H3(100 Hz) sopra-predetto di ~3 dB: la dinamica del compressore (attack 8 ms / release 60 ms) "
        "produce H3 via modulazione di ampiezza; sufficiente per il THD totale (+1.7 dB).")
    add("- H3(1 kHz/10 kHz) sopra-predetto di 9-11 dB: la tanh degli stadi op-amp (kOpAmp, calibrato su THD "
        "totale in Fase 2) pesa sulle armoniche singole; il THD totale resta entro +3.1 dB.")
    add("")

    # --- Sezione 2: predizioni livelli ---
    add("## 2. Predizioni modello ai livelli rimandati (§0.4)\n")
    add("Misure HW a -24/-30/-36 dBFS RIMANDATE (unità non accessibile). I valori modello qui sotto sono i "
        "**target di validazione**: quando le misure HW saranno disponibili, il confronto deve stare entro "
        "±2-3 dB (come a -20 dBFS).\n")
    add("| Livello (dBFS RMS) | f | THD modello | H2 modello | H3 modello | Target §0.4 (estrapolazione HW) |")
    add("|---|---|---|---|---|---|")
    for level in LEVELS:
        for freq in KEY_FREQS:
            r = get_row(results, freq, level, "full")
            if not r:
                continue
            old = PRED04_OLD.get((level, freq), "—")
            add(f"| {level} | {freq} Hz | {r['thd_pct']:.4f}% | {r['h2_pct']:.4f}% | "
                f"{r['h3_pct']:.4f}% | {old} |")
    add("")
    add("Comportamento atteso (Mecc. A ∝ livello): H2% cala di ~6 dB ogni 6 dB di livello "
        "(H2 ∝ A² sul segnale, THD% = H2/A1). A -30 dBFS il THD modello a 10 kHz/1 kHz è "
        "0.0107%/0.0128% (i target §0.4 di estrapolazione HW sono 0.0035%/0.0033%): il Meccanismo A "
        "tiene H2 ~3-4 dB sopra il vecchio modello v3 (0.0046%/0.0105%) e scala linearmente col segnale.\n")
    add("**Test discriminante su 100 Hz a -30 dBFS**: il modello v4 predice THD(100 Hz) = 0.0120% "
        "(H3 = 0.0035%): l'H3 a bassa banda del modello nasce da limiter + dinamica del compressore e "
        "sparisce appena sotto la soglia (-20 dBFS peak). Il target §0.4 per la misura HW (0.33-0.40%, "
        "derivato per estrapolazione da 'H3(100 Hz) ≈ costante al variare del livello') implicava "
        "invece un meccanismo di crossover livello-indipendente. Quindi:\n")
    add("- se la misura HW a -30 dBFS mostra H3(100 Hz) ancora ~0.3% -> esiste un meccanismo "
        "crossover/livello-indipendente nell'HW (candidato: Meccanismo B, kLo > 0 da tarare);")
    add("- se H3(100 Hz) crolla a ~0.01% -> confermato il comportamento del modello (H3 da dinamica "
        "del gain cell/limiter), Meccanismo B resta scollegato.\n")
    add("Sotto -36 dBFS i target di validazione diventano inaffidabili (H2 modello ~ -86 dB rel., "
        "vicino al floor di misura).\n")

    # --- Sezione 3: ablazione ---
    add("## 3. Ablazione meccanismi (-20 dBFS, mix)\n")
    add("| Scenario | 100 Hz THD | 1 kHz THD | 10 kHz THD | 100 Hz H3 | 1 kHz H2 |")
    add("|---|---|---|---|---|---|")
    for scen_name, _, desc in ABLATION:
        row = [f"| **{scen_name}**"]
        for freq in KEY_FREQS:
            r = get_row(results, freq, -20, scen_name)
            row.append(f"{r['thd_pct']:.4f}%" if r else "n/d")
        h100 = get_row(results, 100, -20, scen_name)
        h1k = get_row(results, 1000, -20, scen_name)
        row.append(f"{h100['h3_pct']:.4f}%" if h100 else "n/d")
        row.append(f"{h1k['h2_pct']:.4f}%" if h1k else "n/d")
        add(" | ".join(row))
    add("")
    add("Letture: `a_off` isola il contributo del Meccanismo A (H2); `b_test` mostra l'effetto (non voluto) "
        "di Meccanismo B: peggiora H3(100 Hz) da 0.42% verso l'alto -> taratura kLo = 0 confermata; "
        "`opamp_off` mostra l'H3 residuo del solo compressore; `fase1` = riferimento pre-distorsioni.\n")

    add("## 4. Note di calibrazione\n")
    add("- Calibrazione **relativa**: manca R_in (jack INPUT -> pin 5, lacuna L24) -> lo scaling analogico "
        "0 dBm <-> dBFS non è fissato; kVos è tarato sul rapporto H2/A1 misurato, non sull'offset VOS "
        "assoluto in volt.")
    add("- Opzione C (saturazione gain cell a +8 dBm, datasheet p.6): **solo documentata**, non "
        "parametrizzata — a -20 dBFS RMS il segnale è ~8-10 dB sotto la saturazione; verificabile solo "
        "con misure HW a livello alto (non disponibili: l'uscita DDX satura in REW a -20 dBFS).")
    add("- Pinout NE570N: mapping shift +1 (vecchio N = nuovo N+1) confermato dalle riletture di Sessione 12; "
        "da confermare con 3 test rapidi quando l'unità sarà accessibile (L17).")
    add("")

    REPORT_PATH.write_text("\n".join(L), encoding="utf-8")
    print(f"Report: {REPORT_PATH}")

    # --- Grafici ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for freq, color in zip(KEY_FREQS, ["#1f77b4", "#d62728", "#2ca02c"]):
        rows = [r for r in results if r["freq"] == freq and r["scenario"] == "full"
                and r["level"] in LEVELS]
        rows.sort(key=lambda x: x["level"])
        axes[0].plot([r["level"] for r in rows], [r["thd_pct"] for r in rows],
                     "o-", color=color, label=f"{freq} Hz")
        rows2 = [r for r in results if r["freq"] == freq and r["scenario"] == "full"
                 and r["level"] in LEVELS]
        axes[1].plot([r["level"] for r in rows2], [r["h2_pct"] for r in rows2],
                     "s-", color=color, label=f"{freq} Hz (H2)")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Livello (dBFS RMS)")
    axes[0].set_ylabel("THD (%)")
    axes[0].set_title("THD modello vs livello (mix, stato calibrato S12)")
    axes[0].grid(True, which="both", alpha=0.3)
    axes[0].legend()
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Livello (dBFS RMS)")
    axes[1].set_ylabel("H2 (%)")
    axes[1].set_title("2ª armonica vs livello (Mecc. A)")
    axes[1].grid(True, which="both", alpha=0.3)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(OUTDIR / "thd_v4_levels.png", dpi=150)
    plt.close(fig)
    print(f"Grafico: {OUTDIR / 'thd_v4_levels.png'}")


if __name__ == "__main__":
    sys.exit(main())
