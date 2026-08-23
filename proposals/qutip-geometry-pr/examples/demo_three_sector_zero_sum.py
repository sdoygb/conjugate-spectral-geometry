"""Demo: three-sector zero-sum constraint.

Sector A: inverted monopole on S^2,           C = +1
Sector B: Qi-Wu-Zhang model (m = +1) on T^2,  C = +1
Sector C: double-cover QWZ (m = -1) on T^2,   C = -2

Global constraint: C_A + C_B + C_C = 0.
"""

import numpy as np
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


if __name__ == "__main__":
    n = 32
    theta = np.linspace(0.0, np.pi, n + 1)
    phi = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    k = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)

    C_A = chern_number(sector_a, theta, phi, wrap1=False, wrap2=True)
    C_B = chern_number(sector_b, k, k, wrap1=True, wrap2=True)
    C_C = chern_number(sector_c, k, k, wrap1=True, wrap2=True)

    print(f"Sector A (S^2 inverted monopole):  C_A = {C_A:+.12f}")
    print(f"Sector B (T^2 QWZ, m=+1):         C_B = {C_B:+.12f}")
    print(f"Sector C (T^2 double-cover QWZ):   C_C = {C_C:+.12f}")
    print(f"Zero-sum: C_A + C_B + C_C = {C_A + C_B + C_C:+.3e}")
