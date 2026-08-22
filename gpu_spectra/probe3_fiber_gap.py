#!/usr/bin/env python3
"""探针③：宏观速率零方差律（谱间隙纤维化不变性的数值检验）

对应：定理 5.8.3.02（谱间隙的纤维化不变性）、10.75 §6 探针1（宏观速率零方差）、
      10.20 §8.1（宏观弛豫速率由纤维化结构唯一锁定，与微观细节无关）。

设计（三系综对照）：
  A. 纤维化系综：固定纤维间结构（super-graph = 循环图 C_m，权重固定），
     随机化纤维内权重（i.i.d. Uniform[0.5,1.5]）
     → 预言：谱间隙 λ₂(L) 跨系综 std → 0（宏观速率=纤维化结构签名）
  A0. 纤维内确定性权重（≡1）基准：给出理论谱间隙（纤维化不变性的极限）
  B. ER 对照系综：同规模(N=256)无结构随机图，平均度 4
     → 谱间隙跨系综 std 显著（随机性在宏观尺度"复活"）
  C. 结构破缺系综：纤维间权重也随机化（纤维化结构被破坏）
     → 方差出现，且数值落于 A 与 B 之间（确认方差来源是纤维间结构）

物理对应：λ₂(L) = 宏观弛豫速率（谱间隙），离散混合时间 τ_mix ≈ 1/λ₂。
探针检验：同纤维化结构、不同微观细节的系综，宏观速率必须唯一。
"""
import numpy as np

def spectral_gap(A):
    """图 Laplacian 第二小特征值（Fiedler 值）= 谱间隙"""
    L = np.diag(A.sum(axis=1)) - A
    ev = np.linalg.eigvalsh(L)
    return ev[1]

def fiber_ensemble(N, m, seeds, intra_dist, inter_w=1.0, sparse_intra=False):
    """纤维化图系综：N 节点分 m 个纤维（每纤维 s=N//m 节点）。
    纤维间：super-graph = 循环图 C_m，权重 inter_w（标量=固定，callable=随机化破缺）。
    纤维内：intra_dist(rng, (s,s)) 生成权重，对角化后上三角对称化。
    对称性保证：纤维间权重先建对称 super 邻接矩阵，再填充块。
    """
    s = N // m
    gaps = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        A = np.zeros((N, N))
        # 纤维内
        for f in range(m):
            idx = slice(f * s, (f + 1) * s)
            W = intra_dist(rng, (s, s))
            if sparse_intra:
                W = (rng.random((s, s)) < 0.5) * W
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

def er_ensemble(N, seeds, avg_deg, w=1.0):
    """ER 随机图对照系综"""
    p = avg_deg / (N - 1)
    gaps = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        W = (rng.random((N, N)) < p).astype(float)
        W = np.triu(W, 1)
        W = W + W.T
        W[W > 0] = w
        gaps.append(spectral_gap(W))
    return np.array(gaps)

def report(name, gaps, ref=None):
    mu, sd = gaps.mean(), gaps.std(ddof=1)
    rel = sd / mu if mu > 0 else float('nan')
    line = (f"{name:28s}  mean={mu:.6f}  std={sd:.6e}  "
            f"std/mean={rel:.2e}  min={gaps.min():.6f}  max={gaps.max():.6f}")
    if ref is not None:
        line += f"  |Δmean/ref|={abs(mu - ref) / ref:.2e}"
    print(line)
    return mu, sd

def main():
    N, m = 256, 16
    seeds = list(range(50))

    print(f"=== 探针③：宏观速率零方差律  N={N} m={m} seeds={len(seeds)} ===")
    print(f"{'系综':28s}  谱间隙统计（跨系综）\n")

    # A0. 纤维内确定性权重（≡1）——纤维化不变性的基准（理论谱间隙）
    gA0 = fiber_ensemble(N, m, seeds, lambda rng, shp: np.ones(shp))
    mu0, sd0 = report("A0 纤维化·确定性纤维内", gA0)
    print(f"    → 理论谱间隙（基准，std 应≈0 仅舍入）")

    # A. 纤维化系综：纤维内权重随机化 Uniform[0.5,1.5]
    gA = fiber_ensemble(N, m, seeds, lambda rng, shp: 0.5 + 1.0 * rng.random(shp))
    report("A  纤维化·随机纤维内", gA, ref=mu0)
    print(f"    → 预言：std/mean 小（≪1e-2），宏观速率不变（纤维化不变性）")

    # B. ER 对照
    gB = er_ensemble(N, seeds, avg_deg=4)
    report("B  ER 随机图对照", gB)
    print(f"    → 对照：std/mean 显著（随机性在宏观尺度复活）")

    # C. 结构破缺：纤维间权重也随机化（对称采样）
    gC = fiber_ensemble(N, m, seeds, lambda rng, shp: 0.5 + 1.0 * rng.random(shp),
                        inter_w=lambda rng: 0.5 + 1.0 * rng.random())
    report("C  纤维化·纤维间破缺", gC, ref=mu0)
    print(f"    → 破缺：方差应介于 A 与 B 之间（方差来源=纤维间结构）")

    # 比值对比
    ratio_AB = gA.std(ddof=1) / gB.std(ddof=1)
    ratio_AC = gA.std(ddof=1) / gC.std(ddof=1)
    print(f"\n对比度：std(A)/std(B) = {ratio_AB:.2e}"
          f"（≪1 ⟹ 纤维化锁定宏观速率）")
    print(f"对比度：std(A)/std(C) = {ratio_AC:.2e}"
          f"（≪1 ⟹ 方差确实来自纤维间结构破缺）")

    print("\n判定：")
    ok_A = gA.std(ddof=1) / mu0 < 1e-3
    ok_C = gC.std(ddof=1) > 10 * gA.std(ddof=1)
    print(f"  A 纤维化不变性（std/μ0 < 1e-3）: {'✓ 确认' if ok_A else '✗ 未达'}")
    print(f"  C 破缺引入方差（std(C) > 10×std(A)）: {'✓ 确认' if ok_C else '✗ 未达'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
