#!/usr/bin/env python3
"""
探针㉑：中国区域纤维化结构分析（WVS Wave 7 中国样本）
================================================================
设计说明（诚实修订）：
WVS Wave 7 中国的 N_REGION_ISO 为 29 个数字编码（156001–156034），
公开资料（问卷/网页）未提供省名映射；N_TOWN 全缺失。因此：
- 南北分组因无省名映射不可行，留作开放问题（需官方 codebook）
- 本探针改为：29 个省级区域作为纤维，检验中国内部的三尺度刚性
  （区域=纤维、个体=随机点、集体量=区域均值），与探针⑥ 同框架

检验：
1) η²(29 区域) —— 区域结构解释个体差异的比例
2) 区域 std 排名（最脆弱区域，编码标识）
3) bootstrap 200 次区域排序稳定性 ρ（区域均值排序是否锁定）
4) 对照：中国 29 区域 vs 全球 66 国的 η²
"""
import pandas as pd
import numpy as np
import json
from collections import defaultdict

ALPHA = 'CHN'
Q49 = 'Q49'
REG = 'N_REGION_ISO'

df = pd.read_csv('WVS_Cross-National_Wave_7_csv_v6_0.csv',
                 usecols=['B_COUNTRY_ALPHA', Q49, REG], low_memory=False)
cn = df[(df['B_COUNTRY_ALPHA'] == ALPHA) & (df[Q49] > 0)]
print(f'中国有效样本: {len(cn)}  (Q49 1-10)')

# ---- 每区域统计 ----
g = cn.groupby(REG)[Q49]
stats = pd.DataFrame({
    'n': g.count(), 'mean': g.mean(), 'std': g.std()
}).dropna(subset=['std'])
stats = stats.sort_values('std', ascending=False)
print(f'\n区域数: {len(stats)}')
print('\n最脆弱区域 (std 最高 8):')
print(stats.head(8).to_string())
print('\n最稳健区域 (std 最低 6):')
print(stats.tail(6).to_string())

# ---- η²(区域) ----
grand_mean = cn[Q49].mean()
ssb = sum(stats['n'] * (stats['mean'] - grand_mean) ** 2)
sst = sum((cn[Q49] - grand_mean) ** 2)
eta2 = ssb / sst
print(f'\nη²(29 区域) = {eta2:.4f}  (区域解释 {eta2*100:.1f}% 个体差异)')

# ---- bootstrap 排序稳定性 ----
rng = np.random.default_rng(42)
regs = stats.index.tolist()
n_reg = len(regs)
# 基准排序：按真实区域均值降序
base_order = stats['mean'].sort_values(ascending=False).index.tolist()
rhos = []
for _ in range(200):
    # 按区域从个体重采样
    sampled_means = {}
    for r in regs:
        vals = cn.loc[cn[REG] == r, Q49].values
        if len(vals) == 0:
            continue
        boot = rng.choice(vals, size=len(vals), replace=True)
        sampled_means[r] = boot.mean()
    order = sorted(sampled_means, key=lambda r: -sampled_means[r])
    # Spearman rank corr with base
    rank_base = {r: i for i, r in enumerate(base_order)}
    rank_boot = {r: i for i, r in enumerate(order)}
    d2 = sum((rank_base[r] - rank_boot[r]) ** 2 for r in order)
    rho = 1 - 6 * d2 / (n_reg * (n_reg ** 2 - 1))
    rhos.append(rho)
rhos = np.array(rhos)
print(f'\nbootstrap 200 次区域排序稳定性: ρ 均值={rhos.mean():.4f}, min={rhos.min():.4f}')

# ---- 对照: 全球 66 国 η² (同一 Q49) ----
df_all = df[df[Q49] > 0]
gm_all = df_all[Q49].mean()
g_all = df_all.groupby('B_COUNTRY_ALPHA')[Q49].agg(['count', 'mean'])
ssb_all = sum(g_all['count'] * (g_all['mean'] - gm_all) ** 2)
sst_all = sum((df_all[Q49] - gm_all) ** 2)
eta2_all = ssb_all / sst_all
print(f'\n对照: 全球 66 国 η²(国家) = {eta2_all:.4f}')
print(f'比值: η²(中国区域)/η²(国家) = {eta2/eta2_all:.2f}')

# ---- 区域 CLT 判别: 区域均值散布 vs 采样噪声 ----
# 每区域均值散布 std
spread = stats['mean'].std()
# 平均采样噪声 (区域级 CLT): mean(sigma/sqrt(n))
noise = (stats['std'] / np.sqrt(stats['n'])).mean()
ratio = spread / noise
print(f'\nCLT 判别: 区域均值散布 {spread:.3f} / 采样噪声 {noise:.3f} = {ratio:.1f}')

out = {
    'n': int(len(cn)), 'n_regions': int(len(stats)),
    'eta2_region': float(eta2), 'eta2_country': float(eta2_all),
    'ratio_eta2': float(eta2 / eta2_all),
    'bootstrap_rho': {'mean': float(rhos.mean()), 'min': float(rhos.min())},
    'clt_ratio': float(ratio),
    'top_vulnerable': {str(r): {'std': float(s), 'n': int(n)}
                       for r, s, n in zip(stats.index[:8], stats['std'][:8], stats['n'][:8])},
}
with open('probe21_results.json', 'w') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print('\n已保存 probe21_results.json')
