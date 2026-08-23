"""Test case 2: three-sector zero-sum constraint.

Three independent two-level families with sector Chern numbers
(+1, +1, -2), so the global sum vanishes. Every individual sector
integral is nonzero, hence the zero-sum is a genuine global constraint:
it holds only if all three sectors are computed consistently, making it
a strong end-to-end test of mesh handling, periodic wrapping, and gauge
fixing.

Sector A: inverted monopole on S^2,           C = +1
Sector B: Qi-Wu-Zhang model (m = +1) on T^2,  C = +1
Sector C: double-cover QWZ (m = -1) on T^2,   C = -2
"""

import numpy as np
import pytest
from qutip import sigmax, sigmay, sigmaz

from qutip_geometry import chern_number


def sector_a(theta, phi):
    d = -(
        np.sin(theta) * np.cos(phi) * sigmax()
        + np.sin(theta) * np.sin(phi) * sigmay()
        + np.cos(theta) * sigmaz()
    )
    return d


def sector_b(k1, k2):
    return (
        np.sin(k1) * sigmax()
        + np.sin(k2) * sigmay()
        + (1.0 - np.cos(k1) - np.cos(k2)) * sigmaz()
    )


def sector_c(k1, k2):
    return (
        np.sin(2.0 * k1) * sigmax()
        + np.sin(k2) * sigmay()
        + (-1.0 - np.cos(2.0 * k1) - np.cos(k2)) * sigmaz()
    )


def sphere_mesh(n):
    return (
        np.linspace(0.0, np.pi, n + 1),
        np.linspace(0.0, 2.0 * np.pi, n, endpoint=False),
    )


def torus_mesh(n):
    k = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return k, k


def sector_cherns(n):
    theta, phi = sphere_mesh(n)
    k1, k2 = torus_mesh(n)
    C_A = chern_number(sector_a, theta, phi, wrap1=False, wrap2=True)
    C_B = chern_number(sector_b, k1, k2, wrap1=True, wrap2=True)
    C_C = chern_number(sector_c, k1, k2, wrap1=True, wrap2=True)
    return C_A, C_B, C_C


@pytest.mark.parametrize("n", [16, 32, 64])
def test_sector_values(n):
    C_A, C_B, C_C = sector_cherns(n)
    assert C_A == pytest.approx(1.0, abs=1e-10)
    assert C_B == pytest.approx(1.0, abs=1e-10)
    assert C_C == pytest.approx(-2.0, abs=1e-10)


@pytest.mark.parametrize("n", [16, 32, 64])
def test_zero_sum(n):
    C_A, C_B, C_C = sector_cherns(n)
    assert C_A + C_B + C_C == pytest.approx(0.0, abs=1e-10)


def test_zero_sum_is_nontrivial():
    """Every sector integral is nonzero; only their sum vanishes."""
    C_A, C_B, C_C = sector_cherns(32)
    assert abs(C_A) > 0.9
    assert abs(C_B) > 0.9
    assert abs(C_C) > 1.9
