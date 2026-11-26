# Sessione 14 — Debugging GUI (formato, spaziature, allineamenti, area click stereo, titolo)

Pre: snapshot `.snapshot_14_pre_gui/` (src/, tests/, CMakeLists.txt su f8b89e3).
Vincoli: NON toccare i pot (dimensioni/resa grafica), il DSP (PluginProcessor.cpp, DDX777Core.h), verify.py, i rocker switch (item 7).

## Step 14-A — formato generale + cornici
- kW 1000→1100, kH 136→150
- tutte le x ×1.1 (round-half-up): sezioni, assi knob, jack, LED, switch, logo
- y: shift +8 coerente (knobCY/jackCY 67→75, ledY 20→28, switch 45→53, titoli 21→29, label basse 99→107, logo +8)
- cornici: frameTop 16 (invariato), frameBottom 118→134 (altezza 102→118, margine 16/16 simmetrico)
- file: RackPanel.h (Layout), RackPanel.cpp (serigrafia), PluginEditor.cpp (bounds jack, switch, lambda L), InputJack.cpp (kOriginY)

Risultato A:
- build VST3 + ddx_screenshot: 0 errori; PNG `ddx14a_mono.png`/`ddx14a_stereo.png` 1100×150
- **Bug trovato e fixato in A**: lambda `L()` in `PluginEditor.cpp resized()` usava `20.0f` hardcoded → LED peak/hold a y20 invece di `ledY` 28; fix `static_cast<float>(ddxui::Layout::ledY)`. Riconvalidato: peak/hold LED 16 px @y28..36, power LED 61 px.
- check pixel (check14a.py + check14a2.py): **TUTTO OK** — 7 cappucci pot nei centri, cornici y16/y134 (zona logo senza cornice = atteso), jack mono/foro/anello, jacks stereo (41,75)/(73,75) fori più scuri dell'anello, tutte le label basse centrati ≤1.5px (con mascheratura stroke cornici nei crop), titoli presenti, DDX-777 centro 985.0, neon STEREO 604 px x934..1038 senza toccare POWER (1044), mono senza rosso, rocker disegnati.
- **NOTA (non FAIL)**: 20 px cream "Seiwa" dentro il box rocker (x1051..1060, y54..55/67..69) — overlap pre-esistente (c'era anche a 1000px), fix previsto da item 8 in Fase D (logoCX 1007→985). ® y40..51 finisce a x1071 ma 2px sopra il rocker (y53), nessun tocco col POWER LED (y28..36).
- artefatti di check risolti: label-centre contaminati dalle stroke cornici (x191/420/618/711/909 nel crop) → mascherati; cornice x1000 assente = zona logo by design; foro stereo r1 antialias → test "più scuro dell'anello".

## Step 14-B — InputJack + area click + label rossa
- **item 2**: titolo INPUT centrato su jackCX (sectionLabel x0=11, x1=`2*jackCX-inX0`=103 → box 15..107, centro 57; era 69.5)
- **item 3**: jack dual **r15** a `jackCX±16` (centri 41/73, gap 2 px); mono r13 invariato; anello/foro/gradiente parametrizzati dal raggio: `reduced(4r/13)`, `reduced(9r/13)`, gradiente `±9r/13` (identici a r13 = valori storici 4/9/±9)
- **item 11**: click solo sul rettangolo titolo INPUT (`Layout::inputLabel*` = abs (15,23,92,14) → locale (4,3,92,14)); `mouseDown` ignora il resto; cursore a mano **solo** sul titolo (`mouseMove/mouseEnter/mouseExit`), default freccia
- INPUT titolo **rosso #B4281E** in stereo (sectionLabel con parametro colour)
- **rimosso il fade**: via `stereoTick()`/`stereoAlpha_` (h + cpp + chiamata in timerCallback); `setStereoOn` repaint immediato su cambio; neon on/off istantaneo
- `inputY0` 28→20: bounds InputJack **(11,20,119,80)** per includere il titolo a y23 nella hit-area (il resto dell'area resta invisibile/non cliccabile)

## Step 14-C — allineamento e spaziatura label
- **item 4**: PEAK ricentrato sull'asse `peakX`: box `(122.5, titleY, 55, 14)` centro **150** (era 156.5)
- **item (titoli)**: riga titoli `titleY` **29→23** (INPUT/FEED BACK/DELAY/DELAY TIME/MODULATION + PEAK) → gap testo↔corona tacche ~6 px (era 0-1 px); costante `bottomLabelY`=107 per le etichette basse (valore invariato)
- **item 6**: etichette scala Knob.cpp `r38→r41` (Level010/Level0to20/Factor); **Range lasciato a r37** (con r40 "512" toccherebbe "RANGE mS"): spinta esterna +3 uniforme solo dove previsto
- riferimento gap LEVEL↔corpo ~6 px: nessuna modifica (valore di riferimento)

## Step 14-D — titolo e sottotitoli
- **item 8**: `logoCX` **1007→985**: glyph "Seiwa" finivano a x~1050 sul rocker POWER (1051) → ora ~1028 (23 px di stacco); fix overlap pre-esistente (20 px cream nel box rocker)
- **item 10**: trio **Arial 13 bold tr2.0**: DIGITAL DELAY 12→13 e tr 1.6→2.0; DDX–777 14→13; STEREO (ensureNeon) 9→13
- **fix neon storico**: le immagini neon erano ~63×25 blitate in un rect 146×32 con `stretchToFit` → testo allargato ~2.3×; ora immagine = label+2×border (146×32), testo centrato dentro, `drawImageAt` 1:1 senza stretch

## Step 14-E — cornici con margini maggiori
- `frameTop` **16→14**, `frameBottom` **134→136** (altezza cornice 118→122), contenuti invariati
- (approvato senza check intermedio; verifica solo sul PNG finale)

## Esito finale (step 14)
- Build finale VS18 x64 Release: 0 errori (VST3 + ddx_screenshot)
- PNG headless finale (mono + stereo): 1100x150, check strutturale pulito (cornici 14/136, titoli y23, PEAK centro 150.0, INPUT rosso in stereo, logo fuori dal rocker, neon 1:1 non deformato)
- verify.py --force: **19 PASS / 6 FAIL / 7 INFO** = baseline (DSP intatto)
- Deploy UAC: MD5 post-copia = MD5 build = 74EE5CCB44C690481FCE29ADB1D3C178, 2026-10-09T00:21:51
- Nota jack dual: r15 a +-16 da jackCX -> gap nominale 2 px, chiuso dall'antialias (tangenti visivi, come da numeri approvati)
