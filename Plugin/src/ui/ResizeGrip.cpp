#include "ResizeGrip.h"

#include "PluginEditor.h"

ResizeGrip::ResizeGrip (juce::RangedAudioParameter& uiScaleParam)
    : scaleParam (uiScaleParam)
{
    setMouseCursor (juce::MouseCursor::BottomRightCornerResizeCursor);
}

void ResizeGrip::paint (juce::Graphics& g)
{
    const float s = static_cast<float> (getWidth()) / 20.0f;
    g.addTransform (juce::AffineTransform::scale (s));

    // triangolo "__/" incassato nell'angolo (leggermente inset per non
    // uscire dai bounds a scala estrema)
    const float w = 20.0f;
    juce::Path p;
    p.startNewSubPath (w - 16.0f, w - 2.0f);
    p.lineTo (w - 2.0f,  w - 2.0f);
    p.lineTo (w - 2.0f,  w - 16.0f);
    p.closeSubPath();

    const bool hov = isMouseOver (true);
    g.setColour (ddxui::kSilk.withAlpha (hov ? 200.0f : 40.0f));
    g.fillPath (p);
    g.setColour (ddxui::kSilk.withAlpha (hov ? 230.0f : 70.0f));
    g.strokePath (p, juce::PathStrokeType (1.0f));
}

void ResizeGrip::timerCallback()
{
    // 14-i: preview scale sul contenuto (transform affine), mai setSize.
    if (auto* ed = findParentComponentOfClass<SeiwaDDX777AudioProcessorEditor>())
    {
        ed->setPreviewScale (pendingS);
        commitParam (pendingS);
    }
}

void ResizeGrip::mouseDown (const juce::MouseEvent& e)
{
    dragging = true;
    startS = juce::jlimit (0.5f, 2.0f, scaleParam.convertFrom0to1 (scaleParam.getValue()));
    pendingS = startS;
    startPos = e.position;
    // 14-h H3: apre il gesto sul param — per l'host l'intero drag e' UNA
    // sola azione continuativa (coalescing), non N eventi separati/s.
    scaleParam.beginChangeGesture();
}

void ResizeGrip::mouseDrag (const juce::MouseEvent& e)
{
    if (! dragging)
        return;

    // Solo aggiorna il target: nessun setSize, nessun param qui (14-f F5b).
    // Il timer a 33 ms li applica (fonte di verita' unica = questo timer).
    const float ds = ((e.position.x - startPos.x) + (e.position.y - startPos.y)) / 600.0f;
    pendingS = juce::jlimit (0.5f, 2.0f, startS + ds);

    if (! isTimerRunning())
        startTimer (kTimerMs);
}

void ResizeGrip::mouseUp (const juce::MouseEvent&)
{
    dragging = false;
    stopTimer();

    commitParam (pendingS);

    // 18: rilascio = rilascia la preview (baseScale riprende il controllo),
    // poi UNA sola richiesta setSize all'host col valore finale. Se l'host
    // accetta, la finestra si adatta; se rifiuta, il contenuto resta scalato
    // via baseScale (letterbox centrato). MAI setResizeLimits min=max e mai
    // setSize durante il drag (14-f F5b / 14-h H3: 1 azione host per drag).
    if (auto* ed = findParentComponentOfClass<SeiwaDDX777AudioProcessorEditor>())
    {
        ed->clearPreviewScale();
        ed->setSize (juce::roundToInt (ddxui::Layout::kW * pendingS),
                     juce::roundToInt (ddxui::Layout::kH * pendingS));
        ed->repaint();
    }

    // 14-h H3: chiude il gesto (host: fine azione unica).
    scaleParam.endChangeGesture();
}

void ResizeGrip::mouseEnter (const juce::MouseEvent&) { repaint(); }
void ResizeGrip::mouseExit  (const juce::MouseEvent&) { repaint(); }

void ResizeGrip::commitParam (float s)
{
    const float target = scaleParam.convertTo0to1 (juce::jlimit (0.5f, 2.0f, s));
    if (scaleParam.getValue() != target)
        scaleParam.setValueNotifyingHost (target); // 14-f F5a: param continuo
}
