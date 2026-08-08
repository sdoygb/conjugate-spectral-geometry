#!/usr/bin/env python3
"""诊断 Zenodo 新旧 API 端点"""
import os, requests

BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(BASE, ".zenodo_token")).read().strip()
H = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

tests = [
    ("旧deposit端点+UA", "GET", "https://zenodo.org/api/deposit/depositions", {"size": 1}),
    ("新records搜索(公开)", "GET", "https://zenodo.org/api/records", {"size": 1}),
    ("新user/records(带token)", "GET", "https://zenodo.org/api/user/records", {"size": 1}),
    ("新records带token", "GET", "https://zenodo.org/api/records", {"size": 1, "q": "access_right:open"}),
    ("API文档", "GET", "https://zenodo.org/api/", None),
]

for name, method, url, params in tests:
    try:
        r = requests.request(method, url, params=params, headers=H, timeout=30)
        body = r.text[:150].replace("\n", " ")
        print(f"[{name}] HTTP {r.status_code}  {body}")
    except Exception as e:
        print(f"[{name}] ERROR {e}")
