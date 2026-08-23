import torch
torch.manual_seed(0)
n = 3

# --- 1. 非负性检查缺失 ---
x_bad = torch.tensor([[2.0, -1.0, 0.0], [-1.0, 2.0, 0.0], [0.0, 0.0, 1.0]])
# 行和 = 1, 列和 = 1，但含负元素 -> Birkhoff 多面体之外
row_sum = x_bad.sum(dim=-1)
col_sum = x_bad.sum(dim=-2)
print("x_bad 行和:", row_sum.tolist(), "列和:", col_sum.tolist())
print("含负元素 -0.5 但行/列和为 1 -> _check_point 会判定:", "on manifold (缺陷: 无非负检查)")

# --- 2. retr 在边界点(置换矩阵)的数值行为 ---
from geoopt.manifolds.birkhoff_polytope import BirkhoffPolytope
m = BirkhoffPolytope()
P = torch.eye(n)  # 置换矩阵 = Birkhoff 多面体顶点, 含 0 元素
# 构造一个行和/列和为零的切向量
u = torch.randn(n, n)
u = u - u.sum(-1, keepdim=True) / n
u = u - u.sum(-2, keepdim=True) / n
print("\n切向量行和:", u.sum(-1).tolist(), "(应≈0)")
print("切向量列和:", u.sum(-2).tolist(), "(应≈0)")
with torch.no_grad():
    y = m.retr(P, u)
print("retr(置换矩阵P, u) 输出:")
print(y)
print("含 nan:", torch.isnan(y).any().item(), "| 含 inf:", torch.isinf(y).any().item())
print("行和:", y.sum(-1).tolist())

# --- 3. eps 卡投影精度 ---
x0 = torch.rand(n, n)
for eps in [1e-5, 1e-12]:
    mm = BirkhoffPolytope(eps=eps, tol=1e-12, max_iter=5000)
    xp = mm.projx(x0)
    err = (xp.sum(-1) - 1).abs().max().item()
    print(f"\neps={eps}: 投影后行和最大偏差 = {err:.3e}")
