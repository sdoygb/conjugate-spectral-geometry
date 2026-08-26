#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第3轮：Azure APIM key 的两种传递方式 + api.imf.org 数据端点"""
import os, urllib.request, urllib.error

KEY = open(os.path.join(os.path.dirname(__file__), '.imf_api_key')).read().strip()

CANDIDATES = [
    # portal APIM：header vs query param
    ('P1 header', 'https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF?limit=2', {'Ocp-Apim-Subscription-Key': KEY}),
    ('P2 query', 'https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF?subscription-key=' + KEY, {}),
    # api.imf.org 数据端点（SDMX 3.0 标准格式）
    ('A1 data', 'https://api.imf.org/external/sdmx/3.0/data/IMF,DOTS,1.0/DOT.CN.TXG_FOB_USD.US.A?startPeriod=2023&endPeriod=2024', {}),
    ('A2 data', 'https://api.imf.org/external/sdmx/3.0/data/IMF,DOTS/DOT.CN.TXG_FOB_USD.US.A?startPeriod=2023&endPeriod=2024', {}),
    ('A3 structure', 'https://api.imf.org/external/sdmx/3.0/structure/dataflow/IMF?format=sdmx-json', {}),
]

def probe(name, url, headers):
    h = dict(headers); h.setdefault('Accept', 'application/json')
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '')
            return f'HTTP {r.status} | {ct[:40]} | {len(body)}B | {body[:150].decode("utf-8","replace")[:120]}'
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code} | {e.read()[:250].decode("utf-8","replace")[:230]}'
    except Exception as e:
        return f'{type(e).__name__}: {e}'

for name, url, hdrs in CANDIDATES:
    print(f'[{name}] {url[:110]}')
    print(f'  -> {probe(name, url, hdrs)}')
