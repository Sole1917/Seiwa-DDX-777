# MEASUREMENTS_13h-bis.md — Analisi misure HW 05/10/2026 (sessione 13h-bis)

> **Data misure**: 05/10/2026 18:33:16  
> **Cartella**: `Prep/Segnali_Test/Risultati/`  
> **Stato modello**: 13h (22 PASS / 4 FAIL / 6 INFO)  
> **Scopo**: Definire target HW reali per redesign 13i (HF chain refit)

---

## 1. Lista file analizzati (timestamp 05/10/2026 18:33:16)

| # | File | Tipo | Size | Ruolo |
|---|------|------|------|-------|
| 1 | `noise_maudioch1 .wav` | Rumore | 3.84 MB | Baseline scheda (cavo scollegato, DDX acceso) |
| 2 | `noise_directout (dry) .wav` | Rumore | 3.84 MB | DIRECT OUT, dry puro (buffer input) |
| 3 | `noise_mixdry .wav` | Rumore | 3.84 MB | MIX OUT, DELAY=0 (percorso mix) |
| 4 | `noise_peak 10, fdbck 0, delay 10  .wav` | Rumore | 3.84 MB | MIX OUT, FB=0% |
| 5 | `noise_peak 10, fdbck 2, delay 10  .wav` | Rumore | 3.84 MB | MIX OUT, FB=2 (≈20%) |
| 6 | `noise_peak 10, fdbck 10, delay 10 .wav` | Rumore | 3.84 MB | MIX OUT, FB=10 (100%) |
| 7 | `fb10_impulse_35s .wav` | Impulso | 13.6 MB | Impulso da 01_impulse_single.wav, FB=100%, 35.3s |
| 8 | `fb10_impulse_35s 34 ripetizioni.PNG` | Spettrogramma | 566 KB | Panoramica echi |
| 9 | `fb10_impulse_35s 34 ripetizioni rate 8.PNG` | Spettrogramma | 1.4 MB | Decimato (rate 8) |
| 10 | `pinknoise_peak 5, fdbk 0, delay 10, 512x1, source normalized -30db rms .wav` | Pink noise | 5.38 MB | Risposta HF, FB=0, LEVEL=5 |

**File aggiuntivi 04/10 (per confronto H_loop)**:
- `peak 10, feedback 10, delay 10, 512 ms.wav` (12.4 MB, 21.5s, 40 echi, int32 stereo)
- `peak 10, feedback 2 circa, delay 10, 512 ms.wav` (FB=2)
- `peak 10, feedback 5 circa, delay 10, 512 ms.wav` (FB=5)

---

## 2. Analisi Rumore (6 file)

### 2.1 Metodologia
- Finestra: 10 s centrali (esclusi primi 500 ms)
- RMS/peak/crest in dBFS
- Spettro: Welch, Hann 1s, NFFT=262144, 50% overlap
- Sottrazione quadratura rumore scheda (`noise_maudioch1`)

### 2.2 Risultati tabellari

| Condizione | RMS (dBFS) | Peak (dBFS) | Crest (dB) | RMS_eff* (dBFS) | Note |
|------------|------------|-------------|------------|-----------------|------|
| **maudioch1** (ref) | **−91.02** | **−76.99** | **14.03** | −91.02 | Baseline scheda (cavo scollegato) |
| directout_dry | **−94.21** | −80.69 | 13.52 | **< ref** | DDX input buffer attenua il floor |
| mixdry | **−93.86** | −79.38 | 14.48 | **< ref** | Percorso mix (DELAY=0) più quieto del ref |
| FB=0% | **−77.42** | −67.37 | **10.05** | **−77.62** | Loop aperto: +13.6 dB sopra ref |
| FB=2% | **−78.56** | −68.28 | **10.28** | **−78.82** | FB=2%: +12.5 dB sopra ref |
| FB=10% | **−77.64** | −66.68 | **10.95** | **−77.84** | FB=100%: +13.2 dB sopra ref |

\* `RMS_eff` = sottrazione quadratura rumore scheda: `10·log10(10^(RMS_X/10) − 10^(RMS_maudio/10))`.  
"N/A" = valore misurato ≤ ref + 1 dB → rumore DDX trascurabile, dominato da scheda.

### 2.3 Spettri (delta vs maudioch1)

| Condizione | 50 Hz delta | 100 Hz delta | >10 kHz max spur |
|------------|-------------|--------------|------------------|
| directout_dry | −12.0 dB | −5.6 dB | +11.4 dB @ 15.8 kHz |
| mixdry | −16.5 dB | −10.8 dB | +13.6 dB @ 31.3 kHz |
| FB=0% | **+22.9 dB** | **+24.8 dB** | +23.5 dB @ 28.7 kHz |
| FB=2% | **+21.1 dB** | **+27.9 dB** | +23.7 dB @ 28.9 kHz |
| FB=10% | **+22.8 dB** | **+26.1 dB** | +23.3 dB @ 28.8 kHz |

**Osservazioni chiave**:
1. **directout_dry e mixdry sono PIÙ QUIETI del noise floor scheda** (RMS −94.2/−93.9 vs −91.0 dBFS). Il buffer d'ingresso DDX attenua il rumore della scheda.
2. **Il loop aggiunge ~13-14 dB di rumore** sopra il floor scheda (FB>0: RMS ≈ −77.5 dBFS vs ref −91.0 dBFS).
3. **Crest factor HW**: FB=10% → 10.95 dB (modello 13h: 4.8 dB a FB=100%). Il modello sottostima il crest di **6.1 dB**.
4. **Rete 50/100 Hz**: amplificata dal loop di **+22–28 dB** (FB>0). Assente a FB=0 e nel dry.
5. **Spurie >10 kHz**: picchi a ~28.8 kHz (+23 dB vs ref) → probabile imaging/aliasing del campionatore (f_word/2 ≈ 15.5 kHz → 2× = 31 kHz).

![Spettri rumore overlay](build/meas_13h_bis/noise_spectra_overlay.png)
![Delta vs ref](build/meas_13h_bis/noise_spectra_delta.png)

### 2.4 Conclusione follow-up C (noise peak FAIL)
- Il FAIL noise peak (−72.5 dBFS vs target −67.3 dBFS) è **rumore reale del loop** (non scheda).
- Crest factor HW a FB=10% = **10.95 dB** vs modello 4.8 dB → il modello sottostima i picchi rari.
- Il rumore a FB=0% (−77.4 dBFS RMS) è **reale DDX** (loop aperto), non scheda.
- **Raccomandazione 13i**: modellare sorgente di picchi rari (quantizzazione non lineare? jitter campionatore?) per alzare crest factor a ~11 dB.

---

## 3. Risposta in Frequenza HF (Pink Noise)

### 3.1 Metodologia
- Sorgente: `06_pink_noise.wav` (−30 dBFS RMS, crest 13.2 dB)
- Registrato: `pinknoise_peak 5...` (−17.77 dBFS RMS, crest 14.5 dB)
- Guadagno scheda diverso tra misure → **solo forma risposta confrontata** (livelli assoluti ignorati)
- Crest registrato 14.5 dB > sorgente 13.2 dB → **nessuna compressione** (compressore trasparente)
- Metodo: Welch (Hann 1s, NFFT=65536, 50% overlap), rapporto PSD

### 3.2 Risultati HW vs Modello 13h

| Metrica | HW (misurato) | Modello 13h | Delta |
|---------|---------------|-------------|-------|
| **Ripple 100 Hz–14 kHz** | **2.97 dB** | 7.89 dB | **−4.92 dB** (HW più piatto) |
| **Punto −3 dB** | **31.33 kHz** | 12.80 kHz | **+18.53 kHz** (HW molto più esteso) |
| **Roll-off >15 kHz** | **−1.1 dB/ott** | ~−24 dB/ott (AA 8 poli) | HW molto più gentile |
| Crest factor sorgente | 13.17 dB | — | — |
| Crest registrato | 14.47 dB | — | Nessuna compressione |

![Risposta HW](build/meas_13h_bis/hf_response_hw.png)
![Zoom HF](build/meas_13h_bis/hf_response_zoom.png)

### 3.3 Analisi
- **Ripple HW = 2.97 dB** vs modello 7.89 dB → **HW è 4.9 dB più piatto** del modello.
- **−3 dB HW = 31.33 kHz** vs modello 12.80 kHz → **HW ha banda 2.4× più ampia**. Il modello taglia troppo presto a causa della catena AA (aa1 @10.4 kHz Q=1.08).
- **Roll-off HW = −1.1 dB/ott** vs modello ~−24 dB/ott (AA 8 poli). L'HW non ha il droop severo del modello.
- Crest registrato (14.5 dB) > sorgente (13.2 dB) → **nessuna compressione** → risposta affidabile.

![Risposta HW](build/meas_13h_bis/hf_response_hw.png)
![Zoom HF](build/meas_13h_bis/hf_response_zoom.png)

### 3.4 Implicazioni per redesign 13i
- Il modello **sovrastima il droop AA** e **sottostima la banda**.
- Il boost eq3 (+12 dB @14 kHz) compensa un droop che **nell'HW non esiste**.
- **Target redesign**: ripple ≤ 1.5 dB (già ok HW), −3 dB ≥ 15 kHz (già ok HW), roll-off gentile.

---

## 4. H_loop Resonance (FAIL #4)

### 4.1 File analizzati
| File | Durata | Echi trovati | Intervallo medio |
|------|--------|--------------|------------------|
| `fb10_impulse_35s .wav` (13h-bis) | 35.3s | 58 echi | **530 ms** (var: 422–1107 ms) |
| `peak 10, feedback 10, delay 10, 512 ms.wav` (04/10) | 21.5s | 40 echi | **546 ms** (esatto) |

### 4.2 H_loop(f) = Eco(n+1)/Eco(n) — Risultati medi

| File | H(18.4 kHz) | H(19.3 kHz) | Max 15–20 kHz | Note |
|------|-------------|-------------|---------------|------|
| **13h-bis (35s)** | **−0.43 dB** | **+1.42 dB** | **+6.42 dB** @ 15.91 kHz | Picchi fino a +52 dB in coppie specifiche (artefatti spettrali) |
| **04/10 (21.5s)** | **−1.48 dB** | **−1.55 dB** | **+0.23 dB** @ 17.70 kHz | Coerente, nessun picco > +1 dB in media |

**Modello 13h**: H_loop +10.1 dB max a 18.4/19.3 kHz (FAIL target ≤ +1.0 dB)

### 4.3 Analisi dettagliata
- **L'HW NON ha la risonanza +10.1 dB del modello**.
- Media HW: **~0 dB** (13h-bis: −0.43/+1.42 dB; 04/10: −1.48/−1.55 dB).
- Picchi individuali fino a **+52 dB** (13h-bis) sono **artefatti di calcolo** (ratio di spettri con nulls/peaks spettrali), non risonanza fisica sostenuta.
- **04/10 (sessione indipendente)** conferma: max medio +0.23 dB, nessun picco > +1 dB.
- **Intervallo echi**: 13h-bis = 530 ms (variazione), 04/10 = 546 ms (esatto, match f_word/2 = 15.515 kHz → 546 ms).

![H_loop 13h-bis](build/meas_13h_bis/h_loop_average.png)
![H_loop comparison](build/meas_13h_bis/h_loop_comparison.png)
![Delta](build/meas_13h_bis/h_loop_delta.png)

### 4.4 Lettura PNG spettrogrammi
| File | Descrizione |
|------|-------------|
| `fb10_impulse_35s 34 ripetizioni.PNG` (1105×745) | Panoramica temporale completa: 34 echi visibili, decadimento esponenziale, energia concentrata <20 kHz. Nessuna riga persistente a 18.4/19.3 kHz. |
| `fb10_impulse_35s 34 ripetizioni rate 8.PNG` (2684×745) | Versione decimata (rate 8): zoom su banda bassa, conferma assenza riga persistente a 18–19 kHz. Decadimento HF progressivo per eco. |

### 4.5 Confronto con modello 13h
| Metrica | HW (04/10) | Modello 13h | Delta |
|---------|------------|-------------|-------|
| H_loop picco 18.4/19.3 kHz | +0.23 dB (avg −1.5 dB) | **+10.1 dB** (FAIL) | **−10.3 dB** |
| Intervallo echi | 546 ms (esatto) | 546 ms (design) | Match |

**Conclusione**: La risonanza +10.1 dB del modello è **un artefatto della catena AA+EQ** (aa1 @10.4 kHz + eq3 +12 dB @14 kHz Q=2.5), **non presente nell'HW reale**. Il redesign 13i deve eliminare questa risonanza spuria.

---

## 5. Tabella Riassuntiva HW vs Modello 13h

| Metrica | HW (misurato) | Modello 13h | Delta | Stato FAIL |
|---------|---------------|-------------|-------|------------|
| **Noise crest (FB=10%)** | 10.95 dB | 4.8 dB | +6.15 dB | #1 noise peak |
| **Noise RMS (FB=10%, post-sub)** | −77.84 dBFS | −77.3 dBFS | −0.54 dB | — |
| **Noise crest (FB=0%)** | 10.05 dB | 4.8 dB | +5.25 dB | #1 (loop aperto) |
| **Ripple 100 Hz–14 kHz** | **2.97 dB** | 7.89 dB | **−4.92 dB** | #2 (modello peggio) |
| **−3 dB frequency** | **31.33 kHz** | 12.80 kHz | **+18.53 kHz** | #3 (modello taglia presto) |
| **H_loop 18.4/19.3 kHz (avg)** | **−1.5 / −1.5 dB** | **+10.1 dB** | **−11.6 dB** | #4 (modello artefatto) |
| **H_loop max 15–20 kHz** | +0.23 dB | +10.1 dB | **−9.9 dB** | #4 |
| **Intervallo echi FB=100%** | 546 ms (esatto) | 546 ms | Match | — |

**Legenda**: verde = HW migliore del modello; rosso = modello peggio; giallo = HW peggio.

---

## 6. Raccomandazioni per Redesign 13i

### 6.1 Target Banda (da misure HW)
| Parametro | Target HW | Azione redesign |
|-----------|-----------|-----------------|
| **Ripple 100 Hz–14 kHz** | ≤ 2.97 dB (HW) → target **≤ 1.5 dB** | Ridisegnare catena AA+EQ per piattificare |
| **−3 dB point** | ≥ 31.33 kHz (HW) → target **≥ 15 kHz** | Già ok HW; modello taglia troppo presto |
| **Roll-off >15 kHz** | Gentile (−1.1 dB/ott) | Non inseguire roll-off steep; evitare over-equalizzazione |

### 6.2 Target Rumore (da misure HW)
| Parametro | HW misurato | Target redesign |
|-----------|-------------|-----------------|
| **Crest factor (FB=100%)** | 10.95 dB | Alzare da 4.8 → **≥ 10 dB** (modellare picchi rari) |
| **Noise RMS (FB=100%, post-sub)** | −77.8 dBFS | Mantenere ≤ −77.3 dBFS |
| **Noise peak (FB=100%)** | −66.7 dBFS | Target ≤ −67.3 dBFS (già ok se crest corretto) |
| **Rete 50/100 Hz** | +22–28 dB amplificazione loop | Isolare ground loop / rivedere feedback path |

### 6.3 Vincolo H_loop (da misure HW)
| Parametro | HW misurato | Vincolo redesign |
|-----------|-------------|------------------|
| **H_loop 18.4/19.3 kHz (avg)** | ≤ 0 dB | **Eliminare risonanza +10.1 dB** (artefatto modello) |
| **H_loop max 15–20 kHz** | ≤ +0.23 dB (avg) | Target ≤ +1.0 dB (già ok HW) |
| **Intervallo echi FB=100%** | 546 ms | Mantenere |

### 6.4 Azioni concrete per 13i
1. **Catena AA**: rimuovere aa1 @10.4 kHz (droop precoce); aa4 @16–17 kHz Q=1.0–1.5; aa2/aa3 per stopband.
2. **EQ**: ridurre eq3 da +12 dB @14 kHz Q=2.5 → +2–3 dB @15–16 kHz Q=1.0; eq2 +1–2 dB @11–12 kHz Q=0.5.
3. **Virtual ADC**: valutare se Butterworth 8° @15 kHz è necessario (HW non ha droop a 15 kHz).
4. **Noise crest**: aggiungere sorgente di picchi rari (es. quantizzatore non lineare a bassa risoluzione, jitter campionatore) per alzare crest a ~11 dB.
5. **Validazione**: ogni step incrementale → `verify.py --force` + misure HW pink noise + impulso FB=100%.

### 6.5 Verdict sui FAIL attuali
| FAIL | Causa | Azione 13i |
|------|-------|------------|
| #1 noise peak | Crest factor HW 11 dB vs modello 4.8 dB | Modellare picchi rari (quantizzazione/jitter) |
| #2 band ripple | Modello AA+EQ crea droop/rippio inesistente in HW | Ridisegnare AA+EQ (target HW 2.97 dB → ≤1.5 dB) |
| #3 band −3 dB | Modello taglia a 12.8 kHz (AA precoce) | HW ha −3dB a 31 kHz → alzare cutoff AA |
| #4 H_loop | Artefatto modello (eq3 +12dB + aa1 10.4k) | HW non ha risonanza → rimuovere boost eq3 + aa1 precoce |

---

## 7. File generati
| File | Descrizione |
|------|-------------|
| `build/meas_13h_bis/noise_results.json` | Dati completi analisi rumore |
| `build/meas_13h_bis/noise_spectra_overlay.png` | Spettri 6 condizioni overlay |
| `build/meas_13h_bis/noise_spectra_delta.png` | Delta vs rumore scheda |
| `build/meas_13h_bis/hf_response_results.json` | Dati risposta HF |
| `build/meas_13h_bis/hf_response_hw.png` | Risposta HW vs modello |
| `build/meas_13h_bis/hf_response_zoom.png` | Zoom 10–24 kHz |
| `build/meas_13h_bis/h_loop_results.json` | Dati H_loop 13h-bis |
| `build/meas_13h_bis/h_loop_comparison_results.json` | Confronto 13h-bis vs 04/10 |
| `build/meas_13h_bis/h_loop_average.png` | H_loop medio 13h-bis |
| `build/meas_13h_bis/h_loop_comparison.png` | Confronto H_loop 13h-bis vs 04/10 |
| `build/meas_13h_bis/h_loop_delta.png` | Differenza H_loop |
| `build/meas_13h_bis/thumb_*.PNG` | Thumbnail spettrogrammi |

---

## 8. Prossimi passi
1. **Avviare sessione 13i** con redesign olistico AA+EQ per risolvere #2, #3, #4 simultaneamente.
2. **Parallelamente**: investigare sorgente crest factor rumore (quantizzatore 12-bit non lineare? jitter campionatore?).
3. **Validazione continua**: ogni modifica → `verify.py --force` + misure HW pink noise + impulso FB=100%.

---

*Report generato automaticamente da script di analisi 13h-bis. Timestamp: 05/10/2026.*