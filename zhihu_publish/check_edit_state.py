#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查3.1编辑页的发布状态"""
import os, time
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    page.goto('https://zhuanlan.zhihu.com/p/2069446836256092706/edit', wait_until='domcontentloaded', timeout=30000)
    time.sleep(6)
    print('URL:', page.url)
    print('标题:', page.title())
    txt = page.evaluate("() => document.body ? document.body.innerText : ''")
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    # 找发布相关按钮/状态
    for i, l in enumerate(lines[:60]):
        print(i, '|', l[:120])
    browser.close()
