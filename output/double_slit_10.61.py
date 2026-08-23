#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按文章 10.61 的数据绘制双缝干涉图：
   λ = 632.8 nm, d = 0.5 mm, D = 1 m, Δx = λD/d = 1.2656 mm
   I(x) = I₀ cos²(π d x / (λ D))   （等幅理想化，无单缝包络，文章 §5 O1）
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- 文章 10.61 §4.1 的锚定数据 ----
lam = 632.8e-9      # m  (He-Ne)
d   = 0.5e-3        # m  缝间距
D   = 1.0           # m  屏距
dx  = lam * D / d   # 条纹间距
print(f"Δx = {dx*1e3:.10f} mm  (文章值 1.2656 mm, 精确 791/625 mm)")

I0 = 1.0
x  = np.linspace(-5.0*dx, 5.0*dx, 4000)
I  = I0 * np.cos(np.pi * d * x / (lam * D))**2

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS", "STHeiti"]
plt.rcParams["axes.unicode_minus"] = False

fig = plt.figure(figsize=(10.5, 7.2))
gs  = fig.add_gridspec(2, 1, height_ratios=[1.25, 1.0], hspace=0.42)

# ---------- 上图：强度分布曲线 ----------
ax1 = fig.add_subplot(gs[0])
ax1.plot(x*1e3, I, color="#1a4fc4", lw=2.2, label=r"$I(x)/I_0=\cos^2(\pi d x/\lambda D)$")
ax1.fill_between(x*1e3, I, color="#1a4fc4", alpha=0.10)

# 峰谷标注
for k in range(-4, 5):
    xk = k*dx
    ax1.plot([xk*1e3], [1.0], marker="o", ms=5, color="#c41a1a", zorder=5)
    if k != 0:
        ax1.annotate(f"$x_{{{k}}}$", (xk*1e3, 1.02), ha="center", fontsize=9, color="#c41a1a")
for k in range(-4, 4):
    xv = (k + 0.5)*dx
    ax1.plot([xv*1e3], [0.0], marker="s", ms=4, color="#555555", zorder=5)
    if k in (-1, 0, 1):
        ax1.annotate(f"谷 $x_{{{k}+1/2}}$", (xv*1e3, -0.085), ha="center", fontsize=8, color="#555555")

# Δx 标注（峰 k=0 到峰 k=1）
ax1.annotate("", xy=(dx*1e3, 1.10), xytext=(0, 1.10),
             arrowprops=dict(arrowstyle="<->", color="#1a4fc4", lw=1.4))
ax1.text(dx*1e3/2, 1.15, r"$\Delta x = \lambda D/d = 1.2656\ \mathrm{mm}$",
         ha="center", fontsize=11, color="#1a4fc4")

ax1.set_xlim(-5.0*dx*1e3, 5.0*dx*1e3)
ax1.set_ylim(-0.22, 1.30)
ax1.set_xlabel("屏上位置  x  (mm)", fontsize=12)
ax1.set_ylabel(r"$I(x)/I_0$", fontsize=12)
ax1.set_title("文章 10.61 定理 3.01：双缝干涉强度  I(x) = I₀cos²(πdx/λD)\n"
              "λ = 632.8 nm (He-Ne) · d = 0.5 mm · D = 1 m · Δx = 1.2656 mm",
              fontsize=12.5, pad=12)
ax1.legend(loc="upper right", fontsize=10.5, frameon=False)
ax1.grid(alpha=0.25, ls=":")

# ---------- 下图：屏幕图样（灰度模拟） ----------
ax2 = fig.add_subplot(gs[1])
ys = np.linspace(-1, 1, 600)
Xs, Ys = np.meshgrid(x, ys)
Pat = np.cos(np.pi * d * Xs / (lam * D))**2
ax2.imshow(Pat, extent=[x[0]*1e3, x[-1]*1e3, -1, 1], cmap="gray",
           aspect="auto", vmin=0, vmax=1, interpolation="bilinear")
ax2.set_xlim(-5.0*dx*1e3, 5.0*dx*1e3)
ax2.set_yticks([])
ax2.set_ylabel("屏面", fontsize=11)
ax2.set_xlabel("屏上位置  x  (mm)", fontsize=12)
ax2.set_title("屏幕图样（灰度 = 强度；亮纹中心 $x_k$ = k × 1.2656 mm，暗纹 x = (k+½) × 1.2656 mm）",
              fontsize=11.5, pad=10)

# 底部数据条
fig.text(0.5, 0.012,
         "等幅理想化（文章命题 10.61.2.02，σ₁=σ₂=1/2，对比度 V=1）；单缝衍射包络 sinc² 未含（文章 §5 开放问题 O1）",
         ha="center", fontsize=9.5, color="#444444")

out = "/Users/oygb/Downloads/GeometryAI-Mac-Build/output/double_slit_10.61.png"
fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
print("saved:", out)
