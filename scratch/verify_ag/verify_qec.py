#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共扼谱几何 1024 家族四档标度律——经典侧端到端验证
V1: [[16,6,4]] 完整量子模拟（态向量 + 稳定子投影 + 最小权重解码）
    ——不依赖任何"经典化"公式，直接算相干注入下的 loss(θ)
V2: [[32,20,4]] / [[64,20,8]] 蒙特卡洛（二项错误注入 + 查表最小权重解码器）
V3: 1024 四档闭式曲线 + 三参数拟合统计功效（10.36 判别方案预演）
码构造：CSS(RM(m-r-1,m), RM(r,m))，d = 2^(r+1)，稳定子 = RM(r,m) 基（X+Z 型）
"""
import numpy as np
from math import comb
import itertools, time

np.set_printoptions(precision=6, suppress=True)
t0 = time.time()
def log(msg):
    print(f"[{time.time()-t0:7.1f}s] {msg}", flush=True)

# ================= RM 码工具 =================
def rm_basis(r, m):
    """RM(r,m) 单项式基：返回 [(指数元组, 2^m bit 支撑整数), ...]"""
    gens = []
    for deg in range(r + 1):
        for S in itertools.combinations(range(m), deg):
            v = 0
            for x in range(1 << m):
                val = 1
                for i in S:
                    if not ((x >> i) & 1):
                        val = 0
                        break
                v |= (val << x)
            gens.append((S, v))
    return gens

def dim_rm(r, m):
    return sum(comb(m, k) for k in range(r + 1))

def gauss_binom(n, k):
    num = den = 1
    for i in range(k):
        num *= (1 << (n - i)) - 1
        den *= (1 << (k - i)) - 1
    return num // den

def flats(m, s):
    return (1 << (m - s)) * gauss_binom(m, s)

def parity_int(x):
    return bin(x).count('1') & 1

def pc(x):
    """popcount parity（Python 3.9 兼容）"""
    return bin(x).count('1') & 1

# ================= V1: [[16,6,4]] 完整量子模拟 =================
def v1_code():
    m, r = 4, 1
    n = 1 << m
    z_gens = rm_basis(r, m)          # Z 稳定子基（RM(1,4)，5 个）
    z_supps = [g for _, g in z_gens]
    x_gens = rm_basis(r, m)          # X 稳定子基（同集合）
    # 逻辑 Z：deg-2 单项式（RM(2,4)/RM(1,4) 代表元）
    zl_supp = None
    for S, v in rm_basis(m - r - 1, m):
        if len(S) == 2:
            zl_supp = v
            break
    return n, z_supps, x_gens, zl_supp

def v1_state(theta_max, seed=1):
    """构造 |0_L⟩，注入 Rx(θ_i)（θ_i 均匀 ≤ θ_max），返回态向量"""
    n, z_supps, x_gens, zl_supp = v1_code()
    # |0_L⟩ = Π (I+X^g)/2 |0^n⟩
    psi = np.zeros(1 << n, dtype=complex)
    psi[0] = 1.0
    idx = np.arange(1 << n)
    for _, g in x_gens:
        perm = idx ^ g
        psi = (psi + psi[perm]) / 2.0
    psi /= np.linalg.norm(psi)
    # 注入：每比特 Rx(θ_i)，θ_i 均匀 [0, θ_max]
    # Rx(θ) = cos(θ/2)·I − i·sin(θ/2)·X
    rng = np.random.default_rng(seed)
    for i in range(n):
        th = rng.uniform(0.0, theta_max)
        c = np.cos(th / 2); s = np.sin(th / 2)
        e = 1 << i
        perm = idx ^ e
        psi = c * psi - 1j * s * psi[perm]
    return psi

def v1_decoder():
    """最小权重解码：全枚举 2^16 掩码（按权重升序），syndrome -> 最小权重错误"""
    n, z_supps, _, _ = v1_code()
    table = {}
    # 按权重升序枚举全部掩码
    for w in range(n + 1):
        for E in itertools.combinations(range(n), w):
            mask = sum(1 << i for i in E)
            s = 0
            for j, g in enumerate(z_supps):
                s |= pc(mask & g) << j
            if s not in table:
                table[s] = mask
    return table

_V1_TABLE = None
def v1_get_table():
    global _V1_TABLE
    if _V1_TABLE is None:
        _V1_TABLE = v1_decoder()
    return _V1_TABLE

def v1_loss(theta_max, seed=1):
    """完整量子 loss：Σ_s P(s)·loss(s)
    loss(s)：最小权重解码 Es 恢复后 Z_L 期望 = (−1)^{Es·zl}·⟨ψ_s|Z^{zl}|ψ_s⟩"""
    n, z_supps, _, zl_supp = v1_code()
    table = v1_get_table()
    psi = v1_state(theta_max, seed)
    idx = np.arange(1 << n)
    # parity 查表（2^16）
    par = np.zeros(1 << n, dtype=np.uint8)
    for x in range(1 << n):
        par[x] = bin(x).count('1') & 1
    # syndrome 数组：s(x) = Σ_j parity(x & g_j)·2^j
    s_arr = np.zeros(1 << n, dtype=np.int64)
    for j, g in enumerate(z_supps):
        s_arr += par[idx & g].astype(np.int64) << j
    amp2 = np.abs(psi) ** 2
    P = np.bincount(s_arr, weights=amp2, minlength=1 << len(z_supps)).astype(float)
    # 每 syndrome 的 loss
    zl_par = par[idx & zl_supp].astype(np.int64)  # 每 x 的 Z_L 奇偶
    loss_s = np.zeros(len(P))
    for s in range(len(P)):
        if P[s] < 1e-300:
            continue
        mask = (s_arr == s)
        psi_s = psi[mask]
        psi_s /= np.linalg.norm(psi_s)
        exp_zl = np.sum(np.abs(psi_s) ** 2 * np.where(zl_par[mask] == 1, -1.0, 1.0))
        Es = table.get(s, 0)
        phase = -1.0 if parity_int(Es & zl_supp) else 1.0
        exp_zl *= phase
        loss_s[s] = (1.0 - exp_zl) / 2.0
    loss = float(np.sum(P * loss_s))
    return loss, P, loss_s

def v1_run():
    print("=" * 70)
    print("V1: [[16,6,4]] 完整量子模拟（含干涉，最小权重解码）")
    print("=" * 70)
    n, z_supps, _, zl_supp = v1_code()
    print(f"码参数: n={n}, Z 稳定子数={len(z_supps)}, 逻辑 Z 支撑={bin(zl_supp).count('1')} 点")
    # 闭式（定理 10.35.1.02，m=4, r=1）
    c4 = (1 - 2 ** (1 - 4)) * comb(16, 2) * 2 ** -4
    c6 = comb(16, 3) * 2 ** -6   # 次主阶：P'(3)=1（任意 3 点 ⊂ 2-平坦）
    print(f"闭式: c4 = {c4:.6f}, c6(次主阶) = {c6:.6f}")
    ths = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
    print(f"{'θ':>6} {'loss(量子)':>12} {'loss(公式)':>12} {'主阶':>12} {'比值':>8}")
    rows = []
    for th in ths:
        loss, P, loss_s = v1_loss(th)
        f_main = c4 * th ** 4
        f_form = f_main + c6 * th ** 6
        rows.append((th, loss, f_form))
        print(f"{th:6.2f} {loss:12.6e} {f_form:12.6e} {f_main:12.6e} {loss/f_form:8.4f}")
    lo = [(th, loss) for th, loss, _ in rows if th <= 0.25]
    lx = np.log(np.array([t for t, _ in lo]))
    ly = np.log(np.array([l for _, l in lo]))
    slope = np.polyfit(lx, ly, 1)[0]
    print(f"低 θ 区 log-log 斜率（θ≤0.25）: {slope:.4f}（理论 4）")
    res = [abs(loss - ff) / ff for _, loss, ff in rows]
    print(f"公式-模拟相对偏差: max {max(res)*100:.2f}%, 平均 {np.mean(res)*100:.2f}%")
    return rows

# ================= V2: 蒙特卡洛端到端 =================
def v2_code(m, r):
    n = 1 << m
    z_gens = rm_basis(r, m)
    z_supps = [g for _, g in z_gens]
    # 逻辑 Z：deg-(r+1) 单项式（∈ RM(m-r-1,m) \ RM(r,m)）
    zl_supp = None
    for S, v in rm_basis(m - r - 1, m):
        if len(S) == r + 1:
            zl_supp = v
            break
    return n, z_supps, zl_supp

def v2_build_decoder(n, z_supps, w0):
    n_cand = sum(comb(n, w) for w in range(w0 + 1))
    log(f"构建解码查表: n={n}, w0={w0}, 候选数={n_cand}")
    table = {}
    for w in range(w0 + 1):
        for E in itertools.combinations(range(n), w):
            mask = sum(1 << i for i in E)
            s = 0
            for j, g in enumerate(z_supps):
                s |= pc(mask & g) << j
            if s not in table:
                table[s] = mask
    log(f"查表完成: {len(table)} 个 syndrome 类")
    return table

def v2_mc(n, z_supps, table, zl_supp, theta, nshots, rng, diagnose=False):
    """二项注入：每比特 X 错误概率 θ²/4。返回 (loss, 失败数)"""
    p = theta * theta / 4.0
    fails = 0
    if diagnose:
        from collections import Counter, defaultdict
        w_fail = defaultdict(int); w_amb = defaultdict(int); w_tot = defaultdict(int)
    for _ in range(nshots):
        w = int(rng.binomial(n, p))
        if w:
            pos = [int(x) for x in rng.choice(n, w, replace=False)]
            mask = 0
            for i in pos:
                mask |= 1 << i
        else:
            mask = 0
        s = 0
        for j, g in enumerate(z_supps):
            s |= pc(mask & g) << j
        Es = table.get(s, 0)
        rem = mask ^ Es
        if diagnose:
            w_tot[w] += 1
            if Es != mask:
                w_amb[w] += 1
            if pc(rem & zl_supp):
                w_fail[w] += 1
        else:
            if pc(rem & zl_supp):
                fails += 1
    if diagnose:
        return fails / nshots, fails, w_fail, w_amb, w_tot
    return fails / nshots, fails

def v2_run():
    print("=" * 70)
    print("V2: 蒙特卡洛端到端（真实最小权重解码器）")
    print("=" * 70)
    rng = np.random.default_rng(42)
    configs = [(5, 1, 0.10, 0.40, 4), (6, 2, 0.10, 0.45, 6)]
    for m, r, th_lo, th_hi, npts in configs:
        n, z_supps, zl_supp = v2_code(m, r)
        w0 = 2 ** r
        print(f"\n--- CSS(RM({m-r-1},{m}), RM({r},{m})) = [[{n},{n-2*dim_rm(r,m)},{2**(r+1)}]] ---")
        print(f"Z 稳定子数 = {len(z_supps)}（dim RM({r},{m}) = {dim_rm(r,m)}）")
        table = v2_build_decoder(n, z_supps, w0)
        ths = [th_lo + (th_hi - th_lo) * i / (npts - 1) for i in range(npts)]
        nshots = 200000
        print(f"{'θ':>6} {'loss(MC)':>12} {'失败数':>8} {'loss/θ^d':>12}")
        rows = []
        for th in ths:
            loss, fails = v2_mc(n, z_supps, table, zl_supp, th, nshots, rng)
            rows.append((th, loss))
            print(f"{th:6.3f} {loss:12.6e} {fails:8d} {loss/(th**(2**(r+1))):12.4e}")
        # 剔除零失败点后拟合
        rows_nz = [(t, l) for t, l in rows if l > 0]
        lx = np.log(np.array([t for t, _ in rows_nz]))
        ly = np.log(np.array([l for _, l in rows_nz]))
        slope = np.polyfit(lx, ly, 1)[0]
        print(f"log-log 斜率（剔除零失败）: {slope:.4f}（理论 {2**(r+1)}）")
        # 分层诊断（θ 中点）
        th_diag = ths[len(ths)//2]
        loss_d, fails_d, w_fail, w_amb, w_tot = v2_mc(n, z_supps, table, zl_supp, th_diag, nshots, rng, diagnose=True)
        print(f"分层诊断 θ={th_diag:.3f}: 权重 -> 二义/翻转/κ")
        for w in sorted(w_tot):
            if w_tot[w] > 0:
                amb = w_amb[w] / w_tot[w]
                flp = w_fail[w] / w_tot[w]
                kap = w_fail[w] / w_amb[w] if w_amb[w] else 0
                print(f"  w={w}: 二义={amb:.4f} 翻转={flp:.4f} κ={kap:.4f}")
        cd = np.mean([l / t ** (2 ** (r+1)) for t, l in rows])
        print(f"归一化系数 c_d 实测: {cd:.4e}")
        if r == 1:
            c_th = (1 - 2 ** (1 - m)) * comb(n, 2) * 2 ** -4
            print(f"闭式 c_d = (1-2^(1-m))·C(n,2)·2^-4 = {c_th:.4e}（偏差 {(cd-c_th)/c_th*100:+.2f}%）")
    return rows

# ================= V3: 1024 闭式 + 拟合功效 =================
def v3_formula_coeffs():
    """10.35 定理 10.35.1.02：m=10 四档主阶+次主阶系数"""
    m = 10
    out = {}
    # r=1: [[1024,1002,4]]  P=1, fail=1-2^(1-m), w0=2
    fail = 1 - 2 ** (1 - m)
    c4 = comb(1024, 2) * fail * 2 ** -4
    c6 = comb(1024, 3) * 2 ** -6
    out['r1'] = (c4, c6, fail)
    # r=2: [[1024,912,8]]  P=1, fail=0.5005（10.35 表 m=10）
    fail2 = 0.5005
    c8 = comb(1024, 4) * fail2 * 2 ** -8
    c10 = comb(1024, 5) * 4.8976e-3 * 2 ** -10
    out['r2'] = (c8, c10, fail2)
    # r=3: [[1024,672,16]]  P·fail = 1.514e-6·0.5
    p3fail = 1.514e-6 * 0.5
    c16 = comb(1024, 8) * p3fail * 2 ** -16
    Pp9 = flats(10, 4) * comb(16, 9) / comb(1024, 9)
    c18 = comb(1024, 9) * Pp9 * 2 ** -18
    out['r3'] = (c16, c18, 0.5)
    # r=4: [[1024,252,32]]  P4 = 3.383e-17, fail ≈ 1/2
    P4 = 3.383e-17
    c32 = comb(1024, 16) * P4 * 0.5 * 2 ** -32
    Pp17 = flats(10, 5) * comb(32, 17) / comb(1024, 17)
    c34 = comb(1024, 17) * Pp17 * 2 ** -34
    out['r4'] = (c32, c34, 0.5)
    return out

def v3_run():
    print("=" * 70)
    print("V3: 1024 四档闭式曲线 + 窗口 + 三参数拟合功效")
    print("=" * 70)
    coeffs = v3_formula_coeffs()
    names = {'r1': ('[[1024,1002,4]]', 4), 'r2': ('[[1024,912,8]]', 8),
             'r3': ('[[1024,672,16]]', 16), 'r4': ('[[1024,252,32]]', 32)}
    print(f"\n{'档':<18} {'主阶系数 c_d':>14} {'次主阶 c_{d+2}':>16} {'fail':>8}")
    for k, (cd, cd2, fail) in coeffs.items():
        print(f"{names[k][0]:<18} {cd:14.4e} {cd2:16.4e} {fail:8.4f}")
    print(f"\n{'θ':>6}", end='')
    for k in coeffs:
        print(f" {'loss('+names[k][0].replace('[','').replace(']','')+')':>16}", end='')
    print()
    ths = [0.013, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09,
           0.15, 0.20, 0.25, 0.30, 0.40, 0.45, 0.47, 0.50, 0.52]
    curve = {}
    for th in ths:
        print(f"{th:6.3f}", end='')
        for k, (cd, cd2, _) in coeffs.items():
            l = cd * th ** names[k][1] + cd2 * th ** (names[k][1] + 2)
            curve.setdefault(k, []).append((th, l))
            print(f" {l:16.4e}", end='')
        print()
    print(f"\n可观测窗口（loss ∈ [1e-3, 0.5]，主阶）:")
    for k, (cd, cd2, _) in coeffs.items():
        d = names[k][1]
        th_lo = (1e-3 / cd) ** (1 / d)
        th_hi = (0.5 / cd) ** (1 / d)
        print(f"  {names[k][0]}: θ ∈ [{th_lo:.4f}, {th_hi:.4f}]（ln 跨度 {np.log(th_hi/th_lo):.3f}）")
    print(f"\n三参数拟合功效（loss = b + cθ^d，N=2e5 shot/点，50 次重复）:")
    try:
        from scipy.optimize import curve_fit
        have_scipy = True
    except ImportError:
        have_scipy = False
        print("  scipy 不可用，跳过拟合功效")
    if have_scipy:
        rng = np.random.default_rng(7)
        windows = {'r1': [0.013, 0.02, 0.03, 0.04, 0.05],
                   'r2': [0.06, 0.07, 0.08, 0.09],
                   'r3': [0.20, 0.22, 0.25, 0.27],
                   'r4': [0.45, 0.47, 0.50, 0.52]}
        for k in coeffs:
            cd, cd2, _ = coeffs[k]
            d_true = names[k][1]
            ths_k = windows[k]
            N = 200000
            ds = []
            for rep in range(50):
                loss_true = [cd * t ** d_true + cd2 * t ** (d_true + 2) for t in ths_k]
                loss_obs = []
                for l in loss_true:
                    l = min(max(l, 1e-6), 1.0)
                    n_fail = rng.binomial(N, l)
                    loss_obs.append(n_fail / N)
                def model(th, b, c, d, e):
                    return b + c * th ** d + e * th ** (d + 2)
                try:
                    popt, pcov = curve_fit(model, ths_k, loss_obs, p0=[0.0, cd, d_true, cd2],
                                           bounds=([-1, 0, 0.5, -1e15], [1, 1e15, 64, 1e15]), maxfev=20000)
                    ds.append(popt[2])
                except Exception:
                    pass
            if ds:
                ds = np.array(ds)
                print(f"  {names[k][0]}: d̂ = {ds.mean():.3f} ± {ds.std():.3f}（真值 {d_true}，"
                      f"偏差 {(ds.mean()-d_true)/ds.std():+.1f}σ）")
    return curve

if __name__ == '__main__':
    rows1 = v1_run()
    rows2 = v2_run()
    v3_run()
    log("全部完成")
