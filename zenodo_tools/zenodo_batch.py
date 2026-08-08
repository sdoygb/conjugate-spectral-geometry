# -*- coding: utf-8 -*-
"""Zenodo 批量更新/新建脚本（断点续传）
用法:
  python3 zenodo_tools/zenodo_batch.py update [limit]   # 更新已有记录（清单 update_manifest.json）
  python3 zenodo_tools/zenodo_batch.py create [limit]   # 新建记录（清单 create_pdfs.json）
"""
import requests, json, time, os, re, sys
from urllib.parse import quote

TOKEN = open('zenodo_tools/.zenodo_token').read().strip()
BASE = 'https://zenodo.org/api'
H = {'Authorization': f'Bearer {TOKEN}'}
PROGRESS_FILE = 'zenodo_tools/progress.json'
LOG_FILE = 'zenodo_tools/batch.log'
SLEEP = 3

def log(msg):
    line = time.strftime('%H:%M:%S') + ' ' + msg
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def api(method, path, retries=6, **kw):
    url = BASE + path
    kw.setdefault('headers', {})
    kw['headers'].update(H)
    for i in range(retries):
        try:
            r = requests.request(method, url, timeout=180, **kw)
        except Exception as e:
            log(f'  [异常] {method} {path}: {e}')
            time.sleep(2)
            continue
        if r.status_code in (200, 201, 202, 204):
            return r
        if r.status_code == 429:
            wait = min(2 ** i * 2, 60)
            log(f'  429 限流，等待 {wait}s')
            time.sleep(wait)
            continue
        if r.status_code == 500:
            log(f'  [500] {method} {path}')
            time.sleep(5)
            continue
        log(f'  [{r.status_code}] {method} {path}: {r.text[:200]}')
        return r
    return None

def upload_files(draft_id, pdf_path):
    fname = os.path.basename(pdf_path)
    qname = quote(fname, safe='')
    r = api('POST', f'/records/{draft_id}/draft/files', json=[{'key': fname}])
    if not r or r.status_code not in (200, 201):
        return False
    with open(pdf_path, 'rb') as f:
        r = api('PUT', f'/records/{draft_id}/draft/files/{qname}/content',
                data=f, headers={'Content-Type': 'application/octet-stream'})
    if not r or r.status_code not in (200, 201):
        return False
    r = api('POST', f'/records/{draft_id}/draft/files/{qname}/commit')
    if not r or r.status_code not in (200, 201, 202):
        return False
    return True

def md_to_old_format(md):
    lic = md.get('license')
    lic_id = lic.get('id') if isinstance(lic, dict) else (lic or 'cc-by-nc-sa-4.0')
    return {
        'title': md.get('title', ''),
        'description': md.get('description', ''),
        'publication_date': md.get('publication_date', '2026-08-08'),
        'access_right': md.get('access_right', 'open'),
        'license': lic_id,
        'version': '260808',
        'upload_type': 'publication',
        'publication_type': 'preprint',
        'creators': [{'name': c['name']} for c in md.get('creators', [])],
        'language': md.get('language', 'zho'),
        'keywords': md.get('keywords', [])
    }

def update_record(item):
    no, recid, pdf = item['no'], item['recid'], item['pdf']
    pdf_path = 'app/articles/PDF/' + pdf
    log(f'[更新 {no}] recid={recid} pdf={pdf}')
    r = api('POST', f'/records/{recid}/versions')
    if not r or r.status_code not in (200, 201):
        return False, 'versions失败'
    draft_id = str(r.json().get('id'))
    log(f'  新draft={draft_id}')
    r = api('GET', f'/records/{draft_id}/draft')
    if not r or r.status_code != 200:
        return False, 'GET draft失败'
    md = r.json().get('metadata', {})
    if not upload_files(draft_id, pdf_path):
        return False, '上传文件失败'
    log('  文件上传完成')
    md_old = md_to_old_format(md)
    r = api('PUT', f'/deposit/depositions/{draft_id}', json={'metadata': md_old})
    if not r or r.status_code not in (200, 201):
        return False, 'PUT metadata失败'
    log('  metadata写入完成(version=260808)')
    r = api('POST', f'/deposit/depositions/{draft_id}/actions/publish')
    if not r or r.status_code not in (200, 201, 202):
        return False, '发布失败'
    d = r.json()
    log(f'  OK id={d.get("id")} doi={d.get("doi")}')
    return True, {'id': d.get('id'), 'doi': d.get('doi'), 'conceptdoi': d.get('conceptdoi')}

def extract_title_desc(md_path):
    with open(md_path, encoding='utf-8') as f:
        txt = f.read()
    m = re.search(r'^#\s+(.+)$', txt, re.M)
    title = m.group(1).strip() if m else os.path.basename(md_path)
    m2 = re.search(r'摘\s*要\s*\n(.*?)(?:\n##|\n#|\Z)', txt, re.S)
    desc = m2.group(1).strip() if m2 else ''
    desc = re.sub(r'\n{2,}', '\n', desc)[:3000]
    return title, desc

def create_record(pdf, md_path):
    title, desc = extract_title_desc(md_path)
    log(f'[新建] pdf={pdf} title={title[:50]}')
    md_old = {
        'title': title,
        'description': desc,
        'publication_date': '2026-08-08',
        'access_right': 'open',
        'license': 'cc-by-nc-sa-4.0',
        'version': '260808',
        'upload_type': 'publication',
        'publication_type': 'preprint',
        'creators': [{'name': 'Ouyang, Guobin'}],
        'language': 'zho',
        'keywords': ['共扼谱几何', 'Conjugate Spectral Geometry', 'Clifford代数', 'Bott周期', '谱几何', '数学物理', 'Geometric Physics']
    }
    r = api('POST', '/deposit/depositions', json={'metadata': md_old})
    if not r or r.status_code not in (200, 201):
        return False, '创建失败'
    draft_id = str(r.json().get('id'))
    log(f'  创建draft={draft_id}')
    if not upload_files(draft_id, 'app/articles/PDF/' + pdf):
        return False, '上传文件失败'
    log('  文件上传完成')
    r = api('POST', f'/deposit/depositions/{draft_id}/actions/publish')
    if not r or r.status_code not in (200, 201, 202):
        return False, '发布失败'
    d = r.json()
    log(f'  OK id={d.get("id")} doi={d.get("doi")}')
    return True, {'id': d.get('id'), 'doi': d.get('doi')}

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        return json.load(open(PROGRESS_FILE))
    return {}

def save_progress(p):
    json.dump(p, open(PROGRESS_FILE, 'w'), ensure_ascii=False, indent=2)

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'update'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    progress = load_progress()
    items = json.load(open('zenodo_tools/update_manifest.json')) if mode == 'update' else json.load(open('zenodo_tools/create_pdfs.json'))
    done = 0
    for item in items:
        key = ('u:' + item['no']) if isinstance(item, dict) else ('c:' + item)
        if key in progress and progress[key].get('ok'):
            continue
        if limit and done >= limit:
            break
        try:
            if mode == 'update':
                ok, info = update_record(item)
            else:
                md_path = 'app/articles/ZH/' + item.replace('.pdf', '.md')
                ok, info = create_record(item, md_path)
        except Exception as e:
            ok, info = False, str(e)
        progress[key] = {'ok': ok, 'info': info, 'time': time.strftime('%Y-%m-%d %H:%M:%S')}
        save_progress(progress)
        done += 1
        time.sleep(SLEEP)
    ok_n = sum(1 for v in progress.values() if v.get('ok'))
    fail_n = sum(1 for v in progress.values() if not v.get('ok'))
    log(f'== 本轮结束: 成功 {ok_n}, 失败 {fail_n} ==')
