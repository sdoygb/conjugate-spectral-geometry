#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construct lattices with high spectral rigidity ratio Lambda_H.

Idea:
  Start from the axis-aligned lattice D = diag(1, M, M, ..., M).
  Its Gram eigenvalues are 1, M^2, ..., M^2, so Lambda_H = M^2.
  Apply a random unimodular matrix U (det = +/-1) to get B = D U.
  The lattice is unchanged, but the basis is non-trivial.

Then verify:
  1. The shortest vector lies inside the spectral-rigidity band.
  2. The band contains far fewer candidates than the full search space.
"""

import numpy as np
from itertools import product

def random_unimodular(n, seed=0, steps=20):
    """Generate a random unimodular integer matrix using elementary ops."""
    rng = np.random.default_rng(seed)
    U = np.eye(n, dtype=int)
    for _ in range(steps):
        op = rng.integers(0, 3)
        i, j = rng.integers(0, n), rng.integers(0, n)
        if i == j:
            continue
        if op == 0:
            # add multiple of row j to row i
            k = int(rng.integers(-3, 4))
            if k:
                U[i] += k * U[j]
        elif op == 1:
            # swap rows
            U[[i, j]] = U[[j, i]]
        else:
            # negate row
            U[i] *= -1
    # ensure det +-1
    if abs(round(np.linalg.det(U))) != 1:
        # fallback to identity
        return np.eye(n, dtype=int)
    return U

def high_lambda_lattice(n, M, seed=0):
    """B = diag(1, M, ..., M) @ U, a unimodular transform of a high-gap lattice."""
    D = np.diag([1] + [M] * (n - 1)).astype(float)
    U = random_unimodular(n, seed=seed)
    return D @ U

def shortest_vector(B, bound=8):
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

def band_stats(B, R=8):
    n = B.shape[1]
    G = B.T @ B
    evals, evecs = np.linalg.eigh(G)
    lam1, lam2 = evals[0], evals[1]
    Lh = lam2 / lam1
    u1 = evecs[:, 0]

    delta_sq = (n * (Lh ** ((n - 1) / n)) - 1) / (Lh - 1)
    delta_sq = max(0.0, min(1.0, delta_sq))
    eta = np.sqrt(delta_sq / (1 - delta_sq)) if delta_sq < 1 else 1e6

    v_min, _ = shortest_vector(B, bound=R)
    contains = False
    if v_min is not None:
        a = v_min @ u1
        w = v_min - a * u1
        sin2 = np.dot(w, w) / np.dot(v_min, v_min)
        contains = sin2 <= delta_sq + 1e-8

    N_full = (2 * R + 1) ** n - 1
    N_band = 0
    for coeff in product(range(-R, R + 1), repeat=n):
        c = np.array(coeff, dtype=float)
        if not c.any():
            continue
        a = c @ u1
        w = c - a * u1
        if np.dot(w, w) <= (eta ** 2) * (a ** 2) + 1e-8:
            N_band += 1

    return Lh, contains, N_full, N_band, N_band / N_full

def main():
    print("Constructing high-Lambda_H lattices")
    print("=" * 70)
    for n in (2, 3, 4):
        for M in (10, 100, 1000):
            B = high_lambda_lattice(n, M, seed=n * 1000 + M)
            Lh, contains, N_full, N_band, ratio = band_stats(B, R=8)
            print(f"n={n} M={M:5d} Lambda_H={Lh:12.1f} contains={contains} "
                  f"N_band/N_full={ratio:.4f} ({N_band}/{N_full})")

if __name__ == "__main__":
    main()
