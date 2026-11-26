#include "RackPanel.h"

#include <cmath>

namespace ddxui
{

float trackedWidth (const juce::Font& font, const juce::String& text, float tracking)
{
    float w = 0.0f;

    for (int i = 0; i < text.length(); ++i)
        w += juce::TextLayout::getStringWidth (font, juce::String::charToString (text[i])) + tracking;

    return w - tracking;
}

void drawTrackedCentred (juce::Graphics& g, const juce::Font& font, const juce::String& text,
                         const juce::Rectangle<float>& area, float tracking, const juce::Colour& colour)
{
    if (text.isEmpty())
        return;

    g.setFont (font);
    g.setColour (colour);

    const float total = trackedWidth (font, text, tracking);
    float x = area.getX() + (area.getWidth() - total) * 0.5f;
    const float boxY = area.getY() + (area.getHeight() - font.getHeight()) * 0.5f;

    for (int i = 0; i < text.length(); ++i)
    {
        const auto s = juce::String::charToString (text[i]);
        const float charW = juce::TextLayout::getStringWidth (font, s);
        g.drawText (s, juce::Rectangle<float> (x, boxY, charW + 1.0f, font.getHeight()),
                    juce::Justification::centredLeft);
        x += charW + tracking;
    }
}

// 14-f F3: variante right-aligned (reintrodotto da 14d): l'ink di destra
// finisce sul bordo destro dell'area (usato per DELAY TIME a dtTitleX1-7).
void drawTrackedRight (juce::Graphics& g, const juce::Font& font, const juce::String& text,
                       const juce::Rectangle<float>& area, float tracking, const juce::Colour& colour)
{
    if (text.isEmpty())
        return;

    g.setFont (font);
    g.setColour (colour);

    const float total = trackedWidth (font, text, tracking);
    float x = area.getRight() - total;
    const float boxY = area.getY() + (area.getHeight() - font.getHeight()) * 0.5f;

    for (int i = 0; i < text.length(); ++i)
    {
        const auto s = juce::String::charToString (text[i]);
        const float charW = juce::TextLayout::getStringWidth (font, s);
        g.drawText (s, juce::Rectangle<float> (x, boxY, charW + 1.0f, font.getHeight()),
                    juce::Justification::centredLeft);
        x += charW + tracking;
    }
}

} // namespace ddxui

RackPanel::RackPanel()
{
    setInterceptsMouseClicks (false, false);
    // 15: caricamento asset renderizzato opzionale (docs/ASSET_BRIEF.md B.5).
    // Con assets/rendered/ vuota entrambi restano invalidi e paint() disegna
    // il pannello procedurale invariato (byte-identico a 14-k).
    hasAsset_ = assetPanel_.tryLoad ("panel_base");
    assetPanelStereo_.tryLoad ("panel_base_stereo");
}

namespace
{

using ddxui::drawTrackedCentred;
using ddxui::drawTrackedRight;
using ddxui::Layout;

void drawFrame (juce::Graphics& g, int x0, int x1)
{
    // 14-quater F3: la cornice e' spezzata alle 5 giunzioni (gap 2*chamfer
    // = 18 px): i rail superiore/inferiore finiscono ai piedi delle diagonali
    // del bowtie, che NON hanno piu' la cornice come base per i triangoli
    // (verificato sul PNG: il segmento di rail tra i piedi chiudeva ∨/Λ).
    const float y0 = (float) Layout::frameTop;
    const float y1 = (float) Layout::frameBottom;
    const float c  = (float) Layout::chamfer;

    const int junctions[] = { Layout::fbX0, Layout::dlX0, Layout::dtX0,
                              Layout::hdX0, Layout::mdX0 };

    juce::Path p;

    // rail superiore: segmenti tra le giunzioni
    int prev = x0 + (int) c;
    for (int j : junctions)
    {
        p.startNewSubPath ((float) prev, y0);
        p.lineTo ((float) (j - (int) c), y0);
        prev = j + (int) c;
    }
    p.startNewSubPath ((float) prev, y0);
    p.lineTo ((float) (x1 - (int) c), y0);

    // rail inferiore: stessi gap
    prev = x0 + (int) c;
    for (int j : junctions)
    {
        p.startNewSubPath ((float) prev, y1);
        p.lineTo ((float) (j - (int) c), y1);
        prev = j + (int) c;
    }
    p.startNewSubPath ((float) prev, y1);
    p.lineTo ((float) (x1 - (int) c), y1);

    // lati verticali + chamfer angoli esterni (l'unica parte continua)
    p.startNewSubPath ((float) x0 + c, y0);
    p.lineTo ((float) x0, y0 + c);
    p.lineTo ((float) x0, y1 - c);
    p.lineTo ((float) x0 + c, y1);
    p.startNewSubPath ((float) x1 - c, y0);
    p.lineTo ((float) x1, y0 + c);
    p.lineTo ((float) x1, y1 - c);
    p.lineTo ((float) x1 - c, y1);

    g.setColour (ddxui::kSilk.withAlpha (235.0f));
    g.strokePath (p, juce::PathStrokeType (1.6f));
}

juce::Font titleFont()  { return juce::Font (juce::FontOptions ("Arial", 13.0f, juce::Font::bold)); }
juce::Font labelFont()  { return juce::Font (juce::FontOptions ("Arial", 12.5f, juce::Font::bold)); }
juce::Font smallFont()  { return juce::Font (juce::FontOptions ("Arial", 10.0f, juce::Font::bold)); }

void sectionLabel (juce::Graphics& g, const juce::String& text, int x0, int x1, bool top,
                   const juce::Colour& colour = ddxui::kSilk, float tracking = 2.0f)
{
    const float y = top ? (float) Layout::titleY : (float) Layout::bottomLabelY;
    drawTrackedCentred (g, top ? titleFont() : labelFont(), text,
                        juce::Rectangle<float> ((float) x0 + 4.0f, y,
                                                (float) (x1 - x0) - 8.0f, 14.0f),
                        tracking, colour);
}

// Etichetta centrata su una coordinata x (centro dei potenziometri).
void knobLabel (juce::Graphics& g, const juce::String& text, int cx)
{
    drawTrackedCentred (g, labelFont(), text,
                        juce::Rectangle<float> ((float) cx - 61.0f, (float) Layout::bottomLabelY,
                                                121.0f, 14.0f),
                        2.0f, ddxui::kSilk);
}

// Zona "STEREO" neon: usata da paint e da ensureNeon, che genera le immagini
// grande esattamente label + 2*border per un blit 1:1 (nessuno stretch).
// 14-e R5: kNeonX 835->816 (blocco logo centrato a cx881); kNeonY 110
// (target gap righe 10/10/10 con Seiwa 34pt ~40..69, DD y75 ~80..86,
// DDX y91 ~97..103, STEREO ~114..121).
constexpr float kNeonBorder = 8.0f;
constexpr float kNeonX = 816.0f, kNeonY = 110.0f, kNeonW = 130.0f, kNeonH = 16.0f;

} // namespace

void RackPanel::paint (juce::Graphics& g)
{
    // 14-bis F1: il componente copre l'intero editor (kW*s x kH*s); si disegna
    // tutto in coordinate di progetto 1000x150 scalando il contesto.
    const float s = static_cast<float> (getLocalBounds().getWidth())
                    / static_cast<float> (Layout::kW);
    g.addTransform (juce::AffineTransform::scale (s));

    const auto area = juce::Rectangle<float> (0.0f, 0.0f,
                                              static_cast<float> (Layout::kW),
                                              static_cast<float> (Layout::kH));

    // 15: se l'asset esiste, pannello statico (gradiente + cornice + bowtie +
    // titoli/label + logo) viene da panel_base[_stereo] (ASSET_BRIEF B.5);
    // altrimenti fallback procedurale identico a 14-k.
    const bool useStereoAsset = hasAsset_ && stereoOn_ && assetPanelStereo_.isValid();

    if (hasAsset_)
    {
        (useStereoAsset ? assetPanelStereo_ : assetPanel_).draw (g, area);
    }
    else
    {
        g.setFillType (juce::FillType (juce::ColourGradient (ddxui::kPanelTop, 0.0f, 0.0f,
                                                             ddxui::kPanelBottom, 0.0f, area.getHeight(),
                                                             false)));
        g.fillAll();
    }

    // titoli sezione (alto) — INPUT rosso quando STEREO (14-B).
    // 15: resta SEMPRE procedurale: cambia colore a runtime (ASSET_BRIEF B.5).
    sectionLabel (g, "INPUT", Layout::inputTitleX0, Layout::inputTitleX1, true,
                  stereoOn_ ? juce::Colour (0xffB4281E) : ddxui::kSilk);

    if (! hasAsset_)
    {
    // 14-ter: "FEED BACK" (92 px a tr2) non sta nella sezione di 90 px:
    // tracking 1.0 -> 84 px, 238..322 dentro 235..325 (divisorie a 1.6 px).
    sectionLabel (g, "FEED BACK", Layout::fbX0, Layout::fbX1, true,
                  ddxui::kSilk, 1.0f);
    sectionLabel (g, "DELAY", Layout::dlX0, Layout::dlX1, true);
    // 14-g G2: DELAY TIME centrata sull'asse del pot FACTOR (factorX 536),
    // tracking 1.0 (era 2.0): drawTrackedRight con area destra =
    // factorX + inkWidth/2 → centro dell'ink esattamente su factorX.
    // Check: destra ~572 ≤ dtX1-7 = 581; sinistra ~499, "32" RANGE a
    // 452..478 → 21px di gap.
    const float dtTrk = 1.0f;
    const float dtInkW = ddxui::trackedWidth (titleFont(), "DELAY TIME", dtTrk);
    drawTrackedRight (g, titleFont(), "DELAY TIME",
                      juce::Rectangle<float> ((float) Layout::dtTitleX0, (float) Layout::titleY,
                                              (float) Layout::factorX + dtInkW * 0.5f
                                                  - (float) Layout::dtTitleX0,
                                              14.0f),
                      dtTrk, ddxui::kSilk);
    sectionLabel (g, "MODULATION", Layout::mdX0, Layout::mdX1, true);

    // etichette bassi
    drawTrackedCentred (g, smallFont(), "-20dB",
                        juce::Rectangle<float> ((float) Layout::jackCX - 33.0f,
                                                (float) Layout::bottomLabelY, 66.0f, 14.0f),
                        0.8f, ddxui::kSilk);
    knobLabel (g, "LEVEL", Layout::peakX);
    knobLabel (g, "LEVEL", Layout::fbX);
    knobLabel (g, "LEVEL", Layout::dlX);
    knobLabel (g, "RANGE mS", Layout::rangeX);
    knobLabel (g, "FACTOR", Layout::factorX);
    knobLabel (g, "HOLD", Layout::holdSwX);
    knobLabel (g, "SPEED", Layout::speedX);
    knobLabel (g, "DEPTH", Layout::depthX);
    // 17-fix3 2b: POWER non e' centrato sull'asse del rocker come gli altri
    // knobLabel: Arial Bold 11pt, tracking 2.0, ink di destra a x=994 e
    // stessa y di DDX-777 (rect y91 h20 -> centro 101).  995 = 994 + ~1 px
    // di right side bearing dell'R finale: drawTrackedRight allinea il bordo
    // destro dell'ADVANCE, non dell'ink.
    drawTrackedRight (g,
                      juce::Font (juce::FontOptions ("Arial", 11.0f, juce::Font::bold)),
                      "POWER",
                      juce::Rectangle<float> (900.0f, 91.0f, 95.0f, 20.0f),
                      2.0f, ddxui::kSilk);

    // PEAK (alto a destra della sezione INPUT; LED e' un componente a sX).
    // 14-C: ricentrato sull'asse peakX (centro 150, era 156.5) e a y23.
    drawTrackedCentred (g, titleFont(), "PEAK",
                        juce::Rectangle<float> ((float) Layout::peakX - 27.5f,
                                                (float) Layout::titleY, 55.0f, 14.0f),
                        2.0f, ddxui::kSilk);

    // logo Seiwa (cream) + DIGITAL DELAY / DDX-777 (serigrafia), zona a destra
    // della sezione MODULATION (nessuna cornice, come nel pannello originale).
    // 14-e R5: blocco (4 righe, incl. neon STEREO) centrato a
    // logoCX = (mdX1 812 + bordo sx POWER 950)/2 = 881 (era 900, troppo
    // attaccato a POWER).
    const float logoCX = 881.0f;
    const juce::Font logoFont (juce::FontOptions ("Georgia", 34.0f, juce::Font::bold | juce::Font::italic));
    g.setColour (ddxui::kLogoCream);
    g.setFont (logoFont);
    const juce::String seiwa = "Seiwa";
    const float logoW = juce::TextLayout::getStringWidth (logoFont, seiwa);
    const float logoX = logoCX - logoW * 0.5f;
    g.drawText (seiwa, juce::Rectangle<float> (logoX, 36.0f, logoW, 46.0f),
                juce::Justification::centredLeft);
    g.setFont (juce::Font (juce::FontOptions ("Arial", 10.0f, juce::Font::bold)));
    g.setColour (ddxui::kLogoCream);
    g.drawText (juce::String::fromUTF8 ("\xc2\xae"),
                juce::Rectangle<float> (logoX + logoW + 2.0f, 38.0f, 12.0f, 12.0f),
                juce::Justification::centredLeft);

    // 14-e R5: trio Arial 11 bold tr2.0, cx881 (rect x826 w110),
    // gap righe 10/10/10: DD y75, DDX y91, STEREO kNeonY110.
    drawTrackedCentred (g, juce::Font (juce::FontOptions ("Arial", 11.0f, juce::Font::bold)), "DIGITAL DELAY",
                        juce::Rectangle<float> (826.0f, 75.0f, 110.0f, 18.0f), 2.0f, ddxui::kSilk);
    drawTrackedCentred (g, juce::Font (juce::FontOptions ("Arial", 11.0f, juce::Font::bold)),
                        juce::String::fromUTF8 ("DDX\xe2\x80\x93" "777"),
                        juce::Rectangle<float> (826.0f, 91.0f, 110.0f, 20.0f), 2.0f, ddxui::kSilk);
    } // if (! hasAsset_) — fine serigrafia statica (15)

    // Scritta "STEREO" con neon rosso, sotto DDX-777 (on/off istantaneo).
    // 15: saltata solo se la variante stereo renderizzata contiene gia' il
    // neon (ASSET_BRIEF D10); altrimenti resta procedurale.
    if (stereoOn_ && ! useStereoAsset)
    {
        ensureNeon();
        g.setOpacity (0.35f); // layer glow (dietro, blur ~8 px)
        g.drawImageAt (neonGlow_, kNeonX - kNeonBorder, kNeonY - kNeonBorder);
        g.setOpacity (1.0f);   // layer sharp #B4281E (davanti)
        g.drawImageAt (neonSharp_, kNeonX - kNeonBorder, kNeonY - kNeonBorder);
        g.setOpacity (1.0f);
    }

    // 14-quater F1: la gerarchia di disegno obbligatoria e' asset -> label ->
    // bounds serigrafici: cornice e divisorie bowtie vengono DPOI di tutta
    // la serigrafia (bounds = topmost, come nel pannello originale).
    // 14-quater F3: la cornice e' spezzata alle 5 giunzioni (gap 2*chamfer)
    // per non far da base ai triangoli ∨/Λ del bowtie.
    // 15: cornice+bowtie gia' dentro panel_base -> salti se c'e' l'asset.
    if (! hasAsset_)
    {
        drawFrame (g, Layout::inX0, Layout::mdX1);
        g.setColour (ddxui::kSilk.withAlpha (235.0f));
        {
            const float ft = (float) Layout::frameTop,  fb = (float) Layout::frameBottom;
            const float c  = (float) Layout::chamfer;
            for (int x : { Layout::fbX0, Layout::dlX0, Layout::dtX0, Layout::hdX0, Layout::mdX0 })
            {
                const float jx = (float) x;
                juce::Path v;
                v.startNewSubPath (jx - c, ft);
                v.lineTo (jx, ft + c);
                v.lineTo (jx, fb - c);
                v.lineTo (jx - c, fb);
                v.startNewSubPath (jx + c, ft);
                v.lineTo (jx, ft + c);
                v.startNewSubPath (jx + c, fb);
                v.lineTo (jx, fb - c);
                g.strokePath (v, juce::PathStrokeType (1.6f));
            }
        }
    }
}

void RackPanel::setStereoOn (bool on)
{
    if (stereoOn_ == on)
        return;

    stereoOn_ = on;
    repaint(); // INPUT rosso + neon aggiornati senza fade (14-B)
}

void RackPanel::ensureNeon()
{
    if (neonGlow_.isValid())
        return;

    const juce::Font font (juce::FontOptions ("Arial", 11.0f, juce::Font::bold));

    // Immagine grande esattamente quanto la zona di disegno (label + bordo):
    // il blit e' 1:1, niente stretch del testo (era image ~63x25 in un rect
    // 146x32 -> testo allargato ~2.3x in orizzontale).
    const int w = static_cast<int> (kNeonW + 2.0f * kNeonBorder);
    const int h = static_cast<int> (kNeonH + 2.0f * kNeonBorder);
    const juce::Rectangle<float> textArea (kNeonBorder, kNeonBorder, kNeonW, kNeonH);

    // Layer sharp: testo saturo #B4281E
    neonSharp_ = juce::Image (juce::Image::ARGB, w, h, true);
    {
        juce::Graphics sg (neonSharp_);
        ddxui::drawTrackedCentred (sg, font, "STEREO", textArea, 2.0f, juce::Colour (0xffB4281E));
    }

    // Layer glow: stesso testo piu' chiaro, poi blur gaussiano ~8 px
    juce::Image glowSrc (juce::Image::ARGB, w, h, true);
    {
        juce::Graphics gg (glowSrc);
        ddxui::drawTrackedCentred (gg, font, "STEREO", textArea, 2.0f, juce::Colour (0xffE8553F));
    }
    neonGlow_ = glowSrc.createCopy();
    juce::ImageConvolutionKernel kernel (9);
    kernel.createGaussianBlur (8.0f);
    kernel.applyToImage (neonGlow_, glowSrc, neonGlow_.getBounds());
}
