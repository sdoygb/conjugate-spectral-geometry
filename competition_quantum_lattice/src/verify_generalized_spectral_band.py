#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Numerical verification of the generalized spectral-rigidity band theorem.

The theorem states: if the smallest eigenvalue of G = B^T B has multiplicity m
and Lambda_H^(m) = lambda_{m+1}/lambda_m is large, then the shortest lattice
vector lies close to the m-dimensional eigenspace of lambda_1.

We construct lattices with degenerate small eigenvalues:
    D = diag(1, ..., 1, M, ..., M)   (m ones, n-m M's)
and apply random unimodular transforms.  Then we check:
  1. The shortest vector lies in the generalized spectral band.
  2. The band contains few candidates.
"""

import numpy as np
from itertools import product

def random_unimodular(n, seed=0, steps=20):
    rng = np.random.default_rng(seed)
    U = np.eye(n, dtype=int)
    for _ in range(steps):
        op = int(rng.integers(0, 3))
        i, j = int(rng.integers(0, n)), int(rng.integers(0, n))
        if i == j:
            continue
        if op == 0:
            k = int(rng.integers(-3, 4))
            if k:
                U[i] += k * U[j]
        elif op == 1:
            U[[i, j]] = U[[j, i]]
        else:
            U[i] *= -1
    if abs(round(np.linalg.det(U))) != 1:
        return np.eye(n, dtype=int)
    return U

def degenerate_lattice(n, m, M, seed=0):
    D = np.diag([1.0]*m + [float(M)]*(n-m))
    U = random_unimodular(n, seed=seed)
    return D @ U

def shortest_vector(B, R=6):
    n = B.shape[1]
    best = None
    best_norm = None
    for coeff in product(range(-R, R+1), repeat=n):
        c = np.array(coeff, dtype=float)
        if not c.any():
            continue
        nrm = np.linalg.norm(B @ c)
        if best_norm is None or nrm < best_norm:
            best_norm = nrm
            best = c
    return best, best_norm

def band_contains(B, v, m, delta_sq, tol=1e-8):
    n = B.shape[1]
    G = B.T @ B
    evals, evecs = np.linalg.eigh(G)
    U = evecs[:, :m]
    # projection onto U
    proj = U @ (U.T @ v)
    perp = v - proj
    sin2 = np.dot(perp, perp) / np.dot(v, v)
    return sin2 <= delta_sq + tol

def band_count(B, m, eta, R):
    n = B.shape[1]
    G = B.T @ B
    evals, evecs = np.linalg.eigh(G)
    U = evecs[:, :m]
    count = 0
    for coeff in product(range(-R, R+1), repeat=n):
        c = np.array(coeff, dtype=float)
        if not c.any():
            continue
        proj = U @ (U.T @ c)
        perp = c - proj
        a2 = np.dot(proj, proj)
        w2 = np.dot(perp, perp)
        if w2 <= (eta**2) * a2 + 1e-8:
            count += 1
    return count

def main():
    print("Generalized spectral-rigidity band verification")
    print("=" * 72)
    cases = [(4, 2, 10, 4, 10), (4, 2, 100, 4, 10),
             (5, 2, 10, 3, 8), (5, 2, 100, 3, 8),
             (5, 3, 10, 3, 8), (5, 3, 100, 3, 8)]
    for n, m, M, R, trials in cases:
        ok = True
        ratios = []
        lh_list = []
        for seed in range(trials):
            B = degenerate_lattice(n, m, M, seed=seed)
            G = B.T @ B
            evals = np.linalg.eigvalsh(G)
            lam_m = evals[m-1]
            lam_next = evals[m]
            Lh = lam_next / lam_m
            lh_list.append(Lh)
            delta_sq = (n * (Lh ** ((n-m)/n)) - 1) / (Lh - 1)
            delta_sq = max(0.0, min(1.0, delta_sq))
            v, _ = shortest_vector(B, R=R)
            if v is None or not band_contains(B, v, m, delta_sq):
                ok = False
                break
            eta = np.sqrt(delta_sq / (1 - delta_sq)) if delta_sq < 1 else 1e6
            cnt = band_count(B, m, eta, R=R)
            N_full = (2*R+1)**n - 1
            ratios.append(cnt / N_full)
        print(f"n={n} m={m} M={M:4d} R={R} Lambda_H^({m}) med={np.median(lh_list):.1f} "
              f"contains_all={ok} avg_ratio={np.mean(ratios):.4f}")

if __name__ == "__main__":
    main()
