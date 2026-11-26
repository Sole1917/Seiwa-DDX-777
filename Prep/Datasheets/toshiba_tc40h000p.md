# Toshiba TC40H000P — Quad 2-input NAND gate C²MOS (equivalente 7400)

| | |
|---|---|
| File PDF | `Prep\Datasheets\toshiba_tc40h000p.pdf` (3 pagine, scansionata) |
| Ref scheda | U5 — marking `Toshiba TC40H000P / JAPAN / 8539H`, DIP-14 |
| Fonte PDF | Toshiba TC40H000P/F datasheet |
| Data verifica | 04/10/2026 |
| Metodo | Render 300 DPI delle 3 pagine + OCR (rapidocr + WinRT) + **lettura visiva p01-p02**; cache `%TEMP%\opencode\ddx_ocr\toshiba_tc40h000p\` |

## Trascrizione utente (claim)

1. VIH = 4,0 V / VIL = 1,0 V
2. Propagation delay tP = 18 / 27 ns

## Controverifica

| # | Claim utente | Esito | Riscontro nel PDF | Pag. |
|---|---|---|---|---|
| 1 | VIH 4,0 / VIL 1,0 | ✅ **CONFERMATO** | Electrical (VDD=5 V): VIH "H" **min 4,0 V** (tutte le temperature); VIL "L" **max 1,0 V** (tutte le temperature) | p02 |
| 2 | tP 18/27 ns | ✅ **CONFERMATO** | Switching (Ta=25 °C, VSS=0, CL=15 pF): **tpLH Circuit 1: typ 18 / max 27 ns** (typ/max). Contesto: tpHL Circuit 1 typ 14 / max 21 ns | p02 |

## Trascrizione dati

**p01 — Descrizione/pinout/abs max:**
- Quad 2-input NAND (equiv. 7400), logica **C²MOS** (serie TC40H = ibrida tra 74C e 74HC); package DIP14 (3D14A-P) + MFP14 (F14GB-P).
- **Pinout DIP-14:** 1=1A, 2=1B, 3=1Y, 4=2A, 5=2B, 6=2Y, **7=VSS**, 8=3Y, 9=3A, 10=3B, 11=4Y, 12=4A, 13=4B, **14=VDD**.
- **Maximum ratings:** VDD = VSS−0,5 .. VSS+10 V; VIN = VSS−0,5 .. VDD+0,5; VOUT = VSS−0,5 .. VDD+0,5; IIN = ±10 mA; PD = 300 (DIP) / 180 (MFP) mW; Tstg −65..+150 °C; Tsol 260 °C × 10 s.
- Truth table NAND standard (L L→H, H L→H, L H→H, H H→L); tutti gli input con protezione.
- **Recommended operating (VSS=0):** VDD **2,0..8,0 V**; VIN 0..VDD; Topr −40..+85 °C.

**p02 — Electrical (VSS=0,0 V):**
- VOH (|IOUT|<1 µA, VDD=5): min 4,95 V (tutte le temperature); typ 25 °C = 5,0 V.
- VOL (|IOUT|<1 µA, VIN=VDD, VDD=5): typ 0,0 / max 0,05 V (anche a −40/85 °C).
- IOH (VOH=4,6 V, VDD=5): min −0,52 (−40 °C) / −0,44 (25 °C) / −0,36 (85 °C) mA.
- IOL (VOL=0,4 V, VIN=VDD, VDD=5): min 1,4 (−40 °C) / 1,1 (25 °C) / 0,8 (85 °C) mA.
- **VIH min 4,0 V · VIL max 1,0 V** (VDD=5, tutte le temperature).
- IIH (VIH=8,0 V, VDD=8): max 0,3 µA (−40/25) / 1,0 µA (85 °C); IIL (VIL=0,0 V): max −0,3 / −1,0 µA; IDD (VDD=5): max 2,0 µA (−40/25) / 10,0 µA (85 °C).

**p02 — Switching (Ta=25 °C, VSS=0, CL=15 pF):**

| Parametro | Circuito | Typ | Max | Unit |
|---|---|---|---|---|
| tor (rise) | 1, VDD=5 | 26 | 40 | ns |
| tof (fall) | 1, VDD=5 | 16 | 30 | ns |
| **tpLH** | **1** | **18** | **27** | ns |
| tpHL | 1 | 14 | 21 | ns |
| tpLH | 2 | 13 | 20 | ns |
| tpHL | 2 | 15 | 23 | ns |
| CIN | — | 5 | — | pF |

(Test circuit: generatore a impulsi + NAND con CL=15 pF a massa.)

## Nota modello DSP

- U5 = glue logic/divisori del clock (blocco Clock/Timing): nessun parametro DSP del plugin deriva da questo datasheet.
- Il delay tipico di 18 ns rispetto al periodo di ~31 µs del clock di sistema è trascurabile.
- Pin 7 (VSS) misurato ≈ mass QFP nella sessione 10 (test D).

## Limiti / note

- Scansione: testo da OCR arbitrato da lettura visiva p01-p02; p03 = diagrammi di timing/app (non trascritti numericamente — p01/p02 coprono tutte le claim).
- "tP 18/27" dell'utente si riferisce a tpLH Circuit 1 (tip/max): coerente; tpHL è più veloce (14/21).
