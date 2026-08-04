#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gt_scc.py — 互锁（共扼）组检测：强连通分量
=============================================
共扼定理必须批量验证、同时入库（禁止单独验证）。
本程序用文章级依赖图检测候选集中的强连通分量（互锁组）。
注意：文章级引用是粗粒度，组内每条边需人工甄别
（真实推导依赖 vs 背景引用）后方可批量验证——"慢慢查"。

用法：
  python3 tools/gt_scc.py            # 检测互锁组 → reports/interlock_groups.json
  python3 tools/gt_scc.py <编号>     # 查某编号所在的互锁组
"""
import os, re, json, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gt_pipeline import (scan_articles, load_master, KNOWN_REJECTED,
                         INCLUDE_DEFINITIONS, NUMBER_FULL, log)

REPORTS = 'reports'


def find_scc(nodes, edges):
    """Tarjan 强连通分量。nodes: set；edges: {node: set(依赖节点)}。返回 size>1 的分量。"""
    index = 0
    stack = []
    on_stack = set()
    indices = {}
    low = {}
    comps = []

    def strongconnect(v):
        nonlocal index
        indices[v] = low[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        for w in edges.get(v, ()):
            if w not in nodes:
                continue
            if w not in indices:
                strongconnect(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], indices[w])
        if low[v] == indices[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                comp.append(w)
                if w == v:
                    break
            comps.append(comp)

    for v in sorted(nodes):
        if v not in indices:
            strongconnect(v)
    return [c for c in comps if len(c) > 1]


def num_key(s):
    return [int(x) for x in s.split('.')]


def build():
    articles = scan_articles()
    master = load_master()
    master_nums = set(master.keys())
    declared, declared_types = {}, {}
    for f, (d, t, r) in articles.items():
        for n in d:
            declared.setdefault(n, []).append(f)
            declared_types.setdefault(n, t.get(n, ''))
    cand = set(declared.keys()) - master_nums - set(KNOWN_REJECTED.keys())
    if not INCLUDE_DEFINITIONS:
        cand = {n for n in cand if declared_types.get(n) != '定义'}
    edges = {}
    for n in cand:
        dd = set()
        for f in declared[n]:
            dd |= articles[f][2]
        edges[n] = {d for d in dd - {n} if d in cand}
    return articles, declared, declared_types, cand, edges


def main():
    articles, declared, declared_types, cand, edges = build()
    comps = find_scc(cand, edges)
    comps.sort(key=lambda c: (-len(c), min(num_key(x) for x in c)))
    out = {'ts': datetime.datetime.now().isoformat(timespec='seconds'),
           'candidates': len(cand), 'groups_count': len(comps),
           'groups_members_total': sum(len(c) for c in comps),
           'groups': []}
    for comp in comps:
        members = sorted(comp, key=num_key)
        g_edges = []
        for a in members:
            for b in edges[a]:
                if b in comp:
                    srcs = [os.path.basename(f) for f in declared[a] if b in articles[f][2]]
                    g_edges.append({'from': a, 'to': b, 'src': srcs})
        out['groups'].append({'members': members, 'edge_count': len(g_edges),
                              'edges': g_edges})
    os.makedirs(REPORTS, exist_ok=True)
    open(os.path.join(REPORTS, 'interlock_groups.json'), 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=1))
    log('scc', {'groups': len(comps), 'members': sum(len(c) for c in comps)})
    print(f'候选 {len(cand)} 条；互锁组 {len(comps)} 个；组成员共 {sum(len(c) for c in comps)} 条')
    for comp in comps:
        members = sorted(comp, key=num_key)
        types = {declared_types.get(m, '?') for m in members}
        print(f'  组[{len(members)}] {", ".join(members)}  (类型: {types})')
    # 查单编号
    if len(sys.argv) > 2:
        q = sys.argv[2]
        hit = [c for c in comps if q in c]
        if hit:
            print(f'\n{q} 所在互锁组: {", ".join(sorted(hit[0], key=num_key))}')
        else:
            print(f'\n{q} 不在任何互锁组（候选 {q in cand}）')


if __name__ == '__main__':
    main()
