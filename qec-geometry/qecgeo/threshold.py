"""threshold.py —— 容错阈值闭式（10.44）

理论：单轮最优纠错下，逻辑错误率 p_L(p) ≈ A·p²（A = η·C(n,2)），
其中 η = 权重 2 错误被误恢复为逻辑算符的比例（全枚举精确计算）。
理想拼接阈值 p_th = 1/A（p_L = 1 的渐近点）。

模块内容：
  - weight2_errors(code)        全部非平凡权重 2 Pauli 错误
  - analyze_eta(code)           精确枚举 η、A、p_th
  - monte_carlo(code, p, ...)   随机 Pauli 噪声 MC 逻辑错误率
  - verify_quadratic(code, ps)  p_L 实测 vs A·p² 对照
  - concatenation_sequence(A, p0, L)  拼接压缩序列
"""
import numpy as np
from itertools import combinations
from .pauli import Pauli


def weight2_errors(code):
    """全部非平凡权重 2 Pauli 错误（9 个 X/Z/Y 组合每对坐标）"""
    n = code.n
    errs = []
    for a, b in combinations(range(n), 2):
        for ta in (1, 2, 3):
            for tb in (1, 2, 3):
                t = [0] * n
                t[a], t[b] = ta, tb
                errs.append(Pauli(n, t))
    return errs


def analyze_eta(code):
    """精确枚举：权重 2 误恢复比例 η → 组合压缩系数 A → 阈值 p_th

    返回 dict：n, total, same_as_single, misrecovered, eta, resid_w3, A, p_th
    """
    n, m = code.n, code.m
    w2 = weight2_errors(code)
    total = len(w2)
    singles = []
    for i in range(n):
        for P in (Pauli.X(n, i), Pauli.Z(n, i), Pauli.Y(n, i)):
            singles.append(P)
    single_synd = set(code.syndrome_of(P) for P in singles)

    same_as_single = 0          # 与某单比特同 syndrome
    misrecovered = 0            # 查表恢复后残留为逻辑算符
    resid_weight3_logical = 0   # 残留为权重 3 逻辑

    for E in w2:
        s = code.syndrome_of(E)
        if s in single_synd:
            same_as_single += 1
            R = code.decode(s)                 # 单比特查表恢复
            Eres = R * E                        # 残留
            is_logical = all(Eres.commutes(g) for g in code.gens) \
                and not code.in_group(Eres)
            if is_logical:
                misrecovered += 1
                wt = sum(1 for t in Eres.t if t != 0)
                if wt == 3:
                    resid_weight3_logical += 1

    eta = misrecovered / total
    # 标准模型：每比特错误率 p，X/Y/Z 各 p/3。
    # 权重 2 错误总概率 = 9·C(n,2)·(p/3)² = C(n,2)·p²
    # 其中被误恢复的比例 = misrecovered/total = eta
    # → p_L = eta·C(n,2)·p²  ✓
    A = eta * n * (n - 1) / 2.0
    return dict(n=n, total=total, same_as_single=same_as_single,
                misrecovered=misrecovered, eta=eta,
                resid_w3=resid_weight3_logical,
                A=A,
                p_th=1.0 / A if A > 0 else float('inf'))


def monte_carlo(code, p, n_trials=300000, seed=42):
    """每比特独立 Pauli 噪声（X/Y/Z 各 p/3），单轮查表纠错，逻辑错误率"""
    rng = np.random.default_rng(seed)
    n = code.n
    n_logical_err = 0
    for _ in range(n_trials):
        E = Pauli.I(n)
        for i in range(n):
            r = rng.random()
            if r < p / 3:
                E = E * Pauli.X(n, i)
            elif r < 2 * p / 3:
                E = E * Pauli.Z(n, i)
            elif r < p:
                E = E * Pauli.Y(n, i)
        if all(t == 0 for t in E.t):
            continue  # 无错误
        s = code.syndrome_of(E)
        R = code.decode(s)
        Eres = R * E
        is_logical = all(Eres.commutes(g) for g in code.gens) \
            and not code.in_group(Eres)
        if is_logical:
            n_logical_err += 1
    return n_logical_err / n_trials


def verify_quadratic(code, ps=(0.01, 0.03, 0.05, 0.08, 0.10, 0.14, 0.20),
                     n_trials=300000, seed=42):
    """p_L 实测 vs A·p² 对照表（验证二次律 p_L ≈ A·p²）

    返回 list[dict(p, pL, Ap2, ratio)]，ratio = pL/(A·p²)
    """
    A = analyze_eta(code)['A']
    out = []
    for p in ps:
        pL = monte_carlo(code, p, n_trials=n_trials, seed=seed)
        out.append(dict(p=p, pL=pL, Ap2=A * p * p,
                        ratio=pL / (A * p * p) if p > 0 else 0.0))
    return out


def concatenation_sequence(A, p0, levels=4):
    """拼接压缩 p_{L+1} = A·p_L²（p_th = 1/A 以下指数压缩）"""
    seq = [p0]
    p = p0
    for _ in range(levels):
        p = A * p * p
        seq.append(p)
    return seq
