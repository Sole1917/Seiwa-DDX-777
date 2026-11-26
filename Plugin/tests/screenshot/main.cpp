// ddx_screenshot — renderizza la UI del plugin in un PNG (headless, nessun
// display/window necessario).
// uso: ddx_screenshot [output.png]
//
// JUCE 8 (Windows) usa un backend Direct2D per le immagini: in un processo
// console headless la prima creazione del device D2D può fallire in modo
// silenzioso (Graphics "inert", immagine trasparente). Si fa quindi un
// warm-up del device e si valida il read-back dei pixel con retry.

#include <juce_core/juce_core.h>
#include <juce_graphics/juce_graphics.h>
#include <juce_audio_processors/juce_audio_processors.h>

#include "PluginProcessor.h"

#include <cstdio>

juce::AudioProcessor* createPluginFilter();

// L'immagine è "renderizzata" se contiene pixel con RGB non neri (il solo
// fill di sfondo nero non conta). Assunzioni: formato ARGB 32 bit, little-endian
// (byte: R, G, B, A).
static bool imageHasContent (const juce::Image& img)
{
    juce::Image::BitmapData bd (img, juce::Image::BitmapData::readOnly);
    if (bd.data == nullptr || bd.width <= 0 || bd.lineStride <= 0)
        return false;

    const uint8_t* base = static_cast<const uint8_t*> (bd.data);
    for (int y = 0; y < bd.height; y += 5)
    {
        const uint8_t* row = base + (size_t) y * bd.lineStride;
        for (int x = 0; x < bd.width; x += 5)
        {
            const uint8_t* px = row + (size_t) x * 4;
            if (px[0] != 0 || px[1] != 0 || px[2] != 0)
                return true;
        }
    }

    return false;
}

static std::unique_ptr<juce::Image> renderEditor (juce::AudioProcessorEditor* editor, int w, int h)
{
    auto img = std::make_unique<juce::Image> (juce::Image::ARGB, w, h, true);
    {
        juce::Graphics g (*img);
        g.fillAll (juce::Colours::black);
        editor->paintEntireComponent (g, true);
    }

    return img;
}

int main (int argc, char* argv[])
{
    juce::ScopedJuceInitialiser_GUI juceInit;

    // Warm-up del backend D2D (dispositivo lazily creato alla prima immagine):
    // ripeti finché un fill non lascia pixel non neri (frame D2D avviato).
    for (int i = 0; i < 10; ++i)
    {
        juce::Image warm (juce::Image::ARGB, 64, 64, true);
        {
            juce::Graphics g (warm);
            g.fillAll (juce::Colour::fromRGBA (0, 40, 0, 255));
        }

        if (imageHasContent (warm))
            break;

        juce::Thread::sleep (80);
    }

    juce::AudioProcessor* proc = createPluginFilter();
    juce::AudioProcessorEditor* editor = (proc != nullptr) ? proc->createEditor() : nullptr;

    if (editor == nullptr)
    {
        std::fprintf (stderr, "errore: editor assente\n");
        delete proc;
        return 1;
    }

    const juce::String outPath = (argc > 1) ? juce::String (argv[1])
                                             : juce::String ("ddx777_ui.png");

    // Debug.GUI: con argomento "stereo" forza STEREO_MODE ON (dual jack + neon);
    // "poweroff" forza POWER OFF, "holdon" forza HOLD ON (crop degli stati
    // switch: default = POWER pressed + HOLD unpressed, poweroff+holdon =
    // POWER unpressed + HOLD pressed — 14h H4, check bordi/glint).
    juce::StringArray args;
    for (int i = 1; i < argc; ++i)
        args.add (juce::String::fromUTF8 (argv[i]));

    const bool stereo  = args.contains ("stereo");
    const bool poweroff = args.contains ("poweroff");
    const bool holdon   = args.contains ("holdon");
    if (auto* seiwa = dynamic_cast<SeiwaDDX777AudioProcessor*> (proc))
    {
        if (stereo)
            seiwa->getParams().getParameter ("STEREO_MODE")->setValueNotifyingHost (1.0f);
        if (poweroff)
            seiwa->getParams().getParameter ("POWER")->setValueNotifyingHost (0.0f);
        if (holdon)
            seiwa->getParams().getParameter ("HOLD")->setValueNotifyingHost (1.0f);
    }

    // L'editor si auto-dimensiona al layout di progetto nel costruttore
    // (PluginEditor::setSize + setResizeLimits).
    const int W = editor->getWidth();
    const int H = editor->getHeight();
    std::printf ("editor: %d x %d\n", W, H);

    // Lascia girare i timer JUCE (fade neon stereo ~300 ms + update LED) finche'
    // non convergono; in assenza di message loop i componenti non si aggiornano.
    juce::MessageManager::getInstance()->runDispatchLoopUntil (600);

    std::unique_ptr<juce::Image> img;
    for (int attempt = 0; attempt < 25; ++attempt)
    {
        img = renderEditor (editor, W, H);
        if (imageHasContent (*img))
        {
            std::printf ("render ok al tentativo %d\n", attempt + 1);
            break;
        }

        img.reset();
        juce::Thread::sleep (150);
    }

    if (! imageHasContent (*img))
    {
        std::fprintf (stderr, "errore: render vuoto dopo i tentativi\n");
        delete editor;
        delete proc;
        return 2;
    }

    juce::File file (outPath);
    file.getParentDirectory().createDirectory();
    // JUCE 8 su Windows: FileOutputStream posiziona a fine file (append).
    // Si cancella il file per scrivere un PNG unico e pulito.
    file.deleteFile();
    const bool ok = [&] ()
    {
        if (auto out = file.createOutputStream())
            return juce::PNGImageFormat().writeImageToStream (*img, *out);
        return false;
    } ();

    delete editor;
    delete proc;

    if (ok)
        std::printf ("PNG: %s\n", outPath.toRawUTF8());
    else
        std::fprintf (stderr, "errore: scrittura PNG\n");

    return ok ? 0 : 1;
}
