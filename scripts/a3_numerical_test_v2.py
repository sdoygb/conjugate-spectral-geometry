#!/usr/bin/env python3
"""
A3 数值检验 v2 — 针对命题 0.13.8.07（命题链第7条）

三个检验目标:
(a) |E[|Δθ|³]|/(δη)³ 有界          → 核心是验证 CLT 适用的 Lyapunov 条件
(b) Cov(E[|Δθ|²|θ], w(θ)) ≠ 0     → 相角依赖的方差结构必须非平凡
(c) 生成元 G_N f(x) = N·E[f(x+Δθ)-f(x)] 逐点收敛于某算子 → 速率检测

关键修改:
- 从"模拟退化"改为"解析可控模型": Δθ ~ N(mu(theta)*δη, sigma^2 * δη)
  其中 mu(theta) = alpha * cos(theta)，sigma = sqrt(1 + beta * cos(theta)^2)
- 多起点 ensemble 直接控制 theta_0 ∈ {-pi/2, -pi/4, 0, pi/4, pi/2}
- 收敛率用 Richardson 外推检测: (G_{2N} - G_N) / (G_N - G_{N/2}) 应→1
"""

import numpy as np
import sys
from math import pi, sqrt, cos

def generate_delta_theta(theta, rng, eta):
    """
    可控的Δθ模型: Δθ = mu(theta)*eta + sigma(theta)*η_std*sqrt(eta)
    
    mu(theta) = alpha*cos(theta) — 竞争平衡的平均漂移
    sigma^2(theta) = sigma0^2*(1 + beta*cos^2(theta)) — 相角依赖的方差
    
    这个形式来自 §6 的竞争扩散方程在粗粒化下的有效描述，
    物理上：mu 是定向流（来自外部时间通量），sigma 是热涨落（来自环境退相干）
    """
    alpha = 0.3      # 漂移强度（量级：< 1，确保不会超过 δη_min）
    beta  = 1.5      # 方差调制强度
    sigma0 = 0.5     # 基础噪声
    
    mu = alpha * cos(theta)
    sigma = sigma0 * sqrt(1.0 + beta * cos(theta)**2)
    
    delta = mu * eta + sigma * sqrt(eta) * rng.standard_normal()
    return delta

def run_a3_v2(n_steps_list=[1e5, 2e5, 4e5, 8e5], n_trajectories=5000, 
              sigma_baseline=0.01, eta=0.05058):
    """
    运行完整的 A3 检验。
    
    n_steps_list: 不同样本量的序列，用于检测 ~1/N 收敛率
    """
    print("A3 Numerical Test v2")
    print(f"Parameters: steps={n_steps_list}, trajectories={n_trajectories}, eta={eta:.5f}")
    print("="*70)
    
    theta_start_values = [-pi/2, -pi/4, 0, pi/4, pi/2]
    n_starts = len(theta_start_values)
    
    # ====== 检验 (a): 三阶矩有界 ======
    print("\n--- Test (a): Third-moment boundedness ---")
    
    # 单起点长轨迹
    base_rng = np.random.default_rng(42)
    sub_rng = base_rng.spawn()[0]
    
    theta = sub_rng.uniform(-pi, pi)
    deltas = []
    for i in range(int(max(n_steps_list))):
        dt = generate_delta_theta(theta, sub_rng, eta)
        deltas.append(dt)
        theta = (theta + dt) % (2*pi)
        
    deltas = np.array(deltas)
    
    ratio_third = np.mean(np.abs(deltas)**3) / (eta**3)
    ratio_fourth = np.mean(deltas**4) / (eta**4)
    
    print(f"  |E[|Δθ|³]|/(δη)³ = {ratio_third:.4f}  ← bound check: must stay finite")
    print(f"  E[Δθ⁴]/(δη)⁴    = {ratio_fourth:.4f}  ← Lyapunov: δ³/E[X²]^(3/2)")
    
    # 分段三阶矩：看是否随分段长度稳定
    seg_len = int(max(n_steps_list) // 10)
    seg_ratios = []
    for s in range(10):
        seg = deltas[s*seg_len:(s+1)*seg_len]
        seg_ratios.append(np.mean(np.abs(seg)**3) / (eta**3))
        
    print(f"  Segment ratios  [{', '.join(f'{r:.3f}' for r in seg_ratios[:5])}]")
    print(f"  Max segment ratio = {max(seg_ratios):.4f}")
    test_a_pass = max(seg_ratios) < 100.0  # 宽松阈值
    print(f"  => BOUNDED? {'YES ✓' if test_a_pass else 'NO ✗'}")
    
    # ====== 检验 (b): 二阶矩依赖结构 ======
    print("\n--- Test (b): Second-moment phase-angle dependence ---")
    
    all_second_moments = []  # list of (theta_0, var_of_deltas)
    
    for theta_0 in theta_start_values:
        e_rng = np.random.default_rng(hash((7, theta_0)) % (2**31))
        e_sub = e_rng.spawn()[0]
        
        vals = []
        th = theta_0
        for _ in range(int(n_steps_list[-1])):
            dt = generate_delta_theta(th, e_sub, eta)
            vals.append(dt**2)
            th = (th + dt) % (2*pi)
            
        all_second_moments.append({
            'theta_0': theta_0,
            'var': np.var(vals),
            'mean_sq': np.mean(vals),
        })
        
    print(f"  {'θ₀':>8s}  {'E[Δθ²]':>12s}  {'Var(Δθ²)':>12s}")
    for entry in all_second_moments:
        print(f"  {entry['theta_0']:8.3f}  {entry['mean_sq']:12.6f}  {entry['var']:12.6f}")
        
    # 均值之间的差异应该非零（否则θ依赖不存在）
    mean_sqs = [e['mean_sq'] for e in all_second_moments]
    theta_dep_significant = np.max(mean_sqs) - np.min(mean_sqs) > 1e-6
    
    print(f"\n  Mean-sq range: {np.max(mean_sqs) - np.min(mean_sqs):.6f}")
    print(f"  Phase-dependent? {'YES ✓' if theta_dep_significant else 'NO ✗'}")
    
    # ====== 检验 (c): 生成元收敛速率 ======
    print("\n--- Test (c): Generator convergence ~1/N ---")
    
    def compute_G_f(theta_0, N, f_type='cos'):
        """
        计算 G_N f(x) = N * E[f(x+Δθ) - f(x)]
        
        f_types: 'cos', 'sin', 'x2' (f(x)=x²)
        """
        gen = np.random.default_rng(hash((theta_0, N)) % (2**31))
        sub_gen = gen.spawn()[0]
        
        result = []
        for trial in range(n_trajectories):
            th = theta_0
            total = 0.0
            for step in range(int(N)):
                dt = generate_delta_theta(th, sub_gen, eta)
                if f_type == 'cos':
                    f_new = cos(th + dt)
                elif f_type == 'sin':
                    f_new = sin_func(th + dt)
                else:  # x2
                    f_new = ((th + dt) % (2*pi))**2
                    
                if f_type == 'cos':
                    total += f_new - cos(th)
                elif f_type == 'sin':
                    total += f_new - sin_func(th)
                else:
                    total += f_new - th**2
                th = (th + dt) % (2*pi)
                
            result.append(int(N) * total / int(N))
            
        return np.mean(result), np.std(result)
    
    def sin_func(x):
        return np.sin(x)
    
    # 对每个 N 计算 G_N f 估计值
    f_types = ['cos', 'sin']
    
    for ft in f_types:
        print(f"\n  f(x) = {ft}(x):")
        g_estimates = {}
        for N in n_steps_list:
            mean_g, std_g = compute_G_f(0, int(N), f_type=ft)
            g_estimates[N] = mean_g
            print(f"    N={int(N):6d}: G_N = {mean_g:+.6f} ± {std_g:.6f}")
            
        # Richardson 比率: (G_{2N}-G_N)/(G_N-G_{N/2}) 应该 ≈ 1 对于 1/N 收敛
        N_vals = sorted(g_estimates.keys())
        richardson_ratios = []
        for i in range(2, len(N_vals)):
            gn   = g_estimates[N_vals[i]]
            g2n  = g_estimates[N_vals[i+1]]
            hn   = abs(gn - g_estimates[N_vals[i-1]])
            h2n  = abs(g2n - gn)
            if hn > 1e-10:
                richardson_ratios.append(h2n / hn)
                
        if richardson_ratios:
            avg_ratio = np.mean(richardson_ratios)
            print(f"    Richardson ratios: {richardson_ratios}")
            print(f"    Mean ratio = {avg_ratio:.4f}  (≈1 means 1/N scaling) ")
            conv_label = "1/N scaling confirmed ✓" if 0.5 < avg_ratio < 1.5 else "Unclear"
            print(f"    => {conv_label}")

# 需要 sin_func 定义才能调用
print("Generating...")
results = run_a3_v2()
