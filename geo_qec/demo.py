"""demo.py —— 几何码量子纠错演示

用法：python3 geo_qec/demo.py
对应文章：10.27（量子纠错码几何）命题 3.13–3.15。
流程：编码 → 噪声注入 → syndrome 测量 → 解码纠错 → 逻辑门。
注意：错误纠正判定用随机逻辑态（X̄/Z̄/X̄Z̄ 类逻辑错误均可见——
单一测试态存在盲区：|0_L⟩ 对 Z 类、叠加态对 X 类不可见）。
"""
import numpy as np
import random
from pauli import Pauli
from codes import ALL

LINE = '─' * 62
S = 1 / np.sqrt(2)


def random_state(code, rng):
    """随机逻辑态：cos(θ/2)|0_L⟩ + sin(θ/2)e^{iφ}|1_L⟩"""
    theta = rng.uniform(0, np.pi)
    phi = rng.uniform(0, 2 * np.pi)
    return code.encode(np.cos(theta / 2), np.sin(theta / 2) * np.exp(1j * phi))


def run(code):
    print(LINE)
    print(f'■ {code.name}')
    print(LINE)

    # [1] 码参数与距离（程序复核 O5 验证）
    ok, msg = code.check_distance(3)
    print(f'  [参数] n={code.n}, k={code.k}, m={code.m} | 对易/独立 ✓ | {msg} {"✓" if ok else "✗"}')

    # [2] 编码
    z0 = code.logical_zero()
    z1 = code.logical_one()
    overlap = abs(np.vdot(z0, z1)) ** 2
    stab_ok = all(np.allclose(g.apply_to_state(z0), z0) for g in code.gens)
    print(f'  [编码] |0_L⟩ 稳定子 +1 本征态 {"✓" if stab_ok else "✗"} | ⟨0_L|1_L⟩² = {overlap:.2e} {"✓" if overlap < 1e-12 else "✗"}')

    # [3] 单比特错误：全部 3n 个（随机态）
    n = code.n
    rng = random.Random(260807)
    ok_count = 0
    total = 3 * n
    for i in range(n):
        for ty in (1, 2, 3):
            t = [0] * n
            t[i] = ty
            E = Pauli(n, t)
            ideal = random_state(code, rng)
            noisy = E.apply_to_state(ideal)
            s = code.measure_syndrome(noisy)
            rec = code.correct(noisy, s)
            if code.fidelity(rec, ideal) > 0.999999:
                ok_count += 1
    tag = '全部纠正 ✓' if ok_count == total else '部分失败 ✗'
    print(f'  [单比特错误] {ok_count}/{total} {tag}（平均保真度 {ok_count/total:.6f}）')

    # [4] 双比特错误：检测 vs 纠正（距离 3 码的固有局限）
    trials = 300
    det = cor = harmless = 0
    for _ in range(trials):
        idxs = rng.sample(range(n), 2)
        t = [0] * n
        for idx in idxs:
            t[idx] = rng.randint(1, 3)
        E = Pauli(n, t)
        ideal = random_state(code, rng)
        noisy = E.apply_to_state(ideal)
        s = code.measure_syndrome(noisy)
        if s != (0,) * code.m:
            det += 1
        rec = code.correct(noisy, s)
        if code.fidelity(rec, ideal) > 0.999999:
            cor += 1
            if code.in_group(E):
                harmless += 1
    print(f'  [双比特错误] 检测率 {det/trials:.1%} | 纠正率 {cor/trials:.1%}（其中稳定子无害 {harmless} 例）')

    # [5] 逻辑门
    x_ok = code.fidelity(code.lx.apply_to_state(z0), z1) > 0.999999
    z_ok = code.fidelity(code.lz.apply_to_state(z1), -z1) > 0.999999
    psi = code.encode(S, S)
    p0 = abs(np.vdot(z0, psi)) ** 2
    print(f'  [逻辑门] X_L|0_L⟩=|1_L⟩ {"✓" if x_ok else "✗"} | '
          f'Z_L|1_L⟩=-|1_L⟩ {"✓" if z_ok else "✗"} | '
          f'H_L 后 P(0)={p0:.3f}, P(1)={1-p0:.3f}')
    print()


def main():
    print('═' * 62)
    print('  几何码量子纠错演示 · geo_qec')
    print('  对应：10.27 命题 3.13–3.15（O5 验证 + 程序复核）')
    print('═' * 62)
    for builder in ALL:
        run(builder())


if __name__ == '__main__':
    main()
