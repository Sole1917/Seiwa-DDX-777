#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_extra/juce_gui_extra.h>

#include "RackPanel.h"
#include "RenderedAsset.h"

// Pannello INPUT: jack di linea 1/4" (+ secondo jack in modalita' stereo).
// Solo il titolo INPUT e' cliccabile (cursore a mano solo li'): un click
// sul titolo toggla STEREO_MODE, il resto dell'area ignora il mouse.
class InputJack : public juce::Component
{
public:
    explicit InputJack (juce::AudioParameterBool& stereoParam)
        : stereoParam_ (stereoParam)
    {
        setInterceptsMouseClicks (true, true);
        // 15: render 5 livelli (ASSET_BRIEF B.5): mono 52x52, stereo 124x60
        // (D2, era 76x52 nel brief). Assente -> fallback procedurale.
        assetMono_.tryLoad ("jack_mono");
        assetStereo_.tryLoad ("jack_stereo");
    }

    void setDual (bool dual)
    {
        if (dual_ != dual)
        {
            dual_ = dual;
            repaint();
        }
    }

    void paint (juce::Graphics&) override;

private:
    void mouseDown (const juce::MouseEvent&) override;
    void mouseMove (const juce::MouseEvent&) override;
    void mouseEnter (const juce::MouseEvent&) override;
    void mouseExit (const juce::MouseEvent&) override;

    juce::Rectangle<float> labelArea() const; // rettangolo hit del titolo INPUT
    void updateCursor (juce::Point<float>);

    juce::AudioParameterBool& stereoParam_;
    bool dual_ = false;

    // 15: asset per stato (mono 26x26 / stereo 62x30 in coordinate progetto).
    RenderedAsset assetMono_;
    RenderedAsset assetStereo_;

    JUCE_DECLARE_NON_COPYABLE (InputJack)
};
