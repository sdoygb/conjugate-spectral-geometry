#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创作中心文章列表：查找 3.1 的发布状态"""
import os, time, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    page.goto('https://www.zhihu.com/creator/manage/creation/all', wait_until='domcontentloaded', timeout=30000)
    time.sleep(6)
    txt = page.evaluate("() => document.body.innerText")
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    hits = []
    for i, l in enumerate(lines):
        if '3.1' in l or '场法向' in l:
            hits.append(' | '.join(lines[max(0,i-3):i+3]))
    if hits:
        print('找到 3.1:')
        for h in hits[:5]:
            print(' >>', h[:200])
    else:
        print('未找到 3.1')
        print('--- 列表中的文章条目（含"_CN_260808"）---')
        for i, l in enumerate(lines):
            if 'CN_260808' in l or 'M5' in l or 'Birkhoff' in l:
                print(' >>', l[:150])
    browser.close()
