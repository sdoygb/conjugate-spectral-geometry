#!/usr/bin/env python3
"""M1: LiH/6-31G (dim=3025) — the NEW descent reproduces 10.91 §12.

Runs the constrained-submanifold Newton descent from the HF seed with the
dual stopping criterion (9.2), and at two variational-space sizes performs
the strict three-way dense comparison (diagonal EN-PT2 / block Newton /
exact 2nd-order Schur complement) against full FCI:

  hierarchy (10.91 §12.2): |E_exact2| <= |E_block| <= |E_diag|
  target (10.91 §12.4):    block-Newton error vs FCI -> 0.0000 mHa
                           at small residual (|V| ~ 500)

Usage:  PYTHONPATH=. .venv311/bin/python3 -u geo10-15/scripts/m1_lih631g.py
"""
import sys, os, time
import numpy as np
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                     # geo10-15/
GEOQC = os.path.join(os.path.dirname(ROOT), "geocore")
for p in (ROOT, GEOQC):
    if p not in sys.path:
        sys.path.insert(0, p)

from solver.system import SectorSystem
from solver.descent import Descent
from solver.blocks import BlockNewton, diagonal_pt2, gather_residual
from solver import verify


def build_lih_631g():
    """LiH/6-31G MO integrals + FCI reference (PySCF)."""
    from pyscf import gto, scf, fci
    mol = gto.M(atom='Li 0 0 0; H 0 0 1.595', basis='6-31g', verbose=0)
    mf = scf.RHF(mol); mf.kernel()
    mo = mf.mo_coeff
    h_mo = mo.T @ mf.get_hcore() @ mo
    t_mo = np.einsum('ap,bq,cr,ds,abcd->pqrs', mo, mo, mo, mo,
                     mol.intor('int2e'), optimize=True)
    e_fci = fci.FCI(mf).kernel()[0]
    return (mol.nao_nr(), mol.nelectron // 2, h_mo, t_mo,
            mol.energy_nuc(), float(mf.e_tot), float(e_fci))


def dense_analysis(V, sys, H_full, all_idx, e_fci, blk):
    """Three-way normal-Hessian comparison at a fixed V (dense anchor)."""
    dim = len(all_idx)
    posV = np.searchsorted(all_idx, V)
    maskV = np.zeros(dim, dtype=bool); maskV[posV] = True
    posO = np.where(~maskV)[0]
    H_VV = H_full[np.ix_(posV, posV)]
    ev, Cv = np.linalg.eigh(H_VV)
    E_var = float(ev[0]); c_var = Cv[:, 0]
    rO = H_full[np.ix_(posO, posV)] @ c_var
    O_idx = all_idx[posO]
    Hn = H_full[np.ix_(posO, posO)] - E_var * np.eye(len(posO))
    x_exact = np.linalg.solve(Hn, rO)
    E_exact2 = -float(rO @ x_exact)

    # diagonal EN-PT2 with the FULL diagonal (H_DD incl. two-body)
    diag_full = np.diag(H_full)
    dn = E_var - diag_full[posO]
    dn = np.where(np.abs(dn) < 1e-10, 1e-10, dn)
    E_diag = float(np.sum(rO ** 2 / dn))

    # our block Newton (same V, disjoint balls)
    E_blk, info = blk.sweep(O_idx, rO, E_var, in_space_idx=V,
                            jacobi_sweeps=3, verbose=False)
    cov = info["residual_coverage"]

    def mha(ec):
        return (E_var + ec - e_fci) * 1000

    print(f"  |V|={len(V):4d}  n_out={len(posO):5d}  ||r_out||={np.linalg.norm(rO):.5f}")
    print(f"    min eig H_N = {np.linalg.eigvalsh(Hn)[0]:+.3e}")
    print(f"    err vs FCI (mHa): variational={mha(0):+.4f}  "
          f"diagPT2={mha(E_diag):+.4f}  block={mha(E_blk):+.4f}  "
          f"exact2nd={mha(E_exact2):+.4f}")
    print(f"    cov={cov:.4f}  n_blocks={info['n_blocks']}  "
          f"block sizes={info['block_sizes'][:6]}")
    if info.get("jacobi_gaps"):
        print(f"    block-Jacobi: rho={info['jacobi_rho']:.3f}  "
              f"gap-to-exact={[f'{g:+.2e}' for g in info['jacobi_gaps']]}")
    if cov > 0.999:
        ok_ord = verify.check_ordering(E_exact2, E_blk, E_diag,
                                       raise_on_error=False)
        print(f"    ordering |exact|<=|block|<=|diag| (cov={cov:.4f}): {ok_ord}")
    else:
        print(f"    (ordering check skipped: coverage {cov:.4f} < 0.999)")
    return E_var, E_blk, E_diag, E_exact2, info


def main():
    print("=" * 78)
    print("M1  LiH/6-31G  constrained-submanifold Newton descent "
          "(10.91 complete)")
    print("=" * 78)
    n_orb, n_occ, h_sp, t_sp, nuc, e_rhf, e_fci = build_lih_631g()
    n_a = n_b = n_occ
    sys = SectorSystem(n_orb, n_a, n_b, h_sp, t_sp, nuc, eps=1e-10)
    dim = sys.dim
    print(f"n_orb={n_orb}, n_a=n_b={n_occ}, dim={dim}, FCI={e_fci:.10f}")
    print(f"HF seed idx={sys.seed_idx}")

    # ---- full dense H on the whole sector (dense anchor; 3025x3025) ----
    print("\nBuilding full dense H ...", flush=True)
    t0 = time.time()
    all_idx = np.arange(dim, dtype=np.int64)
    H_full = np.zeros((dim, dim), dtype=float)
    for j in range(dim):
        u, w = sys.h_col(int(all_idx[j]))
        pos = np.searchsorted(all_idx, u)
        valid = pos < dim
        if valid.any():
            valid[valid] &= all_idx[pos[valid]] == u[valid]
        np.add.at(H_full, (pos[valid], j), w[valid])
    H_full = (H_full + H_full.T) / 2.0
    print(f"dense H_full {H_full.shape} in {time.time()-t0:.1f}s, "
          f"symm err={np.abs(H_full-H_full.T).max():.1e}", flush=True)

    blk = BlockNewton(sys, n_centers=32, max_block=20000, h_build_chunk=200)

    # ---- Analysis at two V sizes (dense three-way comparison) -----------
    print("\n--- dense three-way comparison at two variational sizes ---")
    # V_A: 1 wavepacket (large residual): ball around HF seed
    t0 = time.time()
    V_A, _ = sys.h_col(sys.seed_idx)
    print(f"\n[V_A: HF Bruhat ball] |V|={len(V_A)}  "
          f"(built {time.time()-t0:.1f}s)", flush=True)
    dense_analysis(V_A, sys, H_full, all_idx, e_fci, blk)

    # V_B: grow a few more wavepackets (small residual) — greedy ball cover
    # over the current residual (deterministic; no random choices).
    V = V_A.copy()
    v_set = set(int(x) for x in V)
    for _ in range(2):
        ev, Cv = np.linalg.eigh(H_full[np.ix_(np.searchsorted(all_idx, V),
                                              np.searchsorted(all_idx, V))])
        c_var = Cv[:, 0]
        posV = np.searchsorted(all_idx, V)
        mask = np.zeros(dim, dtype=bool); mask[posV] = True
        rO = H_full[~mask][:, posV] @ c_var
        cand = np.argsort(-np.abs(rO))[:200]
        O_idx = all_idx[~mask]
        best, best_s = None, -1.0
        for ci in cand:
            D = int(O_idx[ci])
            ball, _ = sys.h_col(D)
            n_inter = len(np.intersect1d(V, ball))
            sc = float(rO[ci] ** 2) * (1 - n_inter / max(len(ball), 1))
            if sc > best_s:
                best_s, best = sc, D
        ball, _ = sys.h_col(best)
        V_new = np.union1d(V, ball)
        if len(V_new) == len(V):
            break
        V = V_new
        print(f"  [grow] centre={best}, |V| -> {len(V)}", flush=True)
    print(f"\n[V_B: {len(V_A)} -> grown] |V|={len(V)}", flush=True)
    dense_analysis(V, sys, H_full, all_idx, e_fci, blk)

    # ---- full NEW descent run with dual stopping ------------------------
    print("\n--- new descent loop (correct-then-expand, dual stop 9.2) ---",
          flush=True)
    d = Descent(sys, chem_tol=1.59e-3, max_wavepackets=12,
                n_centers=32, max_block=20000, h_chunk=200,
                jacobi_sweeps=0, ball_cover_topk=100, verbose=True)
    t0 = time.time()
    E_final, E_var, E_corr, V_fin, c_fin, stats = d.run()
    wall = time.time() - t0
    print(f"\ndescent wall = {wall:.1f}s; |V_final|={len(V_fin)}", flush=True)

    # machine-precision checks
    ok_sign = verify.check_sign(stats, raise_on_error=False)
    ok_mono = verify.check_monotone(stats, raise_on_error=False)
    print(f"sign check (E_corr<=0): {ok_sign}")
    print(f"monotonicity (E_var non-increasing): {ok_mono}")

    err = (E_final - e_fci) * 1000
    print(f"\nFCI = {e_fci:+.10f} Ha")
    print(f"E_final (E_var+E_corr) = {E_final:+.10f} Ha")
    print(f"final error vs FCI = {err:+.4f} mHa  "
          f"(chemical accuracy 1.59 mHa)  {'PASS' if abs(err) < 1.59 else 'FAIL'}")
    print("=" * 78)


if __name__ == "__main__":
    main()
