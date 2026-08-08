"""make_power_figs.py —— 任务 5 出图：fig4（sigma_d vs N）、fig5（次主阶污染）"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from power_analysis import simulate_band, BANDS

Ns = [5e4, 1e5, 2e5, 5e5, 1e6]

plt.figure(figsize=(8, 5))
for d in BANDS:
    sigs = [np.nanmean(simulate_band(d, int(N), 0.0, True, 300, 7)[1]) for N in Ns]
    plt.plot(Ns, sigs, 'o-', label=f'd={d}')
plt.axhline(0.1, ls='--', color='gray', lw=1)
plt.text(6.5e4, 0.105, r'$\sigma_{\hat d}=0.1$ 目标', color='gray', fontsize=9)
plt.xscale('log'); plt.yscale('log')
plt.xlabel('N (shots per point)'); plt.ylabel(r'$\sigma_{\hat d}$')
plt.title('Discrimination precision vs shots (m=10, subleading corrected, b=0)')
plt.legend(); plt.grid(alpha=0.3)
plt.tight_layout(); plt.savefig('figs/fig4_sigma_N.png', dpi=150)
print('fig4 saved')

dh0, _, _ = simulate_band(4, int(2e5), 0.0, False, 4000, 13)
dh1, _, _ = simulate_band(4, int(2e5), 0.0, True, 4000, 13)
plt.figure(figsize=(8, 5))
plt.hist(dh0, bins=50, alpha=0.55, label=f'无次主阶修正 (mean={np.mean(dh0):.3f})')
plt.hist(dh1, bins=50, alpha=0.55, label=f'闭式 $\\rho$ 修正 (mean={np.mean(dh1):.3f})')
plt.axvline(4, color='k', ls='--', lw=1.5, label='d=4')
plt.xlabel(r'$\hat d$（d=4 档，N=2e5）'); plt.ylabel('频数（4000 次模拟）')
plt.title('Subleading pollution: uncorrected $\\hat d$ biased +0.31 (15$\\sigma$)')
plt.legend(); plt.tight_layout(); plt.savefig('figs/fig5_subleading_bias.png', dpi=150)
print('fig5 saved')
