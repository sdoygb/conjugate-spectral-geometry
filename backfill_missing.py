#!/usr/bin/env python3
# 补录 3 个真遗漏：8.3.2.02, 8.7.2.02, 8.7.2.03（9.1.2.08 废弃跳过）
import re, sys, os

sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/app')
from master_client import MasterClient

ROOT = '/Users/oygb/Downloads/GeometryAI-Mac-Build'
art_dir = os.path.join(ROOT, 'app/articles')

targets = [
    ('命题', '8.3.2.02', '8.3_暗能量证伪_CN_260808.md'),
    ('命题', '8.7.2.02', '8.7_CMB声学峰_CN_260808.md'),
    ('命题', '8.7.2.03', '8.7_CMB声学峰_CN_260808.md'),
]

def extract_def(fn, num):
    """提取定义处完整段落（到下一个 类型+编号 或 800 字符）"""
    txt = open(os.path.join(art_dir, fn), encoding='utf-8').read()
    # 定位定义处：加粗/标题 + 类型 + 编号 + 句号
    pat = re.compile(r'(?:^#{1,4}\s*|\*\*)(命题|定理|引理|推论|定义|公理|原理)\s*' + re.escape(num) + r'\s*[。）]')
    m = pat.search(txt)
    if not m:
        return None
    start = m.end()
    # 取到下一个同格式定义或 900 字符
    seg = txt[start:start + 900]
    # 截断到下一个 "**命题" / "### " / "证明。" 之后合理位置
    nxt = re.search(r'\n#{1,4}\s|\n\*\*(命题|定理|引理|推论)', seg)
    if nxt:
        seg = seg[:nxt.start()]
    seg = re.sub(r'[#*`>|]', '', seg)
    seg = re.sub(r'\s+', ' ', seg).strip()
    return seg[:600]

c = MasterClient()
for ftype, num, fn in targets:
    content = extract_def(fn, num)
    if not content:
        print(f'{num}: 提取失败!')
        continue
    name = f'{ftype} {num}'
    print(f'--- {name} ---')
    print(content[:200], '...')
    try:
        resp = c.submit_formula(
            formula_name=name,
            formula_content=content,
            derivation_chain=f'来源：{fn} 定义处（DIRECT_PROMOTE 补录）。',
            topology_class='A0',
        )
        print('提交返回:', resp.get('status'), resp.get('message', '')[:60])
    except Exception as e:
        print('提交异常:', str(e)[:100])
