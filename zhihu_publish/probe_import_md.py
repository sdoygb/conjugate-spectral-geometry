#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精细探查写作页 导入 按钮的 Modal：完整文本 + tab + 上传md后的按钮变化"""
import asyncio
from playwright.async_api import async_playwright

STATE = 'zhihu_publish/storage_state.json'

async def full_text(page, sel, label):
    try:
        txt = await page.evaluate("""(sel) => {
            const el = document.querySelector(sel);
            return el ? el.innerText : null;
        }""", sel)
        print(f'--- {label} 完整文本 ---')
        print(txt)
    except Exception as e:
        print(f'--- {label} 错误: {e}')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(storage_state=STATE)
        page = await ctx.new_page()
        await page.goto('https://zhuanlan.zhihu.com/write', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(6000)

        # 点击工具栏 导入
        imp = page.locator('button:has-text("导入")').first
        await imp.click()
        await page.wait_for_timeout(2000)

        # dump Modal 完整文本
        modal_info = await page.evaluate("""() => {
            const modals = document.querySelectorAll('[class*=Modal], [class*=modal], [class*=Dialog], [role=dialog]');
            const out = [];
            for (const m of modals) {
                const r = m.getBoundingClientRect();
                if (r.width < 100) continue;
                out.push({cls: String(m.className).slice(0, 100), text: m.innerText.slice(0, 2000)});
            }
            return out;
        }""")
        print('=== Modal 列表 ===')
        for m in modal_info:
            print('---', m['cls'])
            print(m['text'])

        # dump 所有 input[type=file] 的 accept
        inputs = await page.locator('input[type=file]').all()
        print(f'=== input[type=file]: {len(inputs)} ===')
        for i, inp in enumerate(inputs):
            acc = await inp.get_attribute('accept')
            print(f'  input[{i}] accept={acc}')

        # 上传 md 文件
        md_path = 'app/articles/ZH/3.1_ℳ场法向几何结构_CN_260808.md'
        for inp in inputs:
            acc = await inp.get_attribute('accept') or ''
            if '.md' in acc or '.txt' in acc:
                await inp.set_input_files(md_path)
                print(f'[>] 已上传到 input[{i}]: {md_path}')
                break
        else:
            # 没有匹配的，试第一个
            if inputs:
                await inputs[0].set_input_files(md_path)
                print('[>] 已上传到第一个 input')
            else:
                print('[!] 没有 file input')

        # 等待上传 + 解析
        for t in [2, 4, 8]:
            await page.wait_for_timeout(t * 1000)
            print(f'=== 上传后 {t}s ===')
            modal_info2 = await page.evaluate("""() => {
                const modals = document.querySelectorAll('[class*=Modal], [class*=modal], [class*=Dialog], [role=dialog]');
                const out = [];
                for (const m of modals) {
                    const r = m.getBoundingClientRect();
                    if (r.width < 100) continue;
                    out.push({cls: String(m.className).slice(0, 100), text: m.innerText.slice(0, 3000)});
                }
                return out;
            }""")
            for m in modal_info2:
                print('---', m['cls'])
                print(m['text'])
            # 找所有按钮文字
            btns = await page.evaluate("""() => {
                const out = [];
                for (const b of document.querySelectorAll('button, [role=button], div[tabindex="0"]')) {
                    const t = (b.innerText||'').trim();
                    if (t) out.push(t.slice(0, 40));
                }
                return [...new Set(out)];
            }""")
            print('  可见按钮文本:', btns)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
