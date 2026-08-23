#!/usr/bin/env python3
"""
探针㉓：欧美外部场对东亚子系统谱结构的影响
============================================
把 US/EU 作为外部强耦合节点加入国家耦合图，
检验贸易通道（探针⑩ 第三通道）如何改变区域谱间隙 λ₂ 与二部化指标。

数据来源（2025 年双边贸易额，$B/年）：
- CN-US 574.66 (中国海关 2025) / CN-EU 785.8 (中国海关 2024)
- CN-TW ~250 (估算: 台对陆出口 ~160 + 陆对台 ~90)
- CN-JP ~300 / CN-IN ~130
- US-TW ~150 (美方逆差 126.9 单边, 双向约 150)
- US-IN 239.4 / US-JP ~250
- EU-IN 136 / EU-TW ~60 / JP-TW ~80 / JP-IN ~25 / TW-IN ~15

归一化: w = trade / 785.8 (以中欧为 1.0 基准)

节点: 0=CN 1=TW 2=JP 3=IN 4=US 5=EU
"""
import numpy as np
import json

# ---- 基础边权 (S0 现状) ----
base = 785.8
W = np.zeros((6, 6))
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
    W[i, j] = W[j, i] = v / base

names = ['CN', 'TW', 'JP', 'IN', 'US', 'EU']


def laplacian_lambda2(Wmat):
    """加权 Laplacian 的代数连通度 λ₂"""
    L = np.diag(Wmat.sum(axis=1)) - Wmat
    ev = np.sort(np.linalg.eigvalsh(L))
    return ev[1]


def bipartite_residual(Wmat):
    """二部化指标: 邻接谱 ±λ 配对残差 (探针④ T3 判据, 0=完美二部)"""
    ev = np.sort(np.linalg.eigvalsh(Wmat))
    n = len(ev)
    res = 0.0
    for i in range(n // 2):
        res += abs(ev[i] + ev[n - 1 - i])
    return res / (n // 2)


def report(tag, Wmat):
    l2 = laplacian_lambda2(Wmat)
    br = bipartite_residual(Wmat)
    print(f"{tag:28s} λ₂={l2:.4f}   二部配对残差={br:.4f}")
    return l2, br


print("=== 探针㉓: 欧美外部场对东亚子系统谱结构的影响 ===\n")
print("节点: CN TW JP IN US EU (边权=贸易额/785.8)\n")

results = {}
# S0 现状
l2_0, br_0 = report("S0 现状", W)
results['S0'] = {'lambda2': l2_0, 'bipartite': br_0}

# S1 中美脱钩 (关税覆盖100%, 贸易通道降权)
W1 = W.copy()
W1[0, 4] = W1[4, 0] = 574.66 * 0.3 / base
l2_1, br_1 = report("S1 中美脱钩 (CN-US×0.3)", W1)
results['S1'] = {'lambda2': l2_1, 'bipartite': br_1}

# S2 美台强化 (贸易协定+500B投资)
W2 = W.copy()
W2[4, 1] = W2[1, 4] = 150.0 * 1.5 / base
l2_2, br_2 = report("S2 美台强化 (US-TW×1.5)", W2)
results['S2'] = {'lambda2': l2_2, 'bipartite': br_2}

# S3 欧印强化 (FTA达成)
W3 = W.copy()
W3[5, 3] = W3[3, 5] = 136.0 * 2.0 / base
l2_3, br_3 = report("S3 欧印强化 (EU-IN×2)", W3)
results['S3'] = {'lambda2': l2_3, 'bipartite': br_3}

# S4 组合 (脱钩+两翼强化)
W4 = W.copy()
W4[0, 4] = W4[4, 0] = 574.66 * 0.3 / base
W4[4, 1] = W4[1, 4] = 150.0 * 1.5 / base
W4[5, 3] = W4[3, 5] = 136.0 * 2.0 / base
l2_4, br_4 = report("S4 组合 (脱钩+美台+欧印)", W4)
results['S4'] = {'lambda2': l2_4, 'bipartite': br_4}

# S5 两岸耦合削弱 (CN-TW×0.5, 极端情景)
W5 = W.copy()
W5[0, 1] = W5[1, 0] = 250.0 * 0.5 / base
l2_5, br_5 = report("S5 两岸耦合削弱 (CN-TW×0.5)", W5)
results['S5'] = {'lambda2': l2_5, 'bipartite': br_5}

print("\n=== 关键扫描: US-TW / CN-TW 强度比 r (二部化相变检验) ===")
print("r    λ₂(全图)   二部配对残差")
scan = []
for r in np.linspace(0.1, 3.0, 30):
    Ws = W.copy()
    Ws[4, 1] = Ws[1, 4] = 250.0 * r / base  # US-TW 相对 CN-TW=250 的强度比
    l2 = laplacian_lambda2(Ws)
    br = bipartite_residual(Ws)
    scan.append({'r': float(r), 'lambda2': float(l2), 'bipartite': float(br)})
    if abs(r - 0.5) < 0.01 or abs(r - 1.0) < 0.01 or abs(r - 1.5) < 0.01 or abs(r - 2.0) < 0.01 or abs(r - 2.5) < 0.01:
        print(f"{r:.1f}   {l2:.4f}   {br:.4f}")

# 关键点: r=1 (美台=两岸) 与 r=2 (美台=2×两岸)
r_pts = {}
for r in [0.5, 1.0, 1.5, 2.0, 2.5]:
    Ws = W.copy()
    Ws[4, 1] = Ws[1, 4] = 250.0 * r / base
    r_pts[str(r)] = {
        'lambda2': float(laplacian_lambda2(Ws)),
        'bipartite': float(bipartite_residual(Ws)),
    }

# 台湾的"阵营归属": 比较 CN-TW 与 US-TW 的度贡献
print("\n=== 台湾节点的耦合分配 (度贡献) ===")
for tag, Wm in [('S0 现状', W), ('S2 美台强化', W2), ('S4 组合', W4)]:
    cn_tw = Wm[0, 1]
    us_tw = Wm[4, 1]
    eu_tw = Wm[5, 1]
    jp_tw = Wm[2, 1]
    total = cn_tw + us_tw + eu_tw + jp_tw
    print(f"{tag:12s} CN-TW={cn_tw:.3f} ({cn_tw/total*100:.0f}%)  US-TW={us_tw:.3f} ({us_tw/total*100:.0f}%)  "
          f"EU-TW={eu_tw:.3f} ({eu_tw/total*100:.0f}%)  JP-TW={jp_tw:.3f} ({jp_tw/total*100:.0f}%)")

out = {
    'results': results,
    'scan': scan,
    'r_points': r_pts,
}
with open('gpu_spectra/society/probe23_results.json', 'w') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("\n已保存 probe23_results.json")
