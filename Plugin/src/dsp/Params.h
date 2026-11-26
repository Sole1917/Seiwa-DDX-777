#pragma once

#include <algorithm>
#include <cstdint>

// Parametri e costanti del modello DDX-777 (fonte: HANDOFF_PLUGIN.md §4-§9).
namespace ddx
{

// RANGE: rotary 10 posizioni, scala serigrafata sul pannello (foto 830/836):
// 1, 2, 4, 8, 16, 32, 64, 128, 256, 512 ms (passi uniformi, 10 detent).
constexpr int kRangeMs[10] = { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512 };

// FACTOR: ×0.5 / ×1 / ×2.
constexpr float kFactorValues[3] = { 0.5f, 1.0f, 2.0f };

// Memoria delay: 3× DRAM 64K×1 = 192 Kbit, a 12 bit -> 16384 word.
constexpr int kMemoryWords = 16384;

// Parole per ms nominale: 16384 word / 512 ms = 32 word/ms.
constexpr double kWordsPerMs = 32.0;

// Clock nominale come misurato (sessione 11): 16384 word / 528 ms = 31030.3 Hz.
// Il trimmer hardware è già inclusso in questo valore (bias +3% sulle misure);
// il parametro trim espone ±3% attorno al comportamento misurato.
constexpr double kFbase = 16384.0 / 0.528; // = 31030.303... Hz

// Moltiplicatore di clock per FACTOR, calibrato sulle misure T1 @ RANGE 512:
//   ×0.5 -> 247 ms  => f = 16384/0.247 = 66333.6 Hz  (f/kFbase = 2.13770)
//   ×1   -> 528 ms  => f = 31030.3 Hz                 (1.0)
//   ×2   -> 960 ms  => f = 16384/0.960 = 17066.7 Hz   (f/kFbase = 0.55000)
// Modello: FACTOR scala il clock del VCO prima della divisione (§4/§9), la
// parola usata resta 32×RANGE (memoria sempre piena a RANGE 512).
constexpr double kFactorClock[3] = { (16384.0 / 0.247) / kFbase, 1.0, (16384.0 / 0.960) / kFbase };

// FACTOR continuo (0.5..2.0): interpolazione lineare a tratti sui 3 punti
// calibrati sopra. A f = 0.5 / 1.0 / 2.0 restituisce esattamente
// kFactorClock[0/1/2] (bit-identico alla tabella a 3 posizioni).
inline double factorClockFor (float f)
{
    f = std::clamp (f, 0.5f, 2.0f);
    const double lo = kFactorClock[0], mid = kFactorClock[1], hi = kFactorClock[2];

    if (f <= 0.5f) return lo;
    if (f >= 2.0f) return hi;
    if (f < 1.0f)  return lo + (mid - lo) * (static_cast<double> (f) - 0.5) / 0.5;
    return mid + (hi - mid) * (static_cast<double> (f) - 1.0);
}

// Risoluzione ADC/DAC: 12 bit (L5, sessione 11).
constexpr float kQ12 = 2047.0f; // scala full scale ±1 -> ±2047 LSB

struct Params
{
    float inputLevel  = 1.0f;  // pot PEAK LEVEL (M50kΩB, taper B=lineare) 0..1
    float feedback    = 0.5f;  // pot FEEDBACK LEVEL 0..1 -> bias DC/soglia compander
    float delayLevel  = 0.5f;  // pot DELAY LEVEL 0..1 (wet in mix)
    float speed       = 0.0f;  // pot MODULATION SPEED 0..1 -> freq LFO
    float depth       = 0.0f;  // pot MODULATION DEPTH 0..1 -> indice modulazione clock
    float peakLevel   = 0.5f;  // pot PEAK LEVEL (soglia LED, fuori segnale)
    int   rangeIdx    = 7;     // 0..9 -> 1,2,4,8,16,32,64,128,256,512 ms (default 512)
    float factor      = 1.0f;  // 0.5..2.0 continuo, default ×1 (clock: factorClockFor)
    bool  hold        = false; // rocker HOLD -> freeze (blocco scrittura)
    float trim        = 1.0f;  // trimmer calibrazione clock 0.97..1.03 (±3%)
    uint32_t seed     = 6242;  // seriale per variazioni organiche (§12)
    bool  organic     = false; // abilita tolleranze organiche dal seed (§12)
    bool  dither      = false; // dither TPDF sul quantizzatore (opzionale §7; l'hardware non lo ha)
    float hissMul     = 1.0f;  // moltiplica l'hiss analogico (calibrazione vs −77 dBFS)
};

inline int delayWordsFor (int rangeIdx)
{
    if (rangeIdx < 0) rangeIdx = 0;
    if (rangeIdx > 9) rangeIdx = 9;
    const int words = static_cast<int> (kWordsPerMs * kRangeMs[rangeIdx]);
    // Un buffer circolare di N word non può ritardare di ≥ N word: il puntatore
    // di lettura collasserebbe su quello di scrittura e il wet conterrebbe una
    // copia a delay ~0 oltre che una a delay pieno. Margine di 4 word per i
    // tap cubici (errore di delay −0.025%, ben entro la tolleranza ±1%).
    return words > kMemoryWords - 4 ? kMemoryWords - 4 : words;
}

} // namespace ddx
