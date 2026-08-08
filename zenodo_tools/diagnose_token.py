#!/usr/bin/env python3
"""诊断：对比有效/无效 token 的响应，判断 403 原因"""
import os, requests

BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(BASE, ".zenodo_token")).read().strip()
print(f"token 长度: {len(TOKEN)} 字符")

API = "https://zenodo.org/api/deposit/depositions"

# 1. 用户提供的 token
r1 = requests.get(API, params={"size": 1}, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30)
print(f"[用户token]  HTTP {r1.status_code}  body: {r1.text[:200]}")

# 2. 故意错误的 token
r2 = requests.get(API, params={"size": 1}, headers={"Authorization": "Bearer definitely_wrong_token_xyz"}, timeout=30)
print(f"[错误token]  HTTP {r2.status_code}  body: {r2.text[:200]}")

# 3. 无 token
r3 = requests.get(API, params={"size": 1}, timeout=30)
print(f"[无token]    HTTP {r3.status_code}  body: {r3.text[:200]}")

# 4. 检查用户 token 能否访问公开 API（不需要权限的）
r4 = requests.get("https://zenodo.org/api/records/12345", timeout=30)
print(f"[公开API]    HTTP {r4.status_code}")
