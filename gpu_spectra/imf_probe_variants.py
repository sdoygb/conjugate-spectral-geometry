#!/usr/bin/env python3
"""IMF SDMX 3.0 API 端点变体探测"""
import urllib.request, urllib.error

KEY = open('/Users/oygb/.imf_api_key').read().strip()

VARIANT = [
    ("portal /idata/dataflow (key header)", 'https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF', {'Ocp-Apim-Subscription-Key': KEY}),
    ("portal /idata/dataflow (key query)", 'https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF?subscription-key=' + KEY, {}),
    ("api.external dataflow no key", 'https://api.imf.org/external/sdmx/3.0/dataflow/IMF', {}),
    ("api.external dataflow with key", 'https://api.imf.org/external/sdmx/3.0/dataflow/IMF?subscription-key=' + KEY, {}),
    ("portal root dataflow no key", 'https://portal.api.imf.org/sdmx/3.0/dataflow/IMF', {}),
    ("portal /idata no accept header", 'https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF', {'Ocp-Apim-Subscription-Key': KEY, 'Accept': '*/*'}),
]

for name, url, hdr in VARIANT:
    req = urllib.request.Request(url, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '?')
            print(f"[OK] {name}\n     HTTP {r.status} CT={ct} {len(body)}B\n     head: {body[:120]!r}\n")
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {name}\n     {e.read()[:200]!r}\n")
    except Exception as e:
        print(f"[ERR {type(e).__name__}] {name}\n     {e}\n")
