# DEBUG 14c — GUI refit foto-verificato (sessione 14-ter)

Commit: GUI refit 14c. Baseline DSP invariata: `verify.py --force` = **19 PASS / 6 FAIL / 7 INFO**
(uguali a 14b). Nessuna modifica DSP, logica stereo, dimensioni pot (radius
mozzo/cappuccio, tacche r27..34).

## Modifiche

### F1 — Layout canvas 1000×150 (RackPanel.h)
- `kW1000`, box sezioni: INPUT 11..265 | FEED BACK 265..355 | DELAY 355..444 |
  DELAY TIME 444..618 | HOLD 618..668 | MODULATION 668..842.
- Assi knob: 208 / 304 / 399 / 492 / 582 / 722 / 800; jackCX 65, jackCY 75.
- LED: ledY 28, peakLedY 23, holdLedY 23, peakLedX 238, holdLedX 643,
  powerLedX **972**; rocker: holdSwX 643, powerSwX **972**.
- inputTitleX1 119, inputLabelW 100.

### F2 — Bowtie divisorie + titoli (RackPanel.cpp)
- Bowtie 5× (path ∨/verticale/Λ, chamfer 9, stroke 1.6, kSilk α235).
- `sectionLabel(..., tracking)` con default 2.0; **FEED BACK usa tracking 1.0**.

### F3 — Logo + POWER −15% (RackPanel.cpp, PluginEditor.cpp, RockerSwitch.h)
- `logoCX 900`, Georgia 34pt, `logoCX` commenti 1000×150.
- Neon: blocco DD (845,75,110,18), DDX (845,91,110,20) font 11;
  `kNeonX 835, kNeonY 110, kNeonW 130, kNeonH 16`, `ensureNeon` font 11.
- **Gap righe neon: 10 / 10 / 10** (probe PIL: blocchi 40..69, 80..86, 97..103).
- POWER: `powerSwitch` 30×38, bounds S(957, 56, 30, 38) → centro y75 (56..94);
  LED 12×12 a (972, 28); label POWER centrata 972 → ink 947..995 < 1000.
- `L` lambda a firma (cx, y) per-LED: peak (238,23), hold (643,23), power (972,28).

### F4 — RANGE label (Knob.cpp)
- `drawLabel` r37 → **r41** (riga 205) per non tagliare "RANGE mS".

### F5 — LED ON radiale (LedIndicator.cpp)
- ON = radial gradient kLedOn α110 → α0 (r 4.6) + nucleo + hot-spot #FF6A55
  (1.6,1.4,3.2,3.2) + highlight ovale bianco α130; OFF invariato.
- Stato dopo screenshot: peak/hold OFF (58,10,5), power ON (255,67,50) ✓.

### F6 — Jack a 5 livelli (InputJack.cpp)
- Stack: sagoma r #0B0B0C → disco r·0.92 #4E4E4E → **esagono r·0.75 #8F8F8F**
  (vertici 30+60i°, stroke nero α110) → disco r·0.42 #D6D6D6 → foro r·0.28 kJackHole.
- Dopo il primo PNG l'esagono a r·0.86 era sproporzionato rispetto al dado della
  foto …825 → **applicato fallback concordato 0.75 / 0.42 / 0.28** e rebuild.

## Evidenza foto (deviazioni dalla spec, primato foto)

Coordinate foto …824: frame y197.5..964 (la foto è ruotata 90°),
`scale_x 0.791`, `scale_y` piecewise anchors
[(11,197.5),(304,468),(492,642),(582,724),(722,857),(800,941),(842,964)].

1. **dtTitle 444..618** (non 483..681): "DELAY TIME" ink foto 471..594 →
   centro 531 = centro sezione; con box factor-centered i glyph (534..630)
   attraverserebbero la divisoria 618. Renderizzato 489..572 (centro 530.5) ✓.
2. **FEED BACK tracking 1.0** (era 2.0): a tr2 l'ink 264..356 toccava le
   divisorie; a tr1.0 renderizzato 275..345 ✓.
3. **POWER cx 972** (era 975) — scelta esplicita utente: rocker+LED+label allineati.
4. **HOLD bottom-only**: nessun titolo top aggiunto (foto …824 ambigua;
   collisione con holdLed 643,23); label bottom a 643 (14-bis) mantenuta.
   Da rivalutare se emergesse evidenza migliore.

## Verifiche finali (PIL, `ddx14ter_final.png` 1000×150, stereo, render tent. 1)

- Cornici x11 / x842, bowtie 5× (apici 23/127) ✓.
- Titoli: INPUT red 44..83, FEED BACK 275..345, DELAY 377..421,
  DELAY TIME 489..572, MODULATION 707..802, PEAK 190..226 — nessuna
  collisione con divisorie ✓.
- Logo gap 10/10/10; STEREO red 114..120; Seiwa+DD fino a col 947 < rocker 957;
  ® cols 950..955 rows 36..50; POWER label 947..995 < 1000 ✓.
- Assi knob: peak 207, dl 399, rng 493, fac 583, dpt 798 (fb/spd = inquinamento
  finestra probe, non reali) ✓.
- Label bottom disgiunte: -20dB 51..78 | LEVEL 186..228/282..324/377..419 |
  RANGE 457..526 | FACTOR 554..609 | HOLD 624..660 (gap 15) | SPEED 700..743 |
  DEPTH 777..820 | POWER 947..995 ✓.
- Jack profilo y75: #0B0B0C → #4E4E4E → #8F8F8F → anello chiaro → foro
  #050506; dual centri 49/81 ✓; confronto visivo vs foto …825 ✓.

## Deploy

- MD5 build == installato: `D7D0D4BB5A1D052CC88EEF71BDF08B9A`
  (2026-10-09T14:36:37+02:00).

## Warning build (pre-esistenti, non toccati)

- RackPanel.cpp:217 C4244 drawImageAt float→int.
- RockerSwitch.h cornerRadius C4189; DDX777Core hold C4189.

## Fuori commit (junk)

- `fix_debug*.py`, `presets/`, `test_out.wav`.
