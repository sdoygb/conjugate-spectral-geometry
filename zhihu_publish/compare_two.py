#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比两篇 3.1 的公式形态：原生公式(data-tex) vs 图片公式(img)"""
import os, time
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN')
    page = ctx.new_page()
    for label, u in [
        ('测试篇(24分钟前)', 'https://zhuanlan.zhihu.com/p/2069447577104340542'),
        ('正式篇(3分钟前)', 'https://zhuanlan.zhihu.com/p/2069452947797414492'),
    ]:
        page.goto(u, wait_until='domcontentloaded', timeout=30000)
        time.sleep(5)
        stats = page.evaluate("""() => {
            const el = document.querySelector('.Post-RichText, .RichText, article, .Post-Main') || document.body;
            const html = el.innerHTML || '';
            return {
                tex: (html.match(/data-tex=/g) || []).length,       // 原生公式
                eq_img: (html.match(/zhihu.com\\/equation/g) || []).length, // 知乎公式图
                all_img: el.querySelectorAll('img').length,
                len: (el.innerText || '').length
            };
        }""")
        print(f'[{label}] {u}')
        print(f'   原生公式 data-tex: {stats["tex"]} | 公式图片: {stats["eq_img"]} | 图片总数: {stats["all_img"]} | 正文长度: {stats["len"]}')
    browser.close()
