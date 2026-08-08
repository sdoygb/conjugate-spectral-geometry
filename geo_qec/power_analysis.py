"""power_analysis.py —— 任务 5：10.36 四阶标度律判别方案的统计功效分析

模拟实验流程：对 AG 完备码四档（m=10, d=4/8/16/32），
  1. 解析 loss 真值：loss_true(theta) = b + c_d*theta^d*(1 + rho*theta^2)
     （主阶 + 次主阶，系数来自 10.35 闭式；b = 基线）
  2. 每点 N 次 shots：loss_hat ~ Binomial(N, loss_true)/N
  3. 点选择：loss_hat > 3b（基线淹没剔除，10.36 §6.1 精神）
  4. 次主阶修正：y = ln loss_hat - ln(1 + rho*theta^2)（rho 为无自由参数闭式）
  5. 加权线性拟合 y = ln c + d*ln theta，权重 w = N*loss_hat/(1-loss_hat)
  6. 输出 d_hat、sigma_d、覆盖率 P(|d_hat-d|<=2*sigma_d)、判别余量 4/sigma_d

扫描：N x 档 x 基线 b x 次主阶修正开关；对照 10.36 §5 的 sigma_d 目标值
（0.028/0.062/0.098/0.198 @ N=2e5, sigma_rel=5%）。
"""
import numpy as np
from param_table import ag_params

# ---------------- 档配置（10.36 §3 推荐采样点）----------------
BANDS = {
    4:  dict(r=1, theta=np.array([0.02, 0.03, 0.04, 0.05, 0.06])),
    8:  dict(r=2, theta=np.array([0.06, 0.07, 0.08, 0.09, 0.10])),
    16: dict(r=3, theta=np.array([0.21, 0.23, 0.25, 0.27, 0.29])),
    32: dict(r=4, theta=np.array([0.46, 0.48, 0.50, 0.52, 0.54])),
}
M = 10

def load_band(d):
    """返回 (c_d, rho, theta, d)"""
    p = ag_params(M, BANDS[d]['r'])
    return p['c_d'], p['rho'], BANDS[d]['theta'], d

def simulate_band(d, N, b, with_corr=True, ntrials=300, seed=0):
    """对一档做 ntrials 次判别模拟，返回 (d_hat 数组, sigma_d 数组, 有效点数数组)"""
    rng = np.random.default_rng(seed)
    c_d, rho, theta, _ = load_band(d)
    loss_true = b + c_d * theta ** d * (1.0 + rho * theta ** 2)
    x = np.log(theta)
    dhats = np.zeros(ntrials)
    sigs = np.zeros(ntrials)
    npts = np.zeros(ntrials, dtype=int)
    for t in range(ntrials):
        loss_hat = rng.binomial(N, loss_true) / N
        ok = (loss_hat > 3 * b) & (loss_hat > 0)
        if ok.sum() < 3:
            dhats[t], sigs[t], npts[t] = np.nan, np.nan, ok.sum()
            continue
        lh = loss_hat[ok]
        xx = x[ok]
        if with_corr:
            yy = np.log(lh) - np.log(1.0 + rho * theta[ok] ** 2)
        else:
            yy = np.log(lh)
        w = N * lh / (1.0 - lh)                      # 1/var(ln loss_hat)（delta 方法）
        wsum = w.sum()
        xw = (w * xx).sum() / wsum
        yw = (w * yy).sum() / wsum
        Sxx = (w * (xx - xw) ** 2).sum()
        Sxy = (w * (xx - xw) * (yy - yw)).sum()
        dhats[t] = Sxy / Sxx
        sigs[t] = 1.0 / np.sqrt(Sxx)
        npts[t] = ok.sum()
    return dhats, sigs, npts

def run():
    Ns = [5e4, 1e5, 2e5, 5e5, 1e6]
    bs = [0.0, 1e-3, 1e-2]
    print("=" * 78)
    print("任务 5：10.36 判别方案统计功效分析（m=10，四档；每档 300 次模拟）")
    print("=" * 78)

    # ---- 表 1：sigma_d vs N（b=0，次主阶修正开）----
    print("\n[表 1] sigma_d vs N（b=0，次主阶修正开；10.36 目标 @N=2e5: "
          "0.028/0.062/0.098/0.198）")
    print(f"{'N':>10} | " + " | ".join(f"d={d:<6}" for d in BANDS))
    sig_table = {}
    for N in Ns:
        row = []
        for d in BANDS:
            _, sigs, _ = simulate_band(d, int(N), 0.0, True, ntrials=300, seed=7)
            sig_table[(d, int(N))] = np.nanmean(sigs)
            row.append(f"{np.nanmean(sigs):.4f}")
        print(f"{int(N):>10,} | " + " | ".join(row))

    # ---- 表 2：覆盖率 P(|d_hat-d|<=2 sigma_d)（b=0）----
    print("\n[表 2] 覆盖率（b=0，修正开；目标 ≈ 0.95）")
    print(f"{'N':>10} | " + " | ".join(f"d={d:<6}" for d in BANDS))
    for N in Ns:
        row = []
        for d in BANDS:
            dhats, sigs, _ = simulate_band(d, int(N), 0.0, True, ntrials=300, seed=11)
            cov = np.nanmean(np.abs(dhats - d) <= 2 * sigs)
            row.append(f"{cov:.3f}")
        print(f"{int(N):>10,} | " + " | ".join(row))

    # ---- 表 3：无修正的系统偏差（次主阶污染）----
    print("\n[表 3] 无次主阶修正时的斜率偏差 mean(d_hat - d)（b=0，N=2e5）——"
          "10.36 §6.5 必须用闭式 rho 修正的证据")
    print(f"{'档':>6} | {'mean(d_hat-d) 无修正':>20} | {'sigma_d 无修正':>14} | {'偏差/sigma':>10} | {'mean(d_hat-d) 有修正':>20}")
    for d in BANDS:
        dh0, sg0, _ = simulate_band(d, int(2e5), 0.0, False, ntrials=300, seed=13)
        dh1, sg1, _ = simulate_band(d, int(2e5), 0.0, True,  ntrials=300, seed=13)
        m0, m1 = np.nanmean(dh0 - d), np.nanmean(dh1 - d)
        s0 = np.nanmean(sg0)
        print(f"d={d:<4} | {m0:+.4f} | {s0:.4f} | {m0/s0:+7.1f} | {m1:+.4f}")

    # ---- 表 4：基线 b 的影响（d=4 与 d=32，N=2e5，修正开）----
    print("\n[表 4] 基线 b 的影响（修正开，N=2e5）：sigma_d 与有效点数")
    print(f"{'档':>6} | " + " | ".join(f"b={b:.0e}".replace('e-0','e-') for b in bs))
    for d in [4, 8, 32]:
        row = []
        for b in bs:
            _, sigs, npts = simulate_band(d, int(2e5), b, True, ntrials=300, seed=17)
            row.append(f"{np.nanmean(sigs):.4f}({np.nanmean(npts):.1f}点)")
        print(f"d={d:<4} | " + " | ".join(row))

    # ---- 表 5：协议建议：为达到 sigma_d <= 0.1 且判别余量 >= 40sigma 的最小 N ----
    print("\n[表 5] 协议建议（b=0 修正开）：最小 N 使 sigma_d <= 0.1、判别余量 4/sigma_d >= 40")
    print(f"{'档':>6} | {'N*':>10} | {'sigma_d':>8} | {'余量(4/sigma)':>12}")
    for d in BANDS:
        found = None
        for N in Ns:
            _, sigs, _ = simulate_band(d, int(N), 0.0, True, ntrials=300, seed=23)
            s = np.nanmean(sigs)
            if s <= 0.1 and 4.0 / s >= 40:
                found = (int(N), s)
                break
        if found:
            print(f"d={d:<4} | {found[0]:>10,} | {found[1]:8.4f} | {4/found[1]:12.1f}")
        else:
            print(f"d={d:<4} | {'>1e6':>10} | {'—':>8} | {'—':>12}")

    # ---- 表 6：loss 真值对照 10.36 §3（b=0）----
    print("\n[表 6] loss_true 复现 10.36 §3 采样点 loss 值（括号内为 10.36 表值）")
    for d in BANDS:
        c_d, rho, theta, _ = load_band(d)
        lt = c_d * theta ** d * (1 + rho * theta ** 2)
        ref = {4: [2.0e-3, 1.0e-2, 3.2e-2, 7.7e-2, 1.6e-1],
               8: [4.9e-3, 1.7e-2, 4.9e-2, 1.3e-1, 2.9e-1],
               16: [1.5e-3, 6.4e-3, 1.6e-2, 8.4e-2, 2.6e-1],
               32: [1.2e-3, 4.7e-3, 1.8e-2, 6.1e-2, 2.0e-1]}[d]
        print(f"d={d:<3}: " + "  ".join(f"{theta[i]:.2f}->{lt[i]:.3g}({ref[i]:.2g})" for i in range(5)))

if __name__ == "__main__":
    run()
