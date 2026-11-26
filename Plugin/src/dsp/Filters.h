#pragma once

#include <cmath>

namespace ddx
{

// Biquad RBJ (transposed direct form II).
class Biquad
{
public:
    void setLowpass (double fs, double freq, double q)
    {
        const double w0 = 2.0 * 3.14159265358979323846 * freq / fs;
        const double cw = std::cos (w0), sw = std::sin (w0);
        const double alpha = sw / (2.0 * q);

        const double b0 = (1.0 - cw) / 2.0, b1 = 1.0 - cw, b2 = (1.0 - cw) / 2.0;
        const double a0 = 1.0 + alpha, a1 = -2.0 * cw, a2 = 1.0 - alpha;

        b0_ = b0 / a0; b1_ = b1 / a0; b2_ = b2 / a0;
        a1_ = a1 / a0; a2_ = a2 / a0;
    }

    // RBJ peaking EQ
    void setPeak (double fs, double freq, double q, double gainDb)
    {
        const double A = std::pow (10.0, gainDb / 40.0);
        const double w0 = 2.0 * 3.14159265358979323846 * freq / fs;
        const double cw = std::cos (w0), sw = std::sin (w0);
        const double alpha = sw / (2.0 * q);

        const double b0 = 1.0 + alpha * A, b1 = -2.0 * cw, b2 = 1.0 - alpha * A;
        const double a0 = 1.0 + alpha / A, a1 = -2.0 * cw, a2 = 1.0 - alpha / A;

        b0_ = b0 / a0; b1_ = b1 / a0; b2_ = b2 / a0;
        a1_ = a1 / a0; a2_ = a2 / a0;
    }

    // RBJ high shelf
    void setHighShelf (double fs, double freq, double q, double gainDb)
    {
        const double A = std::pow (10.0, gainDb / 40.0);
        const double w0 = 2.0 * 3.14159265358979323846 * freq / fs;
        const double cw = std::cos (w0), sw = std::sin (w0);
        const double alpha = sw / (2.0 * q);
        const double t = 2.0 * std::sqrt (A) * alpha;

        const double b0 = A * ((A + 1.0) + (A - 1.0) * cw + t);
        const double b1 = -2.0 * A * ((A - 1.0) + (A + 1.0) * cw);
        const double b2 = A * ((A + 1.0) + (A - 1.0) * cw - t);
        const double a0 = (A + 1.0) - (A - 1.0) * cw + t;
        const double a1 = 2.0 * ((A - 1.0) - (A + 1.0) * cw);
        const double a2 = (A + 1.0) - (A - 1.0) * cw - t;

        b0_ = b0 / a0; b1_ = b1 / a0; b2_ = b2 / a0;
        a1_ = a1 / a0; a2_ = a2 / a0;
    }

    void reset() { z1_ = z2_ = 0.0; }

    float process (float x)
    {
        const double y = b0_ * x + z1_;
        z1_ = b1_ * x - a1_ * y + z2_;
        z2_ = b2_ * x - a2_ * y;
        return static_cast<float> (y);
    }

private:
    double b0_ = 1.0, b1_ = 0.0, b2_ = 0.0, a1_ = 0.0, a2_ = 0.0;
    double z1_ = 0.0, z2_ = 0.0;
};

// Generatore pseudo-casuale deterministico (xorshift32) per dither/hiss.
class Rng
{
public:
    explicit Rng (uint32_t seed = 0x9e3779b9u) : s_ (seed ? seed : 1u) {}

    uint32_t nextUint()
    {
        uint32_t x = s_;
        x ^= x << 13; x ^= x >> 17; x ^= x << 5;
        s_ = x;
        return x;
    }

    // uniforme in [-1, 1)
    float nextBipolar()
    {
        return static_cast<float> (nextUint() * (1.0 / 2147483648.0)) - 1.0f;
    }

private:
    uint32_t s_;
};

} // namespace ddx
