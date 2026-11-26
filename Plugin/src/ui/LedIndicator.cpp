#include "LedIndicator.h"

void LedIndicator::paint (juce::Graphics& g)
{
    // 14-bis F1: bounds 8x8 * scala; disegno in coordinate di progetto.
    const float s = static_cast<float> (getWidth()) / 8.0f;
    g.addTransform (juce::AffineTransform::scale (s));
    const auto b = juce::Rectangle<float> (0.0f, 0.0f, 8.0f, 8.0f);

    // 17-fix4 Fix 3 (LED split T244): base + body sempre, glow on demand.
    // SrcOver e' sufficiente - il PNG del glow e' gia' progettato con
    // alpha variabile (rosso puro 255,0,0).  Se manca un layer base si
    // cade nel fallback procedurale sotto.
    if (base_.isValid() && body_.isValid())
    {
        base_.draw (g, b);
        body_.draw (g, b);

        // 18-fix (pattern T244): dual-mode.
        // meter (PEAK): glow additivo con alpha = value (0..1), spento per
        // value <= 0.02 (niente ghost).  status (HOLD/POWER): glow pieno.
        if (isMeter_)
        {
            if (glow_.isValid() && value_ > 0.02f)
            {
                g.setOpacity (value_);
                glow_.draw (g, b);
                g.setOpacity (1.0f);
            }
        }
        else if (on_ && glow_.isValid())
        {
            glow_.draw (g, b);
        }
        return;
    }

    if (on_)
    {
        // 14-ter F5: alone radiale #FF4030 alfa 110->0 su r4.6 (fillAll del
        // bounds 8x8), nucleo pieno, hot-spot #FF6A55 e highlight ovale bianco.
        g.setFillType (juce::FillType (juce::ColourGradient (ddxui::kLedOn.withAlpha (110.0f),
                                                             b.getCentreX(), b.getCentreY(),
                                                             ddxui::kLedOn.withAlpha (0.0f),
                                                             b.getCentreX() + 4.6f, b.getCentreY(),
                                                             true)));
        g.fillAll();
        g.setColour (ddxui::kLedOn);
        g.fillEllipse (b.reduced (1.0f));
        g.setColour (juce::Colour (0xffFF6A55));
        g.fillEllipse (juce::Rectangle<float> (b.getX() + 1.6f, b.getY() + 1.4f, 3.2f, 3.2f));
        g.setColour (juce::Colours::white.withAlpha (130.0f));
        g.fillEllipse (juce::Rectangle<float> (b.getX() + 2.0f, b.getY() + 1.5f, 2.6f, 2.0f));
    }
    else
    {
        g.setColour (ddxui::kLedOff);
        g.fillEllipse (b.reduced (1.0f));
        g.setColour (juce::Colours::black.withAlpha (120.0f));
        g.drawEllipse (b.reduced (1.0f), 1.0f);
    }
}
