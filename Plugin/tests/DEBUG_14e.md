# DEBUG 14-e — fix redistribuzione spazio, switch, resize fluido (R1-R6)

Sessione 14-e: throttling resize, PEAK -8px, FEEDBACK ricentrato, corona
RANGE r41 + DELAY TIME centrato, logo centrato, switch ridisegnati.
Nessun cambio DSP/verify.py/logica stereo.

## Fix

### R1 — Resize fluido con throttle 33ms (ResizeGrip.h/.cpp, PluginEditor.cpp)
- Problema: `setSize` chiamato a ogni evento mouse -> resized()+paint() del
  pannello intero a ogni evento (lag JUCE noto).
- `ResizeGrip` ora e' un `juce::Timer` (33 ms ~30fps):
  - `mouseDrag`: salva `pendingS` (continuo 0.5..2.0), avvia timer se fermo.
    NESSUN setSize qui.
  - `timerCallback`: unico punto di applicazione durante il drag:
    `applyScaleToWindow(pendingS)` (finestra fluida) + `commitParam(pendingS)`
    (param APVTS step 0.05 aggiornato con valore stabilizzato; JUCE quantizza
    internamente -> l'host non vede rumore da ogni evento).
  - `mouseUp`: stopTimer, snap finale della finestra alla griglia del param.
- Editor `timerCallback`: durante il drag (`resizeGrip.isBeingDragged()`) NON
  esegue la size-sync da UI_SCALE (evita conflitti); LED/switch restano
  sincronizzati.
- Nota UI_SCALE: il param APVTS ha step 0.05 (`NormalisableRange(0.5,2.0,0.05)`):
  non e' matematicamente continuo; la finestra e' fluida durante il drag,
  il param e' quantizzato a griglia 0.05 e la finestra snap-a al rilascio.
- N/A: ComponentBoundsConstrainer (finestra min=max, non ridimensionabile dai
  bordi), OpenGL (nessun context nel progetto).

### R2 — PEAK -8px (RackPanel.h)
- `peakX` 178->**170**, `peakLedX` 211->**203** (LED segue, asse+33).
- La hitbox della label INPUT NON e' il vincolo (confermato: `labelArea`
  finisce a x115; inchiostro PEAK "0" a x139, jack a x96, titolo a x85 ->
  gap >= 43px). `InputJack` intatto (kProjectW=119 invariato).

### R3 — FEEDBACK ricentrato (RackPanel.h, opzione A)
- `fbX` 274->**280** = centro sezione (235+325)/2. Nessuna divisoria mossa.
- Check: "0" ink ~248..254 (13px da x235), "10" ~306..312 (13px da x325),
  titolo "FEED BACK" gia' centrato sulla sezione.

### R4 — Corona RANGE r41 + DELAY TIME centrato (Knob.cpp, RackPanel.cpp)
- Range labels r45->**r41** = stessa distanza label-tacca del FACTOR (tacche
  identiche r27..34 -> offset identico; risolve anche il punto 5 della spec).
  Check: "512" ink y95..107, "RANGE mS" y117..124 -> **gap 10px** (a r45 si
  sovrapponeva). Stato 14c/14-ter verificato.
- Titolo DELAY TIME: right-aligned -> **centrato sul box sezione** (centro
  501, ink ~460..542), stato 14-ter. NON su FACTOR (552): l'ink arriverebbe
  a ~593, oltre la divisoria 588. `drawTrackedRight` rimossa (inutilizzata).
- Check "16" (corona, y34+) vs titolo "D" (y22..30): 3-4px verticali, nessuna
  sovrapposizione.

### R5 — Blocco logo centrato (RackPanel.cpp)
- `logoCX` 900->**881** = (mdX1 812 + bordo sx POWER 950)/2. Tutte le righe:
  "Seiwa" (+®), "DIGITAL DELAY" (rect 826..936), "DDX-777", neon "STEREO"
  (`kNeonX` 835->816). Gap divisoria MODULATION->Seiwa: 833-812 = 21px.
- Check: ® a ~937..949, rocker POWER 950..994 ma verticalmente separato
  (® y38..50, rocker y53+).

### R6 — Switch ridisegnati (RockerSwitch.h/.cpp, PluginEditor.cpp)
- Geometria: POWER **44x44** bounds S(950,53,44,44) (progetto 44x44); HOLD
  **22x44** bounds S(602,53,22,44). Enum Style rimosso: un solo percorso che
  disegna l'intero bounds. LED invariati (972/613 = centri).
- Paint: ombra esterna UNIFORME nero alpha150 (translated -1.5/+2.5, nessuna
  luce sull'ombra); corpo kRockerLo off / kRockerHi on (graphite, pressed
  invariato), affondo +2y premuto; highlight top caldo #FFF0D8 alpha40/20 sul
  solo corpo; bordo **#808080** 1.2px; **no laterali** (faccia laterale scura
  rimossa, 14d era: darker 0.55 sul lato sinistro).
- `setPaintingIsUnclipped(true)` in ctor: l'ombra esce dai bounds esatti del
  componente (altrimenti tagliata dal clipping).

## Verifiche (PNG ddx14e_final.png + probe PIL + crop)
- R2: PEAK "0" ink 139..149; jack gray a 96; titolo INPUT (rosso stereo) a
  85; gap 43px (>=36). LED blob c(202,26)~(203,27).
- R3: "0"/"10" FEEDBACK 13px dalle divisorie; titolo centro 284 (box 280,
  asimmetria glyph).
- R4: "512" vs "RANGE mS" gap 10px; DELAY TIME ink 460..542 (centro ~501);
  "16" 3-4px sotto la "D".
- R5: Seiwa ink 833..936 (centro 884); neon STEREO red 811..950 (centro 880);
  DIGITAL DELAY centro 881; ® vs POWER: separazione verticale.
- R6: POWER body 952..991 (bounds 950..994, border #808080 antialias su
  950-951), ombra 81px sotto il corpo; HOLD body+ombra centrato 613; LED
  HOLD c(612,26), POWER c(971,35). Crop: cube/parallelepipedo con highlight,
  border grigio, ombra basso-sinistra; junction ∨/Λ visibili ai lati HOLD.

## Verify (invariato)
- `python tests\verify.py --force` -> **19 PASS, 6 FAIL, 7 INFO** = baseline.

## Deploy
- UAC a Reaper chiuso; MD5 build == installato ==
  **58969CD8BD59F63D9A986485FAB15EAE** (2026-10-09T21:01:37+02:00).

## Deviazioni / note
- UI_SCALE: param a step 0.05 (non continuo); finestra fluida durante il drag
  (timer 33ms), param quantizzato, snap finale. Confermato con l'utente.
- DELAY TIME centrato su SEZIONE (501), non su FACTOR (552): centrare su
  FACTOR collide con la divisoria 588. Confermato con l'utente.
- FEEDBACK: opzione A (solo ricentro) scelta dall'utente (B/C avevano
  collisioni o cascade sulle divisorie).
- Warning build pre-esistenti non toccati: C4244 RackPanel.cpp (drawImageAt
  float->int), C4189 DDX777Core.h:101 hold.
