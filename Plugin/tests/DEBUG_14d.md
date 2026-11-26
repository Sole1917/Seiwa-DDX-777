# DEBUG 14-quater — 8 fix GUI + resize grip (F1-F8)

Sessione 14-quater: spazio INPUT→PEAK, margini cornice, rimozione base
triangoli divisori, DELAY TIME + corona RANGE, LED, resize grip→UI_SCALE,
rocker ridisegnato, risoluzione pot. Nessun cambio DSP/verify.py/logica stereo.

## Fix

### F1 — Shift Δ=30px + gerarchia disegno (RackPanel.h/.cpp)
- `Layout`: inX1 265→235; fb/dl/dt/hd/md box e assi knob tutti −30;
  dtTitleX0/X1 414/588; peakLedX 238→211; holdLedX/holdSwX 643→613;
  mdX1 842→812. INPUT block (jack, titolo, −20dB) fermo.
- `paint()` riordinato: sfondo → titoli/label/logo/neon → cornice+divisorie
  per ultime (bounds topmost). Assets (knob, jack, LED, rocker) restano
  child del sopra RackPanel: nessuna collisione (verificata su PNG).

### F2 — Margini cornice (RackPanel.h)
- frameTop 14→11, frameBottom 136→139 (h128, margini 11, centro 75=knobCY).
- bottomLabelY 113→114.

### F3 — Rimozione base triangoli divisori (RackPanel.cpp)
- La "base" percepita = segmento di cornice orizzontale tra i piedi delle
  diagonali del bowtie (pixel-verified su PNG precedente: frame continuo a
  y13-14 tra x256..274 chiudeva ∨/Λ in triangoli).
- `drawFrame` ora spezza i rail superiore/inferiore alle 5 giunzioni
  (fbX0/dlX0/dtX0/hdX0/mdX0): gap 2*chamfer = 18 px. Piedi diagonali a
  (jx±9, ft/fb) coincidono con le estremità dei segmenti → ∨/Λ aperti.
- Lati verticali + chamfer angoli esterni invariati (cornice comunque
  continua sui lati).

### F4 — DELAY TIME right-aligned + corona r45 (RackPanel.cpp, Knob.cpp)
- Nuova `drawTrackedRight` (ddxui): titolo allineato a destra nel box DT,
  fine ink a dtTitleX1−12 = 576 (ink ~492..574, 12 px di garanzia dalla
  divisoria 588, ~10 px dalla corona "32" a r45).
- Range labels `drawLabel(..., 41.0, ...)` → **45.0** (Knob.cpp:205).
  0/10 e ×0.5/×2 restano r41.

### F5 — LED (RackPanel.h)
- peakLedX 238→**211** (238+3 F5 −30 F1): centro 211, probe pixel (209-212,25-28).
- powerLed: `ledY` 28→**32** (centro 36): probe (969-974,33-38).
- holdLed 643→613 (solo F1): probe (611-614,25-28).

### F6 — Resize grip (ResizeGrip.h/.cpp, PluginEditor.h/.cpp)
- Nuovo componente `ResizeGrip` child dell'editor: triangolo `__/` in
  (980,130)-(1000,130)-(1000,150) di progetto; fill kSilk α40 (α200 hover).
- Cursore `juce::MouseCursor::BottomRightCornerResizeCursor` (JUCE enum
  BottomRightCornerResizeCursor, juce_MouseCursor.h:79).
- mouseDrag: `s = jlimit(0.5, 2.0, startS + (dx+dy)/600)` →
  `scaleParam.setValueNotifyingHost` + `ed->setSize(kW*s, kH*s)` + repaint.
  mouseUp: valore mantenuto. `setResizeLimits` min=max aggiornato da
  resized() del parent.
- Bounds editor: S(980,130,20,20).
- CMakeLists.txt: aggiunto `src/ui/ResizeGrip.cpp`.

### F7 — Rocker ridisegnato (RockerSwitch.h/.cpp, PluginEditor.cpp)
- Enum `Style { Cube, Slim }`: POWER=Cube (30×44), HOLD=Slim (hit 20×44,
  visuale 11×44 = h/4, centrato).
- Bounds editor: holdSwitch S(holdSwX−10, 53, 20, 44);
  powerSwitch S(powerSwX−15, 53, 30, 44) (era y56 h38).
- Paint: luce calda alto-destra → ombra di proiezione basso-sinistra
  (castShadow translated (−1.5,+2.5), α130 Cube / α110 Slim); faccia
  laterale sinistra scura (darker 0.55); highlight top caldo #FFF0D8 α40
  rilasciato / α20 premuto; corpo kRockerLo/kRockerHi (pressed invariato);
  pressione: body translated +2y; bordo kRockerEdge 1.2.

### F8 — Risoluzione pot (PluginProcessor.cpp, Knob.cpp)
- INPUT_LEVEL: `NormalisableRange (0,10,1.0)` → `(0,10)` (solo interval;
  matematica knob→dB in makeCoreParams invariata → verify.py invariato).
- `mouseWheelMove`: fallback continuo `0.05f` → `0.0125f` (1 tacca = 8
  click, x4). numSteps: INPUT 11→1000 automatico (rilevamento interval);
  RANGE resta 10 (choice, unico a scatti). Drag resta continuo.

## Verifiche (PNG ddx14d_final.png + probe PIL)
- F2: frame y10-11 / y138-139 (stroke 1.6 su y=11/139), edge x10-11 / x811-812.
- F3: rail gap a tutte le 5 giunzioni (y10-11 e y138-139 vuoti tra i piedi
  diagonali); ∨/Λ aperti, nessuna base orizzontale.
- F4: DELAY TIME ink 492..574 (target ≤576); corona RANGE completa a r45
  (1,2,4,8,16,32,64,128,256,512).
- F5: LED blob peak (209-212,25-28), hold (611-614,25-28), power ON
  (969-974,33-38).
- F6: grip pixel in (985..1000, 133..148); triangolo `__/` visibile in crop.
- F7: POWER body y56..98 (h44); HOLD slim visuale ~11 px centrato 613;
  highlight/laterale/ombra verificati in crop.
- Label knob tutte presenti a y114..128: LEVEL×3, RANGE mS, FACTOR, HOLD,
  SPEED, DEPTH, POWER.
- Neon STEREO attivo (screenshot stereo): 134 pixel rossi in zona neon.

## Verify (invariato)
- `python tests\verify.py --force` → **19 PASS, 6 FAIL, 7 INFO** = baseline.

## Deploy
- UAC a Reaper chiuso; MD5 build == installato ==
  **3741E2E8F8253A4F6FC1DC8C80018A64** (2026-10-09T19:46:37+02:00).

## Deviazioni / note
- Nessuna. Le assunzioni (a) campo destro solo respiro, (b) F3 = spezzare
  cornice alle giunzioni, (c) F5 PEAK +3 sul valore reale 238 sono state
  confermate dall'utente prima dell'implementazione.
- Warning build pre-esistenti non toccati: C4244 RackPanel.cpp:249/251
  (drawImageAt float→int, era :217 in 14-ter), C4189 DDX777Core.h:101 hold.
