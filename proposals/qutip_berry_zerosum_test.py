#!/usr/bin/env python3
"""
Three-sector zero-sum Chern number test - verification script.

Constructs three two-level Hamiltonian families over distinct parameter
spaces, computes the Chern number of the occupied (lower) band in each
sector with the Fukui-Hatsugai-Suzuki (FHS) lattice formula, and verifies
the global zero-sum constraint C_A + C_B + C_C = 0.

Sector A: inverted monopole on S^2        C = +1
    d(theta,phi) = -(sin t cos p, sin t sin p, cos t)
Sector B: Qi-Wu-Zhang model on T^2, m=+1  C = +1
    d(k1,k2) = (sin k1, sin k2, m - cos k1 - cos k2)
Sector C: double-cover QWZ on T^2, m=-1   C = -2
    d(k1,k2) = (sin 2k1, sin k2, m - cos 2k1 - cos k2)

Each sector integral is individually non-zero; the global constraint
(+1) + (+1) + (-2) = 0 is the only invariant. The script also checks
gauge invariance: multiplying every eigenvector by a random local phase
must leave the FHS Chern number unchanged (link variables absorb the
phases exactly, up to floating-point rounding).
"""

import numpy as np

# Pauli matrices
SX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SY = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
SZ = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def ham_from_d(d):
    """Build 2x2 Hamiltonian from Bloch vector d: H = d . sigma."""
    return d[0] * SX + d[1] * SY + d[2] * SZ


def lower_eigenvectors(H_field):
    """Field of normalized lower-band eigenvectors.

    H_field: array of shape (N1, N2, 2, 2), row-major over the grid.
    Returns array of shape (N1, N2, 2).
    """
    n1, n2 = H_field.shape[:2]
    v = np.zeros((n1, n2, 2), dtype=complex)
    for i in range(n1):
        for j in range(n2):
            _, vecs = np.linalg.eigh(H_field[i, j])
            v[i, j] = vecs[:, 0]  # lowest band
    return v


def fhs_chern(v, wrap1=False):
    """Chern number of the lower band via the FHS lattice formula.

    v: normalized eigenvector field, shape (N1, N2, 2).
    Axis 2 is always periodic (phi or k2 in [0, 2*pi)).
    wrap1=True: axis 1 is periodic too (T^2 model, N1 x N1 grid).
    wrap1=False: axis 1 is an open interval including endpoints (S^2 model,
        theta in [0, pi], N1 = N+1 points).
    Returns C = (1/2pi) * sum over plaquettes of the lattice field strength.
    """
    n1, n2, _ = v.shape
    # link variables U1 (along axis 1) and U2 (along axis 2, j -> j+1 mod n2)
    U1 = np.empty((n1, n2), dtype=complex)
    U2 = np.empty((n1, n2), dtype=complex)
    for i in range(n1):
        for j in range(n2):
            i1 = (i + 1) % n1 if wrap1 else i + 1
            if wrap1 or i < n1 - 1:
                ov = np.vdot(v[i, j], v[i1, j])
                U1[i, j] = ov / abs(ov)
            jp = (j + 1) % n2
            ov = np.vdot(v[i, j], v[i, jp])
            U2[i, j] = ov / abs(ov)
    # plaquette field strength
    total = 0.0
    ni = n1 if wrap1 else n1 - 1
    for i in range(ni):
        for j in range(n2):
            i1 = (i + 1) % n1
            jp = (j + 1) % n2
            w = U1[i, j] * U2[i1, j] * np.conj(U1[i, jp]) * np.conj(U2[i, j])
            total += np.angle(w)  # principal value in (-pi, pi]
    return total / (2.0 * np.pi)


def sector_A_inverted_monopole(N):
    """Inverted monopole on S^2. theta in [0, pi] (N+1 points incl.
    endpoints), phi in [0, 2*pi) periodic (N points).
    Expected C = +1 for the lower band (inversion flips the identity map)."""
    theta = np.linspace(0.0, np.pi, N + 1)
    phi = np.linspace(0.0, 2.0 * np.pi, N, endpoint=False)
    H = np.empty((N + 1, N, 2, 2), dtype=complex)
    for i, t in enumerate(theta):
        for j, p in enumerate(phi):
            d = -np.array([np.sin(t) * np.cos(p),
                           np.sin(t) * np.sin(p),
                           np.cos(t)])
            H[i, j] = ham_from_d(d)
    v = lower_eigenvectors(H)
    return fhs_chern(v, wrap1=False)


def sector_B_qwz(N, m=1.0):
    """QWZ model on T^2, k1,k2 in [0, 2*pi) periodic (N x N points).
    Expected C = +1 for the lower band at m=+1."""
    k = np.linspace(0.0, 2.0 * np.pi, N, endpoint=False)
    H = np.empty((N, N, 2, 2), dtype=complex)
    for i, k1 in enumerate(k):
        for j, k2 in enumerate(k):
            d = np.array([np.sin(k1),
                          np.sin(k2),
                          m - np.cos(k1) - np.cos(k2)])
            H[i, j] = ham_from_d(d)
    v = lower_eigenvectors(H)
    return fhs_chern(v, wrap1=True)


def sector_C_double_qwz(N, m=-1.0):
    """Double-cover QWZ on T^2 (k1 -> 2*k1), m=-1. Expected C = -2."""
    k = np.linspace(0.0, 2.0 * np.pi, N, endpoint=False)
    H = np.empty((N, N, 2, 2), dtype=complex)
    for i, k1 in enumerate(k):
        for j, k2 in enumerate(k):
            d = np.array([np.sin(2.0 * k1),
                          np.sin(k2),
                          m - np.cos(2.0 * k1) - np.cos(k2)])
            H[i, j] = ham_from_d(d)
    v = lower_eigenvectors(H)
    return fhs_chern(v, wrap1=True)


def gauge_invariance_check(N=32):
    """Verify that random local U(1) phases on eigenvectors leave the FHS
    Chern number unchanged (link variables absorb phases exactly, up to
    floating-point rounding)."""
    rng = np.random.default_rng(42)
    k = np.linspace(0.0, 2.0 * np.pi, N, endpoint=False)
    H = np.empty((N, N, 2, 2), dtype=complex)
    for i, k1 in enumerate(k):
        for j, k2 in enumerate(k):
            d = np.array([np.sin(k1), np.sin(k2), 1.0 - np.cos(k1) - np.cos(k2)])
            H[i, j] = ham_from_d(d)
    v0 = lower_eigenvectors(H)
    C0 = fhs_chern(v0, wrap1=True)
    vg = v0 * np.exp(1j * rng.uniform(0.0, 2.0 * np.pi, size=(N, N, 1)))
    Cg = fhs_chern(vg, wrap1=True)
    return C0, Cg


if __name__ == "__main__":
    print("Three-sector zero-sum Chern number verification")
    print("=" * 52)
    print(f"{'N':>5} | {'A (S2 inv. monopole)':>21} | {'B (QWZ m=+1)':>13} | "
          f"{'C (2xQWZ m=-1)':>14} | {'sum':>10}")
    print("-" * 76)
    for N in (16, 32, 64, 128):
        CA = sector_A_inverted_monopole(N)
        CB = sector_B_qwz(N)
        CC = sector_C_double_qwz(N)
        print(f"{N:>5} | {CA:>21.12f} | {CB:>13.12f} | {CC:>14.12f} | "
              f"{CA + CB + CC:>10.3e}")
    print()
    print("Gauge invariance check (QWZ, N=32):")
    C0, Cg = gauge_invariance_check(32)
    print(f"  C before random local phases : {C0:.15f}")
    print(f"  C after random local phases  : {Cg:.15f}")
    print(f"  difference                    : {abs(C0 - Cg):.3e}")
    print(f"  gauge invariant (diff < 1e-15): {abs(C0 - Cg) < 1e-15}")
