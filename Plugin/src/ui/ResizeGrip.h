#pragma once

#include <juce_audio_processors/juce_audio_processors.h>

#include "RackPanel.h"

// 14-quater F6 / 14-e R1 / 14-f F5 / 14-g G5 / 14-i / 18 refactor: triangolo
// "__/" nell'angolo basso-destro della FINESTRA (20x20 pixel reali, figlio
// dell'editor, mai scalato col contenuto). Drag diagonale -> UI_SCALE 0.5..2.0
// CONTINUO. FONTE DI VERITA' UNICA durante il drag = timer del grip (33 ms):
// applica la scala solo come PREVIEW sul contenuto (editor->setPreviewScale,
// transform affine — la finestra host resta ferma, nessuna resizeView a
// 30 Hz). Il param viene aggiornato a ogni tick (beginChangeGesture +
// endChangeGesture = 1 azione host per l'intero drag). A mouseUp: release
// della preview (clearPreviewScale) + commit del param + UNA sola setSize
// sull'editor (wi,hi finali); se l'host la rifiuta, il contenuto scala comunque
// via baseScale = fit della finestra (18: canvas fisso, letterbox centrato).
// Il constrainer dell'editor resta PERMISSIVO [500,75,2000,300] per sempre
// (mai min=max: Reaper lo usa in checkSizeConstraint per clampare -> flip-flop
// a 30 Hz). Nessun setSize durante il drag: contenuto solo via transform.
class ResizeGrip : public juce::Component,
                   private juce::Timer
{
public:
    ResizeGrip (juce::RangedAudioParameter& uiScaleParam);

    void paint (juce::Graphics& g) override;

    bool isBeingDragged() const noexcept { return dragging; }

private:
    void timerCallback() override;

    void mouseDown (const juce::MouseEvent& e) override;
    void mouseDrag (const juce::MouseEvent& e) override;
    void mouseUp   (const juce::MouseEvent& e) override;
    void mouseEnter (const juce::MouseEvent&) override;
    void mouseExit  (const juce::MouseEvent&) override;

    void commitParam (float s);          // notifica host (param continuo, nessuna quantizzazione)

    juce::RangedAudioParameter& scaleParam;
    float startS = 1.0f;
    float pendingS = 1.0f;
    juce::Point<float> startPos { 0.0f, 0.0f };
    bool dragging = false;

    static constexpr int kTimerMs = 33;  // ~30 fps

    JUCE_DECLARE_NON_COPYABLE (ResizeGrip)
};
