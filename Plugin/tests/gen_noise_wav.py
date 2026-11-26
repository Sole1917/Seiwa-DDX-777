import struct, sys
fs = 48000
total = int(1.6 * fs)
nstart = int(0.3 * fs)
nlen = int(0.2 * fs)
s = 42
def rng():
    global s
    s = (s * 1664525 + 1013904223) & 0xFFFFFFFF
    return (s >> 8) / 16777216.0
vals = [rng() * 2.0 - 1.0 for _ in range(nlen)]
acc = sum(v * v for v in vals) / nlen
scale = 0.05 / acc ** 0.5
data = []
for i in range(total):
    v = vals[i - nstart] * scale if (0 <= i - nstart < nlen) else 0.0
    data.append(v)
    data.append(v)
packed = struct.pack(f"<{len(data)}f", *data)
nbytes = len(packed)
header = b"RIFF" + struct.pack("<I", 36 + nbytes) + b"WAVE"
header += b"fmt " + struct.pack("<IHHIIHH", 16, 3, 2, fs, fs * 8, 8, 32)
header += b"data" + struct.pack("<I", nbytes)
open(sys.argv[1] if len(sys.argv) > 1 else "noise48k.wav", "wb").write(header + packed)
print("wav scritto", total, "frames")
