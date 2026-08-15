"""test_qecgeo.py —— qecgeo 单元测试（unittest，零外部依赖）

覆盖：Pauli 代数、码构造自检、距离验证、阈值闭式（η/A/p_th）、
MC 二次律、任意子 Ising 判定。
"""
import unittest
import numpy as np

from qecgeo.pauli import Pauli
from qecgeo.codes import (five_qubit_code, steane_code, shor_code,
                          rm_code_15_7_3, ALL)
from qecgeo.threshold import analyze_eta, monte_carlo, verify_quadratic
from qecgeo.anyon import delta_phase_analysis, is_ising_statistics


class TestPauli(unittest.TestCase):
    def test_multiplication_table(self):
        """X·Z = -iY, Z·X = iY（反交换）"""
        X, Y, Z = Pauli.X(1, 0), Pauli.Y(1, 0), Pauli.Z(1, 0)
        self.assertEqual(X * Z, Pauli(1, [3], -1j))
        self.assertEqual(Z * X, Pauli(1, [3], 1j))
        self.assertEqual(Y * Y, Pauli.I(1))

    def test_symplectic(self):
        X, Z = Pauli.X(1, 0), Pauli.Z(1, 0)
        self.assertEqual(X.symplectic(Z), 1)
        self.assertEqual(X.symplectic(X), 0)

    def test_from_string(self):
        P = Pauli.from_string(5, 'X1Z2Z3X4')
        self.assertEqual(P.t, [1, 2, 2, 1, 0])
        Q = Pauli.from_string(7, 'XXXXXXX')
        self.assertEqual(Q.t, [1] * 7)

    def test_apply_to_state(self):
        X = Pauli.X(1, 0)
        self.assertTrue(np.allclose(X.apply_to_state([0, 1]), [1, 0]))
        Z = Pauli.Z(1, 0)
        self.assertTrue(np.allclose(Z.apply_to_state([1, 0]), [1, 0]))
        self.assertTrue(np.allclose(Z.apply_to_state([0, 1]), [0, -1]))


class TestCodes(unittest.TestCase):
    def test_all_codes_construct(self):
        """四个码都能构造（StabilizerCode.__init__ 内含自检）"""
        for f in ALL:
            code = f()
            self.assertEqual(code.k, code.n - code.m)
            self.assertEqual(len(code.group), 2 ** code.m)

    def test_distance(self):
        """三个几何码距离 = 3"""
        for f in (five_qubit_code, steane_code, shor_code):
            code = f()
            ok, msg = code.check_distance(3)
            self.assertTrue(ok, f'{code.name}: {msg}')

    def test_logical_zero_stabilized(self):
        """|0_L⟩ 被所有生成元稳定（本征值 +1）"""
        code = steane_code()
        state = code.logical_zero()
        for g in code.gens:
            v = np.vdot(state, g.apply_to_state(state))
            self.assertAlmostEqual(v.real, 1.0, places=6)
            self.assertAlmostEqual(v.imag, 0.0, places=6)

    def test_encode_fidelity(self):
        """编码-纠错-保真度：单比特 X 错误可被纠正"""
        code = steane_code()
        ideal = code.logical_zero()
        E = Pauli.X(code.n, 2)
        corrupted = E.apply_to_state(ideal)
        s = code.measure_syndrome(corrupted)
        recovered = code.correct(corrupted, s)
        self.assertGreater(code.fidelity(recovered, ideal), 0.999)


class TestThreshold(unittest.TestCase):
    def test_eta_finite(self):
        """三个码的 η 枚举：0 < η ≤ 1，p_th 有限"""
        for f in (five_qubit_code, steane_code, rm_code_15_7_3):
            r = analyze_eta(f())
            self.assertGreater(r['eta'], 0.0)
            self.assertLessEqual(r['eta'], 1.0)
            self.assertLess(r['p_th'], float('inf'))
            self.assertAlmostEqual(r['A'], r['eta'] * r['n'] * (r['n'] - 1) / 2)

    def test_steane_eta(self):
        """[7,1,3] 的 η 已知值：7 比特码权重 2 误恢复比例（10.44 复核）"""
        r = analyze_eta(steane_code())
        # 与 10.44 程序复核一致的精确枚举值
        self.assertEqual(r['total'], 9 * 21)  # C(7,2)·9 = 189

    def test_mc_quadratic_law(self):
        """小噪声下 p_L ≈ A·p²（ratio ≈ 1）"""
        code = steane_code()
        r = analyze_eta(code)
        pL = monte_carlo(code, 0.03, n_trials=200000, seed=7)
        ratio = pL / (r['A'] * 0.03 ** 2)
        self.assertAlmostEqual(ratio, 1.0, delta=0.15)

    def test_verify_quadratic_structure(self):
        rows = verify_quadratic(steane_code(), ps=(0.01, 0.05), n_trials=50000)
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIn('pL', row)
            self.assertIn('Ap2', row)


class TestAnyon(unittest.TestCase):
    def test_delta8_closed(self):
        """δ⁸ 净相位 ≡ 0 (mod 2π)"""
        r = delta_phase_analysis()
        self.assertLess(r['delta8_phase_mod2pi'], 1e-9)
        self.assertAlmostEqual(r['delta_phase'], 7 * np.pi / 4)

    def test_ising_statistics(self):
        ok, msg = is_ising_statistics()
        self.assertTrue(ok)
        self.assertIn('Ising', msg)


if __name__ == '__main__':
    unittest.main()
