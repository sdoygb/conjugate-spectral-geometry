"""stabilizer.py —— 稳定子码框架（geo_qec 几何码工具包）

编码 |ψ_L⟩、syndrome 测量、解码（查表）、纠错、保真度、距离验证。
对应：10.27 命题 3.13–3.15（几何码构造，O5 程序复核）。
"""
import numpy as np
from itertools import product, combinations
from pauli import Pauli


class StabilizerCode:
    def __init__(self, name, gens, lx, lz):
        self.name = name
        self.gens = gens
        self.lx, self.lz = lx, lz
        self.n = gens[0].n
        self.m = len(gens)
        self.k = self.n - self.m
        self._check()
        self._build_group()
        self._build_table()
        self._cached_zero = None

    # ---------- 自检 ----------
    def _check(self):
        for i in range(self.m):
            for j in range(i + 1, self.m):
                assert self.gens[i].commutes(self.gens[j]), \
                    f'{self.name}: 生成元 {i+1},{j+1} 不对易'
        for g in self.gens:
            assert self.lx.commutes(g) and self.lz.commutes(g), \
                f'{self.name}: 逻辑算符与生成元不对易'
        assert not self.lx.commutes(self.lz), \
            f'{self.name}: X̄ 与 Z̄ 对易'
        # 独立性：symplectic 矩阵秩 = m
        M = np.zeros((self.m, 2 * self.n), dtype=int)
        for r, g in enumerate(self.gens):
            for i in range(self.n):
                M[r, i] = 1 if g.t[i] in (1, 3) else 0           # x 部分
                M[r, self.n + i] = 1 if g.t[i] in (2, 3) else 0  # z 部分
        rank = np.linalg.matrix_rank(M)
        assert rank == self.m, f'{self.name}: 生成元不独立 (秩 {rank} < {self.m})'

    # ---------- 稳定子群 ----------
    def _build_group(self):
        elems = [Pauli.I(self.n)]
        for g in self.gens:
            elems = elems + [e * g for e in elems]
        assert len(elems) == 2 ** self.m
        self.group = elems

    def in_group(self, E):
        return any(E == s for s in self.group)

    # ---------- syndrome ----------
    def syndrome_of(self, E):
        return tuple(E.symplectic(g) for g in self.gens)

    def measure_syndrome(self, state):
        """物理测量：对稳定子本征态返回 ±1 本征值向量（0/1）"""
        s = []
        for g in self.gens:
            v = np.vdot(state, g.apply_to_state(state))
            s.append(0 if v.real > 0 else 1)
        return tuple(s)

    # ---------- 解码 ----------
    def _build_table(self):
        """单比特错误查表：syndrome -> 权重最小错误"""
        self.table = {}
        for i in range(self.n):
            for P in (Pauli.X(self.n, i), Pauli.Z(self.n, i), Pauli.Y(self.n, i)):
                s = self.syndrome_of(P)
                if s not in self.table:
                    self.table[s] = P

    def decode(self, syndrome):
        return self.table.get(syndrome, Pauli.I(self.n))

    def correct(self, state, syndrome):
        return self.decode(syndrome).apply_to_state(state)

    # ---------- 编码 ----------
    def logical_zero(self):
        if self._cached_zero is None:
            state = np.zeros(2 ** self.n, dtype=complex)
            state[0] = 1.0
            acc = np.zeros_like(state)
            for s in self.group:
                acc += s.apply_to_state(state)
            acc /= np.linalg.norm(acc)
            self._cached_zero = acc
        return self._cached_zero.copy()

    def logical_one(self):
        return self.lx.apply_to_state(self.logical_zero())

    def encode(self, alpha=1.0, beta=0.0):
        return alpha * self.logical_zero() + beta * self.logical_one()

    def fidelity(self, state, ideal):
        return abs(np.vdot(ideal, state)) ** 2

    # ---------- 距离验证 ----------
    def check_distance(self, d_target):
        """权重 < d_target 无可遗漏错误；权重 = d_target 存在逻辑算符"""
        n, m = self.n, self.m
        zero_s = (0,) * m
        for w in range(1, d_target):
            for idxs in combinations(range(n), w):
                for types in product((1, 2, 3), repeat=w):
                    t = [0] * n
                    for idx, ty in zip(idxs, types):
                        t[idx] = ty
                    E = Pauli(n, t)
                    if self.syndrome_of(E) == zero_s and not self.in_group(E):
                        return False, f'权重 {w} 存在未检测错误'
        for idxs in combinations(range(n), d_target):
            for types in product((1, 2, 3), repeat=d_target):
                t = [0] * n
                for idx, ty in zip(idxs, types):
                    t[idx] = ty
                E = Pauli(n, t)
                if self.syndrome_of(E) == zero_s and not self.in_group(E):
                    return True, f'd = {d_target}（如 {E}）'
        return False, f'权重 {d_target} 未找到逻辑算符（距离 > {d_target}？）'
