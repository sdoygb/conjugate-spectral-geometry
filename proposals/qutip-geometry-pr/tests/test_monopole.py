"""Test case 1: two-level monopole on S^2 (Chern number +1).

The inverted monopole H = -r_hat . sigma has a lowest band with Chern
number +1. The Chern number is computed on spherical meshes of several
resolutions, and its gauge invariance is checked by applying a
parameter-dependent local gauge transformation to the Hamiltonian.
"""

import numpy as np
import pytest
from qutip import Qobj, sigmax, sigmay, sigmaz

from qutip_geometry import berry_curvature, chern_number


def inverted_monopole(theta, phi):
    d = -(
        np.sin(theta) * np.cos(phi) * sigmax()
        + np.sin(theta) * np.sin(phi) * sigmay()
        + np.cos(theta) * sigmaz()
    )
    return d


def sphere_mesh(n):
    theta = np.linspace(0.0, np.pi, n + 1)
    phi = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return theta, phi


@pytest.mark.parametrize("n", [8, 16, 32, 64])
def test_monopole_chern_number(n):
    theta, phi = sphere_mesh(n)
    C = chern_number(inverted_monopole, theta, phi, wrap1=False, wrap2=True)
    assert C == pytest.approx(1.0, abs=1e-10)


@pytest.mark.parametrize("n", [16, 32])
def test_monopole_curvature_sums_to_chern(n):
    theta, phi = sphere_mesh(n)
    F = berry_curvature(inverted_monopole, theta, phi, wrap1=False, wrap2=True)
    assert F.sum() / (2.0 * np.pi) == pytest.approx(1.0, abs=1e-10)


def test_monopole_gauge_invariance():
    """A local gauge transformation of the Hamiltonian family must not
    change the Chern number."""

    def gauged(theta, phi):
        alpha = 0.7 * np.sin(3.0 * theta) * np.cos(5.0 * phi)
        c, s = np.cos(alpha), np.sin(alpha)
        U = np.array([[c, -s], [s, c]], dtype=float)
        H = inverted_monopole(theta, phi).full()
        return Qobj(U.T @ H @ U)

    theta, phi = sphere_mesh(32)
    C0 = chern_number(inverted_monopole, theta, phi, wrap1=False, wrap2=True)
    C1 = chern_number(gauged, theta, phi, wrap1=False, wrap2=True)
    assert C1 == pytest.approx(C0, abs=1e-10)
