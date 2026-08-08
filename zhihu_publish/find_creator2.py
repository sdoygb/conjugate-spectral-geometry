#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打开知乎创作中心，找文章列表"""
import os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN')
    page = ctx.new_page()
    page.goto('https://www.zhihu.com/creator', wait_until='domcontentloaded')
    page.wait_for_timeout(5000)
    print('URL:', page.url)
    # 侧边栏菜单
    links = page.eval_on_selector_all('a', 'els => els.map(e => e.innerText.trim() + " => " + e.href).filter(s => s.length > 4 && (s.includes("zhihu.com") || s.includes("zhuanlan")))')
    seen = set()
    for l in links:
        if l not in seen:
            seen.add(l)
            print('LINK:', l[:130])
    # 页面正文找文章
    txt = page.inner_text('body')[:2000]
    print('---BODY---')
    print(txt)
    browser.close()
