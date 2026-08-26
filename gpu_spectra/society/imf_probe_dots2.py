#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DOTS 数据端点正式试探：按 ECOFIN_DSD 维度顺序构造 key"""
import os, urllib.request, urllib.error

BASE = 'https://sdmxcentral.imf.org/ws/public/sdmxapi/rest'

def probe(url, save=None):
    req = urllib.request.Request(url, headers={'Accept': 'application/xml, application/json'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '')
            if save:
                open(save, 'wb').write(body)
            return f'HTTP {r.status} | {ct[:40]} | {len(body)} bytes'
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code} | {e.read()[:400].decode("utf-8","replace")[:400]}'
    except Exception as e:
        return f'{type(e).__name__}: {e}'

# key = DATA_DOMAIN.REF_AREA.INDICATOR.COUNTERPART_AREA.FREQ
# 数据域猜测: DOT；指标: TXG_FOB_USD (出口) / TMG_CIF_USD (进口)；频率: A (年度)
tests = [
    ('A1', f'{BASE}/data/IMF,DOTS,DOT.CN.TXG_FOB_USD.US.A?startPeriod=2023&endPeriod=2024'),
    ('A2', f'{BASE}/data/IMF,DOTS,DOT.CN.TMG_CIF_USD.US.A?startPeriod=2023&endPeriod=2024'),
    ('A3', f'{BASE}/data/IMF,DOTS,.CN.TXG_FOB_USD..?startPeriod=2023&endPeriod=2024'),
    ('A4', f'{BASE}/data/IMF,DOTS,DOT.CN.TXG_FOB_USD.US.M?startPeriod=2023-01&endPeriod=2024-12'),
]
for name, url in tests:
    print(f'[{name}] {url}')
    print(f'  -> {probe(url, f"/tmp/imf_dots_{name}.xml")}')
