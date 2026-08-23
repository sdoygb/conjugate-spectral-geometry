#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generic Grover search with an explicit phase oracle matrix.

This is a building block for the two quantum lattice attacks:
  1. Grover-accelerated SVP coefficient enumeration.
  2. Grover-accelerated MLWE/LWE bounded-distance decoding.

The oracle is provided as a diagonal unitary (phase flip on marked states).
For a real SVP/MLWE oracle the marked set would be computed by a norm/error
predicate circuit; in this prototype we use known marked states to validate
the Grover engine and to measure the success probability scaling.
"""

import numpy as np
from pyqpanda3.core import CPUQVM, QCircuit, QProg, H, X, Z, measure


def mcz(qubits: list[int]) -> QCircuit:
    """Multi-controlled Z gate on all qubits (last qubit is target)."""
    cir = QCircuit()
    if len(qubits) == 1:
        cir << Z(qubits[0])
    else:
        cir << Z(qubits[-1]).control(qubits[:-1])
    return cir


def oracle_circuit(n: int, marked: list[int]) -> QCircuit:
    """Phase flip oracle for the given marked basis states."""
    cir = QCircuit()
    qubits = list(range(n))
    for s in marked:
        # little-endian bit order: qubit i is the i-th bit of the integer
        for i in range(n):
            bit = (s >> i) & 1
            if bit == 0:
                cir << X(qubits[i])
        cir << mcz(qubits)
        for i in range(n):
            bit = (s >> i) & 1
            if bit == 0:
                cir << X(qubits[i])
    return cir


def diffusion_circuit(n: int) -> QCircuit:
    """Grover diffusion operator."""
    cir = QCircuit()
    qubits = list(range(n))
    for q in qubits:
        cir << H(q)
    for q in qubits:
        cir << X(q)
    cir << mcz(qubits)
    for q in qubits:
        cir << X(q)
    for q in qubits:
        cir << H(q)
    return cir


def grover_circuit(n: int, marked: list[int], iterations: int) -> QCircuit:
    """Return a Grover circuit for the given marked states."""
    qc = QCircuit()
    qubits = list(range(n))

    # initial superposition
    for q in qubits:
        qc << H(q)

    oracle = oracle_circuit(n, marked)
    diffusion = diffusion_circuit(n)

    for _ in range(iterations):
        qc << oracle
        qc << diffusion

    return qc


def run_grover(n: int, marked: list[int], iterations: int, shots: int = 10000, seed: int = 0) -> dict:
    """Run Grover and return a probability dict keyed by integer state."""
    qvm = CPUQVM()
    prog = QProg(n)
    qubits = prog.qubits()
    prog << grover_circuit(n, marked, iterations)
    for i in range(n):
        prog << measure(qubits[i], i)

    qvm.run(prog, shots)
    res = qvm.result()
    return res.get_prob_dict(qubits)


if __name__ == "__main__":
    # Example: n=5 qubits, search for |10101> = 21
    n = 5
    target = 21
    iters = 3  # ~ pi/4 * sqrt(2^n / 1)
    probs = run_grover(n, [target], iters, shots=20000, seed=0)
    top = sorted(probs.items(), key=lambda x: -x[1])[:5]
    print(f"n={n}, target={target}, iterations={iters}")
    for state, p in top:
        state_int = int(state, 2)
        print(f"  |{state}> ({state_int}): {p:.4f}")
