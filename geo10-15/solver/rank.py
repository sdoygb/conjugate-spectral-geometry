"""Combinatorial rank tables for the S_z sector (bitstring <-> lexicographic
rank), the index layer that makes dim ~1e15 sectors addressable without an
O(2^n_orb) lookup table.

Combined sector index (10.87 §4 / wci.py):
    idx = rank_alpha(az) * dim_beta + rank_beta(bz)
where az/bz are n_orb-bit occupancy bitstrings of the alpha/beta spaces.

The full O(2^n_orb) table (np.full(1 << n_orb)) is impossible at n_orb=38
(2^38 * 8 B = 2.2 TB).  We instead compute the rank on the fly from the
combinatorial number system (lexicographic order matching
itertools.combinations):
    rank = sum_i [ C(n - c_{i-1} - 1, k - i) - C(n - c_i, k - i) ]
with c_i the ascending bit positions of the occupied orbitals, c_{-1} = -1.
Cost: O(n_occ * n) vectorised over numpy arrays — no huge table.

This module is a fresh, self-contained implementation for geo10-15
(the examples/ version was a scratch copy; here it is the project's index
layer, with unrank added).
"""
from math import comb
import numpy as np
from itertools import combinations


class RankTable:
    """bitstring -> lexicographic rank (and rank -> bitstring), on the fly.

    Parameters
    ----------
    n_orb : int — number of spatial orbitals in this spin space
    n_occ : int — number of occupied orbitals (electrons of this spin)
    """

    def __init__(self, n_orb, n_occ):
        if n_occ < 0 or n_occ > n_orb:
            raise ValueError(f"n_occ={n_occ} outside [0, n_orb={n_orb}]")
        self.n_orb = int(n_orb)
        self.n_occ = int(n_occ)
        self.dim = comb(self.n_orb, self.n_occ)
        # Pascal triangle up to n_orb+1 x n_occ+1 (int64 exact for our sizes)
        ct = np.zeros((self.n_orb + 2, self.n_occ + 2), dtype=np.int64)
        for n in range(self.n_orb + 2):
            for k in range(min(n, self.n_occ + 1) + 1):
                ct[n, k] = comb(n, k)
        self.comb_table = ct

    # ------------------------------------------------------------------ rank
    def rank(self, bitstrings):
        """Lexicographic rank of occupancy bitstring(s) — FULLY VECTORISED
        (no per-element Python loop; the geoqc large-system version).

        Occupied positions are the set bits (bit j = 1 means orbital j
        occupied), matching itertools.combinations over range(n_orb)
        enumerated by `sum(1 << j for j in c)`.

        Inputs with the wrong popcount get sentinel -1 (table semantics).
        """
        key = np.asarray(bitstrings, dtype=np.int64)
        scalar = key.ndim == 0
        if scalar:
            key = key.reshape(1)
        n = len(key)
        n_orb, n_occ, ct = self.n_orb, self.n_occ, self.comb_table

        # occupied positions: sort orbitals by (occupancy, orbital index);
        # occupied (1) sort after unoccupied (0); take first n_occ after
        # argsort of ~bits puts unoccupied first, so take LAST n_occ for
        # correctness on any popcount, then sort ascending.
        bits = ((key[:, None] >> np.arange(n_orb, dtype=np.int64)) & 1)
        # positions of occupied orbitals, ascending
        occ = np.argsort(bits, axis=1, kind="stable")[:, -n_occ:]
        positions = np.sort(occ, axis=1).T  # (n_occ, n)

        ranks = np.zeros(n, dtype=np.int64)
        prev_pos = np.full(n, -1, dtype=np.int64)  # c_{-1} = -1
        for i in range(n_occ):
            c_i = positions[i]
            t1_n = np.clip(n_orb - prev_pos - 1, 0, n_orb + 1)
            t2_n = np.clip(n_orb - c_i, 0, n_orb + 1)
            kk = n_occ - i
            ranks += ct[t1_n, kk] - ct[t2_n, kk]
            prev_pos = c_i
        # wrong-popcount inputs -> -1 (sentinel), matching table semantics
        expected = bits.sum(axis=1)
        ranks = np.where(expected == n_occ, ranks, -1)
        return int(ranks[0]) if scalar else ranks

    def __getitem__(self, key):
        """rt[az] / rt[az_array] subscript access (wci.py interface)."""
        return self.rank(key)

    # ---------------------------------------------------------------- unrank
    def unrank(self, ranks):
        """Inverse of rank: lexicographic rank(s) -> occupancy bitstring(s).

        Lexicographic (matches itertools.combinations): the combination is
        chosen element by element; fixing the i-th element (0-based) to j
        leaves C(n-j-1, k-i-1) combinations below it.
        """
        key = np.asarray(ranks, dtype=np.int64)
        scalar = key.ndim == 0
        if scalar:
            key = key.reshape(1)
        n = len(key)
        n_orb, n_occ, ct = self.n_orb, self.n_occ, self.comb_table
        out = np.zeros(n, dtype=np.int64)
        for m in range(n):
            r = int(key[m])
            bits = []
            for i in range(n_occ):
                # smallest candidate for this element
                lo = (bits[-1] + 1) if bits else 0
                # largest candidate leaving room for the remaining elements
                hi = n_orb - (n_occ - i)
                for j in range(lo, hi + 1):
                    cnt = int(ct[n_orb - j - 1, n_occ - i - 1])
                    if r < cnt:
                        bits.append(j)
                        break
                    r -= cnt
            bs = 0
            for c in bits:  # ascending positions -> LSB bits
                bs |= 1 << c
            out[m] = bs
        return int(out[0]) if scalar else out


def build_rank_tables(n_orb, n_a, n_b):
    """Return (rt_a, rt_b, az_of, bz_of) for the S_z=0 (or general) sector.

    az_of[i] = alpha bitstring of rank i (array length C(n_orb, n_a)),
    bz_of[j] = beta bitstring of rank j.  These are the only O(dim_a/b)
    arrays; at n_orb=38, n_a=8 each is 4.89e7 int64 = 391 MB, and the pair
    ~782 MB — acceptable on the 16 GB machine.  rt_a/rt_b are RankTable
    objects (no O(2^n_orb) arrays).
    """
    az_of = np.array([sum(1 << j for j in c)
                      for c in combinations(range(n_orb), n_a)], dtype=np.int64)
    bz_of = np.array([sum(1 << j for j in c)
                      for c in combinations(range(n_orb), n_b)], dtype=np.int64)
    rt_a = RankTable(n_orb, n_a)
    rt_b = RankTable(n_orb, n_b)
    return rt_a, rt_b, az_of, bz_of
