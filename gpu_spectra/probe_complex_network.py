#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针复形：关系网与几何结构（10.81）——可复现计算
====================================================
节点：10.77 探针编号体系 ③④⑤⑥⑦⑧⑨⑩⑪⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕（21 实探针）
边（全部来自 10.77 §22/§23/§24 的推导关系，非事后拼凑）：
  D 依赖边  21 条：判别规则/结论迁移（10.77 §22 递进排除链 + §23 理论-探针表）
  I 互锁边   7 条：同一结构预言的两个面（双向检验/时序衔接/交叉验证）
  C 对偶边   7 条：谱-波型共轭（10.80 §2）：同一结构的结构侧/实现侧投影
  S 数据共享边 33 条：同一主数据源承载多个探针

输出：
  1) 谱不变量：λ_max、λ2、谱间隙 Δ=λ1-λ2、秩（非零特征值数）
  2) 单纯复形同调（GF(2) 边界矩阵）：β0/β1/β2、Euler 特征校验
  3) 定理-探针覆盖度（10.77 §23 理论链条表转置）

用法：python3 gpu_spectra/probe_complex_network.py
"""
import numpy as np
import networkx as nx
from itertools import combinations
import json

# ---------------- 节点 ----------------
P = ['③','④','⑤','⑥','⑦','⑧','⑨','⑩','⑪','⑭',
     '⑮','⑯','⑰','⑱','⑲','⑳','㉑','㉒','㉓','㉔','㉕']
idx = {p: i for i, p in enumerate(P)}
N = len(P)

# ---------------- 依赖边 D（有向：判别规则/结论沿箭头迁移） ----------------
D_edges = [
    ('③','⑤'),  # std 判别规则迁移 → 世行面板（10.75 §6 第五探针）
    ('③','⑥'),  # std 判别规则迁移 → WVS 个体级（10.75 §6 第六探针）
    ('④','⑮'),  # 破缺判别（std 恢复 CLT）→ 战争为破缺事件
    ('④','⑲'),  # 破缺判别（冲突国 std>2.5 vs 和平国 <2.1）→ 2026 结构诊断
    ('④','⑱'),  # T3 二部图假刚性 → 破缺/补缺谱论
    ('④','㉑'),  # 破缺判别（区域内 std）→ 中国区域纤维化
    ('④','㉒'),  # 破缺判别（国家内 std）→ 中印对照
    ('④','㉓'),  # 假刚性（S8 完全二部）→ 域外场
    ('⑥','⑦'),  # 排除链：GDP/教育残差化
    ('⑥','⑧'),  # 排除链：WGI/Hofstede 残差化
    ('⑥','⑨'),  # 排除链：结构级候选
    ('⑥','⑪'),  # 时间版：跨波次
    ('⑨','⑭'),  # 语言家族 → 成对语言距离
    ('⑩','⑭'),  # 成对 Mantel 方法迁移（地理→语言距离）
    ('⑮','⑯'),  # 战争输出 → 两态 Markov
    ('⑯','⑰'),  # 两态 Markov → 风险排名
    ('⑯','⑲'),  # 两态 Markov + 破缺判别 → 结构诊断
    ('⑯','⑳'),  # 两态 Markov 时变参数 → 饱和期
    ('⑲','⑳'),  # 区域补缺窗口 → 全口径饱和计算（⑳ 修正 ⑲ 口径）
    ('⑳','㉔'),  # 饱和窗口 2029–2035 → 补缺传播时序衔接
    ('⑳','㉕'),  # λ_r 下降（补缺弱化）→ 长周期定位
    ('㉓','㉔'),  # 66 国外部场 → 6 节点补缺传播图
    ('㉔','㉕'),  # 补缺传播 → 长周期监测
]

# ---------------- 互锁边 I（无向：同一结构预言的两个面） ----------------
I_edges = [
    ('⑰','⑲'),  # 同一区域双向：最可能破缺点 = 最可能补缺点（两态模型结构预言）
    ('⑲','⑳'),  # 区域窗口 ↔ 全口径饱和期（互证）
    ('⑳','㉔'),  # 时序衔接：2029–2035 ↔ 2034–2038
    ('㉔','㉕'),  # 传播预言 ↔ 长周期监测
    ('⑱','㉔'),  # 历史圆满形态 ↔ 未来传播形态（轴心时代链条）
    ('㉓','㉕'),  # 双源交叉验证：BACI/DOTS BR r=0.8545
    ('⑲','㉔'),  # 补缺窗口 ↔ 补缺传播形态（同一结构预言两个面）
]

# ---------------- 对偶边 C（无向：谱-波型共轭） ----------------
C_edges = [
    ('③','⑥'),  # 刚性判别：谱侧 GPU 系综（std 平坦）↔ 实现侧 WVS 排序（ρ=0.9951）
    ('⑰','⑲'),  # 破缺预言（实现侧）↔ 补缺窗口（结构侧）
    ('⑱','⑳'),  # 圆满者结构事件（Seshat）↔ 饱和期实现统计（10.80 两层结构）
    ('㉓','㉕'),  # 外部场谱论：2024 截面（BACI）↔ 76 年时间序列（DOTS）
    ('⑩','⑭'),  # 成对地理距离 ↔ 成对语言距离（独立结构投影）
]

# ---------------- 数据共享边 S（无向：同一主数据源） ----------------
S_groups = [
    ['⑥','⑦','⑧','⑨','⑪','⑲','㉑','㉒'],  # WVS（⑲ 的国内 std 亦来自 WVS，10.77 §15）
    ['⑮','⑯','⑰','⑲','⑳'],              # UCDP
    ['⑤','⑦'],                            # World Bank（⑤ 生育率、⑦ GDP 同源）
    ['㉓','㉔'],                            # BACI
]
S_edges = []
for g in S_groups:
    S_edges += list(combinations(g, 2))

print(f"节点 V = {N} | 依赖边 D = {len(D_edges)} | 互锁边 I = {len(I_edges)} "
      f"| 对偶边 C = {len(C_edges)} | 数据共享边 S = {len(S_edges)}")
unique_sem = set(D_edges) | set(I_edges) | set(C_edges)
print(f"语义唯一边（D∪I∪C 去重）= {len(unique_sem)} 条")
overlap = set(I_edges) & set(C_edges)
print(f"I∩C 重叠 = {len(overlap)} 条")

# ---------------- 邻接矩阵（谱：全部对称化；D 有向边无向化为机制关联） ----------------
def adj(edges, directed=False, sym=False):
    A = np.zeros((N, N))
    for a, b in edges:
        i, j = idx[a], idx[b]
        A[i, j] += 1
        if not directed:
            A[j, i] += 1
    if directed and sym:
        A = A + A.T
    return A

A_D  = adj(D_edges, directed=True, sym=True)
A_I  = adj(I_edges)
A_C  = adj(C_edges)
A_S  = adj(S_edges)
A_sem = A_D + A_I + A_C                       # 语义图（对称化，多重计数）
A_all = A_D + A_I + A_C + A_S                 # 全图（含数据共享）

def report(name, A):
    vals = np.linalg.eigvalsh(A)
    nz = int(np.sum(np.abs(vals) > 1e-9))
    lmax, l2 = float(vals[-1]), float(vals[-2])
    gap = lmax - l2
    print(f"[{name}] λ_max={lmax:.4f}  λ2={l2:.4f}  Δ={gap:.4f}  秩(非零特征值)={nz}")
    return {'name': name, 'lmax': round(lmax, 4), 'l2': round(l2, 4),
            'gap': round(gap, 4), 'rank': nz}

print("\n===== 谱不变量 =====")
spec = {}
spec['sem']  = report('语义图 D+I+C（对称化多重）', A_sem)
spec['D']    = report('依赖子图 D（对称化）', A_D)
spec['I']    = report('互锁子图 I', A_I)
spec['C']    = report('对偶子图 C', A_C)
spec['all']  = report('全图 D+I+C+S（对称化多重）', A_all)

# ---------------- 单纯复形同调（GF(2) 边界矩阵） ----------------
def gf2_rank(M):
    M = M.copy() % 2
    m, n = M.shape
    r = 0
    for col in range(n):
        piv = None
        for row in range(r, m):
            if M[row, col] % 2 == 1:
                piv = row
                break
        if piv is None:
            continue
        M[[r, piv]] = M[[piv, r]]
        for row in range(m):
            if row != r and M[row, col] % 2 == 1:
                M[row] = (M[row] + M[r]) % 2
        r += 1
        if r == m:
            break
    return r

def homology(verts, edges, faces):
    """返回 (b0, b1, b2, E, F, rank_d2, chi)。edges/faces 为节点元组。"""
    V_list = sorted(verts)
    vi = {v: k for k, v in enumerate(V_list)}
    E_list = sorted(set(tuple(sorted(e)) for e in edges))
    ei = {e: k for k, e in enumerate(E_list)}
    F_list = sorted(set(tuple(sorted(f)) for f in faces))
    nv, ne, nf = len(V_list), len(E_list), len(F_list)
    d1 = np.zeros((nv, ne), dtype=int)
    for e, (a, b) in enumerate(E_list):
        d1[vi[a], e] = 1
        d1[vi[b], e] = 1
    d2 = np.zeros((ne, nf), dtype=int)
    for f, tri in enumerate(F_list):
        for a, b in combinations(tri, 2):
            d2[ei[tuple(sorted((a, b)))], f] = 1
    r1, r2 = gf2_rank(d1), gf2_rank(d2)
    b0 = nv - r1
    b1 = ne - r1 - r2
    b2 = nf - r2
    chi = nv - ne + nf
    assert chi == b0 - b1 + b2, f"Euler 校验失败: χ={chi} vs β0-β1+β2={b0-b1+b2}"
    return b0, b1, b2, ne, nf, r2, chi

def tri_of(edges):
    G = nx.from_edgelist(edges)
    return [tuple(sorted(t)) for t in nx.enumerate_all_cliques(G) if len(t) == 3]

print("\n===== 单纯复形同调 =====")
# 1) 语义复形：21 节点 + 语义唯一边 + 全部三角形面
tri_sem = tri_of(list(unique_sem))
b0s, b1s, b2s, ne_s, nf_s, r2s, chi_s = homology(P, list(unique_sem), tri_sem)
print(f"[语义复形] V=21  E={ne_s}  F={nf_s}  β0={b0s}  β1={b1s}  β2={b2s}  "
      f"rank(∂2)={r2s}  χ={chi_s}")

# 2) 互锁复形：仅 I 边（7 节点 7 边）+ I 三角形
tri_I = tri_of(I_edges)
I_nodes = sorted(set(v for e in I_edges for v in e))
b0i, b1i, b2i, ne_i, nf_i, r2i, chi_i = homology(I_nodes, I_edges, tri_I)
print(f"[互锁复形 I] V={len(I_nodes)}  E={ne_i}  F={nf_i}  β0={b0i}  β1={b1i}  "
      f"β2={b2i}  rank(∂2)={r2i}  χ={chi_i}   三角形={tri_I}")

# 3) 互锁-对偶复形：I∪C 边 + I∪C 三角形
IuC = set(I_edges) | set(C_edges)
tri_IC = tri_of(list(IuC))
IC_nodes = sorted(set(v for e in IuC for v in e))
b0ic, b1ic, b2ic, ne_ic, nf_ic, r2ic, chi_ic = homology(IC_nodes, list(IuC), tri_IC)
print(f"[互锁-对偶复形 I∪C] V={len(IC_nodes)}  E={ne_ic}  F={nf_ic}  β0={b0ic}  "
      f"β1={b1ic}  β2={b2ic}  rank(∂2)={r2ic}  χ={chi_ic}   三角形={tri_IC}")

# 语义复形中未填的 4-环（β1 的代表元，供讨论）
G_IC = nx.from_edgelist(list(IuC))
unfilled = []
for cyc in nx.minimum_cycle_basis(G_IC):
    if len(cyc) == 4:
        unfilled.append([P_n for P_n in cyc])
print(f"互锁-对偶复形最小 4-环（未填面的洞）: {unfilled}")

# ---------------- 定理-探针覆盖度（10.77 §23 转置） ----------------
coverage = {
    '定理 5.8.3.02': ['③','⑥','⑨'],
    '定理 0.9.4.02': ['⑥','⑧'],
    '探针③判别规则': ['⑤','⑥'],
    '10.75 群尺度条款': ['⑤','⑥','⑦','⑧','⑨'],
    '10.76 条件 𝒞': ['⑤'],
    '探针④ T3 反例 → 破缺/补缺谱论': ['⑱'],
    '10.75 长时间条款': ['⑪'],
    '10.75 群尺度条款（成对耦合）': ['⑩','⑭'],
    '探针④ 破缺判别（std 恢复 CLT）': ['⑮'],
    '两态 Markov（泊松破缺+有限弛豫）': ['⑯'],
    '破缺倾向排序（λ_b 驱动）': ['⑰'],
    '两态 Markov + 破缺判别（当前诊断）': ['⑲'],
    '两态 Markov 时变参数（λ_r 下降）': ['⑳'],
    '破缺判别（区域/国家内 std）': ['㉑','㉒'],
    '谱论外部场（λ₂ 与 BR 解耦）': ['㉓'],
    '谱论补缺传播（λ₂ 恢复定向扩散）': ['㉔'],
    '谱论外部场长周期（λ₂ 趋势/BR 周期）': ['㉕'],
}
probe_cover = {p: [] for p in P}
total_links = 0
for th, probes in coverage.items():
    total_links += len(probes)
    for p in probes:
        probe_cover[p].append(th)
print(f"\n===== 定理-探针覆盖度（10.77 §23 转置）=====\n理论链 {len(coverage)} 行 → {total_links} 条连线")
for p in P:
    n = len(probe_cover[p])
    tag = f"{n} 个定理: {probe_cover[p]}" if n else "0（定理源/判别源头角色）"
    print(f"  探针{p}: {tag}")

# ---------------- 摘要输出 ----------------
summary = {
    'V': N, 'D': len(D_edges), 'I': len(I_edges), 'C': len(C_edges),
    'S': len(S_edges), 'semantic_unique': len(unique_sem),
    'spectra': spec,
    'homology': {
        'semantic': {'b0': b0s, 'b1': b1s, 'b2': b2s, 'E': ne_s, 'F': nf_s},
        'interlock': {'b0': b0i, 'b1': b1i, 'b2': b2i, 'E': ne_i, 'F': nf_i},
        'interlock_dual': {'b0': b0ic, 'b1': b1ic, 'b2': b2ic, 'E': ne_ic, 'F': nf_ic},
    },
    'coverage_links': total_links,
    'probe_coverage': {p: len(probe_cover[p]) for p in P},
}
with open('gpu_spectra/probe_complex_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)
print("\n摘要已保存: gpu_spectra/probe_complex_summary.json")
