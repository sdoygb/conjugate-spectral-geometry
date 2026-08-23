"""Parameter-space geometric quantities: Berry curvature and Chern numbers.

Reference implementation for the proposed ``qutip-geometry`` package.

Given a family of Hermitian Hamiltonians ``H(t1, t2)`` over a parameter
space, this module computes

- the Berry curvature of an individual band on a lattice mesh, via the
  Fukui-Hatsugai-Suzuki (FHS) link-variable formula;
- the Chern number of a band (the integral of the curvature);
- the non-Abelian Chern number of a degenerate subspace, via the
  projector (overlap-matrix) method.

All outputs are gauge invariant by construction: the FHS link variables
absorb the arbitrary eigenstate phase at each lattice point, and the
non-Abelian overlap matrices absorb arbitrary unitary rotations of the
degenerate-subspace basis.

References
----------
* T. Fukui, Y. Hatsugai, H. Suzuki, J. Phys. Soc. Jpn. 74, 1674 (2005),
  for the link-variable (lattice) formulation and its non-Abelian
  projector extension.
"""

import numpy as np
from qutip import Qobj

__all__ = ["berry_curvature", "chern_number", "nonabelian_chern_number"]


def _eigenfield(h_func, t1, t2, band):
    """Eigenvector field of band ``band`` over the (t1, t2) mesh."""
    t1 = np.asarray(t1, dtype=float)
    t2 = np.asarray(t2, dtype=float)
    if t1.ndim != 1 or t2.ndim != 1:
        raise ValueError("t1 and t2 must be one-dimensional arrays")
    H0 = h_func(t1[0], t2[0])
    if not isinstance(H0, Qobj):
        raise TypeError("h_func must return a qutip.Qobj")
    dim = H0.shape[0]
    if band < 0 or band >= dim:
        raise ValueError(f"band={band} out of range for {dim}-level system")
    V = np.empty((t1.size, t2.size, dim), dtype=complex)
    for i, v1 in enumerate(t1):
        for j, v2 in enumerate(t2):
            mat = h_func(v1, v2).full()
            if mat.shape != (dim, dim):
                raise ValueError("h_func returned an inconsistent Hilbert space")
            _, evecs = np.linalg.eigh(mat)
            V[i, j] = evecs[:, band]
    return V


def _plaquette_phases(V, wrap1, wrap2):
    """Plaquette field strengths F[i, j] from an eigenvector field V.

    Sum(F) equals 2*pi times the Chern number provided the mesh resolves
    the curvature (no plaquette phase exceeds pi in magnitude).
    """
    n1, n2, _ = V.shape
    m1 = n1 if wrap1 else n1 - 1
    m2 = n2 if wrap2 else n2 - 1
    # Link variables along axis 1 and axis 2.
    U1 = np.empty((m1, n2), dtype=complex)
    for i in range(m1):
        ip = (i + 1) % n1
        for j in range(n2):
            v = np.vdot(V[i, j], V[ip, j])
            U1[i, j] = v / abs(v)
    U2 = np.empty((n1, m2), dtype=complex)
    for i in range(n1):
        for j in range(m2):
            jp = (j + 1) % n2
            v = np.vdot(V[i, j], V[i, jp])
            U2[i, j] = v / abs(v)
    # Plaquette phases: F = Im ln(U1 * U2 * U1^* * U2^*).
    F = np.empty((m1, m2))
    for i in range(m1):
        ip = (i + 1) % n1
        for j in range(m2):
            jp = (j + 1) % n2
            w = U1[i, j] * U2[ip, j] * np.conj(U1[i, jp]) * np.conj(U2[i, j])
            F[i, j] = np.angle(w)
    return F


def berry_curvature(h_func, t1, t2, band=0, wrap1=False, wrap2=True):
    """Plaquette Berry field strengths F[i, j] of band ``band``.

    The sum of the returned array equals 2*pi times the Chern number of
    the band (when the mesh is fine enough that no plaquette phase
    exceeds pi in magnitude).

    Parameters
    ----------
    h_func : callable
        ``h_func(v1, v2) -> Qobj``. A Hermitian Hamiltonian family over
        the parameter space.
    t1, t2 : array_like
        Parameter-space axes. For a spherical mesh, use an open axis
        (endpoints included) together with a periodic one; for a
        toroidal mesh, both axes are periodic (endpoints excluded).
    band : int, default 0
        Eigenband index (0 = lowest energy).
    wrap1, wrap2 : bool
        Whether each axis is periodic.

    Returns
    -------
    F : ndarray of shape (m1, m2)
        Plaquette field strengths; ``F.sum() == 2*pi*C``.
    """
    V = _eigenfield(h_func, t1, t2, band)
    return _plaquette_phases(V, wrap1, wrap2)


def chern_number(h_func, t1, t2, band=0, wrap1=False, wrap2=True):
    """Chern number of band ``band`` over the parameter-space mesh."""
    F = berry_curvature(h_func, t1, t2, band=band, wrap1=wrap1, wrap2=wrap2)
    return F.sum() / (2.0 * np.pi)


def nonabelian_chern_number(h_func, t1, t2, bands, wrap1=True, wrap2=True):
    """Chern number of a (nearly) degenerate band subspace.

    Uses the projector method: at each mesh point the orthonormal basis
    of the subspace spanned by ``bands`` is extracted, and the plaquette
    phase is ``Im ln det`` of the product of overlap matrices around the
    plaquette. The result is gauge invariant under arbitrary unitary
    rotations of the subspace basis, so it works even when the bands are
    exactly degenerate and numerical eigensolvers mix the basis.

    Parameters
    ----------
    h_func : callable
        ``h_func(v1, v2) -> Qobj``. A Hermitian Hamiltonian family.
    t1, t2 : array_like
        Parameter-space axes (see ``chern_number``).
    bands : sequence of int
        Indices of the bands spanning the degenerate subspace.
    wrap1, wrap2 : bool
        Whether each axis is periodic.

    Returns
    -------
    C : float
        Joint Chern number of the subspace.
    """
    t1 = np.asarray(t1, dtype=float)
    t2 = np.asarray(t2, dtype=float)
    if t1.ndim != 1 or t2.ndim != 1:
        raise ValueError("t1 and t2 must be one-dimensional arrays")
    bands = list(bands)
    H0 = h_func(t1[0], t2[0])
    if not isinstance(H0, Qobj):
        raise TypeError("h_func must return a qutip.Qobj")
    dim = H0.shape[0]
    if any(b < 0 or b >= dim for b in bands):
        raise ValueError(f"bands={bands} out of range for {dim}-level system")
    d = len(bands)
    # Orthonormal basis of the subspace at each mesh point.
    U = np.empty((t1.size, t2.size, dim, d), dtype=complex)
    for i, v1 in enumerate(t1):
        for j, v2 in enumerate(t2):
            mat = h_func(v1, v2).full()
            _, evecs = np.linalg.eigh(mat)
            U[i, j] = evecs[:, bands]
    n1, n2 = t1.size, t2.size
    m1 = n1 if wrap1 else n1 - 1
    m2 = n2 if wrap2 else n2 - 1
    total = 0.0
    for i in range(m1):
        ip = (i + 1) % n1
        for j in range(m2):
            jp = (j + 1) % n2
            W = (
                (U[i, j].conj().T @ U[ip, j])
                @ (U[ip, j].conj().T @ U[ip, jp])
                @ (U[ip, jp].conj().T @ U[i, jp])
                @ (U[i, jp].conj().T @ U[i, j])
            )
            total += np.angle(np.linalg.det(W))
    return total / (2.0 * np.pi)
