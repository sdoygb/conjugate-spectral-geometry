#!/usr/bin/env python3
"""
A3 数值检验 v4 — 向量化模拟 + 收敛率检测
对应 0.13 §3 递降采样定理的三个子命题验证
"""

import numpy as np
from math import pi, sqrt

N_TRAJ = 2000          # 每条轨迹样本数
ETA    = 0.05058       # 临界步长
ALPHA  = 0.3           # 漂移系数
BETA   = 1.5           # 扩散调制系数
SIGMA0 = 0.5           # 基础噪声尺度

# ===== 工具函数 =====
def cos_f(x): return np.cos(x)
def sin_f(x): return np.sin(x)

def step_delta(theta, r):
    """给定当前相位 theta 和标准正态扰动 r，返回一步 Δθ"""
    mu = ALPHA * cos_f(theta)
    sig = SIGMA0 * np.sqrt(1.0 + BETA * cos_f(theta)**2)
    return mu * ETA + sig * np.sqrt(ETA) * r

def simulate_single(N, theta0, seeds):
    """单条轨迹：初始 theta0，逐步积分返回 (theta_path, deltas)"""
    thetas = np.empty(N+1)
    deltas = np.empty(N)
    thetas[0] = theta0
    
    for i in range(N):
        r_i = 2.0 * (seeds[i] % 1.0) - 1.0  # [-1, 1]
        d = step_delta(thetas[i], r_i)
        deltas[i] = d
        thetas[i+1] = (thetas[i] + d) % (2*pi)
    
    return thetas, deltas

def generate_seeds(base_seed, count):
    """确定性种子序列（替代 spawn）"""
    state = base_seed
    out = np.empty(count)
    for i in range(count):
        state = (state * 6364136223846793005 + 1) & ((1<<64)-1)
        out[i] = state / float(1<<64)
    return out

# ====== (a) 三阶矩有界 ======
print("="*60)
print("A3 Numerical Test v4")
print(f"N_TRAJ={N_TRAJ}, ETA={ETA:.5f}")
print("="*60)

max_N = int(1e5)  # 降低到 1e5 保证速度

print("\n--- (a) Third-moment boundedness ---")
all_deltas = []
seed_base = 12345
r_seq = generate_seeds(seed_base, max_N * N_TRAJ)

for t in range(N_TRAJ):
    theta_t = -pi/2 + t * pi / (N_TRAJ-1)
    _th, _dels = simulate_single(max_N, theta_t, r_seq[t*max_N:(t+1)*max_N])
    all_deltas.extend(_dels.tolist())

all_deltas = np.array(all_deltas)
ratio_3rd = float(np.mean(np.abs(all_deltas)**3)) / (ETA**3)
ratio_4th = float(np.mean(all_deltas**4)) / (ETA**4)

print(f"  E[|Δθ|³]/η³  = {ratio_3rd:.4f}")
print(f"  E[Δθ⁴]/η⁴    = {ratio_4th:.4f}")

# 分段检查
seg_n = max_N // 10
seg_means = []
for s in range(10):
    seg = all_deltas[s*seg_n:(s+1)*seg_n]
    seg_means.append(float(np.mean(np.abs(seg)**3)))

overall_bound = max(seg_means) / min(seg_means[:5]) if min(seg_means[:5]) > 1e-12 else 999
print(f"  Seg std/max = {np.std(seg_means):.4f} / {np.max(seg_means):.4f}")
print(f"  Ratio spread = {overall_bound:.2f}x")
test_a = overall_bound < 10.0 and ratio_3rd < 100.0
print(f"  => {'PASS: third moment bounded' if test_a else 'FAIL'}")

# ====== (b) 二阶矩相角依赖 ======
print("\n--- (b) Second-moment phase-angle dependence ---")

phi_vals = [-pi/2, -pi/4, 0, pi/4, pi/2]
mean_sq_at_phi = {}

for phi in phi_vals:
    sq_dels = []
    for t in range(N_TRAJ):
        seed_t = t * 1000 + abs(int(phi * 100))
        r_seq = generate_seeds(seed_t, max_N)
        _, dels = simulate_single(max_N, phi, r_seq)
        sq_dels.extend((dels**2).tolist())
    
    mean_sq = float(np.mean(sq_dels))
    var_sq  = float(np.var(sq_dels))
    mean_sq_at_phi[phi] = mean_sq
    print(f"  θ₀={phi:8.3f}: E[Δθ²]={mean_sq:.6f}, Var(Delta²)={var_sq:.6f}")

range_sq = max(mean_sq_at_phi.values()) - min(mean_sq_at_phi.values())
mean_sq_global = float(np.mean(list(mean_sq_at_phi.values())))
dependence_ratio = range_sq / (mean_sq_global + 1e-12)

print(f"\n  Mean-sq range = {range_sq:.6f}, relative = {dependence_ratio:.2%}")
print(f"  => {'Phase-dependent (non-trivial)' if dependence_ratio > 0.01 else 'Uniform (trivial)'}")

# ====== (c) 生成元收敛速率 ======
print("\n--- (c) Generator convergence rate ---")

N_test_values = [100, 500, 1000, 5000]
n_trials = 500  # 足够多以获得稳定估计

for func_name, func, deriv_func in [('cos', cos_f, lambda x: -sin_f(x)), 
                                       ('sin', sin_f, cos_f)]:
    print(f"\n  f(x) = {func_name}(x):")
    g_estimates = {}
    g_stds     = {}
    
    for N in N_test_values:
        G_vals = []
        for trial in range(n_trials):
            seed_tr = trial * 7919 + abs(hash(func_name) % 10000)
            r_seq = generate_seeds(seed_tr, N)
            
            # 快速计算: 从 theta0=0 出发
            th = 0.0
            total_diff = 0.0
            for i in range(N):
                r_i = 2.0 * (r_seq[i] % 1.0) - 1.0
                d = step_delta(th, r_i)
                diff = func(th + d) - func(th)
                total_diff += diff
                th = (th + d) % (2*pi)
            
            G_N = N * total_diff / N  # = total_diff
            G_vals.append(G_N)
        
        g_mean = float(np.mean(G_vals))
        g_std  = float(np.std(G_vals))
        g_estimates[N] = g_mean
        g_stds[N]      = g_std
        print(f"    N={N:5d}: G_N = {g_mean:+.6f} ± {g_std:.6f}")
    
    # Richardson 比率判断收敛阶
    sorted_N = sorted(g_estimates.keys())
    richardsons = []
    for k in range(len(sorted_N)-2):
        denom = abs(g_estimates[sorted_N[k+1]] - g_estimates[sorted_N[k]])
        num   = abs(g_estimates[sorted_N[k+2]] - g_estimates[sorted_N[k+1]])
        if denom > 1e-12:
            richardsons.append(num/denom)
    
    if richardsons:
        avg_r = float(np.mean(richardsons))
        print(f"    Richardson ratios: {[f'{r:.3f}' for r in richardsons]}")
        print(f"    Average = {avg_r:.3f}  (~1 means O(1/N))")
        convergence_ok = 0.3 < avg_r < 2.0
        print(f"    => {'O(1/N) convergence confirmed' if convergence_ok else 'Unclear convergence'}")

print("\n" + "="*60)
print("Summary:")
print(f"  (a) Third-moment bounded:       {'✓' if test_a else '✗'}")
print(f"  (b) Phase-angle dependence:     {'✓' if dependence_ratio > 0.01 else '?'} ({dependence_ratio:.2%})")
print(f"  (c) Convergence rate ≈ 1/N:     ? (see above)")
print("="*60)
print("Done.")
