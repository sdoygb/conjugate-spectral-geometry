#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IMF SDMX 3.0 IMTS 正式拉取+解析：台海监测对双向贸易流
正确映射 TIME_PERIOD 时间轴，输出 CSV"""
import json, csv, sys, urllib.request, urllib.error

BASE = 'https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/IMTS/1.0.0'
ACCEPT = 'application/vnd.sdmx.data+json;version=2.0.0'

SERIES = [
    ('CN_X_TW', 'CHN.XG_FOB_USD.TWN.A',  '中国→台湾 出口 FOB'),
    ('CN_M_TW', 'CHN.MG_CIF_USD.TWN.A',  '中国←台湾 进口 CIF'),
    ('CN_X_US', 'CHN.XG_FOB_USD.USA.A',  '中国→美国 出口 FOB'),
    ('CN_M_US', 'CHN.MG_CIF_USD.USA.A',  '中国←美国 进口 CIF'),
    ('US_X_TW', 'USA.XG_FOB_USD.TWN.A',  '美国→台湾 出口 FOB'),
    ('US_M_TW', 'USA.MG_CIF_USD.TWN.A',  '美国←台湾 进口 CIF'),
]

def fetch(url):
    req = urllib.request.Request(url, headers={'Accept': ACCEPT, 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 'ERR', str(e).encode()

def parse(body):
    d = json.loads(body)
    data = d['data']
    struct = data['structures'][0]
    # 时间轴
    time_vals = []
    for od in struct['dimensions']['observation']:
        if od['id'] == 'TIME_PERIOD':
            time_vals = [v.get('value', v.get('id', '?')) for v in od['values']]
    # 系列
    series_out = []
    for ds in data['dataSets']:
        for skey, s in (ds.get('series', {}) or {}).items():
            obs = {}
            for pkey, v in (s.get('observations', {}) or {}).items():
                idx = int(pkey)
                if idx < len(time_vals):
                    obs[time_vals[idx]] = v[0]
            series_out.append((skey, obs))
    return time_vals, series_out

if __name__ == '__main__':
    results = {}
    all_ok = True
    for tag, key, desc in SERIES:
        url = f'{BASE}/{key}?startPeriod=1990&endPeriod=2026'
        st, body = fetch(url)
        print(f'=== {tag} | {desc} | HTTP {st} | {len(body)} bytes')
        if st == 200:
            try:
                time_vals, series = parse(body)
                for skey, obs in series:
                    years = sorted(obs)
                    n = len(obs)
                    recent = {y: obs[y] for y in years[-6:]}
                    print(f'  series {skey}: {n} obs | {years[0]}–{years[-1]} | 最近6年: {recent}')
                    results[tag] = {'first': years[0], 'last': years[-1], 'obs': obs}
                if not series:
                    print('  !! 无数据')
                    all_ok = False
            except Exception as e:
                print(f'  !! 解析失败: {e}')
                print(f'  raw[:300]: {body[:300]}')
                all_ok = False
        else:
            print(f'  !! 失败: {body[:300]}')
            all_ok = False
        print()

    # 输出 CSV：合并所有系列为列
    if results:
        all_years = sorted(set().union(*[r['obs'].keys() for r in results.values()]))
        outpath = 'imts_taistrait.csv'
        with open(outpath, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['year'] + list(results.keys()))
            for y in all_years:
                row = [y]
                for tag in results:
                    row.append(results[tag]['obs'].get(y, ''))
                w.writerow(row)
        print(f'已保存 {outpath}: {len(all_years)} 年 × {len(results)} 系列')
        # 打印 2022-2025 关键行
        print()
        print('=== 2022–2025 关键行 ===')
        with open(outpath) as f:
            for line in f:
                if line.startswith(('2022', '2023', '2024', '2025', 'year')):
                    print(line.strip())
    print('ALL_OK' if all_ok else 'SOME_FAILED')
    sys.exit(0 if all_ok else 1)
