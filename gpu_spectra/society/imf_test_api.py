#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IMF SDMX 3.0 API 连通性测试（用本地 key）"""
import json, os, sys, urllib.request

KEY = open(os.path.join(os.path.dirname(__file__), '.imf_api_key')).read().strip()
BASE = 'https://portal.api.imf.org/idata/sdmx/3.0'

def get(path):
    req = urllib.request.Request(BASE + path, headers={
        'Ocp-Apim-Subscription-Key': KEY,
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()

for path in ['/dataflow/IMF?limit=2']:
    try:
        status, body = get(path)
        print(f'[OK] {path} -> HTTP {status}, {len(body)} bytes')
        print(body[:1500].decode('utf-8', 'replace'))
    except Exception as e:
        print(f'[FAIL] {path} -> {type(e).__name__}: {e}')
        sys.exit(1)
