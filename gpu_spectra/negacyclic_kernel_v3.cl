/* negacyclic_kernel_v3.cl — 批量 Λ_H：上三角打包存储版
 * 项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
 * 里程碑 2（v3 阶段 A）：突破 Apple OpenCL 32KB local mem 顶格
 *
 * v1 限制（negacyclic_kernel.cl）：全矩阵 __local double A[NMAX*NMAX]
 *   NMAX=48（n=48 → 48×48×8 = 18.4KB），GPU 直跑 d ≤ 24；d=32/48 只能 numpy 补充
 * v3 改进：只存上三角（含对角），打包索引 pk(i,j)=i·n − i(i+1)/2 + j（i ≤ j）
 *   → NMAX=80（n=80 → 80×81/2×8 = 25.9KB < 32KB），GPU 直跑 d ≤ 40
 *   → 对称写两处（(k,p) 与 (p,k)）合并为一处，写量减半、竞争更少
 *
 * 理论输入同 v1（0.9 定理 0.9.4.02/0.9.4.10，定义 0.9.4.01）：
 *   A = d×d negacyclic 矩阵，第一行系数 a[0..d-1] 独立均匀于对称盒 [-q/2, q/2]
 *   B0 = [[A, I], [0, qI]]（无调制变体），G = B0 B0^T = [[AA^T+I, qI], [qI, q^2I]]
 *   Λ_H = λ2/λ1（G 特征值升序），断言 negacyclic + 无调制 ⟹ λ1 = λ2，Λ_H ≡ 1
 *
 * 并行策略：1 work-group = 1 个格；PCG32 系数 → 并行组装 → cyclic Jacobi → λ1/λ2
 * 精度：double（RX570 FP64 实测可用）。
 */

#define NMAX 80   /* n_max = 2·d_max；打包 80×81/2×8B = 25.9KB（< 32KB 顶格） */

/* 打包索引：只存上三角 i≤j；i>j 时交换（对称元素同一位置） */
inline int pk(int i, int j, int n) {
    return (i <= j) ? (i * n - (i * (i + 1)) / 2 + j)
                    : (j * n - (j * (j + 1)) / 2 + i);
}

/* ---- PCG32：32 位随机数（OpenCL uint 自动 32 位回绕） ---- */
inline uint pcg32(uint *s) {
    uint state = *s;
    *s = state * 747796405u + 2891336453u;
    uint word = ((state >> ((state >> 28u) + 4u)) ^ state) * 277803737u;
    return (word >> 22u) ^ word;
}

__kernel void batch_lambdaH(
    __global const uint* seeds,    /* [N] 每格独立种子 */
    const int d,                   /* A 的维数（n = 2d ≤ NMAX） */
    const int q,                   /* 模数（0.9：3329） */
    __global double* L1_out,       /* [N] λ1 */
    __global double* L2_out,       /* [N] λ2 */
    __global double* offdiag_out   /* [N] 收敛质量（非对角平方和） */
) {
    const int gid = get_group_id(0);
    const int lid = get_local_id(0);
    const int lsize = get_local_size(0);
    const int n = 2 * d;
    const int npairs = n * (n - 1) / 2;

    __local double AP[NMAX * (NMAX + 1) / 2];   /* 上三角打包（含对角） */
    __local double acoef[NMAX / 2];
    __local int lp, lq, lskip, lconv;

    /* ---- 1. work-item 0：PCG32 顺序生成 d 个系数（对称盒 [-q/2, q/2]） ---- */
    if (lid == 0) {
        uint rng = seeds[gid];
        const int hq = q / 2;
        for (int k = 0; k < d; k++) {
            uint r = pcg32(&rng);
            int v = (int)(r % (uint)q) - hq;
            acoef[k] = (double)v;
        }
    }
    barrier(CLK_LOCAL_MEM_FENCE);

    /* ---- 2. 并行组装 G = [[AA^T + I, qI], [qI, q^2 I]]（只写上三角） ----
     * negacyclic A[i][k] = a[(k-i) mod d] * (k >= i ? +1 : -1)
     */
    for (int idx = lid; idx < n * n; idx += lsize) {
        const int i = idx / n;
        const int j = idx % n;
        if (i > j) continue;          /* 打包只存上三角 */
        double val;
        if (i < d && j < d) {
            double s = 0.0;
            for (int k = 0; k < d; k++) {
                const int ti = k - i;
                const int ai = (ti >= 0) ? ti : ti + d;
                const double vi = (ti >= 0 ? 1.0 : -1.0) * acoef[ai];
                const int tj = k - j;
                const int aj = (tj >= 0) ? tj : tj + d;
                const double vj = (tj >= 0 ? 1.0 : -1.0) * acoef[aj];
                s += vi * vj;
            }
            val = s + (i == j ? 1.0 : 0.0);
        } else if (i < d && j >= d) {
            val = (i == j - d) ? (double)q : 0.0;
        } else if (i >= d && j < d) {
            val = (i - d == j) ? (double)q : 0.0;   /* 仅 i<j 时可达（i≥d, j<d 恒 i>j，跳过） */
        } else {
            val = (i == j) ? (double)(q * q) : 0.0;
        }
        AP[pk(i, j, n)] = val;
    }
    barrier(CLK_LOCAL_MEM_FENCE);

    /* ---- 3. cyclic Jacobi sweeps（同 v1，读写走打包索引） ---- */
    for (int sw = 0; sw < 24; sw++) {

        for (int pair = 0; pair < npairs; pair++) {

            /* work-item 0：pair 序号 -> 上三角坐标 (p,q) */
            if (lid == 0) {
                int p = 0, qq = 1, cum = 0;
                for (int r = 0; r < n - 1; r++) {
                    int cnt = n - 1 - r;
                    if (pair < cum + cnt) { p = r; qq = p + 1 + (pair - cum); break; }
                    cum += cnt;
                }
                lp = p; lq = qq;
                lskip = (fabs(AP[pk(p, qq, n)]) < 1e-15) ? 1 : 0;
            }
            barrier(CLK_LOCAL_MEM_FENCE);
            if (lskip) continue;

            const int p = lp, q2 = lq;
            const double apq = AP[pk(p, q2, n)];   /* p < q2 恒成立 */

            /* Givens 旋转参数 */
            double tau = (AP[pk(q2, q2, n)] - AP[pk(p, p, n)]) / (2.0 * apq);
            double t = (tau >= 0.0 ? 1.0 : -1.0) / (fabs(tau) + sqrt(1.0 + tau * tau));
            double c = 1.0 / sqrt(1.0 + t * t);
            double s = t * c;

            /* 并行应用旋转：对 k != p,q 更新（打包后 (k,p) 与 (p,k) 同一位置，写一次） */
            for (int k = lid; k < n; k += lsize) {
                if (k == p || k == q2) continue;
                const int kp = pk(k, p, n);
                const int kq = pk(k, q2, n);
                double akp = AP[kp];
                double akq = AP[kq];
                AP[kp] = c * akp - s * akq;
                AP[kq] = s * akp + c * akq;
            }
            /* 对角更新 + 置零 A[p][q]（work-item 0，避免竞争） */
            if (lid == 0) {
                const int pp = pk(p, p, n);
                const int qq2 = pk(q2, q2, n);
                double app = AP[pp];
                double aqq = AP[qq2];
                AP[pp] = app - t * apq;
                AP[qq2] = aqq + t * apq;
                AP[pk(p, q2, n)] = 0.0;
            }
            barrier(CLK_LOCAL_MEM_FENCE);
        }

        /* sweep 结束：offdiag 平方和 < 1e-24 提前退出（上三角） */
        if (lid == 0) {
            double s2 = 0.0;
            for (int r = 0; r < n; r++)
                for (int c = r + 1; c < n; c++)
                    s2 += AP[pk(r, c, n)] * AP[pk(r, c, n)];
            lconv = (s2 < 1e-24) ? 1 : 0;
        }
        barrier(CLK_LOCAL_MEM_FENCE);
        if (lconv) break;
    }

    /* ---- 4. 提取两个最小特征值（work-item 0 串行） ---- */
    if (lid == 0) {
        double m1 = 1e300, m2 = 1e300;
        for (int i = 0; i < n; i++) {
            double v = AP[pk(i, i, n)];
            if (v < m1) { m2 = m1; m1 = v; }
            else if (v < m2) { m2 = v; }
        }
        L1_out[gid] = m1;
        L2_out[gid] = m2;
        double s2 = 0.0;
        for (int r = 0; r < n; r++)
            for (int c = r + 1; c < n; c++)
                s2 += AP[pk(r, c, n)] * AP[pk(r, c, n)];
        offdiag_out[gid] = s2;
    }
}
