# OKI MSM3764A — 65,536-word × 1-bit Dynamic RAM

| | |
|---|---|
| File PDF | `Prep\Datasheets\oki_msm3764.pdf` (18 pagine, scansionata) |
| Ref scheda | U1–U3 (×3, provvisorie) — marking `M3764-15RS / OKI / JAPAN / 44238` |
| Fonte PDF | OKI Memory Databook (databook pp. 61-66 e segg.) |
| Data verifica | 04/10/2026 |
| Metodo | Render 300 DPI di tutte le 18 pagine + OCR (rapidocr PP-OCRv3 + WinRT en-US) + **lettura visiva delle pagine chiave** (p01-p06); arbitro finale = visione nativa. Cache: `%TEMP%\opencode\ddx_ocr\oki_msm3764\` |

## Trascrizione utente (claim)

1. 150 ns (versione -15)
2. 192 Kbit
3. Refresh 128 cicli / 2 ms
4. Pin 8 = Vcc, pin 1 = Vss
5. Delay line 16.384 word × 12 bit

## Controverifica

| # | Claim utente | Esito | Riscontro nel PDF | Pag. |
|---|---|---|---|---|
| 1 | 150 ns (-15) | ✅ **CONFERMATO** | Row access time **150 ns max** per MSM3764A-15 (variante -12 = 120 ns); tRAC max 150 ns in tabella AC | p01, p05 |
| 2 | 192 Kbit | ⚠️ **DIFFORME (ma coerente col sistema)** | Il singolo chip è **65.536 × 1 = 64 Kbit**; i 192 Kbit sono la somma dei 3 chip della scheda (3 × 64 Kbit = 196.608 bit = 16.384 word × 12 bit, esattamente la delay line) | p01 |
| 3 | Refresh 128/2 ms | ✅ **CONFERMATO** | Features: "**128 refresh cycles/2 ms**"; tREF max 2 ms in tabella AC | p01, p05 |
| 4a | Pin 8 = Vcc | ✅ **CONFERMATO** | Pinout DIP-16: pin 8 = Vcc | p02 |
| 4b | Pin 1 = Vss | ⚠️ **DIFFORME (refuso nel datasheet)** | Il disegno DIP-16 del datasheet riporta pin 1 = **NC** ed etichetta "Vcc" sia a pin 8 sia a pin 16 e **non mostra Vss**: refuso del datasheet, poiché lo standard JEDEC 4164/64K×1 DIP-16 (verificato su 3 fonti: Sinclair Wiki, Citylan, cbm-hackers) ha pin 16 = GND/Vss, pin 8 = Vcc, pin 1 = NC. **Vss reale = pin 16**; se la scheda collega pin 1 a massa è una scelta di layout (NC tie a massa), non il pin di alimentazione | p02 |
| 5 | Delay line 16.384 word × 12 bit | ➕ **NON È UN DATASHEET** — claim di sistema (architettura del delay DDX-777); coerente: 16.384 × 12 = 196.608 bit = 3 × 64 Kbit | — |

## Trascrizione dati (p01–p06)

**Descrizione (p01):** NMOS DRAM fully decoded 65.536 × 1 bit; DIP-16 o PLCC-18 (JEDEC pinout); multiplexing riga/colonna; gate silicio NMOS a doppio polisilicio; celle a 1 transistor; timing non critico; tolleranza di alimentazione ampia; compatibile TTL.

**Features (p01):** accesso di riga 120 ns max (-12) / **150 ns max (-15)**; ciclo 220 ns min (-12) / 260 ns min (-15); basso consumo 330 mW attivo, 28 mW standby max; **+5 V ±10%**; uscita TTL three-state; gated CAS; **128 refresh/2 ms**; common I/O con early write; output non latched a fine ciclo; Read-Modify-Write, RAS-only refresh, page mode; latch on-chip indirizzi/data-in; **generatore di bias substrato on-chip (VBB)**.

**Pinout (p02):**
- DIP-16: 1=NC, 2=Din, 3=WE, 4=RAS, 5=A0*, 6=A2*, 7=A1*, **8=Vcc**, 9=A7, 10=A5*, 11=A4*, 12=A3*, 13=A6*, 14=Dout, 15=CAS, 16=disegnato "Vcc" (refuso; = Vss/GND, vedi esito 4b). (* = indirizzi di refresh)
- PLCC-18 (completo): 1=NC, 2=Din, 3=WE, 4=RAS, 5=NC, 6=A0*, 7=A2*, 8=A1*, 9=Vcc, 10=A7, 11=A5*, 12=A4*, 13=A3*, 14=NC, 15=A6*, 16=Dout, 17=CAS, 18=Vss.
- Nomi pin: A0-A7 address, RAS row strobe, CAS column strobe, WE write enable, Din/Dout data, Vcc +5 V, Vss 0 V, NC no connection.

**Abs max / consigliato (p03):**
- Abs max: ogni pin vs Vss −1..+7 V; VCC vs Vss −1..+7 V; Topr 0..70 °C; Tstg −55..+150 °C; PD 1,0 W; corto su uscita 50 mA.
- Consigliato (ref. Vss): Vcc 4,5/5,0/5,5 V; Vss 0 V; VIH 2,4..6,5 V; VIL −1,0..0,8 V; Ta 0..+70 °C.

**DC + capacitanze (p04):**
- ICC1 operating (RAS,CAS cycling, tRC=min) max 60 mA; ICC2 standby (RAS=CAS=VIH) max 5,0 mA; ICC3 refresh (RAS cycling, CAS=VIH) max 40 mA; ICC4 page mode max 60 mA.
- ILI/ILO typ −10, max ±10 µA; VOH (IOH=−5 mA) 2,4 V; VOL (IOL=4,2 mA) max 0,4 V.
- CIN1 (A0-A7, Din) max 5 pF; CIN2 (RAS, CAS, WE) max 8 pF; COUT max 7 pF (Ta=25 °C, 1 MHz).

**AC (p05) — MSM3764A-15:** tRC min 260; tRWC min 280; tPC min 145; **tRAC max 150**; tCAC max 75; tOFF 0..40; tT 3..35; tRP min 100; tRAS 150..10.000; tRSH min 75; tCP min 60; tCAS 75..10.000; tCSH min 150; tRCD 25..75; tCRP 0; tASR 0; tRAH 15; tASC 0; tCAH 20; tAR 95; tWCS −10; tWCH 45; tWRC 120; tWP 45; tRWL 45; tCWL 45; tDS 0; tDH 45; tDHR 120; tCWD 45; tRWD 120; tRRH 0; tCPN 35 (ns); tREF max **2 ms** (unità "ns" stampata nella tabella = refuso).
Variante -12: tRC 220, tRAC 120, tCAC 60, tRP 90, tRAS 120, tRCD 25..60, tPC 120, tCAS 60.

**Note (p06):** (1) pausa iniziale **100 µs dopo power-up**, poi minimo **8 cicli RAS** (es. RAS-only refresh) prima del funzionamento corretto; (2) misure AC con tempo di transizione tT = 5 ns; (3) VIH/VIL di riferimento per il timing; (6) carico equivalente 2 carichi TTL + 100 pF.

**p07–p18 (non quantificate):** p07-p10 diagrammi di timing (early write, RAS-only refresh, page-mode write, hidden refresh/read cycle); p11-p15 tipiche caratteristiche (ICC1-ICC4 vs Vcc, access time vs Vcc, indirizzo vs Vcc/Ta); p16 forme d'onda oscilloscopio (50 ns/div); p17 BIT MAP fisico (refresh addressing colonna A7); p18 pagina promozionale.

## Nota modello DSP

- La linea di delay usa 3 × MSM3764A condivisa con la LSI M60351 (16.384 word × 12 bit, f_camp ≈ 32 kHz, deduzione sessione 11): il claim "192 Kbit" resta corretto a livello di sistema.
- Il timing -15 (tRAC 150 ns) non limita il clock di sistema (~32 kHz ⇒ ciclo ≥ 31 µs).
- Per simulare il refresh: 128 cicli RAS ogni 2 ms + pausa iniziale 100 µs (8 RAS) dopo il power-up.
- **Non serve a modificare il plugin** (nessun parametro DSP deriva da questo datasheet).

## Limiti / note

- Datasheet scansionato: testo da OCR (rapidocr + WinRT) arbitrato da lettura visiva delle pagine p01-p06; p07-p18 elencate ma non trascritte numericamente.
- Esito 4b: il "Vss" della scheda non è verificabile dalle foto (ref designator non leggibili) → se serve, misura di continuità pin 1/pin 16 vs massa.
