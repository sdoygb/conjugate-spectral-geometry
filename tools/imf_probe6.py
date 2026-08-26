import urllib.request, urllib.error, json

def fetch(url, accept):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': accept})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.headers.get('Content-Type', ''), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Content-Type', ''), e.read()
    except Exception as e:
        return 'ERR', '', str(e).encode()

base = 'https://api.imf.org/external/sdmx/3.0/structure/dataflow'
accepts = [
    ('v2.0.0 structure json', 'application/vnd.sdmx.structure+json;version=2.0.0'),
    ('v2.0.0 data json', 'application/vnd.sdmx.data+json;version=2.0.0'),
    ('无Accept默认', None),
    ('xml', 'application/xml'),
]
for name, acc in accepts:
    st, ct, body = fetch(base, acc or '')
    txt = body.decode('utf-8', 'replace')
    print(f'===== [{st}] {name} ({ct}) size={len(body)} =====')
    if st == 200:
        try:
            j = json.loads(txt)
            s = json.dumps(j)
            print('  json keys:', list(j.keys())[:5])
            # 列出 dataflow 条目
            def find_flows(o, depth=0):
                if isinstance(o, dict):
                    if 'dataflows' in o:
                        for f in o['dataflows']:
                            f0 = f.get('dataflow', f)
                            print('  FLOW:', f0.get('id'), '|', f0.get('agencyID'), '|', f0.get('version'))
                    for v in o.values():
                        find_flows(v, depth+1)
                elif isinstance(o, list):
                    for it in o:
                        find_flows(it, depth+1)
            find_flows(j)
            # DOT 命中
            import re
            for m in re.finditer(r'"(?:id)":\s*"([^"]*DOT[^"]*)"', s):
                print('  DOT hit:', m.group(1))
        except Exception as e:
            print('  parse err:', e)
            print('  ', txt[:400].replace('\n', ' '))
    else:
        print('  ', txt[:300].replace('\n', ' '))
    print()
