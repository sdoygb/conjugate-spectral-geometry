# -*- coding: utf-8 -*-
"""d8_kappa_uniform.py —— 同层次主阶 κ' 均匀平均解码抽样
机制：非跨层 5 点集 F₅ 的同类伙伴 = P_T △ F₅（T = F₅ 的 4 点子集，P_T = aff(T) 唯一 3-平坦）。
均匀平均解码（类内随机代表）→ 残留 = P_T（T 随机 4 点子集）→ 方向应均匀 → κ' = κ₂(6)。
对照组：组合序最小（确定性 tie-break）的实测 κ'(z1)=0.3674, κ'(z2)=0.3097（d8_kappa.py）。
"""
import itertools, random, time
import numpy as np

m, n, r = 6, 64, 2
KAPPA = 512 / 1395

def bit_count_c(x):
    return bin(x).count("1")

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
    return cols

cols = build_cols(r, m)

z_masks = []
for keep_bits in (0b111, 0b111000):
    zk = 0
    for v in range(n):
        if (v & keep_bits) == 0:
            zk |= 1 << v
    z_masks.append(zk)

def affine_closure(points):
    """仿射包：t1 + span{t2-t1, ..., tk-t1} 的全部点（2^{k-1} 个），返回掩码"""
    t = sorted(points)
    base = t[0]
    dirs = [p ^ base for p in t[1:]]
    mask = 0
    for sub in range(1 << len(dirs)):
        x = base
        for i, d in enumerate(dirs):
            if (sub >> i) & 1:
                x ^= d
        mask |= 1 << x
    return mask

def is_plane4(p4):
    """4 点集是仿射 2-平面 ⟺ Σv = 0"""
    s = 0
    for p in p4:
        s ^= p
    return s == 0

def rand5_noncross(rng):
    """随机 5 点集，含平面 4 点子集则重抽（跨层剔除）"""
    while True:
        F = set(rng.sample(range(n), 5))
        ok = True
        for comb in itertools.combinations(F, 4):
            if is_plane4(comb):
                ok = False
                break
        if ok:
            return F

def main():
    rng = random.Random(20260807)
    N = 200_000
    t0 = time.time()
    flip = [0, 0]
    checked = 0
    for trial in range(N):
        F = rand5_noncross(rng)
        # 随机 4 点子集 T ⊂ F（均匀平均解码的残留 = aff(T)）
        T = tuple(rng.sample(sorted(F), 4))
        P = affine_closure(T)
        assert bit_count_c(P) == 8
        for i, zk in enumerate(z_masks):
            flip[i] += bit_count_c(P & zk) & 1
        checked += 1
        if checked % 50_000 == 0:
            print(f'... {checked} 样本, κ(z1)={flip[0]/checked:.6f}, κ(z2)={flip[1]/checked:.6f}, {time.time()-t0:.0f}s')
    print(f'\n均匀平均解码 κ 实测（{checked} 样本）:')
    for i, zk in enumerate(z_masks):
        k = flip[i] / checked
        print(f'  κ(z{i+1}) = {k:.6f} vs 闭式 {KAPPA:.6f} (Δ={k-KAPPA:+.6f}, {100*(k-KAPPA)/KAPPA:+.2f}%)')
    print(f'对照（组合序 tie-break，d8_kappa.py 实测）: κ(z1)=0.367435, κ(z2)=0.309677')

if __name__ == '__main__':
    main()
