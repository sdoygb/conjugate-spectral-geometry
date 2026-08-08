#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确认粗体/块级公式/表格在导入后的形态"""
import asyncio, re
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

        stats = {
            'data-tex(公式总数)': len(re.findall(r'data-tex=', html)),
            '块级公式(math/tex;mode=display)': len(re.findall(r'mode=display', html)),
            '行内公式(mode=inline)': len(re.findall(r'mode=inline', html)),
            'b/strong标签': len(re.findall(r'<b[ >]|<strong', html)),
            'table': len(re.findall(r'<table', html)),
            'blockquote': len(re.findall(r'<blockquote', html)),
            'h2': len(re.findall(r'<h2[ >]', html)),
            'h3': len(re.findall(r'<h3[ >]', html)),
            '引用粗体(定理...)': len(re.findall(r'定理 3\.1', html)),
        }
        print('=== 导入统计 ===')
        for k, v in stats.items():
            print(f'  {k}: {v}')

        # 块级公式示例
        i = html.find('mode=display')
        if i >= 0:
            print('块级公式片段:', html[max(0,i-150):i+150].replace(chr(10),' ')[:350])

        # 粗体示例（找"版本"附近）
        j = html.find('版本')
        if j >= 0:
            print('版本行片段:', html[max(0,j-100):j+200].replace(chr(10),' ')[:350])

        # 表格示例
        k = html.find('<table')
        if k >= 0:
            print('表格片段:', html[k:k+400].replace(chr(10),' ')[:450])

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
