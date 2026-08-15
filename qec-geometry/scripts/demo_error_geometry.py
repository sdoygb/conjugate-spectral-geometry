#!/usr/bin/env python3
"""demo_error_geometry.py —— surface code 错误模式几何分类演示（10.54）

用法：cd qec-geometry && python3 scripts/demo_error_geometry.py [--L 4] [--shots 20000]
依赖：stim + pymatching

重要参数说明：A0/A1 几何区分在阈值以下显现（surface code p≈0.005 < 阈值≈0.011）。
默认 noise=0.005 复现 10.54 的配对层 total_dist A1/A0 = 3.00×；高噪声（如 0.03，
远超阈值）下错误模式失去结构、区分度消失（10.54 发现的物理行为）。
"""
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qecgeo.error_geometry import run_error_geometry


def fmt(v):
    return "-" if v is None else f"{v:8.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, default=4)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--noise", type=float, default=0.005,
                    help="噪声率（10.54 的 3.00× 强区分在阈值以下 noise=0.005 显现）")
    ap.add_argument("--shots", type=int, default=20000)
    ap.add_argument("--no-edges", action="store_true", help="跳过配对边分析")
    args = ap.parse_args()

    print("=== surface code 解码 + 错误模式几何分类（A0/A1）===")
    print(f"L={args.L}, rounds={args.rounds}, noise={args.noise}, shots={args.shots}")
    print("注: A0/A1 几何区分在阈值以下（surface code p≈0.005 < 阈值≈0.011）显现；"
          "高噪声下错误模式失去结构、区分度消失（10.54 发现）")
    out = run_error_geometry(args.L, args.rounds, args.noise, args.shots,
                             with_edges=not args.no_edges)
    print(f"电路: {out['n_qubits']} qubits, {out['n_det']} detectors")
    print(f"逻辑错误率 pL = {out['pL']:.5f}")

    print("\n=== 激发层特征（A0 可修正 vs A1 逻辑错误）===")
    st = out['structure']
    print("特征              A0(med)  A0(q90)  A1(med)  A1(q90)")
    for field in ("exc", "min_pair", "diam", "bdry", "cluster"):
        a0m, a0q = st['ok'].get(field + "_med"), st['ok'].get(field + "_q90")
        a1m, a1q = st['err'].get(field + "_med"), st['err'].get(field + "_q90")
        print(f"  {field:10s} {fmt(a0m):>8s} {fmt(a0q):>8s} {fmt(a1m):>8s} {fmt(a1q):>8s}")
    c0, c1 = st['ok'].get('cross_rate'), st['err'].get('cross_rate')
    fmtp = lambda v: "-" if v is None else f"{v*100:7.1f}%"
    print(f"  {'cross':10s} {fmtp(c0):>8s} {'':>8s} {fmtp(c1):>8s} {'':>8s}")
    print(f"\n样本数: A0={st['ok']['n']}, A1={st['err']['n']}")

    if out['edges'] is not None:
        print("\n=== MWPM 配对边（纯链）特征 ===")
        st2 = out['edges']
        print("特征              A0(med)  A0(q90)  A1(med)  A1(q90)")
        for field in ("n_edges", "bdry_edges", "total_dist", "max_dist", "long_rate"):
            a0m, a0q = st2['ok'].get(field + "_med"), st2['ok'].get(field + "_q90")
            a1m, a1q = st2['err'].get(field + "_med"), st2['err'].get(field + "_q90")
            fmt2 = lambda v: "-" if v is None else f"{v:8.2f}"
            print(f"  {field:10s} {fmt2(a0m):>8s} {fmt2(a0q):>8s} {fmt2(a1m):>8s} {fmt2(a1q):>8s}")

    print("\n=== A1/A0 区分度判定 ===")
    for r in out['ratios']:
        if r['ratio'] is None:
            print(f"  {r['field']:10s} 无区分度（均为 0）")
            continue
        print(f"  {r['field']:10s} A1/A0 = {r['ratio']:6.2f} {r['direction']}  "
              f"{r['verdict']}")
    if out['cross_lift'] is not None:
        print(f"  cross      穿越率提升 = {out['cross_lift']:6.2f}×  "
              f"{'★ A1 本质特征' if out['cross_lift'] > 3 else '弱'}")
    print("\n注: A0=局域错误链（平凡拓扑）；A1=跨边界非平凡链（逻辑错误）")


if __name__ == '__main__':
    main()
