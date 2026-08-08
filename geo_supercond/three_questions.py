#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三问判据程序化（定理 9.1.11.01）
=============================
输入：材料 (名称, 空间群编号, 电子结构类型, 磁性状态)
输出：Q1(拓扑) / Q2(通道数) / Q3(磁性) 判定 → 🟢超导 / 🔴不超导 / 🟡条件性

依据：9.1 第11章（三问判据）+ 第12章（52候选空间群枚举，spglib 第一性）
验证锚点：9.1 §11.7 表（8个案例，100%一致）
"""

# ───────────────────────────────
# 1. 52 个候选空间群（第12章枚举结果：点群含 C3 ∩ Z2）
# ───────────────────────────────
CANDIDATES_52 = sorted(
    list(range(221, 231)) +   # O_h  (m-3m)   10
    list(range(200, 207)) +   # T_h  (m-3)     7
    list(range(215, 221)) +   # T_d  (-43m)    6
    list(range(156, 162)) +   # C3v  (3m)      6
    list(range(162, 168)) +   # D3d  (-3m)     6
    list(range(183, 187)) +   # C6v  (6mm)     4
    list(range(187, 191)) +   # D3h  (-6m2)    4
    list(range(191, 195)) +   # D6h  (6/mmm)   4
    list(range(147, 149)) +   # C3i  (-3)      2
    list(range(175, 177)) +   # C6h  (6/m)     2
    [174]                     # C3h  (-6)      1
)
assert len(CANDIDATES_52) == 52, f"候选数错误: {len(CANDIDATES_52)}"

# 已知 N_eff（§11.4 代表值；候选集内未列空间群保守取 3）
N_EFF_KNOWN = {
    166: 7,   # R-3m     A类 Z2可超导（Bi2Se3）
    227: 7,   # Fd-3m    A类（Bi0.9Sb0.1）
    194: 5,   # P6_3/mmc A类
    225: 5,   # Fm-3m    B类 镜面对称（SnTe）
    221: 5,   # Pm-3m    B类
    216: 3,   # F-43m    C类 非中心对称（YPtBi）
    217: 3,   # I-43m    C类
    167: 3,   # R-3c     D类 磁性（Fe2O3 所在类，修正后）
    129: 3,   # P4/nmm   D类 磁性（反铁磁）
}

# ───────────────────────────────
# 2. 枚举类型
# ───────────────────────────────
TOPO_TYPES = {
    'normal_metal':        '普通金属',
    'normal_insulator':    '普通绝缘体',
    'normal_semiconductor':'普通半导体',
    'semimetal':           '普通半金属',
    'z2_ti':               'Z2强拓扑绝缘体',
    'tci':                 '拓扑晶体绝缘体(镜面)',
    'noncentro_ti':        '非中心对称拓扑绝缘体',
    'weak_ti':             '弱拓扑绝缘体',
    'topo_semimetal':      '拓扑半金属',
    'afm_ti':              '反铁磁拓扑绝缘体(PT保护)',
}

MAG_TYPES = {
    'NM':  '非磁性',
    'AFM': '反铁磁',
    'FM':  '铁磁',
    'SG':  '自旋玻璃',
}

# ───────────────────────────────
# 3. 三问判定
# ───────────────────────────────

def q1(topo, mag):
    """Q1（拓扑判据）：K̃⁰(Σ_cond) ≠ 0？
    拓扑类 → 通过；普通类 → 不通过；磁性破坏 T 需额外保护。"""
    if topo in ('z2_ti', 'tci', 'noncentro_ti', 'weak_ti', 'topo_semimetal'):
        if mag == 'NM':
            return 'PASS'
        if mag == 'AFM':
            # 反铁磁破坏 T → Z2 不变量未定义；PT 联合对称可保护（11.2(1)）
            return 'COND'
        return 'FAIL'          # FM/SG：破坏 T 且无保护
    if topo == 'afm_ti':
        # 反铁磁拓扑绝缘体：PT 联合对称保护表面态（MnBi2Te4 类）
        return 'PASS' if mag == 'AFM' else 'FAIL'
    # 普通电子结构（金属/绝缘体/半导体/半金属）
    if mag in ('FM', 'AFM'):
        return 'FAIL'          # 磁性破坏 T 且无其他保护（11.2 Q1(d)）
    return 'FAIL'              # 普通类无拓扑 → K̃⁰ = 0


def q2(topo, sg_num, q1_result):
    """Q2（通道数判据）：N_eff ≥ 3？
    依赖 Q1：Q1 不通过 → 无表面态 → N_eff 无意义（11.6 Fe2O3 逻辑）。"""
    if q1_result == 'FAIL':
        return 'FAIL'          # 短路：无表面态，N_eff 无意义
    if sg_num in N_EFF_KNOWN:
        return 'PASS' if N_EFF_KNOWN[sg_num] >= 3 else 'FAIL'
    if sg_num in CANDIDATES_52:
        return 'PASS'          # 候选集内，保守 N_eff = 3
    return 'FAIL'              # 非候选 → E 类，N_eff = 1


def q3(mag):
    """Q3（磁性判据）：磁性状态允许配对？"""
    if mag == 'NM':
        return 'PASS'
    if mag == 'AFM':
        return 'COND'          # 需 γ_mag 修正；PT 保护时通过（11.9 局限2）
    if mag == 'SG':
        return 'COND'          # 自旋玻璃：需修正 g_pair（11.2(3)）
    return 'FAIL'              # FM：破坏配对（11.2(2)）


def judge(name, sg_num, topo, mag, verbose=True):
    """三问判据主函数。返回 (判定, 明细)。"""
    r1 = q1(topo, mag)
    r2 = q2(topo, sg_num, r1)
    r3 = q3(mag)

    if 'FAIL' in (r1, r2, r3):
        verdict = 'RED'        # 🔴 不超导（几何论框架内）
    elif 'COND' in (r1, r2, r3):
        verdict = 'YELLOW'     # 🟡 条件性超导（需修正）
    else:
        verdict = 'GREEN'      # 🟢 超导

    neff = N_EFF_KNOWN.get(sg_num, 3 if sg_num in CANDIDATES_52 else 1)

    detail = {
        'name': name, 'sg': sg_num, 'topo': topo, 'mag': mag,
        'Q1': r1, 'Q2': r2, 'Q3': r3, 'N_eff': neff, 'verdict': verdict,
    }
    if verbose:
        icon = {'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}[verdict]
        r_icon = {'PASS': '✅', 'COND': '🟡', 'FAIL': '❌'}
        print(f"{icon} {name} (SG {sg_num}, {TOPO_TYPES[topo]}, {MAG_TYPES[mag]})")
        print(f"    Q1(K̃⁰≠0): {r_icon[r1]}  Q2(N_eff≥3): {r_icon[r2]}  "
              f"Q3(磁性): {r_icon[r3]}  N_eff={neff}")
    return detail


# ───────────────────────────────
# 4. 验证锚点（§11.7 表，8 案例必须 100% 一致）
# ───────────────────────────────
ANCHORS = [
    # (名称, 空间群, 拓扑, 磁性, 期望)
    ('Bi2Se3纳米线', 166, 'z2_ti',        'NM',  'GREEN'),
    ('SnTe纳米线',   225, 'tci',          'NM',  'GREEN'),
    ('YPtBi纳米线',  216, 'noncentro_ti', 'NM',  'GREEN'),
    ('Cu',           225, 'normal_metal', 'NM',  'RED'),
    ('Fe',           229, 'normal_metal', 'FM',  'RED'),
    ('Si',           227, 'normal_semiconductor', 'NM', 'RED'),
    ('SiO2',         154, 'normal_insulator',     'NM', 'RED'),
    ('Fe2O3',        167, 'normal_insulator',     'AFM', 'RED'),
]

def run_anchors():
    print("=" * 72)
    print("锚点验证（§11.7 表：8 案例）")
    print("=" * 72)
    n_pass = 0
    for name, sg, topo, mag, expect in ANCHORS:
        d = judge(name, sg, topo, mag, verbose=True)
        ok = (d['verdict'] == expect)
        n_pass += ok
        print(f"    {'✓' if ok else '✗ 期望 ' + expect}")
    print(f"\n锚点通过率：{n_pass}/{len(ANCHORS)}")
    return n_pass == len(ANCHORS)


# ───────────────────────────────
# 5. 演示：文章预言 + 边界案例
# ───────────────────────────────
DEMO = [
    ('MnBi2Te4',     166, 'afm_ti',      'AFM'),  # 反铁磁TI：PT保护 → 🟡
    ('Sr2RuO4',      139, 'normal_metal','NM'),   # 几何论框架内不超导（p波走他径）
    ('UTe2',          71, 'normal_metal','NM'),   # 12.2 排除预言
    ('Bi2Te3',       166, 'z2_ti',       'NM'),   # A类 已知材料
    ('SnTe(体材料)', 225, 'normal_metal','NM'),   # 体材料走特异路径 S1
    ('PrOs4Sb12',    204, 'z2_ti',       'NM'),   # 12.2 候选（T_h）
]

def run_demo():
    print("\n" + "=" * 72)
    print("演示材料判定（文章预言 + 边界案例）")
    print("=" * 72)
    for name, sg, topo, mag in DEMO:
        judge(name, sg, topo, mag, verbose=True)


if __name__ == '__main__':
    all_ok = run_anchors()
    run_demo()
    print("\n" + "=" * 72)
    print(f"总判定：锚点 {'全部通过 ✓' if all_ok else '存在失败 ✗'}")
