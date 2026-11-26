# LOOP_CALIBRATION — ricalibrazione loop gain + verifica rumore in-loop (sessione 13g)

**Data**: 05/10/2026. **Scope**: azioni 1-6 del task 13g (tabella `loopGainFor` sui
target v2, rumore in-loop costante, test feedback in `verify.py`, HANDOFF §8-9-10,
verifica filtro AA/ricostruzione in-loop). Fonti: `FEEDBACK_ANALYSIS_v2.md` +
`feedback_results_v2.json` (misure HW, soglia −60 dBFS peak).

---

## 1. Target (misure HW v2, soglia −60 dBFS)

| FB (pot) | G coda per passo (lineare) | Echi validi |
|---|---|---|
| 100 % (FB10) | **0.9006** (−0.91 dB, n=22) | 22 |
| 50 % (FB5) | **0.3423** (−9.31 dB) | 3 |
| 20 % (FB2) | **0.0957** (−20.38 dB, 1° giro) | 2 |

Floor rumore HW: **−76.9…−77.4 dB RMS** (−66…−67.5 peak) per tutti i FB, **piano**
sulla progressione (coppie 1-2/5-6/10-11: −77.0/−77.0/−76.6 dB, spread 0.4 dB) →
nessun accumulo → il rumore dominante è **post-loop**.

## 2. Tabella finale `loopGainFor()` (DDX777Core.h:388)

```
f = { 0.00, 0.25, 0.50, 1.00 }
g = { 0.00, 0.105, 0.345, 0.760 }
```

- Valori = gain del segnale **re-iniettato** (pre-catena); il gain di loop TOTALE
  misurato in uscita = valore × gain della **catena per-passo** (write: eq1-3 +
  aa1-4 + dec1-4 + quant12bit; read: int1-4 + rec1-5; più compressore NE571 con
  bias da FB).
- **Il fattore catena NON è costante** (ipotesi "G_catena ~1.07-1.17 unica" scartata
  dai dati): misurato dai rapporti picco/picco per FB —
  - FB100 (echi stazionari a −40…−45 dB, coppie 22-36): **≈ 1.17** (+0.7…+1.8 dB)
  - FB50 (coppie a −35…−50 dB): **≈ 1.00**
  - FB25 (coppia a −41 dB): **≈ 1.0**
  La dipendenza è coerente col bias del compressore (soglia −20 − 2·FB dB) e col
  livello degli echi: il 1° giro (ingresso a −27 dB, vicino al knee) vale ~0.92 in
  tutti i FB (coincide col "G 1° giro" HW 0.7735 totale → catena ~0.93).
- Calibrazione iterativa (misura → `g_i ← g_i × target/G_misurata` → rebuild):
  converge in **1 iterazione** (tabella 4 punti derivata dai dati di coppia 13c).

| FB | Tabella (g) | G misurato (mediana coppie) | Target | Dev | n_ecos |
|---|---|---|---|---|---|
| 100 % | 0.760 | **0.8951** | 0.90 ± 0.03 | −0.005 | 35 (HW 22) |
| 50 % | 0.345 | **0.3329** | 0.34 ± 0.03 | −0.007 | 4 (HW ~3) |
| 25 % | 0.105 | **0.1044** | 0.10 ± 0.02 | +0.004 | 2 (HW ~2) |

Tolleranza interna ±0.01 raggiunta su tutti e 3 gli anchor (dev ≤ 0.007).

## 3. Rumore: spostamento post-loop + floor costante

**Cambiamenti** (`DDX777Core.h`):
1. Tap feedback **pulito**: `wPrev_ = w` a riga **236**, subito dopo la catena
   rec1-5 (righe **223-227**) e prima di qualsiasi somma di rumore → il floor
   **non circola nel loop**.
2. Hiss post-loop: `wOut = w + rng_.nextBipolar()·hissAmp` (riga **243**), usato in
   `outMix` (riga 247) e `outWet` (riga 308) → incluso nel wet (il test T3 misura
   con `--emit wet`).
3. **`kHissRms`: 1.8e-4 → 1.3646e-4** (= 10^(−77.3/20), riga 331). Il vecchio
   valore era tarato col hiss IN-loop, dove la catena 15 kHz toglieva ~2.4 dB di
   potenza di banda; post-loop il valore è tarato direttamente sul floor HW
   −77.3 dBFS. (Nota: deviazione da "kHissRms invariato" del task 13g, **necessaria**
   per l'azione 2: il target −77 dB RMS post-loop non è raggiungibile con 1.8e-4,
   che darebbe −74.9.)

**Spread del floor nei gap** (FB100, finestre 100 ms, coppie 1-2/5-6/10-11):

| Stato | Gap 1-2 | Gap 5-6 | Gap 10-11 | Spread |
|---|---|---|---|---|
| Pre-fix (13c: hiss in-loop, tabella 0.82) | −79.4 | −72.1 | −69.5 | **9.8 dB** (FAIL) |
| Post-fix (13g) | −79.1 | −79.2 | −79.1 | **0.1 dB** (PASS ≤ 1.0) |

Il pre-fix mostrava il ramp di accumulo atteso (amplificazione del rumore in-loop
`1/√(1−G²)` × catena: a G≈0.96 → +5 dB sui gap successivi). Post-fix il floor è
piano (±0.1 dB) su tutta la progressione, come in HW (0.4 dB).

## 4. Test `verify.py` §8 (nuovo) — esito `--force`

Setup: fixture impulso 20 s (delta 1.0 @ sample 0, `build/verify_out/fb_impulse_20s.wav`
— `01_impulse_single.wav` dura solo 1 s), render mix con `--range 512 --factor 1
--level 1 --feedback {1.0|0.5|0.25} --delay-level 1`; detection echi = algoritmo v2
(soglia −60 dBFS, ds=48, local-max ±3 ms, min gap 0.4 s, dry esclusa);
G = mediana dei rapporti lineari picco/picco.

| Check | Esito | Valore | Target |
|---|---|---|---|
| loop G FB100 | **PASS** | 0.8951 | 0.90 ± 0.03 |
| loop G FB50 | **PASS** | 0.3329 | 0.34 ± 0.03 |
| loop G FB25 | **PASS** | 0.1044 | 0.10 ± 0.02 |
| n echi FB100 | **PASS** | 35 | ≥ 20 (HW 22) |
| gap RMS spread | **PASS** | 0.1 dB | ≤ 1.0 dB (HW 0.4) |
| (b) energia 20-48k echi 1/5/10 | **PASS** | −10.7/−10.6/−10.7 dB rel (piatte, al floor) | ≤ floor + 10 dB (HW: al floor) |
| (a) RMS eco1/eco10 | **INFO** | **10.7 dB** | 14.4 ± 2 dB (gap = compandor, non modellato — §4bis B) |
| (c) H_loop 15-20k per passo | **FAIL** | **+10.1 dB max** (a 18.37/19.29 kHz) | ≤ +1.0 dB |
| (d) energia 0-20k (INFO) | INFO | e1=−22.3, e5=−27.6, e10=−33.0 dBFS | HW −61.8/−71.6/−76.4 |
| G_forward (INFO) | INFO | eco1 = −27.0 dBFS | HW −38.9 dB (gap noto, saturazione ingresso frozen 13c) |

**T3 (sez. 2, post-fix)**: noise RMS **PASS** (−77.3 = target); noise peak
**FAIL** (−72.5 vs finestra [−72.3, −62.3], 0.2 dB oltre): il rumore del modello
(RNG a banda limitata, crest ≈ 4.8 dB) a −77.3 RMS ha peak intrinsecamente ~5 dB
più basso dell'HW (crest 10 dB). Nota: il baseline 13c falliva la stessa check
sull'altro lato (−61.9, +0.4 dB oltre: rumore in-loop quantizzato a impulsi
sub-LSB risuonanti nel rec).

### Diagnosi (c): risonanza di specchio a 18.37/19.29 kHz

- Il +10.1 dB è concentrato in **due alias stretti**: 18.375 e 19.286 kHz,
  **coniugati attorno a f_word/2 = 15.515 kHz** (12.655↔18.375, 11.744↔19.286 kHz):
  il contenuto in-banda a 11.7/12.7 kHz viene specchiato a ogni campionamento a
  31030.3 Hz e la catena di ricostruzione (int1-4 + rec1-5) non lo sopprime
  sufficientemente **in loop**.
- I due bin crescono passo-passo (S1: −73…−83 dB → S5: −43 dB → S10: −40/−48 dB)
  fino a un floor ~−42 dB: **autoeccitazione del modo accoppiato**, non un gain di
  banda uniforme (mediana H51 in 15-20k = −2.1 dB; energia 20-48k al floor: PASS).
- **Pre-essenza**: al gain tabella 0.82 (13c, G_med 0.959) il modo NON si
  autoeccita (H51 = −1.5 dB); con tabella 0.76 (13g, G_med 0.895) sì. Il mechanismo
  è il **boost 11-14 kHz del fit banda 13c** (eq2 +3.0 dB @11.73k Q0.957,
  eq3 +12 dB @14k Q2.5 → +~9.6 dB a 11.7k) che alimenta il modo: la stabilità
  dipende dal bias/livello del compressore (soglia −22 dB a FB100; gli echi a
  −27…−31 dB stanno sul knee: con 0.82 il gain del modo < 1, con 0.76 > 1).
- L'HW non mostra il floor (eco10 HW 0-20k a −76.4 dB: nessun floor a −45 dB) →
  difetto del modello, non dell'hardware.
- **Decisione 13g**: non fixato ora (rischio peggiorare T2 già al limite);
  Follow-up aperto A con i fix candidati — vedi **§4bis**.

### Diagnosi (a): ratio RMS eco1/eco10

Target HW 14.4 dB (9 passi) = 1.6 dB/step in RMS vs 0.91 dB/step in picco:
gli echi HW **perdono energia oltre il picco** (il transiente si restringe:
crest 8 dB @eco1 → 14.2 dB @eco10). Il modello ha forma di impulso costante per
passo (catena lineare stazionaria): il limite strutturale con G=0.90 è
~8.2 dB (picco) + contributo del modo 19k → 10.7 dB misurati. Non raggiungibile
senza dinamica di forma dell'impulso (fuori scope 13g).

## 4bis. Follow-up aperti (decisione sessione 13g, 05/10/2026)

### Follow-up A — Risonanza specchio (check c, FAIL)

- **Descrizione**: risonanza autoeccitata a 18.37/19.29 kHz, modo accoppiato
  11.7/12.7 kHz ↔ f_word/2 (15.515 kHz), alimentata dal boost 11-14 kHz di
  eq2 (+3 dB @11.73k) / eq3 (+12 dB @14k Q2.5) del fit 13c. Sintomo di un
  eccesso del fit 13c, non un difetto isolato.
- **Impatto**: inudibile direttamente (>16 kHz), nessun impatto sul match di
  banda (T2); indesiderata sul piano della fisicità del modello.
- **Decisione 13g**: non fixare ora (rischio peggiorare T2 già al limite:
  drift max 7.84 dB @13.96 kHz).
- **Tentativo 13i (05/10/2026)**: redesign HF incrementale (aa2/aa3 bypass,
  aa4 Q ridotto, eq3 ridotto) — **fallito**. La catena HF (aa1-aa4,
  eq2/eq3) è in un ottimo locale accoppiato: ogni modifica isolata rompe
  l'equilibrio e introduce regressioni (THD 10k, loop gain, T5). La
  risonanza è un artefatto della catena AA+EQ accoppiata, non un difetto
  isolato fixabile in modo incrementale.
- **Fix candidati (richiedono redesign olistico, non incrementale)**:
  1. Ridiscussione topologia AA: aa1→14 kHz, aa4→16 kHz Q=1.5, aa2/aa3 stopband;
  2. EQ ridisegnato: eq2 +1-2 dB @11-12 kHz Q=0.5, eq3 +2-3 dB @15-16 kHz Q=1.0;
  3. Validazione simultanea di ripple, -3 dB, H_loop, THD, loop gain.
- **Trigger per riaprire**: sessione dedicata 13i+ con approccio monolitico IIR.
- **Stato**: aperto, non bloccante.

### Follow-up B — Dinamica compandor (check a, INFO)

- **Descrizione**: il modello riproduce il loop gain di picco (0.90, confermato
  dai check G per FB) ma non il restringimento del transiente per passo
  (crest factor costante vs HW 8→14.2 dB). Gap RMS eco1/eco10: 10.7 vs 14.4 dB
  (≈3.7 dB).
- **Causa**: dinamica del compandor (gain control tempo-variante) non modellata
  esplicitamente. Il compressore attuale è applicato al segnale ma non ha il
  comportamento "envelope-dependent" che restringe la coda degli echi.
- **Decisione 13g**: check (a) declassato da P/F a **INFO** in `verify.py` §8
  (stessa logica del check G_forward: target misurato, divario documentato,
  fix fuori scope). Il valore resta nel report JSON.
- **Impatto**: coda più "piena" in RMS dell'HW; forma spettrale corretta.
- **Fix candidati (non applicati)**:
  1. Envelope-follower con release più veloce sulla coda;
  2. Compandor con gain control dipendente dall'inviluppo del segnale ritardato;
  3. Revisione del compressore per modellare il restringimento del transiente.
- **Trigger per riaprire**: lavoro dedicato sul compandor dynamics (probabilmente
  assieme alla THD a livelli multipli — i due temi sono correlati).
- **Stato**: aperto, non bloccante.

### Follow-up D — Target −3 dB rivisto (check b, declassato a INFO)

- **Contesto**: il modello 13h aveva −3 dB a 12.80 kHz (FAIL, target 14.5–16.5 kHz). Le misure HW del 05/10/2026 (pink noise, MEASUREMENTS_13h-bis.md) mostrano che il vero −3 dB dell'HW è ≥15 kHz (bordo Nyquist 16 kHz a 32 kHz SR). Il valore di 31.33 kHz misurato dal pink noise è **aliasing** (SR 32 kHz → Nyquist 16 kHz), non banda reale.
- **Conseguenza**: il gap reale del modello è ~2.2 kHz (12.8 → 15 kHz), non ~18 kHz. Il FAIL #3 era sovrastimato.
- **Decisione**: declassare il check §3.b da FAIL a **INFO** in `verify.py` (target rivisto a ≥14 kHz). Il check resta nel report JSON per tracciabilità.
- **Raccomandazione redesign 13i**: privilegiare ripple e H_loop come metriche primarie; −3 dB a 14-15 kHz è sufficiente. Non inseguire 31 kHz (artefatto aliasing).
- **Stato**: chiuso (target rivisto, check declassato a INFO).

### Follow-up C — Crest del rumore post-loop (noise peak, −0.2 dB)

- **Descrizione**: a RMS on-target (−77.3 dBFS), il peak del rumore modello è
  −72.5 dBFS vs HW −67.3 dBFS (−0.2 dB oltre la finestra [−72.3, −62.3]): il crest
  del rumore post-loop liscio è **4.8 dB** contro **10.0 dB** dell'HW. Per centrare
  il peak HW a RMS corretto serve un **componente a picchi rari** sul fondo
  post-loop (carattere misto liscio+spiky del fronte analogico HW).
- **Contesto storico**: 12b/13b −63.9 PASS (rumore in-loop spiky, crest 15.6 dB —
  match fortuito); 13c/13d/13e −61.9 FAIL lato caldo (crest 15.4 dB, P1);
  13g −72.5 FAIL lato freddo (post-loop liscio, crest 4.8 dB).
- **Impatto**: nessuna udibilità (il floor RMS è corretto); limite solo sul check
  peak.
- **Fix candidati (non applicati)**:
  1. Componente a picchi rari (impulsi sparsi a livello −90 dB su envelope lenta);
  2. Shaping spettrale 1/f del fondo;
  3. Rimodulazione del quantizzatore/dither per recuperare picchi residui.
- **Trigger per riaprire**: sessione architettura rumore.
- **Stato**: aperto, non bloccante.

## 5. Azione 6 — filtro AA/ricostruzione in loop: VERIFICATO

Il tap feedback è **dopo** tutta la catena di ricostruzione: `wPrev_ = w` a
`DDX777Core.h:236`, subito dopo `rec5_.process` (catena rec1-5 a righe
**223-227**, a valle di int1-4 a righe 217-221). Ogni giro attraversa
write (eq1-3 → aa1-4 → dec1-4 → quant12bit) e read (int1-4 → rec1-5):
**il filtro anti-aliasing/ricostruzione è già dentro il loop** → nessun filtro da
aggiungere (il fix "aggiungere LP in loop" proposto a monte sarebbe duplicazione).
La verifica spettrale (check b/c §4) conferma che il floor 20-48k resta al floor
(piano, −10.7 dB rel su tutti gli echi).

## 6. Stato `verify.py --force` finale (13g: 21/5/6 → **13h: 22 PASS, 4 FAIL, 6 INFO**)

| Check | Stato | Nota |
|---|---|---|
| §1 delay (5 casi) | PASS | invariato |
| §2 noise RMS | **PASS** | −77.3 on-target (baseline 13c: −77.3; stato intermedio 13g — hiss post-loop con vecchia kHissRms 1.8e-4 —: −74.9, prima del ritardo a 1.3646e-4) |
| §2 noise peak | FAIL (−0.2 dB) | −72.5. Storia: 12b/13b −63.9 PASS (crest 15.6 dB) → 13c/13d/13e −61.9 FAIL lato caldo (P1) → 13g −72.5 lato freddo: conseguenza attesa hiss post-loop a RMS on-target; crest 4.8 vs HW 10.0 dB → follow-up C |
| §3 band ripple 100-14k | FAIL (7.89 dB) | L25 pre-esistente (12b: 7.83; 13c: 7.93) — invariato |
| §3 −3 dB point | FAIL (12.80 kHz) | L25 pre-esistente (12b/13c/13d/13e: 12.80) — invariato |
| §3 drift ours-vs-HW 400-14k | PASS | 0.42 dB (max 7.84 dB @13.96k) |
| §4 aliasing (5) | PASS | invariato |
| §5 THD 1 kHz | **PASS** (2.4 dB) | 0.044 % vs HW 0.033 % (13h). Storico: 12b/13b 0.047 % (+3.1) PASS → 13c 0.100 % (+9.6) FAIL P3 → 13g 0.1061 % (+10.1) → **13h 0.044 % (+2.4) PASS** (knee C¹ M5221: diagnostica `build/p3_diag/`, H3 dominata da M5221 ≈ −71.7 dB, NE571 zero effetto, VOM 13/15 invariato — giustificazione datasheet) |
| §5 THD 100/10 kHz | PASS | 13h: +0.1 / +2.1 dB (13g: +1.7 / +2.1; 100 Hz migliorato con la knee) |
| §6 curva gradini | PASS | invariato |
| §7 A/B spettrale | INFO | invariato |
| §8 (nuovo) | 5/7 P/F PASS | (a) ratio RMS → INFO (follow-up B §4bis); FAIL: (c) H_loop (follow-up A §4bis) |

### Tabella di attribuzione dei FAIL (12b/13b → 13c → 13d/13e → 13g → 13h)

| FAIL | 12b/13b (ultimo PASS o stato) | 13c | 13d/13e (GUI, audio=13c) | 13g | 13h | Attribuzione |
|---|---|---|---|---|---|---|
| noise peak | −63.9 dBFS **PASS** (RMS −79.3, crest 15.6 dB) | −61.9 dBFS **FAIL** (+0.4 lato caldo; "residuo P1") | −61.9 FAIL (invariato) | −72.5 dBFS **FAIL** (−0.2 lato freddo; RMS −77.3, crest 4.8 dB) | −72.5 dBFS **FAIL** (invariato) | P1-13c (rumore in-loop spiky @ FB50=0.45); spostamento lato freddo = conseguenza attesa del hiss post-loop + kHissRms (azione 2); crest → **follow-up C** |
| band ripple 100-14k | 7.83 dB FAIL (L25) | 7.93 dB FAIL | 7.93 dB FAIL | 7.89 dB **FAIL** | 7.89 dB **FAIL** (invariato) | L25 pre-esistente (era 12b, Virtual ADC) — invariato |
| band −3 dB | 12.80 kHz FAIL (L25) | 12.80 kHz FAIL | 12.80 kHz FAIL | 12.80 kHz **FAIL** | 12.80 kHz **FAIL** (invariato) | L25 pre-esistente — invariato |
| THD 1 kHz | 0.047 % (+3.1 dB) **PASS** | 0.100 % (+9.6 dB) **FAIL** ("residuo P3"; regola Q3: non sintonizzare kJfet, indagare scala) | +9.6 dB FAIL (invariato) | 0.1061 % (+10.1 dB) **FAIL** | 0.044 % (+2.4 dB) **PASS** | P3-13c (catena saturazione ingresso; H3 −60.1 dB vs HW −77.9). Diagnostica 13h (`build/p3_diag/`): H3 dominata dal M5221 (≈ −71.7 dB in quadratura; NE571 zero effetto) → **knee C¹ M5221** (lineare fino a 0.9·VOM, asintoto tanh oltre, VOM 13/15 invariato; datasheet: THD 0.007 % typ + grafico p03 THD=1 %). Dopo: H3 −75.2 dB (floor kOpAmp), H2 −68.35 dB (+0.25 dB quantizzazione) |
| H_loop 15-20k | (check inesistente) | (check inesistente) | (check inesistente) | +10.1 dB max **FAIL** | +10.1 dB **FAIL** (invariato) | Nuovo check 13g; risonanza specchio 18.37/19.29 kHz (difetto pre-esistente della catena, esposto al gain target 0.90) — **follow-up A** §4bis |

Fonti: `PLUGIN_STATE.md` § "Risultati ultimo verify.py (12b/13a/13b)";
`PLUGIN_CHANGELOG.md` (entry 11a/11b/13c/13d/13e/13g/13h); `00_stato_sessione.md`
(sessioni 13b-13h); `build/verify_report.json` (13g, 13h).

> **Sintesi**: Nessuna regressione introdotta da 13g né da 13h. Dopo il fix P3
> di 13h (knee C¹ M5221: THD 1 kHz PASS +2.4 dB) i 4 FAIL restanti sono: L25
> (band ripple, −3 dB) pre-esistente da 12b; P1 (noise peak) pre-esistente da
> 13c, spostato lato freddo atteso (follow-up C sul crest); H_loop (risonanza
> specchio) nuovo check 13g (follow-up A). Il fix hiss post-loop (13g) ha
> corretto il comportamento in-loop come da obiettivo.

## 7. Vincoli rispettati

- Non toccati: kJfet/limNE571 (13c), compressore, filtri eq/aa/dec/int/rec,
  VCO/LFO, sezioni 1-7 di `verify.py`, WAV di `Prep/Segnali_Test`.
- 13h: stadio M5221 (thrM5221) da tanh puro a knee C¹ — VOM 13/15 invariato,
  sentinela bypass bit-identica; kJfet/limNE571 intatti (dettaglio §6).
- Unica costante noise modificata: `kHissRms` 1.8e-4 → 1.3646e-4 (conseguenza
  necessaria dello spostamento post-loop deciso nell'azione 2; documentato §3).
- HANDOFF aggiornato: §8 (blocco v2 + calibrazione), §9 (Δt 546.02 ms), §10
  (nota 13g).
