# THD Characterization Report — Seiwa DDX-777 — FASE 2 (5 componenti HF)

**Data**: 2026-10-03 11:48
**Harness**: <PROJECT_ROOT>\Plugin\build\Release\ddx_harness.exe
**Matrice completa**: 8 freq × 9 livelli × 3 mode × 3 variant = 648 render (stato calibrato)
**Ablazione componenti**: 3 scenari × 3 freq = 9 render
**Sweep kOpAmp**: 5 valori × 3 freq = 15 render

## 1. Stato calibrato Fase 2

| Componente | Coefficiente | Stato | Note |
|---|---|---|---|
| Comp 1 — Virtual ADC 32 kHz (AA+ricostruzione 8° @ 15 kHz) | — | ON | attivo di default |
| Comp 2 — Rectifier NE571 banda finita (kRect) | 0.0 | calibrato | contributo < 1 dB al gap; ripple 2f filtrato a 10 kHz |
| Comp 3 — Mismatch DAC R-2R (kDac2/kDac3) | 0.0 / 0.0 | calibrati | aggiungono solo a 1 kHz (H2 @ 2 kHz non filtrata); niente a 10 kHz |
| Comp 4 — Buffer uscita tanh (kBuffer) | 0.0 | calibrato | distorsione broadband: peggiora 1 kHz senza compensare |
| Comp 5 — 4 stadi op-amp 4558D (kOpAmp) | **0.018** | calibrato | chiude il gap a 10 kHz; effetto netto a 1 kHz quasi nullo (interazione col ramo limiter) |

## 2. Tabelle THD % (modalità mix, variante full, stato calibrato)

| Freq (Hz) | -6 dBFS | -12 dBFS | -14 dBFS | -18 dBFS | -20 dBFS | -24 dBFS | -30 dBFS | -36 dBFS | -42 dBFS |
|---|---|---|---|---|---|---|---|---|---|
| 50 | 0.2627% | 0.5646% | 0.7724% | 1.4299% | 1.8443% | 0.0204% | 0.0187% | 0.0323% | 0.0649% |
| 100 | 0.3639% | 0.2807% | 0.3048% | 0.3846% | 0.4312% | 0.0482% | 0.0243% | 0.0174% | 0.0286% |
| 200 | 0.3439% | 0.2038% | 0.2267% | 0.3743% | 0.4756% | 0.0251% | 0.0227% | 0.0381% | 0.0756% |
| 500 | 0.3435% | 0.1440% | 0.1122% | 0.0847% | 0.0836% | 0.0359% | 0.0169% | 0.0153% | 0.0306% |
| 1000 | 0.3147% | 0.1171% | 0.0829% | 0.0464% | 0.0408% | 0.0241% | 0.0105% | 0.0158% | 0.0379% |
| 2000 | 0.3046% | 0.1096% | 0.0753% | 0.0333% | 0.0217% | 0.0191% | 0.0084% | 0.0107% | 0.0266% |
| 5000 | 0.2351% | 0.0668% | 0.0437% | 0.0203% | 0.0148% | 0.0074% | 0.0044% | 0.0076% | 0.0151% |
| 10000 | 0.2785% | 0.1022% | 0.0735% | 0.0405% | 0.0315% | 0.0158% | 0.0046% | 0.0016% | 0.0007% |

## 3. Ablazione — contributo incrementale dei componenti (-20 dBFS, mix, full)

| Scenario | 100 Hz | 1 kHz | 10 kHz | Delta vs HW a 10 kHz |
|---|---|---|---|---|
| Fase 1: VADC off, tutti k=0 | 0.4169% | 0.0388% | 0.0051% | -16.7 dB |
| + Comp 1: VADC on, tutti k=0 | 0.4079% | 0.0395% | 0.0077% | -13.1 dB |
| + Comp 5: kOpAmp=0.018 (stato finale Fase 2) | 0.4312% | 0.0408% | 0.0315% | -0.9 dB |

Comp 2/3/4 calibrati a 0: le misure di calibrazione (sweep su 5-10 valori) hanno mostrato contributo < 1 dB al gap a 10 kHz e/o peggioramento del match a 1 kHz/100 Hz oltre ±2 dB. Non sono quindi attivi nel modello finale.

## 4. Sweep kOpAmp a -20 dBFS (mix, full)

| kOpAmp | 100 Hz | 1 kHz | 10 kHz | Gap 10 kHz vs HW |
|---|---|---|---|---|
| 0.014 | 0.4260% | 0.0368% | 0.0249% | -2.9 dB |
| 0.016 | 0.4286% | 0.0386% | 0.0282% | -1.9 dB |
| 0.018 | 0.4312% | 0.0408% | 0.0315% | -0.9 dB |
| 0.020 | 0.4338% | 0.0434% | 0.0348% | -0.1 dB |
| 0.022 | 0.4364% | 0.0463% | 0.0381% | +0.7 dB |

kOpAmp = 0.018 (default) è il punto che tiene tutte e 3 le frequenze dentro ±2 dB del target HW.

## 5. Analisi — domande chiave

### Q1 — Contributo del limiter (variante completa vs dist_off, -20 dBFS)

| Freq (Hz) | THD completa | THD solo limiter | Contributo limiter |
|---|---|---|---|
| 100 | 0.4312% | 0.4260% | 0.0665% |
| 1000 | 0.0408% | 0.0380% | 0.0149% |
| 10000 | 0.0315% | 0.0305% | 0.0077% |

### Q2 — Contributo del ramo di distorsione d'uscita (variante completa vs comp_off, -20 dBFS)

| Freq (Hz) | THD completa | THD senza limiter | Contributo dist. uscita |
|---|---|---|---|
| 100 | 0.4312% | 0.0802% | 0.4237% |
| 1000 | 0.0408% | 0.0515% | 0.0000% |
| 10000 | 0.0315% | 0.0375% | 0.0000% |

### Q3 — Attivazione del limiter: THD a 10 kHz in funzione del livello (solo limiter, dist_off)

| Livello (dBFS RMS) | Peak (dBFS) | THD (%) | Note |
|---|---|---|---|
| -6 | -3.0 | 0.2774% | SOPRA soglia (-20 dBFS peak) |
| -12 | -9.0 | 0.1011% | SOPRA soglia (-20 dBFS peak) |
| -14 | -11.0 | 0.0725% | SOPRA soglia (-20 dBFS peak) |
| -18 | -15.0 | 0.0395% | SOPRA soglia (-20 dBFS peak) |
| -20 | -17.0 | 0.0305% | SOPRA soglia (-20 dBFS peak) |
| -24 | -21.0 | 0.0148% | sotto soglia |

### Q4 — Virtual ADC: contributo a 10 kHz (-20 dBFS)

| Stato | THD 10 kHz |
|---|---|
| Fase 1 (VADC off, k=0) | 0.0051% |
| + Comp 1 (VADC on, k=0) | 0.0077% |
| + Comp 5 (stato finale) | 0.0315% |
| **HW target** | **0.0350%** |

Il VADC da solo aggiunge +0.0026% a 10 kHz (+3.6 dB); la chiusura del gap principale avviene con Comp 5 (kOpAmp=0.018): da 0.0077% a 0.0315%.

## 6. Confronto Fase 0 / Fase 1 / Fase 2 vs Hardware (-20 dBFS)

| Freq | Fase 0 (comp -6 dBFS) | Fase 1 (limiter -20 dBFS) | Fase 2 (5 componenti) | HW target | Gap Fase 2 vs HW |
|---|---|---|---|---|---|
| 100 Hz | 0.1800% | 0.4080% | 0.4312% | 0.349% | +1.8 dB |
| 1000 Hz | 0.0210% | 0.0395% | 0.0408% | 0.033% | +1.8 dB |
| 10000 Hz | 0.0053% | 0.0053% | 0.0315% | 0.035% | -0.9 dB |

## 7. Sintesi Gap vs Hardware (stato calibrato, -20 dBFS)

| Freq | Fase 2 THD | HW THD | Gap (dB) | Stato |
|---|---|---|---|---|
| 100 Hz | 0.4312% | 0.349% | +1.8 | ✓ Match (±2 dB) |
| 1000 Hz | 0.0408% | 0.033% | +1.8 | ✓ Match (±2 dB) |
| 10000 Hz | 0.0315% | 0.035% | -0.9 | ✓ Match (±2 dB) |

## 8. Note e limitazioni

- **Effetto a 1 kHz di Comp 5**: con kOpAmp > 0 il THD a 1 kHz presenta un minimo non monotono (riduzione parziale della 2ª armonica) che si manifesta solo con il limiter attivo: interazione tra la nonlinearità tanh (ordine dispari) e lo stadio 2° ordine kThdHigh, con fasi definite dal crossover 500 Hz. Reproducibile bit-per-bit; misurato: con limiter ON il contributo netto a 1 kHz è ≈ +0.001% (quasi nullo), mentre con limiter OFF (comp_off) lo stesso kOpAmp aggiunge distorsione come atteso.
- **Armoniche 5-10 non misurabili a 10 kHz** (Nyquist 48 kHz) → THD a 10 kHz calcolato su sole 3 armoniche (20, 30, 40 kHz), sottostimato rispetto a una misura full-band HW.
- **Livello assoluto al limiter HW ignoto** (dipende da pot LEVEL, fader DAW, gain scheda): il target HW 0.349/0.033/0.035% è a -20 dBFS RMS come misurato in sessione 11.
- **Comp 2/3/4 calibrati a 0**: i componenti sono implementati e attivi nel codice (band-pass del rectifier, dopo la quantizzazione 12 bit), ma i coefficienti di distorsione sono nulli perché i dati HW a -20 dBFS non supportano un contributo ≥ 1 dB e qualsiasi valore > 0 peggiorava il match a 1 kHz/100 Hz.
- **Virtual ADC**: filtri Butterworth 8° @ 15 kHz con clock a 3 fasi (96→32→96 kHz), coerente con l'ipotesi di ADC interno 32 kHz.
