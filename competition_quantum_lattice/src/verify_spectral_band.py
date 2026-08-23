#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Numerical verification of the spectral-rigidity band for SVP.

This script checks the theorem:

    sin^2(theta) <= (n * Lambda_H^((n-1)/n) - 1) / (Lambda_H - 1)

for random small lattices, and constructs the explicit spectral-rigidity band

    S_geo = { v in Z^n \\ {0} : ||w||^2 <= eta^2 a^2 }

where a = v.u_1 and w = v - a u_1.

It verifies:
  1. The shortest vector lies inside S_geo.
  2. The number of candidates inside S_geo is much smaller than the full search space.
"""

import numpy as np
from itertools import product

def shortest_vector(B, bound=8):
    """Brute-force shortest nonzero lattice vector."""
    n = B.shape[1]
    best = None
    best_norm = None
    for coeff in product(range(-bound, bound + 1), repeat=n):
        c = np.array(coeff, dtype=float)
        if not c.any():
            continue
        nrm = np.linalg.norm(B @ c)
        if best_norm is None or nrm < best_norm:
            best_norm = nrm
            best = c
    return best, best_norm

def spectral_band_contains(B, v, delta_sq, tol=1e-8):
    """Check whether vector v lies in the spectral-rigidity band."""
    n = B.shape[1]
    G = B.T @ B
    evals, evecs = np.linalg.eigh(G)
    u1 = evecs[:, 0]
    a = v @ u1
    w = v - a * u1
    if abs(a) < tol:
        return False
    sin2 = np.dot(w, w) / np.dot(v, v)
    return sin2 <= delta_sq + tol

def band_candidate_count(B, R, eta):
    """Count integer vectors inside S_geo within [-R,R]^n."""
    n = B.shape[1]
    G = B.T @ B
    evals, evecs = np.linalg.eigh(G)
    u1 = evecs[:, 0]
    count = 0
    for coeff in product(range(-R, R + 1), repeat=n):
        c = np.array(coeff, dtype=float)
        if not c.any():
            continue
        a = c @ u1
        w = c - a * u1
        if np.dot(w, w) <= (eta ** 2) * (a ** 2) + 1e-8:
            count += 1
    return count

def verify_dimension(n, trials=120, bound=5, seed=0):
    rng = np.random.default_rng(seed)
    results = []
    print(f"\nn={n} random lattice spectral-band verification")
    print("=" * 70)
    print(f"{'Lambda_H':>10} {'contains':>8} {'N_full':>10} {'N_band':>10} {'ratio':>10}")

    for trial in range(trials):
        B = rng.integers(-3, 4, size=(n, n)).astype(float)
        if np.linalg.matrix_rank(B) < n:
            continue
        G = B.T @ B
        evals = np.linalg.eigvalsh(G)
        if evals[0] <= 1e-12:
            continue
        lam1, lam2 = evals[0], evals[1]
        Lh = lam2 / lam1

        v_min, _ = shortest_vector(B, bound=bound)
        if v_min is None:
            continue

        delta_sq = (n * (Lh ** ((n - 1) / n)) - 1) / (Lh - 1)
        delta_sq = max(0.0, min(1.0, delta_sq))
        contains = spectral_band_contains(B, v_min, delta_sq)

        eta = np.sqrt(delta_sq / (1 - delta_sq)) if delta_sq < 1 else 1e6
        R = bound
        N_full = (2 * R + 1) ** n - 1
        N_band = band_candidate_count(B, R, eta)

        ratio = N_band / N_full
        results.append((Lh, contains, N_full, N_band, ratio))

        if trial < 8 or not contains:
            print(f"{Lh:10.3f} {str(contains):>8} {N_full:10d} {N_band:10d} {ratio:10.4f}")

    print("-" * 70)
    arr = np.array([r[1] for r in results], dtype=bool)
    ratios = np.array([r[4] for r in results])
    print(f"Total trials: {len(results)}")
    print(f"Shortest vector inside band: {arr.mean():.3f}")
    print(f"Average N_band/N_full: {ratios.mean():.4f}")
    print(f"Median N_band/N_full: {np.median(ratios):.4f}")
    print(f"Max N_band/N_full: {ratios.max():.4f}")
    return results


def main():
    for n in (2, 3, 4):
        verify_dimension(n, trials=100, bound=5, seed=123 + n)

if __name__ == "__main__":
    main()
