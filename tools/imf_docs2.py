import urllib.request, urllib.error, re

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 'ERR', str(e).encode()

targets = [
    ('sdmxcentral', 'https://sdmxcentral.imf.org/'),
    ('imf.data refman', 'https://cran.r-project.org/web/packages/imf.data/refman/imf.data.html'),
    ('apis.io openapi', 'https://apis.io/apis/imf/imf-sdmx-30-data-api/'),
    ('IMF 3.0 data.imf.org', 'https://data.imf.org/external/sdmx/3.0/dataflow/IMF'),
]

for name, url in targets:
    st, body = fetch(url)
    txt = body.decode('utf-8', 'replace')
    print(f'===== [{st}] {name} =====')
    # 找 URL / 端点模式
    hits = re.findall(r'https?://[^\s"\'<>)]+', txt)
    seen = set()
    for h in hits:
        if any(k in h.lower() for k in ('sdmx', 'api.imf', 'idata', 'dataflow')):
            if h not in seen:
                seen.add(h)
                print('  ', h[:160])
    # 找 DOTS / DOT 引用
    for m in re.finditer(r'[^\n]{0,60}(?:DOT|DOTS)[^\n]{0,100}', txt):
        s = m.group(0).strip()
        if 'DOT' in s.upper():
            print('  ~', s[:180])
    print()
