"""check_logical.py —— 验证 10.27 逻辑算符代表元在 all-zero 参考基下的类"""
import numpy as np
from pauli import Pauli
from codes import five_qubit_code, shor_code

print('=== 五比特码 ===')
code = five_qubit_code()
z0 = code.logical_zero()
z1 = code.logical_one()
Xbar_1027 = Pauli.from_string(5, 'X1Y2X3')
Zbar_1027 = Pauli.from_string(5, 'Z1X2Z3')
lx_prog, lz_prog = code.lx, code.lz

for name, E in [('X1Y2X3 (10.27 X̄)', Xbar_1027), ('Z1X2Z3 (10.27 Z̄)', Zbar_1027),
                ('X⊗5 (程序 lx)', lx_prog), ('Z⊗5 (程序 lz)', lz_prog)]:
    comm_gens = all(E.commutes(g) for g in code.gens)
    in_S = code.in_group(E)
    E0 = E.apply_to_state(z0)
    f0 = abs(np.vdot(z0, E0))**2
    f1 = abs(np.vdot(z1, E0))**2
    print(f'  {name}: 与稳定子对易={comm_gens} | ∈S={in_S} | |⟨0|E|0⟩|²={f0:.4f} | |⟨1|E|0⟩|²={f1:.4f}')
# 陪集关系
P = Xbar_1027 * lx_prog
print(f'  X̄_1027·X⊗5 = {P} ∈ S? {code.in_group(P)}')
Q = Zbar_1027 * lz_prog
print(f'  Z̄_1027·Z⊗5 = {Q} ∈ S? {code.in_group(Q)}')
R = Xbar_1027 * Zbar_1027
print(f'  X̄_1027·Z̄_1027 = {R} ∈ S? {code.in_group(R)}')

print()
print('=== Shor 码 ===')
code = shor_code()
z0 = code.logical_zero()
z1 = code.logical_one()
Xbar_1027 = Pauli.from_string(9, 'Z1Z4Z7')
Zbar_1027 = Pauli.from_string(9, 'X1X2X3')
for name, E in [('Z1Z4Z7 (10.27 X̄)', Xbar_1027), ('X1X2X3 (10.27 Z̄)', Zbar_1027)]:
    comm_gens = all(E.commutes(g) for g in code.gens)
    in_S = code.in_group(E)
    E0 = E.apply_to_state(z0)
    f0 = abs(np.vdot(z0, E0))**2
    f1 = abs(np.vdot(z1, E0))**2
    print(f'  {name}: 与稳定子对易={comm_gens} | ∈S={in_S} | |⟨0|E|0⟩|²={f0:.4f} | |⟨1|E|0⟩|²={f1:.4f}')
