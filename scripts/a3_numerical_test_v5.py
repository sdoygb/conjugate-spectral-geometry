"""A3 数值检验 v5 — 向量化工批量 + 简化假设
预期产出: 
  (a) 三阶/四阶矩比 → 确认有界性
  (b) 初相依赖幅度  → 确认漂移贡献
  (c) Richardson外推比率 → 判断收敛阶"""

import numpy as np
from math import pi, sqrt

ETA   = 0.05058
ALPHA = 0.3
BETA  = 1.5
SIGMA0= 0.5

def make_noise(n_samples):
    """确定性伪随机序列（xorshift64）"""
    s = np.arange(n_samples, dtype=np.uint64) ^ 7919
    out = np.empty(n_samples, dtype=np.float64)
    for i in range(n_samples):
        s_val = s[i]
        s_val = ((s_val << 13) ^ s_val) & ((1<<64)-1)
        s_val = ((s_val << 17) ^ s_val) & ((1<<64)-1)
        s_val = ((s_val << 5) ^ s_val) & ((1<<64)-1)
        s[i] = s_val
        out[i] = 2.0 * (s_val >> 11) / float(1<<63) - 1.0
    return out

print("="*50)
print("A3 Test v5 (vectorized)")
print("="*50)

# ====== (a) Third moment boundedness ======
print("\n--- (a) Third-moment boundedness ---")
MAX_N = 5000
N_SEGS = 10
all_ratios = []

for seg in range(N_SEGS):
    theta_0 = -pi/2 + seg * pi / (N_SEGS - 1)
    seeds = make_noise(MAX_N)
    r = seeds[:MAX_N]
    
    # Vectorized: precompute deltas for all steps at once
    mu = ALPHA * np.cos(theta_0)
    sig = SIGMA0 * np.sqrt(1.0 + BETA * np.cos(theta_0)**2)
    deltas = mu * ETA + sig * np.sqrt(ETA) * r
    
    m3 = float(np.mean(np.abs(deltas)**3))
    m4 = float(np.mean(deltas**4))
    eta3 = ETA**3
    eta4 = ETA**4
    
    all_ratios.append(m3/eta3)
    print(f"  Seg {seg}: E[|Δθ|³]/η³={m3/eta3:.4f}, E[Δθ⁴]/η⁴={m4/eta4:.4f}")

print(f"\n  Across segments: mean3={np.mean(all_ratios):.4f} ± {np.std(all_ratios):.4f}")
pass_a = max(all_ratios) < 200 and np.all(np.array(all_ratios) > 0)
print(f"  => {'PASS' if pass_a else 'FAIL'}: third moment bounded")

# ====== (b) Phase-angle dependence of second moment ======
print("\n--- (b) Second-moment phase dependence ---")
PHI_LIST = [-pi/2, -pi/4, 0, pi/4, pi/2]
mean_sq_phis = {}

for phi in PHI_LIST:
    seeds = make_noise(MAX_N)
    r = seeds[:MAX_N]
    mu = ALPHA * np.cos(phi)
    sig = SIGMA0 * np.sqrt(1.0 + BETA * np.cos(phi)**2)
    deltas = mu * ETA + sig * np.sqrt(ETA) * r
    
    ms = float(np.mean(deltas**2))
    var_ms = float(np.var(deltas**2))
    mean_sq_phis[phi] = ms
    print(f"  θ₀={phi:+6.3f}: E[Δθ²]={ms:.8f}, Var={var_ms:.8f}")

vals = list(mean_sq_phis.values())
range_sq = max(vals) - min(vals)
mean_g = float(np.mean(vals))
rel_dep = range_sq / mean_g
print(f"\n  Relative range = {rel_dep:.4%}")
print(f"  Diff contribution: {ALPHA * ETA:.5f} vs diff: {SIGMA0 * sqrt(ETA):.5f}")
pass_b = rel_dep > 0.01
print(f"  => {'Phase-dependent' if pass_b else 'Uniform-ish'}")

# ====== (c) Convergence rate via Richardson ratio ======
print("\n--- (c) Generator convergence rate ---")

N_VALS = [50, 200, 1000]
N_TRIALS = 100

results = {}
for func_name, fc, deriv_fc in [('cos', np.cos, lambda x: -np.sin(x)),
                                   ('sin', np.sin, np.cos)]:
    print(f"\n  f(x) = {func_name}(x):")
    ests = {}
    for N in N_VALS:
        G_vals = []
        for t in range(N_TRIALS):
            seed_base = t * 3571 + abs(hash(func_name) % 10000)
            seq = make_noise(N)
            r_arr = seq[:N]
            
            th = 0.0
            diffs = 0.0
            for i in range(N):
                d = ALPHA * np.cos(th) * ETA + SIGMA0 * np.sqrt(1.0 + BETA*np.cos(th)**2) * np.sqrt(ETA) * r_arr[i]
                diffs += fc(th + d) - fc(th)
                th = (th + d) % (2*pi)
            G_vals.append(N * diffs / N)
        
        g_mean = float(np.mean(G_vals))
        g_std  = float(np.std(G_vals))
        ests[N] = (g_mean, g_std)
        print(f"    N={N:5d}: G̃_N = {g_mean:+.8f} ± {g_std:.8f}")
    
    results[func_name] = ests

# Richardson ratios
sorted_N = sorted(N_VALS)
print("\n  Richardson ratios (consecutive triplets):")
for func_name in ['cos', 'sin']:
    es = results[func_name]
    ratios = []
    for k in range(len(sorted_N)-2):
        denom = abs(es[sorted_N[k+1]][0] - es[sorted_N[k]][0])
        num   = abs(es[sorted_N[k+2]][0] - es[sorted_N[k+1]][0])
        if denom > 1e-15:
            ratios.append(num/denom)
    avg_r = float(np.mean(ratios)) if ratios else 0
    print(f"    {func_name}: ratios={[f'{r:.3f}' for r in ratios]}, avg={avg_r:.3f}")
    conv_ok = 0.1 < avg_r < 10
    print(f"    => {'Plausible O(1/N) or similar' if conv_ok else 'Unclear'}")

print("\n" + "="*50)
print("SUMMARY:")
print(f"  (a) Third-moment bounded:       {'✓' if pass_a else '✗'}")
print(f"  (b) Phase-angle dependence:     {'✓' if pass_b else '?'} ({rel_dep:.2%})")
print(f"  (c) Convergence rate:           ? (see Richardson above)")
print("="*50)
print("Done.")
