#!/usr/bin/env python3
"""探针③扩展：纤维内稀疏化鲁棒性 + std(m) 标度律

对应：定理 5.8.3.02（谱间隙的纤维化不变性）的鲁棒范围探测；
      10.75 §6 探针1 扩展（宏观速率零方差律的边界）。

扩展1（稀疏化鲁棒性）：固定 N=256, m=16，纤维内 Bernoulli(p_intra) 稀疏化
    p_intra ∈ {1.0, 0.75, 0.5, 0.25, 0.1}
    预言：高 p 时跨系综 std→0（不变性保持）；
          低 p 时纤维内变弱、谱间隙开始依赖纤维内细节 → std 上升。
          临界 p* = 不变性的鲁棒性边界。
    A0 系综（确定性权重×随机稀疏图案）与 A 系综（随机权重×随机图案）对比，
    分离"图案随机性"与"权重随机性"对 std 的贡献。

扩展2（std(m) 标度律）：固定 N=256，m ∈ {4,8,16,32,64}
    理论谱间隙（块常数子空间精确解）：λ₂ = s·4sin²(π/m)，s=N/m
    预言：A 系综 std 平坦（~1e-14 浮点级）→ 不变性与 m 无关（群尺度刚性）；
          C 系综（纤维间破缺）std 随 m 呈特征标度 → 对照。
"""
import numpy as np

def spectral_gap(A):
    """图 Laplacian 第二小特征值（Fiedler 值）= 谱间隙"""
    L = np.diag(A.sum(axis=1)) - A
    ev = np.linalg.eigvalsh(L)
    return ev[1]

def fiber_ensemble(N, m, seeds, intra_w_fn, inter_w=1.0, p_intra=1.0):
    """纤维化图系综（扩展版）：p_intra 参数化纤维内 Bernoulli 稀疏化。
    纤维间：super-graph = 循环图 C_m，权重 inter_w（标量=固定，callable=随机破缺）。
    纤维内：intra_w_fn(rng,(s,s)) 生成权重，×Bernoulli(p_intra) 稀疏，上三角对称化。
    """
    s = N // m
    gaps = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        A = np.zeros((N, N))
        # 纤维内
        for f in range(m):
            idx = slice(f * s, (f + 1) * s)
            W = intra_w_fn(rng, (s, s))
            if p_intra < 1.0:
                W = (rng.random((s, s)) < p_intra) * W
            W = np.triu(W, 1)
            A[idx, idx] += W + W.T
        # 纤维间：循环图 C_m（对称 super 邻接）
        S = np.zeros((m, m))
        for f in range(m):
            for g in ((f - 1) % m, (f + 1) % m):
                w = inter_w if not callable(inter_w) else inter_w(rng)
                S[f, g] = S[g, f] = w
        for f in range(m):
            for g in range(m):
                if S[f, g] != 0:
                    A[f * s:(f + 1) * s, g * s:(g + 1) * s] = S[f, g]
        gaps.append(spectral_gap(A))
    return np.array(gaps)

def main():
    N = 256
    seeds = list(range(50))
    uni = lambda rng, shp: 0.5 + 1.0 * rng.random(shp)
    one = lambda rng, shp: np.ones(shp)
    rnd = lambda rng: 0.5 + 1.0 * rng.random()

    print("=== 探针③扩展 1：纤维内稀疏化鲁棒性  N=256 m=16 seeds=50 ===")
    print(f"{'p_intra':>8s} {'系综':22s} {'mean':>10s} {'std':>10s} {'std/mean':>10s} {'|Δμ/μ0|':>10s}")
    for p in [1.0, 0.75, 0.5, 0.25, 0.1]:
        gA0 = fiber_ensemble(N, 16, seeds, one, p_intra=p)
        gA = fiber_ensemble(N, 16, seeds, uni, p_intra=p)
        mu0, sd0 = gA0.mean(), gA0.std(ddof=1)
        muA, sdA = gA.mean(), gA.std(ddof=1)
        print(f"{p:8.2f} {'A0 确定性·稀疏':22s} {mu0:10.6f} {sd0:10.2e} {sd0/mu0:10.2e} {'—':>10s}")
        print(f"{p:8.2f} {'A  随机·稀疏':22s} {muA:10.6f} {sdA:10.2e} {sdA/muA:10.2e} {abs(muA-mu0)/mu0:10.2e}")

    print()
    print("=== 探针③扩展 2：std(m) 标度律  N=256 固定，m ∈ {4,8,16,32,64} ===")
    print(f"{'m':>4s} {'s':>4s} {'理论λ₂':>10s} {'A0 mean':>10s} {'A mean':>10s} {'A std':>10s} "
          f"{'A std/μ':>9s} {'C std':>10s} {'C std/μ':>9s}")
    for m in [4, 8, 16, 32, 64]:
        s = N // m
        theo = s * 4 * np.sin(np.pi / m) ** 2
        gA0 = fiber_ensemble(N, m, seeds, one)
        gA = fiber_ensemble(N, m, seeds, uni)
        gC = fiber_ensemble(N, m, seeds, uni, inter_w=rnd)
        mu0 = gA0.mean()
        muA, sdA = gA.mean(), gA.std(ddof=1)
        muC, sdC = gC.mean(), gC.std(ddof=1)
        print(f"{m:4d} {s:4d} {theo:10.6f} {mu0:10.6f} {muA:10.6f} {sdA:10.2e} "
              f"{sdA/muA:9.2e} {sdC:10.2e} {sdC/muC:9.2e}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
