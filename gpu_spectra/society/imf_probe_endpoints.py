#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IMF SDMX 3.0 API 端点探测：找到返回真实数据的路径"""
import json, os, sys, urllib.request, urllib.error

KEY = open(os.path.join(os.path.dirname(__file__), '.imf_api_key')).read().strip()

# 候选端点（门户网关路径变体）
CANDIDATES = [
    'https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF?limit=2',
    'https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF',
    'https://portal.api.imf.org/api/idata/sdmx/3.0/dataflow/IMF?limit=2',
    'https://portal.api.imf.org/sdmx/3.0/dataflow/IMF?limit=2',
    'https://api.imf.org/external/sdmx/3.0/dataflow/IMF?limit=2',
    'https://api.imf.org/idata/sdmx/3.0/dataflow/IMF?limit=2',
    'https://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/IMF?limit=2',
]

def probe(url):
    req = urllib.request.Request(url, headers={
        'Ocp-Apim-Subscription-Key': KEY,
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '')
            head = body[:200].decode('utf-8', 'replace').replace('\n', ' ')
            return f'HTTP {r.status} | {ct[:40]} | {head[:160]}'
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code} | {e.headers.get("Content-Type", "")[:40]} | {e.read()[:160].decode("utf-8", "replace")[:160]}'
    except Exception as e:
        return f'{type(e).__name__}: {e}'

for url in CANDIDATES:
    print(f'[{url}]')
    print(f'  -> {probe(url)}')
