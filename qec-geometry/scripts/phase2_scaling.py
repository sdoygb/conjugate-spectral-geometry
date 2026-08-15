#!/usr/bin/env python3
"""二期扩展：L 标度律扫描 —— 10.54 §6.3 开放问题的直接回应

问题：
  Q1  total_dist A1/A0 是否随码距 L 增长？（预期 A0 恒定 ~2，A1 ∝ L → ratio ∝ L）
  Q2  显式长链型比例（A1 中 max_dist >= 4）是否随 L 增大？
  Q3  固定种子后结果是否可复现（3 种子波动）？

方法：surface code (unrotated_memory_z), noise=0.005（工作区），rounds=3，
      shots 动态调整保证 A1 样本充足；每个 (L, seed) 结果独立存 JSON（断点续跑）。

用法：
  python phase2_scaling.py --L 4 --seed 42 --shots 20000
  python phase2_scaling.py --L 6 --seed 42 --shots 200000
  python phase2_scaling.py --L 8 --seed 42 --shots 800000
  python phase2_scaling.py --scan            # 全部 L=4/6/8，3 种子
结果：data/phase2/L{L}_s{seed}.json
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qecgeo.error_geometry import (decode_surface, analyze_error_structure,
                                   analyze_edges, edge_maxdist_distribution)


def summarize(res, with_edges=True):
    st = analyze_error_structure(res['dets'], res['coords'], res['le'])
    out = dict(
        pL=float(res['le'].mean()),
        n_ok=int((~res['le']).sum()), n_err=int(res['le'].sum()),
        n_det=res['n_det'], n_qubits=res['circuit'].num_qubits,
        structure=st,
    )
    if with_edges:
        ed = analyze_edges(res['dets'], res['matching'], res['coords'], res['le'])
        out['edges'] = ed
        # 显式长链型分布（Q2）
        dd = edge_maxdist_distribution(res['matching'], res['dets'], res['coords'], res['le'])
        out['longchain'] = dict(
            ok_frac_ge4=float(np.mean([1.0 if m >= 4 else 0.0 for m in dd['ok']])) if dd['ok'] else None,
            err_frac_ge4=float(np.mean([1.0 if m >= 4 else 0.0 for m in dd['err']])) if dd['err'] else None,
            ok_frac_ge6=float(np.mean([1.0 if m >= 6 else 0.0 for m in dd['ok']])) if dd['ok'] else None,
            err_frac_ge6=float(np.mean([1.0 if m >= 6 else 0.0 for m in dd['err']])) if dd['err'] else None,
            ok_maxd_med=float(np.median(dd['ok'])) if dd['ok'] else None,
            err_maxd_med=float(np.median(dd['err'])) if dd['err'] else None,
            ok_maxd_q90=float(np.percentile(dd['ok'], 90)) if dd['ok'] else None,
            err_maxd_q90=float(np.percentile(dd['err'], 90)) if dd['err'] else None,
        )
        # 标度律关键量（Q1）
        td0 = ed['ok'].get('total_dist_med')
        td1 = ed['err'].get('total_dist_med')
        ne0 = ed['ok'].get('n_edges_med')
        ne1 = ed['err'].get('n_edges_med')
        cr0 = st['ok'].get('cross_rate')
        cr1 = st['err'].get('cross_rate')
        out['scaling'] = dict(
            total_dist_A0_med=td0, total_dist_A1_med=td1,
            ratio_total_dist=(td1 / td0) if td0 else None,
            n_edges_A0_med=ne0, n_edges_A1_med=ne1,
            ratio_n_edges=(ne1 / ne0) if ne0 else None,
            cross_A0=cr0, cross_A1=cr1,
            cross_lift=(cr1 / cr0) if cr0 else None,
        )
    return out


def run_one(L, seed, shots, rounds=3, noise=0.005, outdir=None):
    outdir = outdir or os.path.join(os.path.dirname(__file__), '..', 'data', 'phase2')
    os.makedirs(outdir, exist_ok=True)
    outfile = os.path.join(outdir, f'L{L}_s{seed}.json')
    if os.path.exists(outfile):
        print(f'[skip] {outfile}')
        return json.load(open(outfile))
    t0 = time.time()
    res = decode_surface(L, rounds, noise, shots, seed=seed)
    out = summarize(res)
    out['params'] = dict(L=L, rounds=rounds, noise=noise, shots=shots, seed=seed)
    out['wall_s'] = round(time.time() - t0, 1)
    json.dump(out, open(outfile, 'w'), indent=1)
    print(f'[done] L={L} seed={seed} shots={shots} pL={out["pL"]:.4f} '
          f'nA1={out["n_err"]} wall={out["wall_s"]}s')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--L', type=int, default=None)
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--shots', type=int, default=None)
    ap.add_argument('--rounds', type=int, default=3)
    ap.add_argument('--noise', type=float, default=0.005)
    ap.add_argument('--scan', action='store_true', help='全部 L=4/6/8 × 种子 42/123/777')
    args = ap.parse_args()

    if args.scan:
        plan = [(L, s) for L in (4, 6, 8) for s in (42, 123, 777)]
        # shots 预算（A1 样本目标：L=4:300 / L=6:300 / L=8:300，pL 随 L 指数降）
        shots_map = {4: 30000, 6: 300000, 8: 1000000}
        for L, s in plan:
            run_one(L, s, shots_map[L], args.rounds, args.noise)
        # 汇总
        table = []
        for L in (4, 6, 8):
            row = dict(L=L)
            for s in (42, 123, 777):
                try:
                    d = json.load(open(os.path.join(
                        os.path.dirname(__file__), '..', 'data', 'phase2', f'L{L}_s{s}.json')))
                    row[f's{s}_pL'] = d['pL']
                    row[f's{s}_ratio'] = d['scaling']['ratio_total_dist']
                    row[f's{s}_A1td'] = d['scaling']['total_dist_A1_med']
                    row[f's{s}_long4'] = d['longchain']['err_frac_ge4']
                except FileNotFoundError:
                    pass
            table.append(row)
        print(json.dumps(table, indent=1))
        return

    if args.L is None or args.seed is None or args.shots is None:
        print('需 --L --seed --shots，或 --scan')
        return
    run_one(args.L, args.seed, args.shots, args.rounds, args.noise)


if __name__ == '__main__':
    main()
