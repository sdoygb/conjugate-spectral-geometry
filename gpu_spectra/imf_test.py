#!/usr/bin/env python3
"""IMF SDMX 3.0 API 连通性测试"""
import json, urllib.request, urllib.error

KEY = open('/Users/oygb/.imf_api_key').read().strip()

def fetch(url, out=None, accept='application/vnd.sdmx.data+json;version=1.0.0'):
    req = urllib.request.Request(url, headers={'Ocp-Apim-Subscription-Key': KEY, 'Accept': accept})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            print(f"HTTP {r.status}, {len(body)} bytes")
            if out:
                open(out, 'wb').write(body)
            return body
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR {e.code}: {e.reason}")
        print(e.read()[:500])
        return None
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return None

if __name__ == '__main__':
    print("=== 1. dataflow 目录 ===")
    b1 = fetch('https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF', '/tmp/imf_dataflow.json')
    if b1:
        try:
            d = json.loads(b1)
            flows = d.get('data', {}).get('dataflows', [])
            print(f"dataflow 数量: {len(flows)}")
            for f in flows[:40]:
                aid = f.get('id', '?')
                name = f.get('name', '?')
                if isinstance(name, dict):
                    name = name.get('en', name)
                print(f"  {aid}  {str(name)[:70]}")
        except Exception as e:
            print("parse err:", e, b1[:300])
