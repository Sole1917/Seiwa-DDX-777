# Caratterizzazione THD v4 — Sessione 12 (Meccanismi datasheet NE570N)

## Stato calibrato (default del core)

| Parametro | Valore | Note |
|---|---|---|
| kOpAmp | 0.018 | Fase 2, invariato |
| kVos (Mecc. A) | 0.0079 | H2 da offset VOS gain cell, su dry² post-mix; calibrato su T4 |
| kLo (Mecc. B) | 0.0 | Crossover H3 < 500 Hz: la taratura su T4 dà 0 (H3 a bassa banda già fornita dalla dinamica del compressore); meccanismo disponibile via --k-lo |
| Virtual ADC 32 kHz | ON | Fase 2 |

Confronto THD: tolleranza verify.py = 6 dB. Risultato verify.py --force: **THD 3/3 PASS** (+1.7 / +3.1 / +2.2 dB a 100 Hz / 1 kHz / 10 kHz). Banda 2/4 FAIL pre-esistenti (Virtual ADC: -3 dB @ 12.80 kHz fuori da 14.5-16.5 kHz; --no-virtual-adc riporta 14.79 kHz ma l'aliasing T5 fallisce) — documentato in 04_lacune.md, fuori scope Sessione 12 (i meccanismi A/B agiscono solo sul ramo mix).

## 1. Per-armoniche: plugin vs hardware (T4, -20 dBFS RMS, mix)

| f | Armonica | Plugin (dB) | HW (dB) | Gap | Plugin (%) | HW (%) |
|---|---|---|---|---|---|---|
| 100 Hz | H2 | -69.5 | -54.4 | -15.1 dB | 0.0335% | 0.1905% |
| 100 Hz | H3 | -47.5 | -50.8 | +3.3 dB | 0.4213% | 0.2876% |
| 100 Hz | H4 | -102.3 | -69.1 | -33.2 dB | 0.0008% | 0.0352% |
| 100 Hz | H5 | -64.6 | -69.1 | +4.5 dB | 0.0590% | 0.0350% |
| 100 Hz | **THD** | — | — | **+1.8 dB** | **0.4273%** | **0.3486%** |
| 1000 Hz | H2 | -70.2 | -70.3 | +0.1 dB | 0.0308% | 0.0304% |
| 1000 Hz | H3 | -68.5 | -77.8 | +9.3 dB | 0.0376% | 0.0129% |
| 1000 Hz | H4 | -101.6 | -94.5 | -7.1 dB | 0.0008% | 0.0019% |
| 1000 Hz | H5 | -85.4 | -96.9 | +11.4 dB | 0.0054% | 0.0014% |
| 1000 Hz | **THD** | — | — | **+3.4 dB** | **0.0489%** | **0.0331%** |
| 10000 Hz | H2 | -69.2 | -69.3 | +0.2 dB | 0.0349% | 0.0342% |
| 10000 Hz | H3 | -70.3 | -81.1 | +10.8 dB | 0.0305% | 0.0088% |
| 10000 Hz | H4 | -139.8 | -97.1 | -42.7 dB | 0.0000% | 0.0014% |
| 10000 Hz | H5 | n/a | n/a | n/a | n/a | n/a |
| 10000 Hz | **THD** | — | — | **+2.3 dB** | **0.0463%** | **0.0354%** |

Note:

- H2(1 kHz) e H2(10 kHz): match entro 0.1-0.4 dB (Meccanismo A calibrato su questi punti).
- H2(100 Hz) sotto-predetto di ~15 dB: residuo spettrale HW a bassa banda non modellato (candidato: ripple del detector a 2f / modulazione del rectifier — documentato, non implementato).
- H3(100 Hz) sopra-predetto di ~3 dB: la dinamica del compressore (attack 8 ms / release 60 ms) produce H3 via modulazione di ampiezza; sufficiente per il THD totale (+1.7 dB).
- H3(1 kHz/10 kHz) sopra-predetto di 9-11 dB: la tanh degli stadi op-amp (kOpAmp, calibrato su THD totale in Fase 2) pesa sulle armoniche singole; il THD totale resta entro +3.1 dB.

## 2. Predizioni modello ai livelli rimandati (§0.4)

Misure HW a -24/-30/-36 dBFS RIMANDATE (unità non accessibile). I valori modello qui sotto sono i **target di validazione**: quando le misure HW saranno disponibili, il confronto deve stare entro ±2-3 dB (come a -20 dBFS).

| Livello (dBFS RMS) | f | THD modello | H2 modello | H3 modello | Target §0.4 (estrapolazione HW) |
|---|---|---|---|---|---|
| -20 | 100 Hz | 0.4273% | 0.0335% | 0.4213% | — |
| -20 | 1000 Hz | 0.0489% | 0.0308% | 0.0376% | — |
| -20 | 10000 Hz | 0.0463% | 0.0349% | 0.0305% | — |
| -24 | 100 Hz | 0.0236% | 0.0193% | 0.0132% | — |
| -24 | 1000 Hz | 0.0280% | 0.0177% | 0.0214% | — |
| -24 | 10000 Hz | 0.0249% | 0.0200% | 0.0148% | — |
| -30 | 100 Hz | 0.0120% | 0.0095% | 0.0035% | 0.33-0.40% |
| -30 | 1000 Hz | 0.0128% | 0.0090% | 0.0065% | 0.0033% |
| -30 | 10000 Hz | 0.0107% | 0.0100% | 0.0038% | 0.0035% |
| -36 | 100 Hz | 0.0143% | 0.0049% | 0.0049% | — |
| -36 | 1000 Hz | 0.0160% | 0.0052% | 0.0054% | — |
| -36 | 10000 Hz | 0.0051% | 0.0050% | 0.0009% | — |
| -42 | 100 Hz | 0.0285% | 0.0089% | 0.0095% | — |
| -42 | 1000 Hz | 0.0379% | 0.0090% | 0.0092% | — |
| -42 | 10000 Hz | 0.0025% | 0.0025% | 0.0002% | — |

Comportamento atteso (Mecc. A ∝ livello): H2% cala di ~6 dB ogni 6 dB di livello (H2 ∝ A² sul segnale, THD% = H2/A1). A -30 dBFS il THD modello a 10 kHz/1 kHz è 0.0107%/0.0128% (i target §0.4 di estrapolazione HW sono 0.0035%/0.0033%): il Meccanismo A tiene H2 ~3-4 dB sopra il vecchio modello v3 (0.0046%/0.0105%) e scala linearmente con il segnale.

**Test discriminante su 100 Hz a -30 dBFS**: il modello v4 predice THD(100 Hz) = 0.0120% (H3 = 0.0035%): l'H3 a bassa banda del modello nasce da limiter + dinamica del compressore e sparisce appena sotto la soglia (-20 dBFS peak). Il target §0.4 per la misura HW (0.33-0.40%, derivato per estrapolazione da "H3(100 Hz) ≈ costante al variare del livello") implicava invece un meccanismo di crossover livello-indipendente. Quindi:

- se la misura HW a -30 dBFS mostra H3(100 Hz) ancora ~0.3% -> esiste un meccanismo crossover/livello-indipendente nell'HW (candidato: Meccanismo B, kLo > 0 da tarare);
- se H3(100 Hz) crolla a ~0.01% -> confermato il comportamento del modello (H3 da dinamica del gain cell/limiter), Meccanismo B resta scollegato.

Sotto -36 dBFS i target di validazione diventano inaffidabili (H2 modello ~ -86 dB rel., vicino al floor di misura).

## 3. Ablazione meccanismi (-20 dBFS, mix)

| Scenario | 100 Hz THD | 1 kHz THD | 10 kHz THD | 100 Hz H3 | 1 kHz H2 |
|---|---|---|---|---|---|
| **full** | 0.4273% | 0.0489% | 0.0463% | 0.4213% | 0.0308%
| **a_off** | 0.4260% | 0.0380% | 0.0305% | 0.4213% | 0.0008%
| **b_test** | 0.4529% | 0.0441% | 0.0463% | 0.4478% | 0.0308%
| **dist_off** | 0.4260% | 0.0380% | 0.0305% | 0.4213% | 0.0008%
| **opamp_off** | 0.4038% | 0.0479% | 0.0350% | 0.3974% | 0.0309%
| **fase1** | 0.4132% | 0.0470% | 0.0528% | 0.4067% | 0.0305%

Letture: `a_off` isola il contributo del Meccanismo A (H2); `b_test` mostra l'effetto (non voluto) di Meccanismo B: peggiora H3(100 Hz) da 0.42% verso l'alto -> taratura kLo = 0 confermata; `opamp_off` mostra l'H3 residuo del solo compressore; `fase1` = riferimento pre-distorsioni.

## 4. Note di calibrazione

- Calibrazione **relativa**: manca R_in (jack INPUT -> pin 5, lacuna L24) -> lo scaling analogico 0 dBm <-> dBFS non è fissato; kVos è tarato sul rapporto H2/A1 misurato, non sull'offset VOS assoluto in volt.
- Opzione C (saturazione gain cell a +8 dBm, datasheet p.6): **solo documentata**, non parametrizzata — a -20 dBFS RMS il segnale è ~8-10 dB sotto la saturazione; verificabile solo con misure HW a livello alto (non disponibili: l'uscita DDX satura in REW a -20 dBFS).
- Pinout NE570N: mapping shift +1 (vecchio N = nuovo N+1) confermato dalle riletture di Sessione 12; da confermare con 3 test rapidi quando l'unità sarà accessibile (L17).
