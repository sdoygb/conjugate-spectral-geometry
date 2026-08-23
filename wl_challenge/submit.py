#!/usr/bin/env python3
"""submit.py — Weak Lensing Phase 2 正式提交管道

方法：官方 χ²@MAP（功率谱 10 bin + (Ωm,S₈) 插值仿真器 + 网格 MAP 搜索）
已验证（leave-cosmology-out）：种子敏感度 d=+0.11，扰动 TPR@FPR=1.00

用法：
  python3 submit.py --train [--ncosmo 101] [--grid 30] [--ckpt ckpt.npz]
      # 训练阶段：加噪 → 功率谱 → 每宇宙学 μ/Cov → 插值器 → checkpoint（慢，一次）
  python3 submit.py --score --test <test.npy> [--ckpt ckpt.npz] [--out result.json] [--zip]
      # 打分阶段：测试图（已带噪）→ 功率谱 → 网格 MAP → χ² → result.json
  python3 submit.py --test <test.npy> [--ncosmo 3] [--grid 10]
      # 管道自测：小规模训练 + 打分一步（验证格式/流程）

输出：result.json {"ood_scores": [Ntest 个分数]}（分数 = χ²@MAP，高分 = OoD；
ROC 只依赖排序，χ² 与官方 -p 值单调等价）
"""
import numpy as np, os, sys, time, json, zipfile, argparse
from scipy.interpolate import LinearNDInterpolator

# ---------------- 配置 ----------------
DATA = 'wl_challenge/data/full'
KAPPA = f'{DATA}/kappa_full.npy'
LABEL = f'{DATA}/label_newrealization.npy'
MASK = f'{DATA}/WIDE12H_bin2_2arcmin_mask.npy'
SEED = 42
N_BIN = 10
L_EDGE = np.logspace(2, 4, N_BIN + 1)      # multipole bins [100, 10000]
NG, PIXEL = 30, 2.0                        # arcmin^-2, arcmin
SIGMA_EPS = 0.4
PIXEL_RAD = PIXEL * np.pi / (180 * 60)     # 像素弧度
NOISE_SIGMA = SIGMA_EPS / np.sqrt(2 * NG * PIXEL**2)   # 0.02582
BATCH = 256

# ---------------- 功率谱 ----------------
def make_binner(mask):
    """频率网格 + l bin 索引（multipole，含 2π）"""
    ny, nx = mask.shape
    kx = np.fft.fftfreq(nx, d=PIXEL_RAD)
    ky = np.fft.fftfreq(ny, d=PIXEL_RAD)
    K = np.sqrt(kx[None, :]**2 + ky[:, None]**2) * (2 * np.pi)
    index = np.searchsorted(L_EDGE, K)     # 0..N_BIN（N_BIN = 越界）
    return K, index

def power_spectrum_batch(full, K, index):
    """full: (B, ny, nx) float32 → (B, N_BIN) log10 功率谱（均值 bin）"""
    B = full.shape[0]
    F = np.fft.fft2(full)
    xk2 = np.abs(F)**2
    xk2 *= 2.0
    xk2[:, :, 0] /= 2.0
    xk2[:, :, -1] /= 2.0
    kidx = index.ravel()
    kavg = K.ravel()
    out = np.zeros((B, N_BIN), np.float32)
    for b in range(B):
        p = xk2[b].ravel()
        power = np.bincount(kidx, weights=p, minlength=N_BIN + 2)
        nmode = np.bincount(kidx, minlength=N_BIN + 2)
        pk = np.bincount(kidx, weights=kavg, minlength=N_BIN + 2)
        nz = nmode > 0
        P = np.zeros(N_BIN + 2)
        P[nz] = power[nz] / nmode[nz]
        out[b] = np.log10(P[1:-1])         # 去 DC 和越界 bin
    return out

def spec_all(kappa, mask, indices, rng):
    """指定宇宙学：加噪 → 谱 → (Ncos*Nsim, N_BIN) log10PS"""
    ny, nx = mask.shape
    K, index = make_binner(mask)
    nsim, npix = kappa.shape[1], kappa.shape[2]
    out = np.zeros((len(indices) * nsim, N_BIN), np.float32)
    t0 = time.time()
    for ci, c in enumerate(indices):
        noisy = np.asarray(kappa[c], np.float32) + rng.normal(0, NOISE_SIGMA, (nsim, npix)).astype(np.float32)
        for s in range(0, nsim, BATCH):
            batch = noisy[s:s+BATCH]
            full = np.zeros((len(batch), ny, nx), np.float32)
            full[:, mask] = batch
            out[ci*nsim+s:ci*nsim+s+len(batch)] = power_spectrum_batch(full, K, index)
        if ci % 10 == 0 or ci == len(indices) - 1:
            print(f'  PS cosmo {ci+1}/{len(indices)} ({time.time()-t0:.0f}s)', flush=True)
    return out

def spec_test(test_vecs, mask):
    """测试图（已带噪）→ (N, N_BIN) log10PS"""
    ny, nx = mask.shape
    K, index = make_binner(mask)
    N = test_vecs.shape[0]
    out = np.zeros((N, N_BIN), np.float32)
    t0 = time.time()
    for s in range(0, N, BATCH):
        batch = np.asarray(test_vecs[s:s+BATCH], np.float32)
        full = np.zeros((len(batch), ny, nx), np.float32)
        full[:, mask] = batch
        out[s:s+len(batch)] = power_spectrum_batch(full, K, index)
        if s % (5*BATCH) == 0:
            print(f'  PS {min(s+BATCH,N)}/{N} ({time.time()-t0:.0f}s)', flush=True)
    return out

# ---------------- 训练 ----------------
def train(ncosmo, grid_size, ckpt_path):
    t0 = time.time()
    mask = np.load(MASK).astype(bool)
    kappa = np.load(KAPPA, mmap_mode='r')
    label = np.load(LABEL)                     # (101, 256, 5)
    idx = np.arange(ncosmo)
    lab0 = label[idx, 0, :2]                    # 训练宇宙学 (Ωm, S₈)
    rng = np.random.default_rng(SEED)
    print(f'[train] {ncosmo} 宇宙学, 加噪 σ={NOISE_SIGMA:.5f}, grid {grid_size}²', flush=True)

    logPS = spec_all(kappa, mask, idx, rng)    # (ncosmo*256, 10)
    nsim = 256
    mu = logPS.reshape(ncosmo, nsim, N_BIN).mean(1)          # (ncosmo, 10)
    Cov = np.zeros((ncosmo, N_BIN, N_BIN))
    for c in range(ncosmo):
        d = logPS[c*nsim:(c+1)*nsim] - mu[c]
        Cov[c] = (d.T @ d) / (nsim - 1)

    interp_mu = LinearNDInterpolator(lab0, mu)
    interp_cov = LinearNDInterpolator(lab0, Cov.reshape(ncosmo, -1))

    om_g = np.linspace(lab0[:, 0].min(), lab0[:, 0].max(), grid_size)
    s8_g = np.linspace(lab0[:, 1].min(), lab0[:, 1].max(), grid_size)
    Om, S8 = np.meshgrid(om_g, s8_g)
    grid = np.stack([Om.ravel(), S8.ravel()], 1)
    mu_g = interp_mu(grid)
    cov_g = interp_cov(grid).reshape(-1, N_BIN, N_BIN)
    inv_g = np.linalg.inv(cov_g)

    np.savez(ckpt_path, grid=grid, mu_g=mu_g, inv_g=inv_g)
    print(f'[train] checkpoint → {ckpt_path} ({time.time()-t0:.0f}s)', flush=True)

# ---------------- 打分 ----------------
def chi2_grid(logPS, ckpt, batch=512):
    mu_g, inv_g = ckpt['mu_g'], ckpt['inv_g']
    n = len(logPS)
    chi2 = np.zeros(n)
    valid = ~np.isnan(mu_g[:, 0])
    for s in range(0, n, batch):
        x = logPS[s:s+batch]
        d = x[:, None, :] - mu_g[None]          # (B, G, 10)
        c = np.full((len(x), len(mu_g)), np.inf)
        c[:, valid] = np.einsum('bgi,gij,bgj->bg', d[:, valid], inv_g[valid], d[:, valid])
        chi2[s:s+len(x)] = c.min(1)
    return chi2

def score(test_path, ckpt_path, out_path, make_zip=False):
    t0 = time.time()
    ckpt = np.load(ckpt_path, allow_pickle=True)
    mask = np.load(MASK).astype(bool)
    t = np.load(test_path, mmap_mode='r')       # (Ntest, 132019) float16
    Ntest = t.shape[0]
    print(f'[score] 测试集 {t.shape}, 功率谱...', flush=True)
    logPS = spec_test(t, mask)
    print(f'[score] χ² 网格搜索 ({time.time()-t0:.0f}s)...', flush=True)
    chi2 = chi2_grid(logPS, ckpt)
    ood = chi2.astype(np.float64)
    with open(out_path, 'w') as f:
        json.dump({"ood_scores": ood.tolist()}, f)
    print(f'[score] → {out_path}  χ² min={chi2.min():.2f} median={np.median(chi2):.2f} max={chi2.max():.2f} ({time.time()-t0:.0f}s)', flush=True)
    if make_zip:
        zp = out_path.replace('.json', '.zip')
        with zipfile.ZipFile(zp, 'w') as z:
            z.write(out_path, arcname='result.json')
        print(f'[score] → {zp}', flush=True)

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train', action='store_true', help='训练阶段（构建插值器 checkpoint）')
    ap.add_argument('--score', action='store_true', help='打分阶段（需 --test）')
    ap.add_argument('--ncosmo', type=int, default=101)
    ap.add_argument('--grid', type=int, default=30)
    ap.add_argument('--ckpt', default='wl_challenge/ckpt_official.npz')
    ap.add_argument('--test', default='')
    ap.add_argument('--out', default='wl_challenge/result.json')
    ap.add_argument('--zip', action='store_true')
    args = ap.parse_args()

    if args.train:
        train(args.ncosmo, args.grid, args.ckpt)
    if args.score:
        if not os.path.exists(args.ckpt):
            print('[错误] checkpoint 不存在，先跑 --train', file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(args.test):
            print(f'[错误] 测试集不存在: {args.test}', file=sys.stderr)
            sys.exit(1)
        score(args.test, args.ckpt, args.out, make_zip=args.zip)
    if not args.train and not args.score:
        # 管道自测：小规模训练 + 打分
        print('[pipeline-test] 小规模验证（3 宇宙学, grid 10）', flush=True)
        train(min(args.ncosmo, 3), min(args.grid, 10), args.ckpt)
        score(args.test, args.ckpt, args.out, make_zip=args.zip)

if __name__ == '__main__':
    main()
