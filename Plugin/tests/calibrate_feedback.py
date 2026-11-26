#!/usr/bin/env python3
"""
calibrate_feedback.py — calibra il modello del feedback a reostato (P1, 13c).

Misure: per FB = 0 / 25 / 50 / 75 / 100 % (RANGE 64 -> D ~ 66.4 ms, tono
1 kHz -20 dBFS, burst 20 ms) conta le ripetizioni (eco) nell'uscita wet.

Target HW (utente):
    FB  0% -> 1 ripetizione
    FB 25% -> 2-3
    FB 50% -> 5-10
    FB 75% -> 15-30
    FB100% -> autoscillazione a decadimento lento (>= 20 eco,
              la n-esima eco deve restare > 30% della 1-esima per n = 20)

Uso:
    python tests/calibrate_feedback.py [--loop-scale ..] [--bias-span ..]

I coefficienti P3 (JFET/M5221/NE571) restano ai valori fisici di default del
core; qui si tarano solo i parametri del loop (loop-scale, bias-span) e la
tabella kLoopGain in DDX777Core.h.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "build" / "Release" / "ddx_harness.exe"
OUTDIR = ROOT / "build" / "verify_out"
SR = 96000

TARGETS = [
    (0.0, 1, 1),
    (0.25, 2, 3),
    (0.5, 5, 10),
    (0.75, 15, 30),
    (1.0, 20, 40),   # FB=1: minimo 20 (decadimento lento; massimo = buffer)
]


def synth(burst_db=-20.0, f=1000.0, dur_burst=0.02, total=3.0):
    n = int(total * SR)
    x = np.zeros(n)
    nb = int(dur_burst * SR)
    t = np.arange(nb) / SR
    x[:nb] = (10 ** (burst_db / 20.0)) * np.sin(2 * np.pi * f * t)
    nf = int(0.002 * SR)
    x[:nf] *= np.linspace(0, 1, nf)
    x[nb - nf:nb] *= np.linspace(1, 0, nf)
    return x.astype(np.float32)


def run_harness(inp, outp, *args):
    outp = Path(outp)
    if outp.exists():
        outp.unlink()
    cmd = [str(HARNESS), str(inp), str(outp)] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"harness failed: {r.stderr}")


def echo_analysis(wet):
    """Ritorna (n_eco, tempi_ms, ampiezze_normalizzate_alla_1a)."""
    env = np.abs(wet)
    D_ms = 66.4
    D = D_ms / 1000.0 * SR
    # la 1a eco e' il primo picco dopo ~D/2 (il burst e' a t=0)
    search_from = int(0.5 * D)
    i1 = int(search_from + np.argmax(env[search_from:]))
    a1 = env[i1]
    if a1 < 1e-6:
        return 0, [], []
    # soglia = max(2% della 1a eco, 3 LSB): i tick del quantizzatore 12 bit
    # (hiss < 0.5 LSB che quantizza a ±1 LSB) non devono contare come eco
    thr = max(0.02 * a1, 3.0 / 2047.0)
    peaks = [i1]
    i = i1 + int(0.9 * D)   # un picco per slot (il tono 1 kHz ha 2 cicli/eco)
    while i < len(env) - 6:
        if env[i] >= thr and env[i] >= max(env[i - 5:i + 6]):
            peaks.append(i)
            i += int(0.9 * D)
            continue
        i += 1
    times = [p / SR * 1000.0 for p in peaks]
    amps = [env[p] / a1 for p in peaks]
    return len(peaks), times, amps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop-scale", type=float, default=None)
    ap.add_argument("--bias-span", type=float, default=None)
    args = ap.parse_args()

    if not HARNESS.exists():
        print(f"harness non trovato: {HARNESS}")
        return 2

    OUTDIR.mkdir(parents=True, exist_ok=True)
    inp = OUTDIR / "fb_tone.wav"
    wavfile.write(str(inp), SR, synth())

    extra = []
    if args.loop_scale is not None:
        extra += ["--loop-scale", f"{args.loop_scale}"]
    if args.bias_span is not None:
        extra += ["--bias-span", f"{args.bias_span}"]

    print(f"parametri loop: loop-scale={args.loop_scale or 'def'} "
          f"bias-span={args.bias_span or 'def'}\n")
    print(f"{'FB':>5} {'eco':>4} {'target':>8}  stato  dettaglio")

    all_ok = True
    for fb, lo, hi in TARGETS:
        outp = OUTDIR / f"fb_{fb:.2f}.wav"
        run_harness(inp, outp, "--range", "64", "--factor", "1",
                    "--delay-level", "1", "--feedback", f"{fb}",
                    "--emit", "wet", *extra)
        sr, wet = wavfile.read(str(outp))
        wet = wet.astype(np.float64)
        n, times, amps = echo_analysis(wet)

        if fb == 1.0:
            ok = n >= lo
            detail = (f"ultimo/1o = {amps[-1]:.3f}" if amps else "n/d")
            target = f">= {lo}"
        else:
            ok = lo <= n <= hi
            detail = f"1o->2o = {amps[1]:.3f}" if len(amps) > 1 else "solo 1"
            target = f"{lo}-{hi}"

        all_ok &= ok
        print(f"{fb*100:5.0f} {n:4d} {target:>8}  "
              f"{'ok  ' if ok else 'FAIL'}  {detail}")

    print("\ncalibrazione:", "OK (tutti i target rispettati)" if all_ok
          else "NON ok (aggiustare la tabella kLoopGain / loop-scale / bias-span)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
