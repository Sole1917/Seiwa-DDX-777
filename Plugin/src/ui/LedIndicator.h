#pragma once

#include <juce_gui_extra/juce_gui_extra.h>

#include <cmath>

#include "RackPanel.h"
#include "RenderedAsset.h"

// LED rosso (PEAK / HOLD / POWER).
//
// 17-fix4 Fix 3 (LED split T244): 3 layer forniti dall'utente
// (assets/imported/ -> assets/rendered/), 128x128 ciascuno:
//   led_base.png      bezel metallico       (sempre disegnato)
//   led_body_off.png  lente spenta          (sempre disegnato)
//   led_glow_on.png   glow rosso additivo   (ON pieno / meter con alpha=value)
// 18-fix (pattern T244): DUAL-MODE.
//   setOn(bool)     -> status: HOLD, POWER. Glow pieno solo quando on_.
//   setValue(v01)   -> meter:  PEAK (indicatore di livello). Glow additivo con
//                      alpha = v (0..1 continuo), spento per v <= 0.02 (niente
//                      ghost pixel). La curva envelope ha gia' release lento
//                      (~1 s tau): nessun peak-hold in questo fix.
//   OFF = base + body | status ON = base + body + glow pieno
//                    | meter    = base + body + glow con opacity v.
// Se un layer base non e' valido, fallback procedurale invariato (binario).
class LedIndicator : public juce::Component
{
public:
    LedIndicator()
    {
        base_.tryLoad ("led_base");
        body_.tryLoad ("led_body_off");
        glow_.tryLoad ("led_glow_on");

        // one-shot: conferma che i 3 layer sono entrati in BinaryData
        static bool logged = false;
        if (! logged)
        {
            logged = true;
            juce::Logger::writeToLog ("[17] LED hasAsset: base="
                                + juce::String (static_cast<int> (base_.isValid()))
                                + " body=" + juce::String (static_cast<int> (body_.isValid()))
                                + " glow=" + juce::String (static_cast<int> (glow_.isValid())));
        }
    }

    // status (HOLD, POWER): binario.
    void setOn (bool on)
    {
        isMeter_ = false;
        if (on != on_)
        {
            on_ = on;
            repaint();
        }
    }

    // meter (PEAK): livello 0..1 continuo, glow additivo.
    void setValue (float v01)
    {
        isMeter_ = true;
        v01 = juce::jlimit (0.0f, 1.0f, v01);
        if (std::abs (v01 - value_) > 0.001f)
        {
            value_ = v01;
            repaint();
        }
    }

    bool isOn() const noexcept   { return on_; }

    void paint (juce::Graphics& g) override;

private:
    bool isMeter_ = false;
    bool on_ = false;
    float value_ = 0.0f;
    RenderedAsset base_;
    RenderedAsset body_;
    RenderedAsset glow_;
};
