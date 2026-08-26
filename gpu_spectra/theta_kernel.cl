/* theta_kernel.cl — θ 级数精确计数（Leech C24'，逐坐标 DP，纯整数算术）
 * 项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
 * 里程碑 C：格不变量尺度——θ 级数/短向量计数为群尺度刚性的正确载体
 * 文章：10.75 三尺度统计刚性（260823）§4 群尺度；milestoneB 遗留"下一步候选"
 *
 * 目标格：√2·Λ₂₄ = C24' = { x ∈ Z^24 : x mod 2 ∈ G24, Σx ≡ 0 (mod 4) }
 *   （√2Λ₂₄ ⊂ Z^24，det = 2^24，最短范数² = 8，θ 级数 = E12(q⁴) − (65520/691)Δ(q⁴)）
 *
 * 分解：x = u + 2w，u ∈ G24（Golay 码，4096 个码字），w ∈ Z^24
 *   · x mod 2 = u（码字条件）✓
 *   · Σx ≡ 0 (mod 4) ⟺ Σw ≡ Σu/2 (mod 2)；G24 权重 ∈ {0,8,12,16,24} ⟹ Σu/2 全偶 ⟹ Σw 必偶
 *   · ‖x‖² = Σᵢ (uᵢ + 2wᵢ)²  ≤  R
 *
 * 逐坐标 DP（每 work-item = 一个码字，4096 个）：
 *   dp[s][p] = 组合数（范数² = s、Σw mod 2 = p），s ∈ [0, R]
 *   坐标 i：候选 w ∈ {−2..2} 满足 (uᵢ + 2w)² ≤ R，贡献 c = (uᵢ + 2w)²
 *   转移：dp[s][p] → dp[s+c][p ⊕ (w&1)]
 *   实现：s 降序原地更新（c > 0 时 ns > s，源 dp[s] 本轮未污染 ✓）
 * 输出：per_word[gid * nbins + (s−8)/4] = dp[s][0]（Σw 偶），s ∈ {8,12,...,R}
 *   （无原子操作：host 端归约；√2Λ 偶格 ⟹ 范数² ≡ 0 mod 4，最短 8）
 *
 * 精度：ulong（R=64 球内总数 ~3.15e15 < 2^63；单 bin 最大 ~1.67e15 < 2^63 ✓）
 */

#define MAXS 64

__kernel void theta_leech(
    __global const uint* codewords,   /* [4096] 24-bit Golay 码字 */
    const int R,                      /* 范数² 上限，8 ≤ R ≤ MAXS */
    __global ulong* per_word          /* [4096 * nbins]：行 = 码字，列 = s = 8,12,...,R */
) {
    const int gid = get_global_id(0);
    const uint u = codewords[gid];
    const int nbins = (R - 8) / 4 + 1;

    ulong dp0[MAXS + 1];   /* p = 0（Σw 偶） */
    ulong dp1[MAXS + 1];   /* p = 1（Σw 奇） */
    for (int s = 0; s <= R; s++) { dp0[s] = 0; dp1[s] = 0; }
    dp0[0] = 1;            /* w = 0 */

    for (int i = 0; i < 24; i++) {
        const int ui = (int)((u >> i) & 1u);
        /* s 降序：来自 s' < s 的转移尚未发生 ⟹ dp[s] 为本轮前值 ✓ */
        for (int s = R; s >= 0; s--) {
            const ulong v0 = dp0[s];
            const ulong v1 = dp1[s];
            if (v0 == 0 && v1 == 0) continue;
            for (int w = -2; w <= 2; w++) {
                const int c = (ui + 2 * w) * (ui + 2 * w);
                if (c == 0 || s + c > R) continue;   /* c=0 仅 (u=0,w=0)：自转移忽略 */
                const int ns = s + c;
                if (w & 1) { dp0[ns] += v1; dp1[ns] += v0; }
                else       { dp0[ns] += v0; dp1[ns] += v1; }
            }
        }
    }

    /* Σw 偶（p = 0）；√2Λ 偶格 ⟹ 范数² ≡ 0 (mod 4)，最短 8 */
    for (int s = 8; s <= R; s += 4) {
        per_word[gid * nbins + (s - 8) / 4] = dp0[s];
    }
}
