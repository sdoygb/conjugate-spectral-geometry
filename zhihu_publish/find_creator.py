#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打开知乎创作中心，找文章列表入口"""
import json, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN')
    page = ctx.new_page()
    page.goto('https://zhuanlan.zhihu.com/', wait_until='domcontentloaded')
    page.wait_for_timeout(4000)
    print('URL:', page.url)
    # 找文章/内容管理入口
    links = page.eval_on_selector_all('a', 'els => els.map(e => e.innerText.trim() + " => " + e.href).filter(s => s.length > 5)')
    for l in links:
        if any(k in l for k in ['文章', '创作', '管理', '内容', '专栏', '我的']):
            print('LINK:', l[:120])
    # 页面可见按钮
    btns = page.eval_on_selector_all('button', 'els => els.map(e => e.innerText.trim()).filter(t => t && t.length < 20)')
    print('BUTTONS:', [b for b in btns][:30])
    browser.close()
