"""WL Phase 2 基线 v3：重建误差主分数 + 多 k 对比 + 本地 ROC@FPR 指标

数据：(101, 256, 132019) float16
设计：
- N_SUB=4000 像素子采样（固定种子）
- leave-realization-out：80 训练 / 21 验证
- 一次 SVD 后对多个 k（主成分数）重算：
  重建误差（谱外，主分数）与马氏距离（谱内，参考）
- 指标：Cohen d + Phase 2 评分近似（ROC 在 FPR∈[0.001,0.05] 的平均 TPR）
"""
import numpy as np, os, sys, time

DATA = 'wl_challenge/data/full'
KAPPA = f'{DATA}/kappa_full.npy'
MASK = f'{DATA}/WIDE12H_bin2_2arcmin_mask.npy'
SEED = 42
N_SUB = 4000
N_TRAIN_REAL = 80
K_LIST = [100, 300, 500, 800, 1200, 2000, 3000, 3800]
FPR_LO, FPR_HI, N_THRESH = 0.001, 0.05, 200

def roc_avg_tpr(score_id, score_ood, n_thresh=N_THRESH):
    """ROC 在 FPR∈[0.001,0.05] 的平均 TPR（Phase 2 评分近似）"""
    fprs = np.linspace(FPR_LO, FPR_HI, n_thresh)
    thresh = np.quantile(score_id, 1 - fprs)
    tprs = np.array([(score_ood > t).mean() for t in thresh])
    return float(tprs.mean())

def load_subset(k, idx, pix, n_sub):
    """逐 realization 收集：标量索引避免广播失败与中间物化"""
    return np.stack([np.asarray(k[i, :, pix], dtype=np.float32) for i in idx]
                    ).transpose(0, 2, 1).reshape(-1, n_sub)

def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    mask = np.load(MASK).astype(bool)
    pix = rng.choice(mask.sum(), N_SUB, replace=False)
    print(f'[1] mask 有效 {mask.sum()}, 子采样 {N_SUB} ({(time.time()-t0):.0f}s)', flush=True)

    k = np.load(KAPPA, mmap_mode='r')
    nr, nimg, npix = k.shape
    print(f'[2] kappa: {nr} real × {nimg} 张 × {npix} px', flush=True)

    train_idx = np.arange(N_TRAIN_REAL)
    val_idx = np.arange(N_TRAIN_REAL, nr)

    t0 = time.time()
    X = load_subset(k, train_idx, pix, N_SUB)
    print(f'[3] 训练矩阵 {X.shape} ({time.time()-t0:.0f}s)', flush=True)

    t0 = time.time()
    V = load_subset(k, val_idx, pix, N_SUB)
    print(f'[4] 验证矩阵 {V.shape} ({time.time()-t0:.0f}s)', flush=True)

    mu = X.mean(0, keepdims=True)
    sd = X.std(0, keepdims=True); sd[sd == 0] = 1
    Xc = (X - mu) / sd
    Vc = (V - mu) / sd
    del X, V

    t0 = time.time()
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    print(f'[5] SVD 完成 {S.size} 奇异值 ({time.time()-t0:.0f}s)', flush=True)
    var = S**2 / (Xc.shape[0] - 1)
    cum = np.cumsum(var) / var.sum()

    proj_tr = Xc @ Vt.T
    proj_va = Vc @ Vt.T
    norm_tr = np.linalg.norm(Xc, axis=1)
    norm_va = np.linalg.norm(Vc, axis=1)

    print(f'\n{"k":>5} {"var%":>7} {"recon d":>8} {"TPR@FPR":>9} {"md TPR":>8}')
    for kk in K_LIST:
        if kk > S.size:
            continue
        Pk = Vt[:kk].T
        rec_tr = Xc - (Xc @ Pk) @ Pk.T
        rec_va = Vc - (Vc @ Pk) @ Pk.T
        rerr_tr = np.linalg.norm(rec_tr, axis=1) / (norm_tr + 1e-9)
        rerr_va = np.linalg.norm(rec_va, axis=1) / (norm_va + 1e-9)
        d = (rerr_va.mean() - rerr_tr.mean()) / np.sqrt((rerr_va.var() + rerr_tr.var()) / 2)
        tpr = roc_avg_tpr(rerr_tr, rerr_va)
        md_tr = ((proj_tr[:, :kk]**2) / var[:kk]).sum(1)
        md_va = ((proj_va[:, :kk]**2) / var[:kk]).sum(1)
        tpr_md = roc_avg_tpr(md_tr, md_va)
        print(f'{kk:5d} {cum[kk-1]*100:6.1f}% {d:+8.2f} {tpr:9.4f} {tpr_md:8.4f}', flush=True)

    # 保存最优（按 TPR）配置的训练/验证分数，供后续融合
    best = None
    for kk in K_LIST:
        if kk > S.size: continue
        Pk = Vt[:kk].T
        rec_va = Vc - (Vc @ Pk) @ Pk.T
        rerr_va = np.linalg.norm(rec_va, axis=1) / (norm_va + 1e-9)
        rec_tr = Xc - (Xc @ Pk) @ Pk.T
        rerr_tr = np.linalg.norm(rec_tr, axis=1) / (norm_tr + 1e-9)
        tpr = roc_avg_tpr(rerr_tr, rerr_va)
        if best is None or tpr > best[0]:
            best = (tpr, kk, rerr_tr, rerr_va)
    tpr_b, kk_b, rerr_tr_b, rerr_va_b = best
    np.save(f'{DATA}/tr_recon_k{kk_b}.npy', rerr_tr_b)
    np.save(f'{DATA}/val_recon_k{kk_b}.npy', rerr_va_b)
    print(f'\n最佳: k={kk_b} TPR@FPR={tpr_b:.4f}，分数已保存', flush=True)

if __name__ == '__main__':
    main()
