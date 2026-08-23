#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
benchmark: CPU vs GPU(理想模拟) —— 几何论数据计算
对比三类任务：引用图一跳扩展 / 全库向量检索 / 规模外推
GPU 模拟假设（乐观上界）：kernel 效率 100%、无 MoltenVK 转换开销、无内存碎片
实际 RX 570 + MoltenVK 会慢 3-10 倍 —— 本结果是 GPU 的理论上限
"""
import json, time, sys, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = os.path.join(ROOT, 'tools', 'citation_graph.json')
CHROMA = os.path.join(ROOT, 'app', 'chroma_db')

# RX 570 硬件参数
PCIE_BW = 3.94e9      # PCIe 3.0 x4 理论带宽（字节/秒）
GPU_FLOPS = 5.1e12    # FP32（GCN 无张量核）
KERNEL_LAUNCH = 10e-6 # kernel 启动开销（秒）

def bench(fn, reps=100):
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    ts.sort()
    return ts[len(ts) // 2]  # 中位数

# ---------- 数据 ----------
g = json.load(open(GRAPH, encoding='utf-8'))
out, inn = g['out'], g['in']
node_list = sorted(set(out.keys()) | {d for m in out.values() for d in m.keys()})
idx = {n: i for i, n in enumerate(node_list)}
N = len(node_list)
E = sum(len(m) for m in out.values())

A = np.zeros((N, N), dtype=np.float32)
for src, dsts in out.items():
    for dst, info in dsts.items():
        cnt = info.get('count', 1) if isinstance(info, dict) else int(info)
        A[idx[src], idx[dst]] = cnt
Au = ((A + A.T) > 0).astype(np.float32)

entries = ['0.8', '1.5', '1.6', '10.19', '5.5', '6.4', '10.49', '11.13', '6.6', '8.10']
eidx = [idx[e] for e in entries if e in idx]
print(f'引用图: {N} 节点, {E} 条边 | 入口 {len(eidx)} 个 | 邻接矩阵 {N}x{N}')

# ---------- 任务 1：一跳骨架扩展 ----------
def cpu_bfs():
    neigh = {}
    for e in entries:
        for m in (out.get(e, {}), inn.get(e, {})):
            for nid, info in m.items():
                cnt = info.get('count', 1) if isinstance(info, dict) else int(info)
                neigh[nid] = neigh.get(nid, 0) + cnt
    return neigh

def np_prop():
    v = np.zeros(N, dtype=np.float32)
    for e in eidx:
        v[e] = 1.0
    return Au @ v

t1_cpu = bench(cpu_bfs, reps=2000)
t1_np = bench(np_prop, reps=2000)
t1_gpu = KERNEL_LAUNCH + 2 * N * N / GPU_FLOPS

# ---------- 任务 2：全库向量检索（真实数据） ----------
try:
    sys.path.insert(0, os.path.join(ROOT, 'app'))
    from knowledge import VectorKnowledgeBase
    from config import CHROMA_DB_DIR
    vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
    vkb.initialize()
    got = vkb._safe_collection_call('articles_collection', 'get', include=['embeddings'])
    embs = np.array(got.get('embeddings', []), dtype=np.float32)
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)
    print(f'embedding 库: {embs.shape}（ChromaDB 真实数据）')
except Exception as e:
    print(f'ChromaDB 拉取失败 ({e})，用随机数据')
    embs = np.random.RandomState(42).randn(5997, 1024).astype(np.float32)
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)

M, D = embs.shape
q = embs[0].copy()

def cpu_sim():
    return embs @ q

t2_cpu = bench(cpu_sim, reps=200)
data_bytes = M * D * 4
t2_pcie = data_bytes / PCIE_BW
t2_gpu_transfer = t2_pcie + KERNEL_LAUNCH + 2 * M * D / GPU_FLOPS
t2_gpu_resident = KERNEL_LAUNCH + 2 * M * D / GPU_FLOPS

# 生产真实路径：vkb.search（HNSW + BM25 + RRF）
t2_real = None
try:
    vkb.search('精细结构常数 137.036 推导 完整链条', top_k=8)  # 预热（BM25 懒构建）
    t2_real = bench(lambda: vkb.search('精细结构常数 137.036 推导 完整链条', top_k=8), reps=30)
except Exception as e:
    print(f'生产检索计时失败: {e}')

# ---------- 任务 3：规模外推 ----------
print()
print('规模外推（CPU = BLAS 多线程矩阵乘, GPU = 理想常驻 vs 每次传输）:')
print(f'{"规模":>10} {"数据量":>8} {"CPU BLAS":>10} {"GPU常驻":>10} {"GPU每查传输":>12} {"加速比":>8}')
rows = []
for n in [6_000, 60_000, 600_000]:
    E_ = np.random.RandomState(42).randn(n, D).astype(np.float32)
    q_ = E_[0].copy()
    t = bench(lambda: E_ @ q_, reps=20)
    gpu_res = KERNEL_LAUNCH + 2 * n * D / GPU_FLOPS
    gpu_tr = (n * D * 4) / PCIE_BW + KERNEL_LAUNCH + 2 * n * D / GPU_FLOPS
    rows.append((n, t, gpu_res, gpu_tr))
    print(f'{n:>10,} {n*D*4/1e6:>7.1f}MB {t*1e3:>9.2f}ms {gpu_res*1e3:>9.3f}ms {gpu_tr*1e3:>11.2f}ms {t/gpu_res:>7.1f}x')

# ---------- 结果 ----------
print()
print('===== 结果 =====')
print(f'[任务1] 引用图一跳扩展（{E} 边, {N} 节点, 10 入口）:')
print(f'  CPU dict 遍历 : {t1_cpu*1e6:8.1f} μs')
print(f'  numpy 矩阵传播: {t1_np*1e6:8.1f} μs')
print(f'  GPU 理想模拟  : {t1_gpu*1e6:8.1f} μs  (被 {KERNEL_LAUNCH*1e6:.0f}μs kernel 启动淹没)')
print(f'[任务2] 全库暴力检索（{M:,}×{D} = {data_bytes/1e6:.1f}MB）:')
print(f'  CPU BLAS      : {t2_cpu*1e3:8.2f} ms')
print(f'  GPU 常驻显存  : {t2_gpu_resident*1e3:8.3f} ms')
print(f'  GPU 每次传输  : {t2_gpu_transfer*1e3:8.2f} ms  (PCIe x4 传输 {t2_pcie*1e3:.1f}ms 主导)')
if t2_real is not None:
    print(f'  生产路径 vkb.search: {t2_real*1e3:8.2f} ms (HNSW+BM25+RRF, 含真实索引)')
print()
print('GPU 模拟为乐观上界（100% 效率、无 MoltenVK 开销）；实际 RX570+MoltenVK 慢 3-10 倍')
