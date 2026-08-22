#!/usr/bin/env python3
"""补丁3：py 端 seeds 布局按 mode 分 stride（mode 0/1: d, mode 2: d*d）"""
path = 'gpu_spectra/lattice_lambdaH.py'
src = open(path).read()

# ---- 1. run_lambdaH：加 stride ----
old = """def run_lambdaH(ctx, queue, prog, seeds, d, mode, nsweeps=20):
    \"\"\"seeds: (N,d) int32 ∈ [0,q)；返回 min1, min2 各 (N,) float64\"\"\"
    N, dd = seeds.shape
    assert dd == d
    n = 2 * d
    seeds_c = np.ascontiguousarray(seeds, dtype=np.int32)
    mf = cl.mem_flags
    seed_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=seeds_c)
    m1 = np.empty(N, np.float64)
    m2 = np.empty(N, np.float64)
    m1_buf = cl.Buffer(ctx, mf.WRITE_ONLY, N * 8)
    m2_buf = cl.Buffer(ctx, mf.WRITE_ONLY, N * 8)
    wg = n
    prog.lattice_lambdaH(queue, (N * wg,), (wg,),
                         seed_buf, np.float64(Q), np.int32(mode),
                         m1_buf, m2_buf, np.int32(nsweeps))"""
new = """def run_lambdaH(ctx, queue, prog, seeds, d, mode, nsweeps=20):
    \"\"\"seeds: (N, stride) int32；stride=d（negacyclic 第一行）/ d*d（随机矩阵）
    返回 min1, min2 各 (N,) float64\"\"\"
    N, stride = seeds.shape
    assert stride == d or stride == d * d
    n = 2 * d
    seeds_c = np.ascontiguousarray(seeds, dtype=np.int32)
    mf = cl.mem_flags
    seed_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=seeds_c)
    m1 = np.empty(N, np.float64)
    m2 = np.empty(N, np.float64)
    m1_buf = cl.Buffer(ctx, mf.WRITE_ONLY, N * 8)
    m2_buf = cl.Buffer(ctx, mf.WRITE_ONLY, N * 8)
    wg = n
    prog.lattice_lambdaH(queue, (N * wg,), (wg,),
                         seed_buf, np.int32(stride), np.float64(Q),
                         np.int32(mode), m1_buf, m2_buf, np.int32(nsweeps))"""
assert old in src, "1"
src = src.replace(old, new)

# ---- 2. build_G_np：mode 2 需要 d*d 种子 ----
old = """def build_G_np(seeds_row, d, mode):
    \"\"\"单样本：seeds_row (d,) -> A -> G=BB^T (2d,2d)（numpy 精确参照）\"\"\"
    a = seeds_row.astype(np.float64)
    if mode == 2:
        A = a.reshape(d, d)"""
new = """def build_G_np(seeds_row, d, mode):
    \"\"\"单样本：seeds_row (stride,) -> A -> G=BB^T (2d,2d)（numpy 精确参照）
    mode 0/1 用前 d 个（negacyclic 第一行）；mode 2 用全部 d*d 个\"\"\"
    a = seeds_row.astype(np.float64)
    if mode == 2:
        A = a.reshape(d, d)"""
assert old in src, "2"
src = src.replace(old, new)

# ---- 3. check_vs_numpy：按 mode 生成对应 stride 的 seeds ----
old = """    rng = np.random.default_rng(7)
    seeds = rng.integers(0, Q, size=(n_check, d), dtype=np.int32)
    m1, m2 = run_lambdaH(ctx, queue, prog, seeds, d, mode)"""
new = """    rng = np.random.default_rng(7)
    stride = d if mode in (0, 1) else d * d
    seeds = rng.integers(0, Q, size=(n_check, stride), dtype=np.int32)
    m1, m2 = run_lambdaH(ctx, queue, prog, seeds, d, mode)"""
assert old in src, "3"
src = src.replace(old, new)

# ---- 4. run_experiment：按 mode 生成对应 stride 的 seeds ----
old = """    rng = np.random.default_rng(seed)
    seeds = rng.integers(0, Q, size=(N, d), dtype=np.int32)
    t0 = time.perf_counter()
    m1, m2 = run_lambdaH(ctx, queue, prog, seeds, d, mode)"""
new = """    rng = np.random.default_rng(seed)
    stride = d if mode in (0, 1) else d * d
    seeds = rng.integers(0, Q, size=(N, stride), dtype=np.int32)
    t0 = time.perf_counter()
    m1, m2 = run_lambdaH(ctx, queue, prog, seeds, d, mode)"""
assert old in src, "4"
src = src.replace(old, new)

open(path, 'w').write(src)
print("patched3 OK")
