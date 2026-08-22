/* gram_kernel.cl — 格 Gram 矩阵批量生成（negacyclic / 一般随机）
 * 项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
 * 里程碑 1：零方差定律大规模验证（定理 0.9.4.02/0.9.4.10/0.9.4.11）
 *
 * 结构（0.9 §4.1 定义 0.9.4.01 + 定理 0.9.4.02）：
 *   A: d x d 负循环矩阵（第一行系数 a_0..a_{d-1} 均匀于 Z_q）
 *      A[i][j] = a[(j-i) mod d] * (j < i ? -1 : 1)
 *   B = [[A, I_d], [0, q I_d]]（无调制变体）
 *   G = B B^T = [[AA^T + I_d, q I_d], [q I_d, q^2 I_d]]   (2d x 2d)
 *   定理 0.9.4.02：negacyclic 结构 ⟹ λ_1(G) = λ_2(G) ⟹ Λ_H ≡ 1（零方差，确定性）
 *
 * mode 运行时参数（不用编译时宏——避免编译器缓存歧义）：
 *   mode=0: negacyclic（定理断言 Λ_H ≡ 1）
 *   mode=1: 一般随机（A 元素独立均匀 Z_q；对照：Λ_H 波动 ≠ 1）
 * 并行策略：1 work-group = 1 个格。G 输出到 global（batch 循环复用，避开 PCIe 瓶颈）
 */

#define NEG_D 16
#define QMOD 3329

/* xorshift64star PRNG */
ulong xs64(ulong *s) {
    ulong x = *s;
    x ^= x >> 12; x ^= x << 25; x ^= x >> 27;
    *s = x;
    return x * 0x2545F4914F6CDD1DUL;
}

/* gid -> 独立种子（splitmix64 哈希） */
ulong hash_seed(int gid) {
    ulong h = 0x9E3779B97F4A7C15UL ^ (ulong)(gid + 1);
    h ^= h >> 30; h *= 0xBF58476D1CE4E5B9UL;
    h ^= h >> 27; h *= 0x94D049BB133111EBUL;
    h ^= h >> 31;
    return h;
}

__kernel void gen_gram(
    __global double* G_out,   /* [mats][2d][2d] row-major，READ_WRITE 复用 */
    const int mats,
    const int mode             /* 0=negacyclic, 1=general-random */
) {
    const int gid = get_group_id(0);
    const int lid = get_local_id(0);
    const int lsize = get_local_size(0);
    const int d = NEG_D;
    const int n = 2 * d;

    __local double A[NEG_D * NEG_D];
    __local ulong lseed;

    if (lid == 0) lseed = hash_seed(gid) ^ 0xA5A5A5A5UL;
    barrier(CLK_LOCAL_MEM_FENCE);
    ulong st = lseed ^ (ulong)(lid + 1) * 0x9E3779B97F4A7C15UL;

    if (mode == 1) {
        /* 一般随机对照：A 元素独立均匀 Z_q */
        for (int idx = lid; idx < d * d; idx += lsize) {
            ulong x = st ^ (ulong)(idx + 1) * 0xBF58476D1CE4E5B9UL;
            x = xs64(&x);
            A[idx] = (double)(long)(x % (ulong)QMOD);
        }
    } else {
        /* negacyclic：先并行生成第一行系数 a_0..a_{d-1} */
        if (lid < d) {
            ulong x = st ^ 0xDEADBEEFUL;
            x = xs64(&x);
            A[lid] = (double)(long)(x % (ulong)QMOD);
        }
        barrier(CLK_LOCAL_MEM_FENCE);
        /* 铺开 A[i][j] = a[(j-i)%d] * (j<i ? -1 : 1)（负循环移位保范数） */
        for (int idx = lid; idx < d * d; idx += lsize) {
            int i = idx / d, j = idx % d;
            int k = (j - i + d) % d;
            double a = A[k];
            A[i * d + j] = (j < i) ? -a : a;
        }
    }
    barrier(CLK_LOCAL_MEM_FENCE);

    /* 组装 G = [[AA^T + I, qI], [qI, q^2 I]]（2d x 2d） */
    for (int idx = lid; idx < n * n; idx += lsize) {
        int I = idx / n, J = idx % n;
        double v;
        if (I < d && J < d) {
            double s = 0.0;
            for (int k = 0; k < d; k++)
                s += A[I * d + k] * A[J * d + k];
            v = s + (I == J ? 1.0 : 0.0);
        } else if (I < d && J >= d) {
            v = (J == I + d) ? (double)QMOD : 0.0;
        } else if (I >= d && J < d) {
            v = (I == J + d) ? (double)QMOD : 0.0;
        } else {
            v = (I == J) ? (double)((ulong)QMOD * (ulong)QMOD) : 0.0;
        }
        G_out[(size_t)gid * (size_t)n * (size_t)n + idx] = v;
    }
}
