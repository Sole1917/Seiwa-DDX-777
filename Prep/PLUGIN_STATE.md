# PLUGIN_STATE.md — Stato operativo plugin Seiwa DDX-777

**Sessione corrente**: 13i (redesign HF incrementale: fallito, rollback a 13h; target −3 dB rivisto a ≥14 kHz; verify 22/3/7)  
**Data ultimo aggiornamento**: 05/10/2026  
**Versione**: 17 (GUI 1000×136 13b/13d + triangolo classico funzionante + rendering D2D 1:1 a prescindere dallo scaling del display; audio 13h; verify 96 kHz 22/3/7 — 3 FAIL documentati P1-13c/L25-12b/H_loop-13g; ddx_smoke 15/16 — T12 FB=0.75 pre-esistente da 13g (tabella P1 v2, vedi HANDOFF §10))

---

## Stato plugin (sessione 13b)

### Build (Windows, Release)
```
cmake -S Plugin -B Plugin/build
cmake --build Plugin/build --config Release
```
- Toolchain: VS Build Tools v18 (generatore **"Visual Studio 18 2026"**, in
  `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools`), cmake 4.4.3
- Artefatti: `Plugin/build/SeiwaDDX777_artefacts/Release/VST3/DDX-777.vst3` (5.6 MB),
  `...\Standalone\DDX-777.exe`, `...\DDX-777_SharedCode.lib`,
  `Plugin/build/Release/ddx_harness.exe`,
  `Plugin/build/ddx_gen_presets_artefacts/Release/ddx_gen_presets.exe`,
  `Plugin/build/ddx_smoke_artefacts/Release/ddx_smoke.exe` (smoke test audio headless),
  `Plugin/build/ddx_screenshot_artefacts/Release/ddx_screenshot.exe` (PNG UI headless)
- **Gate audio**: `ddx_smoke.exe` (11 test: RMS/no-clip a 48k e 44.1k, delay eco
  528/247/960 ms, BYPASS bit-identico, mono, block 64, state save/recall) — 11/11 PASS.
  È il test che ha isolato il bug audio Beta (IIR instabile a 44.1/48 kHz, vedi sotto).
- Metadati: COMPANY "Sole", PRODUCT "DDX-777", VERSION 1.0.0, codici SOLE/DDX7,
  VST3_CATEGORIES **Fx + Delay** (deviazione: "Vintage" non esiste in JUCE 8.0.9)
- **Deploy REAPER (obbligo, deciso dall'utente)**: a ogni build copiare il bundle
  completo in `C:\Users\ellio\AppData\Local\Programs\Common\VST3\` (unica cartella
  scansionata da Reaper), sostituendo l'eventuale copia precedente.
- **DPI (13e)**: `CMakeLists.txt` imposta `add_compile_definitions(JUCE_WIN_PER_MONITOR_DPI_AWARE=0)`
  (top-level; JUCE 8 compila i moduli come TU amalgamati nei target plugin → macro
  presente in SharedCode/VST3/Standalone). Esito: `getPlatformScaleFactor()`=1.0 →
  rendering D2D **1:1 in pixel fisici** a qualsiasi scaling del display (evita la
  GUI "zoommata+tagliata" sotto host per-monitor-DPI-aware come REAPER). Layout/
  coordinate invariati; su display già al 100% è un no-op visivo.

### Parametri (APVTS "PARAMETERS", 10)
| ID | Nome pannello | Range | Default |
|---|---|---|---|
| INPUT_LEVEL | INPUT LEVEL | 0…+20 dB (solo gain-up) | 0 dB |
| FEEDBACK | FEED BACK LEVEL | 0…1 | 0.5 |
| DELAY_LEVEL | DELAY LEVEL | 0…1 | 0.5 |
| RANGE | RANGE mS | 1,2,4,…,512 (10 scelte) | 512 |
| FACTOR | FACTOR | 0.5…2.0 continuo (×0.5/×1/×2…) | 1.0 |
| MOD_SPEED | MOD SPEED | 0…10 | 0 |
| MOD_DEPTH | MOD DEPTH | 0…10 | 0 |
| HOLD | HOLD | on/off | off |
| MIX | (nuovo, non sul pannello) | 0…1 | 0.95 |
| BYPASS | (utility) | on/off | off |

- MIX: `Params::mixLevel` (default 0.95f) → riga 190 di `DDX777Core.h`; a default il
  rendering è **bit-identico** allo stato pre-13a. Non ricomporre il mix fuori dal core
  (lo stadio di uscita opera sul segnale già mixato).
- **INPUT_LEVEL (13b)**: ora range **0…+20 dB, default 0 dB**, solo gain-up
  (`Decibels::decibelsToGain` ≥ 1.0 sul buffer in entrata; il core resta con
  `inputLevel = 1.0`). Prima era −20…+6 dB con attenuazione.
- **FACTOR (13b)**: ora parametro **continuo 0.5…2.0** (AudioParameterFloat), default 1.0.
  Core: `Params.factor` (float) + `factorClockFor(f)` in `Params.h` — interpolazione
  lineare a tratti sui 3 punti calibrati (0.5→2.13770, 1.0→1.0, 2.0→0.55), **bit-identico
  a 0.5/1/2**. Prima era AudioParameterChoice a 3 posizioni (×0.5/×1/×2).
- **State save/recall (13b)**: ora binario `copyXmlToBinary`/`getXmlFromBinary` con
  `ValueTree::createXml()` + check tag + `replaceState` (API JUCE 8: `createXml` restituisce
  `unique_ptr<XmlElement>`; `hasType` → `hasTagName`; `replaceState` a 1 argomento).
- BYPASS = passthrough + reset dei 2 core al re-engage.
- 2 core indipendenti (L/R): il second channel organico (§12 handoff) resta da implementare.

### UI (editor 1000 × 136 px, 1:1 del pannello ~482 mm; layout 13b ripristinato in 13d)
- `src/ui/RackPanel`: pannello nero (gradiente #222326→#141517, **senza texture** — la
  grana 13c è rimossa in 13d), 6 cornici smussate 45° (frame y 16..118, chamfer 8,
  gap neri ~12 px tra le cornici come foto 830/836), serigrafia cream #EDE0B0, logo
  "Seiwa®" (Georgia boldItalic 40, y28) + DIGITAL DELAY (y66) + DDX-777 (y84).
  Etichette top y21..35, bottom y99..113. L'esperimento GUI 1000×290 della 13c
  (cornici oro #E8C05A, grana, knob 128×128) è **scartato** (decisione utente 13d)
- `src/ui/Knob`: 7 potenziometri (PEAK/INPUT arancio, FEED BACK verde, DELAY giallo,
  RANGE azzurro, FACTOR verde, SPEED arancio, DEPTH giallo); box 96×96 centro y=67;
  mozzo r27, cappuccio r22.5, tacche r30..34 (1.8 px), etichette r37-38; **indice
   triangolare classico con PUNTA VERSO L'ESTERNO** (apice r21, base r11 verso il
   centro, halfWidth **20°**, crema kIndex; angolo in **gradi** per `polar()`) —
   13d: rimossa freccia spessa + shine arc della 13c; **13e: fix unità** (13d passava
   gradi/radianti a `polar(angleDeg)` → triangolo degenerato/invisibile; ora
   `aDeg = 135 + 270*value01`, halfWidth 20°, verificato su screenshot: angoli esatti
   per tutti i knob, 0 artefatti); stile Factor = anello di 12 tacche a cerchio pieno (come il pannello
  originale) con etichette ×0.5/×2; stile **Level0to20** per INPUT — 13d: etichette
  corrette **0/+20** (residuo 13a "-20/0" fixato); RANGE = scala a 8 detent
  (1,8,16,…,512 — parametro 13c, mantenuto). `numSteps()` (13b): knob 0..1 continui,
  knob 0..10 con 11 step
- `src/ui/LedIndicator`: PEAK (30 Hz, da `getPeakLed()`), HOLD (stato parametro),
  **POWER = !BYPASS** (13b: era decorativo sempre acceso); LED 8×8 a y20
  (PEAK x164, HOLD x604, POWER x972)
- `src/ui/RockerSwitch`: HOLD (parametro HOLD) + "POWER" (**13b: ora pilota il parametro
  BYPASS reale**; il parametro fittizio `POWER_SW` è eliminato); rocker y45..89
  (HOLD 30×44 x604, POWER 36×44 x972)
- `src/ui/InputJack`: jack 1/4" centro (52,67) + etichetta −20dB (serigrafia chassis,
  non il range del pot LEVEL che ora è 0…+20 dB)
- Font di sistema (deviazione: Arial bold etichette, Georgia boldItalic wordmark)
- Screenshot UI: `ddx_screenshot.exe` (13d: dimensione letta dall'editor, niente
  hard-code) → ultimo: `build/verify_out/gui_13b_revert.png` (1000×136)

### Preset (5, generati da `ddx_gen_presets`)
`Plugin/presets/`: **Init** (default), **Classic_Slap** (128 ms, FB 0.3, MIX 0.5),
**Ambient_Wash** (512 ms, FB 0.7, MIX 0.7), **Dub_Siren** (256 ms, FB 0.85, SPEED 5,
DEPTH 7, MIX 0.8), **Early_Digital** (512 ms ×2, FB 0.4, MIX 0.6).
Rigenerare: `ddx_gen_presets.exe <cartella>` (usa solo API pubbliche + createPluginFilter).

### Deviazioni dalla spec (documentate, decise dall'utente)
1. **Host rate** — nessun Resampling 32 kHz interno (spec: "Resampling")
2. **Categorie VST3** — solo Fx + Delay ("Vintage" inesistente in JUCE 8.0.9)
3. **Versione 1.0.0** — "-beta" solo in README/description
4. **Layout `src/`** — la spec indicava `Source/` (mantenuto `src/` preesistente)
5. **Font** — approssimazione di sistema
6. **JUCE 8.0.9** — pinned (ultima tag: 8.0.15; upgrade opzionale, attenzione API)

### Trappole API JUCE 8.0.9 (consunte in build)
`getRawParameterValue` → `std::atomic<float>*`; `juce::Atomic` = `get()/set()`; `Graphics`
senza `setThickness`/`removeTransform`/`resetTransform`; `Path::addLineTo`→`lineTo`;
`MouseEvent` = `x/y/position` + `getNumberOfClicks()`; `String::operator[]` +
`String::charToString` (niente `getCharacter`); `NormalisableRange` membri pubblici
`start/end/interval`; `FontOptions` + `Font::bold|Font::italic` (niente `boldItalic`/`sansSerif`);
`Colour(uint32)` esplicito; `withAlpha(float)` (int ambiguo); `ColourGradient(…, isRadial)`
7 argomenti; `setFillType(FillType)` + `fillAll()`; `ValueTree::toXmlString()/fromXml()`
(niente XML su APVTS); `juce_add_console_app` senza source positional; `getParameterID()`
solo su `AudioProcessorParameterWithID`.

---

## Configurazione C++ "baked in" (DDX777Core.h)

File: `D:\Tutto\Programmi\OpenCode\Seiwa DDX-777\Plugin\src\dsp\DDX777Core.h`  
Metodo: `applyFilters()` (linee ~300-340)

**Stabilità Nyquist (13b)**: in `applyFilters()` ogni cutoff passa per
`cut(f) = (f > fs/2) ? 0.45*fs : f`. Motivo: i biquad RBJ sono stabili solo per
`f < fs/2`; a 44.1/48 kHz i cutoff 40 kHz (opLP1-4), 28 kHz (rec4), 48 kHz (rec5) e,
a 44.1 kHz anche 24 kHz (rec2), superano Nyquist → poli fuori dal cerchio unitario →
IIR divergente a ±1e40/NaN in ~50 ms (**root cause del bug audio Beta**: plugin muto/
garbage in REAPER a 44.1/48 kHz; la calibrazione era tutta a 96 kHz, dove era stabile).
A 88.2/96 kHz il clamp non scatta → **bit-identico** alla calibrazione (verify invariato).

### Catena pre-campionatore (AA/EQ)
```cpp
eq1_.setHighShelf(fs_, 250.0 * s, 0.020, 1.200);
eq2_.setPeak     (fs_, 11730.7 * s, 0.957, 3.020);
eq3_.setPeak     (fs_, 14000.0 * s, 2.5,   12.0);
aa1_.setLowpass  (fs_, 10400.5 * s, 1.076);
aa2_.setLowpass  (fs_, 16500.0 * s, 0.539);
aa3_.setLowpass  (fs_, 14200.0 * s, 0.400);
aa4_.setLowpass  (fs_, 15000.0 * s, 3.000);
```

### Ricostruzione post-delay (5 sezioni RBJ Butterworth)
```cpp
rec_.setLowpass (fs_, 18000.0 * s, 0.707);
rec2_.setLowpass(fs_, 24000.0 * s, 0.707);
rec3_.setLowpass(fs_, 14000.0 * s, 0.707);  // smorza risonanza eq3/aa4 a 13–14 kHz
rec4_.setLowpass(fs_, 28000.0 * s, 0.707);
rec5_.setLowpass(fs_, 48000.0 * s, 0.707);  // no-op presso Nyquist
```

### Companding & rumore
```cpp
static constexpr float  kWetMix = 0.95f;
static constexpr float  kHissRms = 1.8e-4f;   // dither uniforme, RMS −77.4 dBFS
// Quantizzazione 12 bit post-companding (nessun expandore)
```

### Virtual ADC 32 kHz (Fase 2, ON di default)
```cpp
// decimazione (AA @ 15 kHz, 8°) + interpolazione (ricostruzione @ 15 kHz, 8°)
dec1..dec4 / int1..int4: Butterworth LP @ 15 kHz (q 0.5411961 / 1.3065630)
// selettiva: --char-virtual-adc / --no-virtual-adc (harness)
```

### Stadi op-amp / buffer (Fase 2)
```cpp
bufLP_.setLowpass(fs_, 15000.0 * s, 0.707);      // Comp 4 (kBuffer = 0)
opLP1..4_.setLowpass(fs_, 40000.0 * s, 0.707);  // Comp 5, 4 stadi (GBW 40 kHz)
double kBuffer_ = 0.0;   // calibrato Fase 2: 0
double kOpAmp_  = 0.018; // calibrato Fase 2: match THD 10 kHz (invariato in S12)
```

### Meccanismi Sessione 12 (datasheet NE570N) — sostituiscono kThdLow/kThdHigh
```cpp
// Meccanismo A (datasheet p.6 "VARIABLE GAIN CELL"): offset VOS -> 2ª armonica
// su dry² (livello ingresso, piano in banda), applicato post-mix.
double kVos_ = 0.0079;  // calibrato su T4: H2 1 kHz 0.0308% vs HW 0.0311% (+0,1 dB)
                        //              H2 10 kHz 0.0349% vs HW 0.0345% (+0,1 dB)
double m2_ = 0.0;       // stima E[dry²] (one-pole kM2 = 0.001): toglie il DC
// Meccanismo B (datasheet p.7): crossover distortion stadio di uscita -> H3 < 500 Hz
outLP_.setLowpass(fs_, 500.0 * s, 0.707);
double kLo_ = 0.0;      // taratura su T4 = 0: l'H3 a bassa banda è già fornito dalla
                        // dinamica del compressore (baseline H3 100 Hz 0.42% vs HW 0.32%);
                        // ogni kLo > 0 peggiora. Disponibile via --k-lo per test futuri.
```

### Iterazione empirica
- `overrideFilters(const double v[19])` + flag `--ffilter` in `tests/harness/main.cpp`
- Ordine 19 valori: `eq2f eq2q eq2g eq3f eq3q eq3g aa1f aa1q aa2f aa2q aa3f aa3q aa4f aa4q recf rec2f rec3f rec4f rec5f`
- Tool: `sweep.py` (funzioni `measure()`/`report()`) + `verify.py --force`

---

## Risultati ultimo verify.py (sessioni 12b/13a/13b — 03/10/2026, `--force`)

```
=== RIEPILOGO: 17 PASS, 2 FAIL, 3 INFO ===
```

| Test | Risultato | Dettaglio |
|---|---|---|
| Delay (5) | PASS | tutti i RANGE/FACTOR |
| Noise RMS | PASS | −79.3 dBFS (target −77.3) |
| Noise peak | PASS | −63.9 dBFS (target −67.3, dentro ±5 dB) |
| **Banda ripple** | **FAIL** | 7.83 dB > 1.5 dB (100 Hz–14 kHz) — Virtual ADC, vedi L25 |
| **Banda −3 dB** | **FAIL** | 12.80 kHz ∉ [14.5, 16.5] kHz — Virtual ADC, vedi L25 |
| Drift vs HW | PASS | 0.43 dB media ≤ 2.5 dB |
| Alias 17–30 kHz | PASS | ≤ −64.2 dBFS |
| T5 fold | PASS | −35.1 dBFS vs HW −30.8 (Virtual ADC lo migliora) |
| THD 100 Hz | PASS | 0.422% vs HW 0.349% (+1.7 dB, tolleranza 6 dB) |
| THD 1 kHz | PASS | 0.047% vs HW 0.033% (+3.1 dB) |
| THD 10 kHz | PASS | 0.045% vs HW 0.035% (+2.2 dB) |
| Curva T6 | PASS | corr 1.000 |

Ri-eseguito post-13a (refactor MIX + packaging): **invariato 17/2/3** (default
`mixLevel = 0.95` bit-identico al pre-13a).
Ri-eseguito post-13b (fix Nyquist + FACTOR continuo): **invariato 17/2/3** — il clamp
è no-op a 96 kHz e `factorClockFor` è bit-identico a 0.5/1/2 (i 5 target di delay
restano 66.2/264.2/528.1/247.1/960.0 ms).

Gate aggiuntivo 13b: `ddx_smoke.exe` **11/11 PASS** (48 kHz e 44.1 kHz) — prima del fix
7 test falliti con output ±1e40/NaN a 48 kHz.

Nota: eseguire sempre `verify.py --force` + `ddx_smoke.exe` dopo modifiche al core
(i render in `build/verify_out` sono caché e possono mascherare regressioni: i 2 FAIL
di banda sono comparsi solo al re-render, e i "vecchi" valori THD del 02/10 erano da
render pre-Sessione-12).

---

## Limitazioni architetturali note

### 1. Banda vs Virtual ADC (pre-esistente Fase 2, decisionato in S12 → L25)
Il Virtual ADC 32 kHz (ON di default da Fase 2) sposta il −3 dB da 14.79 a 12.80 kHz
(fuori da [14.5, 16.5]) e genera ripple 7.83 dB a 13.96 kHz; con `--no-virtual-adc`
la banda passa (1.12 dB, 14.79 kHz) ma l'aliasing T5 fallisce (−27.6 vs HW −30.8 dBFS,
target ≤ HW+3). I meccanismi A/B (Sessione 12) agiscono solo sul ramo mix: non coinvolti.
**Decisione utente (sessione 12b)**: documentare e proseguire; nessun cambiamento al
core Phase 2. Rimedio possibile (non eseguito): ritoccare cutoff decimazione/interpolazione
(15 → ~15.5-15.8 kHz) con re-verifica THD.

### 2. H2(100 Hz) sotto-predetto di ~15 dB (residuo spettrale HW)
Il modello predice H2(100 Hz) = 0.034% vs HW 0.18%: a bassa banda l'HW ha un
meccanismo H2 aggiuntivo non modellato (candidati: ripple del detector a 2f,
modulazione del rectifier). Non impatta il THD totale (+1.7 dB, PASS).

### 3. Calibrazione assoluta non fissata (manca R_in → L24)
kVos è tarato sul rapporto H2/A1 misurato, non sull'offset VOS in volt: serve R_in
per lo scaling analogico 0 dBm ↔ dBFS.

---

## TODO aperti

- [ ] Misure HW rimandate (unità non accessibile): −24/−30/−36 dBFS (target: report v4 §2,
      incluso il **test discriminante** H3(100 Hz) a −30 dBFS: modello predice 0.0035%,
      v3 §0.4 prediceva 0.33-0.40%)
- [ ] Conferma pinout NE570N shift+1: 3 test rapidi (L17, quando l'unità è accessibile)
- [ ] Misura R_in (L24) → calibrazione assoluta Meccanismo A
- [ ] Identificazione C_RECT (L23): foto …845 (radiale blu NE571) o misura
- [ ] Decisione L25: ritocco filtri Virtual ADC (cutoff ~15.5-15.8 kHz) o mantenere status quo
- [ ] Implementare feature "secondo canale organico" (§12 handoff)
- [x] Implementare concept UI (§13 handoff) — **chiuso in 13a** (editor 1000×115, replica pannello)
- [x] Bug audio Beta (plugin muto nel host) — **root cause e fix in 13b**: IIR instabile a
      44.1/48 kHz (cutoff ≥ Nyquist) → clamp `cut()` in `applyFilters()`; gate `ddx_smoke`
- [ ] **Task utente (13b)**: rigenerare i 5 preset (già eseguiti in 13b, da confermare/rivedere)
      e screenshot UI (`ddx_screenshot.exe` o standalone + capture)
- [ ] FEEDBACK knob: oggi senza effetto DSP (limiter threshold fisso −20 dBFS, `p_.feedback`
      non letto nel core) — lacuna di modello da decidere (modellare o etichettare)
- [ ] Test manuali utente: REAPER a 44.1 e 48 kHz (audio presente, delay 528 ms a RANGE 512),
      confronto visivo UI vs pannello (1000×136), no-crash 10 min
- [ ] Risolvere lacune non audio (L2-L4, L6-L11, L14-L16, L18-L22)

---

## Blocchi attuali

- **Banda vs Virtual ADC (L25)**: documentato, decisionato (status quo)
- H2(100 Hz) residuo spettrale: documentato, candidato kRect/ripple detector
- Calibrazione assoluta: bloccata da R_in (L24)
- Lacune foto/misure non audio: L2-L4, L6-L11, L14-L16, L18-L22

---

## File correlati

| File | Ruolo |
|---|---|
| `Plugin/src/dsp/DDX777Core.h` | Modello DSP core (applyFilters, overrideFilters, Meccanismi A/B) |
| `Plugin/tests/verify.py` | Suite test completa (band, T5, noise, THD, delay, drift, curva, A/B) — intangibile; usare `--force` dopo modifiche al core |
| `Plugin/tests/harness/main.cpp` | Harness rendering + flag `--ffilter`, `--k-vos`, `--k-lo`, `--k-opamp`, `--no-virtual-adc` |
| `Plugin/build/Release/ddx_harness.exe` | Harness compilato |
| `Plugin/tests/calibrate_mech12.py` | Calibrazione Meccanismi A/B (toni, flag, per-armoniche) |
| `Plugin/tests/characterize_thd_v4_full.py` | Characterization v4 (per-armoniche, livelli, ablazioni) → `build/char_thd_v4/` |
| `Plugin/tests/THD_characterization_v4.md` | Report v4 (per-armoniche plugin vs T4, predizioni §0.4, ablazioni) |
| `Plugin/tests/band_differential.py` | Diagnostica banda Virtual ADC on/off (evidenza L25) |
| `Plugin/tests/probe_h2.py` | Probe H2@2f per tono a livello verify.py vs calibrazione |
| `tests/sweep.py` | Tool iterazione rapida (measure/report, override 19 valori) |
| `Prep/SEIWA_DDX-777_HANDOFF.md` | Specificà hardware + concept stereo/UI |
| `Prep/PLUGIN_CHANGELOG.md` | Storico modifiche (append-only) |
| `Prep/00_stato_sessione.md` | Log sessioni + prossimo passo |
| `Prep/04_lacune.md` | Lacune L1-L25 (L1/L5/L12/L13 RISOLTE; L23/L24/L25 aperte S12) |
| `Prep/components.md` | Tabelle componenti |
| `Prep/02_componenti_raw.md` | Evidenze raw + append sessioni 11-12 (datasheet NE570N) |
| `Prep/03_blocchi.md` | Architettura a blocchi |
| `Prep/schematic.py` | Schema blocchi → PNG |
| `README.md` (root) | Panoramica progetto: build, test, parametri, preset, deviazioni |
| `Plugin/CMakeLists.txt` | Progettazione JUCE 8.0.9 (metadati spec, plugin + harness + ddx_gen_presets) |
| `Plugin/src/PluginProcessor.{h,cpp}` | Wrapper JUCE: APVTS 10 parametri, 2 core, BYPASS, PEAK atomics, state binario (copyXmlToBinary) |
| `Plugin/src/PluginEditor.{h,cpp}` | Editor 1000×136 (pannello), timer LED (PEAK/HOLD/POWER=!BYPASS) |
| `Plugin/src/ui/{RackPanel,Knob,LedIndicator,RockerSwitch,InputJack}.{h,cpp}` | Componenti UI (namespace `ddxui`) |
| `Plugin/src/dsp/Params.h` | Struct parametri (`mixLevel`, `factor` float + `factorClockFor()`) |
| `Plugin/tests/presets/main.cpp` | Generatore `ddx_gen_presets` (5 preset) |
| `Plugin/presets/*.xml` | I 5 preset (APVTS XML; rigenerati in 13b — FACTOR float) |
| `Plugin/tests/smoke/main.cpp` | `ddx_smoke`: smoke test audio headless del plugin completo (11 test, 48k/44.1k) |
| `Plugin/tests/screenshot/main.cpp` | `ddx_screenshot`: PNG UI headless (`paintEntireComponent` + PNGImageFormat) |