import requests, json, time

TOKEN = open('zenodo_tools/.zenodo_token').read().strip()
BASE = 'https://zenodo.org/api'
H = {'Authorization': f'Bearer {TOKEN}'}

def api(method, path, retries=6, **kw):
    url = BASE + path
    kw.setdefault('headers', {})
    kw['headers'].update(H)
    for i in range(retries):
        try:
            r = requests.request(method, url, timeout=120, **kw)
        except Exception as e:
            print(f'  [异常] {method} {path}: {e}')
            time.sleep(2)
            continue
        if r.status_code in (200, 201, 202, 204):
            return r
        if r.status_code == 429:
            wait = 2 ** i * 2
            print(f'  429 限流，等待 {wait}s')
            time.sleep(wait)
            continue
        if r.status_code == 500:
            print(f'  [500] {method} {path}: {r.text[:800]}')
            time.sleep(3)
            continue
        print(f'  [{r.status_code}] {method} {path}: {r.text[:300]}')
        return r
    return None

draft_id = '21847118'
r = api('GET', f'/records/{draft_id}/draft')
if r:
    d = r.json()
    print('=== DRAFT 状态 ===')
    print('id:', d.get('id'))
    print('parent concept:', d.get('parent', {}).get('id'))
    print('status:', d.get('status'))
    md = d.get('metadata', {})
    print('version:', md.get('version'))
    print('title:', md.get('title'))
    files = d.get('files', {}).get('entries', [])
    print('files:', [(f.get('key'), f.get('status'), f.get('size')) for f in files])
    print('metadata keys:', list(md.keys()))
    json.dump(md, open('zenodo_tools/draft_21847118_metadata.json', 'w'), ensure_ascii=False, indent=2)
    print('metadata 已保存到 zenodo_tools/draft_21847118_metadata.json')
    # 也保存顶层结构（不含大字段）
    top = {k: d.get(k) for k in d if k not in ('metadata', 'files')}
    json.dump(top, open('zenodo_tools/draft_21847118_top.json', 'w'), ensure_ascii=False, indent=2, default=str)
    print('top 已保存')
else:
    print('GET draft 失败')
