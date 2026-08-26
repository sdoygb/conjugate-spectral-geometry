#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sdmxcentral IMF: 找 DOT 数据流 ID + 试探数据端点"""
import json, os, urllib.request, urllib.error

BASE = 'https://sdmxcentral.imf.org/ws/public/sdmxapi/rest'

def probe(url, save=None):
    req = urllib.request.Request(url, headers={'Accept': 'application/xml, application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '')
            if save:
                open(save, 'wb').write(body)
            return f'HTTP {r.status} | {ct[:40]} | {len(body)} bytes'
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code} | {e.read()[:200].decode("utf-8","replace")[:200]}'
    except Exception as e:
        return f'{type(e).__name__}: {e}'

# 1. 数据流目录（找 DOT）
print('[1] dataflow/IMF ->', probe(f'{BASE}/dataflow/IMF', '/tmp/imf_dataflow.xml'))
# 2. 直接查 DOT 数据流
print('[2] dataflow/IMF/DOT ->', probe(f'{BASE}/dataflow/IMF/DOT', '/tmp/imf_dot_dataflow.xml'))
# 3. 试探 DOT 数据（最简 key）
print('[3] data/IMF,DOT ->', probe(f'{BASE}/data/IMF,DOT,....,?startPeriod=2023&endPeriod=2024', '/tmp/imf_dot_data.xml'))
