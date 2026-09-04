"""Bruhat-ball normal-Hessian blocks + block Jacobi (10.91 §6.2/§9.1).

The geometric second-order correction (Lemma D):
    E_corr = -<r_out, H_N^{-1} r_out>,   H_N = Q(H - E0)Q |_{V^\perp}
cannot be computed globally at dim ~1e15.  Bruhat locality (Prop 2.4:
<D'|H|D> != 0 => d_B(D,D') <= 2) makes H_N block-structured: balls centred
at distance >4 are exactly decoupled, so

    H_N ~= (+) H_N^(k) over disjoint Bruhat 2-balls,
    E_corr ~= -sum_k <r|_{B_k}, (H_N^(k))^{-1} r|_{B_k}>          (6.3)

Each ball block is a dense ~10^3-10^4 matrix (intra-ball single/double
excitations) and is inverted exactly — this captures the couplings that
diagonal EN-PT2 throws away, breaking its ~10 mHa structural floor.

Inter-ball coupling between balls at Bruhat distance 3-4 is swept by block
Jacobi (9.1):  delta^{(t+1)} = D^{-1}(r - O delta^{(t)}), convergent iff
rho(D^{-1}O) < 1.

This module is fresh code for geo10-15 (the geoqc examples version was a
post-pass helper inside wci.py; here it is a first-class component of the
main loop, with block-Jacobi and residual-coverage accounting).
"""
import numpy as np
import gc


def gather_residual(local_idx, r_out_idx, r_out_vals):
    """Residual values at local_idx (both sorted ascending)."""
    pos = np.searchsorted(r_out_idx, local_idx)
    valid = pos < len(r_out_idx)
    if valid.any():
        valid[valid] &= r_out_idx[pos[valid]] == local_idx[valid]
    out = np.zeros(len(local_idx), dtype=float)
    out[valid] = r_out_vals[pos[valid]]
    return out


class BlockNewton:
    """One block-Newton sweep over disjoint Bruhat 2-balls (10.91 eq 6.3).

    Parameters
    ----------
    sys : SectorSystem
    n_centers : int — number of top-residual centres (default 20)
    max_block : int — cap per-ball size (safety on 16 GB; larger centres
        with giant balls are truncated with honest coverage accounting)
    h_build_chunk : int — H-block build chunk size
    """

    def __init__(self, sys, n_centers=20, max_block=20000, h_build_chunk=200):
        self.sys = sys
        self.n_centers = n_centers
        self.max_block = max_block
        self.h_build_chunk = h_build_chunk

    # ------------------------------------------------------------- internals
    def _ball_of(self, center):
        """Sorted unique Bruhat 2-ball members (incl. centre)."""
        u, _ = self.sys.h_col(int(center))
        return u

    def _block_H(self, local, E0):
        """Dense normal-Hessian block H_N^(k) = H_block - E0 I on `local`,
        built by one BATCHED apply over all members (vectorised), with
        in-block prefiltering: a target can land in the block only if its
        alpha AND beta bitstrings occur in the block."""
        local = np.asarray(local, dtype=np.int64)
        n = len(local)
        sys = self.sys
        db = sys.dim_b
        az_of, bz_of = sys.az_of, sys.bz_of
        rt_a, rt_b = sys.rt_a, sys.rt_b
        v_az_u = np.unique(az_of[local // db])
        v_bz_u = np.unique(bz_of[local % db])
        H = np.zeros((n, n), dtype=float)
        chunk = self.h_build_chunk
        for c0 in range(0, n, chunk):
            c1 = min(c0 + chunk, n)
            cidx = local[c0:c1]
            azs = az_of[cidx // db]
            bzs = bz_of[cidx % db]
            t_az, t_bz, t_v, src_idx = sys.apply_fn(
                azs, bzs, np.ones(c1 - c0, dtype=complex))
            t_v = np.asarray(t_v).real
            in_az = np.isin(t_az, v_az_u)
            in_bz = np.isin(t_bz, v_bz_u)
            cand = in_az & in_bz
            if cand.any():
                t_idx = rt_a.rank(t_az[cand]) * db + rt_b.rank(t_bz[cand])
                row_pos = np.searchsorted(local, t_idx)
                ok = row_pos < n
                if ok.any():
                    ok[ok] &= local[row_pos[ok]] == t_idx[ok]
                np.add.at(H, (row_pos[ok], np.asarray(src_idx)[cand][ok]
                              + c0), t_v[cand][ok])
            del t_az, t_bz, t_v, src_idx
            gc.collect()
        diag_vals = np.asarray(sys.hd_fn(local)).real
        np.add.at(H, (np.arange(n), np.arange(n)), diag_vals)
        H = (H + H.T) / 2.0
        H -= E0 * np.eye(n)
        return H

    # ---------------------------------------------------------------- sweep
    def sweep(self, r_out_idx, r_out_vals, E0, in_space_idx=None,
              jacobi_sweeps=0, verbose=False):
        """One block-diagonal Newton sweep (10.91 §12.3: single pass already
        ~1e-7 for LiH — far below chemical accuracy; Jacobi as refinement).

        Returns (E_block, info) with info containing block sizes, per-block
        corrections, residual coverage, and (if jacobi_sweeps>0) the block-
        Jacobi refinement trace.
        """
        sys = self.sys
        n_out = len(r_out_idx)
        info = {"n_blocks": 0, "block_sizes": [], "block_E": [],
                "n_assigned": 0, "residual_coverage": 0.0,
                "assigned_idx": None, "block_members": []}
        if n_out == 0:
            return 0.0, info

        r_out_idx = np.asarray(r_out_idx)
        r_out_vals = np.asarray(r_out_vals, dtype=float)

        # 1. centres = top-n_centers residual determinants
        nc = min(self.n_centers, n_out)
        centre_sel = np.argpartition(-np.abs(r_out_vals), nc - 1)[:nc] \
            if n_out > nc else np.arange(nc)
        centres = r_out_idx[centre_sel]

        v_set = set(int(x) for x in np.asarray(in_space_idx)) \
            if in_space_idx is not None else set()
        assigned = set()
        blocks = []

        # 2. disjoint Bruhat 2-balls (greedy first-come assignment)
        for C in centres:
            u = self._ball_of(int(C))
            local = [int(x) for x in u.tolist()
                     if x not in v_set and x not in assigned]
            if not local:
                continue
            if len(local) > self.max_block:
                # truncate to max_block largest-|r| members (honest accounting)
                arr = np.asarray(local)
                rl = gather_residual(arr, r_out_idx, r_out_vals)
                keep = np.argsort(-np.abs(rl))[:self.max_block]
                local = arr[keep].tolist()
            local = np.unique(np.asarray(local, dtype=np.int64))
            assigned.update(local.tolist())
            blocks.append(local)

        # 3. residual-weight coverage
        total_rsq = float(np.sum(r_out_vals ** 2))
        if total_rsq > 0:
            covered = np.array([x for x in r_out_idx.tolist()
                                if x in assigned])
            if len(covered):
                info["residual_coverage"] = float(
                    np.sum(gather_residual(np.unique(covered), r_out_idx,
                                           r_out_vals) ** 2) / total_rsq)

        # 4. per-block dense normal-Hessian inversion
        E_block = 0.0
        for k, local in enumerate(blocks):
            Hn = self._block_H(local, E0)
            m = len(local)
            rb = gather_residual(local, r_out_idx, r_out_vals)
            try:
                x = np.linalg.solve(Hn, rb)
            except np.linalg.LinAlgError:
                w, V = np.linalg.eigh(Hn)
                winv = 1.0 / np.where(np.abs(w) < 1e-10, 1e-10, w)
                x = V @ (winv * (V.T @ rb))
            ek = -float(rb @ x)
            E_block += ek
            info["block_sizes"].append(m)
            info["block_E"].append(ek)
            info["block_members"].append(local.copy())
            if verbose:
                print(f"    block {k}: size={m}, E_corr={ek:+.8f}, "
                      f"|r_block|={np.linalg.norm(rb):.6f}")
            del Hn, rb, x
            gc.collect()

        info["n_blocks"] = len(blocks)
        info["n_assigned"] = len(assigned)
        info["assigned_idx"] = (np.sort(np.asarray(sorted(assigned),
                                                   dtype=np.int64))
                                if assigned else np.array([], dtype=np.int64))

        # 5. block-Jacobi refinement (optional, 10.91 §9.1)
        if jacobi_sweeps > 0 and info["n_blocks"] > 1:
            E_block, info = self._jacobi_refine(
                blocks, r_out_idx, r_out_vals, E0, E_block, info,
                jacobi_sweeps)
        return E_block, info

    # ------------------------------------------------------------ block Jacobi
    def _jacobi_refine(self, blocks, r_out_idx, r_out_vals, E0, E_block,
                       info, n_sweeps):
        """Iterate delta <- D^{-1}(r - O delta) on the fully-assigned subspace.
        Returns refined E_block and appends a gap trace to info."""
        if not blocks:
            return E_block, info
        asg = np.sort(np.asarray(sorted(set().union(
            *(set(map(int, b)) for b in blocks))), dtype=np.int64))
        n = len(asg)
        if n == 0:
            return E_block, info
        H = self._block_H(asg, 0.0)  # batch-built on the union
        Hn = H - E0 * np.eye(n)
        r = gather_residual(asg, r_out_idx, r_out_vals)
        # block diagonal D and coupling O
        pos_of = {int(g): j for j, g in enumerate(asg)}
        D = np.zeros_like(Hn)
        for b in blocks:
            bp = np.array([pos_of[int(g)] for g in b])
            D[np.ix_(bp, bp)] = Hn[np.ix_(bp, bp)]
        O = Hn - D
        # exact solution of the union subspace (anchor for gaps)
        x_exact = np.linalg.solve(Hn, r)
        E_exact = -float(r @ x_exact)
        x = np.linalg.solve(D, r)
        E_iter = -float(r @ x)
        gaps = [E_iter - E_exact]
        try:
            rho = max(abs(np.linalg.eigvals(np.linalg.solve(D, O))))
        except np.linalg.LinAlgError:
            rho = float("nan")
        for _ in range(n_sweeps):
            x = np.linalg.solve(D, r - O @ x)
            E_iter = -float(r @ x)
            gaps.append(E_iter - E_exact)
        info["jacobi_rho"] = float(rho)
        info["jacobi_gaps"] = [float(g) for g in gaps]
        info["jacobi_exact"] = float(E_exact)
        return float(E_exact), info


# ---------------------------------------------------------------------------
# Convenience: diagonal EN-PT2 (for the ordering comparison |2nd|<=|block|<=
# |diag|, and as a cheap mid-iteration estimate — never the final energy)
# ---------------------------------------------------------------------------

def diagonal_pt2(r_out_idx, r_out_vals, E0, sys, top_n=200000,
                 chunk_size=500):
    """E_PT2 = -sum_{D not in V} |r_D|^2 / (H_DD - E0) over top-n residuals.

    Diagonal approximation of H_N (1x1 blocks).  Has a structural floor
    (10.91 Cor 6.2): increasing top_n only approaches it.  Used ONLY for
    comparison and cheap estimates; the final energy comes from block Newton.
    """
    idx = np.asarray(r_out_idx)
    vals = np.asarray(r_out_vals, dtype=float)
    if len(idx) > top_n:
        sel = np.argsort(-np.abs(vals))[:top_n]
        idx, vals = idx[sel], vals[sel]
    n = len(idx)
    s = 0.0
    for c0 in range(0, n, chunk_size):
        c1 = min(c0 + chunk_size, n)
        hdd = np.asarray(sys.hd_fn(idx[c0:c1])).real
        # two-body diagonal must be added: hd_fn is one-body only; the
        # diagonal of H includes two-body (row==col in apply).  For the EN
        # denominator we need the FULL H_DD.  h_col includes it.
        # -> recompute per-determinant via h_col (correct, chunked):
        for j in range(c0, c1):
            u, w = sys.h_col(int(idx[j]))
            hdd_j = float(w[np.where(u == idx[j])[0][0]])
            dn = E0 - hdd_j
            s += vals[j] ** 2 / dn if abs(dn) > 1e-10 else 0.0
    return -float(s)
