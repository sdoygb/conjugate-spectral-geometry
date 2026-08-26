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

cands = [
    ('3.0 dataflow list', 'https://api.imf.org/external/sdmx/3.0/dataflow/IMF'),
    ('3.0 dataflow list refs', 'https://api.imf.org/external/sdmx/3.0/dataflow/IMF?references=children'),
    ('3.0 dataflow DOT', 'https://api.imf.org/external/sdmx/3.0/dataflow/IMF/DOT'),
    ('3.0 dataflow IMF.DOT', 'https://api.imf.org/external/sdmx/3.0/dataflow/IMF.DOT'),
    ('3.0 data DOT', 'https://api.imf.org/external/sdmx/3.0/data/IMF,DOT,./ALL?startPeriod=2023'),
]

for name, url in cands:
    st, ct, body = fetch(url)
    print(f'===== [{st}] {name} ({ct}) size={len(body)} =====')
    txt = body.decode('utf-8', 'replace')
    print(txt[:500].replace('\n', ' ')[:500])
    print()
