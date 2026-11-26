# Seiwa DDX-777 — Emulazione plugin (Beta 1.0)

Emulazione software del **Seiwa DDX-777 Digital Delay** (1985) come plugin audio
**VST3** per Windows, basata sul modello DSP calibrato
sulle registrazioni hardware dell'unità originale.

- Stato: **Beta 1.0** (versione host 1.0.0)
- Framework: **JUCE 8.0.9** (pinned, FetchContent)
- Build: Windows x64, MSVC (VS Build Tools v18), cmake ≥ 3.22
- Autori: emulazione non ufficiale; nessun rapporto con Seiwa. 2026 Sole

---

## Contenuto del repository

```
Seiwa DDX-777/
├── README.md                  ← questo file
├── Prep/                      ← documentazione di progetto (stato, changelog, schema, lacune)
│   ├── PLUGIN_STATE.md        ← stato operativo completo (config DSP, risultati, TODO)
│   ├── PLUGIN_CHANGELOG.md    ← storico sessioni (append-only)
│   ├── SEIWA_DDX-777_HANDOFF.md ← specifica hardware + concept
│   └── ...
├── Plugin/
│   ├── CMakeLists.txt         ← progetto JUCE (plugin + harness + generatore preset)
│   ├── src/
│   │   ├── dsp/               ← modello DSP (DDX777Core.h, Params.h)
│   │   ├── PluginProcessor.*  ← wrapper JUCE (APVTS, 2 core L/R)
│   │   ├── PluginEditor.*     ← editor (replica vettoriale del pannello)
│   │   └── ui/                ← componenti (RackPanel, Knob, LedIndicator, RockerSwitch, InputJack)
│   ├── tests/
│   │   ├── verify.py          ← suite di validazione vs registrazioni HW (96 kHz)
│   │   ├── smoke/main.cpp     ← ddx_smoke: smoke test audio del plugin completo (48k/44.1k)
│   │   ├── screenshot/main.cpp← ddx_screenshot: PNG della UI (headless)
│   │   ├── harness/main.cpp   ← harness offline (render WAV + metriche)
│   │   └── presets/main.cpp   ← generatore dei 5 preset
└── Foto DSP/                  ← fotografie dell'unità originale
```

---

## Build

```bat
cmake -S Plugin -B Plugin/build
cmake --build Plugin/build --config Release
```

Artefatti (in `Plugin/build/`):

| File | Ruolo |
|---|---|
| `SeiwaDDX777_artefacts/Release/VST3/DDX-777.vst3` | plugin VST3 (5.6 MB) |
| `SeiwaDDX777_artefacts/Release/Standalone/DDX-777.exe` | applicazione standalone |
| `Release/ddx_harness.exe` | harness offline (render/WAV, senza GUI) |
| `ddx_gen_presets_artefacts/Release/ddx_gen_presets.exe` | rigenera i preset in `presets/` |
| `ddx_smoke_artefacts/Release/ddx_smoke.exe` | smoke test audio headless (11 test, 48k/44.1k) |
| `ddx_screenshot_artefacts/Release/ddx_screenshot.exe` | screenshot UI headless (PNG) |

**Deploy (obbligatorio a ogni build)**: Reaper scannerizza solo la cartella
`C:\Users\<utente>\AppData\Local\Programs\Common\VST3` — dopo ogni build copiare sempre
un copia completa del bundle lì (sostituendo l'eventuale vecchia):

```bat
copy /Y /S "Plugin\build\SeiwaDDX777_artefacts\Release\VST3\DDX-777.vst3" "C:\Users\<utente>\AppData\Local\Programs\Common\VST3\"
```

---

## Parametri (10)

| Parametro | Pannello | Range | Default |
|---|---|---|---|
| INPUT_LEVEL | INPUT LEVEL (knob PEAK) | 0…+20 dB (solo gain-up) | 0 dB |
| FEEDBACK | FEED BACK LEVEL | 0…1 | 0.5 |
| DELAY_LEVEL | DELAY LEVEL | 0…1 | 0.5 |
| RANGE | RANGE (1–512 ms) | 1,2,4,…,512 | 512 |
| FACTOR | FACTOR | 0.5…2.0 continuo | 1.0 |
| MOD_SPEED | MOD SPEED | 0…10 | 0 |
| MOD_DEPTH | MOD DEPTH | 0…10 | 0 |
| HOLD | HOLD (rocker) | on/off | off |
| MIX | (aggiunta plugin) | 0…1 | 0.95 |
| BYPASS | (utility) | on/off | off |

L'editor replica 1:1 il pannello originale (~482 mm → 1000×136 px): cornici di sezione
smussate, potenziometri con indice triangolare a punta esterna (FACTOR con anello di tacche
a cerchio pieno, come l'originale), LED PEAK/HOLD/POWER (POWER acceso quando non in
BYPASS: il rocker "POWER" pilota il BYPASS), jack d'ingresso.

## Feature introdotte nell'emulazione

1. **MIX / dry-wet**: parametro `Params::mixLevel` introdotto nel core con default 0.95 (eguagliante alla costante originale hardware).
2. **Input level**: potenziometro di ingresso implementato come gain-up only (0…+20 dB), come l'originale.
3. **Jack input**: click sulla label del jack per la gestione stereo (introdotto in fase di sviluppo UI).
4. **Bypass**: rocker "POWER" che pilota il BYPASS; LED POWER acceso quando il plugin non è in BYPASS.

---

## Validazione del modello DSP

Il core è calibrato sulle registrazioni hardware dell'unità originale
(`Prep/Segnali_Test/Risultati/`). La suite `Plugin/tests/verify.py` (17 test + 2 FAIL
documentati + 3 info) riporta lo stato:

```
=== RIEPILOGO: 17 PASS, 2 FAIL, 3 INFO ===
```

I 2 FAIL sono un limite documentato (L25, `Prep/04_lacune.md`): il Virtual ADC interno
a 32 kHz sposta il −3 dB di banda a 12.80 kHz (target 14.5–16.5 kHz) e produce ripple
7.83 dB a 14 kHz; disattivandolo la banda passa ma peggiora l'aliasing (T5).
Dettaglio completo: `Prep/PLUGIN_STATE.md`.

Gate audio del plugin completo (wrapper + processBlock, a 48 kHz e 44.1 kHz):
`Plugin/build/ddx_smoke_artefacts/Release/ddx_smoke.exe` — 11 test (audio presente,
no clipping, delay eco 528/247/960 ms, BYPASS, mono, block 64, state save/recall).
È il test che ha isolato il bug audio della Beta (biquad instabili per cutoff ≥ Nyquist
a 44.1/48 kHz, fix 13b: clamp a 0.45·fs, no-op a 88.2/96 kHz).

Eseguire la verifica dopo modifiche al core:

```bat
python Plugin\tests\verify.py --force
Plugin\build\ddx_smoke_artefacts\Release\ddx_smoke.exe
```

---

## Deviazioni dalla specifica (documentate, decise con l'utente)

1. **Tasso di campionamento interno = host rate**: nessun resampler interno a 32 kHz
   (la spec indicava "Resampling"). Il modello emula la catena 32 kHz con filtri
   dipendente da `fs` (Virtual ADC incluso).
2. **Categorie VST3 = Fx + Delay**: la categoria "Vintage" non esiste in JUCE 8.0.9.
3. **Versione host 1.0.0**: il qualificatore "beta" vive solo in questo README e
   nella descrizione prodotto.
4. **Layout sorgenti `Plugin/src/`**: la specifica indicava `Source/`; mantenuto il
   layout `src/` preesistente.
5. **Font di sistema**: Arial (etichette) e Georgia (wordmark) in approssimazione della
   serigrafia originale.
6. **JUCE 8.0.9 pinned**: ultima tag disponibile 8.0.15; upgrade possibile ma con
   attenzione alle API.

## Note

- Il comportamento audio del plugin è **bit-identico** al modello calibrato per i valori
  di default (il parametro MIX è stato aggiunto come campo `Params::mixLevel` con default
  0.95, eguagliando la costante originale).
- Le misure hardware rimanenti (unità non accessibile: livelli −24/−30/−36 dBFS, R_in,
  C_RECT, conferma pinout) sono tracciate in `Prep/04_lacune.md` e non bloccano la beta.
- Questo progetto è stato sviluppato con l'uso di diversi agenti AI gratuiti (attraverso OpenCode) per la parte di coding e analisi, in un processo di vibecoding collaborativo. Di conseguenza, il codice sorgente e le documentazioni sono il risultato di tale processo: il progetto non è di proprietà di alcun singolo individuo, ma è reso disponibile come open source per trasparenza e riproducibilità. Questo progetto è perciò rilasciato sotto i termini della **Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)**

## Lacune

Il progetto presenta alcune lacune rispetto alla specifica originale: limiti di modellazione
e restrizioni legate all'accesso ai dati hardware disponibili. La gestione dei TODO operativi e
lo stato aggiornato della documentazione sono mantenuti in `Prep/04_lacune.md` e in
`Prep/PLUGIN_STATE.md`.
