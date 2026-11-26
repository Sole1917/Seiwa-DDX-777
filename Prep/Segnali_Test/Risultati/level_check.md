# level_check.md — Verifica livello misure hardware (Sessione 11)

**Data analisi**: 03/10/2026  
**Obiettivo**: Verificare se le misure THD hardware (T4/T8/T9) sono state fatte a un livello comparabile a -20 dBFS RMS (livello di riferimento dei WAV in Segnali_Test).

---

## Tabella livelli

| File orig | File rec | RMS orig (dBFS) | RMS rec (dBFS) | Diff catena (dB) | Peak rec (dBFS) | Clip? | Note |
|---|---|---|---|---|---|---|---|
| 04_sine_1kHz.wav | T4 (seg 1 kHz, 17-28s) | -20.0 | -19.7 | **+0.3** | -15.9 | NO | Misura valida, target HW plausibile |
| 08_sine_100Hz.wav | T4 (seg 100 Hz, 1-12s) | -20.0 | -17.7 | **+2.3** | -13.9 | NO | Misura valida, target HW plausibile |
| 09_sine_10kHz.wav | T4 (seg 10 kHz, 33-44s) | -20.0 | -22.7 | **-2.7** | -17.1 | NO | Gap reale ~13.8 dB (se lineare), ma companding non lineare → valore da rivalutare dopo Task 2 |
| 02_sweep_20Hz_20kHz.wav | T2 .wav | -20.0 | -23.6 | **-3.6** | -11.2 | NO | Misura valida (±5 dB), sweep Farina profilo sqrt(f) |

---

## Interpretazione

### Livello effettivo al compander durante le misure HW

| Parametro | Valore stimato | Nota |
|---|---|---|
| Fader REAPER (output) | ~0 dB (unity) | Diff ~0 dB per 1 kHz |
| Pot LEVEL DDX-777 | **Sconosciuto** | Determina il livello al NE571 |
| Gain scheda audio | **Sconosciuto** | Aggiunge guadagno variabile |
| **Livello al compander (stima)** | **≈ -17 dBFS peak / -20 dBFS RMS** | Se LEVEL al max e REAPER unity |

### Soglia del compander NE571 (plugin attuale)
- Soglia: **-6 dBFS** (peak) con knee 6 dB → transizione -9 a -3 dBFS peak
- Livello stimato HW: **-17 dBFS peak** → **11 dB sotto la soglia**
- Il compander sarebbe **completamente inattivo** (gain = 1.0, nessun THD da companding)

### Implicazione critica
L'attribuzione della sessione 11 *"THD ricondotta al companding NE571"* **potrebbe essere errata** se il livello reale al compander era -17 dBFS peak. Il THD hardware 0.035% a 10 kHz potrebbe provenire da:
- Distorsione stadio d'uscita (DAC + filtro AA + buffer)
- Rumore di quantizzazione 12 bit (aliasato)
- Aliasing del campionamento a 32 kHz
- **NON** dal rectifier NE571 (che era sotto soglia)

---

## Scoperta nuova (utente, da REW)

> Durante le misure originali, l'utente ha osservato che il livello in uscita del DDX-777 **satura a -20 dBFS indipendentemente dalla posizione del pot LEVEL** (oltre una certa soglia, l'uscita resta bloccata a -20 dBFS).

**Ipotesi**: il NE571 hardware è configurato come **LIMITER con soglia fissa a -20 dBFS**, non come compressore morbido.

### Conseguenze per la caratterizzazione
1. Il compander non è un compressore dbx-style con knee morbido
2. È un **hard limiter** con soglia a -20 dBFS
3. Il THD ha un **PICCO intorno a -20 dBFS** (punto di clipping del limiter), non cresce monotonicamente
4. Il target hardware 0.035% a 10 kHz è il THD **alla soglia del limiter**

---

## Azioni per Task 2

1. **Aggiungere test "sweep di livello a 10 kHz"**: -30 a -10 dBFS, passo 2 dB, misura THD comp-only
2. **Verificare forma curva THD vs livello**: picco a -20 dBFS → limiter; crescita monotona → compressore
3. **Aggiornare Q2 del report**: da "companding lineare?" a "limiter o compressore?"
4. **Se limiter confermato**: il modello `Compressor` va modificato per avere soglia a -20 dBFS (non -6 dBFS) e comportamento limiter