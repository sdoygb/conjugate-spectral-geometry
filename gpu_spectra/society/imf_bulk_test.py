#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量下载前的格式探测：测试 v2.1 全量请求 {ISO3}...A 的各种 Accept/format 变体"""
import urllib.request, urllib.error, sys, time

BASE2 = 'https://api.imf.org/external/sdmx/2.1/data/IMF.STA,IMTS,1.0.0'
BASE3 = 'https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/IMTS/1.0.0'

TESTS = [
    # (name, url, headers)
    ('v2.1 XML full CHN', f'{BASE2}/CHN...A',
     {'Accept': 'application/vnd.sdmx.structurespecificdata+xml;version=2.1', 'User-Agent': 'Mozilla/5.0'}),
    ('v2.1 XML full CHN (default)', f'{BASE2}/CHN...A',
     {'User-Agent': 'Mozilla/5.0'}),
    ('v2.1 JSON v1 CHN', f'{BASE2}/CHN...A',
     {'Accept': 'application/vnd.sdmx.data+json;version=1.0.0', 'User-Agent': 'Mozilla/5.0'}),
    ('v2.1 JSON v2 CHN', f'{BASE2}/CHN...A',
     {'Accept': 'application/vnd.sdmx.data+json;version=2.0.0', 'User-Agent': 'Mozilla/5.0'}),
    ('v2.1 JSON format param CHN', f'{BASE2}/CHN...A?format=jsondata',
     {'User-Agent': 'Mozilla/5.0'}),
    ('v3 JSON full CHN', f'{BASE3}/CHN...A?startPeriod=1990&endPeriod=2026',
     {'Accept': 'application/vnd.sdmx.data+json;version=2.0.0', 'User-Agent': 'Mozilla/5.0'}),
]

def run(name, url, headers):
    req = urllib.request.Request(url, headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '?')
            print(f'[OK] {name}\n     HTTP {r.status} CT={ct} {len(body)}B ({time.time()-t0:.1f}s)')
            return body
    except urllib.error.HTTPError as e:
        msg = e.read()[:200]
        print(f'[HTTP {e.code}] {name}\n     {msg!r}')
        return None
    except Exception as e:
        print(f'[ERR {type(e).__name__}] {name}\n     {e}')
        return None

if __name__ == '__main__':
    for name, url, headers in TESTS:
        body = run(name, url, headers)
        if body and len(body) > 10000:
            # 保存第一个成功的，供解析测试
            tag = name.split()[0].replace('.', '_')
            fn = f'/tmp/imf_bulk_{tag}.bin'
            open(fn, 'wb').write(body)
            print(f'     ^ saved {fn}')
        time.sleep(0.5)
