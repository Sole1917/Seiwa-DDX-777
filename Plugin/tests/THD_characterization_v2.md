# THD Characterization Report — Seiwa DDX-777 — FASE 1 (Limiter -20 dBFS)

**Data**: 2026-10-03 02:30
**Harness**: <PROJECT_ROOT>\Plugin\build\Release\ddx_harness.exe
**Matrice completa**: 8 freq × 9 livelli × 3 mode × 3 variant = 648 render
**Q4**: 2 scenari a 10 kHz (-20 dBFS)
**Sweep limiter**: 11 livelli a 10 kHz (dist_off)

## 1. Metodologia

- **Segnale**: sinusoide pura, durata 56.5 s (5×2²⁰ + 2s fade)
- **Livelli**: dBFS RMS (coerente con misure HW)
- **THD**: FFT 2²⁰ punti, finestra Hann, armoniche 2-10 (fino a Nyquist 48 kHz)
- **5 medie**: 5 segmenti non sovrapposti da 2²⁰ campioni
- **Armoniche misurabili a 10 kHz**: solo 2-4 (20, 30, 40 kHz)
- **Limiter**: soglia -20 dBFS peak, attack 8 ms, release 60 ms, hard knee

## 2. Tabelle THD % (modalità mix, variante full)

| Freq (Hz) | -6 dBFS | -12 dBFS | -14 dBFS | -18 dBFS | -20 dBFS | -24 dBFS | -30 dBFS | -36 dBFS | -42 dBFS |
|---|---|---|---|---|---|---|---|---|---|
| 50 | 0.3246% | 0.5729% | 0.7629% | 1.3775% | 1.7605% | 0.0216% | 0.0180% | 0.0315% | 0.0632% |
| 100 | 0.2626% | 0.2474% | 0.2769% | 0.3656% | 0.4169% | 0.0455% | 0.0230% | 0.0177% | 0.0294% |
| 200 | 0.2438% | 0.1944% | 0.2388% | 0.4362% | 0.5753% | 0.0224% | 0.0243% | 0.0479% | 0.0933% |
| 500 | 0.1383% | 0.0871% | 0.0802% | 0.0784% | 0.0819% | 0.0297% | 0.0161% | 0.0145% | 0.0274% |
| 1000 | 0.0492% | 0.0337% | 0.0328% | 0.0357% | 0.0388% | 0.0111% | 0.0086% | 0.0141% | 0.0293% |
| 2000 | 0.0324% | 0.0210% | 0.0198% | 0.0204% | 0.0218% | 0.0072% | 0.0061% | 0.0111% | 0.0223% |
| 5000 | 0.0261% | 0.0141% | 0.0118% | 0.0089% | 0.0081% | 0.0049% | 0.0031% | 0.0059% | 0.0114% |
| 10000 | 0.0227% | 0.0111% | 0.0088% | 0.0059% | 0.0051% | 0.0036% | 0.0018% | 0.0009% | 0.0009% |

## 3. Q4 — Virtual ADC 32 kHz a 10 kHz (-20 dBFS)

| Scenario | THD (%) | THD (dB) | Note |
|----------|---------|----------|------|
| Plugin attuale (96 kHz) | 0.0051% | -85.8 | |
| Plugin + Virtual ADC 32 kHz | 0.0077% | -82.3 | Filtri 8° @ 15 kHz |
| **HW target** | **0.0350%** | **-69.1** | Misura sessione 11 |

## 4. Sweep Livello Limiter a 10 kHz (variante dist_off = solo limiter)

| Livello (dBFS RMS) | Peak (dBFS) | THD (%) | THD (dB) | Note |
|---|---|---|---|---|
| -30 | -27.0 | 0.0007% | -103.3 | sotto soglia |
| -28 | -25.0 | 0.0006% | -104.4 | sotto soglia |
| -26 | -23.0 | 0.0006% | -104.7 | sotto soglia |
| -24 | -21.0 | 0.0006% | -104.9 | sotto soglia |
| -22 | -19.0 | 0.0007% | -103.7 | SOPRA soglia (-20 dBFS peak) |
| -20 | -17.0 | 0.0006% | -104.1 | SOPRA soglia (-20 dBFS peak) |
| -18 | -15.0 | 0.0005% | -105.4 | SOPRA soglia (-20 dBFS peak) |
| -16 | -13.0 | 0.0004% | -107.0 | SOPRA soglia (-20 dBFS peak) |
| -14 | -11.0 | 0.0004% | -108.8 | SOPRA soglia (-20 dBFS peak) |
| -12 | -9.0 | 0.0003% | -110.8 | SOPRA soglia (-20 dBFS peak) |
| -10 | -7.0 | 0.0002% | -112.9 | SOPRA soglia (-20 dBFS peak) |

## 5. Analisi FASE 1

### Confronto Fase 0 (compander -6 dBFS) vs Fase 1 (limiter -20 dBFS)

| Freq | Fase 0 THD | Fase 1 THD | HW THD | Delta Fase1 vs HW (dB) |
|------|------------|------------|--------|------------------------|
| 100 Hz | 0.1800% (-44.9 dB) | 0.4169% (-47.6 dB) | 0.349% (-49.1 dB) | +1.5 dB |
| 1000 Hz | 0.0210% (-67.8 dB) | 0.0388% (-68.2 dB) | 0.033% (-69.6 dB) | +1.4 dB |
| 10000 Hz | 0.0053% (-85.5 dB) | 0.0051% (-85.8 dB) | 0.035% (-69.1 dB) | -16.7 dB |

### Q1 — Con il limiter a -20 dBFS, il THD a 100 Hz sale o scende? Di quanto?

Confronto **variante completa** vs **dist_off** (solo limiter):

| Freq (Hz) | THD completa | THD solo limiter | Contributo limiter |
|---|---|---|---|
| 100 | 0.4169% | 0.4118% | 0.0651% |
| 1000 | 0.0388% | 0.0357% | 0.0150% |
| 10000 | 0.0051% | 0.0006% | 0.0051% |

### Q2 — Con il limiter a -20 dBFS, il THD a 10 kHz sale o scende? Il gap di 16.4 dB si riduce?

Confronto **variante completa** vs **comp_off** (solo distorsione uscita):

| Freq (Hz) | THD completa | THD solo dist. uscita | Contributo dist. uscita |
|---|---|---|---|
| 100 | 0.4169% | 0.0720% | 0.4107% |
| 1000 | 0.0388% | 0.0165% | 0.0351% |
| 10000 | 0.0051% | 0.0056% | 0.0000% |

### Q3 — Il limiter hard introduce distorsione di clipping ai livelli sopra soglia? A quali livelli si attiva?

Sweep livello a 10 kHz (solo limiter, variante dist_off):

| Livello (dBFS RMS) | Peak (dBFS) | THD (%) | THD (dB) | Note |
|---|---|---|---|---|
| -30 | -27.0 | 0.0007% | -103.3 | sotto soglia |
| -28 | -25.0 | 0.0006% | -104.4 | sotto soglia |
| -26 | -23.0 | 0.0006% | -104.7 | sotto soglia |
| -24 | -21.0 | 0.0006% | -104.9 | sotto soglia |
| -22 | -19.0 | 0.0007% | -103.7 | SOPRA soglia (-20 dBFS peak) |
| -20 | -17.0 | 0.0006% | -104.1 | SOPRA soglia (-20 dBFS peak) |
| -18 | -15.0 | 0.0005% | -105.4 | SOPRA soglia (-20 dBFS peak) |
| -16 | -13.0 | 0.0004% | -107.0 | SOPRA soglia (-20 dBFS peak) |
| -14 | -11.0 | 0.0004% | -108.8 | SOPRA soglia (-20 dBFS peak) |
| -12 | -9.0 | 0.0003% | -110.8 | SOPRA soglia (-20 dBFS peak) |
| -10 | -7.0 | 0.0002% | -112.9 | SOPRA soglia (-20 dBFS peak) |

### Q4 — Il virtual ADC 32 kHz ora contribuisce di più al THD a 10 kHz?

- **Plugin attuale (96 kHz)**: 0.0051% (-85.8 dB)
- **Plugin + Virtual ADC 32 kHz**: 0.0077% (-82.3 dB)
- **Target HW**: 0.0350% (-69.1 dB)

**Interpretazione**: Il Virtual ADC **aumenta** il THD di 3.6 dB. L'aliasing contribuisce.

## 6. Sintesi Gap vs Hardware

| Freq | Fase 1 THD | HW THD | Gap (dB) | Stato |
|------|------------|--------|----------|-------|
| 100 Hz | 0.4169% | 0.349% | +1.5 | ✓ Match (±3 dB) |
| 1000 Hz | 0.0388% | 0.033% | +1.4 | ✓ Match (±3 dB) |
| 10000 Hz | 0.0051% | 0.035% | -16.7 | Plugin -16.7 dB (meno distorto) |

## 7. Limitazioni

- Armoniche 5-10 non misurabili a 10 kHz (Nyquist 48 kHz) → THD a 10 kHz calcolato su sole 3 armoniche (sottostimato)
- THD su 3 armoniche (20, 30, 40 kHz) vs HW che misura full-band dopo filtro AA
- Livello assoluto al limiter HW ignoto (dipende da pot LEVEL, fader REAPER, gain scheda)
- Virtual ADC implementato come filtri 8° ordine @ 15 kHz SENZA decimazione reale (solo caratteristiche filtro)
