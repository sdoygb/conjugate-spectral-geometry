#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bench_geometric_vs_brute.py —— 对比实验：几何无枚举验证 vs 暴力枚举

同一判定问题：验证 CSS(RM(r,m)) 仿射完备码的最小距离 d = 2^(r+1)。

路径 A（暴力枚举基准）：枚举权重 1..d-1 的全部 flip 集做 syndrome 测试，
  确认 syndrome 全非零（d >= 2^(r+1)）。枚举数 Σ_{w<d} C(n,w) 随 n 指数增长。
路径 B（几何无枚举，定理 10.30.2.01 / RM 最小权重定理）：
  (1) 列互异 O(n) 判定 -> 权重 2 全检测；
  (2) RM 最小权重定理（C⊥ = RM(m-r-1,m) 最小权重 2^(r+1)）-> 权重 3..d-1 层无逻辑；
  (3) 证书构造：仿射 (r+1)-平坦指标向量 ∈ C⊥ \\ C -> d <= 2^(r+1)。
  O(n^2) 多项式完成。

用法：
  python3 bench_geometric_vs_brute.py --small          # 快速正确性验证（<1min）
  python3 bench_geometric_vs_brute.py --brute 2 6 6    # (r,m)=(2,6) 即 [[64,20,8]] 暴力到权重6
  python3 bench_geometric_vs_brute.py --geo            # 几何版全表（7 个码族成员）
  python3 bench_geometric_vs_brute.py --report         # 外推对比总表
"""
import argparse
import itertools
import math
import os
import time
from array import array

import numpy as np

from p5_explore_d5 import parity_big, rm_rows, ag_flat_count

HERE = os.path.dirname(os.path.abspath(__file__))
RATE_NPZ = os.path.join(HERE, "bench_brute_rate.npz")

# 码族参数表（与 p5_explore_d5.py main 一致）：CSS(RM(r,m), RM(r,m))
CODE_FAMILY = [(1, 5), (1, 6), (2, 6), (2, 7), (3, 8), (3, 9), (4, 10)]


def build_cols(r, m):
    """校验矩阵列：RM(r,m) 单项式评估。列宽 = dim RM(r,m) 位。"""
    monos = []
    for size in range(r + 1):
        for comb in itertools.combinations(range(m), size):
            monos.append(comb)
    cols = []
    for x in range(2 ** m):
        col = 0
        for idx, mono in enumerate(monos):
            if all((x >> i) & 1 for i in mono):
                col |= 1 << idx
        cols.append(col)
    width = len(monos)
    if width <= 63:
        return np.array(cols, dtype=np.int64), width
    return np.array(cols, dtype=object), width


def brute_layer(cols, n, w, batch=1_000_000, verbose=True):
    """暴力：流式枚举权重 w 全部 flip 集（C 级流式缓冲），统计 syndrome=0 个数。"""
    t0 = time.time()
    total = 0
    bad = 0
    it = itertools.combinations(range(n), w)
    while True:
        chunk = list(itertools.islice(it, batch))
        if not chunk:
            break
        # C 级流式缓冲：array('Q') 直接消费迭代器，绕开 tuple-list -> np.array 转换
        buf = array('Q', itertools.chain.from_iterable(chunk))
        arr = np.frombuffer(buf, dtype=np.uint64).reshape(len(chunk), w)
        sx = np.bitwise_xor.reduce(cols[arr], axis=1)
        bad += int(np.count_nonzero(sx == 0))
        total += len(chunk)
        del chunk, buf, arr, sx
    return total, bad, time.time() - t0


def geometric_verify(r, m, n_samples=3000, seed=260807):
    """几何无枚举验证器（证书式，O(n^2)）。返回 (ok, cert, dt)。"""
    import random
    t0 = time.time()
    n = 2 ** m
    rows = rm_rows(r, m)
    rc = len(rows)
    d = 2 ** (r + 1)
    cert = {}
    cols, _ = build_cols(r, m)
    # (1) 列互异 -> 权重 2 全检测（定理 10.30.2.01 结构判定）
    cert['cols_distinct'] = (len(set(cols.tolist())) == n)
    # 权重 2 全量判定（O(n^2) 列对 XOR；这是列对枚举，不是错误空间枚举）
    bad2 = 0
    for a in range(n):
        ca = int(cols[a])
        for b in range(a + 1, n):
            if ca ^ int(cols[b]) == 0:
                bad2 += 1
    cert['w2_undetected'] = bad2
    # (2) 抽样佐证（权重 3..d-1 全检测；严格保证由 RM 最小权重定理）
    rng = random.Random(seed)
    miss = 0
    for _ in range(n_samples):
        w = rng.randint(3, d - 1)
        pos = rng.sample(range(n), w)
        sx = 0
        for p in pos:
            sx ^= int(cols[p])
        if sx == 0:
            miss += 1
    cert['sample_miss'] = miss
    # (3) 证书构造：仿射 (r+1)-平坦 F = {v : v[0:m-r-1]=0}，指标 w_F ∈ C⊥ \ C
    free_bits = list(range(m - r - 1, m))
    wF = 0
    for mask in range(2 ** (r + 1)):
        v = 0
        for j, b in enumerate(free_bits):
            if (mask >> j) & 1:
                v |= 1 << b
        wF |= 1 << v
    in_dual = all(parity_big(wF & row, n) == 0 for row in rows)
    # g = x_{m-r-1}...x_{m-1}（次数 r+1 <= m-r-1，因自正交 2r < m-1），eval_g ∈ C⊥ 基
    g_eval = 0
    for v in range(n):
        if all((v >> b) & 1 for b in free_bits):
            g_eval |= 1 << v
    not_in_C = parity_big(wF & g_eval, n) == 1
    cert['wF_in_Cperp'] = in_dual
    cert['wF_not_in_C'] = not_in_C
    cert['weight'] = bin(wF).count('1')
    dt = time.time() - t0
    ok = (cert['cols_distinct'] and bad2 == 0 and miss == 0
          and in_dual and not_in_C and cert['weight'] == d)
    return ok, cert, dt


def run_small():
    """快速正确性验证：[[32,20,4]] 暴力全闭合 + 两码几何证书。"""
    print("== [small] 正确性验证 ==", flush=True)
    # --- [[32,20,4]] = (r=1, m=5) 暴力全量 ---
    cols, rc = build_cols(1, 5)
    n = 2 ** 5
    d = 2 ** 2
    tot_bad = 0
    t_all = 0.0
    for w in range(1, d):
        total, bad, dt = brute_layer(cols, n, w, batch=200_000)
        print(f"[brute] [[32,20,4]] w={w}: {total} 枚举, syndrome=0 计 {bad}, {dt:.3f}s", flush=True)
        tot_bad += bad
        t_all += dt
    print(f"[brute] [[32,20,4]] 权重 1..{d-1} 合计 syndrome=0 计 {tot_bad} -> d >= {d} ✓  耗时 {t_all:.3f}s", flush=True)
    # 权重 d 层：逻辑算符计数对照闭式
    total, bad, dt = brute_layer(cols, n, d, batch=200_000)
    expect = ag_flat_count(5, 2)
    mark = "✓ 精确吻合" if bad == expect else "✗ 不一致"
    print(f"[brute] [[32,20,4]] 权重 {d}: {total} 枚举, syndrome=0 计 {bad}, 闭式 {expect} -> {mark}", flush=True)
    # --- [[64,20,8]] = (r=2, m=6) 暴力 1..3 ---
    cols8, _ = build_cols(2, 6)
    n8 = 2 ** 6
    bad8 = 0
    for w in range(1, 4):
        total, bad, dt = brute_layer(cols8, n8, w, batch=200_000)
        bad8 += bad
        print(f"[brute] [[64,20,8]] w={w}: {total} 枚举, syndrome=0 计 {bad}, {dt:.3f}s", flush=True)
    print(f"[brute] [[64,20,8]] 权重 1..3: syndrome=0 计 {bad8} ✓（预期 0）", flush=True)
    # --- 几何证书版 ---
    for (r, m) in [(1, 5), (2, 6)]:
        n = 2 ** m
        rc = len(rm_rows(r, m))
        k = n - 2 * rc
        d = 2 ** (r + 1)
        ok, cert, dt = geometric_verify(r, m)
        status = "✓ 全部通过" if ok else "✗ 失败"
        print(f"[geo] [[{n},{k},{d}]] 证书验证 {status}: {cert}  ({dt:.3f}s)", flush=True)


def run_brute(r, m, max_w):
    """[[n,k,d]] 暴力枚举权重 1..max_w，逐层存盘。"""
    n = 2 ** m
    cols, rc = build_cols(r, m)
    k = n - 2 * rc
    d = 2 ** (r + 1)
    print(f"== [brute] [[{n},{k},{d}]] (r={r},m={m}) 暴力枚举权重 1..{max_w} ==", flush=True)
    store = {}
    if os.path.exists(RATE_NPZ):
        with np.load(RATE_NPZ) as z:
            store = {kk: z[kk] for kk in z.files}
    for w in range(1, max_w + 1):
        total, bad, dt = brute_layer(cols, n, w)
        rate = total / dt if dt > 0 else 0.0
        print(f"[brute] w={w}: {total} 枚举, syndrome=0 计 {bad}, {dt:.2f}s ({rate:,.0f} flip/s)", flush=True)
        store[str(w)] = np.array([total, bad, dt])
        np.savez(RATE_NPZ, **store)
    print("[brute] 完成，已存盘 " + RATE_NPZ, flush=True)


def run_geo():
    """几何证书版全表（7 个码族成员）。"""
    print("== [geo] 几何无枚举证书验证全表 ==", flush=True)
    rows_out = []
    for (r, m) in CODE_FAMILY:
        n = 2 ** m
        rc = len(rm_rows(r, m))
        k = n - 2 * rc
        d = 2 ** (r + 1)
        ok, cert, dt = geometric_verify(r, m)
        status = "✓" if ok else "✗"
        print(f"[geo] [[{n},{k},{d}]] {status} 列异={cert['cols_distinct']} w2漏={cert['w2_undetected']} "
              f"抽样漏={cert['sample_miss']} 证书={cert['wF_in_Cperp'] and cert['wF_not_in_C']}  {dt:.3f}s", flush=True)
        rows_out.append((n, k, d, ok, dt))
    return rows_out


def run_report():
    """外推对比总表：暴力实测 + 外推 vs 几何实测。"""
    print("== [report] 几何无枚举 vs 暴力枚举 对比总表 ==", flush=True)
    if not os.path.exists(RATE_NPZ):
        print("缺少 bench_brute_rate.npz，先跑 --brute 2 6 7", flush=True)
        return
    with np.load(RATE_NPZ) as z:
        store = {int(kk): z[kk] for kk in z.files}
    w_max = max(store.keys())
    total_m, _, dt_m = store[w_max]
    rate = total_m / dt_m
    print(f"基准速率（w={w_max} 实测 {total_m:,.0f} flip / {dt_m:.1f}s）= {rate:,.0f} flip/s", flush=True)
    YEAR = 3.15576e7
    UNIVERSE = 1.38e10
    print()
    print(f"{'码':<13}{'n':<7}{'d':<5}{'Σ_{w<d}C(n,w)':>13}{'暴力耗时':>18}{'几何实测':>11}{'加速比':>12}", flush=True)
    for (r, m) in CODE_FAMILY:
        n = 2 ** m
        rc = len(rm_rows(r, m))
        k = n - 2 * rc
        d = 2 ** (r + 1)
        enum = sum(math.comb(n, w) for w in range(1, d))
        ok, cert, dt_geo = geometric_verify(r, m)
        if enum <= 10_000_000:
            # 小码现场暴力全实测（权重 1..d-1）
            cols, _ = build_cols(r, m)
            tt = 0.0
            bb = 0
            for w in range(1, d):
                t_, b_, dtw = brute_layer(cols, n, w)
                bb += b_
                tt += dtw
            dt_brute = tt
            tag = f"{fmt_time(tt)} 全实测"
        elif (r, m) == (2, 6) and (d - 1) in store:
            dt_brute = sum(float(store[w][2]) for w in range(1, d))
            tag = fmt_time(dt_brute) + " 全实测"
        else:
            dt_brute = enum / rate
            tag = fmt_time(dt_brute) + " 外推"
        speedup = dt_brute / dt_geo if dt_geo > 0 else float('inf')
        print(f"[[{n},{k},{d}]]{'':<4}{n:<7}{d:<5}{sci(enum):>13}{tag:>18}{dt_geo:>8.3f}s{sci(speedup):>12}", flush=True)
    print()
    print(f"参照：宇宙年龄 ≈ {UNIVERSE/1e9:.1f}×10^9 年。外推假设单 flip 检测速率恒定"
          f"（同机同实现；n 增大时单 flip 成本只增不减，外推偏乐观）。", flush=True)


def sci(x):
    if x == float('inf'):
        return "∞"
    return f"{x:.2e}"


def fmt_time(s):
    if s < 60:
        return f"{s:.1f}s"
    if s < 3600:
        return f"{s/60:.1f}分"
    if s < 86400:
        return f"{s/3600:.1f}时"
    if s < 3.15576e7:
        return f"{s/86400:.1f}天"
    years = s / 3.15576e7
    if years < 1e5:
        return f"{years:,.0f}年"
    return f"{years:.2e}年"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", action="store_true", help="快速正确性验证")
    ap.add_argument("--brute", nargs=3, type=int, metavar=("R", "M", "MAXW"), help="暴力枚举 (r,m) 权重 1..MAXW")
    ap.add_argument("--geo", action="store_true", help="几何版全表")
    ap.add_argument("--report", action="store_true", help="外推对比总表")
    args = ap.parse_args()
    if args.small:
        run_small()
    elif args.brute:
        run_brute(*args.brute)
    elif args.geo:
        run_geo()
    elif args.report:
        run_report()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
