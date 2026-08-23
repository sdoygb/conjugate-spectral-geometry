#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针⑳：饱和期高精度计算
四层升级：
1. 全口径破缺密度序列（OV CY 1989-2025 三类冲突 + UCDP PRIO 1946-1988 前段）
2. 终止（补缺）率序列：UCDP ConflictTermination 每年终止事件
3. 时变 λ_b(t)/λ_r(t) 分段估计（四时代）
4. 蒙特卡洛饱和期分布（参数不确定传播）→ 中位数 + 90% 区间
"""
import json, math
import numpy as np
import pandas as pd
from collections import defaultdict

np.random.seed(20260823)

# ---------- 1. 数据加载 ----------
prio = pd.read_csv('UcdpPrioConflict_v26_1.csv')
ov = pd.read_csv('OrganizedViolenceCYDataSet26_1.csv')
term = pd.read_csv('UCDPConflictTerminationDataset_v4_2024_Conflict.csv')

# 国家-年冲突状态矩阵：PRIO 1946-1988（国家冲突），OV 1989-2025（全口径：sb=国家冲突）
# 先建 PRIO 侧：year, location 列表
prio_years = defaultdict(set)
for _, r in prio.iterrows():
    y = int(r['year'])
    if y <= 1988:
        prio_years[y].add(str(r['location']).strip())

# OV 侧：country, year, sb_exist（国家冲突存在）+ ns/os 全口径
ov_years_sb = defaultdict(set)
ov_years_all = defaultdict(set)   # 全口径（国家+非国家+单边）
for _, r in ov.iterrows():
    y = int(r['year'])
    c = str(r['country']).strip()
    if int(r['sb_exist']) == 1:
        ov_years_sb[y].add(c)
    if int(r['sb_exist']) == 1 or int(r['ns_exist']) == 1 or int(r['os_exist']) == 1:
        ov_years_all[y].add(c)

# 合并：1946-1988 用 PRIO（国家冲突口径），1989-2025 用 OV（先 sb 口径，再全口径对照）
years = list(range(1946, 2026))
n_countries = 66  # 探针⑮⑯框架的 66 国（WVS 国家集）
# 用 ucdp2iso 拿 66 国列表
with open('ucdp2iso.json') as f:
    ucdp2iso = json.load(f)
iso2country = {v: k for k, v in ucdp2iso.items()}
countries66 = list(ucdp2iso.keys())
# 国家名匹配：OV country 名 vs 66 国名（ucdp2iso 的 key 是 UCDP 国家名）

# 年度破缺密度（66 国口径）
density_sb = {}   # 国家冲突口径
density_all = {}  # 全口径（仅 1989+）
for y in years:
    if y <= 1988:
        loc_set = prio_years.get(y, set())
        # 66 国过滤：名称匹配（保守：直接算 UCDP 全球口径与 66 国口径对比）
        n = sum(1 for loc in loc_set if loc in countries66 or loc in iso2country)
        density_sb[y] = n / len(countries66)
        density_all[y] = None
    else:
        sb_set = ov_years_sb.get(y, set())
        all_set = ov_years_all.get(y, set())
        n_sb = sum(1 for c in sb_set if c in countries66 or c in iso2country)
        n_all = sum(1 for c in all_set if c in countries66 or c in iso2country)
        density_sb[y] = n_sb / len(countries66)
        density_all[y] = n_all / len(countries66)

# ---------- 2. 终止（补缺）率序列 ----------
term_by_year = defaultdict(int)
for _, r in term.iterrows():
    if pd.notna(r['c_epterm']) and int(r['c_epterm']) == 1:
        term_by_year[int(r['c_ep_endyear'])] += 1

# ---------- 3. 时变 λ 分段估计 ----------
# 从 66 国年度状态序列（1946-2025）估计每时代的 W→C 与 C→W 转移率
# 状态：国家冲突口径（sb）
# 先建 66 国逐年状态
state = {}  # (country, year) -> 1/0
for y in years:
    if y <= 1988:
        loc_set = prio_years.get(y, set())
        for c in countries66:
            state[(c, y)] = 1 if c in loc_set else 0
    else:
        sb_set = ov_years_sb.get(y, set())
        for c in countries66:
            state[(c, y)] = 1 if c in sb_set else 0

# 每时代统计
eras = [(1946, 1989, '冷战'), (1990, 2005, '后冷战'), (2006, 2015, '动荡期'), (2016, 2025, '当前')]
era_stats = {}
for (y0, y1, name) in eras:
    n_w2c = 0; n_c2w = 0; n_w = 0; n_c = 0
    for c in countries66:
        for y in range(y0, y1):
            if (c, y) not in state or (c, y+1) not in state:
                continue
            s0 = state[(c, y)]; s1 = state[(c, y+1)]
            if s0 == 0:
                n_w += 1
                if s1 == 1: n_w2c += 1
            else:
                n_c += 1
                if s1 == 0: n_c2w += 1
    lam_b = n_w2c / n_w if n_w else 0
    lam_r = n_c2w / n_c if n_c else 0
    era_stats[name] = dict(n_w=n_w, n_c=n_c, n_w2c=n_w2c, n_c2w=n_c2w,
                           lam_b=lam_b, lam_r=lam_r,
                           pi_c=lam_b/(lam_b+lam_r) if (lam_b+lam_r) else None,
                           tau=1/(lam_b+lam_r) if (lam_b+lam_r) else None)

# ---------- 4. 蒙特卡洛饱和期分布 ----------
# 用当前时代（2016-2025）λ 从二项后验抽样（Beta 近似），模拟 ODE 到 90%/95%/99% 饱和
p0 = density_sb[2025]
n_mc = 5000
results = defaultdict(list)
for _ in range(n_mc):
    # Beta 后验：a = n_事件+1, b = n_风险+1
    es = era_stats['当前']
    lam_b_mc = np.random.beta(es['n_w2c']+1, es['n_w']-es['n_w2c']+1)
    lam_r_mc = np.random.beta(es['n_c2w']+1, es['n_c']-es['n_c2w']+1)
    pi_mc = lam_b_mc / (lam_b_mc + lam_r_mc)
    rate = lam_b_mc + lam_r_mc
    # 解析解：p(t) = pi - (pi - p0) e^{-rate t}
    def t_to_frac(frac):
        p_target = pi_mc * frac
        if p_target <= p0:  # 已超过
            return 0.0
        return -math.log((pi_mc - p_target) / (pi_mc - p0)) / rate
    for frac in (0.90, 0.95, 0.99):
        results[frac].append(t_to_frac(frac))

sat = {}
for frac, ts in results.items():
    ts = np.array(ts)
    sat[f'{int(frac*100)}%'] = dict(
        median=float(np.median(ts)),
        p05=float(np.percentile(ts, 5)),
        p95=float(np.percentile(ts, 95)),
        prob_reached=float(np.mean(ts <= 5)),
    )

# ---------- 5. 输出 ----------
out = {
    'density_sb_by_year': {str(y): density_sb[y] for y in years},
    'density_all_1989_plus': {str(y): density_all[y] for y in years if y >= 1989},
    'terminations_by_year': dict(sorted(term_by_year.items())),
    'era_stats': era_stats,
    'p0_2025': p0,
    'saturation_mc': sat,
    'n_countries': len(countries66),
}
with open('probe20_results.json', 'w') as f:
    json.dump(out, f, indent=1, default=str)

# 打印摘要
print('=== 年度破缺密度（66国，国家冲突口径）关键年份 ===')
for y in [1946, 1965, 1975, 1985, 1989, 1995, 2005, 2015, 2020, 2023, 2024, 2025]:
    print(f'  {y}: {density_sb[y]:.3f}')
print('\n=== 四时代时变转移率 ===')
for name, s in era_stats.items():
    print(f'  {name}: λ_b={s["lam_b"]:.4f} (n={s["n_w"]}, w2c={s["n_w2c"]}), '
          f'λ_r={s["lam_r"]:.4f} (n={s["n_c"]}, c2w={s["n_c2w"]}), '
          f'π={s["pi_c"]:.3f} if pi else "—", τ={s["tau"]:.2f} if tau else "—"')
print('\n=== 终止（补缺）事件：年分布摘要 ===')
t_years = sorted(term_by_year.items())
print(f'  1946-2024 总终止: {sum(v for _,v in t_years)}')
decades = defaultdict(int)
for y, v in t_years:
    decades[y//10*10] += v
for d in sorted(decades):
    print(f'  {d}s: {decades[d]}')
print('\n=== 蒙特卡洛饱和期（当前时代 λ，5000 样本） ===')
for frac, s in sat.items():
    print(f'  {frac}饱和: 中位 {s["median"]:.2f} 年 [5%: {s["p05"]:.2f}, 95%: {s["p95"]:.2f}], '
          f'5年内到达概率 {s["prob_reached"]:.2%}')
print('\np0(2025) =', p0)
