# 全库 vs 主库 差集扫描 v2
# 提取所有"类型+编号（名称）"或"类型+编号。"定义候选，与主库比对
import re, os, sys, json
sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/app')
from master_client import MasterClient

# 1. 主库编号集合
c = MasterClient()
truth = c.fetch_truth(force=True)
master = {}
for t in truth:
    fn = t.get('formula_name', '')
    m = re.match(r'^(定理|命题|引理|推论|原理|公理|定义)\s*([0-9]+(?:\.[0-9]+){1,3}[a-z]?)\s*（([^）]{1,50})）', fn)
    if m:
        master.setdefault(m.group(2), []).append((m.group(1), m.group(3)))
print(f'主库编号条目: {len(master)}', file=sys.stderr)

# 2. 全库文章
ART = '/Users/oygb/Downloads/GeometryAI-Mac-Build/app/articles'
files = []
for root, dirs, fs in os.walk(ART):
    if '/archive' in root or root.endswith('archive'):
        continue
    for f in fs:
        if f.endswith('.md'):
            files.append(os.path.join(root, f))

# 3. 提取定义候选：类型+编号（可能带括号名称）或 类型+编号。
pat_def = re.compile(r'(定理|命题|引理|推论|原理|公理|定义)\s*([0-9]+(?:\.[0-9]+){1,3}[a-z]?)(?:\s*（([^）]{1,60})）)?')
found = {}  # num -> [(ftype, name, file, lineno)]
for fn in files:
    try:
        txt = open(fn, encoding='utf-8').read()
    except Exception:
        continue
    for i, line in enumerate(txt.split('\n')):
        for m in pat_def.finditer(line):
            ftype, num, name = m.group(1), m.group(2), m.group(3)
            parts = num.split('.')
            if len(parts) < 3:
                continue  # 章内编号（1.0、2.1）不算
            try:
                x = int(parts[0])
            except Exception:
                continue
            if x > 10:
                continue  # 首段>10 不是卷号
            # 排除明显引用行（行内有"参见/见/引用/待/由"等？——不排除，靠人工筛选）
            found.setdefault(num, []).append((ftype, name, os.path.basename(fn), i + 1))

# 4. 差集
missing = {num: v for num, v in found.items() if num not in master}
print(f'全库定义候选: {len(found)}, 不在主库: {len(missing)}', file=sys.stderr)
with open('/tmp/missing_all.txt', 'w') as f:
    for num, v in sorted(missing.items()):
        for ftype, name, fn, ln in v:
            f.write(f'{ftype}|{num}|{name}|{fn}|{ln}\n')
print('saved /tmp/missing_all.txt', file=sys.stderr)
# 打印前 200 行
with open('/tmp/missing_all.txt') as f:
    lines = f.readlines()
for l in lines[:200]:
    print(l.rstrip())
