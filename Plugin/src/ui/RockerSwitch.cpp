#include "RockerSwitch.h"

RockerSwitch::RockerSwitch (juce::RangedAudioParameter& param, float projectW, float projectH,
                            const juce::String& assetBase)
    : parameter (param), projectW_ (projectW), projectH_ (projectH)
{
    parameter.addListener (this);
    // 14-h H1: niente setPaintingIsUnclipped — il paint non esce mai dai
    // bounds (corpo reduced(1), glint e bordo interni): clipping di default.

    // 15: asset per stato (ASSET_BRIEF B.5); se uno manca, quello stato
    // usa il fallback procedurale.
    if (assetBase.isNotEmpty())
    {
        assetOn_.tryLoad (assetBase + "_on");
        assetOff_.tryLoad (assetBase + "_off");
    }
}

RockerSwitch::~RockerSwitch()
{
    parameter.removeListener (this);
}

void RockerSwitch::paint (juce::Graphics& g)
{
    // Scala da coordinate reali a coordinate di progetto.
    const float s = static_cast<float> (getWidth()) / projectW_;
    g.addTransform (juce::AffineTransform::scale (s));

    const bool on = isOn();

    // 15: asset renderizzato (corpo+glint+bordo, intero bounds) — se il
    // renderer dello stato non esiste, fallback procedurale sotto (B.5).
    {
        const auto& asset = on ? assetOn_ : assetOff_;
        if (asset.isValid())
        {
            asset.draw (g, juce::Rectangle<float> (0.0f, 0.0f, projectW_, projectH_));
            return;
        }
    }

    // 14-h H1: NESSUNA traslazione +2y in pressed (affondava il bordo
    // inferiore nel clip del bounds). Tutto il paint sta entro reduced(1).
    const auto b = juce::Rectangle<float> (0.0f, 0.0f, projectW_, projectH_).reduced (1.0f);

    // --- corpo pieno: off kRockerLo #101113 / on kRockerHi #3A3D44 ---
    g.setColour (on ? ddxui::kRockerHi : ddxui::kRockerLo);
    g.fillRoundedRectangle (b, 3.5f);

    // --- glint superiore: SOLO stato unpressed (OFF) ---
    // Righe sottili calde a boundsTop+1; al press sparisce = senso di
    // rientranza senza muovere nulla. (Mai piu' blocco interno di 28%.)
    if (! on)
    {
        g.setColour (juce::Colour (0xffFFF0D8).withAlpha (28.0f / 255.0f));
        g.fillRoundedRectangle (juce::Rectangle<float> (b.getX() + 2.0f, b.getY() + 1.0f,
                                                         b.getWidth() - 4.0f, 1.5f),
                                1.0f);
    }

    // --- bordo grigio #808080 1.2px, integro su tutti i 4 lati ---
    g.setColour (juce::Colour (0xff808080));
    g.drawRoundedRectangle (b, 3.5f, 1.2f);
}
