#!/usr/bin/env python3
"""
A3 数值检验（0.13 §8.3 / §9 开放问题 3，命题 0.13.8.07）
平台：10.35 AG r=3/4 码 [[2^m,·,16/32]]，m=10
日期：2026-08-25（v2：修正 resid2 定义一致性；(c2) 改为解析恒等式核对 + MC 收敛验证）

锚定常数（calculate_math 验证，2026-08-25）：
  δη = 1/sqrt(391.05) = 0.05056894054（8.15 因果步长）
  AG r=3: [[1024,·,16]], w0=8,  c_d = 1.05e8（10.35 定理 10.35.1.07 逻辑 Z 翻转主阶）
  AG r=4: [[1024,·,32]], w0=16, c_d = 7.53e7

符号约定：
  drift 占比 resid2 := E[Δθ]² / E[Δθ²] ∈ [0,1]；=1 完全确定性（漂移占优），→0 纯噪声。
  物理参数下 p_fail ~1e-8/1e-24 → 轨道确定性 → resid2 = 1 精确。
"""
import json
import os
import numpy as np

# ================= 锚定常数 =================
DETA = 0.05056894054  # 1/sqrt(391.05)
CODES = {
    "AG_r3": dict(n=1024, w0=8,  d=16, c_d=1.05e8),
    "AG_r4": dict(n=1024, w0=16, d=32, c_d=7.53e7),
}
N_STEPS = 1_000_000
THETA0 = 0.05           # 轨道起点（rad）
N_BINS = 20             # 分箱数（θ ∈ [0, 2π)）
STRESS_P0 = [1e-4, 1e-2, 1e-1]
STRESS_STEPS = 100_000
RNG_SEED = 260825

rng = np.random.default_rng(RNG_SEED)

# ================= 物理失败率 =================
def p_fail_phys(theta, code):
    """10.35 相干噪声失败率（主阶）：c_d · sin²(θ/2)^{w0} · cos²(θ/2)^{n-w0}"""
    eps = np.sin(theta / 2.0) ** 2
    n, w0, c_d = code["n"], code["w0"], code["c_d"]
    return c_d * eps**w0 * (1.0 - eps) ** (n - w0)

# ================= [1] 物理主检验：确定性解析轨道 =================
def physical_analysis(code_name):
    """
    事件率 λ ≈ 1e-8（r=3）/ 1e-24（r=4）→ 10^6 步内事件 ≈ 0 几乎必然。
    轨道 θ_n = (θ0 + n·δη) mod 2π 完全确定，逐项统计可向量化，结果解析精确。
    """
    code = CODES[code_name]
    n = np.arange(N_STEPS)
    theta = (THETA0 + n * DETA) % (2 * np.pi)
    pf = p_fail_phys(theta, code)
    lam = float(pf.sum())           # 期望事件数（泊松参数）
    # 无事件时 Δθ = δη 恒定：
    s3_ratio = 1.0                  # E[|Δθ|³]/δη³ = 1（精确）
    resid2 = 1.0                    # drift 占比 E[Δθ]²/E[Δθ²] = 1（确定性极限）
    idx = (theta / (2 * np.pi) * N_BINS).astype(int) % N_BINS
    cnt = np.bincount(idx, minlength=N_BINS)
    cond3 = np.ones(N_BINS)         # 每箱 E[|Δθ|³]/δη³ = 1
    # 事件贡献上界（解析界）：λ·E[|Δθ_ev|³]/(N·δη³)
    ev3_ratio_bound = lam * (0.5 * ((1 + code["w0"])**3 + abs(1 - code["w0"])**3)) / N_STEPS
    return dict(
        code=code_name, label="physical (analytical)",
        steps=N_STEPS, expected_events=lam,
        global_s3_ratio=float(s3_ratio),
        sup_cond3_ratio=float(cond3.max()),
        sup_resid2=float(resid2),
        bins_occupied=int((cnt > 0).sum()),
        event_contrib_bound=ev3_ratio_bound,
    )

# ================= [2] 应力测试：MC 轨道 =================
def stress_mc(code_name, p0, n_steps=STRESS_STEPS):
    """固定事件率 p0（非物理），检验矩结构形状：p0→0 应逼近物理确定性极限。"""
    code = CODES[code_name]
    w0 = code["w0"]
    cnt = np.zeros(N_BINS)
    s3 = np.zeros(N_BINS)
    s2 = np.zeros(N_BINS)
    s1 = np.zeros(N_BINS)
    theta = THETA0
    events = 0
    for _ in range(n_steps):
        if rng.random() < p0:
            dth = DETA + (1.0 if rng.random() < 0.5 else -1.0) * w0 * DETA
            events += 1
        else:
            dth = DETA
        b = int(theta / (2 * np.pi) * N_BINS) % N_BINS
        cnt[b] += 1
        s3[b] += abs(dth) ** 3
        s2[b] += dth ** 2
        s1[b] += dth
        theta = (theta + dth) % (2 * np.pi)
    mask = cnt > 0
    cond3 = s3[mask] / cnt[mask] / DETA**3
    cond2 = s2[mask] / cnt[mask]
    cond1 = s1[mask] / cnt[mask]
    resid2 = cond1**2 / cond2        # drift 占比（1=确定性，0=纯噪声）
    return dict(
        code=code_name, label=f"stress p0={p0}", steps=n_steps, events=events,
        event_rate=events / n_steps,
        sup_cond3_ratio=float(cond3.max()),
        mean_cond3_ratio=float(cond3.mean()),
        sup_resid2=float(np.nanmax(resid2)),
        mean_resid2=float(np.nanmean(resid2)),
        bins_occupied=int(mask.sum()),
    )

# ================= [3] 生成元检验 =================
def generator_test(F, sigma, theta_star=0.5, Ns=(1e3, 1e4, 1e5, 1e6),
                   n_mc=500_000):
    """
    (c1) 固定步长 Δθ=F：G_N f = N·E[Δf]；f=θ → G_N θ = N·F（发散 ~N，解析精确）。
    (c2) 重标度 Δθ_N = F/N + σ/√N·ξ，f=θ²：
         N·E[Δf] = 2θ*F + F²/N + σ² = L + F²/N  ← 解析恒等式（无 MC 误差）。
         MC 仅验证抽样收敛：N·mean(dth) → F（噪声 ∝ √(N/n_mc)·σ），
         N·mean(dth²) → σ² + F²/N（噪声 ∝ √(N/n_mc)·σ²）。F²/N 项在 n_mc ≫ N 时才可分辨，
         故把 F²/N 收敛视为解析结论，MC 报告其自身收敛速率。
    """
    Ns = [int(N) for N in Ns]
    c1 = [dict(N=N, G_N=float(N * F), L=float(F)) for N in Ns]
    c2_analytic = [dict(N=N, L=float(2 * theta_star * F + sigma**2),
                        pred_dev=float(F**2 / N)) for N in Ns]
    c2_mc = []
    for N in Ns:
        xi = rng.standard_normal(n_mc)
        dth = F / N + sigma / np.sqrt(N) * xi
        m1 = np.mean(dth)
        m2 = np.mean(dth**2)
        c2_mc.append(dict(
            N=N,
            N_m1_minus_F=float(N * m1 - F),        # 应 ~ 0，误差 ∝ σ√(N/n_mc)
            N_m2_minus_sig2=float(N * m2 - sigma**2),  # 应 ≈ F²/N
            pred_F2_over_N=float(F**2 / N),
            mc_err_scale=float(sigma**2 * np.sqrt(N / n_mc)),
        ))
    return dict(c1=c1, c2_analytic=c2_analytic, c2_mc=c2_mc,
                F=float(F), sigma=float(sigma), theta_star=theta_star, n_mc=n_mc)

# ================= 主程序 =================
def main():
    results = {"meta": dict(
        date="2026-08-25", version="v2", deta=DETA, n_steps=N_STEPS, seed=RNG_SEED,
        anchor="δη = 1/sqrt(391.05) = 0.05056894054; "
               "c_d 来自 10.35 定理 10.35.1.07 逻辑 Z 翻转主阶系数",
    ), "physical": [], "stress": [], "generator": []}

    print("[1] 物理主检验（解析确定性轨道）")
    for cname in ("AG_r3", "AG_r4"):
        res = physical_analysis(cname)
        results["physical"].append(res)
        print(f"  {cname}: 期望事件 λ={res['expected_events']:.3e} "
              f"E[|Δθ|³]/δη³={res['global_s3_ratio']} (sup={res['sup_cond3_ratio']}) "
              f"drift 占比={res['sup_resid2']} 事件贡献上界={res['event_contrib_bound']:.2e}")

    print("[2] 应力测试（MC，事件率扫描）")
    for cname in ("AG_r3", "AG_r4"):
        for p0 in STRESS_P0:
            res = stress_mc(cname, p0)
            results["stress"].append(res)
            print(f"  {cname} p0={p0:.0e}: 事件={res['events']} "
                  f"sup E[|Δθ|³]/δη³={res['sup_cond3_ratio']:.6f} "
                  f"drift 占比 sup={res['sup_resid2']:.6f}")

    print("[3] 生成元检验")
    w0 = CODES["AG_r3"]["w0"]
    sigma_stress = np.sqrt(STRESS_P0[1]) * w0 * DETA   # p0=1e-2 单步噪声根
    gres = generator_test(F=DETA, sigma=sigma_stress)
    results["generator"].append(gres)
    print("  (c1) 固定步长 G_N θ = N·F（发散 ~N，解析）:")
    for row in gres["c1"]:
        print(f"    N={row['N']:>10d}  G_N={row['G_N']:.6e}  L={row['L']:.6e}")
    print("  (c2) 解析恒等式 N·E[Δf] = L + F²/N（f=θ²）:")
    for row in gres["c2_analytic"]:
        print(f"    N={row['N']:>10d}  L={row['L']:.6e}  pred F²/N={row['pred_dev']:.6e}")
    print("  (c2) MC 收敛验证（n_mc=%d）:" % gres["n_mc"])
    for row in gres["c2_mc"]:
        print(f"    N={row['N']:>10d}  N·mean(dθ)−F={row['N_m1_minus_F']:.3e} "
              f"N·mean(dθ²)−σ²={row['N_m2_minus_sig2']:.3e} (pred {row['pred_F2_over_N']:.2e}) "
              f"MC 噪声标度={row['mc_err_scale']:.3e}")

    outdir = "output/A3_check"
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "a3_results_v2.json")
    with open(outpath, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n结果已写入 {outpath}")

if __name__ == "__main__":
    main()
