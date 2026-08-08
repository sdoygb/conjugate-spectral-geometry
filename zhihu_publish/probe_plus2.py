#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查创作中心 + 号 → 文章 → 导入 → 导入MD"""
import asyncio
from playwright.async_api import async_playwright

STATE = 'zhihu_publish/storage_state.json'

async def dump_clickables(page, label, max_items=50):
    items = await page.evaluate("""() => {
        const out = [];
        const els = document.querySelectorAll('button, [role=button], a, [tabindex="0"], input[type=file]');
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

async def try_click(page, selectors, label):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=1500):
                await loc.click()
                print(f'[>] {label}: {sel}')
                return True
        except Exception:
            pass
    print(f'[!] {label}: 未找到 {selectors}')
    return False

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(storage_state=STATE)
        page = await ctx.new_page()
        # 创作中心主页
        await page.goto('https://zhuanlan.zhihu.com', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(6000)
        print('[=] URL:', page.url)
        await dump_clickables(page, '创作中心主页')

        # 找 + 号
        found = await try_click(page, [
            'button:has-text("+")', '[class*="plus"]', '[class*="Plus"]',
            '[class*="create"]', '[class*="Create"]', 'text=写文章',
        ], '点击+号')
        if not found:
            # 尝试所有文本为 + 或含新建语义的元素
            for sel in ['text=+', '[aria-label="新建"]', '[aria-label="创建"]']:
                try:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=1500):
                        await loc.click()
                        print(f'[>] 点击: {sel}')
                        found = True
                        break
                except Exception:
                    pass
        await page.wait_for_timeout(3000)
        await dump_clickables(page, '点击+号后')

        # 选 文章
        await try_click(page, ['text=文章', 'button:has-text("文章")', '[role=button]:has-text("文章")'], '选文章')
        await page.wait_for_timeout(3000)
        await dump_clickables(page, '选文章后')

        # 选 导入
        await try_click(page, ['text=导入', 'button:has-text("导入")'], '选导入')
        await page.wait_for_timeout(3000)
        await dump_clickables(page, '选导入后')

        # 选 导入MD
        await try_click(page, ['text=导入MD', 'text=MD', 'button:has-text("MD")'], '选导入MD')
        await page.wait_for_timeout(3000)
        await dump_clickables(page, '选导入MD后')

        # 文件输入
        inputs = await page.locator('input[type=file]').all()
        print(f'[=] input[type=file] 数量: {len(inputs)}')
        for i, inp in enumerate(inputs):
            acc = await inp.get_attribute('accept')
            vis = await inp.is_visible()
            print(f'    input[{i}] accept={acc} visible={vis}')

        print('[=] 最终URL:', page.url)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
