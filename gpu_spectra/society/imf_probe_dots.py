#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DOTS 数据流：查 DSD + 试探数据端点"""
import os, urllib.request, urllib.error

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
        return f'HTTP {e.code} | {e.read()[:300].decode("utf-8","replace")[:300]}'
    except Exception as e:
        return f'{type(e).__name__}: {e}'

# DSD 结构
print('[DSD] dataflow/IMF/DOTS ->', probe(f'{BASE}/dataflow/IMF/DOTS', '/tmp/imf_dots_dsd.xml'))
# 数据端点试探（key 用全点号=所有值）
print('[D1] data/IMF/DOTS/.... ->', probe(f'{BASE}/data/IMF/DOTS/.........?startPeriod=2023&endPeriod=2024', '/tmp/imf_dots_d1.xml'))
# 常见 IMF key: FREQ.REF_AREA.INDICATOR.COMP_BREAKDOWN_1 (4维)
print('[D2] data/IMF/DOTS/A.CN.TXG_FOB_USD.US ->', probe(f'{BASE}/data/IMF/DOTS/A.CN.TXG_FOB_USD.US?startPeriod=2023&endPeriod=2024', '/tmp/imf_dots_d2.xml'))
