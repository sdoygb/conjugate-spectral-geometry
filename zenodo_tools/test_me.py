#!/usr/bin/env python3
"""测试 token 的账号级端点"""
import os, requests

BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(BASE, ".zenodo_token")).read().strip()
H = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

tests = [
    ("/api/me", "https://zenodo.org/api/me"),
    ("/api/accounts/", "https://zenodo.org/api/accounts/"),
    ("/api/user/", "https://zenodo.org/api/user/"),
]

for name, url in tests:
    try:
        r = requests.get(url, headers=H, timeout=30)
        print(f"[{name}] HTTP {r.status_code}  {r.text[:250]}")
    except Exception as e:
        print(f"[{name}] ERROR {e}")
