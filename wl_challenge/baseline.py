"""WL Phase 2 基线 v2：子空间 OoD 检测（子采样 PCA + 马氏距离 + 重建误差）

数据：(101, 256, 132019) float16 —— 101 realizations × 256 张 × 132019 有效像素
任务：给每个测试样本连续 OoD 分数，评分 = ROC 在 FPR∈[0.001,0.05] 的平均 TPR

基线策略：
1. 像素子采样（固定种子 1500 像素）降维（全像素 SVD 不可行）
2. 训练集标准化 + PCA（保留 95% 方差）——PCA 本征值谱 = 数据谱结构
3. OoD 分数 = 马氏距离²（谱内偏离）+ 重建误差（谱外成分）
4. 本地验证：leave-realization-out（80/21）——新 realization = 伪 OoD，
   检验分数能否捕获 realization 级系统效应（Phase 2 语义：测试含未知系统效应）

用法：
  python3 wl_challenge/baseline.py --inspect    # 侦察文件
  python3 wl_challenge/baseline.py              # 跑基线验证
"""
import numpy as np
import os
import sys
import time

DATA = 'wl_challenge/data/full'
KAPPA = f'{DATA}/kappa_full.npy'
MASK = f'{DATA}/WIDE12H_bin2_2arcmin_mask.npy'
LABEL = f'{DATA}/label_newrealization.npy'
TEST = f'{DATA}/WIDE12H_bin2_2arcmin_kappa_test_phase2_new.npy'
SEED = 42
N_SUB = 1500          # 子采样像素数
N_TRAIN_REAL = 80     # 训练 realizations 数


def inspect():
    for name, path in [('kappa', KAPPA), ('mask', MASK), ('label', LABEL), ('test', TEST)]:
        if not os.path.exists(path):
            print(f'{name:6s} 缺失: {path}')
            continue
        a = np.load(path, mmap_mode='r')
        print(f'{name:6s} shape={a.shape} dtype={a.dtype} {os.path.getsize(path)/1e9:.2f}GB')
        del a


def main():
    mask = np.load(MASK).astype(bool)
    rng = np.random.default_rng(SEED)
    pix = rng.choice(mask.sum(), N_SUB, replace=False)
    print(f'mask 有效像素 {mask.sum()}, 子采样 {N_SUB} 像素')

    k = np.load(KAPPA, mmap_mode='r')
    nr, nimg, npix = k.shape
    print(f'kappa: {nr} realizations x {nimg} 张 x {npix} 像素, dtype={k.dtype}')

    train_idx = np.arange(N_TRAIN_REAL)
    val_idx = np.arange(N_TRAIN_REAL, nr)
    print(f'训练 {len(train_idx)} realizations ({len(train_idx)*nimg} 张), '
          f'验证 {len(val_idx)} realizations ({len(val_idx)*nimg} 张)')

    # 训练子采样矩阵 + 标准化
    t0 = time.time()
    X = np.asarray(k[train_idx][:, :, pix], dtype=np.float32)
    X = X.reshape(-1, N_SUB)
    mu = X.mean(axis=0, keepdims=True)
    sd = X.std(axis=0, keepdims=True)
    sd[sd == 0] = 1.0
    X = (X - mu) / sd
    print(f'训练矩阵 {X.shape} float32, 构建耗时 {time.time()-t0:.0f}s')

    # PCA（本征值谱 = 数据的谱结构）
    t0 = time.time()
    Xc = X - X.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    var = S ** 2 / (Xc.shape[0] - 1)
    cum = np.cumsum(var) / var.sum()
    kk = int(np.searchsorted(cum, 0.95)) + 1
    print(f'PCA 保留 {kk}/{N_SUB} 维 (95% 方差), 耗时 {time.time()-t0:.0f}s')
    P = Vt[:kk].T
    eig = var[:kk]
    center = Xc.mean(axis=0, keepdims=True)

    def score_batch(B):
        Bc = B - center
        proj = Bc @ P
        md2 = (proj ** 2 / eig).sum(axis=1)
        rec = Bc - proj @ P.T
        rerr = np.linalg.norm(rec, axis=1) / (np.linalg.norm(Bc, axis=1) + 1e-9)
        return md2, rerr

    # 分布内参考（训练集自身）
    md2_tr, rerr_tr = score_batch(Xc)
    # 伪 OoD（新 realization）
    V = np.asarray(k[val_idx][:, :, pix], dtype=np.float32).reshape(-1, N_SUB)
    V = (V - mu) / sd
    md2_va, rerr_va = score_batch(V)

    print(f'\n马氏距离^2: 训练 median={np.median(md2_tr):.1f} mean={md2_tr.mean():.1f} '
          f'| 验证 median={np.median(md2_va):.1f} mean={md2_va.mean():.1f}')
    print(f'重建误差:    训练 median={np.median(rerr_tr):.4f} mean={rerr_tr.mean():.4f} '
          f'| 验证 median={np.median(rerr_va):.4f} mean={rerr_va.mean():.4f}')

    # 效应量（Cohen's d，不用 scipy）
    def cohens_d(a, b):
        na, nb = len(a), len(b)
        sp = np.sqrt(((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2) / (na + nb - 2))
        return (b.mean() - a.mean()) / sp if sp > 0 else 0.0

    d_md2 = cohens_d(md2_tr, md2_va)
    d_re = cohens_d(rerr_tr, rerr_va)
    print(f'\nCohen d (验证 vs 训练): 马氏距离^2 = {d_md2:+.2f}, 重建误差 = {d_re:+.2f}')
    print('解读: d 明显 > 0 表示新 realization 的系统效应可被分数捕获（管道有效）；')
    print('      d ≈ 0 表示子空间对 realization 差异不敏感（需换特征）。')

    np.save(f'{DATA}/val_md2.npy', md2_va)
    np.save(f'{DATA}/val_recon.npy', rerr_va)
    print('验证分数已保存: val_md2.npy, val_recon.npy')


if __name__ == '__main__':
    if '--inspect' in sys.argv:
        inspect()
    else:
        main()
