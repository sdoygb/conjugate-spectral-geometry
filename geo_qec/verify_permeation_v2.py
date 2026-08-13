#!/usr/bin/env python3
# 链 B（42600 定律优先）：渗透函数精确闭式搜索
L, k0, dT = 3, 2, 5
c13 = L*L + k0*k0
Bott8, Bott16 = 8, 16
c52 = k0*k0*c13
c832 = Bott16*c52
kappa = Bott16**3 / L**3          # 4096/27

K = 839.758793; me = 510.99895
lam_e = (K/me)**(2/3)
n42600 = (Bott16**3 * k0*k0 * c13 + k0**3) / dT
lam2_eff = n42600 * lam_e         # 链 B 锚点
mu = lam2_eff / Bott16**3
lam1_eff = mu * L**3
print(f"链B: lambda2^eff={lam2_eff:.6f}, mu={mu:.8f}, lambda1^eff={lam1_eff:.6f}")

# 裸值（3.11 原文）
lam1_bare, lam2_bare = 392.21, 58760.77
rho_bare = lam2_bare/lam1_bare

# 渗透函数（链 B 精确）
f1 = lam1_eff/lam1_bare
f2 = lam2_eff/lam2_bare
print(f"\nf1 = {f1:.10f}   1-f1 = {1-f1:.10f}   1/(1-f1) = {1/(1-f1):.6f}")
print(f"f2 = {f2:.10f}   f2-1 = {f2-1:.10f}   1/(f2-1) = {1/(f2-1):.6f}")

# ρ_bare 闭式检查
rho_closed = 150*(1-1/c832)
print(f"\nrho_bare 闭式 150(1-1/832) = {rho_closed:.8f}, 实测 {rho_bare:.8f}, 偏差 {abs(rho_closed-rho_bare)/rho_bare*100:.6f}%")

# 用 ρ_bare 闭式反推 f2/f1
ratio_closed = kappa/rho_closed
print(f"f2/f1(闭式) = {ratio_closed:.10f}")
print(f"f2/f1(实测) = {f2/f1:.10f}")

# 搜索 1/(1-f1) 的闭式
print(f"\n--- 搜索 1/(1-f1) = {1/(1-f1):.4f} ---")
N1 = 1/(1-f1)
# 结构数
structs = {'338': 2*c13*c13, '339': 339, '338.5': 2*c13*c13+0.5, '337': 2*c13*c13-1,
           '832/2.452': c832/2.452, '104*3.26': 104*3.26, '52*6.52': c52*6.52,
           '16*21.2': Bott16*21.2, '13*26.09': c13*26.09}
for name, v in structs.items():
    print(f"  {name} = {v:.4f}  偏差 {abs(v-N1)/N1*100:.4f}%")

# 搜索 1/(f2-1) 的闭式
print(f"\n--- 搜索 1/(f2-1) = {1/(f2-1):.4f} ---")
N2 = 1/(f2-1)
cands = {
    '104(=2*13*4)': 2*c13*k0*k0,
    '104*(1+1/338)': 104*(1+1/338),
    '104*(1+1/832)': 104*(1+1/c832),
    '104/(1-1/338)': 104/(1-1/338),
    '105*(1-1/144)': 105*(1-1/144),
    '105-13/17.87': 105-c13/17.87,
    '104.2724=105-0.7276': 105-0.7276,
    '338/3.2415': 338/3.2415,
    '832/7.979': c832/7.979,
    '150*0.69515': 150*0.69515,
    '71*1.4686': 71*1.4686,
}
for name, v in cands.items():
    print(f"  {name} = {v:.6f}  偏差 {abs(v-N2)/N2*100:.4f}%")

# 关键: f1 与 f2 的结构关系
# 若 f1 = 1-1/A, f2 = 1+1/B, 且 f2/f1 = kappa/rho_closed
# 则 (1+1/B)/(1-1/A) = kappa/rho_closed
# 解 B: 1+1/B = R(1-1/A) -> 1/B = R - R/A - 1 -> B = 1/(R-1-R/A)
R = kappa/rho_closed
print(f"\nR = f2/f1 = {R:.10f}")
for A_name, A in [('338', 338), ('339.23', 339.23), ('340', 340)]:
    B = 1/(R - 1 - R/A)
    print(f"  A={A_name}: B = {B:.4f}")

# 直接求 B 从实测: f2 = 1+1/B
B_meas = 1/(f2-1)
print(f"\nB(实测) = {B_meas:.6f}")
# B 与 832 的关系
print(f"B/832 = {B_meas/c832:.8f}")
print(f"832/B = {c832/B_meas:.8f}")
# B 与 104 的关系
print(f"B/104 = {B_meas/104:.8f}")
# B 与 338 的关系  
print(f"B/338 = {B_meas/338:.8f}")
print(f"338/B = {338/B_meas:.8f}")
