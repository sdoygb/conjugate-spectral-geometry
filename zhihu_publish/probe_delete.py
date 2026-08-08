#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查创作中心文章列表的删除入口（不执行删除）"""
import os, time
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN')
    page = ctx.new_page()
    page.goto('https://www.zhihu.com/creator/manage/creation/all', wait_until='domcontentloaded')
    time.sleep(6)
    # 找文章行：找包含 "3.1" 的行
    rows = page.locator('div:has(> div > span:has-text("3.1"))').all()
    print('rows 匹配:', len(rows))
    # 更宽松：找所有含 "3.1" 的元素
    hits = page.locator('text=3.1').all()
    print('text=3.1 命中:', len(hits))
    for h in hits[:10]:
        tag = h.evaluate("e => e.tagName + '.' + (e.className||'').toString().slice(0,60)")
        txt = h.inner_text()[:40].replace('\n', '|')
        print(' ', tag, '|', txt)
    # 文章列表容器：常见 class 是 ContentList / ArticleItem
    for sel in ['.ContentList', '[class*="ArticleItem"]', '[class*="content-item"]', '[class*="ContentItem"]']:
        n = page.locator(sel).count()
        print(sel, '->', n)
    # hover 第一篇文章行看是否有操作按钮
    first = page.locator('[class*="ArticleItem"]').first
    if first.count():
        first.hover()
        time.sleep(1.5)
        btns = page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('button, [role=button], [class*=menu]').forEach(e => {
                const t = (e.innerText||'').trim();
                if (t && t.length < 20) out.push(t.replace(/\\n/g,'|'));
            });
            return [...new Set(out)].slice(0, 40);
        }""")
        print('hover后可见按钮:', btns)
    # 尝试点击行的"更多"（三点）
    page.screenshot(path=os.path.join(HERE, 'creator_list.png'))
    print('截图已存 creator_list.png')
    browser.close()
