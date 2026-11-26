# Mitsubishi M5221 — Dual J-FET input op-amp (classe TL072)

| | |
|---|---|
| File PDF | `Prep\Datasheets\mitsubishi_m5221.pdf` (4 pagine, scansionata) |
| Ref scheda | U9 — marking `M5221 / 4504`, DIP-8 |
| Fonte PDF | Mitsubishi M5221L/P/FP (M5T082P) datasheet |
| Data verifica | 04/10/2026 |
| Metodo | Render 300 DPI delle 4 pagine + OCR (rapidocr + WinRT) + **lettura visiva p01-p03**; cache `%TEMP%\opencode\ddx_ocr\mitsubishi_m5221\` |

## Trascrizione utente (claim)

1. Input resistance Rin = 1000 MΩ
2. Slew rate 13 V/µs
3. THD = 0,007 % (Gv = 40 dB)

## Controverifica

| # | Claim utente | Esito | Riscontro nel PDF | Pag. |
|---|---|---|---|---|
| 1 | Rin 1000 MΩ | ✅ **CONFERMATO** | FEATURES: **Ri = 1000 MΩ typ**; tabella: Rin typ 10³ MΩ (= 1 GΩ typ) | p01, p02 |
| 2 | SR 13 V/µs | ✅ **CONFERMATO** | FEATURES: **SR = 13 V/µs**; tabella: SR typ 13 V/µs (Gv=0 dB, RL=2 kΩ) | p01, p02 |
| 3 | THD 0,007 % @G40dB | ✅ **CONFERMATO** | FEATURES: **THD = 0,007 % (Gv=40 dB, f=1 kHz, typ)** | p01 |

*Coerenza incrociata:* `02_componenti_raw.md` §F2 ("bias 0,4 nA") = IB max 400 pA ✅; "GBW 3 MHz" = fT typ 3 MHz ✅.

## Trascrizione dati

**p01 — Descrizione/features:** dual op-amp con stadio ingresso J-FET, 8-pin SIP/DIP/FP; alto Zin, alta SR, bassa bias; usi stereo/tape/CD/VCR.
FEATURES (typ): Ri = 1000 MΩ; SR = 13 V/µs; Gvo = 106 dB; THD = 0,007 % (Gv=40 dB @1 kHz); ILP = ±50 mA; Pd = 800 (SIP) / 625 (DIP) / 440 (FP) mW.
**Pinout DIP-8:** 1=OUT1, 2=INV-IN1, 3=NONINV-IN1, 4=V−, 5=NONINV-IN2, 6=INV-IN2, 7=OUT2, 8=V+.

**p02 — Abs max (Ta=25 °C):** Vcc ±18 V; ILP ±50 mA; Vid ±30 V; Vic ±15 V; Pd 800/625/440 mW (SIP/DIP/FP); Kθ 8/6,25/4,4 mW/°C; Topr −20..+75 °C; Tstg −55..+125 °C.

**p02 — Electrical (Ta=25 °C, VCC=±15 V):**

| Parametro | Min | Typ | Max | Unit | Note |
|---|---|---|---|---|---|
| Icc | — | 3,0 | 6,0 | mA | Vin=0 |
| Vio | — | 5,0 | 15,0 | mV | RS≤10 kΩ |
| Iio | — | 5 | 200 | pA | — |
| IB | — | 30 | 400 | pA | = 0,4 nA max (§F2) |
| **Rin** | — | **10³ (1000 MΩ)** | — | MΩ | — |
| Gvo | 86 | 106 | — | dB | RL≥2 kΩ, VO=±10 V |
| VOM (RL≥10 k) | ±12 | ±14 | — | V | — |
| VOM (RL≥2 k) | ±10 | ±13 | — | V | — |
| VCM | ±10 | ±12 | — | V | — |
| CMRR | 70 | 76 | — | dB | — |
| SVRR | — | 30 | 150 | µV/V | — |
| Pd | — | 90 | 180 | mW | — |
| **SR** | — | **13** | — | V/µs | Gv=0 dB, RL=2 kΩ |
| **fT (GBW)** | — | **3** | — | MHz | = "GBW 3 MHz" §F2 |
| VNI | — | 2,2 | — | µVrms | Rs=100 Ω, BW 10 Hz–30 kHz |

## Grafici (p03, letti, valori ≈ approssimati)

- Output voltage vs load (Vcc=±15 V, 1 kHz, THD=1 %): Vo ≈3,5 Vrms @100 Ω → ≈8,8 @1 kΩ → ≈10 @10 kΩ.
- Max output vs supply (RL=10 kΩ): Vop-p ≈27 Vpp @±15 V.
- Gain vs freq (Vcc=±15 V, RL=2 kΩ): piatto ≈107 dB fino a ≈10 Hz, −20 dB/dec, unità ≈3 MHz (coerente fT=3 MHz).
- Max output vs freq (RL=10 kΩ): ≈27 Vpp piatto fino a ≈100 kHz, poi in discesa.
- Input bias current vs Ta: IB ≈30 pA da −50 a 0 °C; ≈30-40 pA @25 °C; ≈100 pA @40 °C; ≈1 nA @75 °C; ≈7 nA @100 °C.
- SR waveform: step 5 V in ≈0,4 µs → ≈13 V/µs.

## Nota modello DSP

- U9 = buffer d'ingresso: la **saturazione d'ingresso** è modellata con `thrM5221_ = 13/15` (sessione 13c, P3) — coerente con VOM ≈ ±13 V (typ, RL≥2 kΩ) a ±15 V: la "soglia" del modello corrisponde al massimo swing d'uscita d'ingresso.
- Rin = 1 GΩ e IB = pA: giustificano l'assenza di loading sul LEVEL M50kΩB; nessun parametro da cambiare (vincolo: coefficienti invariati).
- Il THD 0,007 % del datasheet è la specifica del solo M5221 (non del sistema): il THD di sistema è dominato dal companding NE571 (sessione 11/12).

## Limiti / note

- Scansione: OCR arbitrato da lettura visiva; p04 = applicazioni/outline (non critico).
- Valori letti dal grafico marcati ≈.
