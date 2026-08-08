#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用登录态验证知乎文章发布状态：查询创作中心文章列表"""
import os, sys, time, json
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        storage_state=STATE_FILE,
        locale='zh-CN',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/126.0.0.0 Safari/537.36',
    )
    page = ctx.new_page()
    page.goto('https://www.zhihu.com/creator/manage/creation/all', wait_until='domcontentloaded', timeout=30000)
    time.sleep(5)
    print('URL:', page.url)
    print('标题:', page.title())
    txt = page.evaluate("() => document.body ? document.body.innerText : ''")
    # 找文章列表中的 3.1 和状态信息
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    for i, l in enumerate(lines):
        if '3.1' in l or '场法向' in l:
            print('>>', ' | '.join(lines[max(0,i-2):i+4]))
    print('--- 前40行 ---')
    print(' | '.join(lines[:40]))
    browser.close()
