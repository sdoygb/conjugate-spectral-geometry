#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查知乎 playground/zhihu-publisher 页面内容"""
import os, time, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN',
                              user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    page.goto('https://www.zhihu.com/playground/zhihu-publisher', wait_until='domcontentloaded', timeout=60000)
    time.sleep(6)
    print('URL:', page.url)
    print('TITLE:', page.title())
    # 页面可见文本
    txt = page.evaluate("() => document.body.innerText")
    print('=== 页面文本 (前 4000 字符) ===')
    print(txt[:4000])
    # 所有链接
    links = page.evaluate("""() => Array.from(document.querySelectorAll('a')).map(a => (a.innerText||'').trim() + ' => ' + a.href).filter(s => s.length > 3).slice(0, 40)""")
    print('=== 链接 ===')
    for l in links:
        print(' ', l)
    # 按钮
    btns = page.evaluate("""() => Array.from(document.querySelectorAll('button')).map(b => (b.innerText||'').trim().replace(/\\s+/g,' ')).filter(t => t).slice(0, 30)""")
    print('=== 按钮 ===', btns)
    browser.close()
