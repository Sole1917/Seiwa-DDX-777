#include "PluginProcessor.h"
#include "PluginEditor.h"

juce::AudioProcessorValueTreeState::ParameterLayout
SeiwaDDX777AudioProcessor::createParameterLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;

layout.add (std::make_unique<juce::AudioParameterFloat> (
        "INPUT_LEVEL", "INPUT_LEVEL",
        // 14-quater F8: interval 1.0 -> 0 (continuo, come FEEDBACK); la
        // mappatura knob->dB in makeCoreParams e' invariata (verify.py
        // invariato). numSteps() in Knob.cpp rileva l'interval -> 1000.
        juce::NormalisableRange<float> (0.0f, 10.0f),
        5.0f,
        juce::AudioParameterFloatAttributes()));

    layout.add (std::make_unique<juce::AudioParameterFloat> (
        "FEEDBACK", "FEEDBACK",
        juce::NormalisableRange<float> (0.0f, 1.0f), 0.5f,
        juce::AudioParameterFloatAttributes()
            .withStringFromValueFunction ([] (float v, int) { return juce::String (v, 2); })));

    layout.add (std::make_unique<juce::AudioParameterFloat> (
        "DELAY_LEVEL", "DELAY_LEVEL",
        juce::NormalisableRange<float> (0.0f, 1.0f), 0.5f,
        juce::AudioParameterFloatAttributes()
            .withStringFromValueFunction ([] (float v, int) { return juce::String (v, 2); })));

    layout.add (std::make_unique<juce::AudioParameterChoice> (
        "RANGE", "RANGE",
        juce::StringArray { "1", "2", "4", "8", "16", "32", "64", "128", "256", "512" }, 9));

    layout.add (std::make_unique<juce::AudioParameterFloat> (
        "FACTOR", "FACTOR",
        juce::NormalisableRange<float> (0.5f, 2.0f), 1.0f,
        juce::AudioParameterFloatAttributes()
            .withStringFromValueFunction ([] (float v, int)
            {
                auto s = juce::String (v, 2);
                while (s.endsWith ("0")) s = s.dropLastCharacters (1);
                if (s.endsWith (".")) s = s.dropLastCharacters (1);
                return juce::String::fromUTF8 ("\xc3\x97") + s;
            })));

    layout.add (std::make_unique<juce::AudioParameterFloat> (
        "MOD_SPEED", "MOD_SPEED",
        juce::NormalisableRange<float> (0.0f, 10.0f), 0.0f,
        juce::AudioParameterFloatAttributes()
            .withStringFromValueFunction ([] (float v, int) { return juce::String (v, 1); })));

    layout.add (std::make_unique<juce::AudioParameterFloat> (
        "MOD_DEPTH", "MOD_DEPTH",
        juce::NormalisableRange<float> (0.0f, 10.0f), 0.0f,
        juce::AudioParameterFloatAttributes()
            .withStringFromValueFunction ([] (float v, int) { return juce::String (v, 1); })));

    layout.add (std::make_unique<juce::AudioParameterBool> (
        "HOLD", "HOLD", false));

    layout.add (std::make_unique<juce::AudioParameterBool> (
        "POWER", "POWER", true));

    layout.add (std::make_unique<juce::AudioParameterBool> (
        "STEREO_MODE", "STEREO_MODE", false));

    // 14-bis F1: scala dell'interfaccia (50%..200%). Nessun controllo UI dedicato:
    // lo espone la DAW; l'editor lo legge in timerCallback e si ridimensiona.
    // Salvato con lo stato via params.copyState().
    // 14-f F5a: interval 0 (continuo): via DAW il param produce valori
    // arbitrari (es. 0.873), nessuno step a multipli di 0.05.
    layout.add (std::make_unique<juce::AudioParameterFloat> (
        "UI_SCALE", "UI_SCALE",
        juce::NormalisableRange<float> (0.5f, 2.0f), 1.0f,
        juce::AudioParameterFloatAttributes()
            .withStringFromValueFunction ([] (float v, int)
            {
                return juce::String (juce::roundToInt (v * 100.0f)) + juce::String::fromUTF8 (" %");
            })));

    return layout;
}

SeiwaDDX777AudioProcessor::SeiwaDDX777AudioProcessor()
    : AudioProcessor (BusesProperties()
                        .withInput ("Input", juce::AudioChannelSet::stereo(), true)
                        .withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      params (*this, nullptr, "PARAMETERS", createParameterLayout())
{
}

void SeiwaDDX777AudioProcessor::prepareToPlay (double sampleRate, int samplesPerBlock)
{
    coreL.prepare (sampleRate);
    coreR.prepare (sampleRate);
    work_.setSize (3, samplesPerBlock); // mono + outL + outR
    paramsInited_ = false;
    lastPowered_ = true;
    stereoModePrev_ = false;
    peakEnv_ = 0.0f;
    peakLed_ = false;
}

bool SeiwaDDX777AudioProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
    const auto& in = layouts.getMainInputChannelSet();
    const auto& out = layouts.getMainOutputChannelSet();

    if (in != out)
        return false;

    return in == juce::AudioChannelSet::mono() || in == juce::AudioChannelSet::stereo();
}

ddx::Params SeiwaDDX777AudioProcessor::makeCoreParams (uint32_t seed) const
{
    ddx::Params p;
    float inputLevelKnob = static_cast<float> (params.getRawParameterValue ("INPUT_LEVEL")->load());
    float inputLevelDb;
    if (inputLevelKnob <= 5.0f)
        inputLevelDb = -77.0f + inputLevelKnob * 12.604f;
    else
        inputLevelDb = -13.98f + (inputLevelKnob - 5.0f) * 4.0f;
    p.inputLevel = std::pow (10.0f, inputLevelDb / 20.0f);
    p.feedback   = static_cast<float> (params.getRawParameterValue ("FEEDBACK")->load());
    p.delayLevel = static_cast<float> (params.getRawParameterValue ("DELAY_LEVEL")->load());
    p.speed      = static_cast<float> (params.getRawParameterValue ("MOD_SPEED")->load()) * 0.1f;
    p.depth      = static_cast<float> (params.getRawParameterValue ("MOD_DEPTH")->load()) * 0.1f;
    p.rangeIdx   = juce::jlimit (0, 9,
                       static_cast<int> (params.getRawParameterValue ("RANGE")->load() + 0.5f));
    p.factor     = juce::jlimit (0.5f, 2.0f,
                       static_cast<float> (params.getRawParameterValue ("FACTOR")->load()));
    p.hold       = params.getRawParameterValue ("HOLD")->load() > 0.5f;
    p.seed       = seed;
    return p;
}

bool SeiwaDDX777AudioProcessor::paramsChanged (const ddx::Params& a, const ddx::Params& b)
{
    return a.inputLevel != b.inputLevel
        || a.feedback   != b.feedback
        || a.delayLevel != b.delayLevel
        || a.speed      != b.speed
        || a.depth      != b.depth
        || a.rangeIdx   != b.rangeIdx
        || a.factor     != b.factor
        || a.hold       != b.hold
        || a.organic    != b.organic
        || (a.organic && a.seed != b.seed);
}

void SeiwaDDX777AudioProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer&)
{
    juce::ScopedNoDenormals noDenormals;

    const int numSamples = buffer.getNumSamples();
    if (numSamples == 0)
        return;

    const bool powered = params.getRawParameterValue ("POWER")->load() > 0.5f;

    if (! powered)
    {
        if (lastPowered_)
        {
            coreL.reset();
            coreR.reset();
        }

        lastPowered_ = false;
        peakEnv_ = 0.0f;
        peakLed_ = false;

        // Bypass effetto: passa il dry con INPUT_LEVEL applicato
        // (stesso gain della chain attiva), senza delay/compressore/wet.
        const ddx::Params p = makeCoreParams (6242u);
        const float gIn = p.inputLevel;
        if (gIn != 1.0f)
            buffer.applyGain (gIn);
        return;
    }

    lastPowered_ = true;

    const bool stereoMode = params.getRawParameterValue ("STEREO_MODE")->load() > 0.5f;
    if (stereoMode && !stereoModePrev_)
        coreR.reset(); // toggle mono→stereo: delay memory coreR pulita
    stereoModePrev_ = stereoMode;

    // coreR organic solo in stereo; coreL fedele (mai organic) → mono identico a 13h
    ddx::Params pR = makeCoreParams (6243u);
    // 14-i: ORGANIC non e' piu' un parametro esposto. Diventa automatico in
    // modalita' stereo: il canale R ha tolleranze organiche dal seed 6243, il
    // canale L resta nominale (seed 6242). In mono, un solo core nominale.
    pR.organic = stereoMode;
    ddx::Params pL = pR;
    pL.seed = 6242u;
    pL.organic = false;

    // Confronto su pR: cattura anche il toggle STEREO_MODE (pR.organic =
    // stereoMode; pL.organic e' sempre false, quindi pL non lo vedrebbe).
    if (! paramsInited_ || paramsChanged (pR, lastParams_))
    {
        coreL.setParams (pL);
        coreR.setParams (pR);
        lastParams_ = pR;
        paramsInited_ = true;
    }

    const int numChannels = buffer.getNumChannels();

    float* chL = buffer.getWritePointer (0);
    float* chR = numChannels > 1 ? buffer.getWritePointer (1) : nullptr;

    // Downmix input: (L+R)/2 in stereo, altrimenti mono
    float* mono = work_.getWritePointer (0);
    if (chR != nullptr)
        for (int i = 0; i < numSamples; ++i)
            mono[i] = 0.5f * (chL[i] + chR[i]);
    else
        for (int i = 0; i < numSamples; ++i)
            mono[i] = chL[i];

    float* outL = work_.getWritePointer (1);
    float* outR = work_.getWritePointer (2);

    if (stereoMode)
    {
        coreL.process (mono, outL, nullptr, numSamples, nullptr); // L: seed 6242, fedele
        coreR.process (mono, outR, nullptr, numSamples, nullptr); // R: seed 6243, organico
        for (int i = 0; i < numSamples; ++i)
        {
            chL[i] = outL[i];
            if (chR != nullptr) chR[i] = outR[i];
        }
        peakEnv_ = static_cast<float> (std::max (coreL.peakEnvelope(), coreR.peakEnvelope()));
        peakLed_ = coreL.peakLedOn() || coreR.peakLedOn();
    }
    else
    {
        // Mono fedele: un solo core, output duplicato
        coreL.process (mono, outL, nullptr, numSamples, nullptr);
        for (int i = 0; i < numSamples; ++i)
        {
            chL[i] = outL[i];
            if (chR != nullptr) chR[i] = outL[i];
        }
        peakEnv_ = static_cast<float> (coreL.peakEnvelope());
        peakLed_ = coreL.peakLedOn();
    }
}

juce::AudioProcessorEditor* SeiwaDDX777AudioProcessor::createEditor()
{
    return new SeiwaDDX777AudioProcessorEditor (*this);
}

juce::AudioProcessorParameter* SeiwaDDX777AudioProcessor::getBypassParameter() const
{
    // 14-i: il bypass VST3 nativo e' mappato sul rocker POWER (unita' fisica).
    // Il wrapper JUCE non crea piu' il "Bypass" auto-generato: la lista
    // parametri del host mostra un solo bypass oltre a quello nativo VST3.
    return params.getParameter ("POWER");
}

void SeiwaDDX777AudioProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    if (auto xml = params.copyState().createXml())
        copyXmlToBinary (*xml, destData);
}

void SeiwaDDX777AudioProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    juce::MemoryBlock blob;
    blob.replaceAll (data, sizeInBytes);

    if (auto xml = getXmlFromBinary (blob.getData(), static_cast<int> (blob.getSize())))
    {
        if (xml->hasTagName (params.state.getType()))
            params.replaceState (juce::ValueTree::fromXml (*xml));
    }
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new SeiwaDDX777AudioProcessor();
}
