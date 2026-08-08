#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查 zhihu-publisher 三个按钮：申请加入/下载skill/登录授权"""
import os, time, re
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN',
                              user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    page.goto('https://www.zhihu.com/playground/zhihu-publisher', wait_until='domcontentloaded', timeout=60000)
    time.sleep(5)

    # 1. 找所有按钮的 href/onclick/data 属性（可能是 a 标签伪装）
    info = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('button, a, [role=button]').forEach(e => {
            const t = (e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,40);
            if (/申请|skill|授权|下载|测试|登录/.test(t)) {
                out.push({
                    tag: e.tagName, text: t,
                    href: e.getAttribute('href') || '',
                    onclick: e.getAttribute('onclick') || '',
                    cls: (e.className||'').toString().slice(0,60),
                    aria: e.getAttribute('aria-label') || ''
                });
            }
        });
        return out;
    }""")
    print('=== 相关按钮/链接 ===')
    for i in info:
        print(' ', i)

    # 2. 检查页面内嵌 JS/API 端点
    scripts = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('script[src]').forEach(s => out.push(s.src));
        return out.slice(0, 20);
    }""")
    print('=== scripts ===')
    for s in scripts: print(' ', s)

    # 3. 尝试点击"打开登录授权页"看跳转 URL
    try:
        with page.expect_popup(timeout=8000) as popup_info:
            page.click('text=打开登录授权页')
        pop = popup_info.value
        pop.wait_for_load_state('domcontentloaded', timeout=15000)
        time.sleep(3)
        print('=== 授权页 URL ===', pop.url)
        print('=== 授权页文本 ===', pop.evaluate("() => document.body.innerText")[:1500])
        pop.close()
    except Exception as e:
        print('授权页点击异常:', e)

    # 4. 点击"下载 skill"看下载行为
    try:
        with page.expect_download(timeout=10000) as dl_info:
            page.click('text=下载 skill')
        dl = dl_info.value
        print('=== 下载 ===', dl.suggested_filename, dl.url)
        dl.save_as(os.path.join(HERE, dl.suggested_filename))
        print('已保存:', dl.suggested_filename)
    except Exception as e:
        print('下载异常:', e)

    # 5. 点击"申请加入"看反馈
    try:
        page.click('text=申请加入')
        time.sleep(4)
        print('=== 申请后页面文本 ===')
        print(page.evaluate("() => document.body.innerText")[:2000])
    except Exception as e:
        print('申请点击异常:', e)

    browser.close()
