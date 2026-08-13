# 补录 126 个真遗漏：从定义处提取内容，DIRECT_PROMOTE 提交
import re, os, sys, time, json
sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/app')
from master_client import MasterClient

ART = '/Users/oygb/Downloads/GeometryAI-Mac-Build/app/articles'

# 从 missing_all.txt 重新生成定义处清单（与分类逻辑一致）
lines = [l.strip() for l in open('/tmp/missing_all.txt') if l.strip()]
cands = {}
for l in lines:
    ftype, num, name, fn, ln = l.split('|')
    if '_B站' in fn: continue
    cands.setdefault(num, []).append((ftype, name, fn, int(ln)))

def home_prefix(num):
    parts = num.split('.')
    return '.'.join(parts[:2]) + '_' if len(parts) >= 2 else None

todo = []
for num, v in sorted(cands.items()):
    home = home_prefix(num)
    defs = [x for x in v if home and x[2].startswith(home)]
    if defs:
        todo.append((num, defs[0]))

print(f'待补录: {len(todo)}', file=sys.stderr)

# 预加载所需文件
files_needed = set(x[1][2] for x in todo)
texts = {}
for fn in files_needed:
    p = os.path.join(ART, fn)
    try:
        texts[fn] = open(p, encoding='utf-8').read()
    except Exception as e:
        print(f'读取失败 {fn}: {e}', file=sys.stderr)

def extract(fn, ln):
    lines = texts.get(fn, '').split('\n')
    start = max(0, ln - 1)
    seg = '\n'.join(lines[start:start + 6])
    seg = re.sub(r'[#*`|>]', '', seg)
    seg = re.sub(r'\s+', ' ', seg).strip()
    return seg[:400]

# 断点续传
done = set()
if os.path.exists('/tmp/fill_done.txt'):
    done = set(l.strip() for l in open('/tmp/fill_done.txt'))
todo = [x for x in todo if x[0] not in done]
print(f'实际执行: {len(todo)}', file=sys.stderr)

c = MasterClient()
ok, fail = [], []
for i, (num, (ftype, name, fn, ln)) in enumerate(todo):
    content = extract(fn, ln)
    fname = f'{ftype} {num}' + (f'（{name}）' if name else '')
    try:
        resp = c.submit_formula(
            formula_name=fname,
            formula_content=content,
            derivation_chain=f'来源：文章库 {fn} 定义处（行 {ln}）。全量入库补录。',
            topology_class='A0',
        )
        st = resp.get('status', '?')
        print(f'[{i}/{len(todo)}] {num} -> {st}', file=sys.stderr)
        if st == 'promoted':
            ok.append(num)
            with open('/tmp/fill_done.txt', 'a') as f:
                f.write(num + '\n')
        else:
            fail.append((num, st, resp.get('message', '')[:60]))
    except Exception as e:
        print(f'[{i}/{len(todo)}] {num} EXC {e}', file=sys.stderr)
        fail.append((num, 'EXC', str(e)[:60]))
    time.sleep(0.15)

print(f'完成: {len(ok)} 成功, {len(fail)} 失败', file=sys.stderr)
for f in fail:
    print('FAIL:', f, file=sys.stderr)
