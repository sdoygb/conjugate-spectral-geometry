#!/usr/bin/env python3
"""
A3 数值检验 v3 — 修复 numpy RNG API 兼容性问题
"""

import numpy as np
from math import pi

def generate_delta_theta(theta, rng, eta):
    """可控模型: Δθ ~ N(mu*cos(theta), sigma^2*(1+beta*cos^2(theta)))"""
    alpha = 0.3
    beta  = 1.5
    sigma0 = 0.5
    
    mu = alpha * cos(theta) if 'cos' in dir() else np.cos(theta)
    sigma = sigma0 * np.sqrt(1.0 + beta * np.cos(theta)**2)
    
    delta = mu * eta + sigma * np.sqrt(eta) * rng.standard_normal()
    return delta

# ====== 运行引擎 ======
n_steps_list = [1e5, 2e5, 4e5, 8e5]
n_trajectories = 5000
eta = 0.05058

print("A3 Numerical Test v3")
print(f"Parameters: steps={n_steps_list}, trajectories={n_trajectories}, eta={eta:.5f}")
print("="*70)

theta_start_values = [-pi/2, -pi/4, 0, pi/4, pi/2]

# ====== (a) 三阶矩有界 ======
print("\n--- Test (a): Third-moment boundedness ---")

base_seed = 42
all_deltas = []
th = np.random.uniform(-pi, pi, size=1)[0]

for n in range(int(n_steps_list[-1])):
    seed_val = hash((base_seed, th)) % (2**31)
    rng = np.random.default_rng(seed_val)
    dt = generate_delta_theta(th, rng, eta)
    all_deltas.append(dt)
    th = (th + dt) % (2*pi)
    
deltas = np.array(all_deltas)
ratio_third = np.mean(np.abs(deltas)**3) / (eta**3)
ratio_fourth = np.mean(deltas**4) / (eta**4)

print(f"  |E[|Delta|^3]|/(eta)^3 = {ratio_third:.4f}  (bound check)")
print(f"  E[Delta^4]/(eta)^4     = {ratio_fourth:.4f}  (Lyapunov)")

seg_len = int(n_steps_list[-1] // 10)
seg_ratios = []
for s in range(10):
    seg = deltas[s*seg_len:(s+1)*seg_len]
    seg_ratios.append(float(np.mean(np.abs(seg)**3) / (eta**3)))
        
print(f"  Segment ratios (first 5): [{', '.join(f'{r:.3f}' for r in seg_ratios[:5])}]")
test_a_pass = max(seg_ratios) < 100.0
print(f"  => BOUNDED? {'YES' if test_a_pass else 'NO'}")

# ====== (b) 二阶矩相角依赖 ======
print("\n--- Test (b): Second-moment phase-angle dependence ---")

for theta_0 in theta_start_values:
    vals = []
    th = theta_0
    for n in range(int(n_steps_list[-1])):
        seed_val = hash((theta_0, n)) % (2**31)
        rng = np.random.default_rng(seed_val)
        dt = generate_delta_theta(th, rng, eta)
        vals.append(dt**2)
        th = (th + dt) % (2*pi)
        
    mean_sq = float(np.mean(vals))
    var_sq  = float(np.var(vals))
    print(f"  theta_0={theta_0:8.3f}: E[Delta^2]={mean_sq:.6f}, Var(Delta^2)={var_sq:.6f}")

mean_sqs_all = []
for i, theta_0 in enumerate(theta_start_values):
    vals = []
    th = theta_0
    for n in range(int(n_steps_list[-1])):
        seed_val = hash((theta_0, n)) % (2**31)
        rng = np.random.default_rng(seed_val)
        dt = generate_delta_theta(th, rng, eta)
        vals.append(dt**2)
        th = (th + dt) % (2*pi)
    mean_sqs_all.append(float(np.mean(vals)))

range_sq = max(mean_sqs_all) - min(mean_sqs_all)
print(f"\n  Mean-sq range: {range_sq:.6f}")
print(f"  Phase-dependent? {'YES' if range_sq > 1e-6 else 'NO'}")

# ====== (c) 生成元收敛速率 ======
print("\n--- Test (c): Generator convergence ---")

def sin_func(x):
    return np.sin(x)

for f_type in ['cos', 'sin']:
    print(f"\n  f(x) = {f_type}(x):")
    g_estimates = {}
    
    for N in n_steps_list:
        results_list = []
        for trial in range(min(100, n_trajectories)):  # Reduced for speed
            seed_trial = hash((f_type, int(N), trial)) % (2**31)
            rng = np.random.default_rng(seed_trial)
            
            th = 0.0
            total_diff = 0.0
            for step in range(int(N)):
                dt = generate_delta_theta(th, rng, eta)
                if f_type == 'cos':
                    total_diff += np.cos(th + dt) - np.cos(th)
                else:
                    total_diff += sin_func(th + dt) - sin_func(th)
                th = (th + dt) % (2*pi)
                
            G_N = int(N) * total_diff / int(N)
            results_list.append(G_N)
            
        mean_g = float(np.mean(results_list))
        std_g  = float(np.std(results_list))
        g_estimates[int(N)] = mean_g
        print(f"    N={int(N):7d}: G_N = {mean_g:+.6f} +/- {std_g:.6f}")
    
    # Richardson ratio
    N_sorted = sorted(g_estimates.keys())
    richardson = []
    for i in range(2, len(N_sorted)):
        denom = abs(g_estimates[N_sorted[i]] - g_estimates[N_sorted[i-1]])
        if denom > 1e-10:
            num = abs(g_estimates[N_sorted[i+1]] - g_estimates[N_sorted[i]])
            richardson.append(num/denom)
            
    if richardson:
        avg_rich = float(np.mean(richardson))
        print(f"    Richardson ratios: {[f'{r:.2f}' for r in richardson]}")
        print(f"    Mean ratio = {avg_rich:.4f}  (~1 means 1/N)")
        print(f"    => {'CONFIRMED' if 0.5 < avg_rich < 1.5 else 'UNCLEAR'}")

print("\nDone.")
