#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe6_wvs.py — WVS Wave 7 个体级数据三尺度检验
国家 = 纤维, 个体 = 随机点, 集体量 = 国家均值/信任率
检验: η² 方差分解 / CLT 判别 / bootstrap 排序稳定性 / 区域聚合
"""
import csv, json, random
from collections import defaultdict
from statistics import mean, pstdev

CSV = 'WVS_Cross-National_Wave_7_csv_v6_0.csv'

REGION = {
    # Europe
    'AND':'Europe','ARM':'Europe','CYP':'Europe','CZE':'Europe','DEU':'Europe',
    'GBR':'Europe','GRC':'Europe','NIR':'Europe','NLD':'Europe','ROU':'Europe',
    'RUS':'Europe','SRB':'Europe','SVK':'Europe','TUR':'Europe','UKR':'Europe',
    # Asia
    'BGD':'Asia','CHN':'Asia','HKG':'Asia','IDN':'Asia','IND':'Asia','IRN':'Asia',
    'IRQ':'Asia','JPN':'Asia','KAZ':'Asia','KGZ':'Asia','KOR':'Asia','LBN':'Asia',
    'MAC':'Asia','MDV':'Asia','MMR':'Asia','MNG':'Asia','MYS':'Asia','PAK':'Asia',
    'PHL':'Asia','SGP':'Asia','THA':'Asia','TJK':'Asia','TWN':'Asia','UZB':'Asia',
    'VNM':'Asia','JOR':'Asia',
    # Africa
    'EGY':'Africa','ETH':'Africa','KEN':'Africa','LBY':'Africa','MAR':'Africa',
    'NGA':'Africa','TUN':'Africa','ZWE':'Africa',
    # Americas
    'ARG':'Americas','BOL':'Americas','BRA':'Americas','CAN':'Americas','CHL':'Americas',
    'COL':'Americas','ECU':'Americas','GTM':'Americas','MEX':'Americas','NIC':'Americas',
    'PER':'Americas','PRI':'Americas','URY':'Americas','USA':'Americas','VEN':'Americas',
    # Oceania
    'AUS':'Oceania','NZL':'Oceania',
}

def load():
    """流式读取, 只保留需要的列; Q49/Q50 取 1-10, Q57 取 1-2"""
    data = []  # (alpha, region, q49, q50, q57)
    with open(CSV, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            a = row['B_COUNTRY_ALPHA']
            q49 = row['Q49']; q50 = row['Q50']; q57 = row['Q57']
            try:
                q49 = int(q49); q50 = int(q50); q57 = int(q57)
            except ValueError:
                continue
            if not (1 <= q49 <= 10 and 1 <= q50 <= 10 and q57 in (1, 2)):
                continue
            data.append((a, REGION.get(a, 'Other'), q49, q50, q57))
    return data

def country_stats(data):
    """国家级统计: 样本数, 均值, 内部 std"""
    agg = defaultdict(list)
    for a, reg, q49, q50, q57 in data:
        agg[a].append((q49, q50, q57))
    stats = {}
    for a, rows in agg.items():
        q49s = [x[0] for x in rows]
        q57s = [x[2] for x in rows]
        stats[a] = {
            'n': len(rows),
            'mean49': mean(q49s),
            'std49': pstdev(q49s),
            'trust_rate': mean(q57s),  # 1=trust -> rate of 1
        }
    return stats

def eta_squared(values_by_group):
    """η² = SSB/SST"""
    allv = [v for vs in values_by_group.values() for v in vs]
    grand = mean(allv)
    ss_tot = sum((v - grand) ** 2 for v in allv)
    ss_b = sum(len(vs) * (mean(vs) - grand) ** 2 for vs in values_by_group.values())
    return ss_b / ss_tot if ss_tot else 0.0

def clt_check(stats):
    """观察到的国家均值散布 vs CLT 预期 σ/√n"""
    means = [s['mean49'] for s in stats.values()]
    ns = [s['n'] for s in stats.values()]
    stds = [s['std49'] for s in stats.values()]
    obs_spread = pstdev(means)
    # 池化个体 std
    nbar = mean(ns)
    pooled_var = sum((n - 1) * sd ** 2 for n, sd in zip(ns, stds)) / (sum(ns) - len(ns))
    clt_spread = (pooled_var / nbar) ** 0.5
    return obs_spread, clt_spread, pooled_var ** 0.5

def bootstrap_rank_stability(data, nboot=200, seed=42):
    """bootstrap 重采样个体(国家内), 重算国家均值, 与原始排序比 Spearman ρ"""
    random.seed(seed)
    by_country = defaultdict(list)
    for a, reg, q49, q50, q57 in data:
        by_country[a].append(q49)
    orig = {a: mean(v) for a, v in by_country.items()}
    order = sorted(orig, key=lambda a: orig[a])  # 按均值升序
    orig_rank = {a: i for i, a in enumerate(order)}
    rhos = []
    for _ in range(nboot):
        boot_mean = {}
        for a, v in by_country.items():
            m = len(v)
            boot_mean[a] = mean(random.choice(v) for _ in range(m))
        # Spearman
        ranks = sorted(order, key=lambda a: boot_mean[a])
        rank_map = {a: i for i, a in enumerate(ranks)}
        d2 = sum((orig_rank[a] - rank_map[a]) ** 2 for a in order)
        n = len(order)
        rho = 1 - 6 * d2 / (n * (n ** 2 - 1))
        rhos.append(rho)
    return mean(rhos), min(rhos), max(rhos)

def region_analysis(data):
    """区域=纤维 的 η² 与排序稳定性(与探针⑤对齐)"""
    by_reg = defaultdict(list)
    for a, reg, q49, q50, q57 in data:
        by_reg[reg].append(q49)
    eta = eta_squared(by_reg)
    reg_mean = {r: mean(v) for r, v in by_reg.items()}
    return eta, reg_mean

def main():
    print('加载 WVS Wave 7 ...')
    data = load()
    print(f'有效样本: {len(data)}  国家数: {len({d[0] for d in data})}')

    stats = country_stats(data)
    ns = [s['n'] for s in stats.values()]
    print(f'\n每国样本数: min={min(ns)} max={max(ns)} mean={mean(ns):.0f}')

    # 1) 国家级方差分解
    by_country = defaultdict(list)
    for a, reg, q49, q50, q57 in data:
        by_country[a].append(q49)
    eta_c = eta_squared(by_country)
    print(f'\n[1] 方差分解 (Q49 生活满意度)')
    print(f'    η²(国家) = {eta_c:.4f}  -> 国家结构解释 {100*eta_c:.1f}% 的个体差异')

    # 2) CLT 判别
    obs_spread, clt_spread, pooled_sd = clt_check(stats)
    ratio = obs_spread / clt_spread if clt_spread else float('inf')
    print(f'\n[2] CLT 判别 (刚性 vs 随机)')
    print(f'    观察国家均值散布 = {obs_spread:.4f}')
    print(f'    CLT 预期(纯随机采样) = {clt_spread:.4f}')
    print(f'    比值 = {ratio:.1f}  (>>1 = 国家差异是结构性的, 非采样噪声)')

    # 3) bootstrap 排序稳定性
    rho_mean, rho_min, rho_max = bootstrap_rank_stability(data)
    print(f'\n[3] 排序稳定性 (bootstrap 200 次, Q49 国家均值排序)')
    print(f'    平均 Spearman ρ = {rho_mean:.4f}  (min={rho_min:.3f}, max={rho_max:.3f})')
    print(f'    ρ 接近 1 = 国家排序由结构锁定, 不随个体抽样涨落')

    # 4) 区域聚合
    eta_r, reg_mean = region_analysis(data)
    print(f'\n[4] 区域=纤维 聚合 (Q49)')
    print(f'    η²(区域) = {eta_r:.4f}  -> 区域结构解释 {100*eta_r:.1f}%')
    for r in sorted(reg_mean, key=lambda r: -reg_mean[r]):
        print(f'      {r:9s} 均值 {reg_mean[r]:.2f}')

    # 5) 信任率 Q57
    trust_by_country = defaultdict(list)
    for a, reg, q49, q50, q57 in data:
        trust_by_country[a].append(q57)
    trust_rates = {a: mean(v) for a, v in trust_by_country.items()}
    tr = list(trust_rates.values())
    print(f'\n[5] 信任率 Q57 (跨国家散布)')
    print(f'    国家信任率: min={min(tr):.3f} max={max(tr):.3f} std={pstdev(tr):.4f}')
    top = sorted(trust_rates, key=lambda a: -trust_rates[a])[:8]
    bot = sorted(trust_rates, key=lambda a: trust_rates[a])[:8]
    print(f'    最高: {[(a, round(trust_rates[a],3)) for a in top]}')
    print(f'    最低: {[(a, round(trust_rates[a],3)) for a in bot]}')

    # 汇总
    print(f'\n=== 判别判定 ===')
    print(f'η²(国家)={eta_c:.3f}, 均值散布/CLT 预期={ratio:.1f}, bootstrap ρ={rho_mean:.3f}')
    if ratio > 3 and rho_mean > 0.9:
        print('判定: 国家间差异远大于抽样噪声 + 排序稳定 -> 集体差异由结构锁定 (宏观锁定)')
    else:
        print('判定: 证据不足以判定结构锁定')

    out = {
        'N': len(data), 'countries': len(stats),
        'eta2_country': eta_c, 'eta2_region': eta_r,
        'obs_spread': obs_spread, 'clt_spread': clt_spread, 'ratio': ratio,
        'boot_rho_mean': rho_mean,
    }
    with open('probe6_results.json', 'w') as f:
        json.dump(out, f, indent=2)
    print('\n结果已存 probe6_results.json')

if __name__ == '__main__':
    main()
