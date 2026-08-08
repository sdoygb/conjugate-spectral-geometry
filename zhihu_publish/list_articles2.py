#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出创作中心全部内容"""
import os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN')
    page = ctx.new_page()
    page.goto('https://www.zhihu.com/creator/manage/creation/all', wait_until='domcontentloaded')
    page.wait_for_timeout(5000)
    print('URL:', page.url)
    body = page.inner_text('body')
    print(body[:3000])
    browser.close()
