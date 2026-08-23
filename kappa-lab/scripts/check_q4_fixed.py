#!/usr/bin/env python3
"""Q4 修正版：n=20 窗口普适性检验（动态范围限制在 Nyquist 内）。

背景：Q4 首版 n=20 用 l∈[100,10⁴]，最高 bin [7943,10⁴] 超出 Nyquist
(l_max = π/pixsize ≈ 5400) → Nmode=0 → P=0 → 占比钳位 1e-30 → 全部图 S̃ 退化
为同一数值 2.5e27（技术缺陷，非物理）。本版修正：l∈[100,5000]。

设计（数据前固定）：
- 检验 Q4-20：n=20, l∈[100,5000]，训练加噪图 S̃ 中位是否 ∈ (1,2)
- 对照 C10：n=10, l∈[100,5000]，训练加噪图 S̃ 中位（与 G1 的 n=10 [100,10⁴]
  结果 1.933 对比，评估动态范围影响）
- 标定 W20：白噪声 n=20 的 S̃ 中位（估计偏置基线：bin 模式数少 → P 估计波动
  → Jensen 偏置使 S̃ > 1；信号 n=20 解读需扣除该偏置）
"""
import json, os, sys, time
import numpy as np
from scipy.ndimage import gaussian_filter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'wl_challenge', 'data', 'full')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'results', 'g1_pipeline')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kappa_lab.stats.powerspectrum import power_spectrum, SIGMA_NOISE

SEED = 42
PIXEL_ARCMIN = 2.0
N_TRAIN = 80
L_MAX = 5000.0   # Nyquist 内（l_max = π/pixsize ≈ 5396）
PIXSIZE = PIXEL_ARCMIN / 60 * np.pi / 180


def geo_encode(P, n_bin):
    norm = P.sum(1, keepdims=True)
    s2 = P / np.maximum(norm, 1e-30)
    S = (1.0 / np.maximum(s2, 1e-30)).sum(1)
    return S / (n_bin ** 2)


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    mask = np.load(os.path.join(DATA, 'WIDE12H_bin2_2arcmin_mask.npy')).astype(bool)
    ny, nx = mask.shape
    lab = np.load(os.path.join(DATA, 'label_newrealization.npy'))
    kpath = os.path.join(DATA, 'kappa_full.npy')
    if not os.path.exists(kpath):
        kpath = os.path.join(DATA, 'WIDE12H_bin2_2arcmin_kappa_newrealization.npy')
    k = np.load(kpath, mmap_mode='r')
    rng = np.random.default_rng(SEED)

    def run(indices, n_bin, l_edges, perturb=None):
        out = np.zeros((len(indices) * 256, n_bin), np.float32)
        p = 0
        for i in indices:
            v = np.asarray(k[i], dtype=np.float64)
            full = np.zeros((256, ny, nx), np.float64)
            full[:, mask] = v
            if perturb is not None:
                full = perturb(full)
            else:
                full = full + rng.normal(0, SIGMA_NOISE, full.shape) * mask[None]
            for j in range(256):
                _, P = power_spectrum(full[j], PIXSIZE, l_edges)
                out[p + j] = P
            p += 256
            if (i - indices[0]) % 20 == 0:
                print(f'  n={n_bin} cosmo {i}/{indices[-1]} ({time.time()-t0:.0f}s)',
                      flush=True)
        return out

    train_idx = np.arange(N_TRAIN)
    res = {}

    # Q4-20：n=20, [100,5000]
    print('=== Q4 修正版：n=20 [100,5000] ===', flush=True)
    P20 = run(train_idx, 20, np.logspace(2, np.log10(L_MAX), 21))
    S20 = geo_encode(P20, 20)
    med20, q20 = float(np.median(S20)), np.percentile(S20, [16, 84])
    ok20 = (1.0 < med20 < 2.0)
    res['n20'] = {'median': med20, 'q16': float(q20[0]), 'q84': float(q20[1]),
                  'in_window': bool(ok20)}
    print(f'  n=20 S̃ 中位={med20:.4f} [16,84]=[{q20[0]:.4f},{q20[1]:.4f}] '
          f'窗口判定={"通过" if ok20 else "失败"}', flush=True)

    # C10 对照：n=10, [100,5000]
    print('=== 对照：n=10 [100,5000]（与 G1 的 [100,10⁴] 结果 1.933 对比）===',
          flush=True)
    P10 = run(train_idx, 10, np.logspace(2, np.log10(L_MAX), 11))
    S10 = geo_encode(P10, 10)
    med10, q10 = float(np.median(S10)), np.percentile(S10, [16, 84])
    res['n10_5000'] = {'median': med10, 'q16': float(q10[0]), 'q84': float(q10[1])}
    print(f'  n=10 [100,5000] S̃ 中位={med10:.4f} [16,84]=[{q10[0]:.4f},{q10[1]:.4f}] '
          f'(G1 [100,10⁴]: 1.933)', flush=True)

    # W20 白噪声标定：n=20 的估计偏置基线
    print('=== 白噪声标定 n=20 ===', flush=True)
    rng2 = np.random.default_rng(12345)
    nw = 200
    wS = np.zeros(nw)
    for i in range(nw):
        noise = rng2.normal(0, SIGMA_NOISE, (ny, nx)) * mask
        _, P = power_spectrum(noise, PIXSIZE, np.logspace(2, np.log10(L_MAX), 21))
        wS[i] = geo_encode(P[None], 20)[0]
    med_w = float(np.median(wS))
    res['white_n20'] = {'median': med_w}
    print(f'  白噪声 n=20 S̃ 中位={med_w:.4f}（>1 的部分 = bin 估计偏置）',
          flush=True)

    res['timing_s'] = time.time() - t0
    with open(os.path.join(OUT, 'q4_fixed_metrics.json'), 'w') as f:
        json.dump(res, f, indent=2)
    np.savez(os.path.join(OUT, 'q4_fixed_S.npz'), s20=S20, s10=S10, w20=wS)
    print(f'DONE ({time.time()-t0:.0f}s) -> q4_fixed_metrics.json', flush=True)


if __name__ == '__main__':
    main()
