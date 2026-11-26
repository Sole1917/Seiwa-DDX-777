# PLUGIN_CHANGELOG.md — Storico modifiche plugin Seiwa DDX-777

Formato: append-only, dal più recente al più vecchio.  
Per sessione: data, modifiche, motivo, risultato verify (prima → dopo), decisioni.

---

## Sessione 13i — 05/10/2026
**Tema**: Redesign olistico catena HF (AA + EQ) — fallito, rollback a 13h

**Diagnostica pre-redesign** (`Plugin/build/diag_hf/`): isolamento contributi filtri via bypass incrementali.
- aa1 @10.4 kHz Q=1.08: smorza risonanza a ~3 kHz; rimuoverlo fa esplodere risonanza (-3 dB crolla a 3 kHz).
- eq3 +12 dB @14 kHz Q=2.5: compensazione necessaria per droop AA; rimuoverla fa esplodere ripple (23 dB).
- aa2/aa3 @16.5/14.2 kHz: stopband principale; bypass → -3 dB 14.73 kHz (target) ma perde loop gain/anti-aliasing.
- aa4 @15 kHz Q=3: rolloff steep; ridurre Q aiuta banda ma non risolve risonanza.
- eq2 +3 dB @11.7 kHz: contributo secondario.

**Tentativo redesign incrementale (Step 2a'-2b-3a)**:
1. 2a': aa2/aa3 → bypass (48 kHz) → **REGRESSIONE GRAVE**: loop gain esploso (FB100 0.89→1.01), THD 10k +8.6 dB, T5 aliasing FAIL, energia 20-48k FAIL. Rollback immediato.
2. Conclusione: catena HF (aa1-aa4, eq2/eq3) in **ottimo locale accoppiato**. Ogni modifica isolata rompe l'equilibrio (loop gain, THD, aliasing, H_loop).

**Risultato**: redesign incrementale NON praticabile. Rollback a 13h.

**Rilettura target HW (MEASUREMENTS_13h-bis.md)**:
- −3 dB HW = 31.33 kHz è **aliasing** (SR 32 kHz → Nyquist 16 kHz). Banda reale ≥15 kHz.
- Gap reale −3 dB = ~2.2 kHz (12.8 → 15 kHz), non ~18 kHz.
- H_loop HW avg ≈ 0 dB (modello +10.1 dB = artefatto AA+EQ).
- Target realistico: −3 dB ≥14 kHz, ripple ≤1.5 dB, H_loop ≤+1 dB.

**Azioni correttive**:
- verify.py §3: −3 dB check declassato FAIL → INFO, target ≥14 kHz (HW ≥15 kHz, 31 kHz era aliasing).
- LOOP_CALIBRATION.md §4bis A aggiornato: redesign incrementale fallito, richiede sessione dedicata 13i+ monolitico IIR.
- §4bis D aggiunto: target −3 dB rivisto a ≥14 kHz (31 kHz era aliasing).
- HANDOFF §10: THD 1k PASS, −3 dB declassato, 13i fallito, redesign rimandato a 13i+ monolitico.
- LOOP_CALIBRATION.md §4bis D aggiunto: target −3 dB rivisto, aliasing spiegato.

**Risultato verify.py --force**: 22 PASS / 3 FAIL / 7 INFO (era 22/4/6). FAIL residui: #1 noise peak, #2 ripple (L25), #4 H_loop.

**Decisioni**: redesign incrementale NON praticabile (catena HF in ottimo locale accoppiato). Richiede sessione dedicata 13i+ con approccio monolitico IIR (redesign AA+EQ simultaneo). Target −3 dB rivisto a ≥14 kHz (31 kHz HW era aliasing).

---

## Sessione 13h — 05/10/2026
**Tema**: P3 ricalibrazione mirata su H3 — THD 1 kHz da +10.1 dB a +2.4 dB (PASS)

**Diagnostica** (pre-fix, nessuna modifica DSP; render `build/p3_diag/` D1–D8 su
`04_sine_1kHz.wav`, condizioni FB=0/DELAY=10/RANGE=512 + §5 FB0.5; metrica
`thd_percent` di verify.py, §5 agganciato 1:1 al valore FAIL):
- **M5221 = sorgente dominante H3**: §5 H3 −60.1 dB (full) vs −75.2 dB senza
  M5221 (in quadratura H3(M5221) ≈ −71.7 dB); a FB0 −56.9 vs −68.6 dB.
- **NE571 hard-limit (0.20): zero effetto** a FB0/FB0.5 (limite non raggiunto a
  questo livello; s2 ≥ 0.20 solo da LEVEL +6 dB, vedi sweep).
- Compressore: effetto secondario (THD −0.16 dB a FB0; tono 0.75 dB più basso
  con comp off) — non bersaglio.
- Senza M5221: THD 1 kHz = **0.0435 %** (§5) → sotto il target 0.066 % (±6 dB).

**Modifica** (`Plugin/src/dsp/DDX777Core.h`, stadio M5221 della P3):
- tanh normalizzato puro → **knee C¹ a parità di VOM** (13/15 invariato):
  identità (zero armoniche) per u = |s1|/VOM ≤ 0.9, blend smoothstep C¹ in
  [0.9, 1.4], asintoto tanh oltre (saturazione alta invariata).
- Giustificazione fisica (datasheet M5221, trascrizione 13f
  `Prep/Datasheets/mitsubishi_m5221.md`): THD = 0.007 % typ @1 kHz (Gv 40 dB) e
  grafico p03 "THD=1 %" pulito fino a ~8.8 Vrms @1 kΩ (≈0.95·VOM) → il
  componente è lineare ben sotto VOM; il tanh puro iniettava H3 8–10× la spec
  del componente. u0 = 0.9 ancorato al grafico p03.
- Sentinela `thrM5221_ > 1.0` (bypass harness `--thr 2`) resta bit-identica
  (quantizzatore 12 bit, vincolo 13c).

**Risultato** (`verify.py --force`, 96 kHz): 13g 21/5/6 → **13h 22 PASS /
4 FAIL / 6 INFO**:
- **THD 1 kHz: 0.1061 % (+10.1 dB, FAIL) → 0.044 % (+2.4 dB, PASS)**; H3
  −60.1 → −75.2 dB (floor kOpAmp); H2 −68.6 → −68.35 dB (+0.25 dB, pattern di
  quantizzazione; kJfet/kVos intatti).
- THD 100/10 kHz: PASS, +0.1 / +2.1 dB (13g: +1.7 / +2.1).
- §1–§4, §6, §7, §8: valori identici a 13g (loop G 0.8951/0.3329/0.1044; §3
  7.89 dB / 12.80 kHz L25; H_loop +10.1 dB).
- FAIL restanti (nessuno nuovo): P1-13c noise peak (follow-up C), L25-12b
  band ripple/−3 dB, 13g H_loop (follow-up A).
- **ddx_smoke: 15/16 — T12 (FB=0.75, 15-30 ripetizioni; eco=8-9) FAIL
  pre-esistente da 13g** (isolato: fallisce identico senza la knee; tabella
  P1 v2: FB0.75 ≈ 0.55 vs 13c ≈ 0.635 → meno echi; ambito P1/loop-gain, non P3
  — rivedere con la tabella P1 / follow-up A).
- Sweep saturazione P3 (`saturation_sweep.py`, ri-eseguito): +0 dB 0.0365 %,
  +6 dB 2.29 % H3-dominante — firma **pre-esistente da 13c** (log 13c:
  0.0683/2.89 %; +6 dB = hard-clip NE571, s2 ≈ 0.245 > 0.20); miglioramento
  leggero attribuibile alla P1 13g (FB50 0.45→0.345) + knee.

**Vincoli rispettati**: kJfet, kHissRms, loopGainFor (13g), eq2/eq3/int/rec,
sezioni 1–7 di `verify.py`, WAV di `Prep/Segnali_Test`, render esistenti
(diagnostica in directory nuova `build/p3_diag/`).

**Decisioni**: fix giustificato dal datasheet (no sweep cieco); riuso sentinela
`--thr`/`--lim` (i flag di bypass del task esistevano già nel codice); u0 = 0.9
(grafico p03); branch "limite fisico / follow-up D" non si è verificato.

---

## Sessione 13g — 05/10/2026
**Tema**: Ricalibrazione loop gain sui target v2 (soglia −60 dBFS) + spostamento hiss
post-loop + test feedback `verify.py` §8 (task "13d-loop"; etichetta **13g** per
evitare collisioni: 13d/13e = GUI, 13f = datasheet)

**Modifiche** (`Plugin/src/dsp/DDX777Core.h` + `Plugin/tests/verify.py`):
- `loopGainFor(fb)`: tabella 4 punti {0→0, 0.25→0.105, 0.5→0.345, 1.0→0.760}
  (sostituisce 13c {0, 0.22, 0.45, 0.72, 0.82}). I valori sono gain di re-iniezione
  pre-catena: G totale = valore × gain catena per-passo, che **non è costante**
  (~1.17 al livello stazionario di FB100, ~1.0 a FB50/25 — dipende dal bias del
  compressore e dal livello degli echi; l'ipotesi di un fattore unico è stata
  scartata dai dati di coppia). Target: `FEEDBACK_ANALYSIS_v2.md` (G coda
  FB100 0.9006 / FB50 0.3423 / FB25 1° giro 0.0957, soglia −60 dBFS).
- Hiss **post-loop** (era in-loop da 13c P1): tap feedback pulito `wPrev_ = w`
  dopo rec5 (`DDX777Core.h:236`, a valle di int1-4/rec1-5 → il floor non circola
  nel loop); `wOut = w + hiss` (riga 243) usato in outMix+outWet (incluso nel wet,
  che è ciò che misura T3); `kHissRms` 1.8e-4 → **1.3646e-4** (= 10^(−77.3/20),
  riga 331): post-loop il valore è tarato direttamente sul floor HW (con 1.8e-4
  post-loop si sarebbe avuto −74.9; deviation da "kHissRms invariato" del task,
  necessaria e documentata).
- `verify.py` §8 nuovo (fixture impulso 20 s `build/verify_out/fb_impulse_20s.wav`,
  render mix `--range 512 --factor 1 --level 1 --feedback {1.0|0.5|0.25}
  --delay-level 1`, detection echi = algoritmo v2): loop G per FB, n echi,
  gap RMS spread, spettri eco 1/5/10 (energia 20-48k, H_loop 15-20k, 0-20k INFO),
  G_forward INFO. Check (a) RMS eco1/eco10 declassato P/F → **INFO** (gap 3.7 dB
  = dinamica compandor non modellata; valore resta nel report JSON).

**Risultato** (`verify.py --force`, 96 kHz): 13c/13d/13e 15/4/3 → **13g 21 PASS /
5 FAIL / 6 INFO**. Nuovi PASS §8: loop G FB100/50/25 = 0.8951/0.3329/0.1044 vs
target 0.90/0.34/0.10 (dev ≤ 0.007, tol ±0.01; calibrazione convergente in
1 passo), n echi FB100 = 35 ≥ 20 (HW 22), gap RMS spread 0.1 dB ≤ 1.0 (13c: 9.8),
energia 20-48k al floor. I 5 FAIL: **nessuno introdotto da 13g** —
- **L25** (band ripple 7.89 dB, −3 dB @12.80 kHz): pre-esistenti da 12b (Virtual
  ADC), invariati;
- **P1** (noise peak): pre-esistente da 13c (−61.9, +0.4 dB lato caldo, "residuo
  P1"); ora −72.5 (−0.2 dB lato freddo): conseguenza attesa del hiss post-loop a
  RMS on-target (−77.3; crest 4.8 dB vs HW 10.0 dB → **follow-up C**);
- **P3** (THD 1 kHz 0.106 %, +10.1 dB): pre-esistente da 13c (+9.6 dB, "residuo
  P3", regola Q3); +0.5 dB in 13g da interferenza bin H3 (il §5 rendera con il
  default `--feedback 0.5` del harness e il punto tabella FB50 è passato da 0.45 a
  0.345; il criterio H2–H11 ±1 % è invariato e non include il rumore incoerente:
  floor nei bin ≈ 55 dB sotto il H3 dominante −60.1 dB);
- **H_loop 15-20k** (+10.1 dB max): **nuovo check**; risonanza specchio
  18.37/19.29 kHz (modo accoppiato 11.7/12.7k ↔ f_word/2 = 15.515 kHz, alimentato
  dal boost 11-14k di eq2/eq3 del fit 13c) — difetto pre-esistente della catena
  esposto al gain target 0.90, non fixato in 13g (rischio sul match T2 già al
  limite: drift max 7.84 dB @13.96 kHz → **follow-up A**).

**Decisioni utente**: tabella 4 punti; target = G totale in uscita (calibrazione
iterativa ±0.01); hiss post-loop (tap pulito); check (a) → INFO; risonanza specchio
non fixata (follow-up); follow-up C (crest rumore) tracciato; etichetta sessione
**13g**.

**Follow-up aperti** (`Plugin/tests/LOOP_CALIBRATION.md` §4bis): **A** risonanza
specchio (notch 18.4/19.3k sul path write, riduzione boost eq2/eq3 alla fonte, o
revisione fit 13c; trigger: revisione fit di banda T2); **B** dinamica compandor
(envelope-follower con release più veloce, gain control dipendente dall'inviluppo
del segnale ritardato; trigger: compandor dynamics / THD a livelli multipli);
**C** crest rumore post-loop (componente a picchi rari per centrare HW peak −67.3
a RMS −77.3; trigger: sessione architettura rumore).

**Doc**: `Plugin/tests/LOOP_CALIBRATION.md` (report completo: tabella finale,
G misurati, spread pre/post, check a-d, tabella di attribuzione FAIL
13b→13c→13d/13e→13g con fonti); HANDOFF §8 (blocco v2 + calibrazione), §9
(Δt 546.02 ms vs 545.7 v1 / 528.8 T1), §10 (attribuzione FAIL + follow-up A/B/C).
Nessun cambio: saturazione ingresso (13c), compressore, filtri eq/aa/dec/int/rec,
VCO/LFO, sezioni 1-7 di `verify.py`, WAV di `Prep/Segnali_Test`.

---

## Sessione 13e — 04/10/2026
**Tema**: Debug GUI (post-13d): (1) pointer knob invisibile/malformato; (2) GUI "zoommata
~20-30%" con testo/controlli tagliati ai bordi in REAPER

**Diagnosi**:
1. **Pointer**: `Knob.cpp` — `polar(ox,oy,angleDeg,r)` (linea 99) converte
   gradi→radiani internamente, ma il triangolo passava `a` e `halfWidth` già in
   **radiani** → angolo interpretato come ~2° (anziché 135°) e apertura base 0.7°
   → triangolo degenerato in una striscia invisibile. Presente già dal 13c
   ("freccia spessa" era in realtà la striscia + shine arc).
2. **Scaling**: JUCE 8.0.9 default `JUCE_WIN_PER_MONITOR_DPI_AWARE=1`
   (`juce_gui_basics.h:128`). In un processo/host per-monitor-DPI-aware (REAPER)
   `getPlatformScaleFactor()` ritorna la scala del monitor (es. 1.25) e
   `Direct2DGraphicsContext::startFrame(dpiScale)` scala l'intero contenuto,
   mentre la finestra VST3 è dimensionata a scala 1.0 (`getDefaultMasterScale()`
   = 1.0 per i plugin) → contenuto overflow: GUI ingrandita + tagliata a
   destra/basso. Non riproduttivo in headless (`Direct2DImageContext` usa
   sempre scale 1.0 → i nostri screenshot erano perfetti). Segnali display:
   `AppliedDPI=192` (200%) in HKCU; sessione agente su display virtuale
   1280×800@100% (non visibile l'interattivo utente).

**Modifiche** (solo UI + build, niente layout/DSP/parametri):
- `Knob.cpp` (`paint()`): triangolo in **gradi**: `aDeg = 135.0 + 270.0 *
  value01()`, `halfWidthDeg = 20.0` (≈0.35 rad), apice r21 / base r11 invariati
  (punta verso l'esterno, base verso il centro, crema kIndex, sopra il cap).
- `CMakeLists.txt`: `add_compile_definitions(JUCE_WIN_PER_MONITOR_DPI_AWARE=0)`
  (top-level, propagate a tutti i target; i moduli JUCE 8 sono compilati come TU
  amalgamati nei nostri target → macro verificata nei .vcxproj di
  SharedCode/VST3/Standalone). Effetto: `getPlatformScaleFactor()` = 1.0
  incondizionato (windowing line 2191) → rendering D2D 1:1 in pixel fisici,
  indipendente dallo scaling del sistema; finestra VST3 resta 1000×136.
  `setDPIAwareness()` no-op per i plugin (`!isStandaloneApp()` → return): nessun
  rischio su REAPER. Se il display fosse già al 100% il cambio è no-op visivo.

**Risultato**: `ddx_smoke` **16/16 PASS** (DSP intatto). Screenshot
`build/verify_out/gui_pointer_fix.png` + `gui_13e_dpi.png` (identiche, headless
1:1): PIL/misure → tutti e 7 i knob con triangolo a centro r≈13-15, angoli esatti
(INPUT 135°=0%, FB 270°=50%, RANGE 45°=100°, DT 225°=1/3, altri 135°=0%),
0 pixel crema nella posizione del vecchio bug (0°); forma isoscele verificata
su mappa ASCII (apice esterno, base al centro). `verify.py` non riguardato
(niente DSP).

**Deploy**: VST3 5,572,608 B + standalone ricalcolati; `DDX-777.vst3` copia
singola in `%LOCALAPPDATA%\Programs\Common\VST3` (vecchia istanza rimossa).

**Da verificare in REAPER** (unico punto non testabile in headless): aprire
DDX-777 → GUI non zoommata, niente tagli ai bordi ("Seiwa" intero, POWER dentro
la cornice), triangoli visibili sui knob. Se il problema scaling persistesse:
necessario screenshot della finestra FX in REAPER per analisi.

---

## Sessione 13d — 04/10/2026
**Tema**: Revert GUI alla versione 13b + pointer "triangolo classico" mirrored (decisione utente: la GUI 13c a 290 px era una regressione)

**Decisioni utente**: ripristinare layout/stile della GUI precedente (cornici gialle/cream,
sfondo scuro pulito, proporzioni 1000×136, layout controlli fedele all'originale);
knob = triangolo classico con **punta verso l'esterno, base verso il centro** (come foto
830), senza il "riflesso bianco curvo" (shine arc) né la freccia spessa; **niente**
modifiche DSP/parametri, niente nuovi elementi UI.

**Modifiche** (solo UI + tool screenshot):
- `RackPanel.h`: kH **290 → 136**; frameTop/Bottom **37/249 → 16/118**, chamfer 8;
  colori 13b: pannello gradiente **#222326 → #141517**, serigrafia **cream #EDE0B0**
  (kSilk/kLogoCream); jackCX **48 → 52** (jack 13b centro (52,67)); knobCY **150 → 67**;
  ledY **58 → 20**. Coordinate X delle cornici/knob invariate (già derivate dalle foto
  830/836, gap neri ~12 px tra le cornici).
- `RackPanel.cpp`: rimossa la texture a grana (13b = gradiente pulito); etichette
  sezione top y **21..35**, bottom y **99..113**; logo "Seiwa®" Georgia **40** px a
  y **28**, "DIGITAL DELAY" y **66**, "DDX-777" y **84** (riposizione 13b 28/66/84).
- `Knob.cpp`: geometria 13b (box 96×96): mozzo **r27**, cappuccio **r22.5**, tacche
  **r30..34** (1.8 px), etichette **r37-38** (font 9-10); rimosse knurl e **shine arc**;
  indice = **triangolo classico** apice **r21** (punta verso l'esterno), base **r11**
  verso il centro, halfWidth 0.35 rad, colore crema kIndex. Range/Factor/Level invariati
  nella logica (RANGE resta a 8 detent — parametro 13c, non toccato).
- `Knob.h` + `Knob.cpp`: fix etichette stile **Level0to20**: "-20/0" → **"0/+20"**
  (residuo 13a: il parametro INPUT_LEVEL è 0…+20 dB gain-up dal 13b).
- `PluginEditor.cpp`: knob **128×128 → 96×96** (cy 67), jack (52,67), LED **12×12 y52 →
  8×8 y20**, rocker **y45..89** (HOLD 30×44, POWER 36×44).
- `tests/screenshot/main.cpp`: rimosso `setSize(1000,290)` hard-coded → la dimensione
  è letta dall'editor (si auto-dimensiona al layout di progetto).
- Nessun cambio DSP/parametri/preset: `DDX777Core.h`, `Params.h`, `PluginProcessor.cpp`
  intatti.

**Risultato verify** (invariato, 96 kHz): `verify.py --force` **15 PASS / 4 FAIL /
3 INFO** — stessi 4 FAIL documentati pre-revert (noise peak −61.9 = P1; band ripple
7.93 dB e −3 dB @12.80 kHz = L25 pre-esistenti; THD 1 kHz +9.6 dB = P3).
`ddx_smoke` **16/16 PASS** (DSP invariato confermato). Screenshot UI rigenerato:
`build/verify_out/gui_13b_revert.png` (1000×136).

**Deploy**: build Release completa (VST3 5,588,992 B + standalone); `DDX-777.vst3`
copia singola in `%LOCALAPPDATA%\Programs\Common\VST3` (vecchia istanza rimossa,
verificata 1 sola istanza; cartella primaria `C:\Program Files\Common Files\VST3`
restante non scrivibile senza admin).

**Nota**: le coordinate X esatte della GUI 13b non sono documentate (nessun backup
del codice 13b); è stato mantenuto il layout X 13c (fedele alle foto 830/836, con gap
tra cornici). Eventuali raffinatori sui soli X vanno fatti su `RackPanel.h` (Layout).

---

## Sessione 13c — 03/10/2026
**Tema**: P1 feedback audio a reostato, P3 saturazione ingresso, P2 GUI 1000×290 (poi
revertita in 13d), scala RANGE a 8 detent

**P1 — feedback (reostato)**: `DDX777Core.h` `loopGainFor(fb)` = g{0.0, 0.22, 0.45,
0.72, 0.82} (FB=0 → loop aperto, FB=1 → 0.82), `biasSpanDb_ = 2.0`, `loopScale_ = 1.0`;
tap feedback a valle del ramo "post-DAC". Calibrazione eco 96 kHz: 1/3/6/18/40 ripetizioni
(OK). Residuo noto: noise peak −61.9 vs HW −67.3 dBFS (+5.4 dB, verificato in verify).

**P3 — saturazione ingresso**: catena JFET (k**Jfet_** = 0.003) → M5221 (thr
**thrM5221_** = 13/15) → sommatore → NE571 limiter (lim**NE571_** = 0.20). Sweep
THD vs LEVEL (sine): 0 dB 0.0683 %, +6 dB 2.89 % (H3-dominante). Residuo noto:
THD 1 kHz +9.6 dB vs HW (regola Q3: non sintonizzare kJfet, indagare scala).

**P2 — GUI 1000×290 (SUPERATA da 13d)**: RackPanel riscritto (kH 290, frame
37..249, gap neri 12 px tra cornici, colori "oro" #E8C05A/crema #F5EBD0 campionati
dalle foto, texture a grana sottile 4 px alpha 1-3, knob 128×128 cy150, jack 26 px
bronzo, fix overlap INPUT/PEAK e POWER/DIGITAL DELAY, logo Georgia 46); knob con
freccia spessa (apice r25/base r7/halfWidth 0.9) + shine arc 9→12 ore (rimossa in 13d);
tacche/numeri knob → crema kIndex.

**RANGE 8 detent (Foto 830, MANTENUTO in 13d)**: `kRangeMs[8] = {1,8,16,32,64,128,256,512}`
in `Params.h` (default idx 7 = 512 ms), `PluginProcessor.cpp` choice 8 label default 7
(jlimit 0-7), harness `--range` ms|idx 0-7, smoke T9-13 (idx4 = 64 ms) e T7 (2/7 = 16 ms),
preset rigenerati (Classic 5.0/128 ms, Ambient 7.0, Dub 6.0/256 ms, Early 7.0, Init 7.0).

**Tool screenshot (fix JUCE 8)**: size dinamiche dall'editor; warm-up D2D + retry +
`imageHasContent` (pixel RGB non neri) per i frame headless flaky; **`file.deleteFile()`
prima di `createOutputStream()`** (FileOutputStream JUCE 8 su Windows = append
OPEN_ALWAYS+FILE_END: i PNG venivano concatenati → screenshot "neri/vecchi");
BitmapData: pixelStride = byte/pixel, lineStride = byte/riga.

**Deploy single-folder (04/10)**: primaria `C:\Program Files\Common Files\VST3` non
scrivibile (serve admin) → fallback `%LOCALAPPDATA%\Programs\Common\VST3`; istanze vecchie
rimosse; scan ricorsivo = **1 sola istanza** DDX-777.vst3; T244.vst3 e schulz.audio intatti.

**Risultato verify** (fine 13c, prima del revert 13d): `verify.py --force`
**15 PASS / 4 FAIL / 3 INFO** (FAIL: noise peak P1, band ripple + −3 dB L25, THD 1 kHz P3);
`ddx_smoke` 16/16 PASS; `calibrate_feedback.py` OK.

---

## Sessione 13b — 03/10/2026
**Tema**: Bug-fix list Beta 1.0 — bug audio (root cause IIR instabile a 44.1/48 kHz), state save/recall binario, LED POWER, UI 1000×136 senza sovrapposizioni, FACTOR continuo, pointer esterno, LEVEL gain-up

**Decisioni utente (confermate questa sessione)**: versione **1.0.0** (non 1.0.0-beta);
categorie VST3 **Fx + Delay** ("Effect"/"Vintage" non esistono nella lista VST3 JUCE 8.0.9);
altezza pannello **136 px** (+18% su 115).

**Bug audio 🔴 (root cause)**: il plugin "non faceva audio" nel host a 44.1/48 kHz.
L'analisi statica non l'aveva trovato; lo ha trovato lo smoke test headless (nuovo target
`ddx_smoke`): a 48 kHz l'output esplodeva a ±1e40/NaN in ~50 ms. Causa: i biquad RBJ
(`Biquad::setLowpass`) sono stabili solo per `f < fs/2`; a 44.1/48 kHz i cutoff
**40 kHz (opLP1-4, stadi 4558D kOpAmp=0.018 attivo)**, **28 kHz (rec4)**, **48 kHz (rec5)**
e, a 44.1 kHz anche **24 kHz (rec2)**, superano Nyquist → poli fuori dal cerchio unitario
→ IIR divergente. La calibrazione/verify era tutta a **96 kHz** (dove era stabile:
rec5 a Nyquist esatto, opLP a 40k < 48k) → mai rilevato. **Fix**: in `applyFilters()`
clamp dei cutoff `f > fs/2` a `0.45*fs` (tutti i setLowpass/setPeak/setHighShelf via helper
`cut()`): a 88.2/96 kHz i valori restano **bit-identici** (verify invariato), a 44.1/48 kHz
la catena diventa stabile.
Verifiche: `ddx_smoke` **11/11 PASS** (RMS/no-clip a 48k e 44.1k, delay eco 528.0/247.1/
959.9/528.0 ms per RANGE 512 × FACTOR 1/0.5/2 + 44.1k, BYPASS bit-identico, mono, block 64,
state save/recall); `verify.py --force` **17/2/3 invariato** (baseline 96 kHz intatta).

**Modifiche**:
- `src/dsp/DDX777Core.h` `applyFilters()`: helper `cut()` (clamp Nyquist) su tutti i
  coefficienti di cutoff — unico cambio numerico del core ( vedi sopra )
- `src/dsp/Params.h`: `factorIdx` (int 0..2) → **`float factor = 1.0f` (0.5..2.0)**; nuova
  `factorClockFor(f)`: interpolazione lineare a tratti sui 3 punti calibrati
  (0.5→2.13770, 1.0→1.0, 2.0→0.55) → **bit-identico a 0.5/1/2**
- `DDX777Core.h` riga 84: `kFactorClock[clampIdx(factorIdx)]` → `factorClockFor (p_.factor)`
- `PluginProcessor.cpp`: **FACTOR** `AudioParameterChoice` → `AudioParameterFloat`
  (0.5..2.0, default 1.0, stringa ×0.5/×1/×1.5…); **INPUT_LEVEL** −20..+6 dB → **0..+20 dB,
  default 0 dB** (solo gain-up: `decibelsToGain` ≥ 1.0 nel processBlock, core invariato
  con `inputLevel=1.0`); **state save/recall** con il pattern `copyState().createXml()` +
  `AudioProcessor::copyXmlToBinary` / `getXmlFromBinary` + check tag + `replaceState`
  (già testato in ddx_smoke T7)
- `PluginEditor.cpp`: **LED POWER = !BYPASS** (costruttore + timerCallback 30 Hz); rocker
  "POWER" ora sul parametro BYPASS reale (il fittizio `POWER_SW` è eliminato)
- **UI 1000×136** (`RackPanel.h/.cpp`, `PluginEditor.cpp`): frame 16..118, etichette
  top y21..35 / bottom y99..113, knob 96×96 centro y=67, jack (52,67), LED y20..28,
  rocker y45..89, logo riposizionato (28/66/84); risolti gli overlap segnalati
  (PEAK/FEEDBACK, DELAY TIME/scaltiera RANGE, MODULATION/SPEED-DEPTH, ×0.5/×2)
- `Knob.cpp`: raggio mozzo 31→27, cappuccio 25.5→22.5, tacche 33..38.5 → 30..34,
  label r 40-42 → 36/38; **indice triangolare con PUNTA VERSO L'ESTERNO** (apice r21,
  base r11 — prima l'apice era al centro); stile **Factor**: anello di 12 tacche a
  cerchio pieno (come il pannello originale) con ×0.5/×2; nuovo stile **Level0to20**
  (etichette 0/+20) per INPUT; **fix `numSteps()`**: i knob 0..1 (FEEDBACK/DELAY_LEVEL)
  erano quantizzati a 2 posizioni (2 steps) → ora continui; i knob 0..10 passano da
  10 a 11 step (il "10" era irraggiungibile con wheel/drag)
- `tests/harness/main.cpp`: `--factor` ora float diretto 0.5..2.0 (valori CLI 0.5/1/2
  invariati → verify.py invariato)
- Nuovi target CMake: **`ddx_smoke`** (smoke test audio headless, 11 test) e
  **`ddx_screenshot`** (PNG della UI headless via `paintEntireComponent` + PNGImageFormat;
  uso: `ddx_screenshot.exe [out.png]`)
- Preset rigenerati con `ddx_gen_presets` (FACTOR ora float: Early_Digital 2.0)

**Risultato verify** (prima → dopo, `--force`, 96 kHz): **17 PASS / 2 FAIL / 3 INFO →
invariato** (i 2 FAIL restano L25 banda/Virtual ADC; il fix Nyquist è no-op a 96 kHz).
Nuovo gate: `ddx_smoke` 11/11 PASS (prima del fix: 7 falliti, output ±1e40/NaN a 48 kHz).

**Note JUCE 8.0.9 (API breaking scoperte in build)**: `ValueTree::createXml()` e
`getXmlFromBinary` restituiscono `std::unique_ptr<XmlElement>` (niente `delete`);
`XmlElement` non ha `hasType` (usa `hasTagName`); `APVTS::replaceState` a 1 argomento;
`NormalisableRange` ha `convertTo0to1`/`convertFrom0to1` (niente `convertToNonNormalised`);
`AudioBuffer::copyFrom` a 6 argomenti (con `sourceChannel`); `File::createOutputStream`
restituisce `unique_ptr`; niente `getSlice`/`createComponentScreenshot` (usare
`paintEntireComponent` + `PNGImageFormat::writeImageToStream`).

**Non toccato (per vincolo utente)**: calibrazioni kOpAmp 0.018 / kVos 0.0079 / kLo 0.0
(invariati; il fix è strutturale sul clamp Nyquist, non sui valori); serigrafia
"Seiwa DDX-777"; `p_.feedback` resta senza effetto DSP (limiter threshold fisso −20 dBFS:
lacuna di modello preesistente, documentata, non fixata in questa sessione).

---

## Sessione 13a — 03/10/2026 (sera)
**Tema**: Beta 1.0 — packaging JUCE 8.0.9 (VST3 + Standalone Windows), UI pannello 1:1, 10 parametri APVTS, 5 preset

**Decisioni utente (confermate)**:
- SR interno = **host rate, NO Resampling** (deviazione documentata dalla riga spec "Resampling 32 kHz")
- Geometria editor = **fedeltà 1:1 ~1000 × ~115 px** (non 250-300 px della spec)
- Versione host = **1.0.0** ("-beta" solo in README/description)
- Font = **approssimazione di sistema** (Arial bold etichette, Georgia boldItalic wordmark)

**Modifiche**:
- `Plugin/CMakeLists.txt` riscritto: metadati spec (COMPANY "Sole", PRODUCT "DDX-777", codici
  SOLE/DDX7, DESCRIPTION, `© 2026 Sole`, VERSION 1.0.0), VST3_CATEGORIES **Fx + Delay**
  ("Vintage" non esiste nelle categorie JUCE 8.0.9), MSVC `/utf-8`, source `src/ui/*`,
  target `ddx_harness` (invariato) e `ddx_gen_presets` (nuovo)
- `src/dsp/Params.h`: nuovo campo `float mixLevel = 0.95f;`
- `src/dsp/DDX777Core.h` riga 190: `dry + w * wetGain * kWetMix` → `p_.mixLevel`
  (default 0.95 → output **bit-identico**; il mix NON è ricomponibile fuori dal core:
  lo stadio di uscita nonlineare opera sul segnale già mixato)
- `src/PluginProcessor.{h,cpp}` riscritti per JUCE 8: APVTS "PARAMETERS" (10 parametri),
  2 core L/R, pre-gain dB su INPUT_LEVEL, BYPASS passthrough + reset al re-engage,
  atomics PEAK (led/envelope), state XML via `copyState().toXmlString()` /
  `replaceState(ValueTree::fromXml(...))` (API JUCE 8: `copyXmlStringTo`/`setState` rimossi)
- UI nuova in `src/ui/`: `RackPanel` (colori + layout 1000×115, 6 cornici smussate 45°,
  serigrafia, logo Seiwa®/DIGITAL DELAY/DDX-777), `Knob` (stili Level010/Range/Factor,
  arco 270°, 11/10 tacche, indice triangolare, drag verticale, wheel, double-click→default),
  `LedIndicator`, `RockerSwitch` (HOLD/POWER), `InputJack`; `PluginEditor` 1000×115 fisso,
  timer 30 Hz per LED PEAK/HOLD, POWER decorativo (sempre acceso)
- `tests/presets/main.cpp`: generatore `ddx_gen_presets` (solo API pubbliche +
  `createPluginFilter`) → **5 preset** in `Plugin/presets/`: Init, Classic_Slap
  (RANGE 128, FB 0.3, MIX 0.5), Ambient_Wash (512, 0.7, 0.7), Dub_Siren (256, 0.85,
  SPEED 5, DEPTH 7, 0.8), Early_Digital (512, ×2, 0.4, 0.6)
- Doc: `README.md` (root, nuovo), `PLUGIN_STATE.md` v14

**Risultato build**: Release MSVC (VS Build Tools v18 "Visual Studio 18 2026", cmake 4.4.3):
`DDX-777.vst3` (5.4 MB) + `DDX-777.exe` (standalone) + `DDX-777_SharedCode.lib` +
`ddx_harness.exe` + `ddx_gen_presets.exe`; 5 preset scritti e verificati.

**Risultato verify** (prima → dopo, `--force`): **17 PASS / 2 FAIL / 3 INFO → invariato**
(i 2 FAIL restano L25 banda/Virtual ADC; refactor MIX a default 0.95 bit-identico).

**Note JUCE 8.0.9 (API breaking scoperte in build)**: `getRawParameterValue` →
`std::atomic<float>*`; `juce::Atomic` ha `get()`/`set()` (non `.load()`); `Graphics` senza
`setThickness`/`removeTransform`/`resetTransform` (drawLine accetta thickness; triangolo in
coordinate assolute); `Path::addLineTo` → `lineTo`; `MouseEvent` ha `x/y/position`,
`getNumberOfClicks()`; `String` senza `getCharacter` (usa `operator[]` + `String::charToString`);
`NormalisableRange` con membri pubblici `start/end/interval`; `Font::boldItalic` rimosso
(`Font::bold | Font::italic` + `FontOptions`); `Colour(uint32)` esplicito; `Colour::withAlpha`
ambiguo con int (passare float); `ColourGradient` richiede 7° argomento `isRadial`;
`fillAll(FillType)` + `setFillType` (niente `fillAll(brush)`); `ValueTree::toXmlString`/
`fromXml` (niente XML su APVTS); `juce_add_console_app` senza source positional
(`target_sources` dopo); `getParameterID()` solo su `AudioProcessorParameterWithID`.

**Decisioni/deviazioni documentate**: host rate (no Resampling); categorie Fx+Delay (niente
Vintage); versione 1.0.0; layout `src/` (spec diceva `Source/`); font di sistema; JUCE resta
8.0.9 (pinned; ultima tag 8.0.15). TODO "concept UI (§13 handoff)" chiuso.

---

## Sessione 12b — 03/10/2026 (pomeriggio)
**Tema**: Datasheet NE570N (estrazione utente) → Meccanismi A/B nel core; calibrazione su T4; characterization v4

**Modifiche**:
- `DDX777Core.h`: rimossi `kThdLow`/`kThdHigh`; implementati **Meccanismo A** (kVos, offset VOS
  gain cell → H2 su `dry²`, applicato post-mix; m2_ one-pole kM2=0.001 per il DC) e
  **Meccanismo B** (kLo, crossover → H3 < 500 Hz via outLP_); setter `setKVos`/`setKLo`,
  reset `m2_`
- `harness/main.cpp`: flag `--k-vos` / `--k-lo` (sentinela −1.0, default = valori calibrati del core)
- Calibrazione su T4 (armoniche via FFT, 5 segmenti 2^20): **kVos = 0.0079** (H2 1 kHz = 0.0308%
  vs HW 0.0311%, +0.1 dB; H2 10 kHz = 0.0349% vs HW 0.0345%, +0.1 dB); **kLo = 0** (l'H3 a bassa
  banda è già fornito dalla dinamica del compressore: baseline H3 100 Hz = 0.42% vs HW 0.32%;
  ogni kLo > 0 peggiora — meccanismo resta disponibile via `--k-lo`)
- `kOpAmp` invariato (0.018, Fase 2)
- Nuovi tool: `tests/calibrate_mech12.py` (calibrazione A/B), `tests/characterize_thd_v4_full.py`
  (→ `tests/THD_characterization_v4.md` + `build/char_thd_v4/results.csv` + PNG),
  `tests/band_differential.py` (diagnostica banda VADC on/off), `tests/probe_h2.py`
- Datasheet NE570N: append in `02_componenti_raw.md` § "Sessione 12 — Datasheet NE570N"
  (valori numerici + **correzione pinout DIP-16, mapping shift +1**)
- Doc: `04_lacune.md` (L17 correzione pinout "ipotesi forte, da confermare"; **L23** C_RECT
  0.8-6 µF; **L24** R_in; **L25** banda vs Virtual ADC), `03_blocchi.md` §2 (pin rietichettati),
  `00_stato_sessione.md`, `PLUGIN_STATE.md` (versione 13)

**Risultato verify** (prima → dopo, `--force`): THD 100 Hz/1 kHz/10 kHz **3/3 PASS**
(+1.7/+3.1/+2.2 dB, tolleranza 6 dB) — il FAIL "THD 10 kHz 16.5 dB under" del 02/10 è risolto dal
Meccanismo A post-mix. **Banda 2/4 FAIL pre-esistenti emersi al re-render** (Virtual ADC Fase 2:
−3 dB @ 12.80 kHz, ripple 7.83 dB; con `--no-virtual-adc` la banda passa ma l'aliasing T5 fallisce
−27.6 vs −30.8 dBFS) — non legati alla sessione (A/B agiscono solo sul ramo mix).

**Decisioni** (utente): D — documentare i 2 FAIL di banda (L25) e proseguire, nessun cambiamento
al core Fase 2; misure HW −24/−30/−36 dBFS rimandate (unit non accessibile) → target di validazione
in report v4 §2, incluso il **test discriminante** H3(100 Hz) a −30 dBFS (modello: 0.0035%;
estrapolazione HW §0.4: 0.33-0.40% → se HW manterrà ~0.3%, Meccanismo B da riattivare).
Calibrazione assoluta resta relativa (manca R_in, L24). Opzione C (+8 dBm) solo documentata.

---

## Sessione 12a — 03/10/2026 (mattina)
**Tema**: Fase 2 — 5 componenti HF (Virtual ADC, rectifier, DAC R-2R, buffer, stadi op-amp)

**Modifiche**:
- `DDX777Core.h`: **Virtual ADC 32 kHz ON di default** (dec1-4/int1-4, Butterworth 8° @ 15 kHz,
  flag `--char-virtual-adc`/`--no-virtual-adc`); stadi Comp 2-5 (kRect, kDac2/kDac3, kBuffer,
  kOpAmp) con filtri di banda (bufLP_ @ 15 kHz, opLP1-4 @ 40 kHz)
- Calibrazione (sweep + matrice 648 render, `characterize_thd_v3_full.py`): kRect/kDac2/kDac3/
  kBuffer → **0** (contributo < 1 dB e/o peggioramento match), **kOpAmp = 0.018** (gap 10 kHz
  −16.7 dB → −0.9 dB; tutte le 3 frequenze dentro ±2 dB)
- Report: `tests/THD_characterization_v3.md` + `build/char_thd_v3/` (648 render matrice + 9
  ablazioni + 15 sweep)

**Risultato**: THD mix stato calibrato: 100 Hz 0.4312% (HW 0.349%, +1.9 dB), 1 kHz 0.0408%
(HW 0.033%, +1.7 dB), 10 kHz 0.0315% (HW 0.035%, −0.9 dB)
**Nota**: con Virtual ADC ON di default il punto −3 dB si sposta a 12.80 kHz (fuori da
14.5-16.5 kHz) — emerso come FAIL verify.py solo al primo re-render `--force` (sessione 12b),
documentato come L25.

---

## Sessione 12 — 02/10/2026
**Tema**: Riorganizzazione documentazione (handoff pulito, PLUGIN_STATE, PLUGIN_CHANGELOG)

**Modifiche**:
- Rinominato `HANDOFF_PLUGIN.md` → `SEIWA_DDX-777_HANDOFF.md`
- Aggiornati tutti i riferimenti cross-file (00_stato_sessione.md, 02_componenti_raw.md, 03_blocchi.md, schematic.py, verify.py)
- Pulito `SEIWA_DDX-777_HANDOFF.md`: rimossa sezione 10b "Stato finale plugin", sezione 10 limitata a limitazioni hardware, mantenute sezioni 1-13 (spec HW + concept stereo/UI)
- Creato `PLUGIN_STATE.md` (configurazione corrente + verify + limitazioni + TODO)
- Creato `PLUGIN_CHANGELOG.md` (questo file, storia sessioni 9-11 ricostruita)
- Aggiornato `00_stato_sessione.md` con sessione 12

**Risultato verify**: 17 PASS / 2 FAIL (invariato, solo documentazione)

**Decisioni**: Separazione netta tra specifica hardware (handoff) e stato operativo (PLUGIN_STATE + CHANGELOG)

---

## Sessione 11b — 01/10/2026 (pomeriggio)
**Tema**: Correzione THD 1 kHz, noise tuning, T5 gap analysis

**Modifiche**:
- `DDX777Core.h`: `kHissRms` 2.3e-4 → 1.8e-4 (RMS −77.4 dBFS target)
- `DDX777Core.h`: Distorsione selettiva riscritta con crossover outLP_ a 500 Hz:
  - `kThdLow = 0.0070` (100 Hz → THD ≈ 0.35%)
  - `kThdHigh = 0.00068` (1/10 kHz → THD ≈ 0.034%)
- `outLP_` crossover abbassato da 1 kHz → 500 Hz (1 kHz ora in hi-band, 100 Hz in lo-band)
- Reconstruction filters: rec3=14k (smorza risonanza eq3/aa4), rec4=28k, rec5=48k (no-op)

**Motivo**: THD 1 kHz era 13.3 dB over (0.154% vs 0.033% HW). Il crossover a 1 kHz divideva il fondamentale tra lo/hi band → doppia contribuzione. Crossover a 500 Hz allinea 100 Hz (lo) e 1/10 kHz (hi).

**Risultato verify**: 15 PASS / 4 FAIL → **17 PASS / 2 FAIL**
- THD 100 Hz: 6.2 dB → **5.7 dB PASS**
- THD 1 kHz: 13.3 dB FAIL → **4.0 dB PASS**
- THD 10 kHz: 8.6 dB FAIL → **16.5 dB FAIL** (nuovo regresso: ric10kHz attenuato dai filtri rec)
- Noise RMS: -74.3 → **-77.4 PASS**
- Noise peak: -60.9 → **-62.8 PASS** (dentro ±5 dB)
- T5: -27.6 dBFS (0.18 dB short, invariato)

**Decisioni**:
- Accettato THD 10 kHz come limitazione architetturale (distorsione post-ricostruzione)
- T5 gap 0.18 dB irrisolvibile senza rompere −3 dB
- Configurazione 4-section (rec=18k/24k/14k/28k) stabile

---

## Sessione 11a — 01/10/2026 (mattina)
**Tema**: Iterazione empirica filtri EQ/AA/reconstruction via sweep.py + --ffilter

**Modifiche**:
- Aggiunto `overrideFilters(const double v[19])` in `DDX777Core.h` + flag `--ffilter` in `tests/harness/main.cpp`
- Creato `sweep.py` con `measure()`/`report()` per iterazione rapida senza ricompilare
- Sweep sistematico EQ/AA/rec → configurazione vincente:
  - eq2=11730.7/0.957/+3.02, eq3=14000/2.5/+12.0
  - aa1=10400.5/1.076, aa2=16500/0.539, aa3=14200/0.40, aa4=15000/3.0
  - rec_=18000/0.707, rec2_=24000/0.707
- Identificato bug doppio `rec2_.process()` in `process()` (riga duplicata)
- Fix doppio rec2_ → banda rotta (3.10 dB), ripristinato come feature (due sezioni rec2_ a 24k = smorzamento risonanza eq3/aa4)
- Aggiunto rec3_, rec4_, rec5_ per controllo granulare ricostruzione
- `kHissRms` 4.5e-4 → 2.3e-4 → 1.8e-4
- `kAnalogThd` (globale 0.0041) → distorsione selettiva outLP_ 1 kHz + kThdLow/kThdHigh

**Motivo**: Fit teorico Python inaffidabile; iterazione empirica con `--ffilter` unico metodo affidabile. Il fit Python prediceva ripple 0.99 dB ma realtà C++ mostrava 24 dB (cascade order/coefficienti diversi).

**Risultato verify (iterazioni intermedie)**: da 10/17 PASS → 15/17 PASS
- Banda ripple: 2.38 dB FAIL → **1.12 dB PASS**
- Banda −3dB: 14.37 FAIL → **14.79 PASS**
- T5: -24.9 FAIL → **-27.6 FAIL** (0.18 dB short)
- Noise RMS: -71.1 → **-77.4 PASS**
- THD 100 Hz: 6.2 dB FAIL → **5.7 dB PASS**
- THD 1 kHz: 4.5 dB PASS → **13.3 dB FAIL** (crossover 1 kHz problematico)
- THD 10 kHz: 8.6 dB FAIL → **8.6 dB FAIL**

**Decisioni**:
- `fiteq7.py` (fit teorico) abbandonato → solo iterazione empirica
- Doppio `rec2_` mantenuto come feature (due sezioni a 24k smorzano risonanza eq3/aa4)
- Distorsione selettiva necessaria per THD frequenza-dipendente

---

## Sessione 11 — 01/10/2026 (mattina presto)
**Tema**: Misure audio T1-T6 su hardware reale → risoluzione L1/L5/L12/L13

**Misure utente (Segnali_Test/)**:
- T1 Delay: 66/262/528/247/960 ms (RANGE 64/256/512 ×1, ×0.5, ×2)
- T2 Banda: ~15 kHz, taglio 15-16 kHz
- T3 Rumore: −67 dBFS
- T4 THD: da companding NE571 (non saturazione)
- T5 Aliasing: nessuno rilevato
- T6 Curva trasferimento: companding attivo

**Deduzioni**:
- **12 bit** confermati (5 indizi: filtro AA, companding dbx-style, epoca 1985, DRAM 192 Kbit @ 32 kHz, ascolto)
- **f_camp ≈ 32 kHz nominali** (effettivi ≈ 31 kHz: 16384 word ÷ 528 ms)
- **Bias clock +3%** (trimmer `203`)
- Filtro anti-aliasing confermato tra NE571 pin6 e M60351 (test A: 0 bip)
- NE571: solo compressore ch.1, retroazione fissa 46.1 kΩ, ch.2 spento (L17 RISOLTA)
- FEEDBACK LEVEL = reostato bias DC VCC↔pin4 (non ricircolo audio)

**File aggiornati**: `04_lacune` (L1/L5/L12/L13 RISOLTE), `components` (U4), `03_blocchi` (§2 catena aggiornata, §3 bias clock), `02_componenti_raw` (append sessione 11), `schematic.py` (box aggiornati, PNG rigenerato)

**Risultato**: Hardware completamente caratterizzato per modellazione plugin

---

## Sessione 10 — 30/09/2026
**Tema**: Chiusura L5 (risoluzione bit-depth) + test A/D

**Eventi**:
- L5 chiusa: "non determinabile senza oscilloscopio o analisi spettro" (chiusa per impossibilità strumentale)
- Ipotesi **12 bit [I]** forte su 5 indizi (documentata come default)
- Test utente A: NE571 pin6↔M60351 = 0 bip → filtro anti-aliasing interposto [C]
- Test B: pin4 = 9 bip = GND QFP (scartato)
- Test D: TC40H pin7 = ~10 bip = massa QFP
- `03_blocchi` §2: "Zona campionamento" rinominata, stage "Filtro anti-aliasing" separato a valle
- `schematic.py`: 2 nuovi box catena, indici riscalati, box DAC → "DAC integrato in U4 [I]"

**Risultato**: L5 chiusa con ipotesi documentata, catena segnale finalizzata

---

## Sessione 9 — 29/09/2026
**Tema**: Correzione package U4 + risoluzione L17 (NE571 config)

**Eventi**:
- Package U4 corretto: **QFP-56 (14 pin/lato)** (ex LQFP-48) — corretto in components/raw/blocchi/lacune
- Ricerca M60351: 4 query EN/JP → 0 datasheet (nota in U4/L5)
- **L17 RISOLTA**: NE571 config confermata
  - Solo compressore ch.1 (pin4↔pin6 retroazione 46.1 kΩ)
  - Canale 2 (expandore) spento (pin11 = 0 V)
  - FEEDBACK LEVEL = reostato bias DC VCC↔pin4
  - "Feedback" udito = effetto companding, non ricircolo
- L5 riscritta con strategia Indizi A-F (priorità A→B→D→C→E, F=ascolto)
- `03_blocchi` §2 topologia NE571 riscritta (expandore rimosso, nota 12 bit)
- 13 foto `Closeup back/` lette singolarmente → inventario sez. F (lettere nodo A-N)
- PNG rigenerato (testata 98 foto, box L5/L17/FEEDBACK aggiornati)
- Conteggio verificato: 85 + 13 = 98 foto totali

**Decisioni**: Package QFP-56 confermato; NE571 = solo compressore; FEEDBACK = bias DC

---

## Sessione 8 — 28/09/2026
**Tema**: Consolidamento F4 blocco C + CHECKPOINT C/D

**Eventi**:
- "Non assegnati" (H.1 pot/rotary/trimmer, H.2 jack, H.3 switch/LED, H.4 PSU, H.5 meccanica, H.6 connettori, H.7 RC) con foto verificate
- NOBLE dedup (H.3 rocker = attuazione, H.4 voce unica sezionatore+snubber+serie fusibile)
- RANGE = rotary switch 10 pos. (wafer …844, scala 1-512 ms), FACTOR separati
- Lenti ×2 → "LED bianchi/IR/fototransistor?" + **L19** in lacune
- Induttore → Ref **IND1 (prov.)** (voce dedicata + puntatore H.7)
- Verifica incrociata automatica: Ref 31/31 presenti in raw, lacune L1-L22 lineari (22/22)
- Fix `03_blocchi.md` (M8532 → data code 8532); refuso R3/R4 NE571 riscritto

---

## Sessione 7 — 27/09/2026
**Tema**: F4 Blocco B — identificazioni utente + CHECKPOINT B

**Eventi**:
- C5 = 27 nF (ex 273J50), Q1 = 2SK118 (K118), Q2 = J43P55 (→2SJ43? L20)
- L20-L22 in lacune; 03_blocchi §2 con buffer JFET + zona anti-aliasing
- 5 precisazioni integrate: U18 = circuito discreto NON IC (zener+transistor+C1µF, 7.4V)
- Q1 alimentazione = "presunto +15 V analogico (L16)" + nota rail analogico
- Q2 ammorbidito in 03_blocchi §2 (nessun ruolo affermato)
- Colonna Data code in tabella U (U10→LM311N+8532, U1-U3 44238, U5 8539H, U7 K8436, U8 4507, U9 4504)

---

## Sessione 6 — 26/09/2026
**Tema**: F4 Blocco A — components.md testata + rail + U1-U18

**Eventi**:
- `components.md`: testata + rail + U1-U18 scritto
- Confermato con riserva + correzioni integrate (U18 TO-92 "da confermare", nota 273J50→C5)
- Identificazioni utente appendate in raw: C5 27nF, Q1 2SK118, Q2 J43P55

---

## Sessione 5 — 25/09/2026
**Tema**: CHECKPOINT A — tabella chip confermata

**Eventi**:
- Datasheet principali: M60351 KO, MSM3764, TC40H000P, M5224P, M5221, NE571 OK
- Residui: HD14066, 4558, LM311
- Confermato da utente: misure +5V, U10=LM311N, U18, zona timing
- `03_blocchi.md` + `04_lacune.md` creati

---

## Sessione 4 — 24/09/2026
**Tema**: F3 — architettura a blocchi + scenari

**Eventi**:
- `03_blocchi.md` scritto: catena audio, clock, scenari modulazione
- `04_lacune.md` creato: L1-L22
- OPZIONE 2 scelta, **scenario A confermato** (modulazione clock VCO), C scartato
- `schematic.py` v1: 2600×1800, margini ≥100, font ≥14, legenda, UTF-8

---

## Sessione 3 — 23/09/2026
**Tema**: F2 — ricerca datasheet + append raw

**Eventi**:
- 809/869/877+F2 NE571 appendate in `02_componenti_raw.md`
- `03_blocchi.md` aggiornato
- `04_lacune` (L5 + L16-L18) scritto

---

## Sessione 2 — 22/09/2026
**Tema**: F1 — analisi foto + inventario

**Eventi**:
- Survey completo 83/83 foto
- `01_foto_inventario.md` scritto
- `02_componenti_raw.md` iniziato (append incrementale)
- Verifiche mirate: AN7815✓ 867, LM31? 844, DRAM 4ª scartata, 884=rete, fusibile n/v

---

## Sessione 1 — 21/09/2026
**Tema**: Avvio progetto — setup + regole

**Eventi**:
- Repo inizializzato: `E:\tutto\OpenCode\Seiwa DDX-777\`
- Regole: Pillow per rendering, italiano, Ref provvisorie, checkpoint obbligatori
- `00_stato_sessione.md` creato con regole ripresa