#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe9_structure.py — WVS Wave 7 个体级: 锁的结构级候选检验
问题(续探针⑧): GDP/教育/WGI/Hofstede 标量都不是锁。锁在"纤维结构"层——
  结构级候选: 地理集群(WB区域) / 语言家族 / 制度组合模式(WGI k-means) / 文化组合模式(Hofstede k-means)
设计(与探针⑥⑦⑧同口径):
  对每个分组 G (区域/语族/制度簇/文化簇):
    G1: η²(G) 个体级 — 分组解释多少个体方差
    G2: 国家均值级 R²(G→均值) — 分组解释多少国家间均值方差(锁的直接载体)
    G3: 组内排序稳定性 — 组内国家均值的 bootstrap ρ(≥3国组)
    G4: 残差化(减去组均值)后 η²(国家) 与 bootstrap ρ — 去掉组结构后锁是否还在
判定:
  ρ_resid 塌缩(→0~0.5) -> 该分组解释了锁(结构级锁定, 比标量更接近纤维结构)
  ρ_resid 仍 ≈0.99  -> 锁比该分组更细(组内仍有稳定排序), 锁在更精细的配置
数据: WVS_Cross-National_Wave_7_csv_v6_0.csv, wb_countries.json, qog_std_ts_jan25.csv, hofstede.csv
"""
import csv, json, math, random
import numpy as np
from collections import defaultdict
from statistics import mean, pstdev

CSV = 'WVS_Cross-National_Wave_7_csv_v6_0.csv'
WB = 'wb_countries.json'
QOG = 'qog_std_ts_jan25.csv'
HOF = 'hofstede.csv'

WGI_DIMS = ['wbgi_vae', 'wbgi_pve', 'wbgi_gee', 'wbgi_rqe', 'wbgi_rle', 'wbgi_cce']
HOF_DIMS = ['pdi', 'idv', 'mas', 'uai', 'ltowvs', 'ivr']
HOF_ALIAS = {
    'AUL': 'AUS', 'BAN': 'BGD', 'BOS': 'BIH', 'BUF': 'BFA', 'CAF': 'CAF',
    'CHI': 'CHN', 'COS': 'CRI', 'CRO': 'HRV', 'SAL': 'SLV', 'GEE': 'DEU',
    'GER': 'DEU', 'GRE': 'GRC', 'GUA': 'GTM', 'HOK': 'HKG', 'ICE': 'ISL',
    'IDO': 'IDN', 'IRA': 'IRN', 'IRE': 'IRL', 'KYR': 'KGZ', 'LAT': 'LVA',
    'LIT': 'LTU', 'MAL': 'MYS', 'MOL': 'MDA', 'MOR': 'MAR', 'NET': 'NLD',
    'NIG': 'NGA', 'PHI': 'PHL', 'PUE': 'PRI', 'ROM': 'ROU', 'SER': 'SRB',
    'SIN': 'SGP', 'SLK': 'SVK', 'SLV': 'SVN', 'SAF': 'ZAF', 'SPA': 'ESP',
    'SWI': 'CHE', 'TAI': 'TWN', 'TAN': 'TZA', 'TRI': 'TTO', 'VIE': 'VNM',
    'URU': 'URY', 'ALG': 'DZA', 'DEN': 'DNK', 'BUL': 'BGR', 'EGY': 'EGY',
}
SKIP_HOF = {'AFE', 'AFW', 'ARA', 'ECA', 'BEF', 'SWF', 'SWG', 'SAW'}

# 语言家族 (主导/国家语言, Ethnologue/Glottolog 风格分类, 66 国)
LANG_FAM = {
    'AND': 'Romance', 'ARG': 'Romance', 'ARM': 'Armenian', 'AUS': 'Germanic',
    'BGD': 'IndoAryan', 'BOL': 'Romance', 'BRA': 'Romance', 'CAN': 'Germanic',
    'CHL': 'Romance', 'CHN': 'SinoTibetan', 'COL': 'Romance', 'CYP': 'Greek',
    'CZE': 'Slavic', 'DEU': 'Germanic', 'ECU': 'Romance', 'EGY': 'Semitic',
    'ETH': 'AfroAsiatic', 'GBR': 'Germanic', 'GRC': 'Greek', 'GTM': 'Romance',
    'HKG': 'SinoTibetan', 'IDN': 'Austronesian', 'IND': 'IndoAryan', 'IRN': 'Iranian',
    'IRQ': 'Semitic', 'JOR': 'Semitic', 'JPN': 'Japonic', 'KAZ': 'Turkic',
    'KEN': 'NigerCongo', 'KGZ': 'Turkic', 'KOR': 'Koreanic', 'LBN': 'Semitic',
    'LBY': 'Semitic', 'MAC': 'SinoTibetan', 'MAR': 'Semitic', 'MDV': 'IndoAryan',
    'MEX': 'Romance', 'MMR': 'SinoTibetan', 'MNG': 'Mongolic', 'MYS': 'Austronesian',
    'NGA': 'NigerCongo', 'NIC': 'Romance', 'NIR': 'Germanic', 'NLD': 'Germanic',
    'NZL': 'Germanic', 'PAK': 'IndoAryan', 'PER': 'Romance', 'PHL': 'Austronesian',
    'PRI': 'Romance', 'ROU': 'Romance', 'RUS': 'Slavic', 'SGP': 'SinoTibetan',
    'SRB': 'Slavic', 'SVK': 'Slavic', 'THA': 'TaiKadai', 'TJK': 'Iranian',
    'TUN': 'Semitic', 'TUR': 'Turkic', 'TWN': 'SinoTibetan', 'UKR': 'Slavic',
    'URY': 'Romance', 'USA': 'Germanic', 'UZB': 'Turkic', 'VEN': 'Romance',
    'VNM': 'Austroasiatic', 'ZWE': 'NigerCongo',
}
LANG_FAM_CN = {
    'Romance': '罗曼', 'Armenian': '亚美尼亚', 'Germanic': '日耳曼', 'IndoAryan': '印度-雅利安',
    'SinoTibetan': '汉藏', 'Greek': '希腊', 'Slavic': '斯拉夫', 'Semitic': '闪米特',
    'AfroAsiatic': '亚非', 'Austronesian': '南岛', 'Iranian': '伊朗', 'Japonic': '日本语系',
    'Turkic': '突厥', 'NigerCongo': '尼日尔-刚果', 'Koreanic': '朝鲜语系', 'Mongolic': '蒙古',
    'TaiKadai': '侗台', 'Austroasiatic': '南亚',
}


def load_wvs():
    data = []
    with open(CSV, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            a = row['B_COUNTRY_ALPHA']
            try:
                q49 = int(row['Q49'])
            except ValueError:
                continue
            if not (1 <= q49 <= 10):
                continue
            data.append((a, q49))
    return data


def load_wb_regions():
    resp = json.load(open(WB))
    out = {}
    for rec in resp[1]:
        iso = rec['id']
        reg = rec['region']['value'].strip()
        if reg and reg != 'Aggregates':
            out[iso] = reg
    return out


def load_qog_wgi():
    by = defaultdict(lambda: defaultdict(list))
    with open(QOG, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                yr = int(row['year'])
            except (ValueError, TypeError):
                continue
            if not (2017 <= yr <= 2022):
                continue
            iso = row.get('ccodealp')
            for dim in WGI_DIMS:
                v = row.get(dim)
                if v not in (None, ''):
                    try:
                        by[iso][dim].append(float(v))
                    except ValueError:
                        pass
    out = {}
    for iso, d in by.items():
        if all(len(d.get(x, [])) >= 1 for x in WGI_DIMS):
            out[iso] = {x: mean(d[x]) for x in WGI_DIMS}
    return out


def load_hofstede():
    out = {}
    with open(HOF, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f, delimiter=';')
        for row in r:
            c = row['ctr']
            if c in SKIP_HOF:
                continue
            iso = HOF_ALIAS.get(c, c)
            vals = {}
            ok = True
            for dim in HOF_DIMS:
                v = row.get(dim)
                if v in (None, '', '#NULL!'):
                    ok = False
                    break
                try:
                    vals[dim] = float(v)
                except ValueError:
                    ok = False
                    break
            if ok and iso not in out:
                out[iso] = vals
    return out


def eta_squared(values_by_group):
    allv = [v for vs in values_by_group.values() for v in vs]
    grand = mean(allv)
    ss_tot = sum((v - grand) ** 2 for v in allv)
    ss_b = sum(len(vs) * (mean(vs) - grand) ** 2 for vs in values_by_group.values())
    return ss_b / ss_tot if ss_tot else 0.0


def boot_rank_stability(by_country_values, nboot=200, seed=42):
    rng = np.random.default_rng(seed)
    countries = list(by_country_values.keys())
    orig = {a: mean(v) for a, v in by_country_values.items()}
    order = sorted(countries, key=lambda a: orig[a])
    orig_rank = {a: i for i, a in enumerate(order)}
    arrs = {a: np.asarray(by_country_values[a], dtype=float) for a in countries}
    sizes = {a: len(arrs[a]) for a in countries}
    n = len(order)
    rhos = []
    for _ in range(nboot):
        boot_mean = {}
        for a in countries:
            m = sizes[a]
            boot_mean[a] = arrs[a][rng.integers(0, m, m)].mean()
        ranks = sorted(order, key=lambda a: boot_mean[a])
        rank_map = {a: i for i, a in enumerate(ranks)}
        d2 = sum((orig_rank[a] - rank_map[a]) ** 2 for a in order)
        rhos.append(1 - 6 * d2 / (n * (n ** 2 - 1)))
    return mean(rhos), min(rhos)


def kmeans(X, k, iters=100, seed=7):
    """X: list of (label, [features]) -> {label: cluster}"""
    random.seed(seed)
    items = list(X)
    pts = [p for _, p in items]
    n, d = len(pts), len(pts[0])
    # k-means++ 初始化
    cents = [pts[random.randrange(n)]]
    for _ in range(k - 1):
        dsq = [min(sum((p[j] - c[j]) ** 2 for j in range(d)) for c in cents) for p in pts]
        tot = sum(dsq)
        if tot == 0:
            break
        r = random.random() * tot
        acc = 0.0
        for i in range(n):
            acc += dsq[i]
            if acc >= r:
                cents.append(pts[i])
                break
    assign = [0] * n
    for _ in range(iters):
        for i in range(n):
            assign[i] = min(range(len(cents)),
                            key=lambda c: sum((pts[i][j] - cents[c][j]) ** 2 for j in range(d)))
        newc = []
        for c in range(len(cents)):
            members = [pts[i] for i in range(n) if assign[i] == c]
            if members:
                newc.append([mean(members[i][j] for i in range(len(members))) for j in range(d)])
            else:
                newc.append(cents[c])
        cents = newc
    return {items[i][0]: assign[i] for i in range(n)}


def standardize_profile(cov, dims):
    """返回 {iso3: [z-scores]} 与 {iso3: {dim: z}}"""
    out = {}
    for a in cov:
        row = []
        for dim in dims:
            vals = [cov[b][dim] for b in cov]
            mu, sd = mean(vals), pstdev(vals)
            row.append((cov[a][dim] - mu) / sd if sd else 0.0)
        out[a] = row
    return out


def run_group(name, by_country, group_of, nboot=200):
    """by_country: {iso3: [values]}; group_of: {iso3: group_label}"""
    print(f'\n============ {name} ============')
    grp_countries = {a for a in by_country if a in group_of}
    n_match = len(grp_countries)
    print(f'国家匹配: {n_match} / {len(by_country)}')
    if n_match < 8:
        print('  覆盖太少, 跳过')
        return None
    # G1: η²(分组) 个体级
    vals_by_g = defaultdict(list)
    for a in grp_countries:
        vals_by_g[group_of[a]].extend(by_country[a])
    eta_g = eta_squared(dict(vals_by_g))
    # G2: 国家均值级 R²(分组 → 均值)
    cmeans = {a: mean(by_country[a]) for a in grp_countries}
    grand = mean(cmeans.values())
    ss_tot = sum((cmeans[a] - grand) ** 2 for a in cmeans)
    gmean = {g: mean(cmeans[a] for a in grp_countries if group_of[a] == g)
             for g in set(group_of[a] for a in grp_countries)}
    ss_b = sum(sum((cmeans[a] - gmean[group_of[a]]) ** 2 for a in grp_countries if group_of[a] == g)
               for g in gmean)
    r2_g = ss_b / ss_tot if ss_tot else 0.0
    # G3: 组内排序稳定性 (≥3国组)
    within_rhos = {}
    for g in gmean:
        members = [a for a in grp_countries if group_of[a] == g]
        if len(members) >= 3:
            sub = {a: by_country[a] for a in members}
            rho_g, rho_g_min = boot_rank_stability(sub, nboot=min(nboot, 50))
            within_rhos[g] = (len(members), round(rho_g, 4))
    # G4: 残差化(减组均值)后 η²(国家) 与 ρ
    by_c_resid = {}
    for a in grp_countries:
        g = group_of[a]
        shift = mean(q for a in grp_countries if group_of[a] == g for q in by_country[a])
        by_c_resid[a] = [q - shift for q in by_country[a]]
    eta_res = eta_squared(by_c_resid)
    rho_res, rho_res_min = boot_rank_stability(by_c_resid, nboot=nboot)
    # 基准: 同子集原始 ρ
    sub_raw = {a: by_country[a] for a in grp_countries}
    rho_raw, rho_raw_min = boot_rank_stability(sub_raw, nboot=nboot)
    eta_raw = eta_squared(sub_raw)
    print(f'  [子集基准] η²(国家)={eta_raw:.4f}, ρ={rho_raw:.4f} (min={rho_raw_min:.3f})')
    print(f'  G1 η²({name})={eta_g:.4f}  |  G2 R²(分组→国家均值)={r2_g:.4f}')
    print(f'  G3 组内 ρ: ' + ', '.join(f'{g}(n={v[0]})={v[1]}' for g, v in
          sorted(within_rhos.items(), key=lambda kv: -kv[1][0])[:8]) or '无≥3国组')
    print(f'  G4 残差化后: η²(国家)={eta_res:.4f} (Δ={eta_res - eta_raw:+.4f}), ρ={rho_res:.4f} (min={rho_res_min:.3f})')
    return {'n': n_match, 'eta_group': eta_g, 'r2_group_country': r2_g,
            'within_rho': within_rhos, 'eta2_resid': eta_res, 'rho_resid': rho_res,
            'rho_resid_min': rho_res_min, 'rho_raw': rho_raw}


def main():
    print('加载 WVS / WB区域 / WGI / Hofstede ...')
    data = load_wvs()
    wb = load_wb_regions()
    wgi = load_qog_wgi()
    hof = load_hofstede()
    print(f'样本 {len(data)}, WVS国家 {len({d[0] for d in data})}, WB区域覆盖 {len(wb)}, '
          f'WGI覆盖 {len(wgi)}, Hofstede覆盖 {len(hof)}')

    agg = defaultdict(list)
    for a, q49 in data:
        agg[a].append(q49)
    by_c_raw = dict(agg)
    rho_raw, rho_raw_min = boot_rank_stability(by_c_raw)
    eta_raw = eta_squared(by_c_raw)
    print(f'\n[全库基准] η²(国家)={eta_raw:.4f}, 排序稳定性 ρ={rho_raw:.4f} (min={rho_raw_min:.3f})')

    res = {'raw': {'eta2': eta_raw, 'rho': rho_raw}}

    # A) 地理集群 (WB 区域)
    group_of = {}
    for a in agg:
        if a in wb:
            group_of[a] = wb[a].strip()
    res['A_地理集群'] = run_group('A) 地理集群(WB区域)', by_c_raw, group_of)

    # B) 语言家族
    group_of = {a: LANG_FAM[a] for a in agg if a in LANG_FAM}
    fam_cn = {fam: LANG_FAM_CN.get(fam, fam) for fam in set(group_of.values())}
    print('\n  语族国家数: ' + ', '.join(f'{fam_cn[f]}({sum(1 for x in group_of.values() if x == f)})'
          for f in sorted(set(group_of.values()), key=lambda f: -sum(1 for x in group_of.values() if x == f))))
    res['B_语言家族'] = run_group('B) 语言家族', by_c_raw, group_of)

    # C) 制度组合模式 (WGI k-means, k=4)
    cov_ok = {a: wgi[a] for a in agg if a in wgi}
    zs = standardize_profile(cov_ok, WGI_DIMS)
    for k in (4, 3):
        cl = kmeans([(a, zs[a]) for a in cov_ok], k, seed=7)
        group_of = dict(cl)
        res[f'C_WGI_kmeans{k}'] = run_group(f'C) 制度组合模式(WGI k-means k={k})', by_c_raw, group_of)

    # D) 文化组合模式 (Hofstede k-means, k=4)
    cov_ok = {a: hof[a] for a in agg if a in hof}
    zs = standardize_profile(cov_ok, HOF_DIMS)
    for k in (4, 3):
        cl = kmeans([(a, zs[a]) for a in cov_ok], k, seed=7)
        group_of = dict(cl)
        res[f'D_Hofstede_kmeans{k}'] = run_group(f'D) 文化组合模式(Hofstede k-means k={k})', by_c_raw, group_of)

    json.dump(res, open('probe9_results.json', 'w'), ensure_ascii=False, indent=2)
    print('\n已保存 probe9_results.json')


if __name__ == '__main__':
    main()
