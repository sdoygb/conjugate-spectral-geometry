#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch: enrich_with_graph 骨架扩展改为 out(上游,权重2) + in(下游,权重1)"""
import io, sys

path = 'app/knowledge.py'
with io.open(path, encoding='utf-8') as f:
    src = f.read()

old = """            neigh: Dict[str, int] = {}
            for eid in entry_ids:
                for _m in (out_map.get(eid, {}), in_map.get(eid, {})):
                    for nid, info in _m.items():
                        # 兼容两种结构：out 存 {'count','weight'}，in 存 int
                        cnt = info.get('count', 1) if isinstance(info, dict) else int(info)
                        neigh[nid] = neigh.get(nid, 0) + cnt"""

new = """            neigh: Dict[str, int] = {}
            for eid in entry_ids:
                # 上游（out：入口依赖的前置基础）权重 2；下游（in：引用入口的应用）权重 1
                for nid, info in out_map.get(eid, {}).items():
                    # 兼容两种结构：out 存 {'count','weight'}，in 存 int
                    cnt = info.get('count', 1) if isinstance(info, dict) else int(info)
                    neigh[nid] = neigh.get(nid, 0) + 2 * cnt
                for nid, info in in_map.get(eid, {}).items():
                    cnt = info.get('count', 1) if isinstance(info, dict) else int(info)
                    neigh[nid] = neigh.get(nid, 0) + cnt"""

assert old in src, 'anchor not found'
src = src.replace(old, new, 1)
with io.open(path, 'w', encoding='utf-8') as f:
    f.write(src)
print('patch applied')
