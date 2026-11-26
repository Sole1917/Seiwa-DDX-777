# Sessione 14-bis — Refit serigrafia (scala UI fluida, box uniti, margini, centrature)

Pre: HEAD `7c7461e` (sessione 14 completa). Vincoli: NON toccare pot, DSP, verify.py, logica stereo.
Ordine esecutivo: read-only + conferma utente → F1-F9 → unico PNG headless 1× → deploy UAC → commit unico.

## Fase read-only (confermata dall'utente)
- Geometria attuale: 6 cornici separate, gap 13-14 px; frameTop/Bottom **già 14/136** (F3 = no-op, applicato in 14-E)
- titleY 23, bottomLabelY 107, y asse "0" = 104, punta tacca = 41
- `drawJack` gradienti oro: corpo #A08A4A→#4A4028, anello #7A6838→#3A3220
- Conferme: F4/F5 = centro rect h14 (y_target 120 / 27.5 → top 113 / 20); F1 = parametro APVTS senza slider dedicato

## F1 — UI_SCALE fluida 50-200%
- `UI_SCALE` AudioParameterFloat (0.5-2.0, step 0.05, default 1.0) in `createParameterLayout`
  → salvato/ristabilitato con `params.copyState()` (nessuna modifica a getState/setState)
- Editor: `readUiScale()` in ctor (setSize + setResizeLimits min=max = size corrente, niente doppia
  scala) e in `timerCallback` (30 Hz): se cambia → ridimensiona
- `resized()` già scalava i bounds figli con `s = getWidth()/kW`; paint dei figli ora disegna in
  coordinate fisse di progetto e scala il contesto con `g.addTransform(scale(s))`:
  RackPanel (kW), InputJack (119, hit-area INPUT divisa per s), Knob (96, centro 48/48),
  LedIndicator (8), RockerSwitch (ctor con projectW/H: 30x44 / 36x44)
- mouseDrag Knob già normalizzato su getHeight() → invariato a qualunque scala

## F2 — box uniti
- Una cornice esterna `inX0=11 → mdX1=909` (chamfer 9 solo agli angoli esterni) + 5 divisorie
  verticali a fbX0/dlX0/dtX0/hdX0/mdX0 (205/312/420/631/711), da frameTop a frameBottom
- inX1..hdX1 restano solo per centrare i titoli di sezione

## F3 — margini
- frameTop 16→14, frameBottom 134→136 **già applicati in sessione 14 (14-E)** → no-op

## F4 — label inferiori
- `bottomLabelY` 107 → **113** (centro 120 = (frameBottom 136 + asse "0" 104)/2)
- righe glyph misurate sul PNG: 116..123 (erano 109..117); POWER incluso

## F5 — label superiori
- `titleY` 23 → **20** (centro 27.5 = (frameTop 14 + punta tacca 41)/2)
- righe glyph misurate: 22..30; `inputLabelY = titleY` segue (hit-area INPUT locale y0)
- PEAK verifica: centro x150 invariato

## F6 — DELAY TIME su FACTOR
- `dtTitleX0=474 / dtTitleX1=672` (x0+x1 = 2*factorX = 1146, larghezza uguale)
- misurato: glyph 531..614, **centro 572.5** (era 519.5), finisce prima della divisoria 631

## F7 — tacche più lunghe
- `r_interno` 30 → **27** in tutti e 3 i rami (Factor/Range/default), esterno 34 invariato
- misurato: punta tacca PEAK a x150 → righe 41..46 (era ~41..45), lunghezza 4→7 px

## F8 — sottotitoli logo (gap uniformi 6 px)
- Dati read-only "Seiwa bottom 82" erano **contaminati** (ink di DIGITAL DELAY nello stesso crop):
  probe su `ddx14_final_mono.png` → Seiwa 45..70, DD 78..86, DDX 97..105, POWER 110..117
- Gap reali baseline: 8/11/10 (non negativi come ipotizzato). Obiettivo confermato dell'utente:
  gap uniformi 2-8 px → scelto **g=6**:
  - DIGITAL DELAY y 74 → **72** (glyph 76..84)
  - DDX-777 y 92 → **85** (glyph 90..98)
  - STEREO kNeonY 112 → **101** (glyph 104..112)
- Verifica su `ddx14b_final.png`: gap **6/6/6** ✓; nota: le posizioni proposte dall'utente
  (88/104/120) avrebbero dato gap 22/9/6, fuori dal range 2-8 → ricalcolate sui dati reali

## F9 — jack argento
- Corpo #C8C8C8→#505050, anello #B0B0B0→#404040 (erano toni oro); bordo nero/faccette/foro
  già in scala di grigi → invariati
- Probe: corpo TL (178,178,178), anello (98,98,98), foro (5,5,6) ✓

## Build / check / deploy
- `cmake --build build --config Release --target SeiwaDDX777_VST3 ddx_screenshot`: 0 errori
- **Unico PNG headless 1×** (`ddx14b_final.png`, stereo): editor 1100x150, tutte le verifiche
  geometriche sopra OK; cornice unica + 5 divisorie, vecchi bordi interni (191/299/407/618/697)
  assenti; INPUT rosso in stereo; frame y13..14 / 135..136
- verify.py --force: **19 PASS / 6 FAIL / 7 INFO = baseline invariata** (nessun impatto DSP)
- Deploy UAC (Reaper chiuso): MD5 post-copia `B8C9688F2EC66416CC9D2EDA7A4DC7C1`
  (2026-10-09T01:22:27), build = installato **MATCH**
