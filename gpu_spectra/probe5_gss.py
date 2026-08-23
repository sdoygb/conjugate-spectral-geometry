#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针⑤：GSS 社会版三尺度统计刚性检验（v2，修复索引+连通性）
============================================================
数据：GSS 1972-2024（N=75699 人）
设计：
  - 人 = 点；纤维 = 年份（m 个）；指标 = 6 个态度/行为变量
  - 每纤维状态向量 μ_y = 该年指标均值（z-score 后）
  - 纤维图：m×m kNN 图（k=5，保证连通）
  - 谱量 λ_min = 图 Laplacian 第二小特征值（纤维间相干性度量）
  - 系综 = bootstrap（每年份内重抽样）→ std_boot
  - 对照 = shuffle（打乱年份标签）→ std_shuffle
判别规则（探针③）：std 平坦且 std_boot << std_shuffle → 结构锁定（刚性）；
               std_shuffle ≈ std_boot ~ m^{-1/2} → 纯随机平均。
"""
import pandas as pd
import numpy as np
from scipy.sparse.linalg import eigsh
from scipy.sparse import diags

RNG = np.random.default_rng(20260823)
DTA = '/tmp/gss/GSS_stata/gss7224_r3a.dta'
INDICATORS = ['happy', 'health', 'educ', 'attend', 'polviews', 'partyid']
N_BOOT = 600

# ---------- 数据 ----------
df = pd.read_stata(DTA, convert_categoricals=False)
df = df[['year'] + INDICATORS].copy()
for c in INDICATORS:
    mu, sd = df[c].mean(), df[c].std()
    df[c] = (df[c] - mu) / sd
df = df.dropna().reset_index(drop=True)
print(f'有效样本 N={len(df)}，年份 {df.year.min()}-{df.year.max()}')

years = np.sort(df.year.unique())
m = len(years)
print(f'纤维（年份）数 m={m}')

vals = df[INDICATORS].values
yvals = df.year.values
idx_by_year = {y: np.where(yvals == y)[0] for y in years}

def state_vectors(assign_year):
    df_tmp = df.copy()
    df_tmp['year'] = assign_year
    g = df_tmp.groupby('year')[INDICATORS].mean()
    return g.loc[years].values

def fiber_gap(mu_mat, k_nn=5):
    D = np.sqrt(((mu_mat[:, None, :] - mu_mat[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(D, np.inf)
    W = np.zeros_like(D)
    for i in range(D.shape[0]):
        nn = np.argsort(D[i])[:k_nn]
        W[i, nn] = 1.0
    W = (W + W.T) / 2.0
    d = W.sum(1)
    L = diags(d) - W
    evals = eigsh(L, k=2, which='SM', return_eigenvectors=False)
    return evals[0], D

# ---------- 观测 ----------
mu_obs = state_vectors(yvals)
lam_obs, D_obs = fiber_gap(mu_obs)
print(f'\n观测：λ_min = {lam_obs:.6f}')

SST = df[INDICATORS].var(0).sum() * (len(df) - 1)
SSB = sum(len(g) * ((g[INDICATORS].mean() - df[INDICATORS].mean()) ** 2).sum().sum()
         for _, g in df.groupby('year'))
print(f'组间方差占比 SSB/SST = {SSB/SST:.4f}')

# ---------- bootstrap ----------
print(f'\nbootstrap N={N_BOOT} ...')
lam_boot = np.empty(N_BOOT)
for b in range(N_BOOT):
    mu_b = np.empty((m, len(INDICATORS)))
    for i, y in enumerate(years):
        sel = RNG.choice(idx_by_year[y], size=len(idx_by_year[y]), replace=True)
        mu_b[i] = vals[sel].mean(0)
    lam_boot[b], _ = fiber_gap(mu_b)
std_boot = lam_boot.std()
print(f'std_boot(λ_min) = {std_boot:.3e}   mean={lam_boot.mean():.6f}')

# ---------- shuffle ----------
print(f'shuffle N={N_BOOT} ...')
lam_shuf = np.empty(N_BOOT)
all_idx = np.arange(len(df))
for b in range(N_BOOT):
    yr_shuf = yvals[RNG.permutation(all_idx)]
    mu_b = np.empty((m, len(INDICATORS)))
    for i, y in enumerate(years):
        sel = all_idx[yr_shuf == y]
        mu_b[i] = vals[sel].mean(0)
    lam_shuf[b], _ = fiber_gap(mu_b)
std_shuf = lam_shuf.std()
print(f'std_shuf(λ_min) = {std_shuf:.3e}   mean={lam_shuf.mean():.6f}')

# ---------- 判别 ----------
ratio = std_shuf / std_boot
print(f'\n=== 判别 ===')
print(f'std_shuf/std_boot = {ratio:.1f}')
if ratio > 3:
    verdict = '结构锁定（刚性）：年份集体指标差异远超抽样噪声'
elif ratio > 1.2:
    verdict = '弱结构：部分结构、部分噪声'
else:
    verdict = '未锁定：年份集体差异 ≈ 随机平均（中心极限）'
print('判定:', verdict)

dmu = np.diff(mu_obs, axis=0)
ac1 = np.corrcoef(dmu[:-1].ravel(), dmu[1:].ravel())[0, 1]
print(f'\n长时间条款：Δμ 一阶自相关 = {ac1:+.3f}')

with open('/tmp/gss/probe5_result.txt', 'w') as f:
    f.write(f'N={len(df)} m={m}\n')
    f.write(f'lam_obs={lam_obs:.6f}\n')
    f.write(f'SSB/SST={SSB/SST:.4f}\n')
    f.write(f'std_boot={std_boot:.3e}\n')
    f.write(f'std_shuf={std_shuf:.3e}\n')
    f.write(f'ratio={ratio:.1f}\n')
    f.write(f'verdict={verdict}\n')
    f.write(f'ac1={ac1:+.3f}\n')
print('\n已保存 /tmp/gss/probe5_result.txt')
