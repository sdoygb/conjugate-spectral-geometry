#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证导入质量：公式/表格/引用/代码块在编辑器中的形态"""
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

        # 导入
        await page.locator('button:has-text("导入")').first.click()
        await page.wait_for_timeout(2000)
        await page.locator('text=导入文档').first.click()
        await page.wait_for_timeout(1500)

        async with page.expect_file_chooser(timeout=10000) as fc_info:
            await page.locator('text=点击选择本地文档').first.click()
        fc = await fc_info.value
        await fc.set_files('app/articles/ZH/3.1_ℳ场法向几何结构_CN_260808.md')
        await page.wait_for_timeout(5000)

        # 编辑器全文分析
        info = await page.evaluate("""() => {
            const ed = document.querySelector('[contenteditable=true]');
            if (!ed) return null;
            const html = ed.innerHTML;
            const text = ed.innerText;
            return {
                len: text.length,
                h2: (html.match(/<h2/g) || []).length,
                h3: (html.match(/<h3/g) || []).length,
                h4: (html.match(/<h4/g) || []).length,
                math_spans: (html.match(/data-math/g) || []).length,
                img: (html.match(/<img/g) || []).length,
                table: (html.match(/<table/g) || []).length,
                blockquote: (html.match(/<blockquote/g) || []).length,
                code: (html.match(/<pre/g) || []).length,
                strong: (html.match(/<strong/g) || []).length,
                dollar_remain: (text.match(/\\$/g) || []).length,
                text_preview: text.slice(0, 600)
            };
        }""")
        print('=== 导入后编辑器结构 ===')
        for k, v in info.items():
            print(f'  {k}: {v}')

        # 找一处公式的 HTML 形态
        math_sample = await page.evaluate("""() => {
            const ed = document.querySelector('[contenteditable=true]');
            const m = ed.querySelector('[data-math], img[src*="equation"]');
            return m ? m.outerHTML.slice(0, 400) : '无公式元素';
        }""")
        print('公式元素示例:', math_sample)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
