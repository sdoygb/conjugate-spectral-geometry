#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""侦察知乎写作页 DOM：标题框与编辑器结构"""
import os, time, json
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    page.goto('https://zhuanlan.zhihu.com/write', wait_until='domcontentloaded', timeout=30000)
    time.sleep(6)
    # 侦察所有 contenteditable / textarea / input
    info = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('[contenteditable], textarea, input').forEach(el => {
            const r = el.getBoundingClientRect();
            out.push({
                tag: el.tagName, ce: el.getAttribute('contenteditable'),
                cls: (el.className || '').toString().slice(0, 80),
                ph: el.getAttribute('placeholder') || el.getAttribute('data-placeholder') || '',
                w: Math.round(r.width), h: Math.round(r.height),
                txt: (el.innerText || el.value || '').slice(0, 60)
            });
        });
        return out;
    }""")
    for i, it in enumerate(info):
        print(i, json.dumps(it, ensure_ascii=False))
    # 找发布按钮
    btns = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('button').forEach(b => {
            const t = (b.innerText || '').trim();
            if (t) out.push(t.slice(0, 20));
        });
        return out;
    }""")
    print('按钮:', btns[:20])
    browser.close()
