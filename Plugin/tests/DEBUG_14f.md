# DEBUG 14-f — switch pulito, riequilibrio sezioni, DT right-align, SPEED/DEPTH centrati, UI_SCALE continuo

Sessione 14-f (fix post-14e, piano R1-R6 approvato con 6 correzioni).
Nessun cambio DSP/verify.py/logica stereo. HEAD precedente: 16533f0 (14e).

## Fix

### F1 — RockerSwitch: highlight interno rimosso (RockerSwitch.cpp)
- Problema: il `fillRoundedRectangle` highlight (#FFF0D8 α20/α40) rendeva
  visibile un "rettangolo grigio interno" nel corpo: probe pixel col x=972
  (POWER ON) = fascia (73,75,80) per y57..67 su corpo (58,61,68); col x=613
  (HOLD OFF) = fascia (53,52,50) su (16,17,19).
- Fix: righe 43-48 cancellate. Restano solo (check 14f): (a) ombra esterna
  uniforme nero α150 offset (−1.5,+2.5); (b) corpo pieno kRockerLo/Hi;
  (c) bordo #808080 1.2px. Se mancherà il glint si rivaluta con gradiente
  lineare sul solo corpo (mai fill pieno).

### F2 — Riequilibrio sezioni INPUT/FB/DELAY/DT (RackPanel.h)
- INPUT si stringe di 20px: `inX1`/`fbX0` 235→215; FB e DELAY traslano
  (larghezze invariate): `fbX1`/`dlX0` 325→305, `dlX1`/`dtX0` 414→394.
  `dtX1`/`hdX0` 588, `hdX1`/`mdX0` 638, `mdX1` 812 invariati.
- Assi: `fbX` 280→260, `dlX` 369→350 (centro 349.5); `peakX` 170 invariato
  → gap_PEAK = 215−170 = 45 = gap_FEEDBACK (260−215).
- RANGE/FACTOR ricentrati sul nuovo box DT (394..588, centro 491) con
  spread invariato 90: `rangeX` 462→446, `factorX` 552→536. NOTA: lo spread
  70 proposto (~467/537) collideva (label "0..10" a r41 si sovrappongono di
  ~6px); spread 90 con 14px di garanzia da entrambe le divisorie.
- DELAY TIME guadagna +20px a sinistra (box 174→194px).

### F3 — DELAY TIME right-align a dtTitleX1−7 (RackPanel.h/.cpp)
- `drawTrackedRight` reintrodotta (rimossa in 14e): specchio di
  drawTrackedCentred con x = area.getRight() − trackedWidth.
- Titolo: ink di destra a 588−7 = **581** (misura di riferimento: label
  FEED BACK ha ink destro a ~318 vs bordo 325 = 7px). `dtTitleX0` 414→394.
- Check PIL: ink reale 498..580 (gap 8px da 588); "32" RANGE a x452..478
  → 20px dall'ink sinistro del titolo, nessuna collisione.

### F4 — SPEED/DEPTH simmetrici su mdCx (RackPanel.h)
- mdX0..mdX1 = 638..812 → mdCx = **725**. Passo p=76: `speedX` 692→**687**,
  `depthX` 770→**763**. (687+763)/2 = 725 esatto.
- Check PIL: label "SPEED" ink 665..708 (mid 686.5), "DEPTH" 740..784
  (mid 762); label corona "0" a x658 (11px da divisoria 638), "10" a 792
  (11px da 812).

### F5a — UI_SCALE continuo (PluginProcessor.cpp)
- `NormalisableRange<float>(0.5f, 2.0f, 0.05f)` → `(0.5f, 2.0f)` (interval
  0 = continuo). Grep residui: nessun altro intervallo per UI_SCALE;
  readUiScale/commitParam già jlimit 0.5..2; StringFromValue arrotonda al
  % intero per il display (es. 0.873 → "87 %"). Drag via DAW produce valori
  arbitrari. I preset salvati con multipli di 0.05 si caricano normalmente.

### F5b — Resize: guard anti-ridondante + buffer (ResizeGrip.cpp/.h, RackPanel.cpp)
- `applyScaleToWindow`: guard `if (w == ed->getWidth() && h == ed->getHeight())
  return;` — setSize/setResizeLimits/repaint solo se la size è nuova.
  Copre sia il timer (33ms) sia mouseUp: ≤1 resized()/tick, zero se stabile.
- `mouseUp`: snap finale a `pendingS` ESATTO (non al param, che potrebbe
  essere stale dell'ultimo tick); singolo setSize, senza timer.
- `commitParam`: commenti aggiornati (param continuo, nessuna quantizza-
  zione 0.05). `mouseDrag` resta solo pendingS (già 14e).
- RackPanel ctor: `setBufferedToImage(true)` — sfondo+cornici+serigrafia
  statici cachati; `setStereoOn` re-rendera il buffer su repaint. Knob/LED/
  switch restano non-buffered (dinamici).

## Verifiche (PNG ddx14f_final.png + probe PIL + crop 3×)
- F1: col x=972 y58..95 uniforme (58,61,68); col x=613 y56..93 uniforme
  (16,17,19); bordi/ombra presenti (100,101,104)/(10,11,12).
- F2: divisorie a 215/305/394/588/638 (scan y45); "512"↔"×0.5" gap 17px;
  midpoint RANGE/FACTOR = 491.2; PEAK titolo mid 170.5, fine 188 (27px da
  divisoria 215).
- F3: DT ink 498..580, gap 8px da 588; "32"↔titolo 20px.
- F4: midpoint SPEED/DEPTH = 724.25 ≈ 725.
- Crop: POWER cube uniforme (no blocco interno), HOLD idem; DT right-align
  con bowtie; MODULATION simmetrico; FB/DELAY label entro sezioni.

## Verify (invariato)
- `python tests\verify.py --force` → **19 PASS, 6 FAIL, 7 INFO** = baseline.

## Deploy
- UAC a Reaper chiuso; MD5 build == installato ==
  **A45E0B3B57E4DD810B129CF8FDB52EB9** (2026-10-09T22:05:07+02:00).

## Deviazioni / note
- Le 6 correzioni allo spec (convalidate dall'utente): dtX1 588 (non 578),
  dlX 350, RANGE/FACTOR 446/536 (spread 90, non 467/537 con spread 70),
  SPEED/DEPTH 687/763 (mdCx 725, non 695), UI_SCALE via NormalisableRange
  interval 0 (non .withRange su attributi), highlight rimosso per check
  (lista "lasciare solo" contraddiceva azione+check — vince il check).
- mouseUp usa pendingS (non il param) per lo snap finale.
- Warning build pre-esistenti non toccati: C4244 RackPanel.cpp (drawImageAt
  float->int), C4189 DDX777Core.h:101 hold.
