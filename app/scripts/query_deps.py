#!/usr/bin/env python3
"""定理依赖图查询工具 —— 推导时快速查上下游。

用法:
  python3 app/scripts/query_deps.py deps 1.3.4.01        # 查某定理的直接依赖和被依赖
  python3 app/scripts/query_deps.py upstream 1.3.4.01    # 查某定理的所有祖先（依赖链）
  python3 app/scripts/query_deps.py downstream 0.1.2.01  # 查某定理的所有后代（被依赖链）
  python3 app/scripts/query_deps.py chain 0.1.2.01 1.3.4.01  # 找两个定理间的依赖路径
  python3 app/scripts/query_deps.py roots                # 列出所有根节点
  python3 app/scripts/query_deps.py stats                # 统计概览
  python3 app/scripts/query_deps.py article 3.1          # 查某篇文章的所有定理
  python3 app/scripts/query_deps.py search Born          # 按名称搜索定理
"""

import json
import sys
import os
from collections import deque

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "theorem_dependency_graph.json")

def load():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_node(data, tnum):
    return data["nodes"].get(tnum)

def deps(data, tnum):
    node = get_node(data, tnum)
    if not node:
        print(f"定理 {tnum} 不在图中")
        return
    print(f"\n{'='*60}")
    print(f"  {node['type']} {tnum}")
    print(f"  {node['name'][:80]}")
    print(f"  文章: {node['article']}")
    print(f"{'='*60}")
    
    if node["depends_on"]:
        print(f"\n  依赖 ({len(node['depends_on'])}):")
        for d in sorted(node["depends_on"], key=lambda x: tuple(map(int, x.split('.')))):
            dn = get_node(data, d)
            name = dn["name"][:50] if dn else "(不在图中)"
            atype = dn["type"] if dn else "?"
            print(f"    ← {atype} {d}  {name}")
    else:
        print(f"\n  依赖: (无) ← 根节点")
    
    if node["depended_by"]:
        print(f"\n  被依赖 ({len(node['depended_by'])}):")
        for d in sorted(node["depended_by"], key=lambda x: tuple(map(int, x.split('.')))):
            dn = get_node(data, d)
            name = dn["name"][:50] if dn else "(不在图中)"
            atype = dn["type"] if dn else "?"
            print(f"    → {atype} {d}  {name}")
    else:
        print(f"\n  被依赖: (无) ← 叶节点")
    print()

def upstream(data, tnum):
    """BFS 找所有祖先"""
    node = get_node(data, tnum)
    if not node:
        print(f"定理 {tnum} 不在图中")
        return
    visited = set()
    queue = deque(node["depends_on"])
    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        cn = get_node(data, cur)
        if cn:
            queue.extend(cn["depends_on"])
    
    print(f"\n{tnum} 的祖先链 ({len(visited)} 个):")
    for v in sorted(visited, key=lambda x: tuple(map(int, x.split('.')))):
        vn = get_node(data, v)
        name = vn["name"][:50] if vn else "?"
        print(f"  {vn['type']} {v}  {name}")

def downstream(data, tnum):
    """BFS 找所有后代"""
    node = get_node(data, tnum)
    if not node:
        print(f"定理 {tnum} 不在图中")
        return
    visited = set()
    queue = deque(node["depended_by"])
    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        cn = get_node(data, cur)
        if cn:
            queue.extend(cn["depended_by"])
    
    print(f"\n{tnum} 的后代链 ({len(visited)} 个):")
    for v in sorted(visited, key=lambda x: tuple(map(int, x.split('.')))):
        vn = get_node(data, v)
        name = vn["name"][:50] if vn else "?"
        print(f"  {vn['type']} {v}  {name}")

def chain(data, src, dst):
    """BFS 找最短依赖路径"""
    if src not in data["nodes"]:
        print(f"源定理 {src} 不在图中")
        return
    if dst not in data["nodes"]:
        print(f"目标定理 {dst} 不在图中")
        return
    
    # BFS 从 src 出发找 dst
    parent = {src: None}
    queue = deque([src])
    found = False
    while queue and not found:
        cur = queue.popleft()
        if cur == dst:
            found = True
            break
        cn = data["nodes"].get(cur)
        if cn:
            for dep in cn["depended_by"]:  # 顺着被依赖方向走
                if dep not in parent:
                    parent[dep] = cur
                    queue.append(dep)
    
    if not found:
        print(f"未找到从 {src} 到 {dst} 的依赖路径")
        # 尝试反向
        print("尝试反向搜索...")
        parent2 = {dst: None}
        queue2 = deque([dst])
        found2 = False
        while queue2 and not found2:
            cur = queue2.popleft()
            if cur == src:
                found2 = True
                break
            cn = data["nodes"].get(cur)
            if cn:
                for dep in cn["depends_on"]:
                    if dep not in parent2:
                        parent2[dep] = cur
                        queue2.append(dep)
        if found2:
            path = []
            cur = src
            while cur:
                path.append(cur)
                cur = parent2[cur]
            print(f"\n依赖路径 ({len(path)-1} 层):")
            for i, p in enumerate(path):
                pn = data["nodes"].get(p, {})
                print(f"  {'  ' * i}{pn.get('type','?')} {p}  {pn.get('name','?')[:50]}")
            return
    
    # 回溯路径
    path = []
    cur = dst
    while cur:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    
    print(f"\n依赖路径 ({len(path)-1} 层):")
    for i, p in enumerate(path):
        pn = data["nodes"].get(p, {})
        arrow = "  " * i + ("↓" if i < len(path)-1 else "●")
        print(f"  {arrow} {pn.get('type','?')} {p}  {pn.get('name','?')[:50]}")

def roots_cmd(data):
    roots = [n for n in data["nodes"].values() if not n["depends_on"]]
    print(f"\n根节点 ({len(roots)}):")
    for r in sorted(roots, key=lambda x: x["number"]):
        print(f"  {r['type']} {r['number']}  {r['name'][:60]}  [{r['article']}]")

def stats_cmd(data):
    nodes = data["nodes"]
    roots = [n for n in nodes.values() if not n["depends_on"]]
    leaves = [n for n in nodes.values() if not n["depended_by"]]
    
    type_counts = {}
    vol_counts = {}
    for n in nodes.values():
        t = n["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
        v = n.get("volume", "?")
        vol_counts[v] = vol_counts.get(v, 0) + 1
    
    print(f"\n{'='*50}")
    print(f"  定理依赖图统计")
    print(f"{'='*50}")
    print(f"  总节点: {len(nodes)}")
    print(f"  总边:   {sum(len(n['depends_on']) for n in nodes.values())}")
    print(f"  根节点: {len(roots)}")
    print(f"  叶节点: {len(leaves)}")
    print(f"  文章数: {len(data['articles'])}")
    
    print(f"\n  按类型:")
    for t, c in sorted(type_counts.items()):
        print(f"    {t}: {c}")
    
    print(f"\n  按卷:")
    for v, c in sorted(vol_counts.items()):
        print(f"    卷{v}: {c}")
    
    # Top 被依赖
    top = sorted(nodes.values(), key=lambda n: len(n["depended_by"]), reverse=True)[:10]
    print(f"\n  最被依赖 Top 10:")
    for n in top:
        print(f"    {n['type']} {n['number']}  ({len(n['depended_by'])}次)  {n['name'][:50]}")

def article_cmd(data, num):
    """查某篇文章的所有定理"""
    articles = [a for a in data["article_info"] if a.startswith(num)]
    if not articles:
        print(f"未找到编号 {num} 的文章")
        return
    
    for a in sorted(articles):
        info = data["article_info"][a]
        print(f"\n{a}")
        print(f"  标题: {info.get('title','?')}")
        print(f"  定理数: {info.get('theorem_count', 0)}")
        deps = info.get("dependencies", [])
        if deps:
            print(f"  文章级依赖: {', '.join(deps)}")
        
        # 列出定理
        thms = [n for n in data["nodes"].values() if n["article"] == num]
        if thms:
            print(f"  定理列表:")
            for t in sorted(thms, key=lambda x: x["number"]):
                print(f"    {t['type']} {t['number']}  {t['name'][:60]}")

def search_cmd(data, keyword):
    results = []
    for n in data["nodes"].values():
        if keyword.lower() in n["name"].lower() or keyword in n["number"]:
            results.append(n)
    
    if not results:
        print(f"未找到包含 '{keyword}' 的定理")
        return
    
    print(f"\n搜索结果 ({len(results)}):")
    for n in sorted(results, key=lambda x: x["number"]):
        print(f"  {n['type']} {n['number']}  {n['name'][:70]}  [{n['article']}]")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    data = load()
    
    if cmd == "deps":
        deps(data, sys.argv[2])
    elif cmd == "upstream":
        upstream(data, sys.argv[2])
    elif cmd == "downstream":
        downstream(data, sys.argv[2])
    elif cmd == "chain":
        chain(data, sys.argv[2], sys.argv[3])
    elif cmd == "roots":
        roots_cmd(data)
    elif cmd == "stats":
        stats_cmd(data)
    elif cmd == "article":
        article_cmd(data, sys.argv[2])
    elif cmd == "search":
        search_cmd(data, sys.argv[2])
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
