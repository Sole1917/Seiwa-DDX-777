"""Differenziale banda: Virtual ADC on/off, mecc. A/B fuori dal percorso wet/direct."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import verify as V

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "verify_out"
OUT.mkdir(parents=True, exist_ok=True)

swp = OUT / "flatsweep_diff.wav"
V.synth_flat_sweep(swp)

for tag, extra in [("adc_on", []), ("adc_off", ["--no-virtual-adc"])]:
    bw = OUT / f"band_wet_{tag}.wav"
    bd = OUT / f"band_direct_{tag}.wav"
    V.run_harness(swp, bw, "--range", "512", "--delay-level", "1", "--emit", "wet", *extra)
    V.run_harness(swp, bd, "--range", "512", "--delay-level", "1", "--emit", "direct", *extra)
    sr, wet = V.load(str(bw))
    _, direct = V.load(str(bd))
    our_dig, d_ours = V.band_ours_digital(sr, wet, direct, tsw=12.0)
    grid = V.BAND_GRID
    m_flat = (grid >= 100) & (grid <= V.BAND_FLAT_TO_HZ)
    ripple = float(max(abs(v) for v in our_dig[m_flat]))
    cut = V.first_cut(grid, our_dig)
    print(f"{tag}: delay={d_ours*1000:.1f} ms ripple(100-14k)={ripple:.2f} dB "
          f"cut=-3dB@{cut/1000:.2f} kHz")
    for g in (1000, 5000, 10000, 12000, 13000, 14000, 15000):
        i = min(range(len(grid)), key=lambda k: abs(grid[k] - g))
        print(f"   {g/1000:5.1f} kHz: {our_dig[i]:+7.2f} dB")
