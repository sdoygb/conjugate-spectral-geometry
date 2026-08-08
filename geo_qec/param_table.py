"""param_table.py —— 任务 6：AG 完备码族 [[2^m, k, 2^{r+1}]] 完整参数表
全部来自 10.35 闭式（引理 10.35.2.06/07/09/10，定理 10.35.1.01/1.07），零模拟：
  n = 2^m,  k = n - 2*dim RM(r,m),  d = 2^{r+1},  w0 = 2^r
  P(w0)  = [flats(m,r+1)*E(r+1,w0) + flats(m,r)] / C(n,w0)         (10.33 闭式)
  fail(w0) = 1 - P(r)/(v(r)*P(w0)) - P(r+1)/(v(r+1)*P(w0))        (引理 10.35.2.07)
  v(r) = 2^{m-r},  v(r+1) = 2                                     (引理 10.35.2.06)
  kappa_r(m) = 2^{(r+1)(m-r-1)} / [m choose r+1]_2                (引理 10.35.2.10)
  c_d   = C(n,w0)*P(w0)*fail(w0)*kappa*2^{-2w0}      (loss_Z 主阶，定理 10.35.1.07)
  c'    = C(n,w0+1)*P'(w0+1)*kappa*2^{-2(w0+1)}      (loss_Z 次主阶，引理 10.35.2.09 × kappa)
  rho   = c'/c_d
"""
from math import comb
from fractions import Fraction

def gb(m, k):
    """高斯二项 [m k]_2（正整数）"""
    if k < 0 or k > m:
        return 0
    num = den = 1
    for i in range(k):
        num *= (1 << (m - i)) - 1
        den *= (1 << (k - i)) - 1
    return num // den

def flats(m, k):
    """m 维 F_2 空间中 k-平坦数 = 2^{m-k} [m k]_2"""
    return (1 << (m - k)) * gb(m, k)

_E = {}
def E(k, s):
    """k 维平坦内、仿射包恰 k 维的 s 点子集数（递推 E(k,s) = C(2^k,s) - sum_{j<k} flats(k,j) E(j,s)）"""
    key = (k, s)
    if key in _E:
        return _E[key]
    if s == 1:
        r = 1 if k == 0 else 0          # 单点仿射包 0 维
        _E[key] = r
        return r
    if k == 0 or s > (1 << k):
        _E[key] = 0
        return 0
    total = comb(1 << k, s)
    for j in range(k):
        total -= flats(k, j) * E(j, s)
    _E[key] = total
    return total

def ag_params(m, r):
    """返回 AG 完备码 [[2^m, k, 2^{r+1}]] 的全套参数（10.35 闭式）"""
    n = 1 << m
    d = 1 << (r + 1)
    w0 = 1 << r
    dim_rm = sum(comb(m, i) for i in range(r + 1))
    k = n - 2 * dim_rm
    if k < 1:
        return None
    # --- P(w0)：权重 w0 子集包含于 (r+1)-平坦的比例（10.33 闭式）---
    Pw = Fraction(flats(m, r + 1) * E(r + 1, w0) + flats(m, r), comb(n, w0))
    # --- 仿射包恰 r / r+1 维的比例 P(r), P(r+1) ---
    Pr  = Fraction(flats(m, r), comb(n, w0))
    Pr1 = Fraction(flats(m, r + 1) * E(r + 1, w0), comb(n, w0))
    # --- 类大小 v(r) = 2^{m-r}, v(r+1) = 2（引理 10.35.2.06）---
    v_r, v_r1 = 1 << (m - r), 2
    # --- fail(w0)（引理 10.35.2.07）---
    fail = Fraction(1) - Pr / (v_r * Pw) - Pr1 / (v_r1 * Pw)
    # --- kappa（引理 10.35.2.10）---
    kap = (1 << ((r + 1) * (m - r - 1))) / gb(m, r + 1)
    # --- 次主阶简并比例 P'(w0+1)（引理 10.35.2.09）---
    Pprime = Fraction(flats(m, r + 1) * comb(1 << (r + 1), w0 + 1), comb(n, w0 + 1))
    # --- 系数（loss_Z 版，× kappa；次主阶亦 × kappa）---
    c_d  = float(Fraction(comb(n, w0)) * Pw * fail / (1 << (2 * w0))) * kap
    c_nx = float(Fraction(comb(n, w0 + 1)) * Pprime / (1 << (2 * (w0 + 1)))) * kap
    import math
    ln_cd = math.log(c_d)
    return dict(m=m, r=r, n=n, k=k, d=d, w0=w0,
                Pw=float(Pw), Pr=float(Pr), Pr1=float(Pr1),
                fail=float(fail), kap=kap,
                Pprime=float(Pprime), c_d=c_d, ln_cd=ln_cd, c_nx=c_nx,
                rho=c_nx / c_d)

def main():
    rows = []
    for m in range(3, 13):
        for r in range(1, min(4, (m - 1) // 2) + 1):
            p = ag_params(m, r)
            if p is None:
                continue
            rows.append(p)
    # ---- Markdown 表 ----
    lines = []
    lines.append("| $m$ | $r$ | 码 $[[n,k,d]]$ | $w_0$ | $P(w_0)$ | $\\mathrm{fail}(w_0)$ | $\\kappa_r(m)$ | $c_d$（loss$_Z$） | $\\ln c_d$ | $c'$（次主阶） | $\\rho=c'/c_d$ |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for p in rows:
        lines.append(
            f"| {p['m']} | {p['r']} | $[[{p['n']},{p['k']},{p['d']}]]$ | {p['w0']} "
            f"| {p['Pw']:.6g} | {p['fail']:.6g} | {p['kap']:.6g} "
            f"| {p['c_d']:.6g} | {p['ln_cd']:.4f} | {p['c_nx']:.6g} | {p['rho']:.6g} |")
    text = "\n".join(lines)
    with open("param_table.md", "w", encoding="utf-8") as f:
        f.write("# AG 完备码族完整参数表（10.35 闭式，任务 6）\n\n" + text + "\n")
    print(text)
    # 与 10.36 表交叉验证（m=10）
    print("\n--- 交叉验证 m=10（10.36 表：c_d = 1.23e4 / 2.94e7 / 1.05e8 / 7.53e7；kappa = 0.3761/0.3304/0.3122/0.3072）---")
    for p in rows:
        if p['m'] == 10:
            print(f"  r={p['r']}: kappa={p['kap']:.4f}  c_d={p['c_d']:.4e}  ln c_d={p['ln_cd']:.3f}  fail={p['fail']:.4f}  Pw={p['Pw']:.4g}  rho={p['rho']:.4g}")

if __name__ == "__main__":
    main()
