#!/usr/bin/env python3
"""G1：端到端几何管道——代数作用量 OoD 检测。

管道（头尾标准，中间几何论）:
  κ 图（标准）→ log10 P(l) 10 bin（标准统计量，l∈[100,10^4]）
  → sin²θ_i = P_i/Σ_j P_j（占比归一化）
  → S = Σ_i 1/sin²θ_i（代数作用量，10.8 §2 定义）
  → S̃ = S/n²（无标度化）
  → 分数 f = |S̃ - μ_train|（双侧偏离训练分布）
  → TPR@FPR（官方评估协议，FPR∈[0.001,0.05] 对数 100 点）

预言（数据前固定，判据写死）:
  P1  训练集加噪 κ 图的 S̃ 中位数 ∈ (1, 2)      [谱条件无标度化窗口]
  P2  纯白噪声图 S̃ 显著小于信号图（Jensen 下界趋于 1）
  P3  extra_noise 扰动 → S̃ 中位数减小（向白噪声退化）
  P4  blur 扰动 → S̃ 中位数增大（谱变陡 → 不均匀度增）
  P5  干净新宇宙学弱分离（tpr < 0.7 且低于所有扰动 tpr，结构同官方 d=+0.11）

假设（明示）:
  H1  谱条件 (100<S<200) 从观测者位置推广到场统计量作用量 —— 无定理支撑，
      本脚本即 H1 的检验：P1 失败则 H1 关闭（但 z/双侧分数检测仍可评估）。

纪律:
  - rng 消耗顺序与基线完全一致（训练→验证→blur×2 不消耗→extra_noise×2 消耗），
    保证与基线使用相同的加噪图，对比公平。
  - 训练集只用于标定 μ_train 与 P1 检验；测试集（21 新宇宙学 + 4 扰动）不参与任何标定。
"""
import json
import os
import sys
import time

import numpy as np
from scipy.ndimage import gaussian_filter
from sklearn.metrics import roc_curve

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "wl_challenge", "data", "full")
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "g1_pipeline"
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kappa_lab.stats.powerspectrum import SIGMA_NOISE, power_spectrum

SEED = 42
PIXEL_ARCMIN = 2.0
N_BIN = 10
L_EDGE = np.logspace(2, 4, N_BIN + 1)
N_TRAIN_COSMO = 80
PIXSIZE = PIXEL_ARCMIN / 60 * np.pi / 180
WINDOW = (1.0, 2.0)  # 谱条件无标度化：S̃ ∈ (1,2)


def tpr_at_fpr(score_id, score_ood):
    """官方评估协议：TPR 在 FPR∈[0.001,0.05] 对数 100 点平均。"""
    y = np.concatenate([np.zeros(len(score_id)), np.ones(len(score_ood))])
    s = np.concatenate([score_id, score_ood])
    fpr, tpr, _ = roc_curve(y, s)
    grid = np.logspace(np.log10(0.001), np.log10(0.05), 100)
    return float(np.mean(np.interp(grid, fpr, tpr)))


def cohen_d(a, b):
    return (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2)


def geo_encode(P_batch):
    """线性功率 (N, N_BIN) → 代数作用量 S̃ (N,)。

    sin²θ_i = P_i/ΣP；S = Σ 1/sin²θ_i；S̃ = S/n²。
    Jensen: S ≥ n²/Σsin²θ = n²，等号当且仅当谱均匀（白噪声）→ S̃ ≥ 1。
    """
    norm = P_batch.sum(1, keepdims=True)
    s2 = P_batch / np.maximum(norm, 1e-30)  # sin²θ_i
    S = (1.0 / np.maximum(s2, 1e-30)).sum(1)
    return S / (N_BIN**2)


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    mask = np.load(os.path.join(DATA, "WIDE12H_bin2_2arcmin_mask.npy")).astype(bool)
    ny, nx = mask.shape
    lab = np.load(os.path.join(DATA, "label_newrealization.npy"))
    rng = np.random.default_rng(SEED)
    kpath = os.path.join(DATA, "kappa_full.npy")
    if not os.path.exists(kpath):
        kpath = os.path.join(DATA, "WIDE12H_bin2_2arcmin_kappa_newrealization.npy")
    k = np.load(kpath, mmap_mode="r")
    nr, nimg, npix = k.shape
    assert (nr, nimg, npix) == (101, 256, 132019), k.shape
    train_idx = np.arange(N_TRAIN_COSMO)
    val_idx = np.arange(N_TRAIN_COSMO, nr)
    print(f"G1 几何管道 | 数据 {kpath.split('/')[-1]} | {nr}×{nimg} 图", flush=True)

    def logPS_batch(indices, perturb=None):
        """与基线相同的 rng 消耗顺序；返回线性功率 (N, N_BIN)。"""
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
                out[p + j] = P
            p += nimg
            if (i - indices[0]) % 20 == 0:
                print(f"  PS cosmo {i}/{indices[-1]} ({time.time()-t0:.0f}s)", flush=True)
        return out

    def blur(sig):
        return lambda imgs: np.stack([gaussian_filter(im, sigma=sig) for im in imgs])

    def extra_noise(sig):
        return lambda imgs: imgs + rng.normal(0, sig, imgs.shape) * mask[None]

    print("训练集功率谱（80×256）...", flush=True)
    tr_P = logPS_batch(train_idx)
    tr_S = geo_encode(tr_P)
    mu_tr = float(np.mean(tr_S))
    print("验证集功率谱（21×256 干净）...", flush=True)
    val_P = logPS_batch(val_idx)
    val_S = geo_encode(val_P)

    med_tr = float(np.median(tr_S))
    q_tr = np.percentile(tr_S, [16, 84])
    med_val = float(np.median(val_S))
    q_val = np.percentile(val_S, [16, 84])
    print(f"训练 S̃: 中位数={med_tr:.4f} [16,84]%=[{q_tr[0]:.4f},{q_tr[1]:.4f}]", flush=True)
    print(f"验证 S̃: 中位数={med_val:.4f} [16,84]%=[{q_val[0]:.4f},{q_val[1]:.4f}]", flush=True)

    p1 = WINDOW[0] <= med_tr <= WINDOW[1]
    print(f"P1 训练 S̃ 中位数∈(1,2): {'通过' if p1 else '失败'}", flush=True)

    # P2: 纯白噪声（独立 rng，不干扰主序列）
    rng2 = np.random.default_rng(12345)
    nw = 200
    wS = np.zeros(nw)
    for i in range(nw):
        noise = rng2.normal(0, SIGMA_NOISE, (ny, nx)) * mask
        _, P = power_spectrum(noise, PIXSIZE, L_EDGE)
        wS[i] = geo_encode(P[None])[0]
    med_w = float(np.median(wS))
    p2 = med_w < med_tr
    print(f"P2 纯白噪声 S̃: 中位数={med_w:.4f} vs 信号 {med_tr:.4f}: {'通过' if p2 else '失败'}", flush=True)

    # 双侧分数（训练集标定 μ，测试集不参与）
    f_tr = np.abs(tr_S - mu_tr)
    f_val = np.abs(val_S - mu_tr)

    metrics = {
        "P1": bool(p1), "P2": bool(p2), "P3": None, "P4": None, "P5": None,
        "H1": bool(p1),  # H1 与 P1 同一检验
        "train_S_tilde": {"median": med_tr, "mean": mu_tr, "q16": float(q_tr[0]), "q84": float(q_tr[1])},
        "val_S_tilde": {"median": med_val, "q16": float(q_val[0]), "q84": float(q_val[1])},
        "white_noise_S_tilde": {"median": med_w},
        "perturbs": {}, "seed": {}, "timing_s": {},
    }

    # 扰动（保持 rng 顺序：blur 不消耗、extra_noise 消耗）
    for name, pf in [
        ("blur_1px", blur(1.0)),
        ("blur_2px", blur(2.0)),
        ("extra_noise_0.5sn", extra_noise(0.5 * SIGMA_NOISE)),
        ("extra_noise_1.0sn", extra_noise(1.0 * SIGMA_NOISE)),
    ]:
        print(f"扰动 {name}...", flush=True)
        Vp = logPS_batch(val_idx, perturb=pf)
        Sp = geo_encode(Vp)
        med_p = float(np.median(Sp))
        direction = (med_p > med_val) if name.startswith("blur") else (med_p < med_val)
        f_p = np.abs(Sp - mu_tr)
        tpr = tpr_at_fpr(f_val, f_p)
        d = cohen_d(f_p, f_val)
        metrics["perturbs"][name] = {
            "median_S_tilde": med_p, "direction_ok": bool(direction), "d": float(d), "tpr_at_fpr": tpr,
        }
        print(f"  {name:24s} S̃中位={med_p:.4f} d={d:+.2f} TPR@FPR={tpr:.4f} 方向{'对' if direction else '错'}", flush=True)

    p3 = all(metrics["perturbs"][n]["direction_ok"] for n in ["extra_noise_0.5sn", "extra_noise_1.0sn"])
    p4 = all(metrics["perturbs"][n]["direction_ok"] for n in ["blur_1px", "blur_2px"])
    metrics["P3"], metrics["P4"] = bool(p3), bool(p4)
    print(f"P3 extra_noise→S̃减小: {'通过' if p3 else '失败'} | P4 blur→S̃增大: {'通过' if p4 else '失败'}", flush=True)

    # P5: 种子敏感度（干净新宇宙学 vs 训练）
    d_seed = cohen_d(f_val, f_tr)
    tpr_seed = tpr_at_fpr(f_tr, f_val)
    min_perturb_tpr = min(m["tpr_at_fpr"] for m in metrics["perturbs"].values())
    p5 = (tpr_seed < 0.7) and (min_perturb_tpr > tpr_seed)
    metrics["seed"] = {"d": float(d_seed), "tpr_at_fpr": tpr_seed, "official_d": 0.11}
    metrics["P5"] = bool(p5)
    print(f"P5 种子敏感度: d={d_seed:+.2f} TPR@FPR={tpr_seed:.4f} (官方 d=+0.11, 扰动最低 tpr={min_perturb_tpr:.4f}): {'通过' if p5 else '失败'}", flush=True)

    metrics["timing_s"]["total"] = time.time() - t0
    with open(os.path.join(OUT, "g1_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    np.savez(os.path.join(OUT, "S_tilde.npz"), tr=tr_S, val=val_S, white=wS)
    print(f"DONE ({time.time()-t0:.0f}s) -> {OUT}/g1_metrics.json", flush=True)


if __name__ == "__main__":
    main()
