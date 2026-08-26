import urllib.request, urllib.error, json

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
                                               'Accept': 'application/vnd.sdmx.data+json;version=1.0.0, application/json'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.headers.get('Content-Type', ''), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Content-Type', ''), e.read()
    except Exception as e:
        return 'ERR', '', str(e).encode()

st, ct, body = fetch('https://api.imf.org/external/sdmx/3.0/structure/dataflow')
print(f'===== [{st}] structure/dataflow ({ct}) size={len(body)} =====')
txt = body.decode('utf-8', 'replace')
if st == 200:
    try:
        j = json.loads(txt)
        def walk(o, path=''):
            if isinstance(o, dict):
                if 'id' in o and ('name' in o or 'names' in o):
                    nm = o.get('name') or (o.get('names', [{}])[0].get('name') if o.get('names') else '')
                    print('  FLOW:', o.get('id'), '| agency:', o.get('agencyID'), '| ver:', o.get('version'), '|', str(nm)[:60])
                for k, v in o.items():
                    walk(v, path + '/' + k)
            elif isinstance(o, list):
                for it in o:
                    walk(it, path)
        walk(j)
        # 找 DOT 相关
        s = json.dumps(j)
        import re
        for m in re.finditer(r'"(?:id|Name|name)":\s*"([^"]*DOT[^"]*)"', s):
            print('  HIT DOT:', m.group(1))
    except Exception as e:
        print('json parse err', e)
        print(txt[:800])
else:
    print(txt[:500])
