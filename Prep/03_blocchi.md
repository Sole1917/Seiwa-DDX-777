# DDX-777 — Architettura a blocchi (F3)

Legenda evidenze:
- **[C]** = confermato da foto/misure
- **[P]** = presunto (deduzione forte da componenti/posizione)
- **[I]** = ipotesi (da verificare → vedi `04_lacune.md`)

---

## 1. Alimentazione

```
AC 220V 50/60Hz [C]
   │
   ├─ Fusibile 5×20 (rating non leggibile) [C — 840, 884]
   ├─ Filtro EMI A91S2 250V~ [C — 840, 884]
   ├─ Switch NOBLE (POWER) [C — 809: "NOBLE JAPAN" leggibile sul
   │    primario, cap snubber sui morsetti; ordine serie con
   │    fusibile = [P]]
   └─ Trasformatore EI (secondari multipli; stempigliatura da leggere) [C]
         │
         ├─ rettifico+filtro ──► nodo ~7,4 V [C-misura]
         │                          │
         │                     U18: regolatore DISCRETO +5V
         │                     (zener 5,1V mis. 4,8V + transistor
         │                      di passaggio + C 1µF 50V) [C-misura]
         │                          │
         │                          ▼
         │                     +5 V DIGITALE rail [C-misura:
         │                     TC40H pin14=4,71V; DRAM pin8=4,90V]
         │                          ├─ U1-U3 DRAM M3764 [C]
         │                          ├─ U5 TC40H000P [C]
         │                          ├─ U4 M60351 [P]
         │                          ├─ U6 HD14066BP [P]
         │                          └─ U10 LM311N [P — da verificare]
         │
         └─ rettifico+filtro ──► U17 AN7815 (+15V) [C]
                                      │
                                      ▼
                                +15 V ANALOGICO [C]
                                      ├─ U8 M5224P [C]
                                      ├─ U9 M5221 [C]
                                      ├─ U7 NE571 [P]
                                      └─ U11..U16 JRC4558 [P]

GND comune [C]

Ramo −15 V: ASSENTE secondo foto — nessun 79xx/negative regulator in
nessuna delle 83 foto (angoli PSU letti: 840, 867, 869, 877, 878, 884) [C-foto].

Bias analogico in alimentazione SINGOLA +15V/GND:
  - U7 NE571: progettato per single supply (datasheet 6-18 V, VREF
    interno 1,8 V sui nodi di somma) [C-datasheet]
  - U8 M5224P: classe single-supply (equivalente LM324) [C-datasheet]
  - U11..U16 JRC4558 / U9 M5221: bias a mid-rail ~7,5 V
    (partitore + buffer presunto, forse sezione libera di U8) [I → L16]
```

---

## 2. Segnale audio (catena principale)

```
INPUT 1/4" −20dB [C]
   │
   ▼
LEVEL pot M50k (etichetta pannello "PEAK LEVEL" = pot, non il LED) [C]
   │
   ▼
Stage buffer/ingresso: U9 M5221 (op-amp JFET) [P] + **Q1 2SK118**
   (JFET a basso rumore, NF 0,5 dB): buffer ad alta impedenza tra
   LEVEL e l'ADC del M60351 [P-tesi utente → L21]
   │
   ▼
Compressore U7 NE571 — solo canale 1 [P] (pin 5 = sommatore virt.,
    │         pin 7 = OUT 1 → ADC; canale 2 spento: pin 12 = 0 V → L17)
    │         [numeri pin = pinout NE570N corretto, sessione 12]
   ▼
Zona campionamento (S&H): L1 ALN 252F + C5 27 nF + Q2
   J43P55 (2SJ43?) — possibile coppia complementare con Q1 o
   commutazione: ipotesi da verificare (L20/L21)
   │
   ▼
Filtro anti-aliasing (test A: 0 continuità diretta): configurazione
   presunta Sallen-Key o retroazione multipla con op-amp
   M5224P/M5221 [I]
   │
   ▼
A/D + controller  U4 M60351 (QFP-56, 14 pin/lato, lato saldature) [P]
   │         (conversioni integrate; DAC integrato in U4 →
   │          L5 RISOLTA: 12 bit (rumore −67 dBFS),
   │          f_camp ≈ 32 kHz [M11])
   ▼
Memoria  U1-U3 = 3× M3764-15RS 64K×1 (192 Kbit) [C]
   │         (modalità bit-serial/fast-page → [I])
   ▼
D/A: integrata in U4 [P] — nessun chip DAC discreto fra U1-U18 [C-foto]
   │         (nessun expandore in esercizio: canale 2 NE571 spento → L17)
   ├──► DELAY LEVEL pot M50k = livello WET [C+P]
   │                    │
   │                    ▼
   │              MIX OUT jack = dry + wet×DELAY LEVEL [P]
   │
    └─ FEEDBACK LEVEL pot M50k [C] ──► reostato di bias DC: VCC
                                        (NE571 pin 13) ↔ pin 5 =
                                        soglia companding — NON
                                        ricircolo audio [L17 RISOLTA]

DIRECT: dry path ──────────────────────► DIRECT out jack, separato [C+P]
HOLD switch frontale [C] ──► freeze (blocco indirizzi?) [I]

RAMO PEAK (parallelo, NON nel percorso audio):
  campione stadio ingresso ──► driver: sezione libera U8 M5224P
  o U9 M5221 come comparatore di soglia [I → L18] ──► LED PEAK [C]
   (NOT U10 — scenario C scartato: ritiro utente)
```

**Nota sessione 9 — L17 RISOLTA (topologia NE571 confermata):** canale 1 = compressore,
canale 2 spento (pin 11 OUT 2 = 0 V) → unità mono, nessun expandore in esercizio.
Retroazione del compressore: rete **FISSA 46,1 kΩ (≈47 kΩ E24)** tra pin 4 (INV IN 1)
e pin 6 (OUT 1) — non varia col pot (0 → 10: 46,1 kΩ costante). Pot FEEDBACK LEVEL =
reostato di bias DC tra VCC (pin 12) e pin 4 → sposta il punto di lavoro/soglia del
companding; il "feedback" percepito è effetto del companding, non ricircolo audio.
Continuità verificate: pin 4 ↔ jack INPUT, pin 4 ↔ pot FEEDBACK; pin 4 ↔ pin 12 = 855 Ω
(resistenza interna del chip, pot in parallelo). Dettaglio in `04_lacune.md` (L17).

**Nota sessione 12 — correzione pinout NE570N:** il datasheet (estrazione utente;
`02_componenti_raw.md` § "Sessione 12 — Datasheet NE570N") mostra un layout DIP-16 diverso
da quello usato in sessione 9: **mapping shift +1 (vecchio N = nuovo N+1)**, unico mapping
coerente con tutte le 7 misure. I numeri pin nel diagramma sopra sono aggiornati al pinout
corretto (vecchio 4 → **5** INV IN 1; vecchio 6 → **7** OUTPUT 1; vecchio 12 → **13** VCC;
vecchio 11 → **12** INV IN 2). La nota di sessione 9 sopra resta valida come registro storico
con le etichette vecchie. Stato: ipotesi forte, da confermare con 3 test rapidi (L17, `04_lacune.md`).

**Nota risoluzione — 12 bit [I] → L5:** 192 Kbit a 32 kHz ≈ 6 s teorici vs
512/1024 ms reali → oversampling o word seriali 12 bit; compandor NE571 dbx-style
tipico dei delay a 12 bit (maschera il rumore di quantizzazione); data code 1985 →
12 bit era lo standard pro (8 bit già obsoleto). Indizio F (ascolto dell'utente: suono
vicino a 12 bit) = forte ma non definitivo.
**Confermato 12 bit (sessione 11): rumore −67 dBFS.** → L5 **RISOLTA (sessione 11)**
(vedi `04_lacune.md`; la strategia Indizi A-F è stata superata dalle misure audio).

---

## 3. Clock / Timing (zona vicino U5 — aggiornamento utente)

Componenti del blocco [C]: U10 LM311N (data code 8532), cap poliestere **1000 pF**,
trimmer di calibrazione (vite bianca), 2× elettrolitico **100 µF 10 V**
(filtro +5V), 3 diodi (clamp/reg./parte di U18), U5 TC40H000P (NAND HCMOS).

```
              MODULATION SPEED/DEPTH pots [C]
                        │
                        ▼ [P]
   ┌────────── CLOCK / TIMING ──────────┐
   │  U10 LM311N + C 1000pF + trimmer  │
   │  (scenario scelto: VCO/rilassamento│──► U5 TC40H000P [P]
   │   — vedi §4)                       │     (glue logic / buffer / divisori)
   └────────────────────────────────────┘              │
                                                       ▼
                              RANGE mS rotary 1..512 [C] + DELAY TIME
                              FACTOR ×0.5..×2 [C] ── divisori [P]
                                                       │
                                                       ▼
                                        clock → U4 M60351 / U1-U3 [P]
                                        (f campionamento = tempo max
                                         delay, banda, carattere) [C-fisica]
```

**Nota sessione 11 — bias clock +3% (→ L1 RISOLTA):** le misure di delay danno errori
quasi costanti su tutto il RANGE (+3,1% a 64, +2,3% a 256, +3,1% a 512) → il trimmer `203`
fissa il VCO **~3% oltre la nominale**: f_camp effettiva **≈ 31 kHz** vs 32 kHz teoriche
(16384 word ÷ 528 ms). FACTOR ×2 → 960 ms (−6,25%), ×0,5 → 247 ms (−3,5%).

---

## 4. Scenari LM311N — scelta e evidenze

| Scen. | Ipotesi | Evidenze a favore | Evidenze contro |
|---|---|---|---|
| **A (CONFERMATO — scelta finale)** | **VCO / osc. a rilassamento**: clock varcabile in tensione | 1) **gruppo timing (trimmer `203` + C 1000 pF) accanto a U10 = prova fisica principale** [C-posizione]; 2) U10 adiacente a U5 (distribuzione clock); 3) MODULATION SPEED/DEPTH presuppone clock analogico varcabile (spiega wow/chorus); 4) RANGE/FACTOR come divisori digitali a valle; 5) conferma esplicita dell'utente (sessione 3) | non deducibile a pin-level dalle foto |
| B | Oscillatore a frequenza fissa (trimmer = solo calibrazione) | trimmer di calibrazione presente; clock stabile coerente con RANGE/FACTOR puramente digitali | MODULATION SPEED/DEPTH perderebbe effetto sul clock (a meno di modulazione indirizzi in U4) — alternativa aperta |
| **C — SCARTATA** | Rivelatore di picco (LED PEAK) | — (ritiro utente: "collegato al LM311" è stato un errore) | posizione fisica (zona timing, non stadio ingresso); driver PEAK = sezione libera di U8/U9 [I → L18] |

**Scelta:** Scenario A. Residuo **chiuso (sessione 11)**: clock unico con bias
trimmer +3%, f_camp ≈ 31-32 kHz (dettaglio in §3). → `04_lacune.md` L1 **RISOLTA**.

---

## 5. Controllo remoto / logica

```
REMOTE jacks: HOLD / MODULATION / DELAY [C]
   └─► logica (U4 e/o U5 + HD14066) [I] ──► freeze / mod on-off / tap delay?
HOLD frontale switch+LED [C]
POWER frontale switch+LED [C]
RANGE rotary 10 pos. + FACTOR pot [C] ──► divisori clock [P]
```
