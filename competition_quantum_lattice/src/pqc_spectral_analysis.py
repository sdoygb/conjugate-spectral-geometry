#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze the spectral rigidity ratio Lambda_H for PQC-like random q-ary lattices.

This script samples random q-ary matrices A (entries uniform mod q), forms the
Gram matrix G = A^T A, and reports the distribution of Lambda_H = lambda_2/lambda_1.

The goal is to check whether standard random PQC-like lattices exhibit the high
spectral rigidity that our attack exploits.
"""

import numpy as np

def sample_lambda_h(n, q, rng):
    A = rng.integers(0, q, size=(n, n)).astype(float)
    G = A.T @ A
    evals = np.linalg.eigvalsh(G)
    if evals[0] <= 1e-12:
        return None
    return evals[1] / evals[0]

def analyze(n, q, trials=200, seed=0):
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(trials):
        lh = sample_lambda_h(n, q, rng)
        if lh is not None:
            vals.append(lh)
    arr = np.array(vals)
    print(f"n={n:3d} q={q:5d} trials={len(arr):3d} "
          f"mean={arr.mean():7.3f} median={np.median(arr):7.3f} "
          f"max={arr.max():8.1f} "
          f">10: {np.mean(arr>10):.3f} >100: {np.mean(arr>100):.3f} >1000: {np.mean(arr>1000):.3f}")

def main():
    print("PQC-like random q-ary lattice spectral rigidity analysis")
    print("=" * 80)
    for q in (257, 3329):
        for n in (8, 16, 32):
            analyze(n, q, trials=100, seed=q + n)

if __name__ == "__main__":
    main()
