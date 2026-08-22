/* lattice_kernel.cl — 里程碑1：negacyclic/随机格 Gram 谱 Λ_H 批量 GPU 计算
 * 项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
 * 文章 0.9（260821）定理 0.9.4.01/0.9.4.02/0.9.4.10/0.9.4.11
 *
 * 编译：-DLAT_D=16 或 -DLAT_D=32（格维数，编译期常量）
 * 每个 work-group = 1 个格样本；WG size = n = 2*LAT_D
 * LDS 预算（RX570 驱动限制 32KB！）：
 *   G 上三角压缩 (2d)(2d+1)/2 doubles + A d² ints
 *   d=32 → 64*65/2*8=16.6KB + 4KB = 20.6KB < 32KB ✓
 *
 * G 上三角压缩索引：TRI(i,j) = i*n - i(i-1)/2 + (j-i)，仅 i<=j 有效
 * seeds 布局：每样本 seed_stride 个 int32
 *   mode 0/1（negacyclic）：stride=d，取前 d 个作第一行
 *   mode 2（一般随机）：stride=d*d，取全部作矩阵
 *
 * 流程：seeds → A(d×d) → G=BB^T(2d×2d) → cyclic Jacobi → min2 特征值
 * mode 0 = negacyclic 无调制  B=[[A,I],[0,qI]]   G=[[AA^T+I, qI],[qI, q²I]]
 * mode 1 = negacyclic 有调制  B=[[A,I],[qI,0]]   G=[[AA^T+I, qA],[qA^T, q²I]]
 * mode 2 = 一般随机（非 negacyclic，无调制）——归因修正对照组
 */
#pragma OPENCL EXTENSION cl_khr_fp64 : enable

#ifndef LAT_D
#define LAT_D 32
#endif
#define LAT_N (2 * LAT_D)
#define TRI(i, j) ((i) * LAT_N - ((i) * ((i) - 1)) / 2 + ((j) - (i)))
#define NTRI (LAT_N * (LAT_N + 1) / 2)

__kernel void lattice_lambdaH(
    __global const int* seeds,      /* [N*seed_stride] int32 ∈ [0,q-1] */
    const int seed_stride,
    const double qd,                /* (double)q */
    const int mode,                 /* 0=neg无调制 1=neg有调制 2=随机 */
    __global double* out_min1,      /* [N] */
    __global double* out_min2,      /* [N] */
    const int max_sweeps)
{
    const int n = LAT_N;
    const int d = LAT_D;
    const int gid = get_group_id(0);
    const int lid = get_local_id(0);
    const int lsz = get_local_size(0);     /* = n */
    const int npairs = n * (n - 1) / 2;

    __local double G[NTRI];
    __local int A[LAT_D * LAT_D];
    __local int lp, lq, lskip, lconv;

    const __global int* a = seeds + gid * seed_stride;

    /* ---- 0. 清零 G ---- */
    for (int idx = lid; idx < NTRI; idx += lsz)
        G[idx] = 0.0;

    /* ---- 1. 构造 A ---- */
    if (mode == 2) {
        for (int idx = lid; idx < d * d; idx += lsz)
            A[idx] = a[idx];
    } else {
        for (int idx = lid; idx < d * d; idx += lsz) {
            int j = idx / d, k = idx % d;
            int kk = (k - j + d) % d;
            A[idx] = (k >= j) ? a[kk] : -a[kk];
        }
    }
    barrier(CLK_LOCAL_MEM_FENCE);

    /* ---- 2. 组装 G = BB^T 上三角（i<=j 才计算） ---- */
    for (int idx = lid; idx < n * n; idx += lsz) {
        int i = idx / n, j = idx % n;
        if (i > j) continue;
        double val;
        if (i < d && j < d) {
            double s = 0.0;
            for (int k = 0; k < d; k++)
                s += (double)A[i * d + k] * (double)A[j * d + k];
            val = s + ((i == j) ? 1.0 : 0.0);
        } else if (i < d && j >= d) {
            int jj = j - d;
            val = (mode == 1) ? (double)A[i * d + jj] * qd   /* qA 块 */
                              : ((i == jj) ? qd : 0.0);       /* qI 块 */
        } else if (i >= d && j < d) {
            int ii = i - d;
            val = (mode == 1) ? (double)A[j * d + ii] * qd   /* qA^T 块 */
                              : ((ii == j) ? qd : 0.0);       /* qI 块 */
        } else {
            val = (i == j) ? qd * qd : 0.0;                   /* q²I 块 */
        }
        G[TRI(i, j)] = val;
    }
    barrier(CLK_LOCAL_MEM_FENCE);

    /* ---- 3. cyclic Jacobi（上三角压缩，三区更新） ---- */
    for (int sw = 0; sw < max_sweeps; sw++) {
        for (int pair = 0; pair < npairs; pair++) {
            if (lid == 0) {
                int p = 0, q = 1, cum = 0;
                for (int r = 0; r < n - 1; r++) {
                    int cnt = n - 1 - r;
                    if (pair < cum + cnt) { p = r; q = p + 1 + (pair - cum); break; }
                    cum += cnt;
                }
                lp = p; lq = q;
                lskip = (fabs(G[TRI(p, q)]) < 1e-15) ? 1 : 0;
            }
            barrier(CLK_LOCAL_MEM_FENCE);
            if (lskip) continue;

            const int p = lp, q = lq;
            const double apq = G[TRI(p, q)];
            double tau = (G[TRI(q, q)] - G[TRI(p, p)]) / (2.0 * apq);
            double t = (tau >= 0.0 ? 1.0 : -1.0) / (fabs(tau) + sqrt(1.0 + tau * tau));
            double c = 1.0 / sqrt(1.0 + t * t);
            double s = t * c;

            /* 三区更新（全部落在上三角）：
             * k < p:      (k,p) (k,q)
             * p < k < q:  (p,k) (k,q)
             * k > q:      (p,k) (q,k) */
            for (int k = lid; k < n; k += lsz) {
                if (k == p || k == q) continue;
                double akp, akq;
                if (k < p) {
                    akp = G[TRI(k, p)];
                    akq = G[TRI(k, q)];
                    G[TRI(k, p)] = c * akp - s * akq;
                    G[TRI(k, q)] = s * akp + c * akq;
                } else if (k < q) {
                    akp = G[TRI(p, k)];
                    akq = G[TRI(k, q)];
                    G[TRI(p, k)] = c * akp - s * akq;
                    G[TRI(k, q)] = s * akp + c * akq;
                } else {
                    akp = G[TRI(p, k)];
                    akq = G[TRI(q, k)];
                    G[TRI(p, k)] = c * akp - s * akq;
                    G[TRI(q, k)] = s * akp + c * akq;
                }
            }
            if (lid == 0) {
                double app = G[TRI(p, p)];
                double aqq = G[TRI(q, q)];
                G[TRI(p, p)] = app - t * apq;
                G[TRI(q, q)] = aqq + t * apq;
                G[TRI(p, q)] = 0.0;
            }
            barrier(CLK_LOCAL_MEM_FENCE);
        }
        /* sweep 结束：上三角 offdiag² 和 < 1e-22 提前退出 */
        if (lid == 0) {
            double s2 = 0.0;
            for (int r = 0; r < n; r++)
                for (int c = r + 1; c < n; c++)
                    s2 += G[TRI(r, c)] * G[TRI(r, c)];
            lconv = (s2 < 1e-22) ? 1 : 0;
        }
        barrier(CLK_LOCAL_MEM_FENCE);
        if (lconv) break;
    }

    /* ---- 4. 最小两个特征值（对角元未排序 → 单 work-item 扫描） ---- */
    if (lid == 0) {
        double m1 = G[TRI(0, 0)];
        double m2 = G[TRI(1, 1)];
        if (m1 > m2) { double t = m1; m1 = m2; m2 = t; }
        for (int i = 2; i < n; i++) {
            double v = G[TRI(i, i)];
            if (v < m1) { m2 = m1; m1 = v; }
            else if (v < m2) { m2 = v; }
        }
        out_min1[gid] = m1;
        out_min2[gid] = m2;
    }
}
