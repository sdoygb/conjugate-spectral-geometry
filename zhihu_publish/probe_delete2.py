#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查文章行的操作按钮（更多/删除入口），不执行删除"""
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

    # 找到 "3.1 ℳ场法向几何结构" 元素，向上找行容器
    el = page.locator('span:has-text("3.1 ℳ场法向几何结构")').first
    print('span 命中:', el.count())
    if el.count():
        # 向上找 5 层父级，打印每层 class
        info = el.evaluate("""e => {
            const out = [];
            let cur = e;
            for (let i = 0; i < 6 && cur; i++) {
                out.push({tag: cur.tagName, cls: (cur.className||'').toString().slice(0,80),
                          role: cur.getAttribute && cur.getAttribute('role'),
                          label: cur.getAttribute && cur.getAttribute('aria-label')});
                cur = cur.parentElement;
            }
            return out;
        }""")
        for i, d in enumerate(info):
            print(f'  L{i}: {d}')
        # 行容器 = L3 或 L4，dump 其内部按钮
        row = el.evaluate("e => { let c = e; for (let i=0;i<3;i++) c = c.parentElement; return c; }")
        btns = page.evaluate("""(row) => {
            const out = [];
            row.querySelectorAll('button, [role=button], [aria-label], [class*=more i], [class*=More i], [class*=opera i]').forEach(e => {
                const t = (e.innerText||'').trim().replace(/\\s+/g,' ');
                const l = e.getAttribute('aria-label') || '';
                const c = (e.className||'').toString().slice(0,50);
                if (t || l) out.push({t: t.slice(0,30), l: l.slice(0,30), c});
            });
            return out.slice(0, 30);
        }""", row)
        print('行内可操作元素:')
        for b in btns:
            print('  ', b)

        # hover 行后再次 dump
        try:
            page.locator('span:has-text("3.1 ℳ场法向几何结构")').first.hover()
            time.sleep(1.5)
            btns2 = page.evaluate("""(row) => {
                const out = [];
                row.querySelectorAll('button, [role=button], [aria-label]').forEach(e => {
                    const t = (e.innerText||'').trim().replace(/\\s+/g,' ');
                    const l = e.getAttribute('aria-label') || '';
                    if (t || l) out.push({t: t.slice(0,30), l: l.slice(0,30)});
                });
                return out.slice(0, 30);
            }""", row)
            print('hover后行内可操作元素:')
            for b in btns2:
                print('  ', b)
        except Exception as ex:
            print('hover 异常:', ex)
    browser.close()
