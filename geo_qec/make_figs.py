# -*- coding: utf-8 -*-
"""三张演示图：比特数跃迁 / θ⁴ 标度律 / 错误注入显微镜（mathtext 版）"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np, os, random
from p4_demo_1023 import make_code, single_bit_syndromes, col_value

for f in ['/System/Library/Fonts/Hiragino Sans GB.ttc', '/System/Library/Fonts/PingFang.ttc',
          '/System/Library/Fonts/STHeiti Medium.ttc']:
    if os.path.exists(f):
        fm.fontManager.addfont(f)
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'PingFang HK', 'STHeiti', 'Songti SC']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'dejavusans'
plt.rcParams['axes.formatter.use_mathtext'] = True
os.makedirs('figs', exist_ok=True)

# ============ 图 1：比特数跃迁 ============
ms = list(range(3, 11))
ns = [2**m - 1 for m in ms]
sv_mem = [16 * 2.0**n for n in ns]
sym_mem = [2*m*n/8/1024 for m, n in zip(ms, ns)]
t_total = [1.8e-5, 4.2e-5, 1.3e-4, 4.7e-4, 1.7e-3, 8.3e-3, 2.9e-2, 1.2e-1]
ATOMS = 1e80

fig, ax1 = plt.subplots(figsize=(11, 6.5))
ax1.set_xscale('log'); ax1.set_yscale('log')
ax1.plot(ns, sv_mem, 'o-', color='#c0392b', lw=2.5, ms=7, label='态矢量内存 $2^n\\times16$ B')
ax1.axhline(ATOMS, color='#7f8c8d', ls='--', lw=1.2)
ax1.text(16, ATOMS*1.8, '可观测宇宙原子总数 $\\approx 10^{80}$', fontsize=10, color='#7f8c8d')
ax1.set_ylabel('态矢量内存（字节，对数）', color='#c0392b', fontsize=13)
ax1.tick_params(axis='y', labelcolor='#c0392b')
ax1.set_xlabel('物理比特数 n（方向完备码 $2^m-1$）', fontsize=13)

ax2 = ax1.twinx()
ax2.set_yscale('log')
ax2.plot(ns, sym_mem, 's-', color='#2980b9', lw=2.5, ms=7, label='符号内存（KB）')
ax2.plot(ns, t_total, '^-', color='#27ae60', lw=2.5, ms=8, label='全量验证时间（秒）')
ax2.set_ylabel('符号内存（KB）/ 验证时间（秒，对数）', fontsize=13)
ax2.tick_params(axis='y', labelcolor='#2980b9')
ax2.set_ylim(1e-5, 1e3)

ax1.annotate('n=1023：态矢量 $1.7\\times10^{309}$ B\n= 宇宙原子数的 $10^{228}$ 倍',
             xy=(1023, sv_mem[-1]), xytext=(120, 1e250), fontsize=11, color='#c0392b',
             arrowprops=dict(arrowstyle='->', color='#c0392b'))
ax1.annotate('符号 2.5 KB，全量验证 0.12 s', xy=(1023, 2.5), xytext=(90, 0.003),
             fontsize=11, color='#2980b9', arrowprops=dict(arrowstyle='->', color='#2980b9'))
ax1.annotate('n=28 处态矢量内存达 4.3 GB（机器极限）', xy=(28, 16*2.0**28),
             xytext=(40, 1e12), fontsize=10, color='#7f8c8d',
             arrowprops=dict(arrowstyle='->', color='#7f8c8d'))
ax1.set_title('比特数跃迁：指数维度的死亡 vs 几何结构的平坦\n'
              '（方向完备码 $[[2^m-1,\\,2^m-1-2m,\\,3]]$，全量验证时间含单比特与权重 2 全部错误）',
              fontsize=13.5)
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1+h2, l1+l2, loc='upper left', fontsize=11, framealpha=0.9)
plt.tight_layout(); plt.savefig('figs/fig1_bit_transition.png', dpi=150)
plt.close()
print('fig1 OK')

# ============ 图 2：θ⁴ 标度律 ============
thetas = np.array([0.05, 0.1, 0.2, 0.4])
data = {'$[[5,1,3]]$': ([3.2e-07, 5.3e-06, 8.5e-05, 1.4e-03], 4.04, '#e67e22'),
        '$[[7,1,3]]$': ([4.0e-07, 8.7e-06, 9.9e-05, 2.4e-03], 4.12, '#8e44ad'),
        '$[[9,1,3]]$': ([1.6e-07, 1.9e-06, 3.9e-05, 8.4e-04], 4.14, '#16a085')}
fig, ax = plt.subplots(figsize=(10, 6.5))
for lab, (loss, slope, col) in data.items():
    ax.loglog(thetas, loss, 'o-', color=col, lw=2, ms=8, label=f'{lab}：斜率 {slope:.2f}')
th = np.logspace(-2.3, -0.3, 50)
ax.loglog(th, 1.5*th**4, 'k--', lw=1.5, label='参考线 $\\theta^4$（斜率 4）')
kappa = 151.7
ax.axvline(1/kappa, color='#c0392b', ls=':', lw=1.5)
ax.text(1/kappa*1.02, 3e-13, 'H1 截断 $\\theta_{max}=1/\\kappa \\approx 0.0066$\n外推损失 $\\approx 10^{-10}$\n（比界 $A\\kappa^{-1}$ 保守 7 个数量级）',
        fontsize=10, color='#c0392b', va='bottom')
ax.set_xlabel('单比特噪声上界 $\\theta_{max}$（弧度）', fontsize=13)
ax.set_ylabel('最优纠错后损失 $L = 1 - F$', fontsize=13)
ax.set_title('几何论预言：独立噪声下纠错后损失 $\\sim \\theta^4$\n'
             '（不可恢复成分权重 $\\geq 3$，恢复干涉主导——7 比特芯片即可检验）', fontsize=14)
ax.legend(fontsize=11, loc='lower right')
ax.grid(True, which='both', alpha=0.3)
plt.tight_layout(); plt.savefig('figs/fig2_theta4_powerlaw.png', dpi=150)
plt.close()
print('fig2 OK')

# ============ 图 3：错误注入显微镜（1023 码） ============
m, n = 10, 1023
H, gens, _, _ = make_code(m)
SX, SZ = single_bit_syndromes(H, n, m)
cols = [col_value(H, j, m) for j in range(n)]

def syn_x(xm):
    s = 0
    for r in range(m):
        bz = bin(xm & H[r]).count('1') & 1
        s = (s << 1) | bz
        s = (s << 1) | 0
    return s

def bars(s, L=20):
    return [(s >> (L-1-k)) & 1 for k in range(L)]

random.seed(260807)
a = random.randrange(n)
sa = syn_x(1 << a)
b1, b2 = 706, 1
c_ = cols[b1] ^ cols[b2]
jc = cols.index(c_)
s2 = syn_x((1 << b1) | (1 << b2))
s_c = syn_x(1 << jc)
assert s2 == s_c

fig, axes = plt.subplots(2, 2, figsize=(13, 7), gridspec_kw={'height_ratios': [1.6, 1]})
for ax in axes[0]:
    ax.set_xlim(0, 1023); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.set_xlabel('1023 个物理比特', fontsize=10)
    ax.tick_params(axis='x', labelsize=7)
ax0 = axes[0][0]
ax0.scatter(range(n), [0.5]*n, s=2, c='#bdc3c7', marker='s')
ax0.scatter([a], [0.5], s=60, c='#c0392b', marker='s', zorder=5)
ax0.text(a+8, 0.62, f'$X_a$（a={a+1}）', fontsize=10, color='#c0392b')
ax0.set_title('(a) 注入单比特错误 $X_a$', fontsize=12)
ax1 = axes[0][1]
ax1.scatter(range(n), [0.5]*n, s=2, c='#bdc3c7', marker='s')
ax1.scatter([b1, b2], [0.5, 0.5], s=60, c='#e67e22', marker='s', zorder=5)
ax1.scatter([jc], [0.5], s=60, c='#8e44ad', marker='s', zorder=5)
ax1.text(b1+8, 0.62, f'$X_{{b1}}$（{b1+1}）', fontsize=9, color='#e67e22')
ax1.text(b2+8, 0.62, f'$X_{{b2}}$（{b2+1}）', fontsize=9, color='#e67e22')
ax1.text(jc+8, 0.62, f'恢复 $X_c$（{jc+1}）', fontsize=9, color='#8e44ad')
ax1.set_title('(b) 注入共线权重 2 错误 $X_{706}X_1$（列 706$\\oplus$1 = 707）', fontsize=12)
for ax in axes[1]:
    ax.set_xlim(0, 20); ax.set_ylim(0, 1); ax.set_yticks([])
    ax.set_xlabel('syndrome（20 位：10 个 Z 型 + 10 个 X 型生成元）', fontsize=10)
ax0b = axes[1][0]
for k, b in enumerate(bars(sa)):
    ax0b.add_patch(plt.Rectangle((k, 0), 0.8, 1, color='#c0392b' if b else '#ecf0f1', ec='#95a5a6'))
ax0b.set_title('(c) syndrome $\\ne 0$ → 查表恢复 $X_a$ → $R\\cdot E = I$：完美恢复', fontsize=11)
ax1b = axes[1][1]
for k, b in enumerate(bars(s2)):
    ax1b.add_patch(plt.Rectangle((k, 0), 0.8, 1, color='#c0392b' if b else '#ecf0f1', ec='#95a5a6'))
ax1b.set_title('(d) syndrome = syndrome($X_c$) → 恢复 $X_c$ → 残留 $X_{706}X_1X_{707}$\n'
               '（权重 3 逻辑算符：与全部 20 生成元对易且非稳定子——d=3 纠正边界）', fontsize=10)
plt.tight_layout(); plt.savefig('figs/fig3_error_microscope.png', dpi=150)
plt.close()
print('fig3 OK')
print('生成完毕：figs/fig1_bit_transition.png, figs/fig2_theta4_powerlaw.png, figs/fig3_error_microscope.png')
