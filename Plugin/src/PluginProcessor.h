#pragma once

#include <juce_audio_utils/juce_audio_utils.h>

#include "dsp/DDX777Core.h"

class SeiwaDDX777AudioProcessor : public juce::AudioProcessor
{
public:
    SeiwaDDX777AudioProcessor();
    ~SeiwaDDX777AudioProcessor() override = default;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported (const BusesLayout& layouts) const override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }
    juce::AudioProcessorParameter* getBypassParameter() const override;

    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 1.0; }

    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram (int) override {}
    const juce::String getProgramName (int) override { return {}; }
    void changeProgramName (int, const juce::String&) override {}

    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;

    juce::AudioProcessorValueTreeState& getParams() noexcept { return params; }
    bool getPeakLed() const noexcept { return peakLed_.get(); }
    float getPeakEnvelope() const noexcept { return peakEnv_.get(); }

private:
    static juce::AudioProcessorValueTreeState::ParameterLayout createParameterLayout();
    ddx::Params makeCoreParams (uint32_t seed) const;
    static bool paramsChanged (const ddx::Params& a, const ddx::Params& b);

    juce::AudioProcessorValueTreeState params;
    ddx::DDX777Core coreL, coreR;
    ddx::Params lastParams_ {};
    bool paramsInited_ = false;
    bool lastPowered_ = true;
    bool stereoModePrev_ = false;
    juce::AudioBuffer<float> work_; // 3 canali: mono, outL, outR (alloc. in prepareToPlay)
    juce::Atomic<float> peakEnv_ { 0.0f };
    juce::Atomic<bool> peakLed_ { false };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (SeiwaDDX777AudioProcessor)
};
