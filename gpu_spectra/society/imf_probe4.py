#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第4轮：SDMX 3.0 标准 Accept 头 + 找 portal APIM 网关真实路径"""
import os, urllib.request, urllib.error

KEY = open(os.path.join(os.path.dirname(__file__), '.imf_api_key')).read().strip()

ACCEPTS = [
    'application/vnd.sdmx.structure+json;version=1.0.0',
    'application/vnd.sdmx.data+json;version=1.0.0',
    'application/xml',
    'application/json',
]

def probe(url, headers, save=None):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            if save and body:
                open(save, 'wb').write(body)
            return f'HTTP {r.status} | {r.headers.get("Content-Type","")[:45]} | {len(body)}B | {body[:120].decode("utf-8","replace")[:100]}'
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code} | {e.read()[:200].decode("utf-8","replace")[:180]}'
    except Exception as e:
        return f'{type(e).__name__}: {e}'

print('=== api.imf.org/external/sdmx/3.0 结构端点，不同 Accept ===')
for acc in ACCEPTS:
    url = 'https://api.imf.org/external/sdmx/3.0/structure/dataflow/IMF'
    r = probe(url, {'Accept': acc})
    print(f'  [{acc[:45]}] -> {r}')

print('\n=== api.imf.org 数据端点，SDMX JSON Accept ===')
for url in [
    'https://api.imf.org/external/sdmx/3.0/data/IMF,DOTS,1.0/DOT.CN.TXG_FOB_USD.US.A?startPeriod=2023&endPeriod=2024',
    'https://api.imf.org/external/sdmx/3.0/data/IMF,DOTS/DOT.CN.TXG_FOB_USD.US.A?startPeriod=2023&endPeriod=2024',
    'https://api.imf.org/external/sdmx/3.0/data/IMF,DOTS/A.CN.TXG_FOB_USD.US?startPeriod=2023&endPeriod=2024',
]:
    r = probe(url, {'Accept': 'application/vnd.sdmx.data+json;version=1.0.0'})
    print(f'  [{url[:100]}] -> {r}')

print('\n=== portal APIM 网关路径候选（带 key header）===')
for path in [
    '/idata/sdmx/3.0/dataflow/IMF',
    '/api/idata/sdmx/3.0/dataflow/IMF',
    '/sdmx/3.0/dataflow/IMF',
    '/external/sdmx/3.0/structure/dataflow/IMF',
    '/dataflow/IMF',
    '/IMF/sdmx/3.0/dataflow/IMF',
]:
    url = 'https://portal.api.imf.org' + path
    r = probe(url, {'Ocp-Apim-Subscription-Key': KEY, 'Accept': 'application/vnd.sdmx.structure+json;version=1.0.0'})
    tag = 'HTML登录页' if 'DOCTYPE html' in r else r
    print(f'  [{path}] -> {tag}')
