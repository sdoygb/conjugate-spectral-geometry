# -*- coding: utf-8 -*-
"""d8_kappa.py —— [[64,20,8]] 次主阶 κ' 闭式核对
闭式：κ'(w₀+1) = κ_r(m) = 2^{(r+1)(m-r-1)}/[m; r+1]_2 —— r=2, m=6: 512/1395 = 0.3670251...
机制：失败 flip 的残留恒为 8 点 3-平坦指示 χ_P（∈ RM(3,6)\RM(2,6)），
逻辑 Z 翻转 ⟺ |P ∩ z_l| 奇（z_l = 固定 3-平坦支撑），比例 = 互补方向比。

用法（分步避免 shell 120s 超时）：
  python3 d8_kappa.py --w4    # 权重 4 主阶 κ 实测 + 存 known/reps npz（~30s）
  python3 d8_kappa.py --w5a   # 权重 5 第一遍：min_order + 跨层（~60s）
  python3 d8_kappa.py --w5b   # 权重 5 第二遍：κ' 实测（跨层/同层分计）（~90s）
"""
import itertools, sys, time, argparse
from collections import Counter
import numpy as np

m, n, r = 6, 64, 2
KAPPA = 512 / 1395          # κ₂(6) = 2^9/[6;3]_2 = 0.3670251...

def build_cols(r, m):
    monos = []
    for size in range(r + 1):
        monos += list(itertools.combinations(range(m), size))
    cols = []
    for x in range(2**m):
        col = 0
        for idx, mono in enumerate(monos):
            if all((x >> i) & 1 for i in mono):
                col |= 1 << idx
        cols.append(col)
    return np.array(cols, dtype=np.uint64)

cols = build_cols(r, m)

def bit_count_c(x):
    return bin(x).count("1")

def flip_to_mask(comb):
    mk = 0
    for i in comb:
        mk |= 1 << i
    return mk

# 两个逻辑 Z 支撑（3-平坦），κ 应不依赖选择（只依赖维数）
z_masks = []
for keep_bits in (0b111, 0b111000):
    zk = 0
    for v in range(n):
        if (v & keep_bits) == 0:
            zk |= 1 << v
    assert bit_count_c(zk) == 8
    z_masks.append(zk)

def comb_batches(w, batch=1_000_000):
    it = itertools.combinations(range(n), w)
    while True:
        chunk = list(itertools.islice(it, batch))
        if not chunk:
            break
        yield np.array(chunk, dtype=np.uint64)

def report(res_hist, flip, fail, label):
    print(f'[{label}] fail = {fail:,}  残留权重分布: {dict(res_hist)}')
    for i, zk in enumerate(z_masks):
        k = flip[i] / fail
        print(f'[{label}] κ 实测(z{i+1}) = {k:.6f} vs 闭式 {KAPPA:.6f} (Δ={k-KAPPA:+.6f}, {100*(k-KAPPA)/KAPPA:+.2f}%)')

def run_w4():
    t0 = time.time()
    reps = {}                       # syndrome → 代表掩码（权重 ≤ 4）
    known = set()
    for w in (1, 2, 3):
        for comb in itertools.combinations(range(n), w):
            s = 0
            for i in comb:
                s ^= int(cols[i])
            known.add(s)
            reps[s] = flip_to_mask(comb)
    print(f'[w1-3] {len(known)} syndrome（全成功，代表=自身），{time.time()-t0:.0f}s')

    min_order = {}
    cross = 0
    for order, comb in enumerate(itertools.combinations(range(n), 4)):
        s = 0
        for i in comb:
            s ^= int(cols[i])
        if s in known:
            cross += 1
        elif s not in min_order:
            min_order[s] = order
    print(f'[w4] 第一遍: 跨层 {cross}, 类数 {len(min_order)}, {time.time()-t0:.0f}s')

    rep4 = {}
    fail4 = 0
    res_hist = Counter()
    flip = [0, 0]
    for order, comb in enumerate(itertools.combinations(range(n), 4)):
        mk = flip_to_mask(comb)
        s = 0
        for i in comb:
            s ^= int(cols[i])
        if s in known:
            fail4 += 1
            L = mk ^ reps[s]
        elif order == min_order[s]:
            rep4[s] = mk
            reps[s] = mk
            continue
        else:
            fail4 += 1
            L = mk ^ rep4[s]
        res_hist[bit_count_c(L)] += 1
        for i, zk in enumerate(z_masks):
            flip[i] += bit_count_c(L & zk) & 1
    print(f'[w4] fail4 = {fail4:,} ({fail4/635376:.6f})')
    report(res_hist, flip, fail4, 'w4 主阶')
    print(f'[w4] 耗时 {time.time()-t0:.0f}s')

    known_arr = np.array(sorted(known), dtype=np.uint64)
    reps_arr = np.array([reps[s] for s in known_arr], dtype=np.uint64)
    np.savez('d8_kappa_known.npz', known_arr=known_arr, reps_arr=reps_arr)
    print(f'[w4] 已存 known/reps（{len(known)} 类）-> d8_kappa_known.npz')

def run_w5a():
    """第一遍：min_order（非跨层）+ 跨层计数"""
    t0 = time.time()
    data = np.load('d8_kappa_known.npz')
    known = set(data['known_arr'].tolist())
    print(f'[w5a] 加载 known（{len(known)}）')
    min_order = {}
    cross = 0
    go = 0
    for batch in comb_batches(5):
        syms = np.bitwise_xor.reduce(cols[batch], axis=1)
        for j, s in enumerate(syms.tolist()):
            if s in known:
                cross += 1
            elif s not in min_order:
                min_order[s] = go + j
        go += len(batch)
        if go % 4_000_000 == 0:
            print(f'[w5a] ... {go/1e6:.0f}M, 跨层 {cross}, 类 {len(min_order)}, {time.time()-t0:.0f}s')
    print(f'[w5a] 完成: 跨层 {cross}, 非跨层类 {len(min_order)}, {time.time()-t0:.0f}s')
    arr_s = np.array(list(min_order.keys()), dtype=np.uint64)
    arr_o = np.array(list(min_order.values()), dtype=np.uint64)
    np.savez('d8_kappa_minorder.npz', s_arr=arr_s, o_arr=arr_o)
    print(f'[w5a] 已存 min_order（{len(min_order)} 类）-> d8_kappa_minorder.npz')

def run_w5b():
    """第二遍：失败判定 + 残留 + κ' 实测（跨层/同层分计）"""
    t0 = time.time()
    data = np.load('d8_kappa_known.npz')
    known = set(data['known_arr'].tolist())
    reps_lo = dict(zip(data['known_arr'].tolist(), data['reps_arr'].tolist()))
    mo = np.load('d8_kappa_minorder.npz')
    min_order = dict(zip(mo['s_arr'].tolist(), mo['o_arr'].tolist()))
    print(f'[w5b] 加载 known({len(known)}) + min_order({len(min_order)})')

    rep5 = {}
    fail_cross = fail_same = 0
    hist_cross, hist_same = Counter(), Counter()
    flip_cross, flip_same = [0, 0], [0, 0]
    go = 0
    for batch in comb_batches(5):
        syms = np.bitwise_xor.reduce(cols[batch], axis=1)
        masks = np.zeros(len(batch), dtype=np.uint64)
        for k in range(5):
            masks |= np.left_shift(np.uint64(1), batch[:, k])
        for j in range(len(batch)):
            s = int(syms[j])
            od = go + j
            mk = int(masks[j])
            if s in known:
                fail_cross += 1
                L = mk ^ reps_lo[s]
                hist_cross[bit_count_c(L)] += 1
                for i, zk in enumerate(z_masks):
                    flip_cross[i] += bit_count_c(L & zk) & 1
            elif od == min_order[s]:
                rep5[s] = mk
            else:
                fail_same += 1
                L = mk ^ rep5[s]
                hist_same[bit_count_c(L)] += 1
                for i, zk in enumerate(z_masks):
                    flip_same[i] += bit_count_c(L & zk) & 1
        go += len(batch)
        if go % 4_000_000 == 0:
            print(f'[w5b] ... {go/1e6:.0f}M, 跨层失败 {fail_cross}, 同层失败 {fail_same}, {time.time()-t0:.0f}s')

    print(f'[w5b] 完成: 跨层失败 {fail_cross:,}, 同层失败 {fail_same:,}, 总 {fail_cross+fail_same:,} ({ (fail_cross+fail_same)/7624512:.6f})')
    report(hist_cross, flip_cross, fail_cross, 'w5 跨层')
    report(hist_same, flip_same, fail_same, 'w5 同层')
    tot = fail_cross + fail_same
    tot_flip = [a + b for a, b in zip(flip_cross, flip_same)]
    report(Counter(dict(hist_cross) + dict(hist_same)) if False else (hist_cross + hist_same),
           tot_flip, tot, 'w5 总(次主阶)')
    print(f'[w5b] 耗时 {time.time()-t0:.0f}s')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--w4', action='store_true')
    ap.add_argument('--w5a', action='store_true')
    ap.add_argument('--w5b', action='store_true')
    args = ap.parse_args()
    if args.w4:
        run_w4()
    elif args.w5a:
        run_w5a()
    elif args.w5b:
        run_w5b()
    else:
        ap.print_help()
