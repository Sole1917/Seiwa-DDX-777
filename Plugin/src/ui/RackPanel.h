#pragma once

#include <juce_gui_extra/juce_gui_extra.h>

#include "RenderedAsset.h"

namespace ddxui
{

// Colori della serigrafia 13b (pannello nero, stampa cream/giallo chiaro).
inline const juce::Colour kPanelTop    (0xff222326);
inline const juce::Colour kPanelBottom (0xff141517);
inline const juce::Colour kSilk        (0xffEDE0B0);   // serigrafia cream
inline const juce::Colour kLogoCream   (0xffEDE0B0);   // logo "Seiwa"
inline const juce::Colour kShaft       (0xff0D0E10);
inline const juce::Colour kCapOrange   (0xffE87A1E);
inline const juce::Colour kCapGreen    (0xff2E9B5E);
inline const juce::Colour kCapYellow   (0xffE8D84A);
inline const juce::Colour kCapBlue     (0xff3A9BC7);
inline const juce::Colour kIndex       (0xffF5EEDC);
inline const juce::Colour kLedOff      (0xff3A0A05);
inline const juce::Colour kLedOn       (0xffFF4030);
inline const juce::Colour kRockerDark  (0xff08090A);
inline const juce::Colour kRockerEdge  (0xff2A2C31);
inline const juce::Colour kRockerLo    (0xff101113);
inline const juce::Colour kRockerHi    (0xff3A3D44);
inline const juce::Colour kJackHole    (0xff050506);

// Geometria di progetto 1000 x 150 (14-ter F1: refit foto-verificato su
// Foto DSP/…824 — canvas 1000, sezioni/assi da misure foto, campo destro
// 842..1000 per logo/POWER ridotti ~15%).
struct Layout
{
    static constexpr int kW = 1000, kH = 150;

    // 14-quater F1+F2: shift uniforme Δ=30px a destra del blocco INPUT
    // (box INPUT 254->224, tutti gli altri box/assi invariati) + cornice
    // 11..139 (h128, margini 11 come refit 824; centro 75 = knobCY).
    static constexpr int frameTop = 11, frameBottom = 139, chamfer = 9;

    // Riga titoli (alto) e riga etichette (basso).
    // 14-bis F5: titoli centrati tra frameTop e punta tacca -> rect h14 top=20.
    // 14-quater F2: ((frameBottom+104)/2)-7 = 114.
    static constexpr int titleY = 20, bottomLabelY = 114;

    // 14-bis F2: una cornice esterna unica (inX0..mdX1) con chamfer solo agli
    // angoli esterni + 5 divisorie verticali (a fbX0/dlX0/dtX0/hdX0/mdX0).
    // 14-quater F1: Δ=30px da fbX0 a mdX1 (box largheze invariate, mdX1
    // 842->812); campo destro 812..1000 solo respiro (nessun cambio logo).
    // 14-f F2: INPUT si stringe di 20 (inX1 235->215), FB e DELAY traslano
    // a sinistra di 20 (larghezze invariate), DELAY TIME guadagna +20px a
    // sinistra (394..588); dtX1/hdX0 588 e tutto il resto invariato.
    // gap_PEAK = 215-170 = 45 = gap_FEEDBACK (260-215).
    static constexpr int inX0 = 11,  inX1 = 215;   // INPUT (jack + LEVEL)
    static constexpr int fbX0 = 215, fbX1 = 305;   // FEED BACK
    static constexpr int dlX0 = 305, dlX1 = 394;   // DELAY
    static constexpr int dtX0 = 394, dtX1 = 588;   // DELAY TIME (RANGE + FACTOR)
    static constexpr int hdX0 = 588, hdX1 = 638;   // HOLD
    static constexpr int mdX0 = 638, mdX1 = 812;   // MODULATION

    // 14-f F3: il titolo DELAY TIME torna ALLINEATO A DESTRA (come 14d):
    // fine ink a dtTitleX1-7 = 581 (7px di garanzia dalla divisoria 588,
    // stessa misura della label FEED BACK rispetto al suo bordo a 325).
    static constexpr int dtTitleX0 = 394, dtTitleX1 = 588;

    static constexpr int knobCY = 75;              // centro dei potenziometri
    static constexpr int peakX   = 170;            // 14-e R2: 178-8 (vs INPUT >=36px)
    static constexpr int fbX     = 260;            // 14-f F2: centro sezione (215+305)/2
    static constexpr int dlX     = 350;            // 14-f F2: centro sezione (305+394)/2 = 349.5
    static constexpr int rangeX  = 446;            // 14-f F2: centro nuovo DT 491, spread 90
    static constexpr int factorX = 536;            // 14-f F2: 446+90
    static constexpr int speedX  = 687;            // 14-f F4: mdCx 725, p=76
    static constexpr int depthX  = 763;            // 14-f F4: 687+76

    static constexpr int jackCX = 65, jackCY = 75;

    // Titolo INPUT centrato sull'asse del jack (14-B, item 2) e rettangolo
    // hit per click/cursore (item 11). Deve combaciare con sectionLabel
    // (inset +4, h14) e con l'origine di InputJack.
    static constexpr int inputTitleX0 = inX0;
    static constexpr int inputTitleX1 = 2 * jackCX - inX0;               // 119
    static constexpr int inputLabelX  = inputTitleX0 + 4;                // 15
    static constexpr int inputLabelY  = titleY;                          // 20
    static constexpr int inputLabelW  = inputTitleX1 - inputTitleX0 - 8; // 100
    static constexpr int inputLabelH  = 14;

    // 14-quater F5: POWER centro y32-4 -> bounds ledY 32 (centro 36).
    // 14-e R2: PEAK LED segue il pot -8 (211->203, asse+33).
    // 14-g G4: POWER switch 36x36 (era 44x44), asse x invariato 972
    // (cx 908 collideva col logo "Seiwa"/DIGITAL DELAY, opzione B).
    static constexpr int ledY = 32, peakLedY = 23, holdLedY = 23;
    static constexpr int peakLedX  = 203;           // 211-8
    static constexpr int holdLedX  = 613;           // 643-30
    static constexpr int powerLedX = 972;           // campo destro invariato
    static constexpr int holdSwX   = 613;           // 643-30
    static constexpr int powerSwX  = 972;

    // Origine (in coordinate di progetto) dei bounds di InputJack: deve
    // combaciare con resized() e con kOrigin in InputJack.cpp. y = titleY
    // per includere nella hit-area il titolo INPUT (14-bis F5: y20).
    static constexpr int inputY0 = 20;
};

float trackedWidth (const juce::Font& font, const juce::String& text, float tracking);
void drawTrackedCentred (juce::Graphics& g, const juce::Font& font, const juce::String& text,
                         const juce::Rectangle<float>& area, float tracking, const juce::Colour& colour);
// 14-f F3: right-aligned (ink di destra sul bordo destro dell'area).
void drawTrackedRight (juce::Graphics& g, const juce::Font& font, const juce::String& text,
                       const juce::Rectangle<float>& area, float tracking, const juce::Colour& colour);

} // namespace ddxui

// Sfondo del pannello: verniciatura nera mottata, cornici di sezione e
// serigrafia oro.
class RackPanel : public juce::Component
{
public:
    RackPanel();
    void paint (juce::Graphics&) override;

    void setStereoOn (bool on); // repaint immediato su cambio (nessun fade)

private:
    void ensureNeon();

    bool stereoOn_ = false;
    juce::Image neonGlow_;  // layer dietro: testo piu' chiaro, blur gaussiano
    juce::Image neonSharp_; // layer davanti: testo saturo #B4281E

    // 15: asset renderizzato opzionale (docs/ASSET_BRIEF.md B.5). Il base
    // contiene gradiente+cornice+bowtie+titoli/label (tranne INPUT)+logo;
    // la variante stereo (opzionale, D10) e' usata al posto del neon
    // procedurale quando STEREO_MODE e' on. Assente -> fallback identico 14-k.
    RenderedAsset assetPanel_;
    RenderedAsset assetPanelStereo_;
    bool hasAsset_ = false;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (RackPanel)
};
