"""工具 B d 扫描汇总：循环标度律普适性 + κ 分布 Gamma 形状 + 尾部概率
读 toolB_dscan_{d}.npz (d=32,64,128,256) 与 toolB_p2_centered.npz
"""
import numpy as np
from scipy import stats

def summarize(d, tag=""):
    f = f"toolB_dscan_{d}.npz"
    try:
        z = np.load(f)
    except FileNotFoundError:
        print(f"[{tag}] d={d}: 文件缺失"); return None
    LH, kap, th = z['LH'], z['kappa'], z['theta']
    dcE, dcz, dcnz, dcpos = z['dc_E'], z['dc_zero'], z['dc_nz'], z['dc_pos']
    # Gamma 拟合（三参数：shape, loc, scale）
    try:
        gs, gl, gsc = stats.gamma.fit(kap, floc=0)
        ks_p = stats.kstest(kap, 'gamma', args=(gs, gl, gsc)).pvalue
        ks_str = f"KS p={ks_p:.3f}"
    except Exception as e:
        gs = gl = gsc = np.nan; ks_str = f"fit失败 {e}"
    ln_s, ln_l, ln_sc = stats.lognorm.fit(kap, floc=0)
    print(f"===== d={d} N={len(LH)} [{tag}] =====")
    print(f"Λ_H:  mean={LH.mean():.3f} CV={LH.std()/LH.mean():.3f} [{LH.min():.2f}, {LH.max():.2f}]  P(>4)={np.mean(LH>4):.3f} P(<1.2)={np.mean(LH<1.2):.3f}")
    print(f"κ:    mean={kap.mean():.3f} CV={kap.std()/kap.mean():.3f} [{kap.min():.2f}, {kap.max():.2f}]  P(>4)={np.mean(kap>4):.3f}")
    print(f"θ:    mean={th.mean():.3f} std={th.std():.3f}")
    print(f"Gamma fit: shape={gs:.3f} loc={gl:.3f} scale={gsc:.3f}  {ks_str}")
    print(f"lognorm:  s={ln_s:.3f} scale={ln_sc:.3f}")
    # 循环标度律：归一化 E|μ|(dc)/E|μ|(1)
    norm = dcE / dcE[0]
    pts = [0, 1, 3, 7, 15, 31, 63, 127, 255]
    sel = [p for p in pts if p < len(norm)]
    print("归一化 E|μ|(dc): " + "  ".join(f"dc{p+1}:{norm[p]:.3f}" for p in sel))
    # 稀疏率
    selz = [p for p in pts if p < len(dcz)]
    print("稀疏率 P(μ=0):  " + "  ".join(f"dc{p+1}:{dcz[p]:.3f}" for p in selz))
    # 符号偏置（近距离）
    print(f"P(μ>0|μ≠0) dc1-4: {dcpos[0]:.3f} {dcpos[1]:.3f} {dcpos[2]:.3f} {dcpos[3]:.3f}")
    return dict(d=d, LH=LH, kap=kap, th=th, dcE=dcE, dcz=dcz)

print("=" * 70)
res = {}
for d in [32, 64, 128, 256]:
    r = summarize(d, "非中心化")
    if r: res[d] = r
print("=" * 70)
