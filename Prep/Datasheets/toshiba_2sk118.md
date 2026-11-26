# Toshiba 2SK118 — JFET N-channel a basso rumore (TO-92)

| | |
|---|---|
| File PDF | `Prep\Datasheets\toshiba_2sk118.pdf` (4 pagine, testo estraibile) |
| Ref scheda | Q1 — marking `K118` (TO-92) |
| Fonte PDF | Toshiba 2SK118 (doc. 2003-03-25) |
| Data verifica | 04/10/2026 |
| Metodo | Estrazione testo PyMuPDF (p01, p04) + **lettura visiva dei grafici p02 e p03** (p02/p03 sono solo figure, testo estratto vuoto); cache `%TEMP%\opencode\ddx_ocr\toshiba_2sk118_fitz.txt`, `toshiba_2sk118\p02.png`, `p03.png` |

## Trascrizione utente (claim)

1. Caratteristica quadratica: ID = IDSS (1 − VGS/Vp)²
2. Classi IDSS R / O / Y / GR
3. NF = 0,5 dB
4. Ciss = 8,2 pF
5. |Yfs| min 1,2 mS

## Controverifica

| # | Claim utente | Esito | Riscontro nel PDF | Pag. |
|---|---|---|---|---|
| 1 | ID = IDSS(1−VGS/Vp)² | ⚠️ **NON STAMPATA** (comportamento coerente) | L'equazione non compare nel datasheet; la **curva parabolica** ID-VGS è confermata graficamente (curve per IDSS=5,6/4,0/2,6/1,3 mA con pinch-off ≈ −2,4/−2,0/−1,6/−0,7 V) — legge di Shockley classica dei JFET, coerente ma non verificabile come formula testuale | p02 (grafico) |
| 2 | Gruppi R/O/Y/GR | ✅ **CONFERMATO** | Note IDSS classification: **R 0,3~0,75, O 0,6~1,4, Y 1,2~3,0, GR 2,6~6,5 mA** | p01 |
| 3 | NF 0,5 dB | ✅ **CONFERMATO** | Features: "Low noise: **NF = 0,5 dB typ** (RG=100 kΩ, f=120 Hz)"; tabella: typ 0,5 / max 5,0 dB (VDS=15 V, VGS=0) | p01 |
| 4 | Ciss 8,2 pF | ✅ **CONFERMATO** | Input capacitance **typ 8,2 pF** (VDS=10 V, VGS=0, f=1 MHz) | p01 |
| 5 | Yfs min 1,2 mS | ✅ **CONFERMATO** | Forward transfer admittance **min 1,2 mS** (VDS=10 V, VGS=0, f=1 kHz) | p01 |

## Trascrizione dati (p01)

**Descrizione:** Silicon N-channel junction FET per general purpose, impedance converter, condenser microphone; small package (2-4E1B, 0,13 g).

**Abs max (Ta=25 °C):** VGDS −50 V; IG 10 mA; PD 100 mW; Tj 125 °C; Tstg −55..+125 °C.

**Electrical (Ta=25 °C):**

| Parametro | Condizioni | Min | Typ | Max | Unit |
|---|---|---|---|---|---|
| IGSS gate cut-off current | VGS=−30 V, VDS=0 | — | — | −1,0 | nA |
| V(BR)GDS breakdown | VDS=0, IG=−100 µA | −50 | — | — | V |
| IDSS drain current | VDS=10 V, VGS=0 | 0,3 | — | 6,5 | mA |
| VGS(OFF) gate-source cut-off | VDS=10 V, ID=0,1 µA | −0,4 | — | −5,0 | V |
| \|Yfs\| forward transfer adm. | VDS=10 V, VGS=0, f=1 kHz | **1,2** | — | — | mS |
| Ciss input capacitance | VDS=10 V, VGS=0, f=1 MHz | — | **8,2** | — | pF |
| Crss reverse transfer cap. | VGD=−10 V, ID=0, f=1 MHz | — | 2,6 | — | pF |
| NF noise figure | VDS=15 V, VGS=0, RG=100 kΩ, f=120 Hz | — | **0,5** | 5,0 | dB |

Gruppi IDSS (claim 2). Feature aggiuntiva: IGSS = −1 nA max (VGS=−30 V).

## Grafici (letti, valori ≈ approssimati)

**p02 (static characteristics):**
- ID–VDS/VGS: saturazione per VDS ≥ ~5 V; IDSS ≈ 5,6 mA a VGS=0 (curva tip).
- ID–VGS per IDSS = 5,6/4,0/2,6/1,3 mA: parabole (claim 1) con VGS(OFF) ≈ −2,4/−2,0/−1,6/−0,7 V.
- ID–VDS low-voltage: knee ~1 V; VGS=0 → ≈4,7 mA; −0,2→4,0; −0,4→3,4; −0,6→2,9; −0,8→2,4; −1,0→1,9; −1,2→1,5; −1,4→1,2; −1,6→0,9 mA.
- |Yfs|–ID: ≈1,7 mS @1 mA; ≈2,7 @3 mA; ≈4,0 @6 mA (curva IDSS=6,0 mA).
- Ciss–VDS: ≈13 pF @0,5 V → 10 pF @3 V → 9 pF @10 V → 8 pF @30 V (coerente con typ 8,2 pF).
- Crss–VGD: ≈8 pF @−0,5 V → 2,6 @−10 V → 1,5 @−30 V.

**p03 (noise + derating):**
- |Yfs|–IDSS (log): 1,3 mS @0,3 mA → 5 mS @10 mA; VGS(OFF)–IDSS: −0,5 V @0,3 mA → −3 V @4,5 mA (coerente col range −0,4..−5,0 V).
- NF–f (VDS=15 V, ID=1 mA): RG=10 kΩ ~5 dB @10 Hz → ~1 dB @1 kHz → ~0,6 @10 kHz; RG=100 kΩ ~1,2 @10 Hz → 0,5 @100 Hz-1 kHz; RG=1 MΩ ~2 @10 Hz → 0,5 @1 kHz.
- NF–RG: minimo ~0,1–0,3 dB attorno a 30–100 kΩ; a 120 Hz peggiora sotto i 3 kΩ (≈8 dB a 500 Ω).
- NF–ID (RG=100 kΩ): ~0,2 dB per ID > 0,2 mA a 120 Hz; ~0,25 dB a 1 kHz; ~0,1 dB a 10 kHz.
- NF–VDS: a 120 Hz cresce oltre ~16 V (≈2 dB a 30 V); a 10 kHz piatto ~0,6 dB.
- PD–Ta: 100 mW fino a 25 °C, derating lineare a 0 @125 °C (≈ −1 mW/°C).

## Nota modello DSP

- Q1 2SK118 è modellato nel plugin come **saturazione d'ingresso della catena analogica**: `kJfet_ = 0.003` (sessione 13c, P3) — la curva di Shockley quadratica giustifica il modello; il datasheet fornisce IDSS/VGS(OFF)/Yfs per ancorare la scala.
- Il **gruppo IDSS del Q1 della scheda non è noto** (marking `K118` senza lettera di classe) → usare il range completo 0,3–6,5 mA.
- Vincolo: **non ritoccare kJfet_** (regola utente "non modificare i coefficienti calibrati").

## Limiti / note

- L'equazione quadratica (claim 1) resta **[I]**: coerente con i grafici ma non stampata nel PDF; serve eventualmente un textbook/datasheet JFET generico come fonte citata.
- p04 = sole "Restrictions on product use" (nessun dato tecnico).
