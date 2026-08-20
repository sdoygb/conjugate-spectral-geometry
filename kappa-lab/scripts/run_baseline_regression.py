#!/usr/bin/env python3
"""阶段 1：基线回归——复现官方功率谱 χ²@MAP 管道，固化基准指标。

与官方 baseline_official.py 逐位对齐（同 SEED=42、同 rng 消耗顺序）：
- 训练 80 宇宙学 × 256 仿真 → log10 P(l) 10 bin → μ/Cov → LinearNDInterpolator
- 30² 网格 MAP → χ²@MAP（训练自身 + 验证 21 干净新宇宙学）
- 4 种扰动（模糊 ×2、额外噪声 ×2）→ cohen-d + TPR@FPR

输出：kappa-lab/results/baseline_regression/{metrics.json, chi2.npz}
对比：wl_challenge/data/full/official_results_original.npz（Pearson r、最大逐点差）

用法：python3 kappa-lab/scripts/run_baseline_regression.py
"""
import json, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'wl_challenge', 'data', 'full')
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PKG, 'results', 'baseline_regression')
sys.path.insert(0, PKG)
from kappa_lab.stats.powerspectrum import power_spectrum, SIGMA_NOISE

SEED = 42
PIXEL_ARCMIN = 2.0
N_BIN = 10
L_EDGE = np.logspace(2, 4, N_BIN + 1)
N_TRAIN_COSMO = 80
GRID_N = 30
PIXSIZE = PIXEL_ARCMIN / 60 * np.pi / 180


def tpr_at_fpr_official(score_id, score_ood):
    """官方评分：ROC 在 FPR∈[0.001,0.05] 对数空间 100 点平均 TPR"""
    from sklearn.metrics import roc_curve
    y = np.concatenate([np.zeros(len(score_id)), np.ones(len(score_ood))])
    s = np.concatenate([score_id, score_ood])
    fpr, tpr, _ = roc_curve(y, s)
    fpr_grid = np.logspace(np.log10(0.001), np.log10(0.05), 100)
    return float(np.mean(np.interp(fpr_grid, fpr, tpr)))


def cohen_d(a, b):
    return (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    mask = np.load(os.path.join(DATA, 'WIDE12H_bin2_2arcmin_mask.npy')).astype(bool)
    ny, nx = mask.shape
    lab = np.load(os.path.join(DATA, 'label_newrealization.npy'))
    rng = np.random.default_rng(SEED)
    k = np.load(os.path.join(DATA, 'kappa_full.npy'), mmap_mode='r')
    nr, nimg, npix = k.shape
    assert (nr, nimg, npix) == (101, 256, 132019), k.shape
    train_idx = np.arange(N_TRAIN_COSMO)
    val_idx = np.arange(N_TRAIN_COSMO, nr)

    def logPS_batch(indices, perturb=None):
        """逐宇宙学算加噪功率谱（rng 消耗顺序与官方一致）"""
        out = np.zeros((len(indices) * nimg, N_BIN), np.float32)
        p = 0
        for i in indices:
            v = np.asarray(k[i], dtype=np.float64)
            full = np.zeros((nimg, ny, nx), np.float64)
            full[:, mask] = v
            if perturb is not None:
                full = perturb(full)
            else:
                full = full + rng.normal(0, SIGMA_NOISE, full.shape) * mask[None]
            for j in range(nimg):
                _, P = power_spectrum(full[j], PIXSIZE, L_EDGE)
                out[p + j] = np.log10(P + 1e-30)
            p += nimg
            if (i - indices[0]) % 20 == 0:
                print(f'  PS cosmo {i}/{indices[-1]} ({time.time()-t0:.0f}s)', flush=True)
        return out

    print('训练功率谱...', flush=True)
    tr_logP = logPS_batch(train_idx)
    tr_logP_c = tr_logP.reshape(len(train_idx), nimg, N_BIN)
    mu = tr_logP_c.mean(1)
    cov = np.zeros((len(train_idx), N_BIN, N_BIN))
    for i in range(len(train_idx)):
        d = tr_logP_c[i] - mu[i]
        cov[i] = d.T @ d / (nimg - N_BIN - 2)

    from scipy.interpolate import LinearNDInterpolator
    cosmo = lab[train_idx, 0, :2]
    mu_interp = LinearNDInterpolator(cosmo, mu, fill_value=np.nan)
    cov_interp = LinearNDInterpolator(cosmo, cov, fill_value=np.nan)
    om_grid = np.linspace(cosmo[:, 0].min(), cosmo[:, 0].max(), GRID_N)
    s8_grid = np.linspace(cosmo[:, 1].min(), cosmo[:, 1].max(), GRID_N)
    Gx, Gy = np.meshgrid(om_grid, s8_grid, indexing='ij')
    grid_pts = np.stack([Gx.ravel(), Gy.ravel()], 1)
    mu_g = mu_interp(grid_pts)
    cov_g = cov_interp(grid_pts)
    ok = np.isfinite(mu_g).all(1)
    inv_g = np.zeros_like(cov_g)
    for g in range(GRID_N ** 2):
        if ok[g]:
            inv_g[g] = np.linalg.inv(cov_g[g])

    def chi2_at_maps(logP_batch):
        """每样本：网格搜索 χ² 最小值（MAP χ²）"""
        n = len(logP_batch)
        chi2_min = np.full(n, np.inf)
        B = 512
        for s in range(0, n, B):
            b = logP_batch[s:s + B]
            for g in range(GRID_N ** 2):
                if not ok[g]:
                    continue
                d = b - mu_g[g]
                c2 = np.einsum('ni,ij,nj->n', d, inv_g[g], d)
                np.minimum(chi2_min[s:s + B], c2, out=chi2_min[s:s + B])
        return chi2_min

    print('验证功率谱（干净新宇宙学）...', flush=True)
    val_logP = logPS_batch(val_idx)
    val_chi2 = chi2_at_maps(val_logP)
    tr_chi2 = chi2_at_maps(tr_logP)

    metrics = {
        'tr_chi2_median': float(np.median(tr_chi2)),
        'val_chi2_median': float(np.median(val_chi2)),
        'seed_sensitivity_d': float(cohen_d(val_chi2, tr_chi2)),
        'seed_sensitivity_tpr': float(tpr_at_fpr_official(tr_chi2, val_chi2)),
        'perturbs': {},
        'config': {'seed': SEED, 'n_train': N_TRAIN_COSMO, 'n_val': nr - N_TRAIN_COSMO,
                   'n_bin': N_BIN, 'l_range': [float(L_EDGE[0]), float(L_EDGE[-1])],
                   'grid_n': GRID_N, 'sigma_noise': SIGMA_NOISE},
    }
    print(f'训练 χ² median={metrics["tr_chi2_median"]:.1f}, 验证 χ² median={metrics["val_chi2_median"]:.1f}')
    print(f'种子敏感度: d={metrics["seed_sensitivity_d"]:+.2f} TPR@FPR={metrics["seed_sensitivity_tpr"]:.4f}', flush=True)

    from scipy.ndimage import gaussian_filter

    def blur(sig):
        return lambda imgs: np.stack([gaussian_filter(im, sigma=sig) for im in imgs])

    def extra_noise(sig):
        return lambda imgs: imgs + rng.normal(0, sig, imgs.shape) * mask[None]

    perturbs = [
        ('blur_1px', blur(1.0)),
        ('blur_2px', blur(2.0)),
        ('extra_noise_0.5sn', extra_noise(0.5 * SIGMA_NOISE)),
        ('extra_noise_1.0sn', extra_noise(1.0 * SIGMA_NOISE)),
    ]
    print('扰动响应（ID=干净新宇宙学, OoD=扰动新宇宙学）:', flush=True)
    for name, pf in perturbs:
        Vp = logPS_batch(val_idx, perturb=pf)
        c2 = chi2_at_maps(Vp)
        metrics['perturbs'][name] = {
            'd': float(cohen_d(c2, val_chi2)),
            'tpr_at_fpr': float(tpr_at_fpr_official(val_chi2, c2)),
        }
        print(f'  {name:24s} d={metrics["perturbs"][name]["d"]:+.2f} '
              f'TPR@FPR={metrics["perturbs"][name]["tpr_at_fpr"]:.4f}', flush=True)

    orig = np.load(os.path.join(DATA, 'official_results_original.npz'))
    r_tr = float(np.corrcoef(tr_chi2, orig['tr_chi2'])[0, 1])
    r_val = float(np.corrcoef(val_chi2, orig['val_chi2'])[0, 1])
    maxdiff_tr = float(np.abs(tr_chi2 - orig['tr_chi2']).max())
    maxdiff_val = float(np.abs(val_chi2 - orig['val_chi2']).max())
    metrics['regression'] = {
        'pearson_r_tr': r_tr, 'pearson_r_val': r_val,
        'max_abs_diff_tr': maxdiff_tr, 'max_abs_diff_val': maxdiff_val,
    }
    print(f'回归对比: r_tr={r_tr:.8f} r_val={r_val:.8f} '
          f'maxdiff_tr={maxdiff_tr:.2e} maxdiff_val={maxdiff_val:.2e}', flush=True)

    metrics['timing_s'] = {'total': time.time() - t0}
    np.savez(os.path.join(OUT, 'chi2.npz'), tr_chi2=tr_chi2, val_chi2=val_chi2)
    with open(os.path.join(OUT, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f'DONE ({time.time()-t0:.0f}s) -> {OUT}/metrics.json', flush=True)


if __name__ == '__main__':
    main()
