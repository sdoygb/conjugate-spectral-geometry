#!/usr/bin/env python3
"""surface code 解码 + 错误模式空间结构分析（几何论切入点）

流程：
  1. stim 生成 surface code 电路（含噪声模型）→ 采样 detector 数据
  2. PyMatching (MWPM) 解码 → 逻辑错误率 vs 噪声
  3. 错误模式空间结构分析（几何论语言）：
     - A0 类（局域错误）：激发局域、可修正 → "平凡拓扑"（Berry 相位 0）
     - A1 类（逻辑错误）：错误链跨边界非平凡 → "整体拓扑"（Berry 相位 2π）
  4. 量化对比：逻辑错误 vs 非逻辑错误的激发空间结构差异
     特征：激发数 / 最近激发对距离 / 空间直径 / 边界距离 / 最大簇大小

用法：
  python3 toric_decode.py [--L 4] [--rounds 3] [--noise 0.03] [--shots 20000]
  python3 toric_decode.py --scan     # 扫描逻辑错误率 vs 噪声
"""
import numpy as np
import stim
import pymatching
import argparse, time
from collections import defaultdict

# ---------- 1. 电路生成 + 解码 ----------

def build_circuit(L, rounds, noise):
    """surface code 电路（stim 内置生成器），噪声 = 统一 depolarizing/翻转率"""
    return stim.Circuit.generated(
        "surface_code:unrotated_memory_z",
        distance=L,
        rounds=rounds,
        after_clifford_depolarization=noise,
        before_round_data_depolarization=noise,
        after_reset_flip_probability=noise,
        before_measure_flip_probability=noise,
    )

def get_detector_coords(circuit):
    """stim 1.15 返回 {det_idx: [x, y, t]}"""
    try:
        return circuit.get_detector_coordinates()
    except Exception:
        return None

def decode(L, rounds, noise, shots):
    t0 = time.time()
    circuit = build_circuit(L, rounds, noise)
    dem = circuit.detector_error_model(decompose_errors=False)
    matching = pymatching.Matching.from_detector_error_model(dem)
    sampler = circuit.compile_detector_sampler()
    dets, obs = sampler.sample(shots, separate_observables=True)
    preds = matching.decode_batch(dets)
    le = np.any(preds != obs, axis=1)
    coords = get_detector_coords(circuit)
    return dict(circuit=circuit, dets=dets, obs=obs, preds=preds, le=le,
                coords=coords, matching=matching, n_det=dets.shape[1],
                dt=time.time() - t0)

# ---------- 2. 错误模式空间结构分析 ----------

def cluster_sizes(ps):
    """ps: [(x,y),...] → 连通分量大小列表（曼哈顿距离 ≤ 2 连通）

    注：单比特错误产生相邻稳定子激发对，稳定子坐标曼哈顿距离 = 2
    （第一版 min_pair_med=2.0 的观测证实），故邻域半径取 2。
    """
    if not ps:
        return []
    n = len(ps)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            if abs(ps[i][0] - ps[j][0]) + abs(ps[i][1] - ps[j][1]) <= 2:
                union(i, j)
    cnt = defaultdict(int)
    for i in range(n):
        cnt[find(i)] += 1
    return list(cnt.values())

def analyze_error_structure(res, L):
    """错误模式空间结构分析（几何论 A0/A1 视角）"""
    dets, coords = res["dets"], res["coords"]
    le = res["le"]
    n = len(dets)
    exc_counts = dets.sum(axis=1)
    # 码的全局边界（穿越判据用）
    gx = gy = 0
    if coords is not None:
        all_x = [c[0] for c in coords.values() if len(c) >= 3]
        all_y = [c[1] for c in coords.values() if len(c) >= 3]
        gx = max(all_x) if all_x else 0
        gy = max(all_y) if all_y else 0
    per_sample = []
    for s in range(n):
        exc_idx = np.where(dets[s])[0]
        base = dict(exc=int(exc_counts[s]), min_pair=None, n_layers=None,
                    diam=None, bdry=None, cluster=None, cross=None)
        if coords is None or len(exc_idx) == 0:
            per_sample.append(base)
            continue
        # 每激发点 (x, y, t)
        pts = []
        for d in exc_idx:
            c = coords.get(d)
            if c is None or len(c) < 3:
                continue
            pts.append((int(c[0]), int(c[1]), int(c[2])))
        if not pts:
            per_sample.append(base)
            continue
        # 按时间层分组
        layers = defaultdict(list)
        for x, y, t in pts:
            layers[t].append((x, y))
        # 最近激发对（同层内平面曼哈顿距离）
        min_pair = None
        diam = 0.0
        for t, ps in layers.items():
            for i in range(len(ps)):
                for j in range(i + 1, len(ps)):
                    dist = abs(ps[i][0] - ps[j][0]) + abs(ps[i][1] - ps[j][1])
                    if min_pair is None or dist < min_pair:
                        min_pair = dist
                    if dist > diam:
                        diam = dist
        # 边界距离（激发点到码边界的最小距离）
        max_x = max(p[0] for p in pts)
        max_y = max(p[1] for p in pts)
        bdry = min(min(x, max_x - x, y, max_y - y) for x, y, _ in pts)
        # 穿越判据（A1 拓扑本质：错误链同时接触相对边界）
        xs_all = [p[0] for p in pts]
        ys_all = [p[1] for p in pts]
        cross = int((min(xs_all) <= 0 and max(xs_all) >= gx) or
                    (min(ys_all) <= 0 and max(ys_all) >= gy))
        # 每层最大簇
        max_cluster = 0
        for t, ps in layers.items():
            sizes = cluster_sizes(ps)
            if sizes:
                max_cluster = max(max_cluster, max(sizes))
        per_sample.append(dict(exc=int(exc_counts[s]), min_pair=min_pair,
                               n_layers=len(layers), diam=diam, bdry=bdry,
                               cluster=max_cluster, cross=cross))
    # 汇总（按逻辑错误分组）
    grp_ok, grp_err = [], []
    for s in range(n):
        (grp_err if le[s] else grp_ok).append(per_sample[s])

    def summ(grp):
        if not grp:
            return {}
        f = {}
        for field in ("exc", "min_pair", "n_layers", "diam", "bdry", "cluster"):
            v = [g[field] for g in grp if g[field] is not None]
            f[field + "_med"] = float(np.median(v)) if v else None
            f[field + "_q90"] = float(np.percentile(v, 90)) if v else None
        cr = [g["cross"] for g in grp if g.get("cross") is not None]
        f["cross_rate"] = float(np.mean(cr)) if cr else None
        return dict(n=len(grp), **f)

    return dict(ok=summ(grp_ok), err=summ(grp_err))

def analyze_edges(res, matching):
    """MWPM 配对边纯链分析（decode_to_edges_array）

    decode_to_edges_array 返回配对节点对（无权重列）→ 用 detector 坐标
    计算每条配对边的空间距离作为链长代理。A1 逻辑链跨越整个码 →
    应有更长距离的配对边、更多边界连接（几何论 A1 = 非平凡拓扑链）。
    """
    dets, le, coords = res["dets"], res["le"], res["coords"]
    n = len(dets)
    nd = matching.num_detectors
    # 全局边界（边界距离用）
    gx = gy = 0
    if coords is not None:
        all_x = [c[0] for c in coords.values() if len(c) >= 3]
        all_y = [c[1] for c in coords.values() if len(c) >= 3]
        gx = max(all_x) if all_x else 0
        gy = max(all_y) if all_y else 0

    def edge_dist(e):
        a, b = int(e[0]), int(e[1])
        if a >= nd and b >= nd:
            return 0.0
        if a >= nd:  # 边界-探测器：探测器到最近边界的距离
            c = coords.get(b)
            if c is None or len(c) < 3:
                return 0.0
            return min(c[0], gx - c[0], c[1], gy - c[1])
        if b >= nd:
            c = coords.get(a)
            if c is None or len(c) < 3:
                return 0.0
            return min(c[0], gx - c[0], c[1], gy - c[1])
        ca, cb = coords.get(a), coords.get(b)
        if ca is None or cb is None or len(ca) < 3 or len(cb) < 3:
            return 0.0
        return abs(ca[0] - cb[0]) + abs(ca[1] - cb[1])  # 空间曼哈顿距离

    per = []
    t0 = time.time()
    for s in range(n):
        edges = matching.decode_to_edges_array(dets[s])
        if len(edges) == 0:
            per.append(dict(n_edges=0, bdry_edges=0, total_dist=0.0, max_dist=0.0,
                            long_straight=None, long_rate=0.0))
            continue
        bdry = int(np.sum((edges[:, 0] >= nd) | (edges[:, 1] >= nd)))
        dists = [edge_dist(e) for e in edges]
        mx = float(max(dists))
        # 最长内部 detector-detector 边的直度（A1 穿越链应更"直"）
        best = None
        best_dist = -1.0
        for e in edges:
            a, b = int(e[0]), int(e[1])
            if a >= nd or b >= nd:
                continue
            ca, cb = coords.get(a), coords.get(b)
            if ca is None or cb is None or len(ca) < 3 or len(cb) < 3:
                continue
            d = abs(ca[0] - cb[0]) + abs(ca[1] - cb[1])
            if d > best_dist:
                best_dist = d
                best = (d, abs(ca[0] - cb[0]), abs(ca[1] - cb[1]))
        straight = (max(best[1], best[2]) / best[0]) if best is not None and best[0] > 0 else None
        per.append(dict(n_edges=int(len(edges)), bdry_edges=bdry,
                        total_dist=float(sum(dists)), max_dist=mx,
                        long_straight=straight, long_rate=float(mx >= 4.0)))
        if s % 10000 == 0 and s > 0:
            print(f"  edges {s}/{n} ({time.time()-t0:.0f}s)", flush=True)
    grp_ok, grp_err = [], []
    for s in range(n):
        (grp_err if le[s] else grp_ok).append(per[s])

    def summ(grp):
        if not grp:
            return {}
        f = {}
        for field in ("n_edges", "bdry_edges", "total_dist", "max_dist", "long_rate"):
            v = [g[field] for g in grp]
            f[field + "_med"] = float(np.median(v))
            f[field + "_q90"] = float(np.percentile(v, 90))
        ls = [g["long_straight"] for g in grp if g["long_straight"] is not None]
        f["long_straight_med"] = float(np.median(ls)) if ls else None
        return dict(n=len(grp), **f)

    return dict(ok=summ(grp_ok), err=summ(grp_err))


# ---------- 3. 主流程 ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, default=4)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--noise", type=float, default=0.03)
    ap.add_argument("--shots", type=int, default=20000)
    ap.add_argument("--scan", action="store_true", help="扫描逻辑错误率 vs 噪声")
    args = ap.parse_args()

    if args.scan:
        print("=== 噪声扫描（L=%d, rounds=%d, shots=%d）===" % (args.L, args.rounds, args.shots))
        ps = [0.005, 0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15]
        table = []
        for p in ps:
            r = decode(args.L, args.rounds, p, args.shots)
            pL = r["le"].mean()
            table.append((p, pL, r["dt"]))
            print(f"  p={p:.3f}  pL={pL:.5f}  ({r['dt']:.1f}s)")
        print("\n结果表:")
        for p, pL, dt in table:
            print(f"  {p} {pL}")
        return

    r = decode(args.L, args.rounds, args.noise, args.shots)
    print("=== surface code 解码 ===")
    print(f"L={args.L}, rounds={args.rounds}, noise={args.noise}, shots={args.shots}")
    print(f"电路: {r['circuit'].num_qubits} qubits, {r['n_det']} detectors, 编译 {r['dt']:.1f}s")
    print(f"逻辑错误率 pL = {r['le'].mean():.5f} ({r['le'].sum()}/{args.shots})")

    print("\n=== 错误模式空间结构（几何论 A0/A1 视角）===")
    st = analyze_error_structure(r, args.L)
    print("特征              A0(可修正)      A1(逻辑错误)")
    print("                  med     q90     med     q90")
    for field in ("exc", "min_pair", "diam", "bdry", "cluster"):
        a0 = st["ok"].get(field + "_med"), st["ok"].get(field + "_q90")
        a1 = st["err"].get(field + "_med"), st["err"].get(field + "_q90")
        fmt = lambda v: "-" if v is None else f"{v:8.1f}"
        print(f"  {field:10s} {fmt(a0[0])} {fmt(a0[1])} {fmt(a1[0])} {fmt(a1[1])}")
    c0, c1 = st["ok"].get("cross_rate"), st["err"].get("cross_rate")
    fmtp = lambda v: "-" if v is None else f"{v * 100:7.1f}%"
    print(f"  {'cross':10s} {fmtp(c0):>8s} {'':>8s} {fmtp(c1):>8s} {'':>8s}")
    print(f"\n样本数: A0={st['ok']['n']}, A1={st['err']['n']}")

    print("\n=== MWPM 配对边（纯链）分析 ===")
    st2 = analyze_edges(r, r["matching"])
    print("特征              A0(可修正)      A1(逻辑错误)")
    print("                  med     q90     med     q90")
    for field in ("n_edges", "bdry_edges", "total_dist", "max_dist", "long_rate"):
        a0 = st2["ok"].get(field + "_med"), st2["ok"].get(field + "_q90")
        a1 = st2["err"].get(field + "_med"), st2["err"].get(field + "_q90")
        fmt = lambda v: "-" if v is None else f"{v:8.2f}"
        print(f"  {field:10s} {fmt(a0[0])} {fmt(a0[1])} {fmt(a1[0])} {fmt(a1[1])}")
    ls0, ls1 = st2["ok"].get("long_straight_med"), st2["err"].get("long_straight_med")
    fmts = lambda v: "-" if v is None else f"{v:8.2f}"
    print(f"  {'strght':10s} {fmts(ls0):>8s} {'':>8s} {fmts(ls1):>8s} {'':>8s}")
    print("判定（配对边特征，A1/A0 比值）：")
    for field in ("n_edges", "bdry_edges", "total_dist", "max_dist", "long_rate"):
        m0, m1 = st2["ok"].get(field + "_med"), st2["err"].get(field + "_med")
        if m0 is None or m1 is None:
            continue
        if m0 == 0 and m1 == 0:
            print(f"  {field:10s} 两者均为 0 → 无区分度")
            continue
        ratio = m1 / m0 if m0 > 0 else float("inf")
        arrow = "↑" if m1 > m0 else ("↓" if m1 < m0 else "=")
        print(f"  {field:10s} A1/A0 = {ratio:6.2f} {arrow}  "
              f"{'有区分度' if ratio > 1.5 or ratio < 0.67 else '无区分度'}")
    # 区分度判定
    print("\n判定（A1 vs A0 的 med 差异方向）：")
    for field in ("diam", "bdry", "cluster", "min_pair"):
        m0, m1 = st["ok"].get(field + "_med"), st["err"].get(field + "_med")
        if m0 is None or m1 is None:
            continue
        if m0 == 0 and m1 == 0:
            print(f"  {field:10s} 两者均为 0 → 无区分度")
            continue
        ratio = m1 / m0 if m0 > 0 else float("inf")
        arrow = "↑" if m1 > m0 else ("↓" if m1 < m0 else "=")
        print(f"  {field:10s} A1/A0 = {ratio:6.2f} {arrow}  "
              f"{'有区分度' if ratio > 1.5 or ratio < 0.67 else '无区分度'}")
    if c0 is not None and c1 is not None and c0 > 0:
        lift = c1 / c0
        print(f"  cross      A1/A0 穿越率 = {lift:6.2f}×  "
              f"{'★ A1 本质特征' if lift > 3 else '弱'}")
    print("\n注: A0=局域错误链（平凡拓扑）；A1=跨边界非平凡链（逻辑错误）")

if __name__ == "__main__":
    main()
