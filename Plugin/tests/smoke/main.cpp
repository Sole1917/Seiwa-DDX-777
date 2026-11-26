// ddx_smoke — audio smoke test del plugin COMPLETO (createPluginFilter +
// processBlock), non solo del core DSP. Se il plugin fa silenzio nel host,
// deve farlo anche qui.
//
// usage: ddx_smoke
//
//   T1  impostazioni default: burst di rumore, RMS(out) > 0, no clipping
//   T2  delay eco: RANGE 512 x FACTOR 1.0 -> ~528 ms
//   T3  FACTOR 0.5 -> ~247 ms, FACTOR 2.0 -> ~960 ms (FACTOR continuo)
//   T4  BYPASS: out == in bit-identici
//   T5  mono (1 canale)
//   T6  block da 64 campioni (block size del host)
//   T7  state save/recall (copyXmlToBinary/getXmlFromBinary)
//   T9-T13  feedback audio (13c): conteggio eco a RANGE 64 ms per FB
//           0 / 0.25 / 0.5 / 0.75 / 1.0 (spec: 1 / 2-3 / 5-10 / 15-30 /
//           decadimento lento senza runaway)

#include <juce_core/juce_core.h>
#include <juce_audio_processors/juce_audio_processors.h>

#include <algorithm>
#include <cmath>
#include <cstdio>

juce::AudioProcessor* createPluginFilter();

namespace
{

int g_fail = 0;

void report (bool ok, const char* name, const juce::String& detail = {})
{
    std::printf ("%s%s%s\n",
                 ok ? "PASS " : "FAIL ",
                 name,
                 detail.isEmpty() ? ""
                                  : (juce::String ("  [") + detail + "]").toRawUTF8());
    if (! ok)
        ++g_fail;
}

float rmsAll (const juce::AudioBuffer<float>& buf)
{
    double s = 0.0;
    int n = 0;
    for (int ch = 0; ch < buf.getNumChannels(); ++ch)
    {
        const float* d = buf.getReadPointer (ch);
        for (int i = 0; i < buf.getNumSamples(); ++i)
        {
            s += static_cast<double> (d[i]) * d[i];
            ++n;
        }
    }
    return static_cast<float> (std::sqrt (s / n));
}

void fillNoise (juce::AudioBuffer<float>& buf, int start, int len, float rmsTarget, uint32_t seed)
{
    buf.clear();
    uint32_t s = seed;
    for (int ch = 0; ch < buf.getNumChannels(); ++ch)
    {
        float* d = buf.getWritePointer (ch);
        double acc = 0.0;
        for (int i = start; i < start + len; ++i)
        {
            s = s * 1664525u + 1013904223u;
            const float u = static_cast<float> ((s >> 8) * (1.0 / 16777216.0));
            d[i] = u * 2.0f - 1.0f;
            acc += static_cast<double> (d[i]) * d[i];
        }
        const float scale = static_cast<float> (rmsTarget / std::sqrt (acc / len));
        for (int i = start; i < start + len; ++i)
            d[i] *= scale;
    }
}

// Argmax della cross-correlazione in[] x out[] su lag in [lo, hi]:
// l'eco appare a lag = delay. Il rumore ha autocorrelazione a spike singola.
int echoLag (const float* in, const float* out, int n, int start, int len, int lo, int hi)
{
    int best = lo;
    double bestVal = -1e300;
    for (int lag = lo; lag <= hi; ++lag)
    {
        double c = 0.0;
        for (int i = start; i < start + len && i + lag < n; ++i)
            c += static_cast<double> (in[i]) * out[i + lag];
        if (c > bestVal)
        {
            bestVal = c;
            best = lag;
        }
    }
    return best;
}

float denorm (juce::AudioProcessor& proc, const char* id)
{
    for (auto* p : proc.getParameters())
        if (auto* w = dynamic_cast<juce::AudioProcessorParameterWithID*> (p))
            if (w->getParameterID() == id)
                if (auto* r = dynamic_cast<juce::RangedAudioParameter*> (p))
                    return static_cast<float>
                           (r->getNormalisableRange().convertFrom0to1 (r->getValue()));
    return -1e30f;
}

bool setParam (juce::AudioProcessor& proc, const char* id, float denormValue)
{
    for (auto* p : proc.getParameters())
        if (auto* w = dynamic_cast<juce::AudioProcessorParameterWithID*> (p))
            if (w->getParameterID() == id)
                if (auto* r = dynamic_cast<juce::RangedAudioParameter*> (p))
                {
                    r->setValueNotifyingHost (r->getNormalisableRange()
                                               .convertTo0to1 (denormValue));
                    return true;
                }
    return false;
}

// Conta le ripetizioni (eco) nell'uscita MIX sottraendo il dry (out - g*in).
// D (delay reale, con offset del modello ~ +3%) e' misurato per
// cross-correlazione tra il burst e il wet; la copia k-esima del burst
// giace in [burstStart + k*D, burstStart + k*D + burstLen]. Soglia:
// max(2% del 1o eco, ~1.5 LSB del quantizzatore) per non contare il tick
// di quantizzazione. k=1 = echo diretto del burst (la "1a ripetizione").
int countEchoes (const float* in, const float* out, int n, double fs,
                 int burstStart, int burstLen, double dNomMs, int maxK,
                 double* dMsOut = nullptr, float* lastRatio = nullptr)
{
    int iMax = burstStart;
    for (int i = burstStart; i < burstStart + burstLen; ++i)
        if (std::fabs (in[i]) > std::fabs (in[iMax]))
            iMax = i;
    const double g = out[iMax] / in[iMax];

    // D per cross-correlazione: lag in [0.75*Dnom, 1.5*Dnom]
    const int lo = static_cast<int> (0.75 * dNomMs * fs / 1000.0);
    const int hi = static_cast<int> (1.5 * dNomMs * fs / 1000.0);
    int dS = lo;
    double bestC = -1e300;
    for (int lag = lo; lag <= hi && burstStart + burstLen + lag < n; ++lag)
    {
        double c = 0.0;
        for (int i = burstStart; i < burstStart + burstLen; ++i)
            c += static_cast<double> (in[i])
                 * (static_cast<double> (out[i + lag]) - g * in[i + lag]);
        if (c > bestC)
        {
            bestC = c;
            dS = lag;
        }
    }
    if (dMsOut != nullptr)
        *dMsOut = 1000.0 * dS / fs;

    const int m0 = static_cast<int> (0.001 * fs);
    float peaks[64] = {};
    for (int k = 1; k <= maxK && k < 64; ++k)
    {
        int a = std::max (0, burstStart + k * dS - m0);
        int b = std::min (n - 1, burstStart + k * dS + burstLen + m0);
        double m = 0.0;
        for (int i = a; i <= b; ++i)
            m = std::max (m, std::fabs (static_cast<double> (out[i])
                                        - g * in[i]));
        peaks[k] = static_cast<float> (m);
    }

    const float thr = std::max (0.02f * peaks[1], 8.0e-4f);
    int cnt = 0;
    for (int k = 1; k <= maxK && k < 64; ++k)
    {
        if (peaks[k] > thr)
            ++cnt;
        else
            break;
    }

    if (lastRatio != nullptr && peaks[1] > 0.0f)
        *lastRatio = peaks[cnt >= 2 ? cnt : 1] / peaks[1];
    return cnt;
}

} // namespace

int main()
{
    juce::AudioProcessor* proc = createPluginFilter();

    if (proc == nullptr)
    {
        report (false, "createPluginFilter");
        return 1;
    }

    const double fs = 48000.0;
    proc->prepareToPlay (fs, 512);

    const int total  = static_cast<int> (1.6 * fs);   // 1.6 s
    const int nStart = static_cast<int> (0.3 * fs);   // burst 0.3-0.5 s
    const int nLen   = static_cast<int> (0.2 * fs);
    const float rmsIn = 0.05f;                        // -26 dBFS, sotto la soglia limiter

    juce::MidiBuffer midi;

    auto resetDefaults = [&]
    {
        for (auto* p : proc->getParameters())
            p->setValueNotifyingHost (p->getDefaultValue());
    };

    auto setFactor = [&](float f)
    {
        for (auto* p : proc->getParameters())
            if (auto* w = dynamic_cast<juce::AudioProcessorParameterWithID*> (p))
                if (w->getParameterID() == "FACTOR")
                    if (auto* r = dynamic_cast<juce::RangedAudioParameter*> (p))
                        r->setValueNotifyingHost (r->getNormalisableRange().convertTo0to1 (f));
    };

    auto copyInToOut = [&](const juce::AudioBuffer<float>& in, juce::AudioBuffer<float>& out)
    {
        for (int ch = 0; ch < in.getNumChannels(); ++ch)
            out.copyFrom (ch, 0, in, ch, 0, in.getNumSamples());
    };

    auto processAll = [&](juce::AudioBuffer<float>& out, int blockSize)
    {
        for (int i = 0; i < out.getNumSamples(); i += blockSize)
        {
            const int n = std::min (blockSize, out.getNumSamples() - i);
            float* ptrs[2] = { out.getWritePointer (0) + i,
                               out.getNumChannels() > 1 ? out.getWritePointer (1) + i : nullptr };
            juce::AudioBuffer<float> slice (ptrs, out.getNumChannels(), 0, n);
            proc->processBlock (slice, midi);
        }
    };

    // --- T1 + T2: default (RANGE 512, FACTOR 1.0, MIX 0.95, DELAY_LEVEL 0.5) ---
    {
        resetDefaults();
        juce::AudioBuffer<float> in (2, total), out (2, total);
        fillNoise (in, nStart, nLen, rmsIn, 42u);
        copyInToOut (in, out);
        processAll (out, 512);

        float peak = 0.0f;
        for (int ch = 0; ch < 2; ++ch)
        {
            const float* d = out.getReadPointer (ch);
            for (int i = 0; i < total; ++i)
                peak = std::max (peak, std::fabs (d[i]));
        }

        const float o = rmsAll (out);
        report (o > 0.01f, "T1 audio out (impostazioni default)",
                juce::String ("RMS=" + juce::String (o, 4)));
        report (peak < 0.999f, "T1 no clipping",
                juce::String ("peak=" + juce::String (peak, 4)));

        const int expLag = static_cast<int> (std::lround (528.0 * fs / 1000.0));
        const int lag = echoLag (in.getReadPointer (0), out.getReadPointer (0), total,
                                 nStart, nLen, expLag - 3000, expLag + 3000);
        const double ms = 1000.0 * lag / fs;
        report (std::fabs (ms - 528.0) <= 15.0,
                "T2 delay eco (RANGE 512 x FACTOR 1.0)",
                juce::String (ms, 1) + " ms (atteso ~528)");
    }

    // --- T3: FACTOR continuo ---
    {
        const struct { float factor; double ms; } cases[] =
        {
            { 0.5f, 247.0 },
            { 2.0f, 960.0 },
        };

        for (const auto& c : cases)
        {
            resetDefaults();
            setFactor (c.factor);

            juce::AudioBuffer<float> in (2, total), out (2, total);
            fillNoise (in, nStart, nLen, rmsIn, 7u);
            copyInToOut (in, out);
            processAll (out, 512);

            const int expLag = static_cast<int> (std::lround (c.ms * fs / 1000.0));
            const int lag = echoLag (in.getReadPointer (0), out.getReadPointer (0), total,
                                     nStart, nLen, expLag - 3000, expLag + 3000);
            const double got = 1000.0 * lag / fs;
            report (std::fabs (got - c.ms) <= 15.0,
                    "T3 delay eco FACTOR",
                    juce::String ("x") + juce::String (c.factor, 1) + " -> " +
                    juce::String (got, 1) + " ms (atteso ~" + juce::String (c.ms, 0) + ")");
        }
    }

    // --- T4: BYPASS ---
    {
        resetDefaults();
        for (auto* p : proc->getParameters())
            if (auto* w = dynamic_cast<juce::AudioProcessorParameterWithID*> (p))
                if (w->getParameterID() == "BYPASS")
                    p->setValueNotifyingHost (1.0f);

        juce::AudioBuffer<float> in (2, total), out (2, total);
        fillNoise (in, nStart, nLen, rmsIn, 99u);
        copyInToOut (in, out);
        processAll (out, 512);

        bool same = true;
        for (int ch = 0; ch < 2; ++ch)
        {
            const float* a = in.getReadPointer (ch);
            const float* b = out.getReadPointer (ch);
            for (int i = 0; i < total; ++i)
                if (a[i] != b[i])
                {
                    same = false;
                    break;
                }
        }

        report (same, "T4 BYPASS out == in (bit-identico)");
        resetDefaults();
    }

    // --- T5: mono ---
    {
        juce::AudioBuffer<float> in (1, total), out (1, total);
        fillNoise (in, nStart, nLen, rmsIn, 5u);
        copyInToOut (in, out);
        processAll (out, 512);

        const float o = rmsAll (out);
        report (o > 0.01f, "T5 mono (1 canale)",
                juce::String ("RMS=" + juce::String (o, 4)));
    }

    // --- T6: block da 64 campioni ---
    {
        juce::AudioBuffer<float> in (2, total), out (2, total);
        fillNoise (in, nStart, nLen, rmsIn, 11u);
        copyInToOut (in, out);
        processAll (out, 64);

        const float o = rmsAll (out);
        report (o > 0.01f, "T6 block 64 campioni (stile host)",
                juce::String ("RMS=" + juce::String (o, 4)));
    }

    // --- T8: 44.1 kHz (sample rate host) ---
    {
        proc->prepareToPlay (44100.0, 512);
        const double fs2 = 44100.0;
        const int total2  = static_cast<int> (1.6 * fs2);
        const int nStart2 = static_cast<int> (0.3 * fs2);
        const int nLen2   = static_cast<int> (0.2 * fs2);

        resetDefaults();
        juce::AudioBuffer<float> in (2, total2), out (2, total2);
        fillNoise (in, nStart2, nLen2, rmsIn, 31u);
        copyInToOut (in, out);
        processAll (out, 512);

        float peak = 0.0f;
        for (int ch = 0; ch < 2; ++ch)
        {
            const float* d = out.getReadPointer (ch);
            for (int i = 0; i < total2; ++i)
                peak = std::max (peak, std::fabs (d[i]));
        }

        const float o = rmsAll (out);
        const int expLag = static_cast<int> (std::lround (528.0 * fs2 / 1000.0));
        const int lag = echoLag (in.getReadPointer (0), out.getReadPointer (0), total2,
                                 nStart2, nLen2, expLag - 3000, expLag + 3000);
        const double ms = 1000.0 * lag / fs2;
        report (o > 0.01f && peak < 0.999f, "T8 44.1 kHz (sample rate host)",
                juce::String ("RMS=" + juce::String (o, 4)
                              + " peak=" + juce::String (peak, 4)));
        report (std::fabs (ms - 528.0) <= 15.0, "T8 delay eco 44.1 kHz",
                juce::String (ms, 1) + " ms (atteso ~528)");

        proc->prepareToPlay (48000.0, 512);
    }

    // --- T9-T13: feedback audio (13c) ---
    // Tono 1 kHz -20 dBFS, burst 20 ms, RANGE 64 ms x FACTOR 1.0 (D = 64 ms).
    // out = MIX = dry + wet*DELAY_LEVEL*MIX; il dry si rimuove con out - g*in.
    {
        const double fs3 = 48000.0;
        const int total3  = static_cast<int> (1.8 * fs3);
        const int nStart3 = static_cast<int> (0.25 * fs3);
        const int nLen3   = static_cast<int> (0.02 * fs3);
        const int maxK = 22;

        juce::AudioBuffer<float> outFb (2, total3);

        auto runFb = [&](float fb, int& cnt, double& dMs, float& ratio,
                         float& peak)
        {
            resetDefaults();
            setParam (*proc, "RANGE", 4.0f);      // idx 4 = 64 ms (scala 1,8,...,512)
            setParam (*proc, "FEEDBACK", fb);

            juce::AudioBuffer<float> in (2, total3);
            for (int ch = 0; ch < 2; ++ch)
            {
                float* d = in.getWritePointer (ch);
                std::fill (d, d + total3, 0.0f);
                const int fade = std::min (256, nLen3 / 2);
                for (int i = nStart3; i < nStart3 + nLen3; ++i)
                {
                    const float t = static_cast<float> (i - nStart3) / fs3;
                    float amp = 0.1f;
                    const int rel = i - nStart3;
                    if (rel < fade)
                        amp *= static_cast<float> (rel + 1) / fade;
                    else if (rel >= nLen3 - fade)
                        amp *= static_cast<float> (nLen3 - rel) / fade;
                    d[i] = amp * std::sin (2.0 * juce::MathConstants<double>::pi
                                           * 1000.0 * t);
                }
            }
            copyInToOut (in, outFb);
            processAll (outFb, 512);

            peak = 0.0f;
            for (int ch = 0; ch < 2; ++ch)
            {
                const float* d = outFb.getReadPointer (ch);
                for (int i = 0; i < total3; ++i)
                    peak = std::max (peak, std::fabs (d[i]));
            }
            cnt = countEchoes (in.getReadPointer (0), outFb.getReadPointer (0),
                               total3, fs3, nStart3, nLen3, 64.0, maxK,
                               &dMs, &ratio);
        };

        int cnt = 0;
        double dMs = 0.0;
        float ratio = 0.0f, peak = 0.0f;

        runFb (0.00f, cnt, dMs, ratio, peak);
        report (cnt == 1, "T9 FB=0: un'unica ripetizione",
                juce::String ("eco=" + juce::String (static_cast<double> (cnt), 0)
                              + " D=" + juce::String (dMs, 1) + "ms"));

        runFb (0.25f, cnt, dMs, ratio, peak);
        report (cnt >= 2 && cnt <= 3, "T10 FB=0.25: 2-3 ripetizioni",
                juce::String ("eco=" + juce::String (static_cast<double> (cnt), 0)
                              + " D=" + juce::String (dMs, 1) + "ms"));

        runFb (0.50f, cnt, dMs, ratio, peak);
        report (cnt >= 5 && cnt <= 10, "T11 FB=0.50: 5-10 ripetizioni",
                juce::String ("eco=" + juce::String (static_cast<double> (cnt), 0)
                              + " D=" + juce::String (dMs, 1) + "ms"));

        runFb (0.75f, cnt, dMs, ratio, peak);
        report (cnt >= 12 && cnt <= 25, "T12 FB=0.75: 15-30 ripetizioni",
                juce::String ("eco=" + juce::String (static_cast<double> (cnt), 0)
                              + " D=" + juce::String (dMs, 1) + "ms"));

        runFb (1.00f, cnt, dMs, ratio, peak);
        report (cnt >= 15 && ratio <= 0.5f && peak < 0.999f,
                "T13 FB=1.00: decadimento lento, no runaway",
                juce::String ("eco=" + juce::String (static_cast<double> (cnt), 0)
                              + " ultimo/1o=" + juce::String (ratio * 100.0, 1)
                              + "%" + " peak=" + juce::String (peak, 4)));
    }

    // --- T7: state save/recall ---
    {
        resetDefaults();
        setFactor (1.5f);
        for (auto* p : proc->getParameters())
            if (auto* w = dynamic_cast<juce::AudioProcessorParameterWithID*> (p))
            {
                if (w->getParameterID() == "RANGE")
                    p->setValueNotifyingHost (2.0f / 7.0f);   // idx 2/7 = 16 ms
                else if (w->getParameterID() == "MIX")
                    p->setValueNotifyingHost (0.3f);
            }

        juce::MemoryBlock blob;
        proc->getStateInformation (blob);

        juce::AudioProcessor* proc2 = createPluginFilter();
        proc2->setStateInformation (blob.getData(), static_cast<int> (blob.getSize()));

        const float f2 = denorm (*proc2, "FACTOR");
        const float r2 = denorm (*proc2, "RANGE");
        const float m2 = denorm (*proc2, "MIX");
        const bool ok = std::fabs (f2 - 1.5f) < 1.0e-3f
                      && std::fabs (r2 - 2.0f) < 1.0e-3f
                     && std::fabs (m2 - 0.3f) < 1.0e-3f;
        report (ok, "T7 state save/recall",
                juce::String ("FACTOR=" + juce::String (f2, 2)
                              + " RANGE=" + juce::String (r2, 1)
                              + " MIX=" + juce::String (m2, 2)));
        delete proc2;
    }

    delete proc;

    std::printf (g_fail == 0 ? "\nsmoke: TUTTI I TEST PASS\n"
                             : "\nsmoke: %d FALLITI\n", g_fail);
    return g_fail == 0 ? 0 : 1;
}

