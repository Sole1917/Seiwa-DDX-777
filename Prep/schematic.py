# Seiwa Digital Delay DDX-777 — schema a blocchi (F5)
# Genera schematic.png da Pillow. Font >= 14px, margini >= 100px,
# legenda C/P/I in basso a destra.
import math

from PIL import Image, ImageDraw, ImageFont

W, H = 2600, 1800
M = 100  # margine
RIGHT = W - M - 4   # 2496: rispetta margine dx >= 100 px

F = r"C:\Windows\Fonts\arial.ttf"
FB = r"C:\Windows\Fonts\arialbd.ttf"

f_title = ImageFont.truetype(FB, 40)
f_sub = ImageFont.truetype(F, 17)
f_sec = ImageFont.truetype(FB, 22)
f_bt = ImageFont.truetype(FB, 16)   # titolo box
f_bb = ImageFont.truetype(F, 15)    # corpo box
f_sm = ImageFont.truetype(F, 14)    # note piccole
f_lg_t = ImageFont.truetype(FB, 20)
f_lg = ImageFont.truetype(F, 17)

GRAY = (60, 60, 60)
DARK = (35, 35, 35)
RED = (190, 30, 30)
GRN = (40, 130, 80)
ORG = (190, 120, 30)

SEC = {
    "psu": ((235, 242, 250), (70, 110, 160), (30, 60, 110)),
    "sig": ((233, 246, 236), GRN, (20, 90, 55)),
    "clk": ((253, 242, 229), ORG, (150, 90, 15)),
    "ctl": ((243, 235, 250), (130, 80, 180), (90, 50, 140)),
}

img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)


def section(x, y, w, h, title, kind):
    fill, border, tcol = SEC[kind]
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=fill, outline=border, width=3)
    d.text((x + 16, y + 12), title, font=f_sec, fill=tcol)


def box(x, y, w, h, title, lines=(), border=GRAY, tcol=DARK, tfont=f_bt, bodyfont=f_bb):
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill="white", outline=border, width=2)
    d.text((x + 10, y + 8), title, font=tfont, fill=tcol)
    ty = y + 8 + tfont.size + 6
    for ln in lines:
        d.text((x + 10, ty), ln, font=bodyfont, fill=DARK)
        ty += bodyfont.size + 4


def arrow(x1, y1, x2, y2, color=GRAY, width=3, head=13):
    ang = math.atan2(y2 - y1, x2 - x1)
    d.line([x1, y1, x2, y2], fill=color, width=width)
    a1 = ang - math.pi / 6
    a2 = ang + math.pi / 6
    d.polygon([(x2, y2),
               (x2 - head * math.cos(a1), y2 - head * math.sin(a1)),
               (x2 - head * math.cos(a2), y2 - head * math.sin(a2))], fill=color)


def dashed(pts, color=GRAY, width=2, seg=14, gap=10):
    """Polyline tratteggiata: pts = [(x, y), ...]"""
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        length = math.hypot(x2 - x1, y2 - y1)
        if length == 0:
            continue
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        t = 0.0
        while t < length:
            t2 = min(t + seg, length)
            d.line([x1 + ux * t, y1 + uy * t, x1 + ux * t2, y1 + uy * t2],
                   fill=color, width=width)
            t = t2 + gap


def label(x, y, text, font=f_sm, fill=GRAY):
    d.text((x, y), text, font=font, fill=fill)


# ---------------------------------------------------------------- header
d.text((M, 100), "SEIWA DIGITAL DELAY DDX-777 — Schema a blocchi", font=f_title, fill=DARK)
d.text((M, 154), "Tokyo Trading Co., ser. 006242 · reverse engineering documentale da 98 foto (F5) · "
                 "Ref provvisorie: nessun designator in serigrafia · lit. it.", font=f_sub, fill=GRAY)

# ================================================================ 1 PSU
sec_y = 190
section(M, sec_y, RIGHT - M, 330, "1 · ALIMENTAZIONE", "psu")
cy = sec_y + 60
bh = 96
w1 = [("AC 220V", ["cavo rete + guarnizione"], 165),
      ("Fusibile 5×20", ["rating → L2"], 175),
      ("Sezionatore NOBLE", ["rocker POWER frontale"], 235),
      ("Filtro EMI A91S2", ["+ cap X2 2,2 nF"], 225),
      ("Trasformatore EI", ["stemma → L3"], 190),
      ("Rettifica [I]", ["diodi non identificati"], 215),
      ("Nodo 7,4 V", ["mis. utente"], 150)]
x, gap = M + 20, 30
centers = []
for title, lines, w in w1:
    box(x, cy, w, bh, title, lines)
    centers.append((x, w))
    x += w + gap
for i in range(len(centers) - 1):
    x0, w0 = centers[i]
    arrow(x0 + w0 + 4, cy + bh // 2, x0 + w0 + gap - 5, cy + bh // 2)

x_nodo, w_nodo = centers[-1]
x_u18 = x
box(x_u18, cy, 310, bh, "U18 — reg. +5 V DISCRETO",
    ["zener ~5,1 V + transistor", "+ C 1 µF 50 V · TO-92 [L22]"], tcol=(30, 60, 110))
x_p5 = x_u18 + 310 + gap
box(x_p5, cy, 220, bh, "+5 V digitale",
    ["mis. 4,71 / 4,90 V", "→ U1-U3, U5 [C]"], tcol=(20, 90, 55), border=GRN)
arrow(x_nodo + w_nodo + 4, cy + bh // 2, x_u18 - 5, cy + bh // 2)
arrow(x_u18 + 310 + 4, cy + bh // 2, x_p5 - 5, cy + bh // 2)

# ramo +15 V dal nodo 7,4 V
cy2 = cy + bh + 34
xn = x_nodo + w_nodo // 2
dashed([(xn, cy + bh), (xn, cy2 + 42)])
x_u17 = xn - 300
x_p15 = x_u17 - 240 - 30
box(x_u17, cy2, 240, 84, "U17 AN7815", ["reg. fisso +15 V (TO-220)"], tcol=(30, 60, 110))
box(x_p15, cy2, 240, 84, "+15 V analogico", ["→ U7-U9, U11-U16 [C]"],
    tcol=(20, 90, 55), border=GRN)
arrow(xn, cy2 + 42, x_u17 + 244, cy2 + 42, color=SEC["psu"][1])
arrow(x_u17 - 4, cy2 + 42, x_p15 + 244, cy2 + 42)
label(xn + 34, cy2 + 4, "−15 V ASSENTE: nessun 79xx in 83 foto [C → L15/L16]", fill=RED)
label(xn + 34, cy2 + 32, "Bias mid-rail ~7,5 V: partitore + buffer [I → L16]")
label(xn + 34, cy2 + 60, "IND1 (prov.): ALN 252F ~2,5 mH, filtro [→ L10]")

# ================================================================ 2 CATENA
sec_y = 540
section(M, sec_y, RIGHT - M, 400, "2 · CATENA SEGNALE — catena corretta [C-utente]", "sig")
cy = sec_y + 56
bh = 92
chain = [("INPUT 1/4\"", ["−20 dB (frontale)"], 165),
         ("LEVEL pot", ["M50kΩB [C]"], 150),
         ("Buffer U9 M5221", ["+ Q1 2SK118 [P]"], 235),
         ("U7 NE571", ["compressore [C]"], 190),
         ("Zona campionamento", ["L1 ALN 252F + C5 27nF", "commutazione/S&H? [P]"], 188),
         ("Filtro anti-aliasing", ["[I] — test A: 0 bip"], 190),
         ("U4 M60351", ["ADC 12 bit [C-misure]"], 164),
         ("DRAM U1-U3", ["192 Kbit [C]"], 140),
         ("U4 M60351", ["DAC 12 bit integrato [C]"], 195),
         ("senza expandore", ["ch. 2 spento → L17"], 165),
         ("DELAY LEVEL", ["M50kΩB [C]"], 150),
         ("MIX OUT", ["1/4\""], 125)]
x, gap = M + 20, 28
xs_chain = []
for title, lines, w in chain:
    box(x, cy, w, bh, title, lines)
    xs_chain.append((x, w))
    x += w + gap
for i in range(len(xs_chain) - 1):
    x0, w0 = xs_chain[i]
    arrow(x0 + w0 + 3, cy + bh // 2, x0 + w0 + gap - 4, cy + bh // 2)

rowb = cy + bh + 44
rowb_mid = rowb + 42

# DIRECT: presa dopo il LEVEL pot
lvl_x = xs_chain[1][0] + xs_chain[1][1] // 2
box(M + 20, rowb, 240, 84, "DIRECT OUT 1/4\"", ["dry separato [P]"], tcol=(20, 90, 55))
dashed([(lvl_x, cy + bh), (lvl_x, rowb_mid)])
arrow(lvl_x, rowb_mid, M + 20 + 244, rowb_mid)

# FEEDBACK: reostato di bias DC (VCC ↔ NE571 pin 4) — NON nel percorso audio [L17]
fb_x, fb_w = 750, 330
box(fb_x, rowb, fb_w, 84, "FEEDBACK LEVEL M50kΩB",
    ["reostato bias DC: VCC ↔ NE571 pin 4 [L17 RISOLTA]"])
dl_x = xs_chain[10][0] + xs_chain[10][1] // 2
dashed([(dl_x, cy + bh), (dl_x, rowb_mid)])
u6_x, u6_w = 1130, 250
box(u6_x, rowb, u6_w, 84, "U6 HD14066", ["routing/bypass/hold [P]"])
arrow(dl_x, rowb_mid, u6_x + u6_w + 4, rowb_mid)
comp_x = xs_chain[3][0] + xs_chain[3][1] // 2
dashed([(u6_x + 20, rowb), (u6_x + 20, cy + bh + 22), (comp_x, cy + bh + 22)])
arrow(comp_x, cy + bh + 22, comp_x, cy + bh + 3)
label(comp_x + 14, cy + bh + 26, "→ ingresso compressore [P]")

# PEAK: presa dopo il buffer, LED sul pannello
pk_x, pk_w = 400, 310
box(pk_x, rowb, pk_w, 84, "LED PEAK (front)",
    ["driver: op-amp libero U8/U9 [I → L18]", "etichetta ≠ pot \"PEAK LEVEL\""],
    border=ORG)
buf_x = xs_chain[2][0] + xs_chain[2][1] // 2
dashed([(buf_x, cy + bh), (buf_x, cy + bh + 40), (pk_x + 120, cy + bh + 40)])
arrow(pk_x + 120, cy + bh + 40, pk_x + 120, rowb - 2)

# ================================================================ 3 CLOCK
sec_y = 960
section(M, sec_y, RIGHT - M, 310, "3 · CLOCK / TIMING — scenario A confermato [C]", "clk")
cy = sec_y + 96
bh = 96
clk = [("U10 LM311N", ["VCO / osc. a rilassamento", "gruppo timing: trim 203 + C1 1000 pF [C]"], 330),
       ("U5 TC40H000P", ["quad NAND HCMOS (osc./glue)", "data code 8539H"], 285),
       ("RANGE rotary 10 pos.", ["1, 2, 4 … 512 ms [C]", "wafer retro …844"], 265),
       ("FACTOR ×0.5 / 1 / 2", ["pot o switch?", "tipo da confermare"], 255),
       ("Divisori clock [I]", [""], 190),
       ("f_camp → U4 + DRAM", ["f_camp ≈ 32 kHz → L12/L13 RISOLTE"], 300)]
x, gap = M + 20, 36
xs_clk = []
for title, lines, w in clk:
    box(x, cy, w, bh, title, [l for l in lines if l])
    xs_clk.append((x, w))
    x += w + gap
for i in range(len(xs_clk) - 1):
    x0, w0 = xs_clk[i]
    arrow(x0 + w0 + 4, cy + bh // 2, x0 + w0 + gap - 6, cy + bh // 2)

# LFO modulazione agganciata al VCO
ly = cy + bh + 24
box(M + 20, ly, 230, 62, "MOD. SPEED pot [C]", [], tfont=f_bt)
box(M + 270, ly, 230, 62, "MOD. DEPTH pot [C]", [], tfont=f_bt)
box(M + 520, ly, 300, 62, "LFO / modulazione [P]", ["modula VCO / divisori"])
arrow(M + 254, ly + 31, M + 266, ly + 31)
arrow(M + 504, ly + 31, M + 516, ly + 31)
arrow(M + 660, ly, xs_clk[0][0] + 165, cy + bh + 3, color=ORG)

# link f_camp -> DRAM (sale dalla sez.3 alla sez.2)
fc_x = xs_clk[5][0] + xs_clk[5][1] // 2
dram_x = xs_chain[7][0] + xs_chain[7][1] // 2
s2_cy, s2_bh = 596, 92
dashed([(fc_x, cy), (fc_x, 850), (dram_x, 850), (dram_x, s2_cy + s2_bh + 8)])
arrow(dram_x, s2_cy + s2_bh + 8, dram_x, s2_cy + s2_bh - 2)
label(dram_x + 14, 820, "f_camp → clock DRAM/U4 [C]", fill=(150, 90, 15))

# ================================================================ 4 REMOTO
sec_y = 1290
section(M, sec_y, RIGHT - M, 250, "4 · CONTROLLO REMOTO / PANNELLO FRONTALE", "ctl")
cy = sec_y + 56
box(M + 20, cy, 300, 92, "REMOTE ×3 (retro)", ["HOLD / MODULATION / DELAY [C]"])
box(M + 350, cy, 260, 92, "U6 HD14066 [P]", ["switching ingressi remoti"])
box(M + 640, cy, 440, 92, "destinazioni [P]",
    ["HOLD → freeze loop · MOD → LFO", "DELAY → RANGE / FACTOR"])
arrow(M + 324, cy + 46, M + 346, cy + 46)
arrow(M + 614, cy + 46, M + 636, cy + 46)
box(M + 1120, cy, 640, 170, "PANNELLO FRONTALE [C]",
    ["POWER rocker+LED (attua sez. NOBLE H.4) · HOLD rocker+LED",
     "Pot M50kΩB: PEAK LEVEL, FEEDBACK LEVEL, DELAY LEVEL,",
     "SPEED, DEPTH · FACTOR ×0.5/1/2 · RANGE rotary 10 pos.",
     "INPUT 1/4\" −20 dB · LED PEAK (≠ pot PEAK LEVEL)"], tcol=(90, 50, 140))
box(M + 1800, cy, 580, 170, "NOTE / ALIMENTAZIONE",
    ["NE571 / 4558 / M5221: single-supply +15 V [C-datasheet],",
     "bias mid-rail ~7,5 V [I → L16].  −15 V assente [C-foto].",
     "U18 = circuito discreto NON IC [C-misure utente].",
     "IND1 (prov.) = ALN 252F ~2,5 mH ipotizzato [→ L10]."], tcol=(30, 60, 110))

# ================================================================ bottom
ny = 1560
d.rounded_rectangle([M, ny, M + 1660, ny + 136], radius=10,
                    fill=(248, 248, 248), outline=GRAY, width=2)
d.text((M + 14, ny + 10), "STATO LACUNE CHIAVE", font=f_bt, fill=DARK)
d.text((M + 14, ny + 42),
       "L5/L12/L13 RISOLTE (sessione 11): 12 bit confermato (rumore −67 dBFS), f_camp ≈ 31-32 kHz (16384 word → 528 ms), banda ~15 kHz, taglio 15-16 kHz",
       font=f_sm, fill=DARK)
d.text((M + 14, ny + 66),
       "L1 RISOLTA (sessione 11): VCO LM311N — clock ~31 kHz, bias trimmer +3% (delay 66/262/528 ms su RANGE 64/256/512)",
       font=f_sm, fill=DARK)
d.text((M + 14, ny + 90),
       "L17 RISOLTA: nessun ricircolo audio — retroazione fissa 46,1 kΩ pin4↔pin6; pot FEEDBACK = bias DC VCC↔pin4 [test sessione 9]",
       font=f_sm, fill=DARK)
d.text((M + 14, ny + 114),
       "Fonti: 02_componenti_raw.md · 03_blocchi.md · 04_lacune.md · components.md · Segnali_Test/ · SEIWA_DDX-777_HANDOFF.md — Ref: U1-U18, C1-C6, R1-R7, Q1-Q2, D1-D5, IND1",
       font=f_sm, fill=GRAY)

# legenda (basso a destra)
lx = W - M - 624
d.rounded_rectangle([lx, ny, lx + 620, ny + 136], radius=10,
                    fill="white", outline=GRAY, width=3)
d.text((lx + 16, ny + 10), "LEGGENDA", font=f_lg_t, fill=DARK)
d.text((lx + 16, ny + 46), "[C]", font=f_lg, fill=(20, 120, 60))
d.text((lx + 76, ny + 46), "confermato (foto / misure)", font=f_lg, fill=DARK)
d.text((lx + 16, ny + 78), "[P]", font=f_lg, fill=(190, 110, 10))
d.text((lx + 76, ny + 78), "presunto", font=f_lg, fill=DARK)
d.text((lx + 320, ny + 78), "[I]", font=f_lg, fill=(120, 60, 170))
d.text((lx + 380, ny + 78), "ipotesi", font=f_lg, fill=DARK)
d.text((lx + 16, ny + 110), "→ segnale · ┆ deduzione · Ref = provvisorie",
       font=f_sm, fill=GRAY)

img.save(r"E:\tutto\OpenCode\Seiwa DDX-777\schematic.png")
print("OK schematic.png", img.size)
