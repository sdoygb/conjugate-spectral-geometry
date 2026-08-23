#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a 9-qubit spectral-rigidity Grover circuit for Origin Wukong.

This script builds the predicate-based spectral-rigidity Grover circuit for
the n=3 high-Lambda_H lattice and prints its OriginIR representation, which can
be submitted to the Origin Quantum cloud platform.

Run:
    python3 wukong_submit.py
"""

import math
import numpy as np
from itertools import product

from grover_search import grover_circuit
from quantum_oracle_attack import high_lambda_lattice, all_vectors, spectral_band_data
from pyqpanda3.core import QProg, measure


def build_circuit(n=3, M=100, R=3, seed=7):
    B = high_lambda_lattice(n, M, seed=seed)
    vectors, marked, stats = spectral_band_data(B, R)
    N = len(vectors)
    nq = max(1, math.ceil(math.log2(N)))
    M_count = len(marked)
    iters = int(math.pi / 4 * math.sqrt(N / max(1, M_count)))

    qc = grover_circuit(nq, marked, iters)
    prog = QProg(nq)
    qubits = prog.qubits()
    prog << qc
    for i in range(nq):
        prog << measure(qubits[i], i)
    return prog, {
        "n": n,
        "M": M,
        "R": R,
        "Lambda_H": stats["Lambda_H"],
        "N_full": N,
        "N_marked": M_count,
        "qubits": nq,
        "iters": iters,
    }


def main():
    prog, info = build_circuit()
    print("Origin Wukong submission circuit")
    print("=" * 72)
    for k, v in info.items():
        print(f"{k}: {v}")
    print("-" * 72)
    print(prog.originir())
    # Save OriginIR to file for manual submission
    with open("../../results/wukong_circuit.originir", "w", encoding="utf-8") as f:
        f.write(prog.originir())
    print("Saved to results/wukong_circuit.originir")


if __name__ == "__main__":
    main()
