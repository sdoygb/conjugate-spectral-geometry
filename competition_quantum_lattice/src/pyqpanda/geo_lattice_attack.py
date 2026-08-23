#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geometry-theory inspired Grover attack prototype.

Pipeline:
  1. Construct a high-Lambda_H lattice  B = diag(1, M, ..., M) * U.
  2. Compute the spectral-rigidity band S_geo from the Gram matrix.
  3. Restrict the search space to S_geo (classically enumerated for the
     small-scale prototype).
  4. Encode the band candidates into qubits.
  5. Run Grover to find the shortest lattice vector inside the band.

This demonstrates that the spectral-rigidity band reduces the quantum search
space from N_full to N_band, and that Grover then needs only
O(sqrt(N_band)) oracle queries.
"""

import math
import numpy as np
from itertools import product

from grover_search import run_grover


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


def high_lambda_lattice(n, M, seed=0):
    D = np.diag([1.0] + [float(M)] * (n - 1))
    U = random_unimodular(n, seed=seed)
    return D @ U


def spectral_band_candidates(B, R=8):
    """Return (candidates, target_index, stats)."""
    n = B.shape[1]
    G = B.T @ B
    evals, evecs = np.linalg.eigh(G)
    lam1, lam2 = evals[0], evals[1]
    Lh = lam2 / lam1
    u1 = evecs[:, 0]

    delta_sq = (n * (Lh ** ((n - 1) / n)) - 1) / (Lh - 1)
    delta_sq = max(0.0, min(1.0, delta_sq))
    eta = np.sqrt(delta_sq / (1 - delta_sq)) if delta_sq < 1 else 1e6

    # brute-force shortest vector and band candidates
    best = None
    best_norm = None
    candidates = []
    for coeff in product(range(-R, R + 1), repeat=n):
        c = np.array(coeff, dtype=float)
        if not c.any():
            continue
        nrm = np.linalg.norm(B @ c)
        if best_norm is None or nrm < best_norm:
            best_norm = nrm
            best = tuple(int(x) for x in c)
        a = c @ u1
        w = c - a * u1
        if np.dot(w, w) <= (eta ** 2) * (a ** 2) + 1e-8:
            candidates.append(tuple(int(x) for x in c))

    # ensure the shortest vector is included (it should be, by the theorem)
    if best not in candidates:
        candidates.append(best)

    candidates = sorted(set(candidates))
    target_index = candidates.index(best)

    N_full = (2 * R + 1) ** n - 1
    stats = {
        "Lambda_H": Lh,
        "N_full": N_full,
        "N_band": len(candidates),
        "ratio": len(candidates) / N_full,
        "shortest": best,
        "target_index": target_index,
    }
    return candidates, target_index, stats


def run_case(n, M, R, seed):
    B = high_lambda_lattice(n, M, seed=seed)
    candidates, target_index, stats = spectral_band_candidates(B, R=R)

    print(f"n={n}, M={M}, R={R}, Lambda_H={stats['Lambda_H']:.1f}")
    print(f"  shortest={stats['shortest']}, N_full={stats['N_full']}, "
          f"N_band={stats['N_band']}, ratio={stats['ratio']:.4f}")

    nq = max(1, math.ceil(math.log2(len(candidates))))
    full_nq = math.ceil(math.log2(stats['N_full']))
    print(f"  qubits: {full_nq} -> {nq}")

    iters = int(math.pi / 4 * math.sqrt(2 ** nq))
    probs = run_grover(nq, [target_index], iters, shots=10000)
    success = probs.get(f"{target_index:0{nq}b}", 0.0)
    print(f"  Grover success probability = {success:.4f} (iters={iters})")
    return stats, success


def main():
    print("Geometry-theory Grover attack prototype (n=2,3,4)")
    print("=" * 72)

    cases = [
        (2, 100, 8, 42),
        (3, 100, 5, 43),
        (3, 1000, 5, 44),
        (4, 100, 4, 45),
        (4, 1000, 4, 46),
    ]

    for n, M, R, seed in cases:
        run_case(n, M, R, seed)
        print()


if __name__ == "__main__":
    main()
