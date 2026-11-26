#!/usr/bin/env python3
"""
Reorganize DDX777Core.h to move member variables before methods
"""
import re

with open(r'<PROJECT_ROOT>\Plugin\src\dsp\DDX777Core.h', 'r', encoding='utf-8') as f:
    content = f.read()

# Find class boundaries
class_start = content.find('class DDX777Core')
class_end_idx = content.find('};', content.find('class DDX777Core'))
class_text = content[class_start:class_end_idx + 2]

# Find the public: section
public_idx = content.find('public:', content.find('class DDX777Core'))
class_body_start = content.find('{', content.find('class DDX777Core')) + 1

# Find the first method (prepare)
first_method = content.find('void prepare')
class_body_start = content.find('{', content.find('class DDX777Core')) + 1

# Split class into: header (class declaration + public:), methods, member variables
# Find where member variables start (first line with "double fs_ = 48000.0;")
member_start_idx = content.find('double fs_ = 48000.0;', content.find('class DDX777Core'))
if member_start_idx == -1:
    print("Could not find member variable section")
    exit(1)

# Split content into: before class, class declaration + public:, methods, member variables, closing
before_class = content[:content.find('class DDX777Core')]
class_decl = content[content.find('class DDX777Core'):content.find('{', content.find('class DDX777Core')) + 1]
class_body = content[content.find('{', content.find('class DDX777Core')) + 1:content.rfind('};')]
after_class = content[content.rfind('};') + 2:]

# Split class body into methods and member variables
class_body = content[content.find('{', content.find('class DDX777Core')) + 1:content.rfind('};')]

# Find the member variable section (starts with "double fs_ = 48000.0;")
member_start = class_body.find('double fs_ = 48000.0;')
if member_start == -1:
    print("Could not find member variable section")
    exit(1)

methods_part = class_body[:member_start]
member_vars = class_body[member_start:]

# Now reconstruct: class declaration + public: + member variables + methods
new_class_body = '''public:
    // Member variables (must be declared before methods that use them)
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
    // Virtual ADC 32 kHz: downsample 96->32 (4 biquad = 8° ordine @ 15 kHz)
    Biquad dec1_, dec2_, dec3_, dec4_;
    // upsample 32->96 (4 biquad = 8° ordine @ 15 kHz)
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
    // HOLD crossfade (13i): transizione fluida 7.5 ms per evitare click
    float holdCrossfade_ = 1.0f;
    float holdCrossfadeTarget_ = 1.0f;
    bool holdPrev_ = false;
    // HOLD write enable crossfade (13i): evita click su attivazione/disattivazione HOLD
    float writeEnable_ = 1.0f;
    float writeEnableTarget_ = 1.0f;
    // Feedback gain smoothing (13i): evita click sui cambi di FEEDBACK
    float fbGainSmoothed_ = 0.0f;
    // P3 (Sessione 13c): saturazione d'ingresso -- valori fisici (datasheet):
    //   2SK118  JFET: kJfet = Vx / (2*(1-m)*|Vp|): Vx scala del nodo, m bias,
    //   vedi 03_blocchi.md s3 e report calibrazione
    double kJfet_ = 0.003;
    // M5221P dual JFET op-amp: soft limit uscita ai rail (Vom +-13 typ a +-15 V) -> tanh normalizzato
    double thrM5221_ = 13.0 / 15.0;
    double limNE571_ = 0.20;
    // P1 (Sessione 13c): feedback a reostato -- gain di loop vs pot, tabella
    double loopScale_ = 1.0;   // moltiplicatore diagnostico (calibrazione)
    double biasSpanDb_ = 2.0;  // span effettivo del bias DC sul compressore
    // Meccanismi Sessione 12 (datasheet NE570N), calibrati su T4:
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
    double m2_ = 0.0;          // stima E[dry^2] per il DC del quadrato (Mecc. A)
    // P3 (Sessione 13c): saturazione d'ingresso -- valori fisici (datasheet):
    //   2SK118  JFET: kJfet = Vx / (2*(1-m)*|Vp|): Vx scala del nodo, m bias,
    //   vedi 03_blocchi.md s3 e report calibrazione
    double kJfet_ = 0.003;
    // M5221P dual JFET op-amp: soft limit uscita ai rail (Vom +-13 typ a +-15 V) -> tanh normalizzato
    double thrM5221_ = 13.0 / 15.0;
    double limNE571_ = 0.20;
    // P1 (Sessione 13c): feedback a reostato -- gain di loop vs pot, tabella
    double loopScale_ = 1.0;   // moltiplicatore diagnostico (calibrazione)
    double biasSpanDb_ = 2.0;  // span effettivo del bias DC sul compressore

    // Methods...
'''

# Now we need to extract the methods from the original class
# and append them after the member variables

# For simplicity, let's just replace the entire class body
# This is a complex transformation, so let's do it step by step

# First, let's find the exact content we need to replace
with open(r'<PROJECT_ROOT>\Plugin\src\dsp\DDX777Core.h', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the class definition and its body
class_start_idx = content.find('class DDX777Core')
class_end_idx = content.find('};', content.find('class DDX777Core'))
class_text = content[content.find('class DDX777Core'):content.find('};', content.find('class DDX777Core')) + 2]

# Find the public: section
public_idx = content.find('public:', content.find('class DDX777Core'))
class_body_start = content.find('{', content.find('class DDX777Core')) + 1
class_body_end = content.rfind('};', content.find('class DDX777Core'))

class_body = content[content.find('{', content.find('class DDX777Core')) + 1:content.rfind('};', content.find('class DDX777Core'))]

# Find where member variables start (double fs_ = 48000.0;)
member_start_idx = content.find('double fs_ = 48000.0;', content.find('class DDX777Core'))
methods_part = content[content.find('{', content.find('class DDX777Core')) + 1:member_start_idx]
member_vars = content[member_start_idx:content.rfind('};', content.find('class DDX777Core'))]

# Reconstruct
new_class = content[:content.find('class DDX777Core')] + \
    'class DDX777Core\n{\npublic:\n' + \
    member_vars_text + '\n' + \
    methods_text + \
    '\n};' + \
    content[content.rfind('};') + 2:]

# This is getting complex. Let me write a proper script file instead.

print("Script ready to run")