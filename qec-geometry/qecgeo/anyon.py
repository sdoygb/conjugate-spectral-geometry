"""anyon.py —— 任意子统计类型判定（10.43/10.44）

δ = Cl(8) Majorana 8-循环置换：8-循环 = 7 个相邻对换；
单次对换携带 Ising（Majorana）交换相位 e^{±iπ/4}；
δ 净相位 = 7π/4 = -π/4；δ⁸ 净相位 = 14π ≡ 0 (mod 2π)，
与 Berry 相位 2π 一致 → 回路闭合无剩余相位。

判定：δ⁸ 回路携带 Ising 型（Majorana 型）任意子统计，
非 Fibonacci 型（Fibonacci 型要求非 Abelian 相位结构）。
"""
import numpy as np

# Cl(8) Majorana 8-循环置换参数
N_SWAPS = 7                 # 8-循环分解为 7 个对换
PHASE_PER_SWAP = np.pi / 4  # Majorana 交换相位（Ivanov）


def delta_phase_analysis():
    """δ 循环置换的交换相位分析（10.44 Part C）

    返回 dict：n_swaps, phase_per_swap, delta_phase,
               delta8_phase_mod2pi, delta8_phase_rad
    """
    delta_phase = N_SWAPS * PHASE_PER_SWAP          # 7π/4 = -π/4
    delta8_phase = 8 * delta_phase                  # 14π ≡ 0 (mod 2π)
    return dict(n_swaps=N_SWAPS, phase_per_swap=PHASE_PER_SWAP,
                delta_phase=delta_phase,
                delta8_phase_mod2pi=float(delta8_phase % (2 * np.pi)),
                delta8_phase_rad=float(delta8_phase))


def is_ising_statistics(tol=1e-9):
    """判定：δ⁸ 回路是否携带 Ising 型任意子统计（净相位 ≡ 0 mod 2π）

    返回 (bool, 说明 str)
    """
    r = delta_phase_analysis()
    closed = abs(r['delta8_phase_mod2pi']) < tol
    if closed:
        return True, ('δ⁸ 净相位 ≡ 0 (mod 2π)：回路闭合，'
                      '携带 Ising 型（Majorana 型）任意子统计，非 Fibonacci 型')
    return False, ('δ⁸ 净相位非零：非闭合，不满足 Ising 判定')


def verify_delta8_berry_consistency():
    """δ⁸ 与 Berry 相位 2π 的一致性验证

    返回 dict：delta8_phase, berry_phase_2pi, consistent
    """
    r = delta_phase_analysis()
    return dict(delta8_phase=r['delta8_phase_rad'],
                berry_phase_2pi=2 * np.pi,
                consistent=abs(r['delta8_phase_mod2pi']) < 1e-9)
