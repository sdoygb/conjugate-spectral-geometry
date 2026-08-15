#!/usr/bin/env python3
"""demo_threshold.py —— 容错阈值闭式演示（10.44）

用法：cd qec-geometry && python3 scripts/demo_threshold.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qecgeo.codes import five_qubit_code, steane_code, rm_code_15_7_3
from qecgeo.threshold import analyze_eta, verify_quadratic, concatenation_sequence
from qecgeo.anyon import delta_phase_analysis, is_ising_statistics

SEP = "=" * 72


def main():
    print(SEP)
    print("Part A: 权重 2 误恢复比例 η（全枚举）→ 阈值闭式 p_th = 1/(η·C(n,2))")
    print(SEP)
    for f in (five_qubit_code, steane_code, rm_code_15_7_3):
        code = f()
        r = analyze_eta(code)
        print(f"\n{code.name} (n={r['n']})")
        print(f"  权重 2 Pauli 总数        : {r['total']}")
        print(f"  与单比特同 syndrome      : {r['same_as_single']} "
              f"({r['same_as_single']/r['total']:.4f})")
        print(f"  误恢复为逻辑算符         : {r['misrecovered']} "
              f"({r['eta']:.4f})")
        print(f"  组合压缩系数 A=η·C(n,2)  : {r['A']:.4f}")
        print(f"  理想拼接阈值 p_th = 1/A  : {r['p_th']:.4f} "
              f"({r['p_th']*100:.2f}%)")

    print()
    print(SEP)
    print("Part B: 随机 Pauli 噪声 Monte Carlo（[7,1,3]，验证 p_L ≈ A·p²）")
    print(SEP)
    code7 = steane_code()
    A7 = analyze_eta(code7)['A']
    print(f"  理论：p_L(p) ≈ A·p², A = {A7:.4f}, p_th = 1/A = {1/A7:.4f}")
    for row in verify_quadratic(code7):
        print(f"  p={row['p']:5.2f}:  p_L(实测) = {row['pL']:.5e}   "
              f"A·p² = {row['Ap2']:.5e}   p_L/(A·p²) = {row['ratio']:6.3f}")

    print()
    print(f"  拼接压缩 p_{{L+1}} = A·p_L²（p_th = {1/A7:.4f}）：")
    for p0 in (0.001, 0.01, 0.05):
        seq = concatenation_sequence(A7, p0)
        print(f"    p0 = {p0}: " + " → ".join(f"{x:.2e}" for x in seq))

    print()
    print(SEP)
    print("Part C: δ 循环置换的 Majorana 交换相位（Ising 特征，10.43/10.44）")
    print(SEP)
    r = delta_phase_analysis()
    print(f"  8-循环 δ 分解为 {r['n_swaps']} 个相邻对换")
    print(f"  单次对换相位（Ising/Majorana 交换）= e^{{±iπ/4}}")
    print(f"  δ 的净相位 = 7·π/4 = {r['delta_phase']:.6f} rad "
          f"= e^{{i7π/4}} = e^{{-iπ/4}}")
    print(f"  δ⁸ 净相位 = {r['delta8_phase_rad']:.6f} rad mod 2π = "
          f"{r['delta8_phase_mod2pi']:.2e}  ≈ 1（与 Berry 相位 2π 一致 ✓）")
    ok, msg = is_ising_statistics()
    print(f"  判定：{msg}")

    print()
    print(SEP)
    print("完成。")
    print(SEP)


if __name__ == '__main__':
    main()
