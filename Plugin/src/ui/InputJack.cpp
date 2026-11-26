#include "InputJack.h"

#include <cmath>

// Il componente e' piazzato da PluginEditor::resized con origine in coordinate
// Layout (inX0, inputY0): i centri dei jack vanno espressi come offset locali.
namespace
{
constexpr float kOriginX = static_cast<float> (ddxui::Layout::inX0);
constexpr float kOriginY = static_cast<float> (ddxui::Layout::inputY0);

// Larghezza del bounds in coordinate di progetto (deve combaciare con
// PluginEditor::resized: 119x80). Serve per lo scale transform (14-bis F1).
constexpr float kProjectW = 119.0f;

// 14-ter F6: jack a 5 livelli (confronto con foto …825): dopo il primo PNG
// l'esagono a r*0.86 risultava sproporzionato rispetto al dado (scuro) della
// foto -> fallback concordato: sagoma r #0B0B0C | disco r*0.92 #4E4E4E |
// esagono r*0.75 #8F8F8F | disco r*0.42 #D6D6D6 | foro r*0.28 kJackHole.
// Vertici esagono a 30+60i gradi (come gli attuali facet radiali).
void drawJack (juce::Graphics& g, float cx, float cy, float r)
{
    auto ellipse = [&] (float rr)
    {
        return juce::Rectangle<float> (cx - rr, cy - rr, 2.0f * rr, 2.0f * rr);
    };

    // 1) sagoma/anello esterno
    g.setColour (juce::Colour (0xff0B0B0C));
    g.fillEllipse (ellipse (r));

    // 2) disco corpo
    g.setColour (juce::Colour (0xff4E4E4E));
    g.fillEllipse (ellipse (0.92f * r));

    // 3) esagono (faccette del dado)
    {
        juce::Path hex;
        for (int i = 0; i < 6; ++i)
        {
            const double a = (i * 60.0 + 30.0) * juce::MathConstants<double>::pi / 180.0;
            const float px = cx + 0.75f * r * (float) std::cos (a);
            const float py = cy + 0.75f * r * (float) std::sin (a);
            if (i == 0) hex.startNewSubPath (px, py);
            else        hex.lineTo (px, py);
        }
        hex.closeSubPath();
        g.setColour (juce::Colour (0xff8F8F8F));
        g.fillPath (hex);
        g.setColour (juce::Colours::black.withAlpha (110.0f));
        g.strokePath (hex, juce::PathStrokeType (1.0f));
    }

    // 4) disco frontale
    g.setColour (juce::Colour (0xffD6D6D6));
    g.fillEllipse (ellipse (0.42f * r));

    // 5) foro
    g.setColour (ddxui::kJackHole);
    g.fillEllipse (ellipse (0.28f * r));
}
} // namespace

void InputJack::paint (juce::Graphics& g)
{
    // 14-bis F1: scala da coordinate reali a coordinate di progetto.
    const float s = static_cast<float> (getWidth()) / kProjectW;
    g.addTransform (juce::AffineTransform::scale (s));

    const float sx = static_cast<float> (ddxui::Layout::jackCX) - kOriginX;
    const float sy = static_cast<float> (ddxui::Layout::jackCY) - kOriginY;

    // 15: asset renderizzato per stato (ASSET_BRIEF B.5): mono 26x26 sul
    // centro, stereo 62x30 (jack a ±16, r15) — se manca, fallback qui sotto.
    if (! dual_)
    {
        if (assetMono_.isValid())
        {
            assetMono_.draw (g, juce::Rectangle<float> (sx - 13.0f, sy - 13.0f, 26.0f, 26.0f));
            return;
        }
    }
    else if (assetStereo_.isValid())
    {
        assetStereo_.draw (g, juce::Rectangle<float> (sx - 31.0f, sy - 15.0f, 62.0f, 30.0f));
        return;
    }

    // Mono: jack singolo r13. Stereo: due jack r15 affiancati a jackCX+-16
    // (centri 41/73, gap 2 px — 14-B, item 3).
    if (! dual_)
    {
        drawJack (g, sx, sy, 13.0f);
    }
    else
    {
        drawJack (g, sx - 16.0f, sy, 15.0f);
        drawJack (g, sx + 16.0f, sy, 15.0f);
    }
}

juce::Rectangle<float> InputJack::labelArea() const
{
    using L = ddxui::Layout;
    return juce::Rectangle<float> (static_cast<float> (L::inputLabelX) - kOriginX,
                                   static_cast<float> (L::inputLabelY) - kOriginY,
                                   static_cast<float> (L::inputLabelW),
                                   static_cast<float> (L::inputLabelH));
}

void InputJack::mouseDown (const juce::MouseEvent& e)
{
    // Solo il titolo INPUT e' cliccabile (14-B, item 11).
    // 14-bis F1: e.position e' in pixel reali, labelArea in coordinate di
    // progetto -> si riporta il punto nelle coordinate di progetto.
    const float s = static_cast<float> (getWidth()) / kProjectW;
    if (! labelArea().contains (e.position / s))
        return;

    stereoParam_.setValueNotifyingHost (1.0f - stereoParam_.get());
}

void InputJack::mouseMove (const juce::MouseEvent& e)
{
    updateCursor (e.position);
}

void InputJack::mouseEnter (const juce::MouseEvent& e)
{
    updateCursor (e.position);
}

void InputJack::mouseExit (const juce::MouseEvent&)
{
    setMouseCursor (juce::MouseCursor::NormalCursor);
}

void InputJack::updateCursor (juce::Point<float> p)
{
    // Cursore a mano solo sopra il titolo INPUT (14-B, item 11).
    // 14-bis F1: p arriva in pixel reali -> coordinate di progetto.
    const float s = static_cast<float> (getWidth()) / kProjectW;
    setMouseCursor (labelArea().contains (p / s) ? juce::MouseCursor::PointingHandCursor
                                                 : juce::MouseCursor::NormalCursor);
}
