# DEBUG 14-g — switch senza ombre, DT sopra FACTOR, POWER 36x36, resize single-source

Sessione 14-g (fix post-14f, piano G1-G5 approvato con correzioni).
Nessun cambio DSP/verify.py/logica stereo. HEAD precedente: 73652d7 (14f).

## Fix

### G1 — RockerSwitch: ombra esterna rimossa integralmente (RockerSwitch.cpp)
- Problema: l'ombra (nero α150, traslata −1.5/+2.5) clippava contro
  l'item durante le interazioni, diventando un artefatto.
- Fix: blocco castShadow cancellato. Il paint contiene SOLO corpo pieno
  kRockerLo/Hi (+ sink premuto +2y, invariato) + bordo #808080 1.2px.
  (L'highlight interno era già rimosso in 14f.)
- `setPaintingIsUnclipped(true)` resta: non serve più all'ombra ma alla
  faccia premuta (body translated(0,+2) sporge 1px sotto i bounds).
- Check: crop 3x POWER/HOLD — nessun pixel scuro fuori dal corpo; se
  mancasse la profondità → fix separato con gradiente interno (mai ombra).

### G2 — DELAY TIME centrata su FACTOR, tracking 1.0 (RackPanel.cpp)
- drawTrackedRight (reintrodotta in 14f) con tracking 1.0 (era 2.0) e
  area destra = factorX + inkWidth/2 → centro dell'ink esattamente su
  factorX = 536.
- Check PIL: ink 500..573, mid **536.5**; destra 573 ≤ dtX1−7 = 581;
  "32" RANGE (452..478) dista **22px**.

### G3 — HOLD: nessun cambio (verifica obbligatoria, confermata)
- knobLabel centra già su cx; holdSwX = 613.
- Probe PIL su PNG intermedio e finale: ink **594..630, mid 612.0**,
  margini **L6/R8** dentro 588..638. Confermato → nessun tocco al codice.

### G4 — POWER 36x36, asse x972 invariato (RackPanel.h, PluginEditor.cpp)
- 44x44 → 36x36 (−4px per lato): powerSwitch costruito con projectW/H
  36x36; bounds S(954, 53, 36, 36); powerSwX/powerLedX/label restano 972.
- NOTA: il powerCx=908 della spec (816+1000/2) cadeva SOPO il logo
  ("Seiwa" 833..936 y36..69 e "DIGITAL DELAY" ~826..936 y75..89):
  overlap documentato con probe. Scelta utente: **opzione B — solo
  ridimensionare, asse 972 invariato**.
- Check: body 956..987 y57..88 (32x32 con reduced+sink), dentro 954..990;
  LED blob ~972; label POWER invariata 947..995; gap switch→® ~4px
  (verticalmente separati); nessuna collisione col logo.
- Check intermedio obbligatorio (richiesto dall'utente): PNG ddx14g_mid
  generato e probe-ato DOPO G4 e PRIMA di G5 (layout stabile).

### G5 — Resize: fonte di verita' unica, limits fuori dal drag
(ResizeGrip.cpp/.h, PluginEditor.cpp)
- Problema: durante il drag, `setResizeLimits` veniva ricalcolato a ogni
  tick (33ms) — alcuni host re-impongono la propria size memorizzata quando
  i limiti cambiano = il "salto alla versione grande".
- Fix:
  - `applyScaleToWindow` fa SOLO setSize+repaint (con guard); niente
    setResizeLimits.
  - `timerCallback`: applyScaleToWindow + commitParam (invariato, 14f).
  - `mouseUp`: commitParam(pendingS) → **setResizeLimits una tantum** →
    **setSize esplicito finale** con l'ultimo pendingS → repaint singolo.
  - mouseDrag resta solo pendingS (invariato); editor timerCallback resta
    guardato da isBeingDragged(); resized() non chiama setSize; nessun
    param listener (polling 30Hz).
- Verifica log: contatore DBG-only (`#if JUCE_DEBUG`) `setSizeDuringDrag_`
  resettato a mouseDown, incrementato a ogni setSize applicato, stampato a
  mouseUp: atteso ≤ ~30 durante un drag di 1s in Reaper (DebugView).
  (L'harness screenshot non simula drag.)

## Verifiche (ddx14g_mid.png + ddx14g_final.png, probe PIL + crop 3x)
- Intermedio (post-G4): 11/11 PASS. Finale: **10/10 PASS**, incluse le
  regressioni (divisorie 215/305/394/588/638, gap PEAK).
- G1: nessun pixel <(18,18,20) sotto POWER (y91..101) e HOLD (y98..108);
  colonna x972 uniforme corpo/bordo.
- Crop: POWER cubo 36x36 uniforme senza ombra; campo destro logo+POWER
  senza sovrapposizioni; DELAY TIME sopra FACTOR a tr1.0.

## Verify (invariato)
- `python tests\verify.py --force` → **19 PASS, 6 FAIL, 7 INFO** = baseline.

## Deploy
- UAC a Reaper chiuso; MD5 build == installato ==
  **ECB52D5850D784A68E46372A16681362** (2026-10-09T23:05:19+02:00).

## Deviazioni / note
- G4: powerCx=908 (spec) scartato per collisione col logo; opzione B
  (972) scelta dall'utente via question tool.
- G3: probe PIL richiesto e confermato (594..630, mid 612, L6/R8) →
  nessuna modifica.
- Warning build pre-esistenti non toccati: C4244 RackPanel.cpp
  (drawImageAt float->int), C4189 DDX777Core.h:101 hold.
