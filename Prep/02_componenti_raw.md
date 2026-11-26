# Componenti RAW — append-only (source of truth)

Regola: append dopo OGNI foto analizzata / OGNI ricerca datasheet. Non cancellare righe.
Colonne: Foto | Ref | Tipo | Sigla/Marking | Package | Valore | Funzione | Note

## IC — lato componenti (survey 843-846, 850-869, letture dirette 871-879)

| Foto | Ref | Tipo | Sigla/Marking | Package | Valore | Funzione | Note |
|---|---|---|---|---|---|---|---|
| …843,844,849,850,853,854,855,868,869 | U1-U3 (prov.) | DRAM | `M3764-15RS / OKI / JAPAN / 44238` ×3 | DIP-16 | 64K×1, 150ns fast-page (datasheet OKI MSM3764) | Memoria delay | Ref provvisorie; eventuale 4ª (`…RS 2298`) da verificare — …867 |
| …804,807,810,811,814,815,868* | U4 (prov.) | LSI custom | `OKI JAPAN / M60351 / 5102` | QFP-56 (14 pin/lato) | — | Controller delay / ADC-DAC? | Montato su LATO SALDATURE; datasheet non reperito; "5102" = date code? |
| …844,845,850,851,852,856,857,868,869,878* | U5 (prov.) | Logica | `Toshiba TC40H000P / JAPAN / 8539H` | DIP-14 | quad NAND 2-ingressi (C²MOS, eq. 7400) | Glue logic / clock | Datasheet Toshiba confermato |
| …844,845,846,852,855,857,858,859,860,861,874* | U6 (prov.) | Switch analogico | `HD14066BP / 4M2 7` (Hitachi) | DIP-14 | quad bilateral switch | Routing: feedback/bypass/modulazione | — |
| …845,846,855,858,862,863,864,865,866,872* | U7 (prov.) | Compandor | `NE571N / K8436` (Signetics "S") | DIP-16 | expander+compressor, RMS detector | AGC/companding nel loop feedback | — |
| …843,844,850,851,852,856,868,869,878* | U8 (prov.) | Op-amp quad | `Mitsubishi M5224P / 4507` | DIP-14 | quad op-amp (eq. LM324-class, da confermare) | Filtri/mixer | — |
| …844,853,855,857,858,859,860,861,862,863,871* | U9 (prov.) | Op-amp dual | `Mitsubishi ▲5221 / 4504` | DIP-8 | dual op-amp (da datasheet) | Stage analogico | — |
| …844,845,852,855,857,858,863,878* | U10 (prov.) | Comparatore? | riga1 `…8532` (batch?) riga2 `LM 31N` → prob. **LM311N** | DIP-8 | — | Prob. comparatore PEAK LED | LETTURA PARZIALE — da verificare con crop |
| …840,845,846,859,860,861,862,863,865,871*,872*,873*,874* | U11+ (prov.) | Op-amp dual | `4558D / JRC` code `5061`,`1650`,`5200`,`5200` (varie) | DIP-8 | NE5558/4558-class dual | Op-amp generali (filtri, I/O, mixer) | 6-7 pezzi; per-sigla 4558 vs 4560 da verificare (alcuni leggono 4560D) |
| …867,868,869,878* | Uxx (prov.) | Regolatore | `AN7815` (Panasonic) + radiatore | TO-220 | +15 V | Rail positivo analogico | Un solo regolatore visibile; rail negativo e +5V DA CERCARE |
| …845,875*? | — | Transistor | TO-92 nero (marking illeggibile) | TO-92 | — | da verificare | 1-2 pezzi |
| …845,862,863,864,865,866 | — | LED | lente chiara/trasparente 5mm ×2 (coppia) | 5mm | — | Prob. indicatori/opto | chiari = LED bianchi o fototransistor? da verificare |

## Pannelli / connettori / pot

| Foto | Ref | Tipo | Sigla/Marking | Package | Valore | Funzione | Note |
|---|---|---|---|---|---|---|---|
| …824,826,825 | — | Jack 1/4" | `INPUT` `−20dB` | panel TS | — | Ingresso audio (mononon bilanciato) | Frontale |
| …819,822 | — | Jack 1/4" ×2 | `MIX OUT`, `DIRECT` | panel TS | — | Uscite mista + dry | Retro |
| …819,820 | — | Jack 1/4" ×3 | `REMOTE: HOLD, MODULATION, DELAY` | panel | — | Footswitch remoti | Retro |
| …824,830-832 | — | Switch + LED | `HOLD` rocker + LED rosso | panel | — | Freeze delay | Frontale |
| …824,835 | — | Switch + LED | `POWER` rocker + LED rosso | panel | — | Mains | Frontale |
| …824,828,829 | — | Pot/rotary | `RANGE mS` (azzurro), scala 1,2,4,8,16,32,64,128,256,512 | rotary 10 pos. | — | Selezione range delay (clock/divider) | Frontale |
| …829,831 | — | Pot | `DELAY TIME / FACTOR` (verde), ×0.5…×2 | pot linear? | — | Trim tempo delay | Frontale |
| …826,827 | — | Pot | `PEAK LEVEL` (arancio) 0-10 | pot | `M50kΩB` (dorso) | Livello ingresso / soglia PEAK | Dorso pot: `M50kΩB 50 C` — …872,879 |
| …826,827 | — | Pot | `FEEDBACK LEVEL` (verde) 0-10 | pot | `M50kΩB` | Loop feedback | — |
| …827,828 | — | Pot | `DELAY LEVEL` (giallo) 0-10 | pot | `M50kΩB` | Mix delay | — |
| …831,832 | — | Pot | `MODULATION SPEED` (arancio) 0-10 | pot | `M50kΩB` | Velocità LFO mod | — |
| …832,833 | — | Pot | `MODULATION DEPTH` (giallo) 0-10 | pot | `M50kΩB` | Profondità LFO | — |
| …844,853,878* | — | Rotary switch | wafer fenolico, ~10 fili arcobaleno | panel | — | RANGE (o FACTOR) | collegato a fascio colorato |
| …867,869 | — | Trimpot | giallo `203` | trimmer | 20 kΩ | Clock/offset (da verificare) | — |
| …850,851,856,868 | — | Trimpot | cermet bianco tondo | trimmer | da verificare | Calibrazione (bias/level) | — |

## PSU / rete

| Foto | Ref | Tipo | Sigla/Marking | Package | Valore | Funzione | Note |
|---|---|---|---|---|---|---|---|
| …840,841,870* | — | Filtro di linea | `A91S2 / 3A/48A / 250V~ / (S) / A2H4` | box chassis | — | Filtro EMI AC | Montato a chassis |
| …840,841 | — | Cap X2 | maroon `ECQ-U / .0022µF / 40/085/21 / X2 / 250V~` | dip film | 2.2 nF | Cap X2 di sicurezza | In parallelo/attorno a switch |
| …808,809,817,842,884*,885* | — | Fusibile | cartuccia vetro in clips porta-fusibile nero | 5×20 | rating non leggibile | Protezione rete | Rating DA VERIFICARE (foto macro dedicata) |
| …816,842,874* | — | Trasformatore | EI, nastro blu, morsetti rossi/blu | PCB/chassis | primario: "…20V"? da verificare | Isolamento + secondari multipli | Stempigliatura da leggere |
| …809,817 | — | Switch rete | `NOBLE` `JAPAN` (teal) | panel rocker | — | Power switch | — |
| …840,841 | — | Presa/cavo rete | cavo fisso + guarnizione | — | AC 220V 50/60Hz | Ingresso rete | Retro: "AC 220V" |

## Passivi — valori letti finora (append progressivo)

| Foto | Ref | Tipo | Sigla/Marking | Package | Valore | Funzione | Note |
|---|---|---|---|---|---|---|---|
| …804,806,807,810 | — | Cap ceramico | arancio `104` `25V`? | disc | 100 nF | Decoupling lato saldature (vicino QFP) | 25V da verificare |
| …840 | — | Cap X2 | `.0022µF` | film | 2.2 nF | (vedi sopra) | — |
| …850,851,856,867,868 | — | Elettrolitico | nero `…H02 8510` | radiale | da verificare | PSU filtro | — |
| …878* | — | Elettrolitico | nero grande `+ …µ …35V` (470µF 35V?) | radiale grande | da verificare | Rail PSU | LETTURA DA CONFERMARE |
| …850,867,868 | — | Elettrolitico | blu chiaro grande | radiale grande | da verificare | Rail PSU | — |
| …853,855,864,865,866 | — | Elettrolitici blu | `…50V`, `56µ`? | radiale S | 56 µF / 50 V? | Filtri locali | Lettura parziale |
| …853,855,857,858,863 | — | Cap assiale verde | `…352F`/`…252F` (serigrafia bianca) | assiale | da verificare | ? (film o induttanza?) | IDENTITÀ DA CHIARIRE — croppare |
| …851,856,867,868,869 | — | Cap film teal | `223` | assiale/dip | 22 nF | filtro | — |
| …859,861,862,865,866 | — | Cap film giallo | `102` / `102K`? / `472M`? | dip | 1-4.7 nF? | filtro | Letture parziali |
| …849 | — | Diodi vetro | DO-35 con banda catodo | — | segnale (1N4148-class) | — | tipo non leggibile |
| — | — | Resistori assiale | bande colore visibili ma non decodificabili a questa risoluzione | assiale | da verificare | — | DECODIFICA DA CROP INGRANDITI (F1 mirato) |

## Ricerche datasheet (append dopo OGNI ricerca)

| Ricerca | Esito |
|---|---|
| TC40H000P | **OK** — Toshiba C²MOS, quad 2-input NAND (equiv. 7400), datasheet 3pp. alldatasheet/datasheet4u; serie TC40H = tra 74C e 74HC |
| M3764-15RS / MSM3764 | **OK** — OKI 64K×1 DRAM, fast-page, 150 ns, DIP-16, +5V (1983 OKI Memory Databook; ace4parts; omo-ic) |
| OKI M60351 | **KO (confermato)** — ricerche EN/JP + alldatasheet.com/search M60351 → 0 risultati OKI (solo Vishay M6035x). **LSI custom da maschera** per Tokyo Trading. Ipotesi: controller delay + conversione A/D-D/A integrate → "da verificare" |
| M5224P | **OK** — Mitsubishi QUAD SINGLE POWER SUPPLY op-amp (classe LM324), DIP-14, Vsup max 18V, alldatasheet 108375 |
| M5221 / M5221P | **OK** — Mitsubishi DUAL J-FET INPUT op-amp (classe TL072), DIP-8, GBW 3 MHz, slew 13 V/µs, bias 0.4 nA, Vsup ±15V nominali, datasheet4u 1307009 |
| NE571N | **OK** — Signetics/Philips DUAL COMPANDOR (compressor+expandor): rectifier RMS + cella G + op-amp per canale; DIP-16; app note ON Semi/Philips: usato per "bucket brigade e digital audio delay"; attack/release = 10k×CRECT |
| HD14066BP | (conferma implicita) Hitachi quad bilateral switch CMOS eq. 4066 — datasheet reperibile su richiesta |
| JRC4558D | (conferma implicita) New Japan Radio 4558 dual op-amp — datasheet reperibile |

### Correzioni/aggiunte da ricerche F2
- U8 M5224P → funzione: op-amp quad alimentazione singola (probabile stage a alimentazione singola/mediatrice riferimento VREF).
- U9 M5221 → JFET dual (ingresso alta impedenza → stage ingresso/buffer candidato).
- NE571 → NON è "solo AGC": è compandor completo; nel DDX-777 probabilmente compressore nel path delay + expandor in feedback (o viceversa) per dynamic range della memoria DRAM.

## Trascrizioni datasheet (indice) — sessione 13f (04/10/2026)

Una trascrizione per PDF in `Prep\Datasheets\<basename>.md` (stesso nome/case del PDF): claim utente controverificate (✅/⚠️/➕ con pagina), dati integrati, grafici letti, nota modello DSP.

| IC | U-ref | Trascrizione | PDF | Esito controverifica | Data |
|---|---|---|---|---|---|
| OKI MSM3764A | U1–U3 (prov.) | `oki_msm3764.md` | `oki_msm3764.pdf` (scansione, 18 pp) | ✅ 4/5 (150 ns, refresh 128/2ms, pin8=Vcc); ⚠️ 192 Kbit = 3 chip, pin1=Vss → NC (Vss=pin16, refuso datasheet) | 04/10/2026 |
| Panasonic AN7815 | U17 | `panasonic_an7815.md` | `panasonic_an7815.pdf` (testo, 11 pp) | ✅ 5/5 (15V/1A, 17,5-30V, 14,4-15,6V, 90 µV, 54 dB) | 04/10/2026 |
| TI LM311N | U10 | `ti_lm311n.md` | `ti_lm311n.pdf` (testo, 42 pp) | ✅ 3/3 (115/165 ns, Vio 2-7,5 mV, uso Oscillators) | 04/10/2026 |
| Toshiba 2SK118 | Q1 | `toshiba_2sk118.md` | `toshiba_2sk118.pdf` (testo, 4 pp) | ✅ 4/5 (gruppi R/O/Y/GR, NF 0,5 dB, Ciss 8,2 pF, Yfs 1,2 mS); ⚠️ equazione quadratica non stampata (parabola confermata nei grafici) | 04/10/2026 |
| Toshiba TC40H000P | U5 | `toshiba_tc40h000p.md` | `toshiba_tc40h000p.pdf` (scansione, 3 pp) | ✅ 2/2 (VIH 4,0/VIL 1,0; tP 18/27 ns) | 04/10/2026 |
| Hitachi HD14066BP | U6 | `hitachi_hd14066bp.md` | `hitachi_hd14066bp.pdf` (scansione, 2 pp) | ❌ Ron 100-300 Ω **non verificabile**: il file è la selection guide della serie HD14000B/UB, non il datasheet del 4066; ✅ funzione quad switch | 04/10/2026 |
| JRC NJM4558D | U11–U16 (×6-7) | `jrc_4558d.md` | `jrc_4558d.pdf` (testo, 4 pp) | ✅ 2/2 (SR 1 V/µs, GB 3 MHz); ➕ 6-7 esemplari = dato di sistema | 04/10/2026 |
| Mitsubishi M5221 | U9 | `mitsubishi_m5221.md` | `mitsubishi_m5221.pdf` (scansione, 4 pp) | ✅ 3/3 (Rin 1000 MΩ, SR 13 V/µs, THD 0,007 % @40 dB) | 04/10/2026 |
| Mitsubishi M5224P | U8 | `mitsubishi_m5224p.md` | `mitsubishi_m5224p.pdf` (scansione, 6 pp) | ✅ 3/3 (classe C >100 µA, pull-up 3 kΩ, THD ~100×) | 04/10/2026 |
| Philips NE570N (fam. NE570/571) | U7 (NE571N) | `NE570N.md` | `NE570N.PDF` (scansione, 7 pp) | ✅ 14/14 claim (Vref 1,8 V, R1-R4, τ=10k×CRECT, I1/I2, IG, IOUT, +8 dBm, THD, 250 µA, 741/1 MHz, SR ±5, ripple→H3); ➕ ordine catena THD = inferenza di sistema | 04/10/2026 |

Metodo: PDF a strato testuale → estrazione PyMuPDF + lettura visiva tabelle/grafici chiave; scansioni → render 300 DPI + OCR doppio motore (rapidocr PP-OCRv3 + WinRT en-US) + lettura visiva (arbitro). Cache: `%TEMP%\opencode\ddx_ocr\`; note di verifica complete: `%TEMP%\opencode\ddx_notes.md`. Nessun valore nei file di sessione è stato smentito → nessun fix incrociato; arricchimento L23 (CRECT tip circuito test 2,2 µF) in `04_lacune.md`.

## Letture dirette + crop sessione 2 (append)

| Foto | Ref | Tipo | Sigla/Marking | Package | Valore | Funzione | Note |
|---|---|---|---|---|---|---|---|
| …867 (crop 867_rams) | Uxx | Regolatore | `AN7815` + `5E2` (Panasonic) | TO-220 | **+15 V — CONFERMATO leggibile** | Rail +15V analogico | Radiatore/bracket; adiacente: TC40H000P ("000P"), 3 resistenze (bande rosse-marroni, decodifica non sicura), elettrolitico blu, connettore nero multipin |
| …867 (crop 867_top) | — | DRAM ×3 (NO 4ª) | coda `…RS 238` = tail di `44238` | DIP-16 | — | — | **Correzione: nessuna 4ª DRAM** — era lo stesso cluster visto da altra angolazione (3× M3764 confermati in 844) |
| …867 (crop 867_top) | — | Trimpot | crema/bianco tondo | trimmer | da verificare | offset/clock | Stesso bianco tondo visibile in 844_ax |
| …867 (crop 867_top) | — | Diodi | 2 vetro (1 con banda blu → zener?) + 1 vetro rame | DO-35/DO-41 | da verificare | riferimenti | — |
| …844 (lettura singola) | — | PANORAMICA digitale | 3× `M3764-15RS OKI JAPAN 44238`, `TC40H000P 8539H`, `M5224P 4507` ×2, `HD14066BP 4M2 7`, `M5221 4504`, `4558D JRC 5061`, DIP-8 `LM31?…8532` | misto | — | Sezione digitale + I/O | foto migliore per topografia digitale: DRAM cluster in basso-sx, TC40H centro, 14066 dx, LED chiari ×2, TO-92, jacks retro alto-sx, rotary switch basso-dx, pot `…05 C` basso |
| …844 (crop 844_lm31) | U10 (prov.) | Comparatore | riga sx `…M9532`/`8532`? riga dx `LM 31?` | DIP-8 | — | Prob. **LM311N** (PEAK LED) | Lettura confermata parzialmente: `LM`+`31x`+date `8532`; resta PROBABILE (survey: "LM 31N") — da confermare con altra foto/angolo |
| …844 (crop 844_lm31/trim) | — | Trimpot | giallo `202` o `203` | trimmer | 2 kΩ o 20 kΩ? | bias/clock | Diverso o stesso del giallo di 867? DA VERIFICARE |
| …844 (crop 844_trim) | — | Cap ceramico | `TC40H000P` + `8539H` date code | — | — | — | Conferma logica glue: 1985 wk39 |
| …844 (crop 844_cap) | — | Elettrolitico | nero: `+ G1? 2 / W02? / 8510` | radiale L | **da verificare** (8510 = date code) | PSU filtro | Accanto: azzurro grande (valore n/v) + bracket grigio con vite + M5224P 4507 |
| …844 (crop 844_ax) | — | Cap assiale teal | parziale: `…W…` / `1µ…`? / `…F`? | assiale | **da verificare** (1 µF?) | accoppiamento/filtro | IDENTITÀ ancora incerta nonostante crop; stessi "352F/252F" dei survey |
| …844 (crop 844_ax) | — | Resistori ×2 | bande rosse-marroni (luce calda, decodifica non sicura) | assiale | 220R? 2.2k? | vicino TC40H/DRAM | DA VERIFICARE con altra foto |
| …844 (crop 844_ax) | — | Diodo vetro scuro | corpo nero/vetro rame | DO-35 | da verificare | segnale | + 3 cap arancio disc |
| …845 (crop 845_bot) | — | CONFERME | `NE571N K8436`, `4558D JRC 5061`, `4558D JRC 5200` | DIP-16/8 | — | — | 845 NON contiene LM31 → foto del LM31 = 844. Retro pot: marca `…05 C` (M50kΩB). Rotary switch con fili arcobaleno |
| …840 (crop 840_fuse) | — | Fusibile | nessuna stampa visibile | 5×20 | rating NON leggibile | rete | Solo clip + fili |
| …884 (lettura singola) | — | Angolo rete | fusibile holder nero + filtro `A91S2 3A/? 250V~ A2H4` + switch `NOBLE` + X2 maroon + retro pot | chassis | — | Mains entry | **884 NON è 2° regolatore**: nessun TO-220 qui |
| …884 (crop 884_fuse) | — | Fusibile | nessun rating stampato | 5×20 | **non determinabile da foto** | rete | Misura fisica necessaria |
| …874 (crop 874_res) | — | Campo 4558 | `4558D JRC 5061` + `4558D JRC 5200` + ~20 resistori a bande nitide + diodo vetro + cap film giallo-verde | — | decodifica bande: IN CORSO (luce variabile) | mixer/filtri | Buona base per decodifica RC se necessaria |
| …878 (crop reg/caps/topram) | — | (box errati) | contenuti non corrispondenti alle stime | — | — | — | DA RICRUD con rilettura 878; cap grande n/v; regolatore già confermato via 867 |

### Correzioni da letture sessione 2
- **4ª DRAM → NON esistente** (era coda `44238`). Totale DRAM = 3 (U1-U3).
- **884 = angolo rete**, non secondo regolatore.
- **Foto del DIP-8 "LM31x" = …844** (non 845).
- Rating fusibile e valori elettrolitici principali: **non leggibili** con le foto disponibili.

### Aperti prima del checkpoint
- **+5V digitale**: origine NON individuata (DRAM/logica richiedono +5V; unico regolatore visibile = AN7815 +15V). Cercare eventuale 7805 su staffa/lato saldature in foto PSU residue (…869, 877, 870).
- Datasheet residui: HD14066, JRC4558, LM311 (se confermato).

## Dati da misure dirette utente (append — fonte: misure su circuito, sessione utente)

| Voce | Dato | Note |
|---|---|---|
| TC40H000P (U5) | **4,71 V** misurati pin 14 (Vcc) vs pin 7 (GND) | Rail +5V digitale funzionante; caduta su pista |
| M3764-15RS (U1-U3) | **4,90 V** misurati pin 8 (Vcc) vs pin 1 (Vss) | Idem |
| +15V analogico | da AN7815 (U17, TO-220 su dissipatore; logo ▲ Panasonic, codice lotto `5E2`/`552` — secondario incerto) | Alimenta M5224P, M5221, NE571, JRC4558 |
| +5V digitale | **regolatore DISCRETO**: zener ~5,1V (misurato 4,8V) + transistor di passaggio + elettrolitico 1 µF 50 V | Alimenta DRAM, TC40H000P, M60351 (presunto) → **U18** |
| Nodo intermedio | **7,4 V** misurati sul transistor di passaggio | Presunto ingresso del regolatore discreto |
| Regolatore discreto | vedi U18 sotto | — |

## Componenti nuovi da misure/identificazioni utente (append)

| Foto | Ref | Tipo | Sigla/Marking | Package | Valore | Funzione | Note |
|---|---|---|---|---|---|---|---|
| (zona timing, foto 844) | U18 (prov.) | Regolatore +5V discreto | zener ~5,1V (mis. 4,8V) + transistor passaggio + elettrolitico `1 µF 50 V` | discreto | +5 V uscita; 7,4 V al nodo in ingresso | Rail +5V digitale | Circuito discreto (non IC); misure utente |
| …844 (crop) | U10 (prov.) | Comparatore | **`M8532 LM 311N`** (data code 8532) | DIP-8 | — | **LM311N**: osc. a rilassamento/VCO **o** rivelatore picco PEAK **o** ADC 1-bit (scenari in 03_blocchi.md) | Sigla COMPLETA confermata da utente; zona timing vicino U5 |
| zona timing | — | Cap poliestere | timing | film assiale | **1000 pF (1 nF)** | Costante di tempo LM311 | Blocco Clock/Timing |
| zona timing | — | Trimpot | "vite bianca" (tondo crema) | trimmer | calibrazione frequenza clock | Blocco Clock/Timing | Identità chiarita: è un potenziometro di calibrazione |
| zona timing | — | Elettrolitici ×2 | — | radiale S | **100 µF 10 V** | Filtro rail +5V (nella zona timing) | — |
| zona timing | — | Diodi ×3 | — | DO-35 | da identificare | clamp / regolazione / parte del reg. +5V | — |
| (zona alimentazione) | — | Induttore assiale teal | `ALN 252F` (letto anche "352F" dai survey) | assiale | probabile **2,5 mH** (25×10²) — IPOTESI | filtro di alimentazione | Identità risolta: induttore, non cap |
| (zona alimentazione) | — | Cap assiale azzurro | — | assiale | probabile poliestere | filtro | — |
| zona clock (deduzione utente) | — | (vedi sopra) | LM311N + 1000pF + trimmer + 2×100µF 10V + 3 diodi | blocco | — | **Clock/Timing** — cuore del tempo di delay (f campionamento, max delay, banda) | Vicino a U5 TC40H000P |

### Correzioni sessione utente
- **+5V digitale: ESISTE e misurato** (non più "non individuato"): generato da regolatore discreto (U18), non da 7805.
- U10: sigla completa `M8532 LM 311N` (LM311N), non "probabile LM311" — ora **confermata**.
- `ALN/352F` assiale = **induttore 2,5 mH** (ipotesi valore), non condensatore.
- Trimpot "vite bianca" = potenziometro di calibrazione clock.

## Letture dirette sessione 3 (809, 869, 877) + F2 NE571 (append)

| Foto | Ref | Tipo | Sigla/Marking | Package | Valore | Funzione | Note |
|---|---|---|---|---|---|---|---|
| …809 (lettura diretta) | — | Switch rete | `NOBLE` `JAPAN` (teal) | panel rocker | — | POWER (primario) | **CONFERMATO leggibile**; cap snubber rossa sui morsetti; fusibile a molla accanto; trasformatore a dx. Ordine serie switch/fusibile = [P] |
| …869 (lettura diretta) | U17 | Regolatore | `▲552` `AN7815` (Panasonic) | TO-220 | +15 V | Rail analogico | Codice lotto **552** confermato (coerente con misura utente) |
| …869 | — | Trimpot | giallo `203` | trimmer | **20 kΩ** | calibrazione (clock/offset) | **Confermato leggibile** (risolve 202 vs 203 → 203) |
| …869 | — | Induttore assiale | teal `252` | assiale | prob. 2,5 mH [I] | filtro alimentazione | **"252" confermato** (survey "352F" = lettura errata) |
| …869 | U1-U3 | DRAM ×3 | `M3764-15RS OKI JAPAN 44238` | DIP-16 | 64K×1 | memoria delay | ×3 confermate; nessuna 4ª |
| …869 | U10 | Comparatore | `M8532` `LM` (riga2) | DIP-8 | — | **LM311N** (clock osc. — scenario A) | Sigla confermata |
| …869 | U8 | Op-amp quad | `M5224P 4507` | DIP-14 | — | — | + TC40H000P 8539H, elettrolitici `…8510`/`…8502`, pot retro `M50kΩB`; **nessun 79xx/2° regolatore** |
| …877 (lettura diretta) | — | Plancia analogica | NE571N K8436, 4558D JRC (codes 5201/0661/1650/5207/5061…), M5221 4504, HD14066BP 4M2 7, TC40H000P, lenti chiare ×2 | misto | — | — | **nessun regolatore negativo** in tutta la plancia; pot M50kΩB ×5 + rotary |
| F2: NE571/SA571 | — | Datasheet | ON Semi/Philips (SA571-d.pdf; app note NE570/571) | — | — | — | **Single supply 6-18 V, VREF interno 1,8 V** per nodi di somma; "intended for use in single power supply systems" → coerente con assenza −15V |

### Correzioni/decisioni sessione 3
- Scenario LM311: **A CONFERMATO** (oscillatore clock); frase utente "LED PEAK collegato al LM311" = **ritirata, scenario C scartato** → driver PEAK = sezione libera M5224P/M5221 [I → L18].
- −15V: **assente secondo foto** (nessun 79xx in 83 foto) → architettura single-supply +15V/GND [C-foto].

## Identificazioni componenti nuove (verifiche visive utente — append)

| Ref | Tipo | Sigla/Marking | Valore/package | Funzione | Note |
|---|---|---|---|---|---|
| C5 (prov.) | Cap poliestere assiale | `273J50` = 27×10³ pF, J=±5%, 50 V | **27 nF / 50 V** assiale | filtro o accoppiamento zona ALN/timing | **CORREZIONE: `273J50` NON è un regolatore, è un CONDENSATORE** (nessun riferimento al codice era presente nei file progetto) |
| Q1 (prov.) | JFET N basso rumore | `K118` = **2SK118** (Toshiba) | TO-92; V(BR)GDS −50 V, I(D) 10 mA, 100 mW, NF 0,5 dB tip. | buffer alta impedenza o S&H prima di ADC [P-tesi utente] | tra pot LEVEL e M60351 |
| Q2 (prov.) | JFET P o PNP | `J43P55` → probabile **2SJ43** | da confermare | complementare con Q1: coppia push-pull / commutazione S&H [I] | "P55" potrebbe essere lotto/variante → **da confermare con foto macro (L20)**; zona vicina ALN 252F + C5 27 nF → possibile filtro anti-alias/campionamento [I] |
| U18 (nota) | Regolatore +5 V | componente **TO-92** vicino AN7815, sigla non letta con certezza | discreto | +5 V digitale | misure 4,71 V (TC40H) e 4,90 V (DRAM) confermano rail funzionante; **sigla da confermare (L22)** |

### Correzioni data code (sessione utente — non modificare le righe sopra)
Sigla produttore e data code vanno separati:
- U1-U3: `M3764-15RS` (OKI), data code **44238** (1984 wk23)
- U5: `TC40H000P` (Toshiba), data code **8539H** (1985 wk39)
- U7: `NE571N` (Signetics), data code **K8436** (1984 wk36)
- U8: `M5224P` (Mitsubishi), data code **4507**
- U9: `M5221` (Mitsubishi), data code **4504**
- U10: **`LM311N`** (TI o equivalente) — NON "M8532"; data code **8532** (1985 wk32); "M8532 LM 311N" = marking completo letto in foto
- U17: `AN7815` (Panasonic), data code **552**
- U18 = circuito DISCRETO (transistor + zener + C 1 µF), non un IC

### Mappa Ref F4 → evidenze in raw (nota: le righe con queste Ref esistono solo in components.md; qui restano le evidenze)
| Ref in components.md | Evidenza in raw / foto |
|---|---|
| C1 (1000 pF) | cap poliestere gruppo timing (trimmer `203` + cap) — …844, …869 |
| C2, C3 (100 µF 10 V ×2) | elettrolitici zona timing +5 V — …844, …869 (valori da misure utente) |
| C4 (1 µF 50 V) | elettrolitico uscita regolatore U18 — …869 |
| C6 (poliestere arancione) | cap disc zona QFP lato saldature — …804, …807, …810 |
| R1-R4 (timing pull-up/down) | resistori zona U5/U10 — …844, …869 |
| R5-R6 (partitore mid-rail) | resistenza campo op-amp — …874, …877 |
| R7+ (carici NE571/4558) | resistenza campo — …845, …874, …877 |
| D1-D3 (diodi timing) | diodi vetro DO-35 zona timing/U18 — …844, …845 |
| D4 (zener 5,1 V; mis. 4,8 V) | zener zona AN7815 — …869 (misura utente) |
| D5 (protezione) | diodo segnale zona rail/I-O — …869, …877 |
| U17 | = righe raw con "Uxx Regolatore AN7815" — …867, …868, …869 |
| U11-U16 (±1) | = riga raw "U11+" (4558D JRC) — …840, …845-846, …859-865, …871-874 |
| IND1 | = riga raw "Induttore assiale teal ALN 252F" — …855, …863 |
| Q1, Q2, C5, U18 | righe già appenate sopra (sessioni F4) ✓ |

## Sessione 9 — correzione package, L17 RISOLTA, strategia L5 (append)

- **Correzione applicata a riga 11**: U4 M60351 package `QFP-64 (≈16 pin/lato)` → **`QFP-56 (14 pin/lato)`** — conteggio pin verificato sulle nuove Closeup back (…6248/…6250/…6254: 14 pin/lato). Nota tecnica: QFP-56 con bus 16-18 piste verso DRAM è coerente con il multiplexing indirizzi (fast-page: RAS + CAS) per 3 DRAM 64K×1.
- **Ricerca definitiva M60351**: 4 query mirate (EN/JP) → **0 datasheet, 0 riferimento commerciale**. Confermato: **LSI custom OKI per Tokyo Trading**. L5 resta aperta: chiudibile solo con misura su QFP-56 (oscilloscopio) o con la strategia Indizi A-F (tester) in `04_lacune.md`.
- **Test sessione 9 — configurazione NE571 → L17 RISOLTA**:
  - Pin 4 (INV IN 1) = sommatore virtual ground del compressore; pin 6 (OUT 1) → ADC M60351 (percorso forward)
  - Rete retroazione **FISSA: 46,1 kΩ** (≈ 47 kΩ E24) tra pin 4 e pin 6 — non varia con il pot FEEDBACK (0 → 46,1 kΩ; 10 → 46,1 kΩ)
  - Pot FEEDBACK = **reostato** tra VCC (pin 12) e pin 4 → bias DC / soglia companding, non feedback audio
  - Continuità: pin 4 ↔ jack INPUT (dry via R_in); pin 4 ↔ pot FEEDBACK
  - Pin 4 ↔ pin 12 = **855 Ω** (resistenza interna del chip, pot in parallelo)
  - Canale 2 spento (pin 11 OUT 2 = **0 V**) → unità mono; solo compressore, no expandore
- **Ipotesi 12 bit [I]** (fonte: utente): 3× DRAM 64K×1 = 192 Kbit → a 32 kHz ≈ 6 s teorici vs 512/1024 ms reali → oversampling o word seriali 12 bit; NE571 dbx-style tipico di delay 12 bit (maschera il rumore di quantizzazione); data code 1985 → 12 bit standard pro (8 bit obsoleti). Indizio F (ascolto: suono vicino a 12 bit) = forte ma non definitivo.
- **Nuove foto `Foto DSP/Closeup back/` (13 file `5904461077515276244`–`…256`, tutte lato saldature, letture singole sessione 9)**: serigrafia con **lettere di nodo A, B, C, D, E, F, G, H, K, L, M, N** (12 lettere, niente I/J); M60351 QFP-56 con fascio di piste verso DRAM/logica; **3 pad del pot FEEDBACK marcati a pallini rossi** (marcatura utente segnalata su …6252; pallini rilevati anche in …6253/…6254); pot con fili rossi/arancio al bordo scheda. Anche 2 file nella root `5904461077515276139` / `…140` (serie nuova, non classificati → inventario con `*`).
- Conteggio foto: 85 root + 13 closeup = **98 totali** (83 serie storica + 2 serie nuova in root + 13 closeup).

## Test utente (tester) — sessione 10 (append)

| Test | Percorso | Risultato | Conclusione |
|---|---|---|---|
| A | NE571 pin 6 → M60351 | **0 bip** | nessun collegamento diretto: **filtro anti-aliasing interposto** tra compressore e LSI |
| B | NE571 pin 4 → M60351 | 9 bip apparenti | = pin GND del QFP (test fuorviante, scartato) |
| D | TC40H pin 7 → M60351 | ~10 bip | = massa multi-pin QFP (coerente con B) |
| C, E, F | visivo rete DAC / VREF / ascolto | non eseguiti | — |

Chiusura L5: **NON DETERMINABILE senza oscilloscopio o analisi spettro** (conferma = gradini di quantizzazione sul pin DAC out, oppure SNR → bit effettivi). Ipotesi **12 bit [I]** forte per 5 indizi indipendenti (filtro anti-aliasing, compandor NE571 dbx-style, epoca 1985, DRAM 192 Kbit @32 kHz, ascolto); 8 bit non escluso ma meno probabile. Per modelli DSP: usare 12 bit come default documentando l'incertezza. Dettaglio in `04_lacune.md` (blocco L5, sessione 10). *→ superata dalla sessione 11, vedi sotto.*

## Sessione 11 — misure audio (append)

Fonte: test audio dell'utente in `Segnali_Test/` (15 WAV 96 kHz/32-bit float, generati da
`genera_segnali.py`). Valori riferiti dall'utente.

| Test | Contenuto | Risultato |
|---|---|---|
| T1 | delay | 64×1 = **66 ms**, 256×1 = **262 ms**, 512×1 = **528 ms**, 512×0,5 = **247 ms**, 512×2 = **960 ms** (errori +3,1% / +2,3% / +3,1% / −3,5% / −6,25%) |
| T2 | banda | risposta **piatta fino a ~15 kHz**, taglio a **15-16 kHz** |
| T3 | rumore | fondo **−67 dBFS** |
| T4/T8/T9 | THD | distorsione ricondotta al **companding NE571** |
| T5 | aliasing | **nessun aliasing** |
| T6 | curva di trasferimento | **companding attivo** |

**Deduzioni (sessione 11):**

- **12 bit** confermati: −67 dBFS è il rumore di fondo atteso a 12 bit (8 bit darebbe ~−53 dBFS)
- **f_camp ≈ 32 kHz**: 192 Kbit ÷ 12 bit = 16384 word ÷ 528 ms ≈ 31 kHz effettivi (32 kHz nominali)
- **bias clock +3%**: trimmer `203` fissa il VCO ~3% oltre la nominale
- banda ~15 kHz coerente con f_camp 31-32 kHz + filtro anti-aliasing

→ `04_lacune.md`: L1, L5, L12, L13 → **RISOLTE**. `components.md` (U4) e `03_blocchi.md` (§3 + coerenza §2/§4) aggiornati.

## Sessione 12 — Datasheet NE570N (append)

Fonte: estrazione utente da `Prep\NE570N.PDF` (datasheet scansionato, non leggibile via OCR).
Contenuto numerico riportato dall'utente:

| Parametro | Valore | Note |
|---|---|---|
| VREF | 1,8 V | riferimento interno |
| IB | 140 µA | corrente di base |
| I1 / I2 | 140 / 280 µA | correnti rectifier |
| R1–R4 | 10 kΩ / 20 kΩ / 20 kΩ / 30 kΩ | rete interna detector |
| τ attack/release | 10 kΩ × CRECT | costanti tempo = 10 kΩ × condensatore del rectifier |
| THD gain cell | 0,3–1,0% (untrimmed); 0,05–0,1% (trimmed) | a riposo, specifica del datasheet |
| THD a 0 dBm con offset 1 mV | 0,34%, **2ª armonica** | → meccanismo H2 ∝ offset × VIN (Meccanismo A plugin) |
| Max input rectifier | 250 µA | |
| Saturazione gain cell | **+8 dBm** | → Opzione C plugin (solo documentata, non parametrizzata) |
| Op-amp interni | 1 MHz (classe 741), slew ±5 V/µs | |
| Output | ±20 mA | |

**Pinout NE570N DIP-16 (corretto, sessione 12)** — diversi dai pin usati nelle sessioni 9-11:

| Pin | Funzione |
|---|---|
| 1 | RECTIFIER CAPACITOR 1 (→ C_RECT, lacuna L23) |
| 4 | GND |
| 5 | INVERTED INPUT 1 (sommatore compressore) |
| 7 | OUTPUT 1 (→ ADC M60351) |
| 8/9 | THRESHOLD TRIM (THD trim) |
| 12 | INVERTED INPUT 2 (canale 2) |
| 13 | VCC |
| 14 | OUTPUT 2 |

**Mapping rispetto alle sessioni precedenti: shift +1 (vecchio N = nuovo N+1)** — unico mapping
coerente con tutte le 7 misure della sessione 9 (R_f 46,1 kΩ tra 5↔7; pot FEEDBACK reostato 13↔5;
canale 2 off = pin 12 a 0 V; 5↔13 = 855 Ω; VCC = pin 13). L'ipotesi alternativa (lato sinistro
invariato, destro ribaltato) fallisce su "vecchio pin 4 ↔ jack INPUT" (nuovo 4 = GND). Stato:
**ipotesi forte, da confermare con 3 test rapidi quando l'unità sarà accessibile** (vedi L17,
04_lacune.md): pin 4 ≈ 0 V, pin 5 ≈ 1,8 V, pin 13 ≈ 13-15 V.

**Implicazioni per il modello (decisioni sessione 12):**

- Meccanismo A (kVos = 0,0079): H2 da offset VOS gain cell su `dry²` post-mix — calibrato su T4
  (H2 1 kHz = 0,0308% vs HW 0,0311%, +0,1 dB; H2 10 kHz = 0,0349% vs 0,0345%).
- Meccanismo B (kLo = 0,0): crossover H3 < 500 Hz implementato ma scollegato — la taratura su T4
  dà 0 (l'H3 a bassa banda è già fornito dalla dinamica del compressore: baseline 0,42% vs HW 0,32%).
- Opzione C (+8 dBm): solo documentata — non verificabile (uscita DDX satura in REW a −20 dBFS).
- **THD trim (pin 8/9)**: il THD HW a 10 kHz = 0,035% è sotto la specifica trimmed (0,05–0,1%) →
  la cella è probabilmente trimmata; nessuna conseguenza sul modello.
- **C_RECT (L23)**: τ back-calc dal detector del modello (attack 8 ms / release 60 ms) →
  C_RECT ≈ 0,8–6 µF (τ = 10 kΩ × C_RECT). Candidati in foto …845: elettrolitico radiale blu in
  alto-sinistra del NE571 + condensatori film a destra; C5 27 nF esclusa (zona ALN/timing).

**Armoniche HW misurate (T4, sessione 12, FFT 5 segmenti 2^20):**

| f | A1 (dBFS) | H2 | H3 | H4 | H5 | THD |
|---|---|---|---|---|---|---|
| 100 Hz | −16,2 | −54,7 dB (0,18%) | **−50,9 dB (0,32%)** | −69,3 | −69,2 | 0,343% |
| 1 kHz | −14,0 | **−70,3 dB (0,0311%)** | −77,9 | −94,6 | −96,8 | 0,0332% |
| 10 kHz | −19,4 | **−69,3 dB (0,0345%)** | −81,3 | −97,0 | — | 0,0352% |

Lettura chiave: H2% costante in banda (0,031% a 1 kHz, 0,0345% a 10 kHz) nonostante A1 cali di
5,4 dB → H2 segue il livello di **ingresso**, non del mix → Meccanismo A applicato su `dry²`.
A 100 Hz H3 > H2 → "crossover" a bassa banda (fornito nel modello dalla dinamica del compressore,
non da un meccanismo dedicato).
