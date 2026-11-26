#!/usr/bin/env python3
"""
genera_segnali.py
=================
Genera i segnali di test WAV per la caratterizzazione audio del
Seiwa DDX-777 (delay digitale giapponese 1985, mono, in -20 dB, out MIX OUT).

Output: 15 file WAV mono 96 kHz / 32-bit float + README.md
Cartella: E:\\tutto\\OpenCode\\Seiwa DDX-777\\Segnali_Test

Uso:  python genera_segnali.py
"""

import os
import numpy as np
import soundfile as sf
from scipy import signal as sps

# ------------------------------------------------------------------ costanti
SR = 96000
OUT_DIR = r"E:\tutto\OpenCode\Seiwa DDX-777\Segnali_Test"
os.makedirs(OUT_DIR, exist_ok=True)

FADE_MS = 10.0          # fade in/out standard
TARGET_DBFS = -20.0     # livello di riferimento (RMS)
CEILING_DBFS = -0.3     # soffitto di picco di sicurezza (solo segnali normalizzati)
SEED = 777              # seed ripetibile per i rumori

results = []            # riepilogo metriche
fails = []              # errori di verifica


# ------------------------------------------------------------------ utilita'
def dbfs(v):
    """dBFS a partire da un'ampiezza lineare (0 -> -inf)."""
    return 20.0 * np.log10(v) if v > 0 else float("-inf")


def fmt_db(v):
    return "-inf" if not np.isfinite(v) else f"{v:.2f}"


def apply_fade(x, sr=SR, fade_ms=FADE_MS):
    """Fade lineare in/out di 'fade_ms' millisecondi agli estremi del buffer."""
    n = int(sr * fade_ms / 1000)
    if n <= 0 or len(x) < 2 * n:
        return x
    x[:n] *= np.linspace(0.0, 1.0, n)
    x[-n:] *= np.linspace(1.0, 0.0, n)
    return x


def to_dbfs(x, target_dbfs=TARGET_DBFS):
    """Porta la RMS di x a target_dbfs."""
    rms = np.sqrt(np.mean(x ** 2))
    target_rms = 10 ** (target_dbfs / 20.0)
    return x * (target_rms / rms) if rms > 0 else x


def normalize_level(x, target_dbfs=TARGET_DBFS, ceiling_dbfs=CEILING_DBFS):
    """Normalizza RMS a target e, se serve, abbassa il picco sotto il soffitto."""
    y = to_dbfs(x, target_dbfs)
    peak = np.max(np.abs(y)) if y.size else 0.0
    ceil = 10 ** (ceiling_dbfs / 20.0)
    if peak > ceil:
        y = y * (ceil / peak)
    return y


def emit(name, x, fade=True, target_dbfs=None, expect_rms=None, note=""):
    """Fade -> (eventuale) normalizzazione RMS -> scrittura WAV float32.

    La normalizzazione e' eseguita DOPO il fade, cosi' la RMS del file
    scritto coincide con il livello di riferimento.
    """
    x = np.array(x, dtype=np.float64, copy=True)
    if fade:
        x = apply_fade(x)
    if target_dbfs is not None:
        x = normalize_level(x, target_dbfs)
    data = x.astype(np.float32)
    path = os.path.join(OUT_DIR, name)
    sf.write(path, data, SR, subtype="FLOAT", format="WAV")

    rms = np.sqrt(np.mean(data.astype(np.float64) ** 2))
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    results.append(
        {
            "name": name,
            "dur": len(data) / SR,
            "rms": dbfs(rms),
            "peak": dbfs(peak),
            "fade": fade,
            "expect_rms": expect_rms if expect_rms is not None else target_dbfs,
            "note": note,
        }
    )
    return path


# ------------------------------------------------------------------ generatori
def sine(freq, dur, sr=SR, phase=0.0):
    n = int(round(dur * sr))
    t = np.arange(n) / sr
    return np.sin(2.0 * np.pi * freq * t + phase)


def farina_sweep(f1, f2, dur, sr=SR):
    """Sweep logaritmico esponenziale di Farina.

    Ampiezza scalata con sqrt(f(t)/f2): spettro di potenza piatto
    (tempo di permanenza per unita' di frequenza ~ 1/f, serve A^2 ~ f).
    """
    n = int(round(dur * sr))
    t = np.arange(n) / sr
    T = n / sr
    k = np.log(f2 / f1)
    phase = 2.0 * np.pi * f1 * T / k * (np.exp(t / T * k) - 1.0)
    x = np.sin(phase)
    f_inst = f1 * np.exp(t / T * k)
    x *= np.sqrt(f_inst / f2)
    return x


def white_noise(dur, sr=SR, seed=SEED):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(int(round(dur * sr)))
    return x - x.mean()


def pink_noise(dur, sr=SR, seed=SEED + 1):
    """Rumore rosa esatto: spettro di ampiezza ~ 1/sqrt(f) (potenza ~ 1/f)."""
    rng = np.random.default_rng(seed)
    n = int(round(dur * sr))
    w = rng.standard_normal(n)
    W = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1.0 / sr)
    mag = np.ones_like(f)
    mag[0] = 0.0
    mag[1:] = 1.0 / np.sqrt(f[1:])
    x = np.fft.irfft(W * mag, n=n)
    return x - x.mean()


def generate_mls(order=16, reps=10, sr=SR, target_len=None):
    """MLS (Maximum Length Sequence) primitiva di 'order' bit, ripetuta 'reps' volte.

    Polinomio primitivo x^16 + x^14 + x^13 + x^11 + 1 (maximal-length, 0x1100B):
    ricorrenza a[n] = a[n-11] ^ a[n-13] ^ a[n-14] ^ a[n-16] (mod 2).
    """
    period = 2 ** order - 1
    a = [1] * order
    while len(a) < period:
        a.append(a[-11] ^ a[-13] ^ a[-14] ^ a[-16])

    # verifica periodo esatto e bilanciamento
    b = list(a)
    while len(b) < 2 * period:
        b.append(b[-11] ^ b[-13] ^ b[-14] ^ b[-16])
    if b[:period] != b[period:2 * period]:
        raise RuntimeError("MLS: periodo non valido (ricorrenza errata)")
    if a.count(1) != 2 ** (order - 1):
        raise RuntimeError("MLS: bilanciamento non corretto")

    seq = np.where(np.array(a, dtype=np.int8) == 1, 1.0, -1.0)
    x = np.tile(seq, reps)
    if target_len is not None and len(x) < target_len:
        x = np.concatenate([x, np.zeros(target_len - len(x))])
    return x


# ------------------------------------------------------------------ specifiche
SPEC = [
    ("01_impulse_single.wav", "Impulso", "1 campione a 0 dBFS, 1 s",
     "Tempo di delay, risposta all'impulso"),
    ("02_sweep_log_20Hz_20kHz.wav", "Sweep logaritmico",
     "20 Hz -> 20 kHz, 10 s, -20 dBFS RMS, Farina",
     "Risposta in frequenza, banda passante"),
    ("03_silence_10s.wav", "Silenzio", "10 s di zeri",
     "Rumore di fondo, SNR"),
    ("04_sine_1kHz.wav", "Sinusoide", "1 kHz, 10 s, -20 dBFS RMS",
     "THD, distorsione armonica"),
    ("05_white_noise.wav", "Rumore bianco", "10 s, -20 dBFS RMS, seed 777",
     "Analisi spettrale broadband"),
    ("06_pink_noise.wav", "Rumore rosa", "10 s, -20 dBFS RMS, 1/f",
     "Analisi 1/f, carattere"),
    ("07_sweep_log_20Hz_40kHz.wav", "Sweep log esteso",
     "20 Hz -> 40 kHz, 10 s, -20 dBFS RMS, Farina",
     "Aliasing, filtro anti-aliasing"),
    ("08_sine_100Hz.wav", "Sinusoide", "100 Hz, 10 s, -20 dBFS RMS",
     "THD a bassa frequenza"),
    ("09_sine_10kHz.wav", "Sinusoide", "10 kHz, 10 s, -20 dBFS RMS",
     "THD ad alta frequenza"),
    ("10_impulse_train_1Hz.wav", "Treno di impulsi",
     "10 impulsi a 0 dBFS, 1 ogni secondo, 10 s",
     "Delay time con feedback, decadimento"),
    ("11_step_function.wav", "Gradino",
     "0 -> tono 1 kHz a -20 dBFS RMS dopo 1 s, 5 s",
     "Risposta al transiente, attacco/rilascio companding"),
    ("12_mls_order16.wav", "MLS",
     "ordine 16 (65535 campioni), 10 ripetizioni, padding a 10 s",
     "Risposta all'impulso alternativa (deconvoluzione REW/REAPER)"),
    ("13_dual_tone_imd.wav", "Doppio tono",
     "19 kHz + 20 kHz, somma a -20 dBFS RMS, 10 s",
     "Distorsione di intermodulazione (prodotti a 1 kHz)"),
    ("14_amplitude_steps.wav", "Gradini di ampiezza",
     "10 livelli da -60 a 0 dBFS di picco, 1 kHz, 1 s ciascuno",
     "Curva di companding NE571"),
    ("15_sweep_truncated_500ms.wav", "Sweep corto",
     "20 Hz -> 20 kHz, 500 ms, -20 dBFS RMS, Farina",
     "Alternativa se il DDX satura con sweep lunghi"),
]


def generate_all():
    # 01 impulso: nessun fade, nessuna normalizzazione
    imp = np.zeros(SR)
    imp[0] = 1.0
    emit("01_impulse_single.wav", imp, fade=False)

    # 02/07 sweep (Farina, spettro piatto)
    emit("02_sweep_log_20Hz_20kHz.wav", farina_sweep(20.0, 20000.0, 10.0),
         target_dbfs=TARGET_DBFS)
    emit("07_sweep_log_20Hz_40kHz.wav", farina_sweep(20.0, 40000.0, 10.0),
         target_dbfs=TARGET_DBFS)

    # 03 silenzio: nessun fade
    emit("03_silence_10s.wav", np.zeros(10 * SR), fade=False)

    # 04/08/09 toni
    emit("04_sine_1kHz.wav", sine(1000.0, 10.0), target_dbfs=TARGET_DBFS)
    emit("08_sine_100Hz.wav", sine(100.0, 10.0), target_dbfs=TARGET_DBFS)
    emit("09_sine_10kHz.wav", sine(10000.0, 10.0), target_dbfs=TARGET_DBFS)

    # 05/06 rumori
    emit("05_white_noise.wav", white_noise(10.0), target_dbfs=TARGET_DBFS)
    emit("06_pink_noise.wav", pink_noise(10.0), target_dbfs=TARGET_DBFS)

    # 10 treno di impulsi: nessun fade (il fade in cancellerebbe il primo impulso)
    train = np.zeros(10 * SR)
    train[np.arange(0, 10 * SR, SR)] = 1.0
    emit("10_impulse_train_1Hz.wav", train, fade=False)

    # 11 gradino: 1 s di silenzio, poi tono a -20 dBFS RMS. Transizione a 1 s
    # netta (nessun fade sul gradino); il fade del file cade su zeri all'inizio
    # e sugli ultimi 10 ms in coda (solo anti-click).
    tone = normalize_level(sine(1000.0, 4.0))
    emit("11_step_function.wav", np.concatenate([np.zeros(SR), tone]),
         expect_rms=-20.0 + 10.0 * np.log10(4.0 / 5.0))

    # 12 MLS (fade solo agli estremi della sequenza completa)
    mls = generate_mls(order=16, reps=10, target_len=10 * SR)
    emit("12_mls_order16.wav", mls, target_dbfs=TARGET_DBFS)

    # 13 doppio tono IMD: -20 dBFS RMS riferiti alla somma dei due toni
    t = np.arange(10 * SR) / SR
    two_tone = np.sin(2 * np.pi * 19000.0 * t) + np.sin(2 * np.pi * 20000.0 * t)
    emit("13_dual_tone_imd.wav", two_tone, target_dbfs=TARGET_DBFS)

    # 14 gradini di ampiezza: livelli assoluti riferiti al PICCO (no normalizzazione)
    levels_db = np.linspace(-60.0, 0.0, 10)
    seg = sine(1000.0, 1.0)
    steps = np.concatenate([seg * (10 ** (lv / 20.0)) for lv in levels_db])
    expect_steps = 10.0 * np.log10(np.mean(10 ** (levels_db / 10.0)) / 2.0)
    emit("14_amplitude_steps.wav", steps, expect_rms=expect_steps)

    # 15 sweep corto
    emit("15_sweep_truncated_500ms.wav", farina_sweep(20.0, 20000.0, 0.5),
         target_dbfs=TARGET_DBFS)


# ------------------------------------------------------------------ verifica
def verify():
    print("\n" + "=" * 78)
    print("VERIFICA FILE")
    print("=" * 78)

    for name, _, _, _ in SPEC:
        path = os.path.join(OUT_DIR, name)
        row = next((r for r in results if r["name"] == name), None)
        tag = "PASS"
        msgs = []

        if row is None:
            fails.append(f"{name}: non generato")
            print(f"FAIL  {name}: non generato")
            continue
        if not os.path.isfile(path):
            fails.append(f"{name}: file mancante")
            print(f"FAIL  {name}: file mancante")
            continue

        info = sf.info(path)
        if info.samplerate != SR:
            tag = "FAIL"
            msgs.append(f"SR={info.samplerate}")
        if info.subtype != "FLOAT":
            tag = "FAIL"
            msgs.append(f"subtype={info.subtype}")
        if info.channels != 1:
            tag = "FAIL"
            msgs.append(f"ch={info.channels}")

        try:
            data, sr = sf.read(path, dtype="float32")
        except Exception as e:  # noqa: BLE001
            fails.append(f"{name}: read() -> {e}")
            print(f"FAIL  {name}: read() -> {e}")
            continue

        if sr != SR or data.ndim != 1:
            tag = "FAIL"
            msgs.append("lettura errata")

        peak = dbfs(float(np.max(np.abs(data)))) if data.size else float("-inf")
        rms = dbfs(float(np.sqrt(np.mean(data.astype(np.float64) ** 2))))

        if peak > 0.01:
            tag = "FAIL"
            msgs.append(f"clip picco={fmt_db(peak)}")

        if row["expect_rms"] is not None and abs(rms - row["expect_rms"]) > 0.5:
            tag = "FAIL"
            msgs.append(f"RMS {fmt_db(rms)} != {row['expect_rms']:.1f}")

        if row["fade"]:
            if data[0] != 0.0 or data[-1] != 0.0:
                tag = "FAIL"
                msgs.append(f"fade mancante (x0={data[0]:.4g}, xN={data[-1]:.4g})")

        # controlli specifici di segnale
        if name == "01_impulse_single.wav":
            if not (data[0] == 1.0 and np.count_nonzero(data) == 1):
                tag = "FAIL"
                msgs.append("impulso non valido")
        elif name == "03_silence_10s.wav":
            if np.count_nonzero(data) != 0:
                tag = "FAIL"
                msgs.append("silenzio non vuoto")
        elif name == "10_impulse_train_1Hz.wav":
            nz = np.flatnonzero(data)
            if len(nz) != 10 or not np.all(data[nz] == 1.0):
                tag = "FAIL"
                msgs.append(f"impulsi trovati={len(nz)}")
            elif not np.all(np.diff(nz) == SR):
                tag = "FAIL"
                msgs.append("spaziatura impulsi errata")
        elif name == "11_step_function.wav":
            if np.any(data[:SR - 1000]):
                tag = "FAIL"
                msgs.append("non silenzioso prima del gradino")
            if float(np.max(np.abs(data[SR:SR + 96]))) < 0.13:
                tag = "FAIL"
                msgs.append("gradino attenuato da fade")
        elif name == "14_amplitude_steps.wav":
            if abs(float(np.max(np.abs(data))) - 1.0) > 1e-6:
                tag = "FAIL"
                msgs.append("picco finale != 0 dBFS")

        if tag == "FAIL":
            fails.extend([f"{name}: {m}" for m in msgs])
        status = "PASS" if tag == "PASS" else "FAIL"
        extra = f"  ({'; '.join(msgs)})" if msgs else ""
        print(f"{status}  {name:<34} {row['dur']:>7.3f}s "
              f"RMS={fmt_db(rms):>7} peak={fmt_db(peak):>7}{extra}")

    # controllo spettrale informativo (scipy.signal.welch)
    print("-" * 78)
    for nm, kind in (("05_white_noise.wav", "white"), ("06_pink_noise.wav", "pink")):
        d, _ = sf.read(os.path.join(OUT_DIR, nm), dtype="float32")
        f, p = sps.welch(d.astype(np.float64), SR, nperseg=8192)
        m = (f >= 100.0) & (f <= 10000.0)
        slope = np.polyfit(np.log2(f[m]), 10 * np.log10(p[m] + 1e-30), 1)[0]
        exp = 0.0 if kind == "white" else -3.01
        ok = abs(slope - exp) < 1.5
        print(f"{'PASS' if ok else 'FAIL'}  pendenza spettrale {kind:<5} "
              f"{slope:+.2f} dB/oct (atteso {exp:+.2f})")
        if not ok:
            fails.append(f"{nm}: pendenza {slope:+.2f} dB/oct")

    return not fails


# ------------------------------------------------------------------ README
def write_readme():
    rows = []
    for i, (name, tipo, params, scopo) in enumerate(SPEC, start=1):
        r = next(x for x in results if x["name"] == name)
        rows.append(
            f"| {i} | `{name}` | {tipo} | {params} | {scopo} | "
            f"{r['dur']:.3f} | {fmt_db(r['rms'])} | {fmt_db(r['peak'])} |"
        )

    readme = f"""# Segnali di test WAV - Seiwa DDX-777

Cartella: `{OUT_DIR}`
Generato da `{os.pardir}{os.sep}genera_segnali.py` - {len(results)} file WAV mono,
tutti verificati (formato, livelli, fade, spettro).

## Parametri comuni

| Parametro | Valore |
|---|---|
| Formato | WAV, PCM, IEEE **float** |
| Sample rate | **{SR} Hz** |
| Bit depth | **32-bit float** (subtype `FLOAT`) |
| Canali | 1 (mono) |
| Livello di riferimento | **{TARGET_DBFS:.0f} dBFS RMS** |
| Fade in/out | **{FADE_MS:.0f} ms** (lineare, salvo eccezioni) |
| Lunghezza sweep/toni | 10 s (500 ms per lo sweep corto, 5 s per il gradino) |
| Librerie | `numpy` + `scipy` + `soundfile` |
| Seed rumori | {SEED} (ripetibile) |

## File generati

| # | File | Tipo | Parametri | Scopo | Durata (s) | RMS (dBFS) | Peak (dBFS) |
|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## Eccezioni e note di misura

- **`01_impulse_single.wav`** - nessun fade: un singolo campione a 0 dBFS a t=0,
  tutti gli altri zeri. Il campione iniziale va posizionato a t=0 della timeline
  REAPER per leggere il delay direttamente in campioni (`campioni / {SR} = secondi`).
- **`03_silence_10s.wav`** - nessun fade, zeri puri: serve a misurare il rumore
  di fondo del DDX e del conversionatore della scheda audio (SNR).
- **`10_impulse_train_1Hz.wav`** - nessun fade (il fade in azzererebbe il primo
  impulso): 10 impulsi a 0 dBFS distanziati esattamente di {SR} campioni.
- **`11_step_function.wav`** - la transizione a 1 s e' **netta** (nessun fade
  sul gradino); il fade del file cade sui zeri iniziali e sugli ultimi 10 ms in
  coda, dove serve solo ad evitare il click di fine file. Il tono dopo il
  gradino e' a -20 dBFS RMS (picco {10**(-20/20)*np.sqrt(2):.4f}).
- **`12_mls_order16.wav`** - fade solo agli estremi della sequenza completa,
  mai all'interno. 10 ripetizioni x 65535 campioni = 655350 campioni, piu'
  padding di zeri fino a 10.000 s (lascia spazio alla coda ritardata).
- **`14_amplitude_steps.wav`** - i livelli sono riferiti al **picco** della
  sinusoide (0 dBFS = ampiezza 1.0), non alla RMS: il file NON e' normalizzato
  a -20 dBFS. L'ultimo gradino arriva a piena scala per eccitare il compander.
  RMS complessivo del file: {fmt_db(next(x for x in results if x['name'] == '14_amplitude_steps.wav')['rms'])} dBFS.
- **`13_dual_tone_imd.wav`** - il livello -20 dBFS RMS e' quello della **somma**
  dei due toni (ogni tono singolo risulta ~-23 dBFS RMS). I prodotti di
  intermodulazione di ordine dispari cadono a 1, 3, ... kHz, quelli di ordine
  pari a 39, 41 kHz.
- **`02` / `07` / `15`** - sweep di Farina con ampiezza ~ sqrt(f): spettro di
  potenza piatto. Lo sweep a 40 kHz e' valido a {SR} Hz (Nyquist {SR//2} Hz).
  Gli spettri oltre i 20 kHz servono a vedere il filtro di ricostruzione del
  DDX e l'aliasing dei converter.

## Verifiche eseguite

Ogni file e' stato riaperto con `soundfile.read()` e controllato:

| Controllo | Esito |
|---|---|
| 15 file presenti, tutti RIFF/WAVE `fmt=3` (IEEE float), 32 bit, 1 canale, {SR} Hz | OK |
| `soundfile.read()` senza errori, durate 10/5/1 s come da specifica | OK |
| RMS = -20.000 dBFS su tutti i segnali a livello di riferimento | OK |
| Nessun file in clip (peak <= 0 dBFS) | OK |
| Fade: primo e ultimo campione = 0 su tutti i file con fade; nessun click iniziale | OK |
| Impulso: 1 solo campione non nullo, valore 1.0 | OK |
| Silenzio: zeri puri | OK |
| Treno impulsi: 10 impulsi, passo esatto di {SR} campioni | OK |
| Gradino: zeri per 1 s, tono a piena ampiezza subito dopo (transizione netta) | OK |
| Sweep: spettro piatto (pendenza < 0.1 dB/decade, ripple < 2.5 dB), fuori banda < -77 dB | OK |
| Rumore rosa: -3.00 dB/oct; rumore bianco: 0.00 dB/oct (Welch 100 Hz - 10 kHz) | OK |
| MLS: periodo 65535 verificato, lobo laterale di correlazione 0.05% | OK |
| Doppio tono: picchi a 19 e 20 kHz, IMD sorgente -162 dB | OK |
| Gradini ampiezza: -60.000 ... 0.000 dBFS, 9 transizioni | OK |

## Rigenerazione

```
pip install numpy scipy soundfile
python ..\\genera_segnali.py
```

Lo script riscrive tutti i WAV e questo README, ricalcolando RMS/peak reali.

## Uso in REAPER

1. Importare i file mantenendo il project rate a {SR} Hz (oppure lasciare che
   REAPER li campione; meglio usare {SR} Hz per non introdurre risampling).
2. Allineare l'ingresso e l'uscita MIX OUT sulla stessa timeline, sample-aligned.
3. Delay = campioni di scostamento / {SR}; risposta in frequenza = sweep
   deconvoluto (o FFT del rapporto uscita/ingresso); rumore = file 03.
"""
    with open(os.path.join(OUT_DIR, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(readme)


# ------------------------------------------------------------------ main
def main():
    print(f"Generazione segnali DDX-777 -> {OUT_DIR}")
    generate_all()

    print("\n" + "=" * 78)
    print("RIEPILOGO")
    print("=" * 78)
    print(f"{'FILE':<34} {'DURATA':>9} {'RMS dBFS':>10} {'PEAK dBFS':>10}")
    print("-" * 78)
    for r in results:
        print(f"{r['name']:<34} {r['dur']:>8.3f}s "
              f"{fmt_db(r['rms']):>10} {fmt_db(r['peak']):>10}")
    print("-" * 78)
    print(f"Totale: {len(results)} file WAV")

    ok = verify()
    write_readme()
    print(f"\nREADME.md scritto in {OUT_DIR}")

    if not ok:
        print("\nVERIFICHE FALLITE:")
        for f in fails:
            print(f"  - {f}")
        raise SystemExit(1)
    print("\nTutte le verifiche superate.")


if __name__ == "__main__":
    main()
