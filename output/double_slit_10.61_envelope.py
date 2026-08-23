# 双缝干涉对比图：文章10.61理想化 vs 真实实验（含单缝包络）
# 参数（来自文章10.61 §4.1）：λ=632.8nm, d=0.5mm, D=1m
# 缝宽 a 文章未锚定（O1），此处取 a=0.1mm 作示意
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['mathtext.fontset'] = 'dejavusans'

lam = 632.8e-9   # m
d = 0.5e-3       # m 缝间距（中心到中心）
D = 1.0          # m
a = 0.1e-3       # m 缝宽（示意值，O1 未锚定）
dx = lam * D / d # 条纹间距 = 1.2656e-3 m

x = np.linspace(-8*dx, 8*dx, 4000)
u = np.pi * a * x / (lam * D)

I_ideal = np.cos(np.pi * d * x / (lam * D))**2            # 文章定理3.01
I_real  = (np.sin(u)/np.where(u==0, 1, u))**2 * I_ideal   # cos² × sinc²包络
I_real  = np.where(u==0, 1.0, I_real)

fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True,
                         gridspec_kw={'height_ratios': [1, 1]})
fig.subplots_adjust(hspace=0.05)

colors = ['#1f5fbf', '#b03030']
titles = [r'文章 10.61 理想化：$I(x)=I_0\cos^2(\pi d x/\lambda D)$（定理 3.01，等亮条纹）',
          r'真实实验：$I(x)=I_0\,\mathrm{sinc}^2(\pi a x/\lambda D)\cdot\cos^2(\pi d x/\lambda D)$（含单缝包络，中央亮、两旁暗）']

for ax, I, c, t in zip(axes, [I_ideal, I_real], colors, titles):
    ax.plot(x*1e3, I, color=c, lw=1.8)
    ax.fill_between(x*1e3, I, alpha=0.15, color=c)
    ax.set_ylabel(r'$I(x)/I_0$')
    ax.set_title(t, fontsize=11)
    ax.grid(alpha=0.3, lw=0.4)
    ax.set_xlim(-8*dx*1e3, 8*dx*1e3)
    ax.set_ylim(-0.08, 1.15)
    ax.axvline(0, color='gray', lw=0.8, ls='--')

# 标注
axes[0].annotate(r'$\Delta x = 1.2656$ mm', xy=(1.2656, 0.95), xytext=(2.6, 0.85),
                 arrowprops=dict(arrowstyle='->', color='gray'), fontsize=9)
axes[0].text(0.4, 0.42, '每条亮纹等亮', fontsize=9, color='#1f5fbf')
axes[1].annotate(r'sinc² 包络第一零点：$x=\lambda D/a = 6.33$ mm $\approx 5\Delta x$',
                 xy=(6.328, 0.05), xytext=(2.6, 0.60),
                 arrowprops=dict(arrowstyle='->', color='#b03030'), fontsize=9, color='#b03030')
axes[1].text(0.4, 0.42, '中央最亮，两旁渐暗', fontsize=9, color='#b03030')

axes[1].set_xlabel(r'屏上位置 $x$ (mm)')
fig.suptitle(r'双缝干涉：等幅理想化 vs 真实包络（$\lambda=632.8$ nm, $d=0.5$ mm, $D=1$ m）'
             '\n缝宽 a=0.1 mm 为示意值——文章 O1 未锚定', fontsize=12)
fig.savefig('output/double_slit_10.61_envelope.png', dpi=150, bbox_inches='tight')
print(f'dx = {dx*1e3:.7f} mm')
print(f'sinc² 第一零点 x = {lam*D/a*1e3:.4f} mm = {(lam*D/a)/dx:.2f} Δx')
