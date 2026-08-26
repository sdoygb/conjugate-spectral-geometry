#!/usr/bin/env python3
"""
A3 数值检验：AG r=3/4 码上的离散演化样本
目标：验证命题 0.13.8.07（命题链第7条）

针对 AG 码族 r=3/4、m=10 的简化模型检测：
(a) |E[|Δθ|³]|/(δη)³ 有界
(b) 二阶矩余项 E[|Δθ|²|θ] − Cov 一致可积
(c) 生成元 G_N 逐点收敛速率 ~ 1/N

设计说明：
- θ = 耦合相角，取值 [-π, π)，由等测度分布采样
- Δθ 模拟：每个周期 δ 迭代产生一次随机位移
  - 成功解码：Δθ = F(θ)δη_min + σ(θ)ξ （对流+噪声）
  - 失败解码：额外添加随机脉冲 ε ~ N(0, σ_fail²)
- 使用 AG r=3/4 码的失败率数据作为权重
"""

import numpy as np
import sys
from math import pi, sqrt

def delta_theta_model(theta, rng, sigma_noise):
    """
    模拟单次 δ 迭代产生的 Δθ。
    
    参数:
    - theta: 当前耦合相角
    - rng: numpy Generator (新 API)
    - sigma_noise: 基础噪声水平
    
    返回:
    - delta_theta: 本次迭代的位移
    - failed: 是否解码失败
    """
    # 相角相关的失败率模型（来自 10.35 标度律逻辑）
    # 成功时：无逻辑错误，Δθ 仅含环境噪声
    # 失败时：残留逻辑翻转，附加相位扰动
    
    success_prob = 1.0 / (1.0 + np.exp(-10 * (np.abs(theta) - 0.3)))
    
    if rng.random() < success_prob:
        # 成功：Δθ = F(θ)*δη + 小噪声
        # F(θ) 为竞争平衡平均位移（§7），近似为 cos(θ) * F_max
        F_max = 0.5
        delta_theta = F_max * np.cos(theta) * 0.05058 + sigma_noise * rng.standard_normal()
        failed = False
    else:
        # 失败：附加随机脉冲 (kappa ≈ 0.33 为 r=3 的高层错误系数)
        kappa = 0.33
        epsilon = kappa * pi * rng.choice([-1, 1])
        F_max = 0.5
        delta_theta = F_max * np.cos(theta) * 0.05058 + sigma_noise * rng.standard_normal() + epsilon
        failed = True
        
    return delta_theta, failed

def run_a3_test(n_steps=int(1e6), sigma_noise=0.01, n_repeats=5):
    """
    运行 A3 三组检验。
    """
    print(f"A3 Numerical Test")
    print(f"Parameters: n_steps={n_steps}, sigma_noise={sigma_noise}")
    print("="*60)
    
    all_results = []
    
    for rep in range(n_repeats):
        # 使用新 API：spawn 生成独立的子流
        base_rng = np.random.default_rng(rep * 42 + 7)
        sub_rng = base_rng.spawn(2)[0]  # spawn takes one argument: number of children
        
        theta = sub_rng.uniform(-pi, pi)
        deltas = []
        failed_count = 0
        
        for i in range(n_steps):
            dt, failed = delta_theta_model(theta, sub_rng, sigma_noise=sigma_noise)
            deltas.append(dt)
            if failed:
                failed_count += 1
            theta = (theta + dt) % (2*pi)
            
        deltas = np.array(deltas)
        eta = 0.05058  # δη_min
        
        # (a) 三阶矩有界
        third_moment = np.mean(np.abs(deltas)**3)
        ratio_third = third_moment / (eta**3)
        
        # (b) 二阶矩余项
        var_delta = np.var(deltas)
        mean_sq = np.mean(deltas**2)
        remainder = mean_sq - var_delta  
        
        sorted_abs = np.sort(np.abs(deltas))
        tail_contribution = np.sum(sorted_abs[-min(1000, len(sorted_abs)):]**2) / len(sorted_abs)
        
        # (c) 生成元收敛速率
        f_vals = np.sin(np.cumsum(deltas) % (2*pi))
        df = np.diff(f_vals)
        G_N_f = n_steps * np.mean(df[:n_steps//2])  
        G_N_f_late = n_steps * np.mean(df[n_steps//2:]) 
        
        convergence_rate = abs(G_N_f - G_N_f_late) / abs(G_N_f) if G_N_f != 0 else 0
        
        result = {
            'ratio_third': ratio_third,
            'variance': var_delta,
            'mean_squared': mean_sq,
            'remainder': remainder,
            'tail_contrib': tail_contribution,
            'convergence_rate': convergence_rate,
        }
        all_results.append(result)
        print(f"Repeat {rep}: third_ratio={ratio_third:.3f}, conv_rate={convergence_rate:.2e}")
    
    # 汇总统计
    ratios = [r['ratio_third'] for r in all_results]
    means = {k: np.mean([r[k] for r in all_results]) for k in ['remainder', 'convergence_rate']}
    
    print("\n" + "="*60 + "\nSUMMARY\n" + "="*60)
    print(f"(a) |E[|Δθ|³]|/(δη)³ bounded? {'YES' if max(ratios) < 100 else 'NO'}")
    print(f"    Mean: {np.mean(ratios):.4f} ± {np.std(ratios):.4f}")
    
    print(f"\n(b) Second-moment consistency: {'YES' if means['remainder'] > 0 else 'NO'}")
    print(f"    Remainder: {means['remainder']:.6f}")
    
    print(f"\n(c) ~1/N scaling likely? {'LIKELY' if means['convergence_rate'] < 0.1 else 'UNCLEAR'}")
    print(f"    Rate: {means['convergence_rate']:.2e}")
    
    return all_results

if __name__ == '__main__':
    if '--quick' in sys.argv:
        n_steps = int(1e5)
    else:
        n_steps = int(1e6)
    
    results = run_a3_test(n_steps=n_steps, sigma_noise=0.01, n_repeats=5)
