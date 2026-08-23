#!/usr/bin/env python3
"""探针⑤ 社会版判别分析 v8（块间骨架方案——探针③最忠实移植）。

机制（与探针③一一对应）：
  探针③: 纤维化结构(块间完全二分) => 纤维内随机化 => 宏观速率(谱间隙)逐位不变
  社会版: 社区结构(纤维) => 社区内随机重连 => 块间骨架矩阵 B 不变
          => 宏观速率 lambda_2(B) 精确不变 (锁定)

判别: std(lambda_2(B); 社区内重连) vs std(lambda_2(B); 全图重连)
  平坦=刚性(结构锁定)   m^-1/2=随机(未锁定)
"""
import numpy as np
import networkx as nx
from scipy.sparse import coo_matrix
import sys, time

def load_adj(path):
    edges = []
    with open(path) as f:
        for line in f:
            if line.startswith('#'):
                continue
            u, v = line.strip().split()[:2]
            edges.append((int(u), int(v)))
    edges = np.array(edges, dtype=np.int64)
    nodes = np.unique(edges)
    remap = {n: i for i, n in enumerate(nodes)}
    r = np.array([remap[u] for u in edges[:, 0]])
    c = np.array([remap[v] for v in edges[:, 1]])
    N = len(nodes)
    A = coo_matrix((np.ones(len(r)), (r, c)), shape=(N, N)).tocsr()
    A = A + A.T
    A.data = np.ones(len(A.data))
    return A, N, len(edges)

def lpa_communities(A, seed=42):
    G = nx.from_scipy_sparse_array(A)
    comms = list(nx.algorithms.community.asyn_lpa_communities(G, seed=seed))
    comms = [np.sort(np.array(list(c), dtype=np.int64)) for c in comms]
    return [c for c in comms if len(c) >= 4]

def block_matrix(A, comms):
    m = len(comms)
    node2comm = np.full(A.shape[0], -1, dtype=np.int64)
    for i, cl in enumerate(comms):
        node2comm[cl] = i
    coo = A.tocoo()
    mask = coo.row < coo.col
    r, c = coo.row[mask], coo.col[mask]
    cr, cc = node2comm[r], node2comm[c]
    valid = (cr >= 0) & (cc >= 0)
    B = np.zeros((m, m))
    np.add.at(B, (cr[valid], cc[valid]), 1)
    B = B + B.T
    return B

def block_gap(B):
    d = B.sum(axis=1)
    if np.any(d <= 0):
        return 0.0
    dinv = 1.0 / np.sqrt(d)
    Ln = np.eye(len(B)) - np.outer(dinv, dinv) * B
    w = np.sort(np.linalg.eigvalsh(Ln))
    return float(w[1] if w[0] < 1e-8 else w[0])

def rewire_comm(A, comms, seed=1):
    """社区内配置模型重连（不改变跨社区边 => 块间矩阵 B 不变）"""
    rng = np.random.default_rng(seed)
    coo = A.tocoo()
    r, c = coo.row, coo.col
    m = r < c
    r, c = r[m], c[m]
    keep = np.ones(len(r), dtype=bool)
    new_r, new_c = [], []
    for cl in comms:
        if len(cl) < 4:
            continue
        inr = np.isin(r, cl)
        inc = np.isin(c, cl)
        both = inr & inc
        if both.sum() < 2:
            continue
        keep &= ~both
        deg = np.zeros(len(cl), dtype=np.int64)
        ri = np.searchsorted(cl, r[both])
        ci2 = np.searchsorted(cl, c[both])
        deg += np.bincount(ri, minlength=len(cl))
        deg += np.bincount(ci2, minlength=len(cl))
        total = int(deg.sum())
        if total % 2 != 0:
            j = int(np.argmax(deg)); deg[j] -= 1
        stubs = np.repeat(np.arange(len(cl)), deg)
        rng.shuffle(stubs)
        a_s, b_s = stubs[0::2], stubs[1::2]
        key = np.sort(np.stack([a_s, b_s], axis=1), axis=1)
        new_r.extend(cl[key[:, 0]])
        new_c.extend(cl[key[:, 1]])
    R = np.concatenate([r[keep], np.array(new_r, dtype=np.int64)]) if new_r else r[keep]
    C = np.concatenate([c[keep], np.array(new_c, dtype=np.int64)]) if new_c else c[keep]
    N = A.shape[0]
    A2 = coo_matrix((np.ones(len(R)), (R, C)), shape=(N, N)).tocsr()
    A2 = A2 + A2.T
    A2.data = np.ones(len(A2.data))
    return A2

def rewire_global(A, seed=2):
    """全图配置模型重连（破坏社区结构 => B 变化）"""
    rng = np.random.default_rng(seed)
    d = np.asarray(A.sum(axis=1)).ravel().astype(np.int64)
    N = A.shape[0]
    total = int(d.sum())
    if total % 2 != 0:
        j = int(np.argmax(d)); d[j] -= 1
    stubs = np.repeat(np.arange(N), d)
    rng.shuffle(stubs)
    key = np.sort(np.stack([stubs[0::2], stubs[1::2]], axis=1), axis=1)
    A2 = coo_matrix((np.ones(len(key)), (key[:, 0], key[:, 1])), shape=(N, N)).tocsr()
    A2 = A2 + A2.T
    A2.data = np.ones(len(A2.data))
    return A2

def main():
    dataset = sys.argv[1] if len(sys.argv) > 1 else 'facebook'
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    paths = {'facebook': '/tmp/socdata/facebook_combined.txt',
             'astro': '/tmp/socdata/ca-AstroPh.txt'}
    print(f"=== 探针⑤ 社会版判别分析 v8 [块间骨架] [{dataset}]  R={R} ===")
    t0 = time.time()
    A, N, M = load_adj(paths[dataset])
    print(f"图: N={N}, M={M//2}")

    comms = lpa_communities(A)
    m = len(comms)
    sizes = sorted([len(c) for c in comms], reverse=True)
    print(f"LPA 社区数 m={m}, 社区规模 top5={sizes[:5]}")

    B0 = block_matrix(A, comms)
    gap0 = block_gap(B0)
    print(f"基线 lambda_2(B) = {gap0:.9f}")

    # 社区内重连（预期 B 不变 => 精确锁定）
    gaps_w = []
    for i in range(R):
        Aw = rewire_comm(A, comms, seed=100 + i)
        Bw = block_matrix(Aw, comms)
        gaps_w.append(block_gap(Bw))
    gaps_w = np.array(gaps_w)
    mu_w, std_w = float(gaps_w.mean()), float(gaps_w.std(ddof=1))
    print(f"社区内重连: lambda_2(B) mean={mu_w:.9f}  std={std_w:.3e}")

    # 全图重连（破坏社区结构 => B 变化）
    gaps_g = []
    for i in range(R):
        Ag = rewire_global(A, seed=200 + i)
        Bg = block_matrix(Ag, comms)
        gaps_g.append(block_gap(Bg))
    gaps_g = np.array(gaps_g)
    mu_g, std_g = float(gaps_g.mean()), float(gaps_g.std(ddof=1))
    print(f"全图重连:   lambda_2(B) mean={mu_g:.9f}  std={std_g:.3e}")

    ratio = std_w / std_g if std_g > 0 else float('inf')
    print(f"\n对比度 std(社区内)/std(全图) = {ratio:.3e}")
    verdict = '结构锁定宏观速率 (刚性)' if ratio < 0.05 else '未锁定(随机)'
    print(f"判定: {verdict}")
    print(f"\nRESULT {dataset} N={N} M={M//2} m={m} gap0={gap0:.9f} "
          f"within_mean={mu_w:.9f} within_std={std_w:.3e} "
          f"global_std={std_g:.3e} ratio={ratio:.3e} verdict={verdict}")
    print(f"耗时 {time.time()-t0:.1f}s")

if __name__ == '__main__':
    main()
