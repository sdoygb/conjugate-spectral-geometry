"""check_2err.py —— 双比特错误纠回率来源分析"""
import numpy as np
from itertools import combinations, product
from pauli import Pauli
from codes import ALL

for code in (b() for b in ALL):
    n = code.n
    ok = 0
    total = 0
    examples = []
    for i, j in combinations(range(n), 2):
        for ti, tj in product((1, 2, 3), repeat=2):
            t = [0] * n
            t[i] = ti
            t[j] = tj
            E = Pauli(n, t)
            total += 1
            ideal = code.encode(1, 0)
            noisy = E.apply_to_state(ideal)
            s = code.measure_syndrome(noisy)
            E1 = code.decode(s)
            rec = E1.apply_to_state(noisy)
            F = code.fidelity(rec, ideal)
            if F > 0.999999:
                ok += 1
                if len(examples) < 5:
                    prod = E1 * E
                    examples.append((E, E1, prod, code.in_group(prod)))
    print(f'{code.name}: 纠回 {ok}/{total} = {ok/total:.1%}')
    for E, E1, prod, inS in examples:
        print(f'    E={E}  E1={E1}  E1·E={prod}  ∈S={inS}')
