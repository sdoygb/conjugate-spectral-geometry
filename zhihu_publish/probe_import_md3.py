#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确探查：导入文档tab → 文件选择器 → 上传 → 是否直接解析"""
import asyncio
from playwright.async_api import async_playwright

STATE = 'zhihu_publish/storage_state.json'

async def editor_info(page):
    return await page.evaluate("""() => {
        const ed = document.querySelector('[contenteditable=true]');
        const ta = document.querySelector('textarea');
        return {
            editor_len: ed ? ed.innerText.length : -1,
            editor_html: ed ? ed.innerHTML.slice(0, 300) : '',
            title: ta ? ta.value : ''
        };
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

        # 切"导入文档"tab
        await page.locator('text=导入文档').first.click()
        await page.wait_for_timeout(1500)

        # 点击"点击选择本地文档"区域，捕获文件选择器
        try:
            async with page.expect_file_chooser(timeout=10000) as fc_info:
                await page.locator('text=点击选择本地文档').first.click()
            fc = await fc_info.value
            print('[=] 文件选择器 input 属性:')
            el = fc.element
            print('    tag:', await el.evaluate('e => e.tagName'))
            print('    accept:', await el.evaluate('e => e.accept'))
            print('    multiple:', await el.evaluate('e => e.multiple'))
            # 用文件选择器上传
            md_path = 'app/articles/ZH/3.1_ℳ场法向几何结构_CN_260808.md'
            await fc.set_files(md_path)
            print('[>] 已通过文件选择器上传')
        except Exception as e:
            print('[!] expect_file_chooser 失败:', e)
            # 兜底：找 accept 含 md 的 input 上传
            inputs = await page.locator('input[type=file]').all()
            for inp in inputs:
                acc = await inp.get_attribute('accept') or ''
                print('    input accept:', acc)
                if '.md' in acc:
                    await inp.set_input_files('app/articles/ZH/3.1_ℳ场法向几何结构_CN_260808.md')
                    print('[>] 已上传到该 input')
                    break

        # 观察上传后的状态变化
        for t in [2, 4, 8]:
            await page.wait_for_timeout(t * 1000)
            # 只打印 Modal 文本和编辑器状态
            modals = await page.evaluate("""() => {
                const out = [];
                for (const m of document.querySelectorAll('[class*=Modal]')) {
                    const r = m.getBoundingClientRect();
                    if (r.width < 100) continue;
                    out.push(m.innerText.slice(0, 800));
                }
                return out;
            }""")
            print(f'=== {t}s: Modal数={len(modals)} ===')
            for m in modals:
                print('  |', m.replace(chr(10), ' / ')[:300])
            print('  编辑器:', await editor_info(page))

            # 如果出现"选择文件"对话框（含"请选择文件"），尝试点文件行
            if any('请选择文件' in m for m in modals):
                # 点文件行（文件名）
                fn = '3.1_ℳ场法向几何结构_CN_260808.md'
                rows = page.locator(f'[class*=Modal] div:has-text("{fn}")')
                cnt = await rows.count()
                print(f'  文件行数: {cnt}')
                for i in range(cnt):
                    try:
                        await rows.nth(i).click(timeout=2000)
                        print(f'  点击了文件行[{i}]')
                        await page.wait_for_timeout(1000)
                        break
                    except Exception as e:
                        print(f'  文件行[{i}]点击失败: {str(e)[:80]}')
                # 看按钮
                btns = await page.evaluate("""() => {
                    const out = [];
                    for (const b of document.querySelectorAll('[class*=Modal] button, [class*=Modal] [role=button], [class*=Modal] div[tabindex]')) {
                        const t = (b.innerText||'').trim().replace(/[\\u200b\\n]/g,'');
                        if (t) out.push(t.slice(0, 20));
                    }
                    return [...new Set(out)];
                }""")
                print('  Modal按钮:', btns)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
