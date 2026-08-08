"""geo_qec 扩展性基准
1) 态矢量内存实测（complex128，2^n × 16B）
2) 当前框架（群枚举编码）扩展性：重复码 [[n,1,2]]，n=10..18
3) 优化编码（迭代投影 O(m·2^n)）扩展性：n=20..28

运行：python3 geo_qec/bench_extend.py
"""
import numpy as np
import time
import gc
from pauli import Pauli
from stabilizer import StabilizerCode


def repetition_gens(n):
    """[[n,1,2]] 重复码生成元：Z_i Z_{i+1}（i=1..n-1），逻辑 X=X^⊗n、Z=Z_1"""
    gens = [Pauli.Z(n, i) * Pauli.Z(n, i + 1) for i in range(n - 1)]
    lx = Pauli.I(n)
    for i in range(n):
        lx = lx * Pauli.X(n, i)
    lz = Pauli.Z(n, 0)
    return gens, lx, lz


def logical_zero_fast(n, gens):
    """迭代投影：|0_L⟩ ∝ Π_j (I+g_j)|0...0⟩，O(m·2^n)
    展开乘积 = Σ_{s∈S} s|0...0⟩（生成元对易），与群枚举版精确等价。"""
    state = np.zeros(2 ** n, dtype=complex)
    state[0] = 1.0
    for g in gens:
        state = state + g.apply_to_state(state)
    return state / np.linalg.norm(state)


print('=' * 64)
print('1) 态矢量内存实测（complex128 = 2^n × 16 B）')
print('=' * 64)
for n in (20, 24, 26, 27, 28, 29):
    gb = 2 ** n * 16 / 1e9
    try:
        t0 = time.time()
        v = np.ones(2 ** n, dtype=np.complex128)
        t1 = time.time()
        v = v.reshape(-1, 2, 2 ** (n - 1))
        v[:, 1, :] *= -1          # 触碰全部内存（模拟 Z 相位）
        s = float(v.sum())
        t2 = time.time()
        print(f'n={n:2d}: 单个态矢量 {gb:6.2f} GB | 分配 {t1-t0:5.2f}s | 全遍历 {t2-t1:5.2f}s | sum={s:.0f}')
        del v
        gc.collect()
    except MemoryError:
        print(f'n={n:2d}: {gb:6.2f} GB  MemoryError')
        break

print()
print('=' * 64)
print('2) 当前框架（群枚举编码）扩展性：重复码 [[n,1,2]]')
print('=' * 64)
for n in (10, 12, 14, 16, 18):
    t0 = time.time()
    code = StabilizerCode(f'[[{n},1,2]] 重复码', *repetition_gens(n))
    t1 = time.time()
    z0 = code.logical_zero()
    t2 = time.time()
    print(f'n={n:2d}: 码构造(群 2^{n-1}) {t1-t0:7.2f}s | 编码 {t2-t1:7.2f}s')
    del code, z0
    gc.collect()

print()
print('=' * 64)
print('3) 优化编码（迭代投影 O(m·2^n)）扩展性')
print('=' * 64)
for n in (20, 24, 26, 27, 28):
    gb = 2 ** n * 16 / 1e9
    try:
        gens, lx, lz = repetition_gens(n)
        t0 = time.time()
        z0 = logical_zero_fast(n, gens)
        t1 = time.time()
        z1 = lx.apply_to_state(z0)
        E = Pauli.Y(n, n - 1)
        noisy = E.apply_to_state(z1)
        s = tuple(E.symplectic(g) for g in gens)
        rec = noisy                                # 演示性：只测规模
        F = abs(np.vdot(z1, rec)) ** 2
        t2 = time.time()
        print(f'n={n:2d}: 态矢量 {gb:5.2f} GB×3 | 编码 {t1-t0:6.2f}s | 全流程 {t2-t1:6.2f}s')
        del z0, z1, noisy, rec
        gc.collect()
    except MemoryError:
        print(f'n={n:2d}: MemoryError')
        break
