#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""填充后细节验证：公式img、表格、标题层级、引用块"""
import os, time, json, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from md2zhihu import convert
STATE_FILE = os.path.join(HERE, 'storage_state.json')

md_path = sys.argv[1] if len(sys.argv) > 1 else 'app/articles/ZH/3.1_ℳ场法向几何结构_CN_260808.md'
title, body = convert(md_path)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    try:
        ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    except Exception:
        pass
    page = ctx.new_page()
    page.goto('https://zhuanlan.zhihu.com/write', wait_until='domcontentloaded', timeout=30000)
    time.sleep(5)
    page.wait_for_selector('textarea.Input', timeout=15000).fill(title)
    page.evaluate("""async (html) => {
        const plain = html.replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ').trim();
        await navigator.clipboard.write([new ClipboardItem({
            'text/html': new Blob([html], {type: 'text/html'}),
            'text/plain': new Blob([plain], {type: 'text/plain'})
        })]);
    }""", body)
    page.click('.public-DraftEditor-content')
    time.sleep(1)
    page.keyboard.press('Meta+v')
    time.sleep(6)

    detail = page.evaluate("""() => {
        const ed = document.querySelector('.public-DraftEditor-content');
        const out = {};
        out.img_src_prefix = {};
        ed.querySelectorAll('img').forEach(im => {
            const s = im.src.split('?')[0];
            out.img_src_prefix[s] = (out.img_src_prefix[s] || 0) + 1;
        });
        out.table_count = ed.querySelectorAll('table').length;
        out.blockquote_count = ed.querySelectorAll('blockquote').length;
        out.h2 = ed.querySelectorAll('h2, h3').length;
        // Draft 块类型统计（data-block 或 css class）
        out.blocks = {};
        ed.querySelectorAll('[data-block="true"]').forEach(b => {
            const cls = (b.className || '').split(' ').filter(c => c.includes('header') || c.includes('blockquote') || c.includes('list') || c.includes('code')).join(',');
            out.blocks[cls || 'plain'] = (out.blocks[cls || 'plain'] || 0) + 1;
        });
        return out;
    }""")
    print(json.dumps(detail, ensure_ascii=False, indent=1))
    browser.close()
