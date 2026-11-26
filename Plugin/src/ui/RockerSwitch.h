#pragma once

#include <juce_audio_processors/juce_audio_processors.h>

#include "RackPanel.h"
#include "RenderedAsset.h"

// Rocker switch nero (HOLD / POWER) — 14-h H1: corpo pieno (off kRockerLo
// #101113 / on kRockerHi #3A3D44) + glint hairline caldo SOLO in OFF
// (boundsTop+1, α28; la scomparsa al press = senso di rientranza) + bordo
// grigio #808080 1.2px. NESSUNA ombra, NESSUNA traslazione, NESSUN
// setPaintingIsUnclipped: tutto il paint sta entro bounds (reduced(1)).
// Paint stateless (pure function di isOn): nessun residuo da click cycle.
class RockerSwitch : public juce::Component,
                     private juce::AudioProcessorParameter::Listener
{
public:
    // projectW/H: dimensioni in coordinate di progetto (1000x150).
    // POWER 36x36 (14-g G4), HOLD 22x44 (14-e R6).
    // assetBase (15): prefisso asset opzionale "rocker_power"/"rocker_hold" ->
    // prova a caricare <base>_on e <base>_off (ASSET_BRIEF B.5); vuoto o
    // assente -> fallback procedurale invariato.
    RockerSwitch (juce::RangedAudioParameter& parameter, float projectW, float projectH,
                  const juce::String& assetBase = {});
    ~RockerSwitch() override;

    bool isOn() const noexcept   { return parameter.getValue() > 0.5f; }

    void paint (juce::Graphics& g) override;

private:
    void parameterValueChanged (int, float) override { repaint(); }
    void parameterGestureChanged (int, bool) override {}

    void mouseDown (const juce::MouseEvent&) override
    {
        parameter.setValueNotifyingHost (isOn() ? 0.0f : 1.0f);
    }

    juce::RangedAudioParameter& parameter;
    float projectW_, projectH_;

    // 15: render per stato (72x72 power / 44x88 hold, bordo incluso, B.5).
    RenderedAsset assetOn_;
    RenderedAsset assetOff_;

    JUCE_DECLARE_NON_COPYABLE (RockerSwitch)
};
