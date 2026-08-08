#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出知乎账号的文章（标题、URL、发布时间、状态）"""
import json, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN')
    page = ctx.new_page()
    # 创作中心 API：文章列表
    resp = page.goto('https://zhuanlan.zhihu.com/api/me/articles?page=1&limit=20', wait_until='domcontentloaded')
    try:
        data = resp.json()
        arts = data.get('data', [])
        print(f'文章总数: {data.get("paging", {}).get("totals", len(arts))}')
        for a in arts:
            print(f'- [{a.get("state", "?")}] {a.get("title", "")}')
            print(f'    URL: https://zhuanlan.zhihu.com/p/{a.get("id")}  时间: {a.get("created", "")}')
    except Exception as e:
        print('API 解析失败:', e)
        print('URL:', page.url)
        print('BODY:', page.content()[:800])
    browser.close()
