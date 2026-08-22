/* jacobi_kernel.cl — 批量 Jacobi 特征值分解（实对称矩阵）v2.1：cyclic Jacobi
 * 项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
 *
 * 并行策略：1 work-group = 1 个矩阵（编译时常数 MAT_N）
 *   - work-item 0：计算本轮要旋转的对 (p,q)（cyclic 顺序）+ Givens 参数
 *   - 全体 work-item：并行应用旋转（每 work-item 处理不相交的列集合 k）
 *   - 每 sweep = 完整遍历 N(N-1)/2 个上三角对（经典 Jacobi 二次收敛）
 * 收敛：max_sweeps 轮 + 每轮结束 offdiag 平方和 < 1e-24 提前退出
 * 输出：特征值（对角元）+ 非对角平方和（宿主判断收敛质量）
 *
 * v2.1：去掉 red[256] 归约数组，offdiag 统计改为 work-item 0 串行——
 *       使 local mem 仅含 A[MAT_N*MAT_N]，支持 MAT_N=64（64x64x8=32KB 顶格）。
 *
 * 精度：double（RX570 FP64 已实测可用）。
 * 矩阵实对称（0.9 负循环格 Gram = B B^T 即此结构）。
 */

__kernel void batch_jacobi(
    __global const double* A_in,     /* [mats][MAT_N][MAT_N] row-major */
    __global double* eig_out,        /* [mats][MAT_N] 特征值 */
    __global double* offdiag_out,    /* [mats] 非对角平方和 */
    const int mats,
    const int max_sweeps
) {
    const int gid = get_group_id(0);
    const int lid = get_local_id(0);
    const int lsize = get_local_size(0);
    const int npairs = MAT_N * (MAT_N - 1) / 2;

    __local double A[MAT_N * MAT_N];
    __local int lp, lq, lskip, lconv;

    /* ---- 加载矩阵到 local memory ---- */
    const __global double* base = A_in + (size_t)gid * MAT_N * MAT_N;
    for (int i = lid; i < MAT_N * MAT_N; i += lsize)
        A[i] = base[i];
    barrier(CLK_LOCAL_MEM_FENCE);

    /* ---- cyclic Jacobi sweeps ---- */
    for (int sw = 0; sw < max_sweeps; sw++) {

        for (int pair = 0; pair < npairs; pair++) {

            /* work-item 0：pair 序号 -> 上三角坐标 (p,q) */
            if (lid == 0) {
                int p = 0, q = 1, cum = 0;
                for (int r = 0; r < MAT_N - 1; r++) {
                    int cnt = MAT_N - 1 - r;
                    if (pair < cum + cnt) { p = r; q = p + 1 + (pair - cum); break; }
                    cum += cnt;
                }
                lp = p; lq = q;
                lskip = (fabs(A[p * MAT_N + q]) < 1e-15) ? 1 : 0;
            }
            barrier(CLK_LOCAL_MEM_FENCE);
            if (lskip) continue;   /* 全体一致跳过已零元素 */

            const int p = lp, q = lq;
            const double apq = A[p * MAT_N + q];

            /* Givens 旋转参数：tau -> t -> c,s （经典 Jacobi 公式） */
            double tau = (A[q * MAT_N + q] - A[p * MAT_N + p]) / (2.0 * apq);
            double t = (tau >= 0.0 ? 1.0 : -1.0) / (fabs(tau) + sqrt(1.0 + tau * tau));
            double c = 1.0 / sqrt(1.0 + t * t);
            double s = t * c;

            /* 并行应用旋转：对 k != p,q 更新行/列（对称写两处） */
            for (int k = lid; k < MAT_N; k += lsize) {
                if (k == p || k == q) continue;
                double akp = A[k * MAT_N + p];   /* = A[p][k] 对称 */
                double akq = A[k * MAT_N + q];   /* = A[q][k] */
                A[k * MAT_N + p] = c * akp - s * akq;
                A[k * MAT_N + q] = s * akp + c * akq;
                A[p * MAT_N + k] = A[k * MAT_N + p];
                A[q * MAT_N + k] = A[k * MAT_N + q];
            }
            /* 对角更新 + 置零 A[p][q]（work-item 0，避免竞争） */
            if (lid == 0) {
                double app = A[p * MAT_N + p];
                double aqq = A[q * MAT_N + q];
                A[p * MAT_N + p] = app - t * apq;
                A[q * MAT_N + q] = aqq + t * apq;
                A[p * MAT_N + q] = 0.0;
                A[q * MAT_N + p] = 0.0;
            }
            barrier(CLK_LOCAL_MEM_FENCE);
        }

        /* sweep 结束：work-item 0 检查 offdiag 平方和，决定是否提前退出 */
        if (lid == 0) {
            double s2 = 0.0;
            for (int r = 0; r < MAT_N; r++)
                for (int c = r + 1; c < MAT_N; c++)
                    s2 += A[r * MAT_N + c] * A[r * MAT_N + c];
            lconv = (s2 < 1e-24) ? 1 : 0;
        }
        barrier(CLK_LOCAL_MEM_FENCE);
        if (lconv) break;
    }

    /* ---- 输出：特征值 + 非对角平方和（work-item 0 串行，省 local mem） ---- */
    for (int i = lid; i < MAT_N; i += lsize)
        eig_out[gid * MAT_N + i] = A[i * MAT_N + i];

    if (lid == 0) {
        double s2 = 0.0;
        for (int r = 0; r < MAT_N; r++)
            for (int c = r + 1; c < MAT_N; c++)
                s2 += A[r * MAT_N + c] * A[r * MAT_N + c];
        offdiag_out[gid] = s2;
    }
}
