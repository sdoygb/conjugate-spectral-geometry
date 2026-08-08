#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump 编辑器 HTML，找公式被转换成的形态"""
import asyncio
from playwright.async_api import async_playwright

STATE = 'zhihu_publish/storage_state.json'

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(storage_state=STATE)
        page = await ctx.new_page()
        await page.goto('https://zhuanlan.zhihu.com/write', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(6000)
        await page.locator('button:has-text("导入")').first.click()
        await page.wait_for_timeout(2000)
        await page.locator('text=导入文档').first.click()
        await page.wait_for_timeout(1500)
        async with page.expect_file_chooser(timeout=10000) as fc_info:
            await page.locator('text=点击选择本地文档').first.click()
        fc = await fc_info.value
        await fc.set_files('app/articles/ZH/3.1_ℳ场法向几何结构_CN_260808.md')
        await page.wait_for_timeout(5000)

        html = await page.evaluate("""() => {
            const ed = document.querySelector('[contenteditable=true]');
            return ed ? ed.innerHTML : '';
        }""")
        print('HTML 总长:', len(html))

        # 找公式相关的标记：span 特殊 class、svg、math 相关
        import re
        # 找 "半径" 附近的 HTML
        for kw in ['半径', 'S', 'omega', 'math', 'svg', 'canvas']:
            idxs = [m.start() for m in re.finditer(kw, html)]
            print(f'关键字 {kw!r}: {len(idxs)} 处')
            if idxs and kw in ['半径', 'omega', 'math']:
                i = idxs[0]
                print('  片段:', html[max(0,i-200):i+300].replace(chr(10), ' ')[:500])

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
