"""geo10-15 solver: constrained-submanifold Newton descent (10.91 complete).

M1 scope: LiH/6-31G (dim=3025) — reproduce 10.91 §12 block-Newton
0.0000 mHa against dense FCI, with the NEW main loop (correct-then-expand,
dual stopping 9.2).  Reuses geoqc building blocks (exterior sector action,
rank tables, diagonal lookup) but does NOT reuse wci.py's main loop.

Layering (each module imports only the layer below):
    rank.py     — combinatorial RankTable (bitstring <-> lexicographic rank)
    system.py   — build the sector Hamiltonian (apply_fn / hd_fn / seed)
    blocks.py   — Bruhat-ball normal-Hessian blocks + block Jacobi
    descent.py  — the NEW main loop: constrained-submanifold Newton
    verify.py   — machine-precision checks (sign, monotonicity, ordering)
"""
