#include "PluginEditor.h"

#include <cmath>

namespace
{

// 14-bis F1: scala UI letta dal parametro APVTS (default 1.0 = 1000x150).
float readUiScale (SeiwaDDX777AudioProcessor& p)
{
    if (auto* v = p.getParams().getRawParameterValue ("UI_SCALE"))
        return juce::jlimit (0.5f, 2.0f, v->load());

    return 1.0f;
}

juce::Rectangle<int> scaledEditorSize (float s)
{
    return juce::Rectangle<int> (juce::roundToInt (ddxui::Layout::kW * s),
                                 juce::roundToInt (ddxui::Layout::kH * s));
}

} // namespace

SeiwaDDX777AudioProcessorEditor::SeiwaDDX777AudioProcessorEditor (SeiwaDDX777AudioProcessor& p)
    : AudioProcessorEditor (&p),
      processor (p),
      content (p)
{
    // 18: UNA sola setSize al caricamento, dimensionata da UI_SCALE (fallback
    // iniziale). Da qui in poi il contenuto scala sempre via transform: nessun
    // altro setSize (tranne l'unica richiesta del grip a mouseUp). Constrainer
    // permissivo su [500,75,2000,300] per sempre (mai min=max: Reaper lo usa
    // in checkSizeConstraint per clampare -> flip-flop).
    baseScale = readUiScale (processor);
    const auto size = scaledEditorSize (baseScale);
    setSize (size.getWidth(), size.getHeight());
    setResizeLimits (500, 75, 2000, 300);

    addAndMakeVisible (content);
    addAndMakeVisible (resizeGrip);

    startTimerHz (30);
}

void SeiwaDDX777AudioProcessorEditor::paint (juce::Graphics& g)
{
    // 18: sfondo chassis durante il letterboxing (tutto il contenuto vive nel
    // ContentContainer scalato; qui non c'e' nulla da disegnare).
    g.fillAll (ddxui::kPanelTop);
}

void SeiwaDDX777AudioProcessorEditor::resized()
{
    // 18: canvas interno sempre 1000x150 (coordinate di progetto).
    content.setBounds (0, 0, ddxui::Layout::kW, ddxui::Layout::kH);

    // Resize host-driven (bordo finestra): baseScale = fit della finestra.
    // Non durante il drag (la scala la tiene previewScale) ne' quando la
    // UI_SCALE del DAW/preset ha vinto (timerCallback).
    if (! resizeGrip.isBeingDragged() && previewScale <= 0.0f)
        baseScale = juce::jlimit (0.5f, 4.0f,
                                  juce::jmin (static_cast<float> (getWidth())  / ddxui::Layout::kW,
                                              static_cast<float> (getHeight()) / ddxui::Layout::kH));

    updateContentTransform();

    // Grip in angolo basso-destro, 20x20 pixel reali (non scala col contenuto).
    const int gripSize = 20;
    resizeGrip.setBounds (getWidth()  - gripSize,
                          getHeight() - gripSize,
                          gripSize, gripSize);
}

void SeiwaDDX777AudioProcessorEditor::setPreviewScale (float s)
{
    previewScale = s;
    updateContentTransform();
}

void SeiwaDDX777AudioProcessorEditor::clearPreviewScale()
{
    previewScale = -1.0f;
    updateContentTransform();
}

void SeiwaDDX777AudioProcessorEditor::updateContentTransform()
{
    // 18: scala = preview (drag grip) se attiva, altrimenti baseScale.
    // Il canvas e' sempre 1000x150; la finestra puo' essere qualsiasi
    // dimensione -> letterbox centrato.
    const float s = (previewScale > 0.0f) ? previewScale : baseScale;

    const float ox = 0.5f * (static_cast<float> (getWidth())  - ddxui::Layout::kW * s);
    const float oy = 0.5f * (static_cast<float> (getHeight()) - ddxui::Layout::kH * s);

    content.setTransform (juce::AffineTransform::scale (s).translated (ox, oy));
    content.repaint();
}

void SeiwaDDX777AudioProcessorEditor::timerCallback()
{
    // 18: nessun setSize, nessun flip. Se UI_SCALE cambia (DAW/preset),
    // baseScale lo segue e il contenuto scala in place via transform.
    // Il resto del timer (LED/jack/stereo) e' del ContentContainer.
    if (! resizeGrip.isBeingDragged() && previewScale <= 0.0f)
    {
        const float s = readUiScale (processor);
        if (! juce::approximatelyEqual (s, baseScale))
        {
            baseScale = s;
            updateContentTransform();
        }
    }
}
