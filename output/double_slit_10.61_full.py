# -*- coding: utf-8 -*-
"""双缝干涉完整图（文章10.61 定理3.04：sinc² 包络 × cos² 干涉项）
参数全部来自文章 10.61 §4：λ=632.8nm, d=0.5mm, D=1m, a=0.1mm(示意)
I(x) = I0 * sinc²(πax/λD) * cos²(πdx/λD)   (定理 10.61.3.04)
包络第一零点 x0 = λD/a = 6.328 mm = 5Δx；中央包络内 9 条亮纹 (推论 10.61.3.05)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'Arial Unicode MS', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False
rcParams['mathtext.fontset'] = 'dejavusans'

# ---- 文章数据（10.61 §4.1）----
lam = 632.8e-9      # m，He-Ne
d   = 0.5e-3        # m，缝间距
D   = 1.0           # m，屏距
a   = 0.1e-3        # m，缝宽（文章未锚定，示意值，推论 3.05 示例）
dx  = lam * D / d   # 条纹间距 = 1.2656e-3 m
x0  = lam * D / a   # 包络第一零点 = 6.328e-3 m

# ---- 强度公式（定理 10.61.3.04）----
x = np.linspace(-8.5 * dx, 8.5 * dx, 4000)
u = np.pi * a * x / (lam * D)          # 包络自变量
v = np.pi * d * x / (lam * D)          # 干涉自变量
sinc = np.where(np.abs(u) > 1e-12, np.sin(u) / u, 1.0)
I = sinc**2 * np.cos(v)**2             # I/I0 完整强度
env = sinc**2                          # 包络

# ---- 亮纹位置（推论 3.05：|k| < d/a = 5 ⟹ k = 0,±1,...,±4 共 9 条）----
ks = np.arange(-4, 5)
xk = ks * dx

fig = plt.figure(figsize=(10.5, 8.2), facecolor='white')
gs = fig.add_gridspec(2, 1, height_ratios=[1.25, 1.0], hspace=0.30)

# ---- 上图：强度曲线 ----
ax1 = fig.add_subplot(gs[0])
ax1.plot(x * 1e3, I, '-', color='#1f5fbf', lw=2.0, label=r'$I(x)/I_0 = \mathrm{sinc}^2(\pi a x/\lambda D)\cdot\cos^2(\pi d x/\lambda D)$')
ax1.plot(x * 1e3, env, '--', color='#c0563e', lw=1.4, alpha=0.9, label=r'包络 $\mathrm{sinc}^2(\pi a x/\lambda D)$')
ax1.axvline(x0 * 1e3, color='#c0563e', lw=1.0, ls=':', alpha=0.7)
ax1.axvline(-x0 * 1e3, color='#c0563e', lw=1.0, ls=':', alpha=0.7)
ax1.plot(xk * 1e3, np.full_like(xk, 0.02), 'v', color='#1f5fbf', ms=7, label=r'亮纹 $x_k = k\Delta x$（9 条）')
ax1.annotate(r'包络零点 $x_0 = \lambda D/a = 6.328$ mm $= 5\Delta x$',
             xy=(x0 * 1e3, 0.0), xytext=(3.2, 0.78),
             arrowprops=dict(arrowstyle='->', color='#c0563e', lw=1.0), color='#c0563e', fontsize=10)
ax1.annotate(r'条纹间距 $\Delta x = \lambda D/d = 1.2656$ mm',
             xy=(0.6, 0.62), xytext=(0.9, 0.88),
             arrowprops=dict(arrowstyle='->', color='#1f5fbf', lw=1.0), color='#1f5fbf', fontsize=10)
ax1.set_xlim(-8.5 * dx * 1e3, 8.5 * dx * 1e3)
ax1.set_ylim(-0.06, 1.12)
ax1.set_xlabel('屏上位置 x (mm)')
ax1.set_ylabel(r'$I(x)/I_0$')
ax1.set_title('双缝干涉完整强度（文章 10.61 定理 3.04）——中间亮、两旁渐暗', fontsize=13)
ax1.legend(loc='upper right', fontsize=9.5, framealpha=0.9)
ax1.grid(alpha=0.25, lw=0.4)

# ---- 下图：屏幕灰度图样（完整公式）----
ax2 = fig.add_subplot(gs[1])
# 模拟屏幕：y 方向展开条纹，x 方向为屏上位置
X, Y = np.meshgrid(x, np.linspace(0, 1, 160))
u2 = np.pi * a * X / (lam * D)
v2 = np.pi * d * X / (lam * D)
sinc2 = np.where(np.abs(u2) > 1e-12, np.sin(u2) / u2, 1.0)
I2 = sinc2**2 * np.cos(v2)**2
ax2.imshow(I2, extent=[x[0] * 1e3, x[-1] * 1e3, 0, 1], aspect='auto', cmap='gray_r', vmin=0, vmax=1)
ax2.axvline(x0 * 1e3, color='#c0563e', lw=1.0, ls=':', alpha=0.8)
ax2.axvline(-x0 * 1e3, color='#c0563e', lw=1.0, ls=':', alpha=0.8)
ax2.set_xlim(-8.5 * dx * 1e3, 8.5 * dx * 1e3)
ax2.set_yticks([])
ax2.set_xlabel('屏上位置 x (mm)')
ax2.set_title('屏幕图样：中央 9 条亮纹（|k| ≤ 4），包络零点外条纹消失', fontsize=11)

fig.text(0.01, 0.012,
         '数据：λ=632.8 nm, d=0.5 mm, D=1 m, a=0.1 mm（10.61 §4.1）；'
         'Δx=1.2656 mm；x0=6.328 mm=5Δx；等幅理想化（命题 2.02）→ 完整包络（定理 3.04）',
         fontsize=9, color='#555555')

fig.savefig('output/double_slit_10.61_full.png', dpi=160, bbox_inches='tight')
print('saved: output/double_slit_10.61_full.png')
print(f'dx  = {dx*1e3:.10f} mm  (文章精确值 1.2656)')
print(f'x0  = {x0*1e3:.10f} mm  (= 5*dx, 精确)')
print(f'x0/dx = {x0/dx:.10f}')
print(f'I(0)/I0   = {I[np.argmin(np.abs(x))]:.6f}')
print(f'I(x0)/I0  = {I[np.argmin(np.abs(x - x0))]:.6f}  (包络零点, 应为 0)')
