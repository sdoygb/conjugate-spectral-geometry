"""Geometric certificate verifier: locks the distance d = 2^(r+1) of
CSS(RM(r,m)) without enumeration.

Positioning (distance-certifying, as opposed to distance-finding):
    when the distance is a theorem, stop computing it — verify it.
    The brute-force path enumerates the error space sum_{w<d} C(n,w)
    (exponential); this module's certificate path costs O(n^2) (polynomial)
    and produces a machine-checkable certificate.

The three certificate steps (matching Thm. 10.30.2.01 and the RM
minimum-weight theorem):

  (1) Column distinctness (executed, O(n))
      The syndrome of an X-type weight-2 error {a,b} is cols[a] ^ cols[b],
      so column distinctness <=> all weight-2 errors are detected (the
      structural criterion of Thm. 10.30.2.01).
      A full weight-2 column-pair XOR is additionally performed as a
      machine-level cross-check (O(n^2) column pairs, not an error
      enumeration).

  (2) Lower bound d >= 2^(r+1) (theorem + sampling corroboration)
      RM minimum-weight theorem: the minimum weight of C⊥ = RM(m-r-1,m) is
      2^(r+1), and the minimum weight of C = RM(r,m) is 2^(m-r) > 2^(r+1)
      (self-orthogonality 2r < m-1).
      X errors are undetectable <=> e ∈ C; logically trivial <=> e ∈ C⊥;
      hence logical X errors are C \\ C⊥ with minimum weight 2^(r+1);
      Z-side symmetric.
      Corroboration: random sampling over weights 3..d-1 is fully detected
      (executed).

  (3) Upper bound d <= 2^(r+1) (certificate w_F, all checks executed on the
      machine)
      Take the affine (r+1)-flat F = {v : the first m-r-1 coordinates of v
      are 0}; its indicator vector w_F has weight exactly 2^(r+1).
      Verify w_F ∈ C⊥: w_F is orthogonal to all basis rows of C (executed).
      Verify w_F ∉ C: take g = prod_{i=m-r-1}^{m-1} x_i (degree r+1 <=
      m-r-1), whose evaluation vector lies in a basis of C⊥, and
      w_F · eval_g = 1 (executed).
      w_F ∈ C⊥ \\ C with |w_F| = 2^(r+1) => a logical X operator of weight d
      exists.

Together (2)(3): d = 2^(r+1).
"""
from __future__ import annotations

import random
import time
from dataclasses import asdict, dataclass

from .rm_codes import build_cols, css_params, parity_big, rm_rows

__all__ = ["DistanceCertificate", "certify"]


@dataclass
class DistanceCertificate:
    """Distance certificate of CSS(RM(r,m)): the result of every machine
    check."""

    r: int
    m: int
    n: int
    k: int
    d: int
    cols_distinct: bool      # (1) column distinctness (=> all weight-2 errors detected)
    w2_undetected: int       # (1') weight-2 column-pair XOR zero count (machine cross-check)
    sample_miss: int         # (2') undetected count in the weight 3..d-1 sampling corroboration
    wF_in_Cperp: bool        # (3) w_F orthogonal to all basis rows (∈ C⊥)
    wF_not_in_C: bool        # (3) w_F · eval_g = 1 (∉ C)
    wF_weight: int           # (3) |w_F| = 2^(r+1)
    elapsed: float = 0.0     # verification time (seconds)

    @property
    def valid(self) -> bool:
        """Certificate fully valid: all machine checks pass, locking
        d = 2^(r+1)."""
        return (
            self.cols_distinct
            and self.w2_undetected == 0
            and self.sample_miss == 0
            and self.wF_in_Cperp
            and self.wF_not_in_C
            and self.wF_weight == self.d
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        status = "VALID" if self.valid else "INVALID"
        return (
            f"[[{self.n},{self.k},{self.d}]] certificate {status} "
            f"(cols_distinct={self.cols_distinct}, w2_undetected={self.w2_undetected}, "
            f"sample_miss={self.sample_miss}, wF_in_Cperp={self.wF_in_Cperp}, "
            f"wF_not_in_C={self.wF_not_in_C}, |wF|={self.wF_weight}) "
            f"in {self.elapsed:.4f}s"
        )


def certify(
    r: int,
    m: int,
    n_samples: int = 3000,
    seed: int = 260807,
    do_w2_full: bool = True,
) -> DistanceCertificate:
    """Verify the distance of CSS(RM(r,m)) and return a machine-checkable
    certificate.

    Parameters
    ----------
    r, m : RM order and number of variables (must satisfy
           self-orthogonality 2r < m-1).
    n_samples : number of samples in the weight 3..d-1 corroboration.
    seed : random seed for the sampling (reproducibility).
    do_w2_full : whether to run the full weight-2 column-pair XOR (O(n^2),
                 a machine-level cross-check). Column distinctness is already
                 logically equivalent to full weight-2 detection; this switch
                 only controls the redundant check.

    Returns
    -------
    DistanceCertificate : valid=True iff all checks pass, locking
                          d = 2^(r+1).
    """
    t0 = time.time()
    n, k, d = css_params(r, m)
    rows = rm_rows(r, m)
    cols, _ = build_cols(r, m)

    # (1) column distinctness
    cols_distinct = len(set(int(c) for c in cols)) == n

    # (1') full weight-2 column-pair XOR (machine cross-check)
    w2_undetected = 0
    if do_w2_full:
        clist = [int(c) for c in cols]
        for a in range(n):
            ca = clist[a]
            for b in range(a + 1, n):
                if ca ^ clist[b] == 0:
                    w2_undetected += 1

    # (2') weight 3..d-1 sampling corroboration
    rng = random.Random(seed)
    clist = [int(c) for c in cols]
    sample_miss = 0
    for _ in range(n_samples):
        w = rng.randint(3, d - 1)
        pos = rng.sample(range(n), w)
        sx = 0
        for p in pos:
            sx ^= clist[p]
        if sx == 0:
            sample_miss += 1

    # (3) certificate w_F: indicator vector of an affine (r+1)-flat, in C⊥ \\ C
    free_bits = list(range(m - r - 1, m))
    wF = 0
    for mask in range(2 ** (r + 1)):
        v = 0
        for j, b in enumerate(free_bits):
            if (mask >> j) & 1:
                v |= 1 << b
        wF |= 1 << v
    wF_in_Cperp = all(parity_big(wF & row, n) == 0 for row in rows)

    g_eval = 0
    for v in range(n):
        if all((v >> b) & 1 for b in free_bits):
            g_eval |= 1 << v
    wF_not_in_C = parity_big(wF & g_eval, n) == 1
    wF_weight = bin(wF).count("1")

    cert = DistanceCertificate(
        r=r,
        m=m,
        n=n,
        k=k,
        d=d,
        cols_distinct=cols_distinct,
        w2_undetected=w2_undetected,
        sample_miss=sample_miss,
        wF_in_Cperp=wF_in_Cperp,
        wF_not_in_C=wF_not_in_C,
        wF_weight=wF_weight,
        elapsed=time.time() - t0,
    )
    return cert
