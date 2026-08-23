/* negacyclic_kernel_v4.cl — 批量 Λ_H：global 矩阵 + 行缓存 blocked 版
 * 项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
 * 里程碑 2（v4 阶段 B）：突破 local 顶格，GPU 直跑 d=48/64（及更大）
 *
 * v1（negacyclic_kernel.cl）  ：全矩阵 __local，NMAX=48（18.4KB）→ d≤24
 * v3a（negacyclic_kernel_v3.cl）：上三角打包 __local，NMAX=80（25.9KB）→ d≤40
 * v4 本文件：矩阵驻留 __global（每格 n×n 连续），解除 32KB local 顶格
 *   → NMAX=256（n=256 → d=128）
 *   → 每对旋转只把涉及的行 p、q 缓存到 __local（行缓存，2·n·8B），
 *     更新走 global 对称写（写两处：上三角 + 下三角）
 *
 * 理论输入同 v1（0.9 定理 0.9.4.02/0.9.4.10，定义 0.9.4.01）：
 *   A = d×d negacyclic 矩阵，第一行系数 a[0..d-1] 独立均匀于对称盒 [-q/2, q/2]
 *   B0 = [[A, I], [0, qI]]（无调制变体），G = B0 B0^T = [[AA^T+I, qI], [qI, q^2I]]
 *   Λ_H = λ2/λ1（G 特征值升序），断言 negacyclic + 无调制 ⟹ λ1 = λ2，Λ_H ≡ 1
 *
 * 并行策略：1 work-group = 1 个格；PCG32 系数 → 并行组装 → cyclic Jacobi
 *   （每对 (p,q)：行缓存 + 并行旋转应用）→ λ1/λ2
 * 精度：double（RX570 FP64 实测可用）。
 */

#define NMAX 256   /* n_max = 2·d_max；矩阵驻留 global（每格 n×n） */

/* ---- PCG32：32 位随机数（OpenCL uint 自动 32 位回绕） ---- */
inline uint pcg32(uint *s) {
    uint state = *s;
    *s = state * 747796405u + 2891336453u;
    uint word = ((state >> ((state >> 28u) + 4u)) ^ state) * 277803737u;
    return (word >> 22u) ^ word;
}

__kernel void batch_lambdaH_v4(
    __global const uint* seeds,    /* [N] 每格独立种子 */
    const int d,                   /* A 的维数（n = 2d ≤ NMAX） */
    const int q,                   /* 模数（0.9：3329） */
    const int g0,                  /* 本 chunk 起始格索引（分批运行） */
    __global double* A_work,       /* [m * n * n] 本 chunk 每格全矩阵工作区 */
    __global double* L1_out,       /* [N] λ1（写 g0+gid） */
    __global double* L2_out,       /* [N] λ2 */
    __global double* offdiag_out   /* [N] 收敛质量（非对角平方和） */
) {
    const int gid = get_group_id(0);   /* chunk 内 0..m-1 */
    const int gabs = g0 + gid;         /* 全局格索引（seeds / 输出） */
    const int lid = get_local_id(0);
    const int lsize = get_local_size(0);
    const int n = 2 * d;
    const int npairs = n * (n - 1) / 2;
    const int base = gid * n * n;
    __global double* A = A_work + base;

    __local double acoef[NMAX / 2];   /* negacyclic 第一行系数 */
    __local double rowp[NMAX];        /* 行缓存 p（当前旋转对） */
    __local double rowq[NMAX];        /* 行缓存 q */
    __local int lp, lq, lskip, lconv;

    /* ---- 1. work-item 0：PCG32 顺序生成 d 个系数（对称盒 [-q/2, q/2]） ---- */
    if (lid == 0) {
        uint rng = seeds[gabs];
        const int hq = q / 2;
        for (int k = 0; k < d; k++) {
            uint r = pcg32(&rng);
            int v = (int)(r % (uint)q) - hq;
            acoef[k] = (double)v;
        }
    }
    barrier(CLK_LOCAL_MEM_FENCE);

    /* ---- 2. 并行组装 G = [[AA^T + I, qI], [qI, q^2 I]]（全矩阵，对称两处） ----
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
        A[j * n + i] = val;   /* 对称写（同值，无竞争：不同 idx 对应不同地址） */
    }
    barrier(CLK_LOCAL_MEM_FENCE);

    /* ---- 3. cyclic Jacobi sweeps（行缓存版） ---- */
    for (int sw = 0; sw < 30; sw++) {

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
            const double apq = A[p * n + q2];   /* 旋转前读取（对称位置已置零则跳过） */

            /* Givens 旋转参数 */
            double tau = (A[q2 * n + q2] - A[p * n + p]) / (2.0 * apq);
            double t = (tau >= 0.0 ? 1.0 : -1.0) / (fabs(tau) + sqrt(1.0 + tau * tau));
            double c = 1.0 / sqrt(1.0 + t * t);
            double s = t * c;

            /* 行缓存：把行 p、行 q 拷到 local（旋转应用的只读基） */
            for (int k = lid; k < n; k += lsize) {
                rowp[k] = A[p * n + k];
                rowq[k] = A[q2 * n + k];
            }
            barrier(CLK_LOCAL_MEM_FENCE);

            /* 并行应用旋转：对 k != p,q 更新（对称两处写回） */
            for (int k = lid; k < n; k += lsize) {
                if (k == p || k == q2) continue;
                const double akp = rowp[k];
                const double akq = rowq[k];
                const double nkp = c * akp - s * akq;
                const double nkq = s * akp + c * akq;
                A[k * n + p] = nkp;  A[p * n + k] = nkp;
                A[k * n + q2] = nkq; A[q2 * n + k] = nkq;
            }
            /* 对角更新 + 置零 A[p][q]、A[q][p]（work-item 0） */
            if (lid == 0) {
                const double app = rowp[p];
                const double aqq = rowq[q2];
                A[p * n + p] = app - t * apq;
                A[q2 * n + q2] = aqq + t * apq;
                A[p * n + q2] = 0.0;
                A[q2 * n + p] = 0.0;
            }
            barrier(CLK_LOCAL_MEM_FENCE);
        }

        /* sweep 结束：offdiag 平方和 < 1e-24 提前退出（work-item 0 串行） */
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
        L1_out[gabs] = m1;
        L2_out[gabs] = m2;
        double s2 = 0.0;
        for (int r = 0; r < n; r++)
            for (int c = r + 1; c < n; c++)
                s2 += A[r * n + c] * A[r * n + c];
        offdiag_out[gabs] = s2;
    }
}
