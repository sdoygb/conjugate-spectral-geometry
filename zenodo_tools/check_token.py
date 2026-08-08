#!/usr/bin/env python3
"""Zenodo API token 验证脚本 v2"""
import json, os, sys
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(BASE, ".zenodo_token")).read().strip()
API = "https://zenodo.org/api/deposit/depositions"

r = requests.get(API, params={"size": 3}, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30)
print(f"HTTP {r.status_code}")
if r.status_code != 200:
    print(r.text[:500])
    sys.exit(1)

data = r.json()
print(f"OK: 返回 {len(data)} 条记录，token 有效")
for d in data:
    print(f"  id={d['id']}  conceptrecid={d.get('conceptrecid')}  state={d.get('state')}  files={len(d.get('files', []))}  title={d['metadata'].get('title','')[:50]}")
