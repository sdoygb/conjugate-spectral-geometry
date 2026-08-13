# -*- coding: utf-8 -*-
"""引用完整性审计：文章引用编号 vs 主库真理层清单
用法: python3 audit_citations.py <文章文件>
输出三类问题：未知编号 / 名称不匹配 / 正常
"""
import re, sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))
from master_client import MasterClient

# 1. 读文章
fn = sys.argv[1]
txt = open(fn, encoding='utf-8').read()

# 2. 提取引用：类型+编号（可带名称），支持字母后缀（推论 3.1.6.03a/b）
CITE_RE = re.compile(
    r'(定理|命题|引理|推论|原理|公理|定义)\s*'
    r'([0-9]+(?:\.[0-9]+){1,3}[a-z]?)'
    r'\s*(?:（([^）]{1,60})）)?'
)
cites = [(m.group(1), m.group(2), m.group(3)) for m in CITE_RE.finditer(txt)]

# 3. 主库清单
c = MasterClient()
truth = c.fetch_truth(force=True)
master = {}  # num -> (type, name, formula_name)
for t in truth:
    fname = t.get('formula_name', '') or ''
    m = re.match(
        r'^(定理|命题|引理|推论|原理|公理|定义)\s*'
        r'([0-9]+(?:\.[0-9]+){1,3}[a-z]?)\s*（([^）]+)）', fname)
    if m:
        master[m.group(2)] = (m.group(1), m.group(3), fname)

# 4. 比对
unknown, mismatch, ok = [], [], []
seen = set()
for ftype, num, name in cites:
    if num in seen:
        continue
    seen.add(num)
    if num not in master:
        unknown.append((ftype, num, name))
    else:
        mtype, mname, mfname = master[num]
        if name and mname and name != mname:
            mismatch.append((ftype, num, name, mname))
        else:
            ok.append((ftype, num, name))

# 5. 报告
print(f'=== 引用审计: {os.path.basename(fn)} ===')
print(f'主库真理层总数: {len(truth)} | 含编号条目: {len(master)}')
print(f'文章引用编号（去重）: {len(seen)}')
print(f'--- 未知编号（主库查不到）: {len(unknown)} ---')
for ftype, num, name in unknown:
    print(f'  ?? [{ftype} {num}]（{name or "无名称"}）')
print(f'--- 名称不匹配（E类嫌疑）: {len(mismatch)} ---')
for ftype, num, name, mname in mismatch:
    print(f'  !! [{ftype} {num}] 文章称"{name}" | 主库称"{mname}"')
print(f'--- 正常: {len(ok)} ---')
for ftype, num, name in ok:
    print(f'  OK [{ftype} {num}]（{name or ""}）')
