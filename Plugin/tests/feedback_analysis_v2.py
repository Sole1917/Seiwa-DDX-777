#!/usr/bin/env python
# -*- coding: utf-8 -*-
# feedback_analysis_v2.py — Rianalisi misure feedback DDX-777 (FB=2/5/10)
#
# Differenze da v1 (feedback_analysis.py):
#   - Soglia UNICA e FISSA: -60 dBFS a picco (rilevamento + validita').
#     Nessun margine adattivo sul noise floor: un eco e' valido se il suo
#     picco e' > -60 dBFS. I campioni/echi sotto -60 NON vengono contati.
#   - Loop gain riportata sia in dB (G_n = A[n+1]-A[n]) sia in scala LINEARE
#     (G_n = A[n+1]/A[n]), per confronto diretto con la soglia di
#     autoscillazione del modello DSP (G_lineare = 1).
#   - Rumore progressivo nel loop: coppie (1-2, 5-6, 10-11) usate in modo
#     DINAMICO — se un eco non e' valido la coppia viene segnalata come
#     non coperta (es. eco 10-11 con pochi echi validi).
#   - Spettro echi 1/5/10 (FB10) con ampiezza RMS di ciascun eco, per
#     normalizzare i confronti spettrali a parita' di livello.
#   - dt con fit lineare + errore standard (confronto 528 ms e 545.7 ms).
#
# Input (read-only):
#   Prep\Segnali_Test\Risultati\peak 10, feedback {2,5,10}, delay 10, 512 ms.wav
# Output (cartella di questo script):
#   feedback_v2_decay.png, feedback_v2_g_vs_level.png, feedback_v2_spectra.png,
#   feedback_v2_noise_progressive.png, feedback_v2_deltat.png,
#   feedback_results_v2.json
#
# Condizioni note: 96 kHz, 24 bit, contenuto mono in file STEREO (L==R) -> uso L.
# FACTOR=x1, MODULATION=0, HOLD=off, LEVEL=10. Il picco a t~0 ms (full scale)
# e' il DRY/impulso d'ingresso (riferimento), NON un eco: escluso dai conti.

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
THR_DB = -60.0            # soglia UNICA a picco (rilevamento + validita')
THR = 10 ** (THR_DB / 20.0)
NFFT = 32768
W_HALF_MS = 5.0
GAP_WIN_S = 0.10
MIN_GAP_S = 0.40
DT_REF_OLD_MS = 528.0     # valore "vecchio" (sessione 11) per confronto
DT_REF_V1_MS = 545.7      # valore v1 (reliable) per confronto

FILES = [
    ('peak 10, feedback 10, delay 10, 512 ms.wav', 'FB10'),
    ('peak 10, feedback 5 circa, delay 10, 512 ms.wav', 'FB5'),
    ('peak 10, feedback 2 circa, delay 10, 512 ms.wav', 'FB2'),
]
# conti v1 da confrontare: (detect a -80, reliable a floor+6dB)
V1_COUNTS = {'FB10': (39, 22), 'FB5': (13, 3), 'FB2': (8, 2)}
PAIRS = [(1, 2), (5, 6), (10, 11)]   # coppie rumore progressivo (1-based)
SPECTRO_IDX = [1, 5, 10]             # echi per lo spettro FB10 (1-based)
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
    return 20.0 * np.log10(np.maximum(a, 1e-30))


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
    rms = float(np.sqrt(np.mean(seg ** 2)))
    return f, amp, rms


def fit_slope_err(n, t):
    # fit lineare t = b + k*n con errore standard di k
    n = np.asarray(n, dtype=float)
    t = np.asarray(t, dtype=float)
    k, b = np.polyfit(n, t, 1)
    resid = t - (k * n + b)
    ss_res = float(np.sum(resid ** 2))
    ss_x = float(np.sum((n - n.mean()) ** 2))
    N = len(n)
    se = float(np.sqrt(max(ss_res, 0.0) / max(N - 2, 1) / ss_x)) if N > 2 else 0.0
    return float(k), float(b), se


def analyze_file(x, peaks, amps):
    A = db(amps)
    t_ms = peaks.astype(float) / SR * 1000.0
    rec = {}
    is_dry = t_ms[0] < 5.0
    dry = {'t_ms': float(t_ms[0]), 'A_dbfs': float(A[0]), 'is_dry': bool(is_dry)}
    ep = peaks[1:]
    ap = amps[1:]
    Ae = A[1:]
    te = t_ms[1:]
    n_valid = int(len(ep))
    G_dB = np.diff(Ae)
    G_lin = ap[1:] / np.maximum(ap[:-1], 1e-30)
    dt = np.diff(ep).astype(float) / SR * 1000.0
    G_forward = float(Ae[0] - A[0]) if n_valid else None
    # rumore nei gap (tra eco n e n+1), finestra 100 ms al centro
    nwin = int(GAP_WIN_S * SR)
    gap_rms, gap_pk = [], []
    for i in range(n_valid - 1):
        mid = (ep[i] + ep[i + 1]) // 2
        a = max(0, mid - nwin // 2)
        seg = x[a:a + nwin]
        gap_rms.append(db(np.sqrt(np.mean(seg ** 2))))
        gap_pk.append(db(float(np.max(np.abs(seg)))))
    gap_r = np.array(gap_rms) if gap_rms else np.array([])
    gap_p = np.array(gap_pk) if gap_pk else np.array([])
    floor_rms = float(np.median(gap_r[1:])) if len(gap_r) > 2 \
        else (float(np.median(gap_r)) if len(gap_r) else float('nan'))
    floor_peak = float(np.median(gap_p)) if len(gap_p) else float('nan')
    # dt: mediana/SCD per coppia + fit lineare con errore standard
    dt_med = float(np.median(dt)) if len(dt) else None
    dt_std = float(np.std(dt)) if len(dt) else None
    dt_fit, dt_fit_se, dt_fit_n = (None, None, 0)
    if n_valid >= 3:
        idx = np.arange(n_valid, dtype=float)
        kk, bb, se = fit_slope_err(idx, te)
        dt_fit, dt_fit_se, dt_fit_n = kk, se, n_valid
    rec.update({
        'dry': dry,
        'n_valid': n_valid,
        'noise_floor_rms_dB': floor_rms,
        'noise_floor_peak_dB': floor_peak,
        'G_forward_dB': G_forward,
        'first_echo_t_ms': float(te[0]) if n_valid else None,
        'first_echo_A_dB': float(Ae[0]) if n_valid else None,
        'last_echo_A_dB': float(Ae[-1]) if n_valid else None,
        'dt_median_ms': dt_med,
        'dt_std_ms': dt_std,
        'dt_fit_ms': dt_fit,
        'dt_fit_se_ms': dt_fit_se,
        'dt_fit_n': dt_fit_n,
        'dt_delta_vs_old_ms': (dt_fit - DT_REF_OLD_MS) if dt_fit else None,
        'dt_delta_vs_v1_ms': (dt_fit - DT_REF_V1_MS) if dt_fit else None,
        'echoes': [
            {'n': i + 1, 't_ms': float(te[i]), 'A_dbfs': float(Ae[i]),
             'A_linear': float(ap[i]),
             'G_loop_dB': (float(G_dB[i - 1]) if i > 0 else None),
             'G_loop_linear': (float(G_lin[i - 1]) if i > 0 else None),
             'dt_ms': (float(dt[i - 1]) if i > 0 else None),
             'gap_noise_rms_dB': (float(gap_r[i - 1]) if i < len(gap_r) else None),
             'gap_noise_peak_dB': (float(gap_p[i - 1]) if i < len(gap_p) else None)}
            for i in range(n_valid)
        ],
        'peaks_echo': ep.tolist(),
    })
    return rec, G_dB, G_lin


def main():
    results = {'sr': SR, 'threshold_dbfs': THR_DB,
               'dt_ref_old_ms': DT_REF_OLD_MS, 'dt_ref_v1_ms': DT_REF_V1_MS,
               'files': {}}
    per = {}
    for fname, tag in FILES:
        x = load_mono24(os.path.join(DIR_RES, fname))
        peaks, amps = detect_peaks(x)
        rec, G_dB, G_lin = analyze_file(x, peaks, amps)
        rec['name'] = fname
        rec['tag'] = tag
        per[tag] = rec
        # ripopolare i campi di confronto v1 (serve il tag)
        rec['n_detect_v1'] = V1_COUNTS.get(tag, (None,))[0]
        rec['n_reliable_v1'] = V1_COUNTS.get(tag, (None,))[1]

    # fit loop gain (dB/passo) sugli echi validi + G vs livello
    for tag, rec in per.items():
        ev = rec['echoes']
        n = len(ev)
        fit_db = None
        if n >= 3:
            idx = np.arange(n, dtype=float)
            Aarr = np.array([e['A_dbfs'] for e in ev])
            k, b = np.polyfit(idx, Aarr, 1)
            fit_db = float(k)
        rec['loop_gain_fit_dB_per_pass'] = fit_db
        rec['loop_gain_fit_linear_per_pass'] = (
            10 ** (fit_db / 20.0) if fit_db is not None else None)
        g1 = ev[1]['G_loop_dB'] if n > 1 else None
        g1l = ev[1]['G_loop_linear'] if n > 1 else None
        rec['G_first_pass_dB'] = g1
        rec['G_first_pass_linear'] = g1l
        # G vs A (dipendenza dal livello)
        if n > 2:
            Ax = np.array([e['A_dbfs'] for e in ev[:-1]])
            Gx = np.array([e['G_loop_dB'] for e in ev[1:]])
            k2, b2 = np.polyfit(Ax, Gx, 1)
            rec['GvsA_fit'] = {'slope_dBperdB': float(k2),
                               'intercept_dB': float(b2)}
        else:
            rec['GvsA_fit'] = None

    # rumore progressivo: coppie dinamiche
    for tag, rec in per.items():
        n = rec['n_valid']
        out = []
        for a, b in PAIRS:
            if b <= n:
                # gap tra eco a e eco b (contigui): indice 0-based = a-1
                out.append({
                    'pair': '%d-%d' % (a, b),
                    'covered': True,
                    'gap_rms_dB': rec['echoes'][a - 1]['gap_noise_rms_dB'],
                    'gap_peak_dB': rec['echoes'][a - 1]['gap_noise_peak_dB'],
                })
            else:
                out.append({'pair': '%d-%d' % (a, b), 'covered': False,
                            'gap_rms_dB': None, 'gap_peak_dB': None})
        rec['noise_progressive'] = out
        rec['noise_progressive_all_covered'] = all(o['covered'] for o in out)

    # spettri FB10 (eco 1/5/10) + RMS per normalizzazione
    fb = per['FB10']
    x = load_mono24(os.path.join(DIR_RES, fb['name']))
    ep = np.array(fb['peaks_echo'])
    specs = {}
    sel_used = []
    for target in SPECTRO_IDX:
        if target <= fb['n_valid']:
            m = int(ep[target - 1])
            f, amp, rms = spectrum(x, m)
            specs[target] = {
                'f': f.tolist(), 'amp': amp.tolist(),
                'label': 'eco %d' % target,
                'A_dbfs': float(fb['echoes'][target - 1]['A_dbfs']),
                'rms_window_db': float(db(rms)),
                'rms_window_linear': rms,
            }
            sel_used.append(target)
    fb['spectro_targets_requested'] = SPECTRO_IDX
    fb['spectro_targets_used'] = sel_used
    fb['spectro_not_covered'] = [t for t in SPECTRO_IDX if t not in sel_used]
    # bande per eco
    bands = {}
    for t in sel_used:
        f = np.array(specs[t]['f'])
        amp = np.array(specs[t]['amp'])
        m0 = (f >= 20) & (f <= 20000)
        m1 = (f > 20000) & (f <= 48000)
        e0 = float(np.sqrt(np.mean(amp[m0] ** 2)))
        e1 = float(np.sqrt(np.mean(amp[m1] ** 2)))
        mh = (f >= 15000) & (f <= 47000)
        kk, bb = np.polyfit(np.log2(f[mh]), db(amp[mh]), 1)
        bands[t] = {'e_0_20k_db': float(db(e0)), 'e_20_48k_db': float(db(e1)),
                    'hf_ratio_db': float(20 * np.log10(max(e1, 1e-30) / e0)),
                    'hf_slope_db_per_oct': float(kk)}
    fb['bands'] = bands
    fb['spectra'] = {str(t): specs[t] for t in sel_used}
    results['files'] = per

    # ---------------- grafici ----------------
    # 1) decadimento + G (dB e lineare)
    fig, axes = plt.subplots(3, 3, figsize=(17, 10))
    for r, (fname, tag) in enumerate(FILES):
        rec = per[tag]
        ev = rec['echoes']
        n = np.arange(1, rec['n_valid'] + 1)
        A = [e['A_dbfs'] for e in ev]
        Gd = [e['G_loop_dB'] for e in ev if e['G_loop_dB'] is not None]
        Gl = [e['G_loop_linear'] for e in ev if e['G_loop_linear'] is not None]
        ax = axes[r][0]
        ax.plot(n, A, 'o-', ms=4, color=COLORS[tag], label='A_n')
        ax.axhline(THR_DB, color='k', lw=0.7, ls=':', label='-%g dBFS' % -THR_DB)
        ax.axhline(rec['noise_floor_rms_dB'], color='gray', lw=0.7, ls=':',
                   label='floor RMS %4.1f' % rec['noise_floor_rms_dB'])
        ax.set_title('%s — ampiezza echi validi (dry=%4.1f dBFS)'
                     % (tag, rec['dry']['A_dbfs']), fontsize=9)
        ax.set_xlabel('n eco')
        ax.set_ylabel('dBFS')
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
        ax = axes[r][1]
        ax.plot(n[1:], Gd, 'o-', ms=4, color=COLORS[tag])
        if rec['loop_gain_fit_dB_per_pass'] is not None:
            ax.axhline(rec['loop_gain_fit_dB_per_pass'], color='gray',
                       lw=0.7, ls='--')
        ax.set_title('%s — G_loop (dB/eco; fit=%s)'
                     % (tag,
                        ('%5.2f' % rec['loop_gain_fit_dB_per_pass'])
                        if rec['loop_gain_fit_dB_per_pass'] is not None
                        else 'n/d'), fontsize=9)
        ax.set_xlabel('coppia (n, n+1)')
        ax.set_ylabel('dB/eco')
        ax.grid(alpha=0.3)
        ax = axes[r][2]
        ax.semilogy(n[1:], Gl, 'o-', ms=4, color=COLORS[tag])
        ax.axhline(1.0, color='red', lw=0.8, ls=':', label='G=1 (autoscill.)')
        if rec['loop_gain_fit_linear_per_pass'] is not None:
            ax.axhline(rec['loop_gain_fit_linear_per_pass'], color='gray',
                       lw=0.7, ls='--',
                       label='fit=%.3f' % rec['loop_gain_fit_linear_per_pass'])
        ax.set_title('%s — G_loop lineare (per passo)' % tag, fontsize=9)
        ax.set_xlabel('coppia (n, n+1)')
        ax.set_ylabel('G lineare')
        ax.grid(alpha=0.3, which='both')
        ax.legend(fontsize=7)
    fig.suptitle('v2 — Decadimento e loop gain (soglia %g dBFS; dry escluso)'
                 % THR_DB, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(HERE, 'feedback_v2_decay.png'), dpi=150)
    plt.close(fig)

    # 2) G vs livello (dB + lineare)
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for fname, tag in FILES:
        rec = per[tag]
        ev = rec['echoes']
        Ax = [e['A_dbfs'] for e in ev[:-1]]
        Gx = [e['G_loop_dB'] for e in ev[1:]]
        Gxl = [e['G_loop_linear'] for e in ev[1:]]
        ax.scatter(Ax, Gx, s=22, color=COLORS[tag], label=tag + ' (dB)', alpha=0.85)
        if rec['GvsA_fit']:
            xs = np.linspace(min(Ax), max(Ax), 50)
            k, b = rec['GvsA_fit']['slope_dBperdB'], rec['GvsA_fit']['intercept_dB']
            ax.plot(xs, k * xs + b, color=COLORS[tag], lw=1,
                    label='%s fit (p=%.2f)' % (tag, k))
    ax.set_xlabel('A_n (dBFS)')
    ax.set_ylabel('G_loop (dB/eco)')
    ax.set_title('v2 — Loop gain vs livello eco (companding nel loop?)')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'feedback_v2_g_vs_level.png'), dpi=150)
    plt.close(fig)

    # 3) spettri FB10 eco 1/5/10 (assoluti + normalizzati a parita' di RMS)
    n_spec = max(len(sel_used), 1)
    fig, axes = plt.subplots(2, n_spec, figsize=(3.6 * n_spec, 7),
                             sharex=True)
    if n_spec == 1:
        axes = axes[:, 0]
    # scala di normalizzazione: RMS del primo eco usato
    ref_rms = np.array([specs[t]['rms_window_linear'] for t in sel_used])
    for j, t in enumerate(sel_used):
        f = np.array(specs[t]['f'])
        amp = np.array(specs[t]['amp'])
        s = specs[t]
        ax = axes[0][j]
        ax.plot(f / 1000.0, db(amp), lw=0.9, color='tab:blue')
        ax.set_title('%s — assolute (A=%5.1f dBFS, RMS win=%5.1f dB)'
                     % (s['label'], s['A_dbfs'], s['rms_window_db']), fontsize=8)
        ax.set_ylabel('dBFS', fontsize=8)
        ax.grid(alpha=0.3)
        ax.set_xlim(0, 48)
        axn = axes[1][j]
        # scala l'eco al RMS di riferimento (eco1): parita' di livello
        scale_db = 20.0 * np.log10(max(ref_rms[0], 1e-30) /
                                   max(specs[t]['rms_window_linear'], 1e-30))
        axn.plot(f / 1000.0, db(amp) + scale_db, lw=0.9, color='tab:red')
        axn.set_title('%s — normalizzata al RMS di eco%d (%+.1f dB)'
                      % (s['label'], sel_used[0], scale_db), fontsize=8)
        axn.set_ylabel('dBFS (a parita\' di RMS)', fontsize=8)
        axn.grid(alpha=0.3)
        axn.set_xlim(0, 48)
    axes[1][n_spec - 1].set_xlabel('kHz')
    fig.suptitle('v2 — Spettri FB10 (10 ms, Hann, NFFT=%d) su %s'
                 % (NFFT, ', '.join('eco%d' % t for t in sel_used)), fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(os.path.join(HERE, 'feedback_v2_spectra.png'), dpi=150)
    plt.close(fig)

    # 4) rumore progressivo (coppie dinamiche)
    fig, ax = plt.subplots(figsize=(8.5, 5))
    xlab = np.arange(len(PAIRS))
    for fname, tag in FILES:
        rec = per[tag]
        rp = [o['gap_rms_dB'] for o in rec['noise_progressive']]
        pp = [o['gap_peak_dB'] for o in rec['noise_progressive']]
        rp = [v if v is not None else np.nan for v in rp]
        pp = [v if v is not None else np.nan for v in pp]
        ax.plot(xlab, rp, 'o-', ms=5, color=COLORS[tag],
                label=tag + ' RMS')
        ax.plot(xlab, pp, 's--', ms=4, color=COLORS[tag], alpha=0.5,
                label=tag + ' picco')
    ax.set_xticks(xlab)
    ax.set_xticklabels(['eco %d-%d' % p for p in PAIRS])
    ax.set_title('v2 — Rumore nel loop per coppia (finestra 100 ms)')
    ax.set_ylabel('dBFS')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'feedback_v2_noise_progressive.png'), dpi=150)
    plt.close(fig)

    # 5) dt per coppia + fit
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for fname, tag in FILES:
        rec = per[tag]
        dtx = [e['dt_ms'] for e in rec['echoes'][1:] if e['dt_ms'] is not None]
        ax.plot(np.arange(1, len(dtx) + 1), dtx, 'o-', ms=3, color=COLORS[tag],
                label=tag)
        if rec['dt_fit_ms']:
            ax.axhline(rec['dt_fit_ms'], color=COLORS[tag], lw=0.7, alpha=0.5,
                       ls='--')
    ax.axhline(DT_REF_OLD_MS, color='gray', lw=1, ls=':',
               label='ref vecchio %g ms' % DT_REF_OLD_MS)
    ax.axhline(DT_REF_V1_MS, color='k', lw=1, ls=':',
               label='ref v1 %g ms' % DT_REF_V1_MS)
    ax.set_title('v2 — Δt tra echi validi (ms)')
    ax.set_xlabel('coppia (n, n+1)')
    ax.set_ylabel('ms')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'feedback_v2_deltat.png'), dpi=150)
    plt.close(fig)

    out = os.path.join(HERE, 'feedback_results_v2.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print('JSON:', out)
    for fname, tag in FILES:
        r = per[tag]
        print('%s: validi=%d (v1 detect=%s/reliable=%s) | floorRMS/PK=%4.1f/%4.1f | '
              'Gfwd=%5.1f | G1pass=%5.1f dB / %.4f lin | Gloop_fit=%s dB / %s lin | '
              'dt_fit=%6.1f±%.1f ms (n=%d, d_old=%+.1f d_v1=%+.1f) | A1=%4.1f->A_last=%4.1f'
              % (tag, r['n_valid'], r['n_detect_v1'], r['n_reliable_v1'],
                 r['noise_floor_rms_dB'], r['noise_floor_peak_dB'],
                 r['G_forward_dB'], r['G_first_pass_dB'],
                 (r['G_first_pass_linear'] if r['G_first_pass_linear'] is not None
                  else float('nan')),
                 ('%5.2f' % r['loop_gain_fit_dB_per_pass'])
                 if r['loop_gain_fit_dB_per_pass'] is not None else '  n/d',
                 ('%.4f' % r['loop_gain_fit_linear_per_pass'])
                 if r['loop_gain_fit_linear_per_pass'] is not None else ' n/d',
                 (r['dt_fit_ms'] if r['dt_fit_ms'] is not None else float('nan')),
                 (r['dt_fit_se_ms'] or 0.0), r['dt_fit_n'],
                 (r['dt_delta_vs_old_ms'] or 0.0), (r['dt_delta_vs_v1_ms'] or 0.0),
                 r['first_echo_A_dB'], r['last_echo_A_dB']))
        np_ = r['noise_progressive']
        cov = ', '.join(('%s:%s' % (o['pair'],
                                    ('rms %4.1f' % o['gap_rms_dB'])
                                    if o['covered'] else 'NESSUNA'))
                         for o in np_)
        print('   rumore progressivo: %s | tutte coperte=%s'
              % (cov, r['noise_progressive_all_covered']))
    print('spettri FB10:', fb['spectro_targets_used'],
          '(non coperti: %s)' % (fb['spectro_not_covered'] or '-'))
    for t in sel_used:
        s = specs[t]
        b = bands[t]
        print('   %s: A=%5.1f dBFS | RMS win=%5.1f dB | 0-20k=%5.1f | '
              '20-48k=%5.1f | HF ratio=%+5.1f dB | pendenza 15-47k=%4.1f dB/ott'
              % (s['label'], s['A_dbfs'], s['rms_window_db'],
                 b['e_0_20k_db'], b['e_20_48k_db'], b['hf_ratio_db'],
                 b['hf_slope_db_per_oct']))


if __name__ == '__main__':
    main()
