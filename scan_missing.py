#!/usr/bin/env python3
# 精确扫描：检测所有文章的"定义处"（标题/加粗/表格样式），与主库比对输出遗漏
import os, re, sys

sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/app')
from master_client import MasterClient

ROOT = '/Users/oygb/Downloads/GeometryAI-Mac-Build'
art_dir = os.path.join(ROOT, 'app/articles')

# 1. 文章列表 -> 前缀集合
prefixes = set()
for fn in os.listdir(art_dir):
    if fn.endswith('.md'):
        m = re.match(r'^([0-9]+(?:\.[0-9]+)+)_', fn)
        if m:
            prefixes.add(m.group(1))
print('文章前缀数:', len(prefixes))

# 2. 扫描所有文章的定义处
defs = {}  # num -> (ftype, filename, snippet)
pat_def = re.compile(
    r'(?:^#{1,4}\s*|\*\*|\|\s*\*\*|\|\s*)'   # 定义样式前缀：标题/加粗/表格
    r'(定理|命题|引理|推论|原理|公理|定义)\s*'
    r'([0-9]+\.[0-9]+(?:\.[0-9]+){1,2}[a-z]?)\s*[。）]'
)
for fn in sorted(os.listdir(art_dir)):
    if not fn.endswith('.md'):
        continue
    txt = open(os.path.join(art_dir, fn), encoding='utf-8').read()
    for m in pat_def.finditer(txt):
        ftype, num = m.group(1), m.group(2)
        xy = '.'.join(num.split('.')[:2])
        if xy not in prefixes:
            continue
        if num not in defs:
            seg = txt[m.end():m.end() + 500]
            seg = re.sub(r'[#*`>|]', '', seg)
            seg = re.sub(r'\s+', ' ', seg).strip()[:300]
            defs[num] = (ftype, fn, seg)
print('定义处编号总数:', len(defs))

# 3. 主库已有编号
c = MasterClient()
truth = c.fetch_truth(force=True)
master_nums = set()
for t in truth:
    m = re.match(r'^(定理|命题|引理|推论|原理|公理|定义)\s*([0-9]+\.[0-9]+(?:\.[0-9]+){1,2}[a-z]?)\s*[（。]',
                 t.get('formula_name', ''))
    if m:
        master_nums.add(m.group(2))
print('主库编号条目:', len(master_nums))

# 4. 差集
missing = {k: v for k, v in defs.items() if k not in master_nums}
print('=== 遗漏（定义处但主库无）:', len(missing), '===')
for num in sorted(missing, key=lambda s: [int(x) for x in re.split(r'\.', s) if x.isdigit()]):
    ftype, fn, seg = missing[num]
    print(f'{ftype} {num} | {fn} | {seg[:90]}')

# 保存遗漏清单
with open('/Users/oygb/Downloads/GeometryAI-Mac-Build/missing_list.txt', 'w', encoding='utf-8') as f:
    for num in sorted(missing, key=lambda s: [int(x) for x in re.split(r'\.', s) if x.isdigit()]):
        ftype, fn, seg = missing[num]
        f.write(f'{ftype}|{num}|{fn}|{seg[:300]}\n')
print('已保存 missing_list.txt')
