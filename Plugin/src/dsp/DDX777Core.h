#pragma once

#include <cmath>

#include "Params.h"
#include "Filters.h"
#include "DelayLine.h"
#include "Compressor.h"
#include "OrganicSeed.h"

namespace ddx
{

// Catena audio mono DDX-777 (HANDOFF §3, aggiornata Sessione 13c):
//   INPUT → LEVEL → JFET 2SK118 (saturazione) → M5221P (soft clip ai rail)
//   → SOMMATORE pin 5 (segnale + feedback reostato post-DAC, bias DC)
//   → gain cell NE571 (hard limit +8 dBm) → compressore NE571
//   → anti-aliasing → campionatore @ f_word (12 bit) → delay 16384 word
//   → DAC (interp.) → ricostruzione → MIX (dry + wet×DELAY LEVEL) / DIRECT (dry)
//
// Clock: VCO f_base (misurata, trim ±3%) × FACTOR × LFO (SPEED/DEPTH) —
// la modulazione entra PRIMA della divisione (§9) e produce wow/chorus.
// HOLD: freeze della scrittura, la lettura continua → loop del contenuto
// memorizzato [ipotesi §3].
class DDX777Core
{
public:
    void prepare (double fs)
    {
        fs_ = fs;
        comp_.prepare (fs);
        applyFilters();
        reset();
    }

void reset()
    {
        delay_.clear();
        comp_.reset();
        eq1_.reset(); eq2_.reset(); eq3_.reset();
        aa1_.reset(); aa2_.reset(); aa3_.reset(); aa4_.reset();
        rec_.reset();
        rec2_.reset();
        rec3_.reset();
        rec4_.reset();
        rec5_.reset();
        outLP_.reset();
        bufLP_.reset();
        m2_ = 0.0;
        opLP1_.reset(); opLP2_.reset(); opLP3_.reset(); opLP4_.reset();
        writePos_ = 0.0;
        readPos_ = 0.0;
        delayWordsSm_ = static_cast<double> (delayWordsFor (9));
        lfoPhase_ = 0.0;
        peakEnv_ = 0.0;
        peakLed_ = false;
        aaPrev_ = 0.0f;
        wPrev_ = 0.0f;
        rng_ = Rng (0x1234567u);
        // Smoothing per parametri modulazione (tau ~50 ms)
        speedSm_ = 0.0f;
        depthSm_ = 0.0f;
    }

    void setParams (const Params& p)
    {
        p_ = p;

        tol_ = p.organic ? tolerancesFor (p.seed) : Tolerances();

        comp_.setDetectorTimes (0.008 * tol_.detector, 0.06 * tol_.detector);
        // Hard limiter: soglia fissa a -20 dBFS peak (NE571 limiter mode)
        comp_.configure (kThresholdDb);
        applyFilters();

        targetDelayWords_ = static_cast<double> (delayWordsFor (p.rangeIdx));
    }

    // ----- rendering di un blocco -----
    // outMix = dry + wet×delayLevel (MIX OUT); outDirect = dry (DIRECT);
    // outWet = uscita D/A pura (per analisi, opzionale).
    void process (const float* in, float* outMix, float* outDirect, int n,
                  float* outWet = nullptr)
    {
        const double kLfoBase = 0.05;                    // Hz a SPEED=0 (spento)
        
        // Smoothing parametri modulazione (tau ~50 ms) — coefficiente
        // per-sample. Lo smoothing e' applicato DENTRO il loop (per-sample)
        // subito sotto: applicarlo una volta per blocco rendeva il tempo di
        // assestamento reale ~500x piu' lento (~25 s invece di ~50 ms).
        const double kSmoothCoeff = 1.0 - std::exp (-1.0 / (fs_ * 0.05));
        // FACTOR NON smoothed: influenza direttamente il delay timing

        const double trimEff = static_cast<double> (p_.trim) * tol_.clock;
        const double fWordNom = kFbase * trimEff * factorClockFor (p_.factor);
        lastFWord_ = fWordNom;

        const double stepNom = fWordNom / fs_;
        const double kd = 1.0 - std::exp (-1.0 / (fs_ * 0.005)); // rampa 5 ms su RANGE
        const double hissAmp = kHissRms * p_.hissMul * tol_.noise * 1.7320508f; // RMS→ampiezza uniforme
        const bool hold = p_.hold;
        const float gIn = p_.inputLevel;

        // P1 (Sessione 13c): feedback a reostato. Il pot FEEDBACK regola
        // contemporaneamente (a) la quantita' di segnale ritardato reiniettato
        // (resistenza in serie R_pot = (1-pot)*50k tra il tap post-DAC e il
        // sommatore) e (b) il bias DC del compressore (pull-up a VCC sul nodo
        // del cursore). Gain di loop vs pot: tabella L(fb) calibrata sui
        // numeri di ripetizione HW (taper equivalente del reostato, 13c).
        const double fbPot = static_cast<double> (clamp01 (p_.feedback));
        const double fbGain = loopGainFor (fbPot) * loopScale_;
        // Bias DC sul compressore: piu' feedback -> soglia piu' bassa (piu'
        // pumping). Span calibrato (kFeedbackSpanDb=12 era la stima iniziale).
        comp_.configure (kThresholdDb - fbPot * biasSpanDb_);

        for (int i = 0; i < n; ++i)
        {
            // Smoothing parametri modulazione per-sample (tau ~50 ms)
            speedSm_  += static_cast<float> (kSmoothCoeff * (p_.speed  - speedSm_));
            depthSm_  += static_cast<float> (kSmoothCoeff * (p_.depth  - depthSm_));

            const float xIn = in[i];
            const float dry = xIn * gIn;

            // --- P3 (Sessione 13c): saturazione d'ingresso, ordine reale ---
            // Gli stadi sono "bit-identity" quando disabilitati (sentinelle
            // 0 / >1 dal test harness): il quantizzatore 12 bit su toni
            // quasi-coerenti e' sensibile a 1 ulp di differenza -> la via
            // "transparent" deve restare bit-identica al baseline 13b.
            // 1) JFET 2SK118: transfer quadratica Id ~ gm0*v + Idss/|Vp|^2 * v^2
            //    (kJfet = Vx / (2*(1-m)*|Vp|): Vx scala del nodo, m bias,
            //    vedi 03_blocchi.md s3 e report calibrazione)
            float s1 = dry;
            if (kJfet_ != 0.0)
                s1 = dry + static_cast<float> (kJfet_) * dry * dry;
            // 2) M5221P dual JFET op-amp: soft limit dell'uscita ai rail
            //    (Vom ±13 typ a ±15 V). 13h: lineare fino a 0.9*Vom poi knee
            //    C1 nel tanh normalizzato (datasheet: THD 0.007% typ @1 kHz,
            //    grafico p03 THD=1% solo oltre ~0.95*Vom)
            if (thrM5221_ <= 1.0)
            {
                const double m5 = static_cast<double> (thrM5221_);
                const double x = static_cast<double> (s1);
                const double u = std::fabs (x) / m5;
                if (u >= 1.4)
                    s1 = static_cast<float> (m5 * std::tanh (x / m5));
                else if (u > 0.9)
                {
                    const double t = (u - 0.9) / 0.5;
                    const double s = t * t * (3.0 - 2.0 * t);
                    s1 = static_cast<float>
                         (x - s * (x - m5 * std::tanh (x / m5)));
                }
            }
            // P1 (Sessione 13c): feedback a reostato, nodo di somma sul pin 5
            // NE571 (inv. input della gain cell): segnale diretto + audio
            // ritardato reiniettato (tap DOPO i filtri di ricostruzione DAC).
            const float s2 = s1 + static_cast<float> (fbGain) * wPrev_;
            // 3) NE571 gain cell: hard limit (+8 dBm -> 0.20 nel dominio)
            float s3 = s2;
            if (limNE571_ <= 1.0)
            {
                const float lim = static_cast<float> (limNE571_);
                if (s3 > lim) s3 = lim;
                else if (s3 < -lim) s3 = -lim;
            }

            // --- ramo compressore (NE571 ch.1, bias da FEEDBACK) ---
            float c = comp_.process (s3);

            // --- filtro anti-aliasing + equalizzazione (§6: piatto a 15 kHz,
            //     taglio 15-16 kHz; EQ pre-sampler cancella il droop del
            //     campionatore/interpolazione, vedi fit_filters.py) ---
            float a = eq1_.process (c);
            a = eq2_.process (a);
            a = eq3_.process (a);
            a = aa4_.process (a);
            a = aa3_.process (a);
            a = aa2_.process (a);
            a = aa1_.process (a);

            // Virtual ADC 32 kHz: filtro decimazione (ADC anti-alias 8° @ 15 kHz)
            if (virtualAdc_)
            {
                a = dec1_.process (a);
                a = dec2_.process (a);
                a = dec3_.process (a);
                a = dec4_.process (a);
            }

// --- clock con LFO (modulazione del VCO, §9) ---
            double mod = 0.0;
            if (depthSm_ > 1.0e-4f && speedSm_ > 1.0e-4f)
            {
                // ricalcolati per-sample perche' speedSm_/depthSm_ cambiano ogni campione
                const double fLfo = kLfoBase * std::pow (160.0, clamp01 (speedSm_)); // ..8 Hz
                const double modDepth = 0.08 * clamp01 (depthSm_); // ±8% di tempo a DEPTH 10
                const double lfoInc = fLfo / fs_;
                lfoPhase_ += lfoInc;
                if (lfoPhase_ >= 1.0) lfoPhase_ -= 1.0;
                mod = modDepth * std::sin (2.0 * 3.14159265358979323846 * lfoPhase_);
            }
            const double step = stepNom * (1.0 + mod);

            // --- HOLD crossfade on write enable (smooth freeze/unfreeze) ---
            writeEnableTarget_ = p_.hold ? 0.0f : 1.0f;
            writeEnable_ += kWriteCrossfade * (writeEnableTarget_ - writeEnable_);

            // HOLD release: detect transition from hold to not-hold
            // When released, inject the current frozen content into the feedback loop
            if (holdPrev_ && !p_.hold)
            {
                // Re-inject current delay content at readPos_ into the write path
                // This simulates the frozen signal entering the feedback circuit
                float frozenSample = delay_.readCubic (readPos_);
                // The next write will include this frozen sample mixed with feedback
                // We achieve this by writing the frozen sample at current writePos
                // and advancing writePos by one word
                delay_.write (static_cast<int> (writePos_), frozenSample);
                writePos_ += 1.0;
                if (writePos_ >= kMemoryWords) writePos_ -= kMemoryWords;
            }
            holdPrev_ = p_.hold;

            // --- eventi di campionamento: scrittura al traverso dei word clock ---
            // Il valore campionato è il segnale post-AA interpolato sub-campione.
            if (writeEnable_ > 0.001f)
            {
                const double prev = writePos_;
                const double target = prev + step;

                if (target >= static_cast<double> (kMemoryWords))
                {
                    emitSegment (0.0, prev, static_cast<double> (kMemoryWords), prev,
                                 step, aaPrev_, a);
                    emitSegment (static_cast<double> (kMemoryWords), 0.0,
                                 target - kMemoryWords, prev, step, aaPrev_, a);
                    writePos_ = target - kMemoryWords;
                }
                else
                {
                    emitSegment (0.0, prev, target, prev, step, aaPrev_, a);
                    writePos_ = target;
                }

                delayWordsSm_ += kd * (targetDelayWords_ - delayWordsSm_);
                readPos_ = writePos_ - delayWordsSm_;
                if (readPos_ < 0.0) readPos_ += kMemoryWords;
            }
            else
            {
                // HOLD: scrittura ferma (crossfaded), la lettura continua -> loop (freeze)
                readPos_ += step;
                if (readPos_ >= kMemoryWords) readPos_ -= kMemoryWords;
            }
            aaPrev_ = a;

            // --- DAC: interpolazione cubica + ricostruzione ---
            float w = delay_.readCubic (readPos_);

            // Virtual ADC 32 kHz: filtro interpolazione (DAC reconstruction 8° @ 15 kHz)
            if (virtualAdc_)
            {
                w = int1_.process (w);
                w = int2_.process (w);
                w = int3_.process (w);
                w = int4_.process (w);
            }

            w = rec_.process (w);
            w = rec2_.process (w);
            w = rec3_.process (w);
            w = rec4_.process (w);
            w = rec5_.process (w);

            // P1 (Sessione 13c): punto di tap del reostato (post-DAC, per il
            // prossimo campione: la re-iniezione arriva all'additore con un
            // latency di linea di 1 campione, trascurabile). Il tap resta
            // PULITO (Sessione 13d): il fondo di rumore non circola nel loop —
            // le misure HW hanno il floor fisso a ~-77 dB RMS per tutti i FB,
            // senza accumulo progressivo (FEEDBACK_ANALYSIS_v2.md §5) -> la
            // fonte di rumore dominante e' post-loop, non re-iniettata.
            wPrev_ = w;

            // Hiss analogico: floor fisso POST-loop (aggiunto UNA volta al
            // mix out, NON al solo wet: il floor analogico è presente su tutta
            // la catena — misure HW FEEDBACK_ANALYSIS_v2 §2: -77 dBFS identico
            // su FB=0/2/10). Livello ricalibrato 13d: post-loop il rumore non
            // passa piu' dalla catena 15 kHz, quindi kHissRms (vedi sotto) e'
            // tarato direttamente sul floor HW -77.3 dBFS.
            const float wOut = w;

            if (outMix != nullptr)
            {
                // Equal-power crossfade: dryGain = cos(angle), wetGain = sin(angle)
                // angle = delayLevel * PI/2, where delayLevel in [0,1] maps to [0, PI/2]
                const float angle = std::min(1.0f, std::max(0.0f, p_.delayLevel)) * 1.57079632679f;
                const float dryGain = std::cos(angle);
                const float wetGain = std::sin(angle);
                double mo = dry * dryGain + wOut * wetGain;
                mo += static_cast<double> (rng_.nextBipolar() * hissAmp); // hiss sul mix out
                if (! charDistOff_)
                {
                    // Meccanismo A (Sessione 12, datasheet NE570N p.6 "VARIABLE GAIN
                    // CELL"): offset VOS della cella -> 2a armonica proporzionale
                    // all'ampiezza (THD% = k x VOS x VIN). Applicato sul segnale
                    // di ingresso (dry, piano in banda) DOPO il mix: i dati T4
                    // mostrano H2% costante in banda (0.031% a 1 kHz, 0.0345% a
                    // 10 kHz nonostante A1 cali di 5.4 dB) -> H2 segue il livello
                    // di ingresso, non quello del mix; e la riga a 20 kHz arriva
                    // in uscita a pieno livello mentre la catena 32 kHz del
                    // modello la attenuerebbe di ~25 dB.
                    // m2_ = stima E[dry²]: toglie il DC al quadrato.
                    if (kVos_ != 0.0)
                    {
                        const double dv = static_cast<double> (dry);
                        m2_ += kM2 * (dv * dv - m2_);
                        mo += kVos_ * (dv * dv - m2_);
                    }
                    // Meccanismo B (datasheet p.7): crossover distortion dello
                    // stadio di uscita (quiescent current bassa, dead zone al
                    // traverso zero) -> banda < 500 Hz dominata da armoniche
                    // dispari (T4 a 100 Hz: H3 -50.9 dB > H2 -54.7 dB).
                    if (kLo_ != 0.0)
                    {
                        const double lo = outLP_.process (static_cast<float> (mo));
                        mo += kLo_ * lo * lo * lo;
                    }
                }
                // Comp 4 (Fase 2): buffer di uscita (op-amp): banda @ 15 kHz +
                // saturazione soft tanh. kBuffer = 0 → trasparente.
                if (kBuffer_ != 0.0)
                {
                    const double bl = bufLP_.process (static_cast<float> (mo));
                    mo = bl + kBuffer_ * (std::tanh (bl) - bl);
                }
                // Comp 5 (Fase 2): 4 stadi op-amp 4558D: nonlinearita tanh +
                // banda @ 40 kHz (GBW/stadio). kOpAmp = 0 → trasparente.
                if (kOpAmp_ != 0.0)
                {
                    Biquad* oplp[4] = { &opLP1_, &opLP2_, &opLP3_, &opLP4_ };
                    for (int st = 0; st < 4; ++st)
                    {
                        const double b = oplp[st]->process (static_cast<float> (mo));
                        mo = b + kOpAmp_ * (std::tanh (b) - b);
                    }
                }
                outMix[i] = static_cast<float> (mo);
            }
            if (outDirect != nullptr)  outDirect[i] = dry;
            if (outWet != nullptr)
                outWet[i] = wOut + static_cast<float> (rng_.nextBipolar() * hissAmp); // tap wet: floor DAC

            // --- ramo PEAK LED (parallelo, fuori dal segnale) ---
            const double rect = std::fabs (static_cast<double> (dry));
            peakEnv_ += (rect > peakEnv_ ? 0.05 : 0.001) * (rect - peakEnv_);
            const double thr = 0.02 + 0.9 * clamp01 (p_.peakLevel);
            if (peakEnv_ > thr)                        peakLed_ = true;
            else if (peakEnv_ < thr * 0.7)             peakLed_ = false;
        }
    }

    // ----- accessori -----
    double sampleRate() const noexcept { return fs_; }
    double clockHz() const noexcept { return lastFWord_; }        // senza LFO
    double delayMs() const noexcept
    {
        return 1000.0 * delayWordsSm_ / lastFWord_;
    }
    double delayWords() const noexcept { return delayWordsSm_; }
    bool peakLedOn() const noexcept { return peakLed_; }
    double peakEnvelope() const noexcept { return peakEnv_; }
    const Params& params() const noexcept { return p_; }

// coefficienti di calibrazione (usati da verify.py / harness per debug)
    static constexpr double kThresholdDb = -20.0;  // limiter NE571: soglia fissa -20 dBFS peak

            static constexpr float  kHissRms = 1.3646e-4f; // 10^(-77.3/20): floor HW T3.
                                                        // Sessione 13c: 1.8e-4 era tarato
                                                        // con l'hiss IN-loop (passava dalla
                                                        // catena 15 kHz, che togliva ~2.4 dB
                                                        // di potenza di banda). Sessione 13d:
                                                        // hiss POST-loop (tap pulito, no
                                                        // accumulo nel loop — vedi processo()
                                                        // e FEEDBACK_ANALYSIS_v2.md §5),
                                                        // quindi il valore e' tarato
                                                        // direttamente sul floor -77.3 dBFS.
                                                        // (LSB 12 bit = 4.88e-4: senza dither
                                                        // sigma < 0.5 LSB quantizza a ZERO.)
    // Meccanismi di distorsione d'uscita (Sessione 12 — datasheet NE570N):
    // Meccanismo A: offset VOS gain cell -> 2a armonica ∝ ampiezza (kVos, membro)
    // Meccanismo B: crossover output stage -> dispari in banda < 500 Hz (kLo, membro)
    // Calibrati su T4 (100 Hz / 1 kHz / 10 kHz, -20 dBFS RMS): H2 HW 0.18/0.031/
    // 0.034% e H3 HW 0.32% a 100 Hz. Calibrazione relativa (scaling analogico
    // sconosciuto, vedi L24 R_in).
    static constexpr double kM2 = 0.001;    // tau stima E[mo²] (~10 ms @96 kHz)

    // Flag per caratterizzazione THD
    void setCharDistOff (bool on) { charDistOff_ = on; }
    void setCharCompOff (bool on) { comp_.setDisabled (on); }
    void setVirtualAdc (bool on) { virtualAdc_ = on; }

    // Coefficienti Fase 2 (0 = trasparente; tarati su misure HW)
    void setKRect (double k) { comp_.setKRect (k); }
    void setKdac2 (double k) { kDac2_ = k; }
    void setKdac3 (double k) { kDac3_ = k; }
    void setKbuffer (double k) { kBuffer_ = k; }
    void setKopamp (double k) { kOpAmp_ = k; }
    void setKVos (double k) { kVos_ = k; }
    void setKLo (double k) { kLo_ = k; }

    // P3/P1 (Sessione 13c): coefficienti saturazione ingresso e feedback
    // reostato (calibrazione/diagnostica; i default sono i valori fisici
    // dai datasheet, vedi report calibrazione e 03_blocchi.md)
    void setKjfet (double k) { kJfet_ = k; }
    void setThrM5221 (double t) { thrM5221_ = t; }
    void setLimNE571 (double l) { limNE571_ = l; }
    void setLoopScale (double s) { loopScale_ = s; }
    void setBiasSpan (double s) { biasSpanDb_ = s; }

private:
    // Tabella del gain di loop vs pot FEEDBACK (ricalibrazione v2, sessione
    // 13d — FEEDBACK_ANALYSIS_v2.md, soglia -60 dBFS). Valori = gain del
    // segnale reiniettato (pre-catena); il gain di loop TOTALE misurato in
    // uscita e' valore x gain della catena per-passo, che NON e' costante:
    // a FB 100% gli echi stazionano a -40/-45 dB dove la catena vale ~1.17,
    // a FB 50/25% la catena vale ~1.0 (misurato 13d, coppie 20-36). I target
    // totali sono i G lineari HW a -60 dBFS: FB 100% -> 0.90 (22 echi),
    // 50% -> 0.34, 25% -> 0.10. g[0]=0: a 0% feedback il reostato apre il
    // loop -> nessun repeat. Loop < 1 a 100%: decadimento lento, nessun
    // plateau/autoscillazione sostenuta. Dettaglio: LOOP_CALIBRATION.md.
    double loopGainFor (double fb) const
    {
        static const double f[4] = { 0.0, 0.25, 0.5, 1.0 };
        static const double g[4] = { 0.0, 0.105, 0.345, 0.760 };

        if (fb <= f[0]) return g[0];
        if (fb >= f[3]) return g[3];
        for (int i = 1; i < 4; ++i)
            if (fb <= f[i])
            {
                const double t = (fb - f[i - 1]) / (f[i] - f[i - 1]);
                return g[i - 1] + t * (g[i] - g[i - 1]);
            }
        return g[3];
    }

private:
    static float clamp01 (float v) { return v < 0.0f ? 0.0f : (v > 1.0f ? 1.0f : v); }
    static int clampIdx (int v, int n) { return v < 0 ? 0 : (v >= n ? n - 1 : v); }

    void applyFilters()
    {
        const double s = tol_.cutoff;  // tolleranza organica ±10% sui cutoff
        // Stabilita': il biquad lowpass RBJ e' stabile solo per f < fs/2.
        // A 44.1/48 kHz (gli sample rate comuni degli host) i cutoff
        // 24-48 kHz (rec2/rec4/rec5, stadi op-amp 40 kHz) superano Nyquist:
        // i poli escono dal cerchio unitario e l'IIR diverge a ±1e40/NaN in
        // ~50 ms (il plugin "non fa audio" a 44.1/48 kHz, era stabile solo a
        // >= 88.2 kHz dove viveva la calibrazione). Clamp a 0.45*fs solo
        // quando serve: da 88.2 kHz in su i valori restano bit-identici.
        const double nyq = 0.5 * fs_;
        const double fClamp = 0.45 * fs_;
        auto cut = [nyq, fClamp] (double f) { return f > nyq ? fClamp : f; };

        // equalizzazione pre-campionatore (fit_filters6: correzione additiva su
        // curva wet/direct a livello costante, modello RBJ verificato vs freqz;
        // pesi 100Hz-14k rigidi, 14-16.5k liberi per attutire 19-25 kHz = T5)
        eq1_.setHighShelf (fs_, cut (250.000 * s), 0.020, 1.200);
        eq2_.setPeak (fs_, cut (11730.7 * s), 0.957, 3.020);
        eq3_.setPeak (fs_, cut (14000.0 * s), 2.500, 12.000);

        // anti-aliasing 8 poli (4 sezioni RBJ): eq3 compensa il droop del
        // campionatore sopra 12 kHz, aa2/aa3 chiudono lo stopband 17-26 kHz
        aa1_.setLowpass (fs_, cut (10400.5 * s), 1.076);
        aa2_.setLowpass (fs_, cut (16500.0 * s), 0.539);
        aa3_.setLowpass (fs_, cut (14200.0 * s), 0.400);
        aa4_.setLowpass (fs_, cut (15000.0 * s), 3.000);

        // ricostruzione D/A (post-campionatore): 2 sezioni Butterworth a 15.5 kHz.
        // Un solo biquad (12 dB/ott) lasciava passare i campioni immagine
        // 16-31 kHz del campionatore a 31030 Hz, che il filtro di analisi di
        // T5 (butter 4 @15 kHz, stopband ~24 dB/ott) ricompone in banda:
        // era la voce dominante della misura T5 (LP24k non la riduceva).
        rec_.setLowpass (fs_, cut (18000.0 * s), 0.707);
        rec2_.setLowpass (fs_, cut (24000.0 * s), 0.707);
        rec3_.setLowpass (fs_, cut (14000.0 * s), 0.707);
        rec4_.setLowpass (fs_, cut (28000.0 * s), 0.707);
        rec5_.setLowpass (fs_, cut (48000.0 * s), 0.707);  // no-op near Nyquist

        // crossover 1 kHz (Butterworth) per la distorsione d'uscita selettiva
        outLP_.setLowpass (fs_, cut (500.0 * s), 0.707);

        // Comp 4 (Fase 2): banda op-amp buffer di uscita @ 15 kHz
        bufLP_.setLowpass (fs_, cut (15000.0 * s), 0.707);
        // Comp 5 (Fase 2): banda stadi op-amp 4558D @ 40 kHz
        opLP1_.setLowpass (fs_, cut (40000.0 * s), 0.707);
        opLP2_.setLowpass (fs_, cut (40000.0 * s), 0.707);
        opLP3_.setLowpass (fs_, cut (40000.0 * s), 0.707);
        opLP4_.setLowpass (fs_, cut (40000.0 * s), 0.707);

        // Virtual ADC 32 kHz: decimation 96→32 kHz (Butterworth 8° @ 15 kHz = 4 biquad)
        dec1_.setLowpass (fs_, cut (15000.0 * s), 0.5411961);
        dec2_.setLowpass (fs_, cut (15000.0 * s), 1.3065630);
        dec3_.setLowpass (fs_, cut (15000.0 * s), 0.5411961);
        dec4_.setLowpass (fs_, cut (15000.0 * s), 1.3065630);
        // Interpolation 32→96 kHz (stesso filtro)
        int1_.setLowpass (fs_, cut (15000.0 * s), 0.5411961);
        int2_.setLowpass (fs_, cut (15000.0 * s), 1.3065630);
        int3_.setLowpass (fs_, cut (15000.0 * s), 0.5411961);
        int4_.setLowpass (fs_, cut (15000.0 * s), 1.3065630);
    }

public:
    // Sovrascrizione numerica dei filtri (solo per sweep di calibrazione dal
    // test harness): fissa la catena con s=1.0 (niente tolleranza organica).
    // Ordine valori: eq2f eq2q eq2g eq3f eq3q eq3g aa1f aa1q aa2f aa2q
    //                aa3f aa3q aa4f aa4q recf rec2f rec3f rec4f rec5f
    void overrideFilters (const double v[19])
    {
        const double s = 1.0;
        eq2_.setPeak (fs_, v[0] * s, v[1], v[2]);
        eq3_.setPeak (fs_, v[3] * s, v[4], v[5]);
        aa1_.setLowpass (fs_, v[6] * s, v[7]);
        aa2_.setLowpass (fs_, v[8] * s, v[9]);
        aa3_.setLowpass (fs_, v[10] * s, v[11]);
        aa4_.setLowpass (fs_, v[12] * s, v[13]);
        rec_.setLowpass (fs_, v[14] * s, 0.707);
        rec2_.setLowpass (fs_, v[15] * s, 0.707);
        rec3_.setLowpass (fs_, v[16] * s, 0.707);
        rec4_.setLowpass (fs_, v[17] * s, 0.707);
        rec5_.setLowpass (fs_, v[18] * s, 0.707);
    }

private:

    // Un segmento di avanzamento: crosses i word clock in (aLocal, bLocal],
    // con coordinate assolute per l'interpolazione del segnale.
    void emitSegment (double base, double aLocal, double bLocal, double aAbs,
                      double step, float vPrev, float vNow)
    {
        if (bLocal <= aLocal)
            return;

        const long kFirst = static_cast<long> (std::floor (aLocal)) + 1;
        const long kLast = static_cast<long> (std::floor (bLocal));

        for (long k = kFirst; k <= kLast; ++k)
        {
            double frac = (base + static_cast<double> (k) - aAbs) / step;
            if (frac < 0.0) frac = 0.0;
            if (frac > 1.0) frac = 1.0;

            const float xs = vPrev + (vNow - vPrev) * static_cast<float> (frac);

            // --- dither TPDF opzionale (§7) + quantizzazione 12 bit (ADC in U4) ---
            const float d = p_.dither
                                ? 0.5f * (rng_.nextBipolar() + rng_.nextBipolar())
                                : 0.0f;
            // Comp 3 (Fase 2): mismatch R-2R del DAC 12 bit — nonlinearita
            // 2a/3a armonica applicata DOPO la quantizzazione (dominio 32 kHz).
            // kDac2/kDac3 = 0 → trasparente.
            float q = quantize12 (xs, d);
            if (kDac2_ != 0.0 || kDac3_ != 0.0)
            {
                const double qd = q;
                q = static_cast<float> (qd + kDac2_ * qd * qd
                                            + kDac3_ * qd * qd * qd);
            }
            delay_.write (static_cast<int> (base + static_cast<double> (k)), q);
        }
    }

    Params p_;
    Tolerances tol_;

    double fs_ = 48000.0;
    double lastFWord_ = kFbase;

    DelayLine delay_;
    Compressor comp_;
    Biquad eq1_, eq2_, eq3_;
    Biquad aa1_, aa2_, aa3_, aa4_;
    Biquad rec_;
    Biquad rec2_;
    Biquad rec3_;
    Biquad rec4_;
    Biquad rec5_;
    Biquad outLP_;   // crossover 500 Hz per Meccanismo B (crossover, banda < 500 Hz)
    // Virtual ADC 32 kHz: downsample 96→32 (4 biquad = 8° ordine @ 15 kHz)
    Biquad dec1_, dec2_, dec3_, dec4_;
    // upsample 32→96 (4 biquad = 8° ordine @ 15 kHz)
    Biquad int1_, int2_, int3_, int4_;
    // Comp 4 (Fase 2): buffer di uscita op-amp, banda @ 15 kHz
    Biquad bufLP_;
    // Comp 5 (Fase 2): 4 stadi op-amp 4558D, banda @ 40 kHz
    Biquad opLP1_, opLP2_, opLP3_, opLP4_;
    Rng rng_ { 0x1234567u };

    double writePos_ = 0.0;
    double readPos_ = 0.0;
    double delayWordsSm_ = 16384.0;
    double targetDelayWords_ = 16384.0;
    double lfoPhase_ = 0.0;
    double peakEnv_ = 0.0;
    bool peakLed_ = false;
    float aaPrev_ = 0.0f;
    float wPrev_ = 0.0f;      // P1: tap post-DAC del sample precedente (feedback reostato)
    bool charDistOff_ = false;
    bool virtualAdc_ = true;   // Comp 1 (Fase 2): Virtual ADC 32 kHz attivo di default
    // HOLD crossfade on write enable (not output): smooth freeze/unfreeze
    float writeEnable_ = 1.0f;
    float writeEnableTarget_ = 1.0f;
    static constexpr float kWriteCrossfade = 1.0f / (0.010f * 96000.0f);  // ~10 ms @ 96 kHz
    // HOLD release: re-inject frozen content into feedback loop
    bool holdPrev_ = false;
    // Smoothing parametri modulazione (tau ~50 ms)
    float speedSm_  = 0.0f;
    float depthSm_  = 0.0f;
    // Coefficienti Fase 2 (0 = trasparente)
    double kDac2_ = 0.0;       // Comp 3: mismatch R-2R 2a armonica
    double kDac3_ = 0.0;       // Comp 3: mismatch R-2R 3a armonica
    double kBuffer_ = 0.0;     // Comp 4: saturazione tanh buffer uscita (calibrato: 0)
    double kOpAmp_ = 0.018;    // Comp 5: nonlinearita stadi op-amp 4558D (calibrato Fase 2: match 10 kHz)
    // Meccanismi Sessione 12 (datasheet NE570N), calibrati su T4:
    double kVos_ = 0.0079;     // Mecc. A: offset VOS gain cell -> 2a armonica (calibrato su T4: H2 1 kHz = 0.0308% vs HW 0.0311%)
    double kLo_ = 0.0;         // Mecc. B: crossover output stage -> H3 banda < 500 Hz. Taratura: 0 (non necessario:
                              // l'H3 a bassa banda e' gia' fornito dalla dinamica del compressore, baseline H3 100 Hz
                              // = 0.42% vs HW 0.32%; ogni kLo > 0 peggiora lo scostamento). Meccanismo disponibile
                              // via --k-lo per test futuri.
    double m2_ = 0.0;          // stima E[dry²] per il DC del quadrato (Mecc. A)
    // P3 (Sessione 13c): saturazione d'ingresso — valori fisici (datasheet):
    //   2SK118  JFET: kJfet = Vx / (2*(1-m)*|Vp|); |Vp| 0.4..5.0 V (tip ~1.5 V),
    //               m = 0.5 (bias a meta' gate), Vx = scala del nodo stimata
    //               4.5 mV (H2 a -20 dBFS ~ meta' della misura HW 0.033%)
    //   M5221P  dual JFET op-amp: soft limit uscita ai rail (Vom ±13 typ @±15V)
    //   NE571   gain cell: hard limit +8 dBm -> 0.20 nel dominio
    double kJfet_ = 0.003;
    double thrM5221_ = 13.0 / 15.0;
    double limNE571_ = 0.20;
    // P1 (Sessione 13c): feedback a reostato — gain di loop vs pot, tabella
    // kLoopGain (taper calibrato sui numeri di ripetizione HW: FB 0%->1 eco,
    // 25%->2-3, 50%->5-10, 75%->15-30, 100%->decadimento lento)
    double loopScale_ = 1.0;   // moltiplicatore diagnostico (calibrazione)
    double biasSpanDb_ = 2.0;  // span effettivo del bias DC sul compressore
};

} // namespace ddx
