# Segnali di test WAV - Seiwa DDX-777

Cartella: `E:\tutto\OpenCode\Seiwa DDX-777\Segnali_Test`
Generato da `..\genera_segnali.py` - 15 file WAV mono,
tutti verificati (formato, livelli, fade, spettro).

## Parametri comuni

| Parametro | Valore |
|---|---|
| Formato | WAV, PCM, IEEE **float** |
| Sample rate | **96000 Hz** |
| Bit depth | **32-bit float** (subtype `FLOAT`) |
| Canali | 1 (mono) |
| Livello di riferimento | **-20 dBFS RMS** |
| Fade in/out | **10 ms** (lineare, salvo eccezioni) |
| Lunghezza sweep/toni | 10 s (500 ms per lo sweep corto, 5 s per il gradino) |
| Librerie | `numpy` + `scipy` + `soundfile` |
| Seed rumori | 777 (ripetibile) |

## File generati

| # | File | Tipo | Parametri | Scopo | Durata (s) | RMS (dBFS) | Peak (dBFS) |
|---|---|---|---|---|---|---|---|
| 1 | `01_impulse_single.wav` | Impulso | 1 campione a 0 dBFS, 1 s | Tempo di delay, risposta all'impulso | 1.000 | -49.82 | 0.00 |
| 2 | `02_sweep_log_20Hz_20kHz.wav` | Sweep logaritmico | 20 Hz -> 20 kHz, 10 s, -20 dBFS RMS, Farina | Risposta in frequenza, banda passante | 10.000 | -20.00 | -8.60 |
| 3 | `03_silence_10s.wav` | Silenzio | 10 s di zeri | Rumore di fondo, SNR | 10.000 | -inf | -inf |
| 4 | `04_sine_1kHz.wav` | Sinusoide | 1 kHz, 10 s, -20 dBFS RMS | THD, distorsione armonica | 10.000 | -20.00 | -16.98 |
| 5 | `05_white_noise.wav` | Rumore bianco | 10 s, -20 dBFS RMS, seed 777 | Analisi spettrale broadband | 10.000 | -20.00 | -5.57 |
| 6 | `06_pink_noise.wav` | Rumore rosa | 10 s, -20 dBFS RMS, 1/f | Analisi 1/f, carattere | 10.000 | -20.00 | -6.83 |
| 7 | `07_sweep_log_20Hz_40kHz.wav` | Sweep log esteso | 20 Hz -> 40 kHz, 10 s, -20 dBFS RMS, Farina | Aliasing, filtro anti-aliasing | 10.000 | -20.00 | -8.19 |
| 8 | `08_sine_100Hz.wav` | Sinusoide | 100 Hz, 10 s, -20 dBFS RMS | THD a bassa frequenza | 10.000 | -20.00 | -16.98 |
| 9 | `09_sine_10kHz.wav` | Sinusoide | 10 kHz, 10 s, -20 dBFS RMS | THD ad alta frequenza | 10.000 | -20.00 | -16.98 |
| 10 | `10_impulse_train_1Hz.wav` | Treno di impulsi | 10 impulsi a 0 dBFS, 1 ogni secondo, 10 s | Delay time con feedback, decadimento | 10.000 | -49.82 | 0.00 |
| 11 | `11_step_function.wav` | Gradino | 0 -> tono 1 kHz a -20 dBFS RMS dopo 1 s, 5 s | Risposta al transiente, attacco/rilascio companding | 5.000 | -20.98 | -16.99 |
| 12 | `12_mls_order16.wav` | MLS | ordine 16 (65535 campioni), 10 ripetizioni, padding a 10 s | Risposta all'impulso alternativa (deconvoluzione REW/REAPER) | 10.000 | -20.00 | -18.34 |
| 13 | `13_dual_tone_imd.wav` | Doppio tono | 19 kHz + 20 kHz, somma a -20 dBFS RMS, 10 s | Distorsione di intermodulazione (prodotti a 1 kHz) | 10.000 | -20.00 | -14.31 |
| 14 | `14_amplitude_steps.wav` | Gradini di ampiezza | 10 livelli da -60 a 0 dBFS di picco, 1 kHz, 1 s ciascuno | Curva di companding NE571 | 10.000 | -11.98 | 0.00 |
| 15 | `15_sweep_truncated_500ms.wav` | Sweep corto | 20 Hz -> 20 kHz, 500 ms, -20 dBFS RMS, Farina | Alternativa se il DDX satura con sweep lunghi | 0.500 | -20.00 | -8.82 |

## Eccezioni e note di misura

- **`01_impulse_single.wav`** - nessun fade: un singolo campione a 0 dBFS a t=0,
  tutti gli altri zeri. Il campione iniziale va posizionato a t=0 della timeline
  REAPER per leggere il delay direttamente in campioni (`campioni / 96000 = secondi`).
- **`03_silence_10s.wav`** - nessun fade, zeri puri: serve a misurare il rumore
  di fondo del DDX e del conversionatore della scheda audio (SNR).
- **`10_impulse_train_1Hz.wav`** - nessun fade (il fade in azzererebbe il primo
  impulso): 10 impulsi a 0 dBFS distanziati esattamente di 96000 campioni.
- **`11_step_function.wav`** - la transizione a 1 s e' **netta** (nessun fade
  sul gradino); il fade del file cade sui zeri iniziali e sugli ultimi 10 ms in
  coda, dove serve solo ad evitare il click di fine file. Il tono dopo il
  gradino e' a -20 dBFS RMS (picco 0.1414).
- **`12_mls_order16.wav`** - fade solo agli estremi della sequenza completa,
  mai all'interno. 10 ripetizioni x 65535 campioni = 655350 campioni, piu'
  padding di zeri fino a 10.000 s (lascia spazio alla coda ritardata).
- **`14_amplitude_steps.wav`** - i livelli sono riferiti al **picco** della
  sinusoide (0 dBFS = ampiezza 1.0), non alla RMS: il file NON e' normalizzato
  a -20 dBFS. L'ultimo gradino arriva a piena scala per eccitare il compander.
  RMS complessivo del file: -11.98 dBFS.
- **`13_dual_tone_imd.wav`** - il livello -20 dBFS RMS e' quello della **somma**
  dei due toni (ogni tono singolo risulta ~-23 dBFS RMS). I prodotti di
  intermodulazione di ordine dispari cadono a 1, 3, ... kHz, quelli di ordine
  pari a 39, 41 kHz.
- **`02` / `07` / `15`** - sweep di Farina con ampiezza ~ sqrt(f): spettro di
  potenza piatto. Lo sweep a 40 kHz e' valido a 96000 Hz (Nyquist 48000 Hz).
  Gli spettri oltre i 20 kHz servono a vedere il filtro di ricostruzione del
  DDX e l'aliasing dei converter.

## Verifiche eseguite

Ogni file e' stato riaperto con `soundfile.read()` e controllato:

| Controllo | Esito |
|---|---|
| 15 file presenti, tutti RIFF/WAVE `fmt=3` (IEEE float), 32 bit, 1 canale, 96000 Hz | OK |
| `soundfile.read()` senza errori, durate 10/5/1 s come da specifica | OK |
| RMS = -20.000 dBFS su tutti i segnali a livello di riferimento | OK |
| Nessun file in clip (peak <= 0 dBFS) | OK |
| Fade: primo e ultimo campione = 0 su tutti i file con fade; nessun click iniziale | OK |
| Impulso: 1 solo campione non nullo, valore 1.0 | OK |
| Silenzio: zeri puri | OK |
| Treno impulsi: 10 impulsi, passo esatto di 96000 campioni | OK |
| Gradino: zeri per 1 s, tono a piena ampiezza subito dopo (transizione netta) | OK |
| Sweep: spettro piatto (pendenza < 0.1 dB/decade, ripple < 2.5 dB), fuori banda < -77 dB | OK |
| Rumore rosa: -3.00 dB/oct; rumore bianco: 0.00 dB/oct (Welch 100 Hz - 10 kHz) | OK |
| MLS: periodo 65535 verificato, lobo laterale di correlazione 0.05% | OK |
| Doppio tono: picchi a 19 e 20 kHz, IMD sorgente -162 dB | OK |
| Gradini ampiezza: -60.000 ... 0.000 dBFS, 9 transizioni | OK |

## Rigenerazione

```
pip install numpy scipy soundfile
python ..\genera_segnali.py
```

Lo script riscrive tutti i WAV e questo README, ricalcolando RMS/peak reali.

## Uso in REAPER

1. Importare i file mantenendo il project rate a 96000 Hz (oppure lasciare che
   REAPER li campione; meglio usare 96000 Hz per non introdurre risampling).
2. Allineare l'ingresso e l'uscita MIX OUT sulla stessa timeline, sample-aligned.
3. Delay = campioni di scostamento / 96000; risposta in frequenza = sweep
   deconvoluto (o FFT del rapporto uscita/ingresso); rumore = file 03.
