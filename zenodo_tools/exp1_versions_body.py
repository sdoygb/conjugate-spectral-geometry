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
        print(f'  [{r.status_code}] {method} {path}: {r.text[:400]}')
        if r.status_code == 500:
            time.sleep(3)
            continue
        return r
    return None

# 1. 删除半损坏 draft（21847174 已被测试清掉字段）
r = api('DELETE', '/records/21847174/draft')
print('删除旧draft 21847174:', r.status_code if r else 'None')

# 2. POST versions 带 metadata body（测试创建新版本时能否直接写入 version）
body = {'metadata': {'version': '260808'}}
r = api('POST', '/records/21717496/versions', json=body)
if r and r.status_code in (200, 201):
    d = r.json()
    new_id = d.get('id')
    print('新draft id:', new_id)
    # 3. GET 检查 metadata 继承 + version 是否写入
    r2 = api('GET', f'/records/{new_id}/draft')
    if r2:
        md = r2.json().get('metadata', {})
        print('version:', md.get('version'))
        print('keys:', sorted(md.keys()))
        print('resource_type:', json.dumps(md.get('resource_type'), ensure_ascii=False))
        print('license:', json.dumps(md.get('license'), ensure_ascii=False))
        print('language:', md.get('language'))
        print('keywords:', json.dumps(md.get('keywords'), ensure_ascii=False))
        print('creators:', json.dumps(md.get('creators'), ensure_ascii=False))
        print('title:', md.get('title'))
        print('files:', json.dumps(r2.json().get('files', []), ensure_ascii=False)[:500])
        json.dump({'id': new_id, 'metadata': md}, open('zenodo_tools/draft_state.json', 'w'), ensure_ascii=False, indent=2)
        print('状态已保存到 zenodo_tools/draft_state.json')
    else:
        print('GET draft 失败')
else:
    print('POST versions 失败:', r.status_code if r else 'None', r.text[:300] if r else '')
