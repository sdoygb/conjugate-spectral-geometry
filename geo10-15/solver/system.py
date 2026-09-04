"""System assembly: sector Hamiltonian building blocks for geo10-15.

Wraps the machine-verified geoqc building blocks (reused, not rewritten):
  - geoqc.integrals.spin_orbital_integrals  (spatial -> spin-orbital tensors)
  - geoqc.exterior.sparse_action_sz_vec      (matrix-free H|v>, Bruhat 2-ball)
  - geoqc.exterior.sector_diagonal_at        (one-body diagonal on demand)

Delivers a uniform "SectorSystem" used by the descent loop at any scale
(3025-dense M1 up to 2.39e15-nominal M3):

    sys = SectorSystem(n_orb, n_a, n_b, o_spatial, t_spatial, nuc)
    apply_fn, hd_fn, seed_idx, db, az_of, bz_of, rt_a, rt_b

apply_fn(azs, bzs, vals) -> (t_az, t_bz, t_v, src_idx): H|v> excitation part
    (includes the two-body diagonal in row==col terms).
hd_fn(idxs) -> one-body diagonal + nuclear repulsion at arbitrary indices.
seed_idx: HF determinant combined index.
"""
import numpy as np
from math import comb

try:
    from geoqc.integrals import spin_orbital_integrals
    from geoqc.exterior import sparse_action_sz_vec, sector_diagonal_at
    _HAS_GEOQC = True
except ImportError as e:
    _HAS_GEOQC = False
    _GEOQC_ERR = e

from .rank import build_rank_tables


class SectorSystem:
    """S_z-conserving N-electron sector of a molecular Hamiltonian."""

    def __init__(self, n_orb, n_a, n_b, o_spatial, t_spatial, nuc,
                 eps=1e-4, gpu_apply=None):
        if not _HAS_GEOQC:
            raise ImportError(
                "geoqc not importable — add geocore/ to sys.path. " +
                str(_GEOQC_ERR))
        self.n_orb = int(n_orb)
        self.n_a = int(n_a)
        self.n_b = int(n_b)
        self.nelec = n_a + n_b
        self.ns = 2 * self.n_orb
        self.nuc = float(nuc)
        self.eps = eps
        self.dim_a = comb(self.n_orb, self.n_a)
        self.dim_b = comb(self.n_orb, self.n_b)
        self.dim = self.dim_a * self.dim_b

        # spin-orbital one-body (real spatial -> complex spin-orbital diag)
        o_s = np.zeros((self.ns, self.ns), dtype=complex)
        o_s[0::2, 0::2] = np.asarray(o_spatial, dtype=float)
        o_s[1::2, 1::2] = np.asarray(o_spatial, dtype=float)
        self.o_s = o_s

        # two-body: CPU path needs the full spin-orbital tensor; the GPU
        # occupancy-aware doubles path works from the spatial tensor and can
        # skip t_s (M3: n_orb=38 -> t_s = 76^4 * 16 B = 534 MB, acceptable;
        # n_orb=85 -> 13.4 GB, must skip).
        if gpu_apply is None:
            _, self.t_s = spin_orbital_integrals(
                np.asarray(o_spatial, dtype=float),
                np.asarray(t_spatial, dtype=float))
            self.t_pass = self.t_s
        else:
            self.t_s = None
            self.t_pass = None
        self.gpu_apply = gpu_apply

        # rank tables (combinatorial, no O(2^n_orb) arrays)
        self.rt_a, self.rt_b, self.az_of, self.bz_of = build_rank_tables(
            self.n_orb, self.n_a, self.n_b)

        # matrix-free apply
        self.apply_fn, _, _, _, _, _ = sparse_action_sz_vec(
            self.ns, self.nelec, 0, self.o_s, self.t_pass, self.nuc,
            self.eps, gpu_apply=self.gpu_apply)

        # HF seed = lowest n_a / n_b orbitals
        e_a = np.array([self.o_s[2 * k, 2 * k].real for k in range(self.n_orb)])
        hf_a = np.sort(np.argsort(e_a)[:self.n_a])
        hf_b = hf_a.copy()
        hf_az = int(np.sum(1 << hf_a))
        hf_bz = int(np.sum(1 << hf_b))
        self.seed_idx = int(self.rt_a.rank(np.array([hf_az]))[0]) * \
            self.dim_b + int(self.rt_b.rank(np.array([hf_bz]))[0])
        self.hf_az = hf_az
        self.hf_bz = hf_bz

    # ------------------------------------------------------------------ diag
    def hd_fn(self, idxs):
        """One-body diagonal + nuc at arbitrary combined indices (on demand)."""
        return sector_diagonal_at(
            self.ns, self.nelec, 0, self.o_s, self.t_s, self.nuc,
            idxs=np.asarray(idxs, dtype=np.int64),
            lookup_tables=(self.az_of, self.bz_of, self.dim_b))

    # ------------------------------------------------------------- Bruhat 2-ball
    def bruhat_ball(self, center_idx, exclude=None):
        """supp(H|D>) = Bruhat 2-ball around centre (10.88 prop 2.06).

        Returns the sorted unique combined indices of all determinants
        connected to |D> by <=2 excitations, plus D itself (diagonal).
        exclude: set of combined indices to drop (e.g. current V).
        """
        u, w = apply_H_one(self.apply_fn, self.hd_fn, self.dim_b,
                           self.az_of, self.bz_of, self.rt_a, self.rt_b,
                           np.array([1.0]), np.array([int(center_idx)]))
        if exclude:
            ex = np.asarray(sorted(exclude), dtype=np.int64)
            mask = np.isin(u, ex, assume_unique=False)
            u = u[~mask]
            w = w[~mask]
        return u, w

    def h_col(self, center_idx, vals=None):
        """Full column H|D> (with coefficients), as (idx, values)."""
        v = np.ones(1, dtype=complex) if vals is None else np.asarray(vals)
        u, w = apply_H_one(self.apply_fn, self.hd_fn, self.dim_b,
                           self.az_of, self.bz_of, self.rt_a, self.rt_b,
                           v, np.array([int(center_idx)]))
        return u, w

    def apply_H_on(self, idx_arr, coeffs):
        """H|psi> for psi supported on idx_arr with coefficients coeffs.

        Returns (unique_target_idx_sorted, merged_values_real).
        """
        azs = self.az_of[idx_arr // self.dim_b]
        bzs = self.bz_of[idx_arr % self.dim_b]
        t_az, t_bz, t_v, src = self.apply_fn(azs, bzs, np.asarray(coeffs))
        t_idx = self.rt_a.rank(t_az) * self.dim_b + self.rt_b.rank(t_bz)
        all_idx = np.concatenate([t_idx, idx_arr])
        all_v = np.concatenate([np.asarray(t_v).real,
                                np.asarray(self.hd_fn(idx_arr) *
                                           np.asarray(coeffs)).real])
        u, inv = np.unique(all_idx, return_inverse=True)
        w = np.zeros(len(u), dtype=float)
        np.add.at(w, inv, all_v)
        return u, w


def apply_H_one(apply_fn, hd_fn, db, az_of, bz_of, rt_a, rt_b, vals, idx):
    """Single-column H|D> (kept for parity with geoqc.wci.apply_H)."""
    azs = az_of[idx // db]
    bzs = bz_of[idx % db]
    result = apply_fn(azs, bzs, vals)
    if len(result) == 4:
        t_az, t_bz, t_v, _ = result
    else:
        t_az, t_bz, t_v = result
    t_idx = rt_a.rank(t_az) * db + rt_b.rank(t_bz)
    all_idx = np.concatenate([t_idx, idx])
    all_v = np.concatenate([np.asarray(t_v).real,
                            np.asarray(hd_fn(idx) * vals).real])
    u, inv = np.unique(all_idx, return_inverse=True)
    w = np.zeros(len(u), dtype=float)
    np.add.at(w, inv, all_v)
    return u, w
