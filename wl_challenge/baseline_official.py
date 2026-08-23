"""官方基线复现：功率谱 χ²@MAP（Phase 2 starting kit 移植）
- 训练：N_tr 宇宙学 × 256 realization，加形状噪声(σ=0.0258) → log10 P(l) 10 bin
- 每宇宙学均值 μ(θ)、协方差 Cov(θ)，LinearNDInterpolator 在 (Ωm,S₈) 平面插值
- 验证样本：粗网格搜索 MAP → χ²@MAP
- OoD 分数 = χ²（可转 -p 值）
- 评估：ID=干净新宇宙学, OoD=扰动新宇宙学, TPR@FPR（官方对数空间100点）
"""
import numpy as np, os, sys, time

DATA = 'wl_challenge/data/full'
KAPPA = f'{DATA}/kappa_full.npy'
MASK = f'{DATA}/WIDE12H_bin2_2arcmin_mask.npy'
LABEL = f'{DATA}/label_newrealization.npy'
SEED = 42
NG = 30.0          # 星系数密度 arcmin^-2
PIXEL_ARCMIN = 2.0
SIGMA_NOISE = 0.4 / (2 * NG * PIXEL_ARCMIN**2) ** 0.5   # 0.0258
N_BIN = 10
L_EDGE = np.logspace(2, 4, N_BIN + 1)
N_TRAIN_COSMO = 80
GRID_N = 30        # MAP 粗网格每维点数

def tpr_at_fpr_official(score_id, score_ood, labels=None):
    """官方评分：ROC 在 FPR∈[0.001,0.05] 对数空间 100 点平均 TPR"""
    from sklearn.metrics import roc_curve
    y = np.concatenate([np.zeros(len(score_id)), np.ones(len(score_ood))])
    s = np.concatenate([score_id, score_ood])
    fpr, tpr, _ = roc_curve(y, s)
    fpr_grid = np.logspace(np.log10(0.001), np.log10(0.05), 100)
    tpr_grid = np.interp(fpr_grid, fpr, tpr)
    return float(np.mean(tpr_grid))

def cohen_d(a, b):
    return (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2)

def power_spectrum(x, pixsize_radian, kedge):
    """官方功率谱函数（含实 FFT 对称修正），返回 (k_avg, P(k))"""
    xk = np.fft.rfft2(x)
    xk2 = (xk * xk.conj()).real
    Nmesh = x.shape
    k = np.zeros((Nmesh[0], Nmesh[1] // 2 + 1))
    k += np.fft.fftfreq(Nmesh[0], d=pixsize_radian).reshape(-1, 1) ** 2
    k += np.fft.rfftfreq(Nmesh[1], d=pixsize_radian).reshape(1, -1) ** 2
    k = k ** 0.5 * 2 * np.pi
    index = np.searchsorted(kedge, k)
    power = np.bincount(index.flatten(), weights=xk2.flatten(), minlength=len(kedge)+1)
    Nmode = np.bincount(index.flatten(), minlength=len(kedge)+1)
    power_k = np.bincount(index.flatten(), weights=k.flatten(), minlength=len(kedge)+1)
    if Nmesh[1] % 2 == 0:
        power += np.bincount(index[..., 1:-1].flatten(), weights=xk2[..., 1:-1].flatten(), minlength=len(kedge)+1)
        Nmode += np.bincount(index[..., 1:-1].flatten(), minlength=len(kedge)+1)
        power_k += np.bincount(index[..., 1:-1].flatten(), weights=k[..., 1:-1].flatten(), minlength=len(kedge)+1)
    else:
        power += np.bincount(index[..., 1:].flatten(), weights=xk2[..., 1:].flatten(), minlength=len(kedge)+1)
        Nmode += np.bincount(index[..., 1:].flatten(), minlength=len(kedge)+1)
        power_k += np.bincount(index[..., 1:].flatten(), weights=k[..., 1:].flatten(), minlength=len(kedge)+1)
    nz = Nmode > 0
    k_avg = np.zeros(len(kedge) + 1); P = np.zeros(len(kedge) + 1)
    k_avg[nz] = power_k[nz] / Nmode[nz]
    P[nz] = power[nz] / Nmode[nz]
    return k_avg[1:-1], P[1:-1]   # 去掉 DC 和越界 bin

def main():
    t0 = time.time()
    mask = np.load(MASK).astype(bool)
    ny, nx = mask.shape
    lab = np.load(LABEL)
    print(f'噪声 σ={SIGMA_NOISE:.5f}, l bin edges={L_EDGE[0]:.0f}..{L_EDGE[-1]:.0f}', flush=True)

    rng = np.random.default_rng(SEED)
    k = np.load(KAPPA, mmap_mode='r')
    nr, nimg, npix = k.shape
    train_idx = np.arange(N_TRAIN_COSMO)
    val_idx = np.arange(N_TRAIN_COSMO, nr)

    pixsize_radian = PIXEL_ARCMIN / 60 * np.pi / 180

    def logPS_batch(indices, perturb=None):
        """逐宇宙学算加噪功率谱，返回 (len(indices)*nimg, N_BIN) log10 P"""
        out = np.zeros((len(indices) * nimg, N_BIN), np.float32)
        p = 0
        for i in indices:
            v = np.asarray(k[i], dtype=np.float64)          # (256, 132019)
            full = np.zeros((nimg, ny, nx), np.float64)
            full[:, mask] = v
            if perturb is not None:
                full = perturb(full)
            else:
                full = full + rng.normal(0, SIGMA_NOISE, full.shape) * mask[None]
            for j in range(nimg):
                _, P = power_spectrum(full[j], pixsize_radian, L_EDGE)
                out[p + j] = np.log10(P + 1e-30)
            p += nimg
            if (i - indices[0]) % 20 == 0:
                print(f'  PS cosmo {i}/{indices[-1]} ({time.time()-t0:.0f}s)', flush=True)
        return out

    # 训练 logP
    print('训练功率谱...', flush=True)
    tr_logP = logPS_batch(train_idx)
    print(f'训练 logP {tr_logP.shape} ({time.time()-t0:.0f}s)', flush=True)

    # 每宇宙学均值/协方差
    tr_logP_c = tr_logP.reshape(len(train_idx), nimg, N_BIN)
    mu = tr_logP_c.mean(1)                                   # (80, 10)
    cov = np.zeros((len(train_idx), N_BIN, N_BIN))
    for i in range(len(train_idx)):
        d = tr_logP_c[i] - mu[i]
        cov[i] = d.T @ d / (nimg - N_BIN - 2)
    print(f'每宇宙学 μ/cov 完成 ({time.time()-t0:.0f}s)', flush=True)

    # 插值器（scipy）
    from scipy.interpolate import LinearNDInterpolator
    cosmo = lab[train_idx, 0, :2]
    mu_interp = LinearNDInterpolator(cosmo, mu, fill_value=np.nan)
    cov_interp = LinearNDInterpolator(cosmo, cov, fill_value=np.nan)

    # MAP 网格
    om_grid = np.linspace(cosmo[:, 0].min(), cosmo[:, 0].max(), GRID_N)
    s8_grid = np.linspace(cosmo[:, 1].min(), cosmo[:, 1].max(), GRID_N)
    Gx, Gy = np.meshgrid(om_grid, s8_grid, indexing='ij')
    grid_pts = np.stack([Gx.ravel(), Gy.ravel()], 1)
    mu_g = mu_interp(grid_pts)                                # (900, 10)
    cov_g = cov_interp(grid_pts)                              # (900, 10, 10)
    ok = np.isfinite(mu_g).all(1)
    inv_g = np.zeros_like(cov_g)
    for g in range(GRID_N**2):
        if ok[g]:
            inv_g[g] = np.linalg.inv(cov_g[g])
    print(f'MAP 网格 {GRID_N}² 就绪 ({time.time()-t0:.0f}s)', flush=True)

    def chi2_at_maps(logP_batch):
        """每样本：网格搜索 χ² 最小值（MAP χ²）"""
        n = len(logP_batch)
        chi2_min = np.full(n, np.inf)
        B = 512
        for s in range(0, n, B):
            b = logP_batch[s:s+B]                             # (b, 10)
            for g in range(GRID_N**2):
                if not ok[g]:
                    continue
                d = b - mu_g[g]
                c2 = np.einsum('ni,ij,nj->n', d, inv_g[g], d)
                np.minimum(chi2_min[s:s+B], c2, out=chi2_min[s:s+B])
        return chi2_min

    # 验证集（干净新宇宙学）
    print('验证功率谱（干净）...', flush=True)
    val_logP = logPS_batch(val_idx)
    val_chi2 = chi2_at_maps(val_logP)
    print(f'验证 χ² 完成 ({time.time()-t0:.0f}s)', flush=True)

    # 训练集自身 χ²（参考分布）
    tr_chi2 = chi2_at_maps(tr_logP)
    print(f'训练 χ² median={np.median(tr_chi2):.1f}, 验证 χ² median={np.median(val_chi2):.1f}', flush=True)
    print(f'种子敏感度: d={cohen_d(val_chi2, tr_chi2):+.2f} TPR@FPR={tpr_at_fpr_official(tr_chi2, val_chi2):.4f}', flush=True)

    # 扰动：物理模型差异代理（高斯模糊 = 分辨率/PSF 差异；额外噪声 = 观测条件差异）
    from scipy.ndimage import gaussian_filter
    def blur(sig):
        return lambda imgs: np.stack([gaussian_filter(im, sigma=sig) for im in imgs])
    def extra_noise(sig):
        return lambda imgs: imgs + rng.normal(0, sig, imgs.shape) * mask[None]

    perturbs = [
        ('模糊 σ=1px (PSF 差异)', blur(1.0)),
        ('模糊 σ=2px (PSF 差异)', blur(2.0)),
        ('额外噪声 σ=0.5σn', extra_noise(0.5 * SIGMA_NOISE)),
        ('额外噪声 σ=1.0σn', extra_noise(1.0 * SIGMA_NOISE)),
    ]
    print(f'\n扰动响应（ID=干净新宇宙学, OoD=扰动新宇宙学）:', flush=True)
    for name, pf in perturbs:
        Vp = logPS_batch(val_idx, perturb=pf)
        c2 = chi2_at_maps(Vp)
        d = cohen_d(c2, val_chi2)
        tpr = tpr_at_fpr_official(val_chi2, c2)
        print(f'  {name:26s} d={d:+.2f} TPR@FPR={tpr:.4f}', flush=True)

    np.savez(f'{DATA}/official_results.npz', tr_chi2=tr_chi2, val_chi2=val_chi2)
    print(f'DONE ({time.time()-t0:.0f}s)', flush=True)

if __name__ == '__main__':
    main()
