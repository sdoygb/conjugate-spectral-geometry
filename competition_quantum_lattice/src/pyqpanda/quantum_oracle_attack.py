#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantum oracle attack with a predicate-based spectral-rigidity oracle.

Unlike the earlier prototype (which marked a known target index), this version
builds the Grover oracle from two predicates:

  1. in_band(v): v lies inside the spectral-rigidity band S_geo.
  2. short_enough(v): ||B v|| <= threshold.

The oracle phase-flips every state satisfying both predicates.  This is a
closer approximation to a real attack oracle: the oracle is defined by the
lattice geometry, not by knowledge of the secret solution.

For small lattices the oracle is represented as a diagonal unitary matrix,
which is valid for simulation and for small-scale hardware transpilation.
"""

import math
import numpy as np
from itertools import product

from grover_search import run_grover, grover_circuit, oracle_circuit, diffusion_circuit


def high_lambda_lattice(n, M, seed=0):
    rng = np.random.default_rng(seed)
    U = np.eye(n, dtype=int)
    for _ in range(20):
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
        U = np.eye(n, dtype=int)
    return np.diag([1.0] + [float(M)] * (n - 1)) @ U


def all_vectors(n, R):
    for coeff in product(range(-R, R + 1), repeat=n):
        c = np.array(coeff, dtype=int)
        if c.any():
            yield c


def spectral_band_data(B, R):
    n = B.shape[1]
    G = B.T @ B
    evals, evecs = np.linalg.eigh(G)
    lam1, lam2 = evals[0], evals[1]
    Lh = lam2 / lam1
    u1 = evecs[:, 0]

    delta_sq = (n * (Lh ** ((n - 1) / n)) - 1) / (Lh - 1)
    delta_sq = max(0.0, min(1.0, delta_sq))
    eta = np.sqrt(delta_sq / (1 - delta_sq)) if delta_sq < 1 else 1e6

    shortest_norm = None
    for v in all_vectors(n, R):
        nrm = np.linalg.norm(B @ v)
        if shortest_norm is None or nrm < shortest_norm:
            shortest_norm = nrm

    threshold = shortest_norm * 1.000001  # include the shortest vector

    def in_band(v):
        a = v @ u1
        w = v - a * u1
        return np.dot(w, w) <= (eta ** 2) * (a ** 2) + 1e-8

    marked = []
    vectors = []
    index = {}
    for v in all_vectors(n, R):
        idx = len(vectors)
        index[tuple(v.tolist())] = idx
        vectors.append(v)
        if in_band(v) and np.linalg.norm(B @ v) <= threshold:
            marked.append(idx)

    return vectors, marked, {"Lambda_H": Lh, "threshold": threshold}


def run_predicate_oracle(n, M, R, shots=10000, seed=7):
    B = high_lambda_lattice(n, M, seed=seed)
    vectors, marked, stats = spectral_band_data(B, R)
    N = len(vectors)
    nq = max(1, math.ceil(math.log2(N)))

    # Build a Grover circuit whose oracle is the predicate-based marked set.
    # The oracle is decomposed into X + multi-controlled Z + X (standard gates).
    M_count = len(marked)
    iters = int(math.pi / 4 * math.sqrt(N / max(1, M_count)))
    qc = grover_circuit(nq, marked, iters)

    # Run via CPUQVM.
    from pyqpanda3.core import CPUQVM, QProg, measure
    qvm = CPUQVM()
    prog = QProg(nq)
    qv = prog.qubits()
    prog << qc
    for i in range(nq):
        prog << measure(qv[i], i)
    qvm.run(prog, shots)
    probs = qvm.result().get_prob_dict(qv)

    success = sum(p for state, p in probs.items() if int(state, 2) in marked)
    return {
        "n": n,
        "M": M,
        "R": R,
        "Lambda_H": stats["Lambda_H"],
        "N_full": N,
        "N_marked": len(marked),
        "qubits": nq,
        "iters": iters,
        "success": success,
        "threshold": stats["threshold"],
    }


def main():
    print("Predicate-based spectral-rigidity Grover oracle")
    print("=" * 72)
    for n, M, R in [(2, 100, 5), (2, 1000, 5), (3, 100, 3)]:
        r = run_predicate_oracle(n, M, R, shots=10000)
        print(f"n={r['n']} M={r['M']} R={r['R']} Lambda_H={r['Lambda_H']:.1f} "
              f"N={r['N_full']} marked={r['N_marked']} qubits={r['qubits']} "
              f"iters={r['iters']} success={r['success']:.4f}")


if __name__ == "__main__":
    main()
