#include "RenderedAsset.h"

#if DDX777_HAS_RENDERED_ASSETS
 // Esiste solo quando il target CMake DDX777_Assets e' linkato
 // (CMakeLists.txt: glob su assets/rendered/*.png).
 #include <BinaryData.h>
#endif

bool RenderedAsset::tryLoad (const juce::String& name)
{
   #if DDX777_HAS_RENDERED_ASSETS
    int dataSize = 0;

    // Il nome mangled generato da JUCE per un PNG e' "<nome>_png" e
    // getNamedResource() fa uno switch su hash: prova prima il suffisso
    // "_png" (matcha sempre), poi il nome grezzo per robustezza futura
    // (eventuali asset non-PNG).
    const void* data = BinaryData::getNamedResource ((name + "_png").toRawUTF8(), dataSize);

    if (data == nullptr)
        data = BinaryData::getNamedResource (name.toRawUTF8(), dataSize);

    if (data)
    {
        img_ = juce::ImageFileFormat::loadFrom (data, dataSize);
        return img_.isValid();
    }
   #else
    juce::ignoreUnused (name);
   #endif

    img_ = {};
    return false;
}

void RenderedAsset::draw (juce::Graphics& g, juce::Rectangle<float> target, float alpha) const
{
    if (! isValid())
        return;

    g.setImageResamplingQuality (juce::Graphics::highResamplingQuality);
    g.setOpacity (alpha);
    g.drawImage (img_, target);
}
