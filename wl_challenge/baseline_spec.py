"""谱特征基线 A'：径向功率谱形状 + 马氏距离 OoD 检测

语义（修正版）：ID = 干净新种子（未训练 realization 的干净图），OoD = 扰动注入图
评估：ROC 在 FPR∈[0.001,0.05] 的平均 TPR（Phase 2 评分指标）

谱几何动机：种子差异集中在低频/整体幅度；系统效应（噪声/缺陷/PSF）有特定尺度指纹。
总功率归一化 → 谱形状特征 → 对全局尺度鲁棒。
"""
import numpy as np, os, sys, time

DATA = 'wl_challenge/data/full'
KAPPA = f'{DATA}/kappa_full.npy'
MASK = f'{DATA}/WIDE12H_bin2_2arcmin_mask.npy'
SEED = 42
N_TRAIN_REAL = 80
N_BIN = 32
BATCH = 256
REG = 1e-6


def tpr_at_fpr(score_id, score_ood, fpr_lo=0.001, fpr_hi=0.05, n=200):
    th = np.quantile(score_id, 1 - np.linspace(fpr_lo, fpr_hi, n))
    return float(np.mean([(score_ood > t).mean() for t in th]))


def cohen_d(a, b):
    return (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2)


def main():
    t0 = time.time()
    mask = np.load(MASK).astype(bool)
    ny, nx = mask.shape
    k = np.load(KAPPA, mmap_mode='r')
    nr, nimg, npix = k.shape
    print(f'kappa {nr}x{nimg}x{npix}, mask {ny}x{nx} 有效 {mask.sum()}', flush=True)

    # rfft2 频率坐标 + 径向 bin（预计算，只算一次）
    u = np.arange(ny); u = np.where(u > ny // 2, u - ny, u)
    v = np.arange(nx // 2 + 1)
    U, V = np.meshgrid(u, v, indexing='ij')
    R = np.sqrt(U.astype(np.float32) ** 2 + V.astype(np.float32) ** 2)
    rmax = R.max()
    bin_idx = np.clip((R / (rmax + 1e-6) * N_BIN).astype(np.int32), 0, N_BIN - 1).ravel()
    cnts = np.bincount(bin_idx, minlength=N_BIN)

    def spec_batch(vecs):
        """vecs: (B, npix) float32 -> (B, N_BIN) 谱特征（总功率归一 + log）"""
        B = vecs.shape[0]
        out = np.zeros((B, N_BIN), np.float32)
        for s in range(0, B, BATCH):
            b = vecs[s:s + BATCH]
            full = np.zeros((b.shape[0], ny, nx), np.float32)
            full[:, mask] = b
            F = np.fft.rfft2(full)
            ps = np.abs(F) ** 2
            ps = ps.reshape(ps.shape[0], -1)
            sums = np.array([np.bincount(bin_idx, weights=p, minlength=N_BIN) for p in ps])
            ps_b = sums / np.maximum(cnts, 1)
            tot = ps_b.sum(axis=1, keepdims=True)
            out[s:s + BATCH] = np.log(ps_b / (tot + 1e-30) + 1e-12)
        return out

    def spec_all(indices, perturb=None):
        out = np.zeros((len(indices) * nimg, N_BIN), np.float32)
        p = 0
        for i in indices:
            v = np.asarray(k[i], dtype=np.float32)
            if perturb is not None:
                v = perturb(v)
            out[p:p + nimg] = spec_batch(v)
            p += nimg
            print(f'  realization {i} done ({time.time()-t0:.0f}s)', flush=True)
        return out

    train_idx = np.arange(N_TRAIN_REAL)
    val_idx = np.arange(N_TRAIN_REAL, nr)

    print('训练谱特征（80 realizations）...', flush=True)
    tr_spec = spec_all(train_idx)
    print(f'训练谱 {tr_spec.shape} ({time.time()-t0:.0f}s)', flush=True)

    print('验证谱特征（21 realizations，干净）...', flush=True)
    val_spec = spec_all(val_idx)
    print(f'验证谱 {val_spec.shape} ({time.time()-t0:.0f}s)', flush=True)

    # 校准：训练均值/协方差 -> 马氏距离
    mu = tr_spec.mean(0)
    Xc = tr_spec - mu
    cov = (Xc.T @ Xc) / (len(tr_spec) - 1)
    cov_reg = cov + REG * np.trace(cov) / N_BIN * np.eye(N_BIN)
    inv = np.linalg.inv(cov_reg)

    def mahal(spec):
        d = spec - mu
        return np.sqrt(np.einsum('ij,jk,ik->i', d, inv, d))

    tr_score = mahal(tr_spec)
    id_score = mahal(val_spec)
    print(f'\n种子敏感度: 干净验证 vs 训练 d={cohen_d(id_score, tr_score):+.2f} TPR@FPR={tpr_at_fpr(tr_score, id_score):.4f}', flush=True)

    # 扰动（全像素域，逐 realization 注入）
    sigma_g = float(np.asarray(k[val_idx[0]], dtype=np.float32).std())
    print(f'kappa 全局 std ≈ {sigma_g:.4f}', flush=True)
    rng = np.random.default_rng(SEED + 1)
    n_def5 = int(npix * 0.05)
    n_def10 = int(npix * 0.10)
    idx5 = rng.choice(npix, n_def5, replace=False)
    idx10 = rng.choice(npix, n_def10, replace=False)

    def defect(v, idx):
        v = v.copy()
        v[:, idx] = 0
        return v

    perturbs = [
        ('高斯噪声 0.1σ', lambda v: v + rng.normal(0, 0.1 * sigma_g, v.shape)),
        ('高斯噪声 0.25σ', lambda v: v + rng.normal(0, 0.25 * sigma_g, v.shape)),
        ('高斯噪声 0.5σ', lambda v: v + rng.normal(0, 0.5 * sigma_g, v.shape)),
        ('共享缺陷 5%', lambda v: defect(v, idx5)),
        ('共享缺陷 10%', lambda v: defect(v, idx10)),
        ('尺度 ×1.05', lambda v: v * 1.05),
        ('尺度 ×1.10', lambda v: v * 1.10),
    ]

    print(f'\n扰动响应（ID=干净验证, OoD=扰动验证）:', flush=True)
    for name, f in perturbs:
        Vp_spec = spec_all(val_idx, perturb=f)
        ood = mahal(Vp_spec)
        d = cohen_d(ood, id_score)
        tpr = tpr_at_fpr(id_score, ood)
        print(f'  {name:18s} d={d:+.2f} TPR@FPR={tpr:.4f}', flush=True)

    np.savez(f'{DATA}/spec_results.npz', tr_score=tr_score, id_score=id_score, mu=mu, inv=inv)
    print('ALL DONE', flush=True)


if __name__ == '__main__':
    main()
