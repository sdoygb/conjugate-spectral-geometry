"""Construction utilities for Reed-Muller codes and CSS affine-complete codes.

CSS(RM(r,m), RM(r,m)): X-type stabilizers are taken from RM(r,m) and Z-type
stabilizers from its dual RM(m-r-1,m). Under the self-orthogonality condition
2r < m-1 this yields a [[2^m, 2^m - 2*dim, 2^(r+1)]] quantum code.

The distance formula d = 2^(r+1) rests on two classical results (the skeleton
of the certificate verifier):
  * RM minimum-weight theorem: the minimum weight of RM(t,m) is 2^(m-t)
    (MacWilliams-Sloane, Ch. 13; combinatorial Schwartz-Zippel type argument).
  * Duality theorem: RM(r,m)^perp = RM(m-r-1,m).

All generator-matrix rows / vectors are Python big integers used as bit
masks: bit v corresponds to the point v of AG(m,2) (coordinates given by the
binary expansion of v), so a vector occupies 2^m bits.
"""
from __future__ import annotations

import itertools
import math

import numpy as np

__all__ = [
    "rm_dim",
    "rm_rows",
    "parity_big",
    "ag_flat_count",
    "css_params",
    "build_cols",
    "FAMILY_EXAMPLES",
]


def rm_dim(r: int, m: int) -> int:
    """Dimension of RM(r,m) = sum_{i=0..r} C(m,i)."""
    return sum(math.comb(m, i) for i in range(r + 1))


def rm_rows(r: int, m: int) -> list[int]:
    """Generator matrix of RM(r,m): evaluations of all monomials of degree
    <= r on AG(m,2).

    Each row is a 2^m-bit big integer; the number of rows is rm_dim(r,m).
    """
    n = 2 ** m
    rows = []
    for deg in range(r + 1):
        for S in itertools.combinations(range(m), deg):
            row = 0
            for v in range(n):
                if all((v >> i) & 1 for i in S):
                    row |= 1 << v
            rows.append(row)
    return rows


def parity_big(x: int, nbits: int) -> int:
    """Parity (0/1) of the number of 1 bits in the low nbits bits of integer x."""
    s = 1
    while s < nbits:
        x ^= x >> s
        s *= 2
    return x & 1


def ag_flat_count(m: int, k: int) -> int:
    """Number of k-flats (k-dimensional affine subspaces) of AG(m,2)
    = 2^(m-k) * [m;k]_2 (Gaussian binomial)."""
    num = den = 1
    for i in range(k):
        num *= (2 ** m - 2 ** i)
        den *= (2 ** k - 2 ** i)
    return 2 ** (m - k) * (num // den)


def css_params(r: int, m: int) -> tuple[int, int, int]:
    """Parameters [[n, k, d]] of CSS(RM(r,m), RM(r,m)) (under
    self-orthogonality 2r < m-1)."""
    n = 2 ** m
    rc = rm_dim(r, m)
    k = n - 2 * rc
    d = 2 ** (r + 1)
    return n, k, d


def build_cols(r: int, m: int) -> tuple[np.ndarray, int]:
    """Columns of the parity-check matrix: column a = values of the RM basis
    rows at point a (syndrome labels for X errors).

    Column width = rm_dim(r,m) bits. Returns an int64 array (vectorized path)
    when width <= 63, otherwise an object array (big-integer path).
    Returns (cols, width).
    """
    rows = rm_rows(r, m)
    n = 2 ** m
    cols = []
    for a in range(n):
        col = 0
        for i, row in enumerate(rows):
            if (row >> a) & 1:
                col |= 1 << i
        cols.append(col)
    width = len(rows)
    if width <= 63:
        return np.array(cols, dtype=np.int64), width
    return np.array(cols, dtype=object), width


# Verified family members (CSS(RM(r,m), RM(r,m)), 2r < m-1)
FAMILY_EXAMPLES: list[tuple[int, int]] = [
    (1, 5), (1, 6), (2, 6), (2, 7), (3, 8), (3, 9), (4, 10),
]
