#!/usr/bin/env python3
"""Upgrade proj_doubly_stochastic: primal-feasibility convergence criterion."""
import pathlib

manifold = pathlib.Path('/Users/oygb/Downloads/GeometryAI-Mac-Build/geoopt/geoopt/manifolds/birkhoff_polytope.py')
src = manifold.read_text()

old = '''@torch.jit.script
def proj_doubly_stochastic(
    x, max_iter: int = 300, eps: float = 1e-12, tol: float = 1e-5
):
    it_num = 0
    c = 1.0 / (x.sum(dim=-2, keepdim=True) + eps)
    r = 1.0 / ((x @ c.transpose(-1, -2)) + eps)
    while it_num < max_iter:
        it_num += 1
        cinv = torch.matmul(r.transpose(-1, -2), x)
        if torch.max(torch.abs(cinv * c - 1)) <= tol:
            break
        c = 1.0 / (cinv + eps)
        r = 1.0 / ((x @ c.transpose(-1, -2)) + eps)
    return x * (r @ c)'''

new = '''@torch.jit.script
def proj_doubly_stochastic(
    x, max_iter: int = 300, eps: float = 1e-12, tol: float = 1e-5
):
    it_num = 0
    c = 1.0 / (x.sum(dim=-2, keepdim=True) + eps)
    r = 1.0 / ((x @ c.transpose(-1, -2)) + eps)
    y = x * (r @ c)
    while it_num < max_iter:
        if torch.max(
            torch.abs(y.sum(dim=-2, keepdim=True) - 1)
        ) <= tol and torch.max(torch.abs(y.sum(dim=-1, keepdim=True) - 1)) <= tol:
            break
        it_num += 1
        cinv = torch.matmul(r.transpose(-1, -2), x)
        c = 1.0 / (cinv + eps)
        r = 1.0 / ((x @ c.transpose(-1, -2)) + eps)
        y = x * (r @ c)
    return y'''

assert src.count(old) == 1, 'anchor count: %d' % src.count(old)
src = src.replace(old, new)
manifold.write_text(src)
print('proj_doubly_stochastic upgraded')
