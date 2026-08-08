import json, re, sys, os
from collections import defaultdict, deque

sys.setrecursionlimit(10000)

_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, 'dependency_graph.json'), encoding='utf-8') as f:
    data = json.load(f)

nodes = data['nodes']
n2m = data['name_to_master']

def resolve(dep):
    if '公理' in dep:
        fid = n2m.get('公理（零之动）') or n2m.get('公理')
        return fid
    s = dep.strip().rstrip('。．.').strip()
    if s in n2m:
        return n2m[s]
    m = re.search(r'\d+\.\d+(\.\d+)*', dep)
    if m:
        num = m.group(0)
        for k, fid in n2m.items():
            km = re.search(r'\d+\.\d+(\.\d+)*', k)
            if km and km.group(0) == num:
                return fid
    return None

axiom_fid = n2m.get('公理（零之动）') or n2m.get('公理')
prom = {fid: node for fid, node in nodes.items() if node.get('status') == 'promoted'}

fwd = defaultdict(set)
unresolved = []
for fid, node in prom.items():
    for dep in node.get('dependencies', []):
        tfid = resolve(dep)
        if tfid and tfid in prom:
            fwd[fid].add(tfid)
        else:
            unresolved.append((fid, dep[:44]))
print("依赖边:", sum(len(v) for v in fwd.values()), "未解析:", len(unresolved))
for u in unresolved[:16]:
    print("  ?", prom[u[0]]['formula_name'][:24], "<-", u[1])

idx = {}; low = {}; st = []; on = set(); sccs = []; cnt = [0]
def sc(v):
    idx[v] = low[v] = cnt[0]; cnt[0] += 1
    st.append(v); on.add(v)
    for w in fwd[v]:
        if w not in idx:
            sc(w); low[v] = min(low[v], low[w])
        elif w in on:
            low[v] = min(low[v], idx[w])
    if low[v] == idx[v]:
        s = []
        while True:
            w = st.pop(); on.discard(w); s.append(w)
            if w == v: break
        sccs.append(s)
for v in prom:
    if v not in idx:
        sc(v)

print("\n=== 闭合环（SCC>1）===")
for s in sccs:
    if len(s) > 1:
        print([prom[f]['formula_name'][:34] for f in s])

comp_of = {}
for s in sccs:
    if len(s) > 1:
        c = tuple(sorted(s))
        for f in s: comp_of[f] = c
    else:
        comp_of[s[0]] = s[0]

comp_edges = defaultdict(set)
for fid in prom:
    c = comp_of[fid]
    for w in fwd[fid]:
        cw = comp_of[w]
        if cw != c:
            comp_edges[c].add(cw)

csize = defaultdict(int)
for f in prom:
    csize[comp_of[f]] += 1

rev = defaultdict(set)
for c, outs in comp_edges.items():
    for o in outs:
        rev[o].add(c)

allc = set(comp_of.values())
indeg = {c: len(rev[c]) for c in allc}
q = deque([c for c in allc if indeg[c] == 0])
topo = []
while q:
    v = q.popleft()
    topo.append(v)
    for w in comp_edges[v]:
        indeg[w] -= 1
        if indeg[w] == 0:
            q.append(w)

dist = {c: 0 for c in allc}
axiom_c = comp_of[axiom_fid]
dist[axiom_c] = 1
for c in topo:
    if dist[c] > 0:
        for w in rev[c]:
            if dist[w] < dist[c] + 1:
                dist[w] = dist[c] + 1

depth = {}
for fid in prom:
    c = comp_of[fid]
    base = dist.get(c, 1)
    depth[fid] = base if base > 0 else 1
    if csize[c] > 1:
        depth[fid] = base + csize[c] - 1

targets = ['0.1.3.06','0.2.1.01','0.2.1.02','0.2.2.01','0.2.2.02','0.2.2.03',
           '0.3.1.01','0.3.2.01','0.3.3.01','0.4.4.01','0.5.1.01','0.5.1.02','0.5.1.03',
           '0.6.7.01','0.6.7.02','0.7.1.01','0.7.2.01','0.7.3.01',
           '0.8.3.01','0.8.3.02','0.8.3.03','0.8.3.04','0.8.3.05',
           '0.9.5.01','0.9.7.01','0.9.7.12','2.1.2.01','2.1.3.01','3.12.1.01',
           '3.8.2.01','3.8.2.02','3.8.2.04']
print("\n=== 因果深度（精确匹配）===")
for fid, node in prom.items():
    name = node.get('formula_name','')
    for t in targets:
        if t in name:
            print(f"{t}: d={depth[fid]:2d}  {name[:40]}")
            break
print("范围:", min(depth.values()), "-", max(depth.values()))
