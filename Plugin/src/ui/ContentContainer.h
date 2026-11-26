#pragma once

#include "PluginProcessor.h"

#include "RackPanel.h"
#include "Knob.h"
#include "LedIndicator.h"
#include "RockerSwitch.h"
#include "InputJack.h"

// 14-i: contenuto editor 1000x150 in coordinate di progetto pure. Nessuna
// scala interna: e' l'editor ad applicare il transform per fit/preview
// (AffineTransform via updateContentTransform in PluginEditor). Timeline
// annidata: il container possiede il timer a 30 Hz degli indicatori
// (LED/jack/stereo) — logica del contenuto, non della finestra.
class ContentContainer : public juce::Component,
                         private juce::Timer
{
public:
    explicit ContentContainer (SeiwaDDX777AudioProcessor&);
    ~ContentContainer() override = default;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    void timerCallback() override;

    SeiwaDDX777AudioProcessor& processor;
    RackPanel rack;
    InputJack jack;
    Knob peakKnob, feedbackKnob, delayKnob, rangeKnob, factorKnob, speedKnob, depthKnob;
    LedIndicator peakLed, holdLed, powerLed;
    RockerSwitch holdSwitch, powerSwitch;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (ContentContainer)
};
