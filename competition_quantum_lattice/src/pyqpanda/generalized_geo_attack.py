#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generalized spectral-rigidity Grover attack prototype.

This prototype encodes the generalized spectral-rigidity band (m-dimensional
smallest-eigenvalue subspace) into a Grover oracle.  It supports:

  1. Degenerate high-gap lattices D = diag(1,...,1,M,...,M) * U.
  2. Module-like negacyclic matrices (ML-KEM-style small analog).

The oracle marks states satisfying:
  - in_generalized_band(v): distance to the m-dimensional eigenspace is small
  - short_enough(v): ||B v|| <= threshold
"""

import math
import numpy as np
from itertools import product

from grover_search import run_grover, grover_circuit


# ---------- lattice construction ----------

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
    D = np.diag([1.0] * m + [float(M)] * (n - m))
    U = random_unimodular(n, seed=seed)
    return D @ U


def negacyclic_matrix(v):
    n = len(v)
    M = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            if j >= i:
                M[i, j] = v[j - i]
            else:
                M[i, j] = -v[n - (i - j)]
    return M


def module_like_lattice(k, n, q, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(k):
        row = []
        for j in range(k):
            v = rng.integers(0, q, size=n)
            row.append(negacyclic_matrix(v))
        rows.append(np.hstack(row))
    return np.vstack(rows).astype(float)


# ---------- generalized spectral band ----------

def generalized_band_data(B, m, R):
    n = B.shape[1]
    G = B.T @ B
    evals, evecs = np.linalg.eigh(G)
    lam_m = evals[m - 1]
    lam_next = evals[m]
    Lh = lam_next / lam_m
    U = evecs[:, :m]

    delta_sq = (n * (Lh ** ((n - m) / n)) - 1) / (Lh - 1)
    delta_sq = max(0.0, min(1.0, delta_sq))
    eta = np.sqrt(delta_sq / (1 - delta_sq)) if delta_sq < 1 else 1e6

    shortest_norm = None
    shortest = None
    for coeff in product(range(-R, R + 1), repeat=n):
        c = np.array(coeff, dtype=float)
        if not c.any():
            continue
        nrm = np.linalg.norm(B @ c)
        if shortest_norm is None or nrm < shortest_norm:
            shortest_norm = nrm
            shortest = tuple(int(x) for x in c)

    threshold = shortest_norm * 1.000001

    def in_band(v):
        proj = U @ (U.T @ v)
        perp = v - proj
        return np.dot(perp, perp) <= (eta ** 2) * np.dot(proj, proj) + 1e-8

    marked = []
    vectors = []
    for coeff in product(range(-R, R + 1), repeat=n):
        c = np.array(coeff, dtype=float)
        if not c.any():
            continue
        idx = len(vectors)
        vectors.append(c)
        if in_band(c) and np.linalg.norm(B @ c) <= threshold:
            marked.append(idx)

    return vectors, marked, {
        "Lambda_H_m": Lh,
        "m": m,
        "shortest": shortest,
        "threshold": threshold,
    }


# ---------- attack ----------

def run_attack(B, m, R, shots=10000, seed=7):
    vectors, marked, stats = generalized_band_data(B, m, R)
    N = len(vectors)
    nq = max(1, math.ceil(math.log2(N)))
    M_count = len(marked)
    iters = int(math.pi / 4 * math.sqrt(N / max(1, M_count)))
    probs = run_grover(nq, marked, iters, shots=shots)
    success = sum(p for state, p in probs.items() if int(state, 2) in marked)
    return {
        "N_full": N,
        "N_marked": M_count,
        "qubits": nq,
        "iters": iters,
        "success": success,
        **stats,
    }


def main():
    print("Generalized spectral-rigidity Grover attack")
    print("=" * 72)

    # Case 1: degenerate high-gap lattice, m=2
    for n, m, M, R in [(4, 2, 100, 4), (5, 2, 100, 3)]:
        B = degenerate_lattice(n, m, M, seed=42)
        r = run_attack(B, m, R)
        print(f"[degenerate] n={n} m={m} M={M} R={R} "
              f"Lambda_H^({m})={r['Lambda_H_m']:.1f} N={r['N_full']} marked={r['N_marked']} "
              f"qubits={r['qubits']} success={r['success']:.4f}")

    # Case 2: module-like negacyclic lattice (ML-KEM style small analog)
    # Larger dimensions use smaller R to keep brute-force enumeration feasible.
    module_cases = [
        (1, 4, 2),   # dim=4, R=2, 5^4=625
        (2, 4, 2),   # dim=8, R=2, 5^8=390k
        (1, 8, 1),   # dim=8, R=1, 3^8=6561
        (2, 5, 1),   # dim=10, R=1, 3^10=59049
    ]
    for k, n, R in module_cases:
        q = 17
        B = module_like_lattice(k, n, q, seed=7)
        dim = k * n
        m = 2  # spectral degeneracy from real cyclotomic structure
        try:
            r = run_attack(B, m, R)
            print(f"[module-like] k={k} n={n} dim={dim} R={R} "
                  f"Lambda_H^({m})={r['Lambda_H_m']:.3f} N={r['N_full']} marked={r['N_marked']} "
                  f"qubits={r['qubits']} success={r['success']:.4f}")
        except Exception as e:
            print(f"[module-like] k={k} n={n} failed: {e}")


if __name__ == "__main__":
    main()
