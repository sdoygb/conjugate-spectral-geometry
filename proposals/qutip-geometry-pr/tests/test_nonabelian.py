"""Test case 3: non-Abelian Chern number of a degenerate subspace.

Two inverted-monopole copies (optionally coupled by a small term) have
a two-dimensional low-energy subspace. The non-Abelian projector method
must return the joint Chern number +2 -- independent of the basis
mixing inside the degenerate subspace, and equal to the sum of the
individual Abelian band Chern numbers when the degeneracy is lifted.
"""

import numpy as np
import pytest
from qutip import Qobj, sigmax, sigmay, sigmaz

from qutip_geometry import chern_number, nonabelian_chern_number


def two_copy_monopole(theta, phi, lam=0.0):
    d = -(
        np.sin(theta) * np.cos(phi) * sigmax()
        + np.sin(theta) * np.sin(phi) * sigmay()
        + np.cos(theta) * sigmaz()
    )
    H = np.kron(np.eye(2), d.full())
    if lam != 0.0:
        V = np.zeros((4, 4), dtype=complex)
        V[0, 2] = V[2, 0] = V[1, 3] = V[3, 1] = lam
        H = H + V
    return Qobj(H)


def sphere_mesh(n):
    return (
        np.linspace(0.0, np.pi, n + 1),
        np.linspace(0.0, 2.0 * np.pi, n, endpoint=False),
    )


@pytest.mark.parametrize("n", [8, 16, 32])
def test_exactly_degenerate_subspace(n):
    """Fully degenerate copies: the projector method gives the joint
    Chern number, immune to arbitrary eigensolver basis mixing."""
    theta, phi = sphere_mesh(n)
    C = nonabelian_chern_number(
        two_copy_monopole, theta, phi, bands=[0, 1], wrap1=False, wrap2=True
    )
    assert C == pytest.approx(2.0, abs=1e-10)


@pytest.mark.parametrize("lam", [0.01, 0.3])
def test_lifted_degeneracy_matches_abelian_sum(lam):
    """With a gap opened, the joint Chern number equals the sum of the
    individual Abelian band Chern numbers."""
    theta, phi = sphere_mesh(16)

    def h(theta_, phi_):
        return two_copy_monopole(theta_, phi_, lam=lam)

    C_na = nonabelian_chern_number(
        h, theta, phi, bands=[0, 1], wrap1=False, wrap2=True
    )
    C0 = chern_number(h, theta, phi, band=0, wrap1=False, wrap2=True)
    C1 = chern_number(h, theta, phi, band=1, wrap1=False, wrap2=True)
    assert C_na == pytest.approx(C0 + C1, abs=1e-10)
    assert C0 == pytest.approx(1.0, abs=1e-10)
    assert C1 == pytest.approx(1.0, abs=1e-10)


def test_subspace_basis_rotation_invariance():
    """Rotating the two copies into each other with a parameter-dependent
    gauge transformation must not change the joint Chern number."""
    theta, phi = sphere_mesh(16)

    def rotated(theta_, phi_):
        alpha = 1.3 * np.sin(2.0 * theta_) + 0.6 * np.cos(3.0 * phi_)
        c, s = np.cos(alpha), np.sin(alpha)
        U = np.array(
            [[c, 0, -s, 0], [0, c, 0, -s], [s, 0, c, 0], [0, s, 0, c]],
            dtype=float,
        )
        H = two_copy_monopole(theta_, phi_).full()
        return Qobj(U.T @ H @ U)

    C0 = nonabelian_chern_number(
        two_copy_monopole, theta, phi, bands=[0, 1], wrap1=False, wrap2=True
    )
    C1 = nonabelian_chern_number(
        rotated, theta, phi, bands=[0, 1], wrap1=False, wrap2=True
    )
    assert C1 == pytest.approx(C0, abs=1e-10)
