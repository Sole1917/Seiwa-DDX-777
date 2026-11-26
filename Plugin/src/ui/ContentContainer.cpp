#include "ContentContainer.h"

ContentContainer::ContentContainer (SeiwaDDX777AudioProcessor& p)
    : processor (p),
      peakKnob (*processor.getParams().getParameter ("INPUT_LEVEL"), ddxui::kCapOrange, Knob::Style::Level010),
      feedbackKnob (*processor.getParams().getParameter ("FEEDBACK"), ddxui::kCapGreen, Knob::Style::Level010),
      delayKnob (*processor.getParams().getParameter ("DELAY_LEVEL"), ddxui::kCapYellow, Knob::Style::Level010),
      rangeKnob (*processor.getParams().getParameter ("RANGE"), ddxui::kCapBlue, Knob::Style::Range),
      factorKnob (*processor.getParams().getParameter ("FACTOR"), ddxui::kCapGreen, Knob::Style::Factor),
      speedKnob (*processor.getParams().getParameter ("MOD_SPEED"), ddxui::kCapOrange, Knob::Style::Level010),
      depthKnob (*processor.getParams().getParameter ("MOD_DEPTH"), ddxui::kCapYellow, Knob::Style::Level010),
      // 14-e R6 / 14-g G4: POWER 36x36 (era 44x44, asse x972 invariato,
      // bounds 954..990), HOLD 22x44 (parallelepipedo, bounds 602..624);
      // centrati su knobCY75 -> y53..89 (POWER) / y53..97 (HOLD).
      // 15: 4° argomento = prefisso asset renderizzato (ASSET_BRIEF B.5);
      // assente in assets/rendered/ -> fallback procedurale invariato.
      holdSwitch (*processor.getParams().getParameter ("HOLD"), 22.0f, 44.0f, "rocker_hold"),
      powerSwitch (*processor.getParams().getParameter ("POWER"), 36.0f, 36.0f, "rocker_power"),
      jack (*dynamic_cast<juce::AudioParameterBool*>(
                processor.getParams().getParameter ("STEREO_MODE")))
{
    addAndMakeVisible (rack);
    addAndMakeVisible (jack);
    addAndMakeVisible (peakKnob);
    addAndMakeVisible (feedbackKnob);
    addAndMakeVisible (delayKnob);
    addAndMakeVisible (rangeKnob);
    addAndMakeVisible (factorKnob);
    addAndMakeVisible (speedKnob);
    addAndMakeVisible (depthKnob);
    addAndMakeVisible (peakLed);
    addAndMakeVisible (holdLed);
    addAndMakeVisible (powerLed);
    addAndMakeVisible (holdSwitch);
    addAndMakeVisible (powerSwitch);

    powerLed.setOn (processor.getParams().getRawParameterValue ("POWER")->load() > 0.5f);

    startTimerHz (30);
}

void ContentContainer::paint (juce::Graphics&)
{
}

void ContentContainer::resized()
{
    // 14-i: coordinate di progetto pure (1000x150), nessuna scala interna.
    // Il transform di preview/fit e' solo dell'editor (PluginEditor::resized).
    rack.setBounds (0, 0, ddxui::Layout::kW, ddxui::Layout::kH);

    jack.setBounds (ddxui::Layout::inX0,
                    ddxui::Layout::inputY0, 119, 80); // jacks + hit-area titolo INPUT

    auto K = [] (int cx)
    {
        return juce::Rectangle<int> (cx - 48,
                                     ddxui::Layout::knobCY - 48, 96, 96);
    };
    peakKnob.setBounds (K (ddxui::Layout::peakX));
    feedbackKnob.setBounds (K (ddxui::Layout::fbX));
    delayKnob.setBounds (K (ddxui::Layout::dlX));
    rangeKnob.setBounds (K (ddxui::Layout::rangeX));
    factorKnob.setBounds (K (ddxui::Layout::factorX));
    speedKnob.setBounds (K (ddxui::Layout::speedX));
    depthKnob.setBounds (K (ddxui::Layout::depthX));

    // 14-ter F4: PEAK/HOLD LED a y23, POWER LED a y28 (Layout::ledY).
    auto L = [] (int cx, int y)
    {
        return juce::Rectangle<int> (cx - 4, y, 8, 8);
    };
    peakLed.setBounds (L (ddxui::Layout::peakLedX, ddxui::Layout::peakLedY));
    holdLed.setBounds (L (ddxui::Layout::holdLedX, ddxui::Layout::holdLedY));
    powerLed.setBounds (L (ddxui::Layout::powerLedX, ddxui::Layout::ledY));

    // 14-g G4: POWER 36x36 (bounds 954..990, cx972 invariato, 4px per lato
    // ridotti), HOLD 22x44 (bounds 602..624, centro 613 = LED/label);
    // entrambi centrati su knobCY75 -> y53..89 / y53..97.
    holdSwitch.setBounds (ddxui::Layout::holdSwX - 11, 53, 22, 44);
    powerSwitch.setBounds (ddxui::Layout::powerSwX - 18, 53, 36, 36);
}

void ContentContainer::timerCallback()
{
    // 18-fix (T244): PEAK e' un livello continuo (envelope 0..1), non binario.
    peakLed.setValue (processor.getPeakEnvelope());

    // HOLD e POWER restano binari (status).
    holdLed.setOn (processor.getParams().getRawParameterValue ("HOLD")->load() > 0.5f);
    powerLed.setOn (processor.getParams().getRawParameterValue ("POWER")->load() > 0.5f);

    const bool stereo = processor.getParams().getRawParameterValue ("STEREO_MODE")->load() > 0.5f;
    jack.setDual (stereo);
    rack.setStereoOn (stereo); // repaint su cambio (nessun fade, 14-B)
}
