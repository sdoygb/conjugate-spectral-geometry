#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看编辑器中被识别为公式的元素（data-math）内容"""
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

        # 找所有 data-math 元素的内容
        math_elems = await page.evaluate("""() => {
            const ed = document.querySelector('[contenteditable=true]');
            const out = [];
            if (!ed) return out;
            for (const m of ed.querySelectorAll('[data-math], [data-formula], [data-latex]')) {
                out.push({attr: m.getAttribute('data-math') || m.getAttribute('data-formula') || m.getAttribute('data-latex'),
                          text: m.innerText.slice(0, 100)});
            }
            // 也找 img 带 equation 的
            for (const img of ed.querySelectorAll('img[src*="equation"], img[src*="math"]')) {
                out.push({img: img.src.slice(0, 150)});
            }
            return out;
        }""")
        print('=== 被识别的公式元素 ===')
        for m in math_elems:
            print(' ', m)

        # 检查正文中 LaTeX 残留（\frac 等）
        text = await page.evaluate("""() => {
            const ed = document.querySelector('[contenteditable=true]');
            const t = ed ? ed.innerText : '';
            return {
                backslash: (t.match(/\\\\/g) || []).length,
                frac: (t.match(/frac/g) || []).length,
                sqrt: (t.match(/sqrt/g) || []).length,
                hat: (t.match(/hat/g) || []).length,
                sample: (t.match(/.{40}frac.{40}/) || ['无'])[0]
            };
        }""")
        print('=== LaTeX 残留统计 ===')
        print(text)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
