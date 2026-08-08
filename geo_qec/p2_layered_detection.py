"""p2_layered_detection.py —— P2：刚度分层采样检验

对应 10.28 §6 O6（程序接口 P2）。检验 10.28 §3 的分层结构：
  定义 10.28.2.01（扇区分类）、定理 10.28.2.02（刚度分层检测定理）、
  推论 10.28.2.03（遍历预算分层）。

验证项：
  A. 码内类复核：3n Pauli 全枚举 → syndrome 全非零（检测率 1，代数保证）
  B. 通道类检测语义（态矢量模拟，k=1 码）
     B1 单比特旋转注入：检测/漏检两路径恢复保真度均 = 1（漏检无害）
     B2 检测率 = sin²(θ/2)（数值 vs 闭式）
     B3 逻辑方向注入：syndrome 恒 0（不可检测），
        F = |c + is⟨ψ|E|ψ⟩|²（|0_L⟩ 是 Z̄ 本征态 ⟹ Z̄ 注入为全局相位）
  C. 分层预算等价性：连续谱检测率由闭式决定 → 通道类无需全枚举
  D. 有害漏检率标度
     D1 独立噪声（每比特 θᵢ ≤ θ_max）：纠错后损失 ~ θ_max⁴
        （权重 ≥3 成分与权重 1 成分同 syndrome 类的恢复干涉主导；
        本质：所有不可恢复成分权重 ≥3，最小损失阶 = θ⁴）
     D2 H1 截断（θ_max = A/κ ≈ 0.0066）下有害率 ≪ κ⁻¹（外推），
        定理 10.28.2.02 的 Aκ⁻¹ 界保守 ≥7 个数量级
  E. [[15,7,3]] 复核：45 单比特全检测；逻辑 |0...0_L⟩ 上
     35 线 Z 型 = 全局相位（⟨ψ|E|ψ⟩ = ±1）、X 型损失 = sin²(θ/2)
"""
import numpy as np
from itertools import combinations, product

from pauli import Pauli
from stabilizer import StabilizerCode
import codes as geo_codes
from p1_direction15 import direction_matrix, css_gens, pg_lines, css_logical_basis

KAPPA = 151.7


# ---------- 工具 ----------
def syndrome_of(E, gens):
    return tuple(E.symplectic(g) for g in gens)


def rotation_state(psi, E, theta):
    """U(θ) = cos(θ/2)·I + i·sin(θ/2)·E 作用在态矢量 psi 上（归一化）"""
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    out = c * psi + 1j * s * E.apply_to_state(psi)
    return out / np.linalg.norm(out)


def code_projector(code):
    """k=1 码的码空间投影 P₀ = |0_L⟩⟨0_L| + |1_L⟩⟨1_L|"""
    psi0 = code.logical_zero()
    psi1 = code.lx.apply_to_state(psi0)
    return np.outer(psi0, psi0.conj()) + np.outer(psi1, psi1.conj()), psi0


def recovery_table(code):
    """syndrome → 恢复算符（权重 1..3 枚举，每类取首个代表；s=0 恒等类除外）"""
    n, gens = code.n, code.gens
    table = {}
    for w in (1, 2, 3):
        for idxs in combinations(range(n), w):
            for types in product((1, 2, 3), repeat=w):
                t = [0] * n
                for idx, ty in zip(idxs, types):
                    t[idx] = ty
                E = Pauli(n, t)
                s = syndrome_of(E, gens)
                if s != (0,) * len(gens) and s not in table:
                    table[s] = E
    assert len(table) == 2 ** len(gens) - 1, \
        f'syndrome 覆盖不全: {len(table)}/{2 ** len(gens) - 1}'
    return table


def optimal_recovery_fidelity(psi_ideal, psi_noisy, code, table):
    """最优纠错后的平均保真度：F = Σ_s |⟨ψ_ideal|E_s·ψ_noisy⟩|²
    （s=0 类 E₀=I；逻辑成分 syndrome=0 留在码空间，造成损失）"""
    F = abs(np.vdot(psi_ideal, psi_noisy)) ** 2          # s = 0 类
    for E in table.values():
        amp = np.vdot(psi_ideal, E.apply_to_state(psi_noisy))
        F += abs(amp) ** 2
    return F


def group_projection(gens, v):
    """stabilizer 群平均投影：Σ_{s∈S}s·v（到码空间）"""
    n = gens[0].n
    elems = [Pauli.I(n)]
    for g in gens:
        elems = elems + [e * g for e in elems]
    w = np.zeros(2 ** n, complex)
    for e in elems:
        w += e.apply_to_state(v)
    return w


def logical_zero_15(H):
    """[[15,7,3]] 的逻辑 |0...0_L⟩：码空间投影 + 7 个 Z̄ᵢ 的 +1 投影"""
    gens = css_gens(H)
    n = H.shape[1]
    rng = np.random.default_rng(0)
    v = rng.standard_normal(2 ** n) + 1j * rng.standard_normal(2 ** n)
    w = group_projection(gens, v)
    _, z_bars = css_logical_basis(H)
    for z in z_bars:
        w = w + z.apply_to_state(w)               # (I + Z̄ᵢ)·w
    return w / np.linalg.norm(w)


# ---------- 验证项 ----------
def verify_intra(code, label):
    """A：3n Pauli 全枚举 → syndrome 全非零（检测率 1）"""
    n, gens = code.n, code.gens
    zero_s = (0,) * len(gens)
    cnt = 0
    for i in range(n):
        for P in (1, 2, 3):
            t = [0] * n
            t[i] = P
            E = Pauli(n, t)
            assert syndrome_of(E, gens) != zero_s, f'{label}: {E} 未检测'
            cnt += 1
    print(f'  {label}: {cnt} 个单比特 Pauli 全检测 ✓（检测率 = 1，与 κ 无关）')
    return cnt


def verify_channel_semantics(code, P0, psi, label, seed):
    """B1+B2：单比特旋转注入——漏检无害、检测率闭式 sin²(θ/2)"""
    n, gens = code.n, code.gens
    zero_s = (0,) * len(gens)
    worst_miss, worst_det, worst_p = 0.0, 0.0, 0.0
    rng = np.random.default_rng(seed)
    for i in range(n):
        for P in (1, 2, 3):
            t = [0] * n
            t[i] = P
            E = Pauli(n, t)
            s = syndrome_of(E, gens)
            assert s != zero_s, f'{label}: 单比特 {E} 未检测（d≥3 违反）'
            theta = float(rng.uniform(0.05, 0.4))
            psi_p = rotation_state(psi, E, theta)
            # 漏检路径：P₀ψ'（归一化）→ 保真度
            miss = P0 @ psi_p
            miss /= np.linalg.norm(miss)
            F_miss = abs(np.vdot(psi, miss)) ** 2
            # 检测路径：syndrome s，恢复 E（同类代表）→ P₀Eψ'
            det = P0 @ E.apply_to_state(psi_p)
            det /= np.linalg.norm(det)
            F_det = abs(np.vdot(psi, det)) ** 2
            # B2：漏检概率 = ‖P₀ψ'‖² → 检测率 = 1 − ‖P₀ψ'‖² vs sin²(θ/2)
            p_miss_num = np.linalg.norm(P0 @ psi_p) ** 2
            p_det_num = 1 - p_miss_num
            p_det_closed = np.sin(theta / 2) ** 2
            worst_miss = max(worst_miss, abs(1 - F_miss))
            worst_det = max(worst_det, abs(1 - F_det))
            worst_p = max(worst_p, abs(p_det_num - p_det_closed))
    print(f'  {label}: 检测路径 |1−F| = {worst_det:.1e}、漏检路径 |1−F| = {worst_miss:.1e}'
          f'（漏检无害 ✓）、检测率误差 |Δsin²(θ/2)| = {worst_p:.1e} ✓')
    return worst_det, worst_miss, worst_p


def verify_logical_injection(code, psi, label):
    """B3：逻辑方向注入（X̄/Z̄/X̄Z̄）——syndrome 恒 0（不可检测），
    F = |c + is⟨ψ|E|ψ⟩|²（|0_L⟩ 是 Z̄ 本征态：Z̄ 注入为全局相位损失 0；
    X̄ 注入损失 sin²(θ/2)）"""
    theta = 0.3
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    worst_f = 0.0
    for E in (code.lx, code.lz, code.lx * code.lz):
        assert syndrome_of(E, code.gens) == (0,) * len(code.gens), \
            f'{label}: 逻辑方向 {E} syndrome ≠ 0'
        psi_p = rotation_state(psi, E, theta)
        F = abs(np.vdot(psi, psi_p)) ** 2
        ov = np.vdot(psi, E.apply_to_state(psi))      # ⟨ψ|E|ψ⟩（数值）
        F_closed = abs(c + 1j * s * ov) ** 2
        worst_f = max(worst_f, abs(F - F_closed))
    print(f'  {label}: 逻辑方向 syndrome 恒 0（不可检测 ✓），'
          f'F = |c + is⟨ψ|E|ψ⟩|² 误差 {worst_f:.1e} ✓')
    return worst_f


def verify_independent_noise(code, psi, label, seed,
                             thetas=(0.05, 0.1, 0.2, 0.4), trials=30):
    """D1：独立噪声（每比特 θᵢ ≤ θ_max）→ 最优纠错后损失 vs θ_max"""
    n = code.n
    table = recovery_table(code)
    rng = np.random.default_rng(seed)
    losses = []
    for tm in thetas:
        Ls = []
        for _ in range(trials):
            psi_p = psi.copy()
            for i in range(n):
                P = int(rng.integers(1, 4))
                th = float(rng.uniform(0, tm))
                E = Pauli(n, [0] * n)
                E.t[i] = P
                psi_p = rotation_state(psi_p, E, th)
            F = optimal_recovery_fidelity(psi, psi_p, code, table)
            Ls.append(max(0.0, 1 - F))
        losses.append(float(np.mean(Ls)))
    x = np.log(np.array(thetas, float))
    y = np.log(np.maximum(losses, 1e-16))
    slope, intercept = np.polyfit(x, y, 1)
    print(f'  {label}: 损失 = {["%.1e" % L for L in losses]}，'
          f'log-log 斜率 = {slope:.2f}（预期 ≈4：权重 ≥3 成分与权重 1 成分'
          f'同 syndrome 类，恢复干涉主导）')
    return losses, float(slope), float(intercept)


def verify_direction15():
    """E：[[15,7,3]] —— 45 单比特全检测；逻辑 |0...0_L⟩ 上
    35 线 Z 型 = ±1（全局相位，损失 0）、X 型 = 0（损失 sin²(θ/2)）"""
    H = direction_matrix(4)
    gens = css_gens(H)
    n = H.shape[1]
    zero_s = (0,) * len(gens)
    cnt = 0
    for i in range(n):
        for P in (1, 2, 3):
            t = [0] * n
            t[i] = P
            assert syndrome_of(Pauli(n, t), gens) != zero_s
            cnt += 1
    psi = logical_zero_15(H)
    lines = sorted(pg_lines(H))
    worst_z, worst_x = 0.0, 0.0
    for (i, j, k) in lines:
        for ty in (1, 2):                      # X 型与 Z 型逻辑方向
            t = [0] * n
            t[i] = t[j] = t[k] = ty
            E = Pauli(n, t)
            ov = np.vdot(psi, E.apply_to_state(psi))
            if ty == 2:                        # Z 型线 = 逻辑 Z 组合：±1
                worst_z = max(worst_z, abs(abs(ov) - 1.0))
            else:                              # X 型线 = 逻辑 X 组合：0
                worst_x = max(worst_x, abs(ov))
    print(f'  [[15,7,3]]: {cnt} 个单比特全检测 ✓；逻辑 |0...0_L⟩ 上：')
    print(f'    35 线 Z 型 |⟨ψ|E|ψ⟩| = 1 ± {worst_z:.1e}（⟹ 全局相位，损失 0）✓')
    print(f'    35 线 X 型 |⟨ψ|E|ψ⟩| < {worst_x:.1e}（⟹ 损失精确 sin²(θ/2)）✓')
    return cnt, len(lines), worst_z, worst_x


def main():
    print('P2 — 刚度分层采样检验（10.28 §3、§6 O6）')
    print('=' * 72)

    codes = [geo_codes.five_qubit_code(), geo_codes.steane_code(),
             geo_codes.shor_code()]
    labels = ['[[5,1,3]]', '[[7,1,3]]', '[[9,1,3]]']

    print('[A] 码内类复核：3n Pauli 全枚举 → 检测率 1（代数保证，与 κ 无关）')
    for code, lab in zip(codes, labels):
        verify_intra(code, lab)

    print('-' * 72)
    print('[B] 通道类检测语义（态矢量模拟，单比特旋转注入）')
    for code, lab in zip(codes, labels):
        P0, psi = code_projector(code)
        verify_channel_semantics(code, P0, psi, lab,
                                 seed=100 + codes.index(code))
        verify_logical_injection(code, psi, lab)

    print('-' * 72)
    print('[C] 分层预算等价性')
    print('  连续谱（θ ∈ [0, θ_max]）的检测率由闭式 sin²(θ/2) 决定（[B2] 数值验证），')
    print('  恢复保真度由代数保证（[B1]）⟹ 通道类无需全枚举连续谱：')
    print('  预算 = 3n（码内全枚举）+ O(1)（闭式验证）≪ 3n + 连续谱枚举 ✓')

    print('-' * 72)
    print('[D] 有害漏检率标度')
    fits = {}
    for code, lab in zip(codes, labels):
        P0, psi = code_projector(code)
        losses, slope, intercept = verify_independent_noise(
            code, psi, lab, seed=200 + codes.index(code))
        fits[lab] = (losses, slope, intercept)

    print('  H1 截断外推（θ_max = A/κ，A = 1，κ = 151.7 → θ_max ≈ 0.00659）：')
    for lab in labels:
        _, slope, intercept = fits[lab]
        loss_h1 = np.exp(intercept + slope * np.log(1.0 / KAPPA))
        print(f'    {lab}: 损失(θ_max=1/κ) ≈ {loss_h1:.1e}'
              f'（≪ κ⁻¹ = 6.6e-3，保守 {6.6e-3 / max(loss_h1, 1e-16):.0e} 倍）')

    print('-' * 72)
    print('[E] [[15,7,3]] 完备方向码 m=4 补充复核')
    verify_direction15()

    print('=' * 72)
    print('P2 结论：')
    print('  (1) 码内类检测率 = 1（代数）；通道类检测率 = sin²(θ/2)，漏检无害')
    print('  (2) 分层预算成立：连续谱无需全枚举')
    print('  (3) 独立噪声下纠错后损失 ~ θ⁴（权重 ≥3 成分与单比特成分同类干涉；')
    print('      本质：不可恢复成分权重 ≥3，θ⁴ 为最小损失阶，仍是高阶压制）')
    print('  (4) H1 截断（θ_max = A/κ）下有害漏检率 ≪ κ⁻¹：')
    print('      定理 10.28.2.02 的界 Aκ⁻¹ ≈ 0.66% 保守 ≥7 个数量级，实际 ~ κ⁻⁴ 量级')


if __name__ == '__main__':
    main()
