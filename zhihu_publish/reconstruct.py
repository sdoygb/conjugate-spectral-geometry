#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""还原发布记录：检查两个可疑 URL + 创作中心完整文章列表"""
import os, time
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')
URLS = [
    'https://zhuanlan.zhihu.com/p/2069446836256092706',
    'https://zhuanlan.zhihu.com/p/2069447577104340542',
    'https://zhuanlan.zhihu.com/p/2069452947797414492',
]

with sync_playwright() as p:
    # 1) 无登录态检查三个 URL 是否公开
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(locale='zh-CN',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    for u in URLS:
        try:
            page.goto(u, wait_until='domcontentloaded', timeout=25000)
            time.sleep(3)
            title = page.title()
            body = page.evaluate("() => (document.body.innerText || '').slice(0, 120).replace(/\\n/g, ' | ')")
            print(f'[匿名] {u}\n   -> URL={page.url} | 标题={title} | 正文: {body}')
        except Exception as e:
            print(f'[匿名] {u}\n   -> 异常: {type(e).__name__}: {str(e)[:100]}')
    browser.close()

    # 2) 登录态打开创作中心文章列表，提取标题+链接
    browser2 = p.chromium.launch(headless=True)
    ctx2 = browser2.new_context(storage_state=STATE_FILE, locale='zh-CN')
    page2 = ctx2.new_page()
    page2.goto('https://www.zhihu.com/creator/manage/creation/all', wait_until='domcontentloaded', timeout=30000)
    time.sleep(6)
    # 抓文章卡片：标题 + 时间
    arts = page2.evaluate("""() => {
        const out = [];
        document.querySelectorAll('a').forEach(a => {
            const t = (a.innerText || '').trim();
            const h = a.href || '';
            if (t && (h.includes('/p/') || h.includes('/answer/') || h.includes('/zhuanlan/')) && t.length < 60) {
                out.push(t + ' => ' + h);
            }
        });
        return out;
    }""")
    seen = set()
    for a in arts:
        if a not in seen:
            seen.add(a)
            print('[列表]', a[:120])
    body2 = page2.inner_text('body')
    # 找"发布于 X 分钟前"上下文
    lines = [l.strip() for l in body2.split('\n') if l.strip()]
    for i, l in enumerate(lines):
        if '发布于' in l:
            ctx_lines = lines[max(0,i-3):i+1]
            print('[时间线]', ' | '.join(ctx_lines)[:150])
    browser2.close()
