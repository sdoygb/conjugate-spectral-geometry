#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IMF SDMX 端点精确路径探测（第2轮）"""
import json, os, urllib.request, urllib.error

KEY = open(os.path.join(os.path.dirname(__file__), '.imf_api_key')).read().strip()

CANDIDATES = [
    # api.imf.org/external/sdmx/3.0 结构端点变体
    'https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF',
    'https://api.imf.org/external/sdmx/3.0/structure/dataflow/IMF',
    'https://api.imf.org/external/sdmx/3.0/dataflow/IMF',
    'https://api.imf.org/external/sdmx/3.0/structure/dataflow/IMF?format=sdmx-json',
    # sdmxcentral（官方，无需 key）
    'https://sdmxcentral.imf.org/ws/public/sdmxapi/rest/dataflow/IMF',
    'https://sdmxcentral.imf.org/sdmx/rest/dataflow/IMF',
    # 数据端点（DOT 数据流直接试探）
    'https://api.imf.org/external/sdmx/3.0/data/IMF,DOT,....,?startPeriod=2023&endPeriod=2024',
]

def probe(url):
    headers = {'Accept': 'application/json'}
    if 'portal.api.imf.org' in url:
        headers['Ocp-Apim-Subscription-Key'] = KEY
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '')
            head = body[:300].decode('utf-8', 'replace').replace('\n', ' ')
            return f'HTTP {r.status} | {ct[:40]} | {head[:260]}'
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code} | {e.headers.get("Content-Type", "")[:40]} | {e.read()[:200].decode("utf-8", "replace")[:200]}'
    except Exception as e:
        return f'{type(e).__name__}: {e}'

for url in CANDIDATES:
    print(f'[{url}]')
    print(f'  -> {probe(url)}')
