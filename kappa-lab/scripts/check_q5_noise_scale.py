#!/usr/bin/env python3
"""Q5：F4 噪声缩放预言检验。

F4(iv) 预言：S̃ ∈ (1,2) ⇔ ρ > ρ_min(β)。WL 观测者 ρ_wl ≈ 0.0854（由 S̃=1.933, β=1.2 反推），
ρ_min(1.2) ≈ 0.0791 → 预言交点 f* = sqrt(ρ_min/ρ_wl) ≈ 0.962（σn 降到 96% 时 S̃ 越过 2）。

检验：固定图、缩放噪声 σn' = σn×f，实测 S̃(f) 中位数曲线，与 F4 预言对比。
"""
import numpy as np
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kappa_lab.stats.powerspectrum import power_spectrum

SEED = 42
PIXEL_ARCMIN = 2.0
N_BIN = 10
L_EDGE = np.logspace(2, 4, N_BIN + 1)
SIGMA_NOISE = 0.02582
PIXSIZE = PIXEL_ARCMIN / 60 * np.pi / 180
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'wl_challenge', 'data', 'full')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'results', 'g1_pipeline')

N_COSMO = 20          # 前 20 个训练宇宙学（5120 图/档，中位数统计足够）
FS = [1.0, 0.98, 0.965, 0.95, 0.94, 0.92, 0.9, 0.8, 0.6, 0.4, 0.2, 0.05]

def geo_encode(P):
    norm = P.sum(1, keepdims=True)
    s2 = P / np.maximum(norm, 1e-30)
    return (1.0 / np.maximum(s2, 1e-30)).sum(1) / (N_BIN ** 2)

def main():
    t0 = time.time()
    mask = np.load(os.path.join(DATA, 'WIDE12H_bin2_2arcmin_mask.npy')).astype(bool)
    ny, nx = mask.shape
    kpath = os.path.join(DATA, 'kappa_full.npy')
    k = np.load(kpath, mmap_mode='r')
    rng = np.random.default_rng(SEED)

    # F4 预言（事前）：β=1.2, ρ_wl=0.0854, ρ_min(1.2)=0.0791 → f*
    rho_wl, rho_min = 0.0854, 0.0791
    fstar_pred = np.sqrt(rho_min / rho_wl)
    print(f'F4 预言: f* = sqrt({rho_min:.4f}/{rho_wl:.4f}) = {fstar_pred:.4f} '
          f'(σn 降至 {fstar_pred*100:.1f}% 时 S̃ 越过 2)', flush=True)

    results = {}
    for f in FS:
        sn = SIGMA_NOISE * f
        s_all = np.zeros(N_COSMO * 256)
        p = 0
        for i in range(N_COSMO):
            v = np.asarray(k[i], dtype=np.float64)
            full = np.zeros((256, ny, nx), np.float64)
            full[:, mask] = v
            full = full + rng.normal(0, sn, full.shape) * mask[None]
            for j in range(256):
                _, P = power_spectrum(full[j], PIXSIZE, L_EDGE)
                s_all[p] = geo_encode(P[None])[0]
                p += 1
        med, q16, q84 = np.median(s_all), np.percentile(s_all, 16), np.percentile(s_all, 84)
        results[f] = {'median': float(med), 'q16': float(q16), 'q84': float(q84)}
        print(f'  f={f:.3f} (σn={sn:.5f})  S̃中位={med:.4f} [{q16:.3f},{q84:.3f}] '
              f'{"越界!" if med > 2 else "窗口内"} ({time.time()-t0:.0f}s)', flush=True)

    # 交点插值（S̃ 随 f 减而增 → 从窗口内越过 2）
    fs_sorted = sorted(results.keys())
    meds = [results[f]['median'] for f in fs_sorted]
    fstar_obs = None
    for a, b in zip(fs_sorted, fs_sorted[1:]):
        ma, mb = results[a]['median'], results[b]['median']
        if ma <= 2.0 <= mb:
            fstar_obs = a + (2.0 - ma) / (mb - ma) * (b - a)
            break
    hit = fstar_obs is not None and abs(fstar_obs - fstar_pred) < 0.02
    print(f'\n实测交点 f*_obs = {fstar_obs:.4f} vs F4 预言 f* = {fstar_pred:.4f} '
          f'(比值 {fstar_obs/fstar_pred:.3f})', flush=True)
    print(f'判定: {"✅ 命中" if hit else "❌ 未命中"} (容差 ±0.02)', flush=True)

    out = os.path.join(OUT, 'q5_noise_scale.json')
    with open(out, 'w') as fp:
        json.dump({'fstar_pred': fstar_pred, 'fstar_obs': fstar_obs, 'hit': bool(hit),
                   'results': {str(f): v for f, v in results.items()}}, fp, indent=2)
    print(f'DONE ({time.time()-t0:.0f}s) -> {out}', flush=True)

if __name__ == '__main__':
    main()
