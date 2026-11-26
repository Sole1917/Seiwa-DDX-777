#pragma once

#include <cstdint>

namespace ddx
{

// §12 — "secondo canale organico": variazioni deterministiche derivate dal
// seriale. Tolleranze: R ±5%, C ±10%, hFE ±20%, ESR +20%, trimmer ±2%.
// Lo stesso seriale produce sempre le stesse tolleranze (seed deterministico).
struct Tolerances
{
    double clock    = 1.0; // moltiplica f_camp (trimmer, ±2%)
    double cutoff   = 1.0; // scala le frequenze dei filtri (C ±10%)
    double noise    = 1.0; // livello hiss/analogico (R ±5%, hFE ±20%)
    double detector = 1.0; // scala attack/release NE571 (C/R tolerance)
    double thrDb    = 0.0; // offset soglia compander (±1.5 dB)
};

inline Tolerances tolerancesFor (uint32_t serial)
{
    uint32_t s = serial * 2654435761u + 0x9e3779b9u;
    if (s == 0) s = 1;

    auto next01 = [&s]() -> double
    {
        s ^= s << 13; s ^= s >> 17; s ^= s << 5;
        return ((s >> 8) * (1.0 / 16777216.0)); // uniforme 24 bit
    };

    Tolerances t;
    t.clock    = 1.0 + (next01() - 0.5) * 0.04;  // ±2%
    t.cutoff   = 1.0 + (next01() - 0.5) * 0.20;  // ±10%
    t.noise    = 1.0 + (next01() - 0.5) * 0.50;  // ±25%
    t.detector = 1.0 + (next01() - 0.5) * 0.40;  // ±20%
    t.thrDb    = (next01() - 0.5) * 3.0;         // ±1.5 dB
    return t;
}

} // namespace ddx
