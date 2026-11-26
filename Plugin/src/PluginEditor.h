#pragma once

#include "PluginProcessor.h"

#include "ui/ContentContainer.h"
#include "ui/ResizeGrip.h"

// 18: editor a CANVAS FISSO 1000x150. Owna il ContentContainer (contenuto in
// coordinate progetto, mai ridimensionato) e il ResizeGrip (angolo basso
// destro, 20x20 pixel reali). L'editor NON chiama mai setSize tranne che nel
// costruttore (ultima richiesta del grip a mouseUp): la scala e' sempre un
// AffineTransform via updateContentTransform(). previewScale > 0 = preview del
// drag grip (finestra ferma); altrimenti baseScale = scala persistente
// (UI_SCALE param, fallback = fit della finestra host, che e' libera).
class SeiwaDDX777AudioProcessorEditor : public juce::AudioProcessorEditor,
                                        private juce::Timer
{
public:
    explicit SeiwaDDX777AudioProcessorEditor (SeiwaDDX777AudioProcessor&);
    ~SeiwaDDX777AudioProcessorEditor() override = default;

    void paint (juce::Graphics&) override;
    void resized() override;

    // Usati dal ResizeGrip durante il drag (preview scale, senza setSize).
    void setPreviewScale (float s);
    void clearPreviewScale();

private:
    void timerCallback() override;
    void updateContentTransform();

    SeiwaDDX777AudioProcessor& processor;
    ContentContainer content;
    ResizeGrip resizeGrip { *processor.getParams().getParameter ("UI_SCALE") };

    float previewScale = -1.0f; // >0: preview dal grip (drag in corso); <0: usa baseScale
    float baseScale = 1.0f;     // scala persistente: UI_SCALE param o fit della finestra

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (SeiwaDDX777AudioProcessorEditor)
};
