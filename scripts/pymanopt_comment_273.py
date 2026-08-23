"""Post implementation-plan comment on pymanopt issue #273."""
import json
import os
import ssl
import urllib.request

TOKEN_PATH = os.path.expanduser("~/Downloads/GeometryAI-Mac-Build/.github_token")
TOKEN = open(TOKEN_PATH).read().strip()
CTX = ssl._create_unverified_context()

BODY = """I'd like to pick this up. Proposed implementation plan for a ``DoublyStochastic`` manifold.

**Geometry** (following Douik-Hassibi 2019, "Matrix Manifolds and the Birkhoff Polytope", and manopt's ``multinomialdoublystochasticfactory``):

- Base set: strictly positive doubly stochastic n x n matrices, dimension (n-1)^2
- Tangent space: { V : V 1 = 0, V^T 1 = 0 }
- Riemannian metric: <V, W>_X = tr(V^T W / X)  (entrywise division)
- Orthogonal projection: Pi(V) = V - (a 1^T + 1 b^T), with a = V 1 / n - (1^T V 1)/(2 n^2) 1 and b = V^T 1 / n - (1^T V 1)/(2 n^2) 1
- Exponential map / retraction: R_X(V) = Sinkhorn( X * exp(V / X) )  (closed-form, global)
- Riemannian gradient: grad f = X * Pi(grad f)
- Parallel transport: P_{X -> Y}(V) = Pi_Y( V * Y / X )

**Numerical safeguards** (drawn from prior experience implementing and stress-testing Sinkhorn-based Birkhoff retractions, cf. the geoopt BirkhoffPolytope boundary issues): bounded Sinkhorn iterations with tolerance, max_iter cap with convergence warnings, and guards for degenerate V / X near zero.

**Planned tests**: idempotent projection, doubly-stochasticity of retractions, first-order agreement of retraction with exp, transport isometry, random point/tangent sampling properties.

Two questions for maintainers:
1. Should ``log``/``dist`` raise NotImplementedError (no closed-form inverse is known), or is a numerical shooting-based ``log`` preferred?
2. Any preference on including a Sinkhorn-based ``pair_mean``?

I can open a PR once the implementation and tests are ready.
"""

req = urllib.request.Request(
    "https://api.github.com/repos/pymanopt/pymanopt/issues/273/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "sdoygb",
    },
    method="POST",
)
with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
    d = json.loads(r.read().decode())
print("comment id:", d.get("id"))
print("created:", d.get("created_at"))
print("url:", d.get("html_url"))
