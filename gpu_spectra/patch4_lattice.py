#!/usr/bin/env python3
"""补丁4：验证改用相对误差判据；sweeps 20→30"""
path = 'gpu_spectra/lattice_lambdaH.py'
src = open(path).read()

old = """def check_vs_numpy(ctx, queue, prog, d, mode, n_check=32, tol=1e-9):
    \"\"\"小批量 GPU vs numpy：min1/min2 逐样本比对\"\"\"
    rng = np.random.default_rng(7)
    stride = d if mode in (0, 1) else d * d
    seeds = rng.integers(0, Q, size=(n_check, stride), dtype=np.int32)
    m1, m2 = run_lambdaH(ctx, queue, prog, seeds, d, mode)
    err1 = err2 = 0.0
    for i in range(n_check):
        G = build_G_np(seeds[i], d, mode)
        ev = np.linalg.eigvalsh(G)
        err1 = max(err1, abs(m1[i] - ev[0]))
        err2 = max(err2, abs(m2[i] - ev[1]))
    ok = max(err1, err2) < tol
    print(f"  [验证 d={d:2d} mode={mode} {MODE_NAMES[mode]:20s}] "
          f"max|Δλ1|={err1:.3e} max|Δλ2|={err2:.3e}  {'✓' if ok else '✗'}")
    return ok"""
new = """def check_vs_numpy(ctx, queue, prog, d, mode, n_check=32, rtol=1e-10):
    \"\"\"小批量 GPU vs numpy：min1/min2 逐样本比对（相对误差判据）\"\"\"
    rng = np.random.default_rng(7)
    stride = d if mode in (0, 1) else d * d
    seeds = rng.integers(0, Q, size=(n_check, stride), dtype=np.int32)
    m1, m2 = run_lambdaH(ctx, queue, prog, seeds, d, mode)
    rerr1 = rerr2 = 0.0
    for i in range(n_check):
        G = build_G_np(seeds[i], d, mode)
        ev = np.linalg.eigvalsh(G)
        scale = max(1.0, abs(ev[0]), abs(ev[1]))
        rerr1 = max(rerr1, abs(m1[i] - ev[0]) / scale)
        rerr2 = max(rerr2, abs(m2[i] - ev[1]) / scale)
    ok = max(rerr1, rerr2) < rtol
    print(f"  [验证 d={d:2d} mode={mode} {MODE_NAMES[mode]:20s}] "
          f"rel|Δλ1|={rerr1:.3e} rel|Δλ2|={rerr2:.3e}  {'✓' if ok else '✗'}")
    return ok"""
assert old in src, "1"
src = src.replace(old, new)

# run_lambdaH 默认 nsweeps 20 -> 30
old = "def run_lambdaH(ctx, queue, prog, seeds, d, mode, nsweeps=20):"
new = "def run_lambdaH(ctx, queue, prog, seeds, d, mode, nsweeps=30):"
assert old in src, "2"
src = src.replace(old, new)

# main 里的 [A] 标题文案
old = 'print("\\n[A] GPU vs numpy 正确性验证（每组 32 样本，tol=1e-9）:")'
new = 'print("\\n[A] GPU vs numpy 正确性验证（每组 32 样本，相对误差 rtol=1e-10）:")'
assert old in src, "3"
src = src.replace(old, new)

open(path, 'w').write(src)
print("patched4 OK")
