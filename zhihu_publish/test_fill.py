#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""填充验证：标题 fill + 正文剪贴板粘贴，检查内容是否真正进入 Draft.js 状态"""
import os, sys, time, json
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from md2zhihu import convert
STATE_FILE = os.path.join(HERE, 'storage_state.json')

md_path = sys.argv[1] if len(sys.argv) > 1 else 'app/articles/ZH/3.1_ℳ场法向几何结构_CN_260808.md'
title, body = convert(md_path)
print('标题:', title)
print('HTML长度:', len(body))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    try:
        ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    except Exception as e:
        print('授权剪贴板失败:', e)
    page = ctx.new_page()
    page.goto('https://zhuanlan.zhihu.com/write', wait_until='domcontentloaded', timeout=30000)
    time.sleep(5)

    # 1. 标题
    ta = page.wait_for_selector('textarea.Input', timeout=15000)
    ta.fill(title)
    time.sleep(1)
    got_title = ta.input_value()
    print('标题填入验证:', repr(got_title[:40]), 'OK' if got_title == title else 'FAIL')

    # 2. 正文：剪贴板写入 HTML，粘贴到编辑器
    ok = page.evaluate("""async (html) => {
        const plain = html.replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ').trim();
        const item = new ClipboardItem({
            'text/html': new Blob([html], {type: 'text/html'}),
            'text/plain': new Blob([plain], {type: 'text/plain'})
        });
        await navigator.clipboard.write([item]);
        return true;
    }""", body)
    print('剪贴板写入:', ok)

    ed = page.wait_for_selector('.public-DraftEditor-content', timeout=15000)
    ed.click()
    time.sleep(1)
    page.keyboard.press('Meta+v')
    print('已粘贴，等待 Draft.js 处理…')
    # 轮询等待内容增长
    for i in range(30):
        time.sleep(2)
        n = page.evaluate("() => document.querySelector('.public-DraftEditor-content').innerText.length")
        imgs = page.evaluate("() => document.querySelectorAll('.public-DraftEditor-content img').length")
        print(f'  [{i*2}s] 文本长度={n} 图片数={imgs}')
        if n > 5000:
            break
    browser.close()
