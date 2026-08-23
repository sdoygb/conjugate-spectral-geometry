#!/usr/bin/env python3
"""
探针㉔：补缺传播序列——"次圆满者从中国到西方"的谱论形式化
================================================================
基于探针㉓ 的 6 节点贸易耦合图（CN TW JP IN US EU，边权=2025 贸易额/785.8）：
- S4 当前组合（中美脱钩 CN-US×0.3 + 美台强化 US-TW×1.5 + 欧印强化 EU-IN×2）
- P1 东方补缺（S4 基础上恢复东方连接：CN-TW×1.3、CN-JP×1.2、CN-IN×1.3）
- P2 西方桥恢复（P1 基础上：CN-US×0.8、CN-EU×1.2）
- P3 完全回到 S0（脱钩前现状）

检验：
1) λ₂ 与二部配对残差的轨迹（补缺是否恢复结构稳健）
2) 东/西补缺的增量贡献（东主西次？）
3) 台湾节点耦合份额变化（归属反转）
4) 传播时间窗口（2-3 个弛豫周期 τ=1/(λ_b+λ_r)）
"""
import numpy as np
import json

base = 785.8
W0 = np.zeros((6, 6))
edges = {
    (0, 5): 785.8,   # CN-EU
    (0, 4): 574.66,  # CN-US
    (0, 2): 300.0,   # CN-JP
    (0, 1): 250.0,   # CN-TW
    (0, 3): 130.0,   # CN-IN
    (4, 1): 150.0,   # US-TW
    (4, 3): 239.4,   # US-IN
    (4, 2): 250.0,   # US-JP
    (5, 3): 136.0,   # EU-IN
    (5, 1): 60.0,    # EU-TW
    (2, 1): 80.0,    # JP-TW
    (2, 3): 25.0,    # JP-IN
    (1, 3): 15.0,    # TW-IN
}
for (i, j), v in edges.items():
    W0[i, j] = W0[j, i] = v / base

names = ['CN', 'TW', 'JP', 'IN', 'US', 'EU']


def laplacian_lambda2(Wm):
    L = np.diag(Wm.sum(axis=1)) - Wm
    ev = np.sort(np.linalg.eigvalsh(L))
    return float(ev[1])


def bipartite_residual(Wm):
    ev = np.sort(np.linalg.eigvalsh(Wm))
    n = len(ev)
    res = 0.0
    for i in range(n // 2):
        res += abs(ev[i] + ev[n - 1 - i])
    return float(res / (n // 2))


def tw_share(Wm):
    cn_tw, us_tw, eu_tw, jp_tw = Wm[0, 1], Wm[4, 1], Wm[5, 1], Wm[2, 1]
    total = cn_tw + us_tw + eu_tw + jp_tw
    return {'CN': cn_tw / total, 'US': us_tw / total, 'EU': eu_tw / total, 'JP': jp_tw / total}


# ---- 状态构造 ----
S4 = W0.copy()
S4[0, 4] = S4[4, 0] = 574.66 * 0.3 / base
S4[4, 1] = S4[1, 4] = 150.0 * 1.5 / base
S4[5, 3] = S4[3, 5] = 136.0 * 2.0 / base

P1 = S4.copy()
P1[0, 1] = P1[1, 0] = 250.0 * 1.3 / base   # CN-TW×1.3
P1[0, 2] = P1[2, 0] = 300.0 * 1.2 / base   # CN-JP×1.2
P1[0, 3] = P1[3, 0] = 130.0 * 1.3 / base   # CN-IN×1.3

P2 = P1.copy()
P2[0, 4] = P2[4, 0] = 574.66 * 0.8 / base  # CN-US×0.8（恢复 80%）
P2[0, 5] = P2[5, 0] = 785.8 * 1.2 / base   # CN-EU×1.2

P3 = W0.copy()  # 回到脱钩前

states = {'S4_当前组合': S4, 'P1_东方补缺': P1, 'P2_西方桥恢复': P2, 'P3_回S0': P3}

print('=== 探针㉔: 补缺传播序列 ===')
print(f"{'状态':16s} {'λ₂':>8s} {'二部残差':>8s}  TW份额 CN/US/EU/JP")
results = {}
for tag, Wm in states.items():
    l2 = laplacian_lambda2(Wm)
    br = bipartite_residual(Wm)
    sh = tw_share(Wm)
    results[tag] = {'lambda2': l2, 'bipartite': br, 'tw_share': sh}
    print(f"{tag:16s} {l2:8.4f} {br:8.4f}  {sh['CN']*100:4.1f}%/{sh['US']*100:4.1f}%/{sh['EU']*100:4.1f}%/{sh['JP']*100:4.1f}%")

d1 = results['P1_东方补缺']['lambda2'] - results['S4_当前组合']['lambda2']
d2 = results['P2_西方桥恢复']['lambda2'] - results['P1_东方补缺']['lambda2']
print(f"\nΔ₁ 东方补缺 = {d1:.4f}  ({d1/(d1+d2)*100:.1f}%)")
print(f"Δ₂ 西方桥   = {d2:.4f}  ({d2/(d1+d2)*100:.1f}%)")
print(f"比值 Δ₁/Δ₂  = {d1/d2:.2f}")
print(f"P2 完成态 vs S0 现状: {results['P2_西方桥恢复']['lambda2']:.4f} vs {laplacian_lambda2(W0):.4f}  ({(results['P2_西方桥恢复']['lambda2']-laplacian_lambda2(W0))/laplacian_lambda2(W0)*100:+.1f}%)")
print(f"P2 完成态 vs S4 当前: {(results['P2_西方桥恢复']['lambda2']-results['S4_当前组合']['lambda2'])/results['S4_当前组合']['lambda2']*100:+.1f}%")
print(f"P3 回S0    vs P2 完成态: {laplacian_lambda2(W0):.4f} vs {results['P2_西方桥恢复']['lambda2']:.4f}  ({(laplacian_lambda2(W0)/results['P2_西方桥恢复']['lambda2']-1)*100:+.1f}%)")

# 传播时间窗口
lb, lr = 0.0611, 0.1899
tau = 1.0 / (lb + lr)
print(f"\n弛豫周期 τ = 1/(λ_b+λ_r) = 1/{lb+lr:.4f} = {tau:.2f} 年")
print(f"2τ = {2*tau:.1f} 年, 3τ = {3*tau:.1f} 年 → 2026 起窗口 {2026+2*tau:.0f}–{2026+3*tau:.0f}")

with open('probe24_results.json', 'w') as f:
    json.dump({'results': results, 'd1': d1, 'd2': d2,
               'tau': tau, 'window': [2026 + 2 * tau, 2026 + 3 * tau]}, f, indent=2, ensure_ascii=False)
print('\n已保存 probe24_results.json')
