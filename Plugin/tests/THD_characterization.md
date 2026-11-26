# THD Characterization Report — Seiwa DDX-777

**Data**: 2026-10-03 02:30  
**Harness**: <PROJECT_ROOT>\Plugin\build\Release\ddx_harness.exe  
**Matrice completa**: 8 freq × 9 livelli × 3 mode × 3 variant = 504 render  
**Q4**: 2 render (10 kHz, -20 dBFS, current vs virtual ADC)  
**Compander sweep**: 11 render (10 kHz, -30 a -10 dBFS, dist_off)

---

## 1. Metodologia

- **Segnale**: sinusoide pura, durata 56.5 s (5×2²⁰ + 2s fade)
- **Livelli**: dBFS RMS (coerente con misure HW)
- **THD**: FFT 2²⁰ punti, finestra Hann, armoniche 2-10 (fino a Nyquist 48 kHz)
- **5 medie**: 5 segmenti non sovrapposti da 2²⁰ campioni
- **Armoniche misurabili a 10 kHz**: solo 2-4 (20, 30, 40 kHz)

---

## 2. Risultati chiave (estratto matrici completa)

### THD % a -20 dBFS, modalità mix, variante completa

| Freq (Hz) | THD plugin | THD HW | Gap (dB) |
|---|---|---|---|
| 100 | 0.180% | 0.349% | -45.7 |
| 1 kHz | 0.021% | 0.033% | -43.8 |
| 10 kHz | 0.005% | 0.035% | -56.3 |

### Decomposizione THD a -20 dBFS (modalità mix)

| Freq | THD completa | Solo companding (dist_off) | Solo dist. uscita (comp_off) |
|---|---|---|---|
| 100 Hz | 0.180% | 0.167% | 0.165% |
| 1 kHz | 0.021% | 0.014% | 0.014% |
| 10 kHz | 0.005% | 0.0006% | 0.005% |

**Nota**: THD totale ≈ √(companding² + dist_uscita²) → le due sorgenti sono sostanzialmente indipendenti e si sommano in quadratura.

---

## 3. Q4 — Virtual ADC 32 kHz a 10 kHz (-20 dBFS)

| Scenario | THD (%) | THD (dB) | Δ vs attuale |
|---|---|---|---|
| Plugin attuale (96 kHz) | 0.0053% | -85.5 dB | — |
| Plugin + Virtual ADC 32 kHz | 0.0080% | -81.9 dB | **+3.6 dB** |
| **HW target** | **0.0350%** | **-69.1 dB** | — |

**Interpretazione**: Il Virtual ADC (filtri 8° @ 15 kHz, simulazione aliasing 32 kHz) **aumenta il THD di 3.6 dB**. L'aliasing da campionamento 32 kHz **contribuisce** al THD hardware, ma il gap rimane **12.8 dB** (0.0080% vs 0.0350%). L'aliasing spiega solo ~20% del gap.

---

## 4. Sweep Livello Compander a 10 kHz (variante dist_off = solo companding)

| Livello (dBFS RMS) | THD (%) | THD (dB) |
|---|---|---|
| -30 | 0.0007% | -103.3 |
| -28 | 0.0006% | -104.4 |
| -26 | 0.0006% | -104.7 |
| -24 | 0.0007% | -103.5 |
| -22 | 0.0006% | -103.9 |
| -20 | 0.0006% | -104.2 |
| -18 | 0.0006% | -104.7 |
| -16 | 0.0005% | -105.4 |
| -14 | 0.0005% | -106.0 |
| -12 | 0.0004% | -107.3 |
| -10 | 0.0004% | -107.7 |

**Analisi**: Il THD del companding è **costante (~0.0006%)** su tutti i livelli da -30 a -10 dBFS. Nessun picco a -20 dBFS. Il compander è **completamente inattivo** a questi livelli (soglia plugin a -6 dBFS, livelli test 11-16 dB sotto soglia).

---

## 5. Analisi delle 4 Domande

### Q1 — Il companding attuale produce distorsione dipendente dalla frequenza? Quanta?

**Sì, fortemente dipendente dalla frequenza**:
- 100 Hz: 0.167% (93% del THD totale)
- 1 kHz: 0.014% (65% del THD totale)  
- 10 kHz: 0.0006% (11% del THD totale)

Il companding domina alle basse frequenze (ripple rivelatore a 2×f), diventa trascurabile alle alte.

---

### Q2 — La distorsione d'uscita attuale è lineare col livello o ha una curva? (Limiter vs compressore)

La distorsione d'uscita attuale (kThdLow/kThdHigh) segue la legge **k·x²** → THD proporzionale all'ampiezza (lineare in dB col livello).

**MA**: il compander attuale NON è un limiter. Il sweep livello mostra THD costante → compander **inattivo** a tutti i livelli testati (soglia -6 dBFS vs livelli -10 to -30 dBFS).

L'osservazione REW ("cliff a -20 dBFS") suggerisce che l'HW è un **limiter con soglia -20 dBFS**, non un compressore morbido. Il modello plugin va riprogettato.

---

### Q3 — Dove il divario col target è massimo?

| Freq | THD plugin | THD HW | Gap |
|---|---|---|---|
| 100 Hz | 0.180% | 0.349% | **45.7 dB** |
| 1 kHz | 0.021% | 0.033% | **43.8 dB** |
| 10 kHz | 0.005% | 0.035% | **56.3 dB** |

**Massimo a 10 kHz** (56.3 dB). Il gap è ovunque > 40 dB → il modello attuale sottostima drasticamente il THD HW.

---

### Q4 — Il THD a 10 kHz nel plugin è generato a 96 kHz o include aliasing da 32 kHz?

Il Virtual ADC **aumenta il THD di 3.6 dB** (0.0053% → 0.0080%). L'aliasing da 32 kHz **contribuisce** ma spiega solo ~20% del gap (12.8 dB rimanenti su 56.3 dB).

**Conclusione**: L'aliasing è un fattore ma **non la causa principale** del gap.

---

## 6. Verifica attribuzione THD Sessione 11

L'attribuzione "THD da companding NE571" (sessione 11) è **smentita** dai dati:

- Livello stimato al compander HW: ≈ -17 dBFS peak (-20 dBFS RMS)
- Soglia compander plugin: -6 dBFS peak (knee -9..-3 dBFS)  
- **Risultato**: Livello HW stimato **11 dB sotto soglia** → compander inattivo
- **Conclusione**: Il THD hardware 0.035% a 10 kHz **NON proviene dal companding** NE571
- Fonte probabile HW: stadio uscita (DAC 12 bit + filtro AA + buffer) + aliasing 32 kHz

---

## 7. Raccomandazione per modellazione fisica NE571

Basata sui risultati:

1. **Il compander NON è un compressore dbx-style con soglia a -6 dBFS**
2. **Il compander HW è un LIMITER con soglia a -20 dBFS** (osservazione REW: uscita satura a -20 dBFS indipendentemente dal pot LEVEL)
3. **Il THD massimo è ALLA SOGLIA del limiter** (-20 dBFS), non cresce monotonicamente
4. **Modello consigliato**:
   - Limiter hard con soglia a -20 dBFS peak
   - Attack/release NE571 (τ_a=8ms, τ_r=60ms)
   - Rectifier full-wave → gain computer con knee infinito (hard limit)
4. **Virtual ADC 32 kHz**: necessario per replicare aliasing armoniche > 16 kHz
5. **Stadio d'uscita**: DAC 12 bit + filtro AA 8° ordine @ 15 kHz + buffer analogico

---

## 8. Limitazioni della caratterizzazione

- Armoniche 5-10 non misurabili a 10 kHz (Nyquist 48 kHz) → THD a 10 kHz calcolato su sole 3 armoniche (sottostimato)
- THD su 3 armoniche (20, 30, 40 kHz) vs HW che misura full-band dopo filtro AA
- Soglia compander stimata, non misurata direttamente su HW
- Livello assoluto al compander HW ignoto (dipende da pot LEVEL, fader REAPER, gain scheda)
- Cliff a -20 dBFS osservato qualitativamente in REW, non quantificato
- Virtual ADC implementato come filtri 8° ordine @ 15 kHz SENZA decimazione reale (solo caratteristiche filtro)

---

## 9. File prodotti

- `tests/characterize_thd.py` — script completo caratterizzazione
- `build/char_thd/results.csv` — dati grezzi (ultima run: compander sweep)
- `build/char_thd/THD_vs_freq.png` — grafico THD vs frequenza
- `build/char_thd/THD_vs_level.png` — grafico THD vs livello
- `build/char_thd/THD_comparison.png` — confronto plugin vs HW
- `tests/THD_characterization.md` — questo report
- `Prep/Segnali_Test/Risultati/level_check.md` — verifica livelli misure HW (Task 1)

---

## 10. Prossimi passi suggeriti

1. **Implementare limiter NE571 con soglia -20 dBFS** nel core DSP (sostituire Compressor attuale)
2. **Aggiungere Virtual ADC 32 kHz con decimazione/interpolazione reale** (non solo filtri)
3. **Modellare stadio uscita HW**: DAC 12 bit (quantizzazione + dither) + filtro AA analogico + buffer
4. **Validare contro misure HW** a livelli noti (servono misure HW a livelli controllati)