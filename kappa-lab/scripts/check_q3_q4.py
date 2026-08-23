#!/usr/bin/env python3
"""Q3/Q4 区分检验：场编码定理的判决实验。

Q3: 纯无噪信号谱的 S̃（预测 > 2 → 支持 M4：窗口刻画"观测谱"而非信号谱）
Q4: n=5/20 bin 下训练加噪 κ 图 S̃ 中位数是否仍 ∈ (1,2)
    （若普适 → 窗口无标度；若漂移 → n=10 特定，下界匹配是巧合）

预言（数据前固定，2026-08-20）：
  Q3: 无噪训练谱 S̃ 中位数 > 2（与加噪 1.933 对比）
  Q4: n=5 与 n=20 的训练加噪 S̃ 中位数 ∈ (1,2)  ⇔ 窗口普适
"""
import json, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'wl_challenge', 'data', 'full')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'g1_pipeline')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kappa_lab.stats.powerspectrum import power_spectrum, SIGMA_NOISE

SEED = 42
PIXEL_ARCMIN = 2.0
PIXSIZE = PIXEL_ARCMIN / 60 * np.pi / 180
N_TRAIN_COSMO = 80
WINDOW = (1.0, 2.0)


def geo_encode(P_batch, n_bin):
    """P_batch: (N, n_bin) 线性功率 → S̃ (N,)"""
    norm = P_batch.sum(1, keepdims=True)
    s2 = P_batch / np.maximum(norm, 1e-30)
    S = (1.0 / np.maximum(s2, 1e-30)).sum(1)
    return S / (n_bin ** 2)


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    mask = np.load(os.path.join(DATA, 'WIDE12H_bin2_2arcmin_mask.npy')).astype(bool)
    ny, nx = mask.shape
    rng = np.random.default_rng(SEED)
    kpath = os.path.join(DATA, 'kappa_full.npy')
    if not os.path.exists(kpath):
        kpath = os.path.join(DATA, 'WIDE12H_bin2_2arcmin_kappa_newrealization.npy')
    k = np.load(kpath, mmap_mode='r')
    nr, nimg, npix = k.shape
    assert (nr, nimg, npix) == (101, 256, 132019), k.shape
    train_idx = np.arange(N_TRAIN_COSMO)

    def logPS_batch(indices, n_bin, noisy, rng_use):
        L_EDGE = np.logspace(2, 4, n_bin + 1)
        out = np.zeros((len(indices) * nimg, n_bin), np.float32)
        p = 0
        for i in indices:
            v = np.asarray(k[i], dtype=np.float64)
            full = np.zeros((nimg, ny, nx), np.float64)
            full[:, mask] = v
            if noisy:
                full = full + rng_use.normal(0, SIGMA_NOISE, full.shape) * mask[None]
            for j in range(nimg):
                _, P = power_spectrum(full[j], PIXSIZE, L_EDGE)
                out[p + j] = P
            p += nimg
            if (i - indices[0]) % 20 == 0:
                print(f'  cosmo {i}/{indices[-1]} n_bin={n_bin} noisy={noisy} ({time.time()-t0:.0f}s)', flush=True)
        return out

    res = {'window': WINDOW, 'q3': {}, 'q4': {}}

    # ---- Q3: 无噪信号谱（不消耗主 rng）----
    print('=== Q3: 无噪信号谱 S̃（预测 > 2）===', flush=True)
    P3 = logPS_batch(train_idx, 10, noisy=False, rng_use=rng)
    S3 = geo_encode(P3, 10)
    med3 = float(np.median(S3))
    q3 = np.percentile(S3, [16, 84])
    res['q3'] = {'n_bin': 10, 'median': med3, 'q16': float(q3[0]), 'q84': float(q3[1]),
                 'prediction_gt_2': bool(med3 > 2.0)}
    print(f'Q3: 无噪 S̃ 中位={med3:.4f} [16,84]=[{q3[0]:.4f},{q3[1]:.4f}]  '
          f'(加噪对照 1.933) 预言>2: {"✅" if med3 > 2 else "❌"}', flush=True)

    # ---- Q4: n=5 / n=20 加噪谱（独立加噪序列，避免与基线交叉）----
    print('=== Q4: bin 数普适性（n=5, 20，预测仍 ∈(1,2)）===', flush=True)
    saved = {}
    for nb in (5, 20):
        rng_q4 = np.random.default_rng(SEED + nb)
        P4 = logPS_batch(train_idx, nb, noisy=True, rng_use=rng_q4)
        S4 = geo_encode(P4, nb)
        saved[f's{nb}'] = S4
        med4 = float(np.median(S4))
        q4 = np.percentile(S4, [16, 84])
        res['q4'][str(nb)] = {'median': med4, 'q16': float(q4[0]), 'q84': float(q4[1]),
                              'in_window': bool(WINDOW[0] <= med4 <= WINDOW[1])}
        print(f'Q4 n={nb:2d}: S̃ 中位={med4:.4f} [16,84]=[{q4[0]:.4f},{q4[1]:.4f}]  '
              f'∈(1,2): {"✅" if WINDOW[0] <= med4 <= WINDOW[1] else "❌"}', flush=True)

    res['timing_s'] = time.time() - t0
    with open(os.path.join(OUT, 'q3_q4_metrics.json'), 'w') as f:
        json.dump(res, f, indent=2)
    np.savez(os.path.join(OUT, 'q3_q4_S_tilde.npz'), s3_noisy10=S3, **saved)
    print(f'DONE ({time.time()-t0:.0f}s) -> {OUT}/q3_q4_metrics.json', flush=True)


if __name__ == '__main__':
    main()
