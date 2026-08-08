"""Generate the three figures for the PRA submission (QEC_Paper_Exact_Scaling_Geometric_CSS_RM_EN)."""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 10, 'axes.labelsize': 11,
                     'legend.fontsize': 9, 'xtick.labelsize': 9,
                     'ytick.labelsize': 9})

OUT = os.path.join('app', 'articles', 'figures')
os.makedirs(OUT, exist_ok=True)

# ---------------- data (closed forms, Sec. 8.1 of the paper) ----------------
C = {4: 1.23e4, 8: 2.94e7, 16: 1.05e8, 32: 7.53e7}
COL = {4: '#d62728', 8: '#1f77b4', 16: '#2ca02c', 32: '#9467bd'}
CODES = {4: '[[1024,1002,4]]', 8: '[[1024,912,8]]', 16: '[[1024,672,16]]', 32: '[[1024,252,32]]'}
# observable windows: 1e-3 <= c_d theta^d <= 0.5 (Theorem 26)
W = {d: ((1e-3 / C[d]) ** (1.0 / d), (0.5 / C[d]) ** (1.0 / d)) for d in (4, 8, 16, 32)}
print('windows (exact):', {d: (round(W[d][0], 4), round(W[d][1], 4)) for d in W})
GAPS = [(W[8][1], W[16][0]), (W[16][1], W[32][0])]
OVERLAP = (W[8][0], W[4][1])
print('gaps:', GAPS, 'overlap:', OVERLAP)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + '.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(OUT, name + '.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)


# ---------------- Figure 1: family parameters at fixed n = 1024 ----------------
rs = np.arange(5)
k_vals = np.array([1022, 1002, 912, 672, 252])   # k = 2^10 - 2 dim RM(r,10)
d_vals = 2.0 ** (rs + 1)

fig, ax1 = plt.subplots(figsize=(6.6, 4.0))
ax1.plot(rs[1:], k_vals[1:], 'o-', color='#1f77b4', lw=1.8, ms=7,
         label='logical dimension $k$ (left axis)')
ax1.plot([0], [1022], 'o', color='#1f77b4', ms=7, fillstyle='none')
ax1.set_xlabel('$r$')
ax1.set_ylabel('logical dimension $k$', color='#1f77b4')
ax1.tick_params(axis='y', labelcolor='#1f77b4')
ax1.set_xticks(rs)
ax1.set_ylim(0, 1150)

ax2 = ax1.twinx()
ax2.plot(rs[1:], d_vals[1:], 's--', color='#d62728', lw=1.8, ms=7,
         label='distance $d = 2^{r+1}$ (right axis)')
ax2.plot([0], [2], 's', color='#d62728', ms=7, fillstyle='none')
ax2.set_yscale('log')
ax2.set_ylabel('distance $d$', color='#d62728')
ax2.tick_params(axis='y', labelcolor='#d62728')
ax2.set_ylim(1, 80)

for r, k, d in zip(rs, k_vals, d_vals):
    ax1.annotate(f'$[[1024,{k},{int(d)}]]$', (r, k), xytext=(8, 4),
                 textcoords='offset points', fontsize=8.5)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', frameon=False)
ax1.grid(alpha=0.3, which='both')
save(fig, 'fig1_family_params')

# ---------------- Figure 2: parameter-free scaling predictions ----------------
theta = np.logspace(np.log10(0.008), np.log10(0.7), 400)
fig, ax = plt.subplots(figsize=(6.6, 4.6))
for d in (4, 8, 16, 32):
    c = C[d]
    w0, w1 = W[d]
    loss = c * theta ** d
    m_out = (theta < w0) | (theta > w1)
    ax.plot(theta[m_out], loss[m_out], '--', color=COL[d], lw=1.1, alpha=0.45)
    m_in = (theta >= w0) & (theta <= w1)
    ax.plot(theta[m_in], loss[m_in], '-', color=COL[d], lw=2.6)
    ax.text(w1 * 1.06, 0.5 * 1.25, f'$\\theta^{{{d}}}$', color=COL[d], fontsize=12, va='bottom')

for g in GAPS:
    ax.axvspan(*g, color='gray', alpha=0.18, zorder=0)
ax.axhline(1e-3, color='gray', ls=':', lw=1.0)
ax.axhline(0.5, color='gray', ls=':', lw=1.0)
ax.text(0.60, 1.5e-3, '$10^{-3}$', fontsize=9, color='gray', ha='right')
ax.text(0.60, 0.60, '$0.5$', fontsize=9, color='gray', ha='right')

ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlabel('rotation bound $\\theta_{\\max}$')
ax.set_ylabel('logical-$Z$-flip loss $\\mathrm{loss}(\\theta_{\\max})$')
ax.set_xlim(0.008, 0.7); ax.set_ylim(1e-3, 10)
ax.grid(alpha=0.3, which='both')

handles = [plt.Line2D([], [], color=COL[d], lw=2.6, label=f'$d={d}$  ' + CODES[d])
           for d in (4, 8, 16, 32)]
ax.legend(handles=handles, loc='upper left', frameon=False)
save(fig, 'fig2_scaling_law')

# ---------------- Figure 3: observable windows on the theta axis ----------------
fig, ax = plt.subplots(figsize=(6.6, 3.4))
ypos = {4: 4, 8: 3, 16: 2, 32: 1}
for d in (4, 8, 16, 32):
    w0, w1 = W[d]
    ax.barh(ypos[d], w1 - w0, left=w0, height=0.62, color=COL[d], alpha=0.85,
            edgecolor='k', lw=0.6)
    ax.text((w0 + w1) / 2, ypos[d] + 0.42, CODES[d], ha='center', fontsize=8.5)

for g in GAPS:
    ax.axvspan(*g, color='gray', alpha=0.35, zorder=0)
ax.text((GAPS[0][0] + GAPS[0][1]) / 2, 4.62, 'gap', ha='center', fontsize=9,
        color='0.25', style='italic')
ax.text((GAPS[1][0] + GAPS[1][1]) / 2, 4.62, 'gap', ha='center', fontsize=9,
        color='0.25', style='italic')
ax.axvspan(*OVERLAP, color='gold', alpha=0.35, zorder=0)
ax.text((OVERLAP[0] + OVERLAP[1]) / 2, 4.62, 'overlap', ha='center', fontsize=9,
        color='0.25', style='italic')

ax.set_yticks([1, 2, 3, 4])
ax.set_yticklabels(['$d{=}32$', '$d{=}16$', '$d{=}8$', '$d{=}4$'])
ax.set_xlabel('rotation bound $\\theta_{\\max}$')
ax.set_xlim(0, 0.62)
ax.set_ylim(0.3, 5.0)
ax.grid(axis='x', alpha=0.3)
save(fig, 'fig3_windows')

print('done:', sorted(os.listdir(OUT)))
