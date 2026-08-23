#!/usr/bin/env python3
"""Apply the three Birkhoff fixes to geoopt and append regression tests."""
import pathlib

base = pathlib.Path('/Users/oygb/Downloads/GeometryAI-Mac-Build/geoopt')
manifold = base / 'geoopt/manifolds/birkhoff_polytope.py'
tests = base / 'tests/test_birkhoff.py'

src = manifold.read_text()

# --- Fix 1: non-negativity check ---
old1 = """        col_ok = torch.allclose(
            col_sum, col_sum.new((1,)).fill_(1), atol=atol, rtol=rtol
        )
        if row_ok and col_ok:"""
new1 = """        col_ok = torch.allclose(
            col_sum, col_sum.new((1,)).fill_(1), atol=atol, rtol=rtol
        )
        nonneg_ok = bool((x >= -atol).all())
        if row_ok and col_ok and nonneg_ok:"""
assert src.count(old1) == 1, 'fix1 anchor not unique: %d' % src.count(old1)
src = src.replace(old1, new1)

# --- Fix 2: retr NaN at vertices ---
old2 = """    def retr(self, x, u):
        k = u / x
        y = x * torch.exp(k)
        y = self.projx(y)
        y = torch.max(y, y.new(1).fill_(1e-12))
        return y"""
new2 = """    def retr(self, x, u):
        eps = 1e-12
        k = u / torch.clamp(x, min=eps)
        k = torch.clamp(k, max=50.0)
        y = torch.where(x > eps, x * torch.exp(k), torch.clamp(x + u, min=0.0))
        y = self.projx(y)
        y = torch.max(y, y.new(1).fill_(eps))
        return y"""
assert src.count(old2) == 1, 'fix2 anchor not unique: %d' % src.count(old2)
src = src.replace(old2, new2)

# --- Fix 3: align function-level default eps with the class default ---
old3 = "    x, max_iter: int = 300, eps: float = 1e-5, tol: float = 1e-5"
new3 = "    x, max_iter: int = 300, eps: float = 1e-12, tol: float = 1e-5"
assert src.count(old3) == 1, 'fix3 anchor not unique: %d' % src.count(old3)
src = src.replace(old3, new3)

manifold.write_text(src)
print('manifold patched')

# --- regression tests ---
test_append = '''

def test_check_point_rejects_negative_entries():
    birkhoff = geoopt.manifolds.BirkhoffPolytope()
    x_bad = torch.tensor(
        [[2.0, -1.0, 0.0], [-1.0, 2.0, 0.0], [0.0, 0.0, 1.0]]
    )
    ok, _ = birkhoff._check_point_on_manifold(x_bad)
    assert not ok
    # a genuine doubly stochastic matrix still passes
    ok, _ = birkhoff._check_point_on_manifold(torch.eye(3))
    assert ok


def test_retr_at_vertex_permutation_matrix():
    birkhoff = geoopt.manifolds.BirkhoffPolytope()
    P = torch.eye(3)
    torch.manual_seed(0)
    u = torch.randn(3, 3)
    u = u - u.mean(dim=0, keepdim=True)
    u = u - u.mean(dim=1, keepdim=True)
    ok, reason = birkhoff._check_vector_on_tangent(P, u)
    assert ok, reason
    y = birkhoff.retr(P, u)
    assert torch.isfinite(y).all()
    assert (y >= 0).all()
    np.testing.assert_allclose(
        y.sum(dim=-1), torch.ones(3), atol=1e-5, rtol=1e-5
    )
    np.testing.assert_allclose(
        y.sum(dim=-2), torch.ones(3), atol=1e-5, rtol=1e-5
    )


def test_proj_doubly_stochastic_default_eps_accuracy():
    torch.manual_seed(1)
    x = torch.rand(4, 4)
    y = geoopt.manifolds.birkhoff_polytope.proj_doubly_stochastic(x)
    np.testing.assert_allclose(
        y.sum(dim=-1), torch.ones(4), atol=1e-5, rtol=1e-5
    )
    np.testing.assert_allclose(
        y.sum(dim=-2), torch.ones(4), atol=1e-5, rtol=1e-5
    )
'''

t = tests.read_text()
if 'test_check_point_rejects_negative_entries' not in t:
    t += test_append
    tests.write_text(t)
    print('tests appended')
else:
    print('tests already present')
