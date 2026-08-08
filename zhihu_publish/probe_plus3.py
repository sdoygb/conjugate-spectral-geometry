#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查：+号 → 写文章 → 导入 → 导入MD（监听新页面/对话框）"""
import asyncio
from playwright.async_api import async_playwright

STATE = 'zhihu_publish/storage_state.json'

async def dump_clickables(page, label, max_items=60):
    items = await page.evaluate("""() => {
        const out = [];
        const els = document.querySelectorAll('button, [role=button], a, [tabindex="0"], input[type=file], input, textarea');
        for (const e of els) {
            const r = e.getBoundingClientRect();
            if (r.width < 2 || r.height < 2) continue;
            const txt = (e.innerText || e.value || e.placeholder || '').trim().slice(0, 50);
            const cls = String(e.className || '').slice(0, 60);
            out.push({tag: e.tagName, txt, cls, accept: e.accept || '', type: e.type || ''});
        }
        return out;
    }""")
    print(f'--- {label} ---')
    seen = set()
    for it in items:
        key = (it['tag'], it['txt'], it['cls'][:20])
        if key in seen: continue
        seen.add(key)
        print(f"  {it['tag']:<8} txt={it['txt']!r:<40} accept={it['accept']!r:<28} type={it['type']!r}")
        if len(seen) >= max_items: break

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(storage_state=STATE)
        page = await ctx.new_page()

        # 监听新页面
        new_pages = []
        ctx.on('page', lambda pg: new_pages.append(pg))

        await page.goto('https://zhuanlan.zhihu.com', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(6000)

        # 点击 + 号
        plus = page.locator('[class*="Plus"]').first
        await plus.click()
        await page.wait_for_timeout(2500)
        print('[=] +号菜单已打开')

        # 点击 写文章
        btn = page.locator('button:has-text("写文章")').first
        print('[=] 写文章按钮可见:', await btn.is_visible())
        await btn.click()
        print('[>] 已点击写文章')
        await page.wait_for_timeout(5000)

        # 检查新页面
        print(f'[=] 新页面数量: {len(new_pages)}')
        for np in new_pages:
            print(f'   新页面URL: {np.url}')
        print('[=] 当前页URL:', page.url)

        # dump 当前页（可能弹出对话框）
        await dump_clickables(page, '点击写文章后')

        # 如果有新页面，dump 新页面
        for np in new_pages:
            await np.wait_for_timeout(4000)
            await dump_clickables(np, f'新页面 {np.url}')

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
