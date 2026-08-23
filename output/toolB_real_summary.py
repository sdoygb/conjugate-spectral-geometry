"""工具 B 汇总：REAL-mode vs MOD-mode（d=256）的 μ 统计对比 + κ/Λ_H 分布"""
import json
import numpy as np

def load_jsonl(path):
    recs = []
    with open(path) as f:
        for line in f:
            if line.strip():
                recs.append(json.loads(line))
    return recs

recs = load_jsonl("toolB_real_mustats.jsonl")
LH = np.array([r["LH"] for r in recs])
kap = np.array([r["kappa"] for r in recs])
th = np.array([r["theta"] for r in recs])
lam1 = np.array([r["lam1_MM"] for r in recs])
lam2 = np.array([r["lam2_MM"] for r in recs])
lammax = np.array([r["lammax_MM"] for r in recs])

print("=== REAL-mode d=256 N=%d ===" % len(recs))
def stat(name, x):
    print(f"{name}: mean={x.mean():.4f} std={x.std():.4f} CV={x.std()/x.mean():.4f} [{x.min():.4f}, {x.max():.4f}]")
stat("Λ_H", LH); stat("κ(μ)", kap); stat("θ=Λ_H/κ", th)
stat("λ1(MMᵀ)", lam1); stat("λ2(MMᵀ)", lam2); stat("λmax(MMᵀ)", lammax)
print(f"P(Λ_H>3.55)={np.mean(LH>3.55):.3f}  P(Λ_H<1.02)={np.mean(LH<1.02):.3f}  P(κ>4)={np.mean(kap>4):.3f}")

# 循环曲线（跨样本平均）
d = 256
E = np.zeros(d); Z = np.zeros(d); NZ = np.zeros(d); P = np.zeros(d)
for r in recs:
    E += np.array(r["dc_E"]); Z += np.array(r["dc_zero"])
    NZ += np.array(r["dc_nz"]); P += np.array(r["dc_pos"])
E /= len(recs); Z /= len(recs); NZ /= len(recs); P /= len(recs)

print("\n=== REAL-mode 循环标度律 ===")
print("dc | E|μ| | 归一化 | 零率 | 非零均值 | P(+|≠0)")
for dc in [1, 2, 4, 8, 16, 32, 64, 96, 128, 160, 192, 224, 256]:
    i = dc - 1
    print(f"{dc:3d} | {E[i]:.4f} | {E[i]/E[0]:.4f} | {Z[i]:.4f} | {NZ[i]:.4f} | {P[i]:.4f}")

# MOD 对比（dscan_256.npz，N=25）
d2 = np.load("toolB_dscan_256.npz")
Em = d2["dc_E"]; Zm = d2["dc_zero"]
print("\n=== MOD-mode（dscan_256, N=25）循环标度律 ===")
print("dc | E|μ| | 归一化 | 零率")
for dc in [1, 2, 4, 8, 16, 32, 64, 96, 128, 160, 192, 224, 256]:
    i = dc - 1
    print(f"{dc:3d} | {Em[i]:.4f} | {Em[i]/Em[0]:.4f} | {Zm[i]:.4f}")

# 两曲线差异（dc 1..128 的归一化差）
diff = np.abs(E[:128]/E[0] - Em[:128]/Em[0])
print(f"\n归一化曲线最大差 (dc≤128): {diff.max():.4f} at dc={diff.argmax()+1}")

# 小维度（MOD d=32/64/128）对比
for dd in [32, 64, 128]:
    try:
        dn = np.load(f"toolB_dscan_{dd}.npz")
        En = dn["dc_E"]; Zn = dn["dc_zero"]
        # 取公共 dc 范围比较（real 的 dc 1..min(d,256)）
        m = min(dd, 256)
        d1 = np.abs(E[:m]/E[0] - En[:m]/En[0])
        print(f"MOD d={dd} vs REAL d=256 归一化曲线最大差 (dc≤{m}): {d1.max():.4f}")
    except Exception as e:
        print(f"d={dd}: {e}")
