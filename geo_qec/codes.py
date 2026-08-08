"""codes.py —— 三个几何码（10.27 命题 3.13–3.15）"""
from pauli import Pauli
from stabilizer import StabilizerCode


def five_qubit_code():
    """[[5,1,3]] 五比特码 —— 10.27 式 (4.16)，结构常数 ΔΘ=5（循环 Z₅ 对称）

    逻辑算符：all-zero 参考基（|0_L⟩ ∝ Σ_{s∈S}s|00000⟩）下 X 类由 X⊗5
    承载、Z 类由 Z⊗5 承载（已验证）；10.27 注的 X̄=X₁Y₂X₃ 为该基下的
    X̄Z̄ 类代表（作用在 |0_L⟩ 上与 X̄ 相同），Z̄=Z₁X₂Z₃ 为 X 类代表。
    """
    n = 5
    gens = [
        Pauli.from_string(n, 'X1Z2Z3X4'),
        Pauli.from_string(n, 'X2Z3Z4X5'),
        Pauli.from_string(n, 'X3Z4Z5X1'),
        Pauli.from_string(n, 'X4Z5Z1X2'),
    ]
    lx = Pauli.from_string(n, 'X1X2X3X4X5')
    lz = Pauli.from_string(n, 'Z1Z2Z3Z4Z5')
    return StabilizerCode('[[5,1,3]] 五比特码（ΔΘ=5）', gens, lx, lz)


def steane_code():
    """[[7,1,3]] Steane 码 —— 10.27 式 (4.17)，七层截断 / Fano 平面 7 线"""
    n = 7
    H = [(0, 0, 0, 1, 1, 1, 1),
         (0, 1, 1, 0, 0, 1, 1),
         (1, 0, 1, 0, 1, 0, 1)]
    gens = []
    for row in H:                                    # X 型（CSS）
        gens.append(Pauli(n, [1 if b else 0 for b in row]))
    for row in H:                                    # Z 型（CSS）
        gens.append(Pauli(n, [2 if b else 0 for b in row]))
    lx = Pauli.from_string(n, 'X' * n)
    lz = Pauli.from_string(n, 'Z' * n)
    return StabilizerCode('[[7,1,3]] Steane 码（七层/Fano）', gens, lx, lz)


def shor_code():
    """[[9,1,3]] Shor 码 —— 10.27 命题 3.15，素三分解 3×3（组内 Z 型 + 组间 X 型）

    逻辑算符：all-zero 参考基下 X 类由 X₁X₂X₃ 承载、Z 类由 Z₁Z₄Z₇ 承载
    （10.27 命题 3.15(ii) 的 GHZ 基命名相反——X̄=Z₁Z₄Z₇、Z̄=X₁X₂X₃，
    见文章基规范注）。
    """
    n = 9
    gens = [
        Pauli.from_string(n, 'Z1Z2'), Pauli.from_string(n, 'Z2Z3'),
        Pauli.from_string(n, 'Z4Z5'), Pauli.from_string(n, 'Z5Z6'),
        Pauli.from_string(n, 'Z7Z8'), Pauli.from_string(n, 'Z8Z9'),
        Pauli.from_string(n, 'X1X2X3X4X5X6'),
        Pauli.from_string(n, 'X1X2X3X7X8X9'),
    ]
    lx = Pauli.from_string(n, 'X1X2X3')
    lz = Pauli.from_string(n, 'Z1Z4Z7')
    return StabilizerCode('[[9,1,3]] Shor 码（3×3 素三分解）', gens, lx, lz)


ALL = [five_qubit_code, steane_code, shor_code]
