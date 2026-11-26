#include "Knob.h"

#include <cmath>

Knob::Knob (juce::RangedAudioParameter& param, const juce::Colour& cap, Style s)
    : parameter (param), capColour (cap), style (s)
{
    parameter.addListener (this);

    // 15: mappatura capColour -> filmstrip (ASSET_BRIEF B.5): PEAK/SPEED
    // arancio, FEEDBACK/FACTOR verde, DELAY/DEPTH giallo, RANGE blu.
    // Asset non incorporato (assets/rendered/ vuota) -> tryLoad no-op.
    juce::String filmstrip;
    if      (capColour == ddxui::kCapOrange) filmstrip = "knob_orange_filmstrip";
    else if (capColour == ddxui::kCapGreen)  filmstrip = "knob_green_filmstrip";
    else if (capColour == ddxui::kCapYellow) filmstrip = "knob_yellow_filmstrip";
    else if (capColour == ddxui::kCapBlue)   filmstrip = "knob_blue_filmstrip";

    if (filmstrip.isNotEmpty())
        asset_.tryLoad (filmstrip);
}

Knob::~Knob()
{
    parameter.removeListener (this);
}

float Knob::value01() const
{
    if (style == Style::Factor)
    {
        // getValue() e' normalizzato 0..1: va convertito in raw 0.5..2.0
        const float v = parameter.convertFrom0to1 (parameter.getValue());
        return juce::jlimit(0.0f, 1.0f, std::log2(v / 0.5f) / 2.0f);
    }
    return parameter.getValue();
}

int Knob::numSteps() const
{
    const auto& range = parameter.getNormalisableRange();

    // Scalette intere 0..N (N<=10) -> N+1 posizioni; tutto il resto (0..1,
    // 0.5..2, dB) e' continuo.
    if (range.interval <= 0.0f || range.start != 0.0f
        || range.end < 1.0f || range.end > 10.0f)
        return 1000;

    return static_cast<int> (std::lround (range.end)) + 1;
}

void Knob::setValue01 (float v)
{
    if (style == Style::Factor)
    {
        // Inverso di value01(): spazio log -> raw -> normalizzato
        v = juce::jlimit(0.0f, 1.0f, v);
        const float raw = 0.5f * std::exp2(2.0f * v);
        parameter.setValueNotifyingHost (parameter.convertTo0to1 (raw));
        return;
    }
    parameter.setValueNotifyingHost (v);
}

void Knob::mouseDown (const juce::MouseEvent& e)
{
    if (e.getNumberOfClicks() > 1)
    {
        // getDefaultValue() e' normalizzato: setValueNotifyingHost diretto
        // (setValue01 per lo stile Factor si aspetta lo spazio log)
        parameter.setValueNotifyingHost (parameter.getDefaultValue());
        return;
    }

    dragging = true;
    dragStartY = static_cast<float> (e.y);
    dragStartValue = value01();
}

void Knob::mouseDrag (const juce::MouseEvent& e)
{
    if (! dragging)
        return;

    const float delta = (dragStartY - e.y) * (4.0f / static_cast<float> (getHeight()));
    float v = dragStartValue + delta;
    const int steps = numSteps();

    if (steps < 1000)
    {
        const int idx = juce::jlimit (0, steps, static_cast<int> (std::lround (v * steps)));
        v = static_cast<float> (idx) / static_cast<float> (steps);
    }
    else
    {
        v = juce::jlimit (0.0f, 1.0f, v);
    }

    if (v != value01())
        setValue01 (v);
}

void Knob::mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails& details)
{
    const float dir = details.deltaY > 0.0f ? 1.0f : (details.deltaY < 0.0f ? -1.0f : 0.0f);

    if (dir == 0.0f)
        return;

    const int steps = numSteps();
    // 14-quater F8: wheel sui pot fluidi 0.05 -> 0.0125 (1 tacca = 8 click,
    // x4); le posizioni discrete (numSteps < 1000) restano a 1 step/tacca.
    float v = value01() + dir * (steps < 1000 ? 1.0f / static_cast<float> (steps) : 0.0125f);
    v = juce::jlimit (0.0f, 1.0f, v);

    if (steps < 1000)
    {
        const int idx = juce::jlimit (0, steps, static_cast<int> (std::lround (v * steps)));
        v = static_cast<float> (idx) / static_cast<float> (steps);
    }

    if (v != value01())
        setValue01 (v);
}

namespace
{

juce::Point<float> polar (float ox, float oy, double angleDeg, double r)
{
    const double a = angleDeg * juce::MathConstants<double>::pi / 180.0;
    return juce::Point<float> (static_cast<float> (ox + r * std::cos (a)),
                               static_cast<float> (oy + r * std::sin (a)));
}

} // namespace

void Knob::paint (juce::Graphics& g)
{
    // 14-bis F1: il componente ha bounds 96x96 * scala; si disegna tutto in
    // coordinate di progetto (96x96, centro 48/48) e si scala il contesto.
    const float s = static_cast<float> (getWidth()) / 96.0f;
    g.addTransform (juce::AffineTransform::scale (s));

    const float ox = 48.0f;
    const float oy = 48.0f;

    const juce::Colour silk = ddxui::kSilk;

    // ---- serigrafia della scala (box 96x96: tacche r27..34, etichette r41;
    //      14-C item 6: etichette 38->41; 14-ter F4: Range 37->41;
    //      14-bis F7: interno tacche 30->27, lunghezza 4->7) ----
    g.setColour (silk);

    if (style == Style::Factor)
    {
        // 11 tacche su 270 gradi (135 -> 405), identico a SPEED/DEPTH
        for (int i = 0; i < 11; ++i)
        {
            const double a = 135.0 + i * 27.0;
            g.drawLine (polar (ox, oy, a, 27.0).x, polar (ox, oy, a, 27.0).y,
                        polar (ox, oy, a, 34.0).x, polar (ox, oy, a, 34.0).y, 1.8f);
        }
    }
    else if (style == Style::Range)
    {
        // 10 tacche sui detent (135 -> 405, passi di 270/9), come il pannello
        for (int i = 0; i < 10; ++i)
        {
            const double a = 135.0 + i * (270.0 / 9.0);
            g.drawLine (polar (ox, oy, a, 27.0).x, polar (ox, oy, a, 27.0).y,
                        polar (ox, oy, a, 34.0).x, polar (ox, oy, a, 34.0).y, 1.8f);
        }
    }
    else
    {
        // 11 tacche su 270 gradi (135 -> 405)
        for (int i = 0; i < 11; ++i)
        {
            const double a = 135.0 + i * 27.0;
            g.drawLine (polar (ox, oy, a, 27.0).x, polar (ox, oy, a, 27.0).y,
                        polar (ox, oy, a, 34.0).x, polar (ox, oy, a, 34.0).y, 1.8f);
        }
    }

    auto drawLabel = [&g, ox, oy, silk] (double angleDeg, const juce::String& text,
                                         double r, float h)
    {
        const auto p = polar (ox, oy, angleDeg, r);
        g.setFont (juce::Font (juce::FontOptions ("Arial", h, juce::Font::bold)));
        g.setColour (silk);
        g.drawText (text, juce::Rectangle<float> (p.x - h * 1.8f, p.y - h * 0.55f,
                                                  h * 3.6f, h * 1.4f),
                    juce::Justification::centred);
    };

    if (style == Style::Level010)
    {
        drawLabel (135.0, "0", 41.0, 10.0f);
        drawLabel (45.0, "10", 41.0, 10.0f);
    }
    else if (style == Style::Level0to20)
    {
        drawLabel (135.0, "0", 41.0, 10.0f);
        drawLabel (45.0, "+20", 41.0, 10.0f);
    }
    else if (style == Style::Factor)
    {
        // FACTOR: etichette ×0.5 (sinistra/135°), ×2 (destra/405°=45°) — NO ×1 at centre
        drawLabel (135.0, juce::String::fromUTF8 ("\xc3\x97" "0.5"), 41.0, 10.0f);
        drawLabel (45.0, juce::String::fromUTF8 ("\xc3\x97" "2"), 41.0, 10.0f);
    }
    else if (style == Style::Range)
    {
        // 10 detent serigrafati, passo 270/9 (foto 830/836).
        // 14-e R4/R5: corona r41 = stessa distanza label-tacca del FACTOR
        // (tacche identiche r27..34 -> offset identico); a r45 (14d) "512"
        // toccava "RANGE mS", a r41 il gap e' ~2.4 px (stato 14c/14-ter).
        const char* vals[] = { "1", "2", "4", "8", "16", "32", "64", "128", "256", "512" };

        for (int i = 0; i < 10; ++i)
            drawLabel (135.0 + i * (270.0 / 9.0), vals[i], 41.0, 9.0f);
    }
    
    // ---- corpo del potenziometro (mozzo r27, cappuccio r22.5) ----
    // 15: se il filmstrip esiste, il corpo (mozzo+cappuccio+indice, sfondo
    // trasparente) viene da lì: tile 192x192 (2x del box 96x96) centrata sul
    // componente, frame = round(value01 * (frames-1)) (ASSET_BRIEF B.5/C.3).
    // La corona sopra resta procedurale. Se assente, fallback qui sotto.
    if (asset_.isValid())
    {
        const int tileW = 192;
        const int frames = juce::jmax (1, asset_.image().getWidth() / tileW);
        const int frame = juce::jlimit (0, frames - 1,
                                        juce::roundToInt (value01() * (float) (frames - 1)));

        g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
        g.drawImage (asset_.image(),
                     0, 0, 96, 96,                 // dest (coordinate progetto)
                     frame * tileW, 0, tileW, tileW, // sorgente: tile del filmstrip
                     false);
        return;
    }

    g.setColour (ddxui::kShaft);
    g.fillEllipse (juce::Rectangle<float> (ox - 27.0f, oy - 27.0f, 54.0f, 54.0f));
    g.setColour (juce::Colours::black.withAlpha (120.0f));
    g.drawEllipse (juce::Rectangle<float> (ox - 27.0f, oy - 27.0f, 54.0f, 54.0f), 1.0f);

    g.setColour (capColour);
    g.fillEllipse (juce::Rectangle<float> (ox - 22.5f, oy - 22.5f, 45.0f, 45.0f));
    g.setColour (juce::Colours::black.withAlpha (90.0f));
    g.drawEllipse (juce::Rectangle<float> (ox - 22.5f, oy - 22.5f, 45.0f, 45.0f), 1.0f);

    // indice triangolare classico: PUNTA VERSO L'ESTERNO (apice r21),
    // base verso il centro (r11) — come il pannello originale.
    // NB: polar() vuole GRADI (fa la conversione interna).
    const double aDeg = 135.0 + 270.0 * value01();
    const double halfWidthDeg = 20.0;

    juce::Path tri;
    tri.startNewSubPath (polar (ox, oy, aDeg, 21.0));
    tri.lineTo (polar (ox, oy, aDeg - halfWidthDeg, 11.0));
    tri.lineTo (polar (ox, oy, aDeg + halfWidthDeg, 11.0));
    tri.closeSubPath();

    g.setColour (ddxui::kIndex);
    g.fillPath (tri);
}
