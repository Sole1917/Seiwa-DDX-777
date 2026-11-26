# Hitachi HD14066BP — Quad bilateral switch (selezione della serie HD14000B/UB)

| | |
|---|---|
| File PDF | `Prep\Datasheets\hitachi_hd14066bp.pdf` (2 pagine, scansionata) |
| Ref scheda | U6 — marking `HD14066BP / 4M2 7`, DIP-14 |
| Fonte PDF | Hitachi "CMOS Logic HD14000B/UB Series" selection guide (databook pp. 272-273) — **NON il datasheet dedicato del solo HD14066** |
| Data verifica | 04/10/2026 |
| Metodo | Render 300 DPI delle 2 pagine + OCR (rapidocr + WinRT) + lettura visiva; cache `%TEMP%\opencode\ddx_ocr\hitachi_hd14066bp\` |

## Trascrizione utente (claim)

1. Ron 100–300 Ω

## Controverifica

| # | Claim utente | Esito | Riscontro nel PDF | Pag. |
|---|---|---|---|---|
| 1 | Ron 100–300 Ω | ❌ **NON VERIFICABILE da questo PDF** | Il file è la **selection guide della serie HD14000B/UB**: contiene features/abs max di serie e la lista dei dispositivi, **nessuna tabella elettrica del 4066** (né Ron, né capacitance, né timing). Per Ron serve il datasheet dedicato HD14066B/CD4066 | p01-p02 |
| — | *funzione quad analog switch* (implicita) | ✅ **CONFERMATO** | Selection guide: **HD14066B = "Quad. Analog Switch/Quad. Multiplexer"** (switch bilaterale quad); HD14016B affiancato | p01 |

## Trascrizione dati (quanto basta dal PDF)

**Nota manoscritta** in testa a p01: "Not available … the US" (leggibile parzialmente).

**Features serie (p01):** low current drain 0,5 nA typ/package (VDD=5 V); high noise margin **45% typ / 30% min** di VDD; **VDD = 3..18 V**; Topr −40..+85 °C; drive 2 TTL low-power load / 1 Schottky TTL / 2 HTL; conforme EIA/JEDEC; parametri garantiti a 5, 10, 15 V.

**Abs max serie (p01):** VDD −0,5..+18 V; Vin −0,5..VDD+0,5; Vout −0,5..VDD+0,5; Iin ±10 mA; TA −40..+85 °C; Tstg −65..+150 °C; PD 300 mW.

**Package (p02):** outline DP-14/DG-14 (HD14066P = plastic DIP-14) e DP-16/DG-16/DP-24/DG-24 per gli altri componenti della serie.

**p02:** prosecuzione della selection guide (shift register, contatori, PLL, gate) + outline dei package. Nessun dato elettrico aggiuntivo.

## Nota modello DSP

- U6 HD14066 = routing/bypass/hold dei jacks REMOTE (HOLD/MODULATION/DELAY): modello come switch ideale (R_on ≈ 0 nel plugin); il Ron reale 100–300 Ω (se confermato da datasheet dedicato) è in serie con impedenze di linea ≤ kΩ → effetto trascurabile sul segnale.
- Alimentazione presunta +5 V (lacuna L7): coerente col range serie 3..18 V, ma **da misurare** (Vdd-GND su U6).

## Limiti / attenzione

- ⚠️ **Il nome file inganna**: `hitachi_hd14066bp.pdf` non è il datasheet del 4066. La claim Ron 100–300 Ω resta **aperta**; per chiuderla serve scaricare il datasheet HD14066B (o equivalente CD4066) — non presente in `Prep\Datasheets\`.
- Nota manoscritta sul documento originale non interamente leggibile.
