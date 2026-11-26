# Mitsubishi M5224P — Quad op-amp single-supply (classe LM324)

| | |
|---|---|
| File PDF | `Prep\Datasheets\mitsubishi_m5224p.pdf` (6 pagine; p03 = grafici, p06 = pagina promozionale; testo quasi assente → trattato come scansione) |
| Ref scheda | U8 (×1 confermata; eventuale 2ª con sigla parziale) — marking `M5224P / 4507`, DIP-14 |
| Fonte PDF | Mitsubishi M5224P datasheet (databook) |
| Data verifica | 04/10/2026 |
| Metodo | Render 300 DPI delle pagine + OCR (rapidocr + WinRT) + **lettura visiva p01, p02, p04, p05** (p03 = grafici Ib/Ta + gain, elencati ma non quantificati); cache `%TEMP%\opencode\ddx_ocr\mitsubishi_m5224p\` |

## Trascrizione utente (claim)

1. Crossover distortion da classe C sopra 100 µA di carico
2. Pull-up esterno 3 kΩ
3. THD migliorato ≈100× con pull-up (dead-zone/crossover)

## Controverifica

| # | Claim utente | Esito | Riscontro nel PDF | Pag. |
|---|---|---|---|---|
| 1 | Classe C crossover >100 µA | ✅ **CONFERMATO** | Fig. 5: circuito con corrente valutata **Ic ≈ 100 µA (Q14)** → bias A-class fino a 100 µA (output fino a quasi GND); **oltre 100 µA** (carico maggiore) si attiva Q13 senza corrente di riposo = **C-class bias** (basi Q5/Q6/Q13 corte) → crossover distortion, "*may not be suitable for audio signal amplifiers*" | p05 |
| 2 | Pull-up 3 kΩ | ✅ **CONFERMATO** | "REDUCTION OF DISTORTION": per usi audio, **pull-up esterno (e.g. 3 kΩ)** aumenta il bias di classe A e riduce la distorsione (Fig. 7: Rp 3 kΩ, ±15 V, RL 10 kΩ) | p05 |
| 3 | THD ~100× / dead-zone | ✅ **CONFERMATO** | Fig. 8 THD vs Output (Vcc=±15 V, 1 kHz): senza pull-up THD ≈0,01–0,3 % con **salto attorno a 0,5–1 Vrms** (crossover/dead-zone); con Rp 3 kΩ THD ≈0,0015–0,01 % → **≈2 decadi (≈100×) attorno a 1 Vrms** | p05 |

*Nota interna al datasheet (non claim):* FEATURES riporta Gvo = 110 dB typ mentre la tabella elettrica riporta Gvo min 25 / typ 100 V/mV (= 100 dB) → **discordanza interna del datasheet**, annotata.

## Trascrizione dati

**p01 — Descrizione/features:** quad single-supply op-amp, 14-pin DIP (14P4) / FP (14P2S-A); ingresso/uscita dal livello GND; usi motor control (cassette, turntables, VTR, CD), automotive, comunicazioni; usabile come comparatore.
FEATURES: Vi = −0,3..+36 V (ingresso comune a livello GND); Vcc = 3..36 V; Gvo = 110 dB typ (features) / 100 V/mV typ (tabella); Pd = 700 mW (P) / 550 mW (FP).
**Pinout 14:** 1=VOUT1, 2=VIN(−)1, 3=VIN(+)1, 4=Vcc, 5=VIN(+)2, 6=VIN(−)2, 7=VOUT2, 8=VOUT3, 9=VIN(−)3, 10=VIN(+)3, **11=GND**, 12=VIN(+)4, 13=VIN(−)4, 14=VOUT4.

**p02 — Abs max (Ta=25 °C):** Vcc 36 (±18) V; Isink/Isource ±50 mA; Vid ±36 V; Vi −0,3..+36 V; Pd 700 (DIP) / 550 (FP) mW; Kθ 7/5,5 mW/°C; Topr −20..+75 °C; Tstg −55..+125 °C.

**p02 — Electrical (Ta=25 °C, Vcc=+15 V):**

| Parametro | Min | Typ | Max | Unit |
|---|---|---|---|---|
| Vio | — | 2 | 7 | mV |
| IB | — | 45 | 250 | nA |
| Iio | — | 5 | 50 | nA |
| Vicm | 0 | — | Vcc−1,5 | V |
| Icc | — | 1,1 | 1,5 | mA |
| Gvo | 25 | **100** (=100 dB) | — | V/mV |
| Vo (RL=2 kΩ) | 0 | — | Vcc−1,5 | V |
| CMRR | 65 | 85 | — | dB |
| SVRR | 65 | 100 | — | dB |
| CSR (1-20 kHz) | — | 120 | — | dB |
| Isource | 20 | 40 | — | mA |
| Isink | 10 | 20 | — | mA |
| Isink (VO=200 mV) | 12 (µA) | 50 (µA) | — | — |

**p04 — Grafici/basic operation (letti):**
- ΔV vs Isource: ΔV ≈1,2 V piatto fino a ≈10 mA, poi crollo (30-50 mA).
- Vo vs Isink (V+=15 V): Vo scende a ≈0,05 V per Isink ≈0,1 mA, piatta ≈0,5-0,6 V tra 0,1-1 mA, risale >1 V verso 10 mA.
- M5224 opera input/output da 0 V (GND) con alimentazione singola; VB(ON): M5218 ≈1,1 V, M5224 ≈−0,1 V → differenziale attivo anche a 0 V (Fig. 3: M5218 non funziona sotto Vi 1,1 V).

**p05 — Output stage + distorsione (cuore delle claim):**
- Fig. 4 (M5218): output AB-class push-pull senza crossover, ma Vo non scende sotto ≈1,1 V.
- Fig. 5 (M5224): **bias A-class ≈100 µA (Q14)** → output fino a quasi GND; carico oltre 100 µA → Q13, nessuna corrente di riposo = **classe C**, crossover distortion ("may not be suitable for audio signal amplifiers").
- REDUCTION OF DISTORTION: pull-up esterno **3 kΩ** (Fig. 7: Rp 3 kΩ, ±15 V, RL 10 kΩ) → Fig. 8: **THD ≈100× minore** attorno a 1 Vrms; senza pull-up salto di THD a 0,5-1 Vrms (dead-zone).
- Bias DC di uscita deve stare a Vcc/2 (regime single e dual).

**p03 (non quantificato):** grafici Ib vs Ta + gain vs freq — elencati, valori non letti.

## Nota modello DSP

- U8 M5224P alimentato a +15 V singolo: crossover della classe C (sopra 100 µA di carico) è la base fisica del **Meccanismo B (kLo, crossover H3 < 500 Hz)** già implementato ma con taratura 0 nel core (sessione 12b): nel plugin la distorsione a bassa banda è fornita dalla dinamica del compressore; kLo resta **0,0** (vincolo utente) salvo che la misura HW futura non mostri H3(100 Hz) ~0,3 % a −30 dBFS (test discriminante §0.4, `THD_characterization_v4.md`).
- Il datasheet (Fig. 8) fornisce la prova di letteratura per il crossover, non una taratura diretta: 100× sul THD del *solo* op-amp a 1 Vrms con Rp 3 kΩ.
- La scheda ha un pull-up 3 kΩ sul M5224P? **Non verificato dalle foto** → resta ipotesi (coerente con il claim utente).

## Limiti / note

- PDF quasi senza strato testuale (498 car.) → verifica interamente da render + OCR + visione.
- p06 = pagina promozionale (non tecnica).
- Gvo 110 dB (features) vs 100 dB (tabella): discordanza interna al datasheet, riportata com'è.
