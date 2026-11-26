# Seiwa Digital Delay DDX-777 — Tabella componenti (F4)

**Seriale 006242 · Tokyo Trading Co. · Fonti:** letture dirette foto, survey
803-869 (una-per-una), misure e annotazioni utente.
**Ref:** la serigrafia non mostra designator → **Ref provvisorie** (U1..U18,
C1.., R1.., Q1.., D1..). Ordinamento: U → C → R → Q → D, numeri crescenti;
componenti senza Ref in **"Non assegnati"** (fine tabella).
**Affidabilità lettura:** Alta / Media / Probabile / Presunta.
Colonna **Foto** sempre presente; `…8xx` = `59022092777015918xx.jpg`.

---

## A. Alimentazione (rail)

| Rail | Tensione | Sorgente | Carichi principali | Evidenza |
|---|---|---|---|---|
| +15 V analogico | 15 V nominale | **U17 AN7815** (TO-220 su dissipatore) | U8 M5224P, U9 M5221, U7 NE571, U11-U16 4558 | [C] foto …867, …869 |
| +5 V digitale | **4,71-4,90 V misurati** | **U18 regolatore discreto (da confermare)**: componente TO-92 non identificato con certezza (sigla non letta); le misure 4,71 V (TC40H pin 14) e 4,90 V (DRAM pin 8) confermano rail +5 V funzionante | U1-U3, U5 [C]; U4, U6, U10 [P] | [C-misure utente] → L22 |
| Nodo intermedio | **7,4 V misurati** | rettifico → ingresso U18 | U18 in | [C-misura] |
| GND | 0 V | comune | tutti | [C] |
| −15 V | **ASSENTE** | nessun 79xx in 83 foto | — | [C-foto] → conferma L16 |
| Bias mid-rail | ~7,5 V (partitore + buffer) | presunto (forse sezione libera U8) | 4558, M5221 | [I → L16] |

---

## B. IC (Ref U)

*Tabella IC "pura" (U1-U16): i regolatori U17/U18 sono nella
sotto-tabella **B.1**.*

| Ref | Tipo | Sigla / Marking | Data code | Package | Funzione / Ruolo | Alimentazione | Affidabilità | Foto |
|---|---|---|---|---|---|---|---|---|
| U1-U3 | DRAM | `M3764-15RS` (OKI) ×3 | 44238 (1984 wk23) | DIP-16 | Memoria delay 64K×1, 150 ns fast-page (3 = 192 Kbit) | **+5 V (mis. 4,90 V)** | Alta | 844, 850, 854, 867, 869 |
| U4 | LSI custom | `OKI M60351` | 5102 (da interpretare) | QFP-56 (14 pin/lato) | LSI custom OKI per Tokyo Trading — **datasheet inesistente** (ricerca definitiva: 4 query EN/JP, 0 risultati); controller delay + A/D + D/A integrate; **L5/L12/L13 RISOLTE (sessione 11)**: risoluzione **12 bit confermata**, f_camp ≈ 31-32 kHz, banda ~15 kHz; montato lato saldature | +5 V (presunto) | Alta (sigla) / ruolo = Presunto | 804, 810, 868 |
| U5 | Logica | `TC40H000P` (Toshiba) | 8539H (1985 wk39) | DIP-14 | Quad NAND HCMOS — glue logic + oscillatore di clock (Blocco Clock/Timing) | **+5 V (mis. 4,71 V)** | Alta | 844, 867, 869 |
| U6 | Switch analogico | `HD14066BP` (Hitachi) | 4M2 7 | DIP-14 | Quad bilateral switch — routing/bypass/modulazione | +5 V (presunto → L7) | Alta | 844, 874 |
| U7 | Compandor | `NE571N` (Signetics) | K8436 (1984 wk36) | DIP-16 | Compressore + expandor (companding per il loop DRAM) | +15 V (presunto; datasheet single-supply OK) | Alta | 845, 872, 877 |
| U8 | Op-amp quad | `M5224P` (Mitsubishi) (×1 confermata; eventuale 2ª, sigla parziale) | 4507 | DIP-14 | Quad op-amp classe LM324 (single-supply): filtri/mixer/Vref | +15 V | Alta (1ª) / Media (2ª) | 844, 867, 869 |
| U9 | Op-amp dual | `M5221` (Mitsubishi) | 4504 | DIP-8 | Dual op-amp JFET (classe TL072) — buffer ingresso | +15 V | Alta | 844 |
| U10 | Oscillatore clock | `LM311N` (TI o equivalente) — marking completo `M8532 LM 311N` | 8532 (1985 wk32) | DIP-8 | **VCO/oscillatore di clock, scenario A confermato** | +5 V (presunto → L8) | Alta (sigla) | 844, 869 |
| U11-U16 (±1) | Op-amp dual | `4558D` (JRC) (codes 5061, 1650, 5200, 5201, 0661, 5207…) ×6-7 | varie | DIP-8 | Dual op-amp generali: filtri, I/O, mixer, driver | +15 V | Alta (sigla) / Media (conteggio → L6) | 840, 844, 845, 871-874, 877 |

*Colonna **Data code** = codice produttore/data separato dalla sigla
(correzione sessione utente: es. U10 non è "M8532" ma LM311N + 8532).*

*Correzione: un "273J50" ipotizzato inizialmente come regolatore è in
realtà il condensatore **C5 = 27 nF 50 V** (vedi tabella C). Nessun
riferimento a 273J50 era presente in questo file.*

*Nota U4 (sessione 10 — superata dalla sessione 11): Risoluzione **12 bit [I]**, supportata
da 5 indizi (filtro anti-aliasing, compandor, epoca, capacità DRAM,
ascolto). Allora non deducibile senza oscilloscopio.*

*Aggiornamento sessione 11: ipotesi 12 bit **confermata** da misure audio — rumore di
fondo −67 dBFS (coerente con 12 bit, non con 8), f_camp ≈ 32 kHz (192 Kbit ÷ 12 bit =
16384 word ÷ 528 ms), banda ~15 kHz con taglio 15-16 kHz. L5, L12, L13 → **RISOLTE**.*

### B.1 Regolatori (U17, U18) — sotto-tabella dedicata (non IC)

| Ref | Tipo | Sigla / Marking | Data code | Package | Funzione / Ruolo | Alimentazione | Affidabilità | Foto |
|---|---|---|---|---|---|---|---|---|
| U17 | Regolatore (IC) | `AN7815` (Panasonic ▲) | 552 | TO-220 | Regolatore fisso **+15 V** | in da rettifico → out +15 V | Alta | 867, 869 |
| U18 | **Circuito discreto — NON IC** (regolatore +5 V, da confermare) | TO-92 vicino U17 (sigla transistor non letta) | — | discreto | **regolatore +5 V discreto: zener ~5,1 V (mis. 4,8 V) + transistor di passaggio + C 1 µF 50 V in uscita; ingresso ~7,4 V; sigla transistor da confermare (L22)** | in 7,4 V → out +5 V | Media (funzionamento = Alta [misure]; sigla = da leggere → L22) | 869 (zona AN7815), 844 |

---

## C. Blocco Clock/Timing (affiancato a U5)

Cuore del controllo del tempo: determina la frequenza di campionamento,
quindi tempo massimo di delay, banda passante e carattere sonoro [C-fisica].

| Componente del blocco | Ref | Ruolo |
|---|---|---|
| `TC40H000P` (quad NAND) | **U5** | oscillatore/logica di clock |
| `LM311N` (data code 8532) | **U10** | VCO / oscillatore a rilassamento (scenario A confermato) |
| Trimmer giallo `203` (20 kΩ) | *Non assegnati* | calibrazione frequenza clock |
| Cap poliestere 1000 pF | **C1** | costante di tempo del VCO |
| Elettrolitici 100 µF 10 V ×2 | **C2-C3** | filtro rail +5 V nella zona |
| Elettrolitico 1 µF 50 V | **C4** | uscita regolatore U18 (+5 V) |
| Resistori pull-up/pull-down | **R1-R4** (gruppo, n da confermare) | polarizzazione U5/U10 |
| Diodi clamp/zener | **D1-D4** | protezione / riferimento U18 |
| Pot MODULATION SPEED/DEPTH | *Non assegnati* | controllo del VCO [P] |
| RANGE mS 1..512 + FACTOR ×0.5-×2 | *Non assegnati* | divisori digitali a valle [P] |

---

## D. Condensatori (Ref C — numeri crescenti)

| Ref | Tipo | Sigla/Marking | Valore | Funzione | Affidabilità | Foto |
|---|---|---|---|---|---|---|
| C1 | Cap poliestere (timing) | — | **1000 pF (1 nF)** | costante di tempo VCO (U10) | Alta | 844, 869 (zona U5/U10) |
| C2, C3 | Elettrolitico ×2 | — | **100 µF / 10 V** | filtro rail +5 V (zona timing) | Alta | 844, 869 |
| C4 | Elettrolitico | — | **1 µF / 50 V** | uscita regolatore U18 | Alta (misure utente) | 869 |
| C5 | Cap poliestere assiale | `273J50` (27×10³ pF, J=±5%, 50 V) | **27 nF / 50 V** | filtro/accoppiamento zona ALN/timing — *ex-"regolatore": correzione* | Alta (decodifica codice) | 844, 869 (zona ALN) |
| C6 | Cap poliestere arancione | — | da leggere | filtro/accoppiamento zona ADC (vicino U4) | Media | 804, 807, 810 |

---

## E. Resistori (Ref R — numeri crescenti)

| Ref | Gruppo | Funzione | Valore | Affidabilità | Foto |
|---|---|---|---|---|---|
| R1-R4 (n da confermare) | zona timing U5/U10 | pull-up / pull-down logica | da decodificare (bande) | Presunto (gruppo) | 844, 869, 874 |
| R5-R6 (n da confermare) | plancia op-amp | partitore bias mid-rail ~7,5 V (4558/M5221) | da decodificare | Presunto → L16 | 874, 877 |
| R7+ (n da confermare) | uscite NE571/4558 | resistori di carico del compandor (sigle pin datasheet, non Ref) | da decodificare | Presunto | 845, 874, 877 |

*Ref di blocco indicative: le quantità non sono singolarizzabili dalle
foto; bande resistori nitide disponibili in …874 per decodifica dedicata.*

---

## F. FET / Transistor (Ref Q — numeri crescenti)

| Ref | Tipo | Sigla/Marking | Package | Funzione | Alimentazione | Affidabilità | Foto |
|---|---|---|---|---|---|---|---|
| Q1 | JFET N basso rumore | `K118` = **2SK118** (Toshiba): V(BR)GDS −50 V, I(D) 10 mA, 100 mW, NF 0,5 dB | TO-92 | buffer alta impedenza o sample & hold tra LEVEL e ADC [P-tesi utente → L21] | **presunto +15 V analogico (L16)** — stesso rail dello stadio analogico (M5221/M5224P/NE571) | Alta (sigla) / Ruolo Presunto | segnale utente; TO-92 visibili …844, …845 |
| Q2 | JFET P o PNP | `J43P55` → probabile **2SJ43** | da confermare | **possibile coppia complementare con Q1 o commutazione — ipotesi da verificare (L20/L21)**; posizione vicina ad ALN+C5 | da verificare | **Probabile — DA CONFERMARE (L20)** | zona ALN 252F (…844, …869); serve macro |

---

## G. Diodi (Ref D — numeri crescenti)

| Ref | Tipo | Sigla/Marking | Funzione | Affidabilità | Foto |
|---|---|---|---|---|---|
| D1-D3 (gruppo) | Diodi segnale DO-35 | bande visibili (tipo non leggibile) | zona timing: clamp / regolazione / parte U18 — da identificare (L11) | Media | 844, 869 |
| D4 | Zener | ~5,1 V (misurato 4,8 V) | riferimento regolatore +5 V (U18) | Alta (misura utente) | 869 (zona AN7815) |
| D5 | Diodo di protezione | da leggere | protezione (rail o I/O) [P] | Probabile | 869, 877 |

Note Ref: U-numbers provvisori. U4 = unico componente con ruolo non
datasheet-izzato (custom OKI; L5 → **RISOLTA sessione 11**: ruolo e
12 bit confermati da misure audio, datasheet comunque inesistente).

---

## H. Non assegnati (Ref non assegnate)

Ordine: potenziometri → jack → switch/LED → PSU → meccanica →
connettori → campi RC.

### H.1 Potenziometri, rotary e trimmer

| Componente | Sigla / Valore | Funzione | Affidabilità | Foto |
|---|---|---|---|---|
| Pot frontale (arancio) | `M50kΩB 50 C` (dorso) | PEAK LEVEL — livello ingresso | Alta | 826, 827; dorso 872, 879 |
| Pot frontale (verde) | `M50kΩB` | FEEDBACK LEVEL — reostato di bias DC compressore (test L17) | Alta | 826, 827 |
| Pot frontale (giallo) | `M50kΩB` | DELAY LEVEL — mix wet | Alta | 827, 828 |
| Pot frontale (arancio) | `M50kΩB` | MODULATION SPEED — LFO | Alta | 831, 832 |
| Pot frontale (giallo) | `M50kΩB` | MODULATION DEPTH — LFO | Alta | 832, 833 |
| Pot frontale (verde) | scala discreta ×0.5 / ×1 / ×2 | DELAY TIME / FACTOR — **tipo da confermare** (pot con scala a 3 valori o switch a 2-3 posizioni) | Media | 829, 831 |
| Rotary switch frontale (azzurro, **10 posizioni**; contatti wafer visibili sul retro → …844) | scala **1, 2, 4, 8, 16, 32, 64, 128, 256, 512 ms** | RANGE mS — selezione range (clock/divisori) | Alta | 824, 828, 829, 844 |
| Trimmer giallo | `203` = **20 kΩ** (confermato) | calibrazione clock/offset | Alta | 844, 867, 869 |
| Trimmer giallo (2ª lettura) | `202`/`203` in …844 | stesso del 203 o secondo pezzo? | Media → da verificare | 844 |
| Trimmer cermet / "vite bianca" tondo | crema/bianco | calibrazione (clock in zona timing / bias) — uno o due pezzi? | Media | 844, 850, 851, 856, 867, 868 |

### H.2 Jack

| Componente | Sigla / Valore | Funzione | Affidabilità | Foto |
|---|---|---|---|---|
| Jack 1/4" frontale | `INPUT −20dB` | ingresso audio | Alta | 824, 825 |
| Jack 1/4" retro ×2 | — | MIX OUT + DIRECT (uscite) | Media (etichette) | 819 (crop 820-822) |
| Jack 1/4" retro ×3 | `REMOTE: HOLD, MODULATION, DELAY` | controllo pedali | Alta | 819, 820 |

### H.3 Switch e LED

| Componente | Sigla / Valore | Funzione | Affidabilità | Foto |
|---|---|---|---|---|
| Rocker frontale + LED | `POWER` + LED rosso | accensione — attuazione meccanica del sezionatore NOBLE (vedi H.4) | Alta | 824, 835 |
| Rocker frontale + LED | `HOLD` + LED rosso | freeze delay | Alta | 824, 830-832 |
| LED pannello | — | **PEAK** (ind. overload; ≠ pot "PEAK LEVEL") | Media (foto pannello) | 824 |
| Lenti chiare ×2 su board | — | **identificazione da confermare: LED bianchi, LED IR o fototransistor?** → L19 | Media | 844, 877 |

### H.4 PSU (rete)

| Componente | Sigla / Valore | Funzione | Affidabilità | Foto |
|---|---|---|---|---|
| Trasformatore EI | nastro blu, morsetti rossi/blu; stemma non leggibile → L3 | isolamento + secondari multipli | Media | 816, 842, 874 |
| Sezionatore rete (voce unica) | `NOBLE JAPAN` (teal), attuato dal rocker POWER frontale; cap snubber sui morsetti; in serie con fusibile 5×20 [P] | accensione rete | Alta | 809, 817, 884 |
| Filtro EMI | `A91S2 / 3A/48A / 250V~ / A2H4` | filtro di linea | Alta | 840, 841, 870, 884 |
| Cap X2 | `ECQ-U / .0022µF / 40/085/21 / X2 / 250V~` = 2,2 nF | sicurezza rete | Alta | 840, 841 |
| Fusibile 5×20 (cartuccia in clip) | **rating non leggibile → L2** | protezione | Alta (esistenza) / rating da misurare | 808, 809, 817, 840, 842, 884 |
| Cavo rete fisso + guarnizione | `AC 220V 50/60Hz` | ingresso rete | Alta | 840, 841 |

### H.5 Meccanica

| Componente | Sigla / Valore | Funzione | Affidabilità | Foto |
|---|---|---|---|---|
| Chassis + fondo nero | 4 piedini | corpo | Alta | 823 |
| Mascherina frontale | alluminio verniciato + serigrafia | pannello | Alta | 824 |
| Viti / bracket interni | (grigio accanto elettrolitico 844) | fissaggio | Alta | 844, 884 |

### H.6 Connettori interni

| Componente | Sigla / Valore | Funzione | Affidabilità | Foto |
|---|---|---|---|---|
| Connettore bianco multipin | — | routing tra board | Media | 868, 869 |
| Connettori neri multipin | — | interfacce board | Media | 867, 869 |
| Fascio fili arcobaleno (~10) | — | collegamento rotary switch | Alta | 844, 853, 878 |
| Morsetti trasformatore | rossi/blu | secondari | Alta | 816 |

### IND1 (prov.) — Induttore

| Ref | Tipo | Sigla / Marking | Valore | Funzione | Affidabilità | Foto |
|---|---|---|---|---|---|---|
| **IND1 (prov.)** | Induttore assiale teal | `ALN 252F` (letto anche "352F") | **2,5 mH ipotizzato** (25×10²) — conferma valore in **L10** | filtro alimentazione | Alta (tipo) / valore Presunto | 855, 863 |

### H.7 Campi RC e gruppi senza Ref

| Gruppo | Sigla / Valore | Funzione | Affidabilità | Foto |
|---|---|---|---|---|
| Resistenza campo ×~20-30 | bande visibili, valori da decodificare → L14 | polarizzazione/carico op-amp | Media | 845, 874 |
| Elettrolitico nero | `…H02 / 8510` (date code) | filtro PSU/rail | Media (valore → L4) | 844, 850, 851, 856, 867, 868, 869 |
| Elettrolitico nero grande | `…µ …35V` (470 µF 35 V?) | rail PSU | Probabile (lettura) | 878 |
| Elettrolitico azzurro grande | valore n/v | rail PSU | Media | 844 |
| Elettrolitico blu | — | filtro zona regolatore | Media | 867 |
| Cap ceramici arancio | `104` (100 nF) `25V`? | decoupling (lato saldature, vicino QFP) | Alta (104) / 25V da verificare | 804, 806, 807, 810, 844 |
| Cap film teal | `223` = 22 nF | filtro | Alta | 851, 856, 867, 868, 869 |
| Cap film giallo | `102`/`102K`?/`472M`? (1-4,7 nF?) | filtro | Media (letture parziali) | 859, 861, 862, 865, 866 |
| Induttore | `ALN 252F` | **vedi IND1** (voce dedicata sopra) | — | 855, 863 |
| Diodi vetro DO-35 ×n di campo | tipi da identificare | segnale | Media | 844, 845 |
| Elettrolitici piccoli ×n di campo | valori parziali (es. "…50V") | accoppiamento/filtro | Media | 845, 871-874 |

*Nessuna serigrafia del dispositivo riporta designator: tutti i Ref di
questo file sono provvisori (assegnati per area/tipo).* 
