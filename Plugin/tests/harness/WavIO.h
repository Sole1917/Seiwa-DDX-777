#pragma once

// I/O WAV minimale per l'harness: legge PCM 16/24/32 bit e IEEE float 32/64,
// scrive IEEE float 32 bit. Nessuna dipendenza esterna.

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

namespace wavio
{

struct Wav
{
    double fs = 48000.0;
    int channels = 0;
    std::vector<std::vector<float>> ch; // ch[c][i]
    size_t frames = 0;
};

inline bool readWav (const std::string& path, Wav& w, std::string& err)
{
    std::FILE* f = std::fopen (path.c_str(), "rb");
    if (f == nullptr) { err = "apertura fallita: " + path; return false; }

    auto rd32 = [&]() -> uint32_t {
        uint8_t b[4] = {};
        if (std::fread (b, 1, 4, f) != 4) return 0;
        return (uint32_t) b[0] | ((uint32_t) b[1] << 8) | ((uint32_t) b[2] << 16) | ((uint32_t) b[3] << 24);
    };
    auto rd16 = [&]() -> uint16_t {
        uint8_t b[2] = {};
        if (std::fread (b, 1, 2, f) != 2) return 0;
        return (uint16_t) ((uint32_t) b[0] | ((uint32_t) b[1] << 8));
    };

    char riff[4];
    if (std::fread (riff, 1, 4, f) != 4 || std::memcmp (riff, "RIFF", 4) != 0)
    { err = "non è un file RIFF"; std::fclose (f); return false; }
    rd32();
    char wave[4];
    if (std::fread (wave, 1, 4, f) != 4 || std::memcmp (wave, "WAVE", 4) != 0)
    { err = "non è un file WAVE"; std::fclose (f); return false; }

    uint16_t format = 0, bits = 0;
    int channels = 0;
    double fs = 0;
    std::vector<uint8_t> data;

    while (true)
    {
        char id[4];
        if (std::fread (id, 1, 4, f) != 4) break;
        const uint32_t size = rd32();

        if (std::memcmp (id, "fmt ", 4) == 0)
        {
            format = rd16();
            channels = rd16();
            fs = (double) rd32();
            rd32(); // byte rate
            rd16(); // block align
            bits = rd16();
            if (size > 16) std::fseek (f, size - 16, SEEK_CUR);
        }
        else if (std::memcmp (id, "data", 4) == 0)
        {
            data.resize (size);
            if (std::fread (data.data(), 1, size, f) != size)
            { err = "data troncati"; std::fclose (f); return false; }
        }
        else
        {
            std::fseek (f, size + (size & 1), SEEK_CUR);
        }
    }
    std::fclose (f);

    if (channels <= 0 || fs <= 0.0 || data.empty())
    { err = "fmt/data mancanti"; return false; }

    const int bytesPer = bits / 8;
    if (bytesPer <= 0 || (int) data.size() < bytesPer * channels)
    { err = "bits non supportati"; return false; }

    const size_t frames = data.size() / (size_t) (bytesPer * channels);
    w.fs = fs;
    w.channels = channels;
    w.frames = frames;
    w.ch.assign ((size_t) channels, std::vector<float> (frames));

    const uint8_t* p = data.data();
    for (size_t i = 0; i < frames; ++i)
    {
        for (int c = 0; c < channels; ++c)
        {
            float v = 0.0f;
            const uint8_t* q = p + (size_t) (i * channels + c) * (size_t) bytesPer;
            if (format == 3 && bits == 32)      { float fv;    std::memcpy (&fv, q, 4); v = fv; }
            else if (format == 3 && bits == 64) { double dv;   std::memcpy (&dv, q, 8); v = (float) dv; }
            else if (format == 1 && bits == 16) { int16_t s;   std::memcpy (&s, q, 2); v = s / 32768.0f; }
            else if (format == 1 && bits == 24)
            {
                int32_t s = (int32_t) ((uint32_t) q[0] | ((uint32_t) q[1] << 8) | ((uint32_t) q[2] << 16));
                if (s & 0x800000) s |= ~0xFFFFFF;
                v = (float) (s / 8388608.0);
            }
            else if (format == 1 && bits == 32) { int32_t s;   std::memcpy (&s, q, 4); v = (float) (s / 2147483648.0); }
            else { err = "formato non supportato"; return false; }

            w.ch[(size_t) c][i] = v;
        }
    }
    return true;
}

inline bool writeFloat32 (const std::string& path, const Wav& w, std::string& err)
{
    std::FILE* f = std::fopen (path.c_str(), "wb");
    if (f == nullptr) { err = "scrittura fallita: " + path; return false; }

    const uint32_t ch = (uint32_t) w.channels;
    const uint32_t fs = (uint32_t) (w.fs + 0.5);
    const uint32_t dataBytes = (uint32_t) (w.frames * ch * 4);

    auto wr32 = [&](uint32_t v) {
        uint8_t b[4] = { (uint8_t) (v & 0xff), (uint8_t) ((v >> 8) & 0xff),
                         (uint8_t) ((v >> 16) & 0xff), (uint8_t) ((v >> 24) & 0xff) };
        std::fwrite (b, 1, 4, f);
    };
    auto wr16 = [&](uint16_t v) {
        uint8_t b[2] = { (uint8_t) (v & 0xff), (uint8_t) ((v >> 8) & 0xff) };
        std::fwrite (b, 1, 2, f);
    };

    std::fwrite ("RIFF", 1, 4, f);
    wr32 (36 + dataBytes);
    std::fwrite ("WAVE", 1, 4, f);
    std::fwrite ("fmt ", 1, 4, f);
    wr32 (16);
    wr16 (3);          // IEEE float
    wr16 ((uint16_t) ch);
    wr32 (fs);
    wr32 (fs * ch * 4);
    wr16 ((uint16_t) (ch * 4));
    wr16 (32);
    std::fwrite ("data", 1, 4, f);
    wr32 (dataBytes);

    std::vector<float> inter ((size_t) (w.frames * ch));
    for (uint32_t i = 0; i < (uint32_t) w.frames; ++i)
        for (uint32_t c = 0; c < ch; ++c)
            inter[(size_t) (i * ch + c)] = w.ch[c][i];

    if (std::fwrite (inter.data(), 4, inter.size(), f) != inter.size())
    { err = "scrittura data incompleta"; std::fclose (f); return false; }

    std::fclose (f);
    return true;
}

} // namespace wavio
