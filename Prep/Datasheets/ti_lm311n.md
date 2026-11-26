# Texas Instruments LM311N — Comparatore differenziale (LM111/LM211/LM311)

| | |
|---|---|
| File PDF | `Prep\Datasheets\ti_lm311n.pdf` (42 pagine, testo estraibile) |
| Ref scheda | U10 — marking completo `M8532 LM 311N` (data code 8532 = 1985 wk32), DIP-8 |
| Fonte PDF | TI SLCS007K — LM111, LM211, LM311 Differential Comparators (set 1973, rev. mar 2017) |
| Data verifica | 04/10/2026 |
| Metodo | Estrazione testo PyMuPDF su 42 pagine + **lettura visiva p06** (tabelle Electrical/Switching) + p04 (abs max, letta via testo con conferma incrociata); cache `%TEMP%\opencode\ddx_ocr\ti_lm311n_fitz.txt`, `ti_lm311n\p06.png` |

## Trascrizione utente (claim)

1. Tempi di risposta 115 / 165 ns
2. Vio 2–7,5 mV
3. Uso nella scheda: VCO / clock

## Controverifica

| # | Claim utente | Esito | Riscontro nel PDF | Pag. |
|---|---|---|---|---|
| 1 | 115/165 ns | ✅ **CONFERMATO** | Switching characteristics (VCC±=±15 V, TA=25 °C): Response time **low-to-high = 115 ns typ**, **high-to-low = 165 ns typ** (RC=500 Ω a 5 V, CL=5 pF; step 100 mV con 5 mV di overdrive, fino al crossing di 1,4 V). Feature in p01: "Fast Response Time: 165 ns" | p06 |
| 2 | Vio 2–7,5 mV | ✅ **CONFERMATO** | VIO LM311 a 25 °C: **typ 2 / max 7,5 mV** (full range 0..70 °C: typ 4 / max 10 mV). Per LM111/211: typ 0,7 / max 3 mV | p06 |
| 3 | VCO/clock | ✅ **COERENTE** (uso di sistema, non specifica) | Applications del datasheet includono "**Oscillators**" e "Peak Detectors"; strobe capability + single 5-V supply adatti all'oscillatore a rilassamento U10 (trim 203 + C 1000 pF) | p01 |

## Trascrizione dati

**Features (p01):** Fast response 165 ns; strobe capability; max IB 300 nA; max IIO 70 nA; può operare da singolo 5-V supply; qualifiche automotive/Q-Temp.

**Pinout (p01/p02):** DIP-8 — 1 BALANCE, 2 IN−, 3 IN+, 4 V−, 5 EMIT OUT, 6 COL OUT, 7 BAL/STRB, 8 V+.

**Abs max (p04):** VCC+ 18 V; VCC− −18 V; VCC+−VCC− 36 V; VID ±30 V; Vin (entrambi gli ingressi) ±15 V e mai > supply; emitter out → VCC− 30 V; collector out → VCC− **LM311 40 V** (LM111/211 50 V); corto su uscita a massa max 10 s; TJ 150 °C; packages D/P/PS/PW/JG/FK.

**Electrical (p06, VCC±=±15 V, letta visivamente) — colonna LM311:**

| Parametro | Condizioni | TA | Min | Typ | Max | Unit |
|---|---|---|---|---|---|---|
| VIO input offset | See(3) | 25 °C | — | **2** | **7,5** | mV |
| VIO | " | full range | — | 4 | 10 | mV |
| IIO input offset current | See(3) | 25 °C | — | 6 | 50 | nA |
| IIO | " | full range | — | 20 | 70 | nA |
| IB input bias current | 1 V ≤ VO ≤ 14 V | 25 °C | — | 100 | 250 | nA |
| IB | " | full range | — | 150 | 300 | nA |
| IIL(S) strobe low-level | Vstrobe=0,3 V, VID≤−10 mV | 25 °C | — | −3 | — | mA |
| VICR common-mode range | lower / upper | full range | −14,7/13 | −14,5/13,8 | — | V |
| AVD large-signal diff. ampl. | 5 V≤VO≤35 V, RL=1 kΩ | 25 °C | 40 | 200 | — | V/mV |
| IOH collector leakage | VID=5 mV, VOH=35 V | 25 °C | — | 0,2 | 50 | nA |
| VOL collector-emitter | IOL=50 mA, VID=−10 mV | 25 °C | — | 0,75 | 1,5 | V |
| VOL (4,5 V supply) | VCC+=4,5 V, IOL=8 mA | full range | — | 0,23 | 0,4 | V |
| ICC+ output low | no load | 25 °C | — | 5,1 | 7,5 | mA |
| ICC− output high | no load | 25 °C | — | −4,1 | −5 | mA |

Note: (1) full range LM311 = 0..70 °C; (2) tipici a 25 °C; (3) offset con pull-up 7,5 kΩ a VCC+, uscite 14 V/1 V; (4) strobe driven −3..−5 mA (non cortocircuito a massa).

**Switching (p06):** L→H 115 ns typ, H→L 165 ns typ (condizioni al claim 1).

## Nota modello DSP

- Il plugin non modella il LM311: clock di campionamento (f_camp ≈ 32 kHz con bias +3% sul trimmer `203`) è stabilito dall'hardware; serve solo come riferimento che l'oscillatore a rilassamento usa un comparatore con risposta ~100 ns (trascurabile rispetto al periodo di ~31 µs).
- L'uso "VCO/clock" è lo scenario A confermato della sessione 6/7 (blocco Clock/Timing, `03_blocchi.md` §3).

## Limiti / note

- PDF a 42 pagini (famiglia LM111/211/311 con app-circuit): letti p01 (features), p04 (abs max), p06 (tabelle); le 40 pagini restanti (figure 1-31, app notes) non trascritte — le caption di Fig. 3/4 (response vs overdrive) sono nel testo.
- Condizioni di misura 115/165 ns: 5 mV di overdrive, non usabile come delay del sistema.
