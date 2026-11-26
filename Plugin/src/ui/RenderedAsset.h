#pragma once

#include <juce_gui_extra/juce_gui_extra.h>

// 15: wrapper degli asset renderizzati (docs/ASSET_BRIEF.md, contratto B.5).
// Ogni componente prova a caricare la propria risorsa BinaryData: se assente
// (build con assets/rendered/ vuota) o illeggibile, isValid() resta false e
// il componente disegna il fallback procedurale invariato (identico a 14-k).
class RenderedAsset
{
public:
    RenderedAsset() = default;

    // Carica la risorsa binaria chiamata "name" (filename SENZA estensione,
    // case-sensitive). Il lookup usa pero' il nome mangled di JUCE, quindi
    // il suffisso "_png" e' provato come suffisso PRIMARIO, con fallback sul
    // nome grezzo per asset non-PNG. Restituisce true se caricata. Con
    // DDX777_HAS_RENDERED_ASSETS=0 e' un no-op e restituisce false.
    bool tryLoad (const juce::String& name);

    bool isValid() const noexcept { return img_.isValid() && img_.getWidth() > 0; }

    // Stira l'immagine su "target" con resampling ad alta qualita'. No-op se
    // !isValid(). "alpha" viene applicato con setOpacity (1.0 = invariato).
    void draw (juce::Graphics& g, juce::Rectangle<float> target, float alpha = 1.0f) const;

    // Accesso grezzo (es. Knob: crop del tile del filmstrip).
    const juce::Image& image() const noexcept { return img_; }

private:
    juce::Image img_;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (RenderedAsset)
};
