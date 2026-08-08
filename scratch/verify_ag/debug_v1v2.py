#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试：V1 固定θ/多zl对照 + V2 类二义性 vs 逻辑翻转分层统计"""
import numpy as np
from math import comb
import itertools
from collections import defaultdict
from verify_qec import (rm_basis, pc, v1_code, v1_get_table,
                        v2_code, v2_build_decoder)

# ---------- V1: 固定 θ 注入（所有 θ_i = θ） ----------
def v1_state_fixed(theta, seed=1):
    n, z_supps, x_gens, zl_supp = v1_code()
    psi = np.zeros(1 << n, dtype=complex)
    psi[0] = 1.0
    idx = np.arange(1 << n)
    for _, g in x_gens:
        perm = idx ^ g
        psi = (psi + psi[perm]) / 2.0
    psi /= np.linalg.norm(psi)
    c = np.cos(theta / 2); s = np.sin(theta / 2)
    for i in range(n):
        e = 1 << i
        perm = idx ^ e
        psi = c * psi - 1j * s * psi[perm]
    return psi

def v1_loss_gen(psi, zl_supp, z_supps):
    """通用 loss：给定态与逻辑 Z，返回 (loss, P 数组, loss_s 数组)"""
    n = 16
    idx = np.arange(1 << n)
    par = np.zeros(1 << n, dtype=np.uint8)
    for x in range(1 << n):
        par[x] = bin(x).count('1') & 1
    s_arr = np.zeros(1 << n, dtype=np.int64)
    for j, g in enumerate(z_supps):
        s_arr += par[idx & g].astype(np.int64) << j
    amp2 = np.abs(psi) ** 2
    P = np.bincount(s_arr, weights=amp2, minlength=1 << len(z_supps)).astype(float)
    table = v1_get_table()
    zl_par = par[idx & zl_supp].astype(np.int64)
    loss_s = np.zeros(len(P))
    for s in range(len(P)):
        if P[s] < 1e-300:
            continue
        mask = (s_arr == s)
        psi_s = psi[mask]
        psi_s /= np.linalg.norm(psi_s)
        exp_zl = np.sum(np.abs(psi_s) ** 2 * np.where(zl_par[mask] == 1, -1.0, 1.0))
        Es = table.get(s, 0)
        if pc(Es & zl_supp):
            exp_zl *= -1.0
        loss_s[s] = (1.0 - exp_zl) / 2.0
    loss = float(np.sum(P * loss_s))
    return loss, P, loss_s

print("=" * 72)
print("V1 调试：固定 θ（所有 θ_i = θ）对照 + 多逻辑算符")
print("=" * 72)
n, z_supps, x_gens, zl0 = v1_code()
# 所有 deg-2 单项式作 zl 候选
zl_cands = {}
for S, v in rm_basis(2, 4):
    if len(S) == 2:
        zl_cands[''.join(f'x{i+1}' for i in S)] = v
c4 = (1 - 2 ** (1 - 4)) * comb(16, 2) * 2 ** -4
c6 = comb(16, 3) * 2 ** -6
for th in [0.05, 0.10, 0.20]:
    psi = v1_state_fixed(th)
    f = c4 * th ** 4 + c6 * th ** 6
    print(f"\nθ = {th}: 公式 loss = {f:.6e}（主阶 {c4*th**4:.6e}）")
    for name, zl in zl_cands.items():
        loss, P, loss_s = v1_loss_gen(psi, zl, z_supps)
        print(f"  zl={name}: loss = {loss:.6e}  比值(loss/公式) = {loss/f:.4f}")
    # syndrome 概率 vs 公式（权重 2 层）
    P2_formula = comb(16, 2) * (th / 2) ** 4 * (1 - th ** 2 / 4) ** 14
    print(f"  权重2层 syndrome 总概率: 量子 = {np.sum(P[P > 1e-12]):.6e}（含 0 号）")
    # 非零 syndrome 概率（排除 s=0）
    P_nz = np.sum(P[1:]) if len(P) > 1 else 0.0
    print(f"  非零 syndrome 总概率: 量子 = {P_nz:.6e} vs 公式权重2层 = {P2_formula:.6e}")

# ---------- V2: 类二义性 vs 逻辑翻转 ----------
print("\n" + "=" * 72)
print("V2 诊断：[[32,20,4]]（m=5, r=1）类二义性 vs 逻辑翻转")
print("=" * 72)
n, z_supps, zl = v2_code(5, 1)
table = v2_build_decoder(n, z_supps, 2)
rng = np.random.default_rng(3)
theta = 0.20
p = theta * theta / 4.0
N = 300000
w_tot = defaultdict(int); w_amb = defaultdict(int); w_log = defaultdict(int)
for _ in range(N):
    w = int(rng.binomial(n, p))
    if w:
        pos = [int(x) for x in rng.choice(n, w, replace=False)]
        mask = 0
        for i in pos:
            mask |= 1 << i
    else:
        mask = 0
    s = 0
    for j, g in enumerate(z_supps):
        s |= pc(mask & g) << j
    Es = table.get(s, 0)
    w_tot[w] += 1
    if Es != mask:
        w_amb[w] += 1
    rem = mask ^ Es
    if pc(rem & zl):
        w_log[w] += 1
print(f"θ={theta}: 总样本 {N}，p = {p:.4e}")
print(f"{'w':>3} {'总数':>8} {'类二义':>8} {'二义率':>8} {'逻辑翻转':>8} {'翻转率':>8} {'翻转/二义':>8}")
for w in sorted(w_tot):
    if w_tot[w] > 0:
        amb = w_amb[w] / w_tot[w]
        lg = w_log[w] / w_tot[w]
        ratio = (w_log[w] / w_amb[w]) if w_amb[w] else float('nan')
        print(f"{w:3d} {w_tot[w]:8d} {w_amb[w]:8d} {amb:8.4f} {w_log[w]:8d} {lg:8.4f} {ratio:8.4f}")
# 闭式对照
print(f"闭式 fail(2) = 1-2^(1-m) = {1-2**(1-5):.4f}（类大小 2^(m-1) = {2**(5-1)}）")

# ---------- V2 诊断 [[64,20,8]] ----------
print("\n" + "=" * 72)
print("V2 诊断：[[64,20,8]]（m=6, r=2）类二义性 vs 逻辑翻转")
print("=" * 72)
n, z_supps, zl = v2_code(6, 2)
table = v2_build_decoder(n, z_supps, 4)
rng = np.random.default_rng(4)
theta = 0.31
p = theta * theta / 4.0
N = 150000
w_tot = defaultdict(int); w_amb = defaultdict(int); w_log = defaultdict(int)
for _ in range(N):
    w = int(rng.binomial(n, p))
    if w:
        pos = [int(x) for x in rng.choice(n, w, replace=False)]
        mask = 0
        for i in pos:
            mask |= 1 << i
    else:
        mask = 0
    s = 0
    for j, g in enumerate(z_supps):
        s |= pc(mask & g) << j
    Es = table.get(s, 0)
    w_tot[w] += 1
    if Es != mask:
        w_amb[w] += 1
    rem = mask ^ Es
    if pc(rem & zl):
        w_log[w] += 1
print(f"θ={theta}: 总样本 {N}，p = {p:.4e}")
print(f"{'w':>3} {'总数':>8} {'类二义':>8} {'二义率':>8} {'逻辑翻转':>8} {'翻转率':>8} {'翻转/二义':>8}")
for w in sorted(w_tot):
    if w_tot[w] > 0:
        amb = w_amb[w] / w_tot[w]
        lg = w_log[w] / w_tot[w]
        ratio = (w_log[w] / w_amb[w]) if w_amb[w] else float('nan')
        print(f"{w:3d} {w_tot[w]:8d} {w_amb[w]:8d} {amb:8.4f} {w_log[w]:8d} {lg:8.4f} {ratio:8.4f}")
