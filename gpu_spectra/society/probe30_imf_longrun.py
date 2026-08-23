"""探针30 v3：IMF DOTS 长周期贸易耦合轨迹（1948–2023）
用 TMG_CIF（进口）构建双边矩阵：w_ij = M[i←j] + M[j←i]
USA 出口(TXG)数据缺失，但进口(TMG)完整且恒等式 TBG=TXG-TMG 验证通过。
"""
import csv, json, os
import numpy as np
from collections import defaultdict

DATA = os.path.expanduser('~/Downloads/IMF_DOT.csv')

# 节点：IMF 伙伴码 → 名称（国家白名单，排除区域聚合码）
NODES = {
    'CN': '924', 'TW': '528', 'US': '111', 'JP': '158', 'IN': '534', 'EU': '998',
    'KR': '542', 'RU': '922', 'HK': '532', 'GB': '112', 'CA': '156', 'AU': '193',
    'BR': '223', 'MX': '273', 'ID': '536', 'SG': '576', 'TH': '578', 'MY': '548',
    'VN': '582', 'PH': '566', 'PK': '564', 'SA': '456', 'CH': '146',
}
EU27 = ['AUT','BEL','BGR','HRV','CYP','CZE','DNK','EST','FIN','FRA','DEU','GRC',
        'HUN','IRL','ITA','LVA','LTU','LUX','MLT','NLD','POL','PRT','ROU','SVK',
        'SVN','ESP','SWE']

# 读取 TMG_CIF（进口）
M = defaultdict(float)
with open(DATA, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['INDICATOR'] != 'IMF_DOT_TMG_CIF_USD':
            continue
        ref = row['REF_AREA']
        p = row['COMP_BREAKDOWN_1']
        if not p.startswith('IMF_CNT_COUNTRY_'):
            continue
        code = p.split('_')[-1]
        year = row['TIME_PERIOD']
        if not (year.isdigit() and 1948 <= int(year) <= 2023):
            continue
        try:
            val = float(row['OBS_VALUE'])
        except (ValueError, TypeError):
            continue
        M[(ref, code, int(year))] += val
print(f'TMG 读取完成: {len(M)} 条')

# 国家 → 报告国 ISO3（用于查询 M[ref←code]）
name2iso = {'CN':'CHN','TW':'TWN','US':'USA','JP':'JPN','IN':'IND','KR':'KOR','RU':'RUS',
            'HK':'HKG','GB':'GBR','CA':'CAN','AU':'AUS','BR':'BRA','MX':'MEX','ID':'IDN',
            'SG':'SGP','TH':'THA','MY':'MYS','VN':'VNM','PH':'PHL','PK':'PAK','SA':'SAU','CH':'CHE'}

def import_flow(importer_iso, partner_code, y):
    """importer_iso 从 partner_code 的进口（美元）；partner=EU 时聚合 998"""
    if partner_code == '998':
        return M.get((importer_iso, '998', y), 0.0)
    return M.get((importer_iso, partner_code, y), 0.0)

def eu_import_from(partner_code, y):
    """EU27 成员国从 partner_code 的进口聚合（≈EU←partner）"""
    return sum(M.get((m, partner_code, y), 0.0) for m in EU27)

def edge_w(name_i, name_j, y):
    """节点 name_i, name_j（节点名）的双边贸易流 w = i←j + j←i（进口视角）"""
    ci, cj = NODES[name_i], NODES[name_j]
    w = 0.0
    ri, rj = name2iso.get(name_i), name2iso.get(name_j)
    # i←j：i 从 j 进口
    if ri is not None:
        w += import_flow(ri, cj, y)
    elif name_i == 'EU':
        w += eu_import_from(cj, y)
    # j←i：j 从 i 进口
    if rj is not None:
        w += import_flow(rj, ci, y)
    elif name_j == 'EU':
        w += eu_import_from(ci, y)
    return w

def build_matrix(sel_names, years):
    n = len(sel_names)
    mats = {}
    for y in years:
        W = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                w = edge_w(sel_names[i], sel_names[j], y)
                W[i, j] = W[j, i] = w
        mats[y] = W
    return mats

def spectrum(W):
    """探针㉓ 口径：非归一化拉普拉斯 λ₂ + 邻接矩阵对称配对残差 BR"""
    n = len(W)
    if n < 2 or W.sum() == 0:
        return 0.0, 0.0
    L = np.diag(W.sum(axis=1)) - W
    ev_l = np.sort(np.linalg.eigvalsh(L))
    l2 = float(ev_l[1]) if n > 1 else 0.0
    ev_a = np.sort(np.linalg.eigvalsh(W))
    br = float(sum(abs(ev_a[i] + ev_a[n-1-i]) for i in range(n//2)) / (n//2))
    return l2, br

years = list(range(1948, 2024))
core6 = ['CN','TW','US','JP','IN','EU']
nodes24 = list(NODES.keys())

mats6 = build_matrix(core6, years)
mats24 = build_matrix(nodes24, years)

res = {'years': years, 'lam2_6': [], 'br_6': [], 'lam2_24': [], 'br_24': []}
for y in years:
    l6, b6 = spectrum(mats6[y])
    l24, b24 = spectrum(mats24[y])
    res['lam2_6'].append(round(l6, 6)); res['br_6'].append(round(b6, 6))
    res['lam2_24'].append(round(l24, 6)); res['br_24'].append(round(b24, 6))

edges = {}
for name, (a, b) in {'CN-US': ('CN','US'), 'CN-TW': ('CN','TW'), 'US-TW': ('US','TW'),
                     'CN-JP': ('CN','JP'), 'CN-IN': ('CN','IN'), 'US-EU': ('US','EU'),
                     'CN-EU': ('CN','EU'), 'US-JP': ('US','JP'), 'JP-KR': ('JP','KR'),
                     'TW-JP': ('TW','JP'), 'TW-US': ('TW','US'), 'TW-HK': ('TW','HK')}.items():
    edges[name] = {str(y): round(edge_w(a, b, y)/1e8, 3)
                   for y in years if y in (1950,1960,1970,1980,1990,2000,2005,2010,2015,2018,2019,2020,2021,2022,2023)}

out = {'nodes': NODES, 'years': years, 'edges': edges,
       'lam2_6': res['lam2_6'], 'br_6': res['br_6'],
       'lam2_24': res['lam2_24'], 'br_24': res['br_24']}
with open('gpu_spectra/society/probe30_imf_longrun.json', 'w') as f:
    json.dump(out, f, indent=1)

print('=== 6 节点 λ₂/BR 长周期（进口视角）===')
for i, y in enumerate(years):
    if y in (1948,1955,1960,1970,1980,1990,2000,2010,2015,2018,2019,2020,2021,2022,2023):
        print(f'{y}: λ₂={res["lam2_6"][i]:.4f}  BR={res["br_6"][i]:.4f}')
print('\n=== 关键边（亿美元，进口视角双向）===')
for name, s in edges.items():
    print(f'{name}: {s}')
print('\n已保存 probe30_imf_longrun.json')
