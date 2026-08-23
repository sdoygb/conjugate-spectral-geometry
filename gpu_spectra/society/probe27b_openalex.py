#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针㉗b：信息流——OpenAlex 全球论文合著网络的谱轨迹（1995-2024 抽样年）
方法：对每个核心国 A 查询 filter=publication_year:Y,authorships.countries:A
      &group_by=authorships.countries → 得到 A 论文的合著国分布
      → 对称化 → 矩阵 → λ₂/BR（GCC）
"""
import urllib.request, json, time, numpy as np, sys

CORE = ['CN', 'TW', 'US', 'JP', 'IN', 'DE', 'FR', 'IT', 'GB', 'CA', 'RU', 'KR', 'AU']
YEARS = [1995, 2000, 2005, 2010, 2015, 2020, 2024]

def query(country, year):
    url = (f'https://api.openalex.org/works?filter=publication_year:{year},'
           f'authorships.countries:{country}&group_by=authorships.countries&per-page=50')
    req = urllib.request.Request(url, headers={'User-Agent': 'geometry-research mailto:research@example.com'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read().decode())
            counts = {}
            for g in d.get('group_by', []):
                cc = g['key'].rstrip('/').split('/')[-1].upper()
                counts[cc] = g['count']
            return counts
        except Exception as e:
            if attempt == 3:
                print(f'  ERR {country} {year}: {e}', file=sys.stderr); return None
            time.sleep(3 * (attempt + 1))

def main():
    out = {}
    for year in YEARS:
        row = {}
        for c in CORE:
            counts = query(c, year)
            if counts is None: continue
            row[c] = counts
            time.sleep(0.35)  # 限速
        out[year] = row
        print(f'year {year} done: {len(row)} countries', flush=True)
    with open('gpu_spectra/society/openalex_coauth_13c.json', 'w') as f:
        json.dump(out, f)
    print('saved gpu_spectra/society/openalex_coauth_13c.json')

if __name__ == '__main__':
    main()
