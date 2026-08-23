#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe8_wgi_hofstede.py — WVS Wave 7 + WGI 制度质量 / Hofstede 文化维度
问题(续探针⑦): 国家排序的锁定不可还原为 GDP/教育。这个锁是"制度质量(WGI)"还是"文化维度(Hofstede)"?
设计:
  A) WGI (QoG wbgi_* 六指标, 2017-2022 均值):
     A1: 国家均值满意度 vs 各维度 单变量 r/R² (6个)
     A2: 六维度复合(标准分均值) 单回归; 多变量 OLS 全模型 R²_adj
     A3: 个体级残差化(减去国家级 WGI 预测平移)后 η²(国家) 与 bootstrap 排序稳定性 ρ
  B) Hofstede (六维度):
     B1/B2/B3: 同上
  C) 组合: WGI+Hofstede+GDP 全模型解释的国家间方差比例
判定: 残差化后 ρ 仍 ≈ 0.995 -> 锁定不可还原为制度/文化标量属性(纤维结构本身锁定);
       ρ 塌缩 -> 锁定由该组变量解释
数据: WVS_Cross-National_Wave_7_csv_v6_0.csv, qog_std_ts_jan25.csv, hofstede.csv, wb_gdp.json
"""
import csv, json, math, random
from collections import defaultdict
from statistics import mean, pstdev

CSV = 'WVS_Cross-National_Wave_7_csv_v6_0.csv'
QOG = 'qog_std_ts_jan25.csv'
HOF = 'hofstede.csv'
GDP_JSON = 'wb_gdp.json'

WGI_DIMS = ['wbgi_vae', 'wbgi_pve', 'wbgi_gee', 'wbgi_rqe', 'wbgi_rle', 'wbgi_cce']
WGI_LABEL = {'wbgi_vae': '话语权/问责', 'wbgi_pve': '政治稳定', 'wbgi_gee': '政府效能',
             'wbgi_rqe': '监管质量', 'wbgi_rle': '法治', 'wbgi_cce': '腐败控制'}
HOF_DIMS = ['pdi', 'idv', 'mas', 'uai', 'ltowvs', 'ivr']
HOF_LABEL = {'pdi': '权力距离', 'idv': '个人主义', 'mas': '男性气质',
             'uai': '不确定性规避', 'ltowvs': '长期取向', 'ivr': '放纵'}

# Hofstede 非 ISO3 代码 -> ISO3 (WVS 用 ISO3)
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


def load_wvs():
    data = []
    with open(CSV, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            a = row['B_COUNTRY_ALPHA']
            try:
                q49 = int(row['Q49']); q57 = int(row['Q57'])
            except ValueError:
                continue
            if not (1 <= q49 <= 10 and q57 in (1, 2)):
                continue
            data.append((a, q49, q57))
    return data


def load_qog_wgi():
    """QoG wbgi_* 六指标 -> {iso3: {dim: mean(2017-2022)}}"""
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


def load_gdp():
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
    return {iso: mean(v) for iso, v in by.items() if len(v) >= 2}


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
    mx, my = mean(xs), mean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    if vx == 0:
        return my, 0.0
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / vx
    return my - b * mx, b


def ols_multiple(X, y):
    """y ~ b0 + Σ bj Xj, 正规方程, 返回 (b0, [bj], R²)"""
    n, p = len(y), len(X)
    # 增广设计矩阵
    A = [[1.0] + [X[j][i] for j in range(p)] for i in range(n)]
    AtA = [[sum(A[i][a] * A[i][b] for i in range(n)) for b in range(p + 1)] for a in range(p + 1)]
    Aty = [sum(A[i][a] * y[i] for i in range(n)) for a in range(p + 1)]
    # 高斯消元
    M = [AtA[i] + [Aty[i]] for i in range(p + 1)]
    for col in range(p + 1):
        piv = max(range(col, p + 1), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        if abs(M[col][col]) < 1e-12:
            return None
        for r in range(p + 1):
            if r != col:
                f = M[r][col] / M[col][col]
                M[r] = [M[r][c] - f * M[col][c] for c in range(p + 2)]
    beta = [M[i][p + 1] / M[i][i] for i in range(p + 1)]
    yhat = [sum(beta[k] * A[i][k] for k in range(p + 1)) for i in range(n)]
    my = mean(y)
    ss_res = sum((y[i] - yhat[i]) ** 2 for i in range(n))
    ss_tot = sum((y[i] - my) ** 2 for i in range(n))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    n_eff = n - p - 1
    r2_adj = 1 - (1 - r2) * (n - 1) / n_eff if n_eff > 0 else r2
    return beta[0], beta[1:], r2, r2_adj


def eta_squared(values_by_group):
    allv = [v for vs in values_by_group.values() for v in vs]
    grand = mean(allv)
    ss_tot = sum((v - grand) ** 2 for v in allv)
    ss_b = sum(len(vs) * (mean(vs) - grand) ** 2 for vs in values_by_group.values())
    return ss_b / ss_tot if ss_tot else 0.0


def boot_rank_stability(by_country_values, nboot=200, seed=42):
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
    print('加载 WVS / WGI / Hofstede / GDP ...')
    data = load_wvs()
    wgi = load_qog_wgi()
    hof = load_hofstede()
    gdp = load_gdp()
    print(f'样本 {len(data)}, WVS国家 {len({d[0] for d in data})}, WGI覆盖 {len(wgi)}, Hofstede覆盖 {len(hof)}')

    agg = defaultdict(list)
    for a, q49, q57 in data:
        agg[a].append(q49)
    by_c_raw = dict(agg)
    rho_raw, rho_raw_min = boot_rank_stability(by_c_raw)
    eta_raw = eta_squared(by_c_raw)
    print(f'[基准] 原始 η²(国家)={eta_raw:.4f}, 排序稳定性 ρ={rho_raw:.4f} (min={rho_raw_min:.3f})')

    res = {'raw': {'eta2': eta_raw, 'rho': rho_raw}}

    def run_block(name, cov, label):
        """cov: {iso3: {dim: value}}, label: {dim: 中文}"""
        print(f'\n============ {name} ============')
        cov_ok = {a: cov[a] for a in agg if a in cov}
        print(f'国家匹配: {len(cov_ok)} / {len(agg)}')
        if not cov_ok:
            return
        dims = list(label.keys())
        # 单变量
        for dim in dims:
            xs = [cov_ok[a][dim] for a in cov_ok]
            ys = [mean(agg[a]) for a in cov_ok]
            r = pearson_r(xs, ys)
            print(f'  {label[dim]:<6} vs 满意度: r={r:+.3f}, R²={r*r:.4f}')
        # 复合(标准分均值)
        zs = {}
        for a in cov_ok:
            z = []
            for dim in dims:
                vals = [cov_ok[b][dim] for b in cov_ok]
                mu, sd = mean(vals), pstdev(vals)
                z.append((cov_ok[a][dim] - mu) / sd if sd else 0.0)
            zs[a] = mean(z)
        xs = [zs[a] for a in cov_ok]
        ys = [mean(agg[a]) for a in cov_ok]
        r = pearson_r(xs, ys)
        print(f'  复合(六维标准分均值): r={r:+.3f}, R²={r*r:.4f}')
        # 多变量 (列式)
        rows = [[cov_ok[a][dim] for dim in dims] for a in cov_ok]
        X = [[rows[i][j] for i in range(len(rows))] for j in range(len(dims))]
        ml = ols_multiple(X, ys)
        if ml:
            b0, bs, r2, r2a = ml
            print(f'  多变量全模型: R²={r2:.4f}, R²_adj={r2a:.4f}')
            print(f'    系数: ' + ', '.join(f'{label[dims[i]]}={bs[i]:+.4f}' for i in range(len(dims))))
        else:
            r2a = None
            print('  多变量回归奇异(共线性过强), 用复合替代')
            r2a = r * r
        # 残差化: 用复合 OLS 国家均值预测平移
        a0, b = ols_coef(xs, ys)
        by_c_resid = {}
        for a in cov_ok:
            shift = a0 + b * zs[a]
            by_c_resid[a] = [q - shift for q in agg[a]]
        eta_res = eta_squared(by_c_resid)
        rho_res, rho_res_min = boot_rank_stability(by_c_resid)
        print(f'  复合残差化后: η²(国家)={eta_res:.4f} (Δ={eta_res - eta_raw:+.4f}), ρ={rho_res:.4f} (min={rho_res_min:.3f})')
        res[name] = {'n': len(cov_ok), 'r2_composite': r * r, 'r2_adj': r2a,
                     'eta2_resid': eta_res, 'rho_resid': rho_res, 'rho_resid_min': rho_res_min}
        return cov_ok

    cov_wgi = run_block('A) WGI 制度质量', wgi, WGI_LABEL)
    cov_hof = run_block('B) Hofstede 文化维度', hof, HOF_LABEL)

    # ============ C) 组合 WGI+Hofstede+GDP ============
    print('\n============ C) WGI + Hofstede + GDP 全模型 ============')
    both = {a: wgi[a] for a in agg if a in wgi and a in hof and a in gdp}
    if both:
        countries = list(both.keys())
        y = [mean(agg[a]) for a in countries]
        dims_use = WGI_DIMS + HOF_DIMS + ['logGDP']
        rows = []
        for a in countries:
            row = [wgi[a][d] for d in WGI_DIMS] + [hof[a][d] for d in HOF_DIMS] + [math.log(gdp[a])]
            rows.append(row)
        Xt = [[rows[i][j] for i in range(len(rows))] for j in range(len(dims_use))]
        # 同子集基准(对照): 仅这 N 国时的原始 η²/ρ
        sub_raw = {a: agg[a] for a in countries}
        eta_sub = eta_squared(sub_raw)
        rho_sub, rho_sub_min = boot_rank_stability(sub_raw)
        print(f'  [子集基准] 仅这 {len(countries)} 国: 原始 η²={eta_sub:.4f}, ρ={rho_sub:.4f}')
        ml = ols_multiple(Xt, y)
        if ml:
            b0, bs, r2, r2a = ml
            print(f'  WGI(6)+Hofstede(6)+GDP 全模型 (N={len(countries)}): R²={r2:.4f}, R²_adj={r2a:.4f}')
            print(f'  解释国家间方差 {r2*100:.1f}% (未解释 {100*(1-r2):.1f}%)')
            res['C_full'] = {'n': len(countries), 'r2': r2, 'r2_adj': r2a}
        else:
            print('  全模型奇异')
        # 复合残差化(全模型预测平移)
        if ml:
            b0, bs, r2, r2a = ml
            by_c_resid = {}
            for i, a in enumerate(countries):
                shift = b0 + sum(bs[j] * Xt[j][i] for j in range(len(dims_use)))
                by_c_resid[a] = [q - shift for q in agg[a]]
            eta_res = eta_squared(by_c_resid)
            rho_res, rho_res_min = boot_rank_stability(by_c_resid)
            print(f'  全模型残差化后: η²={eta_res:.4f}, ρ={rho_res:.4f} (min={rho_res_min:.3f})')
            res['C_full']['eta2_resid'] = eta_res
            res['C_full']['rho_resid'] = rho_res

    json.dump(res, open('probe8_results.json', 'w'), ensure_ascii=False, indent=2)
    print('\n已保存 probe8_results.json')


if __name__ == '__main__':
    main()
