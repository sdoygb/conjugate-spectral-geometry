#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查 CreationCard 的操作按钮（v3），不执行删除"""
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

    def card_buttons():
        return page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('[class*=CreationCard]').forEach(card => {
                const txt = card.innerText || '';
                if (!txt.includes('3.1')) return;
                const info = {title: txt.split('\\n')[0].slice(0,30)};
                const ops = [];
                card.querySelectorAll('button, [role=button], [aria-label], [class*=more i], [class*=More i]').forEach(e => {
                    const t = (e.innerText||'').trim().replace(/\\s+/g,' ');
                    const l = e.getAttribute('aria-label') || '';
                    const c = (e.className||'').toString().slice(0,40);
                    if (t || l) ops.push({t: t.slice(0,25), l: l.slice(0,25), c});
                });
                info.ops = ops;
                out.push(info);
            });
            return out;
        }""")

    print('--- 初始状态 ---')
    for c in card_buttons():
        print(c)

    # hover 第一张 3.1 卡片，再看
    try:
        cards = page.locator('[class*=CreationCard]')
        n = cards.count()
        print(f'卡片数: {n}')
        for i in range(n):
            t = cards.nth(i).inner_text()[:30].replace('\n', '|')
            print(f'  卡片[{i}]: {t}')
        # hover 包含 3.1 的卡片
        for i in range(n):
            if '3.1' in cards.nth(i).inner_text()[:60]:
                cards.nth(i).hover()
                time.sleep(1.5)
                print(f'--- hover 卡片[{i}] 后 ---')
                for c in card_buttons():
                    if c['title'].startswith('3.1'):
                        print(c)
                break
    except Exception as ex:
        print('hover 异常:', ex)
    browser.close()
