cmake_minimum_required(VERSION 3.22)

project(SeiwaDDX777 VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(MSVC)
    add_compile_options(/utf-8)
endif()

# Pannello pixel-preciso 1000x136: su Windows JUCE 8 default a
# JUCE_WIN_PER_MONITOR_DPI_AWARE=1 fa scalare il contenuto D2D dal DPI del
# monitor dentro una finestra VST3 dimensionata a scala 1.0 -> su display con
# scaling >100% la UI risulta ingrandita e tagliata ai bordi. Forziamo
# rendering 1:1 in pixel fisici (indipendente dallo scaling del sistema).
add_compile_definitions(JUCE_WIN_PER_MONITOR_DPI_AWARE=0)

include(FetchContent)

FetchContent_Declare(
    JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 8.0.9
    GIT_SHALLOW TRUE
)

FetchContent_MakeAvailable(JUCE)

if(APPLE)
    set(DDX_FORMATS VST3 AU)
else()
    set(DDX_FORMATS VST3)
endif()

juce_add_plugin(SeiwaDDX777
    COMPANY_NAME "Sole"
    COMPANY_COPYRIGHT "© 2026 Sole"
    PRODUCT_NAME "DDX-777"
    DESCRIPTION "Emulation of Seiwa Digital Delay DDX-777 (1985)"
    PLUGIN_MANUFACTURER_CODE SOLE
    PLUGIN_CODE DDX7
    FORMATS ${DDX_FORMATS}
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE
    VST3_CATEGORIES Fx Delay
    AU_MAIN_TYPE kAudioUnitType_Effect
)

set(DDX_SOURCES
    src/PluginProcessor.cpp
    src/PluginEditor.cpp
    src/ui/ContentContainer.cpp
    src/ui/Knob.cpp
    src/ui/LedIndicator.cpp
    src/ui/RockerSwitch.cpp
    src/ui/InputJack.cpp
    src/ui/RackPanel.cpp
    src/ui/RenderedAsset.cpp
    src/ui/ResizeGrip.cpp
)

target_sources(SeiwaDDX777 PRIVATE ${DDX_SOURCES})

target_include_directories(SeiwaDDX777 PRIVATE src)

target_compile_definitions(SeiwaDDX777 PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
    JUCE_DISPLAY_SPLASH_SCREEN=0
)

target_link_libraries(SeiwaDDX777
    PRIVATE
        juce::juce_dsp
        juce::juce_audio_utils
        juce::juce_gui_extra
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)

# ---------------------------------------------------------------------------
# 15: asset renderizzati opzionali (docs/ASSET_BRIEF.md, Parte C)
# Con assets/rendered/ vuota il glob e' vuoto: nessuna risorsa BinaryData,
# DDX777_HAS_RENDERED_ASSETS=0 e build identica a 14-k (fallback procedurale).
# I PNG arrivano dall'artista 3D con i nomi di ASSET_BRIEF B.5; CONFIGURE_DEPENDS
# li incorpora al prossimo build senza toccare questo file.
# ---------------------------------------------------------------------------
file(GLOB DDX777_RENDERED_PNGS CONFIGURE_DEPENDS
     "${CMAKE_CURRENT_SOURCE_DIR}/assets/rendered/*.png")

if(DDX777_RENDERED_PNGS)
    juce_add_binary_data(DDX777_Assets SOURCES ${DDX777_RENDERED_PNGS})
    set_target_properties(DDX777_Assets PROPERTIES POSITION_INDEPENDENT_CODE TRUE)
    target_link_libraries(SeiwaDDX777 PRIVATE DDX777_Assets)
    target_compile_definitions(SeiwaDDX777 PRIVATE DDX777_HAS_RENDERED_ASSETS=1)
    list(LENGTH DDX777_RENDERED_PNGS DDX777_ASSET_COUNT)
    message(STATUS "DDX-777: ${DDX777_ASSET_COUNT} asset renderizzati in assets/rendered/ incorporati")
else()
    target_compile_definitions(SeiwaDDX777 PRIVATE DDX777_HAS_RENDERED_ASSETS=0)
    message(STATUS "DDX-777: nessun asset in assets/rendered/ -> fallback procedurale (14-k)")
endif()

# ---------------------------------------------------------------------------
# Harness offline (no JUCE): core DSP + WAV + metriche JSON
# ---------------------------------------------------------------------------
add_executable(ddx_harness tests/harness/main.cpp)
target_include_directories(ddx_harness PRIVATE src)
set_target_properties(ddx_harness PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)

# ---------------------------------------------------------------------------
# Generatore preset (5 XML APVTS in presets/)
# ---------------------------------------------------------------------------
juce_add_console_app(ddx_gen_presets)
target_sources(ddx_gen_presets PRIVATE tests/presets/main.cpp)
target_include_directories(ddx_gen_presets PRIVATE src)
target_link_libraries(ddx_gen_presets PRIVATE
    SeiwaDDX777
    juce::juce_audio_processors
    juce::juce_audio_utils
    juce::juce_gui_basics
    juce::juce_gui_extra
    juce::juce_dsp
)

# ---------------------------------------------------------------------------
# Smoke test audio headless (plugin completo: createPluginFilter + processBlock)
# ---------------------------------------------------------------------------
juce_add_console_app(ddx_smoke)
target_sources(ddx_smoke PRIVATE tests/smoke/main.cpp)
target_include_directories(ddx_smoke PRIVATE src)
target_link_libraries(ddx_smoke PRIVATE
    SeiwaDDX777
    juce::juce_audio_processors
    juce::juce_audio_utils
    juce::juce_gui_basics
    juce::juce_dsp
)

# ---------------------------------------------------------------------------
# Screenshot UI headless (PNG)
# ---------------------------------------------------------------------------
juce_add_console_app(ddx_screenshot)
target_sources(ddx_screenshot PRIVATE tests/screenshot/main.cpp)
target_include_directories(ddx_screenshot PRIVATE src)
# Piu' JUCE_MODAL_LOOPS_PERMITTED: il tool di solo test fa girare la message
# loop con runDispatchLoopUntil() per far convergere il fade del neon stereo.
target_compile_definitions(ddx_screenshot PRIVATE JUCE_MODAL_LOOPS_PERMITTED=1)
target_link_libraries(ddx_screenshot PRIVATE
    SeiwaDDX777
    juce::juce_audio_processors
    juce::juce_audio_utils
    juce::juce_gui_basics
    juce::juce_gui_extra
    juce::juce_dsp
)
