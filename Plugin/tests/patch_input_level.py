#!/usr/bin/env python3
"""
Patch INPUT_LEVEL parameter in PluginProcessor.cpp
"""

with open(r'<PROJECT_ROOT>\Plugin\src\PluginProcessor.cpp', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    layout.add (std::make_unique<juce::AudioParameterFloat> (
        "INPUT_LEVEL", "INPUT_LEVEL",
        juce::NormalisableRange<float> (0.0f, 1.0f), 1.0f,
        juce::AudioParameterFloatAttributes()
            .withStringFromValueFunction ([] (float v, int) { return juce::String (v * 10.0f, 1); })));'''

new = '''    layout.add (std::make_unique<juce::AudioParameterFloat> (
        "INPUT_LEVEL", "INPUT_LEVEL",
        juce::NormalisableRange<float> (0.0f, 10.0f, 1.0f,
            // Custom mapping: 0-6 = -60 to 0 dB (10 dB/step), 6-10 = 0 to +12 dB (3 dB/step)
            [](float v) { 
                if (v <= 6.0f) return (v - 6.0f) * 10.0f;      // -60 to 0 dB
                else return (v - 6.0f) * 3.0f;                  // 0 to +12 dB
            },
            [](float db) { 
                if (db <= 0.0f) return 6.0f + db / 10.0f;       // -60 to 0 dB
                else return 6.0f + db / 3.0f;                   // 0 to +12 dB
            }),
        6.0f,  // default = unity (0 dB)
        juce::AudioParameterFloatAttributes()
            .withStringFromValueFunction ([] (float v, int) { 
                if (v <= 0.0f) return juce::String (v, 1) + " dB";
                else return juce::String ("+" + juce::String (v, 1) + " dB"); 
            }));'''

with open(r'<PROJECT_ROOT>\Plugin\src\PluginProcessor.cpp', 'r', encoding='utf-8') as f:
    content = f.read()

if old in content:
    content = content.replace(old, new)
    with open(r'<PROJECT_ROOT>\Plugin\src\PluginProcessor.cpp', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced successfully')
else:
    print('OLD TEXT NOT FOUND')
    idx = content.find('INPUT_LEVEL')
    if idx >= 0:
        print(repr(content[idx:idx+500]))
    else:
        print('INPUT_LEVEL not found')