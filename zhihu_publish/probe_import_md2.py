#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正确流程探查：导入按钮 → 导入文档tab → 上传md → 选中 → 导入 → 验证编辑器"""
import asyncio
from playwright.async_api import async_playwright

STATE = 'zhihu_publish/storage_state.json'

async def dump_modal(page, label):
    info = await page.evaluate("""() => {
        const modals = document.querySelectorAll('[class*=Modal]');
        const out = [];
        for (const m of modals) {
            const r = m.getBoundingClientRect();
            if (r.width < 100) continue;
            out.push(m.innerText.slice(0, 2500));
        }
        return out;
    }""")
    print(f'=== {label} ===')
    for t in info:
        print(t)
        print('---')

async def editor_len(page):
    return await page.evaluate("""() => {
        const ed = document.querySelector('[contenteditable=true]');
        return ed ? ed.innerText.length : -1;
    }""")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(storage_state=STATE)
        page = await ctx.new_page()
        await page.goto('https://zhuanlan.zhihu.com/write', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(6000)

        # 点导入
        await page.locator('button:has-text("导入")').first.click()
        await page.wait_for_timeout(2000)
        await dump_modal(page, '导入Modal打开')

        # 找"导入文档 MD/Doc" tab 并点击
        tab = page.locator('text=导入文档').first
        print('[=] 导入文档tab可见:', await tab.is_visible())
        await tab.click()
        await page.wait_for_timeout(1500)
        await dump_modal(page, '点击导入文档tab后')

        # 上传 md 到 input[0]（accept 含 .md）
        md_path = 'app/articles/ZH/3.1_ℳ场法向几何结构_CN_260808.md'
        inputs = await page.locator('input[type=file]').all()
        print(f'[=] file inputs: {len(inputs)}')
        target = None
        for inp in inputs:
            acc = await inp.get_attribute('accept') or ''
            if '.md' in acc:
                target = inp
                break
        if target is None:
            target = inputs[0]
        await target.set_input_files(md_path)
        print('[>] 已上传 md')

        for t in [2, 4]:
            await page.wait_for_timeout(t * 1000)
            await dump_modal(page, f'上传后{t}s')

        # 点击文件行（选中）——真实点击
        file_row = page.locator('div[tabindex="0"]:has-text(".md")').first
        if await file_row.count() > 0:
            await file_row.click()
            print('[>] 点击文件行')
        else:
            # 找含文件名的行
            file_row = page.locator(f'text={md_path.split("/")[-1]}').first
            await file_row.click()
            print('[>] 点击文件名')
        await page.wait_for_timeout(1500)
        await dump_modal(page, '选中文件后')

        # dump 按钮文字
        btns = await page.evaluate("""() => {
            const out = [];
            for (const b of document.querySelectorAll('button, [role=button], div[tabindex="0"]')) {
                const t = (b.innerText||'').trim().replace(/\\u200b/g,'');
                if (t && t.length < 30) out.push(t);
            }
            return [...new Set(out)];
        }""")
        print('可见按钮:', btns)

        # 找导入按钮（文本含"导入"且不是 tab）
        imp_btn = None
        for b in await page.locator('button:has-text("导入"), div[tabindex="0"]:has-text("导入")').all():
            txt = (await b.inner_text()).strip()
            if 'MD' in txt or '导入文档' in txt:
                continue
            imp_btn = b
            break
        if imp_btn is not None:
            print('[>] 点击导入按钮:', repr(await imp_btn.inner_text()))
            await imp_btn.click()
            await page.wait_for_timeout(5000)
            await dump_modal(page, '点击导入后')
            print('[=] 编辑器长度:', await editor_len(page))
            # 标题
            title = await page.locator('textarea').first.input_value()
            print('[=] 标题:', repr(title))
        else:
            print('[!] 未找到导入按钮')

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
