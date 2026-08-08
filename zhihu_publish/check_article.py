#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证知乎文章是否公开可访问（无头模式，不带登录态）"""
import sys, time
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else 'https://zhuanlan.zhihu.com/p/2069446836256092706'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        locale='zh-CN',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/126.0.0.0 Safari/537.36',
    )
    page = ctx.new_page()
    page.goto(url, wait_until='domcontentloaded', timeout=30000)
    time.sleep(3)
    print('最终URL:', page.url)
    print('标题:', page.title())
    # 抓正文开头文本
    txt = page.evaluate("() => document.body ? document.body.innerText.slice(0, 500) : ''")
    print('正文开头:', txt.replace('\n', ' | ')[:500])
    browser.close()
