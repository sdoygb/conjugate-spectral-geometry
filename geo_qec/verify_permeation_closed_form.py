#!/usr/bin/env python3
# 10.47 O-渗透函数：f1, f2 闭式系统验证
# 结构常数（互锁骨架）: Lambda=3, k0=2, dT=5(DeltaTheta), 13=Lambda^2+k0^2
L, k0, dT = 3, 2, 5
c13 = L*L + k0*k0          # 13
Bott8, Bott16 = 8, 16      # Bott 扩张因子
c71 = Bott8*L*L - 1        # 71 = 8*9-1
c52 = k0*k0*c13            # 52 = 4*13
c832 = Bott16*c52          # 832 = 16*52
LH = k0*L*dT*dT            # Lambda_H = 150
kappa = Bott16**3 // (L**3) if (Bott16**3) % (L**3)==0 else Bott16**3/(L**3)  # 4096/27
kappa = Bott16**3 / L**3

# 物理输入
K = 839.758793   # keV, 普适质量量子
me = 510.99895   # keV, 电子质量
lam_e = (K/me)**(2/3)
print(f"lambda_e = {lam_e:.10f}")

# 42600 定律
n42600 = (Bott16**3 * k0*k0 * c13 + k0**3) / dT   # (4096*4*13+8)/5
print(f"42600 = {n42600:.6f} (整数? {n42600==int(n42600)})")
lam2_eff_pred = n42600 * lam_e
print(f"lambda2^eff(预言) = {lam2_eff_pred:.6f}  (实测 59324.3)")

mu = lam_e * 5325/512
print(f"mu = {mu:.8f} (lambda_e*5325/512)")
lam1_eff_pred = mu * 27
print(f"lambda1^eff(预言) = {lam1_eff_pred:.6f}  (实测 391.05)")

# 裸值（3.11 原文）
lam1_bare = 392.21
lam2_bare = 58760.77

# ---- 渗透函数实测 ----
f1_meas = lam1_eff_pred/lam1_bare
f2_meas = lam2_eff_pred/lam2_bare
print(f"\nf1(实测,用预言) = {f1_meas:.10f}")
print(f"f2(实测,用预言) = {f2_meas:.10f}")
rho_bare = lam2_bare/lam1_bare
print(f"rho_bare = {rho_bare:.10f}")

# ---- 候选闭式 ----
# f1: 10.46 已有 1-1/(2*13^2)
f1_cand = 1 - 1/(2*c13*c13)
print(f"\n[f1] 候选 1-1/(2*13^2) = {f1_cand:.10f}  偏差 {abs(f1_cand-f1_meas)/f1_meas*100:.6f}%")

# rho_bare: 新发现 150*(1-1/832) = 150*831/832
rho_cand = LH * (1 - 1/c832)
print(f"[rho_bare] 候选 150*(1-1/832) = {rho_cand:.10f}  偏差 {abs(rho_cand-rho_bare)/rho_bare*100:.6f}%")
print(f"   831 = {c832-1} = 832-1")

# f2: 由 f1, kappa, rho_bare 推导
f2_cand = f1_cand * kappa / rho_cand
print(f"[f2] 候选 f1*kappa/rho_bare = {f2_cand:.10f}  偏差 {abs(f2_cand-f2_meas)/f2_meas*100:.6f}%")

# f2 的 1+1/N 形式
inv = 1/(f2_meas-1)
print(f"\nf2-1 = {f2_meas-1:.10f}, 1/(f2-1) = {inv:.6f}")
print(f"  候选整数: 104 (偏差 {abs(inv-104)/104*100:.4f}%)")

# ---- 分解尝试: f2-1 的倒数 N 的各种组合 ----
print(f"\n--- N = 1/(f2-1) = {inv:.6f} 的分解 ---")
combos = {
    "2*13*4(=104)": 2*c13*k0*k0,
    "8*13(=104)": Bott8*c13,
    "16*13/2(=104)": Bott16*c13/2,
    "2*52(=104)": 2*c52,
    "105-0.726": L*dT*(dT+k0),
    "112-7.726": Bott16*(dT+k0),
    "16*6.517": Bott16*6.5171,
    "13*8.021": c13*8.02106,
    "71+33.27": c71+33.2737,
    "16^4/628.5": Bott16**4/628.5,
}
for name, val in combos.items():
    print(f"  {name} = {val:.6f}")

# ---- 更系统的搜索: N 用 {2,3,5,13,16,52,71,832} 的简单组合 ----
print(f"\n--- 搜索 N ≈ {inv:.4f} 的结构组合 ---")
import itertools
base = [2,3,5,13,16,52,71,832]
best = []
for a in base:
    for b in base:
        for op in ['*','/']:
            if op=='*': v = a*b
            else: v = a/b
            dev = abs(v-inv)/inv*100
            if dev < 0.5:
                best.append((dev, f"{a}{op}{b}={v:.4f}"))
            for c in base:
                for op2 in ['*','/','+','-']:
                    if op2=='*': v2=v*c
                    elif op2=='/': v2=v/c
                    elif op2=='+': v2=v+c
                    else: v2=v-c
                    dev2 = abs(v2-inv)/inv*100
                    if dev2 < 0.05:
                        best.append((dev2, f"({a}{op}{b}){op2}{c}={v2:.4f}"))
best.sort()
for dev, s in best[:15]:
    print(f"  偏差{dev:.4f}%: {s}")

# ---- 验证链条: 若所有闭式成立, 检查自洽 ----
print(f"\n--- 闭式链自洽 ---")
lam2_bare_closed = lam1_bare * rho_cand
print(f"lambda2^bare(闭式) = {lam2_bare_closed:.6f} vs 原文 {lam2_bare} (差 {abs(lam2_bare_closed-lam2_bare):.4f})")
lam1_eff_closed = lam1_bare * f1_cand
print(f"lambda1^eff(闭式) = {lam1_eff_closed:.6f} vs 预言 {lam1_eff_pred:.6f}")
lam2_eff_closed = lam2_bare * f2_cand
print(f"lambda2^eff(闭式) = {lam2_eff_closed:.6f} vs 预言 {lam2_eff_pred:.6f}")
print(f"  谱比(闭式) = {lam2_eff_closed/lam1_eff_closed:.6f} vs kappa={kappa:.6f}")
