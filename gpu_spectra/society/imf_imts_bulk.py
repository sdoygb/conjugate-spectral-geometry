#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IMF IMTS 批量下载：49 报告国（探针30 NODES 22 国 + EU27 成员国）
v2.1 免 key 端点，全量 {ISO3}...A，区间 2022-2026（含 2023 重叠验证）
输出: society/imts_bulk_raw/{ISO3}.xml + imts_bulk_parsed.json（仅 MG_CIF_USD/XG_FOB_USD/TBG_USD）
"""
import json, os, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = 'https://api.imf.org/external/sdmx/2.1/data/IMF.STA,IMTS,1.0.0'
OUTDIR = 'imts_bulk_raw'
os.makedirs(OUTDIR, exist_ok=True)

# 探针30 NODES：节点名 -> IMF 伙伴码（用于结果组织）
NODES = {'CN':'924','TW':'528','US':'111','JP':'158','IN':'534','EU':'998','KR':'542',
         'RU':'922','HK':'532','GB':'112','CA':'156','AU':'193','BR':'223','MX':'273',
         'ID':'536','SG':'576','TH':'578','MY':'548','VN':'582','PH':'566','PK':'564',
         'SA':'456','CH':'146'}
# 节点名 -> 报告国 ISO3（EU 为聚合，不直接下载）
NAME2ISO = {'CN':'CHN','TW':'TWN','US':'USA','JP':'JPN','IN':'IND','KR':'KOR','RU':'RUS',
            'HK':'HKG','GB':'GBR','CA':'CAN','AU':'AUS','BR':'BRA','MX':'MEX','ID':'IDN',
            'SG':'SGP','TH':'THA','MY':'MYS','VN':'VNM','PH':'PHL','PK':'PAK','SA':'SAU','CH':'CHE'}
EU27 = ['AUT','BEL','BGR','HRV','CYP','CZE','DNK','EST','FIN','FRA','DEU','GRC',
        'HUN','IRL','ITA','LVA','LTU','LUX','MLT','NLD','POL','PRT','ROU','SVK',
        'SVN','ESP','SWE']

REPORTERS = sorted(set(NAME2ISO.values()) | set(EU27))
print(f'报告国: {len(REPORTERS)} 个 = 22 节点 + EU27({len(EU27)})', flush=True)

def fetch(iso3):
    url = f'{BASE}/{iso3}...A?startPeriod=2022&endPeriod=2026'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
                                               'Accept': 'application/vnd.sdmx.structurespecificdata+xml;version=2.1'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
            fn = os.path.join(OUTDIR, f'{iso3}.xml')
            open(fn, 'wb').write(body)
            return iso3, 'OK', len(body)
    except urllib.error.HTTPError as e:
        return iso3, f'HTTP{e.code}', 0
    except Exception as e:
        return iso3, f'{type(e).__name__}:{e}', 0

def main():
    t0 = time.time()
    ok, fail = [], []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch, iso): iso for iso in REPORTERS}
        for fut in as_completed(futs):
            iso, st, n = fut.result()
            if st == 'OK':
                ok.append((iso, n))
                print(f'  [{len(ok)}/{len(REPORTERS)}] {iso}: {n/1e6:.2f}MB ({time.time()-t0:.0f}s)', flush=True)
            else:
                fail.append((iso, st))
                print(f'  [FAIL] {iso}: {st}', flush=True)
    print(f'完成: OK={len(ok)} FAIL={len(fail)} 耗时 {time.time()-t0:.0f}s')
    if fail:
        print('失败:', fail)
    return 0 if not fail else 1

if __name__ == '__main__':
    sys.exit(main())
