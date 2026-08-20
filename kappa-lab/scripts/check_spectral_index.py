"""第一条几何检验：P(l) 局部谱指数 vs 几何指数族。

几何预言（docs/geometrization_proposal.md #1）：
若谱刚性 −5/3 推论（10.8 §5.3）在 κ 场有对应物，则存在 ≥2 倍动态范围的
尺度区间使 |dlogP/dlogl + 5/3| < 0.1。

判据：命中 → 扩展；不命中 → 该路径诚实关闭。
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(ROOT)   # 仓库根（wl_challenge 所在处）
sys.path.insert(0, ROOT)

from kappa_lab.stats.powerspectrum import (
    SIGMA_NOISE,
    PIXEL_ARCMIN,
    add_shape_noise,
    power_spectrum,
    unpack_masked,
)

DATA = f"{PROJ}/wl_challenge/data"
KAPPA = f"{DATA}/sampled_WIDE12H_bin2_2arcmin_kappa.npy"
MASK = f"{DATA}/full/WIDE12H_bin2_2arcmin_mask.npy"
SEED = 42
N_BIN = 50                      # 细 bin（官方 10 bin 的 5 倍分辨率）
L_EDGE = np.logspace(2, 4, N_BIN + 1)
PIXSIZE_RAD = PIXEL_ARCMIN / 60 * np.pi / 180

# 几何指数族候选（10.8 资产）
GEO_INDICES = {
    "-5/3 (谱刚性/惯性子区)": -5 / 3,
    "-3/2 (涡量级联类)": -3 / 2,
    "-1 (经典对数区)": -1.0,
    "-2 (θ→0 作用量极限)": -2.0,
    "0 (白噪声)": 0.0,
}

TOL = 0.1          # 命中容差
MIN_DYN = 2.0      # 最小动态范围（倍数）


def local_index(lk, lP, span=3):
    """局部谱指数：logP vs logk 的 span 点滑动线性拟合（平滑噪声）。"""
    n = len(lk)
    n_eff = np.full(n, np.nan)
    for i in range(span // 2, n - span // 2):
        sl = slice(i - span // 2, i + span // 2 + 1)
        n_eff[i] = np.polyfit(lk[sl], lP[sl], 1)[0]
    return n_eff


def main():
    rng = np.random.default_rng(SEED)
    mask = np.load(MASK).astype(bool)
    k = np.load(KAPPA).astype(np.float64)          # (3, 30, 132019)
    print(f"数据: κ {k.shape}, mask {mask.sum()} 像素, σ_n={SIGMA_NOISE:.5f}")

    full = unpack_masked(k, mask)                  # (3, 30, 1424, 176)
    full = add_shape_noise(full, rng)              # 与基线一致的加噪
    print("加噪完成，计算细 bin 功率谱...")

    Psum = None
    for c in range(full.shape[0]):
        for r in range(full.shape[1]):
            _, P = power_spectrum(full[c, r], PIXSIZE_RAD, L_EDGE)
            Psum = P if Psum is None else Psum + P
    Pmean = Psum / (full.shape[0] * full.shape[1])

    kc = np.sqrt(L_EDGE[:-1] * L_EDGE[1:])         # bin 几何中点
    lk, lP = np.log10(kc), np.log10(Pmean)
    n_eff = local_index(lk, lP)

    print(f"\n{'l':>8s} {'n_eff':>8s}  几何候选命中")
    print("-" * 60)
    for i in range(len(lk)):
        tag = ""
        for name, idx in GEO_INDICES.items():
            if np.isfinite(n_eff[i]) and abs(n_eff[i] - idx) < TOL:
                tag = f"← {name}"
        if i % 5 == 0 or tag:
            print(f"l={kc[i]:7.0f} {n_eff[i]:+8.2f}  {tag}")

    print("\n--- 连续窗口扫描（≥2 倍动态范围，平均 n_eff 命中容差 0.1）---")
    verdict = "未命中"
    for name, idx in GEO_INDICES.items():
        best = None
        for i in range(len(lk)):
            for j in range(i + 2, len(lk)):
                if kc[j] / kc[i] < MIN_DYN:
                    continue
                w = n_eff[i : j + 1]
                if np.isnan(w).any():
                    continue
                m = np.mean(w)
                if best is None or abs(m - idx) < abs(best[1] - idx):
                    best = (f"l∈[{kc[i]:.0f},{kc[j]:.0f}]", m)
        if best:
            ok = abs(best[1] - idx) < TOL
            print(f"  {name:30s} 最优窗口 {best[0]:20s} 平均 n_eff={best[1]:+.3f} {'✔ 命中' if ok else ''}")
            if ok:
                verdict = f"命中: {name} @ {best[0]}"

    print(f"\n判据结论: {verdict}")
    if "命中" not in verdict:
        print("几何指数族未出现在 WL κ 谱中 → 路径 #1 诚实关闭（预期：ΛCDM n_eff≈−0.7）")

    os.makedirs(f"{ROOT}/results", exist_ok=True)
    np.savez(
        f"{ROOT}/results/spectral_index.npz",
        kc=kc, P=Pmean, n_eff=n_eff, verdict=verdict,
    )
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
        ax[0].loglog(kc, Pmean, "o-", ms=3, label="κ 谱 P(l)（3 cosmo × 30 sim 平均）")
        ax[0].set_ylabel("P(l)")
        ax[0].legend()
        ax[1].semilogx(kc, n_eff, "o-", ms=3, label="局部谱指数 n_eff")
        for name, idx in GEO_INDICES.items():
            ax[1].axhline(idx, ls="--", lw=0.8, label=name)
        ax[1].set_ylim(-4, 2)
        ax[1].set_xlabel("l")
        ax[1].set_ylabel("n_eff = dlogP/dlogl")
        ax[1].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(f"{ROOT}/results/spectral_index.png", dpi=150)
        print(f"图已保存: {ROOT}/results/spectral_index.png")
    except Exception as e:
        print(f"画图跳过: {e}")


if __name__ == "__main__":
    main()
