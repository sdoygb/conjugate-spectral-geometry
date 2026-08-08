# 横向门验证：[[16,6,4]] (m=4,r=1) 态向量 + [[64,20,8]] (m=6,r=2) 符号检查
import numpy as np, itertools

# ============ 工具 ============
def eval_poly(mon_tuple, pts):
    """单项式（变量索引元组）在 pts 上的评估"""
    if not mon_tuple:
        return np.ones(len(pts), dtype=np.uint8)
    return pts[:, list(mon_tuple)].prod(axis=1)

def gen_code(mons, pts):
    """生成码的全部码字（2^|mons| 个）"""
    n = len(pts)
    words = []
    for mask in range(1 << len(mons)):
        v = np.zeros(n, dtype=np.uint8)
        for j, mon in enumerate(mons):
            if mask >> j & 1:
                v ^= eval_poly(mon, pts)
        words.append(v)
    return words

def to_idx(v):
    return sum(int(b) << i for i, b in enumerate(v))

def apply_H_all(psi, n):
    psi = psi.copy().reshape([2] * n)
    H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    for i in range(n):
        psi = np.tensordot(H, psi, axes=(1, i))
        psi = np.moveaxis(psi, 0, i)
    return psi.reshape(-1)

def apply_S_all(psi):
    out = np.zeros_like(psi)
    nz = np.nonzero(psi)[0]
    for idx in nz:
        k = bin(int(idx)).count('1')
        out[idx] = psi[idx] * (1j ** k)
    return out

# ============ [[16,6,4]]: m=4, r=1 ============
print("=" * 60)
print("[[16,6,4]]: m=4, r=1, C2=RM(1,4), C1=C2⊥=RM(2,4)")
m = 4
pts = np.array(list(itertools.product([0, 1], repeat=m)), dtype=np.uint8)
mons1 = [c for s in range(2) for c in itertools.combinations(range(m), s)]   # deg<=1, 5 个
mons2 = [c for s in range(3) for c in itertools.combinations(range(m), s)]   # deg<=2, 11 个
C2 = gen_code(mons1, pts)   # 32 个码字
C1 = gen_code(mons2, pts)   # 2048 个码字

# |0_L> = Σ_{x∈C2}|x>/√|C2|
zeroL = np.zeros(1 << 16, dtype=complex)
for x in C2:
    zeroL[to_idx(x)] = 1.0
zeroL /= np.sqrt(len(C2))

# --- 横向 H：H⊗16|0_L> 应 = |+_L> = Σ_{y∈C1}|y>/√|C1| ---
H0L = apply_H_all(zeroL, 16)
exp_plus = np.zeros(1 << 16, dtype=complex)
for y in C1:
    exp_plus[to_idx(y)] = 1.0
exp_plus /= np.sqrt(len(C1))
print(f"横向H: |<+_L|H⊗16|0_L>| = {abs(np.vdot(exp_plus, H0L)):.12f}  (应=1)")

# --- 横向 S：S⊗16|0_L> = Σ i^{|x|}|x>，α = <0_L|S⊗16|0_L> ---
S0L = apply_S_all(zeroL)
alpha = np.vdot(zeroL, S0L)
print(f"横向S: α = <0_L|S⊗16|0_L> = {alpha:.6f}  (理论: C2权重≡0 mod4 时 =1)")

# C2 权重 mod 4 分布
wmod = {}
for x in C2:
    w = int(x.sum()) % 4
    wmod[w] = wmod.get(w, 0) + 1
print(f"C2=RM(1,4) 权重 mod4 分布: {wmod}  (全 ≡0 mod4: {set(wmod)=={0}})")

# 逻辑 X 支撑 a_j（C1\C2 的 6 个独立代表：二次单项式指示）
print("\n逻辑支撑 a ∈ RM(2,4)\\RM(1,4)，γ_j = <1_L^j|S⊗16|1_L^j>  vs 理论 i^{|a|}：")
for i, j in itertools.combinations(range(4), 2):
    a = eval_poly((i, j), pts)
    w = int(a.sum())
    oneL = np.zeros(1 << 16, dtype=complex)
    for x in C2:
        oneL[to_idx(x ^ a)] = 1.0
    oneL /= np.sqrt(len(C2))
    gam = np.vdot(oneL, apply_S_all(oneL))
    theo = 1j ** w
    match = "✓" if abs(gam - theo) < 1e-12 else "✗"
    tag = {0: "恒等", 1: "逻辑S", 2: "逻辑Z", 3: "-i·逻辑S"}[w % 4]
    print(f"  a=指示(x{i+1}x{j+1}): |a|={w} (mod4={w%4})  γ={gam:.6f} 理论={theo:.6f} {match}  → {tag}")

# ============ [[64,20,8]]: m=6, r=2 符号检查 ============
print("\n" + "=" * 60)
print("[[64,20,8]]: m=6, r=2, C2=RM(2,6)（22 基）")
m2 = 6
pts2 = np.array(list(itertools.product([0, 1], repeat=m2)), dtype=np.uint8)
mons2_6 = [c for s in range(3) for c in itertools.combinations(range(m2), s)]  # 22 个
basis = [eval_poly(mon, pts2) for mon in mons2_6]

# (a) 自正交：任意基向量 v·w = 0（16 位内积——64 位向量点积 mod 2）
viol = 0
for v in basis:
    for w in basis:
        if int((v & w).sum()) % 2 != 0:
            viol += 1
print(f"(a) 自正交 v·w=0 检查: 违规 {viol}/484  → {'✓' if viol==0 else '✗'}")

# (b) C2 基向量权重 ≡ 0 mod 4 + 随机组合
bad = [int(v.sum()) % 4 for v in basis if int(v.sum()) % 4 != 0]
rng = np.random.default_rng(7)
combo_bad = 0
for _ in range(2000):
    mask = rng.integers(0, 2, len(basis))
    v = np.zeros(64, dtype=np.uint8)
    for j, b in enumerate(basis):
        if mask[j]:
            v ^= b
    if int(v.sum()) % 4 != 0:
        combo_bad += 1
print(f"(b) C2 权重 ≡0 mod4: 基向量违规 {len(bad)}/22, 2000 随机组合违规 {combo_bad} → {'✓' if not bad and combo_bad==0 else '✗'}")

# (c) Y_v = X_v Z_v 与全部稳定子生成元对易（X_w、Z_w for w ∈ 基）
#     X_v 与 Z_w 反对易 ⟺ v·w=1；Y_v 与 X_w: v·w；Y_v 与 Z_w: v·w
viol2 = 0
for v in basis:
    for w in basis:
        if int((v & w).sum()) % 2 != 0:
            viol2 += 1
print(f"(c) Y_v 与稳定子对易（⟺ v·w=0 ∀w）: 违规 {viol2}/484 → {'✓' if viol2==0 else '✗'}")

# (d) 横向 CNOT 稳定子映射：X_v⊗I → X_v⊗X_v ∈ 稳定子群（两块的 X 稳定子乘积）
print("(d) 横向CNOT: X_v⊗X_v = (X_v⊗I)(I⊗X_v) ∈ 稳定子群（乘积闭包）→ 标准 CSS 事实 ✓（无需数值）")
print("\n全部验证完成。")
