# 验证 11.13 §4 公式 vs 1.5 §4.1 公式在 σ* 处的数值
import numpy as np

s = np.array([0.777912, 0.210603, 0.011484])

# 11.13 §4 公式: (1/2) sum_{i,j} (si*sj/sqrt(si*sj)) * (18/(si*sj))
val = 0.0
for i in range(3):
    for j in range(3):
        val += (s[i]*s[j]/np.sqrt(s[i]*s[j])) * (18.0/(s[i]*s[j]))
val *= 0.5
print(f"11.13 公式代入 sigma* = {val:.1f}  (11.13 声称 137.036, 偏差 {val/137.036:.1f} 倍)")

# 1.5 §4.1 公式: (sum 1/si + sum_{i<j} 1/sqrt(si*sj)) / C^2
# C 由 2pC^3 + C^2 = 1 确定, p = sqrt(s1 s2 s3)
p = float(np.sqrt(s.prod()))
# 数值解 C
C = 0.5
for _ in range(200):
    C = C - (2*p*C**3 + C**2 - 1) / (6*p*C**2 + 2*C)
S15 = (np.sum(1.0/s) + sum(1.0/np.sqrt(s[i]*s[j]) for i in range(3) for j in range(i+1, 3))) / C**2
print(f"1.5 公式代入 sigma* (C={C:.4f}, C^2={C**2:.4f}) = {S15:.1f}  (137.036 零阶近似)")

# 对称极限对比
s_sym = np.array([1/3, 1/3, 1/3])
v11 = 0.0
for i in range(3):
    for j in range(3):
        v11 += (s_sym[i]*s_sym[j]/np.sqrt(s_sym[i]*s_sym[j])) * (18.0/(s_sym[i]*s_sym[j]))
v11 *= 0.5
p2 = float(np.sqrt(s_sym.prod()))
C2 = 0.5
for _ in range(200):
    C2 = C2 - (2*p2*C2**3 + C2**2 - 1) / (6*p2*C2**2 + 2*C2)
v15 = (np.sum(1.0/s_sym) + sum(1.0/np.sqrt(s_sym[i]*s_sym[j]) for i in range(3) for j in range(i+1, 3))) / C2**2
print(f"对称极限: 11.13 公式 = {v11:.1f}, 1.5 公式 = {v15:.1f} (1.5 原文 S_min=24)")
