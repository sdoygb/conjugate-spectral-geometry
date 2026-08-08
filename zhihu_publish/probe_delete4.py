#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查 3.1 卡片的更多菜单（v4），不执行删除"""
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

    # 所有卡片：标题 + 时间 + 更多按钮
    info = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('[class*=CreationCard]').forEach(card => {
            const txt = (card.innerText || '').replace(/\\s+/g, ' ');
            if (!txt.includes('3.1')) return;
            // 找卡片内的"更多"按钮
            let moreBtn = null;
            card.querySelectorAll('button, [role=button]').forEach(e => {
                const t = (e.innerText||'').trim();
                if (t === '更多' || (e.getAttribute('aria-label')||'').includes('更多')) moreBtn = e;
            });
            out.push({txt: txt.slice(0, 120), hasMore: !!moreBtn});
        });
        return out;
    }""")
    for i, d in enumerate(info):
        print(f'3.1卡片[{i}]:', d['txt'][:100])
        print('   有更多按钮:', d['hasMore'])

    # 点击第一张 3.1 卡片的"更多"
    clicked = page.evaluate("""() => {
        const cards = document.querySelectorAll('[class*=CreationCard]');
        for (const card of cards) {
            const txt = (card.innerText || '').replace(/\\s+/g, ' ');
            if (!txt.includes('3.1')) continue;
            const btns = card.querySelectorAll('button, [role=button]');
            for (const e of btns) {
                const t = (e.innerText||'').trim();
                if (t === '更多' || (e.getAttribute('aria-label')||'').includes('更多')) {
                    e.click();
                    return true;
                }
            }
        }
        return false;
    }""")
    print('点击更多:', clicked)
    time.sleep(2)

    # dump 弹出的菜单
    menu = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('[class*=Menu], [class*=menu], [role=menuitem], [class*=Dropdown]').forEach(e => {
            const t = (e.innerText||'').trim().replace(/\\s+/g, ' ');
            if (t && t.length < 60) out.push(t);
        });
        return [...new Set(out)].slice(0, 30);
    }""")
    print('弹出菜单项:', menu)

    # 页面所有可见按钮（可能菜单是 popup）
    btns = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('button, [role=button]').forEach(e => {
            const t = (e.innerText||'').trim().replace(/\\s+/g, ' ');
            if (t && t.length < 25) out.push(t);
        });
        return [...new Set(out)].slice(-30);
    }""")
    print('页面按钮(尾部):', btns)
    browser.close()
