"""debug.py —— 定位 demo 输出异常（临时调试脚本）"""
import numpy as np
from pauli import Pauli
from codes import five_qubit_code, steane_code, shor_code

for code in (five_qubit_code(), steane_code(), shor_code()):
    print('=' * 50)
    print(code.name)
    z0 = code.logical_zero()
    print('  z0 norm =', np.linalg.norm(z0))
    print('  z0 非零分量数 =', np.count_nonzero(np.abs(z0) > 1e-12))
    for gi, g in enumerate(code.gens[:3]):
        gz = g.apply_to_state(z0)
        print(f'  g{gi+1}·z0 偏差 = {np.max(np.abs(gz - z0)):.3e}')
    lx0 = code.lx.apply_to_state(z0)
    print(f'  X̄·z0 与 z0 偏差 = {np.max(np.abs(lx0 - z0)):.3e}')

    # 单比特错误逐个检查
    fails = 0
    for i in range(code.n):
        for ty in (1, 2, 3):
            t = [0] * code.n
            t[i] = ty
            E = Pauli(code.n, t)
            ideal = code.encode(1, 0)
            noisy = E.apply_to_state(ideal)
            s = code.measure_syndrome(noisy)
            se = code.syndrome_of(E)
            rec = code.correct(noisy, s)
            F = code.fidelity(rec, ideal)
            if F < 0.999999:
                fails += 1
                if fails <= 3:
                    print(f'  FAIL {E}: synd(meas)={s} synd(E)={se} F={F:.4f}')
    print(f'  单比特失败数 = {fails}/{3*code.n}')
