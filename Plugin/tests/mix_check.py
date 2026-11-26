#!/usr/bin/env python3
import os, sys, numpy as np
from scipy.io import wavfile
from scipy import signal
import subprocess

SR = 96000
BASE_DIR = r"<PROJECT_ROOT>\Prep\Segnali_Test\Risultati"
OUT_DIR = r"<PROJECT_ROOT>\Plugin\build\meas_13i"
HARNESS = r"<PROJECT_ROOT>\Plugin\build\Release\ddx_harness.exe"

os.makedirs(OUT_DIR, exist_ok=True)

def load_wav(path):
    sr, x = wavfile.read(path)
    if x.ndim > 1:
        x = x[:, 0]
    orig_dtype = x.dtype
    x = x.astype(np.float64)
    if np.issubdtype(orig_dtype, np.integer):
        x = x / (float(np.iinfo(orig_dtype).max) + 1.0)
    return sr, x

baseline_content = "11730.7 0.957 3.020 14000.0 2.500 12.000 10400.5 1.076 16500.0 0.539 14200.0 0.400 15000.0 3.000 48000.0 24000.0 14000.0 28000.0 48000.0"
with open(os.path.join(OUT_DIR, "baseline.txt"), "w") as f:
    f.write(baseline_content)

imp = np.zeros(int(2 * SR))
imp[0] = 1.0
imp_path = os.path.join(OUT_DIR, "impulse_short.wav")
wavfile.write(imp_path, SR, imp.astype(np.float32))

print("Rendering impulse with FB=0, DELAY=10, RANGE=512...")
out_wav = os.path.join(OUT_DIR, "mix_test_fb0_delay10.wav")
result = subprocess.run([
    r"<PROJECT_ROOT>\Plugin\build\Release\ddx_harness.exe",
    r"<PROJECT_ROOT>\Prep\Segnali_Test\01_impulse_single.wav",
    out_wav,
    "--range", "512", "--feedback", "0", "--delay-level", "1",
    "--ffilter", os.path.join(OUT_DIR, "baseline.txt")
], capture_output=True, text=True)

print("Return code:", result.returncode)
print("stderr:", result.stderr)

sr, y = load_wav(out_wav)
print("Output length: %.2fs, peak=%.2f dBFS" % (len(y)/SR, 20*np.log10(np.max(np.abs(y)))))

dry_window = y[0:4800]
first_echo_start = int(0.54 * SR)
first_echo_window = y[first_echo_start:first_echo_start+4800]

dry_rms = 20*np.log10(np.sqrt(np.mean(dry_window**2)) + 1e-12)
dry_peak = 20*np.log10(np.max(np.abs(dry_window)) + 1e-12)
echo_rms = 20*np.log10(np.sqrt(np.mean(first_echo_window**2)) + 1e-12)
echo_peak = 20*np.log10(np.max(np.abs(first_echo_window)) + 1e-12)

print("Dry RMS: %.2f dBFS, Peak: %.2f dBFS" % (dry_rms, dry_peak))
print("Echo RMS: %.2f dBFS, Peak: %.2f dBFS" % (echo_rms, echo_peak))
print("Peak ratio (dry vs echo): %.2f dB" % (dry_peak - echo_peak))
print("RMS ratio (dry vs echo): %.2f dB" % (dry_rms - echo_rms))

expected_wet_peak = 20 * np.log10(0.95)
print("Expected wet peak (mixLevel=0.95): %.2f dBFS" % expected_wet_peak)
print("Expected dry vs echo peak ratio: %.2f dB" % (-20*np.log10(0.95)))

print("\nRendering with FB=0, DELAY=0...")
out_wav2 = os.path.join(OUT_DIR, "mix_test_fb0_delay0.wav")
result2 = subprocess.run([
    r"<PROJECT_ROOT>\Plugin\build\Release\ddx_harness.exe",
    r"<PROJECT_ROOT>\Prep\Segnali_Test\01_impulse_single.wav",
    os.path.join(OUT_DIR, "mix_test_fb0_delay0.wav"),
    "--range", "512", "--feedback", "0", "--delay-level", "0",
    "--ffilter", os.path.join(OUT_DIR, "baseline.txt")
], capture_output=True, text=True)
print("Return code:", result2.returncode)
print("stderr:", result2.stderr)

sr, y2 = load_wav(out_wav2)
dry2_rms = 20*np.log10(np.sqrt(np.mean(y2[:4800]**2)) + 1e-12)
dry2_peak = 20*np.log10(np.max(np.abs(y2[:4800])) + 1e-12)
print("DELAY=0: RMS=%.2f dBFS, Peak=%.2f dBFS" % (dry2_rms, dry2_peak))

# Save results to JSON
import json
results = {
    "dry_rms_db": dry_rms,
    "dry_peak_db": dry_peak,
    "echo_rms_db": echo_rms,
    "echo_peak_db": echo_peak,
    "peak_ratio_db": dry_peak - echo_peak,
    "rms_ratio_db": dry_rms - echo_rms,
    "dry0_rms_db": dry2_rms,
    "dry0_peak_db": dry2_peak,
    "expected_wet_peak_db": expected_wet_peak,
    "expected_ratio_db": -20*np.log10(0.95)
}
with open(os.path.join(OUT_DIR, "mix_check_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved to mix_check_results.json")