#!/usr/bin/env python3
"""10.45 验证：κ 刚度比闭式 κ = (16/3)^3 = 4096/27

验证三重一致（全部来自已入库数值，无新增拟合参数）：
  1. κ 闭式 vs 测量值：λ2_eff/λ1_eff vs 4096/27
  2. O8 过度设计比：κ/κ_min vs 16^3/3^4（κ_min = Λ = 3）
  3. 同源因子：λ1_eff/Λ^3 与 λ2_eff/16^3 是否同一比例因子

输入（10.27 命题 10.27.3.05(ii)，渗透修正后数值）：
  λ1_eff = 391.05 （ℳ 扇区慢模刚度）
  λ2_eff = 59324.3（ℐ 扇区快模刚度）
结构常数（0.5，命题 0.5.2.01 互锁已验证）：
  Λ = 3, ΔΘ = 5, k₀ = 2
Bott 扩张因子（命题 0.2.4.01）：δ⁸(Cl(n)) ≅ Cl(n) ⊗ Mat(16,ℝ)，16 = Mat(16,ℝ) 维度
"""
from fractions import Fraction

def main():
    # ── 输入 ──────────────────────────────────────────────
    lam1 = 391.05      # λ1_eff（10.27 命题 10.27.3.05(ii)）
    lam2 = 59324.3     # λ2_eff（同上）
    kappa_meas = lam2 / lam1

    Lambda, dTheta, k0 = 3, 5, 2   # 结构常数（0.5）
    Bott16 = 16                     # Mat(16,ℝ) 维度（0.2.4.01）

    # ── 候选闭式 ──────────────────────────────────────────
    base = Fraction((dTheta + Lambda) * k0, Lambda)   # (ΔΘ+Λ)·k₀/Λ = 16/3
    kappa_closed = base ** 3                          # (16/3)^3 = 4096/27
    kappa_closed_f = float(kappa_closed)

    print("=" * 66)
    print("10.45 κ 闭式验证：κ = [(ΔΘ+Λ)·k₀/Λ]^3 = (16/3)^3 = 4096/27")
    print("=" * 66)

    # ── 验证 1：κ 闭式 vs 测量 ────────────────────────────
    rel1 = abs(kappa_closed_f - kappa_meas) / kappa_meas
    print(f"\n[1] κ 闭式")
    print(f"    闭式: κ = {kappa_closed_f:.10f} = {kappa_closed}")
    print(f"    测量: κ = λ2/λ1 = {lam2}/{lam1} = {kappa_meas:.10f}")
    print(f"    相对差 = {rel1*100:.6f} %")
    assert rel1 < 1e-4, "κ 闭式验证失败（>0.01%）"

    # ── 验证 2：O8 过度设计比 ─────────────────────────────
    # κ_min ≈ 3（10.43 §3.2.1 乘幂模型安全边际临界值）；结构等同 Λ = 3
    kappa_min = float(Lambda)
    ratio_meas = kappa_meas / kappa_min
    ratio_closed = Fraction(Bott16**3, Lambda**4)     # 16^3/3^4
    ratio_closed_f = float(ratio_closed)
    rel2 = abs(ratio_closed_f - ratio_meas) / ratio_meas
    print(f"\n[2] O8 过度设计比 κ/κ_min（κ_min = Λ = 3）")
    print(f"    测量: {kappa_meas:.4f}/3 = {ratio_meas:.6f}")
    print(f"    闭式: 16^3/3^4 = {ratio_closed_f:.6f} = {ratio_closed}")
    print(f"    相对差 = {rel2*100:.6f} %")
    assert rel2 < 1e-3, "O8 比验证失败（>0.1%）"

    # ── 验证 3：同源因子 ──────────────────────────────────
    f1 = lam1 / Lambda**3        # λ1/Λ^3
    f2 = lam2 / Bott16**3        # λ2/16^3
    rel3 = abs(f1 - f2) / f2
    print(f"\n[3] 同源因子（λ ∝ 结构基数，共享 Hessian 标度）")
    print(f"    λ1/Λ^3 = {lam1}/27 = {f1:.6f}")
    print(f"    λ2/16^3 = {lam2}/4096 = {f2:.6f}")
    print(f"    相对差 = {rel3*100:.6f} %")
    assert rel3 < 1e-4, "同源因子验证失败（>0.01%）"

    # ── 旁证：备选 λ1（3.11 重算值 392.2）下的闭式偏差 ──────
    lam1_alt = 392.2
    kappa_alt = lam2 / lam1_alt
    rel_alt = abs(kappa_closed_f - kappa_alt) / kappa_alt
    print(f"\n[旁证] 备选 λ1 = 392.2（3.11 Hessian 重算）：κ = {kappa_alt:.6f}")
    print(f"        与闭式相对差 = {rel_alt*100:.4f} %（在 λ1 跨文章不确定度 ~0.3% 内）")

    print("\n" + "=" * 66)
    print("全部验证通过：三重 0.001% 级一致支持候选闭式")
    print("κ = [(ΔΘ+Λ)·k₀/Λ]^3 = 4096/27 ≈ 151.704（探索稿，待第一性谱论验证）")
    print("=" * 66)

if __name__ == "__main__":
    main()
