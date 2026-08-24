#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针㉕ 更新补充：归一化口径（÷max edge）BR/λ₂ + 关键边 + TW 份额（2022-2025）
输出: probe30_imts_2025_full.json（含归一化口径与边）+ imts_24node_trajectory_2025.csv
"""
import json
import numpy as np

PARSED = 'imts_bulk_parsed.json'
OLD = 'probe30_imf_longrun.json'
OUT = 'probe30_imts_2025_full.json'
CSV = 'imts_24node_trajectory_2025.csv'

data = json.load(open(PARSED))

NAME2ISO = {'CN':'CHN','TW':'TWN','US':'USA','JP':'JPN','IN':'IND','KR':'KOR','RU':'RUS',
            'HK':'HKG','GB':'GBR','CA':'CAN','AU':'AUS','BR':'BRA','MX':'MEX','ID':'IDN',
            'SG':'SGP','TH':'THA','MY':'MYS','VN':'VNM','PH':'PHL','PK':'PAK','SA':'SAU','CH':'CHE'}
EU27 = ['AUT','BEL','BGR','HRV','CYP','CZE','DNK','EST','FIN','FRA','DEU','GRC',
        'HUN','IRL','ITA','LVA','LTU','LUX','MLT','NLD','POL','PRT','ROU','SVK',
        'SVN','ESP','SWE']
core6 = ['CN','TW','US','JP','IN','EU']
nodes24 = list(NAME2ISO.keys()) + ['EU']
years = ['2022','2023','2024','2025']

def import_flow(imp, part, y):
    return data.get(imp, {}).get(part, {}).get('MG_CIF_USD', {}).get(y, 0.0)

def eu_import_from(part, y):
    return sum(import_flow(m, part, y) for m in EU27)

def edge_w(ni, nj, y):
    if ni == 'EU' and nj == 'EU':
        return 0.0
    w = 0.0
    if ni == 'EU':
        w += eu_import_from(NAME2ISO[nj], y)
        w += sum(import_flow(NAME2ISO[nj], m, y) for m in EU27)
    elif nj == 'EU':
        w += sum(import_flow(NAME2ISO[ni], m, y) for m in EU27)
        w += eu_import_from(NAME2ISO[ni], y)
    else:
        w += import_flow(NAME2ISO[ni], NAME2ISO[nj], y)
        w += import_flow(NAME2ISO[nj], NAME2ISO[ni], y)
    return w

def build_matrix(names, y):
    n = len(names)
    W = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            w = edge_w(names[i], names[j], y)
            W[i, j] = W[j, i] = w
    return W

def spectrum(W, norm=True):
    n = len(W)
    if n < 2 or W.sum() == 0:
        return 0.0, 0.0, 0.0
    Wn = W / W.max() if norm else W
    L = np.diag(Wn.sum(axis=1)) - Wn
    ev_l = np.sort(np.linalg.eigvalsh(L))
    l2 = float(ev_l[1]) if n > 1 else 0.0
    ev_a = np.sort(np.linalg.eigvalsh(Wn))
    br = float(sum(abs(ev_a[i] + ev_a[n - 1 - i]) for i in range(n // 2)) / (n // 2))
    return l2, br, float(W.max())

res = {}
print('=== 归一化口径（÷当年最大边，探针㉓/㉔可比）===')
for y in years:
    l6, b6, mx6 = spectrum(build_matrix(core6, y), norm=True)
    l24, b24, mx24 = spectrum(build_matrix(nodes24, y), norm=True)
    res[y] = dict(lam2_6_norm=l6, br_6_norm=b6, max_edge_6=mx6,
                  lam2_24_norm=l24, br_24_norm=b24, max_edge_24=mx24)
    print(f'{y}: BR6={b6:.4f} λ₂6={l6:.4f} (max={mx6/1e9:.1f}B) | BR24={b24:.4f} λ₂24={l24:.4f} (max={mx24/1e9:.1f}B)')

print('\n=== 关键边（亿美元，双向进口视角）===')
edges = {}
for a, b in [('CN','US'),('CN','TW'),('US','TW'),('CN','JP'),('CN','IN'),('CN','EU'),
             ('US','EU'),('US','JP'),('TW','JP'),('TW','HK'),('CN','KR'),('JP','KR'),('US','KR')]:
    row = {}
    for y in years:
        row[int(y)] = round(edge_w(a, b, y) / 1e8, 1)
    edges[f'{a}-{b}'] = row
    print(f'{a}-{b}: {row}')

print('\n=== TW 耦合份额 CN/(CN+US)（亿美元）===')
for y in years:
    cn_tw = edge_w('CN', 'TW', y) / 1e8
    us_tw = edge_w('US', 'TW', y) / 1e8
    share = cn_tw / (cn_tw + us_tw) * 100 if (cn_tw + us_tw) > 0 else float('nan')
    print(f'{y}: CN-TW={cn_tw:.1f}  US-TW={us_tw:.1f}  CN份额={share:.1f}%')

# 拼接历史 + 输出
old = json.load(open(OLD))
yrs = old['years'] + [2024, 2025]
out = {'nodes': old['nodes'], 'years': yrs,
       'edges': old['edges'],
       'lam2_6': old['lam2_6'] + [res['2024']['lam2_6_norm'] * 0, res['2025']['lam2_6_norm'] * 0],  # 占位
       'br_6': old['br_6'], 'br_24': old['br_24'],
       'imts_2022_2025': res, 'key_edges_2022_2025': edges,
       'tw_share': {y: None for y in years},
       'source_note': '1948-2023: IMF DOT (WB mirror); 2024-2025: IMF IMTS API v2.1'}
# 填充 TW 份额
for y in years:
    cn_tw = edge_w('CN', 'TW', y) / 1e8
    us_tw = edge_w('US', 'TW', y) / 1e8
    out['tw_share'][y] = round(cn_tw / (cn_tw + us_tw) * 100, 2) if (cn_tw + us_tw) > 0 else None
json.dump(out, open(OUT, 'w'), indent=1)
print(f'\n已保存 {OUT}')

# 24 节点轨迹 csv（2022-2025 用新数据 + 历史 json 前段）
rows = []
for i, y in enumerate(old['years']):
    rows.append(dict(year=y, lam2_24=old['lam2_24'][i], br_24=old['br_24'][i]))
for y in years:
    rows.append(dict(year=int(y), lam2_24=res[y]['lam2_24_norm'] * 0 + 0, br_24=0.0))  # 占位，不输出
# 只用非归一化口径输出（与历史一致）
rows = []
for i, y in enumerate(old['years']):
    rows.append((y, old['lam2_24'][i], old['br_24'][i]))
# 新年份的非归一化值从之前 json 读
newj = json.load(open('probe30_imts_2025.json'))
for y in years:
    idx = newj['years'].index(int(y))
    rows.append((int(y), newj['lam2_24'][idx], newj['br_24'][idx]))
with open(CSV, 'w') as f:
    f.write('year,lam2_24,br_24\n')
    for y, l, b in rows:
        f.write(f'{y},{l:.6e},{b:.6e}\n')
print(f'已保存 {CSV}: {rows[0][0]}-{rows[-1][0]} 共 {len(rows)} 年')
