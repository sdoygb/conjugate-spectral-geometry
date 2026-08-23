#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针⑤b：GSS 社会版刚性判别的稳健性检查"""
import pandas as pd
import numpy as np
from scipy.sparse.linalg import eigsh
from scipy.sparse import diags

RNG = np.random.default_rng(20260823)
DTA = '/tmp/gss/GSS_stata/gss7224_r3a.dta'
ALL_IND = ['happy', 'health', 'educ', 'attend', 'polviews', 'partyid']
N_BOOT = 400

df = pd.read_stata(DTA, convert_categoricals=False)
for c in ALL_IND:
    df[c] = (df[c] - df[c].mean()) / df[c].std()
df = df[['year'] + ALL_IND].dropna().reset_index(drop=True)
vals = df[ALL_IND].values
yvals = df.year.values
years = np.sort(df.year.unique())
m_all = len(years)

def gap_for(mu_mat, k_nn):
    D = np.sqrt(((mu_mat[:, None, :] - mu_mat[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(D, np.inf)
    W = np.zeros_like(D)
    for i in range(D.shape[0]):
        W[i, np.argsort(D[i])[:k_nn]] = 1.0
    W = (W + W.T) / 2.0
    L = diags(W.sum(1)) - W
    return eigsh(L, k=2, which='SM', return_eigenvectors=False)[0]

def boot_shuf(idx_sets, k_nn, nb):
    lam_b = np.empty(nb); lam_s = np.empty(nb)
    n_y = [len(s) for s in idx_sets]
    all_idx = np.concatenate(idx_sets)
    yr_assign = np.concatenate([np.full(n, i) for i, n in enumerate(n_y)])
    for b in range(nb):
        mu_b = np.empty((len(idx_sets), vals.shape[1]))
        for i, s in enumerate(idx_sets):
            sel = RNG.choice(s, size=len(s), replace=True)
            mu_b[i] = vals[sel].mean(0)
        lam_b[b] = gap_for(mu_b, k_nn)
        perm = RNG.permutation(all_idx)
        mu_s = np.empty((len(idx_sets), vals.shape[1]))
        for i in range(len(idx_sets)):
            mu_s[i] = vals[perm[yr_assign == i]].mean(0)
        lam_s[b] = gap_for(mu_s, k_nn)
    return lam_b.std(), lam_s.std()

def run(tag, inds, k_nn, year_subset=None):
    df2 = df[['year'] + inds]
    if year_subset is not None:
        df2 = df2[df2.year.isin(year_subset)]
    df2 = df2.dropna()
    ys = np.sort(df2.year.unique())
    idx_sets = [np.where(df2.year.values == y)[0] for y in ys]
    v = df2[inds].values
    global vals
    old = vals; vals = v
    sb, ss = boot_shuf(idx_sets, k_nn, N_BOOT)
    vals = old
    print(f'{tag:28s} m={len(ys):3d} k={k_nn} std_boot={sb:.3e} std_shuf={ss:.3e} ratio={ss/sb:5.1f}')
    return ss / sb

print('=== 指标组合稳健性（k=5, 全年份） ===')
r1 = run('全部6指标', ALL_IND, 5)
r2 = run('去partyid(5指标)', ALL_IND[:5], 5)
r3 = run('去polviews(5指标)', ALL_IND[:4]+ALL_IND[5:], 5)
r4 = run('态度三题(happy,health,attend)', ['happy','health','attend'], 5)

print('=== k 稳健性（全指标） ===')
for k in [3, 7]:
    run(f'k={k}', ALL_IND, k)

print('=== 分时段 ===')
early = [y for y in years if y <= 1999]
late = [y for y in years if y >= 2000]
run('1974-1999', ALL_IND, 5, early)
run('2000-2024', ALL_IND, 5, late)

print('=== m 标度律（探针③判别：刚性平坦 vs 随机 m^-1/2） ===')
for seg in [10, 15, 20]:
    sub = years[:seg]
    run(f'm~{seg}（前{seg}年）', ALL_IND, 5, sub)
