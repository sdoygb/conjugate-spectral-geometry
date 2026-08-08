#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查知乎新建文章导入MD入口：+号 → 文章 → 导入 → 导入MD"""
import asyncio, json
from playwright.async_api import async_playwright

STATE = 'zhihu_publish/storage_state.json'

async def dump_clickables(page, label, max_items=40):
    """dump 页面上可见的可点击元素文本"""
    items = await page.evaluate("""() => {
        const out = [];
        const els = document.querySelectorAll('button, [role=button], a, [tabindex="0"], input[type=file]');
        for (const e of els) {
            const r = e.getBoundingClientRect();
            if (r.width < 2 || r.height < 2) continue;
            const txt = (e.innerText || e.value || e.placeholder || '').trim().slice(0, 60);
            const cls = String(e.className || '').slice(0, 80);
            out.push({tag: e.tagName, txt, cls, accept: e.accept || '', type: e.type || ''});
        }
        return out;
    }""")
    print(f'--- {label} ---')
    seen = set()
    for it in items:
        key = (it['tag'], it['txt'], it['cls'][:30])
        if key in seen: continue
        seen.add(key)
        print(f"  {it['tag']:<8} txt={it['txt']!r:<40} accept={it['accept']!r:<30} type={it['type']!r} cls={it['cls'][:40]}")
        if len(seen) >= max_items: break

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(storage_state=STATE)
        page = await ctx.new_page()
        # 1. 打开知乎主页
        await page.goto('https://www.zhihu.com', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)
        await dump_clickables(page, '知乎主页 可点击元素')

        # 2. 找 + 号按钮（发布入口）
        plus = None
        for sel in ['button:has-text("+")', '[aria-label*="发布"]', '[aria-label*="创作"]']:
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=2000):
                    plus = loc
                    print(f'[+] 找到发布按钮: {sel}')
                    break
            except Exception:
                pass
        if plus is None:
            # 全页找文本为 + 的元素
            try:
                plus = page.locator('text=+').first
                print('[+] 用 text=+ 找到')
            except Exception:
                print('[!] 未找到 + 按钮')
                await browser.close()
                return
        await plus.click()
        await page.wait_for_timeout(3000)
        await dump_clickables(page, '点击+号后')

        # 3. 找"文章"选项
        for sel in ['text=文章', 'button:has-text("文章")', '[role=button]:has-text("文章")']:
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=2000):
                    await loc.click()
                    print(f'[>] 点击文章: {sel}')
                    break
            except Exception:
                pass
        await page.wait_for_timeout(3000)
        await dump_clickables(page, '选文章后')

        # 4. 找"导入"
        for sel in ['text=导入', 'button:has-text("导入")', '[role=button]:has-text("导入")']:
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=2000):
                    await loc.click()
                    print(f'[>] 点击导入: {sel}')
                    break
            except Exception:
                pass
        await page.wait_for_timeout(3000)
        await dump_clickables(page, '选导入后')

        # 5. 找"导入MD"
        for sel in ['text=导入MD', 'text=MD', 'button:has-text("MD")']:
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=2000):
                    await loc.click()
                    print(f'[>] 点击导入MD: {sel}')
                    break
            except Exception:
                pass
        await page.wait_for_timeout(3000)
        await dump_clickables(page, '选导入MD后')

        # 6. 找文件输入框
        inputs = await page.locator('input[type=file]').all()
        print(f'[=] input[type=file] 数量: {len(inputs)}')
        for i, inp in enumerate(inputs):
            acc = await inp.get_attribute('accept')
            print(f'    input[{i}] accept={acc}')

        # 保存当前 URL 和页面文本片段
        print('[=] 当前URL:', page.url)
        body_text = await page.evaluate("() => document.body.innerText.slice(0, 1500)")
        print('--- 页面文本 ---')
        print(body_text)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
