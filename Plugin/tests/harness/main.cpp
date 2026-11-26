// ddx_harness — renderizza il core DSP DDX-777 su un WAV in ingresso.
//
 // usage:
 //   ddx_harness <in.wav> <out.wav> [opzioni]
 // opzioni:
  //   --range <ms|idx>       1,2,4,8,16,32,64,128,256,512 (default 512) oppure indice 0-9
  //   --factor <0.5..2>      continuo, default 1
 //   --level <0..1>         PEAK LEVEL (input), default 1
 //   --feedback <0..1>      FEEDBACK LEVEL, default 0.5
 //   --delay-level <0..1>   DELAY LEVEL (wet), default 1
 //   --speed <0..1>         MODULATION SPEED, default 0
 //   --depth <0..1>         MODULATION DEPTH, default 0
 //   --trim <0.97..1.03>    trimmer clock, default 1
 //   --hold                 freeze
 //   --seed <n> --organic   abilita tolleranze organiche §12
 //   --stereo               Stereo Strategy A: downmix input a mono, coreL seed
 //                          6242 fedele (organic off) → ch0, coreR seed 6243
 //                          organico (organic on) → ch1, uscita 2 canali
 //   --json <path>          metriche debug (f_word, delay_ms, ...)
 //   --char-comp-off        disabilita compressore NE571 (caratterizzazione)
 //   --char-dist-off        disabilita distorsione d'uscita (caratterizzazione)
 //   --char-virtual-adc     abilita Virtual ADC 32 kHz (attivo di default Fase 2)
 //   --no-virtual-adc       disabilita Virtual ADC 32 kHz
 //   --k-rect <v>           modulazione gain dal rectifier NE571 (Comp 2)
 //   --k-dac2 <v>           mismatch R-2R DAC 2a armonica (Comp 3)
 //   --k-dac3 <v>           mismatch R-2R DAC 3a armonica (Comp 3)
  //   --k-buffer <v>         saturazione tanh buffer uscita (Comp 4)
  //   --k-opamp <v>          nonlinearita stadi op-amp 4558D (Comp 5)
  //   --k-vos <v>            offset VOS gain cell -> 2a armonica (Mecc. A, Sessione 12; default core 0.0079)
  //   --k-lo <v>             crossover output stage -> H3 banda < 500 Hz (Mecc. B, Sessione 12; default core 0.0)
  //   --j <v>                coefficiente quadratico JFET 2SK118 (P3; default core 0.003)
  //   --thr <v>              soglia soft-clip M5221P (P3; default core 13/15)
  //   --lim <v>              hard limit gain cell NE571 (P3; default core 0.20)
  //   --loop-scale <v>       moltiplicatore gain loop feedback (P1; default core 1.0)
  //   --bias-span <v>        span bias DC compressore in dB (P1; default core 2.0)
  //   --ffilter <file>       file con 19 numeri override filtri
 //   --emit <mix|direct|wet> output mode, default mix

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "dsp/DDX777Core.h"
#include "WavIO.h"

namespace
{

struct Arg
{
    std::string in, out, json;
    std::string emit = "mix"; // mix | direct | wet
    std::string ffilter;      // file con 19 numeri (override filtri sweep)
    bool stereo = false;
    bool charCompOff = false;
    bool charDistOff = false;
    bool virtualAdc = false;
    bool noVirtualAdc = false;
    // Coefficienti Fase 2 (-1 = flag assente: mantieni default calibrati del core)
    double kRect = -1.0, kdac2 = -1.0, kdac3 = -1.0, kBuffer = -1.0, kOpAmp = -1.0;
    // Meccanismi Sessione 12 (stesso schema sentinela)
    double kVos = -1.0, kLo = -1.0;
    // P3/P1 Sessione 13c (stesso schema sentinela)
    double kjfet = -1.0, thrM5221 = -1.0, limNE571 = -1.0;
    double loopScale = -1.0, biasSpan = -1.0;
    ddx::Params p;
};

bool parseArgs (int argc, char** argv, Arg& a, std::string& err)
{
    if (argc < 3) { err = "usage: ddx_harness <in.wav> <out.wav> [options]"; return false; }
    a.in = argv[1];
    a.out = argv[2];

    auto need = [&](int i) -> const char* {
        if (i >= argc) { err = "valore mancante per " + std::string (argv[i - 1]); return nullptr; }
        return argv[i];
    };

    for (int i = 3; i < argc; ++i)
    {
        const std::string k = argv[i];
        if (k == "--hold") { a.p.hold = true; continue; }
        if (k == "--organic") { a.p.organic = true; continue; }
        if (k == "--stereo") { a.stereo = true; continue; }
        if (k == "--dither") { a.p.dither = true; continue; }
        if (k == "--char-comp-off") { a.charCompOff = true; continue; }
        if (k == "--char-dist-off") { a.charDistOff = true; continue; }
        if (k == "--char-virtual-adc") { a.virtualAdc = true; continue; }
        if (k == "--no-virtual-adc") { a.noVirtualAdc = true; continue; }

        if (k == "--k-rect" || k == "--k-dac2" || k == "--k-dac3" ||
            k == "--k-buffer" || k == "--k-opamp" ||
            k == "--k-vos" || k == "--k-lo")
        {
            const char* v = need (i + 1);
            if (v == nullptr) return false;
            const double dv = std::atof (v);
            ++i;
            if (k == "--k-rect") a.kRect = dv;
            else if (k == "--k-dac2") a.kdac2 = dv;
            else if (k == "--k-dac3") a.kdac3 = dv;
            else if (k == "--k-buffer") a.kBuffer = dv;
            else if (k == "--k-opamp") a.kOpAmp = dv;
            else if (k == "--k-vos") a.kVos = dv;
            else a.kLo = dv;
            continue;
        }

        if (k == "--j" || k == "--thr" || k == "--lim" ||
            k == "--loop-scale" || k == "--bias-span")
        {
            const char* v = need (i + 1);
            if (v == nullptr) return false;
            const double dv = std::atof (v);
            ++i;
            if (k == "--j") a.kjfet = dv;
            else if (k == "--thr") a.thrM5221 = dv;
            else if (k == "--lim") a.limNE571 = dv;
            else if (k == "--loop-scale") a.loopScale = dv;
            else a.biasSpan = dv;
            continue;
        }

        const char* v = need (i + 1);
        if (v == nullptr) return false;
        ++i;

        if (k == "--range")
        {
            const int val = std::atoi (v);
            int idx = -1;
            for (int r = 0; r < 10; ++r)
                if (ddx::kRangeMs[r] == val) { idx = r; break; }
            if (idx < 0 && val >= 0 && val <= 9) idx = val;
            if (idx < 0) { err = "range non valido (1,2,4,8,16,32,64,128,256,512, o indice 0-9)"; return false; }
            a.p.rangeIdx = idx;
        }
        else if (k == "--factor")
        {
            a.p.factor = std::clamp ((float) std::atof (v), 0.5f, 2.0f);
        }
        else if (k == "--level")        a.p.inputLevel = (float) std::atof (v);
        else if (k == "--feedback")     a.p.feedback = (float) std::atof (v);
        else if (k == "--delay-level")  a.p.delayLevel = (float) std::atof (v);
        else if (k == "--speed")        a.p.speed = (float) std::atof (v);
        else if (k == "--depth")        a.p.depth = (float) std::atof (v);
        else if (k == "--trim")         a.p.trim = (float) std::atof (v);
        else if (k == "--seed")         a.p.seed = (uint32_t) std::atoi (v);
        else if (k == "--hiss")         a.p.hissMul = (float) std::atof (v);
        else if (k == "--json")         a.json = v;
        else if (k == "--ffilter")      a.ffilter = v;
        else if (k == "--emit")
        {
            a.emit = v;
            if (a.emit != "mix" && a.emit != "direct" && a.emit != "wet")
            { err = "--emit deve essere mix|direct|wet"; return false; }
        }
        else { err = "opzione sconosciuta: " + k; return false; }
    }
    return true;
}

} // namespace

int main (int argc, char** argv)
{
    Arg a;
    std::string err;

    if (! parseArgs (argc, argv, a, err))
    {
        std::fprintf (stderr, "errore: %s\n", err.c_str());
        return 2;
    }

    wavio::Wav in;
    if (! wavio::readWav (a.in, in, err))
    {
        std::fprintf (stderr, "errore lettura: %s\n", err.c_str());
        return 1;
    }

    // ---- Configurazione core ----
    std::vector<ddx::DDX777Core> cores;
    std::vector<float> mono; // downmix condiviso (solo --stereo)

    if (a.stereo)
    {
        // Stereo Strategy A: input downmixato a mono, due core con seed diversi.
        // coreL fedele (seed 6242, organic off), coreR organico (seed 6243, on).
        struct { uint32_t seed; bool organic; } cfg[2] = { { 6242u, false }, { 6243u, true } };
        cores.resize (2);
        for (int c = 0; c < 2; ++c)
        {
            ddx::Params p = a.p;
            p.seed = cfg[c].seed;
            p.organic = cfg[c].organic;
            cores[c].prepare (in.fs);
            cores[c].setParams (p);
        }
        mono.assign (in.frames, 0.0f);
        const int nch = in.channels > 0 ? in.channels : 1;
        for (size_t i = 0; i < in.frames; ++i)
        {
            float s = 0.0f;
            for (int c = 0; c < nch; ++c) s += in.ch[c][i];
            mono[i] = s / (float) nch;
        }
    }
    else
    {
        // un core per canale (stereo organico §12: seed diverso per canale)
        cores.resize ((size_t) in.channels);
        for (size_t c = 0; c < cores.size(); ++c)
        {
            ddx::Params p = a.p;
            if (p.organic) p.seed = a.p.seed + (uint32_t) c;
            cores[c].prepare (in.fs);
            cores[c].setParams (p);
        }
    }

    // override filtri (sweep di calibrazione): file con 19 numeri
    double ov[19];
    bool haveOv = false;
    if (! a.ffilter.empty())
    {
        std::FILE* f = std::fopen (a.ffilter.c_str(), "r");
        if (f)
        {
            int n = 0;
            while (n < 19 && std::fscanf (f, "%lf", &ov[n]) == 1) ++n;
            haveOv = (n == 19);
            std::fclose (f);
        }
        if (! haveOv)
        {
            std::fprintf (stderr, "errore: --ffilter richiede 19 numeri\n");
            return 2;
        }
        for (size_t c = 0; c < cores.size(); ++c)
            cores[c].overrideFilters (ov);
    }

    // Flag caratterizzazione THD
    if (a.charCompOff)
        for (size_t c = 0; c < cores.size(); ++c)
            cores[c].setCharCompOff (true);
    if (a.charDistOff)
        for (size_t c = 0; c < cores.size(); ++c)
            cores[c].setCharDistOff (true);
    if (a.virtualAdc && ! a.noVirtualAdc)
        for (size_t c = 0; c < cores.size(); ++c)
            cores[c].setVirtualAdc (true);
    if (a.noVirtualAdc)
        for (size_t c = 0; c < cores.size(); ++c)
            cores[c].setVirtualAdc (false);

    // Coefficienti Fase 2 (-1 = flag assente: mantieni default calibrati del core)
    for (size_t c = 0; c < cores.size(); ++c)
    {
        if (a.kRect >= 0.0)     cores[c].setKRect (a.kRect);
        if (a.kdac2 >= 0.0)     cores[c].setKdac2 (a.kdac2);
        if (a.kdac3 >= 0.0)     cores[c].setKdac3 (a.kdac3);
        if (a.kBuffer >= 0.0)   cores[c].setKbuffer (a.kBuffer);
        if (a.kOpAmp >= 0.0)    cores[c].setKopamp (a.kOpAmp);
        if (a.kVos >= 0.0)     cores[c].setKVos (a.kVos);
        if (a.kLo >= 0.0)      cores[c].setKLo (a.kLo);
        // P3/P1 Sessione 13c
        if (a.kjfet >= 0.0)      cores[c].setKjfet (a.kjfet);
        if (a.thrM5221 > 0.0)    cores[c].setThrM5221 (a.thrM5221);
        if (a.limNE571 > 0.0)    cores[c].setLimNE571 (a.limNE571);
        if (a.loopScale >= 0.0)  cores[c].setLoopScale (a.loopScale);
        if (a.biasSpan >= 0.0)   cores[c].setBiasSpan (a.biasSpan);
    }

    wavio::Wav out;
    out.fs = in.fs;
    out.channels = a.stereo ? 2 : in.channels;
    out.frames = in.frames;
    out.ch.assign ((size_t) out.channels, std::vector<float> (in.frames));

    const int block = 512;
    std::vector<float> mix ((size_t) block), direct ((size_t) block), wet ((size_t) block);

    for (size_t c = 0; c < cores.size(); ++c)
    {
        auto& core = cores[c];
        const float* src = a.stereo ? mono.data() : in.ch[c].data();
        auto& dst = out.ch[c];

        for (size_t i = 0; i < in.frames; i += (size_t) block)
        {
            const int n = (int) std::min ((size_t) block, in.frames - i);
            core.process (src + i, mix.data(), direct.data(), n, wet.data());

            const std::vector<float>* which = &mix;
            if (a.emit == "direct") which = &direct;
            else if (a.emit == "wet") which = &wet;

            for (int j = 0; j < n; ++j)
                dst[i + (size_t) j] = (*which)[(size_t) j];
        }
    }

    if (! wavio::writeFloat32 (a.out, out, err))
    {
        std::fprintf (stderr, "errore scrittura: %s\n", err.c_str());
        return 1;
    }

    // statistiche di picco
    float peak = 0.0f;
    for (const auto& chn : out.ch)
        for (float v : chn)
            if (std::fabs (v) > peak) peak = std::fabs (v);

    const auto& c0 = cores[0];
    std::fprintf (stderr,
                   "ddx_harness: fs=%.0f ch=%d frames=%zu range=%dms factor=%.2f "
                   "f_word=%.1fHz delay=%.2fms peak=%.3f\n",
                   in.fs, in.channels, in.frames,
                   ddx::kRangeMs[a.p.rangeIdx], a.p.factor,
                   c0.clockHz(), c0.delayMs(), peak);

    if (! a.json.empty())
    {
        std::FILE* jf = std::fopen (a.json.c_str(), "wb");
        if (jf != nullptr)
        {
            std::fprintf (jf,
                          "{\n"
                          "  \"sample_rate\": %.1f,\n"
                          "  \"channels\": %d,\n"
                          "  \"frames\": %zu,\n"
                          "  \"range_ms\": %d,\n"
                          "  \"factor\": %.2f,\n"
                          "  \"f_word_hz\": %.4f,\n"
                          "  \"delay_ms\": %.4f,\n"
                          "  \"delay_words\": %.4f,\n"
                          "  \"trim\": %.4f,\n"
                          "  \"peak\": %.6f\n"
                          "}\n",
                           in.fs, in.channels, in.frames,
                           ddx::kRangeMs[a.p.rangeIdx], a.p.factor,
                           c0.clockHz(), c0.delayMs(), c0.delayWords(),
                          a.p.trim, peak);
            std::fclose (jf);
        }
    }

    return 0;
}
