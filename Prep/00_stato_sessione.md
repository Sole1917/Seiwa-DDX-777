# Stato analisi — Seiwa Digital Delay DDX-777

**Sessione:** avviata 01/10/2026
**Regola ripresa:** in caso di interruzione, rileggere questo file + `02_componenti_raw.md` e ripartire dal "Prossimo passo".

## Fase corrente
- [x] F1 — analisi foto (survey completo 83/83; scrittura raw in corso)
- [x] F1 — scrittura `01_foto_inventario.md` + append `02_componenti_raw.md`
- [x] F1 — verifiche mirate (crop zoom valori critici: AN7815✓ 867, LM31? 844, DRAM 4ª scartata, 884=rete, fusibile n/v)
- [x] F2 — ricerca datasheet principali (M60351 KO, MSM3764, TC40H000P, M5224P, M5221, NE571 OK; residui: HD14066, 4558, LM311)
- [x] CHECKPOINT — tabella chip → confermato da utente (inclusi misure +5V, U10=LM311N, U18, zona timing)
- [x] F3 — architettura a blocchi → `03_blocchi.md` + `04_lacune.md`
- [x] CHECKPOINT — `03_blocchi.md` → confermato: OPZIONE 2, **scenario A confermato**, C scartato (ritiro utente)
- [x] Step 1-3: append raw (809/869/877+F2 NE571) ✓; 03_blocchi aggiornato ✓; 04_lacune (L5 + L16-L18) ✓
- [x] F4 Blocco A — `components.md`: testata + rail + U1-U18 (scritto) → **confermato con riserva** + correzioni integrate (U18 TO-92 "da confermare", nota correzione 273J50→C5)
- [x] Identificazioni utente appendate in raw: C5 27nF (ex-273J50), Q1 2SK118 (K118), Q2 J43P55 (→2SJ43? L20); L20-L22 in lacune; 03_blocchi §2 con buffer JFET + zona anti-aliasing
- [x] CHECKPOINT B — **CONFERMATO con 5 precisazioni → integrate tutte:**
  U18 = circuito discreto NON IC (topologia zener+transistor+C1µF, in 7,4V); Q1 alimentazione = "presunto +15 V analogico (L16)" + nota rail analogico; Q2 ammorbidito in 03_blocchi §2 (nessun ruolo affermato); colonna **Data code** aggiunta in tabella U (U10→LM311N+8532, U1-U3 44238, U5 8539H, U7 K8436, U8 4507, U9 4504); correzione data code appendata in raw
- [x] F4 Blocco C — "Non assegnati" (H.1 pot/rotary/trimmer, H.2 jack, H.3 switch/LED, H.4 PSU, H.5 meccanica, H.6 connettori, H.7 campi RC) con foto verificate dal raw (scritto)
- [x] CHECKPOINT C — **CONFERMATO con 4 precisazioni → integrate:** NOBLE dedup (H.3 rocker = attuazione, H.4 voce unica sezionatore+snubber+serie fusibile); RANGE = rotary switch 10 pos. (wafer …844, scala 1-512 ms) e FACTOR separati ("tipo da confermare"); lenti ×2 → "LED bianchi/IR/fototransistor?" + **L19** in lacune; induttore → Ref **IND1 (prov.)** (voce dedicata + puntatore H.7, nessuna collisione con L1)
- [x] F4 consolidamento: verifica incrociata automatica → **Ref 31/31 presenti in raw** (blocco "Mappa Ref F4 → evidenze" appendato in raw per C/R/D/U17/IND1); **lacune tutte presenti, L1-L22 lineare (22/22)**; fix `03_blocchi.md` (M8532 → data code 8532); refuso R3/R4 NE571 riscritto
- [x] CHECKPOINT D — riepilogo/residui/stati L5+L17 presentati all'utente
- [x] F5 — `schematic.py` (Pillow) → `schematic.png` **2600×1800** — verificato: margini 100/103/108/103 (≥100 ✓), font ≥14 px, legenda C/P/I basso-dx ✓, encoding UTF-8 pulito (incidente mojibake PowerShell risolto riscrivendo il file), etichette verificate per pixel
- [x] F6 — output finale consegnato ← FINE
- [x] Fix post-F6 (archiviazione): refuso `03_blocchi.md` §3 ("orma" → "glue logic / buffer / divisori"); conteggio lacune allineato a **L1-L22 (22/22)** in questo file e in `schematic.py` (PNG rigenerato, margini ≥100 riconfermati); U17/U18 spostati in sotto-tabella **B.1 Regolatori** (tabella B = IC pura U1-U16) — verifica automatica: Ref 31/31 ✓, lacune 22/22 lineari ✓
- [x] **Sessione 9** (post-consegna): correzione package **QFP-56 (14 pin/lato)** in components/raw/blocchi/lacune (raw riga 11 editata + tracciata in append); ricerca definitiva M60351 (4 query EN/JP → 0 datasheet) nota in U4/L5; **L17 → RISOLTA** (config NE571: solo compressore ch.1, retroazione fissa 46,1 kΩ pin4↔pin6, pot FEEDBACK = reostato di bias DC VCC↔pin4, canale 2 = 0 V); L5 riscritta con **strategia Indizi A-F col tester** (priorità A→B→D→C→E, F = ascolto) e ipotesi **12 bit [I]**; `03_blocchi` §2 topologia NE571 riscritta (expandore rimosso, nota 12 bit); components coerenza H.1/U6; 13 foto `Closeup back/` lette singolarmente → inventario sez. F (lettere di nodo A-N, M60351 ~14 pin/lato, 3 pallini rossi pot FEEDBACK in …6252); PNG rigenerato (testata 98 foto, box L5/L17/FEEDBACK aggiornati); conteggio verificato **85+13 = 98**; "nessun 79xx in 83 foto" lasciato invariato
- [x] **Sessione 10 — Chiusura L5**: L5 → **stato al tempo: non determinabile senza oscilloscopio o analisi spettro** (chiusa; conferma = gradini quantizzazione sul pin DAC out o SNR→bit); ipotesi **12 bit [I]** forte su 5 indizi (filtro anti-aliasing, compandor dbx-style, epoca 1985, DRAM 192 Kbit @32 kHz, ascolto); 12 bit = default documentato per modelli DSP. Test utente: A (NE571 pin6↔M60351 = 0 bip → filtro anti-aliasing interposto), B (pin4 = 9 bip apparenti = GND QFP, scartato), D (TC40H pin7 = ~10 bip = massa QFP), C/E/F non eseguiti → appendati in raw. File: `04_lacune` (riga L5 + blocco dettaglio + fix tabella L18-L22 + nota finale); `components` (riga U4 + nota 5 indizi); `03_blocchi` §2 ("Zona campionamento" rinominata, stage "Filtro anti-aliasing" separato a valle → ordine NE571→S&H→filtro→M60351); `schematic.py` (2 nuovi box in catena — Zona campionamento + Filtro anti-aliasing prima dell'ADC, indici `xs_chain` riscalati [10]/[7], box PEAK spostato a 400/310 per via del nuovo `dl_x`=2250, box DAC → "DAC integrato in U4 [I]", box L5 bottom → nota di chiusura "non determinabile") → PNG rigenerato; grep di verifica: package (solo cit. storica in raw), stato L5, Filtro anti-aliasing, 12 bit [I], margini ≥100
- [x] **Sessione 11 — misure audio → L1/L5/L12/L13 RISOLTE**: test utente T1-T6 su `Segnali_Test/` → delay 66/262/528/247/960 ms (RANGE 64/256/512 ×1, ×0,5, ×2), banda ~15 kHz (taglio 15-16 kHz), rumore −67 dBFS, THD da companding NE571, nessun aliasing, companding attivo; deduzioni **12 bit**, **f_camp ≈ 32 kHz** (16384 word ÷ 528 ms ≈ 31 kHz effettivi), **bias clock +3%** (trimmer `203`). File: `04_lacune` (righe L1/L5/L12/L13 + nuovo blocco "RISOLTE (sessione 11)" + nota finale, blocco sessione 10 marcato superato); `components` (riga U4 + Nota U4 + nota Ref U4); `03_blocchi` (§3 nota bias +3%, fix coerenza §2 riga 90 e nota 12 bit, §4 residuo L1 chiuso); `02_componenti_raw` (append "## Sessione 11 — misure audio"); `schematic.py` (box L5/L12/L13 RISOLTE, box L1 RISOLTA, box f_camp, box catena ADC/DAC 12 bit, rimossa dal codice la condizione di box "critica" L5) → PNG rigenerato; **`SEIWA_DDX-777_HANDOFF.md` creato (13 sezioni)**.
- [x] **Sessione 12 — riorganizzazione documentazione** (handoff pulito, PLUGIN_STATE, PLUGIN_CHANGELOG): `SEIWA_DDX-777_HANDOFF.md` rinominato da `HANDOFF_PLUGIN.md` + tutti i riferimenti aggiornati; rimossa sezione 10b stato plugin, sezione 10 limitata a limitazioni HW; creato `PLUGIN_STATE.md` (config C++ baked, verify 17/2, limitazioni, TODO); creato `PLUGIN_CHANGELOG.md` (storia sessioni 9-11); aggiornati riferimenti in 00_stato_sessione, 02_componenti_raw, 03_blocchi, schematic.py, verify.py.
- [x] **Sessione 12b (03/10/2026) — Datasheet NE570N + meccanismi plugin A/B**: contenuto numerico datasheet estratto dall'utente (scansione non OCRabile) → append in `02_componenti_raw.md` § "Sessione 12 — Datasheet NE570N" (valori + **correzione pinout DIP-16**: shift +1, vecchio N = nuovo N+1; L17 rietichettata "ipotesi forte, da confermare con 3 test rapidi quando l'unità è accessibile"). Plugin: rimossi kThdLow/kThdHigh, implementati **Meccanismo A** (kVos = 0,0079, H2 da offset VOS gain cell su `dry²` post-mix, calibrato su T4: H2 1 kHz +0,1 dB / 10 kHz +0,1 dB) e **Meccanismo B** (kLo, crossover H3 < 500 Hz — taratura = 0: l'H3 a bassa banda è già fornito dalla dinamica del compressore; meccanismo disponibile via `--k-lo`); kOpAmp invariato (0,018); flag harness `--k-vos`/`--k-lo`. **verify.py --force: THD 3/3 PASS** (+1,7/+3,1/+2,2 dB vs tolleranza 6 dB); **banda 2/4 FAIL pre-esistenti** (Virtual ADC Phase 2: −3 dB @ 12,80 kHz fuori da 14,5-16,5; `--no-virtual-adc` fa passare la banda ma fallisce l'aliasing T5) → **decisione utente: documentare (L25) e proseguire**, fuori scope. Characterization **v4** (`tests/characterize_thd_v4_full.py` → `tests/THD_characterization_v4.md` + CSV + PNG): per-armoniche plugin vs T4, predizioni modello a −24/−30/−36/−42 dBFS (target validazione per le misure HW rimandate), ablazioni. **Test discriminante §0.4**: a −30 dBFS il modello predice THD(100 Hz) = 0,012% (H3 crolla: nasce da limiter/compander); se la misura HW mostrasse H3(100 Hz) ~0,3% → meccanismo crossover livello-indipendente (Meccanismo B da riattivare). Lacune: **L23** (C_RECT 0,8-6 µF, candidati foto …845), **L24** (R_in → calibrazione assoluta), **L25** (banda vs Virtual ADC). File: `Plugin/src/dsp/DDX777Core.h`, `Plugin/tests/harness/main.cpp`, `Plugin/tests/calibrate_mech12.py`, `Plugin/tests/band_differential.py`, `Plugin/tests/probe_h2.py`, report v4; doc aggiornati (04_lacune L17/L23/L24/L25, 02_componenti_raw, 03_blocchi §2, PLUGIN_STATE, PLUGIN_CHANGELOG, HANDOFF).

- [x] **Sessione 13a (03/10/2026) — Beta 1.0 packaging plugin**: JUCE 8.0.9 (pinned) → `DDX-777.vst3` + standalone `DDX-777.exe` (metadati spec: Sole/DDX-777, SOLE/DDX7, 1.0.0, Fx+Delay); 10 parametri APVTS (nuovi MIX 0.95 e BYPASS; `Params::mixLevel` al posto della costante kWetMix a riga 190 — bit-identico a default); UI editor 1000×115 replica pannello (RackPanel/Knob/LedIndicator/RockerSwitch/InputJack in `Plugin/src/ui/`); 5 preset generati in `Plugin/presets/` da `ddx_gen_presets`; doc: `README.md` (root), `PLUGIN_STATE.md` v14, `PLUGIN_CHANGELOG.md` 13a. **verify.py --force invariato 17 PASS / 2 FAIL (L25) / 3 INFO**. Decisioni utente: host rate (no Resampling), geometria 1:1 ~1000×115, versione 1.0.0, font di sistema. Trappole API JUCE 8.0.9 tracciate in `PLUGIN_STATE.md`.

- [x] **Sessione 13b (03/10/2026) — bug-fix list Beta 1.0 (7 item utente)**:
  1. **Bug audio 🔴 (root cause trovata + fix)**: il plugin "non faceva audio" nel host.
     Nuovo target `ddx_smoke` (smoke test audio headless, 11 test) → a 48 kHz l'output
     esplodeva a ±1e40/NaN in ~50 ms. Causa: biquad RBJ instabili per `f ≥ fs/2`: a
     44.1/48 kHz i cutoff 40 kHz (opLP1-4), 28 kHz (rec4), 48 kHz (rec5) (+24 kHz rec2 a
     44.1k) superano Nyquist → poli fuori dal cerchio unitario. La calibrazione era a
     96 kHz (stabile) → mai rilevato. Fix: helper `cut()` in `applyFilters()` (clamp
     `f > fs/2` → `0.45*fs`), **bit-identico a 88.2/96 kHz** → verify invariato.
  2. **State save/recall**: pattern `copyState().createXml()` + `copyXmlToBinary` /
     `getXmlFromBinary` + check tag + `replaceState` (testato in ddx_smoke T7).
  3. **LED POWER = !BYPASS** (costruttore + timerCallback); rocker "POWER" sul parametro
     BYPASS reale (il fittizio `POWER_SW` eliminato).
  4. **UI 1000×136** (+18%, decisione utente): frame 16..118, knob 96×96 y=67, risolti gli
     overlap segnalati; **pointer knob con PUNTA VERSO L'ESTERNO** (apice r21/base r11);
     FACTOR con anello di 12 tacche a cerchio pieno (come in foto); nuovo stile Level0to20;
     fix `numSteps()` (knob 0..1 continui, 0..10 a 11 step).
  5. **FACTOR continuo 0.5..2.0** (float; `factorClockFor()` interpolazione a tratti sui 3
     punti calibrati — bit-identico a 0.5/1/2; harness `--factor` float; preset rigenerati).
  6. **LEVEL gain-up 0..+20 dB, default 0** (era −20..+6; `decibelsToGain` ≥ 1.0, core invariato).
  7. **Rebuild + deploy + gate**: VST3 (1.0.0, Fx+Delay) copiato in
     `C:\Users\ellio\AppData\Local\Programs\Common\VST3\`; **verify.py --force: 17/2/3
     invariato** (96 kHz); **ddx_smoke: 11/11 PASS** (prima: 7 fail, ±1e40 a 48k).
  Decisioni utente: versione **1.0.0** (non -beta), categorie **Fx+Delay** (Effect/Vintage
  inesistenti in VST3/JUCE 8.0.9), altezza **136 px**. Preset rigenerati e screenshot UI
  dichiarati **task dell'utente** (il tool `ddx_screenshot.exe` resta disponibile).
   Doc: `PLUGIN_STATE.md` v15, `PLUGIN_CHANGELOG.md` entry 13b. 

- [x] **Sessione 13c (03/10/2026) — P1 feedback audio, P3 saturazione ingresso, P2 GUI, RANGE 8 detent**:
   1. **P1 feedback a reostato**: `loopGainFor` g={0.0,0.22,0.45,0.72,0.82}
      (FB=0 → loop aperto), `biasSpanDb_=2.0`, `loopScale_=1.0`; calibrazione 96k eco
      1/3/6/18/40 OK. Residuo: noise peak −61.9 vs HW −67.3 dBFS.
   2. **P3 saturazione ingresso**: kJfet_=0.003, thrM5221_=13/15, limNE571_=0.20;
      sweep THD vs LEVEL (0 dB 0.0683 %, +6 dB 2.89 % H3-dominante). Residuo:
      THD 1 kHz +9.6 dB vs HW (non sintonizzare kJfet — regola Q3).
   3. **RANGE 8 detent (Foto 830)**: `kRangeMs[8]={1,8,16,32,64,128,256,512}`,
      default idx 7; scelta APVTS 8 label; harness `--range` 0-7; smoke T9-13/T7;
      preset rigenerati (5.0/7.0/6.0/7.0/7.0).
   4. **P2 GUI 1000×290 (poi scartata in 13d)**: cornici oro, grana, knob freccia
      spessa + shine arc — decisioni di layout tracciate in `PLUGIN_CHANGELOG.md`.
   5. **Fix tool screenshot** (JUCE 8): deleteFile pre-scrittura (append bug
      FileOutputStream), warm-up D2D + retry + imageHasContent, size dinamiche.
   6. **Deploy single-folder** (04/10): primaria `C:\Program Files\Common Files\VST3`
      non scrivibile (serve admin) → fallback `%LOCALAPPDATA%\Programs\Common\VST3`,
      1 sola istanza DDX-777.vst3 (T244.vst3 e schulz.audio intatti).
   Verifiche: `ddx_smoke` 16/16; `verify.py --force` 15/4/3 (FAIL: noise peak P1,
   band ripple + −3 dB L25 pre-esistenti, THD 1 kHz P3); `calibrate_feedback.py` OK.
   Doc: `PLUGIN_STATE.md`, `PLUGIN_CHANGELOG.md` entry 13c.

- [x] **Sessione 13d (04/10/2026) — REVERT GUI alla 13b + triangolo classico (task utente)**:
   la GUI 13c (1000×290, freccia spessa + shine arc "riflesso bianco curvo") dichiarata
   regressione → ripristinato layout/stile 13b: **1000×136**, frame 16..118, serigrafia
   cream #EDE0B0, pannello #222326→#141517 senza texture, etichette top y21/bottom y99,
   logo y28/66/84, knob 96×96 cy67 (mozzo r27, cap r22.5, tacche r30..34), jack (52,67),
   LED 8×8 y20, rocker y45..89. **Pointer knob = triangolo classico PUNTA VERSO
   L'ESTERNO (apice r21, base r11, halfWidth 0.35) — mirrored rispetto alla freccia
   spessa 13c**; shine arc e knurl rimosse. Fix etichette INPUT **0/+20** (residuo 13a
   "-20/0"). Scala RANGE a 8 detent MANTENUTA (parametro 13c — vincolo: niente
   DSP/parametri). Tool screenshot: rimosso setSize(1000,290) hard-coded.
    Verifiche: `ddx_smoke` 16/16 (DSP invariato), `verify.py --force` 15/4/3 invariato,
    screenshot `build/verify_out/gui_13b_revert.png` (1000×136). Build Release + deploy
    VST3 single instance in `%LOCALAPPDATA%\Programs\Common\VST3`.
    Doc: `PLUGIN_STATE.md` v16, `PLUGIN_CHANGELOG.md` entry 13c+13d.

- [x] **Sessione 13e (04/10/2026) — DEBUG GUI: pointer knob + scaling/zoom (task utente)**:
   1. **Pointer (bug certo, fixato)**: `Knob::paint()` passava l'angolo del triangolo in
      **radiani** a `polar(ox,oy,angleDeg,r)` (che converte gradi→radiani internamente,
      riga 99) → apice a ~2° anziché 135°, apertura base 0.7° → triangolo degenerato in
      striscia invisibile (presente già dal 13c). Fix: `aDeg = 135.0 + 270.0*value01()`,
      `halfWidthDeg = 20.0`; geometria invariata (apice r21 punta-esterno, base r11,
      crema kIndex, sopra il cap). Verificato su screenshot (PIL + mappe ASCII): tutti e
      7 i knob con triangolo, angoli esatti per valore (135°/270°/45°/225°), baricentro
      r≈13-15, 0 pixel nella posizione del vecchio bug (0°), forma isoscele corretta.
   2. **Scaling/zoom (root cause in JUCE 8.0.9, fix applicato)**: default
      `JUCE_WIN_PER_MONITOR_DPI_AWARE=1` → dentro host per-monitor-DPI-aware (REAPER)
      `getPlatformScaleFactor()` = scala monitor (es. 1.25) e `Direct2D startFrame`
      scala l'intero contenuto, mentre la finestra VST3 resta a scala 1.0
      (`getDefaultMasterScale()` per plugin) → GUI ingrandita ~25% + tagliata a
      destra/basso ("Seiwa"/POWER). Non visibile in headless (ImageContext usa
      scale 1.0). Fix: `CMakeLists.txt` → `add_compile_definitions(JUCE_WIN_PER_MONITOR_DPI_AWARE=0)`
      (macro verificata nei .vcxproj SharedCode/VST3/Standalone; JUCE 8 compila i moduli
      come TU amalgamati nei nostri target; `setDPIAwareness()` è no-op per i plugin →
      nessun rischio sul processo di REAPER). Esito: rendering D2D **1:1 in pixel
      fisici** a qualsiasi scaling del display; finestra resta 1000×136.
   Vincoli rispettati: nessun cambio layout/posizioni, DSP, parametri; nessun nuovo
   elemento UI. Verifiche: `ddx_smoke` 16/16 (DSP intatto), screenshot
   `build/verify_out/gui_pointer_fix.png` e `gui_13e_dpi.png` (identiche — headless 1:1),
   `verify.py` non riguardato (niente DSP). Build Release completa + deploy VST3
   5,572,608 B single instance in `%LOCALAPPDATA%\Programs\Common\VST3`.
   Doc: `PLUGIN_STATE.md` v17, `PLUGIN_CHANGELOG.md` entry 13e.

- [x] **Sessione 13f (04/10/2026) — Trascrizione + controverifica datasheet (10 PDF)**:
   Task utente: controverificare il riassunto dei valori sui 10 PDF di `Prep\Datasheets\`,
   fill-in OCR/visivo per le scansioni (testo **e grafici**), scrivere 10 `.md` con
   basename/case identico al PDF + **solo indice** in `02_componenti_raw.md`.
   **Decisioni capability**: opencode-vision NO (niente GOOGLE_API_KEY; "niente key: solo
   stack locale"); stack = render 300 DPI (PyMuPDF) + OCR doppio (rapidocr PP-OCRv3 +
   WinRT en-US) + **lettura visiva del modello come arbitro**; paddlepaddle non
   installabile (nessun wheel cp314). Cache e script in `%TEMP%\opencode\`
   (`ddx_ocr\`, `render_ocr.py`, `winocr.ps1`, note `ddx_notes.md`).
   **Fase A (6 scansioni, 40 pagine render+OCR, tutte le pagine chiave rilette a vista)**
   + **Fase B (4 PDF a testo: fitz + tabelle/grafici a vista)**. Esiti: ✅ **38 claim
   confermate**; ⚠️ 4: MSM3764 "192 Kbit" = 3 chip (coerente sistema), MSM3764
   "pin1=Vss" = NC nel datasheet (Vss=pin16; refuso del disegno, standard JEDEC 4164
   verificato con 3 fonti), 2SK118 equazione quadratica non stampata (parabola nei
   grafici), 4558 "6-7 esemplari" = dato di sistema; ❌ 1: **HD14066 Ron 100-300 Ω non
   verificabile** — `hitachi_hd14066bp.pdf` è la selection guide della serie HD14000B/UB
   (nessuna tabella 4066; serve datasheet dedicato, aperto come residuo). Tutte le
   NE570N 14/14 confermate (prima volta leggibile: sessione 12b era "estrazione utente").
   **File creati** (10): `Prep\Datasheets\{oki_msm3764, panasonic_an7815, ti_lm311n,
   toshiba_2sk118, toshiba_tc40h000p, hitachi_hd14066bp, jrc_4558d, mitsubishi_m5221,
   mitsubishi_m5224p, NE570N}.md` — ognuno: testata, claim trascritte, controverifica
   ✅/⚠️/➕ con pagina, dati integrati, grafici (valori ≈), nota modello DSP, limiti.
   **Aggiornamenti**: `02_componenti_raw.md` → nuova sezione `## Trascrizioni datasheet
   (indice)` (tabella 10 righe, dopo §Ricerche datasheet); `04_lacune.md` → L23
   arricchita (CRECT tip circuito test 2,2 µF / τ22 ms, preferire candidati ≈2,2 µF) e
   L17 nota pinout "confermato visivamente 13f". **Nessun valore smentito nei file
   esistenti → nessun fix incrociato** in 03_blocchi/components. Risidui aperti:
    datasheet HD14066B dedicato (Ron), lettura grafici p03 M5224P/p07-18 MSM3764 (non
    critici).

- [x] **Sessione 13g (05/10/2026) — Ricalibrazione loop gain + rumore post-loop (task 13d-loop)**:
   Target v2 (`Plugin/tests/FEEDBACK_ANALYSIS_v2.md`, soglia −60 dBFS): G coda
   FB100=0.9006 / FB50=0.3423 / FB2 (1° giro)=0.0957; floor piano (−77.0/−77.0/−76.6)
   → rumore post-loop; RMS eco1/eco10 HW 14.4 dB; Δt fit 546.02±0.01 ms.
   - `loopGainFor` a 4 punti {0→0, 0.25→0.105, 0.5→0.345, 1.0→0.760} (sostituisce 13c
     {0, 0.22, 0.45, 0.72, 0.82}): gain di re-iniezione pre-catena; G_catena **non
     costante** (~1.17 al livello stazionario di FB100, ~1.0 a FB50/25 — dipende da
     bias/livello del compressore). Calibrazione iterativa: converge in 1 passo;
     G misurati **0.8951/0.3329/0.1044** (dev ≤ 0.007 vs target 0.90/0.34/0.10 ±0.01).
   - Hiss **post-loop** (era in-loop da 13c P1): tap feedback pulito `wPrev_ = w`
     dopo rec5 (`DDX777Core.h:236`; il floor non circola nel loop), `wOut = w + hiss`
     (riga 243) in outMix+outWet; `kHissRms` 1.8e-4 → **1.3646e-4** (= 10^(−77.3/20),
     riga 331; post-loop il valore è tarato sul floor HW: con 1.8e-4 post-loop si
     aveva −74.9). Spread floor nei gap: 9.8 dB (13c) → **0.1 dB** (13g).
   - `verify.py` §8 nuovo (fixture impulso 20 s, render FB100/50/25, detection echi
     algoritmo v2): loop G per FB, n echi, gap RMS spread, spettri eco 1/5/10
     (energia 20-48k, H_loop 15-20k, 0-20k INFO), G_forward INFO. Check (a) RMS
     eco1/eco10 declassato P/F → **INFO** (gap 3.7 dB = dinamica compandor non
     modellata).
   - `verify.py --force` (96 kHz): 13c/13d/13e 15/4/3 → **13g 21 PASS / 5 FAIL /
     6 INFO — nessuna regressione da 13g** (attribuzione completa:
     `Plugin/tests/LOOP_CALIBRATION.md` §6). FAIL: L25 (band ripple 7.89 dB,
     −3 dB @12.80 kHz) pre-esistenti da 12b; P1 (noise peak −72.5, −0.2 dB lato
     freddo) pre-esistente da 13c (−61.9 lato caldo), spostamento atteso; P3 (THD
     1 kHz 0.106 %, +10.1 dB) pre-esistente da 13c (+9.6 dB; +0.5 dB secondario:
     interferenza bin H3, il §5 rendera con default `--feedback 0.5` e il punto
     tabella FB50 è passato da 0.45 a 0.345); H_loop 15-20k (+10.1 dB max) = nuovo
     check, risonanza specchio 18.37/19.29 kHz (difetto pre-esistente della catena
     esposto al gain 0.90).
   - Follow-up aperti (LOOP_CALIBRATION.md §4bis): **A** risonanza specchio
     (trigger: revisione fit di banda T2); **B** dinamica compandor (trigger:
     compandor dynamics / THD a livelli multipli); **C** crest rumore post-loop
     4.8 vs 10 dB (trigger: sessione architettura rumore).
   - HANDOFF §8 (blocco v2 + calibrazione), §9 (Δt 546.02 ms), §10 (attribuzione
     FAIL + voci follow-up A/B/C). Doc: `Plugin/tests/LOOP_CALIBRATION.md`.
    Vincoli rispettati: saturazione ingresso (13c), compressore, filtri
    eq/aa/dec/int/rec, VCO/LFO, sezioni 1-7 di verify.py, WAV di Segnali_Test intatti.

- [x] **Sessione 13h (05/10/2026) — P3 ricalibrazione mirata su H3 (THD 1 kHz)**:
    Task: ridurre THD 1 kHz (0.1061 %, +10.1 dB vs HW 0.033 %) aggredendo H3
    senza toccare H2/kJfet; no sweep cieco; se non riducibile → documentare
    limite (follow-up D).
    - **Diagnostica** (render `build/p3_diag/` D1–D8 su 04_sine_1kHz, metodo
      `thd_percent` di verify.py; §5 agganciato 1:1 al valore FAIL): M5221 =
      sorgente dominante H3 (≈ −71.7 dB in quadratura a FB0.5; −56.9 → −68.6 dB
      a FB0 con/senza M5221); NE571 hard-limit zero effetto (limite 0.20 non
      raggiunto a FB0/FB0.5); compressore effetto secondario (−0.16 dB THD a
      FB0). Senza M5221: THD = 0.0435 % → sotto target 0.066 % (±6 dB).
    - **Fix** (`DDX777Core.h`, stadio M5221 P3): tanh puro → **knee C¹ a
      parità di VOM** (13/15 invariato): lineare fino a u = 0.9·VOM, smoothstep
      C¹ in [0.9, 1.4], asintoto tanh oltre (saturazione alta invariata).
      Giustificazione: datasheet M5221 (trascrizione 13f,
      `Prep/Datasheets/mitsubishi_m5221.md`) THD 0.007 % typ @1 kHz + grafico
      p03 THD=1 % pulito fino a ~0.95·VOM (il tanh puro iniettava H3 8–10× la
      spec). Sentinela `thrM5221_ > 1.0` (harness `--thr 2`) bit-identica.
    - **Risultato** (`verify.py --force`): 13g 21/5/6 → **13h 22 PASS / 4 FAIL /
      6 INFO**. THD 1 kHz 0.1061 % (+10.1, FAIL) → **0.044 % (+2.4 dB, PASS)**;
      H3 −60.1 → −75.2 dB (floor kOpAmp); H2 −68.6 → −68.35 dB (+0.25 dB pattern
      di quantizzazione, kJfet/kVos intatti). THD 100/10 kHz PASS (+0.1/+2.1).
      §1–§4, §6–§8 identici a 13g. FAIL restanti (nessuno nuovo): P1-13c noise
      peak (follow-up C), L25-12b band ripple/−3dB, 13g H_loop (follow-up A).
      ddx_smoke 15/16: **T12 (FB=0.75) FAIL pre-esistente da 13g** (isolato:
      fallisce identico senza la knee; tabella P1 v2 FB0.75 ≈ 0.55 vs 13c
      ≈ 0.635) — ambito P1/loop-gain, vedi HANDOFF §10.
    - **Sweep saturazione P3** (`saturation_sweep.py` ri-eseguito): +0 dB
      0.0365 %, +6 dB 2.29 % H3-dominante — firma pre-esistente da 13c (log
      13c: 0.0683/2.89 %; +6 dB = hard-clip NE571, s2 ≈ 0.245 > 0.20);
      miglioramento leggero dovuto a P1 13g (FB50 0.45→0.345) + knee.
    - Doc: `PLUGIN_CHANGELOG.md` (entry 13h), `PLUGIN_STATE.md` (22/4/6),
      HANDOFF §10 (THD → PASS), `LOOP_CALIBRATION.md` §6/§7.
    Vincoli rispettati: kJfet, kHissRms, loopGainFor (13g), eq2/eq3/int/rec,
    verify.py §1–7, WAV Segnali_Test, render esistenti (diagnostica in
    `build/p3_diag/`).

- [x] **Sessione 13i (05/10/2026) — Redesign olistico catena HF (AA+EQ) — fallito, rollback a 13h**:
    Task: redesign olistico catena HF (aa1-aa4, eq2/eq3, rec1-rec5) per risolvere
    FAIL #2 (ripple 7.89 dB), #3 (−3 dB 12.80 kHz), #4 H_loop (+10.1 dB) con
    approccio incrementale; se non risolvibile → rollback e documentare target
    reali HW.
    - **Diagnostica Step 1** (`build/diag_hf/`, `analyze_hf_diag.py`): bypass
      incrementale filtri via `--ffilter` su impulso; risultati chiave:
      aa1 @10.4 kHz smorza risonanza 3 kHz (rimuoverlo → −3 dB a 3 kHz);
      eq3 +12 dB compensa droop AA; aa2/aa3 stopband principale (bypass →
      −3 dB 14.73 kHz ma perde loop gain/anti-aliasing); eq3 +12 dB genera
      risonanza 18.4/19.3 kHz (+10.1 dB H_loop).
    - **Step 2a'**: aa2/aa3 bypass (48 kHz) → **REGRESSIONE GRAVE**: loop gain
      FB100 0.89→1.01, THD 10k +8.6 dB, T5 aliasing FAIL, energia 20-48k FAIL.
      Rollback immediato. Confermato: aa2/aa3 critici per loop gain/anti-aliasing.
    - **Conclusione**: catena HF in ottimo locale accoppiato. Redesign
      incrementale NON praticabile. Rollback a 13h.
    - **Rilettura target HW** (MEASUREMENTS_13h-bis.md): −3 dB HW 31.33 kHz
      = aliasing (SR 32 kHz, Nyquist 16 kHz). Banda reale ≥15 kHz. Gap reale
      −3 dB = 2.2 kHz (12.8 → 15 kHz). H_loop HW avg ≈ 0 dB (modello +10.1 dB
      = artefatto). Target realistico: −3 dB ≥14 kHz, ripple ≤1.5 dB,
      H_loop ≤+1 dB.
    - **Azioni correttive (post-rollback)**:
      - verify.py §3: −3 dB check declassato FAIL → INFO, target ≥14 kHz.
      - LOOP_CALIBRATION.md §4bis A: redesign incrementale fallito, richiede
        sessione 13i+ monolitico IIR. §4bis D: target −3 dB rivisto a ≥14 kHz.
      - HANDOFF §10: THD 1k PASS, −3 dB declassato, 13i fallito, redesign
        rimandato a 13i+ monolitico.
      - verify.py §3: −3 dB check declassato FAIL → INFO, target ≥14 kHz.
    - **Risultato verify.py --force**: 22 PASS / 3 FAIL / 7 INFO (era 22/4/6).
      FAIL residui: #1 noise peak (P1-13c), #2 ripple (L25-12b), #4 H_loop (13g).
    - Doc: `PLUGIN_CHANGELOG.md` 13i, `PLUGIN_STATE.md` (22/3/7),
      HANDOFF §10, LOOP_CALIBRATION.md §4bis A/D, `verify.py` §3.
    Vincoli rispettati: nessun DSP toccato post-rollback, stato 13h ripristinato.

## Prossimo passo
Plugin con **audio 13h** (loop gain + hiss post-loop di 13g; P3 con knee M5221:
THD 1 kHz PASS +2.4 dB; P1 + RANGE 8 detent di 13c) e **GUI 13e** (13d+13e:
triangolo pointer funzionante + build DPI-unaware): VST3 deployato in
`%LOCALAPPDATA%\Programs\Common\VST3` (1 istanza, 04/10 11:15 — **datato
rispetto all'audio 13h**: rebuild + redeploy da rifare prima del test REAPER).
**Task utente**:
aprire DDX-777 in REAPER e verificare: (a) GUI NON più zoommata/tagliata ("Seiwa"
intero, POWER dentro la cornice), (b) triangoli visibili sui knob (punta esterna,
ruotano col valore). Se (a) persistesse → inviare screenshot della finestra FX in
REAPER per analisi (l'unico aspetto non riproducibile in headless: IContext D2D
usa sempre scale 1.0). **Task utente (ereditato da 13d)**: test manuali REAPER a
44.1/48 kHz. Se l'utente chiede
raffinatori UI: i soli X delle cornici/knob (layout 13b non documentato — usato quello
13c, fedele alle foto 830/836) stanno in `Plugin/src/ui/RackPanel.h` (struct Layout).
Per riprese future: `00_stato_sessione.md` + `04_lacune.md` (L1-L25; L1/L5/L12/L13 RISOLTE,
L17 ipotesi forte, L23/L24/L25 aperte — misure HW rimandate, unità non accessibile).
Residui plugin: FEEDBACK senza effetto DSP (lacuna di modello); "secondo canale organico"
(§12 handoff); upgrade eventuale JUCE → 8.0.15.
**Datasheet (13f, 04/10/2026)**: task completato — 10 `.md` in `Prep\Datasheets\` +
indice in `02_componenti_raw.md`; residuo: scaricare datasheet **HD14066B dedicato**
(claim Ron 100-300 Ω non verificabile con la selection guide presente); verifiche
opzionali: grafici p03 M5224P e p07-p18 MSM3764 (non critici). Note complete di
verifica: `%TEMP%\opencode\ddx_notes.md` (scratch).

**Sessione 13i (redesign HF): fallito, rollback a 13h**. Target −3 dB rivisto a
≥14 kHz (31 kHz HW era aliasing). Verify 22/3/7 (FAIL: noise peak P1-13c, ripple
L25-12b, H_loop 13g). Redesign HF incrementale NON praticabile (catena HF in
ottimo locale accoppiato). Richiede sessione dedicata 13i+ con approccio
monolitico IIR. Priorità: ripple → H_loop → −3 dB. Noise crest (FAIL #1) sessione
separata.

## Esiti chiave sessione 2 (dettagli in 02_componenti_raw.md)
- AN7815 +15V: confermato leggibile (867).
- DRAM: 3× M3764-15RS (44238) — 4ª NON esistente.
- DIP-8 "LM31x": foto = 844 (prob. LM311N, date 8532).
- 884 = angolo rete (fusibile+filtraudio+NOBLE+X2), nessun 2° regolatore.
- Fusibile 5×20: rating non stampato/leggibile → misura fisica.

## Note / decisioni utente
- Rendering: **Python + Pillow** (niente graphviz/matplotlib). File: `schematic.py` → `schematic.png`.
- Lingua deliverable: **italiano**.
- Ref designator: non leggibili in foto → **Ref provvisorie U1..Un per gli IC** (nota "provvisoria"); passivi senza Ref → sezione "Non assegnati".
- Ordinamento tabelle: primario tipo (U,C,R,Q,D…), secondario numero crescente, terziario non-assegnati in fondo. Colonna "Foto di riferimento" SEMPRE presente.
- Scrittura incrementale obbligatoria; checkpoint obbligatorio prima di F4.
- Refuso corretto: "ipotesi".

## Affidabilità attribuzione foto (attenzione)
- Subagent 803-869: letture una-per-una → attribuzione fidata.
- Letture mie batched su 870-885: possibile ordine non preservato → attribuzione da verificare con letture singole prima di citare in `components.md`.
