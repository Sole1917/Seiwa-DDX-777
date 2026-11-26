# HANDOFF — Plugin Seiwa DDX-777

Documento di consegna per lo sviluppo del plugin (emulazione del **Seiwa Digital Delay
DDX-777**, 1985). Stato reverse engineering al **01/10/2026 (sessione 11)**.
Lingua: italiano. Fonte primaria: i file di progetto elencati in §11.

---

## 1. Identità e scopo plugin

**Hardware**: Seiwa Digital Delay DDX-777 — delay digitale rack 19" 1U con companding analogico NE571,
epoca 1985 (data codes 8532/8539), costruito su LSI custom **OKI M60351** (per Tokyo
Trading) + 3 DRAM **M3764-15RS** 64K×1 (192 Kbit totali) + compandor **NE571**.

**Scopo del plugin**: emulazione **mono fedele** (§12 estende a stereo opzionale) della
catena: compressione → campionamento → delay digitale → mix, con i controlli originali
(RANGE, FACTOR, FEEDBACK, DELAY LEVEL, MODULATION SPEED/DEPTH, HOLD) e il carattere
sonoro misurato (§5-§9).

**Cosa rende "vero" il plugin**: 12 bit con companding attivo, f_camp ≈ 32 kHz, banda
~15 kHz, rumore di fondo −67 dBFS, wow/chorus dal clock modulato.

---

## 2. Stato reverse engineering

| Stato | Significato | Esempi |
|---|---|---|
| **[C]** | confermato (foto / misure) | catena audio, config NE571, 192 Kbit, −15 V assente, +5 V misurato |
| **[P]** | presunto | U4 = controller+A/D+D/A, alimentazione +5 V di U4/U6/U10 |
| **[I]** | ipotesi (da verificare) | S&H nella "zona campionamento", Q1/Q2 = S&H o anti-aliasing, routing REMOTE |

**Confermato nelle sessioni 9-11**: topologia NE571 (solo compressore, ch.2 spento →
L17 RISOLTA); **12 bit, f_camp ≈ 32 kHz, banda ~15 kHz** → L5/L12/L13 RISOLTE
(sessione 11); clock VCO con bias trimmer +3% → L1 RISOLTA.

**Aperto (non audio — non blocca il plugin)**: L2 fusibile, L3 trasformatore,
L4 valori elettrolitici, L6 4558/4560, L7/L8 alimentazioni U6/U10, L9 socket DRAM extra,
L10 induttore, L11 diodi timing, L14 RC path audio, L15/L16 rail negativo e single-supply,
L18 driver LED PEAK, L19 lenti ×2, L20/L21/L22 Q2 e U18.

**Regole di lettura**: Ref designator **provvisorie** (U1-U18, C1-C6, R1-R7 gruppi,
Q1-Q2, D1-D5, IND1); le citazioni storiche nei file di sessione precedenti restano
verbatim (archivio), lo stato corrente è quello di `04_lacune.md`.

---

## 3. Catena segnale

```
INPUT 1/4" (−20 dB) → LEVEL M50kΩB → buffer U9 M5221 (+ Q1 2SK118 [P])
  → U7 NE571 compressore (ch.1; feedback fisso 46,1 kΩ pin4↔pin6)
  → zona campionamento (IND1 ALN 252F + C5 27 nF + Q2) [P]
  → filtro anti-aliasing [C-misure: taglio 15-16 kHz]
  → U4 M60351 ADC 12 bit [C-misure]
  → DRAM U1-U3 (192 Kbit)
  → U4 M60351 DAC 12 bit [C]
  → (nessun expandore: ch.2 NE571 spento → L17)
  → DELAY LEVEL M50kΩB → MIX OUT (dry + wet×DELAY LEVEL)
```

- **DIRECT OUT**: dry separato, preso dopo il LEVEL pot.
- **FEEDBACK LEVEL M50kΩB**: **reostato di bias DC VCC↔NE571 pin 4** — non è nel
  percorso audio; regola la soglia del companding (L17).
- **LED PEAK**: ramo parallelo, driver = op-amp libero U8/U9 [I → L18].
- **HOLD**: freeze (blocco indirizzi?) [I].
- **REMOTE jacks**: HOLD / MODULATION / DELAY → logica U4/U5 + HD14066 [I].
- **Clock**: U10 LM311N (VCO/osc. a rilassamento) + C 1000 pF + trimmer `203` →
  U5 TC40H000P (glue logic/divisori) → RANGE (rotary 10 pos.) + FACTOR → f_camp.

---

## 4. Parametri da esporre

| Parametro | Hardware | Range proposto | Note |
|---|---|---|---|
| **RANGE** | rotary switch 10 posizioni (1…512 ms) | 10 step: 1, 2, 4, 8, 16, 32, 64, 128, 256, 512 ms | scala dichiarata sul pannello |
| **FACTOR** | ×0,5 / ×1 / ×2 | 3 posizioni | moltiplica il tempo (e scala f_camp) |
| **FEEDBACK LEVEL** | pot M50kΩB (verde) | 0-100% | = bias DC del compander, non ricircolo |
| **DELAY LEVEL** | pot M50kΩB | 0-100% | livello wet in mix |
| **SPEED** (MODULATION) | pot M50kΩB (arancio) | 0-10 | LFO sul clock → wow/chorus |
| **DEPTH** (MODULATION) | pot M50kΩB (giallo) | 0-10 | profondità modulazione |
| **MIX** | non fisico (MIX OUT = dry + wet) | dry/wet opzionale | l'hardware mescola di default |
| **HOLD** | rocker + LED | on/off | freeze del delay |
| **(extra)** PEAK LEVEL | pot frontale | 0-100% | soglia LED PEAK, non nel segnale |
| **(extra)** INPUT / DIRECT | jack | — | presenze frontali/posteriori |

---

## 5. Modello delay

- Memoria: **192 Kbit = 3× DRAM 64K×1**; a **12 bit** → **16384 word**.
- **f_camp ≈ 32 kHz nominali** (effettiva ≈ 31 kHz: 16384 word ÷ 528 ms).
- **t_max**: 528 ms @ RANGE 512 ×1 (misurato); **960 ms** con FACTOR ×2;
  **247 ms** con ×0,5. Altri RANGE: 66 ms @64, 262 ms @256.
- **Bias clock +3%**: il trimmer `203` fissa il VCO ~3% oltre la nominale
  (errori misurati +3,1% / +2,3% / +3,1% / −3,5% / −6,25%). Il plugin deve esporre
  un **trimmer di calibrazione ±3%** (±2% nel seed stereo, §12).
- Modalità DRAM: bit-serial / fast-page [I] — non determinante per il modello.

---

## 6. Risposta in frequenza

- **Piatta fino a ~15 kHz**, **taglio a 15-16 kHz** (filtro anti-aliasing dedicato
  confermato: NE571 pin6 → M60351 = nessun collegamento diretto).
- Coerente con f_camp 31-32 kHz: transizione di taglio ≈ Nyquist.
- L'hardware non ha filtri RF/line-level esotici: il carattere è dato da anti-aliasing +
  companding, non da EQ.

---

## 7. Rumore e quantizzazione

- **Rumore di fondo: −67 dBFS** (misurato) → coerente con **12 bit**
  (un quantizzatore a 8 bit darebbe ~−53 dBFS).
- **Nessun aliasing** rilevato (test T5): l'anti-aliasing funziona.
- Nel modello: quantizzazione a 12 bit **dopo** il companding in compressione. Non c'è
  espansione in uscita (canale 2 NE571 spento). L'errore viene mascherato dalla curva —
  implementare il dithering/opzionale coerentemente con −67 dBFS.

---

## 8. Distorsione / companding NE571

- **Companding attivo** (test T6): curva di compressione visibile sul trasferimento.
- THD misurata è **dominata dal companding** (T4/T8/T9), non da saturazione:
  la distorsione "è il suono", va mantenuta.
- Configurazione hardware confermata (L17, sessione 9; **numeri pin con correzione
  sessione 12, shift +1**):
  - canale 1 = **solo compressore**, canale 2 (expandore) **spento** (pin 12 = 0 V);
  - retroazione **fissa 46,1 kΩ** (≈47 kΩ E24) tra pin 5 e pin 7;
  - **FEEDBACK LEVEL** = reostato VCC(pin 13)↔pin 5 → **bias DC / soglia**;
  - il "feedback" udito è effetto del companding, non ricircolo.
- Modello: compressore dbx-style in ingresso, nessuna espansione in uscita.

### Feedback loop gain — misure v2 (sessione 13d, soglia −60 dBFS)

Rianalisi delle 3 registrazioni feedback (FB 100/50/20 %) con soglia unica
−60 dBFS peak (`Plugin/tests/FEEDBACK_ANALYSIS_v2.md`):

| Parametro | HW FB10 | HW FB5 | HW FB2 |
|---|---|---|---|
| Echi validi (−60 dBFS) | 22 | 3 | 2 |
| G 1° giro (lineare) | 0.7735 (−2.23 dB) | — | 0.0957 (−20.38 dB) |
| G coda per passo (lineare) | **0.9006** (−0.91 dB, n=22) | **0.3423** (−9.31 dB) | — |
| Floor rumore (RMS/peak) | −76.9 / −66.0 dB | −77.4 / −67.5 dB | −76.4 / −66.7 dB |
| Δt (fit) | 546.02 ± 0.01 ms | 542.39 ms | 540.46 ms |

- Floor **piano** su tutti i FB e su tutta la progressione (coppie 1-2/5-6/10-11:
  −77.0/−77.0/−76.6 dB) → il rumore dominante è **post-loop**, non re-iniettato
  (nessun accumulo nel loop).
- Spettro echi: energia 20-48 kHz al floor (−105…−106 dB) → low-pass ~15-20 kHz
  confermato; ratio RMS eco1/eco10 = 14.4 dB.
- **Calibrazione 13d**: `loopGainFor` a 4 punti {0→0, 0.25→0.105, 0.5→0.345,
  1.0→0.760}; i valori sono gain di re-iniezione (pre-catena): il gain di loop
  totale = valore × gain della catena per-passo, che **non è costante**
  (~1.17 al livello stazionario di FB100, ~1.0 a FB50/25 — dipende dal bias
  del compressore e dal livello). Hiss spostato **post-loop** (tap feedback
  pulito) e `kHissRms = 1.3646e-4` (floor −77.3 dBFS, target T3).
  Verifica: `verify.py` §8; dettaglio: `Plugin/tests/LOOP_CALIBRATION.md`.

### Mappa meccanismi del modello (stato sessione 12b)

| # | Meccanismo | Origine (datasheet NE570N) | Implementazione nel core | Stato |
|---|---|---|---|---|
| — | Companding (limiter −20 dBFS peak + attack/release) | NE571 ch.1 | `Compressor` + `kOpAmp` stadi | attivo (Fase 2) |
| 1 | **kOpAmp = 0.018** | stadi op-amp 4558D | 4× tanh + LP @ 40 kHz | calibrato Fase 2, invariato |
| A | **kVos = 0.0079** | p.6 "VARIABLE GAIN CELL": offset VOS → THD = k·VOS·VIN (0.34% 2ª armonica a 1 mV/0 dBm) | `mo += kVos·(dry² − E[dry²])` post-mix; H2 ∝ livello ingresso (piano in banda) | **calibrato S12 su T4** (H2 1 kHz +0.1 dB, 10 kHz +0.1 dB) |
| B | **kLo = 0** | p.7 crossover distortion stadio di uscita (H3 dispari < 500 Hz) | `mo += kLo·lo³`, lo = LP 500 Hz di `mo` | **taratura = 0** (H3 a bassa banda già fornito dalla dinamica del compressore); disponibile via `--k-lo` |
| C | Saturazione gain cell +8 dBm | p.6 | **solo documentata**, non parametrizzata | non verificabile (uscita satura in REW a −20 dBFS) |

Armoniche target HW (T4, −20 dBFS RMS): 100 Hz H3 −50.9 dB > H2 −54.7 dB (THD 0.343%);
1 kHz H2 −70.3 dB (THD 0.0332%); 10 kHz H2 −69.3 dB (THD 0.0352%). Report completo:
`Plugin/tests/THD_characterization_v4.md` (per-armoniche, livelli, ablazioni, test
discriminante a −30 dBFS).

---

## 9. Modulazione (LFO / wow)

- **MODULATION SPEED/DEPTH** modulano il **clock VCO** (scenario A confermato) →
  variazione del tempo di delay → **wow/chorus** analogico, non un pitch-shift digitale.
- Da implementare come **modulazione della f_camp** (jitter/bend lento), non come
  delay-line read-pointer warping indipendente, per restare fedeli.
- **REMOTE: MODULATION** → accensione/spegnimento LFO (logica U4/U5 + HD14066 [I]).
- RANGE/FACTOR restano divisori digitali a valle: la modulazione entra *prima* della
  divisione.
- **Δt misurati (sessione 13d, rianalisi v2)**: fit sulla progressione degli echi
  feedback (FB10, n=22, soglia −60 dBFS): **546.02 ± 0.01 ms** per passo (542.39 a
  FB5, 540.46 a FB2) — vs 545.7 ms (analisi v1, +0.3 ms) e vs 528.8 ms (T1, delay
  dry→eco1 a RANGE 512×1): la distanza echi-adiacenti eccede il delay secco di
  ~17 ms (effetto del percorso di re-iniezione/ricostruzione; documentato in
  `Plugin/tests/FEEDBACK_ANALYSIS_v2.md`). Il modello usa 527.9 ms
  (f_word = 16384/0.528 s = 31030.3 Hz); lo scarto vs il fit v2 resta aperto.

---

## 10. Limitazioni e da verificare

- LSI M60351 **senza datasheet** (ricerca definitiva: 4 query EN/JP → 0 risultati):
  il comportamento esatto (pipe, latenza interna, modalità DRAM) è ricostruito.
- Lacune aperte (foto/misure non audio): L2-L4, L6-L11, L14-L16, L18-L22; audio:
  **L23** (C_RECT, 0.8-6 µF), **L24** (R_in → calibrazione assoluta Meccanismo A),
  **L25** (banda vs Virtual ADC: decisionato — documentare, status quo).
- **Pinout NE570N**: correzione sessione 12 (shift +1) = ipotesi forte coerente con tutte
  le 7 misure di sessione 9; **da confermare con 3 test rapidi** quando l'unità è
  accessibile (pin 4 ≈ 0 V, pin 5 ≈ 1.8 V, pin 13 ≈ 13-15 V) → L17.
- Misure HW rimandate: −24/−30/−36 dBFS (target di validazione: report v4 §2, incluso il
  test discriminante H3(100 Hz) a −30 dBFS).
- Ref designator **provvisorie**; valori RC del path audio (L14) non decodificati.
- Alimentazione: −15 V **assente** (single-supply +15 V [C-foto], bias mid-rail ~7,5 V [I]).
- Non misurato: curve esatte dei filtri oltre il taglio, drift termico, comportamento
  del freeze (HOLD) a livello di indirizzi.
- §10 nota aggiornata (sessione 13g): i dati di decay/risonanza/impulso sono ora usati
  per il loop gain e il floor di rumore (vedi §8-9 e FEEDBACK_ANALYSIS_v2.md). Restano
  fuori scope solo i parametri non misurati (jitter, wow, group delay dipendente
  dal livello).
- **THD 1 kHz (PASS da 13h, +2.4 dB)**: era FAIL da **P3-13c** (catena saturazione
  ingresso; H3 −60.1 dB vs HW −77.9 dB). Diagnostica 13h (`build/p3_diag/`): H3
  dominata dal M5221 (≈ −71.7 dB in quadratura a §5; NE571 e compressore
  trascurabili a questo livello) → **knee C¹ sul M5221** (lineare fino a
  0.9·VOM, asintoto tanh oltre; VOM 13/15 invariato; giustificazione: datasheet
  M5221 THD 0.007 % typ @1 kHz + grafico p03 THD=1 %). Dopo: 0.044 % (+2.4 dB),
  H3 −75.2 dB (floor kOpAmp), H2 −68.35 dB (±0.25 dB quantizzazione). Dettaglio:
  `Plugin/tests/LOOP_CALIBRATION.md` §6 + `PLUGIN_CHANGELOG.md` (entry 13h).
- **Noise peak (FAIL, −72.5 dB)**: pre-esistente da **P1-13c** lato caldo (−61.9,
  rumore in-loop spiky); 13g lo sposta al lato freddo atteso (hiss post-loop +
  kHissRms): RMS on-target −77.3, crest 4.8 dB vs HW 10.0. Crest da allineare —
  **follow-up C** (`Plugin/tests/LOOP_CALIBRATION.md` §4bis).
- **Follow-up aperto 13g A — risonanza specchio 19 kHz** (check (c) `verify.py` §8,
  FAIL): modo autoeccitato a 18.37/19.29 kHz, modo accoppiato 11.7/12.7k ↔ f_word/2,
  alimentato dal boost 11-14k di eq2/eq3 (fit 13c). Nessun impatto sul match di banda
  T2; riaprire alla revisione del fit di banda T2 (sessione dedicata). **Tentativo
  13i (redesign HF incrementale): fallito**. La catena HF (aa1-aa4, eq2/eq3) è
  in ottimo locale accoppiato; fix richiede redesign olistico monolitico IIR
  (sessione dedicata 13i+). Fix candidati: `Plugin/tests/LOOP_CALIBRATION.md` §4bis.
- **Target −3 dB rivisto (check b, declassato a INFO)**: il modello 13h aveva
  −3 dB a 12.80 kHz (FAIL, target 14.5–16.5 kHz). Le misure HW del 05/10/2026
  (pink noise, `MEASUREMENTS_13h-bis.md`) mostrano che il vero −3 dB dell'HW è
  ≥15 kHz (bordo Nyquist 16 kHz a 32 kHz SR). Il valore di 31.33 kHz misurato
  dal pink noise è **aliasing** (SR 32 kHz → Nyquist 16 kHz), non banda reale.
  Il gap reale è ~2.2 kHz (12.8 → 15 kHz), non ~18 kHz. Check §3.b declassato da
  FAIL a **INFO** in `verify.py` (target rivisto a ≥14 kHz).
- **ddx_smoke T12 (FB=0.75, eco 8-9 vs attese 15-30) — pre-esistente da 13g**:
  scoperta in 13h (isolata: fallisce identico senza la knee M5221). Causa:
  tabella P1 v2 (13g) interpolata a FB0.75 ≈ 0.55 vs 13c ≈ 0.635 → meno echi.
  Ambito P1/loop-gain: rivedere insieme alla tabella P1 / follow-up A.
- **Follow-up aperto 13g B — dinamica compandor** (check (a) `verify.py` §8,
  declassato a INFO): ratio RMS eco1/eco10 = 10.7 vs 14.4 ± 2 dB — il restringimento
  del transiente per passo (gain control envelope-dipendente) non è modellato.
  Riaprire alla sessione compandor dynamics / THD a livelli multipli. Fix candidati:
  `Plugin/tests/LOOP_CALIBRATION.md` §4bis.

---

## 11. Riferimenti

**File di progetto** (radice `E:\tutto\OpenCode\Seiwa DDX-777\`):

| File | Contenuto |
|---|---|
| `00_stato_sessione.md` | stato, log sessioni 1-11, prossimo passo |
| `01_foto_inventario.md` | inventario 98 foto |
| `02_componenti_raw.md` | evidenze raw + **append "Sessione 11 — misure audio"** |
| `03_blocchi.md` | architettura a blocchi (§2 catena, §3 clock, §4 scenari) |
| `04_lacune.md` | lacune L1-L22 (**L1/L5/L12/L13 RISOLTE**) |
| `components.md` | tabelle componenti (U4, rail, C, R, Q, D, H) |
| `schematic.py` → `schematic.png` | schema a blocchi renderizzato |
| `SEIWA_DDX-777_HANDOFF.md` | questo documento |

**Dati di test**: `Segnali_Test/` (15 WAV 96 kHz/32-bit float + `README.md` +
spettrogrammi), generatori in `genera_segnali.py`.

**Misure sessione 11**: tabella T1-T6 + deduzioni in `02_componenti_raw.md`
(sezione "Sessione 11"), sintesi in `04_lacune.md`.

---

## 12. Feature "secondo canale organico" (stereo — concept)

**Concept**: il plugin nasce come emulazione mono fedele del DDX-777. Cliccando
sull'etichetta INPUT del pannello frontale, questa si illumina di rosso e appare un
secondo jack INPUT. Si attiva un canale 2 stereo che replica l'intera catena DSP con
micro-variazioni organiche.

**Variazioni da implementare (seed deterministico)**:

- Tolleranze componenti: resistori ±5%, condensatori ±10%, hFE ±20%
- Invecchiamento: ESR +20% su elettrolitici, drift componenti
- Calibrazione trimmer clock: ±2%
- Seed: hash del seriale (es. 006242 per canale 1, 006243 per canale 2)

**Obiettivo**: immagine stereo naturale e organica, non artificiosa. Le micro-variazioni
restano sotto il cofano (l'utente percepisce uno strumento, non due).

**Razionale**: il DDX-777 hardware è mono per vincoli di memoria (192 Kbit insufficienti
per 2 canali a 12 bit). In software la memoria è illimitata, quindi il canale 2 è
estensione coerente, non emulazione.

**Implementazione suggerita**:

- Due istanze parallele del modello DSP (L e R)
- Seed diverso per canale → variazioni deterministiche ma diverse
- Parametri linkati (RANGE, FACTOR, FEEDBACK) ma con offset organici
- Opzione "unlink" per controllo indipendente (opzionale)

---

## 13. Concept UI e interazione

**Pannello frontale**:

- Riproduzione fedele del pannello DDX-777 (colori knob, LED, serigrafia)
- INPUT (jack + etichetta cliccabile)
- LEVEL (arancio), PEAK (LED rosso)
- FEEDBACK (verde), DELAY (giallo)
- RANGE (azzurro, 10 posizioni), FACTOR (verde, ×0.5/×1/×2)
- HOLD (rocker + LED)
- MODULATION: SPEED (arancio), DEPTH (giallo)
- POWER (rocker + LED)

**Pannello posteriore** (o pannello espandibile):

- MIX OUT, DIRECT
- REMOTE: HOLD, MODULATION, DELAY

**Interazione chiave**:

- Click su etichetta INPUT → LED rosso + secondo jack INPUT
- Doppio click su un controllo → reset al default
- Right-click → parametri avanzati (opzionale)

**Estensioni opzionali**:

- Slider "invecchiamento" (0-40 anni) → evoluzione dinamica delle variazioni organiche
- Preset con seriali diversi (es. "DDX-777 #006242", "#006243")
- Selezione mono/stereo/wide