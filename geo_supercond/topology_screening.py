# -*- coding: utf-8 -*-
"""
230 空间群拓扑超导筛选枚举
判据：定理 9.1.12.01 —— [G_晶格, P_tau] = 0 且 [G_晶格, P_sigma2] = 0
  = 点群含 C3 旋转（3 次或 6 次轴）且含 Z2 对换（镜面反射或空间反演）
实现：spglib 数据库第一性枚举（530 Hall 设置 -> 230 空间群 -> 对称操作矩阵判据）
验证锚点：9.1 文章 12.2 表（194/204/227/166/216 候选；139/71 非候选）
"""
import numpy as np
import spglib

def mat_order(R):
    """旋转矩阵阶数（1-6），非单位旋转返回 0"""
    acc = np.eye(3, dtype=int)
    for k in range(1, 7):
        acc = acc @ R
        if np.array_equal(acc, np.eye(3, dtype=int)):
            return k
    return 0

def has_c3(rots):
    """含 C3：存在 3 次旋转（ord=3）或 6 次旋转（ord=6，C6 包含 C3）"""
    return any(mat_order(R) in (3, 6) for R in rots)

def has_z2(rots):
    """含 Z2 对换：存在二阶 det=-1 正交变换（镜面反射或空间反演 -I）"""
    return any(np.array_equal(R @ R, np.eye(3, dtype=int))
               and int(round(np.linalg.det(R))) == -1 for R in rots)

# ---- 第一性数据收集：530 Hall 设置 -> 230 空间群（取每个编号首个 Hall）----
sg_data = {}
for hall in range(1, 531):
    sg = spglib.get_spacegroup_type(hall)
    num = sg.number
    if num not in sg_data:
        sym = spglib.get_symmetry_from_database(hall)
        sg_data[num] = {'short': sg.international_short,
                        'point': sg.pointgroup_schoenflies,
                        'point_int': sg.pointgroup_international,
                        'rots': sym['rotations'],
                        'hall': sg.hall_symbol}

assert len(sg_data) == 230, f"空间群收集不完整: {len(sg_data)}"

# ---- 判据筛选 ----
candidates, excluded = [], []
for num in range(1, 231):
    d = sg_data[num]
    c3, z2 = has_c3(d['rots']), has_z2(d['rots'])
    if c3 and z2:
        candidates.append((num, d['short'], d['point'], 'C3+Z2'))
    elif c3 and not z2:
        excluded.append((num, d['short'], d['point'], '仅C3'))
    elif not c3 and z2:
        excluded.append((num, d['short'], d['point'], '仅Z2'))
    else:
        excluded.append((num, d['short'], d['point'], '无'))

# ---- 验证锚点（12.2 表）----
anchors = {194: ('P63/mmc', True), 204: ('Im-3m', True), 227: ('Fd-3m', True),
           166: ('R-3m', True), 216: ('F-43m', True),
           139: ('I4/mmm', False), 71: ('Immm', False)}
print("=" * 72)
print("验证锚点（9.1 文章 12.2 表）")
print("=" * 72)
ok = True
cand_nums = {c[0] for c in candidates}
for num, (short, expect) in anchors.items():
    d = sg_data[num]
    hit = (num in cand_nums) == expect
    ok &= hit
    print(f"  No.{num:3d} {d['short']:<10s} 点群 {d['point']:<6s} 候选={'是' if num in cand_nums else '否'} "
          f"预期={'候选' if expect else '非候选'} {'✓' if hit else '✗ MISMATCH'}")
print(f"\n  锚点全部命中: {ok}")

# ---- 统计 ----
print("=" * 72)
print(f"候选空间群: {len(candidates)}/230 = {100*len(candidates)/230:.2f}%")
print(f"  （文章 12.6 预言：约 21%）")
print("=" * 72)

# 按点群分组
from collections import defaultdict
by_point = defaultdict(list)
for num, short, point, tag in candidates:
    by_point[point].append((num, short))
print(f"\n候选点群 {len(by_point)} 个：")
for pg in sorted(by_point, key=lambda p: -len(by_point[p])):
    nums = [n for n, _ in by_point[pg]]
    print(f"  {pg:<6s} {len(nums):2d} 个空间群: {nums}")

print(f"\n排除明细（含 C3 但无 Z2）: "
      f"{len([e for e in excluded if e[3]=='仅C3'])} 个")
for e in [e for e in excluded if e[3] == '仅C3']:
    print(f"    No.{e[0]:3d} {e[1]:<10s} {e[2]}")
print(f"排除明细（含 Z2 但无 C3）: "
      f"{len([e for e in excluded if e[3]=='仅Z2'])} 个")

# ---- 候选完整清单 ----
print("\n候选空间群完整清单：")
for num, short, point, tag in sorted(candidates):
    print(f"  No.{num:3d} {short:<10s} {point}")
