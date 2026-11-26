# DDX-777 — VST3 Plugin

Emulazione del Seiwa Digital Delay DDX-777 (1985), delay digitale a 12 bit con clock modulabile (VCO + LFO), compandor NE571, saturazione d'ingresso JFET/M5221/NE571, feedback a reostato.

## Stato Corrente

**verify.py --force: 22 PASS / 3 FAIL / 7 INFO**

- PASS: delay timing, noise RMS, aliasing, THD, transfer curve, loop gain FB
- FAIL: noise peak (+5.2 dB), band ripple (7.89 dB), H_loop 15-20 kHz (+10.1 dB)
- INFO: spectral A/B, band -3dB point, RMS eco1/10, energia 0-20k/20-48k, G_forward

I 3 FAIL sono pre-esistenti (sessione 13c/13d) e non bloccano il rilascio.

## Requisiti Build

- **JUCE 8** (incluso come submodulo in `build/_deps/juce-src/`)
- **CMake 3.20+**
- **MSVC 2022** (Visual Studio 17.x)
- Windows 10/11 x64

## Comandi Build

```powershell
cd Plugin
cmake -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
```

Output VST3: `build/SeiwaDDX777_artefacts/Release/VST3/DDX-777.vst3/`

## Comandi Test

```powershell
cd Plugin
python tests/verify.py --force
```

## Controlli Principali

| Controllo | Target | Note |
|-----------|--------|------|
| Delay timing (T1) | 64–512 ms × factor | ±1 ms vs HW |
| Noise floor (T2) | −77.3 dBFS RMS | Peak +5 dB noto |
| Freq response (T3) | ±1.5 dB 100–14 kHz | Ripple 7.9 dB noto |
| Aliasing (T4) | ≤ −29 dB in-band | OK |
| THD (T4) | ≤ 6 dB vs HW | OK |
| Transfer curve (T6) | corr ≥ 0.9 | 1.000 OK |
| Loop gain FB (T8) | FB100=0.90, FB50=0.34, FB25=0.10 | OK |

## Parametri Principali

- **INPUT_LEVEL** (0–10): 0=−60 dB … 6=0 dB (unity) … 10=+12 dB
- **FEEDBACK** (0–1): livello feedback + bias DC compandor
- **DELAY_LEVEL** (0–1): wet gain nel MIX OUT
- **RANGE** (10 pos): 1, 2, 4, 8, 16, 32, 64, 128, 256, 512 ms
- **FACTOR** (0.5–2.0): ×0.5 / ×1 / ×2 continuo
- **MOD_SPEED** (0–10): frequenza LFO 0.05–8 Hz
- **MOD_DEPTH** (0–10): indice modulazione clock ±8%
- **HOLD** (on/off): freeze scrittura (crossfade 5 ms su write enable)
- **MIX** (0–1): dry/wet balance MIX OUT
- **OUTPUT_TRIM** (−20–0 dB): trim post-mix
- **BYPASS** (on/off): hard bypass
- **PEAK_LED** soglia: parametro `PEAK_LEVEL` (fuori segnale)

## Note

- Progetto **privato, non commerciale** — solo ricerca/educazione
- Autore: Sole
- Basato su reverse engineering da schemi, datasheet (NE571, M5221, 2SK118, 4558D) e misure HW (sessioni 11–13)

## File di Progetto

- `HANDOFF_PLUGIN.md` — specifica completa architettura
- `PLUGIN_STATE.md` — stato lavori per sessione
- `CHANGELOG.md` — storico modifiche
- `LOOP_CALIBRATION.md` — calibrazione feedback reostato
- `FEEDBACK_ANALYSIS_v2.md` — analisi dettagliata feedback
- `03_blocchi.md` — documentazione catena segnale