import sys
sys.path.insert(0, "/Users/oygb/Downloads/GeometryAI-Mac-Build/geoopt")
import torch
import geoopt
from geoopt.manifolds.birkhoff_polytope import proj_doubly_stochastic

torch.manual_seed(0)
P = torch.eye(3)
u = torch.randn(3, 3)
u = u - u.mean(dim=0, keepdim=True)
u = u - u.mean(dim=1, keepdim=True)

# reproduce retr's pre-projection output (current fixed version)
eps = 1e-12
k = u / torch.clamp(P, min=eps)
k = torch.clamp(k, max=50.0)
yraw = torch.where(P > eps, P * torch.exp(k), torch.clamp(P + u, min=0.0))
print("yraw =")
print(yraw.numpy())
print("yraw row sums:", yraw.sum(dim=-1).numpy(), " col sums:", yraw.sum(dim=-2).numpy())

print()
print(f"{'floor':>8} {'max_iter':>8} {'row_err':>10} {'col_err':>10} {'min_y':>10}")
for floor in [0.0, 1e-8, 1e-6, 1e-4, 1e-3, 3e-3, 1e-2, 3e-2]:
    yin = torch.max(yraw, torch.tensor(floor))
    for max_iter in [300, 3000]:
        y = proj_doubly_stochastic(yin, max_iter=max_iter, eps=1e-12, tol=1e-5)
        rerr = (y.sum(dim=-1) - 1).abs().max().item()
        cerr = (y.sum(dim=-2) - 1).abs().max().item()
        print(f"{floor:>8.0e} {max_iter:>8} {rerr:>10.3e} {cerr:>10.3e} {y.min().item():>10.3e}")
