#!/usr/bin/env python3
"""测试新平台 token 权限 + 搜索用户已有记录"""
import os, json, requests

BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(BASE, ".zenodo_token")).read().strip()
H = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "Content-Type": "application/json"}

# 1. 测试 token：创建空草稿（不发布，随后删除）
print("=== 1. 测试创建草稿权限 ===")
try:
    r = requests.post("https://zenodo.org/api/records", headers=H, json={"metadata": {"title": "TEST-DRAFT-DELETE-ME", "upload_type": "publication", "publication_type": "preprint", "creators": [{"name": "Test, Test"}], "access_right": "open", "license": "cc-by-4.0"}}, timeout=30)
    print(f"HTTP {r.status_code}  {r.text[:300]}")
    if r.status_code in (200, 201):
        rid = r.json().get("id")
        print(f"草稿创建成功 id={rid}，测试后删除")
        # 删除草稿
        r2 = requests.delete(f"https://zenodo.org/api/records/{rid}/draft", headers=H, timeout=30)
        print(f"删除草稿: HTTP {r2.status_code}")
except Exception as e:
    print(f"ERROR {e}")

# 2. 搜索 conjugate spectral geometry 相关记录
print("\n=== 2. 搜索已有记录 ===")
for q in ["conjugate spectral geometry", "共轭谱几何"]:
    r = requests.get("https://zenodo.org/api/records", params={"q": f'title:"{q}"', "size": 5}, headers=H, timeout=30)
    if r.status_code == 200:
        hits = r.json().get("hits", {}).get("hits", [])
        print(f"q='{q}': {len(hits)} 条")
        for h in hits[:5]:
            md = h.get("metadata", {})
            print(f"  id={h['id']} concept={h.get('conceptrecid')} title={md.get('title','')[:60]} files={len(h.get('files',[]))}")
    else:
        print(f"q='{q}': HTTP {r.status_code} {r.text[:100]}")
