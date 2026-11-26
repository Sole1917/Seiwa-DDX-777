# DEBUG_13n â€” Changelog di sessione

Step 1 â€” Rimozione target Standalone
File: CMakeLists.txt

Righe modificate: 31, 33

Diff sintetico: `set(DDX_FORMATS VST3 AU Standalone)` / `set(DDX_FORMATS VST3 Standalone)` â†’ `set(DDX_FORMATS VST3 AU)` / `set(DDX_FORMATS VST3)`

Motivazione: build deve generare solo VST3.

Step 2 — Rimozione tick FACTOR duplicati in paint()
File: src/ui/Knob.cpp

Righe modificate: 187-195 (secondo blocco Factor)

Diff sintetico: blocco else if (style == Style::Factor) con ciclo for (i=1..11) che ridisegnava le 11 tacche -> solo drawLabel x0.5 e x2

Motivazione: bug — le 11 tacche sono gia disegnate dal primo blocco (riga 135), 22 tacche sovrapposte.

Step 3 — Rimozione dead code
File: src/dsp/DDX777Core.h

Righe modificate: 107 (rimossa), 371-378 (kFeedbackSpanDb + kWetMix con commenti), 612 (charCompOff_), 649-651 (decPhase_/decOut_/intPhase_)

Diff sintetico: rimossi kWetMix=0.95f e kFeedbackSpanDb=12.0 con blocchi di commento -> rimossi; rimossi i membri charCompOff_/decPhase_/decOut_/intPhase_ -> rimossi; const float wetGain = p_.delayLevel; (riga 107) -> rimossa (ombra gia unused, resta solo wetGain = std::sin(angle) a riga ~288)

Motivazione: dead code, no impatto funzionale (grep: nessun riferimento fuori da DDX777Core.h/.bak; il commento storico a riga 118 che cita kFeedbackSpanDb resta intenzionale).

Step 4 — LFO check usa valori smoothed
File: src/dsp/DDX777Core.h

Righe modificate: 194

Diff sintetico: if (p_.depth > 1.0e-4f && p_.speed > 1.0e-4f) -> if (depthSm_ > 1.0e-4f && speedSm_ > 1.0e-4f)

Motivazione: incoerenza tra check (raw) e uso (modDepth/step derivati dai valori smoothed) — il gate LFO si apriva/chiudeva usando i parametri grezzi mentre la modulazione usa speedSm_/depthSm_.

Step 5 — Correzione kWriteCrossfade (0.1 -> ~0.001)
File: src/dsp/DDX777Core.h

Righe modificate: 617

Diff sintetico: static constexpr float kWriteCrossfade = 0.1f; -> static constexpr float kWriteCrossfade = 1.0f / (0.010f * 96000.0f); (commento ~10 ms @ 96 kHz invariato)

Motivazione: bug — 0.1f e' coefficiente one-pole con tau = 10 campioni = 0.1 ms @ 96 kHz, non 10 ms come diceva il commento; il nuovo valore dà tau ~= 960 campioni = 10 ms. Effetto voluto: transizione HOLD/un-HOLD piu' lenta (confermato dall'utente).

Step 6 — POWER bypass passa dry con INPUT_LEVEL applicato
File: src/PluginProcessor.cpp

Righe modificate: 138-158 (blocco if (! powered))

Diff sintetico: return; // out = in (in-place) -> costruzione makeCoreParams(), gIn = p.inputLevel, buffer.applyGain(gIn) se != 1.0, poi return

Motivazione: bug — POWER OFF lasciava il buffer a unita' mentre POWER ON applica dry = xIn * gIn (0.20 a tacca 5 = -14 dB): salto di +14 dB percepito al toggle. Ora il gain di INPUT_LEVEL resta applicato al dry anche in bypass.

Step 7 — Rimozione dipendenza juce dal core DSP
File: src/dsp/DDX777Core.h (verificati anche Params.h, Compressor.h, DelayLine.h, Filters.h, OrganicSeed.h — nessun altro riferimento juce)

Righe modificate: 292

Diff sintetico: const float angle = juce::jlimit(0.0f, 1.0f, p_.delayLevel) * juce::MathConstants<float>::halfPi; -> const float angle = std::min(1.0f, std::max(0.0f, p_.delayLevel)) * 1.57079632679f;

Motivazione: sbloccare build di ddx_harness (target standalone senza JUCE). La riga juce:: era preesistente (introdotta in 3a40c38) e rompeva la compilazione dell'harness; equivalente std numericamente identico (jlimit(0,1,x) == min/max clamp, halfPi == 1.57079632679f), nessun impatto DSP.

Step 8 — Fix smoothing modulation per-sample
File: src/dsp/DDX777Core.h

Righe: blocco process() (85-94, 103, 120, 191-198)

Diff sintetico: smoothing speedSm_/depthSm_ spostato da sopra-il-loop (una volta per blocco) a prime righe del loop per-sample; fLfo/modDepth/lfoInc ricalcolati per-sample dentro il gate LFO (prima calcolati una volta per blocco fuori dal loop)

Motivazione: coeffone dimensionato per-sample, applicato per-blocco ? tempo di assestamento reale ~500x piu' lento (~25 s invece di ~50 ms). Il gate usa gia' i valori smoothed (Step 4), ora coerente con l'uso per-sample.

Step 9-14 — Stereo Strategy A (DSP)
File: src/PluginProcessor.cpp, src/PluginProcessor.h, tests/harness/main.cpp

Modifiche: parametri STEREO_MODE (default false) e ORGANIC (default false) nel layout; makeCoreParams(uint32_t seed) con p.seed e p.organic da ORGANIC; paramsChanged esteso con organic/seed; routing processBlock con downmix (L+R)/2, coreL seed 6242 fedele (organic sempre false) / coreR seed 6243 organico (organic solo in stereo), mono fedele = solo coreL copiato su entrambi i canali; buffer di lavoro work_ (3 canali mono/outL/outR) allocato in prepareToPlay; reset coreR al toggle mono->stereo (stereoModePrev_); harness flag --stereo (downmix mono condiviso, WAV 2 canali, L=coreL fedele R=coreR organico)

Motivazione: supporto stereo con micro-variazioni organiche (secondo canale organico); mono invariato rispetto al baseline 13h.

## Step 15 — Hiss applicato all'output mix (non solo wet)
- File: src/dsp/DDX777Core.h
- Righe: process(), calcolo wOut e mo (290, 299-300, 351)
- Diff: wOut senza hiss; hiss aggiunto a mo subito dopo il mix dry/wet; tap outWet (--emit wet) mantiene il proprio draw di hiss (floor DAC, usato dai test noise verify.py)
- Motivazione: il floor analogico è presente su tutta la catena, non solo nel wet; incoerenza con misure HW (FEEDBACK_ANALYSIS_v2 §2): -77 dBFS identico su FB=0/2/10 e indipendente da DELAY_LEVEL

## Step 16-20 — GUI stereo
- File: src/ui/InputJack.h/cpp, src/ui/RackPanel.h/cpp, src/PluginEditor.cpp/h
- Modifiche: click sull'area INPUT (jack + etichetta + "-20dB") toggla STEREO_MODE via setValueNotifyingHost; cursore hand; jack dual (r=10) in stereseo, singolo (r=13) in mono; scritta "STEREO" rossa #B4281E con neon (blur gaussiano ~8px, 2 layer) sotto DDX-777; fade 300ms a 30Hz via stereoTick; bounds InputJack estesi a S(10,20,108,84)
- Motivazione: esporre STEREO_MODE in GUI secondo concept "secondo canale organico"
- Tool test: ddx_screenshot accetta argomento "stereo" (setValueNotifyingHost) e fa convergere il fade via message loop (JUCE_MODAL_LOOPS_PERMITTED=1 sul solo target); verifica pixel dei PNG renderizzati.
