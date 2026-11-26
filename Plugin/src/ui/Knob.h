#pragma once

#include <juce_audio_processors/juce_audio_processors.h>

#include "RackPanel.h"
#include "RenderedAsset.h"

// Potenziometro del pannello: mozzo zigrinato, cappuccio colorato,
// indice triangolare crem, arco di tacche 270 gradi.
class Knob : public juce::Component,
             private juce::AudioProcessorParameter::Listener
{
public:
    enum class Style
    {
        Level010,   // 11 tacche, etichette 0 / 10
        Level0to20, // 11 tacche, etichette 0 / +20 (INPUT LEVEL)
        Range,      // 8 detent 1,8,16,...,512 (scala serigrafata, foto 830)
        Factor      // anello di 12 tacche a cerchio pieno, etichette x0.5 / x2
    };

    Knob (juce::RangedAudioParameter& parameter, const juce::Colour& capColour, Style style);
    ~Knob() override;

    void paint (juce::Graphics& g) override;

private:
    void parameterValueChanged (int, float) override { repaint(); }
    void parameterGestureChanged (int, bool) override {}

    void mouseDown (const juce::MouseEvent& e) override;
    void mouseDrag (const juce::MouseEvent& e) override;
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails& details) override;

    float value01() const;
    int numSteps() const;
    void setValue01 (float v);

    juce::RangedAudioParameter& parameter;
    const juce::Colour capColour;
    const Style style;
    float dragStartY = 0.0f;
    float dragStartValue = 0.0f;
    bool dragging = false;

    // 15: filmstrip del cappuccio knob_<colore>_filmstrip, 64 frame da
    // 192x192 (ASSET_BRIEF B.5). Assente -> fallback procedurale. La corona
    // (tacche/numerali) resta SEMPRE procedurale, sotto l'asset (D9).
    RenderedAsset asset_;

    JUCE_DECLARE_NON_COPYABLE (Knob)
};
