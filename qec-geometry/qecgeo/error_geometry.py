"""error_geometry.py —— 解码错误模式的几何分类（A0/A1，10.54）

几何论视角：
  - A0 类（局域错误）：激发局域、可修正 → 平凡拓扑（Berry 相位 0）
  - A1 类（逻辑错误）：错误链跨边界非平凡 → 整体拓扑（Berry 相位 2π）

特征提取（对每个采样错误模式）：
  激发层特征：exc（激发数）/ min_pair（最近激发对距离）/ n_layers（时间层数）
              / diam（空间直径）/ bdry（边界距离）/ cluster（最大簇大小）
              / cross（穿越判据：错误链同时接触相对边界 → A1 本质特征）
  配对边特征（MWPM）：n_edges / bdry_edges / total_dist / max_dist
              / long_straight（最长内部边直度）/ long_rate

已知结果（10.54，surface code L=4）：配对层 total_dist A1/A0 ≈ 3.00×，
cross 穿越率 A1 远高于 A0 —— 配对层是 A0/A1 分类的最强区分层。

依赖：stim + pymatching（可选，仅 surface code 演示需要）。
"""
import numpy as np
from collections import defaultdict

# ---------- 1. 电路生成 + 解码 ----------

def build_surface_circuit(L, rounds, noise):
    """surface code 电路（stim 内置生成器），噪声 = 统一 depolarizing/翻转率"""
    import stim
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


def decode_surface(L, rounds, noise, shots):
    """surface code 解码全流程：电路 → DEM → 采样 → MWPM 解码 → 逻辑错误标记

    返回 dict：circuit/dets/obs/preds/le/coords/matching/n_det/dt
    """
    import pymatching
    import time
    t0 = time.time()
    circuit = build_surface_circuit(L, rounds, noise)
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

def _cluster_sizes(ps):
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


def _global_extent(coords):
    """码的全局边界（穿越判据用）：(gx, gy) 或 (0, 0)"""
    if coords is None:
        return 0, 0
    all_x = [c[0] for c in coords.values() if len(c) >= 3]
    all_y = [c[1] for c in coords.values() if len(c) >= 3]
    return (max(all_x) if all_x else 0, max(all_y) if all_y else 0)


def analyze_error_structure(dets, coords, le):
    """错误模式空间结构分析（几何论 A0/A1 视角）

    返回 dict(ok=汇总A0, err=汇总A1)，每侧含 med/q90 统计 + cross_rate
    """
    n = len(dets)
    exc_counts = dets.sum(axis=1)
    gx, gy = _global_extent(coords)
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
            sizes = _cluster_sizes(ps)
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


def analyze_edges(dets, matching, coords, le):
    """MWPM 配对边纯链分析（A1 非平凡拓扑链应在配对层显现）

    decode_to_edges_array 返回配对节点对（无权重列）→ 用 detector 坐标
    计算每条配对边的空间距离作为链长代理。A1 逻辑链跨越整个码 →
    应有更长距离的配对边、更多边界连接。
    """
    n = len(dets)
    nd = matching.num_detectors
    gx, gy = _global_extent(coords)

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


def _ratio_line(field, ok, err, threshold=1.5):
    """A1/A0 比值判定（有区分度阈值 1.5 / 0.67）"""
    m0, m1 = ok.get(field + "_med"), err.get(field + "_med")
    if m0 is None or m1 is None:
        return None
    if m0 == 0 and m1 == 0:
        return dict(field=field, ratio=None, direction="=", verdict="无区分度（均为 0）")
    ratio = m1 / m0 if m0 > 0 else float("inf")
    arrow = "↑" if m1 > m0 else ("↓" if m1 < m0 else "=")
    verdict = "有区分度" if ratio > threshold or ratio < 1 / threshold else "无区分度"
    return dict(field=field, ratio=float(ratio), direction=arrow, verdict=verdict)


def run_error_geometry(L=4, rounds=3, noise=0.03, shots=20000, with_edges=True):
    """一键入口：surface code 错误模式几何分析（10.54 复现）

    返回 dict：pL, structure(A0/A1 激发层特征), edges(配对边特征),
               ratios(区分度判定), cross_lift(穿越率提升)
    """
    res = decode_surface(L, rounds, noise, shots)
    st = analyze_error_structure(res["dets"], res["coords"], res["le"])
    out = dict(pL=float(res["le"].mean()), structure=st, edges=None,
               ratios=[], cross_lift=None, n_det=res["n_det"],
               n_qubits=res["circuit"].num_qubits)
    # 穿越率提升（A1 本质特征）
    c0 = st["ok"].get("cross_rate")
    c1 = st["err"].get("cross_rate")
    if c0 is not None and c1 is not None and c0 > 0:
        out["cross_lift"] = float(c1 / c0)
    # 激发层区分度
    for field in ("exc", "min_pair", "n_layers", "diam", "bdry", "cluster"):
        r = _ratio_line(field, st["ok"], st["err"])
        if r is not None:
            out["ratios"].append(r)
    if with_edges:
        st2 = analyze_edges(res["dets"], res["matching"], res["coords"], res["le"])
        out["edges"] = st2
        for field in ("n_edges", "bdry_edges", "total_dist", "max_dist", "long_rate"):
            r = _ratio_line(field, st2["ok"], st2["err"])
            if r is not None:
                out["ratios"].append(r)
        # 配对层直度
        ls0, ls1 = st2["ok"].get("long_straight_med"), st2["err"].get("long_straight_med")
        if ls0 is not None and ls1 is not None and ls0 > 0:
            out["ratios"].append(dict(field="long_straight",
                                      ratio=float(ls1 / ls0),
                                      direction="↑" if ls1 > ls0 else "↓",
                                      verdict="有区分度" if ls1 / ls0 > 1.5 or ls1 / ls0 < 0.67 else "无区分度"))
    return out
