#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 49 个 IMTS XML → 双边贸易矩阵 → 重建 6/24 节点 λ₂/BR（2022-2025）
并拼接 probe30_imf_longrun.json 历史轨迹 → 输出 imts_bulk_parsed.json + probe30_imts_2025.json
口径：w_ij = M[i←j] + M[j←i]（进口视角，MG_CIF_USD），与 probe30 完全一致
验证：TBG = XG - MG；2023 重叠年与 probe30 json 对照
"""
import json, os, sys, glob, xml.etree.ElementTree as ET
import numpy as np

OUTDIR = 'imts_bulk_raw'
PARSED = 'imts_bulk_parsed.json'
OUT = 'probe30_imts_2025.json'
OLD = 'probe30_imf_longrun.json'

NAME2ISO = {'CN':'CHN','TW':'TWN','US':'USA','JP':'JPN','IN':'IND','KR':'KOR','RU':'RUS',
            'HK':'HKG','GB':'GBR','CA':'CAN','AU':'AUS','BR':'BRA','MX':'MEX','ID':'IDN',
            'SG':'SGP','TH':'THA','MY':'MYS','VN':'VNM','PH':'PHL','PK':'PAK','SA':'SAU','CH':'CHE'}
ISO2NAME = {v: k for k, v in NAME2ISO.items()}
EU27 = ['AUT','BEL','BGR','HRV','CYP','CZE','DNK','EST','FIN','FRA','DEU','GRC',
        'HUN','IRL','ITA','LVA','LTU','LUX','MLT','NLD','POL','PRT','ROU','SVK',
        'SVN','ESP','SWE']
# 核心6 与 全24 节点顺序（与 probe30 相同）
core6 = ['CN','TW','US','JP','IN','EU']
nodes24 = list(NAME2ISO.keys()) + ['EU']

def parse_xml(path):
    """返回 {partner: {ind: {year: value}}}  (reporter 已知 = 文件名)"""
    tree = ET.parse(path)
    root = tree.getroot()
    out = {}
    for el in root.iter():
        tag = el.tag.split('}')[-1]
        if tag != 'Series':
            continue
        a = el.attrib
        ind = a.get('INDICATOR')
        partner = a.get('COUNTERPART_COUNTRY')
        if ind not in ('MG_CIF_USD', 'XG_FOB_USD', 'TBG_USD'):
            continue
        d = out.setdefault(partner, {})
        dd = d.setdefault(ind, {})
        for obs in el:
            if obs.tag.split('}')[-1] == 'Obs':
                y = obs.attrib.get('TIME_PERIOD')
                v = obs.attrib.get('OBS_VALUE')
                if y and v is not None:
                    try:
                        dd[y] = float(v)
                    except ValueError:
                        pass
    return out

def main():
    data = {}  # reporter -> parsed
    for fn in sorted(glob.glob(f'{OUTDIR}/*.xml')):
        iso = os.path.basename(fn)[:-4]
        data[iso] = parse_xml(fn)
        n_part = len(data[iso])
        n_obs = sum(len(obs) for pd in data[iso].values() for obs in pd.values())
        print(f'{iso}: {n_part} 伙伴, {n_obs} 观测', flush=True)
    json.dump(data, open(PARSED, 'w'))
    print(f'已保存 {PARSED}', flush=True)

    # ---- 验证 1: TBG = XG - MG ----
    print('\n=== 验证 TBG = XG - MG（取 CHN 对 USA 2023-2025）===')
    chn = data['CHN']
    for y in ('2023', '2024', '2025'):
        x = chn['USA']['XG_FOB_USD'].get(y)
        m = chn['USA']['MG_CIF_USD'].get(y)
        t = chn['USA']['TBG_USD'].get(y)
        diff = (x - m) - t if x is not None and m is not None and t is not None else None
        print(f'  {y}: X={x/1e9:.2f}B M={m/1e9:.2f}B T={t/1e9:.2f}B 残差={diff/1e9 if diff is not None else "NA"}B')

    # ---- 矩阵构建 ----
    def import_flow(importer_iso, partner_iso, y, ind='MG_CIF_USD'):
        """importer_iso 从 partner_iso 的进口（CIF）"""
        pd_ = data.get(importer_iso, {})
        return pd_.get(partner_iso, {}).get(ind, {}).get(y, 0.0)

    def eu_import_from(partner_iso, y):
        return sum(import_flow(m, partner_iso, y) for m in EU27)

    def edge_w(name_i, name_j, y):
        """节点名双边的 w = i←j + j←i"""
        if name_i == 'EU' and name_j == 'EU':
            return 0.0
        w = 0.0
        if name_i == 'EU':
            w += eu_import_from(NAME2ISO[name_j], y)
            # EU→j 无直接数据，j 的进口已含 EU 成员国；用 j 从 EU27 聚合近似
            w += sum(import_flow(NAME2ISO[name_j], m, y) for m in EU27)
        elif name_j == 'EU':
            w += sum(import_flow(NAME2ISO[name_i], m, y) for m in EU27)
            w += eu_import_from(NAME2ISO[name_i], y)
        else:
            w += import_flow(NAME2ISO[name_i], NAME2ISO[name_j], y)
            w += import_flow(NAME2ISO[name_j], NAME2ISO[name_i], y)
        return w

    def build_matrix(names, y):
        n = len(names)
        W = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                w = edge_w(names[i], names[j], y)
                W[i, j] = W[j, i] = w
        return W

    def spectrum(W):
        n = len(W)
        if n < 2 or W.sum() == 0:
            return 0.0, 0.0
        L = np.diag(W.sum(axis=1)) - W
        ev_l = np.sort(np.linalg.eigvalsh(L))
        l2 = float(ev_l[1]) if n > 1 else 0.0
        ev_a = np.sort(np.linalg.eigvalsh(W))
        br = float(sum(abs(ev_a[i] + ev_a[n - 1 - i]) for i in range(n // 2)) / (n // 2))
        return l2, br

    years = ['2022', '2023', '2024', '2025']
    res = {'years': years, 'lam2_6': [], 'br_6': [], 'lam2_24': [], 'br_24': []}
    print('\n=== 6 节点 / 24 节点 λ₂/BR（新 IMTS 数据）===')
    for y in years:
        l6, b6 = spectrum(build_matrix(core6, y))
        l24, b24 = spectrum(build_matrix(nodes24, y))
        res['lam2_6'].append(round(l6, 6)); res['br_6'].append(round(b6, 6))
        res['lam2_24'].append(round(l24, 6)); res['br_24'].append(round(b24, 6))
        print(f'{y}: λ₂6={l6:.4f} BR6={b6:.4f} | λ₂24={l24:.4f} BR24={b24:.4f}')

    # ---- 拼接历史 ----
    old = json.load(open(OLD))
    print(f'\n历史轨迹: {old["years"][0]}-{old["years"][-1]} ({len(old["years"])} 年)')
    # 重叠验证：2022/2023 新 vs 旧
    print('=== 重叠验证（新 IMTS vs 旧 IMF_DOT）===')
    for i, y in enumerate(old['years']):
        if str(y) in years:
            o6, o24 = old['br_6'][i], old['br_24'][i]
            n6 = res['br_6'][years.index(str(y))]
            n24 = res['br_24'][years.index(str(y))]
            print(f'{y}: BR6 旧={o6:.6f} 新={n6:.6f} 差={n6-o6:+.6f} | BR24 旧={o24:.6f} 新={n24:.6f} 差={n24-o24:+.6f}')

    # 拼接：旧 1948-2023 + 新 2024-2025（2022/2023 用旧值保持一致）
    yrs = old['years'] + [2024, 2025]
    lam2_6 = old['lam2_6'] + res['lam2_6'][-2:]
    br_6 = old['br_6'] + res['br_6'][-2:]
    lam2_24 = old['lam2_24'] + res['lam2_24'][-2:]
    br_24 = old['br_24'] + res['br_24'][-2:]

    out = {'nodes': old['nodes'], 'years': yrs,
           'edges': old['edges'],
           'lam2_6': lam2_6, 'br_6': br_6, 'lam2_24': lam2_24, 'br_24': br_24,
           'imts_new': res, 'source_note': '1948-2023: IMF DOT (WB mirror); 2024-2025: IMF IMTS API v2.1'}
    json.dump(out, open(OUT, 'w'), indent=1)
    print(f'\n已保存 {OUT}: {yrs[0]}-{yrs[-1]} 共 {len(yrs)} 年')

if __name__ == '__main__':
    main()
