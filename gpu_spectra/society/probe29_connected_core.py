#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针㉙ (P0 第二步)：核心图连通分量分析 → λ₂ 有意义化
================================================================
问题: 64 节点全图归一化后弱边淹没 λ₂ (~1e-4, 无信息量);
      top100 核心图含孤立小国 → 图不连通 → λ₂=0.
解决: 对核心图 (top100/top150/tau02) 取最大连通分量 (GCC),
      在 GCC 上计算 λ₂/BR → 反映核心结构的真实代数连通度.

输出: probe29_results.json + 分析结论
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv('baci_66_yearly_v2.csv')
codes = sorted(set(df['i'].unique()) | set(df['j'].unique()))
idx = {c: k for k, c in enumerate(codes)}
N = len(codes)
print(f'节点数: {N}', flush=True)

def matrix_of(year):
    M = np.zeros((N, N))
    sub = df[df['year'] == year]
    for _, r in sub.iterrows():
        a, b, v = idx[r['i']], idx[r['j']], r['v']
        M[a, b] += v
        M[b, a] += v
    return M

def gcc_of(W):
    """最大连通分量 (按节点数); 返回 (子图邻接矩阵, 子图节点列表, 全图分量数)"""
    n = W.shape[0]
    # BFS 找连通分量
    seen = np.zeros(n, bool)
    comps = []
    for s in range(n):
        if seen[s]:
            continue
        stack = [s]; seen[s] = True; comp = []
        while stack:
            u = stack.pop(); comp.append(u)
            nbrs = np.nonzero(W[u] > 0)[0]
            for v in nbrs:
                if not seen[v]:
                    seen[v] = True; stack.append(v)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    gcc = comps[0]
    Wg = W[np.ix_(gcc, gcc)]
    return Wg, [codes[i] for i in gcc], len(comps)

def metrics_sub(W):
    n = W.shape[0]
    deg = W.sum(axis=1)
    mx = W.max()
    if mx <= 0 or n < 2:
        return dict(l2=0.0, br=0.0, n=n)
    Wn = W / mx
    L = np.diag(Wn.sum(axis=1)) - Wn
    ev = np.sort(np.linalg.eigvalsh(L))
    l2 = float(ev[1])
    evA = np.sort(np.linalg.eigvalsh(Wn))
    br = float(sum(abs(evA[i] + evA[n - 1 - i]) for i in range(n // 2)) / (n // 2))
    return dict(l2=l2, br=br, n=n)

def core_W(M, topk=None, tau=None):
    mx = M.max()
    W = M / mx
    if topk is not None:
        flat = np.triu(W, 1).flatten()
        pos = flat[flat > 0]
        thr = np.sort(pos)[-topk] if len(pos) >= topk else 0.0
        mask = np.triu(W, 1) >= thr
    else:
        mask = np.triu(W, 1) >= tau
    return np.where(mask | mask.T, W, 0.0)

years = list(range(1995, 2025))
rows = []
for y in years:
    M = matrix_of(y)
    r = dict(year=y)
    for name, W in [('full', M / M.max()), ('top100', core_W(M, topk=100)),
                    ('top150', core_W(M, topk=150)), ('tau02', core_W(M, tau=0.02))]:
        Wg, gcc_list, ncomp = gcc_of(W)
        m = metrics_sub(Wg)
        r[f'{name}_gcc_n'] = m['n']
        r[f'{name}_gcc_l2'] = m['l2']
        r[f'{name}_gcc_br'] = m['br']
        r[f'{name}_ncomp'] = ncomp
    print(f'{y}: full λ₂={r["full_gcc_l2"]:.6f} (n={r["full_gcc_n"]}) | '
          f'top100 λ₂={r["top100_gcc_l2"]:.6f} (n={r["top100_gcc_n"]}, 分量{r["top100_ncomp"]}) | '
          f'top150 λ₂={r["top150_gcc_l2"]:.6f} (n={r["top150_gcc_n"]}) | '
          f'tau02 λ₂={r["tau02_gcc_l2"]:.6f} (n={r["tau02_gcc_n"]})', flush=True)
    rows.append(r)

res = dict(years=years, trajectory=rows)
json.dump(res, open('probe29_results.json', 'w'), ensure_ascii=False, indent=1)
print('[done]')
