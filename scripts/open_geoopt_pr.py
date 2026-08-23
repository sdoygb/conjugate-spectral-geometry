import urllib.request, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
tok = open("/Users/oygb/Downloads/GeometryAI-Mac-Build/.github_token").read().strip()

body = """Closes #249.

## Summary

Three fixes that harden `BirkhoffPolytope` at and near boundary points. All three are reproducible on master; evidence and minimal reproducers are in #249.

## Changes

### 1. `_check_point_on_manifold` rejects negative entries

A doubly stochastic matrix is nonnegative with unit row/column sums. Previously only the sums were checked, so e.g. `[[2,-1,0],[-1,2,0],[0,0,1]]` was accepted as a point on the manifold.

### 2. `retr` no longer produces NaN at vertices

At a permutation matrix (the central use case of Birdal et al. 2019, permutation synchronization), `k = u / x` divides by zero and the output is all-NaN for any nontrivial tangent vector. Fix:

- divide by `torch.clamp(x, min=1e-12)` and clamp `k` to 50 (guards `exp` overflow);
- entries with `x <= 1e-12` take a first-order step `clamp(x + u, min=0)` instead of the multiplicative update (which has 0 as an absorbing state), floored at `1e-3`;
- when the input point has (near-)zero entries, project with `max_iter=500` instead of the class default 100.

The larger budget is needed because Sinkhorn–Knopp converges only linearly on near-singular supports: at a permutation matrix, 100 iterations leave row-sum residuals of 1.5e-3, while 300 iterations reach 9.8e-6 (measured, see #249). Interior points keep the fast path unchanged.

### 3. `proj_doubly_stochastic`: eps default and convergence criterion

- `eps` default `1e-5` -> `1e-12`, matching the `BirkhoffPolytope.__init__` default. With `1e-5` the row/column sums of the projection carry a systematic ~2e-5 error; with `1e-12` it drops to ~1.2e-7.
- The loop now converges on the primal residuals `|col_sum - 1|`, `|row_sum - 1|` of the projected output instead of the dual criterion `|cinv * c - 1|`. On inputs with (near-)zero entries the dual criterion breaks early while the primal error is still ~2e-3.

## Tests

Three new cases in `tests/test_birkhoff.py`:

- negative-entry matrix is rejected, `I_3` still accepted;
- `retr` at a permutation matrix: finite, nonnegative, doubly stochastic within 1e-4 (measured worst case 9.8e-6);
- default-eps projection of a random 4x4 matrix is doubly stochastic within 1e-5.

`tests/test_birkhoff.py`: 4 passed (incl. the existing Adam/permutation-sync test)."""

data = json.dumps({
    "title": "fix: harden BirkhoffPolytope at boundary points",
    "head": "sdoygb:master",
    "base": "master",
    "body": body,
}).encode()

req = urllib.request.Request(
    "https://api.github.com/repos/geoopt/geoopt/pulls",
    data=data,
    headers={
        "Authorization": "token " + tok,
        "User-Agent": "sdoygb",
        "Content-Type": "application/json",
    },
    method="POST",
)
r = urllib.request.urlopen(req, context=ctx)
d = json.loads(r.read())
print("PR ->", r.status, d.get("number"), d.get("html_url"))
