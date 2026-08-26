#!/usr/bin/env python3
"""IMF SDMX 3.0 数据端点探测：验证 CN→TW / CN→US 序列响应格式
序列: IMTS (前 DOTS)  COUNTRY.INDICATOR.COUNTERPART_COUNTRY.FREQUENCY
示例: CN.XG_FOB_USD.TW.A  = 中国出口到台湾，年度
"""
import json, urllib.request, urllib.error, os, time

KEY = open('/Users/oygb/.imf_api_key').read().strip()

BASE3 = 'https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/IMTS/1.0.0'
BASE2 = 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,'

SERIES = [
    ('CN->TW X annual (v3)',   f'{BASE3}/CN.XG_FOB_USD.TW.A'),
    ('CN->US X annual (v3)',   f'{BASE3}/CN.XG_FOB_USD.US.A'),
    ('TW->CN X annual (v3)',   f'{BASE3}/TW.XG_FOB_USD.CN.A'),
    ('CN->TW X annual (v2)',   f'{BASE2}CN.XG_FOB_USD.TW.A'),
]

def fetch(name, url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '?')
            print(f"[OK] {name}\n     HTTP {r.status} CT={ct} {len(body)}B")
            return body
    except urllib.error.HTTPError as e:
        msg = e.read()[:400]
        print(f"[HTTP {e.code}] {name}\n     {msg!r}")
        return None
    except Exception as e:
        print(f"[ERR {type(e).__name__}] {name}\n     {e}")
        return None

if __name__ == '__main__':
    for name, url in SERIES:
        # 变体 A：无 key
        body = fetch(name + ' [nokey]', url, {'Accept': 'application/vnd.sdmx.data+json;version=1.0.0'})
        if body and len(body) > 300:
            open('/tmp/imf_series_probe.json', 'wb').write(body)
            print("     ^ saved to /tmp/imf_series_probe.json")
            try:
                d = json.loads(body)
                data = d.get('data', {})
                dsets = data.get('dataSets', [])
                struct = data.get('structure', {})
                dims = struct.get('dimensions', {}).get('dataSet', [])
                print(f"     dataSets={len(dsets)} dims={[x.get('id') for x in dims]}")
                if dsets:
                    obs = dsets[0].get('observations', {})
                    n = len(obs)
                    print(f"     observations={n}")
                    # 打印前 8 个观察值
                    keys = sorted(obs.keys(), key=lambda k: [int(x) for x in k.split(':')])
                    series_keys = struct.get('dimensions', {}).get('series', [])
                    print(f"     series dims={[x.get('id') for x in series_keys]}")
                    for k in keys[:8]:
                        print(f"       {k}: {obs[k]}")
                    print(f"     ... 共 {n} 个观察值")
            except Exception as e:
                print(f"     parse err: {e}")
            break  # 第一个成功就停
        time.sleep(1)
