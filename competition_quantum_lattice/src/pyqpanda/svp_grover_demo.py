#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grover-accelerated SVP coefficient enumeration demo (small prototype).

A 2D lattice is used for illustration.  The coefficient pair (x, y) is encoded
into 10 qubits (5 bits for x, 5 bits for y).  A real SVP oracle would compute
the lattice norm and mark all vectors whose norm is below a threshold.  In this
prototype we mark the known short-vector solution to validate the Grover engine
and to provide a reproducible 10-qubit experiment.

Complexity:
  Classical exhaustive search over B^2 candidates: O(2^{2m})
  Grover search: O(2^m) oracle queries, i.e. quadratic speedup.
"""

from grover_search import run_grover


def encode_vector(x: int, y: int, bits: int = 5) -> int:
    """Encode (x, y) into an integer: x in high bits, y in low bits."""
    return (x << bits) | y


def main():
    bits = 5
    n = 2 * bits  # 10 qubits

    # A deliberately simple lattice basis and a known short vector.
    # v = (2, 1) -> x=2, y=1
    x, y = 2, 1
    target = encode_vector(x, y, bits)

    # Optimal Grover iterations for one marked state among 2^n.
    import math
    iters = int(math.pi / 4 * math.sqrt(2 ** n))

    print(f"SVP prototype: {n} qubits, target short vector ({x},{y})")
    print(f"target encoded state = {target} = |{target:0{n}b}>")
    print(f"Grover iterations = {iters}")

    probs = run_grover(n, [target], iters, shots=20000)
    top = sorted(probs.items(), key=lambda kv: -kv[1])[:5]
    for state, p in top:
        state_int = int(state, 2)
        xx = (state_int >> bits) & ((1 << bits) - 1)
        yy = state_int & ((1 << bits) - 1)
        print(f"  |{state}> ({state_int}): {p:.4f}  -> ({xx},{yy})")

    success = probs.get(f"{target:0{n}b}", 0.0)
    print(f"\nSuccess probability for target ({x},{y}): {success:.4f}")


if __name__ == "__main__":
    main()
