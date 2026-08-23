"""探针④：普适条件压力测试（真实版 2026-08-23）
T1 随机 d-正则图（expander）        ——期望满足 (D2)(D4)
T2 随机核 K=randn(N,N)             ——期望违反 (D2)
T3 二部图（两部等大, 随机二部）     ——期望揭示 配对+平凡零模 判别陷阱
对照 negacyclic / circulant        ——0.9 已知结果复核

核心统计量（对每个样本）：
  L = I - D^{-1/2} A D^{-1/2}（归一化拉普拉斯，半正定）
    lam_min(L)  最小特征值（连通图=0，平凡零模）
    lam2(L)     谱间隙（最小非零特征值）
    lam_max(L)  最大特征值
  A 邻接矩阵谱（二部图验证 ±λ 配对残差）
"""
import numpy as np


def random_d_regular(n, d, seed):
    """配置模型随机 d-正则图（无自环、无重边）。"""
    rng = np.random.default_rng(seed)
    for _attempt in range(200):
        stubs = np.repeat(np.arange(n), d)
        rng.shuffle(stubs)
        pairs = stubs.reshape(-1, 2)
        if np.any(pairs[:, 0] == pairs[:, 1]):
            continue
        A = np.zeros((n, n))
        ok = True
        for a, b in pairs:
            if A[a, b]:
                ok = False
                break
            A[a, b] = 1
            A[b, a] = 1
        if ok:
            return A
    raise RuntimeError("d-正则图构造失败")


def random_bipartite(n, p, seed):
    """随机二部图：两部各 n/2 顶点，边概率 p；重试直到无孤立顶点。"""
    rng = np.random.default_rng(seed)
    m = n // 2
    for _ in range(100):
        B = (rng.random((m, m)) < p).astype(float)
        A = np.zeros((n, n))
        A[:m, m:] = B
        A[m:, :m] = B.T
        if np.all(A.sum(axis=1) > 0):
            return A
    raise RuntimeError("二部图构造失败：持续存在孤立顶点")


def norm_laplacian(A):
    """归一化拉普拉斯 L = I - D^{-1/2} A D^{-1/2}（无孤立顶点时良定义）。"""
    d = A.sum(axis=1)
    assert np.all(d > 0), "存在孤立顶点"
    Dinv_sqrt = np.diag(1.0 / np.sqrt(d))
    return np.eye(A.shape[0]) - Dinv_sqrt @ A @ Dinv_sqrt


def spectrum_stats(A):
    """返回 (lam_min, lam2, lam_max, 邻接配对残差)。"""
    L = norm_laplacian(A)
    lam_L = np.sort(np.linalg.eigvalsh(L))
    lam_A = np.sort(np.linalg.eigvalsh(A))
    # 二部图配对残差：谱关于 0 对称 ⟹ 排序后 lam_A[i] ≈ -lam_A[n-1-i]
    n = A.shape[0]
    pair_residual = np.max(np.abs(lam_A[:n // 2] + lam_A[n // 2:][::-1])) if n % 2 == 0 else np.nan
    return lam_L[0], lam_L[1], lam_L[-1], pair_residual


def run_ensemble(name, gen, seeds, n, extra=""):
    rows = []
    for s in seeds:
        A = gen(n, s)
        rows.append(spectrum_stats(A))
    arr = np.array(rows)
    print(f"[{name}] {extra}")
    print(f"  lam_min(L): mean={arr[:,0].mean():.6e}  std={arr[:,0].std():.3e}")
    print(f"  lam2(L)   : mean={arr[:,1].mean():.6e}  std={arr[:,1].std():.3e}")
    print(f"  lam_max(L): mean={arr[:,2].mean():.6e}  std={arr[:,2].std():.3e}")
    print(f"  配对残差  : mean={arr[:,3].mean():.3e}  max={arr[:,3].max():.3e}")
    return arr


def negacyclic_gram_inline(d, seed):
    rng = np.random.default_rng(seed)
    a = rng.integers(-10, 10, size=d).astype(float)
    A = np.zeros((d, d))
    for i in range(d):
        for k in range(d):
            A[i, (i + k) % d] = a[k] * ((-1) ** ((i + k) // d))
    B = np.zeros((2 * d, 2 * d))
    B[:d, :d] = A
    B[:d, d:] = np.eye(d)
    B[d:, :d] = 7.0 * np.eye(d)
    return B @ B.T


def circulant_gram_inline(d, seed):
    rng = np.random.default_rng(seed)
    a = rng.integers(-10, 10, size=d).astype(float)
    A = np.zeros((d, d))
    for i in range(d):
        for k in range(d):
            A[i, (i + k) % d] = a[k]
    B = np.zeros((2 * d, 2 * d))
    B[:d, :d] = A
    B[:d, d:] = np.eye(d)
    B[d:, :d] = 7.0 * np.eye(d)
    return B @ B.T


def main():
    seeds = list(range(50))

    # ---- T1: 随机 d-正则图 ----
    arr1 = run_ensemble("T1 随机d-正则(d=4)", lambda n, s: random_d_regular(n, 4, s), seeds, 256)

    # ---- T2: 随机核 K=randn(N,N)，谱对象 K^T K（Gram 半正定） ----
    rows2 = []
    rng = np.random.default_rng(20260823)
    for s in seeds:
        K = rng.standard_normal((256, 256))
        G = K.T @ K
        lam = np.sort(np.linalg.eigvalsh(G))
        rows2.append((lam[0], lam[1], lam[-1], np.nan))
    arr2 = np.array(rows2)
    print(f"[T2 随机核 K^T K]")
    print(f"  lam_min: mean={arr2[:,0].mean():.6e}  std={arr2[:,0].std():.3e}")
    print(f"  lam2   : mean={arr2[:,1].mean():.6e}  std={arr2[:,1].std():.3e}")

    # ---- T3: 二部图（两部各 128，p=4/128 平均度 4）----
    arr3 = run_ensemble("T3 随机二部图(p=0.0625)", lambda n, s: random_bipartite(n, 0.0625, s), seeds, 256)

    # ---- 对照: negacyclic 谱刚性比 Λ_H=λ2/λ1（0.9.4.01, Gram 型）----
    rows_neg = []
    for s in range(50):
        G = negacyclic_gram_inline(64, s)
        lam = np.sort(np.linalg.eigvalsh(G))
        rows_neg.append((lam[0], lam[1], lam[1] / lam[0]))
    arrn = np.array(rows_neg)
    print(f"[对照 negacyclic d=64]")
    print(f"  lam_min: mean={arrn[:,0].mean():.6e}  std={arrn[:,0].std():.3e}")
    print(f"  LambdaH=lam2/lam1: mean={arrn[:,2].mean():.10f}  std={arrn[:,2].std():.3e}")

    # ---- 对照: circulant（d=8, 自配对块统计）----
    rows_circ = []
    for s in range(50):
        G = circulant_gram_inline(8, s)
        lam = np.sort(np.linalg.eigvalsh(G))
        rows_circ.append((lam[0], lam[1], lam[1] / lam[0]))
    arrc = np.array(rows_circ)
    print(f"[对照 circulant d=8]")
    print(f"  LambdaH: mean={arrc[:,2].mean():.6f}  std={arrc[:,2].std():.3e}  (非零方差=自配对破坏刚性)")

    print("\n=== 判别规则验证 ===")
    print(f"T3 二部图: lam_min≡0 精确(std={arr3[:,0].std():.1e}) → 零方差但非刚性(平凡零模)")
    print(f"T1 d-正则: lam_min≈0(连通) 但 lam2 有涨落 std={arr1[:,1].std():.2e}")
    print(f"对照 negacyclic: lam_min>0 且 LambdaH std={arrn[:,2].std():.1e} → 真正刚性")


if __name__ == "__main__":
    main()
