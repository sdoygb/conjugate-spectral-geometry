"""The NEW main loop: constrained-submanifold Newton descent (10.91 Thm 8.1).

Correct-then-expand alternation (user-confirmed design):
    V_0 = {HF seed}
    loop:
      ①  Rayleigh-Ritz on V_k        (submanifold criticalisation, r_in = 0)
      ②  out-of-space residual r_out
      ④  block-Newton normal-Hessian correction E_corr (eq 6.3) — EVERY round
      ②  dual stopping (9.2): |E_corr| < eps_chem AND |dE_corr| < eps_chem
      ③  if not converged: expand V by the best Bruhat ball (ball cover),
          V_{k+1} = V_k ∪ B(D*,2);  goto ①

Energy reporting:
    E_variational = RR eigenvalue on V_k (monotone decreasing, Prop 4.2)
    E_final = E_variational + E_corr  (block-Newton, unbiased 2nd order)

Differences from geoqc/wci.py (which this deliberately does NOT reuse):
  - correction (④) runs every round and is BLOCK Newton, not diagonal PT2;
  - stopping (②) uses |E_corr| (Newton gain) with the dual criterion (9.2),
    never ||r_out|| < tol (the "false convergence" metric, 10.91 §7);
  - expansion (③) and correction alternate within one loop body.
"""
import time
import numpy as np
import gc

from .blocks import BlockNewton, diagonal_pt2, gather_residual


class DescentStats:
    def __init__(self):
        self.rounds = []  # (n_var, E_var, E_corr, r_out_norm, t_H, t_r, t_b)

    def __repr__(self):
        return "\n".join(
            f"  round {k}: |V|={r[0]:6d} E_var={r[1]:+.10f} "
            f"E_corr={r[2]:+.8f} ||r_out||={r[3]:.5f} "
            f"(H {r[4]:.1f}s, r {r[5]:.1f}s, blk {r[6]:.1f}s)"
            for k, r in enumerate(self.rounds))


class Descent:
    """Constrained-submanifold Newton descent on the S_z sector."""

    def __init__(self, sys, chem_tol=1.59e-3, max_wavepackets=40,
                 n_centers=20, max_block=20000, h_chunk=200,
                 jacobi_sweeps=0, ball_cover_topk=100, verbose=True,
                 energy_floor_tol=1e-8, max_wp_size=None):
        self.sys = sys
        self.chem_tol = chem_tol
        self.max_wavepackets = max_wavepackets
        self.block_newton = BlockNewton(sys, n_centers=n_centers,
                                        max_block=max_block,
                                        h_build_chunk=h_chunk)
        self.h_chunk = h_chunk
        self.jacobi_sweeps = jacobi_sweeps
        self.ball_cover_topk = ball_cover_topk
        self.verbose = verbose
        self.energy_floor_tol = energy_floor_tol
        self.max_wp_size = max_wp_size  # Bruhat-ball truncation (strongest
        # |H_D,centre| couplings kept; geoqc Wavepacket criterion)

    # ------------------------------------------------------------- utilities
    def _v_index_sets(self, V):
        """Sorted unique alpha/beta bitstrings inside V (for prefiltering)."""
        db = self.sys.dim_b
        az_of, bz_of = self.sys.az_of, self.sys.bz_of
        return (np.unique(az_of[V // db]), np.unique(bz_of[V % db]),
                az_of, bz_of)

    def _apply_chunk(self, V, c0, c1, coeffs=None):
        """Batched H action on V[c0:c1] (or excitation-only part with
        coeffs), returning (t_az, t_bz, t_v, src_local)."""
        db = self.sys.dim_b
        az_of, bz_of = self.sys.az_of, self.sys.bz_of
        chunk_idx = V[c0:c1]
        azs = az_of[chunk_idx // db]
        bzs = bz_of[chunk_idx % db]
        vals = (np.ones(c1 - c0, dtype=complex) if coeffs is None
                else np.asarray(coeffs, dtype=complex))
        t_az, t_bz, t_v, src_idx = self.sys.apply_fn(azs, bzs, vals)
        return t_az, t_bz, t_v, src_idx + c0

    def _build_H(self, unique_idx, col_thresh=1e-5, cache_cols=True):
        """Dense H on V via chunked BATCH apply with in-V prefiltering,
        PLUS (if cache_cols) cached filtered columns H_cols[j] =
        (target_idx, values) for the incremental residual.

        KEY optimisation: rank is applied ONLY to targets that are either
        (a) in-V candidates (az AND bz bitstrings occur in V) or
        (b) significant (|value| > col_thresh) for the column cache
        (skipped entirely when cache_cols=False — cheap pure-H builds).
        The remaining tiny out-of-space targets are never ranked.
        """
        n = len(unique_idx)
        db = self.sys.dim_b
        rt_a, rt_b = self.sys.rt_a, self.sys.rt_b
        v_az_u, v_bz_u, az_of, bz_of = self._v_index_sets(unique_idx)
        H = np.zeros((n, n), dtype=float)
        H_cols = {}
        chunk = self.h_chunk
        for c0 in range(0, n, chunk):
            c1 = min(c0 + chunk, n)
            t_az, t_bz, t_v, src_global = self._apply_chunk(unique_idx,
                                                            c0, c1)
            t_v = np.asarray(t_v).real
            # (a) in-V candidates need rank for the H fill
            in_az = np.isin(t_az, v_az_u)
            in_bz = np.isin(t_bz, v_bz_u)
            cand = in_az & in_bz
            # (b) significant targets need rank for the column cache
            sig = (np.abs(t_v) > col_thresh) if cache_cols else cand
            need = cand | sig
            if need.any():
                t_idx_need = (rt_a.rank(t_az[need]) * db
                              + rt_b.rank(t_bz[need]))
            # H fill (only in-V rows)
            if cand.any():
                t_idx = np.full(cand.sum(), -1, dtype=np.int64)
                # map back: cand positions within need
                need_pos = np.cumsum(need) - 1
                t_idx[:] = t_idx_need[need_pos[cand]]
                row_pos = np.searchsorted(unique_idx, t_idx)
                ok = row_pos < n
                if ok.any():
                    ok[ok] &= unique_idx[row_pos[ok]] == t_idx[ok]
                np.add.at(H, (row_pos[ok], src_global[cand][ok]),
                          t_v[cand][ok])
                del t_idx
            # column cache (significant targets, grouped by source)
            if cache_cols and sig.any():
                s_idx = np.full(sig.sum(), -1, dtype=np.int64)
                need_pos = np.cumsum(need) - 1
                s_idx[:] = t_idx_need[need_pos[sig]]
                s_v = t_v[sig]
                s_src = src_global[sig]
                order = np.argsort(s_src, kind="stable")
                s_idx = s_idx[order]; s_v = s_v[order]
                s_src = s_src[order]
                boundaries = np.where(np.diff(s_src) != 0)[0] + 1
                starts = np.concatenate([[0], boundaries])
                ends = np.concatenate([boundaries, [len(s_src)]])
                for si in range(len(starts)):
                    src = int(s_src[starts[si]])
                    key = int(unique_idx[src])  # combined index of source
                    H_cols[key] = (s_idx[starts[si]:ends[si]].copy(),
                                   s_v[starts[si]:ends[si]].copy())
            del t_az, t_bz, t_v, src_global, need
            import gc as _gc
            _gc.collect()
        # one-body diagonal + nuc (apply_fn gave the two-body diagonal)
        diag_vals = np.asarray(self.sys.hd_fn(unique_idx)).real
        np.add.at(H, (np.arange(n), np.arange(n)), diag_vals)
        # add one-body diagonal into cached columns
        for j in range(n):
            key = int(unique_idx[j])
            if key in H_cols:
                p, v = H_cols[key]
                H_cols[key] = (np.concatenate([p, [key]]),
                               np.concatenate([v, [diag_vals[j]]]))
            else:
                H_cols[key] = (np.array([key], dtype=np.int64),
                               np.array([diag_vals[j]], dtype=float))
        H = (H + H.T) / 2.0
        return H, H_cols

    def _eigh_ground(self, H):
        w, V = np.linalg.eigh(H)
        return float(w[0]), V[:, 0]

    # ----------------------------------------------------------- main loop
    def run(self, max_rounds=None, init_ball=True):
        """Run the descent from the HF seed.

        V_0 = Bruhat 2-ball of the HF seed (truncated to max_wp_size) —
        the first wavepacket; grows by ball-cover expansion each round.

        Returns (E_final, stats) where
          E_final = E_var(final) + E_corr(final)  (block-Newton corrected)
        plus the final variational space and wavefunction for analysis.
        """
        sys = self.sys
        max_rounds = max_rounds or self.max_wavepackets
        stats = DescentStats()

        # cumulative variational space (union of Bruhat balls, grows only)
        if init_ball:
            ball0, w0 = sys.h_col(int(sys.seed_idx))
            if self.max_wp_size is not None and len(ball0) > self.max_wp_size:
                order = np.argsort(-np.abs(w0))[:self.max_wp_size]
                ball0 = ball0[order]
            V = np.asarray(ball0, dtype=np.int64)
        else:
            V = np.array([int(sys.seed_idx)], dtype=np.int64)
        E_corr_prev = None
        E_prev = None

        for it in range(max_rounds):
            t0 = time.time()
            H_mat, H_cols = self._build_H(V)
            t_H = time.time() - t0
            E_var, c_var = self._eigh_ground(H_mat)

            # residual (out-of-space) from cached columns — no second apply
            t0 = time.time()
            r_out_idx, r_out_vals = self._residual_from_cols(
                V, c_var, E_var, H_cols)
            t_r = time.time() - t0
            r_out_norm = float(np.linalg.norm(r_out_vals)) \
                if len(r_out_vals) else 0.0

            # block-Newton correction (every round — the geometric 2nd order)
            t0 = time.time()
            E_corr, binfo = self.block_newton.sweep(
                r_out_idx, r_out_vals, E_var, in_space_idx=V,
                jacobi_sweeps=self.jacobi_sweeps, verbose=False)
            t_b = time.time() - t0

            stats.rounds.append((len(V), E_var, E_corr, r_out_norm,
                                 t_H, t_r, t_b))
            if self.verbose:
                print(f"  round {it+1:2d}: |V|={len(V):6d}  "
                      f"E_var={E_var:+.10f}  E_corr={E_corr:+.8f}  "
                      f"E_var+E_corr={E_var+E_corr:+.10f}  "
                      f"||r_out||={r_out_norm:.5f}  cov="
                      f"{binfo['residual_coverage']:.4f}  n_blk="
                      f"{binfo['n_blocks']}  (H {t_H:.1f}s r {t_r:.1f}s "
                      f"blk {t_b:.1f}s)", flush=True)
                if binfo.get("jacobi_gaps"):
                    print(f"        jacobi: rho={binfo['jacobi_rho']:.3f} "
                          f"gaps={[f'{g:+.1e}' for g in binfo['jacobi_gaps']]}")

            # ---- dual stopping criterion (10.91 §9.2) ----
            dE_corr = abs(E_corr - E_corr_prev) if E_corr_prev is not None \
                else float("inf")
            if abs(E_corr) < self.chem_tol and dE_corr < self.chem_tol:
                if self.verbose:
                    print(f"  CONVERGED (dual 9.2): |E_corr|={abs(E_corr):.2e}"
                          f" < {self.chem_tol:.2e}, dE_corr={dE_corr:.2e}")
                break
            # energy floor guard (variational E stops moving)
            if E_prev is not None and abs(E_var - E_prev) < self.energy_floor_tol \
                    and len(r_out_vals) == 0:
                break
            E_corr_prev = E_corr
            E_prev = E_var

            if it == max_rounds - 1:
                break

            # ---- expand: best Bruhat ball by ball-cover selection ----
            new_center = self._select_center(r_out_idx, r_out_vals, V)
            ball, wball = self.sys.h_col(int(new_center))
            if self.max_wp_size is not None and len(ball) > self.max_wp_size:
                # truncate to the strongest couplings (Wavepacket criterion)
                order = np.argsort(-np.abs(wball))[:self.max_wp_size]
                ball = ball[order]
            V_new = np.union1d(V, ball)
            if len(V_new) == len(V):
                if self.verbose:
                    print("  V unchanged — terminating expansion")
                break
            V = V_new
            gc.collect()

        E_final = E_var + E_corr
        return E_final, E_var, E_corr, V, c_var, stats

    # ------------------------------------------------------------ residual
    def _residual_from_cols(self, V, c_var, E_var, H_cols, r_in_tol=1e-9):
        """r_out from cached columns: r = sum_j coeff_j * H|D_j> - E psi,
        aggregated by target idx (geoqc design).  In-space rows give r_in
        (~0 after eigh); out-of-space rows are returned sorted."""
        n = len(V)
        # aggregate over columns: dict-free via stacked arrays is heavy;
        # geoqc accumulates per column into r_out via np.unique over the
        # concatenation of all filtered columns (in + out targets).
        idx_parts = []
        val_parts = []
        for j in range(n):
            key = int(V[j])
            if key in H_cols:
                p, v = H_cols[key]
                idx_parts.append(p)
                val_parts.append(v * float(c_var[j]))
        if not idx_parts:
            return (np.array([], dtype=np.int64),
                    np.array([], dtype=float))
        all_idx = np.concatenate(idx_parts)
        all_v = np.concatenate(val_parts)
        u, inv = np.unique(all_idx, return_inverse=True)
        w = np.zeros(len(u), dtype=float)
        np.add.at(w, inv, all_v)
        # subtract E*psi on in-space rows
        pos = np.searchsorted(V, u)
        in_space = pos < n
        if in_space.any():
            in_space[in_space] &= V[pos[in_space]] == u[in_space]
        if in_space.any():
            w[in_space] -= E_var * c_var[pos[in_space]]
        out_mask = ~in_space
        return u[out_mask], w[out_mask]

    # ------------------------------------------------------- ball selection
    def _select_center(self, r_out_idx, r_out_vals, V):
        """Bruhat-ball greedy-cover selection (10.88 §5.3 / 10.91 eq 5.2):
        score(D) = |r_D|^2 * (1 - |B(D,2) ∩ V| / |B(D,2)|)."""
        sys = self.sys
        idx = np.asarray(r_out_idx)
        vals = np.asarray(r_out_vals, dtype=float)
        if len(idx) > self.ball_cover_topk:
            sel = np.argsort(-np.abs(vals))[:self.ball_cover_topk]
            idx, vals = idx[sel], vals[sel]
        best_score = -1.0
        best_center = int(idx[0])
        for j in range(len(idx)):
            D = int(idx[j])
            ball, _ = sys.h_col(D)
            n_inter = len(np.intersect1d(V, ball))
            n_ball = len(ball)
            frac = 1.0 - n_inter / max(n_ball, 1)
            score = float(vals[j] ** 2) * frac
            if score > best_score:
                best_score = score
                best_center = D
        return best_center


def run_descent(sys, **kw):
    """Convenience entry point."""
    d = Descent(sys, **kw)
    return d.run()
