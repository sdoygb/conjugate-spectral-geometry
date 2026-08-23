#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe7_covariates.py — WVS Wave 7 + GDP/教育协变量: "什么结构锁定排序"
问题: 国家(纤维)排序被结构锁定 (探针⑥ ρ=0.995)。这个锁是 GDP/教育 可还原的吗?
设计:
  A) GDP 协变量: 国家均值满意度 vs log(GDPpc) 的 R²; GDP 残差化后个体级 bootstrap
     排序稳定性(与探针⑥同款); 个体级 GDP 调整后 η²(国家) 的下降幅度
  B) 教育协变量: 个体级教育梯度(国家内 Q275 vs Q49); 国家均值教育 vs 满意度;
     教育残差化后 η²(国家)
  C) 组合: GDP + 教育 同时调整后 η²(国家)
判定: 残差化后排序稳定性仍 ≈ 原始(0.995) 且 η² 下降 <20% -> 锁定不可还原为 GDP/教育
       (文化/制度结构锁定); η² 大幅下降 + 排序塌缩 -> 锁定由 GDP/教育 解释
"""
import csv, json, math, random
from collections import defaultdict
from statistics import mean, pstdev

CSV = 'WVS_Cross-National_Wave_7_csv_v6_0.csv'
GDP_JSON = 'wb_gdp.json'

def load_wvs():
    """流式读取: Q49 满意度, Q57 信任, Q275 教育; 国家 = B_COUNTRY_ALPHA"""
    data = []  # (alpha, q49, q57, q275)
    with open(CSV, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            a = row['B_COUNTRY_ALPHA']
            try:
                q49 = int(row['Q49']); q57 = int(row['Q57']); q275 = int(row['Q275'])
            except ValueError:
                continue
            if not (1 <= q49 <= 10 and q57 in (1, 2)):
                continue
            if not (1 <= q275 <= 8):
                q275 = None
            data.append((a, q49, q57, q275))
    return data

def load_gdp():
    """wb_gdp.json -> {iso3: mean GDPpc(2017-2022)}"""
    meta, records = json.load(open(GDP_JSON))
    by = defaultdict(list)
    for rec in records:
        iso = rec['countryiso3code']
        try:
            yr = int(rec['date'])
        except ValueError:
            continue
        if 2017 <= yr <= 2022 and rec['value'] is not None:
            by[iso].append(rec['value'])
    gdp = {}
    for iso, vals in by.items():
        if len(vals) >= 2:
            gdp[iso] = mean(vals)
    return gdp

def pearson_r(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return 0.0
    return cov / math.sqrt(vx * vy)

def ols_coef(xs, ys):
    """y ~ a + b*x 返回 (a, b)"""
    mx, my = mean(xs), mean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    if vx == 0:
        return my, 0.0
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / vx
    return my - b * mx, b

def eta_squared(values_by_group):
    """η² = SSB/SST"""
    allv = [v for vs in values_by_group.values() for v in vs]
    grand = mean(allv)
    ss_tot = sum((v - grand) ** 2 for v in allv)
    ss_b = sum(len(vs) * (mean(vs) - grand) ** 2 for vs in values_by_group.values())
    return ss_b / ss_tot if ss_tot else 0.0

def boot_rank_stability(by_country_values, nboot=200, seed=42):
    """个体级 bootstrap 重采样(国家内, 与探针⑥同款): 重算国家均值排序的 Spearman ρ
    by_country_values: {country: [个体值,...]}  (原始值或残差化值均可)
    """
    random.seed(seed)
    countries = list(by_country_values.keys())
    orig = {a: mean(v) for a, v in by_country_values.items()}
    order = sorted(countries, key=lambda a: orig[a])
    orig_rank = {a: i for i, a in enumerate(order)}
    rhos = []
    for _ in range(nboot):
        boot_mean = {}
        for a in countries:
            v = by_country_values[a]
            m = len(v)
            boot_mean[a] = mean(random.choice(v) for _ in range(m))
        ranks = sorted(order, key=lambda a: boot_mean[a])
        rank_map = {a: i for i, a in enumerate(ranks)}
        d2 = sum((orig_rank[a] - rank_map[a]) ** 2 for a in order)
        n = len(order)
        rhos.append(1 - 6 * d2 / (n * (n ** 2 - 1)))
    return mean(rhos), min(rhos)

def main():
    print('加载 WVS + GDP ...')
    data = load_wvs()
    gdp = load_gdp()
    n_country = len({d[0] for d in data})
    print(f'样本 {len(data)}, 国家 {n_country}, GDP 可匹配国家 {len(gdp)}')

    agg = defaultdict(list)
    for a, q49, q57, q275 in data:
        agg[a].append((q49, q57, q275))

    # 原始: 国家 -> 个体 Q49 列表
    by_c_raw = {a: [x[0] for x in rows] for a, rows in agg.items()}
    rho_raw, rho_raw_min = boot_rank_stability(by_c_raw)
    print(f'[基准] 原始排序稳定性 (个体级 bootstrap, 与探针⑥同款): ρ={rho_raw:.4f} (min={rho_raw_min:.3f})')

    # ============ A) GDP 协变量 ============
    print('\n============ A) GDP 协变量 (人均 GDP 对数) ============')
    gdp_ok = {a: gdp[a] for a in agg if a in gdp}
    xs = [math.log(gdp_ok[a]) for a in gdp_ok]
    ys = [mean([x[0] for x in agg[a]]) for a in gdp_ok]
    r = pearson_r(xs, ys)
    print(f'[A1] 国家均值满意度 vs log(GDPpc): r={r:.4f}, R²={r*r:.4f}  (N={len(gdp_ok)} 国)')

    a0, b = ols_coef(xs, ys)
    print(f'[A2] OLS: mean49 = {a0:.3f} + {b:.4f}·log(GDPpc)')

    # GDP 残差化个体值: q49 - (a0 + b*logGDP_c)  (logGDP 在国家内恒定 = 国家均值平移)
    by_c_resid = {}
    for a in gdp_ok:
        shift = a0 + b * math.log(gdp_ok[a])
        by_c_resid[a] = [q49 - shift for q49 in by_c_raw[a]]
    rho_resid, rho_resid_min = boot_rank_stability(by_c_resid)
    print(f'[A3] GDP 残差化后排序稳定性: ρ={rho_resid:.4f} (min={rho_resid_min:.3f})')
    print(f'     (原始 ρ={rho_raw:.4f}; Δρ={rho_resid - rho_raw:+.4f})')

    # 个体级 GDP 调整后 η²(国家)
    eta_adj = eta_squared(by_c_resid)
    print(f'[A4] 个体级 GDP 调整后 η²(国家) = {eta_adj:.4f} (原始 {eta_squared(by_c_raw):.4f})')

    # ============ B) 教育协变量 ============
    print('\n============ B) 教育协变量 (Q275, 1-8) ============')
    grad = []
    for a, rows in agg.items():
        edu_q = [(x[2], x[0]) for x in rows if x[2] is not None]
        if len(edu_q) >= 30:
            grad.append(pearson_r([p[0] for p in edu_q], [p[1] for p in edu_q]))
    print(f'[B1] 国家内教育-满意度相关: 平均 r={mean(grad):.4f}, 国家间 std={pstdev(grad):.4f} (N={len(grad)} 国)')

    epairs = [(a, rows) for a, rows in agg.items() if any(x[2] is not None for x in rows)]
    er = pearson_r([mean([x[2] for x in rows if x[2] is not None]) for a, rows in epairs],
                   [mean([x[0] for x in rows]) for a, rows in epairs])
    print(f'[B2] 国家均值教育 vs 满意度: r={er:.4f}, R²={er*er:.4f} (N={len(epairs)} 国)')

    # 个体级教育残差化: 池化 OLS q49 ~ q275
    e0, eb = ols_coef([x[2] for a, rows in agg.items() for x in rows if x[2] is not None],
                      [x[0] for a, rows in agg.items() for x in rows if x[2] is not None])
    by_c_edu = defaultdict(list)
    for a, rows in agg.items():
        for x in rows:
            if x[2] is not None:
                by_c_edu[a].append(x[0] - (e0 + eb * x[2]))
    eta_edu = eta_squared(by_c_edu)
    print(f'[B3] 个体级教育调整后 η²(国家) = {eta_edu:.4f} (原始 {eta_squared(by_c_raw):.4f})')
    print(f'     池化教育梯度: b_edu={eb:.4f}')

    # ============ C) 组合 GDP+教育 ============
    print('\n============ C) GDP + 教育 组合 ============')
    # 个体级: q49 ~ logGDP + 教育 双变量 OLS 残差
    combo = []
    for a, rows in agg.items():
        if a not in gdp_ok:
            continue
        lg = math.log(gdp_ok[a])
        for x in rows:
            if x[2] is not None:
                combo.append((lg, x[2], x[0]))
    cx = [p[0] for p in combo]; cz = [p[1] for p in combo]; cy = [p[2] for p in combo]
    n = len(combo)
    mx, mz, my = mean(cx), mean(cz), mean(cy)
    vx = sum((x - mx) ** 2 for x in cx)
    vz = sum((z - mz) ** 2 for z in cz)
    vxz = sum((x - mx) * (z - mz) for x, z in zip(cx, cz))
    vxy = sum((x - mx) * (y - my) for x, y in zip(cx, cy))
    vzy = sum((z - mz) * (y - my) for z, y in zip(cz, cy))
    denom = vx * vz - vxz ** 2
    if abs(denom) < 1e-12:
        print('  组合回归奇异, 跳过')
    else:
        b1 = (vz * vxy - vxz * vzy) / denom
        b2 = (vx * vzy - vxz * vxy) / denom
        b0 = my - b1 * mx - b2 * mz
        by_c_combo = defaultdict(list)
        idx = 0
        for a, rows in agg.items():
            if a not in gdp_ok:
                continue
            lg = math.log(gdp_ok[a])
            for x in rows:
                if x[2] is not None:
                    by_c_combo[a].append(cy[idx] - (b0 + b1 * lg + b2 * cz[idx])); idx += 1
        eta_combo = eta_squared(by_c_combo)
        print(f'[C1] GDP+教育 双调整后 η²(国家) = {eta_combo:.4f} (原始 {eta_squared(by_c_raw):.4f})')
        print(f'     系数: b_logGDP={b1:.4f}, b_edu={b2:.4f}, b0={b0:.3f}')

    # ============ 判定 ============
    print('\n============ 判定 ============')
    eta_raw = eta_squared(by_c_raw)
    d_eta_gdp = (eta_raw - eta_adj) / eta_raw
    d_eta_edu = (eta_raw - eta_edu) / eta_raw
    print(f'GDP R²={r*r:.3f} | GDP残差化 Δρ={rho_resid - rho_raw:+.3f} | '
          f'η² 下降: GDP后 {100*d_eta_gdp:.1f}%, 教育后 {100*d_eta_edu:.1f}%')
    if rho_resid > 0.9 and d_eta_gdp < 0.2:
        print('残差化后排序仍稳定 + η²几乎不变 -> 锁定不可还原为 GDP/教育 (文化/制度结构锁定)')
    elif rho_resid > 0.7:
        print('残差化后排序部分稳定 -> GDP 是锁定的部分来源, 但非全部')
    else:
        print('残差化后排序明显塌缩 -> 排序锁定主要由 GDP 解释')

    out = {
        'N': len(data), 'countries': n_country,
        'rho_raw': rho_raw,
        'gdp_r': r, 'gdp_r2': r * r,
        'rho_gdp_resid': rho_resid,
        'eta2_raw': eta_raw, 'eta2_gdp_adj': eta_adj, 'eta2_edu_adj': eta_edu,
        'd_eta_gdp_pct': 100 * d_eta_gdp, 'd_eta_edu_pct': 100 * d_eta_edu,
        'edu_within_r_mean': mean(grad), 'edu_between_r': er,
    }
    with open('probe7_results.json', 'w') as f:
        json.dump(out, f, indent=2)
    print('\n结果已存 probe7_results.json')

if __name__ == '__main__':
    main()
