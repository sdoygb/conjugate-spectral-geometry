#!/usr/bin/env python3
"""Zenodo 批量上传/更新脚本（新平台 InvenioRDM API）
用法:
  python3 zenodo_upload.py update <record_id> <pdf_path>        # 更新已有记录（新版本+换文件+version=260808）
  python3 zenodo_upload.py create <pdf_path> <title>             # 新建记录并发布
  python3 zenodo_upload.py batch_update <map.json>              # 批量更新（JSON: [{id, pdf, title}]）
  python3 zenodo_upload.py batch_create <map.json>              # 批量新建（JSON: [{pdf, title}]）
"""
import requests, time, json, sys, os, re
from urllib.parse import quote

BASE = 'https://zenodo.org/api'
TOKEN = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.zenodo_token')).read().strip()
H = {'Authorization': f'Bearer {TOKEN}'}

# 模板：从 10.20 中文记录复制的 metadata 骨架
TEMPLATE = {
    "creators": [{"person_or_org": {"family_name": "Ouyang", "given_name": "Guobin",
                                    "name": "Ouyang, Guobin", "type": "personal"}}],
    "license": {"id": "cc-by-nc-sa-4.0"},
    "access_right": "open",
    "keywords": ["Conjugate Spectral Geometry", "Clifford Algebra", "Bott Periodicity",
                 "Spectral Geometry", "Mathematical Physics", "Geometric Physics"],
    "language": "eng",
    "resource_type": {"title": "Preprint", "type": "publication", "subtype": "preprint"},
}


def api(method, path, retries=6, **kw):
    url = BASE + path
    kw.setdefault('headers', {})
    kw['headers'].update(H)
    for i in range(retries):
        try:
            r = requests.request(method, url, timeout=180, **kw)
        except requests.exceptions.RequestException as e:
            print(f'  [net] {method} {path} 异常: {e}，重试 {i+1}/{retries}')
            time.sleep(2 ** i)
            continue
        if r.status_code in (200, 201, 202, 204):
            return r
        if r.status_code == 429:
            wait = min(2 ** i * 3, 60)
            print(f'  [429] 限流，等待 {wait}s')
            time.sleep(wait)
            continue
        if r.status_code >= 500:
            print(f'  [{r.status_code}] 服务器错误，重试 {i+1}/{retries}')
            time.sleep(2 ** i)
            continue
        print(f'  [{r.status_code}] {method} {path}: {r.text[:200]}')
        return r
    return None


def get_draft_files(new_id):
    """返回新版本 draft 的文件列表 [{key, status}]"""
    r = api('GET', f'/records/{new_id}/draft')
    if not r or r.status_code != 200:
        return []
    return r.json().get('files', [])


def upload_pdf(new_id, pdf_path):
    """上传 PDF（官方流程：POST files 初始化 -> PUT content -> POST commit）"""
    fname = os.path.basename(pdf_path)
    qname = quote(fname, safe='')
    r = api('POST', f'/records/{new_id}/draft/files', json=[{'key': fname}])
    if not r or r.status_code not in (200, 201):
        print(f'  初始化文件条目失败: {r.status_code if r else "None"}')
        return False
    with open(pdf_path, 'rb') as f:
        r = api('PUT', f'/records/{new_id}/draft/files/{qname}/content',
                data=f, headers={'Content-Type': 'application/octet-stream'})
    if not r or r.status_code not in (200, 201):
        print(f'  内容上传失败: {r.status_code if r else "None"} {r.text[:150] if r else ""}')
        return False
    rc = api('POST', f'/records/{new_id}/draft/files/{qname}/commit')
    if not rc or rc.status_code not in (200, 201, 202):
        print(f'  commit 失败: {rc.status_code if rc else "None"} {rc.text[:150] if rc else ""}')
        return False
    return True


def update_record(rec_id, pdf_path, version='260808'):
    print(f'== 更新记录 {rec_id} <- {os.path.basename(pdf_path)}')
    # 1. 创建新版本
    r = api('POST', f'/records/{rec_id}/versions')
    if not r or r.status_code not in (200, 201):
        print(f'  !! 创建新版本失败，跳过')
        return False
    new_id = r.json()['id']
    print(f'  新版本 draft: {new_id}')
    # 2. 删除旧文件（new version 通常复制父文件）
    for f in get_draft_files(new_id):
        key = f['key']
        api('DELETE', f'/records/{new_id}/draft/files/{quote(key, safe="")}')
        print(f'  删除旧文件: {key}')
    # 3. 上传新 PDF
    if not upload_pdf(new_id, pdf_path):
        print('  !! 上传失败')
        return False
    print(f'  已上传: {os.path.basename(pdf_path)}')
    # 4. 更新 metadata（version）
    r = api('GET', f'/records/{new_id}/draft')
    if not r or r.status_code != 200:
        print('  !! 读取 draft 失败')
        return False
    md = r.json().get('metadata', {})
    md.pop('doi', None)
    md['version'] = version
    r = api('PUT', f'/records/{new_id}', json={'metadata': md})
    if not r or r.status_code not in (200, 201):
        print('  !! metadata 更新失败')
        return False
    print(f'  version -> {version}')
    # 5. 发布
    r = api('POST', f'/records/{new_id}/draft/actions/publish')
    if not r or r.status_code != 202:
        print('  !! 发布失败')
        return False
    print(f'  ✅ 已发布: {new_id} (concept {r.json().get("conceptrecid")})')
    return True


def extract_abstract(md_path):
    """从文章 md 提取摘要"""
    try:
        txt = open(md_path, encoding='utf-8').read()
    except Exception:
        return ''
    m = re.search(r'##\s*摘\s*要\s*\n(.*?)(?=\n##|\Z)', txt, re.S)
    if not m:
        m = re.search(r'摘要[:：]\s*\n?(.*?)(?=\n##|\Z)', txt, re.S)
    if not m:
        return ''
    return m.group(1).strip()[:1500]


def create_record(pdf_path, title):
    print(f'== 新建记录: {title} <- {os.path.basename(pdf_path)}')
    md = dict(TEMPLATE)
    md['title'] = title
    md['version'] = '260808'
    md['publication_date'] = '2026-08-08'
    abstract = extract_abstract(pdf_path.replace('.pdf', '.md').replace('/PDF/', '/ZH/'))
    # 若 ZH 目录不存在则尝试原目录同名 md
    if not abstract:
        alt = os.path.splitext(pdf_path)[0] + '.md'
        abstract = extract_abstract(alt)
    md['description'] = abstract or f'{title}（共扼谱几何系列，版本 260808）。'
    r = api('POST', '/records', json={'metadata': md})
    if not r or r.status_code not in (200, 201):
        print('  !! 创建失败')
        return False
    new_id = r.json()['id']
    print(f'  draft: {new_id}')
    if not upload_pdf(new_id, pdf_path):
        print('  !! 上传失败')
        return False
    r = api('POST', f'/records/{new_id}/draft/actions/publish')
    if not r or r.status_code != 202:
        print('  !! 发布失败')
        return False
    print(f'  ✅ 已发布: {new_id} (concept {r.json().get("conceptrecid")})')
    return True


def batch_update(map_file):
    items = json.load(open(map_file))
    ok = fail = 0
    for it in items:
        try:
            if update_record(it['id'], it['pdf']):
                ok += 1
            else:
                fail += 1
        except Exception as e:
            print('  异常:', e)
            fail += 1
        time.sleep(1)
    print(f'批量更新完成: 成功 {ok}, 失败 {fail}')


def batch_create(map_file):
    items = json.load(open(map_file))
    ok = fail = 0
    for it in items:
        try:
            if create_record(it['pdf'], it['title']):
                ok += 1
            else:
                fail += 1
        except Exception as e:
            print('  异常:', e)
            fail += 1
        time.sleep(1)
    print(f'批量新建完成: 成功 {ok}, 失败 {fail}')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'update':
        update_record(sys.argv[2], sys.argv[3])
    elif cmd == 'create':
        create_record(sys.argv[2], sys.argv[3])
    elif cmd == 'batch_update':
        batch_update(sys.argv[2])
    elif cmd == 'batch_create':
        batch_create(sys.argv[2])
    else:
        print(__doc__)
