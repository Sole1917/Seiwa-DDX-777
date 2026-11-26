#pragma once

#include <cmath>

namespace ddx
{

// Hard Limiter modellato su NE571 canale 1 (limiter mode) — FASE 1 + FASE 2.
//
// Due componenti:
// 1. Detector lento (attack/release 8/60 ms): gain DC sopra soglia -20 dBFS
//    (comportamento Fase 1, match 100 Hz / 1 kHz).
// 2. Rectifier full-wave con banda finita (one-pole @ 20 kHz, componente 2):
//    il segnale di controllo ha ripple a 2×f; il gain è modulato
//    proporzionalmente alla parte sopra soglia. kRect = 0 → trasparente
//    (baseline Fase 1).
class Compressor
{
public:
    void prepare (double fs)
    {
        fs_ = fs;
        setDetectorTimes (attackSec_, releaseSec_);
        const double tau20 = 1.0 / (2.0 * 3.14159265358979323846 * 20000.0); // ~8 µs
        kr20_ = 1.0 - std::exp (-fs_ * tau20);
        thrLin_ = std::pow (10.0, thrDb_ * 0.05);
        detSlow_ = 0.0;
        rectFast_ = 0.0;
    }

    void reset()
    {
        detSlow_ = 0.0;
        rectFast_ = 0.0;
    }

    // tau_a / tau_r in secondi (detector lento, attack/release NE571)
    void setDetectorTimes (double tauA, double tauR)
    {
        attackSec_ = tauA;
        releaseSec_ = tauR;
        ka_ = 1.0 - std::exp (-1.0 / (fs_ * tauA));
        kr_ = 1.0 - std::exp (-1.0 / (fs_ * tauR));
    }

    // Soglia in dBFS peak (default -20)
    void configure (double thresholdDb)
    {
        thrDb_ = thresholdDb;
        thrLin_ = std::pow (10.0, thrDb_ * 0.05);
    }

    // Coefficiente di modulazione del gain dal rectifier rapido (0 = Fase 1)
    void setKRect (double k) { kRect_ = k; }

    // Bypass per caratterizzazione THD
    void setDisabled (bool d) { disabled_ = d; }

    float process (float x) noexcept
    {
        if (disabled_) return x;

        const double rect = std::fabs (static_cast<double> (x));

        // 1) Detector lento: gain DC sopra soglia (Fase 1)
        detSlow_ += (rect > detSlow_ ? ka_ : kr_) * (rect - detSlow_);
        const double levelDb = 20.0 * std::log10 (detSlow_ + 1.0e-9);
        const double overSlow = levelDb - thrDb_;
        const double gSlowDb = (overSlow > 0.0) ? -overSlow : 0.0;

        // 2) Rectifier banda-finita (Comp 2): ripple a 2×f
        rectFast_ += kr20_ * (rect - rectFast_);

        // Modulazione del gain: solo sopra soglia, su parte AC sopra il DC
        double gRipple = 0.0;
        if (detSlow_ > thrLin_ && kRect_ != 0.0)
        {
            const double excessAc = rectFast_ - detSlow_;
            gRipple = -kRect_ * (excessAc > 0.0 ? excessAc : 0.0);
        }

        const double gain = std::pow (10.0, gSlowDb * 0.05) * (1.0 + gRipple);
        return static_cast<float> (static_cast<double> (x) * gain);
    }

    double thresholdDb() const noexcept { return thrDb_; }

private:
    double fs_ = 48000.0;
    double attackSec_ = 0.008;
    double releaseSec_ = 0.06;
    double ka_ = 0.0013, kr_ = 0.000173;
    double detSlow_ = 0.0;
    double rectFast_ = 0.0;
    double kr20_ = 0.0;    // one-pole 20 kHz sul rectifier
    double thrDb_ = -20.0;
    double thrLin_ = 0.1;
    double kRect_ = 0.0;
    bool disabled_ = false;
};

} // namespace ddx