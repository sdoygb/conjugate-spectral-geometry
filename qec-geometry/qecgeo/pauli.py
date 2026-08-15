"""pauli.py —— n 比特 Pauli 算符（qecgeo 几何码工具包）

表示：每比特类型 t_i ∈ {0=I, 1=X, 2=Z, 3=Y}，整体相位 ∈ {±1, ±i}。
单比特乘法表由 2×2 矩阵自动生成，避免手写错误。
"""
import numpy as np

# ---------- 单比特乘法表（自动生成） ----------
_I = np.eye(2, dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)
_Y = 1j * _X @ _Z
_MATS = [_I, _X, _Z, _Y]           # t -> 矩阵
_MUL = {}                          # (a, b) -> (c, phase)
for a in range(4):
    for b in range(4):
        M = _MATS[a] @ _MATS[b]
        for c in range(4):
            P = _MATS[c]
            for ph, V in ((1, P), (-1, -P), (1j, 1j * P), (-1j, -1j * P)):
                if np.allclose(M, V):
                    _MUL[a, b] = (c, ph)
                    break
            else:
                continue
            break


class Pauli:
    __slots__ = ('n', 't', 'phase')

    def __init__(self, n, t=None, phase=1):
        self.n = n
        self.t = [0] * n if t is None else list(t)
        self.phase = phase

    # ---------- 构造 ----------
    @classmethod
    def I(cls, n):
        return cls(n)

    @classmethod
    def X(cls, n, i):
        t = [0] * n
        t[i] = 1
        return cls(n, t)

    @classmethod
    def Z(cls, n, i):
        t = [0] * n
        t[i] = 2
        return cls(n, t)

    @classmethod
    def Y(cls, n, i):
        t = [0] * n
        t[i] = 3
        return cls(n, t)

    @classmethod
    def from_string(cls, n, s):
        """'X1Z2Z3X4'（1-based 索引）或 'XXXXXXX'（顺序填充）"""
        t = [0] * n
        j = 0
        i = 0
        while i < len(s):
            ch = s[i]
            if ch in 'XYZI':
                k = i + 1
                while k < len(s) and s[k].isdigit():
                    k += 1
                if k > i + 1:
                    idx = int(s[i + 1:k]) - 1
                else:
                    idx = j
                    j += 1
                t[idx] = {'I': 0, 'X': 1, 'Z': 2, 'Y': 3}[ch]
                i = k
            else:
                i += 1
        return cls(n, t)

    # ---------- 运算 ----------
    def __mul__(self, other):
        n = self.n
        t = [0] * n
        ph = self.phase * other.phase
        for i in range(n):
            c, p = _MUL[self.t[i], other.t[i]]
            t[i] = c
            ph *= p
        return Pauli(n, t, ph)

    def __eq__(self, other):
        return (self.n == other.n and self.t == other.t
                and np.isclose(self.phase, other.phase))

    def weight(self):
        return sum(1 for x in self.t if x)

    def symplectic(self, other):
        """symplectic 内积 mod 2：1 ⟺ 反交换"""
        s = 0
        for i in range(self.n):
            xi = 1 if self.t[i] in (1, 3) else 0
            zi = 1 if self.t[i] in (2, 3) else 0
            xo = 1 if other.t[i] in (1, 3) else 0
            zo = 1 if other.t[i] in (2, 3) else 0
            s += xi * zo + zi * xo
        return s % 2

    def commutes(self, other):
        return self.symplectic(other) == 0

    # ---------- 态矢量作用 ----------
    def apply_to_state(self, state):
        """|ψ⟩ -> P|ψ⟩（约定：索引最高位 = 比特 0）

        单比特实现：Z 相位 -> X 翻转 -> （Y 型补因子 i），
        即 Y = iXZ = i·(先 Z 后 X)。
        """
        out = np.array(state, dtype=complex).copy()
        n = self.n
        for i in range(n):
            ti = self.t[i]
            if ti == 0:
                continue
            bit = n - 1 - i
            out = out.reshape(-1, 2, 1 << bit)
            if ti in (2, 3):            # Z：相位
                out[:, 1, :] *= -1
            if ti in (1, 3):            # X：翻转
                out = out[:, ::-1, :].copy()
                if ti == 3:             # Y = iXZ：补因子 i
                    out = out * 1j
        return (self.phase * out).reshape(-1)

    def __repr__(self):
        parts = []
        for i in range(self.n):
            parts.append('IXZY'[self.t[i]] + str(i + 1))
        ph = '' if self.phase == 1 else (str(self.phase) + '·')
        return ph + ''.join(parts)
