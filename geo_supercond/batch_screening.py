#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量三问判据筛选接口（定理 9.1.11.01 程序化）
=========================================
功能：
  1. N_eff 表：52 候选空间群全扫（spglib 符号 + N_eff 分配）
  2. 批量判定：CSV 输入 → CSV 输出

输入 CSV 列：name, spacegroup, topo_type, magnetism
  topo_type 键：normal_metal / normal_insulator / normal_semiconductor /
                semimetal / z2_ti / tci / noncentro_ti / weak_ti /
                topo_semimetal / afm_ti
  magnetism 键：NM(非磁) / AFM(反铁磁) / FM(铁磁) / SG(自旋玻璃)

输出 CSV 列：name, spacegroup, international, point_group, topo_type,
             magnetism, Q1, Q2, Q3, N_eff, verdict, note
  verdict：GREEN(🟢超导) / YELLOW(🟡条件性) / RED(🔴不超导)
"""
import csv
import sys
import spglib
from three_questions import judge, CANDIDATES_52, N_EFF_KNOWN

ICON = {'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}


def build_sg_index():
    """遍历 530 个 hall 设置，建立 {空间群编号: (国际符号, Schoenflies点群)}。"""
    idx = {}
    for hall in range(1, 531):
        sg = spglib.get_spacegroup_type(hall)
        num = sg.number
        if num not in idx:
            idx[num] = (sg.international_short, sg.pointgroup_schoenflies)
    return idx


def neff_table(idx, out_path='candidates_neff.csv'):
    """52 候选空间群全扫 → N_eff 表。"""
    rows = []
    for num in CANDIDATES_52:
        short, sch = idx[num]
        neff = N_EFF_KNOWN.get(num, 3)          # 候选集内未列 → 保守下限 3
        note = 'known(§11.4)' if num in N_EFF_KNOWN else 'conservative'
        rows.append([num, short, sch, neff, note])
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['spacegroup', 'international', 'point_group', 'N_eff', 'note'])
        w.writerows(rows)
    from collections import Counter
    dist = Counter(r[3] for r in rows)
    n_known = sum(1 for r in rows if r[4] == 'known(§11.4)')
    print(f"N_eff 表已生成：{out_path}")
    print(f"  候选总数 {len(rows)}（已知值 {n_known} 个，保守值 {len(rows)-n_known} 个）")
    print(f"  N_eff 分布：{dict(sorted(dist.items()))}")
    return rows


def batch_judge(idx, in_path, out_path):
    """CSV 批量判定接口。"""
    with open(in_path, newline='', encoding='utf-8') as f:
        materials = list(csv.DictReader(f))
    results = []
    for m in materials:
        name = m['name'].strip()
        sg = int(m['spacegroup'])
        topo = m['topo_type'].strip()
        mag = m['magnetism'].strip()
        short, sch = idx.get(sg, ('?', '?'))
        d = judge(name, sg, topo, mag, verbose=False)
        note = ''
        if d['verdict'] == 'GREEN' and topo != 'afm_ti':
            note = '超导候选'
        elif d['verdict'] == 'YELLOW':
            note = '需γ_mag/g_pair修正'
        elif d['Q1'] == 'FAIL':
            note = '拓扑缺失'
        results.append([name, sg, short, sch, topo, mag,
                        d['Q1'], d['Q2'], d['Q3'], d['N_eff'],
                        d['verdict'], note])
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['name', 'spacegroup', 'international', 'point_group',
                    'topo_type', 'magnetism', 'Q1', 'Q2', 'Q3', 'N_eff',
                    'verdict', 'note'])
        w.writerows(results)
    print(f"\n批量判定完成：{len(results)} 个材料 → {out_path}")
    from collections import Counter
    vdist = Counter(r[10] for r in results)
    print(f"  判定分布：{ {k: vdist[k] for k in ('GREEN', 'YELLOW', 'RED')} }")
    for r in results:
        print(f"  {ICON[r[10]]} {r[0]:<14} SG{r[1]:<4} {r[2]:<8} {r[3]:<5} "
              f"Q1={r[6]:<4} Q2={r[7]:<4} Q3={r[8]:<4} N_eff={r[9]:<2} {r[11]}")


if __name__ == '__main__':
    idx = build_sg_index()
    if len(sys.argv) > 1 and sys.argv[1] == 'neff':
        neff_table(idx, sys.argv[2] if len(sys.argv) > 2 else 'candidates_neff.csv')
    elif len(sys.argv) > 1 and sys.argv[1] == 'batch':
        batch_judge(idx, sys.argv[2], sys.argv[3])
    else:
        neff_table(idx)
        batch_judge(idx, 'demo_materials.csv', 'demo_results.csv')
