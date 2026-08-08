#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""登录态打开文章页，验证发布内容与公式渲染"""
import os, time, sys, json
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')
url = sys.argv[1] if len(sys.argv) > 1 else 'https://zhuanlan.zhihu.com/p/2069447577104340542'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    page.goto(url, wait_until='domcontentloaded', timeout=30000)
    time.sleep(6)
    print('最终URL:', page.url)
    print('页面标题:', page.title())
    txt = page.evaluate("() => document.querySelector('.Post-RichText, .RichText, article, .Post-Main') ? (document.querySelector('.Post-RichText, .RichText, article, .Post-Main').innerText || '').slice(0, 800) : (document.body.innerText || '').slice(0, 400)")
    print('正文开头:', txt.replace('\n', ' | ')[:600])
    imgs = page.evaluate("() => { const el = document.querySelector('.Post-RichText, .RichText, article'); return el ? el.querySelectorAll('img').length : 0; }")
    print('公式图片数:', imgs)
    browser.close()
