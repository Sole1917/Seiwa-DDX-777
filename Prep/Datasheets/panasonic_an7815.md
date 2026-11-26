# Panasonic AN7815 — Regolatore positivo fisso 15 V, 1 A

| | |
|---|---|
| File PDF | `Prep\Datasheets\panasonic_an7815.pdf` (11 pagine, testo estraibile) |
| Ref scheda | U17 — marking `▲552 AN7815` (Panasonic), TO-220 su dissipatore |
| Fonte PDF | Panasonic AN78xx/AN78xxF Series Voltage Regulators (databook) |
| Data verifica | 04/10/2026 |
| Metodo | Estrazione testo PyMuPDF (fitz) su tutte le 11 pagine + **lettura visiva della tabella elettrica p06** (le colonne del testo estratto sono rimescolate); cache `%TEMP%\opencode\ddx_ocr\panasonic_an7815_fitz.txt` e `panasonic_an7815\p06.png` |

## Trascrizione utente (claim)

1. 15 V / 1 A
2. Ingresso 17,5–30 V
3. Uscita 14,4–15,6 V
4. Rumore 90 µV
5. Ripple rejection 54 dB

## Controverifica

| # | Claim utente | Esito | Riscontro nel PDF | Pag. |
|---|---|---|---|---|
| 1 | 15 V / 1 A | ✅ **CONFERMATO** | Titolo serie "**3-pin positive output voltage regulator (1 A type)**"; tabella "AN7815, 7815F (**15V type**)" | p01, p06 |
| 2 | In 17,5–30 V | ✅ **CONFERMATO** | Range di test **Line regulation: VI = 17,5 to 30 V** (e ΔIBias(IN) VI = 17,5 to 30 V) | p06 |
| 3 | Out 14,4–15,6 V | ✅ **CONFERMATO** | Output voltage VO (Tj=25 °C): **min 14,4 / typ 15 / max 15,6 V** | p06 |
| 4 | Rumore 90 µV | ✅ **CONFERMATO** | Output noise voltage Vno (f = 10 Hz–100 kHz): **typ 90 µV** | p06 |
| 5 | RRI 54 dB | ✅ **CONFERMATO** | Ripple rejection RR (VI = 18,5–28,5 V, f = 120 Hz): **min 54 dB** (è il minimo garantito; typ non stampato) | p06 |

## Trascrizione dati

**Overview (p01):** regolatore positivo fisso 3 pin, 11 tensioni (5/6/7/8/9/10/12/15/18/20/24 V), "current capacity of up to 1 A", nessun componente esterno; protezioni integrate: overcurrent limit, thermal overload, ASO (area of safe operation); block diagram (riferimento, error amp, current limiter, thermal protection). Package HSIP003-P-0000 (serie AN78xx) / -0000A (F). **Pinout: 1 = Input, 2 = Common, 3 = Output.**

**Abs max (p02, Ta=25 °C):** VI = **35 V** (AN7805..AN7818, incluso AN7815; 40 V per AN7820/24); PD = **15 W** (AN78xx) / 10,25 W (AN78xxF) *seguiti la curva di derating; sopra Tj 150 °C il circuito stacca l'uscita*; Topr −30..+80 °C; Tstg −55..+150 °C.

**Electrical Characteristics AN7815/7815F, Ta=25 °C (p06, letta visivamente):**

| Parametro | Condizioni | Min | Typ | Max | Unit |
|---|---|---|---|---|---|
| Output voltage VO | Tj=25 °C | **14,4** | **15** | **15,6** | V |
| Output voltage tolerance VO | VI=18–30 V, IO=5 mA–1 A, Tj=0–125 °C | 14,25 | — | 15,75 | V |
| Line regulation REGIN | VI=**17,5–30 V**, Tj=25 °C | — | 11 | 300 | mV |
| Line regulation REGIN | VI=20–26 V, Tj=25 °C | — | 3 | 150 | mV |
| Load regulation REGL | IO=5 mA–1,5 A | — | 12 | 300 | mV |
| Load regulation REGL | IO=250–750 mA | — | 4 | 150 | mV |
| Bias current IBias | Tj=25 °C | — | 4 | 8 | mA |
| ΔIBias(IN) | VI=17,5–30 V | — | — | 1 | mA |
| ΔIBias(L) | IO=5 mA–1 A | — | — | 0,5 | mA |
| Output noise voltage Vno | f=10 Hz–100 kHz | — | **90** | — | µV |
| Ripple rejection RR | VI=18,5–28,5 V, f=120 Hz | **54** | — | — | dB |
| Min in/out voltage diff. VDIF(min) | IO=1 A | — | 2 | — | V |
| Output impedance ZO | f=1 kHz | — | 19 | — | mΩ |
| Output short-circuit current IO(Short) | VI=30 V | — | 700 | — | mA |
| Peak output current IO(Peak) | Tj=25 °C | — | 2 | — | A |
| ΔVO/Ta | IO=5 mA, Tj=0–125 °C | — | −1 | — | mV/°C |

Note: (1) il test a Tj=25 °C va eseguito in <10 ms; (2) default test VI=23 V, IO=500 mA, CI=0,33 µF, CO=0,1 µF. Stessa pagina contiene anche la tabella AN7818 (18 V: VO 17,3/18/18,7; Vno 110 µV; RR min 53 dB).

## Nota modello DSP

- AN7815 = rail **+15 V analogico** (U17): alimenta M5224P, M5221, NE571, U11-U16 4558 — nessun effetto diretto sui parametri DSP del plugin.
- Utile per il modello di alimentazione: caduta minima 2 V a pieno carico, ripple sull'ingresso del regolatore attenuato di ≥54 dB (coerente con il rumore −67 dBFS misurato a valle).

## Limiti / note

- Testate/figure immagini: solo testo + lettura visiva di p06; le curve di transient/ripple (p07-p11) non sono state quantificate.
- Il valore 54 dB è minimo (nessun typ) — per il modello usare 54 dB come caso peggiore.
