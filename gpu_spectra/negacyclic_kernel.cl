/* negacyclic_kernel.cl — 批量 Λ_H（谱刚性比）计算：negacyclic 无调制格
 * 项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
 * 里程碑 1：零方差定律大规模验证（0.9 §4.3，定理 0.9.4.02/0.9.4.10）
 *
 * 理论输入（0.9，精确公式）：
 *   A = d×d 负循环矩阵，第一行系数 a[0..d-1] 独立均匀于对称盒 [-q/2, q/2]
 *   B0 = [[A, I], [0, qI]]（无调制变体，10.58 P2 实验对象）
 *   G = B0 B0^T = [[AA^T + I, qI], [qI, q^2 I]]   （2d × 2d）
 *   Λ_H = λ2 / λ1（特征值排序 λ1 ≤ λ2 ≤ ...，定义 0.9.4.01）
 *   断言：negacyclic + 无调制 ⟹ λ1(G) = λ2(G)，Λ_H ≡ 1（定理 0.9.4.02，确定性）
 *
 * 并行策略：1 work-group = 1 个格（编译时常数 NMAX = 2d_max）
 *   - work-item 0：PCG32 顺序生成 d 个系数（对称盒）
 *   - 全体 work-item：并行组装 G（2d×2d，local memory）
 *   - cyclic Jacobi（复制自 jacobi_kernel.cl v2.1，n = 2d）
 *   - work-item 0：提取两个最小特征值 → L1/L2 输出
 *
 * 限制：n = 2d ≤ NMAX = 48（Apple AMD 编译器 32KB local 数组触发 SC failed；24.5KB 安全），d ∈ {8,16,24}。
 * 精度：double（RX570 FP64 已实测可用）。
 */

#define NMAX 48

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

    __local double A[NMAX * NMAX];
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

    /* ---- 2. 并行组装 G = [[AA^T + I, qI], [qI, q^2 I]] ----
     * negacyclic A[i][k] = a[(k-i) mod d] * (k >= i ? +1 : -1)
     */
    for (int idx = lid; idx < n * n; idx += lsize) {
        const int i = idx / n;
        const int j = idx % n;
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
            val = (i - d == j) ? (double)q : 0.0;
        } else {
            val = (i == j) ? (double)(q * q) : 0.0;
        }
        A[i * n + j] = val;
    }
    barrier(CLK_LOCAL_MEM_FENCE);

    /* ---- 3. cyclic Jacobi sweeps（同 jacobi_kernel.cl v2.1） ---- */
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
                lskip = (fabs(A[p * n + qq]) < 1e-15) ? 1 : 0;
            }
            barrier(CLK_LOCAL_MEM_FENCE);
            if (lskip) continue;

            const int p = lp, q2 = lq;
            const double apq = A[p * n + q2];

            /* Givens 旋转参数 */
            double tau = (A[q2 * n + q2] - A[p * n + p]) / (2.0 * apq);
            double t = (tau >= 0.0 ? 1.0 : -1.0) / (fabs(tau) + sqrt(1.0 + tau * tau));
            double c = 1.0 / sqrt(1.0 + t * t);
            double s = t * c;

            /* 并行应用旋转：对 k != p,q 更新行/列（对称写两处） */
            for (int k = lid; k < n; k += lsize) {
                if (k == p || k == q2) continue;
                double akp = A[k * n + p];
                double akq = A[k * n + q2];
                A[k * n + p] = c * akp - s * akq;
                A[k * n + q2] = s * akp + c * akq;
                A[p * n + k] = A[k * n + p];
                A[q2 * n + k] = A[k * n + q2];
            }
            /* 对角更新 + 置零 A[p][q]（work-item 0，避免竞争） */
            if (lid == 0) {
                double app = A[p * n + p];
                double aqq = A[q2 * n + q2];
                A[p * n + p] = app - t * apq;
                A[q2 * n + q2] = aqq + t * apq;
                A[p * n + q2] = 0.0;
                A[q2 * n + p] = 0.0;
            }
            barrier(CLK_LOCAL_MEM_FENCE);
        }

        /* sweep 结束：offdiag 平方和 < 1e-24 提前退出 */
        if (lid == 0) {
            double s2 = 0.0;
            for (int r = 0; r < n; r++)
                for (int c = r + 1; c < n; c++)
                    s2 += A[r * n + c] * A[r * n + c];
            lconv = (s2 < 1e-24) ? 1 : 0;
        }
        barrier(CLK_LOCAL_MEM_FENCE);
        if (lconv) break;
    }

    /* ---- 4. 提取两个最小特征值（work-item 0 串行） ---- */
    if (lid == 0) {
        double m1 = 1e300, m2 = 1e300;
        for (int i = 0; i < n; i++) {
            double v = A[i * n + i];
            if (v < m1) { m2 = m1; m1 = v; }
            else if (v < m2) { m2 = v; }
        }
        L1_out[gid] = m1;
        L2_out[gid] = m2;
        double s2 = 0.0;
        for (int r = 0; r < n; r++)
            for (int c = r + 1; c < n; c++)
                s2 += A[r * n + c] * A[r * n + c];
        offdiag_out[gid] = s2;
    }
}
