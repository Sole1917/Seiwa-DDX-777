# Lacune / domande aperte (aggiornamento continuo)

Ogni voce: domanda → evidenza mancante → foto/misura necessaria.

| # | Domanda | Stato attuale | Serve |
|---|---|---|---|
| L1 | Residuo scenario LM311N (A **CONFERMATO**): VCO continuo o rilassamento? (C scartato — ritiro utente) | **RISOLTA (sessione 11)** — delay scalano proporzionalmente al RANGE (66/262/528 ms per 64/256/512) con errore quasi costante (~+3%) → sorgente clock unica + divisione digitale; f_clock ≈ 31 kHz con bias trimmer +3% | — (per il modello DSP conta f_camp ≈ 32 kHz nominali, regolabile ±3%) |
| L2 | Rating fusibile 5×20 | Nessuna stampa leggibile (…840, …884) | Misura fisica o macro del corpo del fusibile |
| L3 | Trasformatore: primario/secondari (valori V) | Nastro blu, morsetti rossi/blu visti; stempigliatura non inquadrata (…842) | Macro sul retro/stemma del trasformatore |
| L4 | Valori elettrolitici principali (nero "…8510", azzurro grande, 100µF×2 date) | Marchiature parziali | Macro per marca + µF/V (foto …844 zona ALN, …850, …867) |
| L5 | U4 M60351 — ADC/DAC interni? risoluzione 8 o 12 bit? | **RISOLTA (sessione 11)** — 12 bit confermati dalle misure: rumore di fondo **−67 dBFS** (coerente con 12 bit; 8 bit darebbe ~−53 dBFS); f_camp ≈ 32 kHz da delay 528 ms @512×1 | — (LSI custom OKI senza datasheet; dettaglio nel blocco sessione 11 sotto) |
| L6 | 4558D: 4558 o 4560? quanti esatti (6 o 7)? | Sigla "4558D" letta su più chip; alcuni survey "4560D" | Macro su ogni DIP-8 4558 del gruppo (…840, …871-874) |
| L7 | Alimentazione U6 HD14066 (+5V presunto) | 4066 è CMOS → coerente con +5V | Misura Vdd-GND su U6 |
| L8 | Alimentazione U10 LM311N (+5V probabile) | Datasheet LM311: supply ≥ ±2V (singolo 5V possibile ma limite) | Misura Vcc-GND su U10 |
| L9 | DRAM: 3 sole popolate? (footprint extra non usati?) | 3× M3764 viste in …844; nessuna 4ª | Foto …844/…854 zona DRAM: spazi vuoti per altri socket? |
| L10 | Valore esatto induttore `ALN 252F` | Ipotesi 2,5 mH | Macro altra foto (…855/…863) o misura L (LCR) |
| L11 | 3 diodi zona timing: zener + 2? | Funzione da identificare | Macro con marcatura corpo (…844/…845) |
| L12 | Capacità totale delay: 192 Kbit / f_camp = t_max? | **RISOLTA (sessione 11)** — 192 Kbit ÷ 12 bit = **16384 word**; ÷ 528 ms → **f_camp ≈ 31 kHz** (32 kHz nominali); t_max = 528 ms @512×1, 960 ms @512×2, 247 ms @512×0,5 | — |
| L13 | Banda audio / risoluzione (bit)? | **RISOLTA (sessione 11)** — banda **~15 kHz**, taglio **15-16 kHz**; risoluzione **12 bit** (rumore −67 dBFS); nessun aliasing (T5) | — |
| L14 | RC path audio (valori filtri/mixer) | Bande resistori nitide in …874 ma decodifica non completa | Decodifica bande da crop dedicati (se servono per components.md: riportare "da verificare") |
| L15 | Rail −15V: assente o non identificato? | **Assente secondo foto** (nessun 79xx in 83 foto; 869/877 riletti) → architettura single-supply +15V/GND [C-foto] | Conferma con misura → L16 |
| L16 | Conferma alimentazione singola: pin di alimentazione di U7 NE571 (V+/GND), U11-U16 4558 e U9 M5221 (V+/V−) | NE571 datasheet single-supply [C]; 4558/M5221 con bias mid-rail ~7,5 V [I] | **Misura**: tensioni sui pin (se V− = GND → conferma); cercare partitore+buffer mid-rail (sezione libera U8?) |
| L17 | Punto di reiniezione del FEEDBACK: post-expand → pre- o post-compressor? | **RISOLTA (sessione 9)** — nessun ricircolo audio: la topologia confermata è nella nota sotto la tabella; **correzione pinout NE570N in sessione 12 (shift +1, ipotesi forte da confermare)** — blocco sotto | 3 test rapidi di tensione quando l'unità è accessibile |
| L18 | Driver del LED PEAK: sezione libera di U8 M5224P o U9 M5221 come comparatore di soglia? | Scenario C (LM311) scartato [decisione utente]; nessuna traccia seguita | Foto tracce dal LED/cavo frontale al pin di un op-amp; oppure misura: quale pin segue la soglia del segnale |
| L19 | Identificazione **lenti chiare ×2** su scheda (…844, …877): LED bianchi, LED IR o fototransistor? | Viste in due punti diversi; nessuna marcatura, polarità ignota | Macro fronte + retro della lente; oppure misura: continuità/diodo-test sui 2 terminali |
| L20 | Conferma sigla **J43P55** (2SJ43 o PNP?) | Lettura utente non univoca; "P55" potrebbe essere codice di lotto/variante | **Foto macro** del corpo del componente (zona ALN 252F / C 27 nF) |
| L21 | Ruolo di Q1 2SK118 / Q2 2SJ43: buffer ingresso, sample & hold o commutazione? | Tesi utente: JFET basso rumore prima dell'ADC; coppia complementare prossima ad ALN+C27nF → possibile anti-aliasing/campionamento [I] | Foto macro posizione+tracce (lato saldature) o misura: segnale su gate/drain nel range audio |
| L22 | Conferma visiva U18: sigla e package del TO-92 vicino all'AN7815 | Regolatore +5 V funzionante (misure 4,71/4,90 V) ma sigla non letta | **Foto macro** del TO-92 in zona …869/…867 (accanto AN7815) |
| L23 | Valore C_RECT (capacità del rectifier NE570N, pin 1): τ attack/release = 10 kΩ × C_RECT | Back-calc dal detector del modello (attack 8 ms / release 60 ms) → **0,8–6 µF**. Candidati foto …845: elettrolitico radiale blu in alto-sinistra del NE571 + film a destra; C5 27 nF esclusa (zona ALN/timing). **+ Sessione 13f: τ = 10 kΩ × C_RECT confermata verbatim dal datasheet (p03); il circuito di test tipico usa 2,2 µF (τ = 22 ms) → preferire candidati ≈2,2 µF** | Identificazione visiva (bande/punti) o misura LCR/C |
| L24 | Valore R_in (jack INPUT → pin 5 INV IN 1) | Esistenza confermata da continuità, valore sconosciuto | **Serve per lo scaling analogico (0 dBm ↔ dBFS) della calibrazione assoluta del Meccanismo A (H2 ∝ VOS × VIN)**: misura ohmmetrica del percorso o lettura bande colore |
| L25 | Banda modello vs verifica: Virtual ADC 32 kHz (default ON Fase 2) sposta il −3 dB a 12,80 kHz (fuori da 14,5-16,5 kHz) e genera ripple 7,83 dB a 13,96 kHz; con `--no-virtual-adc` la banda passa (1,12 dB, 14,79 kHz) ma l'aliasing T5 fallisce (−27,6 vs HW −30,8 dBFS, target ≤ HW+3) | **Pre-esistente (Fase 2), non legato alla sessione 12** (i meccanismi A/B agiscono solo sul ramo mix; la banda usa wet/direct) | Decisione: ritoccare i filtri decimazione/interpolazione (cutoff ~15,5-15,8 kHz) o accettare i 2 FAIL come nota di congruenza. **Decisione utente sessione 12: documentare e proseguire** (report v4 §1) |

### L17 — RISOLTA (sessione 9)

Configurazione NE571 confermata con test finali (canale 1 = compressore, canale 2 spento):

- Pin 4 (INV IN 1) = sommatore virtual ground del compressore
- Pin 6 (OUT 1) → ADC M60351 (percorso forward)
- Rete di retroazione **FISSA: 46,1 kΩ** (≈ 47 kΩ E24) tra pin 4 e pin 6 — non varia ruotando il pot FEEDBACK (0 → 46,1 kΩ, 10 → 46,1 kΩ)
- Pot FEEDBACK = **reostato** tra VCC (pin 12) e pin 4, regola il bias DC del compressore, non il feedback audio
- Funzione: sposta il punto di lavoro del compressore (soglia companding)
- Il "feedback" percepito è effetto del companding, non ricircolo audio
- Continuità confermata: pin 4 ↔ jack INPUT (dry via R_in); pin 4 ↔ pot FEEDBACK (bias)
- Pin 4 ↔ pin 12 = 855 Ω (resistenza interna del chip, pot in parallelo)
- Canale 2 spento (pin 11 OUT 2 = 0 V) — unità mono; configurazione: solo compressore, no expandore

#### L17 — Sessione 12: correzione pinout NE570N (ipotesi forte, da confermare)

Il datasheet (estrazione utente sessione 12; **pinout riletto e confermato visivamente in sessione 13f**, vedi `Datasheets\NE570N.md` p01) mostra un pinout diverso
da quello usato nelle sessioni 9-11. Il mapping **shift +1 (vecchio N = nuovo N+1)** è l'unico
coerente con tutte le 7 misure della sessione 9:

| Misure sessione 9 (vecchie etichette) | Nuovo pin | Nuova etichetta |
|---|---|---|
| INV IN 1 (sommatore, → jack INPUT) | 5 | INVERTED INPUT 1 |
| OUTPUT 1 (→ ADC) | 7 | OUTPUT 1 |
| VCC (pot FEEDBACK reostato) | 13 | VCC |
| Canale 2 off (= 0 V) | 12 | INVERTED INPUT 2 |
| R_f 46,1 kΩ | 5 ↔ 7 | — |
| 855 Ω (pin 5↔13, pot in parallelo) | 5 ↔ 13 | — |

L'ipotesi alternativa (lato sinistro invariato, lato destro ribaltato) fallisce su
"vecchio pin 4 ↔ jack INPUT" (nuovo pin 4 = **GND**, non ingresso). Le misure restano valide,
solo rietichettate.

**Conferma (quando l'unità sarà accessibile)** — 3 test rapidi:
1. pin 4 (nuovo) ≈ 0 V (GND)
2. pin 5 ≈ 1,8 V (VREF/sommatore)
3. pin 13 ≈ 13-15 V (VCC)

### L5 — iter fino alla chiusura (sessione 10, superata dalla sessione 11)

**Stato al checkpoint sessione 10 (poi superato dalle misure della sessione 11):** la risoluzione non era deducibile da foto/tester. U4 M60351 = LSI custom OKI per Tokyo Trading (ricerca definitiva: 4 query EN/JP → 0 datasheet, 0 riferimento commerciale), package QFP-56 (14 pin/lato), ~10 pin di massa sul package.

- **Test A**: NE571 pin 6 → M60351 = **0 continuità** → tra compressore e LSI è inserito uno **stadio filtro anti-aliasing** (indizio indipendente)
- **Test B**: NE571 pin 4 → M60351 = 9 bip apparenti → in realtà pin GND del QFP (test fuorviante, scartato)
- **Test D**: TC40H pin 7 → M60351 = ~10 bip → massa multi-pin del QFP (coerente con B)
- Test C/E/F non eseguiti
- Nessun DAC/ADC discreto sul PCB (foto) → conversioni integrate nel LSI [C-foto]

**Ipotesi 12 bit [I] al checkpoint sessione 10 — 5 indizi indipendenti (poi confermata, sessione 11):** (1) stadio filtro anti-aliasing dedicato a valle del compressore; (2) compandor NE571 (architettura dbx-style); (3) epoca progetto (data code 1985); (4) memoria DRAM 192 Kbit @ ~32 kHz; (5) ascolto/registrazione dell'utente.

Esito sessione 10: per il modello DSP si usava **12 bit come default**, documentando l'incertezza.
Conferma con oscilloscopio (gradini di quantizzazione sul pin DAC out) o analisi spettro (SNR →
bit effettivi) → **ottenuta in sessione 11 con le misure audio**: rumore di fondo −67 dBFS,
f_camp ≈ 32 kHz, banda ~15 kHz (vedi blocco sopra).

### L1 / L5 / L12 / L13 — RISOLTE (sessione 11)

Misure audio eseguite dall'utente sui test in `Segnali_Test/` (15 WAV 96 kHz/32-bit float,
generati da `genera_segnali.py`). Dati e deduzioni in `02_componenti_raw.md`
(sezione "Sessione 11").

- **L5** — 12 bit confermati dal rumore di fondo **−67 dBFS** (8 bit darebbe ~−53 dBFS)
- **L12** — 192 Kbit ÷ 12 bit = 16384 word ÷ 528 ms → **f_camp ≈ 31 kHz** (32 kHz nominali);
  t_max = 528 ms @512×1, 960 ms @512×2, 247 ms @512×0,5
- **L13** — banda **~15 kHz**, taglio **15-16 kHz**, nessun aliasing (T5)
- **L1** — delay 66/262/528 ms su RANGE 64/256/512 con errore ~+3% costante
  → clock unico + divisori; bias del trimmer `203` = **+3%** sulla nominale
- **T4/T8/T9 + T6** — THD e curva di trasferimento ricondotte al **companding NE571** (attivo)

Nota: L1, L5, L12, L13 sono **RISOLTE** (sessione 11, misure audio): 12 bit, f_camp ≈ 31-32 kHz,
banda ~15 kHz con taglio 15-16 kHz, rumore −67 dBFS, bias clock +3%. Lacune rimaste aperte:
L2-L4, L6-L11, L14-L16, L18-L22 (foto/misure non audio).
