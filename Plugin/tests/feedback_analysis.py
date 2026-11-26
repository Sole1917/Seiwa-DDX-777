#!/usr/bin/env python
# -*- coding: utf-8 -*-
# feedback_analysis.py — Analisi misure feedback DDX-777 (FB=2/5/10)
#
# Input (read-only):
#   Prep\Segnali_Test\Risultati\peak 10, feedback {2,5,10}, delay 10, 512 ms.wav
#   Prep\Segnali_Test\01_impulse_single.wav (riferimento spettrale d'ingresso)
# Output (cartella di questo script):
#   feedback_decay.png, feedback_g_vs_level.png, feedback_spectra_per_echo.png,
#   feedback_loop_transfer.png, feedback_noise_vs_echo.png, feedback_jitter.png,
#   feedback_results.json
#
# Condizioni note: 96 kHz, 24 bit, contenuto mono in file STEREO (L==R) -> uso L.
# Soglia -80 dBFS (direttiva utente). FACTOR=x1, MODULATION=0, HOLD=off, LEVEL=10.
#
# Note di lettura del segnale:
#   - Il picco a t~0 ms (full scale) e' il DRY/impulso d'ingresso, NON un eco.
#   - La catena di feedback parte dal primo picco ritardato (~545 ms).
#   - Gli echi affondano in un noise floor (~-77 dBFS) = quantizzazione del
#     sampler 12-bit nel loop; sotto floor+10 dB i picchi sono inaffidabili.

import os
import json
import wave
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DIR_STIM = r'<PROJECT_ROOT>\Prep\Segnali_Test'
DIR_RES = os.path.join(DIR_STIM, 'Risultati')
SR = 96000
THR_DB = -80.0
THR = 10 ** (THR_DB / 20.0)
NFFT = 32768
W_HALF_MS = 5.0
GAP_WIN_S = 0.10
MIN_GAP_S = 0.40
PEAK_MARGIN_DB = 6.0      # eco affidabile se A > (pico massimo del rumore) + 6 dB

FILES = [
    ('peak 10, feedback 10, delay 10, 512 ms.wav', 'FB10'),
    ('peak 10, feedback 5 circa, delay 10, 512 ms.wav', 'FB5'),
    ('peak 10, feedback 2 circa, delay 10, 512 ms.wav', 'FB2'),
]
COLORS = {'FB10': 'tab:blue', 'FB5': 'tab:orange', 'FB2': 'tab:green'}


def load_mono24(path):
    with wave.open(path, 'rb') as w:
        if w.getframerate() != SR:
            raise RuntimeError('SR inatteso: %d' % w.getframerate())
        if w.getsampwidth() != 3:
            raise RuntimeError('bits inattesi: %d' % (w.getsampwidth() * 8))
        n = w.getnframes()
        raw = w.readframes(n)
    b = np.frombuffer(raw, dtype=np.uint8).reshape(n, 6)
    L = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)
         | (b[:, 2].astype(np.int32) << 16))
    L = np.where(L >= 2 ** 23, L - 2 ** 24, L)
    return L.astype(np.float64) / 2 ** 23


def load_float_wav(path):
    # WAVE IEEE-float (fmt=3, 4 byte/sample) o PCM16; ritorna canale 0 float64
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:4] == b'RIFF'
    off = 12
    sr = channels = fmt = None
    while off + 8 <= len(data):
        cid = data[off:off + 4]
        sz = int.from_bytes(data[off + 4:off + 8], 'little')
        body = off + 8
        if cid == b'fmt ':
            fmt = int.from_bytes(data[body:body + 2], 'little')
            channels = int.from_bytes(data[body + 2:body + 4], 'little')
            sr = int.from_bytes(data[body + 4:body + 8], 'little')
        elif cid == b'data':
            bps = 4 if fmt == 3 else 2
            n = sz // (bps * channels)
            dt = np.float32 if fmt == 3 else np.int16
            x = np.frombuffer(data, dtype=dt, offset=body,
                              count=n * channels).reshape(-1, channels)
            x = x[:, 0].astype(np.float64)
            if fmt != 3:
                x = x / 32768.0
            return x, sr, channels, fmt
        off = body + sz + (sz & 1)
    raise RuntimeError('chunk data non trovato')


def detect_peaks(x, thr=THR, min_gap_s=MIN_GAP_S):
    env = np.abs(x)
    ds = 48
    n_ds = (len(env) // ds) * ds
    env_ds = env[:n_ds].reshape(-1, ds).max(axis=1)
    min_gap_ds = int(min_gap_s * SR / ds)
    cand = np.where(env_ds > thr)[0]
    peaks_ds = []
    for c in cand:
        if peaks_ds and (c - peaks_ds[-1]) < min_gap_ds:
            if env_ds[c] > env_ds[peaks_ds[-1]]:
                peaks_ds[-1] = c
        else:
            peaks_ds.append(c)
    w = int(0.003 * SR)
    peaks = []
    amps = []
    for p in peaks_ds:
        c = p * ds
        a = max(0, c - w)
        b = min(len(x), c + w + 1)
        m = a + int(np.argmax(env[a:b]))
        if peaks and (m - peaks[-1]) < int(min_gap_s * SR):
            if env[m] > env[peaks[-1]]:
                peaks[-1] = m
                amps[-1] = env[m]
        else:
            peaks.append(m)
            amps.append(env[m])
    return np.array(peaks, dtype=int), np.array(amps, dtype=float)


def db(a):
    return 20.0 * np.log10(np.maximum(a, 1e-12))


def hann(N):
    if N <= 2:
        return np.ones(N)
    return 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(N) / (N - 1)))


def spectrum(x, m, half_ms=W_HALF_MS, nfft=NFFT):
    h = int(half_ms * SR / 1000.0)
    seg = x[m - h:m + h]
    if seg.size != 2 * h:
        seg = seg[-2 * h:] if m >= h else x[:2 * h]
    win = hann(seg.size)
    X = np.fft.rfft(seg * win, n=nfft)
    f = np.fft.rfftfreq(nfft, 1.0 / SR)
    amp = 2.0 * np.abs(X) / win.sum()
    return f, amp


def analyze_file(x, peaks, amps):
    A = db(amps)
    t_ms = peaks.astype(float) / SR * 1000.0
    rec = {}
    # dry = primo picco (t < 5 ms)
    is_dry = t_ms[0] < 5.0
    dry = {'t_ms': float(t_ms[0]), 'A_dbfs': float(A[0]), 'is_dry': bool(is_dry)}
    ep = peaks[1:]
    Ae = A[1:]
    te = t_ms[1:]
    G_loop = np.diff(Ae)                      # eco -> eco
    dt = np.diff(ep).astype(float) / SR * 1000.0
    G_forward = float(Ae[0] - A[0]) if len(Ae) else None
    # rumore nei gap (tra eco n e n+1), finestra 100 ms al centro
    nwin = int(GAP_WIN_S * SR)
    gap_rms, gap_pk = [], []
    for i in range(len(ep) - 1):
        mid = (ep[i] + ep[i + 1]) // 2
        a = max(0, mid - nwin // 2)
        seg = x[a:a + nwin]
        gap_rms.append(db(np.sqrt(np.mean(seg ** 2))))
        gap_pk.append(db(float(np.max(np.abs(seg)))))
    gap_r = np.array(gap_rms)
    gap_p = np.array(gap_pk)
    # floor RMS = mediana dei gap (escludo il primo, transiente d'avvio)
    floor_rms = float(np.median(gap_r[1:])) if len(gap_r) > 2 \
        else (float(np.median(gap_r)) if len(gap_r) else 0.0)
    # floor a picco = mediana dei max|gap|: gli echi sotto questo + margine
    # si confondono con i picchi del rumore (crest factor ~12-13 dB)
    peak_floor = float(np.median(gap_p)) if len(gap_p) else floor_rms
    reliable = Ae > (peak_floor + PEAK_MARGIN_DB)
    # loop gain nel regime affidabile: fit A vs indice eco
    loop_gain = None
    if int(np.sum(reliable)) >= 3:
        idx = np.where(reliable)[0]
        k, b = np.polyfit(idx.astype(float), Ae[idx], 1)
        loop_gain = float(k)
    # G del primo giro (eco1 -> eco2), regime a livello alto
    g_first = float(G_loop[0]) if len(G_loop) else None
    # dt affidabile: coppie dove entrambi gli echi sono sopra il floor a picco
    dt_rel = dt[reliable[:-1]] if int(np.sum(reliable)) >= 2 else dt
    dt_med = float(np.median(dt_rel)) if len(dt_rel) else None
    dt_std = float(np.std(dt_rel)) if len(dt_rel) else None
    # periodo robusto: fit lineare t = t0 + n*dt sugli echi affidabili
    dt_fit, dt_fit_n = None, 0
    if int(np.sum(reliable)) >= 3:
        idx = np.where(reliable)[0]
        kk, bb = np.polyfit(idx.astype(float), te[idx], 1)
        dt_fit = float(kk)
        dt_fit_n = int(len(idx))
    # G vs A (dipendenza dal livello) — solo coppie affidabili
    gvsA = None
    m_both = reliable[:-1] & reliable[1:]
    if int(np.sum(m_both)) >= 3:
        k2, b2 = np.polyfit(Ae[:-1][m_both], G_loop[m_both], 1)
        gvsA = {'slope_dBperdB': float(k2), 'intercept_dB': float(b2)}
    rec.update({
        'dry': dry,
        'n_ecos': int(len(ep)),
        'n_reliable': int(np.sum(reliable)),
        'G_forward_dB': G_forward,
        'G_first_pass_dB': g_first,
        'loop_gain_fit_dB_per_pass': loop_gain,
        'noise_floor_rms_dB': floor_rms,
        'noise_floor_peak_dB': peak_floor,
        'first_echo_t_ms': float(te[0]) if len(te) else None,
        'first_echo_A_dB': float(Ae[0]) if len(Ae) else None,
        'last_echo_A_dB': float(Ae[-1]) if len(Ae) else None,
        'dt_median_ms': dt_med,
        'dt_std_ms': dt_std,
        'dt_fit_ms': dt_fit,
        'dt_fit_n': dt_fit_n,
        'GvsA_fit': gvsA,
        'echoes': [
            {'n': i + 1, 't_ms': float(te[i]), 'A_dbfs': float(Ae[i]),
             'G_loop_dB': (float(G_loop[i - 1]) if i > 0 else None),
             'dt_ms': (float(dt[i - 1]) if i > 0 else None),
             'gap_noise_dB': (float(gap_r[i - 1]) if i < len(gap_r) else None),
             'reliable': bool(reliable[i])}
            for i in range(len(ep))
        ],
        'peaks_echo': ep.tolist(),
    })
    return rec


def main():
    results = {'sr': SR, 'threshold_dbfs': THR_DB,
               'peak_margin_db': PEAK_MARGIN_DB, 'files': {}}
    per = {}
    for fname, tag in FILES:
        x = load_mono24(os.path.join(DIR_RES, fname))
        peaks, amps = detect_peaks(x)
        rec = analyze_file(x, peaks, amps)
        rec['name'] = fname
        rec['tag'] = tag
        per[tag] = rec

    # spettri su FB10 — solo echi affidabili (sopra il floor a picco)
    fb = per['FB10']
    x = load_mono24(os.path.join(DIR_RES, fb['name']))
    ep = np.array(fb['peaks_echo'])
    rel_mask = np.array([e['reliable'] for e in fb['echoes']])
    rel_idx = np.where(rel_mask)[0]
    if len(rel_idx) >= 5:
        sel = np.unique(np.linspace(rel_idx[0], rel_idx[-1], 5).astype(int))
        sel = [int(s) for s in sel]
    elif len(rel_idx):
        sel = [int(s) for s in rel_idx]
    else:
        sel = [0]
    specs = {}
    for i in sel:
        f, amp = spectrum(x, ep[i])
        specs[i] = {'f': f.tolist(), 'amp': amp.tolist(),
                    'label': 'eco %d' % (i + 1),
                    'A_dbfs': float(fb['echoes'][i]['A_dbfs'])}

    # H_loop pulita = eco2 / eco1 (1 giro, entrambi interni al file,
    # windowing simmetrico valido): solo FB10
    f_1, a_1 = spectrum(x, ep[0])
    f_2, a_2 = spectrum(x, ep[1])
    h_loop_db = db(a_2 / np.maximum(a_1, 1e-12))
    fb['h_loop'] = {'f': f_2.tolist(), 'amp': h_loop_db.tolist(),
                    'note': 'eco2/eco1 = 1 giro del loop (FB10)',
                    'echo1_A_dbfs': float(fb['echoes'][0]['A_dbfs']),
                    'echo2_A_dbfs': float(fb['echoes'][1]['A_dbfs'])}

    # stimolo d'ingresso: caratterizzazione (e' un delta monosample bianco)
    stim = os.path.join(DIR_STIM, '01_impulse_single.wav')
    try:
        xin, sr_in, ch_in, fmt_in = load_float_wav(stim)
        ax_ = np.abs(xin)
        npk = int(np.argmax(ax_))
        pk = float(ax_[npk])
        nz = int(np.sum(ax_ > pk * 0.01))
        results['meta'] = {'input_stimulus': os.path.basename(stim),
                           'sr': int(sr_in), 'channels': int(ch_in),
                           'fmt': int(fmt_in),
                           'peak_at_sample': int(npk), 'peak': pk,
                           'samples_above_-40dB': int(nz),
                           'note': ('delta monosample bianco (spettro piatto); '
                                    'il dry a t~0 ms nel file e\' alla sequenza '
                                    'iniziale: spettro del dry non misurabile '
                                    '(windowing troncato)')}
    except Exception as e:
        results['meta'] = {'input_stimulus_error': str(e)}

    # bande + H per giro
    bands = {}
    for i in sel:
        f = np.array(specs[i]['f'])
        amp = np.array(specs[i]['amp'])
        m0 = (f >= 20) & (f <= 20000)
        m1 = (f > 20000) & (f <= 48000)
        e0 = float(np.sqrt(np.mean(amp[m0] ** 2)))
        e1 = float(np.sqrt(np.mean(amp[m1] ** 2)))
        mh = (f >= 15000) & (f <= 47000)
        kk, bb = np.polyfit(np.log2(f[mh]), db(amp[mh]), 1)
        mc = (f >= 20000) & (f <= 40000)
        sc = amp[mc] ** 2
        fc = float(np.sum(f[mc] * sc) / max(float(np.sum(sc)), 1e-30))
        bands[i] = {'e_0_20k_db': float(db(e0)), 'e_20_48k_db': float(db(e1)),
                    'hf_ratio_db': float(20 * np.log10(e1 / e0)),
                    'hf_slope_db_per_oct': float(kk),
                    'centroid_20_40k_hz': fc}
    fb['bands'] = bands
    fb['spectra_indices'] = sel
    results['files'] = per

    # ---------------- grafici ----------------
    # 1) decadimento (dry separato)
    fig, axes = plt.subplots(3, 2, figsize=(13, 11))
    for r, (fname, tag) in enumerate(FILES):
        rec = per[tag]
        echo = rec['echoes']
        n = np.arange(1, rec['n_ecos'] + 1)
        A = [e['A_dbfs'] for e in echo]
        G = [e['G_loop_dB'] for e in echo if e['G_loop_dB'] is not None]
        ax = axes[r][0]
        ax.plot(n, A, 'o-', ms=4, color=COLORS[tag], label='A_n')
        ax.axhline(THR_DB, color='k', lw=0.7, ls=':', label='-80 dBFS')
        ax.axhline(rec['noise_floor_rms_dB'], color='gray', lw=0.7, ls=':',
                   label='floor RMS %4.1f' % rec['noise_floor_rms_dB'])
        ax.axhline(rec['noise_floor_peak_dB'], color='gray', lw=0.7, ls='--',
                   label='floor picco %4.1f' % rec['noise_floor_peak_dB'])
        ax.set_title('%s — ampiezza echi (dry=%4.1f dBFS)'
                     % (tag, rec['dry']['A_dbfs']), fontsize=9)
        ax.set_xlabel('n eco (1 = primo ritardato, ~%d ms)'
                      % int(rec['first_echo_t_ms']))
        ax.set_ylabel('dBFS')
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
        ax = axes[r][1]
        ax.plot(n[1:], G, 'o-', ms=4, color=COLORS[tag])
        ax.axhline(0, color='k', lw=0.7, ls=':')
        if rec['loop_gain_fit_dB_per_pass'] is not None:
            ax.axhline(rec['loop_gain_fit_dB_per_pass'], color='gray',
                       lw=0.7, ls='--')
        ax.set_title('%s — G_loop (dB/eco; fit affidabile=%s)'
                     % (tag,
                        ('%5.2f' % rec['loop_gain_fit_dB_per_pass'])
                        if rec['loop_gain_fit_dB_per_pass'] is not None
                        else 'n/d'), fontsize=9)
        ax.set_xlabel('coppia (n, n+1)')
        ax.set_ylabel('dB/eco')
        ax.grid(alpha=0.3)
    fig.suptitle('Decadimento echi (soglia %g dBFS; dry a t~0 ms escluso)'
                 % THR_DB, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(HERE, 'feedback_decay.png'), dpi=150)
    plt.close(fig)

    # 2) G vs livello
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for fname, tag in FILES:
        rec = per[tag]
        echo = rec['echoes']
        Ax = [e['A_dbfs'] for e in echo[:-1]]
        Gx = [e['G_loop_dB'] for e in echo[1:]]
        ax.scatter(Ax, Gx, s=22, color=COLORS[tag], label=tag, alpha=0.85)
        if rec['GvsA_fit']:
            xs = np.linspace(min(Ax), max(Ax), 50)
            k, b = rec['GvsA_fit']['slope_dBperdB'], \
                rec['GvsA_fit']['intercept_dB']
            ax.plot(xs, k * xs + b, color=COLORS[tag], lw=1,
                    label='%s fit (pend. %.2f)' % (tag, k))
    ax.set_xlabel('A_n (dBFS)')
    ax.set_ylabel('G_loop (dB/eco)')
    ax.set_title('Loop gain vs livello eco (companding nel loop?)')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'feedback_g_vs_level.png'), dpi=150)
    plt.close(fig)

    # 3) spettri per eco
    fig, axes = plt.subplots(len(sel), 1,
                             figsize=(9, 1.6 * len(sel) + 1.2), sharex=True)
    if len(sel) == 1:
        axes = [axes]
    for a, i in zip(axes, sel):
        f = np.array(specs[i]['f'])
        amp = np.array(specs[i]['amp'])
        a.plot(f / 1000.0, db(amp), lw=0.9, color='tab:blue')
        a.set_title('%s (A=%5.1f dBFS)' % (specs[i]['label'],
                                           specs[i]['A_dbfs']), fontsize=8)
        a.set_ylabel('dBFS', fontsize=8)
        a.grid(alpha=0.3)
        a.set_xlim(0, 48)
    axes[-1].set_xlabel('kHz')
    fig.suptitle('Spettri per eco — FB10 (finestra 10 ms, Hann, NFFT=%d)'
                 % NFFT, fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(HERE, 'feedback_spectra_per_echo.png'), dpi=150)
    plt.close(fig)

    # 4) H_loop pulita (eco1/dry) + bande
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axes[0]
    fhl = np.array(fb['h_loop']['f'])
    ax.plot(fhl / 1000.0, np.array(fb['h_loop']['amp']),
            lw=1.2, color='tab:blue', label='H_loop = eco2/eco1 (1 giro)')
    ax.axhline(0, color='k', lw=0.7, ls=':')
    ax.set_title('H_loop(f) — 1 giro del loop, eco2/eco1 (FB10)', fontsize=10)
    ax.set_xlabel('kHz')
    ax.set_ylabel('dB')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_xlim(0, 48)
    ax = axes[1]
    ns = [i + 1 for i in sel]
    hr = [bands[i]['hf_ratio_db'] for i in sel]
    sl = [bands[i]['hf_slope_db_per_oct'] for i in sel]
    ax.plot(ns, hr, 's-', ms=5, color='tab:red',
            label='energia 20-48k / 0-20k (dB)')
    ax.plot(ns, sl, '^-', ms=5, color='tab:purple',
            label='pendenza 15-48k (dB/ottava)')
    ax.set_title('Roll-off HF per eco (FB10)', fontsize=10)
    ax.set_xlabel('n eco')
    ax.set_ylabel('dB / dB per ottava')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'feedback_loop_transfer.png'), dpi=150)
    plt.close(fig)

    # 5) rumore gap
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for fname, tag in FILES:
        rec = per[tag]
        g = [e['gap_noise_dB'] for e in rec['echoes']
             if e['gap_noise_dB'] is not None]
        ax.plot(np.arange(1, len(g) + 1), g, 'o-', ms=3, color=COLORS[tag],
                label=tag)
    ax.set_title('RMS rumore nei gap (finestra %g ms)' % (GAP_WIN_S * 1000),
                 fontsize=10)
    ax.set_xlabel('gap (tra eco n e n+1)')
    ax.set_ylabel('dBFS')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'feedback_noise_vs_echo.png'), dpi=150)
    plt.close(fig)

    # 6) jitter + baricentro
    fig, axes = plt.subplots(2, 1, figsize=(9, 7))
    for fname, tag in FILES:
        rec = per[tag]
        dtx = [e['dt_ms'] for e in rec['echoes'][1:]
               if e['dt_ms'] is not None]
        ax = axes[0]
        ax.plot(np.arange(1, len(dtx) + 1), dtx, 'o-', ms=3, color=COLORS[tag],
                label=tag)
        if rec['dt_median_ms']:
            ax.axhline(rec['dt_median_ms'], color=COLORS[tag], lw=0.7,
                       alpha=0.5, ls='--')
    axes[0].set_title('Δt tra echi (ms; atteso ≈528)', fontsize=10)
    axes[0].set_xlabel('coppia (n, n+1)')
    axes[0].set_ylabel('ms')
    axes[0].grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    fc = [bands[i]['centroid_20_40k_hz'] for i in sel]
    axes[1].plot(ns, fc, 's-', ms=5, color='tab:purple')
    axes[1].set_title('Baricentro 20-40 kHz per eco (FB10) — trend di tilt',
                      fontsize=10)
    axes[1].set_xlabel('n eco')
    axes[1].set_ylabel('Hz')
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'feedback_jitter.png'), dpi=150)
    plt.close(fig)

    out = os.path.join(HERE, 'feedback_results.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print('JSON:', out)
    for fname, tag in FILES:
        r = per[tag]
        print('%s: dry=%4.1f@%4.1fms | n_ecos=%d (affidabili %d) | '
              'Gfwd=%5.1f | G1pass=%5.1f dB | Gloop_fit=%s dB/passo | '
              'floorRMS/PK=%4.1f/%4.1f | dt_med=%6.1f±%.1f fit=%6.1f(n=%d) | '
              'A1=%4.1f->A_last=%4.1f dBFS'
              % (tag, r['dry']['A_dbfs'], r['dry']['t_ms'], r['n_ecos'],
                 r['n_reliable'], r['G_forward_dB'],
                 (r['G_first_pass_dB'] if r['G_first_pass_dB'] is not None
                  else float('nan')),
                 ('%5.2f' % r['loop_gain_fit_dB_per_pass'])
                 if r['loop_gain_fit_dB_per_pass'] is not None else '  n/d',
                 r['noise_floor_rms_dB'], r['noise_floor_peak_dB'],
                 r['dt_median_ms'], (r['dt_std_ms'] or 0.0),
                 (r['dt_fit_ms'] if r['dt_fit_ms'] is not None
                  else float('nan')), r['dt_fit_n'],
                 r['first_echo_A_dB'], r['last_echo_A_dB']))
    hl = fb['h_loop']
    fh = np.array(hl['f']); ah = np.array(hl['amp'])
    for lo, hi in [(100, 1000), (1000, 5000), (5000, 10000),
                   (10000, 20000), (20000, 48000)]:
        m = (fh >= lo) & (fh < hi)
        print('  H_loop eco2/eco1 [%4d-%5d Hz]: %+6.1f dB'
              % (lo, hi, float(np.median(ah[m]))))
    print('spettri FB10:', [specs[i]['label'] for i in sel])


if __name__ == '__main__':
    main()
