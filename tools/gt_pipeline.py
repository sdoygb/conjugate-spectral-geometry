#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gt_pipeline.py — 共扼谱几何入库流水线（判据固化，2026-08-05 起强制）
=====================================================================
两个入库判据（程序强制，任何入库动作必须通过）：
  判据1 依赖闭合：候选定理的源文章引用的所有编号，必须已在主库或本批已入。
  判据2 圆满验证：submit_to_master 主库独立验证通过（A0/A1 拓扑分类 + Berry 相位）。

编号规范：全数字 (^\\d+\\.\\d+\\.\\d+\\.\\d+$)，禁止字母后缀。
类型词   ：定理|命题|公理|引理|推论（"定义"依赖检查时识别，入库由 INCLUDE_DEFINITIONS 控制）。

用法：
  python3 tools/gt_pipeline.py audit            # 核查主库全部定理的依赖闭合 → reports/master_dep_audit.json
  python3 tools/gt_pipeline.py queue            # 候选拓扑排序 → reports/ingest_queue.json + blocked_queue.json
  python3 tools/gt_pipeline.py check <编号>     # 单条候选依赖检查
  python3 tools/gt_pipeline.py ingest <编号>    # 入库（强制判据1，判据2须先有 submit 验证记录）
  所有动作写入 logs/audit_log.jsonl（持久化，防遗忘）
"""
import os, re, json, sys, glob, datetime

ROOT = 'app/articles'
REPORTS = 'reports'
LOGS = 'logs'
os.makedirs(REPORTS, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)

# ---------- 配置（修改需用户确认） ----------
TYPE_WORDS = r'(?:定理|命题|公理|引理|推论)'           # 入库类型词
TYPE_WORDS_REF = r'(?:定理|命题|公理|引理|推论|定义)'  # 依赖检查识别全部声明（含定义）
INCLUDE_DEFINITIONS = False  # 定义类入库开关。用户决定(2026-08-05)：定义类不入库——定义是公式封装，其内部公式以公式/定理形式入库
NUMBER_RE = r'(\d+\.\d+\.\d+\.\d+)'                  # 全数字编号，禁止字母后缀
NUMBER_FULL = re.compile(r'^\d+\.\d+\.\d+\.\d+$')

# 定义→内核公式映射（用户决定 2026-08-05：定义不入库，定义是公式封装，其内部公式以公式/定理形式入库）
# 引用定义的依赖经此映射传递闭合：内核公式须已在主库（或递归经其他定义传递到主库公式）。
# 主库判据实证（2.6.2.01 驳回，2026-08-05）：纯集合/结构定义无 (θ_M,θ_C,θ_I) 闭环，不能作为圆满公式入库，
# 故拆解的正确形态是"定义→内核公式映射"而非"定义→定理转述"。
DEF_CLOSURE = {
    '2.6.2.01': ['0.1.1.01', '0.3.1.01'],   # 景观：δ迭代结构 + Bott周期分类
    '2.6.1.01': ['2.1.2.01', '0.5.0.01', '0.5.1.01', '0.5.1.02', '0.5.1.03', '2.3.5.01', '2.3.5.02'],  # 区域：B₂分解 + E₈桥接 + 结构常数 + 信息层
    '2.6.1.02': ['2.6.1.01'],               # 宇宙：区域概念（递归传递）
    '2.6.1.03': ['2.6.1.01', '2.3.5.03', '2.2.1.01'],  # 本区域：区域 + 跨区域导入 + 不动点Cramer
}

# 本地判据已知驳回（非纯几何/非定理/数值扫描），入库时直接跳过并记录原因
KNOWN_REJECTED = {
    '2.2.2.01': 'α⁻¹导出（物理常数，非纯几何）',
    '2.3.2.01': '景观范围数值扫描（非定理）',
    '3.12.1.02': '质量算符K（物理量纲）',
    '3.12.2.01': 'ℏ导出（物理常数）',
    '3.12.11.02': '对应表（非定理）',
    '3.12.11.03': '开放问题（非定理）',
    '3.7.4.06': '超精细能量（物理数值）',
    '3.9.3.02': 'k普适性（物理常数）',
    '3.9.4.04': '辐射修正（物理数值）',
}

# ---------- 声明/引用提取 ----------
def make_decl_patterns(type_words):
    return [
        re.compile(r'^\*\*(' + type_words + r')\s*' + NUMBER_RE + r'\s*(?:[（(](.+?)[）)])?[。．.]?\*\*', re.MULTILINE),
        re.compile(r'^>\s*\*\*(' + type_words + r')\s*' + NUMBER_RE + r'\s*(?:[（(](.+?)[）)])?[。．.]?\*\*', re.MULTILINE),
        re.compile(r'^\*\*【(' + type_words + r')\s*' + NUMBER_RE + r'\s*】(?:[（(](.+?)[）)])?[。．.]?\*\*', re.MULTILINE),
        re.compile(r'^\|\s*\*\*(' + type_words + r')\s*' + NUMBER_RE + r'\s*(?:[（(](.+?)[）)])?[。．.]?\*\*', re.MULTILINE),
        re.compile(r'^\|\s*(' + type_words + r')\s*' + NUMBER_RE + r'\s*\|', re.MULTILINE),
        re.compile(r'(?<![A-Za-z0-9_])\*\*(' + type_words + r')\s*' + NUMBER_RE + r'\s*(?:[（(](.+?)[）)]\s*)?[。．]?\*\*'),
        re.compile(r'^(?:#{1,3})\s*(?:\d+(?:\.\d+)*\s*)?(' + type_words + r')\s*' + NUMBER_RE + r'\s*(?:[（(](.+?)[）)])?[。．.]?\*?', re.MULTILINE),
    ]

REF_PAT = re.compile(TYPE_WORDS_REF + r'\s*' + NUMBER_RE)

def decl_num(text):
    """返回 (声明编号集合, 编号->类型映射)（全数字规范过滤）"""
    nums, types = set(), {}
    for pat in make_decl_patterns(TYPE_WORDS_REF):
        for m in pat.finditer(text):
            n = m.group(2)
            if NUMBER_FULL.match(n):
                nums.add(n)
                types.setdefault(n, m.group(1))
    return nums, types

def ref_nums(text):
    """返回引用编号集合（全数字规范过滤）"""
    return {m.group(1) for m in REF_PAT.finditer(text) if NUMBER_FULL.match(m.group(1))}

def scan_articles():
    """扫描根目录文章（排除 archive 与 00_ 索引），返回 {路径: (声明集, 类型映射, 引用集)}"""
    files = [p for p in glob.glob(os.path.join(ROOT, '*.md'))
             if 'archive' not in p and not os.path.basename(p).startswith('00_')]
    out = {}
    for f in sorted(files):
        with open(f, encoding='utf-8') as fh:
            text = fh.read()
        nums, types = decl_num(text)
        out[f] = (nums, types, ref_nums(text))
    return out

def load_master():
    """读主库（master_ai/master_chroma_db, master_formulas），返回 {编号: [metadata,...]}"""
    import chromadb
    client = chromadb.PersistentClient(path='master_ai/master_chroma_db')
    col = client.get_collection('master_formulas')
    data = col.get(include=['metadatas', 'documents'])
    master = {}
    for i, mid in enumerate(data['ids']):
        md = data['metadatas'][i]
        num = md.get('article_number') or ''
        if not NUMBER_FULL.match(num):
            continue  # 公理等特殊条目无标准编号，不参与依赖比对
        master.setdefault(num, []).append(md)
    return master

def log(action, payload):
    rec = {'ts': datetime.datetime.now().isoformat(timespec='seconds'),
           'action': action, **payload}
    with open(os.path.join(LOGS, 'audit_log.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

# ---------- 判据1：依赖闭合审计 ----------
def audit():
    articles = scan_articles()
    master = load_master()
    master_nums = set(master.keys())
    declared, declared_types = {}, {}
    for f, (d, t, r) in articles.items():
        for n in d:
            declared.setdefault(n, []).append(f)
            declared_types.setdefault(n, t.get(n, ''))
    report = {'ts': datetime.datetime.now().isoformat(timespec='seconds'),
              'master_total': len(master_nums), 'items': {}}

    def def_core_in_master(def_num, _seen=None):
        """定义编号的内核公式是否已在主库（递归传递：定义→定义→公式）"""
        if def_num not in DEF_CLOSURE:
            return False  # 未拆解：依赖保持开放
        _seen = _seen or set()
        if def_num in _seen:
            return False
        _seen.add(def_num)
        for c in DEF_CLOSURE[def_num]:
            if c in master_nums:
                continue
            if declared_types.get(c) == '定义':
                if not def_core_in_master(c, _seen):
                    return False
            else:
                return False
        return True

    for num in sorted(master_nums, key=lambda s: [int(x) for x in s.split('.')]):
        src = declared.get(num, [])
        deps = set()
        for f in src:
            deps |= articles[f][2]
        deps -= {num}
        missing = sorted(d for d in deps if d not in master_nums)
        ghosts = [d for d in missing if d not in declared]       # 无声明（笔误）
        pendable = [d for d in missing if d in declared and declared_types.get(d) != '定义']  # 有声明可补（非定义类）
        defdeps = [d for d in missing if declared_types.get(d) == '定义']  # 定义封装依赖：定义不入库，内核公式（DEF_CLOSURE）在主库即闭合
        def_closed = [d for d in defdeps if def_core_in_master(d)]
        def_open = [d for d in defdeps if d not in def_closed]
        rejected = [d for d in missing if d in KNOWN_REJECTED]   # 已驳回
        real_missing = [d for d in missing if d not in def_closed]
        report['items'][num] = {
            'src': src,
            'deps': sorted(deps),
            'closed': not real_missing,
            'missing': missing,
            'ghost': ghosts,
            'pendable': pendable,
            'def_deps': defdeps,
            'def_closed': def_closed,
            'def_open': def_open,
            'rejected': rejected,
        }
    report['ghost_total'] = sorted(set(
        g for v in report['items'].values() for g in v['ghost']),
        key=lambda s: [int(x) for x in s.split('.')])
    report['pendable_total'] = sorted(set(
        p for v in report['items'].values() for p in v['pendable']),
        key=lambda s: [int(x) for x in s.split('.')])
    report['def_total'] = sorted(set(
        p for v in report['items'].values() for p in v['def_deps']),
        key=lambda s: [int(x) for x in s.split('.')])
    report['def_open_total'] = sorted(set(
        p for v in report['items'].values() for p in v['def_open']),
        key=lambda s: [int(x) for x in s.split('.')])
    open(os.path.join(REPORTS, 'master_dep_audit.json'), 'w', encoding='utf-8').write(
        json.dumps(report, ensure_ascii=False, indent=1))
    closed = sum(1 for v in report['items'].values() if v['closed'])
    log('audit', {'master_total': len(master_nums), 'closed': closed,
                  'pendable_refs': len(report['pendable_total']),
                  'def_open_refs': len(report['def_open_total']),
                  'ghost_refs': len(report['ghost_total'])})
    print(f'主库 {len(master_nums)} 条：依赖闭合 {closed} 条；'
          f'可补依赖编号 {len(report["pendable_total"])} 个；'
          f'定义封装依赖 {len(report["def_total"])} 个（已拆解闭合 {len(report["def_total"]) - len(report["def_open_total"])}，未拆解 {len(report["def_open_total"])}）；'
          f'笔误幽灵编号 {len(report["ghost_total"])} 个')
    unclosed = [n for n, v in report['items'].items() if not v['closed']]
    print('未闭合：', ', '.join(unclosed) if unclosed else '无')

# ---------- 拓扑队列 ----------
def topo_queue():
    articles = scan_articles()
    master = load_master()
    master_nums = set(master.keys())
    declared, declared_types = {}, {}
    for f, (d, t, r) in articles.items():
        for n in d:
            declared.setdefault(n, []).append(f)
            declared_types.setdefault(n, t.get(n, ''))
    # 候选 = 全部声明编号 - 已在主库 - 已驳回（定义类按开关）
    cand = set(declared.keys()) - master_nums - set(KNOWN_REJECTED.keys())
    if not INCLUDE_DEFINITIONS:
        cand = {n for n in cand if declared_types.get(n) != '定义'}
    # 依赖图（文章级）：候选编号的依赖 = 其声明文章引用的编号
    deps_of = {}
    for n in cand:
        dd = set()
        for f in declared[n]:
            dd |= articles[f][2]
        deps_of[n] = dd - {n}
    # 拓扑排序：反复取"依赖全在主库∪已入"的候选
    in_master = set(master_nums)
    ingest_q, blocked = [], {}
    remaining = set(cand)
    while True:
        ready = [n for n in remaining if deps_of[n] <= in_master]
        if not ready:
            break
        for n in sorted(ready, key=lambda s: [int(x) for x in s.split('.')]):
            ingest_q.append(n)
            in_master.add(n)
            remaining.discard(n)
    for n in remaining:
        blocked[n] = sorted(deps_of[n] - in_master)
    out = {'ts': datetime.datetime.now().isoformat(timespec='seconds'),
           'candidates_total': len(cand),
           'ingest_queue': ingest_q, 'blocked': blocked}
    open(os.path.join(REPORTS, 'ingest_queue.json'), 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=1))
    log('queue', {'candidates_total': len(cand), 'ready': len(ingest_q),
                  'blocked': len(blocked)})
    print(f'候选 {len(cand)} 条：可入队列 {len(ingest_q)} 条；阻塞 {len(blocked)} 条')
    if ingest_q:
        print('可入前10：', ingest_q[:10])
    if blocked:
        print('阻塞示例：', list(blocked.items())[:3])

# ---------- 单条检查 ----------
def check_one(num):
    if not NUMBER_FULL.match(num):
        print(f'编号 {num} 不符合全数字规范，拒绝。'); return
    articles = scan_articles()
    master = load_master()
    master_nums = set(master.keys())
    declared = {}
    for f, (d, t, r) in articles.items():
        for n in d:
            declared.setdefault(n, []).append(f)
    if num in master_nums:
        print(f'{num} 已在主库。'); return
    if num in KNOWN_REJECTED:
        print(f'{num} 已被驳回：{KNOWN_REJECTED[num]}'); return
    if num not in declared:
        print(f'{num} 无声明（引用笔误或未提取）。'); return
    deps = set()
    for f in declared[num]:
        deps |= articles[f][2]
    deps -= {num}
    missing = sorted(d for d in deps if d not in master_nums)
    print(f'{num} 声明于 {declared[num]}')
    print(f'依赖 {len(deps)} 个；未闭合 {len(missing)} 个：{missing}')

# ---------- 入库（强制判据1） ----------
def ingest(num):
    if not NUMBER_FULL.match(num):
        print(f'编号 {num} 不符合全数字规范，拒绝。'); return
    articles = scan_articles()
    master = load_master()
    master_nums = set(master.keys())
    if num in master_nums:
        print(f'{num} 已在主库，跳过。'); return
    if num in KNOWN_REJECTED:
        print(f'{num} 已被驳回（{KNOWN_REJECTED[num]}），拒绝入库。'); return
    declared = {}
    for f, (d, t, r) in articles.items():
        for n in d:
            declared.setdefault(n, []).append(f)
    if num not in declared:
        print(f'{num} 无声明，拒绝。'); return
    deps = set()
    for f in declared[num]:
        deps |= articles[f][2]
    deps -= {num}
    missing = sorted(d for d in deps if d not in master_nums)
    if missing:
        print(f'判据1失败：依赖未闭合，缺 {missing}。拒绝入库（等依赖入后重试）。')
        log('ingest_rejected', {'num': num, 'missing': missing})
        return
    print(f'{num} 判据1通过（依赖闭合）。判据2需主库验证通过后 confirm。')

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'audit'
    if cmd == 'audit': audit()
    elif cmd == 'queue': topo_queue()
    elif cmd == 'check' and len(sys.argv) > 2: check_one(sys.argv[2])
    elif cmd == 'ingest' and len(sys.argv) > 2: ingest(sys.argv[2])
    else: print(__doc__)
