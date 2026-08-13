#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_speedup.py —— 几何无枚举验证 vs 暴力枚举：加速比曲线（含交叉点）

数据来源：
  - 实测：bench_geometric_vs_brute.py 的暴力全枚举（[[32,20,4]]、[[64,50,4]]、[[64,20,8]]）
    与几何证书验证（全部 7 码，本脚本现场复测以保证可复现）
  - 外推：[[128,70,8]] 及以上，按权重 7 层实测速率 2.18e6 flip/s 线性外推
    （同机同实现；n 增大时单 flip 成本只增不减，外推偏乐观）
输出：bench_speedup_curve.png
"""
import os
import sys
import math
from math import comb

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_geometric_vs_brute import build_cols, brute_layer, geometric_verify, rm_rows, RATE_NPZ

YEAR = 3.15576e7
AGE_UNIVERSE_S = 1.38e10 * YEAR  # 4.35e17 s

# 码族成员（与 10.30 文章表一致）：(r, m)
FAMILY = [(1, 5), (1, 6), (2, 6), (2, 7), (3, 8), (3, 9), (4, 10)]
# 实测的暴力点：枚举数 < 1e7 全实测；[[64,20,8]] 用 npz 存档的权重 1..7 全实测
MEASURED = {(1, 5), (1, 6), (2, 6)}


def main():
    # ---- 外推速率基准（权重 7 实测） ----
    with np.load(RATE_NPZ) as z:
        store = {int(kk): z[kk] for kk in z.files}
    w_max = max(store.keys())
    total_m, _, dt_m = store[w_max]
    rate = float(total_m) / float(dt_m)
    print(f"外推基准速率（w={w_max} 实测）= {rate:,.0f} flip/s")

    # ---- 逐码计算：枚举数 / 暴力耗时 / 几何实测 ----
    rows = []
    for (r, m) in FAMILY:
        n = 2 ** m
        rc = len(rm_rows(r, m))
        k = n - 2 * rc
        d = 2 ** (r + 1)
        enum = sum(comb(n, w) for w in range(1, d))
        # 几何证书：现场实测
        ok, cert, dt_geo = geometric_verify(r, m)
        assert ok, (r, m)
        # 暴力耗时
        if (r, m) == (2, 6):
            dt_brute = sum(float(store[w][2]) for w in range(1, d))  # 全实测 7.05e8
        elif (r, m) in MEASURED:
            cols, _ = build_cols(r, m)
            tt = 0.0
            for w in range(1, d):
                _, _, dtw = brute_layer(cols, n, w)
                tt += dtw
            dt_brute = tt
        else:
            dt_brute = enum / rate  # 外推
        speedup = dt_brute / dt_geo
        rows.append(dict(r=r, m=m, n=n, k=k, d=d, enum=enum,
                         dt_brute=dt_brute, dt_geo=dt_geo, speedup=speedup,
                         measured=(r, m) in MEASURED or (r, m) == (2, 6)))
        print(f"[[{n},{k},{d}]] enum={enum:.3e} brute={dt_brute:.3e}s "
              f"geo={dt_geo:.3f}s speedup={speedup:.3e} measured={rows[-1]['measured']}")

    enum_a = np.array([r['enum'] for r in rows], dtype=float)
    speed_a = np.array([r['speedup'] for r in rows], dtype=float)
    n_a = np.array([r['n'] for r in rows], dtype=float)
    brute_a = np.array([r['dt_brute'] for r in rows], dtype=float)
    geo_a = np.array([r['dt_geo'] for r in rows], dtype=float)
    meas = np.array([r['measured'] for r in rows])

    # ---- 图 ----
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(14, 6))
    ms, mf = 9, 'o'
    c_meas, c_ext = '#1f5fd6', '#9aa4b5'
    label_meas, label_ext = 'measured (full enumeration)', 'extrapolated (rate 2.18e6 flip/s)'

    # 左面板：加速比 vs 枚举数（log-log），交叉点
    for r, e, s, mm in zip(rows, enum_a, speed_a, meas):
        col = c_meas if mm else c_ext
        lab = label_meas if (mm and not any(x[0] == 'm' for x in axL.get_legend_handles_labels()[1])) else None
        axL.plot(e, s, mf, color=col, ms=ms, markerfacecolor=col if mm else 'none',
                 label=(label_meas if mm else label_ext) if lab is None and False else None)
    # 手动图例
    axL.plot([], [], 'o', color=c_meas, ms=ms, label=label_meas)
    axL.plot([], [], 'o', color=c_ext, ms=ms, markerfacecolor='none', label=label_ext)
    axL.set_xscale('log'); axL.set_yscale('log')
    axL.axhline(1.0, color='#d62728', ls='--', lw=1.2)
    axL.text(2e3, 1.4, 'speedup = 1  (cross-over)', color='#d62728', fontsize=9)
    # 线性拟合（log10 域）
    coef = np.polyfit(np.log10(enum_a), np.log10(speed_a), 1)
    xf = np.logspace(3, 61, 200)
    axL.plot(xf, 10 ** np.polyval(coef, np.log10(xf)), '-', color='#7f7f7f', lw=0.9,
             label=f'fit slope = {coef[0]:.3f}')
    x_cross = 10 ** (-coef[1] / coef[0])
    axL.plot(x_cross, 1.0, '*', color='#d62728', ms=14)
    # 数据点标注
    for r in rows:
        dy = 0.25 if r['speedup'] > 1 else -0.25
        axL.annotate(f"[[{r['n']},{r['k']},{r['d']}]]",
                     (r['enum'], r['speedup']), textcoords='offset points',
                     xytext=(6, 12 if r['speedup'] > 1 else -14), fontsize=8, color='#333')
    axL.set_xlabel('error space enumerated  $\\Sigma_{w<d} C(n,w)$')
    axL.set_ylabel('speedup  =  brute-force time / geometric time')
    axL.set_title('Speedup vs error-space size\n(cross-over at ~4e4 errors: d=4 still fast, d=8 already 10^4x)')
    axL.legend(loc='upper left', fontsize=8)
    axL.grid(True, which='both', alpha=0.25)

    # 右面板：暴力耗时 vs n（log-log），宇宙年龄参照
    for r, nn, bb, mm in zip(rows, n_a, brute_a, meas):
        col = c_meas if mm else c_ext
        axR.plot(nn, bb, mf, color=col, ms=ms, markerfacecolor=col if mm else 'none')
    axR.plot([], [], 'o', color=c_meas, ms=ms, label=label_meas)
    axR.plot([], [], 'o', color=c_ext, ms=ms, markerfacecolor='none', label=label_ext)
    axR.set_xscale('log'); axR.set_yscale('log')
    axR.axhline(AGE_UNIVERSE_S, color='#d62728', ls='--', lw=1.2)
    axR.text(40, AGE_UNIVERSE_S * 1.7, 'age of universe (1.38e10 yr)', color='#d62728', fontsize=9)
    for r in rows:
        if r['dt_brute'] > AGE_UNIVERSE_S:
            axR.annotate(f"[[{r['n']},{r['k']},{r['d']}]]", (r['n'], r['dt_brute']),
                         textcoords='offset points', xytext=(6, -14), fontsize=8, color='#333')
        elif r['n'] >= 64:
            axR.annotate(f"[[{r['n']},{r['k']},{r['d']}]]", (r['n'], r['dt_brute']),
                         textcoords='offset points', xytext=(6, 8), fontsize=8, color='#333')
    # 几何耗时：贴地曲线
    axR.plot(n_a, geo_a, 's-', color='#2ca02c', ms=5, lw=1, label='geometric certificate (measured)')
    axR.set_xlabel('code length  n')
    axR.set_ylabel('wall time (s)  [brute-force: measured + extrapolated]')
    axR.set_title('Brute-force enumeration time vs code length\n(geometric verification stays below 1 s)')
    axR.legend(loc='upper left', fontsize=8)
    axR.grid(True, which='both', alpha=0.25)

    fig.suptitle('Geometric no-enumeration verification vs brute-force enumeration  (CSS(RM(r,m)) affine-complete codes)',
                 fontsize=12, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bench_speedup_curve.png')
    fig.savefig(out, dpi=200)
    print(f"saved: {out}")
    print(f"fit: log10(speedup) = {coef[0]:.4f} * log10(enum) + {coef[1]:.4f}")
    print(f"cross-over at enum = {x_cross:.2e}  (=> d~4-5 at n=64)")


if __name__ == '__main__':
    main()
