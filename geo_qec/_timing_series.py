"""计时：方向完备码 m=3..10 的结构验证时间（绘图数据）"""
import time
from p4_demo_1023 import make_code, single_bit_syndromes

def timing(m):
    H, gens, n, k = make_code(m)
    t0 = time.time()
    SX, SZ = single_bit_syndromes(H, n, m)
    t1 = time.time()
    assert all(s != 0 for s in SX) and all(s != 0 for s in SZ)
    for a in range(n):
        for b in range(a + 1, n):
            assert (SX[a] ^ SX[b]) != 0 and (SZ[a] ^ SZ[b]) != 0
    t2 = time.time()
    return n, k, t1 - t0, t2 - t1

print('m   n       k      syndrome表     权重2全量结构判定  符号内存(KB)')
rows = []
for m in range(3, 11):
    n, k, t1, t2 = timing(m)
    mem = 2 * m * n / 8 / 1024
    rows.append((m, n, k, t1, t2, mem))
    print(f'{m:2d}  {n:5d}  {k:5d}   {t1:.3f}s        {t2:.3f}s          {mem:.2f}')
print('\n# 绘图数据 (m, n, k, t_syndrome, t_w2, mem_KB)')
print(rows)
