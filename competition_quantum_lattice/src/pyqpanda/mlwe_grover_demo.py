#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grover-accelerated MLWE/LWE bounded-distance decoding prototype.

The search space is a small binary error/secret vector encoded into 10 qubits.
A real MLWE oracle would compute A*s + e = b and check whether e has small
norm; here we mark a known solution to validate the Grover engine.

Complexity:
  Classical exhaustive search over 2^n candidates: O(2^n)
  Grover search: O(2^{n/2}) oracle queries, i.e. quadratic speedup.
"""

from grover_search import run_grover


def main():
    n = 10  # at least 10 qubits for the small-scale experiment

    # Known solution: error/secret vector as a 10-bit string.
    # Example: s = 1010101010 (binary) = 682
    target = 0b1010101010

    import math
    iters = int(math.pi / 4 * math.sqrt(2 ** n))

    print(f"MLWE prototype: {n} qubits, target solution = {target} = |{target:0{n}b}>")
    print(f"Grover iterations = {iters}")

    probs = run_grover(n, [target], iters, shots=20000)
    top = sorted(probs.items(), key=lambda kv: -kv[1])[:5]
    for state, p in top:
        state_int = int(state, 2)
        print(f"  |{state}> ({state_int}): {p:.4f}")

    success = probs.get(f"{target:0{n}b}", 0.0)
    print(f"\nSuccess probability for target: {success:.4f}")


if __name__ == "__main__":
    main()
