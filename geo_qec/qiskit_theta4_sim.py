#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qiskit_theta4_sim.py — 10.29 θ⁴ 损失标度律的 Qiskit Aer 本地模拟

对应文章:
  10.28 §6 O6 / 10.29 §4-5
  预言: 相干单比特旋转注入下, 最优纠错后损失 L ~ θ_max⁴ (log-log 斜率 ≈ 4)
  对照: 随机 Pauli (非相干) 噪声下损失 ~ p² (斜率 → 2)

本脚本使用 Qiskit Aer statevector 模拟:
  1. 制备逻辑零态 |0_L>
  2. 对每个物理比特施加相干旋转 U(θ) = cos(θ/2)·I + i·sin(θ/2)·E
  3. 用查表恢复计算最优纠错后保真度
  4. 扫描 θ_max 并拟合 log-log 斜率

运行:
  python3 qiskit_theta4_sim.py
"""
import numpy as np
from itertools import combinations, product

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector, Operator

# ---------- 码定义（与 geo_qec/codes.py 一致） ----------

def pauli_matrix(n, t):
    """t: list of int, 0=I 1=X 2=Z 3=Y（按 Pauli 习惯）"""
    eye = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    Y = 1j * X @ Z
    mats = [eye, X, Z, Y]
    M = np.array([1.0])
    for ty in t:
        M = np.kron(M, mats[ty])
    return M


def symplectic(P, Q):
    """两个 Pauli 串是否对易：True=对易, False=反对易"""
    n = len(P)
    phase = 1
    for i in range(n):
        if P[i] == 0 or Q[i] == 0:
            continue
        # 只有 X 与 Z 或 Y 与 Z 等非对易需要处理；这里简化用矩阵乘积迹判断
        pass
    # 直接用矩阵对易关系判断（小 n 够用）
    MP = pauli_matrix(n, P)
    MQ = pauli_matrix(n, Q)
    return np.allclose(MP @ MQ, MQ @ MP)


def syndrome_of(E, gens):
    return tuple(int(not symplectic(E, g)) for g in gens)


def five_qubit_code():
    n = 5
    gens = [
        [0, 1, 2, 2, 1],  # X Z Z X I  (1=X,2=Z)
        [1, 0, 1, 2, 2],  # I X Z Z X
        [2, 1, 0, 1, 2],  # X I X Z Z
        [2, 2, 1, 0, 1],  # Z X I X Z
    ]
    lx = [1, 1, 1, 1, 1]
    lz = [2, 2, 2, 2, 2]
    return n, gens, lx, lz


def steane_code():
    n = 7
    H = [
        [0, 0, 0, 1, 1, 1, 1],
        [0, 1, 1, 0, 0, 1, 1],
        [1, 0, 1, 0, 1, 0, 1],
    ]
    gens = []
    for row in H:
        gens.append([1 if b else 0 for b in row])
    for row in H:
        gens.append([2 if b else 0 for b in row])
    lx = [1] * n
    lz = [2] * n
    return n, gens, lx, lz


def shor_code():
    n = 9
    gens = [
        [2, 2, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 2, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 2, 2, 0],
        [0, 0, 0, 0, 0, 0, 0, 2, 2],
        [1, 1, 1, 1, 1, 1, 0, 0, 0],
        [1, 1, 1, 0, 0, 0, 1, 1, 1],
    ]
    lx = [1, 1, 1, 0, 0, 0, 0, 0, 0]
    lz = [2, 0, 0, 2, 0, 0, 2, 0, 0]
    return n, gens, lx, lz


# ---------- 逻辑零态 / 码空间投影 ----------

def group_projection(gens, v):
    n = len(gens[0])
    dim = 2 ** n
    w = np.zeros(dim, complex)
    # 枚举 stabilizer 群（小码 2^m 项）
    elems = [np.zeros(n, dtype=int)]
    for g in gens:
        new = []
        for e in elems:
            # 逐位乘 Pauli：I=0, X=1, Z=2, Y=3
            t = []
            for a, b in zip(e, g):
                if a == 0:
                    t.append(b)
                elif b == 0:
                    t.append(a)
                elif a == b:
                    t.append(0)  # P^2 = I
                else:
                    # XZ=-iY, ZX=iY, XY=iZ, YX=-iZ, YZ=iX, ZY=-iX
                    # 这里只做投影，整体相位不影响码空间；用简单规则
                    # 为了正确性，直接用矩阵生成群元素相位太繁琐；
                    # 此处用 stabilizer 矩阵乘法并追踪相位（简化为 0/1/2/3）
                    # 对 X,Z,Y 的乘法表:
                    # X*Z=Y? 实际 XZ = -iY, 但群投影只需要生成元集合。
                    # 为稳妥，改用穷举 stabilizer 矩阵乘积（见下）
                    pass
            new.append(t)
        # 上面太复杂，直接使用矩阵乘法生成群元素
        elems = None
        break
    # 更稳妥：用矩阵乘法枚举 stabilizer 群
    mats = [pauli_matrix(n, g) for g in gens]
    group_mats = [np.eye(dim, dtype=complex)]
    for M in mats:
        group_mats = group_mats + [G @ M for G in group_mats]
    w = sum(G @ v for G in group_mats)
    return w


def logical_zero(n, gens):
    rng = np.random.default_rng(0)
    dim = 2 ** n
    v = rng.standard_normal(dim) + 1j * rng.standard_normal(dim)
    w = group_projection(gens, v)
    w /= np.linalg.norm(w)
    return w


def code_projector(n, gens, lx, psi0):
    psi1 = pauli_matrix(n, lx) @ psi0
    P = np.outer(psi0, psi0.conj()) + np.outer(psi1, psi1.conj())
    return P, psi1


def recovery_table(n, gens):
    table = {}
    zero = (0,) * len(gens)
    for w in (1, 2, 3):
        for idxs in combinations(range(n), w):
            for types in product((1, 2, 3), repeat=w):
                t = [0] * n
                for idx, ty in zip(idxs, types):
                    t[idx] = ty
                s = syndrome_of(t, gens)
                if s != zero and s not in table:
                    table[s] = t
    assert len(table) == 2 ** len(gens) - 1, f'覆盖不全 {len(table)}'
    return table


def optimal_recovery_fidelity(psi_ideal, psi_noisy, P0, table):
    F = abs(np.vdot(psi_ideal, psi_noisy)) ** 2
    for E in table.values():
        amp = np.vdot(psi_ideal, pauli_matrix(len(psi_ideal).bit_length() - 1, E) @ psi_noisy)
        F += abs(amp) ** 2
    return F


def rotation_matrix(n, t, theta):
    E = pauli_matrix(n, t)
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return c * np.eye(2 ** n) + 1j * s * E


def single_qubit_rotation_matrix(ty, theta):
    eye = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    Y = 1j * X @ Z
    mats = [eye, X, Z, Y]
    E = mats[ty]
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return c * eye + 1j * s * E


# ---------- Qiskit Aer 模拟 ----------

def simulate_state(psi0, rotations):
    """rotations: list[(qubit_index, Pauli_type, theta)]"""
    n = int(np.log2(len(psi0)))
    qc = QuantumCircuit(n)
    qc.initialize(psi0, range(n))
    for i, ty, th in rotations:
        qc.unitary(single_qubit_rotation_matrix(ty, th), [i])
    qc.save_statevector()
    sim = AerSimulator(method='statevector')
    qc = transpile(qc, sim)
    result = sim.run(qc, shots=1).result()
    return result.get_statevector(qc).data


def run_pauli_control(code_name='[[7,1,3]]', ps=(0.02, 0.04, 0.08, 0.16), trials=100, seed=1):
    """随机 Pauli 信道对照组：损失 ~ p²，log-log 斜率 ≈ 2"""
    if code_name == '[[5,1,3]]':
        n, gens, lx, lz = five_qubit_code()
    elif code_name == '[[7,1,3]]':
        n, gens, lx, lz = steane_code()
    else:
        n, gens, lx, lz = shor_code()

    psi0 = logical_zero(n, gens)
    P0, _ = code_projector(n, gens, lx, psi0)
    table = recovery_table(n, gens)
    rng = np.random.default_rng(seed)

    losses = []
    for p in ps:
        Ls = []
        for _ in range(trials):
            psi = psi0.copy()
            for i in range(n):
                if rng.random() < p:
                    ty = int(rng.integers(1, 4))
                    t = [0] * n
                    t[i] = ty
                    psi = pauli_matrix(n, t) @ psi
            F = optimal_recovery_fidelity(psi0, psi, P0, table)
            Ls.append(max(0.0, 1 - F))
        losses.append(float(np.mean(Ls)))

    x = np.log(np.array(ps, float))
    y = np.log(np.maximum(losses, 1e-16))
    slope, intercept = np.polyfit(x, y, 1)
    return losses, slope, intercept


def run_theta4(code_name='[[5,1,3]]', thetas=(0.05, 0.1, 0.2, 0.4), trials=10, seed=0):
    if code_name == '[[5,1,3]]':
        n, gens, lx, lz = five_qubit_code()
    elif code_name == '[[7,1,3]]':
        n, gens, lx, lz = steane_code()
    else:
        n, gens, lx, lz = shor_code()

    psi0 = logical_zero(n, gens)
    P0, _ = code_projector(n, gens, lx, psi0)
    table = recovery_table(n, gens)
    rng = np.random.default_rng(seed)

    losses = []
    for tm in thetas:
        Ls = []
        for _ in range(trials):
            rotations = []
            for i in range(n):
                ty = int(rng.integers(1, 4))
                th = float(rng.uniform(0, tm))
                rotations.append((i, ty, th))
            psi_noisy = simulate_state(psi0, rotations)
            F = optimal_recovery_fidelity(psi0, psi_noisy, P0, table)
            Ls.append(max(0.0, 1 - F))
        losses.append(float(np.mean(Ls)))

    x = np.log(np.array(thetas, float))
    y = np.log(np.maximum(losses, 1e-16))
    slope, intercept = np.polyfit(x, y, 1)
    return losses, slope, intercept


def main():
    print('10.29 θ⁴ 损失标度律 — Qiskit Aer 本地模拟')
    print('=' * 72)
    for code in ['[[5,1,3]]', '[[7,1,3]]']:
        losses, slope, _ = run_theta4(code, trials=10, seed=42)
        print(f'{code}: loss={["%.2e" % L for L in losses]}, log-log slope={slope:.2f}')
    print('预期: 斜率 ≈ 4 (相干旋转 θ⁴)')

    print('-' * 72)
    print('随机 Pauli 信道对照组 (损失 ~ p², 以 [[7,1,3]] 为例)')
    losses, slope, _ = run_pauli_control('[[7,1,3]]', trials=100, seed=7)
    print(f'[[7,1,3]]: loss={["%.2e" % L for L in losses]}, log-log slope={slope:.2f}')
    print('预期: 斜率 ≈ 2 (随机 Pauli 噪声)')


if __name__ == '__main__':
    main()
