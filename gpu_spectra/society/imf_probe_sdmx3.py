#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并发探测 portal.api.imf.org 网关路径（ThreadPool 8并发）"""
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

KEY = 'fb93f6f01b0a41d88a98e47c5f8cf9f2'
paths = [
    '/idata/sdmx/3.0/dataflow/IMF',
    '/api/idata/sdmx/3.0/dataflow/IMF',
    '/idata-api/sdmx/3.0/dataflow/IMF',
    '/api/sdmx/3.0/dataflow/IMF',
    '/sdmx/3.0/dataflow/IMF',
    '/idata/sdmx/3.0/structure/dataflow/IMF',
    '/idata/sdmx/3.0/data/IMF,DOT,....',
    '/idata/dataflow/IMF',
    '/idata/v1/data/IMF,DOT,....',
    '/external/sdmx/3.0/dataflow/IMF',
    '/external/sdmx/2.1/data/IMF,DOT,....',
    '/idata/sdmx/3.0/dataflow/IMF?format=json',
]

def probe(path):
    url = 'https://portal.api.imf.org' + path
    req = urllib.request.Request(url, headers={
        'Accept': 'application/json, application/xml',
        'Ocp-Apim-Subscription-Key': KEY,
        'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            ct = r.headers.get('Content-Type', '')
            body = r.read(120)
            kind = 'HTML' if 'html' in ct else 'DATA'
            return f'  {r.status:3d} {kind:4s} CT={ct[:36]:36s} {body[:60].decode("utf-8","replace")[:60]!r}'
    except urllib.error.HTTPError as e:
        ct = e.headers.get('Content-Type', '')
        body = e.read()[:120]
        kind = 'HTML' if 'html' in ct else 'DATA'
        return f'  {e.code:3d} {kind:4s} CT={ct[:36]:36s} {body.decode("utf-8","replace")[:60]!r}'
    except Exception as e:
        return f'  ERR {str(e)[:70]}'

with ThreadPoolExecutor(max_workers=8) as ex:
    for p, res in zip(paths, ex.map(probe, paths)):
        print(f'[{p}]')
        print(res)
