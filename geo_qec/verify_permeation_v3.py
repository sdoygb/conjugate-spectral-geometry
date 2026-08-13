#!/usr/bin/env python3
# O-渗透函数：N1=1/(1-f1), N2=1/(f2-1) 闭式系统搜索（链 B）
L, k0, dT = 3, 2, 5
c13 = L*L + k0*k0
Bott8, Bott16 = 8, 16
c52 = k0*k0*c13
c832 = Bott16*c52
c21 = L*(dT+k0)          # 21 = 3*7
c7 = dT+k0               # 7
c105 = L*dT*c7           # 105 = 3*5*7
c144 = Bott16*L*L        # 144 = 16*9

K = 839.758793; me = 510.99895
lam_e = (K/me)**(2/3)
lam2_eff = 42600*lam_e
mu = lam2_eff/4096
lam1_eff = mu*27

lam1_bare, lam2_bare = 392.21, 58760.77
f1 = lam1_eff/lam1_bare
f2 = lam2_eff/lam2_bare
N1 = 1/(1-f1)
N2 = 1/(f2-1)
print(f"链B: N1 = 1/(1-f1) = {N1:.6f}, N2 = 1/(f2-1) = {N2:.6f}")
print(f"N1/N2 = {N1/N2:.8f} (候选 13/4+1/324 = {13/4+1/324:.8f})")

# === N1 候选 ===
print(f"\n=== N1 = {N1:.4f} 候选 ===")
N1_cands = {
    "338": 2*c13*c13,
    "339": 339,
    "339.2=16*(21+1/5)": Bott16*(c21+1/dT),
    "339.2=16*21+16/5": Bott16*c21 + Bott16/dT,
    "16*21.2": Bott16*21.2,
    "340": 340,
    "337": 2*c13*c13-1,
    "338+λe-5/27": 338+lam_e-dT/(L**3),
    "13*26.09": c13*26.09,
    "52*6.523": c52*6.523,
}
for name, v in N1_cands.items():
    dev = abs(v-N1)/N1*100
    print(f"  {name} = {v:.6f}  偏差 {dev:.5f}%")

# === N2 候选 ===
print(f"\n=== N2 = {N2:.4f} 候选 ===")
N2_cands = {
    "104=2*13*4": 2*c13*k0*k0,
    "105*(1-1/144)": c105*(1-1/c144),
    "105*(1-1/144.16)": c105*(1-1/(c144+k0*k0/(dT*dT))),
    "104*(1+1/382)": 104*(1+1/382),
    "104*(1+1/381.9)": 104*(1+1/381.9),
    "832/7.979": c832/7.979,
    "832/(8-21/1000)": c832/(8-c21/1000),
    "105-0.7276": c105-0.7276,
    "150*0.69515": 150*0.69515,
    "105*(1-1/144.16)精确": c105*(1-1/(c144+4/25)),
    "16^4/628.5": Bott16**4/628.5,
}
for name, v in N2_cands.items():
    dev = abs(v-N2)/N2*100
    print(f"  {name} = {v:.6f}  偏差 {dev:.5f}%")

# === 双参数搜索: N2 = A*(1 ± 1/B) 形式 ===
print(f"\n=== N2 = A*(1+1/B) 搜索 ===")
bases_A = [104, 105, 8*c13, 2*c52, c832/8, 150]
best = []
for A in bases_A:
    B = 1/(N2/A - 1)
    if B > 0:
        best.append((abs(B-round(B))/B, f"A={A}: B={B:.4f} (最近整数 {round(B)})"))
    # A*(1-1/B)
    B2 = 1/(1 - N2/A)
    if B2 > 0:
        best.append((abs(B2-round(B2))/B2, f"A={A}: B2(减)={B2:.4f} (最近整数 {round(B2)})"))
best.sort()
for dev, s in best[:8]:
    print(f"  整数偏差{dev*100:.3f}%: {s}")

# === N1 = A*(1 ± 1/B) 搜索 ===
print(f"\n=== N1 = A*(1+1/B) 搜索 ===")
best = []
for A in [338, 339, 340, 336, 337, 338.5, 338.2, 339.5]:
    B = 1/(N1/A - 1)
    if B > 0:
        best.append((abs(B-round(B))/B, f"A={A}: B={B:.4f} (最近整数 {round(B)})"))
    B2 = 1/(1 - N1/A)
    if B2 > 0:
        best.append((abs(B2-round(B2))/B2, f"A={A}: B2(减)={B2:.4f} (最近整数 {round(B2)})"))
best.sort()
for dev, s in best[:8]:
    print(f"  整数偏差{dev*100:.3f}%: {s}")

# === 关键检验: 若 N2 = 105(1-1/144) 且 N1/N2 = 13/4+1/324, N1 = ? ===
S = 13/4 + 1/324
N1_from_N2 = S * 105*(1-1/c144)
print(f"\nN1(from N2=105*143/144, S) = {N1_from_N2:.4f} vs 实测 {N1:.4f}  偏差 {abs(N1_from_N2-N1)/N1*100:.4f}%")

# === 自洽检验: N1*N2 结构 ===
print(f"\nN1*N2 = {N1*N2:.2f}")
print(f"  /338 = {N1*N2/338:.4f}")
print(f"  /832 = {N1*N2/832:.4f}")
print(f"  /(338*832) = {N1*N2/(338*832):.8f}")
print(f"  1/(N1*N2) = {1/(N1*N2):.10f}")
print(f"  1/(N1*N2)*1e6 = {1e6/(N1*N2):.4f}")
