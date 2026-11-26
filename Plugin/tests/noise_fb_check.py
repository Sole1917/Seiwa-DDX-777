#!/usr/bin/env python3
import os, sys, numpy as np
from scipy.io import wavfile
from scipy import signal
import subprocess
import json

SR = 96000
OUT_DIR = r"<PROJECT_ROOT>\Plugin\build\meas_13i"
HARNESS = r"<PROJECT_ROOT>\Plugin\build\Release\ddx_harness.exe"

os.makedirs(OUT_DIR, exist_ok=True)

def load_wav(path):
    sr, x = wavfile.read(path)
    if x.ndim > 1: x = x[:, 0]
    orig_dtype = x.dtype
    x = x.astype(np.float64)
    if np.issubdtype(orig_dtype, np.integer):
        x = x / (float(np.iinfo(orig_dtype).max) + 1.0)
    return sr, x

# Baseline filter file
baseline_content = "11730.7 0.957 3.020 14000.0 2.500 12.000 10400.5 1.076 16500.0 0.539 14200.0 0.400 15000.0 3.000 48000.0 24000.0 14000.0 28000.0 48000.0"
with open(os.path.join(OUT_DIR, "baseline.txt"), "w") as f:
    f.write(baseline_content)

def render_silence(fb_val, name):
    """Render silence (zeros input) with given feedback"""
    out_wav = os.path.join(OUT_DIR, f"silence_fb{fb_val}.wav")
    result = subprocess.run([
        HARNESS,
        # Input silence
        r"<PROJECT_ROOT>\Prep\Segnali_Test\Risultati\noise_maudioch1.wav",
        out_wav,
        "--range", "512",
        "--feedback", str(fb_val),
        "--delay-level", "1",
        "--ffilter", os.path.join(OUT_DIR, "baseline.txt")
    ], capture_output=True, text=True)
    print(f"  FB={fb_val}: Return code={result.returncode}")
    if result.returncode != 0:
        print(f"  stderr: {result.stderr}")
        return None
    sr, y = load_wav(out_wav)
    # Skip first 500ms
    skip = int(0.5 * SR)
    y = y[skip:]
    # Take 10s
    y = y[:10*SR]
    rms_db = 20*np.log10(np.sqrt(np.mean(y**2)) + 1e-12)
    peak_db = 20*np.log10(np.max(np.abs(y)) + 1e-12)
    return {"name": name, "fb": fb_val, "rms_db": rms_db, "peak_db": peak_db, "samples": len(y)}

def measure_noise(fb_val, name):
    return render_silence(fb_val, name)

print("=== Noise Measurement: FB=0 vs FB=10 ===")

# Use existing noise file for FB=0 reference
# Actually, let's render our own silence with the correct settings
fb0 = measure_noise(0, "FB=0")
fb10 = measure_noise(10, "FB=10")

if fb0 and fb10:
    print(f"\n=== Results ===")
    print(f"FB=0:  RMS={fb0['rms_db']:.2f} dBFS, Peak={fb0['peak_db']:.2f} dBFS")
    print(f"FB=10: RMS={fb10['rms_db']:.2f} dBFS, Peak={fb10['peak_db']:.2f} dBFS")
    print(f"Delta RMS: {fb10['rms_db'] - fb0['rms_db']:.2f} dB")
    print(f"Delta Peak: {fb10['peak_db'] - fb0['peak_db']:.2f} dB")

# Also test with the recorded noise files for comparison
print("\n=== Using recorded noise files ===")
for fname in ["noise_maudioch1.wav", "noise_peak 10, fdbck 0, delay 10  .wav", "noise_peak 10, fdbck 10, delay 10 .wav"]:
    path = os.path.join(r"<PROJECT_ROOT>\Prep\Segnali_Test\Risultati", fname)
    if os.path.exists(path):
        sr, x = load_wav(path)
        x = x[int(0.5*SR):]  # skip 0.5s
        x = x[:10*SR]
        rms_db = 20*np.log10(np.sqrt(np.mean(x**2)) + 1e-12)
        peak_db = 20*np.log10(np.max(np.abs(x)) + 1e-12)
        print(f"{fname}: RMS={rms_db:.2f} dBFS, Peak={peak_db:.2f} dBFS")

# Save results
results = {
    "fb0_rms_db": fb0["rms_db"] if fb0 else None,
    "fb0_peak_db": fb0["peak_db"] if fb0 else None,
    "fb10_rms_db": fb10["rms_db"] if fb10 else None,
    "fb10_peak_db": fb10["peak_db"] if fb10 else None,
}
with open(os.path.join(OUT_DIR, "noise_fb_comparison.json"), "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved to noise_fb_comparison.json")

def load_wav(path):
    sr, x = wavfile.read(path)
    if x.ndim > 1: x = x[:, 0]
    orig_dtype = x.dtype
    x = x.astype(np.float64)
    if np.issubdtype(orig_dtype, np.integer):
        x = x / (float(np.iinfo(orig_dtype).max) + 1.0)
    return sr, x