#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针㉗b2：OpenAlex 合著矩阵 → λ₂/BR 轨迹"""
import json, numpy as np

CORE = ['CN', 'TW', 'US', 'JP', 'IN', 'DE', 'FR', 'IT', 'GB', 'CA', 'RU', 'KR', 'AU']
IDX = {c: i for i, c in enumerate(CORE)}
YEARS = [1995, 2000, 2005, 2010, 2015, 2020, 2024]

def lambda2_br(M):
    import networkx as nx
    deg = M.sum(axis=1)
    active = deg > 0
    n_act = int(active.sum())
    if n_act < 2: return 0.0, 0.0, n_act, 0
    G = nx.from_numpy_array(M[active][:, active])
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    gcc_nodes = sorted(comps[0])
    n_gcc = len(gcc_nodes)
    Ms = M[active][:, active][np.ix_(gcc_nodes, gcc_nodes)]
    L = np.diag(Ms.sum(axis=1)) - Ms
    ev = np.sort(np.linalg.eigvalsh(L))
    l2 = float(ev[1]) if n_gcc > 1 else 0.0
    evA = np.sort(np.linalg.eigvalsh(Ms))
    n = len(evA)
    br = float(sum(abs(evA[i] + evA[n-1-i]) for i in range(n//2)) / (n//2)) if n > 1 else 0.0
    return l2, br, n_act, n_gcc

def main():
    data = json.load(open('gpu_spectra/society/openalex_coauth_13c.json'))
    traj = []
    for year in YEARS:
        row = data.get(str(year), {})
        M = np.zeros((13, 13))
        for a in row:
            if a not in IDX: continue
            counts = row[a]
            for cc, v in counts.items():
                if cc in IDX and cc != a:
                    M[IDX[a], IDX[cc]] += v
        # 对称化
        S = (M + M.T) / 2
        mx = S.max()
        if mx > 0: S = S / mx
        l2, br, n_act, n_gcc = lambda2_br(S)
        traj.append({'year': year, 'n_active': n_act, 'gcc': n_gcc,
                     'lambda2': l2, 'BR': br})
        print(f"{year}: n_active={n_act} GCC={n_gcc} λ₂={l2:.4f} BR={br:.4f}")
    with open('gpu_spectra/society/openalex_13_trajectory.csv', 'w') as f:
        f.write('year,n_active,gcc,lambda2,BR\n')
        for t in traj:
            f.write(f"{t['year']},{t['n_active']},{t['gcc']},{t['lambda2']:.6f},{t['BR']:.6f}\n")
    print('saved openalex_13_trajectory.csv')

if __name__ == '__main__':
    main()
