"""实验 A：可迁移性测试——扰动注入模拟真实 OoD，评估方法在真实语义下的判别力

修正设计：真实 Phase 2 中 ID = 干净模拟图（含新种子），OoD = 含系统效应图。
- ID 分数分布  = 干净验证集（21 个新 realization，无扰动）的重建误差
- OoD 分数分布 = 同一验证集注入扰动（噪声/缺陷/尺度）后的重建误差
- 指标：ROC 在 FPR∈[0.001,0.05] 的平均 TPR（Phase 2 评分）
- 参考：训练集自身分数（种子误报率底限）
"""
import numpy as np, os, sys, time

DATA = 'wl_challenge/data/full'
KAPPA = f'{DATA}/kappa_full.npy'
MASK = f'{DATA}/WIDE12H_bin2_2arcmin_mask.npy'
SEED = 42
N_SUB = 4000
N_TRAIN_REAL = 80
K = 3000

def tpr_at_fpr(score_id, score_ood, fpr_lo=0.001, fpr_hi=0.05, n=200):
    th = np.quantile(score_id, 1 - np.linspace(fpr_lo, fpr_hi, n))
    return float(np.mean([(score_ood > t).mean() for t in th]))

def cohen_d(a, b):
    return (b.mean() - a.mean()) / np.sqrt((a.var() + b.var()) / 2)

def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    mask = np.load(MASK).astype(bool)
    pix = rng.choice(mask.sum(), N_SUB, replace=False)
    k = np.load(KAPPA, mmap_mode='r')
    nr, nimg, npix = k.shape
    train_idx = np.arange(N_TRAIN_REAL)
    val_idx = np.arange(N_TRAIN_REAL, nr)

    X = np.stack([np.asarray(k[i, :, pix], dtype=np.float32) for i in train_idx])
    X = X.transpose(0, 2, 1).reshape(-1, N_SUB)
    V = np.stack([np.asarray(k[i, :, pix], dtype=np.float32) for i in val_idx])
    V = V.transpose(0, 2, 1).reshape(-1, N_SUB)
    print(f'[加载] 训练 {X.shape} 验证 {V.shape} ({time.time()-t0:.0f}s)', flush=True)

    mu = X.mean(0, keepdims=True)
    sd = X.std(0, keepdims=True); sd[sd == 0] = 1
    Xc = (X - mu) / sd
    Vc = (V - mu) / sd

    t0 = time.time()
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    print(f'[SVD] {S.size} 奇异值 ({time.time()-t0:.0f}s)', flush=True)
    Pk = Vt[:K].T

    def recon_err(Bc):
        rec = Bc - (Bc @ Pk) @ Pk.T
        return np.linalg.norm(rec, axis=1) / (np.linalg.norm(Bc, axis=1) + 1e-9)

    # 三个分数分布
    tr_score = recon_err(Xc)      # 训练集自身（种子误报底限参考）
    id_score = recon_err(Vc)      # 干净新种子 = 真实测试 ID 角色
    print(f'[参考] 种子敏感度: 干净验证 vs 训练 d={cohen_d(tr_score, id_score):+.2f} '
          f'TPR@FPR={tpr_at_fpr(tr_score, id_score):.4f}  ← 若高则方法会误报干净新种子', flush=True)

    # 扰动注入（像素域原始值 V 上做，再标准化打分）
    sigma_g = float(V.std())
    print(f'[信息] kappa 全局 std = {sigma_g:.4f}', flush=True)

    # 共享位置缺陷（系统性缺陷：所有图同一批像素被污染）
    def shared_defect(frac):
        idx = rng.choice(N_SUB, int(N_SUB * frac), replace=False)
        Vp = V.copy()
        Vp[:, idx] = 0.0
        return Vp

    perts = {
        '高斯噪声 σ=0.1σg': V + rng.normal(0, 0.1 * sigma_g, V.shape),
        '高斯噪声 σ=0.25σg': V + rng.normal(0, 0.25 * sigma_g, V.shape),
        '高斯噪声 σ=0.5σg': V + rng.normal(0, 0.5 * sigma_g, V.shape),
        '共享缺陷 5% 像素置0': shared_defect(0.05),
        '共享缺陷 10% 像素置0': shared_defect(0.10),
        '尺度 ×1.05': V * 1.05,
        '尺度 ×1.10': V * 1.10,
    }
    print()
    print(f'{"扰动":28s} {"d(vs 干净验证)":>14s} {"TPR@FPR":>10s}')
    for name, Vp in perts.items():
        Vpc = (Vp - mu) / sd
        ood_score = recon_err(Vpc)
        d = cohen_d(id_score, ood_score)
        tpr = tpr_at_fpr(id_score, ood_score)
        print(f'{name:28s} {d:>+14.2f} {tpr:>10.4f}', flush=True)

    # 保存（供 C 管道复用）
    np.savez(f'{DATA}/subspace_k{K}.npz', mu=mu, sd=sd, Pk=Pk, S=S,
             tr_score=tr_score, id_score=id_score)
    print('[保存] subspace_k3000.npz (mu/sd/Pk/S/分数)', flush=True)
    print('DONE', flush=True)

if __name__ == '__main__':
    main()
