#pragma once

#include <algorithm>
#include <cmath>

#include "Params.h"

namespace ddx
{

// Linea di delay: buffer circolare di 16384 word a 12 bit (float in [-1,1]).
// Le posizioni sono in "parole" con parte frazionaria; la lettura usa
// interpolazione cubica Catmull-Rom (ricostruzione del DAC).
class DelayLine
{
public:
    void clear()
    {
        for (auto& w : buf_) w = 0.0f;
    }

    void write (int wordIndex, float value) noexcept
    {
        buf_[wordIndex & (kMemoryWords - 1)] = value;
    }

    // pos in [0, kMemoryWords), frazionaria
    float readCubic (double pos) const noexcept
    {
        while (pos < 0.0) pos += kMemoryWords;
        while (pos >= kMemoryWords) pos -= kMemoryWords;

        const long i1 = static_cast<long> (pos);
        const double f = pos - static_cast<double> (i1);
        const long i0 = (i1 - 1) & (kMemoryWords - 1);
        const long i2 = (i1 + 1) & (kMemoryWords - 1);
        const long i3 = (i1 + 2) & (kMemoryWords - 1);

        const double y0 = buf_[i0], y1 = buf_[i1 & (kMemoryWords - 1)], y2 = buf_[i2], y3 = buf_[i3];

        const double a = -0.5 * y0 + 1.5 * y1 - 1.5 * y2 + 0.5 * y3;
        const double b = y0 - 2.5 * y1 + 2.0 * y2 - 0.5 * y3;
        const double c = -0.5 * y0 + 0.5 * y2;
        const double d = y1;

        return static_cast<float> (((a * f + b) * f + c) * f + d);
    }

private:
    float buf_[kMemoryWords] = {};
};

// Quantizzatore ADC 12 bit con dither TPDF ±1 LSB e hard-clip full scale.
inline float quantize12 (float x, float ditherLsb) noexcept
{
    if (x > 1.0f)  x = 1.0f;
    if (x < -1.0f) x = -1.0f;

    const float v = x * kQ12 + ditherLsb;
    float r = std::floor (v + 0.5f);
    if (r > kQ12)  r = kQ12;
    if (r < -kQ12 - 1.0f) r = -kQ12 - 1.0f;
    return r / kQ12;
}

} // namespace ddx
